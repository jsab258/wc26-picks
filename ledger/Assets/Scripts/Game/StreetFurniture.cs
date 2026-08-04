using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Signs (roadmap M12, step 4).
    ///
    /// Traffic control the player can READ. The rules already exist in Core —
    /// lights at the four big crossings, stop signs everywhere else, lanes that
    /// are not through roads — but a rule the city obeys without telling you is
    /// indistinguishable from arbitrary behaviour. A car stopping at an empty
    /// junction looks like a bug until there is a sign there.
    ///
    /// Street names do more work than the signs do. An address is the unit
    /// people give directions in and gossip in, and the plates read from the
    /// same table as the witness lines, so the city cannot tell the player one
    /// name and a character another.
    public static class StreetFurniture
    {
        public static int SignCount { get; private set; }

        public static void Build()
        {
            SignCount = 0;
            foreach (var n in StreetMap.Nodes)
            {
                if (!n.IsJunction) continue;
                BuildNamePlates(n);
                if (!Signals.HasLights(n)) BuildStopSigns(n);
            }
            BuildLaneSigns();
            BuildOverheadCables();
        }

        /// How many cables got strung. Read by the sim, for the same reason
        /// `Dressed` is: "the street feels enclosed" has to be a count.
        public static int CableCount { get; private set; }

        /// CABLES ACROSS THE STREET — `Dressing.CableAt`, which has been on the
        /// reach ledger since the ledger was written.
        ///
        /// Its own comment says it: *"Overhead clutter is the cheapest thing
        /// there is for making a street feel ENCLOSED rather than like two rows
        /// of boxes with a gap, and nobody ever budgets for it."* The function
        /// was written, tested, entered on the debt ledger as "authored in
        /// Dressing and drawn nowhere", and left. `built is not running`, in the
        /// one system whose entire job is to stop the city reading as two rows
        /// of boxes with a gap — which is precisely how the review still reads.
        ///
        /// The span is the edge's own width, so `CableAt`'s 14m cutoff does the
        /// deciding: alleys and streets get cables, and a wide avenue does not,
        /// because a cable over a main road reads as a mistake rather than as a
        /// slum. Prosperity is the back-alley figure on a lane and the
        /// street-front figure otherwise — the same two constants the facades
        /// are dressed from, so a poor lane strings more than a good street.
        static void BuildOverheadCables()
        {
            CableCount = 0;
            foreach (var e in StreetMap.Edges)
            {
                var a = StreetMap.Node(e.A);
                var b = StreetMap.Node(e.B);
                if (a == null || b == null) continue;
                double dx = b.X - a.X, dz = b.Z - a.Z;
                double len = System.Math.Sqrt(dx * dx + dz * dz);
                if (len < 1e-3) continue;
                dx /= len; dz /= len;
                double prosperity = e.Kind == "lane" ? 0.15 : 0.55;

                // Every seven metres along, which is far enough apart that two
                // cables never read as a net and close enough that a short lane
                // still gets one.
                for (double s = 6.0; s < len - 6.0; s += 7.0)
                {
                    double x = a.X + dx * s, z = a.Z + dz * s;
                    if (!Dressing.CableAt(x, z, prosperity, e.Width)) continue;
                    Cable(x, z, dx, dz, e.Width);
                    CableCount++;
                }
            }
        }

        /// One cable, as two sagging segments.
        ///
        /// TWO AND NOT ONE, because a dead-straight line at six metres reads as
        /// scaffolding. Two segments meeting a third of a metre lower in the
        /// middle is the cheapest thing that reads as weight — a real catenary
        /// would be a mesh, and at this distance in fog nobody can tell the
        /// difference between a curve and one bend.
        static void Cable(double x, double z, double dx, double dz, double span)
        {
            // Across the street, not along it: the perpendicular.
            var across = new Vector3((float)-dz, 0, (float)dx);
            var mid = new Vector3((float)x, 0, (float)z);
            float half = (float)span * 0.5f + 0.6f;   // into the facade at each end
            const float high = 6.0f, sag = 0.35f;
            var left = mid - across * half + Vector3.up * high;
            var right = mid + across * half + Vector3.up * high;
            var low = mid + Vector3.up * (high - sag);
            Segment($"Cable_{x:0}_{z:0}_a", left, low);
            Segment($"Cable_{x:0}_{z:0}_b", low, right);
        }

        static void Segment(string name, Vector3 from, Vector3 to)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.position = (from + to) * 0.5f;
            go.transform.up = (to - from).normalized;
            go.transform.localScale = new Vector3(0.05f, (to - from).magnitude, 0.05f);
            go.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Metal);
            Strip(go.GetComponent<Collider>());
        }

        /// Two boards on one post at each junction, one per street, set on the
        /// corner where somebody arriving can actually read them.
        static void BuildNamePlates(StreetNode n)
        {
            if (!StreetMap.NamesAt(n, out var ns, out var ew)) return;
            float d = (float)StreetMap.AvenueWidth / 2f + 2.0f;
            var basePos = new Vector3((float)n.X - d, 0, (float)n.Z + d);

            Post($"NamePost_{n.Id}", basePos, 3.0f);
            Plate($"NamePlate_{n.Id}_ns", basePos + new Vector3(0, 2.75f, 0), ns, 90f);
            Plate($"NamePlate_{n.Id}_ew", basePos + new Vector3(0, 2.40f, 0), ew, 0f);
            SignCount += 2;
        }

        /// A stop sign on every approach that actually exists. The outer ring has
        /// three approaches, not four, and a sign facing empty ground is the kind
        /// of detail that quietly tells the player the world is generated.
        static void BuildStopSigns(StreetNode n)
        {
            foreach (var e in StreetMap.EdgesAt(n.Id))
            {
                if (!e.Driveable) continue;
                var other = StreetMap.Node(StreetMap.Other(e, n.Id));
                if (other == null) continue;

                // Set back down the approaching road, on the driver's right.
                float dx = (float)(other.X - n.X), dz = (float)(other.Z - n.Z);
                float len = Mathf.Sqrt(dx * dx + dz * dz);
                if (len < 0.001f) continue;
                dx /= len; dz /= len;
                float back = (float)StreetMap.AvenueWidth / 2f + 1.4f;
                float side = (float)e.Width / 2f + 1.2f;
                // Right of an inbound driver (travelling -d) is (-dz, dx).
                var at = new Vector3((float)n.X + dx * back - dz * side, 0,
                                     (float)n.Z + dz * back + dx * side);

                Post($"StopPost_{n.Id}_{other.Id}", at, 2.4f);
                var face = GameObject.CreatePrimitive(PrimitiveType.Cube);
                face.name = $"StopSign_{n.Id}_{other.Id}";
                face.transform.position = at + new Vector3(0, 2.2f, 0);
                face.transform.localScale = new Vector3(0.78f, 0.78f, 0.07f);
                // Turned on its point: at graybox scale a diamond reads as
                // "octagon" far better than a cube reads as anything.
                face.transform.rotation = Quaternion.Euler(0, Mathf.Atan2(dx, dz) * Mathf.Rad2Deg, 45f);
                face.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.BrickRed);
                Strip(face.GetComponent<Collider>());
                SignCount++;
                // No lettering on these. A red diamond on a post at a junction
                // already reads as "stop", and the alternative was a hundred and
                // forty-four TextMesh renderers — which do not batch — to say
                // something the shape says on its own. The street names get text
                // because a name cannot be inferred from a shape.
            }
        }

        /// Lanes are the connectors to doorways, not through roads. Traffic in
        /// Core already refuses to thread them; this is the sign that says so, so
        /// a player who walks up one understands what they are looking at.
        static void BuildLaneSigns()
        {
            foreach (var e in StreetMap.Edges)
            {
                if (e.Driveable) continue;
                var a = StreetMap.Node(e.A);
                var b = StreetMap.Node(e.B);
                if (a == null || b == null) continue;
                // The junction end is the end somebody could drive in from.
                var junction = a.IsJunction ? a : b.IsJunction ? b : null;
                var doorway = junction == a ? b : a;
                if (junction == null) continue;

                float dx = (float)(doorway.X - junction.X), dz = (float)(doorway.Z - junction.Z);
                float len = Mathf.Sqrt(dx * dx + dz * dz);
                if (len < 0.001f) continue;
                dx /= len; dz /= len;
                var at = new Vector3((float)junction.X + dx * 6f - dz * 2.4f, 0,
                                     (float)junction.Z + dz * 6f + dx * 2.4f);

                Post($"LanePost_{e.A}_{e.B}", at, 2.1f);
                var disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                disc.name = $"NoEntry_{e.A}_{e.B}";
                disc.transform.position = at + new Vector3(0, 1.95f, 0);
                disc.transform.localScale = new Vector3(0.62f, 0.05f, 0.62f);
                disc.transform.rotation = Quaternion.Euler(90f, Mathf.Atan2(dx, dz) * Mathf.Rad2Deg, 0);
                disc.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.BrickRed);
                Strip(disc.GetComponent<Collider>());
                SignCount++;
            }
        }

        /// Bus stops and cab ranks drawn, and the count.
        public static int TransitCount { get; private set; }

        /// THE BUS ALREADY STOPS; NOTHING SAYS WHERE.
        ///
        /// `TrafficSim.BusLoop` and `TrafficSim.Ranks` have been on the reach
        /// ledger since it was written, and BOTH REASONS WERE WRONG in the
        /// direction that wastes a day. `BusLoop` said "the bus route exists and
        /// no bus is drawn following it" — a bus IS spawned onto the loop by
        /// `Populate`, `RouteBusFrom` keeps it there, `IsBusStop` makes it dwell
        /// every third junction, and `TrafficHost` draws every vehicle by kind.
        /// The whole behaviour runs. `Ranks` had already been half-corrected on
        /// 4 August — taxis do wait on ranks — and its remaining note names the
        /// real gap in one clause: "nothing draws a rank, signs one".
        ///
        /// That is the same gap for both, and it is the interesting one. A bus
        /// that halts for eight seconds at an unmarked corner is a bug to
        /// anybody watching; the same halt beside a post with a sign on it is a
        /// bus route. `StreetFurniture` exists for exactly this argument and
        /// makes it in its own header — *"a rule the city obeys without telling
        /// you is indistinguishable from arbitrary behaviour. A car stopping at
        /// an empty junction looks like a bug until there is a sign there."*
        /// Written about stop signs, true of this, and nobody applied it.
        ///
        /// FROM THE SIM'S OWN ROUTE, NOT A SECOND COPY OF IT. The loop is
        /// derivable from `StreetMap` alone, so this could have recomputed it
        /// and been right today — and would be the fourth "one idea, two
        /// implementations" in this project, with the marker drifting off the
        /// route the first time either rule changed and nothing to report it.
        /// The sim is passed in and asked.
        public static void BuildTransit(TrafficSim sim)
        {
            TransitCount = 0;
            if (sim == null) return;

            foreach (var id in sim.BusLoop)
            {
                if (!sim.IsBusStop(id)) continue;
                var n = StreetMap.Node(id);
                if (n == null) continue;
                // OFF THE CARRIAGEWAY, on the same reasoning the bins are
                // pulled back to their walls: a post standing in a running lane
                // is a permanent obstruction to a sim that treats geometry as
                // real. Four metres out along the diagonal clears an avenue
                // junction's corner without needing a footway lookup that does
                // not exist.
                var at = new Vector3((float)n.X + 4f, 0, (float)n.Z + 4f);
                Post($"BusStop_{id}_post", at, 2.6f);
                Plate($"BusStop_{id}", at + new Vector3(0, 2.35f, 0), "BUS", 45f);
                TransitCount++;
            }

            foreach (var id in sim.Ranks)
            {
                var n = StreetMap.Node(id);
                if (n == null) continue;
                var at = new Vector3((float)n.X + 4f, 0, (float)n.Z - 4f);
                Post($"Rank_{id}_post", at, 2.6f);
                Plate($"Rank_{id}", at + new Vector3(0, 2.35f, 0), "TAXI", -45f);
                TransitCount++;
            }
        }

        // ---- pieces ----

        static void Post(string name, Vector3 at, float height)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.position = at + new Vector3(0, height / 2f, 0);
            go.transform.localScale = new Vector3(0.1f, height, 0.1f);
            go.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Metal);
            Strip(go.GetComponent<Collider>());
        }

        static void Plate(string name, Vector3 at, string text, float yaw)
        {
            var board = GameObject.CreatePrimitive(PrimitiveType.Cube);
            board.name = name;
            board.transform.position = at;
            board.transform.localScale = new Vector3(2.6f, 0.34f, 0.06f);
            board.transform.rotation = Quaternion.Euler(0, yaw, 0);
            board.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Plaster);
            Strip(board.GetComponent<Collider>());
            Label(name + "_text", at, text, yaw, 0.055f);
        }

        /// Text on a sign, double-sided — a plate you can only read from one side
        /// is worse than no plate, because you walk round it to find out.
        static void Label(string name, Vector3 at, string text, float yaw, float size)
        {
            foreach (var flip in new[] { 0f, 180f })
            {
                var go = new GameObject($"{name}_{flip:0}");
                go.transform.position = at;
                go.transform.rotation = Quaternion.Euler(0, yaw + flip, 0);
                go.transform.Translate(0, 0, -0.05f, Space.Self);
                var tm = go.AddComponent<TextMesh>();
                tm.text = text;
                tm.characterSize = size;
                tm.fontSize = 64;
                tm.anchor = TextAnchor.MiddleCenter;
                tm.alignment = TextAlignment.Center;
                tm.color = new Color(0.93f, 0.92f, 0.88f);
                // THE SECOND PLATE ONLY WORKS IF THE FIRST ONE HAS A BACK.
                // Both copies were drawing through the board and through each
                // other, so every sign in the city read as forward and
                // backward glyphs superimposed. `Hidden/LedgerText` culls the
                // reverse face and respects depth, which makes the plate
                // genuinely double-sided instead of doubly wrong.
                WorldText.Adopt(tm);
            }
        }

        static void Strip(Collider c)
        {
            if (c != null) Object.Destroy(c);
        }
    }
}
