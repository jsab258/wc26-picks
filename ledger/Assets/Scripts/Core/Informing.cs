using System.Collections.Generic;

namespace Ledger.Core
{
    /// M21, THE FIRST PIECE: THE LAW AS SOMETHING YOU CAN POINT.
    ///
    /// The roadmap scores this 40 against a target of 70 and says why in one
    /// line: *"you are subject to the law; you cannot use it."* Every piece of
    /// police machinery in this game — `Inquiry`, `HomicideBook`, Ellis on the
    /// street — has exactly one subject, the player. Naming somebody else is
    /// the verb that turns the game's central threat into a tool the player can
    /// hold, and it costs nothing new to build because the information layer
    /// already decides what anybody believes.
    ///
    /// THE THESIS, AND IT IS THE WHOLE DESIGN: **truth is not an input.** A
    /// true accusation nobody will corroborate is ignored. A false one three
    /// people will swear to lands. That is not cynicism for its own sake, it is
    /// this project's moat pointed at the player for once — information 90
    /// against a best-in-class 65 — and it is the difference between a crime
    /// game where your weapon is a gun and one where it is what people believe.
    ///
    /// NOTHING HERE IS A NEW NUMBER. The bar is `LedgerState.CaseStandsAt`, which
    /// already means "this would stand up in front of a magistrate" and which
    /// `HomicideBook.TestimonyGrade` deliberately duplicates. The corroboration
    /// shape is `HomicideBook`'s, whose own comment says it best: *"Every
    /// witness after the first. Corroboration is what turns one person's word
    /// into a case."* An accusation against a rival is weighed exactly as the
    /// police weigh one against you, because it is the same police.
    ///
    /// WHAT IS NOT HERE. This decides what an accusation is WORTH; it does not
    /// apply it. `Weigh` returns the outcome and the mark, and the Game layer
    /// closes the target's access and files the fact. That split is deliberate
    /// — Core compiles and tests in this container and the Game layer costs a
    /// 28-minute round trip — but rule 6 says built is not running, so the
    /// wiring is on the queue as its own item and this is not finished until a
    /// gate proves something called it.
    public enum Accusation
    {
        /// Nobody will back it. The law hears you out and does nothing.
        Ignored,
        /// Somebody will back it, but not enough for a charge. It sits in a
        /// file, and files are read later.
        Noted,
        /// It stands up. The target is the one being asked about now.
        Charged,
        /// The law already knows better, and now it knows you said otherwise.
        BlewBack,
    }

    /// What one accusation is worth, and what it costs to have made it.
    public class Denunciation
    {
        public string TargetId = "";
        public Accusation Outcome = Accusation.Ignored;

        /// The strongest case the street would actually give the police, on the
        /// same 0..1 scale everything else in this game grades testimony on.
        public double Corroboration;

        /// And the strongest case against your version of it.
        public double Contradiction;

        /// How many people would say it out loud to a detective. Printed
        /// alongside the weight because one person at 0.9 and three at 0.4 are
        /// different situations that a single number cannot tell apart — the
        /// same reason `deedWitnesses` and `deedEyesOpen` are both in the
        /// verdict.
        public int Corroborators;

        /// WHAT IT COSTS, RETURNED AS DATA SO A CALLER CANNOT FORGET IT.
        ///
        /// Walking into a police station is an act, and this game's whole
        /// premise is that acts are seen. An informer who pays nothing is a
        /// delete button with extra steps, and the temptation to ship it that
        /// way is exactly why the cost is a return value rather than a note in
        /// a design document: the Game layer has to receive this fact and put
        /// it somewhere, and a fact about the player entering the information
        /// layer is the same currency everything else in the game trades in.
        ///
        /// Never null. On a blowback it says you lied; otherwise it says you
        /// talked, which on this street is quite enough.
        public Fact MarkOnYou = new Fact("player", "informer", "no");

        public string Why = "";
    }

    /// One person's willingness to say a thing to a detective.
    ///
    /// SEPARATE FROM KNOWING IT, because those come apart constantly and the
    /// gap is where this system lives. `Watched.WouldTalkToPolice` already
    /// models somebody who saw a killing and will or will not repeat it; this
    /// is the same distinction generalised, and the caller supplies the answer
    /// rather than this file guessing at loyalty.
    public struct Testimony
    {
        /// What this person actually holds on the topic. Null means they have
        /// nothing to say and they are skipped.
        public Fact Holds;

        /// How much a detective would weigh them, 0..1 — the same scale as
        /// `Gossip` confidence and `ActThree`'s surviving leads.
        public double Credibility;

        /// Whether they would say it to the police at all.
        public bool WouldTalk;

        public Testimony(Fact holds, double credibility, bool wouldTalk)
        {
            Holds = holds;
            Credibility = Feel.Clamp01(credibility);
            WouldTalk = wouldTalk;
        }
    }

    public static class Informing
    {
        /// The bar an accusation has to clear, and it is not a new number.
        /// `LedgerState.CaseStandsAt` is the game's existing statement of what
        /// would stand up in front of a magistrate, and a charge against a
        /// rival is judged by the same magistrate as a charge against you.
        public const double StandsAt = LedgerState.CaseStandsAt;

        /// Every corroborator after the first, straight off `HomicideBook`.
        /// Reused rather than re-picked so the two cannot drift: if the game
        /// ever changes its mind about what corroboration is worth, it changes
        /// its mind once.
        public const double PerExtraWitness = HomicideBook.PerExtraWitness;

        /// WEIGH AN ACCUSATION. `claim` is what you tell the law; `street` is
        /// everybody who might be asked about it.
        ///
        /// The claim's SUBJECT is the person you are naming, and it is read
        /// from the fact rather than passed alongside it — two ways to say who
        /// is accused is two ways to disagree, and this game has been bitten by
        /// a parameter that meant two things once already tonight.
        public static Denunciation Weigh(Fact claim, IEnumerable<Testimony> street)
        {
            var d = new Denunciation();
            if (claim == null)
            {
                d.Why = "no claim";
                return d;
            }
            d.TargetId = claim.Subject;

            // NAMING YOURSELF IS NOT A TOOL. It is a confession, the game has
            // an Act III for it, and letting it through here would quietly
            // provide a second and much stupider route into the same place.
            if (claim.Subject == "player")
            {
                d.Why = "you cannot inform on yourself";
                d.MarkOnYou = new Fact("player", "informer", "no");
                return d;
            }

            double best = 0, worst = 0;
            if (street != null)
            {
                foreach (var t in street)
                {
                    if (t.Holds == null || !t.WouldTalk) continue;
                    if (!t.Holds.SameTopic(claim)) continue;

                    if (t.Holds.Value == claim.Value)
                    {
                        // The strongest single voice, then every other voice as
                        // corroboration on top. One believable person is a
                        // lead; three people agreeing is a case.
                        if (t.Credibility > best)
                        {
                            if (best > 0) d.Corroboration += PerExtraWitness;
                            best = t.Credibility;
                        }
                        else d.Corroboration += PerExtraWitness;
                        d.Corroborators++;
                    }
                    else if (t.Credibility > worst) worst = t.Credibility;
                }
            }
            d.Corroboration = Feel.Clamp01(best + d.Corroboration);
            d.Contradiction = worst;

            // BLOWBACK FIRST, because it is the outcome that makes the verb
            // worth having. If the law can already be told otherwise by
            // somebody it believes at least as much, the accusation does not
            // merely fail — it becomes a thing known about you, and this game
            // remembers things known about you for the rest of the save.
            //
            // The comparison is against the strongest CONTRARY voice rather
            // than against the total, because a detective who has one credible
            // person saying you are wrong does not need a second one.
            if (d.Contradiction > 0 && d.Contradiction >= d.Corroboration)
            {
                d.Outcome = Accusation.BlewBack;
                d.MarkOnYou = new Fact("player", "lied_to_police", d.TargetId);
                d.Why = $"contradicted at {d.Contradiction:0.00} against {d.Corroboration:0.00}";
                return d;
            }

            // AND THE MARK LANDS EVEN WHEN THE ACCUSATION DOES NOT. You were
            // seen going in. That is the cost, it is not refundable, and it is
            // the reason this is a decision rather than a free action.
            d.MarkOnYou = new Fact("player", "informer", d.TargetId);

            if (d.Corroboration >= StandsAt)
            {
                d.Outcome = Accusation.Charged;
                d.Why = $"{d.Corroborators} will swear to it, weight {d.Corroboration:0.00}";
            }
            else if (d.Corroboration > 0)
            {
                d.Outcome = Accusation.Noted;
                d.Why = $"weight {d.Corroboration:0.00}, under {StandsAt:0.00}";
            }
            else
            {
                d.Outcome = Accusation.Ignored;
                d.Why = "nobody will back it";
            }
            return d;
        }

        /// Where the law's attention goes after a charge sticks.
        ///
        /// A charge does NOT clear an inquiry that is already about you.
        /// Pointing a detective at somebody else while she is asking your
        /// neighbours about you is a distraction, not an exit — and a version
        /// of this that let a manhunt be talked away would be the single most
        /// exploitable thing in the game. Below `Investigation` she was not
        /// looking at you anyway, so there is nothing to redirect.
        public static bool RedirectsInquiry(Accusation outcome, Inquiry current) =>
            outcome == Accusation.Charged && current < Inquiry.Investigation;

        /// What a blowback does to the person who was accused of nothing.
        ///
        /// Nothing. Deliberately. The temptation is to have the target learn
        /// they were named and hate you for it, and that is a good scene — but
        /// it belongs to the gossip layer, which already carries who said what
        /// about whom, and duplicating it here would give the game two answers
        /// to the same question. The mark on the player is what this file
        /// produces; who hears about it is `Gossip`'s business.
        /// HOW MUCH BEING THE MAN WHO NAMED SOMEBODY MAKES YOU KNOWN.
        ///
        /// The second source notoriety has, and the first was violence. That
        /// matters more than the arithmetic: with ONE source, `Campaign.Noted`
        /// could take a maximum and nothing was lost, because there was nothing
        /// to accumulate against. With two, a maximum means the larger source
        /// permanently silences the smaller — one witnessed killing at 0.75 and
        /// no amount of informing could ever move the number again. Notoriety
        /// is how KNOWN you are, not what you are worst for, so `Noted` now
        /// closes a fraction of the remaining gap and this can matter.
        ///
        /// THE SHAPE, AND WHAT IS ASSERTED RATHER THAN GUESSED. These are
        /// design constants like `Violence.Notoriety`'s division by six, not
        /// thresholds read off a measurement, and pretending otherwise would be
        /// worse than saying so. What the tests hold are the ORDERING claims,
        /// which are the design:
        ///
        ///   - a charge that sticks is the loudest, because the law acting on
        ///     your word is the version of this the street repeats;
        ///   - blowback is the next loudest and deliberately not the quietest —
        ///     being caught lying to a detective is famous in the wrong way;
        ///   - being SEEN going in doubles whatever it was worth, because this
        ///     game's premise is that acts are seen, and an informer nobody saw
        ///     is not yet an informer to anybody;
        ///   - nothing here reaches what a witnessed killing is worth, which
        ///     `Violence.Notoriety` floors at 0.75.
        ///
        /// Corroboration scales it because a charge nobody would back and a
        /// charge six people would back are different events wearing one name.
        public static double Notoriety(Accusation outcome, double corroboration, bool seen)
        {
            double baseline =
                outcome == Accusation.Charged ? 0.30
                : outcome == Accusation.BlewBack ? 0.20
                : outcome == Accusation.Noted ? 0.10
                : 0.04;
            double weight = baseline * (0.5 + 0.5 * Feel.Clamp01(corroboration));
            return Feel.Clamp01(seen ? weight * 2.0 : weight);
        }

        public static string Describe(Accusation a) =>
            a == Accusation.Charged ? "It stuck. They are the ones being asked about now."
            : a == Accusation.Noted ? "It went in a file. Files get read."
            : a == Accusation.BlewBack ? "They already knew better, and now they know you said otherwise."
            : "Nobody would back it.";
    }
}
