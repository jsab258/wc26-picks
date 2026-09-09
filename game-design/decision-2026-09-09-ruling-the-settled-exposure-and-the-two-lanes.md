# Ruling: the settled exposure, the frozen tool, and the two lanes

> **STATUS: LOG, 2026-09-09. NOT CURRENT** once the conditions in section 8 are
> met and the batch is committed. Director ruling at spawn
> 2026-09-09T19:18:12Z on a four-piece batch across both lanes, a SIMULATION
> change, so the escalation is mechanical rather than judged.
> BUILDS ON: `game-design/decision-2026-09-09-ruling-the-sun-the-bootstrap-and-the-board.md`
> (14:24Z) section 3.3, whose freeze on `tools/frame-shadow-probe.py` piece B is
> tested against; and `game-design/decision-2026-09-09-ruling-the-sun-ladder.md`
> (16:28Z), whose run 38 this ruling retro-invalidates in part.
> STRIKES one of the three readings the exposure finding rests on, section 2.2.
> DECIDES the open question the art-lane builder raised rather than took,
> section 4.

VERDICT: ALL FOUR PIECES APPROVED. A's DIAGNOSIS STANDS ON TWO OF ITS THREE
LEGS AND THE THIRD IS STRUCK; A's STATED COST IS INCOMPLETE AND IS ENLARGED
HERE. B IS INSIDE THE FREEZE, NOT A BREACH. C's WAIT LIST NARROWS TO THE TWO
JOBS ON THE PC. D IS APPROVED IN FULL AND ITS THIRD BACKTICK BUYS A LINT, NOT
A PARAGRAPH IN CLAUDE.md.

## 0. What I could not run

NO BASH IN THIS SPAWN. I executed nothing: not `ledger/verify.py`, not
`tools/frame-shadow-probe.py`, not `tools/verdict-dupkeys.py`, not
`ue-probe/tests/frame-stats-test.cpp`, not the eight-fixture guard run, not a
git command. EVERY NUMBER IN SECTIONS A, B, C AND D OF THE BRIEF IS A
BUILDER'S, TAKEN IN ANOTHER SESSION, AND THIS RULING CONVERTS NONE OF THEM
INTO A MEASUREMENT. Section 8 turns the load-bearing ones into conditions on
the approval, which is the device the 14:24 and 16:28 rulings used today for
the same reason.

What I could do without a shell was read, and four things in this ruling are
mine rather than reported. Named so they can be checked:

- I counted the `runs-on` lines across `.github/workflows/` myself. NINE jobs
  read `[self-hosted, ledger-pc]` and none disagree: `ledger-setup-msvc.yml:82`,
  `ledger-restart-telegram-bot.yml:63`, `ledger-build-windows.yml:23`,
  `ledger-install-supervisor-task.yml:114`, `ledger-vignette-fetch.yml:60`,
  `ledger-art-blender-preview.yml:84`, `ledger-mesh-import.yml:58`,
  `ledger-imagegen.yml:157`, `ledger-probe-unreal.yml:52`. The three the
  builder calls GitHub-hosted read `macos-latest` (`ledger-build-mac.yml:37`),
  `ubuntu-latest` (`ledger-core-tests.yml:23`) and `ubuntu-latest`
  (`ledger-ai-playtest.yml:17`). C's population claim and queue 200's 9 of 9
  are both confirmed against the files.
- I read `production/queue/194-skycentre-measures-brick-on-half-the-cameras.md`
  in full. It is what strikes A's third reading, section 2.2.
- I read `ue-probe/tests/frame-stats-test.cpp` at 487 to 549 and found the
  determinism comparator already carries its rejecting case and its never-ran
  case. I had intended to demand both and I withdraw the demand, section 2.4.
- I searched every file under `.github/workflows/` for a backtick inside a
  double-quoted `echo` and found no live site. The pattern was single-line and
  double-quoted only, so it would not see `printf` or `Write-Host`, and no cap
  bit on that search.

Read in part, at every line this ruling rests on:
`.github/workflows/ledger-art-blender-preview.yml` 140 to 254,
`.github/workflows/ledger-imagegen.yml` at 51, 117, 292, 461, 492 to 513, 562
to 595, 666 to 723 and 750 to 759,
`ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp` 1580 to 1634,
`production/queue/208-the-camera-key-is-one-per-run-on-a-many-shot-line.md`,
`ledger/verify.py` 3024 to 3259, `.claude/agent-log.tsv` line 482.

## 1. Premise check, CLAUDE.md section 0

Nothing in this batch dates the world outside 1988 to 1992, nothing cites GTA V
as a target, nothing proposes a purchase or an account, no tool enters and no
licence entry moves. Piece D moves in the opposite direction and defends the
allowlist: the destructive path it closes would have written a stripped
`ATTRIBUTION.json` over the provenance of 45 shipped pictures, and that file is
licence evidence, which is law here. Pieces A and B serve the visual half of
the Meridian Test by way of the instrument: a rig that cannot photograph the
street at a settled exposure cannot certify how the street looks, and test
point 1 is a person not bouncing off the visuals. No conflict with the premise.

## 2. Piece A: the finding is right, one of its three legs is not

### 2.1. The verdict is approved

Temporal auto exposure, unconverged, carried across shots. Approved as the
cause. It is the rare finding that names an INSTRUMENT fault rather than a
world fault, which is CLAUDE.md rule 3 working as intended, and the three
readings were written with their meanings declared before they were taken,
which is the only reason this is a measurement and not a story.

### 2.2. R3 IS STRUCK, and the record must not cite it again

R3 was billed as "the place" and it is the leg that fails.

R3 reads `band.skyCentre` over 23040 pixels. The band is a fixed pixel
rectangle, 512/0/768/90, and 768 minus 512 is 256, times 90 is 23040 exactly,
so R3 is reading that rectangle and no other. That arithmetic is mine.

`production/queue/194-skycentre-measures-brick-on-half-the-cameras.md`, filed
earlier today and still READY, says of that same rectangle: "the cameras it is
read on do not share a field of view: cam_A and cam_B render at fovV=60.0,
cam_hook at 39.0. On the wide cameras that rectangle is mostly rooftops."

R1 was taken on camA_night and camB_night, the two wide cameras. If R3's pair
was taken on either, its pixels are BRICK, and brick is lit by the lanterns the
probe is switching off. R3 then does not merely fail to support the verdict, IT
SUPPORTS THE EXPLANATION IT WAS WRITTEN TO REFUTE: 0.8450 falling to 0.7731 is
a darkening, and darkening is exactly what removing a lantern does to a lit
wall. Queue 194 records cam_A's brick value as 0.8459, nine ten-thousandths
from R3's first reading.

SO R3 IS STRUCK BY DEFAULT. It is reinstated only if the resident confirms both
of its frames were photographed on cam_hook, where that rectangle does see sky.
The burden sits on the reading, because there is an open finding against its
band, and a reading whose validity depends on an unstated camera is not
evidence.

THE VERDICT DOES NOT NEED IT, and that is why this strike costs nothing:

- R1 IS THE CONTROL THAT CARRIES THE CLAIM. It compares two photographs of one
  shot with NOTHING TOGGLED between them, 0.28 s apart. Its validity needs no
  band definition and no camera argument, because the whole frame is the
  denominator and the scene is identical by construction. 715552 of 921600
  pixels darker, and 900970 of 921600 on the other camera, is a picture
  changing while the world does not.
- R2 IS THE DIRECTION AND THE SIGNATURE. Lights are being removed and the frame
  brightens, which is the wrong sign for any explanation that lives in the
  scene. The increments 295 253 214 174 139 121 94 fall in ratios of about
  0.86, 0.85, 0.81, 0.80, 0.87 and 0.78, and a decay near 0.85 per 0.28 s frame
  is a time constant near 1.7 s. Those ratios and that constant are my
  arithmetic on the builder's series, not a new measurement. A geometric decay
  is the shape of a first order low pass filter, which is what eye adaptation
  is. It is not the shape of a scene losing discrete lights one at a time.

FOR A FUTURE SESSION: the load now sits on R1 and R2 alone. If either is later
challenged, the finding does not have a spare leg, and nobody should discover
that by counting three.

### 2.3. The fix is approved and its cost is larger than the builder named

Snapping the adaptation RATE rather than pinning the exposure VALUE is
approved, and the builder's rule 2 reasoning for not pinning is correct: the
adapted exposure is a render-thread quantity this process never reads, so a
pinned value tonight would be a number nobody measured.

THE NAMED COST IS ACCEPTED: this rig can no longer judge a transition or an
adaptation-dependent moment, and walking out of a dark alley is the example.
That is a real loss and it is the right trade, because a rig that cannot
photograph a settled frame cannot judge anything at all.

THE COST IS INCOMPLETE, AND THIS IS THE OVERTURN. At speed 10000 the adaptation
is INSTANT but it is still AUTOMATIC. Exposure remains a function of the scene,
so removing a lantern still moves the exposure, and the delta the rig prints is
the radiance change AFTER auto exposure has fought part of it back. THE FIX
BUYS DETERMINISM, NOT PHOTOMETRY. A future session that reads "the exposure
fault is fixed" and then quotes a cross-condition light delta as a radiance
change will be wrong in a new way, and the sign of the new error is the same
direction as the old one: deltas read SMALLER than the light actually moved.

WHAT MAKES THAT MEASURABLE RATHER THAN ASSERTED, AND IT NEEDS NO NEW CODE. The
run already prints a per-shot band whose scene radiance is invariant across the
lantern conditions, because lanterns do not light the sky. Read `band.skyCentre`
ACROSS CONDITIONS on cam_hook shots only, where queue 194 says the rectangle
sees sky, and it is an exposure witness for free. Flat across conditions means
the deltas are quotable. Moving means they are not, and the series it prints is
the number the pinned value gets set from, which is ship the printer, read the
runs, set the bound, in that order. NO BOUND IS SET TONIGHT, per rule 2. The
witness is not valid on cam_A or cam_B until queue 194 lands, by the same
argument that strikes R3, and using it there would be the identical mistake
one day later.

### 2.4. The acceptance test: I withdraw my objection, having read it

I intended to refuse the acceptance test for having no rejecting case, which
CLAUDE.md rule 5b requires. I read `ue-probe/tests/frame-stats-test.cpp` at 487
to 549 and it is already there, in the tested layer, in the right order:

- Accepting first: two identical frames, `rigDeterminism=IDENTICAL`,
  `rigDiffPixels=0/1600`, `rigMaxAbsChannelDiff=0/255`.
- Rejecting, planted: three moved pixels, `rigDeterminism=DIFFERS`,
  `rigDiffPixels=3/1600`, `rigMaxAbsChannelDiff=7/255`, and a signed negative
  mean delta.
- Never-ran: `rigDeterminism=NOTHING-MEASURED` with
  `rigDiffPixels=nothing-measured` rather than a zero, plus a caller status
  word that outranks the arithmetic.

That is rule 5b and rule 3b satisfied in the layer where the tests run, which
is what `.claude/rules/instruments.md` demands of measurement arithmetic and
formatting. `rigRepeatAfterShots=11/11` prints the order separation with its
denominator. NO EPSILON is right: the claim under test is that identical inputs
give the same picture, and an epsilon on that claim is a ratchet.

The gap that remains is the live wiring, not the maths: a comparator that
accidentally reads one file twice prints IDENTICAL for ever. That is condition
C6.

### 2.5. The latent sky recapture, removed in the same pass

Approved. A capture keyed on the condition id, so that two shots naming one
condition in a row share a capture, is latent in run 38 only because no spec
line happens to name a condition twice in a row. THE NEXT SPEC THAT DOES IS ONE
EDIT AWAY AND WOULD HAVE PRODUCED A SILENT WRONG ANSWER, not a failure. Fixing
a latent order fault found while fixing a live one is correct and is not scope
creep, because it is the same fault.

## 3. What a past measurement from this rig is worth

THE SENTENCE, and it is written to be applied rather than admired:

A number from this rig is worth something only if it is a comparison INSIDE one
photograph, because a whole-frame exposure multiplier cancels in a same-frame
difference and cancels in nothing else; every cross-frame and cross-condition
number this rig printed before the rate snap is void, and in run 38 the
contamination has a known sign, later frames read brighter, so lanterns
REMOVED read BRIGHTER.

Two riders, because the sentence will be quoted without them otherwise. First,
a same-frame comparison keeps its SIGN and its ORDERING, not its magnitude,
since the tonemap is not a linear scale. Second, the sentence holds on both
sides of the fix: before the snap because the exposure drifted, after it
because the exposure still compensates. Same-frame is the safe comparison in
both regimes, which is why this rule outlives tonight.

## 4. Piece C: the wait list narrows to the two on the PC

THE OPEN QUESTION IS DECIDED. Wait on `probe-unreal` and `build-windows` only.
Keep querying all five and keep printing all five statuses in `artQueueSeries`,
because observing a hosted job costs one REST call and waiting on it costs this
PC real minutes.

Jafar said "queuing behind the game lane for the runner", and "for the runner"
is the whole clause. Three reasons, the second of which is decisive:

1. The three hosted workflows contend for nothing this job holds. I read their
   `runs-on` lines myself, section 0.
2. THE ART PREVIEW JOB IS ITSELF ON `[self-hosted, ledger-pc]`, line 84 of its
   own file. The poll loop therefore SLEEPS WHILE HOLDING THE RUNNER. Waiting
   on a hosted job is a lock held while sleeping: it hands the game lane no
   runner time and it delays the two PC jobs the wait exists to yield to.
   Waiting on the hosted three is not neutral, it is negative, and no series is
   needed to know the sign of that.
3. The builder's own cycle argument already establishes that sleeping on the
   two PC names is a cycle the cap breaks. Narrowing does not weaken that; it
   removes the half of the list where waiting cannot even be a courtesy.

CONSEQUENCE, STATED IN ADVANCE SO NOBODY READS IT AS A BUG: with the list
narrowed, and one runner process serving one job at a time, the loop should
read clear on the first poll essentially always, and the yield becomes a
roughly 30 second no-op. THAT IS THE CORRECT OUTCOME. GitHub's runner queue
already implements what Jafar asked for, before this file gets a say, and what
remains of value is the printed series and the NO-RUN verdict.

AND A TRIPWIRE. If a `.pc` name ever reads in progress while this step is
executing, that is a FINDING and not a wait: it would mean more than one runner
process is registered on ledger-pc, which breaks the one-job-at-a-time
assumption this whole design rests on. It must be printed loudly rather than
slept through.

MY OWN FINDING, WHICH THE BUILDER DID NOT RAISE: the five-workflow population
is UNDER-INCLUSIVE on the runner axis. Besides this job there are eight other
`ledger-pc` jobs and the list names two of them.
`ledger-vignette-fetch.yml` in particular feeds the game lane's own vignette
probe and is on the PC and is not on the list. I am NOT expanding the list
tonight: dropping the hosted three is free and certain, adding PC names costs
waiting, and the series that would justify it does not exist yet. Filed,
section 7.

Also in C, approved without conditions: the failed query no longer counting as
busy, on the builder's reasoning that under a queue a failure counted as busy
is the infinite wait; `QUEUE-CAP-HIT` with busy names and lanes and exit 1
rather than rendering anyway; `queued` deliberately absent from the status
filter; the `NO-RUN` verdict published on refusal, which is directly
`.claude/rules/ci.md` and which fixes a genuine denominator fault, a lane that
never rendered for a week reading identical to a lane nobody dispatched; the
`runs-on` pin at 9 of 9, which I checked; and the job timeout at 65, where 12
minutes of cap plus 30 minutes of render leaves 23 minutes of margin and the
harm it prevents is a run that commits no verdict at all.

ONE THING C MUST NOT DO SILENTLY: a wait of zero because the API was
unreadable and a wait of zero because nothing was busy must not print the same.
The `unknown` count belongs in the committed verdict beside its denominator.

## 5. Piece B: inside the freeze, not a breach

INSIDE. Three reasons, and the third is the one that makes it testable.

1. THE FREEZE NAMES WHAT IT FREEZES. The 14:24 ruling, section 3.3: "The
   maths, the luma weights, the tracer and the binning are frozen", with an
   explicit carve-out, "Frame and shot selection may become arguments". Reading
   a camera pose off the shot's own keys instead of off the run line is shot
   selection and binding. Binning is a histogram word and binding is not it.
   Refusing an unparseable pose instead of raising, and rewording two comments,
   are not measurement changes.
2. THE FREEZE WAS SCOPED "in the same commit as the light change", to keep an
   input readback from moving an outcome. This batch is not the light change.
3. THE FREEZE SHIPPED ITS OWN ESCAPE CLAUSE and it is the acceptance test here:
   "that fix lands and re-runs against the OLD frames first, and the number it
   changes is stated." The builder verified against a fixture from the real
   formatters, which is good and is not that. Condition C8.

THE LINE THAT SEPARATES INSIDE FROM BREACH, and it is mechanical: on run 38's
old frames the only permitted change is REFUSED becoming BOUND. A number that
was measured before and MOVES is a breach of the freeze, and the resident stops
and escalates rather than reasoning about why it moved.

Note for whoever runs C8: run 38's frames are void as photometry under section
3 but remain a valid BIND fixture, because the bind reads pose keys and an
exposure drift does not move a pose. No luma number that re-run prints may be
quoted as a fact about the street.

The rest of B is approved. Zero new ambiguity at 99 same-line and 16 cross-line
over 59 lines against 99 and 16 over 58 committed is a proper zero with a
moving denominator, and the reversed-shot-order run reading byte-identically is
the acceptance criterion queue 208 asked for, met on its own terms.

## 6. Piece D: approved in full, and the third backtick buys a lint

Approved. Three notes, one of them a ruling.

The rule 6 finding is the cheapest lesson in the batch: a tool grew
`--batch-settings` and its only caller never learned. The guard belongs in the
workflow and not in `imagegen.py`, because a tool invoked without `--spec`
structurally cannot know one was requested. A guard belongs at the site that
knows the intent.

The destructive half is the serious half. A REFUSED manifest and a stripped
`ATTRIBUTION.json` written over the provenance of 45 shipped pictures, staged
by name, is licence evidence destroyed by a fallback, and the allowlist is law.
It never fired. Rule 5, look before you destroy, and the guard refuses before
anything is spent, with `itemsExamined=0 picturesGenerated=0
result=nothing-measured` rather than a bare refusal.

THE RULING: RUNNING IT IS WHY THE TWO FAULTS EXIST TO REPORT, which is
`.claude/rules/ci.md`'s own first bullet, the entry point being cheaper than
the argument. Fault 2, a detector counting every `spec` key while
`batch_settings` is last-wins on an append-only sentinel, would have refused
every future run permanently and is section 7's pattern in a fourth place.
Fault 1, backticks inside a double-quoted `echo` executed by the shell, is the
THIRD instance of a class CLAUDE.md already carries a sentence about. The
sentence did not prevent it because the sentence is scoped to commit messages
and heredocs and this was a workflow echo. A THIRD INSTANCE IS WHERE A WRITTEN
WARNING IS REPLACED BY A MECHANICAL CHECK. DO NOT ADD A PARAGRAPH TO CLAUDE.md:
it was 16,291 words on 1 September and its own rule sends new paragraphs to a
casebook. The incident goes to
`ledger-v2/studio-v2/casebook-build-and-evidence.md` and the lint goes to the
queue, covering `printf` and `Write-Host` as well as `echo`, which my own
search did not.

## 7. What this batch actually is: one fault in five places

Four builders found the same fault and none of them said so, which is why it is
worth naming here rather than in four places.

1. A: the exposure carried ACROSS SHOTS, so a frame's value depended on which
   shot preceded it.
2. A: the sky recapture keyed on condition id, so two shots naming one
   condition in a row shared a capture.
3. B: the camera printed on a one-per-run line, last camera placed wins.
4. D: the detector counting every occurrence of a key whose setting is
   last-wins.
5. MINE, found by reading the artifact:
   `ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp:1625` prints
   `tonemapStat=last-camera-placement/one-per-run`. The exposure override WRITE
   at 1610 to 1614 is on the camera's own component, but the READBACK that
   proves the snap was in force is one-per-run and last-wins. The action may be
   per-camera while the evidence for it is not, and only the evidence is
   committed.

THE RULE, which is queue 208's own sentence generalised: when a key can appear
more than once, the reader declares which occurrence wins; per-sample facts
print on the sample line; and A RIG WHOSE OUTPUT DEPENDS ON THE ORDER OF ITS
OWN SHOTS IS ONE REORDERING FROM SILENCE, so any rig that photographs more than
one thing owes a proof of order independence on its own output. A's
`rigDeterminism` and B's reversed-order run are that proof in two places. The
tonemap line does not have one yet.

## 8. Conditions the resident checks before committing

Nothing here is committed on my ruling that is not named in it. Anything else
in the diff is uncovered, and `director_cadence` is right to keep blocking it.

- **C1.** `python3 ledger/verify.py` green, and the footer pasted FROM
  `ledger/.verify-footer`, never from the scrollback.
- **C2.** `tools/docs-check.py` passes on this record, which declares LOG in
  its first lines.
- **C3.** `director_cadence` clears with this record's stamp. It names
  2026-09-09T19:18:12Z, which I read at `.claude/agent-log.tsv` line 482 and
  which is the only `studio-director` row after 2026-09-09T19:00Z.
- **C4.** A, BLOCKING: confirm at the call site that the override write at
  `VignetteShot.cpp` 1610 to 1614 executes on EVERY camera placement and not
  once per run. If only the last camera got the snap, the batch does not land,
  because that is section 7's fault wearing the fix's clothes.
- **C5.** A: the `frame-stats-test` rig block passes all three cases, read from
  the output. I read the source at 487 to 549 and ran nothing.
- **C6.** A, BLOCKING: the scratch file the repeat writes is outside every path
  the commit step stages by name, and the committed verdict shows
  `rigRepeatAfterShots` with a non-zero numerator. A comparator wired to read
  one file twice prints IDENTICAL for ever, and a repeat committed under the
  first shot's name is the run photographing its own evidence twice.
- **C7.** A: read which camera R3's two frames were taken on. cam_hook
  reinstates R3; cam_A or cam_B leaves it struck as section 2.2 struck it by
  default. The verdict stands on R1 and R2 either way, so this changes the
  record and not the decision.
- **C8.** B, BLOCKING: re-run the changed tool against run 38's OLD committed
  frames and state what changed. REFUSED becoming BOUND is permitted. A
  previously measured number that MOVES is a freeze breach: stop and escalate.
- **C9.** B: `verdict-dupkeys.py` re-run and read FROM THE FILE, with the
  denominator change from 58 lines to 59 stated beside the unchanged 99 and 16.
- **C10.** C: the wait list narrowed to `probe-unreal` and `build-windows`,
  with the other three still queried and printed. This is ruled, so nobody has
  to decide it again. If the wait condition is not literally a one-line change,
  the resident does NOT hand-apply it: it goes to the queue carrying this
  ruling, and the harm meanwhile is bounded at 12 minutes by C's own cap.
- **C11.** C: the `unknown` poll count appears in the committed verdict beside
  its denominator, so a zero wait from a dead API cannot read as a zero wait
  from a free runner.
- **C12.** D: the eight-fixture guard run re-run and read from its output, 8
  passed, 4 accepting and 4 refusing.

## 9. The quality ladder: no aspect closes with a blank next rung

Per `production/quality-ladder.md`, asked at close: best available, or first
working? All four are first working, and all four have a named next rung, so
none of them is a research task tonight.

- A: PIN THE EXPOSURE VALUE, set from the witness series of section 2.3, which
  restores cross-condition photometry and buys back the transition blindness
  the rate snap pays for. Blocked on queue 194 for the witness to be valid.
- B: split the tonemap readback per shot, section 7 item 5. Then the 99
  same-line and 16 cross-line ambiguous keys, which this batch held flat but
  did not reduce.
- C: yield BEFORE taking the runner rather than busy-waiting while holding it.
  The cap papers over a busy-wait that owns the resource it is yielding.
- D: the lint that makes the backtick class mechanical across `echo`, `printf`
  and `Write-Host`.

FILED TO `production/queue/` BY NAME, numbers being whatever is free above 212,
because the name is the identity and a parallel session may take a number:
the exposure witness and the pinned value; the tonemap readback is one-per-run
on a many-shot run; the art lane yields while holding the runner; the wait list
is under-inclusive on the ledger-pc axis; a lint for backticks in double-quoted
shell strings in workflows; the verdict's 99 and 16 ambiguous keys.

Six items against Jafar's standing order that neither lane ends a turn with
work in the queue: one is blocked on queue 194, two are one-line changes, and
the rest are the next rungs above. The resident works them in that order while
budget and ceiling remain, per rule 13, and arms the resume rather than
stopping on a landed batch.

<!--RULING spawn=2026-09-09T19:18:12Z-->
