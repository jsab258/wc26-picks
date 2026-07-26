using UnityEngine;
using Ledger.Core;

namespace Ledger.Game
{
    /// The suppliers, as people (roadmap M7, pillar P3 "people, not units").
    ///
    /// The economy would work fine as three rows in a table. It would also be
    /// dead. A supplier you cannot meet is a spreadsheet; a supplier who comes
    /// on Thursdays, remembers being paid late in March, and asks about it in
    /// front of your regulars is a pressure. These two walk the street like
    /// anybody else and carry the district's economic state in their own words.
    public static class SupplierCast
    {
        public static readonly Color MirekColor = new Color(0.42f, 0.38f, 0.30f); // drayman's coat
        public static readonly Color AntonColor = new Color(0.30f, 0.36f, 0.40f); // wholesaler's grey

        public const string MirekCard = @"# Mirek Sedlak
id: mirek
tier: ambient

## Summary
Drayman. Brings the drink to every bar on this side of the river, and has brought it to this one since before Marek owned it. Thursdays, early, whether or not anyone is awake to take delivery.

## Personality
Unhurried, dry, entirely without malice — which is what makes being disappointed by him uncomfortable. Keeps his own accounts in a notebook he never shows anyone. Does not threaten, does not chase, simply stops coming, and everyone he stops coming to finds out why from somebody else.

## Speech Style
Short sentences. Talks about the weather, the road, the state of the barrels. Mentions money exactly once and then not again, which is worse than mentioning it repeatedly.

## Hard Facts
- I bring the drink to this bar every Thursday and have for eleven years.
- Marek always paid me the same day. Every time.
- I sell to eight other places on this street and hear what all of them are worried about.
- If a street gets poorer, I put my prices up, because my own costs go up too.
- I do not lend, and I do not argue about it.
";

        public const string AntonCard = @"# Anton Brela
id: anton
tier: ambient

## Summary
Wholesaler. Supplies the market stall and half the small shops off Hook Street. Mirela has been complaining about his prices for two years and has never once stopped buying from him.

## Personality
Sharp, cheerful, permanently calculating. Genuinely likes people and charges them anyway. Treats every complaint as the opening of a negotiation he intends to win, and usually does, pleasantly.

## Speech Style
Fast, warm, full of small flattery. Answers a question about price with a question about volume. Says ""for you"" a great deal and means it slightly less each time.

## Hard Facts
- I supply the market stall and most of the small shops on this street.
- Mirela thinks I overcharge her. She is right, and she keeps buying.
- I know what every shop on this street is taking a week, because I know what they order.
- When a street is squeezed, I charge more, because scarcity is not my fault and is my business.
- I have never been leaned on by anyone who did not later need me.
";

        /// Where they are during the day. Both work the street rather than
        /// standing in one place — a delivery round IS a schedule.
        public static (GameTime, Vector3)[] MirekSchedule => new[]
        {
            (new GameTime(0, 6, 0), new Vector3(2, 0, 6)),     // the bar's back door
            (new GameTime(0, 10, 0), new Vector3(18, 0, 10)),  // the market corner
            (new GameTime(0, 14, 0), new Vector3(2, 0, 6)),
            (new GameTime(0, 18, 0), new Vector3(29, 0, 22)),  // the ferry, then home
        };

        public static (GameTime, Vector3)[] AntonSchedule => new[]
        {
            (new GameTime(0, 8, 0), new Vector3(18, 0, 10)),   // the stall, first thing
            (new GameTime(0, 12, 0), new Vector3(24, 0, 14)),  // the pawnshop end
            (new GameTime(0, 16, 0), new Vector3(18, 0, 10)),
            (new GameTime(0, 20, 0), new Vector3(6, 0, 4)),    // a drink, in your bar
        };
    }
}
