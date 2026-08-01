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

        /// NULL IS NAMED RATHER THAN DEREFERENCED, and it is not hygiene.
        ///
        /// `SaveChaos` found this from the other end: a save file whose rumour
        /// record had lost its `subj` key handed a null straight into
        /// `ToLowerInvariant()`, and the NullReferenceException went all the way
        /// out through `SaveCodec.Restore` — which the front end catches
        /// `SaveIncompatibleException` from, and nothing else. A player with a
        /// half-written save got a stack trace on the load screen.
        ///
        /// NOT MADE PERMISSIVE. Defaulting null to "" would have silenced the
        /// crash and built a fact with an empty subject, and `SameTopic`
        /// compares subject and predicate — so every gutted fact would match
        /// every other gutted fact and contradict them. A quiet wrong answer in
        /// the one system the game uses to decide whether a lie lands is worse
        /// than a loud refusal, so the refusal is loud and says which argument.
        public Fact(string subject, string predicate, string value)
        {
            if (subject == null) throw new ArgumentNullException(nameof(subject));
            if (predicate == null) throw new ArgumentNullException(nameof(predicate));
            if (value == null) throw new ArgumentNullException(nameof(value));
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

        /// Why this person's suspicion is where it is, most recent last.
        ///
        /// BOUNDED, because it was not, and `Soak` measured the consequence:
        /// over 499 in-game days the seven-person street accumulated 684 of
        /// these, strictly monotonically, at +1.363 a day and with nothing that
        /// ever removes one. The rumour counts in the same run oscillated
        /// between 9 and 74 — gossip decays, and the contrast is what made this
        /// one legible as a leak rather than as traffic. On a long save it
        /// grows until the save does.
        ///
        /// AND NOTHING READS IT. Three writers, zero call sites anywhere in the
        /// game, the editor or the tools — rule 6, `built is not running`, in a
        /// field rather than an API. That is why the fix is a cap and not a
        /// deletion: "why is Lena suspicious of me" is the moat this project is
        /// actually built on (information 90 against a best-in-class 65), and a
        /// trail nobody reads yet is a trail somebody should. Deleting it would
        /// make wiring that answer a rewrite instead of a hookup. It belongs on
        /// the reach ledger, not in the bin.
        ///
        /// THE CAP IS DERIVED, NOT PICKED. `Value` is clamped to 0..1 and each
        /// event moves it by roughly 0.12 to 0.35 (`ContradictionSuspicion`
        /// 0.35, `LeakSuspicion` 0.12), so the most recent dozen or so entries
        /// already sum to several times the entire range — nothing older can
        /// still be part of the explanation for where the number sits now.
        /// Thirty-two is that dozen with room, and it makes the trail a fixed
        /// cost per person forever.
        public const int MaxReasons = 32;

        public IReadOnlyList<string> Reasons => _reasons;
        readonly List<string> _reasons = new List<string>();

        void Note(string line)
        {
            _reasons.Add(line);
            // One at a time, from the front: this is called once per event, so
            // the list is never more than one over.
            if (_reasons.Count > MaxReasons) _reasons.RemoveAt(0);
        }

        public SuspicionLevel Level =>
            Value < 0.25 ? SuspicionLevel.Trusting :
            Value < 0.50 ? SuspicionLevel.Uneasy :
            Value < 0.80 ? SuspicionLevel.Suspicious :
                           SuspicionLevel.Confronting;

        /// Save-load overlay: value only; the reasons trail restarts.
        public void Restore(double value)
        {
            Value = Math.Clamp(value, 0.0, 1.0);
            Note("(restored from save)");
        }

        public void Raise(double amount, string reason)
        {
            Value = Math.Clamp(Value + amount, 0.0, 1.0);
            Note($"+{amount:0.00} {reason}");
        }

        public void Lower(double amount, string reason)
        {
            Value = Math.Clamp(Value - amount, 0.0, 1.0);
            Note($"-{amount:0.00} {reason}");
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
