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
        GameObject _root;
        Text _continueLabel, _saveNote;

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
            contBtn.onClick.AddListener(() =>
            {
                // Continue opens the NEWEST save wherever it lives — the
                // autosave usually, a fresher manual copy when there is one.
                GameController.PendingLoadPath = SaveSlots.NewestPath();
                StartGame(load: true);
            });

            // P2: the manual copies, each its own door back in.
            float slotY = 70;
            foreach (var (slot, line) in SaveSlots.SlotLines())
            {
                int s2 = slot;
                MenuButton(_root.transform, line, new Vector2(0.5f, 0.5f), new Vector2(430, slotY), new Vector2(300, 44))
                    .onClick.AddListener(() =>
                    {
                        GameController.PendingLoadPath = SaveSlots.SlotPath(s2);
                        StartGame(load: true);
                    });
                slotY -= 52;
            }

            MenuButton(_root.transform, "New game", new Vector2(0.5f, 0.5f), new Vector2(0, 4), new Vector2(360, 52))
                .onClick.AddListener(() => StartGame(load: false));
            MenuButton(_root.transform, "Options", new Vector2(0.5f, 0.5f), new Vector2(0, -62), new Vector2(360, 52))
                .onClick.AddListener(() =>
                {
                    // One options screen, shared with the pause menu. A second
                    // copy is how the rebind list drifted to six rows while the
                    // game listened for nine.
                    UiFade.Out(_root);
                    OptionsScreen.Show(() =>
                    {
                        if (_root == null) return;
                        _root.SetActive(true);
                        UiFade.In(_root);
                    });
                });
            MenuButton(_root.transform, "Quit", new Vector2(0.5f, 0.5f), new Vector2(0, -128), new Vector2(360, 52))
                .onClick.AddListener(Quit);

            _saveNote = Label(_root.transform, SaveSlots.Describe(), new Vector2(0.5f, 0), new Vector2(0, 90), new Vector2(1100, 30), 15, TextAnchor.LowerCenter);
            _saveNote.color = UiTheme.Dim;
            Label(_root.transform, "Conversations are live — press F2 in game to enter an Anthropic API key.", new Vector2(0.5f, 0), new Vector2(0, 50), new Vector2(1100, 28), 14, TextAnchor.LowerCenter)
                .color = UiTheme.Dim;

            // Present, not faded in: the menu IS the boot screen, and fading
            // it up from nothing at launch reads as a stutter rather than as
            // a transition.
            UiFade.Present(_root);
        }

        // Options and controls now live in OptionsScreen, opened from here and
        // from the pause menu. They were here, which meant the only way to
        // change text size or a keybinding was to quit to the main menu.

        // ---- transitions ----

        void StartGame(bool load)
        {
            // Checked BEFORE anything irreversible: below this line the
            // autosave may be deleted, and a double-click that got that far
            // and then bailed would have thrown the save away for nothing.
            if (_starting || Blackout.Busy) return;
            _starting = true;
            if (!load) SaveSlots.DeleteAuto();   // the manual copies are the player's property
            GameSettings.Current.Save();
            Showing = false;
            // The menu leaves and the street arrives UNDER BLACK, where the
            // join cannot be seen. Destroying on the click cut from a dark
            // field straight into a lit city — the same hard cut the Fall
            // used to have, and the last one §8 had left in it.
            UiFade.Out(_root);
            Blackout.Cover(() =>
            {
                Destroy(gameObject);
                var go = new GameObject("GameController");
                go.AddComponent<GameController>();
            });
        }
        bool _starting;

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
