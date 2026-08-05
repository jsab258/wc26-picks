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
        ///
        /// CHECKED, 5 August, and the table is innocent — but read the second
        /// half before concluding anything from that. I read
        /// `review_day1_noon`, saw two foreground bodies in bright saturated
        /// trousers, and filed it as off-brief for a noir game. Printed rather
        /// than argued: seven of the eight bands top out between 0.09 and 0.55
        /// saturation, and the only hot one is `shellsuit` at 0.62-0.85 with a
        /// WEIGHT OF 1 IN 31 — three per cent of the city, deliberately, which
        /// is what a shellsuit was.
        ///
        /// AND THE HUE SAYS THE YELLOW IS NOT FROM THIS TABLE AT ALL, WHICH IS
        /// NOT THE SAME AS SAYING IT IS NOT THERE — and the first version of
        /// this note got that wrong, in writing, an hour before the next frame
        /// contradicted it.
        ///
        /// `shellsuit` sits at hue 0.82-0.90, which is magenta, and no band
        /// covers 0.12-0.36 above 0.26 saturation. I concluded from that that
        /// my eyes were the unreliable instrument and filed it as the sixth
        /// thing condemned off a still and cleared by a number.
        ///
        /// It is the opposite. The trousers ARE bright yellow in every frame,
        /// and the reason no band explains them is that **these bodies are not
        /// wearing the wardrobe**. `roadmap.md` says it plainly: texture
        /// extraction switched the paint path off the morning it landed — the
        /// models arrive textured, `bodySkinnedEver=0` because nothing is
        /// painted, and the wash maps over a kept Mixamo albedo instead. The
        /// yellow is the MODEL's own texture. `crowdSatRange=0.06..0.73` is
        /// measuring that albedo, not this table.
        ///
        /// THE LESSON IS ABOUT WHERE I LOOKED, not about the eyes. Checking the
        /// palette was right; concluding from a clean palette that the RENDER
        /// was clean assumed the palette reaches the render, and for these
        /// twelve bodies it does not. A number that exonerates one system says
        /// nothing about a second system standing in front of it.
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

        /// HOW MUCH SATURATION SURVIVES INTO A WASH. Half, unchanged, because
        /// it was never the broken half: a full-saturation multiply over a
        /// textured garment reads as coloured plastic, a look this project
        /// shipped once and had to undo.
        public const double WashSat = 0.5;

        /// HOW DARK THE DARKEST COAT MAY MAKE A TEXTURE. Measured, not picked.
        /// See `Wash` below for the series it came from.
        public const double WashFloor = 0.45;

        /// A WARDROBE ENTRY AS A MULTIPLIER OVER SOMEBODY ELSE'S TEXTURE.
        ///
        /// The models arrived with their own textures this morning, so nothing
        /// is painted any more — `bodySkinned=0 bodyDressed=0` — and this is
        /// now the ONLY route the wardrobe has to the eye. Which makes it worth
        /// having a rule with a test on it rather than three lines in a Game
        /// file nothing here can compile.
        ///
        /// WHAT WAS WRONG WITH THE OLD ONE, AND IT IS NOT A TUNING MISS. It
        /// took the band's hue and half its saturation at value **1.0** — value
        /// discarded entirely, with a comment claiming the multiply "shifts its
        /// colour clearly and darkens it barely". Half of that is true. The
        /// other half is why the noon still shows two women in the same bright
        /// yellow trousers.
        ///
        /// Black is v 0.09-0.20 and grey is v 0.26-0.44 at the SAME hue band
        /// and the same near-zero saturation. The one axis that tells those two
        /// apart is VALUE, and value was the axis being thrown away — so 36% of
        /// the city, by weight, washed to the same colour, and that colour was
        /// white. Replicating this over the real 40x30 name roster:
        ///
        ///     distance of the wash from WHITE, 1200 people
        ///       min 0.7  p25 2.4  median 9.1  p75 14.4  max 25.7
        ///       under 5%: 473 of 1200 (39%)
        ///     within black  median 0.9  max 3.1
        ///     within grey   median 0.8  max 2.3
        ///
        /// A multiply by white is the identity. Thirty-nine percent of the
        /// population was wearing no wardrobe at all, and the counter that was
        /// supposed to prove the wash ran — `bodyTinted=5334` — is true and
        /// says nothing about whether any of it arrived.
        ///
        /// WHERE THE FLOOR COMES FROM. Carrying value in as
        /// `floor + (1-floor) * val/MaxValue` and sweeping the floor:
        ///
        ///     floor   wash vs white       two people apart    within black/grey
        ///     0.25    med 38.0  <5%: 0%   med 16.9  <5%:  8%   5.8 / 8.7
        ///     0.35    med 34.5  <5%: 0%   med 15.5  <5%:  9%   5.0 / 7.5
        ///     0.45    med 31.3  <5%: 1%   med 14.2  <5%: 10%   4.3 / 6.5
        ///     0.55    med 27.4  <5%: 2%   med 13.2  <5%: 11%   3.5 / 5.4
        ///     0.65    med 23.1  <5%: 3%   med 12.0  <5%: 13%   2.8 / 4.2
        ///     1.00    med  9.1  <5%: 39%  med 10.7  <5%: 26%   0.9 / 0.8
        ///
        /// 1.00 is the shipped code. There is no cliff, so the floor is a look
        /// decision inside a working range rather than a threshold with a right
        /// answer — 0.45 halves the darkest coat's albedo, which separates
        /// black from grey while leaving the cloth legible, and the still is
        /// what corrects it. What the sweep DOES settle is that every floor
        /// under 1.0 removes the 39%, which is the fault.
        ///
        /// NORMALISED AGAINST `MaxValue`, so the brightest coat the crowd may
        /// wear passes through untouched and nothing here can make the street
        /// dimmer than the wardrobe already says it is. That also means this
        /// cannot drift from the value ceiling: raise `MaxValue` and the wash
        /// re-spreads itself over the new range without a second edit.
        ///
        /// BOTH HALVES OF THE GUARD WERE RUN, which is rule 5b and is the half
        /// that normally goes unrun. Setting `WashFloor` back to 1.00 — the
        /// shipped behaviour — and running CoreTests gives
        ///
        ///     ok     - the brightest coat washes at full value, nothing is dimmed
        ///     FAILED - and the darkest coat is visibly darker — span 0.000
        ///
        /// so the accepting assertion passes under both rules (which is what
        /// makes it worth having) and the rejecting one scores exactly zero on
        /// the code this replaces.
        ///
        /// Returns HSV, like `Dress`, because Core does not know what a colour
        /// is and the conversion belongs where `Color.HSVToRGB` lives.
        /// AND THE VERSION THAT KNOWS WHAT IT IS MULTIPLYING, which is the one
        /// to use wherever the albedo has been measured.
        ///
        /// THE MEASUREMENT CAME BACK AND IT CHANGED THE RULE. `bodyAlbedo` read
        /// seventeen distinct sheets on the bought models:
        ///
        ///     0.04 0.14 0.21 0.21 0.22 0.35 0.38 0.44 0.50
        ///     0.54 0.58 0.61 0.62 0.67 0.73 0.78 (+1)
        ///
        /// against a wardrobe ceiling of 0.46. Eight of them are ABOVE it, the
        /// brightest by two thirds — so `MaxValue`'s promise that no crowd
        /// garment outshines a cast authored at 0.65-0.75 was being broken by
        /// the texture, not by the wardrobe. And I had guessed 0.9 for that
        /// number in three places before measuring it; the real top is 0.78 and
        /// the real MEDIAN is 0.50, so half the sheets were never the problem
        /// and a global darkening would have crushed them for nothing.
        ///
        /// SO THE ANCHOR IS PER MATERIAL AND NEEDS NO CONSTANT AT ALL. To land
        /// a garment at the value the wardrobe chose, multiply by
        /// `wardrobeValue / albedo`. That is not a tuning; it is what a
        /// multiply IS. A bright sheet gets pulled down to the band, a dark one
        /// is left alone because a multiply cannot lift it, and the ceiling
        /// enforces itself:
        ///
        ///     coat 0.46 on sheet 0.78 -> x0.59 -> renders 0.46, exactly the cap
        ///     coat 0.46 on sheet 0.14 -> x1.00 -> renders 0.14, under it
        ///     coat 0.09 on sheet 0.78 -> floor -> renders 0.35, as dark as
        ///                                        this is allowed to go
        ///
        /// AND THE FLOOR'S JOB CHANGES WITH IT. It used to mean "how dark may a
        /// coat make a texture", picked off a sweep. It now means "how far may
        /// a multiply darken before the cloth stops reading", which is a
        /// statement about legibility rather than about the palette — the same
        /// number, a better-founded question, and it is worth saying so out
        /// loud because a constant whose justification quietly changes is how
        /// `liveArmDrop` came to be read as the wrong thing.
        ///
        /// `albedo <= 0` means NOT MEASURED, and falls back to the ceiling
        /// normalisation below. Not to 1.0: an unmeasured sheet returning "no
        /// wash" would be the multiply-by-white this whole family exists to
        /// remove, arriving quietly on any body whose probe failed.
        public static void Wash(double hue, double sat, double val, double albedo,
                                out double washHue, out double washSat,
                                out double washVal)
        {
            washHue = hue;
            washSat = Feel.Clamp01(sat * WashSat);
            if (albedo <= 0)
            {
                washVal = WashFloor + (1.0 - WashFloor) * Feel.Clamp01(val / MaxValue);
                return;
            }
            double want = val / albedo;
            washVal = want < WashFloor ? WashFloor : (want > 1.0 ? 1.0 : want);
        }

        public static void Wash(double hue, double sat, double val,
                                out double washHue, out double washSat,
                                out double washVal)
            => Wash(hue, sat, val, -1, out washHue, out washSat, out washVal);
    }
}
