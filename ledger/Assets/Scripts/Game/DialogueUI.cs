using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Ledger.Game
{
    /// All UI for M0, constructed from code: HUD clock, talk prompt, the
    /// conversation window, first-run API key entry (F2), and the debug
    /// "Ledger" panel (F1) showing memory/suspicion/cost live.
    public partial class DialogueUI : MonoBehaviour
    {
        GameController _game;
        PlayerController _player;
        List<ConversationHost> _hosts;
        ConversationHost _current;  // who the open dialogue is with
        ConversationHost _nearest;  // who is in talk range right now

        Font _font;
        Transform _canvas;
        /// So the Fall can stage itself rather than announce itself.
        public Transform CanvasRoot => _canvas;
        Text _clockText;
        Text _statusText;
        Text _toastText;
        float _toastUntil;
        GameObject _endPanel;
        Text _promptText;
        float _promptAlpha;
        /// Both from Ledger.Core, both tested there. A key pressed just before
        /// an action becomes legal still counts, and a prompt survives a step
        /// out of range.
        readonly InputBuffer _talkBuffer = new InputBuffer();
        readonly Forgiveness _grace = new Forgiveness();
        /// The coat takes a moment to go on, and that moment is legible.
        readonly VerbBeat _coatVerb = new VerbBeat
        {
            AnticipationSeconds = 0.35, ConsequenceSeconds = 0.5, RecoverySeconds = 0.25,
        };

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
        Button _collectBtn, _forgiveBtn;

        // Suggestion chips (player decision 2026-07-26): 2–3 contextual openers
        // drawn from live state. Clicking one says it; typing stays the game.
        GameObject _chipRow;
        readonly Button[] _chipBtns = new Button[3];
        readonly Text[] _chipLabels = new Text[3];
        readonly string[] _chipSays = new string[3];

        // PP7: the posture question, asked over the won week (act1-draft.md).
        GameObject _posturePanel;

        // The pause menu (production track P1): the game used to have no way
        // out of itself.
        GameObject _pausePanel;
        bool _paused;

        void TogglePause()
        {
            if (SimMode.Days > 0) return;
            _paused = !_paused;
            if (_pausePanel == null) BuildPausePanel();
            _pausePanel.SetActive(_paused);
            Time.timeScale = _paused ? 0f : 1f;
            _player.InputLocked = _paused;
            Audio.Ui("page");
        }

        void BuildPausePanel()
        {
            _pausePanel = MakePanel(_canvas, "Pause", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(520, 540));
            var t = MakeText(_pausePanel.transform, "PauseTitle", new Vector2(0.5f, 1), new Vector2(0, -24), new Vector2(460, 36), 24, TextAnchor.UpperCenter);
            t.text = "P A U S E D";
            t.color = UiTheme.Dim;

            var resume = MakeButton(_pausePanel.transform, "Resume", new Vector2(0.5f, 1), new Vector2(0, -100), new Vector2(320, 48));
            resume.onClick.AddListener(TogglePause);

            var save = MakeButton(_pausePanel.transform, "Save now", new Vector2(0.5f, 1), new Vector2(0, -158), new Vector2(320, 48));
            save.onClick.AddListener(() => { _game.SaveNow(); Audio.Ui("coin"); });

            // P2: a manual copy in a rotating drawer — snapshot before a risky
            // night, reopen it from the main menu if the night goes wrong.
            var copy = MakeButton(_pausePanel.transform, "Keep a copy", new Vector2(0.5f, 1), new Vector2(0, -216), new Vector2(320, 48));
            copy.onClick.AddListener(() => { _game.SaveToSlot(SaveSlots.NextSlot()); Audio.Ui("coin"); });

            var menu = MakeButton(_pausePanel.transform, "Save and quit to menu", new Vector2(0.5f, 1), new Vector2(0, -274), new Vector2(320, 48));
            menu.onClick.AddListener(() =>
            {
                _game.SaveNow(quiet: true);
                Time.timeScale = 1f;
                Destroy(_game.gameObject);
                Destroy(gameObject);
                MainMenu.Create();
            });

            // Options, reachable mid-game at last. Before this the only way to
            // change text size, sensitivity, volume or a keybinding was to quit
            // to the main menu, which fails the plainest expectation anybody has
            // of a pause screen.
            var options = MakeButton(_pausePanel.transform, "Options", new Vector2(0.5f, 1), new Vector2(0, -332), new Vector2(320, 48));
            options.onClick.AddListener(() =>
            {
                _pausePanel.SetActive(false);
                OptionsScreen.Show(() => { if (_pausePanel != null) _pausePanel.SetActive(true); });
            });

            var quit = MakeButton(_pausePanel.transform, "Save and quit to desktop", new Vector2(0.5f, 1), new Vector2(0, -390), new Vector2(320, 48));
            quit.onClick.AddListener(() => { _game.SaveNow(quiet: true); MainMenu.Quit(); });

            MakeText(_pausePanel.transform, "PauseHint", new Vector2(0.5f, 0), new Vector2(0, 26), new Vector2(460, 30), 15, TextAnchor.LowerCenter)
                .text = "The city keeps its state. Everything you did is in the save.";
        }

        // Empire v1: two context-sensitive verbs — the money route and the
        // leverage route — living above the hook/debt row while talking to
        // someone the other ledger has business with.
        Button _empireBtnA, _empireBtnB;
        Button _empireBtnC;   // the Table's third answer — defy is never gated (audit 2026-07-27)
        Text _empireLabelC;
        Text _empireLabelA, _empireLabelB;

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
            _font = UiTheme.LoadFont();

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
            // The street layer: sodium amber on the world HUD, cold ink in the books.
            _clockText = MakeText(canvasGo.transform, "Clock", new Vector2(1, 1), new Vector2(-20, -20), new Vector2(360, 40), 26, TextAnchor.UpperRight);
            _statusText = MakeText(canvasGo.transform, "Status", new Vector2(1, 1), new Vector2(-20, -54), new Vector2(640, 30), 18, TextAnchor.UpperRight);
            _statusText.color = UiTheme.Dim;
            _toastText = MakeText(canvasGo.transform, "Toast", new Vector2(0.5f, 1), new Vector2(0, -60), new Vector2(1000, 36), 21, TextAnchor.MiddleCenter);
            _toastText.color = UiTheme.AmberSoft;
            _promptText = MakeText(canvasGo.transform, "Prompt", new Vector2(0.5f, 0), new Vector2(0, 60), new Vector2(800, 36), 22, TextAnchor.MiddleCenter);
            _promptText.color = UiTheme.Amber;
            var help = MakeText(canvasGo.transform, "Help", new Vector2(0, 1), new Vector2(20, -20), new Vector2(700, 32), 16, TextAnchor.UpperLeft);
            help.text = "WASD move    Shift run    E talk    C coat    L ledger    J plan    T phone    F car    F2 key    Esc close";
            help.color = UiTheme.Dim;

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
            _titleText.color = UiTheme.Amber; // a person, not a page — street warmth
            _historyText = MakeText(_dialoguePanel.transform, "History", new Vector2(0.5f, 1), new Vector2(0, -50), new Vector2(860, 280), 18, TextAnchor.LowerLeft);

            // The placeholder is the only onboarding the router gets: a player who
            // never learns they can say the thing instead of hunting for its button
            // is playing a smaller game than the one we built.
            _input = MakeInput(_dialoguePanel.transform, "Say something — or say what you want to do...", new Vector2(0.5f, 0), new Vector2(-60, 18), new Vector2(720, 44));
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

            // Mickey's book: collection is a conversation, not a fight.
            _collectBtn = MakeButton(_dialoguePanel.transform, "Collect the debt", new Vector2(0.5f, 0), new Vector2(-250, 112), new Vector2(220, 36));
            _forgiveBtn = MakeButton(_dialoguePanel.transform, "Tear out the page", new Vector2(0.5f, 0), new Vector2(250, 112), new Vector2(220, 36));
            _collectBtn.onClick.AddListener(CollectDebt);
            _forgiveBtn.onClick.AddListener(ForgiveDebt);
            _collectBtn.gameObject.SetActive(false);
            _forgiveBtn.gameObject.SetActive(false);

            _empireBtnA = MakeButton(_dialoguePanel.transform, "", new Vector2(0.5f, 0), new Vector2(-250, 152), new Vector2(300, 36));
            _empireBtnB = MakeButton(_dialoguePanel.transform, "", new Vector2(0.5f, 0), new Vector2(250, 152), new Vector2(300, 36));
            _empireLabelA = _empireBtnA.GetComponentInChildren<Text>();
            _empireLabelB = _empireBtnB.GetComponentInChildren<Text>();
            _empireLabelA.fontSize = UiTheme.Scaled(16);
            _empireLabelB.fontSize = UiTheme.Scaled(16);
            _empireBtnC = MakeButton(_dialoguePanel.transform, "", new Vector2(0.5f, 0), new Vector2(250, 192), new Vector2(300, 36));
            _empireLabelC = _empireBtnC.GetComponentInChildren<Text>();
            _empireLabelC.fontSize = UiTheme.Scaled(16);
            _empireBtnA.onClick.AddListener(() => EmpireAct(false));
            _empireBtnB.onClick.AddListener(() => EmpireAct(true));
            _empireBtnC.onClick.AddListener(EmpireActThird);
            _empireBtnA.gameObject.SetActive(false);
            _empireBtnB.gameObject.SetActive(false);
            _empireBtnC.gameObject.SetActive(false);

            // Chips float just above the panel, out of the history's way.
            _chipRow = new GameObject("Chips");
            _chipRow.transform.SetParent(_dialoguePanel.transform, false);
            Place(_chipRow, new Vector2(0.5f, 1), new Vector2(0, 42), new Vector2(880, 36));
            for (int i = 0; i < 3; i++)
            {
                int idx = i;
                var anchor = i == 0 ? new Vector2(0, 0.5f) : i == 1 ? new Vector2(0.5f, 0.5f) : new Vector2(1, 0.5f);
                _chipBtns[i] = MakeButton(_chipRow.transform, "", anchor, Vector2.zero, new Vector2(286, 32));
                _chipLabels[i] = _chipBtns[i].GetComponentInChildren<Text>();
                _chipLabels[i].fontSize = UiTheme.Scaled(15);
                _chipLabels[i].fontStyle = FontStyle.Italic;
                _chipLabels[i].color = UiTheme.Dim;
                _chipBtns[i].onClick.AddListener(() => SayChip(idx));
            }
            _chipRow.SetActive(false);

            _dialoguePanel.SetActive(false);
        }

        /// The other ledger's verbs for whoever you're talking to. A = the money
        /// route (buy clean / buy the marker / turn the key / sort their need /
        /// put them on a round), B = the leverage route (a usable secret spent
        /// on a shop or a recruitment). Empire opens with the city (day 8).
        void RefreshEmpireButtons()
        {
            var id = CurrentHostId();
            _empireSayA = _empireSayB = null;   // the router reads these; never stale
            _empireBtnC.gameObject.SetActive(false);   // only the Table uses it
            if (id == null || !_game.Campaign.OpenMode)
            {
                _empireBtnA.gameObject.SetActive(false);
                _empireBtnB.gameObject.SetActive(false);
                return;
            }
            var e = _game.Empire;
            string labelA = null, labelB = null;
            bool enabledA = true;

            // Act III outranks everything, because during the audit these people
            // are only one thing to you. Each verb appears in front of exactly
            // the person it costs something with — never on a menu.
            if (ActThreeButtons(id)) return;

            var act2 = _game.ActTwo;

            // The machine's letter (PP2): while the licence hangs, Hal is
            // the man who deals with paper — both of the letter's named options
            // live in front of him. These verbs existed only as words on the
            // letter before (audit 2026-07-27): InjunctionAnswered had no
            // setter and the fee was never charged.
            if (id == "Hal" && act2.Pp2Fired && act2.BarFrozen(_game.Now))
            {
                _empireBtnA.gameObject.SetActive(true);
                _empireLabelA.text = $"Pay the fees properly (${ActTwoState.InjunctionFee})";
                _empireBtnA.interactable = _game.Wallet.Clean >= ActTwoState.InjunctionFee;
                _empireBtnB.gameObject.SetActive(true);
                _empireLabelB.text = $"Have him make it disappear (${ActTwoState.InjunctionFee * 2})";
                _empireBtnB.interactable = _game.Wallet.Total >= ActTwoState.InjunctionFee * 2;
                _empireSayA = "pay the licence fees properly, clean money, stamped receipt";
                _empireSayB = "pay Hal to make the licence review disappear";
                return;
            }

            // Hal's brokerage (Act II PP5): reads, truces, and the room.
            if (id == "Hal" && act2.Pp5Fired)
            {
                labelA = $"Buy a read (${ActTwoState.ReadPrice})";
                enabledA = _game.Wallet.Total >= ActTwoState.ReadPrice;
                labelB = act2.TruceSpent ? "A truce, again (he declines)" : $"Broker a truce (${ActTwoState.TrucePrice})";
                _empireSayA = "pay him to tell you where you stand with the three arms";
                _empireSayB = "pay him to buy you peace with whoever is worst";
                _empireBtnA.gameObject.SetActive(true);
                _empireLabelA.text = labelA;
                _empireBtnA.interactable = enabledA;
                _empireBtnB.gameObject.SetActive(true);
                _empireLabelB.text = labelB;
                _empireBtnB.interactable = !act2.TruceSpent && _game.Wallet.Total >= ActTwoState.TrucePrice;
                return;
            }

            // The Table (PP7): the head is in the room and wants an answer.
            if (act2.TableArmId != null && !act2.TableFired
                && _game.Empire.ArmOf(act2.TableArmId)?.HeadName == _current.Card.Name)
            {
                // act2-draft PP7: "Accept, defy, or counter with leverage."
                // Defy is NEVER gated; counter appears only with the standing
                // to back it. Two buttons used to compress this to two verbs,
                // making defy unreachable exactly when the player had earned
                // the third option (audit 2026-07-27).
                _empireBtnA.gameObject.SetActive(true);
                _empireLabelA.text = "Take the terms";
                _empireBtnA.interactable = true;
                bool canCounter = _game.Empire.ArmOf(act2.TableArmId).Standing >= 0.5;
                _empireBtnB.gameObject.SetActive(true);
                _empireLabelB.text = "Refuse them";
                _empireBtnB.interactable = true;
                _empireSayA = "accept the terms they are putting to you";
                _empireSayB = "refuse their terms outright";
                if (canCounter)
                {
                    _empireBtnC.gameObject.SetActive(true);
                    _empireLabelC.text = "Name your own number";
                    _empireBtnC.interactable = true;
                }
                return;
            }

            var biz = FindBusinessOf(id);
            var hook = _game.HooksBook.UsableHook(id);
            if (biz != null)
            {
                if (biz.DebtHeld) { labelA = "Turn the key (you hold the paper)"; _empireSayA = $"call in the paper you hold and take the {biz.Name}"; }
                else if (_game.Wallet.Clean >= biz.AskPrice) { labelA = $"Buy the {biz.Name} (${biz.AskPrice} clean)"; _empireSayA = $"buy the {biz.Name} outright with clean money"; }
                else if (biz.DebtPrice > 0) { labelA = $"Buy their marker (${biz.DebtPrice})"; _empireSayA = $"buy up the debt the {biz.Name} owes elsewhere"; }
                else { labelA = $"Buy the {biz.Name} (${biz.AskPrice} — short)"; enabledA = false; }
                if (hook != null) { labelB = $"Take the {biz.Name} (what you know)"; _empireSayB = $"use what you know on them to take the {biz.Name}"; }
            }
            else
            {
                var crew = e.CrewOf(id);
                if (crew != null && crew.Assignment == null)
                {
                    var open = e.Rackets.Find(r => !r.Established &&
                        (r.RequiresBusinessId == null || (e.BusinessOf(r.RequiresBusinessId)?.Owned ?? false)));
                    if (open != null) { labelA = $"Put them on the {open.Name}"; _empireSayA = $"put them to work running the {open.Name}"; }
                }
                else if (crew != null && crew.Assignment != null)
                {
                    // §6.5 daily: how you split their take. Cycles on click.
                    labelA = crew.Cut == "fair" ? "Their cut: fair (change)"
                        : crew.Cut == "generous" ? "Their cut: generous (change)"
                        : "Their cut: skimmed (change)";
                    _empireSayA = "change how much of the take they keep";
                }
                // Somebody the Director had ask you for money (roadmap M8).
                // Outranks everything else for the same reason the supplier does:
                // they are standing there with a figure in their head.
                else if (_game.DemandFrom(id) is GameController.OpenDemand asked)
                {
                    labelA = $"Give {id} the ${asked.Amount}";
                    enabledA = _game.PlayerCash >= asked.Amount;
                    _empireSayA = $"pay {id} the ${asked.Amount} they asked you for";
                }
                // A supplier you owe, or one who has stopped coming (roadmap M7).
                // Settling up outranks recruiting: the man is standing there with
                // a figure in his head and it is the only thing he wants to discuss.
                else if (_game.OutstandingSupplier(id) is Supplier owed)
                {
                    labelA = owed.Refusing ? $"Make it right with {owed.Name}" : $"Settle what you owe {owed.Name}";
                    _empireSayA = owed.Refusing
                        ? $"pay {owed.Name} whatever it takes to start bringing {owed.Goods} again"
                        : $"pay {owed.Name} the money you owe him for {owed.Goods}";
                }
                else if (crew == null && _game.TryNeedOf(id, out var cost, out _))
                {
                    labelA = $"Sort what they need (${cost})";
                    enabledA = _game.Wallet.Total >= cost;
                    _empireSayA = "pay for the thing they need, so they owe you and come to work for you";
                    if (hook != null) { labelB = "Bring them in (what you know)"; _empireSayB = "use what you know on them so they come to work for you"; }
                }
            }

            _empireBtnA.gameObject.SetActive(labelA != null);
            if (labelA != null) { _empireLabelA.text = labelA; _empireBtnA.interactable = enabledA; }
            _empireBtnB.gameObject.SetActive(labelB != null);
            if (labelB != null) _empireLabelB.text = labelB;
        }

        Business FindBusinessOf(string ownerId)
        {
            foreach (var b in _game.Empire.Businesses)
                if (b.OwnerId == ownerId && !b.Owned) return b;
            return null;
        }

        /// The audit's three verbs, shown to the three people they belong to.
        /// Returns true when Act III has claimed the buttons.
        bool ActThreeButtons(string id)
        {
            var a3 = _game.ActThree;
            if (!a3.Opened || a3.AuditClosed) return false;
            var e = _game.Empire;

            // Reese. Nothing to buy and nothing to threaten — the only thing on
            // offer is how much of the business he reads.
            if (id == ActThreeState.InspectorName)
            {
                _empireBtnA.gameObject.SetActive(true);
                _empireLabelA.text = "Fetch him what he asked for";
                _empireBtnA.interactable = _game.InspectorWaiting;
                _empireSayA = "go and get the record he has asked for and put it in front of him";
                _empireBtnB.gameObject.SetActive(true);
                _empireLabelB.text = "Tell him to put it in writing";
                _empireBtnB.interactable = _game.InspectorWaiting;
                _empireSayB = "tell him to submit the request in writing";
                return true;
            }

            // Hal: the way out. A bad price, and he does not ask why.
            if (id == "Hal" && !a3.SoldUp
                && (e.Businesses.Exists(b => b.Owned) || e.Rackets.Exists(r => r.Established)))
            {
                _empireBtnA.gameObject.SetActive(true);
                _empireLabelA.text = "Sell up, pay everyone off";
                _empireBtnA.interactable = true;
                _empireSayA = "have him sell everything you own and settle with everyone, whatever it costs";
                _empireBtnB.gameObject.SetActive(_game.ActTwo.Pp5Fired);
                _empireLabelB.text = $"Buy a read (${ActTwoState.ReadPrice})";
                _empireBtnB.interactable = _game.Wallet.Total >= ActTwoState.ReadPrice;
                _empireSayB = "pay him to tell you where you stand with the three arms";
                return true;
            }

            // Ellis: point it elsewhere. Only offered once she has asked, and
            // only if somebody actually told you something worth giving her.
            if (id == "Ellis" && a3.Pp3Fired && !a3.Deflected && !a3.SoldUp)
            {
                _empireBtnA.gameObject.SetActive(true);
                _empireLabelA.text = "Give her the arm";
                _empireBtnA.interactable = _game.EllisInterviews.Count > 0;
                _empireSayA = "give her the organization that has been hardest on you, with enough to make it stick";
                _empireBtnB.gameObject.SetActive(false);
                return true;
            }

            // The successor: the only ending you have to reach for.
            if (a3.SuccessorId == null && a3.Pp4Fired)
            {
                var ready = _game.ReadySuccessor();
                if (ready != null && ready.Id == id)
                {
                    _empireBtnA.gameObject.SetActive(true);
                    _empireLabelA.text = "Sign it over to them";
                    _empireBtnA.interactable = true;
                    _empireSayA = "sign the whole thing over to them and go";
                    _empireBtnB.gameObject.SetActive(false);
                    return true;
                }
            }

            // PP5, the last day. Offered last so it never covers a bigger verb,
            // and offered to whoever you actually managed to reach — in person
            // or on the line, which is the whole design of the scene.
            var lastDay = _game.LastDayOffer(id);
            if (lastDay != null)
            {
                _empireBtnA.gameObject.SetActive(true);
                _empireLabelA.text = lastDay;
                _empireBtnA.interactable = true;
                _empireSayA = "say the thing there is still time to say";
                _empireBtnB.gameObject.SetActive(false);
                return true;
            }
            return false;
        }

        /// The matching half of ActThreeButtons. Same order, same conditions —
        /// so what the button says and what it does cannot drift apart.
        bool ActThreeAct(string id, bool leverage)
        {
            var a3 = _game.ActThree;
            if (!a3.Opened || a3.AuditClosed) return false;
            var e = _game.Empire;

            if (id == ActThreeState.InspectorName)
            {
                if (!_game.AnswerInspector(cooperate: !leverage))
                    Narrate("\"I have what I need for today,\" Reese says, and goes back to it.");
                return true;
            }

            if (id == "Hal" && !a3.SoldUp
                && (e.Businesses.Exists(b => b.Owned) || e.Rackets.Exists(r => r.Established)))
            {
                if (!leverage) _game.SellUp();
                else BuyHalvardRead();
                return true;
            }

            if (id == "Ellis" && a3.Pp3Fired && !a3.Deflected && !a3.SoldUp)
            {
                if (!leverage && !_game.Deflect())
                    Narrate("\"I need something to point at,\" she says. \"You have not given me a name that anybody would stand behind.\"");
                return true;
            }

            if (a3.SuccessorId == null && a3.Pp4Fired)
            {
                var ready = _game.ReadySuccessor();
                if (ready != null && ready.Id == id) { if (!leverage) _game.HandOver(id); return true; }
            }

            if (_game.LastDayOffer(id) != null)
            {
                // The "no time for another" line lands as the CODA of the final
                // call — its old site required SpendLastDay to fail while the
                // offer existed in the same frame, which is impossible, so the
                // authored line had never displayed (audit 2026-07-27).
                if (!leverage && _game.SpendLastDay(id) && _game.ActThree.LastDayLeft <= 0)
                    Narrate(ActThreeState.LastDaySpentText);
                return true;
            }
            return false;
        }

        void BuyHalvardRead()
        {
            var e = _game.Empire;
            if (!_game.ActTwo.Pp5Fired) return;
            if (!_game.Wallet.Spend(ActTwoState.ReadPrice, dirtyOk: true)) { Narrate("He names the price again, patiently."); return; }
            _game.ActTwo.ReadsBought++;
            var loudest = e.Arms[0];
            foreach (var a in e.Arms) if (a.Attention > loudest.Attention) loudest = a;
            Narrate($"\"One imagines,\" Hal says to the counter, \"that {loudest.HeadName}'s people are " +
                $"{(loudest.Stage >= 4 ? "finished deliberating" : loudest.Stage >= 3 ? "reaching for what is yours" : loudest.Stage >= 2 ? "pricing you weekly" : "merely curious")}. " +
                "One imagines nothing else.\"");
        }

        /// The Table's counter — the one verb that needed a third button.
        void EmpireActThird()
        {
            var id = CurrentHostId();
            if (id == null) return;
            var act2 = _game.ActTwo;
            if (act2.TableArmId != null && !act2.TableFired
                && _game.Empire.ArmOf(act2.TableArmId)?.HeadName == _current.Card.Name)
                _game.AnswerTable("counter");
        }

        void EmpireAct(bool leverage)
        {
            var id = CurrentHostId();
            if (id == null) return;
            var e = _game.Empire;
            var g = _game.Gossip.Mill.Get(id);
            var act2 = _game.ActTwo;

            if (ActThreeAct(id, leverage)) return;

            if (id == "Hal" && act2.Pp2Fired && act2.BarFrozen(_game.Now))
            {
                if (!leverage)
                {
                    // Official fees want clean money — a licensing office is the
                    // one counter in this city where the other kind is a risk.
                    if (!_game.Wallet.Spend(ActTwoState.InjunctionFee, dirtyOk: false))
                    { Narrate("\"The office wants clean notes,\" Hal says, without looking up. \"They always do.\""); return; }
                    act2.InjunctionAnswered = true;
                    Narrate("Hal walks the fees over himself, before lunch. The stamp is dated the day the letter was. " +
                        "\"Paper answers paper,\" he says. The till runs again by evening.");
                }
                else
                {
                    if (!_game.Wallet.Spend(ActTwoState.InjunctionFee * 2, dirtyOk: true))
                    { Narrate("He does not repeat the figure."); return; }
                    act2.InjunctionAnswered = true;
                    Narrate("Hal folds the letter into his coat. Two days later it has never existed — no file, no fee, " +
                        "no review. Nobody at the machine's counter remembers signing anything.");
                }
                return;
            }

            if (id == "Hal" && act2.Pp5Fired)
            {
                if (!leverage)
                {
                    if (!_game.Wallet.Spend(ActTwoState.ReadPrice, dirtyOk: true)) { Narrate("He names the price again, patiently."); return; }
                    act2.ReadsBought++;
                    var loudest = e.Arms[0];
                    foreach (var a in e.Arms) if (a.Attention > loudest.Attention) loudest = a;
                    Narrate($"\"One imagines,\" Hal says to the counter, \"that {loudest.HeadName}'s people are " +
                        $"{(loudest.Stage >= 4 ? "finished deliberating" : loudest.Stage >= 3 ? "reaching for what is yours" : loudest.Stage >= 2 ? "pricing you weekly" : "merely curious")}. " +
                        "One imagines nothing else.\"");
                }
                else
                {
                    if (act2.TruceSpent) { Narrate("\"A person may buy peace once a season,\" he says. \"Not twice.\""); return; }
                    if (!_game.Wallet.Spend(ActTwoState.TrucePrice, dirtyOk: true)) { Narrate("He does not repeat the figure."); return; }
                    act2.TruceSpent = true;
                    var worst = e.Arms[0];
                    foreach (var a in e.Arms) if (a.Attention > worst.Attention) worst = a;
                    worst.Attention = System.Math.Max(0, worst.Attention - ActTwoState.TruceRelief);
                    Narrate($"Hal writes nothing down. Within a day, {worst.HeadName}'s people have other things to look at.");
                }
                return;
            }

            if (act2.TableArmId != null && !act2.TableFired
                && e.ArmOf(act2.TableArmId)?.HeadName == _current.Card.Name)
            {
                _game.AnswerTable(!leverage ? "accept" : "defy");
                return;
            }

            var biz = FindBusinessOf(id);
            var hook = _game.HooksBook.UsableHook(id);

            // Answering a demand (roadmap M8) and settling with a supplier
            // (M7) — the SAME ordering as the label logic above, so what the
            // button says and what it does cannot drift apart.
            if (biz == null && _game.DemandFrom(id) != null && !leverage)
            {
                _game.SettleDemand(id, out var demandLine);
                if (demandLine != null) Narrate(demandLine);
                return;
            }

            var supplierOwed = biz == null && _game.DemandFrom(id) == null
                ? _game.OutstandingSupplier(id) : null;
            if (supplierOwed != null && !leverage)
            {
                _game.SettleSupplier(supplierOwed.Id, out var settleLine);
                if (settleLine != null) Narrate(settleLine);
                return;
            }

            if (biz != null)
            {
                if (leverage && hook != null)
                {
                    Narrate(e.AcquireViaHook(biz, hook, g, _game.Now).Message);
                }
                else if (biz.DebtHeld)
                {
                    Narrate(e.Squeeze(biz, g, _game.Gossip.Mill, _game.Now).Message);
                }
                else if (_game.Wallet.Clean >= biz.AskPrice)
                {
                    Narrate(e.BuyClean(biz, _game.Wallet, g, _game.Now)
                        ? $"Papers, a handshake, ${biz.AskPrice} clean. The {biz.Name} is yours, and {id} still runs the counter."
                        : "The clean route needs clean money. All of it.");
                }
                else if (biz.DebtPrice > 0)
                {
                    Narrate(e.BuyDebt(biz, _game.Wallet)
                        ? $"You buy {id}'s paper for ${biz.DebtPrice}. What you do with it is tomorrow's question."
                        : "You can't cover the marker.");
                }
                return;
            }

            var crew = e.CrewOf(id);
            if (crew != null && crew.Assignment == null)
            {
                var open = e.Rackets.Find(r => !r.Established &&
                    (r.RequiresBusinessId == null || (e.BusinessOf(r.RequiresBusinessId)?.Owned ?? false)));
                if (open != null && e.Establish(open, crew, _game.Now))
                    Narrate($"{id} nods once. The {open.Name} is theirs from tonight.");
                return;
            }
            if (crew != null && crew.Assignment != null)
            {
                var next = crew.Cut == "fair" ? "generous" : crew.Cut == "generous" ? "skim" : "fair";
                e.SetCut(crew, next, _game.Gossip.Mill, _game.Now);
                Narrate(next == "generous" ? $"You bump {id}'s cut without being asked. They notice things like that."
                    : next == "skim" ? $"You start shorting {id}'s envelope. Free money, on a fuse."
                    : $"Back to the standard split with {id}. Fair is fair.");
                return;
            }
            if (leverage && hook != null && g != null)
            {
                Narrate(e.RecruitByHook(g, hook, _game.Now)
                    ? $"{id} goes quiet, then nods. They work for you now — because they must."
                    : "That lever doesn't move them.");
                return;
            }
            if (_game.TryNeedOf(id, out var cost, out var line) && g != null)
            {
                bool joined = e.RecruitByNeed(g, id, cost, _game.Wallet, _game.Now);
                Narrate($"{line} (-${cost})" + (joined
                    ? $" {id} is with you now — by choice."
                    : $" {id} owes you, and knows it. Not a yes. Yet."));
            }
        }

        // What has already been asked of each person, so a chip never offers
        // the same opener twice (playtest 2026-07-28).
        readonly Dictionary<string, HashSet<string>> _asked = new Dictionary<string, HashSet<string>>();

        HashSet<string> AskedOf(string id)
        {
            if (id == null) return new HashSet<string>();
            if (!_asked.TryGetValue(id, out var set)) { set = new HashSet<string>(); _asked[id] = set; }
            return set;
        }

        /// The last thing this person actually said, so the next chip can
        /// follow it rather than re-offering the opening menu.
        string LastLineFrom(string id)
        {
            if (_current == null) return null;
            var history = HistoryOf(_current);
            var mark = $"<b>{id}:</b> ";
            for (int i = history.Count - 1; i >= 0; i--)
                if (history[i].StartsWith(mark)) return history[i].Substring(mark.Length);
            return null;
        }

        void SayChip(int i)
        {
            if (_current == null || _waiting || string.IsNullOrEmpty(_chipSays[i])) return;
            AskedOf(CurrentHostId()).Add(_chipLabels[i].text);
            _input.text = _chipSays[i];
            Submit();
        }

        /// 2–3 contextual openers from live game state — the act's threads, known
        /// leads, tonight's beat, Mickey's book. Never the only path.
        void RefreshChips()
        {
            var id = CurrentHostId();
            if (id == null) { _chipRow.SetActive(false); return; }
            var opts = new List<(string label, string say)>();

            if (id == "Noor")
                opts.Add(("the warehouse fire", "What do you know about the warehouse fire?"));
            if (id == "Lena")
                opts.Add(("the real books", "Mickey kept more than one ledger, didn't he?"));
            var lead = CurrentLead();
            if (lead != null && !lead.Handled)
                opts.Add(("what people are saying", "What exactly are people saying about me?"));
            foreach (var b in _game.Beats.All)
                if (b.HostId == id && b.State == BeatState.Pending && b.Day == _game.Now.Day)
                { opts.Add(("tonight", "About tonight. I'll do my best to be there.")); break; }
            if (_game.Debts.Of(id) != null)
                opts.Add(("Mickey's book", "Your name is in Mickey's book. Talk to me about what's owed."));

            // FOLLOW THE CONVERSATION. These were a fixed list per person, so
            // after asking about Mickey the chip still said "Mickey" (playtest
            // 2026-07-28). Anything already asked of this person drops out, and
            // the last thing they SAID offers the obvious next question.
            var asked = AskedOf(id);
            var lastSaid = LastLineFrom(id);
            if (lastSaid != null)
            {
                if (lastSaid.Contains("Mickey") && !asked.Contains("how he died"))
                    opts.Insert(0, ("how he died", "You knew him. How did he actually die?"));
                if ((lastSaid.Contains("police") || lastSaid.Contains("Ellis")) && !asked.Contains("the police"))
                    opts.Insert(0, ("the police", "Has somebody been round asking questions?"));
                if (lastSaid.Contains("money") && !asked.Contains("the money"))
                    opts.Insert(0, ("the money", "Say plainly what you think I owe, or what you're owed."));
            }
            opts.Add(("Mickey", "Tell me about my uncle. What was he really like?"));
            opts.Add(("the street", "How is the street treating everyone these days?"));
            opts.RemoveAll(o => asked.Contains(o.label));

            _chipRow.SetActive(true);
            for (int i = 0; i < 3; i++)
            {
                bool has = i < opts.Count;
                _chipBtns[i].gameObject.SetActive(has);
                _chipSays[i] = has ? opts[i].say : null;
                if (has) _chipLabels[i].text = opts[i].label;
            }
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
                // The router shares the key; drop it so it reconnects too.
                _game.ResetLlm();
                _router = null;
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
            var lt = MakeText(_ledgerPanel.transform, "LedgerTitle", new Vector2(0.5f, 1), new Vector2(0, -12), new Vector2(520, 30), 20, TextAnchor.UpperCenter);
            lt.text = "T H E   B O O K S";
            lt.color = UiTheme.Dim;
            _ledgerText = MakeText(_ledgerPanel.transform, "LedgerText", new Vector2(0.5f, 1), new Vector2(0, -50), new Vector2(520, 556), 16, TextAnchor.UpperLeft);
            _ledgerPanel.SetActive(false);
        }

        void BuildSummaryPanel(Transform parent)
        {
            _summaryPanel = MakePanel(parent, "DaySummary", new Vector2(0.5f, 1), new Vector2(0, -120), new Vector2(640, 250));
            _summaryTitle = MakeText(_summaryPanel.transform, "SummaryTitle", new Vector2(0.5f, 1), new Vector2(0, -14), new Vector2(600, 32), 22, TextAnchor.UpperCenter);
            _summaryTitle.color = UiTheme.Dim;
            _summaryText = MakeText(_summaryPanel.transform, "SummaryText", new Vector2(0.5f, 1), new Vector2(0, -54), new Vector2(580, 180), 18, TextAnchor.UpperLeft);
            _summaryPanel.SetActive(false);
        }

        /// The Persona-style day anchor: each morning, the night's books in one
        /// card. In the open city it becomes the two-books report: the fronts'
        /// take, the rounds' take, and how hard the Dockside arm is leaning.
        public void ShowDaySummary(int dayClosed, int takings, int washed, int talkCount,
            string streetWord, string outfitWord, int clean, int dirty, int racketToday = 0)
        {
            if (SimMode.Days > 0) return; // never block the self-test
            bool open = _game.Campaign.OpenMode;
            _summaryTitle.text = open ? $"THE TWO BOOKS · DAY {dayClosed}" : $"CLOSING THE BOOKS · DAY {dayClosed}";
            var sb = new System.Text.StringBuilder();
            sb.AppendLine($"{(open ? "The fronts" : "Bar takings")} <color={UiTheme.HexCredit}><b>+${takings}</b></color>" +
                (racketToday > 0 ? $"   ·   the rounds <color={UiTheme.HexAmber}><b>+${racketToday} dirty</b></color>" : "") +
                (washed > 0 ? $"   ·   washed <color={UiTheme.HexCredit}>+${washed}</color>" : ""));
            sb.AppendLine($"Cash <b>${clean}</b> clean" +
                (dirty > 0 ? $"   <color={UiTheme.HexDebit}><b>− ${dirty} unwashed</b></color>" : ""));
            if (open)
            {
                var r = _game.Empire.Rival;
                var rivalWord = r.Stage switch
                {
                    0 => "hasn't looked your way",
                    1 => "has noticed you",
                    2 => $"takes ${r.ProtectionTaxPerDay}/day off the top",
                    3 => "is reaching for your people",
                    _ => "is at your door",
                };
                sb.AppendLine($"The street is <b>{streetWord}</b>. The outfit is <b>{(_game.Campaign.OutfitCutOff ? "silent" : outfitWord)}</b>. Dockside {rivalWord}.");
            }
            else sb.AppendLine($"The street is <b>{streetWord}</b>. The outfit is <b>{outfitWord}</b>.");
            sb.AppendLine(talkCount == 0
                ? $"<color={UiTheme.HexDim}>No open liabilities you know of.</color>"
                : talkCount == 1
                    ? $"<color={UiTheme.HexDebit}><b>Somebody is carrying something on you</b></color> — press L for the books."
                    : talkCount <= 3
                        ? $"<color={UiTheme.HexDebit}><b>A few people are carrying things on you</b></color> — press L for the books."
                        : $"<color={UiTheme.HexDebit}><b>Too many people are carrying things on you</b></color> — press L for the books.");
            // The street's own words — the strongest story the player KNOWS about
            // (belief, never ground truth), quoted verbatim from the mill.
            KnownLead word = null;
            foreach (var k in _game.Knowledge.Entries)
                if (!k.Handled && (word == null || k.ConfidenceWhenLearned > word.ConfidenceWhenLearned)) word = k;
            if (word != null)
                sb.AppendLine($"<color={UiTheme.HexDim}><i>Word on the street, as you heard it: \"{word.Summary}\" — and {word.HolderName} is telling it.</i></color>");
            _summaryText.text = sb.ToString();
            _summaryPanel.SetActive(true);
            _summaryUntil = Time.unscaledTime + 9f;
        }

        void RefreshLedger()
        {
            // The position line: the two kinds of money, credit against debit.
            var sb = new System.Text.StringBuilder();
            sb.Append($"<size=26><b>${_game.Wallet.Clean}</b></size> clean");
            if (_game.Wallet.Dirty > 0)
                sb.Append($"   <color={UiTheme.HexDebit}><b>− ${_game.Wallet.Dirty} unwashed</b></color>");
            sb.AppendLine();
            sb.AppendLine();

            // Liabilities: what the street holds on you — belief, never ground truth.
            sb.AppendLine($"<color={UiTheme.HexDim}><b>LIABILITIES — what the street holds</b></color>");
            int shown = 0;
            foreach (var k in _game.Knowledge.Entries)
            {
                if (shown++ >= 12) { sb.AppendLine("…"); break; }
                // A word, not a figure — the legibility law the rest of this
                // screen already obeys (HeatWord, StrainWord, ProsperityWord).
                // "−0.62" told the player nothing a person would say; how hard
                // someone would swear to it does (audit 2026-07-27).
                var figure = k.Handled
                    ? $"<color={UiTheme.HexHeld}>settled</color>"
                    : $"<color={UiTheme.HexDebit}><b>{GripWord(k.ConfidenceWhenLearned)}</b></color>";
                sb.AppendLine($"<b>{k.HolderName}</b> — \"{k.Summary}\"  {figure}");
                sb.AppendLine($"   <color={UiTheme.HexDim}>posted day {k.LearnedAt.Day} · {k.Source}</color>");
            }
            if (shown == 0)
                sb.AppendLine($"<color={UiTheme.HexDim}>No entries. As far as you know, nobody is talking.\nThe street posts here when you see a witness, a loyal\nfriend warns you, or someone admits it to your face.</color>");

            // Assets: what you hold on them (§6.3).
            var held = new System.Text.StringBuilder();
            foreach (var s in _game.HooksBook.Known)
            {
                bool leashed = _game.Gossip != null && _game.Gossip.Mill != null &&
                               (_game.Gossip.Mill.Get(s.OwnerId)?.Leashed ?? false);
                var state = s.Strong
                    ? (leashed ? $"<color={UiTheme.HexCredit}><b>+held</b></color>" : $"<color={UiTheme.HexCredit}>+standing</color>")
                    : (s.HookSpent ? $"<color={UiTheme.HexHeld}>spent</color>" : $"<color={UiTheme.HexCredit}>+one favor</color>");
                held.AppendLine($"<b>{s.OwnerId}</b> — {s.Summary}  {state}");
                held.AppendLine($"   <color={UiTheme.HexDim}>posted day {s.LearnedAt.Day} · from {s.LearnedFrom}</color>");
            }
            var owed = new System.Text.StringBuilder();
            foreach (var d in _game.Debts.All)
                if (d.Outstanding)
                    owed.AppendLine($"<b>{d.Name}</b> — \"{d.Note}\"  <color={UiTheme.HexCredit}><b>+${d.Amount}</b></color>" +
                        $"\n   <color={UiTheme.HexDim}>in Mickey's hand</color>");
            if (held.Length > 0)
                sb.Append($"\n<color={UiTheme.HexDim}><b>ASSETS — what you hold</b></color>\n").Append(held);
            if (owed.Length > 0)
                sb.Append($"\n<color={UiTheme.HexDim}><b>RECEIVABLES — Mickey's book</b></color>\n").Append(owed);

            // The other ledger (open mode): what the street is becoming yours.
            var e = _game.Empire;
            bool anyEmpire = _game.Campaign.OpenMode &&
                (e.Businesses.Exists(b => b.Owned || b.DebtHeld) || e.Crew.Count > 0 || e.Rival.Stage > 0);
            if (anyEmpire)
            {
                sb.Append($"\n<color={UiTheme.HexDim}><b>THE STREET — the other book</b></color>\n");
                // The district's own money, said the way a person would say it —
                // never a percentage (roadmap M7's legibility requirement).
                var econ = _game.Economy;
                sb.AppendLine($"<color={UiTheme.HexDim}>People here are <b>{econ.ProsperityWord()}</b>; prices are <b>{econ.PriceWord()}</b>.</color>");
                // Doors you have actually stood in front of — and only those.
                // Listing every way into every room you have never visited is
                // the same omniscience §6.2 refuses everywhere else.
                var doors = _game.GatesLine();
                if (doors != null) sb.Append(doors);
                foreach (var s in econ.Suppliers)
                {
                    if (s.Refusing)
                        sb.AppendLine($"<b>{s.Name}</b> — <color={UiTheme.HexDebit}>stopped bringing {s.Goods}</color>");
                    else if (s.Unpaid > 0)
                        sb.AppendLine($"<b>{s.Name}</b> — <color={UiTheme.HexHeld}>owed for " +
                            (s.Unpaid == 1 ? "a delivery" : s.Unpaid == 2 ? "two deliveries" : "weeks of deliveries") +
                            $" of {s.Goods}</color>");
                }
                foreach (var b in e.Businesses)
                {
                    if (b.Owned)
                        sb.AppendLine($"<b>the {b.Name}</b> — yours ({b.AcquiredVia})  <color={UiTheme.HexCredit}>+${b.CleanIncomePerDay}/day · washes ${b.LaunderPerDay}</color>");
                    else if (b.DebtHeld)
                        sb.AppendLine($"<b>the {b.Name}</b> — you hold {b.OwnerId}'s paper  <color={UiTheme.HexHeld}>unturned</color>");
                }
                foreach (var c in e.Crew)
                    sb.AppendLine(c.Departed
                        ? $"<b>{c.Name}</b> — <color={UiTheme.HexDebit}>gone to the docks</color>"
                        : $"<b>{c.Name}</b> — crew ({c.Route}){(c.Assignment != null ? $" · runs the {e.RacketOf(c.Assignment)?.Name}" : "")}");
                var rivalWord = e.Rival.Stage switch
                {
                    0 => "hasn't looked your way",
                    1 => "has noticed you",
                    2 => $"taxes you ${e.Rival.ProtectionTaxPerDay}/day",
                    3 => "is reaching for your people",
                    _ => "is at your door",
                };
                sb.AppendLine($"<color={UiTheme.HexDim}>The Dockside arm {rivalWord}.</color>");
                var machine = e.ArmOf("machine");
                if (machine.Stage > 0)
                    sb.AppendLine($"<color={UiTheme.HexDim}>The machine {(machine.Stage >= 4 ? "requests a meeting" : machine.Stage >= 3 ? "bills you by letter" : machine.Stage >= 2 ? "inspects your fronts" : "reads your deeds")}.</color>");
                var crew9 = e.ArmOf("newcrew");
                if (crew9.Stage > 0)
                    sb.AppendLine($"<color={UiTheme.HexDim}>The New crew {(crew9.Stage >= 4 ? "circles the block" : crew9.Stage >= 3 ? "taxes your rounds" : crew9.Stage >= 2 ? "makes noise on your street" : "tagged your wall")}.</color>");
                if (e.TotalRacketIncome > 0)
                    sb.AppendLine($"<color={UiTheme.HexDim}>Rounds to date: ${e.TotalRacketIncome} dirty.</color>");
            }

            // Act III: the one thing in this book that has a deadline. A date
            // and a shape — never a countdown, never a figure.
            if (_game.ActThree.Opened)
            {
                sb.Append($"\n<color={UiTheme.HexDebit}><b>THE AUDIT</b></color>\n");
                if (_game.ActThree.AuditClosed)
                    // The authored post-close line — including Quiet's
                    // "not yours anymore" — had no caller (audit 2026-07-27).
                    sb.AppendLine($"<color={UiTheme.HexDim}>{_game.ActThreeLedgerLine()}</color>");
                else
                {
                    var books = _game.Books();
                    sb.AppendLine($"The inspection is set for <b>day {_game.ActThree.AuditClosesDay}</b>.");
                    sb.AppendLine($"<color={UiTheme.HexDim}>{ActThreeState.StrainWord(ActThreeState.LedgerStrain(books))}.</color>");
                    // What he is actually reading, which is the half of it the
                    // player can still change.
                    if (_game.ActThree.InspectorArrived)
                        sb.AppendLine($"<color={UiTheme.HexDim}>Reese: {ActThreeState.ScopeWord(ActThreeState.ScopeFactor(books.Cooperations, books.Stonewalls))}.</color>");
                    if (_game.ActThree.SoldUp)
                        sb.AppendLine($"<color={UiTheme.HexHeld}>There is nothing left for them to find.</color>");
                    if (_game.ActThree.Deflected)
                        sb.AppendLine($"<color={UiTheme.HexHeld}>They are looking somewhere else. Somebody paid for that.</color>");
                    if (_game.ActThree.SuccessorId != null)
                        sb.AppendLine($"<color={UiTheme.HexHeld}>It is {books.SuccessorName}'s name on the licence now.</color>");
                }
            }
            _ledgerText.text = sb.ToString();
        }

        void Update()
        {
            var now = _game.Now;
            var money = _game.Wallet.Dirty > 0
                ? $"${_game.Wallet.Clean} <color={UiTheme.HexAmber}>+ ${_game.Wallet.Dirty} dirty</color>"
                : $"${_game.Wallet.Clean}";
            // Plain chrome. The em dash and the middle dot are a WRITER's
            // punctuation and they read as somebody's house style rather than
            // as a game's instrument panel (playtest 2026-07-28).
            _clockText.text = $"Day {now.Day}   {now.Hour:D2}:{now.Minute:D2}   {now.Slot}      {money}";

            // Campaign readout: the week, the street's mood, the outfit's patience —
            // in words, not meters. Cheap enough to refresh on a coarse cadence.
            if (Time.frameCount % 30 == 0 || _statusText.text.Length == 0)
            {
                var camp = _game.Campaign;
                double heat = _game.Gossip != null && _game.Gossip.Mill != null ? _game.Gossip.Mill.DayCircleHeat() : 0.0;
                // Open mode drops the countdown framing: nobody is counting days.
                _statusText.text = (camp.OpenMode
                        ? $"The open city, day {now.Day}"
                        : $"Day {Mathf.Min(now.Day, camp.SurviveDays)} of {camp.SurviveDays}") +
                    $".   The street: {HeatWord(heat)}.   The outfit: " +
                    (camp.OutfitCutOff ? "silent" : PatienceWord(camp.OutfitPatience)) + "." +
                    (camp.Falls == 1 ? "   You have fallen once."
                        : camp.Falls > 1 ? "   The street has watched you fall more than once." : "") +
                    (_game.WearingCoat ? $"   <color={UiTheme.HexAmber}>In the coat.</color>" : "");
            }

            if (_toastUntil > 0f && Time.unscaledTime > _toastUntil) { _toastText.text = ""; _toastUntil = 0f; }

            if (_endPanel != null)
            {
                if (Input.GetKeyDown(KeyCode.R)) Restart();
                // The won week continues into the open city (open-city-spec.md).
                if (Input.GetKeyDown(KeyCode.Space) && _endCamp != null
                    && _endCamp.Verdict == Verdict.WonWeek && _game.ActOne.Posture != null)
                {
                    Destroy(_endPanel);
                    _endPanel = null;
                    _endCamp = null;
                    _game.ContinueToOpenMode();
                }
                return; // the week is settled; only the end screen listens now
            }
            if (_posturePanel != null) return; // the question holds the room

            var found = NearestHostInRange();
            bool dialogueOpen = _dialoguePanel.activeSelf;

            // FORGIVENESS WINDOW (game-feel-spec.md §1). The prompt used to
            // vanish the instant you stepped a centimetre out of range, which
            // makes it flicker on the boundary and teaches players to stand
            // unnaturally still. It now survives a beat, so the offer outlives
            // the exact arithmetic of where your feet are.
            if (found != null) { _nearest = found; _grace.SeenInRange(Time.time); }
            else if (!_grace.StillOffered(Time.time)) _nearest = null;

            bool offering = !dialogueOpen && _nearest != null;
            _promptText.text = offering ? $"Press E to talk to {_nearest.Card.Name}" : "";

            // AND IT FADES (§6). A prompt that pops is the single most common
            // tell that a game's interface was bolted on rather than staged.
            _promptAlpha = (float)Feel.Approach(_promptAlpha, offering ? 1f : 0f, 11.0, Time.deltaTime);
            var pc = _promptText.color;
            pc.a = _promptAlpha;
            _promptText.color = pc;

            // The options screen owns the whole keyboard while it is up. Placed
            // BEFORE any other key is read: the first version of this guard sat
            // after the Talk key, so a player adjusting the volume could still
            // start a conversation with whoever they happened to be standing
            // next to.
            if (OptionsScreen.Open) return;

            var keys = GameSettings.Current;

            // INPUT BUFFERING (§1). A press up to 150ms before the prompt
            // became legal still counts. Players never report "no input
            // buffer" — they report the game as unresponsive, and then you go
            // looking for a performance problem that is not there.
            if (Input.GetKeyDown(keys.Key("Talk"))) _talkBuffer.Press(Time.time);
            if (_nearest != null && !dialogueOpen && !_keyPanel.activeSelf
                && _talkBuffer.Consume(Time.time))
                OpenDialogue(_nearest);
            if (Input.GetKeyDown(keys.Key("Pause")))
            {
                // Escape closes whatever is open; with nothing open, it pauses.
                // The Plan, Phone and day-summary panels were missing from this
                // chain, so Escape opened the pause menu ON TOP of them (audit
                // 2026-07-27). Toggles for the first two, because they own
                // their input locks; a plain SetActive would leave those set.
                if (dialogueOpen) CloseDialogue();
                else if (_planPanel != null && _planPanel.activeSelf) TogglePlan();
                else if (_phonePanel != null && _phonePanel.activeSelf) TogglePhone();
                else if (_summaryPanel != null && _summaryPanel.activeSelf) _summaryPanel.SetActive(false);
                else if (_ledgerPanel.activeSelf) _ledgerPanel.SetActive(false);
                else if (_keyPanel.activeSelf) _keyPanel.SetActive(false);
                else if (_debugPanel.activeSelf) _debugPanel.SetActive(false);
                else TogglePause();
                _keyPanel.SetActive(false);
                _debugPanel.SetActive(false);
            }
            if (_paused) { _player.InputLocked = true; return; }
            if (Input.GetKeyDown(keys.Key("Debug"))) _debugPanel.SetActive(!_debugPanel.activeSelf);
            if (Input.GetKeyDown(KeyCode.F2)) _keyPanel.SetActive(!_keyPanel.activeSelf);
            // The Ledger — only while not typing into the dialogue box.
            if (Input.GetKeyDown(keys.Key("Ledger")) && !dialogueOpen && !_keyPanel.activeSelf)
            {
                _ledgerPanel.SetActive(!_ledgerPanel.activeSelf);
                if (_ledgerPanel.activeSelf) { RefreshLedger(); Audio.Ui("page"); }
            }
            if (_ledgerPanel.activeSelf && Time.frameCount % 30 == 0) RefreshLedger();

            // Planning (roadmap M7.5) — open city only, and never over a
            // conversation. Jobs are what the open city gives you INSTEAD of an
            // outfit telling you where to be.
            if (Input.GetKeyDown(keys.Key("Plan")) && !dialogueOpen && !_keyPanel.activeSelf
                && !_ledgerPanel.activeSelf) TogglePlan();

            // The telephone (roadmap M10). Only where there is a line, which is
            // the point — a phone you carry would be a different century and a
            // different game.
            if (Input.GetKeyDown(keys.Key("Phone")) && !dialogueOpen && !_keyPanel.activeSelf
                && !_ledgerPanel.activeSelf) TogglePhone();
            if (_phonePanel != null && _phonePanel.activeSelf
                && Input.GetKeyDown(KeyCode.Escape)) TogglePhone();
            if (_ledgerPanel.activeSelf && Input.GetKeyDown(KeyCode.Escape)) _ledgerPanel.SetActive(false);
            // The plan panel had no Escape at all — the only way out was the
            // "Not tonight" button, and a panel with one exit is a panel that
            // traps somebody who reached for the key every other panel uses.
            if (_planPanel != null && _planPanel.activeSelf
                && Input.GetKeyDown(KeyCode.Escape)) TogglePlan();

            // The runner's coat — day face or night face, one key, never while typing.
            // THE COAT IS A VERB, not a boolean (game-feel-spec.md §6).
            //
            // It used to flip instantly with a toast, which is the exact
            // "instant state flip" the spec calls the hallmark of a
            // prototype — and the coat is a MECHANIC here, the difference
            // between being named and being a shape in the dark. Putting one
            // on takes a moment, and the moment is the point: the wind-up is
            // your chance to change your mind, and the rustle is what makes
            // it a garment rather than a flag.
            if (Input.GetKeyDown(keys.Key("Coat")) && !dialogueOpen && !_keyPanel.activeSelf)
            {
                if (_coatVerb.Begin()) Audio.Foley("cloth", 0.5f);
            }
            _coatVerb.Tick(Time.deltaTime);
            if (_coatVerb.Fired)
            {
                _game.WearingCoat = !_game.WearingCoat;
                Audio.Foley(_game.WearingCoat ? "coat_on" : "coat_off");
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
                    (_game.Gossip != null ? "\n\n" + _game.Gossip.StatusLine() : "") +
                    "\n\n" + _game.PurseStatusLine() +
                    "\n\n" + _game.PhoneStatusLine();

            if (dialogueOpen && _input.isFocused && Input.GetKeyDown(KeyCode.Return))
                Submit();

            // Offer damage control only when the person you're talking to is actually
            // carrying talk about the player; refresh the payoff price as it entrenches.
            if (dialogueOpen && Time.frameCount % 30 == 0)
            {
                RefreshDamageControlRow();
                RefreshChips();
            }
            // Every frame, not every 30: at an Act III state boundary a stale
            // label executes a different verb than the one displayed (audit
            // 2026-07-27). The buttons re-derive from the same state the click
            // handler reads, so what you see is what you press.
            if (dialogueOpen) RefreshEmpireButtons();
            else if (!dialogueOpen && _dcRow.activeSelf) _dcRow.SetActive(false);
            if (!dialogueOpen && _chipRow.activeSelf) _chipRow.SetActive(false);
            if (!dialogueOpen && _empireBtnA.gameObject.activeSelf)
            {
                _empireBtnA.gameObject.SetActive(false);
                _empireBtnB.gameObject.SetActive(false);
            }

            if (dialogueOpen && Time.frameCount % 30 == 0)
            {
                RefreshHookAndDebtButtons();
            }
            else if (!dialogueOpen && _hookBtn.gameObject.activeSelf)
            {
                _hookBtn.gameObject.SetActive(false);
                _collectBtn.gameObject.SetActive(false);
                _forgiveBtn.gameObject.SetActive(false);
            }

            _player.InputLocked = AnyPanelDemandsInput();
        }

        /// THE input-lock policy, in one place. Update() re-derives InputLocked
        /// from this every frame, so a panel that locks input in its own toggle
        /// but is missing here has its lock erased one frame later — exactly
        /// what happened to the Plan and Phone panels (audit 2026-07-27). The
        /// UI smoke test asserts through this method for every locking panel,
        /// so leaving a new panel out of it is a red build, not a subtle walk-
        /// while-planning bug.
        public bool AnyPanelDemandsInput() =>
            _dialoguePanel.activeSelf || _keyPanel.activeSelf
            || (_planPanel != null && _planPanel.activeSelf)
            || (_phonePanel != null && _phonePanel.activeSelf);

        static string HeatWord(double h) => GameController.StreetWord(h);

        /// How hard the holder would swear to what they have on you.
        static string GripWord(double c) =>
            c >= 0.75 ? "they'd swear to it"
            : c >= 0.5 ? "they'll repeat it"
            : "half a story";
        static string PatienceWord(double p) => GameController.OutfitWord(p);

        /// A short transient line at the top of the screen — takings banked, a job
        /// posted, a drop made. The campaign's voice outside of dialogue.
        public void Toast(string line, float seconds = 7f)
        {
            _toastText.text = line;
            _toastUntil = Time.unscaledTime + seconds;
        }

        /// The week is over, one way or another. Freezes play input and offers restart.
        /// A won week earns PP7 first — Lena's question over the true books — and
        /// the verdict screen then carries the day-8 teaser: the city opens.
        /// Self-test hook: take the end screen down and give the player back
        /// their legs.
        ///
        /// A LOST week puts this panel up and sets InputLocked, permanently —
        /// the won-week path has a sim bypass a few lines below and the lost
        /// one never did, because until the coverage floor existed nothing
        /// after a loss was ever tested. The bot has been sitting behind a
        /// "campaign over" screen, unable to walk, while the sim asserted
        /// things about the open city.
        ///
        /// Never called from the game: a player who loses the week reads the
        /// screen and presses R.
        public bool DismissEndScreen()
        {
            if (_endPanel == null) return false;
            Destroy(_endPanel);
            _endPanel = null;
            _endCamp = null;
            if (_player != null) _player.InputLocked = false;
            return true;
        }

        public void ShowEnd(Campaign camp)
        {
            if (_endPanel != null || _posturePanel != null) return;
            CloseDialogue();
            _player.InputLocked = true;
            _promptText.text = "";
            _dcRow.SetActive(false);
            _chipRow.SetActive(false);

            if (camp.Verdict == Verdict.WonWeek && _game.ActOne.Posture == null)
            {
                // The sim bot answers and walks straight into the open city, so
                // week two runs in CI without a screen in the way.
                if (SimMode.Days > 0)
                {
                    _game.AnswerPosture("takeover");
                    _game.ContinueToOpenMode();
                    return;
                }
                ShowPostureScene(camp);
                return;
            }
            ShowEndPanel(camp);
        }

        void ShowPostureScene(Campaign camp)
        {
            _posturePanel = MakePanel(_canvas, "PostureScene", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1000, 520));
            var t = MakeText(_posturePanel.transform, "Title", new Vector2(0.5f, 1), new Vector2(0, -20), new Vector2(900, 40), 26, TextAnchor.UpperCenter);
            t.text = "T H E   T R U E   B O O K S";
            t.color = UiTheme.Dim;
            MakeText(_posturePanel.transform, "Scene", new Vector2(0.5f, 1), new Vector2(0, -72), new Vector2(880, 340), 19, TextAnchor.UpperLeft)
                .text = ActOneState.PostureSceneText;
            MakePostureButton("Wind it down", "winddown", -330, camp);
            MakePostureButton("Take it over", "takeover", 0, camp);
            MakePostureButton("Refuse to answer", "refused", 330, camp);
        }

        void MakePostureButton(string label, string key, float x, Campaign camp)
        {
            var b = MakeButton(_posturePanel.transform, label, new Vector2(0.5f, 0), new Vector2(x, 24), new Vector2(300, 46));
            b.onClick.AddListener(() =>
            {
                _game.AnswerPosture(key);
                Destroy(_posturePanel);
                _posturePanel = null;
                ShowEndPanel(camp);
            });
        }

        Campaign _endCamp;

        void ShowEndPanel(Campaign camp)
        {
            if (_endPanel != null) return;
            _endCamp = camp;
            bool won = camp.Verdict == Verdict.WonWeek;
            _endPanel = MakePanel(_canvas, "EndPanel", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1100, won ? 640 : 420));
            var title = MakeText(_endPanel.transform, "EndTitle", new Vector2(0.5f, 1), new Vector2(0, -50), new Vector2(1000, 70), 44, TextAnchor.UpperCenter);
            title.text = won ? "YOU LASTED THE WEEK"
                : camp.Verdict == Verdict.LostExposed ? "EXPOSED" : "CAST OUT";
            title.color = won ? UiTheme.Credit : UiTheme.Debit;
            MakeText(_endPanel.transform, "EndReason", new Vector2(0.5f, 1), new Vector2(0, -130), new Vector2(950, 60), 22, TextAnchor.UpperCenter)
                .text = camp.VerdictReason;
            MakeText(_endPanel.transform, "EndStats", new Vector2(0.5f, 1), new Vector2(0, -190), new Vector2(950, 50), 18, TextAnchor.UpperCenter)
                .text = $"Drops made: {camp.JobsDone}   ·   missed: {camp.JobsMissed}   ·   takings banked: ${_game.TotalTakings}   ·   " +
                        $"washed: ${_game.Wallet.TotalWashed}   ·   cash: ${_game.Wallet.Clean} clean, ${_game.Wallet.Dirty} dirty";
            if (won)
                MakeText(_endPanel.transform, "Teaser", new Vector2(0.5f, 1), new Vector2(0, -245), new Vector2(920, 330), 17, TextAnchor.UpperLeft)
                    .text = ActOneState.TeaserText;
            MakeText(_endPanel.transform, "EndHint", new Vector2(0.5f, 0), new Vector2(0, 24), new Vector2(950, 36), 20, TextAnchor.LowerCenter)
                .text = won
                    ? "SPACE — keep the keys: day 8, the city opens   ·   R — replay the week"
                    : "Press R to start the week over";
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
            if (_dialoguePanel.activeSelf || _keyPanel.activeSelf || _endPanel != null || _posturePanel != null) return;
            OpenDialogue(host);
        }

        /// Open a conversation with somebody the player is NOT standing next to
        /// — currently only the telephone. Public because the call comes from
        /// the game rather than from walking up to a person.
        public void OpenConversation(ConversationHost host)
        {
            if (host == null) return;
            OpenDialogue(host);
        }

        void OpenDialogue(ConversationHost host)
        {
            Audio.DuckMusic(true);
            _current = host;
            // A loyal-enough carrier admits what they hold the moment you sit down.
            var walker = host.GetComponent<NpcWalker>();
            _game.LearnFromHost(walker != null ? walker.DisplayName : host.Card.Name);
            _titleText.text = host.Card.Name;
            _dialoguePanel.SetActive(true);
            _input.text = "";
            _input.ActivateInputField();
            RefreshChips();
            RenderHistory();
        }

        void CloseDialogue()
        {
            Audio.DuckMusic(false);
            // Hanging up ends the call. If this is not cleared, the next
            // face-to-face conversation would still be told nobody can see
            // anybody, which is the sort of stale flag that produces a
            // character behaving oddly for reasons nobody can trace.
            if (_current != null) _current.OnTheLine = false;
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
            // The intent router (roadmap M6.5) sits between typing and speaking.
            // Most lines are speech and fall straight through, exactly as before
            // this existed — the router is additive, not a gate.
            var handled = await TryRouteAsync(text, host);
            if (handled)
            {
                _waiting = false;
                RefreshActionRows();
                return;
            }

            var reply = await host.SayAsync(text); // Unity's context resumes this on the main thread
            _waiting = false;

            // Remove the placeholder BY MATCHING IT, not by position. The router
            // path above can drop it before falling through, and blind removal
            // would then delete the player's own line instead.
            if (history.Count > 0 && history[history.Count - 1].EndsWith("is thinking...</i>"))
                history.RemoveAt(history.Count - 1);
            history.Add($"<b>{name}:</b> {reply}");
            RenderHistory();
        }

        /// Routes one typed line. Returns true if the line WAS an action and has
        /// been carried out (and narrated); false if it was speech, which is the
        /// common case and leaves the caller's behaviour untouched.
        async System.Threading.Tasks.Task<bool> TryRouteAsync(string text, ConversationHost host)
        {
            IntentContext ctx;
            try
            {
                // The catalogue must describe THIS instant, not the last 30-frame
                // tick, or the router can be offered a verb that has just expired.
                RefreshActionRows();
                ctx = BuildIntentContext();
            }
            catch (System.Exception) { return false; }   // routing must never break talking

            Intent intent;
            try { intent = await Router.RouteAsync(text, ctx, _game.Now); }
            catch (System.Exception) { return false; }

            // The player may have walked off, or the world moved, while we waited.
            if (_current != host) return false;
            if (intent.Kind == IntentKind.Narrative) return false;

            try { RefreshActionRows(); } catch (System.Exception) { return false; }

            if (intent.Kind == IntentKind.Mechanical)
            {
                // Re-checked against the state we just refreshed: a verb that went
                // stale while the router thought is not fired, it becomes speech.
                if (!Live(ButtonFor(intent.VerbId))) return false;
                DropThinking(host);
                if (!ExecuteVerb(intent.VerbId)) return false;
                Audio.Ui("tick");
                return true;
            }

            var verdict = Adjudicator.Resolve(intent, NovelState(intent));
            DropThinking(host);
            if (verdict.Passed) ApplyNovel(intent, verdict);
            Narrate(NovelLine(intent, verdict));
            Audio.Ui(verdict.Passed ? "tick" : "page");
            return true;
        }

        /// Removes the "…is thinking" placeholder before an action narrates over
        /// it. Nobody is thinking: the player did something.
        void DropThinking(ConversationHost host)
        {
            var history = HistoryOf(host);
            if (history.Count > 0 && history[history.Count - 1].EndsWith("is thinking...</i>"))
                history.RemoveAt(history.Count - 1);
            RenderHistory();
        }

        /// Offer damage control only when the person you're talking to is actually
        /// carrying talk about the player; the payoff price moves as it entrenches.
        void RefreshDamageControlRow()
        {
            var lead = CurrentLead();
            _dcRow.SetActive(lead != null);
            if (lead == null) return;
            int price = BribePriceFor(lead);
            _payLabel.text = _game.PlayerCash >= price ? $"Pay off (${price})" : $"Pay off (${price} — short)";
            _payBtn.interactable = _game.PlayerCash >= price;
            _leanLabel.text = "Lean on them";
            _doubtLabel.text = "Plant doubt";
        }

        void RefreshHookAndDebtButtons()
        {
            var hook = CurrentHostHook();
            _hookBtn.gameObject.SetActive(hook != null);
            if (hook != null)
                _hookLabel.text = hook.Strong ? "Use what you know (they're yours)" : "Call in what you know (once)";

            var debtor = _game.Debts.Of(CurrentHostId() ?? "");
            bool owes = debtor != null;
            _collectBtn.gameObject.SetActive(owes);
            _forgiveBtn.gameObject.SetActive(owes);
        }

        /// Everything that decides which buttons are live. The per-frame pass runs
        /// this in pieces on a 30-frame cadence; the router runs the whole thing
        /// before and after it acts, so the catalogue it is offered — and the
        /// staleness check when it executes — are both against current state
        /// rather than up to half a second old.
        void RefreshActionRows()
        {
            if (_current == null) return;
            RefreshDamageControlRow();
            RefreshHookAndDebtButtons();
            RefreshEmpireButtons();
            RefreshChips();
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
            var result = mill.Bribe(known.HolderId, known.TopicKey, price, _game.Now, _game.Purses);
            if (ResolveStale(known, result)) return;
            // Money only changes hands if they actually take it.
            if (result.Outcome == DcOutcome.Contained)
            {
                _game.Wallet.Spend(price, dirtyOk: true);
                _game.Knowledge.MarkHandled(known.HolderId, known.TopicKey);
                Audio.Ui("coin");   // it only sounds like money if money moved
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

        void CollectDebt()
        {
            var id = CurrentHostId();
            var debtor = id != null ? _game.Debts.Of(id) : null;
            if (debtor == null) return;
            var outcome = debtor.Collect(_game.Gossip.Mill.Get(id), _game.Wallet, _game.Gossip.Mill,
                _game.Now, _game.Purses);
            switch (outcome)
            {
                case CollectOutcome.Paid:
                    Narrate($"They count it out slowly. +${debtor.LastPaid} clean. The page closes; something else closes with it."); break;
                // Roadmap M13: willing is not the same as able. The line names
                // what they COULD find and what is still on the page — never
                // what is left in the drawer, because you did not see the drawer,
                // you saw a person emptying it.
                case CollectOutcome.PaidPart:
                    Narrate($"{debtor.LastLine} +${debtor.LastPaid} clean. ${debtor.Amount} still on the page, " +
                            "and now they know you will come back for it."); break;
                case CollectOutcome.Begged:
                    Narrate(debtor.LastLine ?? "They don't have it. They ask for a day — and mean it. Come back tomorrow."); break;
                case CollectOutcome.Refused:
                    Narrate("They tell you where to put Mickey's old paper. By tonight, the street will hear you came squeezing."); break;
                default:
                    Narrate("Not today. You already asked."); break;
            }
        }

        void ForgiveDebt()
        {
            var id = CurrentHostId();
            var debtor = id != null ? _game.Debts.Of(id) : null;
            if (debtor == null) return;
            if (debtor.Forgive(_game.Gossip.Mill.Get(id), _game.Now))
                Narrate($"You tear the page out where they can see it. ${debtor.Amount}, gone. They won't forget this.");
        }

        void PlantDoubt()
        {
            var known = CurrentLead();
            if (known == null) return;
            var result = _game.Gossip.Mill.Discredit(known.TopicKey, null, _game.Now);
            if (ResolveStale(known, result)) return;   // the Fall can wipe a story out from under a lead (audit 2026-07-27)
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

        /// Two Books panel: a hairline edge with the dark fill inset one pixel —
        /// the whole visual system is edges and figures, not boxes and chrome.
        GameObject MakePanel(Transform parent, string name, Vector2 anchor, Vector2 offset, Vector2 size)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<Image>();
            img.color = UiTheme.Hairline;
            Place(go, anchor, offset, size);

            var fill = new GameObject("Fill");
            fill.transform.SetParent(go.transform, false);
            fill.AddComponent<Image>().color = UiTheme.PanelBg;
            var r = fill.GetComponent<RectTransform>();
            r.anchorMin = Vector2.zero; r.anchorMax = Vector2.one;
            r.offsetMin = new Vector2(1, 1); r.offsetMax = new Vector2(-1, -1);
            return go;
        }

        Text MakeText(Transform parent, string name, Vector2 anchor, Vector2 offset, Vector2 size, int fontSize, TextAnchor align)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var text = go.AddComponent<Text>();
            text.font = _font;
            text.fontSize = UiTheme.Scaled(fontSize);
            text.alignment = align;
            text.color = UiTheme.Ink;
            text.supportRichText = true;
            Place(go, anchor, offset, size);
            return text;
        }

        InputField MakeInput(Transform parent, string placeholder, Vector2 anchor, Vector2 offset, Vector2 size)
        {
            var go = new GameObject("Input");
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<Image>();
            img.color = UiTheme.Field;
            Place(go, anchor, offset, size);

            var textComp = MakeText(go.transform, "Text", new Vector2(0.5f, 0.5f), Vector2.zero, size - new Vector2(20, 8), 18, TextAnchor.MiddleLeft);
            var placeholderComp = MakeText(go.transform, "Placeholder", new Vector2(0.5f, 0.5f), Vector2.zero, size - new Vector2(20, 8), 18, TextAnchor.MiddleLeft);
            placeholderComp.text = placeholder;
            placeholderComp.color = UiTheme.Dim;
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
            img.color = UiTheme.ButtonBg;
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
