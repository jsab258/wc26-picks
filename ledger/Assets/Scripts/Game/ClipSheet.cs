using UnityEngine;

namespace Ledger.Game
{
    /// A CONTACT SHEET OF EVERY ANIMATION, ON A REAL BODY.
    ///
    /// WHY THIS EXISTS. Jafar asked whether the people in the stills are moving
    /// right or whether we are playing the wrong animations, and nothing this
    /// project produces could answer it. Every committed screenshot is a street
    /// at 1280x720 where a person is about forty pixels tall; a wave and a
    /// punch are the same smudge at that size.
    ///
    /// `tools/clip-motion.py` answers the half a FILE can prove and it found
    /// two real faults — two slots holding identical bytes, and three clips
    /// whose root never moves. What no file reader can do is say which
    /// animation a clip actually IS. Every Mixamo FBX names its take
    /// "mixamo.com", so there is no internal label to check a filename against,
    /// and inferring content from the curves produced two confident findings
    /// that both died: hip HEIGHT is not comparable between clips (a stand-up
    /// legitimately starts at 8cm) and Euler ranges inflate on wrap (the walk
    /// reads 131 degrees of hip roll).
    ///
    /// So it has to be a picture, and it has to be rendered by something
    /// holding the RETARGETED humanoid rig rather than the file as shipped —
    /// which is the same reason `body-proportions.py` refuses a model the build
    /// measures happily. Where the reader and the build disagree, the build
    /// wins, and this is the build.
    ///
    /// THREE PHASES PER CLIP, NOT ONE. A single instant cannot tell a greeting
    /// from a punch, and the cheapest way to make a sheet useless is to sample
    /// every clip at the same pose. Early, middle and late.
    ///
    /// WHAT IT DELIBERATELY IS NOT. Not a gate. Nothing here can fail a build
    /// or turn red, because the judgement it supports is "does that look like a
    /// man talking", which is a person's to make. The numbers that CAN be
    /// gated already are, in `game-design/clip-findings.txt`.
    public static class ClipSheet
    {
        /// The layer everything this renders lives on, so the camera sees the
        /// body and nothing else and the city's sun cannot light it. 30 is
        /// unnamed in this project and unnamed layers render perfectly well —
        /// a name is a Project Settings entry, and needing one would put this
        /// instrument's correctness in a file nobody reviews.
        const int SheetLayer = 30;

        /// One tile. Tall rather than square because the subject is a standing
        /// figure, and 220 pixels of person is the difference between reading a
        /// pose and guessing at one — the street stills give about forty.
        const int TileWidth = 110;
        const int TileHeight = 220;
        const int PhasesPerClip = 3;
        const int ClipsPerRow = 6;

        /// Where in each clip the three samples are taken. Not 0 and not 1: a
        /// Mixamo clip's first and last frames are the same pose for anything
        /// that loops, so sampling the ends would give two identical tiles and
        /// hide the middle, which is the part that identifies the motion.
        static readonly float[] Phases = { 0.15f, 0.45f, 0.78f };

        /// Reported on the done line. `-1` is "the pass never ran", which is a
        /// different fault from "it ran and found no clips" — the distinction
        /// this project has now shipped wrong in a ratio, a gate and a
        /// diagnostic.
        public static int Tiles = -1;
        public static string Why = "not tried";

        /// Renders the sheet into `outDir`. Returns the number of clips drawn.
        ///
        /// FAILS SOFT, ALWAYS. A picture nobody asked for must never be able to
        /// stop the run that produces every other measurement — the sim is the
        /// only process in this pipeline with a graphics device, so everything
        /// downstream of a throw here would be lost with it.
        public static int Render(string outDir)
        {
            GameObject root = null;
            RenderTexture rt = null;
            Texture2D tile = null, sheet = null;
            var prevActive = RenderTexture.active;
            var prevAmbient = RenderSettings.ambientLight;
            var prevAmbientMode = RenderSettings.ambientMode;
            try
            {
                var prefab = Resources.Load<GameObject>(Editorless.BodyLoadPath);
                var controller = Resources.Load<RuntimeAnimatorController>(
                    Editorless.SheetControllerPath);
                var manifest = Resources.Load<TextAsset>(Editorless.SlotsLoadPath);
                if (prefab == null || controller == null || manifest == null)
                {
                    Why = string.Format("missing asset (body={0} controller={1} slots={2})",
                                        prefab != null, controller != null, manifest != null);
                    Tiles = 0;
                    return 0;
                }

                var slots = manifest.text.Split('\n');
                var wanted = new System.Collections.Generic.List<string>();
                foreach (var s in slots)
                {
                    var t = s.Trim();
                    if (t.Length > 0) wanted.Add(t);
                }
                if (wanted.Count == 0)
                {
                    Why = "the slot manifest is empty";
                    Tiles = 0;
                    return 0;
                }

                // FAR BELOW THE CITY. The sheet runs after the world is built —
                // `SimDirector.Begin` is the only hook that has one — so the
                // body has to go somewhere the streets are not. The layer mask
                // below is what actually isolates it; this is so a stray
                // shadow-caster or a probe cannot reach into shot.
                var origin = new Vector3(0f, -5000f, 0f);
                root = new GameObject("ClipSheet");
                root.transform.position = origin;

                var body = Object.Instantiate(prefab, origin, Quaternion.identity, root.transform);
                SetLayer(body, SheetLayer);
                var animator = body.GetComponent<Animator>();
                if (animator == null)
                {
                    Why = "the body prefab carries no Animator";
                    Tiles = 0;
                    return 0;
                }
                animator.runtimeAnimatorController = controller;
                animator.applyRootMotion = false;
                // ALWAYS ANIMATE, for the reason the body prefab already
                // carries it: the sim never renders a live camera, so a
                // renderer nobody is continuously looking at is culled out of
                // retargeting and freezes in its bind pose. A sheet of
                // sixty-seven identical T-poses would read as sixty-seven
                // broken clips.
                animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;

                // EVERY COMPONENT STAYS ON, AND THE FIRST VERSION TURNED THEM
                // ALL OFF — which produced a sheet that libelled all 67 clips.
                //
                // The reasoning was "`CharacterRig` composes a lean, a limp and
                // an arm swing on top of whatever the Animator wrote, and this
                // picture has to be of the CLIP". It sounded right and the first
                // rendered sheet refuted it: every tile came back with one arm
                // clawed up beside the head and the shoes lying detached on the
                // ground, while the same build's street still shows a man in a
                // blue suit walking correctly, arms swinging, feet planted.
                //
                // The cause is that `CharacterRig.Awake` calls `Bind()` and runs
                // whether the component is enabled or not, so disabling it left
                // the pose it binds with and removed the LateUpdate that
                // finishes the job. Disabling half a system is not the same as
                // not having it.
                //
                // And the premise was wrong anyway. The question this sheet
                // exists to answer is Jafar's — *does it look real* — and what
                // a player sees IS the clip plus the procedural layer. A
                // picture of the clip alone would be a picture of something
                // nobody ever looks at.
                //
                // WHAT THIS STILL DOES NOT SHOW, said rather than discovered
                // later: the whole sheet is drawn inside ONE frame, so
                // `CharacterRig`'s LateUpdate runs once for all 201 tiles
                // rather than once per tile. The rig is intact and its bind is
                // correct — that is what fixes the broken pose — but the
                // per-frame lean, limp and arm swing are not sampled per tile.
                // Getting those needs a frame each, which is a coroutine and a
                // second round trip; it is worth doing only if a tile turns
                // out to disagree with the street still, and it is written down
                // here so nobody reads this sheet as more than it is.

                // GROUND UNDER THE FEET, because foot IK is part of what a
                // player sees and it reaches for a surface. Without one the
                // solver hunts for a floor five kilometres above and bends
                // every leg towards it — the sheet would report a rig fault
                // that only the sheet has. Unlit dark grey so it reads as a
                // shadow catcher rather than as scenery.
                var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
                floor.name = "ClipSheetFloor";
                floor.transform.SetParent(root.transform);
                floor.transform.position = origin;
                floor.transform.localScale = new Vector3(0.6f, 1f, 0.6f);
                SetLayer(floor, SheetLayer);
                // AND NO COLLIDER. `CreatePrimitive` adds one, and a body with
                // a controller standing exactly on it would be pushed out of
                // frame by the physics step — a fault that would look like a
                // clip putting somebody through the floor.
                var floorCollider = floor.GetComponent<Collider>();
                if (floorCollider != null) Object.Destroy(floorCollider);
                var floorMat = floor.GetComponent<Renderer>().material;
                if (floorMat != null) floorMat.color = new Color(0.30f, 0.31f, 0.34f, 1f);

                var lightGo = new GameObject("ClipSheetKey");
                lightGo.transform.SetParent(root.transform);
                lightGo.transform.position = origin + new Vector3(0f, 3f, -3f);
                lightGo.transform.rotation = Quaternion.Euler(35f, 20f, 0f);
                var key = lightGo.AddComponent<Light>();
                key.type = LightType.Directional;
                key.intensity = 1.15f;
                key.color = Color.white;
                key.shadows = LightShadows.None;
                key.cullingMask = 1 << SheetLayer;

                var camGo = new GameObject("ClipSheetCam");
                camGo.transform.SetParent(root.transform);
                var cam = camGo.AddComponent<Camera>();
                cam.enabled = false;               // rendered by hand, never per frame
                cam.clearFlags = CameraClearFlags.SolidColor;
                // Mid grey, chosen so a dark silhouette and a pale one both
                // read. A black background loses the noir wardrobe entirely,
                // which is most of this cast.
                cam.backgroundColor = new Color(0.42f, 0.44f, 0.47f, 1f);
                cam.cullingMask = 1 << SheetLayer;
                cam.orthographic = false;
                cam.fieldOfView = 32f;
                cam.nearClipPlane = 0.05f;
                cam.farClipPlane = 40f;
                // Slightly above the waist and back far enough for a 1.8m
                // figure to fit with headroom: 2 * 3.9 * tan(16 deg) = 2.24m.
                // Clips that put the body on the floor overflow sideways, and
                // that is information rather than a fault.
                cam.transform.position = origin + new Vector3(0f, 1.0f, 3.9f);
                cam.transform.rotation = Quaternion.Euler(0f, 180f, 0f);

                // A FIXED AMBIENT, RESTORED. The sim's own lighting moves with
                // the clock, so without this the sheet would look different
                // depending on which minute of the run it was taken in — and a
                // diagnostic whose appearance depends on when you ran it is one
                // nobody can compare across builds.
                RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
                RenderSettings.ambientLight = new Color(0.32f, 0.33f, 0.36f, 1f);

                int rows = (wanted.Count + ClipsPerRow - 1) / ClipsPerRow;
                int sheetW = ClipsPerRow * PhasesPerClip * TileWidth;
                int sheetH = rows * TileHeight;
                sheet = new Texture2D(sheetW, sheetH, TextureFormat.RGB24, false);
                rt = new RenderTexture(TileWidth, TileHeight, 24, RenderTextureFormat.ARGB32);
                tile = new Texture2D(TileWidth, TileHeight, TextureFormat.RGB24, false);
                cam.targetTexture = rt;

                var ledger = new System.Text.StringBuilder();
                ledger.Append("row\tcol\tslot\n");
                int drawn = 0;
                for (int i = 0; i < wanted.Count; i++)
                {
                    int hash = Animator.StringToHash(Editorless.StatePrefix + wanted[i]);
                    if (!animator.HasState(0, hash)) continue;
                    int row = i / ClipsPerRow, col = i % ClipsPerRow;
                    for (int p = 0; p < PhasesPerClip; p++)
                    {
                        animator.Play(hash, 0, Phases[p]);
                        // ZERO DELTA, TWICE. `Play` only queues the state; the
                        // first `Update` enters it and the second evaluates it
                        // at the normalised time asked for. One call leaves the
                        // previous clip's pose on the bones, which would shift
                        // every tile one clip to the left and look like a
                        // wholesale mislabelling.
                        animator.Update(0f);
                        animator.Update(0f);
                        RenderTexture.active = rt;
                        cam.Render();
                        tile.ReadPixels(new Rect(0, 0, TileWidth, TileHeight), 0, 0);
                        tile.Apply();
                        // Rows run DOWN the sheet and texture coordinates run
                        // up, so the row is flipped here rather than in the
                        // reader — a ledger whose row numbers disagree with the
                        // picture is worse than no ledger.
                        int x = (col * PhasesPerClip + p) * TileWidth;
                        int y = sheetH - (row + 1) * TileHeight;
                        sheet.SetPixels(x, y, TileWidth, TileHeight, tile.GetPixels());
                    }
                    ledger.Append(row).Append('\t').Append(col).Append('\t')
                          .Append(wanted[i]).Append('\n');
                    drawn++;
                }
                sheet.Apply();

                System.IO.Directory.CreateDirectory(outDir);
                System.IO.File.WriteAllBytes(System.IO.Path.Combine(outDir, "clips.jpg"),
                                             sheet.EncodeToJPG(70));
                System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "clips.tsv"),
                                            ledger.ToString());
                Tiles = drawn;
                Why = string.Format("{0} of {1} slot(s) drawn, {2}x{3}",
                                    drawn, wanted.Count, sheetW, sheetH);
                Debug.Log(string.Format("ClipSheet: {0}", Why));
                return drawn;
            }
            catch (System.Exception e)
            {
                Tiles = -1;
                Why = e.GetType().Name + ": " + e.Message;
                Debug.Log("ClipSheet: FAILED " + Why);
                return -1;
            }
            finally
            {
                RenderTexture.active = prevActive;
                RenderSettings.ambientLight = prevAmbient;
                RenderSettings.ambientMode = prevAmbientMode;
                if (tile != null) Object.Destroy(tile);
                if (sheet != null) Object.Destroy(sheet);
                if (rt != null) { rt.Release(); Object.Destroy(rt); }
                if (root != null) Object.Destroy(root);
            }
        }

        static void SetLayer(GameObject go, int layer)
        {
            go.layer = layer;
            foreach (Transform child in go.transform) SetLayer(child.gameObject, layer);
        }

        /// THE NAMES THE EDITOR SIDE WROTE, REPEATED ONCE AND ONLY ONCE.
        ///
        /// `Assets/Editor` does not ship in a player build, so the runtime
        /// cannot reference `ClipSheetAssets` and read its constants — the
        /// asmdef boundary is real and a build is how you find out. Two string
        /// literals in two assemblies that agree today is exactly the drift
        /// `CharacterPrefab.SpeedParam` exists to prevent, so the Editor side
        /// asserts against these rather than the other way round.
        public static class Editorless
        {
            public const string BodyLoadPath = "Characters/Body";
            public const string SheetControllerPath = "Characters/Body_sheet";
            public const string SlotsLoadPath = "Characters/clip_slots";
            public const string StatePrefix = "Sheet_";
        }
    }
}
