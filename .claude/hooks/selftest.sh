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
gate_out() {  # $1=command  -> prints the hook's stdout AND stderr, one channel
    printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$1" \
        | VERIFY_FOOTER="$FOOTER" bash "$HERE/verify-gate.sh" 2>&1
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

# ---- the collapsed new directory (24 Aug) ----
# `git status --porcelain` reports a brand-new directory as ONE non-file entry
# (`?? newmod/`), so `[ -f ]` skipped it and nothing inside a new module was
# ever freshness-checked, however large. Printed here rather than asserted:
# pinning a PASS to git's default expansion would make a future git version
# block every commit in the project, which is the failure rule 5b is about.
mkdir -p newmod; printf 'a\nb\nc\n' > newmod/Big.cs
echo "  note porcelain default: $(git status --porcelain | grep newmod || echo NONE)"
echo "  note porcelain -uall:   $(git status --porcelain -uall | grep newmod || echo NONE)"

# ACCEPTING FIRST: the new module is OLDER than the footer, so it must pass —
# the expensive direction is a hook that blocks every commit made after any
# untracked file appears.
sleep 1; echo "verify green" > "$FOOTER"
call_gate "git commit -m msg";         [ $? -eq 0 ] && say ok "a new untracked directory older than the footer still passes" || say bad "a new untracked directory older than the footer still passes"

# REJECTING: a file INSIDE that new directory, touched after the footer. This
# is the hole — it passed before `-uall`, because the loop only ever saw
# `newmod/`, which is not a file.
sleep 1; echo "d" >> newmod/Big.cs
call_gate "git commit -m msg";         [ $? -eq 2 ] && say ok "a file inside a NEW untracked directory is freshness-checked" || say bad "a file inside a NEW untracked directory is freshness-checked"

# And the whole point of naming it: the message must name the file, not the
# directory, or the next reader cannot tell which one moved.
printf '{"tool_name":"Bash","tool_input":{"command":"git commit -m msg"}}' \
    | VERIFY_FOOTER="$FOOTER" bash "$HERE/verify-gate.sh" 2>&1 >/dev/null \
    | grep -q 'newmod/Big.cs' \
    && say ok "the block names the file inside the new directory" \
    || say bad "the block names the file inside the new directory"
rm -rf newmod

# ---- the repo-blind gate (24 Aug), and it can DEADLOCK an unattended loop ----
# This hook fires on every `git commit` THE SESSION runs, and until today it
# read this project's footer and this project's `git status` whichever
# repository the commit was actually in. It blocked a real commit in a second
# repo because LEDGER's tree was mid-work. Left alone overnight that is not an
# annoyance: work in the second repo cannot be committed while this one is
# busy, so it sits uncommitted until the ephemeral container reclaims it.
#
# The rungs below are a LADDER — one tree, one instant, one contributor
# toggled (which repo the commit targets) — so the difference between them is
# the whole finding. ACCEPTING RUNG FIRST: the expensive failure here is a
# gate that blocks a commit it was never able to assess.
OTHER=$(mktemp -d)
trap 'rm -rf "$WORK" "$OTHER"' EXIT
( cd "$OTHER" && git init -q -b main . && git config user.email t@t \
                                       && git config user.name t )
echo other > "$OTHER/thing.txt"
OTHER_TOP=$(git -C "$OTHER" rev-parse --show-toplevel)

# Put THIS repo into the state that caused the deadlock: dirty and stale.
sleep 1; echo z >> file.txt
mkdir -p sub

call_gate "cd $OTHER && git add -A && git commit -m msg"
[ $? -eq 0 ] && say ok "a commit in ANOTHER repo passes while this tree is stale (cd form)" \
             || say bad "a commit in ANOTHER repo passes while this tree is stale (cd form)"
call_gate "git -C $OTHER commit -m msg"
[ $? -eq 0 ] && say ok "a commit in ANOTHER repo passes while this tree is stale (git -C form)" \
             || say bad "a commit in ANOTHER repo passes while this tree is stale (git -C form)"
# A pass that says nothing is indistinguishable from a gate that never ran.
gate_out "git -C $OTHER commit -m msg" | grep -q "PASSED-UNASSESSED.*different-repo.*commitRepo=$OTHER_TOP" \
    && say ok "the cross-repo pass names both repos and why it passed" \
    || say bad "the cross-repo pass names both repos and why it passed"
# A red verify DELETES the footer, so the repo decision must not depend on it.
mv "$FOOTER" "$FOOTER.hidden"
call_gate "cd $OTHER && git commit -m msg"
[ $? -eq 0 ] && say ok "a commit in ANOTHER repo passes even with no footer here" \
             || say bad "a commit in ANOTHER repo passes even with no footer here"
mv "$FOOTER.hidden" "$FOOTER"

# THE OTHER RUNG, same tree, same second: the protection must survive the fix.
call_gate "git commit -m msg"
[ $? -eq 2 ] && say ok "a SAME-repo stale commit is still blocked (the fix kept the guard)" \
             || say bad "a SAME-repo stale commit is still blocked (the fix kept the guard)"
call_gate "cd sub && git commit -m msg"
[ $? -eq 2 ] && say ok "a cd to a subdirectory of THIS repo is still gated" \
             || say bad "a cd to a subdirectory of THIS repo is still gated"
call_gate "git -C sub commit -m msg"
[ $? -eq 2 ] && say ok "git -C into THIS repo is gated (it escaped the old detector entirely)" \
             || say bad "git -C into THIS repo is gated (it escaped the old detector entirely)"
call_gate "cd /nonexistent-$$ && git commit -m msg"
[ $? -eq 2 ] && say ok "a cd to a directory that does not exist falls back to this repo" \
             || say bad "a cd to a directory that does not exist falls back to this repo"
# `git commit-graph write` creates no commit; blocking it would be a false
# BLOCK on a maintenance command. Asserting SILENCE as well as exit 0 is what
# separates "not a commit" from "assessed and passed" — the two look identical
# from the exit code alone.
[ -z "$(gate_out 'git commit-graph write')" ] \
    && say ok "git commit-graph is not treated as a commit (silent, exit 0)" \
    || say bad "git commit-graph is not treated as a commit (silent, exit 0)"
call_gate "git commit; echo done"
[ $? -eq 2 ] && say ok "a commit terminated by ; is still caught" \
             || say bad "a commit terminated by ; is still caught"

# ---- the machine-written exclusion (24 Aug) ----
# `.claude/agent-log.tsv` is appended by the SubagentStart hook on every spawn,
# so it is newer than the footer almost always, and ALONE it was blocking
# commits whose code was fully verified. ACCEPTING CASE FIRST again.
rm -rf sub; git checkout -q -- file.txt 2>/dev/null
sleep 1; echo "verify green" > "$FOOTER"          # green over the whole tree
sleep 1; mkdir -p .claude; echo "when	agent" > .claude/agent-log.tsv
call_gate "git commit -m msg"
[ $? -eq 0 ] && say ok "an agent-log-only change does not block a verified commit" \
             || say bad "an agent-log-only change does not block a verified commit"
# ...and it must SAY it excluded something, and that the exclusion BIT, or the
# filter is invisible and the next reader cannot tell it from a clean tree.
OUT=$(gate_out "git commit -m msg")
printf '%s' "$OUT" | grep -q 'excluded=.claude/agent-log.tsv' \
    && say ok "the pass line names the exclusion" || say bad "the pass line names the exclusion"
printf '%s' "$OUT" | grep -q 'excludedNewerThanFooter=1' \
    && say ok "the pass line says the exclusion BIT (1 excluded path was newer)" \
    || say bad "the pass line says the exclusion BIT (1 excluded path was newer)"
printf '%s' "$OUT" | grep -qE 'walked=[0-9]+ checked=[0-9]+ stale=0/[0-9]+' \
    && say ok "the zero ships its denominator (walked/checked beside stale=0)" \
    || say bad "the zero ships its denominator (walked/checked beside stale=0)"

# REJECTING: a real source change after verify still blocks — and it must
# block for the SOURCE file, not be excused by the excluded one sitting beside
# it. This is the case the exclusion could have widened into.
sleep 1; echo w >> file.txt
OUT=$(gate_out "git commit -m msg")
call_gate "git commit -m msg"
[ $? -eq 2 ] && say ok "a real source change after verify still blocks" \
             || say bad "a real source change after verify still blocks"
printf '%s' "$OUT" | grep -q 'BLOCKED.*file.txt' \
    && say ok "the block names the source file" || say bad "the block names the source file"
printf '%s' "$OUT" | grep -q 'BLOCKED.*agent-log' \
    && say bad "the block does not list the excluded file as a finding" \
    || say ok "the block does not list the excluded file as a finding"
printf '%s' "$OUT" | grep -q 'BLOCK .*excluded=.claude/agent-log.tsv excludedSeen=1 excludedNewerThanFooter=1' \
    && say ok "the block line still declares the exclusion and that it bit" \
    || say bad "the block line still declares the exclusion and that it bit"
# The list is NAMED, not a pattern: a sibling file under the same directory
# must still be freshness-checked, or the exclusion has silently grown.
git checkout -q -- file.txt 2>/dev/null
sleep 1; echo "verify green" > "$FOOTER"; sleep 1; echo x > .claude/settings-note.txt
call_gate "git commit -m msg"
[ $? -eq 2 ] && say ok "a sibling file in .claude/ is NOT excluded (named list, not a pattern)" \
             || say bad "a sibling file in .claude/ is NOT excluded (named list, not a pattern)"

# The log-agent suite below counts rows from an empty start, so the fixture
# log written above must not be left standing in its way.
rm -rf .claude

# session-start must not error outside the happy path (empty repo, no queue).
bash "$HERE/session-start.sh" >/dev/null 2>&1 && say ok "session-start survives a bare repo" || say bad "session-start survives a bare repo"

# ---- the agent audit trail (log-agent.sh) ----
# The delegation rule (CLAUDE.md, THE STUDIO SPLIT) had no instrument; this
# log is it, so its own failure modes are the ones that would make the
# instrument lie: a spawn that goes unrecorded, and a row that corrupts the
# file every later reading depends on.
call_log() {  # $1 = raw stdin -> returns the hook's exit code
    printf '%s' "$1" \
        | AGENT_LOG="$AGENTLOG" AGENT_SPAWN_INTENT="$INTENT" \
          bash "$HERE/log-agent.sh" >/dev/null 2>&1
}
AGENTLOG="$WORK/.claude/agent-log.tsv"
INTENT="$WORK/.claude/spawn-intent"
rows() { [ -f "$AGENTLOG" ] && wc -l < "$AGENTLOG" | tr -d ' ' || echo 0; }

# DEFINITION FIXTURES, 2026-09-10 (E2): log-agent.sh now reads model: out of
# .claude/agents/<agent_type>.md at spawn time and consumes a matching
# .claude/spawn-intent for an upward or downward override, so the accepting
# case needs both, in the same sandbox the hook will see.
mkdir -p "$WORK/.claude/agents"
cat > "$WORK/.claude/agents/systems-builder.md" <<'DEFEOF'
---
name: systems-builder
model: opus
---
fixture agent, selftest only
DEFEOF
cat > "$WORK/.claude/agents/low-tier-worker.md" <<'DEFEOF'
---
name: low-tier-worker
model: haiku
---
fixture agent, selftest only — body mentions model: opus, must not match
DEFEOF

# ACCEPTING FIRST, again — the expensive failure is an audit trail that
# records nothing and looks exactly like a director who delegated nothing.
call_log '{"agent_type":"systems-builder","session_id":"x"}'
[ "$(rows)" = "2" ] && say ok "a spawn appends a row under a header" \
                    || say bad "a spawn appends a row under a header (rows=$(rows))"
grep -q '^when	agent	model	reason	agentId$' "$AGENTLOG" \
    && say ok "the header names all five columns, written once, first" \
    || say bad "the header names all five columns, written once, first"
[ "$(tail -1 "$AGENTLOG" | cut -f2)" = "systems-builder" ] \
    && say ok "the row carries the agent type" \
    || say bad "the row carries the agent type"
[ "$(tail -1 "$AGENTLOG" | cut -f3)" = "opus" ] \
    && say ok "the row carries the model read from the agent's own definition (opus)" \
    || say bad "the row carries the model read from the agent's own definition (opus)"
[ "$(tail -1 "$AGENTLOG" | cut -f4)" = "default" ] \
    && say ok "a spawn at its declared model reads reason=default" \
    || say bad "a spawn at its declared model reads reason=default"

# A MATCHING spawn-intent: model AND its up: reason token captured together,
# same row, same read — the paired reading the construction rules ask for.
echo "agent=systems-builder model=fable reason=up:review:queue/099" > "$INTENT"
call_log '{"agent_type":"systems-builder","agent_id":"up1"}'
[ "$(tail -1 "$AGENTLOG" | cut -f3)" = "fable" ] \
    && say ok "a matching spawn-intent's model (fable) is captured" \
    || say bad "a matching spawn-intent's model (fable) is captured"
[ "$(tail -1 "$AGENTLOG" | cut -f4)" = "up:review:queue/099" ] \
    && say ok "its reason= token is captured in the SAME row" \
    || say bad "its reason= token is captured in the SAME row"
[ "$(tail -1 "$AGENTLOG" | cut -f5)" = "up1" ] \
    && say ok "the row carries the SubagentStart payload's own agentId" \
    || say bad "the row carries the SubagentStart payload's own agentId"
[ ! -f "$INTENT" ] && say ok "a matching spawn-intent is consumed (deleted)" \
                    || say bad "a matching spawn-intent is consumed (deleted)"

# A MISMATCHED spawn-intent (a different agent_type) must survive untouched:
# an intent meant for a spawn that has not fired yet is not another spawn's
# to consume.
echo "agent=some-other-agent model=fable reason=up:review:queue/001" > "$INTENT"
call_log '{"agent_type":"systems-builder"}'
[ "$(tail -1 "$AGENTLOG" | cut -f3)" = "opus" ] \
    && say ok "a MISMATCHED spawn-intent is ignored (model falls back to declared)" \
    || say bad "a MISMATCHED spawn-intent is ignored (model falls back to declared)"
[ -f "$INTENT" ] && say ok "a MISMATCHED spawn-intent survives, unconsumed" \
                  || say bad "a MISMATCHED spawn-intent survives, unconsumed"
rm -f "$INTENT"

# DOWNWARD via a matching intent: free, recorded as fact, and the intent's
# own up: reason token (meant for an upward move) is never used for one.
echo "agent=systems-builder model=haiku reason=up:should-be-ignored" > "$INTENT"
call_log '{"agent_type":"systems-builder"}'
[ "$(tail -1 "$AGENTLOG" | cut -f3)" = "haiku" ] \
    && say ok "a downward spawn-intent's model (haiku) is captured" \
    || say bad "a downward spawn-intent's model (haiku) is captured"
[ "$(tail -1 "$AGENTLOG" | cut -f4)" = "down" ] \
    && say ok "a downward route reads reason=down, never the intent's own up: token" \
    || say bad "a downward route reads reason=down, never the intent's own up: token"

# An agent_type with NO definition file on disk: the model column says so
# in the literal word "none" (rule 3b), never a blank read as "no opinion".
call_log '{"agent_type":"general-purpose"}'
[ "$(tail -1 "$AGENTLOG" | cut -f3)" = "none" ] \
    && say ok "an agent_type with no definition file records none, not a guess" \
    || say bad "an agent_type with no definition file records none, not a guess"
[ "$(tail -1 "$AGENTLOG" | cut -f4)" = "default" ] \
    && say ok "with no declared baseline, reason reads default (nothing to override)" \
    || say bad "with no declared baseline, reason reads default (nothing to override)"

# UPWARD with NO intent file at all: the sentinel, never a blank. Exercises
# the SubagentStart payload's own optional .model field too (measured absent
# today, checked anyway per the hook's own comment).
call_log '{"agent_type":"low-tier-worker","model":"fable"}'
[ "$(tail -1 "$AGENTLOG" | cut -f3)" = "fable" ] \
    && say ok "a payload-supplied model (fable) is used when present" \
    || say bad "a payload-supplied model (fable) is used when present"
[ "$(tail -1 "$AGENTLOG" | cut -f4)" = "up:MISSING" ] \
    && say ok "upward with no matching intent writes up:MISSING, never a blank" \
    || say bad "upward with no matching intent writes up:MISSING, never a blank"

# One line per spawn, and the header is NOT rewritten on a later one.
call_log '{"agent_type":"claim-auditor"}'
[ "$(rows)" = "8" ] && say ok "an eighth row appends one line, no new header" \
                    || say bad "an eighth row appends one line, no new header (rows=$(rows))"
# The whole point of the file: counting spawns by type must work.
[ "$(cut -f2 "$AGENTLOG" | grep -c 'auditor\|builder\|worker\|purpose')" = "7" ] \
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
# A tab in a value would split the row and every later `cut -fN` would read
# the wrong column — the verdict's no-spaces rule, one file over.
call_log '{"agent_type":"a\tb","agent_id":"id\tx"}'
[ "$(tail -1 "$AGENTLOG" | awk -F'\t' '{print NF}')" = "5" ] \
    && say ok "a tab in a value cannot split the row (all five columns stand)" \
    || say bad "a tab in a value cannot split the row (all five columns stand)"
[ "$(tail -1 "$AGENTLOG" | cut -f2)" = "a b" ] \
    && say ok "the tab in the agent name is itself replaced with a space" \
    || say bad "the tab in the agent name is itself replaced with a space"
[ "$(tail -1 "$AGENTLOG" | cut -f5)" = "id x" ] \
    && say ok "the tab in the agentId is itself replaced with a space" \
    || say bad "the tab in the agentId is itself replaced with a space"

# THE FALLBACK IS A SECOND IMPLEMENTATION AND THEREFORE A SECOND THING TO
# TEST. Every test above ran the jq branch, because jq is on this PATH; a
# container without it would silently take the grep branch and nobody would
# know until the log came back empty. One idea, two implementations, and the
# one nobody looks at is the one missing a line. `awk` is added to this PATH
# too: the model lookup below uses it in BOTH branches (it has nothing to do
# with the jq/grep fallback), and a PATH missing it would silently read
# every model as declared-only (never a payload/intent override) rather
# than fail loudly.
NOJQ="$WORK/nojq"; mkdir -p "$NOJQ"
for b in cat grep head sed tr date mkdir dirname bash awk rm cut; do
    p=$(command -v "$b") && ln -sf "$p" "$NOJQ/$b"
done
FALLLOG="$WORK/.claude/fallback.tsv"
FALLINTENT="$WORK/.claude/fallback-intent"
printf '{"agent_type":"systems-builder","agent_id":"fb1"}' \
    | PATH="$NOJQ" AGENT_LOG="$FALLLOG" AGENT_SPAWN_INTENT="$FALLINTENT" \
      bash "$HERE/log-agent.sh" >/dev/null 2>&1
[ "$(tail -1 "$FALLLOG" 2>/dev/null | cut -f2)" = "systems-builder" ] \
    && say ok "the no-jq fallback records the spawn too" \
    || say bad "the no-jq fallback records the spawn too"
[ "$(tail -1 "$FALLLOG" 2>/dev/null | cut -f3)" = "opus" ] \
    && say ok "the no-jq fallback still reads the model from the definition (awk, not jq)" \
    || say bad "the no-jq fallback still reads the model from the definition (awk, not jq)"
[ "$(tail -1 "$FALLLOG" 2>/dev/null | cut -f5)" = "fb1" ] \
    && say ok "the no-jq fallback extracts agentId too (grep, not jq)" \
    || say bad "the no-jq fallback extracts agentId too (grep, not jq)"
echo "agent=systems-builder model=fable reason=up:engine:ledger/Assets/x" > "$FALLINTENT"
printf '{"agent_type":"systems-builder","agent_id":"fb2"}' \
    | PATH="$NOJQ" AGENT_LOG="$FALLLOG" AGENT_SPAWN_INTENT="$FALLINTENT" \
      bash "$HERE/log-agent.sh" >/dev/null 2>&1
[ "$(tail -1 "$FALLLOG" 2>/dev/null | cut -f3)" = "fable" ] \
    && say ok "the no-jq fallback also consumes a matching spawn-intent" \
    || say bad "the no-jq fallback also consumes a matching spawn-intent"
[ ! -f "$FALLINTENT" ] \
    && say ok "the no-jq fallback deletes the intent it consumed" \
    || say bad "the no-jq fallback deletes the intent it consumed"
printf 'garbage {{{' \
    | PATH="$NOJQ" AGENT_LOG="$FALLLOG" AGENT_SPAWN_INTENT="$FALLINTENT" \
      bash "$HERE/log-agent.sh" >/dev/null 2>&1
[ "$(wc -l < "$FALLLOG" | tr -d ' ')" = "3" ] \
    && say ok "the no-jq fallback appends nothing for garbage" \
    || say bad "the no-jq fallback appends nothing for garbage"

echo "hooks selftest: $PASS passed, $FAIL failed"
exit $([ $FAIL -eq 0 ] && echo 0 || echo 1)
