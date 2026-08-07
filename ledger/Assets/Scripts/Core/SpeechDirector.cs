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

        /// SET FROM EVIDENCE, ON THE FIRST REAL LINE. The step count of a line
        /// depends on its words, and there is no measurement of how — 97 steps
        /// was one line, and nobody has counted steps against characters. So
        /// this starts at a figure taken from that one line (97 steps for 22
        /// characters, rounded down to 4) and is REPLACED the moment a real
        /// line reports its own. Named rather than hidden because it is the
        /// weakest number here.
        public double StepsPerCharacter { get; private set; } = 4.0;
        public bool StepsPerCharacterMeasured { get; private set; }

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

        /// How long this text is expected to take on this machine, in seconds.
        /// Zero when nothing has been measured yet.
        public double Projected(string text)
        {
            if (StepsPerSecond <= 0) return 0.0;
            var t = VoiceBank.Normalise(text);
            return (t.Length * StepsPerCharacter) / StepsPerSecond;
        }

        /// The deadline to hand `SpeechPlan` for this line.
        ///
        /// A LITTLE MORE THAN THE PROJECTION, not the raw patience. A line
        /// projected at 1.2 seconds that is still running at 4 has gone wrong
        /// — the step count ran away, or the machine stalled — and cutting it
        /// at 2.4 frees the slot for the next one instead of spending the
        /// whole budget discovering that. Never below `PatienceSeconds` on the
        /// first lines, when there is nothing to project from.
        public double Deadline(string text)
        {
            double projected = Projected(text);
            if (projected <= 0) return PatienceSeconds;
            return Math.Min(PatienceSeconds, Math.Max(projected * 2.0, 0.5));
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
                var t = VoiceBank.Normalise(text);
                if (t.Length > 0)
                {
                    double observed = run.Steps / (double)t.Length;
                    StepsPerCharacter = StepsPerCharacterMeasured
                        ? StepsPerCharacter * 0.75 + observed * 0.25
                        : observed;
                    StepsPerCharacterMeasured = true;
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
                + "speechNoModel={4} speechStepsPerSec={5} speechStepsPerChar={6}",
                Asked, Banked, Live, TooSlow, NoModel,
                StepsPerSecond > 0 ? StepsPerSecond.ToString("0.00") : "unmeasured",
                StepsPerCharacterMeasured
                    ? StepsPerCharacter.ToString("0.00")
                    : "unmeasured");
        }

        public void Reset()
        {
            Banked = Live = TooSlow = NoModel = 0;
            StepsPerSecond = 0;
            StepsPerCharacter = 4.0;
            StepsPerCharacterMeasured = false;
            _rates.Clear();
        }
    }
}
