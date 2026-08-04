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
        public static int Taken { get; private set; }
        public static int MissedCalls { get; private set; }
        public static int Refused { get; private set; }

        /// The last one in words, because a count says the code ran and this
        /// says what it decided.
        public static string LastRead { get; private set; } = "she has not rung";

        public static void Reset()
        {
            Placed = Taken = MissedCalls = Refused = 0;
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
            // the PLAYER rather than about somebody being rung.
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
