#!/bin/bash
# PreToolUse hook on Bash: BLOCK `git commit` unless the verify footer is
# green and fresher than every staged/modified file.
#
# Why a BLOCK and not a reminder: "run verify before committing" is a rule,
# and the CLAUDE.md this template ships is mostly a list of rules that
# decayed. The extracted project pasted unmeasured claims into commit
# messages three times; printing "NOT GREEN — do not paste this" under the
# footer did not stop the third. A warning printed after a decision cannot
# reach the decision. A blocked tool call can.
#
# Contract (Claude Code PreToolUse for Bash):
#   stdin:  { "tool_name": "Bash", "tool_input": { "command": "..." } }
#   exit 0  = allow
#   exit 2  = block, stderr shown to the model
#
# Tested both ways (rule 5b) by .claude/hooks/selftest.sh:
#   ACCEPT: non-commit commands; commit with fresh footer
#   REJECT: commit with no footer; commit with footer older than a change

FOOTER="${VERIFY_FOOTER:-tools/.verify-footer}"

INPUT=$(cat)
if command -v jq >/dev/null 2>&1; then
    COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
else
    COMMAND=$(printf '%s' "$INPUT" \
        | grep -oE '"command"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' \
        | head -1 | sed 's/^"command"[[:space:]]*:[[:space:]]*"//; s/"$//')
fi

# Only git commit is gated. Not push (already-committed work must always be
# pushable — ephemeral environments roll back, and stranded green work is
# worse than any gap this hook closes), not add, not anything else.
printf '%s' "$COMMAND" | grep -qE '(^|[;&|]\s*)git\s+([a-z-]+\s+)*commit\b' || exit 0

if [ ! -f "$FOOTER" ]; then
    echo "BLOCKED: $FOOTER does not exist — the last verify run was red or" >&2
    echo "never ran. Run the project's verify (it writes the footer when" >&2
    echo "green, deletes it when red), fix what is red, then commit with" >&2
    echo "the footer pasted from the file. A red run has nothing to give you." >&2
    exit 2
fi

# Freshness: the footer must be newer than every tracked change being
# committed. `git status --porcelain` covers staged and unstaged; untracked
# files are included because `git commit -a`/pathspec commits can pick them
# up once added, and a stale-footer false BLOCK costs one re-run while a
# false ALLOW costs an unverified commit.
STALE=""
while IFS= read -r line; do
    f="${line:3}"
    # rename lines are "R  old -> new"; take the new path
    case "$f" in *" -> "*) f="${f##* -> }";; esac
    [ -f "$f" ] || continue
    [ "$f" -nt "$FOOTER" ] && STALE="$STALE $f"
done < <(git status --porcelain 2>/dev/null)

if [ -n "$STALE" ]; then
    echo "BLOCKED: these files changed after the last green verify:$STALE" >&2
    echo "Re-run verify so the footer describes the tree being committed." >&2
    exit 2
fi

exit 0
