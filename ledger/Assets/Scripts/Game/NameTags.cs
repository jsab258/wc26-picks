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
    /// AND IT MAKES A MEASUREMENT GATEABLE — BUT NOT THE ONE THIS COMMENT
    /// ORIGINALLY NAMED. It said `collidingNames` had been printed for three
    /// builds and gated on nothing, and that a working declutter finally made
    /// zero reachable there. Wrong: `collidingNames` counts every `TextMesh` in
    /// the scene, and the scene is full of street plates, stop signs and lane
    /// signs on posts that cluster at junctions by design. The build settled it
    /// at `collidingNames=144 nameTagsOffered=1` — a hundred and forty-four
    /// overlaps among text this class never touches, and one nameplate to
    /// place. Zero was never reachable there and never should have been.
    ///
    /// What became gateable is `WorstUnplaced`, below: the labels this class
    /// owns, after it has finished with them. `collidingNames` stays printed
    /// and ungated, because a jump in it means the street furniture moved and
    /// that is worth seeing without being a legibility failure.
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

        /// Pairs of STILL-VISIBLE managed labels that overlap once the pass has
        /// finished — the postcondition, not the workload.
        ///
        /// THE GATE HAS TO MEASURE WHAT THE DECLUTTER CONTROLS. The first
        /// version gated on `collidingNames`, which counts every `TextMesh` in
        /// the scene — and the scene is full of street furniture: name plates,
        /// stop signs, lane signs, neon words, all on posts that legitimately
        /// cluster at a junction. The build came back `collidingNames=144
        /// nameTagsOffered=1`: a hundred and forty-four overlaps among text this
        /// class never sees, and one nameplate to declutter. The gate was
        /// unsatisfiable and it was measuring somebody else's population.
        ///
        /// AND THEN THE FIX WAS WRONG TWICE MORE, both worth writing down
        /// because they are the failure modes this repo keeps producing:
        ///
        ///   - the replacement incremented this counter in the same `blocked`
        ///     branch as `Suppressed`, so it was that number with a second name
        ///     while its comment claimed it was what remained AFTERWARDS. Every
        ///     one of those collisions was then successfully hidden — they are
        ///     the declutter WORKING, and gating on zero of them would have
        ///     demanded an empty street.
        ///   - the gate clause became `Suppressed >= 0`, which is true of any
        ///     int that only counts up. Swapping an unsatisfiable gate for a
        ///     vacuous one is moving the bound to make red go away.
        ///
        /// So this is computed as a genuine postcondition: after the pass, take
        /// the labels still showing and ask whether any two of them are in the
        /// same place. Zero by construction — which is the point. A gate on a
        /// constructed invariant costs nothing while the construction holds and
        /// fires the moment somebody changes the resolver to nudge instead of
        /// hide, or reorders it so a rect is compared before it is final.
        public static int UnplacedNow { get; private set; }

        /// The worst that got past the resolver on ANY frame of the run, and
        /// how many frames actually resolved something.
        ///
        /// MAXIMUM, BECAUSE OF THE QUESTION IT ANSWERS. The sim reads these once
        /// at the end of a day; `UnplacedNow` at that instant describes one
        /// frame out of thousands and a collision two seconds earlier would be
        /// invisible. "Did this ever fail" is answered by the maximum — the same
        /// reasoning that made the maximum WRONG for the AO ceiling, where the
        /// question was "is the pass everywhere" and a maximum maximised the
        /// very quantity the bound existed to keep small. Same statistic, and it
        /// is right here for precisely the reason it was wrong there.
        ///
        /// `ResolvedFrames` is the other half and it is a count, not a maximum,
        /// because it answers "did this run at all" — without it, a declutter
        /// that never executed reports a perfect zero and gates green.
        public static int WorstUnplaced { get; private set; }
        public static int ResolvedFrames { get; private set; }

        /// The tallest a SHOWING nameplate has been over the run, as a fraction
        /// of screen height. Worst-over-run rather than a sample, for the reason
        /// the first version of this measurement failed: it read 0.036 while the
        /// still that prompted it showed a name spanning a third of the frame.
        /// Both were true — the sample happened at a moment with no label near.
        public static float WorstNameFrac { get; private set; }

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
            UnplacedNow = 0;
            var cam = Camera.main;
            if (cam == null || _offered.Count == 0) return;
            ResolvedFrames++;

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
                else
                {
                    kept.Add(rect);
                    // HOW BIG A NAME EVER GETS, MEASURED WHERE THE NAMES ARE.
                    //
                    // `SimDirector.MeasureTextFaults` reported
                    // `worstTextHeightFrac=0.210` — a label a fifth of the
                    // screen tall — under a comment claiming it measured "what
                    // NameTags manages". It did not: it looped over every
                    // `TextMesh` in the scene, and this city is full of street
                    // plates that are SUPPOSED to be large when you stand next
                    // to one. The same reading that made the mirrored-text
                    // count meaningless.
                    //
                    // Here the set is exactly the offered NPC labels, the rects
                    // are already computed, and a suppressed label is excluded
                    // because it is invisible and its size is not a fault. The
                    // number this produces is answerable: no threshold on it
                    // yet, because rule 2 — print the series first, then bound
                    // it from the evidence.
                    float frac = rect.height / Mathf.Max(1f, cam.pixelHeight);
                    if (frac > WorstNameFrac) WorstNameFrac = frac;
                }
            }

            // THE POSTCONDITION, ASKED SEPARATELY FROM THE WORK.
            //
            // Everything above is what the pass DID. This is what it LEFT: of
            // the labels still showing, is any pair in the same place. It is
            // deliberately not the `blocked` tally — those are the collisions
            // the declutter resolved, and requiring zero of THEM would be
            // requiring an empty street.
            //
            // Redundant while the loop above is correct, and that is the whole
            // value of it. It re-derives the claim from the result instead of
            // restating the loop, so it survives the rewrite that breaks the
            // loop — which is the failure a gate exists to catch and the one a
            // counter incremented inside the loop cannot.
            for (int i = 0; i < kept.Count; i++)
                for (int j = i + 1; j < kept.Count; j++)
                    if (kept[i].Overlaps(kept[j])) UnplacedNow++;
            if (UnplacedNow > WorstUnplaced) WorstUnplaced = UnplacedNow;
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
