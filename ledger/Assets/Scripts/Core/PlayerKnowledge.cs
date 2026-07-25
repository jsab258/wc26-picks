using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// One entry in the player's ledger: a piece of talk the player BELIEVES is out
    /// there. A snapshot from the moment it was learned — the network moves on
    /// without updating it, which is the point.
    public class KnownLead
    {
        public string HolderId, HolderName, TopicKey, Summary, Source;
        public double ConfidenceWhenLearned;
        public GameTime LearnedAt;
        public bool Sensitive;
        public bool Handled; // the player believes they dealt with it
    }

    /// The player's belief-state about the rumor network. Design rule (design-doc
    /// §6.2): the player sees what they BELIEVE the city knows — never ground truth.
    /// Entries arrive only through play: seeing who watched you work, a loyal
    /// friend's warning, or a carrier admitting what they hold in conversation.
    public class PlayerKnowledge
    {
        readonly Dictionary<string, KnownLead> _known = new Dictionary<string, KnownLead>();

        static string Key(string holderId, string topicKey) => holderId + "|" + topicKey;

        public int Count => _known.Count;

        public IEnumerable<KnownLead> Entries =>
            _known.Values.OrderByDescending(k => k.LearnedAt.TotalMinutes);

        public bool Knows(string holderId, string topicKey) =>
            _known.ContainsKey(Key(holderId, topicKey));

        /// Record (or refresh) a lead the player just learned about. Returns true if
        /// this is news; refreshing an old entry updates the snapshot and un-handles
        /// it (if you're hearing about it again, it isn't dealt with).
        public bool Learn(Lead lead, string source, GameTime now)
        {
            var key = Key(lead.HolderId, lead.TopicKey);
            if (_known.TryGetValue(key, out var existing))
            {
                existing.ConfidenceWhenLearned = lead.Confidence;
                existing.LearnedAt = now;
                existing.Source = source;
                existing.Handled = false;
                return false;
            }
            _known[key] = new KnownLead
            {
                HolderId = lead.HolderId, HolderName = lead.HolderName,
                TopicKey = lead.TopicKey, Summary = lead.Summary, Source = source,
                ConfidenceWhenLearned = lead.Confidence, LearnedAt = now,
                Sensitive = lead.Sensitive,
            };
            return true;
        }

        /// Save-load overlay: re-insert a persisted entry verbatim.
        public void Restore(KnownLead k)
        {
            if (k != null) _known[Key(k.HolderId, k.TopicKey)] = k;
        }

        public void MarkHandled(string holderId, string topicKey)
        {
            if (_known.TryGetValue(Key(holderId, topicKey), out var k)) k.Handled = true;
        }

        /// The strongest still-unhandled talk the player believes this NPC is
        /// carrying — what the damage-control verbs key off.
        public KnownLead StrongestFor(string holderId) =>
            _known.Values.Where(k => k.HolderId == holderId && !k.Handled)
                .OrderByDescending(k => k.ConfidenceWhenLearned).FirstOrDefault();
    }
}
