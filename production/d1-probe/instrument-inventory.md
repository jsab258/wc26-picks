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
