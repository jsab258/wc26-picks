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
            // This attribute hook fires once per process; scene RE-loads (the end
            // screen's restart) come through sceneLoaded instead.
            StandUp();
            UnityEngine.SceneManagement.SceneManager.sceneLoaded += (_, __) => StandUp();
        }

        static void StandUp()
        {
            if (Object.FindFirstObjectByType<GameController>() != null) return;
            if (Object.FindFirstObjectByType<MainMenu>() != null) return;

            // Clear whatever placeholder content the boot scene carried.
            foreach (var root in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
                Object.Destroy(root);

            // Settings and sound come up before anything else; the self-test
            // skips the front end entirely and drops straight into the city.
            UiTheme.SetColourblind(GameSettings.Current.ColourblindSafe);
            Audio.Initialize();
            // AND THE CAPTION BAR, here rather than lazily on the first
            // caption. Two of the three channels it carries — the street
            // going quiet and the music turning — are POLLED in its Update
            // rather than pushed, so a bar that only comes into existence
            // when something pushes to it can never show either of them. The
            // channel would have been dead on arrival and looked wired.
            CaptionBar.Ensure();

            if (SimMode.Days > 0)
            {
                var go = new GameObject("GameController");
                go.AddComponent<GameController>();
                return;
            }
            MainMenu.Create();
        }
    }
}
