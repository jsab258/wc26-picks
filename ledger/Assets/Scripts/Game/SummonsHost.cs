using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// THE CALLER FOR `Summoning`, so the rival ringing you is a thing that
    /// happens rather than a thing that exists.
    ///
    /// Rule 6, in the form this project keeps producing: a Core file lands
    /// tested, documented and unreached, `reach-check` says so in the same
    /// minute, and the roadmap row goes on describing a gap that is now only
    /// a missing call site. Sixty-one public Core APIs were once found in that
    /// state at once.
    ///
    /// WHY THE DAY CLOSE, AND WHY THAT IS NOT THE HOUR SHE RINGS. The close is
    /// the one instant every system in the game agrees is "a day" — the till is
    /// counted and the fuse advances there — so it is where the question gets
    /// ASKED. Giving the rival a timer of her own would be a second clock for
    /// one idea, which has already cost this project the arms, the billboards
    /// and the foot plant.
    ///
    /// But the close fires at eight in the morning, and she telephones at nine
    /// at night. This paragraph said "she rings in the evening — this is the
    /// moment the till is counted" and was wrong the hour after it was written:
    /// those are different times and the code now says so. The call is
    /// evaluated at the close and DATED to the evening it belongs to, which
    /// matters mechanically as well as in the fiction — a callbox is only live
    /// inside its own hours.
    ///
    /// WHAT ANSWERS THE CALL IN CI. Nobody. There is no player to pick up, and
    /// that is the honest state rather than a limitation to work around: the
    /// sim's player is a bot standing wherever the night left it, so whether
    /// the phone is reachable is a real question with a real answer, and the
    /// answer is the mechanic. What the interactive game will add is the third
    /// outcome — picking up and saying no — which needs a prompt and belongs
    /// with the UI.
    public static class SummonsHost
    {
        /// Calls she placed, and what each came to.
        ///
        /// FOUR COUNTERS FOR ONE EVENT, AND THEY MUST ADD UP. `Placed` is the
        /// denominator: without it, `Taken=0` reads identically whether nobody
        /// ever answered or she never rang, and this file exists precisely
        /// because a system that never runs looks like a system that runs
        /// quietly. The gate compares them, the same shape as the informer's
        /// mark against the accusations that earned it.
        public static int Placed { get; private set; }
        /// Why the last miss was a miss. Empty when the call was taken.
        ///
        /// `Taken=0` beside `Placed=1` is the ambiguity CLAUDE.md names in its
        /// own words — one missed call reads identically to a player who was
        /// out on the street — and adding the player branch to `NearPhone` fixed
        /// only half of it: the outcome became possible, and the reason stayed
        /// invisible.
        public static string MissWhy { get; private set; } = "";
        public static int Taken { get; private set; }
        public static int MissedCalls { get; private set; }
        public static int Refused { get; private set; }

        /// The last one in words, because a count says the code ran and this
        /// says what it decided.
        public static string LastRead { get; private set; } = "she has not rung";

        public static void Reset()
        {
            Placed = Taken = MissedCalls = Refused = 0;
            MissWhy = "";
            LastRead = "she has not rung";
        }

        /// Once a day, at the close. Returns true when a call was placed.
        public static bool Nightly(GameController game)
        {
            if (game == null || game.Empire == null) return false;
            var arm = game.Empire.Rival;
            var call = Summoning.Due(arm, game.Now.Day, game.Now.Hour);
            if (call == null) return false;

            Placed++;

            // REACHABLE MEANS NEAR A LINE, AND THE PHONE LAYER ALREADY KNOWS.
            //
            // `PhoneBook.ReachableNow` was built in M10 with a note that the
            // whole point of a telephone is that it can fail to find you, and
            // it takes the proximity test from the caller rather than guessing
            // at it. `GameController.NearPhone` is that test and has been
            // running for weeks; this is the first thing that asks it about
            // the PLAYER rather than about somebody being rung — and asking it
            // that question the first time is what showed it had no answer for
            // him at all. It walked the walker list and the crowd, and the
            // player is in neither, so it returned false for every line at
            // every hour and "you were not reachable" was the only outcome this
            // mechanic could produce. Fixed in `PhoneSetup`; the first build's
            // single missed call reads identically either way, which is why it
            // had to be found by reading.
            //
            // ASKED AT THE HOUR SHE RINGS, NOT THE HOUR THE DAY TURNS. The day
            // closes at eight in the morning; she calls at nine at night. A
            // callbox is only live inside its own hours, so asking at eight
            // would report the player unreachable for a reason that has nothing
            // to do with where he was standing — the miss would be the world's
            // fault rather than his, which is the one thing that would make
            // this mechanic feel arbitrary instead of chosen.
            var atRing = new GameTime(game.Now.Day, Summoning.RingsAtHour, 0);
            bool reachable = game.Phones != null
                && game.Phones.ReachableNow("player", atRing, game.NearPhone);

            // TWO OUTCOMES HERE AND THREE IN THE MODEL, said out loud so the
            // missing one is a known gap rather than a silent simplification.
            // Refusing is picking up and saying no, which needs somebody to
            // decide; there is nobody in CI, and inventing an answer for the
            // bot would put a decision the player owns inside the harness.
            var answer = reachable ? Answered.Took : Answered.Missed;
            if (answer == Answered.Took) Taken++; else MissedCalls++;

            // AND WHY, BECAUSE `Taken=0` STILL CANNOT SAY. The player branch in
            // `NearPhone` was added this afternoon, which made `Took`
            // REACHABLE; the run then reported `summonsPlaced=1 summonsTaken=0`
            // again, and reachable is not the same as reached. A miss has two
            // completely different causes — no line was live at nine, or a live
            // line was live and the player was nowhere near it — and they want
            // opposite things done about them. The first is a world that never
            // offered the choice; the second is the mechanic working.
            //
            // `MissWhy` names which. The lines are asked once more, ignoring
            // proximity, so "was any line even open" and "was he near one" are
            // separated rather than collapsed into a single false.
            if (answer == Answered.Missed)
            {
                bool anyLive = game.Phones != null
                               && game.Phones.ReachableNow("player", atRing, (_, __) => true);
                MissWhy = anyLive ? "a line was live and he was not near it"
                                  : "no line was live at that hour";
            }
            else MissWhy = "";

            Summoning.Apply(game.Empire, call, answer, game.Now.Day);
            LastRead = Summoning.ReadOf(call, answer);

            // AND HER PEOPLE HEAR ABOUT IT, through the same arm-memory path
            // every other rival act uses. A call nobody on the street knows
            // about is a number moving in private, which is the thing this
            // game is built not to do.
            var mill = game.Gossip != null ? game.Gossip.Mill : null;
            if (mill != null)
                foreach (var id in arm.Members)
                    mill.Get(id)?.Memory.Append(
                        new MemoryEvent(game.Now, "heard", 0.8, LastRead));

            Debug.Log($"SummonsHost: {LastRead} (stage={arm.Stage} "
                      + $"attention={arm.Attention:0.00} standing={arm.Standing:0.00} "
                      + $"terms=[{call.Terms}])");
            return true;
        }
    }
}
