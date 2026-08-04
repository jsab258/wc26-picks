using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// THE CALLER FOR `Press`, so the paper is a thing the town reads rather
    /// than a model nobody asks.
    ///
    /// WHY THE DAY CLOSE, LIKE THE RIVAL'S CALL. A paper comes out in the
    /// morning and reports last night. The close is the one instant every
    /// system here agrees is "a day", so both the summons and this hang off it
    /// rather than growing clocks of their own.
    ///
    /// WHAT IT FILES, AND INTO WHOM. Every mill agent, at once, with no tie
    /// strength and no proximity — that is the entire point of a newspaper and
    /// it is the only channel in this game that works that way. Everything else
    /// moves person to person and decays; this reaches somebody who was three
    /// districts away and asleep.
    ///
    /// THE CONFIDENCE COMES FROM `Press` AND IS NOT AN EYEWITNESS'S, so a story
    /// read and a story seen corroborate on the same topic key instead of
    /// stacking as two beliefs — the distinction the day-circle heat reading is
    /// built on, and the reason `Press` does not invent its own predicate.
    public static class PressHost
    {
        /// Editions printed, stories that carried the player's name, and the
        /// last headline.
        ///
        /// `Editions` IS THE DENOMINATOR and it is the one that matters here.
        /// `Named=0` reads identically whether the town never had a case
        /// against the player or the paper never ran at all, and this is
        /// precisely a system whose failure mode is being quietly absent.
        public static int Editions { get; private set; }
        public static int Named { get; private set; }
        public static int Readers { get; private set; }
        public static string LastHeadline { get; private set; } = "no edition";

        public static void Reset()
        {
            Editions = Named = Readers = 0;
            LastHeadline = "no edition";
        }

        /// Once a day, at the close, for the night that just ended.
        public static bool Nightly(GameController game)
        {
            if (game == null || game.Gossip == null || game.Gossip.Mill == null) return false;
            var last = ViolenceHost.Last;
            // `Deed` IS A STRUCT, so it is never null and `last.Deed == null`
            // would have been a compile error I could not see locally — the
            // Game layer's first compiler is twenty-eight minutes away. The
            // real "no act yet" test is the event id being empty, which is what
            // an unset deed actually carries.
            if (last == null || string.IsNullOrEmpty(last.Deed.EventId)) return false;

            // ONE EDITION PER ACT, NOT PER DAY. `ViolenceHost.Last` is the most
            // recent act, and running it again the next morning would print the
            // same killing twice — which would double a reputation off one
            // event, the fault `HomicideBook` has its own guard against and
            // says so in a comment.
            if (last.Deed.EventId == _printed) return false;

            // WHAT THE STREET WOULD TELL A DETECTIVE, and the paper is not
            // allowed a better source than that. `Pressure` is the police's own
            // reading of how much of a case there is; passing it means the
            // paper and the law can never disagree about whether the player is
            // nameable, which is a disagreement no reader could interpret.
            double streetCase = game.Homicides != null
                ? game.Homicides.Pressure(game.Gossip.Mill, game.IsAlive, game.Now.Day)
                : 0;

            var story = Press.Print(game.Now.Day, last.Notoriety, streetCase,
                                    last.Lethal, game.DistrictOfPlayer());
            if (story == null) return false;

            _printed = last.Deed.EventId;
            Editions++;
            LastHeadline = story.Headline;
            if (story.NamesYou) Named++;

            foreach (var g in game.Gossip.Mill.Agents)
            {
                if (g == null) continue;
                game.Gossip.Mill.Witness(g.Id, story.Content, story.Headline,
                                         sensitive: story.NamesYou, now: game.Now,
                                         confidence: story.Confidence);
                Readers++;
            }

            // AND BEING NAMED IN THE PAPER IS BEING KNOWN. An unnamed story is
            // worth exactly nothing here, by design: notoriety is how known YOU
            // are, and a town reading about a body on Hook Street has learned
            // nothing about the publican.
            double fame = Press.Notoriety(story);
            if (fame > 0 && game.Campaign != null) game.Campaign.Noted(fame);

            Debug.Log($"PressHost: {story.Headline} (named={story.NamesYou} "
                      + $"confidence={story.Confidence:0.00} readers={Readers} "
                      + $"streetCase={streetCase:0.00})");
            return true;
        }

        static string _printed = "";
    }
}
