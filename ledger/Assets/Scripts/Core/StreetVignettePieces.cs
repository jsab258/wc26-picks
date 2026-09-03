using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Ledger.Core
{
    /// THE FLAT PIECE LIST: ONE STREET, WRITTEN DOWN ONCE, READ BY BOTH
    /// ENGINES.
    ///
    /// WHY THIS FILE EXISTS AND WHAT IT IS FOR. The engine comparison is only
    /// worth running if every difference in a judged pair is a RENDERER
    /// difference. Two emitters reading `vignette-scene.json` and each doing
    /// its own layout is two chances to disagree about where a kerb goes, and
    /// a disagreement of that kind renders as a lighting difference to
    /// anybody looking at the two stills. So the layout is done ONCE, here,
    /// by the layer CoreTests can run, and written to
    /// `production/specs/vignette-pieces.json`. Unity consumes
    /// `StreetVignette.Plan` in memory; Unreal consumes this file; both are
    /// the same 546 objects because both came out of `StreetVignette.Read`.
    ///
    /// IT STAYS ADMISSIBLE UNDER THE SHARED-JSON RULE BY CONSTRUCTION. D1b
    /// requires every object in each engine to arrive from one shared JSON
    /// through a generator. It still does: the shared JSON is the source, the
    /// generator is `StreetVignette`, and this file is that generator's
    /// output written down rather than a second opinion about it. Nothing
    /// here decides a dimension, computes a level or invents a default. If a
    /// number appears in this file that is not in `StreetVignette.Plan`, that
    /// is a bug in this file.
    ///
    /// WHY THE FORMATTING IS HERE AND NOT IN EITHER EMITTER. The standing
    /// rule from 25 August: measurement arithmetic and formatting live where
    /// the tests run. A writer in the Unity layer ships UNRUN, and an unrun
    /// writer producing a plausible-looking JSON file is the silent-instrument
    /// failure this project keeps paying for. `Write` returns a string and
    /// touches no disk, so CoreTests can compare it to the committed bytes
    /// without a file system in the loop.
    ///
    /// WHY IT IS BYTE-DETERMINISTIC, AND WHAT THAT COSTS. The drift guard is
    /// a byte comparison, which is the only kind that cannot be argued with,
    /// so every source of run-to-run variation is removed here rather than
    /// tolerated: every double goes through `Number` at a fixed six decimals,
    /// every dictionary is emitted in ordinal key order (a
    /// `Dictionary&lt;,&gt;`'s enumeration order is not part of its contract),
    /// every line ends in a bare `\n` whatever the host platform thinks a line
    /// ending is, and no timestamp, path or machine name appears anywhere in
    /// the output. THE COST is quantisation: a coordinate in this file is
    /// rounded to a micrometre, so Unreal stands its objects up to 0.5 um from
    /// where Unity stands the same object from the unrounded plan. That is
    /// four orders of magnitude below the thinnest piece in the scene (2 mm of
    /// chewing gum) and is stated here so no later reader has to rediscover
    /// that the two engines are not bit-identical by construction.
    ///
    /// ONE PIECE PER LINE, deliberately. A 546-object scene serialised as one
    /// line is a diff nobody can read, and the whole value of committing this
    /// file is that a layout change shows up in review as the pieces that
    /// moved.
    public static class StreetVignettePieces
    {
        /// Bumped when a reader would break. A consumer that does not
        /// recognise the string must refuse rather than guess, which is the
        /// same fail-closed rule the scene reader follows.
        public const string Schema = "ledger.vignette-pieces/1";

        /// Six decimals on a metre is a micrometre; on a degree it is about
        /// 0.1 mm of arc at the far end of the longest piece in the scene.
        /// Chosen so the printed value is shorter than the double and still
        /// far finer than anything the renderer can show.
        public const int Decimals = 6;

        /// THE PATH THIS TEXT BELONGS AT, said once so the writer and the
        /// guard cannot disagree about it. Relative to the repository root.
        public const string RelativePath = "production/specs/vignette-pieces.json";

        /// ONE NUMBER, WRITTEN THE SAME WAY EVERY TIME.
        ///
        /// Three faults are closed here and each of them has bitten a project
        /// somewhere: `ToString()` under a comma-decimal culture emits
        /// `1,5` and produces a file no JSON parser will read; negative zero
        /// prints as `-0` and makes a byte comparison fail on a value that is
        /// numerically identical; and a NaN or an infinity prints as `NaN`,
        /// which is not JSON at all and would ship a file that parses
        /// nowhere. The first two are fixed, the third THROWS, because a
        /// piece list containing a NaN coordinate is not a file worth
        /// writing and the failure should land on the writer rather than on
        /// whatever tries to read it three weeks later.
        public static string Number(double v)
        {
            if (double.IsNaN(v) || double.IsInfinity(v))
                throw new ArgumentOutOfRangeException(
                    "v", "vignette piece list cannot serialise " +
                         v.ToString(CultureInfo.InvariantCulture));
            double r = Math.Round(v, Decimals, MidpointRounding.AwayFromZero);
            if (r == 0) r = 0;  // -0.0 == 0.0 is true, so this kills the sign
            return r.ToString("0.######", CultureInfo.InvariantCulture);
        }

        static string Q(string s) => s == null ? "null" : "\"" + MiniJson.EscapeString(s) + "\"";

        static string Kv(string key, string rawValue) => Q(key) + ":" + rawValue;

        static string Kn(string key, double v) => Q(key) + ":" + Number(v);

        static string Ks(string key, string v) => Q(key) + ":" + Q(v);

        static string Kb(string key, bool v) => Q(key) + ":" + (v ? "true" : "false");

        static string Ki(string key, int v) => Q(key) + ":" + v.ToString(CultureInfo.InvariantCulture);

        /// A JSON array body, in the list's own order. The order IS the
        /// contract for `lit_names`: it is the order the parade emitted the
        /// cards in, so two engines walking the array light the same windows
        /// in the same sequence and a diff of this file reads as a list of
        /// windows rather than a reshuffle.
        static string IntList(List<int> v)
        {
            var parts = new List<string>(v.Count);
            foreach (var i in v) parts.Add(i.ToString(CultureInfo.InvariantCulture));
            return string.Join(",", parts.ToArray());
        }

        static string StrList(List<string> v)
        {
            var parts = new List<string>(v.Count);
            foreach (var t in v) parts.Add(Q(t));
            return string.Join(",", parts.ToArray());
        }

        /// ONE PIECE AS ONE LINE. Public because it is the unit the guard
        /// reports a difference in, and because a reader written against
        /// this file wants the field list in one place rather than inferred
        /// from a sample.
        ///
        /// `edge` and `region` are carried even though they are not
        /// geometry: they are the axes the placement instrument breaks down
        /// on, and the alternative is the Unreal side re-deriving a band
        /// boundary and reporting its rows against a different partition
        /// than Unity's. Two breakdowns of one scene that do not line up is
        /// the same failure as two layouts, one level up.
        public static string PieceLine(StreetVignette.Piece p)
        {
            var sb = new StringBuilder(256);
            sb.Append('{');
            sb.Append(Ks("bom", p.Bom)).Append(',');
            sb.Append(Ks("name", p.Name)).Append(',');
            sb.Append(Ks("shape", p.Shape)).Append(',');
            sb.Append(Ks("surface", p.Surface)).Append(',');
            // WHAT TO LOAD, AND NULL FOR A PRIMITIVE. Five hundred and fifty
            // of these lines carry `"asset":null` and forty-three carry a
            // held prop's stem or a picture's path with its crop; the field
            // is written on every line anyway, because a reader that has to
            // ask whether a key is present before it can parse a line is a
            // reader with two code paths, and the Unreal one is not written
            // yet. `null` is JSON, not a string.
            sb.Append(Ks("asset", p.Asset)).Append(',');
            sb.Append(Kn("x_m", p.X)).Append(',');
            sb.Append(Kn("y_m", p.Y)).Append(',');
            sb.Append(Kn("z_m", p.Z)).Append(',');
            sb.Append(Kn("sx_m", p.SX)).Append(',');
            sb.Append(Kn("sy_m", p.SY)).Append(',');
            sb.Append(Kn("sz_m", p.SZ)).Append(',');
            sb.Append(Kn("pitch_deg", p.PitchDeg)).Append(',');
            sb.Append(Kn("yaw_deg", p.YawDeg)).Append(',');
            // ROLL IS NOT AN AFTERTHOUGHT AND IT IS THE FIELD THIS LIST IS
            // MOST LIKELY TO LOSE. A cylinder's axis is local +y in both
            // engines, so every pipe, boom, gutter and handrail in the scene
            // is a cylinder ROTATED, and nine of the 146 are rolled. A piece
            // list that carries pitch and yaw and quietly drops roll writes
            // the same 546 lines, passes a count check, and stands nine pipes
            // on end in Unreal while Unity lies them down. The guard's
            // round-trip half exists for exactly this field.
            sb.Append(Kn("roll_deg", p.RollDeg)).Append(',');
            sb.Append(Ks("edge", p.Edge)).Append(',');
            sb.Append(Ks("region", p.Region)).Append(',');
            sb.Append(Kb("emissive", p.Emissive));
            sb.Append('}');
            return sb.ToString();
        }

        /// HOW MANY PIECES CARRY TWO OR MORE NON-ZERO ROTATIONS.
        ///
        /// `StreetVignetteHost` states in a comment that no piece in this
        /// scene does, and therefore that the Euler composition order has
        /// never been exercised and the two engines cannot differ on it. That
        /// comment says in as many words that no shipped test counts it, so
        /// this counts it. It is the number that decides whether Unreal may
        /// pick any composition order it likes: at zero, it may; above zero,
        /// Core owes a statement of what it meant by the pair and the two
        /// engines can disagree about a rotation while every other check
        /// here passes.
        public static int MultiRotationCount(List<StreetVignette.Piece> pieces)
        {
            int n = 0;
            foreach (var p in pieces)
            {
                int turns = 0;
                if (Math.Abs(p.PitchDeg) > 1e-9) turns++;
                if (Math.Abs(p.YawDeg) > 1e-9) turns++;
                if (Math.Abs(p.RollDeg) > 1e-9) turns++;
                if (turns >= 2) n++;
            }
            return n;
        }

        /// How many pieces carry one shape. Whole-list count, and the
        /// caller names the shape so `mesh` and `decal` cannot be counted by
        /// two different rules in two places.
        public static int ShapeCount(List<StreetVignette.Piece> pieces, string shape)
        {
            int n = 0;
            foreach (var p in pieces) if (p.Shape == shape) n++;
            return n;
        }

        /// How many pieces are marked emissive. Whole-list count.
        public static int EmissiveCount(List<StreetVignette.Piece> pieces)
        {
            int n = 0;
            foreach (var p in pieces) if (p.Emissive) n++;
            return n;
        }

        /// How many DISTINCT names the list carries. The `Piece` contract
        /// says the name is unique and that the still and the log share it;
        /// a duplicate makes a per-object report ambiguous in both engines at
        /// once, so the count is emitted beside `pieces` and the two being
        /// equal is the assertion.
        public static int UniqueNameCount(List<StreetVignette.Piece> pieces)
        {
            var seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (var p in pieces) seen.Add(p.Name ?? "");
            return seen.Count;
        }

        /// THE WHOLE FILE, AS TEXT. No I/O: the caller decides where bytes go,
        /// which is what lets the drift guard compare without a temp file.
        public static string Write(StreetVignette.Plan plan,
                                  string aheadRun = null, int aheadPiecesThen = 0)
        {
            if (plan == null) throw new ArgumentNullException("plan");
            if (plan.Error != null)
                throw new InvalidOperationException(
                    "refusing to write a piece list from a plan that failed to read: " + plan.Error);

            var sb = new StringBuilder(200 * 1024);
            sb.Append("{\n");
            sb.Append(Ks("schema", Schema)).Append(",\n");
            sb.Append(Ks("source", "production/specs/vignette-scene.json")).Append(",\n");
            sb.Append(Ks("generator", "Ledger.Core.StreetVignettePieces.Write, via ledger/CoreTests")).Append(",\n");
            sb.Append(Ks("what",
                "The D1b street vignette as a flat list of primitives. Generated, never hand-edited: "
                + "regenerate with `dotnet run -c Release --project ledger/CoreTests -- --write-vignette-pieces`. "
                + "Both engines build from this so that every difference in a judged pair is a renderer difference.")).Append(",\n");
            sb.Append(Ks("regenerate",
                "dotnet run -c Release --project ledger/CoreTests -- --write-vignette-pieces")).Append(",\n");
            sb.Append(Ki("quantisation_decimals", Decimals)).Append(",\n");
            sb.Append(Ks("quantisation_note",
                "Every number is rounded to that many decimals, so a coordinate here is within 0.5 um of the "
                + "unrounded plan Unity builds from. Deliberate: a byte-identical drift guard needs a fixed "
                + "printed form, and 0.5 um is four orders below the thinnest piece in the scene.")).Append(",\n");

            // THE FRAME, WRITTEN DOWN WHERE THE READER IS. The convention is
            // settled and is not this file's to change; it is repeated here
            // because a consumer in another language and another engine
            // should not have to find it in a C# comment. Each engine
            // converts in ONE place, and the two conversions differ on
            // purpose: a piece is a frame, a camera is a facing.
            sb.Append(Q("frame")).Append(":{");
            sb.Append(Ks("units", "metres")).Append(',');
            sb.Append(Ks("x", "along-the-street")).Append(',');
            sb.Append(Ks("y", "up/0-at-the-road-crown")).Append(',');
            sb.Append(Ks("z", "across-the-street/+z-is-east")).Append(',');
            sb.Append(Ks("yaw_deg", "compass-bearing-from-+x/turns-+x-toward-+z")).Append(',');
            sb.Append(Ks("pitch_deg", "about-+x/positive-tips-the-+z-end-down")).Append(',');
            sb.Append(Ks("roll_deg", "about-+z/lays-a-cylinder-axis-along-the-street")).Append(',');
            sb.Append(Ks("size", "full-size-before-rotation/not-half-extents")).Append(',');
            sb.Append(Ks("centre", "x_m/y_m/z_m-is-the-CENTRE-of-the-piece")).Append(',');
            sb.Append(Ks("cylinder_axis", "local-+y-in-both-engines/height-is-sy_m/diameter-is-sx_m-and-sz_m")).Append(',');
            sb.Append(Ks("mesh_placement", "load-asset/never-scale-it/put-its-own-bounds-centre-on-x_m,y_m,z_m")).Append(',');
            sb.Append(Ks("decal_placement", "a-quad/sx_m-by-sy_m/normal-is--z-before-rotation/sz_m-is-0")).Append(',');
            sb.Append(Ks("unity_piece_rotation", "Euler(pitch,-yaw,roll)")).Append(',');
            sb.Append(Ks("unity_camera_rotation", "Euler(pitch,90-yaw,0)"));
            sb.Append("},\n");

            var counts = new List<string>();
            counts.Add(Ki("pieces", plan.Pieces.Count));
            counts.Add(Ki("unique_names", UniqueNameCount(plan.Pieces)));
            counts.Add(Ki("emissive", EmissiveCount(plan.Pieces)));
            counts.Add(Ki("multi_rotation", MultiRotationCount(plan.Pieces)));
            // THE TWO COUNTS QUEUE ITEM 046 EXISTS FOR, in the file as
            // well as on the verdict line. `props` and `decals` here are
            // what the plan ASKED FOR, which is the M of the run's
            // propsPlaced=N/M: this file cannot know what the engine
            // managed to load, and the two numbers must not be confused.
            counts.Add(Ki("props_asked", ShapeCount(plan.Pieces, "mesh")));
            counts.Add(Ki("decals_asked", ShapeCount(plan.Pieces, "decal")));
            counts.Add(Ki("bom_lines", plan.PerBom.Count));
            counts.Add(Ki("cameras", plan.Cameras.Count));
            counts.Add(Ki("conditions", plan.Conditions.Count));
            counts.Add(Ki("shots", plan.Shots.Count));
            sb.Append(Q("counts")).Append(":{").Append(string.Join(",", counts.ToArray())).Append("},\n");

            // THE ACKNOWLEDGED GAP BETWEEN THIS FILE AND THE NEWEST UNITY
            // RUN, WRITTEN ONLY WHEN ASKED FOR.
            //
            // The cross-engine check compares this file's count to the count
            // a Unity player actually stood up on the build machine. That
            // comparison is the thing that makes a judged pair admissible,
            // so it may not be loosened; but a layout change necessarily
            // lands BEFORE the Unity run that would confirm it, and without
            // a way to say so the change cannot be committed at all: the
            // check is red, verify writes no footer, and the run that would
            // clear it needs the commit.
            //
            // So the gap is DECLARED, with the run it is a gap against and
            // what that run counted. It is not a waiver: the check still
            // fails the moment a newer run lands, whatever that run says,
            // because a stale acknowledgement is an unread one.
            if (aheadRun != null)
            {
                sb.Append(Q("ahead_of_unity_run")).Append(":{");
                sb.Append(Ks("run", aheadRun)).Append(',');
                sb.Append(Ki("pieces_then", aheadPiecesThen)).Append(',');
                sb.Append(Ks("what",
                    "This file is AHEAD of the newest landed Unity run named here, which counted "
                    + "pieces_then objects. A judged pair made against that run's stills is "
                    + "inadmissible until a Unity run agrees with this file. The key is spent the "
                    + "moment any newer run lands and CoreTests then demands its removal.")).Append(',');
                sb.Append(Ks("remove_with",
                    "dotnet run -c Release --project ledger/CoreTests -- --write-vignette-pieces"));
                sb.Append("},\n");
            }

            // THE SHAPE TALLY AS THE VERDICT PRINTS IT, character for
            // character, through the same formatter the Unity host uses. It
            // is here so a reader can hold this file's line and the landed
            // run's line side by side without re-deriving either.
            sb.Append(Ks("shapes_line", StreetVignette.ShapeReport(plan.Pieces))).Append(",\n");

            // THE BILL-OF-MATERIALS ROLL CALL. Sorted, because a dictionary's
            // enumeration order is not part of its contract and an unsorted
            // one would make this file's bytes depend on the runtime.
            var bomKeys = new List<string>(plan.PerBom.Keys);
            bomKeys.Sort(StringComparer.Ordinal);
            var bomParts = new List<string>();
            foreach (var k in bomKeys) bomParts.Add(Ki(k, plan.PerBom[k]));
            sb.Append(Q("per_bom")).Append(":{").Append(string.Join(",", bomParts.ToArray())).Append("},\n");

            // THE LAMP. Gamma-encoded sRGB, which is what the plan carries
            // and what a Unity Color literal means in a gamma project. An
            // emitter in a linear project must convert and must say which it
            // used; the colour space is named in the file so that statement
            // has something to be checked against.
            sb.Append(Q("lantern")).Append(":{");
            sb.Append(Ks("colour_space", "gamma-sRGB")).Append(',');
            sb.Append(Kn("r", plan.LampR)).Append(',');
            sb.Append(Kn("g", plan.LampG)).Append(',');
            sb.Append(Kn("b", plan.LampB)).Append(',');
            sb.Append(Kn("range_m", plan.LampRangeM)).Append(',');
            sb.Append(Kn("intensity", plan.LampIntensity)).Append(',');
            sb.Append(Ks("placement", "one-point-light-0.05m-below-the-centre-of-each-emissive-piece"));
            sb.Append("},\n");

            // H5: THE WINDOW PRACTICALS, AND THE NAMES THEY LIGHT.
            //
            // The names, not the bay indices, are the contract. A reader
            // that had to turn lit_bays into objects would be re-deriving
            // the parade's bay numbering in a second language, and the Unity
            // Host's old rule (any piece name containing `_interior`) already
            // proves how that goes: by 2 September it also matched three C11
            // decal cards, so it would have lit nine things while printing
            // six. lit_bays rides beside the names as the DATA CHOICE that
            // produced them, so a reviewer can see the decision and the
            // consequence on one line.
            //
            // THE FLAT HALF IS PRINTED WITH AN EMPTY LIST RATHER THAN
            // OMITTED. D8_upper_windows carries no interior card, so those
            // two numbers light nothing today; a key that vanished when its
            // count went to zero would read as a key that was never there.
            sb.Append(Q("window_practicals")).Append(":{");
            sb.Append(Ks("colour_space", "gamma-sRGB")).Append(',');
            sb.Append(Kn("r", plan.WindowR)).Append(',');
            sb.Append(Kn("g", plan.WindowG)).Append(',');
            sb.Append(Kn("b", plan.WindowB)).Append(',');
            sb.Append(Kn("shop_intensity", plan.WindowShopIntensity)).Append(',');
            sb.Append(Kn("shop_range_m", plan.WindowShopRangeM)).Append(',');
            sb.Append(Kn("flat_intensity", plan.WindowFlatIntensity)).Append(',');
            sb.Append(Kn("flat_range_m", plan.WindowFlatRangeM)).Append(',');
            sb.Append(Ki("shop_cards", plan.WindowCards.Count)).Append(',');
            sb.Append(Ki("flat_cards", plan.WindowFlatNames.Count)).Append(',');
            sb.Append(Q("lit_bays")).Append(":[").Append(IntList(plan.WindowLitBays)).Append("],");
            sb.Append(Q("lit_names")).Append(":[").Append(StrList(plan.WindowLitNames)).Append("],");
            sb.Append(Q("flat_lit_names")).Append(":[").Append(StrList(plan.WindowFlatNames)).Append("],");
            sb.Append(Ks("placement",
                "one-point-light-0.4m-above-the-centre-of-each-lit_names-piece/shadows-off"));
            sb.Append("},\n");

            // THE TWO MULTIPLY STRENGTHS, so the Unreal side dirties its
            // street by the same amount rather than picking a number. Copied
            // into the scene file from the town's decal layer, which measured
            // them; the note travels with them there.
            sb.Append(Q("decals")).Append(":{");
            sb.Append(Kn("strength_ground", plan.DecalStrengthGround)).Append(',');
            sb.Append(Kn("strength_wall", plan.DecalStrengthWall)).Append(',');
            sb.Append(Ks("blend", "card=opaque-picture/multiply=darkens-what-is-under-it")).Append(',');
            sb.Append(Ks("crop", "in-the-asset-string-after-a-#/u0,v0,u1,v1/v-from-the-bottom"));
            sb.Append("},\n");

            sb.Append(Q("sun")).Append(":{");
            sb.Append(Kn("elevation_deg", plan.SunElevationDeg)).Append(',');
            sb.Append(Kn("azimuth_deg", plan.SunAzimuthDeg));
            sb.Append("},\n");

            // ONE TILING TABLE, NOT TWO. `StreetVignetteHost` already says
            // this in as many words: the Unreal emitter needs the same table
            // and a second copy of it would be a second street. It rides in
            // this file so the second copy has nowhere to live.
            var tileKeys = new List<string>(plan.TilingM.Keys);
            tileKeys.Sort(StringComparer.Ordinal);
            var tileParts = new List<string>();
            foreach (var k in tileKeys) tileParts.Add(Kn(k, plan.TilingM[k]));
            sb.Append(Q("surface_tiling")).Append(":{");
            sb.Append(Kn("default_m", plan.TilingDefaultM)).Append(',');
            sb.Append(Q("per_surface_m")).Append(":{").Append(string.Join(",", tileParts.ToArray())).Append("}");
            sb.Append("},\n");

            sb.Append(Q("cameras")).Append(":[\n");
            for (int i = 0; i < plan.Cameras.Count; i++)
            {
                var c = plan.Cameras[i];
                bool camFound = plan.GroundAt(c.X, c.Z, out double camGroundY, out string camEdge);
                sb.Append('{');
                sb.Append(Ks("id", c.Id)).Append(',');
                sb.Append(Kn("x_m", c.X)).Append(',');
                sb.Append(Kn("z_m", c.Z)).Append(',');
                // NOT AN ABSOLUTE HEIGHT. The scene file measures eye height
                // from the ground under the camera, which on a footway that
                // falls 1 in 40 is not y=0; the emitter must ask its own
                // ground for the level and add this. Named in the key so the
                // Unreal side cannot read it as a world y.
                sb.Append(Kn("eye_height_above_ground_m", c.EyeHeightM)).Append(',');
                // AND THE GROUND IT IS MEASURED FROM, RESOLVED HERE.
                //
                // The key above is a height above the pavement, and the
                // footway falls 1 in 40, so an emitter that read it as a
                // world y would stand the two cameras at different heights on
                // the two sides of the street and the matched pair would not
                // be matched at all. The Unity host asks `plan.GroundAt`; an
                // Unreal emitter would have to re-implement the crossfall,
                // the channel, the kerb top and the footway fall in C++ to
                // ask the same question, and would then be comparing its own
                // second opinion about the street to its own geometry. So the
                // answer is written down: eye y is ground_y_m plus
                // eye_height_above_ground_m, in both engines, with no
                // arithmetic about the street in either.
                sb.Append(Kb("ground_found", camFound)).Append(',');
                sb.Append(Kn("ground_y_m", camGroundY)).Append(',');
                sb.Append(Ks("ground_edge", camEdge)).Append(',');
                sb.Append(Kn("yaw_deg", c.YawDeg)).Append(',');
                sb.Append(Kn("pitch_deg", c.PitchDeg)).Append(',');
                sb.Append(Kn("fov_vertical_deg", c.FovDeg));
                sb.Append('}');
                sb.Append(i + 1 < plan.Cameras.Count ? ",\n" : "\n");
            }
            sb.Append("],\n");

            sb.Append(Q("conditions")).Append(":[\n");
            for (int i = 0; i < plan.Conditions.Count; i++)
            {
                var c = plan.Conditions[i];
                sb.Append('{');
                sb.Append(Ks("id", c.Id)).Append(',');
                sb.Append(Ks("hdri", c.Hdri)).Append(',');
                sb.Append(Kb("sun", c.SunOn)).Append(',');
                sb.Append(Kb("lanterns", c.LanternsOn)).Append(',');
                sb.Append(Kb("window_practicals", c.WindowsOn)).Append(',');
                sb.Append(Kn("wetness", c.Wetness)).Append(',');
                sb.Append(Kn("fog_density", c.FogDensity));
                sb.Append('}');
                sb.Append(i + 1 < plan.Conditions.Count ? ",\n" : "\n");
            }
            sb.Append("],\n");

            sb.Append(Q("shots")).Append(":[\n");
            for (int i = 0; i < plan.Shots.Count; i++)
            {
                var s = plan.Shots[i];
                sb.Append('{');
                sb.Append(Ks("id", s.Id)).Append(',');
                sb.Append(Ks("camera", s.CameraId)).Append(',');
                sb.Append(Ks("condition", s.ConditionId));
                sb.Append('}');
                sb.Append(i + 1 < plan.Shots.Count ? ",\n" : "\n");
            }
            sb.Append("],\n");

            sb.Append(Q("pieces")).Append(":[\n");
            for (int i = 0; i < plan.Pieces.Count; i++)
            {
                sb.Append(PieceLine(plan.Pieces[i]));
                sb.Append(i + 1 < plan.Pieces.Count ? ",\n" : "\n");
            }
            sb.Append("]\n");
            sb.Append("}\n");
            return sb.ToString();
        }

        /// READ THE FILE BACK INTO PIECES.
        ///
        /// This is half the drift guard and it is the half that can see a
        /// LOST FIELD. A generator that never writes `roll_deg` and a guard
        /// that only compares the generator to itself both pass for ever; the
        /// way to catch it is to parse the committed bytes with an
        /// independent reader and re-run the shape tally on what comes back.
        /// If roll did not survive, `cylRolled` reads 0 against the plan's 9.
        ///
        /// It is also the reference implementation for the Unreal reader: the
        /// key names, the types and the fail-closed behaviour are all here,
        /// run by the test suite, rather than described in prose that a C++
        /// reader can drift away from.
        ///
        /// `error` is non-null and the return is null when a required key is
        /// missing. A missing key is never defaulted, for the same reason
        /// `StreetVignette.Read` never defaults one: a default lets two
        /// engines quietly build two different streets.
        public static List<StreetVignette.Piece> Parse(string text, out string error)
        {
            error = null;
            Dictionary<string, object> root;
            try { root = MiniJson.AsObject(MiniJson.Deserialize(text)); }
            catch (Exception e) { error = "piece list unreadable: " + e.Message; return null; }
            if (root == null) { error = "piece list is not an object"; return null; }

            string schema = MiniJson.GetString(root, "schema");
            if (schema != Schema)
            {
                error = "piece list schema is " + (schema ?? "(absent)") + ", expected " + Schema;
                return null;
            }
            var arr = MiniJson.GetList(root, "pieces");
            if (arr == null) { error = "piece list has no pieces array"; return null; }

            var outPieces = new List<StreetVignette.Piece>(arr.Count);
            for (int i = 0; i < arr.Count; i++)
            {
                var o = MiniJson.AsObject(arr[i]);
                if (o == null) { error = "piece " + i + " is not an object"; return null; }
                try
                {
                    outPieces.Add(new StreetVignette.Piece
                    {
                        Bom = S(o, "bom"), Name = S(o, "name"),
                        Shape = S(o, "shape"), Surface = S(o, "surface"),
                        Asset = S(o, "asset"),
                        X = D(o, "x_m"), Y = D(o, "y_m"), Z = D(o, "z_m"),
                        SX = D(o, "sx_m"), SY = D(o, "sy_m"), SZ = D(o, "sz_m"),
                        PitchDeg = D(o, "pitch_deg"), YawDeg = D(o, "yaw_deg"),
                        RollDeg = D(o, "roll_deg"),
                        Edge = S(o, "edge"), Region = S(o, "region"),
                        Emissive = B(o, "emissive"),
                    });
                }
                catch (Exception e)
                {
                    error = "piece " + i + " (" + (MiniJson.GetString(o, "name") ?? "unnamed") + "): " + e.Message;
                    return null;
                }
            }
            return outPieces;
        }

        // ================ PHASE A2: THE PROBES, SECOND FILE ==============

        /// THE SCHEMA OF THE PROBE LIST. Its own, bumped on its own, because
        /// a reader of the feet is not a reader of the pieces and tying them
        /// together would make every layout change look like a schema change.
        public const string FeetSchema = "ledger.vignette-feet/1";

        public const string FeetRelativePath = "production/specs/vignette-feet.json";

        /// ONE PROBE, AS THE FILE CARRIES IT.
        ///
        /// TWO HALVES, AND THE SECOND IS THE ONE THAT GETS LEFT OUT.
        /// `FootY` is where the plan says the underside of the piece sits.
        /// `DatumFound` and `DatumY` are the plan's separate answer to
        /// whether there is any ground under (x,z) at all and at what level.
        /// Eight blocks once hung over open sea at a foot gap of exactly
        /// 0.00 because only the first question was ever asked, so both
        /// travel and neither is optional.
        ///
        /// WHY THIS FILE EXISTS AT ALL. Without it the Unreal placement
        /// instrument would have to re-implement `Foot5` (five probes per
        /// footprint, half-extents swapped at yaw 90) and `GroundAt` (the
        /// crossfall, the channel, the gully dish, the kerb top, the footway
        /// fall, the plots) in C++, in a layer this container cannot compile,
        /// and would then be comparing its own second opinion about the
        /// street to its own geometry. It would pass while both were wrong.
        public struct FootRow
        {
            public string Name, Bom, Edge, Region, DatumEdge;
            public double X, Z, FootY, DatumY;
            public bool DatumFound;
        }

        /// ONE PROBE AS ONE LINE, in the same shape as `PieceLine`.
        public static string FootLine(StreetVignette.Foot f, bool datumFound,
                                      double datumY, string datumEdge)
        {
            var sb = new StringBuilder(224);
            sb.Append('{');
            sb.Append(Ks("name", f.Name)).Append(',');
            sb.Append(Ks("bom", f.Bom)).Append(',');
            // THE PIECE'S EDGE AND THE DATUM'S EDGE ARE DIFFERENT FACTS and
            // both are written. A bin whose piece is filed under
            // `east_footway` can have a corner probe land on `east_kerb`,
            // and a breakdown that folded the two would hide exactly the
            // half-on-half-off case the five probes exist to find.
            sb.Append(Ks("edge", f.Edge)).Append(',');
            sb.Append(Ks("region", f.Region)).Append(',');
            sb.Append(Kn("x_m", f.X)).Append(',');
            sb.Append(Kn("z_m", f.Z)).Append(',');
            sb.Append(Kn("foot_y_m", f.FootY)).Append(',');
            sb.Append(Kb("datum_found", datumFound)).Append(',');
            sb.Append(Kn("datum_y_m", datumY)).Append(',');
            sb.Append(Ks("datum_edge", datumEdge));
            sb.Append('}');
            return sb.ToString();
        }

        /// HOW MANY PROBES FIND NO GROUND UNDER THEM IN THE PLAN ITSELF.
        /// The analytic half, computed here so that a red number in a run
        /// can be attributed: a probe the PLAN says is over nothing is a
        /// layout fault, and a probe the plan says is over ground and the
        /// engine says is not is an emitter fault. Whole-list count; the
        /// caller prints it with `plan.Feet.Count` as its denominator.
        public static int DatumMissingCount(StreetVignette.Plan plan)
        {
            int n = 0;
            foreach (var f in plan.Feet)
                if (!plan.GroundAt(f.X, f.Z, out double _, out string __)) n++;
            return n;
        }

        /// THE WHOLE PROBE FILE, AS TEXT. No I/O, same as `Write`.
        public static string WriteFeet(StreetVignette.Plan plan,
                                       string aheadRun = null, int aheadFeetThen = 0)
        {
            if (plan == null) throw new ArgumentNullException("plan");
            if (plan.Error != null)
                throw new InvalidOperationException(
                    "refusing to write a probe list from a plan that failed to read: " + plan.Error);

            var sb = new StringBuilder(160 * 1024);
            sb.Append("{\n");
            sb.Append(Ks("schema", FeetSchema)).Append(",\n");
            sb.Append(Ks("source", "production/specs/vignette-scene.json")).Append(",\n");
            sb.Append(Ks("generator", "Ledger.Core.StreetVignettePieces.WriteFeet, via ledger/CoreTests")).Append(",\n");
            sb.Append(Ks("what",
                "The placement instrument's probe points for the D1b street vignette, five per footed "
                + "piece, with the level the plan expects under each one. Generated by the same run "
                + "that writes vignette-pieces.json, never hand-edited. An emitter raycasts its own "
                + "geometry at x_m,z_m and compares what it hits to foot_y_m; it never re-derives "
                + "Foot5 or the crossfall, because an instrument that computes its own datum is "
                + "measuring itself.")).Append(",\n");
            sb.Append(Ks("regenerate",
                "dotnet run -c Release --project ledger/CoreTests -- --write-vignette-pieces")).Append(",\n");
            sb.Append(Ki("quantisation_decimals", Decimals)).Append(",\n");
            sb.Append(Q("frame")).Append(":{");
            sb.Append(Ks("units", "metres")).Append(',');
            sb.Append(Ks("x", "along-the-street")).Append(',');
            sb.Append(Ks("y", "up/0-at-the-road-crown")).Append(',');
            sb.Append(Ks("z", "across-the-street/+z-is-east")).Append(',');
            sb.Append(Ks("foot_y_m", "where-the-PLAN-puts-the-underside-of-the-piece-at-this-probe")).Append(',');
            sb.Append(Ks("datum_y_m", "where-the-PLAN-says-the-GROUND-is-under-x_m,z_m")).Append(',');
            sb.Append(Ks("datum_found", "false-means-the-plan-itself-has-no-ground-there/not-an-engine-miss")).Append(',');
            sb.Append(Ks("gap", "engine-raycast-y-minus-foot_y_m/positive-is-floating/negative-is-sunk")).Append(',');
            sb.Append(Ks("ray", "start-3m-above-foot_y_m-and-end-2m-below/so-floating-and-sunk-both-register"));
            sb.Append("},\n");

            int missing = DatumMissingCount(plan);
            sb.Append(Q("counts")).Append(":{");
            sb.Append(Ki("feet", plan.Feet.Count)).Append(',');
            sb.Append(Ki("footed_pieces", FootedPieceCount(plan))).Append(',');
            sb.Append(Ki("pieces", plan.Pieces.Count)).Append(',');
            // ZERO WITH ITS DENOMINATOR, IN THE FILE AS WELL AS IN A RUN.
            sb.Append(Ki("datum_missing", missing)).Append(',');
            sb.Append(Ki("datum_examined", plan.Feet.Count));
            sb.Append("},\n");

            if (aheadRun != null)
            {
                sb.Append(Q("ahead_of_unity_run")).Append(":{");
                sb.Append(Ks("run", aheadRun)).Append(',');
                sb.Append(Ki("feet_then", aheadFeetThen)).Append(',');
                sb.Append(Ks("what",
                    "This file is AHEAD of the newest landed Unity run named here, whose placement "
                    + "line reported feet_then probes. Same rule as the piece list's key: it is spent "
                    + "the moment any newer run lands and CoreTests then demands its removal."));
                sb.Append("},\n");
            }

            sb.Append(Q("feet")).Append(":[\n");
            for (int i = 0; i < plan.Feet.Count; i++)
            {
                var f = plan.Feet[i];
                bool found = plan.GroundAt(f.X, f.Z, out double gy, out string gedge);
                sb.Append(FootLine(f, found, gy, gedge));
                sb.Append(i + 1 < plan.Feet.Count ? ",\n" : "\n");
            }
            sb.Append("]\n");
            sb.Append("}\n");
            return sb.ToString();
        }

        /// HOW MANY DISTINCT PIECES REACHED THE PROBE. Not the same number as
        /// `pieces`: only a piece that is supposed to be standing on
        /// something gets a `Foot5`, so this over `pieces` is the share of
        /// the scene the placement instrument can see at all.
        public static int FootedPieceCount(StreetVignette.Plan plan)
        {
            var seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (var f in plan.Feet) seen.Add(f.Name ?? "");
            return seen.Count;
        }

        /// READ THE PROBE FILE BACK. The other half of the guard, and the
        /// reference implementation for the Unreal reader, exactly as
        /// `Parse` is for the pieces. Fail-closed on a missing key.
        public static List<FootRow> ParseFeet(string text, out string error)
        {
            error = null;
            Dictionary<string, object> root;
            try { root = MiniJson.AsObject(MiniJson.Deserialize(text)); }
            catch (Exception e) { error = "probe list unreadable: " + e.Message; return null; }
            if (root == null) { error = "probe list is not an object"; return null; }
            string schema = MiniJson.GetString(root, "schema");
            if (schema != FeetSchema)
            {
                error = "probe list schema is " + (schema ?? "(absent)") + ", expected " + FeetSchema;
                return null;
            }
            var arr = MiniJson.GetList(root, "feet");
            if (arr == null) { error = "probe list has no feet array"; return null; }
            var outFeet = new List<FootRow>(arr.Count);
            for (int i = 0; i < arr.Count; i++)
            {
                var o = MiniJson.AsObject(arr[i]);
                if (o == null) { error = "probe " + i + " is not an object"; return null; }
                try
                {
                    outFeet.Add(new FootRow
                    {
                        Name = S(o, "name"), Bom = S(o, "bom"),
                        Edge = S(o, "edge"), Region = S(o, "region"),
                        X = D(o, "x_m"), Z = D(o, "z_m"), FootY = D(o, "foot_y_m"),
                        DatumFound = B(o, "datum_found"),
                        DatumY = D(o, "datum_y_m"), DatumEdge = S(o, "datum_edge"),
                    });
                }
                catch (Exception e)
                {
                    error = "probe " + i + " (" + (MiniJson.GetString(o, "name") ?? "unnamed") + "): " + e.Message;
                    return null;
                }
            }
            return outFeet;
        }

        // ============ QUEUE 041: THE AHEAD-OF-RUN KEY, JUDGED ============

        /// THE TWO ANSWERS THE CROSS-ENGINE QUESTION HAS, kept apart because
        /// they fail for different reasons and want different actions.
        /// `CountOk` is "may a judged pair be made from this file and the
        /// landed stills". `KeyOk` is "is the acknowledgement still the
        /// truth". A spent key with a caught-up run leaves the first true
        /// and the second false, and the fix is to regenerate without the
        /// flag rather than to land anything.
        public struct AheadOfRunVerdict
        {
            public bool CountOk, KeyOk;
            public string CountLine, KeyLine;
        }

        /// JUDGE THE FILE, THE KEY AND THE NEWEST LANDED RUN. Pure: every
        /// input is a value, so CoreTests can plant a layout change, a stale
        /// key and a caught-up run without a Unity run existing for any of
        /// them. No spaces inside any value on either line.
        public static AheadOfRunVerdict JudgeAheadOfRun(
            int fileCount, bool haveKey, string keyRun, int keyCountThen,
            bool haveRun, string newestRun, int newestCount)
        {
            var v = new AheadOfRunVerdict { CountOk = false, KeyOk = true };
            if (!haveRun)
            {
                // NOTHING MEASURED, IN WORDS. No landed run carries the line,
                // so the file's count has nothing to be checked against and
                // that is not the same as agreement.
                v.CountLine = "CROSS-ENGINE nothing-measured file=" + fileCount
                            + " landedRunsWithTheLine=0";
                v.KeyLine = haveKey
                    ? "AHEAD-OF-RUN-KEY unjudgeable run=" + Safe(keyRun) + " no-landed-run-to-compare"
                    : "AHEAD-OF-RUN-KEY absent nothing-to-judge";
                v.KeyOk = !haveKey;
                return v;
            }
            if (!haveKey)
            {
                v.CountOk = (newestCount == fileCount);
                v.CountLine = "CROSS-ENGINE " + (v.CountOk ? "agreed" : "DISAGREED")
                            + " file=" + fileCount + " run=" + Safe(newestRun) + " counted=" + newestCount;
                v.KeyLine = "AHEAD-OF-RUN-KEY absent nothing-to-judge";
                return v;
            }
            if (!string.Equals(keyRun, newestRun, StringComparison.Ordinal))
            {
                // THE KEY IS SPENT. A newer run has landed, so whatever the
                // key acknowledged is no longer the state of the world. The
                // count is judged against the new run on its own merits and
                // the key must go whichever way that lands, because an
                // acknowledgement nobody re-read is a waiver.
                v.CountOk = (newestCount == fileCount);
                v.CountLine = "CROSS-ENGINE " + (v.CountOk ? "agreed" : "DISAGREED")
                            + " file=" + fileCount + " run=" + Safe(newestRun) + " counted=" + newestCount
                            + " keyIgnoredBecauseItNames=" + Safe(keyRun);
                v.KeyOk = false;
                v.KeyLine = "AHEAD-OF-RUN-KEY stale names=" + Safe(keyRun)
                          + " newestLanded=" + Safe(newestRun)
                          + " remove-it-by-regenerating-without---ahead-of-run";
                return v;
            }
            if (newestCount == fileCount)
            {
                // The named run IS the newest and it agrees, so there is no
                // gap left to acknowledge and the key is describing a state
                // that has ended.
                v.CountOk = true;
                v.CountLine = "CROSS-ENGINE agreed file=" + fileCount
                            + " run=" + Safe(newestRun) + " counted=" + newestCount;
                v.KeyOk = false;
                v.KeyLine = "AHEAD-OF-RUN-KEY spent run=" + Safe(keyRun)
                          + " caught-up-at=" + newestCount
                          + " remove-it-by-regenerating-without---ahead-of-run";
                return v;
            }
            if (keyCountThen != newestCount)
            {
                // The key names the newest run and MISDESCRIBES it. That is
                // worse than a stale key: it is a written claim about a
                // landed measurement that the measurement does not support.
                v.CountOk = false;
                v.CountLine = "CROSS-ENGINE DISAGREED file=" + fileCount
                            + " run=" + Safe(newestRun) + " counted=" + newestCount
                            + " keyClaimed=" + keyCountThen;
                v.KeyOk = false;
                v.KeyLine = "AHEAD-OF-RUN-KEY misdescribes run=" + Safe(keyRun)
                          + " claimed=" + keyCountThen + " actual=" + newestCount;
                return v;
            }
            v.CountOk = true;
            v.CountLine = "AHEAD-OF-RUN " + Safe(newestRun) + " file=" + fileCount
                        + " run=" + newestCount + " acknowledged";
            v.KeyLine = "AHEAD-OF-RUN-KEY current names=" + Safe(keyRun)
                      + " which-is-the-newest-landed-run";
            return v;
        }

        /// No spaces and no empty string in a printed value, because every
        /// reader in this project splits on whitespace and an empty value
        /// silently shifts the next key into its place.
        static string Safe(string s)
        {
            if (string.IsNullOrEmpty(s)) return "none";
            var sb = new StringBuilder(s.Length);
            foreach (var c in s) sb.Append(char.IsWhiteSpace(c) ? '~' : c);
            return sb.ToString();
        }

        static string S(Dictionary<string, object> o, string k)
        {
            if (!o.TryGetValue(k, out var v)) throw new KeyNotFoundException("missing key " + k);
            return v as string;
        }

        static double D(Dictionary<string, object> o, string k)
        {
            if (!o.TryGetValue(k, out var v) || v == null)
                throw new KeyNotFoundException("missing key " + k);
            return Convert.ToDouble(v, CultureInfo.InvariantCulture);
        }

        static bool B(Dictionary<string, object> o, string k)
        {
            if (!o.TryGetValue(k, out var v) || !(v is bool))
                throw new KeyNotFoundException("missing or non-boolean key " + k);
            return (bool)v;
        }

    }
}
