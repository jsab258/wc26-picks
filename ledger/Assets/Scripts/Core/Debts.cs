using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    public enum CollectOutcome { Paid, PaidPart, Begged, Refused, Nothing }

    /// One line in Mickey's book of uncollectable debts (the founding premise's
    /// inheritance). Collection is social, not violent: whether they pay, beg, or
    /// dig in is decided by who they are — and pressing people has a price.
    public class Debtor
    {
        public string Id;         // gossiper id
        public string Name;
        public int Amount;
        public string Note;       // what the money was for, in Mickey's hand
        /// What the last collection actually produced, and what it left behind.
        /// Read by the UI so the line it prints is the truth rather than the ask.
        public int LastPaid { get; private set; }
        public string LastLine { get; private set; }
        public bool Collected { get; private set; }
        public bool Forgiven { get; private set; }
        public int LastAskedDay { get; private set; } = -1;

        public bool Outstanding => !Collected && !Forgiven;

        /// Trait-gated collection. Loyal debtors pay (grudgingly); the nervous beg
        /// for a day; the rest refuse — and tell the street you came squeezing.
        /// `purses` is optional so every existing caller and test keeps working;
        /// pass it and the willing debtor can only hand over what they actually
        /// have, which is roadmap M13 and the whole point of the system.
        public CollectOutcome Collect(Gossiper g, Wallet wallet, GossipMill mill, GameTime now,
            PurseBook purses = null)
        {
            if (!Outstanding || g == null) return CollectOutcome.Nothing;
            if (LastAskedDay == now.Day) return CollectOutcome.Nothing; // once a day
            LastAskedDay = now.Day;
            LastPaid = 0;
            LastLine = null;

            if (g.Loyalty >= 0.5)
            {
                // Willing is not the same as able. Without a purse book this is
                // the old behaviour exactly; with one, a man who turns over £90
                // a week cannot produce £400 because you asked nicely.
                int paid = Amount;
                // FALSE WITH NO PURSE BOOK, and that is the old behaviour
                // exactly: without a book there is no such thing as an empty
                // drawer, so nobody can be cleaned out by paying.
                bool cleanedOut = false;
                if (purses != null)
                {
                    var payment = purses.Take(Id, Amount, now.Day, g.DisplayName);
                    paid = payment.Paid;
                    LastLine = payment.Line;
                    cleanedOut = payment.Emptied && payment.InFull;
                }
                LastPaid = paid;

                if (paid <= 0)
                {
                    // Willing and empty. That is a beg, and it is a truthful one.
                    g.Memory.Append(new MemoryEvent(now, "conversation", 0.55,
                        $"The new owner came for Mickey's £{Amount} and I had nothing to give them. " +
                        "I have never been so glad of a drawer nobody can argue with."));
                    return CollectOutcome.Begged;
                }

                wallet.EarnClean(paid);
                if (paid < Amount)
                {
                    Amount -= paid;
                    // Emptying somebody costs more standing than being paid by
                    // them earns you. They stood there and counted it out.
                    g.Loyalty = Math.Clamp(g.Loyalty - 0.09, 0, 1);
                    g.Memory.Append(new MemoryEvent(now, "conversation", 0.7,
                        $"Gave the new owner every coin in the place — £{paid} — against Mickey's book. " +
                        $"Still £{Amount} short and they know where I live."));
                    return CollectOutcome.PaidPart;
                }

                Collected = true;

                // PAID IN FULL AND CLEANED OUT IS NOT THE SAME DAY AS PAID IN
                // FULL, and until now the game could not tell them apart.
                //
                // `Payment` has carried `InFull` and `Emptied` since it was
                // written and nothing read either — `Payment.InFull` has an
                // entry on the reach ledger saying "the purse records it and no
                // UI or reaction reads it". The branch above splits on `paid <
                // Amount`, which asks whether the DEBT is clear. Whether the
                // MAN is clear is a different question with the same answer
                // shape, and it is the one that decides what he is like
                // tomorrow.
                //
                // THE COST IS BEING EMPTIED, NOT BEING SHORT. So this takes the
                // same 0.09 the part-payment branch does rather than a third
                // number: somebody who counted out every coin he had resents it
                // exactly as much whether or not it happened to clear the book.
                // Reusing the constant is the point — two numbers for one idea
                // is how the fog came to have two owners.
                g.Loyalty = Math.Clamp(g.Loyalty - (cleanedOut ? 0.09 : 0.05), 0, 1);
                g.Memory.Append(new MemoryEvent(now, "conversation", cleanedOut ? 0.7 : 0.6,
                    cleanedOut
                        ? $"Paid the new owner Mickey's £{paid} to the penny and there is "
                          + "nothing left in the place. Fair is fair. I still counted it twice."
                        : $"Paid the new owner what I owed Mickey. £{paid}. It stung, but fair is fair."));
                return CollectOutcome.Paid;
            }
            if (g.Nerve <= 0.5)
            {
                g.Memory.Append(new MemoryEvent(now, "conversation", 0.5,
                    $"The new owner asked about Mickey's £{Amount}. I begged a day. I don't have it."));
                return CollectOutcome.Begged;
            }
            g.Loyalty = Math.Clamp(g.Loyalty - 0.1, 0, 1);
            g.Memory.Append(new MemoryEvent(now, "observation", 0.7,
                $"The new owner came collecting Mickey's old paper. I told them where to put it."));
            if (mill != null && !g.Holds("player.debt_collecting", "true"))
                g.Rumors.Add(new Rumor
                {
                    Content = new Fact("player", "debt_collecting", "true"), OriginId = g.Id,
                    Summary = "the new owner came collecting Mickey's old debts, hard",
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
                $"The new owner tore my page out of Mickey's book. £{Amount}, gone like that. I won't forget it."));
            return true;
        }

        /// Save-load overlay. Amount is included because part-payment changes
        /// it — a debt that reset to its original figure on load would be a
        /// quiet way of stealing back everything the player collected.
        public void Restore(bool collected, bool forgiven, int lastAskedDay, int amount = -1)
        {
            Collected = collected; Forgiven = forgiven; LastAskedDay = lastAskedDay;
            if (amount >= 0) Amount = amount;
        }
    }

    public class DebtBook
    {
        readonly List<Debtor> _debtors = new List<Debtor>();
        public void Add(Debtor d) => _debtors.Add(d);
        public IEnumerable<Debtor> All => _debtors;
        public Debtor Of(string id) => _debtors.FirstOrDefault(d => d.Id == id && d.Outstanding);
        public Debtor ById(string id) => _debtors.FirstOrDefault(d => d.Id == id);

        /// Overnight, anybody who was emptied and still owes goes to whoever
        /// they have. You will often not know this happened — you will notice
        /// that they paid, and that they are colder about it than the money
        /// explains.
        public List<string> NightBorrowing(PurseBook purses, GossipMill mill, GameTime now)
        {
            var went = new List<string>();
            if (purses == null) return went;
            foreach (var d in _debtors)
            {
                if (!d.Outstanding) continue;
                var purse = purses.Of(d.Id);
                if (purse == null || purse.LastEmptiedDay < 0) continue;
                var patron = purses.Borrow(d.Id, d.Amount, now.Day);
                if (patron == null) continue;
                went.Add(d.Id);

                var g = mill?.Get(d.Id);
                var lender = mill?.Get(patron);
                if (g != null)
                    g.Memory.Append(new MemoryEvent(now, "conversation", 0.75,
                        $"Went to {lender?.DisplayName ?? patron} and asked for money, because of Mickey's book " +
                        "and the person who bought it. I will be paying for that asking longer than for the money."));
                if (lender != null)
                    lender.Memory.Append(new MemoryEvent(now, "conversation", 0.6,
                        $"{g?.DisplayName ?? d.Id} came to me for money. The new owner has been leaning on them. " +
                        "I gave it. I will remember that I gave it."));
            }
            return went;
        }
    }
}
