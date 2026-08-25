# Decision — the dressing batch, signage, and the US diamond (director, 25 Aug 2026)

> **STATUS — LOG, 2026-08-25. NOT CURRENT after the batch commit and the
> audit-fix commit both land.** Director ruling on the 1,792-line builder
> batch (KitDressing, lamp forms, StreetDressing, spec corrections, the
> animation direction guard, the unpinned fixture, the works-lamp fix).
> Claims verified tier-2 before this spawn; director spot-checks done this
> session: `WorldBuilder.RegisterStreetLight` exists and `StreetDressing`
> lights are born dark (StreetDressing.cs:498, WorldBuilder.cs:39, and the
> tier-2 audit's md5-pinned re-read independently confirms); `walk_start`
> on disk is `Start Walking Backwards` with the guard's history block
> naming the fault (pick_animations.py:404-417); the `StreetDressing.Build()`
> call site is WorldBuilder.cs:340 (the brief said 323 — the file grew;
> substance holds). This file is the decision RECORD the strengthened
> `director_cadence` is designed to require — a spawn row alone certified
> this very batch as reviewed while the reviewer was dead.

## A — COMMIT NOW. Commit is not dispatch.

One reviewed commit for this batch; this ruling is that review. Reasons,
in order of weight:

1. ~1,800 uncommitted lines in a container that has rolled its checkout
   back three times TODAY is the largest live risk on the board. "Push
   the moment it is green" is the habit that has made every rollback
   free; holding the batch is the one state in which a rollback costs.
2. Holding buys nothing. The batch cannot be measured either way while
   dispatch is barred — so the only effect of waiting is to couple this
   batch's fate to the hang fix, which is the mirror image of what "red
   fixes never wait for a batch" exists to prevent. A batch does not
   wait for a red fix either.
3. The image-generation round trip is a deliverable Jafar is actively
   waiting on and it is blocked behind this tree.

Structure: (a) this batch lands now as one commit; (b) the eleven
tier-2 measurement fixes land as a SECOND reviewed commit — they are
builder work and need their own review row; (c) the hang fix commits the
moment it is green, independently, as a red fix.

**Condition on re-dispatch, not on commit:** the dispatch bar lifts only
after the hang fix AND at least the parser-breaking audit fixes (the
double-`=` token, C1) have landed. The first build back is the run whose
numbers everyone will read; sending it out with an instrument that
prints unreadable tokens wastes the exact round trip we are starving for.

## B — The welded diamond REJECTS. The rolled plate is conditional.

`road-sign-warning` (diamond welded to post): **PLACE → REJECT.** A
MUTCD diamond on a post is one of the loudest single "wrong country"
tells a street can carry, and the premise — a British port town,
late-analog — outranks a free asset every time. Britain warns with
triangles (Worboys); a diamond warning sign has never stood on a
British street.

`road-sign-object-warning` rolled 45°: **honest dressing IF AND ONLY IF
the face carries no US livery after the roll.** Geometry is
country-neutral once it reads as a square, and rectangular information
plates are genuinely British; the FACE carries the nationality. If the
baked texture keeps the yellow warning livery — now rotated 45° — it is
a fake and rejects with its sibling. And per rule 4: the outline method
measured symmetry, not what the plate reads as at street distance, so
whichever way this lands it is confirmed off the first still, not off
the apex-midpoint number.

## C — Signage is a named gap, not a hole in the batch. It queues HIGH.

The batch boundary was reached; holding 1,792 landed lines hostage to
unbuilt work inverts the batch rule. The gap is legible every run
(`sign_post:nothing-offered`), which is rule 3b satisfied. But this is
not ordinary queue filler: **street nameplates are the single
highest-value signage item** — visible (Jafar's sequence puts visual
first) and a direct feed of the information moat, because named streets
with no way to read a name is the moat with a hole in it. Queue item
"signage — street nameplates first", at or near the top of `## Now`
once the hang fix and audit fixes land. First task inside it: see D.

## D — First working, closes as such — with two exceptions that do NOT close.

- **`kitAlbedo`'s 24-key cap, now 6 keys short, is not a rung — it is a
  cap that is currently BITING**, and a cap that bites silently is an
  instrument fault (rule 3b). It goes into the audit-fix commit: raise
  it or make it announce; raising is the one-line class.
- **The twice-duplicated private TextMesh lettering idiom does not
  defer past signage.** Building C would mint a third private copy, and
  one-idea-N-implementations is this project's most-documented bug
  shape. Extract-to-one-shared-tested-implementation is the signage
  item's first task.

Onto the quality ladder by name: pub-sign board (mast ships an arm with
no plate — build the board); British terrace + correct-country houses —
next rung currently blank, so by the standing rule that is a RESEARCH
task (fetch sources, nothing purchased), not a finished aspect.

## E — Bank the re-pick; attach it to the image-gen delivery.

Do not send a separate ask. The image-gen round trip is already a
message he must receive the moment the tree unblocks (which A does);
the re-pick rides in that same message as a second one-click item.
One interruption, two items, plain terms. Nothing is red meanwhile —
the guard makes `walk_start` unpickable, so the cost of waiting is a
missing start animation, a rung not a fault. It goes on the queue so it
survives the session.

## Not ruled on

- The hang diagnosis and heartbeat design — in flight, tier-3; the
  resident reviews the diffs.
- The eleven audit findings individually — verifier finding stands, no
  tier conflict was raised, builder is fixing; only their ORDERING is
  ruled above (parser-breaking ones gate re-dispatch).
- The cfg 1.0/2.0 A/B probe — the shape (measure before paying the cost
  on all fourteen images) is correct and needs no ruling.
- The `director_cadence` artifact-gate implementation — direction
  endorsed (the decision-record variant CLAUDE.md already names as
  stronger; my own death proved the spawn-row version certifies nothing);
  the implementation is a builder brief the resident reviews.

---

## Resident note — how ruling A's dispatch bar is satisfied (25 Aug, after the diagnosis)

**The ruling was written before the hang diagnosis existed, and the diagnosis
removes the thing the bar was waiting for.** A's condition reads "the bar lifts
only after the hang fix AND the parser-breaking audit fixes land". There is no
hang fix: the engineer changed no code, could not demonstrate a cause in its
own files, and recommends **re-dispatching as the discriminating test** — it
costs the same one round trip as a speculative fix and, unlike a fix, cannot be
wrong. The director named the hang work as something it was explicitly NOT
ruling on and left it to the resident, so this is a reading, not an override.

**The condition is met by the CHANNEL fixes rather than by a behaviour fix.**
`ledger-build-windows.yml` already computes `$timedOut` and `$p.ExitCode` and
throws both away, so "killed at 24 minutes" and "crashed" arrive identical;
`simExit` / `simTimedOut` / `simWaitSeconds` plus an in-sim watchdog that beats
the external kill are being built now. With those in, **the first build back
classifies itself** — which is what "the first build back is the run everyone
reads" was protecting. Land the channel fixes and the parser fixes, then
dispatch.

**A discriminating dispatch of `e8c5949` alone is NOT currently executable, and
that is worth knowing before anyone plans around it.** `.github/workflows/
ledger-build-windows.yml` declares bare `workflow_dispatch:` with **no inputs**,
and dispatch resolves a branch or tag rather than a commit — the runner checks
out whatever the ref points at when it STARTS. Pinning `e8c5949` would need
either a pushed tag (a ref nobody asked for) or a `ref` input on the workflow.
**Neither is worth doing on spec:** the bisect is two wide (`677beb64` and
`e72f58a3` are the only two of fourteen unbuilt commits touching
`ledger/Assets`), and a green run kills the question outright. Add the workflow
input only if the next run stalls again — then it is worth a round trip and not
before.

**And the intermittent candidate is live, contrary to what I told the engineer.**
Counted over every kept run: 352 total, 3 with no done line. Rare, not
unprecedented. My earlier "1 in 60, so intermittent is dead" was wrong twice
over — see the queue's hang item for the IK half, which was worse.

---

## Director addendum — the resident's reading of A is RATIFIED (25 Aug, on resume)

The note above is confirmed as the ruling, not merely a reading. "The hang
fix" was written on the assumption a demonstrated cause existed; with no code
changed and a bisect only two wide, **re-dispatching behind a channel that
classifies its own death IS the cheapest decisive measurement**, and a
self-classifying first build is exactly what the bar was protecting. Condition
A therefore reads, finally: the channel fixes (`simExit` / `simTimedOut` /
`simWaitSeconds` + the in-sim heartbeat) landed AND the parser-breaking audit
fixes landed. Two riders:

1. **The parser half is still OPEN on disk** — checked this session, this
   spawn: `SimDirector.cs:16246` still emits `kitDressing={...Line()}`, the
   double-`=` token of audit finding C1. The stamp below unblocks the COMMIT;
   it does not lift the dispatch bar. Nobody dispatches on the strength of
   this file until that emit is fixed and the channel fixes are in.
2. **The ref-input judgement is endorsed as written**: a green run kills the
   question, so the `workflow_dispatch` ref input is adjacent work with a
   name, built only if the next run stalls again.

Noted without ruling: two numbers fed to the diagnosis were wrong and both are
corrected in `queue.md` with the false sentences kept quoted — the right
correction shape; the IK "regime break" was a printed field compared against a
channel that healthy runs cannot emit into, which is rule 3b's
absent-denominator fault wearing a log gate's clothes.

<!--RULING spawn=2026-08-25T19:26:14Z-->
