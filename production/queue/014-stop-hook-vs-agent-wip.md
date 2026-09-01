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
