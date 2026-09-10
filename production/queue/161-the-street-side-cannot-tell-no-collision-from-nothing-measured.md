line: instrument (the walk clip's evidence)
spec: Rename the street-side collision reading in ue-probe VignetteShot to
  propPlacedWithCollision / propPlacedCollisionUnread / propPlacedCollisionStat, make
  it three-valued YES / NO / UNKNOWN, print the words nothing measured at a zero
  denominator, carry PROXY on the stat, and MOVE the tally, the arithmetic and the
  string into the tested header with rows in both directions in
  ue-probe/tests/vignette-spec-test.cpp.
acceptance: a placed mesh collidable by a complex-as-simple flag reads YES and not NO,
  a mesh with no body setup reads UNKNOWN and not NO, and both rows run in the container
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-08, and it BLOCKS THE WALK CLIP DISPATCH. Amendment A5 of
  game-design/decision-2026-09-08-queue-147-the-composed-telling-and-the-clause-the-bank-never-had.md
  section 7.
  THREE FAULTS IN ONE EIGHT-LINE FUNCTION. PropCollisionPrims returns 0 both when
  there is NO body setup and when a body setup holds zero aggregate elements, so "no
  collision object" and "collision by a complex trace flag" read identically. The last
  landed walk run prints propCollisionPrims=0/0 with propCollisionUnread=0, a zero
  over a zero denominator, while propCentreWorstMm on the same line correctly prints
  on=nothing-measured/of=0. And the key name says Prims while the thing counted is
  MESHES, on both sides of the clash.
  WHY IT BLOCKS. The same run prints propsAsMesh=0/23, propStandIns=23/23 and
  propFallbackWhy=prop_drainage_grate_01_0=no-uasset-for-drainage_grate_01. The mesh
  route has never placed one prop mesh in the walk build, so the false NO has not
  happened yet, and the FIRST run on which it can happen is the run that produces
  Jafar's clip. A reading that cannot tell no collision from nothing measured, asked
  for the first time on the run that IS the deliverable, is the same failure twice.
  ALSO REFUTED HERE: propCollisionEnabled=QueryOnly/the-walk-path is not a sweep and
  answers nothing. VignetteShot.cpp 940 picks that literal from bInteractive, the same
  bool that drove SetCollisionEnabled at 513. It restates the code's intention and
  cannot fail: two numbers from one variable, wearing a verdict key.
