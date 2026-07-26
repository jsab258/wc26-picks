using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Who on this street has what, and who they could go to (roadmap M13,
    /// `counterparty-purses-spec.md`).
    ///
    /// Only the named cast is authored. Everybody else — including all three
    /// thousand generated residents — gets a purse derived on demand from a
    /// stable hash of their id, so the same person always has the same means
    /// and nobody had to write three thousand numbers.
    ///
    /// The authored ones exist because their means are CHARACTER. Sam owes $120
    /// and turns over about sixty a week: that debt was never going to be one
    /// visit, and the fact that it isn't should come from who he is rather than
    /// from a difficulty curve. Rocco is comfortable and owes little, so he can
    /// simply pay — and does, which makes Sam's inability legible by contrast.
    ///
    /// Patrons are the interesting field. Somebody with a patron can be squeezed
    /// harder than they can afford, because they will go and get it; the money
    /// moves rather than appearing, and the favour they now owe is world state
    /// the Director can read. Somebody with NO patron cannot, and nobody to go
    /// to is a harder life than it sounds.
    public partial class GameController
    {
        void BuildPurses()
        {
            // Sam: a runner's wages, no cushion, and an uncle who has never once
            // said no. Pressing him works, and it costs him his uncle.
            Purses.Add(new Purse
            {
                OwnerId = "Sam", Name = "Sam",
                Weekly = 60, Ceiling = 95, Cash = 45,
                PatronId = "Danica",
            });

            // Rocco: the door has been good to him and he owes almost nothing.
            // He pays in full, first time, which is what makes Sam legible.
            Purses.Add(new Purse
            {
                OwnerId = "Rocco", Name = "Rocco",
                Weekly = 140, Ceiling = 260, Cash = 180,
                PatronId = null,
            });

            // Danica: the one with money on this street, and therefore the one
            // everybody's debts eventually route through.
            Purses.Add(new Purse
            {
                OwnerId = "Danica", Name = "Danica",
                Weekly = 220, Ceiling = 520, Cash = 380,
                PatronId = null,
            });

            // Ruta's pawnshop: a till, and a till is never as full as a shop
            // looks. She can go to Halvard, which is exactly the arrangement
            // that makes a pawnbroker somebody else's instrument.
            Purses.Add(new Purse
            {
                OwnerId = "Ruta", Name = "Ruta",
                Weekly = 190, Ceiling = 300, Cash = 120,
                PatronId = "Halvard",
            });

            Purses.Add(new Purse
            {
                OwnerId = "Halvard", Name = "Halvard",
                Weekly = 400, Ceiling = 900, Cash = 640,
                PatronId = null,
            });

            // Viktor: everything is in the shop and none of it is in the drawer.
            Purses.Add(new Purse
            {
                OwnerId = "Viktor", Name = "Viktor",
                Weekly = 110, Ceiling = 160, Cash = 55,
                PatronId = "Ruta",
            });

            // Lena and Ada work for wages and keep almost nothing to hand. They
            // are not people you collect from; they are here so the district's
            // liquidity is honest about what a wage looks like.
            Purses.Add(new Purse { OwnerId = "Lena", Name = "Lena", Weekly = 70, Ceiling = 90, Cash = 40 });
            Purses.Add(new Purse { OwnerId = "Ada", Name = "Ada", Weekly = 65, Ceiling = 85, Cash = 35 });
        }

        /// Developer readout (F1). Never shown to the player: what a purse holds
        /// is something you learn by asking somebody for money.
        public string PurseStatusLine()
        {
            var sb = new System.Text.StringBuilder();
            sb.Append($"-- purses --\nstreet liquidity: {Purses.Liquidity():0.00}\n");
            int shown = 0;
            foreach (var p in Purses.All)
            {
                if (shown++ >= 6) break;
                sb.Append($"  {p.Name}: ${p.Cash}/{p.Ceiling}");
                if (p.PatronId != null) sb.Append($" (can go to {p.PatronId})");
                if (p.TimesEmptied > 0) sb.Append($" — emptied {p.TimesEmptied}x");
                sb.Append('\n');
            }
            int favours = 0;
            foreach (var f in Purses.Favours) if (!f.Settled) favours++;
            sb.Append($"  favours owed on this street: {favours}");
            return sb.ToString();
        }
    }
}
