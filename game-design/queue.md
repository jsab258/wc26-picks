# The work stack

> **STATUS: LIVE**, verified 2026-08-21. What gets picked up next, in order.
> The plan is `roadmap.md` and it wins; this is the next few hours of it.

## Why this file exists, and how to use it

The next items are written down BEFORE a dispatch and taken from the top
afterwards, so no judgement is required at the exact point where judgement was
failing. Full account in CLAUDE.md under AUTO MODE.

- **Every item fits inside one build round trip (~28 min)**, or it gets split.
- **CI-needed items are marked** and batched into the next dispatch.
- **Take from the top; move finished items out.** `roadmap-history.md` holds
  the cut blocks and `docs-check` caps this file at 400 lines, which is what
  forces the tidy.
- **`## Standing work` never empties.** Running out of short items is a refill
  signal, not a stop signal.

---

## Now

### SUPERSEDED 2026-08-31 — the v2 respec landed; read this before the block below

The block below was written 26 Aug for a Monday that arrived differently:
Jafar delivered the LEDGER v2 respec package (`ledger-v2/`, entry point
`handoff/HANDOFF.md`), which supersedes the old roadmap and this queue's
priorities. **The current work is the handoff's Phase 0**, and the queue
mechanism itself is being replaced by `production/queue/` per
`ledger-v2/studio-v2/runner.md`. Items below stay valid as raw material and
several (the sky fix, the picture wiring) will reappear as Phase 2 work; do
not START from them.

### START HERE — the 26 Aug parked-state block (superseded, kept for its facts)

**26 Aug: usage hold to Monday afternoon.** 85% of the weekly limit went in
under two days, so the loop was stopped deliberately. Nothing is broken and
nothing is mid-flight: tree clean, everything pushed, no watcher armed, no
build running. **The watchdog is DISABLED** — re-enable it (CLAUDE.md, AUTO
MODE, *Starting it*, step 1) as the FIRST action, or the chain has no restart
mechanism and one bad turn parks the project silently again.

**The three items it ordered** (wire one picture; build the tiling check;
write the prompt entries — 28 of ~52 were written 26 Aug) **stay valid as
Phase 2 raw material.** The what-not-to-do lesson stands under v2 as the
routing law: of 110 agent spawns on 25 Aug, 78 were the project working on
itself; `gameShareDay` rides in every verify footer because of it.

**THE ONE DECISION WAITING FOR A DIRECTOR** is the sky fix (item 1). It is a
mandatory trigger — a landing that changes a conclusion — and the finding is
already measured and written down, so the spawn is a RULING, not an
investigation. Fold any other pending questions into that same spawn: one
decision, one spawn.

### Where the street got to

Clips: 64 filled (`walk_start` deliberately empty), 0 wrong. The street talks,
argues, leans, works counters. **The front is M17.10: the visual bar is GTA
V.** Playtest retargeted to Jafar's Windows machine after the visual stage,
with live speech; `playtest-plan.md` has the runbook. The self-hosted runner
`ledger-pc` builds on his machine, ~17.6 min a round against 33-41 in the
cloud, all 72 gates green.

**Three standing warnings that cost a day each and are easy to re-derive
wrongly.** `meanFrame` has a ~1ms NOISE FLOOR, so single-run diffs under 1ms
mean nothing. Shadows (5.1ms) and per-pixel lights (4.4ms) hold the frame —
the crowd does NOT; draw calls, vertex budget and shadow reach are all dead
ends, measured. And the crowd guard on how far a line runs on road is
CORRECT: the frame showing 1-2 people is the guard working, so do not chase
density by loosening it — the lever is where ROUTES go.

Full accounts of all of it in `roadmap-history.md`.

### Startable right now — JAFAR'S SEQUENCE (22 Aug, his words):
### "1. visual, 2. voices/speech, 3. playtest, then feedback/fixes and
### then continue w roadmap." Within a stage, order by what shows on
### screen. Nothing from a later stage starts while an earlier one has
### startable work, except reading a landed verdict, which is free.

1. **THE WATCHDOG STILL TESTS ATTENDANCE, NOT A REVIEW.** *(the CLAUDE.md
   half of this item is DISCHARGED — the "neither built" sentence is gone and
   the paragraph now describes the live gate, the two residual holes and this
   twin.)* The watchdog's DAILIES CHECK reads *"if no `studio-director` row in
   the last 12 hours, spawn"* — a ROW, which is attendance. A director killed
   mid-ruling satisfies it exactly as a completed review does: the fault
   closed in the commit gate on 25 Aug, still live one layer out.
   `verify.py` already has the machinery to ask the better question (a stamped
   ruling newer than the reference), and the director ruled it must CALL that
   parse rather than grow a second copy — one idea, one implementation.
   Not startable without a director spawn (it changes the cadence mechanism);
   fold it into the next mandatory one.

1. **THE SASHAY IS SCREENED; ONE RE-PICK ON HIS PC CLEARS IT.** *(visual)*
   `walk_start` holds "Catwalk Walk Start Turn 180 Left", so every man in
   Meridian begins walking with a runway turn. Depth 3 is deleted from
   `walk_start` and `walk_stop` (measured: its whole candidate set in both is
   Catwalk runway clips) and `turn_ok` refuses any clip whose NAME says it
   turns — same axis as `direction_ok` refusing one that goes backwards. **The
   clip is still on disk until a re-pick renames it**, which is his one
   double-click; the slot then comes back EMPTY and falls back to the
   locomotion tree, which is the right answer.
   **AND THE COMMENT THAT NAMED THE FAULT WAS WRONG, WHICH IS THE FINDING.**
   It said depth 2 and "all 8 candidates are Catwalk variants"; depth 2 has
   three candidates and none is a Catwalk. Acting on it would have deleted the
   depth that never had the fault. Full account in `clip-findings.txt`,
   including the costume screen written first and WITHDRAWN — it refused the
   game's default idle, and a name cannot tell a monster's motion from a file
   exported off a monster rig.

1. **THE SKY FORK IS SETTLED: THE DOME RENDERS AS `source^2.05` AT THE
   HORIZON — PLUMBING, NOT ART.** *(visual, and it was the barred lever)*
   `SkyGain` ran for the first time on `0d42f51`, sim green, and exactly ONE
   of its four written predictions fires. Read against the prediction, not
   after it:
   - raw `xsrc` on sky is **0.276**, not ~1.000 -> the dome does NOT render
     what it was authored. Prediction (b) is out.
   - it is **not constant** across elevation — 0.149 at the horizon to 0.480
     at 20..45deg — so it is not a scalar sitting on the dome. Out.
   - it **CLIMBS with elevation**, which is prediction 3 verbatim: *a power
     law, not a scalar ... SUSPECT THE PLUMBING, NOT THE ART.* **IN.**
   - `xgrade` on sky is **4.236, the HIGHEST of the four bands** (gnd 3.707,
     shd 3.214, lit 2.523), so the common path is not sky-hostile. Out.
   **Fitted, the exponent at the horizon is 2.053 and 2.056** over the two
   lowest bands — inside the **2.05..2.09** window `SkyGain`'s own comment
   named IN ADVANCE as the gamma/linear mismatch signature. The horizon is
   where every camera in the game looks. Higher bands drift to 1.54, which is
   a second term (cloud/cover/curve) mixing in and is not the subject.
   **AND THE GRADE IS EXONERATED BY THE RAW ARM.** Dry noon raw ordering is
   `lit 0.198 > gnd 0.134 > sky 0.053 > shd 0.043`; graded is
   `lit 0.499 > gnd 0.495 > sky 0.223 > shd 0.138`. **Identical ordering** —
   the frame arrives inverted and the grade preserves it. The vignette
   alternative is ruled out by its own printed number (`vig` 0.873 on sky, a
   13% reduction against an 85% shortfall), which is exactly why it was
   printed.
   **NOT ACTED ON, DELIBERATELY.** Reading a landed verdict is free; deciding
   what to change is a director trigger and this landing changes a
   conclusion. The ruling waits for the next spawn. What it must rule on: the
   funnel between `SceneLighting.C()` and the dome shader applies one gamma
   too many, and the fix is at the funnel — `LightModel.SkyColour` is NOT the
   address. Note the family: this is the same class fault as the MPB tints
   two items below, on the largest surface in every frame.

1. **WIRE ONE GENERATED PICTURE INTO THE STREET BEFORE GENERATING ANY MORE.**
   *(visual, and it gates the whole picture batch)* **Nothing in the game names
   `Decals/generated`** — zero references across all 186 Game files. Fourteen
   pictures are in the repository and no code loads one, so a four-hour batch
   would change nothing on screen. `fascia_mickeys.png` is the candidate: shop
   fascias today are `StreetFurniture` building a plaster box at 2.6x0.34x0.06
   and lettering it with `WorldBuilder.Letter`, so the geometry, placement and
   yaw already exist and are correct — the picture replaces the material and
   drops the `Letter` call. **First real question: the board is 7.6:1 and the
   picture is 2:1.** Done means SEEN in a committed frame, not "wired".
   Full spec: `imagegen-batch-2.md`.

1. **NOTHING ANSWERS "DOES THIS TILE" — AND THE MOST VISIBLE POSSIBLE FAULT
   SAILED THROUGH.** *(visual)* `wall_salt_render.png` has a WHITE BORDER
   around the whole image; tiled, it draws a white grid across every building
   in the district. The blank check reads it at spread 242/255 and calls it
   healthy, CORRECTLY — it asks "is this picture blank" and a border is a
   small fraction of the pixels. Compare the first N rows against the last N
   (and columns), print the edge difference per item, refuse an item whose
   opposite edges do not meet. Both fixtures are free and already on disk:
   `fascia_mickeys` accepts (and should be exempt BY KIND, not by luck),
   `wall_salt_render` rejects.

1. **THE WALL EXPERIMENT — ONE IMAGE, AND IT DECIDES A WHOLE KIND.**
   *(visual)* Both wall items failed and the negative channel meant to prevent
   one of them **has never been tested against a frame that had the fault** —
   I concluded off two 512 probes that neither reproduced it. The untried run
   is the picture that FAILED: seed 8036 at 1024 with cfg 2.0, so the negative
   is live. About two minutes on his card. Until it comes back clean AND
   tiles, walls do not ride the long batch.

1. **`namedJunctions=1` OF 97 — 49 OF 51 STREET NAMES ARE UNREACHABLE, AND
   THE GUARD FOR THIS EXACT FAULT REPORTS ZERO.** *(moat: information)*
   `StreetMap.NameOf` compares SCALED node coordinates against the UNSCALED
   district avenue tables, so only the founding cross at (0,0) ever matches.
   **This is the SIXTH consumer to read those tables raw** — and
   `tools/lint-avenues.py:54` EXEMPTS `StreetMap.cs` as "the owner of the
   transform", so it prints `0 raw avenue reads` over a denominator that
   excludes the one file the fault lives in. A zero whose denominator omits
   its subject; rule 3b wearing an exemption's clothes. **IT IS THREE SITES, NOT ONE, measured by the
   rebuilt lint: `NameOf` x3, `AddressOf` x4 — the nearest-street FALLBACK,
   which is the path taken for 96 of 97 junctions — and `DistancePenalty` x2,
   the tie-break that stops a Hook position being named a Copper Row street.
   Fixing `NameOf` alone leaves the fallback and the tie-break wrong.** Queue
   item `streetmap-nameof-scaled-vs-raw`; Core, needs a ruling (changes
   `AddressOf` strings feeding gossip, breaks three CoreTests). **And the
   OWNER exemption was one of THREE holes, not the bug:** `NameOf` reads
   through an alias (`var cross = d.AvenuesZ; cross[0]`), which the old
   pattern matched ZERO times — asserted in the selftest so nobody re-derives
   "the exemption was it". It also CORRECTS the premise ruling C was given: plates have
   been placed all along (`signs=59 wallPlates=2`) at the one junction that
   can name itself, so "named streets and no way to read a name" was wrong —
   the hole is the LOOKUP, not the signage. `sign_plate_name` now files
   `junction_unnamed:192` every run, so it is legible in the channel
   everyone already reads rather than needing a fresh investigation.

1. **STAGE 2 (SPEECH) — JAFAR'S PRIORITY 2, NOT STARTED, AND THE RUNTIME WAS
   NEVER THE PROBLEM.** The channel answered on its first run: DirectML lands,
   three runtime files, `LEDGER_ONNX` defined — `RUNTIME_OK`. So
   `speechLive=0` with `speechNoModel=29` across 301 builds is **the voice
   MODEL missing from the build**, not a broken runtime. **The stage opens
   with the model:** find what `OnnxSpeech` loads and whether anything stages
   it into the Windows build the way `voices-into-build` stages the banked
   clips. **Do not spend a round trip re-testing the fetch** — it is green and
   named. *(Cut by the resident in a trim for space on 25 Aug and restored
   the same minute: it is a LIVE priority-2 item, not a closed block. Look
   before you destroy — the rule applies to a queue as much as to a file.)*

1. **PLAYBOOK SYNC DEFERRED: `playbook-sync-hybrid-resident`.** CLAUDE.md's
   THE-HYBRID-RESIDENT section was rewritten 25 Aug; `jsab258/game-studio` has
   not absorbed it and is outside this session's push scope. `template-sync`
   is DEFERRED, not stamped synced — different facts, must not print alike.

1. **`valueRungs` POOLS TWO CAMERA FAMILIES WHOSE `sky` MEDIANS DO NOT
   OVERLAP — a measurement-validity finding, flagged and deliberately not
   acted on.** On `c5a75c9`, one run, one weather tag: district rows read
   `sky` 0.371-0.425, reference rows 0.596-0.698 — **disjoint, with a 0.171
   gap.** So `sky`'s median is a function of the camera FAMILY, which means
   `sky>lit` is asking a different question of an aerial row than of a street
   row, while `valueRungs` sums both into one numerator. **Height and
   occlusion are confounded and the builder explicitly did NOT claim pitch
   causes it** — that restraint is right and the next reader should keep it.
   **RULED 26 Aug: SPLIT BY FAMILY — two keys, one per family, each with its
   own denominator, and the pooled key RETIRES.** Caveat-and-keep was refused
   in as many words: *caveats decay, emits don't.* **But NOT in the same
   commit as the re-aim**, because that landing's Identity B predicts the
   POOLED denominator at exactly 63, and changing the instrument alongside
   the subject confounds the identity built to validate it. **Do it in the
   next instrument batch. **UNBLOCKED 26 Aug — the identity has been read at
   `c03ead2`, so the split may proceed.** Until it lands the standing caveat
   holds: do not quote a pooled `valueRungs` as a street reading. The CAUSE is explicitly not ruled — height, occlusion and pitch
   are confounded, and separating them is a measurement to design, not a
   guess to make.

1. **`sky>lit` FAILS ON 15 OF 15 DRY CAMERA ROWS — CAUSE FOUND, see the sky
   item at the top.** The ordering item stays open because the FIX is not made;
   what is closed is the search. Full prior account in `roadmap-history.md`.


1. **TWO LINTS STILL CANNOT TELL A FULL SWEEP FROM AN EMPTY ONE.** *(the
   `lint-static` half of this item is DISCHARGED — it now prints `29 walked`
   with a named drop clause and the arithmetic `29 + 535 = 564 offered`, and
   CLAUDE.md's exemplar paragraph is corrected. The sun item is CLOSED and
   moved to `roadmap-history.md`.)* What remains, measured rather than
   assumed: `lint-nested` exits 0 **byte-identically for a full 88-file sweep
   and for a sweep of nothing** — its denominator is the REFERENCE set it
   compares against, while the Game file count that would actually move is
   computed and thrown away. `lint-shadow` re-globs at print time, so one line
   carries two moments. Same one-line repair both times: print the set walked,
   and name what was dropped. `lint-conditional-reach` is the model.

1. **VERIFY'S RED PATH IS A `head -3` — it reports ONE finding of nine,**
   truncated at 90 chars, with no count and no `(+8 more)`. The cap that
   announces itself is a standing rule and the verify footer is the one place
   it is not obeyed, which is where it costs most: a red run's single line
   reads as the whole problem. Owner: whoever holds `verify.py`.


1. **THE DRESSING LANDED: 736/739 placed, ZERO missed, all gates green, cost
   inside the ~1ms noise floor** (`71316fa`; 6/6 lamp forms, `city-kit-suburban`
   is no longer an unreached kit, and the Game layer names 73 models against
   62). Survey and signage verdicts in `agent-reports/kit-survey.md`. Open,
   and both about REPETITION — the tell
   the GTA bar exists to kill: `yard_fence` is 163 of 166 on the SHORTEST
   panel (`1x2`/`1x3` placed zero) — read the yard-depth series before
   touching the probe, the census says the gap is a CONSTANT 3.00m whenever
   the row-depth cap binds; and one street corner cannot see 736 objects,
   which is the argument for the eye-level cameras, not evidence of absence.

1. **DIRECTOR RULED THE DRESSING BATCH, 25 Aug — full text in
   `decision-dressing-batch.md`.** Live parts only: **the welded diamond
   REJECTS** (a US diamond on a post is the loudest wrong-country tell there
   is); the rolled plate is honest **iff** no US livery survives the 45° roll,
   confirmed off the first still and not off the apex-midpoint number.
   **Signage queues HIGH** — named streets whose names cannot be read is the
   information moat with a hole in it — and the duplicated TextMesh idiom is
   signage's FIRST task, because building signage otherwise mints a third
   private copy. On the ladder by name: the pub-sign board (the kit ships a
   mast arm with no plate) and a British terrace, whose next rung is blank and
   is therefore a RESEARCH task, not a fetch.
   **E: DISCHARGED 26 Aug** — both one-click items ran on his PC in one
   interruption; the re-pick's result and the probes' are in `clip-findings.txt`
   and `imagegen/prompts.json`.

1. **M17.10 — THE VISUAL BAR IS GTA V (PS3). Jafar's order, 21 Aug, twice.**
   *(the most on-screen thing there is)* Plan in `roadmap.md` 17.10,
   decomposition and research in `visual-bar-spec.md`. The look is carried by
   surface history, density, depth, light, atmosphere — in that order; his
   overcast reference frame proves dirt+depth+density carry a frame with no
   interesting light.

   **LANDED (accounts in `roadmap-history.md`):** V0+V1 whole; build D's kit
   furniture, yellows, chimney pots, aerials, reactions; **V1.5 LINEAR
   CLOSED**. Open from those passes: the sky dome (V6).

   **FOUR SKY HDRIs ARE FETCHED AND WIRED TO NOTHING** (24 Aug).
   `ledger/Assets/Sky/polyhaven/` holds 23MB of 2k captures, banked and
   attributed, and `grep` finds ZERO Game-layer references. Built and not
   running, on the one element in every outdoor frame.

   **DECIDED 24 Aug, ON EVIDENCE: THE REFLECTION/ENVIRONMENT SOURCE ONLY,
   VISIBLE DOME UNTOUCHED.** The numbers make the pick, not a preference.
   Glass 0.90 / Window 0.85 across town reflects a **64px cubemap off a
   three-colour gradient** — the largest reflective area in the game sitting
   on an empty environment, which is why every landed frame has near-black
   windows. Reflection-only is additive and cannot regress the continuous
   day. **Two real obstacles:** the captures must move under
   `Assets/Resources` (`Resources.Load` cannot reach `Assets/Sky`, `LoadImage`
   will not read `.hdr`), which moves the directory `attribution-check.py`
   maps to Poly Haven; and there is no NIGHT capture, so night keeps the
   procedural cubemap and the handover needs a ramp. **Ship the measurement:**
   the environment cubemap's own luma spread before and after — a flat
   gradient and a real sky differ by an order of magnitude there. Full
   reasoning in `roadmap-history.md`.

   **LINEAR MPB CLASS-FAULT UNDER TEST:** MPB colours skip gamma-to-linear,
   so display-authored tints weakened at the flip. Body wash fixed; 13 other
   MPB sites wait on the verdict. Real remainder: feet and shoes at 224-234,
   both tiers. **Second MPB fault open beside it:** `_Color` set through a
   property block on a shader with no `_Color` is a silent no-op — see the
   kit-paint items below.

   **V6 FIRST SLICE LANDED** (dusk warmth, sun glow, sodium deck). Open
   from V6: the dome's cloud structure per time of day.
1. **THE `e8c5949` STALL — CLOSED, account in `roadmap-history.md`.** Live
   remainder only: 3 of 352 kept runs have no done line, so the class recurs
   and the instrumentation is the deliverable, not a fix.

1. **THE INQUIRY RUNS NOW; TWO THINGS GATED ON IT STILL DO NOT.** *(moat:
   information)* `inquiry=Manhunt` lands, but `summonsTaken=0` and
   `redirectRelief=0.00` sit at zero — the latter in **248 of 326** runs on
   tonight's `--constant` sweep, which now sees sentinel words and bracketed
   rows (79 never-moved keys of 1347 harvested, 177 rows swept). The phone-line
   cause stands; the inquiry cause does not, and the two were read as one.

1. **THREE READINGS WHOSE SAMPLE IS TOO SMALL TO SEPARATE ANYTHING.**
   `patrolOnBeatMean=0.00` over 3 shots against `0.18` over 17 — zero of three
   separates nothing. The body budget closed at 87.8% (account in
   `roadmap-history.md`) but left two the same way: the centre-third foot
   reading, and white pills with no committed still.

1. **Smuggling** (M21) — **BUILT** (account in `roadmap-history.md`).
   Remainders: a player verb to recruit the signer, and gambling behind it.
   Read `cargoes`/`manifests` next build.
2. **The other day-job tracks** (M18) — `Core/DayJob` is the courier round,
   singular; the doc offers bar/courier/office on the first morning.
3. **Interiors beyond the pub** (M20) — every other door is a threshold.

**Reactions are LIVE and measured** (flinch/glance/wave/point/head_no
all firing; most refusals are glance cooldowns doing their job).
**greet reads 0of0 and that is the SIM'S ECONOMY, not a wire fault**:
it needs a loyal (≥0.35) need-route crew member passing the player and
the sim skims, so the condition never exists. Deliberately NOT
planted — a staged loyal runner would pollute the crew-decay gates.
The wire is proven by the five kinds sharing its path.

### The quality ladder (standing order 16 Aug: best available, not first working)

Before closing any visible item, ask: best available result, or first working
one? Take the next rung or name it here. A blank next rung is a research task.

| aspect | rung now | known next rung, free |
|---|---|---|
| textures | 2K colour+normal; roughness on walls AND ground (24 Aug, normalised so the wet calibration held: reflMax 0.89 unchanged); vertical run-off streaks in brick/plaster/concrete | AO maps; a second albedo variant per surface |
| buildings | procedural terraces, photo surfaces, pots+aerials, shopfront depth (V4), painted joinery, window SILLS (24 Aug, 2133) | window REVEALS (a recess needs an opening in the mass, not a proud box); door furniture |
| doors | 376 leaves on hinges, damped-spring swing, latch + creak, DOORWAY approach not a radius; proven live (`doorSwing=376/6/6/0/1`) | a shove — `HitStop` is unreachable at the shipped damping (8.4% overshoot vs a 15% stop, two CoreTests), so the thump needs a door pushed rather than eased; then walkers using doors |
| kit props | repaint applies everywhere (`kitPaint=1997/0`) | grey each kit colormap once at load, preserving luma — a multiply cannot desaturate (0.820 -> 0.788 measured) |
| vehicles | Kenney kit + town paints | curated higher-fidelity CC0 set (Quaternius/Sketchfab), same pipeline |
| props | Kenney + Base Mesh furniture, yellows (build D) | dock clutter density read; higher-tier swaps |
| characters | Mixamo bodies, gait archetypes | Jafar's clip session; combat set is disk-only |
| lighting | REAL noon shadows + deepened AO + grade; linear closed; V6 first slice | the AMBIENT FILL — a sun-perpendicular wall reads 0.039 against a lit 0.431, and `ambientSeries` is dispatched to set it; then HDRI as the environment source |
| animation feel | walk/idles + 18 activities + 6 reactions wired | reaction states for the rigs that refuse them — X's reactWhy reads noState:339 against cooldown:97, so most asks die on a controller with no state for the slot; then smoke/thinking re-harvest; walk transitions (disk-only) |
| audio | foley, barks, procedural score | voices into build (Thu); positional street sounds |

- **M21, the two ledgers.** Empire growth, law as a tool, what expansion costs
  you. Entirely unbuilt, entirely Core, so entirely doable here without a round
  trip. This is the largest piece of unwritten game left.
- **M22, the shape of a playthrough.** Onboarding, pacing, replayability and
  succession — also unbuilt and also Core-shaped.
- **Read a system and write down what it actually does.** Every system here
  has at least one comment now false, and each one found is a bug that would
  otherwise have been believed. **Read the code that produces a number too**
  — three faults in `CollidingNames` came from reading it, not its readings.
- **Turn a still into a number.** Five faults found by opening a frame and none
  by a gate. Anything a frame shows that no metric names is a metric worth
  adding.
- **DROPS DELIVER EVERY RUN.** Open: the d12 shape — a night the job
  never owned (`held:waypoint`, ran=0) while the skip plant says it
  stopped at day 11. Trace-first: read TraceJob's window source against
  the active-job timing before any change.
