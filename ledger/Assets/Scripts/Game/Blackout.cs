using Ledger.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// A short fade to black that OUTLIVES whatever is being torn down
    /// (game-feel-spec §8).
    ///
    /// The Fall has ScreenCurtain, which is two seconds of held silence and
    /// exactly right for three days vanishing. Leaving to the menu is a
    /// different kind of cut and needs a different length: the player has
    /// already decided, so this is a beat rather than a scene. What it shares
    /// with the curtain is the rule — change the world UNDER black, where the
    /// join cannot be seen.
    ///
    /// It builds its OWN canvas on its own root object rather than living
    /// under the UI it is covering, because the whole point is that the thing
    /// it covers is about to be destroyed.
    public class Blackout : MonoBehaviour
    {
        public const float DownSeconds = 0.28f;
        public const float UpSeconds = 0.45f;

        Image _black;
        System.Action _underBlack;
        float _t;
        bool _switched;

        static Blackout _instance;
        public static bool Busy => _instance != null;

        /// Fade down, run `underBlack` at the moment nothing is visible, fade
        /// back up. Returns false if one is already running, so a second click
        /// cannot start a second teardown.
        public static bool Cover(System.Action underBlack)
        {
            if (_instance != null) return false;
            var go = new GameObject("Blackout");
            DontDestroyOnLoad(go);
            _instance = go.AddComponent<Blackout>();
            _instance._underBlack = underBlack;
            _instance.Build();
            return true;
        }

        void Build()
        {
            var canvasGo = new GameObject("BlackoutCanvas");
            canvasGo.transform.SetParent(transform, false);
            var canvas = canvasGo.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            // Above the options screen (300), above everything. A blackout
            // something renders over is not a blackout.
            canvas.sortingOrder = 900;
            var go = new GameObject("Black");
            go.transform.SetParent(canvasGo.transform, false);
            _black = go.AddComponent<Image>();
            _black.color = new Color(0, 0, 0, 0);
            _black.raycastTarget = true;    // nothing is clickable through it
            var r = go.GetComponent<RectTransform>();
            r.anchorMin = Vector2.zero; r.anchorMax = Vector2.one;
            r.offsetMin = Vector2.zero; r.offsetMax = Vector2.zero;
        }

        void Update()
        {
            // Unscaled: the pause menu stopped the clock, and a fade that
            // will not run at timeScale zero is a frozen screen.
            _t += Time.unscaledDeltaTime;

            if (_t < DownSeconds)
            {
                _black.color = new Color(0, 0, 0, (float)Menus.EaseIn(_t / DownSeconds));
                return;
            }

            // The latch, for the same reason VerbBeat and Curtain have one: a
            // long frame must not skip the moment, and this moment is where
            // the entire world is replaced.
            if (!_switched)
            {
                _switched = true;
                _black.color = Color.black;
                var action = _underBlack;
                _underBlack = null;
                action?.Invoke();
                return;     // give the new world a frame to build before revealing it
            }

            float up = (_t - DownSeconds) / UpSeconds;
            if (up >= 1f)
            {
                _instance = null;
                Destroy(gameObject);
                return;
            }
            _black.color = new Color(0, 0, 0, 1f - (float)Menus.EaseIn(up));
        }
    }
}
