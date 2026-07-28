using System;

namespace Ledger.Core
{
    /// THE PROCEDURAL ANIMATION RIG (the-gap.md §3b).
    ///
    /// Built BEFORE the characters land, and against capsules, deliberately.
    /// Animation is the biggest single gap between this and KCD2, and the
    /// part of it that is not bought — foot planting, look-at, the lean, the
    /// breathing, the limp on the body rather than in the footstep rhythm —
    /// is all maths that can be written and proved now. When the Mixamo FBXs
    /// arrive the work is a wiring job rather than a starting point.
    ///
    /// Everything here is engine-free. The Unity layer supplies a skeleton
    /// and a raycast; this decides what the bones do.
    ///
    /// The design position it serves, from game-feel-spec §2: **CODE-DRIVEN,
    /// not root motion.** The momentum and gait in `Feel` are already tested
    /// and frame-rate independent; root motion would move authority for
    /// movement inside clips we did not author and cannot test, and the two
    /// would fight. The accepted cost is foot sliding — which is exactly what
    /// the IK below exists to fix, and which is far cheaper to fix than a
    /// movement model is to replace.
    public static class Rig
    {
        // ---- two-bone IK ---------------------------------------------------

        /// Solve a hip-knee-foot chain by the law of cosines.
        ///
        /// Returns the angles in RADIANS: `hip` is how far the upper bone
        /// swings back from pointing straight at the target, `knee` is how
        /// far the lower bone bends from straight. Both are zero when the leg
        /// is fully extended, which is the convention that makes "no IK" and
        /// "IK at full reach" the same pose rather than a pop.
        ///
        /// THE CONVENTION, WRITTEN DOWN, because getting it wrong costs an
        /// afternoon and looks like a broken solver. With the hip at the
        /// origin and the target straight down:
        ///
        ///     upper bone direction  =  `hip` off straight down
        ///     LOWER bone direction  =  `hip - knee` off straight down
        ///     knee = hipPos + upper * dir(hip)
        ///     foot = knee   + lower * dir(hip - knee)
        ///
        /// where dir(a) = (sin a, -cos a). The first test written against
        /// this used `hip - (pi - knee)` and missed the target by 0.84m — the
        /// solver was correct and the reconstruction was not.
        public static (double hip, double knee) TwoBone(double upper, double lower, double reach)
        {
            if (upper <= 0 || lower <= 0) return (0, 0);
            // OVER-EXTENSION IS THE COMMON CASE, not the edge case: a walking
            // leg is nearly straight for most of its cycle, and a solver that
            // returns NaN past full reach snaps the leg once per step. Clamp
            // instead — the foot simply cannot get there, which is true.
            double max = upper + lower;
            double min = Math.Abs(upper - lower);
            reach = Feel.Clamp(reach, min + 1e-6, max - 1e-6);

            // Interior angle at the knee.
            double cosKnee = (upper * upper + lower * lower - reach * reach) / (2 * upper * lower);
            double knee = Math.PI - Math.Acos(Feel.Clamp(cosKnee, -1, 1));

            // How far the upper bone swings off the straight line to the target.
            double cosHip = (upper * upper + reach * reach - lower * lower) / (2 * upper * reach);
            double hip = Math.Acos(Feel.Clamp(cosHip, -1, 1));

            return (hip, knee);
        }

        /// How far the pelvis must drop so BOTH feet can reach their targets.
        ///
        /// The half of foot IK everybody forgets. Planting each foot
        /// independently on a slope stretches one leg past its reach and the
        /// character does the splits; dropping the hips to the lower foot is
        /// what makes a figure stand on a kerb like a person instead of like
        /// a decal.
        public static double PelvisDrop(double leftGround, double rightGround, double legLength)
        {
            double lower = Math.Min(leftGround, rightGround);
            double higher = Math.Max(leftGround, rightGround);
            double spread = higher - lower;
            // Never more than a quarter of the leg: past that the character
            // is crouching rather than standing on uneven ground, and it
            // reads as a bug.
            return -Feel.Clamp(spread * 0.5, 0, legLength * 0.25);
        }

        /// Where a foot should actually sit, given where the animation put it
        /// and where the ground turned out to be.
        ///
        /// The clamp matters more than the lerp: a foot that follows the
        /// ground exactly will chase a kerb edge or a passing car's collider
        /// and jitter. Beyond the limit the animation wins and the foot
        /// simply floats or clips, which is a smaller lie than a shaking leg.
        public const double MaxFootAdjustMetres = 0.42;

        public static double FootHeight(double animated, double ground, double blend)
        {
            double wanted = Feel.Clamp(ground, animated - MaxFootAdjustMetres,
                                               animated + MaxFootAdjustMetres);
            return animated + (wanted - animated) * Feel.Clamp01(blend);
        }

        /// IK is faded OUT as a foot swings and IN as it plants. Full-strength
        /// IK through the whole cycle drags the swinging foot along the
        /// ground, which looks worse than no IK at all.
        ///
        /// `phase` is 0..1 through one foot's cycle; the plant is the middle.
        public static double PlantBlend(double phase)
        {
            phase = phase - Math.Floor(phase);
            // Down through 0.15..0.35, planted 0.35..0.75, up through
            // 0.75..0.9. Smoothstepped at both ends so nothing pops.
            if (phase < 0.15) return 0;
            if (phase < 0.35) return Smooth((phase - 0.15) / 0.20);
            if (phase < 0.75) return 1;
            if (phase < 0.90) return 1 - Smooth((phase - 0.75) / 0.15);
            return 0;
        }

        // ---- look-at -------------------------------------------------------

        /// A HEAD DOES NOT TURN ALONE. Splitting the turn down the spine is
        /// the difference between a character looking at you and an owl.
        ///
        /// Returns degrees for chest, neck and head, summing to the reachable
        /// part of `degrees`. Anything past the total limit is simply not
        /// looked at, which is why people turn their whole body — and the
        /// caller can see that it was not reached and turn the body.
        public const double LookLimitDegrees = 78;

        public static (double chest, double neck, double head) LookSplit(double degrees)
        {
            double sign = degrees < 0 ? -1 : 1;
            double d = Feel.Clamp(Math.Abs(degrees), 0, LookLimitDegrees);
            // Weighted toward the head for small glances and down into the
            // chest for large ones: you flick your eyes at a passing face and
            // you turn to look at somebody who said your name.
            double t = d / LookLimitDegrees;
            double chestShare = 0.10 + 0.35 * t * t;
            double neckShare = 0.30 + 0.05 * t;
            double headShare = 1.0 - chestShare - neckShare;
            return (sign * d * chestShare, sign * d * neckShare, sign * d * headShare);
        }

        /// Whether the body has to come round. Exposed because it is a
        /// DECISION the character makes, not a clamp — somebody who has to
        /// turn to look at you has been made to do something.
        public static bool MustTurnBody(double degrees) => Math.Abs(degrees) > LookLimitDegrees;

        // ---- lean ----------------------------------------------------------

        /// Lean into acceleration, out of braking, and bank into a turn.
        /// Free weight: the momentum is already simulated and nothing has
        /// ever shown it.
        public static (double pitch, double roll) Lean(double accelMetresPerSecSq,
                                                       double turnDegreesPerSec,
                                                       double speed)
        {
            // Forward when speeding up, back when stopping. Capped hard: a
            // character leaning fifteen degrees is falling over, not running.
            double pitch = Feel.Clamp(accelMetresPerSecSq * 0.30, -7.0, 9.0);
            // Bank scales with SPEED as well as turn rate — a pivot on the
            // spot has no lean in it, and banking a stationary turn is the
            // single most common giveaway of a procedural rig.
            double bank = -turnDegreesPerSec * 0.035 * Feel.Clamp01(speed / 4.0);
            return (pitch, Feel.Clamp(bank, -11.0, 11.0));
        }

        // ---- breathing -----------------------------------------------------

        /// Chest rise, as an additive on top of whatever is playing.
        ///
        /// Rate and depth both come from real state — stamina from Combat,
        /// capability from HarmBook. A character who has just fought is
        /// AUDIBLY AND VISIBLY out of breath without a single authored clip,
        /// and stays that way for as long as the simulation says.
        public static double BreathRate(double stamina, double capability)
        {
            double tired = 1.0 - Feel.Clamp01(stamina);
            double hurt = 1.0 - Feel.Clamp01(capability);
            // Breaths per second. Resting ~0.25 (fifteen a minute), spent
            // ~0.85 — fast, but not a panting dog.
            return 0.25 + 0.50 * tired + 0.18 * hurt;
        }

        public static double BreathDepth(double stamina, double capability)
        {
            double tired = 1.0 - Feel.Clamp01(stamina);
            double hurt = 1.0 - Feel.Clamp01(capability);
            // A hurt person breathes SHALLOWER, not deeper — a cracked rib
            // stops you filling your lungs. Getting this backwards is the
            // obvious mistake and it reads instantly as wrong.
            return (0.010 + 0.022 * tired) * (1.0 - 0.45 * hurt);
        }

        public static double Breath(double time, double stamina, double capability)
        {
            double rate = BreathRate(stamina, capability);
            double depth = BreathDepth(stamina, capability);
            // Asymmetric: the in-breath is quicker than the out-breath, which
            // is true and is what stops it reading as a sine wave.
            double p = (time * rate) % 1.0;
            double shape = p < 0.4 ? Smooth(p / 0.4) : 1.0 - Smooth((p - 0.4) / 0.6);
            return (shape - 0.5) * 2.0 * depth;
        }

        // ---- the limp, on the body -----------------------------------------

        /// The limp already exists in the FOOTSTEP RHYTHM (game-feel-spec §2,
        /// built without a model because a limp is an ASYMMETRY). This is the
        /// same asymmetry expressed as pose, for when there is a body to put
        /// it on.
        ///
        /// Returns how much to shorten the bad leg's stance and how far to
        /// dip the pelvis onto the good one. Driven by the SAME capability
        /// number as the audio, so the two cannot disagree — a limp you can
        /// hear but not see is worse than neither.
        public static (double stanceScale, double pelvisDip) Limp(double capability, bool badLegIsLeft,
                                                                  double phase)
        {
            double hurt = Feel.Clamp01(1.0 - Feel.Clamp01(capability));
            if (hurt < 0.05) return (1.0, 0);
            // Weight comes off the bad leg fast and stays on the good one.
            double p = phase - Math.Floor(phase);
            bool onBadLeg = badLegIsLeft ? p < 0.5 : p >= 0.5;
            double stance = onBadLeg ? 1.0 - 0.35 * hurt : 1.0 + 0.10 * hurt;
            double dip = onBadLeg ? 0 : -0.045 * hurt;
            return (stance, dip);
        }

        // ---- helpers -------------------------------------------------------

        static double Smooth(double t)
        {
            t = Feel.Clamp01(t);
            return t * t * (3 - 2 * t);
        }
    }
}
