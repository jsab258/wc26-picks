using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// Population at district scale (roadmap M9, design doc §17 gap 3).
    ///
    /// The city had 36 people in it. That was never a constraint — we proved
    /// generation works months ago, 60 validator-passed cards in 19 calls — it
    /// was a decision nobody revisited. This revisits it.
    ///
    /// THE ARRANGEMENT, which is KCD2's and is the only one that works: almost
    /// nobody is simulated. A resident is a dozen fields until the player's
    /// attention reaches them, and then they become a person. Three bands:
    ///
    ///   Near — a walker in the world with a full brain: memory, knowledge,
    ///          suspicion, a place in the gossip mill. Costly. Capped.
    ///   Mid  — in the gossip mill and nowhere else. They carry and pass talk,
    ///          they can be met if the player goes to them, they do not render.
    ///   Far  — a record. They contribute to the district STATISTICALLY and hold
    ///          no individual state at all. Thousands of these cost nothing.
    ///
    /// The honesty of the Far band is the whole trick. It does not pretend to
    /// simulate people it isn't simulating. It answers exactly one question —
    /// *roughly how much of this district has heard something* — and when one of
    /// them is promoted, that answer is used to decide, deterministically,
    /// whether this particular person had heard it. The same resident always
    /// resolves the same way, so the player can leave a street and come back to
    /// a consistent world rather than a re-rolled one.
    ///
    /// ANYONE LOAD-BEARING IS NEVER DEMOTED. Crew, suppliers, debtors, anyone
    /// holding a rumor about the player, anyone the player has ever spoken to:
    /// they stay at their band whatever the caps say. Losing a person's memory
    /// because the player walked two streets away would violate pillar P5 more
    /// severely than any performance win could justify.

    public enum Lod
    {
        /// A record. Statistical only.
        Far = 0,
        /// In the gossip mill; carries and spreads talk. Not rendered.
        Mid = 1,
        /// A walker with a full brain.
        Near = 2,
    }

    /// One of the district's people, at rest. Twelve fields, no allocations
    /// beyond the strings — this is what makes thousands affordable.
    public class Resident
    {
        public string Id;
        /// Position in the population list. Kept so anything that needs to reach
        /// a resident's neighbours does not have to scan three thousand records.
        public int Index;
        public string Name;
        public string District;
        public string Trade;
        /// "day" | "night" | "both" — which circle they talk in.
        public string Circle = "day";
        public double Greed, Nerve, Loyalty;
        /// Where they sleep and where they work, as world coordinates. Ints, and
        /// no engine types, so Core stays engine-free.
        public int HomeX, HomeZ, WorkX, WorkZ;
        public int WorkFromHour = 9, WorkToHour = 18;

        public Lod Band = Lod.Far;
        /// Set once the game has promoted them and they have real state. Such a
        /// person is never demoted below Mid again.
        public bool Known;

        public override string ToString() => $"{Name} ({Trade}, {District}, {Band})";
    }

    public class Population
    {
        public readonly List<Resident> Residents = new List<Resident>();
        // Lookup by id. The gossip mill asks "where is r1842" once per graph
        // edge per round, and scanning three thousand records for that would
        // make the crowd cost more than it is worth.
        readonly Dictionary<string, Resident> _byId = new Dictionary<string, Resident>();

        /// How many people may have a body and a brain at once. The number is a
        /// frame-budget decision, not a design one.
        public int NearCap = 28;
        /// How many may be in the gossip mill at once. Larger, because a mill
        /// entry is cheap next to a walker — this is the band that makes the
        /// street feel populated by people you have not met yet.
        public int MidCap = 120;

        /// How near a body has to be to exist at all. THE CAPS ARE NOT ENOUGH:
        /// band assignment is by RANK, so the nearest 28 people got bodies
        /// however far away they were — walk into an empty district and the
        /// crowd materialises around you at whatever distance the 28th-nearest
        /// person happens to be. That is the "characters appear suddenly"
        /// playtest note, and it is the same bug as "too many characters":
        /// rank with no ceiling always fills the quota (2026-07-28).
        public double NearMetres = 34;
        public double MidMetres = 130;
        /// Hysteresis: once you have a body you keep it a little past the
        /// ceiling, so somebody walking the boundary does not strobe.
        public double BandSlack = 6;

        // ---- generation ----

        static readonly string[] Given =
        {
            "Frank", "Dolores", "Ray", "Rita", "Vince", "Donna", "Walt", "Jeanie", "Curtis", "Marla",
            "Pete", "Yolanda", "Tony", "Kathy", "Stan", "Nadine", "Wendell", "Sandy", "Doug", "Lucille",
            "Earl", "Marcy", "Joey", "Renee", "Bruce", "Vera", "Sal", "Dawn", "Roland", "Zora",
            "Ivan", "Millie", "Carl", "Bev", "Nick", "Angie", "Gus", "Terri", "Lonnie", "Ollie",
        };

        static readonly string[] Family =
        {
            "Sedlak", "Brella", "Novak", "Kovacs", "Horvath", "Maddox", "Pallas", "Vaughn", "Zorich", "Simms",
            "Babich", "Dury", "Griggs", "Hodak", "Ivers", "Jukes", "Clary", "Loveric", "Mathis", "Nizich",
            "Odom", "Perry", "Rukavina", "Salas", "Tomic", "Uzelac", "Vukas", "Zeigler", "Cavett", "Dujmovic",
        };

        static readonly string[] Trades =
        {
            "dock hand", "line cook", "clerk", "mechanic", "printer", "bus driver", "baker",
            "night janitor", "bookkeeper", "welder", "hairdresser", "cab driver", "roofer", "nurse",
            "stevedore", "barber", "secretary", "electrician", "cook", "security guard", "waitress", "trucker",
            "cashier", "machinist", "usher", "scrap hauler", "bartender", "ferry hand", "forklift driver", "sign painter",
        };

        /// Everybody in the district, deterministically. The same seed always
        /// produces the same city — which is what lets a save file store a seed
        /// and a handful of exceptions instead of ten thousand people.
        /// How the city's people divide between its districts, in parts.
        ///
        /// Equal thirds were fine while both districts were places people live,
        /// and became a lie the moment Ironside existed: a warehouse district
        /// with a thousand residents is not a place without witnesses, it is a
        /// suburb with bad lighting. Density IS the district's character here —
        /// what makes Ironside worth walking to at night is that almost nobody
        /// sleeps between those long walls.
        ///
        /// Null means equal, which is what every caller that predates this got.
        public static IReadOnlyList<string> Spread(IReadOnlyList<string> districts,
            IReadOnlyList<int> weights)
        {
            if (districts == null || districts.Count == 0) return districts;
            if (weights == null || weights.Count != districts.Count) return districts;
            var wheel = new List<string>();
            for (int i = 0; i < districts.Count; i++)
                for (int w = 0; w < Math.Max(0, weights[i]); w++) wheel.Add(districts[i]);
            return wheel.Count > 0 ? wheel : districts;
        }

        /// `weights` is where people SLEEP; `workWeights` is where they spend
        /// the day. Two lists rather than one, because the difference between
        /// them is the most useful thing a district generator can express:
        /// Ironside houses almost nobody and employs a third of the city, so it
        /// is crowded at noon and empty at midnight — and a player who works
        /// that out has learned something real about where to do things.
        /// Both default to equal shares, which is what callers predating this got.
        public static Population Generate(int count, int seed, IReadOnlyList<string> districts,
            IReadOnlyList<int> weights = null, IReadOnlyList<int> workWeights = null)
        {
            var pop = new Population();
            if (count <= 0 || districts == null || districts.Count == 0) return pop;

            var rng = new Random(seed);
            var used = new HashSet<string>();
            // The wheel repeats each district in proportion to its share, so
            // the round-robin below stays exactly as deterministic as it was.
            var wheel = Spread(districts, weights);
            var workWheel = Spread(districts, workWeights ?? weights);

            for (int i = 0; i < count; i++)
            {
                var district = wheel[i % wheel.Count];
                string name = null;
                // Given × Family is 1200 combinations; past that, people share a
                // name with somebody, which is true of real streets. A middle
                // initial keeps ids unique without inventing silly names.
                for (int attempt = 0; attempt < 6 && name == null; attempt++)
                {
                    var candidate = Given[rng.Next(Given.Length)] + " " + Family[rng.Next(Family.Length)];
                    if (used.Add(candidate)) name = candidate;
                }
                if (name == null)
                    name = Given[rng.Next(Given.Length)] + " " + Family[rng.Next(Family.Length)];

                bool night = rng.NextDouble() < 0.28;
                var r = new Resident
                {
                    Id = $"r{i:0000}",
                    Index = i,
                    Name = name,
                    District = district,
                    Trade = Trades[rng.Next(Trades.Length)],
                    Circle = night ? (rng.NextDouble() < 0.3 ? "both" : "night") : "day",
                    Greed = Round2(0.2 + rng.NextDouble() * 0.6),
                    Nerve = Round2(0.2 + rng.NextDouble() * 0.6),
                    Loyalty = Round2(0.3 + rng.NextDouble() * 0.4),
                };
                // People live IN their district. This was -40..40 for everybody,
                // which was fine while there was one district and quietly wrong
                // the moment there were two: three hundred residents "of Copper
                // Row" were living in the Hook, and the crowd would never have
                // gone north of the cut.
                Place(rng, district, out r.HomeX, out r.HomeZ);
                // And about a third of them cross the water to work, which is
                // what makes the two bridges carry somebody rather than being
                // scenery. A commuter is also the cheapest possible reason for a
                // face to be somewhere it is not usually seen.
                var worksIn = rng.NextDouble() < 0.33 ? Across(workWheel, district, rng) : district;
                Place(rng, worksIn, out r.WorkX, out r.WorkZ);
                if (night) { r.WorkFromHour = 20; r.WorkToHour = 4; }
                else { r.WorkFromHour = 7 + rng.Next(3); r.WorkToHour = 16 + rng.Next(4); }
                pop.Residents.Add(r);
                pop._byId[r.Id] = r;
            }
            return pop;
        }

        /// A point inside the named district, or inside the founding one when
        /// the name is somewhere that exists in the fiction and not yet on the
        /// ground (Ironside). Deliberately inset from the edges so nobody's
        /// front door is in the middle of an avenue.
        static void Place(Random rng, string districtName, out int x, out int z)
        {
            foreach (var d in StreetMap.Districts)
            {
                if (d.Name != districtName) continue;
                int minX = (int)d.AvenuesX[0] + 6, maxX = (int)d.AvenuesX[d.AvenuesX.Length - 1] - 6;
                int minZ = (int)d.AvenuesZ[0] + 6, maxZ = (int)d.AvenuesZ[d.AvenuesZ.Length - 1] - 6;
                x = rng.Next(minX, maxX + 1);
                z = rng.Next(minZ, maxZ + 1);
                return;
            }
            x = rng.Next(-40, 41);
            z = rng.Next(-40, 41);
        }

        /// Somewhere that is not here, for the third of people who commute.
        ///
        /// Drawn off the WORK wheel, which is how Ironside ends up with hands
        /// in it: almost nobody sleeps there, and the day still fills the goods
        /// yards with people who came down the two roads from somewhere else
        /// and will leave again before dark. The gap between who is there at
        /// noon and who is there at midnight is the district, and it falls
        /// straight out of the two lists rather than out of a special case.
        static string Across(IReadOnlyList<string> wheel, string here, Random rng)
        {
            for (int attempt = 0; attempt < 8; attempt++)
            {
                var pick = wheel[rng.Next(wheel.Count)];
                if (pick != here) return pick;
            }
            for (int i = 0; i < wheel.Count; i++)
                if (wheel[i] != here) return wheel[i];
            return here;
        }

        static double Round2(double v) => Math.Round(v, 2);

        // ---- level of detail ----

        /// Assigns bands. `distanceTo` is how far the player's attention is from
        /// a resident — the game passes world distance; the lab passes whatever
        /// it likes. `loadBearing` is the set of ids that must never be demoted
        /// below Mid, whatever the caps say.
        ///
        /// Returns the residents whose band CHANGED, so the game can spawn and
        /// despawn exactly those and nothing else.
        // Scratch buffers reused across calls. This runs every few seconds for
        // the whole life of a session, and a fresh LINQ chain over three
        // thousand people each time is three thousand delegate invocations, two
        // enumerators and a new list — per call, forever. None of that is
        // needed: the set of residents does not change, only their order does.
        readonly List<Resident> _ordered = new List<Resident>();
        readonly Dictionary<string, double> _distanceCache =
            new Dictionary<string, double>(StringComparer.Ordinal);

        /// Is this person out of doors right now? MOST PEOPLE ARE INSIDE — the
        /// street of a living city is a handful of walkers, not its whole
        /// population standing on the pavement. Deterministic per person and
        /// hour, so somebody who is out stays out rather than flickering, and
        /// biased to the working day: mornings and evenings move, small hours
        /// do not (playtest 2026-07-28).
        public static bool OutdoorsAt(Resident r, int hour)
        {
            if (r == null) return false;
            int h = ((hour % 24) + 24) % 24;
            // A stable per-person-per-hour value in [0,1).
            unchecked
            {
                int seed = r.Index * 486187739 + h * 97;
                seed ^= seed >> 13; seed *= 1274126177; seed ^= seed >> 16;
                double roll = (seed & 0x7FFFFFF) / (double)0x8000000;
                double chance =
                    h >= 23 || h < 5 ? 0.03 :          // the small hours belong to few
                    h < 7 ? 0.07 :
                    h < 9 ? 0.20 :                     // out to work
                    h < 12 ? 0.13 :
                    h < 14 ? 0.18 :                    // the middle of the day
                    h < 17 ? 0.13 :
                    h < 19 ? 0.20 :                    // home again
                    0.10;
                return roll < chance;
            }
        }

        public List<Resident> SetBands(Func<Resident, double> distanceTo, ISet<string> loadBearing,
            Func<Resident, bool> hasBody = null)
        {
            var changed = new List<Resident>();
            if (distanceTo == null) return changed;

            // Distance is measured ONCE per resident and cached for the sort.
            // A comparison-based sort asks for each key O(log n) times, so
            // without this the game computes ~35,000 square roots to place 3,000
            // people — and it is the same 3,000 answers every time.
            _distanceCache.Clear();
            _ordered.Clear();
            for (int i = 0; i < Residents.Count; i++)
            {
                var r = Residents[i];
                _distanceCache[r.Id] = distanceTo(r);
                _ordered.Add(r);
            }

            // Load-bearing people are placed first and take their slots off the
            // top, so a crowded street can never evict the bookkeeper.
            // The Index tiebreak is load-bearing, not tidiness. List.Sort is
            // UNSTABLE where OrderBy was stable, so two people standing the same
            // distance away could swap places between calls and be reported as
            // having changed band when nothing about them changed — the game
            // would despawn and respawn them for nothing, forever. A total
            // ordering makes the result identical every time it is asked.
            _ordered.Sort((a, b) =>
            {
                bool la = IsLoadBearing(a, loadBearing), lb = IsLoadBearing(b, loadBearing);
                if (la != lb) return la ? -1 : 1;
                int d = _distanceCache[a.Id].CompareTo(_distanceCache[b.Id]);
                return d != 0 ? d : a.Index.CompareTo(b.Index);
            });

            int near = 0, mid = 0;
            foreach (var r in _ordered)
            {
                double dist = _distanceCache[r.Id];
                // The ceiling, with slack for whoever already has a body.
                double nearLimit = NearMetres + (r.Band == Lod.Near ? BandSlack : 0);
                double midLimit = MidMetres + (r.Band == Lod.Mid ? BandSlack : 0);
                bool bodyOk = hasBody == null || hasBody(r);

                Lod want;
                if (near < NearCap && dist <= nearLimit && bodyOk) { want = Lod.Near; near++; }
                else if (mid < MidCap && dist <= midLimit) { want = Lod.Mid; mid++; }
                else want = Lod.Far;

                // The one rule that overrides the caps: somebody with real state
                // is never dropped back to a record.
                if (want == Lod.Far && IsLoadBearing(r, loadBearing)) want = Lod.Mid;

                if (r.Band == want) continue;
                r.Band = want;
                changed.Add(r);
            }
            return changed;
        }

        static bool IsLoadBearing(Resident r, ISet<string> loadBearing) =>
            r.Known || (loadBearing != null && loadBearing.Contains(r.Id));

        public IEnumerable<Resident> InBand(Lod band) => Residents.Where(r => r.Band == band);
        public int CountIn(Lod band) => Residents.Count(r => r.Band == band);
        public Resident ById(string id) =>
            id != null && _byId.TryGetValue(id, out var r) ? r : null;

        // ---- the statistical band ----

        /// Roughly what share of the district has heard some version of the talk
        /// about the player, 0..1. This is the ONLY question the Far band
        /// answers, and it is answered as an aggregate because that is all it
        /// honestly knows.
        ///
        /// It rises with how loud the street already is and with how many days
        /// the talk has had to travel, and it saturates — a story never reaches
        /// literally everyone, because some people do not listen.
        public const double AmbientCeiling = 0.8;

        public static double AmbientReach(double heat, int daysCirculating)
        {
            heat = Math.Max(0, Math.Min(1, heat));
            int days = Math.Max(0, daysCirculating);
            // Saturating growth: fast for the first few days, then flattening.
            double travelled = 1.0 - Math.Pow(0.72, days);
            return AmbientCeiling * heat * travelled;
        }

        /// When a Far resident is promoted, did THIS person hear it? Decided by a
        /// stable hash of their id against the ambient reach, so the answer never
        /// changes between visits. Walking away and coming back must not re-roll
        /// the neighbourhood's memory.
        public static bool HeardIt(Resident r, double ambientReach)
        {
            if (r == null || ambientReach <= 0) return false;
            if (ambientReach >= 1) return true;
            return StableFraction(r.Id) < ambientReach;
        }

        /// FNV-1a, folded to 0..1. Deterministic across runs and platforms —
        /// string.GetHashCode is not, and a world that reshuffles itself between
        /// sessions is not a world.
        internal static double StableFraction(string s)
        {
            unchecked
            {
                uint hash = 2166136261;
                foreach (var c in s ?? "")
                {
                    hash ^= c;
                    hash *= 16777619;
                }
                return hash / (double)uint.MaxValue;
            }
        }

        /// The district's population in a phrase, for the ledger panel. A count
        /// on its own is a statistic; this is a street.
        public string StatusLine() =>
            $"{Residents.Count} people on this side of the river; " +
            $"{CountIn(Lod.Near)} of them in front of you, {CountIn(Lod.Mid)} within earshot";

        // ---- persistence ----

        /// A generated population is stored as its seed plus the exceptions:
        /// who has been met, and who is currently promoted. Ten thousand people
        /// in a few hundred bytes, which is the point of generating them.
        public Dictionary<string, object> Capture(int count, int seed)
        {
            var known = Residents.Where(r => r.Known).Select(r => (object)r.Id).ToList();
            return new Dictionary<string, object>
            {
                { "count", count }, { "seed", seed }, { "known", known },
            };
        }

        public void RestoreKnown(Dictionary<string, object> data)
        {
            if (data == null) return;
            foreach (var r in Residents) { r.Known = false; r.Band = Lod.Far; }
            var known = MiniJson.GetList(data, "known");
            if (known == null) return;
            var ids = new HashSet<string>(known.OfType<string>());
            foreach (var r in Residents)
                if (ids.Contains(r.Id)) { r.Known = true; r.Band = Lod.Mid; }
        }
    }

    /// P5's "statistical sim elsewhere", made concrete: one number per
    /// district for what the far city is FEELING while nobody renders it.
    /// Computed from things that are already district-keyed — how much of the
    /// district the player's empire owns, and how poor the street has gotten —
    /// and cashed in at exactly one moment: when a resident is promoted into
    /// the live mill, they arrive already shaped by where they live. A
    /// squeezed, half-owned quarter sends up warier, less loyal people; a
    /// rich untouched one sends up people with no opinion of you yet. The far
    /// city is not frozen; it is summarized.
    public static class DistrictPulse
    {
        /// 0..1. Deliberately gentle: this seeds STARTING posture, it does not
        /// play the game for anybody.
        public static double Unease(int ownedBusinessesHere, double prosperity) =>
            Math.Clamp(0.18 * ownedBusinessesHere + Math.Max(0.0, 0.45 - prosperity) * 1.2, 0.0, 1.0);

        /// How the pulse lands on a promoted resident: suspicion floor and a
        /// loyalty shave, both bounded so authored people stay authorable.
        public static (double suspicionFloor, double loyaltyShave) Arrival(double unease) =>
            (Math.Min(0.5, unease * 0.35), Math.Min(0.2, unease * 0.15));
    }
}
