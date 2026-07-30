using System;

namespace Ledger.Core
{
    /// SENSES. The foundation `weapons-spec.md` says this project never had.
    ///
    /// The pipeline is PERCEPTION → OBSERVATION → REACTION → MEMORY & TALK,
    /// and stages 3 and 4 are the best-tested work in the project while 1 and
    /// 2 did not exist at all. This file is stage 1.
    ///
    /// WHAT IS NEW HERE IS NOT THE CONE. Every stealth game has a cone. Two
    /// things in this file are ours:
    ///
    ///   1. **Light is an input**, and we have been computing it for weeks
    ///      without a single NPC ever reading it. `LightModel` knows how lit
    ///      any spot is at any hour; until now that was renderer trivia.
    ///   2. **Loudness is relative** (Chaos Theory's ambient bar). A sound is
    ///      not audible at a radius; it is audible at a radius *given what is
    ///      already happening where the listener is standing*. The bar on a
    ///      busy night hides a shot that a residential street at 3am carries
    ///      the length of. All of those numbers already existed for the mixer.
    ///
    /// NOTHING HERE IS A BOOLEAN. Detection is a confidence that accumulates,
    /// identification is a five-rung ladder, and hearing returns a radius
    /// rather than a yes. Spec §16 holds the calibration and the reasoning
    /// for every constant below.
    public static class Perception
    {
        // ---------------------------------------------------------------
        // VISION — cone, range, light, motion, and time in cone
        // ---------------------------------------------------------------

        /// Total field of view, degrees. Human-ish and deliberately wide:
        /// narrow cones make hiding behind somebody's shoulder trivial, which
        /// is the failure mode that makes stealth feel like exploiting a bug.
        public const double FovDegrees = 120.0;

        /// The inner band with full acuity. Outside it and inside `Fov`, only
        /// MOTION registers — Blacklist's band model. A man standing still at
        /// the edge of vision is genuinely not seen, and that is a tactic.
        public const double AcuityDegrees = 60.0;

        /// Metres, in clear daylight, at which a person registers as present.
        /// You can tell someone is there across a street and not much further.
        public const double DetectRangeMetres = 40.0;

        /// Identification ranges, clear daylight, by rung. See `IdRung`.
        public const double Rung1SilhouetteMetres = 35.0;
        public const double Rung2MarkMetres = 18.0;
        public const double Rung3FaceMetres = 8.0;

        /// RECOGNITION REACHES FURTHER THAN A FACE, and this is the most
        /// characteristic number in the project. You know how a friend walks.
        /// At twenty metres in the rain a stranger is a shape and your
        /// neighbour is *you* — which is the whole reason the acquaintance
        /// graph makes this game able to do something no AAA crime game can.
        public const double Rung4RecogniseMetres = 25.0;

        /// How well somebody has to know you before gait and bearing carry a
        /// name. Below this they are a stranger and top out at rung 3.
        public const double RecognitionFamiliarity = 0.35;

        /// Seconds of continuous presence in the acuity band before a glance
        /// becomes a look.
        public const double NoticeSeconds = 0.35;

        /// Seconds before an identification is attempted. Slower than
        /// detection, because recognising is harder than spotting.
        public const double IdentifySeconds = 1.2;

        /// THE GAME'S OWN SPEEDS, not a human being's.
        ///
        /// The first version of this file put "running" at 3.2 m/s, which is
        /// roughly a real person's jog and is BELOW this game's walk —
        /// `Locomotion.WalkSpeed` is 4.0 and `RunSpeed` is 7.0. The result was
        /// that walking down the street at night registered as running, and the
        /// sim reported two hundred and seven notices for it in a run where
        /// nobody ran once.
        ///
        /// The numbers were checked against reality instead of against the
        /// project, and the project's copy was in the next folder. So they are
        /// derived now rather than typed, and there is nothing left to drift.
        public static double WalkPace => Locomotion.WalkSpeed;
        public static double RunPace => Locomotion.RunSpeed;

        /// Halfway between a walk and a run is where one becomes the other.
        public static double RunningThreshold => (WalkPace + RunPace) / 2.0;

        /// Below this somebody is standing about rather than moving.
        public const double StillBelow = 0.35;

        /// How fast attention accrues by what the subject is doing. Stillness
        /// is a tactic and running is a confession.
        public static double MotionFactor(double metresPerSecond)
        {
            if (metresPerSecond <= 0.05) return 0.5;             // standing still
            if (metresPerSecond >= RunPace) return 2.0;          // flat out
            // A walk sits at exactly 1.0 and the ends interpolate, so there is
            // no cliff where slowing from a jog to a fast walk halves your
            // exposure.
            return metresPerSecond <= WalkPace
                ? 0.5 + 0.5 * (metresPerSecond - 0.05) / (WalkPace - 0.05)
                : 1.0 + 1.0 * (metresPerSecond - WalkPace) / (RunPace - WalkPace);
        }

        /// Where an angle off the observer's facing falls. Returns 1.0 in the
        /// acuity band, 0.35 in the peripheral band (motion only), 0 outside.
        public static double ConeWeight(double degreesOffAxis)
        {
            double a = Math.Abs(degreesOffAxis);
            if (a <= AcuityDegrees / 2) return 1.0;
            if (a <= FovDegrees / 2) return 0.35;
            return 0.0;
        }

        /// Every visual range is multiplied by how lit the subject is.
        ///
        /// 0..1 in, a multiplier out. Not linear: the difference between a
        /// doorway and an unlit street matters far more than the difference
        /// between overcast and full sun, because the bottom of the range is
        /// where the game is played.
        public static double LightFactor(double lightLevel)
        {
            double l = Feel.Clamp01(lightLevel);
            // 0 → 0.12 (a doorway), 0.25 → ~0.34, 0.5 → ~0.55, 1 → 1.0.
            return Feel.Clamp(0.12 + 0.88 * Math.Pow(l, 0.78), 0.12, 1.0);
        }

        /// Can this observer see that subject at all, before time is counted?
        /// Occlusion is checked LAST by the caller on purpose — see §17.1; a
        /// ray is the expensive test and cone/range/light reject most cases.
        public static bool InSight(double metres, double degreesOffAxis,
                                   double lightLevel, bool occluded,
                                   double subjectSpeed = -1)
        {
            if (occluded) return false;
            // Default to a walking subject rather than to a magic 1.4 that was
            // not this game's walk either.
            if (subjectSpeed < 0) subjectSpeed = WalkPace;
            double w = ConeWeight(degreesOffAxis);
            if (w <= 0) return false;
            // The peripheral band is motion-only. A still subject at the edge
            // of vision is not seen, however lit they are.
            if (w < 1.0 && subjectSpeed < StillBelow) return false;
            return metres <= DetectRangeMetres * LightFactor(lightLevel);
        }

        /// THE IDENTIFICATION LADDER, and it is deliberately NOT monotonic.
        ///
        /// Rung 3 is a face at eight metres; rung 4 is recognition at
        /// twenty-five. An acquaintance therefore skips rung 3 entirely, and a
        /// **stranger can never reach rung 4 at any distance** — being close
        /// to somebody who has never met you does not let them name you.
        /// Calling it a ladder in v3 of the spec implied otherwise and the
        /// review pass caught it.
        ///
        ///   0 "someone"                    3 "I'd know him again"
        ///   1 "a man, big, long coat"      4 "that's Tom, runs the bar"
        ///   2 "the one with the limp"
        public static int IdRung(double metres, double lightLevel,
                                 double familiarity, bool hasDistinguishingMark,
                                 bool faceToward = true)
        {
            double f = LightFactor(lightLevel);
            int best = 0;

            if (metres <= Rung1SilhouetteMetres * f) best = 1;
            if (hasDistinguishingMark && metres <= Rung2MarkMetres * f) best = 2;
            // A face has to be pointed at you. A limp does not, which is why
            // rung 2 survives a subject walking away and rung 3 does not.
            if (faceToward && metres <= Rung3FaceMetres * f) best = 3;
            if (familiarity >= RecognitionFamiliarity && metres <= Rung4RecogniseMetres * f)
                best = 4;

            return best;
        }

        /// THE SYMMETRY RULE, spec §15.1: *if you can tell he is facing you,
        /// and you are in light, he can see you.*
        ///
        /// This is the game's only PROSPECTIVE signal — everything else in the
        /// design tells the player they were seen, and stealth-adjacent play
        /// is planning. The rule is a promise to the player that there is no
        /// hidden third factor, so it has to be true of the model rather than
        /// merely nearly true, which is why it is one function rather than a
        /// paragraph in the how-to-play.
        ///
        /// Facing has to be READABLE for the promise to hold, so this returns
        /// false beyond the distance at which a silhouette resolves — better
        /// to say "you cannot tell" than to imply safety.
        public const double FacingReadableMetres = 18.0;

        public static bool FacingIsReadable(double metres, double lightLevel) =>
            metres <= FacingReadableMetres * LightFactor(lightLevel);

        /// The rule itself, as the player will learn it.
        ///
        /// TWO LIGHTS, NOT ONE, and the first version got this wrong in the one
        /// signal the player is actually promised. Reading his facing needs
        /// light on HIM; his seeing you needs light on YOU. Collapsing them into
        /// a single number makes the rule lie in the case that matters most —
        /// you standing under a lamp reading a man who is in a dark doorway,
        /// where you cannot tell which way he is facing and the model would have
        /// said you could. Same mistake in the same shape as one distance for
        /// the actor and the victim, found by re-reading rather than by a test.
        ///
        /// `lightOnYou` is the number the vignette responds to, so that half of
        /// the promise still comes from one source.
        public static bool SymmetryPredictsSeen(double metres, double degreesOffAxis,
                                                double lightOnYou, double lightOnThem,
                                                bool occluded)
        {
            // Cannot tell which way he is facing → the rule declines to promise.
            if (!FacingIsReadable(metres, lightOnThem)) return false;
            return InSight(metres, degreesOffAxis, lightOnYou, occluded);
        }

        // ---------------------------------------------------------------
        // HEARING — loudness against the local ambient floor
        // ---------------------------------------------------------------

        /// Ambient floors, dB-like units, AT THE LISTENER. Spec §16.2.
        ///
        /// The listener's floor rather than the source's is the whole trick:
        /// it is what lets a shot inside a loud bar still be heard by the
        /// quiet street outside once the wall has taken its cut.
        public const double AmbientNight3am = 15.0;
        public const double AmbientDaytimeStreet = 45.0;
        public const double AmbientMarketNoon = 58.0;
        public const double AmbientBarBusy = 68.0;
        /// Rain adds to whatever floor is under it, outdoors only.
        public const double AmbientRainAdds = 12.0;

        /// Event loudnesses. These are the second draft: the first put a
        /// walking footstep at 20 against a 3am floor of 25, which made
        /// footsteps INAUDIBLE IN A SILENT STREET and flatly contradicted the
        /// spec's own example of the frightened man who hears one behind him.
        /// Caught by re-reading, not by a test, which is the argument for the
        /// worked cases in `CoreTests`.
        public const double LoudFootstepWalk = 25.0;
        public const double LoudFootstepRun = 38.0;
        public const double LoudDoorSlam = 55.0;
        public const double LoudShout = 65.0;
        public const double LoudBottleSmash = 70.0;
        public const double LoudSuppressed22 = 62.0;
        public const double LoudSnub38 = 100.0;

        /// A wall does not scale the radius, it subtracts from the loudness —
        /// which is what makes occlusion compose correctly with masking
        /// instead of fighting it. Matched to `Acoustics.LowPassHz`, where a
        /// wall is a different filter rather than more distance.
        public const double WallAttenuation = 22.0;

        /// Base radius and the doubling interval. `r = Base * 2^((L-A)/Div)`.
        public const double AudibleBaseMetres = 1.5;
        public const double AudibleDivisor = 8.0;
        public const double AudibleCapMetres = 250.0;

        /// How far a sound of this loudness carries to a listener standing in
        /// this much ambient. Zero when the ambient swallows it.
        ///
        /// Worked, so it can be checked rather than trusted:
        ///   footstep 25 @ 3am 15    →  3.6m   (behind you, if you listen)
        ///   footstep 25 @ street 45 →    0    (nothing at all)
        ///   suppressed 62 @ bar 68  →    0    (the jukebox eats it)
        ///   suppressed 62 @ 3am 15  →   86m   (the length of the street)
        ///   snub 100 @ street 45    →  177m
        ///   shout 65 @ market 58    →  2.2m   (which is why shouting fails)
        public static double AudibleRadius(double loudness, double ambientFloor,
                                           bool occluded = false)
        {
            double l = loudness - (occluded ? WallAttenuation : 0.0);
            if (l <= ambientFloor) return 0.0;
            double r = AudibleBaseMetres * Math.Pow(2.0, (l - ambientFloor) / AudibleDivisor);
            return Math.Min(r, AudibleCapMetres);
        }

        /// An alert listener hears more. Not a separate state machine — the
        /// floor drops, so the SAME arithmetic produces escalation. A calm man
        /// ignores a bang two streets away; a frightened one hears a footstep.
        public const double AlertFloorDrop = 8.0;

        public static double EffectiveFloor(double ambientFloor, double alertness) =>
            ambientFloor - AlertFloorDrop * Feel.Clamp01(alertness);

        public static bool Heard(double metres, double loudness, double ambientFloor,
                                 bool occluded = false, double alertness = 0)
            => metres <= AudibleRadius(loudness, EffectiveFloor(ambientFloor, alertness), occluded);

        /// Hearing gives direction and distance, never identity. Kept as a
        /// function so no caller can accidentally pass a name through it: the
        /// asymmetry between "a shot, that way, close" and "Tom fired it" is
        /// the entire design space this system opens up.
        public static (double bearing, double metres) HeardAs(
            double bearingDegrees, double metres) => (bearingDegrees, metres);

        // ---------------------------------------------------------------
        // ATTENTION — the accumulator, which is where the bugs live
        // ---------------------------------------------------------------

        /// One observer's attention on one subject.
        ///
        /// TIME-WEIGHTED, NOT SAMPLE-COUNTED, and this is not a detail. §17.1
        /// recomputes vision at ~6Hz staggered rather than every frame, so
        /// counting samples would make notice time depend on the tick rate and
        /// on frame rate — the exact bug that produced a 13fps reading from a
        /// 104fps stream in `FrameRate`. Every accrual is multiplied by the dt
        /// it covers, so a 6Hz tick and a 60Hz tick reach `NoticeSeconds` at
        /// the same wall-clock moment.
        public struct Attention
        {
            double _seconds;      // effective, motion-weighted seconds accrued
            double _rung;         // best identification reached, as a double for decay

            public double Seconds => _seconds;
            public bool Noticed => _seconds >= NoticeSeconds;
            public bool Identified => _seconds >= IdentifySeconds;
            public int Rung => (int)Math.Round(_rung);

            /// `dt` is real seconds since this pair was last evaluated — which
            /// at 6Hz staggered is about 0.167, not a frame.
            public void Tick(double dt, bool inSight, double coneWeight,
                             double motionFactor, int rungIfIdentified)
            {
                if (!(dt > 0)) return;                  // catches zero, negative, NaN

                if (!inSight)
                {
                    // Attention fades rather than resetting. A man who glanced
                    // at you, looked away and glanced back has been looking at
                    // you, and a hard reset would let a player pump the system
                    // by stepping in and out of a doorway.
                    _seconds = Math.Max(0, _seconds - dt * 0.6);
                    return;
                }

                _seconds += dt * coneWeight * motionFactor;

                if (_seconds >= IdentifySeconds && rungIfIdentified > _rung)
                    _rung = rungIfIdentified;
            }

            /// What this observer would say, if asked, right now.
            public int Reached() => Noticed ? Rung : 0;
        }
    }
}
