using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    public enum Verdict { Ongoing, WonWeek, LostExposed, LostCastOut }

    /// The week-long double-life campaign as a pure state machine: a nightly outfit
    /// job (miss too many and you're cast out), daily bar takings taxed by street
    /// heat, and an exposure fuse — sustained heat across consecutive days, not a
    /// single spike, is what ends you, so there is always one day to fight back.
    /// No Unity, no LLM; fully unit-testable.
    public class Campaign
    {
        // Playtest knobs.
        public int SurviveDays = 7;
        // 0.70 is where the HUD starts calling the street "hostile" — the lose rule
        // reads as: two mornings in a row of a hostile street and you're done.
        public double ExposureThreshold = 0.70;
        public int ExposureFuseDays = 2;          // consecutive hot daily closes to lose
        public double PatienceLossPerMiss = 0.34; // three missed jobs and you're out
        public double PatienceGainPerJob = 0.10;
        // The bar is the livelihood; the night job is an obligation with a stipend.
        // That ratio is what makes the heat tax (and therefore bribes) worth money:
        // a hot street costs real income, not pocket change next to the night pay.
        public int JobPay = 90;
        public int BarBaseTakings = 220;
        public double HeatTakingsPenalty = 0.85;  // fraction of takings lost at heat 1.0

        public double OutfitPatience { get; private set; } = 1.0;
        public int ExposedStreak { get; private set; }
        public int JobsDone { get; private set; }
        public int JobsMissed { get; private set; }
        public int DaysClosed { get; private set; }
        public Verdict Verdict { get; private set; } = Verdict.Ongoing;
        public string VerdictReason { get; private set; } = "";

        // Open mode (open-city-spec.md, approved 2026-07-26): from day 8 the
        // campaign stops being survivable and starts being ownable. No win state;
        // losing is still possible but scarring, never terminal — the fuse
        // triggers a Fall (arrest, prison days, the city updates) instead of an
        // ending, and outfit patience running out cuts you off instead of
        // casting you out.
        public bool OpenMode { get; private set; }
        public bool OutfitCutOff { get; private set; }
        public bool FallPending { get; private set; }
        public int Falls { get; private set; }

        /// Day 8: the week is won, the posture is spoken, the counting stops.
        public void EnterOpenMode()
        {
            if (Verdict != Verdict.WonWeek) return;
            OpenMode = true;
            Verdict = Verdict.Ongoing;
            VerdictReason = "";
            ExposedStreak = 0;
        }

        /// The world has staged the Fall the fuse demanded; the books reopen.
        public void ConsumeFall()
        {
            if (!FallPending) return;
            FallPending = false;
            Falls++;
            ExposedStreak = 0;
        }

        /// Self-test hook: stage a Fall without waiting for two hot closes.
        public void ForcePendingFall()
        {
            if (OpenMode && Verdict == Verdict.Ongoing) FallPending = true;
        }

        /// Self-test hook: open the city without having earned it.
        ///
        /// The CI bot is not a player, and its job is not to DESERVE the open
        /// city — it is to exercise it. A run that loses the week on day six
        /// leaves every gate past day eight inert (the empire, the Director,
        /// operations, both later acts), and the build goes green having proven
        /// the first six days twice. That happened, silently, and the only
        /// reason it was caught is that somebody read the numbers under a green
        /// tick.
        ///
        /// Never called from the game. `EnterOpenMode` is the real door and it
        /// still requires the week to have been won.
        public void ForceOpenMode()
        {
            OpenMode = true;
            Verdict = Verdict.Ongoing;
            VerdictReason = "";
            ExposedStreak = 0;
        }

        /// Save-load overlay for the open-mode fields (additive; old saves default off).
        public void RestoreOpen(bool openMode, bool outfitCutOff, bool fallPending, int falls)
        {
            OpenMode = openMode;
            OutfitCutOff = outfitCutOff;
            FallPending = fallPending;
            Falls = falls;
        }

        /// The outfit's drop window: late night, spilling past midnight.
        public static bool InJobWindow(GameTime t) => t.Hour >= 22 || t.Hour < 2;

        /// Save-load overlay: state only, rules unchanged.
        public void Restore(double patience, int exposedStreak, int jobsDone, int jobsMissed,
            int daysClosed, Verdict verdict, string reason)
        {
            // COUNTS CANNOT BE NEGATIVE, whatever the file says.
            //
            // A save carrying `"jobsMissed": -1e308` restored to minus two
            // billion missed jobs — `SaveChaos` found fifteen of these in a
            // run. Every comparison downstream reads `JobsMissed >= n` to
            // decide whether the outfit has lost patience, so a large negative
            // does not merely look wrong: it makes the outfit permanently,
            // silently forgiving, which is the failure this whole campaign
            // layer exists to produce the opposite of.
            //
            // Clamped rather than refused, because unlike the day these have a
            // correct floor and a save is not unreadable for having a bad one.
            // PATIENCE IS A 0..1 QUANTITY and this is the only door into it
            // that did not say so. `JobDone` caps it at 1.0 and `JobMissed`
            // floors it at 0.0 — the invariant is the class's own, restated
            // here rather than invented, because restore had been the one path
            // that bypassed both. A save reading `"patience": 0.659e999999999`
            // parses to Infinity, and `SaveChaos` restored one: at Infinity
            // the `<= 0.0` cut-off on line 142 can never fire and the outfit
            // never loses patience with the player again.
            OutfitPatience = double.IsNaN(patience) ? 0.0 : Math.Min(1.0, Math.Max(0.0, patience));
            ExposedStreak = Math.Max(0, exposedStreak);
            JobsDone = Math.Max(0, jobsDone);
            JobsMissed = Math.Max(0, jobsMissed);
            DaysClosed = Math.Max(0, daysClosed);
            Verdict = verdict;
            VerdictReason = reason ?? "";
        }

        /// WHICH NIGHTS, NOT JUST HOW MANY.
        ///
        /// M21's competence axis is explicit that there is NO EGO METER: growth
        /// is "a run of individually reasonable decisions that compound", and
        /// the design note's own example is *"miss tonight because this job
        /// matters, and that is the sixth night running"*. The game already
        /// punishes it. What it could not do was SAY it — `JobsMissed` is a
        /// total, and a total cannot tell one bad week from six nights in a row.
        ///
        /// So the days are kept. This is the smallest possible brick of that
        /// axis and it needs no new system: two call sites already know the
        /// date, and everything downstream reads a list instead of inventing a
        /// meter.
        ///
        /// Bounded, because a save is a file somebody can hand-edit and a
        /// hundred-day open city should not carry a hundred-entry array for a
        /// question that only ever looks at the recent past.
        public const int NightsRemembered = 14;
        readonly List<int> _missedNights = new List<int>();
        readonly List<int> _doneNights = new List<int>();
        public IReadOnlyList<int> MissedNights => _missedNights;
        public IReadOnlyList<int> DoneNights => _doneNights;

        static void Remember(List<int> nights, int day)
        {
            if (day < 0 || nights.Contains(day)) return;
            nights.Add(day);
            while (nights.Count > NightsRemembered) nights.RemoveAt(0);
        }

        /// How many drops you have missed since the last one you delivered.
        ///
        /// NAMED FOR WHAT IT COUNTS, and the first draft was not. It was called
        /// a "run" and its comment said it stopped at the first gap — but a
        /// night with no drop posted is skipped rather than breaking the count,
        /// deliberately, because after a cut-off the outfit posts nothing and
        /// counting silence as failure would say "eleven nights running" to a
        /// player nobody had asked. Skipping silence is right; calling the
        /// result a consecutive run was not, and the two disagreed by exactly
        /// the case the comment used as its example.
        ///
        /// So: walk back from `today` through the remembered window, count
        /// missed nights, and STOP at a delivered one. Missed four, delivered
        /// one, missed two reads as two. That is the sentence the ledger wants.
        public int MissedSinceLastDelivery(int today)
        {
            int missed = 0;
            for (int day = today; day > today - NightsRemembered && day >= 0; day--)
            {
                if (_doneNights.Contains(day)) break;
                if (_missedNights.Contains(day)) missed++;
            }
            return missed;
        }

        /// The nights, from a save. Separate from `Restore` because that one
        /// takes seven positional arguments already and an eighth and ninth
        /// would be two more places to pass the wrong list.
        ///
        /// CLAMPED AND DEDUPED THROUGH THE SAME DOOR the live path uses, so a
        /// hand-edited file cannot plant a hundred nights or a negative day.
        /// `SaveChaos` throws malformed values at every field in this class and
        /// the ones that survived it did so by having exactly one way in.
        public void RestoreNights(IEnumerable<object> missed, IEnumerable<object> done)
        {
            _missedNights.Clear();
            _doneNights.Clear();
            if (missed != null)
                foreach (var o in missed) if (o is double d) Remember(_missedNights, (int)d);
            if (done != null)
                foreach (var o in done) if (o is double d) Remember(_doneNights, (int)d);
        }

        public void JobDone(int day = -1)
        {
            if (Verdict != Verdict.Ongoing) return;
            JobsDone++;
            Remember(_doneNights, day);
            OutfitPatience = Math.Min(1.0, OutfitPatience + PatienceGainPerJob);
        }

        public void JobMissed(int day = -1)
        {
            if (Verdict != Verdict.Ongoing || OutfitCutOff) return;
            JobsMissed++;
            Remember(_missedNights, day);
            OutfitPatience = Math.Max(0.0, OutfitPatience - PatienceLossPerMiss);
            if (OutfitPatience <= 0.0)
            {
                // In the week, exhausted patience ends you. In the open city it
                // ends the arrangement: no more drops, no more pay — and, later,
                // an outfit with reasons of its own (Empire v1's rival).
                if (OpenMode) OutfitCutOff = true;
                else
                {
                    Verdict = Verdict.LostCastOut;
                    VerdictReason = "The outfit stopped calling. Then they sent someone.";
                }
            }
        }

        /// Daily close (the bar's morning open): bank yesterday's takings shrunk by
        /// street heat, advance the exposure fuse, and check for the week won.
        /// Returns the takings banked.
        public int CloseDay(double dayHeat)
        {
            if (Verdict != Verdict.Ongoing) return 0;
            DaysClosed++;
            double h = Math.Clamp(dayHeat, 0.0, 1.0);
            int takings = (int)Math.Round(BarBaseTakings * Math.Max(0.0, 1.0 - HeatTakingsPenalty * h));

            if (h >= ExposureThreshold)
            {
                ExposedStreak++;
                if (ExposedStreak >= ExposureFuseDays)
                {
                    // Open mode: the same fuse stages a Fall — arrest, days lost,
                    // the city updated — never an ending (P5: the city's state is
                    // the save file, and an ending screen contradicts an open game).
                    if (OpenMode) FallPending = true;
                    else
                    {
                        Verdict = Verdict.LostExposed;
                        VerdictReason = "The street stopped guessing and started knowing. The day world closed its doors.";
                        return takings;
                    }
                }
            }
            else ExposedStreak = 0;

            if (!OpenMode && DaysClosed >= SurviveDays)
            {
                Verdict = Verdict.WonWeek;
                VerdictReason = "Seven days. Both lives intact. For now.";
            }
            return takings;
        }
    }
}
