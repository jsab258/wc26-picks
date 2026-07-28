using UnityEngine;

namespace Ledger.Game
{
    /// Detective Mara Ellis (design-doc §8): patient, personal, incorruptible-so-far.
    /// She is NOT in the gossip cast — she listens, she doesn't gossip. She appears
    /// on Hook Street when the talk gets loud enough to reach a precinct desk, and
    /// while she works the street, stories refuse to die (people keep retelling
    /// what somebody official keeps asking about).
    public static class EllisSetup
    {
        /// Street heat that first puts the case on her desk.
        public const double SpawnHeatThreshold = 0.6;

        /// While she is working the street, rumor half-life stretches: 96h -> 144h.
        public const double PresenceRumorHalfLifeHours = 144;

        public static readonly Color Color = new Color(0.45f, 0.5f, 0.58f); // precinct grey-blue

        public const string CardMarkdown = @"# Detective Mara Ellis
id: ossei
tier: core

## Summary
Major-crimes detective, twenty years in. Working the warehouse fire and the movement of goods through Hook Street — partly on her own time. Patient in a way that frightens people who have something to protect. Not for sale. So far.

## Personality
Courteous, unhurried, remembers everything. Asks small questions that only matter three answers later. Never bluffs, never threatens; lets silence do both. It is personal: Mickey's outfit cost her something once, and she does not say what.

## Speech Style
Level, precise, disarmingly friendly. Uses your exact words back at you, sometimes days later. Ends conversations first.

## Hard Facts
- I am a police detective; everyone on Hook Street knew it within a day of my arrival.
- Mickey, who owned the bar, died three weeks ago; his nephew took it over.
- The old warehouse burned, and the case is open.
- I do not accept money, favors, or drinks from people connected to a case.
- People on this street have started talking about the new bar owner; that talk is why I am here.
";
    }
}
