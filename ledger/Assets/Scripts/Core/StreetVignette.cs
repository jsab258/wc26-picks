using System;
using System.Collections.Generic;
using System.Globalization;

namespace Ledger.Core
{
    /// THE D1b STREET VIGNETTE, TURNED FROM THE SHARED JSON INTO A LIST OF
    /// PRIMITIVES, IN THE LAYER THE TESTS CAN REACH.
    ///
    /// NAME COLLISION, SAID ONCE SO NOBODY HAS TO FIND IT TWICE. The token
    /// `Vignette` already means the LENS vignette in this repository
    /// (`LightModel.VignetteCorner`, `VignetteParam`, the post shader's
    /// `_Vignette`). That is a different thing entirely. Everything belonging
    /// to the D1b street scene is prefixed `StreetVignette`, so a grep for
    /// `StreetVignette` gets this family and only this family.
    ///
    /// WHY THE ARITHMETIC IS HERE AND NOT IN THE EMITTER. The standing rule
    /// from 25 August: measurement arithmetic and formatting live where the
    /// tests run. The Unity layer does not compile in the review container, so
    /// a levels calculation written in `StreetVignetteHost` would ship unrun,
    /// and an unrun calculation producing a plausible metre value is the
    /// silent-instrument failure. This class does the section, the levels, the
    /// bay layout and the scatter; the emitter supplies only membership, order
    /// and live state (which prefab, which material, what a raycast hit).
    ///
    /// WHY IT READS A FILE RATHER THAN HOLDING CONSTANTS. `game-design/
    /// decision-D1b-rescope.md` makes this the admissibility rule of the whole
    /// engine comparison: every object in each engine arrives via its
    /// generator from ONE shared JSON, and a hand-edited scene disqualifies
    /// the still. A dimension hard-coded here would be a dimension the Unreal
    /// emitter cannot read, which is the same failure wearing a nicer hat. So
    /// every number below comes from `production/specs/vignette-scene.json`
    /// and there is no default for any of them: a missing key is an ERROR, not
    /// a fallback, because a fallback would let the two engines quietly build
    /// two different streets and both stills would look fine.
    public static class StreetVignette
    {
        /// One primitive. The emitter turns each of these into exactly one
        /// object, so the piece count in the plan and the object count in the
        /// scene are the same number and a gate can say so.
        ///
        /// TWO SHAPES ONLY, box and cylinder. Every engine has both as a
        /// built-in, so neither emitter needs a mesh asset to stand the scene
        /// up, and neither can differ from the other by importing a different
        /// one.
        public struct Piece
        {
            public string Bom;       // the bill-of-materials line that authorises this
            public string Name;      // unique instance name; the still and the log share it
            public string Shape;     // "box" or "cyl"
            public string Surface;   // AssetLibrary logical surface name
            public double X, Y, Z;   // CENTRE, metres, in the JSON's frame
            public double SX, SY, SZ;// full size, metres, before rotation
            public double PitchDeg;  // about +x, positive tips the +z end DOWN
            public double YawDeg;    // about +y, compass from +x
            // ABOUT +z, AND IT EXISTS SO A PIPE CAN LIE DOWN. A cylinder's
            // axis is local +y in both engines, so the only way to express a
            // gutter, an aerial boom or a handrail is to ROTATE it: roll 90
            // lays the axis along the street (x), pitch 90 lays it across
            // (z). Without this field the alternative is to stretch one
            // diameter to the pipe's length, which renders as a flattened
            // disc and reads as a pipe only in the piece count.
            public double RollDeg;
            public string Edge;      // lateral band: the axis placement varies on
            public string Region;    // longitudinal band: the other axis
            public bool Emissive;    // the lantern bowls, and nothing else
        }

        /// ONE PROBE POINT UNDER ONE PIECE THAT IS SUPPOSED TO BE STANDING ON
        /// SOMETHING. This is half of the placement instrument and it is the
        /// half that is easy to leave out: `FootY` is what the PLAN says the
        /// underside sits at, and the emitter answers separately whether there
        /// is any ground under (X,Z) at all. Eight blocks once hung over open
        /// sea at a foot gap of exactly 0.00 because only the first question
        /// was ever asked.
        public struct Foot
        {
            public string Name, Bom, Edge, Region;
            public double X, Z, FootY;
        }

        /// WHERE A CAMERA STANDS AND WHERE IT LOOKS. The name has now dodged
        /// TWO collisions and the second is the interesting one. It is not
        /// `Camera`, because every Game file carries both `using UnityEngine`
        /// and `using Ledger.Core`, so a Core type called `Camera` is CS0104
        /// at player-build time and nothing local can see it;
        /// `ledger/lint-usings.py` caught that before a build did. It is then
        /// not `Vantage` either, because `Observation.cs` line 145 already
        /// declares a TOP-LEVEL `Ledger.Core.Vantage`, which is the geometry
        /// of one witness and a different idea entirely. Two structs of one
        /// name in one namespace, one nested and one not, is legal C# and is
        /// a trap for every later reader. `tools/lint-nested.py` is what
        /// found it, by going red on its own accepting case.
        public struct ShotVantage
        {
            public string Id;
            public double X, Z, EyeHeightM, YawDeg, PitchDeg, FovDeg;
        }

        public struct Condition
        {
            public string Id, Hdri;
            public bool SunOn, LanternsOn, WindowsOn;
            public double Wetness, FogDensity;
        }

        public struct Shot
        {
            public string Id, CameraId, ConditionId;
        }

        /// The street's cross section, computed once from the JSON widths and
        /// falls. NOTHING ELSE IN THIS FILE MAY RE-DERIVE A LEVEL: two copies
        /// of "where is the top of the kerb" is the shape this project keeps
        /// finding wrong on the copy nobody opens.
        public sealed class StreetSection
        {
            public double LengthM;
            public double HalfWidthM, CrossFall, ChannelWidthM;
            public double KerbUpstandM, KerbWidthM, KerbDepthM, KerbBlockM;
            public double FootwayWidthM, FootwayCrossFall;

            /// y=0 is the carriageway crown, so the channel is NEGATIVE and
            /// the footway is positive. Both fall out of the two crossfalls
            /// and are never written down anywhere else.
            public double ChannelY => -HalfWidthM * CrossFall;
            public double KerbTopY => ChannelY + KerbUpstandM;
            public double KerbFaceZ => HalfWidthM;
            public double FootwayFrontZ => HalfWidthM + KerbWidthM;
            public double BuildingLineZ => FootwayFrontZ + FootwayWidthM;
            public double FootwayBackY => KerbTopY + FootwayWidthM * FootwayCrossFall;

            /// The dropped kerb and the gully recess, both of which change the
            /// kerb top at a named x on a named side and nowhere else.
            public string DroppedSide;
            public double DroppedCentreX, DroppedWidthM, DroppedFlushM;
            public int DroppedTaperBlocks;
            public string GullySide;
            public double GullyCentreX, GullyGrateM, GullyRecessM, GullyDishM;

            /// WHERE THE TOP OF THE KERB IS AT THIS x ON THIS SIDE.
            ///
            /// Three cases and they are ordered by how local they are: the
            /// gully recess is 0.40 m wide and wins over the crossover, the
            /// crossover is metres wide and wins over the run, and the run is
            /// the whole street. Written once here because both the kerb
            /// emitter and the ground query need the answer and they must not
            /// be able to disagree.
            public double KerbTopAt(double x, string side)
            {
                if (side == GullySide && Math.Abs(x - GullyCentreX) <= GullyGrateM * 0.5)
                    return KerbTopY - GullyRecessM;
                if (side == DroppedSide)
                {
                    double d = Math.Abs(x - DroppedCentreX);
                    double flat = DroppedWidthM * 0.5;
                    double taper = DroppedTaperBlocks * KerbBlockM;
                    double dropped = ChannelY + DroppedFlushM;
                    if (d <= flat) return dropped;
                    if (d <= flat + taper && taper > 0)
                        return dropped + (KerbTopY - dropped) * ((d - flat) / taper);
                }
                return KerbTopY;
            }
        }

        /// A rectangle of ground behind a building line that the scene has to
        /// emit or the buildings standing on it have no datum under them. Not
        /// a JSON field: it is the block's own footprint, so it cannot drift
        /// away from the block it exists for.
        public struct Plot
        {
            public double X0, X1, Z0, Z1, Y;
            public string Side;
        }

        public sealed class Plan
        {
            public string Error;
            public StreetSection Sec;
            public readonly List<Piece> Pieces = new List<Piece>();
            public readonly List<Foot> Feet = new List<Foot>();
            public readonly List<ShotVantage> Cameras = new List<ShotVantage>();
            public readonly List<Condition> Conditions = new List<Condition>();
            public readonly List<Shot> Shots = new List<Shot>();
            /// Which BOM lines this plan actually emitted, and how many
            /// pieces each contributed. A line with a zero here is a line
            /// that was named and never placed, which is exactly the thing a
            /// bill of materials exists to make visible.
            public readonly Dictionary<string, int> PerBom = new Dictionary<string, int>();
            internal readonly List<Plot> Plots = new List<Plot>();
            /// The lantern colour, carried through from the JSON so the
            /// emitter never picks an amber by eye. Gamma-encoded sRGB, which
            /// is what a Unity `Color` literal means in a gamma project; the
            /// linear triple is in the JSON beside it for an emitter whose
            /// project is linear.
            public double LampR, LampG, LampB, LampRangeM, LampIntensity;
            public double SunElevationDeg, SunAzimuthDeg;
            /// Metres of world per texture repeat, per logical surface, with
            /// the fallback for a surface the table does not name. Here
            /// rather than in either emitter for the same reason every other
            /// dimension is: two engines with two tiling tables are two
            /// different streets photographed from the same place.
            public double TilingDefaultM = 3.0;
            public readonly Dictionary<string, double> TilingM = new Dictionary<string, double>();

            public double TileMetres(string surface)
            {
                if (surface != null && TilingM.TryGetValue(surface, out double m) && m > 0) return m;
                return TilingDefaultM;
            }

            /// IS THERE GROUND UNDER (x,z), AND AT WHAT HEIGHT.
            ///
            /// The analytic datum. The emitter raycasts the geometry it
            /// actually built and compares; that comparison is the whole
            /// point, so this must never be derived FROM the geometry or the
            /// instrument would be measuring itself.
            public bool GroundAt(double x, double z, out double y, out string edge)
            {
                y = 0; edge = "none";
                var s = Sec;
                double az = Math.Abs(z);
                string side = z >= 0 ? "east" : "west";
                if (x >= 0 && x <= s.LengthM)
                {
                    if (az <= s.HalfWidthM - s.ChannelWidthM)
                    {
                        y = -az * s.CrossFall; edge = side + "_carriageway"; return true;
                    }
                    if (az <= s.HalfWidthM)
                    {
                        y = -az * s.CrossFall; edge = side + "_channel";
                        if (side == s.GullySide && Math.Abs(x - s.GullyCentreX) <= s.GullyGrateM * 0.5)
                            y -= s.GullyDishM;
                        return true;
                    }
                    if (az <= s.FootwayFrontZ)
                    {
                        y = s.KerbTopAt(x, side); edge = side + "_kerb"; return true;
                    }
                    if (az <= s.BuildingLineZ)
                    {
                        // The footway keeps its own fall whatever the kerb in
                        // front of it is doing. A real crossover ramps the
                        // footway too; that is a named next step and its
                        // absence is 125 mm over 2 m, not a level error.
                        y = s.KerbTopY + (az - s.FootwayFrontZ) * s.FootwayCrossFall;
                        edge = side + "_footway"; return true;
                    }
                }
                foreach (var p in Plots)
                    if (x >= p.X0 && x <= p.X1 && az >= Math.Min(Math.Abs(p.Z0), Math.Abs(p.Z1))
                        && az <= Math.Max(Math.Abs(p.Z0), Math.Abs(p.Z1))
                        && (z >= 0) == (p.Side == "east"))
                    {
                        y = p.Y; edge = p.Side + "_plot"; return true;
                    }
                return false;
            }

            internal void Add(Piece p)
            {
                Pieces.Add(p);
                PerBom.TryGetValue(p.Bom, out int n);
                PerBom[p.Bom] = n + 1;
            }

            /// FOUR CORNERS AND THE CENTRE OF A FOOTPRINT, which is five
            /// probes rather than one because the failure this instrument
            /// exists for is a footprint half on and half off the ground. A
            /// centre-only probe cannot see it, and that is how the eight
            /// blocks over open sea passed.
            internal void Foot5(Piece p, double footY)
            {
                double hx = p.SX * 0.5, hz = p.SZ * 0.5;
                // The half-extents swap at yaw 90; every other yaw is probed
                // UNROTATED. Nothing footed carries yaw 90 today, and the
                // litter (G8) carries an arbitrary yaw, so its true footprint
                // reaches up to 6 cm beyond where its probes look on the
                // widest piece at 45 degrees; queue 033 rotates the corners.
                if (Math.Abs(((p.YawDeg % 180) + 180) % 180 - 90) < 1e-6) { var t = hx; hx = hz; hz = t; }
                double[] dx = { 0, -hx, hx, -hx, hx };
                double[] dz = { 0, -hz, -hz, hz, hz };
                for (int i = 0; i < 5; i++)
                    Feet.Add(new Foot
                    {
                        Name = p.Name, Bom = p.Bom, Edge = p.Edge, Region = p.Region,
                        X = p.X + dx[i], Z = p.Z + dz[i], FootY = footY
                    });
            }
        }

        /// The longitudinal band a metre position falls in. Six-metre bands
        /// because that is the bay module both terraces are laid out on, so a
        /// per-region row lines up with a unit of frontage rather than with an
        /// arbitrary slice of road.
        public const double RegionSpanM = 6.0;

        public static string RegionOf(double x)
        {
            int b = (int)Math.Floor(x / RegionSpanM);
            if (b < 0) b = 0;
            return string.Format(CultureInfo.InvariantCulture, "x{0:00}_{1:00}",
                                 b * (int)RegionSpanM, (b + 1) * (int)RegionSpanM);
        }

        /// WHAT SHAPES A PLAN ASKED FOR, IN ONE LINE, AND HOW MANY OF ITS
        /// PIPES ARE LYING DOWN.
        ///
        /// A piece count cannot see the failure this line exists for. Every
        /// cylinder's axis is local +y in both engines, so a gutter, an
        /// aerial boom or a handrail is a cylinder ROTATED: roll about +z
        /// lays the axis along the street, pitch about +x lays it across.
        /// An emitter that drops the rotation stands the same number of
        /// pieces up and every pipe among them is a flattened disc. So the
        /// count of rolled and pitched cylinders is printed beside the count
        /// of cylinders, and the verdict can say how many pipes were laid.
        ///
        /// WHOLE-PLAN COUNTS, one line per plan, never per piece. The three
        /// cylinder columns partition the cylinders exactly (roll is
        /// classified first, so a piece carrying both is counted as rolled
        /// and only once), and `box + cyl + unknown` is `pieces`.
        ///
        /// FORMATTED HERE, not in the emitter, because this layer is the one
        /// CoreTests can run: a formatter written in the Unity layer ships
        /// unrun, and an unrun formatter printing a plausible string is the
        /// silent-instrument failure this project keeps paying for.
        public static string ShapeReport(List<Piece> pieces)
        {
            int box = 0, cyl = 0, unknown = 0, rolled = 0, pitched = 0, upright = 0;
            foreach (var p in pieces)
            {
                if (p.Shape == "box") { box++; continue; }
                if (p.Shape != "cyl") { unknown++; continue; }
                cyl++;
                if (Math.Abs(p.RollDeg) > 1e-9) rolled++;
                else if (Math.Abs(p.PitchDeg) > 1e-9) pitched++;
                else upright++;
            }
            return string.Format(CultureInfo.InvariantCulture,
                "shapes pieces={0} box={1} cyl={2} unknown={3} "
                + "cylRolled={4} cylPitched={5} cylUpright={6}",
                pieces.Count, box, cyl, unknown, rolled, pitched, upright);
        }

        /// READ THE SHARED SCENE AND LAY IT OUT.
        ///
        /// Returns a plan whose `Error` is non-null when the JSON is missing
        /// something. It never guesses: see the class comment.
        public static Plan Read(string json)
        {
            var plan = new Plan();
            Dictionary<string, object> root;
            try { root = MiniJson.AsObject(MiniJson.Deserialize(json)); }
            catch (Exception e) { plan.Error = "scene json unreadable: " + e.Message; return plan; }
            if (root == null) { plan.Error = "scene json is not an object"; return plan; }

            try
            {
                var street = Obj(root, "street");
                var cway = Obj(street, "carriageway");
                var chan = Obj(street, "channel");
                var kerb = Obj(street, "kerb");
                var foot = Obj(street, "footway");
                var drop = Obj(street, "dropped_kerb");
                var gully = Obj(street, "gully");

                var sec = new StreetSection
                {
                    LengthM = Num(street, "length_m"),
                    HalfWidthM = Num(cway, "half_width_m"),
                    CrossFall = Num(cway, "crossfall"),
                    ChannelWidthM = Num(chan, "width_m"),
                    KerbUpstandM = Num(kerb, "upstand_m"),
                    KerbWidthM = Num(kerb, "width_m"),
                    KerbDepthM = Num(kerb, "depth_m"),
                    KerbBlockM = Num(kerb, "block_length_m"),
                    FootwayWidthM = Num(foot, "width_m"),
                    FootwayCrossFall = Num(foot, "crossfall"),
                    DroppedSide = Str(drop, "side"),
                    DroppedCentreX = Num(drop, "centre_x_m"),
                    DroppedWidthM = Num(drop, "crossover_width_m"),
                    DroppedTaperBlocks = (int)Num(drop, "taper_blocks"),
                    DroppedFlushM = Num(drop, "flush_upstand_m"),
                    GullySide = Str(gully, "side"),
                    GullyCentreX = Num(gully, "centre_x_m"),
                    GullyGrateM = Num(gully, "grate_size_m"),
                    GullyRecessM = Num(gully, "recess_depth_m"),
                    GullyDishM = Num(gully, "dish_depth_m"),
                };
                plan.Sec = sec;

                // ORDER MATTERS ONLY HERE: the plots have to exist before
                // anything asks whether there is ground under a building.
                var blocks = MiniJson.GetList(root, "blocks");
                if (blocks == null) throw new KeyNotFoundException("blocks");
                foreach (var b in blocks)
                {
                    var blk = MiniJson.AsObject(b);
                    double x0 = Num(blk, "start_x_m");
                    double x1 = x0 + Num(blk, "bays") * Num(blk, "bay_width_m");
                    double depth = Num(blk, "depth_m");
                    string side = Str(blk, "side");
                    double sgn = side == "east" ? 1 : -1;
                    plan.Plots.Add(new Plot
                    {
                        X0 = x0, X1 = x1, Side = side, Y = sec.FootwayBackY,
                        Z0 = sgn * sec.BuildingLineZ, Z1 = sgn * (sec.BuildingLineZ + depth)
                    });
                }

                Ground(plan, root);
                Kerbs(plan);
                foreach (var b in blocks) Block(plan, root, MiniJson.AsObject(b));
                Columns(plan, root);
                Furniture(plan, root);
                Scatter(plan, root);
                Optics(plan, root);
            }
            catch (Exception e)
            {
                plan.Error = "scene json incomplete: " + e.Message;
            }
            return plan;
        }

        // ---- the ground, which is BOM line A0 and the reason it exists ----

        static void Ground(Plan plan, Dictionary<string, object> root)
        {
            var s = plan.Sec;
            var street = Obj(root, "street");
            string asphalt = Str(Obj(street, "carriageway"), "surface");
            string channel = Str(Obj(street, "channel"), "surface");
            string paving = Str(Obj(street, "footway"), "surface");
            const double slabThick = 0.30; // the slab is buried; only its top face is ever seen

            foreach (int sgn in new[] { 1, -1 })
            {
                string side = sgn > 0 ? "east" : "west";
                // THE CAMBER, AND IT IS THE WHOLE POINT OF A0. Each half of
                // the carriageway is one slab tilted by the crossfall, so the
                // crown really is 75 mm above the channel and the wet
                // condition's water collects where a road puts it rather than
                // in a puddle the artist chose.
                double zc0 = 0, zc1 = s.HalfWidthM - s.ChannelWidthM;
                Slab(plan, "A0_ground_planes", side + "_carriageway", asphalt,
                     0, s.LengthM, sgn * zc0, sgn * zc1, 0, -zc1 * s.CrossFall, slabThick,
                     side + "_carriageway");
                Slab(plan, "A0_ground_planes", side + "_channel", channel,
                     0, s.LengthM, sgn * zc1, sgn * s.HalfWidthM,
                     -zc1 * s.CrossFall, s.ChannelY, slabThick, side + "_channel");
                // AND THE PAVEMENT AT A DIFFERENT LEVEL, which is A0's other
                // half: 100 mm above the crown of the road at the building
                // line, falling 50 mm back to the kerb.
                Slab(plan, "A0_ground_planes", side + "_footway", paving,
                     0, s.LengthM, sgn * s.FootwayFrontZ, sgn * s.BuildingLineZ,
                     s.KerbTopY, s.FootwayBackY, slabThick, side + "_footway");
            }

            // THE PLOTS. Not decoration: without them every building in the
            // scene has no datum under its footprint and the placement
            // instrument would report a hundred false alarms, which is how an
            // instrument gets switched off.
            int n = 0;
            foreach (var p in plan.Plots)
            {
                n++;
                Slab(plan, "A0_ground_planes", "plot_" + n, paving,
                     p.X0, p.X1, Math.Min(p.Z0, p.Z1), Math.Max(p.Z0, p.Z1),
                     p.Y, p.Y, slabThick, p.Side + "_plot");
            }
        }

        /// A tilted slab from (z0,y0) to (z1,y1), z0 < z1 always. The pitch
        /// is derived from the two ends rather than passed in, so a slab can
        /// never be laid at a fall the section did not ask for.
        static void Slab(Plan plan, string bom, string name, string surface,
                         double x0, double x1, double z0, double z1,
                         double y0, double y1, double thick, string edge)
        {
            if (z1 < z0) { var t = z0; z0 = z1; z1 = t; var u = y0; y0 = y1; y1 = u; }
            double dz = z1 - z0, dy = y1 - y0;
            double len = Math.Sqrt(dz * dz + dy * dy);
            double pitch = -Math.Atan2(dy, dz) * 180.0 / Math.PI;
            // Down the slab's own normal by half its thickness, so the TOP
            // face lands on the two levels asked for.
            double nz = -dy / len, ny = dz / len;
            plan.Add(new Piece
            {
                Bom = bom, Name = "ground_" + name, Shape = "box", Surface = surface,
                X = (x0 + x1) * 0.5, Y = (y0 + y1) * 0.5 - ny * thick * 0.5,
                Z = (z0 + z1) * 0.5 - nz * thick * 0.5,
                SX = x1 - x0, SY = thick, SZ = len,
                PitchDeg = pitch, Edge = edge, Region = "all"
            });
        }

        // ---- B1, B2, B3: the kerb run, the crossover and the gully ----

        static void Kerbs(Plan plan)
        {
            var s = plan.Sec;
            int blocks = (int)Math.Floor(s.LengthM / s.KerbBlockM);
            foreach (int sgn in new[] { 1, -1 })
            {
                string side = sgn > 0 ? "east" : "west";
                double zc = sgn * (s.KerbFaceZ + s.KerbWidthM * 0.5);
                for (int i = 0; i < blocks; i++)
                {
                    double x0 = i * s.KerbBlockM, xm = x0 + s.KerbBlockM * 0.5;
                    // THE GULLY BLOCK IS THREE PIECES, not one lowered block.
                    // The recess is 0.40 m wide because that is the MEASURED
                    // footprint of the grate that will sit in it; cutting the
                    // whole 0.915 m block down would be inventing a dimension
                    // to save two objects.
                    bool gully = side == s.GullySide
                                 && Math.Abs(xm - s.GullyCentreX) < s.KerbBlockM * 0.5;
                    if (gully)
                    {
                        double w = s.GullyGrateM, wing = (s.KerbBlockM - w) * 0.5;
                        KerbPiece(plan, side, "B3_gully_recess", "gully_lo",
                                  s.GullyCentreX, w, zc, s.KerbTopY - s.GullyRecessM);
                        KerbPiece(plan, side, "B3_gully_recess", "gully_w0",
                                  s.GullyCentreX - (w + wing) * 0.5, wing, zc, s.KerbTopAt(x0, side));
                        KerbPiece(plan, side, "B3_gully_recess", "gully_w1",
                                  s.GullyCentreX + (w + wing) * 0.5, wing, zc, s.KerbTopAt(x0 + s.KerbBlockM, side));
                        continue;
                    }
                    double top = s.KerbTopAt(xm, side);
                    bool dropped = side == s.DroppedSide && top < s.KerbTopY - 1e-9;
                    KerbPiece(plan, side, dropped ? "B2_dropped_kerb" : "B1_kerbstone_run",
                              "kerb" + i.ToString("000"), xm, s.KerbBlockM, zc, top);
                }
                // AND THE DISH UNDER THE GRATE, so the water has somewhere to
                // go and the grate is not a sticker on flat tarmac.
                if (side == s.GullySide)
                {
                    double z = sgn * (s.HalfWidthM - s.GullyGrateM * 0.5);
                    plan.Add(new Piece
                    {
                        Bom = "B3_gully_recess", Name = "gully_dish_" + side, Shape = "box",
                        Surface = "kerb", X = s.GullyCentreX,
                        Y = s.ChannelY - s.GullyDishM - 0.15, Z = z,
                        SX = s.GullyGrateM, SY = 0.30, SZ = s.GullyGrateM,
                        Edge = side + "_channel", Region = RegionOf(s.GullyCentreX)
                    });
                }
            }
        }

        static void KerbPiece(Plan plan, string side, string bom, string tag,
                              double xm, double len, double zc, double top)
        {
            var s = plan.Sec;
            plan.Add(new Piece
            {
                Bom = bom, Name = "kerb_" + side + "_" + tag, Shape = "box", Surface = "kerb",
                X = xm, Y = top - s.KerbDepthM * 0.5, Z = zc,
                SX = len, SY = s.KerbDepthM, SZ = s.KerbWidthM,
                Edge = side + "_kerb", Region = RegionOf(xm)
            });
        }

        // ---- C and D: the terrace, its frontage and its roofline ----

        static void Block(Plan plan, Dictionary<string, object> root, Dictionary<string, object> blk)
        {
            var s = plan.Sec;
            var facade = Obj(root, "facade");
            var roofline = Obj(root, "roofline");
            var shopSpec = Obj(root, "shopfront");
            string id = Str(blk, "id"), side = Str(blk, "side");
            double sgn = side == "east" ? 1 : -1;
            int bays = (int)Num(blk, "bays");
            double bw = Num(blk, "bay_width_m"), x0 = Num(blk, "start_x_m");
            double depth = Num(blk, "depth_m");
            string wallSurface = Str(blk, "wall_surface");
            var storeys = MiniJson.GetList(blk, "storey_heights_m");
            double h0 = ToD(storeys[0]), h1 = ToD(storeys[1]);
            double baseY = s.FootwayBackY, eavesY = baseY + h0 + h1;
            double frontZ = sgn * s.BuildingLineZ;
            bool shopfront = Str(blk, "ground_floor") == "shopfront";
            var roof = Obj(blk, "roof");

            for (int i = 0; i < bays; i++)
            {
                double bx0 = x0 + i * bw, bxm = bx0 + bw * 0.5;
                var carcass = new Piece
                {
                    Bom = "C1_terrace_carcass", Name = id + "_bay" + i, Shape = "box",
                    Surface = wallSurface, X = bxm, Y = baseY + (h0 + h1) * 0.5,
                    Z = sgn * (s.BuildingLineZ + depth * 0.5),
                    SX = bw, SY = h0 + h1, SZ = depth,
                    Edge = side + "_plot", Region = RegionOf(bxm)
                };
                plan.Add(carcass);
                plan.Foot5(carcass, baseY);

                if (shopfront) Shopfront(plan, shopSpec, id, i, bx0, bw, frontZ, sgn, baseY, h0, wallSurface);
                else GroundFloorPlain(plan, shopSpec, facade, id, i, bx0, bw, frontZ, sgn, baseY, h0, wallSurface, side);

                // D8 plus C13: the first-floor windows with their reveal,
                // sill and lintel. One object would be a decal; three is what
                // stops the wall reading as a plane.
                Windows(plan, facade, id + "_up" + i, bx0, bw, frontZ, sgn,
                        baseY + h0, h1, wallSurface, side);
            }

            double blockLen = bays * bw;
            if (Str(roof, "kind") == "pitched")
                Pitched(plan, roofline, roof, id, x0, blockLen, depth, frontZ, sgn, eavesY, side, bays, bw, wallSurface);
            else
                Parapet(plan, roof, id, x0, blockLen, depth, frontZ, sgn, eavesY, side);

            // D5, one per bay boundary, which is where a real downpipe goes:
            // it drains one roof slope into one gully rather than standing
            // wherever there was room.
            var dp = Obj(roofline, "downpipe");
            for (int i = 1; i < bays; i++)
                Downpipe(plan, dp, id + "_dp" + i, x0 + i * bw, frontZ, sgn, baseY, eavesY, side);
        }

        static void Shopfront(Plan plan, Dictionary<string, object> spec, string id, int bay,
                              double bx0, double bw, double frontZ, double sgn,
                              double baseY, double h0, string wallSurface)
        {
            double pw = Num(spec, "pilaster_width_m"), pp = Num(spec, "pilaster_projection_m");
            double sr = Num(spec, "stallriser_height_m"), srp = Num(spec, "stallriser_projection_m");
            double tr = Num(spec, "transom_height_m"), trt = Num(spec, "transom_thickness_m");
            double fb = Num(spec, "fascia_bottom_m"), fp = Num(spec, "fascia_projection_m");
            double gr = Num(spec, "glazing_recess_m"), icd = Num(spec, "interior_card_depth_m");
            var sd = Obj(spec, "shop_door"); var xd = Obj(spec, "side_door");
            double sdw = Num(sd, "width_m"), sdh = Num(sd, "height_m"), sdg = Num(sd, "glazed_from_m");
            double xdw = Num(xd, "width_m"), xdh = Num(xd, "height_m");
            string reg = RegionOf(bx0 + bw * 0.5), edge = (sgn > 0 ? "east" : "west") + "_footway";
            string pedge = (sgn > 0 ? "east" : "west") + "_plot";

            // Left to right across the bay: pilaster, side door to the flat,
            // shop door, glazing, pilaster. That layout is what makes a
            // British parade unit read as one address with two doors.
            for (int p = 0; p < 2; p++)
            {
                double px = p == 0 ? bx0 + pw * 0.5 : bx0 + bw - pw * 0.5;
                var pil = new Piece
                {
                    Bom = "C5_shopfront_assembly", Name = id + "_pil" + bay + "_" + p, Shape = "box",
                    Surface = wallSurface, X = px, Y = baseY + h0 * 0.5, Z = frontZ - sgn * pp * 0.5,
                    SX = pw, SY = h0, SZ = pp, Edge = edge, Region = reg
                };
                plan.Add(pil); plan.Foot5(pil, baseY);
            }
            double openX0 = bx0 + pw, openW = bw - 2 * pw;
            double doorSideX = openX0 + xdw * 0.5;
            double doorShopX = openX0 + xdw + sdw * 0.5;
            double glazeX0 = openX0 + xdw + sdw, glazeW = openW - xdw - sdw;

            var stall = new Piece
            {
                Bom = "C5_shopfront_assembly", Name = id + "_stall" + bay, Shape = "box",
                Surface = "concrete", X = glazeX0 + glazeW * 0.5, Y = baseY + sr * 0.5,
                Z = frontZ - sgn * srp * 0.5, SX = glazeW, SY = sr, SZ = srp,
                Edge = edge, Region = reg
            };
            plan.Add(stall); plan.Foot5(stall, baseY);

            plan.Add(new Piece
            {
                Bom = "C7_shop_glazing", Name = id + "_glass" + bay, Shape = "box", Surface = "glass",
                X = glazeX0 + glazeW * 0.5, Y = baseY + (sr + tr) * 0.5, Z = frontZ - sgn * (gr + 0.02),
                SX = glazeW, SY = tr - sr, SZ = 0.04, Edge = edge, Region = reg
            });
            plan.Add(new Piece
            {
                Bom = "C5_shopfront_assembly", Name = id + "_transom" + bay, Shape = "box",
                Surface = wallSurface, X = glazeX0 + glazeW * 0.5, Y = baseY + tr + trt * 0.5,
                Z = frontZ - sgn * gr * 0.5, SX = glazeW, SY = trt, SZ = gr,
                Edge = edge, Region = reg
            });
            plan.Add(new Piece
            {
                Bom = "C7_shop_glazing", Name = id + "_toplight" + bay, Shape = "box", Surface = "glass",
                X = glazeX0 + glazeW * 0.5, Y = baseY + (tr + trt + fb) * 0.5, Z = frontZ - sgn * (gr + 0.02),
                SX = glazeW, SY = fb - tr - trt, SZ = 0.04, Edge = edge, Region = reg
            });
            plan.Add(new Piece
            {
                Bom = "C5_shopfront_assembly", Name = id + "_fascia" + bay, Shape = "box",
                Surface = "wood", X = bx0 + bw * 0.5, Y = baseY + (fb + h0) * 0.5,
                Z = frontZ - sgn * fp * 0.5, SX = bw, SY = h0 - fb, SZ = fp,
                Edge = edge, Region = reg
            });
            // WHAT IS BEHIND THE GLASS AT NIGHT. Geometry only: the artwork
            // on it is BOM line C11, which is the 2D generator's line and not
            // this emitter's. A lit window with nothing behind it is a glowing
            // rectangle and the night frame is half the D1b evidence.
            var card = new Piece
            {
                Bom = "C5_shopfront_assembly", Name = id + "_interior" + bay, Shape = "box",
                Surface = "interior", X = bx0 + bw * 0.5, Y = baseY + tr * 0.5,
                Z = frontZ + sgn * icd, SX = openW, SY = tr, SZ = 0.10,
                Edge = pedge, Region = reg
            };
            plan.Add(card); plan.Foot5(card, baseY);

            Door(plan, "C8_door_shop", id + "_shopdoor" + bay, doorShopX, sdw, sdh, sdg,
                 frontZ, sgn, baseY, edge, reg, wallSurface, fb);
            Door(plan, "C9_door_side", id + "_sidedoor" + bay, doorSideX, xdw, xdh, xdh,
                 frontZ, sgn, baseY, edge, reg, wallSurface, fb);
            var lp = new Piece
            {
                Bom = "C9_door_side", Name = id + "_letterplate" + bay, Shape = "box", Surface = "metal",
                X = doorSideX, Y = baseY + Num(xd, "letterplate_at_m"), Z = frontZ - sgn * 0.055,
                SX = Num(xd, "letterplate_width_m"), SY = Num(xd, "letterplate_height_m"), SZ = 0.02,
                Edge = edge, Region = reg
            };
            plan.Add(lp);
        }

        /// A door leaf with a spandrel above it up to the fascia or the head
        /// of the storey. `glazedFrom` equal to the height means a solid
        /// panelled leaf, which is what the side door to the flat is.
        static void Door(Plan plan, string bom, string name, double x, double w, double h,
                         double glazedFrom, double frontZ, double sgn, double baseY,
                         string edge, string reg, string wallSurface, double headTo)
        {
            var leaf = new Piece
            {
                Bom = bom, Name = name, Shape = "box", Surface = "wood",
                X = x, Y = baseY + glazedFrom * 0.5, Z = frontZ - sgn * 0.03,
                SX = w, SY = glazedFrom, SZ = 0.06, Edge = edge, Region = reg
            };
            plan.Add(leaf); plan.Foot5(leaf, baseY);
            if (glazedFrom < h - 1e-9)
                plan.Add(new Piece
                {
                    Bom = bom, Name = name + "_light", Shape = "box", Surface = "glass",
                    X = x, Y = baseY + (glazedFrom + h) * 0.5, Z = frontZ - sgn * 0.03,
                    SX = w, SY = h - glazedFrom, SZ = 0.04, Edge = edge, Region = reg
                });
            plan.Add(new Piece
            {
                Bom = bom, Name = name + "_spandrel", Shape = "box", Surface = wallSurface,
                X = x, Y = baseY + (h + headTo) * 0.5, Z = frontZ - sgn * 0.05,
                SX = w, SY = headTo - h, SZ = 0.10, Edge = edge, Region = reg
            });
        }

        static void GroundFloorPlain(Plan plan, Dictionary<string, object> spec,
                                     Dictionary<string, object> facade, string id, int bay,
                                     double bx0, double bw, double frontZ, double sgn,
                                     double baseY, double h0, string wallSurface, string side)
        {
            var xd = Obj(spec, "side_door");
            string reg = RegionOf(bx0 + bw * 0.5), edge = side + "_footway";
            Door(plan, "C9_door_side", id + "_door" + bay, bx0 + bw * 0.25,
                 Num(xd, "width_m"), Num(xd, "height_m"), Num(xd, "height_m"),
                 frontZ, sgn, baseY, edge, reg, wallSurface, h0 - 0.30);
            Windows(plan, facade, id + "_gf" + bay, bx0 + bw * 0.4, bw * 0.6, frontZ, sgn,
                    baseY, h0, wallSurface, side);
        }

        static void Windows(Plan plan, Dictionary<string, object> facade, string name,
                            double bx0, double bw, double frontZ, double sgn,
                            double storeyY, double storeyH, string wallSurface, string side)
        {
            int n = (int)Num(facade, "windows_per_bay");
            double ww = Num(facade, "window_width_m"), wh = Num(facade, "window_height_m");
            double rev = Num(facade, "reveal_depth_m");
            double sp = Num(facade, "sill_projection_m"), st = Num(facade, "sill_thickness_m");
            double sx = Num(facade, "sill_extra_width_m"), lt = Num(facade, "lintel_thickness_m");
            double head = storeyY + storeyH - Num(facade, "head_below_ceiling_m");
            double sill = head - wh;
            string reg = RegionOf(bx0 + bw * 0.5), edge = side + "_footway";
            for (int i = 0; i < n; i++)
            {
                double x = bx0 + bw * (i + 0.5) / n;
                // THE REVEAL IS THE WHOLE POINT and it is one brick on its
                // side, 102.5 mm, not a round number chosen for looks.
                plan.Add(new Piece
                {
                    Bom = "D8_upper_windows", Name = name + "_w" + i, Shape = "box", Surface = "window",
                    X = x, Y = (sill + head) * 0.5, Z = frontZ + sgn * rev,
                    SX = ww, SY = wh, SZ = 0.06, Edge = edge, Region = reg
                });
                plan.Add(new Piece
                {
                    Bom = "C13_sills_lintels", Name = name + "_sill" + i, Shape = "box", Surface = "concrete",
                    X = x, Y = sill - st * 0.5, Z = frontZ - sgn * (sp * 0.5 - rev * 0.5),
                    SX = ww + sx, SY = st, SZ = sp + rev, Edge = edge, Region = reg
                });
                plan.Add(new Piece
                {
                    Bom = "C13_sills_lintels", Name = name + "_lintel" + i, Shape = "box", Surface = "concrete",
                    X = x, Y = head + lt * 0.5, Z = frontZ + sgn * rev * 0.5,
                    SX = ww + sx, SY = lt, SZ = rev, Edge = edge, Region = reg
                });
            }
        }

        static void Pitched(Plan plan, Dictionary<string, object> roofline, Dictionary<string, object> roof,
                            string id, double x0, double len, double depth, double frontZ, double sgn,
                            double eavesY, string side, int bays, double bw, string wallSurface)
        {
            var s = plan.Sec;
            double pitch = Num(roof, "pitch_deg"), over = Num(roof, "eaves_overhang_m");
            double rise = (depth * 0.5) * Math.Tan(pitch * Math.PI / 180.0);
            double ridgeZ = sgn * (s.BuildingLineZ + depth * 0.5), ridgeY = eavesY + rise;
            double frontEaveZ = frontZ - sgn * over, backEaveZ = sgn * (s.BuildingLineZ + depth + over);
            Slab(plan, "C1_terrace_carcass", id + "_roof_front", Str(roof, "surface"),
                 x0, x0 + len, frontEaveZ, ridgeZ, eavesY, ridgeY, 0.15, side + "_plot");
            Slab(plan, "C1_terrace_carcass", id + "_roof_back", Str(roof, "surface"),
                 x0, x0 + len, ridgeZ, backEaveZ, ridgeY, eavesY, 0.15, side + "_plot");

            // D6, the eaves gutter and its fascia board. The shadow line
            // under an eaves is what stops a roof reading as a lid.
            var g = Obj(roofline, "gutter");
            double gd = Num(g, "diameter_m");
            plan.Add(new Piece
            {
                Bom = "D6_gutter_run", Name = id + "_gutter", Shape = "cyl", Surface = Str(g, "surface"),
                X = x0 + len * 0.5, Y = eavesY + gd * 0.5, Z = frontEaveZ,
                // A LYING PIPE, NOT A STRETCHED DISC. The length is SY
                // because SY is the axis of a cylinder in both engines, and
                // RollDeg 90 lays that axis along the street. The yaw that
                // used to be here rotated nothing: yaw turns a cylinder
                // about its own axis.
                SX = gd, SY = len, SZ = gd, RollDeg = 90,
                Edge = side + "_plot", Region = "all"
            });
            plan.Add(new Piece
            {
                Bom = "D6_gutter_run", Name = id + "_fascia_board", Shape = "box", Surface = "wood",
                X = x0 + len * 0.5, Y = eavesY - Num(g, "fascia_depth_m") * 0.5, Z = frontEaveZ,
                SX = len, SY = Num(g, "fascia_depth_m"), SZ = Num(g, "fascia_thickness_m"),
                Edge = side + "_plot", Region = "all"
            });

            // D2 on the party walls, which is where a stack serving two
            // houses has to be, and D4 on the ones the JSON names.
            var ch = Obj(roofline, "chimney");
            var ae = Obj(roofline, "aerial");
            var onStacks = new List<int>();
            foreach (var v in MiniJson.GetList(ae, "on_stacks")) onStacks.Add((int)ToD(v));
            double chTop = ridgeY + Num(ch, "height_above_ridge_m");
            for (int i = 1; i < bays; i++)
            {
                double sx = x0 + i * bw;
                plan.Add(new Piece
                {
                    Bom = "D2_chimney_stack", Name = id + "_stack" + i, Shape = "box",
                    Surface = Str(ch, "surface"), X = sx, Y = (eavesY + chTop) * 0.5, Z = ridgeZ,
                    SX = Num(ch, "width_m"), SY = chTop - eavesY, SZ = Num(ch, "depth_m"),
                    Edge = side + "_plot", Region = RegionOf(sx)
                });
                if (onStacks.Contains(i)) Aerial(plan, ae, id + "_aerial" + i, sx, ridgeZ, chTop, side);
            }
        }

        static void Aerial(Plan plan, Dictionary<string, object> ae, string name,
                           double x, double z, double topY, string side)
        {
            double mh = Num(ae, "mast_height_m"), md = Num(ae, "mast_diameter_m");
            double bl = Num(ae, "boom_length_m"), bd = Num(ae, "boom_diameter_m");
            int n = (int)Num(ae, "elements");
            double el = Num(ae, "element_length_m"), ed = Num(ae, "element_diameter_m");
            string reg = RegionOf(x);
            plan.Add(new Piece
            {
                Bom = "D4_tv_aerial", Name = name + "_mast", Shape = "cyl", Surface = "metal",
                X = x, Y = topY + mh * 0.5, Z = z, SX = md, SY = mh, SZ = md,
                Edge = side + "_plot", Region = reg
            });
            double boomY = topY + mh;
            plan.Add(new Piece
            {
                Bom = "D4_tv_aerial", Name = name + "_boom", Shape = "cyl", Surface = "metal",
                // Rolled, so the boom runs ALONG the street, which is the
                // axis its elements are already spread along below.
                X = x, Y = boomY, Z = z, SX = bd, SY = bl, SZ = bd, RollDeg = 90,
                Edge = side + "_plot", Region = reg
            });
            for (int i = 0; i < n; i++)
            {
                // The elements are 0.27 m because that is a half wave at the
                // middle of the UHF band the country watched television on.
                double t = n == 1 ? 0.5 : i / (double)(n - 1);
                plan.Add(new Piece
                {
                    Bom = "D4_tv_aerial", Name = name + "_el" + i, Shape = "cyl", Surface = "metal",
                    X = x - bl * 0.5 + bl * t, Y = boomY, Z = z,
                    // Pitched 90, so each element lies ACROSS the street, at
                    // right angles to the boom, which is what makes it an
                    // aerial rather than a ladder.
                    SX = ed, SY = el, SZ = ed, PitchDeg = 90,
                    Edge = side + "_plot", Region = reg
                });
            }
        }

        static void Parapet(Plan plan, Dictionary<string, object> roof, string id,
                            double x0, double len, double depth, double frontZ, double sgn,
                            double eavesY, string side)
        {
            var s = plan.Sec;
            double ph = Num(roof, "parapet_height_m"), pt = Num(roof, "parapet_thickness_m");
            double cw = Num(roof, "coping_width_m"), ct = Num(roof, "coping_thickness_m");
            plan.Add(new Piece
            {
                Bom = "C1_terrace_carcass", Name = id + "_roofdeck", Shape = "box",
                Surface = Str(roof, "surface"), X = x0 + len * 0.5, Y = eavesY - 0.075,
                Z = sgn * (s.BuildingLineZ + depth * 0.5), SX = len, SY = 0.15, SZ = depth,
                Edge = side + "_plot", Region = "all"
            });
            plan.Add(new Piece
            {
                Bom = "D7_parapet_coping", Name = id + "_parapet", Shape = "box",
                Surface = Str(roof, "surface"), X = x0 + len * 0.5, Y = eavesY + ph * 0.5,
                Z = frontZ - sgn * pt * 0.5, SX = len, SY = ph, SZ = pt,
                Edge = side + "_plot", Region = "all"
            });
            plan.Add(new Piece
            {
                Bom = "D7_parapet_coping", Name = id + "_coping", Shape = "box", Surface = "concrete",
                X = x0 + len * 0.5, Y = eavesY + ph + ct * 0.5, Z = frontZ - sgn * pt * 0.5,
                SX = len, SY = ct, SZ = cw, Edge = side + "_plot", Region = "all"
            });
        }

        static void Downpipe(Plan plan, Dictionary<string, object> dp, string name, double x,
                             double frontZ, double sgn, double baseY, double eavesY, string side)
        {
            double d = Num(dp, "diameter_m"), so = Num(dp, "standoff_m");
            double sh = Num(dp, "shoe_height_m"), sp = Num(dp, "shoe_projection_m");
            double z = frontZ - sgn * (so + d * 0.5);
            string reg = RegionOf(x), edge = side + "_footway";
            var pipe = new Piece
            {
                Bom = "D5_downpipe", Name = name, Shape = "cyl", Surface = Str(dp, "surface"),
                X = x, Y = baseY + sh + (eavesY - baseY - sh) * 0.5, Z = z,
                SX = d, SY = eavesY - baseY - sh, SZ = d, Edge = edge, Region = reg
            };
            plan.Add(pipe);
            var shoe = new Piece
            {
                Bom = "D5_downpipe", Name = name + "_shoe", Shape = "box", Surface = Str(dp, "surface"),
                X = x, Y = baseY + sh * 0.5, Z = z - sgn * sp * 0.25,
                SX = d, SY = sh, SZ = d + sp * 0.5, Edge = edge, Region = reg
            };
            plan.Add(shoe); plan.Foot5(shoe, baseY);
            plan.Add(new Piece
            {
                Bom = "D5_downpipe", Name = name + "_hopper", Shape = "box", Surface = Str(dp, "surface"),
                X = x, Y = eavesY - Num(dp, "hopper_height_m") * 0.5, Z = z,
                SX = Num(dp, "hopper_width_m"), SY = Num(dp, "hopper_height_m"),
                SZ = Num(dp, "hopper_depth_m"), Edge = edge, Region = reg
            });
        }

        // ---- E1, E2 and H4: the columns, the lanterns and their count ----

        static void Columns(Plan plan, Dictionary<string, object> root)
        {
            var s = plan.Sec;
            var lighting = Obj(root, "lighting");
            var col = Obj(lighting, "column");
            var lan = Obj(lighting, "lantern");
            double mh = Num(col, "mounting_height_m");
            // THE SPACING IS A RATIO, so the lantern count follows from the
            // mounting height rather than being written down twice. H4 asks
            // for four practicals and four is what 5.0 m at 4.0x over 42 m of
            // street with alternating sides produces.
            double spacing = mh * Num(col, "spacing_per_mounting_height");
            double setback = Num(col, "setback_from_kerb_m");
            double bd = Num(col, "base_diameter_m"), bh = Num(col, "base_height_m");
            double sd = Num(col, "shaft_diameter_m"), reach = Num(col, "outreach_m");
            double first = Num(col, "first_offset_m");
            int n = 0;
            for (double x = first; x <= s.LengthM - first * 0.25; x += spacing * 0.5)
            {
                // Alternating sides, so the spacing on any one side is the
                // full ratio and the street is lit from both.
                double sgn = (n % 2 == 0) ? 1 : -1;
                string side = sgn > 0 ? "east" : "west";
                double z = sgn * (s.FootwayFrontZ + setback);
                double gy = s.KerbTopY + setback * s.FootwayCrossFall;
                string reg = RegionOf(x);
                var b = new Piece
                {
                    Bom = "E1_lighting_column", Name = "column" + n + "_base", Shape = "cyl",
                    Surface = Str(col, "surface"), X = x, Y = gy + bh * 0.5, Z = z,
                    SX = bd, SY = bh, SZ = bd, Edge = side + "_footway", Region = reg
                };
                plan.Add(b); plan.Foot5(b, gy);
                plan.Add(new Piece
                {
                    Bom = "E1_lighting_column", Name = "column" + n + "_shaft", Shape = "cyl",
                    Surface = Str(col, "surface"), X = x, Y = gy + bh + (mh - bh) * 0.5, Z = z,
                    SX = sd, SY = mh - bh, SZ = sd, Edge = side + "_footway", Region = reg
                });
                // The swan neck, three short cylinders on a quarter circle.
                // A straight bracket reads as a modern column and this is a
                // 1990 street.
                for (int k = 0; k < 3; k++)
                {
                    double a = (k + 0.5) / 3.0 * Math.PI * 0.5;
                    plan.Add(new Piece
                    {
                        Bom = "E1_lighting_column", Name = "column" + n + "_neck" + k, Shape = "cyl",
                        Surface = Str(col, "surface"), X = x,
                        Y = gy + mh - reach * (1 - Math.Sin(a)) * 0.5,
                        Z = z - sgn * reach * (1 - Math.Cos(a)),
                        SX = sd * 0.8, SY = reach * 0.45, SZ = sd * 0.8,
                        PitchDeg = -(a * 180.0 / Math.PI) * (sgn > 0 ? 1 : -1),
                        Edge = side + "_footway", Region = reg
                    });
                }
                plan.Add(new Piece
                {
                    Bom = "E2_sodium_lantern_head", Name = "lantern" + n, Shape = "box",
                    Surface = "metal", X = x, Y = gy + mh - Num(lan, "height_m") * 0.5,
                    Z = z - sgn * reach, SX = Num(lan, "length_m"), SY = Num(lan, "height_m"),
                    SZ = Num(lan, "width_m"), Emissive = true,
                    Edge = side + "_footway", Region = reg
                });
                n++;
            }
        }

        // ---- E3, E4, E8, E13: what stands on the pavement ----

        static void Furniture(Plan plan, Dictionary<string, object> root)
        {
            var s = plan.Sec;
            var list = MiniJson.GetList(root, "furniture");
            if (list == null) return;
            foreach (var f in list)
            {
                var o = MiniJson.AsObject(f);
                string bom = Str(o, "bom"), side = Str(o, "side");
                double sgn = side == "east" ? 1 : -1;
                double x = Num(o, "x_m");
                double setback = Num(o, "setback_from_kerb_m");
                double z = sgn * (s.FootwayFrontZ + setback);
                double gy = s.KerbTopY + setback * s.FootwayCrossFall;
                string reg = RegionOf(x), edge = side + "_footway";
                if (bom == "E3_telephone_kiosk") Kiosk(plan, o, x, z, gy, sgn, edge, reg);
                else if (bom == "E4_pillar_box") PillarBox(plan, o, x, z, gy, sgn, edge, reg);
                else if (bom == "E8_guard_railing") Railing(plan, o, x, s, sgn, side);
                else if (bom == "E13_household_dustbin") Dustbins(plan, o, x, z, gy, edge, reg);
            }
        }

        static void Kiosk(Plan plan, Dictionary<string, object> o, double x, double z,
                          double gy, double sgn, string edge, string reg)
        {
            double p = Num(o, "plan_m"), h = Num(o, "height_m");
            double ph = Num(o, "plinth_height_m"), pw = Num(o, "post_width_m");
            double ch = Num(o, "cornice_height_m"), co = Num(o, "cornice_overhang_m");
            double cp = Num(o, "cap_plan_m"), cph = Num(o, "cap_height_m");
            double bodyH = h - ph - ch - cph;
            const string B = "E3_telephone_kiosk";
            var plinth = new Piece
            {
                Bom = B, Name = "kiosk_plinth", Shape = "box", Surface = "concrete",
                X = x, Y = gy + ph * 0.5, Z = z, SX = p, SY = ph, SZ = p, Edge = edge, Region = reg
            };
            plan.Add(plinth); plan.Foot5(plinth, gy);
            for (int i = 0; i < 4; i++)
            {
                double dx = (i < 2 ? -1 : 1) * (p - pw) * 0.5;
                double dz = (i % 2 == 0 ? -1 : 1) * (p - pw) * 0.5;
                plan.Add(new Piece
                {
                    Bom = B, Name = "kiosk_post" + i, Shape = "box", Surface = "metal",
                    X = x + dx, Y = gy + ph + bodyH * 0.5, Z = z + dz,
                    SX = pw, SY = bodyH, SZ = pw, Edge = edge, Region = reg
                });
            }
            // Three glazed sides and a door leaf on the fourth. NO CROWN AND
            // NO LETTERING: canon requires every brand fictional and the
            // Meridian telephone operator has not been written, so the kiosk
            // ships unlettered rather than carrying a real mark.
            for (int i = 0; i < 4; i++)
            {
                bool front = i == 0;
                double a = i * Math.PI * 0.5;
                plan.Add(new Piece
                {
                    Bom = B, Name = front ? "kiosk_door" : "kiosk_glass" + i, Shape = "box",
                    Surface = "glass", X = x + Math.Sin(a) * p * 0.5 * sgn,
                    Y = gy + ph + bodyH * 0.5, Z = z + Math.Cos(a) * p * 0.5 * sgn,
                    SX = (i % 2 == 0 ? p - pw * 2 : 0.05), SY = bodyH * 0.92,
                    SZ = (i % 2 == 0 ? 0.05 : p - pw * 2), Edge = edge, Region = reg
                });
            }
            plan.Add(new Piece
            {
                Bom = B, Name = "kiosk_cornice", Shape = "box", Surface = "metal",
                X = x, Y = gy + ph + bodyH + ch * 0.5, Z = z,
                SX = p + co * 2, SY = ch, SZ = p + co * 2, Edge = edge, Region = reg
            });
            plan.Add(new Piece
            {
                Bom = B, Name = "kiosk_cap", Shape = "box", Surface = "metal",
                X = x, Y = gy + ph + bodyH + ch + cph * 0.5, Z = z,
                SX = cp, SY = cph, SZ = cp, Edge = edge, Region = reg
            });
        }

        static void PillarBox(Plan plan, Dictionary<string, object> o, double x, double z,
                              double gy, double sgn, string edge, string reg)
        {
            const string B = "E4_pillar_box";
            double bd = Num(o, "body_diameter_m"), bh = Num(o, "body_height_m");
            double cd = Num(o, "cap_diameter_m"), ch = Num(o, "cap_height_m");
            double dh = Num(o, "dome_height_m");
            var body = new Piece
            {
                Bom = B, Name = "pillarbox_body", Shape = "cyl", Surface = "metal",
                X = x, Y = gy + bh * 0.5, Z = z, SX = bd, SY = bh, SZ = bd,
                Edge = edge, Region = reg
            };
            plan.Add(body); plan.Foot5(body, gy);
            plan.Add(new Piece
            {
                Bom = B, Name = "pillarbox_cap", Shape = "cyl", Surface = "metal",
                X = x, Y = gy + bh + ch * 0.5, Z = z, SX = cd, SY = ch, SZ = cd,
                Edge = edge, Region = reg
            });
            plan.Add(new Piece
            {
                Bom = B, Name = "pillarbox_dome", Shape = "cyl", Surface = "metal",
                X = x, Y = gy + bh + ch + dh * 0.5, Z = z, SX = cd * 0.86, SY = dh, SZ = cd * 0.86,
                Edge = edge, Region = reg
            });
            plan.Add(new Piece
            {
                Bom = B, Name = "pillarbox_aperture", Shape = "box", Surface = "metal",
                X = x, Y = gy + Num(o, "aperture_at_m"), Z = z - sgn * bd * 0.48,
                SX = Num(o, "aperture_width_m"), SY = Num(o, "aperture_height_m"), SZ = 0.03,
                Edge = edge, Region = reg
            });
        }

        static void Railing(Plan plan, Dictionary<string, object> o, double x0,
                            StreetSection s, double sgn, string side)
        {
            const string B = "E8_guard_railing";
            int panels = (int)Num(o, "panels"), infill = (int)Num(o, "infill_per_panel");
            double pl = Num(o, "panel_length_m"), h = Num(o, "height_m");
            double pd = Num(o, "post_diameter_m"), rd = Num(o, "rail_diameter_m");
            double idm = Num(o, "infill_diameter_m"), setback = Num(o, "setback_from_kerb_m");
            double z = sgn * (s.FootwayFrontZ + setback);
            double gy = s.KerbTopY + setback * s.FootwayCrossFall;
            string edge = side + "_footway";
            for (int p = 0; p <= panels; p++)
            {
                double px = x0 + p * pl;
                var post = new Piece
                {
                    Bom = B, Name = "rail_post" + p, Shape = "cyl", Surface = "metal",
                    X = px, Y = gy + h * 0.5, Z = z, SX = pd, SY = h, SZ = pd,
                    Edge = edge, Region = RegionOf(px)
                };
                plan.Add(post); plan.Foot5(post, gy);
            }
            for (int p = 0; p < panels; p++)
            {
                double pxm = x0 + (p + 0.5) * pl;
                string reg = RegionOf(pxm);
                foreach (double ry in new[] { h - rd, h * 0.45 })
                    plan.Add(new Piece
                    {
                        Bom = B, Name = "rail_bar" + p + "_" + (int)(ry * 100), Shape = "cyl",
                        Surface = "metal", X = pxm, Y = gy + ry, Z = z,
                        // Rolled, so the bar runs along the railing between
                        // its two posts instead of standing on end.
                        SX = rd, SY = pl, SZ = rd, RollDeg = 90, Edge = edge, Region = reg
                    });
                for (int i = 0; i < infill; i++)
                    plan.Add(new Piece
                    {
                        Bom = B, Name = "rail_inf" + p + "_" + i, Shape = "cyl", Surface = "metal",
                        X = x0 + p * pl + pl * (i + 1) / (double)(infill + 1),
                        Y = gy + h * 0.5, Z = z, SX = idm, SY = h, SZ = idm,
                        Edge = edge, Region = reg
                    });
            }
        }

        static void Dustbins(Plan plan, Dictionary<string, object> o, double x, double z,
                             double gy, string edge, string reg)
        {
            const string B = "E13_household_dustbin";
            int n = (int)Num(o, "count");
            double sp = Num(o, "spacing_m");
            double bd = Num(o, "body_diameter_m"), bh = Num(o, "body_height_m");
            double ld = Num(o, "lid_diameter_m"), lh = Num(o, "lid_height_m");
            for (int i = 0; i < n; i++)
            {
                double bx = x + i * sp;
                var body = new Piece
                {
                    Bom = B, Name = "dustbin" + i, Shape = "cyl", Surface = Str(o, "surface"),
                    X = bx, Y = gy + bh * 0.5, Z = z, SX = bd, SY = bh, SZ = bd,
                    Edge = edge, Region = RegionOf(bx)
                };
                plan.Add(body); plan.Foot5(body, gy);
                plan.Add(new Piece
                {
                    Bom = B, Name = "dustbin" + i + "_lid", Shape = "cyl", Surface = Str(o, "surface"),
                    X = bx, Y = gy + bh + lh * 0.5, Z = z, SX = ld, SY = lh, SZ = ld,
                    Edge = edge, Region = RegionOf(bx)
                });
            }
        }

        // ---- G8 and G9: what a street that has been lived in has on it ----

        static void Scatter(Plan plan, Dictionary<string, object> root)
        {
            var s = plan.Sec;
            var sc = Obj(root, "scatter");
            double seed = Num(sc, "seed");
            var lit = Obj(sc, "litter");
            int ln = (int)Num(lit, "count");
            double share = Num(lit, "gutter_share");
            double lo = Num(lit, "min_size_m"), hi = Num(lit, "max_size_m");
            double th = Num(lit, "thickness_m");
            for (int i = 0; i < ln; i++)
            {
                // Dressing.Roll is this project's one deterministic roll,
                // FNV-1a over quantised coordinates. Reused rather than
                // reimplemented so that the Unreal emitter has one function to
                // port and the two scatters cannot drift apart.
                double r0 = Dressing.Roll(seed, i, 1), r1 = Dressing.Roll(seed, i, 2);
                double r2 = Dressing.Roll(seed, i, 3), r3 = Dressing.Roll(seed, i, 4);
                double x = r0 * s.LengthM;
                double sgn = r1 < 0.5 ? 1 : -1;
                bool gutter = r2 < share;
                double az = gutter
                    ? s.HalfWidthM - s.ChannelWidthM * (0.15 + 0.7 * r3)
                    : s.BuildingLineZ - 0.10 - 0.35 * r3;
                double size = lo + (hi - lo) * r3;
                plan.GroundAt(x, sgn * az, out double gy, out string edge);
                var p = new Piece
                {
                    Bom = "G8_litter", Name = "litter" + i, Shape = "box", Surface = "plaster",
                    X = x, Y = gy + th * 0.5, Z = sgn * az, SX = size, SY = th, SZ = size * 0.7,
                    YawDeg = r0 * 180.0, Edge = edge, Region = RegionOf(x)
                };
                plan.Add(p); plan.Foot5(p, gy);
            }

            var gum = Obj(sc, "gum");
            int gn = (int)Num(gum, "count");
            double glo = Num(gum, "min_size_m"), ghi = Num(gum, "max_size_m");
            for (int i = 0; i < gn; i++)
            {
                double r0 = Dressing.Roll(seed, i, 11), r1 = Dressing.Roll(seed, i, 12);
                double r2 = Dressing.Roll(seed, i, 13);
                double x = r0 * s.LengthM;
                double sgn = r1 < 0.5 ? 1 : -1;
                // Footway only. Gum on the carriageway would be wrong and
                // nobody would ever see it.
                double az = s.FootwayFrontZ + 0.10 + (s.FootwayWidthM - 0.20) * r2;
                double size = glo + (ghi - glo) * r2;
                plan.GroundAt(x, sgn * az, out double gy, out string edge);
                var p = new Piece
                {
                    Bom = "G9_chewing_gum", Name = "gum" + i, Shape = "cyl", Surface = "concrete",
                    X = x, Y = gy + 0.001, Z = sgn * az, SX = size, SY = 0.002, SZ = size,
                    Edge = edge, Region = RegionOf(x)
                };
                plan.Add(p); plan.Foot5(p, gy);
            }
        }

        // ---- the cameras, the two conditions and the four matched shots ----

        static void Optics(Plan plan, Dictionary<string, object> root)
        {
            foreach (var c in MiniJson.GetList(root, "cameras"))
            {
                var o = MiniJson.AsObject(c);
                plan.Cameras.Add(new ShotVantage
                {
                    Id = Str(o, "id"), X = Num(o, "x_m"), Z = Num(o, "z_m"),
                    EyeHeightM = Num(o, "eye_height_m"), YawDeg = Num(o, "yaw_deg"),
                    PitchDeg = Num(o, "pitch_deg"), FovDeg = Num(o, "fov_vertical_deg")
                });
            }
            foreach (var c in MiniJson.GetList(root, "conditions"))
            {
                var o = MiniJson.AsObject(c);
                plan.Conditions.Add(new Condition
                {
                    Id = Str(o, "id"), Hdri = Str(o, "hdri"),
                    SunOn = Str(o, "sun") == "on",
                    LanternsOn = Str(o, "lanterns") == "on",
                    WindowsOn = Str(o, "window_practicals") == "on",
                    Wetness = Num(o, "wetness"), FogDensity = Num(o, "fog_density")
                });
            }
            foreach (var sh in MiniJson.GetList(root, "shots"))
            {
                var o = MiniJson.AsObject(sh);
                plan.Shots.Add(new Shot
                {
                    Id = Str(o, "id"), CameraId = Str(o, "camera"), ConditionId = Str(o, "condition")
                });
            }
            var lan = Obj(Obj(root, "lighting"), "lantern");
            var rgb = MiniJson.GetList(lan, "gamma_srgb");
            plan.LampR = ToD(rgb[0]); plan.LampG = ToD(rgb[1]); plan.LampB = ToD(rgb[2]);
            plan.LampRangeM = Num(lan, "range_m");
            plan.LampIntensity = Num(lan, "intensity");
            var sun = Obj(Obj(root, "lighting"), "sun");
            plan.SunElevationDeg = Num(sun, "day_elevation_deg");
            plan.SunAzimuthDeg = Num(sun, "day_azimuth_deg");
            var tiling = Obj(root, "surface_tiling");
            plan.TilingDefaultM = Num(tiling, "default_m");
            foreach (var kv in Obj(tiling, "per_surface_m"))
                plan.TilingM[kv.Key] = ToD(kv.Value);
        }

        // ---- readers that throw rather than default ----

        static Dictionary<string, object> Obj(Dictionary<string, object> o, string k)
        {
            var v = MiniJson.GetObject(o, k);
            if (v == null) throw new KeyNotFoundException(k);
            return v;
        }

        static string Str(Dictionary<string, object> o, string k)
        {
            var v = MiniJson.GetString(o, k);
            if (v == null) throw new KeyNotFoundException(k);
            return v;
        }

        static double Num(Dictionary<string, object> o, string k)
        {
            if (o == null || !o.TryGetValue(k, out var v) || v == null)
                throw new KeyNotFoundException(k);
            return ToD(v);
        }

        static double ToD(object v) => Convert.ToDouble(v, CultureInfo.InvariantCulture);
    }
}
