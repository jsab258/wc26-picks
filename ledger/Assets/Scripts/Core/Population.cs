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

        // ---- generation ----

        static readonly string[] Given =
        {
            "Milos", "Vesna", "Tibor", "Ruta", "Ferko", "Danica", "Zlatko", "Ivana", "Bojan", "Mirela",
            "Petar", "Jelena", "Anton", "Katica", "Stjepan", "Nada", "Vlado", "Sanja", "Drago", "Ljubica",
            "Emil", "Marta", "Josip", "Rada", "Branko", "Vera", "Slavko", "Dunja", "Radomir", "Zora",
            "Ivo", "Milena", "Karel", "Bosa", "Nikola", "Anka", "Gojko", "Tereza", "Lazar", "Olga",
        };

        static readonly string[] Family =
        {
            "Sedlak", "Brela", "Novak", "Kovac", "Horvat", "Marek", "Palas", "Vrban", "Zoric", "Simek",
            "Babic", "Duric", "Grgic", "Hodak", "Ivsic", "Jukic", "Klaric", "Lovric", "Matic", "Nizic",
            "Odak", "Peric", "Rukavina", "Salaj", "Tomic", "Uzelac", "Vukas", "Zebic", "Cvitan", "Dujmovic",
        };

        static readonly string[] Trades =
        {
            "dock hand", "seamstress", "clerk", "fishmonger", "printer", "tram driver", "baker",
            "night porter", "book-keeper", "welder", "laundress", "cab driver", "cobbler", "nurse",
            "stevedore", "barber", "typist", "glazier", "cook", "watchman", "tailor", "carter",
            "shop girl", "millwright", "usher", "rag man", "chandler", "ferryman", "cooper", "sign painter",
        };

        /// Everybody in the district, deterministically. The same seed always
        /// produces the same city — which is what lets a save file store a seed
        /// and a handful of exceptions instead of ten thousand people.
        public static Population Generate(int count, int seed, IReadOnlyList<string> districts)
        {
            var pop = new Population();
            if (count <= 0 || districts == null || districts.Count == 0) return pop;

            var rng = new Random(seed);
            var used = new HashSet<string>();

            for (int i = 0; i < count; i++)
            {
                var district = districts[i % districts.Count];
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
                    HomeX = rng.Next(-40, 41),
                    HomeZ = rng.Next(-40, 41),
                    WorkX = rng.Next(-40, 41),
                    WorkZ = rng.Next(-40, 41),
                };
                if (night) { r.WorkFromHour = 20; r.WorkToHour = 4; }
                else { r.WorkFromHour = 7 + rng.Next(3); r.WorkToHour = 16 + rng.Next(4); }
                pop.Residents.Add(r);
                pop._byId[r.Id] = r;
            }
            return pop;
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
        public List<Resident> SetBands(Func<Resident, double> distanceTo, ISet<string> loadBearing)
        {
            var changed = new List<Resident>();
            if (distanceTo == null) return changed;

            // Load-bearing people are placed first and take their slots off the
            // top, so a crowded street can never evict the bookkeeper.
            var ordered = Residents
                .OrderByDescending(r => IsLoadBearing(r, loadBearing))
                .ThenBy(distanceTo)
                .ToList();

            int near = 0, mid = 0;
            foreach (var r in ordered)
            {
                Lod want;
                if (near < NearCap) { want = Lod.Near; near++; }
                else if (mid < MidCap) { want = Lod.Mid; mid++; }
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
}
