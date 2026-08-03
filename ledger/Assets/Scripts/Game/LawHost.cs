using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// THE CALLER FOR `Informing`, so the verb is a thing that happens rather
    /// than a thing that exists.
    ///
    /// Rule 6 in the form it usually takes here: `Informing` shipped tested,
    /// documented and with no call site, and `reach-check` said so in the same
    /// minute. Sixty-one public Core APIs were once found in that state, two
    /// untested and forty unreached. A system nobody calls is not half done, it
    /// is a plan.
    ///
    /// WHAT IT WIRES INTO, AND WHY THAT ONE. The obvious hook was `Access` —
    /// the roadmap's done-condition is "their access closes" — and `Access` has
    /// no callers in the Game layer either. Hooking an unwired system to an
    /// unwired system is not wiring, it is a longer plan. The gossip mill is
    /// live, it is ticking every frame in every build, and it is what the
    /// roadmap means by "what the street believes": a rumour spreads, decays,
    /// can be bought quiet, scared quiet or left to go cold. Putting both ends
    /// of a denunciation into it means the verb inherits all of that for free
    /// and none of it has to be re-invented for the law.
    public static class LawHost
    {
        /// How many accusations were made, and how many marks went on the
        /// player for making them.
        ///
        /// TWO COUNTERS FOR ONE EVENT, AND THEY MUST AGREE. The mark is the
        /// entire reason this verb is a decision — an informer who pays nothing
        /// is a delete button with extra steps. `Informing` returns the mark as
        /// data precisely so a caller cannot silently drop it, and a count of
        /// denunciations on its own could not tell a working wiring from one
        /// that files nothing. So both are counted and the gate compares them,
        /// which is the same shape as `deedDispatched` against `deedArrived`.
        public static int Denounced { get; private set; }
        public static int MarksFiled { get; private set; }

        /// The last one, in words, for the verdict. A count says the code ran;
        /// this says what it decided, which is the thing worth reading.
        public static string LastVerdict { get; private set; } = "none";

        public static void Reset()
        {
            Denounced = 0;
            MarksFiled = 0;
            LastVerdict = "none";
        }

        /// Name somebody to the law.
        ///
        /// `seenById` is whoever clocked you going in — the cost, and it is a
        /// required argument rather than an optional one on purpose. There is
        /// no overload that lets a caller skip it.
        public static Denunciation Denounce(GameController game, string seenById,
                                            string targetId, string predicate, string value)
        {
            if (game == null || game.Gossip == null || game.Gossip.Mill == null) return null;
            if (string.IsNullOrEmpty(targetId) || string.IsNullOrEmpty(predicate)) return null;

            var mill = game.Gossip.Mill;
            var claim = new Fact(targetId, predicate, value ?? "");
            string topic = claim.Subject + "." + claim.Predicate;

            // WHAT THE STREET WOULD ACTUALLY TELL A DETECTIVE.
            //
            // `Best(topic)` and not `BestOfValue(topic, claim.Value)`: the
            // strongest telling this person holds on the subject, whatever it
            // says. Filtering to the version that agrees with the accusation
            // would make contradiction structurally impossible and quietly
            // delete the outcome that gives the verb its cost — the same shape
            // as a search that only looks where the answer already is.
            var street = new List<Testimony>();
            foreach (var g in mill.Agents)
            {
                if (g == null) continue;
                var r = g.Best(topic);
                if (r == null) continue;
                street.Add(new Testimony(r.Content, r.Confidence, Watched.WouldTalkToPolice(g)));
            }

            var d = Informing.Weigh(claim, street);
            Denounced++;
            LastVerdict = $"{d.Outcome} ({d.Corroborators} of {street.Count}, {d.Why})";

            // THE MARK, FIRST AND UNCONDITIONALLY. Before the outcome is
            // applied, so no early return can ever skip the cost — every
            // ordering where the payment comes second is one refactor away from
            // a path that does not pay.
            if (!string.IsNullOrEmpty(seenById) && mill.Get(seenById) != null)
            {
                string said = d.Outcome == Accusation.BlewBack
                    ? $"He told them about {d.TargetId}, and they knew better."
                    : $"He was in talking to them about {d.TargetId}.";
                // Sensitive: this belongs to the night face. Somebody who knows
                // the player as a publican learning he informs on people is
                // exactly the leak the two-circles design is built around.
                mill.Witness(seenById, d.MarkOnYou, said, sensitive: true, now: game.Now,
                             confidence: 0.9);
                MarksFiled++;
            }

            // AND WHAT IT DID TO THE TARGET, in the same currency. A charge
            // that stuck is a thing the street now says about them, carried by
            // the person who was willing to say it — not a flag on an object.
            if (d.Outcome == Accusation.Charged)
            {
                var teller = FirstWillingTeller(mill, topic, claim.Value);
                if (teller != null)
                    mill.Witness(teller, new Fact(d.TargetId, "charged", claim.Predicate),
                                 $"They have {d.TargetId} in for it.", sensitive: false,
                                 now: game.Now, confidence: 0.9);
            }
            return d;
        }

        /// How many alibis the player has offered, and how many were caught.
        ///
        /// Counted because "the claim path runs" and "the claim path can catch
        /// a lie" are different facts and only the first is obvious. A run
        /// where claims are made and none is ever contradicted would look
        /// identical to a working system and be a broken one — the same split
        /// `speechMissing` needed before it could be read.
        public static int ClaimsMade { get; private set; }
        public static int ClaimsCaught { get; private set; }

        /// THE PLAYER SAYS WHERE THEY WERE, and the street writes it down.
        ///
        /// Lives here rather than inside `DialogueUI` so the sim can exercise
        /// the REAL path. The dialogue route reaches this through an async
        /// router the sim does not drive, and a gate on a call site nothing in
        /// CI can reach is a gate that proves the code compiles. One method,
        /// two callers, and the run exercises what the player exercises.
        public static ClaimResult Claim(GameController game, ConversationHost host, string said)
        {
            if (game == null || host == null || host.Engine == null) return ClaimResult.Unknown;
            var claim = Claims.Extract(said, game.Now, Claims.KnownPlaces());
            if (claim == null) return ClaimResult.Unknown;
            ClaimsMade++;
            var was = host.Engine.ProcessClaim(claim, game.Now);
            if (was == ClaimResult.Contradiction) ClaimsCaught++;
            // AND THE STREET CARRIES IT. `ProcessClaim` moves one person's
            // suspicion; `PlayerClaims` is what makes the alibi a thing that
            // exists after the conversation ends and can be checked against
            // later — which is the half `Informing` accuses from.
            game.Gossip?.Mill?.PlayerClaims(host.Card?.Name ?? "", claim, game.Now);
            return was;
        }

        /// Whoever will actually repeat it, for attribution. The charge has to
        /// come from a person, because in this game every rumour does — an
        /// unattributed one cannot be bribed, leashed or contradicted, and
        /// would be the one piece of information on the street with no handle
        /// on it.
        static string FirstWillingTeller(GossipMill mill, string topic, string value)
        {
            foreach (var g in mill.Agents)
            {
                if (g == null || !Watched.WouldTalkToPolice(g)) continue;
                if (g.BestOfValue(topic, value) != null) return g.Id;
            }
            return null;
        }
    }
}
