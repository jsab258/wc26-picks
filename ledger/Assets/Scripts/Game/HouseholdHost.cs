using UnityEngine;
using Ledger.Core;

namespace Ledger.Game
{
    /// M18, wired. The rooms above the pub, and who is in them.
    ///
    /// BUILT AND WIRED IN ONE COMMIT, on purpose. `Core/Household` went in and
    /// the reach check immediately reported seven unreached APIs — correctly:
    /// a Core system with no caller is this project's oldest failure and the
    /// ledger it would have gone on is supposed to count DOWN. Adding seven
    /// entries to it and calling the milestone started would have been the
    /// same move that left `Brandish`, `MayFrisk` and `Acquire` at zero callers
    /// for a month.
    ///
    /// WHAT MAKES A NIGHT A NIGHT AT HOME. Not a menu, not a verb the player
    /// selects — where they physically were when the day turned. The roadmap
    /// says the rooms above the pub, so home is the bar door, and the test is
    /// proximity at the moment the day closes. That means going home is
    /// something you DO in the world rather than something you confirm, which
    /// is the difference between a place and a checkbox.
    public class HouseholdHost
    {
        /// How close to the door counts as under the roof. The bar's own
        /// interior is a few metres across and `ConversationHost.TalkRange`
        /// is what the game already calls "near enough to be with somebody",
        /// so twice that is the building rather than a spot on the pavement.
        public const float HomeRadius = ConversationHost.TalkRange * 2f;

        public Household Book { get; } = new Household();

        int _lastNightScored;
        /// Counters the sim reads. `nightsHome` and `nightsAway` together must
        /// equal the days elapsed, or the scorer is being skipped — which is
        /// exactly how a nightly system quietly stops running.
        public int NightsHome { get; private set; }
        public int NightsAway { get; private set; }
        public int TalkersWired { get; private set; }

        /// Which grievances have already reached the mill, so a nightly
        /// re-wire tops up loyalty without re-telling the same story.
        readonly System.Collections.Generic.HashSet<string> _told =
            new System.Collections.Generic.HashSet<string>();

        public HouseholdHost()
        {
            // Two, and they are the smallest household that can express the
            // milestone: somebody who depends on the money and somebody who
            // depends on the person. A single dependent collapses those into
            // one relationship and the design's whole point is that they come
            // apart.
            Book.Add(new Dependent { Id = "nell", Name = "Nell", Relation = "mother" });
            Book.Add(new Dependent { Id = "bry", Name = "Bry", Relation = "brother" });
        }

        /// Score the night that just ended. Called once per day close.
        ///
        /// `heat` is the street's, and it only reaches the house if the player
        /// was IN it — trouble follows you through the door or it does not
        /// follow you at all.
        public void CloseNight(int day, Vector3 playerAt, int cleanGiven, double heat)
        {
            if (day <= _lastNightScored) return;
            _lastNightScored = day;

            bool home = Vector3.Distance(playerAt, WorldBuilder.BarDoor) <= HomeRadius;
            if (home)
            {
                NightsHome++;
                Book.NightAtHome(day, cleanGiven, heat);
            }
            else
            {
                NightsAway++;
                Book.NightAway(day);
            }
        }

        /// THE PART THAT MAKES IT A RELATIONSHIP AND NOT A STAT.
        ///
        /// Nobody reads a neglect score. A dependent whose bond has fallen past
        /// `TalkFreely` is ADDED TO THE MILL as an ordinary agent whose loyalty
        /// is their bond — and from there the existing machinery does all of it:
        /// who they talk to, what carries, how fast, whether the player can
        /// discredit it. The people closest to you become the people most
        /// willing to talk about you, through the same code that governs a
        /// barman who has taken against you.
        ///
        /// Re-applied every close rather than once, because a bond that
        /// recovers should walk the loyalty back up. Adding an agent that is
        /// already there is a no-op in `GossipMill`, which is what makes this
        /// safe to call repeatedly.
        public void WireTalkers(GossipMill mill, GameTime now)
        {
            if (mill == null) return;
            TalkersWired = 0;
            foreach (var d in Book.Talkers())
            {
                var g = mill.Get(d.Id);
                if (g == null)
                {
                    g = new Gossiper(d.Id, d.Name, new MemoryStore(d.Id),
                                     new KnowledgeBase(), new SuspicionTracker(),
                                     "day", greed: 0.3, nerve: 0.5, loyalty: d.Bond);
                    mill.Add(g);
                }
                g.Loyalty = d.Bond;

                // AND WHAT THEY WOULD ACTUALLY SAY. A grievance is not
                // decoration: it goes into the agent's memory, which is what
                // `GossipMill` retrieves from when somebody asks them about
                // you. Without this the dependent turns up in the mill as a
                // disloyal stranger with nothing to tell — a relationship
                // reduced to a loyalty number, which is the exact failure the
                // done-condition forbids.
                //
                // ONCE EACH, TRACKED HERE, because `MemoryStore.Append` does
                // not deduplicate — it is an unconditional `Events.Add`. I had
                // written a comment claiming it was content-addressed and
                // checked only because the claim was the shape this project
                // keeps getting burned by. It was false: re-wiring on every
                // close would have stacked the same grievance every day until
                // `Prune` started throwing away real memories to make room for
                // copies of one line.
                foreach (var line in d.Grievances)
                {
                    var key = d.Id + "\u001f" + line;
                    if (!_told.Add(key)) continue;
                    g.Memory.Append(new MemoryEvent(now, "lived", 0.9, line));
                }

                TalkersWired++;
            }
        }

        /// One line for the verdict, so a run can be judged on it.
        public string Report() =>
            $"household[home={NightsHome} away={NightsAway} bond={Book.MeanBond:0.00} "
            + $"cond={Book.MeanCondition:0.00} talkers={Book.TalkerCount} wired={TalkersWired}]";
    }
}
