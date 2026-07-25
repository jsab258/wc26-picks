using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// Undirected weighted acquaintance graph: how likely, and how faithfully, two
    /// NPCs pass talk about a third party (usually the player). Weight is 0..1.
    public class SocialGraph
    {
        readonly Dictionary<string, Dictionary<string, double>> _ties =
            new Dictionary<string, Dictionary<string, double>>();

        public void Link(string a, string b, double weight)
        {
            if (a == b) return;
            Put(a, b, weight);
            Put(b, a, weight);
        }

        void Put(string from, string to, double w)
        {
            if (!_ties.TryGetValue(from, out var row)) { row = new Dictionary<string, double>(); _ties[from] = row; }
            row[to] = Math.Clamp(w, 0.0, 1.0);
        }

        public double Tie(string a, string b) =>
            _ties.TryGetValue(a, out var row) && row.TryGetValue(b, out var w) ? w : 0.0;

        public IEnumerable<string> Contacts(string id) =>
            _ties.TryGetValue(id, out var row) ? row.Keys : Enumerable.Empty<string>();
    }

    /// A propagating piece of talk about someone. Content is a structured Fact so it
    /// can be checked against what an NPC already knows; Confidence decays each hop so
    /// third-hand rumor carries less weight than an eyewitness account.
    public class Rumor
    {
        public Fact Content;       // e.g. player.location_d2_evening = warehouse
        public string OriginId;    // the first-hand source
        public string Summary;     // human/LLM-readable phrasing of the content
        public double Confidence;  // 0..1
        public int Hops;           // 0 = witnessed first-hand
        public bool Sensitive;     // pertains to the player's hidden (night) life

        public string TopicKey => $"{Content.Subject}.{Content.Predicate}";
    }

    /// One NPC's social side: their memory, what they factually know, how much they
    /// trust the player, the rumors they carry, and which of the player's two faces
    /// they belong to ("day", "night", or "both"). A thin aggregate the mill drives.
    public class Gossiper
    {
        public string Id;
        public string DisplayName;
        public string Circle = "day"; // "day" | "night" | "both"
        public MemoryStore Memory;
        public KnowledgeBase Knowledge;
        public SuspicionTracker Suspicion;
        public readonly List<Rumor> Rumors = new List<Rumor>();

        public Gossiper(string id, string displayName, MemoryStore memory,
            KnowledgeBase knowledge, SuspicionTracker suspicion, string circle = "day")
        {
            Id = id;
            DisplayName = displayName;
            Memory = memory ?? new MemoryStore(id);
            Knowledge = knowledge ?? new KnowledgeBase();
            Suspicion = suspicion ?? new SuspicionTracker();
            Circle = circle;
        }

        public bool Holds(string topicKey, string value) =>
            Rumors.Any(r => r.TopicKey == topicKey && r.Content.Value == value);

        public Rumor Best(string topicKey) =>
            Rumors.Where(r => r.TopicKey == topicKey).OrderByDescending(r => r.Confidence).FirstOrDefault();
    }

    /// One thing that happened during a gossip round — for the sim report and for the
    /// player-facing "heat" readout.
    public class GossipEvent
    {
        public string FromId, ToId;
        public Rumor Rumor;
        public bool Contradiction; // the rumor collided with a claim the player made to ToId
        public bool Exposure;      // a night-life rumor reached a day-circle NPC
    }

    /// The rumor network. Seeds first-hand sightings, records the player's claims to
    /// individual NPCs, and — each round — lets socially-tied NPCs who are together
    /// pass talk along. Contradictions and cross-circle leaks move suspicion; nothing
    /// here calls the LLM (the model only voices the fallout later, in conversation).
    public class GossipMill
    {
        readonly Dictionary<string, Gossiper> _agents = new Dictionary<string, Gossiper>();
        readonly SocialGraph _graph;

        // Tunables. Confidence is multiplied by tie strength and this factor per hop;
        // a rumor stops spreading once it drops below the share floor.
        public double HopDecay = 0.8;
        public double MinConfidenceToShare = 0.2;
        public double ContradictionSuspicion = 0.35; // scaled by rumor confidence
        public double LeakSuspicion = 0.12;          // day-NPC hears a night rumor, no prior lie

        public GossipMill(SocialGraph graph) { _graph = graph ?? new SocialGraph(); }

        public void Add(Gossiper g) => _agents[g.Id] = g;
        public Gossiper Get(string id) => _agents.TryGetValue(id, out var g) ? g : null;
        public IEnumerable<Gossiper> Agents => _agents.Values;

        /// A first-hand sighting enters the network at full confidence.
        public void Witness(string witnessId, Fact content, string summary, bool sensitive, GameTime now)
        {
            var w = Get(witnessId);
            if (w == null) return;
            w.Knowledge.Learn(content); // they know it for certain
            if (!w.Holds(content.Subject + "." + content.Predicate, content.Value))
            {
                w.Rumors.Add(new Rumor
                {
                    Content = content, OriginId = witnessId, Summary = summary,
                    Confidence = 1.0, Hops = 0, Sensitive = sensitive,
                });
            }
            w.Memory.Append(new MemoryEvent(now, "observation", sensitive ? 0.9 : 0.6, $"I saw it myself: {summary}"));
        }

        /// The player tells one NPC something checkable. Recorded so a later rumor can
        /// contradict it — this is how a lie eventually catches up with the liar.
        public void PlayerClaims(string npcId, Fact claim, GameTime now)
        {
            var n = Get(npcId);
            if (n == null) return;
            n.Knowledge.Learn(claim);
            n.Memory.Append(new MemoryEvent(now, "conversation", 0.4,
                $"The new owner told me: {claim.Predicate.Replace('_', ' ')} was {claim.Value}."));
        }

        /// One gossip round. `together` decides which tied pairs are actually in a
        /// position to talk this round (co-located in game, or always-true in tests).
        /// Returns everything that propagated, for logging.
        public List<GossipEvent> Tick(GameTime now, Func<string, string, bool> together = null)
        {
            var events = new List<GossipEvent>();

            // Snapshot each agent's rumors so a rumor picked up THIS round doesn't also
            // hop again in the same round (keeps spread to one hop per round, and the
            // loop deterministic and terminating).
            var snapshot = _agents.Values.ToDictionary(a => a.Id, a => a.Rumors.ToList());

            foreach (var speaker in _agents.Values)
            {
                foreach (var listenerId in _graph.Contacts(speaker.Id))
                {
                    var listener = Get(listenerId);
                    if (listener == null) continue;
                    if (together != null && !together(speaker.Id, listenerId)) continue;

                    double tie = _graph.Tie(speaker.Id, listenerId);
                    if (tie <= 0) continue;

                    foreach (var r in snapshot[speaker.Id])
                    {
                        if (r.Confidence < MinConfidenceToShare) continue;
                        double passed = r.Confidence * tie * HopDecay;
                        if (passed < MinConfidenceToShare) continue;

                        // Don't re-tell something the listener already holds at least as
                        // strongly — stops rumors amplifying by bouncing back and forth.
                        var existing = listener.Best(r.TopicKey);
                        if (existing != null && existing.Content.Value == r.Content.Value && existing.Confidence >= passed)
                            continue;

                        var heard = new Rumor
                        {
                            Content = r.Content, OriginId = r.OriginId, Summary = r.Summary,
                            Confidence = passed, Hops = r.Hops + 1, Sensitive = r.Sensitive,
                        };
                        listener.Rumors.Add(heard);
                        listener.Memory.Append(new MemoryEvent(now, "heard",
                            Math.Clamp(passed * 0.8, 0.2, 0.85),
                            $"I heard from {speaker.DisplayName} that {r.Summary}"));

                        var ev = new GossipEvent { FromId = speaker.Id, ToId = listenerId, Rumor = heard };

                        // Consequence 1: the rumor collides with a claim the player made
                        // to this listener — the lie is exposed.
                        if (listener.Knowledge.CheckClaim(r.Content) == ClaimResult.Contradiction)
                        {
                            listener.Suspicion.Raise(ContradictionSuspicion * passed,
                                $"a rumor about {r.TopicKey} contradicts what the new owner told me");
                            listener.Memory.Append(new MemoryEvent(now, "observation", 0.85,
                                $"What I heard about {r.TopicKey.Replace("player.", "")} doesn't match what they told me to my face."));
                            ev.Contradiction = true;
                        }
                        // Consequence 2: a night-life secret reaches someone from the
                        // player's daytime world — the double life springs a leak.
                        else if (r.Sensitive && listener.Circle == "day")
                        {
                            listener.Suspicion.Raise(LeakSuspicion * passed, "heard something that doesn't fit the person I thought I knew");
                            ev.Exposure = true;
                        }

                        events.Add(ev);
                    }
                }
            }
            return events;
        }

        /// Does this NPC now carry a sensitive (night-life) rumor about the player? The
        /// player-facing signal that a secret has reached someone it shouldn't have.
        public bool KnowsSecret(string npcId) =>
            Get(npcId)?.Rumors.Any(r => r.Sensitive && r.Confidence >= MinConfidenceToShare) ?? false;

        /// A 0..1 "heat" reading: the strongest sensitive rumor anywhere in the day
        /// circle. Rises as secrets spread — the escalation the player feels instead of
        /// a countdown.
        public double DayCircleHeat()
        {
            double max = 0;
            foreach (var a in _agents.Values)
                if (a.Circle == "day")
                    foreach (var r in a.Rumors)
                        if (r.Sensitive && r.Confidence > max) max = r.Confidence;
            return max;
        }
    }
}
