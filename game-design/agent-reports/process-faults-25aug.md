# Three process faults found by running four agents at once

> **STATUS — LOG, 2026-08-25. NOT CURRENT** once the fixes below land.
>
Coordinator account. Written against Jafar's gate for overnight autonomy
(*"we need to get the process right, no waste of tokens and max output,
before we let this run autonomously all night"*). Every number below was
read this session, not recalled.

---

## 1. EVERY AGENT STOPPED ONE SENTENCE SHORT OF FINISHING — 4 of 4

The expensive one. Four agents were spawned in parallel and **all four
hit their turn limit and stopped mid-task**, each with a line announcing
the work it was about to do:

| agent | tool uses | tokens | stopped saying |
|---|---|---|---|
| fixture unpinning | 30 | 112,671 | "That's a real gap; fixing it." |
| ref-bench audit | 25 | 123,380 | "Now the rest of the instrument." |
| plinth unwrap | 30 | 74,428 | "Now the two deletions." |
| dark-CI channel | 35 | 87,881 | "Now the workflow." |

**~398,000 tokens spent, zero tasks delivered on the first pass.** Every
one had done the reading, formed the plan, and stopped before the edit —
the most expensive possible place to stop, because the reading is the
part that does not survive if the agent is not resumed.

They were all recoverable: `SendMessage` to the agent id resumes it with
its context intact, and all four then proceeded. So the cost was one
round of coordinator attention, not the tokens. **But an unattended loop
overnight would not have resumed them.** It would have read four
completion notifications, found the tree half-edited, and either
committed partial work or re-spawned agents to redo the reading.

**Cause: my briefs, not the agents.** The four prompts averaged ~700
words and each carried a full rationale, the project rules that applied,
and a list of hard requirements. That is the right CONTENT — the
verifiers' value comes from knowing why — but it consumes turns before
any work starts.

**Fixes, in order of cheapness:**
1. **Put standing constraints in the agent definition, not the brief.**
   "Do not commit", "run verify", "grep the twin", "report to a file"
   are true of every builder task in this project and are currently
   retyped into every brief.
2. **One deliverable per spawn.** The dark-CI brief carried a structural
   workflow fix AND a wire-or-allowlist decision AND an archaeology
   question. That is three tasks.
3. **Say the budget in the brief** — "you have ~30 tool calls, spend at
   most a third on reading" — so the agent paces itself rather than
   discovering the wall.
4. **Never leave a stopped agent unresumed.** A completion notification
   whose text ends in an intention is a STOPPED agent, not a finished
   one. Overnight this needs to be mechanical: if the summary does not
   report a result, resume rather than proceed.

## 2. THE SCRATCHPAD IS SHARED, AND A FIXED FILENAME IS A COLLISION

The session scratchpad is shared with every spawned agent — proven by
its contents: `bandsheet.png`, `cm_fixture.py`, `probe1-7.py`,
`*.keep` backups, all written by agents during this session.

I write commit messages to a file there (the CLAUDE.md rule that a
message must not go through an unquoted heredoc, because the shell has
twice EXECUTED a backticked identifier out of one). The filename was
`msg.txt`. Between writing it and committing, it was overwritten, and
**the commit landed carrying a different commit's message entirely** —
a duplicate of `7cbb214f`'s, describing frame-drift work not in the
diff. Caught by reading the commit back; amended before pushing.

The file's mtime sits inside another agent's active window, and the
scratchpad demonstrably holds other agents' files, so a collision is
the explanation that fits. I have not proven WHICH agent wrote it and
am not claiming one.

**Fix, applied:** commit-message files now carry the sha in the name
(`msg-coordinator-<sha>.txt`). The general rule: **anything the
coordinator writes to the shared scratchpad needs a unique name**, and
anything read back after any delay needs reading back, not assuming.

The deeper point is the one this project keeps paying for: an
instrument that quietly loses information looks identical to one that
worked. `git commit -F` cannot tell a stale file from a fresh one.

## 3. THE COMMIT GATE ASSUMES ONE WRITER

`verify-gate.sh` blocks a commit unless the verify footer is fresher
than every changed file. That is correct and it has teeth — it caught a
real staleness twice this session.

With four agents editing, **the tree is almost never stable long enough
for a whole-tree footer to describe it.** Two commit attempts were
blocked by files a live agent was mid-edit on, neither of which was in
the path-scoped commit being made. A message-only `--amend`, which
changes no tracked content at all, was blocked the same way.

Not a bug — the gate is doing what it was built to do, against a
workload it was not built for. But overnight, an unattended loop that
cannot commit will accumulate work in a container that gets reclaimed,
which is the failure mode the "commit as soon as it is green" habit
exists to prevent.

**Candidate fixes, none applied yet — this needs the both-ways test
before it is trusted, and loosening a gate is exactly what rule 2
forbids doing casually:**
- Scope freshness to the PATHS being committed. Weaker, and arguably
  still honest: verify's whole-tree checks did pass over a tree
  containing those paths.
- Allow a message-only `--amend` when `git diff --cached --quiet`
  passes, since it changes no content.
- Serialize: hold a lock so only one writer edits at a time. Safest,
  and it gives up most of the parallelism.

Recommendation: the second is unambiguously safe and small. The first
needs a decision, because it genuinely weakens the guarantee.

---

## What this means for overnight

The loop is not ready to run unattended tonight on this evidence. Fault
1 is the blocker: an unattended coordinator would have banked ~398k
tokens of reading and delivered nothing, four times. Fault 1's fixes 1
and 4 are small and mechanical, and both are testable before dark.
