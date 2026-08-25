# Unpinning two rejecting fixtures from live project assets

**LOG — 25 Aug 2026. NOT CURRENT after the work below is committed.**
Agent: instrument-builder. Base commit `80a91049`. **Not committed** — the
director reviews and commits.

Files changed, and only these two:

- `/home/user/wc26-picks/tools/clip-motion.py`
- `/home/user/wc26-picks/tools/prop-dimensions.py`

---

## 1. The rule, and the incident that priced it

`.claude/rules/instruments.md`:

> **Selftest ships with the tool, accepting case first.** For tools that
> check the project itself, the live codebase is the accepting fixture, and
> the rejecting fixture is SYNTHETIC (a key that exists nowhere), so doing
> the work the tool prompts can never break the tool.

`tools/ref-bench.py` broke this and paid for it yesterday: its low-content
rejecting fixture was pinned to `district_downtown`, and when that camera was
improved the selftest went red. It read as *the tool broke*. It meant *the
project improved*. `ref-bench.py:231` now carries the repair in prose —
"THE REJECTING FIXTURE IS SYNTHETIC, AND THAT IS THE POINT ... the work it
exists to prompt must never break the instrument."

Two more sites had the same shape. Both are fixed here.

---

## 2. Site 1 — `tools/clip-motion.py`

### What it was (at `80a91049`, lines 425-443)

```python
    # REJECTING: a body model carries a rig and no take, and it must not
    # come back looking like a healthy clip. ...
    # Written that way round on purpose, because the frozen rule is what
    # this file's whole finding rests on and pointing it at a body with
    # no animation is the one input we know the answer for.
    body = os.path.join(CHARACTERS, "Joe.fbx")
    if os.path.isfile(body):
        r = measure(body)
        ...
        elif not r["frozen"]:
            failures.append("a rig with no take was measured as a moving clip")
```

`Characters/Joe.fbx` is a live cast body. Measured before touching it, so the
claim is checked rather than remembered:

```
Joe.fbx parse+measure -> 2 keys, frozen= True
```

True today. **Not a property of the tool.** Baking a Mixamo take onto Joe is
ordinary work here — we fetch takes constantly — and the moment anyone does,
this selftest prints *"a rig with no take was measured as a moving clip"*: a
sentence about a tool bug, describing a project improvement. Exactly
ref-bench's failure, one asset over.

The defending comment ("pointing it at a body with no animation is the one
input we know the answer for") was **true when written and false now**, so it
was rewritten rather than left — rule 1's second corollary.

### What it is now

**`measure(path)` split into `measure(path)` + `measure_tree(root)`**
(`tools/clip-motion.py:190`). `measure(path)` keeps its exact signature —
`tools/mixamo-pick/pick_animations.py` calls it three times via `_CM.measure`
and is unchanged. One implementation of the measurement; the path version is
now four lines of parse-then-delegate.

**`synthetic_rig(moved_cm, turned_deg, keys, hip_cm, fps)`**
(`tools/clip-motion.py:~455`) builds a Mixamo-shaped FBX **tree** — a
`mixamorig:Hips` Model with no Model parent, one `AnimationCurveNode` per
animated property, one `AnimationCurve` per axis, and the `OP` connection
records that tie them together. The same shape `_index` and `_channels` walk
in a real clip. Nothing on disk; nothing anyone can fix.

**Which layer this exercises, and which it does not — stated in the
docstring, because a fixture that bypasses a layer cannot catch a regression
in it.** The tree goes to `measure_tree`, so the fixture covers the object
index, the root-parenting refusal, the channel walk, the unit scale and every
bound. It does **not** cover `BP.parse_fbx`, the byte reader, because it never
produces bytes. That layer's accepting fixture is the 64 real Kaydara files
parsed a few lines above — a better fixture for a parser than anything written
here, and a parser regression fails *there*.

**It is a ladder of two rungs, one contributor toggled**, printed from the
same vantage in the same run:

| rung | movedCm | turnedDeg | keys | must read |
|---|---|---|---|---|
| rest, no take | 0.00 | 0.0 | 2 | `frozen=True` |
| with a take | 40.00 | 25.0 | 31 | `frozen=False` |

One rung alone says nothing. A `frozen` flag wired to `True` passes a
rest-only fixture and turns all 64 clips into findings; wired to `False` it
passes a take-only fixture and makes the tool's whole finding unreachable.
The bounds (`FROZEN_CM=1.0`, `FROZEN_DEG=2.0`) sit *between* the rungs, so
both are pinned by the pair — demonstrated as break 3 below.

### The accepting case did not move

Still the live harvest: 64 clips must parse, each 0.2-60s, ≥2 keys, ≤30m
travel. Correct, and the best fixture available.

### Denominators and the synthetic announcement

Both outcomes now carry the full denominator, with the synthetic count kept
**separate** from the real one — 2 of these inputs are ones this file wrote,
and they are not evidence about the harvest:

```
SELFTEST PASSED -- 64 clips read, 0 declined, 2 synthetic rigs, rejecting case held
SELFTEST FAILED -- 1 failure(s) over 64 clips read, 0 declined, 2 synthetic rigs
```

and every fixture line says what it is, on pass and on fail:

```
  SYNTHETIC FIXTURE (built here, no project asset): rest-pose, no take    0.00cm   0.0 deg   2 keys  frozen=True
```

---

## 3. Site 2 — `tools/prop-dimensions.py`

### What it was (at `80a91049`, lines 336-346)

```python
    # REJECTING CASE — the old reader, run again on the same file.
    root, _ = _bp.parse_fbx(os.path.join(CAR_KIT, "police.fbx"), max_array=VERT_CAP)
    pooled = float("inf")
    for geom in root.find("Objects").find_all("Geometry"):
        ...
    check(pooled < -1,
          "REJECTING CASE — pooling the parts unplaced buries the car", ...)
```

It asserts that **a real shipped asset still reproduces the bug.** Re-export
`police.fbx`, or replace it with a pre-placed variant, and the selftest goes
red for the asset having been *fixed*.

### What it is now

**`synthetic_car()`** (`tools/prop-dimensions.py:~345`) builds the tree
itself: one body and four wheels, each mesh about its own origin, each placed
by its Model's `Lcl Translation`, connected by `OO` records. Straight into
`assemble()`, which is where the bug was.

**The part table was read off the real kit, not invented** —
`python3 tools/prop-dimensions.py --parts police` prints:

```
  wheel-back-left   x  30.0..60.0   y   0.0..60.0   z -111.0..-51.0
  body              x -75.0..75.0   y  20.0..130.0  z -155.0..135.0
```

so police's wheels are geometry `-30..+30` hung at y=30 and its body is
geometry `0..110` hung at y=20. `_SYNTH_PARTS` reproduces the bug **at the
size it really had**, which is why the rejecting rung still reads exactly
`-30.0` — the number the old table used to print.

**Which layer this exercises, and which it does not** — again stated: the OO
connection walk, the translation lookup and the per-part boxes, and **not**
`_bp.parse_fbx`, whose accepting fixture is the 25 real car-kit FBX parsed
from disk in the same run.

**A ladder of three lines off one tree**, and the third one is the important
one:

```
  ok   SYNTHETIC LADDER, rung 1 — placed, the fixture's tyres touch the road — 5 parts, floor 0.0, wanted 0.0
  ok   SYNTHETIC LADDER, rung 2 — REJECTING: pooled unplaced, it buries the car — pooled floor -30.0, wanted -30.0 — the number the table used to print
  ok   SYNTHETIC LADDER — and the two rungs stand apart, so the fixture still reproduces the bug — pooled/placed -30.0/0.0, separation 30.0 (needs > 1.0)
```

### The third line exists because break-testing found the first two were nearly tautologies

`SYNTH_FLOOR` and `SYNTH_POOLED` are **derived** from `_SYNTH_PARTS` rather
than typed twice — which is right (one implementation per idea) and has a
sting: *an expected value derived from the fixture moves with the fixture.*
Edit the fixture and both rungs keep passing while measuring nothing.

Found by running break B below, not by reasoning about it: a fixture
"improved" to hold pre-placed parts passed **both** rungs and had stopped
reproducing the bug entirely. That is the ref-bench fault wearing a fixture's
clothes, and it would have shipped.

The separation check is the repair, and it is a **paired reading** —
`pooled/placed -30.0/0.0` in one entry, with the separation beside it, rather
than two keys whose relationship a reader has to hold in their head.

### Denominators, caps, and one thing the pass line could not say

`check()` printed its measured value **only when red**, so every green line
read `ok` with no number under it. "the car kit is on disk to measure against"
is a different claim over 25 models and over 1, and the line could not tell
them apart — rule 3b, on a pass line. `check()` now prints `got` on both
outcomes, and the values that were bare name-lists carry their denominator:

| line | was | now |
|---|---|---|
| kit on disk | `ok   the car kit is on disk to measure against` | `— 25 models walked` |
| unplaced | `ok   every vehicle yields placed geometry` | `— 0 of 25 unplaced: none` |
| rotated | `ok   and none of them uses a rotation or a scale` | `— 0 of 25 rotated or scaled: none` |
| floors | `.. floors: ambulance=0 ... kart-oodi=0 ...` | `.. floors, 25 measured: ... (+17 more not shown)` |
| accepting | `ok   ACCEPTING CASE ...` | `— worst of 25 is van, 0.00 off the road` |
| squash | `ok   no kit model is squashed past half ...` | `— worst of 5 kinds is truck at 0.61` |
| footer | `prop-dimensions selftest ok` | `— 25 kit vehicles measured, 5 kinds squash-checked, 1 synthetic car (built here, no asset)` |

The floors line's ` ...` was a cap that did not say it bit — the `head -3`
fault in a filter's clothing. It now says `(+17 more not shown)` and prints
its denominator first. Both `worst of` lines default to the words
`nothing measured` when the set is empty, so a never-ran cannot read as clean.

The synthetic input is counted **apart** from the real ones in the footer for
the same reason as clip-motion's: 1 of these inputs is one this file wrote.

`_capped()` was added rather than a fourth inline `[:4]`.

---

## 4. BOTH WAYS — every run pasted

Rule 5b: a guard has two outcomes and shipping it means having watched both.
Every break was applied to the code **under test**, run, and reverted; the
revert was confirmed by `diff` against a pristine copy each time, and
`grep -rn "DELIBERATE BREAK" tools/ ledger/` returns nothing.

### 4.1 clip-motion — ACCEPTING (today's code)

```
64 clips read, 0 declined
no two clips share content
FROZEN ROOT — the hips neither move nor turn across the whole
clip, so the body is animated from the waist up:
    block_end      Standing Block End           0.67cm 1.8° over 3.80s
    lean           Leaning                      0.54cm 0.5° over 2.50s
    still by definition, not counted: lie_still    Laying Idle              0.36cm 0.6° over 12.50s
clipFindings=2 duplicates=0 frozen=2 stillByDesign=1 clipsRead=64

  SYNTHETIC FIXTURE (built here, no project asset): rest-pose, no take    0.00cm   0.0 deg   2 keys  frozen=True
  SYNTHETIC FIXTURE (built here, no project asset): with a take          40.00cm  25.0 deg  31 keys  frozen=False
SELFTEST PASSED -- 64 clips read, 0 declined, 2 synthetic rigs, rejecting case held
EXIT=0
```

### 4.2 clip-motion — BREAK 1: `rng` returns a maximum instead of a range

`return (max(v) - min(v)) * factor` → `return max(v) * factor`

```
64 clips read, 0 declined
no two clips share content
no frozen roots in 64 clips
clipFindings=0 duplicates=0 frozen=0 stillByDesign=0 clipsRead=64

  SYNTHETIC FIXTURE (built here, no project asset): rest-pose, no take  100.00cm   0.0 deg   2 keys  frozen=False
  SYNTHETIC FIXTURE (built here, no project asset): with a take         100.00cm  25.0 deg  31 keys  frozen=False
  FAIL: a synthetic rig with no take was measured as a moving clip (100.00cm 0.0 deg)
SELFTEST FAILED -- 1 failure(s) over 64 clips read, 0 declined, 2 synthetic rigs
EXIT=1
```

Note `clipFindings=0` — the tool's entire finding vanished and the report
read **clean**. Nothing in the accepting case noticed. The rest rung is what
caught it.

### 4.3 clip-motion — BREAK 2: the frozen flag can no longer say no

`"frozen": moved_cm < FROZEN_CM and turned_deg < FROZEN_DEG` → `"frozen": True`

```
clipFindings=63 duplicates=0 frozen=63 stillByDesign=1 clipsRead=64

  SYNTHETIC FIXTURE (built here, no project asset): rest-pose, no take    0.00cm   0.0 deg   2 keys  frozen=True
  SYNTHETIC FIXTURE (built here, no project asset): with a take          40.00cm  25.0 deg  31 keys  frozen=True
  FAIL: a synthetic rig that travels 40.00cm and turns 25.0 deg was measured as frozen -- the frozen rule cannot say no
SELFTEST FAILED -- 1 failure(s) over 64 clips read, 0 declined, 2 synthetic rigs
EXIT=1
```

### 4.4 clip-motion — BREAK 3: the bounds loosened to swallow everything

`FROZEN_CM = 1.0 / FROZEN_DEG = 2.0` → `100.0 / 100.0` (rule 2's forbidden move)

```
  SYNTHETIC FIXTURE (built here, no project asset): rest-pose, no take    0.00cm   0.0 deg   2 keys  frozen=True
  SYNTHETIC FIXTURE (built here, no project asset): with a take          40.00cm  25.0 deg  31 keys  frozen=True
  FAIL: a synthetic rig that travels 40.00cm and turns 25.0 deg was measured as frozen -- the frozen rule cannot say no
SELFTEST FAILED -- 1 failure(s) over 64 clips read, 0 declined, 2 synthetic rigs
```

The ladder pins the **bounds**, not merely the flag. The old Joe.fbx fixture
(0.00cm / 0.0deg) could not have caught this: it sits under any bound.

### 4.5 prop-dimensions — ACCEPTING (today's code)

```
  ok   the car kit is on disk to measure against — 25 models walked
  ok   every vehicle yields placed geometry — 0 of 25 unplaced: none
  ok   and none of them uses a rotation or a scale — 0 of 25 rotated or scaled: none
  .. floors, 25 measured: ambulance=0 delivery-flat=0 delivery=0 firetruck=0 garbage-truck=0 hatchback-sports=0 kart-oobi=0 kart-oodi=0 (+17 more not shown)
  ok   ACCEPTING CASE — every vehicle's wheels touch the road (y=0) — worst of 25 is van, 0.00 off the road
  ok   SYNTHETIC LADDER, rung 1 — placed, the fixture's tyres touch the road — 5 parts, floor 0.0, wanted 0.0
  ok   SYNTHETIC LADDER, rung 2 — REJECTING: pooled unplaced, it buries the car — pooled floor -30.0, wanted -30.0 — the number the table used to print
  ok   SYNTHETIC LADDER — and the two rungs stand apart, so the fixture still reproduces the bug — pooled/placed -30.0/0.0, separation 30.0 (needs > 1.0)
  ok   the kind table parses out of Core/Traffic.cs — 7 kinds read
  ok   and the kit mapping out of Game/TrafficHost.cs — 7 kinds mapped
  .. bike: first candidate oga_vehicles_bicycle ships as .obj — not measurable here
  .. bus: first candidate oga_vehicles_bus ships as .obj — not measurable here
  .. squash (1.00 keeps the kit's own proportions): car=0.73/0.70 police=0.72/0.70 taxi=0.75/0.67 truck=0.61/0.87 van=0.68/0.87
  ok   no kit model is squashed past half to fit its kind — worst of 5 kinds is truck at 0.61
  ok   the vertex cap is lifted, so a model reads whole — 1430 verts
  ok   and it has a size — (150.0, 130.00000268220901, 309.9999688565731)

prop-dimensions selftest ok — 25 kit vehicles measured, 5 kinds squash-checked, 1 synthetic car (built here, no asset)
EXIT=0
```

### 4.6 prop-dimensions — BREAK A: `assemble` stops applying the placement

`off[a] += t[a]` → `off[a] += 0.0` — the historical pooling bug, restored.

```
  ok   the car kit is on disk to measure against — 25 models walked
  ok   every vehicle yields placed geometry — 0 of 25 unplaced: none
  ok   and none of them uses a rotation or a scale — 0 of 25 rotated or scaled: none
  .. floors, 25 measured: ambulance=-30 delivery-flat=-30 delivery=-100 firetruck=-30 garbage-truck=-30 hatchback-sports=-30 kart-oobi=-21 kart-oodi=-21 (+17 more not shown)
  FAIL ACCEPTING CASE — every vehicle's wheels touch the road (y=0) — worst of 25 is delivery, 100.00 off the road
  FAIL SYNTHETIC LADDER, rung 1 — placed, the fixture's tyres touch the road — 5 parts, floor -30.0, wanted 0.0
  ok   SYNTHETIC LADDER, rung 2 — REJECTING: pooled unplaced, it buries the car — pooled floor -30.0, wanted -30.0 — the number the table used to print
  ok   the kind table parses out of Core/Traffic.cs — 7 kinds read
prop-dimensions selftest 2 problem(s) — 25 kit vehicles measured, 5 kinds squash-checked, 1 synthetic car (built here, no asset)
```

The signature of the historical bug is exactly what the ladder prints:
**rung 1 collapses onto rung 2** — placed and pooled both read `-30.0`.

### 4.7 prop-dimensions — BREAK B: the fixture stops discriminating

All five `_SYNTH_PARTS` rewritten as pre-placed geometry with zero
translation — i.e. somebody "improves" the fixture and it no longer
reproduces the bug at all.

**First attempt (one wheel only) was NOT caught** — the other three wheels
still held the `-30`, and both rungs stayed green. That near-miss is what
prompted the separation check. With all five parts pre-placed:

```
  ok   SYNTHETIC LADDER, rung 1 — placed, the fixture's tyres touch the road — 5 parts, floor 0.0, wanted 0.0
  ok   SYNTHETIC LADDER, rung 2 — REJECTING: pooled unplaced, it buries the car — pooled floor 0.0, wanted 0.0 — the number the table used to print
  FAIL SYNTHETIC LADDER — and the two rungs stand apart, so the fixture still reproduces the bug — pooled/placed 0.0/0.0, separation 0.0 (needs > 1.0)
prop-dimensions selftest 1 problem(s) — 25 kit vehicles measured, 5 kinds squash-checked, 1 synthetic car (built here, no asset)
```

Both derived rungs pass and the fixture is measuring nothing. Only the
separation says so.

---

## 5. `ledger/verify.py`

Run at the end. **The suite is RED, for two reasons that are not mine** —
another batch is live in the tree (`AssetLibrary.cs`, `SimDirector.cs`,
`WorldBuilder.cs`, `verify.py`, the core-tests workflow, and two untracked
shell tools, none of them touched by this work):

```
DIRECTOR NOT SPAWNED: 525 changed line(s) (525 tracked + 0 untracked in 0 new file(s))
vs 100 threshold under Assets/Scripts, 0 director row(s) since HEAD ...
UNTRACKED/ABSENT TOOL(S): tools/ci-checks.sh(untracked), tools/reach-check.sh(untracked)
```

Neither can be caused by a change under `tools/*.py` — the cadence gate counts
lines under `Assets/Scripts`, and I created no untracked file.

**The footer segments for these two tools, exact text:**

```
[19/19 selftest fixtures]
prop reader ok (12 checks)
clips ok (64 read, 2 known finding(s))
clip picker ok
```

- `clips ok (64 read, 2 known finding(s))` — clip-motion, matching
  `game-design/clip-findings.txt`; the debt ratchet is unmoved.
- `prop reader ok (12 checks)` — prop-dimensions, up from 10 (one rejecting
  check became three ladder lines). `verify.py` counts `ok`-prefixed lines and
  the new footer sentence does not start with `ok`, so nothing else shifted.
- `clip picker ok` — `pick_animations.py` calls `clip-motion`'s `measure(path)`
  three times; the `measure`/`measure_tree` split left that signature alone and
  the picker's own selftest is green.
- Also unchanged and green: `0 lint errors`, `0 shape errors`, `3761 CoreTests`.

---

## 6. The twin sweep — every other selftest in `tools/`

**One idea, two implementations, and the one nobody looks at is the one
missing a line.** So: does a third site exist?

Method, mechanical rather than by memory. `ast` walk over every `.py` under
`tools/`, extracting each `selftest`/`self_test` body; 50 tools carry one, 38
bodies touch a filesystem or parse verb. Then a second pass over each
rejecting-marked region with docstrings, comment tails **and string literals
stripped** — because a frozen *copy* of a real asset embedded as a literal is
NOT a pin (fixing the real thing cannot move the copy), whereas a *read* of one
is. Scanners kept at
`/tmp/claude-0/-home-user-wc26-picks/b9cd91ae-0774-5237-89a0-83f5e9373b08/scratchpad/scan.py`
and `scan2.py`.

### FOUND — a third site, NOT fixed (outside this brief)

**`tools/lint-conditional-reach.py:116-127`.** Two faults, and the second is
worse than the one I was sent for.

```python
    # THE REJECTING CASE, BUILT BY REMOVING THE ONE REFERENCE. This is the
    # exact state the repository was in before the backend was wired up.
    target = GAME / "Audio.cs"
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(original.replace("OnnxSpeech", "NothingAtAll"),
                          encoding="utf-8")
        bad2 = audit(lambda _s: None)
        check(any("OnnxSpeech" in b for b in bad2), ...)
    finally:
        target.write_text(original, encoding="utf-8")
```

1. **Pinned to a real project identifier.** The case only rejects while
   `OnnxSpeech`'s *only* caller lives in `Audio.cs`. Checked, not assumed —
   `grep -rn OnnxSpeech ledger/Assets/Scripts --include=*.cs` shows the type
   declared in `Game/OnnxSpeech.cs`, three references in `Game/Audio.cs`
   (`:1116`, `:1127`, `:1194`) and doc-comment mentions in
   `Core/SpeechStream.cs`. **Add one real caller anywhere else** — ordinary
   work, the speech backend is live roadmap work right now — and the blanket
   replace no longer makes the type unreachable, `bad2` comes back empty, and
   the check goes RED *because the project did more work*. Rename it and the
   same thing happens. Identical shape to ref-bench, Joe.fbx and police.fbx.
2. **It writes to a tracked Game-layer source file on disk, during
   `verify.py`, on every commit.** `ledger/Assets/Scripts/Game/Audio.cs` is
   tracked (confirmed with `git ls-files --error-unmatch`) and
   `ledger/verify.py:554` runs this tool. The `finally` restores it — unless
   the process dies between the two writes. CLAUDE.md records the container
   rolling this checkout back three times on 19 August; a kill in that window
   leaves `Audio.cs` holding `NothingAtAll` and the next reader diagnosing a
   Unity compile error that nothing in git explains. Rule 5: look before you
   destroy, and scope destructive commands to what the operation produced.
   This one writes over an artefact it did not produce.

   The fix is available and cheap and I did not take it, because
   `tools/lint-conditional-reach.py` and everything under
   `Assets/Scripts/Game/` are outside this brief and other agents are live in
   that tree: `audit()` already takes its sources from `GAME`, so the
   rejecting case wants an in-memory or `tmpdir` copy of the tree with a
   **synthetic** conditional type in it — a name that exists nowhere — rather
   than a real one temporarily deleted from a real file.

### FOUND — a weaker pin, NOT fixed (ref-bench is off-limits this session)

**`tools/ref-bench.py:1912-1937`.** The truncated-image rejecting case does
the right thing with the bytes — it copies two real district stills to a
tempdir and truncates the *copy* — but it opens with

```python
    src = sorted(p for p in SIMDIR.iterdir()
                 if p.name.startswith("district_") and p.suffix == ".jpg")
    check("rejecting: a district still exists to truncate", bool(src))
```

so the case is pinned to a real still *existing*. Weaker than the three above
(a still disappearing is a regression, not an improvement), and it degrades
politely — `if src:` skips the rest rather than mis-reporting. Worth noting
only because the skip means five checks can silently stop running while the
tool still prints a pass; the `check(..., bool(src))` line above is what keeps
that from being silent, and it is doing its job. **Not a finding, listed for
completeness.** Its denominator `n_refs + 3` is *derived from the live
reference directory*, which is the good version of the thing that bit me in
§4.7 — adding a reference frame keeps it correct.

### CHECKED AND CLEAN — copies, not reads

These name a real asset or identifier in their rejecting case and are **not**
pinned, because the fixture is a frozen literal in the tool. Improving the
real thing cannot move the copy.

| tool | rejecting fixture | why it is safe |
|---|---|---|
| `tools/lint-static.py:199` | `ApplyDetailToCrowd` as it was actually written, Allman braces and all | inline `_Fake("A.cs", """...""")` string; the real method can be rewritten freely |
| `tools/verdict-dupkeys.py:157` | the real `collidingWorldText 5 vs 9` pair off the landed glyphs/done lines | inline list of two literal strings |
| `tools/frame-drift.py:494` | a camera that walked | TSV rows written into a tempdir by `posewrite()` |
| `tools/sheet-read.py:322` | black / tiny / absent / prone clips | a PIL sheet drawn in the selftest, tempdir, `atexit` cleanup |
| `tools/decal-ink.py:624` | dimension mismatch, unreadable set, empty bank | synthetic sets |
| `tools/body-proportions.py:420` | an inverted rig | a synthetic dict, and its comment already says "there is no such FBX on disk, so it is built here rather than left untested — rule 5b cuts both ways" |
| `tools/lint-filetype.py:72` | the real CS0103 error, put back | literal |
| `tools/verdict-read.py:205` | a real cross-line pair | literal |

### CHECKED AND CLEAN — the quarantine pattern, and it is the third good answer

**`tools/mixamo-pick/pick_animations.py:854-861`** already solved this
problem, **and its comment is the clearest statement of the rule in the
repository**:

> The two halves point at different real files on purpose — accepting at what
> SHIPS, so a bad re-pick goes red here; rejecting at `known-bad/`, so a good
> re-pick cannot empty it.

`tools/mixamo-pick/known-bad/` holds four Mixamo clips that shipped under
`Characters` until the posture screen caught them, **kept out of the build so
a re-pick cannot replace them.** On 21 August a re-pick moved five clips from
the rejecting half to the accepting half — the exact event that would have
broken clip-motion and prop-dimensions — and this selftest survived it,
because the rejecting half was already quarantined.

So there are two valid answers, not one: **synthetic** (built by the tool,
nothing on disk) or **quarantined** (a real artefact deliberately parked
outside the pipeline). What is never valid is a *live* asset. Quarantine has a
cost synthetic does not — `tools/attribution-check.py:29` carries a `WATCHED`
row for `known-bad` precisely because those files still carry a licence
obligation. For clip-motion and prop-dimensions, synthetic was cheaper and
carries no obligation.

---

## 7. Found and NOT fixed

1. **`tools/lint-conditional-reach.py:116`** — the third pinned rejecting
   case, and it mutates a tracked `Game/Audio.cs` on disk inside `verify.py`.
   §6. Needs its own brief; the file and the Game layer are both outside this
   one.
2. **`measure_tree`'s parented-hips refusal has no fixture at all.**
   `tools/clip-motion.py:206-210` returns `"hips are parented -- local curves
   are not world motion"`, and no clip in the harvest has parented hips, so
   that branch has never executed in a selftest. `synthetic_rig` could grow a
   `parented=True` argument in four lines and cover it. Deliberately left:
   this brief was unpinning, and adding an assertion is a different change
   that wants its own review.
3. **`tools/clip-motion.py:413` — `if len(read) < 40`** is an unmeasured
   bound sitting in the accepting case. The harvest reads 64. Where 40 came
   from is not stated anywhere. Not touched (rule 2 cuts both ways: I have no
   series for it either).
4. **`tools/prop-dimensions.py:309` — `check(len(vehicles) >= 20, ...)`**
   same shape, 25 on disk today. Not touched.
5. **The 54MB `Joe.fbx` parse is gone from the selftest**, but that is not a
   speed claim — measured before saying so, `parse_fbx` skips large arrays and
   the whole call was **0.134s**. Removing it saves nothing worth reporting;
   noted because the tempting sentence was wrong.
6. **`tools/prop-dimensions.py` docstring at `:381-383`** still frames the
   rejecting case in the old prose ("pool the same meshes without their
   placements"). It is now accurate about the *mechanism* and no longer names
   police.fbx, so it was left; the detailed history sits in `synthetic_car`'s
   own docstring where the code is.

---

## 8. Conclusions this confirms or overturns

- **Confirms** the 24 August ref-bench diagnosis and generalises it: pinning a
  rejecting fixture to a live asset is not a one-off slip in one tool, it is a
  pattern with **four** instances in this repository (ref-bench/fixed,
  clip-motion/fixed here, prop-dimensions/fixed here,
  lint-conditional-reach/open).
- **Confirms** the picker's `known-bad/` design, retroactively: the 21 August
  re-pick is the event that would have broken both tools fixed here, and the
  picker walked through it green because its rejecting half was quarantined.
  That was a good call at the time and it now has a second and third proof.
- **Overturns nothing measured about the game.** Both tools reported the same
  readings before and after — `clipFindings=2` (`block_end`, `lean`),
  `prop reader ok`, every car floor at 0. This work changed what the
  instruments can *survive*, not what they say.
- **New, and not in any conclusion yet:** an expectation derived from its own
  fixture is an assertion comparing a thing to itself. Two of my own rungs had
  it, for one break-test's duration. Any ladder whose rungs share a derivation
  needs a third line asserting the rungs stand apart — and that line is the
  paired reading, `pooled/placed`, not two keys a reader has to relate.

---

## 9. Key names and output lines added

Neither tool writes to `verdict.txt`, so no verdict keys were added. The
machine-readable line `clipFindings=... duplicates=... frozen=...
stillByDesign=... clipsRead=...` is **unchanged** — `verify.py:196` reads it by
key and would have named any absentee.

New selftest output lines, all whitespace-safe and all naming what they are a
statistic of:

```
  SYNTHETIC FIXTURE (built here, no project asset): <label> <movedCm>cm <turnedDeg> deg <keys> keys  frozen=<bool>
SELFTEST PASSED -- N clips read, M declined, 2 synthetic rigs, rejecting case held
SELFTEST FAILED -- K failure(s) over N clips read, M declined, 2 synthetic rigs

  ok   SYNTHETIC LADDER, rung 1 — placed, the fixture's tyres touch the road — 5 parts, floor 0.0, wanted 0.0
  ok   SYNTHETIC LADDER, rung 2 — REJECTING: pooled unplaced, it buries the car — pooled floor -30.0, wanted -30.0
  ok   SYNTHETIC LADDER — and the two rungs stand apart ... — pooled/placed -30.0/0.0, separation 30.0 (needs > 1.0)
  .. floors, N measured: <name>=<floor> ... (+K more not shown)
prop-dimensions selftest ok — N kit vehicles measured, M kinds squash-checked, 1 synthetic car (built here, no asset)
```

New public names: `measure_tree`, `synthetic_rig`, `_fbx_node` (clip-motion);
`synthetic_car`, `_SYNTH_PARTS`, `SYNTH_FLOOR`, `SYNTH_POOLED`, `_pnode`,
`_capped` (prop-dimensions).

**Not committed.** Working tree holds three other agents' changes; the two
files above are mine and mine alone.
