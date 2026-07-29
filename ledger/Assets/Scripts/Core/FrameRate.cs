using System;

namespace Ledger.Core
{
    /// A frame-time readout for the debug panel.
    ///
    /// EXISTS FOR ONE REASON: CI has no GPU, so this project has never
    /// measured a frame time that means anything, and the first person to
    /// play it is the first real measurement. If they cannot read the number
    /// off the screen, the most important unknown in the project stays
    /// unknown for another day.
    ///
    /// TWO NUMBERS, NOT ONE, and this is the part people get wrong. An
    /// average frame time is close to useless for judging whether a game
    /// feels smooth: thirty seconds at 120fps with four 200ms hitches in it
    /// averages beautifully and is horrible to play. The hitches are the
    /// experience. So the panel shows the typical frame AND the worst recent
    /// one, and the gap between them is usually the more actionable half.
    public struct FrameRate
    {
        /// Seconds of history the worst-case window covers. Short enough that
        /// a hitch you just felt is still on screen when you look down, long
        /// enough that it does not vanish before you do.
        public const double WindowSeconds = 3.0;

        // EACH FRAME COUNTS ONCE. The first version smoothed with the
        // 1-exp(-k*dt) this project uses everywhere else — which weights each
        // sample BY ITS OWN DURATION, so a 200ms stall counts as much as
        // twenty-four good frames. It reported 13fps for a stream a profiler
        // would call 104, and a readout that pessimistic is as useless as one
        // that hides the stalls, just in the other direction.
        //
        // A frame-count mean over a rolling window is what every profiler
        // shows and what a player means by "frame rate". Two alternating
        // buckets rather than one, because a single bucket reset on a timer
        // makes the number jump to whatever the first frame after the reset
        // happened to be.
        double _sumA, _sumB;
        int _countA, _countB;
        double _ageA, _ageB;
        double _worst;
        double _worstAge;
        bool _started;

        double Mean
        {
            get
            {
                int n = _countA + _countB;
                return n > 0 ? (_sumA + _sumB) / n : 0;
            }
        }

        public double MeanMs => Mean * 1000.0;
        public double WorstMs => _worst * 1000.0;
        public double Fps => Mean > 1e-6 ? 1.0 / Mean : 0;

        public void Tick(double dt)
        {
            if (!(dt > 0)) return;     // catches zero, negative AND NaN

            // The offset has to be established on the FIRST frame. Both
            // buckets start at age zero, so without this they roll over
            // together every window and the reading momentarily comes from a
            // single sample — which is the exact collapse two buckets exist
            // to prevent. Caught by a test measuring the worst deviation over
            // two thousand alternating frames rather than by reading the
            // code, where it looks fine.
            if (!_started) { _started = true; _ageB = WindowSeconds / 2; }

            _sumA += dt; _countA++; _ageA += dt;
            _sumB += dt; _countB++; _ageB += dt;
            // The buckets are half a window out of phase, so one is always
            // between half and a full window old and the reported figure
            // never collapses to a single frame.
            // Both reset the same way. An earlier version reset B to one
            // sample instead of none, which looked deliberate and bought
            // nothing — proved by a break run that swapped it back and
            // changed no reading anywhere. THE PHASE OFFSET is the whole
            // mechanism: whichever bucket has just emptied, the other is
            // between half and a full window old and carries the reading.
            if (_ageA >= WindowSeconds) { _sumA = 0; _countA = 0; _ageA = 0; }
            if (_ageB >= WindowSeconds) { _sumB = 0; _countB = 0; _ageB = 0; }

            // The worst frame in the window, which DECAYS rather than
            // latching. A worst-ever number is wrong for the rest of the
            // session after one hitch during load, and a readout nobody
            // trusts is a readout nobody reads.
            _worstAge += dt;
            if (dt >= _worst || _worstAge >= WindowSeconds)
            {
                _worst = dt;
                _worstAge = 0;
            }
        }

        /// One line, phrased so it can be read aloud down a phone.
        public string Line() =>
            $"{Fps:0} fps  ({MeanMs:0.0} ms typical, {WorstMs:0.0} ms worst of the last "
            + $"{WindowSeconds:0} s)";

        /// Whether the gap between typical and worst is big enough to be the
        /// thing worth reporting.
        ///
        /// Three times the typical frame is roughly where a hitch stops being
        /// a statistic and starts being something a hand notices.
        public bool Hitching => _worst > Mean * 3.0 && _worst > 0.033;
    }
}
