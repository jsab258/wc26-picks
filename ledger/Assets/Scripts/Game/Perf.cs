using System.Collections.Generic;
using System.Diagnostics;

namespace Ledger.Game
{
    /// Frame-time instrumentation.
    ///
    /// This exists because of a specific lesson from the indie post-mortems:
    /// performance problems in a systems-heavy game are almost never where the
    /// developer guessed, and by the time they are obvious they are load-bearing.
    /// Traffic is the first subsystem in this project that runs work every single
    /// frame for every visible object, so it goes in WITH a measurement rather
    /// than being measured after somebody notices a stutter.
    ///
    /// Deliberately tiny: a stopwatch, a dictionary of running totals, and a
    /// coarse histogram for the frame percentile. No allocation in the hot path,
    /// nothing to configure, and the numbers land in the CI sim report so a
    /// regression shows up as a diff in a build log rather than as a feeling.
    public static class Perf
    {
        public class Counter
        {
            public string Name;
            public int Samples;
            public double TotalMs, WorstMs;
            public double MeanMs => Samples > 0 ? TotalMs / Samples : 0;
        }

        static readonly Dictionary<string, Counter> _counters = new Dictionary<string, Counter>();
        static readonly List<string> _order = new List<string>();

        // Frame times, bucketed to two seconds. A histogram rather than a list
        // because the sim runs for ten minutes and keeping every frame would be
        // tens of megabytes to answer one question.
        //
        // The range was 200ms and that was a mistake the first run caught: the
        // CI runner has no GPU, falls back to software rasterisation, and turns
        // in 191ms frames — so every percentile landed in the overflow bucket
        // and read as exactly 200.00ms. A percentile pinned at the top of its
        // own range is not a measurement, it is a shrug, and it would have
        // hidden a real regression behind a plausible number.
        const int Buckets = 8000;
        const double BucketMs = 0.25;
        static readonly int[] _frames = new int[Buckets + 1];
        static int _frameCount;
        static double _frameTotalMs, _frameWorstMs;

        public static void Reset()
        {
            _counters.Clear();
            _order.Clear();
            for (int i = 0; i < _frames.Length; i++) _frames[i] = 0;
            _frameCount = 0;
            _frameTotalMs = _frameWorstMs = 0;
        }

        /// One frame happened, and took this long.
        public static void Frame(double seconds)
        {
            double ms = seconds * 1000.0;
            if (ms < 0) return;
            _frameCount++;
            _frameTotalMs += ms;
            if (ms > _frameWorstMs) _frameWorstMs = ms;
            int b = (int)(ms / BucketMs);
            _frames[b < 0 ? 0 : b > Buckets ? Buckets : b]++;
        }

        /// A named piece of per-frame work took this long.
        public static void Add(string name, double ms)
        {
            if (!_counters.TryGetValue(name, out var c))
            {
                _counters[name] = c = new Counter { Name = name };
                _order.Add(name);
            }
            c.Samples++;
            c.TotalMs += ms;
            if (ms > c.WorstMs) c.WorstMs = ms;
        }

        /// Scoped timer: `using (Perf.Time("traffic")) { ... }`.
        public static Scope Time(string name) => new Scope(name);

        public struct Scope : System.IDisposable
        {
            readonly string _name;
            readonly long _start;
            public Scope(string name) { _name = name; _start = Stopwatch.GetTimestamp(); }
            public void Dispose() =>
                Add(_name, (Stopwatch.GetTimestamp() - _start) * 1000.0 / Stopwatch.Frequency);
        }

        public static int FrameCount => _frameCount;
        public static double MeanFrameMs => _frameCount > 0 ? _frameTotalMs / _frameCount : 0;
        public static double WorstFrameMs => _frameWorstMs;

        /// The frame time this fraction of frames came in under. p95 is the
        /// number that matters — a good mean with a bad tail is a game that
        /// stutters, and the mean will never tell you so.
        public static double FramePercentileMs(double fraction)
        {
            if (_frameCount == 0) return 0;
            int want = (int)(_frameCount * fraction);
            int seen = 0;
            for (int i = 0; i < _frames.Length; i++)
            {
                seen += _frames[i];
                if (seen >= want) return i * BucketMs;
            }
            return _frameWorstMs;
        }

        public static Counter Get(string name) =>
            _counters.TryGetValue(name, out var c) ? c : null;

        /// Everything measured, for the sim report.
        public static List<object> Report()
        {
            var list = new List<object>();
            foreach (var name in _order)
            {
                var c = _counters[name];
                list.Add(new Dictionary<string, object>
                {
                    { "what", c.Name },
                    { "calls", c.Samples },
                    { "meanMs", System.Math.Round(c.MeanMs, 4) },
                    { "worstMs", System.Math.Round(c.WorstMs, 3) },
                    { "totalMs", System.Math.Round(c.TotalMs, 1) },
                });
            }
            return list;
        }

        public static string Summary() =>
            $"frames={_frameCount} meanFrame={MeanFrameMs:0.00}ms p95={FramePercentileMs(0.95):0.00}ms " +
            $"worstFrame={WorstFrameMs:0.0}ms";
    }
}
