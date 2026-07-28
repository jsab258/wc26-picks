using System.Collections.Generic;
using Ledger.Core;

namespace Ledger.Game
{
    /// The district's gates (roadmap M7.5). Content as data: this is the only
    /// file that knows which places on Hook Street have somebody standing in
    /// front of them, and none of it is hardcoded in the simulation.
    ///
    /// Four gates, deliberately few. A street where every door is a puzzle is
    /// a puzzle box, not a street — most places are simply open, and the ones
    /// that are not should each teach you a different thing about how this city
    /// decides who counts.
    ///
    ///   THE BACK ROOM   who vouches for you
    ///   THE OFFICE      what you are, on paper
    ///   THE LOFT        whether anybody has heard of you (and it wants: no)
    ///   THE YARD        whether anybody has heard of you (and it wants: yes)
    ///
    /// The last two are the pair worth having. One room closes as you become
    /// somebody; the other opens. There is no build that holds both.
    public static class AccessSetup
    {
        public static List<Gate> Build()
        {
            var gates = new List<Gate>();

            // Hal's back room at the ferry. Neutral ground, and the way in
            // is that somebody says your name for you — or, failing that, that
            // you look like nobody worth stopping.
            gates.Add(new Gate("backroom", "the back room at the ferry", "Hal's man")
                {
                    Refusal = "\"Private tonight.\" He does not move, and does not look at you again.",
                }
                .WithKey(new AccessKey(KeyKind.Introduction, who: "Hal")
                    .Reads("He hears whose name you say and steps aside without a word.",
                           "Hal would have to speak for you, and Hal speaks for very few people."))
                .WithKey(new AccessKey(KeyKind.Standing, 40, who: "dockside")
                    .Reads("He knows who you run with. Tonight that is enough.",
                           "You would need to stand better with the docks than you do."))
                .WithKey(new AccessKey(KeyKind.Payment, 60)
                    .Reads("He takes the sixty without counting it and finds something else to look at.",
                           "Sixty would do it. You do not have sixty."))
                .WithKey(new AccessKey(KeyKind.Dress, dress: "plain")
                    .Reads("He looks at what you are wearing, decides you are nobody, and loses interest.",
                           "The coat is the problem. In there, it is the wrong thing to be wearing.")));

            // The harbourmaster's office. Daylight, paperwork, and a clerk who
            // has never been frightened of anybody in his life — unless you
            // happen to know something about him.
            gates.Add(new Gate("harbor_office", "the harbourmaster's office", "the clerk")
                {
                    Refusal = "\"Appointments,\" the clerk says, to the ledger rather than to you.",
                }
                .WithKey(new AccessKey(KeyKind.Before, 16)
                    .Reads("The counter is still open. He sighs and waves you through.",
                           "They shut the counter at four. You have left it too late."))
                .WithKey(new AccessKey(KeyKind.Hook)
                    .Reads("He meets your eye, remembers what you know about him, and looks away first.",
                           "If you had something on him this would be a different conversation."))
                .WithKey(new AccessKey(KeyKind.Payment, 120)
                    .Reads("The money goes under the ledger. The ledger does not move.",
                           "It would take a hundred and twenty to make him forget the appointments book.")));

            // The loft above the laundry. A quiet room for quiet people. It
            // closes as you become somebody, which is the point of it.
            gates.Add(new Gate("laundry", "the loft above the laundry", "the woman at the press")
                {
                    Refusal = "She looks at you for a long moment. \"We're full,\" she says, of an empty stairway.",
                }
                .WithKey(new AccessKey(KeyKind.Quiet, 30)
                    .Reads("She has not heard anything about you. That is the entire test, and you pass it.",
                           "Too many people are saying your name this week for a room like this."))
                .WithKey(new AccessKey(KeyKind.Introduction, who: "Ada")
                    .Reads("You mention Ada. Her whole face changes, and the stairs are yours.",
                           "Ada could vouch for you here, if Ada thought better of you.")));

            // The repair yard after dark. The opposite door: it only opens to
            // somebody the street already talks about, or to somebody who
            // brought enough people that talking is beside the point.
            gates.Add(new Gate("repair_yard", "the boat repair yard", "the man with the dog")
                {
                    Refusal = "\"Don't know you,\" he says. The dog agrees with him.",
                }
                .WithKey(new AccessKey(KeyKind.Notorious, 45)
                    .Reads("He knows the name. He decides, visibly, not to be the man who stopped you.",
                           "Nobody back there has heard of you yet, and that is the only currency they take."))
                .WithKey(new AccessKey(KeyKind.Crew, 2)
                    .Reads("He counts the people behind you, does the arithmetic, and opens the gate.",
                           "Not on your own. Two people behind you and he would not have to think about it."))
                .WithKey(new AccessKey(KeyKind.After, 21)
                    .Reads("After nine the yard belongs to whoever is standing in it.",
                           "Come back after nine, when the yard belongs to whoever is standing in it.")));

            return gates;
        }
    }
}
