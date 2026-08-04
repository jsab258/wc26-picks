using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// THE CALLER FOR `Reliability`, so missing drops costs something.
    ///
    /// `Campaign.MissedSinceLastDelivery` has had exactly one consumer since it
    /// was written — a line on the ledger screen — and the roadmap's competence
    /// row says what that means: *"the first two bricks are visible (missed
    /// nights, skimmed envelopes) but neither yet closes anything."* A number
    /// the player can read and the world cannot is a number, not a mechanic.
    ///
    /// WHO HEARS IT, AND IT IS NOT EVERYBODY. The paper reaches the whole town
    /// at once because that is what a newspaper is; this is the opposite kind
    /// of fact. Somebody who was expecting a parcel notices you did not bring
    /// it, and it moves from there person to person like everything else in
    /// this game. So it is filed into the DAY CIRCLE only — the people whose
    /// business hours overlap a delivery round — and left to spread on its own.
    ///
    /// ONCE PER STANDING, NOT ONCE PER NIGHT. Filing the same fact every
    /// evening would make a fortnight of absence into fourteen separate
    /// stories, and the mill would read that as fourteen people independently
    /// confirming it. `Holds` is the same guard `PressHost` and the debt
    /// collector already use for exactly this.
    public static class ReliabilityHost
    {
        public static int Filed { get; private set; }
        public static int Heard { get; private set; }
        public static string LastRead { get; private set; } = "nobody has noticed";

        public static void Reset()
        {
            Filed = Heard = 0;
            LastRead = "nobody has noticed";
            _lastStanding = Reliability.Standing.Fine;
        }

        public static bool Nightly(GameController game)
        {
            if (game == null || game.Campaign == null) return false;
            if (game.Gossip == null || game.Gossip.Mill == null) return false;

            int missed = game.Campaign.MissedSinceLastDelivery(game.Now.Day);
            var standing = Reliability.Of(missed);
            LastRead = $"{standing} after {missed}";
            if (standing == Reliability.Standing.Fine)
            {
                // A DELIVERY CLEARS IT, and this is where that becomes true
                // rather than merely being true of the counter. `_lastStanding`
                // resets so the next slide files again — otherwise one bad
                // fortnight would inoculate a player for the rest of the
                // campaign, which is the opposite of consequence persistence.
                _lastStanding = Reliability.Standing.Fine;
                return false;
            }
            if (standing == _lastStanding) return false;
            _lastStanding = standing;

            var content = Reliability.ContentFor(standing);
            string summary = Reliability.SummaryFor(standing, missed);
            double confidence = Reliability.Confidence(missed);

            foreach (var g in game.Gossip.Mill.Agents)
            {
                if (g == null || g.Circle == "night") continue;
                if (g.Holds(content.Subject + "." + content.Predicate, content.Value)) continue;
                game.Gossip.Mill.Witness(g.Id, content, summary,
                                         sensitive: false, now: game.Now,
                                         confidence: confidence);
                Heard++;
            }
            Filed++;
            Debug.Log($"ReliabilityHost: {standing} after {missed} missed — "
                      + $"{Heard} in the day circle now hold it (confidence {confidence:0.00})");
            return true;
        }

        static Reliability.Standing _lastStanding = Reliability.Standing.Fine;
    }
}
