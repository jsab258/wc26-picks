using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Owns the game clock, day/night cycle, and world orchestration for the
    /// M0 tech spike: one graybox block, a player, three scheduled NPCs, and
    /// Lena (the full conversational character).
    public class GameController : MonoBehaviour
    {
        public float MinutesPerRealSecond = 2f; // 1 game day = 12 real minutes (sim mode overrides)

        public GameTime Now { get; private set; } = new GameTime(1, 9, 0);
        public CostTracker Cost { get; } = new CostTracker();

        // Two currencies that resist mixing (design-doc §6.7): the bar pays clean,
        // the outfit pays dirty, and dirty only becomes clean by washing through
        // the till. PlayerCash stays as the "what I can hand over right now" total.
        public Wallet Wallet { get; } = new Wallet(250);
        public int PlayerCash => Wallet.Total;

        public Campaign Campaign { get; } = new Campaign();
        public PlayerKnowledge Knowledge { get; } = new PlayerKnowledge();
        // Act I's authored spine state (act1-draft.md): pressure-point flags,
        // the posture answer, Noor's two drawers.
        public ActOneState ActOne { get; } = new ActOneState();

        // Empire v1 (open-city-spec §2): the other ledger. Businesses, crew,
        // rackets, and the Dockside street arm watching it all grow.
        public EmpireBook Empire { get; } = EmpireSetup.Build();
        public SecretsBook HooksBook { get; } = SecretsSetup.Build();
        // Marek's book of uncollectable debts (design-doc §1: part of the inheritance).
        public DebtBook Debts { get; } = new DebtBook();
        public int TotalTakings { get; private set; }
        public int LastTakings { get; private set; } = -1;
        public int NightWitnesses { get; private set; }

        // A loyal-enough NPC pulls the player aside when they're carrying talk about
        // them (once a day each); a carrier this loyal also admits what they hold
        // when you talk to them. Both feed PlayerKnowledge — the only window the
        // player ever gets into the rumor network.
        public const double WarnLoyaltyFloor = 0.6;
        public const double RevealLoyaltyFloor = 0.45;
        const float WarnRange = 4f;
        readonly Dictionary<string, int> _lastWarnDay = new Dictionary<string, int>();

        // Disguise v0 (design-doc §6.4 cover): the runner's coat. Worn at a drop,
        // witnesses can't swear it was you (reduced rumor confidence); worn where the
        // day world can see you in daylight, it is itself something to talk about.
        public bool WearingCoat;
        public const double CoatWitnessConfidence = 0.6;
        public bool AnyCoatedWitnessed { get; private set; }
        public double MaxCoatedWitnessConf { get; private set; }
        public int TotalConfrontations { get; private set; }
        readonly Dictionary<string, int> _coatSeenDay = new Dictionary<string, int>();

        public static string OutfitWord(double p) =>
            p > 0.66 ? "satisfied" : p > 0.33 ? "impatient" : "furious";

        // Authored week beats (design-doc §4): the day life asks for the same evening
        // hours the outfit does. Windows overlap the drop window on purpose — thread
        // both if you're quick, or choose whose memory of you matters more tonight.
        public BeatBook Beats { get; } = new BeatBook();
        readonly Dictionary<string, Vector3> _beatSpots = new Dictionary<string, Vector3>();
        readonly HashSet<string> _beatInvited = new HashSet<string>();
        GameObject _beatMarker;
        string _beatMarkerId;

        /// The street's mood about the player, in words — shared by the HUD and by
        /// conversation context so everyone describes the same weather.
        public static string StreetWord(double heat) =>
            heat < 0.2 ? "quiet" : heat < 0.45 ? "murmuring" : heat < 0.7 ? "uneasy" : "hostile";

        public double CurrentHeat => _gossip != null && _gossip.Mill != null ? _gossip.Mill.DayCircleHeat() : 0.0;

        float _minuteAccumulator;
        Light _sun;
        readonly List<NpcWalker> _npcs = new List<NpcWalker>();
        readonly List<ConversationHost> _hosts = new List<ConversationHost>();
        ConversationHost _lena;
        ConversationHost _noor;
        GossipDirector _gossip;
        DialogueUI _ui;
        PlayerController _player;
        int _lastReflectedDay;
        int _lastAgedHour = -1;

        // Detective Ossei (design-doc §8): spawns once the street's talk gets loud
        // enough to reach a precinct desk; while she works it, rumors refuse to die.
        public bool OsseiSpawned { get; private set; }
        public double ObservedPeakHeat { get; private set; }
        ConversationHost _ossei;
        NpcWalker _osseiWalker;

        // §6.5: heat is what witnesses actually saw AND TOLD. When a first-hand
        // witness crosses Ossei's path, she interviews them — unless their silence
        // was bought or leashed first. The race the whole game is about.
        public List<string> OsseiInterviews { get; } = new List<string>();
        readonly HashSet<string> _interviewed = new HashSet<string>();

        // Suspicion escalation (§6.4): Confronting NPCs block the player's path and
        // demand answers — once per day each. Leashed NPCs never escalate (§6.3).
        readonly Dictionary<string, int> _confrontedDay = new Dictionary<string, int>();

        // Night job state. The drop point rotates by day; the marker exists only
        // while the job is open (22:00–02:00).
        GameObject _jobMarker;
        int _jobPostedDay = -1;
        int _lastClosedDay = 1; // day 1's morning is already underway at start
        static readonly Vector3[] DropPoints =
        {
            new Vector3(14, 0, -12), new Vector3(-16, 0, -11), new Vector3(12, 0, 10),
        };

        public GossipDirector Gossip => _gossip;
        public PlayerController Player => _player;
        public Vector3? ActiveJobPos => _jobMarker != null ? (Vector3?)_jobMarker.transform.position : null;

        public void ToastLine(string line, float seconds = 6f) => _ui?.Toast(line, seconds);

        void Start()
        {
            WorldBuilder.BuildBlock();
            _sun = WorldBuilder.BuildSun();

            var player = PlayerController.Spawn(new Vector3(0, 1.2f, -8));
            _player = player;

            _npcs.Add(NpcWalker.Spawn("Rocco", new Color(0.75f, 0.3f, 0.25f), new[]
            {
                (new GameTime(0, 7, 0), new Vector3(18, 0, 14)),   // docks
                (new GameTime(0, 12, 0), WorldBuilder.BarDoor + new Vector3(2, 0, 1)),
                (new GameTime(0, 19, 0), new Vector3(-16, 0, -12)), // home
            }));
            _npcs.Add(NpcWalker.Spawn("Ada", new Color(0.3f, 0.5f, 0.75f), new[]
            {
                (new GameTime(0, 8, 0), new Vector3(-14, 0, 12)),  // apartment steps
                (new GameTime(0, 10, 0), new Vector3(10, 0, -14)), // market corner
                (new GameTime(0, 17, 0), new Vector3(-14, 0, 12)),
            }));
            _npcs.Add(NpcWalker.Spawn("Sam", new Color(0.4f, 0.65f, 0.35f), new[]
            {
                (new GameTime(0, 9, 0), new Vector3(14, 0, -12)),
                (new GameTime(0, 13, 0), new Vector3(14, 0, 12)),
                (new GameTime(0, 16, 0), new Vector3(-12, 0, 14)),
                (new GameTime(0, 21, 0), new Vector3(-12, 0, -14)),
            }));

            _npcs.Add(NpcWalker.Spawn("Mirela", new Color(0.8f, 0.6f, 0.3f), new[]
            {
                (new GameTime(0, 8, 0), new Vector3(10, 0, -14)),  // market stall
                (new GameTime(0, 18, 0), new Vector3(-12, 0, 14)), // home
            }));
            _npcs.Add(NpcWalker.Spawn("Josip", new Color(0.35f, 0.45f, 0.5f), new[]
            {
                (new GameTime(0, 6, 0), new Vector3(18, 0, 14)),   // docks
                (new GameTime(0, 20, 0), WorldBuilder.BarDoor + new Vector3(3, 0, -1)),
                (new GameTime(0, 23, 0), new Vector3(16, 0, 12)),  // home by the water
            }));
            _npcs.Add(NpcWalker.Spawn("Viktor", new Color(0.6f, 0.5f, 0.3f), new[]
            {
                (new GameTime(0, 9, 0), new Vector3(-28, 0, -6)),  // his shop, now standing
                (new GameTime(0, 13, 0), new Vector3(10, 0, -14)), // errands at the market corner
                (new GameTime(0, 17, 0), new Vector3(-26, 0, 14)), // the teahouse, per his card
                (new GameTime(0, 22, 0), new Vector3(-16, 0, -12)), // home on the west row
            }));

            // The generated district population (open-city-spec §3): the batch
            // walks. Brains arrive via the generic host loop below; secrets join
            // the book so the leverage economy scales with the street.
            foreach (var w in Tier2Batch.SpawnWalkers()) _npcs.Add(w);
            foreach (var s in Tier2Batch.Secrets()) HooksBook.Add(s);

            var lenaWalker = NpcWalker.Spawn("Lena", new Color(0.55f, 0.4f, 0.6f), new[]
            {
                (new GameTime(0, 8, 0), WorldBuilder.BarCounter),
                (new GameTime(0, 23, 30), WorldBuilder.BarDoor + new Vector3(-1, 0, -1)),
            });
            _npcs.Add(lenaWalker);
            _lena = lenaWalker.gameObject.AddComponent<ConversationHost>();
            _lena.Initialize(this, LenaSetup.CardMarkdown, LenaSetup.SeedKnowledge, LenaSetup.SeedMemories);
            _lena.SceneContext = "Behind the counter of the Hook Street bar, talking with the new owner.";
            // Lena keeps the books: she knows exactly what the till took and whether
            // the street's talk is what's thinning it.
            _lena.ExtraContext = () =>
            {
                var mood = $"Talk about the new owner around the street is {StreetWord(CurrentHeat)}.";
                var firstDay = Now.Day == 1 ? " It is the new owner's first day; you are showing them the place, half testing them. Your walkthrough ended at the cellar door you did not open — \"storeroom's nothing, mind the step\" — and you would rather they didn't think about that door again." : "";
                if (LastTakings < 0) return $"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week.{firstDay} {mood}{HostRevealText("Lena")}{SecretContext("Lena")}{SuspicionBehaviorText("Lena")}";
                var thin = LastTakings < Campaign.BarBaseTakings * 0.7
                    ? " You know the takings are thin because of what people are saying about the owner." : "";
                return $"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week. " +
                       $"Yesterday the bar took in ${LastTakings}.{thin} {mood}{HostRevealText("Lena")}{SecretContext("Lena")}{SuspicionBehaviorText("Lena")}";
            };
            _hosts.Add(_lena);

            // Noor Farid (approved card): lives above Ada's, walks the port beat.
            // Act I's PP3 is her card doing its job — she asks about the fire
            // because it is a Hard Fact, not because a quest flag fired.
            var noorWalker = NpcWalker.Spawn("Noor", NoorSetup.Color, new[]
            {
                (new GameTime(0, 7, 30), new Vector3(18, 0, 14)),   // docks, working the beat
                (new GameTime(0, 11, 0), new Vector3(10, 0, -14)),  // market corner
                (new GameTime(0, 14, 0), new Vector3(-14, 0, 12)),  // the room above Ada's, writing
                (new GameTime(0, 20, 0), WorldBuilder.BarDoor + new Vector3(-2, 0, 2)),
                (new GameTime(0, 23, 0), new Vector3(-14, 0, 12)),  // home
            });
            _npcs.Add(noorWalker);
            _noor = noorWalker.gameObject.AddComponent<ConversationHost>();
            _noor.Initialize(this, NoorSetup.CardMarkdown, null, null);
            _noor.SceneContext = "On her rounds of Hook Street, notebook half out of a pocket, talking with the new bar owner.";
            _noor.ExtraContext = () =>
            {
                var sb = new System.Text.StringBuilder();
                sb.Append($"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week on Hook Street. ");
                sb.Append($"Talk about the new owner around the street is {StreetWord(CurrentHeat)}.");
                if (Now.Day <= 2) sb.Append(" You have only just met the new owner.");
                if (OsseiSpawned) sb.Append(NoorSetup.OsseiContextLine); // PP6: two collectors, different rules
                if (ActOne.NoorDrawersBroken) sb.Append(NoorSetup.DrawerBrokenLine);
                else if (ActOne.NoorDrawersEngaged) sb.Append(NoorSetup.DrawerHeldLine);
                sb.Append(HostRevealText("Noor")).Append(SecretContext("Noor")).Append(SuspicionBehaviorText("Noor"));
                return sb.ToString();
            };
            _hosts.Add(_noor);

            // The rest of the cast gets conversation brains too — you can find the
            // witness and handle him directly instead of only hearing about it from Lena.
            foreach (var npc in _npcs)
            {
                var member = CastSetup.Get(npc.DisplayName) ?? Tier2Setup.Get(npc.DisplayName) ?? Tier2Batch.Get(npc.DisplayName);
                if (member == null) continue;
                var host = npc.gameObject.AddComponent<ConversationHost>();
                host.Initialize(this, member.Card, null, null);
                host.SceneContext = member.Scene;
                var walkerName = npc.DisplayName;
                host.ExtraContext = () =>
                    $"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week on Hook Street. " +
                    $"Talk about the new owner around the street is {StreetWord(CurrentHeat)}." +
                    $"{ActOneState.DayOneContext(walkerName, Now.Day)}{HostRevealText(walkerName)}{BeatContext(walkerName)}{SecretContext(walkerName)}{SuspicionBehaviorText(walkerName)}";
                _hosts.Add(host);
            }

            _ui = DialogueUI.Create(this, player, _hosts);

            _gossip = gameObject.AddComponent<GossipDirector>();
            _gossip.Begin(this, _npcs, _hosts);
            _gossip.OnEvents = OnGossipEvents;

            // The week's two dilemma evenings: both windows sit inside the outfit's
            // drop window. Ada tests the day face; Rocco tests the family face.
            Beats.Add(new Beat
            {
                Id = "tea", HostId = "Ada", Title = "Tea with Ada", Day = 3, StartHour = 22, EndHour = 24,
                InviteText = "Ada catches you by the market: \"Come for tea tonight. After you close — twenty-two o'clock. I'll wait up.\"",
            });
            _beatSpots["tea"] = new Vector3(-14, 0, 12); // her apartment steps
            Beats.Add(new Beat
            {
                Id = "toast", HostId = "Rocco", Title = "A drink for Marek", Day = 5, StartHour = 22, EndHour = 24,
                InviteText = "Rocco, quiet at the door: \"I never drank to Marek proper. Not once since we buried him. Tonight I do. Sit with me, boss — ten o'clock, my front step.\"",
            });
            // His home stoop, not the bar door: attendance must be a deliberate trip,
            // never a side effect of walking out of your own bar.
            _beatSpots["toast"] = new Vector3(-16.5f, 0, -12.5f);

            if (SimMode.Days > 0)
                gameObject.AddComponent<SimDirector>().Begin(this, player);

            Debts.Add(new Debtor { Id = "Sam", Name = "Sam", Amount = 120, Note = "stock money, never repaid" });
            Debts.Add(new Debtor { Id = "Rocco", Name = "Rocco", Amount = 60, Note = "the door take, '19" });

            TryLoad();
        }

        void Update()
        {
            _minuteAccumulator += Time.deltaTime * MinutesPerRealSecond;
            while (_minuteAccumulator >= 1f)
            {
                _minuteAccumulator -= 1f;
                Now = Now.AddMinutes(1);
            }

            UpdateSun();
            foreach (var npc in _npcs) npc.Tick(Now);

            // Once per game-hour, let rumors cool if nobody is keeping them alive — this
            // is what makes the player's "lie low and let it blow over" option real.
            if (Now.Hour != _lastAgedHour)
            {
                _lastAgedHour = Now.Hour;
                _gossip?.Mill?.Age(Now);
            }

            // Nightly reflection: distill the day's memories into beliefs once, from 23:00.
            // Use >= 23, not == 23: under the accelerated sim clock a single frame can
            // step across the exact hour, and the per-day guard already limits it to once.
            if (Now.Hour >= 23 && Now.Day > _lastReflectedDay && _lena != null && _lena.Ready)
            {
                _lastReflectedDay = Now.Day;
                _ = _lena.RunReflectionAsync(Now);
            }

            UpdateCampaign();
            if (Campaign.FallPending) RunTheFall();
            UpdateBeats();
            if (Input.GetKeyDown(KeyCode.F5)) SaveNow();
            if (Time.frameCount % 30 == 0)
            {
                CheckLoyalWarnings();
                CheckOssei();
                CheckConfrontations();
                CheckBarks();
                CheckOsseiInterviews();
                CheckOnboarding();
                CheckActOne();
            }
        }

        // RDR2's lesson, run on real memory: the city greets what it remembers.
        // Barks only fire when the relationship state SAYS something — neutral
        // strangers stay silent, so every bark is information.
        readonly Dictionary<string, int> _barkDay = new Dictionary<string, int>();

        void CheckBarks()
        {
            if (_gossip == null || _gossip.Mill == null || _player == null || _ui == null) return;
            foreach (var npc in _npcs)
            {
                if (npc == null) continue;
                var name = npc.DisplayName;
                if (_barkDay.TryGetValue(name, out var d) && d == Now.Day) continue;
                if (_lastWarnDay.TryGetValue(name, out var wd) && wd == Now.Day) continue; // warnings outrank barks
                if (Vector3.Distance(npc.transform.position, _player.transform.position) > 5f) continue;
                var line = BarkFor(name);
                if (line == null) continue;
                _barkDay[name] = Now.Day;
                _ui.Toast(line, 5f);
                break; // one voice per pass
            }
        }

        // First-morning onboarding: three lines, diegetic in tone, never in sim.
        int _onboardStep;

        void CheckOnboarding()
        {
            if (SimMode.Days > 0 || Now.Day != 1 || _ui == null) return;
            if (_onboardStep == 0 && (Now.Hour > 9 || (Now.Hour == 9 && Now.Minute >= 10)))
            {
                _onboardStep = 1;
                _ui.Toast("The bar is yours now. Walk up to anyone and press E to talk — they remember.", 9f);
            }
            else if (_onboardStep == 1 && Now.Hour >= 10)
            {
                _onboardStep = 2;
                _ui.Toast("Press L for your ledger: what you believe the street knows about you — and what you hold over it.", 9f);
            }
            else if (_onboardStep == 2 && Now.Hour >= 12)
            {
                _onboardStep = 3;
                _ui.Toast("Tonight the outfit will want its first drop made. C toggles the runner's coat — harder to name in the dark, harder to explain in daylight.", 10f);
            }
        }

        void CheckOsseiInterviews()
        {
            if (!OsseiSpawned || _osseiWalker == null || _gossip == null || _gossip.Mill == null) return;
            foreach (var npc in _npcs)
            {
                if (npc == null || npc == _osseiWalker) continue;
                if (npc.DisplayName == "Noor") continue; // she never shares with police — the whole of her ethics
                var g = _gossip.Mill.Get(npc.DisplayName);
                if (g == null || g.Leashed) continue; // a leashed witness gives her nothing
                if (Vector3.Distance(npc.transform.position, _osseiWalker.transform.position) > 6f) continue;
                foreach (var r in g.Rumors)
                {
                    if (r.Hops != 0 || r.Content.Subject != "player") continue;
                    if (g.Suppressed.Contains(r.TopicKey)) continue; // bought silence holds, even against her
                    if (!_interviewed.Add(npc.DisplayName + "|" + r.TopicKey)) continue;
                    OsseiInterviews.Add($"{npc.DisplayName} told you: {r.Summary}");
                    g.Memory.Append(new MemoryEvent(Now, "conversation", 0.8,
                        $"The detective asked me straight. I told her what I saw: {r.Summary}"));
                    if (_ossei != null) _ossei.Memory.Append(new MemoryEvent(Now, "conversation", 0.85,
                        $"Interviewed {npc.DisplayName}. Statement: {r.Summary}"));
                }
            }
        }

        // ---- Act I (act1-draft.md, approved): authored moments over the machine ----

        void CheckActOne()
        {
            // PP1 — day one: the tour ends at a door that stays shut.
            if (!ActOne.Pp1Fired && Now.Day == 1 && (Now.Hour > 9 || (Now.Hour == 9 && Now.Minute >= 30)))
            {
                ActOne.Pp1Fired = true;
                ToastLine(ActOneState.Pp1CellarLine, 9f);
                _lena?.Memory.Append(new MemoryEvent(Now, "observation", 0.7,
                    "Walked the new owner through the place. Ended the tour at the cellar door and kept it shut. Storeroom's nothing, I said. Mind the step."));
            }

            // PP4 — the book under the step: fires the moment the player learns
            // where, whichever channel taught them (confession, sharing, pressure).
            if (!ActOne.Pp4Fired)
            {
                var s = HooksBook.ById("lena_ledger");
                if (s != null && s.KnownToPlayer)
                {
                    ActOne.Pp4Fired = true;
                    ToastLine(ActOneState.Pp4LedgerPage, 14f);
                    _lena?.Memory.Append(new MemoryEvent(Now, "observation", 0.9,
                        "The new owner knows where Marek's real ledger is now. All of it. Even the page about the warehouse."));
                }
            }

            CheckNoorDrawers();
        }

        /// Noor's two drawers: while they hold, anything she hears about the
        /// player stays out of circulation — suppressed, not forgotten.
        void CheckNoorDrawers()
        {
            if (_gossip == null || _gossip.Mill == null || ActOne.NoorDrawersBroken) return;
            var g = _gossip.Mill.Get("Noor");
            if (g == null) return;
            if (!ActOne.NoorDrawersEngaged)
            {
                if (g.Loyalty < NoorSetup.DrawerLoyaltyFloor) return;
                ActOne.NoorDrawersEngaged = true;
                ToastLine("Something has shifted with Noor. What she hears about you lately goes in the drawer that isn't a story.", 8f);
            }
            foreach (var r in g.Rumors)
                if (r.Content.Subject == "player" && g.Suppressed.Add(r.TopicKey))
                    ActOne.NoorDrawerTopics.Add(r.TopicKey);
        }

        /// A caught lie is the one thing that breaks the drawers: loyalty drops
        /// double, and everything she was sitting on is a story again.
        void OnGossipEvents(List<GossipEvent> events)
        {
            if (events == null || _gossip == null || _gossip.Mill == null) return;
            foreach (var ev in events)
            {
                if (!ev.Contradiction || ev.ToId != "Noor") continue;
                var g = _gossip.Mill.Get("Noor");
                if (g == null) return;
                g.Loyalty = System.Math.Clamp(g.Loyalty - NoorSetup.CaughtLieLoyaltyDrop, 0, 1);
                if (ActOne.NoorDrawersEngaged && !ActOne.NoorDrawersBroken)
                {
                    ActOne.NoorDrawersBroken = true;
                    foreach (var t in ActOne.NoorDrawerTopics) g.Suppressed.Remove(t);
                    ActOne.NoorDrawerTopics.Clear();
                    g.Memory.Append(new MemoryEvent(Now, "observation", 0.9,
                        "I caught the new owner lying to me. Everything moves to the story drawer now."));
                    ToastLine("Noor has gone quiet on you. Whatever she was keeping out of print, she isn't anymore.", 8f);
                }
                return; // one lie lands once per batch
            }
        }

        /// Day 8 (open-city-spec.md): the won week and the spoken posture open the
        /// city. The verdict machinery stands down; the two ledgers are the game.
        public void ContinueToOpenMode()
        {
            if (Campaign.Verdict != Verdict.WonWeek || ActOne.Posture == null) return;
            Campaign.EnterOpenMode();
            if (_player != null) _player.InputLocked = false;
            SaveNow(quiet: true);
            ToastLine("Day 8. Nobody is counting the days anymore. Two books, no ceiling.", 10f);
        }

        /// The Fall (open-city-spec.md, decision 4): exposure in the open city is
        /// survivable but scarring. Three days inside; the unwashed cash is
        /// seized; the street stops guessing and starts KNOWING — rumors collapse
        /// into hard fact, suspicion has nothing left to feed on, and everyone
        /// thinks a little less of you. The city remembers. Play resumes.
        void RunTheFall()
        {
            if (!Campaign.FallPending || _gossip == null || _gossip.Mill == null) return;
            Campaign.ConsumeFall();
            if (_jobMarker != null) { Destroy(_jobMarker); _jobMarker = null; }

            int seized = Wallet.Seize();
            Now = new GameTime(Now.Day + 3, 8, 0);
            _lastClosedDay = Now.Day;   // the skipped mornings never close
            _jobPostedDay = Now.Day;    // no ghost job from the lost nights

            var didTime = new Fact("player", "did_time", "true");
            foreach (var a in _gossip.Mill.Agents)
            {
                a.Rumors.RemoveAll(r => r.Content.Subject == "player");
                a.Knowledge.Learn(didTime);
                a.Loyalty = System.Math.Clamp(a.Loyalty - 0.15, 0, 1);
                a.Suspicion.Restore(0.2); // nothing left to suspect — they know
                a.Memory.Append(new MemoryEvent(Now, "heard", 0.9,
                    "They took the new owner in. Three days inside. Nobody on this street is guessing anymore."));
            }
            // The talk is over — it's public record now; the old liabilities settle.
            foreach (var k in Knowledge.Entries) Knowledge.MarkHandled(k.HolderId, k.TopicKey);

            _ui?.Toast(seized > 0
                ? $"THE FALL. Three days inside. They kept the ${seized} they found — the money the books couldn't explain. The street knows now. Start from there."
                : "THE FALL. Three days inside. They found nothing to keep, which is the only mercy. The street knows now. Start from there.", 14f);
            SaveNow(quiet: true);
        }

        /// The recruit-by-need table: the authored roster first, then the
        /// generated batch's own needs (default price, their card's words).
        public bool TryNeedOf(string id, out int cost, out string line) =>
            EmpireSetup.TryNeed(id, out cost, out line) || Tier2Batch.TryNeed(id, out cost, out line);

        /// PP7: the player says out loud which life they're choosing. Dialogue +
        /// a Fact every cast brain learns (player decision 2026-07-26); mechanics
        /// are Act II's job. Ossei is excluded — the answer travels as street
        /// talk, and this street does not talk to police on purpose.
        public void AnswerPosture(string choice)
        {
            if (ActOne.Posture != null) return;
            ActOne.Posture = choice;
            var summary = ActOneState.PostureSummary(choice);
            var fact = new Fact("player", "posture", choice);
            foreach (var host in _hosts)
            {
                if (host == null || host == _ossei) continue;
                host.Knowledge.Learn(fact);
                host.Memory.Append(host == _lena
                    ? new MemoryEvent(Now, "conversation", 0.95, $"Day seven, over the true books, I asked straight. {summary}.")
                    : new MemoryEvent(Now, "heard", 0.7, $"Word moved down the street inside a day: {summary}."));
            }
            SaveNow(quiet: true);
        }

        string BarkFor(string name)
        {
            if (name == "Ossei")
                return OsseiSpawned ? "Ossei watches you pass. She doesn't pretend otherwise." : null;
            var g = _gossip.Mill.Get(name);
            if (g == null) return null;
            if (g.Leashed) return $"{name} finds somewhere else to look as you pass.";
            if (g.Suspicion.Level == SuspicionLevel.Confronting) return $"{name} stares at you, arms folded. No greeting.";
            if (g.Suspicion.Level == SuspicionLevel.Suspicious) return $"{name} watches you a beat too long before nodding.";
            bool carries = false;
            foreach (var l in _gossip.Mill.Leads("player"))
                if (l.HolderId == name) { carries = true; break; }
            if (carries && g.Suspicion.Level == SuspicionLevel.Uneasy)
                return $"{name} gives you a thin nod. Something's behind it.";
            if (g.Loyalty >= 0.7) return $"{name} raises a hand as you pass. \"Boss.\"";
            return null;
        }

        void CheckOssei()
        {
            double heat = CurrentHeat;
            if (heat > ObservedPeakHeat) ObservedPeakHeat = heat;
            if (OsseiSpawned || heat < OsseiSetup.SpawnHeatThreshold) return;
            SpawnOssei();
        }

        void SpawnOssei()
        {
            if (OsseiSpawned) return;
            OsseiSpawned = true;

            var walker = NpcWalker.Spawn("Ossei", OsseiSetup.Color, new[]
            {
                (new GameTime(0, 9, 0), new Vector3(10, 0, -14)),   // market corner, listening
                (new GameTime(0, 12, 0), WorldBuilder.BarDoor + new Vector3(3, 0, 2)),
                (new GameTime(0, 15, 0), new Vector3(18, 0, 14)),   // the docks
                (new GameTime(0, 19, 0), new Vector3(-14, 0, 10)),  // apartment row
                (new GameTime(0, 22, 0), new Vector3(4, 0, -4)),    // a corner with a view, at night
            });
            _npcs.Add(walker); // she walks and talks; she is NOT added to the gossip mill
            _osseiWalker = walker;
            _ossei = walker.gameObject.AddComponent<ConversationHost>();
            _ossei.Initialize(this, OsseiSetup.CardMarkdown, null, null);
            _ossei.SceneContext = "On Hook Street, unhurried, notebook in hand, talking with the new bar owner.";
            _ossei.ExtraContext = () =>
            {
                var sb = new System.Text.StringBuilder();
                sb.Append($"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week. ");
                // She has been interviewing the street: she knows what the loudest
                // stories ARE (not whether they're true) and probes around them.
                var leads = _gossip != null && _gossip.Mill != null ? _gossip.Mill.Leads("player") : null;
                if (OsseiInterviews.Count > 0)
                {
                    sb.Append("Witness statements you hold: ");
                    for (int i = System.Math.Max(0, OsseiInterviews.Count - 2); i < OsseiInterviews.Count; i++)
                        sb.Append($"\"{OsseiInterviews[i]}\" ");
                }
                if (leads != null && leads.Count > 0)
                {
                    sb.Append("From your interviews you know what people are saying: ");
                    for (int i = 0; i < leads.Count && i < 2; i++)
                        sb.Append($"\"{leads[i].Summary}\"{(i == 0 && leads.Count > 1 ? "; " : ". ")}");
                    sb.Append("You ask small, precise questions around these stories and remember every answer.");
                }
                return sb.ToString();
            };
            _hosts.Add(_ossei);

            // Her presence keeps stories alive: people retell what officials keep asking about.
            if (_gossip != null && _gossip.Mill != null)
                _gossip.Mill.RumorHalfLifeHours = OsseiSetup.PresenceRumorHalfLifeHours;

            _ui?.Toast("A stranger is working Hook Street. Tan coat, level voice, takes her time. Asks about you.", 10f);
        }

        /// §6.4 top rung: an NPC at Confronting suspicion blocks the player's path
        /// and demands answers — the conversation opens itself.
        void CheckConfrontations()
        {
            if (_gossip == null || _gossip.Mill == null || _player == null || _ui == null) return;
            foreach (var npc in _npcs)
            {
                if (npc == null || npc.DisplayName == "Ossei") continue;
                var g = _gossip.Mill.Get(npc.DisplayName);
                if (g == null || g.Leashed) continue;
                if (g.Suspicion.Level != SuspicionLevel.Confronting) continue;
                if (_confrontedDay.TryGetValue(npc.DisplayName, out var d) && d == Now.Day) continue;
                if (Vector3.Distance(npc.transform.position, _player.transform.position) > WarnRange) continue;

                _confrontedDay[npc.DisplayName] = Now.Day;
                TotalConfrontations++;
                var host = npc.GetComponent<ConversationHost>();
                if (host == null) continue;
                _ui.Toast($"{npc.DisplayName} steps into your path. This isn't a chat.", 6f);
                _ui.ForceDialogue(host);
                break; // one ambush at a time
            }
        }

        void UpdateBeats()
        {
            if (_gossip == null || _gossip.Mill == null) return;

            // Morning invitation, once, on the beat's day.
            var today = Beats.For(Now.Day);
            if (today != null && today.State == BeatState.Pending && Now.Hour >= 9 && _beatInvited.Add(today.Id))
                _ui?.Toast(today.InviteText, 10f);

            // Lapsed windows resolve to skipped — people remember.
            foreach (var missed in Beats.ResolveLapsed(id => _gossip.Mill.Get(id), Now))
                _ui?.Toast($"You never went. {missed.HostId} will remember that.");

            var open = Beats.Open(Now);
            if (open == null || _beatMarkerId != open.Id)
            {
                // Marker must always belong to the currently open beat — destroy on
                // close AND on any beat change, so a stale marker can never attend
                // a different beat than the one it stands for.
                if (_beatMarker != null) { Destroy(_beatMarker); _beatMarker = null; }
                _beatMarkerId = null;
                if (open == null) return;
            }
            if (_beatMarker == null && _beatSpots.TryGetValue(open.Id, out var spot))
            {
                // A warm porch-light glow, distinct from the drop's hot orange.
                _beatMarker = SpawnGlowMarker(spot, new Color(0.7f, 0.85f, 1f), $"Beat_{open.Id}");
                _beatMarkerId = open.Id;
            }
            if (_beatMarker != null && _player != null)
            {
                var p = _player.transform.position;
                var m = _beatMarker.transform.position;
                if (Vector3.Distance(new Vector3(p.x, 0, p.z), new Vector3(m.x, 0, m.z)) < 2.5f)
                {
                    open.Attend(_gossip.Mill.Get(open.HostId), Now);
                    Destroy(_beatMarker);
                    _beatMarker = null;
                    _beatMarkerId = null;
                    _ui?.Toast($"{open.Title}. You stayed a while. {open.HostId} will remember this.", 8f);
                }
            }
        }

        void UpdateCampaign()
        {
            if (Campaign.Verdict != Verdict.Ongoing) return; // world keeps turning; stakes are settled

            // Daily close at the bar's morning open: bank takings taxed by the
            // street's current heat, and advance the exposure fuse.
            if (Now.Hour >= 8 && Now.Day > _lastClosedDay)
            {
                _lastClosedDay = Now.Day;
                double heat = CurrentHeat;
                int takings = Campaign.CloseDay(heat);
                // Owned fronts pay clean and get heat-taxed exactly like the bar
                // — a front is a front. Their washing capacity joins the till's.
                foreach (var b in Empire.Businesses)
                    if (b.Owned && b.CleanIncomePerDay > 0)
                        takings += (int)System.Math.Round(b.CleanIncomePerDay * System.Math.Max(0.0, 1.0 - 0.85 * heat));
                Wallet.EarnClean(takings);
                TotalTakings += takings;
                LastTakings = takings;
                Wallet.LaunderPerDay = 120 + Empire.OwnedLaunderCapacity;
                int washed = Wallet.Launder();
                var line = takings >= Campaign.BarBaseTakings
                    ? $"Bar takings: +${takings}."
                    : $"Bar takings: +${takings}. The talk on the street is costing you.";
                if (washed > 0) line += $" ${washed} of night money washed through the till.";
                _ui?.Toast(line);

                int talk = 0;
                foreach (var k in Knowledge.Entries) if (!k.Handled) talk++;
                _ui?.ShowDaySummary(Now.Day - 1, takings, washed, talk,
                    StreetWord(heat), OutfitWord(Campaign.OutfitPatience), Wallet.Clean, Wallet.Dirty);

                // The bookkeeper sees a hoard the till can't explain. Diegetic
                // "unexplained money" pressure (design-doc §6.7) — small, daily.
                if (Wallet.Dirty > Wallet.LaunderPerDay && _lena != null)
                {
                    _lena.Suspicion.Raise(0.04, "cash keeps appearing that the books cannot explain");
                    _lena.Memory.Append(new MemoryEvent(Now, "observation", 0.6,
                        "Counted the till again. There is money moving through this bar that no tap sold."));
                }
                // The empire's day settles with the books (open mode only): racket
                // takes, witnesses into the mill, the rival's daily read. Income
                // folds into one line; the street's own moves get their own voice.
                if (Campaign.OpenMode && _gossip != null && _gossip.Mill != null)
                {
                    int racketTotal = 0;
                    string streetLine = null;
                    foreach (var ev in Empire.DailyTick(Now, Wallet, _gossip.Mill))
                    {
                        if (ev.Kind == "income") racketTotal += ev.Amount;
                        else streetLine = ev.Text; // rival/crew/witness — the last one speaks
                    }
                    if (racketTotal > 0) _ui?.Toast($"The street's rounds bring in ${racketTotal} dirty.", 7f);
                    if (streetLine != null) _ui?.Toast(streetLine, 11f);
                }

                if (Campaign.Verdict != Verdict.Ongoing) { EndCampaign(); return; }
                SaveNow(quiet: true); // the morning close is the autosave point
            }

            // Night job lifecycle: posted at 22:00, open until 02:00, done by
            // standing at the glowing drop, missed if the window closes first.
            // A cut-off outfit posts nothing — the silence is the consequence.
            bool inWindow = Campaign.InJobWindow(Now) && !Campaign.OutfitCutOff;
            if (inWindow && Now.Hour >= 22 && _jobPostedDay != Now.Day)
            {
                _jobPostedDay = Now.Day;
                SpawnJobMarker(DropPoints[Now.Day % DropPoints.Length]);
                // PP2 — the first ask is authored: the runner names Marek's
                // compliance, so refusal reads as breaking HIS deal.
                if (!ActOne.Pp2Fired)
                {
                    ActOne.Pp2Fired = true;
                    _ui?.Toast(ActOneState.Pp2RunnerLine, 12f);
                }
                else _ui?.Toast("The outfit wants a drop made tonight. Find the glow on the street before 02:00.");
            }
            if (_jobMarker == null) return;

            if (!inWindow)
            {
                Destroy(_jobMarker);
                _jobMarker = null;
                Campaign.JobMissed();
                _ui?.Toast(Campaign.OutfitCutOff
                    ? "The outfit stops calling. No runner, no pay, no protection. The street will notice the silence."
                    : "You missed the outfit's drop. They won't forget.");
                if (Campaign.Verdict != Verdict.Ongoing) EndCampaign();
            }
            else if (_player != null)
            {
                var p = _player.transform.position;
                var m = _jobMarker.transform.position;
                if (Vector3.Distance(new Vector3(p.x, 0, p.z), new Vector3(m.x, 0, m.z)) < 2.5f)
                {
                    Destroy(_jobMarker);
                    _jobMarker = null;
                    Campaign.JobDone();
                    Wallet.EarnDirty(Campaign.JobPay);
                    double conf = WearingCoat ? CoatWitnessConfidence : 1.0;
                    var seen = _gossip != null ? _gossip.WitnessNightJob(p, Now.Day, Now, conf)
                        : new List<string>();
                    NightWitnesses += seen.Count;
                    if (WearingCoat && seen.Count > 0)
                    {
                        AnyCoatedWitnessed = true;
                        // End-to-end check: read the created rumors back out of the
                        // mill, so the sim can prove the doubt actually landed.
                        foreach (var w in seen)
                        {
                            var g = _gossip.Mill.Get(w);
                            if (g == null) continue;
                            var r = g.Best($"player.night_job_d{Now.Day}");
                            if (r != null && r.Confidence > MaxCoatedWitnessConf) MaxCoatedWitnessConf = r.Confidence;
                        }
                    }
                    // You saw them see you: each witness becomes a known lead.
                    foreach (var w in seen)
                        foreach (var lead in _gossip.Mill.Leads("player"))
                            if (lead.HolderId == w && lead.TopicKey == $"player.night_job_d{Now.Day}")
                                Knowledge.Learn(lead, $"you saw {w} watching", Now);
                    _ui?.Toast(seen.Count > 0
                        ? WearingCoat
                            ? $"Drop made. +${Campaign.JobPay} dirty. {string.Join(" and ", seen)} saw a figure in a coat."
                            : $"Drop made. +${Campaign.JobPay} dirty. {string.Join(" and ", seen)} saw you — and your face."
                        : $"Drop made. +${Campaign.JobPay} dirty.");
                }
            }
        }

        /// Loyal NPCs pull the player aside (once a day each) when carrying fresh
        /// talk about them — the ambient channel into PlayerKnowledge.
        void CheckLoyalWarnings()
        {
            if (_gossip == null || _gossip.Mill == null || _player == null || _ui == null) return;
            bool daylight = Now.Hour >= 8 && Now.Hour < 20;
            foreach (var npc in _npcs)
            {
                if (npc == null) continue;
                var name = npc.DisplayName;
                var g = _gossip.Mill.Get(name);
                if (g == null) continue;

                // The coat in broad daylight: a day-circle face clocking you in your
                // night clothes is quietly filed away — the disguise's price.
                if (WearingCoat && daylight && g.Circle == "day"
                    && (!_coatSeenDay.TryGetValue(name, out var cd) || cd != Now.Day)
                    && Vector3.Distance(npc.transform.position, _player.transform.position) <= 6f)
                {
                    _coatSeenDay[name] = Now.Day;
                    g.Suspicion.Raise(0.05, "saw the new owner in that runner's coat in broad daylight");
                    g.Memory.Append(new MemoryEvent(Now, "observation", 0.5,
                        "Saw the new owner out in that heavy runner's coat, midday. Who dresses like that for bar work?"));
                }

                if (g.Loyalty < WarnLoyaltyFloor) continue;
                if (_lastWarnDay.TryGetValue(name, out var d) && d == Now.Day) continue;
                if (Vector3.Distance(npc.transform.position, _player.transform.position) > WarnRange) continue;
                foreach (var lead in _gossip.Mill.Leads("player"))
                {
                    if (lead.HolderId != name || Knowledge.Knows(lead.HolderId, lead.TopicKey)) continue;
                    Knowledge.Learn(lead, $"{name} warned you", Now);
                    // Closer friends deliver it closer — the same channel, warmer voice.
                    var intro = g.Loyalty >= 0.75
                        ? $"{name} grips your arm, voice low:"
                        : $"{name} pulls you aside:";
                    _ui.Toast($"{intro} \"People are saying {lead.Summary}. Thought you should hear it from me.\"");
                    _lastWarnDay[name] = Now.Day;
                    break; // one warning per encounter
                }
            }
        }

        /// A carrier loyal enough admits what they hold when you open a conversation;
        /// the admissions become known leads. Secrets travel the same channel:
        /// deep-trust confession of their own, looser sharing of someone else's
        /// (design-doc §6.3 — knowledge as loot, earned through relationships).
        /// Called once per dialogue open.
        public void LearnFromHost(string walkerName)
        {
            if (_gossip == null || _gossip.Mill == null) return;
            var g = _gossip.Mill.Get(walkerName);
            if (g == null) return;
            if (g.Loyalty >= RevealLoyaltyFloor)
                foreach (var lead in _gossip.Mill.Leads("player"))
                    if (lead.HolderId == walkerName)
                        Knowledge.Learn(lead, $"{walkerName} admitted it", Now);

            foreach (var s in HooksBook.TellableBy(walkerName, g.Loyalty,
                SecretsSetup.ConfessLoyaltyFloor, SecretsSetup.ShareLoyaltyFloor))
            {
                s.Learn(walkerName, Now);
                _ui?.Toast(s.OwnerId == walkerName
                    ? $"{walkerName} trusts you with something heavy. It's in your ledger now."
                    : $"{walkerName} tells you something about {s.OwnerId}. It's in your ledger now.", 8f);
            }
        }

        /// Context line for an authored beat involving this NPC — pending tonight,
        /// honored, or stood up. Injected so the character brings it up themselves.
        public string BeatContext(string walkerName)
        {
            foreach (var b in Beats.All)
            {
                if (b.HostId != walkerName) continue;
                if (b.State == BeatState.Pending && b.Day == Now.Day && _beatInvited.Contains(b.Id))
                    return $" You have invited the new owner to {b.Title.ToLowerInvariant()} tonight at {b.StartHour}:00 and you hope they come.";
                if (b.State == BeatState.Attended)
                    return $" The new owner came to {b.Title.ToLowerInvariant()} — it meant a lot to you.";
                if (b.State == BeatState.Skipped)
                    return $" You invited the new owner to {b.Title.ToLowerInvariant()} and they never showed. It stung; you don't hide it well.";
            }
            return "";
        }

        /// §6.4 escalation, voiced: how suspicious this NPC currently is shapes how
        /// they handle the conversation. Leashed NPCs never escalate.
        public string SuspicionBehaviorText(string walkerName)
        {
            var g = _gossip != null && _gossip.Mill != null ? _gossip.Mill.Get(walkerName) : null;
            if (g == null || g.Leashed) return "";
            switch (g.Suspicion.Level)
            {
                case SuspicionLevel.Uneasy:
                    return " Something about the new owner doesn't sit right; you probe with small, casual questions without letting on what you've heard.";
                case SuspicionLevel.Suspicious:
                    return " You have been comparing notes with others about the new owner; you test their story against what you've gathered and watch for the seams.";
                case SuspicionLevel.Confronting:
                    return " Enough. You confront the new owner directly and demand straight answers about what people are saying. You will not be brushed off this time.";
                default:
                    return "";
            }
        }

        /// Context for the secrets economy: what this NPC has confided or shared,
        /// and — if the player has used a hook on them — how that sits.
        public string SecretContext(string walkerName)
        {
            var sb = new System.Text.StringBuilder();
            foreach (var s in HooksBook.All)
            {
                if (!s.KnownToPlayer) continue;
                if (s.OwnerId == walkerName)
                {
                    var g = _gossip != null && _gossip.Mill != null ? _gossip.Mill.Get(walkerName) : null;
                    if (g != null && g.Leashed)
                        sb.Append($" The new owner knows your secret ({s.Summary}) and has made clear they will use it. You are cold, careful, compliant — and you say nothing about them to anyone.");
                    else if (s.HookSpent)
                        sb.Append($" The new owner knows your secret ({s.Summary}) and once called in a favor over it. You call it even, but it sits between you.");
                    else if (s.LearnedFrom == walkerName)
                        sb.Append($" You confided your secret to the new owner yourself ({s.Summary}). Saying it aloud relieved and terrified you.");
                    // Learned from a third party and never used: they don't know you know.
                }
                else if (s.LearnedFrom == walkerName)
                    sb.Append($" You told the new owner what you know about {s.OwnerId}: {s.Summary}");
            }
            return sb.ToString();
        }

        /// Context line so a loyal carrier actually SAYS what they've heard.
        public string HostRevealText(string walkerName)
        {
            if (_gossip == null || _gossip.Mill == null) return "";
            var g = _gossip.Mill.Get(walkerName);
            if (g == null || g.Loyalty < RevealLoyaltyFloor) return "";
            var held = new List<string>();
            foreach (var lead in _gossip.Mill.Leads("player"))
                if (lead.HolderId == walkerName) held.Add(lead.Summary);
            return held.Count == 0 ? ""
                : $" You have heard talk about the new owner ({string.Join("; ", held)}) and, out of loyalty, you admit what you've heard if it comes up.";
        }

        // ---- save/load (P5: the city's state is the save file) ----

        public string SavePath => System.IO.Path.Combine(Application.persistentDataPath, "ledger-save.json");

        Dictionary<string, object> ExtraFlags() => new Dictionary<string, object>
        {
            { "empire", Empire.Capture() },
            { "wearingCoat", WearingCoat }, { "osseiSpawned", OsseiSpawned },
            { "totalTakings", TotalTakings }, { "lastTakings", LastTakings },
            { "nightWitnesses", NightWitnesses }, { "anyCoatedWitnessed", AnyCoatedWitnessed },
            { "maxCoatedWitnessConf", MaxCoatedWitnessConf }, { "totalConfrontations", TotalConfrontations },
            { "jobPostedDay", _jobPostedDay }, { "lastClosedDay", _lastClosedDay },
            { "lastReflectedDay", _lastReflectedDay }, { "observedPeakHeat", ObservedPeakHeat },
            { "pp1", ActOne.Pp1Fired }, { "pp2", ActOne.Pp2Fired }, { "pp4", ActOne.Pp4Fired },
            { "posture", ActOne.Posture ?? "" },
            { "noorDrawers", ActOne.NoorDrawersEngaged }, { "noorBroken", ActOne.NoorDrawersBroken },
        };

        public string CaptureSave() =>
            SaveCodec.Capture(Now, Wallet, Campaign, Knowledge, HooksBook, Beats, _gossip.Mill, Debts, ExtraFlags());

        public void SaveNow(bool quiet = false)
        {
            if (_gossip == null || _gossip.Mill == null) return;
            try
            {
                System.IO.File.WriteAllText(SavePath, CaptureSave());
                if (!quiet) _ui?.Toast("The ledger is written. (Saved.)", 3f);
            }
            catch (System.Exception e) { Debug.LogError($"Save failed: {e.Message}"); }
        }

        public void DeleteSave()
        {
            try { if (System.IO.File.Exists(SavePath)) System.IO.File.Delete(SavePath); }
            catch (System.Exception e) { Debug.LogError($"Delete save failed: {e.Message}"); }
        }

        /// Overlay a saved city onto the freshly-authored one. Runs at the end of
        /// Start, after every authored system exists. NPC memories load themselves
        /// (markdown per character).
        void TryLoad()
        {
            try
            {
                if (SimMode.Days > 0) return; // the self-test always plays a fresh week
                if (!System.IO.File.Exists(SavePath)) return;
                var now = SaveCodec.Restore(System.IO.File.ReadAllText(SavePath),
                    Wallet, Campaign, Knowledge, HooksBook, Beats, _gossip.Mill, Debts, out var extra);
                Now = now;
                WearingCoat = FlagB(extra, "wearingCoat");
                TotalTakings = FlagI(extra, "totalTakings");
                LastTakings = FlagI(extra, "lastTakings");
                NightWitnesses = FlagI(extra, "nightWitnesses");
                AnyCoatedWitnessed = FlagB(extra, "anyCoatedWitnessed");
                MaxCoatedWitnessConf = FlagD(extra, "maxCoatedWitnessConf");
                TotalConfrontations = FlagI(extra, "totalConfrontations");
                _jobPostedDay = FlagI(extra, "jobPostedDay");
                _lastClosedDay = FlagI(extra, "lastClosedDay");
                _lastReflectedDay = FlagI(extra, "lastReflectedDay");
                ObservedPeakHeat = FlagD(extra, "observedPeakHeat");
                ActOne.Pp1Fired = FlagB(extra, "pp1");
                ActOne.Pp2Fired = FlagB(extra, "pp2");
                ActOne.Pp4Fired = FlagB(extra, "pp4");
                var posture = extra.TryGetValue("posture", out var po) ? po as string : null;
                ActOne.Posture = string.IsNullOrEmpty(posture) ? null : posture;
                ActOne.NoorDrawersEngaged = FlagB(extra, "noorDrawers");
                ActOne.NoorDrawersBroken = FlagB(extra, "noorBroken");
                if (extra.TryGetValue("empire", out var em)) Empire.Restore(MiniJson.AsObject(em));
                if (ActOne.NoorDrawersEngaged && !ActOne.NoorDrawersBroken)
                {
                    // Drawer contents ride the mill's suppression sets; rebuild the
                    // index of which topics the drawer (not a bribe) is holding.
                    var noorG = _gossip.Mill.Get("Noor");
                    if (noorG != null)
                        foreach (var t in noorG.Suppressed)
                            if (t.StartsWith("player.")) ActOne.NoorDrawerTopics.Add(t);
                }
                if (FlagB(extra, "osseiSpawned")) SpawnOssei();
                _ui?.Toast($"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)}. The street remembers where you left it.", 6f);
                if (Campaign.Verdict != Verdict.Ongoing) EndCampaign();
            }
            catch (System.Exception e) { Debug.LogError($"Load failed: {e.Message}"); }
        }

        static bool FlagB(Dictionary<string, object> d, string k) => d.TryGetValue(k, out var v) && v is bool b && b;
        static int FlagI(Dictionary<string, object> d, string k) => d.TryGetValue(k, out var v) && v != null ? System.Convert.ToInt32(v) : 0;
        static double FlagD(Dictionary<string, object> d, string k) => d.TryGetValue(k, out var v) && v != null ? System.Convert.ToDouble(v) : 0.0;

        void EndCampaign()
        {
            if (_jobMarker != null) { Destroy(_jobMarker); _jobMarker = null; }
            _ui?.ShowEnd(Campaign);
        }

        void SpawnJobMarker(Vector3 pos) =>
            _jobMarker = SpawnGlowMarker(pos, new Color(1f, 0.55f, 0.15f), "JobDrop");

        GameObject SpawnGlowMarker(Vector3 pos, Color color, string name)
        {
            var marker = GameObject.CreatePrimitive(PrimitiveType.Cube);
            marker.name = name;
            marker.transform.position = new Vector3(pos.x, 0.3f, pos.z);
            marker.transform.localScale = new Vector3(0.9f, 0.6f, 0.9f);
            var mat = marker.GetComponent<Renderer>().material;
            mat.color = color;
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", color * 2.2f);

            var glow = new GameObject("Glow");
            glow.transform.SetParent(marker.transform, false);
            glow.transform.localPosition = Vector3.up * 1.5f;
            var l = glow.AddComponent<Light>();
            l.type = LightType.Point;
            l.range = 7f;
            l.intensity = 2.2f;
            l.color = color;
            return marker;
        }

        void UpdateSun()
        {
            if (_sun == null) return;
            // 06:00 sunrise, 18:00 sunset mapped across a full rotation.
            float dayFraction = (Now.Hour * 60 + Now.Minute) / 1440f;
            float sunAngle = dayFraction * 360f - 90f;
            _sun.transform.rotation = Quaternion.Euler(sunAngle, 35f, 0);

            float daylight = Mathf.Clamp01(Mathf.Sin(dayFraction * Mathf.PI * 2f - Mathf.PI / 2f) + 0.15f);
            _sun.intensity = Mathf.Lerp(0.02f, 1.15f, daylight);
            _sun.color = Color.Lerp(new Color(1f, 0.55f, 0.35f), Color.white, daylight);

            // Gradient ambient (sky/equator/ground) + fog, lerped night→day. Richer than
            // a single flat ambient colour: surfaces pick up sky tint from above and a
            // warm bounce from the ground.
            RenderSettings.ambientSkyColor = Color.Lerp(new Color(0.05f, 0.06f, 0.10f), new Color(0.55f, 0.62f, 0.78f), daylight);
            RenderSettings.ambientEquatorColor = Color.Lerp(new Color(0.05f, 0.05f, 0.07f), new Color(0.45f, 0.46f, 0.48f), daylight);
            RenderSettings.ambientGroundColor = Color.Lerp(new Color(0.02f, 0.02f, 0.03f), new Color(0.22f, 0.20f, 0.18f), daylight);
            RenderSettings.fogColor = Color.Lerp(new Color(0.04f, 0.05f, 0.08f), new Color(0.62f, 0.66f, 0.72f), daylight);
            WorldBuilder.SetLampsEnabled(daylight < 0.25f);
            WorldBuilder.SetWindowsLit(daylight < 0.35f); // windows warm up a touch before the street lamps
        }
    }
}
