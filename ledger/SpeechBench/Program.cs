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

            var backend = OnnxSpeech.Open(models, id => cond, s => tok.Encode(s),
                                          out why);
            if (backend == null) { Console.WriteLine("BENCH: open: " + why); return 1; }

            using (backend)
            {
                int width = backend.Rows * backend.VocabSize;
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
                if (backend.Residency == "device")
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
