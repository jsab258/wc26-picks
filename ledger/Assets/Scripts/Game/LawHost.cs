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

        /// How many charges actually moved the detective off the player.
        ///
        /// SEPARATE FROM `Denounced`, because a charge that sticks and a charge
        /// that sticks AND redirects are different events — most charges land
        /// while she is already asking about you by name, and `RedirectsInquiry`
        /// refuses those on purpose. One counter for both would report the verb
        /// working on a run where the redirect never once fired.
        public static int Redirected { get; private set; }

        /// The last one, in words, for the verdict. A count says the code ran;
        /// this says what it decided, which is the thing worth reading.
        public static string LastVerdict { get; private set; } = "none";

        public static void Reset()
        {
            Denounced = 0;
            MarksFiled = 0;
            Redirected = 0;
            NotorietyFiled = 0;
            LastNotoriety = 0;
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
            // CAPTURED AS A BOOL, because the same fact is read twice — once
            // to file the mark and once to weigh the notoriety — and two
            // spellings of one condition is how they come apart later.
            bool saw = !string.IsNullOrEmpty(seenById) && mill.Get(seenById) != null;
            if (saw)
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

                // AND THE DETECTIVE LOOKS AT THEM INSTEAD, FOR FOUR DAYS.
                //
                // `RedirectsInquiry` returned a bool that nothing acted on until
                // now, which is rule 6 on the file beside it: the roadmap's own
                // note says `Inquiry` was derived from the homicide book rather
                // than stored, so there was nowhere to put the answer.
                // `HomicideBook.PointAt` is that place, and the relief it buys
                // decays to nothing over `RedirectHolds` days.
                //
                // The guard stays in `Informing` rather than moving here: a
                // manhunt cannot be talked away, an investigation already about
                // you by name cannot be turned, and below that she was not
                // looking at you anyway. Asking the current stage BEFORE
                // pointing, because pointing changes it and a test against the
                // state you just altered is a test of nothing.
                if (game.Homicides != null
                    && Informing.RedirectsInquiry(d.Outcome, game.PoliceInquiry))
                {
                    game.Homicides.PointAt(d.TargetId, game.Now.Day);
                    Redirected++;
                    LastVerdict += $", inquiry pointed at {d.TargetId}";
                }
            }

            // AND THE STREET LEARNS WHO YOU ARE — THE SECOND SOURCE NOTORIETY
            // HAS, and until now it had exactly one.
            //
            // WHY IT BELONGS HERE RATHER THAN IN `Informing`. Core decides what
            // an accusation is WORTH; the Game layer decides what happens. That
            // split is the file's own rule and it is also what stopped this
            // being a maximum: with one source a maximum was harmless, and with
            // two it would have meant a single witnessed killing silencing
            // every informing the player ever did.
            //
            // `seen` is whether anybody actually watched you walk in, which is
            // the same fact the mark above is conditional on. Being an informer
            // nobody saw is not yet being an informer to anybody, and the
            // weight doubles when they did.
            if (game.Campaign != null)
            {
                double fame = Informing.Notoriety(d.Outcome, d.Corroboration, saw);
                if (fame > 0) { game.Campaign.Noted(fame); NotorietyFiled++; }
                LastNotoriety = fame;
            }
            return d;
        }

        /// How many accusations charged the player's reputation, and what the
        /// last one was worth. The denominator `notoriety` needs: a run where
        /// nobody informed and a run where the wiring broke both leave the
        /// number where violence put it, and only this can tell them apart.
        public static int NotorietyFiled;
        public static double LastNotoriety;

        /// How many alibis the player has offered, and how many were caught.
        ///
        /// Counted because "the claim path runs" and "the claim path can catch
        /// a lie" are different facts and only the first is obvious. A run
        /// where claims are made and none is ever contradicted would look
        /// identical to a working system and be a broken one — the same split
        /// `speechMissing` needed before it could be read.
        /// Why the last claim attempt did what it did. See the guards.
        public static string ClaimWhy { get; private set; } = "not tried";

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
            // WHY IT DID NOT LAND, RECORDED. `claimsMade=0` came back from the
            // first build with three possible causes and no way to tell them
            // apart: no host, a host whose brain has not been built yet, or a
            // sentence the extractor did not recognise. Guessing between three
            // silent early returns is a round trip each.
            if (game == null) { ClaimWhy = "no game"; return ClaimResult.Unknown; }
            if (host == null) { ClaimWhy = "no host"; return ClaimResult.Unknown; }
            // NO ENGINE NEEDED. Checking a claim is bookkeeping over knowledge,
            // suspicion and memory — the host owns all three — and requiring
            // the LLM-backed engine made it unreachable in the sim, which runs
            // without a client. That is what `claimVia=[game.Hosts]` beside
            // `claimWhy=[not tried]` was saying: found the host, engine null.
            if (host.Knowledge == null) { ClaimWhy = "host has no knowledge"; return ClaimResult.Unknown; }
            var claim = Claims.Extract(said, game.Now, Claims.KnownPlaces());
            if (claim == null)
            {
                ClaimWhy = $"nothing extracted from \"{said}\" ({Claims.KnownPlaces().Count} places)";
                return ClaimResult.Unknown;
            }
            ClaimWhy = "ok";
            ClaimsMade++;
            // A LIE ON THE TELEPHONE IS A SMALLER LIE, and that cuts both
            // ways — the alibi that checks out also buys you less. `OnTheLine`
            // already changes what the model is told; this is the mechanical
            // half, which `PhoneBook.Damped` has been sitting there to provide
            // since the phone layer was written.
            double weight = host.OnTheLine ? PhoneBook.Damped(1.0) : 1.0;
            var was = Claims.Process(host.Knowledge, host.Suspicion, host.Memory, claim, game.Now, weight);
            if (was == ClaimResult.Contradiction) ClaimsCaught++;
            // AND THE STREET CARRIES IT. `ProcessClaim` moves one person's
            // suspicion; `PlayerClaims` is what makes the alibi a thing that
            // exists after the conversation ends and can be checked against
            // later — which is the half `Informing` accuses from.
            game.Gossip?.Mill?.PlayerClaims(host.Card?.Name ?? "", claim, game.Now);

            // AND WHOEVER ELSE WAS STANDING THERE.
            //
            // An alibi told to one person was told to exactly one person,
            // however crowded the room, because nothing anywhere asked whether
            // a bystander made out the WORDS. The perception model resolves
            // hearing a NOISE — direction and distance, never identity — and
            // `Acoustics.CanMakeOutWords` and `OverheardConfidence` were built
            // for the other half and had no caller in the game.
            //
            // This is the mechanic, not a detail: the whole point of a lie in
            // LEDGER is that it survives the conversation and can be checked
            // later, so WHERE you tell it has to be a decision. It was not one
            // while the street was deaf by construction.
            //
            // AT OVERHEARD CONFIDENCE, capped at 0.9 by the Core call so a
            // thing caught across a room can never be promoted into hard
            // knowledge — which is the line between this game's mill and a
            // database, and the reason the cap lives in Core rather than here.
            //
            // NOT ON THE TELEPHONE. A voice in a handset is not in the room,
            // and the one thing worse than a street that cannot hear you is a
            // street that hears the half of the call it is not present for.
            ClaimOverheard = 0;
            if (!host.OnTheLine)
            {
                // THE HOSTS, not a walker list. `GameController` keeps its
                // walkers private and exposes `Hosts`, and the hosts are the
                // people who can carry a claim anyway — a background walker
                // has no brain to put it in, so an ear it cannot use is not an
                // ear. Cheaper too: hosts are a handful, walkers are dozens.
                var ears = new List<Acoustics.Ear>();
                var at = host.transform.position;
                foreach (var h in game.Hosts)
                {
                    if (h == null || h == host || !h.isActiveAndEnabled) continue;
                    var who = h.Card?.Name;
                    if (string.IsNullOrEmpty(who)) continue;
                    ears.Add(new Acoustics.Ear(who,
                        Vector3.Distance(h.transform.position, at)));
                }
                // THE CLAIM ITSELF, not a fact rebuilt from its parts. `claim`
                // IS a `Fact` — the first version read `claim.Place` off it and
                // reconstructed the predicate from `Claims.LocationKey`, which
                // is a second implementation of the key the extractor already
                // chose. Two spellings of one topic mean the overheard version
                // could never contradict the told version, and a claim nobody
                // can contradict is the one thing this whole system is for.
                foreach (var o in Acoustics.WhoOverheard(ears, Audio.ChatterLevel))
                {
                    if (game.Gossip?.Mill?.Get(o.ListenerId) == null) continue;
                    game.Gossip.Mill.Witness(o.ListenerId, claim,
                        $"heard {game.Me.InTalk(game.Gossip.Mill)} say they were at {claim.Value}",
                        false, game.Now, o.Confidence);
                    ClaimOverheard++;
                }
            }
            return was;
        }

        /// How many bystanders caught the last claim. Reported by the sim: a
        /// mechanic that never fires is indistinguishable from one that is not
        /// wired, and this one is wired to a distance threshold that a quiet
        /// street can legitimately never satisfy.
        public static int ClaimOverheard { get; private set; }

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
