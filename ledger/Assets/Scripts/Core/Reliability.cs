namespace Ledger.Core
{
    /// WHAT THE STREET SAYS ABOUT SOMEBODY WHO KEEPS NOT TURNING UP.
    ///
    /// `Campaign.MissedSinceLastDelivery` counts drops the player was posted
    /// and did not deliver, carefully — it skips nights the outfit posted
    /// nothing, because counting silence as failure would tell a player they
    /// had failed eleven nights nobody asked them to work. It has exactly ONE
    /// consumer: a line on the ledger screen. It closes nothing, and the
    /// roadmap's competence row says so in its own words — *"the first two
    /// bricks are visible (missed nights, skimmed envelopes) but neither yet
    /// closes anything."*
    ///
    /// THE CONSEQUENCE IS SOCIAL, NOT ECONOMIC, AND THAT IS A DELIBERATE
    /// CHOICE RATHER THAN THE EASY ONE. The obvious move is to make the outfit
    /// pay less or stop posting drops. Both are cliffs, and the second one is
    /// worse than a cliff: the sim's `jobRan` gate exists to prove a drop can
    /// be made end to end, the bot already completes them rarely, and a rule
    /// that stopped posting them would turn a struggling gate into a
    /// permanently red one — a guard blocking the case it exists to check,
    /// which is the fault this project has recorded four times in one day.
    ///
    /// What a missed drop actually costs is that people talk. That is the
    /// moat — social memory 93 against a best-in-class of 60 — and it is the
    /// half of consequence this game is supposed to be better at than anybody.
    /// A reputation for not turning up is also the honest precondition for any
    /// LATER economic consequence: the outfit should stop offering work because
    /// word got round, not because a counter crossed a line.
    ///
    /// NOTHING HERE INVENTS A NUMBER FOR "UNRELIABLE". The thresholds below are
    /// the only decision, they are authored like `Wardrobe`'s bands rather than
    /// tuned against a measurement, and they say what a small outfit is like:
    /// one miss is a bad night, three is a pattern, and it takes a delivery to
    /// clear it because `MissedSinceLastDelivery` already stops counting at one.
    public static class Reliability
    {
        /// One missed drop is an accident. Below this nobody says anything —
        /// and saying nothing is a decision, because a street that comments on
        /// every single lapse is a street with no sense of proportion and the
        /// player learns to ignore it.
        public const int TalkedAboutAt = 2;

        /// And this is where it stops being bad luck. A rumour at this level
        /// carries higher confidence because more people have seen the same
        /// thing — which is the mill's own rule, not a new one.
        public const int PatternAt = 4;

        public enum Standing { Fine, Slipping, Unreliable }

        public static Standing Of(int missedSinceLastDelivery)
        {
            if (missedSinceLastDelivery >= PatternAt) return Standing.Unreliable;
            if (missedSinceLastDelivery >= TalkedAboutAt) return Standing.Slipping;
            return Standing.Fine;
        }

        /// How sure the street is, on the mill's 0..1 scale.
        ///
        /// RISES WITH THE COUNT because confidence is what actually differs: a
        /// man who missed two nights is a man somebody noticed, and a man who
        /// missed six is a man everybody agrees about. This is the same shape
        /// the racket rumour uses — `0.45 + 0.35 * (1 - competence)` — and the
        /// floor is deliberately the same 0.45, so a first mention of
        /// unreliability is worth exactly what a first mention of a racket is
        /// and the two cannot drift into disagreeing about what hearsay means.
        public const double FirstMention = 0.45;

        public static double Confidence(int missed)
        {
            if (missed < TalkedAboutAt) return 0;
            double over = missed - TalkedAboutAt;
            double span = System.Math.Max(1, PatternAt - TalkedAboutAt);
            return Feel.Clamp01(FirstMention + 0.35 * Feel.Clamp01(over / span));
        }

        /// The fact the street ends up holding. ONE predicate, so a second
        /// person hearing it CORROBORATES rather than starting a second story
        /// — the distinction `GossipMill.DayCircleHeat` is built on and the
        /// reason `Press` was made to reuse the witness's key rather than
        /// invent its own.
        public static Fact ContentFor(Standing s) =>
            new Fact("player", "unreliable", s == Standing.Unreliable ? "badly" : "yes");

        public static string SummaryFor(Standing s, int missed) =>
            s == Standing.Unreliable
                ? $"the publican has not shown up for {missed} runs — nobody is holding a parcel for him now"
                : $"the publican missed {missed} runs; people are starting to say it";
    }
}
