line: instrument (the standing rule about where arithmetic lives)
spec: The grate camera's grid geometry, framing angles and degree wrapping move out of
  ue-probe/Source/LedgerProbe/Private/WalkProbe.cpp into a header a container test
  compiles, with the 17-check harness the A3 builder already wrote shipping beside them
  in ue-probe/tests/.
acceptance: the same checks run inside ledger/verify.py's ue_probe_tests, and the
  planted case where the five-ray vote reads 5/5 while the 81-cell grid reads 72/81
  is one of them
max_sessions: 1
status: READY 2026-09-09, and it is a KNOWN gap against a standing rule rather than a
  discovery. The rule, ruled 25 August after a third instance: measurement arithmetic
  and formatting live where the tests run, because a formatter written in a layer that
  does not compile locally ships UNRUN.
  WHAT HAPPENED: amendment A3 of
  game-design/decision-2026-09-09-the-railing-in-the-line.md forbade touching any file
  but WalkProbe.cpp, deliberately and correctly, because it was a printing-only change
  going out on a clock. So the grid spacing, the framing angles and WrapDeg180 all
  landed in a translation unit no container compiles. The builder wrote a 17-check
  harness anyway, proved it green, and reported that A3's own scope forbade shipping
  it. That is the right way to hit a scope wall.
  THE CHECK THAT MATTERS MOST, and the reason this is not tidying: rejecting case 3
  plants a 42 mm bar 5.5 cm off centre, and the five-ray vote reads 5/5 CLEAR while
  the 81-cell grid reads 72/81. That is the sampling fault the whole grid exists to
  expose, proven on a planted condition, and today it is proven only in a scratch file
  that will be deleted with the container.
  THE HARNESS EXISTS AND ITS METHOD IS WORTH KEEPING: the functions under test are cut
  out of WalkProbe.cpp by script and included, so the thing tested is the thing that
  ships rather than a copy that can drift.
