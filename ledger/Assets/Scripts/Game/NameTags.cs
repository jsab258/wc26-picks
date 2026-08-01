using System.Collections.Generic;
using UnityEngine;

namespace Ledger.Game
{
    /// TWO NAMES IN THE SAME PLACE ARE WORSE THAN ONE NAME, and the street had
    /// 185 such pairs.
    ///
    /// The distance rule was already right — a name resolves as you get close
    /// enough to speak to somebody and is not there across the road — and it is
    /// not sufficient. Six people standing at a junction are all inside talking
    /// range, so six names arrive at once, overlap, and none of them can be
    /// read. Recognition does not work like that: you pick out the person you
    /// are looking at, not the crowd behind them.
    ///
    /// So the nearest label wins its patch of screen and anything farther that
    /// collides with it stands down. That is a real declutter rather than a cap
    /// on the count — a cap would hide the sixth person on an empty street,
    /// where there was nothing wrong with showing them.
    ///
    /// AND IT MAKES THE MEASUREMENT GATEABLE. `collidingNames` has been printed
    /// for three builds and gated on nothing, because zero was unreachable and
    /// any other number was a threshold nobody had measured. With a declutter
    /// that actually resolves collisions, zero is both reachable and correct,
    /// and the sim can require it. A number reported for three builds and never
    /// acted on is the same as no number at all.
    public static class NameTags
    {
        struct Candidate
        {
            public TextMesh Label;
            public float Distance;
        }

        static readonly List<Candidate> _offered = new List<Candidate>();
        static int _frame = -1;

        /// How many labels stood down on the last resolved frame, and how many
        /// were offered. Printed so a declutter that quietly stopped running
        /// looks different from a street with nothing to declutter.
        public static int Suppressed { get; private set; }
        public static int Offered { get; private set; }

        /// A walker offers its label each frame it wants one shown.
        ///
        /// OFFERED, NOT SHOWN. The walker has already decided the label is close
        /// enough and faded it in; this decides whether it survives contact with
        /// the labels in front of it. Splitting it that way keeps the distance
        /// rule where the person is and the screen rule where the screen is.
        public static void Offer(TextMesh label, float distance)
        {
            if (label == null) return;
            Sweep();
            _offered.Add(new Candidate { Label = label, Distance = distance });
        }

        /// Resolve the previous frame's offers once, at the start of the next.
        ///
        /// DEFERRED BY A FRAME ON PURPOSE. Walkers update in an order nobody
        /// controls, so resolving as they arrive would let the first one win by
        /// being first rather than by being nearest. Waiting until the set is
        /// complete costs one frame of latency on a label appearing, which is
        /// invisible, and buys a decision that does not depend on iteration
        /// order — the same reasoning as `CharacterRig.SolvedLastFrame`.
        static void Sweep()
        {
            if (Time.frameCount == _frame) return;
            _frame = Time.frameCount;
            Resolve();
            _offered.Clear();
        }

        static void Resolve()
        {
            Offered = _offered.Count;
            Suppressed = 0;
            var cam = Camera.main;
            if (cam == null || _offered.Count == 0) return;

            // Nearest first, so the winner of any overlap is the person the
            // player is closest to — which is the one they are most likely to
            // be looking at and the only one they can speak to.
            _offered.Sort((a, b) => a.Distance.CompareTo(b.Distance));

            var kept = new List<Rect>(_offered.Count);
            foreach (var c in _offered)
            {
                if (c.Label == null) continue;
                var r = c.Label.GetComponent<Renderer>();
                if (r == null) continue;
                if (!ScreenRect(cam, r.bounds, out var rect)) continue;

                bool blocked = false;
                foreach (var k in kept)
                    if (k.Overlaps(rect)) { blocked = true; break; }

                if (blocked)
                {
                    // Hidden, not moved. Nudging a colliding label somewhere
                    // free would put a name over the wrong person's head, which
                    // is a worse failure than not naming them — this game is
                    // about who saw whom, and a misattributed name is a lie.
                    var col = c.Label.color;
                    col.a = 0f;
                    c.Label.color = col;
                    Suppressed++;
                }
                else kept.Add(rect);
            }
        }

        /// A world-space bounds as a screen rectangle, or false if it is behind
        /// the camera — where the projection is meaningless and every rect
        /// would appear to collide with every other.
        public static bool ScreenRect(Camera cam, Bounds b, out Rect rect)
        {
            rect = default;
            var lo = cam.WorldToScreenPoint(b.min);
            var hi = cam.WorldToScreenPoint(b.max);
            if (lo.z <= 0f || hi.z <= 0f) return false;
            rect = Rect.MinMaxRect(Mathf.Min(lo.x, hi.x), Mathf.Min(lo.y, hi.y),
                                   Mathf.Max(lo.x, hi.x), Mathf.Max(lo.y, hi.y));
            return true;
        }
    }
}
