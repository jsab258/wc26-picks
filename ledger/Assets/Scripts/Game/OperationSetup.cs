using System.Collections.Generic;
using Ledger.Core;

namespace Ledger.Game
{
    /// The jobs worth planning (roadmap M7.5). Content as data, engine-free, so
    /// CoreTests compiles the file the game actually loads.
    ///
    /// Three, and they are not a difficulty ladder. Each one wants a DIFFERENT
    /// plan, which is the only reason to have more than one:
    ///
    ///   THE CUSTOMS SHED   easy to get into, impossible to be unseen at —
    ///                      the hour is the whole decision.
    ///   THE HARBOUR SAFE   hard, overlooked, and it wants hands and tools.
    ///                      Forcing it works; forcing it is heard.
    ///   THE WAREHOUSE ROW  Mickey's old ground, and the reason the case is
    ///                      open. Nobody sees anything out there. Doing it is
    ///                      not the problem; doing it is the problem.
    ///
    /// The third one is the one that matters. It pays worst, it is the safest
    /// job on the board, and going back to the place that burned is the single
    /// loudest thing the player can do about the story they are standing in.
    public static class OperationSetup
    {
        public static List<OperationTarget> Build() => new List<OperationTarget>
        {
            new OperationTarget
            {
                Id = "customs_run",
                Name = "the customs shed",
                PlaceId = "customs_shed",
                Difficulty = 0.30,   // a bad lock and a bored man
                Payout = 180,
                Exposure = 0.85,     // on the water, lit, and never actually empty
            },
            new OperationTarget
            {
                Id = "harbor_safe",
                Name = "the harbourmaster's safe",
                PlaceId = "harbor_office",
                Difficulty = 0.68,   // wants hands, tools, or a great deal of nerve
                Payout = 420,
                Exposure = 0.35,     // an office at night is an office at night
            },
            new OperationTarget
            {
                Id = "warehouse_row",
                Name = "what is left in the warehouse row",
                PlaceId = "warehouse_row",
                Difficulty = 0.40,
                Payout = 150,        // the worst money on the board, deliberately
                Exposure = 0.15,     // nobody goes out there, which is why it burned
            },
        };
    }
}
