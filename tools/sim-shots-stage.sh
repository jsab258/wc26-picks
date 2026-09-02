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

# ---------------------------------------------------------------------------
# framesStaged — DID THIS RUN ACTUALLY TAKE THE PICTURE THE LEDGER DESCRIBES?
#
# WHY. On 25 August `frames.tsv` landed headed `# commit 14f964a` with fresh
# day12/day13 rows, and no `hunt_*.jpg` was written by that stills commit or by
# the one before it — those JPEGs are 22-24 August images. The ledger said
# `day12_noon meanLuma=0.079`; the file on disk measures 0.114. So a row can
# describe a picture the run never took and read as authoritative, and nothing
# could tell "the run photographed this" from "a row exists for this".
#
# That is the fault this script was written for, one layer up: the stale thing
# is a ROW rather than a file.
#
# HOW IT DECIDES, and it is deliberately not a clock. A picture belongs to this
# run iff git sees the file as changed or untracked — a rendered JPEG is never
# byte-identical to last week's. Mtimes are a property of the runner's disk (a
# checkout rewrites them all) and any age threshold would be a bound with no
# series behind it, which rule 2 forbids.
#
# WHAT IT IS A STATISTIC OF: a whole-run count, taken once at staging time,
# over the rows of the ledger. It goes in the verdict, never on the sim's done
# line, because the sim cannot know what git staged — that fact does not exist
# until after it exits.
#
# EVERY ZERO SHIPS ITS DENOMINATOR and never-ran prints WORDS: no ledger, and
# no git to ask, are sentences, so neither can read as "0 of 0, all fine".
frames_staged_line() {
  local dir=$1 framesflag=$2; shift 2
  local staged=("$@")
  if [ "$framesflag" != 1 ] || [ ! -f "$dir/frames.tsv" ]; then
    echo "framesStaged=no-ledger-this-run framesRows=0 framesUnstaged=[no-ledger]"
    return 0
  fi
  if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "framesStaged=no-git-cannot-tell framesRows=0 framesUnstaged=[no-git]"
    return 0
  fi
  local rows=0 have=0 shot base f dirty found
  local missing=()
  while IFS=$'\t' read -r shot _rest; do
    case "$shot" in ''|'#'*|shot) continue ;; esac
    rows=$((rows + 1))
    found=0
    for f in "${staged[@]}"; do
      case "$f" in *.jpg) ;; *) continue ;; esac
      base=$(basename "$f" .jpg)
      if [ "$base" = "$shot" ] || [ "${base%"_$shot"}" != "$base" ]; then
        # CHANGED OR UNTRACKED, asked of git rather than of the clock.
        dirty=$(git status --porcelain -- "$f" 2>/dev/null || true)
        if [ -n "$dirty" ]; then found=1; break; fi
      fi
    done
    if [ "$found" = 1 ]; then have=$((have + 1)); else missing+=("$shot"); fi
  done < "$dir/frames.tsv"
  local names="none"
  if [ ${#missing[@]} -gt 0 ]; then
    # THE CAP ANNOUNCES ITSELF. An unannounced truncation reads as a finding —
    # a `| head -3` once read as "three of five bodies failed".
    names=$(printf '%s/' "${missing[@]:0:8}"); names=${names%/}
    if [ ${#missing[@]} -gt 8 ]; then names="$names/+$(( ${#missing[@]} - 8 ))more-not-shown"; fi
  fi
  echo "framesStaged=$have/$rows framesRows=$rows framesUnstaged=[$names]"
}

if [ "${1:-}" = "--selftest" ]; then
  # ACCEPTING CASE FIRST (rule 5b): the expensive failure for a guard is that
  # nothing survives it. Both cases run through a throwaway git repo, because
  # the question this asks is a git question and a fixture that fakes the
  # answer would only test the fixture.
  #
  # THE FIXTURE COMMITS WITH PLUMBING (`write-tree` + `commit-tree` +
  # `update-ref`) AND THAT IS NOT DECORATION. `.claude/hooks/verify-gate.sh` is
  # a PreToolUse gate that blocks any Bash command containing `git commit`
  # unless this repository's verify footer is green — it reads the SESSION cwd,
  # so it cannot see that a `cd` inside this script has moved to /tmp. Porcelain
  # here would make a throwaway fixture in another repository unrunnable
  # whenever LEDGER is mid-work, which is exactly when a builder runs it. The
  # plumbing writes the same commit object and leaves the gate at full strength
  # for the commits it exists to stop.
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  cd "$tmp"; git init -q .; mkdir -p game-design/sim-shots
  d=game-design/sim-shots
  snap() {  # tracked-and-unchanged, without tripping the commit gate
    git add -A >/dev/null
    local tr; tr=$(git write-tree)
    local parent=(); local head; head=$(git rev-parse -q --verify HEAD || true)
    [ -n "$head" ] && parent=(-p "$head")
    local c; c=$(git -c user.email=t@t -c user.name=t commit-tree "$tr" "${parent[@]}" -m snap)
    git update-ref HEAD "$c"
  }
  printf 'shot\tmeanLuma\nday1_noon\t0.3\nday12_noon\t0.079\n' > $d/frames.tsv
  echo old1 > $d/review_day1_noon.jpg; echo old2 > $d/hunt_day12_noon.jpg
  snap
  echo new1 > $d/review_day1_noon.jpg; echo new2 > $d/hunt_day12_noon.jpg
  acc=$(frames_staged_line "$d" 1 "$d/review_day1_noon.jpg" "$d/hunt_day12_noon.jpg")
  echo "  accepting: $acc"
  case "$acc" in
    "framesStaged=2/2 framesRows=2 framesUnstaged=[none]")
      echo "sim-shots-stage --selftest: ok — a run that photographed both rows reads 2/2" ;;
    *) echo "sim-shots-stage --selftest: FAILED THE CASE IT MUST ACCEPT — two fresh pictures for two rows did not read 2/2"; exit 2 ;;
  esac
  # REJECTING CASE: the real fault of 25 August — a row whose picture is last
  # week's file, untouched by this run, plus a row with no picture at all.
  snap
  printf 'shot\tmeanLuma\nday1_noon\t0.3\nday12_noon\t0.079\nday13_noon\t0.495\n' > $d/frames.tsv
  echo newer1 > $d/review_day1_noon.jpg
  rej=$(frames_staged_line "$d" 1 "$d/review_day1_noon.jpg" "$d/hunt_day12_noon.jpg")
  echo "  rejecting: $rej"
  case "$rej" in
    *"framesStaged=1/3"*"day12_noon/day13_noon"*)
      echo "sim-shots-stage --selftest: ok — a stale picture and a row with no picture are both named" ;;
    *) echo "sim-shots-stage --selftest: FAILED THE CASE IT MUST REJECT — a stale hunt_ frame counted as photographed"; exit 2 ;;
  esac
  nol=$(frames_staged_line "$d" 0)
  echo "  never-ran: $nol"
  case "$nol" in
    *"framesStaged=no-ledger-this-run"*)
      echo "sim-shots-stage --selftest: ok — no ledger prints words, not 0/0" ;;
    *) echo "sim-shots-stage --selftest: FAILED — a run with no ledger must not read as a clean zero"; exit 2 ;;
  esac
  exit 0
fi

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
# `hunt_*` RIDES THE SAME FLAG AND HAD TO BE NAMED HERE OR IT WOULD NOT EXIST.
# The sim writes a pair of stills while the detective is running a manhunt —
# the loudest state the game has, and one no committed frame had ever shown,
# because the review quota fills on days 1-2 and the killing is staged around
# day 12. Written by the sim and never staged is the same as never taken, and
# it would have looked exactly like the feature not working.
#
# Same flag rather than its own: both come from the sim reaching a screenshot,
# which is the fact the flag records. A run with no manhunt in it simply
# produces no `hunt_` files and the glob is empty — `nullglob` is on above.
# `ref_*` IS THE R1 CONVERGENCE SET — five player-height frames matched to the
# five GTA references (`SimDirector.RefTour`). Named here for the same reason
# `hunt_*` had to be: a glob that is not in this list does not exist to the
# commit, and `frames.tsv` would then carry five rows describing pictures that
# are not on disk — the exact provenance fault `framesStaged` was written for.
# `nullglob` is on above, so a run that took no ref frames contributes nothing.
# `vign_*` IS THE D1b STREET VIGNETTE SET, added here in the same commit
# as the commit script's glob rather than three files away from it,
# because that gap is what this file already carries two paragraphs
# about: one idea, two implementations, and the copy nobody opens is
# the one missing the line.
if [ "$stills" = 1 ]; then files+=("$dir"/review_*.jpg "$dir"/hunt_*.jpg "$dir"/district_*.jpg "$dir"/ref_*.jpg "$dir"/vign_*.jpg); fi
if [ "$frames" = 1 ]; then files+=("$dir/frames.tsv"); fi
# The clip contact sheet is taken once, before day one, so a run can produce it
# and no street stills at all — which is why it gets its own flag rather than
# riding on the stills one. Its ledger goes with it or the sheet is 67 unlabelled
# tiles.
if [ "$clips" = 1 ]; then files+=("$dir/clips.jpg" "$dir/clips.tsv"); fi

# THE MEASUREMENT GOES INTO THE CHANNEL THAT CAN BE READ — the verdict file and
# the per-run copy with it, or the two disagree about one run. STDOUT stays
# paths-only: the caller `mapfile`s it.
staged_line=$(frames_staged_line "$dir" "$frames" "${files[@]}")
for target in "$dir/verdict.txt" "$dir/runs/$sha7.txt"; do
  [ -f "$target" ] && printf 'SimShotsStage: %s\n' "$staged_line" >> "$target"
done
echo "sim-shots-stage: $staged_line" >&2

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
