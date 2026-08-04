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
        /// walker forty metres away is not about to be run over, and scanning
        /// three thousand residents every frame to discover that is exactly the
        /// kind of cost that gets baked in before anybody measures it.
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

        void TickTraffic(float step)
        {
            if (Traffic == null) return;
            using (Perf.Time("traffic"))
            {
                if (Now.Hour != _trafficHour)
                {
                    _trafficHour = Now.Hour;
                    Traffic.SetHour(_trafficHour);
                }
                GatherHazards();
                Traffic.Step(step);
                // PER PASS, NOT PER RUN. A lifetime total would answer "has any
                // vehicle ever stopped", which is yes and is useless; the peak
                // over passes is how many were showing red AT ONCE, and it is
                // taken beside `VehiclesDrawn` from the same loop so the two
                // cannot describe different moments — the two-maxima fault this
                // project found four of in one night.
                BrakeLampsLit = VehiclesDrawn = 0;
                foreach (var v in Traffic.Vehicles) PlaceBody(v);
                if (BrakeLampsLit > BrakeLampsPeak) BrakeLampsPeak = BrakeLampsLit;
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
                    if (w == null || w.DisplayName == s.VictimId) continue;
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
                pitch = (v.Kind.Id == "truck" || v.Kind.Id == "bus" ? 0.72f : 1.0f)
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

        void EnsureBody(Vehicle v)
        {
            if (_vehicleBodies.ContainsKey(v.Id)) return;
            var root = new GameObject($"Vehicle_{v.Id}_{v.Kind.Id}").transform;

            float len = (float)v.Kind.Length, wid = (float)v.Kind.Width, hi = (float)v.Kind.Height;
            var paint = PaintFor(v);

            switch (v.Kind.Id)
            {
                case "bike":
                    Part(root, "frame", new Vector3(0, hi * 0.55f, 0), new Vector3(wid, hi * 0.35f, len), paint);
                    Part(root, "rider", new Vector3(0, hi * 0.85f, -0.1f), new Vector3(0.45f, hi * 0.5f, 0.35f), Coat());
                    break;

                case "bus":
                    Part(root, "body", new Vector3(0, hi * 0.55f, 0), new Vector3(wid, hi * 0.8f, len), paint);
                    Part(root, "band", new Vector3(0, hi * 0.72f, 0), new Vector3(wid + 0.04f, hi * 0.22f, len * 0.92f),
                        AssetLibrary.Glass);
                    break;

                case "truck":
                    Part(root, "cab", new Vector3(0, hi * 0.4f, len * 0.30f), new Vector3(wid, hi * 0.62f, len * 0.34f), paint);
                    Part(root, "load", new Vector3(0, hi * 0.52f, -len * 0.18f), new Vector3(wid, hi * 0.8f, len * 0.62f),
                        AssetLibrary.Wood);
                    break;

                case "van":
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

            if (v.Kind.Id != "bike")
            {
                // Headlamps. Emissive at night through the same window material
                // the buildings use, so a car coming down an avenue after dark
                // is two lights before it is a shape — which is most of what
                // makes a street at night feel occupied.
                float nose = len / 2f - 0.1f;
                float lampY = v.Kind.Id == "truck" || v.Kind.Id == "bus" ? hi * 0.35f : 0.45f;
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

        /// A paint colour that is stable for a given vehicle — nobody wants the
        /// bus changing colour when the crowd re-bands.
        string PaintFor(Vehicle v)
        {
            switch (v.Kind.Id)
            {
                case "bus": return AssetLibrary.Metal;
                case "truck": return AssetLibrary.Metal;
                case "taxi": return AssetLibrary.Metal;
                case "bike": return AssetLibrary.Metal;
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
                    head.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Window);
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
