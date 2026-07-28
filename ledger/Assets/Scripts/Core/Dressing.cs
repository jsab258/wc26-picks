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
                                    bool alley = false)
        {
            double slots = lengthMetres / MetresPerPiece * Density(prosperity, alley);
            return (int)Feel.Clamp(Math.Floor(slots), 0, MaxPerFacade);
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

        /// Dress one facade: a wall running from (ax,az) to (bx,bz), with the
        /// building on the left and the street on the right.
        ///
        /// Everything comes back against the wall — nothing is ever placed
        /// out in the roadway, which is both correct and the thing that
        /// makes a naive scatter look wrong.
        public static List<Dressed> Facade(double ax, double az, double bx, double bz,
                                           double prosperity, bool alley, bool hasDoor)
        {
            var placed = new List<Dressed>();
            double dx = bx - ax, dz = bz - az;
            double length = Math.Sqrt(dx * dx + dz * dz);
            if (length < 1.0) return placed;
            dx /= length; dz /= length;
            // Outward normal: rotate the direction 90 degrees toward the street.
            double nx = dz, nz = -dx;
            double facing = Feel.HeadingDegrees(nx, nz);

            int budget = BudgetFor(length, prosperity, alley);
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
