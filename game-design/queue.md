# The work stack

> **STATUS — LIVE**, verified 2026-08-21. What gets picked up next, in order.
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

### Where the street got to

Clips: 65 filled, 0 wrong. The street talks, argues, leans, works
counters. **The front is M17.10: the visual bar is GTA V** — item 1.

**THE PLAYTEST IS RETARGETED (22 Aug, Jafar):** *"I'll try to run it on
my windows machine after visual stuff is done. live voices/speech should
be working too."* His pipeline run came back ALL CLEAR at **1.7x real
time** on DirectML — the overhang is the SERIAL stages, not the model
(~25 tok/s both ways). Speech stage's first item: **the fp16 lever,
measured on his card** (one-click converter+timer shipped 22 Aug). The
streaming overlap exists in the backend, gated on a sustainability test
his card misses by ~15%; if his number clears ~1.0x the backend needs
Float16 binds and edge conversions (fp32-typed today).
`playtest-plan.md` has the session runbook; keep speech self-checks
green on every landing.
**THE RUNNER IS REGISTERED AND FLIPPED (22 Aug): `ledger-pc` builds
on his machine**; account in `roadmap-history.md`. **ALL 72 GATES
GREEN and holding.** ~17.6 min/round on his GPU vs cloud 33-41 over
11 rounds; the BUILD is no longer the bottleneck, the dispatch
cadence is. Closed 23 Aug: hair, furniture, clip sheet, dayJob and
beats (both onto StreetMap.Route), shopfront joinery.

**PERFORMANCE IS MEASURED; THREE GUESSES DIED.** `frameCost` ladder:
all:22.4 noShadow:17.3 noPixLights:18.0 noBodies:23.3. **Shadows 5.1ms
and per-pixel lights 4.4ms hold the frame; the crowd is not in the
bill.** Dead: draw calls, vertex budget, shadow reach. Only the rungs'
DIFFERENCES are a frame time.

**THE STREET WAS NEVER AS EMPTY AS THE PICTURES.** Three faults, all
found by measuring, all closed: the draw radius stopped at 34m (now
70); `streetBodies` counted people THROUGH WALLS (linecast now); and
the cameras stood badly (`ShotMidBlockedAt=0.30` off its own bimodal
series, 12 of 13 shots fixed; the street shot also FLED the crowd).
Day frames are NOT like-for-like across these.

**Closed 23 Aug and moved to `roadmap-history.md`:** the day/night
exposure fix (aperture was the lever, noon:night 1.25 -> **2.35:1**;
the Clamp ceiling and the rain term would each have eaten it silently
— both still live, do not re-raise without reading the history entry),
and the sills + ground roughness binding. Full accounts there.

**THE CROWD BEHAVES.** Density arrived as 13 people in convoy down the
CARRIAGEWAY: `Steer`'s first branch tested only for SOLID blockers, so
tarmac stopped nobody and every pavement rule below it was
unreachable. Guard on how far a line RUNS ON road (12m): headingIntoRoad
13 -> 5, crowdTightest 0.04 -> 0.23; its sampling cost 1.9ms until
coarsened 0.5m -> 1.5m. The frame then showed 1-2 people — correct
behaviour, fewer visible. DO NOT chase this by loosening the guard;
the lever is where ROUTES go. **meanFrame ~28.4ms with a ~1ms NOISE
FLOOR** (a comment-only build moved it 0.9ms), so single-run diffs
under 1ms mean nothing. `places` went red once and recovered untouched
(3/289 flaky). Revert `runs-on` if he bows out.
**BEFORE THE PLAYTEST, THE FULL ULTRACODE AUDIT** (Jafar, 22 Aug:
"a full ultracode audit before playtesting is a good idea"). Multi-agent
sweep of the whole codebase against every rule in CLAUDE.md, triaged into
the queue before he downloads the build. Pre-approved, token-heavy by design.

### Startable right now — JAFAR'S SEQUENCE (22 Aug, his words):
### "1. visual, 2. voices/speech, 3. playtest, then feedback/fixes and
### then continue w roadmap." Within a stage, order by what shows on
### screen. Nothing from a later stage starts while an earlier one has
### startable work, except reading a landed verdict, which is free.

1. **CLAUDE.md's `director_cadence` PARAGRAPH IS NOW FALSE — NEXT DIRECTOR
   SPAWN.** It says "Two candidate fixes, neither built". **The stronger one
   is built and live**: the gate now requires a decision RECORD in
   `game-design/decision-*.md` closing with `<!--RULING spawn=STAMP-->`,
   the stamp quoted verbatim from the log row. Both outcomes were watched on
   real data tonight — it REFUSED the director's own unstamped ruling ("a
   spawn row is attendance, not a review") and went `REVIEWED` once stamped.
   Selftest 38 -> 53 fixtures, and the refusal message now tells you to
   RESUME a killed director rather than restart one. Touching CLAUDE.md is a
   mandatory director trigger, so this waits for the next spawn rather than
   being edited here — but it must not wait long: a rules file that describes
   a hole as open when it is closed sends the next session to build it twice.
   **AND THE WATCHDOG HAS THE SAME HOLE, UNFIXED.** Its DAILIES CHECK reads
   *"if no `studio-director` row in the last 12 hours, spawn"* — a ROW, which
   is attendance. A director killed mid-ruling satisfies it exactly as a
   completed review does, which is the fault just closed in the commit gate,
   still live one layer out. `verify.py` already has the machinery to ask the
   better question (a stamped ruling newer than the reference). Same spawn.

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

1. **`sky>lit` FAILS ON 15 OF 15 DRY CAMERA ROWS — the whole game, measured.**
   Five references, seven districts, three others: **not one dry camera has the
   sky as the brightest broad surface.** References want sky > lit > ground >
   shadow; we read lit > ground > sky > shadow. The other two orderings largely
   HOLD, so this is ONE BAND out of place, not a general grade fault. **Ground
   work is invisible until it moves** — the road still renders 0.85 from albedo
   0.008. **No lever yet:** the aperture-versus-dome fork needs a discriminator
   that moves OPPOSITE ways under the two hypotheses.

1. **IDENTITY B BROKE, 63 PREDICTED vs 65 LANDED — AND THE EXPLANATION IS THE
   POINT.** Cause, checkable on the line: **8** rows read `litnone@0` before and
   **2** do now, so **SIX** rows gained, not the five predicted — 6x2 = 12, and
   53 + 12 = 65. The sixth is `day5_noon`, flagged by an earlier builder as a
   DIFFERENT fault (single perpendicular) but which also runs through
   `TourVantage`, so the one-character change reached it uncounted. **The
   instrument was right; the model of what it touched was incomplete — which is
   exactly what an identity is for.** Also missed: the lit-ray RANKING.
   Predicted downtown > copper ~ strip > hook >> fairview; actual hook 675 >
   copper 511 > downtown 445 > fairview 354 > strip 279. **Fairview was named
   the weak one in advance and is not.** Frontage metres did not predict lit
   rays and whatever does is unmeasured.

1. **THE NOON SUN IS IN THE NORTH — CLOSED.** `Euler(52,180,0)` -> sunward
   `(0,+0.788,+0.616)`; only north-facing walls are lit. A comment saying "due
   SOUTH" had been quoted forward into four documents and five camera
   placements. All corrected, re-swept, no live copy. Refs re-aimed, then
   districts; **`litnone@0` rows went 8 -> 2**, and the two remaining are dusk
   and a rainy noon, where no wall is lit and `?` is the honest answer.



1. **OUR EXEMPLAR OF RULE 3b IS ITSELF THE FAULT — `lint-static` INFLATES ITS
   DENOMINATOR 19x.** It prints `560 static bodies walked`; it actually scans
   **29**, across 14 of 88 files. `collect()` keeps only files matching
   `public partial class` exactly once and drops the rest **with no message**
   — 531 unexamined, 95% of the printed denominator. **CLAUDE.md cites that
   very line as the exemplar of the rule-3b fix**, so the rules file teaches
   the disease as the cure. Two items: fix the printed number (the SCOPE may
   be intentional; the DENOMINATOR is the bug) and correct CLAUDE.md — a
   director trigger. `lint-conditional-reach` names its unwalked set and is
   the model to copy. Six other lints are clean on this axis, checked.

1. **VERIFY'S RED PATH IS A `head -3` — it reports ONE finding of nine,**
   truncated at 90 chars, with no count and no `(+8 more)`. The cap that
   announces itself is a standing rule and the verify footer is the one place
   it is not obeyed, which is where it costs most: a red run's single line
   reads as the whole problem. Owner: whoever holds `verify.py`.

1. **THE VALUE INVERSION IS A DAYLIGHT FAULT, NOT A GRADE FAULT — read off
   the 71316fa pair before any number, which is the standing rule.** At NIGHT
   the structure is CORRECT: dark sky, dark ground, bright sodium points, one
   wet amber pool carrying the frame. At NOON it is inverted — near-white
   paving under a near-black storm sky, in both the new frame and the one
   before it. **The same grade produces a right answer at night and a wrong
   one at noon**, which localises the fault to the daylight path (aperture x
   dome authoring) and away from `FilmGrade` generally. That is a narrowing,
   not a conclusion: a picture is good evidence something is WRONG and poor
   evidence of WHAT, and four correct things here were once condemned off one
   screenshot. **`Core/ValuePanel` is being built to settle it with bands
   rather than eyes** — do not move a lever before it lands and prints a
   series (rule 2; the aperture moves ONCE, off a post-fix printed series).

1. **THE DRESSING LANDED: 736/739 placed, ZERO missed, all gates green, cost
   inside the ~1ms noise floor.** Open, and both about REPETITION — the tell
   the GTA bar exists to kill: `yard_fence` is 163 of 166 on the SHORTEST
   panel (`1x2`/`1x3` placed zero) — read the yard-depth series before
   touching the probe, the census says the gap is a CONSTANT 3.00m whenever
   the row-depth cap binds; and one street corner cannot see 736 objects,
   which is the argument for the eye-level cameras, not evidence of absence.


1. **DIRECTOR RULED THE DRESSING BATCH, 25 Aug — `decision-dressing-batch.md`.**
   **A: commit now, commit is not dispatch.** Re-DISPATCH stays barred until
   the hang fix AND the parser-breaking audit fixes land — the first build
   back is the run everyone reads. **B: the welded diamond REJECTS** (a US
   diamond on a post is the loudest wrong-country tell there is; the premise
   outranks a free asset). The rolled plate is honest **iff** no US livery
   survives the 45° roll — **confirm off the first still, not off the
   apex-midpoint number.** **C: signage is a named gap, and it queues HIGH** —
   street nameplates first: named streets whose names cannot be read is the
   information moat with a hole in it. **D: closes as first-working, with two
   that do NOT close** — `kitAlbedo`'s cap is a silently-biting instrument
   fault, not a rung, so it rides the audit-fix commit; and the duplicated
   TextMesh idiom is signage's FIRST task, because building signage otherwise
   mints a third private copy. Onto the ladder by name: the pub-sign board
   (the kit ships a mast arm with no plate) and a British terrace — the
   terrace's next rung is blank, so it is a RESEARCH task, not a fetch.
   **E: bank the `walk_start` re-pick and attach it to the image-gen
   delivery** — one interruption, two one-click items.




1. **THE TWO KITS ARE WIRED AND MEASURED (landed `71316fa`).** 736 of 739
   placed, ZERO missed, 6/6 lamp forms; `city-kit-suburban` is no longer an
   unreached kit and the Game layer now names 73 models against 62. Open, in
   `agent-reports/kit-survey.md`: the signage verdicts (the warning "triangle"
   is a US diamond — the welded one REJECTS), and the fence repetition below.


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
   **Glass is smoothness 0.90 and Window 0.85** (`SurfaceSpec`), on every
   facade in town — already highly reflective. What they reflect is a **64px
   cubemap baked off a three-colour gradient**, no structure at all. The
   near-black windows in every landed frame are dark BECAUSE there is
   nothing to reflect, not because they were authored dark: that is the
   largest reflective area in the game sitting on an empty environment. The
   blend shape trades a CONTINUOUS day (dusk warmth, night sodium, a per-day
   deck the ambient reads from) for photographic detail and pops between
   four fixed states; reflection-only is additive and cannot regress it.
   **Obstacles, both real:** (a) `Resources.Load` cannot reach `Assets/Sky`
   and `LoadImage` does not read `.hdr`, so the captures must MOVE under
   `Assets/Resources`, which moves the directory `attribution-check.py` maps
   to Poly Haven; (b) there is no NIGHT capture, so night keeps the
   procedural cubemap and the handover needs a ramp.

   **Ship the measurement with it:** the environment cubemap's own luma
   spread, before and after — a flat gradient and a real sky differ by an
   order of magnitude there, and that is the number that says the wire took.


   **LINEAR MPB CLASS-FAULT UNDER TEST:** MPB colours skip
   gamma-to-linear, so display-authored tints weakened at the flip. BODY
   WASH fixed first; 13 other MPB sites wait on the verdict, which was
   itself blocked by its own instrument until 23 Aug (the palest-part table
   named BlobShadow — a multiply quad sampling the pavement — four runs
   running; attribution skips Hidden/ shaders now). Real remainder: feet and
   shoes at 224-234, both tiers. **And a SECOND MPB fault is now open
   beside it:** `_Color` set through a property block on a shader that has
   no `_Color` is a silent no-op — see the kit-paint items below.

   **V6 FIRST SLICE LANDED** (dusk warmth, sun glow, sodium deck). Open
   from V6: the dome's cloud structure per time of day.
1. **THE `e8c5949` STALL WAS THE INTERMITTENT — CLOSED, CHANNEL IMPROVED.**
   Two later builds ran clean (`simExit=0`, 733s and 735s), so candidate B
   stands and no behaviour fix was needed. What the episode bought: the build
   step now prints `simExit` / `simTimedOut` / `simWaitSeconds` — it always
   computed them and threw them away, so "killed at 24 min" and "crashed"
   arrived identical — plus an in-sim watchdog that beats the external kill
   and `tools/hang-report.py`, which leads with POSITION rather than a tail of
   engine warnings. **The IK-warning lead was mine and was FALSE:** the raw
   tail is gated behind "no done line", so a healthy run cannot emit it; the
   warning appears in 3 of the 3 runs where it CAN appear. A printed field
   compared against an absent one. 3 of 352 kept runs have no done line, so
   this class recurs — the instrumentation is the deliverable, not a fix.


1. **BODY BUDGET CLOSED AT 87.8%** (account in `roadmap-history.md`). Live:
   the centre-third foot reading, and white pills with no committed still.

1. **THE INQUIRY RUNS NOW; TWO THINGS GATED ON IT STILL DO NOT.** *(moat:
   information)* `inquiry=Manhunt` lands, but `summonsTaken=0` and
   `redirectRelief=0.00` sit at zero — the latter in **248 of 326** runs on
   tonight's `--constant` sweep, which now sees sentinel words and bracketed
   rows (79 never-moved keys of 1347 harvested, 177 rows swept). The phone-line
   cause stands; the inquiry cause does not, and the two were read as one.



1. **PATROL DENSITY — open: `patrolOnBeatMean=0.00` over 3 shots vs `0.18`
   over 17. Zero of three separates nothing.



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
