using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Ledger.EditorTools
{
    /// Headless build entry point for CI. Creates a boot scene on the fly if the
    /// project doesn't have one yet, so the pipeline is verifiable before the
    /// M0 scene lands.
    public static class CiBuild
    {
        const string ScenePath = "Assets/Scenes/Boot.unity";

        public static void BuildWindows()
        {
            if (!System.IO.File.Exists(ScenePath))
            {
                System.IO.Directory.CreateDirectory("Assets/Scenes");
                var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
                EditorSceneManager.SaveScene(scene, ScenePath);
                Debug.Log($"CiBuild: created placeholder scene at {ScenePath}");
            }

            KeepRuntimeShaderVariants();

            var options = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = "build/LEDGER/LEDGER.exe",
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None,
            };

            var report = BuildPipeline.BuildPlayer(options);
            Debug.Log($"CiBuild: {report.summary.result}, size {report.summary.totalSize} bytes, " +
                      $"{report.summary.totalErrors} errors, {report.summary.totalWarnings} warnings");

            if (report.summary.result != BuildResult.Succeeded)
                EditorApplication.Exit(1);
        }

        /// The world builds all its materials at runtime, so the shader-variant
        /// collector — which only scans assets that ship in the build — never sees
        /// them and strips keyword variants those runtime materials rely on (notably
        /// Standard's _EMISSION, which the night windows need to glow). Dropping a
        /// material that uses each needed variant into a Resources folder forces the
        /// variant into the build; everything under Resources ships with its variants.
        static void KeepRuntimeShaderVariants()
        {
            const string resDir = "Assets/Resources";
            const string matPath = resDir + "/KeepStandardEmission.mat";
            if (AssetDatabase.LoadAssetAtPath<Material>(matPath) != null) return;
            if (!System.IO.Directory.Exists(resDir)) System.IO.Directory.CreateDirectory(resDir);

            var mat = new Material(Shader.Find("Standard"));
            mat.EnableKeyword("_EMISSION");
            mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            mat.SetColor("_EmissionColor", new Color(1f, 0.8f, 0.4f));
            AssetDatabase.CreateAsset(mat, matPath);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("CiBuild: added Resources material to retain the Standard _EMISSION variant");
        }
    }
}
