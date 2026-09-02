line: production (D1 comparison, the critical path)
spec: game-design/decision-2026-09-02-vignette-batch-canon-crews-d1-timebox.md, Ruling 10
acceptance: phase by phase below; each phase is ONE dispatch and its DISPATCH line names what that run will prove
max_sessions: 3
status: READY 2026-09-02. engine-specialist. THE CRITICAL PATH on merit, not on a clock: the timebox was retired 2026-09-02 (game-design/decision-2026-09-02-d1-timebox-retired.md); this item stays first because it is the only queued work that moves the Phase 0 exit gate.

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
