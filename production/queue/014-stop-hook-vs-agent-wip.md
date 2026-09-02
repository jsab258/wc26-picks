line: infrastructure (governance)
spec: this file
acceptance: the stop hook stops demanding a clean tree while a builder agent is running, or the resident has a supported way to mark a path as agent work in progress; the constitution's rule is unchanged and the hook stops contradicting it
max_sessions: 1

TWO RULES DISAGREE AND NOTHING RECONCILES THEM.

CLAUDE.md, THE STUDIO SPLIT: "Agents' uncommitted work-in-progress is NOT
committed under them by a stop-hook's nagging; the tree goes clean in one
reviewed commit per builder report."

The stop hook, on every turn while a builder is running: "There are untracked
files in the repository. Please commit and push these changes."

The constitution wins and the resident held. But it fired twice in three
minutes on 2026-09-01 while the dashboard builder was mid-build, and a rule
that has to be consciously defended on every turn is a rule waiting to lose
one. THAT IS NOT HYPOTHETICAL HERE: the studio split was skipped for an
entire day earlier the same day, because a session-level instruction
outranked the constitution quietly and nobody raised the conflict. This is
the same shape with a hook in the instruction's place, and the pressure runs
toward the wrong answer, because committing is the action that makes the
nagging stop.

The fix is to make the hook aware, not to make the human stronger. Options,
in the order they look right:
1. The hook consults the spawn log and stays quiet when an agent row has no
   matching completion. Cheapest and needs no new state.
2. A marker file the resident writes when it spawns and removes when it
   commits the batch. More moving parts and it can go stale.
3. Path-based exemption. Brittle: it needs updating for every new builder.

Whatever is chosen, the hook's message should say WHY it is quiet rather
than simply not firing, because a check that goes silent is
indistinguishable from a check that is broken.

## MEASURED 2026-09-01 23:55Z by the resident: option 1 cannot work as written

It fired three more times tonight, on three consecutive turns, while two and
then three builders held the tree. So the pressure this item predicts is not
hypothetical and is now the commonest single event in a working session.

Before building option 1, I opened the two things it depends on.

**The hook is `~/.claude/stop-hook-git-check.sh`, OUTSIDE this repository.**
It reads only git state: `git diff --quiet`, `git diff --cached --quiet`, and
`git ls-files --others --exclude-standard`. It knows nothing about agents and
there is no in-repo file it currently consults. So no change committed to
this repository can quiet it by itself; any repo-side fix has to be a file
the hook is taught to read, which means the hook changes too.

**`.claude/agent-log.tsv` HAS TWO COLUMNS, `when` and `agent`.** Every row is
a spawn. There is no completion row, no end timestamp, no status. So option
1, "the hook consults the spawn log and stays quiet when an agent row has no
matching completion", has nothing to match against: every row in the file
looks identical to a row whose agent is still running, forever. Implemented
as written it would go quiet permanently after the first spawn, which is the
worst outcome available here, because a check that is silent is
indistinguishable from a check that is broken. This item's own closing
sentence says exactly that.

THIS IS THE SPAWN-LOG HOLE AGAIN, third instance. It was found in
`director_cadence` (a spawn cleared the gate without a review), fixed there
by testing an ARTIFACT, the ruling record, rather than attendance. The
watchdog's dailies check still has it. Now option 1 here proposes it a third
time, in a queue item written by someone who knew about the first two. The
log is an attendance register; it cannot answer any question of the form "did
that finish".

So the shortlist reorders, and the reasons are now measured rather than
guessed:

- Option 2, a marker the resident writes at spawn and clears at commit, is
  the only one of the three that carries the fact the hook needs. Its named
  weakness is staleness, which is boundable: the marker carries the spawn
  time and the agent name, and the hook SAYS how old it is and nags anyway
  past a bound. A marker that can go stale silently is the same fault again.
- Option 1 is dead unless the log grows a completion column, which is a
  bigger change than this item and would fix the watchdog too. If anyone
  takes that on, it is one instrument for three consumers and should be
  scoped as such rather than as a hook fix.
- Option 3 is unchanged and still brittle.

NOT BUILT TONIGHT, deliberately. A builder holds `CLAUDE.md` and the studio
framework docs right now, and this item edits governance. Two concurrent
rewrites of the rules would be the mistake this whole item is about.

## RULED 2026-09-02 (director, decision-2026-09-02-constitution-cut-attribution-pc-channel.md, Ruling 7)

The resident's measurement is accepted: two columns, every row a spawn, and
option 1 implemented as written goes silent for ever. This is the attendance
hole for the third time and it is worth one instrument, which is queue 024,
not this item.

FIRST STEP OF THIS ITEM, before anything else: the stop hook lives at
`~/.claude/stop-hook-git-check.sh`, OUTSIDE this repository, so no claim
about what it does can be checked from the tree. Record its text in
`production/stop-hook.md` under the same contract the watchdog prompt has:
when the hook changes, that file changes in the same commit, or the claim
goes back to being unverifiable. Do this before anyone teaches the hook to
read anything.

UNTIL 024 LANDS: the constitution wins, the resident holds, and the nag is a
NAMED FALSE POSITIVE rather than a thing to be resolved on the night. When
the hook is finally taught to stay quiet, it prints WHY it is quiet, per this
item's own closing sentence.
