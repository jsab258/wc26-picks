using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// A structured fact an NPC holds: ("player", "location_d2_evening", "warehouse").
    /// Facts power the contradiction check that moves suspicion — the game state
    /// decides whether a lie lands; the LLM only performs the reaction.
    public class Fact
    {
        public string Subject;
        public string Predicate;
        public string Value;

        public Fact(string subject, string predicate, string value)
        {
            Subject = subject.ToLowerInvariant();
            Predicate = predicate.ToLowerInvariant();
            Value = value.ToLowerInvariant();
        }

        public bool SameTopic(Fact other) => Subject == other.Subject && Predicate == other.Predicate;
        public override string ToString() => $"{Subject}.{Predicate}={Value}";
    }

    public enum ClaimResult { Unknown, Consistent, Contradiction }

    /// What one NPC actually knows (witnessed or heard). Claims by the player are
    /// checked against this — an NPC cannot be talked out of what it knows.
    public class KnowledgeBase
    {
        public List<Fact> Facts { get; } = new List<Fact>();

        public void Learn(Fact fact)
        {
            // Later information about the same topic replaces earlier (people update).
            Facts.RemoveAll(f => f.SameTopic(fact));
            Facts.Add(fact);
        }

        public ClaimResult CheckClaim(Fact claim)
        {
            var known = Facts.FirstOrDefault(f => f.SameTopic(claim));
            if (known == null) return ClaimResult.Unknown;
            return known.Value == claim.Value ? ClaimResult.Consistent : ClaimResult.Contradiction;
        }
    }

    public enum SuspicionLevel { Trusting, Uneasy, Suspicious, Confronting }

    /// One NPC's suspicion toward the player, 0..1. Moved only by game events
    /// (contradictions, sightings, rumors, reassurance) — never by the LLM.
    public class SuspicionTracker
    {
        public double Value { get; private set; }
        public List<string> Reasons { get; } = new List<string>();

        public SuspicionLevel Level =>
            Value < 0.25 ? SuspicionLevel.Trusting :
            Value < 0.50 ? SuspicionLevel.Uneasy :
            Value < 0.80 ? SuspicionLevel.Suspicious :
                           SuspicionLevel.Confronting;

        public void Raise(double amount, string reason)
        {
            Value = Math.Clamp(Value + amount, 0.0, 1.0);
            Reasons.Add($"+{amount:0.00} {reason}");
        }

        public void Lower(double amount, string reason)
        {
            Value = Math.Clamp(Value - amount, 0.0, 1.0);
            Reasons.Add($"-{amount:0.00} {reason}");
        }

        /// Text the LLM receives describing how this character currently feels
        /// about the player — descriptive, not decision-making.
        public string ToPromptDescriptor()
        {
            switch (Level)
            {
                case SuspicionLevel.Trusting:
                    return "You currently trust this person and are at ease with them.";
                case SuspicionLevel.Uneasy:
                    return "Something about this person has started to feel off to you. You are friendly but a little guarded.";
                case SuspicionLevel.Suspicious:
                    return "You are actively suspicious of this person. Their stories haven't added up. You probe with pointed questions and share little.";
                default:
                    return "You have essentially caught this person in their lies. You confront them about the inconsistencies you know about, firmly.";
            }
        }
    }
}
