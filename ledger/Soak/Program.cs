using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Ledger.Core;

namespace Ledger.Soak
{
    /// LAYER 4, TIME: the other half. What the world does after a very long
    /// time, and whether it does the same thing twice.
    ///
    ///     dotnet run -c Release --project ledger/Soak
    ///     dotnet run -c Release --project ledger/Soak -- --days 2000 --seed 3
    ///
    /// WHAT THIS IS NOT. `BalanceLab` already drives the real Core day loop for
    /// four hundred weeks per policy, and it is not this: it measures BALANCE —
    /// fate tables, cash curves, whether a strategy dominates. It asks whether
    /// the numbers are GOOD. This asks whether they are NUMBERS.
    ///
    /// THREE QUESTIONS, and the roadmap names the reason for all three as "a
    /// bug that is currently unreproducible":
    ///
    ///   1. DETERMINISM. Same seed, same world, twice — do the two runs agree
    ///      day by day? A save file is a promise that the world can be put back
    ///      the way it was, and hidden nondeterminism (an unseeded RNG, an
    ///      iteration order that depends on hash layout, a clock read) breaks
    ///      that promise silently and only for some players. This names the
    ///      first day the two runs diverge, which is the difference between a
    ///      bug report and a bug.
    ///
    ///   2. INVARIANTS, every day rather than at the end. NaN, infinity, a
    ///      negative purse, a suspicion outside 0..1. `SaveChaos` found five of
    ///      these reachable through a corrupt file; this asks whether ordinary
    ///      play reaches them on its own after long enough. A NaN that appears
    ///      on day 300 and is checked for on day 500 has had two hundred days
    ///      to spread.
    ///
    ///   3. GROWTH, REPORTED AND NOT GATED. Rumours, memories, reasons trails,
    ///      debts. Something that grows without bound is a leak, and on a long
    ///      enough save it is the leak that ends the playthrough — but NOBODY
    ///      HAS MEASURED what these do over five hundred days, so this prints
    ///      the series and the per-day slope and gates on none of it. Rule 2:
    ///      make the run print the number, look, and set the threshold from
    ///      evidence. Inventing a rumour ceiling here would be `nightNotDarker`
    ///      failing at 0.136 against 0.135, again.
    static class Program
    {
        static int _checks, _failed;
        static readonly List<string> _findings = new List<string>();

        static int Main(string[] args)
        {
            System.Globalization.CultureInfo.CurrentCulture =
                System.Globalization.CultureInfo.InvariantCulture;
            int days = ArgInt(args, "--days", 500);
            int seed = ArgInt(args, "--seed", 1);

            Console.WriteLine($"Soak — {days} in-game days, seed {seed}");

            var a = Run(days, seed);
            var b = Run(days, seed);

            // ---- 1. determinism -------------------------------------------
            int diverged = -1;
            for (int i = 0; i < Math.Min(a.digests.Count, b.digests.Count); i++)
                if (a.digests[i] != b.digests[i]) { diverged = i; break; }
            if (diverged < 0 && a.digests.Count != b.digests.Count) diverged = Math.Min(a.digests.Count, b.digests.Count);

            Require(a.digests.Count == b.digests.Count,
                    $"two runs of seed {seed} last the same number of days "
                    + $"({a.digests.Count} vs {b.digests.Count})");
            Require(diverged < 0,
                    diverged < 0
                        ? "same seed, same world"
                        : $"same seed, same world — DIVERGED on day {diverged + 1} "
                          + $"({Snip(a.states.ElementAtOrDefault(diverged))} vs "
                          + $"{Snip(b.states.ElementAtOrDefault(diverged))})");

            // ---- 2. invariants --------------------------------------------
            Require(a.brokenOn < 0,
                    a.brokenOn < 0
                        ? "no invariant broke in any day"
                        : $"no invariant broke — day {a.brokenOn}: {a.brokenWhy}");

            // ---- 3. growth, reported --------------------------------------
            Console.WriteLine($"  ran {a.digests.Count} day(s), verdict {a.verdict}");
            Console.WriteLine("  growth (REPORTED, NOT GATED — no ceiling has been measured):");
            foreach (var (label, series) in a.growth)
            {
                var shown = Sample(series, 8);
                double slope = series.Count > 1
                    ? (series[series.Count - 1] - series[0]) / (double)(series.Count - 1)
                    : 0.0;
                Console.WriteLine($"    {label,-16} [{string.Join(" ", shown)}]  "
                                  + $"first={series[0]} last={series[series.Count - 1]} "
                                  + $"per-day={slope:+0.000;-0.000;0.000}");
            }

            Console.WriteLine();
            if (_failed == 0)
            {
                Console.WriteLine($"soak ok — all {_checks} checks passed");
                return 0;
            }
            Console.WriteLine($"soak FAILED — {_failed} of {_checks} checks");
            foreach (var f in _findings) Console.WriteLine("  FAILED " + f);
            return 1;
        }

        static void Require(bool ok, string what)
        {
            _checks++;
            if (ok) return;
            _failed++;
            _findings.Add(what);
        }

        class Outcome
        {
            public readonly List<uint> digests = new List<uint>();
            public readonly List<string> states = new List<string>();
            public readonly List<(string label, List<int> series)> growth =
                new List<(string, List<int>)>();
            public int brokenOn = -1;
            public string brokenWhy = "";
            public string verdict = "?";
        }

        /// One full run of the real Core systems, hour by hour.
        ///
        /// The shape is `BalanceLab`'s open-city loop, because that is the loop
        /// the game actually runs and a soak of a loop nobody plays is a soak of
        /// nothing. What differs is what happens at the end of each day: the lab
        /// records money, this records a digest and checks the world is still
        /// made of numbers.
        ///
        /// THE ROSTER IS A COPY AND THE ECONOMY IS NOT. Seven gossipers and
        /// three purses are restated here rather than shared with the lab, and
        /// that is a deliberate line: the properties under test are properties
        /// of the SYSTEMS, so any representative street exercises them. The
        /// economy is different — it is a shipped table of suppliers and prices
        /// that the game reads, so `EconomySetup` is compiled in rather than
        /// approximated, exactly as the lab does it.
        static Outcome Run(int days, int seed)
        {
            var o = new Outcome();
            var rng = new Random(seed);
            var camp = new Campaign();
            var mill = BuildStreet();
            var wallet = new Wallet(250);
            var economy = Ledger.Game.EconomySetup.Build();
            var purses = new PurseBook();
            purses.Add(new Purse { OwnerId = "Sam", Name = "Sam", Weekly = 60, Ceiling = 95, Cash = 45 });
            purses.Add(new Purse { OwnerId = "Rocco", Name = "Rocco", Weekly = 140, Ceiling = 260, Cash = 180 });
            purses.Add(new Purse { OwnerId = "Donna", Name = "Donna", Weekly = 220, Ceiling = 520, Cash = 380 });

            mill.Witness("Rocco", new Fact("player", "location_d2_evening", "warehouse"),
                         "the new owner was at the old warehouse the night of the fire",
                         true, new GameTime(1, 9, 0));

            var rumours = new List<int>();
            var reasons = new List<int>();
            var leads = new List<int>();
            var purseCash = new List<int>();

            var now = new GameTime(1, 9, 0);
            int lastClosedDay = 1;
            while (now.Day <= days)
            {
                now = now.AddMinutes(60);
                mill.Age(now);
                mill.Tick(now, (x, y) => rng.NextDouble() < 0.10);

                if (now.Hour < 8 || now.Day <= lastClosedDay) continue;
                lastClosedDay = now.Day;

                double heat = mill.DayCircleHeat();
                int takings = camp.CloseDay(heat);
                wallet.EarnClean((int)Math.Round(takings * economy.FactorFor("bar")));
                wallet.Launder();
                if (camp.Verdict == Verdict.WonWeek) camp.EnterOpenMode();
                economy.DailyTick(now, wallet, 0, 0, heat);
                purses.DailyTick(now.Day, economy.Prosperity);

                // A NEW RUMOUR NOW AND THEN, because a street where nothing
                // ever happens again is a street whose growth curves are flat
                // by construction — and a flat curve from a dead world is the
                // most convincing wrong answer this tool could give.
                if (rng.NextDouble() < 0.25)
                    mill.Witness("Rocco", new Fact("player", "seen_d" + now.Day, "the yard"),
                                 "somebody was in the yard again", true, now);

                string state = State(now, wallet, camp, economy, mill, purses);
                o.states.Add(state);
                o.digests.Add(VoiceBank.Hash(state));

                if (o.brokenOn < 0)
                {
                    var why = Broken(now, wallet, camp, economy, mill, purses);
                    if (why != null) { o.brokenOn = now.Day; o.brokenWhy = why; }
                }

                rumours.Add(mill.Agents.Sum(g => g.Rumors.Count));
                reasons.Add(mill.Agents.Sum(g => g.Suspicion.Reasons.Count));
                leads.Add(mill.Leads("player").Count());
                purseCash.Add(purses.All.Sum(p => p.Cash));
            }

            o.verdict = camp.Verdict.ToString();
            o.growth.Add(("rumours", rumours));
            o.growth.Add(("suspicion notes", reasons));
            o.growth.Add(("leads on player", leads));
            o.growth.Add(("purse cash", purseCash));
            return o;
        }

        /// Everything that must be identical between two runs of one seed,
        /// as text. Text rather than a struct because when it differs the
        /// DIFFERENCE is the finding, and a hash alone cannot be read.
        static string State(GameTime now, Wallet w, Campaign c, Economy e,
                            GossipMill m, PurseBook p)
        {
            var sb = new StringBuilder();
            sb.Append(now.Day).Append('|').Append(w.Clean).Append(',').Append(w.Dirty)
              .Append('|').Append(c.OutfitPatience.ToString("0.000000")).Append(',')
              .Append(c.JobsDone).Append(',').Append(c.JobsMissed).Append(',').Append(c.Verdict)
              .Append('|').Append(e.Prosperity.ToString("0.000000")).Append(',')
              .Append(e.PriceLevel.ToString("0.000000")).Append('|');
            // ORDERED BY ID, and that is not tidiness either — enumerating a
            // Dictionary in insertion order happens to be stable in .NET today
            // and is not promised anywhere. A digest that depends on it would
            // report a divergence that is really the runtime's, which is the
            // instrument lying in the most convincing possible way.
            foreach (var g in m.Agents.OrderBy(x => x.Id, StringComparer.Ordinal))
                sb.Append(g.Id).Append(':').Append(g.Rumors.Count).Append(',')
                  .Append(g.Loyalty.ToString("0.0000")).Append(',')
                  .Append(g.Suspicion.Value.ToString("0.0000")).Append(';');
            sb.Append('|');
            foreach (var q in p.All.OrderBy(x => x.OwnerId, StringComparer.Ordinal))
                sb.Append(q.OwnerId).Append(':').Append(q.Cash).Append(';');
            return sb.ToString();
        }

        /// The first invariant this world breaks, or null.
        ///
        /// Every clause is a thing the rest of the game reads without checking.
        /// None of them is a threshold — they are the ranges the types
        /// themselves already promise, which is why they can be asserted
        /// without measuring anything first.
        static string Broken(GameTime now, Wallet w, Campaign c, Economy e,
                             GossipMill m, PurseBook p)
        {
            if (w.Clean < 0) return $"wallet.Clean={w.Clean}";
            if (w.Dirty < 0) return $"wallet.Dirty={w.Dirty}";
            if (Bad(c.OutfitPatience)) return $"patience={c.OutfitPatience}";
            if (c.OutfitPatience < 0.0 || c.OutfitPatience > 1.0)
                return $"patience={c.OutfitPatience} outside 0..1";
            if (c.JobsDone < 0 || c.JobsMissed < 0)
                return $"jobs={c.JobsDone}/{c.JobsMissed}";
            if (Bad(e.Prosperity)) return $"prosperity={e.Prosperity}";
            if (Bad(e.PriceLevel)) return $"priceLevel={e.PriceLevel}";
            if (e.PriceLevel <= 0.0) return $"priceLevel={e.PriceLevel} (a price cannot be free)";
            foreach (var g in m.Agents)
            {
                if (Bad(g.Loyalty)) return $"{g.Id}.Loyalty={g.Loyalty}";
                if (Bad(g.Suspicion.Value)) return $"{g.Id}.Suspicion={g.Suspicion.Value}";
                if (g.Suspicion.Value < 0.0 || g.Suspicion.Value > 1.0)
                    return $"{g.Id}.Suspicion={g.Suspicion.Value} outside 0..1";
                foreach (var r in g.Rumors)
                    if (Bad(r.Confidence)) return $"{g.Id} holds a rumour with confidence {r.Confidence}";
            }
            foreach (var q in p.All)
                if (q.Cash < 0) return $"{q.OwnerId}'s purse holds {q.Cash}";
            return null;
        }

        static bool Bad(double d) => double.IsNaN(d) || double.IsInfinity(d);

        /// Same seven-person street the lab and the game wire up.
        static GossipMill BuildStreet()
        {
            var graph = new SocialGraph();
            graph.Link("Rocco", "Lena", 0.7);
            graph.Link("Rocco", "Sam", 0.8);
            graph.Link("Sam", "Lena", 0.6);
            graph.Link("Ada", "Lena", 0.6);
            graph.Link("Ada", "Sam", 0.5);
            graph.Link("Joey", "Rocco", 0.6);
            graph.Link("Joey", "Sam", 0.3);
            graph.Link("Marla", "Ada", 0.5);
            graph.Link("Marla", "Sam", 0.4);
            graph.Link("Victor", "Lena", 0.4);
            graph.Link("Victor", "Sam", 0.5);
            var mill = new GossipMill(graph);
            mill.Add(Brain("Lena", "day", 0.25, 0.75, 0.5));
            mill.Add(Brain("Rocco", "night", 0.6, 0.5, 0.6));
            mill.Add(Brain("Ada", "day", 0.15, 0.8, 0.4));
            mill.Add(Brain("Sam", "both", 0.85, 0.25, 0.3));
            mill.Add(Brain("Joey", "night", 0.7, 0.45, 0.35));
            mill.Add(Brain("Marla", "day", 0.55, 0.35, 0.4));
            mill.Add(Brain("Victor", "day", 0.7, 0.4, 0.4));
            return mill;
        }

        static Gossiper Brain(string name, string circle, double greed, double nerve, double loyalty) =>
            new Gossiper(name, name, new MemoryStore(name.ToLowerInvariant()), new KnowledgeBase(),
                         new SuspicionTracker(), circle, greed, nerve, loyalty);

        /// Evenly spaced readings including both ends — the shape of the curve
        /// rather than its first eight days, which on a growth question is the
        /// only part that answers anything.
        static List<int> Sample(List<int> series, int n)
        {
            var outp = new List<int>();
            if (series.Count == 0) return outp;
            if (series.Count <= n) return new List<int>(series);
            for (int i = 0; i < n; i++)
                outp.Add(series[(int)((long)i * (series.Count - 1) / (n - 1))]);
            return outp;
        }

        static string Snip(string s) =>
            s == null ? "(none)" : s.Length <= 110 ? s : s.Substring(0, 110) + "…";

        static int ArgInt(string[] args, string name, int fallback)
        {
            for (int i = 0; i + 1 < args.Length; i++)
                if (args[i] == name && int.TryParse(args[i + 1], out var v)) return v;
            return fallback;
        }
    }
}
