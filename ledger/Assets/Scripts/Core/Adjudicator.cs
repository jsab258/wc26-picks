using System;

namespace Ledger.Core
{
    /// The deterministic half of the novel-action path (design doc §17 gap 1).
    ///
    /// The router may say a player is attempting something the verb list does not
    /// contain. It names a requirement and an effect from closed vocabularies —
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

        public static Adjudication Resolve(Intent intent, AdjudicationInput state)
        {
            if (intent == null || state == null || intent.Kind != IntentKind.Novel)
                return Adjudication.Fail("nothing to resolve");

            int amount = Math.Max(0, intent.CheckAmount);

            switch (intent.Check)
            {
                case Checks.None:
                    break;

                case Checks.Cash:
                {
                    int cost = Math.Min(amount, MaxNovelCost);
                    if (state.Clean < cost)
                        return Adjudication.Fail($"that takes ${cost} clean, and you have ${state.Clean}");
                    return Pass(intent, cost, dirty: false);
                }

                case Checks.DirtyCash:
                {
                    int cost = Math.Min(amount, MaxNovelCost);
                    if (state.Dirty < cost)
                        return Adjudication.Fail($"that takes ${cost} you can't be seen with, and you have ${state.Dirty}");
                    return Pass(intent, cost, dirty: true);
                }

                case Checks.Standing:
                    // Named as a percentage so the router never has to reason
                    // about the simulation's -1..1 scale.
                    if (state.Standing * 100.0 < amount)
                        return Adjudication.Fail("you don't stand well enough with them for that");
                    break;

                case Checks.Hook:
                    if (!state.HoldsHook)
                        return Adjudication.Fail("you'd need something on them, and you have nothing");
                    break;

                case Checks.Crew:
                    if (state.Crew < amount)
                        return Adjudication.Fail(amount == 1
                            ? "that needs somebody who works for you"
                            : $"that needs {amount} people, and you have {state.Crew}");
                    break;

                case Checks.Hour:
                    if (state.Hour < amount)
                        return Adjudication.Fail("it's too early in the day for that");
                    break;

                case Checks.Heat:
                    if (state.Heat * 100.0 > amount)
                        return Adjudication.Fail("too many people are watching you right now");
                    break;

                default:
                    // Unreachable if the router validated, and harmless if not.
                    return Adjudication.Fail("nothing to resolve");
            }

            return Pass(intent, 0, dirty: false);
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
