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
    }
}
