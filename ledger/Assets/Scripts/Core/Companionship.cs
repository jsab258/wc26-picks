using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// M18. THE PERSON WALKING NEXT TO YOU.
    ///
    /// The roadmap names the version worth building and rules out the other
    /// one in the same sentence: *"`CrewMember` exists as a roster entry;
    /// nobody walks beside you. Somebody accompanying you sees what you do —
    /// which makes them a witness under M16's rules, and that is the
    /// interesting version."*
    ///
    /// SO A COMPANION IS NOT A BUFF. The obvious implementation — a follower
    /// who adds to your intimidation, spots trouble sooner, carries a second
    /// weapon — is a stat with legs, and this project has a rule about those.
    /// The interesting version is that the person who is with you all the time
    /// KNOWS EVERYTHING YOU DID, and the only thing between that knowledge and
    /// the street is how they feel about you.
    ///
    /// AND THE MECHANISM IS ALREADY BUILT, WHICH IS THE TELL THAT IT IS RIGHT.
    /// `Witnesses.Resolve` walks every `NpcWalker` within eighty metres of a
    /// deed and hands each one to `Observe.Resolve`. A companion who physically
    /// follows the player is therefore a witness through the SAME CODE as the
    /// man across the road — standing at two metres, in the light you are in,
    /// facing you, already watching. Nothing here special-cases them into the
    /// witness list, because the whole design is that they do not need it:
    /// they are a full-rung sighting by standing there.
    ///
    /// What this file owns is the two things geometry cannot answer — who
    /// agrees to come, and what leaves with them when they stop.
    ///
    /// THE TRADE, STATED PLAINLY, because it is the reason the feature is worth
    /// its cost. A companion gives you the one thing this game is actually
    /// about: information. They are looking somewhere you are not, so they see
    /// the watchers you missed. And they are the perfect witness to everything
    /// you do. The person who tells you who is watching you is the person who
    /// can tell them what you did — one relationship, both directions, and the
    /// player cannot take one without the other.
    public class Companion
    {
        public string Id;
        public string Name;
        /// The day they started walking with you.
        public int SinceDay;

        /// Set when they stop, with the reason, because a companion who simply
        /// vanished from the roster would be a bug indistinguishable from a
        /// design. `Empire` learnt this the same way: *"betrayal is visible,
        /// never silent"*.
        public bool Departed;
        public string WhyLeft = "";
        public int LeftDay = -1;

        /// THE EVENT IDS THEY STOOD NEXT TO YOU FOR.
        ///
        /// Ids and not `Observation`s, deliberately. The observation belongs to
        /// the witness record that `Witnesses.Resolve` already produced for
        /// them; storing a second copy here would be two sources for one fact,
        /// which is how the wet-road threshold drifted from itself. This is an
        /// index into what already exists.
        ///
        /// BOUNDED, for the reason `SuspicionTracker.Reasons` and
        /// `Dependent.Grievances` are: an accumulating list with no ceiling is
        /// a leak, and the soak found the last one at 684 entries over 499
        /// days. Twenty-four is a fortnight of nights with something happening
        /// on each of them, which is more than any real run.
        public const int MaxCarried = 24;
        public IReadOnlyList<string> Witnessed => _witnessed;
        readonly List<string> _witnessed = new List<string>();

        /// ONCE EACH. A deed resolves against every witness every time it is
        /// re-resolved, and a companion present for one killing must not read
        /// as present for six. `MemoryStore.Append` does not deduplicate — I
        /// checked, because the last time I asserted it did it was false — so
        /// the check lives here where the set is small and the key is exact.
        public void Saw(string eventId)
        {
            if (string.IsNullOrEmpty(eventId)) return;
            if (_witnessed.Contains(eventId)) return;
            _witnessed.Add(eventId);
            if (_witnessed.Count > MaxCarried) _witnessed.RemoveAt(0);
        }

        /// Save-load overlay: state only.
        public void Restore(int sinceDay, bool departed, string why, int leftDay)
        {
            SinceDay = Math.Max(0, sinceDay);
            Departed = departed;
            WhyLeft = why ?? "";
            LeftDay = leftDay;
        }
    }

    /// The rules of walking with somebody.
    ///
    /// NOTE WHAT IS NOT IN HERE: no spotting chance, no detection bonus, no
    /// radius. Rule 2 of this project is that a threshold you have not measured
    /// is not allowed, and the honest way to obey it was not to invent numbers
    /// and print a series — it was to notice that the question already has an
    /// answer. Whether a companion sees a watcher is `Perception`'s job, from
    /// where the companion is standing and which way they are facing, exactly
    /// as it is for everybody else in the city. That makes WHERE THEY WALK a
    /// real thing rather than a modifier, and it adds no constant at all.
    public static class Escort
    {
        /// Nobody goes out on a night's work beside somebody they do not
        /// trust. TAKEN, NOT PICKED: `Empire.RecruitLoyaltyFloor` is 0.55 and
        /// means "the need route ends in a yes only past this" — which is the
        /// same question in different clothes. Saying yes to walking into a
        /// night with you is saying yes to you.
        public const double WalksWithYouAbove = 0.55;

        /// And where they stop. THE SAME LINE THE GAME ALREADY DRAWS TWICE:
        /// `Empire.PoachLoyaltyFloor` 0.4 ("below this, a poached crew member
        /// walks") and `Household.TalkFreely` 0.40 ("the point at which
        /// somebody stops being yours"). A companion crossing it is both at
        /// once — they walk, and they talk, and they are the best-informed
        /// witness in the game when they do.
        ///
        /// The gap between the two constants is deliberate and is not slack:
        /// it is hysteresis. Without it a crew member hovering on the line
        /// would join and leave every night, which reads as a bug and is a
        /// worse story than either state.
        public const double WalksAwayBelow = 0.40;

        /// Will they come out with you tonight.
        ///
        /// Nerve is in it because accompanying somebody to do something is not
        /// the same as approving of it — a loyal coward stays in the bar, and
        /// that is a character rather than a failure. Same shape as
        /// `Empire.Competence`, which reads nerve and loyalty together.
        public static bool WillWalk(double loyalty, double nerve, bool departed = false) =>
            !departed && loyalty >= WalksWithYouAbove && nerve >= 0.3;

        /// Whether the one walking with you has stopped being yours.
        public static bool WalksAway(double loyalty) => loyalty < WalksAwayBelow;

        /// WHAT THEY SEE THAT YOU DO NOT — as a set difference, not a chance.
        ///
        /// The caller resolves both sightlines through the ordinary perception
        /// model: who is visible from the player's position and facing, and who
        /// is visible from the companion's. This is only the subtraction, and
        /// it is in Core because it is the part with a rule in it — the report
        /// is what they add, never the whole list. A companion who told you
        /// everything you could already see would be a HUD element.
        public static IEnumerable<string> Adds(IEnumerable<string> youSaw,
                                               IEnumerable<string> theySaw)
        {
            var mine = new HashSet<string>(youSaw ?? Enumerable.Empty<string>());
            return (theySaw ?? Enumerable.Empty<string>())
                   .Where(w => !string.IsNullOrEmpty(w) && !mine.Contains(w))
                   .Distinct();
        }

        /// WHAT WALKS OUT OF THE DOOR WITH THEM.
        ///
        /// The whole point of the milestone in one call. When a companion
        /// crosses the line, this is the list of things they were standing next
        /// to you for — and every one of them is already an `Observation` in
        /// the witness record at full rung, because they were at two metres in
        /// your light facing you. Nothing needs to be manufactured at the
        /// moment of betrayal; it has been accumulating the whole time, which
        /// is exactly why it is frightening rather than punitive.
        public static IReadOnlyList<string> CarriesAway(Companion c) =>
            c == null ? Array.Empty<string>() : c.Witnessed;

        /// How exposed the player is to one companion, for the endings matrix.
        ///
        /// REPORTED, NOT FED BACK — the same rule `Household.MeanBond` carries.
        /// Nothing in the simulation reads this. It exists so a run can be
        /// JUDGED, and if a future ending calculation consumes it directly then
        /// the relationship has become a stat again and M18's done-condition
        /// has been quietly failed.
        public static int Exposure(Companion c) => c == null ? 0 : c.Witnessed.Count;
    }
}
