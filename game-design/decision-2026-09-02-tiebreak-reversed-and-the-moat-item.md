# DIRECTOR RULING: ties go to Unreal and that moves D1's weight from (b) to (a); the blind look and the preference coexist by ORDER; D12 and D11 do not displace 027, they expose that the queue had no moat item (2 Sep 2026, evening)

> **STATUS: LOG, 2026-09-02. NOT CURRENT once the dictated edits T1 to T8, M1 to M4, Q1 to Q5 and B1 are applied; from then the D1 register, the queue, production/NOW.md and the next brief are the reading copies and this file is their history.**

This document carries exactly one em-dash, in the banner, because
`tools/docs-check.py` line 55 accepts no other form.

Tenth ruling since 1 September. No shell: every number below was read from a
file this session and the file and line are named beside it. Nothing was
taken from a builder's or the resident's report. This spawn costs roughly 2
of today's points and today is already over its 10 (budget.md line 157), so
the ruling is text, every edit is free to apply, and NOTHING SPAWNS TODAY.

## What was verified

- My row: `.claude/agent-log.tsv` line 203, `2026-09-02T14:56:47Z
  studio-director`, the newest in the file. `.git/logs/HEAD` line 360: the
  newest commit is `edf8c66e` at epoch 1788360616, which is 14:50:16Z; my
  row is newer than every commit in the reflog.
- `ledger-v2/respec/decision-register/D1-engine-probe.md` in full (10
  lines): line 6 and line 10 both say ties go to Unity. `D12` and `D11` in
  full. `game-design/decision-D1b-rescope.md` lines 84 to 92 (the definition
  of decisively better) and 96. `decisions-pending.md` lines 14 to 48 (the
  card, Jafar's words at 38). The timebox ruling in full; the rotation
  ruling in full (its Ruling 5 sets the applied/deferred rule this record
  follows).
- Every live copy of the tie sentence, by grep outside `legacy/`, opened at
  the hit: `production/d1-probe/plan.md` 5 and 32 to 34; `measurements.md`
  175 to 176; `instrument-inventory.md` 78 to 79; `evidence-channel-spec.md`
  70 to 73. `NOW.md` already says Unreal (line 36).
- `production/queue/`: all 27 status lines; 027, 028, 032, 035 in full;
  036 in full; `README.md`. No item names D12, D11, the Ledger or the
  information layer. `roadmap-v2.md` in full (17 lines; row 2 lists
  "what-they-know HUD"). `reference-extraction.md` lines 1 to 20 (item 1 is
  that HUD). `vision-pillars-v2.md` in full: no HUD, no Ledger; pillar 1 is
  the moat and it is engine-neutral. `scope-v2.md` grep: venues only.
- `ledger/Assets/Scripts/Core/PlayerKnowledge.cs` in full (83 lines):
  `KnownLead` carries holder, topic, summary, source, confidence when
  learned, learned-at, sensitive, handled; the class comment says the
  player sees what they BELIEVE, never ground truth. `Gossip.cs` line 43:
  `Hops`, 0 for witnessed first-hand, is the only provenance a `Fact`
  carries. `Claims.cs` 1 to 45, `Reliability.cs` 1 to 45. Call sites:
  `GameController.cs` 92 and 180 to 183 ("the only window the player ever
  gets into the rumor network"), `DialogueUI.cs` 1052, 2173, 2183, 2194,
  `SimDirector.cs` 13813; `CoreTests/Program.cs` 21 mentions.
- `production/budget.md` in full: lines 156 to 157 (10 points a day, today
  ran at roughly 40), 161 (a spawn costs 1.5 to 2), 165 to 176 (the three
  part rule). `quality-ladder.md` in full (line 34: median 10 min over 9
  rows before cook or capture; 20 minutes is run 16's estimate WITH them,
  per the timebox ruling's Ruling 5, and is not a measurement).
- `production/briefs/` grep for pros, cons, Unreal, tie-break: nothing. The
  pros and cons he asked for have not been sent.

## Ruling 1: the rule after the reversal. Unreal wins on equal; "decisively better" survives as a definition and changes sides

The two readings the brief names are one rule seen from two ends, and the
D1b definition is what makes them one. D1b line 92 says anything short of
Unreal preferred in three of four pairs and worse in none IS a tie. So a
rule in which "decisively better" stayed Unreal's bar AND ties went to
Unreal would contradict itself: the tie is by definition the case where
that bar was not cleared. The only coherent rule is the mirror:

**Unity wins only if (b) is decisively better FOR UNITY, or (a) fails for
Unreal by non-convergence or hand-edit dependence. Otherwise Unreal wins,
on equal as on better.** "Decisively better" keeps its D1b definition
(preferred on the D8 decomposition in at least three of four pairs, worse
in none, both engines' frame times quoted for every pair) and is now the
bar Unity must clear.

Named consequence, so it is not discovered at close: Unity ahead in one or
two pairs with Unreal ahead in none is a tie under that definition and goes
to Unreal. That is what "ties go to Unreal" means when the definition is
kept rather than reinvented, and I will not invent a plurality rule to
soften it. The close-out names the case in words if it arises and puts the
per-pair sheet to Jafar, because he asked for the pros and cons WITH his
answer so that the decision stays revisitable on evidence (card, line 45).

What this does to the probe: the weight moves from (b) to (a). Before,
Unreal had to prove its frames; now it has to LAND four admissible pairs
through a loop that converges without a hand-made asset, and that is
winning unless Unity's frames are decisively preferred. Measurement (a) is
therefore the decisive measurement, its failure modes stand exactly as
ruled this morning (measurements.md 178 to 199), and its instrument is
queue 032's round-trip printer, which rides 027's first UE dispatch. The
protection on the decision now guards the other direction too: an
unmeasurable UE side closes UNRESOLVED and never becomes "Unreal wins" on
the strength of the preference.

## Ruling 2: the preference and the blind look coexist by ORDER, and here is the sentence

The sentence, for the person holding two images: **write A, B or EQUAL for
this pair on the D8 decomposition, and why, before any label is unmasked;
the tie-break is a rule applied to your written sheet afterwards by whoever
unmasks it, so a preference for Unreal can be in the rule and never in the
sheet.**

Three things make that real rather than declared. The sheet is written
first and committed before the map is opened. The map (which side is which
engine, per pair, from a seeded coin) is committed BEFORE the look, so the
assignment cannot be chosen after the verdict. And the instrument that
produces an unlabelled pair does not exist today: both engines commit
engine-named files. It is queue 038 (Q4), an instrument-builder session
that WAITS until UE Phase B lands a still, because a sheet tool with one
side blank measures nothing.

## Ruling 3: what D12 and D11 reorder. Not 027; the absence of a moat item

The premise check first. Pillar 1 (vision-pillars-v2.md line 15) is the
moat and it is engine-neutral Core; pillar 5 is what the engine serves.
Meridian Test conditions 2 and 3 are the moat; condition 1 is the engine.
Nothing in D12 or D11 contradicts the premise section; both sharpen it.
The premise stands.

The finding: the queue holds twenty-two ready items and not one is about
the information layer, on the day the owner ruled at premise level how the
moat is shown. That is the reorder D12 owes, and it is an ADDITION, not a
swap. 027 stays first: it is the owner's stated allocation, it is the only
item that moves the Phase 0 gate, and after Ruling 1 landing its pairs is
the decision. But the second builder slot of a day is not 027's, because
027 is bottlenecked by a round trip and not by builder hours, and that slot
had been going to governance. It now goes to the moat first.

What the moat item IS, read from the code and not guessed. D12's central
rule is already in Core: `PlayerKnowledge` is the only window the player
gets into the mill (GameController.cs 182), its entries carry source, time
and confidence when learned, and the class says never ground truth
(PlayerKnowledge.cs 18 to 19). It is wired (five Game call sites, 21 test
mentions), so this is a rescope, not a build from blank. What D12 and D11
add, each with the file that lacks it: per-entry provenance as witnessed,
heard with source and time, or deduced (Gossip.cs 43 carries only `Hops`;
`KnownLead` has `Source` and `LearnedAt` but no tag); per-EVENT entries
beside per-person; the conversation showing the page for the person in
front of you (DialogueUI holds a `KnownLead` at 1052, not a page); D11's
per-NPC remembered record of the player's claims read back as the REASON a
claim is believed or doubted (Claims.cs and `ProcessClaim` move suspicion;
whether the reason is surfaceable is the question); and the what-they-know
HUD scoped to law enforcement in wanted states, which today exists only as
a roadmap phrase (M1) and a reference-extraction line (M2).

Queue 037 (Q2) is one systems-builder session, engine-neutral C#, tested
locally, whose deliverable is a LIVE spec naming per clause the Core line
that carries it or MISSING, plus a call-site list of every Game-layer read
of NPC memory that reaches a player-facing surface, each marked allowed
(through `PlayerKnowledge`) or D12-violating, with counts. No code beyond
that: the guard's shape (a verify.py lint over Game files, in the family of
the existing raw-avenue-read lint) is named as the spec's next rung and is
built after the survey has printed, not before (rule 2).

Why now rather than after D1 closes: Phase 1 transliterates Core, guarded
by the test suite. A Core that already matches D12 is ported once; a Core
that does not is ported and then extended in C++ blind at one hypothesis
per round trip. Two points now, spent in the cheap loop, are the cheapest
those clauses will ever be.

## Ruling 4: the queue order, spendable at 10 points a day, and what WAITS

A day is two builder spawns, one director review of the batch, and the
resident's turns: roughly 2 + 2 + 2 + 3 (budget.md 161, 165 to 176). If a
day's readings say the resident ran heavy, slot 2 is dropped, never slot 1.

PROCEEDS, in this order:

1. **027**, slot 1 of every day until D1 closes or the six-dispatch review
   fires. Phase A now (engine-free, CoreTests, local); Phase B on the first
   UE dispatch, carrying 032's printer.
2. **037**, slot 2 of day 1. The moat item, Ruling 3.
3. **028 item 1**, slot 2 of day 2, while Phase B is in flight; items 2 to
   4 ride the same content-wrangler session.
4. **032's named change**, after its printer has printed a series over two
   or three dispatches. Not before: the cost that dominates is unknown
   until step one runs (032 line 31).
5. **038**, the blind pair sheet, when UE Phase B lands a still.

WAITS, and why:

- **035** (the lantern). The values live in the shared JSON, so both engines
  render the same flood and the pair stays fair; and the first UE night
  frame says whether the flood is the JSON or Unity's light-unit conversion,
  which is worth knowing before the printer is written.
- **020 to 026, 030, 033, 034, 036.** Governance and small fixes. Nothing of
  them spends a builder slot while a moat or admissibility item can fill a
  UE wait. 029 stays resident-only and free. 026 needs a director row and
  gets one only when a mandatory trigger spawns one anyway.
- **Everything visual on the ladder**, as already recorded there.

## Ruling 5: the pros and cons Jafar asked for, in his terms, for the next brief (B1)

**Unreal.** For: the higher ceiling out of the box (Lumen, Nanite,
MetaHuman, City Sample crowds and vehicles, all free) and the stronger
faces path, which is condition 1 of the Meridian Test. Against: the loop is
a blind C++ hypothesis per round trip (10 minutes median over 9 rows before
cook and capture, run 16 estimates 20 with them), every Core rung after the
port pays that loop for the life of the project against the weekly budget
he named as the real constraint, binary assets are where an agent's edits
fail, and nothing of Unreal has rendered yet.

**Unity.** For: it runs today (four matched stills, `datumMissing=0/845`,
nothing hand-placed, per NOW.md 14 to 19), the Core loop is local and the
instruments exist, so every point buys more verified rungs. Against: the
ceiling is ours to reach with our own work on GI, wet surfaces and faces
(CC4 path), and nothing comparable to the City Sample comes free.

**What the reversal buys and costs, plainly:** it moves the burden of proof.
Unreal now wins by landing, unless Unity's frames are decisively better;
the price is that a tie buys the slower loop on every rung from then on.
The one thing that would reopen it is the loop failing (a), which is
measured, not argued, and 032 is its instrument.

## Dictated edits. Each id is listed in the commit message as applied or deferred with a reason; the next director greps this list before ruling on anything new

**T1. `ledger-v2/respec/decision-register/D1-engine-probe.md`**, append after
line 10, one paragraph:

```
AMENDED 2026-09-02, second amendment of the day: THE TIE-BREAK IS REVERSED by Jafar ("UE - but tell me pros/cons of each", answering the card in game-design/decisions-pending.md; ruling game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md). The rule now reads: Unity wins only if (b) is decisively better for Unity, or (a) fails for Unreal by non-convergence or hand-edit dependence (production/d1-probe/measurements.md). Otherwise Unreal wins, on equal as on better. "Decisively better" keeps its D1b definition (preferred on the D8 decomposition in at least three of four pairs, worse in none, both frame times quoted per pair) and changes sides: it is the bar Unity must clear; Unity ahead in one or two pairs with Unreal ahead in none is a tie and goes to Unreal, named in words at close. The pairs are still judged blind: A, B or EQUAL written per pair before any label is unmasked, the tie-break applied to the sheet afterwards. (a) is unchanged and is now the decisive measurement. An unmeasurable UE side still closes UNRESOLVED and never becomes either engine's win by default.
```

**T2. `production/d1-probe/plan.md`** line 5, `taste. Ties go to Unity.`,
becomes `taste. Ties went to Unity until 2026-09-02 and go to Unreal since (register, second amendment of that date).`
Lines 32 to 34, from `in measurements.md, and never by a date. The decision rule is unchanged,` to `UNRESOLVED" still means an external blocker, not a slow loop.`, become:

```
in measurements.md, and never by a date. Later the same day Jafar REVERSED
the tie-break (register, second 2026-09-02 amendment): ties go to Unreal,
Unity wins only decisively, and "if the UE side cannot be measured, D1
closes UNRESOLVED" still means an external blocker, not a slow loop, and
never becomes either engine's win by default.
```

**T3. `production/d1-probe/measurements.md`** lines 175 to 176 become:

```
D1 gave ties to Unity until 2026-09-02 and gives them to Unreal since (the
register's second amendment of that date). A tie is a MEASURED tie either
way. If the UE side cannot be measured, D1 closes UNRESOLVED, never "Unity
wins" and, now that the preference points the other way, never "Unreal
wins" either.
```

**T4. `production/d1-probe/instrument-inventory.md`** lines 78 to 79, from
`already there, which is momentum` to `giving ties to Unity. The number that will`, become:

```
already there, which is momentum rather than an engine property. D1's rule
credited that momentum by giving ties to Unity until 2026-09-02; since then
ties go to Unreal and momentum is not credited. The number that will
```

**T5. `production/d1-probe/evidence-channel-spec.md`** lines 72 to 73 become:

```
become either engine's win by default: a tie is a MEASURED tie (to Unity
until 2026-09-02, to Unreal since). An unmeasurable UE side closes D1 UNRESOLVED.
```

**T6. `game-design/decision-D1b-rescope.md`**, insert after line 92
(`Anything short of that is a tie, and ties go to Unity.`), which stays:

```
REVERSED 2026-09-02 by Jafar: ties go to Unreal, and the definition above is now the bar UNITY must clear; the register's second 2026-09-02 amendment is the reading copy (game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md).
```

**T7. `game-design/decisions-pending.md`**, append after line 48:

```
Ruled: game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md, Ruling 1 (the rule as it now reads) and Ruling 5 (the pros and cons he asked for, carried in the next brief).
```

**T8. `production/queue/027-ue-vignette-emitter.md`** line 5, append to the
status line: ` Since the tie-break reversal (2026-09-02, same ruling as 037), landing its four admissible pairs through a converging loop is winning unless Unity is decisively better: (a) is the decisive measurement, and 032's round-trip printer rides this item's first UE dispatch.`

**M1. `ledger-v2/respec/roadmap-v2.md`** row 2, `what-they-know HUD;` becomes
`the Ledger (D12); what-they-know HUD only for law enforcement in wanted states;`. The row counts 53 words today and 63 after; the 80-word row law holds and `tools/docs-check.py` confirms it in verify.

**M2. `ledger-v2/respec/reference-extraction.md`** line 6 becomes:
`1. The what-they-know HUD over the seven slots and the identification ladder. SCOPED DOWN 2026-09-02 by D12-information-surfaces: law enforcement's institutional knowledge during wanted states only; the player-facing surface is the Ledger.`

**M3. `production/quality-ladder.md`**, append to the first table (after
line 34):

```
| Information layer (D12, Core) | PlayerKnowledge is the only window the player gets into the mill (GameController.cs line 182): per-holder, per-topic leads with source, time and confidence when learned, never ground truth; wired at five Game call sites, 21 CoreTests mentions. | Queue 037: per-entry provenance as witnessed / heard(source, time) / deduced (Gossip.cs carries only Hops); per-event entries beside per-person; the conversation page for the person in front of you; D11's per-NPC record read back as the reason a claim is believed or doubted. |
```

**M4. `ledger-v2/respec/decision-register/D12-information-surfaces.md`**,
append at the end:

```
## Queued 2026-09-02

Queue 037 (the Core rescope, a spec and a call-site survey, one session) by game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md, Ruling 3. The roadmap's Phase 2 row and reference-extraction item 1 were corrected in the same ruling to carry the scope-down.
```

**Q1. `production/NOW.md`** lines 34 to 62 (the section `## Two decisions
Jafar made on 2 September, and the work they owe`) become:

```
## Two decisions Jafar made on 2 September: RULED

Ruling: game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md.

THE TIE-BREAK GOES TO UNREAL and the rule now reads: Unity wins only if
its frames are decisively better (D1b's definition, three of four pairs
and worse in none, frame times quoted) or the Unreal loop fails (a) by
non-convergence or hand-edit dependence; otherwise Unreal, on equal as on
better. That moves the weight of D1 from (b) to (a): landing four
admissible Unreal pairs through a converging loop is winning, so 032's
round-trip printer is the decisive instrument and rides 027's first UE
dispatch. The pairs are still judged BLIND: the judge writes A, B or EQUAL
per pair on the D8 decomposition before any label is unmasked; the
tie-break is applied to that sheet afterwards by the unmasking, never
while looking. The unlabelled sheet is queue 038 and waits for a UE still.

D12 AND D11 DO NOT DISPLACE 027; they exposed that the queue held no item
for the moat at all. Queue 037 (the Ledger's Core rescope, one
systems-builder session, engine-neutral) is the FIRST UE-WAIT FILLER and
takes the second builder slot of a day ahead of every governance item.
PlayerKnowledge.cs is already the only window the player gets into the
mill (GameController.cs line 182); what D12 adds is named in 037.

THE ORDER, at 10 points a day (two builders and one director review):
slot 1 is always 027 (Phase A now, Phase B plus 032's printer on the
first UE dispatch); slot 2 is 037, then 028's figure, then 032's named
change once its printer has printed; 038 when UE Phase B lands a still;
035 waits behind that still; governance waits. Nothing spawns on 2
September after this ruling lands: the day ran at roughly 40 points
against 10 (budget.md condition 4).
```

And lines 79 to 83 (`## In flight`) become:

```
## In flight

- Nothing running. The evening ruling is landing as text.
- NEXT ACTION, tomorrow, after Jafar's usage number: spawn the
  engine-specialist for 027 Phase A plus 032's printer (one brief, facts
  inline per ledger-v2/studio-v2/brief-template.md), then the
  systems-builder for 037. Both diffs go to one director before commit.
```

**Q2. `production/queue/037-d12-ledger-core-rescope.md`**, new file:

```
line: production (the moat: information layer, Core)
spec: ledger-v2/respec/decision-register/D12-information-surfaces.md, D11-player-progression.md; game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md, Ruling 3
acceptance: (1) production/specs/d12-ledger-core.md, LIVE, one row per D12 and D11 clause naming the Core type and line that carries it or MISSING, with the CoreTests names that prove each carried one and the counts printed; (2) a call-site list, by grep with the pattern quoted, of every Game-layer read of NPC memory, Fact or GossipMill state that reaches a player-facing surface, each marked allowed (through PlayerKnowledge) or D12-violating, with the number examined; (3) the guard's shape named as the spec's next rung (a verify.py lint over Game files), NOT built
max_sessions: 1
status: READY 2026-09-02. systems-builder, one session, engine-neutral C#. FIRST UE-WAIT FILLER: the second builder slot of a day, ahead of every governance item, never the first slot, which is 027's.

FACTS INLINE, so the session is spent writing and not reading. Core:
PlayerKnowledge.cs (83 lines; KnownLead carries HolderId, TopicKey,
Summary, Source, ConfidenceWhenLearned, LearnedAt, Sensitive, Handled;
the class comment says never ground truth); Gossip.cs line 43 (Hops, 0 =
witnessed first-hand, the only provenance a Fact carries); Claims.cs
(a typed sentence becomes a Fact; ProcessClaim moves suspicion);
Informing.cs; Reliability.cs; Homicide.cs (TestimonyGrade). Game call
sites of PlayerKnowledge and KnownLead: GameController.cs 92 and 180 to
183, DialogueUI.cs 1052, 2173, 2183, 2194, SimDirector.cs 13813.
CoreTests/Program.cs: 21 mentions. The clauses to survey: witnessed /
heard(source, time) / deduced per entry; per-event entries beside
per-person; the conversation page for the person present; the model of
what an NPC knows with confidence, assembled only from evidence the
player holds; D11's per-NPC record of the player's claims, surfaceable
as the reason a claim is believed or doubted; no stored global
credibility number anywhere (grep for it and print the count); the
what-they-know HUD scoped to law enforcement in wanted states.
```

**Q3. `production/queue/032-ue-loop-investment.md`** line 5, append to the
status line: ` RISES 2026-09-02 (game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md, Ruling 1): with ties to Unreal, (a) decides D1 and this item's printer is (a)'s instrument. Step one rides 027's first UE dispatch; the named change waits for the printed series.`

**Q4. `production/queue/038-blind-pair-sheet.md`**, new file:

```
line: infrastructure (D1 comparison, the blind reading)
spec: game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md, Ruling 2
acceptance: tools/blind-pairs.py composites each of the four pairs with sides assigned by a seeded coin, writes the map to production/d1-probe/blind/map.json and the unlabelled sheets beside it, refuses to run if any of the eight stills is missing (printing which), and a sheet file with A, B or EQUAL per pair must be committed before a second invocation will print the map; selftest accepting case first on planted images, rejecting case a missing still
max_sessions: 1
status: WAITS 2026-09-02 until UE Phase B lands a still. instrument-builder. Both engines commit engine-named files today, so no blind look is possible without this.
```

**Q5. `production/queue/035-sodium-lantern-floods-a-near-wall.md`** line 5
becomes: `status: WAITS 2026-09-02 behind 027 Phase B (game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md, Ruling 4). Found by opening all four stills, which is the only way it could have been found. The lantern values live in the shared JSON, so both engines render the same flood and the pair stays fair; the first UE night frame says whether the flood is the JSON or Unity's light-unit conversion, and that is worth knowing before the printer is written.`

**B1. The next brief to Jafar** carries, with the cam_A night still as its
picture: one paragraph that the tie-break is applied as he ruled and what
it now means (Ruling 1, the named consequence included); the pros and cons
of Ruling 5 as written; that the moat now has a queue item; and the ask
for one usage number before anything spawns tomorrow.

**Not edited, and why.** The timebox ruling and the rotation ruling: LOGs,
this record is their amendment. `canon.md`: no world fact touched.
`vision-pillars-v2.md`: nothing in D11 or D12 contradicts it, and the goal
block is checked by `tools/goal-block-check.py`. `tools/dashboard/
build-dashboard.py`: `read_d1` carries no tie wording (grep this session).
`production/queue/done/000` line 35: a done item, history.

## Deliberately not decided

- The engine. Ruling 1 says how D1 closes; it does not close it.
- Any number for "tolerable" on the cost half of (a). No series; 032's
  printer is what produces one.
- The Ledger's visual design. D12 says it waits for a frame; so does the
  ladder.
- Whether the flood in cam_B night is the JSON or the conversion. The first
  UE night frame.
- Whether the guard 037 names is a lint or a test. After the survey prints.

## For the next session in one line each

- Apply T1 to T8, M1 to M4, Q1 to Q5 by hand, each target line confirmed
  by grep first; verify; one commit staged by name, the message listing
  every id as applied or deferred with a reason; push.
- Send B1 with the cam_A night still; ask for one usage number; spawn
  nothing else today.
- Tomorrow, after the number: engine-specialist for 027 Phase A plus 032's
  printer (facts inline), then systems-builder for 037; one director
  reviews both diffs before commit.
- When 027's first UE dispatch lands: `shotStatus` first, then the still
  (rule 4), then the printer's series; the parade must sit on the same side
  of cam_A's frame as in the Unity still or the pairs are mirrors.
- When a UE still exists: spawn 038 so the first blind look is blind.

Spawn row, quoted verbatim from `.claude/agent-log.tsv` (line 203):

    2026-09-02T14:56:47Z	studio-director

<!--RULING spawn=2026-09-02T14:56:47Z-->
