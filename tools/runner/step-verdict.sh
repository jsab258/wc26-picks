#!/usr/bin/env bash
# SUCCESS, FAILURE AND SKIPPED ARE THREE STATES, AND A SUMMARY THAT KNOWS TWO
# OF THEM INVENTS THE THIRD.
#
# THE INCIDENT. Imagegen run 33654488608 stopped at a setup step, so Actions
# SKIPPED the four work steps. The summary tested each outcome against
# `success` and printed a named cause on anything else, so it announced:
#     SELFTEST FAILED - imagegen.py does not pass its own checks on this machine
#     ATTRIBUTION CHECK FAILED
#     GENERATE FAILED - the exit code says which: 2 disk, 3 setup, ...
# None of that was observed. The selftest passes 123/123 and never ran on that
# machine. Three causes named in the confident voice of a diagnosis, for three
# steps no instrument had looked at, and a reader of that output goes hunting a
# Windows selftest bug that does not exist. That is the project's oldest
# instrument fault: a message describing something the instrument never
# measured.
#
# THE RULE THIS ENFORCES. A cause sentence is printed only for a step that RAN
# and returned non-zero. A step that never ran gets one fact and no theory:
# that it never ran, and the name of the step that stopped the job.
#
# WHY A FILE AND NOT A `run:` BLOCK. Nothing in this container can reach
# ledger-pc, a Windows shell or a self-hosted runner, so a decision written
# inside a workflow step ships UNRUN, and an unrun summariser printing a
# plausible sentence is exactly the failure above wearing a new hat
# (.claude/rules/instruments.md: measurement arithmetic and formatting live
# where the tests run). Here the decision is a file with `--selftest`, both
# outcomes, runnable anywhere, and the workflow supplies only membership,
# order and live state. Same shape as tools/runner/python3-shim.sh.
#
# CONCLUSION VERSUS OUTCOME, WHICH ARE NOT THE SAME FIELD AND ARE THE WHOLE
# TRICK HERE:
#   `steps.x.outcome`    the raw result, BEFORE continue-on-error is applied.
#   `steps.x.conclusion` the result AFTER it, which is what Actions acts on.
# A continue-on-error step that fails has outcome=failure, conclusion=success.
# So --work is fed OUTCOMES (the truth about whether the work happened) and
# --setup is fed CONCLUSIONS (a step stops the job only when its conclusion is
# failure). Feeding outcomes to --setup would name a step that stopped nothing.
#
# CALLERS: .github/workflows/ledger-imagegen.yml, steps `Commit what arrived,
# by name` (--stopper-only, so the stopper reaches the COMMITTED verdict and
# not only a log nobody can fetch) and `The verdict, named step by step`.
#
# SELFTEST, ACCEPTING CASE FIRST, RUNNABLE ANYWHERE:
#     bash tools/runner/step-verdict.sh --selftest
set -u

NL="
"
SEP=$'\t'

SETUP=""      # ordered name=conclusion,... for every step before the work
WORK=""       # ordered name=outcome,... for the work steps
NONGATING=""  # comma list of work step names whose non-success is not red
CAUSES=""     # name<TAB>sentence per line, printed only on a real failure

# A TRAILING NEWLINE, BECAUSE `while read` DROPS A LAST LINE THAT LACKS ONE.
# Without it this file's own selftest saw `examined=3` on a four-step list and
# missed `sha=failure` as the stopper, which is the exact fixture it exists to
# catch. The accepting case is what found it.
split_commas() { printf '%s\n' "$1" | tr ',' '\n'; }

cause_for() {
  local k v
  while IFS="$SEP" read -r k v; do
    [ "$k" = "$1" ] || continue
    printf '%s' "$v"
    return 0
  done <<EOF
${CAUSES}
EOF
  printf '%s' "the step ran and returned non-zero; no cause sentence was supplied for it"
}

# THE STOPPER: the FIRST step in declared order whose CONCLUSION is failure.
# First, not any: once Actions skips the rest, every later step's conclusion is
# `skipped`, and the one that stopped the job is the earliest red one.
find_stopper() {
  local pair
  while read -r pair; do
    [ -n "$pair" ] || continue
    if [ "${pair#*=}" = "failure" ]; then
      printf '%s' "${pair%%=*}"
      return 0
    fi
  done < <(split_commas "$SETUP")
  printf 'none'
}

summarise() {
  local stopper pair name state gating bad=0
  local examined=0 ok=0 failed=0 skipped=0 unknown=0
  stopper="$(find_stopper)"

  local tail_sentence
  if [ "$stopper" = "none" ]; then
    # A SKIP WITH NO RED SETUP STEP IS ITS OWN FINDING, not a blank. It means
    # the thing that stopped the job is not in the list this summary was
    # handed, which is a fault in the CALLER and has to be readable as one.
    tail_sentence="and NO step in the list this summary was given reported a failure, so what stopped the job is not in that list: the caller's --setup is missing a step"
  else
    tail_sentence="the job stopped at the step '$stopper'"
  fi

  while read -r pair; do
    [ -n "$pair" ] || continue
    name="${pair%%=*}"
    state="${pair#*=}"
    examined=$((examined + 1))
    gating=yes
    case ",${NONGATING}," in *",${name},"*) gating=no ;; esac
    case "$state" in
      success)
        ok=$((ok + 1))
        ;;
      failure)
        # IT RAN AND RETURNED NON-ZERO. The cause sentence describes something
        # that was actually observed, so it is printed.
        echo "$name FAILED - $(cause_for "$name")"
        failed=$((failed + 1))
        [ "$gating" = yes ] && bad=1
        ;;
      skipped)
        # IT NEVER RAN. NOTHING about it was measured, so no cause is printed:
        # this is the whole reason the file exists.
        echo "$name SKIPPED - it never ran, so nothing at all is known about it; $tail_sentence"
        skipped=$((skipped + 1))
        [ "$gating" = yes ] && bad=1
        ;;
      *)
        # `cancelled`, or an empty string when Actions recorded no outcome for
        # the step at all. Named as unreadable rather than guessed at.
        echo "$name NO-READABLE-OUTCOME - Actions reported '${state:-<empty>}' for it, which is neither success, failure nor skipped; $tail_sentence"
        unknown=$((unknown + 1))
        [ "$gating" = yes ] && bad=1
        ;;
    esac
  done < <(split_commas "$WORK")

  # EVERY ZERO SHIPS ITS DENOMINATOR (CLAUDE.md rule 3b), and a summary that
  # examined nothing says so in words rather than printing a clean-looking
  # zero. Whole-run numbers, one line, no spaces inside a value.
  if [ "$examined" -eq 0 ]; then
    echo "workSteps nothing measured - this summary was handed an empty --work list, so its silence about every step is ignorance and not a pass"
    bad=1
  else
    echo "workSteps examined=$examined success=$ok failed=$failed skipped=$skipped noReadableOutcome=$unknown stopper=$stopper nonGating=${NONGATING:-none}"
  fi
  return "$bad"
}

# ---------------------------------------------------------------- selftest --
_run() { # feed one fixture through the whole thing, capture output and rc
  ( SETUP="$1"; WORK="$2"; NONGATING="$3"; CAUSES="$4"; summarise; echo "rc=$?" )
}

_want() { # description, haystack, needle
  case "$2" in
    *"$3"*) echo "  ok   $1" ;;
    *) echo "  FAIL $1"; echo "       wanted to find: $3"; echo "       in: $2"; BAD=1 ;;
  esac
}

_wantnot() {
  case "$2" in
    *"$3"*) echo "  FAIL $1"; echo "       must NOT contain: $3"; echo "       in: $2"; BAD=1 ;;
    *) echo "  ok   $1" ;;
  esac
}

selftest() {
  BAD=0
  local C out
  C="selftest${SEP}imagegen.py does not pass its own checks on this machine${NL}generate${SEP}the exit code says which: 2 disk, 3 setup${NL}"

  local ALLOK="Checkout=success,paths=success,shim=success,workspace=success,sha=success"

  # ACCEPTING CASE FIRST: everything ran and passed. Green, no cause sentences,
  # and the denominator is still printed.
  out="$(_run "$ALLOK" "selftest=success,probe=success,generate=success,attribution=success" "probe" "$C")"
  _want "ACCEPTING: all four succeeded is green" "$out" "rc=0"
  _wantnot "ACCEPTING: a green run names no failure" "$out" "FAILED"
  _wantnot "ACCEPTING: a green run names no skip" "$out" "SKIPPED"
  _want "ACCEPTING: the denominator ships even when nothing is wrong" "$out" "examined=4 success=4 failed=0 skipped=0"

  # THE RUN-1 FIXTURE, VERBATIM, AND IT IS THE REASON THIS FILE EXISTS.
  # Setup step `sha` red, all four work steps skipped.
  out="$(_run "Checkout=success,paths=success,shim=success,workspace=success,sha=failure" \
              "selftest=skipped,probe=skipped,generate=skipped,attribution=skipped" "probe" "$C")"
  _want "run-1: a skipped step is called SKIPPED" "$out" "selftest SKIPPED - it never ran"
  _wantnot "run-1: a skipped step NEVER prints its cause sentence" "$out" "does not pass its own checks"
  _wantnot "run-1: a skipped step is never called FAILED" "$out" "FAILED"
  _want "run-1: the step that stopped the job is named" "$out" "the job stopped at the step 'sha'"
  _want "run-1: the counts separate skipped from failed" "$out" "examined=4 success=0 failed=0 skipped=4"
  _want "run-1: a run that banked nothing is still red" "$out" "rc=1"

  # A REAL FAILURE, which is the case whose cause sentence IS an observation.
  out="$(_run "$ALLOK" "selftest=failure,probe=success,generate=success,attribution=success" "probe" "$C")"
  _want "failure: the step that ran and failed is called FAILED" "$out" "selftest FAILED"
  _want "failure: and its cause sentence is printed, because it was observed" "$out" "does not pass its own checks"
  _wantnot "failure: a step that ran is never called SKIPPED" "$out" "selftest SKIPPED"
  _want "failure: red" "$out" "rc=1"

  # MIXED, because the interesting case is one step failing while others ran:
  # only the failing step's cause may appear.
  out="$(_run "$ALLOK" "selftest=success,probe=success,generate=failure,attribution=success" "probe" "$C")"
  _want "mixed: only the failing step's cause is printed" "$out" "generate FAILED - the exit code says which"
  _wantnot "mixed: the passing step gets no sentence at all" "$out" "selftest"
  _want "mixed: counts" "$out" "examined=4 success=3 failed=1 skipped=0"

  # NON-GATING: the probe is a finding, not a gate. It must still be REPORTED.
  out="$(_run "$ALLOK" "selftest=success,probe=failure,generate=success,attribution=success" "probe" "$C")"
  _want "non-gating: a non-gating failure is still printed" "$out" "probe FAILED"
  _want "non-gating: and does not turn the summary red" "$out" "rc=0"

  # THE STOPPER IS THE FIRST RED SETUP STEP, not the last and not any.
  out="$(_run "Checkout=success,paths=failure,shim=failure,workspace=skipped,sha=skipped" \
              "selftest=skipped,probe=skipped,generate=skipped,attribution=skipped" "probe" "$C")"
  _want "stopper: the FIRST red setup step is the one named" "$out" "stopped at the step 'paths'"
  _wantnot "stopper: a later red step is not named as the stopper" "$out" "stopped at the step 'shim'"

  # A SKIP WITH NO RED SETUP STEP IS A CALLER FAULT AND SAYS SO.
  out="$(_run "$ALLOK" "selftest=skipped,probe=skipped,generate=skipped,attribution=skipped" "probe" "$C")"
  _want "no stopper: the gap is named rather than left blank" "$out" "not in that list"
  _want "no stopper: and the key says none" "$out" "stopper=none"

  # AN UNREADABLE OUTCOME IS NOT QUIETLY A FAILURE.
  out="$(_run "$ALLOK" "selftest=,probe=success,generate=success,attribution=success" "probe" "$C")"
  _want "empty outcome: named as unreadable, not diagnosed" "$out" "selftest NO-READABLE-OUTCOME"
  _wantnot "empty outcome: no cause sentence is invented for it" "$out" "does not pass its own checks"
  _want "empty outcome: counted in its own column" "$out" "noReadableOutcome=1"

  # NOTHING MEASURED IS NOT A PASS.
  out="$(_run "$ALLOK" "" "probe" "$C")"
  _want "empty work list: says nothing measured, in words" "$out" "nothing measured"
  _want "empty work list: and is red, because silence is not a pass" "$out" "rc=1"

  # A FAILURE WITH NO SUPPLIED CAUSE STILL SAYS ONLY WHAT IS KNOWN.
  out="$(_run "$ALLOK" "attribution=failure" "" "$C")"
  _want "missing cause: says the step returned non-zero and nothing more" "$out" "no cause sentence was supplied"

  # --stopper-only, which is what puts the stopper in the COMMITTED verdict.
  out="$( SETUP="Checkout=success,paths=success,shim=success,workspace=success,sha=failure" find_stopper )"
  _want "stopper-only: prints the bare name for the verdict's steps string" "$out" "sha"
  out="$( SETUP="$ALLOK" find_stopper )"
  _want "stopper-only: prints none when nothing stopped the job" "$out" "none"
  _wantnot "stopper-only: never prints a value with a space in it" "$out" " "

  echo "step-verdict selftest: $( [ "$BAD" -eq 0 ] && echo "PASS" || echo "FAILED" )"
  return "$BAD"
}

# ------------------------------------------------------------------- args --
STOPPER_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --setup)       SETUP="$2"; shift 2 ;;
    --work)        WORK="$2"; shift 2 ;;
    --non-gating)  NONGATING="$2"; shift 2 ;;
    --cause)       CAUSES="${CAUSES}${2%%=*}${SEP}${2#*=}${NL}"; shift 2 ;;
    --stopper-only) STOPPER_ONLY=1; shift ;;
    --selftest)    selftest; exit $? ;;
    *) echo "step-verdict.sh: unknown argument '$1'" >&2; exit 2 ;;
  esac
done

if [ "$STOPPER_ONLY" -eq 1 ]; then
  find_stopper
  echo
  exit 0
fi

summarise
exit $?
