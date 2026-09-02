using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// THE UNITY EMITTER FOR THE D1b STREET VIGNETTE.
    ///
    /// One half of measurement (b). `game-design/decision-D1b-rescope.md`
    /// makes the rule this class exists to obey: every object in each engine's
    /// scene arrives via its GENERATOR from one shared JSON, and a hand-edited
    /// binary scene or uasset disqualifies the still. So this file contains no
    /// dimension at all. Every metre comes from
    /// `production/specs/vignette-scene.json` by way of
    /// `Ledger.Core.StreetVignette`, which does the section, the levels, the
    /// bay layout and the scatter in the layer CoreTests can reach. What is
    /// left here is what only an engine can supply: a primitive, a material, a
    /// light, a raycast and a frame.
    ///
    /// NAME COLLISION, SAID ONCE. `Vignette` elsewhere in this codebase is the
    /// LENS vignette (`FilmGrade.Vignette`, `LightModel.VignetteCorner`).
    /// Everything to do with the D1b street scene is prefixed
    /// `StreetVignette`.
    ///
    /// WHAT IT PRINTS, AND WHY THAT IS THE POINT. A scene that stands up and
    /// is never measured is a scene nobody can trust from a log. Three
    /// instruments run before any picture is taken: the piece count against
    /// the plan, the bill-of-materials roll call (which authorised line
    /// emitted nothing), and the placement metric in both its halves. All
    /// three land in the verdict file through the same channel the sim uses.
    public class StreetVignetteHost : MonoBehaviour
    {
        /// Where the shared scene lands in a player build.
        /// `tools/stage-vignette-scene.py` puts it there from
        /// `production/specs/`, which is the same shape as the voice staging:
        /// one source in the repository, copied to where Unity will carry it,
        /// never a second committed copy that can drift.
        const string SceneRelative = "Vignette/scene.json";

        /// HOW MANY FRAMES THE FRAME TIME IS A MEDIAN OF, and how many are
        /// thrown away first. The re-scope ruling requires the frame time
        /// printed beside every still's identifier, and a single timed render
        /// is a measurement of whatever the driver was doing that millisecond.
        /// Warm-up frames are discarded because the first render after a
        /// condition change compiles shader variants and uploads a cubemap,
        /// which is a real cost but not the one a comparison is about.
        const int WarmFrames = 8;
        const int TimedFrames = 24;

        const int ShotWidth = 1280, ShotHeight = 720;

        Camera _cam;
        Light _sun;
        readonly List<Light> _lanterns = new List<Light>();
        readonly List<Light> _windows = new List<Light>();
        int _errors;

        void Start() { StartCoroutine(Run()); }

        IEnumerator Run()
        {
            Log("run starting; scene from " + SceneRelative);
            string path = Path.Combine(Application.streamingAssetsPath, SceneRelative);
            if (!File.Exists(path))
            {
                // A RUN THAT MEASURED NOTHING SAYS SO, in words. This one is
                // the whole point of the staging step existing, and a missing
                // file here reads exactly like a broken emitter unless it is
                // named.
                Log("nothing measured: no scene file at " + path
                    + " (run tools/stage-vignette-scene.py before the build)");
                Finish(2);
                yield break;
            }

            var plan = StreetVignette.Read(File.ReadAllText(path));
            if (plan.Error != null)
            {
                Log("nothing measured: " + plan.Error);
                Finish(2);
                yield break;
            }
            Log(string.Format(CultureInfo.InvariantCulture,
                "plan pieces={0} feet={1} cameras={2} conditions={3} shots={4}",
                plan.Pieces.Count, plan.Feet.Count, plan.Cameras.Count,
                plan.Conditions.Count, plan.Shots.Count));

            AssetLibrary.Initialize();
            SceneLighting.ApplyQuality();

            // THE SCENE ITSELF. Emitted, counted, and the count checked
            // against the plan: an emitter that silently drops a piece is
            // exactly the failure the admissibility rule is about, and
            // "looked fine" cannot see it.
            var root = new GameObject("StreetVignette");
            int made = 0;
            foreach (var p in plan.Pieces)
                if (Emit(root.transform, plan, p)) made++;
            Log(string.Format(CultureInfo.InvariantCulture,
                "emitted pieces={0}/{1} errors={2}", made, plan.Pieces.Count, _errors));

            Lights(root.transform, plan);
            Log(string.Format(CultureInfo.InvariantCulture,
                "practicals lanterns={0} windows={1}", _lanterns.Count, _windows.Count));

            // Colliders exist by construction on a Unity primitive, but the
            // physics world is only rebuilt at the end of the frame, so the
            // probe would raycast into nothing if it ran now.
            yield return null;
            Physics.SyncTransforms();

            Probe(plan);
            Log(StreetVignettePlacement.BomReport(plan.PerBom, Authorised));

            _cam = MakeCamera();
            foreach (var shot in plan.Shots) yield return Shoot(plan, shot);

            Log("done. errors=" + _errors);
            Finish(_errors == 0 ? 0 : 1);
        }

        // ---- the geometry ----------------------------------------------

        bool Emit(Transform parent, StreetVignette.Plan plan, StreetVignette.Piece p)
        {
            GameObject go;
            try
            {
                go = GameObject.CreatePrimitive(p.Shape == "cyl"
                    ? PrimitiveType.Cylinder : PrimitiveType.Cube);
            }
            catch (System.Exception e)
            {
                _errors++;
                Log("emit failed for " + p.Name + ": " + e.Message);
                return false;
            }
            go.name = p.Name;
            go.transform.SetParent(parent, false);
            go.transform.position = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
            // Unity's yaw is measured from +z and the scene file's from +x, so
            // the ninety is the frame conversion and it happens HERE, once,
            // which is where the scene file says each emitter must do it.
            go.transform.rotation = Quaternion.Euler((float)p.PitchDeg,
                                                     90f - (float)p.YawDeg, 0f);
            // A Unity cylinder is 2 units tall and 1 across, so its Y scale is
            // half the height asked for. A cube is 1 in every axis.
            go.transform.localScale = p.Shape == "cyl"
                ? new Vector3((float)p.SX, (float)p.SY * 0.5f, (float)p.SZ)
                : new Vector3((float)p.SX, (float)p.SY, (float)p.SZ);

            var r = go.GetComponent<Renderer>();
            r.sharedMaterial = p.Emissive
                ? Lantern(plan)
                : AssetLibrary.Material(p.Surface ?? AssetLibrary.Concrete);
            if (!p.Emissive) Tile(r, plan, p);
            return true;
        }

        /// PER-OBJECT TILING SO A FORTY-TWO METRE ROAD IS NOT ONE STRETCHED
        /// PHOTOGRAPH. Metres per repeat comes from the scene file, because
        /// the Unreal emitter needs the same table and a second copy of it
        /// would be a second street.
        ///
        /// THE ASPECT CORRECTION IS `TextureFit.Isotropic`, the same call
        /// `WorldBuilder.SetTiling` makes and for the same reason: two of the
        /// pack's textures are not square, and a raw pair renders them oblong
        /// on exactly the objects that tile per size. One implementation, in
        /// Core, tested there.
        static void Tile(Renderer r, StreetVignette.Plan plan, StreetVignette.Piece p)
        {
            double m = plan.TileMetres(p.Surface);
            if (m <= 0) return;
            double u = Mathf.Max(1f, (float)(p.SX / m));
            double v = Mathf.Max(1f, (float)(System.Math.Max(p.SY, p.SZ) / m));
            var tex = r.sharedMaterial != null ? r.sharedMaterial.mainTexture : null;
            if (tex != null) TextureFit.Isotropic(u, v, tex.width, tex.height, out u, out v);
            var mpb = new MaterialPropertyBlock();
            r.GetPropertyBlock(mpb);
            mpb.SetVector("_MainTex_ST", new Vector4((float)u, (float)v, 0, 0));
            r.SetPropertyBlock(mpb);
        }

        Material _lantern;
        Material Lantern(StreetVignette.Plan plan)
        {
            if (_lantern != null) return _lantern;
            // 589 nm through the CIE tables and the sRGB matrix, computed in
            // the scene file and quoted there. Not an amber chosen by eye.
            var c = new Color((float)plan.LampR, (float)plan.LampG, (float)plan.LampB, 1f);
            _lantern = new Material(AssetLibrary.Opaque(c)) { name = "mat_sodium_bowl" };
            _lantern.EnableKeyword("_EMISSION");
            _lantern.SetColor("_EmissionColor", c * 2f);
            return _lantern;
        }

        // ---- H4 and H5: the practicals, placed at the geometry ----------

        void Lights(Transform parent, StreetVignette.Plan plan)
        {
            foreach (var p in plan.Pieces)
            {
                if (!p.Emissive) continue;
                // THE LIGHT AND THE BOWL ARE EMITTED TOGETHER, which the bill
                // of materials asks for in as many words: the geometry is E2
                // and the light is H4, and separating them is how a lamp comes
                // to glow with nothing lit under it.
                var go = new GameObject("light_" + p.Name);
                go.transform.SetParent(parent, false);
                go.transform.position = new Vector3((float)p.X, (float)p.Y - 0.05f, (float)p.Z);
                var l = go.AddComponent<Light>();
                l.type = LightType.Point;
                l.color = new Color((float)plan.LampR, (float)plan.LampG, (float)plan.LampB, 1f);
                l.range = (float)plan.LampRangeM;
                l.intensity = (float)plan.LampIntensity;
                l.shadows = LightShadows.Soft;
                _lanterns.Add(l);
            }
            // H5: the spill from a lit shopfront onto the wet pavement, which
            // is the second light source of the night frame and the one that
            // makes a wet pavement worth having. Placed at the interior cards
            // the shopfront emitter already put behind the glass, so a lit
            // window always has something behind it to be lit.
            foreach (var p in plan.Pieces)
            {
                if (!p.Name.Contains("_interior")) continue;
                var go = new GameObject("light_" + p.Name);
                go.transform.SetParent(parent, false);
                go.transform.position = new Vector3((float)p.X, (float)p.Y + 0.4f, (float)p.Z);
                var l = go.AddComponent<Light>();
                l.type = LightType.Point;
                l.color = new Color(1f, 0.86f, 0.62f, 1f);
                l.range = 7f;
                l.intensity = 1.6f;
                l.shadows = LightShadows.None;
                _windows.Add(l);
            }
        }

        // ---- the placement instrument, both halves ----------------------

        /// RAYCAST EVERY FOOTPRINT PROBE AT THE GEOMETRY THIS EMITTER
        /// ACTUALLY BUILT, and hand the raw pair to Core, which does the
        /// arithmetic and the formatting.
        ///
        /// THE COMPARISON IS PLAN AGAINST ENGINE, deliberately. Asking the
        /// plan where the ground is and then comparing that to the plan would
        /// be the instrument measuring itself, and it would pass while the
        /// emitter put every object a metre in the air.
        ///
        /// THE RAY STARTS ABOVE AND ENDS BELOW the level the plan expects, so
        /// a piece that is floating and a piece that is sunk are both found;
        /// a ray cast downward from the foot itself can only ever find the
        /// second kind.
        void Probe(StreetVignette.Plan plan)
        {
            var place = new StreetVignettePlacement();
            place.NotePieces(plan.Pieces.Count);
            const float above = 3.0f, below = 2.0f;
            foreach (var f in plan.Feet)
            {
                var from = new Vector3((float)f.X, (float)f.FootY + above, (float)f.Z);
                bool hit = false; float y = 0;
                var hits = Physics.RaycastAll(from, Vector3.down, above + below);
                float best = float.MaxValue;
                foreach (var h in hits)
                {
                    // Only the ground counts as a datum. A probe that lands on
                    // the object's own body would report a perfect gap for a
                    // piece hanging in the air, which is the fault in its
                    // purest form.
                    if (!h.collider.name.StartsWith("ground_")) continue;
                    float d = (float)f.FootY - h.point.y;
                    if (Mathf.Abs(d) < best) { best = Mathf.Abs(d); y = h.point.y; hit = true; }
                }
                place.Probe(f.Bom, f.Edge, f.Region, f.Name, f.FootY, hit, y);
            }
            foreach (var line in place.Report()) Log(line);
        }

        /// The bill-of-materials lines this scene is answerable for. The same
        /// list `CoreTests.StreetVignetteAuthorised` asserts against, and the
        /// duplication is deliberate and bounded: CoreTests cannot link the
        /// Unity layer, so the choice is one list checked by a test and read
        /// here, or no check at all. If they drift, the test fails first.
        static readonly List<string> Authorised = new List<string>
        {
            "A0_ground_planes", "B1_kerbstone_run", "B2_dropped_kerb", "B3_gully_recess",
            "C1_terrace_carcass", "C5_shopfront_assembly", "C7_shop_glazing",
            "C8_door_shop", "C9_door_side", "C13_sills_lintels",
            "D2_chimney_stack", "D4_tv_aerial", "D5_downpipe", "D6_gutter_run",
            "D7_parapet_coping", "D8_upper_windows",
            "E1_lighting_column", "E2_sodium_lantern_head", "E3_telephone_kiosk",
            "E4_pillar_box", "E8_guard_railing", "E13_household_dustbin",
            "G8_litter", "G9_chewing_gum",
        };

        // ---- the two conditions and the four matched frames -------------

        UnityEngine.Camera MakeCamera()
        {
            var go = new GameObject("StreetVignetteCamera");
            var cam = go.AddComponent<Camera>();
            cam.nearClipPlane = 0.05f;
            cam.farClipPlane = 400f;
            cam.tag = "MainCamera";
            return cam;
        }

        void Apply(StreetVignette.Plan plan, StreetVignette.Condition c)
        {
            if (_sun == null)
            {
                var go = new GameObject("StreetVignetteSun");
                _sun = go.AddComponent<Light>();
                _sun.type = LightType.Directional;
                _sun.shadows = LightShadows.Soft;
            }
            _sun.enabled = c.SunOn;
            // Elevation and azimuth come from the scene file, where the
            // elevation is arithmetic off the latitude art-direction R-B1
            // sets. A Los Santos noon sun is the fastest way to make a
            // British street read as somewhere else.
            _sun.transform.rotation = Quaternion.Euler((float)plan.SunElevationDeg,
                                                       (float)plan.SunAzimuthDeg, 0f);
            _sun.intensity = c.SunOn ? 0.85f : 0f;
            _sun.color = new Color(0.95f, 0.96f, 1f, 1f);
            foreach (var l in _lanterns) l.enabled = c.LanternsOn;
            foreach (var l in _windows) l.enabled = c.WindowsOn;

            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            var sky = c.SunOn ? new Color(0.42f, 0.46f, 0.52f) : new Color(0.05f, 0.05f, 0.07f);
            RenderSettings.ambientSkyColor = sky;
            RenderSettings.ambientEquatorColor = sky * 0.75f;
            RenderSettings.ambientGroundColor = sky * 0.45f;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogDensity = (float)c.FogDensity;
            RenderSettings.fogColor = c.SunOn
                ? new Color(0.55f, 0.58f, 0.62f) : new Color(0.06f, 0.05f, 0.05f);
            if (_cam != null)
            {
                _cam.clearFlags = CameraClearFlags.SolidColor;
                _cam.backgroundColor = RenderSettings.fogColor;
            }

            // THE HDRI, LOADED THE SAME WAY `SkyEnvironment` LOADS ITS FOUR
            // AND FAILING CLOSED ON SHAPE FOR THE SAME REASON. An .hdr
            // imports as 2D by default, `customReflectionTexture` accepts
            // only a cube, and binding a 2D one throws once per frame: one
            // run wrote 593,328 log lines and took a single screenshot. So
            // the shape is checked and NAMED rather than assumed, and a
            // wrong-shaped file leaves the ambient trilight above as the
            // whole environment.
            var tex = Resources.Load<Texture>(c.Hdri);
            if (tex == null) Log("hdri " + c.Id + " missing=" + c.Hdri);
            else if (tex.dimension != UnityEngine.Rendering.TextureDimension.Cube)
                Log("hdri " + c.Id + " wrongShape=" + c.Hdri + "(" + tex.dimension + ")");
            else
            {
                // Assigned as a `Texture`, exactly as `SkyEnvironment.Apply`
                // does it: the property takes the base type, and a cast to
                // `Cubemap` here would be a second idiom for one binding.
                RenderSettings.defaultReflectionMode =
                    UnityEngine.Rendering.DefaultReflectionMode.Custom;
                RenderSettings.customReflectionTexture = tex;
                RenderSettings.reflectionIntensity = 1f;
                Log("hdri " + c.Id + " bound=" + c.Hdri);
            }
            AssetLibrary.SetWetness((float)c.Wetness);
            DynamicGI.UpdateEnvironment();
        }

        IEnumerator Shoot(StreetVignette.Plan plan, StreetVignette.Shot shot)
        {
            StreetVignette.ShotVantage cam = default;
            bool haveCam = false;
            foreach (var c in plan.Cameras) if (c.Id == shot.CameraId) { cam = c; haveCam = true; }
            StreetVignette.Condition cond = default;
            bool haveCond = false;
            foreach (var c in plan.Conditions) if (c.Id == shot.ConditionId) { cond = c; haveCond = true; }
            if (!haveCam || !haveCond)
            {
                _errors++;
                Log("shot " + shot.Id + " nothing measured: no such "
                    + (haveCam ? "condition " + shot.ConditionId : "camera " + shot.CameraId));
                yield break;
            }

            Apply(plan, cond);

            // EYE HEIGHT IS MEASURED FROM THE PAVEMENT UNDER THE CAMERA, not
            // from the scene origin. The footway falls 1 in 40 to the kerb, so
            // a camera placed at a fixed y would stand at a different height
            // on each side of the street and the two frames would not be
            // matched at all.
            plan.GroundAt(cam.X, cam.Z, out double groundY, out string edge);
            var eye = new Vector3((float)cam.X, (float)(groundY + cam.EyeHeightM), (float)cam.Z);
            _cam.transform.position = eye;
            _cam.transform.rotation = Quaternion.Euler((float)cam.PitchDeg,
                                                       90f - (float)cam.YawDeg, 0f);
            _cam.fieldOfView = (float)cam.FovDeg;
            yield return null;

            var rt = new RenderTexture(ShotWidth, ShotHeight, 24, RenderTextureFormat.ARGB32);
            var prevTarget = _cam.targetTexture;
            var prevActive = RenderTexture.active;
            double medianMs = -1;
            try
            {
                _cam.targetTexture = rt;
                for (int i = 0; i < WarmFrames; i++) _cam.Render();
                // A MEDIAN, AND IT SAYS SO IN THE KEY. The ruling requires the
                // frame time quoted beside every still, and a single timed
                // render measures whatever the driver was doing that
                // millisecond. `TimedFrames` renders, sorted, middle taken.
                var ms = new double[TimedFrames];
                var watch = new System.Diagnostics.Stopwatch();
                for (int i = 0; i < TimedFrames; i++)
                {
                    watch.Restart();
                    _cam.Render();
                    GL.Flush();
                    watch.Stop();
                    ms[i] = watch.Elapsed.TotalMilliseconds;
                }
                System.Array.Sort(ms);
                medianMs = ms.Length % 2 == 1
                    ? ms[ms.Length / 2]
                    : (ms[ms.Length / 2 - 1] + ms[ms.Length / 2]) * 0.5;

                RenderTexture.active = rt;
                var tex = new Texture2D(ShotWidth, ShotHeight, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, ShotWidth, ShotHeight), 0, 0);
                tex.Apply();
                Directory.CreateDirectory("sim-out");
                File.WriteAllBytes(Path.Combine("sim-out", shot.Id + ".jpg"), tex.EncodeToJPG(70));
                Object.Destroy(tex);
            }
            finally
            {
                _cam.targetTexture = prevTarget;
                RenderTexture.active = prevActive;
                rt.Release();
                Object.Destroy(rt);
            }

            var file = new FileInfo(Path.Combine("sim-out", shot.Id + ".jpg"));
            // ONE LINE PER FRAME, carrying the identifiers the judging pairs
            // by and the frame cost the ruling says every pair must quote. No
            // spaces inside any value: every reader of these lines splits on
            // whitespace.
            Log(string.Format(CultureInfo.InvariantCulture,
                "shot {0} camera={1} condition={2} eye={3:0.000}/on={4} " +
                "frameMedianMs={5:0.00}/of={6}warm{7} px={8}x{9} kb={10}",
                shot.Id, shot.CameraId, shot.ConditionId, eye.y, edge,
                medianMs, TimedFrames, WarmFrames, ShotWidth, ShotHeight,
                file.Exists ? file.Length / 1024 : 0));
            if (!file.Exists) _errors++;
        }

        // ---- housekeeping ----------------------------------------------

        static void Log(string s) => Debug.Log("StreetVignette: " + s);

        void Finish(int code)
        {
            if (Application.isBatchMode || Application.isEditor) Application.Quit(code);
            else Application.Quit(code);
        }
    }
}
