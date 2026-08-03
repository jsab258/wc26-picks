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
            // Either answer is worth a build. Neither is worth a guess.
            importer.bakeAxisConversion = false;

            // The bodies have skin; the clips do not need it imported twice.
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

                Debug.Log($"CharacterAudit: models={models} humanoid={humanoid} "
                          + $"validHumanAvatar={validHuman} clips={clips}"
                          + (noAvatar.Count > 0
                                 ? " noAvatar=[" + string.Join(", ", noAvatar) + "]"
                                 : ""));
            }
            catch (System.Exception e)
            {
                // A REPORT THAT KILLS THE BUILD IS WORSE THAN NO REPORT. This
                // runs inside the one entry point the whole Windows pipeline
                // goes through, and it is a diagnostic, not a gate.
                Debug.Log($"CharacterAudit: FAILED {e.GetType().Name}: {e.Message}");
            }
        }
    }
}
