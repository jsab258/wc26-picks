using System;

namespace Ledger.Core
{
    /// THE THREAD THAT IS STILL OPEN WHEN THE DAY CLOSES.
    ///
    /// WHY THIS EXISTS. `design-doc.md` §4 says the player's "one more day"
    /// comes from three things, the first of which is *"an unresolved thread
    /// every evening — **the sim guarantees one** (a rumor in flight, a recruit
    /// wavering, a date promised)"*. An audit on 2026-08-18 checked every
    /// system the document defines against the code and this was the only
    /// RETENTION claim in the whole design; nothing implemented it, nothing
    /// owned it, and no milestone mentioned it. A promise in the one section
    /// anybody reads to find out whether a game is sticky is the worst place
    /// for a system that does not exist, because it reads as solved.
    ///
    /// WHAT THIS IS AND IS NOT. This picks the thread. It does not CREATE one,
    /// and the difference is the whole honesty of the feature: a guarantee
    /// that works by inventing something when the day was genuinely quiet is a
    /// guarantee about the text, not about the world. So `Tonight` returns
    /// `None` when nothing is open and says so, the run reports how often that
    /// happened, and only a measured count of empty evenings can justify
    /// building the half that plants one. Rule 5b's corollary in advance: a
    /// probe that only fires on a lucky run is not a probe, and the way to fix
    /// that is to plant the condition — but plant it on EVIDENCE, not on the
    /// assumption that evenings are ever empty.
    ///
    /// THE ORDER IS AUTHORED AND THAT IS NOT RULE 2's PROBLEM. Rule 2 forbids
    /// a THRESHOLD invented instead of measured — a number that decides
    /// whether something is TRUE. Nothing here decides truth: every candidate
    /// below is already true when it is offered, and the ranking only decides
    /// which of several true things a player is told about first. That is an
    /// editorial judgement, like `Wardrobe`'s bands, and it is authored on
    /// purpose: the law coming for you outranks an unpaid debt, which outranks
    /// a friend you let down, because that is the order a person in this
    /// situation would actually feel them.
    public static class LooseEnds
    {
        /// What kind of thing is still hanging. Ordered by how loudly it would
        /// keep somebody awake, most first — `CompareTo` on the enum IS the
        /// tiebreak, so adding a kind in the wrong place changes the ranking
        /// and the tests below will say so.
        public enum Kind
        {
            /// Nothing was open. A real answer, reported rather than hidden.
            None = 0,
            /// A detective is asking, and the asking has reached your name.
            Law,
            /// Somebody who works for you is close to walking.
            Crew,
            /// A name in Mickey's book who still owes you.
            ///
            /// THIS TIER WAS WRITTEN THE WRONG WAY ROUND AND THE CODE SAID SO
            /// BEFORE IT SHIPPED. The first version was money the PLAYER owed,
            /// with a due date — a shape borrowed from other games and present
            /// nowhere in this one. `Debtor` is the founding premise's
            /// inheritance and runs the other way: people owe HIM, collection
            /// is social, and the only date involved is when he last asked.
            /// The tribute a patron pays is a daily deduction with no due day
            /// at all. Checking the accessors before wiring is what caught it.
            Owed,
            /// Somebody asked for an evening and has not had it.
            Promise,
            /// A story about you is moving between people.
            Rumour,
            /// Somebody thought less of you at the end of today than at the start.
            Standing,
        }

        /// One open thread, and the sentence a player reads.
        public readonly struct Thread
        {
            public readonly Kind Of;
            /// The person it is about. Empty for threads that are about the
            /// world rather than a person.
            public readonly string Who;
            /// What the day summary shows. Built from the real names and
            /// numbers rather than templated over them, because a line that
            /// says "you have an unresolved matter" is what this feature
            /// exists NOT to be.
            public readonly string Line;

            public Thread(Kind of, string who, string line)
            {
                Of = of;
                Who = who ?? "";
                Line = line ?? "";
            }

            public bool Any => Of != Kind.None;

            public static readonly Thread None = new Thread(Kind.None, "", "");
        }

        /// EVERYTHING THE EVENING COULD BE ABOUT, AS PLAIN DATA.
        ///
        /// A struct of primitives rather than references to the hosts that
        /// hold them, so this is testable without Unity and so Core keeps its
        /// one direction of dependency. The caller assembles it; that is
        /// twenty lines in the Game layer and it is what makes the choosing
        /// provable here.
        public struct Evening
        {
            /// The day that is closing.
            public int Day;

            /// The inquiry's stage, on `Homicide`'s own ladder, and whether
            /// the paper or the detective has reached the player's name. An
            /// inquiry that has not reached you is not YOUR loose end.
            public int InquiryStage;
            public bool InquiryNamesYou;
            public string InquiryAbout;

            /// The largest name still open in Mickey's book, and the day the
            /// player last asked them for it. `-1` is never asked, which is
            /// the loudest version: an inherited debt nobody has been to see.
            public int OwedAmount;
            public string OwedBy;
            public int OwedLastAskedDay;

            /// The crew member closest to walking, and how close. Loyalty runs
            /// 0..1 and `Empire` breaks people below its own floor; the caller
            /// passes that floor rather than this file inventing a second one.
            public string CrewNearestBreaking;
            public double CrewLoyalty;
            public double CrewBreakingPoint;

            /// Who asked for an evening, and the day they asked. The open
            /// city's social calendar already does the asking.
            public string PromisedTo;
            public int PromisedOnDay;

            /// A story about the player that is still moving. `Topic` is the
            /// mill's own topic key, so the line can say what it is about.
            public int RumoursInFlight;
            public string RumourTopic;

            /// The person whose opinion of the player fell furthest today, and
            /// by how much on the 0..1 trust scale.
            public string TrustFell;
            public double TrustFellBy;
        }

        /// A rumour has to be MOVING, not merely to exist. The mill always
        /// holds something; one story still in flight at the end of the day is
        /// the smallest number that means "this is still happening".
        public const int RumoursThatCount = 1;

        /// A fall in somebody's opinion small enough to be a rounding is not a
        /// thread. This is the same 0.05 a payday's skim costs a runner in
        /// `Empire`, taken from there rather than chosen here, so the game has
        /// one idea of what a noticeable change of heart is.
        public const double TrustFallThatCounts = 0.05;

        /// THE ONE ENTRY POINT. Deterministic: the same evening always names
        /// the same thread, because a summary that shuffled between saves
        /// would make the player doubt the one screen that is supposed to be
        /// the day's record.
        public static Thread Tonight(Evening e)
        {
            // Highest kind first, and the enum's own order is the ranking —
            // see the type. Each branch returns immediately, so no candidate
            // can be built and then silently dropped.
            if (e.InquiryStage > 0 && e.InquiryNamesYou)
            {
                var about = string.IsNullOrEmpty(e.InquiryAbout) ? "the business" : e.InquiryAbout;
                return new Thread(Kind.Law, "",
                    $"They are still asking about {about}, and now they are asking about you.");
            }

            if (!string.IsNullOrEmpty(e.CrewNearestBreaking)
                && e.CrewLoyalty <= e.CrewBreakingPoint)
                return new Thread(Kind.Crew, e.CrewNearestBreaking,
                    $"{e.CrewNearestBreaking} did not say much when you paid them.");

            if (e.OwedAmount > 0 && !string.IsNullOrEmpty(e.OwedBy))
            {
                // NEVER ASKED IS THE LOUD ONE, and it is the founding premise
                // sitting untouched: a book of debts the player inherited and
                // has not opened. Asking recently is the quiet one — the thread
                // is still open, but it is waiting on them rather than on you.
                if (e.OwedLastAskedDay < 0)
                    return new Thread(Kind.Owed, e.OwedBy,
                        $"{e.OwedBy} is in Mickey's book for £{e.OwedAmount} and has never been asked.");
                int since = e.Day - e.OwedLastAskedDay;
                if (since <= 0)
                    return new Thread(Kind.Owed, e.OwedBy,
                        $"{e.OwedBy} owes £{e.OwedAmount} and said what they said today.");
                return new Thread(Kind.Owed, e.OwedBy,
                    since == 1
                        ? $"{e.OwedBy} owes £{e.OwedAmount}, and you asked yesterday."
                        : $"{e.OwedBy} owes £{e.OwedAmount}, and you asked {since} days ago.");
            }

            if (!string.IsNullOrEmpty(e.PromisedTo))
            {
                int waited = e.Day - e.PromisedOnDay;
                if (waited <= 0)
                    return new Thread(Kind.Promise, e.PromisedTo,
                        $"{e.PromisedTo} asked whether you were free this week.");
                return new Thread(Kind.Promise, e.PromisedTo,
                    waited == 1
                        ? $"{e.PromisedTo} asked you for an evening yesterday."
                        : $"{e.PromisedTo} asked you for an evening {waited} days ago.");
            }

            if (e.RumoursInFlight >= RumoursThatCount)
            {
                var topic = string.IsNullOrEmpty(e.RumourTopic) ? "you" : e.RumourTopic;
                return new Thread(Kind.Rumour, "",
                    e.RumoursInFlight == 1
                        ? $"Somebody is still telling people about {topic}."
                        : $"{e.RumoursInFlight} people are still telling that story about {topic}.");
            }

            if (!string.IsNullOrEmpty(e.TrustFell) && e.TrustFellBy >= TrustFallThatCounts)
                return new Thread(Kind.Standing, e.TrustFell,
                    $"{e.TrustFell} has been thinking about something you said.");

            // AND THE HONEST ANSWER WHEN THE DAY WAS QUIET. Returning a filler
            // sentence here would satisfy the design document and lie to the
            // player, and it would make the count below meaningless — which is
            // the number that decides whether the planting half is worth
            // building at all.
            return Thread.None;
        }

        /// How many evenings in a run had nothing open. THE DENOMINATOR IS THE
        /// POINT (rule 3b): `emptyEvenings=0` means the guarantee holds, and it
        /// means nothing at all unless the run also says how many evenings it
        /// closed. Both are reported together or neither is.
        /// HOW MANY THREADS WERE OPEN THAT EVENING, not which one won.
        ///
        /// `Tonight` returns on the FIRST tier that fires, in priority order,
        /// which is right — the player gets one thread, the most important one.
        /// It also means the tally can only ever report the winner, and six
        /// evenings of `[Owed:6]` reads as "five of the six tiers are dead"
        /// when what it says is "Mickey's book always has somebody outstanding,
        /// so nothing below Owed can ever be reached".
        ///
        /// Those are completely different facts and only one of them is a bug.
        /// Feeding the lower tiers harder would change nothing visible, which
        /// is why the fix is the READING rather than the code (rule 3b: a
        /// number needs the denominator that makes it mean something).
        ///
        /// Counted rather than returned, because the evening still shows one
        /// thread and this must not change what a player sees.
        public static int OpenCount(Evening e)
        {
            int n = 0;
            if (e.InquiryStage > 0 && e.InquiryNamesYou) n++;
            if (!string.IsNullOrEmpty(e.CrewNearestBreaking)
                && e.CrewLoyalty <= e.CrewBreakingPoint) n++;
            if (e.OwedAmount > 0 && !string.IsNullOrEmpty(e.OwedBy)) n++;
            if (!string.IsNullOrEmpty(e.PromisedTo)) n++;
            if (e.RumoursInFlight >= RumoursThatCount) n++;
            if (!string.IsNullOrEmpty(e.TrustFell) && e.TrustFellBy >= TrustFallThatCounts) n++;
            return n;
        }

        /// How many tiers exist, so `OpenCount` has a ceiling to be read
        /// against. `Kind.None` is not a tier.
        public static int Tiers => Enum.GetValues(typeof(Kind)).Length - 1;

        public sealed class Tally
        {
            public int Evenings { get; private set; }
            public int Empty { get; private set; }
            /// Summed across evenings, not last-wins. An evening's open count
            /// assigned to a field and read at the end of a run describes the
            /// LAST evening, which is the mistake this project has now made
            /// twice with counters written the same day they were read.
            public int OpenSum { get; private set; }
            public int OpenMost { get; private set; }
            readonly int[] _byKind = new int[Enum.GetValues(typeof(Kind)).Length];

            /// WHAT THE CREW LOOKED LIKE ON EACH EVENING, which no
            /// end-of-run number can say.
            ///
            /// The Crew tier has never once been offered across the project's
            /// recorded history. The first measurement of why was taken at the
            /// END of the run and read `crewWorstLoyalty=0.325` against a floor
            /// of 0.400 — the condition MET, and the tier still never fired.
            ///
            /// That looked like a wiring bug and it is not. The Crew branch
            /// sits second, above Owed, so an evening where the condition held
            /// would have beaten the five Owed evenings that did fire. The
            /// condition was therefore false on those evenings and true at the
            /// end: loyalty crosses the floor after the last summary, and one
            /// reading taken at the end cannot see that.
            ///
            /// So the tally records the evenings themselves. `CrewEvenings` is
            /// the denominator — evenings where a crew loyalty could be read at
            /// all — and without it "never below the floor" cannot be told from
            /// "there was no crew yet".
            public int CrewEvenings { get; private set; }
            public int CrewEveningsBelowFloor { get; private set; }
            /// The best and worst an evening ever saw. A single worst cannot
            /// say whether loyalty is drifting down all run or sat flat and
            /// dropped at the end, and those want different work.
            public double CrewBestEvening { get; private set; } = -1;
            public double CrewWorstEvening { get; private set; } = -1;

            public void Saw(Thread t) => Saw(t, 0);

            public void Saw(Thread t, int openTonight)
            {
                Evenings++;
                if (!t.Any) Empty++;
                _byKind[(int)t.Of]++;
                OpenSum += openTonight;
                if (openTonight > OpenMost) OpenMost = openTonight;
            }

            /// The evening's crew reading, recorded whether or not the Crew
            /// tier won. That is the whole point: a tier that loses to a
            /// higher one still had its condition evaluated, and only counting
            /// the winners makes a never-fires tier indistinguishable from a
            /// never-true one.
            ///
            /// `loyalty` below zero means nothing was readable — no crew, or
            /// nobody with an opinion yet — and is counted as an evening with
            /// no reading rather than as a loyal one.
            public void SawCrew(double loyalty, double floor)
            {
                if (loyalty < 0) return;
                CrewEvenings++;
                if (loyalty <= floor) CrewEveningsBelowFloor++;
                if (CrewBestEvening < 0 || loyalty > CrewBestEvening) CrewBestEvening = loyalty;
                if (CrewWorstEvening < 0 || loyalty < CrewWorstEvening) CrewWorstEvening = loyalty;
            }

            /// The crew story as one spaceless value: evenings read, of those
            /// how many were at or below the floor, then best and worst seen.
            public string CrewLine() =>
                CrewEvenings == 0
                    ? "noEveningRead"
                    : $"{CrewEveningsBelowFloor}of{CrewEvenings}"
                      + $"/best{CrewBestEvening:0.000}/worst{CrewWorstEvening:0.000}";

            public int Count(Kind k) => _byKind[(int)k];

            /// One verdict value, and NO SPACES IN IT — the file is
            /// space-separated `key=value` and a value with a space is
            /// silently truncated by every reader in this project.
            public string Line()
            {
                var sb = new System.Text.StringBuilder();
                sb.Append(Evenings).Append('/').Append(Empty).Append("/[");
                bool first = true;
                foreach (Kind k in Enum.GetValues(typeof(Kind)))
                {
                    if (k == Kind.None || Count(k) == 0) continue;
                    if (!first) sb.Append(',');
                    sb.Append(k).Append(':').Append(Count(k));
                    first = false;
                }
                if (first) sb.Append("none");
                sb.Append("]/open");
                // Total then worst, both against the tier ceiling, so
                // "one tier outranked the rest" stops looking like "one
                // tier exists".
                sb.Append(OpenSum).Append('/').Append(OpenMost)
                  .Append("of").Append(Tiers);
                return sb.ToString();
            }
        }
    }
}
