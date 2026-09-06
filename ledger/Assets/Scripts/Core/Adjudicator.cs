using System;

namespace Ledger.Core
{
    /// The deterministic half of the novel-action path (design doc §17 gap 1).
    ///
    /// The router may say a player is attempting something the verb list does not
    /// contain. It names a requirement and an effect from closed vocabularies,
    /// and then stops. THIS decides whether the attempt lands, using nothing but
    /// numbers the simulation already tracks. The model is not consulted here and
    /// its magnitude is treated as a suggestion inside a hard clamp.
    ///
    /// The point of the whole arrangement: novel actions are SMALL AND REAL
    /// rather than large and fake. A player who says something clever gets a
    /// nudge that actually moved the simulation; a player who says something
    /// clever and expensive gets told, honestly, that they cannot afford it.
    public class AdjudicationInput
    {
        public int Clean;
        public int Dirty;
        public int Crew;
        public int Hour;
        /// Standing with whichever arm the action touches, -1..1.
        public double Standing;
        /// 0..1. Heat checks are inverted: you must be UNDER the named number.
        public double Heat;
        public bool HoldsHook;
    }

    public class Adjudication
    {
        public bool Passed;
        /// Plain-language account of the failure, for narration. Empty on success.
        public string Reason = "";
        public string Effect = Effects.Nothing;
        public double Magnitude;
        /// What the attempt actually cost, already validated as affordable.
        public int CashSpent;
        public bool SpentDirty;

        public static Adjudication Fail(string reason) =>
            new Adjudication { Passed = false, Reason = reason };
    }

    public static class Adjudicator
    {
        /// A novel action may never demand a fortune. The router naming a huge
        /// figure would otherwise turn a throwaway line into a surprise
        /// bankruptcy; capping it means the worst case is a modest, visible
        /// spend. Large sums belong to authored verbs, which state their price.
        public const int MaxNovelCost = 500;

        /// A player who has NOTHING: no clean money, no dirty money, nobody
        /// working for them, no leverage, the day not yet started and the whole
        /// street watching. Every field sits at the worst value its own declared
        /// range allows (Clean, Dirty and Crew are counts and floor at 0; Hour is
        /// a GameTime hour, 0..23; Standing is -1..1 and Heat is 0..1, per
        /// AdjudicationInput above, and Heat is the one that inverts). No number
        /// here is a judgement and none of it is tuning: it is the far end of
        /// each range, and it is a ruler rather than a state anybody plays in.
        static readonly AdjudicationInput Floor = new AdjudicationInput
        {
            Clean = 0, Dirty = 0, Crew = 0, Hour = 0,
            Standing = -1.0, Heat = 1.0, HoldsHook = false,
        };

        /// THE MODEL DOES NOT ADJUDICATE (queue 113; outside audit, 2026-09-06).
        ///
        /// The model proposes the action AND names the requirement that governs
        /// it, so nothing in the vocabulary stops it naming one that cannot say
        /// no. "none" refuses nothing by construction; "cash" for £0, "crew" of
        /// 0, "hour" after 0 and "heat" under 100% are the same hole wearing a
        /// vocabulary word. Checks.Known() says the field is WELL FORMED. It has
        /// never said the requirement bites, and reading it as though it did is
        /// how check:none reached live state for a month.
        ///
        /// So the game asks its own question before it honours the model's: run
        /// the named requirement, with the model's own amount, against the Floor
        /// player. If even they clear it, it is a formality rather than a
        /// requirement, and an effect that writes to the simulation does not get
        /// to travel on it. A model-supplied check may NARROW what happens; it
        /// may never REMOVE the constraint.
        ///
        /// Note what this deliberately is not: clamping the magnitude is no
        /// answer at all, because a small unrefusable change is still the model
        /// deciding, and the authority is the fault rather than the size.
        static bool Binds(string check, int amount) =>
            Evaluate(check, amount, Floor).Refused;

        public static Adjudication Resolve(Intent intent, AdjudicationInput state)
        {
            if (intent == null || state == null || intent.Kind != IntentKind.Novel)
                return Adjudication.Fail("nothing to resolve");

            int amount = Math.Max(0, intent.CheckAmount);

            // An effect that changes nothing needs no requirement, which is what
            // "none" is for and the whole of what it is for. An effect outside
            // the vocabulary is not asked either: Pass() coerces it to Nothing,
            // so it reaches no state to begin with.
            if (Effects.AltersState(intent.Effect) && !Binds(intent.Check, amount))
                return Adjudication.Fail("saying it doesn't make it so");

            var outcome = Evaluate(intent.Check, amount, state);
            if (outcome.Refused) return Adjudication.Fail(outcome.Reason);
            return Pass(intent, outcome.Cost, outcome.Dirty);
        }

        /// One requirement measured against one state. Reason is empty when the
        /// requirement is met, and Cost is what meeting it takes out of the
        /// wallet. Split out of Resolve so that the SAME code answers both
        /// questions asked of a check: does this player meet it, and could
        /// anybody ever fail it. Two readings of one implementation cannot drift
        /// apart the way a second copy of the rules would.
        struct Outcome
        {
            public string Reason;
            public int Cost;
            public bool Dirty;

            public bool Refused => !string.IsNullOrEmpty(Reason);

            public static Outcome Met(int cost = 0, bool dirty = false) =>
                new Outcome { Reason = "", Cost = cost, Dirty = dirty };

            public static Outcome No(string reason) =>
                new Outcome { Reason = reason };
        }

        static Outcome Evaluate(string check, int amount, AdjudicationInput state)
        {
            switch (check)
            {
                case Checks.None:
                    // Met by everybody, including the Floor player, which is why
                    // Binds() will not carry a state-altering effect on it.
                    return Outcome.Met();

                case Checks.Cash:
                {
                    int cost = Math.Min(amount, MaxNovelCost);
                    if (state.Clean < cost)
                        return Outcome.No($"that takes £{cost} clean, and you have £{state.Clean}");
                    return Outcome.Met(cost, dirty: false);
                }

                case Checks.DirtyCash:
                {
                    int cost = Math.Min(amount, MaxNovelCost);
                    if (state.Dirty < cost)
                        return Outcome.No($"that takes £{cost} you can't be seen with, and you have £{state.Dirty}");
                    return Outcome.Met(cost, dirty: true);
                }

                case Checks.Standing:
                    // Named as a percentage so the router never has to reason
                    // about the simulation's -1..1 scale.
                    if (state.Standing * 100.0 < amount)
                        return Outcome.No("you don't stand well enough with them for that");
                    return Outcome.Met();

                case Checks.Hook:
                    if (!state.HoldsHook)
                        return Outcome.No("you'd need something on them, and you have nothing");
                    return Outcome.Met();

                case Checks.Crew:
                    if (state.Crew < amount)
                        return Outcome.No(amount == 1
                            ? "that needs somebody who works for you"
                            : state.Crew == 0
                                ? "that needs more hands than yours, and yours are the only ones you have"
                                : "that needs more hands than you can put on it");
                    return Outcome.Met();

                case Checks.Hour:
                    if (state.Hour < amount)
                        return Outcome.No("it's too early in the day for that");
                    return Outcome.Met();

                case Checks.Heat:
                    if (state.Heat * 100.0 > amount)
                        return Outcome.No("too many people are watching you right now");
                    return Outcome.Met();

                default:
                    // Unreachable if the router validated, and harmless if not.
                    // It refuses at the Floor as well, so an unknown name can
                    // never be mistaken for a requirement that binds.
                    return Outcome.No("nothing to resolve");
            }
        }

        static Adjudication Pass(Intent intent, int cost, bool dirty)
        {
            var effect = Effects.Known(intent.Effect) ? intent.Effect : Effects.Nothing;
            double mag = intent.Magnitude;
            if (double.IsNaN(mag) || double.IsInfinity(mag)) mag = 0;
            mag = Math.Max(0, Math.Min(Effects.MaxMagnitude, mag));

            return new Adjudication
            {
                Passed = true,
                Effect = effect,
                Magnitude = mag,
                CashSpent = cost,
                SpentDirty = dirty,
            };
        }
    }
}
