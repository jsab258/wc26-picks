using System.Collections.Generic;

namespace Ledger.Core
{
    /// WHO IS IN, AT AN HOUR — and therefore which windows are lit.
    ///
    /// THE NIGHT SKYLINE IS A WALL OF IDENTICAL CREAM RECTANGLES, which is what
    /// `review_day1_night` shows and the first thing the eye goes to.
    /// `WorldBuilder.SetWindowsLit` walks every window in the city and writes
    /// one emissive colour to all of them, so after dusk every flat in seven
    /// districts is occupied and equally bright.
    ///
    /// THE FIX IS NOT A JITTER. A random lit/unlit pattern would look better
    /// and mean nothing, and this project has a name for that — a system built,
    /// plausible, and saying nothing. A lit window means SOMEBODY IS IN. That
    /// is the information pillar rather than decoration: a dark window at an
    /// address you know is a fact about where somebody is, and the moat this
    /// game is chasing is information 90 against a best-in-class of 65.
    ///
    /// EVERYTHING HERE COMES FROM FIELDS THAT ALREADY EXIST. `Resident` carries
    /// `WorkFromHour`, `WorkToHour` and `Circle`, authored when the population
    /// is generated. Nothing new is invented about a person; this only asks the
    /// question nobody had asked of them.
    ///
    /// ON AUTHORED HOURS RATHER THAN MEASURED ONES. `OutFrom`/`OutTo` are
    /// picked, and that is allowed for the same reason `Wardrobe`'s bands are
    /// authored rather than sampled: they are a statement about what a place is
    /// like, not a threshold applied to a measurement. Rule 2 forbids inventing
    /// a bound that a run could have told me; it does not forbid deciding that
    /// a port town's night circle is out from seven. What a run must tell me is
    /// the RESULT — `HomeFraction` is measured over the real population every
    /// hour, and the verdict prints it, so "most of the city is in at three in
    /// the morning" is checkable rather than assumed.
    public static class Occupancy
    {
        /// When the night circle goes out, and when it comes back.
        ///
        /// `Population` already sorts residents into "day", "night" and "both"
        /// circles and uses it to decide who hears what; this is the same fact
        /// applied to where they physically are. A day-circle person is out
        /// while working and in otherwise, which needs no constant at all —
        /// these two exist only for the people the population has already
        /// labelled as out after dark.
        public const int OutFrom = 19;
        public const int OutTo = 1;

        /// Is this person's home occupied at this hour?
        ///
        /// THREE STATES COLLAPSED TO ONE QUESTION, deliberately. Asleep and
        /// awake are the same answer to "is the window lit" only if you assume
        /// people sleep in the dark, which they do — so the sleep window is
        /// where this would grow next, and it is left out rather than guessed
        /// because a run cannot currently tell me whether a city that goes dark
        /// at 1am reads as a city or as a power cut. That is a still's
        /// question and the still does not exist yet.
        public static bool AtHome(Resident r, int hour)
        {
            if (r == null) return false;
            int h = ((hour % 24) + 24) % 24;

            // AT WORK. The window is theirs and they are not behind it.
            // Handles a shift that crosses midnight, because `Population`
            // generates night trades and a from > to is how it says so.
            if (Spans(r.WorkFromHour, r.WorkToHour, h)) return false;

            // OUT. Only for the circles the population has already marked as
            // night people — a day-circle resident who is not at work is in.
            if ((r.Circle == "night" || r.Circle == "both") && Spans(OutFrom, OutTo, h))
                return false;

            return true;
        }

        /// Does an hour fall inside a window that may cross midnight?
        ///
        /// ONE IMPLEMENTATION, because a second copy of this is precisely how
        /// two systems come to disagree about what "night" means — the fault
        /// this project names more than any other. Half-open at the end so a
        /// shift 9-18 and a shift 18-2 do not both claim 18:00.
        public static bool Spans(int from, int to, int hour)
        {
            int f = ((from % 24) + 24) % 24;
            int t = ((to % 24) + 24) % 24;
            int h = ((hour % 24) + 24) % 24;
            if (f == t) return false;
            return f < t ? (h >= f && h < t) : (h >= f || h < t);
        }

        /// What share of the city is in, at this hour. 0..1, and -1 when there
        /// is nobody to ask — which is a different finding from "nobody is
        /// home" and must not render as a dark city.
        public static double HomeFraction(IReadOnlyList<Resident> residents, int hour)
        {
            if (residents == null || residents.Count == 0) return -1;
            int home = 0;
            for (int i = 0; i < residents.Count; i++)
                if (AtHome(residents[i], hour)) home++;
            return (double)home / residents.Count;
        }

        /// Should THIS window be lit, given that share?
        ///
        /// DETERMINISTIC PER WINDOW, so a flat does not flicker between frames
        /// and a player can learn that the third window along is dark on
        /// Tuesdays. A random draw per frame would be the same fraction and a
        /// completely different thing — noise rather than information — and
        /// nothing in a screenshot could tell them apart.
        ///
        /// NOT AN ADDRESS. The honest version is that this window belongs to
        /// that resident, and it needs an address system the game does not
        /// have: `Resident.HomeX/HomeZ` are placed by the population generator
        /// and the buildings are placed by `WorldBuilder`, with nothing tying
        /// them together. So the FRACTION is real and measured, and WHICH
        /// windows carry it is a stable hash. Said plainly here because a
        /// future reader will otherwise assume the mapping is meaningful and
        /// build a mechanic on it — the same way the door system got built
        /// twice.
        public static bool WindowLit(string windowId, double homeFraction)
        {
            if (homeFraction < 0) return true;
            return Physique.Fraction(windowId ?? "", 31) < homeFraction;
        }
    }
}
