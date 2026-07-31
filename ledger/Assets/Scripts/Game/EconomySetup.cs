using Ledger.Core;

namespace Ledger.Game
{
    /// The district's suppliers (roadmap M7). Content as data, per the
    /// separability principle: this is the only file that knows who brings
    /// what to Hook Street, and none of it is hardcoded in the simulation.
    ///
    /// They are people first. Mitch has brought the drink to this bar since
    /// before Mickey died and expects to be paid on Thursdays. Tony is the
    /// wholesaler Marla already wants leaned on — her recruitment need has
    /// named him since the roster was written, and now he exists.
    public static class EconomySetup
    {
        public static Economy Build()
        {
            var e = new Economy();

            e.Suppliers.Add(new Supplier
            {
                Id = "drayman",
                Name = "Mitch",
                Goods = "the drink",
                ServesBusinessId = "bar",     // the bar itself — a real id, because
                                              // FactorFor(null) means the district
                                              // and must never match a supplier
                PricePerWeek = 90,
                Standing = 0.25,              // Mickey's arrangement, inherited
            });

            e.Suppliers.Add(new Supplier
            {
                Id = "wholesaler",
                Name = "Tony",
                Goods = "the stock",
                ServesBusinessId = "stall",
                PricePerWeek = 60,
                Standing = -0.1,              // Marla's complaint, from her side
            });

            e.Suppliers.Add(new Supplier
            {
                Id = "miller",
                Name = "Donna's cousin",
                Goods = "the flour",
                ServesBusinessId = "bakery",
                PricePerWeek = 45,
                Standing = 0.1,
            });

            // Calibrated against the shipped rackets: collection £60 + protection
            // £80 + fencing £100 = £240 at full spread, so £180 is "taking most of
            // what this street has" without requiring every racket to be running.
            e.SqueezeFullAt = 180.0;

            return e;
        }
    }
}
