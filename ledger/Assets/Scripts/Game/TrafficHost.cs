using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The game-side half of traffic (roadmap M12).
    ///
    /// Core decides where every vehicle is; this builds bodies for them and
    /// moves those bodies. The split is the same one the rest of the project
    /// uses and it earns its keep here more than anywhere: the CI sim runs this
    /// for nine game-days on a machine with no graphics driver, and every rule
    /// that matters was already proven in CoreTests before a single cube existed.
    ///
    /// The one thing this layer decides for itself is what the player and the
    /// crowd look like TO the traffic: it hands Core a list of hazards each
    /// frame, and Core stops for them. A driver in this game does not run
    /// people over — see `streets-and-cars-spec.md` §5.
    public partial class GameController
    {
        public TrafficSim Traffic { get; private set; }

        /// How many vehicles the city carries.
        ///
        /// This said "sixteen blocks; a dozen or so reads as a working
        /// district without ever becoming a queue the player has to sit
        /// through". It was written when the game was one district. There are
        /// seven now, and the sentence stayed put while the city grew around
        /// it — the same way "nothing here pushes" outlived the step that
        /// pushes.
        ///
        /// FOURTEEN CARS IN A SEVEN-DISTRICT CITY IS TWO PER DISTRICT, and it
        /// shows: across twelve committed stills — four street views at noon
        /// and at night, three builds apart — not one vehicle has appeared in
        /// frame. Wide shots straight down a main road, empty. A city with two
        /// cars per district does not read as quiet, it reads as evacuated.
        ///
        /// RAISED ON MEASUREMENT, NOT ON TASTE. The run reports
        /// `trafficMs=0.994` at 14, so a vehicle costs 0.071ms of the traffic
        /// scope. The game-systems budget is 12ms and the last run used 5.96ms
        /// of it, so:
        ///
        ///     28 vehicles -> traffic 1.99ms, game total 6.96ms of 12ms
        ///     42 vehicles -> traffic 2.98ms, game total 7.95ms of 12ms
        ///
        /// Twenty-eight and not forty-two, for a reason that is about a
        /// different gate: `perfOk` requires the traffic scope's mean under
        /// 4ms, and 42 lands at ~2.98 — a 25% margin on a prediction, which is
        /// how the frame budget came to fail on runner noise in the first
        /// place. 28 doubles the density, keeps a 100% margin, and is one step
        /// of the same loop the sky is on: move it, look at the still, move it
        /// again. Four per district is not the destination.
        ///
        /// WHAT THIS DOES NOT ACCOUNT FOR is render cost, and that is stated
        /// rather than hidden: each vehicle is now a dozen-odd boxes plus four
        /// to six wheels, and CI software-rasterises with no GPU, so the
        /// residue outside the game scopes will grow and the sim will take
        /// longer. The frame gate is on the game's half deliberately, so this
        /// cannot fail it — the honest cost is wall-clock on the runner.
        ///
        /// And it finally puts the wheels from M17.7 in front of a camera,
        /// which twelve stills have not managed.
        public const int VehicleCount = 28;
        /// Hazards are gathered from whoever is closest, not from everybody — a
        /// walker forty metres away is not about to be run over.
        ///
        /// AND THE REASON THIS CARRIED WAS A COST NOBODY PAYS. It said the
        /// alternative was "scanning three thousand residents every frame", and
        /// `GatherHazards` has never done that: it walks `_npcs`, the WALKER
        /// list, which the crowd cap holds at about forty. The three thousand
        /// are records in `Population` and no loop here touches them.
        ///
        /// The bound is still right and the honest reason is a different one:
        /// what it saves is not the scan, it is the LIST. Every hazard handed
        /// to `TrafficSim` is tested against every vehicle on every step, so
        /// forty hazards against twenty-eight vehicles is the real product —
        /// and a radius keeps that product about the traffic near the player
        /// rather than about the size of the crowd.
        public const float HazardRange = 34f;

        readonly Dictionary<int, Transform> _vehicleBodies = new Dictionary<int, Transform>();
        /// Head, the junction it governs, and which axis it faces. Kept as a
        /// list rather than parsed back out of object names — junction ids
        /// contain an underscore, so name-splitting would have read "j1_1" as
        /// "j1" and quietly lit half the district off the wrong junction.
        struct SignalHead { public Renderer Lamp; public StreetNode Node; public bool NorthSouth; }
        readonly List<SignalHead> _signalHeads = new List<SignalHead>();
        MaterialPropertyBlock _mpb;
        int _trafficHour = -1;

        void BuildTraffic()
        {
            Traffic = new TrafficSim(seed: PopulationSeed);
            Traffic.Populate(VehicleCount);
            // HERE RATHER THAN IN `WorldBuilder`, because this is where the
            // route exists. `StreetFurniture.Build` runs during world
            // construction and has no sim; asking it to recompute the bus loop
            // from `StreetMap` would work today and be a second copy of a rule
            // that only one place owns.
            StreetFurniture.BuildTransit(Traffic);
            _mpb = new MaterialPropertyBlock();
            foreach (var v in Traffic.Vehicles) EnsureBody(v);

            // Your car, parked outside the bar. One car, always in the same
            // place, because a vehicle you have to go and find is an errand
            // rather than a convenience.
            //
            // WHERE it parks matters more than it looks. Your car is a hazard to
            // the AI whether you are in it or not — as it should be — so a car
            // left standing in a running lane is a permanent obstruction, and
            // Hook Street would be queued solid for the rest of the campaign.
            // So the spot is searched for rather than hardcoded: off the
            // carriageway, clear of every building, near the door.
            PlayerCar.Spawn(FindParkingNear(WorldBuilder.BarDoor), 0f);
            Debug.Log($"Traffic: {Traffic.Vehicles.Count} vehicles on {StreetMap.Edges.Count} streets");

            // THE WHEEL PROPORTIONS, PRINTED, because a still cannot settle
            // them. Twenty-eight vehicles finally put a car in frame and the
            // wheels look large against the body — but "looks large" off a
            // 1280x720 JPEG is exactly the reading that condemned three
            // perfectly good textures earlier tonight. The radius comes from
            // `hi * 0.20` clamped to [0.22, 0.55], and whether that is right
            // depends on numbers nothing has ever reported.
            //
            // A wheel should be roughly a third of a car's total height and
            // rather less of a lorry's. This line makes that checkable next
            // run instead of arguable now.
            var seen = new HashSet<string>();
            foreach (var v in Traffic.Vehicles)
            {
                if (v.Kind == null || !seen.Add(v.Kind.Id)) continue;
                float hi = (float)v.Kind.Height, len = (float)v.Kind.Length;
                float r = Mathf.Clamp(hi * 0.20f, 0.22f, 0.55f);
                Debug.Log($"Traffic: wheels {v.Kind.Id} len={len:0.00} hi={hi:0.00} "
                          + $"radius={r:0.000} diameter={r * 2f:0.000} "
                          + $"dia/hi={(hi > 0 ? r * 2f / hi : 0):0.00} "
                          + $"dia/len={(len > 0 ? r * 2f / len : 0):0.00}");
            }
        }

        /// How many vehicles have changed what they are this run, and how many
        /// of those bodies were actually rebuilt.
        ///
        /// KEPT AS A PAIR, and the second is the one that matters. Core can
        /// decide a van is now a patrol car and the street will go on showing
        /// a van for ever, because `_vehicleBodies` caches a body per id and
        /// nothing in `PlaceBody` ever asks whether the kind still matches.
        /// That is rule 6 in its purest form — a system built, tested, and
        /// connected to nothing — so the two numbers are printed side by side
        /// and a gap between them is the wiring being broken.
        public static int PatrolsRebalanced, PatrolBodiesRebuilt;

        /// Tell the sim how hard the detective is looking, then let it move
        /// parked cars between kinds.
        ///
        /// THE WEIGHT COMES FROM CORE AND THE STAGE COMES FROM THE GAME, which
        /// is the only split that lets the mapping be tested here at all:
        /// `TrafficSim.PatrolWeightFor` is a pure function of `Inquiry` with
        /// eight CoreTests on it, and this line is the whole of the Game-layer
        /// half. If it were a table in this file the only way to check it
        /// would be a Windows round trip.
        int RebalancePatrols()
        {
            if (Traffic == null) return 0;
            var stage = PoliceInquiry;
            Traffic.PatrolWeight = Ledger.Core.TrafficSim.PatrolWeightFor(stage);

            // AND WHERE THEY WORK, which is the half that reaches the screen.
            //
            // `01f4eeb` had all six patrol cars out under a manhunt and
            // `patrolInShotMean=0.10` — one frame in ten. Six cars spread over
            // seven districts is nothing anywhere, and the answer is not a
            // bigger weight, it is a BEAT: the district the player is standing
            // in, which is where the trouble is by definition.
            //
            // CLEARED WHEN NOBODY IS LOOKING, and that matters as much as
            // setting it. A beat that cannot be stood down would leave the
            // player's own district under patrol for the rest of the save
            // whatever they did — a consequence that never expires, which is
            // the exploit `Informing` refuses by name at the other end of this
            // same system.
            Traffic.PatrolFocusDistrict =
                stage != Inquiry.None && Player != null
                    ? (Ledger.Core.StreetMap.DistrictAt(
                           Player.transform.position.x,
                           Player.transform.position.z) ?? "")
                    : "";
            _patrolChanged.Clear();
            int changed = Traffic.Rebalance(_patrolChanged);
            // AND THE BODY HAS TO FOLLOW, or Core is right and the street is
            // wrong. Destroyed rather than edited: `EnsureBody` builds a whole
            // vehicle — kit mesh, wheels, lamps, the patrol car's roof beacon
            // — from the kind, and there is no half of that worth reproducing
            // here as a second implementation.
            foreach (var id in _patrolChanged)
            {
                if (!_vehicleBodies.TryGetValue(id, out var t)) continue;
                if (t != null) Destroy(t.gameObject);
                _vehicleBodies.Remove(id);
                PatrolBodiesRebuilt++;
            }
            foreach (var v in Traffic.Vehicles)
                if (_patrolChanged.Contains(v.Id)) EnsureBody(v);
            return changed;
        }
        readonly List<int> _patrolChanged = new List<int>();

        void TickTraffic(float step)
        {
            if (Traffic == null) return;
            using (Perf.Time("traffic"))
            {
                if (Now.Hour != _trafficHour)
                {
                    _trafficHour = Now.Hour;
                    Traffic.SetHour(_trafficHour);
                    // AND HOW MANY PATROL CARS THE STREET SHOULD BE CARRYING,
                    // once an hour, straight after the parking.
                    //
                    // Order matters and is the point: `SetHour` decides which
                    // vehicles are parked up, and `Rebalance` only ever
                    // converts a parked one — so a car changes what it is
                    // while nobody can see it, and is a patrol car by the time
                    // it drives out again. Any other order converts vehicles
                    // that are about to be on screen.
                    PatrolsRebalanced += RebalancePatrols();
                }
                GatherHazards();
                Traffic.Step(step);
                // PER PASS, NOT PER RUN. A lifetime total would answer "has any
                // vehicle ever stopped", which is yes and is useless; the peak
                // over passes is how many were showing red AT ONCE, and it is
                // taken beside `VehiclesDrawn` from the same loop so the two
                // cannot describe different moments — the two-maxima fault this
                // project found four of in one night.
                BrakeLampsLit = VehiclesDrawn = VehiclesOffRoad = 0;
                foreach (var v in Traffic.Vehicles) PlaceBody(v);
                if (BrakeLampsLit > BrakeLampsPeak) BrakeLampsPeak = BrakeLampsLit;
                // AND THE DENOMINATOR FROM THE SAME INSTANT, which is the
                // whole reason this is three lines rather than one. A peak of
                // vehicles off the road divided by a peak of vehicles drawn is
                // two different moments quoted as a fraction — the fault this
                // project found four instances of in one night. The count of
                // vehicles showing AT the worst frame is captured with it.
                if (VehiclesOffRoad > VehiclesOffRoadPeak)
                {
                    VehiclesOffRoadPeak = VehiclesOffRoad;
                    VehiclesAtOffRoadWorst = VehiclesDrawn;
                }
            }
            if (SimMode.Days == 0) HearTraffic();
            CheckCollisions();
        }

        /// The player hit somebody (roadmap M11 + M12, player decision
        /// 2026-07-27: collisions that hurt without killing).
        ///
        /// This is the only place in the game where the player can hurt somebody
        /// by accident, and that is what makes it interesting: there is no menu,
        /// no confirmation, and no way to claim you meant something else. You
        /// were driving, and now somebody is on the ground.
        void CheckCollisions()
        {
            var car = PlayerCar.Instance;
            if (Traffic == null || car == null || !car.Occupied) return;

            var p = car.transform.position;
            var hit = Traffic.Contact(p.x, p.z, Mathf.Abs(car.Speed),
                PlayerCar.Kind.Width / 2.0 + 0.2, PlayerCar.Kind.Length / 2.0 + 0.2);
            if (hit == null) return;
            Traffic.Strikes.Clear();

            var s = hit.Value;
            if (_struckRecently.TryGetValue(s.VictimId, out var lastDay) && lastDay == Now.Day) return;
            _struckRecently[s.VictimId] = Now.Day;

            // Force decides the injury, and NOTHING decides a death. A knock at
            // walking pace is a bruise; the top of an arcade speed range is a
            // broken bone and a very bad morning. That is the whole range.
            var kind = s.Force > 0.6 ? InjuryKind.Broken
                     : s.Force > 0.25 ? InjuryKind.Cut
                     : InjuryKind.Bruised;
            var injury = Harm.Inflict(s.VictimId, s.VictimName, kind, Now.Day,
                $"knocked down in the street by a car, and the car was being driven by {Me.Surname}");

            // The car takes the hit too — you do not drive away from this at
            // speed, which gives the player a beat to understand what happened
            // rather than leaving it behind at forty.
            car.Jolt();
            Audio.Ui("dread");

            var mill = _gossip != null ? _gossip.Mill : null;
            var victim = mill?.Get(s.VictimId);
            if (victim != null)
            {
                victim.Memory.Append(new MemoryEvent(Now, "observation", 1.0,
                    $"{Me.Surname} hit me with a car. I am {injury?.Look ?? "hurt"}. " +
                    "It was not on purpose. That is not the same as it being nothing."));
                victim.Loyalty = Mathf.Clamp01((float)(victim.Loyalty - 0.35));
                victim.Suspicion.Raise(0.15, "was knocked down in the street by that car");
                // Not a feud yet — an accident is not a war. But it is the kind
                // of thing that becomes one if it goes unanswered, so it is
                // recorded as an exchange with low heat and left to the player.
                Harm.Flare("player", Me.Surname, s.VictimId, s.VictimName, Now.Day, heat: 0.2);
            }

            // Everybody nearby saw it, and this is the one fact the coat cannot
            // soften: they did not see a figure, they saw a car and what it did.
            if (mill != null)
                foreach (var w in _npcs)
                {
                    if (w == null || w.GossipId == s.VictimId) continue;
                    if (Vector3.Distance(w.transform.position, p) > 14f) continue;
                    mill.Witness(w.DisplayName,
                        new Fact("player", $"struck_d{Now.Day}", s.VictimId),
                        $"{Me.Surname} put {s.VictimName} on the road with a car on Hook Street",
                        sensitive: true, now: Now, confidence: 0.95);
                }

            _ui?.Toast($"You hit {s.VictimName}. They are {injury?.Look ?? "hurt"}, and getting up slowly. " +
                       "Everyone on this street saw the car.", 12f);
        }

        readonly Dictionary<string, int> _struckRecently = new Dictionary<string, int>();

        /// The city sounds occupied. One engine bed for the whole district,
        /// tracking the nearest moving vehicle: a dozen looping sources would mix
        /// to roughly this, and what sells a street is that something is running
        /// nearby rather than the stereo placement of each individual car.
        void HearTraffic()
        {
            if (!Audio.Ready || _player == null) return;
            var at = _player.transform.position;
            const float earshot = 30f;
            float best = 0f, pitch = 1f;
            foreach (var v in Traffic.Vehicles)
            {
                if (v.Dormant) continue;
                if (v.Kind.EngineNote == "none") continue;      // a bicycle is silent
                float dx = (float)v.X - at.x, dz = (float)v.Z - at.z;
                float d = Mathf.Sqrt(dx * dx + dz * dz);
                if (d > earshot) continue;
                float speedFrac = Mathf.Clamp01((float)(v.Speed / v.Kind.TopSpeed));
                float loud = (1f - d / earshot) * (0.30f + 0.70f * speedFrac);
                if (loud <= best) continue;
                best = loud;
                // A lorry idles lower than a cab does.
                pitch = (v.Kind.Id == Ledger.Core.VehicleKinds.TruckId || v.Kind.Id == Ledger.Core.VehicleKinds.BusId ? 0.72f : 1.0f)
                        + speedFrac * 0.45f;
            }
            var mine = PlayerCar.Instance;
            if (mine != null && mine.Occupied)
            {
                // Your own engine wins: you are sitting on it.
                float own = 0.55f + 0.45f * Mathf.Clamp01(Mathf.Abs(mine.Speed) / PlayerCar.MaxSpeed);
                if (own > best) { best = own; pitch = 0.85f + Mathf.Abs(mine.Speed) / PlayerCar.MaxSpeed * 0.6f; }
            }
            Audio.Traffic(best, pitch);
        }

        /// Everybody a driver must not hit. The player always; the nearest
        /// walkers; and nothing further away than a driver could reach before
        /// the next gather.
        /// IS A VEHICLE STANDING IN THIS SHOT.
        ///
        /// The judgement camera has now been blocked by four different
        /// classes of thing and each was found by a human opening the frame:
        /// a wall (fixed with `PointClear`), a lamp column (fixed by stepping
        /// past the kerb), a walker (fixed by sliding along the street), and
        /// now a parked car — `SceneAudit` named it `cabin:1.93m@3.7`, which
        /// is a vehicle's glass cabin two metres from the lens.
        ///
        /// The slide only ever tested `NpcWalker.Live`. Vehicles were never
        /// in it, and the player's own car parks near the bar door where the
        /// player starts, so the one vehicle guaranteed to be near the camera
        /// was the one nothing looked for.
        ///
        /// MEASURED AGAINST THE RENDERER'S OWN BOUNDS rather than a radius
        /// somebody picked: a bus is 10.5m and a bike is 1.8m, so any single
        /// number would be wrong for one of them, and rule 2 forbids inventing
        /// it. `SqrDistance` to the world AABB is exact and needs no bound
        /// beyond the clearance the caller already uses for people.
        /// How many patrol cars are in THIS camera's frame right now.
        ///
        /// SIX EXIST AND THE PLAYER SEES ONE ARE DIFFERENT FACTS, which is the
        /// whole of rule 6 and the reason this counter exists rather than
        /// `patrolNow` being taken as the answer. `b71c71f` reported
        /// `patrolWant=6 patrolNow=6 patrolsChanged=5 patrolBodies=5` — every
        /// link in the chain firing — and not one of the six committed stills
        /// has a white car in it. Both of those can be true at once, and until
        /// something counts what is in frame there is no way to tell "the
        /// patrols are out and the camera was pointed elsewhere" from "the
        /// mechanism runs and nothing reaches the screen".
        ///
        /// Awake only: a dormant vehicle is hidden, so counting it would say
        /// the street is full of police at four in the morning when it is
        /// empty. Position rather than renderer bounds, matching how
        /// `streetBodies` asks the same question about people, so the two
        /// numbers are comparable.
        /// AND THE DENOMINATOR, WITHOUT WHICH THE PATROL COUNT IS A JUDGEMENT
        /// RATHER THAN A MEASUREMENT.
        ///
        /// The beat took `patrolInShotMean` from 0.10 to 0.20 — a real
        /// doubling — and 0.20 still sounds thin. But thin against WHAT? If
        /// the review cameras typically have two vehicles of any kind in
        /// frame, then one in five being a patrol car is a heavily policed
        /// street and the thing to fix is where the cameras point. If they
        /// typically have eight, it is thin and the beat needs more cars.
        /// Those are opposite conclusions from the same number, and nothing
        /// in the verdict could tell them apart — rule 3b, on a fraction
        /// whose numerator was built two builds ago.
        ///
        /// `all` counts every awake vehicle in the same frustum at the same
        /// instant, so the pair cannot be two different moments quoted as a
        /// ratio.
        public void VehiclesInShot(Camera eye, out int patrols, out int all)
        {
            patrols = all = 0;
            if (eye == null || Traffic == null) return;
            foreach (var v in Traffic.Vehicles)
            {
                if (v == null || v.Dormant || v.Kind == null) continue;
                var vp = eye.WorldToViewportPoint(
                    new Vector3((float)v.X, 0.6f, (float)v.Z));
                if (!(vp.z > 0f && vp.x >= 0f && vp.x <= 1f && vp.y >= 0f && vp.y <= 1f))
                    continue;
                all++;
                if (v.Kind.Id == Ledger.Core.VehicleKinds.PoliceId) patrols++;
            }
        }

        public bool AnyVehicleWithin(Vector3 at, float metres)
        {
            float m2 = metres * metres;
            foreach (var kv in _vehicleBodies)
            {
                var t = kv.Value;
                if (t == null) continue;
                foreach (var r in t.GetComponentsInChildren<Renderer>())
                    if (r != null && r.bounds.SqrDistance(at) < m2) return true;
            }
            var mine = PlayerCar.Instance;
            if (mine != null)
                foreach (var r in mine.GetComponentsInChildren<Renderer>())
                    if (r != null && r.bounds.SqrDistance(at) < m2) return true;
            return false;
        }

        void GatherHazards()
        {
            var list = Traffic.Hazards;
            list.Clear();
            Vector3 focus = _player != null ? _player.transform.position : Vector3.zero;
            if (_player != null)
                list.Add(new TrafficSim.Hazard { X = focus.x, Z = focus.z, R = 0.6, Id = "player" });

            // Your car is an obstacle to everybody else's, whether you are in it
            // or you left it in the road.
            var mine = PlayerCar.Instance;
            if (mine != null)
            {
                var mp = mine.transform.position;
                // Sized to the car itself, not generously: an inflated radius
                // reaches across the kerb and stops traffic in a lane the car is
                // not actually in.
                list.Add(new TrafficSim.Hazard { X = mp.x, Z = mp.z, R = 1.2, Id = Traffic.PlayerHazardId });
            }

            float range2 = HazardRange * HazardRange;
            for (int i = 0; i < _npcs.Count; i++)
            {
                var npc = _npcs[i];
                if (npc == null) continue;
                var p = npc.transform.position;
                float dx = p.x - focus.x, dz = p.z - focus.z;
                if (dx * dx + dz * dz > range2) continue;
                // Named, so a collision can report WHO rather than reporting
                // that a car hit a coordinate.
                list.Add(new TrafficSim.Hazard
                {
                    X = p.x, Z = p.z, R = 0.5,
                    Id = npc.DisplayName, Name = npc.DisplayName,
                });
            }
        }

        /// A spot to leave a car: not on a road a driver uses, not inside a
        /// building, and as close to the door as those two allow. Searched in
        /// rings so the answer is the nearest acceptable spot rather than the
        /// first one that happens to be listed.
        static Vector3 FindParkingNear(Vector3 door)
        {
            for (float radius = 4f; radius <= 16f; radius += 1.5f)
                for (int step = 0; step < 16; step++)
                {
                    float a = step * Mathf.PI * 2f / 16f;
                    var spot = new Vector3(door.x + Mathf.Cos(a) * radius, 0.05f,
                                           door.z + Mathf.Sin(a) * radius);
                    if (StreetMap.OnRoad(spot.x, spot.z, margin: 1.2)) continue;
                    if (!WorldBuilder.PointClear(spot, inflate: 2.0f)) continue;
                    return spot;
                }
            // Nowhere clear near the door: the crossing is always tarmac and
            // always somewhere, and a car in the road beats a car in a wall.
            return new Vector3(door.x + 6f, 0.05f, door.z);
        }

        // ---- bodies ----

        /// Which kit models may dress each vehicle kind, in preference
        /// order — tried until one resolves, so a name the kit turns out
        /// not to have costs nothing but a lookup. Several per kind on
        /// purpose: the per-vehicle offset into this list is what stops
        /// every car on the street being the same car.
        ///
        /// CONFIRMED AGAINST tools/props/listings.json, 16 Aug: every
        /// car_kit_ name below exists in the fetched Car Kit. The bus and
        /// the bicycle come from the OGA haul of 22 Aug instead (CC0,
        /// licence re-read at fetch time) — both packs ship a Bus.fbx and
        /// they share one prefab key, last write wins, either is a bus.
        /// FULL PREFAB KEYS since that haul: two kits supply vehicles now,
        /// so a baked car_kit_ prefix would make every other kit
        /// unreachable from here.
        ///
        /// `police` USED TO BE ON THE NEVER-REFERENCED LIST, with the karts
        /// and the race cars, under "wrong era, wrong town". That was a guess
        /// about a file nobody had opened, and it was wrong: the model is a
        /// plain saloon a fifth longer than the sedan, and its body maps to
        /// the WHITE region of the shared colormap (#cbcbde) where every other
        /// car maps to mid-slate. White saloon, slate stripe — the right car.
        /// The karts and race cars stay out, and so do `ambulance` and
        /// `firetruck`: both are slate in this palette, so neither reads as
        /// what it is without livery work nobody has done.
        static string[] KitCandidates(string kindId)
        {
            switch (kindId)
            {
                case Ledger.Core.VehicleKinds.PoliceId: return new[] { "car_kit_police" };
                // `taxi`, not "cab" — the id is `taxi` and only the NAME
                // is "cab". This branch was dead from the day it was
                // written and every cab in the city got a plain sedan.
                case Ledger.Core.VehicleKinds.TaxiId: return new[] { "car_kit_taxi", "car_kit_sedan" };
                case Ledger.Core.VehicleKinds.VanId:  return new[] { "car_kit_van", "car_kit_delivery" };
                case Ledger.Core.VehicleKinds.TruckId: return new[] { "car_kit_truck", "car_kit_delivery_flat", "car_kit_truck_flat" };
                // From the OGA haul — the Car Kit has neither. The school
                // bus stays out: yellow American, wrong town. The two
                // bicycle models are one with a square frame and one
                // without; either reads as a bike at street distance.
                case Ledger.Core.VehicleKinds.BusId:  return new[] { "oga_vehicles_bus" };
                case Ledger.Core.VehicleKinds.BikeId: return new[] { "oga_vehicles_bicycle", "oga_vehicles_squareframebicycle" };
                default:      return new[] { "car_kit_sedan", "car_kit_suv", "car_kit_hatchback_sports", "car_kit_sedan_sports" };
            }
        }

        void EnsureBody(Vehicle v)
        {
            if (_vehicleBodies.ContainsKey(v.Id)) return;
            var root = new GameObject($"Vehicle_{v.Id}_{v.Kind.Id}").transform;

            float len = (float)v.Kind.Length, wid = (float)v.Kind.Width, hi = (float)v.Kind.Height;
            var paint = PaintFor(v);

            // A KIT MESH, WHEN ONE HAS ARRIVED (max-polish order, 16 Aug).
            // The props-fetch job commits CC0 vehicle models; PropPrefab
            // makes them loadable; this prefers them and falls back to the
            // primitive construction below unchanged — a build with no
            // models is exactly the build we shipped yesterday. The mesh
            // replaces the BODY AND WHEELS only: the head and brake lamps
            // are still ours (they are the night read and a gate counts
            // them), and Core still owns motion and collision.
            //
            // Scaled by its longest horizontal axis to the kind's length,
            // rotated if that axis is X — a kit's forward convention is a
            // fact we learn from the first stills, not one to assume.
            GameObject kitBody = null;
            var candidates = KitCandidates(v.Kind.Id);
            for (int c = 0; c < candidates.Length && kitBody == null; c++)
                kitBody = AssetLibrary.TryInstantiateProp(
                    candidates[(v.Id + c) % candidates.Length],
                    Vector3.zero, Quaternion.identity);

            // WHICH VEHICLES ACTUALLY GOT A MESH, AND WHICH DID NOT.
            //
            // The comment above says a build with no kit models is exactly
            // the build we shipped before — which is the point of the
            // fallback and also the reason it needs counting. A silent
            // fallback is indistinguishable from a working pipeline from
            // anywhere outside this function, and `propsPlaced=822` cannot
            // settle it: that counts every kit prop in the world, lamps and
            // cones included, so cars could be primitives inside a large
            // healthy-looking total.
            //
            // Kept as a PAIR rather than a ratio, so the denominator is on
            // the same line as the numerator and nobody has to divide two
            // numbers that might have come from different moments.
            VehiclesBodied++;
            if (kitBody != null) VehiclesKitted++;
            else if (VehicleFallbackWhy.Length < 60)
                VehicleFallbackWhy += (VehicleFallbackWhy.Length > 0 ? "," : "") + v.Kind.Id;
            if (kitBody != null)
            {
                // REPAINTED INTO THE TOWN'S PALETTE. The kit's own texture is
                // holiday-brochure mint — the first stills showed every car
                // on the street wearing the same cheerful green. A dark
                // multiply over the palette texture keeps the kit's shading
                // and windows while the paint goes late-analog: navy, black,
                // burgundy, bottle, grey, stone — the wardrobe's vocabulary,
                // stable per vehicle. The cab is black, because a British
                // cab is a black cab.
                var paintMpb = new MaterialPropertyBlock();
                paintMpb.SetColor("_Color", KitPaint(v));
                foreach (var kr0 in kitBody.GetComponentsInChildren<Renderer>())
                    kr0.SetPropertyBlock(paintMpb);

                // THE PUSH BAR IS THE ONLY AMERICAN THING ABOUT THE PATROL CAR,
                // and it is one named child. The kit calls it `grill` and puts
                // it at the front — 100 x 51 x 25 units at z +130..155, which
                // is where the extra 55 units of the model's 310 come from.
                // Dropped before the bounds are taken, so the car scales to its
                // body rather than to its bumper.
                foreach (var t0 in kitBody.GetComponentsInChildren<Transform>())
                    if (t0 != kitBody.transform && t0.name.StartsWith("grill"))
                        DestroyImmediate(t0.gameObject);

                kitBody.transform.SetParent(root, false);

                // THE BOX, NOT JUST THE LENGTH — and lorries were the reason.
                //
                // This used to scale UNIFORMLY by the model's longest
                // horizontal axis, which is right if a kit's proportions match
                // ours and this kit's do not. Measured with
                // `tools/prop-dimensions.py`, every kit vehicle rendered
                // wider than the box the sim collides and gaps with:
                //
                //   car   2.47m wide against a declared 1.8  (+37%)
                //   van   2.95m            against 2.0        (+47%)
                //   truck 3.97m            against 2.4        (+65%)
                //
                // On an eight-metre avenue that is chunky and legal. On a
                // six-metre street the lane centres are 1.5m from the middle,
                // so a 3.97m lorry reaches 0.48m PAST the centreline and 0.48m
                // over the kerb — two of them passing overlap by most of a
                // metre. `vehiclesOffRoad=0` said none of this, and could not:
                // it measures `Kind.Width`, which is the box, and the box was
                // never what was too big.
                //
                // So each axis goes to its own dimension and the mesh ends up
                // exactly the vehicle the sim thinks it is.
                //
                // BOUNDS OVER EVERY RENDERER. The old line took
                // `GetComponentInChildren<Renderer>()` — the FIRST one, which
                // for `police` is a wheel, since the kit orders its parts
                // wheel, wheel, wheel, body, grill, wheel. It happened to
                // return a body for the models shipped so far and that is luck,
                // not a rule.
                var rends = kitBody.GetComponentsInChildren<Renderer>();
                if (rends.Length > 0)
                {
                    var bb = rends[0].bounds;
                    for (int r = 1; r < rends.Length; r++) bb.Encapsulate(rends[r].bounds);
                    var size = bb.size;
                    // A kit whose length runs along X is turned to face down Z.
                    // localScale is applied in the model's own axes, BEFORE
                    // that rotation, so the factors swap with it.
                    bool sideways = size.x > size.z;
                    if (sideways)
                        kitBody.transform.localRotation = Quaternion.Euler(0, 90f, 0);
                    float meshLen = Mathf.Max(size.x, size.z);
                    float meshWid = Mathf.Min(size.x, size.z);
                    float meshHi = size.y;
                    if (meshLen > 0.01f && meshWid > 0.01f && meshHi > 0.01f)
                    {
                        float sLen = len / meshLen, sWid = wid / meshWid, sHi = hi / meshHi;
                        kitBody.transform.localScale = sideways
                            ? new Vector3(sLen, sHi, sWid)
                            : new Vector3(sWid, sHi, sLen);

                        // AND THE WHEELS STAY ROUND. A wheel rolls in the plane
                        // of (length axis, up), so squashing height against
                        // length turns it into an ellipse — 30% out on a car,
                        // which is the one part of a vehicle an eye checks
                        // without being asked. Correcting the child's own Y by
                        // the ratio makes its effective height match its
                        // effective length again; it stays THINNER by `sWid`,
                        // which is right, because the car is narrower now.
                        // Multiplied rather than assigned: an imported child
                        // may already carry a scale of its own.
                        float round = sHi > 0.0001f ? sLen / sHi : 1f;
                        foreach (var t1 in kitBody.GetComponentsInChildren<Transform>())
                        {
                            if (t1 == kitBody.transform) continue;
                            if (!t1.name.StartsWith("wheel")) continue;
                            var s1 = t1.localScale;
                            s1.y *= round;
                            t1.localScale = s1;
                        }
                    }
                    // Grounded: after scale, rotation and the wheel correction
                    // the renderers know where their feet are; sit them on y=0.
                    // Re-read, because every one of those moved them.
                    var reread = kitBody.GetComponentsInChildren<Renderer>();
                    if (reread.Length > 0)
                    {
                        var gb = reread[0].bounds;
                        for (int r = 1; r < reread.Length; r++) gb.Encapsulate(reread[r].bounds);
                        kitBody.transform.localPosition = new Vector3(0, -gb.min.y, 0);
                    }
                }
                foreach (var col in kitBody.GetComponentsInChildren<Collider>())
                    Destroy(col);   // Core owns collision, same as the primitives
            }

            if (kitBody == null)
            switch (v.Kind.Id)
            {
                case Ledger.Core.VehicleKinds.BikeId:
                    // A CYCLIST, NOT TWO SLABS. Nine of the city's 28 vehicles
                    // are bicycles and every one is a primitive — the kit has
                    // no bicycle in it, all 50 of its models are already
                    // extracted, so this construction IS the bike until a
                    // different CC0 kit arrives. It was a 0.7 x 0.6 x 1.8 box
                    // for the frame with a single box sitting on it, which at
                    // street distance reads as a crate with a person on top.
                    //
                    // The wheels were already right (`Wheels` gives a bike two
                    // at 0.45m). What was missing is everything that says
                    // BICYCLE from twenty metres: a thin frame instead of a
                    // slab, a saddle and a fork, HANDLEBARS across the front —
                    // the one part that is unmistakable in silhouette — and a
                    // rider who leans, with legs and a head rather than a
                    // single upright block.
                    //
                    // Six small boxes where there were two, so nine bikes cost
                    // 54 primitives instead of 18. Against 822 props already
                    // placed that is not a number worth protecting, and it is
                    // the cheapest available step up for a third of the
                    // traffic — "best available, not first working".
                    Part(root, "frameBar", new Vector3(0, 0.62f, 0),
                         new Vector3(0.07f, 0.09f, len * 0.66f), paint);
                    Part(root, "seatTube", new Vector3(0, 0.78f, -len * 0.14f),
                         new Vector3(0.07f, 0.34f, 0.07f), paint);
                    Part(root, "saddle", new Vector3(0, 0.95f, -len * 0.17f),
                         new Vector3(0.13f, 0.06f, 0.26f), paint);
                    Part(root, "fork", new Vector3(0, 0.80f, len * 0.31f),
                         new Vector3(0.07f, 0.40f, 0.07f), paint);
                    Part(root, "bars", new Vector3(0, 1.00f, len * 0.30f),
                         new Vector3(0.52f, 0.05f, 0.05f), paint);
                    Part(root, "riderLegs", new Vector3(0, 0.72f, -0.02f),
                         new Vector3(0.30f, 0.50f, 0.24f), Coat());
                    Part(root, "riderTorso", new Vector3(0, 1.12f, len * 0.06f),
                         new Vector3(0.40f, 0.52f, 0.28f), Coat());
                    Part(root, "riderHead", new Vector3(0, 1.45f, len * 0.10f),
                         new Vector3(0.20f, 0.22f, 0.20f), Coat());
                    break;

                case Ledger.Core.VehicleKinds.BusId:
                    Part(root, "body", new Vector3(0, hi * 0.55f, 0), new Vector3(wid, hi * 0.8f, len), paint);
                    Part(root, "band", new Vector3(0, hi * 0.72f, 0), new Vector3(wid + 0.04f, hi * 0.22f, len * 0.92f),
                        AssetLibrary.Glass);
                    break;

                case Ledger.Core.VehicleKinds.TruckId:
                    Part(root, "cab", new Vector3(0, hi * 0.4f, len * 0.30f), new Vector3(wid, hi * 0.62f, len * 0.34f), paint);
                    Part(root, "load", new Vector3(0, hi * 0.52f, -len * 0.18f), new Vector3(wid, hi * 0.8f, len * 0.62f),
                        AssetLibrary.Wood);
                    break;

                case Ledger.Core.VehicleKinds.VanId:
                    Part(root, "body", new Vector3(0, hi * 0.5f, -len * 0.08f), new Vector3(wid, hi * 0.72f, len * 0.82f), paint);
                    Part(root, "nose", new Vector3(0, hi * 0.32f, len * 0.38f), new Vector3(wid * 0.95f, hi * 0.4f, len * 0.24f), paint);
                    break;

                default: // car, cab
                    Part(root, "body", new Vector3(0, 0.42f, 0), new Vector3(wid, 0.6f, len), paint);
                    Part(root, "cabin", new Vector3(0, 0.85f, -len * 0.06f), new Vector3(wid * 0.88f, 0.5f, len * 0.46f),
                        AssetLibrary.Glass);
                    break;
            }

            Wheels(root, v.Kind, len, wid, hi);

            if (v.Kind.Id != Ledger.Core.VehicleKinds.BikeId)
            {
                // Headlamps. Emissive at night through the same window material
                // the buildings use, so a car coming down an avenue after dark
                // is two lights before it is a shape — which is most of what
                // makes a street at night feel occupied.
                float nose = len / 2f - 0.1f;
                float lampY = v.Kind.Id == Ledger.Core.VehicleKinds.TruckId || v.Kind.Id == Ledger.Core.VehicleKinds.BusId ? hi * 0.35f : 0.45f;
                Lamp(root, "lampL", new Vector3(-wid * 0.32f, lampY, nose));
                Lamp(root, "lampR", new Vector3(wid * 0.32f, lampY, nose));

                // AND THE BACK OF IT, which is the half a street actually sees.
                //
                // Headlamps are two lights coming toward you and the note above
                // says why they matter. Every vehicle in this city has been
                // driving away from the player with nothing lit at all — and a
                // stopped car showing red is the one traffic image a noir
                // street is built out of.
                //
                // `Vehicle.Waiting` is what decides it, and this is its first
                // caller: it has been `Speed < 0.15` in Core, unit-tested and
                // reachable by nothing, since the day it was written. The
                // engine audio already fades with speed, so the sound of a
                // vehicle at rest was right; nothing had ever asked what a
                // vehicle at rest LOOKS like.
                //
                // Smaller and lower than the headlamps because a tail lamp is,
                // and because two equal pairs at both ends would read as a
                // vehicle facing both ways at once in fog.
                float tail = -len / 2f + 0.1f;
                Lamp(root, "brakeL", new Vector3(-wid * 0.30f, lampY * 0.85f, tail),
                     new Vector3(0.16f, 0.11f, 0.06f));
                Lamp(root, "brakeR", new Vector3(wid * 0.30f, lampY * 0.85f, tail),
                     new Vector3(0.16f, 0.11f, 0.06f));
            }

            // THE ROOF LAMP, AND IT IS WHAT MAKES A PATROL CAR ONE.
            //
            // The kit model has no light bar — checked part by part, it is a
            // body, four wheels and a front push bar we drop. So its whole
            // claim to being a police car is that it is white in a street of
            // slate saloons, and white is what a pale car looks like at noon
            // and what every car looks like under a street lamp.
            //
            // Two boxes on the roof: a dark plinth across the cabin and one
            // lamp on it, emissive through the same window material as the
            // headlamps, so it carries after dark exactly as they do. A single
            // blue lamp on a plinth is the British period shape — a full
            // American bar would undo the reason this model was allowed in.
            //
            // Built here rather than in the kit branch on purpose: it runs on
            // the primitive fallback too, so a build whose props did not
            // extract still puts a light on the roof instead of shipping an
            // ordinary car that the sim believes is the police.
            if (v.Kind.Id == Ledger.Core.VehicleKinds.PoliceId)
            {
                Part(root, "bar", new Vector3(0, hi + 0.03f, -len * 0.04f),
                     new Vector3(wid * 0.52f, 0.06f, 0.20f), AssetLibrary.Metal);
                Lamp(root, "beacon", new Vector3(0, hi + 0.10f, -len * 0.04f),
                     new Vector3(0.26f, 0.10f, 0.18f));
            }

            _vehicleBodies[v.Id] = root;
            PlaceBody(v);
        }

        Transform Part(Transform parent, string name, Vector3 local, Vector3 size, string material)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = local;
            go.transform.localScale = size;
            go.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(material);
            var col = go.GetComponent<Collider>();
            if (col != null) Destroy(col);   // Core owns collision; a physics body would fight it
            return go.transform;
        }

        /// A wheel, which every vehicle in this city has been driving without.
        ///
        /// THE ONE TELL THAT SURVIVES FOG. The traffic already has per-kind
        /// silhouettes — a truck's cab and load, a bus's window band, a car's
        /// cabin set back off the bonnet — and headlamps that carry it at
        /// night. It still read as boxes sliding down the road, because a box
        /// with no wheels is a box however well proportioned, and the eye finds
        /// the missing wheel before it finds anything else.
        ///
        /// Cheap in the way the art direction wants: Unity's cylinder is one
        /// shared built-in mesh, so four per vehicle costs four draws of
        /// geometry that already exists and no new asset at all.
        ///
        /// The cylinder's axis runs up its Y with radius 0.5 and height 2, so
        /// the scale below is (diameter, width/2, diameter) and the rotation
        /// lays that axis along X — across the car, which is the way an axle
        /// goes.
        void Wheel(Transform parent, string name, float x, float z, float radius, float width)
        {
            var t = Part(parent, name, new Vector3(x, radius, z),
                         new Vector3(radius * 2f, width * 0.5f, radius * 2f),
                         AssetLibrary.Asphalt);
            t.GetComponent<MeshFilter>().sharedMesh = WheelMesh();
            t.localRotation = Quaternion.Euler(0f, 0f, 90f);
        }

        /// Set once from a throwaway cylinder, because `Part` builds cubes and
        /// this is the only round thing in the traffic. `Mannequin` learned the
        /// same lesson: take the built-in mesh, share it, and never let a
        /// primitive per instance become a mesh per instance.
        static Mesh _wheelMesh;

        static Mesh WheelMesh()
        {
            if (_wheelMesh != null) return _wheelMesh;
            var probe = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            _wheelMesh = probe.GetComponent<MeshFilter>().sharedMesh;
            Destroy(probe);
            return _wheelMesh;
        }

        /// Where the axles sit, per kind. Derived from the kind's own
        /// dimensions rather than authored per vehicle, so a kind whose size
        /// changes keeps its wheels underneath it.
        void Wheels(Transform root, VehicleKind kind, float len, float wid, float hi)
        {
            float r = Mathf.Clamp(hi * 0.20f, 0.22f, 0.55f);
            float w = kind.Id == "bike" ? 0.10f : 0.20f;
            float axle = len * 0.32f;

            if (kind.Id == "bike")
            {
                // Two, in line, and slightly larger for their body — a bicycle
                // or a motorbike is mostly wheel.
                float br = Mathf.Clamp(hi * 0.28f, 0.24f, 0.45f);
                Wheel(root, "wheelF", 0f, len * 0.35f, br, w);
                Wheel(root, "wheelR", 0f, -len * 0.35f, br, w);
                return;
            }

            float side = wid * 0.5f;
            Wheel(root, "wheelFL", -side, axle, r, w);
            Wheel(root, "wheelFR", side, axle, r, w);
            Wheel(root, "wheelRL", -side, -axle, r, w);
            Wheel(root, "wheelRR", side, -axle, r, w);

            // A SECOND REAR AXLE ON THE HEAVY ONES, which is what actually
            // distinguishes a lorry from a long car at a glance.
            if (kind.Id == "truck" || kind.Id == "bus")
            {
                Wheel(root, "wheelRL2", -side, -axle + len * 0.14f, r, w);
                Wheel(root, "wheelRR2", side, -axle + len * 0.14f, r, w);
            }
        }

        void Lamp(Transform parent, string name, Vector3 local) =>
            Lamp(parent, name, local, new Vector3(0.22f, 0.16f, 0.08f));

        void Lamp(Transform parent, string name, Vector3 local, Vector3 size)
        {
            var t = Part(parent, name, local, size, AssetLibrary.Window);
            var r = t.GetComponent<Renderer>();
            WorldBuilder.RegisterNightLight(r);
        }

        /// How many vehicles were showing brake lights at once, at the worst,
        /// and how many were drawn at all beside it.
        ///
        /// THE DENOMINATOR, because `brakeLampsLit=0` reads as "the traffic
        /// never stops" and is equally consistent with the toggle never
        /// running — and this city's cabs demonstrably wait on ranks and its
        /// buses dwell at stops, so a genuine zero would itself be a finding.
        public static int BrakeLampsLit, BrakeLampsPeak, VehiclesDrawn;
        /// Vehicles whose centre is off every road a car uses, this pass and at
        /// worst — with the number DRAWN at that same worst pass, so the two can
        /// honestly be read as a fraction.
        public static int VehiclesOffRoad, VehiclesOffRoadPeak, VehiclesAtOffRoadWorst;

        /// HOW MANY VEHICLES WEAR A KIT MESH, AND OUT OF HOW MANY.
        /// Cumulative over the whole run — every body built, not a peak and
        /// not a per-frame reading — so they are printed on the done line
        /// where a lifetime count belongs, never on a shot line. Both, or
        /// neither: `VehiclesKitted` alone cannot tell a pipeline that
        /// failed from a street with no cars on it.
        public static int VehiclesKitted, VehiclesBodied;
        /// Which KINDS fell back to primitives, so a partial failure names
        /// itself instead of showing up as a number slightly below the
        /// denominator. Capped, and the cap is visible in the value.
        public static string VehicleFallbackWhy = "";
        /// WHO left the road, last seen: kind/id@x/z, the directed edge, the
        /// distance along it, junction occupancy and what blocked it. "none"
        /// until anything ever goes off-road, so a clean run says so.
        public static string OffRoadWorstDesc = "none";

        /// The kit-mesh paints, multiplied over the kit's palette texture.
        /// Dark on purpose: these are saloons on a wet street in a noir
        /// port, and the lamps are what glow. Values sit above the old
        /// tint-crush floor — the kit texture averages bright, so the
        /// products land near the asphalt-to-wardrobe band, not below it.
        /// PUBLIC because the parked cars (WorldBuilder) read the same
        /// table — one palette for every car in town, moving or not.
        /// They reach it as GameController.KitPaints: this file declares
        /// partial GameController, not a TrafficHost type.
        public static readonly Color[] KitPaints =
        {
            new Color(0.16f, 0.18f, 0.24f),   // navy
            new Color(0.12f, 0.12f, 0.13f),   // black
            new Color(0.34f, 0.16f, 0.17f),   // burgundy
            new Color(0.16f, 0.25f, 0.20f),   // bottle green
            new Color(0.38f, 0.39f, 0.41f),   // grey
            new Color(0.48f, 0.45f, 0.40f),   // stone
        };

        /// THE PATROL CAR IS THE ONE VEHICLE THE MULTIPLY MUST NOT TOUCH.
        ///
        /// Every colour in `KitPaints` is between 0.12 and 0.48, which is the
        /// point of them — the kit ships holiday-brochure mint and this town
        /// does not have any. Applied to `police` that arithmetic would take a
        /// #cbcbde body to about #3d3d43 and produce a dark saloon, which is
        /// the exact car it was brought in to not be. Near-white rather than
        /// white: 0.88 keeps it inside the palette's ceiling instead of being
        /// the brightest thing in the frame, and the model's own slate stripe
        /// survives because a multiply preserves the ratio between them.
        static readonly Color PatrolWhite = new Color(0.88f, 0.88f, 0.90f);

        static Color KitPaint(Vehicle v) =>
            v.Kind.Id == Ledger.Core.VehicleKinds.PoliceId ? PatrolWhite
            : v.Kind.Id == Ledger.Core.VehicleKinds.TaxiId ? KitPaints[1]
            : KitPaints[((v.Id % KitPaints.Length) + KitPaints.Length) % KitPaints.Length];

        /// A paint colour that is stable for a given vehicle — nobody wants the
        /// bus changing colour when the crowd re-bands.
        string PaintFor(Vehicle v)
        {
            switch (v.Kind.Id)
            {
                case Ledger.Core.VehicleKinds.BusId: return AssetLibrary.Metal;
                case Ledger.Core.VehicleKinds.TruckId: return AssetLibrary.Metal;
                case Ledger.Core.VehicleKinds.TaxiId: return AssetLibrary.Metal;
                case Ledger.Core.VehicleKinds.BikeId: return AssetLibrary.Metal;
                default: return v.Id % 2 == 0 ? AssetLibrary.Metal : AssetLibrary.Concrete;
            }
        }

        static string Coat() => AssetLibrary.Plaster;

        void PlaceBody(Vehicle v)
        {
            if (!_vehicleBodies.TryGetValue(v.Id, out var t) || t == null) return;
            // A dormant vehicle is parked up for the night — it is not stepped,
            // is not an obstacle, and is not drawn. Hiding it rather than moving
            // it means the street empties after midnight and refills at seven,
            // which is what a street does.
            bool shown = t.gameObject.activeSelf;
            if (shown == v.Dormant) t.gameObject.SetActive(!v.Dormant);
            if (v.Dormant) return;
            t.position = new Vector3((float)v.X, 0.05f, (float)v.Z);
            t.rotation = Quaternion.Euler(0, (float)v.Heading, 0);

            // IS IT ON A ROAD AT ALL?
            //
            // FROM A STILL, AND THE STILL WAS ONLY HALF RIGHT — which is why
            // this is a counter rather than a fix. `review_day5_noon` shows
            // what read as several vehicles across the pavement at odd angles.
            // The angles are impossible: the line above sets rotation from
            // heading about Y only, so a vehicle in this game cannot tilt, and
            // whatever is leaning in that frame is street furniture. A picture
            // is good evidence that something is wrong and poor evidence of
            // what — rule 4, third time today.
            //
            // What the picture CAN support is the position, and nothing has
            // ever checked it. `Traffic` steps vehicles along street edges, so
            // the expected answer is zero and a non-zero one means the stepper
            // leaves the carriageway somewhere — most likely at a junction,
            // where an edge ends and the next has not begun.
            //
            // THE MARGIN IS THE VEHICLE'S OWN HALF-WIDTH, not a tolerance
            // picked to make the number small: a car legitimately at the kerb
            // has its centre inside the road and its body over the edge, and
            // flagging that would be measuring the model rather than the fault.
            // A CAB ON A RANK IS NOT OFF THE ROAD, and the instrument is what
            // proved it: `offRoadWho=[taxi/17@32.2/18.9/edge:stop_ferry_stop-
            // j3_3/s:0.4/blk:stop]` — a taxi 0.4m onto the ferry-stop spur,
            // which is exactly where `TrafficSim.Ranks` sends it to wait.
            //
            // `OnRoad` walks DRIVEABLE edges only, and `Driveable => Kind !=
            // "lane"` — every place's spur, including both ranks, is a lane.
            // So the sim drives cabs onto rank spurs by design and the gate
            // reads that design as a fault. The number was measuring the
            // model, which is the thing a threshold must never do.
            //
            // NARROW ON PURPOSE: only a vehicle whose CURRENT edge touches a
            // rank or a bus stop it is entitled to use. A car that wanders
            // down somebody's alley still trips, which is the fault this
            // gate exists for.
            bool atOwnStop = Traffic != null
                && ((v.Kind.WaitsAtRanks && (Traffic.Ranks.Contains(v.FromId)
                                             || Traffic.Ranks.Contains(v.ToId)))
                    || (v.Kind.StopsAtStops && (Traffic.IsBusStop(v.FromId)
                                                || Traffic.IsBusStop(v.ToId))));
            if (!atOwnStop
                && !Ledger.Core.StreetMap.OnRoad(v.X, v.Z, v.Kind.Width * 0.5))
            {
                VehiclesOffRoad++;
                // NAME THE CULPRIT. offRoad went intermittent-1 on 16 Aug
                // (green four builds, then 1 in two of the next three) and a
                // count cannot be chased — it says a vehicle left the road
                // somewhere in nine days and nothing else. Kind, id, position
                // and the edge it should be on turn the next red into an
                // answer. Last-wins is fine: any culprit beats a bare count,
                // and offRoad has never exceeded 1.
                OffRoadWorstDesc = $"{v.Kind.Id}/{v.Id}@{v.X:0.0}/{v.Z:0.0}"
                    + $"/edge:{v.FromId ?? "none"}-{v.ToId ?? "none"}"
                    + $"/s:{v.S:0.0}/inJ:{v.InJunction ?? "no"}/blk:{v.BlockedBy ?? "no"}";
            }

            // BRAKE LIGHTS, off `Vehicle.Waiting`. Toggled by the RENDERER
            // rather than the GameObject: `WorldBuilder.RegisterNightLight`
            // holds the renderer to drive its emissive after dark, and
            // deactivating the object would leave that registry pointing at a
            // thing it can no longer light — the same class of fault as a
            // declutter holding a label somebody else destroyed.
            VehiclesDrawn++;
            bool lit = v.Waiting;
            if (lit) BrakeLampsLit++;
            SetLamp(t, "brakeL", lit);
            SetLamp(t, "brakeR", lit);
        }

        static void SetLamp(Transform body, string name, bool on)
        {
            var lamp = body.Find(name);
            if (lamp == null) return;
            var r = lamp.GetComponent<Renderer>();
            if (r != null && r.enabled != on) r.enabled = on;
        }

        // ---- signals ----

        /// The lights are built once and only ever recoloured; the phase itself
        /// is a pure function of the clock over in Core, so nothing here has to
        /// remember anything.
        void BuildSignalHeads()
        {
            foreach (var n in StreetMap.Nodes)
            {
                if (!Signals.HasLights(n)) continue;
                // One head per approach, set back on the corner it governs.
                for (int k = 0; k < 4; k++)
                {
                    float ox = k == 0 ? -1f : k == 1 ? 1f : 0f;
                    float oz = k == 2 ? -1f : k == 3 ? 1f : 0f;
                    float d = (float)StreetMap.AvenueWidth / 2f + 1.4f;
                    var pos = new Vector3((float)n.X + ox * d, 0, (float)n.Z + oz * d);

                    var post = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    post.name = $"Signal_{n.Id}_{k}";
                    post.transform.position = pos + new Vector3(0, 1.6f, 0);
                    post.transform.localScale = new Vector3(0.14f, 3.2f, 0.14f);
                    post.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Metal);
                    var pcol = post.GetComponent<Collider>();
                    if (pcol != null) Destroy(pcol);

                    var head = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    head.name = $"SignalHead_{n.Id}_{k}";
                    head.transform.position = pos + new Vector3(0, 3.2f, 0);
                    head.transform.localScale = new Vector3(0.34f, 0.8f, 0.34f);
                    var hr = head.GetComponent<Renderer>();
                    hr.sharedMaterial = AssetLibrary.Material(AssetLibrary.Window);
                    // The shared window material now carries the pane-grid
                    // emission mask; a signal head is a LAMP and must glow
                    // whole, not as four panes behind a cross. Same override
                    // as RegisterNightLight, and TickSignals reads the block
                    // before writing, so this survives every phase change.
                    var hmpb = new MaterialPropertyBlock();
                    hr.GetPropertyBlock(hmpb);
                    hmpb.SetTexture("_EmissionMap", Texture2D.whiteTexture);
                    hr.SetPropertyBlock(hmpb);
                    var hcol = head.GetComponent<Collider>();
                    if (hcol != null) Destroy(hcol);

                    head.transform.SetParent(post.transform, true);
                    _signalHeads.Add(new SignalHead
                    {
                        Lamp = head.GetComponent<Renderer>(),
                        Node = n,
                        NorthSouth = k >= 2,
                    });
                }
            }
        }

        static readonly Color GreenLamp = new Color(0.25f, 0.85f, 0.30f);
        static readonly Color AmberLamp = new Color(0.95f, 0.66f, 0.15f);
        static readonly Color RedLamp = new Color(0.85f, 0.20f, 0.18f);

        void TickSignals()
        {
            if (Traffic == null || _signalHeads.Count == 0) return;
            using (Perf.Time("signals"))
            {
                foreach (var head in _signalHeads)
                {
                    if (head.Lamp == null) continue;
                    var phase = Signals.Phase(head.Node, Traffic.Clock);
                    bool ns = head.NorthSouth;
                    Color c = RedLamp;
                    if (phase == (ns ? "ns-green" : "ew-green")) c = GreenLamp;
                    else if (phase == (ns ? "ns-amber" : "ew-amber")) c = AmberLamp;

                    head.Lamp.GetPropertyBlock(_mpb);
                    _mpb.SetColor("_Color", c * 0.6f);
                    _mpb.SetColor("_EmissionColor", c * 1.4f);
                    head.Lamp.SetPropertyBlock(_mpb);
                }
            }
        }

        // ---- what a witness saw ----

        /// The phrase for the vehicle the PLAYER arrived in, or null if they
        /// walked. Deliberately not "whatever vehicle happened to be nearby" —
        /// a lorry passing on the avenue is not something the player did, and a
        /// witness who reports it is lying to the player through the game.
        ///
        /// This is the consequence half of the car (spec §4): driving somewhere
        /// is faster and more memorable than walking there, and the coat does
        /// not hide a vehicle.
        public string VehicleSeenAt(Vector3 where, float within = 12f)
        {
            var car = PlayerCar.Instance;
            if (car != null)
            {
                var p = car.transform.position;
                float dx = p.x - where.x, dz = p.z - where.z;
                if (dx * dx + dz * dz <= within * within) return PlayerCar.Kind.Witness;
            }

            // AND ANY OTHER VEHICLE THAT HAPPENED TO BE STANDING THERE.
            //
            // This only ever looked at the player's OWN car, so arriving on
            // foot meant no witness ever mentioned a vehicle — even with a van
            // at the kerb. `TrafficSim.NearestTo` exists for exactly this and
            // has never been called; its own comment says it is "how a witness
            // comes to say 'somebody came in a car' instead of 'somebody was
            // about'", and every `VehicleKind` already carries the words to say
            // it with, because "a truck is not a bicycle".
            //
            // THE POINT IS THAT THIS CAN BE WRONG ABOUT YOU. A witness reports
            // the vehicle that was there, not the vehicle that was involved. If
            // a delivery van was at the kerb while you walked up, the street
            // now says a delivery van was there and the investigation has a
            // description to chase that has nothing to do with you. That is the
            // misattribution side of the moat — `Misattribute` sat at zero call
            // sites for the same reason, and a street that can only ever be
            // right about you is a street with no bluffs in it.
            var near = Traffic?.NearestTo(where.x, where.z, within);
            return near?.Kind?.Witness;
        }

        /// Get in, or get out. The car has to be in reach, and you cannot climb
        /// into one mid-conversation.
        void CheckDriving()
        {
            var car = PlayerCar.Instance;
            if (car == null || _player == null) return;
            if (!Input.GetKeyDown(GameSettings.Current.Key("Drive"))) return;

            if (car.Occupied) { car.GetOut(); _ui?.Toast("You get out and pocket the key."); return; }
            if (_player.InputLocked) return;
            if (!car.WithinReach(_player.transform.position)) return;
            car.GetIn(_player, _player.Eye);
            _ui?.Toast($"You get in. {GameSettings.Current.Key("Drive")} to get out again.");
        }
    }
}
