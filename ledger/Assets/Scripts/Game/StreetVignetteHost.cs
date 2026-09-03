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
        /// THE FLAT PRACTICALS, KEPT APART FROM THE SHOP ONES. Two BOM
        /// entries, two ranges, two intensities, and one of them lights
        /// nothing today; folding them into one list would make the empty
        /// half invisible in the count and in the condition switch.
        readonly List<Light> _flats = new List<Light>();
        /// WHAT WAS ASKED FOR, CAPTURED BEFORE ANY LOOKUP. A denominator
        /// counted from successes can never report a failure.
        int _windowsAsked, _windowCards, _flatsAsked;
        bool _sunLogged;
        int _errors;
        /// THE TWO COUNTS QUEUE ITEM 046 EXISTS FOR. Whole-run tally, in
        /// Core, because the arithmetic and the string have to live where
        /// the tests run: this layer does not compile in the review
        /// container, and an unrun formatter printing a plausible
        /// `propsPlaced=23/23` is the silent-instrument failure. Everything
        /// this file gives it is live state: did the prefab load, was the
        /// picture on disk, how tall did the mesh turn out.
        readonly StreetVignetteAssets _assets = new StreetVignetteAssets();

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
            // THE DENOMINATOR COMES OFF THE PLAN, BEFORE ANY LOADING, so a
            // run that dies halfway still prints what it was ASKED for. A
            // denominator counted from successes is a denominator that can
            // never report a failure.
            foreach (var p in plan.Pieces)
            {
                if (p.Shape == "mesh") _assets.Ask(true, p.Asset);
                else if (p.Shape == "decal") _assets.Ask(false, p.Asset);
            }
            foreach (var p in plan.Pieces)
                if (Emit(root.transform, plan, p)) made++;
            Log(string.Format(CultureInfo.InvariantCulture,
                "emitted pieces={0}/{1} errors={2}", made, plan.Pieces.Count, _errors));
            // HOW MANY PIPES WERE LAID, from the formatter CoreTests runs.
            // A piece count cannot tell a gutter from a disc; this line can,
            // and the same string is printed by the tested layer, so the
            // verdict never carries a string nothing ever ran.
            Log(StreetVignette.ShapeReport(plan.Pieces));
            // DID THE HELD BYTES REACH THE FRAME. 37 props and 14 pictures
            // sat in this repository while every shipped still was
            // primitives, and nothing said so because nothing counted.
            Log(_assets.Report());

            Lights(root.transform, plan);
            Log(string.Format(CultureInfo.InvariantCulture,
                // WHAT EACH NUMBER IS A COUNT OF, and every zero with its
                // denominator. `windowsLit` is lights actually placed over
                // the shop interior cards the parade emitted, which is the
                // only honest denominator: it is what COULD be lit. `flatsLit`
                // says the words rather than printing a bare zero, because
                // no flat has an interior card to stand a light at and
                // `flatsLit=0` alone cannot tell that from a failure.
                "practicals lanterns={0} windowsLit={1}/{2} windowsAsked={3} {4}",
                _lanterns.Count, _windows.Count, _windowCards, _windowsAsked,
                _flatsAsked == 0
                    ? "flatsLit=0/0 nothing-to-light"
                    : string.Format(CultureInfo.InvariantCulture,
                                    "flatsLit={0}/{1}", _flats.Count, _flatsAsked)));

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
            // FOUR SHAPES, AND THE LAST TWO CARRY THE HELD BYTES. They are
            // routed FIRST and by name: the primitive line below falls back
            // to a cube for anything it does not recognise, so a mesh or a
            // decal reaching it would stand up as a grey box, count as
            // emitted, and pass every gate in this file.
            if (p.Shape == "mesh") return EmitProp(parent, p);
            if (p.Shape == "decal") return EmitDecal(parent, plan, p);
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
            // THE FRAME CONVERSION FOR A BOX, WHICH IS NOT THE ONE FOR A
            // CAMERA, and the difference cost the first four frames.
            //
            // A camera is a FACING: it looks along its +z, so a bearing b is
            // Unity yaw 90 - b. That is what `Shoot` does and it is correct
            // there and unchanged. A piece is a FRAME: Core has already laid
            // its SX along the street at YawDeg 0 (`Slab` sets SX = x1 - x0,
            // `KerbPiece` sets SX = len, `Block` sets SX = bw), so yaw 0 has
            // to be the IDENTITY here. The 90 that used to sit in this line
            // was copied from the camera conversion, and Unity's
            // Euler(0,90,0) sends local +x to world -z: it built the road
            // ACROSS the street, faced the shopfronts at each other and
            // tilted the camber along the kerb instead of toward it. That is
            // what the first render showed on run 8f19add: the still under
            // game-design/sim-shots/ is overwritten by every run, so the
            // durable evidence is game-design/sim-shots/runs/8f19add.txt
            // line 97, where the engine-side probe read datumMissing=521/845
            // while the plan-side probe read 0/845 on the same scene.
            //
            // THE MINUS is the two yaw senses: the scene file's yaw turns +x
            // toward +z, Unity's turns +x toward -z. THE ROLL is what lets a
            // pipe lie down, because a cylinder's axis is local +y in both
            // engines; roll 90 lays that axis along the street and pitch 90
            // lays it across. NO piece in this scene carries two non-zero
            // rotations (0 of 546 by reading every emitting family in Core; no shipped test counts it), so
            // the composition order has never been exercised; if one ever
            // does, Unity composes Euler as Z then X then Y and Core owes a
            // statement of what it meant by the pair.
            go.transform.rotation = Quaternion.Euler((float)p.PitchDeg,
                                                     -(float)p.YawDeg,
                                                     (float)p.RollDeg);
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

        /// A HELD PROP, LOADED BY NAME AND NEVER SCALED.
        ///
        /// THROUGH `AssetLibrary.TryInstantiateProp`, WHICH IS THE ONE
        /// INSTRUMENTED DOOR. A private `Resources.Load` here would make
        /// every prop in the vignette invisible to `kitAlbedo` and would skip
        /// the arrival-albedo note; `Furniture.PlaceAt` carries the incident
        /// (a factory-white swing bin that survived a build in which every
        /// other bin went metal). Same key scheme, same door.
        ///
        /// THE PIVOT IS NOT ASSUMED, IT IS READ. Measured off the shipped
        /// .glb files: awning_02's origin is at its top-back because it hangs
        /// off a wall, poster and framed_poster are centred, drainage_grate_01
        /// sits 15 mm below its origin, and the rest stand on theirs. So the
        /// plan says where the prop's BOUNDING BOX CENTRE goes and this puts
        /// the loaded bounds centre there, which is right for all four cases
        /// and needs no per-prop offset table to go stale. `renderer.bounds`
        /// is the axis-aligned box of the already-rotated mesh, and the AABB
        /// of a rotated box is centred on that box's own centre, so the
        /// correction is exact at any yaw and not just at multiples of 90.
        bool EmitProp(Transform parent, StreetVignette.Piece p)
        {
            var rot = Quaternion.Euler((float)p.PitchDeg, -(float)p.YawDeg, (float)p.RollDeg);
            var want = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
            string key = "base_mesh_" + p.Asset;
            var go = AssetLibrary.TryInstantiateProp(key, want, rot);
            if (go == null)
            {
                // NOT AN ERROR, AND NOT SILENT EITHER. The prop pipeline
                // writes its prefabs at BUILD time, so a container with no
                // Unity has none of them; that reads differently from a
                // placement that never ran, and the reason is what says so.
                _assets.Absent(true, p.Asset, "no-prefab/Props/Prop_" + key);
                return false;
            }
            go.name = p.Name;
            go.transform.SetParent(parent, true);
            var bounds = MeshBounds(go);
            if (bounds.HasValue)
            {
                go.transform.position += want - bounds.Value.center;
                // THE PRINTER, NOT A BOUND (rule 2). The scene file's dims
                // were measured off the .glb by a script and the importer is
                // a second opinion about the same bytes; a prop placed from
                // dimensions that are not its own stands in the wrong place
                // with every count green. Core keeps the worst of the series
                // and no run has ever printed one, so there is no threshold
                // here to fail against yet.
                _assets.NoteHeight(p.Name, p.SY, bounds.Value.size.y);
            }
            // MATERIAL REPLACEMENT AND NOT A PROPERTY BLOCK. These props
            // import through glTFast, whose shader has no `_Color` for an
            // MPB to set, and they ship untextured at albedo 1.0: white
            // furniture in a wet grey street. `TintFurniture` is the one
            // implementation of the swap and it counts what the renderers
            // took, so the vignette's props land in the same instrument the
            // town's do.
            WorldBuilder.TintFurniture(go, AssetLibrary.Material(
                p.Surface ?? AssetLibrary.Concrete), key);
            _assets.Landed(true);
            return true;
        }

        /// The combined bounds of everything under a prop, or nothing at all
        /// when it has no renderer. Null rather than `default`, because a
        /// zero-size box centred on the origin would move the prop to the
        /// road crown and look like a placement bug.
        static Bounds? MeshBounds(GameObject go)
        {
            Bounds b = default; bool any = false;
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (!any) { b = r.bounds; any = true; }
                else b.Encapsulate(r.bounds);
            }
            return any ? b : (Bounds?)null;
        }

        /// A PICTURE ON A SURFACE, WHICH IS THE OTHER HALF OF 046.
        ///
        /// TWO BLENDS AND THE SCENE FILE SAYS WHICH. `card` is an opaque
        /// picture (a signboard, a bill, a lit interior). `multiply` is grime
        /// that can only ever darken what is under it, and it goes through
        /// the town's own `DecalLayer` loader and shader rather than a second
        /// copy of the colour-plus-opacity join.
        ///
        /// A MISSING IMAGE IS COUNTED, NOT THROWN. Three of the twenty
        /// pictures this street asks for are the C11 interior cards, which
        /// the image generator has not made yet: the plan asks, the run says
        /// which were absent by name, and the day the PNG lands the night
        /// frame gets it with no code change.
        bool EmitDecal(Transform parent, StreetVignette.Plan plan, StreetVignette.Piece p)
        {
            if (!StreetVignette.SplitAsset(p.Asset, out string id,
                                           out double u0, out double v0, out double u1, out double v1))
            {
                _assets.Absent(false, p.Asset, "crop-unparseable");
                return false;
            }
            bool multiply = p.Surface == "multiply";
            var root = Path.Combine(Application.streamingAssetsPath, "Decals");
            Texture2D tex = null;
            if (multiply) tex = DecalLayer.LoadSet(Path.Combine(root, id.Replace('/', Path.DirectorySeparatorChar)));
            else
            {
                var file = Path.Combine(root, id.Replace('/', Path.DirectorySeparatorChar) + ".png");
                if (File.Exists(file))
                {
                    tex = new Texture2D(2, 2, TextureFormat.RGBA32, true);
                    if (!tex.LoadImage(File.ReadAllBytes(file))) { Object.Destroy(tex); tex = null; }
                    else tex.wrapMode = TextureWrapMode.Clamp;
                }
            }
            if (tex == null)
            {
                _assets.Absent(false, id, multiply ? "no-set-dir" : "no-png-on-disk");
                return false;
            }

            var go = new GameObject(p.Name);
            go.transform.SetParent(parent, false);
            go.transform.position = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
            // THE SAME ROTATION LINE EVERY OTHER PIECE GETS, and it has to
            // be: a decal's plane is the piece's frame, its normal is -z
            // before rotation (the winding of `DecalLayer.Quad`), and the
            // piece list states that convention so the Unreal reader can
            // match it. The camera's own conversion is a different one and
            // stays where it is.
            go.transform.rotation = Quaternion.Euler((float)p.PitchDeg,
                                                     -(float)p.YawDeg,
                                                     (float)p.RollDeg);
            go.transform.localScale = new Vector3((float)p.SX, (float)p.SY, 1f);
            go.AddComponent<MeshFilter>().sharedMesh = DecalLayer.Quad();
            var mr = go.AddComponent<MeshRenderer>();
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = !multiply;
            Material mat;
            if (multiply)
            {
                var sh = Shader.Find("Hidden/LedgerDecal");
                if (sh == null)
                {
                    _assets.Absent(false, id, "shader-missing/Hidden-LedgerDecal");
                    Object.Destroy(go);
                    return false;
                }
                mat = new Material(sh) { mainTexture = tex };
                // Ground or wall, and the two strengths come from the scene
                // file where the town's measured series put them.
                bool onGround = p.Edge != null
                    && (p.Edge.EndsWith("_carriageway") || p.Edge.EndsWith("_channel"));
                mat.SetFloat("_Strength", (float)(onGround
                    ? plan.DecalStrengthGround : plan.DecalStrengthWall));
            }
            else
            {
                // An opaque picture. Standard, low smoothness, so a painted
                // signboard takes the street's light like the fascia behind
                // it instead of glowing.
                var sh = Shader.Find("Standard");
                mat = new Material(sh != null ? sh : Shader.Find("Sprites/Default"))
                { mainTexture = tex };
                mat.SetFloat("_Glossiness", 0.08f);
            }
            mat.name = "mat_decal_" + p.Name;
            // THE CROP, AND IT IS WHY THE PICTURES ARE USABLE AT ALL. The
            // generated images are photographs of a thing IN a street, so
            // fascia_fish_market is a whole shopfront with a pavement and a
            // sky in it; the rect is the part of it that is the sign.
            mat.mainTextureScale = new Vector2((float)(u1 - u0), (float)(v1 - v0));
            mat.mainTextureOffset = new Vector2((float)u0, (float)v0);
            mr.sharedMaterial = mat;
            _assets.Landed(false);
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
            //
            // WHICH WINDOWS IS A DATA CHOICE AND IT IS NO LONGER MADE HERE
            // (queue 040). This loop used to light every piece whose name
            // CONTAINED `_interior` at a colour, a range and an intensity
            // written in this file, which is two faults in one line. The
            // numbers were a second opinion no Unreal emitter could read, and
            // the name test was a rule about strings: by 2 September it also
            // matched the three C11 interior decal cards, so it would have
            // lit nine objects while `windowsLit` said six. The plan now
            // names the pieces, and this loop looks each one up. A name in
            // the plan that no piece answers to is COUNTED and named rather
            // than skipped, because a practical that never lit is exactly
            // what the count exists to find.
            var byName = new Dictionary<string, StreetVignette.Piece>();
            foreach (var p in plan.Pieces) byName[p.Name] = p;
            _windowsAsked = plan.WindowLitNames.Count;
            _windowCards = plan.WindowCards.Count;
            var missed = new List<string>();
            foreach (var name in plan.WindowLitNames)
            {
                if (!byName.TryGetValue(name, out var p)) { missed.Add(name); continue; }
                var go = new GameObject("light_" + p.Name);
                go.transform.SetParent(parent, false);
                go.transform.position = new Vector3((float)p.X, (float)p.Y + 0.4f, (float)p.Z);
                var l = go.AddComponent<Light>();
                l.type = LightType.Point;
                l.color = new Color((float)plan.WindowR, (float)plan.WindowG, (float)plan.WindowB, 1f);
                l.range = (float)plan.WindowShopRangeM;
                l.intensity = (float)plan.WindowShopIntensity;
                l.shadows = LightShadows.None;
                _windows.Add(l);
            }
            if (missed.Count > 0)
            {
                _errors++;
                Log("practicals unplaced=" + missed.Count + "/" + plan.WindowLitNames.Count
                    + " first=" + missed[0]);
            }
            // THE FLAT HALF, WHICH LIGHTS NOTHING TODAY. D8_upper_windows
            // carries no interior card, so there is no object to hang a
            // practical on and the plan's list is empty. It is placed and
            // counted through the same loop rather than being skipped,
            // because a pair of numbers that vanishes when its list is empty
            // reads as a pair nobody asked for.
            foreach (var name in plan.WindowFlatNames)
            {
                if (!byName.TryGetValue(name, out var p)) continue;
                var go = new GameObject("light_" + p.Name);
                go.transform.SetParent(parent, false);
                go.transform.position = new Vector3((float)p.X, (float)p.Y + 0.4f, (float)p.Z);
                var l = go.AddComponent<Light>();
                l.type = LightType.Point;
                l.color = new Color((float)plan.WindowR, (float)plan.WindowG, (float)plan.WindowB, 1f);
                l.range = (float)plan.WindowFlatRangeM;
                l.intensity = (float)plan.WindowFlatIntensity;
                l.shadows = LightShadows.None;
                _flats.Add(l);
            }
            _flatsAsked = plan.WindowFlatNames.Count;
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
            // The lines that carry held bytes, added 2 Sep with queue item
            // 046. Kept in step with `CoreTests.StreetVignetteAuthorised` by
            // the test that asserts against it, which fails first.
            "A5_double_yellow_lines", "A7_gully_grate", "A8_manhole",
            "C6_fascia_lettering", "C11_lit_interior_card",
            "D3_chimney_pots", "E5_bollards", "E6_public_bins",
            "E11_cones_barrier", "E12_a_board_posters", "E14_dock_clutter",
            "E18_shop_awnings", "G1_leak_stains", "G2_asphalt_damage",
            "G4_moss_damp", "G5_stickers", "G6_fly_posters",
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
            //
            // AND THE AZIMUTH IS A COMPASS BEARING, NOT A UNITY YAW. The
            // scene file's frame block puts north at +x and east at +z, so
            // the JSON's azimuth is a bearing TO the sun; a facing at
            // bearing b is Unity yaw 90 - b (the camera's own conversion);
            // and a directional light faces the way its light TRAVELS,
            // which is bearing azimuth - 180. So the yaw is 270 - azimuth,
            // and handing the bearing straight to Unity, as this line did,
            // was 140 degrees out on this scene's own numbers: the JSON's
            // day azimuth is 205, the yaw is 65, the old line set 205.
            //
            // WHAT THE DAY FRAME SHOULD SHOW, so the reading is a check and
            // not an impression: the light travels toward bearing 25, so
            // every shadow runs north-north-east, which in this frame is +x
            // rotated 25 degrees toward +z. If they run any other way, this
            // conversion is still wrong and the line below says what was
            // applied.
            float sunYaw = 270f - (float)plan.SunAzimuthDeg;
            _sun.transform.rotation = Quaternion.Euler((float)plan.SunElevationDeg,
                                                       sunYaw, 0f);
            if (!_sunLogged)
            {
                // ONE LINE PER RUN, and it prints the value ASKED FOR beside
                // the value the transform HOLDS afterwards, because the only
                // proof a conversion reached the object is reading it back.
                // The conversion itself stays UNVERIFIED until a day frame is
                // opened and the shadow direction is read against the
                // bearing: this line is what makes that reading possible.
                _sunLogged = true;
                Log(string.Format(CultureInfo.InvariantCulture,
                    "sun elevation={0:0.0} bearing={1:0.0} unityYaw={2:0.0} appliedYaw={3:0.0}",
                    plan.SunElevationDeg, plan.SunAzimuthDeg, sunYaw,
                    _sun.transform.eulerAngles.y));
            }
            _sun.intensity = c.SunOn ? 0.85f : 0f;
            _sun.color = new Color(0.95f, 0.96f, 1f, 1f);
            foreach (var l in _lanterns) l.enabled = c.LanternsOn;
            foreach (var l in _windows) l.enabled = c.WindowsOn;
            foreach (var l in _flats) l.enabled = c.WindowsOn;

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
