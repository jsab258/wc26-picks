namespace Ledger.Core
{
    /// WHAT THE CROWD IS WEARING, and it is not a random hue.
    ///
    /// FOUND IN A SCREENSHOT. The first noon still showed a street of people in
    /// mint green and pale lilac against grey stone and wet asphalt. Both crowd
    /// spawners were picking clothing as `HSVToRGB(stableFraction, s, v)` with
    /// the hue running the WHOLE WHEEL — so a third of the population wore
    /// colours no British port town in the 1930s ever sold, and the art
    /// direction's first rule ("one palette across seven districts beats
    /// scattered high-resolution assets") was being broken by the most visible
    /// objects in the frame.
    ///
    /// They also disagreed with each other: `PopulationHost` used saturation
    /// 0.22 at value 0.45 and `Tier2Batch` used 0.35 at 0.55, so which crowd a
    /// walker belonged to changed how loud their coat was. One source now, and
    /// this is it.
    ///
    /// THE BANDS ARE AUTHORED, not sampled. Working clothes of the period and
    /// the place: charcoal and grey, brown and tan, olive and khaki, navy and
    /// slate, and ox-blood — with grey and brown common and ox-blood rare,
    /// because that is how a street looks. Everything else the wheel offers is
    /// simply not in the wardrobe.
    ///
    /// IN CORE BECAUSE IT IS ARITHMETIC AND A RULE. The visible half needs a
    /// screenshot and a twenty-eight-minute round trip; that every output lands
    /// inside a named band and no crowd member is ever brighter than the cast
    /// does not, and CoreTests holds both.
    public static class Wardrobe
    {
        /// One entry of the wardrobe. Hue in turns (0..1), because that is what
        /// `Color.HSVToRGB` takes and converting twice is how a hue ends up
        /// eleven degrees off.
        public struct Band
        {
            public string Name;
            public double HueFrom, HueTo;
            public double SatFrom, SatTo;
            public double ValFrom, ValTo;
            /// Relative frequency. A street is mostly grey and brown.
            public int Weight;
        }

        /// NOBODY IN THE CROWD OUTSHINES A NAMED CHARACTER. The cast are
        /// authored at value 0.65-0.75 (Rocco 0.75, Ada 0.75, Sam 0.65); the
        /// wardrobe tops out here, well beneath them, so the eye still goes to
        /// the people who matter. `Tier2Batch` claimed this in a comment —
        /// "never brighter than the cast" — while using 0.55 with no mechanism
        /// to enforce it. Now it is a number a test can hold.
        public const double MaxValue = 0.46;

        /// The wardrobe itself. Ordered, and the order is part of the identity:
        /// changing it re-dresses the whole city.
        public static readonly Band[] Bands =
        {
            // Charcoal through to slate grey. Hue barely matters at this
            // saturation, which is the point of a grey.
            new Band { Name = "charcoal", HueFrom = 0.55, HueTo = 0.62,
                       SatFrom = 0.02, SatTo = 0.09, ValFrom = 0.26, ValTo = 0.42, Weight = 5 },
            // Brown, tan, the colour of a working coat.
            new Band { Name = "brown", HueFrom = 0.055, HueTo = 0.10,
                       SatFrom = 0.24, SatTo = 0.44, ValFrom = 0.28, ValTo = 0.44, Weight = 5 },
            // Olive and khaki — surplus, and everywhere in this period.
            new Band { Name = "olive", HueFrom = 0.13, HueTo = 0.18,
                       SatFrom = 0.18, SatTo = 0.36, ValFrom = 0.26, ValTo = 0.40, Weight = 3 },
            // Navy and slate blue. The one cool note, and it reads well against
            // sodium light at night.
            new Band { Name = "navy", HueFrom = 0.58, HueTo = 0.645,
                       SatFrom = 0.20, SatTo = 0.42, ValFrom = 0.24, ValTo = 0.40, Weight = 4 },
            // Ox-blood. Rare on purpose — one in a crowd, never a third of it.
            new Band { Name = "oxblood", HueFrom = 0.965, HueTo = 0.995,
                       SatFrom = 0.28, SatTo = 0.46, ValFrom = 0.24, ValTo = 0.38, Weight = 2 },
        };

        static int TotalWeight()
        {
            int t = 0;
            foreach (var b in Bands) t += b.Weight;
            return t;
        }

        /// Dress somebody, deterministically, from a stable fraction in 0..1.
        ///
        /// The SAME fraction always produces the same clothes — a walker who
        /// changed coat when the crowd re-banded would be a walker you cannot
        /// learn to recognise, and recognition is the whole game.
        ///
        /// Returns HSV. The Game layer converts; Core does not know what a
        /// `Color` is.
        public static void Dress(double fraction, out double hue, out double sat, out double val)
        {
            // Fold anything into 0..1 rather than trusting the caller. A hash
            // that returns 1.0 exactly would otherwise index off the end.
            double f = fraction - System.Math.Floor(fraction);
            if (double.IsNaN(f) || f < 0) f = 0;

            // Pick the band by weight.
            double target = f * TotalWeight();
            var band = Bands[Bands.Length - 1];
            double acc = 0;
            foreach (var b in Bands)
            {
                acc += b.Weight;
                if (target < acc) { band = b; break; }
            }

            // AND A SECOND, DECORRELATED FRACTION FOR THE POSITION INSIDE THE
            // BAND. Reusing `f` would make hue, saturation and value all move
            // together, so every brown coat in the city would be the lightest
            // brown or the darkest one and nothing between — a banding artifact
            // that looks like a palette and is actually one number wearing
            // three hats.
            double g = f * 977.0;
            g -= System.Math.Floor(g);
            double h2 = f * 5081.0;
            h2 -= System.Math.Floor(h2);

            hue = band.HueFrom + (band.HueTo - band.HueFrom) * g;
            sat = band.SatFrom + (band.SatTo - band.SatFrom) * h2;
            val = band.ValFrom + (band.ValTo - band.ValFrom) * (1.0 - g);
            if (val > MaxValue) val = MaxValue;
        }

        /// Which band a fraction dresses from. For the tests and the sim
        /// verdict — a distribution that has quietly collapsed onto one band is
        /// a palette failure that every individual colour would pass.
        public static string BandOf(double fraction)
        {
            double f = fraction - System.Math.Floor(fraction);
            if (double.IsNaN(f) || f < 0) f = 0;
            double target = f * TotalWeight();
            double acc = 0;
            foreach (var b in Bands)
            {
                acc += b.Weight;
                if (target < acc) return b.Name;
            }
            return Bands[Bands.Length - 1].Name;
        }
    }
}
