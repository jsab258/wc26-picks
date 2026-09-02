# Casebook: the build, the compile blind spots and the evidence channel

STATUS: LIVE. Verified 2026-09-01.

Moved out of CLAUDE.md on 2026-09-01 by task 013. This is the Unity-era
operating knowledge: the Game layer does not compile in the container, which
hides a specific family of errors until a round trip; the only feedback
channel that has ever worked here is a file committed by CI; and a build can
report success while having measured nothing.

The terse rules are in .claude/rules/ci.md. Note that the engine is an OPEN
question under ledger-v2/respec/decision-register/D1-engine-probe.md, so the
Unity specifics below are historic operating knowledge rather than settled
policy. The lessons about blind spots, allow-lists and evidence channels
outlive whichever engine wins.

---

<!-- moved verbatim from CLAUDE.md lines 766-787 on 2026-09-01, task 013 -->

## 12. If you cannot read the output, fix that before anything else

For one whole night I diagnosed this project by inference, because every
channel out of a CI job was blocked and I kept working around it instead of
repairing it:

- the log API returns a fixed ~4KB **byte** tail, so nothing mid-log is
  reachable and GitHub's own post-job cleanup fills that window every run;
- `get_check_run` returns the step summary EMPTY — and a comment in the
  workflow asserted that channel worked;
- artifacts are on a host this environment denies outright.

So three separate faults were diagnosed from a step's **duration** (2m10s of
retry sleep meaning six failed pushes) and from a branch that had not moved,
and a 291-byte artefact standing in for "the directory was empty". That is
divination, and I did hours of it before doing the ten-minute fix.

**The rule.** A blocked feedback channel is not an inconvenience to route
around, it is the highest-leverage bug on the board — fix it FIRST, and prefer
a channel this environment can definitely read. In this repo that means a file
in the repository. Everything since has been settled in seconds by
`game-design/sim-shots/`.

<!-- moved verbatim from CLAUDE.md lines 791-1070 on 2026-09-01, task 013 -->

## Project mechanics you will otherwise learn the hard way

**The Game layer does not compile here.** Only `Core` does. Locally you get
`ledger/verify.py` — lint, ShapeCheck (Roslyn, reference-independent
diagnostics only), stale-anchor detection, 2,884 CoreTests, and break-runs.
A type error against a Unity API is invisible until the Windows CI build, which
takes ~28 minutes. **Batch Game-layer changes; never claim a phase is done on a
local green.**

**AND SHAPECHECK WAS DISCARDING SYNTAX ERRORS, WHICH IS THE OPPOSITE FAULT AND
THE CHEAPER ONE.** 4 August: a missing `+` between two adjacent string literals
in `SimDirector` produced `CS1003: Syntax error, ',' expected`, the build died,
the sim never ran, and the question that build was dispatched to answer came
back unanswerable. ShapeCheck had reported ZERO errors on that same file
seconds earlier.

The cause was an ALLOW-LIST: `if (!interesting.Contains(d.Id)) continue`, a set
of diagnostic ids somebody thought to add. That is right for semantic
diagnostics — this compilation has no reference assemblies, so most of them are
noise about types it cannot see. It is indefensible for SYNTAX, which is the
one class that needs no references at all and is the cheapest, most certain
thing a parser can say.

Syntax diagnostics now come from the TREES rather than the compilation:
`SyntaxTree.GetDiagnostics()` returns exactly the parser's own errors, by
construction, with nothing semantic mixed in — no list to maintain and nothing
to forget to add. Tested both ways, and the rejecting case is the real error
put back: it lands on the same line and column CI reported.

**AND THE SAME PASTE HAD A SECOND ERROR AT ITS OTHER END, WHICH THE SYNTAX PASS
COULD NOT SEE EITHER.** One hour after the fix above, the next build died on
`CS0023: Operator '+' cannot be applied to operand of type 'string'` — a stray
leading `+` on a line whose predecessor already ended with one, which is unary
plus applied to a string. SEMANTIC, not syntactic, so the new tree pass was
blind to it and the allow-list swallowed it exactly as it had swallowed the
first. One edit, two compile errors, two round trips.

CS0023 is in the list now, and it was checked rather than assumed, because its
binary sibling CS0019 was tried once and REMOVED for false positives on Unity's
maths types. Run over the whole repository, where every hit is a false positive
by definition because CI compiles this code: zero. It fires on a UNARY operator
and the Unity comparisons that killed CS0019 are all binary.

The lesson generalises past this file. **An allow-list silently discards
everything nobody thought of, and it looks identical to a clean result.** That
is rule 3b — a zero needs a denominator — wearing a filter's clothes. And
fixing one hole in an allow-list does not fix the allow-list: the second error
was in the same paste, twenty lines away, and still got through.

**AND "REFERENCE-INDEPENDENT" IS THE PART THAT BITES.** ShapeCheck can run here
precisely because it does not need the assemblies — which means every diagnostic
that requires RESOLVING a name is invisible to it, not just Unity ones. Five
have now each cost a round trip, every one about a name that exists somewhere
other than where it was written:

| | | |
|---|---|---|
| CS0119 | `EvidenceHost.Watched` shadowed `Core.Watched` | `tools/lint-shadow.py` |
| CS0426 | `Mixing.Bus` — `Bus` is a SIBLING of `Mixing`, not nested | `tools/lint-nested.py` |
| CS0120 | a static body reaching an instance member | `tools/lint-static.py` |
| CS0103 | `TrafficHost.BrakeLampsPeak` — **there is no type called `TrafficHost`** | `tools/lint-filetype.py` |
| CS0118 | `Game.Campaign` in a static class — `Game` bound to the NAMESPACE | `tools/lint-namespace.py` |

The fifth is the family's purest form and cost two builds. Inside
`namespace Ledger.Game`, the bare identifier `Game` resolves to that namespace,
so writing `Game.Campaign.Noted(...)` in a class with no `Game` member compiles
the sentence against `Ledger.Game` and fails with "is a namespace but is used
like a variable". `PlayerController` has a real `public GameController Game`
field, which is why the shape reads as normal — and is also the accepting case
any lint for it must pass. The tell is unmistakable and greppable: a namespace
can never be compared to null, so `Game != null` in a file that declares no
`Game` member is the error every time.

The last is the cheapest of the four and the most embarrassing: `TrafficHost.cs`
declares `partial class GameController`, and so do thirteen other Game-layer
files. I took a type name off a FILENAME without opening the file. Measure
before writing the rule — fourteen files in that folder declare no type of
their own name, so it is a systemic trap rather than a slip.

These tools are name-matching rather than type-resolving, so they get written
twice: the first CS0426 version flagged thirteen call sites that compile
perfectly. **The live codebase is the accepting case and it is the best one
available — every hit on today's code is a false positive by definition**, so
the check needs no fixture to be trusted and cannot be fooled by one I wrote.
Run any new lint of this kind against the whole repository before believing it.

**AND RUN IT AGAINST THE ERROR IT WAS WRITTEN FOR, WHICH IS THE HALF THAT GOES
UNRUN.** `lint-filetype` passed the whole repository and then scored ZERO on the
very line that prompted it. The name was in the trap set, the pattern was right,
and the reference never reached either — because it lives inside `$"..."` and
the stripper removed every double-quoted run wholesale.

**`$"..."` IS CODE.** `SimDirector`'s done-line is one interpolated string
hundreds of expressions long and is the largest concentration of Game-layer
static reads in the project. `lint-shadow` had been throwing all of it away
since it was written, with a docstring approving of it — *"a verdict line with
`Traces.` in it is prose that happens to be quoted"*, which is true of a plain
string and false of an interpolated one. Every CS0119 in the done-line was
invisible. One idea, two implementations, and the second was found only because
the rejecting case was actually run.

**A "FAILED" BUILD IS USUALLY A RED GATE, NOT A BROKEN BUILD.** Checked 24
Aug after seeing two of the last three runs marked `failure` and briefly
reading that as a broken channel: the failing STEP is "Run game simulation",
and it ran its full twelve minutes and every step after it succeeded — stills
committed, verdict written, artifact uploaded. The sim exits non-zero when a
gate is red, which is correct, and GitHub then paints the whole job red.

So the Actions list shows a wall of failures on a project whose builds are
fine, and the distinction that matters is the one already in this file:
**`NO PLAYER LOG` means the sim did not run; `failure` on its own usually
means it ran and something it measured was out of bounds.** Read the verdict
before reading the run's colour — the colour is the least informative thing
about it.

**THE COST IS NEVER THE ERROR, IT IS THE COMMITS ON TOP OF IT.** CS0426 landed
and three more Game-layer commits went out before the verdict came back, so
three separate answers each moved a round trip further away. When a build comes
back `NO PLAYER LOG`, stop dispatching and fix it first.

**MEASURED PROPERLY ON 4 AUGUST, AND IT IS MUCH WORSE THAN THREE.** One wrong
type name — `TrafficHost.` for `GameController.` — rode **18 commits and killed
4 consecutive builds**. Every one of those builds was dispatched to answer a
different live question: whether the texture extraction worked, whether foot IK
ran, whether the typography change landed, whether the loiter guard held. All
four came back `NO PLAYER LOG` and answered nothing.

The multiplier is auto mode itself. Dispatching in parallel is right and it
means a compile error is not one lost round trip but every round trip until it
is noticed — and `NO PLAYER LOG` looks identical whether the cause is a compile
error or a licence seat, so the instinct is to blame contention and dispatch
again. **Read the COMPILE ERRORS block in the verdict before re-dispatching. It
is printed there for this exact case.**

**You can SEE and READ the game — use it.** Every Windows build commits four
stills and a verdict to `game-design/sim-shots/`, overwritten each run:

    review_day{1,2}_{noon,night}.jpg    what the street actually looks like
    verdict.txt                         the done-line, FAILING GATES, the sky
                                        readings, the places line, glyph and
                                        wardrobe counts, wheel proportions
    runs/<sha7>.txt                     the same verdict, kept per commit

`git pull` and read them. Do NOT try to tail the job log — see rule 12. The
verdict is committed, so `git log -- game-design/sim-shots/verdict.txt` gives a
HISTORY of measurements: that is how the AO ceiling was shown to be sitting
inside its own instrument's noise across five runs. Adding a number to that file
costs one line and pays for itself the first time a gate fails.

**DISPATCH BUILDS IN PARALLEL — BUT NOT MORE THAN ABOUT THREE.** The Windows job
is `workflow_dispatch` with no concurrency group, so nothing queues it, and that
is how a day of serial hypotheses turns into two waves. The limit is not the
runner, it is the **Unity Personal licence**: on 4 August, four builds dispatched
inside twenty minutes and **two of them died on "Activate Unity license", five
seconds in**, contending for a seat.

That failure is expensive out of all proportion because it is SILENT in the only
channel that can be read here. The job still commits a verdict, the verdict says
`NO PLAYER LOG — the sim did not run on this commit`, and that reads exactly like
a Game-layer compile error — the one class of fault that cannot be checked
locally. I read my own correct C# for several minutes before checking the step
list. The activation step now retries once after a pause, and the verdict names
both attempts, so the next occurrence is a line rather than a search. Five round trips on the
upside-down player cost two and a half hours because I sent one question at a
time when I could have sent three. Each run keeps its own `runs/<sha7>.txt`, so
concurrent builds are concurrent ANSWERS rather than one answer overwriting
another.

**A VERDICT VALUE MAY NOT CONTAIN A SPACE.** The file is space-separated
`key=value` and everything that reads it assumes that — `verdict-read.py`,
`verdict-keys.py`, and every grep anybody has ever typed at it. On 4 August
`crowdBodyWidth` was emitted as `0.45(narrowest 0.39 broadest 0.53)` and the
reader returned `0.45(narrowest`, silently, with no sign it had truncated
anything. That is the exact class of quietly-wrong answer `verdict-read.py`
exists to prevent, happening to the tool one layer down. Use `/` and `..`
(`0.45/0.39..0.53`) or a bracketed list, which the reader consumes whole.

**AND A REASON ON THE REACH LEDGER DECAYS EXACTLY LIKE A COMMENT.** The tool
proves an API has no caller; nothing proves the sentence explaining why is
still true. Three were wrong on 4 August alone — the bus route and the cab
ranks both described BEHAVIOUR as missing when it had been running for weeks
and the real gap was signage, and `TrafficSim.AwakeCount` claimed "the sim's
performance gate reads" it when nothing in the Game layer referenced it at
all. The pattern in all three is a reason describing the consumer somebody
INTENDED rather than one that exists, and a wrong reason sends the next person
at work that finished a fortnight ago. Read the entry AND the code.

**`verdict.txt` is the last run to LAND, which is not the newest commit.** Two
builds ran together and the one on the older commit finished second and laid
its output over the newer one's — so the file everything treats as "latest"
held the stale answer, and only the sha on line one said so. Runners here vary
by twenty minutes, so dispatch order tells you nothing about landing order. The
workflow now keeps whichever verdict came from the newer commit and lets the
loser contribute only its `runs/` file. **Check the sha on line 1 anyway**, and
when you dispatched a specific question, read `runs/<sha7>.txt` and not the
default.

**AND A BUILD THAT RENDERED NOTHING STILL COMMITS STILLS — ITS OWN CHECKOUT'S.**
The newer-wins rule above fixed which run's answer survives. It did not fix
what a run is allowed to claim as its answer, and on 4 August that cost the
morning. A build on `c61047f` came back `NO PLAYER LOG` with three compile
errors and its commit — "Sim stills from c61047f" — replaced all six JPEGs and
rewrote `frames.tsv`. It cannot have rendered anything. `git add
game-design/sim-shots` carried the directory it had CHECKED OUT, seven commits
behind the tip, so the branch went backwards and the frames landed indexed
under the sha of the build that failed to make them. **I opened all six and
read them as evidence about that commit.** The `verdict-keys.json` exclusion
was this same fault found earlier on one file, and excluding one file was too
narrow: "everything in the directory" is not a description of what a run
produced. `tools/sim-shots-stage.sh` now names the output — always the verdict
and the per-run copy, the stills only if the sim reached a screenshot, the
ledger only if it wrote one.

So the still-reading rule gains a first step: **read line 1 and the `NO PLAYER
LOG` line before looking at any frame.** A picture in this directory is only
evidence about the commit named beside it if that commit ran.

**THE CONTAINER ROLLS THIS CHECKOUT BACK, AND IT DOES NOT LOOK LIKE THAT.**
Three times on 19 August the working tree reset to `cacebe2` while origin held
several more commits. Nothing was lost — everything here is pushed the moment it
goes green — and the whole cost was the DIAGNOSIS, because every symptom reads
as a code problem first:

  * `gamecheck` said 168 files where it had said 172 twenty minutes earlier,
    with no deletions anywhere in git;
  * `git status` showed `queue.md` MODIFIED, carrying two dozen lines of
    retired content dated six days back that nobody had written that day;
  * a grep for a queue item added an hour before came back empty.

Four files vanishing from a compile is alarming, and a document silently
reverting is alarming, and both are completely explained by the checkout having
moved underneath the process. The first occurrence cost the better part of an
hour before the cause was even suspected.

**`python3 tools/resync.py` says ROLLED BACK in its first line, and `--fix`
resets to origin.** It only acts when HEAD is a strict ANCESTOR of origin — the
rollback signature, and the one state in which a hard reset can lose nothing —
and it REFUSES when the tree is ahead, because that is unpushed work and the
answer there is to push it. Tested against all four states.

**The habit that makes it free: commit and push as soon as a thing is green.**
Every rollback so far has cost nothing because of that and nothing else.

**Always run `ledger/verify.py` before committing, and PASTE THE FOOTER FROM
THE FILE.** A green run writes `ledger/.verify-footer`; a red run deletes it.

    python3 ledger/verify.py && git commit -F - <<EOF
    ...
    $(cat ledger/.verify-footer)
    EOF

**AND WRITE THE MESSAGE TO A FILE, NOT INTO AN UNQUOTED HEREDOC.** Twice now a
message containing a `backticked` identifier has been fed to `<<EOF` and the
shell has EXECUTED the word, committing a sentence with a hole in it — the
second time inside a paragraph about instruments quietly losing information.
`<<'EOF'` quotes it, but then `$(cat ledger/.verify-footer)` does not expand
either. So: write the prose to a file with no shell in the loop, `cat` the
footer onto the end, and commit with `-F`. Both halves work and neither can eat
a word.

It exists because I put unmeasured test counts in two commit messages, and the
FILE exists because printing "NOT GREEN — do not paste this into a commit
message as if it were" underneath the footer did not stop me doing it a third
time. The message gets written before the check finishes, from a footer already
in the scrollback, and a warning printed afterwards cannot reach a decision
already made. Paste from the file and a red run has nothing to give you.

**HuggingFace and most external hosts are blocked from this container** (403
through the proxy). Anything corpus-related must go through CI, so make each
run maximally informative rather than a single blind attempt.

**Verify a workflow's effects, not just its exit code.** A CI job here has
reported success while: deleting the clips, pushing nothing, producing zero
output for every character it was asked for, and committing a truncated log.

**Branch:** `claude/game-dev-ai-automation-2h67ix`. Never open a PR unless
asked. Never make a purchase or use an account — every purchase is Jafar's.

**Voice sourcing consent rule:** only corpora whose contributors donated their
voices to build speech technology, and **no identifiable public figures, ever.**
