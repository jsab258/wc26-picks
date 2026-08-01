using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// M18. THE PEOPLE WHOSE WEEK IS WORSE WHEN YOURS IS.
    ///
    /// The roadmap's case for this milestone is the sharpest sentence in the
    /// document: *"A belief network is only frightening if the people in it are
    /// people you would miss. The game can currently model the street knowing
    /// you are a criminal, and cannot model anybody being at home waiting for
    /// you. Every consequence the moat produces lands on nothing."*
    ///
    /// THE DONE-CONDITION IS THE DESIGN CONSTRAINT, and it is unusually strict:
    /// *a run where the player never goes home is measurably worse in the
    /// endings matrix than one where they do — and the difference comes from
    /// RELATIONSHIPS rather than from a stat.*
    ///
    /// That rules out the obvious implementation. A `HomeComfort` number that
    /// feeds the ending calculation would satisfy "measurably worse" and fail
    /// the clause that matters: it would be a stat wearing a family's clothes,
    /// and the player would learn to top it up like a fuel gauge.
    ///
    /// So neglect does not have a number of its own that anything reads.
    /// A dependent who is not seen becomes a WORSE-DISPOSED MEMBER OF THE
    /// SOCIAL GRAPH — their loyalty falls, and loyalty is what `GossipMill`
    /// already consults when deciding who repeats what about you. The
    /// consequence of not going home is that the people closest to you become
    /// the people most willing to talk about you, through the exact machinery
    /// that already governs everybody else.
    ///
    /// That is also why it is frightening rather than merely costly: the
    /// witness who can hurt you most is the one who knows where you were on
    /// the nights nobody else can account for.
    public class Dependent
    {
        public string Id;
        public string Name;
        /// What they are to the player, for the writing. Not mechanical.
        public string Relation = "";

        /// 0..1. How much of themselves they still give you. Falls with
        /// absence, recovers with presence, and is the ONLY thing this class
        /// exports into the wider game — deliberately, because the moment it
        /// exports a second number somebody will balance against the second one.
        public double Bond { get; private set; } = 0.75;

        /// 0..1. How their own week is going, which is money and safety and
        /// not the player's attention. Kept separate from `Bond` because a
        /// dependent can be well provided for and still not see you, and that
        /// combination is the whole subject of this milestone.
        public double Condition { get; private set; } = 0.6;

        /// The last day the player was under the same roof at night.
        public int LastSeenDay { get; private set; } = 0;

        /// What they would say about it, oldest first, capped.
        ///
        /// BOUNDED FOR THE REASON `SuspicionTracker.Reasons` WAS: an
        /// accumulating list with no reader and no ceiling is a leak, and the
        /// soak found the last one at 684 entries over 499 days. Six is what a
        /// person actually brings up.
        public const int MaxGrievances = 6;
        public IReadOnlyList<string> Grievances => _grievances;
        readonly List<string> _grievances = new List<string>();

        internal void Note(string line)
        {
            _grievances.Add(line);
            if (_grievances.Count > MaxGrievances) _grievances.RemoveAt(0);
        }

        internal void SetBond(double v) => Bond = Math.Clamp(v, 0.0, 1.0);
        internal void SetCondition(double v) => Condition = Math.Clamp(v, 0.0, 1.0);
        internal void Seen(int day) => LastSeenDay = day;

        /// Save-load overlay: state only.
        public void Restore(double bond, double condition, int lastSeenDay)
        {
            Bond = Math.Clamp(bond, 0.0, 1.0);
            Condition = Math.Clamp(condition, 0.0, 1.0);
            LastSeenDay = Math.Max(0, lastSeenDay);
        }
    }

    /// The home and the people in it.
    public class Household
    {
        readonly List<Dependent> _people = new List<Dependent>();
        public IReadOnlyList<Dependent> People => _people;

        public void Add(Dependent d) { if (d != null) _people.Add(d); }
        public Dependent ById(string id) =>
            id == null ? null : _people.FirstOrDefault(p => p.Id == id);

        // ---- the numbers, and where each one comes from ------------------

        /// What one night away costs a bond.
        ///
        /// DERIVED FROM THE WEEK, NOT PICKED. The campaign's unit is a
        /// seven-day week and its verdict turns on that scale, so the figure
        /// that matters is what a full week of absence does. At 0.06 a night a
        /// bond of 0.75 crosses `TalkFreely` on the sixth night and reaches
        /// 0.33 by the seventh. One missed night is nearly nothing and a whole
        /// week is most of the relationship, which is the shape the design
        /// wants: forgiving of a bad night, unforgiving of a pattern.
        public const double BondLostPerNightAway = 0.06;

        /// And what being there returns. LOWER THAN THE LOSS, on purpose.
        /// Absence is cheap to accumulate and expensive to undo, because a
        /// symmetric rate makes going home a chore you clear rather than a
        /// relationship you keep — the player would learn to alternate.
        public const double BondGainedPerNightHome = 0.04;

        /// Below this a dependent will repeat what they know about you to
        /// somebody who asks.
        ///
        /// I FIRST WROTE 0.35 HERE AND CLAIMED IT WAS "`Gossip`'s own idea of a
        /// loyal agent, restated so the two cannot drift". That was false —
        /// `Gossip` has no such threshold, and I checked only because the claim
        /// was the kind this project has been burned by. The real lines already
        /// drawn are `Empire.RecruitLoyaltyFloor` 0.55 ("the need route ends in
        /// a yes only past this"), `Empire.PoachLoyaltyFloor` 0.4 ("below this,
        /// a poached crew member walks"), `StreetVoice` warming above 0.65, and
        /// `ActThreeHost` treating 0.15 as departed.
        ///
        /// 0.4 is the right one and it is the same idea: the point at which
        /// somebody stops being YOURS. A crew member walks there; a dependent
        /// stops keeping your nights to themselves there. Copied rather than
        /// shared because `PoachLoyaltyFloor` is an instance tunable on
        /// `Empire` and this is a constant, so the two are named together here
        /// to be compared rather than silently diverging.
        ///
        /// It also lands the week where the design wants it: a bond of 0.75
        /// losing 0.06 a night crosses 0.4 on the sixth consecutive night away.
        /// A bad night is nearly free; a week is most of the relationship.
        public const double TalkFreely = 0.40;

        /// Nobody is ever entirely gone. A bond floors here rather than at
        /// zero, because a family member who has written you off completely is
        /// a different story beat and not a slider position.
        public const double BondFloor = 0.05;

        // ---- the day ----------------------------------------------------

        /// A night the player spent at home.
        ///
        /// `given` is clean money handed over — dirty money is deliberately not
        /// accepted here, and that is a design statement rather than an
        /// oversight: the one place the player cannot launder is the kitchen
        /// table. Bringing home what cannot be explained is `HeatBroughtHome`,
        /// below, and it costs rather than helps.
        public void NightAtHome(int day, int givenClean = 0, double heatBroughtHome = 0.0)
        {
            foreach (var p in _people)
            {
                p.SetBond(p.Bond + BondGainedPerNightHome);
                p.Seen(day);

                // Money is CONDITION, never bond. You cannot buy your way back
                // into somebody's good opinion by being richer at them, and a
                // game where you can is a game about a resource.
                if (givenClean > 0)
                    p.SetCondition(p.Condition + Math.Min(0.25, givenClean / 400.0));

                if (heatBroughtHome > 0.01)
                {
                    // BEING THERE WITH THE TROUBLE IS NOT THE SAME AS BEING
                    // THERE. Heat under the same roof frightens the people
                    // under it — condition falls even though attendance rose,
                    // which is the case a single "time at home" number cannot
                    // express at all.
                    p.SetCondition(p.Condition - heatBroughtHome * 0.30);
                    if (heatBroughtHome > 0.5)
                        p.Note($"day {day}: you brought it into the house");
                }
            }
        }

        /// A night the player spent elsewhere.
        public void NightAway(int day)
        {
            foreach (var p in _people)
            {
                double before = p.Bond;
                p.SetBond(Math.Max(BondFloor, p.Bond - BondLostPerNightAway));
                // Noted at the crossing, not every night — a grievance list that
                // records each absence is a log, and what a person carries is
                // the moment it started to mean something.
                if (before >= TalkFreely && p.Bond < TalkFreely)
                    p.Note($"day {day}: stopped expecting you");
            }
        }

        /// Who would now repeat what they know, and to whom it matters.
        ///
        /// THIS IS THE WHOLE MILESTONE IN ONE METHOD. It does not compute a
        /// penalty; it returns PEOPLE. The caller wires them into the mill as
        /// agents whose loyalty is their bond, and from that point the existing
        /// machinery does everything — who they talk to, what carries, how fast
        /// it spreads, whether the player can discredit it.
        public IEnumerable<Dependent> Talkers() =>
            _people.Where(p => p.Bond < TalkFreely);

        /// The household's own state of the week, for the endings matrix.
        ///
        /// REPORTED, NOT FED BACK. Nothing in the simulation reads this — it
        /// exists so a run can be JUDGED, which is the difference between a
        /// measurement and a mechanic. If a future ending calculation consumes
        /// it directly, the done-condition has been quietly failed and the
        /// difference has become a stat again.
        public double MeanBond => _people.Count == 0 ? 0 : _people.Average(p => p.Bond);
        public double MeanCondition => _people.Count == 0 ? 0 : _people.Average(p => p.Condition);
        public int TalkerCount => _people.Count(p => p.Bond < TalkFreely);
    }
}
