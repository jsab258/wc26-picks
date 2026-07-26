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

        /// How many vehicles the district carries. Sixteen blocks; a dozen or so
        /// reads as a working district without ever becoming a queue the player
        /// has to sit through.
        public const int VehicleCount = 14;
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

        void BuildTraffic()
        {
            Traffic = new TrafficSim(seed: PopulationSeed);
            Traffic.Populate(VehicleCount);
            _mpb = new MaterialPropertyBlock();
            foreach (var v in Traffic.Vehicles) EnsureBody(v);
            Debug.Log($"Traffic: {Traffic.Vehicles.Count} vehicles on {StreetMap.Edges.Count} streets");
        }

        void TickTraffic(float step)
        {
            if (Traffic == null) return;
            using (Perf.Time("traffic"))
            {
                GatherHazards();
                Traffic.Step(step);
                foreach (var v in Traffic.Vehicles) PlaceBody(v);
            }
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
                list.Add(new TrafficSim.Hazard { X = focus.x, Z = focus.z, R = 0.6 });

            float range2 = HazardRange * HazardRange;
            for (int i = 0; i < _npcs.Count; i++)
            {
                var npc = _npcs[i];
                if (npc == null) continue;
                var p = npc.transform.position;
                float dx = p.x - focus.x, dz = p.z - focus.z;
                if (dx * dx + dz * dz > range2) continue;
                list.Add(new TrafficSim.Hazard { X = p.x, Z = p.z, R = 0.5 });
            }
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

        void Lamp(Transform parent, string name, Vector3 local)
        {
            var t = Part(parent, name, local, new Vector3(0.22f, 0.16f, 0.08f), AssetLibrary.Window);
            var r = t.GetComponent<Renderer>();
            WorldBuilder.RegisterNightLight(r);
        }

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
            t.position = new Vector3((float)v.X, 0.05f, (float)v.Z);
            t.rotation = Quaternion.Euler(0, (float)v.Heading, 0);
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

        /// The phrase for whatever vehicle was closest to a place, or null if the
        /// answer is "nothing, they were on foot". This is how a witness comes to
        /// say "somebody came in a car" instead of "somebody was about" — and the
        /// coat does not hide a vehicle.
        public string VehicleSeenAt(Vector3 where, float within = 12f)
        {
            if (Traffic == null) return null;
            var v = Traffic.NearestTo(where.x, where.z, within);
            return v?.Kind.Witness;
        }
    }
}
