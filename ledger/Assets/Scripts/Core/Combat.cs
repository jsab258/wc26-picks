using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// Combat, phases 1 and 2 (game-design/combat-spec.md).
    ///
    /// The filter that decides everything, from agency-model.md: **violence
    /// is SEEN.** In a game whose antagonist is gossip, a fight's cost is
    /// witnesses rather than damage — so the witness rules are not a
    /// follow-up feature, they are half of what combat IS.
    ///
    /// Jafar's lethality answer set a harder problem than the one I proposed.
    /// Killing a witness has to GENUINELY WORK — the rumour must actually
    /// stop — or the choice is fake and the player notices inside one
    /// attempt. So violence must work and cost more than it saves, which is
    /// harder to balance than violence that simply does not work.
    public enum Blow
    {
        /// Not an attack. A stance change everyone can see.
        SquareUp,
        /// One committed swing: slow, telegraphed, heavy.
        Strike,
        /// Distance, not damage. The de-escalation tool.
        Shove,
        /// Absorb rather than avoid.
        Guard,
        /// Leave. A verb, and usually the right one.
        BackOff,
        /// NOT a combat move — a decision made afterwards, with somebody on
        /// the ground and the street watching. Deliberately separate so it
        /// can never happen in the flow of a scuffle.
        Finish,
    }

    /// How badly somebody is doing. Read off the body, never off a bar.
    public enum Footing
    {
        Steady,
        /// Rocked. Guard is dropping.
        Reeling,
        /// On the ground. Cannot act; can be finished.
        Down,
    }

    public class Fighter
    {
        public string Id;
        public string Name;
        /// 0..1, from HarmBook.Capability. A hurt fighter is a worse one.
        public double Capability = 1.0;
        /// 0..1. Spent by striking, recovered by not. Not displayed as a
        /// number — it is breathing, and a guard that drops.
        public double Stamina = 1.0;
        public Footing Footing = Footing.Steady;
        public bool Guarding;
        /// Accumulated punishment this fight. Resets between fights; the
        /// LASTING damage is HarmBook's job, not this one's.
        public double Punished;

        public bool CanAct => Footing != Footing.Down;
    }

    /// What one exchange did. Returned rather than applied, so the caller
    /// decides what it means — and so all of it is testable without a world.
    public struct BlowResult
    {
        public bool Landed;
        public bool Guarded;
        /// The target went down on this blow.
        public bool Floored;
        /// Somebody died. Rare, permanent, and never accidental — only a
        /// deliberate Finish on somebody already Down.
        public bool Killed;
        /// 0..1, how hard. Drives the sound and the camera, not a number on
        /// screen.
        public double Force;
        public string Why;
    }

    public static class Combat
    {
        /// Metres. Beyond this a strike cannot reach, and the game must never
        /// let one connect anyway — a hit at four metres is the fastest way
        /// to lose a player's trust in a fight.
        public const double Reach = 1.6;
        public const double ShoveReach = 1.9;

        /// What a swing costs the swinger. Striking when exhausted is how a
        /// fight turns, and it should be the player's own fault.
        ///
        /// RETUNED 2026-07-28 after BalanceLab's fight lab found the whole
        /// system inert. At the original numbers a clean strike did 0.86
        /// against a floor of 1.0, so a fight was over in TWO BLOWS and
        /// stamina fell from 1.00 to 0.88 in the course of it. Every
        /// mechanic in this file except Strike was therefore decorative —
        /// guard, footing and stamina never got a turn — and the lab's
        /// verdict was blunt: mashing Strike won 76% of exchanges and took
        /// the LEAST punishment doing it, which is exactly the outcome
        /// combat-spec §2 says breaks the fiction.
        ///
        /// A fight is now three to four committed swings, and by the last
        /// one a mashing player is hitting at 0.59 instead of 0.81 — down
        /// nearly a third, because they spent everything early. That is the
        /// mechanic the constant was written for, finally reachable.
        public const double StrikeStamina = 0.34;
        public const double ShoveStamina = 0.10;
        /// Per second, when not striking. Deliberately slower than a swing
        /// costs: a fighter who can mash and recover has no reason to stop.
        public const double StaminaRecovery = 0.09;

        /// Punishment needed to floor somebody, at full capability.
        public const double FloorAt = 2.8;

        public static double StaminaCost(Blow b) =>
            b == Blow.Strike ? StrikeStamina :
            b == Blow.Shove ? ShoveStamina : 0.0;

        /// Can this blow even be attempted right now? Separated from
        /// resolution so the UI can grey a verb out for the SAME reason the
        /// simulation will refuse it — a prompt that offers something the
        /// rules then decline is the definition of clunky.
        public static bool Available(Blow b, Fighter self, Fighter target, double metres)
        {
            if (self == null || !self.CanAct) return false;
            if (b == Blow.BackOff) return true;
            if (b == Blow.Guard) return self.Stamina > 0.05;
            if (target == null) return false;
            switch (b)
            {
                case Blow.SquareUp: return target.CanAct && metres <= 6.0;
                case Blow.Strike:
                    return target.CanAct && metres <= Reach && self.Stamina >= StrikeStamina;
                case Blow.Shove:
                    return target.CanAct && metres <= ShoveReach && self.Stamina >= ShoveStamina;
                case Blow.Finish:
                    // ONLY on somebody already down, and only within reach.
                    // The separation is the design: this must never be
                    // something that happens mid-scuffle.
                    return target.Footing == Footing.Down && metres <= Reach;
                default: return false;
            }
        }

        /// Resolve one blow. No randomness: a fight the player cannot read is
        /// a fight they cannot learn, and dice make every telegraph a lie.
        public static BlowResult Resolve(Blow b, Fighter self, Fighter target, double metres)
        {
            var r = new BlowResult();
            if (!Available(b, self, target, metres))
            {
                r.Why = "not available";
                return r;
            }

            self.Stamina = Feel.Clamp01(self.Stamina - StaminaCost(b));

            switch (b)
            {
                case Blow.BackOff:
                case Blow.SquareUp:
                    r.Why = b.ToString();
                    return r;

                case Blow.Guard:
                    self.Guarding = true;
                    r.Why = "guard";
                    return r;

                case Blow.Shove:
                {
                    r.Landed = true;
                    r.Force = 0.3;
                    // A shove never injures and never floors a steady
                    // fighter. It buys distance, which is the point.
                    if (target.Footing == Footing.Reeling)
                    {
                        target.Footing = Footing.Down;
                        r.Floored = true;
                    }
                    r.Why = "shove";
                    return r;
                }

                case Blow.Strike:
                {
                    // A tired swing is a weak one. This is the whole reason
                    // stamina exists, and it is felt rather than read.
                    double power = 0.55 + 0.45 * self.Stamina;
                    power *= 0.5 + 0.5 * Feel.Clamp01(self.Capability);
                    r.Guarded = target.Guarding;
                    // Guarding ABSORBS, it does not negate — a guard that
                    // makes you invulnerable is a guard the player holds
                    // forever.
                    // A guard now saves nearly four fifths rather than two
                    // thirds. At the old value guarding cost a whole turn to
                    // avoid a third of one hit, which is a losing trade in
                    // every situation — so the verb existed and nobody would
                    // ever have used it.
                    double through = target.Guarding ? power * 0.22 : power;
                    target.Punished += through;
                    target.Guarding = false;      // a landed blow breaks it

                    double floorAt = FloorAt * Feel.Clamp(target.Capability, 0.35, 1.0);
                    if (target.Punished >= floorAt)
                    {
                        target.Footing = Footing.Down;
                        r.Floored = true;
                    }
                    else if (target.Punished >= floorAt * 0.55)
                    {
                        target.Footing = Footing.Reeling;
                    }
                    r.Landed = true;
                    r.Force = Feel.Clamp01(through);
                    r.Why = r.Guarded ? "struck through a guard" : "struck clean";
                    return r;
                }

                case Blow.Finish:
                    // Rare, permanent, deliberate. There is no path to this
                    // that does not go through a decision made in the quiet
                    // afterwards.
                    r.Landed = true;
                    r.Killed = true;
                    r.Force = 1.0;
                    r.Why = "finished";
                    return r;
            }
            r.Why = "nothing";
            return r;
        }

        /// Not striking is how you get your wind back.
        public static void Breathe(Fighter f, double seconds)
        {
            if (f == null || seconds <= 0) return;
            f.Stamina = Feel.Clamp01(f.Stamina + StaminaRecovery * seconds);
        }
    }

    // ---------------------------------------------------------------------

    /// WHO SAW IT (combat-spec §7b, phase 2).
    ///
    /// A fight is the loudest event in the game, and its cost is entirely
    /// here. Fighting in an alley at night is a different act from fighting
    /// outside the bar at noon, and that difference IS the game.
    public class FightWitness
    {
        public string Id;
        public double Metres;
        public bool Occluded;
    }

    public static class Violence
    {
        /// A scuffle carries further than speech — bodies are loud — so it
        /// gets the shout range rather than the speaking one.
        public const double SeenFrom = Acoustics.ShoutCarry;

        /// How sure a witness is about a FIGHT. Higher than for overheard
        /// speech at the same distance: you do not need to make out words to
        /// know what you are looking at.
        public static double Confidence(double metres, bool occluded, double streetNoise = 0)
        {
            if (metres > SeenFrom) return 0;
            double i = Acoustics.Intelligibility(metres, occluded, streetNoise, SeenFrom);
            double c = 0.35 + 0.6 * i;
            // Through a wall you heard it and did not see it: you know
            // something happened and not what.
            if (occluded) c = Math.Min(c, 0.5);
            return Feel.Clamp(c, 0.0, 0.95);
        }

        /// Everyone near enough to carry it away.
        public static List<FightWitness> Saw(IEnumerable<FightWitness> nearby,
                                             double streetNoise = 0)
        {
            var seen = new List<FightWitness>();
            if (nearby == null) return seen;
            foreach (var w in nearby)
                if (w != null && Confidence(w.Metres, w.Occluded, streetNoise) > 0.05)
                    seen.Add(w);
            return seen;
        }

        /// THE ONE FACT THAT CANNOT BE DISCREDITED.
        ///
        /// Every other rumour in this game can be muddied, contradicted,
        /// suppressed or left to decay. None of that machinery touches a
        /// corpse. That asymmetry against everything else in the mill is what
        /// makes killing terrifying rather than efficient — and it is why a
        /// killing is recorded at a confidence the discredit path cannot
        /// reach, for everybody who saw it, regardless of distance.
        public const double BodyConfidence = 1.0;

        /// A killing is known to everyone in sight AT CERTAINTY, and to the
        /// wider street as a fact soon after, because a body does not stay a
        /// rumour. Distance changes who saw YOU do it — not whether it
        /// happened.
        public static double KillingConfidence(double metres, bool occluded)
        {
            if (metres > SeenFrom) return 0;
            // Seeing it is being certain. This is the point: the thing that
            // makes murder work as a solution is exactly what makes it
            // impossible to walk back.
            return occluded ? 0.6 : BodyConfidence;
        }

        /// What a fight is worth as a topic. A brawl outside the bar at noon
        /// is the day's news; the same fight in an alley at three is a sound
        /// somebody half-heard.
        public static double Notoriety(int witnessCount, bool killed)
        {
            double n = Feel.Clamp01(witnessCount / 6.0);
            return killed ? Feel.Clamp(0.75 + 0.25 * n, 0.75, 1.0) : n * 0.7;
        }
    }
}
