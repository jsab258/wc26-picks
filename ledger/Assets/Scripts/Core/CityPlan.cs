using System.Linq;

namespace Ledger.Core
{
    /// THE CITY'S SHAPE, IN ONE PLACE, BECAUSE IT WAS IN TWO.
    ///
    /// `PopulationHost` held the district list and the home/work shares, and
    /// `Recurrence` held a copy under a comment reading: *"copied from
    /// `PopulationHost` because that class is Unity-side and cannot be linked
    /// here. If these drift, the tool is measuring a city the game does not
    /// build — so they are asserted below."*
    ///
    /// **There was no assertion.** Not one, anywhere in that file. A comment
    /// naming a risk and promising a guard against it, with no guard — which is
    /// the exact shape rule 1's second corollary is about, and the seventh
    /// instrument fault found in a single day.
    ///
    /// It matters more than a stale comment usually would, because two live
    /// decisions were taken off that tool this afternoon: cutting the city to
    /// three districts, and sizing the named cast at about fifty. Both would
    /// have been measurements of a city nobody was building, and nothing would
    /// have said so.
    ///
    /// The fix is not to add the missing assertion. Two copies that agree today
    /// are two copies, and a test that they still match is a test that somebody
    /// remembered to update both. There is one copy now, in Core, which the
    /// engine-free tools link directly and `PopulationHost` reads — so the
    /// classes of fault that comment worried about cannot occur rather than
    /// being detected after the fact.
    ///
    /// SHARES ARE PARTS, NOT PERCENTAGES. They are fed to `Population.Spread`,
    /// which builds a weighted wheel, so only their ratios matter. They are
    /// written to total 100 because that makes them readable as percentages,
    /// and `Balanced` checks it — not because anything requires it.
    public static class CityPlan
    {
        /// Seven districts (M14). The shares carry the §7 characters: Fairview
        /// HOUSES people and employs almost nobody, Ironside and the Exchange
        /// are the inverse, the Parade's workforce keeps night hours, and
        /// Gullwing is nearly empty both ways — that emptiness is its mechanic.
        ///
        /// Ironside is the reason there are two lists at all. It houses about
        /// one person in twenty-five and employs one in five, so it is busy at
        /// noon and all but empty after dark, which is what "places without
        /// witnesses" has to mean if it is going to mean anything.
        public static readonly string[] Districts =
            { "the Hook", "Copper Row", "Ironside", "the Exchange", "the Parade", "Fairview", "Gullwing" };

        public static readonly int[] HomeShares = { 30, 28, 4, 3, 6, 22, 7 };
        public static readonly int[] WorkShares = { 24, 22, 20, 16, 9, 3, 6 };

        /// The seed and headcount the game builds with. Here for the same
        /// reason as the shares: `Recurrence` had its own copies of both, and a
        /// tool measuring a different population from a different seed is
        /// measuring a different city while reporting on this one.
        public const int Seed = 20260726;
        public const int Count = 700;

        /// The two districts that already house 58% of the city and employ 46%
        /// of it, and the three that were chosen over them on the evidence: a
        /// full week gives 47.4 distinct faces at three against 53.6 at two,
        /// and — the number that actually decided it — 9.9 people met more than
        /// once against 10.1. The second cut buys six more strangers and two
        /// tenths of a recurring face, and recurrence is the whole quantity a
        /// town-you-learn is made of.
        public static readonly int[] KeepTwo = { 0, 1 };
        public static readonly int[] KeepThree = { 0, 1, 2 };

        /// Every list the same length, and the shares readable as percentages.
        /// Cheap, and it is the one thing a hand-edited table gets wrong: a
        /// district appended to one array and not the others silently shifts
        /// every share after it onto the wrong place.
        public static bool Balanced =>
            Districts.Length == HomeShares.Length
            && Districts.Length == WorkShares.Length
            && HomeShares.Sum() == 100 && WorkShares.Sum() == 100;
    }
}
