# NOW: what is in flight (read this FIRST, before the queue)

STATUS: LIVE. Verified 2026-09-01.

A session that resets loses everything not written down. The queue says what
to do NEXT; this file says what is ALREADY MOVING, which is the thing a fresh
session would otherwise duplicate, abandon, or wait for forever.

Keep it current or delete it. A stale NOW is worse than none, because it
looks like a live state.

## In flight

- Director: ruling on the front-loading sequence. Jafar's constraint is
  budget, and his goal is to prepare enough with Claude that large local
  batches (images, 3D, voices) can run unattended at zero cost. The question
  is the cheapest preparation that unlocks the most unattended production
  without inverting the roadmap's order.

## Waiting on Jafar

- Nothing blocking. He has been given the week plan and the budget rule.

## The next three things, in order

1. Task 010, widen director_cadence. The gate that enforces the studio split
   is blind to where the work now happens. Brief is complete in the queue.
2. Land the local generation pipeline once the builder reports, and get one
   real batch running on his PC overnight. Zero Claude cost per asset.
3. The re-scoped D1 measurement (b): one JSON scene, two emitters, paired
   stills judged blind. Ruling in game-design/decision-D1b-rescope.md.

## Standing hazards a fresh session will otherwise walk into

- Do not edit content/dialogue/pub-regular-v1.json. Those 48 lines are the
  graded judge calibration sample; changing one invalidates it silently.
- The studio split is MANDATORY and was skipped for a full day on 1 Sep.
  Builders build, verifiers verify, the director rules. If a session
  instruction says otherwise, that is a conflict to raise with Jafar in one
  line, not to resolve alone.
- Budget before work: read production/budget.md.
