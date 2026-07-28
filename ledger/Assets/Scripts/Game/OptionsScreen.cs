using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// Options and controls, as ONE screen that two places can open (player
    /// decision 7, 2026-07-27).
    ///
    /// It used to live inside MainMenu, which meant the only way to change text
    /// size, mouse sensitivity, volume or a keybinding was to quit to the main
    /// menu. That fails the plainest expectation a player has of a pause menu.
    ///
    /// The fix is deliberately an EXTRACTION rather than a second copy. The last
    /// time this front end had two lists of the same thing — the rebind rows and
    /// the real bindings — they drifted, and three keys became un-rebindable
    /// because adding a binding and adding a row are two edits and nobody does
    /// the second one. A duplicated options panel would drift exactly the same
    /// way, so there is one, and MainMenu opens it like everybody else.
    ///
    /// It builds its own overlay canvas at a high sort order, so it works over
    /// the menu and over a paused city without either of them knowing.
    public class OptionsScreen : MonoBehaviour
    {
        public static bool Open { get; private set; }

        Font _font;
        Transform _canvas;
        GameObject _optionsPanel, _keysPanel;
        string _rebinding;
        GameObject _shade;
        System.Action _onClose;
        readonly Dictionary<string, Text> _keyLabels = new Dictionary<string, Text>();

        /// Show it. `onClose` runs when the player backs out — the caller uses it
        /// to put its own screen back.
        public static OptionsScreen Show(System.Action onClose = null)
        {
            var go = new GameObject("OptionsScreen");
            var screen = go.AddComponent<OptionsScreen>();
            screen._onClose = onClose;
            screen.Build();
            Open = true;
            return screen;
        }

        void Build()
        {
            _font = UiTheme.LoadFont();

            var canvasGo = new GameObject("OptionsCanvas");
            canvasGo.transform.SetParent(transform, false);
            var canvas = canvasGo.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            // Above the main menu (100) and far above the in-game HUD, because
            // this opens over both.
            canvas.sortingOrder = 300;
            var scaler = canvasGo.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            canvasGo.AddComponent<GraphicRaycaster>();
            if (Object.FindFirstObjectByType<UnityEngine.EventSystems.EventSystem>() == null)
            {
                var es = new GameObject("EventSystem");
                es.AddComponent<UnityEngine.EventSystems.EventSystem>();
                es.AddComponent<UnityEngine.EventSystems.StandaloneInputModule>();
            }
            _canvas = canvasGo.transform;

            // A dimmed field behind, so opening this over a live city reads as
            // stepping out of it rather than as a panel floating over traffic.
            var shade = new GameObject("Shade");
            shade.transform.SetParent(_canvas, false);
            shade.AddComponent<Image>().color = new Color(0.04f, 0.06f, 0.055f, 0.92f);
            Stretch(shade);
            // The shade arrives with the panel rather than a frame ahead of
            // it, or the city dims and then waits.
            UiFade.In(shade);
            _shade = shade;

            BuildOptions();
            BuildKeys();
            _optionsPanel.SetActive(true);
            UiFade.In(_optionsPanel);
            _showing = _optionsPanel;
        }

        void BuildOptions()
        {
            _optionsPanel = Panel(_canvas, "Options", new Vector2(760, 620));
            var s = GameSettings.Current;

            Label(_optionsPanel.transform, "O P T I O N S", new Vector2(0.5f, 1), new Vector2(0, -22),
                new Vector2(700, 38), Typography.Title, TextAnchor.UpperCenter).color = UiTheme.Dim;

            float y = -90;
            MenuSlider(_optionsPanel.transform, "Master volume", y, s.MasterVolume,
                v => { s.MasterVolume = v; Audio.ApplyVolumes(); }); y -= 58;
            MenuSlider(_optionsPanel.transform, "Music", y, s.MusicVolume,
                v => { s.MusicVolume = v; Audio.ApplyVolumes(); }); y -= 58;
            MenuSlider(_optionsPanel.transform, "Sound", y, s.SfxVolume,
                v => { s.SfxVolume = v; Audio.ApplyVolumes(); }); y -= 58;
            MenuSlider(_optionsPanel.transform, "Mouse sensitivity", y,
                Mathf.InverseLerp(0.2f, 3f, s.MouseSensitivity),
                v => s.MouseSensitivity = Mathf.Lerp(0.2f, 3f, v)); y -= 58;
            MenuSlider(_optionsPanel.transform, "Text size", y,
                Mathf.InverseLerp(80, 150, s.TextScalePercent),
                v => s.TextScalePercent = Mathf.RoundToInt(Mathf.Lerp(80, 150, v))); y -= 64;

            MenuToggle(_optionsPanel.transform, "Colourblind-safe colours", y, s.ColourblindSafe,
                v => { s.ColourblindSafe = v; UiTheme.SetColourblind(v); }); y -= 48;
            MenuToggle(_optionsPanel.transform, "Show the odds before risky moves", y, s.ShowOdds,
                v => s.ShowOdds = v); y -= 60;

            // Text size only takes effect on panels built after the change, so
            // say so rather than letting the player wonder why the slider looks
            // broken. Honest beats clever.
            Label(_optionsPanel.transform, "Text size applies to screens opened after this one.",
                new Vector2(0.5f, 1), new Vector2(0, y - 6), new Vector2(660, 26), Typography.Small,
                TextAnchor.UpperCenter).color = UiTheme.Dim;
            y -= 42;

            MenuButton(_optionsPanel.transform, "Controls…", new Vector2(0.5f, 1), new Vector2(0, y),
                new Vector2(300, 44))
                .onClick.AddListener(() => Swap(_optionsPanel, _keysPanel));

            MenuButton(_optionsPanel.transform, "Back", new Vector2(0.5f, 0), new Vector2(0, 24),
                new Vector2(220, 46)).onClick.AddListener(Close);
            _optionsPanel.SetActive(false);
        }

        void BuildKeys()
        {
            _keysPanel = Panel(_canvas, "Controls", new Vector2(680, 640));
            Label(_keysPanel.transform, "C O N T R O L S", new Vector2(0.5f, 1), new Vector2(0, -22),
                new Vector2(620, 38), Typography.Title, TextAnchor.UpperCenter).color = UiTheme.Dim;
            Label(_keysPanel.transform, "WASD moves. Shift runs. Click an action to rebind it.",
                new Vector2(0.5f, 1), new Vector2(0, -58), new Vector2(620, 28), Typography.Small,
                TextAnchor.UpperCenter).color = UiTheme.Dim;

            // Driven from the bindings themselves. The hardcoded version had
            // drifted to six rows while the game listened for nine.
            float y = -110;
            foreach (var action in new List<string>(GameSettings.Current.Keys.Keys))
            {
                var a = action;
                Label(_keysPanel.transform, a, new Vector2(0, 1), new Vector2(60, y),
                    new Vector2(260, 32), Typography.Body, TextAnchor.MiddleLeft);
                var btn = MenuButton(_keysPanel.transform, GameSettings.Current.Key(a).ToString(),
                    new Vector2(1, 1), new Vector2(-60, y - 4), new Vector2(220, 38));
                _keyLabels[a] = btn.GetComponentInChildren<Text>();
                btn.onClick.AddListener(() =>
                {
                    _rebinding = a;
                    _keyLabels[a].text = "press a key…";
                });
                y -= 52;
            }

            MenuButton(_keysPanel.transform, "Back", new Vector2(0.5f, 0), new Vector2(0, 24),
                new Vector2(220, 46)).onClick.AddListener(() =>
                {
                    GameSettings.Current.Save();
                    Swap(_keysPanel, _optionsPanel);
                });
            _keysPanel.SetActive(false);
        }

        /// Everything the rebind screen currently lists — the smoke test
        /// compares this against the actions the game listens for, because the
        /// hardcoded version once drifted to six rows against nine actions
        /// (the founding bug of the UI test file).
        public IReadOnlyCollection<string> ListedActions => _keyLabels.Keys;

        /// One panel leaves while the other arrives, overlapping. Blanking
        /// between them would say the whole screen went away when only its
        /// contents did.
        void Swap(GameObject from, GameObject to)
        {
            UiFade.Out(from);
            to.SetActive(true);
            var f = UiFade.In(to);
            f.Fade.InSeconds = Menus.SwapSeconds;
            f.Fade.RisePixels = 0;      // the frame around them never moved
            var g = UiFade.Ensure(from);
            g.Fade.OutSeconds = Menus.SwapSeconds;
            g.Fade.RisePixels = 0;
            _showing = to;
        }
        GameObject _showing;

        public void Close()
        {
            if (_closing) return;
            _closing = true;
            GameSettings.Current.Save();
            // Open flips NOW rather than when the object dies: the caller uses
            // it to decide whether the options screen is up, and leaving it
            // true through the fade would let a second Escape open a second
            // one over the first.
            Open = false;
            UiFade.Out(_optionsPanel);
            UiFade.Out(_keysPanel);
            UiFade.Out(_shade);
            _onClose?.Invoke();
            // Destroyed only once the fade has actually finished. Destroying
            // on the click is exactly the hard cut this replaces.
            Destroy(gameObject, (float)Menus.OutSeconds + 0.02f);
        }
        bool _closing;

        void Update()
        {
            if (_rebinding != null)
            {
                foreach (KeyCode code in System.Enum.GetValues(typeof(KeyCode)))
                {
                    if (code == KeyCode.None || !Input.GetKeyDown(code)) continue;
                    if (code != KeyCode.Escape) GameSettings.Current.Rebind(_rebinding, code);
                    foreach (var pair in _keyLabels)
                        pair.Value.text = GameSettings.Current.Key(pair.Key).ToString();
                    _rebinding = null;
                    GameSettings.Current.Save();
                    break;
                }
                return;
            }

            // Escape backs out one level, like every other screen in the game.
            if (!Input.GetKeyDown(KeyCode.Escape)) return;
            if (_showing == _keysPanel)
            {
                Swap(_keysPanel, _optionsPanel);
                return;
            }
            Close();
        }

        // ---- widgets (same Two Books grammar as the rest of the UI) ----

        GameObject Panel(Transform parent, string name, Vector2 size)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.AddComponent<Image>().color = UiTheme.Hairline;
            Place(go, new Vector2(0.5f, 0.5f), Vector2.zero, size);
            var fill = new GameObject("Fill");
            fill.transform.SetParent(go.transform, false);
            fill.AddComponent<Image>().color = UiTheme.PanelBg;
            var r = fill.GetComponent<RectTransform>();
            r.anchorMin = Vector2.zero; r.anchorMax = Vector2.one;
            r.offsetMin = new Vector2(1, 1); r.offsetMax = new Vector2(-1, -1);
            return go;
        }

        Text Label(Transform parent, string text, Vector2 anchor, Vector2 offset, Vector2 size,
            int fontSize, TextAnchor align)
        {
            var go = new GameObject("Label");
            go.transform.SetParent(parent, false);
            var t = go.AddComponent<Text>();
            t.font = _font; t.fontSize = UiTheme.Scaled(fontSize); t.alignment = align;
            t.color = UiTheme.Ink; t.supportRichText = true; t.text = text;
            Place(go, anchor, offset, size);
            return t;
        }

        Button MenuButton(Transform parent, string label, Vector2 anchor, Vector2 offset, Vector2 size)
        {
            var go = new GameObject($"Btn_{label}");
            go.transform.SetParent(parent, false);
            go.AddComponent<Image>().color = UiTheme.ButtonBg;
            Place(go, anchor, offset, size);
            Label(go.transform, label, new Vector2(0.5f, 0.5f), Vector2.zero, size, 19, TextAnchor.MiddleCenter);
            return go.AddComponent<Button>();
        }

        void MenuSlider(Transform parent, string label, float y, float value, System.Action<float> onChange)
        {
            Label(parent, label, new Vector2(0, 1), new Vector2(60, y), new Vector2(320, 30), 17, TextAnchor.MiddleLeft);
            var go = new GameObject($"Slider_{label}");
            go.transform.SetParent(parent, false);
            Place(go, new Vector2(1, 1), new Vector2(-60, y - 6), new Vector2(300, 20));
            var bg = new GameObject("Track");
            bg.transform.SetParent(go.transform, false);
            bg.AddComponent<Image>().color = UiTheme.Field;
            Stretch(bg);
            var fillArea = new GameObject("Fill");
            fillArea.transform.SetParent(go.transform, false);
            var fillImg = fillArea.AddComponent<Image>();
            fillImg.color = UiTheme.Credit;
            var fr = fillArea.GetComponent<RectTransform>();
            fr.anchorMin = Vector2.zero; fr.anchorMax = Vector2.one;
            fr.offsetMin = Vector2.zero; fr.offsetMax = Vector2.zero;
            var slider = go.AddComponent<Slider>();
            slider.fillRect = fr;
            slider.targetGraphic = fillImg;
            slider.direction = Slider.Direction.LeftToRight;
            slider.minValue = 0; slider.maxValue = 1; slider.value = value;
            slider.onValueChanged.AddListener(v => onChange(v));
        }

        void MenuToggle(Transform parent, string label, float y, bool value, System.Action<bool> onChange)
        {
            Label(parent, label, new Vector2(0, 1), new Vector2(60, y), new Vector2(420, 30), 17, TextAnchor.MiddleLeft);
            var btn = MenuButton(parent, value ? "on" : "off", new Vector2(1, 1), new Vector2(-60, y - 4), new Vector2(120, 34));
            var lbl = btn.GetComponentInChildren<Text>();
            bool state = value;
            btn.onClick.AddListener(() =>
            {
                state = !state;
                lbl.text = state ? "on" : "off";
                onChange(state);
            });
        }

        static void Stretch(GameObject go)
        {
            var r = go.GetComponent<RectTransform>() ?? go.AddComponent<RectTransform>();
            r.anchorMin = Vector2.zero; r.anchorMax = Vector2.one;
            r.offsetMin = Vector2.zero; r.offsetMax = Vector2.zero;
        }

        static void Place(GameObject go, Vector2 anchor, Vector2 offset, Vector2 size)
        {
            var rect = go.GetComponent<RectTransform>() ?? go.AddComponent<RectTransform>();
            rect.anchorMin = anchor; rect.anchorMax = anchor; rect.pivot = anchor;
            rect.anchoredPosition = offset; rect.sizeDelta = size;
        }
    }
}
