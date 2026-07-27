using System;

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
            OutfitPatience = patience;
            ExposedStreak = exposedStreak;
            JobsDone = jobsDone;
            JobsMissed = jobsMissed;
            DaysClosed = daysClosed;
            Verdict = verdict;
            VerdictReason = reason ?? "";
        }

        public void JobDone()
        {
            if (Verdict != Verdict.Ongoing) return;
            JobsDone++;
            OutfitPatience = Math.Min(1.0, OutfitPatience + PatienceGainPerJob);
        }

        public void JobMissed()
        {
            if (Verdict != Verdict.Ongoing || OutfitCutOff) return;
            JobsMissed++;
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
