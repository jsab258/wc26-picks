#!/bin/bash
# Tests the hooks on BOTH outcomes (rule 5b) — a guard shipped untested on
# its accepting case is the single most repeated failure in the project
# this template came from: four in one day, every one blocking the good
# case, every one reporting as "nothing happened".
#
# Run from the repo root:  bash .claude/hooks/selftest.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PASS=0; FAIL=0
say() { if [ "$1" = ok ]; then PASS=$((PASS+1)); echo "  ok   $2"; else FAIL=$((FAIL+1)); echo "  FAIL $2"; fi; }

call_gate() {  # $1=command  -> returns the hook's exit code
    printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$1" \
        | VERIFY_FOOTER="$FOOTER" bash "$HERE/verify-gate.sh" >/dev/null 2>&1
}

WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
cd "$WORK"
git init -q -b main .
git config user.email t@t; git config user.name t
mkdir -p tools
FOOTER="$WORK/tools/.verify-footer"

# ACCEPTING FIRST — the expensive failure is a gate nothing survives.
call_gate "ls -la";                    [ $? -eq 0 ] && say ok "non-commit commands pass" || say bad "non-commit commands pass"
call_gate "git status";                [ $? -eq 0 ] && say ok "git non-commit passes"    || say bad "git non-commit passes"

echo x > file.txt; git add file.txt
sleep 1; echo "verify green" > "$FOOTER"
call_gate "git commit -m msg";         [ $? -eq 0 ] && say ok "commit with fresh footer passes" || say bad "commit with fresh footer passes"

# REJECTING — with the real cases the gate was written for.
rm -f "$FOOTER"
call_gate "git commit -m msg";         [ $? -eq 2 ] && say ok "commit with no footer is blocked" || say bad "commit with no footer is blocked"

echo "verify green" > "$FOOTER"; sleep 1; echo y >> file.txt
call_gate "git commit -am msg";        [ $? -eq 2 ] && say ok "commit with stale footer is blocked" || say bad "commit with stale footer is blocked"

# A commit buried in a compound command is still a commit.
call_gate "cd sub && git commit -m msg"; [ $? -eq 2 ] && say ok "compound-command commit is caught" || say bad "compound-command commit is caught"

# session-start must not error outside the happy path (empty repo, no queue).
bash "$HERE/session-start.sh" >/dev/null 2>&1 && say ok "session-start survives a bare repo" || say bad "session-start survives a bare repo"

# ---- the agent audit trail (log-agent.sh) ----
# The delegation rule (CLAUDE.md, THE STUDIO SPLIT) had no instrument; this
# log is it, so its own failure modes are the ones that would make the
# instrument lie: a spawn that goes unrecorded, and a row that corrupts the
# file every later reading depends on.
call_log() {  # $1 = raw stdin -> returns the hook's exit code
    printf '%s' "$1" | AGENT_LOG="$AGENTLOG" bash "$HERE/log-agent.sh" >/dev/null 2>&1
}
AGENTLOG="$WORK/.claude/agent-log.tsv"
rows() { [ -f "$AGENTLOG" ] && wc -l < "$AGENTLOG" | tr -d ' ' || echo 0; }

# ACCEPTING FIRST, again — the expensive failure is an audit trail that
# records nothing and looks exactly like a director who delegated nothing.
call_log '{"agent_type":"systems-builder","session_id":"x"}'
[ "$(rows)" = "2" ] && say ok "a spawn appends a row under a header" \
                    || say bad "a spawn appends a row under a header (rows=$(rows))"
grep -q '^when	agent$' "$AGENTLOG" && say ok "the header is written once, first" \
                                   || say bad "the header is written once, first"
grep -q '	systems-builder$' "$AGENTLOG" && say ok "the row carries the agent type" \
                                          || say bad "the row carries the agent type"
# One line per spawn, and the header is NOT rewritten on the second.
call_log '{"agent_type":"claim-auditor"}'
[ "$(rows)" = "3" ] && say ok "a second spawn appends one line, no new header" \
                    || say bad "a second spawn appends one line, no new header (rows=$(rows))"
# The whole point of the file: counting spawns by type must work.
[ "$(cut -f2 "$AGENTLOG" | grep -c 'auditor\|builder')" = "2" ] \
    && say ok "spawns are countable by type" || say bad "spawns are countable by type"

# REJECTING — and the requirement is exit 0 with the file untouched, because
# a hook that blocks or corrupts is worse than no audit trail at all.
BEFORE=$(cat "$AGENTLOG")
call_log 'not json at all {{{'
[ $? -eq 0 ] && say ok "malformed stdin exits 0" || say bad "malformed stdin exits 0"
[ "$(cat "$AGENTLOG")" = "$BEFORE" ] && say ok "malformed stdin appends nothing" \
                                     || say bad "malformed stdin appends nothing"
call_log ''
[ "$(cat "$AGENTLOG")" = "$BEFORE" ] && say ok "empty stdin appends nothing" \
                                     || say bad "empty stdin appends nothing"
call_log '{"session_id":"x"}'
[ "$(cat "$AGENTLOG")" = "$BEFORE" ] && say ok "JSON with no agent_type appends nothing" \
                                     || say bad "JSON with no agent_type appends nothing"
# A tab in the value would split the row and every later `cut -f2` would
# read the wrong column — the verdict's no-spaces rule, one file over.
call_log '{"agent_type":"a\tb"}'
[ "$(tail -1 "$AGENTLOG" | awk -F'\t' '{print NF}')" = "2" ] \
    && say ok "a tab in the agent name cannot split the row" \
    || say bad "a tab in the agent name cannot split the row"

# THE FALLBACK IS A SECOND IMPLEMENTATION AND THEREFORE A SECOND THING TO
# TEST. Every test above ran the jq branch, because jq is on this PATH; a
# container without it would silently take the grep branch and nobody would
# know until the log came back empty. One idea, two implementations, and the
# one nobody looks at is the one missing a line.
NOJQ="$WORK/nojq"; mkdir -p "$NOJQ"
for b in cat grep head sed tr date mkdir dirname bash; do
    p=$(command -v "$b") && ln -sf "$p" "$NOJQ/$b"
done
FALLLOG="$WORK/.claude/fallback.tsv"
printf '{"agent_type":"content-wrangler"}' \
    | PATH="$NOJQ" AGENT_LOG="$FALLLOG" bash "$HERE/log-agent.sh" >/dev/null 2>&1
grep -q '	content-wrangler$' "$FALLLOG" 2>/dev/null \
    && say ok "the no-jq fallback records the spawn too" \
    || say bad "the no-jq fallback records the spawn too"
printf 'garbage {{{' \
    | PATH="$NOJQ" AGENT_LOG="$FALLLOG" bash "$HERE/log-agent.sh" >/dev/null 2>&1
[ "$(wc -l < "$FALLLOG" | tr -d ' ')" = "2" ] \
    && say ok "the no-jq fallback appends nothing for garbage" \
    || say bad "the no-jq fallback appends nothing for garbage"

echo "hooks selftest: $PASS passed, $FAIL failed"
exit $([ $FAIL -eq 0 ] && echo 0 || echo 1)
