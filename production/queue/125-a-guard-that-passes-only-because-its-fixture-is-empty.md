line: production (the Unreal emitter's tests)
spec: this file. Found 2026-09-06 by the engine-specialist building the
  readback instrument, while reading code it was not sent to read.
acceptance: `NoSpacePastPrefix` exercised on a surface line carrying the real
  `albedoLoadedAs=2048x2048/JPEG-BGRA8/srgb=yes`, refusing on the shape it
  exists to refuse and passing on the shape it exists to pass; both outcomes
  watched, accepting case first
max_sessions: 1
status: READY 2026-09-06. NOT this weekend, and not urgent: nothing is
  currently broken by it. Filed because a guard nobody has watched reject is a
  guard nobody has watched.

## The finding

`ue-probe/tests/vignette-spec-test.cpp:490` checks
`NoSpacePastPrefix(L, "surfaceStatus=")`, which requires one equals sign per
token. It passes.

IT PASSES ONLY BECAUSE THE FIXTURE LEAVES `MapLoadedAs` EMPTY. The landed
surface line in `production/d1-probe/ue-vignette-verdict.txt` carries
`albedoLoadedAs=2048x2048/JPEG-BGRA8/srgb=yes`, which has two equals signs in
one token. The guard has never met the shape it exists to reject, and it has
never met the real line either.

## Why it is filed rather than fixed on sight

Changing it changes the format of a LANDED key, which is the sort of edit that
should be made deliberately and not while passing. The engine-specialist left
it alone for that reason and said so, which is the right call.

The safe half is already done: every field added to the surface line in the
readback work carries exactly one equals sign, and its fixture uses realistic
engine path names rather than empty strings.

## The rule this is an instance of

CLAUDE.md 5b: a guard must be tested on the case it should PASS, and it also
needs a run where the thing it asserts CAN happen. This guard has only ever
been run on an input that cannot exercise it. A guard that cannot tell a
regression from an improvement is a ratchet, and one whose fixture is empty
where the real data is full is not even that.

## The bound

The number that moves is the count of surface-line fields the guard actually
inspects. Today the fixture supplies fewer than the landed line does, and the
fix is proven when the fixture line is the landed line's shape, both outcomes
watched.
