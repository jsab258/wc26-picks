using System.Collections.Generic;

namespace Ledger.Game
{
    /// Act I — The Inheritance (game-design/act1-draft.md, approved 2026-07-26).
    /// The authored spine laid over the built week. The systems carry the act;
    /// this is the state and the text for the seven small moments of meaning on
    /// top: pressure points that fire on conditions, never on timers.
    public class ActOneState
    {
        // PP1 — the keys: Lena's tour ends at the cellar door she doesn't open,
        // planting the location of her secret in plain sight.
        public bool Pp1Fired;
        public const string Pp1CellarLine =
            "Lena's tour ends at the cellar door. She doesn't open it. \"Storeroom's nothing,\" she says, already walking. \"Mind the step.\"";

        // PP2 — the first ask: the runner names Marek's compliance, so refusing
        // reads as breaking HIS deal, not dodging a quest.
        public bool Pp2Fired;
        public const string Pp2RunnerLine =
            "The runner doesn't ask. \"Marek made his drops twenty years, no reminders. Arrangements outlive men.\" Find the glow before 02:00 — or teach them who you are instead.";

        // PP4 — the book under the step: fires the moment the player learns
        // lena_ledger, however they learned it. Knowledge with no innocent uses.
        public bool Pp4Fired;
        public const string Pp4LedgerPage =
            "Under the third cellar step: Marek's real ledger. The debts. The washes. And one page in his own hand, dated the week of the fire — \"the warehouse is settled. The fire settled what the rent couldn't.\"";

        // PP7 — the posture: null until answered, then winddown|takeover|refused.
        // Dialogue + a Fact every cast brain learns; mechanics are Act II's job.
        public string Posture;

        public static string PostureSummary(string p) =>
            p == "winddown"
                ? "over the true books, the new owner told Lena they mean to wind the family business down"
            : p == "takeover"
                ? "over the true books, the new owner told Lena they mean to take the family business over — properly"
                : "asked straight what they intend for the family business, the new owner refused to answer Lena";

        // Noor's two drawers (cast-noor-draft.md): at loyalty >= 0.7 she keeps
        // player-talk in the person drawer — a self-imposed leash. A caught lie
        // breaks it for good; the topics she was sitting on come loose again.
        public bool NoorDrawersEngaged;
        public bool NoorDrawersBroken;
        public readonly HashSet<string> NoorDrawerTopics = new HashSet<string>();

        /// PP1's supporting texture: Sam's first-day condolences carry the weight
        /// of a debt he knows about and the player doesn't yet.
        public static string DayOneContext(string walkerName, int day) =>
            day == 1 && walkerName == "Sam"
                ? " It is the new owner's first day; you came by early with condolences and more warmth than you can afford — your name is in Marek's book for $120 and you are fairly sure the new owner doesn't know yet."
                : "";

        // PP7's scene, shown over the won week's verdict.
        public const string PostureSceneText =
            "Morning, day seven. Lena lays Marek's second ledger open on the counter between you — the debts, the washes, the arrangements, twenty years of it in a dead man's hand.\n\n" +
            "\"Seven days,\" she says. \"You've seen what it is now. Marek never chose — he let the street choose for him, a week at a time, and it used him up.\"\n\n" +
            "She turns the ledger to face you.\n\n" +
            "\"So which is it going to be?\"";

        // The day-8 teaser (open-city-spec.md, decision 2): the demo's last note
        // is "the city opens", not "story complete".
        public const string TeaserText =
            "Lena closes the ledger and does not put it back under the step.\n\n" +
            "\"Then you should know what this street actually is. Ruta's pawnshop moves more through its back room than we move through this till. Josip's crates walk off the docks every week and somebody else collects for it. Marek's book has pages I never showed you.\"\n\n" +
            "She sets the cellar key on the counter between you.\n\n" +
            "\"The week is over. Nobody survives this street twice. You keep books on it — or it keeps books on you.\"\n\n" +
            "<i>ACT I — THE INHERITANCE — ends here. From day 8, the city opens: two ledgers, no ceiling.</i>";
    }
}
