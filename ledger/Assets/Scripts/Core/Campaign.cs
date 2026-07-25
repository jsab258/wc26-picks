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
        public double ExposureThreshold = 0.85;
        public int ExposureFuseDays = 2;          // consecutive hot daily closes to lose
        public double PatienceLossPerMiss = 0.34; // three missed jobs and you're out
        public double PatienceGainPerJob = 0.10;
        public int JobPay = 150;
        public int BarBaseTakings = 120;
        public double HeatTakingsPenalty = 0.85;  // fraction of takings lost at heat 1.0

        public double OutfitPatience { get; private set; } = 1.0;
        public int ExposedStreak { get; private set; }
        public int JobsDone { get; private set; }
        public int JobsMissed { get; private set; }
        public int DaysClosed { get; private set; }
        public Verdict Verdict { get; private set; } = Verdict.Ongoing;
        public string VerdictReason { get; private set; } = "";

        /// The outfit's drop window: late night, spilling past midnight.
        public static bool InJobWindow(GameTime t) => t.Hour >= 22 || t.Hour < 2;

        public void JobDone()
        {
            if (Verdict != Verdict.Ongoing) return;
            JobsDone++;
            OutfitPatience = Math.Min(1.0, OutfitPatience + PatienceGainPerJob);
        }

        public void JobMissed()
        {
            if (Verdict != Verdict.Ongoing) return;
            JobsMissed++;
            OutfitPatience = Math.Max(0.0, OutfitPatience - PatienceLossPerMiss);
            if (OutfitPatience <= 0.0)
            {
                Verdict = Verdict.LostCastOut;
                VerdictReason = "The outfit stopped calling. Then they sent someone.";
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
                    Verdict = Verdict.LostExposed;
                    VerdictReason = "The street stopped guessing and started knowing. The day world closed its doors.";
                    return takings;
                }
            }
            else ExposedStreak = 0;

            if (DaysClosed >= SurviveDays)
            {
                Verdict = Verdict.WonWeek;
                VerdictReason = "Seven days. Both lives intact. For now.";
            }
            return takings;
        }
    }
}
