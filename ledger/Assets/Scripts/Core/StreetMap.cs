using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// The street network (roadmap M12, `streets-and-cars-spec.md`).
    ///
    /// The district had buildings and no streets. Geometry sat at all fifteen
    /// planned places and the only roads were the founding cross at x=0 and
    /// z=0, so twenty-two locations stood in open ground — which is exactly why
    /// the city read as a diorama rather than a place.
    ///
    /// This is the network as DATA, engine-free, which buys three things at
    /// once. The walkers can follow actual streets instead of the old "nearest
    /// point on the cross" hack. The cars have something to drive along that is
    /// not a physics guess. And CoreTests can prove the city is connected
    /// without opening Unity — because a city with an unreachable address is
    /// worse than a city with no streets, since the player will walk at it.

    public class StreetNode
    {
        public string Id;
        public double X, Z;
        /// Junctions are grid crossings; stops are the short lane ends outside
        /// a door. Traffic uses junctions; people use both.
        public bool IsJunction;

        public double DistanceTo(StreetNode o) => Math.Sqrt(Sq(X - o.X) + Sq(Z - o.Z));
        static double Sq(double v) => v * v;
        public override string ToString() => $"{Id}({X:0},{Z:0})";
    }

    public class StreetEdge
    {
        public string A, B;
        /// avenue (8m, traffic) | street (6m, the founding cross) | lane (4m,
        /// the connector to a door — nobody drives fast here).
        public string Kind = "avenue";
        public double Length;

        public double Width => Kind == "avenue" ? 8.0 : Kind == "street" ? 6.0 : 4.0;
        public bool Driveable => Kind != "lane";
    }

    public static class StreetMap
    {
        /// A REAL GRID, laid out the way a city is: streets first, blocks
        /// second, buildings filling the blocks. Two things forced this shape.
        ///
        /// First, a test caught the previous attempt running an avenue straight
        /// through a founding building. You do not fit streets around
        /// buildings; you fit buildings inside blocks.
        ///
        /// Second, and worse: the old district was a 90x90m ground slab. Real
        /// walkable blocks run 79m in Portland and 113m in Barcelona's
        /// Eixample, so THE ENTIRE CITY WAS ABOUT THE SIZE OF ONE CITY BLOCK.
        /// That is the actual reason it read as a diorama, and no amount of
        /// traffic on two roads would have fixed it.
        ///
        /// The fix is not to build Barcelona — games compress, because
        /// traversal time is gameplay time, and the research is consistent that
        /// DENSITY carries the feeling of size rather than area does. So:
        /// 26m spacing, 8m avenues, 18m of buildable interior per block. Five
        /// lines each way is sixteen blocks spanning ±52m, which is four times
        /// the old ground area with every block built on. The founding cross at
        /// x=0 and z=0 is two of the ten, so the bar and its street keep their
        /// coordinates exactly and nothing already authored moves.
        ///
        /// Chamfered junction corners are Barcelona's trick and they are nearly
        /// free: cutting the corner off each block turns a crossroads into a
        /// small plaza, opens the sightline diagonally, and is the single
        /// cheapest thing that makes a grid read as designed rather than as
        /// graph paper.
        public const double Spacing = 26.0;
        public const double AvenueWidth = 8.0;
        /// How much is cut off each block corner at a junction (Barcelona's
        /// chamfer). Purely visual, but it is the difference between a city and
        /// a spreadsheet.
        public const double Chamfer = 4.0;
        public static readonly double[] AvenuesX = { -52, -26, 0, 26, 52 };
        public static readonly double[] AvenuesZ = { -52, -26, 0, 26, 52 };

        /// What genuinely cannot move: the bar. It is hand-built, its door and
        /// counter are referenced by name all over the game, and Act I happens
        /// inside it. Every OTHER building is now generated to fill a block,
        /// which is the whole point — the seven hand-placed founding boxes were
        /// laid out when there were two roads, and three of them stood exactly
        /// where an avenue needs to be. Buildings fit inside blocks; streets do
        /// not detour around buildings.
        public static readonly (double X, double Z, double W, double D)[] BuiltMasses =
        {
            (-8, 8, 11, 11),   // the Hook Street bar
        };

        /// Does an avenue at this x (or z) cut through one of those?
        public static bool AvenueClear(double coord, bool northSouth, double width = AvenueWidth)
        {
            foreach (var m in BuiltMasses)
            {
                double c = northSouth ? m.X : m.Z;
                double half = (northSouth ? m.W : m.D) / 2.0;
                if (Math.Abs(coord - c) < half + width / 2.0) return false;
            }
            return true;
        }

        /// One city block: the ground between four streets, and the rectangle
        /// inside it that buildings may actually occupy.
        public class Block
        {
            public double MinX, MaxX, MinZ, MaxZ;      // kerb to kerb
            public double CentreX => (MinX + MaxX) / 2;
            public double CentreZ => (MinZ + MaxZ) / 2;
            public double Width => MaxX - MinX;
            public double Depth => MaxZ - MinZ;
            public bool Contains(double x, double z) =>
                x >= MinX && x <= MaxX && z >= MinZ && z <= MaxZ;
        }

        static List<Block> _blocks;
        public static List<Block> Blocks { get { Ensure(); return _blocks; } }

        /// The block a position falls inside, or null if it is on tarmac.
        public static Block BlockAt(double x, double z)
        {
            Ensure();
            return _blocks.FirstOrDefault(b => b.Contains(x, z));
        }

        static List<StreetNode> _nodes;
        static List<StreetEdge> _edges;
        static Dictionary<string, StreetNode> _byId;
        static Dictionary<string, List<StreetEdge>> _adjacency;

        public static List<StreetNode> Nodes { get { Ensure(); return _nodes; } }
        public static List<StreetEdge> Edges { get { Ensure(); return _edges; } }

        public static StreetNode Node(string id) { Ensure(); return _byId.TryGetValue(id, out var n) ? n : null; }

        /// Rebuilds from scratch. Tests call it; the game never needs to.
        public static void Rebuild() { _nodes = null; Ensure(); }

        static void Ensure()
        {
            if (_nodes != null) return;
            _nodes = new List<StreetNode>();
            _edges = new List<StreetEdge>();
            _byId = new Dictionary<string, StreetNode>();

            // 1. The grid. Twenty-five junctions, sixteen blocks.
            for (int i = 0; i < AvenuesX.Length; i++)
                for (int j = 0; j < AvenuesZ.Length; j++)
                    Add(new StreetNode
                    {
                        Id = $"j{i}_{j}",
                        X = AvenuesX[i],
                        Z = AvenuesZ[j],
                        IsJunction = true,
                    });

            // 2. The avenues between them. The founding cross keeps its own
            // class, because it is narrower and already built.
            for (int i = 0; i < AvenuesX.Length; i++)
                for (int j = 0; j + 1 < AvenuesZ.Length; j++)
                    Link($"j{i}_{j}", $"j{i}_{j + 1}", AvenuesX[i] == 0 ? "street" : "avenue");
            for (int j = 0; j < AvenuesZ.Length; j++)
                for (int i = 0; i + 1 < AvenuesX.Length; i++)
                    Link($"j{i}_{j}", $"j{i + 1}_{j}", AvenuesZ[j] == 0 ? "street" : "avenue");

            // 3. Every place on the map gets a lane to the nearest junction, so
            // it stops being a point in a field and becomes an address.
            foreach (var place in HookMap.Places)
            {
                var stop = new StreetNode
                {
                    Id = "stop_" + place.Id,
                    X = place.X,
                    Z = place.Z,
                    IsJunction = false,
                };
                Add(stop);
                var nearest = _nodes.Where(n => n.IsJunction).OrderBy(n => n.DistanceTo(stop)).First();
                Link(stop.Id, nearest.Id, "lane");
            }

            // 4. The blocks between the streets — the buildable ground.
            _blocks = new List<Block>();
            double half = AvenueWidth / 2.0;
            for (int i = 0; i + 1 < AvenuesX.Length; i++)
                for (int j = 0; j + 1 < AvenuesZ.Length; j++)
                    _blocks.Add(new Block
                    {
                        MinX = AvenuesX[i] + half,
                        MaxX = AvenuesX[i + 1] - half,
                        MinZ = AvenuesZ[j] + half,
                        MaxZ = AvenuesZ[j + 1] - half,
                    });

            _adjacency = new Dictionary<string, List<StreetEdge>>();
            foreach (var e in _edges)
            {
                Adj(e.A).Add(e);
                Adj(e.B).Add(e);
            }
        }

        static List<StreetEdge> Adj(string id)
        {
            if (!_adjacency.TryGetValue(id, out var list))
                _adjacency[id] = list = new List<StreetEdge>();
            return list;
        }

        static void Add(StreetNode n) { _nodes.Add(n); _byId[n.Id] = n; }

        static void Link(string a, string b, string kind)
        {
            var na = _byId[a];
            var nb = _byId[b];
            _edges.Add(new StreetEdge { A = a, B = b, Kind = kind, Length = na.DistanceTo(nb) });
        }

        // ---- queries ----

        public static StreetNode NearestNode(double x, double z, bool junctionsOnly = false)
        {
            Ensure();
            StreetNode best = null;
            double bestD = double.MaxValue;
            foreach (var n in _nodes)
            {
                if (junctionsOnly && !n.IsJunction) continue;
                double d = (n.X - x) * (n.X - x) + (n.Z - z) * (n.Z - z);
                if (d < bestD) { bestD = d; best = n; }
            }
            return best;
        }

        public static IEnumerable<StreetEdge> EdgesAt(string nodeId)
        {
            Ensure();
            return _adjacency.TryGetValue(nodeId, out var list) ? list : Enumerable.Empty<StreetEdge>();
        }

        public static string Other(StreetEdge e, string from) => e.A == from ? e.B : e.A;

        /// Shortest path by distance. Dijkstra rather than A* — the graph is
        /// fifty nodes, and a heuristic would be more code than it saves.
        /// Returns an empty list when there is no route, never null.
        public static List<StreetNode> Route(string fromId, string toId, bool driveableOnly = false)
        {
            Ensure();
            var result = new List<StreetNode>();
            if (!_byId.ContainsKey(fromId) || !_byId.ContainsKey(toId)) return result;
            if (fromId == toId) { result.Add(_byId[fromId]); return result; }

            var dist = new Dictionary<string, double>();
            var prev = new Dictionary<string, string>();
            var unvisited = new HashSet<string>();
            foreach (var n in _nodes) { dist[n.Id] = double.MaxValue; unvisited.Add(n.Id); }
            dist[fromId] = 0;

            while (unvisited.Count > 0)
            {
                string cur = null;
                double best = double.MaxValue;
                foreach (var id in unvisited)
                    if (dist[id] < best) { best = dist[id]; cur = id; }
                if (cur == null) break;              // the rest is unreachable
                if (cur == toId) break;
                unvisited.Remove(cur);

                foreach (var e in EdgesAt(cur))
                {
                    // A driving route may leave a lane at the start and enter one
                    // at the end — that is a car pulling out and parking — but it
                    // may not thread lanes in the middle.
                    if (driveableOnly && !e.Driveable && cur != fromId && Other(e, cur) != toId) continue;
                    var next = Other(e, cur);
                    if (!unvisited.Contains(next)) continue;
                    double alt = dist[cur] + e.Length;
                    if (alt < dist[next]) { dist[next] = alt; prev[next] = cur; }
                }
            }

            if (!prev.ContainsKey(toId) && fromId != toId) return result;
            var walk = new List<StreetNode>();
            for (var at = toId; at != null; at = prev.TryGetValue(at, out var p) ? p : null)
            {
                walk.Add(_byId[at]);
                if (at == fromId) break;
            }
            walk.Reverse();
            return walk[0].Id == fromId ? walk : result;
        }

        /// The closest point ON a street to an arbitrary position, and the edge
        /// it lies on. This is what a walker steers toward: people walk along
        /// streets, not across the blocks between them.
        public static bool NearestOnStreet(double x, double z, out double outX, out double outZ, out StreetEdge edge)
        {
            Ensure();
            outX = x; outZ = z; edge = null;
            double best = double.MaxValue;
            foreach (var e in _edges)
            {
                var a = _byId[e.A];
                var b = _byId[e.B];
                double dx = b.X - a.X, dz = b.Z - a.Z;
                double len2 = dx * dx + dz * dz;
                if (len2 < 1e-6) continue;
                double t = ((x - a.X) * dx + (z - a.Z) * dz) / len2;
                t = t < 0 ? 0 : t > 1 ? 1 : t;
                double px = a.X + t * dx, pz = a.Z + t * dz;
                double d = (px - x) * (px - x) + (pz - z) * (pz - z);
                if (d < best) { best = d; outX = px; outZ = pz; edge = e; }
            }
            return edge != null;
        }

        /// Whether a position is on tarmac of any kind, lanes included.
        public static bool OnStreet(double x, double z, double margin = 0)
        {
            if (!NearestOnStreet(x, z, out var px, out var pz, out var e)) return false;
            double d = Math.Sqrt((px - x) * (px - x) + (pz - z) * (pz - z));
            return d <= e.Width / 2.0 + margin;
        }

        /// Whether a position is on a road a CAR uses. Distinct from OnStreet
        /// because lanes cross block interiors to reach doors — a lane through
        /// a courtyard is correct, an avenue through one is not, and traffic
        /// must only ever be asked about the second kind.
        public static bool OnRoad(double x, double z, double margin = 0)
        {
            Ensure();
            foreach (var e in _edges)
            {
                if (!e.Driveable) continue;
                var a = _byId[e.A];
                var b = _byId[e.B];
                double dx = b.X - a.X, dz = b.Z - a.Z;
                double len2 = dx * dx + dz * dz;
                if (len2 < 1e-6) continue;
                double t = ((x - a.X) * dx + (z - a.Z) * dz) / len2;
                t = t < 0 ? 0 : t > 1 ? 1 : t;
                double px = a.X + t * dx, pz = a.Z + t * dz;
                double d = Math.Sqrt((px - x) * (px - x) + (pz - z) * (pz - z));
                if (d <= e.Width / 2.0 + margin) return true;
            }
            return false;
        }

        // ---- names ----

        /// Streets have names. This is not decoration: an address is the unit
        /// people give directions in and gossip in, and "they were seen on
        /// Copper Row" is a different sentence from "they were seen at
        /// (-26, 14)". The plates at the junctions and the witness lines read
        /// from the same table, so the city can never tell the player one name
        /// and a character another.
        static readonly string[] NamesNorthSouth =
        {
            "Tannery Row", "Copper Row", "Hook Street", "Anchor Walk", "Customs Way",
        };
        static readonly string[] NamesEastWest =
        {
            "Ironside Road", "Bakers Cross", "Quay Street", "Chapel Street", "Harbour Road",
        };

        /// The name of the avenue running along this coordinate, or null if no
        /// avenue runs there.
        public static string NameOf(double coord, bool northSouth)
        {
            var line = northSouth ? AvenuesX : AvenuesZ;
            var names = northSouth ? NamesNorthSouth : NamesEastWest;
            for (int i = 0; i < line.Length && i < names.Length; i++)
                if (Math.Abs(line[i] - coord) < 0.001) return names[i];
            return null;
        }

        /// What a person standing here would call where they are. Junctions read
        /// as a corner of two streets; anywhere else takes the nearest.
        public static string AddressOf(double x, double z)
        {
            Ensure();
            string ns = NameOf(x, true), ew = NameOf(z, false);
            if (ns != null && ew != null) return $"{ns} at {ew}";
            if (ns != null) return ns;
            if (ew != null) return ew;

            double bestD = double.MaxValue;
            string best = null;
            for (int i = 0; i < AvenuesX.Length; i++)
            {
                double d = Math.Abs(AvenuesX[i] - x);
                if (d < bestD) { bestD = d; best = NameOf(AvenuesX[i], true); }
            }
            for (int j = 0; j < AvenuesZ.Length; j++)
            {
                double d = Math.Abs(AvenuesZ[j] - z);
                if (d < bestD) { bestD = d; best = NameOf(AvenuesZ[j], false); }
            }
            return best;
        }

        /// The two streets that meet at a junction, for the plates on its posts.
        public static bool NamesAt(StreetNode n, out string northSouth, out string eastWest)
        {
            northSouth = eastWest = null;
            if (n == null || !n.IsJunction) return false;
            northSouth = NameOf(n.X, true);
            eastWest = NameOf(n.Z, false);
            return northSouth != null && eastWest != null;
        }

        /// Every junction reachable from every other, ignoring lanes. If this is
        /// ever false the city has an island in it and a driver will get stuck.
        public static bool FullyConnected()
        {
            Ensure();
            var junctions = _nodes.Where(n => n.IsJunction).Select(n => n.Id).ToList();
            if (junctions.Count == 0) return false;
            var seen = new HashSet<string> { junctions[0] };
            var queue = new Queue<string>();
            queue.Enqueue(junctions[0]);
            while (queue.Count > 0)
            {
                var cur = queue.Dequeue();
                foreach (var e in EdgesAt(cur))
                {
                    if (!e.Driveable) continue;
                    var next = Other(e, cur);
                    if (seen.Add(next)) queue.Enqueue(next);
                }
            }
            return junctions.All(seen.Contains);
        }
    }
}
