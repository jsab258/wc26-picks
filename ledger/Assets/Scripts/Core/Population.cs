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
                // SCALED BOUNDS, because the avenue arrays are source data
                // and the city is stretched about the origin. Reading them raw
                // put four districts' residents 136-184m from the district
                // they live in — the same fault as `DistrictAt`, in the second
                // of five places that had it.
                StreetMap.BoundsOf(d, out var bx0, out var bx1, out var bz0, out var bz1);
                int minX = (int)bx0 + 6, maxX = (int)bx1 - 6;
                int minZ = (int)bz0 + 6, maxZ = (int)bz1 - 6;
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
        /// WHERE A RESIDENT ACTUALLY IS at this hour.
        ///
        /// THE CROWD DEFECT, found by the density sampler on 2026-07-28: the
        /// sim reported 19 bodies within 20 metres and only THREE of them
        /// were crowd residents. The other sixteen were the authored cast.
        /// Seven hundred simulated people were contributing almost nothing to
        /// the street.
        ///
        /// The cause was not the population number, the LOD caps, or the
        /// spawn logic — all of which were fine. It was that a resident's
        /// position was always their home or their workplace, both of which
        /// are INSIDE BUILDINGS. The player walks on streets. So the near
        /// band could only ever contain the two or three people whose front
        /// doors happened to be within thirty-four metres, and the entire
        /// crowd was permanently indoors.
        ///
        /// Real people are on the street because they are BETWEEN two
        /// places. So an outdoor resident is placed along the line from home
        /// to work, at a stable per-person-per-hour fraction — which puts
        /// them on the routes the streets already follow, spreads them out
        /// rather than clumping them at doors, and moves them hour to hour
        /// without needing a pathfinder.
        ///
        /// Returns false when they are indoors, and the caller should use
        /// home or work as before.
        /// How long one trip across the city lasts. Three hours is generous
        /// for a walk and deliberately so: it is the presence window, and a
        /// short one puts us back to people blinking in and out.
        public const int TripHours = 3;

        public static bool OutdoorPosition(Resident r, int day, int hour, out double x, out double z)
        {
            x = z = 0;
            if (r == null) return false;
            // Presence is decided for the whole block, off the hour the block
            // STARTS, so it cannot change underneath somebody mid-walk.
            int blockStart = (((hour % 24) + 24) % 24) / TripHours * TripHours;
            if (!OutdoorsAt(r, day, blockStart)) return false;

            int h = ((hour % 24) + 24) % 24;
            // A TRIP, not an hourly coin flip.
            //
            // The first version re-rolled presence every hour, and a test
            // caught what that means: somebody outdoors at one o'clock and
            // indoors at two does not walk home, they VANISH — and reappear
            // somewhere else an hour later. That is the "characters appearing
            // suddenly" complaint from the first playtest, reintroduced
            // through a different door.
            //
            // So a trip spans a block of hours. Presence is decided once for
            // the block, and within it the walk advances from one end of the
            // route to the other. Continuous while it lasts, which is what
            // stops a street of people from flickering.
            int block = h / TripHours;
            unchecked
            {
                // A different mix from OutdoorsAt's, or where somebody stands
                // would correlate with whether they are out at all, and the
                // crowd would bunch at one end of every street.
                // THE DAY IS IN HERE TOO, and leaving it out would have been
                // the subtler half of the same bug: a different set of people
                // outdoors, every one of them walking the identical route in
                // the identical direction they walked yesterday. Who is out
                // would vary and what the street LOOKS like would not.
                int d = ((day % 7) + 7) % 7;
                int seed = r.Index * 486187739 + block * 40503 + d * 374761393 + 7;
                seed ^= seed >> 15; seed *= 668265263; seed ^= seed >> 13;
                double along = (seed & 0x7FFFFFF) / (double)0x8000000;
                // Which direction they are walking is also fixed for the
                // trip, so half the crowd is going the other way.
                bool outbound = (seed & 0x8000000) == 0;
                double through = ((h % TripHours) + along) / TripHours;
                double t = outbound ? through : 1.0 - through;
                // Kept off both ends: at 0 or 1 they are standing in a
                // doorway again, which is the thing this exists to fix.
                t = 0.15 + 0.70 * t;
                x = r.HomeX + (r.WorkX - r.HomeX) * t;
                z = r.HomeZ + (r.WorkZ - r.HomeZ) * t;
            }
            return true;
        }

        /// Day 0 is a Monday, so days 5 and 6 of each week are the rest days.
        /// A convention rather than a discovery, stated once here so nothing
        /// downstream has to guess it or quietly assume a different one.
        ///
        /// WHAT THAT MEANS FOR THE CAMPAIGN, worked out rather than left for
        /// somebody to re-derive: `Now.Day` starts at 1, so the new owner's
        /// first day is a Tuesday and the rest days fall on campaign days 5 and
        /// 6 — a Saturday and a Sunday, one weekend inside the survive-week.
        /// That is the right shape by luck rather than by design, and it is
        /// written down so the next person to move the origin can see what they
        /// would be moving.
        ///
        /// AND IT IS NOT EXERCISED IN THE ENGINE. The sim renders campaign days
        /// 1 and 2, both working days, so no CI still has ever shown a rest day
        /// and no gate has ever evaluated one. The behaviour is covered by
        /// CoreTests and by nothing else. Said out loud because "days differ
        /// now" is exactly the kind of claim that reads as finished while half
        /// of it has never run.
        public static bool IsRestDay(int day) => (((day % 7) + 7) % 7) >= 5;

        /// WHICH DAY, AND THERE WAS NO SUCH THING BEFORE.
        ///
        /// This took an hour and reduced it mod 24, and so did `OutdoorPosition`
        /// — so there was no day parameter anywhere in the routine model and
        /// every Tuesday in this town was every Saturday. It surfaced as an
        /// arithmetic artefact rather than as a design complaint: `Recurrence`
        /// looped seven days and every column came out identical, with 86% of
        /// encounters "repeat", which is exactly 6/7. My week was one day
        /// counted seven times.
        ///
        /// That is an immersion fault of the first order for a game whose whole
        /// claim is a town you come to know. Recurrence was TOTAL — you could
        /// not fail to run into the same people, in the same places, at the same
        /// hours, for ever. Learning a town means noticing that the market is
        /// different on a Saturday, and there was nothing to notice.
        ///
        /// Two things now differ. WHO is out changes day to day, because the day
        /// enters the hash — same crowd size, different faces, which is what
        /// makes a familiar face feel like a coincidence instead of a fixture.
        /// And WHEN people are out changes on the rest days: no commute peaks at
        /// eight and six, more of the town outdoors through the middle of the
        /// day and into the evening.
        ///
        /// The weekday numbers are UNCHANGED. They are the ones the crowd
        /// density floor was measured against, and moving them would invalidate
        /// that measurement in the same commit that adds a feature — two changes
        /// at once, neither attributable.
        public static bool OutdoorsAt(Resident r, int day, int hour)
        {
            if (r == null) return false;
            int h = ((hour % 24) + 24) % 24;
            int d = ((day % 7) + 7) % 7;
            // A stable per-person-per-day-per-hour value in [0,1).
            unchecked
            {
                int seed = r.Index * 486187739 + h * 97 + d * 40503;
                seed ^= seed >> 13; seed *= 1274126177; seed ^= seed >> 16;
                double roll = (seed & 0x7FFFFFF) / (double)0x8000000;
                double chance = IsRestDay(day)
                    // A REST DAY. Nobody commutes, so the two sharp peaks
                    // flatten; the town is out later in the morning, thicker
                    // through the middle of the day, and stays out in the
                    // evening. Totalled deliberately close to a weekday so this
                    // changes the SHAPE of a day rather than the size of the
                    // crowd — a busier Saturday would be a separate decision,
                    // and would need its own measurement.
                    ? (h >= 24 || h < 6 ? 0.03 :
                       h < 9 ? 0.06 :                  // nobody is anywhere early
                       h < 11 ? 0.14 :
                       h < 16 ? 0.22 :                 // the long middle of a free day
                       h < 19 ? 0.17 :
                       h < 23 ? 0.14 :                 // and out later than a work night
                       0.05)
                    : (h >= 23 || h < 5 ? 0.03 :       // the small hours belong to few
                       h < 7 ? 0.07 :
                       h < 9 ? 0.20 :                  // out to work
                       h < 12 ? 0.13 :
                       h < 14 ? 0.18 :                 // the middle of the day
                       h < 17 ? 0.13 :
                       h < 19 ? 0.20 :                 // home again
                       0.10);
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
