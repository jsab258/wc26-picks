using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Drives a CanvasGroup from a Core `PanelFade` (game-feel-spec §8).
    ///
    /// Every menu in this game used SetActive, which is a hard cut — the same
    /// class of thing the Fall used to be before it got a curtain. The Core
    /// side holds all the timing and all the awkward cases (reversing a
    /// half-finished fade, the leave-once latch, frame-rate independence);
    /// this is only the part that has to touch Unity.
    ///
    /// Deliberately additive: the panel keeps its own layout and this moves
    /// nothing but alpha, interactability and a few pixels of rise. A
    /// transition that also relayouts is a transition that fights the layout.
    [DisallowMultipleComponent]
    public class UiFade : MonoBehaviour
    {
        public readonly PanelFade Fade = new PanelFade();

        CanvasGroup _group;
        RectTransform _rect;
        Vector2 _home;
        bool _homeKnown;
        /// The object is deactivated once it has finished leaving, so it stops
        /// costing layout — but only after the fade, never instead of it.
        public bool DeactivateWhenGone = true;

        /// Attach to a panel that should arrive now.
        public static UiFade In(GameObject go)
        {
            var f = Ensure(go);
            f.Fade.Show();
            if (!go.activeSelf) go.SetActive(true);
            return f;
        }

        /// Attach to a panel that is already on screen and should stay — used
        /// at build time so the first panel does not fade in at boot, which
        /// reads as a stutter rather than as a transition.
        public static UiFade Present(GameObject go)
        {
            var f = Ensure(go);
            f.Fade.SnapOn();
            f.Apply();
            return f;
        }

        public static UiFade Ensure(GameObject go)
        {
            var f = go.GetComponent<UiFade>();
            if (f == null) f = go.AddComponent<UiFade>();
            return f;
        }

        /// Start it leaving. It deactivates itself when it has gone.
        public static void Out(GameObject go)
        {
            if (go == null) return;
            var f = go.GetComponent<UiFade>();
            // Nothing was ever faded in, so there is nothing to fade out —
            // and snapping it on first would flash the panel at full alpha
            // for one frame on its way out.
            if (f == null) { go.SetActive(false); return; }
            f.Fade.Hide();
        }

        void Awake()
        {
            _group = GetComponent<CanvasGroup>();
            if (_group == null) _group = gameObject.AddComponent<CanvasGroup>();
            _rect = GetComponent<RectTransform>();
            if (_rect != null) { _home = _rect.anchoredPosition; _homeKnown = true; }
        }

        void Update()
        {
            // Unscaled: menus open while the game is paused, and a menu that
            // will not fade in because timeScale is zero is a menu that looks
            // broken at exactly the moment the player reached for it.
            Fade.Tick(Time.unscaledDeltaTime);
            Apply();
            if (Fade.Gone && DeactivateWhenGone) gameObject.SetActive(false);
        }

        void Apply()
        {
            if (_group == null) return;
            // TWO CURVES, WHICH IS WHAT CORE SAYS AND WHAT THIS LINE DID NOT DO.
            //
            // `Menus` states the intent in one sentence: *"Ease-out on the way
            // in (fast start, gentle landing) and ease-in on the way out."*
            // This applied `EaseIn` in BOTH directions, so `Menus.EaseOut` has
            // sat on the reach ledger since it was written — and its entry
            // there was pointing at the right gap while describing it slightly
            // wrong. It is not that the panels never use the menu easing; they
            // use exactly half of it.
            //
            // WHY IT MATTERS RATHER THAN BEING SYMMETRY FOR ITS OWN SAKE. A
            // panel arriving should commit immediately and settle — the player
            // asked for it and wants to see it. A panel leaving should let go
            // gently and then get out of the way, because the thing the player
            // now wants is BEHIND it. Running the arrival curve backwards makes
            // a dismissal linger at the exact moment it is in the way, which is
            // one of the two or three things that make a menu feel slow while
            // every duration in it is correct.
            //
            // `Wanted` is the direction and it is already on the state: it is
            // true from the tick `Show` is called and false from the tick
            // `Hide` is, so a panel reversed mid-transition switches curve at
            // the same instant it switches target. Reading a separate direction
            // flag would be a second copy of that fact.
            _group.alpha = (float)(Fade.Wanted ? Menus.EaseIn(Fade.Alpha)
                                               : Menus.EaseOut(Fade.Alpha));
            _group.interactable = Fade.Interactable;
            _group.blocksRaycasts = Fade.Interactable;
            if (_rect != null && _homeKnown && Fade.RisePixels > 0)
                _rect.anchoredPosition = _home - new Vector2(0, (float)Fade.Rise);
        }
    }
}
