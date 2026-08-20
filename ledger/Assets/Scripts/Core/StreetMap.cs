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

        /// A district: its own grid, its own street names, its own character.
        ///
        /// The city was one district hardcoded into this file. Copper Row
        /// existed in the population, in the fiction and in three characters'
        /// backstories, and nowhere on the ground — which meant the game could
        /// talk about somewhere the player could never walk to. That is a worse
        /// kind of missing than an empty lot.
        public class District
        {
            public string Id, Name;
            public double[] AvenuesX, AvenuesZ;
            public string[] NamesNorthSouth, NamesEastWest;
            /// The founding cross belongs to the Hook alone. Elsewhere every
            /// road is an avenue, because nowhere else has a street the game
            /// was built on top of.
            public bool HasFoundingCross;
        }

        /// STREET-SPEC.MD, THE TOPOLOGY RE-PLAN. The measured case, in one
        /// line: at today's pitch a block holds ONE building per edge and the
        /// whole city tops out near 110 parcels, so no amount of dressing
        /// makes it read as a town. The spec derives the sizes from the
        /// buildings up — two terrace rows plus a yard is 16-19m of buildable
        /// depth, five to ten parcels is 35-70m of frontage — and that means
        /// RECTANGULAR blocks: long frontages on the named street, short ends
        /// on the side street. Today's are square and identical, which is why
        /// every street has the same rhythm.
        ///
        /// APPLIED AS A SCALE ABOUT EACH DISTRICT'S OWN CENTRE, which is the
        /// migration contract's cheapest honest form: one affine map per
        /// district, applied to the avenue lines AND to every address in it,
        /// so a place keeps its street, its side of that street and its
        /// position along it — by construction rather than by re-authoring
        /// sixty-one coordinates by hand and hoping.
        ///
        /// Behind a flag beside `WorldBuilder.TownPlanEnabled`, for the same
        /// reason: the graph is what every gate, walker and schedule consumes,
        /// so the way back has to be one constant.
        public const bool WideBlocks = true;

        /// The Hook's founding cross stays where it is — the pub is hand-built
        /// at fixed coordinates, Act I happens inside it, and a scale about
        /// the origin leaves x=0 and z=0 exactly where they were. Everything
        /// the pub touches sits inside that first block and travels with it.
        /// The long axis grows more than the short one; that anisotropy IS the
        /// rectangle.
        /// ONE STRETCH, ABOUT THE ORIGIN, FOR THE WHOLE CITY — and the first
        /// version scaled each district about its OWN centre, which CoreTests
        /// refused inside a minute ("an avenue is road along its length").
        /// The reason is arithmetic and obvious in hindsight: a district that
        /// grows in place grows INTO its neighbours. Downtown's east edge
        /// moved from -110 to -58 while the Hook's west edge moved from -52
        /// to -112, so two grids occupied the same ground and their avenues
        /// crossed with no junction between them.
        ///
        /// A single affine map over every coordinate cannot do that: every
        /// district, bridge and address moves together, relative arrangement
        /// exactly preserved, and NOTHING overlaps that did not overlap
        /// before. It also delivers the actual goal without touching a road:
        /// carriageways stay 8m while the gaps between them stretch, so the
        /// buildable depth of every block grows by the whole difference.
        ///
        /// Anisotropic on purpose — that is what makes a block a RECTANGLE
        /// with a long frontage and a short end, which is the spec's single
        /// biggest shape change from today's identical squares.
        public const double StretchX = 2.15, StretchZ = 1.15;

        static (double x, double z) BlockScale(District d) =>
            WideBlocks ? (StretchX, StretchZ) : (1.0, 1.0);

        /// The origin, for every district: the Hook's founding cross is at
        /// x=0/z=0 and the pub is hand-built against it, so scaling about the
        /// origin leaves both exactly where they are.
        static (double x, double z) DistrictCentre(District d) => (0.0, 0.0);

        /// The scaled position of an avenue line, and of anything standing
        /// beside one. ONE function, used by the grid, the blocks and the
        /// address migration, so the three cannot disagree — which is the
        /// failure this project finds in pairs more than any other.
        static double ScaleAbout(double v, double centre, double k) =>
            centre + (v - centre) * k;

        /// The Hook, and Copper Row across the cut to the north.
        ///
        /// Copper Row is the design doc's **immigrant market quarter — dense
        /// street life, cash economies, loyalty**. The first version of it drifted
        /// industrial (a foundry, a smelt yard, kilns) because I built it without
        /// reading §7 first; that is Ironside's brief, and it has gone back there.
        ///
        /// The market quarter is the better district for THIS game, which is why
        /// the correction was worth making rather than shrugging at. A cash
        /// economy is exactly where finite purses and Mickey's book of debts bite
        /// hardest: everybody here settles in notes, nobody's money is in a bank,
        /// and "what can you actually lay hands on today" is the question the
        /// whole street lives by.
        ///
        /// Its blocks are tighter (20m against the Hook's 26), which reads as
        /// dense rather than merely old and costs nothing — the grid generator
        /// does not care. Two bridges join the districts, and only two, because a
        /// chokepoint is a place things can happen: somebody waiting at a bridge
        /// is a scene, and somebody waiting on an open grid is a man standing in
        /// a road.
        public const double CopperSpacing = 20.0;
        public static readonly District[] Districts =
        {
            new District
            {
                Id = "hook", Name = "the Hook",
                AvenuesX = new double[] { -52, -26, 0, 26, 52 },
                AvenuesZ = new double[] { -52, -26, 0, 26, 52 },
                NamesNorthSouth = new[] { "Tannery Row", "Copper Row", "Hook Street", "Anchor Walk", "Customs Way" },
                NamesEastWest = new[] { "Ironside Road", "Bakers Cross", "Quay Street", "Chapel Street", "Harbour Road" },
                HasFoundingCross = true,
            },
            new District
            {
                Id = "copper", Name = "Copper Row",
                AvenuesX = new double[] { -40, -20, 0, 20, 40 },
                AvenuesZ = new double[] { 92, 112, 132 },
                NamesNorthSouth = new[] { "Weighhouse Lane", "Saltmarket", "Copper Row", "Lantern Walk", "Basket Street" },
                NamesEastWest = new[] { "The Cut", "Market Road", "Northgate" },
            },
            // IRONSIDE, south past the goods yards. The design doc's brief is
            // three words — **warehouses, logistics, places without witnesses**
            // — and the third one is the only one that is a mechanic.
            //
            // A district is not made quiet by saying so in a name. It is made
            // quiet by two numbers: how far apart the junctions are, and how
            // many people sleep between them. Ironside's blocks are 34m against
            // the Hook's 26 and Copper Row's 20, so there are FEWER corners per
            // acre — long walls, long sightlines, and nowhere for a face to be
            // standing that is not deliberate. And barely anybody lives here
            // (see `Population.Generate`'s weights): the buildings are for goods,
            // and goods do not look out of windows at two in the morning.
            //
            // That is the whole design. Everything the player can do anywhere
            // else, they can do here — the difference is only who sees it, which
            // is the difference this game is made of.
            new District
            {
                Id = "ironside", Name = "Ironside",
                AvenuesX = new double[] { -51, -17, 17, 51 },
                AvenuesZ = new double[] { -160, -126, -92 },
                NamesNorthSouth = new[] { "Foundry Lane", "Smelt Yard", "Crane Street", "Slipway Road" },
                NamesEastWest = new[] { "The Sidings", "Goods Road", "Gate Road" },
            },
            // DOWNTOWN, west along Charter Road (M14, §7: **the day-job world,
            // offices, the machine's lawyers, money laundering**). The inverse
            // of Ironside on the clock: FULL of faces from nine to six and
            // empty after dark, because the mechanic here is respectability —
            // this is where money goes to become deniable, and deniability
            // keeps office hours. Wide formal blocks (30m), because nothing
            // says institution like a street you have to commit to crossing.
            new District
            {
                Id = "downtown", Name = "the Exchange",
                AvenuesX = new double[] { -200, -170, -140, -110 },
                AvenuesZ = new double[] { -26, 4, 34 },
                NamesNorthSouth = new[] { "Chancery Lane", "Exchange Street", "Assay Row", "Bank Walk" },
                NamesEastWest = new[] { "Charter Road", "Office Row", "Court Street" },
            },
            // THE STRIP, east of the Hook (§7: **clubs, gambling, the New
            // crew, information nightlife**). One long spine and short cross
            // streets — a strip is a PROMENADE, somewhere to be seen walking,
            // which is exactly its mechanic: the night circle's day-circle.
            // Everything here is open when everything else is shut, so a face
            // out late has a legitimate reason to exist and a witness pool to
            // go with it. Danny Ro's ground.
            new District
            {
                Id = "strip", Name = "the Parade",
                AvenuesX = new double[] { 96, 118, 140 },
                AvenuesZ = new double[] { -44, -22, 0, 22, 44 },
                NamesNorthSouth = new[] { "Gaslight Walk", "The Parade", "Stage Door Lane" },
                NamesEastWest = new[] { "Cardroom Row", "Marquee Street", "Chorus Lane", "Late Street", "Morning After Lane" },
            },
            // FAIRVIEW, on the north-west rise (§7: **residential hills —
            // where the honest life aspires to live; quiet money**). The
            // district the STRAIGHT LIFE ending is made of: generous blocks,
            // gardens between the junctions, and a witness density that is
            // low but RESPECTABLE — nobody here is out at night, so anybody
            // seen here at night is remembered twice as long. Quiet money
            // does not gossip; it writes letters.
            new District
            {
                Id = "fairview", Name = "Fairview",
                AvenuesX = new double[] { -190, -160, -130 },
                AvenuesZ = new double[] { 96, 126, 156 },
                NamesNorthSouth = new[] { "Laurel Drive", "Fairview Crescent", "Garden Row" },
                NamesEastWest = new[] { "Hillcrest Road", "Vista Terrace", "Quiet Street" },
            },
            // GULLWING, the faded resort waterfront to the south-east (§7:
            // **off-season melancholy, hideouts, endgame turf**). The widest
            // blocks in the city and the fewest people: a promenade built for
            // crowds that stopped coming, which makes it Ironside's cousin
            // with a sadder face — places without witnesses because the
            // witnesses LEFT. Boarding houses that ask no questions; the
            // natural last address for anybody the endgame has made scarce.
            new District
            {
                Id = "gullwing", Name = "Gullwing",
                AvenuesX = new double[] { 96, 128, 160 },
                AvenuesZ = new double[] { -160, -128, -96 },
                NamesNorthSouth = new[] { "Promenade", "Pier Approach", "Shell Walk" },
                NamesEastWest = new[] { "The Esplanade", "Bathhouse Row", "Winter Quay" },
            },
        };

        /// A DISTRICT'S BOUNDS AS THEY ACTUALLY EXIST ON THE MAP — the one
        /// place anything outside this file should ask.
        ///
        /// `AvenuesX`/`AvenuesZ` are UNSCALED SOURCE DATA. `WideBlocks` scales
        /// the whole city about the origin, so a raw read of those arrays
        /// describes a city that was never built. Five separate places read
        /// them raw, and every one of them was wrong in the same direction:
        ///
        ///   `DistrictAt`                  four districts looked 136-184m away
        ///                                 from their own buildings
        ///   `SimDirector.DistrictTour`    aimed seven cameras at bare ground
        ///   `Population.Place`            spawned people off their district
        ///   `WorldBuilder` ground extent  sized the ground plane to the
        ///                                 unscaled map, so the outer
        ///                                 districts stand off the edge of it
        ///
        /// One idea, five implementations, and the four nobody looked at were
        /// the four missing a line. So the scaling stops being something each
        /// caller must remember: ask here and it cannot be forgotten.
        ///
        /// No margin — that is the caller's business and `DistrictAt` is the
        /// only one that wants one.
        public static void BoundsOf(District d, out double minX, out double maxX,
                                    out double minZ, out double maxZ)
        {
            var (kx, kz) = WideBlocks ? (StretchX, StretchZ) : (1.0, 1.0);
            minX = ScaleAbout(d.AvenuesX[0], 0, kx);
            maxX = ScaleAbout(d.AvenuesX[d.AvenuesX.Length - 1], 0, kx);
            minZ = ScaleAbout(d.AvenuesZ[0], 0, kz);
            maxZ = ScaleAbout(d.AvenuesZ[d.AvenuesZ.Length - 1], 0, kz);
        }

        /// The middle avenue crossing of a district, on the map. What a camera
        /// aimed "down the middle of the Exchange" must actually point at.
        public static void CentreOf(District d, out double x, out double z)
        {
            var (kx, kz) = WideBlocks ? (StretchX, StretchZ) : (1.0, 1.0);
            x = ScaleAbout(d.AvenuesX[d.AvenuesX.Length / 2], 0, kx);
            z = ScaleAbout(d.AvenuesZ[d.AvenuesZ.Length / 2], 0, kz);
        }

        /// Which district a position is in, by name, or null out on the cut.
        ///
        /// THE AVENUE ARRAYS ARE UNSCALED SOURCE DATA AND THIS READ THEM RAW,
        /// SO FOUR DISTRICTS HAVE BEEN LOOKING IN THE WRONG PLACE ENTIRELY.
        ///
        /// `WideBlocks` scales the whole city about the origin by `StretchX`
        /// and `StretchZ`. Every other consumer of `AvenuesX`/`AvenuesZ` goes
        /// through `ScaleAbout` — the junction grid, the block rectangles and
        /// the address migration all do. This one did not, so it tested a
        /// scaled position against an unscaled box.
        ///
        /// Near the origin that is a small error and the Hook, Copper Row and
        /// Ironside kept working, which is exactly why it survived. Far from
        /// the origin it is enormous, and the arithmetic matches the measured
        /// world to three figures:
        ///
        ///   district      avenue centre x    x2.15     MEASURED block cluster
        ///   the Exchange           -155     -333.3                    -333.3
        ///   Fairview               -160     -344.0                    -344.0
        ///   the Parade              118      253.7                     254.0
        ///   Gullwing                128      275.2                     275.0
        ///
        /// So the Exchange's BUILDINGS stand 178m from the streets named for
        /// it, and a camera pointed down the Exchange's middle avenue sees
        /// bare ground — which is what all seven district photographs showed
        /// and what `shotDepth` measured before this was understood: the Hook
        /// 24.3m of sight-line, every other district 40.6 to 45.6, the
        /// flat-empty-ground figure predicted for a plain.
        ///
        /// Measured before and after over the real block list: 38 of 52 block
        /// centres were in NO district and four districts held none at all;
        /// scaled, it is 0 of 52 outside and every district has blocks
        /// (16/8/6/6/8/4/4). No two boxes overlap.
        ///
        /// AND THE MARGIN WAS NEVER THE PROBLEM. A previous investigation read
        /// 71% of parcels as district-less and concluded the flat 12m pad was
        /// too narrow against 20-34m block spacing. That reasoning was sound
        /// and the premise was wrong: with the box in the right PLACE, 12, 20
        /// and 26 give identical assignments for all 52 blocks. Widening it
        /// would have treated a symptom, and it destabilised traffic when
        /// tried — which is what stopped it shipping.
        ///
        /// THIS IS NOT A REPORTING FIX. `Traffic.LocalJunctions` keeps
        /// journeys local with this, the patrol beat decides where police work
        /// with it, and `PopulationHost` places people with it. All three have
        /// been running against boxes in the wrong part of the map.
        public static string DistrictAt(double x, double z)
        {
            foreach (var d in Districts)
            {
                BoundsOf(d, out var minX, out var maxX, out var minZ, out var maxZ);
                if (x >= minX - 12 && x <= maxX + 12
                 && z >= minZ - 12 && z <= maxZ + 12) return d.Name;
            }
            return null;
        }

        /// What genuinely cannot move: the bar. It is hand-built, its door and
        /// counter are referenced by name all over the game, and Act I happens
        /// inside it. Every OTHER building is now generated to fill a block,
        /// which is the whole point — the seven hand-placed founding boxes were
        /// laid out when there were two roads, and three of them stood exactly
        /// where an avenue needs to be. Buildings fit inside blocks; streets do
        /// not detour around buildings.
        public static readonly (double X, double Z, double W, double D)[] BuiltMasses =
        {
            (-8, 8, 11, 11),   // the Hook Street pub
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

        /// HOW MANY AUTHORED AVENUES RUN THROUGH A BUILDING THAT CANNOT MOVE.
        ///
        /// `AvenueClear` has sat on the reach ledger since the ledger was
        /// written, as "whether an avenue is unobstructed, for traffic and for
        /// the camera" — which is not what it does. It asks whether an avenue
        /// at a coordinate would cut one of the `BuiltMasses`, and there is
        /// exactly one of those: the Hook Street pub, hand-built, its door and
        /// counter referenced by name all over the game, with Act I happening
        /// inside it.
        ///
        /// NOTHING CALLED IT BECAUSE THE ANSWER IS CURRENTLY YES, BY HAND. The
        /// avenue coordinates are authored arrays and somebody laid them out
        /// around the pub. That is not a reason to delete the check; it is the
        /// definition of a check worth having — the invariant holds because a
        /// person maintained it, and the note above `BuiltMasses` records that
        /// three of the seven original hand-placed boxes stood exactly where an
        /// avenue needed to be. The next person to nudge `AvenuesX` puts a road
        /// through the bar, and the failure is a pub with a carriageway in it,
        /// noticed in a screenshot if at all.
        ///
        /// A COUNT RATHER THAN A REFUSAL, for the reason the clutter probe was
        /// a count first: silently dropping an avenue would replace a visible
        /// fault with an invisible one, and rerouting a grid around a building
        /// is the thing this map deliberately does not do — "buildings fit
        /// inside blocks; streets do not detour around buildings". So the run
        /// reports it and the gate reads it.
        /// AND THE FIRST VERSION OF THIS COUNTED SIX, OF WHICH FOUR WERE THE
        /// INSTRUMENT. `AvenueClear` takes a single coordinate, which was a
        /// complete description of an avenue when this map had one district and
        /// stopped being one the moment it had seven: Copper Row also has an
        /// avenue at x=0, ninety metres north, and a one-coordinate test cannot
        /// tell it from Hook Street. Rule 3 — the ruler before the reading, and
        /// the ruler here is a function whose question the world outgrew.
        ///
        /// So this asks in TWO dimensions, against the district's own extent,
        /// and `AvenueClear` stays as the one-axis helper it actually is.
        ///
        /// WHAT IT FINDS IS REAL AND IT IS TWO. Hook Street runs x -4..4 and the
        /// pub spans -13.5..-2.5, so a metre and a half of the building stands
        /// in the carriageway; Quay Street runs z -4..4 against the pub's
        /// 2.5..13.5, the same again on the other face. The corner of the bar is
        /// in the road, and it has been since the founding cross was laid.
        ///
        /// THE SAME FAULT THE CLUTTER PROBE FOUND FROM THE OTHER END. Eight
        /// pieces of facade dressing could not be pulled out of a carriageway
        /// because their walls were already in it — `dressedStuck`, measured
        /// this afternoon, with the note that "the building is in the road, not
        /// the bin". This is that sentence with a name on it.
        /// Each overlap as `district:axis@coord over Nm`, so the size is legible
        /// rather than a count that could be a rounding or a building.
        public static List<string> MassOverlaps()
        {
            var hits = new List<string>();
            foreach (var d in Districts)
            {
                if (d.AvenuesX == null || d.AvenuesZ == null) continue;
                if (d.AvenuesX.Length == 0 || d.AvenuesZ.Length == 0) continue;
                // The district's footprint, from its own outermost avenues plus
                // a block's reach either side — the same +/-12 the district
                // lookup uses, so two places cannot disagree about where a
                // district is.
                double dMinX = d.AvenuesX[0] - 12, dMaxX = d.AvenuesX[d.AvenuesX.Length - 1] + 12;
                double dMinZ = d.AvenuesZ[0] - 12, dMaxZ = d.AvenuesZ[d.AvenuesZ.Length - 1] + 12;
                foreach (var m in BuiltMasses)
                {
                    double mMinX = m.X - m.W / 2, mMaxX = m.X + m.W / 2;
                    double mMinZ = m.Z - m.D / 2, mMaxZ = m.Z + m.D / 2;
                    if (mMaxX < dMinX || mMinX > dMaxX || mMaxZ < dMinZ || mMinZ > dMaxZ) continue;

                    // `AvenueClear` IS THE AXIS TEST AND IS USED AS ONE, rather
                    // than having its arithmetic copied here. It answers "could
                    // an avenue at this coordinate touch a mass on this axis",
                    // which is exactly the cheap reject this needs; the district
                    // extent above is what it cannot know. Two copies of one
                    // overlap sum is the fault this project names more than any
                    // other, and it would have been invisible — both would
                    // return plausible metres for ever.
                    foreach (var x in d.AvenuesX)
                    {
                        if (AvenueClear(x, northSouth: true)) continue;
                        double over = Math.Min(x + AvenueWidth / 2, mMaxX)
                                    - Math.Max(x - AvenueWidth / 2, mMinX);
                        if (over > 0) hits.Add($"{d.Id}:x@{x:0} over {over:0.0}m");
                    }
                    foreach (var z in d.AvenuesZ)
                    {
                        if (AvenueClear(z, northSouth: false)) continue;
                        double over = Math.Min(z + AvenueWidth / 2, mMaxZ)
                                    - Math.Max(z - AvenueWidth / 2, mMinZ);
                        if (over > 0) hits.Add($"{d.Id}:z@{z:0} over {over:0.0}m");
                    }
                }
            }
            return hits;
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

            // 1. Every district's grid. The Hook's junctions keep their
            // original ids ("j2_2" and the rest) because the traffic model, the
            // bus circuit and a pile of tests all name them — a district system
            // that renamed the founding grid would have been a rewrite wearing
            // a refactor's clothes.
            _blocks = new List<Block>();
            foreach (var d in Districts)
            {
                string prefix = d.Id == "hook" ? "j" : d.Id + "_j";
                // The re-plan lives HERE and nowhere else: the authored tables
                // stay exactly as written (they are the layout's intent), and
                // the scale is applied as they are read. One place to revert,
                // one place to read, and the blocks and the addresses below
                // consume the same two helpers.
                var (kx, kz) = BlockScale(d);
                var (cx0, cz0) = DistrictCentre(d);
                for (int i = 0; i < d.AvenuesX.Length; i++)
                    for (int j = 0; j < d.AvenuesZ.Length; j++)
                        Add(new StreetNode
                        {
                            Id = $"{prefix}{i}_{j}",
                            X = ScaleAbout(d.AvenuesX[i], cx0, kx),
                            Z = ScaleAbout(d.AvenuesZ[j], cz0, kz),
                            IsJunction = true,
                        });

                // The avenues between them. The founding cross keeps its own
                // class, because it is narrower and already built.
                for (int i = 0; i < d.AvenuesX.Length; i++)
                    for (int j = 0; j + 1 < d.AvenuesZ.Length; j++)
                        Link($"{prefix}{i}_{j}", $"{prefix}{i}_{j + 1}",
                            d.HasFoundingCross && d.AvenuesX[i] == 0 ? "street" : "avenue");
                for (int j = 0; j < d.AvenuesZ.Length; j++)
                    for (int i = 0; i + 1 < d.AvenuesX.Length; i++)
                        Link($"{prefix}{i}_{j}", $"{prefix}{i + 1}_{j}",
                            d.HasFoundingCross && d.AvenuesZ[j] == 0 ? "street" : "avenue");

                // The blocks between the streets — the buildable ground.
                double halfW = AvenueWidth / 2.0;
                for (int i = 0; i + 1 < d.AvenuesX.Length; i++)
                    for (int j = 0; j + 1 < d.AvenuesZ.Length; j++)
                        _blocks.Add(new Block
                        {
                            MinX = ScaleAbout(d.AvenuesX[i], cx0, kx) + halfW,
                            MaxX = ScaleAbout(d.AvenuesX[i + 1], cx0, kx) - halfW,
                            MinZ = ScaleAbout(d.AvenuesZ[j], cz0, kz) + halfW,
                            MaxZ = ScaleAbout(d.AvenuesZ[j + 1], cz0, kz) - halfW,
                        });
            }

            // 2. The bridges. TWO, and only two, because a chokepoint is a place
            // where things can happen — somebody waiting at a bridge is a scene,
            // and somebody waiting on an open grid is a man standing in a road.
            Link("j1_4", "copper_j1_0", "avenue");   // the west bridge
            Link("j3_4", "copper_j3_0", "avenue");   // the east bridge

            // South, the two goods roads down off Ironside Road — named for
            // where they go, which is how the Hook has always talked about the
            // place it sends its cargo and does not visit.
            Link("j1_0", "ironside_j1_2", "avenue");
            Link("j3_0", "ironside_j2_2", "avenue");

            // M14: the four outer districts, each joined by the fewest roads
            // its character allows — chokepoints are places things can happen.
            //
            // Downtown, west off the Hook: TWO formal roads, because this is
            // the commuter artery and a district of offices with one door
            // would be a joke the map was telling about itself.
            Link("j0_2", "downtown_j3_1", "avenue");   // Charter Road
            Link("j0_1", "downtown_j3_0", "avenue");   // Court Street approach
            // The Strip, east off the Hook: two, and both stay lit all night.
            Link("j4_2", "strip_j0_2", "avenue");      // Marquee Street west end
            Link("j4_1", "strip_j0_1", "avenue");      // Cardroom Row approach
            // Fairview, up the rise: ONE road from Copper Row and one long
            // drive down to Downtown. Quiet money likes one road in.
            Link("copper_j0_1", "fairview_j2_1", "avenue");   // the hill road
            Link("downtown_j1_2", "fairview_j1_0", "avenue"); // the long drive
            // Gullwing: the winter road down from the Strip, and the goods
            // spur across from Ironside. Both feel longer than they are.
            Link("strip_j1_0", "gullwing_j1_2", "avenue");    // the winter road
            Link("ironside_j3_1", "gullwing_j0_1", "avenue"); // the goods spur

            // 2b. AND EVERY ADDRESS GETS OFF THE ROAD FIRST.
            //
            // Thirty-one of the fifty-two planned places had an authored
            // coordinate inside a carriageway, and twenty-two of them then put
            // a building face there — `placeStopsInRoad=31 placeFacesInRoad=22`
            // in every kept verdict, the second read as the fault for three
            // builds while the first sat beside it saying what it actually was.
            // No placement rule fixes an address in the middle of a road: the
            // door can only be walked away from the stop the schedules send
            // people to, which is a worse game than the facade.
            //
            // HERE, AND THE ORDER IS THE WHOLE REASON. Every driveable edge
            // exists by this line and no `stop_` node does yet, so the snap
            // reads a graph that does not depend on the coordinates it is
            // about to move, and the loop below then builds the lanes from the
            // corrected ones. Doing it in `HookMap` would have been circular;
            // doing it in the world builder would have moved the geometry and
            // left the schedules pointing at the road.
            MigrateAddresses();
            SetPlacesBackFromRoads();

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

        /// HOW FAR ONTO THE PAVEMENT AN ADDRESS IS PUT — half a pavement, a
        /// doorstep rather than a forecourt. Kept small on purpose: the point
        /// is to be off the tarmac, not to be set back into the block.
        public const double PavementStand = 1.6;

        /// AND HOW FAR AN ADDRESS IS ALLOWED TO TRAVEL BEFORE IT STOPS BEING
        /// THAT ADDRESS. Chosen from the series rather than picked, and the
        /// series is the argument — every value run against the real map:
        ///
        ///     cap    still in a road    worst actual move
        ///     5m         11                  3.94m
        ///     6m          7                  5.60m
        ///     8m          3                  6.66m
        ///    12m          3                 11.20m
        ///
        /// 8 is the knee. It clears twenty-eight of the thirty-one with a
        /// median move of 3.60m, and paying four more metres of drift buys
        /// nothing at all. The three that refuse are the same three at every
        /// cap above 8 — `cut_bridge`, `night_gate` and `clerks_steps`, which
        /// are a bridge, a gate and a flight of steps, and a right of way is
        /// where those belong. A refusal is reported rather than silent.
        public const double MaxAddressDrift = 8.0;

        /// How many addresses had to be moved off a carriageway, how far the
        /// worst one went, and how many refused because moving them would have
        /// taken them somewhere that is not their address any more.
        ///
        /// `AddressesRefused` is the one that must be read beside the others:
        /// a refused address is STILL IN THE ROAD, so a run reporting many
        /// moves and no refusals is a different world from one reporting many
        /// of both, and a single "moved" count cannot tell them apart.
        public static int AddressesSetBack, AddressesRefused;
        /// Corners, left where they were ON PURPOSE. A third category, not a
        /// refusal: a refused address wanted to move and could not, and one
        /// of these was never asked to. Folding them together would have
        /// made a deliberate exemption look like nine failures.
        public static int AddressesLeftInRoad;
        public static double AddressDriftWorst;
        static readonly List<double> _addressDrifts = new List<double>();

        /// The typical move beside the worst. A worst of seven with a median of
        /// three and a half is a handful of bad addresses; a median of seven
        /// would be the authored map disagreeing with the street graph
        /// wholesale, and those want different fixes.
        public static double AddressDriftMedian
        {
            get
            {
                if (_addressDrifts.Count == 0) return -1;
                var v = new List<double>(_addressDrifts);
                v.Sort();
                return v[v.Count / 2];
            }
        }

        /// MOVE ONE POINT OFF THE CARRIAGEWAY, and nothing else.
        ///
        /// The set-back below does this for every registered address; this is
        /// the same rule for a single authored coordinate, because the cast's
        /// waypoints have the identical fault and are not in `HookMap`.
        /// Measured: three of the six positions authored as offsets from the
        /// bar door — "across from the bar, coat still on", "one drink, loudly"
        /// — land in Hook Street, and this moves them 1.6 to 2.6 metres, which
        /// keeps them at the pub door and takes them off the road.
        ///
        /// PERPENDICULAR ONLY, so a point's position ALONG a street survives.
        /// Two people standing at different depths into the same road do end up
        /// at the same kerb, and that is correct — they are both at the kerb,
        /// and the spread ring is what separates two people at one place.
        ///
        /// Returns the point unchanged when it is already clear, so a caller
        /// can pass everything through it without deciding first.
        public static void OffTheCarriageway(double x, double z,
                                             out double outX, out double outZ)
        {
            outX = x; outZ = z;
            for (int pass = 0; pass < 6; pass++)
            {
                if (!OnRoad(outX, outZ)) return;
                if (!NearestOnRoad(outX, outZ, out var nx, out var nz, out var width)) return;
                double ox = outX - nx, oz = outZ - nz;
                double len = Math.Sqrt(ox * ox + oz * oz);
                if (len < 0.01) { ox = 1; oz = 0; len = 1; }
                ox /= len; oz /= len;
                double want = width / 2.0 + PavementStand;
                outX = nx + ox * want; outZ = nz + oz * want;
            }
        }

        /// Put every address that stands in a carriageway onto the pavement
        /// beside the road it is addressed from.
        ///
        /// ITERATED, because an address at a JUNCTION is inside two roads and
        /// clearing one puts it inside the other. Each pass steps off whichever
        /// road it is currently in. One pass cleared 17 of 31; six passes clear
        /// 28, and the ones that never settle are boxed in rather than badly
        /// placed.
        ///
        /// IDEMPOTENT BY CONSTRUCTION — the loop's condition is "is this point
        /// on a road", so a second call over already-corrected coordinates does
        /// nothing and moves nobody. That matters because `Ensure` can be
        /// reached from anywhere and a normalisation that drifted a little
        /// further each time would be the worst kind of bug to find.
        /// THE MIGRATION CONTRACT, and the whole reason the re-plan is a
        /// scale rather than a re-authoring. Every address moves by exactly
        /// the transform its own district's grid moved by, so it keeps the
        /// street it is on, the side it is on and how far along it stands —
        /// no coordinate is guessed, and the sixty-one authored places do not
        /// need re-typing.
        ///
        /// ONCE. `Ensure` runs the builder once per process, but a place is
        /// mutable and shared, so a second pass would scale an already-scaled
        /// address and put the letter-writer in the sea.
        ///
        /// The Hook's founding block is exempt: the pub is hand-built at
        /// fixed coordinates in `WorldBuilder`, Act I happens inside it, and
        /// its door, counter and step are authored beside it. Scaling the
        /// door away from the building it belongs to would be the same class
        /// of fault as a name plate on the wrong wall.
        static bool _addressesMigrated;

        static void MigrateAddresses()
        {
            if (!WideBlocks || _addressesMigrated) return;
            _addressesMigrated = true;
            foreach (var place in HookMap.Places)
            {
                // The founding block, where the pub is hand-built.
                if (Math.Abs(place.X) < 14 && Math.Abs(place.Z) < 14) continue;
                var d = DistrictFor(place.X, place.Z);
                if (d == null) continue;
                var (kx, kz) = BlockScale(d);
                var (cx, cz) = DistrictCentre(d);
                place.X = ScaleAbout(place.X, cx, kx);
                place.Z = ScaleAbout(place.Z, cz, kz);
            }
        }

        /// Is this junction on the OUTER RING of its district — the first or
        /// last avenue line on either axis?
        ///
        /// Written for `Signals.HasLights`, which asked `Math.Abs(v) < 52.0`
        /// and meant exactly this. 52 was the Hook's outermost avenue when the
        /// Hook was the whole city; the topology stretch moved that line to
        /// 111.8 and the constant would have quietly switched off every
        /// traffic light in the game — a rule that reads a REMEMBERED
        /// COORDINATE rather than the map it is about, which is the fault
        /// this file has now produced twice in one change.
        public static bool OnOuterRing(StreetNode n)
        {
            if (n == null) return false;
            Ensure();
            foreach (var d in Districts)
            {
                var (kx, kz) = BlockScale(d);
                var (cx, cz) = DistrictCentre(d);
                double x0 = ScaleAbout(d.AvenuesX[0], cx, kx);
                double x1 = ScaleAbout(d.AvenuesX[d.AvenuesX.Length - 1], cx, kx);
                double z0 = ScaleAbout(d.AvenuesZ[0], cz, kz);
                double z1 = ScaleAbout(d.AvenuesZ[d.AvenuesZ.Length - 1], cz, kz);
                if (n.X < x0 - 1 || n.X > x1 + 1 || n.Z < z0 - 1 || n.Z > z1 + 1) continue;
                return Math.Abs(n.X - x0) < 0.01 || Math.Abs(n.X - x1) < 0.01
                    || Math.Abs(n.Z - z0) < 0.01 || Math.Abs(n.Z - z1) < 0.01;
            }
            return false;
        }

        /// Which district an authored coordinate belongs to, by the UNSCALED
        /// tables — because that is the frame the coordinate was written in,
        /// and asking the scaled map would be asking where it has already
        /// moved to.
        static District DistrictFor(double x, double z)
        {
            foreach (var d in Districts)
            {
                double minX = d.AvenuesX[0] - 20, maxX = d.AvenuesX[d.AvenuesX.Length - 1] + 20;
                double minZ = d.AvenuesZ[0] - 20, maxZ = d.AvenuesZ[d.AvenuesZ.Length - 1] + 20;
                if (x >= minX && x <= maxX && z >= minZ && z <= maxZ) return d;
            }
            return null;
        }

        static void SetPlacesBackFromRoads()
        {
            AddressesSetBack = AddressesRefused = AddressesLeftInRoad = 0;
            AddressDriftWorst = 0;
            _addressDrifts.Clear();
            foreach (var place in HookMap.Places)
            {
                // A CORNER BELONGS IN THE ROAD, and moving one is the fault
                // rather than the fix.
                //
                // The first version snapped everything and moved nine of them:
                // `crossing`, `cab_rank`, `cut_bridge`, `night_gate`,
                // `clerks_steps`, `stage_door`, `gaslight_end`, `garden_gate`,
                // `esplanade_shelter`. Read the names — a crossing, a cab rank,
                // a bridge, a gate, a flight of steps, a stage door, the end of
                // a street, a garden gate and a shelter. Every one is a thing
                // that stands at or in a right of way by definition, and
                // `crossing` was pushed 4.6m off the carriageway it IS.
                //
                // `Kind` already carries the distinction and the district
                // builder already reads it: a corner gets a 4x3x4 box that its
                // own comment calls "a shelter, not a building". A thing with
                // no facade cannot have a facade in a road.
                //
                // MEASURED, AND IT IS A BETTER RULE THAN THE DRIFT CAP. With
                // corners exempt, EIGHT planned stops remain in a carriageway
                // and all eight are corners — so every address with a building
                // on it is clear, and the residue is exactly the set that
                // should be there. The cap stays for the genuinely boxed-in
                // case, but it is no longer what is doing the work.
                if (place.Kind == "corner") { AddressesLeftInRoad++; continue; }
                double x = place.X, z = place.Z;
                bool moved = false;
                for (int pass = 0; pass < 6; pass++)
                {
                    if (!OnRoad(x, z)) break;
                    if (!NearestOnRoad(x, z, out var nx, out var nz, out var width)) break;
                    double ox = x - nx, oz = z - nz;
                    double len = Math.Sqrt(ox * ox + oz * oz);
                    // DEAD ON THE CENTRELINE, which is a real case — an address
                    // authored at the middle of an avenue has no outward
                    // direction of its own. Any perpendicular will do and the
                    // next pass corrects the choice if it was the worse one.
                    if (len < 0.01) { ox = 1; oz = 0; len = 1; }
                    ox /= len; oz /= len;
                    double want = width / 2.0 + PavementStand;
                    double cx = nx + ox * want, cz = nz + oz * want;
                    double drift = Math.Sqrt((cx - place.X) * (cx - place.X)
                                             + (cz - place.Z) * (cz - place.Z));
                    if (drift > MaxAddressDrift) break;
                    x = cx; z = cz; moved = true;
                }
                if (!moved) { if (OnRoad(x, z)) AddressesRefused++; continue; }
                double total = Math.Sqrt((x - place.X) * (x - place.X)
                                         + (z - place.Z) * (z - place.Z));
                place.X = x; place.Z = z;
                AddressesSetBack++;
                _addressDrifts.Add(total);
                if (total > AddressDriftWorst) AddressDriftWorst = total;
                if (OnRoad(x, z)) AddressesRefused++;
            }
        }

        /// The closest point on a CARRIAGEWAY, and how wide that carriageway is.
        ///
        /// `NearestOnStreet`'s sibling, and the distinction is the same one
        /// `OnRoad` makes against `OnStreet`: lanes cross block interiors to
        /// reach doors, so the nearest STREET to a building standing in an
        /// avenue is frequently the service lane behind it. Anything asking
        /// "how do I get off the road" has to ask about roads.
        ///
        /// Measured, not supposed: snapping the district's addresses off the
        /// nearest STREET cleared 14 of the 31 that stand in a carriageway,
        /// because places beside a lane snapped relative to the lane's width
        /// and landed back in the avenue. Off the nearest ROAD it is 28 of 31.
        public static bool NearestOnRoad(double x, double z,
                                         out double outX, out double outZ, out double width)
        {
            Ensure();
            outX = x; outZ = z; width = 0;
            double best = double.MaxValue;
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
                double d = (px - x) * (px - x) + (pz - z) * (pz - z);
                if (d < best) { best = d; outX = px; outZ = pz; width = e.Width; }
            }
            return best < double.MaxValue;
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
        /// The name of the road running along this coordinate. Now district-aware:
        /// x=0 is Hook Street in the Hook and Copper Row across the cut, which is
        /// how streets actually work and is the reason this takes a hint.
        ///
        /// `near` is a coordinate on the OTHER axis, used only to decide which
        /// district is being asked about. Without it a bare coordinate is
        /// genuinely ambiguous once there is more than one grid, and guessing
        /// would put the wrong plate on a corner.
        public static string NameOf(double coord, bool northSouth, double near = 0)
        {
            foreach (var d in Districts)
            {
                var cross = northSouth ? d.AvenuesZ : d.AvenuesX;
                if (near < cross[0] - 14 || near > cross[cross.Length - 1] + 14) continue;
                var line = northSouth ? d.AvenuesX : d.AvenuesZ;
                var names = northSouth ? d.NamesNorthSouth : d.NamesEastWest;
                for (int i = 0; i < line.Length && i < names.Length; i++)
                    if (Math.Abs(line[i] - coord) < 0.001) return names[i];
            }
            return null;
        }

        /// What a person standing here would call where they are. Junctions read
        /// as a corner of two streets; anywhere else takes the nearest.
        public static string AddressOf(double x, double z)
        {
            Ensure();
            string ns = NameOf(x, true, z), ew = NameOf(z, false, x);
            if (ns != null && ew != null) return $"{ns} at {ew}";
            if (ns != null) return ns;
            if (ew != null) return ew;

            double bestD = double.MaxValue;
            string best = null;
            foreach (var dist in Districts)
            {
                foreach (var ax in dist.AvenuesX)
                {
                    double d = Math.Abs(ax - x) + DistancePenalty(dist, z, northSouth: true);
                    if (d < bestD) { bestD = d; best = NameOf(ax, true, z); }
                }
                foreach (var az in dist.AvenuesZ)
                {
                    double d = Math.Abs(az - z) + DistancePenalty(dist, x, northSouth: false);
                    if (d < bestD) { bestD = d; best = NameOf(az, false, x); }
                }
            }
            return best;
        }

        /// How far outside a district's own extent the query sits. Keeps a
        /// position in the Hook from being told it is on a Copper Row street
        /// that merely happens to share an x.
        static double DistancePenalty(District d, double along, bool northSouth)
        {
            var cross = northSouth ? d.AvenuesZ : d.AvenuesX;
            double lo = cross[0], hi = cross[cross.Length - 1];
            if (along < lo) return lo - along;
            if (along > hi) return along - hi;
            return 0;
        }

        /// The two streets that meet at a junction, for the plates on its posts.
        public static bool NamesAt(StreetNode n, out string northSouth, out string eastWest)
        {
            northSouth = eastWest = null;
            if (n == null || !n.IsJunction) return false;
            northSouth = NameOf(n.X, true, n.Z);
            eastWest = NameOf(n.Z, false, n.X);
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
