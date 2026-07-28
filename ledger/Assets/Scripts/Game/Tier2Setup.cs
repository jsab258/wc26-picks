using System.Collections.Generic;

namespace Ledger.Game
{
    /// The Tier-2 sample ring: six ambient cards hand-written IN the pipeline
    /// template (game-design/tier2-pipeline-spec.md) to prove its fields before
    /// any batch generation. Only Marla and Joey walk the street today (scene
    /// cost); the other four are data awaiting the district build-out. Validator
    /// rules honored by hand: schedules on real map spots, traits with at least
    /// one non-beige value, secrets with kinds and knowers, no orphan nodes.
    public static class Tier2Setup
    {
        public static CastMember Get(string name)
        {
            switch (name)
            {
                case "Marla": return Marla;
                case "Joey": return Joey;
                case "Victor": return Victor;
                case "Ferko": return Ferko;
                case "Rita": return Rita;
                case "Vesna": return Vesna;
                case "Tibor": return Tibor;
                default: return null;
            }
        }

        // secret: shameful — she shorts the scale for regulars she dislikes (knownBy: Sam)
        // need: her supplier cheats her; she wants someone to lean on him
        // connections: Ada 0.5, Sam 0.4
        static readonly CastMember Marla = new CastMember
        {
            Circle = "day", Greed = 0.55, Nerve = 0.35, Loyalty = 0.4,
            Scene = "At her market stall, weighing vegetables, talking with the new bar owner.",
            Card = @"# Marla
id: mirela
tier: ambient

## Summary
Runs the vegetable stall at the market corner, inherited from her mother. Knows every daytime stomach on Hook Street and what it can afford.

## Personality
Brisk, funny, keeps a running tally of favors in her head. Respects anyone who pays on time.

## Speech Style
Market patter — short, loud, price-shaped. Softens only mid-transaction.

## Hard Facts
- Mickey, who owned the bar, died three weeks ago; he bought onions from me for twenty years.
- My stall is at the market corner every day from eight.
- My produce supplier shorts my crates and thinks I don't count.
",
        };

        // secret: criminal — he moves crates past the customs count for pocket money (knownBy: Rocco)
        // need: his daughter needs a reference for a Downtown job
        // connections: Rocco 0.6, Sam 0.3
        static readonly CastMember Joey = new CastMember
        {
            Circle = "night", Greed = 0.7, Nerve = 0.45, Loyalty = 0.35,
            Scene = "On the docks between shifts, talking with the new bar owner.",
            Card = @"# Joey
id: josip
tier: ambient

## Summary
Dock hand, twenty years on the water side. Big hands, small ambitions, one daughter he'd burn the port down for.

## Personality
Slow to warm, loyal once bought a drink. Complains about the harbormaster to anyone stationary.

## Speech Style
Few words, half of them about tides or overtime. Laughs like a winch.

## Hard Facts
- Mickey, who owned the bar, died three weeks ago.
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
        static readonly CastMember Victor = new CastMember
        {
            Circle = "day", Greed = 0.7, Nerve = 0.4, Loyalty = 0.4,
            Scene = "On his rounds between the market corner and the bar, always mid-calculation, talking with the new bar owner.",
            Card = @"# Victor
id: viktor
tier: ambient

## Summary
Victor has run the pawnshop on the corner for twenty-two years and can name the story behind half the jewelry in the Hook. He keeps a ledger of every deal, official and otherwise, tucked behind a false panel in his counter.

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

        // The rest of the ring, promoted with the district build-out. Their
        // secrets live in SecretsSetup; their needs in EmpireSetup.

        // secret: shameful — sleeps in his cab, lost the flat to cards (knownBy: Joey)
        // need: a big fare he can brag about
        static readonly CastMember Ferko = new CastMember
        {
            Circle = "night", Greed = 0.6, Nerve = 0.5, Loyalty = 0.3,
            Scene = "At the cab rank or leaning on the cab he lives out of, talking with the new bar owner.",
            Card = @"# Ferko
id: ferko
tier: ambient

## Summary
Drives the Hook's only night cab, a diesel relic he keeps running on spite. Knows which doors open after midnight and who came out of them.

## Personality
Big talk, small luck. Friendly to anyone who might be a fare, bitter about everyone who ever won money off him.

## Speech Style
Racetrack patter — odds, sure things, almosts. Calls every destination 'two minutes away'.

## Hard Facts
- I drive the only night cab in the Hook; the rank is mine.
- I see who moves around this district after dark, and where they get out.
- Joey and I go back; we talk when the docks let him go.
",
        };

        // secret: criminal — fences dock pilferage through the pawnshop back room (knownBy: nobody)
        // need: someone to scare off the New crew kid shaking her down
        static readonly CastMember Rita = new CastMember
        {
            Circle = "both", Greed = 0.8, Nerve = 0.6, Loyalty = 0.25,
            Scene = "In and out of the pawnshop's back door with a canvas bag, talking with the new bar owner.",
            Card = @"# Rita
id: ruta
tier: ambient

## Summary
Moves goods nobody reports missing between the docks and the pawnshop's back room. Sharp-eyed, quick-handed, owes nobody an explanation.

## Personality
All business, allergic to sentiment. Prices everything, including favors and people, and pays her debts to the penny — which is why she hates owing anything.

## Speech Style
Short. Numbers where words would do. Ends conversations by walking away mid-sentence.

## Hard Facts
- I do business between the docks and Victor's pawnshop; ask no further.
- Some Strip kid has been taxing my rounds lately, and it is becoming a problem.
- I know what moves through this district and what it's worth, to the crown.
",
        };

        // secret: shameful — reads Father Emil's letters before he does (knownBy: nobody)
        // need: her nephew needs bar work, no questions
        static readonly CastMember Vesna = new CastMember
        {
            Circle = "day", Greed = 0.2, Nerve = 0.7, Loyalty = 0.5,
            Scene = "Sweeping the chapel steps or at the market for the Father's table, talking with the new bar owner.",
            Card = @"# Vesna
id: vesna
tier: ambient

## Summary
Keeps house for Father Emil at the chapel — the floors, the ledgers, the letters, the confidences that leak through old doors. The district's quietest well of information.

## Personality
Patient, devout on the surface, ferociously protective of her family. Judges silently and forgets nothing.

## Speech Style
Soft, unhurried, full of blessings that carry edges. Asks after your mother even if she's never met her.

## Hard Facts
- I keep house for Father Emil at the chapel; I have for eleven years.
- People tell the chapel things they tell no one else.
- My nephew is a good boy who needs steady work, whatever anyone says.
",
        };

        // secret: shameful — waves through friends without tickets and doctors the count (knownBy: Rita)
        // need: cover for the audit week
        static readonly CastMember Tibor = new CastMember
        {
            Circle = "day", Greed = 0.4, Nerve = 0.4, Loyalty = 0.45,
            Scene = "At the customs shed window stamping what needs stamping, talking with the new bar owner.",
            Card = @"# Tibor
id: tibor
tier: ambient

## Summary
Assistant at the customs shed, twenty years of stamps and counts. Nervous, meticulous in public, flexible in private — the crack in the port's paperwork.

## Personality
Anxious, eager to please the wrong people, convinced everyone is about to notice him. Loyal to whoever last made him feel safe.

## Speech Style
Over-explains. Starts answers with 'strictly speaking'. Laughs at things that aren't jokes.

## Hard Facts
- I work the customs shed; my stamp moves cargo, strictly speaking.
- There is an audit coming, there is always an audit coming.
- Rita and I understand each other; I won't say more than that.
",
        };
    }
}
