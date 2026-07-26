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

            e.Rackets.Add(new Racket
            {
                Id = "collection", Name = "collection round", IncomePerDay = 60, BaseRisk = 0.35,
            });
            e.Rackets.Add(new Racket
            {
                Id = "protection", Name = "protection round", IncomePerDay = 80, BaseRisk = 0.5,
            });

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
                default:
                    cost = 0; line = null; return false;
            }
        }
    }
}
