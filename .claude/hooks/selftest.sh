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

echo "hooks selftest: $PASS passed, $FAIL failed"
exit $([ $FAIL -eq 0 ] && echo 0 || echo 1)
