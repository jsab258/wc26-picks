using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// WHAT IS ON YOU TONIGHT — weapons-spec §7.1 and §7.2, wired.
    ///
    /// `Core/Coat` is the whole design: there is no grid, no weight and no bag,
    /// the constraint is CONCEALMENT, and the decision is *what did I bring* —
    /// made at the door, before you know what the night holds, which is exactly
    /// what makes it a decision rather than a shopping trip.
    ///
    /// Every one of its eleven public members had zero callers. `MayFrisk` 0,
    /// `IfYouRefuse` 0, `WorstFind` 0, `CostIfFound` 0, `CarryingSomethingUsed`
    /// 0. The whole cost of carrying was written, unit-tested, green, and could
    /// not happen. This is where it happens.
    ///
    /// ONE COAT, ON THE PLAYER, held statically for the same reason `Witnesses`
    /// is static: the frisk, the arrest, the panel and the sim gate all have to
    /// read the same coat rather than three copies that drift.
    public static class CoatHost
    {
        public static readonly Coat Player = new Coat();

        /// IS THE PLAYER VISIBLY CARRYING SOMETHING, cached because the street
        /// asks once per walker per frame and the answer changes when a coat is
        /// packed.
        ///
        /// `HeldObject.VisibleWhenCarried` decides it — a bat or a sawn-off has
        /// `Concealment.Impossible` and is carried in the open, which its own
        /// comment calls "a different decision entirely" and says "the street
        /// should be able to see that decision". The street could not: the one
        /// call that asks about a notable person passed `weaponVisible: false`
        /// as a literal, and `VisibleWhenCarried` had no callers at all.
        ///
        /// Refreshed by the population pass rather than computed on demand.
        /// `CarriedWeapons` is a LINQ projection and the asker is every walker
        /// on every frame; once a second is what a reading costs, and the coat
        /// changes at a door rather than at sixty hertz.
        public static bool ShowingWeapon { get; private set; }

        public static void RefreshShowingWeapon()
        {
            bool showing = false;
            foreach (var w in Player.CarriedWeapons)
                if (HeldObject.VisibleWhenCarried(w)) { showing = true; break; }
            ShowingWeapon = showing;
        }

        public static int Frisks { get; private set; }
        public static int FrisksRefused { get; private set; }
        public static int FrisksThatFoundSomething { get; private set; }
        public static double WorstCostPaid { get; private set; }
        public static Coat.Refusal LastRefusal { get; private set; }
        public static bool LastFriskFoundAKilling { get; private set; }

        public static void Reset()
        {
            Frisks = FrisksRefused = FrisksThatFoundSomething = 0;
            WorstCostPaid = 0;
            LastRefusal = Coat.Refusal.Allowed;
            LastFriskFoundAKilling = false;
        }

        // ---- THE DECISION AT THE DOOR -------------------------------------

        /// Take it with you. False when it will not fit under the coat, which
        /// is the entire limit and the entire decision.
        public static bool Carry(Traces.Item it) => Player.Carry(it);

        /// Leave it at home, in the rooms above the bar.
        public static void Store(Traces.Item it) => Player.Store(it);

        /// Get rid of it in a hurry — off you, wherever you are standing. Not
        /// disposal: disposal is a verb somebody can watch you perform and it
        /// belongs to Phase 4. This is dropping it.
        public static bool Drop(Traces.Item it) => Player.Drop(it);

        /// It is only a real decision while something has to be left behind,
        /// and that is a predicate rather than prose — a UI that says "choose"
        /// when everything fits is lying to the player.
        public static bool IsAChoice => Player.IsAChoice;
        public static bool CanTakeEverything => Player.CanTakeEverything;
        public static IReadOnlyList<Traces.Item> OnMe => Player.OnMe;
        public static IReadOnlyList<Traces.Item> AtHome => Player.AtHome;

        // ---- THE FRISK (spec §7.2) ----------------------------------------

        /// What one search came to.
        public class FriskResult
        {
            /// False when this person had no grounds and it never happened.
            public bool Happened;
            /// What refusing would have cost — always populated, because the
            /// player is entitled to know before deciding.
            public Coat.Refusal IfRefused;
            /// Whether the player refused, and therefore paid that instead.
            public bool Refused;
            /// The worst thing on you, 0..1.
            public double WorstFind;
            /// What it costs socially, scaled by how much the street is already
            /// talking. Found is worse than used.
            public double Cost;
            /// And the case that is not about the object at all.
            public bool FoundSomethingUsedInAKilling;
        }

        /// Somebody searches you — or does not, because a frisk is never at
        /// random. It follows suspicion, a place with a rule, or somebody
        /// deciding to make a point, and which of those it is decides both
        /// whether it can happen and what refusing costs.
        public static FriskResult Frisk(Coat.Frisker who, double suspicion,
                                        bool placeHasARule, bool makingAPoint,
                                        double streetHeat, bool playerRefuses)
        {
            var result = new FriskResult
            {
                Happened = false,
                IfRefused = Coat.IfYouRefuse(who),
                Refused = false,
                WorstFind = 0,
                Cost = 0,
                FoundSomethingUsedInAKilling = false,
            };

            if (!Coat.MayFrisk(who, suspicion, placeHasARule, makingAPoint)) return result;

            LastRefusal = result.IfRefused;
            if (playerRefuses)
            {
                // REFUSING IS AN ANSWER, and it is neither a crime nor free.
                // Refusing a doorman means not going in; refusing a constable
                // is itself a thing people saw you do.
                result.Refused = true;
                FrisksRefused++;
                return result;
            }

            result.Happened = true;
            Frisks++;
            result.WorstFind = Player.WorstFind();
            result.Cost = Player.CostIfFound(streetHeat);
            result.FoundSomethingUsedInAKilling = Player.CarryingSomethingUsed();
            LastFriskFoundAKilling = result.FoundSomethingUsedInAKilling;
            if (result.WorstFind > 0) FrisksThatFoundSomething++;
            if (result.Cost > WorstCostPaid) WorstCostPaid = result.Cost;
            return result;
        }

        /// Money you cannot account for is exactly what a search turns up, and
        /// it costs nothing to carry until somebody looks.
        public static bool CarryingUnexplained(PurseBook purses, string playerId) =>
            purses != null && purses.CarryingUnexplained(playerId);

        /// An arrest catalogues everything you were carrying, and provenance
        /// becomes the interrogation. Being taken is also a public event that
        /// half the street watched, which the mill carries like any other fact.
        public static bool Arrested(Reaction.Lawful outcome, out bool publicly)
        {
            publicly = Reaction.IsPublicEvent(outcome);
            return Reaction.CataloguesYourCoat(outcome);
        }
    }
}
