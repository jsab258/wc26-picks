# SPEC: dialogue bank, pub-regular archetype, v1 (pilot of the assembly line)

Line: dialogue bank (ledger-v2/studio-v2/pipelines.md). Station 1 of 5.
Date: 2026-08-31. This is the Phase 0 pilot: its purpose is to prove the five
stations run end to end and to produce the judge calibration sample.

## What
48 memory-conditioned lines for the pub_regular archetype: the men and women
who hold down the same stool at Mickey's most nights. English of a British
port town, 1988 to 1992.

## Structure
9 cells: three ladder rungs by three contexts, 5 or 6 variant lines each.
- Rungs (canon, the naming ladder): stranger (knows the pub changed hands,
  not the face), novak (the player is a fact on this street), tom (they
  decided about the player and it was fine).
- The toma rung is EXCLUDED BY SPEC: canon grants it to two or three named
  people ever, so an archetype bank may not contain it. This exclusion is a
  canon fact wearing a spec's clothes; do not add the rung back.
- Contexts: greeting (player walks in), deed_reaction (gossip about a player
  deed has reached the speaker), gossip_pass (the speaker passes a rumour).

## Constraints (the writer's role file carries the standing ones)
- A line KNOWS its rung. A stranger line never contains Novak, Tom or Toma.
  A novak line never contains Tom or Toma as address. Mechanically checked.
- No real brands. Beer is mild, bitter, stout, never a marque. The football
  club, paper, radio station are not yet named: refer to them obliquely
  (the match, the local rag, the pirate station) until the brand bible mints
  names.
- Register per D3. At most two postcard-smut lines in the whole bank.

## Acceptance (station 3)
1. canon-gate.py clean over the bank file.
2. Rung discipline: zero address violations (tools/dialogue-verify.py).
3. Repetition: no two lines with token overlap at or above 0.6 after
   stopword strip (same tool). The bark corpus taught that repetition is
   the tell a player notices first.
4. Tone: NOT CHECKED at this station. The D7 judge needs Jafar's
   calibration sample, which this bank IS. Recorded as pending, not passed.

## Integration contract (station 4)
content/dialogue/pub-regular-v1.json at the repo root: the engine-neutral
source of truth (D1 keeps the engine open; generators emit engine content
later). Schema: bank, archetype, license tag, rungs, lines[] each with id,
rung, context, text. Untagged license fails the license gate.
