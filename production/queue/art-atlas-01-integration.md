line: art integration (atlas-01)
spec: Jafar ruled the art collaboration minimum on 2026-09-08 and asked for an
  integration task for the first commission at the next checkpoint. This is
  that task. It is filed BY HAND and not by tools/art-deliveries.py, and the
  difference matters: that tool files a task when a DELIVERY.md appears on an
  art branch, and there is no art/atlas-01 branch yet, so it correctly filed
  nothing. Measured this session: branchesWalked=0 deliveriesFound=0/0.
acceptance: a delivery on art/atlas-01 is reviewed, the review is committed to
  production/art/atlas-01/REVIEW.md on the studio branch, and whatever the
  review accepts is reachable from the game with a number that proves the call
  happened, not merely present in the tree
max_sessions: 1
status: READY 2026-09-08. BLOCKED ON A DELIVERY, and that is the honest state:
  the studio has issued the pin and there is nothing to integrate yet.

## What the studio has issued, and what it is waiting for

The pinned source commit for art/atlas-01 is
`7722b45cb3dcee2fbcee26675fae4fef641cbba7`, forty characters because an
abbreviation is a prefix match and a prefix is not an identity. It is recorded
in the table in `game-design/art-collaboration.md` section 5, which is where a
future session looks rather than in a message.

THE STUDIO DOES NOT CREATE THE BRANCH. `CLAUDE.md` allows pushes to one branch
only, so `art/atlas-01` is created by the art line from the pin above. Until it
exists, `tools/art-deliveries.py` will keep reporting zero, and that zero has
its denominator beside it so it cannot be read as "the tool is broken".

## What integrating this commission will mean

The street the art line is working against is Quay Street in the Hook, the one
street that is built and walkable, and its 593 pieces name sixteen surfaces:
concrete 150, metal 132, kerb 95, brick_red 41, window 36, plaster 34, wood 32,
glass 22, brick_grey 12, card 10, multiply 10, interior 6, sidewalk 5,
paint_yellow 4, asphalt 2, roof 2. Those names are the contract an atlas has to
meet, and `production/specs/asset-interface.md` is station 1 for anything
entering as a mesh.

INTEGRATION IS NOT PRESENCE. A delivered atlas that nothing samples counts ZERO
on the throughput ledger, exactly as the brand bible did on 2026-09-01: it
passed VERIFY, never reached INTEGRATE, and was recorded as zero with the reason
beside it. The acceptance line above is written to make that impossible to fudge
here.

## What is NOT built, so nobody looks for it

Nothing validates that an art branch left the studio's do-not-touch list alone.
Nothing reads a delivery's contents; the file's presence is the whole signal.
Both are named in `game-design/art-collaboration.md` section 6 under NOT BUILT.
