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

Build, over four runs that reached the compiler:

    cold build      1.12, 0.75, 0.75, 0.75 min
    warm build      0.03 min every time
    binary          324 MB

Cold is genuinely cold every run: clearedBeforeCold has read 0 of 4 on each
of the last two, meaning the checkout wipes the workspace, so nothing carries
over. The 0.03 warm figure is a SECOND INVOCATION INSIDE ONE RUN, not a
next-day rebuild, and it is labelled that way wherever it appears.

Cook, over the two runs that reached one:

    cold cook       2.00, 1.70 min   (pays for shaders and staging once)
    incremental     0.45, 0.43 min   (no edit between: the floor of a cook)

THE PIPELINE IS COMPLETE AS OF RUN 13: build, cook, stage, package, and the
golden test running against the PACKAGED artifact rather than the compile
output. 1221 rows, 0 mismatches, from the binary a player would be given.

One reading to not misread: the packaged run exits 1, because asking the
engine to quit from inside module startup does that by design. A passing run
therefore prints gameExit=1 beside probeTest=PASS. The evidence is the result
file; the exit code only says the process ended. The verdict line says so
now, because that pair is exactly the shape a later reader gets wrong.

Four attempts preceded it and every failure was setup rather than cycle: no
editor target, then the .NET Framework SDK missing, then the golden test
itself killing the cook commandlet it was running inside.

SO A UE EDIT-BUILD-COOK CYCLE ON THIS MACHINE IS ABOUT HALF A MINUTE, warm
build plus incremental cook, against Unity's 2.47 minute warm build. That
comparison is closer to fair than anything above it, because both are the
repeat cost on the same PC. It is still not fair, and the reason is the same
one as before and has not moved: the UE project is two source files and no
content, and Unity is building a whole game with its assets. The number to
watch is not this one, it is whether it holds when the UE side has a street
in it.

Loop, over five real edits: median 10 min, from cycles.tsv, every endpoint
traced to a landed CI commit.

THE LOOP NUMBER IS NOT COMPARABLE TO UNITY'S 17.6 AND MUST NOT BE QUOTED AS
IF IT WERE. The UE side runs no simulation, renders nothing, captures no
stills and commits no verdict of its own. It is a shorter loop because it
does less, and it will grow when it does more. What the four builds do
establish is worth more than a premature comparison: the toolchain works, the
target links, the ported core compiles under UE's own build system, and every
failure so far has been diagnosable from a committed file.

## Setup cost, which is part of measurement a and was not being counted

D1 asks what a cycle costs. It also has to ask what it costs to have a cycle
at all, and on the UE side that is being paid now, one round trip at a time.

    UE 5.8.2 install            blocked for hours by a launcher bug, then
                                worked around in about a minute once the
                                symptom was searched rather than reasoned about
    MSVC build tools            2.9 min, unattended, verified by vswhere
    .NET Framework SDK          found missing by run 9; the editor needs it
    discovery round trips       runs 4 to 9: target shape, runtime config,
                                editor target, and the SDK gap. Six round
                                trips, none of which measured anything about
                                the engine

THE HONEST FRAMING, because this number is easy to misuse in both directions.
Unity's equivalent setup was paid months ago and is invisible, not absent. A
fair reading is not "UE costs six round trips and Unity costs none"; it is
that the UE path is currently unpaved on this machine and each unpaved step
has cost between two seconds and twenty minutes to find. What matters for D1
is whether that curve flattens: setup cost is paid once, cycle cost is paid
forever, and only the second belongs in the decision.

What is worth recording either way: every one of those six failures was
diagnosed from a committed file, and after the diagnosis channel was built,
each took one round trip instead of several. The two that took two round
trips each were the two where the step could not say why it failed.

## What CANNOT yet be concluded, stated plainly so nobody quotes it as if it can

1. The UE module is two files. Unity's build is the whole player with its
   assets. Setting 0.03 min against 2.47 min compares a two-file incremental
   against a full player build, and the honest reading is that the UE side has
   not yet been given enough to compile to be representative.
2. The UE side has no sim, no content, no evidence channel and therefore no
   round trip to compare against Unity's 26 min. Measurement a is half done.
3. Nothing here speaks to measurements b, c or d.

## The unknown that decides the shape of the answer: ANSWERED for step 1

Whether the verdict channel reproduces in UE. It does.

Run 14 committed production/d1-probe/ue-verdict.txt: line 1 naming the commit
it was measured on, no spaces in any value, whole-run numbers on one done
line, and the words NO RUN reserved for a run that measured nothing. It was
collected by name and guarded against the checkout restoring the previous
run's copy.

THE PART THAT MATTERS IS THAT THE EXISTING READER OPENS IT. tools/verdict-read.py,
unchanged in behaviour, reads the UE verdict and keeps every refusal it has:

    three keys from one line       accepted, line number printed for each
    keys from two lines            REFUSED, with the full explanation
    a file that is not there       REFUSED as nothing measured, not as clean

One small change was needed and it is worth naming precisely, because it is
the kind of thing that would otherwise be reported as a format problem. The
reader was wired to game-design/sim-shots, the only place a verdict had ever
been written, so it could not be POINTED at the new file. That is a smaller
finding than an incompatibility and would have looked identical if nobody had
tried it. It takes a --file argument now; the same-line rule and every
refusal are untouched.

So measurement c's one named UNKNOWN is closed for the verdict half. What
remains of task 007 is steps 2 to 4: a still, offscreen, then a placed camera.
Those need -RenderOffScreen rather than -nullrhi, which are opposite things,
and the exact capture call is still unrun here.

## The protection on this decision

D1 gave ties to Unity until 2026-09-02 and gives them to Unreal since (the
register's second amendment of that date). A tie is a MEASURED tie either
way. If the UE side cannot be measured, D1 closes UNRESOLVED, never "Unity
wins" and, now that the preference points the other way, never "Unreal
wins" either.

## What fails measurement a, ruled 2026-09-02 (the timebox is retired)

Until 2 September (a) was going to be failed by a date: no textured UE
still of the shared scene by 2026-09-12 12:00Z would read NOT TOLERABLE.
Jafar retired the date. What fails (a) now is a property of the series in
DISPATCH and cycles.tsv, never of the calendar:

1. NON-CONVERGENCE. Three consecutive dispatches on one phase fail on the
   same failure mode and the committed evidence cannot name the cause. Two
   is the worst this probe has printed (the setup section above: two
   failures took two round trips each, and those were the two where the
   step could not say why). Three is the first point outside the record.
   At three, a director is spawned and either closes (a) NOT TOLERABLE on
   the series or names the instrument change that makes the failure
   readable (rule 12); the count restarts only when the instrument changed,
   never when the guess did.
2. HAND-EDIT DEPENDENCE. A phase that cannot land without a hand-made
   binary asset. D1b's admissibility rule already disqualifies the still;
   the finding here is about the loop: a failed-edit rate of 100 percent on
   that asset class, which is the UE-specific friction (a) was written to
   catch. One interactive session for SETUP (a plugin, a licence prompt) is
   a named ask to Jafar and is not this; a hand-made asset is.
3. THE COST HALF stays a printed pair, not a bound: median cycle and
   dispatches spent for the SAME job (the four vign_* stills) in each
   engine, quoted in the close-out beside the (b) reading. No number is set
   for "tolerable" because no series covers a UE scene with content yet;
   when both engines have the job landed the pair is put to Jafar with the
   blind reading, and a close that cannot quote the pair is not a close.

Rows in cycles.tsv from the compile-only lane (queue 032) carry the word
compile-only in whatWasEdited and are never pooled with full-loop rows: a
lane that does less is faster because it does less.
