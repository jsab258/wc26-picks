using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// Empire v1 (open-city-spec.md §2, approved broader scope): businesses,
    /// crew, rackets, and one observing rival — each an inversion or extension
    /// of a built system, none of it scripted. Pure state + rules; no Unity, no
    /// LLM. The gossip mill remains the nervous system: rackets create witnesses,
    /// witnesses create talk, talk is what the rival actually reacts to.
    public class Business
    {
        public string Id;
        public string Name;
        public string OwnerId;        // gossiper id; stays on to run it when bought
        public string PlaceId;        // HookMap place
        public int AskPrice;          // the clean route: slow, expensive, friendly
        public int DebtPrice;         // buy their paper, then squeeze (0 = no paper)
        public string SecretId;       // the hook route: leverage beats money
        public int CleanIncomePerDay; // heat-taxed like the bar — a front is a front
        public int LaunderPerDay;     // added washing capacity once owned

        public bool Owned;
        public string AcquiredVia;    // clean | debt | hook
        public bool DebtHeld;         // you bought the paper but haven't turned the key
        public int LastSqueezeDay = -1;
    }

    public class CrewMember
    {
        public string Id;             // gossiper id — they keep their life, memory, gossip
        public string Name;
        public string Route;          // need | hook — how they came to you
        public double Competence;     // set from traits at recruitment
        public int RecruitedDay;
        public string Assignment;     // racket id or null
        public bool Departed;         // poached or walked — betrayal is visible, never silent
    }

    public class Racket
    {
        public string Id;             // collection | protection | fencing
        public string Name;
        public int IncomePerDay;      // dirty
        public double BaseRisk;       // chance/day a witness sees the runner work
        public string RequiresBusinessId; // some rackets need a front (fencing needs the pawnshop)
        public bool Established;
        public string RunnerId;
        public int EstablishedDay;
    }

    /// The Dockside street arm (§2.4): flat structure (Nemesis patent — no
    /// promotion ladders, no player-defeat advancement). Attention is driven by
    /// what its people actually observe; stages escalate on thresholds and act
    /// at most once a day.
    public class RivalArm
    {
        public double Attention;      // 0..1
        public int Stage;             // 0 quiet · 1 warning · 2 tax · 3 poach · 4 threat
        public int LastActDay = -1;
        public int ProtectionTaxPerDay; // stage 2+: the street's rent, taken daily
    }

    public class EmpireEvent
    {
        public string Kind;           // income | witness | rival | crew
        public string Text;
        public string ActorId;
        public int Amount;            // income events: the dirty take
    }

    public class EmpireBook
    {
        public readonly List<Business> Businesses = new List<Business>();
        public readonly List<CrewMember> Crew = new List<CrewMember>();
        public readonly List<Racket> Rackets = new List<Racket>();
        public readonly RivalArm Rival = new RivalArm();

        // Tunables.
        public double RecruitLoyaltyFloor = 0.55;   // the need route ends in a yes only past this
        public double NeedLoyaltyBoost = 0.25;      // supplying someone's need is remembered
        public double SqueezeLoyaltyCost = 0.25;
        public double RivalPerEvent = 0.15;         // attention per empire move their people can see
        public double RivalPerWitness = 0.08;       // attention per racket witness in the night circle
        public double PoachLoyaltyFloor = 0.4;      // below this, a poached crew member walks

        public IEnumerable<CrewMember> ActiveCrew => Crew.Where(c => !c.Departed);
        public CrewMember CrewOf(string id) => Crew.FirstOrDefault(c => c.Id == id && !c.Departed);
        public Business BusinessOf(string id) => Businesses.FirstOrDefault(b => b.Id == id);
        public Racket RacketOf(string id) => Rackets.FirstOrDefault(r => r.Id == id);

        public int OwnedLaunderCapacity => Businesses.Where(b => b.Owned).Sum(b => b.LaunderPerDay);

        /// Lifetime dirty income off the rackets — the self-test's proof that
        /// the inverted drop machinery actually pays.
        public int TotalRacketIncome { get; private set; }

        // ---- businesses: three ways in (open-city-spec §2.1) ----

        /// The clean route: full price, clean money only, and the owner stays a
        /// friend — selling to you was their choice.
        public bool BuyClean(Business b, Wallet wallet, Gossiper owner, GameTime now)
        {
            if (b == null || b.Owned) return false;
            if (!wallet.Spend(b.AskPrice, dirtyOk: false)) return false;
            b.Owned = true;
            b.AcquiredVia = "clean";
            if (owner != null)
            {
                owner.Loyalty = Math.Clamp(owner.Loyalty + 0.15, 0, 1);
                owner.Memory.Append(new MemoryEvent(now, "conversation", 0.8,
                    $"Sold the {b.Name} to the new owner. Fair price, paid in full. I still run the counter."));
            }
            Rival.Attention = Math.Clamp(Rival.Attention + RivalPerEvent * 0.5, 0, 1); // even clean money moves get noticed
            return true;
        }

        /// The debt route, step one: buy their paper. Criminal counterparties
        /// take dirty money for it — that is rather the point.
        public bool BuyDebt(Business b, Wallet wallet)
        {
            if (b == null || b.Owned || b.DebtHeld || b.DebtPrice <= 0) return false;
            if (!wallet.Spend(b.DebtPrice, dirtyOk: true)) return false;
            b.DebtHeld = true;
            return true;
        }

        /// The debt route, step two: turn the key. Trait-gated like collection —
        /// the nervous fold, the hard-nosed refuse and tell the street.
        public DcResult Squeeze(Business b, Gossiper owner, GossipMill mill, GameTime now)
        {
            if (b == null || b.Owned || !b.DebtHeld || owner == null)
                return new DcResult { Outcome = DcOutcome.NoSuchRumor, Message = "You hold no paper on them." };
            if (b.LastSqueezeDay == now.Day)
                return new DcResult { Outcome = DcOutcome.AlreadyDenied, Message = "Not twice in one day. Let it sit." };
            b.LastSqueezeDay = now.Day;

            if (owner.Nerve <= 0.6 || owner.Loyalty >= 0.6)
            {
                b.Owned = true;
                b.AcquiredVia = "debt";
                owner.Loyalty = Math.Clamp(owner.Loyalty - SqueezeLoyaltyCost, 0, 1);
                owner.Memory.Append(new MemoryEvent(now, "observation", 0.9,
                    $"The new owner bought my paper and called it. The {b.Name} is theirs now. I work in my own shop."));
                Rival.Attention = Math.Clamp(Rival.Attention + RivalPerEvent, 0, 1);
                return new DcResult { Outcome = DcOutcome.Contained, Message = $"{owner.DisplayName} looks at the paper a long time, then hands over the keys." };
            }
            owner.Memory.Append(new MemoryEvent(now, "observation", 0.9,
                $"The new owner waved my debts at me over the {b.Name}. I told them where to put the paper."));
            var backfire = new Rumor
            {
                Content = new Fact("player", $"squeezing_{b.Id}", "true"),
                OriginId = owner.Id, Summary = $"the new owner is squeezing {owner.DisplayName} for the {b.Name}",
                Confidence = 0.85, Hops = 0, Sensitive = true,
            };
            owner.Rumors.Add(backfire);
            Rival.Attention = Math.Clamp(Rival.Attention + RivalPerEvent, 0, 1);
            return new DcResult { Outcome = DcOutcome.Backfired, NewRumor = backfire,
                Message = $"{owner.DisplayName} doesn't fold — and by tonight the street will know you came squeezing." };
        }

        /// The hook route: leverage beats money (§6.3 applied to property). A
        /// weak hook is spent; a strong hook keeps standing. Either way the shop
        /// changes hands and the owner hates the new arrangement a little.
        public DcResult AcquireViaHook(Business b, Secret secret, Gossiper owner, GameTime now)
        {
            if (b == null || b.Owned || secret == null || secret.OwnerId != b.OwnerId || !secret.KnownToPlayer)
                return new DcResult { Outcome = DcOutcome.NoSuchRumor, Message = "You hold nothing on them worth a shop." };
            if (!secret.Strong && secret.HookSpent)
                return new DcResult { Outcome = DcOutcome.AlreadyDenied, Message = "That favor is already spent." };
            if (!secret.Strong) secret.SpendWeak();
            b.Owned = true;
            b.AcquiredVia = "hook";
            if (owner != null)
            {
                owner.Loyalty = Math.Clamp(owner.Loyalty - 0.3, 0, 1);
                owner.Memory.Append(new MemoryEvent(now, "observation", 0.95,
                    $"The new owner said one quiet sentence about what they know, and I signed the {b.Name} over. I keep the counter. They keep me."));
            }
            Rival.Attention = Math.Clamp(Rival.Attention + RivalPerEvent, 0, 1);
            return new DcResult { Outcome = DcOutcome.Contained,
                Message = $"{owner?.DisplayName ?? b.OwnerId} goes very quiet, and the {b.Name} changes hands without a price." };
        }

        // ---- crew: two ways in (§2.2) ----

        /// The need route: supply what their card says they want. Slow, sticky —
        /// loyalty rises, and past the floor they say yes on their own.
        public bool RecruitByNeed(Gossiper g, string name, int costPaid, Wallet wallet, GameTime now)
        {
            if (g == null || CrewOf(g.Id) != null) return false;
            if (!wallet.Spend(costPaid, dirtyOk: true)) return false;
            g.Loyalty = Math.Clamp(g.Loyalty + NeedLoyaltyBoost, 0, 1);
            if (g.Loyalty < RecruitLoyaltyFloor)
            {
                g.Memory.Append(new MemoryEvent(now, "conversation", 0.7,
                    "The new owner sorted the thing I needed sorting. I owe them. Not everything — but I owe them."));
                return false; // the favor lands; the yes isn't there yet
            }
            Crew.Add(new CrewMember
            {
                Id = g.Id, Name = g.DisplayName, Route = "need",
                Competence = Competence(g), RecruitedDay = now.Day,
            });
            g.Memory.Append(new MemoryEvent(now, "conversation", 0.9,
                "I said yes. I work for the new owner now — because of what they did for me, not what they know about me. There's a difference."));
            Rival.Attention = Math.Clamp(Rival.Attention + RivalPerEvent * 0.5, 0, 1);
            return true;
        }

        /// The hook route: fast, brittle. They join because they must; loyalty
        /// starts wounded and the rot is visible early to the attentive.
        public bool RecruitByHook(Gossiper g, Secret secret, GameTime now)
        {
            if (g == null || CrewOf(g.Id) != null || secret == null
                || secret.OwnerId != g.Id || !secret.KnownToPlayer) return false;
            if (!secret.Strong && secret.HookSpent) return false;
            if (!secret.Strong) secret.SpendWeak();
            g.Loyalty = Math.Clamp(g.Loyalty - 0.2, 0, 1);
            Crew.Add(new CrewMember
            {
                Id = g.Id, Name = g.DisplayName, Route = "hook",
                Competence = Competence(g), RecruitedDay = now.Day,
            });
            g.Memory.Append(new MemoryEvent(now, "observation", 0.95,
                "I work for the new owner now. Not because I chose to. I keep a list in my head of every time they remind me why."));
            Rival.Attention = Math.Clamp(Rival.Attention + RivalPerEvent * 0.5, 0, 1);
            return true;
        }

        static double Competence(Gossiper g) =>
            Math.Clamp(0.3 + g.Nerve * 0.4 + g.Loyalty * 0.2, 0.2, 0.9);

        // ---- rackets (§2.3): the drop machinery, owned ----

        public bool Establish(Racket r, CrewMember runner, GameTime now)
        {
            if (r == null || r.Established || runner == null || runner.Departed) return false;
            if (runner.Assignment != null) return false;
            // Some rackets need a front: no fencing line without a shop to move it through.
            if (r.RequiresBusinessId != null && !(BusinessOf(r.RequiresBusinessId)?.Owned ?? false)) return false;
            r.Established = true;
            r.RunnerId = runner.Id;
            r.EstablishedDay = now.Day;
            runner.Assignment = r.Id;
            Rival.Attention = Math.Clamp(Rival.Attention + RivalPerEvent, 0, 1);
            return true;
        }

        /// One empire day, run at the morning close: racket income, witness
        /// generation through the SAME mill the night drops use, low-loyalty
        /// hook-crew skim, and the rival's daily read of the street. Deterministic
        /// per day (seeded) so the self-test can replay it.
        public List<EmpireEvent> DailyTick(GameTime now, Wallet wallet, GossipMill mill)
        {
            var events = new List<EmpireEvent>();
            var rng = new Random(now.Day * 7919 + 17);

            foreach (var r in Rackets.Where(x => x.Established))
            {
                var runner = CrewOf(r.RunnerId);
                if (runner == null) { r.Established = false; r.RunnerId = null; continue; }

                int income = r.IncomePerDay;
                var runnerG = mill.Get(runner.Id);
                // Rot is visible early: hook-crew whose loyalty has sunk skim the take.
                if (runner.Route == "hook" && runnerG != null && runnerG.Loyalty < 0.3)
                {
                    int skim = income / 4;
                    income -= skim;
                    runnerG.Memory.Append(new MemoryEvent(now, "observation", 0.6,
                        $"Took my extra cut off the {r.Name} take. They squeezed me into this; I square it my own way."));
                    events.Add(new EmpireEvent { Kind = "crew", ActorId = runner.Id,
                        Text = $"The {r.Name} take feels light again. {runner.Name} counts it out without meeting your eye." });
                }
                wallet.EarnDirty(income);
                TotalRacketIncome += income;
                events.Add(new EmpireEvent { Kind = "income", ActorId = runner.Id, Amount = income,
                    Text = $"{runner.Name} brings in ${income} off the {r.Name}." });

                // Witnesses: competence shades both the odds and how sure the story is.
                double risk = r.BaseRisk * (1.35 - runner.Competence);
                if (rng.NextDouble() < risk)
                {
                    var pool = mill.Agents.Where(a => a.Id != runner.Id && !a.Leashed).ToList();
                    if (pool.Count > 0)
                    {
                        var w = pool[rng.Next(pool.Count)];
                        double conf = 0.45 + 0.35 * (1.0 - runner.Competence);
                        mill.Witness(w.Id, new Fact("player", $"racket_{r.Id}_d{now.Day}", "seen"),
                            $"{runner.Name} was working a {r.Name} round for the new owner", true, now, conf);
                        events.Add(new EmpireEvent { Kind = "witness", ActorId = w.Id,
                            Text = $"Somebody clocked {runner.Name} on the {r.Name} round." });
                        if (w.Circle != "day")
                            Rival.Attention = Math.Clamp(Rival.Attention + RivalPerWitness, 0, 1);
                    }
                }
            }

            events.AddRange(RivalTick(now, wallet, mill, rng));
            return events;
        }

        /// The rival reads the street and, at most once a day, acts. Stages are
        /// escalation, not hierarchy; nothing here advances by beating the player.
        List<EmpireEvent> RivalTick(GameTime now, Wallet wallet, GossipMill mill, Random rng)
        {
            var events = new List<EmpireEvent>();
            if (Rival.LastActDay == now.Day) return events;

            int stageDue =
                Rival.Attention >= 0.9 ? 4 :
                Rival.Attention >= 0.75 ? 3 :
                Rival.Attention >= 0.5 ? 2 :
                Rival.Attention >= 0.25 ? 1 : 0;

            // The daily tax stands once imposed, whether or not they escalate today.
            if (Rival.ProtectionTaxPerDay > 0)
            {
                wallet.Spend(Math.Min(Rival.ProtectionTaxPerDay, wallet.Total), dirtyOk: true);
                events.Add(new EmpireEvent { Kind = "rival",
                    Text = $"The Dockside arm takes its ${Rival.ProtectionTaxPerDay} off the top. Nobody asks anymore." });
            }
            if (stageDue <= Rival.Stage) return events;

            Rival.Stage = stageDue;
            Rival.LastActDay = now.Day;
            switch (stageDue)
            {
                case 1:
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "A Dockside man drinks one slow beer at your bar, pays exact, and says only: \"Nice little street. Busy lately.\"" });
                    break;
                case 2:
                    Rival.ProtectionTaxPerDay = 40;
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "Word comes down the docks: the street's rent has gone up for you, specifically. $40 a day, collected without conversation." });
                    break;
                case 3:
                {
                    var target = ActiveCrew
                        .Select(c => (c, g: mill.Get(c.Id)))
                        .Where(x => x.g != null)
                        .OrderBy(x => x.g.Loyalty)
                        .FirstOrDefault();
                    if (target.c != null)
                    {
                        if (target.g.Loyalty < PoachLoyaltyFloor)
                        {
                            target.c.Departed = true;
                            if (target.c.Assignment != null)
                            {
                                var r = RacketOf(target.c.Assignment);
                                if (r != null) { r.Established = false; r.RunnerId = null; }
                                target.c.Assignment = null;
                            }
                            target.g.Memory.Append(new MemoryEvent(now, "observation", 0.95,
                                "The Dockside people offered better, and I took it. The new owner never once asked what I needed."));
                            events.Add(new EmpireEvent { Kind = "rival", ActorId = target.c.Id,
                                Text = $"{target.c.Name} didn't show today. Or yesterday, you realize. The docks have a new face on their payroll." });
                        }
                        else
                        {
                            target.g.Loyalty = Math.Clamp(target.g.Loyalty + 0.1, 0, 1);
                            target.g.Memory.Append(new MemoryEvent(now, "conversation", 0.9,
                                "Dockside offered me double to walk. I told the new owner instead. Remember that."));
                            events.Add(new EmpireEvent { Kind = "rival", ActorId = target.c.Id,
                                Text = $"{target.c.Name}, quiet, at the bar: \"Dockside offered me double. I'm telling you instead. That's worth something, no?\"" });
                        }
                    }
                    else events.Add(new EmpireEvent { Kind = "rival",
                        Text = "Dockside runners have been asking who works for you. Nobody had names to sell. Yet." });
                    break;
                }
                default:
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "Two Dockside men stand across from the bar all evening, doing nothing at all. The message doesn't need words. This street is spoken for." });
                    break;
            }
            return events;
        }

        // ---- persistence (P5) ----

        public Dictionary<string, object> Capture() => new Dictionary<string, object>
        {
            { "businesses", Businesses.Select(b => (object)new Dictionary<string, object>
                {
                    { "id", b.Id }, { "owned", b.Owned }, { "via", b.AcquiredVia ?? "" },
                    { "debtHeld", b.DebtHeld }, { "lastSqueeze", b.LastSqueezeDay },
                }).ToList() },
            { "crew", Crew.Select(c => (object)new Dictionary<string, object>
                {
                    { "id", c.Id }, { "name", c.Name }, { "route", c.Route },
                    { "competence", c.Competence }, { "day", c.RecruitedDay },
                    { "assignment", c.Assignment ?? "" }, { "departed", c.Departed },
                }).ToList() },
            { "rackets", Rackets.Select(r => (object)new Dictionary<string, object>
                {
                    { "id", r.Id }, { "established", r.Established },
                    { "runner", r.RunnerId ?? "" }, { "day", r.EstablishedDay },
                }).ToList() },
            { "rivalAttention", Rival.Attention }, { "rivalStage", Rival.Stage },
            { "rivalLastAct", Rival.LastActDay }, { "rivalTax", Rival.ProtectionTaxPerDay },
            { "racketIncome", TotalRacketIncome },
        };

        public void Restore(Dictionary<string, object> data)
        {
            if (data == null) return;
            foreach (var o in MiniJson.GetList(data, "businesses") ?? new List<object>())
            {
                var d = MiniJson.AsObject(o);
                var b = d != null ? BusinessOf(MiniJson.GetString(d, "id")) : null;
                if (b == null) continue;
                b.Owned = Is(d, "owned");
                var via = MiniJson.GetString(d, "via");
                b.AcquiredVia = string.IsNullOrEmpty(via) ? null : via;
                b.DebtHeld = Is(d, "debtHeld");
                b.LastSqueezeDay = MiniJson.GetInt(d, "lastSqueeze");
            }
            Crew.Clear();
            foreach (var o in MiniJson.GetList(data, "crew") ?? new List<object>())
            {
                var d = MiniJson.AsObject(o);
                if (d == null) continue;
                var assignment = MiniJson.GetString(d, "assignment");
                Crew.Add(new CrewMember
                {
                    Id = MiniJson.GetString(d, "id"), Name = MiniJson.GetString(d, "name"),
                    Route = MiniJson.GetString(d, "route"),
                    Competence = d.TryGetValue("competence", out var comp) ? Convert.ToDouble(comp) : 0.5,
                    RecruitedDay = MiniJson.GetInt(d, "day"),
                    Assignment = string.IsNullOrEmpty(assignment) ? null : assignment,
                    Departed = Is(d, "departed"),
                });
            }
            foreach (var o in MiniJson.GetList(data, "rackets") ?? new List<object>())
            {
                var d = MiniJson.AsObject(o);
                var r = d != null ? RacketOf(MiniJson.GetString(d, "id")) : null;
                if (r == null) continue;
                r.Established = Is(d, "established");
                var runner = MiniJson.GetString(d, "runner");
                r.RunnerId = string.IsNullOrEmpty(runner) ? null : runner;
                r.EstablishedDay = MiniJson.GetInt(d, "day");
            }
            Rival.Attention = data.TryGetValue("rivalAttention", out var ra) ? Convert.ToDouble(ra) : 0;
            Rival.Stage = MiniJson.GetInt(data, "rivalStage");
            Rival.LastActDay = data.TryGetValue("rivalLastAct", out var la) ? Convert.ToInt32(la) : -1;
            Rival.ProtectionTaxPerDay = MiniJson.GetInt(data, "rivalTax");
            TotalRacketIncome = MiniJson.GetInt(data, "racketIncome");
        }

        static bool Is(Dictionary<string, object> d, string key) =>
            d.TryGetValue(key, out var v) && v is bool b && b;
    }
}
