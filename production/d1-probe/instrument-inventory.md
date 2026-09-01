# D1 measurement c: what a move to UE5 costs in instruments

STATUS: measured 2026-09-01, no engine required. This is the honest input to
D1's measurement c, taken by counting rather than by estimating.

## The headline, and why the obvious count is misleading

Of the 54 check functions in ledger/verify.py, only SIX name a Unity-specific
token, and all six name only the PATH `Assets/`, never a Unity API. Read
alone, that number says the instruments are almost engine-neutral and a port
is a path change.

That reading is wrong, and it is wrong in the direction that would flatter
the move. The coupling is not to the ENGINE, it is to the LANGUAGE. Of 49
scripts in tools/, TWENTY-FIVE read C# source directly: every lint
(lint-static, lint-nested, lint-shadow, lint-namespace, lint-filetype,
lint-avenues, lint-conditional-reach, lint-unreached), the reach and gate
readers, shape-check with its Roslyn pass, and the content readers that parse
C# literals. None of those survive a move to C++ as a path change; each is a
parser aimed at a language that would no longer be there.

## The count, with its denominator

| set | examined | PORTS (path change) | REBUILDS (language) |
|---|---|---|---|
| verify.py check functions | 54 | 48 | 6 name `Assets/` paths, trivial |
| tools/*.py | 49 | 24 | 25 |
| Core under test | 98 files, 32,554 lines | transliteration, not a port | |
| CoreTests | 5 files, ~130 test methods, 4,163 assertions at last run | transliteration | |

## The verdict for the decision record

PORTS: the verdict channel and its readers, the screenshot pipeline's
consumers, the doc and queue checks, the license and canon gates, the
throughput and ledger tooling. These read files and text, not code.

REBUILDS: 25 of 49 tools, because they are C# parsers. Plus the Core itself
(32,554 lines) and its test suite (~130 methods carrying 4,163 assertions),
both of which D1 already calls transliteration rather than rewrite, and which
the existing suite guards on the way across.

UNKNOWN, and named rather than guessed: whether the sim's verdict emission
can be reproduced in UE such that the existing readers keep working
unchanged. That is the single largest lever on this number, because the
readers are most of what PORTS. It is answerable only on the machine, during
the UE half of the probe, and it should be the first thing that half checks.

## What this contributes to D1

Measurement c is a COST, not a preference, and it is roughly: half the tool
surface rewritten, the Core and its tests transliterated under guard, the
evidence channel unknown until tested. That cost is real but it is not
disqualifying on its own; D1's rule turns on (b) being decisively better with
(a) tolerable, and this number belongs in the "what it costs to say yes"
column rather than in either of those.


## Addendum 2026-09-01: measurement a, the setup cost, now partly measured

The UE path's setup cost is no longer an estimate. Measured on the machine:

| step | cost | how it was taken |
|---|---|---|
| UE 5.8.2 install | manual, Jafar, one launcher bug in the way | the launcher offered no engine version until a free Samples item was taken; a known bug, thirty seconds once researched, and hours before that |
| MSVC build tools | 2.9 minutes, exit 0, VERIFIED 17.14.37614.0 | automated, one workflow, idempotent, bootstrapper not winget |
| probe round trip | about 90 seconds per run | three runs, wall clock from push to result committed |

MY ESTIMATE OF THE MSVC INSTALL WAS WRONG BY AN ORDER OF MAGNITUDE. I said
tens of minutes; it took 2.9. Recorded because rule 7 says name what
dominates or do not give a number, and I gave a number that dominated
nothing. The download is 4.5 MB of bootstrapper; the workload itself came
down fast on that connection.

WHAT THIS DOES TO THE COMPARISON, stated carefully because a fast install is
not the same as a cheap engine. Setup cost for the UE path is now roughly:
one large engine download, one launcher bug that cost a human evening, and
three automated minutes of toolchain. Unity needed none of it because it was
already there, which is momentum rather than an engine property, and D1's
rule already accounts for that by giving ties to Unity. The number that will
actually decide measurement a is the EDIT-BUILD-TEST cycle, not the install,
and that is still unmeasured on the UE side.
