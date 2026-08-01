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

        public static void BuildWindows() => Build(BuildTarget.StandaloneWindows64,
                                                   "build/LEDGER/LEDGER.exe");

        /// MACOS, WHICH HAS NEVER BEEN COMPILED.
        ///
        /// Nothing in `Assets/Scripts` is Windows-specific — no platform
        /// `#if`, no `.exe` assumption, no Win32 API — so a mac build ought
        /// to work. "Ought to" is precisely the class of claim this project
        /// keeps catching itself making, and the only way to turn it into a
        /// fact is to run the compiler. That is all this is: a proof, not a
        /// shipping pipeline. Signing and notarisation need an Apple
        /// Developer ID, which is a purchase and therefore Jafar's.
        public static void BuildMac() => Build(BuildTarget.StandaloneOSX, "build/LEDGER-mac/LEDGER.app");

        static void Build(BuildTarget target, string outputPath)
        {
            // M17.1, ANSWERED BY THE ONLY THING THAT CAN ANSWER IT. Whether the
            // Mixamo FBX yield valid human Avatars is a question about Unity's
            // importer, and the Game layer does not compile locally — so the
            // build reports it and the line is captured into the verdict file.
            // Diagnostic only: it cannot fail the build.
            CharacterAudit.Report();

            // And the prefab that makes the body reachable from `Resources`,
            // rebuilt every run so it cannot drift from the model it came from.
            CharacterPrefab.Build();

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
                locationPathName = outputPath,
                target = target,
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
