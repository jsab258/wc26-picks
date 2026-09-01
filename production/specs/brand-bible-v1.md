# SPEC: brand bible v1, the four canon owes

STATUS: SPEC. Written 2026-09-01. Line: Signage/brand. Station 1 of 5.

## What this batch produces

One data file, content/brands/brand-bible-v1.json, holding the four brands
canon.md records as outstanding, plus the four already minted so that every
brand in the game is described in one place rather than four.

    owed by canon    the football club
                     the local paper
                     the pirate radio station
                     the regional TV channel

    already minted   Mickey's (the pub)
                     the Tivoli (cinema)
                     Meridian Harbour Board
                     Meridian Ferry

The minted four are RECORDED, not reinvented. Their names are canon and
changing one is a canon violation, not an edit.

## Why these four and why now

They are the four that other lines are blocked on. The radio segment line
cannot write a DJ link without a station. The dialogue line cannot have a
docker complain about a result without a club. A newspaper is the game's
main information surface in a town where news travels by paper, phone and
mouth, and the moat is information. None of these is decoration.

They are also the cheapest possible test of this assembly line end to end,
because a brand is a paragraph and a handful of fields. If the line cannot
manufacture eight paragraphs cleanly, it cannot manufacture a district.

## Canon constraints, which are not negotiable

1. EVERY BRAND IS FICTIONAL. No real clubs, papers, stations or channels, no
   real logos, no real people. This is canon and the license allowlist is
   law. A name that merely resembles a real one is still a violation if a
   reader would take it for the real thing.
2. THE ERA IS 1988 TO 1992 AND LATE-ANALOG. A pirate radio station in this
   window is a transmitter on a roof and a phone-in on a landline, not a
   stream. The paper has a classifieds page and a stone-subbed front. Any
   1950s or 1970s framing is wrong and is corrected on sight; both drifts
   have happened in this project.
3. IT IS A BRITISH PORT TOWN, not a generic one and not an American one. The
   club plays in a regional league nobody outside the county follows. The
   TV channel is a regional franchise, which is what regional television
   was in Britain in this window.
4. TONE. Wet, worked, unglamorous. A brand here has a history of being
   slightly disappointing.

## The fields every entry carries, and why each exists

    id            stable key, used by placement and by dialogue
    name          the in-world name
    kind          club | paper | radio | television | pub | cinema | body | ferry
    founded       a year inside or before the window
    register      how people in the town SAY the name, which is rarely the
                  full one. This is the field dialogue actually consumes
    physical      where it appears as a thing you can see: a sign, a van, a
                  stand, a masthead, a transmitter. A brand with no physical
                  presence cannot be placed and is not finished
    says          what its existence tells you about Meridian
    neverConfuse  the real-world thing a reader might mistake it for, named
                  so the check can be made rather than assumed
    license       tag, mandatory, per the allowlist discipline

`register` and `physical` are the two that make this useful rather than
decorative, and they are the two most likely to be skipped.

## Acceptance, by name

1. tools/canon-gate.py clean over the file. Era and brand screening.
2. A new check, tools/brand-verify.py, shipping with the batch and with its
   selftest, accepting case first. It must assert: every field present and
   non-empty; ids unique; founded inside or before the window; every entry
   has a physical presence; and the four minted names match canon.md
   character for character, read FROM canon.md rather than from a copy.
3. The four minted names unchanged. This is the rejecting case that matters:
   the check must go red if somebody renames Mickey's.
4. No entry may carry a real trade mark. The screen is the canon gate's
   word-bounded brand list, which already refused three of my own strings
   and was corrected by narrowing the match rather than loosening the rule.

## What this batch does NOT do

No placement, no signage geometry, no radio segments, no newspaper content.
Those are separate briefs on separate lines and folding them in here would
break the one-brief-one-deliverable law that exists because breaking it is
waste lesson 3.

## The open question this spec deliberately does not answer

Whether the football club's ground is a location the player can enter. That
is a world-building decision with a cost attached, and it belongs to whoever
owns the district plan, not to a brand entry. The entry names the ground and
stops there.
