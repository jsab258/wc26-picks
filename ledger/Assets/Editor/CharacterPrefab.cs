using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Ledger.EditorTools
{
    /// M17.1, step two: make the body REACHABLE AT RUNTIME.
    ///
    /// The audit answered step one — `models=44 humanoid=44 validHumanAvatar=44
    /// clips=44`, so Unity does produce valid human Avatars from these FBX once
    /// `CharacterImport` forces Humanoid. `CharacterRig.Bind` has had a tier one
    /// waiting for that since it was written: an `Animator` in the children with
    /// `avatar.isHuman`, and everything below it unchanged.
    ///
    /// WHAT WAS STILL MISSING is that nothing can LOAD the FBX. `Resources.Load`
    /// only reaches `Assets/Resources`, and the bodies live in
    /// `Assets/Characters`.
    ///
    /// MOVING THEM WOULD BE THE WRONG FIX: everything under `Resources` ships in
    /// the player whether or not it is used, so moving forty-four FBX there
    /// would put forty-one animation clips and two bodies in the build to reach
    /// one. Instead a PREFAB goes in `Resources` and REFERENCES the model — and
    /// Unity pulls a referenced asset into the build as a dependency, so exactly
    /// what is used ships and nothing else.
    ///
    /// Built by script rather than by hand because nobody opens the Editor on
    /// this project: CI is the only Unity that runs, so a prefab somebody made
    /// once and committed would be a binary nobody could review or regenerate.
    public static class CharacterPrefab
    {
        public const string BodyModel = "Assets/Characters/X Bot.fbx";
        public const string ResourceDir = "Assets/Resources/Characters";
        public const string BodyPrefab = ResourceDir + "/Body.prefab";
        public const string ControllerPath = ResourceDir + "/Body.controller";

        /// The name the runtime asks `Resources.Load` for.
        public const string LoadPath = "Characters/Body";

        /// The float `CharacterRig` writes each frame. Named once here so the
        /// controller that reads it and the code that writes it cannot drift.
        public const string SpeedParam = "Speed";

        /// Reported on the done line so a run says whether the body has
        /// anything to play, rather than leaving it to be inferred from a
        /// screenshot. `-1` is "the builder did not run at all", which is a
        /// different fault from "it ran and found no clips".
        public static int ClipsBound = -1;
        public static string ControllerWhy = "not tried";

        public static void Build()
        {
            try
            {
                var model = AssetDatabase.LoadAssetAtPath<GameObject>(BodyModel);
                if (model == null)
                {
                    Debug.Log($"CharacterPrefab: no model at {BodyModel} — skipping");
                    return;
                }

                var avatar = AvatarOf(BodyModel);
                if (avatar == null || !avatar.isHuman)
                {
                    // NOT AN ERROR, A FINDING. If the importer stopped producing
                    // a human avatar this says so instead of writing a prefab
                    // that binds to nothing and looks like it worked.
                    Debug.Log("CharacterPrefab: model has no valid human avatar — "
                              + "not writing a prefab that cannot bind");
                    return;
                }

                if (!AssetDatabase.IsValidFolder("Assets/Resources"))
                    AssetDatabase.CreateFolder("Assets", "Resources");
                if (!AssetDatabase.IsValidFolder(ResourceDir))
                    AssetDatabase.CreateFolder("Assets/Resources", "Characters");

                var instance = (GameObject)PrefabUtility.InstantiatePrefab(model);
                if (instance == null)
                {
                    Debug.Log("CharacterPrefab: could not instantiate the model");
                    return;
                }

                try
                {
                    instance.name = "Body";
                    var animator = instance.GetComponent<Animator>()
                                   ?? instance.AddComponent<Animator>();
                    animator.avatar = avatar;
                    // AND NOW A CONTROLLER, WHICH IS THE WHOLE VISIBLE FIX.
                    //
                    // The paragraph below is kept because its lesson is real,
                    // but its DECISION was wrong and the still is what says so:
                    // the player stands in the FBX's bind pose with both arms
                    // out at 119 degrees, because nothing has ever animated
                    // this body. The bracket proves our code is not doing it —
                    // `preArmDrop=118.6` sampled before a single line of
                    // `CharacterRig` runs, `liveArmDrop=118.6` after, the same
                    // number to a tenth of a degree.
                    //
                    // "An empty state machine would only fight it" was true of
                    // an EMPTY one. Forty-one clips were imported and audited
                    // every build and not one was ever played — `clips=44`
                    // reported as a success four days running. A breathing idle
                    // and a walk cycle are the difference between a person and
                    // a mannequin sliding along a pavement, and no amount of
                    // procedural lean substitutes for either.
                    //
                    // `CharacterRig.PoseIsDriven` was written for exactly this
                    // and has been false since the day it was added: with a
                    // controller present it now takes the composing branch it
                    // was designed for, and the rest-restore stands down
                    // because something else genuinely is driving the pose.
                    animator.runtimeAnimatorController = BuildLocomotion();
                    //
                    // AND THAT CONTRACT HAD A SHARP EDGE NOBODY HAD WRITTEN
                    // DOWN. An Animator with no controller drives nothing, so
                    // `CharacterRig` is the only thing writing these bones —
                    // which is intended — but `CharacterRig` decided whether to
                    // restore its rest pose by asking whether an Animator
                    // EXISTED. One does. It therefore took neither branch,
                    // never reset, and composed every frame onto its own
                    // previous output until the player was upside down in
                    // mid-air. Eight builds.
                    //
                    // The arrangement is still right. What was missing is that
                    // "there is an Animator" and "something is driving the
                    // pose" are different questions, and this is the line that
                    // makes them different.
                    animator.applyRootMotion = false;
                    animator.cullingMode = AnimatorCullingMode.CullUpdateTransforms;

                    PrefabUtility.SaveAsPrefabAsset(instance, BodyPrefab, out bool ok);
                    Debug.Log($"CharacterPrefab: wrote {BodyPrefab} ok={ok} "
                              + $"avatar={avatar.name} human={avatar.isHuman} "
                              + $"clipsBound={ClipsBound} controller={ControllerWhy}");
                }
                finally
                {
                    Object.DestroyImmediate(instance);
                }

                AssetDatabase.SaveAssets();
            }
            catch (System.Exception e)
            {
                // Diagnostic, never fatal — it runs inside the one entry point
                // the whole Windows pipeline goes through.
                Debug.Log($"CharacterPrefab: FAILED {e.GetType().Name}: {e.Message}");
            }
        }

        /// ONE BLEND TREE ON SPEED: standing, walking, running.
        ///
        /// Deliberately the smallest thing that stops the body being a statue,
        /// and deliberately keyed on a quantity `CharacterRig` already has.
        /// Everything else the forty-one clips could do — the greeting, the
        /// flinch, the smoke, sitting at a counter — is a later layer, and
        /// building all of it before seeing one frame of a walk cycle would be
        /// the same mistake as the systems this project keeps finding unrun.
        ///
        /// THRESHOLDS FROM THE GAME, NOT INVENTED. `Rig`'s own gait model and
        /// the walker's `MoveSpeed` put an ordinary walk at about 1.4 m/s,
        /// which is also the figure `Witnesses` passes to `Perception.InSight`
        /// as `subjectSpeed` for a person walking. The run threshold is the
        /// sprint speed the player controller already uses. If either moves,
        /// these are wrong and the frame will show it.
        ///
        /// WRAPPED, AND FAILING SOFT ON PURPOSE. This is Editor-only API that
        /// cannot be compiled outside CI, so a mistake here would otherwise
        /// take down the one entry point the whole Windows pipeline goes
        /// through — twenty-eight minutes to learn a method name. A null
        /// return leaves the body exactly as it was before this change and
        /// says why on the done line, which is a bad frame instead of no
        /// frames at all.
        static RuntimeAnimatorController BuildLocomotion()
        {
            ClipsBound = 0;
            try
            {
                var idle = ClipFor("idle");
                var walk = ClipFor("walk");
                var run = ClipFor("run");
                if (idle == null)
                {
                    // WITHOUT AN IDLE THERE IS NO CONTROLLER WORTH HAVING. A
                    // tree whose zero-speed pose is a walk cycle looks worse
                    // than the statue, so this refuses rather than half-doing
                    // it — and says which clip was missing.
                    ControllerWhy = "no idle clip under Assets/Characters";
                    return null;
                }

                var controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
                if (controller == null) { ControllerWhy = "could not create controller asset"; return null; }
                controller.AddParameter(SpeedParam, AnimatorControllerParameterType.Float);

                var state = controller.CreateBlendTreeInController("Locomotion", out BlendTree tree, 0);
                tree.blendType = BlendTreeType.Simple1D;
                tree.blendParameter = SpeedParam;
                // Explicit, because automatic thresholds spread the children
                // evenly over 0..1 and would put a full run at one metre per
                // second — the clips would play, at the wrong speeds, which is
                // the kind of wrong that looks like a physics bug.
                tree.useAutomaticThresholds = false;

                tree.AddChild(idle, 0f);   ClipsBound++;
                if (walk != null) { tree.AddChild(walk, 1.4f); ClipsBound++; }
                if (run != null) { tree.AddChild(run, 4.0f); ClipsBound++; }

                controller.layers[0].stateMachine.defaultState = state;
                AssetDatabase.SaveAssets();
                ControllerWhy = $"ok (idle{(walk != null ? "+walk" : "")}{(run != null ? "+run" : "")})";
                return controller;
            }
            catch (System.Exception e)
            {
                ControllerWhy = $"{e.GetType().Name}: {e.Message}";
                ClipsBound = 0;
                return null;
            }
        }

        /// The clip whose file carries this key, e.g. `idle` from
        /// `idle__Breathing Idle_<guid>.fbx`.
        ///
        /// Off the KEY rather than the Mixamo title, because the key is the
        /// name this project chose and `_picks.json` records, while the title
        /// is whatever Adobe called it that year. `__preview__` clips are
        /// Unity's own scratch objects and are not animations anybody asked
        /// for — including one would bind a body to an editor artefact.
        static AnimationClip ClipFor(string key)
        {
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { "Assets/Characters" }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var file = System.IO.Path.GetFileName(path);
                int split = file.IndexOf("__", System.StringComparison.Ordinal);
                if (split < 0 || file.Substring(0, split) != key) continue;
                foreach (var obj in AssetDatabase.LoadAllAssetsAtPath(path))
                {
                    var clip = obj as AnimationClip;
                    if (clip != null && !clip.name.StartsWith("__preview__")) return clip;
                }
            }
            return null;
        }

        static Avatar AvatarOf(string path)
        {
            foreach (var obj in AssetDatabase.LoadAllAssetsAtPath(path))
            {
                var avatar = obj as Avatar;
                if (avatar != null && avatar.isValid && avatar.isHuman) return avatar;
            }
            return null;
        }
    }
}
