# DIRECTOR RULING: the widened director_cadence, the prop viewer, and the four scope questions (1 Sep 2026)

> **STATUS: LOG, 2026-09-01. NOT CURRENT once queue item 015 lands and the bound has been set from the printed series; from then the constants in ledger/verify.py, production/queue/015 and CLAUDE.md are the reading copies and this file is their history.**

The banner above carries the only em-dash in this document, because
`tools/docs-check.py` (lines 55, 65 and 90) hard-codes that character in
the regex it accepts. The instrument that enforces the banner contradicts
the formatting law it sits beside. That is a finding, named in Ruling 6,
and not a licence.

Fourth ruling of the day. Reviewed by reading the code, not the builder's
report: this role has no shell, so nothing below was executed by me and
every executed number is the resident's or the builder's, with my check
being that the code exists and asserts what the number claims.

## What was verified before ruling

- Read `ledger/verify.py` lines 2158 to 3410 (the constants, the
  classifier, the reader, the summary printers, the series printer), 3572
  to 4360 (the selftest through r19, the never-looser sweep, the partition
  sweep, the series-printer fixtures), 4586 to 4680 (the check's own
  docstring) and 5262 to 5331 (the CLI wiring). `--cadence-series` is
  reachable and exits 2 when the walk measured nothing.
- Confirmed by reading, not by the report: the series printer reads
  `_cadence_classify`, the same function the gate reads, so the series and
  the gated number cannot disagree about what work is. The reference
  pathspec is derived from the two constants, not restated; fixture a18
  asserts that derivation reached git for the one evidence path inside a
  work prefix. The non-zero median is the upper median of the sorted
  non-zero values, p90 is the value at index int(0.9 n), and the max is
  printed beside them; each is named for what it is.
- The builder's numbers are consistent with each other and with the code:
  14 of 60 and 28 of 120 over the bound are the same proportion; the
  docstring at line 4629 quotes the 120-commit reading (67 zeroes, median
  123, p90 1920, max 6188) and the brief quotes the 60-commit one. The
  live ladder (narrow 0, wide 2458) is the mechanism fixture r18 and
  r18_old assert, one tree, two scopes, one run. The brief's 2499 and the
  ladder's 2458 are two readings minutes apart of a tree still being
  edited; noted, not reconciled.
- Read all four prop viewer files in full: `propview.py` (863 lines),
  `blender/view_props.py` (390), `3 LOOK AT THE PROPS.bat` (236),
  `where-blender.ps1` (101). Checked the seams by name rather than trusting
  the summary: `probe-tools.ps1` takes `-Out` (line 21) and writes
  `blender`, `blender_version` and `notes` (lines 92, 93, 185), which are
  the three keys `where-blender.ps1` reads. `glb_stats` returns `verts`,
  `tris` and `dims_m` (meshgen.py 265 to 334), the keys propview reads.
  `clean_lod.py` exports `ensure_addon(module)` and `import_any(path)` and
  guards its main. `meshgen.py` is stdlib-only and guards its main, so
  importing it under Blender's Python has no side effect. Every flag the
  .bat passes is in `KNOWN_FLAGS`. `tools/lint-bat-editor.py`, which the
  .bat cites, exists. Zero em-dashes across `tools/meshgen/` (grep count 0)
  against 438 lines carrying one in `ledger/verify.py`.
- The premise: a viewer for props of a late-analog British port town,
  nothing bought, no account used, nothing written into the project. No
  conflict.
- `content/props/manifest.json` and `ATTRIBUTION.json` open with
  `"written": "2026-09-01T20:02:10Z"` and tool versions; both are written
  by `meshgen.py` (lines 1107, 1314, 1505) and published by its `Publisher`,
  which runs `git add -- <names>`, `git commit -m` and `git push` directly
  on Jafar's PC with no verify in the path (lines 1357 to 1389). So the
  runner's publish commits do not pass through this gate; they do, today,
  move its reference instant.
- `.claude/` holds agent definitions carrying `model:` (which the gate's
  own spend reading consumes), `settings.json` (permissions and hook
  wiring), three hooks, two rules files, the agent log (already evidence)
  and `template-sync.txt`, which is written by `tools/template-sync.py
  --stamp` and fingerprints CLAUDE.md's process sections.
- The stale sentence exists at exactly two sites in `CLAUDE.md` (lines 1110
  and 1195). Grepped every `.md` in the project for the claim; the other
  hits are the L27 finding (correct, it describes the old state as a
  fault) and unrelated lint reports.

## Ruling 1: the batch LANDS, with conditions that touch no code

The gate is right and its first red is the gate working. The prop viewer is
the best version of an untestable tool this container can produce: the
untested half is named in every file, the status-file pattern is reused
from `clean_lod`, the read-only promise has an instrument that reads tokens
rather than characters and is proven to fail on a planted write, and the
three endings of the .bat are three paragraphs rather than one. Nothing in
either piece weakens an instrument.

Conditions, all in the same reviewed commit, none of them a code change:

1. **CLAUDE.md corrected at both sites**, text dictated in Ruling 5.
2. **Expect `template_sync` to go red after that edit** and re-stamp it
   with the `--defer` form named in the header of `.claude/template-sync.txt`,
   against a one-line queue item "template sync: cadence scope correction".
   The fingerprint changing is the check doing its job; a refusal from the
   stamping tool is the next thing to read, not to work around.
3. **`production/queue/010-widen-director-cadence.md` moves to `done/`**
   with a status line naming this ruling, and **015's brief is widened** to
   the scope in the section "The scope of 015" below and its status changed
   from BLOCKED to READY.
4. **Stage by name**: `ledger/verify.py`, the four files under
   `tools/meshgen/` (never the `__pycache__` directories), the two queue
   files, `CLAUDE.md`, `.claude/template-sync.txt`, and this file.
5. **The commit message quotes both selftest counts from a run made after
   the CLAUDE.md edit**, never from the brief's 75 and 59.
6. **Commit before pulling.** Jafar's prop run may publish a manifest at any
   moment, and until 015 lands that commit moves the reference past my
   spawn row. If verify reports my row as older than the reference, a
   commit touching the scope landed after 21:46:44Z; the remedy is to
   RESUME this director for a fresh row and stamp, never to edit the stamp.

Nothing in `verify.py` or `tools/meshgen/` changes in this commit. Every
code consequence of Rulings 2 to 6 is folded into 015, which is the next
touch of `verify.py` and unblocks the moment this lands. One builder spawn
for all of it, not three.

## Ruling 2: the bound stays 100 and stays labelled INHERITED

Not set tonight, for two reasons that are both rule 2. First, the series in
front of me is over a classifier this ruling changes: its three largest
readings (6188, 4388, 1053) are the machine-written props files that Ruling
3 removes, so any number read off it is a bound on generated manifests.
Second, I have the summary and not the row. A bound comes from reading the
sorted series for a gap, the way 100 was read off the old series' gap
between 81 and 107; nobody has shown me the new row and I will not set a
number from a median.

**The revisit condition, precisely:** after 015 lands, the resident runs
`python3 ledger/verify.py --cadence-series 120` and pastes the RAW
`non-zero sorted:` line verbatim, with the zeroes count and the `biggest:`
line, into the brief of the next mandatory director spawn. The bound is set
in that ruling. Until then every printed line keeps saying the bound is
inherited, which is what stops it drifting unexamined.

Two things to look at in that row, named now so the next reading is not a
fresh derivation: whether a gap exists near the current bound as it did in
the old series, and whether `content/` commits (a 48-line dialogue bank is
several hundred JSON lines) sit systematically above `tools/` commits. If
they do, one bound over both is two populations under one number, and the
next rung is a per-prefix bound, not a compromise value.

## Ruling 3: the manifest and the attribution file are EVIDENCE

`content/props/manifest.json` and `content/props/ATTRIBUTION.json` are
written by a machine about a run: timestamp, tool versions, per-item
stages, derived licence rows. Nobody authors them, a director reading a
6,000-line JSON diff by eye catches nothing, and the instrument for what
they contain is meshgen's own licence gate and manifest accounting, which
print their denominators. They are the same class as the mesh reports and
CI's verdict, and the runner's publish commit is the same shape as CI
committing its own stills: a commit that cannot have changed anything
reviewed, invalidating a review.

Both become exact-path entries in `DIRECTOR_EVIDENCE`, label `propsout`,
reasons written beside them. `content/` stays a work prefix: the dialogue
bank and the brand bible under it are authored by agents and are exactly
what a director reviews. The classifier's accepting case for `content`
therefore moves from the manifest to `content/dialogue/pub-regular-v1.json`.

Two comments become false the moment this lands and are corrected in the
same edit: the paragraph above `DIRECTOR_EVIDENCE` saying only
`ledger/.verify-footer` sits inside a work prefix, and the docstring at
line 4629 quoting a series that counted these files. That docstring is
re-printed after the change, dated, and says what the reading excludes.

## Ruling 4: `.claude/` is work; plans and specs are not gated by volume

**`.claude/` comes IN**, one prefix, label `claude`, placed after
`.githooks/`. The hooks are process enforcement code, the same class as
`.githooks/`; `settings.json` is the permission surface and the hook
wiring; the agent definitions carry the `model:` line the gate's own spend
reading consumes, so a change to one changes what every footer reports.
`agent-log.tsv` stays evidence by the precedence already encoded, and
`template-sync.txt` joins it as an exact-path evidence entry, label
`templatesync`, because a tool writes it. The rules files ride along as
work rather than being carved out; they are loaded into every session and
shape behaviour the way hooks do, and a three-way split of one directory
is a constant nobody will keep right.

**Plans, specs and the respec stay OUT of the line gate.** `production/
specs`, `production/queue` and `ledger-v2/` reach the director by the
constitution's triggers, which are by KIND (queue refill, anything touching
premise or roadmap), not by volume. A 100-line bound was never measured
against prose, a queue refill of three items is over it, and a gate that
fires on every planning commit is the ratchet rule 5b names. What that
leaves unguarded is real and is named rather than folded in: a large
respec edit with no ruling. The instrument for that is a KIND gate, size
irrelevant, over the premise files, and it is queued as research first
(print how often those paths change) rather than built from this chair.

## Ruling 5: CLAUDE.md is corrected NOW, in this commit

Both sites. The old sentence is kept and the correction sits beside it,
which is the shape this file uses so an error cannot be re-derived. No
em-dash and no italic in the new text.

**Site 1.** Directly after the paragraph ending "so the commit feed shows
the cadence." (line 1114), insert this paragraph:

> **CORRECTED 1 Sep by director ruling (game-design/decision-2026-09-01-cadence-widening-and-propview-batch.md): the scope in the sentence above is stale and is kept so it cannot be re-derived.** Since 1 Sep the gate counts pending lines across a NAMED SET of work prefixes minus a NAMED EVIDENCE LIST, and the reference instant is the newest commit that touched that set. On 1 Sep the old scope printed `0 changed line(s) ... review not required` through a full day of tools, workflow, C++ and hook work with no director review, and its freshness test was comparing against a commit 6.7 days old. The 100-line bound is inherited from the old scope and every printed line says so until a series under the new scope has been read and ruled on. The list itself lives in `DIRECTOR_WORK` and `DIRECTOR_EVIDENCE` in `ledger/verify.py`; read those, not this paragraph, because a copied list decays and the constants are tested.

**Site 2.** In the bullet beginning "Every commit containing builder work
still needs a director row" (line 1193), after "forced a fresh Fable
spawn.", append:

> (Since 1 Sep the reference is the last commit that touched the REVIEWED SCOPE, a named set wider than `ledger/Assets/Scripts`. The mechanism is unchanged; the set moved. See the correction above.)

Applied by the resident under the one-line-correction clause: the text is
dictated, so there is nothing to judge, and CLAUDE.md is outside the
reviewed scope so it moves no reference.

## Ruling 6: the formatting law reaches instrument prose

The source says "no em-dashes, no italic text, anywhere"
(`ledger-v2/studio-v2/constitution.md` line 13). CLAUDE.md's copy narrows
that to "project documents", and CLAUDE.md's own first rule is that the
source wins when the two differ. So yes: a comment, a docstring and a
printed summary string are prose and the law reaches them. The two
builders in this one batch applied it two ways, which is why it needed
ruling: propview is clean and carries a guard; verify.py's new hunks match
a file that carries 438 of them.

**Application, in the resident's own framing, which I accept:** a yes means
a whole-file sweep and not a hunk sweep. So the verify.py hunks are NOT a
landing condition tonight. From this ruling on, three things hold:

1. **New files written from 31 Aug are clean, with a guard.** propview's
   section F is the model and is already the state of `tools/meshgen/`.
2. **Files that predate the law are swept WHOLE**, as no-logic commits
   whose only check is the selftest, under a named queue item. verify.py
   is first on that list because its strings ride into every commit
   message. While in that file, correct the comment at line 2770 claiming
   `git log -1 -- <pathspec>` walks first-parent history; it walks full
   history with path simplification.
3. **The guard for the rest is a lint** over the Python files under
   `tools/` and `ledger/` and everything under `.claude/`, shipping a
   named to-sweep list as its denominator ("N clean of M examined, K on
   the sweep list") so it is green today and the list can only shrink.
   Accepting case: the files already clean. Rejecting case: a planted
   character. And `tools/docs-check.py` is widened in the same item to
   accept a banner without the character, with every existing banner as
   the accepting fixture, so the next ruling does not have to carry one to
   pass.

Anything a builder adds to `verify.py` in 015 is written clean.

## The scope of 015 after this ruling

This ruling is the director review of record for 015 as scoped here. One
tier-3 instrument-builder spawn, do-not-commit standing, told the exact
functions and not to re-read the file:

- Wire `tools/meshgen/propview.py --selftest` and `tools/meshgen/meshgen.py
  --selftest` into `verify.py` as two check functions beside the existing
  lint calls. Each parses the printed "passed, failed" line; RED on any
  failure AND on the line being absent, which is "nothing measured", not a
  pass. Counts ride into the footer.
- `DIRECTOR_EVIDENCE` gains `content/props/manifest.json` and
  `content/props/ATTRIBUTION.json` (label `propsout`) and
  `.claude/template-sync.txt` (label `templatesync`), each with its reason.
- `DIRECTOR_WORK` gains `(".claude/", "claude", reason)` after `.githooks/`.
- Selftest: the classifier's ACCEPT line gains `.claude/hooks/session-start.sh`
  as `("work", "claude")` and swaps the manifest path for
  `content/dialogue/pub-regular-v1.json`; the REJECT-evidence line gains
  the three new paths; r18's literal `workByScope=` string gains
  `/claude:0`; the restore assertion's `len(DIRECTOR_WORK) == 7` becomes 8;
  the docstring's "seven prefixes" becomes eight. a17 covers every new
  evidence rule without an edit.
- The two comments named in Ruling 3 are corrected; the series numbers at
  line 4629 are re-printed after the change and dated.
- propview's assertion "the grid is roughly square (7x6)" is pinned to 37
  props and turns verify red the day the batch reaches 50. It becomes
  `cols == ceil(sqrt(n))` and `rows == ceil(n / cols)`. A fixture tied to
  a live file goes red when the project improves; the cadence selftest's
  own comment says so.
- Not one added line carries an em-dash.
- One commit. If the gate goes red on it for size, the next mandatory
  spawn folds it with the bound decision; it is not split to dodge that.

## Queue items named, next free numbers

- **Premise-touch kind gate** (research first): print, over the last 120
  commits, how often `ledger-v2/respec/`, `canon.md` and CLAUDE.md
  section 0 change and whether a ruling was fresh each time; decide the
  gate from that series. Not built from this ruling.
- **Formatting-law lint and sweep list**, per Ruling 6, including the
  docs-check banner regex and the verify.py whole-file sweep.
- **Template sync deferral** for the CLAUDE.md correction (condition 2).
- **Prop contact sheet**: the same grid propview computes, rendered
  headless by Blender to one PNG under `production/mesh-reports/` and sent
  by the same publisher. Today the only reader of the props is Jafar's
  screen; a committed frame is a channel this container can open (rule 4
  and rule 12), and it is the difference between the studio seeing its own
  output and hearing about it.

## Quality ladder

Neither piece is a ladder row: a player perceives neither, and Jafar
perceives the viewer only as a window that opens. The close question is
still asked. The gate's next rung is the measured bound (Ruling 2). The
viewer's next rung is its first double-click, which is the accepting case
for everything this container cannot run, and the rung after that is the
contact sheet above.

## Deliberately not decided

- The bound's value, and whether one bound fits `content/` and `tools/`.
  Both wait for the printed row.
- Whether `.claude/rules/` should sit outside the scope like CLAUDE.md
  does. Ruled in with the directory; revisit only if it produces a false
  red, with the instance quoted.
- The form of the docs-check banner regex. Queued, not designed here.
- The two residual holes the gate's own docstring names (a stamp naming a
  dead spawn; a resident authoring a decision file). Unchanged, and the
  procedural rule that a resident never stamps a ruling stands.

## For the next session in one line each

- Land: verify.py and the four viewer files as they stand, plus the
  dictated CLAUDE.md text, the template-sync re-stamp, 010 to done, 015
  widened, this file. Commit before pulling.
- Spawn: one instrument-builder for 015 as scoped above. No Fable spawn
  until 015 needs its review, and that review sets the bound.
- Print: `--cadence-series 120` after 015 lands; paste the raw row into the
  next director brief.
- Queue: the four items above, by name.

Spawn row, quoted verbatim from `.claude/agent-log.tsv` (line 180):

    2026-09-01T21:46:44Z	studio-director

<!--RULING spawn=2026-09-01T21:46:44Z-->
