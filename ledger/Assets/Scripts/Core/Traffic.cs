using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// Traffic (roadmap M12, `streets-and-cars-spec.md` §4).
    ///
    /// Arcade, not simulation — this is a game about people, and the car is how
    /// the city sounds and moves rather than a driving model to master. But it
    /// is a MODEL, in Core, engine-free and deterministic, for the same reason
    /// the street network is: the properties that make traffic read as traffic
    /// (nobody overlaps, nobody drives through a red, nobody drives through a
    /// person, and nobody ever wedges the whole grid solid) are exactly the
    /// properties a test can hold, and none of them can be judged by looking at
    /// a screenshot.
    ///
    /// **Nobody dies under a car.** Flagged to the player as a decision rather
    /// than taken quietly, and answered by them on 2026-07-27: collisions that
    /// HURT but do not kill. Vehicular death would eat the gossip and
    /// investigation systems whole — every witness in the district would have
    /// exactly one thing to talk about for the rest of the campaign — while a
    /// knock-down is a hard fact with a vehicle attached, which is machinery
    /// this game already has. See `Strike` below and §5 of the spec.

    /// One class of vehicle. A data table rather than six subclasses, because
    /// the differences between a bus and a bike are numbers plus two flags, and
    /// the Unity layer wants to read them to build the right box.
    public class VehicleKind
    {
        public string Id, Name;
        public double Length, Width, Height;
        public double TopSpeed;        // m/s on an open avenue
        public double Accel, Brake;    // m/s^2
        public double Gap;             // bumper gap kept at rest
        public bool StopsAtStops;      // buses dwell at bus stops
        public bool WaitsAtRanks;      // taxis idle at the ferry stop and the cab rank
        public bool UsesLanes;         // bikes thread the lanes; a bus does not
        public double Rarity;          // relative weight in ordinary traffic
        /// How a witness names it. "somebody came in a car" is a better rumor
        /// than "somebody was about", and a truck is not a bicycle.
        public string Witness;
        /// Sound hint for the Unity layer — no audio decisions in Core.
        public string EngineNote;
    }

    public static class VehicleKinds
    {
        /// THE IDS AS CONSTANTS, so the Game layer can switch on them
        /// instead of retyping the string.
        ///
        /// `TrafficHost` matched `Kind.Id == "cab"` in TWO places — the kit
        /// model lookup and the paint — and no vehicle has ever had that id;
        /// this one is `taxi` and its NAME is "cab". Both branches were dead
        /// from the day they were written, so every taxi in the city has been
        /// getting a generic sedan mesh in a hashed colour, under a comment
        /// reading "the cab is black, because a British cab is a black cab".
        /// One idea, two implementations, both wrong the same way, and a
        /// comment asserting behaviour that never once happened.
        ///
        /// A `const` can appear in a `case` label, which is the whole point:
        /// the compiler now rejects the typo that a string literal accepted
        /// silently. Found by `vehiclesKitted=18/28` — the counter added to
        /// answer a different question entirely.
        public const string CarId = "car";
        public const string VanId = "van";
        public const string TruckId = "truck";
        public const string BusId = "bus";
        public const string TaxiId = "taxi";
        public const string BikeId = "bike";
        public const string PoliceId = "police";

        public static readonly VehicleKind Car = new VehicleKind
        {
            Id = CarId, Name = "car", Length = 4.2, Width = 1.8, Height = 1.5,
            TopSpeed = 11.0, Accel = 2.6, Brake = 5.5, Gap = 1.6, Rarity = 5,
            Witness = "a car", EngineNote = "car",
        };
        public static readonly VehicleKind Van = new VehicleKind
        {
            Id = VanId, Name = "delivery van", Length = 5.4, Width = 2.0, Height = 2.3,
            TopSpeed = 9.5, Accel = 2.0, Brake = 4.8, Gap = 1.8, Rarity = 3,
            Witness = "a delivery van", EngineNote = "van",
        };
        public static readonly VehicleKind Truck = new VehicleKind
        {
            Id = TruckId, Name = "lorry", Length = 7.8, Width = 2.4, Height = 3.0,
            TopSpeed = 8.0, Accel = 1.3, Brake = 4.0, Gap = 2.4, Rarity = 2,
            Witness = "a lorry", EngineNote = "truck",
        };
        public static readonly VehicleKind Bus = new VehicleKind
        {
            Id = BusId, Name = "bus", Length = 10.5, Width = 2.5, Height = 3.2,
            TopSpeed = 8.5, Accel = 1.2, Brake = 4.0, Gap = 2.6, Rarity = 1,
            StopsAtStops = true, Witness = "the bus", EngineNote = "bus",
        };
        public static readonly VehicleKind Taxi = new VehicleKind
        {
            Id = TaxiId, Name = "cab", Length = 4.4, Width = 1.8, Height = 1.6,
            TopSpeed = 11.5, Accel = 2.9, Brake = 5.5, Gap = 1.5, Rarity = 3,
            WaitsAtRanks = true, Witness = "a cab", EngineNote = "car",
        };
        public static readonly VehicleKind Bike = new VehicleKind
        {
            Id = BikeId, Name = "bicycle", Length = 1.8, Width = 0.7, Height = 1.7,
            TopSpeed = 5.5, Accel = 1.6, Brake = 3.5, Gap = 1.0, Rarity = 4,
            UsesLanes = true, Witness = "a bicycle", EngineNote = "none",
        };

        /// A PATROL CAR, AND IT IS IN HERE BECAUSE THE MODEL IS WHITE.
        ///
        /// The kit's `police` sat unused under a comment reading "wrong era,
        /// wrong town", which was a guess about a file nobody had opened. Read
        /// properly it is a 150 x 130 x 290 saloon — a fifth longer than the
        /// kit's sedan, the same width and height — and sampling the shared
        /// colormap at the body's own UVs gives #cbcbde, near-white, where
        /// every other car in the kit maps to mid-slate #6b6d82. A white
        /// saloon with a slate stripe is exactly the area car this town and
        /// this decade had. The one wrong note is a separate front push-bar
        /// mesh the kit calls `grill`, and the Game layer drops that child by
        /// name.
        ///
        /// LONGER AND FASTER THAN A CAR, because it is a big saloon and it is
        /// the only vehicle on this street with a reason to hurry.
        ///
        /// `Witness` is the part that earns its place. Every other kind here
        /// gives a witness a noun; this one gives them "a police car", which
        /// is the only vehicle in the catalogue whose PRESENCE is information.
        /// Rarity 1 — the same as the bus — so it is a thing you notice rather
        /// than a thing you see.
        public static readonly VehicleKind Police = new VehicleKind
        {
            Id = PoliceId, Name = "police car", Length = 4.8, Width = 1.8, Height = 1.5,
            TopSpeed = 12.5, Accel = 3.0, Brake = 6.0, Gap = 1.6, Rarity = 1,
            Witness = "a police car", EngineNote = "car",
        };

        public static readonly VehicleKind[] All = { Car, Van, Truck, Bus, Taxi, Bike, Police };

        public static VehicleKind ById(string id)
        {
            foreach (var k in All) if (k.Id == id) return k;
            return null;
        }
    }

    /// Traffic lights, as a pure function of the clock.
    ///
    /// No state machine, no per-junction ticking: the phase is derived from the
    /// time, so a light cannot drift, cannot desynchronise from its own render,
    /// and survives a save/load without being serialised at all.
    ///
    /// Amber is honest but simple — a vehicle may only ENTER on green, and one
    /// already inside the junction always clears it. So amber is the interval in
    /// which the junction empties, which is what amber is for.
    public static class Signals
    {
        public const double GreenSeconds = 11.0;
        public const double AmberSeconds = 2.0;
        public const double AllRedSeconds = 1.0;
        public const double HalfCycle = GreenSeconds + AmberSeconds + AllRedSeconds;
        public const double Cycle = HalfCycle * 2;

        /// Lights go where the two big roads cross: the four junctions where an
        /// avenue meets an avenue in the interior of the grid. The founding
        /// cross (x=0, z=0) is a narrower old street and keeps its give-way, and
        /// the outer ring gets stop signs — a light on the edge of town with
        /// nothing crossing it is set dressing that costs the player time.
        public static bool HasLights(StreetNode n)
        {
            if (n == null || !n.IsJunction) return false;
            // NOT ON THE OUTER RING, ASKED OF THE MAP. This was
            // `Interior(x) && Interior(z)` against a hardcoded 52.0 — the
            // Hook's outermost avenue back when the Hook was the whole city.
            // The topology stretch moved that line to 111.8 and the constant
            // would have switched off every light in the game while looking
            // like a rule about junctions.
            return !StreetMap.OnOuterRing(n) && n.X != 0 && n.Z != 0;
        }

        /// Junctions do not all switch at once — that is what makes a grid feel
        /// mechanical. A per-junction offset gives something close to a green
        /// wave along each avenue.
        public static double Offset(StreetNode n) =>
            n == null ? 0 : Mod((n.X * 0.15) + (n.Z * 0.35), Cycle);

        /// "ns-green" | "ns-amber" | "all-red" | "ew-green" | "ew-amber".
        public static string Phase(StreetNode n, double t)
        {
            double p = Mod(t + Offset(n), Cycle);
            if (p < GreenSeconds) return "ns-green";
            if (p < GreenSeconds + AmberSeconds) return "ns-amber";
            if (p < HalfCycle) return "all-red";
            p -= HalfCycle;
            if (p < GreenSeconds) return "ew-green";
            if (p < GreenSeconds + AmberSeconds) return "ew-amber";
            return "all-red";
        }

        /// May a vehicle approaching along this axis enter the junction now?
        public static bool MayEnter(StreetNode n, double t, bool northSouth)
        {
            var phase = Phase(n, t);
            return northSouth ? phase == "ns-green" : phase == "ew-green";
        }

        static double Mod(double a, double m)
        {
            double r = a % m;
            return r < 0 ? r + m : r;
        }
    }

    /// One vehicle on the network. Position is (edge, distance along it), not a
    /// free (x, z) — a car that is not on a road is a bug, and this makes that
    /// unrepresentable rather than merely unlikely.
    public class Vehicle
    {
        public int Id;
        public VehicleKind Kind;
        public string ColorHint;          // the Unity layer picks the actual material

        public string FromId, ToId;       // the directed edge being driven
        public StreetEdge Edge;
        public double S;                  // metres of the FRONT bumper from FromId
        public double Speed;

        public double X, Z, Heading;      // derived each step, for the renderer
        public bool Braking;
        public string BlockedBy;          // diagnostic: "car"|"light"|"sign"|"person"|"junction"

        public readonly List<string> Route = new List<string>();
        public double DwellUntil;         // bus at a stop, taxi on a rank
        /// Parked up for the night. A dormant vehicle is not stepped, is not an
        /// obstacle, and is not drawn — the street empties after midnight the
        /// way a street does, rather than the same dozen cars circling at 3am.
        public bool Dormant;
        public string StoppedAt;          // stop sign honoured at this junction
        public string InJunction;         // junction currently occupied, or null
        public string CameFrom;           // the node the InJunction was entered from
        public double ClearedDistance;    // metres driven since entering the new edge

        public bool Waiting => Speed < 0.15;
    }

    /// The traffic model. Fixed-step, deterministic, no floating clock reads —
    /// the host hands it a delta and it substeps internally, so the CI sim at
    /// twenty minutes per second and the player's machine at 60fps produce the
    /// same behaviour rather than merely similar-looking behaviour.
    public class TrafficSim
    {
        public const double SubStep = 0.05;        // seconds
        public const double Lookahead = 26.0;      // how far a driver looks
        public const double JunctionRadius = 5.0;  // "inside the junction"
        public const double SpeedLimitLane = 4.0;
        public const double SpeedLimitStreet = 8.0;
        public const double SpeedLimitAvenue = 11.0;

        /// Something a driver will stop for and never drive through: the player,
        /// a walker crossing, a spilled crate. The host rewrites these each
        /// frame; Core never guesses where people are.
        ///
        /// `Id` is who it is, when it is somebody — needed so a collision can
        /// name a victim rather than reporting that a car hit a coordinate.
        public struct Hazard { public double X, Z, R; public string Id, Name; }

        /// Somebody was struck. Not killed — see the note at the top of the file.
        public struct Strike
        {
            public string VictimId, VictimName;
            public Vehicle By;
            /// True when it was the player at the wheel, which is the only case
            /// where any of this is the player's fault.
            public bool ByPlayer;
            public double Speed;
            /// How hard, 0..1, from the speed it happened at.
            public double Force;
        }

        /// Collisions since the last time anybody asked. The host drains these,
        /// turns them into injuries and memories, and clears the list — Core
        /// reports the physics and decides none of the consequences.
        public readonly List<Strike> Strikes = new List<Strike>();

        /// Below this, a vehicle nudging somebody is a nudge. A driver who has
        /// already braked to walking pace does not put anybody in the infirmary,
        /// and pretending otherwise would make the player's own careful driving
        /// feel unrewarded.
        public const double StrikeSpeed = 2.2;
        /// The player's car is the only thing that can strike anybody. AI
        /// drivers brake in time, always — an NPC car that maimed a pedestrian
        /// while the player watched would be a consequence with no decision
        /// attached, which is the definition of noise.
        public string PlayerHazardId = "player_car";

        public readonly List<Vehicle> Vehicles = new List<Vehicle>();
        public readonly List<Hazard> Hazards = new List<Hazard>();

        public double Clock { get; private set; }
        public int StepsRun { get; private set; }
        /// Diagnostics the sim report gates on.
        public int NearMisses { get; private set; }     // gap closed below a metre
        public int YieldsToPeople { get; private set; } // braked for a hazard

        ulong _rng;
        List<string> _busLoop = new List<string>();
        List<string> _ranks = new List<string>();

        public TrafficSim(int seed = 7)
        {
            _rng = (ulong)(seed <= 0 ? 1 : seed) * 6364136223846793005UL + 1442695040888963407UL;
        }

        double Next() { _rng = _rng * 6364136223846793005UL + 1442695040888963407UL; return ((_rng >> 33) & 0xFFFFFF) / 16777216.0; }
        int NextInt(int n) => n <= 0 ? 0 : (int)(Next() * n) % n;

        // ---- construction ----

        /// The bus's fixed circuit: the outer ring of junctions, clockwise. A bus
        /// that wanders is not a bus.
        public List<string> BusLoop { get { EnsureRoutes(); return _busLoop; } }
        public List<string> Ranks { get { EnsureRoutes(); return _ranks; } }

        void EnsureRoutes()
        {
            if (_busLoop.Count > 0) return;
            int nx = StreetMap.AvenuesX.Length, nz = StreetMap.AvenuesZ.Length;
            for (int i = 0; i < nx; i++) _busLoop.Add($"j{i}_{nz - 1}");
            for (int j = nz - 2; j >= 0; j--) _busLoop.Add($"j{nx - 1}_{j}");
            for (int i = nx - 2; i >= 0; i--) _busLoop.Add($"j{i}_0");
            for (int j = 1; j < nz - 1; j++) _busLoop.Add($"j0_{j}");

            foreach (var id in new[] { "stop_ferry_stop", "stop_cab_rank" })
                if (StreetMap.Node(id) != null) _ranks.Add(id);
        }

        /// A bus stop is every third junction on the circuit — close enough that
        /// waiting for one is never the whole evening, far enough that the bus
        /// is not permanently stationary.
        public bool IsBusStop(string nodeId)
        {
            EnsureRoutes();
            int i = _busLoop.IndexOf(nodeId);
            return i >= 0 && i % 3 == 0;
        }

        /// Populate the streets. Density rather than count is the thing to tune:
        /// this grid is 16 blocks, and about a dozen vehicles reads as a working
        /// district without ever becoming a jam the player has to wait out.
        public void Populate(int count = 14)
        {
            EnsureRoutes();
            Vehicles.Clear();
            var junctions = new List<StreetNode>();
            foreach (var n in StreetMap.Nodes) if (n.IsJunction) junctions.Add(n);
            if (junctions.Count < 2) return;

            // One bus, always, on the circuit.
            var bus = Spawn(VehicleKinds.Bus, StreetMap.Node(_busLoop[0]), StreetMap.Node(_busLoop[1]));
            if (bus != null) RouteBusFrom(bus);

            for (int i = Vehicles.Count; i < count; i++)
            {
                var kind = PickKind();
                var a = junctions[NextInt(junctions.Count)];
                StreetNode b = null;
                foreach (var e in StreetMap.EdgesAt(a.Id))
                {
                    if (!e.Driveable) continue;
                    b = StreetMap.Node(StreetMap.Other(e, a.Id));
                    if (NextInt(3) == 0) break;      // deterministic spread of headings
                }
                if (b == null) continue;
                var v = Spawn(kind, a, b);
                if (v != null) Reroute(v);
            }
        }

        VehicleKind PickKind()
        {
            double total = 0;
            foreach (var k in VehicleKinds.All) if (!k.StopsAtStops) total += k.Rarity;
            double roll = Next() * total;
            foreach (var k in VehicleKinds.All)
            {
                if (k.StopsAtStops) continue;    // buses are placed explicitly
                roll -= k.Rarity;
                if (roll <= 0) return k;
            }
            return VehicleKinds.Car;
        }

        Vehicle Spawn(VehicleKind kind, StreetNode a, StreetNode b)
        {
            var edge = EdgeBetween(a?.Id, b?.Id);
            if (edge == null) return null;
            var v = new Vehicle
            {
                Id = Vehicles.Count + 1,
                Kind = kind,
                FromId = a.Id,
                ToId = b.Id,
                Edge = edge,
                S = kind.Length + 1.0 + Next() * Math.Max(1.0, edge.Length - kind.Length - 4.0),
                Speed = 0,
                ColorHint = kind.Id + NextInt(4),
            };
            // Never stack two spawns on the same stretch of road.
            foreach (var o in Vehicles)
                if (o.FromId == v.FromId && o.ToId == v.ToId && Math.Abs(o.S - v.S) < 14.0)
                    return null;
            Vehicles.Add(v);
            Place(v);
            return v;
        }

        public static StreetEdge EdgeBetween(string a, string b)
        {
            if (a == null || b == null) return null;
            foreach (var e in StreetMap.EdgesAt(a))
                if (StreetMap.Other(e, a) == b) return e;
            return null;
        }

        // ---- stepping ----

        public void Step(double dt)
        {
            if (dt <= 0) return;
            if (dt > 1.0) dt = 1.0;              // a stall must not teleport traffic
            // A FIXED SLICE, ACCUMULATED — not `dt / ceil(dt / SubStep)`.
            //
            // The old line sub-stepped, which looks like frame-rate
            // independence and is not: at 60fps it ran one slice of 16.7ms
            // and at 10fps two slices of 50ms, so the two machines integrated
            // the same ten seconds with different h and drifted apart. Short
            // edges hid it — a vehicle reaching a junction resets S, and the
            // old 26m grid reset everybody several times in ten seconds, so
            // the accumulated difference was clamped before it could show.
            // The topology stretch made edges 2.15x longer, the resets got
            // rarer, and the drift the test allows 2.5m of came back 14.15.
            // The bound was not wrong; it was being flattered by the map.
            //
            // With a fixed slice and a remainder carried forward, any
            // sequence of dt summing to the same total runs the SAME number
            // of identical advances, so the two machines agree by
            // construction rather than by being interrupted often enough.
            _stepAccum += dt;
            while (_stepAccum >= SubStep - 1e-12)
            {
                Advance(SubStep);
                _stepAccum -= SubStep;
            }
        }

        double _stepAccum;

        void Advance(double h)
        {
            Clock += h;
            StepsRun++;

            // Two passes so the outcome never depends on list order: everyone
            // decides against the same world, then everyone moves.
            var targets = new double[Vehicles.Count];
            for (int i = 0; i < Vehicles.Count; i++)
                targets[i] = Vehicles[i].Dormant ? 0 : Decide(Vehicles[i]);

            for (int i = 0; i < Vehicles.Count; i++)
            {
                var v = Vehicles[i];
                if (v.Dormant) { v.Speed = 0; continue; }
                double target = targets[i];
                double was = v.Speed;
                double rate = target < was ? v.Kind.Brake : v.Kind.Accel;
                double delta = target - was;
                double move = rate * h;
                v.Speed += Math.Abs(delta) < move ? delta : Math.Sign(delta) * move;
                if (v.Speed < 0) v.Speed = 0;
                v.Braking = target < was - 0.01;

                double travelled = v.Speed * h;

                // A HARD FLOOR UNDER THE PROMISE, not just a braking model.
                //
                // "An AI driver stops, always" was true only because a 26m
                // grid never let anyone reach 11 m/s. Give a car room to get
                // there and the arithmetic bites: stopping from top speed
                // needs 11m at 5.5 m/s^2, so a person who appears 8m ahead
                // CANNOT be stopped for — the planner brakes, the car goes
                // through, and once past, the corridor test stops seeing them
                // and it accelerates away. The stretch found it by driving a
                // car fifteen metres beyond somebody standing in the road.
                //
                // Braking stays the behaviour; this is the invariant. A
                // vehicle may not advance past a hazard in its own corridor,
                // however fast it arrived — it stops hard against them
                // instead, which is a driver standing on the brakes rather
                // than a driver committing manslaughter. `Enforce` already
                // does exactly this for vehicle-on-vehicle overlap; people
                // were the case nobody wrote it for.
                double blocked = -1;
                if (Heading(v, out var hdx, out var hdz))
                    foreach (var hz in Hazards)
                    {
                        double ahead = CorridorAlong(v, hdx, hdz, hz.X, hz.Z, hz.R);
                        if (ahead >= 0 && (blocked < 0 || ahead < blocked)) blocked = ahead;
                    }
                if (blocked >= 0)
                {
                    double room = Math.Max(0, blocked - v.Kind.Length * 0.5);
                    if (travelled > room)
                    {
                        travelled = room;
                        v.Speed = 0;
                        v.Braking = true;
                        v.BlockedBy = "person";
                    }
                }

                TotalDistance += travelled;
                v.S += travelled;
                v.ClearedDistance += travelled;
                Cross(v);
            }

            Enforce();
            for (int i = 0; i < Vehicles.Count; i++) Place(Vehicles[i]);
        }

        /// The planner keeps a comfortable gap; this makes an overlap impossible.
        ///
        /// The two are not the same job. A follower plans against the room it can
        /// see, but the leader can always brake harder than the follower
        /// predicted, and over a discrete step that showed up as vehicles
        /// interpenetrating by a few centimetres — invisible in a screenshot,
        /// and exactly the kind of thing that becomes a car sticking through a
        /// bus on somebody's monitor at 3am. So after everyone has moved, each
        /// vehicle is clamped behind the one in front. Nose to tail is allowed;
        /// through is not.
        void Enforce()
        {
            _order.Clear();
            for (int i = 0; i < Vehicles.Count; i++) _order.Add(Vehicles[i]);
            _order.Sort((a, b) =>
            {
                int c = string.CompareOrdinal(a.FromId, b.FromId);
                if (c != 0) return c;
                c = string.CompareOrdinal(a.ToId, b.ToId);
                if (c != 0) return c;
                c = b.S.CompareTo(a.S);          // furthest along first
                return c != 0 ? c : a.Id.CompareTo(b.Id);
            });

            for (int i = 1; i < _order.Count; i++)
            {
                var lead = _order[i - 1];
                var v = _order[i];
                if (v.Dormant || lead.Dormant) continue;
                if (v.FromId != lead.FromId || v.ToId != lead.ToId) continue;
                double limit = lead.S - lead.Kind.Length;
                // THE LEADER'S TAIL IS BEHIND THE JUNCTION, and clamping to zero
                // does not separate them — it parks the follower's nose at the
                // edge start while the leader's body still covers it. That is
                // where every negative reading of `TightestGap` comes from: the
                // four gaps in sixty-eight kept runs are -0.28, -2.58, -2.69 and
                // -3.20, and a car is 4.2m long, a bus 10.5m. The arithmetic is
                // `lead.S - lead.Kind.Length` with `lead.S` small, nothing more
                // exotic.
                //
                // AND THE QUESTION IS SETTLED. `Cross` calls `RoomOn(v.ToId,
                // nextId, v.Kind.Length + v.Kind.Gap)` before it lets anybody
                // onto the next edge, and that requires every vehicle already
                // there to have its TAIL at least a full follower-length along
                // it. So a leader whose tail is behind the origin cannot have
                // acquired a follower through the junction, and the negative
                // readings are an arclength measured across a junction rather
                // than two bodies in the same place.
                //
                // Which is why the counter below only fires when the clamp had
                // to act as well.
                // COUNTED ONLY WHEN IT MATTERED, and the first version was not.
                //
                // It incremented on every pair where `lead.S < lead.Kind.Length`,
                // and that is an ordinary geometric fact rather than a fault: a
                // 10.5m bus that has just crossed a junction has its tail behind
                // this edge's origin for the first 10.5 metres, whether or not
                // anybody is following it. One run read 39 and I put "39 tails
                // behind an edge start is a lot" on the queue as an open
                // question about junction entry.
                //
                // It is not open. `Cross` calls `RoomOn(v.ToId, nextId,
                // v.Kind.Length + v.Kind.Gap)` before entering, which requires
                // every vehicle already on the far edge to have its TAIL at
                // least a full follower-length along it — so the entry check
                // does prevent the overlap, and the count was measuring
                // something else entirely while being read as evidence about it.
                //
                // The number that means what the name says is the intersection:
                // a pair the clamp had to act on, whose limit could not separate
                // them. That one is a real fault if it is ever non-zero.
                bool tailBehind = limit < 0;
                if (tailBehind) limit = 0;
                if (v.S > limit)
                {
                    if (tailBehind) TailsBehindStart++;
                    // OVERLAPS RESOLVED, AND THE COUNT IS THE POINT. The clamp
                    // leaves the pair at a gap of EXACTLY `lead.S - length - v.S`
                    // = 0, so `gap=0.00` in the verdict does not mean "traffic
                    // is flowing with no room"; it means "the de-overlap pass
                    // fired at the sampled instant". Sixteen of forty-eight
                    // measured runs read exactly 0.00, which is not a coincidence
                    // and was indistinguishable from a healthy gap because both
                    // pass `>= 0`.
                    //
                    // A planner that never needs this is the goal; a planner that
                    // needs it constantly is a planner that is not working, and
                    // the gate could not tell those apart while the only number
                    // was a distance.
                    OverlapsResolved++;
                    TotalDistance -= v.S - limit;
                    v.S = limit;
                    if (v.Speed > lead.Speed) v.Speed = lead.Speed;
                }
            }
        }

        readonly List<Vehicle> _order = new List<Vehicle>();

        /// What speed this driver wants right now: the limit, reduced by whatever
        /// is closest in front of them.
        double Decide(Vehicle v)
        {
            v.BlockedBy = null;
            if (Clock < v.DwellUntil) { v.BlockedBy = "stop"; return 0; }

            double limit = Math.Min(v.Kind.TopSpeed, LimitOf(v.Edge));
            double dist = DistanceToObstacle(v, out var why);
            if (dist >= Lookahead) return limit;

            v.BlockedBy = why;
            double room = dist - v.Kind.Gap;
            if (room <= 0) return 0;
            // The speed from which this vehicle could still stop in the room it
            // has. Comfortable braking, not emergency braking — the difference is
            // what makes traffic look like driving rather than like collision
            // resolution.
            double safe = Math.Sqrt(2.0 * v.Kind.Brake * 0.9 * room);
            return Math.Min(limit, safe);
        }

        public static double LimitOf(StreetEdge e) =>
            e == null ? SpeedLimitLane
            : e.Kind == "avenue" ? SpeedLimitAvenue
            : e.Kind == "street" ? SpeedLimitStreet
            : SpeedLimitLane;

        double DistanceToObstacle(Vehicle v, out string why)
        {
            why = null;
            double best = Lookahead;

            // 1. The vehicle in front, on this stretch.
            foreach (var o in Vehicles)
            {
                if (o == v || o.Dormant || o.FromId != v.FromId || o.ToId != v.ToId) continue;
                if (o.S <= v.S) continue;
                double gap = o.S - o.Kind.Length - v.S;
                if (gap < best) { best = gap; why = "car"; }
            }

            // 2. A person in the road. An AI driver stops, always, however
            // inconvenient — they have no story to be part of, so all a
            // pedestrian gets from them is a delay.
            if (Heading(v, out var pdx, out var pdz))
                foreach (var hz in Hazards)
                {
                    double ahead = CorridorAlong(v, pdx, pdz, hz.X, hz.Z, hz.R);
                    if (ahead >= 0 && ahead < best) { best = ahead; why = "person"; }
                }

            // 3. The junction at the end of the road, if it will not have us.
            double toJunction = v.Edge.Length - v.S;
            if (toJunction < best)
            {
                var node = StreetMap.Node(v.ToId);
                if (!MayProceed(v, node, out var reason))
                {
                    best = toJunction;
                    why = reason;
                }
            }

            if (best < 0) best = 0;
            if (why == "person" && v.Speed > 0.2) YieldsToPeople++;
            if (why == "car" && best < 1.0) NearMisses++;
            return best;
        }

        /// Distance to a hazard that is genuinely in this vehicle's path, or -1.
        /// THE VEHICLE'S UNIT HEADING, ONCE PER VEHICLE.
        ///
        /// This used to live inside `Corridor`, which is called once per
        /// HAZARD — so a lorry with forty pedestrians near it did forty
        /// identical pairs of node lookups and forty identical square roots
        /// to rediscover the direction of the road it was already on. The
        /// heading does not depend on the hazard at all.
        ///
        /// It is the same shape as the crowd separation's square roots, found
        /// by grepping for that fault rather than by noticing it twice, and
        /// `traffic` is the second largest cost in the game budget after
        /// `npcs`. Behaviour is untouched: the same direction reaches the same
        /// arithmetic, just computed once instead of per hazard, and the
        /// degenerate cases return the same -1 through `false` here.
        bool Heading(Vehicle v, out double dx, out double dz)
        {
            dx = dz = 0;
            var a = StreetMap.Node(v.FromId);
            var b = StreetMap.Node(v.ToId);
            if (a == null || b == null) return false;
            dx = b.X - a.X; dz = b.Z - a.Z;
            double len = Math.Sqrt(dx * dx + dz * dz);
            if (len < 1e-6) return false;
            dx /= len; dz /= len;
            return true;
        }

        /// How far ahead a hazard sits in this vehicle's lane, given a heading
        /// already computed by `Heading`. -1 when it is behind, beyond the
        /// lookahead, or off to the side.
        double CorridorAlong(Vehicle v, double dx, double dz,
                             double hx, double hz, double r)
        {
            double ox = hx - v.X, oz = hz - v.Z;
            double ahead = ox * dx + oz * dz;
            if (ahead < 0 || ahead > Lookahead) return -1;
            double lateral = Math.Abs(ox * dz - oz * dx);
            if (lateral > v.Kind.Width / 2.0 + r + 0.3) return -1;
            return Math.Max(0, ahead - r);
        }

        /// The junction rules, in one place: lights where there are lights, a
        /// full stop where there is a stop sign, never into an occupied box, and
        /// never into a queue with no room on the far side.
        bool MayProceed(Vehicle v, StreetNode node, out string why)
        {
            why = "junction";
            if (node == null) return true;

            // Lane ends are not junctions — they are doorways; you stop there
            // because the road ran out, and the reroute handles it.
            if (!node.IsJunction) return true;

            if (Signals.HasLights(node))
            {
                if (!Signals.MayEnter(node, Clock, IsNorthSouth(v)))
                {
                    why = "light";
                    return false;
                }
            }
            else
            {
                // A stop sign means a stop. Honoured once per approach, cleared
                // when the vehicle leaves the junction behind.
                if (v.StoppedAt != node.Id)
                {
                    if (v.Speed > 0.25 || v.Edge.Length - v.S > JunctionRadius)
                    {
                        why = "sign";
                        return false;
                    }
                    v.StoppedAt = node.Id;
                }
            }
            // From here on the signal says this driver may go, so anyone they
            // yield to must be someone the signal is also letting go — otherwise
            // a car waits politely for a car that is itself sat at a red, which
            // is a deadlock wearing good manners.

            // Somebody is in the box, arriving from somewhere else.
            foreach (var o in Vehicles)
            {
                if (o == v || o.Dormant || o.InJunction != node.Id) continue;
                if (o.CameFrom == v.FromId) continue;   // same approach: car-following covers it
                why = "junction";
                return false;
            }

            // Two drivers waiting at the same box from different approaches: the
            // lower Id goes. Arbitrary but TOTAL, which is what stops a four-way
            // stop from locking solid — the failure mode that would strand the
            // player behind traffic that never moves again.
            foreach (var o in Vehicles)
            {
                if (o == v || o.Dormant || o.ToId != node.Id || o.FromId == v.FromId) continue;
                if (o.Edge == null || o.Id > v.Id) continue;
                if (Clock < o.DwellUntil) continue;                       // they are parked, not waiting
                if (o.Edge.Length - o.S >= JunctionRadius + 1.0) continue; // not here yet
                if (!SignalAllows(o, node)) continue;                     // held by the light themselves
                why = "junction";
                return false;
            }

            var next = NextNodeFor(v, node);
            if (next != null)
            {
                var e = EdgeBetween(node.Id, next);
                if (e != null)
                {
                    // Do not enter unless there is somewhere to be on the far
                    // side. This is what stops a queue from backing across a
                    // junction and gridlocking the grid.
                    foreach (var o in Vehicles)
                    {
                        if (o == v || o.Dormant || o.FromId != node.Id || o.ToId != next) continue;
                        if (o.S - o.Kind.Length < v.Kind.Length + v.Kind.Gap)
                        {
                            why = "junction";
                            return false;
                        }
                    }
                }
            }
            return true;
        }

        /// Would the light (or the stop sign) let this driver into that junction
        /// right now? Read-only — unlike the check inside MayProceed, this one
        /// never records a stop on somebody else's behalf.
        bool SignalAllows(Vehicle v, StreetNode node)
        {
            if (node == null || !node.IsJunction) return true;
            if (Signals.HasLights(node)) return Signals.MayEnter(node, Clock, IsNorthSouth(v));
            return v.StoppedAt == node.Id;
        }

        bool IsNorthSouth(Vehicle v)
        {
            var a = StreetMap.Node(v.FromId);
            var b = StreetMap.Node(v.ToId);
            if (a == null || b == null) return true;
            return Math.Abs(b.Z - a.Z) >= Math.Abs(b.X - a.X);
        }

        // ---- routing ----

        string NextNodeFor(Vehicle v, StreetNode at)
        {
            for (int i = 0; i < v.Route.Count; i++)
                if (v.Route[i] == at.Id)
                    return i + 1 < v.Route.Count ? v.Route[i + 1] : null;
            return v.Route.Count > 0 ? v.Route[0] : null;
        }

        void Cross(Vehicle v)
        {
            // Occupancy means IN the junction, not near it. Marking the box on
            // the approach seemed safer and was the opposite: three vehicles
            // converging on the same crossing each claimed it from four metres
            // out, each saw the other two in it, and all three sat there for the
            // rest of the night. Who is coming is handled by priority below;
            // this is only who is actually in the way.
            if (v.InJunction != null && v.ClearedDistance > v.Kind.Length + JunctionRadius)
            {
                v.InJunction = null;
                v.CameFrom = null;
            }

            if (v.S < v.Edge.Length) return;

            var arrived = StreetMap.Node(v.ToId);

            // The stop line is a hard edge, not a preference. The planner brakes
            // for a red from a comfortable distance, but a driver already inside
            // its own following gap when the light changed would coast across —
            // one crossing in six minutes, and "hardly ever runs a red" is not a
            // property worth having. Held at the line instead; at a twentieth of
            // a second per substep the snap is under a centimetre.
            if (!MayProceed(v, arrived, out _))
            {
                v.S = v.Edge.Length;
                v.Speed = 0;
                return;
            }

            double overshoot = v.S - v.Edge.Length;

            // Consume this node from the route.
            int idx = v.Route.IndexOf(v.ToId);
            if (idx >= 0) v.Route.RemoveRange(0, idx + 1);

            if (arrived != null && v.Kind.StopsAtStops && IsBusStop(arrived.Id))
                v.DwellUntil = Clock + 5.0;
            if (arrived != null && v.Kind.WaitsAtRanks && _ranks.Contains(arrived.Id))
                v.DwellUntil = Clock + 8.0;

            string nextId = v.Route.Count > 0 ? v.Route[0] : null;
            var nextEdge = EdgeBetween(v.ToId, nextId);
            if (nextEdge == null)
            {
                if (v.Kind.StopsAtStops) RouteBusFrom(v); else Reroute(v);
                nextId = v.Route.Count > 0 ? v.Route[0] : null;
                nextEdge = EdgeBetween(v.ToId, nextId);
            }
            if (nextEdge == null)
            {
                // Nowhere to go — turn round rather than sit in the road forever.
                var back = v.FromId;
                nextEdge = EdgeBetween(v.ToId, back);
                nextId = back;
                v.Route.Clear();
                if (nextEdge == null) { v.S = v.Edge.Length; v.Speed = 0; return; }
            }

            // The last word on not driving into the back of anybody. The planner
            // already refuses to enter a junction with no room on the far side,
            // but a reroute chosen AT the junction picks a road the planner never
            // looked at, and that is how a car ended up inside a bus. If the
            // chosen road is full, hold at the stop line — blocking the box is
            // rude, and it clears itself the moment the queue moves.
            if (!RoomOn(v.ToId, nextId, v.Kind.Length + v.Kind.Gap))
            {
                v.S = v.Edge.Length;
                v.Speed = 0;
                return;
            }

            if (arrived != null && arrived.IsJunction)
            {
                v.InJunction = arrived.Id;
                v.CameFrom = v.FromId;
            }
            v.FromId = v.ToId;
            v.ToId = nextId;
            v.Edge = nextEdge;
            v.S = Math.Min(overshoot, nextEdge.Length);
            v.ClearedDistance = 0;
            v.StoppedAt = null;
        }

        /// Is there space at the near end of the road from `from` to `to` for a
        /// vehicle needing this many metres?
        bool RoomOn(string from, string to, double needed)
        {
            foreach (var o in Vehicles)
            {
                if (o.Dormant || o.FromId != from || o.ToId != to) continue;
                if (o.S - o.Kind.Length < needed) return false;
            }
            return true;
        }

        /// How often a vehicle is going somewhere outside its own district.
        /// Enough that the bridges and the goods roads always have somebody on
        /// them; few enough that they are a crossing rather than a queue.
        public const int CrossDistrictPercent = 22;

        readonly Dictionary<string, List<string>> _junctionsByDistrict =
            new Dictionary<string, List<string>>(StringComparer.Ordinal);
        readonly List<string> _allJunctions = new List<string>();

        void IndexJunctions()
        {
            if (_allJunctions.Count > 0) return;
            foreach (var n in StreetMap.Nodes)
            {
                if (!n.IsJunction) continue;
                _allJunctions.Add(n.Id);
                var district = StreetMap.DistrictAt(n.X, n.Z) ?? "";
                if (!_junctionsByDistrict.TryGetValue(district, out var list))
                    _junctionsByDistrict[district] = list = new List<string>();
                list.Add(n.Id);
            }
        }

        List<string> AllJunctions() { IndexJunctions(); return _allJunctions; }

        /// The junctions in the same district as this one.
        List<string> LocalJunctions(string nodeId)
        {
            IndexJunctions();
            var n = StreetMap.Node(nodeId);
            if (n == null) return null;
            var district = StreetMap.DistrictAt(n.X, n.Z) ?? "";
            return _junctionsByDistrict.TryGetValue(district, out var list) ? list : null;
        }

        void Reroute(Vehicle v)
        {
            v.Route.Clear();
            string destination = null;

            if (v.Kind.WaitsAtRanks && _ranks.Count > 0 && NextInt(2) == 0)
                destination = _ranks[NextInt(_ranks.Count)];

            if (destination == null)
            {
                // MOST TRIPS ARE LOCAL, and it is not a realism flourish — it is
                // the difference between a working city and a solid one.
                //
                // Destinations used to be uniform over every junction on the
                // map. With one district that is indistinguishable from local.
                // With three it makes every second vehicle a long-haul commuter,
                // and since the districts are joined by exactly four chokepoints
                // (two bridges, two goods roads) EVERY one of those journeys
                // queues at the same four places. Measured: throughput fell by
                // two thirds over three minutes and fourteen vehicles converged
                // onto one corridor. The chokepoints were doing their job; there
                // was simply no reason for anybody to be anywhere else.
                //
                // Real streets are not like that. Most journeys are short and
                // stay in the neighbourhood, and the ones that cross are a
                // minority — which keeps the bridges carrying somebody without
                // making them the whole city's only story.
                var pool = LocalJunctions(v.ToId);
                if (pool == null || pool.Count == 0 || NextInt(100) < CrossDistrictPercent)
                    pool = AllJunctions();
                if (pool.Count == 0) return;
                for (int tries = 0; tries < 6; tries++)
                {
                    var pick = pool[NextInt(pool.Count)];
                    if (pick != v.ToId && pick != v.FromId) { destination = pick; break; }
                }
                if (destination == null) return;
            }

            // Bikes may thread the lanes; everything else keeps to real roads.
            var path = StreetMap.Route(v.ToId, destination, driveableOnly: !v.Kind.UsesLanes);
            for (int i = 1; i < path.Count; i++) v.Route.Add(path[i].Id);
            // Never route straight back the way we came unless there is no choice.
            if (v.Route.Count > 0 && v.Route[0] == v.FromId && v.Route.Count == 1) v.Route.Clear();
        }

        void RouteBusFrom(Vehicle v)
        {
            EnsureRoutes();
            v.Route.Clear();
            int i = _busLoop.IndexOf(v.ToId);
            if (i < 0) { Reroute(v); return; }
            for (int k = 1; k <= _busLoop.Count; k++)
                v.Route.Add(_busLoop[(i + k) % _busLoop.Count]);
        }

        // ---- presentation helpers ----

        /// Drive on the right, one lane each way. Bikes ride nearer the kerb.
        void Place(Vehicle v)
        {
            var a = StreetMap.Node(v.FromId);
            var b = StreetMap.Node(v.ToId);
            if (a == null || b == null) return;
            double dx = b.X - a.X, dz = b.Z - a.Z;
            double len = Math.Sqrt(dx * dx + dz * dz);
            if (len < 1e-6) return;
            dx /= len; dz /= len;
            double t = Math.Min(v.S, len);
            double offset = v.Kind.UsesLanes
                ? Math.Max(0.8, v.Edge.Width / 2.0 - 1.0)
                : v.Edge.Width / 4.0;
            // Right of travel in Unity's XZ: right = (dz, -dx).
            v.X = a.X + dx * t + dz * offset;
            v.Z = a.Z + dz * t - dx * offset;
            v.Heading = Math.Atan2(dx, dz) * 180.0 / Math.PI;
        }

        /// How busy the streets are at this hour, 0..1. Rush twice a day, quiet
        /// through the small hours, never quite nothing — a city with literally
        /// no traffic at 4am reads as broken rather than as late.
        public static double BusynessAt(int hour)
        {
            if (hour >= 7 && hour < 10) return 1.0;      // morning
            if (hour >= 10 && hour < 17) return 0.8;
            if (hour >= 17 && hour < 20) return 1.0;     // evening
            if (hour >= 20 && hour < 23) return 0.6;
            if (hour >= 23 || hour < 2) return 0.35;
            return 0.2;                                  // the small hours
        }

        /// Park up or wake up so the number of vehicles actually running matches
        /// the hour. Deterministic by index rather than by a roll, so the same
        /// cars are out at the same times and the street has a character.
        public void SetHour(int hour)
        {
            double busy = BusynessAt(hour);
            int want = (int)Math.Round(Vehicles.Count * busy);
            if (want < 2) want = Math.Min(2, Vehicles.Count);
            for (int i = 0; i < Vehicles.Count; i++)
            {
                // The bus runs all day and stops overnight; everything else
                // thins from the back of the list.
                bool awake = i < want;
                var v = Vehicles[i];
                if (v.Dormant == !awake) continue;
                v.Dormant = !awake;
                if (!v.Dormant) { v.StoppedAt = null; v.InJunction = null; v.ClearedDistance = 999; }
            }
        }

        public int AwakeCount()
        {
            int n = 0;
            foreach (var v in Vehicles) if (!v.Dormant) n++;
            return n;
        }

        /// Did the player's car just hit somebody? Called by the host with the
        /// player's vehicle, because the player's car is not in Vehicles — it is
        /// driven by a person, not by this model.
        ///
        /// Deliberately one-directional: AI traffic brakes for people and the
        /// player's car does not brake for anybody, because the player is
        /// holding the wheel and that is exactly the difference between a system
        /// and a decision.
        public Strike? Contact(double x, double z, double speed, double halfWidth, double halfLength)
        {
            if (speed < StrikeSpeed) return null;
            foreach (var hz in Hazards)
            {
                if (hz.Id == PlayerHazardId || string.IsNullOrEmpty(hz.Id)) continue;
                double dx = hz.X - x, dz = hz.Z - z;
                double reach = Math.Max(halfWidth, halfLength) + hz.R;
                if (dx * dx + dz * dz > reach * reach) continue;

                var strike = new Strike
                {
                    VictimId = hz.Id,
                    VictimName = hz.Name ?? hz.Id,
                    ByPlayer = true,
                    Speed = speed,
                    // Walking pace is nothing; the top of the arcade speed range
                    // is as bad as it gets, and it still is not fatal.
                    Force = Math.Clamp((speed - StrikeSpeed) / 9.0, 0, 1),
                };
                Strikes.Add(strike);
                return strike;
            }
            return null;
        }

        /// The nearest vehicle to a point, within a radius — how a witness comes
        /// to say "somebody came in a car" instead of "somebody was about".
        public Vehicle NearestTo(double x, double z, double within = 14.0)
        {
            Vehicle best = null;
            double bestD = within * within;
            foreach (var v in Vehicles)
            {
                if (v.Dormant) continue;
                double d = (v.X - x) * (v.X - x) + (v.Z - z) * (v.Z - z);
                if (d < bestD) { bestD = d; best = v; }
            }
            return best;
        }

        /// Total metres driven, as a liveness signal for the sim report: traffic
        /// that has stopped moving is a bug the player would notice in a second
        /// and a screenshot never would.
        public double TotalDistance { get; private set; }

        /// How many times `Enforce` has had to push a follower back off a leader.
        ///
        /// Zero is the goal: the planner in `Decide` is supposed to keep the
        /// room, and the clamp exists only because a leader can brake harder
        /// over a discrete step than the follower predicted. A count that climbs
        /// with the metres driven means the planner is not planning and the
        /// clamp is doing the driving — which looks identical in a screenshot
        /// and identical in `TightestGap`, because a resolved overlap reads as a
        /// gap of exactly zero and zero passes every bound this has ever had.
        public long OverlapsResolved { get; private set; }

        /// How many times the clamp HAD TO ACT on a pair whose leader's tail was
        /// behind the start of the edge — the one case where clamping to zero
        /// cannot separate them, and therefore the only case where a negative
        /// `TightestGap` is a real interpenetration rather than an arclength
        /// that crosses a junction.
        ///
        /// SHOULD BE ZERO. `Cross` refuses to enter an edge unless every vehicle
        /// already on it has its tail a full follower-length along, so the
        /// condition should be unreachable; a non-zero reading means that check
        /// is being bypassed. See `Enforce` for the version of this that counted
        /// an ordinary geometric fact instead, read 39, and sent me looking for
        /// a junction bug that was not there.
        public long TailsBehindStart { get; private set; }

        /// The pair behind the last `TightestGap()` reading, in words.
        ///
        /// WHY A SENTENCE AND NOT A NUMBER. The gate said `traffic` and nothing
        /// else for four failures running; adding the scalar turned that into
        /// `gap=-2.69`, which is better and still not diagnosable — it does not
        /// say whether a bus is inside a car or a car has just crossed a junction
        /// its leader had not cleared. Those are a physics bug and a coordinate
        /// artefact and they need completely different work. One line here is
        /// cheaper than either guess.
        public string TightestGapWhy { get; private set; } = "not measured";

        /// Smallest bumper gap currently open between any two vehicles sharing a
        /// stretch of road. Negative means an overlap, which must never happen.
        ///
        /// ONE INSTANT, AND THE CALLER MUST KNOW THAT. The sentinel comes back
        /// whenever no two vehicles shared a directed edge at the moment of the
        /// call — which is common and is good news about the city — and 20 of 68
        /// kept runs read `not-measured`. The sim's `trafficOk` accepted all
        /// twenty as proven clearance, because 999 passes `>= 0`.
        public double TightestGap()
        {
            double best = double.MaxValue;
            Vehicle bv = null, bo = null;
            foreach (var v in Vehicles)
                foreach (var o in Vehicles)
                {
                    if (o == v || o.Dormant || v.Dormant) continue;
                    if (o.FromId != v.FromId || o.ToId != v.ToId) continue;
                    if (o.S <= v.S) continue;
                    double gap = o.S - o.Kind.Length - v.S;
                    if (gap < best) { best = gap; bv = v; bo = o; }
                }
            if (best == double.MaxValue)
            {
                TightestGapWhy = "no two vehicles shared a directed edge at this instant";
                return 999;
            }
            // THE LEADER'S TAIL POSITION IS THE WHOLE DIAGNOSIS, so it is stated
            // rather than left to be worked out from three other numbers.
            double tail = bo.S - bo.Kind.Length;
            // COLONS, NOT EQUALS, AND THAT IS NOT COSMETIC. `verdict-keys` reads
            // every `name=` in the verdict as a measurement that must keep
            // being reported — a simple rule that has caught real losses. This
            // sentence is prose, and it only takes this branch when two
            // vehicles share an edge, so `S=` and `tail=` were learned as
            // required measurements and then went missing the first time the
            // road was clear. A false alarm on good news, which is the kind
            // that gets rebaselined on reflex until the checker is worthless.
            //
            // The tool's rule is right. The sentence was breaking it.
            TightestGapWhy =
                $"{bo.Kind.Id}#{bo.Id} lead S:{bo.S:0.00} len:{bo.Kind.Length:0.00} tail:{tail:0.00}"
                + $" over {bv.Kind.Id}#{bv.Id} at S:{bv.S:0.00}"
                + $" on {bo.FromId}->{bo.ToId}"
                + (tail < 0 ? " — LEADER'S TAIL IS BEHIND THE EDGE START" : "");
            return best;
        }
    }
}
