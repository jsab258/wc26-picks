using System.Collections.Generic;

namespace Ledger.Game
{
    /// The Tier-2 sample ring: six ambient cards hand-written IN the pipeline
    /// template (game-design/tier2-pipeline-spec.md) to prove its fields before
    /// any batch generation. Only Mirela and Josip walk the street today (scene
    /// cost); the other four are data awaiting the district build-out. Validator
    /// rules honored by hand: schedules on real map spots, traits with at least
    /// one non-beige value, secrets with kinds and knowers, no orphan nodes.
    public static class Tier2Setup
    {
        public static CastMember Get(string name)
        {
            switch (name)
            {
                case "Mirela": return Mirela;
                case "Josip": return Josip;
                case "Viktor": return Viktor;
                default: return null;
            }
        }

        // secret: shameful — she shorts the scale for regulars she dislikes (knownBy: Sam)
        // need: her supplier cheats her; she wants someone to lean on him
        // connections: Ada 0.5, Sam 0.4
        static readonly CastMember Mirela = new CastMember
        {
            Circle = "day", Greed = 0.55, Nerve = 0.35, Loyalty = 0.4,
            Scene = "At her market stall, weighing vegetables, talking with the new bar owner.",
            Card = @"# Mirela
id: mirela
tier: ambient

## Summary
Runs the vegetable stall at the market corner, inherited from her mother. Knows every daytime stomach on Hook Street and what it can afford.

## Personality
Brisk, funny, keeps a running tally of favors in her head. Respects anyone who pays on time.

## Speech Style
Market patter — short, loud, price-shaped. Softens only mid-transaction.

## Hard Facts
- Marek, who owned the bar, died three weeks ago; he bought onions from me for twenty years.
- My stall is at the market corner every day from eight.
- My produce supplier shorts my crates and thinks I don't count.
",
        };

        // secret: criminal — he moves crates past the customs count for pocket money (knownBy: Rocco)
        // need: his daughter needs a reference for a Downtown job
        // connections: Rocco 0.6, Sam 0.3
        static readonly CastMember Josip = new CastMember
        {
            Circle = "night", Greed = 0.7, Nerve = 0.45, Loyalty = 0.35,
            Scene = "On the docks between shifts, talking with the new bar owner.",
            Card = @"# Josip
id: josip
tier: ambient

## Summary
Dock hand, twenty years on the water side. Big hands, small ambitions, one daughter he'd burn the port down for.

## Personality
Slow to warm, loyal once bought a drink. Complains about the harbormaster to anyone stationary.

## Speech Style
Few words, half of them about tides or overtime. Laughs like a winch.

## Hard Facts
- Marek, who owned the bar, died three weeks ago.
- I work the docks; Rocco and I go back twenty years.
- My daughter is smarter than this street and I mean to get her off it.
",
        };

        // Promoted from tier2-batch-1 (generated, validator-passed) because
        // Empire v1 needs his shop: the pawnbroker with the false-panel ledger.
        // secret: shameful — he skims appraisals to cover a gambling debt (knownBy: nobody)
        // need: a steady, quiet supplier of goods he doesn't have to ask about
        // connections: Lena 0.4, Sam 0.5
        // Schedule walks the built street until the district build-out gives
        // the pawnshop geometry; his shop exists in the books either way.
        static readonly CastMember Viktor = new CastMember
        {
            Circle = "day", Greed = 0.7, Nerve = 0.4, Loyalty = 0.4,
            Scene = "On his rounds between the market corner and the bar, always mid-calculation, talking with the new bar owner.",
            Card = @"# Viktor
id: viktor
tier: ambient

## Summary
Viktor has run the pawnshop on the corner for twenty-two years and can name the story behind half the jewelry in the Hook. He keeps a ledger of every deal, official and otherwise, tucked behind a false panel in his counter.

## Personality
He is shrewd and endlessly transactional, treating every conversation like a negotiation he intends to win. Underneath the haggling he's anxious, always doing sums in his head.

## Speech Style
He talks in numbers and counteroffers, rarely finishing a sentence without naming a price.

## Hard Facts
- I've owned the pawnshop for twenty-two years.
- I keep a ledger of every transaction, going back a decade.
- I have a back room where I store goods people don't want seen.
- I know the jewelers and dealers from here to the harbor office.
",
        };

        /// The four not yet walking: data for the district build-out, template-complete.
        /// (name, circle, greed/nerve/loyalty, secretKind, secretLine, knownBy, need)
        public static readonly List<string[]> Pending = new List<string[]>
        {
            new[] { "Ferko", "night", "0.6/0.5/0.3", "shameful", "sleeps in his cab because he lost the flat to cards", "Josip", "a big fare he can brag about" },
            new[] { "Ruta", "both", "0.8/0.6/0.25", "criminal", "fences dock pilferage through the pawnshop back room", "", "someone to scare off the New crew kid shaking her down" },
            new[] { "Vesna", "day", "0.2/0.7/0.5", "shameful", "reads Father Emil's letters before he does", "", "her nephew needs bar work, no questions" },
            new[] { "Tibor", "day", "0.4/0.4/0.45", "shameful", "waves through friends without tickets and doctors the count", "Ruta", "cover for the audit week" },
        };
    }
}
