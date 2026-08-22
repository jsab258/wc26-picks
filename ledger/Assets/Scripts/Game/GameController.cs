using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Owns the game clock, day/night cycle, and world orchestration for the
    /// M0 tech spike: one graybox block, a player, three scheduled NPCs, and
    /// Lena (the full conversational character).
    public partial class GameController : MonoBehaviour
    {
        public float MinutesPerRealSecond = 2f; // 1 game day = 12 real minutes (sim mode overrides)

        public GameTime Now { get; private set; } = new GameTime(1, 9, 0);
        public CostTracker Cost { get; } = new CostTracker();

        // One shared client for world-level LLM work that belongs to nobody in
        // particular — today the intent router (roadmap M6.5), tomorrow the
        // Director. Characters keep their own clients; this is the game's.
        // Null without a key, and every consumer must degrade rather than fail.
        AnthropicClient _worldLlm;
        bool _worldLlmTried;
        public ILlmClient Llm
        {
            get
            {
                if (_worldLlm == null && !_worldLlmTried)
                {
                    _worldLlmTried = true;
                    var key = Secrets.LoadAnthropicKey();
                    // Same café-wifi bounds as the character clients — the
                    // policy and its reasoning live on ConversationHost.
                    if (!string.IsNullOrEmpty(key))
                        _worldLlm = new AnthropicClient(key,
                            System.TimeSpan.FromSeconds(ConversationHost.LlmTimeoutSeconds))
                            { MaxRetries = ConversationHost.LlmMaxRetries };
                }
                return _worldLlm;
            }
        }

        /// F2 re-key: drop the world client so the next use picks up the new key.
        public void ResetLlm()
        {
            _worldLlm?.Dispose();
            _worldLlm = null;
            _worldLlmTried = false;
        }

        // Two currencies that resist mixing (design-doc §6.7): the bar pays clean,
        // the outfit pays dirty, and dirty only becomes clean by washing through
        // the till. PlayerCash stays as the "what I can hand over right now" total.
        public Wallet Wallet { get; } = new Wallet(250);
        public int PlayerCash => Wallet.Total;

        public Campaign Campaign { get; } = new Campaign();

        /// M18. The rooms above the pub and the two people in them.
        public readonly HouseholdHost Household = new HouseholdHost();

        /// M18. Whoever is walking at your shoulder, and everything they know.
        public readonly CompanionHost Companion = new CompanionHost();

        /// HOW WELL EACH PERSON ON THE STREET KNOWS THE PLAYER'S FACE.
        ///
        /// `Witnesses.Resolve` and `ViolenceHost.Commit` have both taken a
        /// familiarity function since the perception engine was written, and
        /// **no caller has ever passed one** — so it defaulted to null, every
        /// witness scored zero, and `Perception.IdRung`'s top rung was
        /// unreachable in every code path in the game. Four staged deeds,
        /// forty-nine witnesses, `deedBestRung=1`: a city of strangers, every
        /// run, for weeks. Rule 6 exactly — built, tested in Core, never
        /// called.
        ///
        /// Assembled here rather than in either caller because this object is
        /// the only one holding all four facts, and because two callers
        /// building it separately is how they drift.
        public System.Func<NpcWalker, double> FamiliarityWithPlayer => npc =>
        {
            if (npc == null) return Acquaintance.Stranger;

            bool home = false;
            foreach (var d in Household.Book.People)
                if (d != null && d.Name == npc.DisplayName) { home = true; break; }

            return Acquaintance.Of(
                sharesYourHome: home,
                walksWithYou: Companion.Walking == npc,
                inTheSocialGraph: _gossip != null && _gossip.IsCast(npc),
                hasHeardOfYou: _gossip != null && _gossip.HasHeardOfPlayer(npc));
        };
        public PlayerKnowledge Knowledge { get; } = new PlayerKnowledge();
        // Act I's authored spine state (act1-draft.md): pressure-point flags,
        // the posture answer, Noor's two drawers.
        public ActOneState ActOne { get; } = new ActOneState();

        // Empire v1 (open-city-spec §2): the other ledger. Businesses, crew,
        // rackets, and the Dockside street arm watching it all grow.
        public EmpireBook Empire { get; } = EmpireSetup.Build();

        // The district's money (roadmap M7). Squeezing the street makes the
        // street poorer, and a poorer street spends less in your bar — so the
        // night's dirty income quietly costs you clean income in the morning.
        public Economy Economy { get; } = EconomySetup.Build();

        // Act II — The Squeeze (act2-draft.md, approved): the authored spine
        // laid over the empire the player actually built.
        public ActTwoState ActTwo { get; } = new ActTwoState();

        // The day job (doc §6.6): courier shifts at Meridian Parcel. Open-mode
        // only for now — Act I's week belongs to the bar. The dispatcher's card
        // (Zlata, cast-tier1-batch2.md) slots in on approval; the system stands.
        public DayJob Job { get; } = new DayJob();
        GameObject _dispatchMarker, _shiftMarker;
        int _dispatchToastDay;
        int _shiftStop;
        static readonly Vector3 DispatchBoard = new Vector3(20, 0, 8);
        static readonly Vector3[] ShiftStops =
        {
            new Vector3(10, 0, -14),   // the market corner
            new Vector3(20, 0, 8),     // back to the board, signed sheet
        };
        public Vector3? DayJobTargetPos =>
            _shiftMarker != null ? (Vector3?)_shiftMarker.transform.position
            : _dispatchMarker != null ? (Vector3?)_dispatchMarker.transform.position : null;
        public SecretsBook HooksBook { get; } = SecretsSetup.Build();
        // Mickey's book of uncollectable debts (design-doc §1: part of the inheritance).
        public DebtBook Debts { get; } = new DebtBook();
        /// What everybody on this street can actually lay hands on (roadmap M13).
        /// Willing is not the same as able, and the difference is a conversation.
        public PurseBook Purses { get; } = new PurseBook();
        /// Who is hurt, who is carrying it, and who is not finished with whom
        /// (roadmap M11). Violence is deferred as a thing you DO and present as
        /// a thing that has happened to you.
        public HarmBook Harm { get; } = new HarmBook();
        /// The player's name, and the gradient of what people call them
        /// (decided 2026-07-27, delegated by Jafar). Tom Novak.
        public PlayerIdentity Me { get; } = new PlayerIdentity();

        /// The sentence appended to every conversation's scene telling the model
        /// what THIS person calls the player. One place, rather than the same
        /// instruction hand-written into thirty character cards.
        /// The conversation host for somebody, by gossiper id or card name.
        /// The panel layer, for the sim's UI smoke test. Read-only to everybody
        /// else; the game talks to the UI through _ui as it always did.
        public DialogueUI Ui { get; private set; }

        public ConversationHost HostFor(string whoId)
        {
            if (string.IsNullOrEmpty(whoId)) return null;
            foreach (var h in _hosts)
            {
                if (h == null) continue;
                if (h.Card != null && (h.Card.Id == whoId || h.Card.Name == whoId)) return h;
                var walker = h.GetComponent<NpcWalker>();
                if (walker != null && walker.DisplayName == whoId) return h;
            }
            return null;
        }

        public string AddressLine(string gossiperId)
        {
            var g = _gossip != null && _gossip.Mill != null ? _gossip.Mill.Get(gossiperId) : null;
            var name = Me.AddressBy(g);
            return name == Me.Unplaced
                ? $"You do not know this person's name. You think of them as {Me.Unplaced}, and that is how you would refer to them."
                : $"You call them {name}.";
        }
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

        /// Where the currently open beat is, if there is one and we know the
        /// spot. The sim reads this to walk the bot there.
        ///
        /// Exposed because of what CI was reporting: every authored beat came
        /// back Skipped, every run, and the gate passed — it only ever asked
        /// that no beat was left PENDING, and a skipped beat is resolved. So
        /// four hand-written scenes and the whole cinematic framing layer
        /// built on them had never executed in-engine, and nothing said so.
        public Vector3? OpenBeatSpot
        {
            get
            {
                // Looks AHEAD, so somebody who means to go sets off in time.
                // The window is two hours and the sim's clock runs at twenty
                // game-minutes a real second, which makes it six real seconds
                // — not a walk, a teleport requirement.
                var open = Beats.Soon(Now, 3);
                if (open == null) return null;

                // THE HOST IF THERE IS ONE, the stored spot otherwise.
                //
                // Some beats carry hand-authored coordinates rather than a
                // captured walker position, and an authored point can sit
                // inside a doorway, behind a railing, or on the wrong side of
                // a wall — nine days of CI got no closer than eleven metres
                // to one and never attended a single beat. A host walker is
                // standing somewhere a person can walk to, by construction,
                // because they walked there.
                //
                // This is also the better game: the invitation is to meet
                // somebody, and if they have moved you go where they are.
                var host = WalkerForHost(open.HostId);
                if (host != null)
                {
                    // They stand still once the invitation is OPEN — not
                    // during the lead-in, because Ada freezing at seven for a
                    // ten o'clock tea is its own kind of wrong. Before then
                    // she is simply somewhere to head towards.
                    if (open.InWindow(Now))
                    {
                        host.WaitingAsHost = true;
                        _waitingHost = host;
                    }
                    return host.transform.position;
                }
                return _beatSpots.TryGetValue(open.Id, out var spot) ? spot : (Vector3?)null;
            }
        }
        /// Whether an invitation is currently on screen to walk up to.
        ///
        /// Attendance is gated on the marker existing, so a run that never
        /// creates one and a run that never reaches one report identically —
        /// which is how three separate fixes were aimed at the wrong half of
        /// the problem.
        public bool HasBeatMarker => _beatMarker != null;

        /// Released when the window closes, so being stood up costs the host
        /// an evening of standing there rather than the rest of the game.
        NpcWalker _waitingHost;

        void ReleaseWaitingHost()
        {
            if (_waitingHost == null) return;
            _waitingHost.WaitingAsHost = false;
            _waitingHost = null;
        }

        /// How close counts as turning up. See the note at the attendance
        /// check for why it is not 2.5.
        public const float BeatAttendMetres = 3.2f;

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

        /// The people you can actually talk to, read-only. The sim needs one to
        /// tell a lie to, and reaching into a private field from another class
        /// is how a second source of truth gets born.
        public IReadOnlyList<ConversationHost> Hosts => _hosts;
        ConversationHost _lena;
        ConversationHost _noor;
        GossipDirector _gossip;
        DialogueUI _ui;
        PlayerController _player;
        int _lastReflectedDay;
        int _lastAgedHour = -1;

        /// Where the player stood at the hour the rival's line rings, and which
        /// day that sample belongs to. `-1` means the ring hour has not elapsed
        /// yet this run — which is a different answer from "he was somewhere
        /// else", and the summons could not tell them apart because it was
        /// reading a live transform at an unrelated hour.
        public Vector3 PlayerAtRing { get; private set; }
        public int PlayerAtRingDay { get; private set; } = -1;

        // Detective Ellis (design-doc §8): spawns once the street's talk gets loud
        // enough to reach a precinct desk; while she works it, rumors refuse to die.
        public bool EllisSpawned { get; private set; }
        public double ObservedPeakHeat { get; private set; }
        ConversationHost _ossei;
        NpcWalker _osseiWalker;

        // §6.5: heat is what witnesses actually saw AND TOLD. When a first-hand
        // witness crosses Ellis's path, she interviews them — unless their silence
        // was bought or leashed first. The race the whole game is about.
        public List<string> EllisInterviews { get; } = new List<string>();
        readonly HashSet<string> _interviewed = new HashSet<string>();

        // Combat phase 3b. The register of killings, and the police pressure
        // that follows from it. Empty in the overwhelming majority of
        // playthroughs — a whole game can and should be finishable without
        // ever opening it.
        public HomicideBook Homicides { get; } = new HomicideBook();

        /// A REGISTERED PLACE'S CURRENT POSITION, so a routine stops repeating
        /// a coordinate that can move underneath it.
        ///
        /// `StreetMap.SetPlacesBackFromRoads` moves an address that stands in a
        /// carriageway onto the pavement, and it moved thirty-two of them. Six
        /// cast waypoints had been hand-written to sit EXACTLY on a place — the
        /// pawnshop, the teahouse, the boarding house, the ferry, the crossing,
        /// the cab rank — and were stranded by up to 5.6 metres the moment that
        /// landed. Rita would have kept her shop hours three and a half metres
        /// from her own shop.
        ///
        /// Found by grepping for what AGREED with the thing I changed rather
        /// than by a build coming back wrong, which is the only reason it cost
        /// nothing. Two of the six fixed themselves when corners were exempted;
        /// these four had to be pointed at the place instead.
        ///
        /// Falls back to the raw coordinate rather than to the origin: a
        /// mistyped id should put somebody in the wrong street, not in the sea,
        /// and it logs so the typo is findable.
        /// A SPOT NEAR THE BAR DOOR THAT IS NOT IN THE ROAD.
        ///
        /// Six of the cast's routines are authored as offsets from
        /// `WorldBuilder.BarDoor` — "across from the bar, coat still on", "one
        /// drink, loudly" — and the intent is exactly right: people gather
        /// outside the pub and that is where the cast belongs. Three of the six
        /// land in Hook Street, because the offsets were picked by eye and
        /// nothing told them where the kerb is.
        ///
        /// `StreetMap.OffTheCarriageway` is the same rule the addresses use, so
        /// the pavement is defined once. The bar door itself is already clear,
        /// so this only ever moves the offset, and it moves it perpendicular —
        /// a person's position ALONG the street survives.
        public static Vector3 NearBar(float dx, float dz)
        {
            var at = WorldBuilder.BarDoor + new Vector3(dx, 0, dz);
            Ledger.Core.StreetMap.OffTheCarriageway(at.x, at.z, out var x, out var z);
            return new Vector3((float)x, 0, (float)z);
        }

        public static Vector3 PlaceAt(string id)
        {
            var p = HookMap.Get(id);
            if (p != null) return new Vector3((float)p.X, 0, (float)p.Z);
            Debug.LogError($"GameController.PlaceAt: no registered place \"{id}\" — "
                           + "a routine is pointing at an address that does not exist.");
            return Vector3.zero;
        }
        readonly HashSet<string> _deadIds = new HashSet<string>();
        public bool IsAlive(string id) => !_deadIds.Contains(id);
        /// THE DAY IS PASSED, and without it the redirect does nothing.
        ///
        /// `HomicideBook.RedirectReliefOn` returns zero for a caller that cannot
        /// say what day it is — deliberately, because a discount nobody asked
        /// for is worse than no discount — so this property is the difference
        /// between `PointAt` being wired and being decorative. That is the whole
        /// rule-6 failure mode in one argument: the mechanism existed, the
        /// caller existed, and the value never reached it.
        public Inquiry PoliceInquiry =>
            _gossip?.Mill == null ? Inquiry.None : Homicides.Stage(_gossip.Mill, IsAlive, Now.Day);

        /// Every evening of the run, and what was open on it. Static because
        /// the verdict reads it once at the end and a per-instance counter
        /// would be lost to the scene reload the Fall performs.
        public static readonly LooseEnds.Tally LooseEndsTally = new LooseEnds.Tally();

        /// HOW MANY OF THE SIX TIERS ARE ACTUALLY FED, and the denominator is
        /// the point (rule 3b). `Rumour` never appearing in a run's breakdown
        /// means "no rumours were in flight" only if the rumour tier is wired;
        /// otherwise it means nothing at all, and the two read identically.
        /// Three of six today: the law, the crew and Mickey's book. The
        /// promise, the talk and the change of heart need accessors that do
        /// not exist yet as single reads, and inventing them here would be
        /// three more numbers nobody had measured.
        public const int LooseEndTiersFed = 3;
        public const int LooseEndTiers = 6;

        /// THE EVENING, ASSEMBLED FROM WHAT THE GAME ACTUALLY HOLDS.
        ///
        /// Deliberately a plain struct of primitives handed to Core rather
        /// than Core reaching into the hosts: it keeps the choosing testable
        /// without Unity, which is where all thirty-one of its checks live.
        LooseEnds.Evening EveningState(int dayClosed)
        {
            var e = new LooseEnds.Evening { Day = dayClosed };

            // THE LAW, AND THE FIRST VERSION READ A NAME THAT IS NEVER CLEARED.
            //
            // It asked `string.IsNullOrEmpty(Homicides.PointedAt)` — the
            // detective is on you while nobody else is named. That is the right
            // idea and the wrong field. `PointedAt` is set when a charge sticks
            // and NOTHING EVER UNSETS IT: only the RELIEF expires, after
            // `RedirectHolds` days. So one successful redirect, ever, turned
            // this tier off permanently.
            //
            // The run said so and the run is the only reason I know. `inquiry`
            // reached MANHUNT, `pressNamed=1` — the paper had named the player —
            // `homNamed=9`, and the evening thread still reported the law as
            // not open, on every one of six evenings. The denominator built
            // yesterday is what made that visible: `open6/1of6` says exactly
            // one tier was ever live, so the four above and below it were not
            // merely outranked.
            //
            // Reading the live relief instead asks the question the tier means:
            // is there a redirect PULLING HER AWAY RIGHT NOW.
            var stage = PoliceInquiry;
            e.InquiryStage = (int)stage;
            e.InquiryNamesYou = stage != Inquiry.None
                && Homicides.RedirectReliefOn(dayClosed) <= 0;
            e.InquiryAbout = Homicides.PressureWhy(_gossip?.Mill, IsAlive, Now.Day);

            // THE CREW. Loyalty lives on the GOSSIPER, not on `CrewMember` —
            // a crew member is a person on this street who happens to work for
            // you, which is §6.5's whole point — so the floor and the value
            // both come from `Empire` rather than from a second definition.
            double worst = double.MaxValue;
            foreach (var c in Empire.Crew)
            {
                if (c == null || c.Departed) continue;
                var g = _gossip?.Mill?.Get(c.Id);
                if (g == null) continue;
                if (g.Loyalty >= worst) continue;
                worst = g.Loyalty;
                e.CrewNearestBreaking = c.Name;
                e.CrewLoyalty = g.Loyalty;
            }
            e.CrewBreakingPoint = Empire.PoachLoyaltyFloor;

            // MICKEY'S BOOK. The largest name still outstanding, because a
            // player with six open debts should be pointed at the one worth
            // walking across town for.
            Debtor biggest = null;
            foreach (var d in Debts.All)
            {
                if (d == null || !d.Outstanding) continue;
                if (biggest == null || d.Amount > biggest.Amount) biggest = d;
            }
            if (biggest != null)
            {
                e.OwedAmount = biggest.Amount;
                e.OwedBy = biggest.Name;
                e.OwedLastAskedDay = biggest.LastAskedDay;
            }

            return e;
        }
        Inquiry _lastInquiry = Inquiry.None;

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

        /// Where tonight's drop WILL post, knowable before 22:00. The
        /// rotation is deterministic by day, which in-fiction is a pattern
        /// any runner learns inside a week — and it is what lets the sim
        /// bot pre-position instead of starting a 29m walk the moment a
        /// window that lasts twelve real seconds opens (the measured cause
        /// of most jobRan misses: the harness's 20-minutes-per-second
        /// compression makes a four-hour window physically unfair to a bot
        /// that only learns the address when the marker spawns).
        public Vector3 DropPointFor(int day) => DropPoints[day % DropPoints.Length];

        public GossipDirector Gossip => _gossip;
        public PlayerController Player => _player;
        public Vector3? ActiveJobPos => _jobMarker != null ? (Vector3?)_jobMarker.transform.position : null;

        /// An authored beat, said out loud AND framed.
        ///
        /// Hooked here because this is the one funnel every authored moment
        /// already goes through — the pressure points, Ellis's offer, the
        /// audit opening. No new call sites, and a beat that forgets to ask
        /// for framing cannot exist.
        ///
        /// The WEIGHT comes from how long the line asks to be held, which the
        /// writing already declares: an ordinary note takes six seconds and
        /// the audit opening takes thirteen. That is the author saying how
        /// much this matters, in a number that was already there.
        public void ToastLine(string line, float seconds = 6f)
        {
            _ui?.Toast(line, seconds);
            // Under a curtain there is nothing to frame, and a push-in on
            // black is a push-in nobody sees.
            // `SimMode.Days > 0` used to be in this condition, and it meant
            // the entire cinematic layer had never executed in a verified
            // build — Push, HoldSeconds, Authority, the shot sizes, the
            // 180-degree rule, none of it. The reason was real: a push-in
            // part-way through a measured screenshot would move the luminance
            // the lighting gate reads.
            //
            // But that is an argument for suppressing framing AROUND A
            // SCREENSHOT, not for switching it off for the whole run. The sim
            // aborts any live beat before it renders, which is a smaller
            // exclusion and leaves the layer covered.
            if (ScreenCurtain.Busy || _player == null) return;
            double weight = Feel.Clamp01((seconds - 6f) / 10.0);
            var other = NearestInShot();
            _player.Beat.Begin(weight, other != null);

            // AND THE LINE THIS BEAT IS ABOUT. The 180-degree rule has been
            // computed and never consulted since it was written; this is the
            // first caller, and it MEASURES rather than enforces — the beat
            // pulls in along the rig's own line and cannot cross by itself, so
            // whether the follow rig crosses is an open question and a policy
            // written before the answer is a threshold nobody measured.
            var eye = Camera.main;
            if (other != null && eye != null)
            {
                var a = _player.transform.position;
                var b = other.transform.position;
                var c = eye.transform.position;
                _player.Beat.HoldTheLine(a.x, a.z, b.x, b.z, c.x, c.z);
            }
        }

        /// The person this shot is about, or null if it is about the street.
        ///
        /// It returned a BOOL and now returns who, because the 180-degree rule
        /// needs the second subject and "somebody is nearby" cannot supply a
        /// line. NEAREST rather than first-found: the line has to be the one
        /// the player is actually in a scene with, and picking by list order
        /// is the fault this project found in two other places tonight.
        NpcWalker NearestInShot()
        {
            if (_player == null) return null;
            NpcWalker best = null;
            float bestD = 10f;
            foreach (var n in _npcs)
            {
                if (n == null || !n.isActiveAndEnabled) continue;
                float d = Vector3.Distance(n.transform.position, _player.transform.position);
                if (d <= bestD) { bestD = d; best = n; }
            }
            return best;
        }

        /// Quit to the main menu, under black. The city goes away and the menu
        /// arrives at the moment nothing is visible — tearing both down on the
        /// click cut from a lit street to a dark field in a single frame, and
        /// that was the last hard cut §8 had left.
        ///
        /// BY SCENE RELOAD, since 15 Aug, because the city is parentless root
        /// objects and destroying this controller never touched it. The old
        /// body of this method destroyed the UI and itself and created the
        /// menu over a still-standing city — so "New game" from that menu ran
        /// `BuildBlock` on top of the old streets and doubled the geometry.
        /// Bootstrap's root sweep is the one real teardown; every session end
        /// goes through it now (the end screen's R already did).
        public void LeaveToMenu()
        {
            // A second click while one is running does nothing rather than
            // tearing the world down twice.
            Blackout.Cover(() =>
            {
                Time.timeScale = 1f;
                UnityEngine.SceneManagement.SceneManager.LoadScene(
                    UnityEngine.SceneManagement.SceneManager.GetActiveScene().buildIndex);
            });
        }

        void Start()
        {
            WorldBuilder.BuildBlock();
            _sun = WorldBuilder.BuildSun();
            Weather.Ensure(this);   // rain, wetness, and the fog that follows them

            // ON GROUND THAT IS ACTUALLY CLEAR, not on a remembered
            // coordinate. (0, -8) was the pavement outside the bar when a
            // block held one building per edge; the topology stretch filled
            // the blocks — 60 parcels to 376 — and a terrace row landed on
            // the spawn, so the first frame of the game was the inside of a
            // wall. The wish stays exactly where it was; if something now
            // stands there, the nearest clear spot wins, which survives the
            // next re-plan as well as this one.
            var wish = new Vector3(0, 1.2f, -8);
            var spawnAt = wish;
            if (!WorldBuilder.PointClear(spawnAt, 0.6f))
            {
                bool found = false;
                for (float r = 2f; r <= 16f && !found; r += 2f)
                    for (int a = 0; a < 16 && !found; a++)
                    {
                        float th = a * Mathf.PI * 2f / 16f;
                        var probe = wish + new Vector3(Mathf.Cos(th) * r, 0, Mathf.Sin(th) * r);
                        if (!WorldBuilder.PointClear(probe, 0.6f)) continue;
                        spawnAt = probe; found = true;
                    }
                Debug.Log($"GameController: spawn moved off built ground to "
                          + $"{spawnAt.x:0.0},{spawnAt.z:0.0} (wanted {wish.x:0.0},{wish.z:0.0}) found={found}");
            }
            var player = PlayerController.Spawn(spawnAt);
            // AND FACING DOWN THE STREET. The spawn point was clear — the
            // build's log carries no "moved off built ground" line — and the
            // player-height still came back as a close-up of brick anyway,
            // because standing in the open facing a wall looks identical to
            // standing inside one. A first frame is a first impression, and
            // with the blocks now full there is a facade within a few metres
            // of almost anywhere. So the opening view is aimed along the
            // nearest carriageway, which is where the street is.
            if (Ledger.Core.StreetMap.NearestOnRoad(spawnAt.x, spawnAt.z,
                    out var rx, out var rz, out _))
            {
                var along = new Vector3((float)rx - spawnAt.x, 0, (float)rz - spawnAt.z);
                if (along.sqrMagnitude > 0.04f)
                {
                    // Along the road, not at it: turn the offset ninety
                    // degrees so the player looks DOWN the street rather than
                    // across it into the opposite frontage.
                    var look = new Vector3(-along.z, 0, along.x).normalized;
                    player.transform.rotation = Quaternion.LookRotation(look, Vector3.up);
                }
            }
            _player = player;
            // The gait reads the harm system directly, so an injury we have
            // simulated since day one finally shows up in how he walks.
            player.Game = this;
            // The alley sounds like an alley, from the street network we
            // already had — no acoustic volumes were authored for this.
            RoomTone.Ensure(player.Eye != null ? player.Eye.transform : null);
            // The wet road only reflects when there is something to reflect,
            // and only re-renders when the player has actually gone
            // somewhere. Follows the body rather than the eye so that looking
            // around does not drag the probe with it.
            WetReflections.Ensure(player.transform);
            // Grain, vignette and bloom. Fails closed to an unfiltered image
            // if the shader is missing, because an art effect that can break
            // the picture must never be able to.
            FilmGrade.Ensure(player.Eye);

            _npcs.Add(NpcWalker.Spawn("Rocco", new Color(0.75f, 0.3f, 0.25f), new[]
            {
                (new GameTime(0, 7, 0), new Vector3(18, 0, 14)),   // docks
                (new GameTime(0, 12, 0), NearBar(2, 1)),
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

            _npcs.Add(NpcWalker.Spawn("Marla", new Color(0.8f, 0.6f, 0.3f), new[]
            {
                (new GameTime(0, 8, 0), new Vector3(10, 0, -14)),  // market stall
                (new GameTime(0, 18, 0), new Vector3(-12, 0, 14)), // home
            }));
            _npcs.Add(NpcWalker.Spawn("Joey", new Color(0.35f, 0.45f, 0.5f), new[]
            {
                (new GameTime(0, 6, 0), new Vector3(18, 0, 14)),   // docks
                (new GameTime(0, 20, 0), NearBar(3, -1)),
                (new GameTime(0, 23, 0), new Vector3(16, 0, 12)),  // home by the water
            }));
            _npcs.Add(NpcWalker.Spawn("Victor", new Color(0.6f, 0.5f, 0.3f), new[]
            {
                (new GameTime(0, 9, 0), PlaceAt("pawnshop")),      // his shop, now standing
                (new GameTime(0, 13, 0), new Vector3(10, 0, -14)), // errands at the market corner
                (new GameTime(0, 17, 0), PlaceAt("teahouse")),     // the teahouse, per his card
                (new GameTime(0, 22, 0), new Vector3(-16, 0, -12)), // home on the west row
            }));

            // The promoted ring: the district's own operators, on their beats.
            _npcs.Add(NpcWalker.Spawn("Ferko", new Color(0.45f, 0.4f, 0.25f), new[]
            {
                (new GameTime(0, 11, 0), new Vector3(24, 0, -10)),  // the cab rank
                (new GameTime(0, 18, 0), new Vector3(0, 0, -8)),    // trawling the crossing for fares
                (new GameTime(0, 23, 0), new Vector3(24, 0, -10)),  // sleeps in the cab
            }));
            _npcs.Add(NpcWalker.Spawn("Rita", new Color(0.5f, 0.35f, 0.45f), new[]
            {
                (new GameTime(0, 10, 0), PlaceAt("pawnshop")),      // the pawnshop back room
                (new GameTime(0, 15, 0), new Vector3(18, 0, 14)),   // the docks, collecting
                (new GameTime(0, 20, 0), new Vector3(-20, 0, -16)), // home in the south tenements
            }));
            _npcs.Add(NpcWalker.Spawn("Vesna", new Color(0.35f, 0.42f, 0.6f), new[]
            {
                (new GameTime(0, 7, 0), new Vector3(-34, 0, 10)),   // the chapel
                (new GameTime(0, 12, 0), new Vector3(10, 0, -14)),  // the market for the Father's table
                (new GameTime(0, 16, 0), new Vector3(-34, 0, 10)),
                (new GameTime(0, 21, 0), PlaceAt("boarding_house")),// the boarding house
            }));
            _npcs.Add(NpcWalker.Spawn("Tibor", new Color(0.55f, 0.55f, 0.4f), new[]
            {
                (new GameTime(0, 8, 0), new Vector3(36, 0, 12)),    // the customs shed
                (new GameTime(0, 13, 0), new Vector3(34, 0, 6)),    // the harbormaster's office
                (new GameTime(0, 19, 0), new Vector3(-18, 0, 20)),  // home in the north tenements
            }));

            // Tier-1 batch 2 (approved 2026-07-26): the people the story needs
            // standing somewhere. The three organization heads are NOT here —
            // they arrive only when their arm's attention earns the meeting.
            _npcs.Add(NpcWalker.Spawn("June", CastTier1.JuneColor, new[]
            {
                (new GameTime(0, 15, 0), new Vector3(-2, 0, 1)),    // across from the bar, coat still on
                (new GameTime(0, 17, 0), new Vector3(-34, 0, 10)),  // the chapel, for a while
                (new GameTime(0, 20, 0), PlaceAt("ferry_stop")),    // the ferry, back across town to her shift
            }));
            _npcs.Add(NpcWalker.Spawn("Emil", CastTier1.EmilColor, new[]
            {
                (new GameTime(0, 7, 0), new Vector3(-34, 0, 10)),   // the chapel
                (new GameTime(0, 13, 0), new Vector3(10, 0, -14)),  // the market, walking among people
                (new GameTime(0, 16, 0), new Vector3(-34, 0, 10)),
            }));
            _npcs.Add(NpcWalker.Spawn("Zlata", CastTier1.ZlataColor, new[]
            {
                (new GameTime(0, 7, 30), DispatchBoard),            // the board, before anyone else
                (new GameTime(0, 14, 0), new Vector3(18, 0, 14)),   // chasing a late courier at the docks
                (new GameTime(0, 17, 0), DispatchBoard),
                (new GameTime(0, 20, 0), NearBar(4, 2)), // one drink, loudly
            }));
            _npcs.Add(NpcWalker.Spawn("Hal", CastTier1.HalColor, new[]
            {
                (new GameTime(0, 10, 0), new Vector3(31, 0, 21)),   // the coin shop that sells no coins
                (new GameTime(0, 19, 0), new Vector3(31, 0, 21)),
            }));

            // The generated district population (open-city-spec §3): the batch
            // walks. Brains arrive via the generic host loop below; secrets join
            // the book so the leverage economy scales with the street.
            foreach (var w in Tier2Batch.SpawnWalkers()) _npcs.Add(w);
            foreach (var s in Tier2Batch.Secrets()) HooksBook.Add(s);

            // The suppliers walk (roadmap M7). They are not table rows: Mitch
            // comes on Thursdays whether you are awake or not, and knows to the
            // day when he was last paid.
            SpawnSupplier("drayman", SupplierCast.MitchCard, SupplierCast.MitchColor,
                SupplierCast.MitchSchedule, "On his round along Hook Street, talking with the new landlord.");
            SpawnSupplier("wholesaler", SupplierCast.TonyCard, SupplierCast.TonyColor,
                SupplierCast.TonySchedule, "At the market corner, talking with the new landlord.");

            var lenaWalker = NpcWalker.Spawn("Lena", new Color(0.55f, 0.4f, 0.6f), new[]
            {
                (new GameTime(0, 8, 0), WorldBuilder.BarCounter),
                (new GameTime(0, 23, 30), NearBar(-1, -1)),
            });
            _npcs.Add(lenaWalker);
            _lena = lenaWalker.gameObject.AddComponent<ConversationHost>();
            _lena.Initialize(this, LenaSetup.CardMarkdown, LenaSetup.SeedKnowledge, LenaSetup.SeedMemories);
            _lena.SceneContext = "Behind the bar, talking with the new owner.";
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
                       $"Yesterday the bar took in £{LastTakings}.{thin} {mood}{HostRevealText("Lena")}{SecretContext("Lena")}{SuspicionBehaviorText("Lena")}";
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
                (new GameTime(0, 20, 0), NearBar(-2, 2)),
                (new GameTime(0, 23, 0), new Vector3(-14, 0, 12)),  // home
            });
            _npcs.Add(noorWalker);
            _noor = noorWalker.gameObject.AddComponent<ConversationHost>();
            _noor.Initialize(this, NoorSetup.CardMarkdown, null, null);
            _noor.SceneContext = "On her rounds of Hook Street, notebook half out of a pocket, talking with the new landlord.";
            _noor.ExtraContext = () =>
            {
                var sb = new System.Text.StringBuilder();
                sb.Append($"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week on Hook Street. ");
                sb.Append($"Talk about the new owner around the street is {StreetWord(CurrentHeat)}.");
                if (Now.Day <= 2) sb.Append(" You have only just met the new owner.");
                if (EllisSpawned) sb.Append(NoorSetup.EllisContextLine); // PP6: two collectors, different rules
                if (Campaign.OpenMode && Empire.Rival.Stage >= 2)
                    sb.Append(" You have heard the Dockside organization is taxing the new owner's street — protection, on Hook Street, in this day and age. That is a story, and you are pulling at it the way you pull at the fire.");
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
                var member = CastSetup.Get(npc.DisplayName) ?? Tier2Setup.Get(npc.DisplayName)
                    ?? CastTier1.Get(npc.DisplayName) ?? Tier2Batch.Get(npc.DisplayName);
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
            Ui = _ui;

            _gossip = gameObject.AddComponent<GossipDirector>();
            _gossip.Begin(this, _npcs, _hosts);
            _gossip.OnEvents = OnGossipEvents;

            // The crowd on top of the cast (roadmap M9): three thousand people
            // who are records until the player's attention reaches them. The mid
            // band has no body, so the gossip director is told where to find them.
            BuildPopulation();
            _gossip.ExtraPosition = CrowdPositionOf;

            // Traffic (roadmap M12). Built after the population because it takes
            // the same city seed: the same street should have the same bus on it
            // every time you load the same save.
            BuildTraffic();
            BuildSignalHeads();
            BuildPhones();

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
                Id = "toast", HostId = "Rocco", Title = "A drink for Mickey", Day = 5, StartHour = 22, EndHour = 24,
                InviteText = "Rocco, quiet at the door: \"I never drank to Mickey proper. Not once since we buried him. Tonight I do. Sit with me, boss — ten o'clock, my front step.\"",
            });
            // His home stoop, not the bar door: attendance must be a deliberate trip,
            // never a side effect of walking out of your own bar.
            _beatSpots["toast"] = new Vector3(-16.5f, 0, -12.5f);

            if (SimMode.Days > 0)
                gameObject.AddComponent<SimDirector>().Begin(this, player);

            Debts.Add(new Debtor { Id = "Sam", Name = "Sam", Amount = 120, Note = "stock money, never repaid" });
            Debts.Add(new Debtor { Id = "Rocco", Name = "Rocco", Amount = 60, Note = "the door take, '19" });
            BuildPurses();
            Empire.Seed = PopulationSeed;   // one world, one roll stream (audit 2026-07-27)
            // THE SAME IDENTITY, NOT A COPY OF IT. The racket rumours name the
            // player, and a second `PlayerIdentity` would go on saying "Novak"
            // after a save restored a different surname into this one.
            Empire.Owner = Me;

            TryLoad();
        }

        // Sim mode drives the clock from real elapsed time rather than
        // Time.deltaTime. Unity clamps deltaTime to Time.maximumDeltaTime
        // (1/3 s by default), so on a machine rendering at 1 fps the game clock
        // advances at a THIRD of real speed — and a nine-day self-test that
        // should take eleven minutes takes thirty-three. That is exactly what
        // happened on run 30217466971, on a CI runner that had evidently fallen
        // back to software rasterisation. A self-test whose duration depends on
        // the runner's graphics driver is not a self-test you can put a timeout
        // on, so in sim mode the clock ignores the frame rate entirely.
        float _lastRealtime = -1f;

        void Update()
        {
            float step;
            if (SimMode.Days > 0)
            {
                float nowReal = Time.realtimeSinceStartup;
                if (_lastRealtime < 0) _lastRealtime = nowReal;
                // Capped so a long hitch (a level load, a stalled frame) advances
                // the world by a plausible jump instead of teleporting a day.
                step = Mathf.Min(nowReal - _lastRealtime, 2f);
                _lastRealtime = nowReal;
            }
            else step = Time.deltaTime;

            _minuteAccumulator += step * MinutesPerRealSecond;
            while (_minuteAccumulator >= 1f)
            {
                _minuteAccumulator -= 1f;
                Now = Now.AddMinutes(1);
            }

            Perf.Frame(SimMode.Days > 0 ? step : Time.unscaledDeltaTime);

            // WHERE THE FRAME ACTUALLY GOES, because until now nothing knew.
            //
            // `Perf` had exactly two scopes in the whole project — traffic and
            // signals — and the frame gate failed at 302.9ms against a budget
            // of 300 with 298 of those milliseconds unattributed. A gate whose
            // failure message cannot say WHAT grew is a gate that gets its
            // threshold raised, which is the wrong repair and the easy one.
            //
            // These four cover everything this class does per frame; whatever
            // the frame total minus their sum comes to is rendering, which on
            // a GPU-less runner is expected to be most of it. The next run
            // says which, and the number moves only once something has been
            // attributed.
            // NAMED `sun` AND MOSTLY NOT THE SUN, which is why the budget line
            // has never pointed at anything actionable.
            //
            // `frame` is the only gate red on the newest run and has failed 28
            // of 141, and its breakdown reads `game=17.55ms` against a 12ms
            // budget — ours, not the software rasteriser's. `sun=3.15ms` is a
            // quarter of that budget and reads as a directional light being
            // expensive, which it cannot be.
            //
            // `UpdateSun` sets the sun in four lines and then does the entire
            // audio mix — `SetNight`, `SetDaylight`, `SetScore`, `StepMix`,
            // `Standoff.Step` — plus the ambient gradient and the fog, which
            // are `RenderSettings` writes and are not free either. Anybody
            // optimising "the sun" off this number would be reading the wrong
            // system, which is rule 2's warning about a metric keeping its name
            // when the question moves.
            //
            // Split so the reading says which. The work is unchanged and in the
            // same order — `UpdateSun` still owns the sequence, because the
            // comment inside it argues that light and sound must come off ONE
            // daylight number or dusk arrives twice.
            using (Perf.Time("sun")) UpdateSun();
            using (Perf.Time("mix")) UpdateMix();
            // Level of detail before ticking, so a walker spawned this frame
            // starts from the right place rather than the origin.
            // TWO PASSES, TWO BUCKETS, AND THEY WERE POOLED INTO ONE NUMBER.
            //
            // `population=4.08ms` is the largest single item in the only gate
            // that is red — `frame`, at `game=16.04ms` against a 12ms budget —
            // and it has been unactionable because it covers two passes with
            // completely different cadences. `TickPopulation` rebands seven
            // hundred residents EVERY frame; `TickBodyDetail` instantiates and
            // destroys prefabs ONCE A SECOND. Four milliseconds spread evenly
            // over every frame and four milliseconds that is really sixty
            // concentrated in one frame a second are opposite findings with
            // opposite fixes, and their mean reads identically.
            //
            // A number that cannot say which of two things it is measuring is
            // the instrument being wrong, not the subject (rule 3), and the
            // repair is a second scope rather than a guess about which half.
            //
            // The ORDER is unchanged and load-bearing: body LOD runs after the
            // rebanding so a walker spawned by this pass is considered for a
            // face in the same frame it appears rather than a second later.
            {
                var at = _player != null ? _player.transform.position : Vector3.zero;
                using (Perf.Time("population")) TickPopulation(at);
                using (Perf.Time("bodyLod")) TickBodyDetail(at);
            }
            using (Perf.Time("npcs"))
                for (int i = _npcs.Count - 1; i >= 0; i--)
                {
                    var npc = _npcs[i];
                    if (npc == null) { _npcs.RemoveAt(i); continue; }  // despawned crowd
                    npc.Tick(Now);
                }

            // Once per game-hour, let rumors cool if nobody is keeping them alive — this
            // is what makes the player's "lie low and let it blow over" option real.
            if (Now.Hour != _lastAgedHour)
            {
                _lastAgedHour = Now.Hour;
                _gossip?.Mill?.Age(Now);

                // AND WHERE HE WAS WHEN THE TELEPHONE RANG.
                //
                // `SummonsHost.Nightly` runs at the day close — EIGHT IN THE
                // MORNING — and asks `ReachableNow` about lines live at nine at
                // NIGHT, using `NearPhone`, which reads the player's transform
                // right now. So the hour comes from the ring and the position
                // comes from breakfast: a numerator and a denominator taken
                // thirteen hours apart, which is the fault this project has
                // found in four different systems and had not looked for here.
                //
                // `summonsMissWhy=[a line was live and he was not near it]` is
                // therefore a true sentence about the wrong moment, and it has
                // been read as evidence that the mechanic works and the player
                // simply wanders. Nobody could have been near it except by
                // standing at a callbox at eight in the morning.
                //
                // Sampled here because this branch is the only place in the
                // game that fires exactly once per game-hour.
                if (Now.Hour == Ledger.Core.Summoning.RingsAtHour && _player != null)
                {
                    PlayerAtRing = _player.transform.position;
                    PlayerAtRingDay = Now.Day;
                }
            }

            // Nightly reflection: distill the day's memories into beliefs once, from 23:00.
            // Use >= 23, not == 23: under the accelerated sim clock a single frame can
            // step across the exact hour, and the per-day guard already limits it to once.
            if (Now.Hour >= 23 && Now.Day > _lastReflectedDay && _lena != null && _lena.Ready)
            {
                // Days the Fall jumped over never reach their own 23:00; any
                // that carry events (the fall day itself) reflect now, so a
                // lived day is never left raw forever (audit 2026-07-27).
                for (int day = _lastReflectedDay + 1; day < Now.Day; day++)
                    _ = _lena.RunReflectionForDayAsync(day, Now);
                _lastReflectedDay = Now.Day;
                _ = _lena.RunReflectionAsync(Now);
            }

            // Traffic runs on the REAL clock, not the accelerated one. Twenty
            // game-minutes per second is a fine rate for a day to pass at and a
            // nonsense rate for a bus to travel at — at that scale a car would
            // cross the district between two frames. The city's day speeds up;
            // its traffic does not.
            TickTraffic(SimMode.Days > 0 ? step : Time.deltaTime);
            TickSignals();
            if (SimMode.Days == 0) CheckDriving();

            TickWorldDay();
            UpdateCampaign();
            if (Campaign.FallPending) RunTheFall();
            UpdateBeats();
            if (Input.GetKeyDown(GameSettings.Current.Key("Save"))) SaveNow();
            // Every frame, not on the 30-frame cadence: a door you hear half a
            // second after you walk through it is worse than no door at all.
            CheckBarDoor();
            // EVERY FRAME, FOR THE SAME REASON AS THE DOOR: it is a proximity
            // test, and a proximity test sampled on a frame cadence has a
            // window that shrinks as the frame rate falls.
            //
            // It sat inside the thirty-frame block below and `suspicionActs`
            // had never once gone green. The staging works — CI reports
            // `staged=Ada` — and then reports `confronts=0` across seven days
            // of open city. The reason is arithmetic: the CI runner has no GPU
            // and software-rasterises at about 300ms a frame, so thirty frames
            // is NINE SECONDS. A walker crosses the four-metre trigger in
            // about five. The check was sampling straight past the encounter
            // it exists to detect, and reporting that as a fact about the game
            // rather than about its own cadence.
            //
            // At sixty frames a second the old cadence was half a second and
            // fine, which is exactly why this survived: it is only wrong on
            // the machine that measures it. The cost of moving it is one
            // distance comparison per walker per frame, the same shape as
            // `CheckBarDoor` above.
            CheckConfrontations();
            if (Time.frameCount % 30 == 0)
            {
                using var _checkScope = Perf.Time("checks");
                CheckGates();
                CheckLoyalWarnings();
                CheckOssei();
                CheckBarks();
                CheckOsseiInterviews();
                CheckOnboarding();
                CheckActOne();
                CheckActTwo();
                CheckActThree();
                CheckDayJob();
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
                var line = BarkFor(name, out var gesture);
                if (line == null) continue;
                _barkDay[name] = Now.Day;
                // The body performs what the toast says, in the same beat.
                if (gesture != null) npc.React(gesture, 1.8f);
                // AMBIENT: a bark is colour of its moment. It must never eat
                // a queued beat, and a bark held back until the queue drains
                // would land about somebody who has already walked away — so
                // it is dropped, not delayed (the Toast comment carries the
                // policy).
                _ui.Toast(line, 5f, ambient: true);
                break; // one voice per pass
            }
        }

        // First-morning onboarding: four lines, diegetic in tone, never in
        // sim. Movement first — the playtest plan's research found the game
        // taught talking before it ever taught WALKING, and a first-time
        // player on a borrowed laptop starts by standing still. Every key is
        // printed from the live binding, not the default letter: the prompt
        // is read at the exact moment a player trusts it most.
        int _onboardStep;

        void CheckOnboarding()
        {
            if (SimMode.Days > 0 || Now.Day != 1 || _ui == null) return;
            var keys = GameSettings.Current;
            if (_onboardStep == 0 && (Now.Hour > 9 || (Now.Hour == 9 && Now.Minute >= 2)))
            {
                _onboardStep = 1;
                _ui.Toast("Your feet know the way: WASD walks, Shift runs. The street watches whoever is moving.", 8f);
            }
            else if (_onboardStep == 1 && (Now.Hour > 9 || (Now.Hour == 9 && Now.Minute >= 10)))
            {
                _onboardStep = 2;
                _ui.Toast($"The pub is yours now. Walk up to anyone and press {keys.Key("Talk")} to talk — they remember.", 9f);
            }
            else if (_onboardStep == 2 && Now.Hour >= 10)
            {
                _onboardStep = 3;
                _ui.Toast($"Press {keys.Key("Ledger")} for your ledger: what you believe the street knows about you — and what you hold over it.", 9f);
            }
            else if (_onboardStep == 3 && Now.Hour >= 12)
            {
                _onboardStep = 4;
                _ui.Toast($"Tonight the outfit will want its first drop made. {keys.Key("Coat")} toggles the runner's coat — harder to name in the dark, harder to explain in daylight.", 10f);
            }
        }

        void CheckOsseiInterviews()
        {
            if (!EllisSpawned || _osseiWalker == null || _gossip == null || _gossip.Mill == null) return;
            foreach (var npc in _npcs)
            {
                if (npc == null || npc == _osseiWalker) continue;
                if (npc.DisplayName == "Noor") continue; // she never shares with police — the whole of her ethics
                var g = _gossip.Mill.Get(npc.GossipId);
                if (g == null || g.Leashed) continue; // a leashed witness gives her nothing
                if (Vector3.Distance(npc.transform.position, _osseiWalker.transform.position) > 6f) continue;
                foreach (var r in g.Rumors)
                {
                    if (r.Hops != 0 || r.Content.Subject != "player") continue;
                    if (g.Suppressed.Contains(r.TopicKey)) continue; // bought silence holds, even against her
                    if (!_interviewed.Add(npc.DisplayName + "|" + r.TopicKey)) continue;
                    EllisInterviews.Add($"{npc.DisplayName} told you: {r.Summary}");
                    g.Memory.Append(new MemoryEvent(Now, "conversation", 0.8,
                        $"The detective asked me straight. I told her what I saw: {r.Summary}"));
                    if (_ossei != null) _ossei.Memory.Append(new MemoryEvent(Now, "conversation", 0.85,
                        $"Interviewed {npc.DisplayName}. Statement: {r.Summary}"));
                }
            }
        }

        // ---- Act II: the squeeze, fired by the empire's own shape ----

        void CheckActTwo()
        {
            if (!Campaign.OpenMode || _gossip == null || _gossip.Mill == null) return;
            var e = Empire;

            if (!ActTwo.Opened)
            {
                if (!ActTwoState.ShouldOpen(true, e.Businesses.FindAll(b => b.Owned).Count,
                    e.Rackets.FindAll(r => r.Established).Count, e.Crew.FindAll(c => !c.Departed).Count)) return;
                ActTwo.Opened = true;
                ActTwo.OpenedDay = Now.Day;
                ToastLine(ActTwoState.OpenText, 12f);
                return;
            }

            // PP1 — a second organization notices: it isn't one rival anymore.
            if (!ActTwo.Pp1Fired)
            {
                var noticing = e.Arms.FindAll(a => a.Attention >= 0.25);
                if (noticing.Count >= 2)
                {
                    ActTwo.Pp1Fired = true;
                    ToastLine(ActTwoState.FirstNotice(noticing[1].Id), 11f);
                }
            }

            // PP2 — the machine's letter: the bar's licence, under review.
            if (!ActTwo.Pp2Fired && e.ArmOf("machine").Attention >= 0.5)
            {
                ActTwo.Pp2Fired = true;
                ActTwo.InjunctionUntilDay = Now.Day + 2;
                ToastLine(ActTwoState.Pp2LetterText, 14f);
            }

            // PP3 — the kid, properly, outside your door. Real witnesses.
            if (!ActTwo.Pp3Fired &&
                (e.ArmOf("newcrew").Attention >= 0.5 || e.CrewOf("Rita") != null))
            {
                ActTwo.Pp3Fired = true;
                foreach (var a in _gossip.Mill.Agents)
                {
                    if (a.Circle != "day" || a.Leashed) continue;
                    _gossip.Mill.Witness(a.Id, new Fact("player", $"street_incident_d{Now.Day}", "seen"),
                        "there was real trouble outside the new owner's bar — the Strip crowd, glass everywhere", true, Now, 0.55);
                    break;
                }
                ToastLine(ActTwoState.Pp3KidText, 12f);
            }

            // PP5 — the broker opens for business.
            // PP4's guarantee (act2-draft: "fires: any day-life loyalty >= 0.65
            // AND crew >= 1; the guaranteed collision"). The staged version
            // fires when an honored evening is attended; this is the fallback
            // for the player who never sits down — the collision comes to the
            // bar at night instead. The documented condition existed nowhere in
            // code before (audit 2026-07-27).
            if (!ActTwo.Pp4Fired && Now.Hour >= 21)
            {
                var crewMember = e.Crew.Find(c => !c.Departed);
                Gossiper fond = null;
                foreach (var a in _gossip.Mill.Agents)
                    if (a.Circle == "day" && e.CrewOf(a.Id) == null && a.Loyalty >= 0.65
                        && (fond == null || a.Loyalty > fond.Loyalty)) fond = a;
                if (crewMember != null && fond != null)
                {
                    ActTwo.Pp4Fired = true;
                    ToastLine(ActTwoState.Pp4DoorstepText, 14f);
                    fond.Suspicion.Raise(0.18, "one of the new owner's people burst in on night business");
                    fond.Memory.Append(new MemoryEvent(Now, "observation", 0.9,
                        $"I was in the pub, at ease for once, and {crewMember.Name} came through the door with " +
                        "night business written all over them. Whatever it was, it could not wait until morning."));
                    _gossip.Mill.Witness(fond.Id, new Fact("player", $"night_business_d{Now.Day}", "seen"),
                        $"{crewMember.Name} burst into the bar after dark with something for the new owner that could not wait",
                        true, Now, 0.85);
                    _gossip.Mill.Get(crewMember.Id)?.Memory.Append(new MemoryEvent(Now, "observation", 0.8,
                        "Had to walk night business straight into the pub tonight. The whole room saw me do it."));
                }
            }

            if (!ActTwo.Pp5Fired && e.Arms.FindAll(a => a.Attention >= 0.5).Count >= 2)
            {
                ActTwo.Pp5Fired = true;
                ToastLine(ActTwoState.Pp5ShopText, 12f);
            }

            // PP6 — two cases become one case.
            if (!ActTwo.Pp6Fired && EllisSpawned && EllisInterviews.Count > 0
                && e.TotalRacketIncome > 0)
            {
                ActTwo.Pp6Fired = true;
                ToastLine(ActTwoState.Pp6CaseText, 12f);
                _ossei?.Memory.Append(new MemoryEvent(Now, "observation", 0.95,
                    "The fire and the rounds are the same case. I stopped asking about the warehouse today and started asking who collects."));
            }

            // PP7 — the Table: an arm at the summit wants a room.
            if (!ActTwo.TableFired && ActTwo.TableArmId == null)
            {
                var summit = e.Arms.Find(a => a.Stage >= 4);
                if (summit != null)
                {
                    ActTwo.TableArmId = summit.Id;
                    SpawnHead(summit.Id, summit.HeadName);
                    ToastLine($"Hal's message is one line: {summit.HeadName} will see you. The coin shop, when you're ready.", 13f);
                }
            }
        }

        /// PP4 — the collision the act guarantees. You are sitting in the honest
        /// life when the other one knocks: a crew member on the step with
        /// something that will not keep. Both worlds see each other, and the
        /// mill carries it from there. Fires once, on the evening of whoever
        /// thinks best of you — which is exactly what makes it cost something.
        void FireCollision(Beat attended)
        {
            if (!ActTwo.Opened || ActTwo.Pp4Fired || _gossip == null || _gossip.Mill == null) return;
            var crew = Empire.Crew.Find(c => !c.Departed);
            if (crew == null) return;
            var host = _gossip.Mill.Get(attended.HostId);
            if (host == null) return;

            ActTwo.Pp4Fired = true;
            ToastLine(ActTwoState.Pp4CollisionText, 14f);

            // The host saw who came, and at what hour, and how you changed.
            host.Suspicion.Raise(0.18, $"one of the new owner's people came to my door at night");
            host.Memory.Append(new MemoryEvent(Now, "observation", 0.9,
                $"We were sitting down properly for once and {crew.Name} came knocking after dark, for them, not for me. " +
                "Whatever that was about, it could not wait until morning."));
            _gossip.Mill.Witness(host.Id, new Fact("player", $"night_business_d{Now.Day}", "seen"),
                $"the new owner had {crew.Name} at the door in the middle of an evening, and left the table for it",
                true, Now, 0.85);

            // The crew member remembers being sent, and being seen.
            _gossip.Mill.Get(crew.Id)?.Memory.Append(new MemoryEvent(Now, "observation", 0.8,
                "Had to fetch them out of somebody's front room tonight. They didn't like it. Neither did whoever was pouring."));
        }

        /// An organization's head comes to the room Hal arranged. They are
        /// NOT in the gossip mill — heads don't stand on corners trading talk;
        /// they arrive, they are answered, and the street hears about it after.
        readonly HashSet<string> _headsSpawned = new HashSet<string>();

        /// A supplier, walking. Their ExtraContext is the district's economic
        /// state IN THEIR OWN WORDS — the same numbers the daily close reads,
        /// said as a man's circumstance rather than a status line.
        void SpawnSupplier(string supplierId, string card, Color color,
            (GameTime, Vector3)[] schedule, string scene)
        {
            var supplier = Economy.SupplierNamed(supplierId);
            if (supplier == null) return;
            var walker = NpcWalker.Spawn(supplier.Name, color, schedule);
            _npcs.Add(walker);
            var host = walker.gameObject.AddComponent<ConversationHost>();
            host.Initialize(this, card, null, null);
            host.SceneContext = scene;
            host.ExtraContext = () =>
            {
                var owed = supplier.Refusing
                    ? $" You have stopped delivering {supplier.Goods} here. You did not make a scene about it; you simply stopped, and you will not start again for an apology alone."
                    : supplier.Unpaid > 0
                        ? $" You are owed for {supplier.Unpaid} {(supplier.Unpaid == 1 ? "delivery" : "deliveries")} of {supplier.Goods} and you have not been paid. You have mentioned it once."
                        : $" You were paid for {supplier.Goods} on time, and you have no complaint about that.";
                var street = $" The people on this street are {Economy.ProsperityWord()} at the moment, and prices are {Economy.PriceWord()}.";
                var feeling = supplier.Standing > 0.3 ? " You like dealing with this one."
                    : supplier.Standing < -0.25 ? " You have gone off this one, and your prices reflect it."
                    : " You have no strong feeling about this one either way.";
                return owed + street + feeling + SuspicionBehaviorText(supplier.Name);
            };
            _hosts.Add(host);
        }

        /// Settle up with a supplier — the mechanical half of the amends verb.
        /// Deliberately on GameController so the UI, the router, and any future
        /// caller all go through one implementation.
        public bool SettleSupplier(string supplierId, out string line)
        {
            line = null;
            var s = Economy.SupplierNamed(supplierId);
            if (s == null) return false;
            if (s.Refusing) return Economy.MakeAmends(s, Wallet, Now, out line);
            if (s.Unpaid <= 0) { line = $"{s.Name} is square with you. There is nothing to settle."; return false; }

            int owed = Economy.DeliveryPrice(s) * s.Unpaid;
            if (!Wallet.Spend(owed, dirtyOk: true))
            {
                line = $"{s.Name} works out what he's owed — £{owed} — and waits while you don't have it.";
                return false;
            }
            s.Unpaid = 0;
            s.LastPaidDay = Now.Day;
            s.Standing = System.Math.Min(1.0, s.Standing + 0.2);
            Audio.Ui("coin");
            line = $"You count out £{owed}. {s.Name} puts it away without looking at it, which is how you know it mattered.";
            return true;
        }

        /// Whether the person you are standing in front of is a supplier with
        /// something outstanding — the availability rule for the amends verb.
        public Supplier OutstandingSupplier(string personName)
        {
            foreach (var s in Economy.Suppliers)
                if (s.Name == personName && (s.Refusing || s.Unpaid > 0)) return s;
            return null;
        }

        void SpawnHead(string armId, string headName)
        {
            var shortName = armId == "dockside" ? "Sera" : armId == "machine" ? "Aldous" : "Danny";
            if (!_headsSpawned.Add(shortName)) return;
            var member = CastTier1.Get(shortName);
            if (member == null) return;
            var color = shortName == "Sera" ? CastTier1.SeraColor
                : shortName == "Aldous" ? CastTier1.AldousColor : CastTier1.DannyColor;
            // Hal's back room, by the ferry: neutral ground, as arranged.
            var walker = NpcWalker.Spawn(shortName, color, new[]
            {
                (new GameTime(0, 9, 0), new Vector3(29, 0, 22)),
                (new GameTime(0, 22, 0), new Vector3(29, 0, 22)),
            });
            _npcs.Add(walker);
            var host = walker.gameObject.AddComponent<ConversationHost>();
            host.Initialize(this, member.Card, null, null);
            host.SceneContext = member.Scene;
            var arm = Empire.ArmOf(armId);
            host.ExtraContext = () =>
                $" You have called this meeting because the new owner's street has become worth taking. " +
                $"Your standing with them is {(arm.Standing > 0.4 ? "unexpectedly good" : arm.Standing < -0.2 ? "poor" : "neutral")}. " +
                $"Your offer is on the table and you are waiting for an answer. {ActTwoState.TableOffer(armId)}";
            _hosts.Add(host);
        }

        /// The player answers the summit (accept | defy | counter). Like the
        /// posture, the answer becomes a Fact the whole street learns.
        public void AnswerTable(string answer)
        {
            if (ActTwo.TableArmId == null || ActTwo.TableFired) return;
            ActTwo.TableAnswer = answer;
            Empire.ResolveTable(ActTwo.TableArmId, answer, _gossip?.Mill, Now);
            var arm = Empire.ArmOf(ActTwo.TableArmId);
            var fact = new Fact("player", "table", answer);
            foreach (var host in _hosts)
            {
                if (host == null) continue;
                host.Knowledge.Learn(fact);
                host.Memory.Append(new MemoryEvent(Now, "heard", 0.8,
                    $"Word went round inside a day: the new owner sat down with {arm.HeadName} and {(answer == "accept" ? "took the terms" : answer == "defy" ? "refused them" : "named their own")}."));
            }
            ToastLine(ActTwoState.TableResult(ActTwo.TableArmId, answer), 14f);
            SaveNow(quiet: true);
        }

        /// M21: ALLEGIANCE, WHICH UNTIL NOW NEVER SHIFTED.
        ///
        /// The roadmap scores faction politics 45 against a target of 75 with
        /// the note "rivals exist; allegiance never shifts", and the reason was
        /// not missing code. `EmpireBook.PledgeTo` and `BreakWith` were written,
        /// tested and sitting on the reach ledger with that exact sentence as
        /// their reason. Three unwired methods were the whole gap.
        ///
        /// Shaped on `AnswerTable` directly above, because pledging is the same
        /// kind of event: a decision that becomes a Fact the street learns, not
        /// a flag on an object. Flying somebody's colours is the most public
        /// thing the player can do — `PledgeTo`'s own line is "everyone on this
        /// street noticed the day it happened" — so it would be absurd for it
        /// to reach the empire book and not the people in it.
        public bool Pledge(string armId)
        {
            var arm = Empire.ArmOf(armId);
            if (arm == null || !Empire.PledgeTo(armId, _gossip?.Mill, Now)) return false;
            BroadcastAllegiance(new Fact("player", "allegiance", arm.Id),
                $"The new owner flies {arm.HeadName}'s colors now.");
            ToastLine($"You are {arm.HeadName}'s now. The street will know by morning.", 14f);
            return true;
        }

        /// And out again. Nobody takes that quietly, which is the point of
        /// having it: an allegiance you cannot leave is a setting, not a choice.
        public bool WalkOutOn(string armId)
        {
            var arm = Empire.ArmOf(armId);
            if (arm == null || !Empire.BreakWith(armId, _gossip?.Mill, Now)) return false;
            BroadcastAllegiance(new Fact("player", "allegiance", "none"),
                $"The new owner walked out on {arm.HeadName}.");
            ToastLine($"You are on your own again. {arm.HeadName} does not forget that.", 14f);
            return true;
        }

        /// The half both of those share: it is not a decision until somebody
        /// else knows about it.
        void BroadcastAllegiance(Fact fact, string line)
        {
            foreach (var host in _hosts)
            {
                if (host == null) continue;
                host.Knowledge.Learn(fact);
                host.Memory.Append(new MemoryEvent(Now, "heard", 0.8, line));
            }
            AllegianceChanges++;
            SaveNow(quiet: true);
        }

        /// How many times allegiance actually moved. A run where it never does
        /// is the state this milestone exists to leave, and a counter is how a
        /// gate can tell that state from a green one.
        public static int AllegianceChanges { get; private set; }

        /// The courier round (doc §6.6): the board by the docks, a route of
        /// stops, clean pay, and the quiet cover of being someone with a
        /// timecard. Time is the resource — the morning goes to parcels.
        void CheckDayJob()
        {
            if (!Campaign.OpenMode || _ui == null || _player == null) return;

            if (Job.CanAccept(Now))
            {
                if (_dispatchMarker == null)
                {
                    _dispatchMarker = SpawnGlowMarker(DispatchBoard, new Color(0.35f, 0.72f, 0.78f), "DispatchBoard");
                    if (_dispatchToastDay != Now.Day)
                    {
                        _dispatchToastDay = Now.Day;
                        ToastLine("Zlata's board is up by the docks, chalk still wet. \"Routes! Before I give them to someone who turns up on time!\"", 8f);
                    }
                }
            }
            else if (_dispatchMarker != null) { Destroy(_dispatchMarker); _dispatchMarker = null; }

            var p = _player.transform.position;
            if (_dispatchMarker != null &&
                Vector3.Distance(new Vector3(p.x, 0, p.z), new Vector3(DispatchBoard.x, 0, DispatchBoard.z)) < 2.5f
                && Job.Accept(Now))
            {
                Destroy(_dispatchMarker);
                _dispatchMarker = null;
                _shiftStop = 0;
                _shiftMarker = SpawnGlowMarker(ShiftStops[0], new Color(0.35f, 0.72f, 0.78f), "ShiftStop");
                ToastLine("Zlata drops the satchel into your arms mid-sentence. \"Market corner first, and don't let Marla feed you, you'll never leave. Back before dark.\"", 10f);
            }

            if (_shiftMarker != null)
            {
                if (Job.Lapse(Now))
                {
                    Destroy(_shiftMarker);
                    _shiftMarker = null;
                    ToastLine("Evening, and the parcels go back on Zlata's shelf unsigned. She doesn't say anything. She writes something.", 8f);
                    return;
                }
                var m = _shiftMarker.transform.position;
                if (Vector3.Distance(new Vector3(p.x, 0, p.z), new Vector3(m.x, 0, m.z)) < 2.5f)
                {
                    Destroy(_shiftMarker);
                    _shiftMarker = null;
                    if (Job.Advance(ShiftStops.Length))
                    {
                        int pay = Job.Complete(Wallet, Now);
                        ToastLine($"Zlata initials your sheet without looking up. \"+£{pay}. You're not bad at this. Worrying, for a man with a bar.\"", 9f);
                    }
                    else
                    {
                        _shiftStop++;
                        _shiftMarker = SpawnGlowMarker(ShiftStops[_shiftStop], new Color(0.35f, 0.72f, 0.78f), "ShiftStop");
                    }
                }
            }
        }

        /// Self-test hook: put the satchel in the bot's arms without making it
        /// reach the board first.
        ///
        /// The day job is the ONE open-city system the sim did not stage — the
        /// empire beat, the Director's pressures, an operation, the harm layer
        /// and Act III are all staged by hand, and this was left to the bot's
        /// legs. Under the accelerated clock the board is up for four game
        /// hours, which is about twelve real seconds, and the walk across a
        /// district that is now three districts wide does not fit in that.
        ///
        /// So the ACCEPT is staged and the round is not: the bot still has to
        /// walk all three stops and get back to Zlata to be paid, which is the
        /// half that can actually break. Never called from the game — the real
        /// door is standing at the board while the chalk is wet.
        public bool StageDayJobShift()
        {
            if (!Campaign.OpenMode || _shiftMarker != null) return false;
            if (!Job.Accept(Now)) return false;
            if (_dispatchMarker != null) { Destroy(_dispatchMarker); _dispatchMarker = null; }
            _shiftStop = 0;
            _shiftMarker = SpawnGlowMarker(ShiftStops[0], new Color(0.35f, 0.72f, 0.78f), "ShiftStop");
            return true;
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
                        "The new owner knows where Mickey's real ledger is now. All of it. Even the page about the warehouse."));
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
        /// THE FALL, STAGED (game-feel-spec.md §8).
        ///
        /// This is the biggest thing that happens in LEDGER and it used to be
        /// a toast: amber text sliding in over a normally-lit street while
        /// three days snapped forward in front of you. Now the curtain comes
        /// down first, the world changes underneath it where the join cannot
        /// be seen, the words hold on black long enough to be uncomfortable,
        /// and you come back into a different morning.
        ///
        /// If the curtain cannot be staged — no UI yet, or one already
        /// falling — the work still happens IMMEDIATELY and unstaged. A
        /// missed presentation is a disappointment; a skipped Fall is a
        /// broken save and a campaign that never opens.
        void RunTheFall()
        {
            if (!Campaign.FallPending || _gossip == null || _gossip.Mill == null) return;

            // ALREADY FALLING. This is called every frame while the Fall is
            // pending, and pending stays true until the work runs under
            // black — so without this guard the second frame would find the
            // curtain busy, take the unstaged path, and apply the Fall in
            // full daylight a sixtieth of a second after starting to hide it.
            // The staging would have been dead on arrival and looked like it
            // worked in every test that did not watch the screen.
            if (ScreenCurtain.Busy) return;

            Audio.Ui("dread");   // the heaviest thing that happens to you
            if (SimMode.Days == 0 && _ui != null &&
                ScreenCurtain.Fall(_ui.CanvasRoot, FallText(), ApplyTheFall, 3.4f))
                return;
            ApplyTheFall();
        }

        /// What the Fall does to the world. Split out so it can be run under
        /// a black screen, and so the staging can never change the outcome.
        void ApplyTheFall()
        {
            Campaign.ConsumeFall();
            if (_jobMarker != null) { Destroy(_jobMarker); _jobMarker = null; }

            int seized = Wallet.Seize();
            Now = new GameTime(Now.Day + 3, 8, 0);
            _lastClosedDay = Now.Day;   // the skipped mornings never close
            // (_jobPostedDay deliberately NOT touched: posting checks the live
            // window at post time, so no ghost job can appear from the lost
            // nights — and stamping it here suppressed the landing night's
            // legitimate drop, audit 2026-07-27.)

            var didTime = new Fact("player", "did_time", "true");
            // Everyone KNOWS (the fact, the loyalty, the settled suspicion).
            // Only the named cast REMEMBER the day in their own words: a
            // memory line pins an agent as load-bearing forever (Forget
            // refuses non-empty memories), and stamping the whole milled
            // crowd made one Fall permanently pin ~130 residents the LOD
            // could never again release (audit 2026-07-27). The crowd's
            // knowing is fully carried by the fact.
            var principals = new HashSet<string>();
            foreach (var h in _hosts) if (h != null && h.Card != null) principals.Add(h.Card.Name);
            foreach (var a in _gossip.Mill.Agents)
            {
                // EXCEPT THE INDELIBLE ONES. This wipe is the Fall's design
                // — you did time, the street's TALK about you resets — and
                // for five days it also erased every eyewitness's memory of
                // a KILLING, because those facts are filed under "player"
                // too. Found by the heat diary: nineteen witnesses at full
                // confidence on day 14, agents intact on day 17 with no
                // rumour at all, and the one mechanism with no alibi was
                // this line. The homicide design's own words say a body
                // cannot be denied; it cannot be sat out either.
                a.Rumors.RemoveAll(r => r.Content.Subject == "player"
                                        && !r.Indelible);
                a.Knowledge.Learn(didTime);
                a.Loyalty = System.Math.Clamp(a.Loyalty - 0.15, 0, 1);
                a.Suspicion.Restore(0.2); // nothing left to suspect — they know
                if (principals.Contains(a.Id))
                    a.Memory.Append(new MemoryEvent(Now, "heard", 0.9,
                        "They took the new owner in. Three days inside. Nobody on this street is guessing anymore."));
            }
            // The talk is over — it's public record now; the old liabilities settle.
            foreach (var k in Knowledge.Entries) Knowledge.MarkHandled(k.HolderId, k.TopicKey);

            // Ellis got her arrest. For a few days the pressure eases; rumors
            // (there are none about you left anyway) age at street speed.
            if (EllisSpawned)
            {
                _osseiCalmUntilDay = Now.Day + 4;
                _gossip.Mill.RumorHalfLifeHours = 96;
            }

            // The line has already been shown on the curtain in the staged
            // path; a toast on top of it would be the same words twice, and
            // the audit already caught two channels fighting for one event.
            _lastSeized = seized;
            if (SimMode.Days != 0 || _ui == null) _ui?.Toast(FallText(), 14f);
            SaveNow(quiet: true);
        }

        int _lastSeized;

        /// The words. Written before the money is counted because the curtain
        /// needs them up front — it says what was taken using the LAST known
        /// figure, which is the live one at the moment the curtain drops
        /// because seizure happens under black a beat later.
        string FallText()
        {
            int seized = _lastSeized > 0 ? _lastSeized : Wallet.Dirty;
            return seized > 0
                ? $"THE FALL. Three days inside. They kept the £{seized} they found — the money the books couldn't explain. The street knows now. Start from there."
                : "THE FALL. Three days inside. They found nothing to keep, which is the only mercy. The street knows now. Start from there.";
        }

        /// The recruit-by-need table: the authored roster first, then the
        /// generated batch's own needs (default price, their card's words).
        public bool TryNeedOf(string id, out int cost, out string line) =>
            EmpireSetup.TryNeed(id, out cost, out line) || Tier2Batch.TryNeed(id, out cost, out line);

        /// PP7: the player says out loud which life they're choosing. Dialogue +
        /// a Fact every cast brain learns (player decision 2026-07-26); mechanics
        /// are Act II's job. Ellis is excluded — the answer travels as street
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

        /// `gesture` is the clip slot the LINE ITSELF describes, or null.
        /// The prose is the spec here: "waves from the counter" hands back
        /// "wave", "tips two fingers" a greeting — and the sour lines hand
        /// back nothing, because a warm gesture under a wary sentence would
        /// be the text and the body disagreeing in the same second.
        string BarkFor(string name, out string gesture)
        {
            gesture = null;
            if (name == "Ellis")
                return EllisSpawned ? "Ellis watches you pass. She doesn't pretend otherwise." : null;
            var g = _gossip.Mill.Get(name);
            if (g == null) return null;
            if (g.Leashed) return $"{name} finds somewhere else to look as you pass.";
            if (g.Suspicion.Level == SuspicionLevel.Confronting) return $"{name} stares at you, arms folded. No greeting.";
            if (g.Suspicion.Level == SuspicionLevel.Suspicious) return $"{name} watches you a beat too long before nodding.";
            // Empire-aware greetings: the street remembers HOW things became yours.
            var crewBark = Empire.CrewOf(name);
            if (crewBark != null)
            {
                if (crewBark.Route == "hook" || g.Loyalty < 0.35)
                    return $"{name} nods the way people nod at debts. \"Boss.\"";
                gesture = "greet";
                return $"{name} tips two fingers, easy. \"Boss.\"";
            }
            foreach (var b in Empire.Businesses)
                if (b.Owned && b.OwnerId == name)
                {
                    if (b.AcquiredVia == "clean")
                    {
                        gesture = "wave";
                        return $"{name} waves from the counter that used to be theirs. No hard feelings; you paid in full.";
                    }
                    return b.AcquiredVia == "hook"
                        ? $"{name} straightens as you pass, the way people do near ice."
                        : $"{name} watches you pass their old shop and says nothing at all.";
                }

            bool carries = false;
            foreach (var l in _gossip.Mill.Leads("player"))
                if (l.HolderId == name) { carries = true; break; }
            if (carries && g.Suspicion.Level == SuspicionLevel.Uneasy)
                return $"{name} gives you a thin nod. Something's behind it.";
            if (g.Loyalty >= 0.7)
            {
                gesture = "wave";
                return $"{name} raises a hand as you pass. \"Boss.\"";
            }
            return null;
        }

        // After a Fall she has her arrest: the tan coat eases off for a few
        // days, and rumors breathe again — until the heat says she's needed.
        int _osseiCalmUntilDay;

        /// Somebody died at the player's hands. Rare, permanent, and the only
        /// event in the game that cannot be undone, denied, bought off or
        /// waited out (combat-spec §7b).
        ///
        /// `witnesses` is what Violence.Saw returned: everyone in range. The
        /// ones who could actually SEE carry your name; the ones who only
        /// heard it through a wall carry the death without the killer.
        public void RecordKilling(string victimId, string victimName, List<FightWitness> witnesses)
        {
            if (string.IsNullOrEmpty(victimId) || _gossip?.Mill == null) return;
            var k = Homicides.Record(victimId, victimName, Now.Day, Now.Hour, DistrictOfPlayer());
            if (k == null) return;

            if (witnesses != null)
                foreach (var w in witnesses)
                {
                    if (w == null || w.Id == victimId) continue;
                    if (!IsAlive(w.Id)) continue;
                    // Through a wall you know something happened and not what.
                    if (w.Occluded) { if (!k.KnowsOfIt.Contains(w.Id)) k.KnowsOfIt.Add(w.Id); }
                    else if (!k.SawYouDoIt.Contains(w.Id)) k.SawYouDoIt.Add(w.Id);
                }

            // The victim stops carrying anything. This is the containment
            // working, and it has to genuinely work or the choice is fake.
            _deadIds.Add(victimId);
            _gossip.Mill.Forget(victimId);
            foreach (var n in _npcs)
                // `DisplayName`, NOT `name`, AND THIS COULD NEVER HAVE MATCHED.
                // `NpcWalker.Spawn` sets `go.name = $"NPC_{name}"` and
                // `npc.DisplayName = name` three lines apart, so the GameObject
                // is `NPC_Filip` while every id in the gossip mill, the
                // homicide book and the observation model is `Filip`. The body
                // would have gone on walking around the street it died in,
                // visible in the stills, while `_deadIds` said otherwise.
                //
                // Found by writing the first caller this method has ever had —
                // which is the whole argument for rule 6. Nothing about this
                // line looks wrong, it compiles, it is the only comparison of
                // its kind left in the Game layer (grepped), and it was written
                // beside a comment about containment having to "genuinely work
                // or the choice is fake". `ViolenceHost.WalkerNamed` has the
                // correct form and is the one that gets used.
                if (n != null && n.GossipId == victimId)
                { n.gameObject.SetActive(false); break; }

            Homicides.FileWith(_gossip.Mill, k, Now, IsAlive);

            // Everyone who watched is permanently different about you — crew
            // included, and the crew most of all.
            foreach (var id in k.SawYouDoIt) Watched.Saw(_gossip.Mill.Get(id), Now);

            Audio.Foley("dread", 1f);
            _ui?.Toast($"{k.VictimName} is not getting up. Somebody down the street is already walking fast.", 12f);
            SaveNow(quiet: true);
        }

        /// What the score is allowed to know (Core/MusicModel). Small on
        /// purpose: a score that reads twenty variables is a score nobody can
        /// predict, and a player who cannot predict the music cannot learn to
        /// read it.
        ScoreState ScoreNow()
        {
            var st = new ScoreState
            {
                Heat = CurrentHeat,
                Night = NightAmount,
                Police = PoliceInquiry,
                InConversation = _ui != null && _ui.InConversation,
            };
            if (_gossip?.Mill != null)
                st.StrongestLead = _gossip.Mill.StrongestSurvivingPlayerLead();
            if (ActThree.Opened && !ActThree.AuditClosed)
                st.DaysLeftOnAudit = System.Math.Max(0, ActThree.AuditClosesDay - Now.Day);
            // Somebody in sight who will not deal with you. Read off the
            // bodies rather than off the mill, because what matters here is
            // whether the player can SEE them.
            foreach (var n in _npcs)
            {
                if (n == null || !n.isActiveAndEnabled) continue;
                if (n.Stance < StanceKind.Refuses) continue;
                if (_player == null) continue;
                if (Vector3.Distance(n.transform.position, _player.transform.position) > 12f) continue;
                st.Cornered = true;
                break;
            }
            return st;
        }

        /// Public because the paper needs a place name for its headline, and a
        /// second copy of "where is the player" is how two answers to one
        /// question start.
        public string DistrictOfPlayer() =>
            _player != null ? StreetMap.DistrictAt(_player.transform.position.x,
                                                   _player.transform.position.z) : "Hook Street";

        void CheckOssei()
        {
            double heat = CurrentHeat;
            if (heat > ObservedPeakHeat) ObservedPeakHeat = heat;

            // A body is how a detective gets assigned. From here the heat
            // threshold is moot — she is on the street whatever the talk is
            // doing, and she does not go calm again afterwards.
            var inquiry = PoliceInquiry;
            if (inquiry != _lastInquiry)
            {
                _lastInquiry = inquiry;
                if (Police.SummonsEllis(inquiry))
                {
                    _osseiCalmUntilDay = 0;
                    if (!EllisSpawned) SpawnOssei();
                    _gossip.Mill.RumorHalfLifeHours =
                        Police.RumorHalfLifeHours(inquiry, EllisSetup.PresenceRumorHalfLifeHours);
                    string line = Police.Describe(inquiry);
                    if (!string.IsNullOrEmpty(line)) _ui?.Toast(line, 10f);
                }
                ApplySuspicionFloor(inquiry);
                return;
            }
            if (Police.SummonsEllis(inquiry))
            {
                // Applied EVERY tick, not only on the frame the stage
                // changed. The crowd promotes new gossipers as the player
                // moves, and somebody who walked onto the street after the
                // killing would otherwise be the one person on it who had
                // not heard.
                ApplySuspicionFloor(inquiry);
                return;     // and no calm-down path once there is a case
            }

            if (!EllisSpawned && heat >= EllisSetup.SpawnHeatThreshold) { SpawnOssei(); return; }
            if (EllisSpawned && _osseiCalmUntilDay > 0 && Now.Day > _osseiCalmUntilDay
                && heat >= EllisSetup.SpawnHeatThreshold)
            {
                _osseiCalmUntilDay = 0;
                if (_gossip != null && _gossip.Mill != null)
                    _gossip.Mill.RumorHalfLifeHours = EllisSetup.PresenceRumorHalfLifeHours;
                _ui?.Toast("The tan coat is back at the market corner, unhurried as ever. The street's stories stop dying young again.", 9f);
            }
        }

        /// A FLOOR, not a raise: the reason it is there does not go away, so
        /// re-applying it every tick must not compound. Written as "lift to
        /// the floor" rather than "add" for exactly that reason.
        void ApplySuspicionFloor(Inquiry inquiry)
        {
            double floor = Police.SuspicionFloor(inquiry);
            if (floor <= 0 || _gossip?.Mill == null) return;
            foreach (var a in _gossip.Mill.Agents)
                if (a.Suspicion.Value < floor)
                    a.Suspicion.Raise(floor - a.Suspicion.Value, "there is a body and everybody knows it");
        }

        void SpawnOssei()
        {
            if (EllisSpawned) return;
            EllisSpawned = true;

            var walker = NpcWalker.Spawn("Ellis", EllisSetup.Color, new[]
            {
                (new GameTime(0, 9, 0), new Vector3(10, 0, -14)),   // market corner, listening
                (new GameTime(0, 12, 0), NearBar(3, 2)),
                (new GameTime(0, 15, 0), new Vector3(18, 0, 14)),   // the docks
                (new GameTime(0, 19, 0), new Vector3(-14, 0, 10)),  // apartment row
                (new GameTime(0, 22, 0), new Vector3(4, 0, -4)),    // a corner with a view, at night
            });
            _npcs.Add(walker); // she walks and talks; she is NOT added to the gossip mill
            _osseiWalker = walker;
            _ossei = walker.gameObject.AddComponent<ConversationHost>();
            _ossei.Initialize(this, EllisSetup.CardMarkdown, null, null);
            _ossei.SceneContext = "On Hook Street, unhurried, notebook in hand, talking with the new landlord.";
            _ossei.ExtraContext = () =>
            {
                var sb = new System.Text.StringBuilder();
                sb.Append($"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week. ");
                // She has been interviewing the street: she knows what the loudest
                // stories ARE (not whether they're true) and probes around them.
                var leads = _gossip != null && _gossip.Mill != null ? _gossip.Mill.Leads("player") : null;
                if (EllisInterviews.Count > 0)
                {
                    sb.Append("Witness statements you hold: ");
                    for (int i = System.Math.Max(0, EllisInterviews.Count - 2); i < EllisInterviews.Count; i++)
                        sb.Append($"\"{EllisInterviews[i]}\" ");
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
                _gossip.Mill.RumorHalfLifeHours = EllisSetup.PresenceRumorHalfLifeHours;

            _ui?.Toast("A stranger is working Hook Street. Tan coat, level voice, takes her time. Asks about you.", 10f);
        }

        // The bar door. There is no interior in the graybox, so "going inside"
        // is proximity with hysteresis: you hear the door when you arrive, and
        // you have to actually leave before you can hear it again. Without the
        // gap it would rattle every time you shifted your weight on the step.
        const float DoorNear = 2.0f, DoorFar = 3.5f;
        bool _atTheDoor;

        void CheckBarDoor()
        {
            if (_player == null || SimMode.Days > 0) return;
            float d = Vector3.Distance(
                new Vector3(_player.transform.position.x, 0, _player.transform.position.z),
                new Vector3(WorldBuilder.BarDoor.x, 0, WorldBuilder.BarDoor.z));
            if (!_atTheDoor && d <= DoorNear) { _atTheDoor = true; Audio.Ui("door"); }
            else if (_atTheDoor && d >= DoorFar) _atTheDoor = false;
        }

        /// §6.4 top rung: an NPC at Confronting suspicion blocks the player's path
        /// and demands answers — the conversation opens itself.
        void CheckConfrontations()
        {
            if (_gossip == null || _gossip.Mill == null || _player == null || _ui == null) return;
            foreach (var npc in _npcs)
            {
                if (npc == null || npc.DisplayName == "Ellis") continue;
                var g = _gossip.Mill.Get(npc.GossipId);
                if (g == null || g.Leashed) continue;
                if (g.Suspicion.Level != SuspicionLevel.Confronting) continue;
                if (_confrontedDay.TryGetValue(npc.DisplayName, out var d) && d == Now.Day) continue;
                if (Vector3.Distance(npc.transform.position, _player.transform.position) > WarnRange) continue;

                _confrontedDay[npc.DisplayName] = Now.Day;
                TotalConfrontations++;
                var host = npc.GetComponent<ConversationHost>();
                if (host == null) continue;
                Audio.Ui("dread");
                _ui.Toast($"{npc.DisplayName} steps into your path. This isn't a chat.", 6f);
                _ui.ForceDialogue(host);
                break; // one ambush at a time
            }
        }

        /// The open city keeps a social calendar of its own: every few days the
        /// person who thinks best of you asks for an evening. Without this the
        /// honest life simply stops after day 7, and Act II's collision has
        /// nothing to interrupt.
        /// The person a beat's HostId names, for the player's eyes: a crowd
        /// resident's id is "r0123" and must never reach a toast (audit
        /// 2026-07-27).
        string HostName(string hostId) => _gossip?.Mill?.Get(hostId)?.DisplayName ?? hostId;

        /// The walker a beat's host is standing in: cast walkers go by display
        /// name (their id IS their name), promoted crowd residents by resident
        /// id. Matching DisplayName against a crowd id made every generated
        /// evening with a promoted resident unattendable (audit 2026-07-27).
        NpcWalker WalkerForHost(string hostId)
        {
            foreach (var n in _npcs) if (n != null && n.DisplayName == hostId) return n;
            return _crowdWalkers.TryGetValue(hostId, out var w) ? w : null;
        }

        void OfferEvening()
        {
            if (!Campaign.OpenMode || _gossip == null || _gossip.Mill == null) return;
            if (Now.Day < ActTwo.LastEveningDay + ActTwoState.EveningEveryNDays) return;
            if (Now.Hour < 9 || Now.Hour >= 20) return;
            if (Beats.Open(Now) != null) return;
            foreach (var b in Beats.All) if (b.State == BeatState.Pending && b.Day >= Now.Day) return;

            Gossiper best = null;
            foreach (var a in _gossip.Mill.Agents)
                if (a.Circle == "day" && !a.Leashed && (best == null || a.Loyalty > best.Loyalty)) best = a;
            if (best == null || best.Loyalty < 0.5) return;

            ActTwo.LastEveningDay = Now.Day;
            var id = $"evening_d{Now.Day}";
            Beats.Add(new Beat
            {
                Id = id, HostId = best.Id, Title = $"An evening with {best.DisplayName}", Day = Now.Day,
                StartHour = 21, EndHour = 24,
                InviteText = $"{best.DisplayName} catches you on the street, almost shy about it: \"Come by tonight. Nine, after you close. Nothing formal — I just haven't seen you properly in weeks.\"",
            });
        }

        void UpdateBeats()
        {
            if (_gossip == null || _gossip.Mill == null) return;
            OfferEvening();

            // Morning invitation, once, on the beat's day.
            var today = Beats.For(Now.Day);
            if (today != null && today.State == BeatState.Pending && Now.Hour >= 9 && _beatInvited.Add(today.Id))
                _ui?.Toast(today.InviteText, 10f);

            // Lapsed windows resolve to skipped — people remember.
            foreach (var missed in Beats.ResolveLapsed(id => _gossip.Mill.Get(id), Now))
                _ui?.Toast($"You never went. {HostName(missed.HostId)} will remember that.");

            var open = Beats.Open(Now);
            if (open == null || _beatMarkerId != open.Id)
            {
                // Marker must always belong to the currently open beat — destroy on
                // close AND on any beat change, so a stale marker can never attend
                // a different beat than the one it stands for.
                if (_beatMarker != null) { Destroy(_beatMarker); _beatMarker = null; }
                _beatMarkerId = null;
                // The host gets their evening back the moment the invitation
                // is no longer open — whether it was attended or stood up.
                ReleaseWaitingHost();
                if (open == null) return;
            }
            // Generated evenings have no authored spot: use the host's own
            // doorstep, wherever the day has left them standing.
            if (!_beatSpots.ContainsKey(open.Id))
            {
                var hostWalker = WalkerForHost(open.HostId);
                if (hostWalker != null) _beatSpots[open.Id] = hostWalker.transform.position;
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
                float toMarker = Vector3.Distance(new Vector3(p.x, 0, p.z), new Vector3(m.x, 0, m.z));

                // A BEAT IS A PERSON, NOT A COORDINATE.
                //
                // The spot is captured once, when the beat opens, from wherever
                // the host happened to be standing — and then the host walks
                // off, or the spot turns out to sit inside a doorway, or on the
                // far side of a railing. Nine days of CI say the bot got to
                // four metres of it and stopped, every time, and never
                // attended: [tea:Skipped,toast:Skipped,evening_d8:Skipped,
                // evening_d12:Skipped]. That is not a sim quirk. A player who
                // walks to a porch and finds the invitation four metres inside
                // a wall cannot attend it either.
                //
                // So the host's OWN position counts too. Turning up to where
                // somebody is standing is what accepting an invitation means,
                // and it cannot be made unreachable by a bad capture.
                var host = WalkerForHost(open.HostId);
                float toHost = host != null
                    ? Vector3.Distance(new Vector3(p.x, 0, p.z),
                                       new Vector3(host.transform.position.x, 0,
                                                   host.transform.position.z))
                    : float.MaxValue;

                // And the radius is 3.2 rather than 2.5. Two and a half metres
                // is close enough to shake hands over; a porch conversation you
                // have to stand that precisely for is fussy in a way no player
                // would describe as difficulty.
                if (Mathf.Min(toMarker, toHost) < BeatAttendMetres)
                {
                    open.Attend(_gossip.Mill.Get(open.HostId), Now);
                    ReleaseWaitingHost();
                    Destroy(_beatMarker);
                    _beatMarker = null;
                    _beatMarkerId = null;
                    // The collision outranks the pleasant acknowledgment — the
                    // second toast overwrote the first in the same frame, so
                    // the acknowledgment displayed for zero frames whenever
                    // PP4 fired (audit 2026-07-27). One moment, one toast.
                    bool pp4Before = ActTwo.Pp4Fired;
                    FireCollision(open);
                    if (ActTwo.Pp4Fired == pp4Before)
                        _ui?.Toast($"{open.Title}. You stayed a while. {HostName(open.HostId)} will remember this.", 8f);
                }
            }
        }

        int _lastWorldDay = -1;

        /// The day-boundary systems that belong to the WORLD rather than to the
        /// campaign: wounds turning, purses filling, somebody going to their
        /// patron overnight.
        ///
        /// These used to live inside UpdateCampaign, which returns the moment
        /// the verdict settles — so the day the player lost the week was the day
        /// every wound in the city stopped healing and every drawer stopped
        /// refilling. The comment on that early return says "world keeps
        /// turning" and it was the only part of the file that did not.
        ///
        /// A wound does not care whether you lost the week.
        void TickWorldDay()
        {
            if (Now.Hour < 8 || Now.Day <= _lastWorldDay) return;
            // Each CALENDAR day since the last tick, not one tick per call:
            // the Fall jumps the clock three days, and those days happened to
            // the city — purses filled three times, wounds cooled three steps,
            // debts ran three nights. The single-step version quietly made a
            // fall an economic freeze (audit 2026-07-27). Wounds that turned
            // while the player was away are announced on the morning they get
            // back, which is when they would hear about them anyway.
            int from = _lastWorldDay < 0 ? Now.Day : _lastWorldDay + 1;
            _lastWorldDay = Now.Day;
            for (int day = from; day <= Now.Day; day++)
            {
                Purses.DailyTick(day, Economy.Prosperity);
                if (_gossip != null && _gossip.Mill != null)
                    Debts.NightBorrowing(Purses, _gossip.Mill, new GameTime(day, 8, 0));

                // The line is a person's circumstance, so it goes out the same
                // channel as the economy's.
                foreach (var turned in Harm.DailyTick(day))
                    _ui?.Toast(turned, 11f);
            }
        }

        void UpdateCampaign()
        {
            if (Campaign.Verdict != Verdict.Ongoing) return; // stakes are settled; the world is ticked elsewhere

            // Daily close at the bar's morning open: bank takings taxed by the
            // street's current heat, and advance the exposure fuse.
            if (Now.Hour >= 8 && Now.Day > _lastClosedDay)
            {
                _lastClosedDay = Now.Day;
                double heat = CurrentHeat;
                // BEING KNOWN FADES, on its own clock. Here rather than inside
                // `CloseDay` because that method returns the day's takings and
                // is about the OUTFIT's ledger; reputation is the street's, and
                // hiding a second decay inside a money function is how the two
                // would drift apart without anybody noticing.
                Campaign.FadeNotoriety();
                // AND SHE MAY RING. Here for the same reason the decay is
                // here: this instant is the one every system in the game
                // agrees is "a day", and giving the rival a clock of her own
                // is the two-clocks shape that has already cost this project
                // the arms, the billboards and the foot plant.
                SummonsHost.Nightly(this);
                // AND THE PAPER, for the night that just ended. Same instant as
                // the call for the same reason: a system with a clock of its
                // own is a system that drifts from the day everything else
                // means.
                PressHost.Nightly(this);
                // AND WHETHER THE STREET HAS NOTICED YOU KEEP NOT TURNING UP.
                // Same instant as the paper and the rival's call, for the same
                // reason: a system with a clock of its own drifts from the day
                // everything else means.
                ReliabilityHost.Nightly(this);
                int takings = Campaign.CloseDay(heat);

                // M18. THE NIGHT THAT JUST ENDED, and where the player spent it.
                //
                // Scored here because this is the moment the day actually turns
                // — the same instant the till is counted and the fuse advances.
                // Anywhere else and "a night" would be a different length from
                // the one every other system means by it.
                if (_player != null)
                {
                    Household.CloseNight(Now.Day, _player.transform.position,
                                         cleanGiven: 0, heat: heat);
                    Household.WireTalkers(_gossip != null ? _gossip.Mill : null, Now);
                }
                // AND WHETHER THE ONE AT YOUR SHOULDER IS STILL YOURS.
                //
                // Asked nightly rather than at the moment of any particular
                // act, because loyalty moves for reasons that have nothing to
                // do with the companion: `Empire` squeezes it, a skimmed cut
                // erodes it, the rival poaches against it. A departure that
                // could only fire on a player action would miss every one of
                // those — which is the same shape as a system built and never
                // called, one step subtler.
                if (Companion.Current != null && _gossip != null)
                    Companion.CheckLoyalty(_gossip.Mill.Get(Companion.Current.Id), Now.Day);
                // AND WHAT THEY SEE THAT YOU DO NOT, which nothing has ever
                // asked for.
                //
                // `WatchersTheyAdd` is the half of the companion trade the
                // PLAYER gets — who is watching from where she stands that is
                // not watching from where you stand — and it is what makes
                // where she walks a real thing rather than a modifier on a
                // stat. It had no callers, so `LastAdds` sat at its
                // initialiser and `adds=0` has been in every verdict this
                // project has kept.
                //
                // TWO INSTRUMENTS AGREED BEFORE ANYTHING WAS CHANGED.
                // `gates.py --constant` listed `adds=0` as a reading that has
                // never been anything else across 131 runs, and
                // `lint-unreached.py` listed the method as one nothing names.
                // Neither could have found it alone: the first cannot say why a
                // number is stuck, and the second cannot say whether an unnamed
                // method matters.
                //
                // NIGHTLY, LIKE THE LOYALTY CHECK IT SITS BESIDE, and for a
                // harder reason than symmetry: it sweeps every walker in the
                // scene with a sightline test apiece, and the frame gate is
                // already red. Once a night is what a reading costs; once a
                // frame is what a reading costs when nobody checks.
                if (Companion.Current != null && _player != null)
                    Companion.WatchersTheyAdd(_player.transform);
                // The licence is under review: the bar's own till stays shut.
                if (ActTwo.BarFrozen(Now)) takings = 0;
                // Owned fronts pay clean and get heat-taxed exactly like the bar
                // — a front is a front. Their washing capacity joins the till's.
                // The machine's inspections (stage 2+) slow every front you own,
                // and a signed cap slows them further.
                double frontFactor = Empire.FrontFactor;
                // The street's own state, as it stands this morning: how much
                // money the district's people have, what things cost, and whether
                // anyone is still delivering. Neutral at 1.0 on an unsqueezed
                // street, so a campaign that takes nothing is unchanged by it.
                takings = (int)System.Math.Round(takings * Economy.FactorFor("bar"));
                foreach (var b in Empire.Businesses)
                    if (b.Owned && b.CleanIncomePerDay > 0)
                        takings += (int)System.Math.Round(b.CleanIncomePerDay * frontFactor
                            * Economy.FactorFor(b.Id) * System.Math.Max(0.0, 1.0 - 0.85 * heat));
                Wallet.EarnClean(takings);
                if (takings > 0) Audio.Ui("coin");
                TotalTakings += takings;
                LastTakings = takings;
                Wallet.LaunderPerDay = 120 + Empire.OwnedLaunderCapacity;
                int washed = Wallet.Launder();
                // The empire's day settles with the books (open mode only): racket
                // takes, witnesses into the mill, the rival's daily read.
                int racketToday = 0;
                string streetLine = null;
                if (Campaign.OpenMode && _gossip != null && _gossip.Mill != null)
                    // The street's own factor, same as the bar's till: a district
                    // you have starved cannot pay a full round (decision 9).
                    foreach (var ev in Empire.DailyTick(Now, Wallet, _gossip.Mill, Economy.FactorFor(null)))
                    {
                        if (ev.Kind == "income") racketToday += ev.Amount;
                        else streetLine = ev.Text; // rival/crew/witness — the last one speaks
                    }

                // The district settles LAST, on what actually happened today, so
                // tomorrow's takings reflect what you took tonight. Wages are what
                // stays on the street: a generous cut is economic policy, and a
                // skimmed envelope takes money out of the neighbourhood twice.
                int wagesToday = 0;
                foreach (var c in Empire.ActiveCrew)
                    if (c.Assignment != null)
                        wagesToday += c.Cut == "generous" ? 25 : c.Cut == "skim" ? 0 : 10;
                var economyLine = (string)null;
                foreach (var ev in Economy.DailyTick(Now, Wallet, racketToday, wagesToday, heat))
                    if (ev.Kind != "supply") economyLine = ev.Text;  // deliveries are quiet; trouble talks

                // Purses fill from the same prosperity the bar drinks from
                // (roadmap M13), so squeezing the street drains the pockets you
                // are trying to collect from — a few days later, when you have
                // started relying on being paid. Then anybody you emptied who
                // still owes goes to whoever they have, overnight, and the cost
                // of that asking is theirs to carry, not yours to see.
                var line = ActTwo.BarFrozen(Now)
                    ? "The bar stays shut: the licence is under review, and the notice is taped to your own door."
                    : takings >= Campaign.BarBaseTakings
                    ? $"Bar takings: +£{takings}."
                    : $"Bar takings: +£{takings}. The talk on the street is costing you.";
                if (washed > 0) line += $" £{washed} of night money washed through the till.";
                _ui?.Toast(line);
                if (streetLine != null) _ui?.Toast(streetLine, 11f);
                if (economyLine != null) _ui?.Toast(economyLine, 11f);

                // The Director (roadmap M8): fire whatever it scheduled for
                // today, settle any demand whose window has passed, and — only
                // in the open city, and only every few days — let it read the
                // state and author the next pressure. Fire-and-forget: a slow
                // or failed nightly pass must never hold up the morning.
                FireDuePressures();
                CheckDemands();
                if (Campaign.OpenMode) RunDirectorAsync();

                int talk = 0;
                foreach (var k in Knowledge.Entries) if (!k.Handled) talk++;
                _ui?.ShowDaySummary(Now.Day - 1, takings, washed, talk,
                    StreetWord(heat), OutfitWord(Campaign.OutfitPatience), Wallet.Clean, Wallet.Dirty, racketToday);

                // THE THREAD THAT IS STILL OPEN (design-doc §4). The document
                // promises "an unresolved thread every evening — the sim
                // guarantees one" and nothing implemented it until 18 Aug.
                // Read here rather than inside the summary panel because the
                // sim closes days with no UI at all, and a retention promise
                // that only exists when somebody is looking at a screen cannot
                // be measured across a run.
                // ONE STATE, READ ONCE. `Tonight` and `OpenCount` are two
                // walks over the same rules, so building the evening twice
                // would let them disagree about a day that changed between
                // the two calls — and the whole point of the count is that it
                // describes the same evening the thread came from.
                var evening = EveningState(Now.Day - 1);
                var tonight = LooseEnds.Tonight(evening);
                LooseEndsTally.Saw(tonight, LooseEnds.OpenCount(evening));
                // AND THE CREW READING FROM THIS SAME EVENING, whether or not
                // the Crew tier won it. A tier that loses to a higher-ranked
                // one still had its condition evaluated, and counting only
                // winners makes "never fires" and "never true" identical —
                // which is precisely the ambiguity that left this tier
                // unexplained for the project's whole recorded history.
                //
                // Empty name means no crew member is nearest-to-breaking, so
                // there is nothing to read; -1 says so rather than passing a
                // loyalty of zero, which would read as maximum disloyalty.
                LooseEndsTally.SawCrew(
                    string.IsNullOrEmpty(evening.CrewNearestBreaking) ? -1 : evening.CrewLoyalty,
                    evening.CrewBreakingPoint,
                    tonight.Of == LooseEnds.Kind.Crew);
                if (tonight.Any)
                {
                    _ui?.Toast(tonight.Line, 9f);
                    Debug.Log($"LooseEnds: day {Now.Day - 1} {tonight.Of} — {tonight.Line}");
                }
                else
                {
                    // SAID OUT LOUD, because this is the case that decides
                    // whether the planting half is worth building. A quiet
                    // evening that logs nothing is indistinguishable from the
                    // pass not running.
                    Debug.Log($"LooseEnds: day {Now.Day - 1} NOTHING OPEN");
                }

                // The bookkeeper sees a hoard the till can't explain. Diegetic
                // "unexplained money" pressure (design-doc §6.7) — small, daily.
                if (Wallet.Dirty > Wallet.LaunderPerDay && _lena != null)
                {
                    _lena.Suspicion.Raise(0.04, "cash keeps appearing that the books cannot explain");
                    _lena.Memory.Append(new MemoryEvent(Now, "observation", 0.6,
                        "Counted the till again. There is money moving through this pub that no tap sold."));
                }
                // June, the moral mirror (her approved card): her regard tracks
                // inversely to the empire and directly to the honest life. She
                // is not judging the money; she watched this exact shape eat
                // her father, and she is counting the same things twice.
                var juneG = _gossip?.Mill?.Get("June");
                if (juneG != null && Campaign.OpenMode)
                {
                    int holdings = Empire.Businesses.FindAll(b => b.Owned).Count
                        + Empire.Rackets.FindAll(r => r.Established).Count;
                    if (holdings > 0) juneG.Loyalty = System.Math.Clamp(juneG.Loyalty - 0.02 * holdings, 0, 1);
                    if (Job.WorkedYesterday(Now)) juneG.Loyalty = System.Math.Clamp(juneG.Loyalty + 0.03, 0, 1);
                }

                // The cover of honest work (§6.6): a day walked in company
                // uniform lets the day circle breathe out a little.
                if (Job.WorkedYesterday(Now) && _gossip != null && _gossip.Mill != null)
                    foreach (var a in _gossip.Mill.Agents)
                        if (a.Circle == "day")
                            a.Suspicion.Lower(0.02, "steady work reads honest");

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
                // PP2 — the first ask is authored: the runner names Mickey's
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
                Campaign.JobMissed(Now.Day);
                // The independence path is systemic: skipping drops IS the break.
                // When the street already pays you, the silence reads as intent —
                // to you, and to the Dockside arm, who now call it competition.
                if (Campaign.OutfitCutOff && Empire.TotalRacketIncome > 0)
                {
                    Empire.Rival.Attention = System.Math.Clamp(Empire.Rival.Attention + 0.25, 0, 1);
                    _ui?.Toast("You let the silence speak. The outfit stops calling — and the Dockside arm starts calling you what you are now: competition.", 12f);
                }
                else _ui?.Toast(Campaign.OutfitCutOff
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
                    Campaign.JobDone(Now.Day);
                    Wallet.EarnDirty(Campaign.JobPay);
                    Audio.Ui("coin");
                    double conf = WearingCoat ? CoatWitnessConfidence : 1.0;
                    // What they arrived in, and where. The coat lowers confidence
                    // in the face; it does nothing at all to the car.
                    string sawVehicle = VehicleSeenAt(p);
                    string where = Ledger.Core.StreetMap.AddressOf(p.x, p.z);
                    var seen = _gossip != null
                        ? _gossip.WitnessNightJob(p, Now.Day, Now, conf, sawVehicle, where)
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
                    string carNote = sawVehicle == null ? "" : $" And {sawVehicle} they can describe.";
                    _ui?.Toast(seen.Count > 0
                        ? WearingCoat
                            ? $"Drop made. +£{Campaign.JobPay} dirty. {string.Join(" and ", seen)} saw a figure in a coat.{carNote}"
                            : $"Drop made. +£{Campaign.JobPay} dirty. {string.Join(" and ", seen)} saw you — and your face.{carNote}"
                        : $"Drop made. +£{Campaign.JobPay} dirty.");
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
                if (b.HostId != walkerName && HostName(b.HostId) != walkerName) continue;
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

        /// The self-test writes its own file: every SaveNow call site runs in
        /// sim mode too (the sim asserts autosave), and before this split a
        /// -simdays run on a dev machine overwrote the real campaign's save
        /// with the bot's world (audit 2026-07-27).
        public string SavePath => System.IO.Path.Combine(Application.persistentDataPath,
            SimMode.Days > 0 ? "ledger-save-sim.json" : "ledger-save.json");

        Dictionary<string, object> ExtraFlags() => new Dictionary<string, object>
        {
            { "empire", Empire.Capture() },
            { "economy", Economy.Capture() },
            { "harm", Harm.Capture() },
            { "purses", Purses.Capture() },
            { "osseiInterviews", CaptureStrings(EllisInterviews) },
            { "interviewed", CaptureStrings(_interviewed) },
            { "director", Directorate.Capture() },
            { "homicides", Homicides.ToJson() },
            { "dead", CaptureStrings(_deadIds) },
            { "demands", CaptureDemands() },
            { "population", CapturePopulation() },
            { "access", CaptureAccess() },
            { "targets", CaptureTargets() },
            { "dayjob", Job.Capture() },
            { "acttwo", ActTwo.Capture() },
            { "actthree", CaptureActThree() },
            { "wearingCoat", WearingCoat }, { "osseiSpawned", EllisSpawned },
            { "totalTakings", TotalTakings }, { "lastTakings", LastTakings },
            { "nightWitnesses", NightWitnesses }, { "anyCoatedWitnessed", AnyCoatedWitnessed },
            { "maxCoatedWitnessConf", MaxCoatedWitnessConf }, { "totalConfrontations", TotalConfrontations },
            { "jobPostedDay", _jobPostedDay }, { "lastClosedDay", _lastClosedDay },
            { "lastReflectedDay", _lastReflectedDay }, { "observedPeakHeat", ObservedPeakHeat },
            { "osseiCalmUntil", _osseiCalmUntilDay },
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
                WriteSafely(SavePath, CaptureSave());
                if (!quiet) _ui?.Toast("The ledger is written. (Saved.)", 3f);
            }
            catch (System.Exception e) { Debug.LogError($"Save failed: {e.Message}"); }
        }

        /// Cmd-Q, the red button, the window's close box. Until 15 Aug none
        /// of them saved: the pause menu's "Save and quit" was the only exit
        /// that kept the evening, and on a laptop passed between three people
        /// the OS quit is the exit somebody WILL use. The MonoBehaviour
        /// message rather than `Application.wantsToQuit`, deliberately — the
        /// static event outlives this controller, and a session-per-reload
        /// game that subscribes each session leaks a dead handler per
        /// restart. `SaveNow` already guards the too-early case, and the sim
        /// writes to its own split path.
        void OnApplicationQuit() => SaveNow(quiet: true);

        /// A manual copy in a numbered drawer (P2). Same codec, own file.
        public void SaveToSlot(int slot)
        {
            if (_gossip == null || _gossip.Mill == null) return;
            try
            {
                WriteSafely(SaveSlots.SlotPath(slot), CaptureSave());
                _ui?.Toast($"A copy of the ledger goes in the drawer. (Day {Now.Day}.)", 4f);
            }
            catch (System.Exception e) { Debug.LogError($"Slot save failed: {e.Message}"); }
        }

        /// Write-then-swap, keeping the previous good file as .bak (P2:
        /// corruption recovery). A crash mid-write costs the .tmp, never the
        /// save; a corrupted save falls back to the backup on load.
        static void WriteSafely(string path, string json)
        {
            var tmp = path + ".tmp";
            System.IO.File.WriteAllText(tmp, json);
            if (System.IO.File.Exists(path))
            {
                try { System.IO.File.Replace(tmp, path, path + ".bak"); }
                catch (System.Exception)
                {
                    // Replace can refuse across volumes or on exotic mounts;
                    // the slow road reaches the same end state.
                    System.IO.File.Copy(path, path + ".bak", overwrite: true);
                    System.IO.File.Copy(tmp, path, overwrite: true);
                    System.IO.File.Delete(tmp);
                }
            }
            else System.IO.File.Move(tmp, path);
        }

        /// Set by the menus before the controller boots: which file "Continue"
        /// or a slot copy actually opens. Null means the autosave.
        public static string PendingLoadPath;

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
                var loadPath = PendingLoadPath ?? SavePath;
                PendingLoadPath = null;
                if (!System.IO.File.Exists(loadPath)) return;
                var rawSave = System.IO.File.ReadAllText(loadPath);
                bool recovered = false;
                GameTime now;
                Dictionary<string, object> extra;
                try
                {
                    now = SaveCodec.Restore(rawSave,
                        Wallet, Campaign, Knowledge, HooksBook, Beats, _gossip.Mill, Debts, out extra);
                }
                catch (SaveIncompatibleException e) when (e.Fault == SaveFault.Unreadable
                    && System.IO.File.Exists(loadPath + ".bak"))
                {
                    // P2 corruption recovery: the write-behind backup is the
                    // last GOOD ledger. The bad file is set aside, not deleted
                    // — a hand recovery stays possible.
                    SaveSlots.Quarantine(loadPath);
                    rawSave = System.IO.File.ReadAllText(loadPath + ".bak");
                    now = SaveCodec.Restore(rawSave,
                        Wallet, Campaign, Knowledge, HooksBook, Beats, _gossip.Mill, Debts, out extra);
                    recovered = true;
                }
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
                _osseiCalmUntilDay = FlagI(extra, "osseiCalmUntil");
                ActOne.Pp1Fired = FlagB(extra, "pp1");
                ActOne.Pp2Fired = FlagB(extra, "pp2");
                ActOne.Pp4Fired = FlagB(extra, "pp4");
                var posture = extra.TryGetValue("posture", out var po) ? po as string : null;
                ActOne.Posture = string.IsNullOrEmpty(posture) ? null : posture;
                ActOne.NoorDrawersEngaged = FlagB(extra, "noorDrawers");
                ActOne.NoorDrawersBroken = FlagB(extra, "noorBroken");
                if (extra.TryGetValue("empire", out var em)) Empire.Restore(MiniJson.AsObject(em));
                if (extra.TryGetValue("economy", out var ec)) Economy.Restore(MiniJson.AsObject(ec));
                if (extra.TryGetValue("director", out var di))
                {
                    Directorate.Restore(MiniJson.AsObject(di));
                    _lastDirectorDay = Directorate.LastRunDay;
                }
                if (extra.TryGetValue("homicides", out var hk)) Homicides.FromJson(MiniJson.AsObject(hk));
                _deadIds.Clear();
                foreach (var o in MiniJson.GetList(extra, "dead") ?? new List<object>())
                    if (o is string id) _deadIds.Add(id);
                // Reloading must not re-announce a killing from three days ago:
                // the stage is what it is, and the escalation toast fires on a
                // CHANGE. Seed the comparison from the restored world.
                _lastInquiry = PoliceInquiry;
                if (extra.TryGetValue("harm", out var hm)) Harm.Restore(MiniJson.AsObject(hm));
                if (extra.TryGetValue("purses", out var pu)) Purses.Restore(MiniJson.AsObject(pu));
                if (extra.TryGetValue("osseiInterviews", out var oi))
                {
                    EllisInterviews.Clear();
                    foreach (var o in MiniJson.AsList(oi) ?? new List<object>())
                        if (o is string line) EllisInterviews.Add(line);
                }
                if (extra.TryGetValue("interviewed", out var iv))
                {
                    _interviewed.Clear();
                    foreach (var o in MiniJson.AsList(iv) ?? new List<object>())
                        if (o is string key) _interviewed.Add(key);
                }
                if (extra.TryGetValue("demands", out var de)) RestoreDemands(MiniJson.AsList(de));
                if (extra.TryGetValue("population", out var pop)) RestorePopulation(MiniJson.AsObject(pop));
                // Second pass, AFTER the population layer has promoted crowd
                // residents back into the mill: their saved rumors, loyalty and
                // leashes were skipped in the first pass because the agents did
                // not exist yet (audit 2026-07-27). Idempotent for everyone else.
                SaveCodec.RestoreMillAgents(rawSave, _gossip.Mill);
                if (extra.TryGetValue("access", out var acc)) RestoreAccess(MiniJson.AsObject(acc));
                if (extra.TryGetValue("targets", out var tg)) RestoreTargets(MiniJson.AsList(tg));
                if (extra.TryGetValue("dayjob", out var dj)) Job.Restore(MiniJson.AsObject(dj));
                if (extra.TryGetValue("acttwo", out var a2)) ActTwo.Restore(MiniJson.AsObject(a2));
                // People who existed before the save must exist after the load.
                // Ellis always had this (below); the summit head and the
                // inspector did not, which soft-locked the Table and froze the
                // audit on any mid-act reload (audit 2026-07-27) — the verbs
                // they carry are only reachable by talking to them.
                if (ActTwo.TableArmId != null)
                {
                    var tableArm = Empire.ArmOf(ActTwo.TableArmId);
                    if (tableArm != null) SpawnHead(tableArm.Id, tableArm.HeadName);
                }
                if (extra.TryGetValue("actthree", out var a3)) RestoreActThree(MiniJson.AsObject(a3));
                if (ActThree.InspectorArrived && !ActThree.AuditClosed) SpawnInspector();
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
                // SpawnOssei resets the rumor half-life to its presence value;
                // if the save was made inside the post-Fall calm, put the calm
                // back (audit 2026-07-27).
                if (_osseiCalmUntilDay > Now.Day && _gossip != null && _gossip.Mill != null)
                    _gossip.Mill.RumorHalfLifeHours = 96;
                _ui?.Toast(recovered
                    ? $"The ledger's last page was water-damaged; the copy underneath opens instead. Day {Mathf.Min(Now.Day, Campaign.SurviveDays)}."
                    : $"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)}. The street remembers where you left it.", recovered ? 10f : 6f);
                if (Campaign.Verdict != Verdict.Ongoing) EndCampaign();
            }
            catch (System.Exception e) { Debug.LogError($"Load failed: {e.Message}"); }
        }

        static List<object> CaptureStrings(IEnumerable<string> lines)
        {
            var list = new List<object>();
            foreach (var line in lines) list.Add(line);
            return list;
        }

        static bool FlagB(Dictionary<string, object> d, string k) => d.TryGetValue(k, out var v) && v is bool b && b;
        static int FlagI(Dictionary<string, object> d, string k) => d.TryGetValue(k, out var v) && v != null ? System.Convert.ToInt32(v) : 0;
        static double FlagD(Dictionary<string, object> d, string k) => d.TryGetValue(k, out var v) && v != null ? System.Convert.ToDouble(v) : 0.0;

        void EndCampaign()
        {
            if (_jobMarker != null) { Destroy(_jobMarker); _jobMarker = null; }
            _ui?.ShowEnd(Campaign);
        }

        /// The drop marker steps aside from GEOMETRY — `PointClear` tests
        /// scenery, not people, so this cannot dodge a crowd (the courier's
        /// nine-tick stall beside the pub is addressed upstream: the prep
        /// walk now starts at 17:00, so the bot is away from the evening
        /// confab before it forms). What this does buy: a marker can no
        /// longer spawn inside a bin, a bench or the new shopfront trim,
        /// which the furniture pass made possible for the first time this
        /// week. Fixed search order, so the pick is stable per night.
        void SpawnJobMarker(Vector3 pos)
        {
            var at = pos;
            foreach (var step in new[] { 0f, 1.5f, 3f, 4.5f })
            {
                var c = new Vector3(pos.x + step, 0, pos.z);
                if (WorldBuilder.PointClear(c, 1.2f)) { at = c; break; }
                c = new Vector3(pos.x - step, 0, pos.z + step);
                if (WorldBuilder.PointClear(c, 1.2f)) { at = c; break; }
            }
            _jobMarker = SpawnGlowMarker(at, new Color(1f, 0.55f, 0.15f), "JobDrop");
        }

        GameObject SpawnGlowMarker(Vector3 pos, Color color, string name)
        {
            var marker = GameObject.CreatePrimitive(PrimitiveType.Cube);
            marker.name = name;
            marker.transform.position = new Vector3(pos.x, 0.3f, pos.z);
            marker.transform.localScale = new Vector3(0.9f, 0.6f, 0.9f);
            // A WAYPOINT IS NOT FURNITURE, AND THIS ONE WAS SOLID.
            //
            // `CreatePrimitive` ships a collider, and nothing here ever took it
            // off — so the glowing cube marking the place you must REACH is a
            // box you walk into and stop against. Every other primitive in this
            // project that exists to be looked at rather than bumped into has
            // its collider destroyed; this one was written before that habit and
            // nobody grepped for the second site.
            //
            // The drop trace is what sent me here. `d1:MISSED[from=22m
            // nearest=2.8m walked=21.2m held:job=17]` — the bot walked
            // twenty-one of twenty-two metres, steered at the drop for every
            // tick of the window, and finished THIRTY CENTIMETRES outside a
            // 2.5m completion radius. Beside it `d8:done[nearest=2.4m]`. The
            // arrivals cluster on the boundary, which is what an obstacle at
            // the target looks like from the outside.
            //
            // AND THE OBVIOUS FIX WAS THE FORBIDDEN ONE. A miss by 0.3m invites
            // widening the radius to 3.0 and calling it talking distance, which
            // is moving a bound to make red go away — rule 2 by name. The bound
            // is not what is wrong. The thing it measures the distance to is
            // pushing the player back out of it.
            var box = marker.GetComponent<Collider>();
            if (box != null) Destroy(box);
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

        /// 0 at noon, 1 in the dead of night. Read by the film grade.
        public static float NightAmount { get; private set; }

        /// THE AUDIO MIX, LIFTED OUT OF `UpdateSun` SO THE BUDGET CAN NAME IT.
        ///
        /// Every line here ran inside the `sun` timer, which is why that line
        /// read 3.15ms — a quarter of the whole 12ms game budget — for what
        /// looks like a directional light. Same work, same order, same frame;
        /// only the label changes, and `mix` against `sun` finally says which
        /// of the two the frame gate is actually complaining about.
        ///
        /// It reads `NightAmount`, which `UpdateSun` sets immediately before,
        /// so the argument that light and sound must come off ONE daylight
        /// number is preserved by ordering rather than by being in one method.
        void UpdateMix()
        {
            if (_sun == null) return;
            if (Audio.Ready) Audio.SetNight(Now.Hour >= 20 || Now.Hour < 6);
            if (Audio.Ready) Audio.SetDaylight(NightAmount);
            if (Audio.Ready) Audio.SetScore(ScoreNow(), Time.deltaTime);
            // The duck envelope, next to the score because they are the same
            // frame of the same mix. Was a boolean that snapped the music to
            // 35% and back, which breathes audibly on every line.
            if (Audio.Ready) Audio.StepMix(Time.deltaTime);
            // A FINISHED LINE, IF THERE IS ONE. Here because this is already
            // the one place per frame that advances the mix, so live speech
            // lands in the same frame as the ducking that makes room for it.
            if (Audio.Ready) Audio.PumpSpeech();
            // Release the standoff duck when its beat is over. Stepped here
            // because this is already the one place per frame that advances the
            // mix, and a second driver for one envelope is how a duck gets
            // stuck open.
            Standoff.Step();
        }

        void UpdateSun()
        {
            if (_sun == null) return;
            // The room changes with the light: day tone, night tone.
            // The music still swaps on a boundary — it is a different piece
            // of music, not a different time of day — but the ROOM now
            // crossfades continuously, below.
            // 06:00 sunrise, 18:00 sunset. TOWN-PLAN.MD T4, the noon fix:
            // the old mapping put the sun DIRECTLY OVERHEAD at midday
            // (dayFraction 0.5 -> 90 degrees), so vertical walls took no
            // direct light and shadows shrank to nothing — which is exactly
            // the dead pasted-on noon Jafar flagged, caused by an angle no
            // British sky ever reaches. Elevation now peaks at 52 degrees
            // (a northern port in summer) while the azimuth swings east to
            // west, so noon has real shadow direction and a lit side of the
            // street facing a shaded one. Outside daylight the elevation
            // clamps to the horizon; at 0.02 intensity the night cannot
            // tell, and the night is the half that already looks right.
            float dayFraction = (Now.Hour * 60 + Now.Minute) / 1440f;
            float dayT = Mathf.Clamp01((dayFraction - 0.25f) / 0.5f);
            float elev = Mathf.Sin(dayT * Mathf.PI) * 52f;
            float azim = Mathf.Lerp(70f, 290f, dayT);
            _sun.transform.rotation = Quaternion.Euler(elev, azim, 0);

            float daylight = Mathf.Clamp01(Mathf.Sin(dayFraction * Mathf.PI * 2f - Mathf.PI / 2f) + 0.15f);
            // Published so the film grade pushes the stock at night off the
            // SAME number the sun uses. Two independent notions of "how dark
            // is it" would drift, and the grain would peak at the wrong hour.
            NightAmount = 1f - daylight;
            // The contact blobs fade off the SAME number the sun and grade
            // use — the blob proxies the sun's contact shadow, so it must
            // dim on the sun's own clock.
            BlobShadow.Tick(NightAmount);

            // CLOUD SHADOWS, VIA THE LIGHT'S COOKIE (M17.10) — sun and cloud
            // modulation in one shadow path is the frame-study shape, and in
            // built-in it is a texture on the directional light. Built once;
            // the slow lateral drift below scrolls the projection, because a
            // directional cookie is anchored to the light's POSITION even
            // though its illumination is not. Wrapped modulo the cookie tile
            // so a nine-day sim cannot walk the float off its precision.
            if (_sun.cookie == null)
            {
                var ck = SceneLighting.BuildCloudCookie();
                if (ck != null) { _sun.cookie = ck; _sun.cookieSize = 220f; }
            }
            float ct = Time.time;
            _sun.transform.position =
                new Vector3((ct * 1.6f) % 220f, 0f, (ct * 0.9f) % 220f);
            // The mix moved to `UpdateMix`, called on the very next line of
            // `Update` and reading `NightAmount` which is set four lines up —
            // so light and sound still come off the SAME number and dusk still
            // cannot arrive at two different times. See the note at the call
            // site for why they are timed apart.
            // Rain flattens and cools the key light — an overcast sky is a big
            // soft source, not a small hard one (art pass 2026-07-28).
            float wet = Weather.Rain;
            // 1.15 → 1.65 at clear noon (M17.10 V1): against the new ambient
            // share the key:fill ratio lands near 4:1, which is what makes
            // the reference frames' noon read as DIRECTIONAL — a lamp post
            // lying on the pavement instead of a street lit from nowhere.
            // The wet multiplier stays: overcast really does flatten the key.
            _sun.intensity = Mathf.Lerp(0.02f, 1.65f, daylight) * Mathf.Lerp(1f, 0.45f, wet);
            _sun.color = Color.Lerp(
                Color.Lerp(new Color(1f, 0.55f, 0.35f), Color.white, daylight),
                new Color(0.72f, 0.78f, 0.88f), wet);

            // THE AMBIENT WRITES THAT USED TO SIT HERE WERE DEAD CODE, AND
            // THE VALUES BEING TUNED WERE THE CORPSE'S (M17.10 V1).
            // `SceneLighting.LateUpdate` has written all three ambient
            // colours from `LightModel` every frame since it gained its
            // LateUpdate — and LateUpdate runs after Update, so the three
            // `RenderSettings.ambient*` assignments here lost the frame,
            // every frame. One idea, two implementations; the live one is
            // `LightModel.Ambient*` via SceneLighting, and it is now the
            // ONLY one. The restricted-palette reasoning that stood here
            // lives on in `LightModel`'s colour functions, which are the
            // tested copy.
            // THE DAYTIME SKY WAS 2.6x THE SCENE, MEASURED.
            //
            // The first run whose diagnostics could be read reported, at clear
            // noon, `fogRGB=bgRGB=(0.600,0.645,0.700)` — luma 0.638 — against a
            // scene mean luma of 0.245. The sky was two and a half times
            // brighter than everything under it, which is why every noon still
            // came back looking blown out and flat: the brightest thing in
            // frame by a wide margin, with the buildings crushed into a narrow
            // band below it.
            //
            // THE PARAGRAPH THAT STOOD HERE HAD THE CAUSALITY BACKWARDS.
            // It reasoned that because the measured fog matched LightModel's
            // constants, "GameController runs last" — but this is Update and
            // SceneLighting writes fog in LateUpdate, so LateUpdate's
            // LightModel values win the composited frame and the calibrated
            // write that stood below won only mid-Update probe renders. The
            // 1.8x calibration is IN LightModel.FogColour now, single owner.
            //
            // Scaled to sit at ~1.8x the scene mean instead of 2.6x: an
            // overcast port-town sky is a shade above the street, not a
            // lightbox over it. That ratio is a calibrated step rather than a
            // known-correct number — the sky lines print every run, so the next
            // still says whether it wants to go further.
            //
            // NIGHT IS UNTOUCHED. It reads well and nothing here needs to
            // change it.
            // THE FOG WRITE THAT STOOD HERE IS GONE, AND ITS CALIBRATION
            // LIVES ON IN `LightModel.FogColour` (M17.10). The comment above
            // this block claimed GameController "runs last" and LightModel's
            // fog "never reaches the screen" — BACKWARDS: this is Update,
            // SceneLighting writes fog in LateUpdate, so the calibrated
            // values written here lost the composited frame every frame and
            // won only the probes that render mid-Update. That is exactly
            // the split the landed fog readings showed. One owner now:
            // SceneLighting writes `LightModel.FogColour`, which carries the
            // calibrated day arm and the warm sodium night arm both.

            // FOG DISTANCE USED TO BE SET HERE AND UNITY NEVER READ IT.
            //
            // `SceneLighting` sets `RenderSettings.fogMode =
            // FogMode.ExponentialSquared`, and that is the only assignment to
            // fogMode anywhere in the project. Exponential fog is driven by
            // `fogDensity`; `fogStartDistance` and `fogEndDistance` are read
            // ONLY in `FogMode.Linear`. So the three lines that stood here —
            // computing a tightness from daylight and `Weather.FogTightness`
            // and lerping both distances — wrote to two fields nothing sampled.
            //
            // "Weather and fog do the heavy lifting" is the load-bearing
            // sentence of this game's art direction, and half of it had been
            // wired to nothing. The comment that stood here claimed a
            // draw-distance win it was not delivering.
            //
            // Deleted rather than repaired, because the intent is already
            // implemented correctly one file over: `LightModel.FogDensity(night,
            // rain)` takes both time and weather and feeds the parameter the
            // chosen mode actually reads. This was a second, silent
            // implementation of the same idea, losing.

            // The sky is a gradient skybox whose horizon band IS the fog
            // colour (SceneLighting drives it every frame), so the horizon
            // still never shows a seam — the old guarantee, kept, with an
            // actual sky above it. SolidColor survives only as the fallback
            // for a build where the sky shader failed to load; its
            // background is written either way and is harmless under Skybox.
            var cam = Camera.main;
            if (cam != null)
            {
                cam.clearFlags = SceneLighting.SkyboxLive
                    ? CameraClearFlags.Skybox
                    : CameraClearFlags.SolidColor;
                // From the MODEL, not from RenderSettings: with the fog
                // single-ownered into SceneLighting.LateUpdate, reading
                // RenderSettings here in Update would hand back the previous
                // frame's value — harmless, but a second reader of shared
                // mutable state where a direct call is one line.
                var fbg = Ledger.Core.LightModel.FogColour(NightAmount, Weather.Rain);
                var fbgc = new Color((float)fbg.r, (float)fbg.g, (float)fbg.b);
                // Same conversion as SceneLighting's C() funnel, same reason
                // (display-authored colour, raw script assignment, linear
                // project) — and the background MUST agree with the fog it
                // mirrors or the horizon seam returns.
                cam.backgroundColor = QualitySettings.activeColorSpace == ColorSpace.Linear
                    ? fbgc.linear : fbgc;
            }
            WorldBuilder.SetLampsEnabled(daylight < 0.25f);
            WorldBuilder.TickNeon(daylight < 0.35f, Time.time);
            // WINDOWS WARM UP A TOUCH BEFORE THE STREET LAMPS — and which of
            // them warm up is now a fact about the city rather than all of them.
            //
            // `Occupancy.HomeFraction` asks the real population whether each
            // person is at work, out for the evening, or in, using the work
            // hours and circle the generator already gave them. The skyline
            // stops being a wall of identical rectangles, and it stops for a
            // reason a player can eventually use: a dark window means somebody
            // is not home.
            //
            // `Populace` may not exist yet on the first frames, and -1 is the
            // "no population" answer rather than "nobody is in" — the
            // distinction that decides between a normal night and a blackout.
            WorldBuilder.SetWindowsLit(
                daylight < 0.35f,
                Ledger.Core.Occupancy.HomeFraction(
                    Populace != null ? Populace.Residents : null, Now.Hour),
                Now.Hour);
        }
    }
}
