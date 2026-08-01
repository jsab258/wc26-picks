using System;

namespace Ledger.Core
{
    /// Two currencies that resist mixing (design-doc §6.7): clean money spends
    /// anywhere; dirty money is fast but only criminal counterparties take it, and
    /// a supplier to a mob bar taking cash off the counter IS one — the drayman
    /// and the amends-price are paid dirtyOk by design, settled 2026-07-28
    /// (delegated; wrote the fiction in rather than flipping the balance), and
    /// it only becomes clean by washing through the bar's till — a capped daily
    /// pipeline. Hoarded dirty cash is evidence to anyone who sees the books.
    public class Wallet
    {
        public int Clean { get; private set; }
        public int Dirty { get; private set; }
        public int Total => Clean + Dirty;
        public int TotalWashed { get; private set; }

        /// How much dirty cash the bar's till can plausibly absorb per daily close.
        public int LaunderPerDay = 120;

        public Wallet(int startingClean) { Clean = Math.Max(0, startingClean); }

        public void EarnClean(int amount) { if (amount > 0) Clean += amount; }
        public void EarnDirty(int amount) { if (amount > 0) Dirty += amount; }

        /// Spend clean first; touch dirty only when the counterparty takes it
        /// (bribes yes, the day world no). False = can't cover it that way.
        public bool Spend(int amount, bool dirtyOk)
        {
            if (amount <= 0) return true;
            int available = dirtyOk ? Total : Clean;
            if (available < amount) return false;
            int fromClean = Math.Min(Clean, amount);
            Clean -= fromClean;
            int rest = amount - fromClean;
            if (rest > 0) Dirty -= rest;
            return true;
        }

        /// Save-load overlay: state only, invariants unchanged.
        /// A PURSE CANNOT HOLD LESS THAN NOTHING, whatever the file says.
        ///
        /// The constructor has clamped `startingClean` since it was written and
        /// this bypassed it — so `"dirty": -1e308` restored to minus two
        /// billion, and `SaveChaos` found it. That is not a small wrong number:
        /// `Seize()` returns `Dirty` as the amount taken in a Fall, `Launder`
        /// moves it into `Clean`, and every affordability check reads
        /// `Clean >= price`. A large negative dirty purse makes the player
        /// unseizable and permanently broke at once.
        public void Restore(int clean, int dirty, int washed)
        {
            Clean = Math.Max(0, clean);
            Dirty = Math.Max(0, dirty);
            TotalWashed = Math.Max(0, washed);
        }

        /// The law takes what the books can't explain (a Fall seizes the
        /// unwashed). Returns the amount seized.
        public int Seize()
        {
            int seized = Dirty;
            Dirty = 0;
            return seized;
        }

        /// Daily close: wash what the till can absorb. Returns the amount washed.
        public int Launder()
        {
            int washed = Math.Min(Dirty, LaunderPerDay);
            Dirty -= washed;
            Clean += washed;
            TotalWashed += washed;
            return washed;
        }
    }
}
