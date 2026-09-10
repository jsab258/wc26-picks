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
# MODEL, REASON AND AGENTID COLUMNS, added 2026-09-10 for Jafar's model-
# routing ruling, enforcement section (E2) of
# game-design/decision-2026-09-10-ruling-model-routing.md: "the spawn log
# gains a model column ... an upward override carries a written reason in
# that row." Header, from 2026-09-10 on:
#
#     when  agent  model  reason  agentId
#
# MODEL RECORDS WHAT WAS ASKED FOR, NOT WHAT RAN, and a reader who forgets
# that will misread this column in a month. Measured the day this landed:
# the SubagentStart payload carries no model field (branch 1 below is
# dormant), so absent a `.claude/spawn-intent` sidecar the value written is
# the AGENT DEFINITION'S OWN DECLARATION (branch 3) — correct behaviour for
# this design, and indistinguishable in the row from "this is what the model
# actually ran at" unless a reader already knows the fallback order below.
# `instrument-builder opus` logged at 2026-09-10T15:57:27Z while the spawn
# itself ran on sonnet (director-supplied, no sidecar written) is the
# worked example: declared-versus-ran is a JOIN against
# `.claude/agent-turns.tsv`'s `tier` column on `agentId`, not a read of this
# column alone: `tools/spawn-cost.py --routing-drift` is that join, reading
# "what ran" from `.claude/agent-turns.tsv` and "what was asked for" from
# the current `.claude/agents/*.md`, never from this column alone.
#
# MODEL, in this order, first one that answers wins (measured against the
# Claude Code binary before writing this: the SubagentStart payload is
# documented, in its own strings, as "JSON with agent_id and agent_type" —
# no model field today, so branch 1 below is dormant but checked anyway
# rather than assumed absent forever):
#   1. a `.model` field on the SubagentStart payload itself, if the harness
#      ever adds one;
#   2. `.claude/spawn-intent`, ONE LINE the resident writes immediately
#      before the spawn: `agent=<type> model=<tier> reason=<up:token>` —
#      consumed (read, then deleted) only by the hook run whose `agent_type`
#      matches the file's `agent=`, so an intent meant for one spawn is never
#      picked up by an unrelated one that merely happened to fire first;
#   3. the `model:` line in `.claude/agents/<agent_type>.md`;
#   4. the literal word `none`, for a built-in agent_type with no definition
#      file on disk (measured fact, never a guess — rule 3b).
#
# REASON is computed by comparing the chosen MODEL against the DEFINITION's
# own declared model (step 3 above, read regardless of which branch supplied
# the final MODEL, purely as the baseline to compare against):
#   - `default`   MODEL equals the declared model (including when declared
#                 is `none`: there is no baseline to deviate from)
#   - `down`      MODEL ranks BELOW declared — free, and recorded as fact
#   - the intent file's own `reason=` token, when an upward MODEL was
#     supplied BY a matching, consumed intent file
#   - `up:MISSING`, never a blank, when MODEL ranks ABOVE declared but no
#     matching intent file supplied a reason token
#
# DATA ROWS ARE NEVER REWRITTEN: the header is appended only when the log is
# absent, so every row already on disk keeps the exact bytes it was written
# with — no row's agent, model or reason is ever backfilled with a guess
# (rule 3b). The HEADER is the one line this is not true of: on 2026-09-10,
# once the column count it promised stopped matching the widest row actually
# being written, the live file's first line was hand-corrected from
# "when\tagent" to the five-column header above — a METADATA correction, not
# a measurement, and the reason it is safe is the same reason every reader
# below already reads columns by POSITION with a length guard rather than by
# counting against the header: the 529 two-column rows that predate this
# ruling, the handful of short rows from this hook's own intermediate
# drafts, and every five-column row from now on all read correctly whether
# the header names five columns or two.
#
# Contract (Claude Code SubagentStart):
#   stdin:  { "agent_id": "...", "agent_type": "systems-builder", ... }
#   exit 0  = proceed. This hook NEVER blocks: a broken audit trail must not
#             be able to stop the work it is only there to describe.
#
# Tested both ways (rule 5b) by .claude/hooks/selftest.sh:
#   ACCEPT: JSON carrying agent_type appends exactly one well-formed row,
#           with its model looked up from a fixture definition file, and a
#           spawn-intent fixture consumed correctly (and only by the
#           matching agent_type)
#   REJECT: malformed stdin exits 0 and appends nothing — the file it is
#           auditing cannot be corrupted by garbage arriving at it

LOG="${AGENT_LOG:-.claude/agent-log.tsv}"
INTENT="${AGENT_SPAWN_INTENT:-.claude/spawn-intent}"

INPUT=$(cat)
if command -v jq >/dev/null 2>&1; then
    AGENT=$(printf '%s' "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null)
    AGENT_ID=$(printf '%s' "$INPUT" | jq -r '.agent_id // empty' 2>/dev/null)
    PAYLOAD_MODEL=$(printf '%s' "$INPUT" | jq -r '.model // empty' 2>/dev/null)
else
    # Same fallback shape as verify-gate.sh: this hook must work on a
    # container where jq was never installed, and a silently-skipped audit
    # line is indistinguishable from a session that delegated nothing.
    AGENT=$(printf '%s' "$INPUT" \
        | grep -oE '"agent_type"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' \
        | head -1 | sed 's/^"agent_type"[[:space:]]*:[[:space:]]*"//; s/"$//')
    AGENT_ID=$(printf '%s' "$INPUT" \
        | grep -oE '"agent_id"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' \
        | head -1 | sed 's/^"agent_id"[[:space:]]*:[[:space:]]*"//; s/"$//')
    PAYLOAD_MODEL=$(printf '%s' "$INPUT" \
        | grep -oE '"model"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' \
        | head -1 | sed 's/^"model"[[:space:]]*:[[:space:]]*"//; s/"$//')
fi

# NOTHING PARSED, NOTHING WRITTEN. A row with an empty agent column would
# read as "an agent with no name ran", which is a finding; the truth is that
# this hook could not tell, and those must not look the same (rule 3b).
[ -n "$AGENT" ] || exit 0

# A TAB IN A VALUE WOULD SPLIT THE ROW, the same fault as a space in a
# verdict value — every reader of this file splits on tabs. Newlines likewise.
AGENT=$(printf '%s' "$AGENT" | tr '\t\n\r' '   ')
AGENT_ID=$(printf '%s' "$AGENT_ID" | tr '\t\n\r' '   ')
PAYLOAD_MODEL=$(printf '%s' "$PAYLOAD_MODEL" | tr '\t\n\r' '   ')

# ONE FRONT-MATTER KEY (model), read from the SAME block every commit's E1
# check reads: between the first two bare "---" lines. Outside that block is
# prose and must never be matched — a body paragraph that happens to start a
# line with "model:" is not a routing decision.
fm_value() {   # $1=file $2=key  ->  the value after "key:" in front matter
    awk -v k="$2" '
        BEGIN { delim = 0 }
        /^---[[:space:]]*$/ { delim++; if (delim == 2) exit; next }
        delim == 1 {
            n = length(k) + 1
            if (substr($0, 1, n) == k ":") {
                v = substr($0, n + 1)
                sub(/^[[:space:]]+/, "", v)
                sub(/[[:space:]]+$/, "", v)
                print v
                exit
            }
        }
    ' "$1" 2>/dev/null
}

DEFFILE=".claude/agents/${AGENT}.md"
DECLARED="none"
[ -f "$DEFFILE" ] && D="$(fm_value "$DEFFILE" model)" && [ -n "$D" ] && DECLARED="$D"

# THE SPAWN-INTENT FILE: one line, `agent=<type> model=<tier> reason=<token>`,
# written by the resident immediately before the spawn it describes.
# CONSUMED ONLY BY A MATCHING agent_type, and only then deleted — an intent
# meant for a spawn that has not fired yet must survive an unrelated spawn's
# hook run reading past it.
INTENT_MODEL=""
INTENT_REASON=""
INTENT_CONSUMED=0
if [ -f "$INTENT" ]; then
    LINE=$(head -1 "$INTENT" 2>/dev/null)
    IA=$(printf '%s' "$LINE" | grep -oE 'agent=[^ ]*' | head -1 | cut -d= -f2-)
    if [ "$IA" = "$AGENT" ]; then
        INTENT_MODEL=$(printf '%s' "$LINE" | grep -oE 'model=[^ ]*' | head -1 | cut -d= -f2-)
        INTENT_REASON=$(printf '%s' "$LINE" | grep -oE 'reason=[^ ]*' | head -1 | cut -d= -f2-)
        INTENT_CONSUMED=1
        rm -f "$INTENT" 2>/dev/null
    fi
fi

# MODEL: first of payload / consumed intent / declared / "none" that answers.
if [ -n "$PAYLOAD_MODEL" ]; then
    MODEL="$PAYLOAD_MODEL"
elif [ "$INTENT_CONSUMED" = 1 ] && [ -n "$INTENT_MODEL" ]; then
    MODEL="$INTENT_MODEL"
else
    MODEL="$DECLARED"
fi

# THE LADDER, for "above" and "below" only — haiku < sonnet < opus < fable.
rank_of() {
    case "$1" in
        haiku) echo 0 ;; sonnet) echo 1 ;; opus) echo 2 ;; fable) echo 3 ;;
        *) echo "" ;;
    esac
}

if [ "$DECLARED" = "none" ]; then
    # No baseline to deviate from: nothing here is an "override" of anything.
    REASON="default"
elif [ "$MODEL" = "$DECLARED" ]; then
    REASON="default"
else
    RM=$(rank_of "$MODEL")
    RD=$(rank_of "$DECLARED")
    if [ -z "$RM" ] || [ -z "$RD" ]; then
        # A MODEL or DECLARED value off the four-value ladder cannot be
        # ranked; E1 owns refusing that fault at the definition. Recorded as
        # "default" here rather than guessed at as up or down.
        REASON="default"
    elif [ "$RM" -lt "$RD" ]; then
        REASON="down"
    else
        # UPWARD. The intent's own reason token wins when a matching intent
        # supplied one; otherwise the sentinel, NEVER a blank (rule 3b).
        if [ "$INTENT_CONSUMED" = 1 ] && [ -n "$INTENT_REASON" ]; then
            REASON="$INTENT_REASON"
        else
            REASON="up:MISSING"
        fi
    fi
fi

# SAME SANITISING AS THE AGENT COLUMN: no value may carry a tab or a newline
# into the row, or every later split-on-tab reader misreads it.
MODEL=$(printf '%s' "$MODEL" | tr '\t\n\r' '   ')
REASON=$(printf '%s' "$REASON" | tr '\t\n\r' '   ')

mkdir -p "$(dirname "$LOG")" 2>/dev/null
# The header is created only when absent, so an existing log is never
# rewritten — this file is append-only by construction (rule 5: look before
# you destroy, and scope the write to exactly what this spawn produced).
[ -s "$LOG" ] || printf 'when\tagent\tmodel\treason\tagentId\n' >> "$LOG"
printf '%s\t%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$AGENT" "$MODEL" "$REASON" "$AGENT_ID" >> "$LOG"

exit 0
