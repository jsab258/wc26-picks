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
            };

            Console.WriteLine($"weeks/policy={weeks}  talk/h={TalkChancePerHourSameCircle}  witness={WitnessChance}");
            Console.WriteLine($"{"policy",-13} {"win%",5} {"exposed%",8} {"castout%",8} {"avg$",6} {"avgHeat",7} {"avgDC$",6}");
            foreach (var (name, policy) in policies)
            {
                var r = RunMany(policy, weeks);
                Console.WriteLine($"{name,-13} {r.winPct,5:0.0} {r.exposedPct,8:0.0} {r.castoutPct,8:0.0} {r.avgCash,6:0} {r.avgPeakHeat,7:0.00} {r.avgDcSpend,6:0}");
            }

            RunOpenLab(weeks);
        }

        enum DcStyle { None, Bribe, Intimidate, Discredit, Smart }

        class Policy
        {
            public bool SkipJobs;
            public DcStyle Dc = DcStyle.None;
            public bool KeepBeats;     // honor Ada d3 / Rocco d5 evenings, missing those drops
            public bool UseHooks;      // leash Rocco with his secret on day 2
            public bool CollectDebts;  // work Marek's book on day 2
        }

        static (double winPct, double exposedPct, double castoutPct, double avgCash, double avgPeakHeat, double avgDcSpend)
            RunMany(Policy policy, int weeks)
        {
            int win = 0, exposed = 0, castout = 0;
            double cashSum = 0, peakHeatSum = 0, dcSum = 0;
            for (int seed = 0; seed < weeks; seed++)
            {
                var o = RunWeek(policy, new Random(seed * 7919 + 13));
                if (o.verdict == Verdict.WonWeek) win++;
                else if (o.verdict == Verdict.LostExposed) exposed++;
                else if (o.verdict == Verdict.LostCastOut) castout++;
                cashSum += o.cash;
                peakHeatSum += o.peakHeat;
                dcSum += o.dcSpend;
            }
            return (100.0 * win / weeks, 100.0 * exposed / weeks, 100.0 * castout / weeks,
                cashSum / weeks, peakHeatSum / weeks, dcSum / weeks);
        }

        static (Verdict verdict, int cash, double peakHeat, int dcSpend) RunWeek(Policy policy, Random rng)
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
                    if (policy.CollectDebts)
                        foreach (var d in debts) { d.Collect(mill.Get(d.Id), wallet, mill, now); dcSpend -= 0; }
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
            return (camp.Verdict, wallet.Total, peakHeat, dcSpend);
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
            Console.WriteLine($"{"plan",-12} {"reach%",7} {"cash",7} {"falls",6} {"cutoff%",8} {"stage",6} {"rounds$",8} {"broke%",7}");
            foreach (var plan in new[] { OpenPlan.Control, OpenPlan.Aggressive, OpenPlan.Cautious })
            {
                int reached = 0, cutoff = 0, broke = 0;
                double cash = 0, falls = 0, stage = 0, rounds = 0;
                for (int seed = 0; seed < runs; seed++)
                {
                    var o = RunOpenCampaign(plan, new Random(seed * 104729 + 7));
                    if (!o.reachedOpen) continue;
                    reached++;
                    cash += o.endCash; falls += o.falls; stage += o.rivalStage; rounds += o.racketIncome;
                    if (o.cutOff) cutoff++;
                    if (o.endCash < 50) broke++;
                }
                int n = Math.Max(1, reached);
                Console.WriteLine($"{plan,-12} {100.0 * reached / runs,6:0.0}% {cash / n,7:0} {falls / n,6:0.00} " +
                                  $"{100.0 * cutoff / n,7:0.0}% {stage / n,6:0.0} {rounds / n,8:0} {100.0 * broke / n,6:0.0}%");
            }
        }

        static (bool reachedOpen, int endCash, int falls, bool cutOff, int rivalStage, int racketIncome)
            RunOpenCampaign(OpenPlan plan, Random rng)
        {
            var camp = new Campaign();
            var mill = BuildOpenStreet();
            var wallet = new Wallet(250);
            var empire = BuildEmpire();
            mill.Witness("Rocco", new Fact("player", "location_d2_evening", "warehouse"),
                "the new owner was at the old warehouse the night of the fire", true, new GameTime(1, 9, 0));

            var now = new GameTime(1, 9, 0);
            int lastClosedDay = 1, jobPostedDay = -1, lastActDay = 0;
            bool jobOpen = false;

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
                    foreach (var b in empire.Businesses)
                        if (b.Owned) takings += (int)Math.Round(b.CleanIncomePerDay * Math.Max(0.0, 1.0 - 0.85 * heat));
                    wallet.EarnClean(takings);
                    wallet.LaunderPerDay = 120 + empire.OwnedLaunderCapacity;
                    wallet.Launder();
                    if (camp.Verdict == Verdict.WonWeek) camp.EnterOpenMode();
                    if (camp.Verdict != Verdict.Ongoing) break; // lost the week itself
                    if (camp.OpenMode)
                    {
                        empire.DailyTick(now, wallet, mill);
                        if (camp.FallPending)
                        {
                            // The Fall, as the game runs it: seize, the street knows, 3 days gone.
                            camp.ConsumeFall();
                            wallet.Seize();
                            foreach (var a in mill.Agents)
                            {
                                a.Rumors.RemoveAll(r => r.Content.Subject == "player");
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
            return (camp.OpenMode, wallet.Total, camp.Falls, camp.OutfitCutOff, empire.Rival.Stage, empire.TotalRacketIncome);
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
