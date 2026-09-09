#!/bin/bash
# Stop hook: THE TURN BOUNDARY IS WHERE A WAKE IS READ.
#
# WHY THIS EXISTS. Jafar, 2026-09-09, item 3, verbatim: "Wakes. A trigger that
# fires while the session is mid-turn is lost; it cost him yesterday's brief.
# Make wakes queue until the turn ends, and prove it."
#
# THE MEASUREMENT, off the scheduler's own record for trigger
# trig_013itgDeay6t41BHEmaYFbAj (cron 0 4 * * *, persist_session true):
#   last_run.status       ROUTINE_RUN_STATUS_SUCCEEDED
#   last_run.fired_at     2026-09-09T04:09:00.554885534Z
#   last_run.finished_at  2026-09-09T04:09:00.567166Z
# Twelve and a half milliseconds, reported SUCCEEDED. SUCCEEDED means the wake
# was DELIVERED, not that the work happened: the session was mid-turn, the
# injected user turn was absorbed into the running one, and the brief never
# existed. The platform's delivery semantics cannot be changed from inside this
# repository, so the wake stops being the only delivery: it is a durable record
# under production/wakes/ from the moment it is armed, and this hook is the
# boundary that reads it. A wake absorbed mid-turn then changes nothing.
#
# Contract (Claude Code Stop), read off the binary at /opt/claude-code/bin/
# claude on 2026-09-09 rather than remembered:
#   stdin:  { "hook_event_name":"Stop", "stop_hook_active":bool,
#             "session_id":..., "transcript_path":..., "cwd":...,
#             "last_assistant_message":? , "background_tasks":? ,
#             "session_crons":? }   # "Session-scoped cron tasks (CronCreate,
#                                   #  ScheduleWakeup, /loop) that will wake
#                                   #  this session later. Empty array when
#                                   #  none are scheduled."
#   exit 0  = let the turn end. Stdout is the hook's own line, on every
#             outcome, because an allow is not an error and a PASS painted on
#             stderr trains everyone to ignore stderr (the same reasoning as
#             verify-gate.sh, which is the house pattern here).
#   exit 2  = BLOCK the stop; stderr is fed to Claude as the reason.
#
# THE LOOP HAZARD IS REAL and three things bound it, two of them measured:
#   1. stop_hook_active, honoured by the tool (its exit 13). The binary's own
#      words: "check stop_hook_active in the input and return success while
#      it's true".
#   2. The platform overrides after 8 CONSECUTIVE blocks:
#      `let Ad=a.CLAUDE_CODE_STOP_HOOK_BLOCK_CAP??8; if(Ad>0&&_c>Ad)`. Its
#      notice goes to the transcript and nowhere a later session can read.
#   3. wake-queue.py's own cap of 3 blocks CUMULATIVE PER RECORD, which bites
#      first, on purpose, so the notice lands in the record (capBitAt) where
#      the next session can grep it. Exit 11, and it SAYS the cap bit.
# The real loop-breaker is that the work discharges its own record, so the next
# boundary finds nothing due.
#
# THE OPT-OUT, WAKE_DRAIN=off, AND IT IS NEVER SILENT (ruling 2026-09-09,
# section 8 A1). settings.json travels with the repository, so EVERY session in
# EVERY checkout drains the same records, including the `claude -p` that
# tools/runner/executor.py runs in an isolated worktree to answer a question
# Jafar sent from his phone. If the container's daily-brief record is due and
# undischarged at that moment, which is the normal state for hours after an
# absorbed 04:09 wake, that session's first Stop is BLOCKED and the model
# answering him is told to produce the day's brief instead: wrong session,
# wrong work, his answer delayed or bent. So the executor sets WAKE_DRAIN=off
# in the environment of its own invocation and this hook honours it: PERMIT,
# exit 0, and ONE line on stdout naming the reason and the count it chose not
# to block on (`wake-drain: PERMIT reason=opted-out dueOnDisk=N/M`). A silent
# permit is the failure the whole mechanism exists to prevent. The value is
# forwarded to the tool rather than judged here (see below); only the exact
# string `off` opts out, and every other value, including OFF and 0 and false
# and unset, BLOCKS.
#
# WHETHER STOP FIRES AT ALL UNDER `claude -p` is read off the binary the way
# the cap above was, not remembered, and it does: the one mode that turns
# hooks off names itself ("hooks are disabled in this mode (--bare)", and
# `--bare` is "Minimal mode: skip hooks, LSP, ..."), while `-p, --print`'s own
# help lists what print mode changes and hooks are not in it. The full reading,
# with the three quotations and the `--max-turns` branch the Stop payload
# shares, is in tools/wake-queue.py's docstring beside BLOCK_CAP. NOT OBSERVED:
# no `claude -p` was run to watch it; there is no CLI in this container.
#
# WHAT THIS HOOK DOES NOT DO, because a Stop hook here has a history
# (ledger-v2/studio-v2/learning.md L32, production/queue/014): it never asks
# for a commit, never reads the working tree, never mentions a clean tree. It
# drains wakes and nothing else.
#
# ONE FRICTION WORTH KNOWING ABOUT, said here rather than discovered at 3am: a
# BLOCK increments `blocks` in a tracked record file, so the tree is one file
# dirtier than it was and .claude/hooks/verify-gate.sh will want a re-run of
# verify before the next commit. That is the price of the counter surviving a
# container reclaim, and it only happens on a boundary where a wake was
# genuinely due.
#
# FAIL OPEN, DELIBERATELY AND OUT LOUD. Every unexpected outcome here lets the
# turn end. A broken drain that blocks is a session that can never end, which
# needs a human; a broken drain that permits delays a wake whose record is
# still on disk and still due at the next boundary. Recoverable against
# unrecoverable.
#
# Tested both ways, ACCEPTING CASE FIRST, by `python3 tools/wake-queue.py
# --selftest`, which runs THIS FILE as the hook (bash, the real payload shape
# on stdin, the env var below) rather than importing anything:
#   ACCEPT: an empty queue permits the stop and writes nothing to stderr; a
#           record not yet due permits; a discharged record permits; a record
#           armed before the turn and due during it BLOCKS with its
#           instruction and its discharge command in the reason;
#           stop_hook_active=true permits and names what stays due; the cap
#           bites after 3 blocks, permits, and says so; WAKE_DRAIN=off with a
#           DUE record permits, prints dueOnDisk=1/1, and counts no block,
#           while THE SAME RECORD without the opt-out blocks
#   REJECT: stdin that is not JSON permits and prints PERMIT-UNASSESSED; a
#           records path that is a file permits and prints "nothing measured"
# That suite runs at every commit from ledger/verify.py (TOOL_SELFTESTS).
#
# The block in .claude/settings.json that registers this file:
#
#     "Stop": [
#       {
#         "matcher": "",
#         "hooks": [
#           {
#             "type": "command",
#             "command": "WAKE_DIR=production/wakes bash .claude/hooks/wake-drain.sh",
#             "timeout": 15
#           }
#         ]
#       }
#     ]

# The records directory comes from the environment, named in settings.json, the
# same shape as QUEUE_FILE in session-start.sh and VERIFY_FOOTER in
# verify-gate.sh. A relative path is resolved against the REPOSITORY by the
# tool, never against the cwd: a hook is handed whatever directory the session
# happens to be standing in, and a queue that moves with the cwd is a queue
# that silently splits in two.
WAKE_DIR="${WAKE_DIR:-production/wakes}"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOL="$REPO/tools/wake-queue.py"

# THE TOOL MISSING IS NOT A REASON TO BLOCK, and it is not a reason to be
# silent either: a drain that cannot run is a wake nobody is serving.
if [ ! -f "$TOOL" ]; then
    echo "wake-drain: PERMIT-UNASSESSED reason=tool-missing tool=$TOOL | the" \
         "drain could not run, so no wake was examined. This is not a clean" \
         "queue; it is nothing measured."
    exit 0
fi

# THE PAYLOAD IS NOT RE-TYPED HERE AND NEITHER CHANNEL IS MERGED. The tool
# reads this hook's stdin itself, so the JSON parse lives in the tested layer
# with the arithmetic and the wording and there is no fourth bash JSON reader in
# .claude/hooks/ to drift from the other three. The tool's own split is kept:
# the one-line verdict with its denominators on stdout, the BLOCK reason on
# stderr, which is the channel Claude Code feeds back to the model. Merging them
# would have put the verdict line where only the model can see it and the reason
# where only a human can.
#
# THE OPT-OUT IS FORWARDED, NOT DECIDED HERE, for the same reason the payload
# is not re-typed here: the string comparison that turns a guard off belongs in
# the layer that has a selftest, beside the constant that spells the value and
# the line that prints it. This supplies live state and nothing else. The flag
# goes only when the variable is SET, so "never set" and "set to nothing" stay
# two facts rather than one empty string.
DRAIN=(drain --hook --dir "$WAKE_DIR")
if [ -n "${WAKE_DRAIN+set}" ]; then
    DRAIN+=(--wake-drain "$WAKE_DRAIN")
fi

python3 "$TOOL" "${DRAIN[@]}"
RC=$?

case "$RC" in
    10)
        # THE ONLY BLOCKING CODE. The reason is already on stderr.
        exit 2
        ;;
    15)
        # WAKE_DRAIN=off. THE OPT-OUT PERMITS, and its own line on stdout has
        # already said `reason=opted-out` with the count it did not block on.
        # Its own arm rather than a number in the list below, because a reader
        # of this file has to be able to see that the opt-out exists.
        exit 0
        ;;
    0|2|11|12|13|14)
        # Every permit has already printed its line, denominators and all.
        exit 0
        ;;
    *)
        # An exit code this hook does not model: a usage error (64), a crash,
        # a python that is not there. Fail open and SAY that the instrument,
        # not the queue, is what failed. Any traceback is already on stderr
        # above this line.
        echo "wake-drain: PERMIT-UNASSESSED reason=unmodelled-exit rc=$RC |" \
             "the drain did not report a verdict this hook understands, so" \
             "nothing was measured and the turn is allowed to end. This is" \
             "not an empty queue: any due record is still on disk."
        exit 0
        ;;
esac
