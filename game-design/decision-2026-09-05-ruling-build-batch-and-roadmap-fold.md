# Ruling: the 5 September build batch commits, the roadmap fold applies with two gates repaired, run 21 is dispatched on the committed state

> **STATUS: LOG, 2026-09-05. NOT CURRENT.** Director ruling at spawn
> 2026-09-05T16:47:22Z on the nine queue items (089, 090, 091, 095, 096, 097,
> 098, 099, 104), the publisher change, the staged roadmap fold, CLAUDE.md
> rule 13 and the recorded daily prompt. Queue 062 step 2 was ruled at
> 16:15:44Z and is not re-reviewed here. NOT CURRENT once the dictated edits
> in section 9 are applied and the batch is committed; from then the files
> are the reading copies.

VERDICT: APPROVED WITH DICTATED EDITS. The commit goes once section 9 is
applied and section 10's printed lines are in the message. The roadmap fold
APPLIES NOW with phase 1's and phase 4's gates repaired and four findings
recorded open. RUN 21 IS DISPATCHED after that commit. The glance ships with
its two dead taps WITHHELD, not fixed. Four of the nine items are BUILT AND
UNPROVEN and are statused so; five are LANDED. No builder pass is ordered.

## 0. What was read, what was counted, what was not run

No shell. Nothing was executed here; every count below is a read of the
tree, and the selftest counts in the brief are the builders' until section
10 makes the resident print them again into the commit message.

Read in full: the staged fold (`production/scratch/planner/100-roadmap-fold-proposed.md`),
`ledger-v2/respec/roadmap-v2.md`, `production/systems-inventory.json` (27
entries), `tools/systems-inventory-check.py`, `tools/publish-glance.py`,
`.github/workflows/publish-glance.yml`, queue 089, 090, 091, 095, 096, 097,
098, 099, 100, 104, the 062 ruling, `production/briefs/2026-09-05.md`,
`production/watchdog-prompt.md` lines 60 to 130, `production/NOW.md` lines
195 to 314 and 370 to 382, `production/decision-queue.md` lines 1 to 60,
`.claude/agent-log.tsv` lines 240 to 269. Read in part, at every line the
ruling rests on: `tools/glance.py`, `tools/map.py`, `tools/inbox-read.py`,
`tools/runner/telegram-bot.py`, `tools/runner/inbox.py`, `tools/runner/cards.py`,
`tools/queue-check.py`, `tools/docs-check.py`, `tools/dashboard/build-dashboard.py`,
`ledger/verify.py`, `.github/workflows/ledger-probe-unreal.yml`, CLAUDE.md
lines 138 to 157.

Counted, by grep, this spawn:

- `Combat\.` under `ledger/Assets/Scripts/Game`: 1 hit, `PlayerController.cs:399`,
  `Ledger.Core.Combat.StaminaAfterMoving`, inside the walk loop under a
  comment saying combat takes it over when it arrives. `public static` in
  `Core/Combat.cs`: 11 methods across two classes (`Combat` 6, `Violence` 5).
  The Game layer calls `Violence.KillingConfidence` and `Violence.Notoriety`
  (`ViolenceHost.cs:287, :335`); none of `Resolve`, `Available`, `StaminaCost`,
  `Recovered`, `Breathe` has a caller outside Core. The planner's finding holds
  and its own correction holds: `FightWitness` is constructed in Game
  (`ViolenceHost.cs:462, :469`), so "only method called" is the true sentence.
- `Arrested` under `ledger/Assets/Scripts`: 2 hits, `Game/CoatHost.cs:159`
  (definition) and `Core/Homicide.cs:61` (a comment recording no caller).
  Callers: 0 of 2 occurrences.
- The census, my own tally of the 27 entries against the planner's:
  byPhase R=0 0=1 1=3 2=7 3=4 4=2 5=1 6=9, sum 27; byStatus exists=13
  partial=11 absent=3; byArea moat=1 world=5 player-facing=17 content=3
  studio=1; evidence references 61. Every number agrees. Phase 1 is save and
  load (exists), time and calendar (exists), failure states (partial); phase 4
  is inventory and combat, both partial; phase 6 is menus, new game, settings,
  pause (exists), accessibility, graphics settings, credits (partial),
  gamepad, photo mode (absent).
- `parse_roadmap` in `build-dashboard.py:311` takes `cells[0:3]`, needs 3 or
  more cells, skips `---|` and the header. A fourth column is invisible to
  it. It is the only tool under `tools/` that reads `roadmap-v2.md`.
- `tools/docs-check.py` roots at `game-design/` and prints `ledger-v2` in its
  NOT WALKED line (line 206 to 211). It cannot see `roadmap-v2.md` at all, so
  "unrun docs-check on this diff" measures nothing about this diff either way.
- `Grain` in `Game/OptionsScreen.cs`: 0 hits, so the instrument's refusal of
  the builder's first guess is consistent with the tree.
- Em-dashes in the batch files: 0 in the runner tools, the queue items, the
  inventory, the staged fold, NOW.md, CLAUDE.md and the publish workflow. The
  2 in `tools/glance.py` and 1 in `tools/map.py` are the formatting guard's
  own rejecting fixtures (a planted em-dash and a planted italic tag fed to
  `check_formatting`), not prose.
- `production/rulings/`: does not exist. `production/outbound/`: does not
  exist. `production/outbox/`: one message file and no receipt.
  `production/inbox/`: README only. The tree holds NO record of any Telegram
  send, receipt, tap or delivery.
- The glance's `AUDIT = ("dashboard.html", "STATUS.md")` (glance.py:55) are
  repo-root files; the publisher's `SITE_FILES` is index.html, glance.html,
  map.html, .nojekyll. The two audit taps 404 by construction on the
  published site.
- `ledger-probe-unreal.yml` fires on push ONLY for `production/d1-probe/DISPATCH`.
  This batch does not touch it. `publish-glance.yml` fires on push for
  `production/queue/**`, `tools/glance.py` and eleven other paths; this batch
  touches several, so THE COMMIT IS THE PUBLISH.
- `tools/queue-check.py`: first word of `status:` classifies; `LANDED` is
  landed-in-place and not ready; `WAITS` is blocked. `production/queue/` holds
  95 item files plus README, which matches the 95 denominator the counter
  prints. The nine items all still read `READY`.
- 062's dictated edits D1, D2, D3 are applied (`make_base_material.py:78`,
  queue 062 line 63, NOW.md line 381). `production/decision-queue.md` carries
  NO record of Jafar lifting "wait for now": 0 hits for `lift`, 0 for `wait
  for now`. Condition two of the 062 ruling is not yet recorded.
- Studio-director rows: the newest is line 269, `2026-09-05T16:47:22Z`, and
  this ruling's stamp names it. Line 270 is empty.

PREMISE CHECK, CLAUDE.md section 0. Nothing in the batch touches the game's
premise: no engine, no asset, no licence entry, no purchase, GTA V not cited.
The roadmap edit is checked against the premise in section 1 and tightens two
gates towards the moat rather than away from it.

## 1. The roadmap fold: APPLIES NOW, two gates repaired, four findings open

The fold is item 4 part three of Jafar's order and its application closes
item 4, after which the studio stops building studio this week. It applies
now, as a resident edit of dictated text (section 9, D1), for three reasons:

1. Its census is verified twice over, by the planner's read and by mine, and
   it is a column DERIVED from the inventory that `ledger/verify.py` now
   validates on every commit. The risk of the edit is a wrong number, and the
   numbers were counted independently and agree.
2. The only machine reader ignores a fourth column (counted above), so
   nothing downstream can break.
3. The acceptance's `docs-check` clause is unsatisfiable by that tool (it
   does not walk the file and has no per-row word check), which the planner
   found and I confirmed. An unrun docs-check on this diff is not a gap in
   the evidence; a run docs-check would be a green number standing in for
   nothing. The acceptance is met by the hand census, labelled as one in the
   file, with the checker queued (section 11).

WHICH SYSTEMS MOVED PHASE: none, 0 of 27. The fold adds a derived column and
touches no `phase` value.

THE SIX REFUTED CLAIMS, RULED. Two are instrument faults in gates and are
REPAIRED in the dictated text. Four are scope or process questions and are
RECORDED in the roadmap as open.

- REPAIRED, phase 4. "Combat runs and is called from live play" is satisfied
  today by a stamina call in the walk loop. That is rule 5b: a gate that
  cannot fail. The gate now reads: "Core combat resolves a blow from a call
  site outside Core, callers counted and printed, in a landed run; feel
  check; a gunshot produces a measured town-wide perception event". Row
  word count 33 to 44.
- REPAIRED, phase 1. The phase is named the engine of consequence, the moat's
  second pillar is consequence persistence at 95, and the gate did not see
  arrest, whose Game-layer caller count is 0. The gate gains: "arrest
  reachable from live play: the arrest outcome's callers outside Core
  counted and printed, not zero". Engine-neutral wording on purpose, since D1
  may move the Game layer. Row word count 54 to 70. This is a director's
  call on an approved package and is reversible by Jafar on one word; the
  Producer names it tonight (section 6).
- OPEN, phase 4 sizing (Combat.cs is written; the work is call sites).
- OPEN, phase 6 carrying nine systems under a five-word gate. Whether
  ship-prep requires every phase-6 system to read `exists` is a scope
  decision for Jafar, not made in a batch review at the end of a day.
- OPEN, map and minimap in phase 3 with zero code, waiting on D12.
- OPEN, the row law (80 words, instrument link, verified date) has no
  instrument; a queued process item (section 11).

## 2. Run 21: DISPATCHED after this commit, on three conditions

The 062 ruling of 16:15:44Z authorised run 21 on two conditions; this ruling
confirms it on the committed state and adds nothing to the reading table in
that ruling's section 5, which stands unchanged.

Conditions, all resident actions, in order:

1. This batch is committed green, with `40 check(s), 0 failure(s)` and the
   lines in section 10 in the message.
2. Condition two of the 062 ruling is RECORDED: the dictated RULED entry in
   section 9, D5, goes into `production/decision-queue.md` in the same
   commit. Jafar's words are in the tree already, NOW.md item 6; the entry
   points at them.
3. The sha is captured, then a SEPARATE commit touches only
   `production/d1-probe/DISPATCH`, staged by name. Nothing else in that
   commit. Watch by ancestry.

IF RUN 21 PRINTS `materialConnections=12/14` AGAIN, under any status word:
that is a third consecutive landed run at the same fraction, and it is THE
ANSWER. The resident (a) records the reading in the stop-rule bullet of
NOW.md and in queue 062 as the answer, with `materialUvHeadVia` quoted so the
record says which hypothesis died (`..property-write-refused` or
`..unavailable` beside `materialUvHeadTriedAtWorst=9/9`); (b) reports it to
Jafar as an answer through the Producer, not as a retry pending; (c)
dispatches NO run 22 on this script; (d) spawns a director, because a landing
that changes a conclusion is a mandatory trigger, and D1's hand-edit clause
is invoked under that director's ruling and not before. `NO-LINE`, `NO-TOOL`
and `CREATE-FAILED` are nothing measured and neither discharge nor re-fire
the rule; re-dispatch needs a director. 13/14 and 14/14 read per the 062
table.

The frames from run 21 go to him through queue 091's photo path, which is
that path's first real use (section 6). If the photo send is refused, the
refusal is recorded and the frame's repo path goes in its place.

## 3. The two dead taps: WITHHELD from the published page, the publish goes

Jafar's clause is "everything else one tap down". On the published site the
map tap is real and the two audit taps are 404s. A tap into a 404 on the
first page he opens is a lie on the page; a page that says the audit level
is not published yet is a true page that misses one clause, and the clause
is filed. The lie is worse than the omission.

RULING: the two audit taps are withheld by a two-line dictated edit in
`tools/glance.py` (section 9, D2), which is part of this commit, and the
publish of the audit level is a queue item (section 11). Neither publishing
`STATUS.md` as a Pages file (served as source on a phone, exactly the
wrong-content-type case 097 refuses) nor copying a committed `dashboard.html`
(stale by construction, queue 047) is a one-line fix, and the instrument that
counts external hrefs is not to be weakened to let absolute links through.

The edit cannot go red: `AUDIT` has three uses in glance.py (lines 55, 811,
816) and none in its selftest, and `check_map_link` counts the map href only.
The resident reruns the selftest and pastes its count line into the commit
message beside the builder's 48; if the count differs, say by how much.

## 4. `production/rulings/` and what "done" means for 090

The directory not existing is expected, not a fault: the bot writes ruling
records on the `pc-inbox` branch and `tools/inbox-read.py` `deliver()`
creates the directory in this checkout with `os.makedirs` on the first
delivered record (lines 150 to 160, 256 to 258). The fold has a real caller
(`inbox-read.py:348`, `cards.fold_from_disk`), so rule 6 is satisfied for the
wiring.

But the acceptance of 090 is a real tap moving a real card with the WAITING
count printed either side, and that has never happened. Every stage is
selftested on fixtures; the path has not run end to end. RULING: 090 is BUILT
AND UNPROVEN and is statused `WAITS` behind the first real tap (section 9,
D3), which is queue 093's second half. The live WAITING card ("How close
should strangers stand?", DEFAULT B if unruled by 2026-09-07) is the
accepting fixture; when his tap lands and the fold prints
`waitingBefore=1 waitingAfter=0`, 090 closes.

One hole found here and queued (section 11): `ledger/verify.py`'s untracked
gate covers `production/inbox` only (`INBOX_REL`, line 1169), while the same
reader delivers receipts to `production/outbound` and rulings to
`production/rulings`. A delivered ruling record left untracked has the same
failure the inbox gate was written for.

## 5. The inventory's seventh field: KEPT, and sound enough to consume

`evidence` stays. The instrument is `check_evidence_ref`: the path must
resolve and, where a token is given, the token must be a substring of the
file. The builder's report that it refused their own first guess is
consistent with the tree (`Grain` is absent from OptionsScreen.cs). The
accepting fixture is the live inventory, the rejecting fixtures are synthetic
tokens, and verify.py runs the check on every commit. That is the discipline
this project asks for.

Three limits, named so 099 and 100 consume it correctly:

1. A token in a comment satisfies the check. `CoatHost.cs#Arrested` resolves
   on the definition of a method with zero callers. So `exists` means "a path
   resolves", never "reachable" and never "the phase clause is met". The
   fold text says so in its own words and the map's legend must never say
   more than the tool measures.
2. `absent` carries no evidence by rule, so the tool refuses a false `exists`
   and cannot refuse a false `absent`. The asymmetry is the right way round: a
   false exists costs a phase its gate; a false absent costs a builder a look.
3. The 27-name denominator is external to the file (queue 098's list), so
   `covered=27/27` is not the file grading itself. Keep it that way when 098
   moves; the tool already tries `queue/done/`.

## 6. What is DONE and what is BUILT BUT UNPROVEN, for the Producer's report

The tree holds no receipt, no delivered message, no ruling record and no
reading of the published URL. The container cannot reach `github.io`
(measured: proxy CONNECT refused, publish-glance.py docstring). So nothing
Telegram-shaped and nothing on glass can be called done tonight.

DONE, may be reported as such:

- 098, the inventory as data: 27 systems, exists=13 partial=11 absent=3, 61
  evidence references resolving, validated on every commit.
- 100, the fold: the roadmap says which systems each phase carries; two
  gates tightened because the inventory showed they could pass without the
  thing they name; Jafar can revert either on one word.
- 104, typed whole numbers only on the meter; the guard is inverted so a
  returning grid goes red.
- 095, the brief writes itself from repo state (today's is in the tree and
  passed the register); the queue counter moved from a frozen 22 to a
  reading that moves.
- 096 and 099, the glance and the map, as generated files that pass their
  own checks. Opened as files in the container; not yet seen on a phone.

BUILT AND UNPROVEN, each with the one action that proves it:

- 089, the outbox sender: proven by a receipt on `pc-inbox` for a real
  message. Tonight's Producer report goes through the outbox and IS the first
  candidate; tomorrow's 04:00 brief is the second.
- 090, the ruling taps: proven by his tap on the strangers card.
- 091, the photo path: proven by run 21's frames arriving as a photo.
- 097, the published glance: proven by the workflow's own
  `pageResult=OK` for `index.html` and `map.html` (the resident reads those
  two lines from the run before the word "published" is used anywhere; if
  they cannot be read from here, the report says "deploying, not yet read")
  and then by Jafar opening it. Nobody has opened it. He is the first.

The report may not say "sent", "published", "on your phone" or "done" of
anything in the second list. It carries the picture report-frame offers. It
names the two gate repairs in one sentence so he can strike them.

## 7. CLAUDE.md rule 13 and the recorded daily prompt

Rule 13 is APPROVED as written: Jafar's words, dated, no premise conflict,
consistent with rule 8 (arm the watcher), budget.md's ceiling and the
escalation cadence. It sits between rules 11 and 12 in the file; the number
is load-bearing and the position is not, so it moves below rule 12 (section
9, D6).

The daily prompt is recorded whole in `production/watchdog-prompt.md`, names
`tools/morning-brief.py`, carries rule 13, and stages the brief by name. One
rule 1 fault: lines 69 to 72 still say "NOT YET SET IN THE TRIGGER SYSTEM
... This section is a REQUEST", five lines above "STATUS: LIVE, reset
2026-09-05T16:20:45Z". Two statuses in one section is a record that says two
things; the stale one goes (section 9, D7).

## 8. The batch as code: what was checked, what is taken on report

Checked here: the publisher's site list and refusal rule, both halves;
`fetch()` reads `measured` before `status` so a proxy refusal is never a
404; the map's non-zero exit publishes a refusal page rather than a stale
map, and the glance's does not; the workflow's paths filter reads the map's
inputs out of the tools; the workflow's concurrency group is its own; the
bot answers `callback_query` and removes the old keyboard; the fold refuses
before it rules; the verify gates for the four selftests, the inventory and
the untracked inbox parse a count line and go red on none.

Taken on report, and reprinted at commit by section 10: every selftest
count; the queue counter moving both ways; `producer register PASS
filesChecked=2`; docs-check 141/141.

## 9. Dictated edits, applied by the resident before the commit

D1. Replace the whole of `ledger-v2/respec/roadmap-v2.md` with the text
below, verbatim. It is the planner's staged block with the phase 1 and phase
4 gates repaired and the findings section rewritten to say which were
repaired. Delete `production/scratch/planner/100-roadmap-fold-proposed.md`
in the same commit; its content is here and in the roadmap.

````markdown
# Roadmap v2 (2026-08-31)

Row law: each milestone row stays under 80 words, carries an instrument link and a verified date; detail lives in a milestone file; landed rows move to roadmap-history. Rows over the cap, or stale against code changes touching their area, fail the doc-decay gate.

| Phase | Milestone | Exit gate (instrumented) | Systems carried (production/systems-inventory.json, verified 2026-09-05) |
|---|---|---|---|
| R | Respec landed, canon written and approved | Jafar approves canon.md and this package | 0 of 27, by design |
| 0 | Studio v2 scaffold; D1 engine probe; one assembly line piloted (dialogue bank); judge calibration | D1 decision recorded with measurements; pilot line yields a verified piece; judge agreement at or above threshold in studio-v2/verification.md | 1 of 27: 1 partial |
| 1 | Engine of consequence: Core on chosen engine (perception, memory, gossip, schedules, save), largely transliteration guarded by the existing test suite | Gossip instrument green: witnessed crime reaches a second and third NPC within one in-game week; sim holds frame budget at target resident count; Core tests pass; arrest reachable from live play: the arrest outcome's callers outside Core counted and printed, not zero | 3 of 27: 2 exists, 1 partial |
| 2 | A street that lives: one street at the visual bar; kit and decal density; moving faces; live voice loop; the Ledger (D12); what-they-know HUD only for law enforcement in wanted states; petty crime verbs; witness-to-phone-box chase; 30 to 50 residents | Jafar feel check passed; screenshot bar met per D7 judges; conversation latency within budget; phase has a time budget set at kickoff | 7 of 27: 7 exists |
| 3 | The town: full Phase A scope; interior tiers; economy and cash; factions; narrative v2; radio, TV and brand bible; venues | Hours-of-content instrument; repetition blind test passed (no detectable line repetition in a 2-hour session); Meridian Test conditions 2 and 3 sampled | 4 of 27: 3 partial, 1 absent |
| 4 | Fists: melee combat, improvised weapons, scarce firearms as events | Core combat resolves a blow from a call site outside Core, callers counted and printed, in a landed run; feel check; a gunshot produces a measured town-wide perception event | 2 of 27: 2 partial |
| 5 | The region: Phase B land, driving, traffic | Gated on 3 and 4; gates set at kickoff | 1 of 27: 1 partial |
| 6 | Ship-prep (deferred until quality bar met) | The Meridian Test, all four conditions | 9 of 27: 4 exists, 3 partial, 2 absent |

Standing rule: every phase with a taste gate also gets a time or attempt budget at kickoff, set while calm. M17.10's lesson: instrumented phases, bounded milestones.

## The systems column: what it counts, and what it does not

A whole-file census of `production/systems-inventory.json` on 2026-09-05,
grouped by its `phase` field, against the 27 names pinned in queue 098. The
eight cells sum to 27 of 27, so every system names a row and every row can
say what it carries. Phase R carries 0 by design: it is the respec and holds
no player-facing system. The column is a hand census, counted twice
(planner and director) and dated; nothing yet checks it against the file,
which is the queued row-law checker's job.

Read the entries through the validator, never around it. A refused
inventory exits non-zero and emits nothing, so a broken file cannot be read
as a plan:

    python3 tools/systems-inventory-check.py --emit-json > inv.json
    python3 -c "import json;[print(e['phase'],e['status'],e['name']) for e in json.load(open('inv.json'))]" | sort

IT IS NOT A GATE READING. `exists` means a path resolves and, where a token
is given, that token is in it. A token in a comment satisfies it. It does
not mean the row's milestone clause is met: phase 2 counts 7 of 7 as exists
while its own what-they-know HUD clause is not among them, as the HUD
entry's note says. A count of `exists` is a floor under a phase, never a
gate reading for it.

## The fold of 2026-09-05: two gates repaired, four findings open

Ruling: `game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md`.
No row's phase value moved, 0 of 27.

REPAIRED. Phase 4's gate read "Combat runs and is called from live play" and
was already met, before phase 1, by the walk loop: `Ledger.Core.Combat.StaminaAfterMoving`
is called at `Game/PlayerController.cs:399`, the one Core combat method with
a caller outside Core, and it is the stamina term. The gate could not tell a
fight from a walk, so it now names a resolved blow. Phase 1 is the engine of
consequence and its gate did not see arrest: `CoatHost.Arrested` has 0
callers (2 occurrences in the tree, the definition and a comment in
`Core/Homicide.cs` recording the absence), so the gate would go green with
the consequence spine's terminal state unreachable. It now names arrest.
Both are a director's call on an approved package; Jafar reverts either on
one word.

OPEN, recorded and not repaired:

1. Phase 4 sizes combat as unwritten work. `Core/Combat.cs` is written (Blow,
   Fighter, BlowResult, FightWitness, Resolve, Available, StaminaCost) and the
   inventory scores it partial. The open work is call sites, not design.
2. Phase 6 is five words and carries 9 of 27 systems, more than any row,
   including 2 of the 3 absent (gamepad, photo mode) and the local-LLM half
   of graphics settings. Its gate, the Meridian Test, measures none of the
   nine. Whether ship-prep requires every phase-6 system to read exists is
   Jafar's call and is not made here.
3. Phase 3 names seven items and map and minimap is not one; the inventory
   schedules it into phase 3 with zero code and blocker D12. The row waits on
   D12.
4. The row law above demands an instrument link, a verified date and an
   80-word cap per row. 0 of 8 rows carries a link or a date, and nothing
   measures any of it: `tools/docs-check.py` walks `game-design/` only, and no
   tool reads "doc-decay". Counted by hand for this edit, whole row: R 18,
   0 39, 1 70, 2 68, 3 49, 4 44, 5 22, 6 22; worst 70 of 80. Before the fold:
   13, 34, 47, 63, 42, 28, 17, 13. The checker is a queued process item and
   waits, by the standing rule, until the studio builds studio again.
````

D2. `tools/glance.py`, two edits. Line 55 becomes:

    AUDIT = ()  # dashboard.html and STATUS.md are NOT on the published site yet; a tap into a 404 is withheld, not shipped (ruling 2026-09-05 section 3)

Lines 812 to 816, the `foot` assignment, become:

    foot = ("Generated by %s at %s. Beside this page: %s, every system as a "
            "tile. The audit level, dashboard.html and STATUS.md with every "
            "derivation and denominator, is in the repository and not yet "
            "one tap down."
            % (TOOL, now.strftime("%Y-%m-%d %H:%M UTC"), SIBLING[0]))

Then rerun `python3 tools/glance.py --selftest` and paste its count line.

D3. Status lines, first word load-bearing for `tools/queue-check.py`. Replace
each item's `status:` line with the text given.

- 098: `status: LANDED 2026-09-05. 27 entries, exists=13 partial=11 absent=3, 61 evidence references resolving, validator called by ledger/verify.py, selftest 9/9 rungs. The seventh field, evidence, is KEPT by game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md section 5.`
- 100: `status: LANDED 2026-09-05 by game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md section 1. Applied with phase 1 and phase 4 gates repaired and four findings open; 0 of 27 systems moved phase. The acceptance's docs-check clause is unmeasurable by that tool, which walks game-design/ only; the row-law checker is queued.`
- 104: `status: LANDED 2026-09-05. Selftest 73/0 with the keyboard fixture inverted. The first live typed reading on the PC is the proof in use and has not been taken.`
- 095: `status: LANDED 2026-09-05. production/briefs/2026-09-05.md generated by the tool and passed the register; one queue counter (moved 85 to 86 and back on a planted file); run-night.ps1 'Fallback brief' count 0; the trigger prompt is recorded. The morning push rides queue 089 and is unproven until a morning passes.`
- 096: `status: LANDED 2026-09-05. Selftest 48/0; opened as a file in the container, not yet on a phone, which is 097's proof. The audit taps (dashboard.html, STATUS.md) are withheld until they are published, ruling section 3.`
- 099: `status: LANDED 2026-09-05. Selftest 76/0, tiles=27 beside entries=27; opened as a file, not yet on a phone, which is 097's proof.`
- 089: `status: WAITS 2026-09-05 behind the first real send. Built and selftested 43/0; production/outbound/ holds no receipt, so the acceptance's real message and outboundLatencySec are not yet measured. The first candidates are tonight's Producer report and tomorrow's 04:00 brief.`
- 090: `status: WAITS 2026-09-05 behind the first real tap (queue 093). Built and selftested (cards 41/0, bot 73/0, inbox 54/0, inbox-read 25/0); the fold's caller is tools/inbox-read.py:348; production/rulings/ does not exist and is created by the first delivered record. Ruling section 4.`
- 091: `status: WAITS 2026-09-05 behind the first real photo send, which is run 21's frames. Built and selftested.`
- 097: `status: WAITS 2026-09-05 behind the first push's own reading. Pages measured enabled; the workflow requests index.html and map.html after deploy and prints pageResult=; the container cannot reach github.io (proxy CONNECT refused, measured). Done when the run prints pageResult=OK for both and Jafar has opened it. RULED A BY JAFAR 2026-09-05: publish as designed, budget bar included.`

D4. NOW.md, the bullet beginning `**THE UNREAL STOP RULE IS STILL IN FORCE`,
append one sentence after the sentence that names the 062 ruling:

    Dispatch of run 21 confirmed on the committed state by
    game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md
    section 2, which also says what a third 12/14 means.

D5. `production/decision-queue.md`, insert directly under `## RULED THIS
WEEK` and its blank line, in the shape the section already uses:

    ### RULED 2026-09-05 BY JAFAR: run 21 goes, item 6 of his standing order.

    His words, recorded in production/NOW.md item 6 of the 2026-09-05
    standing order: "Then the game: 062 step 2, run 21. THE FIRST TEXTURED
    FRAMES COME TO HIM AS IMAGES." That lifts the "wait for now" of
    2026-09-03 and is condition two of
    game-design/decision-2026-09-05-ruling-062-step-2-third-status-word.md
    section 5. Condition one, step 2 committed, is met by the commit carrying
    this entry. Dispatch follows in its own commit with the sha captured
    first. If 21 prints materialConnections=12/14 that is the answer,
    reported and not retried.

D6. CLAUDE.md: cut the rule 13 block (the paragraph beginning `**13. A turn
ends at the ceiling` through `Jafar, 2026-09-05.` and its trailing blank
line) and paste it after rule 12's paragraph, before `## Before you commit`.
No word changes.

D7. `production/watchdog-prompt.md`, replace lines 69 to 72 (from `STATUS:
NOT YET SET IN THE TRIGGER SYSTEM` to `which is the contract` / `above.`)
with one line:

    Was a REQUEST until 2026-09-05T11:38:02Z, when the trigger was set; the LIVE line below is the reading copy.

## 10. The commit

One reviewed commit for the batch, staged by name. Before it, in this order,
with each printed line pasted into the message verbatim:

1. `python3 tools/ue/make_base_material.py --selftest` summary line, must
   read `40 check(s), 0 failure(s)` (already ruled; still pasted).
2. `python3 tools/systems-inventory-check.py`: the `entries=` line, the
   `byStatus:` line and the `byPhase:` line. `byPhase` must read
   `R=0/27 0=1/27 1=3/27 2=7/27 3=4/27 4=2/27 5=1/27 6=9/27` or the roadmap
   column in D1 is wrong and this approval does not apply.
3. `python3 tools/glance.py --selftest` count line, after D2.
4. `python3 tools/queue-check.py` done line, after D3. Expected shape:
   ready falls by ten and blocked rises by four against the 85/95 and 4/95
   the brief reports; print what it says, not what is expected.
5. `python3 tools/docs-check.py` summary line, after this file exists.
6. `python3 ledger/verify.py`, footer pasted from `ledger/.verify-footer`.

Then the dispatch commit, `production/d1-probe/DISPATCH` alone, sha captured
first.

## 11. Queue items to allocate, none started this week

Numbers are the resident's to assign; none of these spends a pass now, and
the standing rule holds them until the studio builds studio again.

- A. Publish the audit level beside the glance: `dashboard.html` built fresh
  by the publish step and `STATUS.md` rendered as HTML, both in `SITE_FILES`
  and both requested after deploy; the glance's `AUDIT` taps come back when
  this lands. Item 3's last clause.
- B. The untracked gate covers `production/outbound` and `production/rulings`
  as well as `production/inbox`, with a rejecting fixture per directory.
- C. The row-law checker for `roadmap-v2.md`: 80 words per row printed, an
  instrument link and a verified date per row, and the systems column equal
  to the tool's per-phase census. The doc-decay gate the row law names and
  nothing measures.
- D. The publish verdict as a committed file (rule 12): the workflow's
  `pageResult=` lines land in the tree under a name keyed by short sha, so
  "published" is read from a file and not from a step summary.

## 12. The quality ladder at close

The console is at "first working" on the container side and "built, unrun"
on the PC side; the next rung for every unproven path is one real event from
his phone, all four of which happen in the next day without anyone building
anything. The inventory is at "a measurement replacing a claim"; its next
rung is the column checked by machine (item C). The roadmap is at "gates that
can fail"; its next rung is a gate per row that a tool reads, which is D1's
engine decision and not this week's. Run 21's next rung is its reading. None
of these is blank.

<!--RULING spawn=2026-09-05T16:47:22Z paths=ledger-v2/respec/roadmap-v2.md,production/scratch/planner/100-roadmap-fold-proposed.md,production/systems-inventory.json,tools/systems-inventory-check.py,tools/glance.py,tools/map.py,tools/publish-glance.py,.github/workflows/publish-glance.yml,tools/morning-brief.py,tools/queue-check.py,tools/producer-check.py,tools/inbox-read.py,tools/runner/telegram-bot.py,tools/runner/inbox.py,tools/runner/outbox.py,tools/runner/cards.py,tools/runner/run-night.ps1,ledger/verify.py,CLAUDE.md,production/watchdog-prompt.md,production/NOW.md,production/decision-queue.md,production/briefs/2026-09-05.md,production/queue/089-the-outbox-reaches-his-phone-and-the-check-runs-first.md,production/queue/090-a-tapped-option-becomes-a-ruling-in-the-queue.md,production/queue/091-a-verified-visual-arrives-as-a-picture-with-one-caption.md,production/queue/095-the-morning-brief-is-generated-from-repo-state.md,production/queue/096-the-glance-page-phone-first.md,production/queue/097-publish-the-glance-so-it-opens-on-his-phone.md,production/queue/098-the-player-facing-systems-inventory-as-data.md,production/queue/099-the-map-view-rendered-from-the-inventory.md,production/queue/100-fold-the-inventory-into-the-roadmap-as-phases.md,production/queue/104-meter-readings-are-typed-integers-and-nothing-else.md,game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md-->
