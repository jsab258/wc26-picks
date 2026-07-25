using Ledger.Core;

namespace Ledger.Game
{
    /// The cast's authored secrets (design-doc §6.3) — one per character, each a
    /// mirror of who they are: the loyal skimmer, the conscience with a past, the
    /// friendly informant, the bookkeeper with the real books. Learning paths run
    /// through loyalty: an NPC confides their OWN secret only at deep trust
    /// (>= 0.75), and shares someone else's at >= 0.6.
    public static class SecretsSetup
    {
        public const double ConfessLoyaltyFloor = 0.75;
        public const double ShareLoyaltyFloor = 0.6;

        public static SecretsBook Build()
        {
            var book = new SecretsBook();

            var skim = new Secret
            {
                Id = "rocco_skim", OwnerId = "Rocco", Kind = SecretKind.Criminal,
                Summary = "he has skimmed the door take for twenty years — Marek knew, and let it ride.",
            };
            skim.KnownBy.Add("Lena"); // the bookkeeper always knew where the shortfall went
            book.Add(skim);

            var dismissal = new Secret
            {
                Id = "ada_dismissal", OwnerId = "Ada", Kind = SecretKind.Shameful,
                Summary = "her teaching career did not end with retirement — it ended in a quiet dismissal she has never explained.",
            };
            dismissal.KnownBy.Add("Sam"); // Sam hears everything, even old things
            book.Add(dismissal);

            var informant = new Secret
            {
                Id = "sam_informant", OwnerId = "Sam", Kind = SecretKind.Criminal,
                Summary = "he sells neighborhood talk to a police contact, cash for names.",
            };
            book.Add(informant); // nobody else knows; only Sam himself can let it slip

            var ledger = new Secret
            {
                Id = "lena_ledger", OwnerId = "Lena", Kind = SecretKind.Criminal,
                Summary = "Marek kept two sets of books, and Lena still has the real one hidden.",
            };
            ledger.KnownBy.Add("Rocco"); // twenty years at the door; he carried the box once
            book.Add(ledger);

            return book;
        }
    }
}
