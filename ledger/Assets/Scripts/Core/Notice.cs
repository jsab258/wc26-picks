using System;

namespace Ledger.Core
{
    /// WHAT A STREET NOTICES THAT IS NOT A CRIME.
    ///
    /// This file is the reason Phase 1 is worth playing before any weapon
    /// exists. `weapons-spec.md` §3.3 promises the KCD2 feeling — people
    /// noticing you loiter, noticing you run at night, heads coming to windows
    /// at a slammed door — and the original Phase 1 gate tested detection
    /// ranges and occlusion, which is the machinery rather than the
    /// experience. A green Phase 1 could therefore have shipped a city that
    /// computes perfectly and reacts to nothing, which is this project's
    /// signature failure mode and the reason the audit moved these rules
    /// forward into Phase 1.
    ///
    /// KCD2's actual lesson is that the reactivity is BROAD: NPCs react to
    /// being drunk in daylight and to walking around undressed, not only to
    /// crime. None of what follows needs violence to exist.
    public enum Notable
    {
        None = 0,
        /// Standing about where nobody stands about. The commonest one and the
        /// one that makes a street feel inhabited rather than staged.
        Loitering,
        /// Running is normal at noon and is a statement at three in the
        /// morning. Same action, different hour, different meaning — which is
        /// the cheapest possible way to make the clock matter.
        RunningAtNight,
        /// Behind the counter, in the yard, through the wrong door.
        WhereYouShouldNotBe,
        /// A slam, a smash, a shout. Routed through `Perception` hearing, so
        /// what carries depends on the hour and the weather.
        Noise,
        /// Blood on a coat, at conversational distance under a light. Rung-2
        /// evidence: a thing people can describe, never proof of anything.
        BloodOnClothes,
        /// Carrying something you cannot explain, in the open.
        WeaponVisible,
    }

    public static class Notice
    {
        /// Seconds of standing still in view before it reads as loitering
        /// rather than as waiting for somebody. Long enough that crossing a
        /// street or reading a noticeboard is free.
        public const double LoiterSeconds = 30.0;

        /// Below this the sun is up enough that running is just running.
        public const double NightAmountForRunning = 0.5;

        /// Blood is noticed at conversational distance under a light, and not
        /// at all across a dark street. It is the same vision model as
        /// everything else, just with a much shorter range — which is why a
        /// stain that would ruin you in the bar is invisible on the walk home.
        public const double BloodNoticeMetres = 4.5;

        /// What is the most noteworthy thing about this person right now?
        ///
        /// Ordered by how strongly a passer-by would react rather than by
        /// severity to the player, because the street does not know what any
        /// of it means yet. A visible weapon beats blood beats trespass.
        public static Notable What(double secondsStationaryInView, double speed,
                                   double nightAmount, bool whereTheyShouldNotBe,
                                   bool bloodVisible, bool weaponVisible)
        {
            if (weaponVisible) return Notable.WeaponVisible;
            if (bloodVisible) return Notable.BloodOnClothes;
            if (whereTheyShouldNotBe) return Notable.WhereYouShouldNotBe;
            // Derived, not typed. `Perception.RunningThreshold` comes from
            // `Locomotion`, so this cannot disagree with what the player's legs
            // actually do — which it did, badly, when it was a literal 3.2.
            if (speed >= Perception.RunningThreshold && nightAmount >= NightAmountForRunning)
                return Notable.RunningAtNight;
            if (secondsStationaryInView >= LoiterSeconds) return Notable.Loitering;
            return Notable.None;
        }

        /// How hard this pulls attention, 0..1. Feeds the same accumulator
        /// vision uses, so a noteworthy person is noticed FASTER rather than
        /// through a separate code path.
        public static double Interest(Notable n, double nightAmount)
        {
            switch (n)
            {
                case Notable.WeaponVisible: return 1.0;
                case Notable.BloodOnClothes: return 0.85;
                case Notable.WhereYouShouldNotBe: return 0.7;
                // Running at night is more alarming the darker it is, which
                // means the same sprint reads differently at dusk and at 3am
                // without a second rule saying so.
                case Notable.RunningAtNight: return Feel.Clamp(0.35 + 0.45 * nightAmount, 0, 1);
                case Notable.Loitering: return 0.4;
                default: return 0.0;
            }
        }

        /// Does this person merely LOOK, or do they say something?
        ///
        /// The four channels in spec §6.2 are deliberately redundant, and this
        /// is the one that decides whether channel 2 fires. Nerve decides:
        /// somebody timid looks away and says nothing, and a bark from a bold
        /// neighbour is what turns "I think that man saw me" into certainty.
        public static bool WorthRemarking(Notable n, double nerve, double nightAmount = 0)
            => n != Notable.None && Interest(n, nightAmount) * (0.35 + 0.9 * Feel.Clamp01(nerve)) >= 0.45;

        // ---------------------------------------------------------------
        // THE STREET GOING QUIET — channel 1, and the best idea in §6.2
        // ---------------------------------------------------------------

        /// How much of the ambient chatter drops when this many people nearby
        /// have their attention on you, out of this many people present.
        ///
        /// THE EXACT INVERSE OF MASKING, from the same system, for free. The
        /// ambient bed that hides your noise is the same bed whose ABSENCE
        /// announces that you have been clocked — a crowd going quiet is the
        /// most recognisable "you have been noticed" signal a human being
        /// knows, it needs no animation at all, and on thirteen boxes with no
        /// faces that matters more than any amount of gaze work.
        ///
        /// It also runs backwards: the street picking back up is how the
        /// player learns the moment has passed, which is the other thing
        /// stealth-adjacent games are chronically bad at communicating.
        ///
        /// Not linear. Two people out of forty falling silent is a real,
        /// noticeable hole in a room's sound, so the curve is steep early and
        /// then saturates — total silence is reserved for total attention.
        /// A CROWD IS NEEDED FOR A CROWD TO GO QUIET, and the first version
        /// forgot to say so: with one person nearby and that person looking at
        /// you, `attending / present` is 1.0 and the whole street fell silent.
        /// The CI run reported a peak hush of exactly 1.00, which is the number
        /// telling you the model has no idea how many people are there.
        ///
        /// Below this many people the effect is scaled down by how far short of
        /// a crowd it is — two people falling quiet in a market is a hole in the
        /// sound, and two people falling quiet on an empty street is just two
        /// people, because there was nothing to stop.
        public const int CrowdFloor = 8;

        public static double HushFraction(int attending, int present)
        {
            // `present <= 0` is DEAD for correctness and kept anyway, proved
            // by a break run rather than assumed either way: with nobody on
            // the street `crowd` below is already zero, so the whole
            // expression is zero however loudly the share divides. What it
            // actually buys is not having to reason about `attending / 0`
            // producing an infinity that then gets clamped — behaviour that
            // is correct by IEEE and horrible to rely on in a line somebody
            // will edit later.
            if (present <= 0 || attending <= 0) return 0.0;
            double share = Feel.Clamp01((double)attending / present);
            double crowd = Feel.Clamp01((double)present / CrowdFloor);
            // The exponent is above one, not below it. The first draft had
            // 0.45, which is the shape that SATURATES early — it made two
            // people out of forty a 2% change, inaudible, when the whole point
            // is that a small hole in a room's sound is the thing you notice.
            // Caught by a test asserting two-of-forty is audible.
            return Feel.Clamp01((1.0 - Math.Pow(1.0 - share, 4.0)) * crowd);
        }

        /// The ambient floor after the hush, which is what closes the loop:
        /// a street that has gone quiet because it is watching you is a street
        /// in which your next sound carries FURTHER. Being noticed makes you
        /// louder. Nothing else in the design has that shape and it falls
        /// straight out of putting both halves on one number.
        public static double FlooredBy(double ambientFloor, double hush)
        {
            // A hush takes the crowd out of the bed but not the rain, the
            // traffic or the sea — hence a floor under the floor.
            const double Irreducible = 12.0;
            double drop = (ambientFloor - Irreducible) * Feel.Clamp01(hush);
            return Math.Max(Irreducible, ambientFloor - drop);
        }

        /// How fast the street recovers, per second, once attention drops. Slow
        /// enough to be felt as a held breath rather than a glitch.
        public const double HushRecoverPerSecond = 0.45;
    }
}
