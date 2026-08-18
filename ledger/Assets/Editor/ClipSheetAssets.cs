using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Ledger.EditorTools
{
    /// EVERY CLIP ON ONE CONTROLLER, so the game can play any of them by name.
    ///
    /// WHY THIS EXISTS. Jafar asked whether the people in the stills are moving
    /// right or whether we are playing the wrong animations. Nothing this
    /// project produces could answer it: every committed screenshot is a street
    /// at 1280x720 where a person is about forty pixels tall, and a walk cycle
    /// and a death throe are the same smudge at that size.
    ///
    /// `tools/clip-motion.py` answers the half a FILE can prove — two slots
    /// holding the same bytes, and a clip whose root never moves. It found
    /// both. What it cannot do is say which animation a clip actually IS: every
    /// Mixamo FBX names its take "mixamo.com", so there is no internal label to
    /// compare a filename against, and the one time this project tried to infer
    /// content from curves it produced two findings that both died — hip height
    /// is not comparable between clips, and Euler ranges inflate on wrap.
    ///
    /// So the answer has to be a picture, and the picture has to be rendered by
    /// something holding the retargeted humanoid rig — which is Unity, not a
    /// file reader. `game-design/sim-shots/clips.jpg` is that picture.
    ///
    /// THE SPLIT, AND WHY IT IS NOT ALL IN ONE PLACE. Building a controller
    /// needs `UnityEditor.Animations`, which exists only in the Editor. Taking
    /// a picture needs a graphics device, and the Editor build step runs
    /// `-batchmode -nographics`, which has none — `Camera.Render` there draws
    /// nothing at all and would write a sheet of black tiles that looks exactly
    /// like a broken import. The sim is the only process in this pipeline with
    /// a real device, so the Editor builds the asset and `Game/ClipSheet` takes
    /// the picture.
    public static class ClipSheetAssets
    {
        public const string ControllerPath =
            CharacterPrefab.ResourceDir + "/Body_sheet.controller";

        /// The slot list, as a TextAsset beside the controller. A runtime has
        /// no way to enumerate an AnimatorController's STATES — `animationClips`
        /// hands back clips with no state names — so without this the sim could
        /// play every clip and be unable to say which tile is which. One line
        /// per state, in the order the sheet lays them out.
        public const string SlotsPath = CharacterPrefab.ResourceDir + "/clip_slots.txt";

        /// The prefix a state name carries, TAKEN FROM THE RUNTIME rather than
        /// declared again here. `Assets/Editor` does not ship in a player, so
        /// the dependency can only run this way round — and one constant with
        /// one definition is the whole point: a state written `Sheet_` and
        /// looked up as `sheet_` would produce a blank sheet with nothing in
        /// the log to say why.
        public const string StatePrefix = Ledger.Game.ClipSheet.Editorless.StatePrefix;

        public static int States = -1;

        /// One state per clip file under `Assets/Characters`, named for the
        /// SLOT rather than the Mixamo title — the slot is the name this
        /// project chose and `_picks.json` records, and it is what a finding
        /// has to be reported against.
        /// `Assets/Resources/Characters/Body_sheet.controller` ->
        /// `Characters/Body_sheet`, which is what `Resources.Load` wants. Done
        /// by transformation rather than by writing the second string out,
        /// because the two are one fact and a rename that updates only one of
        /// them produces an empty sheet with nothing in the log to say why.
        static string LoadPathOf(string assetPath)
        {
            const string prefix = "Assets/Resources/";
            var p = assetPath.StartsWith(prefix) ? assetPath.Substring(prefix.Length) : assetPath;
            int dot = p.LastIndexOf('.');
            return dot > 0 ? p.Substring(0, dot) : p;
        }

        public static void Build()
        {
            try
            {
                // THE TWO SIDES AGREE, CHECKED RATHER THAN ASSUMED. The Editor
                // writes an asset path and the player asks `Resources.Load` for
                // a load path; they are the same fact in two spellings, in two
                // assemblies, and nothing but this line makes a disagreement
                // visible before the sheet comes back blank.
                if (LoadPathOf(ControllerPath) != Ledger.Game.ClipSheet.Editorless.SheetControllerPath
                    || LoadPathOf(SlotsPath) != Ledger.Game.ClipSheet.Editorless.SlotsLoadPath)
                {
                    States = -1;
                    Debug.Log("ClipSheetAssets: asset paths and the runtime's load "
                              + $"paths disagree ({LoadPathOf(ControllerPath)} vs "
                              + $"{Ledger.Game.ClipSheet.Editorless.SheetControllerPath}) "
                              + "— not writing a sheet the player cannot find");
                    return;
                }
                var slots = new System.Collections.Generic.SortedDictionary<
                    string, AnimationClip>(System.StringComparer.Ordinal);
                foreach (var guid in AssetDatabase.FindAssets(
                             "t:Model", new[] { "Assets/Characters" }))
                {
                    var path = AssetDatabase.GUIDToAssetPath(guid);
                    var file = System.IO.Path.GetFileName(path);
                    int split = file.IndexOf("__", System.StringComparison.Ordinal);
                    // A BODY IS NOT A CLIP. Bodies sit directly in the folder
                    // and carry no `__`; clips live in the tier subfolders and
                    // are named `slot__Title_<guid>.fbx`. Same discriminator
                    // `CharacterImport` uses, not a second one.
                    if (split < 0) continue;
                    var slot = file.Substring(0, split);
                    if (slots.ContainsKey(slot)) continue;
                    foreach (var obj in AssetDatabase.LoadAllAssetsAtPath(path))
                    {
                        var clip = obj as AnimationClip;
                        if (clip == null || clip.name.StartsWith("__preview__")) continue;
                        slots[slot] = clip;
                        break;
                    }
                }

                if (slots.Count == 0)
                {
                    States = 0;
                    Debug.Log("ClipSheetAssets: no clips under Assets/Characters — "
                              + "no sheet controller written");
                    return;
                }

                var controller = AnimatorController.CreateAnimatorControllerAtPath(
                    ControllerPath);
                if (controller == null)
                {
                    States = 0;
                    Debug.Log("ClipSheetAssets: could not create the sheet controller");
                    return;
                }

                var machine = controller.layers[0].stateMachine;
                AnimatorState first = null;
                var names = new System.Text.StringBuilder();
                foreach (var pair in slots)
                {
                    var state = machine.AddState(StatePrefix + pair.Key);
                    state.motion = pair.Value;
                    // NO EXIT AND NO TRANSITIONS, deliberately. The sheet drives
                    // each state by hash with an explicit normalised time and
                    // never lets the graph advance on its own; a transition
                    // would mean a tile showing a blend between two clips and
                    // nothing in the picture would say so.
                    state.speed = 0f;
                    if (first == null) first = state;
                    names.Append(pair.Key).Append('\n');
                }
                machine.defaultState = first;

                // The IK pass OFF here, and that is not an oversight. Foot IK
                // pulls the feet onto ground that does not exist where the sheet
                // is rendered, so leaving it on would bend every leg towards a
                // floor a thousand metres away and the sheet would libel every
                // clip in the set.
                var layers = controller.layers;
                layers[0].iKPass = false;
                controller.layers = layers;

                System.IO.File.WriteAllText(SlotsPath, names.ToString());
                AssetDatabase.ImportAsset(SlotsPath);
                AssetDatabase.SaveAssets();

                States = slots.Count;
                Debug.Log($"ClipSheetAssets: sheet controller with {States} state(s) "
                          + $"at {ControllerPath}");
            }
            catch (System.Exception e)
            {
                // Diagnostic, never fatal — it runs inside the one entry point
                // the whole Windows pipeline goes through, and a picture nobody
                // asked for must not be able to stop a build.
                States = -1;
                Debug.Log($"ClipSheetAssets: FAILED {e.GetType().Name}: {e.Message}");
            }
        }
    }
}
