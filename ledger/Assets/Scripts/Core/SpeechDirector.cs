using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// WHO SPEAKS LIVE, AND WHETHER THIS MACHINE CAN AFFORD IT.
    ///
    /// `SpeechLoop` can generate a line. That is not the same as knowing when
    /// to, and the difference is the whole of whether this feature is pleasant
    /// or a curse. One measured line costs about nine seconds against roughly
    /// three seconds of speech, so a game that simply generates whatever it
    /// wants is a game where conversations stall.
    ///
    /// Three decisions live here, and all three are pure arithmetic, which is
    /// why they are in Core where they can be run rather than in the Game
    /// layer where they would wait ~28 minutes to be wrong.
    ///
    /// 1. ASK THE BANK FIRST, ALWAYS. `VoiceBank` holds 2,010 already-generated
    ///    lines. Anything authored is in there, instant and free. Live speech
    ///    is for what was never written down — which is what putting a voice
    ///    model on the player's machine was FOR, and is a much smaller set
    ///    than "every line".
    ///
    /// 2. THE DEADLINE COMES FROM THE MACHINE, NOT FROM A CONSTANT. A card
    ///    that manages a line in four seconds and one that needs thirty want
    ///    completely different answers, and neither is knowable at build time.
    ///    So the rate is measured from lines actually generated here, and the
    ///    deadline for the next one is set from it.
    ///
    /// 3. WHAT COULD NOT BE AFFORDED IS COUNTED. A feature that quietly does
    ///    nothing on slow hardware is indistinguishable from one that is not
    ///    wired, which is rule 3b and the reason every zero in this project
    ///    ships with a denominator.
    public enum SpeechRoute
    {
        /// The bank has this line. Free, instant, and the answer most of the
        /// time.
        Banked = 0,
        /// Never written down, and this machine can afford to say it.
        Live = 1,
        /// Never written down, and it would not arrive in time. The character
        /// stays quiet; the bubble still appears.
        TooSlow = 2,
        /// No model on this machine at all — no plugin, no device, an
        /// integrated card. The commonest answer in the wild, and it must be
        /// its own outcome rather than folded into `TooSlow`, because the two
        /// have completely different fixes.
        NoModel = 3,
        /// Nothing to say.
        Nothing = 4,
    }

    /// Decides the route for each line and remembers what the machine can do.
    ///
    /// AN INSTANCE, NOT A STATIC. The measured rate is per-machine state, and
    /// a static would make it impossible to test two machines in one run —
    /// which is exactly what the tests below do.
    public class SpeechDirector
    {
        /// How many lines to average the rate over.
        ///
        /// SMALL ON PURPOSE. A machine's speed changes within a session — a
        /// background process, a thermal limit, the player alt-tabbing — and
        /// an average over the whole run cannot see that. Eight is enough to
        /// stop one slow line from closing the feature and short enough to
        /// follow a real change.
        public const int Window = 8;

        /// The longest a line may take before it is not worth having.
        ///
        /// NOT MEASURED, AND SAID SO. This is a judgement about the player's
        /// patience rather than about the hardware: a character muttering
        /// something four seconds after you walked past them has missed the
        /// moment. It is the one number in this file that evidence cannot
        /// settle, so it is exposed for tuning instead of buried.
        public double PatienceSeconds = 4.0;

        /// The steps-per-second this machine has actually managed. Zero until
        /// a line has been generated — which is why `Route` lets the first one
        /// through regardless. A director that refuses to try can never learn
        /// that it could have.
        public double StepsPerSecond { get; private set; }

        /// HOW A LINE'S LENGTH IS COUNTED, and the unit changed once the
        /// tokeniser existed.
        ///
        /// This measured steps per CHARACTER, which was the only thing
        /// available and was wrong in a way that mattered: the model emits one
        /// step per TOKEN, and a token is anywhere from one character to a
        /// whole word. "the" is one token and "ZQXJ" is four, so a
        /// character count misjudges both, in opposite directions.
        ///
        /// `Core/SpeechTokenizer` is the real thing, checked against
        /// HuggingFace's own answers, so the game hands it in and the estimate
        /// counts what the model actually charges for. Null falls back to
        /// characters — a machine with no vocabulary file can still measure
        /// itself, just less well, and that is better than refusing to.
        public Func<string, int> Length;

        int Units(string t)
        {
            if (Length == null) return t.Length;
            try { return Math.Max(1, Length(t)); }
            catch { return t.Length; }
        }

        /// SET FROM EVIDENCE, ON THE FIRST REAL LINE. The step count of a line
        /// depends on its words, and there is no measurement of how. So this
        /// starts at a figure taken from one measured line and is REPLACED the
        /// moment a real one reports its own. Named rather than hidden because
        /// it is the weakest number here.
        ///
        /// RENAMED WITH THE UNIT, because the question it answers moved. Same
        /// field, different meaning, and a name that still said "character"
        /// would be a number quietly answering something it was not asked —
        /// which CLAUDE.md has a whole paragraph about.
        public double StepsPerUnit { get; private set; } = 4.0;
        public bool StepsPerUnitMeasured { get; private set; }

        /// WHAT THE SECOND HALF OF THE PIPELINE COSTS, which this file could
        /// not express at all until now.
        ///
        /// `StepsPerSecond` measures the text stage: the model choosing sound
        /// tokens, one step at a time. Turning those tokens into samples is a
        /// separate network and a separate wait, and on the one machine that
        /// has run this it was 3.5 seconds of a 7.3-second line. So a
        /// projection built only from the step rate was not slightly optimistic
        /// — it was missing half the answer, and no amount of learning could
        /// have taught it better, because there was nowhere for the number to
        /// go.
        ///
        /// TWO COEFFICIENTS, BECAUSE ONE CANNOT SAY WHETHER A SHORT LINE IS
        /// CHEAP. The decoder does a fixed amount of work before it looks at
        /// the first token; quoting the whole cost as a per-token rate would
        /// promise that a five-word line costs a fifth of a twenty-word one,
        /// which is a different claim and probably false. They are fitted
        /// together by least squares from whole lines this machine has
        /// actually decoded.
        ///
        /// ACCUMULATED RATHER THAN WINDOWED, unlike the step rate. The step
        /// rate is windowed because a machine under load speeds up and slows
        /// down; the decoder's cost is a property of the graph and the card,
        /// and forgetting early lines would buy noise rather than freshness.
        public double DecodeFixedSeconds { get; private set; }
        public double DecodeSecondsPerToken { get; private set; }
        public bool DecodeMeasured { get; private set; }

        /// HOW MANY SOUND TOKENS A STEP YIELDS. Not one: the loop takes a step
        /// for every token it samples, and throws away the ones that are not
        /// sound. The projection counts STEPS and the decoder charges for
        /// TOKENS, so something has to carry between them, and an assumed 1.0
        /// is exactly the kind of quiet conversion this project keeps being
        /// bitten by. It starts at 1.0 because on the only line ever measured
        /// end to end all 86 steps produced a token, and it says out loud that
        /// this is an assumption until a real line replaces it.
        public double TokensPerStep { get; private set; } = 1.0;
        public bool TokensPerStepMeasured { get; private set; }

        double _dn, _dsx, _dsy, _dsxx, _dsxy;

        public int Banked { get; private set; }
        public int Live { get; private set; }
        public int TooSlow { get; private set; }
        public int NoModel { get; private set; }

        /// EVERY ZERO'S DENOMINATOR. `Live == 0` on its own cannot tell "this
        /// machine cannot do it" from "nothing ever asked", and those have
        /// nothing in common.
        public int Asked => Banked + Live + TooSlow + NoModel;

        readonly Queue<double> _rates = new Queue<double>();

        /// Which route this line takes.
        ///
        /// `banked` is whether `VoiceBank` has a recording — the caller looks
        /// it up, because only the Game layer knows what is on disk.
        /// `haveModel` is whether a backend loaded.
        public SpeechRoute Route(string voiceId, string text, bool banked, bool haveModel)
        {
            var t = VoiceBank.Normalise(text);
            if (string.IsNullOrEmpty(voiceId) || t.Length == 0) return SpeechRoute.Nothing;
            if (banked) { Banked++; return SpeechRoute.Banked; }
            if (!haveModel) { NoModel++; return SpeechRoute.NoModel; }

            // THE FIRST LINE ALWAYS GOES THROUGH. With no measurement there is
            // no basis to refuse, and refusing would make the measurement
            // unobtainable — the gate would hold itself shut for ever on the
            // one machine that could have told it otherwise. This is the same
            // shape as a probe that only fires on a lucky run.
            if (StepsPerSecond <= 0) { Live++; return SpeechRoute.Live; }

            if (Projected(t) > PatienceSeconds) { TooSlow++; return SpeechRoute.TooSlow; }
            Live++;
            return SpeechRoute.Live;
        }

        /// How long this text is expected to take on this machine, in seconds,
        /// from the ask to the sound. Zero when nothing has been measured yet.
        ///
        /// BOTH HALVES, WHICH IT DID NOT USED TO BE. This returned the step
        /// loop's time and was compared against the player's patience, so on
        /// the measured machine it answered 3.8 for a line the player waits
        /// 7.3 seconds for. The name never changed and neither did the
        /// comparison; the question quietly did, the moment the decoder became
        /// a thing that runs.
        public double Projected(string text)
        {
            if (StepsPerSecond <= 0) return 0.0;
            var t = VoiceBank.Normalise(text);
            double steps = Units(t) * StepsPerUnit;
            return steps / StepsPerSecond + DecodeSeconds(steps);
        }

        /// The decoder's share, for a line of this many STEPS. Zero until a
        /// real line has been decoded on this machine — so a machine that has
        /// never spoken projects exactly what it projected before, and the
        /// honesty arrives with the evidence rather than ahead of it.
        public double DecodeSeconds(double steps)
        {
            if (!DecodeMeasured) return 0.0;
            double tokens = Math.Max(0.0, steps * TokensPerStep);
            return DecodeFixedSeconds + DecodeSecondsPerToken * tokens;
        }

        /// Fold in one finished decode: how many sound tokens, and how long it
        /// took. Called by whoever ran the decoder, because only that side
        /// holds a clock.
        ///
        /// ONE LENGTH IS NOT A SLOPE, and saying so is the whole of the care
        /// here. Until two lines of DIFFERENT length have been decoded there
        /// is no way to separate the fixed cost from the per-token one, so
        /// this reports the average as a flat cost and a zero slope rather
        /// than inventing a division. A slope drawn through one point is a
        /// number with no evidence in it that looks exactly like one with.
        public void ObservedDecode(int tokens, double seconds)
        {
            if (tokens <= 0 || seconds <= 0) return;
            _dn += 1.0;
            _dsx += tokens;
            _dsy += seconds;
            _dsxx += (double)tokens * tokens;
            _dsxy += tokens * seconds;
            DecodeMeasured = true;
            double denom = _dn * _dsxx - _dsx * _dsx;
            if (_dn < 2.0 || Math.Abs(denom) < 1e-9)
            {
                DecodeFixedSeconds = _dsy / _dn;
                DecodeSecondsPerToken = 0.0;
                return;
            }
            double slope = (_dn * _dsxy - _dsx * _dsy) / denom;
            double flat = (_dsy - slope * _dsx) / _dn;
            // NEITHER COEFFICIENT MAY GO NEGATIVE. Two lines of similar length
            // whose times differ by scheduling noise can fit a line sloping
            // downwards, which would say a longer sentence decodes faster and,
            // extended far enough, that a long one costs nothing. Clamped
            // rather than rejected, because the fit is still the best estimate
            // available and the next line will pull it straight.
            DecodeSecondsPerToken = slope < 0.0 ? 0.0 : slope;
            DecodeFixedSeconds = flat < 0.0 ? 0.0 : flat;
        }

        /// The deadline to hand `SpeechPlan` for this line.
        ///
        /// A LITTLE MORE THAN THE PROJECTION, not the raw patience. A line
        /// projected at 1.2 seconds that is still running at 4 has gone wrong
        /// — the step count ran away, or the machine stalled — and cutting it
        /// at 2.4 frees the slot for the next one instead of spending the
        /// whole budget discovering that. Never below `PatienceSeconds` on the
        /// first lines, when there is nothing to project from.
        /// How many acoustic tokens this line is EXPECTED to produce, for
        /// the streaming follower's no-underrun projection. The same
        /// arithmetic `Deadline` uses, stopped one multiply earlier — an
        /// expectation from measured rates, not a promise; the follower
        /// clamps its remainder so a line that outruns this still refuses
        /// to start early.
        public double ExpectedTokens(string text)
        {
            var t = VoiceBank.Normalise(text);
            return Units(t) * StepsPerUnit * TokensPerStep;
        }

        public double Deadline(string text)
        {
            if (StepsPerSecond <= 0) return PatienceSeconds;
            var t = VoiceBank.Normalise(text);
            double steps = Units(t) * StepsPerUnit;
            double loop = steps / StepsPerSecond;
            if (loop <= 0) return PatienceSeconds;
            // AND THE DECODER STILL HAS TO RUN AFTERWARDS. This bounds the
            // STEP LOOP, so it has to be given what is left of the player's
            // patience rather than all of it — handing over the whole budget
            // spends it before the second half of the work starts. It read
            // `Projected` before, which now includes the decode; leaving it
            // alone would have doubled a number that already had the decode in
            // it and called the result a loop deadline.
            double budget = PatienceSeconds - DecodeSeconds(steps);
            if (budget < 0.5) budget = 0.5;
            return Math.Min(budget, Math.Max(loop * 2.0, 0.5));
        }

        /// Fold a finished line back in, so the next decision is better than
        /// this one was.
        ///
        /// BOTH OUTCOMES TEACH. A line that was cut off still measured a rate
        /// — it took real time and did real steps — and throwing that away
        /// would mean a machine only ever learns from its successes, which is
        /// precisely backwards: the slow machines are the ones whose speed
        /// matters and the ones whose lines get cut.
        public void Observed(SpeechRun run, string text)
        {
            if (run == null || run.Steps <= 0 || run.Seconds <= 0) return;

            _rates.Enqueue(run.Steps / run.Seconds);
            while (_rates.Count > Window) _rates.Dequeue();
            double sum = 0;
            foreach (var r in _rates) sum += r;
            StepsPerSecond = sum / _rates.Count;

            // ONLY A WHOLE LINE TELLS YOU HOW LONG A LINE IS. A run cut short
            // by a deadline or a ceiling stopped for a reason that has nothing
            // to do with the words, so counting its steps against its
            // characters would drag the estimate toward whatever the deadline
            // happened to be — the instrument measuring itself.
            if (run.Stop == SpeechStop.Finished || run.Stop == SpeechStop.Repetition)
            {
                // AND HOW MANY OF THOSE STEPS WERE SOUND, for the same reason
                // and from the same whole lines. A cut-off run's tokens are a
                // fraction of a sentence, so the ratio it reports is about
                // where the deadline fell rather than about the model.
                if (run.Tokens != null && run.Tokens.Length > 0)
                {
                    double got = run.Tokens.Length / (double)run.Steps;
                    TokensPerStep = TokensPerStepMeasured
                        ? TokensPerStep * 0.75 + got * 0.25
                        : got;
                    TokensPerStepMeasured = true;
                }
                var t = VoiceBank.Normalise(text);
                if (t.Length > 0)
                {
                    double observed = run.Steps / (double)Units(t);
                    StepsPerUnit = StepsPerUnitMeasured
                        ? StepsPerUnit * 0.75 + observed * 0.25
                        : observed;
                    StepsPerUnitMeasured = true;
                }
            }
        }

        /// One line for the verdict, so a run says what live speech did rather
        /// than leaving it to be inferred.
        ///
        /// NO SPACES IN A VALUE — `verdict.txt` is space-separated `key=value`
        /// and a value with a space in it silently truncates every reader.
        ///
        /// AND AN UNMEASURED RATE SAYS SO RATHER THAN PRINTING 0.00. This
        /// printed a zero for a machine that had never generated a line, which
        /// is rule 3b in the file that talks about rule 3b: `0.00 steps a
        /// second` reads as a measurement of a very slow card, and is in fact
        /// the absence of any measurement at all. Those have opposite next
        /// actions — one is "the model is too slow here", the other is "the
        /// model never ran".
        public string Verdict()
        {
            return string.Format(
                "speechAsked={0} speechBanked={1} speechLive={2} speechTooSlow={3} "
                + "speechNoModel={4} speechStepsPerSec={5} speechStepsPerUnit={6} "
                + "speechDecodeSec={7}",
                Asked, Banked, Live, TooSlow, NoModel,
                StepsPerSecond > 0 ? StepsPerSecond.ToString("0.00") : "unmeasured",
                StepsPerUnitMeasured
                    ? StepsPerUnit.ToString("0.00")
                    : "unmeasured",
                // BOTH COEFFICIENTS IN ONE VALUE, joined by a slash because a
                // space would truncate the line for every reader of
                // `verdict.txt`. Printed together because either alone is a
                // half-answer: a fixed cost with no slope beside it reads as
                // "every line costs this", which is the claim the two-term fit
                // exists to avoid making.
                DecodeMeasured
                    ? DecodeFixedSeconds.ToString("0.00") + "/"
                      + DecodeSecondsPerToken.ToString("0.0000")
                    : "unmeasured");
        }

        public void Reset()
        {
            Banked = Live = TooSlow = NoModel = 0;
            StepsPerSecond = 0;
            StepsPerUnit = 4.0;
            StepsPerUnitMeasured = false;
            DecodeFixedSeconds = DecodeSecondsPerToken = 0.0;
            DecodeMeasured = false;
            TokensPerStep = 1.0;
            TokensPerStepMeasured = false;
            _dn = _dsx = _dsy = _dsxx = _dsxy = 0.0;
            _rates.Clear();
        }
    }
}
