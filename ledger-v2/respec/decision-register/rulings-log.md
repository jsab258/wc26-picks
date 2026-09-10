# The rulings log: one register, every ruling findable

STATUS: LIVE. Written 2026-09-10, in the cleanup batch Jafar ruled that day.
Wrong here is a bug: this file is the register's index, and an index that
misses a ruling sends the next session to invent one.

## Why this shape, and not seventy new D-numbers

Before today the project had three decision stores: this register (the
D-numbered spine, 18 files), the director's own rulings written in place as
the work happened (`game-design/decision-*.md`), and a queue of
cards (`production/decision-queue.md`). Jafar ruled one register on
2026-09-10. A D-number is the heavy instrument: it marks a decision about the
GAME, cited by number in gates, briefs and tool docstrings, and a number
keeps its meaning for ever. Most of the rulings are not that. They are operational
rulings: this batch lands with these amendments, that instrument was wrong and
both ends are fixed, this dispatch goes before that one. Minting a D-number for each
of them would make the spine unreadable and would give each operational call
the same standing as the engine choice. So the register becomes ONE INDEX over
TWO KINDS: the D-numbered spine below, untouched, and a date-ordered log of
every director ruling, each with the path it lives at. One place to look, one
line per ruling, and nothing renumbered.

WHY THE RULING FILES ARE STILL AT `game-design/decision-*.md` AND DID NOT MOVE
UNDER `legacy/`. They are not history: they are the live substrate of a gate.
`ledger/verify.py` defines `DIRECTOR_DECISION_DIR = "game-design"` and
`DIRECTOR_DECISION_GLOB = "decision-*.md"` (lines 3124 and 3125 when measured on
2026-09-10) and globs that directory IN THE WORKING TREE
(`entries = sorted(d.glob(DIRECTOR_DECISION_GLOB))`, line 3332 the same day) to
find the `<!-- RULING spawn=... -->` stamps that `director_cadence` requires
before a commit of builder work is allowed. GREP THE SYMBOL, NOT THE NUMBER:
other lanes were editing `verify.py` while this was written and the two line
numbers had already moved 54 lines that morning. Measured 2026-09-10 while this file was written: 68 of
71 files carry such a stamp, four of them dated today, so moving them would
pull the stamp out from under the very commit that lands this fold. THE COUNT
IS A READING AT AN INSTANT, not a property of the directory: the brief for this
fold said 70 and a concurrent lane added the 71st while the index was being
generated. Re-count it, never quote it. The index points at them where they
are. Moving them needs that glob to move first, and that is a change to the
commit gate, which is a director's call and not a cleanup's.

## The D-numbered spine, untouched

Decisions about the game. Cited by number; a number never changes meaning.

- `D1-engine-probe.md` D1: Engine (probe, do not debate)
- `D2-faces.md` D2: Faces move
- `D3-comedy-register.md` D3: Comedy register
- `D4-combat-before-driving.md` D4: Combat before driving
- `D5-interiors.md` D5: Interiors, three tiers plus promotion by attention
- `D6-spend.md` D6: Spend plan, lower Tier 1
- `D7-verification-model.md` D7: Verification, calibrated taste judges
- `D8-visual-bar.md` D8: Visual bar, resolved for v2
- `D9-quality-ceiling.md` D9: Quality ceiling, resolved for v2
- `D10-framework-freeze.md` D10: game-studio frozen; one operative framework; harvest, not sync
- `D11-player-progression.md` D11: player progression
- `D12-information-surfaces.md` D12: information surfaces
- `D13-street-layout-method.md` D13: street layout method
- `D14-authored-interiors.md` D14: Authored interiors, and the stylised ceiling retired
- `D15-mickeys-on-the-built-street.md` D15: Mickey's is sited on the street that already exists
- `D16-engine-unreal.md` D16: the engine is Unreal
- `D17-no-alcohol-no-gambling.md` D17: no alcohol and no gambling, anywhere
- `D18-content-rule.md` D18: the content rule, permanent

## The director's rulings, date order

Operational rulings, written as the work happened. Each line is the date, what
was ruled, and the file it lives in, all under `game-design/`. Counted
2026-09-10: 71 files, 68 of them carrying a `RULING spawn=` stamp.

- **2026-08-25** batch commit, noon inversion, stale CLAUDE.md, yard_fence, brief shape, ref stills
  `game-design/decision-2026-08-25-partial-batch-noon-inversion.md`
- **2026-08-25** ValuePanel first firing (b7d232b), the three-item batch, and the §3b exemplar (25 Aug 2026)
  `game-design/decision-2026-08-25-valuepanel-landing-and-batch.md`
- **2026-08-25** the dressing batch, signage, and the US diamond (director, 25 Aug 2026)
  `game-design/decision-dressing-batch.md`
- **2026-08-25** ground albedo before decals (director, 25 Aug 2026)
  `game-design/decision-ground-albedo.md`
- **2026-08-26** district re-aim batch, `valueRungs` family pooling, day5_noon perpendicular (26 Aug 2026)
  `game-design/decision-2026-08-26-district-reaim-and-valuerungs-families.md`
- **2026-08-26** instrument-repair batch: series ordering, gate-detail ceiling, lint-red semantics, fixture unpin (26 Aug 2026)
  `game-design/decision-2026-08-26-instrument-repair-batch.md`
- **2026-08-26** sky-gain discriminator batch, fixture pins 5 to 7, shadowed assets, lint promotion (26 Aug 2026)
  `game-design/decision-2026-08-26-sky-discriminator-batch.md`
- **2026-08-26** sun-in-the-north finding, panel-repair batch, district cameras (26 Aug 2026)
  `game-design/decision-2026-08-26-sun-north-district-cameras.md`
- **2026-09-01** the cadence bound is MEASURED at 100, the two-builder batch lands, one overturn confirmed (1 Sep 2026, late)
  `game-design/decision-2026-09-01-cadence-bound-and-batch-review.md`
- **2026-09-01** the widened director_cadence, the prop viewer, and the four scope questions (1 Sep 2026)
  `game-design/decision-2026-09-01-cadence-widening-and-propview-batch.md`
- **2026-09-01** the meshgen batch, the dead builder, and the budget docs (1 Sep 2026)
  `game-design/decision-2026-09-01-meshgen-batch-and-budget.md`
- **2026-09-01** the preparation sequence that unlocks unattended local production (1 Sep 2026)
  `game-design/decision-2026-09-01-production-prep-sequence.md`
- **2026-09-01** D1 measurement (b) is RE-SCOPED, not dropped (1 Sep 2026)
  `game-design/decision-D1b-rescope.md`
- **2026-09-02** the constitution cut lands, the attribution sweep lands, the PC channel lands, and four folded questions (2 Sep 2026)
  `game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md`
- **2026-09-02** the D1 timebox is retired; measurement (a) fails by non-convergence, never by a date; the tilt toward Unreal is an allocation, not a reading (2 Sep 2026)
  `game-design/decision-2026-09-02-d1-timebox-retired.md`
- **2026-09-02** the free lane and the piece list land in one commit, the batch push is imagegen run 1, the window practicals are fixed in Core before Phase B, and a ruling now names the paths it reviewed (2 Sep 2026, evening)
  `game-design/decision-2026-09-02-free-lane-and-piece-list-batch.md`
- **2026-09-02** run 1's stopper is named from a positive record and the fix lands; the stop rule is sharpened; a second silent fault gets its instrument; the landing push is run 2 (2 Sep 2026, 17:20Z)
  `game-design/decision-2026-09-02-imagegen-run1-stopper-and-run2.md`
- **2026-09-02** BANKED means in the commit, the resume record reads what was recorded, and the landing push is the night run (2 Sep 2026, 19:44Z)
  `game-design/decision-2026-09-02-imagegen-run3-banked-means-in-the-commit.md`
- **2026-09-02** the rotation fix lands with one guard added, appliedYaw stays, Foot5 goes to the queue, and a ruling nobody applied is recorded as the process hole it is (2 Sep 2026)
  `game-design/decision-2026-09-02-rotation-fix-lands.md`
- **2026-09-02** ties go to Unreal and that moves D1's weight from (b) to (a); the blind look and the preference coexist by ORDER; D12 and D11 do not displace 027, they expose that the queue had no moat item (2 Sep 2026, evening)
  `game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md`
- **2026-09-02** the vignette batch lands with two in-batch fixes, four pairs bind, five crew names enter canon, and the D1 close is pre-registered (2 Sep 2026)
  `game-design/decision-2026-09-02-vignette-batch-canon-crews-d1-timebox.md`
- **2026-09-03** the 3 September two-builder batch (register gate, banner law, spawn log, UV sweep)
  `game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md`
- **2026-09-03** Director's Console step 2, the governance batch
  `game-design/decision-2026-09-03-directors-console-step-2.md`
- **2026-09-03** the lighting probe and Phase C materials land, with one hand-applied line first; the control-probe design is upheld; the claimed commandlet fallback does not exist and the claim is withdrawn, not the code (3 Sep 2026, 06:0xZ)
  `game-design/decision-2026-09-03-lighting-probe-and-phase-c-materials.md`
- **2026-09-03** the night batch of 2 September lands, with four one-line corrections applied first; the Unreal diff was read and three faults are named; 056 does not close; dispatch order confirmed with an abort clock (3 Sep 2026, 00:25Z to 01:2xZ)
  `game-design/decision-2026-09-03-night-batch-of-2-september.md`
- **2026-09-03** the still gate was reading its own explanation and both ends are fixed; the sweep names the instrument that could not have caught it; MADE now needs a wired UV chain; run 20 dispatches before the step is split (3 Sep 2026, 08:35Z)
  `game-design/decision-2026-09-03-texture-staging-and-the-still-gate-ratchet.md`
- **2026-09-04** queue 067 first pass, the Telegram bot, one builder, one review
  `game-design/decision-2026-09-04-ruling-067-telegram-bot-first-pass.md`
- **2026-09-04** queue 077, the gate's clock is the date in the file's name
  `game-design/decision-2026-09-04-ruling-077-deadline-clock-pin.md`
- **2026-09-05** queue 062 step 2, the third status word, lands and run 21 is authorised on it
  `game-design/decision-2026-09-05-ruling-062-step-2-third-status-word.md`
- **2026-09-05** queue 088, the inbound transport, lands with the wake half named and two holes filed
  `game-design/decision-2026-09-05-ruling-088-inbound-transport-batch.md`
- **2026-09-05** the 5 September build batch commits, the roadmap fold applies with two gates repaired, run 21 is dispatched on the committed state
  `game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md`
- **2026-09-05** the 2026-09-05 standing order becomes the queue, and the wake half is priced before it is armed
  `game-design/decision-2026-09-05-ruling-standing-order-refill-and-the-wake-half.md`
- **2026-09-06** queue 113, the model does not adjudicate. Approved for commit, with four dictated one-liners and three items awaiting numbers
  `game-design/decision-2026-09-06-ruling-113-the-model-does-not-adjudicate.md`
- **2026-09-06** the delivery batch (map availability, the notify consumer, the historical exemption, the outbox). LAND WITH AMENDMENTS
  `game-design/decision-2026-09-06-ruling-delivery-batch-map-availability-and-outbox.md`
- **2026-09-06** the Producer register's link band, the gallery page, and the morning brief in its new shape
  `game-design/decision-2026-09-06-ruling-register-link-band-and-gallery.md`
- **2026-09-06** the run 23 landing (material, study, map, supervisor). LAND WITH AMENDMENTS
  `game-design/decision-2026-09-06-ruling-run23-landing-material-study-map-supervisor.md`
- **2026-09-06** the run 24 landing (the instrument made the fault). LAND WITH AMENDMENTS
  `game-design/decision-2026-09-06-ruling-run24-landing-the-instrument-made-the-fault.md`
- **2026-09-07** Jafar's five rulings of 2026-09-07, and the order the game is built in
  `game-design/decision-2026-09-07-jafars-five-rulings-and-the-order-of-the-game.md`
- **2026-09-07** the executor landing (the third daemon, rule one). LAND WITH AMENDMENTS
  `game-design/decision-2026-09-07-ruling-executor-landing-the-third-daemon.md`
- **2026-09-07** the five-rulings batch (the walk, the scheduled task, the ladder, the clip, the caption). LAND WITH AMENDMENTS
  `game-design/decision-2026-09-07-ruling-five-rulings-batch-walk-task-ladder-clip.md`
- **2026-09-07** the inbox push fix, the plain failure sentence and the reading gate. LAND WITH AMENDMENTS
  `game-design/decision-2026-09-07-ruling-inbox-push-plain-failures-and-the-reading-gate.md`
- **2026-09-07** the installer resync, two fixes after 45de6c21. LAND WITH AMENDMENTS
  `game-design/decision-2026-09-07-ruling-installer-resync-breaks-the-deadlock.md`
- **2026-09-07** the remote restart job, and the pair of processes it would have refused. AMEND, THEN LAND IN TWO COMMITS
  `game-design/decision-2026-09-07-ruling-remote-restart-job-and-the-pair-it-would-have-refused.md`
- **2026-09-07** the walk clip's route, and the process on his PC that never restarted. LAND THE CODE WITH AMENDMENTS, HOLD THE MESSAGE
  `game-design/decision-2026-09-07-ruling-walk-clip-route-and-the-process-that-never-restarted.md`
- **2026-09-08** CrimeProbe, the grate and the art line. LAND WITH AMENDMENTS, DISPATCH IN TWO PUSHES, PULL THE PREVIEW OUT
  `game-design/decision-2026-09-08-crimeprobe-the-grate-and-the-art-line.md`
- **2026-09-08** non-interactive git and the sweep counter. LAND WITH AMENDMENTS
  `game-design/decision-2026-09-08-noninteractive-git-and-the-sweep-counter.md`
- **2026-09-08** queue 147, the composed telling, the clause the bank never had, and two collision readings. LAND WITH AMENDMENTS
  `game-design/decision-2026-09-08-queue-147-the-composed-telling-and-the-clause-the-bank-never-had.md`
- **2026-09-08** the Core port and its eight deviations. LAND WITH AMENDMENTS
  `game-design/decision-2026-09-08-the-core-port-and-its-eight-deviations.md`
- **2026-09-08** the crime, the witness and the overheard consequence. AMEND THE PROPOSAL, THEN BUILD
  `game-design/decision-2026-09-08-the-crime-the-witness-and-the-overheard-consequence.md`
- **2026-09-08** the lookup that lied, and the art line in-house. LAND WITH AMENDMENTS; RUN 3 WAITS FOR SIX SMALL ONES
  `game-design/decision-2026-09-08-the-lookup-that-lied-and-the-art-line-in-house.md`
- **2026-09-08** the return half and the correction. LAND WITH AMENDMENTS, ALL DICTATED
  `game-design/decision-2026-09-08-the-return-half-and-the-correction.md`
- **2026-09-09** the batch of fifteen, the Stop hook that fails open, the rights table that withholds, and what Jafar is told tonight
  `game-design/decision-2026-09-09-batch-of-fifteen-the-wake-hook-the-rights-table-and-what-he-is-told.md`
- **2026-09-09** the grate camera, the z-fight instrument, and what run 35 may claim
  `game-design/decision-2026-09-09-grate-camera-and-zfight.md`
- **2026-09-09** the grid batch reviewed, the elevation refusal upheld, and the null that turns out to be seven samples
  `game-design/decision-2026-09-09-ruling-the-grid-batch-review.md`
- **2026-09-09** the grid, not the ladder, and the sun that was 46 degrees from where the spec asked
  `game-design/decision-2026-09-09-ruling-the-grid-not-the-ladder.md`
- **2026-09-09** the settled exposure, the frozen tool, and the two lanes
  `game-design/decision-2026-09-09-ruling-the-settled-exposure-and-the-two-lanes.md`
- **2026-09-09** the split returns to the first screen, and the Blender that was always there
  `game-design/decision-2026-09-09-ruling-the-split-returns-and-the-blender-that-was-always-there.md`
- **2026-09-09** the sun-intensity ladder, its scope extension, its camera and its order
  `game-design/decision-2026-09-09-ruling-the-sun-ladder.md`
- **2026-09-09** the art lane's bootstrap, the board's two fields, and the sun the sky drowned
  `game-design/decision-2026-09-09-ruling-the-sun-the-bootstrap-and-the-board.md`
- **2026-09-09** the wake-drain opt-out, where its decision lives and how strict it is
  `game-design/decision-2026-09-09-ruling-the-wake-drain-opt-out.md`
- **2026-09-09** the typed systems inventory ships labelled as the studio's reading, seven tiles retyped by the director, two fields added, three retired-contract documents named
  `game-design/decision-2026-09-09-ruling-typed-systems-inventory.md`
- **2026-09-09** The grate rises flush: queue 162 lands, and the two clip risks become measurements
  `game-design/decision-2026-09-09-the-grate-rises-flush.md`
- **2026-09-09** the Hook comparison runs in the lane's own dialect, one link is ruled by whole URL, and the pages are stale, not absent
  `game-design/decision-2026-09-09-the-hook-comparison-the-ruled-link-and-the-stale-pages.md`
- **2026-09-09** the proof that dies with the container, three judgment calls, and the quantity a predicate cannot be written without
  `game-design/decision-2026-09-09-the-proof-that-dies-with-the-container.md`
- **2026-09-09** the railing in the line, the vote, the lift, and the denominator a step may print
  `game-design/decision-2026-09-09-the-railing-in-the-line.md`
- **2026-09-09** the regime change lands, three doors a grep cannot see, the sky with its stand-in retired, and what the Hook caption must say
  `game-design/decision-2026-09-09-the-regime-change-lands-three-doors-the-sky-and-the-caption.md`
- **2026-09-09** the twelve clauses, the person guard, and the buried grate
  `game-design/decision-2026-09-09-the-twelve-clauses-and-the-buried-grate.md`
- **2026-09-10** Cleanup batch: the four named dashboards are not orphans, the census gains 22 tiles, and my own sweep was wrong twice
  `game-design/decision-2026-09-10-cleanup-the-four-dashboards-are-not-orphans.md`
- **2026-09-10** ruling on the exposure ladder and the district sheet, 2026-09-10
  `game-design/decision-2026-09-10-ruling-the-exposure-ladder-and-the-sheet.md`
- **2026-09-10** ruling on the four-lane batch, 2026-09-10
  `game-design/decision-2026-09-10-ruling-the-four-lane-batch.md`
- **2026-09-10** ruling on the painted pieces, queue 223, 226 and 227, 2026-09-10
  `game-design/decision-2026-09-10-ruling-the-painted-pieces.md`

## Rulings that came off the card queue

`production/decision-queue.md` now holds OPEN cards only, by the same ruling.
Everything it had already decided moved, verbatim, to
`ledger-v2/respec/decision-register/queue-rulings-2026-09.md`. Counted there
2026-09-10: 19 card headings, 10 under TAKEN BY THE STUDIO (one of which is the
twelve cards taken at their defaults that morning) and 9 under the two RULED
THIS WEEK headings, plus the two standing orders recorded in Jafar's own words.
Nothing was summarised on the way: his sentences are quoted there exactly as the
queue carried them. The queue file keeps its flow rules, its WAITING section and
the one card under ON US, NOT ON HIM that is still open, which is 1 card of the
20 the file held before the fold.

## How to add to this file

A ruling about the GAME gets a D-number: a new file in this directory and a
line in the spine above. Every other ruling gets a line in the date-ordered log
above, naming its file. A ruling with no line here is a ruling the next session
cannot find, which is the failure this file exists to stop.
