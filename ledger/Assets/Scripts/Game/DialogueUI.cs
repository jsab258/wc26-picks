using System.Collections.Generic;
using Ledger.Core;
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
        List<ConversationHost> _hosts;
        ConversationHost _current;  // who the open dialogue is with
        ConversationHost _nearest;  // who is in talk range right now

        Font _font;
        Transform _canvas;
        Text _clockText;
        Text _statusText;
        Text _toastText;
        float _toastUntil;
        GameObject _endPanel;
        Text _promptText;

        GameObject _ledgerPanel;
        Text _ledgerText;

        GameObject _summaryPanel;
        Text _summaryTitle;
        Text _summaryText;
        float _summaryUntil;

        GameObject _dialoguePanel;
        Text _titleText;
        Text _historyText;
        InputField _input;
        // Each character keeps their own visible conversation log.
        readonly Dictionary<ConversationHost, List<string>> _histories = new Dictionary<ConversationHost, List<string>>();
        bool _waiting;

        GameObject _keyPanel;
        InputField _keyInput;

        // Damage-control row: shown only while talking to someone who is carrying a
        // rumor about the player. Backed entirely by the GossipMill's game-state
        // verbs — the LLM just voices the aftermath.
        GameObject _dcRow;
        Button _payBtn, _leanBtn, _doubtBtn;
        Text _payLabel, _leanLabel, _doubtLabel;
        Button _hookBtn;
        Text _hookLabel;

        GameObject _debugPanel;
        Text _debugText;

        public static DialogueUI Create(GameController game, PlayerController player, List<ConversationHost> hosts)
        {
            var go = new GameObject("UI");
            var ui = go.AddComponent<DialogueUI>();
            ui._game = game;
            ui._player = player;
            ui._hosts = hosts;
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

            _canvas = canvasGo.transform;
            _clockText = MakeText(canvasGo.transform, "Clock", new Vector2(1, 1), new Vector2(-20, -20), new Vector2(360, 40), 26, TextAnchor.UpperRight);
            _statusText = MakeText(canvasGo.transform, "Status", new Vector2(1, 1), new Vector2(-20, -54), new Vector2(640, 30), 18, TextAnchor.UpperRight);
            _toastText = MakeText(canvasGo.transform, "Toast", new Vector2(0.5f, 1), new Vector2(0, -60), new Vector2(1000, 36), 21, TextAnchor.MiddleCenter);
            _promptText = MakeText(canvasGo.transform, "Prompt", new Vector2(0.5f, 0), new Vector2(0, 60), new Vector2(800, 36), 22, TextAnchor.MiddleCenter);
            MakeText(canvasGo.transform, "Help", new Vector2(0, 1), new Vector2(20, -20), new Vector2(700, 32), 16, TextAnchor.UpperLeft)
                .text = "WASD move · Shift run · E talk · C coat · L your ledger · F1 debug · F2 API key · Esc close";

            BuildDialoguePanel(canvasGo.transform);
            BuildKeyPanel(canvasGo.transform);
            BuildDebugPanel(canvasGo.transform);
            BuildLedgerPanel(canvasGo.transform);
            BuildSummaryPanel(canvasGo.transform);

            // In self-test (sim) mode, never auto-open the key panel: it would lock
            // input and freeze the sim-driven player. The sim runs without a live key.
            if (Secrets.LoadAnthropicKey() == null && SimMode.Days == 0) _keyPanel.SetActive(true);
        }

        void BuildDialoguePanel(Transform parent)
        {
            _dialoguePanel = MakePanel(parent, "Dialogue", new Vector2(0.5f, 0), new Vector2(0, 120), new Vector2(900, 420));
            _titleText = MakeText(_dialoguePanel.transform, "Title", new Vector2(0.5f, 1), new Vector2(0, -12), new Vector2(860, 30), 22, TextAnchor.UpperCenter);
            _historyText = MakeText(_dialoguePanel.transform, "History", new Vector2(0.5f, 1), new Vector2(0, -50), new Vector2(860, 280), 18, TextAnchor.LowerLeft);

            _input = MakeInput(_dialoguePanel.transform, "Say something...", new Vector2(0.5f, 0), new Vector2(-60, 18), new Vector2(720, 44));
            var sendBtn = MakeButton(_dialoguePanel.transform, "Send", new Vector2(1, 0), new Vector2(-16, 18), new Vector2(110, 44));
            sendBtn.onClick.AddListener(Submit);

            // Damage-control verbs sit just above the text input, out of the way of
            // normal talk. Only visible when this NPC is actually carrying something.
            _dcRow = new GameObject("DamageControl");
            _dcRow.transform.SetParent(_dialoguePanel.transform, false);
            Place(_dcRow, new Vector2(0.5f, 0), new Vector2(0, 70), new Vector2(860, 40));
            _payBtn = MakeButton(_dcRow.transform, "Pay off", new Vector2(0, 0.5f), new Vector2(0, 0), new Vector2(230, 38));
            _leanBtn = MakeButton(_dcRow.transform, "Lean on them", new Vector2(0.5f, 0.5f), new Vector2(0, 0), new Vector2(230, 38));
            _doubtBtn = MakeButton(_dcRow.transform, "Plant doubt", new Vector2(1, 0.5f), new Vector2(0, 0), new Vector2(230, 38));
            _payLabel = _payBtn.GetComponentInChildren<Text>();
            _leanLabel = _leanBtn.GetComponentInChildren<Text>();
            _doubtLabel = _doubtBtn.GetComponentInChildren<Text>();
            _payBtn.onClick.AddListener(PayOff);
            _leanBtn.onClick.AddListener(LeanOn);
            _doubtBtn.onClick.AddListener(PlantDoubt);
            _dcRow.SetActive(false);

            // The hook (design-doc §6.3): shown whenever the player holds usable
            // leverage on this person — independent of whether they carry any talk,
            // because a leash prevents FUTURE talk too.
            _hookBtn = MakeButton(_dialoguePanel.transform, "Use what you know", new Vector2(0.5f, 0), new Vector2(0, 112), new Vector2(320, 36));
            _hookLabel = _hookBtn.GetComponentInChildren<Text>();
            _hookBtn.onClick.AddListener(UseHook);
            _hookBtn.gameObject.SetActive(false);

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
                foreach (var h in _hosts) h.Reconnect(key);
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

        /// The player-facing Ledger (design-doc §6.2): what YOU believe the city
        /// knows about you — learned through play, snapshots that go stale, never
        /// the live network.
        void BuildLedgerPanel(Transform parent)
        {
            _ledgerPanel = MakePanel(parent, "LedgerPanel", new Vector2(1, 0.5f), new Vector2(-20, 0), new Vector2(560, 620));
            MakeText(_ledgerPanel.transform, "LedgerTitle", new Vector2(0.5f, 1), new Vector2(0, -12), new Vector2(520, 30), 22, TextAnchor.UpperCenter)
                .text = "YOUR LEDGER — what you believe is out there";
            _ledgerText = MakeText(_ledgerPanel.transform, "LedgerText", new Vector2(0.5f, 1), new Vector2(0, -50), new Vector2(520, 556), 16, TextAnchor.UpperLeft);
            _ledgerPanel.SetActive(false);
        }

        void BuildSummaryPanel(Transform parent)
        {
            _summaryPanel = MakePanel(parent, "DaySummary", new Vector2(0.5f, 1), new Vector2(0, -120), new Vector2(640, 250));
            _summaryPanel.GetComponent<Image>().color = new Color(0.06f, 0.06f, 0.09f, 0.95f);
            _summaryTitle = MakeText(_summaryPanel.transform, "SummaryTitle", new Vector2(0.5f, 1), new Vector2(0, -14), new Vector2(600, 32), 24, TextAnchor.UpperCenter);
            _summaryText = MakeText(_summaryPanel.transform, "SummaryText", new Vector2(0.5f, 1), new Vector2(0, -54), new Vector2(580, 180), 18, TextAnchor.UpperLeft);
            _summaryPanel.SetActive(false);
        }

        /// The Persona-style day anchor: each morning, the night's books in one card.
        public void ShowDaySummary(int dayClosed, int takings, int washed, int talkCount,
            string streetWord, string outfitWord, int clean, int dirty)
        {
            if (SimMode.Days > 0) return; // never block the self-test
            _summaryTitle.text = $"— END OF DAY {dayClosed} —";
            var sb = new System.Text.StringBuilder();
            sb.AppendLine($"Bar takings: <b>+${takings}</b>" + (washed > 0 ? $"   ·   washed through the till: <b>${washed}</b>" : ""));
            sb.AppendLine($"Cash: <b>${clean}</b> clean" + (dirty > 0 ? $" + <b>${dirty}</b> dirty in your coat" : ""));
            sb.AppendLine($"The street is <b>{streetWord}</b>. The outfit is <b>{outfitWord}</b>.");
            sb.AppendLine(talkCount == 0
                ? "As far as you know, nobody is carrying talk about you."
                : $"Talk you know about and haven't dealt with: <b>{talkCount}</b> — press L for your ledger.");
            // The street's own words — the strongest story the player KNOWS about
            // (belief, never ground truth), quoted verbatim from the mill.
            KnownLead word = null;
            foreach (var k in _game.Knowledge.Entries)
                if (!k.Handled && (word == null || k.ConfidenceWhenLearned > word.ConfidenceWhenLearned)) word = k;
            if (word != null)
                sb.AppendLine($"<i>Word on the street, as you heard it: \"{word.Summary}\" — and {word.HolderName} is telling it.</i>");
            _summaryText.text = sb.ToString();
            _summaryPanel.SetActive(true);
            _summaryUntil = Time.unscaledTime + 9f;
        }

        void RefreshLedger()
        {
            var sb = new System.Text.StringBuilder();
            int shown = 0;
            foreach (var k in _game.Knowledge.Entries)
            {
                if (shown++ >= 14) { sb.AppendLine("…"); break; }
                var status = k.Handled ? " <color=#8a8>· handled</color>" : "";
                sb.AppendLine($"<b>{k.HolderName}</b> — \"{k.Summary}\"");
                sb.AppendLine($"   <color=#999>learned day {k.LearnedAt.Day} ({k.Source})</color>{status}");
            }
            var text = shown == 0
                ? "Nothing yet. As far as you know, nobody is talking about you.\n\nYou learn what's out there by seeing who watches you, by loyal friends' warnings, and by what people admit to your face.\n"
                : sb.ToString();

            // The other side of the ledger: what you hold on THEM (§6.3).
            var held = new System.Text.StringBuilder();
            foreach (var s in _game.HooksBook.Known)
            {
                bool leashed = _game.Gossip != null && _game.Gossip.Mill != null &&
                               (_game.Gossip.Mill.Get(s.OwnerId)?.Leashed ?? false);
                var state = s.Strong
                    ? (leashed ? "<color=#c66>· held over them</color>" : "<color=#9c9>· standing</color>")
                    : (s.HookSpent ? "<color=#888>· favor spent</color>" : "<color=#9c9>· one favor owed</color>");
                held.AppendLine($"<b>{s.OwnerId}</b> — {s.Summary} {state}");
                held.AppendLine($"   <color=#999>learned day {s.LearnedAt.Day} (from {s.LearnedFrom})</color>");
            }
            _ledgerText.text = text + (held.Length > 0
                ? "\n<b>WHAT YOU HOLD</b>\n" + held
                : "");
        }

        void Update()
        {
            var now = _game.Now;
            var money = _game.Wallet.Dirty > 0
                ? $"${_game.Wallet.Clean} <color=#c96>+ ${_game.Wallet.Dirty} dirty</color>"
                : $"${_game.Wallet.Clean}";
            _clockText.text = $"Day {now.Day} — {now.Hour:D2}:{now.Minute:D2} ({now.Slot})  ·  {money}";

            // Campaign readout: the week, the street's mood, the outfit's patience —
            // in words, not meters. Cheap enough to refresh on a coarse cadence.
            if (Time.frameCount % 30 == 0 || _statusText.text.Length == 0)
            {
                var camp = _game.Campaign;
                double heat = _game.Gossip != null && _game.Gossip.Mill != null ? _game.Gossip.Mill.DayCircleHeat() : 0.0;
                _statusText.text = $"Day {Mathf.Min(now.Day, camp.SurviveDays)} of {camp.SurviveDays}" +
                    $"  ·  the street: {HeatWord(heat)}  ·  the outfit: {PatienceWord(camp.OutfitPatience)}" +
                    (_game.WearingCoat ? "  ·  <color=#c96>in the coat</color>" : "");
            }

            if (_toastUntil > 0f && Time.unscaledTime > _toastUntil) { _toastText.text = ""; _toastUntil = 0f; }

            if (_endPanel != null)
            {
                if (Input.GetKeyDown(KeyCode.R)) Restart();
                return; // the week is settled; only the end screen listens now
            }

            _nearest = NearestHostInRange();
            bool dialogueOpen = _dialoguePanel.activeSelf;
            _promptText.text = !dialogueOpen && _nearest != null
                ? $"Press E to talk to {_nearest.Card.Name}" : "";

            if (Input.GetKeyDown(KeyCode.E) && _nearest != null && !dialogueOpen && !_keyPanel.activeSelf)
                OpenDialogue(_nearest);
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                if (dialogueOpen) CloseDialogue();
                _keyPanel.SetActive(false);
                _debugPanel.SetActive(false);
            }
            if (Input.GetKeyDown(KeyCode.F1)) _debugPanel.SetActive(!_debugPanel.activeSelf);
            if (Input.GetKeyDown(KeyCode.F2)) _keyPanel.SetActive(!_keyPanel.activeSelf);
            // The Ledger — only while not typing into the dialogue box.
            if (Input.GetKeyDown(KeyCode.L) && !dialogueOpen && !_keyPanel.activeSelf)
            {
                _ledgerPanel.SetActive(!_ledgerPanel.activeSelf);
                if (_ledgerPanel.activeSelf) RefreshLedger();
            }
            if (_ledgerPanel.activeSelf && Time.frameCount % 30 == 0) RefreshLedger();
            if (_ledgerPanel.activeSelf && Input.GetKeyDown(KeyCode.Escape)) _ledgerPanel.SetActive(false);

            // The runner's coat — day face or night face, one key, never while typing.
            if (Input.GetKeyDown(KeyCode.C) && !dialogueOpen && !_keyPanel.activeSelf)
            {
                _game.WearingCoat = !_game.WearingCoat;
                Toast(_game.WearingCoat
                    ? "You pull on the runner's coat. Harder to name in the dark; harder to explain in daylight."
                    : "You shrug off the coat. Just the bar owner again.", 5f);
            }

            // Morning summary card: auto-fades, or Esc/click-through dismisses.
            if (_summaryPanel.activeSelf &&
                (Time.unscaledTime > _summaryUntil || Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.Return)))
                _summaryPanel.SetActive(false);

            // F1 shows the brain of whoever you're talking to (or standing near).
            var debugHost = _current ?? _nearest ?? (_hosts.Count > 0 ? _hosts[0] : null);
            if (_debugPanel.activeSelf && debugHost != null && Time.frameCount % 30 == 0)
                _debugText.text = debugHost.DebugReport() +
                    (_game.Gossip != null ? "\n\n" + _game.Gossip.StatusLine() : "");

            if (dialogueOpen && _input.isFocused && Input.GetKeyDown(KeyCode.Return))
                Submit();

            // Offer damage control only when the person you're talking to is actually
            // carrying talk about the player; refresh the payoff price as it entrenches.
            if (dialogueOpen && Time.frameCount % 30 == 0)
            {
                var lead = CurrentLead();
                _dcRow.SetActive(lead != null);
                if (lead != null)
                {
                    int price = BribePriceFor(lead);
                    _payLabel.text = _game.PlayerCash >= price ? $"Pay off (${price})" : $"Pay off (${price} — short)";
                    _payBtn.interactable = _game.PlayerCash >= price;
                    _leanLabel.text = "Lean on them";
                    _doubtLabel.text = "Plant doubt";
                }
            }
            else if (!dialogueOpen && _dcRow.activeSelf) _dcRow.SetActive(false);

            if (dialogueOpen && Time.frameCount % 30 == 0)
            {
                var hook = CurrentHostHook();
                _hookBtn.gameObject.SetActive(hook != null);
                if (hook != null)
                    _hookLabel.text = hook.Strong ? "Use what you know (they're yours)" : "Call in what you know (once)";
            }
            else if (!dialogueOpen && _hookBtn.gameObject.activeSelf) _hookBtn.gameObject.SetActive(false);

            _player.InputLocked = dialogueOpen || _keyPanel.activeSelf;
        }

        static string HeatWord(double h) => GameController.StreetWord(h);
        static string PatienceWord(double p) => GameController.OutfitWord(p);

        /// A short transient line at the top of the screen — takings banked, a job
        /// posted, a drop made. The campaign's voice outside of dialogue.
        public void Toast(string line, float seconds = 7f)
        {
            _toastText.text = line;
            _toastUntil = Time.unscaledTime + seconds;
        }

        /// The week is over, one way or another. Freezes play input and offers restart.
        public void ShowEnd(Campaign camp)
        {
            if (_endPanel != null) return;
            CloseDialogue();
            _player.InputLocked = true;
            _promptText.text = "";
            _dcRow.SetActive(false);

            _endPanel = MakePanel(_canvas, "EndPanel", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1100, 420));
            _endPanel.GetComponent<Image>().color = new Color(0.03f, 0.03f, 0.05f, 0.96f);
            bool won = camp.Verdict == Verdict.WonWeek;
            var title = MakeText(_endPanel.transform, "EndTitle", new Vector2(0.5f, 1), new Vector2(0, -50), new Vector2(1000, 70), 44, TextAnchor.UpperCenter);
            title.text = won ? "YOU LASTED THE WEEK"
                : camp.Verdict == Verdict.LostExposed ? "EXPOSED" : "CAST OUT";
            title.color = won ? new Color(0.75f, 0.9f, 0.7f) : new Color(0.9f, 0.55f, 0.45f);
            MakeText(_endPanel.transform, "EndReason", new Vector2(0.5f, 1), new Vector2(0, -150), new Vector2(950, 90), 22, TextAnchor.UpperCenter)
                .text = camp.VerdictReason;
            MakeText(_endPanel.transform, "EndStats", new Vector2(0.5f, 1), new Vector2(0, -250), new Vector2(950, 60), 18, TextAnchor.UpperCenter)
                .text = $"Drops made: {camp.JobsDone}   ·   missed: {camp.JobsMissed}   ·   takings banked: ${_game.TotalTakings}   ·   " +
                        $"washed: ${_game.Wallet.TotalWashed}   ·   cash: ${_game.Wallet.Clean} clean, ${_game.Wallet.Dirty} dirty";
            MakeText(_endPanel.transform, "EndHint", new Vector2(0.5f, 0), new Vector2(0, 30), new Vector2(950, 40), 20, TextAnchor.LowerCenter)
                .text = "Press R to start the week over";
        }

        void Restart()
        {
            // Restarting the week means renouncing its history: the save goes too.
            _game.DeleteSave();
            // The world is fully code-built, so a clean restart is: drop the
            // controller and UI, reload the scene, and let Bootstrap stand it back up.
            Destroy(_game.gameObject);
            Destroy(gameObject);
            UnityEngine.SceneManagement.SceneManager.LoadScene(
                UnityEngine.SceneManagement.SceneManager.GetActiveScene().buildIndex);
        }

        /// A confrontation opens itself — the NPC demands the conversation. Never
        /// interrupts an existing dialogue, the key prompt, or the end screen.
        public void ForceDialogue(ConversationHost host)
        {
            if (_dialoguePanel.activeSelf || _keyPanel.activeSelf || _endPanel != null) return;
            OpenDialogue(host);
        }

        void OpenDialogue(ConversationHost host)
        {
            _current = host;
            // A loyal-enough carrier admits what they hold the moment you sit down.
            var walker = host.GetComponent<NpcWalker>();
            _game.LearnFromHost(walker != null ? walker.DisplayName : host.Card.Name);
            _titleText.text = host.Card.Name;
            _dialoguePanel.SetActive(true);
            _input.text = "";
            _input.ActivateInputField();
            RenderHistory();
        }

        void CloseDialogue()
        {
            _dialoguePanel.SetActive(false);
            _current = null;
        }

        ConversationHost NearestHostInRange()
        {
            ConversationHost best = null;
            float bestDist = float.MaxValue;
            foreach (var h in _hosts)
            {
                if (h == null || !h.PlayerInRange(_player.transform)) continue;
                float d = Vector3.Distance(_player.transform.position, h.transform.position);
                if (d < bestDist) { bestDist = d; best = h; }
            }
            return best;
        }

        List<string> HistoryOf(ConversationHost host)
        {
            if (!_histories.TryGetValue(host, out var list)) { list = new List<string>(); _histories[host] = list; }
            return list;
        }

        async void Submit()
        {
            var host = _current;
            if (host == null) return;
            var text = _input.text.Trim();
            if (text.Length == 0 || _waiting) return;
            _input.text = "";
            _input.ActivateInputField();

            var history = HistoryOf(host);
            var name = host.Card.Name;
            history.Add($"<b>You:</b> {text}");
            history.Add($"<i>{name} is thinking...</i>");
            RenderHistory();

            _waiting = true;
            var reply = await host.SayAsync(text); // Unity's context resumes this on the main thread
            _waiting = false;

            history.RemoveAt(history.Count - 1);
            history.Add($"<b>{name}:</b> {reply}");
            RenderHistory();
        }

        // ---- damage control ----

        /// The strongest lead the player BELIEVES the NPC this dialogue is with is
        /// carrying, or null. A belief snapshot — possibly stale, never ground truth.
        KnownLead CurrentLead()
        {
            // Belief, not ground truth (design-doc §6.2): the verbs key off what the
            // player has LEARNED this NPC is carrying, not the live network state.
            if (_current == null) return null;
            var walker = _current.GetComponent<NpcWalker>();
            var id = walker != null ? walker.DisplayName : _current.Card.Name;
            return _game.Knowledge.StrongestFor(id);
        }

        int BribePriceFor(KnownLead known)
        {
            // The carrier quotes their real price when asked — that's not omniscience,
            // it's a negotiation. A dead rumor prices from the stale snapshot instead.
            double live = _game.Gossip.Mill.BribePrice(known.HolderId, known.TopicKey);
            if (live > 0) return Mathf.CeilToInt((float)live);
            var mill = _game.Gossip.Mill;
            return Mathf.CeilToInt((float)(mill.BribeBase + mill.BribePerConfidence * known.ConfidenceWhenLearned));
        }

        /// The belief was stale — whatever they were carrying has already died down.
        bool ResolveStale(KnownLead known, DcResult result)
        {
            if (result.Outcome != DcOutcome.NoSuchRumor) return false;
            _game.Knowledge.MarkHandled(known.HolderId, known.TopicKey);
            Narrate("Whatever they were saying, it seems to have died down on its own.");
            return true;
        }

        void PayOff()
        {
            var known = CurrentLead();
            if (known == null) return;
            var mill = _game.Gossip.Mill;
            int price = BribePriceFor(known);
            // Bribes are the one place dirty money spends like clean — criminals take it.
            if (_game.PlayerCash < price)
            {
                Narrate($"You'd need ${price}. You have ${_game.PlayerCash}.");
                return;
            }
            var result = mill.Bribe(known.HolderId, known.TopicKey, price, _game.Now);
            if (ResolveStale(known, result)) return;
            // Money only changes hands if they actually take it.
            if (result.Outcome == DcOutcome.Contained)
            {
                _game.Wallet.Spend(price, dirtyOk: true);
                _game.Knowledge.MarkHandled(known.HolderId, known.TopicKey);
            }
            Narrate(result.Message + (result.Outcome == DcOutcome.Contained ? $" (-${price})" : ""));
        }

        void LeanOn()
        {
            var known = CurrentLead();
            if (known == null) return;
            var result = _game.Gossip.Mill.Intimidate(known.HolderId, known.TopicKey, _game.Now);
            if (ResolveStale(known, result)) return;
            if (result.Outcome == DcOutcome.Contained) _game.Knowledge.MarkHandled(known.HolderId, known.TopicKey);
            Narrate(result.Message);
        }

        string CurrentHostId()
        {
            if (_current == null) return null;
            var walker = _current.GetComponent<NpcWalker>();
            return walker != null ? walker.DisplayName : _current.Card.Name;
        }

        Secret CurrentHostHook()
        {
            var id = CurrentHostId();
            if (id == null) return null;
            var hook = _game.HooksBook.UsableHook(id);
            // A leash already applied needs no button — it's standing.
            if (hook != null && hook.Strong && (_game.Gossip.Mill.Get(id)?.Leashed ?? false)) return null;
            return hook;
        }

        void UseHook()
        {
            var id = CurrentHostId();
            var hook = CurrentHostHook();
            if (id == null || hook == null) return;
            var result = _game.Gossip.Mill.UseHook(id, hook, _game.Now);
            // Keep the player's ledger honest: a favor silences one story (the mill
            // says which); a leash silences the person — everything they hold is dealt with.
            if (result.Outcome == DcOutcome.Contained)
            {
                if (hook.Strong)
                    foreach (var k in _game.Knowledge.Entries)
                    { if (k.HolderId == id) _game.Knowledge.MarkHandled(k.HolderId, k.TopicKey); }
                else if (result.ContainedTopic != null)
                    _game.Knowledge.MarkHandled(id, result.ContainedTopic);
            }
            Narrate(result.Message);
        }

        void PlantDoubt()
        {
            var known = CurrentLead();
            if (known == null) return;
            var result = _game.Gossip.Mill.Discredit(known.TopicKey, null, _game.Now);
            if (result.Outcome == DcOutcome.Contained || result.Outcome == DcOutcome.AlreadyDenied)
                _game.Knowledge.MarkHandled(known.HolderId, known.TopicKey);
            Narrate(result.Message);
        }

        void Narrate(string line)
        {
            if (_current == null) return;
            HistoryOf(_current).Add($"<i>{line}</i>");
            RenderHistory();
        }

        void RenderHistory()
        {
            if (_current == null) { _historyText.text = ""; return; }
            var history = HistoryOf(_current);
            int start = Mathf.Max(0, history.Count - 10);
            var sb = new System.Text.StringBuilder();
            for (int i = start; i < history.Count; i++) sb.AppendLine(history[i]);
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
