using Ledger.Core;

namespace Ledger.Game
{
    /// Empire v1's authored roster (open-city-spec §2, broader scope by player
    /// decision). Two businesses with live owners now — the batch walkers add
    /// more at the district build-out — plus the first two racket types, and
    /// the needs table that makes the recruit-by-need route concrete. All data;
    /// swappable without touching the systems.
    public static class EmpireSetup
    {
        public static EmpireBook Build()
        {
            var e = new EmpireBook();

            e.Businesses.Add(new Business
            {
                Id = "pawnshop", Name = "pawnshop", OwnerId = "Viktor", PlaceId = "pawnshop",
                AskPrice = 900, DebtPrice = 250, SecretId = "viktor_skim",
                CleanIncomePerDay = 60, LaunderPerDay = 80,
            });
            e.Businesses.Add(new Business
            {
                Id = "stall", Name = "market stall", OwnerId = "Mirela", PlaceId = "market_corner",
                AskPrice = 500, DebtPrice = 0, SecretId = "mirela_scale",
                CleanIncomePerDay = 40, LaunderPerDay = 30,
            });

            e.Businesses.Add(new Business
            {
                Id = "teahouse", Name = "teahouse", OwnerId = "Magda", PlaceId = "teahouse",
                AskPrice = 600, DebtPrice = 0, SecretId = "magda_batch",
                CleanIncomePerDay = 45, LaunderPerDay = 40,
            });
            e.Businesses.Add(new Business
            {
                Id = "bakery", Name = "corner bakery", OwnerId = "Danica", PlaceId = "bakery",
                AskPrice = 550, DebtPrice = 150, SecretId = "danica_batch",
                CleanIncomePerDay = 45, LaunderPerDay = 25,
            });

            e.Rackets.Add(new Racket
            {
                Id = "collection", Name = "collection round", IncomePerDay = 60, BaseRisk = 0.35,
            });
            e.Rackets.Add(new Racket
            {
                Id = "protection", Name = "protection round", IncomePerDay = 80, BaseRisk = 0.5,
            });
            // Ruta's line: the best pay on the street, and it needs the shop —
            // no fencing without a front to move it through.
            e.Rackets.Add(new Racket
            {
                Id = "fencing", Name = "fencing line", IncomePerDay = 100, BaseRisk = 0.4,
                RequiresBusinessId = "pawnshop",
            });

            // The organizations are made of people who already walk this street
            // (§6.5). Recruiting any of them is poaching, with consequences —
            // and every one of them has a card, a need, and a secret already.
            e.ArmOf("dockside").Members.AddRange(new[] { "Josip", "Ferko" });
            e.ArmOf("machine").Members.Add("Tibor");   // the stamp in the customs shed
            e.ArmOf("newcrew").Members.Add("Ruta");    // the kid taxes her; Danny counts her as his

            return e;
        }

        /// The need route's table: what supplying each person actually costs,
        /// and the line the street remembers it by. Core cast (Lena, Ada,
        /// Rocco, Noor) are deliberately absent — they are not recruitable.
        public static bool TryNeed(string id, out int cost, out string line)
        {
            switch (id)
            {
                case "Sam":
                    cost = 120; line = "Sam's need has always been simple: cash, counted twice."; return true;
                case "Josip":
                    cost = 100; line = "A letter on good paper, a name Downtown: his daughter gets her interview."; return true;
                case "Mirela":
                    cost = 150; line = "You send someone to have a word with her supplier. The crates arrive full weight from now on."; return true;
                case "Viktor":
                    cost = 200; line = "You quietly clear a slice of Viktor's gambling marker."; return true;
                case "Ferko":
                    cost = 80; line = "You hire Ferko's cab for a week, paid up front — the fare he'll be retelling for a year."; return true;
                case "Ruta":
                    cost = 150; line = "Someone has a word with the Strip kid who's been taxing Ruta's rounds. He finds other rounds."; return true;
                case "Vesna":
                    cost = 60; line = "Vesna's nephew gets steady shifts at the bar, and nobody asks him anything."; return true;
                case "Tibor":
                    cost = 150; line = "The audit week finds Tibor's counts in perfect order. Somehow."; return true;
                default:
                    cost = 0; line = null; return false;
            }
        }
    }
}
