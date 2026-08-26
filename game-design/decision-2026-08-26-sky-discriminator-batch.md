# DIRECTOR RULING — sky-gain discriminator batch, fixture pins 5–7, shadowed assets, lint promotion (26 Aug 2026)

> **STATUS — LOG, 2026-08-26. NOT CURRENT after the sky-gain build lands or the shadow re-key ships — whichever is first re-opens its half.**

Reviewed against the tree, not the report: verify footer read from
`ledger/.verify-footer` (green, and it carries this batch's own numbers —
53/53 selftest fixtures, 40 footer-string fixtures, `prop reach ok, 228
model file(s) minting 213 key(s), 15 shadowed by 12 key collision(s)`);
`Vignette` grepped across `tools/` (zero hits — both ledger entries gone)
and across the repo (live callers in `FilmGrade`, `SimDirector`,
`SkyGain`); the five `skyGain*` emits found on `SimDirector`'s done line;
the prediction section of
`game-design/agent-reports/sky-gain-discriminator.md` read in full.

## A. COMMIT. One reviewed commit for the whole batch.

The evidence standard is met the only way it can be from this seat: the
footer's numbers are the batch's own claims printed by instruments, the
reach ledger moved in the right direction (two entries REMOVED, none
added, callers confirmed by grep this session), and the six break tests
are accepted on the builder's named reds plus byte-identical restores —
with the standing note that claim-auditor's next sweep spot-checks them,
because I did not watch them run. Nothing in the batch touches the
premise; SkyGain serves M17.10 and the fixture work serves the
instruments. Cadence: this record is the review the 03:10 ruling was not.

## B. DISPATCH — YES, the condition is ALREADY MET. The prediction is on disk.

The caveat in the brief ("prediction may not be on disk yet") is stale as
of this reading: `sky-gain-discriminator.md` §"The prediction, written
before the run" ships numeric bounds per outcome, which is exactly what
the last three builds proved a round trip needs. What it contains, and
what any future discriminator must contain, ruled as the template:

1. **An internal identity** (`skyGainRays` band counts = that run's own
   `valueRays`, summing to `of`) — the instrument-first check.
2. **An instrument-sanity band from LANDED arithmetic** (`gnd` `xgrade`
   3.3–4.3 from `groundGainBy`/`groundGainByRaw`) — read FIRST; outside
   it, read nothing else (rule 3).
3. **A numeric fork where the outcomes exclude each other** — `xrawsrc`
   0.10..0.40 at the low rungs; flat = scalar on the dome, climbing
   0.141→0.363→0.593 = double sRGB at the funnel. Same key, same line,
   cannot both be true.

**The builder's departure from my brief is RATIFIED and the brief's shape
is RETRACTED.** I wrote "sky-gain ≈ ground-gain ≈ wall-gain ⇒ common
path"; read against the code, geometry gains contain the whole irradiance
and the sky's contains none, so those three can never be equal and their
inequality proves nothing. The honest carrier of my intent is `xgrade`,
irradiance-free on every band by construction. Recorded here so my
sentence is not quoted forward — a wrong framing re-quoted is the
"noon sun due SOUTH" failure and this file is where it stops.

Dispatch batched with whatever Game-layer work is pending, one dispatch,
sha captured before dispatching, watch by ancestry.

## C. SHADOWED ASSETS — RE-KEY. Neither rename nor accept.

15 files no name can reach, a bus and an ambulance among them, under a
pass whose whole point is dressing a British port town from these kits —
a bus is not optional street furniture in the late-analog premise; the
pass needs these assets addressable. Options weighed:

- **Rename on disk**: touches fetched kit assets, breaks provenance and
  attribution, and a re-fetch silently reintroduces the collision. No.
- **Accept and record**: leaves last-path-wins deciding art. A silent
  resolution rule is the "allow-list discards what nobody thought of"
  shape aimed at assets. No.
- **Re-key in `AssetLibrary`**: our code, no asset mutated, re-fetch
  safe. **Yes.**

Requirements (design is the builder's): every model file on disk
reachable by some key; colliding stems disambiguated by path; every key
placed in the Game layer today resolves to the SAME file it resolves to
now (the street must not silently redress); the footer's shadow count is
the done condition — **15 → 0** — and stays printed afterwards as the
regression guard. Whether a given placement then prefers the `.fbx` over
the `.obj` twin is content-wrangler judgement per asset, not ruled here.

## D. THE LINT IS NOW REQUIRED. The condition I set fired, in writing.

`decision-2026-08-26-instrument-repair-batch.md` §D: "If the sweep finds
ANY hit beyond the four known, the check becomes a standing lint." It
found a fifth, and the repair surfaced a sixth and seventh — both written
LAST NIGHT by the batch fixing this exact class, which is the strongest
possible argument that discipline without a mechanism loses here. No new
decision is needed; this record confirms the trigger and sets scope:

- **Scope**: accepting-case assertions pinned to mutable project state —
  landed artifacts (`game-design/sim-shots/`), regenerated asset outputs,
  and repository aggregate state (file counts, key counts) in EITHER
  direction; the seventh instance was a LOWER bound and the lint must
  catch both signs.
- **Standard**: instruments.md's own — live repository post-sweep is the
  accepting fixture, a synthetic pin the rejecting one, BOTH watched
  before it gates (rule 5b). Runs inside `verify.py`.
- **The coverage floor is not the lint's problem.** 27 of 41 candidate
  selftests and 49 of 55 verify checks remain unread in full; that
  remainder is a NAMED tier-2 sweep item on the queue, because a lint
  catches the shape it can parse and a reader catches the rest. The lint
  existing may not be cited as that sweep having happened.

## NOT RULED ON

- **The sky verdict itself.** Nothing has run; every prediction is
  unlanded. No conclusion about dome vs path exists until the build
  lands, alarm 1 passes, and the identity balances. Anyone quoting this
  file as "the dome is the fault" is quoting a prediction as a reading.
- Disposition of `classify`'s never-fired `prefix` branch (exact=63
  stem=11 prefix=0 none=139) — a dead branch is deleted or reordered,
  builder's call, queued named.
- The exact re-key scheme (builder design against C's requirements).
- Per-asset `.obj`/`.fbx` choices (content-wrangler, at placement).
- The six break tests as watched events — accepted on evidence, subject
  to claim-auditor's standing sweep.
- Cadence-gate mechanics — ruled 25 Aug, unchanged here.

<!--RULING spawn=2026-08-26T04:03:52Z-->
