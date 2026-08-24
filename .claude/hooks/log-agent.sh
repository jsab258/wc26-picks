#!/bin/bash
# SubagentStart hook: append one line per agent spawn to .claude/agent-log.tsv.
#
# WHY THIS EXISTS. CLAUDE.md's THE STUDIO SPLIT (24 Aug, Jafar) says the
# director does not implement — "spawning is the default, not the exception" —
# and it was adopted precisely because the main session had spent a day doing
# builder work inline and burning usage on it. That rule shipped with NO
# INSTRUMENT: whether any given day's work was actually delegated could only be
# answered by reading a transcript, which is exactly the state rule 6 describes
# (a system built, plausible, and never once running) and rule 5b's corollary
# describes one layer out (a rule whose compliance nobody can measure).
#
# This log makes "did the director actually delegate, and to whom" a
# one-command check:
#
#     cut -f2 .claude/agent-log.tsv | sort | uniq -c | sort -rn
#
# COMMITTED, NOT IGNORED. The log IS the instrument, and an instrument that
# lives only in an ephemeral container is one the next session cannot read —
# the same argument that put `game-design/sim-shots/` in the repository (rule
# 12: prefer a channel this environment can definitely read, and in this repo
# that means a file in the repository).
#
# Contract (Claude Code SubagentStart):
#   stdin:  { "agent_type": "systems-builder", ... }
#   exit 0  = proceed. This hook NEVER blocks: a broken audit trail must not
#             be able to stop the work it is only there to describe.
#
# Tested both ways (rule 5b) by .claude/hooks/selftest.sh:
#   ACCEPT: JSON carrying agent_type appends exactly one well-formed row
#   REJECT: malformed stdin exits 0 and appends nothing — the file it is
#           auditing cannot be corrupted by garbage arriving at it

LOG="${AGENT_LOG:-.claude/agent-log.tsv}"

INPUT=$(cat)
if command -v jq >/dev/null 2>&1; then
    AGENT=$(printf '%s' "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null)
else
    # Same fallback shape as verify-gate.sh: this hook must work on a
    # container where jq was never installed, and a silently-skipped audit
    # line is indistinguishable from a session that delegated nothing.
    AGENT=$(printf '%s' "$INPUT" \
        | grep -oE '"agent_type"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' \
        | head -1 | sed 's/^"agent_type"[[:space:]]*:[[:space:]]*"//; s/"$//')
fi

# NOTHING PARSED, NOTHING WRITTEN. A row with an empty agent column would
# read as "an agent with no name ran", which is a finding; the truth is that
# this hook could not tell, and those must not look the same (rule 3b).
[ -n "$AGENT" ] || exit 0

# A TAB IN THE VALUE WOULD SPLIT THE ROW, the same fault as a space in a
# verdict value — every reader of this file splits on tabs. Newlines likewise.
AGENT=$(printf '%s' "$AGENT" | tr '\t\n\r' '   ')

mkdir -p "$(dirname "$LOG")" 2>/dev/null
# The header is created only when absent, so an existing log is never
# rewritten — this file is append-only by construction (rule 5: look before
# you destroy, and scope the write to exactly what this spawn produced).
[ -s "$LOG" ] || printf 'when\tagent\n' >> "$LOG"
printf '%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$AGENT" >> "$LOG"

exit 0
