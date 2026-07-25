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
            };

            Console.WriteLine($"weeks/policy={weeks}  talk/h={TalkChancePerHourSameCircle}  witness={WitnessChance}");
            Console.WriteLine($"{"policy",-13} {"win%",5} {"exposed%",8} {"castout%",8} {"avg$",6} {"avgHeat",7} {"avgDC$",6}");
            foreach (var (name, policy) in policies)
            {
                var r = RunMany(policy, weeks);
                Console.WriteLine($"{name,-13} {r.winPct,5:0.0} {r.exposedPct,8:0.0} {r.castoutPct,8:0.0} {r.avgCash,6:0} {r.avgPeakHeat,7:0.00} {r.avgDcSpend,6:0}");
            }
        }

        enum DcStyle { None, Bribe, Intimidate, Discredit, Smart }

        class Policy
        {
            public bool SkipJobs;
            public DcStyle Dc = DcStyle.None;
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
            int cash = 250, dcSpend = 0;
            double peakHeat = 0;

            // The founding secret, same as in-game: Rocco saw something.
            mill.Witness("Rocco", new Fact("player", "location_d2_evening", "warehouse"),
                "the new owner was at the old warehouse the night of the fire", true, new GameTime(1, 9, 0));

            var now = new GameTime(1, 9, 0);
            int lastClosedDay = 1, jobPostedDay = -1;
            bool jobOpen = false, actedToday = false;
            int lastActDay = 0;

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
                    cash += camp.CloseDay(heat);
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
                        dcSpend += Act(policy.Dc, mill, lead, ref cash, now);
                    }
                }

                // Night job window.
                if (now.Hour >= 22 && jobPostedDay != now.Day) { jobPostedDay = now.Day; jobOpen = true; }
                if (jobOpen && now.Hour >= 23) // resolve an hour into the window
                {
                    jobOpen = false;
                    if (policy.SkipJobs) camp.JobMissed();
                    else
                    {
                        camp.JobDone();
                        cash += camp.JobPay;
                        if (rng.NextDouble() < WitnessChance)
                        {
                            string who = rng.NextDouble() < 0.6 ? "Rocco" : "Sam";
                            mill.Witness(who, new Fact("player", $"night_job_d{now.Day}", "seen"),
                                "the new owner was handling a package in the street past midnight", true, now);
                        }
                    }
                }
            }
            return (camp.Verdict, cash, peakHeat, dcSpend);
        }

        /// One damage-control move against the strongest lead. Returns dollars spent.
        static int Act(DcStyle style, GossipMill mill, Lead lead, ref int cash, GameTime now)
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
                    if (cash < price) { mill.Discredit(lead.TopicKey, null, now); return 0; }
                    var r = mill.Bribe(lead.HolderId, lead.TopicKey, price, now);
                    if (r.Outcome == DcOutcome.Contained) { cash -= price; return price; }
                    return 0;
                case DcStyle.Intimidate:
                    mill.Intimidate(lead.HolderId, lead.TopicKey, now);
                    return 0;
                default:
                    mill.Discredit(lead.TopicKey, null, now);
                    return 0;
            }
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
                default: return true;                        // Sam
            }
        }
    }
}
