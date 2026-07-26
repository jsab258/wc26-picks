using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// Operation planning (roadmap M7.5, agency-model dimension 75 — the biggest
    /// hole the outside-in benchmark found, scoring 5).
    ///
    /// The difference between Hitman and a stealth corridor is that Hitman lets
    /// you DECIDE THINGS BEFOREHAND and then live with them. Not a loadout
    /// screen — four choices, each of which trades one thing you want for
    /// another thing you want:
    ///
    ///   APPROACH  quiet is slow and needs a steady hand; forced is fast and
    ///             loud; social costs you nothing physically and everything if
    ///             the street already talks about you.
    ///   HOUR      late is fewer eyes and more suspicion if you ARE seen —
    ///             nobody innocent is on that street at three in the morning.
    ///   WHO       more people is faster and more competent and much more
    ///             visible, and every one of them can talk afterwards.
    ///   TOOLS     carrying them makes the work easier and makes you a man
    ///             carrying tools, which is its own kind of evidence.
    ///
    /// TWO LAWS FROM THE PROJECT, ENFORCED HERE.
    ///
    /// The read is QUALITATIVE. The player approved "visible odds: a character's
    /// estimate, never a percentage" — so a plan reads as "this will probably go
    /// badly" and the game never becomes a spreadsheet. The number exists inside
    /// the simulation and is never shown.
    ///
    /// The OUTCOME IS DECIDED IN C#, from crew competence, the hour's witness
    /// density, the street's heat and the target's own difficulty. No model is
    /// consulted. What the model does afterwards is voice the people who saw it.

    public enum Approach
    {
        /// Slow, quiet, needs a steady hand. Few witnesses if it works.
        Quiet,
        /// Fast and loud. Reliable, and everybody hears about it.
        Forced,
        /// Talk your way in. Costs nothing physically; ruinous if the street
        /// already knows your name.
        Social,
    }

    /// Something worth doing, and what it would take.
    public class OperationTarget
    {
        public string Id;
        public string Name;
        public string PlaceId;
        /// 0..1. How hard this is before any of your choices.
        public double Difficulty = 0.5;
        /// Dirty money, on success.
        public int Payout = 200;
        /// 0..1. How overlooked this place is at its busiest.
        public double Exposure = 0.5;
        /// Set once done, so a target is a thing that happened rather than a
        /// respawning chore.
        public bool Done;
        public int DoneDay = -1;
    }

    /// The four decisions.
    public class OperationPlan
    {
        public string TargetId;
        public Approach Approach = Approach.Quiet;
        /// 0..23. The hour you go.
        public int Hour = 23;
        /// Crew ids you are bringing. Empty means alone.
        public readonly List<string> Crew = new List<string>();
        public bool Tools;

        public OperationPlan() { }
        public OperationPlan(string targetId) { TargetId = targetId; }

        public OperationPlan Bringing(params string[] ids)
        {
            foreach (var id in ids) if (!string.IsNullOrEmpty(id)) Crew.Add(id);
            return this;
        }
    }

    /// What the game knows when it judges a plan.
    public class OperationState
    {
        /// Competence per crew id, 0..1.
        public readonly Dictionary<string, double> Competence =
            new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        /// Loyalty per crew id, 0..1 — a frightened man talks afterwards.
        public readonly Dictionary<string, double> Loyalty =
            new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        /// The street's talk about the player, 0..1.
        public double Heat;
        /// Whether the player is dressed to not be recognised.
        public bool Coated;
        /// The player's own steadiness, 0..1. Rises with competence per domain.
        public double Nerve = 0.5;

        public double CompetenceOf(string id) =>
            id != null && Competence.TryGetValue(id, out var v) ? v : 0.35;

        public double LoyaltyOf(string id) =>
            id != null && Loyalty.TryGetValue(id, out var v) ? v : 0.5;
    }

    /// A character's estimate of a plan. Never a number the player can see.
    public class PlanRead
    {
        /// How it is put to you, in somebody's voice.
        public string Line = "";
        /// The single thing most likely to go wrong, said plainly.
        public string Worry = "";
        /// Internal only. Never rendered. 0 = certain, 1 = hopeless.
        public double Risk;
        /// Internal only. How many people are likely to see something.
        public double Visibility;
    }

    public class OperationOutcome
    {
        public bool Success;
        /// Got something, but not cleanly. The most interesting result.
        public bool Partial;
        public int Take;
        /// Crew ids who came away rattled enough to talk about it later.
        public readonly List<string> Talkers = new List<string>();
        /// How many strangers saw something. Feeds the gossip mill.
        public int Witnesses;
        public string Line = "";
    }

    public static class Operations
    {
        // ---- reading a plan before you commit to it ----

        public static PlanRead Read(OperationPlan plan, OperationTarget target, OperationState state)
        {
            var read = new PlanRead();
            if (plan == null || target == null || state == null)
            {
                read.Line = "There is nothing here to plan.";
                read.Risk = 1;
                return read;
            }
            if (target.Done)
            {
                read.Line = "That one is already done. There is nothing left in it.";
                read.Risk = 1;
                return read;
            }

            read.Risk = RiskOf(plan, target, state);
            read.Visibility = VisibilityOf(plan, target, state);
            read.Line = RiskWord(read.Risk);
            read.Worry = WorryAbout(plan, target, state, read);
            return read;
        }

        /// The number the player never sees. Every term is a choice they made.
        static double RiskOf(OperationPlan plan, OperationTarget target, OperationState state)
        {
            double risk = target.Difficulty;

            switch (plan.Approach)
            {
                case Approach.Quiet:
                    // Hardest to do, cleanest if done. Leans on your own nerve.
                    risk += 0.18 - 0.30 * state.Nerve;
                    break;
                case Approach.Forced:
                    // Reliable. The risk is not failing, it is being heard.
                    risk -= 0.15;
                    break;
                case Approach.Social:
                    // Free, unless the street already knows who you are.
                    risk += 0.35 * state.Heat - 0.10;
                    break;
            }

            // Hands. Competent hands help; incompetent hands are worse than none,
            // because they still have to be told what to do.
            foreach (var id in plan.Crew)
                risk -= (state.CompetenceOf(id) - 0.35) * 0.28;

            if (plan.Tools) risk -= 0.12;
            // The small hours are quieter but you are slower and colder in them.
            if (plan.Hour >= 2 && plan.Hour < 5) risk += 0.05;

            return Clamp01(risk);
        }

        /// How much of the street is likely to see something.
        static double VisibilityOf(OperationPlan plan, OperationTarget target, OperationState state)
        {
            double vis = target.Exposure * HourDensity(plan.Hour);

            if (plan.Approach == Approach.Forced) vis += 0.30;
            else if (plan.Approach == Approach.Social) vis += 0.10;

            // Everybody you bring is another person standing in a street.
            vis += 0.07 * plan.Crew.Count;
            if (plan.Tools) vis += 0.05;
            if (state.Coated) vis -= 0.20;

            return Clamp01(vis);
        }

        /// How busy the street is at a given hour. Not linear: the small hours
        /// are near-empty, the evening is the worst time to be seen anywhere.
        public static double HourDensity(int hour)
        {
            hour = ((hour % 24) + 24) % 24;
            if (hour >= 2 && hour < 5) return 0.15;
            if (hour >= 5 && hour < 8) return 0.45;
            if (hour >= 8 && hour < 18) return 1.0;
            if (hour >= 18 && hour < 22) return 0.85;
            return 0.40; // 22:00 to 02:00
        }

        /// The approved decision on visible odds: a character's estimate, never a
        /// percentage. If this method ever returns a number, the decision has
        /// been broken.
        public static string RiskWord(double risk) =>
            risk <= 0.18 ? "This is about as safe as this kind of thing gets."
            : risk <= 0.35 ? "This should go all right."
            : risk <= 0.52 ? "This could go either way."
            : risk <= 0.70 ? "This will probably go badly."
            : "This is a bad idea, and saying so out loud does not make it a better one.";

        static string WorryAbout(OperationPlan plan, OperationTarget target, OperationState state, PlanRead read)
        {
            // Name the LARGEST single contributor, so the read teaches the player
            // which of their four decisions to change.
            if (plan.Approach == Approach.Social && state.Heat > 0.5)
                return "Talking your way in only works on people who have not heard of you.";
            if (plan.Approach == Approach.Quiet && state.Nerve < 0.35)
                return "Doing it quietly takes a steadier hand than you have got.";
            if (read.Visibility > 0.6)
                return plan.Hour >= 8 && plan.Hour < 18
                    ? "In broad daylight, half the street will see something."
                    : "Too many people will see this, however it goes.";
            if (plan.Crew.Count > 2)
                return "Four people cannot walk down a street without being four people.";
            var weakest = plan.Crew.OrderBy(state.CompetenceOf).FirstOrDefault();
            if (weakest != null && state.CompetenceOf(weakest) < 0.3)
                return $"{weakest} has never done anything like this.";
            if (plan.Crew.Count == 0 && target.Difficulty > 0.55)
                return "This is not a one-person job.";
            return "Nothing about it is obviously wrong.";
        }

        // ---- doing it ----

        /// Resolves the operation. `roll` is the caller's RNG so the balance lab
        /// can sweep it and the game can seed it per day — the outcome is decided
        /// here, in C#, from state and choices, and never by a model.
        public static OperationOutcome Run(OperationPlan plan, OperationTarget target,
            OperationState state, Func<double> roll)
        {
            var outcome = new OperationOutcome();
            if (plan == null || target == null || state == null || roll == null)
            {
                outcome.Line = "Nothing happened, because there was nothing to do.";
                return outcome;
            }
            if (target.Done)
            {
                outcome.Line = "There is nothing left in it. Somebody already has.";
                return outcome;
            }

            double risk = RiskOf(plan, target, state);
            double vis = VisibilityOf(plan, target, state);
            double r = roll();

            // Three bands, not two. A partial is the interesting result: you got
            // something and left something behind, and the game has somewhere to
            // go afterwards other than "again" or "reload".
            if (r > risk + 0.22)
            {
                outcome.Success = true;
                outcome.Take = target.Payout;
                outcome.Line = plan.Approach == Approach.Quiet
                    ? "It goes the way you planned it, which is rarer than it sounds."
                    : plan.Approach == Approach.Forced
                        ? "It is over in under a minute, and it is not quiet."
                        : "You are inside before anybody thinks to ask twice.";
            }
            else if (r > risk - 0.10)
            {
                outcome.Partial = true;
                outcome.Take = (int)Math.Round(target.Payout * 0.45);
                outcome.Line = "You get most of the way. Most of the way is not all of it, and you leave in a hurry.";
            }
            else
            {
                outcome.Line = "It does not work. You are out of there with nothing and the memory of being nearly caught.";
            }

            // Only a completed job closes the target. A failure leaves it there,
            // harder, which is a consequence rather than a punishment.
            if (outcome.Success || outcome.Partial) target.Done = true;
            else target.Difficulty = Clamp01(target.Difficulty + 0.08);

            // Who saw. Visibility is a rate, not a certainty — and a failure is
            // always more visible than a success, because failing is loud.
            double seen = vis * (outcome.Success ? 0.6 : outcome.Partial ? 1.0 : 1.3);
            outcome.Witnesses = (int)Math.Floor(Clamp01(seen) * 4.0 + (roll() < Clamp01(seen) ? 1 : 0));

            // Your own people. Anyone frightened enough and loyal enough to
            // nobody in particular ends up telling somebody about it.
            foreach (var id in plan.Crew)
            {
                double rattled = (outcome.Success ? 0.15 : outcome.Partial ? 0.4 : 0.65)
                                 * (1.0 - state.LoyaltyOf(id));
                if (roll() < rattled) outcome.Talkers.Add(id);
            }

            return outcome;
        }

        static double Clamp01(double v) => v < 0 ? 0 : v > 1 ? 1 : v;
    }
}
