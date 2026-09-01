# DIRECTOR RULING: D1 measurement (b) is RE-SCOPED, not dropped (1 Sep 2026)

> **STATUS — LOG, 2026-09-01. NOT CURRENT once D1 closes.** A director
> ruling: it records what was
> decided and why, and stops being current when D1 itself closes. The
> live consequence is the AMENDED line in
> ledger-v2/respec/decision-register/D1-engine-probe.md, which is the
> source of truth for what measurement (b) now is.


> **STATUS: LOG, 2026-09-01. NOT CURRENT once the two-line amendment below
> lands in `ledger-v2/respec/decision-register/D1-engine-probe.md`; from then
> the register is the reading copy and this file is its history.**

Prompted by Jafar's question about the planned visual comparison ("same
street, both engines, weeks not hours"): "why? we have a new visual bar, a
different approach, why does the old stuff matter here?" He is challenging
the framing, and the framing was checked against the tree rather than
defended. He is half right, and the half he is right about removes most of
the cost.

## What was verified this session, before ruling

- `ledger-v2/respec/decision-register/D1-engine-probe.md` (2026-08-31):
  measurement (b) is "visual ceiling reached in the timebox on the same
  street built in both engines". Decision rule: "Unreal wins only if (b) is
  decisively better and (a) is tolerable for autonomous operation. Ties go
  to Unity." Same record, standing constraint: "the world stays data-driven:
  JSON/YAML world source of truth, generators emit engine content, binary
  assets are build products."
- `D8-visual-bar.md` (same day): GTA V PS3 retired; the bar is photoreal wet
  overcast grimy Britain, instrumented by Meridian Test conditions 1 and 3
  and D7 judging; the M17.10 decomposition kept as technique.
- `production/d1-probe/plan.md`: week 2 item 4 reads "Build the same street
  in both engines to each engine's ceiling within the box", and the standing
  constraint paragraph forbids hand-edited binary scenes during the probe.
  Timebox ends 2026-09-14.
- `production/d1-probe/measurements.md` (verified 2026-09-01): measurement
  (a) is well advanced on both sides; UE builds, cooks, packages; the ported
  perception core agrees with the shipped C# on 1221 rows; the verdict
  channel reproduces in UE and `tools/verdict-read.py` opens it. The UE
  still-capture path (task 007 steps 2 to 4, -RenderOffScreen) is UNRUN.
- `ledger/Assets/Scripts/Game/AssetLibrary.cs` lines 12 to 16: the Unity
  world is code-generated with a JSON override layer for materials only.
  **No JSON world source of truth exists in either engine. "Generators emit
  engine content" is a standing constraint and a Phase 0 goal, not running
  code.** This is the fact the ruling turns on.

## Ruling 1: (b) stands as a question, and its method is re-scoped

Jafar is right that "the old stuff" does not matter: nobody needs a probe to
learn that UE5 in skilled human hands renders wet overcast Britain well.
That is published, visible in any showcase, and measuring it would be
measuring Epic's artists. He is also right that "weeks" was stale: that
number came from reading "same street" as two hand-builds, quoted from the
probe spec without re-reading it against D8 and the data-driven constraint
(the resident flagged this itself, correctly).

What survives, and what no cheap substitute answers, is the only question
D1's decision rule actually asks: **what can THIS studio's autonomous
pipeline reach in each engine, on this game's content, in bounded time.**
The engine choice is a bet on that number, not on the renderer's ceiling.

**New (b), binding once amended into the register:**

One shared scene definition (JSON), a small British street vignette on the
D8 bar: wet asphalt, brick, overcast day and wet night as two conditions,
practical lights at night, at least one clothed character body. Assets from
the license allowlist only, entering through the pipeline in
`ledger-v2/studio-v2/pipelines.md` (fetch, Blender headless clean, license
tag). A thin generator per engine emits the scene from that JSON. Paired
stills from matched cameras in both conditions, committed through each
engine's verdict channel, with the frame time printed beside each still's
identifiers.

**Admissibility rule, which is where the cheap version would cheat:** every
object in each engine's scene arrives via its generator from the shared
JSON. A hand-edited binary scene or uasset disqualifies the still as (b)
evidence. Pre-made showcase content (City Sample and its kin) is
inadmissible for the same reason: it measures someone else's hands.

**"Decisively better", in terms a person can check:** blind side-by-side
judging of the paired stills (D7 judges if calibrated by then, and Jafar's
own unlabeled look either way). UE wins (b) only if the UE frame is
preferred on the D8 decomposition in at least three of the four pairs (two
cameras by two conditions) and is worse in none, and the judging verdict
quotes both engines' frame times for every pair it cites. No frame-time
bound is set here: none has a printed series yet, and rule 2 forbids
inventing one. A preference that ignores a large printed frame-cost gap is
not a measurement, and the close-out must say so if the case arises.

Anything short of that is a tie, and ties go to Unity.

## Ruling 2: cost

- **Timebox: unchanged, ends 2026-09-14. No extension granted.**
- Round trips, with what dominates named per rule 7: the dominant unknowns
  are the UE still-capture path (unrun) and headless UE asset import
  (unproven). Estimate: order of 10 to 20 UE round trips at the current
  short UE loop, which will lengthen as the scene gains content, plus 5 to
  10 Unity round trips at the recent 17.6 minute median for the Unity
  emitter. Days of unattended CI time. Not weeks, and the "weeks" quote to
  Jafar is withdrawn.
- **Jafar's time: zero during the build** (the self-hosted agent needs
  nothing from him, per the corrected plan), then minutes for one blind
  look at the pairs. One honest maybe: if headless UE asset import fails,
  a single interactive editor session may be needed, and that gets asked
  for as a named ask, not assumed.
- The waste hedge that makes this cheap: the scene JSON and the winning
  engine's emitter ARE the first slice of the data-driven world pipeline
  that Phase 0/1 needs regardless of the engine outcome. The only discard
  is the losing engine's emitter, thin by design.

## Ruling 3: the decision rule survives verbatim

"Ties go to Unity" and "if the UE side cannot be measured, D1 closes
UNRESOLVED, never Unity wins" are both re-affirmed, unchanged. If the box
expires with (b) unmeasured, D1 closes UNRESOLVED per its own rule; it does
not close on taste, on partial pairs, or on this ruling.

## Ruling 4: what (b) must still catch that a cheaper version would hide

1. **Binary-asset agent friction disguised by hand polish.** A UE still
   assembled in the editor would look like a pipeline result and be evidence
   about the editor. The admissibility rule exists for exactly this, and it
   is the UE-specific risk (a) already names.
2. **An off-bar reference scene.** A generic CC0 demo that is not wet
   overcast Britain at night misses precisely where the engines diverge
   (overcast GI, wet-surface response, practical lights), which is where the
   D8 bar lives. The scene contents above are mandatory, not illustrative.
3. **A pretty frame at an unshippable cost.** Stills-only comparison hides
   frame time; every pair prints it, and the judging verdict must quote it.
4. **Someone else's content standing in for the pipeline.** Allowlist plus
   generator placement is the only admissible route in.

## Amendment directed (resident applies in the reviewed commit; two lines)

Append to `D1-engine-probe.md`: "AMENDED 2026-09-01: measurement (b) is
re-scoped per game-design/decision-D1b-rescope.md: one shared JSON scene on
the D8 bar, emitted into both engines by generators, paired stills judged
blind, decisively better defined there. Decision rule unchanged."

This file lives in `game-design/` because the director_cadence gate requires
the ruling stamp inside a `game-design/decision-*.md`; the register carries
the pointer so the source of truth stays one place.

## Deliberately NOT decided

- The engine. That is D1's close-out, on the numbers, inside its box.
- Any frame-time bound (no printed series; rule 2).
- Scene composition and asset picks beyond the mandatory elements.
- Whether D7 judge calibration lands in time. If it does not, the pairs are
  still committed and Jafar's blind preference is the recorded reading;
  whether that suffices for "decisively better" is his call at close, and
  it is flagged to him rather than resolved silently here.

Spawn row, quoted verbatim from `.claude/agent-log.tsv`:

    2026-09-01T15:13:28Z	studio-director

<!--RULING spawn=2026-09-01T15:13:28Z-->
