using System.Collections.Generic;

namespace Ledger.Core
{
    /// Act II — The Squeeze (act2-draft.md, APPROVED 2026-07-26). The act opens
    /// when the city is open AND the empire is real, and its pressure points
    /// fire on conditions the empire itself produces. Pure state + text; the
    /// game layer fires it, the arms drive it.
    public class ActTwoState
    {
        public bool Opened;
        public int OpenedDay = -1;
        public bool Pp1Fired, Pp2Fired, Pp3Fired, Pp4Fired, Pp5Fired, Pp6Fired;
        /// The open city's own social calendar: the last day someone asked you
        /// to an evening. The honest life keeps inviting after the week ends.
        public int LastEveningDay = -1;
        public const int EveningEveryNDays = 4;

        // PP2: the machine's injunction freezes the BAR's takings (never the
        // fronts — the paper is against the licence, not the street).
        public int InjunctionUntilDay = -1;
        public bool InjunctionAnswered;
        public const int InjunctionFee = 200;
        public bool BarFrozen(GameTime now) => now.Day <= InjunctionUntilDay && !InjunctionAnswered;

        // PP7: the summit. One per act; the answer becomes a Fact.
        public string TableArmId;       // which organization called it
        public string TableAnswer;      // accept | defy | counter
        public bool TableFired => TableAnswer != null;

        // Hal's brokerage (PP5): one truce per act, reads priced per use.
        public bool TruceSpent;
        public int ReadsBought;
        public const int ReadPrice = 150;
        public const int TrucePrice = 600;
        public const double TruceRelief = 0.4;

        /// The act opens on empire reality, not on a date: two of {a business
        /// owned, a racket established, crew of two}.
        public static bool ShouldOpen(bool openMode, int ownedBusinesses, int establishedRackets, int crew) =>
            openMode && ((ownedBusinesses > 0 ? 1 : 0) + (establishedRackets > 0 ? 1 : 0) + (crew >= 2 ? 1 : 0)) >= 2;

        public const string OpenText =
            "It isn't one street anymore. Somebody in a good coat priced your bar from the pavement this morning, " +
            "and did not come in. Whatever you have built is now large enough to be worth taking.";

        // PP1 — one line per doctrine, in the voice of the arm that noticed.
        public static string FirstNotice(string armId) =>
            armId == "dockside"
                ? "A Dockside man drinks one slow beer at your pub, pays exact, and says only: \"Nice little street. Busy lately.\""
            : armId == "machine"
                ? "A clerk you've never seen photographs your deed plate, notes something, and leaves without buying anything."
                : "A grinning fish appears on the bar's side wall overnight. Kids' stuff. Kids who wanted you to see it.";

        public const string Pp2LetterText =
            "Cream paper, hand-delivered: Vane, Holt & Partners give notice that the bar's licence is 'under review'. " +
            "The till stays shut to the public until it is answered. Pay the fees, have Hal make it disappear, or wait it out.";

        public const string Pp3KidText =
            "The Strip kid does it properly this time: a stall over, a fire barrel tipped, glass across the walk, " +
            "laughter running off toward the Strip. Half the street saw it happen outside YOUR bar.";

        public const string Pp5ShopText =
            "A message reaches you the old way — folded, unsigned, left with somebody who owed somebody. " +
            "A coin-and-stamp shop by the ferry. A person might hear things there, for a percentage.";

        public const string Pp6CaseText =
            "Ellis has stopped asking about the fire. She asks about rounds now — who collects, on what nights, " +
            "for whom. Two cases became one case, and it has your street's name on it.";

        /// PP4's fallback staging, for the player who never sits down to an
        /// evening: the collision comes to the bar instead (act2-draft: the
        /// GUARANTEED collision — loyalty and a crew are the trigger, not
        /// attendance). Authored per audit 2026-07-27; the condition existed
        /// only in the design doc before.
        public const string Pp4DoorstepText =
            "It happens at your own bar, which is worse. One of your people comes through the front door like a " +
            "dropped glass — night business, said plainly, in front of the one person whose good opinion you were " +
            "still keeping separate. The room does not go quiet. It goes attentive.";

        public const string Pp4CollisionText =
            "A knock, at the wrong door, at the worst hour. One of your people is on the step with something that " +
            "cannot wait until morning — and behind you, at the table, the person you were being tonight is listening.";

        /// PP7's offer, in each head's doctrine and voice.
        public static string TableOffer(string armId) =>
            armId == "dockside"
                ? "Sera Kest lets the silence run, then: \"Twelve per cent of what your street makes, and my people stop " +
                  "counting your crew. I keep every deal I make. That is why my deals are expensive.\""
            : armId == "machine"
                ? "Aldous Vane apologises before he begins. \"Your holdings would be so much safer under proper management — " +
                  "ours. A cap on what the fronts declare, and the inspections stop. Violence is a failure of paperwork.\""
                : "Danny Ro laughs before he's finished the sentence. \"One round, together, mine to run. You get the quiet. " +
                  "I get the corner. Old men would call that generous, if they called me anything.\"";

        public static string TableResult(string armId, string answer)
        {
            if (answer == "accept")
                return armId == "dockside" ? "You take her terms. Twelve per cent, and the counting stops. She shakes once, dry and final."
                    : armId == "machine" ? "You sign where he indicates. The fronts declare less, the inspectors evaporate, and something is now on paper with your name on it."
                    : "You give Danny the corner. He is delighted, which is the part that worries you.";
            if (answer == "defy")
                return armId == "dockside" ? "\"No.\" She looks at you a long moment, unoffended, recalculating. \"Then we'll see what the street is worth to you.\""
                    : armId == "machine" ? "You decline, politely. He is politer. The letters will not stop now; they will multiply."
                    : "You tell Danny to keep off your street. He laughs, and the laugh goes cold halfway through, in old Hook Street vowels.";
            return armId == "dockside" ? "You put your own number on the table and it holds. She almost smiles. \"Mickey never counted that fast.\""
                : armId == "machine" ? "You counter with something his firm would rather not see filed. A pause. \"Let us call the matter closed.\""
                : "You match Danny's noise with your own standing, and he folds it into a joke — but he folds.";
        }

        public Dictionary<string, object> Capture() => new Dictionary<string, object>
        {
            { "opened", Opened }, { "openedDay", OpenedDay },
            { "pp1", Pp1Fired }, { "pp2", Pp2Fired }, { "pp3", Pp3Fired },
            { "pp4", Pp4Fired }, { "pp5", Pp5Fired }, { "pp6", Pp6Fired },
            { "lastEvening", LastEveningDay },
            { "injUntil", InjunctionUntilDay }, { "injAnswered", InjunctionAnswered },
            { "tableArm", TableArmId ?? "" }, { "tableAnswer", TableAnswer ?? "" },
            { "truceSpent", TruceSpent }, { "reads", ReadsBought },
        };

        public void Restore(Dictionary<string, object> d)
        {
            if (d == null) return;
            Opened = Flag(d, "opened"); OpenedDay = MiniJson.GetInt(d, "openedDay");
            Pp1Fired = Flag(d, "pp1"); Pp2Fired = Flag(d, "pp2"); Pp3Fired = Flag(d, "pp3");
            Pp4Fired = Flag(d, "pp4"); Pp5Fired = Flag(d, "pp5"); Pp6Fired = Flag(d, "pp6");
            LastEveningDay = d.ContainsKey("lastEvening") ? MiniJson.GetInt(d, "lastEvening") : -1;
            InjunctionUntilDay = MiniJson.GetInt(d, "injUntil");
            InjunctionAnswered = Flag(d, "injAnswered");
            var arm = MiniJson.GetString(d, "tableArm");
            TableArmId = string.IsNullOrEmpty(arm) ? null : arm;
            var ans = MiniJson.GetString(d, "tableAnswer");
            TableAnswer = string.IsNullOrEmpty(ans) ? null : ans;
            TruceSpent = Flag(d, "truceSpent"); ReadsBought = MiniJson.GetInt(d, "reads");
        }

        static bool Flag(Dictionary<string, object> d, string k) =>
            d.TryGetValue(k, out var v) && v is bool b && b;
    }
}
