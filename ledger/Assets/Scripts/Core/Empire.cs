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
        public string Cut = "fair";   // fair | generous | skim — §6.5: loyalty is cuts paid
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

    /// A rival organization's street presence (§2.4, extended to the doc's
    /// three): flat structure (Nemesis patent — no promotion ladders, no
    /// player-defeat advancement). Attention is driven by what its people
    /// actually observe; stages escalate on thresholds and act at most once a
    /// day. Each arm's doctrine attacks a different ledger:
    ///   dockside — muscle and patience, against your PEOPLE
    ///   machine  — lawyers and paper, against your CLEAN money
    ///   newcrew  — noise, against your COVER
    public class RivalArm
    {
        public string Id = "dockside";
        public string HeadName = "Sera Kest";
        public double Attention;      // 0..1
        public int Stage;             // 0 quiet · 1 notice · 2 pressure · 3 grab · 4 summit
        public int LastActDay = -1;
        public int ProtectionTaxPerDay; // dockside stage 2+: the street's rent

        /// An organization is people (§6.5: "their org charts are individuals —
        /// flippable, bribable, with their own loyalty rot"). These are gossiper
        /// ids: real cards on the street who happen to answer to this arm. Every
        /// verb the player owns works on them; taking one is poaching.
        public readonly List<string> Members = new List<string>();

        /// Where the player stands with this arm, -1 (blood) .. +1 (theirs).
        public double Standing;
        /// True while the player works FOR this arm (one patron at a time).
        public bool IsPatron;
        public int TributePerDay;     // what a patron pays their people, or takes
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

        /// The three organizations (§6.5): Sera Kest's dockside syndicate,
        /// Aldous Vane's machine, Danny Ro's New crew.
        public readonly List<RivalArm> Arms = new List<RivalArm>
        {
            new RivalArm { Id = "dockside", HeadName = "Sera Kest" },
            new RivalArm { Id = "machine", HeadName = "Aldous Vane" },
            new RivalArm { Id = "newcrew", HeadName = "Danny Ro" },
        };
        /// The founding rival keeps its name — existing callers and saves read
        /// the dockside arm through it.
        public RivalArm Rival => Arms[0];
        public RivalArm ArmOf(string id) => Arms.Find(a => a.Id == id);

        /// Doctrine effects other systems consume at the daily close.
        public bool MachineInspecting => ArmOf("machine").Stage >= 2;   // fronts' income -25%
        public bool NewCrewTaxing => ArmOf("newcrew").Stage >= 3;       // rackets' take -20%

        /// Whose banner you fly, if anyone's. Independence is the default and
        /// the hardest road: three organizations, no protection from any.
        public RivalArm Patron => Arms.Find(a => a.IsPatron);
        public RivalArm ArmOfMember(string id) => Arms.Find(a => a.Members.Contains(id));

        // ---- allegiance: pledging, breaking, and taking their people ----

        public double PledgeStandingFloor = 0.2;   // they must not despise you
        public int PatronTribute = 50;             // what a patron's protection costs daily
        public double PoachStandingCost = 0.35;

        /// Work for an arm instead of against it (§ agency): their attention
        /// stops climbing, their protection is real, and the other two start
        /// treating your street as an extension of theirs.
        public bool PledgeTo(string armId, GossipMill mill, GameTime now)
        {
            var arm = ArmOf(armId);
            if (arm == null || arm.IsPatron || arm.Standing < PledgeStandingFloor) return false;
            foreach (var a in Arms) a.IsPatron = false;
            arm.IsPatron = true;
            arm.TributePerDay = PatronTribute;
            arm.Standing = Math.Clamp(arm.Standing + 0.2, -1, 1);
            arm.Attention = Math.Clamp(arm.Attention - 0.4, 0, 1);
            foreach (var other in Arms)
                if (other != arm) other.Standing = Math.Clamp(other.Standing - 0.25, -1, 1);
            Remember(mill, arm, now, $"The new owner flies {arm.HeadName}'s colors now. Everyone on this street noticed the day it happened.");
            return true;
        }

        /// Walk away from a patron. Nobody takes that quietly.
        public bool BreakWith(string armId, GossipMill mill, GameTime now)
        {
            var arm = ArmOf(armId);
            if (arm == null || !arm.IsPatron) return false;
            arm.IsPatron = false;
            arm.TributePerDay = 0;
            // However well you stood with them, leaving ends it below zero:
            // the higher you climbed, the further the fall reads.
            arm.Standing = Math.Clamp(Math.Min(arm.Standing - 0.6, -0.2), -1, 1);
            arm.Attention = Math.Clamp(arm.Attention + 0.35, 0, 1);
            Remember(mill, arm, now, $"The new owner walked out on {arm.HeadName}. That is not a thing people do twice.");
            return true;
        }

        /// Somebody who answered to an arm now answers to you. Called from the
        /// recruit paths — poaching is not a new verb, it is the old verb aimed
        /// at someone who already had an employer.
        public void NotePoach(string id, GossipMill mill, GameTime now)
        {
            var arm = ArmOfMember(id);
            if (arm == null) return;
            arm.Members.Remove(id);
            arm.Standing = Math.Clamp(arm.Standing - PoachStandingCost, -1, 1);
            arm.Attention = Math.Clamp(arm.Attention + 0.2, 0, 1);
            var g = mill?.Get(id);
            g?.Memory.Append(new MemoryEvent(now, "observation", 0.9,
                $"I used to answer to {arm.HeadName}'s people. I answer to the new owner now. Somebody will have noticed by morning."));
            Remember(mill, arm, now, $"One of {arm.HeadName}'s people went over to the new owner.");
        }

        // ---- the Table (Act II PP7): one mechanical effect per answer ----

        /// Dockside accepted: a percentage of everything the street makes.
        public double TributeShare;
        /// Machine accepted: the fronts declare less, so they earn less.
        public bool FrontsCapped;
        /// New crew accepted: a round you staff but do not fully collect from.
        public string SharedRacketId;

        /// Resolve the summit. Accept costs something permanent, defiance costs
        /// peace, a counter costs nothing but requires you to matter already.
        public void ResolveTable(string armId, string answer, GossipMill mill, GameTime now)
        {
            var arm = ArmOf(armId);
            if (arm == null) return;
            switch (answer)
            {
                case "accept":
                    if (armId == "dockside") TributeShare = 0.12;
                    else if (armId == "machine") FrontsCapped = true;
                    else SharedRacketId = Rackets.Find(r => r.Established)?.Id;
                    arm.Standing = Math.Clamp(arm.Standing + 0.4, -1, 1);
                    arm.Attention = Math.Clamp(arm.Attention - 0.5, 0, 1);
                    arm.Stage = Math.Min(arm.Stage, 2);
                    break;
                case "defy":
                    arm.Standing = Math.Clamp(arm.Standing - 0.5, -1, 1);
                    arm.Attention = 1.0;
                    break;
                default: // counter — you had the standing to price yourself
                    arm.Standing = Math.Clamp(arm.Standing + 0.15, -1, 1);
                    arm.Attention = Math.Clamp(arm.Attention - 0.3, 0, 1);
                    arm.Stage = Math.Min(arm.Stage, 3);
                    break;
            }
            Remember(mill, arm, now, $"The new owner sat down with {arm.HeadName} and {(answer == "accept" ? "took the terms" : answer == "defy" ? "said no to her face" : "put their own number on the table")}.");
        }

        /// Arm memory: what an organization's remaining people saw happen.
        static void Remember(GossipMill mill, RivalArm arm, GameTime now, string line)
        {
            if (mill == null) return;
            foreach (var id in arm.Members)
                mill.Get(id)?.Memory.Append(new MemoryEvent(now, "heard", 0.8, line));
        }

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
            NoteDeed(); // deeds are public record — the machine's clerks read them
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
                NoteDeed();
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
            NoteDeed();
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
            Enlist(g, "need", now);
            g.Memory.Append(new MemoryEvent(now, "conversation", 0.9,
                "I said yes. I work for the new owner now — because of what they did for me, not what they know about me. There's a difference."));
            NotePoachInternal(g.Id, now);
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
            Enlist(g, "hook", now);
            g.Memory.Append(new MemoryEvent(now, "observation", 0.95,
                "I work for the new owner now. Not because I chose to. I keep a list in my head of every time they remind me why."));
            NotePoachInternal(g.Id, now);
            Rival.Attention = Math.Clamp(Rival.Attention + RivalPerEvent * 0.5, 0, 1);
            return true;
        }

        static double Competence(Gossiper g) =>
            Math.Clamp(0.3 + g.Nerve * 0.4 + g.Loyalty * 0.2, 0.2, 0.9);

        /// Joining (or re-joining: someone who quit can be won back) revives the
        /// departed record instead of duplicating it — one person, one line in
        /// the book, however many times they've walked.
        void Enlist(Gossiper g, string route, GameTime now)
        {
            var prior = Crew.FirstOrDefault(c => c.Id == g.Id);
            if (prior != null)
            {
                prior.Departed = false;
                prior.Route = route;
                prior.Competence = Competence(g);
                prior.RecruitedDay = now.Day;
                prior.Assignment = null;
                prior.Cut = "fair";
                return;
            }
            Crew.Add(new CrewMember
            {
                Id = g.Id, Name = g.DisplayName, Route = route,
                Competence = Competence(g), RecruitedDay = now.Day,
            });
        }

        /// Recruit paths call this without a mill handle; the arm bookkeeping
        /// still happens, and the poached person's own memory is written by the
        /// caller. Mill-aware callers use NotePoach for the full effect.
        void NotePoachInternal(string id, GameTime now)
        {
            var arm = ArmOfMember(id);
            if (arm == null) return;
            arm.Members.Remove(id);
            arm.Standing = Math.Clamp(arm.Standing - PoachStandingCost, -1, 1);
            arm.Attention = Math.Clamp(arm.Attention + 0.2, 0, 1);
            LastPoachedFrom = arm.Id;
        }

        /// Which organization lost someone most recently — the game layer reads
        /// this to voice the consequence.
        public string LastPoachedFrom { get; private set; }

        /// Every transfer of a deed is public record; the machine's clerks read
        /// the registry so Aldous never has to visit.
        void NoteDeed() =>
            ArmOf("machine").Attention = Math.Clamp(ArmOf("machine").Attention + 0.12, 0, 1);

        /// §6.5 made daily: how you split the take with each of your people.
        /// Generous costs money and builds the loyalty that defeats poaching;
        /// skimming THEIR pay is free money on a fuse — and they keep books too.
        public void SetCut(CrewMember crew, string policy, GossipMill mill, GameTime now)
        {
            if (crew == null || crew.Departed) return;
            if (policy != "fair" && policy != "generous" && policy != "skim") return;
            if (crew.Cut == policy) return;
            crew.Cut = policy;
            var g = mill?.Get(crew.Id);
            g?.Memory.Append(new MemoryEvent(now, "observation", 0.7,
                policy == "generous" ? "The new owner bumped my cut without being asked. I notice things like that."
                : policy == "skim" ? "My envelope is light again. I counted twice. I always count twice."
                : "Back to the standard split. Fair is fair, I suppose."));
        }

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
                // The cut, paid daily (§6.5): generosity is bought loyalty; a
                // skimmed envelope is counted, remembered, and eventually repaid.
                if (runnerG != null)
                {
                    if (runner.Cut == "generous")
                    {
                        income -= 15;
                        runnerG.Loyalty = Math.Clamp(runnerG.Loyalty + 0.03, 0, 1);
                    }
                    else if (runner.Cut == "skim")
                    {
                        income += 15;
                        runnerG.Loyalty = Math.Clamp(runnerG.Loyalty - 0.05, 0, 1);
                        if (now.Day % 3 == 0)
                            runnerG.Memory.Append(new MemoryEvent(now, "observation", 0.65,
                                $"Light again. The {r.Name} pays the same every day; my envelope doesn't. I keep my own book on this."));
                    }
                }
                // Rot completes (§6.5): a need-route crew member skimmed past
                // the breaking point doesn't wait to be poached — they quit,
                // loudly enough to hear, and the round dies with them. Hook-crew
                // can't leave; that is the hook route's whole brittle bargain.
                if (runner.Cut == "skim" && runner.Route == "need" && runnerG != null && runnerG.Loyalty < 0.2)
                {
                    runner.Departed = true;
                    runner.Assignment = null;
                    r.Established = false;
                    r.RunnerId = null;
                    runnerG.Memory.Append(new MemoryEvent(now, "observation", 0.95,
                        "I quit. I joined because they helped me once; I left because of the envelopes. Let them run their own rounds."));
                    events.Add(new EmpireEvent { Kind = "crew", ActorId = runner.Id,
                        Text = $"{runner.Name} leaves the take on the counter and walks. \"Count it yourself from now on.\"" });
                    continue;
                }

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
                // The New crew's kid taxing your rounds (stage 3+): loud, simple, real.
                if (NewCrewTaxing) income = (int)Math.Round(income * 0.8);
                // Treaty terms, if you signed any (Act II's Table).
                if (TributeShare > 0) income = (int)Math.Round(income * (1.0 - TributeShare));
                if (SharedRacketId != null && r.Id == SharedRacketId) income = (int)Math.Round(income * 0.5);
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
            events.AddRange(MachineTick(now, wallet, mill));
            events.AddRange(NewCrewTick(now, mill, rng));
            return events;
        }

        /// The machine (Aldous Vane): paper against your clean money. Its clerks
        /// read the deed registry; its pressure arrives as filings, never faces.
        List<EmpireEvent> MachineTick(GameTime now, Wallet wallet, GossipMill mill)
        {
            var events = new List<EmpireEvent>();
            var arm = ArmOf("machine");
            int stageDue = arm.Attention >= 0.9 ? 4 : arm.Attention >= 0.75 ? 3 : arm.Attention >= 0.5 ? 2 : arm.Attention >= 0.25 ? 1 : 0;

            // Stage 3+: recurring legal fees, clean money only — lawyers don't take cash in envelopes.
            if (arm.Stage >= 3 && now.Day % 3 == 0)
            {
                int fee = Math.Min(150, wallet.Clean);
                if (fee > 0)
                {
                    wallet.Spend(fee, dirtyOk: false);
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = $"Another letter on cream paper. Answering it costs ${fee} in filings and fees. It is not meant to be affordable; it is meant to be regular." });
                }
            }
            if (stageDue <= arm.Stage || arm.LastActDay == now.Day) return events;
            arm.Stage = stageDue;
            arm.LastActDay = now.Day;
            switch (stageDue)
            {
                case 1:
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "A clerk you've never seen photographs the pawnshop's deed plate, notes something, and leaves without buying." });
                    break;
                case 2:
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "Inspectors visit every front you own in one morning. Nothing is wrong; everything is slower now. The paperwork has opinions." });
                    break;
                case 3:
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "A letter from Vane, Holt & Partners: your acquisitions are 'of interest'. The first fees arrive with it." });
                    break;
                default:
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "A single sheet, hand-delivered: a meeting is available, at your convenience, which is to say at his. The machine has finished reading you." });
                    break;
            }
            return events;
        }

        /// The New crew (Danny Ro): noise against your cover. His kids watch the
        /// street's temperature, and their incidents spend YOUR credibility.
        List<EmpireEvent> NewCrewTick(GameTime now, GossipMill mill, Random rng)
        {
            var events = new List<EmpireEvent>();
            var arm = ArmOf("newcrew");
            // Observation: a loud street draws the loud. Heat is what his people see.
            if (mill.DayCircleHeat() >= 0.45)
                arm.Attention = Math.Clamp(arm.Attention + 0.06, 0, 1);

            // Stage 2+: manufactured incidents — heat you didn't earn, every third day.
            if (arm.Stage >= 2 && now.Day % 3 == 1)
            {
                var pool = new List<Gossiper>();
                foreach (var a in Agents(mill)) if (a.Circle == "day" && !a.Leashed) pool.Add(a);
                if (pool.Count > 0)
                {
                    var w = pool[rng.Next(pool.Count)];
                    mill.Witness(w.Id, new Fact("player", $"street_trouble_d{now.Day}", "seen"),
                        "there was trouble on the new owner's street again — broken glass, shouting, that crowd", true, now, 0.5);
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "Glass across the walk outside the bakery, a fire barrel tipped, laughter running off toward the Strip. Your street, your reputation, not your doing." });
                }
            }
            int stageDue = arm.Attention >= 0.9 ? 4 : arm.Attention >= 0.75 ? 3 : arm.Attention >= 0.5 ? 2 : arm.Attention >= 0.25 ? 1 : 0;
            if (stageDue <= arm.Stage || arm.LastActDay == now.Day) return events;
            arm.Stage = stageDue;
            arm.LastActDay = now.Day;
            switch (stageDue)
            {
                case 1:
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "A tag appears on the bar's side wall overnight — a grinning fish. Kids' stuff. Kids who wanted you to see it." });
                    break;
                case 2:
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "The Strip kid is back on your corner, louder now, performing for somebody. The street watches you not deal with it." });
                    break;
                case 3:
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "Your runners report a new toll: the kid takes his cut of your rounds now, 'for the neighborhood'. Danny Ro's neighborhood, apparently." });
                    break;
                default:
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = "Music from a car that circles your block four times, windows down, nobody hurrying. An invitation, the way a lit match is an invitation." });
                    break;
            }
            return events;
        }

        static IEnumerable<Gossiper> Agents(GossipMill mill) => mill.Agents;

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

            // A patron's protection is real: they stop escalating and their
            // rivals' pressure is answered by people who aren't you. It costs.
            if (Rival.IsPatron)
            {
                Rival.Attention = Math.Clamp(Rival.Attention - 0.05, 0, 1);
                if (Rival.TributePerDay > 0 && wallet.Total > 0)
                {
                    wallet.Spend(Math.Min(Rival.TributePerDay, wallet.Total), dirtyOk: true);
                    events.Add(new EmpireEvent { Kind = "rival",
                        Text = $"{Rival.HeadName}'s collector takes the tribute and leaves a nod. Under her flag, that nod is the product." });
                }
                return events;
            }

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
                    { "cut", c.Cut },
                }).ToList() },
            { "rackets", Rackets.Select(r => (object)new Dictionary<string, object>
                {
                    { "id", r.Id }, { "established", r.Established },
                    { "runner", r.RunnerId ?? "" }, { "day", r.EstablishedDay },
                }).ToList() },
            { "rivalAttention", Rival.Attention }, { "rivalStage", Rival.Stage },
            { "rivalLastAct", Rival.LastActDay }, { "rivalTax", Rival.ProtectionTaxPerDay },
            { "arms", Arms.Select(a => (object)new Dictionary<string, object>
                {
                    { "id", a.Id }, { "attention", a.Attention }, { "stage", a.Stage },
                    { "lastAct", a.LastActDay }, { "tax", a.ProtectionTaxPerDay },
                    { "standing", a.Standing }, { "patron", a.IsPatron },
                    { "tribute", a.TributePerDay },
                    { "members", a.Members.Cast<object>().ToList() },
                }).ToList() },
            { "racketIncome", TotalRacketIncome },
            { "tributeShare", TributeShare }, { "frontsCapped", FrontsCapped },
            { "sharedRacket", SharedRacketId ?? "" },
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
                    Cut = string.IsNullOrEmpty(MiniJson.GetString(d, "cut")) ? "fair" : MiniJson.GetString(d, "cut"),
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
            foreach (var o in MiniJson.GetList(data, "arms") ?? new List<object>())
            {
                var d = MiniJson.AsObject(o);
                var arm = d != null ? ArmOf(MiniJson.GetString(d, "id")) : null;
                if (arm == null) continue;
                arm.Attention = d.TryGetValue("attention", out var at) ? Convert.ToDouble(at) : 0;
                arm.Stage = MiniJson.GetInt(d, "stage");
                arm.LastActDay = d.TryGetValue("lastAct", out var laa) ? Convert.ToInt32(laa) : -1;
                arm.ProtectionTaxPerDay = MiniJson.GetInt(d, "tax");
                arm.Standing = d.TryGetValue("standing", out var st) ? Convert.ToDouble(st) : 0;
                arm.IsPatron = Is(d, "patron");
                arm.TributePerDay = MiniJson.GetInt(d, "tribute");
                arm.Members.Clear();
                foreach (var m in (MiniJson.GetList(d, "members") ?? new List<object>()).OfType<string>())
                    arm.Members.Add(m);
            }
            TotalRacketIncome = MiniJson.GetInt(data, "racketIncome");
            TributeShare = data.TryGetValue("tributeShare", out var ts) ? Convert.ToDouble(ts) : 0;
            FrontsCapped = Is(data, "frontsCapped");
            var shared = MiniJson.GetString(data, "sharedRacket");
            SharedRacketId = string.IsNullOrEmpty(shared) ? null : shared;
        }

        static bool Is(Dictionary<string, object> d, string key) =>
            d.TryGetValue(key, out var v) && v is bool b && b;
    }
}
