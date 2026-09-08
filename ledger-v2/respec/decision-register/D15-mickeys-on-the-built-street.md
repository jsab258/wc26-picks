# D15: Mickey's is sited on the street that already exists
Date: 2026-09-08. Status: APPROVED (Jafar, in session). Owner: Direction.
Context: the project has exactly one street built to the visual bar, walkable,
and proven so by machine: 593 pieces, a character that walks it, collision that
stops at a named terrace wall, and a clip on Jafar's phone. It also has a pub
the whole premise turns on, Mickey's, which existed only as a canon line. Two
lines of work, the art line and the game line, were each free to put it
somewhere, which is how a project ends up building one place twice.
Choice, in Jafar's words: "Mickey's, the player's pub, is sited on the street
that already exists and is walkable. The art line and the game line share that
one location."
The address, concretely: the built street is the east Parade, named through
every piece in production/specs/vignette-pieces.json as east_parade_*, with six
ground-floor shopfronts at C7_shop_glazing (east_parade_glass0 to glass5). One
of those bays is Mickey's. Which bay is not decided here and is a small
authored choice; what is decided is the STREET, so nothing is built twice.
THE CANON CONFLICT THIS CREATES, NAMED RATHER THAN SMOOTHED OVER. canon.md
line 10 lists the districts as "the Hook (old port, the player's pub), Copper
Row (market quarter), the Exchange", line 40 says Mickey's is "in the Hook",
and line 19 names the wall crews as "QUAY FIRM (the Hook), PARADE RATS (the
Parade)". The Hook and the Parade are two different districts in canon, so
siting Mickey's on the Parade MOVES IT. Canon is Jafar's and he has ruled, so
canon is updated at both sites and this record is the reason. But two
consequences follow that this record cannot settle alone and that a session
must not quietly invent:
1. "the Hook (old port, the player's pub)" loses its parenthetical. The Hook
   is still the old port. It is no longer where the player lives.
2. The Parade Rats are the wall crew of the street the player's pub now stands
   on. That is either a gift to the story or an accident, and it is Jafar's
   call which.
Both are carried to him in the closing report rather than resolved here.
Instrument: nothing new. The siting is proved by the piece the pub occupies
appearing in the built street's own bill of materials, which the walk verdict
already counts (piecesEmitted=593/593).
Revisit when: Jafar answers the two consequences above, or a gate failure names
this decision.

## Amendment 2026-09-08: OPTION C, ruled by Jafar. Mickey's never moved.

The record above put Mickey's on the Parade and updated canon to match. Jafar
ruled option C instead, in his words: "The built street is Quay Street in the
Hook. Revert the canon edit; keep the piece IDs, retag the street's district.
The wall crew becomes a Hook crew; propose a one-line rename. Canon and the
atlas now agree."

WHAT WAS WRONG WITH THE ORIGINAL, and it is worth saying because the ruling is
better than the reasoning that produced it. The record treated the street's
ASSET NAMES as a claim about its geography. Every piece is called
`east_parade_*`, so the street was read as being on the Parade, and Mickey's
was moved to meet it. But those names were minted before the street had a
district at all: they are identifiers, not an address. The right move was to
name the street, not to move the pub to the naming convention. Canon already
said Quay Street is in the Hook and that Mickey's is in the Hook; both were
correct and neither needed changing.

APPLIED. The two canon edits are reverted, so the district list reads "the Hook
(old port, the player's pub)" and the Player line reads "in the Hook" as they
did. Canon gains one line saying the built street IS Quay Street, in the Hook,
and that the 593 `east_parade_*` identifiers carry no district claim. They are
kept: renaming them would break the bill of materials, the golden rows and
every verdict key that has ever named a piece, for nothing.

CONTENT RETAGGED IN THE SAME PASS, because a ruling that does not reach the
shipped words is a ruling nobody applied. `content/dialogue/crime-witness-v1.json`
named the street eight times and `production/specs/dialogue-crime-witness-v1.md`
three times; all eleven now read Quay Street. Every line took the substitution
without a rewrite ("a smash on Quay Street about half nine"), and
`dialogue-verify` is clean at 0 findings over 24 lines, 276 pairs, worst
overlap 0.28.

THE ONE-LINE RENAME, PROPOSED AND NOT MINTED, because he asked for a proposal:

    PARADE RATS becomes TIDE RATS, a Hook crew.

The reason in one line: it keeps RATS, so the wall reads as the same crew that
moved rather than a name invented to fill a gap, and TIDE is a port word that
belongs to the Hook in a way PARADE never did. The alternative, which needs no
new name at all, is to leave the built street's walls to QUAY FIRM, which canon
already places in the Hook; that is cleaner but loses a crew. Jafar's word
either way, and until then `canon.md` still carries PARADE RATS (the Parade),
which remains true: the Parade still exists as the nightlife district.

STILL OPEN AND STILL HIS, unchanged by this amendment: nothing. The two
consequences the original record raised were both artifacts of the move and
disappear with it. The Hook keeps the player's pub, and the Parade keeps its
own crew.
