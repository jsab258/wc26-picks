using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// WHAT IS ON YOU TONIGHT — `weapons-spec.md` §7.1 and §7.2.
    ///
    /// NOT AN INVENTORY. There is no grid, no weight and no bag: the constraint
    /// is **concealment**, and the whole decision is *what did I bring* — made
    /// at the door, before you know what the night holds, which is precisely
    /// what makes it a decision rather than a shopping trip. A player who can
    /// carry everything has not decided anything.
    ///
    /// There is one screen and it is the coat: what is on you, and what is at
    /// home in the bar.
    public class Coat
    {
        readonly List<Traces.Item> _onMe = new List<Traces.Item>();
        readonly List<Traces.Item> _atHome = new List<Traces.Item>();

        public IReadOnlyList<Traces.Item> OnMe => _onMe;
        public IReadOnlyList<Traces.Item> AtHome => _atHome;

        public IEnumerable<Weapon> CarriedWeapons =>
            _onMe.Select(i => Arsenal.Get(i.WeaponId)).Where(w => w != null);

        public void Store(Traces.Item it)
        {
            if (it == null || it.Disposed) return;
            _onMe.Remove(it);
            if (!_atHome.Contains(it)) _atHome.Add(it);
        }

        /// Take something with you. Fails when it will not fit under the coat,
        /// which is the entire limit.
        public bool Take(Traces.Item it)
        {
            if (it == null || it.Disposed || _onMe.Contains(it)) return false;
            var w = Arsenal.Get(it.WeaponId);
            if (w == null) return false;
            if (!Arsenal.Fits(CarriedWeapons, w)) return false;
            _atHome.Remove(it);
            _onMe.Add(it);
            return true;
        }

        public bool Drop(Traces.Item it) => it != null && _onMe.Remove(it);

        /// THE DECISION AT THE DOOR, as a predicate rather than as prose. It is
        /// only a real decision while something has to be left behind.
        public bool IsAChoice => _atHome.Count > 0 && !CanTakeEverything;

        public bool CanTakeEverything
        {
            get
            {
                var all = _onMe.Concat(_atHome).Select(i => Arsenal.Get(i.WeaponId))
                               .Where(w => w != null).ToList();
                if (all.Count == 0) return true;
                // Ask whether the whole pile would fit, by adding the last one
                // to the rest — `Fits` already answers exactly this.
                return Arsenal.Fits(all.Take(all.Count - 1), all[all.Count - 1]);
            }
        }

        // ---------------------------------------------------------------
        // THE FRISK — spec §7.2, which is the entire cost of carrying
        // ---------------------------------------------------------------

        /// Who is allowed to do it. NEVER AT RANDOM: a frisk follows suspicion,
        /// a place with a rule, or somebody deciding to make a point.
        public enum Frisker
        {
            /// Any point once you are a person of interest.
            Constable,
            /// A place that has one, and refusing means not going in.
            Doorman,
            /// One of the outfits, as a demonstration rather than a search.
            Outfit,
            /// A conversation rather than a search, and much worse for it.
            Ellis,
        }

        public static bool MayFrisk(Frisker who, double suspicion, bool placeHasARule,
                                    bool makingAPoint)
        {
            switch (who)
            {
                case Frisker.Constable: return suspicion >= 0.4;
                case Frisker.Doorman: return placeHasARule;
                case Frisker.Outfit: return makingAPoint;
                case Frisker.Ellis: return suspicion >= 0.25;
                default: return false;
            }
        }

        /// REFUSING IS AN ANSWER. It is not a crime and it is not free —
        /// refusing a doorman means not going in, and refusing a constable is
        /// itself a thing people saw you do.
        public enum Refusal { Allowed, NotGoingIn, SomethingPeopleSaw, MakesItWorse }

        public static Refusal IfYouRefuse(Frisker who) =>
            who == Frisker.Doorman ? Refusal.NotGoingIn
          : who == Frisker.Constable ? Refusal.SomethingPeopleSaw
          : who == Frisker.Outfit ? Refusal.MakesItWorse
          : Refusal.SomethingPeopleSaw;

        /// The worst thing they would find, 0..1. Zero when there is nothing on
        /// you worth a question.
        public double WorstFind() =>
            CarriedWeapons.Select(Arsenal.FriskCost).DefaultIfEmpty(0).Max();

        /// FOUND IS WORSE THAN USED, and this is the number that says so.
        ///
        /// A clean knife found on you the night after a stabbing on your street
        /// is not evidence of anything and will convict you socially anyway —
        /// so the cost is the object's concealment scaled by how much the
        /// street is already talking, not by what the object has actually done.
        public double CostIfFound(double streetHeat) =>
            Feel.Clamp01(WorstFind() * (0.45 + 0.9 * Feel.Clamp01(streetHeat)));

        /// And the one case where it is not about the object at all: a weapon
        /// with a killing in its history, found on you, is a different order of
        /// problem, because provenance turns the frisk into an interrogation.
        public bool CarryingSomethingUsed() => _onMe.Any(i => i.UsedInAKilling);
    }
}
