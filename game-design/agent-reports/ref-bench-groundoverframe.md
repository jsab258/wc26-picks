# ref-bench: a ceiling, a synthetic rejecting fixture, and `groundOverFrame`

LOG — 25 Aug 2026. NOT CURRENT after the next landing.
Instrument-builder account. Every number below was produced in this session by
running the tool; nothing is quoted from the brief or from memory. File touched:
`tools/ref-bench.py` only (2089 lines, was 1668).

---

## 0. WHAT WAS RED, AND WHY THAT MATTERED MORE THAN THE THREE FAILURES

Before anything:

    $ python3 tools/ref-bench.py --selftest
    ref-bench selftest: 75 passed, 3 failed
      FAILED rejecting: district_downtown IS low-content (none)
      FAILED rejecting: its qualifying number is printed with the floor it failed
      FAILED rejecting: district_downtown's line names the ratio row it marks

`verify.py` gates on that selftest, so the whole commit gate was red — on a
build whose only relevant change was **fixing the frame the instrument was
complaining about**. The rejecting fixture was `district_downtown`, chosen
because it was near-black (meanLuma 0.096); the tour-camera re-site in 6137608
made it a lit street (0.412) and the fixture stopped having the property it was
picked for. That is the trap named in `.claude/rules/instruments.md`: doing the
work the instrument exists to prompt must never break the instrument.

---

## 1. THE THREE FIXES

### Fix 1 — the rejecting fixture is synthetic (`tools/ref-bench.py:1641`)

`district_downtown` is gone from the selftest entirely. The rejecting case is
now three images generated in the selftest and written to a temp SIMDIR, run
through the whole `report()` path, so the printed line is what is asserted and
not an internal call:

| fixture | what it is | must qualify | side |
|---|---|---|---|
| `district_synth_black.png` | uniform luma 5/255 | yes | floor |
| `district_synth_blown.png` | uniform luma 217/255 | yes | ceiling |
| `district_synth_mid.png` | 70/90/110 checker, mean 0.353 | **no** | — |

The third is the half that stops this becoming a validator nothing survives: a
rule that marks everything would pass a rejecting-only test. A named
PRECONDITION check runs first — the live references' bounds must lie inside the
synthetic extremes (0.020 < floor, ceiling < 0.851) — so if the reference set
ever moves far enough to invalidate the fixture, the failure says which
assumption broke instead of looking like the rule itself is wrong.

The ACCEPTING fixtures stay pinned to the live set, where the project's rules
put them, and the strongest one is structural rather than pictorial:

    accepting: no reference frame can qualify as low-content (5 of 5 clean)

That cannot be invalidated by any improvement, because the floor is `min()` and
the ceiling is `max()` over those same five frames. If a reference ever
qualifies, the qualifier has stopped being derived from them.

`district_hook` remains the live accepting fixture, and its check was rewritten
from a state assertion into an IMPLICATION — see §2, it is the same trap one
level down.

### Fix 2 — the ceiling half (`tools/ref-bench.py:463`, `:854`, `:866`)

`LOW_CONTENT_CEIL_KEYS = ("groundMean",)`, `above_ceiling()` mirroring
`below_floor()` on the PRINTED values, and `low_content_of()` returning
`(key, value, bound, side)` so the token carries which side fired:
`groundMean:0.726>0.543` beside the old `groundMean:0.132<0.142`.

### Fix 3 — `groundOverFrame` (`tools/ref-bench.py:483` in DIMS, `:758` in `measure`)

Ground-band mean luma ÷ whole-frame mean luma, one decode, both means from one
masked pass — same instant by construction. It sits in `DIMS` immediately after
`groundPatch`, so it appears in the table, in `refGap image=REFBAND`, in every
`refGap image=` line and in the `outside=` list with no separate plumbing.
`groundPatch`'s reading rule is written at `tools/ref-bench.py:593` and printed
in the report legend every run:

    READ GROUND PATCH WITH ground/frame: patch is std/mean, so an ADDITIVE lift
    lowers it and a multiplicative one cannot move it. A low patch means BLOWN
    OR FLAT until ground/frame says which.

---

## 2. THE CEILING: THE SERIES FIRST, THEN THE CHOICE

Rule 2 — the first version of a bound is a printer. The bound is not a number
here: it is `max()` over the five references, recomputed every run, printed on
the REFBAND line and on `refGap scope=ratioband ... ceiling=`.

The five references' own ground-band inputs, sorted, this run:

    groundP90    0.233 · 0.403 · 0.456 · 0.763 · 0.831    floor 0.233  ceiling 0.831
    groundMean   0.142 · 0.216 · 0.293 · 0.536 · 0.543    floor 0.142  ceiling 0.543

THE LADDER, one contributor at a time, all rungs from one pass in one run
(`--series` prints this every time):

    groundP90 below floor      4 of 17   day1_night day2_close day2_night day2_wet
    groundMean below floor     5 of 17   those four + day5_night
    floor either               5 of 17
    floor both                 4 of 17
    groundP90 above ceiling    9 of 17   all seven districts + day2_noon day5_noon
    groundMean above ceiling   7 of 17   those nine LESS district_hook, district_strip
    SHIPPED                   12 of 17   floor-either (5) + ceiling-mean (7)

**The choice: floor on EITHER key, ceiling on the MEAN ONLY.** Both halves are
decided by the same property of a percentile, pointing opposite ways, and both
have a live witness in the table above:

- FLOOR, either: `review_day5_night` has groundP90 **0.525** — one lit lamp —
  over a groundMean of **0.132**. A band that is black except for a fitting is
  not a readable street, and a P90-only floor passes it. (This witness is NEW.
  The docstring's old witness was `district_gullwing` at 0.360/0.115; the
  re-site moved that frame to 0.840/0.554 and the argument had to be re-pinned
  to a frame that still shows it — the same decay that took the rejecting
  fixture down, caught in the same read.)
- CEILING, mean only: `district_hook` (**0.868** / 0.471) and `district_strip`
  (**0.872** / 0.452) print P90s above the references' ceiling with means
  sitting mid-band, because they are genuine street frames carrying bright
  highlights. A symmetric ceiling annotates exactly the two frames whose
  below-band `shadowRatio` (0.149 and 0.140) the 24 Aug ruling requires to stay
  visible as the residual the ambient-fill rung owns. The tool prints that cost
  every run rather than leaving it in a comment:

      A groundP90 ceiling would ALSO take 2 still(s) the mean ceiling leaves
      readable: district_hook district_strip — the cost of the ceiling half
      being symmetric.

`district_ironside` — the frame that prompted this — is now annotated
`groundMean:0.726>0.543`. Its ground band is the emptiest in the set
(`groundPatch` 0.029 against a reference floor of 0.205) and it was sailing
through because the floor half is blind to a white sheet.

**The hook check is now an implication, not a state.** `district_hook`'s
groundP90 IS above the references' ceiling today (0.868 > 0.831), and the
queued ground-albedo work is trying to move that number. Asserting the state
would have re-created the trap of Fix 1 on the accepting side, so the assertion
is the RULE — a P90 over the ceiling must not annotate a frame on its own —
and the check text says which case it exercised this run.

---

## 3. `groundOverFrame`, AND THE ONE PLACE IT IS NOT ANNOTATED

What it is a statistic OF: a ratio of two MEANS of one image, per shot, on the
shot line. Not a peak, not a median, not cumulative.

Reference band measured through this code: **0.387..0.981** — every GTA
reference has ground DARKER than its own frame average. The artifact-reader's
own recomputation put it at 0.41..0.97; the band that ships is this tool's,
recomputed from the references every run, and the small offset is a different
crop/mask, not a disagreement about the shape. Our readings:

    daylight   gullwing 1.019  strip 1.052  hook 1.084  day1_noon 1.115
               ironside 1.218  fairview 1.281  copper 1.330  day5_noon 1.356
               downtown 1.374  day2_noon 1.403
    night/wet  day2_close 0.593  street 0.654  day2_night 0.679  day2_wet 0.816
               day1_night 0.831  day5_night 1.080  day1_dusk 1.018

Ten of ten daylight frames are physically inverted — ground brighter than the
scene it sits in, which no reference ever is. Exposure-independence is asserted
in the selftest by halving every pixel of a synthetic frame: `lumaMean` moves
0.426 → 0.213 and `groundOverFrame` holds at 0.551867 to six decimals.

**The row is NOT marked unreadable on the ceiling side, and that is deliberate
(`tools/ref-bench.py:441`, `:915`).** `RATIO_DIMS` now declares, per row, which
side of the qualifier makes it degenerate:

| row | unreadableOn | why |
|---|---|---|
| `shadowRatio` | floor + ceiling | p10/p90 tends to 1 from both ends — a black band and a blown flat one |
| `groundOverFrame` | floor only | on a dark frame it is nothing (`day5_night` 1.080 at groundMean 0.132 is a lamp over a black frame); on a BLOWN frame it is the finding (`ironside` 1.218) |

The first version marked every ratio row whenever any bound fired, which would
have suppressed the new row on exactly the seven frames it was added to
diagnose. `unreadableOn=` prints on every ratioband line so the asymmetry is
legible from the machine tail, not only from the docstring.

---

## 4. SELFTEST, BOTH WAYS, OUTPUT PASTED

ACCEPTING (the live reference set and the live stills, plus the structural and
planted cases), on the shipped file:

    $ python3 tools/ref-bench.py --selftest
    ref-bench selftest: 101 passed, 0 failed
    $ echo $?
    0

REJECTING — the guard was watched failing three ways. A selftest that only ever
prints "passed" has not been shown to have teeth, so each half was removed from
a COPY of the tool (in the scratchpad, run against the live fixtures) and the
selftest re-run:

    === MUTANT A: LOW_CONTENT_CEIL_KEYS = () (the ceiling half removed) ===
    ref-bench selftest: 94 passed, 7 failed
      FAILED rejecting: the blown frame IS low-content, on the CEILING side (none)
      FAILED rejecting: each qualifying number is printed WITH the bound it failed
      FAILED rejecting: the blown frame loses shadowRatio and KEEPS groundOverFrame — the row that says it is blown (none)
      FAILED rejecting: the summary counts the two halves apart (floor 1, ceiling 1 of 3)
      FAILED ceiling: the MEAN above its ceiling qualifies (the ironside shape: a blown white sheet)
      FAILED sides: the token carries < for a floor and > for a ceiling
      FAILED sides: a floor frame loses both ratio rows, a ceiling frame keeps groundOverFrame

    === MUTANT B: groundOverFrame unreadableOn = ("floor","ceiling") ===
    ref-bench selftest: 99 passed, 2 failed
      FAILED rejecting: the blown frame loses shadowRatio and KEEPS groundOverFrame — the row that says it is blown (groundOverFrame,shadowRatio)
      FAILED sides: a floor frame loses both ratio rows, a ceiling frame keeps groundOverFrame

    === MUTANT C: groundOverFrame computed as lumaMean/groundMean (sign flip) ===
    ref-bench selftest: 100 passed, 1 failed
      FAILED direction: a DARKER ground than its frame reads below 1 (1.812) and a brighter one above 1 (0.594)

Mutant A also shows the accepting half surviving the loss of the rejecting one
(94 still pass), which is what "accepting case first" is for.

`python3 ledger/verify.py` — **exit 0**, footer carries `101 ref-bench checks
(0 failed)`. Note the tree also held another builder's in-flight
`AssetLibrary.cs`/`SimDirector.cs` work (372 changed lines under Assets/Scripts
at the time of the run); verify was green WITH those present, and I touched
nothing of theirs.

---

## 5. THE FIRST REAL SERIES, AND WHAT IT OVERTURNS

Per-shot, from the shipped machine tail (`refGap image=`):

| shot | groundPatch | groundOverFrame | shadowRatio | lowContent | ratioUnreadable |
|---|---|---|---|---|---|
| district_copper | 0.132 | 1.330 | 0.194 | groundMean:0.624>0.543 | shadowRatio |
| district_downtown | 0.152 | 1.374 | 0.200 | groundMean:0.583>0.543 | shadowRatio |
| district_fairview | 0.105 | 1.281 | 0.270 | groundMean:0.655>0.543 | shadowRatio |
| district_gullwing | 0.172 | 1.019 | 0.197 | groundMean:0.554>0.543 | shadowRatio |
| district_hook | 0.273 | 1.084 | 0.149 | none | none |
| district_ironside | 0.029 | 1.218 | 0.294 | groundMean:0.726>0.543 | shadowRatio |
| district_strip | 0.256 | 1.052 | 0.140 | none | none |
| day1_dusk | 0.401 | 1.018 | 0.045 | none | none |
| day1_night | 0.089 | 0.831 | 0.089 | groundP90:0.220<0.233,groundMean:0.098<0.142 | groundOverFrame,shadowRatio |
| day1_noon | 0.157 | 1.115 | 0.235 | none | none |
| day2_close | 0.495 | 0.593 | 0.085 | groundP90:0.180<0.233,groundMean:0.079<0.142 | groundOverFrame,shadowRatio |
| day2_night | 0.154 | 0.679 | 0.190 | groundP90:0.172<0.233,groundMean:0.095<0.142 | groundOverFrame,shadowRatio |
| day2_noon | 0.085 | 1.403 | 0.259 | groundMean:0.627>0.543 | shadowRatio |
| day2_wet | 0.156 | 0.816 | 0.096 | groundP90:0.205<0.233,groundMean:0.098<0.142 | groundOverFrame,shadowRatio |
| day5_night | 0.470 | 1.080 | 0.036 | groundMean:0.132<0.142 | groundOverFrame,shadowRatio |
| day5_noon | 0.136 | 1.356 | 0.179 | groundMean:0.640>0.543 | shadowRatio |
| street | 0.353 | 0.654 | 0.023 | none | none |

**CONFIRMED.** The reader's §1 judgement — the ground is a MATERIAL fault, not
an exposure one — is now a row in the tool rather than a recomputation in a
report. Ten of ten daylight frames inverted, and the annotation's ceiling half
independently marks seven of them from a completely different statistic.

**CONFIRMED, with a number the tool did not have before.** The reader's §3
ruling that the decal work is mis-sequenced: `district_ironside` reads
`groundPatch` 0.029 (worst in the set) at `groundOverFrame` 1.218, which under
the printed reading rule is "blown", not "flat". Sizing decals off that number
today sizes them against albedo.

**OVERTURNED — and this one changes an existing conclusion.** The 24 Aug
decision record closed the dry-tour fork partly on "dry district median 0.201 is
in band, 3 of 7 in band" for `shadowRatio`. With the ceiling half in, that
counting is no longer available: `--series` prints the before/after directly.

    shadowRatio band 0.157..0.388: before 9 of 17 in band; after 1 of 5 READABLE
    in band (+12 unreadable)

Every district that counted as "in band" (copper 0.194, downtown 0.200,
fairview 0.270, gullwing 0.197, ironside 0.294) is a frame whose ground band is
brighter than any reference ground — a p10/p90 over a flat pale sheet. The two
districts that remain READABLE are `district_hook` (0.149) and `district_strip`
(0.140), and both are still BELOW the band, which is exactly the residual the
ruling housed in the ambient-fill rung. So the ruling's residual survives
intact and its supporting "in band" count does not: on today's stills the
shadow question has **two readable district frames, both out of band**, not
seven frames with three in.

---

## 6. KEY NAMES ADDED (machine tail)

Per image (`refGap image=`): `groundOverFrame=` (also on `refGap
image=REFBAND` as `lo..hi`, and it may appear in `outside=`). `lowContent=`
tokens can now carry `>` as well as `<`. `ratioUnreadable=` is now per-frame
rather than all-rows-or-none.

Per ratio row (`refGap scope=ratioband`): `unreadableOn=`, `ceiling=`, plus a
second line because there are now two ratio rows (`dim=groundOverFrame`,
`dim=shadowRatio`).

Whole run (`refGap scope=summary`): `lowContentFloorStills=`,
`lowContentCeilStills=`, `lowContentFloorKeys=`, `lowContentCeilKeys=`
(replacing `lowContentKeys=`). Counting the two halves apart matters:
`lowContentStills=12/17` alone hides that 5 are black and 7 are blown, and
those have opposite fixes. Every value is space-free; `/` and `..` carry the
structure.

---

## 7. THE TWIN SWEEP — the same trap in other tools

Rule 1's third corollary: the moment a fix works, grep for the same fault
elsewhere. I read the rejecting case of every tool in the repo that ships a
selftest (23 files) and classified how each one is pinned.

**Safe, and most of them are:** `decal-ink`, `frame-drift`, `template-sync`,
`verdict-read`, `verdict-dupkeys`, `verdict-emit-dupkeys`, `gate-detail`,
`pc-watcher`, `body-proportions`, `sheet-read` build their rejecting input
synthetically or from a real SHAPE embedded as a string literal in the tool
itself. `lint-conditional-reach` mutates a copy of live code, which is the
right version of "the real error put back". `prop-reach:207` already documents
this exact trap and its fix (a key that is on no disk anywhere), and
`attribution-check:29` pins to `tools/mixamo-pick/known-bad`, a set held OUT of
the build precisely so the screen always has something to refuse — a real
fixture that improving the game cannot reach. That is the pattern to copy.

**TWO FINDINGS, both in files I do not own — for the queue, not edited by me.**
Both tools are gated by `verify.py`, so both would turn the commit gate red for
work having been DONE:

1. **`tools/clip-motion.py:439` — the rejecting case is `Joe.fbx` and it
   asserts the asset has NO animation take.** `body = os.path.join(CHARACTERS,
   "Joe.fbx")`, then `elif not r["frozen"]: failures.append("a rig with no take
   was measured as a moving clip")`. Re-export or re-fetch that body with a
   take baked in — ordinary Mixamo work in this project — and the selftest
   fails, reporting the opposite of what happened. Repair, by analogy with what
   shipped here: build the rejecting FBX (or assert the frozen rule against a
   synthetic two-key rig), or pin it to a body deliberately kept take-less the
   way `known-bad` is kept.
2. **`tools/prop-dimensions.py:337` — the rejecting case is `police.fbx` and it
   asserts a property of that mesh's authoring.** It re-runs the old pooled
   reader on the live car-kit file and requires `pooled < -1`. Swap the car kit
   for one whose parts are authored in place — a live item on the visual ladder
   — and the rejecting case evaporates while the bug it guards against is
   unchanged. Lower probability than (1), same shape.

Neither is urgent; both are cheap, and both are the kind of red that costs an
hour of reading correct code before anyone suspects the fixture.

---

## 8. WHAT I DID NOT TOUCH

`AssetLibrary.cs`, `SimDirector.cs`, anything in `game-design/` except this
report, the decision records, and the two tools named in §7. Nothing was
committed or pushed; the tree is left dirty for the director's review.

## 9. WHAT THIS INSTRUMENT STILL CANNOT DO

`groundOverFrame` says the ground is brighter than its scene. It cannot say
whether the cause is `TextureGrade`, the ambient term or the sun intensity —
that separation needs the ladder the ground-albedo builder is landing, one
contributor toggled at a time in one run. And it is still a steering proxy: a
frame can sit in band and look wrong. The judge is a person with the frames
side by side.
