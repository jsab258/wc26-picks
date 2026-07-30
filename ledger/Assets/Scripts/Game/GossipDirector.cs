using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Wires the Core gossip mill to the in-world NPCs. Each NPC gets a social brain
    /// and a place in the day/night acquaintance graph; Lena reuses her real
    /// conversation brain, so anything that reaches her surfaces in dialogue. NPCs
    /// exchange talk only when they are physically near each other, so rumors travel
    /// at the speed the characters actually cross paths — the doorman carries a night
    /// secret to the bar, and it leaks into the daytime world from there.
    public class GossipDirector : MonoBehaviour
    {
        /// GAME minutes between gossip rounds, not real seconds.
        ///
        /// This was 3 REAL seconds, accumulated from Time.deltaTime — which
        /// Unity clamps to maximumDeltaTime. So on a slow machine the world
        /// clock advanced by real time while the gossip clock advanced by
        /// clamped frames, and the number of times talk spread in a game-day
        /// became a function of the runner's frame rate. Two CI runs of the same
        /// build ended the campaign on different DAYS because of it.
        ///
        /// It is the same bug class as the sim clock, in a file I did not think
        /// to look at when I fixed that one: anything that decides world state
        /// has to be driven by the world's clock. 6 game-minutes matches the old
        /// cadence at the normal 2 game-minutes-per-second, so ordinary play is
        /// unchanged.
        const float TickIntervalGameMinutes = 6f;
        /// A frame in the accelerated sim can cover a lot of game time; catch up
        /// rather than skip, so the number of rounds per game-day is fixed. Capped
        /// so a stall cannot spiral into hundreds of rounds in one frame.
        const int MaxCatchUpRounds = 8;
        const float TalkRange = 6f;

        GameController _game;
        GossipMill _mill;
        readonly Dictionary<string, NpcWalker> _walkers = new Dictionary<string, NpcWalker>();
        float _timer;
        GameTime _lastTickAt;
        bool _haveLastTick;

        public GossipMill Mill => _mill;
        /// The acquaintance graph, exposed so the crowd (roadmap M9) can wire
        /// its own neighbours in as residents enter the simulated band.
        public SocialGraph Graph { get; private set; }

        public void Begin(GameController game, List<NpcWalker> npcs, List<ConversationHost> hosts)
        {
            _game = game;
            foreach (var n in npcs) _walkers[n.DisplayName] = n;

            // Acquaintance graph. Rocco (the doorman) and Lena both work the bar;
            // Sam drifts between everyone; Ada is a daytime regular.
            var graph = new SocialGraph();
            graph.Link("Rocco", "Lena", 0.7);
            graph.Link("Rocco", "Sam", 0.8);
            graph.Link("Sam", "Lena", 0.6);
            graph.Link("Ada", "Lena", 0.6);
            graph.Link("Ada", "Sam", 0.5);
            // Tier-2 sample ring, live pair: the vendor and the dock hand.
            graph.Link("Marla", "Ada", 0.5);
            graph.Link("Marla", "Sam", 0.4);
            graph.Link("Joey", "Rocco", 0.6);
            graph.Link("Joey", "Sam", 0.3);
            // Noor hears everything (cast-noor-draft.md): the street's best
            // listener — talk reaches her fast, and her card compels her to ask.
            graph.Link("Noor", "Ada", 0.7);
            graph.Link("Noor", "Sam", 0.6);
            graph.Link("Noor", "Lena", 0.5);
            graph.Link("Noor", "Rocco", 0.5);
            graph.Link("Noor", "Marla", 0.4);
            // Victor (batch promotion): the pawnbroker's ties from his card.
            graph.Link("Victor", "Lena", 0.4);
            graph.Link("Victor", "Sam", 0.5);
            // The promoted ring's ties: the district's working relationships.
            graph.Link("Ferko", "Joey", 0.5);
            graph.Link("Ferko", "Sam", 0.4);
            graph.Link("Rita", "Victor", 0.6);  // the back room
            graph.Link("Rita", "Joey", 0.4);
            graph.Link("Rita", "Tibor", 0.4);
            graph.Link("Vesna", "Ada", 0.5);
            graph.Link("Vesna", "Marla", 0.4);
            graph.Link("Tibor", "Joey", 0.4);
            // Tier-1 batch 2: the chapel hears everything, dispatch hears the
            // rest, and the broker keeps deliberately thin ties to everyone.
            graph.Link("June", "Lena", 0.5);
            graph.Link("June", "Emil", 0.45);
            graph.Link("Emil", "Vesna", 0.7);   // she keeps his house and reads his letters
            graph.Link("Emil", "Ada", 0.6);
            graph.Link("Zlata", "Joey", 0.5);
            graph.Link("Zlata", "Ferko", 0.45);
            graph.Link("Zlata", "Sam", 0.4);
            graph.Link("Hal", "Sam", 0.3);
            graph.Link("Hal", "Rita", 0.3);
            // The generated batch's connections — links to residents who aren't
            // walking yet simply stay dormant until they do.
            foreach (var (a, b, w) in Tier2Batch.GraphLinks()) graph.Link(a, b, w);
            Graph = graph;
            _mill = new GossipMill(graph);

            // Every gossiper shares its conversation host's real memory, knowledge and
            // suspicion, so a rumor reaching an NPC is felt the next time the player
            // talks to THAT NPC — and a lie told to any of them can be contradicted.
            foreach (var host in hosts)
            {
                var walkerName = host.GetComponent<NpcWalker>() != null
                    ? host.GetComponent<NpcWalker>().DisplayName : host.Card.Name;
                var m = CastSetup.Get(walkerName) ?? Tier2Setup.Get(walkerName)
                    ?? CastTier1.Get(walkerName) ?? Tier2Batch.Get(walkerName);
                _mill.Add(m != null
                    ? new Gossiper(walkerName, walkerName, host.Memory, host.Knowledge, host.Suspicion,
                        m.Circle, m.Greed, m.Nerve, m.Loyalty)
                    : walkerName == "Noor"
                    // Noor: both circles, a bribe is a story, a threat is a story.
                    ? new Gossiper(walkerName, walkerName, host.Memory, host.Knowledge, host.Suspicion,
                        NoorSetup.Circle, NoorSetup.Greed, NoorSetup.Nerve, NoorSetup.StartLoyalty)
                    // Lena: the guarded bookkeeper — near-unbuyable, hard to rattle.
                    : new Gossiper(walkerName, walkerName, host.Memory, host.Knowledge, host.Suspicion,
                        "day", 0.25, 0.75, 0.5));
            }

            // The seed: the doorman saw the player somewhere the daytime world must not
            // find out about. It will leak toward the day circle as the NPCs mingle.
            _mill.Witness("Rocco",
                new Fact("player", "location_d2_evening", "warehouse"),
                "the new owner was at the old warehouse the night of the fire", true, _game.Now);
        }

        /// Fired with every batch of real gossip exchanges (organic ticks and
        /// directed checks alike) so authored systems — Noor's two drawers —
        /// can react to what actually happened on the street.
        public System.Action<List<GossipEvent>> OnEvents;

        void Update()
        {
            if (_mill == null || _game == null) return;

            // The street talks about itself on the REAL clock, not the gossip
            // tick — a conversation is a thing that takes seconds, not game
            // hours (M15.1).
            TickAmbient();
            TickStances();

            var now = _game.Now;
            if (!_haveLastTick) { _lastTickAt = now; _haveLastTick = true; return; }
            _timer += MinutesBetween(_lastTickAt, now);
            _lastTickAt = now;
            if (_timer < TickIntervalGameMinutes) return;

            int rounds = 0;
            while (_timer >= TickIntervalGameMinutes && rounds < MaxCatchUpRounds)
            {
                _timer -= TickIntervalGameMinutes;
                rounds++;
                var events = _mill.Tick(now, Together);
                ReportOverheard(events);
                // The bodies, for every exchange rather than only the ones
                // about the player. A city that talks only about you is a
                // city with one subject, and the claim this game makes is
                // that the mill runs whether you are in it or not.
                StageConfabs(events);
                OnEvents?.Invoke(events);
                RunChecking();
            }
            if (rounds >= MaxCatchUpRounds) _timer = 0f;   // a long stall does not owe us a hundred rounds
        }

        /// Game minutes from one stamp to the next, days included.
        static float MinutesBetween(GameTime a, GameTime b) =>
            (b.Day - a.Day) * 1440f + (b.Hour - a.Hour) * 60f + (b.Minute - a.Minute);

        // The audit's #1 pick: overheard chatter IS the gossip mill. If a real
        // exchange about the player happens within earshot, the player hears the
        // words and gains the lead — the fourth knowledge channel, and unlike
        // GTA's canned barks, every scrap is a true event in the simulation.
        public int Overheard { get; private set; }
        const float EarshotRange = 6f;

        /// Holds the deeper duck for as long as the exchange is on screen,
        /// then releases it. The release itself is slow — Core/Mixing owns
        /// that — so the bed comes back without anybody noticing it left.
        System.Collections.IEnumerator OverhearDuck()
        {
            Audio.DuckForOverheard(true);
            yield return new WaitForSeconds(6.5f);
            Audio.DuckForOverheard(false);
        }

        System.Collections.IEnumerator SayAfter(NpcWalker who, string line, float delay, Color colour, float hold)
        {
            if (delay > 0) yield return new WaitForSeconds(delay);
            if (who != null) SpeechBubble.Say(who.transform, line, hold, colour);
        }

        /// M15.2 — WHO IS PERCEIVING YOU, and how. Recomputed on a slow
        /// cadence (stances change on the scale of rumours, not frames) and
        /// pushed onto the bodies, which express it as gaze and distance.
        float _nextStance;
        readonly Dictionary<string, float> _lastBark = new Dictionary<string, float>();

        /// Every body on the street: the authored cast AND the crowd, which
        /// is most of it. The cast is keyed in the mill by display name and a
        /// promoted resident by id, so the lookup has to try both — a street
        /// where only the six named people react is not a street.
        IEnumerable<(NpcWalker walker, Gossiper agent)> LiveBodies()
        {
            foreach (var kv in _walkers)
            {
                var g = kv.Value != null ? _mill.Get(kv.Value.DisplayName) : null;
                if (g != null) yield return (kv.Value, g);
            }
            if (_game.CrowdBodies != null)
                foreach (var kv in _game.CrowdBodies)
                {
                    if (kv.Value == null) continue;
                    var g = _mill.Get(kv.Key);
                    if (g != null) yield return (kv.Value, g);
                }
        }

        void TickStances()
        {
            if (Time.time < _nextStance) return;
            _nextStance = Time.time + 1.5f;
            var player = _game.Player;
            if (player == null) return;
            // Perceivers needs the player to size the noise ring against the
            // player's own ambient floor. Bound here because this is already
            // the place that hands the player to every walker, and a second
            // binding site is a second thing that can be forgotten.
            Perceivers.BindPlayer(player.transform);

            foreach (var (w, g) in LiveBodies())
            {
                if (w == null || g == null) continue;
                w.SetPlayer(player.transform);

                Rumor strongest = null;
                foreach (var r in g.Rumors)
                    if (r.Content.Subject == "player" && (strongest == null || r.Confidence > strongest.Confidence))
                        strongest = r;

                var stance = StreetVoice.Stance(g.Suspicion.Value, g.Loyalty,
                    strongest != null ? strongest.Confidence : 0.0, g.Leashed, _game.WearingCoat);
                w.Stance = stance;

                // A bark as you pass: said BY somebody who holds a story, and
                // stoppable — press E and they can be asked what they meant,
                // because the same rumour is sitting in their memory.
                if (stance < StanceKind.Comments) continue;
                float d = Vector3.Distance(player.transform.position, w.transform.position);
                if (d > 7f) continue;
                float last = _lastBark.TryGetValue(g.Id, out var t) ? t : -999f;
                if (Time.time - last < 45f) continue;
                _lastBark[g.Id] = Time.time;
                var line = StreetVoice.Recognition(g, strongest, stance, _game.Now.Day * 7 + _game.Now.Hour);
                if (line != null)
                    SpeechBubble.Say(w.transform, line.Text, 5f,
                        stance >= StanceKind.Refuses ? UiTheme.Debit : UiTheme.AmberSoft);
            }
        }

        /// M15.1 — AMBIENT LIFE. The city talking about ITSELF: debts, prices,
        /// a wound that will not heal, the weather. None of it is about the
        /// player, which is exactly why it matters — a place that only ever
        /// discusses you is a stage set, not a city.
        float _nextAmbient;

        void TickAmbient()
        {
            var player = _game.Player;
            if (player == null || _mill == null) return;

            // Who is near enough to be heard at all.
            var near = new List<(NpcWalker w, Gossiper g)>();
            foreach (var (w, g) in LiveBodies())
                if (Vector3.Distance(player.transform.position, w.transform.position) <= 14f) near.Add((w, g));

            double heat = _mill.DayCircleHeat();
            Audio.SetChatter((float)StreetVoice.ChatterLevel(heat, near.Count));
            double every = StreetVoice.AmbientEverySeconds(heat, near.Count);
            if (every > 1e8) return;                       // nobody to talk with
            if (Time.time < _nextAmbient) return;
            _nextAmbient = Time.time + (float)every;

            // Two of them, standing near each other, out of the player's way.
            NpcWalker a = null, b = null;
            Gossiper ga = null, gb = null;
            float best = float.MaxValue;
            for (int i = 0; i < near.Count; i++)
                for (int j = i + 1; j < near.Count; j++)
                {
                    float d = Vector3.Distance(near[i].w.transform.position, near[j].w.transform.position);
                    if (d < best && d < 7f)
                    { best = d; a = near[i].w; b = near[j].w; ga = near[i].g; gb = near[j].g; }
                }
            if (a == null || b == null || ga == null || gb == null) return;

            bool hurt = _game.Harm != null && _game.Harm.Hurts(ga.Id, _game.Now.Day).Count > 0;
            bool feud = _game.Harm != null && _game.Harm.FeudBetween(ga.Id, gb.Id) != null;
            int seed = _game.Now.Day * 17 + _game.Now.Hour * 3 + near.Count;
            var lines = StreetVoice.Ambient(ga, gb, _game.Now,
                _game.Economy.Prosperity, _game.Economy.PriceLevel, hurt, feud, seed);
            for (int i = 0; i < lines.Count; i++)
                StartCoroutine(SayAfter(i == 0 ? a : b, lines[i].Text, i * 2.4f, UiTheme.Dim, 5.5f));
        }

        /// Total confabs staged. The sim gate reads it: an exchange the
        /// player can watch is the game's central mechanic made visible, and
        /// a staging path that quietly stops firing looks identical to a
        /// quiet street.
        public int Confabs { get; private set; }

        /// STAGE THE BODIES for a rumour that just passed between two people
        /// who are standing near each other.
        ///
        /// This is separate from `ReportOverheard` on purpose, and the
        /// difference is the point. That one fires only for rumours about the
        /// PLAYER, within earshot, and gives him a lead — it is a game
        /// mechanic. This fires for ANY exchange between two visible bodies,
        /// and gives him nothing but the sight of it. A city that only ever
        /// talks about you is a city with one subject, and the whole claim
        /// this game makes is that the mill runs whether you are in it or
        /// not.
        void StageConfabs(List<GossipEvent> events)
        {
            if (events == null) return;
            int staged = 0;
            foreach (var ev in events)
            {
                // Two a round at most. The mill can pass a dozen rumours in
                // one tick and staging all of them freezes the street into a
                // tableau of people standing in pairs, which is a stranger
                // sight than the silence it replaced.
                if (staged >= 2) break;
                if (!_walkers.TryGetValue(ev.FromId, out var wa) || wa == null) continue;
                if (!_walkers.TryGetValue(ev.ToId, out var wb) || wb == null) continue;
                if (wa == wb || wa.InConfab || wb.InConfab) continue;

                float apart = Vector3.Distance(wa.transform.position, wb.transform.position);
                // `somewhereToStand` is a road check: the rumour graph has no
                // idea where anybody is and will happily fire an exchange
                // between two people crossing a junction.
                bool clear = OffRoad(wa.transform.position) && OffRoad(wb.transform.position);
                if (!Confab.WorthStopping(apart, true, clear)) continue;

                double tie = _mill != null ? _mill.Tie(ev.FromId, ev.ToId) : 0.4;
                bool sensitive = ev.Rumor != null && ev.Rumor.Sensitive;
                bool hostile = ev.Contradiction;

                // The LISTENER walks over. Both moving reads as choreography.
                wa.SetConfabRole(!Confab.ListenerApproaches, leansLeft: true);
                wb.SetConfabRole(Confab.ListenerApproaches, leansLeft: false);
                // Whether it is about HIM, which is what decides if they
                // break off when he walks up.
                bool aboutPlayer = ev.Rumor != null && ev.Rumor.Content.Subject == "player";
                wa.BeginConfab(wb, tie, sensitive, hostile, aboutPlayer);
                wb.BeginConfab(wa, tie, sensitive, hostile, aboutPlayer);
                Confabs++;
                staged++;
            }
        }

        /// Is there somewhere to stand here? Nobody stops to chat in the
        /// middle of a carriageway — and the rumour graph has no idea where
        /// anybody is standing, so it will happily pass a secret between two
        /// people halfway across a junction.
        ///
        /// Measured off the street centreline the rest of the game already
        /// uses, rather than a new notion of "road", so this cannot disagree
        /// with the pathing about where the road is.
        static bool OffRoad(Vector3 p)
        {
            if (!StreetMap.NearestOnStreet(p.x, p.z, out double sx, out double sz, out _))
                return true;   // no street known here: it is not a carriageway
            double dx = p.x - sx, dz = p.z - sz;
            return System.Math.Sqrt(dx * dx + dz * dz) > 3.0;
        }

        void ReportOverheard(List<GossipEvent> events)
        {
            var player = _game.Player;
            if (player == null || events == null) return;
            foreach (var ev in events)
            {
                if (ev.Rumor == null || ev.Rumor.Content.Subject != "player") continue;
                if (!_walkers.TryGetValue(ev.FromId, out var wa) || wa == null) continue;
                if (!_walkers.TryGetValue(ev.ToId, out var wb) || wb == null) continue;
                var p = player.transform.position;
                if (Vector3.Distance(p, wa.transform.position) > EarshotRange) continue;
                if (Vector3.Distance(p, wb.transform.position) > EarshotRange) continue;

                // M15.1: SAY IT. This is the moment the whole gossip network
                // exists for, and until now the game answered it by adding a
                // row to a panel the player had to press L to read. Two people
                // are discussing him six metres away; they should be audible.
                var fromG = _mill.Get(ev.FromId);
                var toG = _mill.Get(ev.ToId);
                int seed = _game.Now.Day * 31 + _game.Now.Hour;
                var spoken = StreetVoice.Exchange(ev.Rumor, fromG, toG, seed);
                for (int i = 0; i < spoken.Count; i++)
                {
                    var w = i == 0 ? wa : wb;
                    // The reply lands a beat after the telling, the way a
                    // conversation does.
                    StartCoroutine(SayAfter(w, spoken[i].Text, i * 2.1f, UiTheme.AmberSoft, 6.5f));
                }
                Audio.Ui("page");   // the sound of the street noticing you
                // AND THE STREET GETS OUT OF THE WAY. This is the one moment
                // the whole gossip network exists for, and until now it was
                // two lines of dialogue competing on equal terms with rain,
                // traffic and an ambience bed authored for walking around in.
                // Leaning in to catch something is a real thing ears do.
                StartCoroutine(OverhearDuck());

                _game.Knowledge.Learn(new Lead
                {
                    HolderId = ev.ToId,
                    HolderName = _mill.Get(ev.ToId) != null ? _mill.Get(ev.ToId).DisplayName : ev.ToId,
                    SourceId = ev.Rumor.OriginId, TopicKey = ev.Rumor.TopicKey,
                    Summary = ev.Rumor.Summary, Confidence = ev.Rumor.Confidence,
                    Sensitive = ev.Rumor.Sensitive,
                }, "overheard", _game.Now);
                Overheard++;
                _game.ToastLine($"You catch a scrap of talk — {ev.FromId}, low, to {ev.ToId}: \"…{ev.Rumor.Summary}…\"", 7f);
                break; // one scrap per round; the street doesn't monologue
            }
        }

        // §6.4 middle rung: a Suspicious NPC doesn't wait for chance — once a day,
        // the first time they're near someone they know, they ASK (a directed
        // CompareNotes). Leashed NPCs never check; CompareNotes enforces it too.
        readonly Dictionary<string, int> _checkedDay = new Dictionary<string, int>();

        void RunChecking()
        {
            foreach (var checker in _mill.Agents)
            {
                var lvl = checker.Suspicion.Level;
                if (lvl != SuspicionLevel.Suspicious && lvl != SuspicionLevel.Confronting) continue;
                if (checker.Leashed) continue;
                if (_checkedDay.TryGetValue(checker.Id, out var d) && d == _game.Now.Day) continue;
                foreach (var partnerId in _walkers.Keys)
                {
                    if (partnerId == checker.Id || _mill.Get(partnerId) == null) continue;
                    if (!Together(checker.Id, partnerId)) continue;
                    // Directed asking is also audible if you happen to be standing there.
                    var asked = _mill.CompareNotes(checker.Id, partnerId, _game.Now);
                    ReportOverheard(asked);
                    OnEvents?.Invoke(asked);
                    _checkedDay[checker.Id] = _game.Now.Day;
                    ChecksRun++;
                    break;
                }
            }
        }

        public int ChecksRun { get; private set; }

        /// Where somebody simulated-but-not-rendered is standing (roadmap M9's
        /// mid band). Set by GameController; without it the crowd could carry
        /// talk but never pass it on, because a person with no body has no
        /// position and Together would always say no.
        public System.Func<string, Vector3?> ExtraPosition;

        Vector3? PositionOf(string id)
        {
            if (_walkers.TryGetValue(id, out var w) && w != null) return w.transform.position;
            return ExtraPosition != null ? ExtraPosition(id) : null;
        }

        bool Together(string a, string b)
        {
            var pa = PositionOf(a);
            var pb = PositionOf(b);
            if (pa == null || pb == null) return false;
            return Vector3.Distance(pa.Value, pb.Value) <= TalkRange;
        }

        const float WitnessRange = 10f;

        /// A night drop was just made at `dropPos`. Any NPC close enough saw it
        /// first-hand, and a fresh sensitive rumor enters the network — the night
        /// side of the double life generating tomorrow's problem. Returns who saw:
        /// at that range the player saw them too, so each witness becomes a known
        /// lead rather than an invisible tick in the simulation.
        /// `vehicle` is the phrase for whatever the player ARRIVED IN, or null
        /// if they walked. It is appended to the description and — this is the
        /// point — it is appended whether or not they were wearing the coat.
        /// The disguise buys doubt about the face; it buys none about the car
        /// standing in the street. "Someone in a coat, and a car" is a narrower
        /// description than "someone in a coat", and a narrower description is
        /// what an investigator works from.
        public List<string> WitnessNightJob(Vector3 dropPos, int day, GameTime now,
            double confidence = 1.0, string vehicle = null, string address = null)
        {
            var seen = new List<string>();
            if (_mill == null) return seen;
            var summary = confidence >= 0.95
                ? "the new owner was handling a package in the street past midnight"
                : "someone in a runner's coat — maybe the new owner — was handling a package past midnight";
            if (!string.IsNullOrEmpty(address)) summary += $", on {address}";
            if (!string.IsNullOrEmpty(vehicle)) summary += $", and {vehicle} was standing there with them";
            foreach (var kv in _walkers)
            {
                if (kv.Value == null) continue;
                if (Vector3.Distance(kv.Value.transform.position, dropPos) > WitnessRange) continue;
                _mill.Witness(kv.Key, new Fact("player", $"night_job_d{day}", "seen"), summary, true, now, confidence);
                // The vehicle is filed as its own hard fact, not just as words in
                // a sentence: a description the investigation can actually check
                // against, and one the coat never softens.
                if (!string.IsNullOrEmpty(vehicle))
                    _mill.Witness(kv.Key, new Fact("player", $"vehicle_d{day}", vehicle),
                        $"there was {vehicle} outside when it happened", false, now, 0.9);
                seen.Add(kv.Key);
            }
            return seen;
        }

        /// Developer-facing (F1) readout of how far the secret has spread. Deliberately
        /// not shown to the player as a meter — they feel it through Lena's words.
        public string StatusLine()
        {
            if (_mill == null) return "";
            var sb = new System.Text.StringBuilder();
            sb.Append($"-- gossip --\nday-circle heat: {_mill.DayCircleHeat():0.00}\n");
            sb.Append($"Lena has heard the secret: {_mill.KnowsSecret("Lena")}\n");
            var leads = _mill.Leads("player");
            if (leads.Count == 0) sb.Append("no talk about you right now");
            else
            {
                sb.Append("talk about you:");
                for (int i = 0; i < leads.Count && i < 4; i++)
                {
                    var l = leads[i];
                    sb.Append($"\n  {l.HolderName} ({l.Confidence:0.00}{(l.Sensitive ? ", sensitive" : "")}) — {l.Summary}");
                }
            }
            return sb.ToString();
        }
    }
}
