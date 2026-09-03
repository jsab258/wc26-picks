# DIRECTOR RULING: the preparation sequence that unlocks unattended local production (1 Sep 2026)

> **STATUS: LOG, 2026-09-01. NOT CURRENT once the vignette bill of
> materials lands and the CC0 fetch route has one proven end-to-end run;
> from then the BOM file and `production/week-plan.md` are the reading
> copies and this file is their history.**

Prompted by Jafar: prepare as much as possible, with probes and experiments
to ensure things work and quality is good, so that large batches of local
generation can run unattended. The constraint is the budget in
`production/budget.md`, which outranks the work. The question ruled on:
what is the cheapest sequence of Claude-expensive preparation that unlocks
the largest amount of zero-cost local production, without inverting the
plan's order or skipping a gate.

## What was verified this session, before ruling

- `ledger-v2/respec/roadmap-v2.md`: phases R and 0 to 6, instrumented
  exits as briefed. Large asset production sits in phases 2 and 3.
- `production/budget.md`: last row 34 percent total at 28 hours, working
  figure 6 points a day, three stop conditions. Jafar's newer reading
  (38 spent) is NOT yet a row; the resident adds it, because a series
  missing today's reading is the file failing its own rule.
- `production/week-plan.md`: order approved earlier today, corrections
  applied. "Spend Claude on deciding, spend the PC on producing" is the
  structural idea and this ruling is that idea sequenced.
- `production/queue/012-trellis-blocked-replan-asset-sourcing.md`: TRELLIS
  cannot run on the AMD RX 6700, CUDA and VRAM are independent blockers,
  no purchase is authorised. Confirmed by reading, not summary.
- `tools/meshgen/specs/props-local-01.json`: 37 items, all
  `"kind": "file"` from `ledger/Assets/Props/base-mesh/` — existing repo
  assets being measured, pivoted and LOD'd. It is a processing batch, not
  an acquisition list. Confirmed by reading the source blocks.
- No bill of materials exists. Targeted greps over `production/` and
  `ledger-v2/` for the phrase and its synonyms: zero hits.
- `game-design/decision-D1b-rescope.md`: the vignette definition and the
  admissibility rule (every object via generator from shared JSON,
  allowlist only). This is the one concrete asset target in the tree.
- `ledger-v2/studio-v2/verification.md`: judge ships only on both halves,
  a 30-to-50 item sample graded by Jafar at 80 percent held-out agreement
  AND a refusal fixture proving the judge rejects.
- **`production/throughput.md` line 8, and this corrects the brief's
  framing: the dialogue-bank pilot line HAS run.** Pub-regular-v1, 48
  lines, mechanical gates clean (canon, rung, repetition worst 0.18,
  license tagged), tone PENDING the D7 judge, "whose calibration sample
  this bank is". The Phase 0 pilot is not skipped, and roughly a bank's
  worth of the calibration sample already exists as a byproduct.

## Ruling 1: the resident's read, tested

**Correct on the central claim.** The phase structure is sound, nothing is
missing at the phase level, and the missing layer under the current phase
is the bill of materials. Every downstream activity — fetch batches,
generation batches, the vignette scene itself — needs a named target list,
and none exists. The 37-item spec looks like one and is not.

**Three corrections, each of which changes the sequence:**

1. **The AMD image-to-3D probe is demoted, not promoted.** The resident
   lists it first among the four gaps. It is the lowest
   capacity-per-token item on the board: the machine probe already
   answered the only named tool, "any image-to-3D on AMD" is open-ended
   research with weak expected value, and the BOM will most likely show
   the D8 vignette (street furniture, brick, asphalt, practical lights)
   is covered by CC0 libraries with no generation step at all. It becomes
   a CONTINGENT task: it exists only if the landed BOM contains lines
   with no library route, and it starts as a survey, not as installs.
2. **Judge calibration is not a precondition for the first batch.** The
   first batches are CC0 fetch-clean-tag, gated by mechanical instruments
   the pipeline already has (dims, triangle counts, pivot, licence tag).
   A taste judge adds nothing to those. The judge gates the STILLS and
   the dialogue tone, and its sample is assembled from what the batches
   produce anyway. See Ruling 4.
3. **The engine decision is not preparation for local production.** CC0
   GLB libraries are engine-neutral by construction (queue 012, D1b both
   say so), so production does not wait on D1 and D1 does not wait on
   production. They share the vignette BOM, which is why the BOM is first
   for both.

**One thing named so it is not silently lost:** the dialogue pilot's tone
gate is PENDING the judge. Phase 0's exit needs a VERIFIED piece, so until
the judge exists the pilot is a piece produced, not a piece verified. The
judge is therefore on Phase 0's critical path regardless of asset work,
which is one more reason Ruling 4 folds it into work already scheduled.

## Ruling 2: the sequence

Ordered by unlocked-capacity-per-Claude-token. Costs are stated in
sessions against the 6-points-a-day working figure because no tool prints
per-task token costs here; where I cannot estimate, I say so.

1. **Dispatch `props-local-01` on the machine tonight.** Cost: near zero,
   the pipeline is built and director-reviewed today. Unlocks: a 37-prop
   measured, pivoted, LOD'd, engine-neutral library, and the first proof
   of the local Blender backend on real data. Skipped: the night is
   empty and every later batch runs on an unproven backend.
2. **Write the vignette bill of materials.** Cost: one content-wrangler
   session plus one short director-free review pass; call it half a day's
   budget. Unlocks: every overnight batch after it has a named target,
   and the AMD question gets scoped for free (the lines with no library
   route ARE the case for generation, purchases, or neither). Skipped:
   unattended capacity exists with nothing named to produce, which is how
   nights get spent reprocessing what we already have.
3. **Prove the CC0 fetch-clean-tag route end to end on about five BOM
   lines.** Cost: one builder session to write the fetch spec and probe,
   one overnight run, one short read-back; the downloads run on Jafar's
   machine, where the hosts are not blocked. Unlocks: the entire CC0
   acquisition class as overnight work — hundreds of allowlisted assets
   at zero Claude cost. This is the single largest conversion of
   expensive work into free work available this week. Skipped: bulk
   fetching on an unproven route is rule 5 waiting to happen, and licence
   tagging stays unverified, which the allowlist law does not permit.
4. **First full BOM batch overnight, mechanical gates only.** Cost: near
   zero Claude (generate the spec from the BOM, dispatch, read results
   next session). Unlocks: the vignette's asset shelf filled. Skipped:
   step 3's proof never compounds.
5. **Judge calibration, folded into one Jafar sitting.** Cost: one
   instrument-builder session for the grading harness and held-out split;
   minutes of Jafar, once, per Ruling 4. Unlocks: "quality is good" gets
   an instrument, the dialogue pilot's PENDING tone gate can close, and
   Phase 0's exit becomes reachable. Skipped: every taste claim stays a
   mood, and D1b's blind look falls back to Jafar-only reading.
6. **The engine comparison proceeds per the week plan, unchanged.**
   Items 3 to 5 of `production/week-plan.md`, timebox ends 2026-09-14,
   no extension. The BOM and the fetched assets feed the vignette scene
   directly, so steps 2 to 4 sit ON D1's critical path, not beside it.

The week-plan order (governance gate first, then local asset generation,
then the comparison) is unchanged by this ruling; steps 1 to 4 here ARE
week-plan item 2, decomposed.

## Ruling 3: the bill of materials, scope and shape

**It comes first among the Claude-priced items (step 2), and its scope is
the D1b vignette plus the street-furniture families the vignette pulls
in. Not the town.** The engine is undecided and phases 2 and 3 are not
current; a town-wide BOM now would be enumeration for its own sake,
against a scope that D1's outcome may reshape.

Worth writing means one line per item carrying: name; count and variants;
route, exactly one of HAVE (repo path), FETCH (candidate CC0 source
named), GENERATE (no library route found, the honest gap), or BLOCKED
(needs a Jafar decision, for example a purchase); licence; dims policy
(measured at ingest, never invented, per the props-local-01 lesson);
priority (vignette-mandatory versus street-filler); and which mechanical
gate accepts it. The GENERATE and BLOCKED lines are the deliverable's
point: they are the measured answer to whether image-to-3D on AMD matters
and whether any purchase question goes to Jafar.

Busywork looks like: whole-town coverage, per-item prose, invented target
dimensions, or any line with no consumer in the vignette scene. A BOM
line nothing consumes is a wish, not a requirement.

## Ruling 4: judge calibration DURING, never before, and never as homework

The first real batch (CC0 props) does not wait for the judge: its quality
claims are mechanical and already instrumented. Calibration runs
alongside, and the constraint that Jafar is not to be examined is
binding. Concretely:

- The sample is assembled from artifacts the work produces anyway: the 48
  pub-regular lines (already written, already named as the sample) plus
  the first vignette stills and fetched-prop renders as they land, to
  reach the 30-to-50 D7 requires.
- Jafar grades ONCE, in one sitting, scheduled in the same interruption
  as the D1b blind look he already owes. Pass or fail per item, an
  optional word where he feels like it, no rubric, no second round
  designed. Estimated at 15 to 20 minutes; if it runs past that, the
  sample was too big and the harness is at fault, not him.
- The refusal fixtures (verification.md's three bands) are built by a
  tier-3 agent, not graded by Jafar; his sample supplies agreement, the
  fixtures supply refusal, per the spec's own split.
- If the sitting has not happened when the D1 pairs land, D1b's recorded
  fallback stands: his blind preference is the reading, and whether it
  suffices for "decisively better" is flagged to him at close.

## Ruling 5: what is NOT done yet, by name

1. **No AMD image-to-3D rescue.** No ZLUDA, no DirectML ports, no
   CPU-inference experiments, no cloud-GPU research. Contingent on the
   BOM showing GENERATE lines; then a survey session first, and any
   spend-money option goes to Jafar as a named ask, never as work begun.
2. **No purchases and no purchase-shaped research.** Meshy, Tripo, cloud
   GPUs, an NVIDIA card: all Jafar's decisions, raised only if the BOM
   proves a gap that CC0 cannot fill.
3. **No town-wide BOM** (Ruling 3).
4. **No bulk CC0 downloading before step 3's five-item proof lands**,
   including its licence tags being read back from the manifest, not
   assumed from the site.
5. **No judge tuning loops before the graded sample exists**, and no
   second grading round designed under any name.
6. **Nothing visual beyond the comparison scene**, re-affirmed from the
   week plan; the engine is undecided and a rung built now may be built
   against a renderer that does not ship.
7. **No new Fable spawns for the sub-steps above.** Steps 1 to 4 land as
   builder batches under the existing cadence; the next mandatory spawn
   folds their review. One decision, one spawn.

## Corrections directed (resident applies; no new director spawn needed)

- Add Jafar's 38 percent reading to `production/budget.md` as a dated
  row.
- Re-point `production/queue/012` acceptance at this sequence: its "local
  batch route" acceptance is satisfied by steps 3 and 4, and its probe
  staleness fix rides the same builder batch.

Spawn row, quoted verbatim from `.claude/agent-log.tsv`:

    2026-09-01T17:05:18Z	studio-director

<!--RULING spawn=2026-09-01T17:05:18Z-->
