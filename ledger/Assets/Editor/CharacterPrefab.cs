using UnityEditor;
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

        /// The name the runtime asks `Resources.Load` for.
        public const string LoadPath = "Characters/Body";

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
                    // No controller: `CharacterRig` drives the bones itself and
                    // an empty state machine would only fight it. The Animator
                    // is here for its AVATAR — that is the whole contract.
                    animator.applyRootMotion = false;
                    animator.cullingMode = AnimatorCullingMode.CullUpdateTransforms;

                    PrefabUtility.SaveAsPrefabAsset(instance, BodyPrefab, out bool ok);
                    Debug.Log($"CharacterPrefab: wrote {BodyPrefab} ok={ok} "
                              + $"avatar={avatar.name} human={avatar.isHuman}");
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
