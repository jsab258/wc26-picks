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
        public static string Write(StreetVignette.Plan plan)
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
            sb.Append(Ks("unity_piece_rotation", "Euler(pitch,-yaw,roll)")).Append(',');
            sb.Append(Ks("unity_camera_rotation", "Euler(pitch,90-yaw,0)"));
            sb.Append("},\n");

            var counts = new List<string>();
            counts.Add(Ki("pieces", plan.Pieces.Count));
            counts.Add(Ki("unique_names", UniqueNameCount(plan.Pieces)));
            counts.Add(Ki("emissive", EmissiveCount(plan.Pieces)));
            counts.Add(Ki("multi_rotation", MultiRotationCount(plan.Pieces)));
            counts.Add(Ki("bom_lines", plan.PerBom.Count));
            counts.Add(Ki("cameras", plan.Cameras.Count));
            counts.Add(Ki("conditions", plan.Conditions.Count));
            counts.Add(Ki("shots", plan.Shots.Count));
            sb.Append(Q("counts")).Append(":{").Append(string.Join(",", counts.ToArray())).Append("},\n");

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
