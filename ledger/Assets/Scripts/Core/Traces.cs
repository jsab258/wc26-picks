using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// WHAT VIOLENCE LEAVES BEHIND — on you, and on the object.
    ///
    /// `weapons-spec.md` §15.4 and §7.4, both of which were promised in three
    /// places and specified in none until the audit.
    ///
    /// THE POINT OF BOTH IS TIME. One violent minute should cost three in-game
    /// days, and the cheapest way to buy that is to make the aftermath
    /// something people can SEE and something Ellis can FOLLOW. Neither needs
    /// new perception code — blood is another thing the vision model notices,
    /// and provenance is a string on an object.
    public class Stain
    {
        /// In-game minutes since it happened.
        public double AgeMinutes;
        /// 0..1. Fresh blood on a light coat is obvious; a day-old smear is a
        /// mark somebody might mention.
        public double Strength = 1.0;
        /// Whose, which matters for the writing rather than for the maths.
        public string FromWhom;
        /// Yours, from a bottle that broke, is a different conversation.
        public bool YourOwn;
    }

    public static class Traces
    {
        // ---------------------------------------------------------------
        // BLOOD — spec §15.4
        // ---------------------------------------------------------------

        /// Which families mark you at all. Firearms, the cosh and an accident
        /// do not, which is most of the reason to choose them.
        public static bool Marks(Weapon w) => w != null && w.MarksYou;

        /// Blood is noticed at conversational distance under a light and not at
        /// all across a dark street. Same vision model as everything else,
        /// just with a much shorter range — which is why a stain that would
        /// ruin you in the bar is invisible on the walk home.
        public static bool Noticeable(Stain s, double metres, double lightLevel)
        {
            if (s == null || s.Strength <= 0.15) return false;
            double range = Notice.BloodNoticeMetres
                           * Perception.LightFactor(lightLevel)
                           * (0.6 + 0.4 * Feel.Clamp01(s.Strength));
            return metres <= range;
        }

        /// It does not fade on its own in any useful way. That is the design:
        /// dealing with it has to be a decision you make, not a timer you wait
        /// out. Over a whole day it dulls to a mark that is still describable.
        public const double StainFloor = 0.45;

        public static void Age(Stain s, double minutes)
        {
            if (s == null || !(minutes > 0)) return;
            s.AgeMinutes += minutes;
            // Roughly: half a day to reach the floor, and then it stays.
            double dried = 1.0 - 0.55 * Feel.Clamp01(s.AgeMinutes / (12 * 60));
            s.Strength = Math.Max(StainFloor, Math.Min(s.Strength, dried));
        }

        /// Washing takes time and a place. Changing needs the second coat you
        /// thought to bring. Both are verbs; neither is free.
        public const double WashMinutes = 25;

        public static bool Wash(Stain s, double minutesSpent, bool hasWaterAndPrivacy)
        {
            if (s == null || !hasWaterAndPrivacy || minutesSpent < WashMinutes) return false;
            s.Strength = 0;
            return true;
        }

        /// A stain is rung-2 evidence — a distinguishing mark, exactly like the
        /// limp. Not proof of anything; a thing people can describe. Which
        /// means it feeds the identification ladder rather than the case file.
        public static bool CountsAsMark(Stain s) => s != null && s.Strength > 0.3;

        /// WHO SEES IT MATTERS MORE THAN THAT IT EXISTS. Blood noticed by a
        /// stranger is a rumour. Blood noticed by the woman you are seeing is a
        /// scene, and this is the number that makes the difference arithmetic
        /// rather than authorial.
        public static double SocialCost(Stain s, double familiarity)
            => s == null ? 0
             : Feel.Clamp01(s.Strength) * (0.3 + 1.2 * Feel.Clamp01(familiarity));

        // ---------------------------------------------------------------
        // PROVENANCE — spec §7.3 and §7.4
        // ---------------------------------------------------------------

        /// Where a particular object came from. FOUR ROUTES, ALL SOCIAL, and
        /// no random world loot: a pistol in a bin is a video game, a pistol
        /// you can name the seller of is this game.
        public enum Origin
        {
            /// From a person with a schedule, a price and a memory. He can be
            /// leaned on later — by you, or by Ellis.
            Bought,
            /// From a person or a room, on a real schedule, and they NOTICE it
            /// is gone at a time you could have predicted.
            Stolen,
            /// Off somebody in a fight, or off a body. Free, immediate, and the
            /// worst possible history attached.
            Taken,
            /// Exactly once, and authored: something of Mickey's, in the bar.
            Inherited,
            /// A kitchen knife. Untraceable by being ordinary.
            Ordinary,
        }

        /// One physical object with a history. This is what makes the murder
        /// weapon a real thing rather than an inventory row.
        public class Item
        {
            public string InstanceId;
            public string WeaponId;
            public Origin Origin;
            /// Who sold, owned, or lost it — the thread Ellis pulls.
            public string FromWhom;
            /// What has been done with it, in order. Never cleared.
            public readonly List<string> History = new List<string>();
            public bool Disposed;
            public string DisposedWhere;
            /// Whether anybody saw you get rid of it, which is the whole point
            /// of disposal being a verb rather than a menu action.
            public bool DisposalWitnessed;

            public bool UsedInAKilling => History.Any(h => h.StartsWith("killed:"));
        }

        public static Item Acquire(string instanceId, string weaponId, Origin origin,
                                   string fromWhom)
        {
            var w = Arsenal.Get(weaponId);
            // A kitchen knife is ORDINARY whatever route it came by, because
            // ordinariness is a property of the object and not of the
            // transaction. This is the one place the two can disagree and the
            // object wins.
            if (w != null && w.Anonymous && origin == Origin.Bought) origin = Origin.Ordinary;
            var it = new Item
            {
                InstanceId = instanceId, WeaponId = weaponId,
                Origin = origin, FromWhom = origin == Origin.Ordinary ? null : fromWhom,
            };
            it.History.Add($"acquired:{origin}");
            return it;
        }

        public static void Used(Item it, string what, string onWhom)
        {
            if (it == null) return;
            it.History.Add($"{what}:{onWhom}");
        }

        /// CAN ELLIS FOLLOW IT BACK TO YOU?
        ///
        /// This is the payoff for keeping provenance at all, and the answer is
        /// deliberately not binary — it is how strong the thread is.
        public static double Traceability(Item it)
        {
            if (it == null) return 0;
            switch (it.Origin)
            {
                // A named seller who remembers is the strongest thread in the
                // game, and it is a thread that leads to a conversation rather
                // than to a forensics lab, which is much more this game.
                case Origin.Bought: return 0.85;
                // Somebody is already angry about it and has told people.
                case Origin.Stolen: return 0.6;
                // It belonged to a man who is now dead or beaten, and his
                // people know what he carried.
                case Origin.Taken: return 0.45;
                // Mickey's. It is known in the neighbourhood, which cuts both
                // ways: it is his, and everyone knows whose bar it is now.
                case Origin.Inherited: return 0.55;
                // Every kitchen has one. There is nothing to follow.
                case Origin.Ordinary: return 0.05;
                default: return 0.3;
            }
        }

        /// DISPOSAL IS A VERB THAT CAN BE WITNESSED, which is the best single
        /// idea to survive from v1 of the spec untouched.
        ///
        /// Getting rid of it removes the object and leaves the act of getting
        /// rid of it — and if somebody saw that, you have traded a findable
        /// weapon for a witness who watched a man drop something in the canal
        /// at two in the morning.
        public static void Dispose(Item it, string where, bool seen)
        {
            if (it == null || it.Disposed) return;
            it.Disposed = true;
            it.DisposedWhere = where;
            it.DisposalWitnessed = seen;
            it.History.Add($"disposed:{where}");
        }

        /// What the object still costs you once it is gone. Never zero if it
        /// was used in a killing and somebody watched you get rid of it: that
        /// is a worse position than having kept it, and the player should be
        /// able to reason their way to that before finding out.
        public static double ResidualRisk(Item it)
        {
            if (it == null) return 0;
            if (!it.Disposed) return it.UsedInAKilling ? Traceability(it) : Traceability(it) * 0.3;
            if (it.DisposalWitnessed) return Math.Max(0.5, Traceability(it));
            // Gone, unseen. The thread back to the seller survives the object,
            // because he still remembers selling it.
            return Traceability(it) * 0.35;
        }
    }
}
