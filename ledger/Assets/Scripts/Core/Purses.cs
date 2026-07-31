using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// Finite counterparty purses (roadmap M13, `counterparty-purses-spec.md`).
    ///
    /// The living economy made the district's money finite in one direction —
    /// squeeze the street, the street gets poorer, your bar takes less. But
    /// every counterparty still had infinite pockets: Rita owed £180 and
    /// produced £180 on demand, out of a starving street, in one movement. That
    /// is a payout table wearing a person's face.
    ///
    /// A purse is what somebody can lay hands on TODAY. Not their wealth, not
    /// their income — the money in the drawer. Ask for more than that and you
    /// get what is there, and the balance stays on the page.
    ///
    /// The thing this buys is not friction. It is that a big marker stops being
    /// a transaction and becomes a relationship: four visits, or one visit and
    /// a decision about what you are willing to do to shorten it. And the
    /// question "who has the cash, and what do they want for fronting it" is a
    /// conversation, which is what this game is made of.
    public class Purse
    {
        public string OwnerId;
        public string Name;
        /// What they can lay hands on right now.
        public int Cash;
        /// What flows through them in an ordinary week, at ordinary prosperity.
        public int Weekly;
        /// The most they would keep to hand rather than spend it or bank it.
        public int Ceiling;
        /// Who they could go to if they were pressed. Null means nobody, and
        /// nobody is a harder life than it sounds.
        public string PatronId;

        public int LastEmptiedDay = -1;
        public int TimesEmptied;
        /// Money that arrived from the player rather than from their week's
        /// work, and the day it did. A bribed man is a man carrying cash he
        /// cannot account for, which is evidence — and it is exactly the sort
        /// of thing a careful investigator asks about.
        public int Windfall;
        public int LastWindfallDay = -1;
        /// Set the night they borrow, so the game can tell the difference
        /// between somebody who had it and somebody who went and got it.
        public int LastBorrowedDay = -1;
    }

    /// What actually came out of a purse.
    public struct Payment
    {
        public int Paid;
        public int Short;
        public bool Emptied;
        /// Said as a circumstance, never as a figure of what they hold. Null
        /// when they paid in full and the caller has its own line.
        public string Line;

        public bool InFull => Short == 0 && Paid > 0;
        public bool Nothing => Paid == 0;
    }

    /// Somebody went to somebody else for money. Real world state rather than
    /// flavour: the Director can read this and act on it, which is the whole
    /// reason borrowing is worth modelling at all.
    public class Favour
    {
        public string DebtorId, PatronId;
        public int Amount;
        public int Day;
        public bool Settled;
    }

    public class PurseBook
    {
        readonly Dictionary<string, Purse> _purses = new Dictionary<string, Purse>();
        readonly List<Favour> _favours = new List<Favour>();

        public IEnumerable<Purse> All => _purses.Values;
        public IReadOnlyList<Favour> Favours => _favours;

        /// How prosperity scales what flows into a purse. At the ordinary half
        /// this is 1.0, so a campaign that takes nothing behaves exactly as it
        /// did before this file existed — the same rule the rest of the economy
        /// follows.
        public static double FlowAt(double prosperity) =>
            Math.Max(0.15, 0.35 + 1.3 * Math.Clamp(prosperity, 0, 1));

        public Purse Of(string id) =>
            id != null && _purses.TryGetValue(id, out var p) ? p : null;

        public void Add(Purse p)
        {
            if (p == null || p.OwnerId == null) return;
            _purses[p.OwnerId] = p;
        }

        /// A purse for somebody nobody authored one for. Derived from a stable
        /// hash of their id, so three thousand residents are covered without
        /// three thousand authored numbers and the same person always has the
        /// same means. Starts part-full: a street where everybody is broke on
        /// day one is not a street, it is a famine.
        public Purse For(string id, string name = null)
        {
            var existing = Of(id);
            if (existing != null) return existing;
            double h = Population.StableFraction(id ?? "nobody");
            int weekly = 35 + (int)Math.Round(h * 130);          // £35..£165 a week
            var p = new Purse
            {
                OwnerId = id,
                Name = name ?? id,
                Weekly = weekly,
                Ceiling = (int)Math.Round(weekly * (1.1 + h * 1.2)),
            };
            p.Cash = (int)Math.Round(p.Ceiling * (0.30 + h * 0.45));
            Add(p);
            return p;
        }

        /// A day's takings, everywhere at once. Prosperity is the coupling that
        /// makes this worth having: squeezing the street drains the pockets you
        /// are trying to collect from, and it does it a few days later, when you
        /// have started relying on being paid.
        public void DailyTick(int day, double prosperity)
        {
            double flow = FlowAt(prosperity);
            foreach (var p in _purses.Values)
            {
                int gain = (int)Math.Round(p.Weekly / 7.0 * flow);
                if (gain < 1) gain = 1;
                p.Cash = Math.Min(p.Ceiling, p.Cash + gain);
            }
        }

        /// Take what you can. Never more than is there, ever.
        public Payment Take(string id, int wanted, int day, string name = null)
        {
            var p = For(id, name);
            if (wanted <= 0) return new Payment { Paid = 0, Short = 0 };

            int paid = Math.Min(p.Cash, wanted);
            p.Cash -= paid;
            var result = new Payment
            {
                Paid = paid,
                Short = wanted - paid,
                Emptied = p.Cash == 0 && paid > 0,
            };

            if (result.Emptied || paid == 0)
            {
                p.LastEmptiedDay = day;
                p.TimesEmptied++;
            }

            if (paid == 0)
                result.Line = $"{p.Name} turns the drawer round so you can see into it. There is nothing in it.";
            else if (result.Short > 0)
                result.Line = $"{p.Name} counts out everything there is and it comes to £{paid}. " +
                              "You can see there is no more, because they wanted you to see it.";
            return result;
        }

        /// Money the player hands somebody — a bribe, a payoff, a generous cut.
        ///
        /// It goes INTO their drawer rather than out of the world. That is the
        /// same rule borrowing follows and it matters for the same reason: money
        /// that vanishes when spent makes the district's economy a fiction the
        /// moment the player participates in it. Bribe Rocco two hundred and
        /// Rocco has two hundred — and if you come collecting from him next
        /// week, he can pay you with it.
        ///
        /// A windfall is allowed to push somebody past their ceiling, because
        /// the ceiling is what they would keep to hand in the ordinary way and
        /// this is not ordinary. Somebody visibly holding more than their life
        /// explains is the point rather than a rounding error.
        public void Credit(string id, int amount, int day, string name = null, bool windfall = true)
        {
            if (string.IsNullOrEmpty(id) || amount <= 0) return;
            var p = For(id, name);
            p.Cash += amount;
            if (!windfall) { p.Cash = Math.Min(p.Cash, p.Ceiling); return; }
            p.Windfall += amount;
            p.LastWindfallDay = day;
        }

        /// Is this person carrying money their life does not explain? The
        /// threshold is their own weekly turnover: a docker holding a week's
        /// wages in cash is unremarkable, and holding four is a question.
        public bool CarryingUnexplained(string id)
        {
            var p = Of(id);
            return p != null && p.Windfall > p.Weekly;
        }

        /// Overnight, somebody who was emptied and still owes goes to whoever
        /// they have. The money MOVES rather than appearing — the patron's purse
        /// is lighter by exactly what the debtor's is heavier by — and a favour
        /// is recorded, because that is the part that costs.
        ///
        /// Returns the patron's id if they went, null if they had nowhere to go.
        public string Borrow(string debtorId, int need, int day)
        {
            var d = Of(debtorId);
            if (d == null || need <= 0 || d.PatronId == null) return null;
            if (d.LastBorrowedDay == day) return null;         // once a night
            var patron = Of(d.PatronId);
            if (patron == null || patron.Cash <= 0) return null;

            // Nobody lends their last coin, and nobody lends more than the ask.
            int spare = Math.Max(0, patron.Cash - patron.Weekly / 7);
            int lent = Math.Min(spare, need);
            if (lent <= 0) return null;

            patron.Cash -= lent;
            d.Cash += lent;
            d.LastBorrowedDay = day;
            _favours.Add(new Favour
            {
                DebtorId = debtorId, PatronId = d.PatronId, Amount = lent, Day = day,
            });
            return d.PatronId;
        }

        /// Everyone who owes somebody else, for the Director and for the ledger.
        public List<Favour> Owed(string patronId)
        {
            var list = new List<Favour>();
            foreach (var f in _favours)
                if (!f.Settled && f.PatronId == patronId) list.Add(f);
            return list;
        }

        public void Settle(Favour f) { if (f != null) f.Settled = true; }

        /// The district's loose cash, as a share of what it would hold if every
        /// purse were full. A legibility aid for the DEVELOPER only — this is an
        /// F1 number, never a player-facing one.
        public double Liquidity()
        {
            long cash = 0, ceiling = 0;
            foreach (var p in _purses.Values) { cash += p.Cash; ceiling += p.Ceiling; }
            return ceiling == 0 ? 1.0 : (double)cash / ceiling;
        }

        // ---- persistence ----

        public Dictionary<string, object> Capture()
        {
            var purses = new List<object>();
            foreach (var p in _purses.Values)
                purses.Add(new Dictionary<string, object>
                {
                    { "id", p.OwnerId }, { "name", p.Name }, { "cash", p.Cash },
                    { "weekly", p.Weekly }, { "ceiling", p.Ceiling },
                    { "patron", p.PatronId ?? "" },
                    { "windfall", p.Windfall }, { "windfallDay", p.LastWindfallDay },
                    { "emptiedDay", p.LastEmptiedDay }, { "timesEmptied", p.TimesEmptied },
                    { "borrowedDay", p.LastBorrowedDay },
                });
            var favours = new List<object>();
            foreach (var f in _favours)
                favours.Add(new Dictionary<string, object>
                {
                    { "debtor", f.DebtorId }, { "patron", f.PatronId },
                    { "amount", f.Amount }, { "day", f.Day }, { "settled", f.Settled },
                });
            return new Dictionary<string, object> { { "purses", purses }, { "favours", favours } };
        }

        public void Restore(Dictionary<string, object> data)
        {
            if (data == null) return;
            var plist = MiniJson.GetList(data, "purses");
            if (plist != null)
            {
                _purses.Clear();
                foreach (var raw in plist)
                {
                    var o = MiniJson.AsObject(raw);
                    if (o == null) continue;
                    var id = MiniJson.GetString(o, "id");
                    if (string.IsNullOrEmpty(id)) continue;
                    var patron = MiniJson.GetString(o, "patron");
                    Add(new Purse
                    {
                        OwnerId = id,
                        Name = MiniJson.GetString(o, "name"),
                        Cash = MiniJson.GetInt(o, "cash"),
                        Weekly = MiniJson.GetInt(o, "weekly"),
                        Ceiling = MiniJson.GetInt(o, "ceiling"),
                        PatronId = string.IsNullOrEmpty(patron) ? null : patron,
                        LastEmptiedDay = MiniJson.GetInt(o, "emptiedDay"),
                        TimesEmptied = MiniJson.GetInt(o, "timesEmptied"),
                        LastBorrowedDay = MiniJson.GetInt(o, "borrowedDay"),
                        Windfall = MiniJson.GetInt(o, "windfall"),
                        LastWindfallDay = MiniJson.GetInt(o, "windfallDay"),
                    });
                }
            }
            var flist = MiniJson.GetList(data, "favours");
            if (flist != null)
            {
                _favours.Clear();
                foreach (var raw in flist)
                {
                    var o = MiniJson.AsObject(raw);
                    if (o == null) continue;
                    _favours.Add(new Favour
                    {
                        DebtorId = MiniJson.GetString(o, "debtor"),
                        PatronId = MiniJson.GetString(o, "patron"),
                        Amount = MiniJson.GetInt(o, "amount"),
                        Day = MiniJson.GetInt(o, "day"),
                        Settled = o.TryGetValue("settled", out var st) && st is bool sb && sb,
                    });
                }
            }
        }
    }
}
