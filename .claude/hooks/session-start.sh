#!/bin/bash
# SessionStart hook: orientation, and the two checks that catch an
# environment lying about where you are.
#
# 1. Where am I: branch, last commits, tree state.
# 2. ROLLBACK detection: ephemeral containers roll a checkout back under
#    the session, and nothing about it looks like a rollback — files
#    "missing", docs "reverted", greps coming back empty all read as code
#    problems first. The signature is HEAD being a strict ancestor of
#    origin. Detected here so it costs a line instead of an hour.
# 3. Queue head: the next startable work, so the session starts from the
#    plan instead of re-deriving it.

QUEUE="${QUEUE_FILE:-queue.md}"

echo "=== measured-studio session start ==="
echo "branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'not a git repo')"
git log --oneline -5 2>/dev/null | sed 's/^/  /'

DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
[ "$DIRTY" != "0" ] && echo "UNCOMMITTED: $DIRTY path(s) — read before assuming they are yours"

# Rollback signature: fetch quietly; if HEAD is a strict ancestor of the
# remote branch, the checkout has moved backwards under us.
BR=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ -n "$BR" ] && git fetch -q origin "$BR" 2>/dev/null; then
    LOCAL=$(git rev-parse HEAD 2>/dev/null)
    REMOTE=$(git rev-parse "origin/$BR" 2>/dev/null)
    if [ -n "$LOCAL" ] && [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ] \
       && git merge-base --is-ancestor "$LOCAL" "$REMOTE" 2>/dev/null; then
        echo "ROLLED BACK: HEAD is behind origin/$BR — the container reset this"
        echo "checkout. Everything pushed is safe; reset to origin before working."
    fi
fi

if [ -f "$QUEUE" ]; then
    echo "--- queue head ($QUEUE) ---"
    # First numbered item under '## Now', first 3 lines of it.
    awk '/^## Now/{f=1;next} f&&/^1\. /{c=1} c{print "  "$0; n++} n>=3{exit}' "$QUEUE"
else
    echo "no $QUEUE — if this project has work, that file is the first fix"
fi
exit 0
