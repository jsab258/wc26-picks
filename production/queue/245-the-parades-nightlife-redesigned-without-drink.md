# 245. The Parade's nightlife, redesigned without drink, with pictures

STATUS: BLOCKED IN PART, 2026-09-10. THE STREET HALF IS IN FLIGHT: the commission lane began `parade-night-*` drawings on 2026-09-10 and has been given the street and told to leave the interiors alone. What remains blocked is the half that depends on part 4. Part 3 of Jafar's commission of 2026-09-10, in his
words: "the Parade's nightlife redesigned without drink with pictures".
BLOCKED ON: `production/specs/the-pub-without-drink.md`, part 4 of the same
commission, in flight now. The reason is not sequencing tidiness: part 4 decides
what a room full of people is FOR when nobody is drinking, and this item draws
a whole district of those rooms. Drawing first would mean drawing a guess.

## What the Parade is, and why it is the hardest district under D18

`canon.md:11` lists the districts and gives the Parade one word: nightlife. That
is its entire identity, and D18 removes the trade that identity was built on.
Every other district loses a detail. This one loses its premise.

What the town atlas says the Parade is, from
`origin/art/atlas-01:production/art/atlas-01/DISTRICTS.md:12`:

    Cinema, drink trade, taxi calls, occasional contemporary cafe/wine-bar
    refits; daytime cleaning/deliveries precede night queues

Two of those are now void: "drink trade" and "wine-bar refits". Three survive
and they are the seed of the answer: THE CINEMA, THE TAXI CALLS, and the
day-before-night rhythm of cleaning and deliveries.

`canon.md:27` also puts the PARADE RATS here, a wall crew, so the district
carries a faction whose territory is the street itself.

## The connection that is already built and should be used

Mickey's became a minicab office by Jafar's ruling of the same day, and the
atlas row for this district already names "taxi calls" as part of its night. A
cab office and a nightlife street are the same economy: the queue at the end of
the night IS the cab rank. The Mickey's package now in production has a street
rank drawing, so part of this district's night is drawn already.

That is also where the moat lives on this street. A cab rank at midnight is one
of the few places in a town where strangers stand still together long enough to
overhear each other, and the driver hears everything and remembers.

## Done looks like

1. A written redesign, in the shape of the existing district work, that says
   what the Parade's night IS: what opens, what the queues are for, what the
   noise is, who is on the street at eleven, and what the player can do there.
   It must answer the same test part 4 answers: does information still move
   through this street to somebody who was not there?
2. Pictures, at the standard of the in-house Hook sheet approved by Jafar on
   2026-09-10, produced by the three-pass method he made the standard for
   remaining district sheets on the same day.
3. The atlas row corrected on `origin/art/atlas-01` so the two void trades stop
   feeding the sheet generator. `tools/imagegen/sheet-furniture.py:49` reads
   that atlas from the branch, so an uncorrected row reaches a picture.
4. A provenance table saying which words came from which source, per Jafar's
   standing ruling on the concept route.

## Dependencies and risk

Depends on part 4, and on queue 244 for the atlas correction to be visible to
the content gate at all.

Risk, and it is the real one: this is the district where a subtraction is most
likely to read as a hole. A nightlife street with the drink removed and nothing
put in its place will look like a set with the extras sent home, and Meridian
Test condition 3 is a person calling the town alive without being prompted.
Judge the pictures against that sentence and not against compliance.
