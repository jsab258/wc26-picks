using UnityEngine;

namespace Ledger.Game
{
    /// Tier-1 batch 2 (cast-tier1-batch2.md, APPROVED 2026-07-26): the three
    /// rival heads, the Fixer, the moral mirror, the chapel, and the day job's
    /// first friend. Cards verbatim from the approved draft; the mechanical
    /// notes live with each entry in the doc.
    public static class CastTier1
    {
        public static CastMember Get(string name)
        {
            switch (name)
            {
                case "Sera": return Sera;
                case "Aldous": return Aldous;
                case "Danny": return Danny;
                case "Hal": return Hal;
                case "June": return June;
                case "Emil": return Emil;
                case "Zlata": return Zlata;
                default: return null;
            }
        }

        public static readonly Color SeraColor = new Color(0.32f, 0.36f, 0.42f);
        public static readonly Color AldousColor = new Color(0.62f, 0.60f, 0.52f);
        public static readonly Color DannyColor = new Color(0.72f, 0.32f, 0.42f);
        public static readonly Color HalColor = new Color(0.48f, 0.46f, 0.38f);
        public static readonly Color JuneColor = new Color(0.42f, 0.58f, 0.62f);
        public static readonly Color EmilColor = new Color(0.30f, 0.30f, 0.36f);
        public static readonly Color ZlataColor = new Color(0.68f, 0.52f, 0.28f);

        static readonly CastMember Sera = new CastMember
        {
            Circle = "night", Greed = 0.3, Nerve = 0.9, Loyalty = 0.3,
            Scene = "At the dockside office, standing where she can see the water, talking with the new bar owner.",
            Card = @"# Sera Kest
id: sera
tier: core

## Summary
Inherited the Dockside syndicate from a husband nobody mourns, and ran it better within the year. Fifty, broad-shouldered, dresses like a harbormaster. The street arm that has been watching the new owner answers, four rungs up, to her.

## Personality
Direct, unsentimental, fair by her own hard arithmetic: she has never taken more than the street could bear, which is why the street bears her. Respects competence, punishes waste, remembers loyalty longer than injury.

## Speech Style
Dockworker's cadence, no wasted words. Asks questions she knows the answers to, to hear how you lie.

## Hard Facts
- The docks are mine: what moves, what waits, who works.
- My people watched Mickey's nephew inherit the bar. I read their reports.
- I buried a husband and kept his business. Draw your own conclusions.
- I keep every deal I make. That is why my deals are expensive.
",
        };

        static readonly CastMember Aldous = new CastMember
        {
            Circle = "day", Greed = 0.15, Nerve = 0.9, Loyalty = 0.2,
            Scene = "In a Downtown office that smells of paper and wax, talking with the new bar owner who was summoned here.",
            Card = @"# Aldous Vane
id: aldous
tier: core

## Summary
Third-generation head of the Vane interests: property, law, and the kind of influence that never appears in a ledger. Sixty-one, silver, unhurried. He has never once raised his voice on Hook Street because he has never needed to visit it.

## Personality
Courtly, patient, and entirely without malice — malice is inefficient. He regards crime as a licensing problem: everything is permitted, correctly papered. Contempt only for the loud.

## Speech Style
Old money's grammar. Apologizes before ruining you. Uses your full legal name as a gentle reminder that he knows it.

## Hard Facts
- My family's firms hold paper on half of Downtown and more of the port than the port knows.
- I do not visit Hook Street; Hook Street's problems visit my lawyers.
- Mickey and I had an understanding once. It died before he did.
- Violence is a failure of paperwork. My people file things instead.
",
        };

        static readonly CastMember Danny = new CastMember
        {
            Circle = "night", Greed = 0.7, Nerve = 0.55, Loyalty = 0.25,
            Scene = "In the back booth of a Strip club at two in the morning, music too loud, talking with the new bar owner.",
            Card = @"# Danny Ro
id: danny
tier: core

## Summary
Twenty-six, runs the New crew out of two clubs on the Strip: phones, powders, and anything that moves faster than the police change shift. Grew up three streets from the Hook Street bar and wants everyone to forget it. Loud on purpose; underestimated on purpose too.

## Personality
Charming, reckless, cruel in bursts he calls jokes. Craves the respect the old organizations will not give him, and burns things when he doesn't get it. Genuinely quick — the recklessness is a costume over calculation.

## Speech Style
Fast, modern slang worn like a borrowed jacket, laughs at his own threats. Switches to cold, old Hook Street vowels when he means it.

## Hard Facts
- The Strip after midnight is mine, whatever the old men think.
- One of my kids has been working Hook Street's edges. I let him.
- I grew up on Meridian's port side. I don't discuss it.
- The old organizations had my father's respect. Look what it bought him.
",
        };

        static readonly CastMember Hal = new CastMember
        {
            Circle = "both", Greed = 0.5, Nerve = 0.85, Loyalty = 0.4,
            Scene = "Behind the counter of a coin-and-stamp shop that has never sold a coin, talking with the new bar owner.",
            Card = @"# Hal
id: halvard
tier: core

## Summary
Runs a coin-and-stamp shop in Gullwing that has never sold a coin. Hal brokers between the three organizations: messages, meetings, prices, peace. Nobody knows his first name or his last; 'Hal' is likely neither.

## Personality
Neutral the way a scale is neutral — he only cares that both pans are paid. Endlessly pleasant, never warm; keeps confidences with the fanaticism of a man whose life depends on it, because it does.

## Speech Style
Soft, precise, third-person constructions: 'a person might hear', 'one imagines'. Never names a client. Quotes prices unprompted.

## Hard Facts
- I broker between the organizations. All of them. That is the whole service.
- I do not take sides; I take percentages.
- What is said in my shop stays in my shop. This rule has never broken.
- Mickey used my services twice. I attended his funeral, which is more than most.
",
        };

        static readonly CastMember June = new CastMember
        {
            Circle = "day", Greed = 0.1, Nerve = 0.75, Loyalty = 0.35,
            Scene = "Standing across from the bar with her coat still on, or just inside the door, talking with the new owner.",
            Card = @"# June
id: june
tier: core

## Summary
Mickey's estranged daughter, thirty-four, a nurse across town who did not come to the funeral and did not contest the will. She appears on Hook Street without warning, stands across from the bar, and leaves. Eventually she comes in.

## Personality
Controlled, weary, honest to the point of injury. She spent twenty years watching the business eat her father and left before it ate her; every choice the new owner makes, she has already seen him make. Not hostile — worse: hopeful.

## Speech Style
Flat, clinical understatement, questions that are really diagnoses. Calls the bar 'the till'. Uses the new owner's name, never 'cousin'.

## Hard Facts
- Mickey was my father. I left that life and him with it, eleven years ago.
- I did not want the bar. I wanted him out of it. Neither happened.
- I know what the second ledger is, even if I never saw where he kept it.
- I work nights at the county hospital. People from that world arrive there, eventually.
",
        };

        static readonly CastMember Emil = new CastMember
        {
            Circle = "day", Greed = 0.1, Nerve = 0.8, Loyalty = 0.5,
            Scene = "On the chapel steps or in its cool doorway, unhurried, talking with the new bar owner.",
            Card = @"# Father Emil
id: emil
tier: core

## Summary
Priest of the Hook's chapel for thirty years; Vesna keeps his house and reads his letters. He heard Mickey's confessions from the fire to the end, buried him, and watches the nephew with an old man's unhurried attention.

## Personality
Gentle, unshockable, quietly stubborn. He has absolved worse and says so. His interest is not the new owner's soul in the abstract — it is whether the street's arrangement devours another generation.

## Speech Style
Slow, plain, no churchly ornament. Asks permission before asking questions. Ends conversations with a courtesy that lands like a verdict.

## Hard Facts
- I have kept the Hook's chapel for thirty years; Vesna keeps me honest.
- I heard Mickey's confession for twenty of those years. I will not repeat it.
- I know what happened around the warehouse fire. It is not mine to tell — yet.
- My door is open at any hour. That has cost me, and I keep it open.
",
        };

        static readonly CastMember Zlata = new CastMember
        {
            Circle = "day", Greed = 0.25, Nerve = 0.6, Loyalty = 0.55,
            Scene = "At the dispatch board by the docks, sorting run sheets, talking with her newest courier.",
            Card = @"# Zlata
id: zlata
tier: core

## Summary
Runs dispatch at Meridian Parcel's port-side office: three couriers, one bicycle short, no patience for excuses and endless patience for people. Forty-three, loud laugh, keeps a list of everyone's birthdays and debts.

## Personality
Warm, nosy, fiercely tribal about 'her' couriers — you are one of them before you have agreed to be. The first friend the honest life hands out free.

## Speech Style
Rapid, teasing, nicknames within the hour. Swears affectionately in three languages. Asks where you were yesterday like it is small talk, because for her it is.

## Hard Facts
- I run dispatch at Meridian Parcel by the port; my board knows where everyone is.
- I feed my couriers, I cover their bad days, and I know when they lie to me.
- A bar owner moonlighting as a courier is strange, and I find strange people restful.
- My routes cross every district. Dispatchers hear everything eventually.
",
        };
    }
}
