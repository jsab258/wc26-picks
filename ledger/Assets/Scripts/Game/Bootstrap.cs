using UnityEngine;

namespace Ledger.Game
{
    /// Everything in M0 is constructed from code at runtime — no authored scenes,
    /// no prefabs. This hook fires after any scene loads and stands the world up.
    ///
    /// THE SCENE RELOAD IS THE ONLY FULL TEARDOWN THIS PROJECT HAS. The city
    /// is parentless root objects — destroying the GameController does not
    /// touch it — and the sweep below is the one thing that does. Every path
    /// that ends a session (the end screen's R, quit-to-menu) must come back
    /// through a reload, or the next `BuildBlock` stands a second city on top
    /// of the first. That was quit-to-menu → New game until 15 Aug: read from
    /// the code, nothing on that path destroyed a root, and the sim never
    /// walks that path so no gate ever saw the doubling.
    public static class Bootstrap
    {
        /// Set by the end screen's R before it reloads: the player asked to
        /// REPLAY THE WEEK, so this reload lands back in the game rather than
        /// at the front door. A static survives the reload, which is exactly
        /// why it is the channel — and it is cleared where it is read, so a
        /// later quit-to-menu cannot inherit it.
        public static bool RestartStraightIn;

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
            // The saved render scale applies at the front door, not on first
            // entering the city — a relaunch that ran the menu at native and
            // then dropped resolution mid-fade would read as something
            // breaking. Guarded inside against sim and batch runs.
            SceneLighting.ApplyRenderScale();
            Audio.Initialize();
            // AND THE CAPTION BAR, here rather than lazily on the first
            // caption. Two of the three channels it carries — the street
            // going quiet and the music turning — are POLLED in its Update
            // rather than pushed, so a bar that only comes into existence
            // when something pushes to it can never show either of them. The
            // channel would have been dead on arrival and looked wired.
            CaptionBar.Ensure();

            if (SimMode.Days > 0 || RestartStraightIn)
            {
                RestartStraightIn = false;
                var go = new GameObject("GameController");
                go.AddComponent<GameController>();
                return;
            }
            MainMenu.Create();
        }
    }
}
