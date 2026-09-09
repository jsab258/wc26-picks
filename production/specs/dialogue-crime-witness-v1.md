# SPEC: dialogue bank, crime witness and overheard consequence, v1

Line: dialogue bank (ledger-v2/studio-v2/pipelines.md). Station 1 of 5.
Date: 2026-09-08. Ruled by
game-design/decision-2026-09-08-the-crime-the-witness-and-the-overheard-consequence.md,
section 3 (amendment A5): "the line and the witness's own telling both
come from a bank." That ruling is binding and is not restated here in
full; this document operationalises it into a bank a writer can maintain
and a reviewer can check without reading the C++.

## What
24 memory-conditioned lines for the first crime-and-witness vignette in
the packaged Unreal build: a half-brick through a shop window on Quay
Street, witnessed by an archetype called w1 (the shopkeeper) at one of
four identification rungs the perception code assigns from real geometry,
later told to a second archetype called n2 (the lad in the yard) who
replies. These two lines are the first consequence in LEDGER a player can
overhear. English of a British port town, 1988 to 1992.

## Structure
Two contexts, four identification rungs, three variants per cell, 24
lines in total.
- `witness_summary`: what w1 has of the crime at the rung she actually
  achieved, as TWO STRINGS, because the runtime needs two and one string
  cannot be both. Corrected 2026-09-08 (queue 157): this section used to
  say the text "is used twice at runtime" as though verbatim, and it is
  SPLICED in both of those roles.
  - `text` is what she SAYS: a finished first-person sentence, spoken
    whole. It is her half of the overheard exchange when composition
    refuses, and it is the row the verdict names as `bankSummaryText`.
  - `clause` is what the mill FILES as the `Rumor.Summary`: third
    person, lowercase first letter, no interior and no trailing full
    stop, because BOTH consumers splice it. `Gossip.h` 586 writes "I
    heard from " + name + " that " + summary into the heard memory, and
    `StreetVoice`'s templates drop it into the middle of a sentence
    ("You hear all sorts. {What}, apparently."). `StreetVoice.cs` 752 to
    771 states that contract.
  The incident, so no future reader merges them again: filing the
  sentence shipped "I heard from the shopkeeper that He looked straight
  at me before he ran." to `production/d1-probe/ue-crime-memory-n2.md`
  line 6, and composed "You hear all sorts. He looked straight at me
  before he ran. Couldn't tell you his name, but I've got his face now,
  apparently." The clause is WRITTEN, never derived from the sentence:
  lowercasing that sentence leaves the witness's own "me" inside
  somebody else's memory, which is a fault no shape check can see.
- `overheard`: n2's reply, spoken after hers when the two are together
  (`GossipDirector.cs`, `SayAfter` beats at `i * 2.1` seconds), at the
  SAME idRung as the summary it answers.

## The rung discipline, the reason this bank exists
`idRung` is the identification-ladder rung (1 to 4 here; canon's five-rung
ladder tops out at recognition, which is relationship-gated and excluded
until the cast baseline lands, OPEN 2) that the ported perception code
measured for w1 against this crime, from distance, angle, occlusion and
light. It is not a writer's choice: it is a ceiling on what the line may
honestly claim, and every line in this bank is written to sit exactly at
its ceiling, never above it.

- idRung 1, a shape. She saw a figure and nothing else: not sex, not
  build, not clothing, not a mark. A `witness_summary` line names a
  shape, a movement, a shadow against the light, and stops. The paired
  `overheard` reply may react to "just a shape" but may not supply a
  build, a garment or a sex the summary never gave it.
- idRung 2, a distinguishing mark. She has exactly one concrete,
  repeatable detail: a garment, a gait, a cap, on a figure she can now
  call "him". A `witness_summary` line names one such mark and no more.
  The paired `overheard` reply may repeat or deflate that one mark
  (most men on that street could match it); it may not add a second
  mark, a face, or claim the mark identifies anyone.
- idRung 3, a face she would know again. She saw him clearly enough to
  pick him out on sight and says so; she still has no name, no job, no
  address for him. The paired `overheard` reply may treat "a face she'd
  know" as valuable information worth keeping; it may not supply a name
  or a role.
- idRung 4, the person named. She knows exactly who he is: the new owner
  up at Mickey's. Because this is also the point at which he is a fact
  of the street rather than a stranger, the address rung for these lines
  is `novak`, and the line may use the name Novak the way canon's naming
  ladder allows at that rung (the new owner, then Novak, then Tom, then
  Toma; he has not earned Tom or Toma from one witnessed crime). The
  paired `overheard` reply may use the same name and react to the fact
  that it is now known.

THE RULE THAT MAY NEVER BE BROKEN: a reply may not claim more than its
paired summary carried. A rung-1 reply that could be mistaken for a
rung-3 reply, because it names a build or a face the summary never gave,
is wrong no matter how well it reads. No mechanical tool in this pipeline
checks this discipline; it is verified by a human reading the four
sentences above against the twelve pairs, which is why they are written
out here rather than left implicit in the JSON.

## Two different numbers on every line, not one
- `rung` is the ADDRESS rung `tools/dialogue-verify.py` checks
  mechanically: whether a line may contain the words Novak, Tom or Toma.
  idRung 1 to 3 carry `rung: "stranger"` (none of the three names).
  idRung 4 carries `rung: "novak"` (Novak allowed, Tom and Toma still
  refused). `tom` is never used as a rung in this bank: neither
  archetype has earned that standing from a single witnessed crime.
- `idRung` is the IDENTIFICATION rung the perception code measured. The
  runtime uses it to select a variant and to pair a `witness_summary`
  with an `overheard` reply at the same idRung.
These two happen to point the same way at idRung 4 only because that is
where canon's naming ladder and the identification ladder meet (a face
recognised well enough to be named); they answer different questions and
a future change to one must not silently assume it moves the other.

## Speakers, not cast
`w1` displays as "the shopkeeper" and `n2` as "the lad in the yard".
These are archetypes fixed by the crime probe's geometry (a doorstep on
Quay Street; a yard behind the west crossover), not named characters.
Canon's cast baseline is OPEN 2 and a probe does not mint cast: do not
rename either archetype to a day-life-ring name (Sam, Ada, June, and so
on) without a canon ruling naming them explicitly for this vignette.

## Location
One window, on Quay Street, BECAUSE CANON NAMES IT: canon.md lines 13, 15 and
24, ruled 2026-09-08 option C, the built street is Quay Street and it is in the
Hook. The earlier version of this section cited pub-regular-v1 as though a
sibling bank were the authority. It is not, and the citation is struck: canon
outranks every document, and a bank agreeing with canon is agreement, not
evidence. No street name below district level is minted by this bank.

## Selection
Deterministic from `seed = Day * 31 + Hour` (`GossipDirector.cs` line
586, the existing call site this bank's pick replaces at the picking
step, `StreetVoice.Exchange` remaining out of scope as composition). This
bank supplies three variants per cell; naming the exact mapping from seed
to index is the runtime's job, not this document's.

## Constraints (the writer's role file carries the standing ones)
- No line contains the word "player". The ported gossip guard counts
  `summariesSayingPlayer` and the crime run must print zero.
- No em-dashes, no italics, no exclamation marks doing a verb's work.
- No real brands, no era violations: mechanically checked by
  `tools/canon-gate.py`.
- Register per D3: dry British wit, tabloid and Viz-adjacent flavour, the
  noir holds even in the joke. Seaside-postcard smut is permitted
  sparingly elsewhere in the game; none is used here, because a
  shopkeeper reporting a smashed window to a witness is not that moment,
  and forcing one in would read as the AI-slop tic this project refuses.
- The `toma` rung is EXCLUDED: canon grants it to two or three named
  people ever, and neither archetype here has earned it from one
  vignette. This exclusion is a canon fact wearing a spec's clothes; it
  is not this bank's to grant.

## Acceptance (station 3)
1. `tools/canon-gate.py` clean over the bank file: zero era or brand
   findings, denominator printed.
2. `tools/dialogue-verify.py` clean over the bank file: zero rung
   violations, worst repetition overlap printed and under the 0.6 bound,
   license tag present.
3. Tone: NOT CHECKED at this station. The D7 judge rules on tone after
   Jafar's calibration sample; recorded here as pending, not passed.
4. The rung-discipline check above the tool's reach (a reply must not
   outrun its summary) is verified by a human reader against the four
   one-sentence ceilings in this spec; no tool in this pipeline reads
   meaning, so this acceptance step is a reading, not a run.
5. `tools/dialogue-verify.py` READS `text` AND NOT `clause` (it scores
   `ln["text"]` only), so its clean result has a denominator of 24
   texts and zero clauses. Measured by hand with the tool's own scorer
   on 2026-09-08, and reported rather than assumed: 0 rung-name
   findings over 12 clauses examined, 0 of 66 clause pairs at or over
   the 0.60 repetition bound (worst 0.32, cw-ws-r3-01 against
   cw-ws-r3-03), 12 of 12 lowercase-initial, 0 of 12 carrying an
   interior or trailing full stop, 0 of 12 containing the word
   "player". Teaching the tool to score the clause field is queue work,
   not this spec's.
6. The twelve clauses spliced into BOTH runtime frames are printed by
   `ue-probe/tests/crime-probe-test.cpp` for a reader to judge person
   agreement, because no mechanical check in this pipeline can see
   person. The printout is the artifact for that step, not the count.

## Integration contract (station 4)
`content/dialogue/crime-witness-v1.json` at the repo root, found at
runtime the same way `vignette-pieces.json` is (`VignetteShot.cpp` 320 to
324, the same four candidate paths). Schema: `bank`, `license`, `era`,
`register`, `rungs`, `contexts`, `idRungs`, `speakers` (archetype id to
display label), `location`, and `lines[]`, each with `id`, `context`,
`idRung`, `rung`, `speaker`, `text`, plus `clause` on every
`witness_summary` row and on no `overheard` row: an overheard reply is
spoken whole and is never filed as anybody's summary, so there is
nothing for a splice to get wrong. A `witness_summary` row with no
`clause` REFUSES by name (`LedgerCrime::SummaryToFile` files the
bank-unreadable sentinel carrying the row id, and the composer already
refuses on that prefix) and never falls back to the sentence, because
falling back to the sentence is the defect. An untagged license fails
the license gate, same as every other bank.

## What a future reader must not change without a ruling
- The idRung-to-address-rung mapping: 1 to 3 are `stranger`, 4 is
  `novak`, `tom` never appears.
- The two archetypes and their display labels; no cast name is minted
  here.
- The location word, "Quay Street", and the one-window premise.
- The absence of the word "player" and of any `toma` line.
- The discipline that a reply may never claim more than its paired
  summary. Adding detail to make a low-idRung reply feel richer is a
  regression, not an improvement, and the D7 judge should read it as one.

## What is deliberately NOT here, and why
- No voice clips. `VoiceBank` hashes speaker and text to a filename and
  is filed as future work in the ruling (section 8: "a crowd voice for
  the two lines by VoiceBank hash"); this bank only supplies the text
  that hash will eventually cover.
- No composition. `StreetVoice.Exchange`, which composes a reply from
  live world state, is the rung above a bank pick on the quality ladder
  named in the ruling; this bank is the pick, not the composer.
- No cast. Canon's cast baseline is OPEN 2, and the cast-sketch-versus-
  built-cards mismatch is unresolved; `w1` and `n2` are placements the
  crime probe made from geometry, not people the day-life ring has met.

## The 24 lines, AS INDEX PAIRS, for a reviewer checking the discipline without opening the JSON

LISTED AS PAIRS AND NOT AS TWO BUNDLES, ruled 2026-09-09, because the bundle
shape is what let a pairing fault pass a human reading: at rung 2 the reply at
index k answered the summary at a different index, and three lines listed in two
groups of three read as correct while three lines listed as pairs do not. THE
PICK IS BY INDEX. Variant k of `overheard` answers variant k of
`witness_summary`, at the same rung, and a reviewer who cannot read the pair on
one line cannot check that.

    rung 1, a shape only
      01  cw-ws-r1-01  <->  cw-ov-r1-01
      02  cw-ws-r1-02  <->  cw-ov-r1-02
      03  cw-ws-r1-03  <->  cw-ov-r1-03
    rung 2, one mark on a "him"
      01  cw-ws-r2-01  <->  cw-ov-r2-01
      02  cw-ws-r2-02  <->  cw-ov-r2-02
      03  cw-ws-r2-03  <->  cw-ov-r2-03
    rung 3, a face she would know again, no name
      01  cw-ws-r3-01  <->  cw-ov-r3-01
      02  cw-ws-r3-02  <->  cw-ov-r3-02
      03  cw-ws-r3-03  <->  cw-ov-r3-03
    rung 4, Novak, the new owner up at Mickey's, named
      01  cw-ws-r4-01  <->  cw-ov-r4-01
      02  cw-ws-r4-02  <->  cw-ov-r4-02
      03  cw-ws-r4-03  <->  cw-ov-r4-03

RUNG 2 TURNS ON A DISTINCTION THIS SPEC DID NOT STATE, added in the same pass.
An OCCLUDING garment, a cap pulled down or a collar up, is permitted freely and
is part of why the rung tops out where it does: it is the reason she cannot say
more. An IDENTIFYING mark, a limp, a jacket, a build, is permitted EXACTLY ONCE.
That is what makes cw-ws-r2-02 correct rather than tolerated, its cap being
occlusion and its limp being the one mark, and it is what made cw-ws-r2-01's
clause wrong at two marks before it was cut.
