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
        public SecretsBook HooksBook { get; } = SecretsSetup.Build();
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
        GossipDirector _gossip;
        DialogueUI _ui;
        PlayerController _player;
        int _lastReflectedDay;
        int _lastAgedHour = -1;

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
        public Vector3? ActiveJobPos => _jobMarker != null ? (Vector3?)_jobMarker.transform.position : null;

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
                if (LastTakings < 0) return $"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week. {mood}{HostRevealText("Lena")}{SecretContext("Lena")}";
                var thin = LastTakings < Campaign.BarBaseTakings * 0.7
                    ? " You know the takings are thin because of what people are saying about the owner." : "";
                return $"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week. " +
                       $"Yesterday the bar took in ${LastTakings}.{thin} {mood}{HostRevealText("Lena")}{SecretContext("Lena")}";
            };
            _hosts.Add(_lena);

            // The rest of the cast gets conversation brains too — you can find the
            // witness and handle him directly instead of only hearing about it from Lena.
            foreach (var npc in _npcs)
            {
                var member = CastSetup.Get(npc.DisplayName);
                if (member == null) continue;
                var host = npc.gameObject.AddComponent<ConversationHost>();
                host.Initialize(this, member.Card, null, null);
                host.SceneContext = member.Scene;
                var walkerName = npc.DisplayName;
                host.ExtraContext = () =>
                    $"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week on Hook Street. " +
                    $"Talk about the new owner around the street is {StreetWord(CurrentHeat)}." +
                    $"{HostRevealText(walkerName)}{BeatContext(walkerName)}{SecretContext(walkerName)}";
                _hosts.Add(host);
            }

            _ui = DialogueUI.Create(this, player, _hosts);

            _gossip = gameObject.AddComponent<GossipDirector>();
            _gossip.Begin(this, _npcs, _hosts);

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
            UpdateBeats();
            if (Time.frameCount % 30 == 0) CheckLoyalWarnings();
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
                Wallet.EarnClean(takings);
                TotalTakings += takings;
                LastTakings = takings;
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
                if (Campaign.Verdict != Verdict.Ongoing) { EndCampaign(); return; }
            }

            // Night job lifecycle: posted at 22:00, open until 02:00, done by
            // standing at the glowing drop, missed if the window closes first.
            bool inWindow = Campaign.InJobWindow(Now);
            if (inWindow && Now.Hour >= 22 && _jobPostedDay != Now.Day)
            {
                _jobPostedDay = Now.Day;
                SpawnJobMarker(DropPoints[Now.Day % DropPoints.Length]);
                _ui?.Toast("The outfit wants a drop made tonight. Find the glow on the street before 02:00.");
            }
            if (_jobMarker == null) return;

            if (!inWindow)
            {
                Destroy(_jobMarker);
                _jobMarker = null;
                Campaign.JobMissed();
                _ui?.Toast("You missed the outfit's drop. They won't forget.");
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
                    _ui.Toast($"{name} pulls you aside: \"People are saying {lead.Summary}. Thought you should hear it from me.\"");
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
