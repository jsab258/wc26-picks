#!/bin/bash
# PreToolUse hook on Bash: BLOCK `git commit` unless the verify footer is
# green and fresher than every staged/modified file — IN THE REPOSITORY THE
# FOOTER DESCRIBES, and only there.
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
#   exit 0  = allow  (the gate's own line goes to stdout: an allow is not an
#             error, and a PASS painted on stderr trains everyone to ignore
#             stderr, which is where the BLOCK has to be read)
#   exit 2  = block, stderr shown to the model
#
# Tested both ways (rule 5b) by .claude/hooks/selftest.sh:
#   ACCEPT: non-commit commands; commit with fresh footer; commit with a NEW
#           untracked directory OLDER than the footer; a commit in ANOTHER
#           repository while this one is dirty and stale; a change to nothing
#           but the machine-written agent log
#   REJECT: commit with no footer; commit with footer older than a change;
#           commit with a file inside a NEW untracked directory newer than it;
#           a source change after verify, even when the agent log moved too

FOOTER="${VERIFY_FOOTER:-tools/.verify-footer}"

# ---------------------------------------------------------------------------
# NAMED EXCLUSIONS FROM THE FRESHNESS COMPARISON — exact repo-relative paths,
# space-separated, matched whole. NOT a glob and not a directory prefix: a
# pattern grows silently (one `.claude/*` and the hooks themselves stop being
# checked), a named list has to be edited by a person and shows up in a diff.
#
# `.claude/agent-log.tsv` is appended by the SubagentStart hook and
# `.claude/agent-turns.tsv` by the SubagentStop hook, on EVERY agent spawn, so
# in a session that delegates both are newer than the footer almost always.
# They are machine-written, never reviewed, and cannot change what verify
# concludes — so on its own it was blocking commits whose code was fully
# verified. That is the ratchet of rule 5: a guard that cannot tell a
# regression from an improvement, here in its noisiest form.
#
# THE EXCLUSION IS PRINTED ON EVERY OUTCOME LINE, with a count of how many
# excluded paths were actually newer than the footer, because a filter that
# does not say when it bit is indistinguishable from a finding (rule 3b's
# truncation sibling: `(+N more not shown)`).
# agent-turns.tsv added 2026-09-03, the hour the SubagentStop hook was
# registered: it is the same file in the same position and it re-created
# this exact ratchet on its first row. Both are on DIRECTOR_EVIDENCE in
# ledger/verify.py; this is the second list and it has to be kept in step.
FRESHNESS_EXCLUDE=".claude/agent-log.tsv .claude/agent-turns.tsv"

INPUT=$(cat)
if command -v jq >/dev/null 2>&1; then
    COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
else
    COMMAND=$(printf '%s' "$INPUT" \
        | grep -oE '"command"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' \
        | head -1 | sed 's/^"command"[[:space:]]*:[[:space:]]*"//; s/"$//')
fi

# Spaces in a `key=value` value truncate every reader that splits on
# whitespace. No path in this project has one; if one ever does, it prints as
# %20 and the pair survives instead of the line quietly losing its tail.
nsp() { printf '%s' "${1// /%20}"; }

# ---------------------------------------------------------------------------
# DETECTION — ONE implementation, and it hands back the text it matched so the
# working-directory parse below can be bounded EXACTLY at the invocation
# rather than at the first place the word "commit" happens to appear.
#
# Only git commit is gated. Not push (already-committed work must always be
# pushable — ephemeral environments roll back, and stranded green work is
# worse than any gap this hook closes), not add, not anything else.
#
# `-C <dir>` is in the pattern because git takes it as a working directory:
# before it was here, `git -C /somewhere commit` was not recognised as a
# commit at all (`-C` is uppercase; the old class was `[a-z-]`) and sailed
# straight past the gate. Measured on this repo before the change: exit 0.
# `-c <k=v>` is in the same alternative because it also carries an argument
# that must not be mistaken for the subcommand.
#
# The trailing boundary is `[^-_[:alnum:]]|$` rather than `\b` so that
# `git commit;` is still caught (a `;` is a boundary) while `git commit-graph
# write` — which creates no commit — is not.
COMMIT_RE='(^|[;&|][[:space:]]*)git[[:space:]]+([-a-zA-Z]+[[:space:]]+|-[Cc][[:space:]]+[^[:space:]]+[[:space:]]+)*commit([^-_[:alnum:]]|$)'
[[ "$COMMAND" =~ $COMMIT_RE ]] || exit 0
INVOCATION="${BASH_REMATCH[0]}"

# ---------------------------------------------------------------------------
# WHICH REPOSITORY IS BEING COMMITTED TO. Until 24 Aug this hook did not ask:
# it read THIS project's footer and THIS project's `git status` for every
# commit the session made, wherever it was made. It blocked a legitimate
# commit in /home/user/measured-studio-work because LEDGER's tree was
# mid-work, and overnight that is not an annoyance but a DEADLOCK: a second
# repo cannot be committed while this one is busy, the work sits uncommitted,
# and the container reclaim takes it. Nothing in the footer of one repo says
# anything about the tree of another.
#
# Conservative parse, preferring the session cwd — with one exception, below.
TARGET_DIR=""
TARGET_WHY="session-cwd"
UNRESOLVED=""

# `git -C <dir>` wins over any preceding cd: it is what git itself will use.
GITC_RE='(^|[[:space:]])-C[[:space:]]+([^[:space:]]+)'
if [[ "$INVOCATION" =~ $GITC_RE ]]; then
    TARGET_DIR="${BASH_REMATCH[2]}"
    TARGET_WHY="git-C"
else
    # `cd <dir> && ... git commit`: the LAST cd before the invocation.
    PREFIX="${COMMAND%%"$INVOCATION"*}"
    CD_ARG=$(printf '%s' "$PREFIX" \
        | grep -oE '(^|[;&|(][[:space:]]*)cd[[:space:]]+[^;&|)]+' | tail -1 \
        | sed -E 's/^[;&|(]?[[:space:]]*cd[[:space:]]+//; s/[[:space:]]+$//')
    case "$CD_ARG" in
        \"*\") CD_ARG="${CD_ARG#\"}"; CD_ARG="${CD_ARG%\"}" ;;
        \'*\') CD_ARG="${CD_ARG#\'}"; CD_ARG="${CD_ARG%\'}" ;;
    esac
    case "$CD_ARG" in
        "") ;;
        # A shell expansion this process cannot evaluate: `cd "$REPO"`. The
        # command has SAID it is going somewhere else and we cannot tell
        # where — see the fail-open note below.
        *'$'*|*'`'*|*'*'*|*'?'*|*'['*) UNRESOLVED="$CD_ARG" ;;
        '~'|'~/'*) TARGET_DIR="$HOME${CD_ARG#\~}"; TARGET_WHY="cd" ;;
        *) TARGET_DIR="$CD_ARG"; TARGET_WHY="cd" ;;
    esac
    if [ -n "$TARGET_DIR" ]; then
        case "$TARGET_DIR" in /*) ;; *) TARGET_DIR="$PWD/$TARGET_DIR" ;; esac
        # A cd to a directory that does not exist commits nowhere — the
        # command short-circuits. Fall back to the session cwd, which is the
        # conservative side, and keeps `cd sub && git commit` gated here.
        [ -d "$TARGET_DIR" ] || { TARGET_DIR=""; TARGET_WHY="session-cwd"; }
    fi
fi
[ -n "$TARGET_DIR" ] || TARGET_DIR="$PWD"

top_of() { git -C "$1" rev-parse --show-toplevel 2>/dev/null; }

TARGET_TOP=$(top_of "$TARGET_DIR")
[ -n "$TARGET_TOP" ] || TARGET_TOP=$(top_of "$PWD")

# The repo the FOOTER belongs to: the toplevel of its directory, walking up to
# the nearest one that exists (a red verify DELETES the footer, and the gate
# still has to know whose footer is missing).
case "$FOOTER" in /*) FOOTER_ABS="$FOOTER" ;; *) FOOTER_ABS="$PWD/$FOOTER" ;; esac
FOOTER_DIR=$(dirname "$FOOTER_ABS")
while [ ! -d "$FOOTER_DIR" ] && [ "$FOOTER_DIR" != "/" ]; do
    FOOTER_DIR=$(dirname "$FOOTER_DIR")
done
FOOTER_TOP=$(top_of "$FOOTER_DIR")
[ -n "$FOOTER_TOP" ] || FOOTER_TOP=$(top_of "$PWD")

# FAIL OPEN ACROSS REPOSITORIES, deliberately and out loud. The miss is an
# unverified commit in a repo this footer never described — which that repo's
# own verify is responsible for. The alternative is a commit this gate cannot
# assess being blocked until a tree it does not own goes clean, and in an
# unattended overnight loop that ends with the work lost to a container
# reclaim. Recoverable against unrecoverable.
if [ -n "$UNRESOLVED" ]; then
    printf 'verify-gate: PASSED-UNASSESSED reason=cd-target-unresolved arg=%s footerRepo=%s footer=%s excluded=%s | the command changes directory through a shell expansion this hook cannot evaluate, so it cannot tell which repository it is looking at; it passes rather than block work it cannot assess.\n' \
        "$(nsp "$UNRESOLVED")" "$(nsp "$FOOTER_TOP")" "$(nsp "$FOOTER")" "$(nsp "$FRESHNESS_EXCLUDE")"
    exit 0
fi
if [ "$TARGET_TOP" != "$FOOTER_TOP" ]; then
    printf 'verify-gate: PASSED-UNASSESSED reason=different-repo via=%s commitRepo=%s footerRepo=%s footer=%s excluded=%s | this gate only knows the tree its footer describes; that repo has its own verify.\n' \
        "$TARGET_WHY" "$(nsp "${TARGET_TOP:-none}")" "$(nsp "${FOOTER_TOP:-none}")" "$(nsp "$FOOTER")" "$(nsp "$FRESHNESS_EXCLUDE")"
    exit 0
fi

if [ ! -f "$FOOTER" ]; then
    echo "BLOCKED: $FOOTER does not exist — the last verify run was red or" >&2
    echo "never ran. Run the project's verify (it writes the footer when" >&2
    echo "green, deletes it when red), fix what is red, then commit with" >&2
    echo "the footer pasted from the file. A red run has nothing to give you." >&2
    exit 2
fi

# Freshness: the footer must be newer than every change being committed.
# `git status --porcelain` covers staged and unstaged; untracked files are
# included because `git commit -a`/pathspec commits can pick them up once
# added, and a stale-footer false BLOCK costs one re-run while a false ALLOW
# costs an unverified commit.
#
# `-uall` IS LOAD-BEARING, NOT TIDINESS. Default porcelain COLLAPSES a new
# directory into a single non-file entry — `?? newmod/` — so `[ -f ]` below
# skipped it and every file inside a brand-new module went unchecked, however
# many there were and however far they post-dated the footer. Measured on a
# fixture repo, same tree, both flags:
#   git status --porcelain        -> ?? ledger/Assets/Scripts/NewMod/
#   git status --porcelain -uall  -> ?? ledger/Assets/Scripts/NewMod/Big.cs
# It costs nothing here: 12ms against 9ms on this repository.
#
# Paths from `--porcelain` are relative to the TOPLEVEL, not to the cwd, so
# they are stat'd against the toplevel — the hook is not guaranteed to be
# standing at the root of the repo it is assessing.
STALE=""
WALKED=0        # COUNT of porcelain entries seen — the denominator for stale
CHECKED=0       # COUNT of those that were regular files and got stat'd
STALE_N=0       # COUNT of checked files newer than the footer
EXCL_SEEN=0     # COUNT of named-exclusion paths present in this status
EXCL_NEWER=0    # ...of which this many WERE newer: the exclusion BITING
MEASURED=1
STATUS_OUT=$(git -C "$TARGET_TOP" status --porcelain -uall 2>/dev/null) || MEASURED=0

if [ "$MEASURED" = 1 ]; then
    while IFS= read -r line; do
        [ -n "$line" ] || continue
        WALKED=$((WALKED + 1))
        f="${line:3}"
        # rename lines are "R  old -> new"; take the new path
        case "$f" in *" -> "*) f="${f##* -> }" ;; esac
        abs="$TARGET_TOP/$f"
        case " $FRESHNESS_EXCLUDE " in
            *" $f "*)
                EXCL_SEEN=$((EXCL_SEEN + 1))
                if [ -f "$abs" ] && [ "$abs" -nt "$FOOTER_ABS" ]; then
                    EXCL_NEWER=$((EXCL_NEWER + 1))
                fi
                continue
                ;;
        esac
        # WHAT THIS SKIP LETS THROUGH, said out loud rather than left to be
        # rediscovered: anything that is not a regular file this process can stat
        # is passed over, which ERRS TOWARD ALLOW — the direction the comment
        # above calls the expensive one. Two cases remain after `-uall`: a DELETED
        # path (harmless — a file that is gone cannot be newer than the footer)
        # and a path git printed QUOTED because its name holds a quote, a
        # backslash or a control character (`"od\dd"`), which no longer matches
        # the name on disk and is therefore never freshness-checked. Neither is
        # reachable by ordinary work in this repo; both are a false ALLOW if it
        # happens, not a false BLOCK.
        [ -f "$abs" ] || continue
        CHECKED=$((CHECKED + 1))
        if [ "$abs" -nt "$FOOTER_ABS" ]; then
            STALE="$STALE $f"
            STALE_N=$((STALE_N + 1))
        fi
    # Process substitution, not a pipe: a pipe would run the loop in a
    # subshell and every counter below would come back at its initialiser —
    # a zero that means "not measured" wearing a clean result's clothes. And
    # not a heredoc either: an unquoted one would eat backslashes out of the
    # very paths whose odd names the skip comment above is about.
    done < <(printf '%s\n' "$STATUS_OUT")
fi

# Every zero ships its denominator, and a status that never ran must not read
# as a clean tree (rule 3b) — hence the words, not a 0.
if [ "$MEASURED" = 1 ]; then
    COUNTS="walked=$WALKED checked=$CHECKED stale=$STALE_N/$CHECKED"
else
    COUNTS="walked=nothing-measured checked=nothing-measured stale=nothing-measured"
fi
COUNTS="$COUNTS excluded=$(nsp "$FRESHNESS_EXCLUDE") excludedSeen=$EXCL_SEEN excludedNewerThanFooter=$EXCL_NEWER"

if [ -n "$STALE" ]; then
    echo "BLOCKED: these files changed after the last green verify:$STALE" >&2
    echo "verify-gate: BLOCK repo=$(nsp "$TARGET_TOP") footer=$(nsp "$FOOTER") $COUNTS" >&2
    echo "Re-run verify so the footer describes the tree being committed." >&2
    exit 2
fi

echo "verify-gate: PASS repo=$(nsp "$TARGET_TOP") footer=$(nsp "$FOOTER") $COUNTS"
exit 0
