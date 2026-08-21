using UnityEditor;
using UnityEngine;

namespace Ledger.EditorTools
{
    /// Make every fetched prop model REACHABLE AT RUNTIME — the same move,
    /// for the same reason, as CharacterPrefab: `Resources.Load` only
    /// reaches `Assets/Resources`, and the CC0 kit models live under
    /// `Assets/Props` (committed there by the props-fetch CI job). Moving
    /// them into Resources would ship every model whether used or not; a
    /// prefab per model in Resources ships exactly what is referenced.
    ///
    /// Built by script because nobody opens the Editor on this project.
    /// WRITTEN BEFORE THE MODELS ARRIVE, deliberately — the character
    /// pipeline's pattern: the fetch landing shows up in the NEXT build,
    /// not the one after, and this code is reviewed while it is cheap to
    /// be wrong about.
    ///
    /// NAMING: `Resources/Props/Prop_<kit>_<stem>.prefab`, stem lowercased
    /// with spaces and dashes collapsed to underscores. Callers ask
    /// `AssetLibrary.TryInstantiateProp("car-kit/sedan")` style keys — the
    /// resolver normalises the same way, one implementation of the rule.
    public static class PropPrefab
    {
        public const string SourceDir = "Assets/Props";
        public const string ResourceDir = "Assets/Resources/Props";

        /// Reported by the build log: how many models were found and how
        /// many prefabs were written. `-1` means the builder never ran —
        /// a different fact from "ran and found nothing", which is the
        /// expected state until the first props-fetch lands.
        public static int ModelsFound = -1;
        public static int PrefabsWritten = -1;

        public static string Key(string kit, string stem) =>
            (kit + "_" + stem).ToLowerInvariant()
                .Replace(" ", "_").Replace("-", "_");

        public static void Build()
        {
            ModelsFound = 0;
            PrefabsWritten = 0;
            if (!AssetDatabase.IsValidFolder(SourceDir))
            {
                Debug.Log("PropPrefab: no Assets/Props yet — nothing fetched, nothing to do");
                return;
            }
            if (!AssetDatabase.IsValidFolder("Assets/Resources"))
                AssetDatabase.CreateFolder("Assets", "Resources");
            if (!AssetDatabase.IsValidFolder(ResourceDir))
                AssetDatabase.CreateFolder("Assets/Resources", "Props");

            // BY EXTENSION, NOT BY `t:Model`. The type filter only matches
            // Unity's native ModelImporter output (.fbx and friends); glTFast
            // imports .glb through a ScriptedImporter whose main asset is a
            // plain GameObject, so the first build with 37 GLBs on disk found
            // ZERO of them (`furniture=0`, 98d8683) while every FBX kit
            // passed. Files on disk are the ground truth the fetch commits;
            // the importer's opinion of each is what `noAsset` then reports.
            int noAsset = 0;
            var exts = new[] { ".fbx", ".obj", ".glb", ".gltf" };
            foreach (var file in System.IO.Directory.GetFiles(
                         SourceDir, "*.*", System.IO.SearchOption.AllDirectories))
            {
                var ext = System.IO.Path.GetExtension(file).ToLowerInvariant();
                if (System.Array.IndexOf(exts, ext) < 0) continue;
                var path = file.Replace('\\', '/');
                ModelsFound++;
                try
                {
                    if (!BuildOne(path)) noAsset++;
                }
                catch (System.Exception e)
                {
                    // Diagnostic, never fatal — this runs inside the one
                    // entry point the whole build pipeline goes through.
                    Debug.Log($"PropPrefab: FAILED on {path}: {e.GetType().Name}: {e.Message}");
                }
            }
            AssetDatabase.SaveAssets();
            // `noAsset` is the denominator rule 3b demands: "the package did
            // not import the file" and "the file is not there" must not both
            // print as zero prefabs.
            Debug.Log($"PropPrefab: {PrefabsWritten} prefab(s) written from "
                      + $"{ModelsFound} model file(s) under {SourceDir}, "
                      + $"{noAsset} with no importable main asset");
        }

        /// False when the path yields no GameObject main asset — for a .glb
        /// that means glTFast is absent or failed to import it, and the
        /// caller counts those separately from files that are simply not
        /// there.
        static bool BuildOne(string modelPath)
        {
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
            if (model == null) return false;

            var rel = modelPath.Substring(SourceDir.Length + 1);
            var slash = rel.IndexOf('/');
            var kit = slash > 0 ? rel.Substring(0, slash) : "misc";
            var stem = System.IO.Path.GetFileNameWithoutExtension(modelPath);
            var key = Key(kit, stem);

            var instance = (GameObject)PrefabUtility.InstantiatePrefab(model);
            if (instance == null) return false;
            try
            {
                instance.name = "Prop_" + key;
                // THE BOUNDS, PRINTED, because the swap code scales meshes
                // to the primitive dimensions it replaces and a kit's unit
                // convention is a fact to read, not to assume. One line per
                // model, greppable from the build log.
                var r = instance.GetComponentInChildren<Renderer>();
                var b = r != null ? r.bounds.size : Vector3.zero;
                int mats = 0, notex = 0;
                foreach (var rend in instance.GetComponentsInChildren<Renderer>())
                    foreach (var m in rend.sharedMaterials)
                    {
                        mats++;
                        if (m != null && m.mainTexture == null) notex++;
                    }
                PrefabUtility.SaveAsPrefabAsset(
                    instance, $"{ResourceDir}/Prop_{key}.prefab", out bool ok);
                if (ok) PrefabsWritten++;
                Debug.Log($"PropPrefab: {key} ok={ok} "
                          + $"size=({b.x:0.00},{b.y:0.00},{b.z:0.00}) "
                          + $"mats={mats} notex={notex}");
            }
            finally
            {
                Object.DestroyImmediate(instance);
            }
            return true;
        }
    }
}
