# Ruling: the twelve clauses, the person guard, and the buried grate

STATUS: LIVE, verified 2026-09-09. Marked `reference` for docs-check
DELIBERATELY, reason below. Binding on the uncommitted batch of 2026-09-08,
whose last code commit is 4a983509, and on the one dispatch after it.
Verdict: LAND WITH AMENDMENTS. Five block the commit, four block the dispatch,
four are queue items. Director seat, tier 1, no shell: every number here that
is mine is arithmetic off committed files and says so.

WHY `reference` IS ON THIS FILE. It is past the 400-line cap for a live plan.
It is marked because it carries the measured arithmetic two builders work
against and the amendments they execute, which is the checker's own stated
ground, "mark it `reference` if it is a specification", and NOT because a
number was inconvenient. Said out loud for a second reason: the phrase
"reference commit" in the first draft of this header satisfied that check by
accident, which is a gate passing on a word nobody meant. If this record is
ever shortened under 400 lines the marker comes off in the same pass.

## 0. The date on this file, and why

The work is the evening of 8 September. The ruling is made after midnight in
Jafar's zone and my spawn row is 2026-09-09T00:00:45Z. The filename takes
2026-09-09 so that the date a tool reads out of the name agrees with the date
in the stamp at the foot, because `producer-check.py` pins a file's clock to
the ISO date in its own name and a record whose name and stamp disagree is a
gate failure waiting for a quiet week. The batch it rules on is 8 September's
and this document says so rather than letting the name imply otherwise.

## 1. The twelve clauses, as writing

Judged in the file, then judged spliced. Both frames were read with the code
that builds them, not from the brief's shorthand: `StreetVoice.Cap`
(StreetVoice.cs 768 to 771) moves exactly the first character for the
templates that open on the summary, so frame A renders "You hear all sorts.
It was Novak that put the window in..." and the lowercase-initial contract is
correct rather than a typographic fault. Frame B, Gossip.h 586, does not
capitalise and is the reason the contract exists. Both confirmed in the
source this session.

SIX OF TWELVE ARE CLEAN. cw-ws-r1-01, cw-ws-r1-02, cw-ws-r2-02 (see the spec
amendment at A5), cw-ws-r2-03, cw-ws-r3-02, cw-ws-r4-01. The best of them is
r1-01: a time, a place, a ceiling, and not a word past it. "about half nine"
and "donkey jacket" and "pale mac" are the right register: 1988 to 1992,
British port town, one working person telling another in a doorway. Nothing
in the twelve reads as American, as 1950s, or as a writing model performing
grit. The seaside-postcard smut is correctly absent; a smashed shop window is
not that moment and the spec already says so.

TWO FAIL AND MUST CHANGE BEFORE THE COMMIT.

1. `cw-ws-r2-01`: "the one that did the window on Quay Street had a donkey
   jacket on and moved sharp for a big lad". That is three identifying
   marks at a rung whose ceiling is one: a garment, a gait, and a build. The
   spec's own rung-2 sentence says "names one such mark and no more". It
   matters more in the clause than in the sentence because the clause is what
   the mill FILES, and canon's moat says nothing is ever wiped: a rung-2
   sighting that files a build is a permanent false memory with a measured
   rung on it.
2. `cw-ws-r4-02`: "...and he's in that shop often enough to be known
   blindfold". "that shop" has no antecedent inside the clause, and a clause
   is all the listener gets in frame A. The hearer is told which pub he owns
   and never which shop he is a regular of. Credit where it is due: this
   clause QUIETLY REPAIRS a fault in the committed sentence beside it, which
   has the shopkeeper serving him his bitter.

FOUR ARE WEAK AND SHIP, with the reason recorded so the next pass has
somewhere to start: `cw-ws-r1-03` ("whoever did it was a shape" predicates a
person as a shape, where the spoken sentence correctly makes the shape the
object of a verb), `cw-ws-r3-01` ("that face is known now" is noir narration,
not a doorway), `cw-ws-r3-03` ("would be known again anywhere" reaches), and
`cw-ws-r4-03` (the second half is flat and lands on r4-01's beat).

THE CELL-LEVEL FAULT THE REPETITION BOUND CANNOT SEE. All three rung-3
clauses and two of three rung-4 clauses end on an assertion of certainty, and
four of those six use the word "known". The hand-measured worst pairwise
overlap is 0.32 against a 0.60 bound, and that number is true and answers a
different question: it scores shared tokens, not a shared cadence. Three
variants exist so that a player hearing the cell twice hears two different
people; a shared closing device defeats that while passing the gate. The
passive constructions are partly forced, because frame A gives the witness no
antecedent and "she" cannot be used, and r3-02 shows the way out by putting
the action on him instead.

THE LIGHT AND THE CLOCK, FOUND WHILE SPLICING. At rung 1 two of three
clauses name a time of day or an artificial light: "about half nine" and "a
shape against the streetlight". The crime run stages overcast day at D1 12:00
with lanterns off (CrimeProbe.h kLightLevel and the perception ambient
floor), and at that seed the rung-1 pick is index 1, which is the streetlight
line (43 % 3 = 1, the probe's own arithmetic). Nothing in the bank is
conditioned on light and nothing checks it, so the first rung-1 sighting at
noon will have the town describing a streetlight. Queue item, not tonight's
edit, because the spoken sentences carry the same cues and splitting a row's
two strings on this would be worse than the fault.

THE WORST FINDING OF THE NIGHT IS NOT IN THE CLAUSES AT ALL, and it is the
one the rung discipline exists to prevent. The runtime pairs a summary with a
reply BY INDEX at one seed (`VariantIndex`, same seed, same modulus for both
contexts). In file order the rung-2 summaries are donkey jacket, limp and
cap, pale mac; the rung-2 replies are limp and cap, pale mac, donkey jacket.
Every one of the three pairs is therefore misaligned, and the reply deflates a
mark the summary never gave:

    index 0   she: a donkey jacket        he: "A limp and a cap."
    index 1   she: a limp and a cap       he: "A pale mac with the collar up."
    index 2   she: a pale mac             he: "A donkey jacket's not a face."

The spec calls this THE RULE THAT MAY NEVER BE BROKEN, acceptance step 4 is a
human reading against it, and the reading passed because the spec's own
reviewer list at lines 210 to 219 is grouped by rung rather than paired by
index: the checklist shaped the check, and a bundle reading cannot see a
pairing fault. Rung 1, 3 and 4 replies are generic enough to pair at any
index, so rung 2 is the whole of the exposure and it is the whole cell.

## 2. The person guard

HONEST IN INTENT, NOT YET HONEST WHERE IT IS READ. The comment at
crime-probe-test.cpp 69 to 77 states the limit correctly and states it in the
right words. The number is printed 280 lines later, and the reader who meets
`memoriesInFirstPerson=0/12` meets it in a verify footer or a CI log where no
comment travels with it. This project's own convention answers the question
already: `propBurialStat`, `overheardSummaryShapeRule`, `filedBranch` and
`propCollisionAsked` all carry their limit inside the printed value. The guard
is proven able to fire on the exact string that shipped corrupt (line 382),
which is rule 5b satisfied on both outcomes, and that is the half that was in
doubt. So the ruling is: the limit goes on the line, not into a comment.

AND ITS DENOMINATOR IS COUNTING THE WRONG SET. The 12 is `RowsRead`, which is
bank rows picked. The numerator is memories sniffed. A row whose mill passed
nothing leaves `Memory` at "nothing-measured", `AfterTheThat` returns the
whole string, the sniff says false, and an unexamined row counts as clean.
Gossip.h 586 writes the heard memory in the same block that emits the event,
so in practice the two move together and `tellingsComposed=12/12` is a
cross-check, but that is a different key on a different variable and rule 3b
asks what THIS denominator counted. Count the memories actually sniffed and
print that.

## 3. The burial, and what it means for Jafar's item 2

I checked the arithmetic myself off `production/specs/vignette-pieces.json`,
treating y as a centre and sy as a full height, which two dustbin rows already
confirm. cos(1.432096 deg) = 0.999688, tan = 0.025005. Street frame: +z is
east, which is why the covering carriageway is on the grate's WESTERN side.

    ground_east_carriageway  y -0.184266  sy 0.300  z 1.368751  sz 2.745858
    ground_east_channel      y -0.221766  sy 0.300  z 2.868751  sz 0.255080
    gully_dish_east          y -0.255     sy 0.300  z 2.8       sz 0.400
    prop_drainage_grate_01_0 y -0.0925    sy 0.015  z 2.8       sz 0.3999

The two slabs form ONE continuous cross-falling plane: the carriageway's top
face at its channel-side edge reads -0.068630 and the channel's top face at
its road-side edge reads -0.068625, five microns apart. So the surface over
the grate is that plane, y(z) = -0.034313 - 0.025005 (z - 1.368751), and the
grate's top is -0.085 flat. Cover depth across the grate's own footprint:

    west edge  z 2.60005   surface -0.065102   19.90 mm of cover
    centreline z 2.8       surface -0.070102   14.90 mm of cover
    east edge  z 2.99995   surface -0.075101    9.90 mm of cover

EVERY FIGURE THE BUILDER CORRECTED IS CONFIRMED AND ONE IS NOT REPRODUCIBLE.
13.234 mm is exact against the unpitched channel top, so the predecessor's
13.4 mm was a 0.166 mm slip and not a misread row, exactly as the builder
says. 14.91 mm at the centre line lands on my 14.90 mm, and the difference is
where the rotated corner is taken, not a disagreement. The cross-fall
contributes 1.66 mm at the centre line, so queue 162's "one or two
millimetres, not thirteen" was right. The slabs overlap by 0.469 mm in z with
no gap: there is nothing for the grate to poke through. The carriageway's
AABB overlaps 36.2 percent of the grate's footprint and its pitched solid
35.4 percent, so "the western 36 percent" is the AABB reading and is right.
The minimum cover under the carriageway is 16.37 mm, which is the builder's
16.4. I CANNOT REPRODUCE 18.7 mm as the other end of that range: the same
plane gives 19.90 mm at the grate's west edge, and 18.7 corresponds to z
2.648, which is 48 mm inside the footprint. The likeliest reading is that
18.7 is the extreme over SAMPLED CELL CENTRES and 19.90 the extreme over the
footprint. That is a statistic without its name, which is rule 2, and A8
settles it by printing the series rather than by either of us arguing.

THE CHANNEL IS NOT THE DEEPEST COVER: CONFIRMED, and it is the finding that
changes a conclusion. Cover is deepest on the road side and shallowest at the
kerb, which is what a cross-fall toward a gully implies. Queue 162's stated
fix, a gap in the channel slab, would therefore leave the carriageway over 36
percent of the grate at up to 19.90 mm. Queue 162 is amended by this record.

WHAT IT MEANS FOR ITEM 2. Jafar's item 2 is recorded with its middle elided
and no session may fill the ellipsis in; what survives verbatim is the grate
and a clip to his phone. Against that, the state is: as specified, no frame
can show this grate and no capsule can stand on it, because its top is buried
from 9.90 to 19.90 mm along its whole width with no part of it reaching the
surface. Also true and separately important: the gully dish under it has its
top at -0.105, which is inside the channel slab as well, so the whole gully
assembly is embedded in solid boxes. There is no CSG here.

THE FIX IS NOT A GAP IN THE SLABS. Cutting the 42 m channel and carriageway
at each gully turns two rows into four or six, moves the 593-piece count, the
bill of materials, the golden rows and the cross-engine guard, and buys a
recess nobody can see into at 1280 by 720 from a walking camera. The cheap
and honest fix is ONE ROW: the grate rises to the surface AND takes the
channel's own cross-fall, because a flat grate raised to be flush at its
centre line stands 5.0 mm proud at one edge and sits 5.0 mm low at the other,
and a 5 mm lip across a carriageway is a trip hazard that reads wrong before
anyone can say why. The measured target, arithmetic and not a placed reading:
`y_m` from -0.0925 to -0.0776, `pitch_deg` from 0 to 1.432096, which puts the
grate's top face on the road plane across its whole footprint. That row lands
under the art line's own review per queue 162's acceptance, with the before
and after burial reading printed beside it, and the dish stays where it is
tonight because deleting a row moves the piece count.

AND THE BURIAL IS CONFIRMED AT SPEC LEVEL ONLY. The walk build has never
placed one prop mesh (propsAsMesh=0/23), so no placed-bounds reading of this
grate exists anywhere in the repository. Queue 162's acceptance asks for one
and is not yet met.

## 4. The new burial instrument and its two admitted limits

FIT TO SHIP, WITH THREE CHANGES, AND THE MILLIMETRES STAY. The reasoning is
not that 85.00 mm is nearly right. It is that `propBurialStat` already carries
its limit in its own printed value, where the reader meets the number, which
is precisely what the person guard does not do; that `propFootprintGrid`
announces its own resolution and says a narrower gap is invisible; and that
`DeepestMm` is the tie-break in `WorseBurial`, so withholding it would silently
change which of twenty-three props is reported as worst. A number that
declares its own ceiling is an instrument. A number that declares it in a
comment is a trap.

85.00 mm IS EXACTLY WHAT THE CODE SHOULD PRINT, and I checked why rather than
accepting it: the carriageway's AABB top is y 0.000004, the road crown datum,
and 0.000004 minus -0.085 is 85.00 mm. So the value is not noise, it is the
crown height, and the grate's real cover at that cell is 16.37 to 19.90 mm.

THE STATED LIMIT UNDERSTATES ITSELF BY A FACTOR OF TWO. VignetteSpec.h 845
says the overstatement is "34 mm" for the carriageway. The measured
overstatement at this prop is 85.00 minus 14.90, which is 70.10 mm, and it
decomposes exactly: 34.32 mm from the slab's half-width cross-fall plus 35.78
mm from the cell's distance beyond the slab's centre line. The two ADD when
the prop sits at the far edge, and this prop sits past it. A reader who
subtracts the comment's 34 from 85 concludes the cover is 51 mm and is wrong
by 3.4 times. The printed value's own wording, "across its own width", is
right; the comment's arithmetic is half. Correct the comment, not the key.

THE LIMIT THAT MATTERS MOST IS NOT IN EITHER LIST: THIS INSTRUMENT CANNOT
ACCEPT ITS OWN FIX. With the grate raised and pitched as section 3 rules, its
AABB top becomes -0.065104, above the channel's AABB top, so the channel
stops counting as cover and `propFullyBuried` correctly falls from 1 to 0.
But the carriageway's AABB top is still 0.000004 over 36 percent of the
footprint, so the same subject would then print about 36pct at 65.11 mm and a
reader would call a perfect fix a half fix. So: the acceptance of the grate
row change MAY NOT be read off `propBurialWorst`. It is read off a
pitch-aware local cover top, which is pure arithmetic the container can run
because the file carries every pitch, or off queue 163's downward sweep, which
is ground truth and needs a run. Order: the arithmetic first, because it costs
no runner; the sweep second, as the independent confirmation.

THE 3.6 MM STRIP AND THE 85 MM HAVE ONE CAUSE. The strip is the grate's east
sliver beyond the channel slab's unpitched edge, 3.659 mm, which is 0.91
percent of 399.9 mm and reads as the builder's 0.9 percent. Take the slab's
pitch into account and its AABB reaches z 3.000001 and covers the sliver
entirely. AABB against pitched solid is the same conflation in both admitted
limits, which is why one change answers both.

propAnyBuried=10/23 IS THE LINE NOBODY HAS READ. The cap is honest: it shows
three and announces seven held. A header comment accounts for five of them as
AABBs touching at 0.00 mm, and a comment is an analysis, not evidence. Ten
props with something over them, three named, is the state where a build has
measured something and no human has looked, and a bound, if one is ever
wanted, is read off a series nobody has printed. A8 prints it.

## 5. The two sides that disagree by decision

NOT RECONCILED, AND THEY SHOULD NOT BE. The divergence is written at the rule
(VignetteSpec.h 744 to 751) and at the call site (VignetteShot.cpp 488 to
493), both read this session, and the reasoning holds on inspection:
`import_prop_meshes.py` reads a SAVED asset in an editor, where an absent body
setup is a finished fact about a file on disk, and NO is the right word;
`PropCollisionOf` reads an asset LOADED AT RUNTIME in a cooked build, where a
null body setup is also what a reader gets when nothing has built one yet, and
UNKNOWN is the only word that does not assert what nothing answered. Two
populations at two times. A single word across both would have to be the
weaker one, and that is how `propCollisionPrims=0/15` came to report fifteen
refusals as fifteen absences.

ONE THING IS MISSING AND IT IS ONE STRING. The street-side value already names
its population and its proxy status. It does not say that the same case reads
NO on the other side, so a reader holding both files sees UNKNOWN here and NO
there and cannot tell a ruled divergence from a contradiction. A9 puts the
divergence on the line where the numbers meet. Standing rule from this record:
the two tallies are never added, never differenced, and never printed as a
pair without their populations beside them.

## 6. The three things I was asked to check in passing

THE RENUMBERING IS SOUND. 157 to 165 exist, one file each, no gaps and no
duplicates, and the names say what they are. 165 correctly records that the
hand-run clause numbers are evidence for the person who ran them and for
nobody afterwards.

THE CANON CORRECTION IS RIGHT AND INCOMPLETE. Quay Street in the Hook is
canon, ruled by Jafar on 2026-09-08, and spec line 14 now agrees with it. But
the correction fixed the site and not the sentence. Lines 116 to 119 still
read that Quay Street is "the same word the pub-regular-v1 bank already uses
for the district (lines pr-030 and pr-044)". I opened both rows: pr-030 says
"the Parade freehold" and pr-044 says "the Exchange". NEITHER CONTAINS THE
WORDS QUAY STREET. The sentence was true of the word that was corrected away
and is now a false citation in a document tonight's commit carries, and the
clause beside it, "no street name below district level is minted by this
bank", is incoherent once the location IS a street name. This is rule 1's own
instruction: when a claim turns out false, grep for the sentence and not the
site.

THE flatsLit CLAIM IS REFUTED BY ITS OWN FILE. The space inside the value is
real: both engines emit the identical `flatsLit=0/0 nothing-to-light`
(VignetteSpec.h 631, StreetVignetteHost.cs 152), deliberately, so that a zero
arrives with its denominator and its reason. But vignette-spec-test.cpp 313 is
a `Check`, which ASSERTS the spaced form and pins it in place; and the
token walk that would catch it (lines 291 to 307) runs over the SHOT line
only, never over the scene line. So the selftest does not print this rather
than asserting it: it asserts it, and a later fix would fail the test. No tool
parses the key, so the eventual repair is two emits and one assert moving to
`flatsLit=0/0/nothing-to-light`, which is this project's own structure
convention. That is a two-engine change and not tonight's.

## 7. What I could not answer from the repository

- The 18.7 mm end of the carriageway range. My plane gives 19.90 mm at the
  footprint edge. Settled by A8's series, not by prose.
- Whether the placed grate matches its spec row. No run has placed a prop
  mesh, so the burial is a spec reading only.
- The elided middle of Jafar's item 2. The transcript holds the summary and
  not the message; it stays elided and this ruling does not fill it.
- Tone, as against register. The D7 judge waits on Jafar's calibration
  sample, so section 1 rules register and leaves tone pending, as the spec's
  acceptance step 3 already does.
- Whether the town has ever said these words in a build. The newest crime run
  predates the clauses, so `bankSummaryClause` will read nothing-measured
  until the next crime run. Built is not running.
- Both budget meters. Not read this session; I order one dispatch because the
  brief states one, not because I priced it.

## 8. The quality ladder at close

Best available, or first working? On the bank: first working, and the next
rung is named, which is a writer's pass over the four weak clauses with the
shared-cadence fault in the brief. On the person question: the printout of
twelve spliced rows for a human to read IS the best available, because no
mechanical check in this pipeline can see person, and the rung above it is a
judge with a calibration sample that does not exist yet. On the burial: the
AABB reading is first working and the pitch-aware local cover is the named
next rung, with the sweep above that. None of the three aspects has a blank
next rung, so none of them is a research task tonight.

## 9. The amendments

BLOCKING THE COMMIT. A1 to A4 are dictated text and one re-measurement and A5
is a document edit; the RESIDENT applies all five, which is what the split
permits, and none of them asks a builder for a new line of prose.

A1. `cw-ws-r2-01`, clause only, cut to exactly one mark. New value:
    `the one that did the window on Quay Street had a donkey jacket on`
    Pure subtraction, no new words. The spoken sentence on that row keeps its
    own defect and is filed by A12, because the sentence and the clause are a
    pair and only one of them propagates.

A2. `cw-ws-r4-02`, clause only, referent repaired. New value:
    `the new owner that's got Mickey's now, Novak, put the window in, and he's in the shop he did it to often enough to be known blindfold`
    Chosen to add no token r4-01 already carries, because "on Quay Street"
    twice in one cell would push a pair toward the 0.60 bound.

A3. The three rung-2 `overheard` TEXTS are permuted so that index k answers
    summary k, ids staying in numeric order: `cw-ov-r2-01` takes the donkey
    jacket reply, `cw-ov-r2-02` the limp and cap reply, `cw-ov-r2-03` the pale
    mac reply. No word changes and the multiset of lines is identical, so no
    repetition bound moves. Nothing outside the bank and the spec's bundle
    list names a rung-2 id, checked this session.

A4. After A1 to A3, re-run the tool's own scorer over the twelve clauses and
    print the worst pair and its value in the commit message. A shorter string
    can move a normalised ratio in either direction, so this is a measurement
    and not a formality. IF ANYTHING REACHES 0.60 IT COMES BACK TO ME. The
    bound does not move.

A5. Spec, `production/specs/dialogue-crime-witness-v1.md`: the reviewer list
    at lines 210 to 219 is rewritten as INDEX PAIRS, summary k beside reply k,
    because the bundle shape is what let the pairing fault pass a human
    reading. In the same pass, rung 2 gains the distinction this cell turns
    on: an OCCLUDING garment, a cap pulled down or a collar up, is permitted
    and explains the ceiling; an IDENTIFYING mark is permitted exactly once.
    That is what makes `cw-ws-r2-02` correct rather than tolerated. And the
    false citation at lines 116 to 119 is struck: Quay Street is named because
    CANON names it, and pub-regular-v1 is not a precedent for it.

BLOCKING THE DISPATCH, not the commit. A BUILDER applies these; all four are
in the tested layer, so the container proves them before anything reaches the
runner.

A6. `crime-probe-test.cpp`: the twelve-row printout prints the PAIRED REPLY at
    the same index beside each summary. At seeds 15, 29 and 43 the indices are
    0, 2 and 1, so all three variants are visited and tonight's worst fault
    would have been unmissable on one screen. This is the instrument that
    catches the class, not just the instance.

A7. `memoriesInFirstPerson` gains its limit in its own value, in the printed
    line and not in a comment: a word-boundary sniff over the text after the
    first " that ", which catches "me" and "I've" and cannot tell whether a
    third-person clause names the right third person. And its denominator
    becomes the count of memories actually sniffed, with the words nothing
    measured for a row that filed none.

A8. The burial series is PRINTED, in two parts: every buried prop rather than
    the worst three, and the per-cell depth series across the subject's
    footprint with each cell's z. The first is the line nobody has read on ten
    of twenty-three props. The second settles 18.7 against 19.90 by evidence
    and is what any future bound would be read off.

A9. VignetteSpec.h 845 to 846: the overstatement is corrected from 34 mm to
    the full-width figure, 68.6 mm for the carriageway and 6.4 mm for the
    channel, with the measured decomposition at this prop, 34.32 plus 35.78
    equals 70.10 mm, written beside it. In the same pass the collision stat
    value names the ruled divergence: a missing body setup reads UNKNOWN here
    and NO in the importer, by the ruling of 2026-09-08.

QUEUE ITEMS, blocking nothing, each armed with a name so that rule 8 is
satisfied by a file and not by an intention. The RESIDENT files them.

A10. Queue 166: `flatsLit` carries a space inside a value in both engines, the
     selftest asserts the spaced form, and the token walk does not cover the
     scene line. Fix is both emits plus the assert, in one commit, so the two
     engines stay comparable.

A11. Queue 167: the bank is not conditioned on light or clock, and at the
     probe's own seed the rung-1 pick names a streetlight while the run stages
     overcast noon with lanterns off.

A12. Queue 168: a writer's pass over `cw-ws-r1-03`, `cw-ws-r3-01`,
     `cw-ws-r3-03` and `cw-ws-r4-03`, with the shared closing cadence as the
     brief, and over the committed sentence of `cw-ws-r4-02`, which has a
     shopkeeper serving bitter.

A13. Queue 162 is amended in place by section 3: the magnitude is 9.90 to
     19.90 mm across the footprint and 14.90 mm at the centre line, the
     channel is not the deepest cover, the carriageway covers 36 percent, the
     slabs overlap with no gap, and the fix is one row rising and taking the
     cross-fall rather than a gap in a slab. Its acceptance still needs a
     placed-bounds reading, which nothing has ever produced.

## 10. The dispatch

THE ONE REMAINING DISPATCH IS THE BUILDER SPAWN CARRYING A6 TO A9, and it
does not need the runner. If the night's dispatch is instead the PC walk run,
it must carry the grate row of section 3, because a walk clip of a grate
buried 9.90 to 19.90 mm under asphalt cannot be Jafar's item 2 and must not be
reported as it. A walk run without that row is a measurement run, and the
honest thing to send with it is the number, not the picture.

<!--RULING spawn=2026-09-09T00:00:45Z-->
