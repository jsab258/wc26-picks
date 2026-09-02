# DIRECTOR RULING: the constitution cut lands, the attribution sweep lands, the PC channel lands, and four folded questions (2 Sep 2026)

> **STATUS — LOG, 2026-09-02. NOT CURRENT once the batch is committed with the dictated edits applied and queue items 020 to 024 exist; from then CLAUDE.md, the casebooks, ledger/verify.py and the queue files are the reading copies and this file is their history.**

The banner carries the only em-dash in this document, because
`tools/docs-check.py` hard-codes that character in the regex it accepts.
Named as a finding two rulings ago and queued there; not a licence.

Sixth ruling since 1 September. This role has no shell: every executed number
below is the resident's or a builder's, and my check is that the code exists
at the cited line and asserts what the number claims. Where I could not
check, it says so. The builders' reports were not read as evidence; the diffs
were.

## What was verified before ruling

- My own row: `.claude/agent-log.tsv` line 189, the newest in the file.
- `CLAUDE.md` in full (230 lines, the cut). The goal block matches the shape
  `tools/goal-block-check.py` extracts (heading, `## The goal`, closed by
  `---`). The premise paragraph's "working window 1988 to 1992" is
  `canon.md` line 16. GTA V PS3 appears at exactly two sites, both as
  RETIRED with D8 cited (lines 62 and 225); D8 itself read in full.
  `claude_md_size` (verify.py 1023 to 1060) is in the check list at 5656 and
  has an accepting live fixture plus a synthetic pair (5445 to 5477).
- The mover and its checker, read from the scratchpad: `move.py`,
  `verify_moves.py`, `plan.py`. The PLAN has 23 blocks; grep for the marker
  `moved verbatim from CLAUDE.md` finds 23 across the eight destinations.
  The plan's gaps against the original (which I hold in full) are separators
  and headings only, plus the two STAYS blocks. The checker asserts every
  non-blank source line is a substring of its destination, reading the
  original from `git show HEAD:CLAUDE.md`; that is adequate for "nothing
  deleted" and says nothing about order, which `move.py` preserves by
  construction.
- Twenty-four distinctive sentences from the original grepped in
  `ledger-v2/studio-v2/`: all present (the 1950s premise incident, the noon
  sun, the 560-against-29 denominator, `c61047f`, the backticked heredoc,
  the two residual holes, "what counts as one batch", "347 commits and 133
  builds", the two-maxima table, `verdict-read.py`, `resync.py`, the 1 Sep
  cadence correction, and the rest).
- The four carry headers (casebook-claims, operations, organization, runner)
  and `production/quality-ladder.md` in full; `legacy/claude-md-superseded-
  2026-09-01.md` in full; `production/queue/README.md`; L23 in
  `learning.md`; `tools/docs-check.py` lines 27, 49, 134 to 143 (walks
  `game-design/` only and prints the other three roots as NOT WALKED).
- `tools/attribution-check.py` in full (710 lines). `THIRD-PARTY.md` in full.
  `game-design/research/content-sourcing.md` section 1.3. What sits under
  every watched directory row, by glob (see Ruling 3). `tools/props/
  fetch_props.py` 220 to 247 and `fetch_visual.py` 377 to 407.
  `ledger-v2/research/license-allowlist.md` in full.
- `tools/pc-watcher.py`: the docstring, TABLE 300 to 404, `tokens`,
  `command_for`, `missing_steps`, `read_request`, `already_done`, `run_job`,
  `resync`, `deliver_before_discard`, `publish` (789 to 915), `one_pass`
  (918 to 991), `main`, and the selftest at 1270 to 1378. `START THE STUDIO
  MACHINE.bat` in full. `meshgen.py` 1340 to 1355 and `imagegen.py` 1431 to
  1450 for the preflight claim. `tools/pc-request.py` in full.
  `game-design/pc-jobs/request.json` and `result.txt`.
- `tools/props/fetch_vignette.py` 1 to 60 and 170 to 317;
  `production/specs/vignette-fetch-01.json` in full; the BOM
  (`vignette-bill-of-materials.md`) in full; `tools/imagegen/prompts.json`
  item ids by grep; `tools/imagegen/README.md`.
- `ledger/verify.py`: `DIRECTOR_WORK` and `DIRECTOR_EVIDENCE` (2345 to
  2395), `_cadence_read`'s diff and untracked walks (2962 to 3019),
  `director_cadence`'s docstring (4826 to 4945). `.claude/hooks/
  verify-gate.sh` in full, `.claude/hooks/log-agent.sh` in full,
  `.claude/settings.json`, `.githooks/` (one file: `commit-msg`).
- Queue items 011, 012, 013, 014, 016, 017, 018, 019; `production/NOW.md`;
  `production/budget.md`; `production/week-plan.md`; `production/
  watchdog-prompt.md`; `decision-D1b-rescope.md` 1 to 160; the three 1 Sep
  rulings.

## Ruling 1: the batch LANDS, as one commit, with dictated text edits and no logic changes

All three halves are the best version this container can produce of the
thing each was asked for, and each says at the seam what it could not run.
Nothing weakens an instrument. Three instruments that could not see
something now can: a word count in every footer, a suffix residue that names
the format nobody thought of, and a job table whose every flag the selftest
re-reads.

One commit, because the first commit that touches the reviewed scope moves
the reference past my row and a second scope-touching commit would then be
unruled. Stage by name:

`CLAUDE.md`, `ledger/verify.py`, `ledger-v2/studio-v2/casebook-claims.md`,
`ledger-v2/studio-v2/casebook-measurement.md`, `ledger-v2/studio-v2/
casebook-build-and-evidence.md`, `ledger-v2/studio-v2/operations.md`,
`ledger-v2/studio-v2/organization.md`, `ledger-v2/studio-v2/runner.md`,
`legacy/claude-md-superseded-2026-09-01.md`, `production/quality-ladder.md`,
`production/watchdog-prompt.md`, `tools/attribution-check.py`,
`THIRD-PARTY.md`, `game-design/research/content-sourcing.md`,
`tools/props/fetch_props.py`, `ledger/Assets/Props/ATTRIBUTION.json`,
`tools/pc-watcher.py`, `START THE STUDIO MACHINE.bat`, the queue moves and
new items named in Ruling 9, `production/NOW.md`, and this file. Never a
`__pycache__` directory. `game-design/pc-jobs/request.json` is NOT in this
commit (Ruling 8).

Conditions, all text, dictated so nothing is judged at apply time:

1. **CLAUDE.md edits E1 to E6** (Ruling 2). After applying, run verify and
   read the footer's `CLAUDE.md N/2000 words`. My hand count puts N near
   1,989. If N is over 2000, apply E7 as well. If it is still over, STOP and
   resume this director for a fresh row; do not trim by judgement.
2. **runner.md and watchdog-prompt.md corrections D1 and D2** (Ruling 2,
   part C).
3. **The `publish()` docstring D4** (Ruling 4).
4. **The Props attribution note D3, in both places** (Ruling 3).
5. **Queue moves and new items** as in Ruling 9.
6. **The commit message quotes** the CLAUDE.md word count from the footer
   and both selftest counts (attribution-check fixtures, pc-watcher checks)
   from a run made AFTER edits 1 to 4, never the briefs' numbers.
7. **Commit before pulling.** `pc-results` is a separate branch now and the
   props outputs are evidence, so the old hazard is smaller; the rule stands
   because the remedy if the reference moves is to resume this director, not
   to edit the stamp.

## Ruling 2: the cut makes the project safer, on two conditions I am imposing now

The premise question first, because it outranks the formatting ones.

**The file every session reads is now the rules, and the incidents are one
hop away. That is the right trade, and the evidence for it is the old file
itself.** The 16,291-word version records, in its own words, roughly fifteen
rules broken while written down, several within an hour of being written,
one of them (the 1950s premise) asserted over four correct sources. A file
nobody holds in their head does not make its incidents believable; it makes
them unread. A rule read at every session start with a pointer to its
incident is strictly more than a rule and its incident both unread.

What the cut does NOT do is make the pointers get read, and this project's
only data point on pointers is L23: an enforcement clause pointed at a
superseded file for a day and nothing announced it. So the casebook is
retired quietly if, and only if, two things are allowed to happen: the
pointers rot, and the casebooks decay. Neither has an instrument tonight.
`docs-check.py` walks `game-design/` only and prints `ledger-v2/` as NOT
WALKED. Both get one: queue item 020 (Ruling 9). Until it exists, the cut is
safer than the file it replaces and not yet safe.

**Part A: the text edits.** Six, each replacing exact text. E1 removes a
claim that is false in the new file (rules 1 to 12 do not name where their
evidence lives; the bottom section does, by rule number). E3 corrects
"project document" to "anything", which is what the constitution says and
what Ruling 6 of 1 Sep applied to instrument prose. E4 puts the six
escalation triggers, the resume rule, the one-line-correction clause and the
stop-hook rule back into the file that governs the resident: three rulings
cite the one-line clause by name and queue item 014 cites the stop-hook
rule, and neither is in the cut. "Escalation is mechanical, never judged"
with no list is a word, not a mechanism. E2 and E6 pay for E4 in words.

E1. Replace lines 23 to 27 with:

```
Read this first, every session. It is not style guidance. Every rule below
exists because it was broken here, and the incident is what makes it
believable rather than decorative. The incidents moved intact to the
casebooks listed at the bottom, by rule number.
```

E2. Replace lines 29 to 31 with:

```
It was 16,291 words on 2026-09-01. A paragraph added here is read by every
future session, so it goes to a casebook instead.
```

E3. Replace lines 42 to 48 with:

```
Two are absolute and repeated here. THE LICENCE ALLOWLIST IS LAW
(`ledger-v2/research/license-allowlist.md`): nothing ships that is not on it,
and a new tool enters only through a decision record naming its weights
licence. THE FORMATTING LAW: no em-dashes and no italic text in anything
written from 31 August on; older text is corrected opportunistically, never
rewritten wholesale.
```

E4. In the paragraph at line 177, replace the sentence `Escalation is
mechanical, never judged.` with the following; the rest of that paragraph
(from `` `director_cadence` in ``) stays as written:

```
Escalation is mechanical, never judged: a director is spawned for
builder-batch review before commit, queue reorder or refill, a landing that
changes a conclusion, a verifier-versus-builder disagreement, a close-out,
and anything touching premise, roadmap or this file. Pending questions fold
into one spawn; a killed director is resumed, never restarted. The resident
hand-applies only dictated text or a genuine one-line fix, and never commits
a builder's work-in-progress because a stop hook asks: the tree goes clean in
one reviewed commit per batch.
```

E5. Under `## The standard`, remove the two asterisks wrapping Jafar's quote
on lines 189 to 190 so it reads `Jafar: "it has to be ... AI slop here."`,
and on line 193 replace the em-dash between `information 90` and `against`
with a comma, so the line reads `information 90, against a best-in-class`.
Jafar's words are unchanged; the italics and the dash were the writer's, and
a file rewritten from scratch today is the opportunity the
opportunistic-correction rule names. (This falsifies the scratchpad
checker's STAYS assertion for those lines; the checker is a one-shot tool
that has done its job and is not committed.)

E6. Replace lines 196 to 203 with:

```
And the standing order underneath it, 16 Aug, his words: "use creativity and
skill and available resources to get the best possible result in all aspects
of the game." Not "make it work", the best result AVAILABLE. It is asked at
close, through `production/quality-ladder.md`: is this the best available
result or the first working one? A blank next rung is a research task, not a
finished aspect.
```

E7, only if the count is over 2000 after E1 to E6. Replace lines 54 to 56
with:

```
Any 1950s or 1970s framing is wrong; both drifts have happened here, one of
them four times in one conversation over four sources that were all correct.
```

**Part B: the two referred items.** The old H1 was a title, not content; a
title carrying the character the formatting law forbids is replaced by its
compliant equivalent, and the plan records it as SUPERSEDED_IN_PLACE. "Nothing
deleted" stays true of content and the record says the exact thing that
happened. Accepted. `## The standard` staying in CLAUDE.md is right; its
em-dash and italics are corrected by E5 for the reason given there.

**Part C: a claim the cut moved without correcting, and the note that
pointed at it.** `runner.md` line 70 now carries, verbatim, "IT IS DISABLED
RIGHT NOW, 26 Aug". The watchdog was re-enabled 2026-09-01 16:00Z
(`watchdog-prompt.md` line 6). `watchdog-prompt.md`'s closing section says
the stale sentence is in CLAUDE.md's AUTO MODE section, which is no longer
true. Queue item 011 exists for exactly this and waited on a director row
because CLAUDE.md was the host; the host has changed and this row covers it.

D1. In `ledger-v2/studio-v2/runner.md`, after the paragraph ending "never
end a turn without arming something." (line 43), insert:

```
THE WATCHDOG PARAGRAPH BELOW SAYS "IT IS DISABLED RIGHT NOW, 26 Aug". True
when written, false since 2026-09-01 16:00Z, when it was re-enabled with a
rewritten prompt. Corrected here rather than inside the moved text, per the
carry rule above. The live state and the prompt as set are in
production/watchdog-prompt.md, which is dated and wins over this file.
```

D2. In `production/watchdog-prompt.md`, replace the body of the section
`## One known inaccuracy elsewhere, named rather than fixed silently` with:

```
The paragraph saying the watchdog "IS DISABLED RIGHT NOW, 26 Aug" left
CLAUDE.md on 2026-09-01 (task 013) and now sits, verbatim, in
ledger-v2/studio-v2/runner.md, where the carry header directly above it
carries the correction, applied under the director ruling of 2 September.
Queue item 011 closed with that ruling.
```

**Part D: the D8 and L23 fixes, checked.** Both GTA V passages are in
`legacy/` under a LOG banner that names D8 and says what survived the
retirement (the decomposition and the measured-phase method), which matches
D8's own text. The standard's enforcement clause now points at
`production/quality-ladder.md`, whose header records the orphaning, and
`production/queue/README.md` carries the close step. Both correct.

## Ruling 3: the attribution fix is sufficient for its instance, and the wider audit was owed, so I did the cheap half of it

**The fix.** Two declared sets whose union must cover every file walked,
an unclassified residue that prints and fails, `under()` on path components
rather than substrings, a branch that prints for a watched directory with
nothing countable instead of falling through, and twelve fixtures with the
three accepting cases first and the live tree as the first of them. The
OpenGameArt row and the voice-conds row are in `THIRD-PARTY.md`. The `.bin`
ruling rests on bytes (the `LDGRVOICE1` magic, the manifest, the
mel-spectrogram) and the reasoning is the barks' reasoning; accepted. The
row-per-source shape is right and the token for the vignette row being
deliberately not "ambientCG" is the kind of thing that stops a guard going
green for the wrong reason.

**Whether a wider audit is owed: yes, and the cheapest decisive version is
to list what sits under each watched row.** Done tonight by glob. The
result:

| watched row | what is under it | second source? |
|---|---|---|
| `ledger/Assets/Props` (Kenney) | five Kenney kits, `base-mesh/`, `oga-vehicles/` | both now rows |
| `ledger/Assets/StreamingAssets/Decals` (ambientCG) | `ambientcg/`, **`generated/`: 14 PNGs, `manifest.json`, `ATTRIBUTION.json`** | **YES, instance three** |
| `ledger/Assets/Resources/Sky` (Poly Haven) | four `.hdr` under `polyhaven/` | no; but `THIRD-PARTY.md` line 253 names `ledger/Assets/Sky/polyhaven/`, a path that does not exist |
| `ledger/Assets/Characters` (Mixamo) | flat `.fbx` set plus two text files | no |
| `ledger/Assets/StreamingAssets/CityPack` | its own `ATTRIBUTION.json` | no |
| `game-design/voice-live`, `voice-conds`, `picked-clips`, `voice-candidates` | wavs, reports, conditioning | no |
| `game-design/reference` | the five frames | no |

**Instance three, named so it is not found a fourth time by accident:** the
fourteen images under `Decals/generated/` are model output (Z-Image-Turbo,
Apache-2.0 weights, per `tools/imagegen/README.md`), every one marked
`review=pending` in its manifest, and they are counted under the ambientCG
token. `THIRD-PARTY.md` contains no "generated", no "Z-Image", no "Apache"
(grep: zero hits). Nothing unlicensed shipped, the outputs are unrestricted;
the RECORD is wrong in exactly the way the OGA record was, and
`content-sourcing.md` section 4.6 already says what the record must carry
(model, weights licence, training-data claim, review date). This is queue
item 022, a builder's job, not a hand edit tonight: it needs a WATCHED row
with its own token, a fixture, and the section.

**The Props `ATTRIBUTION.json` note.** It says "Sources for every model in
this directory" and lists five Kenney kits while 96 non-Kenney files sit
beneath it. Written by `fetch_props.py` line 238, so the fix is the string
in the generator AND the committed file, to the same text, which is what a
regeneration would produce. And the docstring at 220 to 221 claims
`tools/attribution-check.py` "enforces the pair of files agreeing"; it never
opens `ATTRIBUTION.json`. That sentence is corrected in the same edit.

D3, three sites:

- `tools/props/fetch_props.py` line 238 to 239, the `"note"` string, and
  `ledger/Assets/Props/ATTRIBUTION.json` line 2, the `"note"` value, both
  become:
  `Sources for every Kenney kit under this directory. Other sources here (base-mesh, oga-vehicles) carry their own THIRD-PARTY.md, written by tools/props/fetch_visual.py, and the root THIRD-PARTY.md is the human copy checked by tools/attribution-check.py.`
- `tools/props/fetch_props.py`, the docstring sentence
  `tools/attribution-check.py enforces the pair of files agreeing.` becomes
  `tools/attribution-check.py checks the root THIRD-PARTY.md by token and does not read this file; the pair agreeing is a discipline, not a gate (ruled 2 Sep 2026).`

The Sky path on line 253 and the Decals path on line 223 of
`THIRD-PARTY.md` are the same fault twice; 017 item 1 already owns the
Decals one and gains the Sky twin (Ruling 9). Not dictated tonight because
they belong to one builder touch of a licence document, and the previous
ruling accepted 017 for a builder.

## Ruling 4: the PC channel lands; the resident's review is right on four counts and overstated on two

The four citations check out by reading: `tokens()` is a fixed four-entry
dict (442 to 450) and nothing from the request reaches it; `--no-send` is on
lines 349, 362, 374 and 391; `JOB_TIMEOUT` (426 to 432) with the selftest
at 1307 asserting both directions; `PS` and `PY` share the script-path-second
shape in `command_for` (460 to 476). The premise correction (last run 14
Aug, "dormant" never established) is accepted and is what a builder is for.

**Where I disagree with the review, plainly.**

First, the brief says the builder "prints a warning instead" of a lock file
for two watchers. I read `one_pass`, `main` and the `.bat` in full: no such
warning exists. What exists is an `index.lock` back-off (`one_pass` line
930, returns "busy") and a `.bat` design comment explaining why `schtasks`
is not also registered. Neither says anything when a second watcher is
running. And the shared `STATE` file is written only when a job ENDS (line
988), so a second watcher polling during an eight-hour batch reads the
request as not done and runs the same batch again, on the same card. The
`index.lock` guard cannot see that: no git runs during the job.

Second, the builder's reason for leaving the `publish()` docstring false is
half right. Both generators' `preflight` DO refuse a clone that is not on a
branch (meshgen 1347 to 1353), but both return on `not self.enabled` BEFORE
that test (meshgen 1343, imagegen 1436), and under the watcher every
generator runs `--no-send`. A detached head would degrade a `.bat`-launched
run with sending on, not the watcher's jobs. The conclusion is the same: do
not detach, correct the docstring.

**Decision on the docstring: correct it to describe what the code does. No
code change.** The behaviour is safe by a route the docstring does not
mention: `deliver_before_discard` sees the published commit already on
`pc-results` and the next hard reset puts the local branch back on origin.

D4. Replace lines 798 to 800 of `tools/pc-watcher.py` (the paragraph
beginning `The commit is made on a detached head`) with:

```
    The commit lands on the local branch, which after `resync` is the main
    branch's name at the main branch's sha, so this clone ends one commit
    AHEAD of origin. Nothing detaches: this docstring used to say the commit
    was made on a detached head, and no line here ever did that. The next
    pass's `deliver_before_discard` sees the commit already on `pc-results`
    and the hard reset puts the local branch back on origin's sha, which is
    what keeps the clone clean between jobs. Detaching would be the wrong
    fix anyway: both generators' `preflight` refuse to send from a clone
    that is not on a branch, and a .bat-launched run with sending on would
    go quiet on that reason after a detaching publish.
```

**Decision on two watchers: the refusal of a naive lock file is ENDORSED
for the reason given (a crashed window must not stop the machine for ever),
and the absence of any guard is OVERRULED.** The shape that has both
properties reuses what exists: `STATE` gains a `running` entry written at
job START carrying the request id, the job name and a start time; a second
watcher that reads a `running` entry younger than that job's `JOB_TIMEOUT`
skips the request and prints why, once; an entry older than the timeout is
stale by the same bound that would have killed the job, is ignored, and the
line says so. Both outcomes fixtured. Queue item 023, not a landing
condition: tonight there is one watcher and the Startup copy does not exist
until Jafar clicks the file once. It is first in 023 because the first
double-click while a window is already open is the day it matters.

## Ruling 5: step 4 is FOLDED, and the "runnable tonight" claim is withdrawn

**FOLD.** The 26 PROC lines are not step 4. D1b's admissibility rule (the
re-scope ruling, "every object in each engine's scene arrives via its
generator from the shared JSON") makes them features of the D1b scene
generator whatever any library holds; the BOM says so itself under group B.
Costing them as overnight work was a reading of step 4 made before the BOM
existed, and the resident was right not to re-cost a ruled step alone.

**Step 4 is therefore the seven 2D lines, and its honest cost is one short
content-wrangler session plus zero for the run, not "near zero Claude".**
Verified by grep over `tools/imagegen/prompts.json`: no item id for double
yellow lines, puddle mask, lit interior, street name plate, gutter water,
net curtain or graffiti exists. The batch the channel can run tonight is the
signage batch, already made and skipped on re-run. So "the 7 images of step
4a are now runnable through the channel" is false as a statement about
tonight; the channel is runnable, the batch is not written.

Two of the seven need canon before a prompt can be written (E10 needs a
minted street name; G7 needs in-world crew names), and three of the seven
are better made deterministically than by diffusion (`content-sourcing.md`
Tier A: two yellow strips and a noise mask are Pillow, not a model). The
brief for 025 (Ruling 9) makes that call per line rather than sending all
seven to the image model because the BOM's column said 2D.

The 4,500-a-night arithmetic is struck from step 4 as the resident already
recorded; it describes a bulk material library and nothing on this BOM.

## Ruling 6: cadence measures the tree, and that stays, with one exemption ruled now

018(e) is filed as instance one of revisit condition 3 and the ruling said
three instances make a ruling. That condition was written for a STATISTICAL
question (is the bound wrong); this is a STRUCTURAL one (the reset-survival
file cannot land during the hazard it exists for), and it recurs on every
session that runs builders in parallel, which is now every session. Waiting
for two more instances of a fault whose mechanism is fully read is waiting
for the sake of a rule about a different kind of fault. Ruled now.

**The tree measure is CORRECT for the property that matters and is kept.**
Measuring the staged set instead (the resident's shape 1) would let a
459-line batch land as five 92-line commits, each under the bound; the tree
measure is what makes "splitting a batch cannot dodge review" true, and I
will not trade that for a docs commit. The resident's shape 2 changes no
bound and lands nothing.

**The ruling is shape 3: a commit whose staged set touches NO work prefix
is exempt from the line gate, and the exemption is printed with the tree
total beside it.** Concretely, for 018's builder:

- `director_cadence` reads the staged set (`git diff --cached --numstat`)
  through the same classifier. If zero staged paths classify as `work`, the
  gate prints `cadence exempt: this commit touches no work prefix
  (staged=N paths, all evidence/other); tree holds M pending work line(s)
  not in this commit` and passes. If any staged path is work, the gate is
  judged on the WHOLE tree exactly as today.
- The hole this opens is staging after verify: verify passes on a docs-only
  staged set, then work is staged, then commit. The `verify-gate.sh` hook
  compares mtimes and cannot see staging. So the commit-time check moves
  where the staged set is final: a `.githooks/pre-commit` (the directory
  holds only `commit-msg` today) that re-runs the classification over
  `--cached` and refuses when a work path is staged and no fresh ruling
  covers the tree. One idea, one implementation: the hook calls the same
  function, it does not grow a second parser.
- Fixtures, both outcomes: a docs-only staged set over a dirty work tree is
  ACCEPTED with the exemption line; the same tree with one work file staged
  is REFUSED on the tree total; a work file staged after a green verify is
  REFUSED by the hook.

This is 018(f). `production/` is not a work prefix and `STATUS.md` and the
agent log are evidence, so NOW.md lands under it by construction.

## Ruling 7: the agent log grows a completion event, as one instrument for three consumers, research first

The resident's measurement is right: two columns, every row a spawn, and
option 1 of 014 implemented as written goes silent for ever. This is the
attendance hole for the third time and it is worth one instrument.

**Ruled shape, and the first step is a measurement, not a build.** Claude
Code fires a `SubagentStop` event; nobody in this project has printed what
its payload carries. Step one of 024 is a hook that appends the raw payload
keys to a scratch file for one session and reports them. Building a parser
on an unread payload is the fault the whole rule set is about. Step two,
only after step one: the log gains a third column `event` with values
`start` and `stop`; every existing two-column row reads as `start` by
construction, so the parser in `director_cadence` accepts both widths and
nothing is migrated. Step three: the three consumers, in this order. (a)
L32's resume inflation: a `stop` row lets a resume be told from a fresh
spawn and the footer's `directorSpawns` stop over-counting. (b) The watchdog
dailies test, already ruled on 25 Aug to move to the artifact test. (c) The
stop hook: a `start` with no matching `stop` for the same agent type means a
builder is running, and the hook prints WHY it is quiet, as 014's closing
sentence demands.

Until 024 lands: the constitution wins, the resident holds, and the nag is a
named false positive. One more thing 014 gains: the stop hook lives at
`~/.claude/stop-hook-git-check.sh`, outside this repository, and no claim
about what it does can be checked from the tree. Its text is recorded in
`production/stop-hook.md` the way the watchdog prompt is, with the same
contract, before anyone teaches it to read anything.

## Ruling 8: dispatch tonight, one job, after the batch lands

**Dispatch `fetch-the-vignette-surfaces` tonight, after the batch is
committed and pushed, in its own commit.** Reasons, in order:

1. It is step 3's overnight run, the one the prep sequence says compounds
   everything after it, and it has been ready since `8dc54d3e` landed.
2. It is also the only instrument for the dormancy question the builder
   corrected: an idle watcher and a dead one are indistinguishable until a
   request exists. A request is the measurement.
3. It costs no Claude and no purchase: two CC0 zips, attributed by the same
   run, `--fetch` refusing if the plan does not resolve (fetch_vignette.py
   236 to 238) and exiting non-zero if it writes nothing (313 to 315).
4. The slot holds a job that completed; `tools/pc-request.py` verifies that
   against `pc-results` before writing and refuses otherwise.

Order: batch commit, push, then `python3 tools/pc-request.py
fetch-the-vignette-surfaces vignette-fetch-01`, commit `request.json` alone
(`game-design/` is outside the reviewed scope; no director row is moved).
Then one line to Jafar, because this is a deliverable he is waiting on and
it needs one click from him: the file is `START THE STUDIO MACHINE.bat` at
the top of the project, click it once, it fetches two surfaces and tells him
in a box whether it will start itself at sign-in. Nothing else.

**Do NOT dispatch `make-the-pictures`.** There is nothing to make (Ruling 5).

**What waits, and why.** The shutter pick by eye from fifteen previews is
the previous ruling's ladder rung and it needs `--probe`, which the TABLE
does not carry. `--fetch` tonight takes CorrugatedSteel002 at 4K as the
spec's `assets` entry names it, which the spec's own `route_after_check`
sentence says it deferred. The two sentences in that spec disagree; the code
follows the `assets` list. Acceptable tonight: the asphalt maps are wanted
regardless, the shutter surface is a placeholder under a logical name a
later fetch overwrites, and the probe row is one TABLE line in 023's next
touch of the watcher. Recorded so the next reader does not find a shutter on
disk and call the pick made.

## Ruling 9: queue changes, dictated

Moves to `done/`, each with a status line naming this file:

- **013** (the cut). Acceptance met: under 2000 words with the goal block
  intact and checked, nothing deleted, every destination verified to carry
  its passage, a director row.
- **016** (attribution). Acceptance met by reading: `.glb` in the set, the
  base-mesh row prints a line either way, the stray sweep sees `.glb`
  anywhere (fixture 10), and the shape fix outlives the list.
- **019** (step 4 scope). Ruled FOLD, Ruling 5.
- **011** (watchdog state). Closed by D1 and D2; the sentence's host moved
  and the correction sits beside it.

Amended in place:

- **014** gains Ruling 7's text as a section headed `RULED 2026-09-02`, and
  the `production/stop-hook.md` recording as its first step.
- **017** item 1 gains the Sky twin: `THIRD-PARTY.md` line 253 names
  `ledger/Assets/Sky/polyhaven/`; the files are under
  `ledger/Assets/Resources/Sky/polyhaven/` and the WATCHED row already says
  so. Same fault, same file, thirty lines apart.
- **018** gains (f) with Ruling 6's text.

New items, next free number 020:

- **020-casebook-pointers-and-decay.md** (infrastructure, instruments, one
  instrument-builder). Two checks in `verify.py`, one function. (a) Every
  path listed under CLAUDE.md's `## Where the rest of this file went` exists
  and carries at least one `moved verbatim from CLAUDE.md` marker; the count
  of markers per file is printed. (b) `docs-check.py` widens to walk
  `ledger-v2/studio-v2/casebook-*.md`, `operations.md`, `organization.md`,
  `runner.md` and `legacy/` for the STATUS-banner and verified-date rules,
  with the walked count printed beside the `game-design/` count, and the
  400-line cap NOT applied to a casebook (they are LOG-sized by design; say
  so in the code). Accepting case: the live tree. Rejecting: a pointer to a
  path with no marker.
- **021-session-start-hook-reads-the-superseded-queue.md** (infrastructure,
  governance, one instrument-builder, small). `.claude/settings.json` line
  32 passes `QUEUE_FILE=game-design/queue.md` and `session-start.sh` prints
  the first item under that file's `## Now`, which has been the SUPERSEDED
  block since 31 Aug. Every session opens by reading a retired queue head.
  Point it at `production/NOW.md`'s `## In flight` section instead, print
  the first five lines, and keep the "no file, first fix" branch. `.claude/`
  is a work prefix, so this rides the next reviewed batch.
- **022-attribution-generated-content-row.md** (infrastructure, instruments,
  one instrument-builder). Ruling 3's instance three. A WATCHED row for
  `ledger/Assets/StreamingAssets/Decals/generated` with a token that is not
  already in `THIRD-PARTY.md` (the model's name is the natural one), a
  `THIRD-PARTY.md` section per `content-sourcing.md` 4.6 (model, weights
  licence, training-data claim, review state, and the fact that fourteen
  images are `review=pending`), a fixture proving a generated PNG under the
  ambientCG row is refused without the section. And the mechanical form of
  tonight's hand audit as a printed reading, not a gate: for every watched
  directory row, list its immediate subdirectories that are neither a
  watched row themselves nor named in the row's machine-written manifest.
  Print first; gate from what it prints.
- **023-pc-watcher-second-instance-and-probe-row.md** (infrastructure,
  content pipeline, one engine-specialist). Ruling 4's `running` marker with
  the job's timeout as its staleness bound, both outcomes fixtured; a
  `probe-the-vignette-library` TABLE row running `fetch_vignette.py
  --probe` with a `JOB_TIMEOUT` entry and `tools/props/ambientcg-types.json`
  added to `publish`'s named list; and the spec's C10 sentences reconciled
  so the file says one thing about the shutter.
- **024-agent-log-completion-event.md** (infrastructure, governance, one
  instrument-builder, research first). Ruling 7's three steps in order.
  Step one is a measurement and is the whole first session.
- **025-step-4a-seven-images.md** (production, asset pipeline, one
  content-wrangler). For each of the seven 2D BOM lines decide, in the item
  itself with a one-line reason, deterministic (Pillow, `content-sourcing.md`
  Tier A) or diffusion (`prompts.json` schema 2 entry with seed, negatives
  and the rules clause). E10 and G7 wait on canon names and say so. The
  deliverable is the entries plus a tiny generator for the deterministic
  ones, then ONE `make-the-pictures` dispatch. Acceptance: seven files on
  disk, each attributed by the run that wrote it, none blank, review state
  recorded.

## Quality ladder

- **CLAUDE.md**: rung tonight, standing rules plus tested pointers at about
  1,989 words with the count in every footer. Next rung: the pointers and
  the casebooks under an instrument (020). The rung after: a session that
  breaks a rule and can be shown to have read it, which is the only test of
  whether a rule read is a rule held.
- **Attribution**: rung tonight, a classifier that names what it did not
  classify, with the live tree as its accepting case. Next rung: the
  generated-content row and the sub-source reading (022).
- **PC channel**: rung tonight, one click, jobs by name, a single-writer
  results branch, per-job timeouts, every flag re-read by the selftest. Next
  rung: its first real run, which Ruling 8 dispatches and which is the
  accepting case for everything this container cannot execute. After that,
  the second-instance guard and the probe row (023).

## Deliberately not decided

- Whether the 2000-word bound should move. It is Jafar's number; the count
  is printed on every run and a series will exist before anyone asks.
- A per-prefix cadence bound. Still waits on 018(d)'s printed row.
- The engine, the frame-time bound, the C4 route change: all unchanged
  from the previous rulings and all still waiting on the same evidence.
- Whether `.claude/rules/` should load a casebook conditionally the way it
  loads `instruments.md`. Tempting and unmeasured; it would reload ten
  thousand words on a trigger nobody has watched fire. Not from this chair.

## For the next session in one line each

- Land: the batch as staged in Ruling 1 with E1 to E6, D1 to D4, the queue
  changes, and this file; word count from the footer in the message.
- Dispatch: `fetch-the-vignette-surfaces` in its own commit after the push;
  one line to Jafar naming the `.bat`.
- Do not dispatch pictures; nothing is written to make.
- Spawn: one instrument-builder for 018 (a to f) and one for 020; both are
  `verify.py` touches and one may carry both if it stays inside a session.
- Update NOW.md: three builders landed, no director owed until the next
  trigger, the request waiting on one click.

Spawn row, quoted verbatim from `.claude/agent-log.tsv` (line 189):

    2026-09-02T00:02:48Z	studio-director

<!--RULING spawn=2026-09-02T00:02:48Z-->
