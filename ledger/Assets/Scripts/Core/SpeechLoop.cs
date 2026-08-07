using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// THE PART OF LIVE SPEECH THAT CANNOT BE CONVERTED.
    ///
    /// The voice model is three networks and all three now convert to ONNX and
    /// run on a gamer's card. What does NOT convert is the loop between them:
    /// the text stage emits one token at a time and decides for itself when
    /// the sentence is over, so the number of steps depends on the words. It
    /// was 97 for one measured line and a different number for the next.
    ///
    /// That is why the graph contains ONE step. A tracer walking a
    /// data-dependent loop bakes the count it happened to see as a constant —
    /// it exports without complaint, loads, runs, returns the right shape, and
    /// is wrong for every line but the one it was traced on. The stand-in in
    /// `tools/voice-live/fixture.py` reproduces exactly that, because it is
    /// the likeliest way this model ends up "converted" and useless.
    ///
    /// So the loop lives here, in C#, and this file is the whole of it.
    ///
    /// EVERY CONSTANT BELOW WAS READ OUT OF THE MODEL, NOT REMEMBERED. The
    /// first draft of this file had four of them wrong and was missing a
    /// mechanism entirely — it used top-p 0.8 where the model ships 1.0, had
    /// no `min_p` at all (which is the filter actually doing the work once
    /// top-p is disabled), capped at 600 steps against a real 1000, and knew
    /// nothing about classifier-free guidance, which runs the transformer
    /// TWICE per step and combines the two. Every one of those would have
    /// produced speech: differently-voiced, subtly wrong speech, with no error
    /// anywhere. The sources are named per constant so the next person can
    /// check them in a minute instead of trusting this paragraph.
    ///
    /// WHY CORE AND NOT THE GAME LAYER. The Game layer does not compile in the
    /// container this is written in; a type error there is invisible until a
    /// ~28-minute Windows build. Core compiles in seconds and has 3,343 tests.
    /// Sampling, stopping, budget and determinism are pure logic with no Unity
    /// in them, so they belong where they can be run. What genuinely needs the
    /// engine — an inference session, a GPU, a byte buffer — is behind
    /// `ISpeechBackend` and is the only part that has to wait for a build.
    ///
    /// WHAT THIS IS NOT. It is not a replacement for the recorded bank.
    /// `VoiceBank` holds 2,010 lines that are already generated, instant and
    /// free; anything in it should come from it. This is for the lines that
    /// were never written down — which is the entire point of putting a voice
    /// model on the player's machine rather than a folder of wav files.
    ///
    /// AND A LIVE LINE CAN NEVER BYTE-MATCH ITS BAKED TWIN, which is worth
    /// saying plainly because the reasonable assumption is the opposite.
    /// `VoiceBank` promises that regenerating the bank yields identical takes,
    /// and it does — because the same Python sampler is re-run with the same
    /// seed. This sampler is a different one in a different language. Same
    /// seed, same model, different draw. So a line is EITHER banked OR live,
    /// never checked against both, and the caller decides by asking the bank
    /// first.
    public enum SpeechStop
    {
        /// The model emitted its stop token. The only outcome that yields a
        /// whole utterance.
        Finished = 0,
        /// The step ceiling was reached with no stop token. The utterance is
        /// cut mid-word.
        StepCeiling = 1,
        /// The deadline passed. Also cut mid-word, and the reason is the
        /// player's hardware rather than the model.
        Deadline = 2,
        /// The backend could not produce logits — no session, no device, a
        /// driver that went away mid-line.
        BackendFailed = 3,
        /// Nothing to say: no voice, no text, or a text the tokeniser emptied.
        Nothing = 4,
        /// The model locked into a repeated token and was stopped. This is the
        /// model's own runaway guard, not ours — see `SpeechPlan.StopOnRepeat`.
        Repetition = 5,
    }

    /// The numbers that come out of the model rather than out of a decision.
    ///
    /// `models/t3/modules/t3_config.py`, read rather than recalled.
    public static class SpeechVocab
    {
        /// The width of the logits the model produces.
        public const int Size = 8194;
        /// Start of speech. Sampled mid-line it is dropped from the audio, but
        /// still fed back to the model — see `SpeechLoop.Run`.
        public const int Start = 6561;
        /// End of speech. Ends the line.
        public const int Stop = 6562;
        /// Tokens at or above `Start` are not sound. The model's own pipeline
        /// filters them with `speech_tokens[speech_tokens < 6561]` after
        /// generation, which is where this bound comes from.
        public const int FirstNonAcoustic = 6561;

        public static bool IsAcoustic(int token) => token >= 0 && token < FirstNonAcoustic;
    }

    /// The inference session, from Core's side of the wall.
    ///
    /// EVERY METHOD RETURNS SUCCESS RATHER THAN THROWING. A graphics driver
    /// resetting mid-sentence is a thing that happens on the machines this
    /// ships to, and it must degrade to a quiet character rather than to an
    /// exception crossing a frame boundary. The loop turns a false into
    /// `BackendFailed` and the caller falls back to the bank.
    ///
    /// The caller owns the logits buffer, so a 97-step line allocates once
    /// rather than 97 times.
    public interface ISpeechBackend
    {
        /// How many speech tokens the model can emit — `SpeechVocab.Size` for
        /// chatterbox. Asked rather than assumed so a different model can be
        /// dropped in behind this interface.
        int VocabSize { get; }

        /// The token that ends an utterance.
        int StopToken { get; }

        /// HOW MANY ROWS OF LOGITS EACH CALL PRODUCES, and this is classifier-
        /// free guidance rather than a batching detail.
        ///
        /// chatterbox runs the transformer on TWO sequences at once — the text
        /// as given, and the text with the conditioning removed — then steers
        /// away from the unconditional one:
        ///
        ///     logits = cond + cfg_weight * (cond - uncond)
        ///
        /// It is what makes the model actually say the words rather than
        /// mumble in the right voice, and it doubles the per-step cost, which
        /// is a latency fact the estimates have to carry. It lives out here in
        /// the open rather than hidden inside the backend so the combination
        /// is testable without a GPU.
        ///
        /// 1 means the backend has already combined them, or the model has no
        /// guidance. `logits` must be `Rows * VocabSize` long.
        int Rows { get; }

        /// Prime the model with a voice and a sentence, and produce the logits
        /// for the first token. This is the expensive call — it carries the
        /// reference clip and the whole text — and it is where the key/value
        /// cache is created.
        bool Begin(string voiceId, string text, float[] logits);

        /// One step: feed back the token just chosen, get the next logits.
        /// The backend keeps the cache; Core never sees a tensor.
        bool Next(int token, float[] logits);

        /// Drop the cache. Always called, including after a failure.
        void Release();

        /// TOKENS INTO SOUND — the second half of the model, and the second
        /// half of the cost.
        ///
        /// The loop above produces speech TOKENS, which are not audio: the
        /// flow decoder turns them into a spectrogram and the vocoder turns
        /// that into samples. Measured at 1.43s against the text stage's 8.3s,
        /// so it is a sixth of a line rather than an afterthought.
        ///
        /// Returns null when it fails, like everything else here, because a
        /// driver resetting between the two halves is the same event as one
        /// resetting during the first.
        ///
        /// Mono, at the model's own rate — 24 kHz for chatterbox, read from
        /// `s3gen/const.py`. A wrong rate is a chipmunk rather than an error,
        /// so the caller names it rather than guessing.
        float[] Decode(int[] tokens);
    }

    /// How to run one line.
    ///
    /// THE SAMPLING NUMBERS ARE THE MODEL'S, NOT MINE. Each carries where it
    /// was read from, because the first version of this class invented four of
    /// them and they all looked reasonable. Changing one changes how the voice
    /// sounds, which makes it a casting decision rather than a tuning knob.
    public class SpeechPlan
    {
        /// `tts.py generate(temperature=0.8)`. Applied AFTER the repetition
        /// penalty and BEFORE the two filters — the order matters and it is
        /// the order in `t3.py`'s loop.
        public double Temperature = 0.8;

        /// `tts.py generate(repetition_penalty=1.2)`. Applied to raw logits,
        /// once per distinct token already generated.
        public double RepetitionPenalty = 1.2;

        /// `tts.py generate(min_p=0.05)`. Keep only tokens at least this
        /// fraction as likely as the likeliest one. THIS IS THE FILTER THAT
        /// ACTUALLY RUNS: top-p ships disabled, so a version of this sampler
        /// with nucleus sampling and no min-p — which is what the first draft
        /// was — filters on a rule the model does not use.
        public double MinP = 0.05;

        /// `tts.py generate(top_p=1.0)`, which is off. Kept because the field
        /// is real and someone will want it, and because a 1.0 that says "off"
        /// in the open is better than a filter silently absent.
        public double TopP = 1.0;

        /// `tts.py generate(cfg_weight=0.5)`. Only read when `Rows` is 2.
        public double CfgWeight = 0.5;

        /// `tts.py`: `max_new_tokens=1000`. A ceiling, not a target — 97 steps
        /// was one measured line and the count depends on the words.
        public int StepCeiling = 1000;

        /// Below this, an utterance is a click rather than a word. A model
        /// that emits its stop token immediately has failed at something, and
        /// speaking the result would be worse than staying quiet.
        public int MinSteps = 4;

        /// A RUNAWAY GUARD THE ENGLISH MODEL DOES NOT HAVE. Off by default,
        /// and that default is a correction.
        ///
        /// `alignment_stream_analyzer.py` forces an end-of-speech token when
        /// the last two tokens are equal. I read it, implemented it, defaulted
        /// it ON, and wrote a paragraph elsewhere calling the attention-based
        /// half of the same analyzer a "known gap" in the export.
        ///
        /// Then I read the line that CONSTRUCTS it:
        ///
        ///     if self.hp.is_multilingual:
        ///         alignment_stream_analyzer = AlignmentStreamAnalyzer(...)
        ///
        /// and `is_multilingual` is `text_tokens_dict_size == 2454`. The
        /// English model is 704 — which is exactly the vocabulary size the
        /// probe read off Jafar's install. So for the model this game ships,
        /// the analyzer is None and NONE of it runs.
        ///
        /// That makes the "known gap" not a gap, and makes this guard an
        /// EXTRA one: on by default it would end a line at the first repeated
        /// token, and two identical tokens in a row at 25 Hz is an ordinary
        /// thing in held vowels and silence. A voice cut short mid-word, for a
        /// rule the model does not apply.
        ///
        /// Kept rather than deleted, because the multilingual model does use
        /// it and this is what it does; the code checks the last TWO despite
        /// its own log line saying "3x", and the code is what runs.
        public bool StopOnRepeat = false;

        /// How long the whole line may take, in seconds. Zero disables it.
        ///
        /// MEASURED, AND IT IS WHY THIS FIELD EXISTS. On the machine this was
        /// developed against, one line costs about 9 seconds against roughly
        /// 3.2 seconds of speech. That is fine for something muttered across
        /// the street and unusable for a reply to the player, so the caller
        /// sets this per situation and the loop reports which lines could not
        /// be afforded.
        ///
        /// NOT A PROJECTION, DELIBERATELY. The obvious improvement is to give
        /// up early — at step 20, if the rate says we will not finish in time,
        /// stop and fall back while the fallback is still useful. That needs a
        /// steps-per-character estimate and there is no measurement of one
        /// yet, so this checks elapsed time instead, and `SpeechRun` records
        /// seconds-per-step so the estimate can come from evidence later
        /// rather than from me choosing a number now.
        public double DeadlineSeconds = 0.0;
    }

    /// What one line cost and whether it can be spoken.
    public class SpeechRun
    {
        /// The acoustic tokens, ready for the decoder. Special tokens are
        /// already filtered out.
        public int[] Tokens = new int[0];
        public SpeechStop Stop = SpeechStop.Nothing;
        /// Sampling steps taken, INCLUDING ones whose token was filtered out
        /// of `Tokens`. This is the number that cost time, so it is the number
        /// the latency estimate has to use — `Tokens.Length` is a different
        /// question and answering the first with the second is how a rate ends
        /// up flattering.
        public int Steps;
        public double Seconds;

        /// The measurement the projection above will eventually be built from.
        /// Zero when nothing ran.
        public double SecondsPerStep => Steps > 0 ? Seconds / Steps : 0.0;

        /// WHETHER TO ACTUALLY PLAY THIS, and it is stricter than it looks.
        ///
        /// Only a stop token yields a whole sentence. Every other outcome
        /// leaves the utterance cut mid-word, and a character who stops
        /// halfway through a word reads as a bug to a player, whereas one who
        /// says nothing reads as a person who did not feel like talking. So a
        /// truncated line is thrown away and the caller falls back, rather
        /// than being played because it was expensive to produce.
        ///
        /// A repetition stop counts as finished: that is the model deciding it
        /// is done, the same as an end-of-speech token, and its output up to
        /// that point is a whole utterance.
        public bool Usable =>
            (Stop == SpeechStop.Finished || Stop == SpeechStop.Repetition)
            && Tokens.Length > 0;
    }

    public static class SpeechLoop
    {
        /// A GAP I REPORTED AND THEN DISPROVED, kept because the reasoning
        /// is the useful part.
        ///
        /// `alignment_stream_analyzer.py` reads the transformer's cross
        /// attention every step and uses it to suppress an early stop, to cut
        /// a hallucinated tail, and to catch a repetition. None of that
        /// survives the export, because the graph does not carry attention —
        /// so I wrote it down as a known gap with a known cost.
        ///
        /// It is not a gap. The analyzer is only constructed
        /// `if self.hp.is_multilingual`, and that is
        /// `text_tokens_dict_size == 2454`; the English model is 704, which is
        /// exactly the vocabulary the probe read off Jafar's install. For the
        /// model this game ships it is None and never runs, so the exported
        /// graph is missing nothing the original had.
        ///
        /// The lesson is the one this project keeps paying for: I read the
        /// class and not the line that decides whether it is built. A
        /// mechanism that exists in the source is not a mechanism that runs.
        /// If a multilingual voice is ever used, this becomes a real gap
        /// again and `StopOnRepeat` covers one third of it.
        public static SpeechRun Run(ISpeechBackend backend, string voiceId, string text,
                                    SpeechPlan plan = null, Func<double> nowSeconds = null)
        {
            var run = new SpeechRun();
            if (backend == null) { run.Stop = SpeechStop.BackendFailed; return run; }

            // TWO NORMALISATIONS, AND THEY ARE NOT THE SAME ONE.
            //
            // `VoiceBank.Normalise` decides the clip NAME and therefore the
            // seed: collapse whitespace, keep case, because "no" and "NO" are
            // two performances. `SpeechText.Normalise` is the model's own
            // `punc_norm` and decides what it is TOLD TO SAY: capitalised,
            // punctuation swapped for what it was trained on, a full stop
            // added. Feeding the seed's version to the model would hand it
            // characters it has barely seen; seeding off the model's version
            // would give a line a different name depending on whether it
            // already ended in a full stop.
            var seedText = VoiceBank.Normalise(text);
            var spoken = SpeechText.Normalise(text);
            if (string.IsNullOrEmpty(voiceId) || string.IsNullOrEmpty(seedText)
                || string.IsNullOrEmpty(spoken))
            {
                run.Stop = SpeechStop.Nothing;
                return run;
            }

            plan = plan ?? new SpeechPlan();
            int vocab = backend.VocabSize;
            int rows = backend.Rows < 1 ? 1 : backend.Rows;
            if (vocab <= 0) { run.Stop = SpeechStop.BackendFailed; return run; }

            // THE SAME SEED THE BANK WOULD HAVE USED. `VoiceBank.Seed` is the
            // project's existing answer to "the same line must sound the same
            // twice", and reaching for a fresh seed here would have given the
            // same character a different delivery every time they repeated
            // themselves — which is the exact fault audit item 5 was about.
            var rng = new Random(VoiceBank.Seed(voiceId, seedText));

            var raw = new float[vocab * rows];
            var logits = rows > 1 ? new double[vocab] : null;
            var tokens = new List<int>(128);
            var seen = new HashSet<int>();
            var scratch = new Scratch(vocab);
            int previous = -1;

            double t0 = nowSeconds != null ? nowSeconds() : Clock();
            try
            {
                if (!backend.Begin(voiceId, spoken, raw))
                {
                    run.Stop = SpeechStop.BackendFailed;
                    return run;
                }

                while (true)
                {
                    if (run.Steps >= plan.StepCeiling) { run.Stop = SpeechStop.StepCeiling; break; }

                    int token = Pick(Guided(raw, logits, vocab, rows, plan.CfgWeight),
                                     vocab, seen, plan, rng, scratch);
                    run.Steps++;

                    // THE STOP TOKEN IS NOT KEPT. It is punctuation for the
                    // loop, not a sound. The model's own pipeline reaches the
                    // same place by a longer route — it appends the token,
                    // then `drop_invalid_tokens` cuts the list at the first
                    // end-of-speech and `speech_tokens < 6561` removes the
                    // rest — so not adding it here is the same output.
                    if (token == backend.StopToken)
                    {
                        // A model that stops immediately has not said
                        // anything. Treated as a failure to speak rather than
                        // as a very short line, because the alternative is a
                        // character emitting a click and looking broken.
                        run.Stop = run.Steps >= plan.MinSteps
                            ? SpeechStop.Finished : SpeechStop.StepCeiling;
                        break;
                    }

                    // FED BACK EVEN WHEN IT IS NOT KEPT, and this is the one
                    // easy thing to get wrong here. The model's history must
                    // contain every token it sampled, including a stray
                    // start-of-speech mid-line; only the AUDIO drops it. Feed
                    // back a filtered stream and the model is being told it
                    // said something it did not, from that step onward.
                    if (SpeechVocab.IsAcoustic(token)) tokens.Add(token);
                    seen.Add(token);

                    if (plan.StopOnRepeat && run.Steps >= 3
                        && token == previous && previous >= 0)
                    {
                        run.Stop = SpeechStop.Repetition;
                        break;
                    }
                    previous = token;

                    // CHECKED AFTER THE STEP, NOT BEFORE. Checking first means
                    // a deadline of zero-plus-epsilon returns with no steps at
                    // all and no measurement, and the field that exists to
                    // tell us how slow the machine is would be empty exactly
                    // on the machines that are slow.
                    double now = nowSeconds != null ? nowSeconds() : Clock();
                    run.Seconds = now - t0;
                    if (plan.DeadlineSeconds > 0 && run.Seconds >= plan.DeadlineSeconds)
                    {
                        run.Stop = SpeechStop.Deadline;
                        break;
                    }

                    if (!backend.Next(token, raw))
                    {
                        run.Stop = SpeechStop.BackendFailed;
                        break;
                    }
                }
            }
            finally
            {
                double end = nowSeconds != null ? nowSeconds() : Clock();
                run.Seconds = end - t0;
                backend.Release();
            }

            run.Tokens = tokens.ToArray();
            return run;
        }

        /// Classifier-free guidance: steer the conditional logits away from
        /// the unconditional ones. Returns `raw` untouched when there is only
        /// one row, so the single-row path allocates and copies nothing.
        ///
        /// `t3.py`: `logits = cond + cfg * (cond - uncond)`.
        internal static Array Guided(float[] raw, double[] into, int vocab, int rows, double cfg)
        {
            if (rows < 2 || into == null) return raw;
            for (int i = 0; i < vocab; i++)
            {
                double cond = raw[i], uncond = raw[vocab + i];
                into[i] = cond + cfg * (cond - uncond);
            }
            return into;
        }

        /// The sampler's working memory, allocated once per line rather than
        /// once per step.
        ///
        /// NOT PREMATURE. The vocabulary is 8,194 wide and a line is around a
        /// hundred steps, so a `new double[vocab]` inside the loop is three
        /// arrays a step — about 19 MB of garbage for one sentence. In a game
        /// that is not a cost, it is a stutter: the collection lands on some
        /// frame the player is looking at. The arrays do not vary in size
        /// within a line, so there is nothing to gain by reallocating them.
        internal sealed class Scratch
        {
            public double[] Scaled;
            /// Sorted descending, and NOT normalised — they are divided by
            /// `KeptMass` only when somebody asks for a share.
            public double[] Probs;
            public int[] Order;
            /// How many of `Order` survived the filters.
            public int Keep;
            /// The total weight of those survivors, which is what a draw is
            /// taken against.
            public double KeptMass;

            public Scratch(int vocab)
            {
                Scaled = new double[vocab];
                Probs = new double[vocab];
                Order = new int[vocab];
            }
        }

        /// One token, by the model's own order of operations:
        /// repetition penalty, temperature, min-p, top-p, softmax, draw.
        ///
        /// SEPARATE AND INTERNAL SO IT CAN BE TESTED ON ITS OWN. The loop
        /// around it needs a backend; this needs an array, so the sampler's
        /// edge cases — one live token, all-equal logits, a penalty that
        /// changes the order — are checkable without standing up a model.
        ///
        /// Takes `Array` so the guided (double) and unguided (float) paths
        /// share one implementation rather than becoming the same idea written
        /// twice, which is the fault this project keeps paying for.
        static int Shape(Array source, int vocab, HashSet<int> seen,
                         SpeechPlan plan, Scratch scratch)
        {
            var asFloat = source as float[];
            var asDouble = source as double[];

            // Work in doubles from here. A softmax over float logits
            // underflows to zero for the tail, and the tail is what the
            // filters are deciding about.
            var scaled = scratch.Scaled;
            double temp = plan.Temperature > 0 ? plan.Temperature : 1.0;
            double penalty = plan.RepetitionPenalty > 0 ? plan.RepetitionPenalty : 1.0;

            double max = double.NegativeInfinity;
            for (int i = 0; i < vocab; i++)
            {
                double v = asDouble != null ? asDouble[i] : asFloat[i];
                // THE PENALTY DIVIDES A POSITIVE LOGIT AND MULTIPLIES A
                // NEGATIVE ONE, which is what HuggingFace's
                // `RepetitionPenaltyLogitsProcessor` does. Dividing throughout
                // would make an already unlikely token MORE likely — -8
                // becomes -6.7 — so the penalty would reward exactly the
                // tokens it is meant to discourage, for the whole negative
                // half of the range, which is most of it.
                if (seen != null && penalty != 1.0 && seen.Contains(i))
                    v = v > 0 ? v / penalty : v * penalty;
                v /= temp;
                scaled[i] = v;
                if (v > max) max = v;
            }

            var order = scratch.Order;
            for (int i = 0; i < vocab; i++) order[i] = i;
            Array.Sort(order, (a, b) => scaled[b].CompareTo(scaled[a]));

            double total = 0.0;
            var probs = scratch.Probs;
            for (int i = 0; i < vocab; i++)
            {
                double p = Math.Exp(scaled[order[i]] - max);
                probs[i] = p;
                total += p;
            }
            if (total <= 0 || double.IsNaN(total) || double.IsInfinity(total))
            {
                // Degenerate logits: keep the argmax alone, so the draw below
                // has exactly one thing to land on.
                scratch.Keep = 1;
                scratch.KeptMass = 1.0;
                probs[0] = 1.0;
                return -1;
            }

            // MIN-P FIRST, THEN TOP-P, because that is the order in `t3.py`
            // and the two do not commute. Min-p keeps everything at least
            // `MinP` as likely as the likeliest token — a relative floor, so
            // it widens on a flat distribution and tightens on a confident
            // one, which is why it survives where a fixed nucleus does not.
            int keep = vocab;
            if (plan.MinP > 0 && plan.MinP <= 1.0)
            {
                double floor = plan.MinP * probs[0];   // probs is in sorted order
                keep = 0;
                while (keep < vocab && probs[keep] >= floor) keep++;
            }

            // Top-p over what min-p left. ALWAYS AT LEAST ONE token, or a
            // TopP of zero — or a distribution whose top token already exceeds
            // it — leaves nothing to draw from and the line dies on a
            // configuration value.
            double kept = 0.0;
            for (int i = 0; i < keep; i++) kept += probs[i];
            if (plan.TopP > 0 && plan.TopP < 1.0)
            {
                double want = plan.TopP * kept;
                double acc = 0.0;
                int n = 0;
                while (n < keep)
                {
                    acc += probs[n];
                    n++;
                    if (acc >= want) break;
                }
                keep = n;
                kept = acc;
            }
            if (keep < 1) { keep = 1; kept = probs[0]; }

            scratch.Keep = keep;
            scratch.KeptMass = kept;
            return -1;      // the caller draws; see Pick
        }

        /// THE SURVIVING TOKENS AND THEIR SHARE, for checking this sampler
        /// against the one it copies.
        ///
        /// `tools/voice-live/sampler-reference.py` runs chatterbox's actual
        /// HuggingFace processors over fixed logits and prints which tokens
        /// live and with what weight. This returns the same thing from the C#
        /// side, so the two can be compared as numbers rather than as
        /// behaviour that looks about right.
        ///
        /// THE DRAW IS DELIBERATELY NOT COMPARED. Python and C# have different
        /// random generators, so the same seed picks differently and always
        /// will — which is why a live line can never byte-match a baked one.
        /// The distribution is the part that can be identical, and it is the
        /// whole of the sampler.
        internal static void Distribution(Array source, int vocab, HashSet<int> seen,
                                          SpeechPlan plan, out int[] kept, out double[] weights)
        {
            var scratch = new Scratch(vocab);
            Shape(source, vocab, seen, plan, scratch);
            kept = new int[scratch.Keep];
            weights = new double[scratch.Keep];
            for (int i = 0; i < scratch.Keep; i++)
            {
                kept[i] = scratch.Order[i];
                weights[i] = scratch.Probs[i] / scratch.KeptMass;
            }
        }

        /// One token: shape the distribution, then draw from it.
        internal static int Pick(Array source, int vocab, HashSet<int> seen,
                                 SpeechPlan plan, Random rng, Scratch scratch = null)
        {
            scratch = scratch ?? new Scratch(vocab);
            Shape(source, vocab, seen, plan, scratch);

            double draw = rng.NextDouble() * scratch.KeptMass;
            double walk = 0.0;
            for (int i = 0; i < scratch.Keep; i++)
            {
                walk += scratch.Probs[i];
                if (draw <= walk) return scratch.Order[i];
            }
            // Floating-point accumulation can leave `draw` a hair past the
            // end. The last token of the kept set is the right answer there,
            // and falling off the loop with no return would not be.
            return scratch.Order[scratch.Keep - 1];
        }

        static double Clock()
        {
            return DateTime.UtcNow.Ticks / (double)TimeSpan.TicksPerSecond;
        }
    }
}
