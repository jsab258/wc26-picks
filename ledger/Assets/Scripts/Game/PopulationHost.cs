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
        // MOVED TO CORE, AND KEPT REACHABLE FROM HERE. The table lived here and
        // was copied into `Recurrence` under a comment promising the copies were
        // asserted equal. They were not — there was no assertion anywhere in
        // that file, and two decisions were taken off the tool this afternoon.
        // One copy now, in `CityPlan`, which the engine-free tools link
        // directly; these forward so no call site had to change.
        public static string[] Districts => Ledger.Core.CityPlan.Districts;
        public static int[] HomeShares => Ledger.Core.CityPlan.HomeShares;
        public static int[] WorkShares => Ledger.Core.CityPlan.WorkShares;

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

        /// How many of the crowd are wearing each `Core/Wardrobe` band. Read by
        /// the sim verdict — see `EnsureWalker`.
        public static readonly Dictionary<string, int> WardrobeWorn = new Dictionary<string, int>();
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
            // CHECKED WHERE THE CITY IS BUILT, not only in a test. A district
            // appended to one array and not the others shifts every share after
            // it onto the wrong place, and the city that comes out is plausible
            // — right headcount, right names, wrong distribution — which is the
            // kind of wrong nothing downstream can notice.
            if (!Ledger.Core.CityPlan.Balanced)
                Debug.LogError("PopulationHost: CityPlan is unbalanced — districts and "
                               + "home/work shares disagree in length or do not total 100. "
                               + "The generated city will not be the designed one.");
            Populace = Population.Generate(PopulationCount, PopulationSeed,
                Districts, HomeShares, WorkShares);
            Populace.NearCap = CrowdWalkerCap;
            Populace.MidCap = CrowdMillCap;
            ApplyDetailToCrowd();
        }

        /// THE DETAIL SETTING'S CROWD HALF, which has never been applied.
        ///
        /// `Detail` already drives the light shafts, the shadow distance and
        /// the body detail distance — three settings, three Game callers. Its
        /// fourth, `CrowdFraction`, had none, so choosing Low turned off the
        /// shafts and left every body in the street. `CostIndex` even weights
        /// the crowd at 0.12 of the total, so the presets have been claiming a
        /// saving nothing delivered.
        ///
        /// PROTECTED BY DESIGN, and the model says so: Low keeps three
        /// quarters. Halving the crowd is the largest single frame-time win
        /// available and is the one thing that must not be taken, because the
        /// street IS the game. This applies the model's restraint rather than
        /// inventing its own.
        ///
        /// ON THE NEAR CAP ONLY. `MidCap` is the gossip mill's population —
        /// people who exist and talk without being drawn — and thinning that
        /// for a graphics setting would make the street FORGET things on a
        /// slower machine, which is pillar P5 broken by a quality preset.
        // NOT STATIC. `Populace` is an instance member of `GameController` and
        // this file is one of its partials, so a static method here cannot
        // reach it — CS0120, and the second type-resolution error in one hour
        // that ShapeCheck structurally cannot see. `static` was reflex: the
        // method looked like a pure settings-to-cap mapping, and the one thing
        // it touches is the instance's own population.
        public void ApplyDetailToCrowd()
        {
            if (Populace == null) return;
            double keep = Ledger.Core.Detail.CrowdFraction(
                Ledger.Core.Detail.Parse(GameSettings.Current.Detail));
            Populace.NearCap = System.Math.Max(1,
                (int)System.Math.Round(CrowdWalkerCap * keep));
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
                r => Population.OutdoorsAt(r, Now.Day, Now.Hour));
            foreach (var r in changed) ApplyBand(r, reach);
        }

        /// SPEND THE SKINNED-BODY BUDGET ON THE NEAREST, NOT ON THE FIRST.
        ///
        /// WHAT THIS REPLACES. `NpcWalker.Spawn` used to attach a real body to
        /// the first twelve walkers that asked and leave everybody else a
        /// mannequin for the rest of the run, so the twelve went by SPAWN ORDER
        /// — the woman standing in front of you could be a box while a skinned
        /// mesh was being drawn four districts away. The cap itself was earned:
        /// forty-four bodies took skinned vertices from 16,338 to 1,037,694 and
        /// the frame gate went red, and the geometry says that is real work
        /// rather than a GPU-less runner's noise. What was wrong was WHO got
        /// them.
        ///
        /// THE BAND IS `Population`'s, NOT A SECOND ONE. `NearMetres` and
        /// `BandSlack` already define "near the player" for the crowd, with
        /// hysteresis, and were set from measurement. Inventing a second
        /// distance here would be one idea with two implementations, which is
        /// this project's most repeated fault — and the two would then drift
        /// silently, so a walker could be near enough to talk to and too far
        /// for a face.
        ///
        /// ONCE A SECOND, NOT ONCE A FRAME. The decision is one distance per
        /// walker and costs nothing; the ACT is a prefab instantiate, and doing
        /// that on a frame boundary is how a fix for a frame budget becomes a
        /// frame budget problem.
        void TickBodyDetail(Vector3 playerPos)
        {
            if (Populace == null || _npcs.Count == 0) return;
            if (Time.time < _nextBodyLod) return;
            _nextBodyLod = Time.time + BodyLodSeconds;
            BodyLodPasses++;

            // IS THE SAME WALKER IN THIS LIST TWICE? Folded into a pass that
            // already walks it, once a second, so it costs a hash insert per
            // walker and answers the open half of the name-duplication finding:
            // a label offered six times in one rendered frame, when `Tick` has
            // exactly one caller and that caller is a single pass over this
            // list. There are eleven `_npcs.Add` sites and not one checks.
            _seenWalkers.Clear();
            WalkersListed = _npcs.Count;
            WalkersDuplicated = 0;
            WalkersHurtNow = 0;
            foreach (var n in _npcs)
            {
                if (n == null) continue;
                if (!_seenWalkers.Add(n)) WalkersDuplicated++;

                // AND WHETHER THEY ARE HURT, folded into the same pass for the
                // same reason: it is one dictionary-free scan of the injury
                // list per walker, once a second, and it is the only thing in
                // the game that can make anybody but the player limp.
                //
                // ONCE A SECOND RATHER THAN ONCE A DAY, and that is not
                // laziness about a cheaper trigger. Capability changes the
                // instant somebody is hit by a car or comes off worse in an
                // alley, not at midnight, and a limp that starts the following
                // morning is a consequence the player cannot connect to the
                // thing they just did. A second is under the reaction time this
                // project's own feel spec cares about.
                double cap = Harm.Capability(n.DisplayName, Now.Day);
                n.Capability = cap;
                if (cap < HurtEnoughToShow)
                {
                    WalkersHurtNow++;
                    if (cap < WalkerCapabilityWorst) WalkerCapabilityWorst = cap;
                    // NAMED, because a count of zero has two completely
                    // different causes — nobody in this run got hurt, or the
                    // lookup never matched anybody — and only a name can tell
                    // them apart. That distinction is the whole reason this
                    // wiring was missing for weeks without anything going red.
                    if (WalkersHurtEver.Count < 40) WalkersHurtEver.Add(n.DisplayName);
                }
            }

            _bodyRank.Clear();
            foreach (var n in _npcs)
            {
                if (n == null || !n.WantsRealBody) continue;
                float dx = n.transform.position.x - playerPos.x;
                float dz = n.transform.position.z - playerPos.z;
                _bodyRank.Add((n, dx * dx + dz * dz));
            }
            BodyLodEligible = _bodyRank.Count;
            if (_bodyRank.Count == 0) return;
            _bodyRank.Sort((a, b) => a.d2.CompareTo(b.d2));

            // SQUARED, AND THE SLACK GOES ON THE WALKER THAT ALREADY HAS ONE.
            // That is what makes the boundary sticky: somebody wearing a body
            // keeps it out to 40m, somebody without one has to come inside 34m
            // to earn it, so a walker hovering at the line does not trade a
            // prefab instantiate back and forth every pass.
            double near = Populace.NearMetres, slack = Populace.BandSlack;
            double keep = (near + slack) * (near + slack);
            near *= near;

            // AND THE SAME STICKINESS ON THE RANK, WHICH THE FIRST VERSION HAD
            // ONLY ON THE DISTANCE — measured, not suspected.
            //
            // That version put six metres of hysteresis on the band and none on
            // the CAP, and the run said what that costs: 485 passes produced
            // 1,486 grants and 1,474 revokes. Three swaps a second, for twelve
            // slots — the set churned almost completely every pass, because
            // with 43 eligible walkers the twelfth and thirteenth nearest trade
            // places constantly however sticky the band is. It landed as frame
            // cost rather than as anything visible: the population scope went
            // to 4.70ms and the frame gate stayed red.
            //
            // THE SLACK IS THE BAND'S OWN, AS A PROPORTION, rather than a new
            // number: `BandSlack` is 6 metres on a 34-metre band, so a walker
            // keeps what it has for about a sixth further out than it needed to
            // earn it. Applied to twelve slots that is two. This deliberately
            // lets up to fourteen bodies exist at once — the cost of the
            // hysteresis, bounded and stated, against a thrash that was
            // instantiating a prefab three times a second.
            //
            // NO DWELL TIME STILL. The counters say whether the rank slack was
            // enough, and a time constant invented on top of an untested one
            // would make it impossible to tell which fixed it.
            int slackRanks = (int)System.Math.Round(
                NpcWalker.RealBodyCap * (Populace.BandSlack / Populace.NearMetres));
            int spent = 0;
            int wanted = 0;
            foreach (var (n, d2) in _bodyRank)
            {
                bool has = n.HasRealBody;
                bool inBand = d2 <= (has ? keep : near);
                int limit = NpcWalker.RealBodyCap + (has ? slackRanks : 0);
                bool want = inBand && spent < limit;
                if (want) { spent++; wanted++; }
                n.SetRealBody(want);
            }
            BodyLodNear = wanted;
            BodyLodSlack = slackRanks;
        }

        float _nextBodyLod = -1f;
        /// A PASS A SECOND. Slower than the crowd's rebanding on purpose: that
        /// one moves who EXISTS and has to keep up with walking, this one moves
        /// how somebody is DRAWN and a second of being a mannequin while you
        /// approach is not something a player can see.
        const float BodyLodSeconds = 1f;
        readonly List<(NpcWalker n, float d2)> _bodyRank = new List<(NpcWalker, float)>();

        /// THE DENOMINATORS, because `bodyLodNear=0` on its own cannot tell a
        /// street with nobody on it from a pass that never ran. `Passes` says
        /// the pass ran, `Eligible` says there was anybody to consider, `Near`
        /// says how many of them were close enough and inside the budget.
        public static int BodyLodPasses, BodyLodEligible, BodyLodNear, BodyLodSlack;

        /// The tick list's length and how many of its entries are repeats.
        /// Read by the sim beside the name-duplication counters, because they
        /// are two views of the same suspicion.
        public static int WalkersListed, WalkersDuplicated;
        readonly HashSet<NpcWalker> _seenWalkers = new HashSet<NpcWalker>();

        /// WHO IS LIMPING, and it is a reading rather than a gate.
        ///
        /// NOW versus EVER, and both are needed for opposite reasons. `Now` is
        /// how many of the people currently on the tick list are hurt, so it
        /// can be read against `WalkersListed` from the same instant. `Ever` is
        /// the names, because zero-now and zero-ever mean different things: a
        /// street where nobody happens to be hurt right this second is normal,
        /// and a run where nobody was EVER hurt is a run that cannot say
        /// whether this wiring works at all. That is the corollary rule 5b
        /// picked up on 4 August — a probe needs a run in which the thing it
        /// asserts CAN happen — and the sim plants exactly that condition on
        /// day one when it puts a knife through Sam.
        ///
        /// BOUNDED AT FORTY NAMES so a run that hurts half the city cannot
        /// write a verdict line nothing can read. If it ever saturates, the
        /// count is the number to trust and this set is a sample.
        public static int WalkersHurtNow;
        public static double WalkerCapabilityWorst = 1.0;
        public static readonly SortedSet<string> WalkersHurtEver = new SortedSet<string>();

        /// The capability below which a body visibly limps — `Rig.Limp`'s own
        /// early return expressed the other way round, so the number that
        /// decides whether somebody is COUNTED as limping is the same number
        /// that decides whether they limp. Two copies of this would be one
        /// idea with two implementations, and one of them would eventually be
        /// the one nobody looked at.
        const double HurtEnoughToShow = 1.0 - Ledger.Core.Rig.LimpsAboveHurt;

        /// Distance from the player to wherever this resident's routine has them
        /// right now. Cheap, and it means the crowd around you is the crowd that
        /// would actually be there at this hour.
        double Distance(Resident r, Vector3 playerPos)
        {
            var at = WhereIs(r);
            float dx = at.x - playerPos.x, dz = at.z - playerPos.z;
            return Mathf.Sqrt(dx * dx + dz * dz);
        }

        /// WHERE A RESIDENT IS, in ONE place, because two answers is how the
        /// crowd defect survives a fix.
        ///
        /// This is the line that caused it: it used to return home-or-work
        /// unconditionally, and both are INSIDE BUILDINGS. The player walks on
        /// streets, so the near band could only ever hold the two or three
        /// people whose front doors happened to be within thirty-four metres.
        /// Seven hundred simulated residents were putting three bodies on the
        /// street — the CI density sampler measured 19 bodies within 20m and
        /// only 3 of them crowd; the other sixteen were the authored cast.
        ///
        /// It has to be shared, because band assignment and body placement
        /// both ask. Fixing only one would have moved people without changing
        /// who is near, or the reverse — and either way the street would have
        /// stayed empty while the code looked correct.
        Vector3 WhereIs(Resident r)
        {
            if (Population.OutdoorPosition(r, Now.Day, Now.Hour, out var ox, out var oz))
            {
                // Snapped to the network, because a straight line from home to
                // work runs through buildings. The streets already know where
                // a person can walk.
                if (StreetMap.NearestOnStreet(ox, oz, out var sx, out var sz, out _))
                    return new Vector3((float)sx, 0, (float)sz);
                return new Vector3((float)ox, 0, (float)oz);
            }
            bool working = Now.Hour >= r.WorkFromHour && Now.Hour < r.WorkToHour;
            return working ? new Vector3(r.WorkX, 0, r.WorkZ)
                           : new Vector3(r.HomeX, 0, r.HomeZ);
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
            return WhereIs(r);
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
                    Summary = "somebody has been saying things about the new landlord of the pub on Hook Street",
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
            // THE HUE USED TO RUN THE WHOLE WHEEL. A screenshot showed a street
            // in mint green and pale lilac against grey stone — see
            // `Core/Wardrobe`, which stocks charcoal, brown, olive, navy and
            // ox-blood and nothing else.
            double frac = Population.StableFraction(r.Id);
            Wardrobe.Dress(frac, out double wh, out double ws, out double wv);
            var colour = Color.HSVToRGB((float)wh, (float)ws, (float)wv);

            // TALLIED AS THEY ARE DRESSED. A wardrobe that has quietly
            // collapsed onto one band passes every per-colour check — each
            // charcoal coat is a perfectly legal charcoal coat — and produces a
            // street where everybody is wearing the same thing. The
            // distribution is the property, so the distribution is what the run
            // reports.
            string band = Wardrobe.BandOf(frac);
            WardrobeWorn[band] = WardrobeWorn.TryGetValue(band, out var wc) ? wc + 1 : 1;
            // CROWD, and this is the only place in the game that spawns any.
            var walker = NpcWalker.Spawn(r.Name, colour, new[]
            {
                // Their first waypoint is where they ARE, not where they
                // sleep — otherwise a body spawns beside you on the pavement
                // and immediately sets off for a bed across the district,
                // which is the crowd walking away from the player forever.
                (new GameTime(0, Now.Hour, 0), WhereIs(r)),
                (new GameTime(0, r.WorkFromHour, 0), new Vector3(r.WorkX, 0, r.WorkZ)),
                (new GameTime(0, r.WorkToHour, 0), new Vector3(r.HomeX, 0, r.HomeZ)),
            },
            // MANNEQUINS, DELIBERATELY. This is the anonymous crowd — bodies
            // that fill a street and are never spoken to — and a mannequin
            // reads perfectly well at the distance you ever see one. The named
            // cast gets skinned meshes because those are the people you talk to
            // and have to recognise again.
            //
            // It also bounds the cost to a set somebody chose. `CrowdWalkerCap`
            // already limits how many of these exist; leaving them as
            // mannequins means the number of skinned bodies is the cast size
            // rather than whatever the population happened to be that run.
            realBody: false, crowd: true);
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
