using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// SET DRESSING — the small stuff that makes a street lived-in
    /// (the-gap.md §5, "set dressing density").
    ///
    /// Seven districts of graybox currently share three benches, a dumpster
    /// and a crate stack, all hand-placed near the bar. Everything beyond
    /// Hook Street is bare geometry, and bare geometry is the single
    /// loudest signal that a place was generated rather than built.
    ///
    /// TWO RULES DECIDE ALL OF THIS.
    ///
    /// **Clutter is not scattered, it ACCUMULATES.** It gathers where people
    /// are and where nobody looks — against walls, in corners, beside doors,
    /// down alleys. Uniform random scatter reads as noise and makes a street
    /// look like a mistake; the same number of objects pushed against the
    /// edges reads as a city. This is the whole difference and it costs
    /// nothing.
    ///
    /// **And it is DETERMINISTIC.** Hashed from position, never from a
    /// running RNG. A city that rearranges its bins when you reload a save
    /// is broken in a way players notice immediately and cannot unsee — and
    /// it would break the save/load equality the project already asserts.
    public enum Clutter
    {
        /// Bins, crates, stacked pallets. Against a wall, always.
        Bin = 0,
        /// A drainpipe running down a facade. Vertical, at building corners.
        Drainpipe = 1,
        /// Cellar hatch, kerb stone, a broken flag. Underfoot, flat.
        Ground = 2,
        /// Awning or canopy over a door. Marks an entrance from down the street.
        Awning = 3,
        /// Cables and washing lines strung between facades. Overhead, and the
        /// cheapest way to make a street feel enclosed.
        Overhead = 4,
        /// A puddle. Only where water would actually sit.
        Puddle = 5,
    }

    public struct Dressed
    {
        public Clutter Kind;
        public double X, Z;
        /// Degrees. Clutter against a wall faces out of it.
        public double Facing;
        /// 0.8..1.25 — nothing is exactly the same size as anything else.
        public double Scale;
    }

    public static class Dressing
    {
        /// Minimum gap between two pieces, metres. Below this they read as
        /// one lumpy object rather than as two things.
        public const double MinSpacing = 1.15;

        /// The most a facade may carry, PER METRE OF IT.
        ///
        /// A flat cap was the first version and it was wrong in a way the
        /// density test caught immediately: a twenty-metre shopfront and a
        /// two-hundred-metre alley both stopped at seven, so the cap bound on
        /// every short wall and the prosperity difference it was supposed to
        /// express never showed up at all. Long walls came out sparse and
        /// short ones came out packed — the exact opposite of both.
        public const double MetresPerPiece = 4.0;
        /// An absolute ceiling anyway, for frame time. A street buried in
        /// bins stops reading as a place and starts reading as a warehouse
        /// of props.
        public const int MaxPerFacade = 24;

        /// How many pieces a wall gets: its length AND how poor it is.
        ///
        /// Prosperity has to scale the BUDGET, not merely the per-slot
        /// chance. That was the second version and it was still wrong for
        /// the same reason as the first: a twenty-metre wall offers about
        /// seventeen legal slots after spacing, so even a rich street's
        /// thirty-percent chance fills a five-piece budget every time. The
        /// probability got swamped by the cap and both came out identical
        /// again — 5 vs 5, one number better than 7 vs 7 and just as wrong.
        public static int BudgetFor(double lengthMetres, double prosperity = 0.5,
                                    bool alley = false, double detail = 1.0)
        {
            double slots = lengthMetres / MetresPerPiece * Density(prosperity, alley)
                           * Feel.Clamp01(detail);
            return (int)Feel.Clamp(Math.Floor(slots), 0, MaxPerFacade);
        }

        // ---- WHERE THE DETAIL GOES (the-gap.md §4, the scope call) ---------

        /// Seven districts of graybox exist. The strategy doc says stop
        /// building geography and make two or three of them DENSE, because
        /// content volume is the one row on the comparison table that cannot
        /// be closed and spreading a fixed budget of detail over seven
        /// districts buys seven thin ones.
        ///
        /// This is that call, expressed as arithmetic rather than as a
        /// deletion. Nothing is removed; detail CONCENTRATES.
        ///
        /// AND IT FALLS OFF SMOOTHLY, which is the part worth getting right.
        /// The obvious implementation is a per-district multiplier, and it
        /// produces a seam: a street where clutter stops dead at a boundary
        /// the player cannot see reads as a bug, and is more damaging than
        /// uniform sparseness would have been. A distance ramp has no
        /// boundary to notice.

        /// Metres over which detail thins from full to floor.
        public const double DetailFalloffMetres = 260;

        /// What a district gets when it is far outside the dense core. Not
        /// zero: an empty street is worse than a sparse one, and the whole
        /// argument for concentrating is that the far places still have to
        /// read as places.
        public const double DetailFloor = 0.34;

        /// How densely to dress a facade, from how far it is from the nearest
        /// place worth spending on.
        public static double DetailAt(double metresFromDenseCore)
        {
            double d = Math.Max(0, metresFromDenseCore);
            double t = Feel.Clamp01(d / DetailFalloffMetres);
            // Smoothstep rather than linear: a linear ramp is still visible
            // as a gradient if you walk along it, and the eye is far better
            // at spotting a constant rate of change than a curved one.
            double eased = t * t * (3 - 2 * t);
            return 1.0 - (1.0 - DetailFloor) * eased;
        }

        /// Distance to the nearest of several dense cores. Nearest, not
        /// summed — two dense districts either side of a poor one should not
        /// quietly make the poor one dense as well.
        public static double NearestCore(double x, double z, (double x, double z)[] cores)
        {
            if (cores == null || cores.Length == 0) return 0;
            double best = double.MaxValue;
            foreach (var c in cores)
            {
                double dx = x - c.x, dz = z - c.z;
                double d = Math.Sqrt(dx * dx + dz * dz);
                if (d < best) best = d;
            }
            return best;
        }

        /// How far clutter sits from the wall it leans on.
        public const double WallOffset = 0.45;

        /// HOW MUCH, from how poor the street is.
        ///
        /// A poor street accumulates and a rich one is swept. That is true,
        /// and it is free characterisation: Hook reads as poorer than
        /// Fairview without a single authored difference between them.
        public static double Density(double prosperity, bool alley)
        {
            double poor = 1.0 - Feel.Clamp01(prosperity);
            double d = 0.25 + 0.55 * poor;
            // Nobody tidies an alley.
            if (alley) d = Math.Min(1.0, d * 1.6);
            return Feel.Clamp01(d);
        }

        /// A stable hash of a position. The whole determinism guarantee rests
        /// on this: same metre of street, same bin, forever, on every machine
        /// and after every reload.
        ///
        /// FNV-1a over the quantised coordinates rather than anything from
        /// System.Random or GetHashCode — the latter is randomised per
        /// process on .NET Core, which would have made the city rearrange
        /// itself on every launch while passing every test that ran in one.
        public static uint Hash(double x, double z, int salt)
        {
            unchecked
            {
                // Quantised to a centimetre so floating-point drift in a
                // position cannot change the answer.
                long qx = (long)Math.Round(x * 100), qz = (long)Math.Round(z * 100);
                uint h = 2166136261;
                foreach (long v in new[] { qx, qz, (long)salt })
                    for (int b = 0; b < 8; b++)
                    {
                        h ^= (uint)((v >> (b * 8)) & 0xFF);
                        h *= 16777619;
                    }
                return h;
            }
        }

        /// 0..1 from the hash. Deterministic everywhere.
        public static double Roll(double x, double z, int salt) =>
            (Hash(x, z, salt) % 100000) / 100000.0;

        /// WHAT KIND OF BUILDING THIS IS, which nothing has ever asked.
        ///
        /// Every mass in the city gets the same treatment: a fascia at 3.5m, a
        /// 1.15m door, a cornice. So a five-storey block, a corner shop and a
        /// dock warehouse are the same object at three sizes, and a street
        /// reads as repetition however well each individual wall is dressed.
        /// That is the note `GroundFloor` itself makes — "nothing told you
        /// where you could go in" — solved for one building and not for the
        /// difference between buildings.
        ///
        /// FROM POSITION AND PROSPERITY, deterministically, so the same corner
        /// is the same shop every run and the CI frames stay comparable.
        /// Prosperity is already what `Facade` uses to decide how much rubbish
        /// collects against a wall, and the two agree by construction: a rich
        /// frontage gets shops, a poor one gets tenements, and warehouses sit
        /// where nobody is spending money on the pavement.
        public enum Premises
        {
            /// A wide glazed frontage under a signboard. The commercial floor.
            Shop = 0,
            /// A narrow door, no fascia, windows that are windows rather than
            /// display. Somebody lives behind this wall.
            House = 1,
            /// Flats above a plain street door. The default in a dense poor
            /// district and most of what a port town is made of.
            Tenement = 2,
            /// A loading door wide enough for a cart, and no shopfront at all.
            Warehouse = 3,
        }

        /// How wide this kind of premises makes its street door, in metres.
        ///
        /// Named here rather than in the Game layer because it is the number
        /// that carries the DIFFERENCE — a warehouse door and a house door at
        /// the same width is the whole fault this type exists to fix, and a
        /// constant sitting in a renderer is a constant nobody tests.
        public static double DoorWidth(Premises p) =>
            p == Premises.Warehouse ? 3.0
            : p == Premises.Shop ? 1.3
            : p == Premises.House ? 0.95
            : 1.1;

        /// Whether this kind carries a signboard band over the ground floor.
        /// A house with a shop fascia is the single most obvious way to make a
        /// residential street look like a high street.
        public static bool HasFascia(Premises p) =>
            p == Premises.Shop || p == Premises.Warehouse;

        public static Premises KindAt(double x, double z, double prosperity, bool nearCore)
        {
            double r = Roll(x, z, 11);

            // PROSPERITY IS NOT DOING WHAT I ASKED IT TO, and the distribution
            // printed off this Core is what says so. It was keying the
            // warehouse rule, and the caller supplies only two values —
            // `StreetFrontProsperity` 0.55 and `BackAlleyProsperity` 0.15 —
            // which distinguish the FRONT of a building from its BACK, not a
            // rich district from a poor one. `GroundFloor` dresses street
            // fronts only, and it was handing 0.15 to every front away from a
            // core: forty percent of them came back warehouses. A street of
            // houses does not become an industrial estate because it is a
            // fifteen-minute walk from the shops.
            //
            // So the district signal is `nearCore`, which is real and is
            // computed from the actual core positions. Prosperity stays in the
            // signature because it is a real concept and a later caller may
            // have a genuine gradient — but nothing keys on it until one does,
            // rather than pretending a front/back flag is a wealth map.
            if (!nearCore && r < 0.25) return Premises.Warehouse;
            // Shops cluster where the money and the footfall are. Not
            // guaranteed even at the centre — a high street with a shop in
            // every single unit is a shopping centre, not a town.
            if (nearCore && r < 0.30 + 0.45 * Feel.Clamp01(prosperity)) return Premises.Shop;

            // HOUSES WERE UNREACHABLE AND THE BUILD SAID SO:
            // `premises=[shop42 house0 tenement69 shed18]`.
            //
            // The condition was `prosperity > 0.55`, and the two values any
            // real caller supplies are `StreetFrontProsperity = 0.55` and
            // `BackAlleyProsperity = 0.15`. Strictly greater than 0.55 is
            // false for both, so no wall in the city could ever be a house —
            // while the Core test asserted houses exist by passing 0.80, a
            // number no call site produces.
            //
            // That is rule 6 wearing a passing test: exercised with synthetic
            // input the game never sends. Worse than an untested branch,
            // because the green tick says the opposite.
            //
            // The deeper problem is that prosperity here is not a gradient at
            // all — it is two constants, one per side of the building, so it
            // carries no per-wall variation to key on. Houses therefore key
            // off the roll and the district, which DO vary: near a core a
            // frontage that is not a shop is somebody's front door, and away
            // from one it is flats.
            // AND THEN THERE WERE THREE, WHICH IS ALSO WRONG AND FOR A
            // DIFFERENT REASON. The first repair put houses NEAR a core, in
            // the band left over after shops took everything below 0.55 — so
            // they got a seven-percent sliver of the one place in town where
            // nobody lives in a terraced house. `house3` out of 129.
            //
            // Backwards. A core street front is shops with flats above them;
            // houses are what the streets AWAY from it are made of, alongside
            // the tenements and the sheds. Putting them where the shops are
            // was reaching for the nearest free band rather than asking what
            // the town is like — a threshold picked to make a zero go away,
            // which is the same reflex rule 2 names about making red go away.
            if (nearCore) return Premises.Tenement;   // flats over the shops
            if (r < 0.60) return Premises.House;      // the residential streets
            return Premises.Tenement;
        }

        /// Dress one facade: a wall running from (ax,az) to (bx,bz), with the
        /// building on the left and the street on the right.
        ///
        /// Everything comes back against the wall — nothing is ever placed
        /// out in the roadway, which is both correct and the thing that
        /// makes a naive scatter look wrong.
        public static List<Dressed> Facade(double ax, double az, double bx, double bz,
                                           double prosperity, bool alley, bool hasDoor,
                                           double detail = 1.0)
        {
            var placed = new List<Dressed>();
            double dx = bx - ax, dz = bz - az;
            double length = Math.Sqrt(dx * dx + dz * dz);
            if (length < 1.0) return placed;
            dx /= length; dz /= length;
            // Outward normal: rotate the direction 90 degrees toward the street.
            double nx = dz, nz = -dx;
            double facing = Feel.HeadingDegrees(nx, nz);

            int budget = BudgetFor(length, prosperity, alley, detail);
            if (budget <= 0) return placed;
            // The per-slot roll now chooses WHERE along the wall rather than
            // how many — the budget decides how many, and this decides which
            // metres of the wall got unlucky.
            const double slotChance = 0.55;
            double lastAt = -99;

            // Walk the wall in metre steps and ask each metre whether
            // something collected there. Stepping rather than sampling N
            // random points is what keeps the spacing rule cheap and exact.
            for (double t = 0.8; t < length - 0.8; t += 0.5)
            {
                if (placed.Count >= budget) break;
                if (t - lastAt < MinSpacing) continue;

                double px = ax + dx * t + nx * WallOffset;
                double pz = az + dz * t + nz * WallOffset;
                if (Roll(px, pz, 1) > slotChance) continue;

                double pick = Roll(px, pz, 2);
                Clutter kind;
                // CORNERS COLLECT. The ends of a wall get more than the
                // middle, because that is where things are put down and
                // where nobody sweeps.
                bool nearCorner = t < 2.5 || t > length - 2.5;
                if (nearCorner && pick < 0.45) kind = Clutter.Drainpipe;
                else if (pick < 0.42) kind = Clutter.Bin;
                else if (pick < 0.62) kind = Clutter.Ground;
                else if (pick < 0.78) kind = Clutter.Puddle;
                else if (alley) kind = Clutter.Bin;
                else kind = Clutter.Ground;

                placed.Add(new Dressed
                {
                    Kind = kind, X = px, Z = pz, Facing = facing,
                    Scale = 0.8 + Roll(px, pz, 3) * 0.45,
                });
                lastAt = t;
            }

            // A door gets an awning, because an entrance nobody can find from
            // down the street is an entrance the player walks past.
            //
            // AND NOW THE DOOR. Both come out of this one block, at one
            // position, so a canopy can never end up over blank wall and a
            // door can never end up in the open — which is the obvious way to
            // get this wrong and is invisible from anywhere except a frame.
            //
            // NOT BUDGET-GATED, unlike the clutter above. Bins and puddles are
            // texture and thinning them in a far district is the LOD working;
            // an entrance is architecture, and a building whose door was
            // dropped because a random roll spent the budget is a building the
            // player cannot read at all. The awning keeps its budget check
            // because a missing canopy costs legibility, not meaning.
            if (hasDoor && placed.Count <= budget)
            {
                double mx = ax + dx * (length * 0.5) + nx * WallOffset;
                double mz = az + dz * (length * 0.5) + nz * WallOffset;
                placed.Add(new Dressed
                {
                    Kind = Clutter.Awning, X = mx, Z = mz, Facing = facing,
                    Scale = 1.0,
                });
            }
            return placed;
        }

        /// Cables strung across a street. Overhead clutter is the cheapest
        /// thing there is for making a street feel ENCLOSED rather than like
        /// two rows of boxes with a gap, and nobody ever budgets for it.
        public static bool CableAt(double x, double z, double prosperity, double spanMetres)
        {
            // Too wide to string anything across, and a cable over a main
            // avenue reads as a mistake rather than as a slum.
            if (spanMetres > 14) return false;
            double chance = Density(prosperity, false) * 0.55;
            return Roll(x, z, 7) < chance;
        }
    }
}
