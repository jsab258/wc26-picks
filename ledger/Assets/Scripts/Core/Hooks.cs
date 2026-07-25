using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    public enum SecretKind { Shameful, Criminal }

    /// Design-doc §6.3: what you know about people is loot. A learned shameful
    /// secret is a WEAK hook — one big favor. A learned criminal secret is a
    /// STRONG hook — standing coercion. Hooks are knowledge, so they beat traits:
    /// the unbribable can still be held by what they've done.
    public class Secret
    {
        public string Id;
        public string OwnerId;
        public string Summary;
        public SecretKind Kind;
        /// People besides the owner who know it — the paths it can leak to you by.
        public readonly List<string> KnownBy = new List<string>();

        public bool KnownToPlayer { get; private set; }
        public bool HookSpent { get; private set; } // weak hooks are one-shot
        public GameTime LearnedAt;
        public string LearnedFrom;

        public bool Strong => Kind == SecretKind.Criminal;

        public void Learn(string from, GameTime now)
        {
            if (KnownToPlayer) return;
            KnownToPlayer = true;
            LearnedFrom = from;
            LearnedAt = now;
        }

        public void SpendWeak() { HookSpent = true; }
    }

    /// The city's authored secrets and which of them the player has collected.
    public class SecretsBook
    {
        readonly List<Secret> _secrets = new List<Secret>();

        public void Add(Secret s) => _secrets.Add(s);
        public IEnumerable<Secret> All => _secrets;
        public IEnumerable<Secret> Known => _secrets.Where(s => s.KnownToPlayer);
        public Secret ById(string id) => _secrets.FirstOrDefault(s => s.Id == id);

        /// A hook the player can use on this person right now: known, and either
        /// standing (criminal) or not yet spent (shameful).
        public Secret UsableHook(string ownerId) =>
            _secrets.FirstOrDefault(s => s.OwnerId == ownerId && s.KnownToPlayer
                && (s.Strong || !s.HookSpent));

        /// Secrets this NPC would tell the player, given how loyal they feel:
        /// their own takes deep trust (confession); someone else's takes less
        /// (gossip among friends). Only unlearned secrets are tellable.
        public List<Secret> TellableBy(string npcId, double loyalty, double confessFloor, double shareFloor) =>
            _secrets.Where(s => !s.KnownToPlayer &&
                ((s.OwnerId == npcId && loyalty >= confessFloor) ||
                 (s.KnownBy.Contains(npcId) && loyalty >= shareFloor))).ToList();
    }
}
