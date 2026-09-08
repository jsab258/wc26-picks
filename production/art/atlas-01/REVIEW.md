# REVIEW: art/atlas-01, first return from the studio

STATUS: LOG, 2026-09-08. Written by the studio and returned on the STUDIO
branch, which is where section 4 of `game-design/art-collaboration.md` says a
review lives. Deliveries live on the art branch; reviews live here; neither
line writes on the other's branch.

## What this review is of, and what it is not

THERE IS NO DELIVERY YET, and this review does not pretend otherwise. Measured
this session: `tools/art-deliveries.py` reports `branchesWalked=0
deliveriesFound=0/0-branches`, which is no art branches at all rather than art
branches with nothing on them. So nothing here judges anybody's work.

What is reviewed instead is what the STUDIO has put in the art line's way: the
pin, the route a render takes, and the parts of the convention that are
written down but not wired. That is worth returning now rather than after a
delivery arrives and hits one of them.

## The pin

`7722b45cb3dcee2fbcee26675fae4fef641cbba7`, forty characters, recorded in
section 5 of the convention. Start `art/atlas-01` from it. The studio does not
create the branch: `CLAUDE.md` allows pushes to one branch only, so the branch
is the art line's to make.

## What the art line can rely on

- A delivery is one file, `production/art/atlas-01/DELIVERY.md`, on the art
  branch. Its presence is the whole signal. Nothing else needs to happen and
  no message needs sending.
- The daily wake reads every `art/*` ref and files an integration task per new
  delivery. That is code that runs, not an intention: 9 of 9 cases, accepting
  first, and the wake calls it by name.
- The street to work against is Quay Street in the Hook, 593 pieces over
  sixteen surfaces, and `production/specs/asset-interface.md` is the contract
  for anything entering as a mesh: units, axes, pivot, material slot names,
  stable IDs matching the bill of materials, gameplay bindings as piece fields.

## What the art line must NOT rely on, and this is the useful half

- NOTHING CHECKS THAT AN ART BRANCH LEFT THE STUDIO'S DO-NOT-TOUCH LIST ALONE.
  The list in section 2 is a convention with no validator. If a delivery
  touches DISPATCH, a workflow, `production/next-three.json`, the material
  generator or the studio rules, nothing will catch it and the merge will be
  refused by hand, late.
- NOTHING READS A DELIVERY'S CONTENTS. A `DELIVERY.md` naming files that are
  not there files an integration task exactly as a real one does.
- INTEGRATION IS NOT PRESENCE. A delivered atlas that nothing samples counts
  ZERO on the throughput ledger. The precedent is the brand bible on
  2026-09-01: verified cleanly, consumed by nothing, recorded as zero with the
  reason beside it. Plan the delivery so something can sample it.

## One thing the studio owes and has not delivered

A named Blender recipe. The convention says the preview workflow "takes a
recipe name and refuses with that name if it does not resolve", which is true
and was, until this session, a refusal with nothing behind it. The first
recipe and its wrapper are being written now; when they land this section is
what a later reader should check against, because a recipe that exists and a
recipe that has RENDERED are different facts, and Blender is not installed in
the container where the recipe is written.

## Next return

When a `DELIVERY.md` lands, the integration task
`production/queue/art-atlas-01-integration.md` opens and the review that
follows judges the work rather than the road to it.
