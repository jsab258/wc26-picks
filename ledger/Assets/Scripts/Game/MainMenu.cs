using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// The front end (production track P1). The game used to boot straight into
    /// Hook Street with no way out; this stands in front of it. Two Books
    /// visual language, same code-built uGUI as everything else — no scenes,
    /// no prefabs. Never appears in sim mode.
    public class MainMenu : MonoBehaviour
    {
        Font _font;
        Transform _canvas;
        GameObject _root, _optionsPanel, _keysPanel;
        Text _continueLabel, _saveNote;
        string _rebinding;   // action awaiting a keypress

        public static bool Showing { get; private set; }

        public static MainMenu Create()
        {
            var go = new GameObject("MainMenu");
            var menu = go.AddComponent<MainMenu>();
            menu.Build();
            Showing = true;
            return menu;
        }

        void Build()
        {
            _font = UiTheme.LoadFont();
            var canvasGo = new GameObject("MenuCanvas");
            canvasGo.transform.SetParent(transform, false);
            var canvas = canvasGo.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 100;
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

            // A full-bleed dark field: the books, closed.
            var bg = new GameObject("Field");
            bg.transform.SetParent(_canvas, false);
            bg.AddComponent<Image>().color = new Color(0.04f, 0.06f, 0.055f, 1f);
            var br = bg.GetComponent<RectTransform>();
            br.anchorMin = Vector2.zero; br.anchorMax = Vector2.one;
            br.offsetMin = Vector2.zero; br.offsetMax = Vector2.zero;

            _root = new GameObject("Front");
            _root.transform.SetParent(_canvas, false);
            Stretch(_root);

            var title = Label(_root.transform, "L E D G E R", new Vector2(0.5f, 0.5f), new Vector2(0, 250), new Vector2(900, 90), 64, TextAnchor.MiddleCenter);
            title.color = UiTheme.Ink;
            var sub = Label(_root.transform, "Your two lives are two accounts.", new Vector2(0.5f, 0.5f), new Vector2(0, 190), new Vector2(900, 40), 20, TextAnchor.MiddleCenter);
            sub.color = UiTheme.Dim;

            var hasSave = SaveSlots.HasAny();
            var contBtn = MenuButton(_root.transform, hasSave ? "Continue" : "Continue (no save)", new Vector2(0.5f, 0.5f), new Vector2(0, 70), new Vector2(360, 52));
            _continueLabel = contBtn.GetComponentInChildren<Text>();
            contBtn.interactable = hasSave;
            contBtn.onClick.AddListener(() => StartGame(load: true));

            MenuButton(_root.transform, "New game", new Vector2(0.5f, 0.5f), new Vector2(0, 4), new Vector2(360, 52))
                .onClick.AddListener(() => StartGame(load: false));
            MenuButton(_root.transform, "Options", new Vector2(0.5f, 0.5f), new Vector2(0, -62), new Vector2(360, 52))
                .onClick.AddListener(() => ShowOptions(true));
            MenuButton(_root.transform, "Quit", new Vector2(0.5f, 0.5f), new Vector2(0, -128), new Vector2(360, 52))
                .onClick.AddListener(Quit);

            _saveNote = Label(_root.transform, SaveSlots.Describe(), new Vector2(0.5f, 0), new Vector2(0, 90), new Vector2(1100, 30), 15, TextAnchor.LowerCenter);
            _saveNote.color = UiTheme.Dim;
            Label(_root.transform, "Conversations are live — press F2 in game to enter an Anthropic API key.", new Vector2(0.5f, 0), new Vector2(0, 50), new Vector2(1100, 28), 14, TextAnchor.LowerCenter)
                .color = UiTheme.Dim;

            BuildOptions();
        }

        // ---- options ----

        void BuildOptions()
        {
            _optionsPanel = Panel(_canvas, "Options", new Vector2(760, 620));
            var s = GameSettings.Current;

            Label(_optionsPanel.transform, "O P T I O N S", new Vector2(0.5f, 1), new Vector2(0, -22), new Vector2(700, 34), 22, TextAnchor.UpperCenter)
                .color = UiTheme.Dim;

            float y = -90;
            MenuSlider(_optionsPanel.transform, "Master volume", y, s.MasterVolume, v => { s.MasterVolume = v; Audio.ApplyVolumes(); }); y -= 58;
            MenuSlider(_optionsPanel.transform, "Music", y, s.MusicVolume, v => { s.MusicVolume = v; Audio.ApplyVolumes(); }); y -= 58;
            MenuSlider(_optionsPanel.transform, "Sound", y, s.SfxVolume, v => { s.SfxVolume = v; Audio.ApplyVolumes(); }); y -= 58;
            MenuSlider(_optionsPanel.transform, "Mouse sensitivity", y, Mathf.InverseLerp(0.2f, 3f, s.MouseSensitivity),
                v => s.MouseSensitivity = Mathf.Lerp(0.2f, 3f, v)); y -= 58;
            MenuSlider(_optionsPanel.transform, "Text size", y, Mathf.InverseLerp(80, 150, s.TextScalePercent),
                v => s.TextScalePercent = Mathf.RoundToInt(Mathf.Lerp(80, 150, v))); y -= 64;

            MenuToggle(_optionsPanel.transform, "Colourblind-safe colours", y, s.ColourblindSafe, v => { s.ColourblindSafe = v; UiTheme.SetColourblind(v); }); y -= 48;
            MenuToggle(_optionsPanel.transform, "Show the odds before risky moves", y, s.ShowOdds, v => s.ShowOdds = v); y -= 60;

            MenuButton(_optionsPanel.transform, "Controls…", new Vector2(0.5f, 1), new Vector2(0, y), new Vector2(300, 44))
                .onClick.AddListener(() => { _optionsPanel.SetActive(false); _keysPanel.SetActive(true); });

            MenuButton(_optionsPanel.transform, "Back", new Vector2(0.5f, 0), new Vector2(0, 24), new Vector2(220, 46))
                .onClick.AddListener(() => { GameSettings.Current.Save(); ShowOptions(false); });
            _optionsPanel.SetActive(false);

            BuildKeys();
        }

        readonly Dictionary<string, Text> _keyLabels = new Dictionary<string, Text>();

        void BuildKeys()
        {
            _keysPanel = Panel(_canvas, "Controls", new Vector2(680, 560));
            Label(_keysPanel.transform, "C O N T R O L S", new Vector2(0.5f, 1), new Vector2(0, -22), new Vector2(620, 34), 22, TextAnchor.UpperCenter)
                .color = UiTheme.Dim;
            Label(_keysPanel.transform, "WASD moves. Shift runs. Click an action to rebind it.", new Vector2(0.5f, 1), new Vector2(0, -58), new Vector2(620, 28), 15, TextAnchor.UpperCenter)
                .color = UiTheme.Dim;

            float y = -110;
            foreach (var action in new[] { "Talk", "Ledger", "Coat", "Save", "Debug", "Pause" })
            {
                var a = action;
                Label(_keysPanel.transform, a, new Vector2(0, 1), new Vector2(60, y), new Vector2(260, 32), 18, TextAnchor.MiddleLeft);
                var btn = MenuButton(_keysPanel.transform, GameSettings.Current.Key(a).ToString(), new Vector2(1, 1), new Vector2(-60, y - 4), new Vector2(220, 38));
                _keyLabels[a] = btn.GetComponentInChildren<Text>();
                btn.onClick.AddListener(() =>
                {
                    _rebinding = a;
                    _keyLabels[a].text = "press a key…";
                });
                y -= 52;
            }

            MenuButton(_keysPanel.transform, "Back", new Vector2(0.5f, 0), new Vector2(0, 24), new Vector2(220, 46))
                .onClick.AddListener(() =>
                {
                    GameSettings.Current.Save();
                    _keysPanel.SetActive(false);
                    _optionsPanel.SetActive(true);
                });
            _keysPanel.SetActive(false);
        }

        void ShowOptions(bool on)
        {
            _optionsPanel.SetActive(on);
            _root.SetActive(!on);
        }

        void Update()
        {
            if (_rebinding == null) return;
            foreach (KeyCode code in System.Enum.GetValues(typeof(KeyCode)))
            {
                if (code == KeyCode.None || !Input.GetKeyDown(code)) continue;
                if (code != KeyCode.Escape) GameSettings.Current.Rebind(_rebinding, code);
                foreach (var pair in _keyLabels) pair.Value.text = GameSettings.Current.Key(pair.Key).ToString();
                _rebinding = null;
                GameSettings.Current.Save();
                break;
            }
        }

        // ---- transitions ----

        void StartGame(bool load)
        {
            if (!load) SaveSlots.DeleteAll();
            GameSettings.Current.Save();
            Showing = false;
            Destroy(gameObject);
            var go = new GameObject("GameController");
            go.AddComponent<GameController>();
        }

        public static void Quit()
        {
            GameSettings.Current.Save();
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        // ---- widgets (same Two Books grammar as DialogueUI) ----

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

        Text Label(Transform parent, string text, Vector2 anchor, Vector2 offset, Vector2 size, int fontSize, TextAnchor align)
        {
            var go = new GameObject("Label");
            go.transform.SetParent(parent, false);
            var t = go.AddComponent<Text>();
            t.font = _font; t.fontSize = fontSize; t.alignment = align;
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
            var slider = go.AddComponent<UnityEngine.UI.Slider>();
            slider.fillRect = fr;
            slider.targetGraphic = fillImg;
            slider.direction = UnityEngine.UI.Slider.Direction.LeftToRight;
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
