> **STATUS: LOG, 2026-08-26. NOT CURRENT** after the next change to
> `tools/prop-dimensions.py`, `tools/prop-reach.py` or `ledger/verify.py`, or
> after CLAUDE.md's `confabs` paragraph is corrected. Tier-2 audit, read-only.
> Written up by the resident from the auditor's final message — the auditor has
> no Write tool.

# Two ruled measurements: where the break sits, and whether a fifth pin exists

## PART 1 — the `confabs` regime boundary sits EXACTLY at the rule change

**`fd0b6178` — 2026-08-03T23:30:08Z, "The player can tell a lie, and be caught
telling it".** Found with `git log -S"Junction" -- Game/GossipDirector.cs`, not
by eyeballing a series. Its diff replaces the confab siting test outright:

    -  bool clear = OffRoad(wa...) && OffRoad(wb...)
    +  bool clear = CanStopHere(wa...) && CanStopHere(wb...)

**The partition is by ANCESTRY, so it does not depend on the ordering that was
broken** (`git rev-list --ancestry-path fd0b6178..HEAD`):

    BEFORE (does not contain it)  n= 42   0..42   median  8.5
    AFTER  (contains it)          n=281   7..86   median 34
    boundary runs: 39923767 = 56 (contains) | 15e5845 = 9 (does not)

**One transition — not two, not scattered.** Four commits span the boundary and
two are CI's own stills; `fd0b6178` is the only game-code change in the gap.
`daysClosed=6` is identical in both boundary verdicts, so run length is not the
confound, and `GossipDirector.Confabs` has had exactly one commit in its whole
history, so this is not a renamed number. Corroborated contemporaneously by
`SimDirector.cs:4372`: *"the junction fix took confabs from 7 a run to 56"* —
56 is the measured value of the first containing run.

### It is FOUR regimes, not two — and THAT is what the record gets wrong

    A  pre-walk-slowdown (crowd jogging)  n= 14  11..42  median 20
    B  slow walk + flat-road rule         n= 28   0..18  median  6
    C  junction rule, small map           n=137  28..86  median 54
    D  junction rule, stretched city      n=144   7..51  median 22

Each band is a single contiguous ancestry block. **A->B is `7f71fea8`** (the
9.4 km/h jog -> 1.4 m/s walk — not a conversation-rule change at all).
**C->D is `a21e6e63`, "The city stretches"** — `WideBlocks` on, 60 parcels ->
376.

**So the location in the record is RIGHT and the framing is WRONG.** CLAUDE.md
says 1–13 under the flat-road rule and 29–74 under the junction one; measured,
B is **0–18** and C is **28–86**, and **band C ENDED on 17 August**. Today's
regime is D, 144 runs, median 22. **Correction not proposed here — the director
ruled it returns through the next mandatory spawn.**

### The auditor checked its own probe and found it faulty first

The repaired ordering has **zero commit-time inversions across all 323 runs**.
Its first pass reported three; they were its own timezone-naive string compare
on `%cI`, and re-running with `%ct` dissolved them. The ancestry partitions
each producing exactly one contiguous transition is a second, independent
confirmation that the order is now real.

**Could not settle:** whether anything besides crowd speed caused A->B (one
commit in the gap, the project's own contemporaneous note names it, but it was
not re-derived from code); and no run-length key exists before 26 Aug, so the
confound could be excluded only at the boundaries themselves.

---

## PART 2 — a fifth pin exists, and three more behind it

### Coverage first, because a short list and an incomplete audit must not look alike

    tools/ (.py/.sh) + verify.py                     91 files
    defining a selftest/fixture harness              58
    selftest functions AST-parsed                    57
      ... mentioning an artifact-shaped path         41
      ... READ IN FULL and classified by hand        14
      ... classified from the mechanical scan only   43
    verify.py check functions                        55 enumerated, 6 read in full

**This is a FLOOR on the count, not a ceiling.** 49 of 55 verify checks were
greped, not opened — and rule 3 says grep is not enough, open the function.

### 1. `tools/prop-dimensions.py:542-546` — THE FIFTH. An accepting fixture asserting VALUES of a tracked asset.

    total, size = geometry(CAR_KIT/"police.fbx")
    check(total > 1000, "the vertex cap is lifted, so a model reads whole")
    check(100 < size[2] < 400, "and it has a size")

Measured now: 1430 verts, size `(150.0, 130.0, 309.99997)`. `verify.py:489`
returns False on failure, so it **blocks every commit** — the identical blast
radius to `ref-bench` an hour ago. A replacement police model exported at a
different FBX unit scale, the commonest thing on a kit swap, puts `size[2]`
outside the bound. **Headroom 90 units on a bound whose failure mode is a
factor of 100.**

**And note the shape:** `police.fbx` appears in the repaired four as a
*rejecting* fixture. This is a **second, different site, in a different file,
using the same asset as an ACCEPTING fixture** — rule 1's third corollary
exactly: the repair grepped for one of them.

### 2. `ledger/verify.py:1211` — an exact-equality bound on the cast

`if m.group(1) != "4"` is a second copy of `ConvoProbe/Program.cs:272`'s
`want = new[] { "lena", "rocco", "ada", "sam" }`. Adding a fifth probed
character, or renaming one, fails verify and **the message will say the probe
is broken.** Two numbers, one idea; the constant that should move is in C#, the
one that blocks the commit is in Python.

### 3. `tools/prop-reach.py:206-224` — three assets pinned by name, and an INVERSE RATCHET

    check("the real corpus still has unreached models",
          sum(1 for r in route.values() if r == "none") > 20)

**That floor requires at least 21 fetched models to stay unplaced FOREVER** —
the opposite of what M17.10 wants to be true. Ten lines above sits the
paragraph explaining why the *rejecting* case was made synthetic, in these
words: *"a rejecting case pinned to a real asset asserts that the asset stays
UNUSED, which is the opposite of what this project wants."* **The `> 20` floor
is that same assertion in aggregate.** Today: 213 models, 74 reached, 139
unreached — 118 of headroom, so structural rather than urgent. The three named
assets (`oga_vehicles_bus`, `city_kit_roads_light_curved`,
`base_mesh_park_bench`) are live risk under a re-dressing pass.

`prop-reach.py:227` is **correct and must not be flagged** — it reads the
landed verdict and prints *"NO LANDED VERDICT — the strongest check did not
run, and that is not the same as it passing"*. Rule 3b done right.

### 4. `tools/shape-check.py:383-391` — flagged as a hunch, not an accusation

Tempdir-scoped so it cannot scribble on tracked files, but hard-codes cast ids
(`picks/lena`, `ada.*.mp3`); recasting is a `KeyError`, not a legible failure.
Rejecting-side only, no value assertion. **Not called the fault.**

### Explicitly cleared — do not re-flag

`hang-report.py` (live codebase as accepting fixture, synthetic rejecting rung,
comment says so), `body-proportions.py` (assertions are physics any correct rig
satisfies), `prop-dimensions.py:530` (min over all kit models, degrades
gracefully), `ref-bench.py:2584` (no file read), `pc-watcher.py`,
`stage-voice-assets.py` (contract assertions between two tracked things), and
all five lints sweeping the live tree with synthetic `Synth*` rejecting rungs.

## The deliverable

**The standing lint's condition is MET — a fifth exists.** All four findings
sit behind `verify.py` checks that return False, so **all four block every
commit when they bite.** But size the lint's scope off the **41 candidate
selftests**, not off the 4 confirmed: 14 were read in full.
