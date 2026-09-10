line: instruments
spec: A lint refuses an identifier that is a macro on the toolchain that
  actually builds, so this class of compile error stops costing a round trip.
acceptance: the lint red on a planted "const int PI = 0;" in the ue-probe tree
  and green on the live tree, with the macro list DERIVED rather than hand-typed
  where that is possible
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-10 13:10Z. Cost one full PC round trip today, measured.

  WHAT HAPPENED. The exposure ladder was built, reviewed, gated and dispatched.
  The run came back with sceneStatus=NOTHING-EMITTED,
  sceneNote=build-step-published-no-binary and shotsWrote=0/0, and the cause is
  two lines in ue-build.txt:

    SurfaceBind.h(1027,15): error C2106: '=': left operand must be l-value

  Line 1027 was "const int PI = ProceduralSurfaceIndex(B.Surface);". PI IS A
  MACRO ON THAT TOOLCHAIN, so the declaration expands to a literal on the left
  of an assignment and the compiler says exactly that. Renamed to ProcIdx, three
  occurrences, and the container tests still read 383 of 383.

  WHY THE CONTAINER CANNOT SEE IT, WHICH IS THE WHOLE POINT. The tests here
  compile the same header with g++ against a shim that defines no such macro, so
  the file is valid C++ locally and invalid where it actually builds. That is
  the class .claude/rules/ci.md already names, the compile errors a
  reference-independent check cannot see, and five lints already exist for other
  members of it. THIS IS A SIXTH AND IT HAS NO LINT.

  THE INSTRUMENT WORKED EVEN THOUGH THE BUILD DID NOT, and that is worth
  recording beside the fault. The verdict refused to carry the previous run's
  frames under this run's name: it printed NOTHING MEASURED, named the commit it
  was measuring, and said no frame was attempted. A run that measured nothing
  said so, which is the ci.md rule that makes a red build cheap to diagnose
  instead of a mystery.

  THE LINT'S POPULATION SHOULD BE DERIVED WHERE IT CAN BE. A hand-typed list of
  macro names is the fault this studio ruled a standing standard against on
  9 September: a lint derives its population from the artefacts it checks, never
  from a hand-written list, and a hand list is allowed only as an exemption or a
  floor. If the real macro set cannot be read in the container, say so and make
  the hand list a FLOOR with each entry carrying its reason.
