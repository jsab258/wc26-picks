line: simulation (Core, the law the project is named for)
spec: external audit by a different model family, 2026-09-06, verified by Jafar and re-verified by the resident in the code
acceptance: no model-selected effect can alter state without a check that CAN refuse; the rejecting case is a test that fails if the branch is restored; and the CoreTests case that skips Checks.None while proving checks can fail either covers it or is deleted as a false certificate
max_sessions: 2
status: P0 STOP-THE-LINE, ready 2026-09-06. Ahead of every other item. systems-builder, then a director review because this is Core.

## The hole, read in the code rather than taken on report

`ledger/Assets/Scripts/Core/IntentRouter.cs:457` takes `check`, `effect` and a
magnitude STRAIGHT FROM THE MODEL'S JSON. `Checks.Known("none")` is true, so
`check:none` is in the vocabulary and passes the gate at line 459.

`ledger/Assets/Scripts/Core/Adjudicator.cs:62`:

    case Checks.None:
        break;

It breaks out of the switch and falls through to `Pass`. Every other branch can
return `Adjudication.Fail`. THIS ONE CANNOT REFUSE ANYTHING. DialogueUI then
applies the effect to real state.

So the model both proposes the action AND selects the check that would have
constrained it, and it may select the one that never says no. THE MODEL IS
ADJUDICATING, inside the layer this project is named for.

## Why our gates certified it green

The CoreTests case at roughly line 4095, which exists to prove checks CAN fail,
SKIPS `Checks.None`. So the suite's own proof of refusability is taken over a
set chosen to exclude the one member that cannot refuse. That is not a test
that missed a case; it is a test whose denominator was trimmed to the cases
that pass. It certifies the hole.

## What the fix must do, and what it must not

A model-supplied `check` may narrow what happens, never remove the constraint.
The honest shapes: `none` stops being accepted from model JSON at all; or
`none` routes to a check that can still refuse on magnitude, target and state.
Whichever, THE EFFECT MUST NOT REACH STATE ON THE MODEL'S OWN SAY-SO.

DO NOT fix this by clamping magnitude alone. A small unrefusable change is
still the model adjudicating, and the audit's point is the authority, not the
size.

## Both halves, and the rejecting case is the deliverable

Accepting: a legitimate novel action with a real check still passes, and the
existing behaviour of every other branch is unchanged.
Rejecting: a crafted intent with `check:none` and a state-altering effect is
REFUSED, and the test fails if the `break` is restored. A fix whose test still
passes with the old code has proved nothing.
