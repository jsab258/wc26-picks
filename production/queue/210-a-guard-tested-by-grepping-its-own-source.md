line: instrument
spec: The case asserting that .claude/hooks/wake-drain.sh models exit 15 does it by grepping
  the hook's own source for the string "    15)". A wrong arm body and an unmodelled
  fallthrough both exit 0, so the accepting case passes either way. Assert the BEHAVIOUR
  instead: on the opt-out run, PERMIT-UNASSESSED must be ABSENT and the reason must read
  opted-out.
acceptance: the live hook passes, and a planted hook whose 15 arm body is wrong or missing
  FAILS the case rather than passing it.
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09, found by the director reviewing the change that shipped it, in the
  same session it shipped.
  IT IS THE FAULT THIS PROJECT NAMES MOST OFTEN, one layer in: a guard whose accepting case
  cannot fail is not a guard. Grepping a file for the shape of a branch proves the branch was
  TYPED, never that it RUNS or that it does the right thing when it does.
  THE FIX IS ONE LINE and the rung already exists beside it: _run_hook executes the real bash
  file, so the behavioural assertion costs nothing that is not already paid for.
