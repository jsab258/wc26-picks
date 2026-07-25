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
            _mill = new GossipMill(graph);

            // Every gossiper shares its conversation host's real memory, knowledge and
            // suspicion, so a rumor reaching an NPC is felt the next time the player
            // talks to THAT NPC — and a lie told to any of them can be contradicted.
            foreach (var host in hosts)
            {
                var walkerName = host.GetComponent<NpcWalker>() != null
                    ? host.GetComponent<NpcWalker>().DisplayName : host.Card.Name;
                var m = CastSetup.Get(walkerName);
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
            _mill.Tick(_game.Now, Together);
        }

        bool Together(string a, string b)
        {
            if (!_walkers.TryGetValue(a, out var wa) || !_walkers.TryGetValue(b, out var wb)) return false;
            if (wa == null || wb == null) return false;
            return Vector3.Distance(wa.transform.position, wb.transform.position) <= TalkRange;
        }

        const float WitnessRange = 10f;

        /// A night drop was just made at `dropPos`. Any NPC close enough saw it
        /// first-hand, and a fresh sensitive rumor enters the network — the night
        /// side of the double life generating tomorrow's problem. Returns how many saw.
        public int WitnessNightJob(Vector3 dropPos, int day, GameTime now)
        {
            if (_mill == null) return 0;
            int count = 0;
            foreach (var kv in _walkers)
            {
                if (kv.Value == null) continue;
                if (Vector3.Distance(kv.Value.transform.position, dropPos) > WitnessRange) continue;
                _mill.Witness(kv.Key,
                    new Fact("player", $"night_job_d{day}", "seen"),
                    "the new owner was handling a package in the street past midnight", true, now);
                count++;
            }
            return count;
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
