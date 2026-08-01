namespace Ledger.Core
{
    /// WHAT THE CROWD IS WEARING, and it is not a random hue.
    ///
    /// FOUND IN A SCREENSHOT. The first noon still showed a street of people in
    /// mint green and pale lilac against grey stone and wet asphalt. Both crowd
    /// spawners were picking clothing as `HSVToRGB(stableFraction, s, v)` with
    /// the hue running the WHOLE WHEEL — so a third of the population wore
    /// colours no British port town ever sold, and the art
    /// direction's first rule ("one palette across seven districts beats
    /// scattered high-resolution assets") was being broken by the most visible
    /// objects in the frame.
    ///
    /// They also disagreed with each other: `PopulationHost` used saturation
    /// 0.22 at value 0.45 and `Tier2Batch` used 0.35 at 0.55, so which crowd a
    /// walker belonged to changed how loud their coat was. One source now, and
    /// this is it.
    ///
    /// AND THEN THE BANDS THEMSELVES WERE WRITTEN FOR THE WRONG DECADE.
    ///
    /// This file justified its palette with *"colours no British port town in
    /// the **1930s** ever sold"* and authored to match: charcoal, brown and
    /// tan, olive and khaki, navy and slate, ox-blood. That is interwar
    /// workwear. **The game is late-analog — the eighties and nineties**
    /// (`agency-model.md:163`: landlines, payphones, answering machines,
    /// messages left with people). I have called it 1930s twice in writing;
    /// the first correction is at `decisions-answered.md:802` and this is the
    /// code that correction never reached.
    ///
    /// The tell was that there was NO BLACK IN THE WARDROBE AT ALL, in a
    /// decade of leather jackets and black jeans, while olive-khaki surplus
    /// carried weight 3.
    ///
    /// THE BANDS ARE AUTHORED, not sampled. What a British port town wore at
    /// the end of the eighties: black and denim leading, grey and navy behind
    /// them, stone and burgundy and bottle green for anything smart, and one
    /// rare loud thing. Everything else the wheel offers is simply not in the
    /// wardrobe.
    ///
    /// WHAT SURVIVED THE REWRITE, because it was never about the decade:
    /// `MaxValue` and the mixing. The value ceiling comes from the CAST being
    /// authored at 0.65-0.75, not from any period; the `Mix` fold exists
    /// because FNV-1a hashes bunch in the middle of the range. Both are
    /// unchanged, and the CoreTests that hold them are the reason a palette
    /// rewrite is a safe thing to do at all.
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
            // BLACK, and it leads because it is what the decade actually wore:
            // leather, bomber jackets, black jeans, black coats. The old
            // wardrobe had no black at all, which is the single clearest tell
            // that it was written for the wrong period.
            new Band { Name = "black", HueFrom = 0.60, HueTo = 0.68,
                       SatFrom = 0.02, SatTo = 0.10, ValFrom = 0.09, ValTo = 0.20, Weight = 6 },
            // DENIM. Indigo through stonewash, and the most-worn cloth of the
            // era by a wide margin. Deliberately a distinct band from navy:
            // stonewash is lighter and less saturated than a donkey jacket, and
            // a street where those are the same colour looks synthesised.
            new Band { Name = "denim", HueFrom = 0.58, HueTo = 0.63,
                       SatFrom = 0.26, SatTo = 0.50, ValFrom = 0.24, ValTo = 0.44, Weight = 6 },
            // Grey — marl sweatshirts, trackies, coats. Hue barely matters at
            // this saturation, which is the point of a grey.
            new Band { Name = "grey", HueFrom = 0.55, HueTo = 0.62,
                       SatFrom = 0.02, SatTo = 0.09, ValFrom = 0.26, ValTo = 0.44, Weight = 5 },
            // Navy — parkas, donkey jackets, anoraks. Survives the decade change
            // unaltered, and reads well against sodium light at night.
            new Band { Name = "navy", HueFrom = 0.60, HueTo = 0.66,
                       SatFrom = 0.30, SatTo = 0.52, ValFrom = 0.16, ValTo = 0.30, Weight = 4 },
            // Stone and beige — macs, chinos, the lining of everything.
            new Band { Name = "stone", HueFrom = 0.08, HueTo = 0.12,
                       SatFrom = 0.12, SatTo = 0.26, ValFrom = 0.30, ValTo = 0.46, Weight = 4 },
            // Burgundy and bottle green, the two "smart" colours of the period —
            // cords, shell-suit panels, a good coat.
            new Band { Name = "burgundy", HueFrom = 0.955, HueTo = 0.99,
                       SatFrom = 0.34, SatTo = 0.55, ValFrom = 0.18, ValTo = 0.32, Weight = 3 },
            //
            // BOTTLE GREEN IS CAPPED AT 0.28 AND THAT IS NOT A STYLE CHOICE.
            // CoreTests forbids `h in (0.20, 0.55) && v > 0.30` — the mint/cyan
            // gap, written because the first crowd came out in pale mint and
            // lilac. Bottle green sits inside that hue range and is only
            // admissible because it is DARK. A bottle green that drifted
            // brighter would be mint, which is the exact fault that test exists
            // to catch, so the ceiling is the test's and not mine.
            new Band { Name = "bottle", HueFrom = 0.36, HueTo = 0.43,
                       SatFrom = 0.28, SatTo = 0.50, ValFrom = 0.14, ValTo = 0.28, Weight = 2 },
            // AND THE ONE LOUD THING, which the period demands and the old
            // palette had no room for: a shell suit, a football top, a ski
            // jacket in colours nobody would call tasteful.
            //
            // LOUD BY SATURATION, NOT BY BRIGHTNESS — and that is what makes it
            // possible at all. `MaxValue` 0.46 exists so the crowd never
            // outshines a cast authored at 0.65-0.75, and I nearly treated that
            // as forbidding a bright accent. It does not: it caps VALUE. A
            // saturated teal at v=0.40 is unmistakably loud against black and
            // grey while staying well under the cast, because what reads as
            // "loud" on a noir street is chroma against a desaturated field,
            // not luminance. The period signature and the cast rule are not in
            // conflict once the right axis is named.
            //
            // MAGENTA AND VIOLET, NOT THE TEAL I FIRST WROTE. My first pass put
            // this at hue 0.47-0.56 — teal — which lands squarely inside the
            // mint/cyan gap CoreTests forbids at any value above 0.30. That gap
            // exists because the first crowd this game ever rendered was in
            // mint green and pale lilac, and I had reintroduced the colour the
            // fix removed while believing I was adding period character.
            //
            // The test caught it before the commit. Magenta through violet is
            // just as much the decade — shell suits, ski jackets, anything
            // sold as sportswear — and is nowhere near the region that has
            // already burned this project once.
            //
            // Weight 1 of 31, so it is a person you notice rather than a
            // texture the crowd has.
            new Band { Name = "shellsuit", HueFrom = 0.82, HueTo = 0.90,
                       SatFrom = 0.62, SatTo = 0.85, ValFrom = 0.30, ValTo = 0.44, Weight = 1 },
        };

        static int TotalWeight()
        {
            int t = 0;
            foreach (var b in Bands) t += b.Weight;
            return t;
        }

        /// Spread a stable fraction before it chooses a band.
        ///
        /// THE WEIGHTS WERE RIGHT AND THE STREET WAS STILL WRONG. The first run
        /// to report the tally came back
        ///
        ///     olive:483 brown:441 charcoal:325 navy:261 oxblood:164
        ///
        /// against designed shares of 15.8 / 26.3 / 26.3 / 21.1 / 10.5 percent.
        /// Olive came out at 1.83x its share and was the COMMONEST band while
        /// weighted third; charcoal and navy came in at 0.74x.
        ///
        /// The weighting arithmetic is fine. The input is not uniform:
        /// `Population.StableFraction` is FNV-1a over a name divided by
        /// uint.MaxValue, and over the city's actual roster those hashes bunch
        /// in the middle of the range — exactly where the olive slice sits. A
        /// weighted pick is only as good as the uniformity of what it picks on,
        /// and nothing had ever looked.
        ///
        /// MY TEST PASSED THROUGHOUT, because it fed `i / n` — a perfectly
        /// uniform ramp, which cannot fail a weighting no matter how the real
        /// input behaves. That is the corpus diagnostic reading sixty
        /// consecutive rows of a speaker-ordered dataset and reporting on "the
        /// corpus": the right check against the wrong sample.
        ///
        /// Two multiply-and-fold rounds with coprime primes. Cheap,
        /// deterministic — the same name still always gets the same coat — and
        /// it breaks up clustering without needing to know its shape.
        static double Mix(double f)
        {
            double a = f * 7919.0;
            a -= System.Math.Floor(a);
            double b = (a + f) * 104729.0;
            return b - System.Math.Floor(b);
        }

        /// Which band, from a fraction. ONE implementation, because `Dress` and
        /// `BandOf` each had their own copy of this loop — and two copies of a
        /// rule is how the fog ended up with two owners and the Core-tested one
        /// always losing.
        static Band Pick(double fraction)
        {
            double f = fraction - System.Math.Floor(fraction);
            if (double.IsNaN(f) || f < 0) f = 0;
            double target = Mix(f) * TotalWeight();
            double acc = 0;
            foreach (var b in Bands)
            {
                acc += b.Weight;
                if (target < acc) return b;
            }
            return Bands[Bands.Length - 1];
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

            var band = Pick(f);

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
        public static string BandOf(double fraction) => Pick(fraction).Name;
    }
}
