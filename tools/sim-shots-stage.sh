#!/usr/bin/env bash
# WHAT THIS RUN PRODUCED — the list of files the build job is allowed to commit.
#
# WHY THIS EXISTS. On 4 August a Windows build on c61047f came back
# `NO PLAYER LOG` with three compile errors, and its commit — "Sim stills from
# c61047f" — replaced all six review JPEGs and rewrote frames.tsv. It cannot
# have rendered anything. What it committed was its own CHECKOUT's copies:
# `workflow_dispatch` takes a BRANCH, not a commit, so the runner can be
# building something seven commits behind the tip, and
# `git add game-design/sim-shots` then carries that older directory wholesale
# and calls it output. The branch went BACKWARDS, and the frames landed indexed
# under the sha of the build that failed to render them. I read six of them as
# evidence about that commit before checking the verdict.
#
# THE VERDICT-KEYS EXCLUSION IN THE WORKFLOW IS THE SAME FAULT, FOUND FIRST.
# It says so itself: "a build landing late, on an older commit, reverts the
# manifest and deletes every key added since". That was fixed by excluding one
# file, which was too narrow — the failure is not about which files are authored
# on the dev side, it is that "everything in the directory" is not a description
# of what a run produced. So the list is built from what actually got written.
#
# RULE 5, IN ITS ORIGINAL WORDS: scope destructive commands to exactly what the
# operation produced. A commit that reverts six files is a destructive command.
#
# WHY A SCRIPT AND NOT FOUR LINES IN THE STEP. `verify.py` enforces a ceiling on
# the length of a workflow step, because a step over GitHub's expression limit
# cannot be dispatched at all — and the inline version put it 2,582 characters
# over. The reasoning is the long part, and it belongs somewhere it can be read.
#
# AND IT REPLACES THE `verdict-keys.json` EXCLUSION, WHICH WAS THIS BUG'S FIRST
# SIGHTING. That file is authored on the dev side — the list of measurements
# that must keep being reported — and a run on 5e0e5b5 landing late dropped six
# entries newer commits had added, surfacing only as a merge conflict. Silently
# it is the worst failure a guard can have: the record of a lost measurement is
# deleted by the thing that existed to notice it was lost. An exclusion list
# needs a new entry every time somebody adds a file; naming what the run wrote
# needs none, and covers files nobody has thought of yet.
#
# USAGE: sim-shots-stage.sh <sha7> <stills_mine 0|1> <frames_mine 0|1> [oursdir]
# Prints one path per line ON STDOUT AND NOTHING ELSE, so the caller can
# `mapfile` it. With `oursdir`, also copies those files there — the snapshot the
# workflow's rebase loop reinstates after `git reset --hard`. Copying only these
# is what stops a rebase from reinstating the checkout's stills over a newer
# run's, which the old whole-directory copy did every time it fired.
set -euo pipefail

sha7=${1:?sha7}
stills=${2:-0}
frames=${3:-0}
ours=${4:-}
# FIFTH AND AFTER `ours`, WHICH IS UGLY AND IS THE RIGHT TRADE. `ours` has one
# caller and moving it would break that caller silently on a run nobody is
# watching; appending cannot.
clips=${5:-0}
dir=game-design/sim-shots

shopt -s nullglob

# ALWAYS OURS. Every run writes a verdict, including the ones that produce
# nothing else — that is the entire reason `NO PLAYER LOG` is readable at all.
# The per-run copy carries the sha in its name and so can never collide with a
# concurrent build's.
files=("$dir/verdict.txt" "$dir/runs/$sha7.txt")

# CONDITIONAL, AND EACH ON ITS OWN EVIDENCE. Stills come from the sim reaching a
# screenshot; the frame ledger comes from it writing frames.tsv. A run can
# manage the first and not the second, so one flag would have to guess.
if [ "$stills" = 1 ]; then files+=("$dir"/review_*.jpg); fi
if [ "$frames" = 1 ]; then files+=("$dir/frames.tsv"); fi
# The clip contact sheet is taken once, before day one, so a run can produce it
# and no street stills at all — which is why it gets its own flag rather than
# riding on the stills one. Its ledger goes with it or the sheet is 67 unlabelled
# tiles.
if [ "$clips" = 1 ]; then files+=("$dir/clips.jpg" "$dir/clips.tsv"); fi

if [ -n "$ours" ]; then
  rm -rf "$ours"
  mkdir -p "$ours/runs"
  for f in "${files[@]}"; do
    case "$f" in
      */runs/*) cp "$f" "$ours/runs/" 2>/dev/null || true ;;
      *)        cp "$f" "$ours/"      2>/dev/null || true ;;
    esac
  done
fi

printf '%s\n' "${files[@]}"
