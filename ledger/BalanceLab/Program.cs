using System;
using System.Collections.Generic;
using System.Linq;
using Ledger.Core;

namespace Ledger.BalanceLab
{
    /// Headless Monte-Carlo balance lab: scripted player policies each play many
    /// full weeks against the REAL Campaign + GossipMill code (no Unity, no LLM).
    /// Co-location is approximated by circle-overlap probabilities; night-job
    /// witnesses by a per-job chance. Prints a fate table per policy so knob
    /// changes can be judged against data instead of vibes.
    static class Program
    {
        // World approximation knobs (things the 3D world decides emergently).
        const double TalkChancePerHourSameCircle = 0.10; // tied pair, both "active"
        const double WitnessChance = 0.5;                // someone saw the night drop
        const int WeeksPerPolicy = 400;

        static void Main(string[] args)
        {
            int weeks = args.Length > 0 && int.TryParse(args[0], out var w) ? w : WeeksPerPolicy;
            var policies = new (string name, Policy policy)[]
            {
                ("do-nothing",   new Policy()), // does all jobs, ignores all talk
                ("job-skipper",  new Policy { SkipJobs = true }),
                ("briber",       new Policy { Dc = DcStyle.Bribe }),
                ("intimidator",  new Policy { Dc = DcStyle.Intimidate }),
                ("discrediter",  new Policy { Dc = DcStyle.Discredit }),
                ("smart",        new Policy { Dc = DcStyle.Smart }), // pick the verb per target
                ("beat-keeper",  new Policy { Dc = DcStyle.Smart, KeepBeats = true }),
                ("hook-user",    new Policy { UseHooks = true }),
                ("collector",    new Policy { CollectDebts = true }),
                // Roadmap M13: the same collector, but the people they are
                // collecting from can only pay what they actually have. If this
                // line is dramatically worse than the one above, purses have
                // nerfed a strategy rather than deepened it.
                ("collector+purse", new Policy { CollectDebts = true, Purses = true }),
                // The case that actually exercises M13. In the plain collector
                // rows Sam's loyalty is 0.3, so he refuses whatever is in his
                // pocket and the purse never gets opened — a true result and an
                // uninformative one. These two model a player who did the
                // favours FIRST and is now collecting from people who are
                // willing: without purses, willing means paid in full on the
                // spot; with them, willing means paying what is in the drawer.
                ("warm-collect",     new Policy { CollectDebts = true, WarmFirst = true }),
                ("warm-collect+purse", new Policy { CollectDebts = true, WarmFirst = true, Purses = true }),
            };

            Console.WriteLine($"weeks/policy={weeks}  talk/h={TalkChancePerHourSameCircle}  witness={WitnessChance}");
            Console.WriteLine($"{"policy",-16} {"win%",5} {"exposed%",8} {"castout%",8} {"avg$",6} {"avgHeat",7} {"avgDC$",6} {"got$",5} {"visits",6} {"part",5}");
            foreach (var (name, policy) in policies)
            {
                var r = RunMany(policy, weeks);
                Console.WriteLine($"{name,-16} {r.winPct,5:0.0} {r.exposedPct,8:0.0} {r.castoutPct,8:0.0} {r.avgCash,6:0} {r.avgPeakHeat,7:0.00} {r.avgDcSpend,6:0} {r.avgCollected,5:0} {r.avgVisits,6:0.0} {r.avgPartials,5:0.0}");
            }

            RunOpenLab(weeks);
            RunEndingLab(weeks);
        }

        enum DcStyle { None, Bribe, Intimidate, Discredit, Smart }

        class Policy
        {
            public bool SkipJobs;
            public DcStyle Dc = DcStyle.None;
            public bool KeepBeats;     // honor Ada d3 / Rocco d5 evenings, missing those drops
            public bool UseHooks;      // leash Rocco with his secret on day 2
            public bool CollectDebts;  // work Marek's book on day 2
            public bool Purses;        // M13: counterparties can only pay what they hold
            public bool WarmFirst;     // the player did the favours before asking for the money
        }

        static (double winPct, double exposedPct, double castoutPct, double avgCash, double avgPeakHeat,
                double avgDcSpend, double avgCollected, double avgVisits, double avgPartials)
            RunMany(Policy policy, int weeks)
        {
            int win = 0, exposed = 0, castout = 0;
            double cashSum = 0, peakHeatSum = 0, dcSum = 0, collectedSum = 0, visitSum = 0, partialSum = 0;
            for (int seed = 0; seed < weeks; seed++)
            {
                var o = RunWeek(policy, new Random(seed * 7919 + 13));
                if (o.verdict == Verdict.WonWeek) win++;
                else if (o.verdict == Verdict.LostExposed) exposed++;
                else if (o.verdict == Verdict.LostCastOut) castout++;
                cashSum += o.cash;
                peakHeatSum += o.peakHeat;
                dcSum += o.dcSpend;
                collectedSum += o.collected;
                visitSum += o.visits;
                partialSum += o.partials;
            }
            return (100.0 * win / weeks, 100.0 * exposed / weeks, 100.0 * castout / weeks,
                cashSum / weeks, peakHeatSum / weeks, dcSum / weeks, collectedSum / weeks,
                visitSum / weeks, partialSum / weeks);
        }

        static (Verdict verdict, int cash, double peakHeat, int dcSpend, int collected, int visits, int partials)
            RunWeek(Policy policy, Random rng)
        {
            var camp = new Campaign();
            var mill = BuildStreet();
            var wallet = new Wallet(250);
            int dcSpend = 0;
            double peakHeat = 0;

            // The founding secret, same as in-game: Rocco saw something.
            mill.Witness("Rocco", new Fact("player", "location_d2_evening", "warehouse"),
                "the new owner was at the old warehouse the night of the fire", true, new GameTime(1, 9, 0));

            var now = new GameTime(1, 9, 0);
            int lastClosedDay = 1, jobPostedDay = -1;
            bool jobOpen = false, actedToday = false, specialDone = false;
            int lastActDay = 0;
            var debts = new List<Debtor>
            {
                new Debtor { Id = "Sam", Name = "Sam", Amount = 120, Note = "stock" },
                new Debtor { Id = "Rocco", Name = "Rocco", Amount = 60, Note = "door" },
            };
            // The same means the game authors (PurseSetup): Sam is a runner
            // with an uncle, Rocco has had a good few years at the door.
            PurseBook purses = null;
            if (policy.Purses)
            {
                purses = new PurseBook();
                purses.Add(new Purse { OwnerId = "Sam", Name = "Sam", Weekly = 60, Ceiling = 95, Cash = 45, PatronId = "Danica" });
                purses.Add(new Purse { OwnerId = "Rocco", Name = "Rocco", Weekly = 140, Ceiling = 260, Cash = 180 });
                purses.Add(new Purse { OwnerId = "Danica", Name = "Danica", Weekly = 220, Ceiling = 520, Cash = 380 });
            }
            int collected = 0, visits = 0, partials = 0;
            if (policy.WarmFirst)
                foreach (var d in debts)
                {
                    var g = mill.Get(d.Id);
                    if (g != null) g.Loyalty = Math.Max(g.Loyalty, 0.75);
                }

            while (camp.Verdict == Verdict.Ongoing && !(now.Day > 8))
            {
                now = now.AddMinutes(60);
                mill.Age(now);

                // Hourly mingling: tied pairs whose circles are awake talk sometimes.
                mill.Tick(now, (a, b) => BothActive(a, b, now.Hour) && rng.NextDouble() < TalkChancePerHourSameCircle);

                double heat = mill.DayCircleHeat();
                if (heat > peakHeat) peakHeat = heat;

                // Morning close.
                if (now.Hour >= 8 && now.Day > lastClosedDay)
                {
                    lastClosedDay = now.Day;
                    wallet.EarnClean(camp.CloseDay(heat));
                    wallet.Launder();
                    actedToday = false;
                    if (purses != null)
                    {
                        // The week has no Economy instance; prosperity sits at
                        // the ordinary half, which is the honest assumption for
                        // a campaign that is not yet running rackets.
                        purses.DailyTick(now.Day, 0.5);
                        foreach (var d in debts)
                            if (d.Outstanding && purses.Of(d.Id)?.LastEmptiedDay >= 0)
                                purses.Borrow(d.Id, d.Amount, now.Day);
                    }
                }

                // One damage-control visit per day, around noon, if anyone is talking.
                if (policy.Dc != DcStyle.None && now.Hour >= 12 && now.Day > lastActDay && !actedToday)
                {
                    var lead = mill.Leads("player").FirstOrDefault();
                    if (lead != null && lead.Confidence >= 0.25)
                    {
                        lastActDay = now.Day;
                        actedToday = true;
                        dcSpend += Act(policy.Dc, mill, lead, wallet, now);
                    }
                }

                // Day-2 noon one-shots: leverage and the debt book.
                if (!specialDone && now.Day == 2 && now.Hour >= 12)
                {
                    specialDone = true;
                    if (policy.UseHooks)
                    {
                        var s = new Secret { Id = "skim", OwnerId = "Rocco", Kind = SecretKind.Criminal, Summary = "the skim." };
                        s.Learn("Lena", now);
                        mill.UseHook("Rocco", s, now);
                    }
                    if (policy.CollectDebts && purses == null && now.Day == 2)
                        foreach (var d in debts)
                        {
                            int had = wallet.Clean;
                            var oc = d.Collect(mill.Get(d.Id), wallet, mill, now);
                            if (oc == CollectOutcome.Paid || oc == CollectOutcome.PaidPart) visits++;
                            collected += wallet.Clean - had;
                        }
                }

                // With purses, one visit is not a collection: a man who turns
                // over sixty a week cannot clear a hundred and twenty because
                // you asked. So the collector goes back, which is exactly the
                // behaviour the system is meant to produce.
                if (policy.CollectDebts && purses != null && now.Day >= 2 && now.Hour == 12)
                    foreach (var d in debts)
                    {
                        int had = wallet.Clean;
                        var oc = d.Collect(mill.Get(d.Id), wallet, mill, now, purses);
                        if (oc == CollectOutcome.Paid || oc == CollectOutcome.PaidPart) visits++;
                        if (oc == CollectOutcome.PaidPart) partials++;
                        collected += wallet.Clean - had;
                    }

                // Night job window.
                if (now.Hour >= 22 && jobPostedDay != now.Day) { jobPostedDay = now.Day; jobOpen = true; }
                if (jobOpen && now.Hour >= 23) // resolve an hour into the window
                {
                    jobOpen = false;
                    bool beatNight = policy.KeepBeats && (now.Day == 3 || now.Day == 5);
                    if (beatNight)
                    {
                        camp.JobMissed(); // the evening went to a person instead
                        var host = mill.Get(now.Day == 3 ? "Ada" : "Rocco");
                        if (host != null)
                        {
                            host.Loyalty = Math.Clamp(host.Loyalty + 0.2, 0, 1);
                            host.Suspicion.Lower(0.1, "the new owner made time");
                        }
                    }
                    else if (policy.SkipJobs) camp.JobMissed();
                    else
                    {
                        camp.JobDone();
                        wallet.EarnDirty(camp.JobPay);
                        if (rng.NextDouble() < WitnessChance)
                        {
                            string who = rng.NextDouble() < 0.6 ? "Rocco" : "Sam";
                            mill.Witness(who, new Fact("player", $"night_job_d{now.Day}", "seen"),
                                "the new owner was handling a package in the street past midnight", true, now);
                        }
                    }
                }
            }
            return (camp.Verdict, wallet.Total, peakHeat, dcSpend, collected, visits, partials);
        }

        /// One damage-control move against the strongest lead. Returns dollars spent.
        static int Act(DcStyle style, GossipMill mill, Lead lead, Wallet wallet, GameTime now)
        {
            var g = mill.Get(lead.HolderId);
            if (style == DcStyle.Smart)
                style = g.Greed >= mill.BribeGreedFloor ? DcStyle.Bribe
                    : g.Nerve <= mill.IntimidateNerveCeiling ? DcStyle.Intimidate
                    : DcStyle.Discredit;

            switch (style)
            {
                case DcStyle.Bribe:
                    int price = (int)Math.Ceiling(mill.BribePrice(lead.HolderId, lead.TopicKey));
                    if (wallet.Total < price) { mill.Discredit(lead.TopicKey, null, now); return 0; }
                    var r = mill.Bribe(lead.HolderId, lead.TopicKey, price, now);
                    if (r.Outcome == DcOutcome.Contained) { wallet.Spend(price, true); return price; }
                    return 0;
                case DcStyle.Intimidate:
                    mill.Intimidate(lead.HolderId, lead.TopicKey, now);
                    return 0;
                default:
                    mill.Discredit(lead.TopicKey, null, now);
                    return 0;
            }
        }

        // ==== the open city (days 1-21): does the empire loop hold? ====

        enum OpenPlan { Control, Aggressive, Cautious }

        static void RunOpenLab(int runs)
        {
            Console.WriteLine("\n== open city (21 days; week won -> empire; smart DC throughout) ==");
            Console.WriteLine($"{"plan",-12} {"reach%",7} {"cash",7} {"falls",6} {"cutoff%",8} {"stage",6} {"rounds$",8} {"broke%",7}" +
                              $" {"street",8} {"prices",7} {"nosupp%",8} {"drawers$",8}");
            foreach (var plan in new[] { OpenPlan.Control, OpenPlan.Aggressive, OpenPlan.Cautious })
            {
                int reached = 0, cutoff = 0, broke = 0, noSupply = 0;
                double cash = 0, falls = 0, stage = 0, rounds = 0, prosperity = 0, prices = 0, drawers = 0;
                for (int seed = 0; seed < runs; seed++)
                {
                    var o = RunOpenCampaign(plan, new Random(seed * 104729 + 7));
                    if (!o.reachedOpen) continue;
                    reached++;
                    cash += o.endCash; falls += o.falls; stage += o.rivalStage; rounds += o.racketIncome;
                    prosperity += o.prosperity; prices += o.priceLevel; drawers += o.purseTotal;
                    if (o.cutOff) cutoff++;
                    if (o.endCash < 50) broke++;
                    if (o.supplyLost) noSupply++;
                }
                int n = Math.Max(1, reached);
                Console.WriteLine($"{plan,-12} {100.0 * reached / runs,6:0.0}% {cash / n,7:0} {falls / n,6:0.00} " +
                                  $"{100.0 * cutoff / n,7:0.0}% {stage / n,6:0.0} {rounds / n,8:0} {100.0 * broke / n,6:0.0}%" +
                                  $" {prosperity / n,8:0.00} {prices / n,7:0.00} {100.0 * noSupply / n,7:0.0}% {drawers / n,8:0}");
            }
            Console.WriteLine("  street 0.00-1.00 (0.55 = ordinary) · prices 1.00 = ordinary · nosupp% = a supplier walked · drawers$ = six days of refill after a day-15 sweep — the street's prosperity, read out of pockets");
        }

        static (bool reachedOpen, int endCash, int falls, bool cutOff, int rivalStage, int racketIncome,
                double prosperity, double priceLevel, bool supplyLost, int purseTotal, LedgerState books)
            RunOpenCampaign(OpenPlan plan, Random rng)
        {
            var camp = new Campaign();
            var mill = BuildOpenStreet();
            var wallet = new Wallet(250);
            var empire = BuildEmpire();
            // Roadmap: "the lab does not test a squeezed street's effect on
            // purses" — week mode pins prosperity by construction. Out here
            // prosperity MOVES, so the drawers empty for real.
            var openPurses = new PurseBook();
            openPurses.Add(new Purse { OwnerId = "Sam", Name = "Sam", Weekly = 60, Ceiling = 95, Cash = 45, PatronId = "Danica" });
            openPurses.Add(new Purse { OwnerId = "Rocco", Name = "Rocco", Weekly = 140, Ceiling = 260, Cash = 180 });
            openPurses.Add(new Purse { OwnerId = "Danica", Name = "Danica", Weekly = 220, Ceiling = 520, Cash = 380 });
            // Every world gets its own empire roll stream — the lab's whole
            // point is variance, and a constant salt was collapsing it.
            empire.Seed = rng.Next(1, 1 << 22);
            // Roadmap M7 gates the economy on this lab: a district that inflates
            // away or collapses to nothing is a failed design, not a hard mode.
            var economy = Ledger.Game.EconomySetup.Build();
            mill.Witness("Rocco", new Fact("player", "location_d2_evening", "warehouse"),
                "the new owner was at the old warehouse the night of the fire", true, new GameTime(1, 9, 0));

            var now = new GameTime(1, 9, 0);
            int lastClosedDay = 1, jobPostedDay = -1, lastActDay = 0;
            bool jobOpen = false;
            bool swept = false;   // the day-15 purse sweep, latched
            int takingsToDate = 0;   // Act III reads this: what a bar could plausibly have washed

            while (now.Day <= 21)
            {
                now = now.AddMinutes(60);
                mill.Age(now);
                mill.Tick(now, (a, b) => BothActive(a, b, now.Hour) && rng.NextDouble() < TalkChancePerHourSameCircle);
                double heat = mill.DayCircleHeat();

                if (now.Hour >= 8 && now.Day > lastClosedDay)
                {
                    lastClosedDay = now.Day;
                    int takings = camp.CloseDay(heat);
                    takings = (int)Math.Round(takings * economy.FactorFor("bar"));
                    foreach (var b in empire.Businesses)
                        if (b.Owned) takings += (int)Math.Round(b.CleanIncomePerDay * economy.FactorFor(b.Id)
                            * empire.FrontFactor * Math.Max(0.0, 1.0 - 0.85 * heat));
                    wallet.EarnClean(takings);
                    takingsToDate += takings;
                    wallet.LaunderPerDay = 120 + empire.OwnedLaunderCapacity;
                    wallet.Launder();
                    if (camp.Verdict == Verdict.WonWeek) camp.EnterOpenMode();
                    if (camp.Verdict != Verdict.Ongoing) break; // lost the week itself
                    int racketToday = 0, wagesToday = 0;
                    if (camp.OpenMode)
                    {
                        foreach (var ev in empire.DailyTick(now, wallet, mill, economy.FactorFor(null)))
                            if (ev.Kind == "income") racketToday += ev.Amount;
                        foreach (var c in empire.ActiveCrew)
                            if (c.Assignment != null)
                                wagesToday += c.Cut == "generous" ? 25 : c.Cut == "skim" ? 0 : 10;
                    }
                    economy.DailyTick(now, wallet, racketToday, wagesToday, heat);
                    openPurses.DailyTick(now.Day, economy.Prosperity);
                    // One collection sweep on day 15: without a drain the
                    // ceilings clip everything to the same number (first
                    // measurement literally printed 875 for all three plans —
                    // the ceilings' sum). Six days of REFILL under this
                    // street's prosperity is the coupling, isolated.
                    if (!swept && now.Day >= 15 && now.Hour >= 8)
                    {
                        swept = true;   // >= and a latch: a Fall can jump straight over day 15
                        foreach (var pp in openPurses.All) pp.Cash = 0;
                    }
                    if (camp.OpenMode)
                    {
                        if (camp.FallPending)
                        {
                            // The Fall, as the game runs it: seize, the street knows, 3 days gone.
                            camp.ConsumeFall();
                            wallet.Seize();
                            var didTime = new Fact("player", "did_time", "true");
                            foreach (var a in mill.Agents)
                            {
                                a.Rumors.RemoveAll(r => r.Content.Subject == "player");
                                a.Knowledge.Learn(didTime);   // the record, as the game plants it
                                a.Suspicion.Restore(0.2);
                                a.Loyalty = Math.Clamp(a.Loyalty - 0.15, 0, 1);
                            }
                            now = new GameTime(now.Day + 3, 8, 0);
                            lastClosedDay = now.Day;
                            jobPostedDay = now.Day;
                        }
                    }
                }

                if (now.Hour >= 12 && now.Day > lastActDay)
                {
                    var lead = mill.Leads("player").FirstOrDefault();
                    if (lead != null && lead.Confidence >= 0.25)
                    {
                        lastActDay = now.Day;
                        Act(DcStyle.Smart, mill, lead, wallet, now);
                    }
                }

                if (camp.OpenMode && now.Hour == 10) PlanActions(plan, empire, mill, wallet, now);

                if (now.Hour >= 22 && jobPostedDay != now.Day && !camp.OutfitCutOff) { jobPostedDay = now.Day; jobOpen = true; }
                if (jobOpen && now.Hour >= 23)
                {
                    jobOpen = false;
                    camp.JobDone();
                    wallet.EarnDirty(camp.JobPay);
                    if (rng.NextDouble() < WitnessChance)
                        mill.Witness(rng.NextDouble() < 0.6 ? "Rocco" : "Sam",
                            new Fact("player", $"night_job_d{now.Day}", "seen"),
                            "the new owner was handling a package in the street past midnight", true, now);
                }
            }
            // The world as Act III would find it. Assembled from what the
            // campaign actually did rather than from invented numbers, which is
            // the only way an ending distribution means anything.
            var books = new LedgerState
            {
                BusinessesOwned = empire.Businesses.Count(b => b.Owned),
                RacketsEstablished = empire.Rackets.Count(r => r.Established),
                CrewCount = empire.ActiveCrew.Count(),
                DayCircleRacketHeat = mill.DayCircleHeat(),
                TotalWashed = wallet.TotalWashed,
                TotalRacketIncome = empire.TotalRacketIncome,
                BarTakingsToDate = takingsToDate,
            };
            foreach (var a in mill.Agents)
                if (a.Circle != "night" && a.Loyalty > books.BestDayLifeLoyalty)
                    books.BestDayLifeLoyalty = a.Loyalty;
            books.OsseiCaseAnswerable = mill.StrongestSurvivingPlayerLead() < LedgerState.CaseStandsAt;
            books.PublicRecord = camp.Falls > 0;   // every fall plants the record

            int purseTotal = 0;
            foreach (var pp in openPurses.All) purseTotal += pp.Cash;
            return (camp.OpenMode, wallet.Total, camp.Falls, camp.OutfitCutOff, empire.Rival.Stage,
                empire.TotalRacketIncome, economy.Prosperity, economy.PriceLevel,
                economy.Suppliers.Any(s => s.Refusing), purseTotal, books);
        }

        /// THE ENDING MATRIX, sampled over real worlds (roadmap: Act III).
        ///
        /// The one thing nobody could answer about the endgame: how often does
        /// each ending actually fire? It was known only from unit tests, which
        /// prove that a given world resolves correctly and say nothing about
        /// which worlds a player ends up in.
        ///
        /// So: run the same 21-day campaigns the open lab runs, take the world
        /// each one ends in, and resolve Act III over it three ways — the audit
        /// ignored, the inspector answered every morning, the inspector
        /// stonewalled. Two design claims are on trial here.
        ///
        ///   1. **"Both" must be RARE and earned** (player decision: not
        ///      reachable on a first playthrough). If it shows up in a quarter
        ///      of aggressive runs, it is not rare, it is the default.
        ///   2. **The inspector must matter without deciding everything.** If
        ///      cooperating changes nothing, the verb is decoration. If it
        ///      changes everything, the six days of paperwork have eaten the
        ///      three acts that came before them.
        static void RunEndingLab(int runs)
        {
            Console.WriteLine("\n== the ending matrix (21-day worlds, resolved three ways) ==");
            Console.WriteLine($"{"plan",-12} {"inspector",-11} {"n",4} {"Both",6} {"Kingdom",8} {"Straight",9} {"Burn",6} {"strain",7}");

            foreach (var plan in new[] { OpenPlan.Control, OpenPlan.Aggressive, OpenPlan.Cautious })
            {
                // The fourth row exists because without it the "Both" column is
                // a lie by omission: Both requires the case to have been pointed
                // elsewhere, and the lab bot never does that, so a 0% there
                // would read as "unreachable" when it means "never attempted".
                foreach (var (label, coop, stone, deflected) in new[]
                    { ("ignored", 0, 0, false), ("answered", 5, 0, false),
                      ("stonewalled", 0, 3, false), ("answered+deflect", 5, 0, true) })
                {
                    var tally = new Dictionary<Ending, int>();
                    double strain = 0;
                    int n = 0;
                    for (int seed = 0; seed < runs; seed++)
                    {
                        var o = RunOpenCampaign(plan, new Random(seed * 104729 + 7));
                        if (!o.reachedOpen) continue;
                        n++;
                        var books = o.books;
                        books.Cooperations = coop;
                        books.Stonewalls = stone;
                        // The landscape leg was computed in-world by the run
                        // (surviving lead below testimony grade); her deal ORs in.
                        books.OsseiCaseAnswerable = books.OsseiCaseAnswerable || deflected;
                        strain += ActThreeState.SeenStrain(books);
                        var e = ActThreeState.Resolve(books);
                        tally[e] = tally.TryGetValue(e, out var c) ? c + 1 : 1;
                    }
                    int d = Math.Max(1, n);
                    double Pct(Ending e) => 100.0 * (tally.TryGetValue(e, out var c) ? c : 0) / d;
                    Console.WriteLine($"{plan,-12} {label,-11} {n,4} {Pct(Ending.Both),5:0.0}% " +
                                      $"{Pct(Ending.Kingdom),7:0.0}% {Pct(Ending.StraightLife),8:0.0}% " +
                                      $"{Pct(Ending.BurnBoth),5:0.0}% {strain / d,7:0.00}");
                }
            }
            Console.WriteLine("  strain = what the inspection SEES (books x scope x deflection); " +
                              $"above {LedgerState.BooksHoldThreshold:0.00} you keep nothing.");
            Console.WriteLine("  Quiet is absent by construction: handing over is a deliberate act " +
                              "and the lab bot never reaches for it.");
            Console.WriteLine("  Both without deflect is the information-landscape road (act3-draft answer 3): " +
                              "reachable, and roughly half the rate of taking her deal — refusing is the hardest line, as approved.");
        }

        static void PlanActions(OpenPlan plan, EmpireBook e, GossipMill mill, Wallet wallet, GameTime now)
        {
            if (plan == OpenPlan.Control) return;
            var sam = mill.Get("Sam");
            var viktor = mill.Get("Viktor");
            var josip = mill.Get("Josip");
            var shop = e.BusinessOf("pawnshop");
            var coll = e.RacketOf("collection");

            if (plan == OpenPlan.Aggressive)
            {
                if (e.CrewOf("Sam") == null && sam != null) e.RecruitByNeed(sam, "Sam", 120, wallet, now);
                if (!coll.Established && e.CrewOf("Sam") != null) e.Establish(coll, e.CrewOf("Sam"), now);
                if (!shop.Owned && !shop.DebtHeld && wallet.Total >= shop.DebtPrice) e.BuyDebt(shop, wallet);
                if (!shop.Owned && shop.DebtHeld && viktor != null) e.Squeeze(shop, viktor, mill, now);
                if (e.CrewOf("Josip") == null && josip != null && wallet.Total >= 100) e.RecruitByNeed(josip, "Josip", 100, wallet, now);
                var prot = e.RacketOf("protection");
                if (!prot.Established && e.CrewOf("Josip") != null) e.Establish(prot, e.CrewOf("Josip"), now);
            }
            else // Cautious: clean money only, one round, and not before the street settles.
            {
                if (!shop.Owned && wallet.Clean >= shop.AskPrice && viktor != null) e.BuyClean(shop, wallet, viktor, now);
                if (now.Day >= 12 && e.CrewOf("Sam") == null && sam != null) e.RecruitByNeed(sam, "Sam", 120, wallet, now);
                if (now.Day >= 13 && !coll.Established && e.CrewOf("Sam") != null) e.Establish(coll, e.CrewOf("Sam"), now);
            }
        }

        static EmpireBook BuildEmpire()
        {
            var e = new EmpireBook();
            e.Businesses.Add(new Business
            {
                Id = "pawnshop", Name = "pawnshop", OwnerId = "Viktor", PlaceId = "pawnshop",
                AskPrice = 900, DebtPrice = 250, SecretId = "viktor_skim",
                CleanIncomePerDay = 60, LaunderPerDay = 80,
            });
            e.Businesses.Add(new Business
            {
                Id = "stall", Name = "market stall", OwnerId = "Mirela", PlaceId = "market_corner",
                AskPrice = 500, DebtPrice = 0, SecretId = "mirela_scale",
                CleanIncomePerDay = 40, LaunderPerDay = 30,
            });
            e.Rackets.Add(new Racket { Id = "collection", Name = "collection round", IncomePerDay = 60, BaseRisk = 0.35 });
            e.Rackets.Add(new Racket { Id = "protection", Name = "protection round", IncomePerDay = 80, BaseRisk = 0.5 });
            return e;
        }

        /// The founding street plus the empire's people, ties as in-game.
        static GossipMill BuildOpenStreet()
        {
            var graph = new SocialGraph();
            graph.Link("Rocco", "Lena", 0.7);
            graph.Link("Rocco", "Sam", 0.8);
            graph.Link("Sam", "Lena", 0.6);
            graph.Link("Ada", "Lena", 0.6);
            graph.Link("Ada", "Sam", 0.5);
            graph.Link("Josip", "Rocco", 0.6);
            graph.Link("Josip", "Sam", 0.3);
            graph.Link("Mirela", "Ada", 0.5);
            graph.Link("Mirela", "Sam", 0.4);
            graph.Link("Viktor", "Lena", 0.4);
            graph.Link("Viktor", "Sam", 0.5);
            var mill = new GossipMill(graph);
            mill.Add(Brain("Lena", "day", 0.25, 0.75, 0.5));
            mill.Add(Brain("Rocco", "night", 0.6, 0.5, 0.6));
            mill.Add(Brain("Ada", "day", 0.15, 0.8, 0.4));
            mill.Add(Brain("Sam", "both", 0.85, 0.25, 0.3));
            mill.Add(Brain("Josip", "night", 0.7, 0.45, 0.35));
            mill.Add(Brain("Mirela", "day", 0.55, 0.35, 0.4));
            mill.Add(Brain("Viktor", "day", 0.7, 0.4, 0.4));
            return mill;
        }

        /// Same cast, traits, and ties as the game wires up (CastSetup + GossipDirector).
        static GossipMill BuildStreet()
        {
            var graph = new SocialGraph();
            graph.Link("Rocco", "Lena", 0.7);
            graph.Link("Rocco", "Sam", 0.8);
            graph.Link("Sam", "Lena", 0.6);
            graph.Link("Ada", "Lena", 0.6);
            graph.Link("Ada", "Sam", 0.5);
            var mill = new GossipMill(graph);
            mill.Add(Brain("Lena", "day", 0.25, 0.75, 0.5));
            mill.Add(Brain("Rocco", "night", 0.6, 0.5, 0.6));
            mill.Add(Brain("Ada", "day", 0.15, 0.8, 0.4));
            mill.Add(Brain("Sam", "both", 0.85, 0.25, 0.3));
            return mill;
        }

        static Gossiper Brain(string name, string circle, double greed, double nerve, double loyalty) =>
            new Gossiper(name, name, new MemoryStore(name.ToLowerInvariant()), new KnowledgeBase(),
                new SuspicionTracker(), circle, greed, nerve, loyalty);

        /// Is this pair plausibly in the same place this hour? Mirrors the ACTUAL
        /// in-game schedules, not abstract circles: Rocco drinks at the bar from
        /// noon (next to Lena) and roams at night; Lena works the bar 08-24; Ada is
        /// a daytime face; Sam is out at all hours.
        static bool BothActive(string a, string b, int hour) => Active(a, hour) && Active(b, hour);

        static bool Active(string id, int hour)
        {
            switch (id)
            {
                case "Rocco": return hour >= 12 || hour < 4; // bar afternoons, streets at night
                case "Lena": return hour >= 8;               // behind the counter till close
                case "Ada": return hour >= 8 && hour < 20;
                case "Mirela": return hour >= 8 && hour < 18;  // the stall
                case "Viktor": return hour >= 9 && hour < 20;  // shop hours, then the teahouse
                case "Josip": return hour >= 18 || hour < 6;   // the docks' hours
                default: return true;                        // Sam
            }
        }
    }
}
