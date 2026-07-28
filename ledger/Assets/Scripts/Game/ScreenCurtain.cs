using Ledger.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// The curtain, on screen (game-feel-spec.md §8).
    ///
    /// The spec's rule is no hard cuts anywhere, and the worst offender in
    /// the game is the Fall: three days vanish, the money is seized, and
    /// every person on the street stops guessing about you and simply knows.
    /// It happened as a line of amber text sliding in over a normally-lit
    /// street while the world snapped three days forward in front of you.
    ///
    /// Now it is staged. Fade down, change the world UNDER black where
    /// nobody can see the join, hold on the words long enough to be
    /// uncomfortable, and come back into a different morning. The held beat
    /// is the part that gets skipped and the part that does the work — the
    /// silence is what makes a player sit with it instead of reading it.
    public class ScreenCurtain : MonoBehaviour
    {
        static ScreenCurtain _instance;

        readonly Curtain _curtain = new Curtain();
        Image _black;
        Text _line;
        System.Action _underBlack;

        public static bool Busy => _instance != null && _instance._curtain.Running;

        /// Drop the curtain, run `underBlack` at the moment nothing is
        /// visible, and hold `line` while it is down. Returns false if a
        /// curtain is already falling, in which case the caller must do its
        /// own work immediately rather than lose it.
        public static bool Fall(Transform uiRoot, string line, System.Action underBlack,
                                float hold = 2.6f)
        {
            if (uiRoot == null) return false;
            if (_instance == null)
            {
                var go = new GameObject("ScreenCurtain");
                go.transform.SetParent(uiRoot, false);
                _instance = go.AddComponent<ScreenCurtain>();
                _instance.Build(go.transform);
            }
            if (_instance._curtain.Running) return false;

            _instance._curtain.HoldSeconds = hold;
            _instance._underBlack = underBlack;
            _instance._line.text = line ?? "";
            // Last in the hierarchy = drawn on top of every other panel. A
            // curtain that the ledger renders over is not a curtain.
            _instance.transform.SetAsLastSibling();
            return _instance._curtain.Begin();
        }

        void Build(Transform root)
        {
            var blackGo = new GameObject("Black");
            blackGo.transform.SetParent(root, false);
            _black = blackGo.AddComponent<Image>();
            _black.color = new Color(0, 0, 0, 0);
            _black.raycastTarget = false;
            Stretch(_black.rectTransform);

            var textGo = new GameObject("CurtainLine");
            textGo.transform.SetParent(root, false);
            _line = textGo.AddComponent<Text>();
            _line.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            _line.fontSize = 26;
            _line.alignment = TextAnchor.MiddleCenter;
            _line.color = new Color(0, 0, 0, 0);
            _line.raycastTarget = false;
            var rt = _line.rectTransform;
            Stretch(rt);
            rt.offsetMin = new Vector2(120, 0);
            rt.offsetMax = new Vector2(-120, 0);
        }

        static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        void Update()
        {
            bool wasRunning = _curtain.Running;
            _curtain.Tick(Time.deltaTime);

            if (_curtain.Hidden && _underBlack != null)
            {
                // Everything jarring happens on this one frame, with the
                // screen fully covered.
                var work = _underBlack;
                _underBlack = null;
                work();
            }

            if (_black != null) _black.color = new Color(0, 0, 0, (float)_curtain.Alpha);
            if (_line != null)
                _line.color = new Color(0.92f, 0.87f, 0.78f, (float)_curtain.TextAlpha);

            // A curtain that never lifts because the work threw is worse than
            // no curtain at all, so make sure the screen is clear once it is
            // done regardless of what happened in between.
            if (wasRunning && !_curtain.Running && _black != null)
                _black.color = new Color(0, 0, 0, 0);
        }
    }
}
