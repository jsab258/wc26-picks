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
        // Above every cast member's STARTING loyalty (Rocco sits at exactly 0.6):
        // no secret is a day-one freebie; each must be earned through play — a beat
        // honored, a favor done — before anyone opens up.
        public const double ShareLoyaltyFloor = 0.65;

        public static SecretsBook Build()
        {
            var book = new SecretsBook();

            var skim = new Secret
            {
                Id = "rocco_skim", OwnerId = "Rocco", Kind = SecretKind.Criminal,
                Summary = "he has skimmed the door take for twenty years — Mickey knew, and let it ride.",
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
                Summary = "he sells neighbourhood talk to a police contact, cash for names.",
            };
            book.Add(informant); // nobody else knows; only Sam himself can let it slip

            // Note her card openly admits the real ledger EXISTS — her authored arc
            // gates where it is. The stealable secret is therefore the hiding place:
            // earn her trust and she shows you willingly; learn it from Rocco and you
            // could simply take it. (Player decision, 2026-07-25.)
            var ledger = new Secret
            {
                Id = "lena_ledger", OwnerId = "Lena", Kind = SecretKind.Criminal,
                Summary = "where she hides Mickey's real ledger — under the third cellar step, behind the loose brick.",
            };
            ledger.KnownBy.Add("Rocco"); // he carried the strongbox down those stairs once
            book.Add(ledger);

            // Empire v1 leverage (from the generated batch, promoted with Victor):
            // the acquisition routes need secrets worth a shop.
            book.Add(new Secret
            {
                Id = "viktor_skim", OwnerId = "Victor", Kind = SecretKind.Shameful,
                Summary = "he skims a little off every appraisal to cover a gambling debt his wife doesn't know about.",
            }); // nobody else knows; only Victor himself can let it slip

            var scale = new Secret
            {
                Id = "mirela_scale", OwnerId = "Marla", Kind = SecretKind.Shameful,
                Summary = "she shorts the scale for regulars she dislikes, and has for years.",
            };
            scale.KnownBy.Add("Sam"); // Sam has watched her thumb for years
            book.Add(scale);

            // The promoted ring (district build-out): each secret is the door
            // to something — Rita's is the fencing line itself.
            var cab = new Secret
            {
                Id = "ferko_flat", OwnerId = "Ferko", Kind = SecretKind.Shameful,
                Summary = "he sleeps in the cab — the flat went to a card table two winters ago.",
            };
            cab.KnownBy.Add("Joey");
            book.Add(cab);

            book.Add(new Secret
            {
                Id = "ruta_fence", OwnerId = "Rita", Kind = SecretKind.Criminal,
                Summary = "she fences dock pilferage through the pawnshop's back room, crate by crate.",
            }); // nobody else knows — she is that careful

            book.Add(new Secret
            {
                Id = "vesna_letters", OwnerId = "Vesna", Kind = SecretKind.Shameful,
                Summary = "she reads Father Emil's letters before he does, and has for years.",
            });

            var count = new Secret
            {
                Id = "tibor_count", OwnerId = "Tibor", Kind = SecretKind.Shameful,
                Summary = "he waves friends' cargo through without tickets and doctors the count after.",
            };
            count.KnownBy.Add("Rita"); // of course she knows
            book.Add(count);

            return book;
        }
    }
}
