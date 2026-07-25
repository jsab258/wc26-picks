using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    public enum CollectOutcome { Paid, Begged, Refused, Nothing }

    /// One line in Marek's book of uncollectable debts (the founding premise's
    /// inheritance). Collection is social, not violent: whether they pay, beg, or
    /// dig in is decided by who they are — and pressing people has a price.
    public class Debtor
    {
        public string Id;         // gossiper id
        public string Name;
        public int Amount;
        public string Note;       // what the money was for, in Marek's hand
        public bool Collected { get; private set; }
        public bool Forgiven { get; private set; }
        public int LastAskedDay { get; private set; } = -1;

        public bool Outstanding => !Collected && !Forgiven;

        /// Trait-gated collection. Loyal debtors pay (grudgingly); the nervous beg
        /// for a day; the rest refuse — and tell the street you came squeezing.
        public CollectOutcome Collect(Gossiper g, Wallet wallet, GossipMill mill, GameTime now)
        {
            if (!Outstanding || g == null) return CollectOutcome.Nothing;
            if (LastAskedDay == now.Day) return CollectOutcome.Nothing; // once a day
            LastAskedDay = now.Day;

            if (g.Loyalty >= 0.5)
            {
                Collected = true;
                wallet.EarnClean(Amount);
                g.Loyalty = Math.Clamp(g.Loyalty - 0.05, 0, 1);
                g.Memory.Append(new MemoryEvent(now, "conversation", 0.6,
                    $"Paid the new owner what I owed Marek. ${Amount}. It stung, but fair is fair."));
                return CollectOutcome.Paid;
            }
            if (g.Nerve <= 0.5)
            {
                g.Memory.Append(new MemoryEvent(now, "conversation", 0.5,
                    $"The new owner asked about Marek's ${Amount}. I begged a day. I don't have it."));
                return CollectOutcome.Begged;
            }
            g.Loyalty = Math.Clamp(g.Loyalty - 0.1, 0, 1);
            g.Memory.Append(new MemoryEvent(now, "observation", 0.7,
                $"The new owner came collecting Marek's old paper. I told them where to put it."));
            if (mill != null && !g.Holds("player.debt_collecting", "true"))
                g.Rumors.Add(new Rumor
                {
                    Content = new Fact("player", "debt_collecting", "true"), OriginId = g.Id,
                    Summary = "the new owner came collecting Marek's old debts, hard",
                    Confidence = 0.7, Hops = 0, Sensitive = false,
                });
            return CollectOutcome.Refused;
        }

        /// Tearing up the page buys something money can't.
        public bool Forgive(Gossiper g, GameTime now)
        {
            if (!Outstanding || g == null) return false;
            Forgiven = true;
            g.Loyalty = Math.Clamp(g.Loyalty + 0.15, 0, 1);
            g.Memory.Append(new MemoryEvent(now, "conversation", 0.8,
                $"The new owner tore my page out of Marek's book. ${Amount}, gone like that. I won't forget it."));
            return true;
        }

        /// Save-load overlay.
        public void Restore(bool collected, bool forgiven, int lastAskedDay)
        {
            Collected = collected; Forgiven = forgiven; LastAskedDay = lastAskedDay;
        }
    }

    public class DebtBook
    {
        readonly List<Debtor> _debtors = new List<Debtor>();
        public void Add(Debtor d) => _debtors.Add(d);
        public IEnumerable<Debtor> All => _debtors;
        public Debtor Of(string id) => _debtors.FirstOrDefault(d => d.Id == id && d.Outstanding);
        public Debtor ById(string id) => _debtors.FirstOrDefault(d => d.Id == id);
    }
}
