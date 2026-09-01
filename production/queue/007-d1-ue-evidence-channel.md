line: instrument (D1 probe, the deciding unknown)
spec: production/d1-probe/evidence-channel-spec.md
acceptance: a UE run commits a verdict file naming its commit on line 1 and at least one still, both staged by name; a run that rendered nothing says so and carries nothing forward; tools/verdict-read.py reads the UE verdict unchanged
max_sessions: 3
status: STEP 1 DONE 2026-09-01 (run 14). The UE side commits a traceable
        verdict and tools/verdict-read.py opens it with every refusal intact:
        same-line keys accepted with line numbers, cross-line keys refused,
        a missing file refused as nothing measured. The reader needed a --file
        argument because it was wired to the Unity shots directory; its
        behaviour is unchanged. Steps 2 to 4 (a still, then a placed camera)
        remain and need -RenderOffScreen rather than -nullrhi.

Reproduce LEDGER's evidence channel on the UE side.

WHY THIS AND NOT MORE BUILD TIMING. Measurement a now has real Unity
numbers and a working UE build, and the remaining gap is not performance.
Unity's loop costs what it costs largely because the answer has to travel
through CI to be readable at all; if the UE side cannot produce the same
committed verdict and stills, then D1 is not comparing two engines, it is
comparing an instrumented engine against an uninstrumented one, and the
comparison is worthless in whichever direction it lands.

The deliverable is the channel, not a pretty frame. A grey box photographed
correctly, with provenance, beats a good-looking screenshot nothing can
trace.
