line: production (D1 comparison, the critical path)
spec: game-design/decision-2026-09-02-vignette-batch-canon-crews-d1-timebox.md, Ruling 10
acceptance: phase by phase below; each phase is ONE dispatch and its DISPATCH line names what that run will prove
max_sessions: 3
status: READY 2026-09-02. engine-specialist. THE CRITICAL PATH on merit, not on a clock: the timebox was retired 2026-09-02 (game-design/decision-2026-09-02-d1-timebox-retired.md); this item stays first because it is the only queued work that moves the Phase 0 exit gate. Since the tie-break reversal (2026-09-02, same ruling as 037), landing its four admissible pairs through a converging loop is winning unless Unity is decisively better: (a) is the decisive measurement, and 032's round-trip printer rides this item's first UE dispatch. Phase A LANDED 2026-09-02 (game-design/decision-2026-09-02-free-lane-and-piece-list-batch.md): 546 pieces, sixteen fields, drift plus round-trip plus cross-engine guard. Phase A2 below, queue 040 and queue 041 are ONE engine-specialist session, the Phase A close-out, before Phase B.

## Phase A: a flat piece list, so the two engines cannot disagree on layout

A CoreTests or tool step writes `production/specs/vignette-pieces.json`:
every `Piece` with bom, name, shape, surface, centre, size, pitch, yaw, roll
and emissive, plus cameras, conditions, shots and the lamp colour. Committed,
with a drift guard proving that regenerating it changes nothing and that its
count equals the Unity plan's `pieces=`.

THE UE EMITTER READS THAT, NOT THE SCENE JSON. This is what makes every
difference in a judged pair a RENDERER difference rather than two emitters
disagreeing about where a kerb goes. It stays admissible under the shared
JSON rule by construction: every object still arrives from the shared JSON
through a generator, and the generator is the tested one.

## Phase A2: the probes, same generator, second file

`production/specs/vignette-feet.json`, written by the same
`--write-vignette-pieces` run: one line per probe from `plan.Feet` (845
today: name, bom, edge, region, x, z) plus the datum the plan expects there
from `GroundAt` (level and edge), so the UE placement instrument compares a
raycast to a number in the file and never re-derives `Foot5` or the
crossfall in C++. Same guard shape as the piece list: byte-identical
regeneration, parse back, count equal to the plan's `feet=` print and to
the landed run's `probes=845` denominator (runs/152198e.txt line 98). Ruled
2026-09-02 (free-lane-and-piece-list ruling, Ruling 6). Queue 033 changes
this file and the drift guard is what shows it.

## Phase B: untextured frames

Engine basic shapes; point lights at the emissive pieces; the two conditions
as fog, sky light and a directional light; the four named shots at 1280x720
through run 16's capture path generalised to a list; one verdict line per
shot with the frame time as a MEDIAN over the same warm and timed counts the
Unity host uses (8 and 24). All untextured, deliberately.

## Phase C: materials, which is the unknown

Runtime import of the allowlisted maps into textures, and dynamic instances
of a base material with texture parameters. THE BASE MATERIAL IS MADE BY AN
EDITOR SCRIPT RUN IN THE COOK STEP, a build product committed to git, NEVER
by hand. A hand-made uasset disqualifies the still under D1b.

## Phase D: the character body

Per Ruling 10's first paragraph: the scene as landed is NOT an admissible
(b) scene, because D1b's mandatory contents include at least one clothed
character body and the JSON places none. On the UE side this is precisely
the binary-asset friction D1b Ruling 4 wanted measurement (b) to catch.

## Carried verbatim from the UE builder, waiting behind the phases above

- Per-run copies keyed by short sha for the UE verdicts. The channel spec has
  them; step 1 shipped without one, so step 2 stayed consistent rather than
  diverging.
- Wire `ue-probe/tests/frame-stats-test.cpp` into `verify.py` as a gate so
  the 25 checks cannot rot.
- A brightness bound, which needs the series run 16 will start printing.
