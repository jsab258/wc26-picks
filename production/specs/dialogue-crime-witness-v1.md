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
the packaged Unreal build: a half-brick through a shop window on the
Parade, witnessed by an archetype called w1 (the shopkeeper) at one of
four identification rungs the perception code assigns from real geometry,
later told to a second archetype called n2 (the lad in the yard) who
replies. These two lines are the first consequence in LEDGER a player can
overhear. English of a British port town, 1988 to 1992.

## Structure
Two contexts, four identification rungs, three variants per cell, 24
lines in total.
- `witness_summary`: what w1 files as her memory of the crime, in her own
  words, at the rung she actually achieved. This exact text is used twice
  at runtime: as the "heard" memory line (`Gossip.cs` 394) and as her half
  of the overheard exchange, so it has to read naturally both as a private
  record and as a thing said aloud to someone standing next to her.
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
the Parade; a yard behind the west crossover), not named characters.
Canon's cast baseline is OPEN 2 and a probe does not mint cast: do not
rename either archetype to a day-life-ring name (Sam, Ada, June, and so
on) without a canon ruling naming them explicitly for this vignette.

## Location
One window, on the Parade: the ruling's own phrase for it, and the same
word the pub-regular-v1 bank already uses for the district
(`content/dialogue/pub-regular-v1.json`, lines pr-030 and pr-044). No
street name below district level is minted by this bank.

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

## Integration contract (station 4)
`content/dialogue/crime-witness-v1.json` at the repo root, found at
runtime the same way `vignette-pieces.json` is (`VignetteShot.cpp` 320 to
324, the same four candidate paths). Schema: `bank`, `license`, `era`,
`register`, `rungs`, `contexts`, `idRungs`, `speakers` (archetype id to
display label), `location`, and `lines[]`, each with `id`, `context`,
`idRung`, `rung`, `speaker`, `text`. An untagged license fails the
license gate, same as every other bank.

## What a future reader must not change without a ruling
- The idRung-to-address-rung mapping: 1 to 3 are `stranger`, 4 is
  `novak`, `tom` never appears.
- The two archetypes and their display labels; no cast name is minted
  here.
- The location word, "the Parade", and the one-window premise.
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

## The 24 lines, for a reviewer who wants to check the discipline without opening the JSON
witness_summary: cw-ws-r1-01, cw-ws-r1-02, cw-ws-r1-03 (a shape only);
cw-ws-r2-01, cw-ws-r2-02, cw-ws-r2-03 (one mark, on a "him"); cw-ws-r3-01,
cw-ws-r3-02, cw-ws-r3-03 (a face she would know again, no name); cw-ws-r4-01,
cw-ws-r4-02, cw-ws-r4-03 (Novak, the new owner up at Mickey's, named).
overheard: cw-ov-r1-01, cw-ov-r1-02, cw-ov-r1-03 (reacts to a shape only);
cw-ov-r2-01, cw-ov-r2-02, cw-ov-r2-03 (repeats or deflates the one mark);
cw-ov-r3-01, cw-ov-r3-02, cw-ov-r3-03 (values a face she'd know, adds no
name); cw-ov-r4-01, cw-ov-r4-02, cw-ov-r4-03 (uses Novak's name, reacts to
the consequence of it being known).
