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

        /// A FACT, not a story. Set only by a killing (combat-spec §7b).
        ///
        /// Every other rumour in this game can be muddied, bought quiet,
        /// scared quiet, held on a leash or simply left to go cold. None of
        /// that machinery touches a corpse — Age, Discredit, Contain and the
        /// hop decay in Tick all step over an indelible rumour. That
        /// asymmetry against literally everything else in the mill is the
        /// whole reason killing a witness is terrifying rather than
        /// efficient: it works, and it is the one thing you can never take
        /// back.
        public bool Indelible;

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

        // How the player's damage control lands on this NPC. Greed: how readily they
        // take a bribe. Nerve: how hard they are to intimidate (high = won't scare).
        // Loyalty: goodwill toward the player. All 0..1.
        public double Greed = 0.5;
        public double Nerve = 0.5;
        public double Loyalty = 0.5;

        // Topics this NPC has agreed (or been made) to keep quiet about — they still
        // remember, but they won't pass it on.
        public readonly HashSet<string> Suppressed = new HashSet<string>();

        // Standing coercion (design-doc §6.3 strong hook): the player holds
        // something over them, and NOTHING about the player leaves their lips —
        // current topics and future ones alike. They remember everything.
        public bool Leashed;

        public Gossiper(string id, string displayName, MemoryStore memory,
            KnowledgeBase knowledge, SuspicionTracker suspicion, string circle = "day",
            double greed = 0.5, double nerve = 0.5, double loyalty = 0.5)
        {
            Id = id;
            DisplayName = displayName;
            Memory = memory ?? new MemoryStore(id);
            Knowledge = knowledge ?? new KnowledgeBase();
            Suspicion = suspicion ?? new SuspicionTracker();
            Circle = circle;
            Greed = greed;
            Nerve = nerve;
            Loyalty = loyalty;
        }

        public bool Holds(string topicKey, string value) =>
            Rumors.Any(r => r.TopicKey == topicKey && r.Content.Value == value);

        public Rumor Best(string topicKey) =>
            Rumors.Where(r => r.TopicKey == topicKey).OrderByDescending(r => r.Confidence).FirstOrDefault();

        /// The strongest telling of this PARTICULAR version of the story. The
        /// re-tell guards compare against this rather than Best(): two agents
        /// holding conflicting values must settle, not re-copy each other's
        /// version every round (audit 2026-07-27).
        public Rumor BestOfValue(string topicKey, string value) =>
            Rumors.Where(r => r.TopicKey == topicKey && r.Content.Value == value)
                  .OrderByDescending(r => r.Confidence).FirstOrDefault();
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

        /// How strongly two people are connected, 0..1. Exposed as a
        /// passthrough rather than by handing out the graph: callers outside
        /// the mill want to ASK about a relationship, not to hold and
        /// possibly mutate the thing that defines every relationship.
        public double Tie(string a, string b) => _graph.Tie(a, b);

        public void Add(Gossiper g) => _agents[g.Id] = g;

        /// Takes somebody out of the network (roadmap M9: a resident who has
        /// drifted out of the player's attention band). REFUSES if they are
        /// carrying anything — a rumor or a memory — because dropping those
        /// would mean the world forgot something because the player walked away,
        /// and pillar P5 says the city's state is the save file. Returns whether
        /// they were actually removed.
        public bool Forget(string id)
        {
            var g = Get(id);
            if (g == null) return false;
            if (g.Rumors.Count > 0 || g.Memory.Events.Count > 0 || g.Suppressed.Count > 0 || g.Leashed)
                return false;
            _agents.Remove(id);
            return true;
        }
        /// NULL IS A MISS, NOT A THROW. `Dictionary.TryGetValue(null)` raises
        /// ArgumentNullException — the one lookup method whose whole purpose is
        /// not to throw. `SaveChaos` reached it through `SaveCodec`, from a
        /// saved agent record whose `id` key had been deleted, and the
        /// exception escaped `Restore` past the only type the front end catches.
        /// "No agent by that name" is the honest answer for a name that is not
        /// there, and null is not there.
        public Gossiper Get(string id) =>
            id != null && _agents.TryGetValue(id, out var g) ? g : null;
        public IEnumerable<Gossiper> Agents => _agents.Values;

        /// How many rumour summaries say `word` out loud.
        ///
        /// WHY THIS IS IN CORE AND NOT A GREP. A rumour has two halves that
        /// look alike and are not: `Content` is a FACT, keyed on ids, and
        /// `Summary` is PROSE that a person reads on the ledger screen and a
        /// model reads in a prompt. The id for the player is the literal
        /// string `player`, which is correct in a Fact and is not a word any
        /// character in this game would ever say.
        ///
        /// It shipped. The panel readback from 0eeee6d holds four of these:
        ///
        ///     Rocco — "Mitch says it was player, and came to say so"
        ///
        /// and the sentence beside it, built by a different lambda, says
        /// "Novak" correctly. Same shape as the empty-slot bug repaired in
        /// that exact spot a day earlier — one idea, two implementations, and
        /// the one nobody looks at is the one missing a line. The earlier fix
        /// gave both halves ONE helper; the helper returns an ID, which is
        /// right for the fact and wrong for the words.
        ///
        /// A grep cannot find it because the leak is in the RUNNING world, not
        /// in the source: `{Accused(id)}` is an innocent-looking template, and
        /// what it interpolates depends on whether a witness had a name to
        /// give. So the check has to read the mill, and it lives here because
        /// Core is the layer that compiles and tests in this container.
        ///
        /// WHOLE WORDS. "a player's entrance" is a leak; "two players" is a
        /// different word and matching it would make the number un-actionable.
        public int SummariesSaying(string word)
        {
            if (string.IsNullOrEmpty(word)) return 0;
            int n = 0;
            foreach (var g in _agents.Values)
            {
                if (g == null) continue;
                foreach (var r in g.Rumors)
                    if (r != null && SaysWord(r.Summary, word)) n++;
            }
            return n;
        }

        /// Does `text` contain `word` as a whole word? Case-insensitive,
        /// because a sentence that starts "Player was seen…" is the same bug.
        public static bool SaysWord(string text, string word)
        {
            if (string.IsNullOrEmpty(text) || string.IsNullOrEmpty(word)) return false;
            for (int i = 0; i + word.Length <= text.Length; )
            {
                int at = text.IndexOf(word, i, StringComparison.OrdinalIgnoreCase);
                if (at < 0) return false;
                int end = at + word.Length;
                bool leftFree = at == 0 || !IsWordChar(text[at - 1]);
                bool rightFree = end >= text.Length || !IsWordChar(text[end]);
                if (leftFree && rightFree) return true;
                i = at + 1;
            }
            return false;
        }

        static bool IsWordChar(char c) => char.IsLetterOrDigit(c) || c == '_';

        /// A first-hand sighting enters the network. Confidence defaults to certain;
        /// a disguise (or distance, or darkness) passes less than 1.0 — the witness
        /// saw SOMETHING but can't swear to who, and everything downstream (spread,
        /// heat, bribe prices) inherits that doubt.
        public void Witness(string witnessId, Fact content, string summary, bool sensitive, GameTime now,
            double confidence = 1.0, bool indelible = false)
        {
            var w = Get(witnessId);
            if (w == null) return;
            confidence = Math.Clamp(confidence, 0.0, 1.0);
            if (confidence >= 0.95) w.Knowledge.Learn(content); // only certainty becomes hard knowledge
            var already = w.BestOfValue(content.Subject + "." + content.Predicate, content.Value);
            if (already == null)
            {
                w.Rumors.Add(new Rumor
                {
                    Content = content, OriginId = witnessId, Summary = summary,
                    Confidence = confidence, Hops = 0, Sensitive = sensitive,
                    Indelible = indelible,
                });
            }
            else if (indelible && !already.Indelible)
            {
                // Somebody who half-heard a scuffle later learns there was a
                // body in it. The doubtful version does not survive that: it
                // is upgraded in place, at whatever certainty the body
                // carries, rather than sitting alongside as a live maybe.
                already.Indelible = true;
                already.Confidence = Math.Max(already.Confidence, confidence);
                already.Hops = 0;
                already.Summary = summary;
                if (already.Confidence >= 0.95) w.Knowledge.Learn(content);
            }
            else if (confidence > already.Confidence)
            {
                // A clearer second look strengthens a doubtful first one. This
                // used to drop the repeat on the floor, so no later sighting
                // could ever firm up an early maybe (audit 2026-07-27).
                already.Confidence = confidence;
                already.Hops = 0;
                already.Summary = summary;
            }
            w.Memory.Append(new MemoryEvent(now, "observation", sensitive ? 0.9 : 0.6,
                confidence >= 0.95 ? $"I saw it myself: {summary}"
                    : $"I think I saw it — couldn't swear to it: {summary}"));
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
                        if (r.Confidence < MinConfidenceToShare && !r.Indelible) continue;
                        // Money and hooks buy silence about STORIES. Nobody keeps
                        // a body to themselves because they were paid to.
                        if (!r.Indelible && speaker.Suppressed.Contains(r.TopicKey)) continue; // bribed/scared into silence
                        if (!r.Indelible && speaker.Leashed && r.Content.Subject == "player") continue; // held by a hook
                        // A body arrives at the far end of the street exactly as
                        // true as it left. Hop decay is how a story turns into a
                        // maybe; this is not a story.
                        double passed = r.Indelible ? r.Confidence : r.Confidence * tie * HopDecay;
                        if (passed < MinConfidenceToShare) continue;

                        // Don't re-tell something the listener already holds at least as
                        // strongly — stops rumors amplifying by bouncing back and forth.
                        // Compared against the listener's best rumor OF THIS VALUE, not
                        // the topic's best overall: when two agents hold conflicting
                        // values, comparing against the overall best let each re-add an
                        // identical copy of the other's version every round, growing
                        // Rumors and Memory without bound (audit 2026-07-27).
                        var existing = listener.BestOfValue(r.TopicKey, r.Content.Value);
                        if (existing != null && existing.Confidence >= passed)
                            continue;

                        var heard = new Rumor
                        {
                            Content = r.Content, OriginId = r.OriginId, Summary = r.Summary,
                            Confidence = passed, Hops = r.Hops + 1, Sensitive = r.Sensitive,
                            Indelible = r.Indelible,
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

                        // AFTER the contradiction check, never before: an
                        // indelible rumour arrives at certainty however many
                        // mouths it crossed, and certainty is hard knowledge.
                        // Learning it first would make the listener's own new
                        // fact agree with itself and swallow the very
                        // contradiction the killing is supposed to expose.
                        if (heard.Indelible && heard.Confidence >= 0.95)
                            listener.Knowledge.Learn(heard.Content);

                        events.Add(ev);
                    }
                }
            }
            return events;
        }

        /// Suspicion-driven escalation (design-doc §6.4): a suspicious NPC doesn't
        /// wait for chance encounters — they seek someone out and ASK. A directed,
        /// deterministic exchange: the partner tells the checker everything they're
        /// willing to share about the player (suppression and leashes respected;
        /// leashed checkers don't check — the hook's protection). Same consequence
        /// rules as organic gossip: contradictions with the player's claims and
        /// cross-circle leaks move the checker's suspicion further.
        public List<GossipEvent> CompareNotes(string checkerId, string partnerId, GameTime now)
        {
            var events = new List<GossipEvent>();
            var checker = Get(checkerId);
            var partner = Get(partnerId);
            if (checker == null || partner == null || checker.Leashed) return events;

            checker.Memory.Append(new MemoryEvent(now, "conversation", 0.6,
                $"I asked {partner.DisplayName} straight out what they knew about the new owner."));

            double tie = System.Math.Max(_graph.Tie(checkerId, partnerId), 0.5); // asking directly beats a weak tie
            foreach (var r in partner.Rumors.ToList())
            {
                if (r.Content.Subject != "player") continue;
                if (r.Confidence < MinConfidenceToShare) continue;
                if (partner.Suppressed.Contains(r.TopicKey)) continue;
                if (partner.Leashed) break;

                double passed = r.Confidence * tie * HopDecay;
                if (passed < MinConfidenceToShare) continue;
                // Value-aware for the same reason as Tick's guard: conflicting
                // versions must settle, not breed (audit 2026-07-27).
                var existing = checker.BestOfValue(r.TopicKey, r.Content.Value);
                if (existing != null && existing.Confidence >= passed)
                    continue;

                var heard = new Rumor
                {
                    Content = r.Content, OriginId = r.OriginId, Summary = r.Summary,
                    Confidence = passed, Hops = r.Hops + 1, Sensitive = r.Sensitive,
                };
                checker.Rumors.Add(heard);
                checker.Memory.Append(new MemoryEvent(now, "heard",
                    System.Math.Clamp(passed * 0.8, 0.2, 0.85),
                    $"{partner.DisplayName} told me, when I asked: {r.Summary}"));

                var ev = new GossipEvent { FromId = partnerId, ToId = checkerId, Rumor = heard };
                if (checker.Knowledge.CheckClaim(r.Content) == ClaimResult.Contradiction)
                {
                    checker.Suspicion.Raise(ContradictionSuspicion * passed,
                        $"what {partner.DisplayName} told me contradicts what the new owner said to my face");
                    ev.Contradiction = true;
                }
                else if (r.Sensitive && checker.Circle == "day")
                {
                    checker.Suspicion.Raise(LeakSuspicion * passed, "I went asking, and I did not like the answer");
                    ev.Exposure = true;
                }
                events.Add(ev);
            }
            return events;
        }

        /// Does this NPC now carry a sensitive (night-life) rumor about the player? The
        /// player-facing signal that a secret has reached someone it shouldn't have.
        public bool KnowsSecret(string npcId) =>
            Get(npcId)?.Rumors.Any(r => r.Sensitive && r.Confidence >= MinConfidenceToShare) ?? false;

        /// A 0..1 "heat" reading: how convinced the most-convinced day-circle NPC is
        /// that the player leads a hidden life. DISTINCT stories corroborate — the
        /// noisy-or of an agent's best rumor per topic — so three half-believed
        /// sightings expose you where one never would, while retellings of the SAME
        /// story never stack. This is what makes carelessness (new witnesses every
        /// night) lethal and damage control (kill or discredit a story) meaningful.
        public double DayCircleHeat()
        {
            double max = 0;
            foreach (var a in _agents.Values)
            {
                if (a.Circle != "day") continue;
                // Heat is circulating TALK, and a leashed mouth cannot talk:
                // every spread path (Tick, Leads, CompareNotes) guards the
                // leash, and this read used to be the one side channel that
                // did not — a silenced witness still spawned Ellis and seeded
                // "somebody has been saying things" (audit 2026-07-27).
                if (a.Leashed) continue;
                var bestPerTopic = new Dictionary<string, double>();
                foreach (var r in a.Rumors)
                    if (r.Sensitive && (!bestPerTopic.TryGetValue(r.TopicKey, out var b) || r.Confidence > b))
                        bestPerTopic[r.TopicKey] = r.Confidence;
                double doubt = 1.0;
                foreach (var c in bestPerTopic.Values) doubt *= 1.0 - c;
                double combined = 1.0 - doubt;
                if (combined > max) max = combined;
            }
            return max;
        }

        // ---- awareness: what the player can learn to act on ----

        /// Everyone currently carrying (and willing to spread) talk about the subject,
        /// strongest first — the leads the player works from to decide who to lean on.
        public List<Lead> Leads(string subject = "player")
        {
            var subj = subject.ToLowerInvariant();
            var list = new List<Lead>();
            foreach (var a in _agents.Values)
            {
                if (a.Leashed && subj == "player") continue; // held: carrying, but never spreading
                foreach (var r in a.Rumors)
                    if (r.Content.Subject == subj && r.Confidence >= MinConfidenceToShare && !a.Suppressed.Contains(r.TopicKey))
                        list.Add(new Lead
                        {
                            HolderId = a.Id, HolderName = a.DisplayName, SourceId = r.OriginId,
                            TopicKey = r.TopicKey, Summary = r.Summary, Confidence = r.Confidence, Sensitive = r.Sensitive,
                        });
            }
            return list.OrderByDescending(l => l.Confidence).ToList();
        }

        // ---- damage control: the player's verbs against the rumor mill ----

        public double BribeBase = 50, BribePerConfidence = 150, BribeGreedFloor = 0.3;
        public double IntimidateNerveCeiling = 0.6;
        // Doubt cools a story without erasing it — buying or scaring the holder is
        // the only way to fully kill a telling, which is what keeps money relevant.
        public double DiscreditFactor = 0.65;

        /// What it would cost, right now, to buy this NPC's silence on a topic (more
        /// entrenched talk costs more). 0 = they're not carrying it.
        public double BribePrice(string npcId, string topicKey)
        {
            var r = Get(npcId)?.Best(topicKey);
            return r == null ? 0 : BribeBase + BribePerConfidence * r.Confidence;
        }

        /// Pay an NPC to drop a rumor. A greedy enough NPC pockets it and goes quiet; a
        /// too-principled one is offended and starts saying you tried to buy their silence.
        /// `purses` is optional so every existing caller keeps working. Pass it
        /// and the money you hand over lands in their drawer instead of leaving
        /// the world (roadmap M13) — which means a bribed man is carrying cash
        /// he cannot account for, and can pay a debt with it next week.
        public DcResult Bribe(string npcId, string topicKey, double offer, GameTime now,
            PurseBook purses = null)
        {
            var n = Get(npcId);
            // A leashed NPC already complies — no money needed, no backfire possible
            // (the strong hook's protection guarantee).
            if (n != null && n.Leashed)
                return Dc(DcOutcome.AlreadyDenied, $"{n.DisplayName} is already yours. Save your money.");
            var r = n?.Best(topicKey);
            if (r == null) return Dc(DcOutcome.NoSuchRumor, $"{npcId} isn't carrying that.");
            if (r.Indelible)
                return Dc(DcOutcome.Indelible,
                    $"{n.DisplayName} looks at the money, and then at you, and does not take it.");
            double price = BribeBase + BribePerConfidence * r.Confidence;
            if (offer < price) return Dc(DcOutcome.CantAfford, $"They want more than {offer:0} to forget it.");

            if (n.Greed >= BribeGreedFloor)
            {
                Contain(n, topicKey);
                n.Loyalty = Math.Clamp(n.Loyalty + 0.05, 0, 1);
                purses?.Credit(npcId, (int)Math.Round(price), now.Day, n.DisplayName);
                n.Memory.Append(new MemoryEvent(now, "conversation", 0.5,
                    $"The new owner paid me to keep quiet about {Short(topicKey)}. Suits me."));
                return Dc(DcOutcome.Contained, $"{n.DisplayName} takes the money and lets it drop.");
            }
            var backfire = Backfire(n, "tried_bribe", $"the new owner tried to buy my silence about {Short(topicKey)}", now);
            return new DcResult { Outcome = DcOutcome.Backfired, NewRumor = backfire,
                Message = $"{n.DisplayName} won't be bought — and now they're talking about it." };
        }

        /// Lean on an NPC. The easily-cowed shut up (but resent it); the steady ones
        /// don't scare and now there's worse talk — that you threatened them.
        public DcResult Intimidate(string npcId, string topicKey, GameTime now)
        {
            var n = Get(npcId);
            // The leash outranks the threat — nothing left to scare out of them,
            // and no backfire possible.
            if (n != null && n.Leashed)
                return Dc(DcOutcome.AlreadyDenied, $"{n.DisplayName} already knows what you know. There is nothing left to threaten.");
            var r = n?.Best(topicKey);
            if (r == null) return Dc(DcOutcome.NoSuchRumor, $"{npcId} isn't carrying that.");
            // Threatening a witness to a killing is the one threat that cannot
            // work, because the thing you are threatening them with is exactly
            // the thing they already watched you do.
            if (r.Indelible)
                return Dc(DcOutcome.Indelible,
                    $"{n.DisplayName} has already seen what you do. There is nothing left to threaten them with.");

            if (n.Nerve <= IntimidateNerveCeiling)
            {
                Contain(n, topicKey);
                n.Loyalty = Math.Clamp(n.Loyalty - 0.2, 0, 1);
                n.Memory.Append(new MemoryEvent(now, "observation", 0.7,
                    $"The new owner warned me off talking about {Short(topicKey)}. Best I stay quiet."));
                return Dc(DcOutcome.Contained, $"{n.DisplayName} backs down, rattled.");
            }
            var backfire = Backfire(n, "threatened", $"the new owner threatened me over {Short(topicKey)}", now);
            return new DcResult { Outcome = DcOutcome.Backfired, NewRumor = backfire,
                Message = $"{n.DisplayName} doesn't scare — and now there's worse talk." };
        }

        /// Plant doubt about a specific story, cutting the confidence of every version of
        /// it across the network. Doesn't erase it, and the street only buys a denial
        /// ONCE per story — repeat denials are already priced in. That cap is what
        /// stops "deny everything daily" from being a complete defense: at some point
        /// a story must be killed at its holder, with money or muscle.
        public DcResult Discredit(string topicKey, string value, GameTime now)
        {
            // Refused BEFORE the once-per-story cap is spent, so a denial
            // wasted on a killing does not also burn the denial you might
            // legitimately have needed for something else on that topic.
            if (HoldsIndelible(topicKey, value))
                return new DcResult { Outcome = DcOutcome.Indelible, Affected = 0,
                    Message = "There is a body. No amount of denying makes it not be there." };
            // The cap is per STORY — and two values of one topic are two
            // stories. Keyed by topic alone, denying the warehouse version
            // burned the denial for the docks version too (audit 2026-07-27).
            // Old saves hold bare topic keys; those still read as denied.
            var capKey = value == null ? topicKey : topicKey + "=" + value.ToLowerInvariant();
            if (_discredited.Contains(topicKey) || !_discredited.Add(capKey))
                return new DcResult { Outcome = DcOutcome.AlreadyDenied, Affected = 0,
                    Message = "The street has already heard your denials about that; repeating them changes nothing." };
            var v = value?.ToLowerInvariant();
            int affected = 0;
            foreach (var a in _agents.Values)
                foreach (var r in a.Rumors)
                    if (r.TopicKey == topicKey && (v == null || r.Content.Value == v) && !r.Indelible)
                    { r.Confidence *= DiscreditFactor; affected++; }
            foreach (var a in _agents.Values) a.Rumors.RemoveAll(r => r.Confidence < 0.03 && !r.Indelible);
            return new DcResult { Outcome = affected > 0 ? DcOutcome.Contained : DcOutcome.NoSuchRumor, Affected = affected,
                Message = affected > 0 ? $"Doubt spreads; {affected} telling(s) of it lose weight." : "No such story to discredit." };
        }
        readonly HashSet<string> _discredited = new HashSet<string>();

        /// Save-load surface for the once-per-story denial cap.
        public IEnumerable<string> DiscreditedTopics => _discredited;
        public bool IsDiscredited(string topicKey) => _discredited.Contains(topicKey);

        /// The strongest live lead an investigator could take to a magistrate:
        /// the best-confidence sensitive player rumor held by anyone who is not
        /// leashed, not bribed/scared quiet on that topic, and whose story has
        /// not been publicly discredited. This is what "managing the
        /// information landscape" cashes out to in Act III: drive this below
        /// testimony grade and Ellis's case is answerable WITHOUT taking her
        /// deflection deal (act3-draft.md answer 3, wired per audit 2026-07-27
        /// — before this, Deflected was the sole source of answerability).
        public double StrongestSurvivingPlayerLead()
        {
            double best = 0;
            foreach (var a in Agents)
            {
                foreach (var r in a.Rumors)
                {
                    if (r.Content.Subject != "player" || !r.Sensitive) continue;
                    // A body survives every one of these. It is the one lead
                    // that cannot be managed off the table, so no amount of
                    // information landscaping makes Ellis's case answerable
                    // once there is one.
                    if (r.Indelible) return Math.Max(best, r.Confidence);
                    if (a.Leashed) continue;
                    if (a.Suppressed.Contains(r.TopicKey)) continue;
                    if (_discredited.Contains(r.TopicKey)
                        || _discredited.Contains(r.TopicKey + "=" + (r.Content.Value ?? "").ToLowerInvariant())) continue;
                    if (r.Confidence > best) best = r.Confidence;
                }
            }
            return best;
        }
        public void RestoreDiscredited(IEnumerable<string> topics)
        {
            _discredited.Clear();
            if (topics != null) foreach (var t in topics) _discredited.Add(t);
        }

        /// Use a hook (design-doc §6.3): knowledge beats traits. A STRONG hook
        /// (criminal secret) leashes the target for good — nothing about the player
        /// leaves their lips again, and no backfire is possible; they know what you
        /// know. A WEAK hook (shameful secret) is one big favor: their strongest
        /// current story about you goes quiet, and the hook is spent. Either way
        /// they comply — and hate you a little for it.
        public DcResult UseHook(string npcId, Secret secret, GameTime now)
        {
            var n = Get(npcId);
            if (n == null || secret == null || secret.OwnerId != npcId || !secret.KnownToPlayer)
                return Dc(DcOutcome.NoSuchRumor, "You hold nothing on them.");

            if (secret.Strong)
            {
                if (n.Leashed) return Dc(DcOutcome.AlreadyDenied, "They already know what you know. They haven't forgotten.");
                n.Leashed = true;
                n.Loyalty = System.Math.Clamp(n.Loyalty - 0.3, 0, 1);
                n.Suspicion.Raise(0.1, "the new owner holds it over me");
                n.Memory.Append(new MemoryEvent(now, "observation", 0.95,
                    $"The new owner knows. Said it to my face: {secret.Summary} I keep my mouth shut now — about them, about everything."));
                return Dc(DcOutcome.Contained, $"{n.DisplayName} goes very still. Nothing about you will leave their lips again.");
            }

            if (secret.HookSpent)
                return Dc(DcOutcome.AlreadyDenied, "You already called that favor in. It doesn't work twice.");
            var strongest = n.Rumors.Where(r => r.Content.Subject == "player" && !n.Suppressed.Contains(r.TopicKey))
                .OrderByDescending(r => r.Confidence).FirstOrDefault();
            if (strongest == null)
                return Dc(DcOutcome.NoSuchRumor, "They're not carrying anything worth spending it on. Keep it.");
            secret.SpendWeak();
            Contain(n, strongest.TopicKey);
            n.Loyalty = System.Math.Clamp(n.Loyalty - 0.2, 0, 1);
            n.Memory.Append(new MemoryEvent(now, "observation", 0.85,
                $"The new owner reminded me about {secret.Summary} So I let the talk drop. Once. We're even now."));
            var done = Dc(DcOutcome.Contained, $"{n.DisplayName}'s face changes. That story dies with them — and you're even now.");
            done.ContainedTopic = strongest.TopicKey;
            return done;
        }
        // NOTE (§6.3 deferral): the strong hook's "protection from hostile acts" is
        // enforced for everything NPCs can currently do (spreading, backfires — see
        // the Leashed guards in Tick/Bribe/Intimidate). When M4.2 adds suspicion-
        // driven probe/verify/confront behaviors, leashed NPCs must be barred from
        // those escalations too.

        /// Rumors fade if nobody keeps them alive — the "lie low and let it cool" option.
        /// Call once per in-game hour; confidence decays on a multi-day half-life and
        /// spent rumors drop out entirely.
        public void Age(GameTime now)
        {
            if (_aged)
            {
                double hrs = (now.TotalMinutes - _lastAge.TotalMinutes) / 60.0;
                if (hrs > 0)
                {
                    double f = Math.Pow(0.5, hrs / RumorHalfLifeHours);
                    foreach (var a in _agents.Values)
                    {
                        // A body does not go cold the way a story does. Lying
                        // low is the answer to talk; it is not the answer to
                        // a corpse.
                        foreach (var r in a.Rumors) if (!r.Indelible) r.Confidence *= f;
                        a.Rumors.RemoveAll(r => r.Confidence < 0.03 && !r.Indelible);
                    }
                }
            }
            _lastAge = now;
            _aged = true;
        }
        public double RumorHalfLifeHours = 96;
        GameTime _lastAge;
        bool _aged;

        /// Is anyone carrying this story as a FACT rather than a story?
        public bool HoldsIndelible(string topicKey, string value = null)
        {
            var v = value?.ToLowerInvariant();
            foreach (var a in _agents.Values)
                foreach (var r in a.Rumors)
                    if (r.Indelible && r.TopicKey == topicKey && (v == null || r.Content.Value == v))
                        return true;
            return false;
        }

        void Contain(Gossiper n, string topicKey)
        {
            n.Suppressed.Add(topicKey);
            foreach (var r in n.Rumors)
                if (r.TopicKey == topicKey && r.Confidence > 0.05 && !r.Indelible) r.Confidence = 0.05;
        }

        Rumor Backfire(Gossiper n, string predicate, string summary, GameTime now)
        {
            var fact = new Fact("player", predicate, "true");
            Rumor r = null;
            if (!n.Holds(fact.Subject + "." + fact.Predicate, "true"))
            {
                r = new Rumor { Content = fact, OriginId = n.Id, Summary = summary, Confidence = 0.9, Hops = 0, Sensitive = true };
                n.Rumors.Add(r);
            }
            n.Suspicion.Raise(0.1, "the new owner leaned on me");
            n.Loyalty = Math.Clamp(n.Loyalty - 0.15, 0, 1);
            n.Memory.Append(new MemoryEvent(now, "observation", 0.85, "I won't forget this: " + summary));
            return r ?? n.Best(fact.Subject + "." + fact.Predicate);
        }

        static string Short(string topicKey) => topicKey.Replace("player.", "").Replace('_', ' ');
        static DcResult Dc(DcOutcome o, string msg) => new DcResult { Outcome = o, Message = msg };
    }

    /// `Indelible`: the move was refused because the thing it aimed at is a
    /// body. Deliberately NOT NoSuchRumor — the story is very much alive, and
    /// telling the player it "died down on its own" would be the single most
    /// dishonest line the game could print.
    public enum DcOutcome { NoSuchRumor, CantAfford, Contained, Backfired, AlreadyDenied, Indelible }

    /// The result of a damage-control move: what happened, a line to show the player,
    /// any new rumor the move created (a backfire), and how many rumors it touched.
    public class DcResult
    {
        public DcOutcome Outcome;
        public string Message;
        public Rumor NewRumor;
        public int Affected;
        /// The topic a hook favor silenced — the mill picks its LIVE strongest,
        /// which may differ from what the player believed; callers sync belief off this.
        public string ContainedTopic;
    }

    /// A lead the player can act on: who is carrying talk about them, how sure they are,
    /// where it came from, and whether it touches the hidden life.
    public class Lead
    {
        public string HolderId, HolderName, SourceId, TopicKey, Summary;
        public double Confidence;
        public bool Sensitive;
    }
}
