# D1 measurement a: what one cycle costs, per engine

STATUS: LIVE. Verified 2026-09-01.

The decision D1 has to make is which engine LEDGER is built in. Measurement a
is the loop cost: how long from an edit to seeing whether it worked. This file
holds what has actually been measured, with the boundaries named, because the
single easiest way to get this wrong is to compare two numbers that do not
cover the same span of time.

## The three quantities, and why they are not interchangeable

| file | span it covers | what it can be compared to |
|---|---|---|
| unity-build-steps.tsv | the build step alone, on one named machine | another engine's build on the same machine |
| unity-roundtrip.tsv | source commit to published verdict | another engine's whole CI loop |
| cycles.tsv | edit start to result seen, written live | the felt cycle, once it has rows |

A build time set against a round trip prices the runner, not the engine.

## What is measured, 2026-09-01

### Unity, on ledger-pc (Jafar's PC, the self-hosted agent)

n = 72 runs, warm (the agent keeps Library/ between runs).

    build player      median 2.47 min   p10 2.43   p90 2.97   worst 3.48
    sim run           median 12.28 min
    whole job         median 17.77 min
    queue wait        median 0.03 min

The build is remarkably stable: p10 to p90 spans half a minute over 72 runs.

### Unity, on GitHub hosted runners, for contrast only

n = 116 runs. Build median 2.54 min, but p10 1.78 and p90 4.23, and the whole
job runs 31.03 min against ledger-pc's 17.77. The hosted rows are a different
CPU and are kept separate rather than pooled. Pooling them was the first
version of this measurement and it would have compared a rented CPU against
Jafar's machine while claiming otherwise.

### Unity, whole round trip, from landed evidence

n = 369 real round trips, source commit to the CI commit publishing its
verdict. Median 26.0 min all time, 17.6 min over the recent 20, p10 17.0,
p90 33.9, worst 225.7. 26 of 369 round trips returned nothing at all
(NO PLAYER LOG), which is 7 percent of the loop spent and unanswered.

The all-time median and the recent median differ because the runner moved to
ledger-pc. That is a regime change, visible in the series and invisible to any
single summary, which is why the series is printed above them.

### Unreal, on ledger-pc

n = 1. Cold build 1.12 min, warm build 0.03 min, binary 324 MB.

ONE RUN IS NOT EVIDENCE and this number is not yet a median. It is recorded
because it establishes something else that is worth more right now: the
toolchain works, the target links, and the loop is measurable.

## What CANNOT yet be concluded, stated plainly so nobody quotes it as if it can

1. The UE module is two files. Unity's build is the whole player with its
   assets. Setting 0.03 min against 2.47 min compares a two-file incremental
   against a full player build, and the honest reading is that the UE side has
   not yet been given enough to compile to be representative.
2. The UE side has no sim, no content, no evidence channel and therefore no
   round trip to compare against Unity's 26 min. Measurement a is half done.
3. Nothing here speaks to measurements b, c or d.

## The named unknown that decides the shape of the answer

Whether the verdict channel reproduces in UE. Unity's loop is expensive partly
because the answer has to travel through CI to be readable at all. If a UE
build can produce the same committed verdict locally on ledger-pc, the
comparison changes from build-time to whether the evidence discipline survives
the move. That is the question worth the next probe, and it is not a
performance question.

## The protection on this decision

D1 gives ties to Unity. A tie is a MEASURED tie. If the UE side cannot be
measured, D1 closes UNRESOLVED, never "Unity wins".
