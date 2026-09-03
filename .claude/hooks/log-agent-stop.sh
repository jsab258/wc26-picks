#!/bin/bash
# SubagentStop hook: append one row per FINISHED spawn to
# .claude/agent-turns.tsv, carrying the model tier and the turn count.
#
# WHY THIS EXISTS. `.claude/agent-log.tsv` records one row per spawn and
# nothing else, so the only statistic it can support is a flat average, and
# every estimate in this project rests on "a spawn costs 1.5 to 2 points" --
# a number that averages a 12-turn fable reviewer with a 45-turn opus builder.
# Measured from the transcripts on this machine on 2026-09-03: fable median 12
# turns, opus median 45, opus peak 138. Jafar asked for tier and turns at
# SubagentStop "so calibration is per tier and turns rather than per spawn".
#
# WHY A SECOND FILE AND NOT A COLUMN ON THE FIRST. `.claude/agent-log.tsv` is
# written at SubagentSTART and is read by `director_cadence` in
# ledger/verify.py as the spawn census: every row is one spawn. A stop row
# appended to that same file would double every count it takes, silently, and
# the gate would go on printing confident numbers. Two files, one row each per
# event, joined on agentId.
#
# Contract (Claude Code SubagentStop), read off the binary rather than assumed:
#   stdin: { "hook_event_name":"SubagentStop", "agent_id":..., "agent_type":...,
#            "agent_transcript_path":..., "stop_hook_active":..., ... }
#   THERE IS NO MODEL FIELD AND NO TURN COUNT FIELD. Both are derived from the
#   transcript at agent_transcript_path, which is why the arithmetic lives in
#   tools/spawn-cost.py where the selftest can drive it, and this file is a
#   shim that does none.
#
#   exit 0 ALWAYS. This hook NEVER blocks: a broken audit trail must not be
#   able to stop the work it is only there to describe. It also returns no
#   JSON, so it can never prevent a subagent from ending.
#
# REGISTERED 2026-09-03 by director ruling (game-design/decision-2026-09-03-
# batch-review-register-banner-spawnlog-uvsweep.md). The block below is the
# one in .claude/settings.json; the first row it writes is read before any
# number from the turns log is quoted anywhere.
#
#     "SubagentStop": [
#       {
#         "matcher": "",
#         "hooks": [
#           {
#             "type": "command",
#             "command": "bash .claude/hooks/log-agent-stop.sh",
#             "timeout": 15
#           }
#         ]
#       }
#     ]
#
# Tested both ways by tools/spawn-cost.py --selftest: a real payload appends
# one row carrying tier and turns; malformed stdin, a payload with no
# agent_type, and a transcript that is already gone each write no invented
# number and are counted in their own bucket.

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$REPO/tools/spawn-cost.py" --hook >/dev/null 2>&1
exit 0
