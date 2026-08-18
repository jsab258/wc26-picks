using System;

namespace Ledger.Core
{
    /// WHETHER A BOUGHT MODEL IS BUILT LIKE A PERSON OR LIKE A CARTOON.
    ///
    /// WHY. `review_street.jpg` at 2715f21 put a walker in the foreground
    /// that read as wrong at a glance, and three separate explanations for
    /// it were published and then refuted by measurement — error-shader
    /// magenta (the frame holds zero magenta pixels), a broken mesh, and
    /// cartoon proportions (she measures 7.63 heads, which is a realistic
    /// adult). She is Mixamo's `Sporty Granny` rendering exactly as
    /// authored and there is nothing wrong with her build at all. What the
    /// measuring turned up instead was two OTHER models in the same pool
    /// that genuinely are caricatures, and that nobody had looked at.
    ///
    /// `RealBody.IsMannequin` already keeps `X Bot` and `Y Bot` out of the
    /// pool by NAME. That was right for them — they are untextured grey rig
    /// stand-ins, there is nothing to measure and no threshold would help.
    /// It is the wrong tool here: a hand-written list of caricature names is
    /// a judgement with no number under it, it says nothing about the next
    /// model somebody drops into `Assets/Characters`, and rule 2 forbids
    /// exactly that shape.
    ///
    /// WHY THE ARITHMETIC LIVES IN CORE. The bone heights come from Unity,
    /// which does not compile outside CI, so a threshold applied up there is
    /// one nobody can test for ~28 minutes. Here it is covered by CoreTests
    /// against the real measured models, and there is ONE implementation of
    /// the rule rather than one in the Editor and one in a Python tool that
    /// quietly disagree — rule 1's third corollary, which this project has
    /// paid for repeatedly.
    public static class Proportion
    {
        /// WHERE THE SHOULDERS SIT UP THE FIGURE, floor to neck over floor
        /// to crown. Chosen over the obvious "how many heads tall" because
        /// the crown bone (`HeadTop_End` on a Mixamo rig) sits at the top of
        /// the HAIR: Big Vegas has an afro and Sporty Granny a head of
        /// curlers, so a heads-tall reading cannot tell a large skull from a
        /// tall hairstyle. This can — hair piled above the crown does not
        /// move the neck, while a genuinely large head pushes it down the
        /// body. Neither statistic can see the cranium itself; no bone marks
        /// it. Both are reported by `tools/body-proportions.py` on purpose,
        /// because the pair answers a question neither answers alone.
        ///
        /// Returns false when the figure cannot be measured, rather than a
        /// default that would read as a pass. Rule 3b: an unmeasured model
        /// and a good one must not come out looking the same.
        public static bool TryNeckFraction(double floorY, double neckY, double crownY,
                                           out double fraction)
        {
            fraction = 0.0;
            double height = crownY - floorY;
            if (double.IsNaN(height) || double.IsInfinity(height) || height <= 0.0)
                return false;
            double neck = neckY - floorY;
            if (double.IsNaN(neck) || neck <= 0.0 || neck >= height)
                return false;
            fraction = neck / height;
            return true;
        }

        /// MEASURED, NOT PICKED. `tools/body-proportions.py` read all ten
        /// models in `Assets/Characters` off their bind poses:
        ///
        ///     The Boss        0.762   <- caricature
        ///     Big Vegas       0.761   <- caricature
        ///     Sporty Granny   0.806
        ///     Michelle        0.824
        ///     X Bot           0.826
        ///     Joe             0.831
        ///     Martha          0.831
        ///     Y Bot           0.836
        ///     Sophie          0.837
        ///
        /// The two caricatures sit at 0.761–0.762 and everything else spans
        /// 0.806–0.837. The gap between the clusters (0.044) is wider than
        /// the whole realistic cluster end to end (0.031), so this is a real
        /// break rather than a line drawn through a spread. 0.79 sits inside
        /// that gap with margin on both sides — 0.028 above the caricatures,
        /// 0.016 below the nearest real body.
        ///
        /// Remy is missing from the table above, and the build then settled
        /// why. `tools/body-proportions.py` refuses it: the RAW FBX bind
        /// pose puts the crown of the skull below the head bone and the
        /// knee, ankle and toe-base all at one height, which no standing
        /// figure can do, and all seven of its skin clusters agree.
        ///
        /// UNITY MEASURES IT FINE — the build reports "0 unmeasured but
        /// kept" and writes Remy a prefab, so it passed this bound. The
        /// importer rebuilds the rig rather than trusting the stored bind
        /// pose, so the two readers are looking at different things and
        /// BOTH are right about the thing they read. The one that governs
        /// is the Editor's, because that is the hierarchy the game runs.
        ///
        /// The Python tool stays as it is. It reads the file as shipped,
        /// which is the correct question for "what did this vendor give
        /// us", and refusing beats guessing.
        public const double MinNeckFraction = 0.79;

        /// True only for a figure that was MEASURED and came out below the
        /// bound. An unmeasurable model is not a caricature — it is
        /// unmeasured, which is a different fact and a different fix, and
        /// `TryNeckFraction` is how a caller tells them apart.
        public static bool IsCaricature(double floorY, double neckY, double crownY)
        {
            double f;
            return TryNeckFraction(floorY, neckY, crownY, out f) && f < MinNeckFraction;
        }
    }
}
