using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// NEGOTIATION — M19's verb, and the one place the model earns its keep.
    ///
    /// Recruiting today is two booleans: pay what their card says they need, or
    /// hold a secret over them. Both are menu picks wearing a method signature —
    /// you call it and it returns true. Nothing about what you SAID matters, so
    /// there is nothing to talk your way through and nothing to get wrong.
    ///
    /// THE LAW OF THIS FILE IS THE PROJECT'S LAW: game state decides, the model
    /// performs. Nothing here reads or writes a line of dialogue. It computes
    /// where a person stands, what would move them, and what it costs to move
    /// them — and the conversation engine hands that to the model as the
    /// character's own position, so the ARGUMENT is improvised and the OUTCOME
    /// is not. A player who talks well gets further because the levers they
    /// reach for are better, never because the prose was pretty.
    ///
    /// THE DESIGN CLAIM, AND IT IS THE WHOLE THESIS OF LEDGER IN ONE OBJECT:
    /// the fast levers cost you the person. A threat works best on somebody with
    /// no nerve and leaves a mark that never fully fades; a secret buys a yes
    /// today and poisons the loyalty you will need on day forty. Need and
    /// respect are slow, cost money or time, and hold. Every other game's
    /// persuasion check is a dice roll against a stat — this one is a trade
    /// between getting what you want now and being able to ask again.
    ///
    /// SO A NEGOTIATION CAN BE WON AND STILL BE A MISTAKE, which is the thing
    /// consequence persistence is FOR and the thing a scripted tree cannot do.
    public enum Lever
    {
        /// Cash on the table. Scales with greed, blunted by suspicion — a man
        /// who thinks you are dangerous reads money as a down payment on
        /// something he will not like.
        Money,

        /// The thing their card says they want, actually done. The strongest and
        /// the slowest, and it is gated on having DONE it rather than on saying
        /// so: `Push` takes the fact, not the promise.
        Need,

        /// Something you know that they would rather you did not. Ignores greed
        /// and nerve entirely — that is what makes it feel like a shortcut —
        /// and it is the most expensive thing in this file.
        Secret,

        /// What happens to them if they say no. Scales with how little nerve
        /// they have, which means it works best on exactly the people you will
        /// later wish had stayed.
        Threat,

        /// Treating them as somebody whose answer matters. Slow, free, and the
        /// only lever that never adds resentment. It is also the only one that
        /// gets STRONGER as they come to trust you, so it compounds where the
        /// others decay.
        Respect,
    }

    /// Where a person stands right now, and what it has cost so far.
    public class Position
    {
        public string WhoId;

        /// How far they are from yes, 1 = a flat no, 0 = agreement. Set by what
        /// is being asked for and by what they already make of you.
        public double Resistance = 1.0;

        /// What pushing has cost. This is the number that outlives the scene:
        /// it becomes lost loyalty whether you win or lose.
        public double Resentment;

        /// Levers already pushed, and how hard. Repeating yourself is worth
        /// less each time — see `Novelty`.
        public readonly Dictionary<Lever, int> Pushes = new Dictionary<Lever, int>();

        /// They have walked. Permanent for this negotiation; the caller writes
        /// the memory that makes it permanent for the save.
        public bool Walked;

        public bool Agreed => !Walked && Resistance <= 0.0;

        /// Why it ended, for the verdict line and for the player's own sense of
        /// what just happened. Never a number.
        public string Why = "still talking";
    }

    public static class Negotiation
    {
        /// Past this much resentment they stop dealing, whatever the offer.
        ///
        /// DERIVED FROM THE OTHER TWO CONSTANTS, NOT PICKED — and the first
        /// version was 1.0, which contradicted the sentence that described it.
        /// A hard threat costs 0.45, so two reach 0.90 and could never have
        /// ended anything at a bound of 1.0. The arithmetic, laid out:
        ///
        ///   two hard threats   0.90  -> walks, and must
        ///   three secrets      0.60  -> does not, and must not
        ///   three checked lies 1.08  -> walks, and should
        ///
        /// 0.9 is the only value that satisfies all three. Rule 2, on a number
        /// I had written a claim about before doing the multiplication.
        public const double WalksAt = 0.9;

        /// What a threat adds to resentment every single time, before any
        /// scaling. Nothing else has a floor like this: coercion is never free
        /// even when it works.
        public const double ThreatResentment = 0.45;

        /// What a secret costs. Lower than a threat in the room and worse
        /// afterwards — see `LoyaltyCost`, where it is the only lever that keeps
        /// charging you after the scene ends.
        public const double SecretResentment = 0.2;

        /// Asking again is worth less. The third push of the same lever is
        /// worth a quarter of the first, so a player cannot grind one idea into
        /// a yes — they have to find another angle, which is the interesting
        /// half of a negotiation.
        public static double Novelty(int timesAlready) => 1.0 / (1.0 + timesAlready);

        /// OPEN A NEGOTIATION. `ask` is how big the request is, 0..1 — a favour
        /// is small, signing their life over to you is 1.
        ///
        /// The starting resistance is the ask, moved by what they already think
        /// of you: loyalty they feel toward you takes some off, suspicion they
        /// hold about you adds. So the same request is genuinely easier from
        /// somebody the street speaks well of, without a single line of dialogue
        /// having been written.
        public static Position Open(Gossiper g, double ask)
        {
            var p = new Position { WhoId = g?.Id };
            if (g == null) { p.Walked = true; p.Why = "there is nobody there"; return p; }

            double suspicion = g.Suspicion?.Value ?? 0;
            p.Resistance = Feel.Clamp01(Feel.Clamp01(ask)
                                        - 0.35 * g.Loyalty
                                        + 0.30 * suspicion);

            // A LEASHED PERSON IS NOT NEGOTIATING WITH YOU. `Gossiper.Leashed`
            // means you hold something over them so heavy that nothing about
            // the player leaves their lips. Letting them haggle would make the
            // leash a bargaining position rather than a fact.
            if (g.Leashed) { p.Resistance = 0; p.Why = "they were never going to refuse you"; }
            return p;
        }

        /// PUSH ONE LEVER.
        ///
        /// `weight` is how much of it — pounds as a fraction of what they would
        /// consider real money, how big the secret is, how bad the threat.
        /// `honest` is whether the thing being claimed is TRUE: a need you
        /// actually met, a secret you actually hold. A dishonest push is not
        /// blocked here — people do lie — but it cannot move anybody and it
        /// costs, because the person you are lying to knows their own life.
        public static Position Push(Position p, Gossiper g, Lever lever,
                                    double weight, bool honest = true)
        {
            if (p == null || g == null || p.Walked || p.Agreed) return p;

            weight = Feel.Clamp01(weight);
            p.Pushes.TryGetValue(lever, out int already);
            double fresh = Novelty(already);
            p.Pushes[lever] = already + 1;

            double suspicion = g.Suspicion?.Value ?? 0;

            // A LIE THEY CAN CHECK IS THE WORST MOVE IN THE FILE, and it has to
            // be, or claiming a favour you never did would be strictly better
            // than doing it. It moves them not at all and it costs like a
            // threat, because being taken for a fool is the insult people
            // forgive last.
            if (!honest)
            {
                p.Resentment += ThreatResentment * 0.8;
                p.Why = "they know what you did and did not do";
                return Settle(p);
            }

            double move = 0, resent = 0;
            switch (lever)
            {
                case Lever.Money:
                    // Blunted by suspicion: a frightened man reads cash as a
                    // deposit on something worse.
                    move = weight * (0.25 + 0.55 * g.Greed) * (1.0 - 0.5 * suspicion);
                    break;

                case Lever.Need:
                    // The strongest, and it does not care what they think of
                    // you — you solved their problem and that is a fact about
                    // the world rather than an opinion about you.
                    move = weight * 0.85;
                    break;

                case Lever.Secret:
                    // Ignores greed and nerve. Wins rooms. See `LoyaltyCost`.
                    move = weight * 0.8;
                    resent = SecretResentment * weight;
                    break;

                case Lever.Threat:
                    // Works on the frightened. Always costs, and the cost does
                    // not scale down with novelty the way the movement does —
                    // the second threat persuades less and offends the same.
                    move = weight * (0.2 + 0.7 * (1.0 - g.Nerve));
                    resent = ThreatResentment * (0.5 + 0.5 * weight);
                    break;

                case Lever.Respect:
                    // Free, slow, and the only one that compounds: it works
                    // better the more they already think of you, so it is the
                    // lever that rewards having been decent earlier.
                    move = weight * (0.15 + 0.45 * g.Loyalty);
                    break;
            }

            p.Resistance = Feel.Clamp01(p.Resistance - move * fresh);
            p.Resentment += resent;
            return Settle(p);
        }

        static Position Settle(Position p)
        {
            if (p.Resentment >= WalksAt)
            {
                p.Walked = true;
                p.Why = "you pushed them past the point of dealing with you";
            }
            else if (p.Resistance <= 0)
            {
                p.Why = "they agreed";
            }
            return p;
        }

        /// WHAT THE SCENE COST, PAID AFTER IT ENDS AND WHETHER OR NOT YOU WON.
        ///
        /// This is the number that makes the fast levers expensive. Resentment
        /// carries out of the room as lost loyalty, and a secret keeps charging
        /// on top of it — you did not persuade them, you owned them, and they
        /// know the difference.
        ///
        /// Deliberately NOT applied inside `Push`: a negotiation the player
        /// abandons half way should still have cost them, and a caller that
        /// forgets to settle up would otherwise get coercion for free.
        public static double LoyaltyCost(Position p)
        {
            if (p == null) return 0;
            double cost = p.Resentment * 0.5;
            if (p.Pushes.ContainsKey(Lever.Secret)) cost += 0.2;
            return cost;
        }

        /// WHAT THE MODEL IS TOLD, and the reason this file exists rather than a
        /// stat check. It is a stance, not a script: no words the character must
        /// say, only where they stand and what they are weighing.
        ///
        /// `ConversationEngine` puts this in the character block, so the person
        /// argues their own position in their own voice — and because the
        /// position is computed here, they cannot be talked into something the
        /// game has not agreed to.
        public static string Stance(Position p, Gossiper g)
        {
            if (p == null || g == null) return "";
            if (p.Walked) return "You are done talking to this person. You are not doing what they ask, and you want them gone.";
            if (p.Agreed) return "You have decided to say yes. Say so in your own words, without ceremony.";

            string near = p.Resistance < 0.35 ? "You are close to agreeing and you have not said so yet."
                        : p.Resistance < 0.7 ? "You are listening, and not convinced."
                        : "You do not want to do this.";
            string sore = p.Resentment > 0.5 ? " You are angry at how you are being spoken to, and it is showing."
                        : p.Resentment > 0.2 ? " Something in how they are asking has put your back up." : "";
            return near + sore + " Do not state a number or a condition the conversation has not reached.";
        }
    }
}
