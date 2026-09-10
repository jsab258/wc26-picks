line: production (dialogue and game feel)
spec: game-design/decision-2026-09-06-ruling-113-the-model-does-not-adjudicate.md, section 10 item B
acceptance: a novel action that moves nothing gets an answer from the person the player spoke to, or a narration that does not claim something happened; and NovelLine never says "It lands" when nothing was armed; both proven by a case that fails on the current text
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06. Game feel, found while closing P0. NOT a Core change, so no mandatory director review under the 2026-09-06 narrowing.

## Two faults, both about telling the player something untrue

1. THE SWALLOWED LINE. `DialogueUI.cs:2002-2008` returns before `SayAsync` for
   a `novel/none/nothing` intent, so THE NPC NEVER ANSWERS. The player says
   something to a person and the person does not react; the game narrates
   instead. That is the opposite of the thing this project is built to do.
2. "IT LANDS" WHEN NOTHING DID. `NovelLine` says "It lands" when `ArmFor` is
   null and nothing moved. A narration that reports an effect that did not
   happen is the game lying about its own state, which is the same class as
   the gates this week's audit found green.

## Why it surfaced now

Queue 113 made `none` refuse a state-altering effect, which is correct. The
consequence is that `novel/none/nothing` is now a NORMAL outcome rather than a
rare one, so a path that was seldom taken is about to be taken often. The fix
made an existing feel fault frequent.

## The decision inside it

Whether a novel action that moves nothing should be narrated by the game or
answered by the person. THE PROJECT'S OWN PREMISE ARGUES FOR THE PERSON: the
moat is people who perceive and respond, and a system that quietly narrates
over them is spending the moat to save a call.

## Both halves

Accepting: the player says something that changes nothing and gets a reply
from the person, in character, that does not claim anything moved.
Rejecting: a case that asserts the current behaviour FAILS after the fix. And
"It lands" with a null arm is refused by a test, so the string cannot come
back.
