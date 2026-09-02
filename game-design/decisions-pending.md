# Pending Player Decisions

> **STATUS — LIVE, verified 2026-08-04.** the queue of things only Jafar can answer.
> Kept current. If it is wrong, that is a bug in this file.

Standing queue for anything the autonomous build loop cannot decide alone.
Each entry has options and a recommendation so they can be answered in batch.

## WHAT IS WAITING

Newest first. Every entry says what it means in plain terms, what the options
cost, and what the studio recommends, so it can be answered in one line.

### If the two engines look about the same, which one wins? (added 2026-09-02)

**In plain terms.** You removed the deadline so Unreal gets the time it
needs. Good. But the engine test still has a tie-breaker written into it from
before: if neither engine's picture is clearly better, we pick Unity. Nobody
has checked that with you, and it now matters more, because with no deadline
the likeliest outcome is not "Unreal loses" but "they look close".

**Why it is a real question and not a formality.** A tie going to Unity means
the safe, already-working option wins by default. That is defensible: it is
where the game already runs, and switching costs months. But you have just
said the visual ceiling is what serves the main goal, and a rule that breaks
ties toward the familiar option is a thumb on the scale against exactly that.

| | what it means | what it costs |
|---|---|---|
| A | **Ties go to Unity (RECOMMENDED, and it is the existing rule).** Unreal has to be visibly better to win, not merely equal. | Nothing new. If they tie, we keep the working engine and the months that switching would cost. |
| B | **Ties go to Unreal.** Equal-looking means we take the engine with the higher ceiling for later. | The switch cost, paid on a comparison that by definition showed no advantage today. |
| C | **A tie means keep looking.** Neither wins; we improve the scene and compare again. | Time, with no guarantee the second look is more decisive than the first. |

**The studio recommends A**, on the grounds that "equal" is not evidence for
a change this expensive. If a picture later changes your mind, that is a
better reason than a tie-break rule.

## ANSWERED, kept for the reasoning (these do NOT count as waiting)

An answered card is demoted from `###` to `####` so the dashboard's inbox
count means "waiting on Jafar" and nothing else. The reasoning stays,
because why a thing was decided outlives the decision.

#### ANSWERED 2026-09-02: the engine deadline is REMOVED, and Unreal gets more time, not less

Jafar's ruling, verbatim: "yes but forget the deadline, it's not relevant.
doesn't make sense to set a hard deadline when we can work continuously, we
are limited by 5h and weekly usage limits in claude. rather spend more time
to get UE working, that's what will help us achieve our main goal"

THIS IS BIGGER THAN THE QUESTION ASKED. The question was how to close D1 if
Unreal ran out of time. The answer removes the clock the question depended
on, and with it the premise underneath: a calendar deadline was never the
real constraint. The real constraint is Claude usage, which is measured in
hours and weeks of budget rather than dates, and the project runs
continuously.

What follows, and the director works it through rather than the resident:
the 2026-09-14 timebox in decision-D1b-rescope.md and roadmap-v2.md is
retired; measurement (a), agent-loop friction, can no longer be failed by a
date; and the standing preference tips toward INVESTING in the Unreal path
rather than defaulting to Unity, because the visual ceiling is what serves
the Meridian Test and Jafar has said so plainly.

Kept here rather than deleted so the reasoning survives: the recommendation
was to pre-register a close so the goalposts could not move after the
result. He removed the goalposts instead, which answers the worry properly.

### How close should strangers stand? (added 2026-08-04, late)

**In plain terms.** When crowds gather on the street, people end up standing
45 cm apart, which is touching distance, and 36 of them can pile into a
two-metre circle. Nothing in the game models personal space. Whether that
reads as a busy street or as a riot is a judgement off a picture, not a
number the studio should pick. STILL LIVE: the code is in `NpcWalker.cs` and
running. Best answered once the street vignette has produced a still, which
is why it has waited.

**The street packs people to exactly one body width and stops, and that is the
separation rule doing precisely what it says.** `NpcWalker.StepApart` pushes two
walkers apart only while they are closer than `BodyWidth` — 0.45m, which is a
measured fact about the meshes rather than a preference — and the push is sized
to just clear that. Its job is to stop bodies interpenetrating, it says so, and
it does it: `crowdGapMedian=0.45`, exactly the bound.

**Nothing in the game models personal space.** Thirty-six people can stand
within two metres of one person with every pair legally 45cm apart, and
`crowdHuddleWorst=36` says they do. Forty-five centimetres between strangers is
touching distance.

I chased this to the wrong place first: I widened the ring people stand on at a
scheduled point, on the theory that the mob was people sent to one spot. The
run disproved it in one line — `busiestPlace=12` against a huddle of 36 — so
these are people who END UP together, not people scheduled together.

**The number cannot come from me.** A spacing constant is a statement about how
a street should READ, and this project's own rule is that "whether a dozen
people in a plaza reads as a street or as a demonstration is a judgement for
Jafar off a still, not a number for me to move against a measured decision."

| | what it means | what it costs |
|---|---|---|
| A | **Leave it.** Overlap prevention only. A busy junction packs tight, like a real one at rush hour. | Nothing. But `review_day5_noon` at `2b38df1` is what that looks like, and it reads as a crowd scene rather than a street. |
| B | **A personal-space radius**, bigger than a shoulder, that eases people apart without a hard push. You pick the number off a still. | Small: `StepApart` already has the loop and the antisymmetry. The risk is a street that looks sparse. |
| C | **Find why they converge at all.** They gather at a junction beside a parked truck, which is nobody's home or work. Something is routing them there. | Unknown until read — and it may make A or B unnecessary. |

**Recommendation: C first, then look at a still and decide between A and B.** If
the convergence is a pathing artefact then spacing them out is decorating a
bug, and this project has now twice fixed the visible half of something whose
cause was elsewhere.

## THE FIRST ONE, ADDED 2026-08-04 EVENING

### What does the player get BETTER at?

**In plain terms.** Right now the player never improves at anything. Their
one capability number only ever goes DOWN, when they get hurt. Your crew get
better; you do not. This decides what a playthrough is FOR, so it is a
question about what the game is rather than a thing to build. STILL LIVE and
untouched by the v2 respec.

**The design scorecard's largest relative gap, and it is a design question
rather than a wiring one.** Character competence scores 10 against a target of
40, and the row's reason is one clause: *"crew have it; the player has none,
and `Harm` only ever subtracts."* Your runners have a competence that changes
how strong a link they leave in a rumour. The player has a capability number
that goes down when they are hurt and never goes up at anything.

**Why it cannot be answered from here.** Every other gap on that table was a
thing built and unwired, and those get fixed by finding the caller. This one is
a statement about what the game is: it decides what a playthrough is FOR,
which is squarely M22 and squarely yours.

**Three shapes, and they are not compatible.**

| | what improves | what it feels like | what it costs |
|---|---|---|---|
| A | **Nothing.** The player is a publican, not an operative. What changes is the WORLD — who owes you, who fears you, which doors opened. | Closest to the moat: the progression is social memory, which is the thing this game is already best at. Also the bravest, because a player who feels no personal growth may read it as flat. | Nothing to build. The competence row gets closed as "deliberately none" and the scorecard target moves. |
| B | **Being believed.** A lie holds better, an alibi survives more scrutiny, people take your word further. Grows by getting away with things. | The double life becoming a SKILL. Fits the information pillar exactly, and the systems to hang it on — `Claims`, `Informing`, `HomicideBook.TestimonyGrade` — already exist and are tested. | A number threaded through the accusation and alibi paths, plus a way to see it. Medium. |
| C | **The body.** Fighting, carrying, not being seen — the conventional axis. | Familiar, and it is the one KCD2 does properly with a real training loop. Competing there is competing where we are weakest. | Large, and it depends on M16's fighting actually running, which it does not. |

**My recommendation is B**, and A is a serious answer rather than a cop-out. B
buys the most for the least because the machinery is already built and tested;
A is defensible and would let the row close honestly tomorrow. C is the one to
say no to explicitly, because it is the default a systems-first project drifts
into and it plays to the one strength we have decided not to chase.

**Nothing is blocked on this** — there is other work for weeks. It is here
because it is the largest thing on the scorecard that I should not decide.

## NOTHING ELSE IS WAITING ON JAFAR — still true 2026-08-04

The queue is empty for the first time since it was opened. The last three were
answered together:

| | decision | answer |
|---|---|---|
| 1 | Is cloning a cast donor's voice inside the consent rule? | **YES — proceed.** The nineteen cast VCTK speakers may be cloned. The rule that produced them stands: donated corpora only, no identifiable public figures, ever. |
| 2 | Do the 15 named characters without a voice get cast? | **YES.** Ossei, Zlata, Noor, Halvard and the rest get their own voices rather than falling through to the crowd pool. |
| 3 | Does Phase 3 start before the animation integration? | **Animations first** (Jafar: *"your rec"*). The bodies exist; Phase 3 gets judged on something real rather than on capsules, which is why combat was deferred the first time. |

**Also settled today:** the corpus question (closed by the British decision),
non-verbal foley (the free CC0 route), bark curation (mine, on instruction),
and the Mixamo drop (done 2026-07-30).

**Re-checked 2026-08-04 and still empty.** The one thing that WAS outstanding —
the second Mixamo body fetch — he ran that morning, and eight bodies landed. No
purchase is pending and no decision is blocking the loop.

**And one thing that reads as a pending decision and is not.** The voice engine
question is CLOSED, not open: `production-plan-audio-art.md` §1i is headed
"DECIDED — chatterbox, on the strength of the direction test", four engines were
benchmarked (piper as the control floor, kokoro, xtts, chatterbox), and the
verdicts recorded there are Jafar's own words. Generation is LOCAL and free.
There is nothing to record: the nineteen reference clips in
`game-design/picked-clips/` are VCTK speakers he listened to and picked, and
chatterbox clones identity from those while an exaggeration number carries the
mood. He said it himself on 2026-07-31 and it is quoted in `shopping-list.md`:
*"free obviously. i won't be recording anything."*

Anything new goes below this line.

---

Everything this project has already decided is in `decisions-answered.md`.
