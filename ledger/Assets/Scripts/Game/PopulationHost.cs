using System.Collections.Generic;
using System.Linq;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The game-side half of population scale (roadmap M9, design doc §17 gap 3).
    ///
    /// The authored and generated cast — Lena, Rocco, the batch residents, the
    /// suppliers — are always present and are NOT part of this. This is the
    /// crowd on top of them: three thousand people who exist as records and
    /// become real only as the player's attention reaches them.
    ///
    /// Each band change does exactly one thing:
    ///   Far  -> Mid : they enter the gossip mill, and — decided once,
    ///                 deterministically, from the district's ambient reach —
    ///                 they either had heard the talk about the player or they
    ///                 had not. That decision never re-rolls.
    ///   Mid  -> Near: a walker appears, following their own home/work routine.
    ///   Near -> Mid : the walker is destroyed. Their mind stays in the mill.
    ///   Mid  -> Far : they leave the mill — but ONLY if they are carrying
    ///                 nothing. Somebody holding a rumor or a memory is kept,
    ///                 because the world must not forget things because the
    ///                 player walked around a corner.
    public partial class GameController
    {
        public Population Populace { get; private set; }
        public int PopulationSeed { get; private set; }
        public int PopulationCount { get; private set; }

        /// How many of the crowd may be walking at once. A frame-budget number,
        /// on top of the ~36 authored and generated walkers already in the world.
        /// The city, and how it divides. Kept in one place because the two
        /// share lists must stay the same length as the district list, and a
        /// save-rebuild that used a different split would quietly build a
        /// different city from the same seed.
        // Seven districts (M14), shares per the §7 characters: Fairview
        // HOUSES people and employs almost nobody; Downtown and Ironside are
        // the inverse; the Strip's workforce keeps night hours; Gullwing is
        // nearly empty both ways — that emptiness is its mechanic.
        public static readonly string[] Districts =
            { "the Hook", "Copper Row", "Ironside", "Downtown", "the Strip", "Fairview", "Gullwing" };
        public static readonly int[] HomeShares = { 30, 28, 4, 3, 6, 22, 7 };
        public static readonly int[] WorkShares = { 24, 22, 20, 16, 9, 3, 6 };

        // Set from MEASUREMENT, not from ambition (playtest 2026-07-28). At
        // 3000 residents there were 333 people standing within 34m of the bar
        // door: the caps were not thinning a crowd, they were choosing 28 out of a
        // mob, and every one of them spawned on top of the player. KCD2 carries
        // ~3.5k over square kilometres; this city is about a tenth of one.
        // 700 puts roughly a dozen people out of doors within earshot at
        // midday, which is a street rather than a demonstration.
        public const int CrowdWalkerCap = 12;
        public const int CrowdMillCap = 60;
        /// Re-banding is not free (it sorts the whole population), so it happens
        /// on a timer rather than a frame — the player cannot outrun three
        /// seconds of walking.
        public const float RebandSeconds = 3f;

        readonly Dictionary<string, NpcWalker> _crowdWalkers = new Dictionary<string, NpcWalker>();
        /// The crowd's live walker count, for the sim's budget gate (P5).
        public int CrowdWalkerCount => _crowdWalkers.Count;
        /// Every crowd body, by resident id — the street the gossip director
        /// makes audible and reactive (M15).
        public IEnumerable<KeyValuePair<string, NpcWalker>> CrowdBodies => _crowdWalkers;
        float _nextReband;
        /// The day the current talk about the player started circulating, for
        /// the ambient reach calculation. -1 when the street is quiet.
        int _talkStartedDay = -1;

        void BuildPopulation()
        {
            // The seed is the city. Fixed for now so every playthrough shares a
            // street; when new-game options exist this becomes a choice.
            PopulationSeed = 20260726;
            PopulationCount = 700;
            // Where people sleep, and where they spend the day. Ironside is the
            // reason these are two lists: it houses about one person in
            // fourteen and employs closer to one in three, so it is busy at
            // noon and all but empty after dark. That is what "places without
            // witnesses" has to mean if it is going to mean anything.
            Populace = Population.Generate(PopulationCount, PopulationSeed,
                Districts, HomeShares, WorkShares);
            Populace.NearCap = CrowdWalkerCap;
            Populace.MidCap = CrowdMillCap;
        }

        /// The ids that must never fall out of the simulation whatever the caps
        /// say: anyone who works for the player, supplies them, owes them, or is
        /// carrying talk about them.
        HashSet<string> LoadBearingIds()
        {
            var set = new HashSet<string>();
            var mill = _gossip != null ? _gossip.Mill : null;
            if (mill == null) return set;
            foreach (var r in Populace.Residents)
            {
                if (Empire.CrewOf(r.Name) != null) { set.Add(r.Id); continue; }
                var g = mill.Get(r.Id);
                if (g != null && (g.Rumors.Count > 0 || g.Leashed)) set.Add(r.Id);
            }
            return set;
        }

        void TickPopulation(Vector3 playerPos)
        {
            if (Populace == null || _gossip == null || _gossip.Mill == null) return;
            if (Time.time < _nextReband) return;
            _nextReband = Time.time + RebandSeconds;

            // Talk has to have started somewhere for the far band to have heard
            // anything. First loud day is day zero of its travel.
            double heat = CurrentHeat;
            if (heat > 0.15 && _talkStartedDay < 0) _talkStartedDay = Now.Day;
            else if (heat <= 0.05) _talkStartedDay = -1;
            double reach = _talkStartedDay < 0
                ? 0.0
                : Population.AmbientReach(heat, Now.Day - _talkStartedDay);

            // Only people who are actually OUT get bodies (playtest: the map
            // read as a crowd scene because everyone was on the pavement).
            var changed = Populace.SetBands(r => Distance(r, playerPos), LoadBearingIds(),
                r => Population.OutdoorsAt(r, Now.Hour));
            foreach (var r in changed) ApplyBand(r, reach);
        }

        /// Distance from the player to wherever this resident's routine has them
        /// right now. Cheap, and it means the crowd around you is the crowd that
        /// would actually be there at this hour.
        double Distance(Resident r, Vector3 playerPos)
        {
            bool working = Now.Hour >= r.WorkFromHour && Now.Hour < r.WorkToHour;
            float x = working ? r.WorkX : r.HomeX;
            float z = working ? r.WorkZ : r.HomeZ;
            float dx = x - playerPos.x, dz = z - playerPos.z;
            return Mathf.Sqrt(dx * dx + dz * dz);
        }

        /// Where a crowd member is, whether or not they have a body. The mid
        /// band has no walker, so without this they could carry talk and never
        /// pass it on — a person with no position is never near anyone, and the
        /// whole band would be a dead end.
        Vector3? CrowdPositionOf(string id)
        {
            if (_crowdWalkers.TryGetValue(id, out var w) && w != null) return w.transform.position;
            var r = Populace != null ? Populace.ById(id) : null;
            if (r == null || r.Band == Lod.Far) return null;
            bool working = Now.Hour >= r.WorkFromHour && Now.Hour < r.WorkToHour;
            return working ? new Vector3(r.WorkX, 0, r.WorkZ) : new Vector3(r.HomeX, 0, r.HomeZ);
        }

        void ApplyBand(Resident r, double ambientReach)
        {
            var mill = _gossip.Mill;
            switch (r.Band)
            {
                case Lod.Near:
                    EnsureInMill(r, mill, ambientReach);
                    EnsureWalker(r);
                    break;

                case Lod.Mid:
                    EnsureInMill(r, mill, ambientReach);
                    DespawnWalker(r);
                    break;

                case Lod.Far:
                    DespawnWalker(r);
                    // Forget REFUSES if they are carrying anything. If it
                    // refuses, they have real state and must never be demoted
                    // again — so mark them and put them back in the mid band.
                    if (!mill.Forget(r.Id)) { r.Known = true; r.Band = Lod.Mid; }
                    break;
            }
        }

        void EnsureInMill(Resident r, GossipMill mill, double ambientReach)
        {
            if (mill.Get(r.Id) != null) return;

            var g = new Gossiper(r.Id, r.Name, null, null, null, r.Circle, r.Greed, r.Nerve, r.Loyalty);
            // P5: the district's pulse, cashed in at promotion — where they
            // live has been HAPPENING to them while nobody rendered it.
            double unease = DistrictUnease(r.District);
            if (unease > 0.05)
            {
                var arrival = Ledger.Core.DistrictPulse.Arrival(unease);
                if (g.Suspicion.Value < arrival.suspicionFloor) g.Suspicion.Restore(arrival.suspicionFloor);
                g.Loyalty = System.Math.Clamp(g.Loyalty - arrival.loyaltyShave, 0, 1);
            }
            mill.Add(g);

            // Neighbours: a handful of deterministic ties so talk has somewhere
            // to go. Chosen by index so the same person always knows the same
            // people, and only among those currently simulated — a tie to
            // somebody who is a record would never fire anyway.
            LinkNeighbours(r, mill);

            // The statistical band's one answer, cashed in exactly once: did
            // THIS person already know? Decided by a stable hash, so leaving the
            // street and coming back finds the same neighbourhood.
            if (ambientReach > 0 && Population.HeardIt(r, ambientReach))
            {
                g.Rumors.Add(new Rumor
                {
                    Content = new Fact("player", "street_talk", "something"),
                    OriginId = r.Id,
                    Summary = "somebody has been saying things about the new owner of the bar on Hook Street",
                    // Second-hand and vague by construction: this is a person who
                    // heard it around, not somebody who saw anything.
                    Confidence = 0.3,
                    Hops = 2,
                    Sensitive = false,
                });
                r.Known = true;   // they are carrying something now
            }
        }

        void LinkNeighbours(Resident r, GossipMill mill)
        {
            var graph = _gossip.Graph;
            if (graph == null) return;
            int idx = r.Index;
            if (idx < 0 || idx >= Populace.Residents.Count) return;
            for (int step = 1; step <= 3; step++)
            {
                int j = (idx + step * 137) % Populace.Residents.Count;
                var other = Populace.Residents[j];
                if (other.Id == r.Id || mill.Get(other.Id) == null) continue;
                graph.Link(r.Id, other.Id, 0.3 + 0.1 * step);
            }
        }

        void EnsureWalker(Resident r)
        {
            if (_crowdWalkers.ContainsKey(r.Id)) return;
            var colour = Color.HSVToRGB((float)Population.StableFraction(r.Id), 0.22f, 0.45f);
            var walker = NpcWalker.Spawn(r.Name, colour, new[]
            {
                (new GameTime(0, r.WorkFromHour, 0), new Vector3(r.WorkX, 0, r.WorkZ)),
                (new GameTime(0, r.WorkToHour, 0), new Vector3(r.HomeX, 0, r.HomeZ)),
            });
            _crowdWalkers[r.Id] = walker;
            _npcs.Add(walker);
        }

        void DespawnWalker(Resident r)
        {
            if (!_crowdWalkers.TryGetValue(r.Id, out var walker)) return;
            _crowdWalkers.Remove(r.Id);
            _npcs.Remove(walker);
            if (walker != null) Destroy(walker.gameObject);
        }

        // ---- persistence ----

        /// CI seam: the sim needs to check the save is a seed and not a census,
        /// and the capture itself is private to the save path.
        public Dictionary<string, object> CapturePopulationForSim() => CapturePopulation();

        Dictionary<string, object> CapturePopulation() =>
            Populace != null ? Populace.Capture(PopulationCount, PopulationSeed)
                             : new Dictionary<string, object>();

        // P5: how much of each district the empire owns, recomputed at most
        // once per day — the input to the district pulse.
        readonly Dictionary<string, int> _ownedByDistrict = new Dictionary<string, int>();
        int _pulseDay = -1;

        double DistrictUnease(string districtName)
        {
            if (_pulseDay != Now.Day)
            {
                _pulseDay = Now.Day;
                _ownedByDistrict.Clear();
                foreach (var b in Empire.Businesses)
                {
                    if (!b.Owned) continue;
                    var place = HookMap.Get(b.PlaceId);
                    if (place == null) continue;
                    var d = Ledger.Core.StreetMap.DistrictAt(place.X, place.Z);
                    if (d == null) continue;
                    _ownedByDistrict[d] = (_ownedByDistrict.TryGetValue(d, out var n) ? n : 0) + 1;
                }
            }
            _ownedByDistrict.TryGetValue(districtName, out var owned);
            return Ledger.Core.DistrictPulse.Unease(owned, Economy.Prosperity);
        }

        void RestorePopulation(Dictionary<string, object> data)
        {
            if (Populace == null || data == null) return;
            // A save from a different seed is a different city; rebuild it
            // rather than mapping one street's people onto another's.
            int seed = MiniJson.GetInt(data, "seed");
            int count = MiniJson.GetInt(data, "count");
            if (seed != 0 && (seed != PopulationSeed || count != PopulationCount))
            {
                PopulationSeed = seed;
                PopulationCount = Mathf.Clamp(count, 0, 20000);
                Populace = Population.Generate(PopulationCount, PopulationSeed,
                    Districts, HomeShares, WorkShares);
                Populace.NearCap = CrowdWalkerCap;
                Populace.MidCap = CrowdMillCap;
            }
            foreach (var id in _crowdWalkers.Keys.ToList())
            {
                var r = Populace.ById(id);
                if (r != null) DespawnWalker(r);
            }
            Populace.RestoreKnown(data);
            _nextReband = 0f;   // re-band immediately against the restored world
        }
    }
}
