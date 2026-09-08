# Art collaboration: the minimum, and what is actually wired

> **STATUS: LIVE, verified 2026-09-08.** Ruled by Jafar in session, as the
> minimum needed for an art line to work beside the studio line without the
> two colliding. He asked for exactly this and nothing more, and he asked for
> one distinction to be kept visible throughout: a RECORDED CONVENTION is not
> a WORKING CONSUMER, and neither is an EXECUTABLE RUNNER PATH. Section 6
> states which of the three each item below is, measured rather than claimed.

## 1. Branches

Art branches are named `art/<commission>`. One commission, one branch.

Every art branch STARTS FROM A STUDIO-PINNED COMMIT, issued by the studio and
recorded in section 5. It is not "latest": an art line that rebases onto a
moving studio branch spends its time on merges instead of on art.

## 2. What art work never touches

Art work happens in a SEPARATE CHECKOUT, never in the studio's, and it never
touches any of these, on any branch:

- DISPATCH and the runner discipline (`ledger-v2/studio-v2/runner.md`)
- anything under `.github/workflows/`
- `production/next-three.json`
- the material generator
- studio rules: `CLAUDE.md`, `.claude/rules/`, `ledger-v2/studio-v2/`

The list is short on purpose. Everything on it is a thing that, changed from
two places at once, breaks the studio's ability to measure itself.

IN-HOUSE CLAUSE, ruled 2026-09-08. A spawned designer has no separate
checkout. It writes only under `production/art/<commission>/` in the studio
checkout, and the resident prints `git status --porcelain` before committing to
prove this list held. The separate-checkout sentence above still governs an
outside delivery and a designer given its own clone; it does not govern a
spawn, which never had one.

## 3. A delivery

A delivery is one file: `production/art/<commission>/DELIVERY.md`, committed
on that art branch. Its presence is the signal. Nothing else needs to happen,
and no message needs to be sent.

## 4. What comes back

- A review returns as `production/art/<commission>/REVIEW.md`, on the STUDIO
  branch, under the matching commission directory. Deliveries live on the art
  branch; reviews live here. Neither line writes on the other's branch.
- Taste questions go to Jafar as Telegram cards. Not in a review file, not in
  a brief, not in session output.

## 5. Commissions and their pinned commits

| commission | branch | pinned source commit | issued |
|---|---|---|---|
| atlas-01 | `art/atlas-01` | `7722b45cb3dcee2fbcee26675fae4fef641cbba7` | 2026-09-08 |
| atlas-02 | `art/atlas-02` | `f3f395c5dda6be684183ef4f02c1d0a533207bbf` | 2026-09-08 |

The pin is the full forty characters on purpose. An abbreviation is a prefix
match, and a prefix is not an identity.

THE ART LINE MOVED IN-HOUSE on 2026-09-08 by Jafar's standing order, and the
convention above did not change with it, which is the point of having written
it down before there was anyone to follow it. `atlas-01` was an outside
delivery; `atlas-02` continues it in-house, delivered on 2026-09-08 by a
content-wrangler spawn under this convention (the spawn log has no
`world-designer` row that day); the `world-designer` role in `.claude/agents/`
staffs it from the next commission, with the standing constraints baked into
the role rather than restated per commission: authored breadth, canon governs, photoreal
late-analog Britain, D13 and D14, and this delivery convention. The do-not-touch
list in section 2 binds the in-house line exactly as it bound the outside one,
and still nothing validates it.

## 6. What is a convention, what is a consumer, what is a runner path

RECORDED CONVENTION ONLY, which means a person following it will be
consistent and nothing checks them:
- the branch naming in section 1
- the do-not-touch list in section 2
- the review location in section 4
- taste questions going to Telegram as cards

A WORKING CONSUMER, which means code runs and produces a reading:
- `tools/art-deliveries.py` lists `art/*` branches, finds
  `production/art/<commission>/DELIVERY.md` on each, compares against the
  integration tasks already filed, and files one per new delivery. It has a
  selftest with the accepting case first, and it prints its denominators: how
  many branches were walked, how many deliveries found, how many already
  filed. The daily wake calls it.

AN EXECUTABLE RUNNER PATH, which means a machine can be told to do it:
- `.github/workflows/ledger-art-blender-preview.yml` runs a NAMED Blender
  recipe headlessly, renders previews and commits them to the art branch. It
  is `workflow_dispatch` only, so it never fires on a push, and its
  concurrency group yields rather than queues so it cannot compete with a
  running game job. Lowest priority by construction, not by intention.

NOT BUILT, and named so nobody looks for it:
- nothing validates that an art branch left the section 2 list alone
- nothing checks a delivery's contents, only that the file exists
- THE FIRST RECIPE'S RENDER HAS NEVER EXECUTED. `quay-street-mickeys-walk`
  exists and resolves, so the workflow no longer refuses it, and its PLAN is a
  working consumer: the wrapper's selftest reads the plan on every run, 45 of
  45 cases, and the plan reports five camera stations one bay pitch apart at
  the file's own 1.6 m eye height with `baysInAnyFrame=6/6`. But Blender is
  NOT INSTALLED in the container where the recipe was written, measured three
  ways, so every `bpy` call in it ships unrun and the first execution is the
  first run on the Windows runner. A recipe that exists and a recipe that has
  RENDERED are different facts and this line is here to keep them apart.
