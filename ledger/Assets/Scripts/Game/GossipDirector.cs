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
        const float TickInterval = 3f; // real seconds between gossip rounds
        const float TalkRange = 6f;

        GameController _game;
        GossipMill _mill;
        readonly Dictionary<string, NpcWalker> _walkers = new Dictionary<string, NpcWalker>();
        float _timer;

        public GossipMill Mill => _mill;

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
            graph.Link("Mirela", "Ada", 0.5);
            graph.Link("Mirela", "Sam", 0.4);
            graph.Link("Josip", "Rocco", 0.6);
            graph.Link("Josip", "Sam", 0.3);
            _mill = new GossipMill(graph);

            // Every gossiper shares its conversation host's real memory, knowledge and
            // suspicion, so a rumor reaching an NPC is felt the next time the player
            // talks to THAT NPC — and a lie told to any of them can be contradicted.
            foreach (var host in hosts)
            {
                var walkerName = host.GetComponent<NpcWalker>() != null
                    ? host.GetComponent<NpcWalker>().DisplayName : host.Card.Name;
                var m = CastSetup.Get(walkerName) ?? Tier2Setup.Get(walkerName);
                _mill.Add(m != null
                    ? new Gossiper(walkerName, walkerName, host.Memory, host.Knowledge, host.Suspicion,
                        m.Circle, m.Greed, m.Nerve, m.Loyalty)
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

        void Update()
        {
            if (_mill == null || _game == null) return;
            _timer += Time.deltaTime;
            if (_timer < TickInterval) return;
            _timer = 0f;
            ReportOverheard(_mill.Tick(_game.Now, Together));
            RunChecking();
        }

        // The audit's #1 pick: overheard chatter IS the gossip mill. If a real
        // exchange about the player happens within earshot, the player hears the
        // words and gains the lead — the fourth knowledge channel, and unlike
        // GTA's canned barks, every scrap is a true event in the simulation.
        public int Overheard { get; private set; }
        const float EarshotRange = 6f;

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
                    ReportOverheard(_mill.CompareNotes(checker.Id, partnerId, _game.Now));
                    _checkedDay[checker.Id] = _game.Now.Day;
                    ChecksRun++;
                    break;
                }
            }
        }

        public int ChecksRun { get; private set; }

        bool Together(string a, string b)
        {
            if (!_walkers.TryGetValue(a, out var wa) || !_walkers.TryGetValue(b, out var wb)) return false;
            if (wa == null || wb == null) return false;
            return Vector3.Distance(wa.transform.position, wb.transform.position) <= TalkRange;
        }

        const float WitnessRange = 10f;

        /// A night drop was just made at `dropPos`. Any NPC close enough saw it
        /// first-hand, and a fresh sensitive rumor enters the network — the night
        /// side of the double life generating tomorrow's problem. Returns who saw:
        /// at that range the player saw them too, so each witness becomes a known
        /// lead rather than an invisible tick in the simulation.
        public List<string> WitnessNightJob(Vector3 dropPos, int day, GameTime now, double confidence = 1.0)
        {
            var seen = new List<string>();
            if (_mill == null) return seen;
            var summary = confidence >= 0.95
                ? "the new owner was handling a package in the street past midnight"
                : "someone in a runner's coat — maybe the new owner — was handling a package past midnight";
            foreach (var kv in _walkers)
            {
                if (kv.Value == null) continue;
                if (Vector3.Distance(kv.Value.transform.position, dropPos) > WitnessRange) continue;
                _mill.Witness(kv.Key, new Fact("player", $"night_job_d{day}", "seen"), summary, true, now, confidence);
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
