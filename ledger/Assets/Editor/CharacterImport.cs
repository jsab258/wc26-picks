using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace Ledger.EditorTools
{
    /// M17.1. THE IMPORT SETTINGS, AS CODE, BECAUSE THERE ARE NO `.meta` FILES.
    ///
    /// Forty-four FBX sit in `Assets/Characters` — two bodies and forty-one
    /// Mixamo clips — and NOTHING in the game references them. The roadmap has
    /// called this "the one real unknown" in M17 for weeks, and the reason it
    /// stayed unknown is worth stating plainly:
    ///
    ///   `CharacterRig` needs a Humanoid Avatar. The Avatar is the contract,
    ///   deliberately, because Mixamo's bone names are stable right up until
    ///   somebody re-exports from Blender.
    ///
    ///   Unity does NOT default a model to Humanoid. It imports as Generic, so
    ///   no Avatar is produced and there is nothing to bind to.
    ///
    ///   Import settings live in `.meta` files, and this project tracks ZERO of
    ///   them — checked, not assumed: `find ledger/Assets -name "*.meta"`
    ///   returns nothing, and there is no ignore rule doing it. They simply do
    ///   not exist, so Unity regenerates defaults on every CI checkout.
    ///
    /// COMMITTING `.meta` FILES WOULD CHANGE A PROJECT CONVENTION and hand the
    /// settings to a file format nothing here reviews. An `AssetPostprocessor`
    /// does the same job as tracked, reviewable code that runs deterministically
    /// on every fresh import — which is exactly what CI does every run.
    ///
    /// WHY HUMANOID ON THE CLIPS TOO, not just the bodies. Retargeting is
    /// Humanoid-to-Humanoid: a clip imported Generic carries its own skeleton's
    /// curves and will not drive a different rig. Mixamo exports every clip with
    /// the full skeleton, so each one can produce its own avatar and retarget
    /// through the muscle space. That is the whole reason to pay the Humanoid
    /// tax at all.
    class CharacterImport : AssetPostprocessor
    {
        /// Everything under here is a character asset. Scoped to the folder so
        /// this cannot reach a model somebody adds elsewhere for another reason.
        public const string CharacterFolder = "Assets/Characters/";

        /// How many assets this postprocessor actually touched, and the last
        /// one it saw. Printed by `CharacterAudit`, because a build that
        /// silently never ran the importer looks exactly like a build where
        /// the importer had no effect.
        public static int Ran;
        public static string LastPath = "none";

        /// WHICH CLIPS LOOP, and it is a short list on purpose.
        ///
        /// Mixamo ships every clip non-looping, so a breathing idle plays once
        /// and the body freezes on its last frame — which looks exactly like
        /// the statue this whole change exists to fix, and would have been
        /// read as the controller not working.
        ///
        /// Only sustained states belong here. Looping a death, a flinch or a
        /// fall is worse than not looping it: a man who dies four times a
        /// second is a bug nobody would attribute to an import setting.
        static readonly HashSet<string> Sustained = new HashSet<string>
            { "idle", "walk", "run", "back_away", "guard", "block_hold",
              "sit", "smoke", "work_counter", "lie_still", "talk" };

        /// How many clips were set to loop. Zero when the character folder is
        /// present would mean the key convention has changed under this.
        public static int Looped;

        /// LOOPING IS SET IN THE ANIMATION PASS, not the model pass.
        /// `defaultClipAnimations` is only populated once the importer has
        /// read the take, so doing this in `OnPreprocessModel` would return an
        /// empty array and quietly set nothing at all — a silent no-op wearing
        /// the shape of a fix.
        void OnPreprocessAnimation()
        {
            var path = assetPath.Replace('\\', '/');
            if (!path.StartsWith(CharacterFolder)) return;
            var importer = assetImporter as ModelImporter;
            if (importer == null) return;

            var file = System.IO.Path.GetFileName(path);
            int split = file.IndexOf("__", System.StringComparison.Ordinal);
            if (split < 0 || !Sustained.Contains(file.Substring(0, split))) return;

            var clips = importer.defaultClipAnimations;
            if (clips == null || clips.Length == 0) return;
            for (int i = 0; i < clips.Length; i++)
            {
                clips[i].loopTime = true;
                // `loopPose` matches the first and last frame so a cycle does
                // not jolt at the seam. Right for a walk and for breathing;
                // it is why the list above is short.
                clips[i].loopPose = true;
            }
            importer.clipAnimations = clips;
            Looped++;
        }

        void OnPreprocessModel()
        {
            var path = assetPath.Replace('\\', '/');
            if (!path.StartsWith(CharacterFolder)) return;

            var importer = assetImporter as ModelImporter;
            if (importer == null) return;

            importer.animationType = ModelImporterAnimationType.Human;
            importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            importer.importAnimation = true;

            // MIXAMO SHIPS ITS CLIPS IN CENTIMETRES and its bodies at a scale
            // that puts a "1.8 metre" man at 180 units. `useFileScale` takes the
            // FBX's own unit declaration rather than assuming, which is the
            // difference between a person and a tower block. `Mannequin` builds
            // its bodies at 1.58-1.90m and the sim gates on that range, so a
            // hundredfold error would be caught — but only after a build.
            importer.useFileScale = true;

            // READABLE MESHES, BODIES ONLY.
            //
            // `RealBody` measures how much of the figure the coat covers, by
            // triangle area — the number that tells a dressed body from a bare
            // one, which no renderer COUNT can. Unity imports meshes
            // non-readable by default, and `mesh.vertices` on a non-readable
            // mesh returns an EMPTY ARRAY at runtime rather than throwing. So
            // the first run of that measurement reported `bodyCoatArea=0.000`,
            // which is indistinguishable from the fault it was written to
            // find: a coat covering none of the body. A false positive that
            // looks exactly like the finding — the `Anachronism` lesson, in a
            // different system, three days later.
            //
            // BODIES ONLY, and the test is the folder. Clips live in A/B/C and
            // carry a skeleton nobody reads vertices from; bodies sit directly
            // in `Assets/Characters`. Making all forty-four readable would keep
            // a second CPU copy of every mesh in memory for nothing.
            string rel = path.Substring(CharacterFolder.Length);
            if (!rel.Contains("/")) importer.isReadable = true;

            // AND THE AXIS, which is why the first body to reach the street was
            // lying on its back in the road.
            //
            // Jafar spotted it in `review_day1_noon.jpg`. Every gate said the
            // body was fine — `realBody=1`, `bodiesOk=True`, height in range,
            // `playerPrimitive=False` — because not one of them asks WHICH WAY
            // UP it is. Two noon frames from different days show it in the same
            // attitude, which is what rules out `CharacterRig`'s compounding
            // capsule lean: a drift would tumble differently each time, a fixed
            // rotation looks identical.
            //
            // Mixamo exports Z-up. Without this Unity leaves the conversion as a
            // -90° rotation on a node INSIDE the hierarchy, so
            // `RealBody.TryAttach` setting the instantiated root's
            // `localRotation` to identity — which it does — corrects nothing:
            // the rotation is a level below the transform being straightened.
            // Baking it puts the conversion into the mesh and the rig, and
            // leaves every transform the runtime touches at identity.
            // BODIES ONLY, AND THE BISECT IS WHY. Baking it on the CLIPS is
            // what has had the player upside down all along.
            //
            // The evidence, from one run that sampled the posture three times:
            // the BIND pose measures +0.56 head-above-hips and +0.96
            // hips-above-feet — anatomically right, so the body's own
            // conversion worked. The moment the Animator evaluates a clip it
            // reads -0.11 and -0.78, and `CharacterRig`'s solve then barely
            // moves it (-0.11 to -0.11). Correct T-pose, inverted animation:
            // the inversion enters with the retarget, not with the model and
            // not with our rig.
            //
            // The reason is that Humanoid retargeting goes through MUSCLE
            // SPACE, which is already axis-independent — the avatar defines
            // which way is up. Baking a conversion into a clip's skeleton on
            // top of that applies the rotation twice: once in the baked curves
            // and once in the avatar that reads them. A body needs the bake
            // because its mesh and bind pose are real geometry; a clip does
            // not, because its curves are interpreted rather than placed.
            //
            // Bodies sit at the root of `Assets/Characters/`; clips live in the
            // per-character subfolders. That is the discriminator, and it is a
            // property of the layout rather than a guess about a filename.
            // EXPERIMENT, NOT A FIX, and it is labelled that way on purpose.
            //
            // The four-stage bracket has now located the fault exactly. Bind
            // pose +0.56/+0.96 upright; after scaling +0.53/+0.91, still
            // upright and scaling cleanly by 0.949; after the Animator
            // evaluates, -0.13/-0.78. The import is innocent, the scale is
            // innocent, our rig is innocent. THE AVATAR'S OWN RETARGET INVERTS
            // THE BODY.
            //
            // That points at a disagreement between the mesh and the avatar
            // about which way is up. `bakeAxisConversion` rotates the mesh and
            // the skeleton into Y-up — which is why the ROOT reads upright and
            // why the first body stopped lying on its back — but if the human
            // description is built against the pre-bake orientation, muscle
            // space maps "up" to the old axis and every evaluated pose comes
            // out inverted.
            //
            // I have proposed two fixes on this fault already and both were
            // wrong, so this is not a third. It is the experiment that
            // distinguishes the remaining possibilities: turn the bake OFF
            // entirely and read the same four stages. If bind and scaled go
            // INVERTED while the animated pose comes out UPRIGHT, the mesh and
            // the avatar are provably using opposite conventions and the fix
            // is to make them agree rather than to keep flipping one of them.
            // If everything stays inverted, the bake was never the variable at
            // all and the avatar is simply built wrong.
            //
            // THE EXPERIMENT CAME BACK IDENTICAL, AND THAT IS THE FINDING.
            // With the bake OFF, the four stages read +0.557/+0.955,
            // +0.528/+0.907, -0.142/-0.778, -0.148/-0.777 — the same to three
            // decimals as with it ON. A setting that changes the import cannot
            // leave every measurement bit-identical, so either this
            // postprocessor is not running on the model at all, or the bake is
            // irrelevant to the bone positions we read.
            //
            // Restored to the documented setting, because it has a real
            // incident behind it (the first body reached the street on its
            // back) and turning it off on a null result would be trading a
            // reasoned setting for an unreasoned one. `CharacterAudit` now
            // reports whether this code ran, so the next build says which of
            // the two explanations is true instead of me picking one.
            bool isClipOnly = path.Substring(CharacterFolder.Length).Contains("/");
            importer.bakeAxisConversion = !isClipOnly;

            // The bodies have skin; the clips do not need it imported twice.
            // AND SAY THAT THIS RAN. The bake experiment returned identical
            // numbers with the setting on and off, which is only possible if
            // the setting is irrelevant or this method never executed. Those
            // have opposite fixes and no evidence separated them, so the
            // importer now records its own footprint for the audit to print.
            Ran++;
            LastPath = path;

            // AND THE MATERIALS, WHICH IS WHY EVERY BODY IS ONE FLAT COLOUR.
            //
            // The noon still shows real human meshes — proper anatomy, not
            // boxes — painted a single pale blue and a single flat green.
            // `bodyKeptMats=0` says exactly that in a number: `RealBody` keeps a
            // renderer's own material only when it carries a texture, so zero
            // kept means not one material on any body has one, and the wardrobe
            // repainted all seven parts of Michelle over the top.
            //
            // THE TEXTURES ARE IN THE FILES. Counted, not assumed — the PNG
            // signature `\x89PNG\r\n\x1a\n` appears 4 times in Michelle.fbx, 22
            // in Remy, 6 in Sophie, 6 in Joe, 6 in Martha, 3 in The Boss and
            // once each in Big Vegas and Sporty Granny. Only X Bot and Y Bot
            // have none, which is right: they are the grey stand-ins.
            //
            // Nothing in this method has ever mentioned materials, so every
            // body has been importing on whatever the default happens to be in
            // this Unity version — and a default nobody chose is a setting
            // nobody can reason about. `ImportViaMaterialDescription` reads the
            // FBX's own material description, which is where the embedded
            // texture references live; `InPrefab` keeps the result inside the
            // model asset, which matches this project tracking zero `.meta`
            // files and wanting no generated assets to review.
            //
            // I HAVE NOT WATCHED THIS WORK, and it is a Game-layer setting so
            // the first thing that can is CI. `CharacterAudit` now prints the
            // materials and their textures per body, so the next build says
            // whether this was the fault or only a setting I tidied — and if it
            // is still zero, the report names which of the two halves failed
            // rather than sending me back for another round trip.
            importer.materialImportMode =
                ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            importer.materialLocation = ModelImporterMaterialLocation.InPrefab;

            importer.importBlendShapes = false;
            importer.importCameras = false;
            importer.importLights = false;
        }
    }

    /// WHAT UNITY ACTUALLY PRODUCED, printed. The only way to find out.
    ///
    /// This cannot be checked locally at any level — the Game layer does not
    /// compile here and Unity is the thing that decides whether an FBX yields a
    /// valid human Avatar. So the build says so out loud, the line is captured
    /// into `game-design/sim-shots/verdict.txt`, and M17.1 stops being a
    /// question nobody can answer without opening the Editor.
    public static class CharacterAudit
    {
        public static void Report()
        {
            try
            {
                var guids = AssetDatabase.FindAssets(
                    "t:Model", new[] { "Assets/Characters" });
                int models = 0, humanoid = 0, validHuman = 0, clips = 0;
                var noAvatar = new List<string>();

                foreach (var guid in guids)
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    if (string.IsNullOrEmpty(path)) continue;
                    models++;

                    var importer = AssetImporter.GetAtPath(path) as ModelImporter;
                    if (importer != null
                        && importer.animationType == ModelImporterAnimationType.Human)
                        humanoid++;

                    bool found = false;
                    foreach (var obj in AssetDatabase.LoadAllAssetsAtPath(path))
                    {
                        var avatar = obj as Avatar;
                        if (avatar != null && avatar.isValid && avatar.isHuman)
                        {
                            validHuman++;
                            found = true;
                        }
                        // Unity generates `__preview__` clips for the inspector;
                        // counting those would report animation that does not
                        // ship.
                        var clip = obj as AnimationClip;
                        if (clip != null && !clip.name.StartsWith("__preview"))
                            clips++;
                    }
                    if (!found && noAvatar.Count < 4)
                        noAvatar.Add(System.IO.Path.GetFileName(path));
                }

                Debug.Log($"CharacterAudit: importerRan={CharacterImport.Ran} looped={CharacterImport.Looped} lastImported={CharacterImport.LastPath} "
                          + $"models={models} humanoid={humanoid} "
                          + $"validHumanAvatar={validHuman} clips={clips}"
                          + (noAvatar.Count > 0
                                 ? " noAvatar=[" + string.Join(", ", noAvatar) + "]"
                                 : ""));
                Materials();
            }
            catch (System.Exception e)
            {
                // A REPORT THAT KILLS THE BUILD IS WORSE THAN NO REPORT. This
                // runs inside the one entry point the whole Windows pipeline
                // goes through, and it is a diagnostic, not a gate.
                Debug.Log($"CharacterAudit: FAILED {e.GetType().Name}: {e.Message}");
            }
        }

        /// WHAT UNITY MADE OF THE EMBEDDED TEXTURES, per body.
        ///
        /// `bodyKeptMats=0` is a zero with no denominator, and rule 3b is about
        /// exactly this: it reads as "the wardrobe dressed everybody" and is
        /// equally consistent with "no material reached the mesh at all". Those
        /// have completely different fixes and the number cannot tell them
        /// apart, so this prints the count of what was examined beside it.
        ///
        /// BODIES ONLY. The forty-two clips in A/B/C carry a skeleton and no
        /// mesh worth painting, and forty-seven lines would push the bodies off
        /// the part of the verdict anybody reads.
        static void Materials()
        {
            const string Folder = CharacterImport.CharacterFolder;
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { "Assets/Characters" }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (string.IsNullOrEmpty(path)) continue;
                if (path.Substring(Folder.Length).Contains("/")) continue;

                int mats = 0, textured = 0;
                var detail = new List<string>();
                foreach (var obj in AssetDatabase.LoadAllAssetsAtPath(path))
                {
                    var m = obj as Material;
                    if (m == null) continue;
                    mats++;
                    var tex = m.mainTexture;
                    if (tex != null) textured++;
                    // THE SHADER TOO, because a material with a texture on a
                    // shader that ignores it looks identical to one with no
                    // texture, and this project has no `.meta` files to read
                    // the answer out of.
                    if (detail.Count < 8)
                        detail.Add($"{m.name}:{(m.shader != null ? m.shader.name : "noshader")}"
                                   + $":{(tex != null ? tex.name : "notex")}");
                }
                Debug.Log($"CharacterMaterials: {System.IO.Path.GetFileName(path)} "
                          + $"mats={mats} textured={textured} "
                          + $"[{(detail.Count == 0 ? "no materials on this model" : string.Join(" ", detail))}]");
            }
        }
    }
}
