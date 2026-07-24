using UnityEngine;

namespace Ledger.Game
{
    /// Everything in M0 is constructed from code at runtime — no authored scenes,
    /// no prefabs. This hook fires after any scene loads and stands the world up.
    public static class Bootstrap
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Init()
        {
            if (Object.FindFirstObjectByType<GameController>() != null) return;

            // Clear whatever placeholder content the boot scene carried.
            foreach (var root in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
                Object.Destroy(root);

            var go = new GameObject("GameController");
            go.AddComponent<GameController>();
            Object.DontDestroyOnLoad(go);
        }
    }
}
