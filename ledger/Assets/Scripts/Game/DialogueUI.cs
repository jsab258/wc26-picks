using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// All UI for M0, constructed from code: HUD clock, talk prompt, the
    /// conversation window, first-run API key entry (F2), and the debug
    /// "Ledger" panel (F1) showing memory/suspicion/cost live.
    public class DialogueUI : MonoBehaviour
    {
        GameController _game;
        PlayerController _player;
        ConversationHost _lena;

        Font _font;
        Text _clockText;
        Text _promptText;

        GameObject _dialoguePanel;
        Text _historyText;
        InputField _input;
        readonly List<string> _history = new List<string>();
        bool _waiting;

        GameObject _keyPanel;
        InputField _keyInput;

        GameObject _debugPanel;
        Text _debugText;

        public static DialogueUI Create(GameController game, PlayerController player, ConversationHost lena)
        {
            var go = new GameObject("UI");
            var ui = go.AddComponent<DialogueUI>();
            ui._game = game;
            ui._player = player;
            ui._lena = lena;
            ui.Build();
            return ui;
        }

        void Build()
        {
            _font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

            var canvasGo = new GameObject("Canvas");
            canvasGo.transform.SetParent(transform, false);
            var canvas = canvasGo.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
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

            _clockText = MakeText(canvasGo.transform, "Clock", new Vector2(1, 1), new Vector2(-20, -20), new Vector2(360, 40), 26, TextAnchor.UpperRight);
            _promptText = MakeText(canvasGo.transform, "Prompt", new Vector2(0.5f, 0), new Vector2(0, 60), new Vector2(800, 36), 22, TextAnchor.MiddleCenter);
            MakeText(canvasGo.transform, "Help", new Vector2(0, 1), new Vector2(20, -20), new Vector2(700, 32), 16, TextAnchor.UpperLeft)
                .text = "WASD move · Shift run · E talk · F1 ledger · F2 API key · Esc close";

            BuildDialoguePanel(canvasGo.transform);
            BuildKeyPanel(canvasGo.transform);
            BuildDebugPanel(canvasGo.transform);

            // In self-test (sim) mode, never auto-open the key panel: it would lock
            // input and freeze the sim-driven player. The sim runs without a live key.
            if (Secrets.LoadAnthropicKey() == null && SimMode.Days == 0) _keyPanel.SetActive(true);
        }

        void BuildDialoguePanel(Transform parent)
        {
            _dialoguePanel = MakePanel(parent, "Dialogue", new Vector2(0.5f, 0), new Vector2(0, 120), new Vector2(900, 420));
            MakeText(_dialoguePanel.transform, "Title", new Vector2(0.5f, 1), new Vector2(0, -12), new Vector2(860, 30), 22, TextAnchor.UpperCenter)
                .text = "Lena Moreau";
            _historyText = MakeText(_dialoguePanel.transform, "History", new Vector2(0.5f, 1), new Vector2(0, -50), new Vector2(860, 280), 18, TextAnchor.LowerLeft);

            _input = MakeInput(_dialoguePanel.transform, "Say something...", new Vector2(0.5f, 0), new Vector2(-60, 18), new Vector2(720, 44));
            var sendBtn = MakeButton(_dialoguePanel.transform, "Send", new Vector2(1, 0), new Vector2(-16, 18), new Vector2(110, 44));
            sendBtn.onClick.AddListener(Submit);
            _dialoguePanel.SetActive(false);
        }

        void BuildKeyPanel(Transform parent)
        {
            _keyPanel = MakePanel(parent, "KeyPanel", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(760, 220));
            MakeText(_keyPanel.transform, "KeyTitle", new Vector2(0.5f, 1), new Vector2(0, -14), new Vector2(720, 60), 18, TextAnchor.UpperCenter)
                .text = "Paste your Anthropic API key (stored only on this PC, never uploaded).\nGet one at console.anthropic.com.";
            _keyInput = MakeInput(_keyPanel.transform, "sk-ant-...", new Vector2(0.5f, 0.5f), new Vector2(0, -10), new Vector2(700, 44));
            var saveBtn = MakeButton(_keyPanel.transform, "Save", new Vector2(0.5f, 0), new Vector2(0, 16), new Vector2(140, 44));
            saveBtn.onClick.AddListener(() =>
            {
                var key = _keyInput.text.Trim();
                if (key.Length < 8) return;
                Secrets.SaveAnthropicKey(key);
                _lena.Reconnect(key);
                _keyPanel.SetActive(false);
            });
            _keyPanel.SetActive(false);
        }

        void BuildDebugPanel(Transform parent)
        {
            _debugPanel = MakePanel(parent, "DebugPanel", new Vector2(0, 0.5f), new Vector2(20, 0), new Vector2(640, 700));
            _debugText = MakeText(_debugPanel.transform, "DebugText", new Vector2(0.5f, 1), new Vector2(0, -12), new Vector2(600, 676), 14, TextAnchor.UpperLeft);
            _debugPanel.SetActive(false);
        }

        void Update()
        {
            var now = _game.Now;
            _clockText.text = $"Day {now.Day} — {now.Hour:D2}:{now.Minute:D2} ({now.Slot})";

            bool inRange = _lena != null && _lena.PlayerInRange(_player.transform);
            bool dialogueOpen = _dialoguePanel.activeSelf;
            _promptText.text = !dialogueOpen && inRange ? "Press E to talk to Lena" : "";

            if (Input.GetKeyDown(KeyCode.E) && inRange && !dialogueOpen && !_keyPanel.activeSelf)
                OpenDialogue();
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                if (dialogueOpen) CloseDialogue();
                _keyPanel.SetActive(false);
                _debugPanel.SetActive(false);
            }
            if (Input.GetKeyDown(KeyCode.F1)) _debugPanel.SetActive(!_debugPanel.activeSelf);
            if (Input.GetKeyDown(KeyCode.F2)) _keyPanel.SetActive(!_keyPanel.activeSelf);

            if (_debugPanel.activeSelf && _lena != null && Time.frameCount % 30 == 0)
                _debugText.text = _lena.DebugReport() +
                    (_game.Gossip != null ? "\n\n" + _game.Gossip.StatusLine() : "");

            if (dialogueOpen && _input.isFocused && Input.GetKeyDown(KeyCode.Return))
                Submit();

            _player.InputLocked = dialogueOpen || _keyPanel.activeSelf;
        }

        void OpenDialogue()
        {
            _dialoguePanel.SetActive(true);
            _input.text = "";
            _input.ActivateInputField();
            RenderHistory();
        }

        void CloseDialogue() => _dialoguePanel.SetActive(false);

        async void Submit()
        {
            var text = _input.text.Trim();
            if (text.Length == 0 || _waiting) return;
            _input.text = "";
            _input.ActivateInputField();

            _history.Add($"<b>You:</b> {text}");
            _history.Add("<i>Lena is thinking...</i>");
            RenderHistory();

            _waiting = true;
            var reply = await _lena.SayAsync(text); // Unity's context resumes this on the main thread
            _waiting = false;

            _history.RemoveAt(_history.Count - 1);
            _history.Add($"<b>Lena:</b> {reply}");
            RenderHistory();
        }

        void RenderHistory()
        {
            int start = Mathf.Max(0, _history.Count - 10);
            var sb = new System.Text.StringBuilder();
            for (int i = start; i < _history.Count; i++) sb.AppendLine(_history[i]);
            _historyText.text = sb.ToString();
        }

        // ---- code-built uGUI helpers ----

        GameObject MakePanel(Transform parent, string name, Vector2 anchor, Vector2 offset, Vector2 size)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<Image>();
            img.color = new Color(0.08f, 0.08f, 0.1f, 0.92f);
            Place(go, anchor, offset, size);
            return go;
        }

        Text MakeText(Transform parent, string name, Vector2 anchor, Vector2 offset, Vector2 size, int fontSize, TextAnchor align)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var text = go.AddComponent<Text>();
            text.font = _font;
            text.fontSize = fontSize;
            text.alignment = align;
            text.color = Color.white;
            text.supportRichText = true;
            Place(go, anchor, offset, size);
            return text;
        }

        InputField MakeInput(Transform parent, string placeholder, Vector2 anchor, Vector2 offset, Vector2 size)
        {
            var go = new GameObject("Input");
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<Image>();
            img.color = new Color(0.16f, 0.16f, 0.2f, 1f);
            Place(go, anchor, offset, size);

            var textComp = MakeText(go.transform, "Text", new Vector2(0.5f, 0.5f), Vector2.zero, size - new Vector2(20, 8), 18, TextAnchor.MiddleLeft);
            var placeholderComp = MakeText(go.transform, "Placeholder", new Vector2(0.5f, 0.5f), Vector2.zero, size - new Vector2(20, 8), 18, TextAnchor.MiddleLeft);
            placeholderComp.text = placeholder;
            placeholderComp.color = new Color(1, 1, 1, 0.35f);
            placeholderComp.fontStyle = FontStyle.Italic;

            var input = go.AddComponent<InputField>();
            input.textComponent = textComp;
            input.placeholder = placeholderComp;
            return input;
        }

        Button MakeButton(Transform parent, string label, Vector2 anchor, Vector2 offset, Vector2 size)
        {
            var go = new GameObject($"Button_{label}");
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<Image>();
            img.color = new Color(0.25f, 0.35f, 0.5f, 1f);
            Place(go, anchor, offset, size);
            var text = MakeText(go.transform, "Label", new Vector2(0.5f, 0.5f), Vector2.zero, size, 18, TextAnchor.MiddleCenter);
            text.text = label;
            return go.AddComponent<Button>();
        }

        static void Place(GameObject go, Vector2 anchor, Vector2 offset, Vector2 size)
        {
            var rect = go.GetComponent<RectTransform>();
            if (rect == null) rect = go.AddComponent<RectTransform>();
            rect.anchorMin = anchor;
            rect.anchorMax = anchor;
            rect.pivot = anchor;
            rect.anchoredPosition = offset;
            rect.sizeDelta = size;
        }
    }
}
