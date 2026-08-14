using System;
using System.Collections.Generic;
using System.Diagnostics;
using Ledger.Core;
using Ledger.Game;

namespace Ledger.Bench
{
    /// THE RESIDENCY QUESTION, ASKED OF THE REAL MACHINE.
    ///
    /// Two claims have to hold before the bound path in `OnnxSpeech` is worth
    /// anything, and neither can be checked in the container this was written
    /// in:
    ///
    ///   CORRECT — the bound path must produce the same logits as the host
    ///   path. Same graph, same provider, same inputs: any real difference is
    ///   the binding feeding the wrong tensor somewhere, and wrong tensors
    ///   here are fluent wrong speech with no error anywhere. Checked by
    ///   running both paths through ONE session and comparing every float.
    ///
    ///   FASTER — the whole point. The host path measured 31.8ms flat +
    ///   142us/position of cache round-trip; if binding does not flatten
    ///   that slope, it is complexity with no product. Checked by timing
    ///   steps at the same positions the python probe used, so the numbers
    ///   line up with `step-report.txt` history.
    ///
    /// EVERY NUMBER PRINTS AS key=value WITH NO SPACES IN THE VALUE, because
    /// these lines get read back by the same habits that read verdicts, and
    /// a space in a value silently truncates every reader (CLAUDE.md).
    static class Program
    {
        static int Main(string[] args)
        {
            string models = null, conds = null, tokenizer = null;
            string voice = "rocco";
            bool shortSet = false;
            bool sweep = false;
            int repeat = 0;
            // The sweep's nine-word line, so these numbers read against the
            // sweep's and the probe's. The driver passes it explicitly; this
            // default only covers running the bench by hand.
            string text = "Seen the van again. Thursday, same as last Thursday.";
            int[] positions = { 10, 100, 200, 400 };
            int window = 12;
            for (int i = 0; i + 1 < args.Length; i += 2)
            {
                switch (args[i])
                {
                    case "--models": models = args[i + 1]; break;
                    case "--conds": conds = args[i + 1]; break;
                    case "--tokenizer": tokenizer = args[i + 1]; break;
                    case "--voice": voice = args[i + 1]; break;
                    case "--short": shortSet = args[i + 1] != "0"; break;
                    case "--sweep": sweep = args[i + 1] != "0"; break;
                    case "--repeat": repeat = int(args[i + 1]); break;
                    case "--text": text = args[i + 1]; break;
                    case "--window": window = int.Parse(args[i + 1]); break;
                    case "--positions":
                        var parts = args[i + 1].Split(',');
                        positions = new int[parts.Length];
                        for (int p = 0; p < parts.Length; p++)
                            positions[p] = int.Parse(parts[p]);
                        break;
                    default:
                        Console.WriteLine("BENCH: unknown flag " + args[i]);
                        return 2;
                }
            }
            if (models == null || conds == null || tokenizer == null)
            {
                Console.WriteLine("BENCH: need --models --conds --tokenizer");
                return 2;
            }

            string why;
            var tok = SpeechTokenizer.Load(
                System.IO.File.ReadAllText(tokenizer), out why);
            if (tok == null) { Console.WriteLine("BENCH: tokenizer: " + why); return 1; }

            var condFile = System.IO.Path.Combine(conds, voice + ".bin");
            if (!System.IO.File.Exists(condFile))
            { Console.WriteLine("BENCH: no voice at " + condFile); return 1; }
            var cond = VoiceConditionals.Load(
                System.IO.File.ReadAllBytes(condFile), out why);
            if (cond == null) { Console.WriteLine("BENCH: voice: " + why); return 1; }

            // THE RESOLVER READ THE ID. IT USED TO IGNORE IT, AND THAT IS THE
            // BUG JAFAR'S EARS FOUND WHEN EVERY NUMBER SAID OTHERWISE.
            //
            // This was `id => cond` — a lambda that took the voice id and
            // returned the ONE conditioning loaded at startup, whatever was
            // asked for. So the five-line take spoke every line as Rocco
            // while the log printed "line 2 ada" and "line 3 michelle" beside
            // them, because those strings were the voice REQUESTED and
            // nothing checked that anything used them. He said "all lines are
            // by the same voice" and he was right against three log lines
            // asserting otherwise.
            //
            // It is the project's oldest shape — a label describing an
            // intention rather than a measurement — and the cheap repair is
            // the same every time: make the thing report what it DID. The
            // per-line output now prints the id the resolver actually served.
            var loaded = new System.Collections.Generic.Dictionary<string, VoiceConditionals>();
            var missing = new System.Collections.Generic.HashSet<string>();
            loaded[voice] = cond;
            Func<string, VoiceConditionals> resolve = id =>
            {
                if (string.IsNullOrEmpty(id)) return null;
                VoiceConditionals have;
                if (loaded.TryGetValue(id, out have)) return have;
                // A voice asked for once and absent is absent for good; the
                // set stops a missing file being re-read and re-reported on
                // every line of a long take.
                if (missing.Contains(id)) return null;
                var path = System.IO.Path.Combine(conds, id + ".bin");
                if (!System.IO.File.Exists(path))
                {
                    missing.Add(id);
                    Console.WriteLine("BENCH: no conditioning for '" + id
                                      + "' at " + path);
                    return null;
                }
                string w;
                var got = VoiceConditionals.Load(System.IO.File.ReadAllBytes(path), out w);
                if (got == null)
                {
                    missing.Add(id);
                    Console.WriteLine("BENCH: voice '" + id + "' unreadable: " + w);
                    return null;
                }
                loaded[id] = got;
                return got;
            };

            var backend = OnnxSpeech.Open(models, resolve, s => tok.Encode(s),
                                          out why);
            if (backend == null) { Console.WriteLine("BENCH: open: " + why); return 1; }

            using (backend)
            {
                // ROWS MAY BE UNKNOWN UNTIL THE GRAPH SPEAKS. A dynamic
                // export declares no row count, so the backend learns it
                // from the first real odds — until then `Rows` is 0 and a
                // width computed from it would be an empty array the
                // prefill silently under-fills. One row is the floor: the
                // guided export drives two and writes into the same buffer
                // sized by VocabSize, so asking for two is safe either way.
                // SIZED FROM THE GRAPH, AND CORRECTED BY IT IF THE GRAPH
                // IS OLD. `Rows` is authoritative once the export stamps
                // `ledger.rows`; a graph exported before that leaves it 0,
                // and the honest move is to try, read the refusal, and use
                // the number the graph itself named — the refusal message
                // carries it because a short read was made a failure rather
                // than a partial success.
                int rows = backend.Rows > 0 ? backend.Rows : 1;
                int width = rows * backend.VocabSize;
                var a = new float[width];
                var b = new float[width];
                const int feed = 1234;      // any acoustic token; cost is value-blind

                // ---- CORRECT, before fast is worth asking about ----
                //
                // Host first: it doubles as the session warm-up, so the timed
                // prefills further down are all warmed ones.
                backend.ForceHost = true;
                if (!backend.Begin(voice, text, a))
                { Console.WriteLine("BENCH: host begin: " + backend.Why); return 1; }
                var hostSteps = new List<float[]>();
                for (int k = 0; k < 3; k++)
                {
                    var h = new float[width];
                    if (!backend.Next(feed, h))
                    { Console.WriteLine("BENCH: host step: " + backend.Why); return 1; }
                    hostSteps.Add(h);
                }
                backend.Release();

                // THE NOISE FLOOR, MEASURED BEFORE THE COMPARISON THAT NEEDS
                // IT. Two host runs of the same line answer how much two
                // honest runs differ on this card at all; without it, a
                // bound-vs-host delta has nothing to be judged against and
                // "big" is a feeling. Expected 0.0 — the graph is
                // deterministic — and if it is NOT, that fact rewrites the
                // reading of every number below.
                var repeat = new float[width];
                if (!backend.Begin(voice, text, repeat))
                { Console.WriteLine("BENCH: host repeat begin: " + backend.Why); return 1; }
                double floorWorst = MaxDelta(a, repeat);
                for (int k = 0; k < hostSteps.Count; k++)
                {
                    if (!backend.Next(feed, repeat))
                    { Console.WriteLine("BENCH: host repeat step: " + backend.Why); return 1; }
                    double d = MaxDelta(hostSteps[k], repeat);
                    if (d > floorWorst) floorWorst = d;
                }
                backend.Release();
                Console.WriteLine("BENCH: hostRepeatMaxDelta="
                                  + floorWorst.ToString("0.0e+00"));

                backend.ForceHost = false;
                bool bound = backend.Begin(voice, text, b);
                Console.WriteLine("BENCH: residency=" + NoSpace(backend.Residency));
                if (!bound)
                { Console.WriteLine("BENCH: bound begin: " + backend.Why); return 1; }
                if (backend.Residency == "device")
                {
                    // ONE LINE PER STEP, PRINTED AS IT HAPPENS. The first
                    // bench round died at step two and took step one's
                    // verdict with it — nothing had printed yet, so "did
                    // the resident prefill even agree" went unanswered for
                    // a whole round trip.
                    double worst = MaxDelta(a, b);
                    Console.WriteLine("BENCH: logitsMaxDelta prefill="
                                      + worst.ToString("0.0e+00"));
                    for (int k = 0; k < hostSteps.Count; k++)
                    {
                        var h2 = new float[width];
                        if (!backend.Next(feed, h2))
                        { Console.WriteLine("BENCH: bound step: " + backend.Why); return 1; }
                        double d = MaxDelta(hostSteps[k], h2);
                        if (d > worst) worst = d;
                        Console.WriteLine("BENCH: logitsMaxDelta step" + (k + 1)
                                          + "=" + d.ToString("0.0e+00"));
                        // A disagreement's SHAPE names its cause faster than
                        // its size: how many values, which guidance row, and
                        // whether the rows merely swapped.
                        if (d > 1e-3) Anatomy("step" + (k + 1), hostSteps[k], h2);
                    }
                    // A REAL disagreement is a wrong tensor, and timing a
                    // wrong tensor flatters it. 1e-3 on logits spanning ~40
                    // is float-accumulation territory; past that, stop.
                    if (worst > 1e-3)
                    {
                        Console.WriteLine("BENCH: THE BOUND PATH DISAGREES — "
                            + "not timing a path that speaks different words");
                        return 1;
                    }
                }
                backend.Release();

                // SNAPSHOTTED NOW, because the host timing pass below runs
                // with ForceHost and stamps Residency "host: forced" — the
                // first full agreement run skipped its entire bound timing
                // on exactly that, reading the flag after the host pass had
                // overwritten it, and exited green with half its answer.
                bool proved = backend.Residency == "device";

                // ---- FASTER, measured in the python probe's own buckets ----
                int maxPos = positions[positions.Length - 1] + window;
                var hostMs = TimeSteps(backend, true, voice, text, a, feed, maxPos,
                                       out double hostPrefill);
                if (hostMs == null)
                { Console.WriteLine("BENCH: host timing: " + backend.Why); return 1; }
                double[] boundMs = null; double boundPrefill = 0;
                // ONLY when the check phase actually ran bound. `TimeSteps`
                // with ForceHost=false still succeeds after a binding break —
                // through the host path — and its numbers would wear the
                // wrong label, which is worse than no numbers.
                if (proved)
                {
                    boundMs = TimeSteps(backend, false, voice, text, b, feed, maxPos,
                                        out boundPrefill);
                    // A bench that measured only half its question says so
                    // rather than printing the half as the whole.
                    if (boundMs == null)
                        Console.WriteLine("BENCH: bound timing failed: "
                                          + backend.Why);
                    else if (backend.Residency != "device")
                    {
                        Console.WriteLine("BENCH: the bound pass fell back "
                            + "mid-timing — discarding its numbers: "
                            + NoSpace(backend.Residency));
                        boundMs = null;
                    }
                }

                Console.WriteLine("BENCH: prefillWarmed host="
                    + hostPrefill.ToString("0.000") + "s"
                    + (boundMs != null
                       ? " bound=" + boundPrefill.ToString("0.000") + "s" : ""));
                Report("host", hostMs, positions, window);
                if (boundMs != null) Report("bound", boundMs, positions, window);
                if (boundMs != null)
                {
                    Fit("host", hostMs, positions, window);
                    Fit("bound", boundMs, positions, window);
                }

                // ---- AND THEN SPEAK A WHOLE LINE, WHICH NOTHING HAS EVER
                // ---- ASKED THIS CODE TO DO.
                //
                // Everything above times the loop and compares logits. It
                // proves the graphs run under C# and never once produces a
                // SOUND — and `speechStarted=0 speechSpoken=0` in every
                // recorded run says the game has not either. So live speech
                // has been "finished" for days on the strength of python
                // making audio and C# making numbers, with nobody joining
                // the two.
                //
                // This is the join, and it is deliberately the GAME'S OWN
                // CALL: `SpeechLoop.Run` is what `Audio`'s worker invokes,
                // with the same backend object, the same plan, the same
                // decode. If this writes a wav somebody can play, the C#
                // path works end to end on this card. If it throws, the
                // failure belongs to the game rather than to a build nobody
                // has managed to assemble yet.
                // FIVE LINES, NOT ONE, AND THE SAME FIVE `speak-a-few` USES.
                //
                // The first version of this spoke a single sentence, Jafar
                // judged it "slightly robotic", and there was no way to tell
                // whether that was the C# path, this voice, or the take —
                // `speak.py` says in its own words that the model "has bad
                // days on any given line". One take is one sample, and the
                // python side learned that lesson weeks ago: `speak-a-few`
                // exists because a no-guidance graph was approved off one
                // sentence and the fault it hides shows up on the fourth.
                //
                // Same lines, deliberately: a bare refusal, a repetition that
                // catches a doubled word, a question, a number, and a long
                // one that runs out of breath. Chosen to be awkward, because
                // a test made of comfortable declaratives proves only that
                // comfortable declaratives work. Same voices too, so the C#
                // takes and the python ones can be played against each other
                // rather than against a memory.
                // SHORT LINES ARE THE HYPOTHESIS AND ONE OF THEM IS ONE
                // SAMPLE. The filler appeared on "No." and on nothing else,
                // which is 1 of 5 — and the other four were all long. That
                // is not evidence about short lines, it is evidence about
                // one line. `--short` speaks five of them so the next
                // reading has a denominator, and the street is mostly
                // interjections, so if this is a short-line habit it is a
                // habit that affects most of what the game says.
                string[] lines = shortSet ? new[]
                {
                    "No.",
                    "Yes.",
                    "Who?",
                    "Not here.",
                    "Stop.",
                } : new[]
                {
                    "No.",
                    "Seen the van again. Thursday, same as last Thursday.",
                    "You want me to say that in front of Rocco?",
                    "Forty-two crates, and not one of them opened where I could see it.",
                    "I was nowhere near the yard, and you know it, and so does he.",
                };
                // WHATEVER OF THESE THIS MACHINE HAS. A voice with no
                // precomputed conditioning cannot speak, and refusing the
                // whole stage for a missing third voice would throw away the
                // two takes that were available — rule 5's ratchet.
                // REAL CAST IDS. This read `{"rocco", "ada", "michelle"}`,
                // copied from `speak-a-few`, and MICHELLE IS NOT A VOICE —
                // she is a Mixamo BODY, one of the four character meshes
                // bought for the street. There is no Michelle in the cast,
                // there never has been, and the name had been sitting in the
                // python list long enough to be copied into C#. It surfaced
                // only because the new reporting named the substitution;
                // before that it was invisible on both sides.
                //
                // Rocco, Lena and Ellis: one male and two women who sound
                // nothing like each other, all with conditioning on disk.
                var cast = new[] { "rocco", "lena", "ellis" };
                // ONE WORD, EVERY VOICE — the experiment that separates the
                // model from the reference clip.
                //
                // `parts` was useless on ordinary lines because the silence
                // between words is real speech structure; it cannot tell a
                // filler from a comma. On a SINGLE WORD it has no such
                // problem: "No." is one utterance, so two means the model
                // added one. Restricting the metric to the case it can
                // answer is the difference between an instrument and a
                // number.
                //
                // If every voice does it, it is the model on short text and
                // the fix is upstream of casting. If only some do, it is
                // what their reference clip taught it, and a reference clip
                // is a file we control. Nothing else distinguishes those,
                // and they want completely different work.
                // THE SAME LINE, THE SAME VOICE, N TIMES THROUGH OUR PATH.
                //
                // Twenty draws of "No." with Rocco through chatterbox's own
                // code came back 0.52 to 1.00, median 0.76, not one outlier.
                // Our pipeline produced 1.40 for the same voice and word —
                // outside that whole distribution. That is one sample against
                // twenty, so it is a suspicion rather than a finding, and the
                // symmetric measurement is the only thing that settles it.
                //
                // If our path has a fat tail where pytorch has none, the
                // padding is OURS — the sampler or the graphs — and it is
                // fixable here rather than being a property of the model we
                // have to work around.
                if (repeat > 0)
                {
                    cast = new[] { voice };
                    lines = new string[repeat];
                    for (int i = 0; i < repeat; i++) lines[i] = text;
                    Console.WriteLine("BENCH: " + repeat + " draws of \""
                                      + text + "\" as " + voice);
                }
                else if (sweep)
                {
                    var found = new System.Collections.Generic.List<string>();
                    foreach (var f in System.IO.Directory.GetFiles(conds, "*.bin"))
                        found.Add(System.IO.Path.GetFileNameWithoutExtension(f));
                    found.Sort();
                    cast = found.ToArray();
                    lines = new string[cast.Length];
                    for (int i = 0; i < lines.Length; i++) lines[i] = text;
                    Console.WriteLine("BENCH: sweeping \"" + text + "\" across "
                                      + cast.Length + " voice(s)");
                }
                Console.WriteLine("BENCH: speaking " + lines.Length
                    + " lines through SpeechLoop.Run ...");

                var all = new System.Collections.Generic.List<float>();
                int spoke = 0, refused = 0;
                double totalSpeech = 0, totalWork = 0;
                for (int i = 0; i < lines.Length; i++)
                {
                    // The voice rotates so the set covers more than one
                    // person without costing more lines.
                    // ONE VOICE PER LINE IN A SWEEP, not a rotation: the
                    // whole point is that every voice says the SAME words.
                    string asked = (sweep || repeat > 0) ? cast[i % cast.Length]
                                                          : cast[i % cast.Length];
                    if (sweep) asked = cast[i];
                    // WHICH VOICE ACTUALLY SPOKE, resolved BEFORE the line so
                    // the label cannot outrun the fact. A machine that has
                    // only some of the cast precomputed still gets five takes
                    // — refusing the line would throw away the coverage — but
                    // the substitution is named on the line it happened to,
                    // never inferred from the request.
                    string who = resolve(asked) != null ? asked : voice;
                    var t0 = DateTime.UtcNow;
                    var plan = new SpeechPlan { DeadlineSeconds = 60.0 };
                    var run = SpeechLoop.Run(backend, who, lines[i], plan,
                                             () => (DateTime.UtcNow - t0).TotalSeconds);
                    if (run == null || !run.Usable)
                    {
                        refused++;
                        Console.WriteLine("BENCH: line " + (i + 1) + " (" + who
                            + ") SPOKE NOTHING: "
                            + (run == null ? backend.Why : run.Stop.ToString()));
                        continue;
                    }
                    var dt = DateTime.UtcNow;
                    var samples = backend.Decode(run.Tokens);
                    double decodeSec = (DateTime.UtcNow - dt).TotalSeconds;
                    if (samples == null || samples.Length == 0)
                    {
                        refused++;
                        Console.WriteLine("BENCH: line " + (i + 1) + " (" + who
                            + ") DECODED NOTHING: " + backend.Why);
                        continue;
                    }
                    // FEATHER, BECAUSE THE GAME DOES — AND THE BENCH DID NOT.
                    //
                    // `SpeechSamples.Feather` has existed since the pop was
                    // first heard, and `Audio.PumpSpeech` calls it on every
                    // live line before the clip is built. This bench decoded
                    // and wrote the raw buffer, so the wav Jafar judged was
                    // NOT what the game plays: measured in that file, every
                    // take opened on a step from digital silence to a real
                    // sample — take 2 began at -3108 of 32767 — which is the
                    // pop he heard at the top of each line, five times.
                    //
                    // The bench's whole claim is that it exercises the game's
                    // own path. Skipping a step the game performs makes it a
                    // different path wearing the same name, and the resulting
                    // wav sent him hunting a fault the game does not have.
                    // Anything added to playback belongs here too.
                    // TRIM BEFORE THE FADE. The fade shapes whatever edge
                    // it is given; trimming afterwards would remove the ramp
                    // it had just built and put the step back.
                    // MEASURE BEFORE CUTTING, and report both. A head can be
                    // present and correctly left alone — the "ah" before
                    // "No." runs 440ms and is LOUDER than the word, so the
                    // trim refuses it and a report of what was cut would
                    // call that line clean. `headMs` is the fault; the trim
                    // is only the part of it that can be removed safely.
                    // HOW MANY THINGS IT SAID. The line is one sentence;
                    // more than one utterance means the model added
                    // something. `headMs` cannot see this — it stops at the
                    // first gap, and the "No." with a 440ms filler in it
                    // reported 70ms because a 70ms blip came first.
                    int parts = SpeechSamples.Utterances(samples, 24000);
                    int headMs = SpeechSamples.DetachedHeadMs(samples, 24000);
                    int trimmed = SpeechSamples.TrimDetachedHead(samples, 24000);
                    SpeechSamples.Feather(samples, 24000);
                    double secs = samples.Length / 24000.0;
                    spoke++;
                    totalSpeech += secs;
                    totalWork += run.Seconds + decodeSec;
                    Console.WriteLine("BENCH: line " + (i + 1) + " " + who
                        + (who == asked ? "" : " (asked " + asked + ", absent)")
                        + " stop=" + run.Stop
                        + " tokens=" + run.Tokens.Length
                        + " steps=" + run.Steps
                        + " loop=" + run.Seconds.ToString("0.00")
                        + " decode=" + decodeSec.ToString("0.00")
                        + " speech=" + secs.ToString("0.00")
                        // THE NUMBER THAT WOULD HAVE CAUGHT THE POP. A line
                        // played from silence begins with a step equal to its
                        // first sample, and nothing printed that, so five
                        // audible clicks travelled under a log that looked
                        // healthy. Printed rather than gated: a threshold
                        // here would be invented, and the value is its own
                        // evidence — feathered it is 0, raw it was 0.09.
                        + " head=" + Math.Abs(samples[0]).ToString("0.000")
                        // THE DENOMINATOR FOR "one line in five". Whether a
                        // detached head is a short-line habit or was one
                        // render is a question only more runs can answer,
                        // and only if each one says what it did.
                        + " parts=" + parts
                        + " headMs=" + headMs
                        + " trimmedMs=" + (trimmed / 24.0).ToString("0"));
                    all.AddRange(samples);
                    // Half a second between takes, so they are separable by
                    // ear on one playthrough rather than running together.
                    if (i < lines.Length - 1)
                        all.AddRange(new float[12000]);
                }

                // THE DENOMINATOR, because a count of takes with no total is
                // rule 3b and this file has been bitten by it before.
                Console.WriteLine("BENCH: spoke " + spoke + " of " + lines.Length
                    + " lines, " + refused + " refused");
                if (spoke == 0)
                {
                    Console.WriteLine("BENCH: SPOKE NOTHING at all: " + backend.Why);
                    return 1;
                }
                Console.WriteLine("BENCH: " + totalSpeech.ToString("0.00")
                    + "s of speech in " + totalWork.ToString("0.00") + "s of work"
                    + " (x" + (totalWork / Math.Max(totalSpeech, 0.001)).ToString("0.00")
                    + " realtime)");
                var wav = System.IO.Path.Combine(
                    System.IO.Directory.GetCurrentDirectory(), "bench-spoke.wav");
                WriteWav(wav, all.ToArray(), 24000);
                var info = new System.IO.FileInfo(wav);
                Console.WriteLine("BENCH: wrote " + wav + " ("
                    + (info.Length / 1024) + " KB)");
                Console.WriteLine("BENCH: THE GAME'S OWN CODE SPOKE.");
            }
            return 0;
        }

        /// One full pass: a warmed prefill, then every step to `maxPos`, each
        /// individually clocked. The array is per-position milliseconds.
        static double[] TimeSteps(OnnxSpeech backend, bool host, string voice,
                                  string text, float[] logits, int feed,
                                  int maxPos, out double prefillSeconds)
        {
            backend.ForceHost = host;
            var sw = Stopwatch.StartNew();
            if (!backend.Begin(voice, text, logits))
            { prefillSeconds = 0; return null; }
            prefillSeconds = sw.Elapsed.TotalSeconds;
            var ms = new double[maxPos + 1];
            for (int pos = 1; pos <= maxPos; pos++)
            {
                sw.Restart();
                if (!backend.Next(feed, logits)) { backend.Release(); return null; }
                ms[pos] = sw.Elapsed.TotalMilliseconds;
            }
            backend.Release();
            return ms;
        }

        /// Median of the `window` steps around each asked position — the same
        /// statistic over the same buckets as `probe-step-costs.py`, so the
        /// two histories read against each other.
        static void Report(string name, double[] ms, int[] positions, int window)
        {
            var line = "BENCH: " + name;
            foreach (var p in positions)
                line += " pos" + p + "=" + Bucket(ms, p, window).ToString("0.0");
            Console.WriteLine(line + " (medianMsOver" + window + ")");
        }

        static double Bucket(double[] ms, int pos, int window)
        {
            var seen = new List<double>();
            for (int i = Math.Max(1, pos - window / 2);
                 i <= Math.Min(ms.Length - 1, pos + window / 2); i++)
                seen.Add(ms[i]);
            seen.Sort();
            return seen.Count == 0 ? 0 : seen[seen.Count / 2];
        }

        /// Least squares over the bucket medians: flat cost plus per-position
        /// slope, the two numbers the whole residency argument is about.
        static void Fit(string name, double[] ms, int[] positions, int window)
        {
            double n = positions.Length, sx = 0, sy = 0, sxx = 0, sxy = 0;
            foreach (var p in positions)
            {
                double y = Bucket(ms, p, window);
                sx += p; sy += y; sxx += (double)p * p; sxy += p * y;
            }
            double denom = n * sxx - sx * sx;
            if (Math.Abs(denom) < 1e-9) return;
            double slope = (n * sxy - sx * sy) / denom;
            double flat = (sy - slope * sx) / n;
            Console.WriteLine("BENCH: fit " + name + "="
                + flat.ToString("0.0") + "ms+"
                + (slope * 1000).ToString("0") + "us/pos");
        }

        /// The anatomy of a disagreement: count and rows, then the swap test
        /// — host row 0 against bound row 1 and vice versa — because two
        /// guidance rows in the wrong order produce exactly a large,
        /// deterministic, input-independent delta and nothing else does.
        static void Anatomy(string name, float[] host, float[] bound)
        {
            int half = host.Length / 2;
            int diff = 0, row0 = 0;
            int firstAt = -1;
            for (int i = 0; i < host.Length; i++)
            {
                if (Math.Abs((double)host[i] - bound[i]) <= 1e-3) continue;
                diff++;
                if (i < half) row0++;
                if (firstAt < 0) firstAt = i;
            }
            double sw01 = 0, sw10 = 0;
            for (int i = 0; i < half; i++)
            {
                double d1 = Math.Abs((double)host[i] - bound[half + i]);
                double d2 = Math.Abs((double)host[half + i] - bound[i]);
                if (d1 > sw01) sw01 = d1;
                if (d2 > sw10) sw10 = d2;
            }
            Console.WriteLine("BENCH: anatomy " + name
                + " differing=" + diff + "/" + host.Length
                + " inRow0=" + row0 + " firstAt=" + firstAt
                + " swappedRows=" + Math.Max(sw01, sw10).ToString("0.0e+00"));
        }

        /// A 16-bit mono wav, written by hand because this project ships no
        /// audio library outside Unity and a bench that cannot be LISTENED to
        /// is the reason live speech went days without anybody hearing the
        /// game make a sound.
        static void WriteWav(string path, float[] samples, int rate)
        {
            using (var f = new System.IO.FileStream(path, System.IO.FileMode.Create))
            using (var w = new System.IO.BinaryWriter(f))
            {
                int bytes = samples.Length * 2;
                w.Write(new char[] { 'R', 'I', 'F', 'F' });
                w.Write(36 + bytes);
                w.Write(new char[] { 'W', 'A', 'V', 'E' });
                w.Write(new char[] { 'f', 'm', 't', ' ' });
                w.Write(16);                 // PCM header size
                w.Write((short)1);           // PCM
                w.Write((short)1);           // mono
                w.Write(rate);
                w.Write(rate * 2);           // byte rate
                w.Write((short)2);           // block align
                w.Write((short)16);          // bits
                w.Write(new char[] { 'd', 'a', 't', 'a' });
                w.Write(bytes);
                foreach (var v in samples)
                {
                    float c = v > 1f ? 1f : (v < -1f ? -1f : v);
                    w.Write((short)(c * 32767));
                }
            }
        }

        static double MaxDelta(float[] x, float[] y)
        {
            double worst = 0;
            for (int i = 0; i < x.Length && i < y.Length; i++)
            {
                double d = Math.Abs((double)x[i] - y[i]);
                if (d > worst) worst = d;
            }
            return worst;
        }

        /// The residency string carries prose on the host path; a value with
        /// a space in it truncates every space-separated reader downstream.
        static string NoSpace(string s) { return s == null ? "" : s.Replace(' ', '_'); }
    }
}
