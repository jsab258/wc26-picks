# Decisions: the shadow-gap verdict, and keeping the template repo current

> **STATUS — LOG, 2026-08-24. NOT CURRENT** once superseded; a decision
> record is history the moment it is written, and reads as such.

Two director decisions, recorded in `templates/decision.md`'s shape. Written
here rather than `decisions-pending.md` because that file is the queue of
things only Jafar can answer, and both of these are decided.

---

## Decision 1: the shadow gap is PARTLY closed — regime confirmed, residual named, NO new lever

**Decided by:** studio-director (Fable), 2026-08-24, on the b88adbb landing.

**The question.** The dry-tour experiment landed. Is the benchmark's shadow
contrast gap (shadowRatio vs the references' 0.157..0.388) closed, partly
closed, or still open — and does downtown's 0.676 mean ref-bench needs an
outlier rule?

**The decision.** PARTLY CLOSED, in three parts, none of which is a new
lighting lever:

1. **The regime finding is CONFIRMED and the queue's item 1 closes.** The
   wet-vs-dry split was the gap's bulk: dry district median 0.201 is in band
   (wet was 0.137, below), 3 of 7 in band from 2 of 7, and every dry
   non-district noon was already in band. No lever moves on this evidence.
2. **The residual is hook 0.149 and strip 0.140 ONLY** — 5–11% below a floor
   that is the minimum of five reference frames — and it is HOUSED in the
   already-open ambient-fill ladder rung, not in a new item. Gullwing 0.118
   is excluded from the residual: its frame is a camera fault (see evidence),
   the same class as downtown's, in the other direction.
3. **Yes, ref-bench gets an outlier rule — as ANNOTATION, never exclusion,**
   generic to ratio-derived rows: a sim still whose ground-band input
   statistic (groundP90 / groundMean) sits below the five references' own
   floor for that statistic gets its shadowRatio row marked unreadable, with
   the qualifying number printed, and the summary counts print "in band X of
   Y readable (+Z unreadable, named)". Keyed to the references' own measured
   band, so no number is invented (rule 2).

**The evidence it rests on.** Verified this session, not quoted:
- `game-design/sim-shots/frames.tsv` at commit b88adbb: all seven
  `district_*` rows read rain=0.00 wet=0.00 (lines 17–23). The run was
  complete: `runs/b88adbb.txt` done-line reads frames=25075,
  gatesChecked=72 gatesFailed=0, pass=True.
- Dry shadowRatio by district (ref-bench on the landed stills): copper
  0.201, downtown 0.676, fairview 0.266, gullwing 0.118, hook 0.149,
  ironside 0.292, strip 0.140. Wet series for the same seven: 0.065–0.404,
  2 of 7 in band. Dry non-district noons 0.365 / 0.270 / 0.239, all in band.
- **The four stills, opened (rule 4), which changed the reading:**
  `district_gullwing.jpg` is a dark building mass at arm's length — window
  recess and sills fill the frame; its ground band is unlit facade, so
  0.118 is a reading of a wall, not of street shadow (meanLuma 0.154 at a
  dry noon, lumaThirds 0.071/0.082/0.063). `district_downtown.jpg` is one
  unlit surface with a sliver of skyline (meanLuma 0.096, brightPct 0.50) —
  the known near-black frame, reading falsely HIGH. `district_hook.jpg` and
  `district_strip.jpg` are genuine street frames: elevated vantage, bright
  near-shadowless pavement, deep darks from decals and building bases —
  their below-floor readings are real readings of real frames.
- The residual's lever already exists on independent evidence:
  `ambientSeries` in b88adbb reads shade|lit 0.051|0.404 at x1.0,
  0.094|0.431 at x1.5, 0.153|0.471 at x2.0 — ambient lifts the shade end
  roughly 3x faster than the lit end, which is exactly the shape the
  residual needs.
- `shadowPeakDay=3/0.90` in the same verdict: the shadowDrop series peaked
  on the wet day, consistent with the regime finding.

**What it rules out.**
- *Closing outright*: hides a real 2-of-6-readable shortfall on the two most
  street-like frames, and hides two broken tour cameras behind a closed item.
- *A new shadow lever now*: the auditor's candidate (ambient fill lifting
  groundP10) is correct as physics but already exists as the lighting
  ladder's next rung with its own landed series; opening a second item on
  the same variable is two numbers derived from one lever.
- *Excluding downtown silently from the benchmark*: a dropped frame reports
  a smaller world as a cleaner one (ref-bench's own docstring); annotation
  keeps the denominator visible.

**What would reopen it.**
- Ambient fill lands (value chosen from `ambientSeries`, not from this
  ratio) and hook/strip shadowRatio STILL sits below 0.157 at rain=0.00 —
  then the residual is a real deficit needing its own lever. The proving
  read is the PAIR: groundP10 rising while groundP90 moves little; the ratio
  alone cannot say which end moved.
- The re-sited gullwing/downtown cameras produce readable street frames
  whose ratios sit outside the band.

**Where it is enforced.** Queue item 1 (the dry-tour fork) is discharged and
moves out on the next queue tidy; three builder items go in: (a)
instrument-builder — the ref-bench low-content annotation, both-ways
selftest with downtown as the rejecting fixture and hook as the accepting
one; (b) engine-specialist — re-site the `district_gullwing` and
`district_downtown` tour cameras to frame a street, labelled as a pose
regime break for those two rows only; (c) when the ambient-fill rung is
taken, its landing reads hook/strip groundP10/groundP90 as the movement
proof. Until (a) lands, nothing quotes downtown's shadowRatio.

---

## Decision 2: template drift gets a same-repo fingerprint check with a sync marker, RED on mismatch

**Decided by:** studio-director (Fable), 2026-08-24. Jafar asked directly
for the mechanism after catching the drift himself.

**The question.** The template repo (`jsab258/game-studio`) drifted from
LEDGER's process sections within hours of shipping (resident=Fable vs the
hybrid), caught only because Jafar noticed. What mechanism prevents
recurrence?

**The decision.** Option (a), shaped SAME-REPO: a LEDGER verify check
(`template_sync`) fingerprints CLAUDE.md's process sections (THE STUDIO
SPLIT, THE HYBRID RESIDENT, REPORTING, AUTO MODE) and compares against a
tracked marker file (`.claude/template-sync.txt`) recording the fingerprint
plus the template-repo commit sha that last absorbed it. Mismatch is RED —
blocking the commit — and the discharge is one line: sync the template now
(and record its sha), or record "deferred" with a named queue item. The
check never reads the other repo; the marker is the claim, and the check's
job is to force the claim to be made consciously at the exact moment the
sections change, which is the trigger point the failure lacked.

**The evidence it rests on.** The drift happened within hours and was
caught by the owner, not by any instrument — that is the incident, and it
is the "rule with no trigger point decays" pattern this file names.
Decided without a measured change-frequency series, because the trigger
argument dominates regardless of frequency: a per-change check costs zero
between changes and fires exactly when the risk exists. The cross-repo
awkwardness is real and measured by inspection: the template checkout
exists only in this container, not on the Windows CI runner, so any check
that READS it would be environment-dependent — which is why the marker
shape was chosen over a live diff.

**What it rules out.**
- *(a) as a live cross-repo diff*: environment-dependent; verify must mean
  the same thing everywhere it runs.
- *(b) a dailies standing review*: pays its cost every day whether anything
  changed, catches an hours-scale drift up to a day late, and standing
  items decay — this project's file of record is a list of proofs.
- *(c) a standing queue item*: list-based, no trigger; a stale queue item
  looks like a plan.
- *(d) sync on demand*: the incident. Rejected by the incident.

**What would reopen it.** The marker being bumped without real syncs — if
any future audit finds the template stale behind a green marker, the marker
has decayed into a comment, and the escalation is a periodic cross-repo
content diff run where the checkout exists (this container), added to the
dailies. Also: if the RED proves to block game work more than about once a
week, the discharge path is too heavy and the deferred-with-queue-item arm
gets made cheaper — not the check made quieter.

**Where it is enforced.** The check itself, once built: instrument-builder
item — `template_sync` in `ledger/verify.py`, both-ways selftest per rule
5b (accepting: sections unchanged against a matching marker, AND a changed
section with a freshly updated marker; rejecting: a changed section with a
stale marker, and a missing marker file, which must read as "nothing
recorded", not as clean). Until it lands, the enforcement is this record
plus the hybrid's mandatory trigger: any CLAUDE.md change already spawns
the director, and the director asks the sync question — this file is where
that question is written down.
