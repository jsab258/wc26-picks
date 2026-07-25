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

        // The player's walking-around money. Starts modest so an early payoff hurts;
        // it grows through bar takings (taxed by street heat) and night work.
        public int PlayerCash = 250;

        public Campaign Campaign { get; } = new Campaign();
        public PlayerKnowledge Knowledge { get; } = new PlayerKnowledge();
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
                if (LastTakings < 0) return $"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week. {mood}{HostRevealText("Lena")}";
                var thin = LastTakings < Campaign.BarBaseTakings * 0.7
                    ? " You know the takings are thin because of what people are saying about the owner." : "";
                return $"Day {Mathf.Min(Now.Day, Campaign.SurviveDays)} of the new owner's first week. " +
                       $"Yesterday the bar took in ${LastTakings}.{thin} {mood}{HostRevealText("Lena")}";
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
                    $"Talk about the new owner around the street is {StreetWord(CurrentHeat)}.{HostRevealText(walkerName)}";
                _hosts.Add(host);
            }

            _ui = DialogueUI.Create(this, player, _hosts);

            _gossip = gameObject.AddComponent<GossipDirector>();
            _gossip.Begin(this, _npcs, _hosts);

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
            if (Time.frameCount % 30 == 0) CheckLoyalWarnings();
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
                PlayerCash += takings;
                TotalTakings += takings;
                LastTakings = takings;
                _ui?.Toast(takings >= Campaign.BarBaseTakings
                    ? $"Bar takings: +${takings}."
                    : $"Bar takings: +${takings}. The talk on the street is costing you.");
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
                    PlayerCash += Campaign.JobPay;
                    var seen = _gossip != null ? _gossip.WitnessNightJob(p, Now.Day, Now)
                        : new List<string>();
                    NightWitnesses += seen.Count;
                    // You saw them see you: each witness becomes a known lead.
                    foreach (var w in seen)
                        foreach (var lead in _gossip.Mill.Leads("player"))
                            if (lead.HolderId == w && lead.TopicKey == $"player.night_job_d{Now.Day}")
                                Knowledge.Learn(lead, $"you saw {w} watching", Now);
                    _ui?.Toast(seen.Count > 0
                        ? $"Drop made. +${Campaign.JobPay}. {string.Join(" and ", seen)} saw you."
                        : $"Drop made. +${Campaign.JobPay}.");
                }
            }
        }

        /// Loyal NPCs pull the player aside (once a day each) when carrying fresh
        /// talk about them — the ambient channel into PlayerKnowledge.
        void CheckLoyalWarnings()
        {
            if (_gossip == null || _gossip.Mill == null || _player == null || _ui == null) return;
            foreach (var npc in _npcs)
            {
                if (npc == null) continue;
                var name = npc.DisplayName;
                var g = _gossip.Mill.Get(name);
                if (g == null || g.Loyalty < WarnLoyaltyFloor) continue;
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
        /// the admissions become known leads. Called once per dialogue open.
        public void LearnFromHost(string walkerName)
        {
            if (_gossip == null || _gossip.Mill == null) return;
            var g = _gossip.Mill.Get(walkerName);
            if (g == null || g.Loyalty < RevealLoyaltyFloor) return;
            foreach (var lead in _gossip.Mill.Leads("player"))
                if (lead.HolderId == walkerName)
                    Knowledge.Learn(lead, $"{walkerName} admitted it", Now);
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

        void SpawnJobMarker(Vector3 pos)
        {
            _jobMarker = GameObject.CreatePrimitive(PrimitiveType.Cube);
            _jobMarker.name = "JobDrop";
            _jobMarker.transform.position = new Vector3(pos.x, 0.3f, pos.z);
            _jobMarker.transform.localScale = new Vector3(0.9f, 0.6f, 0.9f);
            var mat = _jobMarker.GetComponent<Renderer>().material;
            mat.color = new Color(1f, 0.55f, 0.15f);
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", new Color(1f, 0.45f, 0.1f) * 2.5f);

            var glow = new GameObject("JobGlow");
            glow.transform.SetParent(_jobMarker.transform, false);
            glow.transform.localPosition = Vector3.up * 1.5f;
            var l = glow.AddComponent<Light>();
            l.type = LightType.Point;
            l.range = 7f;
            l.intensity = 2.2f;
            l.color = new Color(1f, 0.6f, 0.25f);
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
