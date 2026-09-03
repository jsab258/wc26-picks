# Builder report — ref-bench low-content annotation, and `template_sync`

> **STATUS: LOG, 2026-08-24. NOT CURRENT** once superseded. An agent report
> is history the moment it is written. Not committed by the builder; the
> director reviews and commits.

Both items are the two builder tasks of
`game-design/decisions-2026-08-24-shadow-gap-and-template-sync.md` — decision 1
part 3 (a), and decision 2. Nothing here was committed or pushed.

---

## ITEM 1 — the low-content annotation in `tools/ref-bench.py`

### Where it lives

| what | where |
|---|---|
| the derivation, the series and the ladder, in prose | `tools/ref-bench.py:118` (THE LOW-CONTENT ANNOTATION) |
| `RATIO_DIMS` / `LOW_CONTENT_KEYS` — what is annotated and what qualifies it | `tools/ref-bench.py:342` |
| `_printed` / `below_floor` — one printed-value convention, shared with `outside_of` | `tools/ref-bench.py:700`, `:723` |
| `low_content_of` — the qualifying readings for one image | `tools/ref-bench.py:733` |
| `low_content_token` — the pair `groundMean:0.115<0.142` | `tools/ref-bench.py:755` |
| `ratio_band_reading` — in band X of Y readable, +Z unreadable | `tools/ref-bench.py:764` |
| `capped` — the truncation that announces itself | `tools/ref-bench.py:797` |
| table `~` mark (marks, never replaces the `!`) | `tools/ref-bench.py:928` |
| the RATIO ROWS summary block | `tools/ref-bench.py:958` |
| machine tail: `lowContent=` / `ratioUnreadable=` per image | `tools/ref-bench.py:1023` |
| machine tail: `refGap scope=ratioband` per ratio row | `tools/ref-bench.py:1035` |
| `low_content_series` — the printed series and the ladder, in `--series` | `tools/ref-bench.py:1181` |
| the selftest block, accepting fixture first | `tools/ref-bench.py:1424` |

### The threshold, and the series it came from

The threshold is not a number in the file. It is `min()` over the five
reference frames' own reading of each ground-band input statistic, recomputed
every run and printed on the REFBAND line, the `scope=ratioband` line and in
`--series`. Today, 24 Aug:

    groundP90   0.456 · 0.233 · 0.403 · 0.831 · 0.763     floor 0.233
    groundMean  0.293 · 0.142 · 0.216 · 0.536 · 0.543     floor 0.142

A sim still whose groundP90 **or** groundMean prints below the matching floor
has its ratio-derived rows marked `~` and counted apart. The sim series
(`--series`, "LOW-CONTENT QUALIFIER") over the seventeen stills:

    still                groundP90  groundMean  shadowRatio
    district_copper          0.878       0.626        0.201
    district_downtown        0.094       0.078        0.676   <- both below
    district_fairview        0.871       0.653        0.266
    district_gullwing        0.360       0.115        0.118   <- mean only
    district_hook            0.868       0.471        0.149   <- neither
    district_ironside        0.890       0.728        0.292
    district_strip           0.872       0.456        0.140   <- neither
    day1_dusk                0.318       0.140        0.049   <- mean only
    day1_night               0.260       0.157        0.136
    day1_noon                0.603       0.378        0.216
    day2_close               0.240       0.120        0.149   <- mean only
    day2_night               0.153       0.079        0.128   <- both
    day2_noon                0.832       0.631        0.269
    day2_wet                 0.199       0.095        0.099   <- both
    day5_night               0.082       0.048        0.192   <- both
    day5_noon                0.878       0.650        0.197
    street                   0.663       0.185        0.030

### EITHER, not BOTH — the ladder that decided it

One contributor toggled at a time, all four rungs printed from the same
measurement pass in the same run (`--series`, "THE LADDER"):

    groundP90 below floor    4 of 17   downtown day2_night day2_wet day5_night
    groundMean below floor   7 of 17   those four + gullwing day1_dusk day2_close
    either (TAKEN)           7 of 17
    both                     4 of 17

The three the mean catches alone are the argument, and the pictures were opened
before the rule was chosen (rule 4). `district_gullwing` is a dark building
mass at arm's length: groundP90 0.360 is a lit window sill, groundMean 0.115 is
the unlit facade filling the band — the AND rule calls that a readable street,
and the decision record already reads that frame as "a reading of a wall, not
of street shadow". `day1_dusk` and `day2_close` are likewise a black wall and a
close-up torso occupying the ground band.

The pair also answers rule 2's fork test before it is asked: **groundP90 and
groundMean are not one number twice.** Gullwing is the live proof that one can
sit above its floor while the other sits below.

### What it does NOT touch, on purpose

`district_hook` (groundP90 0.868 / groundMean 0.471) and `district_strip`
(0.872 / 0.456) are bright street frames reading below the band at 0.149 and
0.140. Neither is annotated. That shortfall is the residual the ambient-fill
ladder rung owns, and hiding it behind an outlier rule is what the ruling
refused. `district_hook` is the selftest's accepting fixture for exactly this.

### What the annotation changes in the numbers

    shadowRatio band 0.157..0.388:
      before   7 of 17 in band
      after    6 of 10 READABLE in band (+7 unreadable low-content, named)

    districts only (the reading the decision quoted):
      before   3 of 7 in band
      after    3 of 5 readable in band (+2 unreadable: downtown, gullwing)

**Confirms:** the decision's regime finding and its residual. Dry district
in-band count is unchanged at 3; hook 0.149 and strip 0.140 remain the named
residual and remain readable.

**Overturns, narrowly:** `day5_night` shadowRatio 0.192 was being counted as an
in-band reading in the naive 7-of-17. It is a near-black frame (groundP90
0.082, groundMean 0.048) whose ratio is two noise-floor numbers dividing each
other, and it now reads as unreadable rather than as a pass. The "before"
count is printed beside the "after" one in `--series` so this is checkable
rather than asserted.

**Also settled:** nothing may quote `district_downtown`'s 0.676 — the ruling's
"until (a) lands" clause is discharged; the row is now marked `~0.676!` on the
page and `ratioUnreadable=shadowRatio` in the machine tail.

### Rules honoured, concretely

* **Zeros ship denominators.** `readable`, `unreadableRatio`, `stills` and
  `inBand` travel on one line; `readable + unreadableRatio == stills` is
  asserted in the selftest. A run whose every still is low-content prints
  `in band NOTHING MEASURED — 0 of 0 readable stills` (planted fixture, since
  the live data cannot produce it).
* **Caps announce.** `capped()` emits `(+Nmore-not-shown)` past 8 names, in the
  machine line and `(+N more not shown)` in prose. Both directions tested.
* **No spaces in values.** `lowContent=groundMean:0.115<0.142` is one token
  carrying value AND the floor it failed — the paired reading, not two keys.
* **Same instant.** Every count comes from one measurement pass over the same
  ordered list the table and the tail are built from; whole-run counts sit on
  `scope=ratioband` and `scope=summary`, per-image ones on `image=` lines.
* **Key collision avoided.** The ratio-band line says `unreadableRatio=`, not
  `unreadable=`, because the summary line already spends `unreadable=` on
  images that would not decode.
* **The `~` marks, it does not replace.** The `!` (outside the band) stays, so
  the existing three-way agreement check (table flags / `outside=` / summary)
  still holds; the summary line now also states how many of the outside
  readings sit on a `~` row and are therefore not findings.

### Both-ways evidence

Accepting first, as shipped:

    ref-bench selftest: 78 passed, 0 failed

with, among the new ones:

    accepting: district_hook is NOT low-content (none)
    accepting: district_hook's own inputs are above both floors
               (groundP90 0.868>=0.233, groundMean 0.471>=0.142)
    accepting: district_hook's line says lowContent=none ratioUnreadable=none
    rejecting: district_downtown IS low-content
               (groundP90:0.094<0.233,groundMean:0.078<0.142)
    rejecting: district_downtown's line names the ratio row it marks
    rejecting: it is ANNOTATED, NOT DROPPED — the row still carries its value

Mutation-tested, because a selftest that cannot go red is decoration. Two
mutants, each run from the repo root so paths resolve as in a real run:

    MUTANT 1 — LOW_CONTENT_KEYS = ()   (the annotation never fires)
      FAILED rejecting: district_downtown IS low-content (none)
      FAILED rejecting: its qualifying number is printed with the floor it failed
      FAILED rejecting: district_downtown's line names the ratio row it marks
      FAILED floor: the qualifier moves when the references move — one value, two floors
      FAILED floor: EITHER input below its own floor qualifies (the gullwing shape)
      FAILED nothing measured: 0 readable stills reports 0 of 0 with every one named

    MUTANT 2 — AND instead of EITHER      76 passed, 2 failed
      FAILED floor: the qualifier moves when the references move
      FAILED floor: EITHER input below its own floor qualifies (the gullwing shape)

The second mutant is the interesting one: the rule choice itself is guarded, by
a planted fixture carrying gullwing's shape (0.360 / 0.115) rather than by
gullwing's live numbers, so a re-sited camera cannot break the check.

### Live output, for the record

    ~ = LOW-CONTENT frame: a ratio row whose ground-band inputs sit below the
        references' own floor. Marked, never dropped — the value stays on the
        page and may not be quoted.

    shadow contrast  0.157..0.388    0.201    ~0.676!     0.266    ~0.118!
    shadow contrast  0.157..0.388    0.149!    0.292      0.140!   ~0.049!

    RATIO ROWS (1 of 16 dimensions) — the low-content annotation, keyed to the
    five references' OWN floor: groundP90 0.233, groundMean 0.142.
      shadowRatio = groundP10/groundP90, band 0.157..0.388: in band 6 of 10
      readable stills (+7 unreadable low-content), 17 stills examined.
        unreadable: district_downtown district_gullwing day1_dusk day2_close
                    day2_night day2_wet day5_night

    refGap image=district_hook ... outside=groundP90,edgeMid,grainSigma,shadowRatio
      lowContent=none ratioUnreadable=none px=831960/156384/307516 patchWindows=330
    refGap image=district_downtown ... shadowRatio=0.676 outside=...,shadowRatio
      lowContent=groundP90:0.094<0.233,groundMean:0.078<0.142
      ratioUnreadable=shadowRatio px=831960/156384/307516 patchWindows=330
    refGap scope=ratioband dim=shadowRatio inputs=groundP10/groundP90
      band=0.157..0.388 inBand=6 readable=10 unreadableRatio=7 stills=17
      floor=groundP90:0.233/groundMean:0.142 namesShown=7 namesNotShown=0
      unreadableStills=district_downtown,district_gullwing,day1_dusk,day2_close,day2_night,day2_wet,day5_night

### Keys added

Per image: `lowContent`, `ratioUnreadable`.
Per ratio row (`refGap scope=ratioband`): `dim`, `inputs`, `band`, `inBand`,
`readable`, `unreadableRatio`, `stills`, `floor`, `namesShown`,
`namesNotShown`, `unreadableStills`.
On `scope=summary`: `ratioDims`, `lowContentStills`, `lowContentKeys`,
`unreadableRatioReadings`.

---

## ITEM 2 — `template_sync`

### Where it lives

| what | where |
|---|---|
| the check module | `tools/template-sync.py` (new, 470 lines) |
| section registry (the four process sections) | `tools/template-sync.py:76` |
| `sections_of` — structural anchors, spans, missing list | `tools/template-sync.py:99` |
| `fingerprint_of` — per-section + rolled digest | `tools/template-sync.py:140` |
| `evaluate` — the one reading, shared by check and every fixture | `tools/template-sync.py:181` |
| `marker_text_for` — what `--stamp` writes | `tools/template-sync.py:277` |
| selftest, accepting cases first | `tools/template-sync.py:363` |
| the marker | `.claude/template-sync.txt` (new, tracked path, not ignored) |
| the verify check | `ledger/verify.py:675` (`template_sync`) |
| registered in the run list | `ledger/verify.py:2184` |

### What it fingerprints, and how the boundaries are found

Four sections, per the ruling: THE STUDIO SPLIT, THE HYBRID RESIDENT,
REPORTING, AUTO MODE. An anchor is a **structural** line — a `##`..`####`
heading or a line-initial bold run — whose text begins with the section's
words, upper-cased so a template's `## The studio split` matches too. Prose
mentioning the same words cannot move a boundary (asserted both ways). A
section runs to the next anchor or the next `##` heading, whichever comes
first, so the four are disjoint and each prints its own span:

    THE-STUDIO-SPLIT       lines 978-1004 (27)  sha256=1429dac3024ce409
    THE-HYBRID-RESIDENT    lines 1005-1018 (14) sha256=8decaf70866fe164
    REPORTING              lines 1019-1032 (14) sha256=7ec1f012b19d9a86
    AUTO-MODE              lines 1033-1328 (296) sha256=4bf1ebc065c6ea3d
    sections=4/4 lines=351/1376

The `sections=4/4 lines=351/1376` pair rides on every line the tool prints,
green or red: a fingerprint over three sections looks exactly like one over
four, so the coverage is the denominator that makes the digest readable.

### It never reads the other repo

By construction — there is no path to `measured-studio-work` anywhere in the
tool. The template checkout exists in this container and not on the Windows
runner, and a check that means different things in different places is not a
check. The marker is the claim; the tool's job is to force the claim to be
made at the moment the sections change.

### The marker, stamped to the honest current state

    templateRepo=jsab258/game-studio
    state=deferred
    templateSha=none
    queueItem=template-sync-hybrid-resident
    stamped=2026-08-24
    sections=4
    section=key:THE-STUDIO-SPLIT/lines:27/sha256:1429dac3024ce409
    section=key:THE-HYBRID-RESIDENT/lines:14/sha256:8decaf70866fe164
    section=key:REPORTING/lines:14/sha256:7ec1f012b19d9a86
    section=key:AUTO-MODE/lines:296/sha256:4bf1ebc065c6ea3d
    fingerprint=fff4e7f99c58c564

**Why `deferred` and not `synced`, checked rather than assumed.** At stamp
time the template's committed HEAD is `1951af1` and
`git show HEAD:CLAUDE.md | grep -c -i hybrid` returns **0** — the hybrid
resident is not in the template's committed state. Its working tree carries an
in-flight `## The studio split — choose the variant` section (+70 lines,
uncommitted), which has no sha to record. So the only honest claim available
is a deferral with a named item, and `state=synced templateSha=none` is
refused by the tool for exactly this reason.

**One thing for the director.** The deferral names
`template-sync-hybrid-resident`, and no queue item of that name exists yet —
`game-design/queue.md` is outside this builder's file allowance. The tool does
NOT couple to queue.md (that would be a second subject and would have landed
red on a file I may not edit); instead the deferral is named in the verify
footer of **every** commit made while it stands:

    template sync DEFERRED (deferred to template-sync-hybrid-resident,
    4/4 sections, fingerprint fff4e7f99c58c564, 25 fixtures)

so it is visible in the commit feed rather than resting in a file nobody opens.
When the template's sync lands, re-stamp with
`python3 tools/template-sync.py --stamp --template-sha <sha>`.

### Exit codes, one per outcome

    0  in sync (including a properly named deferral)
    1  DRIFT — the sections changed since the marker was stamped
    2  usage
    3  NOTHING MEASURED — no CLAUDE.md, or a registered section has no anchor
    4  NOTHING RECORDED — no marker, unparsable, or a claim naming nothing

3 and 4 are deliberately different words as well as different codes: "the
instrument could not see its subject" and "nobody has ever made the claim" have
different next actions, and neither may read as clean.

### Both-ways evidence

    template-sync selftest: 25 passed, 0 failed

Accepting cases first, and the first of them is the **live** pair — the
repository is the fixture nobody can fake, because doing the work the tool asks
for (editing CLAUDE.md, re-stamping) changes the fixture rather than breaking
it:

    accepting: the live CLAUDE.md + live marker are IN SYNC
    accepting: every registered section has an anchor in the live file (4 of 4)
    accepting: every live section covers real lines
    accepting: a changed section against a RE-STAMPED marker is green
    accepting: state=deferred with a named queue item is green
    accepting: the deferral is NAMED in the summary, so a green run cannot hide it
    accepting: trailing whitespace does not drift
    accepting: the anchors are structural — prose mentioning the section names
               does not move a boundary
    accepting: no marker value carries a space

Rejecting cases, all synthetic except where the live file is the subject — the
"section that exists nowhere" fixture is a key **no file will ever contain**,
so doing the work can never break the tool:

    rejecting: a changed section against a stale marker is DRIFT
    rejecting: the drift names WHICH section moved
    rejecting: it does not accuse the sections that did not move
    rejecting: the discharge is stated in the failure message
    rejecting: a missing marker is NOTHING RECORDED, not clean
    rejecting: an unparsable marker (no fingerprint line) is the same
    rejecting: a registered section with no anchor is NOTHING MEASURED
    rejecting: NOTHING MEASURED reads differently from NOTHING RECORDED
    rejecting: state=deferred naming no queue item is refused
    rejecting: state=synced with templateSha=none is refused
    rejecting: no CLAUDE.md at all is NOTHING MEASURED
    exit codes: five outcomes, five distinct codes; only `ok` is 0

**The incident itself, replayed against the live file.** The exact drift Jafar
caught — resident said Fable where CLAUDE.md says the hybrid — re-run in
memory against the real CLAUDE.md and the real marker (no file was edited):

    exit=1
    template-sync: DRIFT — 1 of 4 process section(s) changed since the marker
    was stamped on 2026-08-24: THE-HYBRID-RESIDENT (now=7a2b9f1a121a3f8a
    marker=fff4e7f99c58c564, sections=4/4 lines=351/1376). DISCHARGE, one or
    the other: sync jsab258/game-studio now and re-stamp with `python3
    tools/template-sync.py --stamp --template-sha <sha>`, or defer with
    `--stamp --defer <queue-item>` naming a queue item.

**The verify wrapper's own red**, proven rather than assumed — marker moved
aside, wrapper run, marker restored:

    ok=False
    template-sync: NOTHING RECORDED — no legible marker at
    /home/user/wc26-picks/.claude/template-sync.txt, so nobody has ever claimed
    the template carries these sections (sections=4/4 lines=351/1376,
    fingerprint=fff4e7f99c58c564). Stamp it: ...

### One design note worth keeping

The verify wrapper runs **the check before the selftest**. The selftest's first
accepting fixture is the live pair, so a real drift fails it too — and
reporting a drift as "the checker is broken" would send the next session
reading the tool instead of the marker. Red for the tree first, red for the
instrument second; green needs both.

---

## The run

Five lints, all green with their denominators:

    lint-shadow      0 shadowed Core types (274 type(s), 87 Game file(s))
    lint-nested      0 nested-type errors (248 top-level Core types checked)
    lint-static      0 static/instance errors (75 instance members across 2
                     partial class(es), 522 static bodies walked)
    lint-filetype    0 filename-as-type error(s) (183 file(s) scanned, 448
                     type(s) declared, 13 filename(s) that are not types)
    lint-namespace   0 namespace-as-value error(s) (183 file(s) scanned, 4
                     namespace segment(s) in scope)
    verdict-emit-dupkeys  0 same-line duplicate key(s) (109 log call(s) across
                          177 file(s)); selftest ok (7 checks)

`python3 ledger/verify.py` — **GREEN**, `ledger/.verify-footer` written. The
two entries this work added or moved:

    template sync DEFERRED (deferred to template-sync-hybrid-resident,
      4/4 sections, fingerprint fff4e7f99c58c564, 25 fixtures)
    78 ref-bench checks (0 failed)

A first pass twenty minutes earlier was red on `reach FAILED — 1 unreached` and
`GAME LAYER DOES NOT COMPILE: Game/SimDirector.cs(10183,21): error CS0103: The
name 'TourVantage' does not exist in the current context`. Both were the other
builder's in-flight `SimDirector.cs` edit (the only C# diff in the tree, +199 /
-19) and both cleared on their next save; no file of theirs was touched here.

Files changed: `tools/ref-bench.py`, `tools/template-sync.py` (new),
`.claude/template-sync.txt` (new), `ledger/verify.py` (one new function plus
one name in the run list; nothing in the `director_cadence` region).
Not committed, not pushed.
