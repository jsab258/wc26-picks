# NOW: what is in flight (read this FIRST, before the queue)

STATUS: LIVE. Verified 2026-09-03 after the batch ruling.

A session that resets loses everything not written down. The queue says what
to do NEXT; this file says what is ALREADY MOVING, which is the thing a fresh
session would otherwise duplicate, abandon, or wait for forever.

Keep it current or delete it. A stale NOW is worse than none, because it
looks like a live state.

## 2026-09-09 22:40Z: A CONTAINER RESTART KILLED TWO BUILDERS MID-EDIT

WHAT WAS LOST AND WHAT WAS NOT. The container restarted, both builders died
mid-edit, and the checkout rolled back behind origin. Everything pushed was
safe. Thirty-five uncommitted paths were not, and they were separated by hand
rather than committed together, because a resident never commits a builder's
work-in-progress.

THE ENGINE BUILDER'S 1625 INSERTIONS WERE REVERTED, NOT LANDED, and the reason
is that the tests caught real defects rather than pinned numbers. Three of 275
checks failed alone: the burial half ships the count it examined over the count
the file asked for; a fixture pinned to "pieces":593 could not be planted after
the count moved to 610; and a nothing-measured cell row CONTAINS A SPACE, which
is the instruments.md rule that every reader splits on whitespace. Two of those
three are faults in the new code. FIXING TESTS TO MAKE RED GO GREEN IS THE ONE
THING THAT ERODES A GATE, so nothing was edited to pass. The work is preserved
as a 2215-line patch in the session scratchpad, which does NOT survive another
container reclaim, and it is cheaper to rebuild from the ruling than to nurse.

WHAT LANDED INSTEAD: the record, the ruling, eight queue items, the pass-2 art
sentinel and spec, the rebuilt comparison sheet and its compositor, and the art
lane's two fascia meshes with their attribution. All of it reviewed, all of it
mine or the director's.

THE ART LANE GOT FURTHER THAN THE GAME LANE and its meshes are on disk:
ledger/Assets/Props/base-mesh/fascia_console_01.glb and fascia_cornice_01.glb,
with production/art/fascia-01/ carrying the station work. Its spec rows were
reverted with the engine batch because they moved a bill-of-materials count
that CoreTests pins, so the meshes are present and named by nothing yet, which
is rule 6 and is stated here rather than hidden. Queue 228 carries the burial
reading its placement produced.

## 2026-09-09 21:15Z: THE FRAME WAS OPENED AND IT MOVED THE RUNG

FOUR THINGS ARE IN FLIGHT RIGHT NOW, three of them builders and one a ruling.
A session that resumes this file should read this section before starting
anything, because all four touch rung 1 and two of them touch the same files.

  in flight  engine builder: the sky-by-sun grid on cam_hook, the in-frame
             ratio in FrameStats, wetness reaching the material, the fog's max
             opacity, and the DISPATCH entry. Resumed once after a turn limit.
  in flight  world designer: the fascia package through all five stations.
  in flight  content wrangler: the four surfaces with no maps (queue 223).
  in flight  studio director: the ruling on the grid, at
             game-design/decision-2026-09-09-ruling-the-grid-not-the-ladder.md.
  ready, held: the art lane's Hook pass 2 is written and validated and is NOT
             pushed, because two builders hold uncommitted work in this
             checkout and merging under them would destroy it. Push it with
             their work, not before.

THE ART LANE COMPLETED ITS FIRST FULL PASS. imagegen run 5 banked four Hook
draws at commit e4924cb7: wroteThisRun=4 blankThisRun=0 checkedThisRun=4, 154
to 157 seconds each. THEY WERE THEN OPENED AND INSPECTED BY VISION, which is
the middle step of the method and the step that had been missing. Seed
20260910 carries a crisp MICKEY'S; the other three garble it; every secondary
fascia is a smear on all four; and the three objects the prompt asked for were
dropped by the model while the four swatches arrived. Pass 2 corrects exactly
those and concedes swatch labels rather than risk the two fascias.

THE REFERENCE NUMBER THAT DROVE THIS RUNG ALL DAY WAS MEASURING A CAPTION
STRIP. The crop at (0,768,1024,1536) is 32 per cent swatch strip and near-white
caption band and omits 106 rows off the top of the photograph. The claim it
supported, that the two pictures' bright ends nearly agree, IS FALSE: reference
street p95 is 0.8239 against our 0.9532. Corrected in production/findings.txt
with nothing deleted, and both copies in this file corrected in place.

AND THE CORRECT BOUNDS WERE ALREADY IN THE REPO. vignette-scene.json's cam_hook
note records the panel content area as x 11 to 1012, y 662 to 1278, written
when cam_hook was placed from that panel, agreeing with tonight's independent
measurement to one pixel. THAT IS THE SECOND TIME IN ONE DAY that this studio
re-derived, wrongly, something already written down; the first cost a CI round
trip on a Blender question answered in blender-setup.txt on 1 September. Queue
220 is now "read the bounds that exist", not "find them".

WHAT THE CORRECTED BANDS SAY, and it is not what the instruction assumed:

    region      ref street photo              ours, ue-vign_hook_day
    ground      mean 0.4159  p95/p05 3.68     mean 0.7735  p95/p05 1.61
    sky         mean 0.6102  p95/p05 4.27     mean 0.6535  p95/p05 4.02

The sky band nearly agrees on level and on ratio; THE WHOLE GAP IS THE GROUND.
Limit stamped on it, because this is the shape that already misled twice: these
are proportional bands over pictures with different content, so the ground rows
are strong and the SKY ROWS ARE WEAK and may be a content coincidence. Queue
222 is that item.

THE BIGGEST FINDING IS NOT A LIGHTING NUMBER. Opening the frame beside the
reference shows no windows, no shop interiors, no signage and no road markings.
The obvious reading, that the blockout is untextured, IS WRONG and the verdict
refutes it: piecesTextured=563/593, texturesImported=36, texResourceValid=12/12.
The real fault is surfacesAbsent=card/interior/multiply/paint_yellow with
mapsFound=36/48, and the arithmetic closes exactly at 4 surfaces times 3 maps.

AND THE READING OF THAT WAS ALSO WRONG, corrected 22:05Z after the wrangler
answered it. NOTHING NEEDS SOURCING. card and multiply ARE NOT SURFACES AT ALL,
they are decal BLEND MODES declared at StreetVignette.cs:57 and enforced at
1651, and all twenty decal images are already on disk, ten generated plus five
CC0 ambientCG sets. paint_yellow is ProceduralOnly at AssetLibrary.cs:1613 and
a pack file for it is deliberately ignored. interior is generated from a tint
and BORROWS its normal and roughness from the window surface at
AssetLibrary.cs:611.

THE ACTUAL CAUSE OF THE BLANK FRAME IS ONE LINE, VignetteShot.cpp:2749: a piece
whose surface did not resolve gets NO MATERIAL INSTANCE AT ALL and renders the
engine default. 10 card + 10 multiply + 6 interior + 4 paint_yellow = 30, and
593 minus 563 is 30. The UE probe is missing four rules the Unity host already
has and that are already written down: the tint fallback, the
interior-borrows-window rule, any decal texture path at all, and the _b variant
rule, whose absence is why 15 of the 51 staged pack files are named by nothing.
THAT is the highest-leverage visual fix on the board and it is queue 223,
rewritten. Queue 227 is the gate whose green state would require shipping wrong
content; queue 226 is a false sentence in three files saying no yellow line art
is held, refuted by measuring it at yellowness 150.5 against 4.8.

THE RESOLVER WAS SIMULATED, NOT ASSUMED: re-implemented in Python against the
51 files on disk it printed surfacesResolved=12/16 mapsFound=36/48 and the same
four absent names, character for character with the PC. The ruler is understood.

THE SUN IS AT 82 DEGREES AND THE SPEC ASKS FOR 36. Proven by arithmetic on
committed files, not inferred. vignette-pieces.json:16 asks elevation_deg 36
and azimuth_deg 205; VignetteSpec.h's own two conversions turn those into an
asked pitch of -36.0 and an asked yaw of 25.0; the committed verdict reads
sunPitchYawRead=-82.0/25.0. YAW AGREES TO THE DECIMAL AND PITCH IS OFF BY
EXACTLY 46.0, which rules out coincidence and rules out the readback reading a
different actor. A 4 m post casts 5.5 m at the asked elevation and 0.56 m at
the rendered one, a factor of ten, and that is queue 197 explained. The
readback has printed the truth on every run since it was written and NOBODY
EVER DIFFERENCED ASKED AGAINST READ. Queue 224.

IT IS NOT THE WHOLE STORY, and the record says so rather than letting the
newest finding eat the older one. The grid ruling's own series has the
shadow-edge step at +0.0270 with three fills and no skylight and -0.0003 on
the same pixels with the captured sky. The sun was at 82 on both sides of that
change, so THE SKY IS WHAT KILLED THE STEP, which is exactly Jafar's diagnosis
with a measurement under it, and the elevation is a standing defect that caps
how much shadow is available at all. Both are real. The run separates them.

THREE OF THE RESIDENT'S OWN READINGS WERE REFUSED BY THE DIRECTOR TONIGHT and
all three deserved it. The inference that a sun would put a lit road far above
0.38 is an absolute-luma claim under unsnapped auto exposure, and there is no
level at which "far above" could have been checked. The frame it called night
is a dusk street with legible setts and a white kerb, which the director
established by OPENING it, as the resident should have. And shotMaxLuma=0.6240
is very likely a control-quad pixel rather than scene content, because
controlQuadHidden names only three frames and the quads are in all eight cam_A
frames. The whole-picture conclusion survives on the two band readings, which
are clean because the quad boxes end at y422 and the ground band starts at
y576.

SO THE ORDER HE GAVE IS BEING RUN IN PARALLEL RATHER THAN RESEQUENCED. His
words were sky, then wetness, then worn materials. The measurement says the
surfaces are the bigger lever and the sky may already be right. Decision TAKEN
and logged per his standing order: both run at once, the picture goes in the
brief with the numbers, and his verdict adjusts it.

## 2026-09-09 17:40Z: TWO LANES, AND NEITHER ENDS A TURN WITH WORK IN THE QUEUE

Jafar, reading total 39, Fable 38, ceiling 75. His standing correction first,
because it is about how a turn ends: "Do not stop when work lands. Continue until
the ceiling or a limit; on a limit arm the resume and continue when it fires. The
06:00 brief is a report on the way, not an end. If you find yourself about to end a
turn with work in the queue and budget left, that is yesterday's fault again; arm
the resume instead."

THE GAME LANE, RUNG 1, IN HIS ORDER. Two faults are fixed FIRST because they block
trusting any comparison at all:
  1. Frames with identical inputs must be the same picture. Run 38 proved they are
     not: camA_day and ladder_sun003 carry identical conditions and differ in every
     one of 921600 pixels, the later shot darker by a luma ratio of 0.82. Find and
     fix the shot-order exposure dependence.
  2. The verdict must carry ONE CAMERA LINE PER SHOT (queue 208) so the shadow probe
     can bind. It refuses on every ladder frame today and is right to.
THEN, and only then: bring the SKY DOWN toward the reference rather than pushing the
sun up, then wetness, then worn materials. EACH VERIFIED BY OPENING THE FRAME
against the lower panel of the Hook sheet, which is rule 4 and is the resident's job.

WHEN RUNG 1 HAS A FRAME WORTH HIS EYE it goes beside the panel in the brief and the
studio MOVES TO RUNG 2 WITHOUT WAITING. His words: "my verdict adjusts, it does not
gate." Nothing waits on him.

THE ART LANE IS PROTECTED at a third of the week's points and now QUEUES BEHIND THE
GAME LANE FOR THE RUNNER RATHER THAN YIELDING. That reverses the standing behaviour:
losing a render to a game job that happened to be running is a third of a lane's
output thrown away. A shared concurrency group is still refused, because that makes a
game job wait behind an art job.

HIS CORRECTION TO THE RECORD, AND IT REMOVES AN EXCUSE THIS STUDIO WAS LEANING ON:
Codex's concept sheets were inspected and corrected BY CODEX ITSELF, not by a person.
We had written "with a human eye between each pass" and built a fairness caveat on it;
their PROVENANCE.md says only "selectively edited after visual inspection" and names no
inspector. THE COMPARISON IS MODEL AGAINST MODEL. So it is not a fairness problem, it
is a METHOD problem, and a method problem has a fix: our lane draws the Hook from the
creation prompt, INSPECTS ITS OWN DRAW BY VISION, corrects once, and the result goes
beside theirs captioned THREE PASSES AGAINST TWO. It is sent whatever it looks like.

THEN the twelve-package batch, THE FASCIA FIRST, through all five stations to a real
mesh in the street. Every day after, in the brief, as images: one district sheet
regenerated in-house by the same three-pass method until all seven exist, one batch
package landed as a real mesh, and the Mickey's blockout iterated from its plans
toward a walkable interior shell. The two partial research gaps continue in the
background.

RULES FOR THE ART LANE, both of which cut against this studio's instincts: NOTHING IT
PRODUCES IS WITHHELD FOR QUALITY OR FAIRNESS, it is sent with an honest caption and he
decides; and NO NEW INSTRUMENT IS BUILT FOR IT THIS WEEK, because what exists is
enough to judge by eye.

THE CHANNEL: nothing reaches him except the daily brief and a genuinely Blocking card.
Every decision with a recommendation is TAKEN and logged.

## 2026-09-09 15:55Z: EVERYTHING HE ASKED FOR ON 9 SEPTEMBER IS LANDED

His three owed items and the map ruling are done and pushed. In his order:

1. THE BOT RUNS TODAY'S CODE. Restart job, botPidChanged=True, and the hash his
   machine reported is the CRLF form of the file here, which is why it can never
   equal ours (queue 193).
2. THE SKY LANDED AND WAS JUDGED, and two of the resident's own readings of it were
   FALSE and are corrected in the record: the control quads were hidden correctly,
   and band.skyCentre is a fixed rectangle full of rooftops on the wide cameras
   (queue 194). The before and after are committed as sky_before_after.jpg.
3. MICKEY'S RENDERED, fourth attempt, twelve point eight seconds, five frames on
   art/atlas-01 at 46d7d759 and the sheet at game-design/sim-shots/mickeys_blockout.jpg.
   Three distinct faults had to be cleared first and each was invisible until the one
   before it was fixed: no pwsh, then Blender searched in the wrong place while this
   repo held its real address since 1 September, then a commit step whose every git
   call was malformed by nullglob.
4. THE MAP IS THE BOARD HE APPROVED. 69 tiles, five areas, typed, and it no longer
   claims he ruled any of it. First screen committed as map_first_screen.jpg.

RUNG 1 CONTINUED AND PRODUCED THE MEASUREMENT IT WAS MISSING. Against Codex's sheet
our street has NO DARK IN IT: median 0.6992 against 0.3568, darkest twentieth 0.3249
against 0.1093 (CORRECTED 19:55Z, the first pair measured the sheet's caption
band; see findings.txt at the 2026-09-09 EVENING block). The cause is named by a control rather than inferred: THE SKY THIS
MORNING DROWNED THE SUN, which is still a bare literal 3.0f. Queue 205 is the ladder
that answers it and it is UNBLOCKED as of 15:36Z, because the probe is a game workflow
and starting one would have destroyed the art render in flight.

QUEUE ITEMS FILED TODAY FROM MEASUREMENT RATHER THAN FROM OPINION: 193 to 207.

THE 06:00 WAKE IS ARMED ON TWO RAILS and needs nothing further: the server Routine
fires 2026-09-10T04:07Z into this session, and production/wakes carries the disk
record, amended three times today with what the message must carry, what it must
admit, and what it must not oversell. THE SPLIT IS RETIRED FROM THE DAILY BRIEF.

WHAT THE MORNING MESSAGE HAS TO WORK WITH, all committed under game-design/sim-shots/:
rung1_vs_reference.jpg, mickeys_blockout.jpg, sky_before_after.jpg,
map_first_screen.jpg.

## 2026-09-09 13:45Z: THE MAP IS THE BOARD, THE SKY IS IN, THE RENDER WAS BLOCKED

SUPERSEDED IN PART BY THE 15:55Z SECTION BELOW IT IN TIME AND ABOVE IT ON THE PAGE:
the render is no longer blocked, it ran, and the previews are committed. Everything
else in this section still holds.

Jafar, reading total 31, Fable 33, ceiling 75. Three owed items and a ruling on
the map. Two owed items are done, the third is blocked and the blocker is named.

LANDED, 60405a13. The map page is the heatmap he approved: 69 tiles in five areas,
three colours, none hidden, the prose areas moved below the fold as the audit view.
The inventory went 27 entries to 69 and its status from evidenced to TYPED, which
is a change of contract, so it went to a director:
game-design/decision-2026-09-09-ruling-typed-systems-inventory.md answers five
questions and dictates six edits, all applied.

WHAT THE BOARD CANNOT DO, and it is his instruction that does not hold at this
size: every system a tile AND one phone screen stop being compatible at about 21
systems. 506 px of overhead plus 16.1 px a tile, so 844 px holds 20, and he named
25 player-facing systems himself. The page keeps every tile and says on its face
that it scrolls. Taken as a decision with a default, not sent as a card.

STILL OWED ON THAT PAGE and it is why the first screen is not yet his to judge:
the board says "ruled by Jafar and updated by his rulings" while 62 of 69 tiles
are a builder's reading and 7 a director's. Nobody has ruled one. A builder is on
it now, adding the computed attribution line plus the `short` and `where` fields
the ruling ordered.

THE SKY LANDED AND TWO OF THE RESIDENT'S OWN READINGS OF IT WERE FALSE. Both were
whole-run keys read as if they described one frame. The control quads were hidden
correctly (controlQuadHidden=3/5 names the rung-1 camera; controlQuads=3/3 is a
PLACEMENT count). And band.skyCentre is a fixed pixel rectangle read across
cameras whose field of view differs by half, so on the wide ones it is full of
rooftops: cam_A's 0.8459 is not the rung-1 camera's, which reads 0.9323 at spread
0.0078. Queue 194.

THE MEASUREMENT RUNG 1 WAS MISSING. The reference panel beside our frame: median
0.3568 against 0.6992, darkest twentieth 0.1093 against 0.3249 (CORRECTED
19:55Z, see findings.txt). OUR STREET HAS NO
DARK IN IT. The sky lit the street UP when the reference has not more light but
more shadow. Four items filed from opening the frame rather than from a gate: 194
the sky band, 195 no windows anywhere, 196 the street furniture is flat grey and
the phone box is not red, 197 nothing casts a contact shadow.

THE RENDER HE ASKED FOR IS BLOCKED AND THE BLOCKER IS NAMED. The Mickey's blockout
was dispatched on its own push after core-tests cleared, exactly as instructed, and
died in twelve seconds: `pwsh: command not found`. Nine workflows run on his PC,
eight call the PATH bootstrap, and the art lane is the one that does not. It is
also the one the bootstrap lint's hand list never names, so the lint read 0
problems honestly. A builder is deriving that list from the workflows instead. WHEN
IT LANDS, THE REQUEST FILE MUST BE TOUCHED AGAIN: the art workflow triggers on a
push to production/pc-ops/art-preview.request and an unchanged file starts nothing.

IN FLIGHT RIGHT NOW, three builders, none of them committing:
  the board's `short` and `where` fields plus the attribution line
  the art lane's PATH bootstrap and the lint that should have caught it
  queue 197's measurement half, naming why nothing casts a shadow

THE 06:00 WAKE IS ARMED TWICE OVER and needs no further action: the server Routine
fires 2026-09-10T04:07Z into this session, and production/wakes carries the disk
record, amended today with what the message must carry and what it must admit is
missing. THE SPLIT IS RETIRED FROM THE DAILY BRIEF, kept as a rule with its
fixtures, because it breaks two of his four register laws.

THREE PICTURES ARE COMMITTED AND WAITING for that message, under
game-design/sim-shots/: rung1_vs_reference.jpg, sky_before_after.jpg,
map_first_screen.jpg.

## 2026-09-09 09:15Z: THE CHANNEL REGIME CHANGE, AND IT RETIRES TODAY'S WORK

Jafar, with a reading of total 25, Fable 24, ceiling 75. His diagnosis first,
because it is the part that matters: "The channel fails because nobody with
judgment sits in it. Replace the machinery with one judgment step."

THAT IS A JUDGEMENT ON WHAT THIS SESSION BUILT. The morning answered a channel
that was not actionable by building MORE MACHINERY: a cards pass, a repaired brief
generator, a page notifier already running. The machinery worked, on its first
real run, and sent him six cards from a stale checkout, one of them withdrawn and
two of the day's missing. He is right that the fault was never the mechanism.

THE FOUR RULINGS, in his words:
1. ONE PRODUCER TURN A DAY writes the single message. It reads the queue, the
   findings, the decision queue, the receipts and the ladder, and decides what he
   sees and what he never sees. THE BRIEF GENERATOR, THE CARDS PASS AND THE PAGE
   NOTIFIER ARE RETIRED. The register stays as a FORMAT CHECK AFTER the Producer
   writes, not as a gate that shapes what is written.
2. The Producer applies the director test itself: no numbers with units, no
   coordinates, no file names, no studio vocabulary. It TAKES every decision that
   has a recommendation and a default, logs it, and reports the notable ones in
   the Sunday summary. THE SIX CARDS ON HIS PHONE ARE RULED AS THEIR
   RECOMMENDATIONS. A card reaches him only when the studio CANNOT form a
   recommendation, at most one a week, with buttons.
3. EVERY BRIEF CARRIES TWO BUTTONS, readable and unreadable. Unreadable means
   tomorrow's is written differently and the Producer says what it changed. THIS
   IS THE ONLY MEASURE OF THE CHANNEL: seven consecutive readable briefs, tapped
   by him, is the acceptance. SELFTESTS DO NOT COUNT.
4. Fix the cards race (queue 189), since one card a week still needs to be the
   right one. NO OTHER CHANNEL WORK.

THEN THE VISUAL WORK THAT DID NOT HAPPEN: the street has no sky, so add one, and
that is the correct fix for the road BEFORE ANY WETNESS; the Hook comparison from
the CREATION prompt in data/concept-prompts.json, not the edit file; the Mickey's
blockout render dispatched. Rung 1 continues. Images and clips arrive INSIDE the
brief.

DONE ALREADY: all eight decisions taken and logged under a new TAKEN BY THE STUDIO
section, WAITING is empty by construction, and the pages card is recorded as
RESOLVED BY EVENTS rather than taken, because the studio decided nothing there and
should not claim to have.

## 2026-09-09 09:15Z: THE ART DISPATCH MUST BE ITS OWN PUSH, OR THE RUN IS LOST

ledger-art-blender-preview.yml YIELDS rather than queues when a game workflow is
in progress, and its list is ledger-probe-unreal, ledger-build-windows,
ledger-build-mac, ledger-core-tests and ledger-ai-playtest. YIELDING LOSES THE
RUN; it does not defer it.

`ledger-core-tests.yml` fires on `tools/*.py` and `ledger/**`. So a push carrying
this batch and the art request TOGETHER starts core-tests, the art lane sees it in
progress, and the Mickey's render is lost rather than queued.

THE ORDER, therefore: land the batch, let core-tests finish, and fire
`production/pc-ops/art-preview.request` as its OWN push with nothing else in it.
Its two lines are exactly:

    commission=atlas-01
    recipe=mickeys-blockout

## 2026-09-09 09:10Z: SMALL, OPEN, AND EASY TO LOSE

The map's visual-ladder block carries one sentence in the third person on a page
written for Jafar in the second: "Every rung is a picture or a session Jafar
clears by eye, so these words are ruled by him". Every tile beside it says "the
street YOU see", "a character YOU control". The ladder file was mine and has been
corrected to second person throughout; this sentence is `tools/map.py` line 1960
and its wording is ASSERTED by `check_visual_ladder_is_ruled_not_measured` at line
3839 (`"ruled by him" in lad`), so it is a two-site change in a builder's file and
not a resident one-liner. Carried into the batch review rather than hand-applied.

## 2026-09-09 07:00Z: JAFAR'S STANDING ORDER, AND IT GATES THE GAME

His words, and the first sentence is the ordering rule for the whole day: "The
channel is not actionable and the art line skipped its visual half. Fix both
before any new game rung." Budget with it: total 16, Fable 17, taken at about
06:00Z, plan is Max 20x, ceiling 75 on the governing meter. Recorded as a row in
production/budget.md with its denominators.

THE ORDER OF THE DAY, his numbering kept:
1. MESSAGES. Every needs-you is its own message naming the exact question, its
   options, the recommendation, the default, the deadline, and a link to that
   one card and nothing else, with tap buttons. A message with nothing for him
   says nothing needs you and nothing more. The brief leads with outcomes, never
   counts, and queue 179 is DONE NOW by his ruling. Every image or clip sent is
   the newest of its kind, dated in its caption.
2. PAGES. The cards page reads the budget from his latest reading. The gallery
   shows the newest images first, dated, all of them, not two embedded files.
   The map page is the project overview: the ladder with the current rung
   marked, the areas as tiles coloured by status, and the next three, readable
   on a phone in five seconds, with no diagnostic text on the first screen. The
   town atlas from art/atlas-01 goes in the gallery as a world page, not on the
   map.
3. WAKES. A trigger that fires mid-turn is lost and it cost him yesterday's
   brief. Make wakes queue until the turn ends, and prove it.
4. ART, THE VISUAL HALF THAT WAS SKIPPED. (a) Regenerate the Hook district sheet
   through the local imagegen lane from concept-final-prompts.json and send it
   beside Codex's hook.png as two images in ONE message; that comparison decides
   whether concept images are made in house, and the previous run answered a
   different question. (b) Run the Mickey's five-camera blockout on his PC
   through the art lane and send the five previews. (c) One message, plain
   English, digesting the atlas-02 research: what was found, what is missing,
   with the link.
5. THE LADDER, visual-first, as a card. Written to production/ladder.md and
   filed as the card "Is this the visual ladder?".
6. THEN START RUNG 1. Art at its quarter share, game the rest. Brief at 06:00.

WHAT THIS REVERSES: the 2026-09-08 ruling "No further channel work this week."
The channel is now item 1 and it explicitly gates the game. The supervisor's
staleness stays a recorded finding.

## 2026-09-09 07:00Z: THE PAGES ARE 36 HOURS STALE, AND TODAY IT IS OUR FAULT

MEASURED on publish run 48, commit 650f0755, 06:28Z. Eight consecutive publish
runs failed this morning, numbers 41 to 48. Run 48 died on our own gate:

    tools/gallery.py --selftest: FAILED. 11 passed, 1 failed, over 10 check(s)
      FAIL the live repository renders a gallery and every check passes
             got: failed=pageBytes
    ##[error]Process completed with exit code 3.

The gallery base64-embeds every picture, the live repository outgrew its own
1000000 byte budget at 1000108, twelve of forty-nine pictures were dropped, and
the publisher runs that selftest as a gate before deploying.

CORRECTED AT 08:50Z, AND THE CORRECTION MATTERS. The resident first wrote that
the pages had NEVER been served. That is FALSE and a director refuted it. Of 48
publish runs, FOUR SUCCEEDED: 12, 13, 14 and 18, the last at 2026-09-07T20:23:12Z
on commit 45de6c21, which is exactly the pageCommit recorded in
production/map-notified.json. So the pages EXIST and were last published about 36
hours ago. THE FAULT IS STALENESS, NOT ABSENCE: every one of the 30 runs since has
failed, so a link Jafar taps opens a real page that does not show what today's
messages describe. That is a different fault with a different fix, and the card
that blamed the github-pages environment protection rule is describing 2026-09-06.

WHETHER THE ENVIRONMENT RULE STILL BITES IS UNKNOWN and is named as unknown: no
run has reached the deploy step since run 18. The order is ours first, un-embed the
gallery, let a run reach the deploy, and read what it says. That card has moved
out of WAITING into a new ON US, NOT ON HIM section of the decision queue so it
does not reach his phone as an ask he cannot act on.

CONSEQUENCE FOR ITEM 1: the per-card link resolves to a 36-hour-old page. The needs-you message
therefore carries the question, options, recommendation, default and deadline IN
FULL, and the link is a convenience rather than the payload.

## 2026-09-09: THE DAILY PROMPT DIFFERS FROM ITS RECORD, WRITTEN HERE FIRST

The daily wake's last line tells the session to compare what it is reading
against production/watchdog-prompt.md and to write any difference here before
doing anything else. THEY DIFFER, by four blocks, each one a ruling made after
the record's last reset on 2026-09-06:

1. The `tools/art-deliveries.py` paragraph and the whole art-branch convention,
   ruled by Jafar 2026-09-08. The record has no mention of it, so a session
   working from the record alone would never walk the art refs.
2. "WHEN SOMETHING IS SILENT, RUN THE EXISTING ENTRY POINT ON THE MACHINE AND
   READ ITS OUTPUT BEFORE PROPOSING A MECHANISM", ruled 2026-09-08 and carried
   in .claude/rules/ci.md.
3. "NOBODY TYPES CONTINUE AGAIN" with the THREE MINUTES OUT resume, ruled
   2026-09-06. This one is worse than an omission: the record carries an OLDER
   wording of rule 13 that the live prompt has replaced, so the record is not
   incomplete, it is wrong.
4. The reference to game-design/art-collaboration.md.

THE RECORD'S OWN WARNING IS WHAT CAUGHT IT: "THIS IS A SECOND COPY AND SECOND
COPIES DRIFT... The file cannot detect its own staleness; only the session
reading both can." It worked, three days late, because no session had compared
them since 2026-09-06. production/watchdog-prompt.md now carries the prompt as
received at 2026-09-09T04:09:00Z with the stale block kept beneath it, so the
drift is readable rather than described.

AND THE SAME WAKE NAMED THREE THINGS THIS SESSION HAD NOT DONE: read the inbox
(done, 0 inbound messages, so no blocking gap), walk the art branches, and stage
the 194 outbound records this checkout is holding untracked.

## 2026-09-09 05:25Z: THE GRATE IS IN A FRAME, AND IT LOOKS LIKE PALE PLASTIC

HEADING CORRECTED 2026-09-09 09:00Z. It read "READABLE AS IRONWORK" for four
hours and that was half true: the geometry reads, the material does not. Cropping
the subject rectangle out of the frame shows the bars and the gaps both pale grey
with almost no separation. Measured since, by tools/road-brightness.py:
roadCause=MATERIAL-ALBEDO, the kerb texture and not the light. The paragraph below
is kept as it was written.

RUN 36 ON 7a3fa3e. The camera traces before it shoots now: it tried three
standpoints, two were refused with rail_post1 named, and the third had five clear
subject rays and took the picture. grateShotStatus=AIMED, grateOccluded=no,
grateBlocker=none, grateCandChosen=02. ue-walk_05_grate_a.png has the drainage
grate dead centre, diagonal slots and a frame, nothing across it. That is the
piece Jafar named as the accepting case for the whole prop route.

EVERY PREDICTION WRITTEN INTO THE DISPATCH ENTRY BEFORE THE RUN HELD, including
the one that would have refuted the ruling behind it: rows 00 and 01 named a RAIL
piece and not prop_crowd_control_barrier_0. Row 02 taken, its control rectangle
OFF-FRAME as predicted, and the framing angles reproduced the computed series to
0.1 degree.

THE VOTE AND THE GRID AGREE ON THE CHOSEN ROW, 5/5 against 81/81, so on this
geometry the five-ray vote sampled past nothing. That is not the class being safe:
the harness proved the vote CAN miss a 42 mm bar 5.5 cm off centre, and the grid
stays for the run where it does. On row 00 the grid's first blocked cell already
named an infill BAR the vote could only call a post.

WHAT THE PICTURE ALSO SHOWS: the grate and the channel and kerb band around it
render NEAR-WHITE, almost paper, while the asphalt a metre further off in the same
frame is textured dark grey with red aggregate. It reads as a shape and not as
metal. Queue 176, and it is the visual bar rather than the prop route.

## 2026-09-09 03:30Z: EVERY KEY IS GREEN AND A RAILING STANDS IN THE LINE

RUN 35 aimed a camera at the grate and wrote two frames. grateShotStatus=AIMED,
grateRectStatus=MEASURED, grateViewRestoreStatus=RESTORED, walkFramesWrote=7/7,
and a director had checked the camera arithmetic before the run and found it
right to two decimals. THE PICTURE IS OF A CROWD CONTROL BARRIER IN FRONT OF A
WHITE VOID. Cropping the exact subject rectangle the verdict names and enlarging
it shows the guard railing's post and mid rail crossing the subject rectangle,
and the piece itself as a near-white patch with almost no texture. CORRECTED
2026-09-09 by a director who opened the frames: the resident named the wrong
occluder and called the pale patch void. The east kerb's pedestrian guard railing
E8 has posts at x=10, 12, 14 and 16 m in the plane z=3.375, one of them at the
grate's own x, and it stands between the camera and the piece; the crowd control
barrier is on the WEST side at x=22.5 m and cannot be in that frame. So there are
TWO faults and not one: a railing in the line, which this change addresses, and a
near-white render, which it does not.

THE Z-FIGHT READING FROM THAT RUN IS VOID AND MUST NOT BE QUOTED. It measured speckle inside a rectangle crossed by the guard railing's
post and mid rail, over a piece that renders as a near-white patch with almost no
texture. A flat near-white patch is not a surface a speckle statistic can read. Every denominator in it is honest,
which is what makes a correct reading of the wrong rectangle the worst kind.

SO ITEM 2 STANDS WHERE RUN 34 LEFT IT: the grate is a real imported mesh, it
reports collision, it is at the running surface, all from placed bounds. NOBODY
HAS SEEN IT. Queue 172 and 173 carry the two faults.

## 2026-09-09 02:40Z: THE GRATE IS AT THE SURFACE, MEASURED FROM PLACED BOUNDS

RUN 34 ON 31902b7: propFullyBuried=0/23 where it was 1/23 and the one was the
grate, and the reading carries via=loaded-asset, so it is the engine's own bounds
and not arithmetic on a file. propsAsMesh=22/23, propPlacedWithCollision=22/22,
propBurialSubject=.../collision=YES/topM=-0.0650/open=60.0pct,
propCentreWorstMm=0.00.

JAFAR'S ITEM 2 IS MET IN EVERY MEASURABLE PART. The grate is a real imported
mesh, it reports collision, it is at the running surface and it is placed 0.00 mm
from where the file put it. WHAT IS MISSING IS A PICTURE: the run's six key frames
are aimed along the street and nothing points at a 0.40 m square at x 12.0 on the
east channel. A builder is adding one still aimed at it and the z-fight reading a
director ruled must be a number rather than an opinion.

TWO CONDITIONS THE CLIP CARRIES WHEREVER IT GOES, and offering it without them is
the only version that is a fault. A double yellow line crosses exactly 25.0
percent of the piece, lying on it rather than through it, its underside 5.6 um
above the top face. And the top face is exactly coincident with two rendered
solids over about 0.16 square metres, which no number in this repository can yet
call a tie or not.

## 2026-09-09 01:10Z: THE STREET IS MADE OF REAL MESHES AND THE TOWN SPEAKS ITS OWN SENTENCE

RUN 33 LANDED EVERY PREDICTION. propsAsMesh=22/23 where every earlier run read
0/23; propPlacedWithCollision=22/22; the only fallback is pavement_sign, whose
GLB holds three mesh nodes and whose resolver correctly refuses to choose. The
throughput ledger's prop row went from 0 verified pieces to 22 in one run of
5 min 42 s, push to landed evidence.

THE OVERHEARD BEAT COMPOSES AND THE FRAME SHOWS IT.
overheardReplyMode=COMPOSED, overheardSummaryShape=clause where it read
sentence-not-clause, and clipCaptionsBySource=spoken..8/bank..0 where it was
0 and 8, with all eight differing from the bank row they would have burned.
Frame 17 of the clip was opened and reads: "You hear all sorts. The man that did
the window looked straight in at the shop before he ran, and his face is known if
not his name, apparently." That sentence did not exist before the run; it was
built from the rumour the mill carried.

WHAT IS NOT MET IS JAFAR'S ITEM 2, and the reason is geometry, not the pipeline.
propFullyBuried=1/23 and the one is the grate: it sits under the carriageway and
the channel both, 20.00 mm of cover at the west footprint edge and 10.25 mm at
the last sampled cell, so no camera can see it. Queue 162 carries the fix, one
row rising and taking the cross-fall, and it is a street-spec change under the
art line's review. THE GRATE IS A VERIFIED PIECE AND IT IS INVISIBLE, and those
are two different facts.

STILL OPEN AND NOT FIXED TONIGHT, by Jafar's own rule that only findings blocking
items 1 to 3 are fixed: six things the six stills say about the visual bar, led by
no human figure in any frame and a pure white sky. They are in the findings file
with the number that would settle each.

## 2026-09-08 NIGHT: THE CRIME LANDED, THE PROPS IMPORT, COLLISION DOES NOT

THE NIGHT'S ONE REQUIRED OUTCOME IS DONE. Run 32 launched the packaged build on
Jafar's PC and committed two crimes on Quay Street, one seen and one blocked by a
named wall (west_south_bay2), both decided by the ported Observe::Resolve on real
line traces rather than by a script. crimeStatus=COMMITTED twice,
witnessStatus=REAL, gossipStatus=REAL, overheardStatus=HEARD, memoryFiles=2/2,
clipStatus=WROTE at 2381728 bytes. production/next-three.json now has all three
steps in `done`, so the milestone's ladder reads 4 of 4 and the map shows the
goal as current.

THE PROP ROUTE WORKS AS OF RUN 3 ON 7f12005. propImported=15/16 propSaved=15/16
propUassetsOnDisk=16, and sixteen .uasset files are committed under
ue-probe/Content/Ledger/Props/. The grate resolves at 0.0474 mm worst against its
spec box.

RUN 4 ANSWERED THE COLLISION QUESTION AND THE ANSWER WAS YES ALL ALONG.
propCollisionPrims=15/15, propCollisionVia=not-needed/already-had-1=15,
propCollidable=15/15, and the grate itself RESOLVED with simplePrims=1,
bodySetup=present and 0.0474 mm worst against its spec box. The glTF import had
put a primitive on every mesh; nothing needed adding. What is still open is
PLACEMENT: the walk build has never placed one prop mesh (propsAsMesh=0/23) and
the grate sits 13.4 mm under the channel slab that spans it, so no frame can
show it yet. Queue 161 and 162 carry those.

WHAT RUN 3 SAID AND WHY IT WAS WORSE THAN NOTHING, kept because a deleted number
cannot be audited. The paragraph below was written before run 4 landed.
propCollisionPrims=0/15 was not a measurement: the legacy library refuses by
returning -1 rather than raising, the importer believed it, and a refusal became
a measured absence. Nothing read whether any of the fifteen has collision. A
mesh with no body setup photographs clean and a walking character falls through
it, so pilot package one still counts ZERO on the throughput ledger. The fix
landed uncommitted tonight: four add routes and three read routes, each read
back, a three-valued propCollidable, and a status word that separates measuring
a failure from failing to measure.

IN FLIGHT TONIGHT, so a fresh session does not duplicate it: queue 147, porting
StreetVoice.Exchange into the probe so the overheard reply is COMPOSED from what
the gossip mill carried rather than PICKED from a bank by seed. That is Jafar's
priority 3 and the rung above what run 32 achieved.

TWO TASTE CARDS ARE WAITING with defaults and a 2026-09-11 deadline: which bay
Mickey's takes, and how many bays it takes. Queue 155 (the pub's pavement beer
drop) is BLOCKED on both, on purpose: the drop goes in front of the pub's door
and building it first puts a hole in the pavement outside a pawnbroker.

## 2026-09-07: THE PAGES SERVE, THE MAP IS A MAP, AND THE ROUTE EXISTS

PAGES. Jafar allowed the branch to deploy. Publish run 12 attempt 2 landed on
`85b5222a` and run 13 on `284cfb76`. Eleven of eleven earlier runs had failed in
seconds with zero steps executed under an environment protection rule, which no
code change here could have fixed. Queue 139 DONE.

THE NOTIFICATION PATH IS PROVEN, and against the served page rather than a local
build. `production/map-notified.json` records `notified=true why=material-change
changedFields=q2/q3 digest=4917df34e120`, and the page it verified was served
from `284cfb76`, the commit that carried the redesign. The run before it recorded
a BASELINE and wrote nothing, which is the nothing-measured rule working: a first
reading is not a change. Queue 134 DONE. What is NOT proven is that Jafar
receives the message, which needs the bot running.

THE MAP. Rejected by Jafar as a dense diagnostic report and rebuilt as a visual
page: one sentence, the street frame inline, what runs and what to press, then an
SVG chain from player action to consequence, with every SHA and verdict key
behind a tap. Three area states are now DERIVED and each overturns a reading the
old page gave: the street is SEEN, NOT MEASURED rather than nothing measured, and
the word is granted only when the frame is shown; memory is RUNS, UNHEARD rather
than harness-only-with-12-of-12-ok; gossip is RUNS, AND HEARD from a different
fraction answering a different question.

THE STALE PRIORITIES ARE STRUCTURALLY IMPOSSIBLE NOW. `production/next-three.json`
is the one source and the NOW.md heading parser is DELETED, so THIS FILE NO
LONGER FEEDS THE MAP. Do not add a heading here expecting it to appear there.
The half that catches a superseded item is that nobody named it: queue 119's file
still says READY, so no status word would ever have caught it.

THE TELEGRAM TO CLAUDE ROUTE EXISTS AND HAS NEVER RUN. `tools/runner/executor.py`
is the third daemon under `START EVERYTHING.bat`. Hop by hop: Telegram, the bot's
inbox file, the pc-inbox branch, a 15 second poll, a journal line written BEFORE
anything starts, a fetch into an isolated worktree, `claude -p` bounded to 60
turns and 30 minutes, the register check, the outbox, the bot's sweep, a receipt
carrying the platform message id.

`git_call` RAISES on the repository root, because pc-watcher hard-resets it about
once a minute. Exactly one git call sits outside that guard, `git worktree add`,
once, touching no index or ref. The journal lives outside both checkouts.

NOTHING HAS BEEN DELIVERED. `production/outbound/` does not exist, so zero
messages have ever reached Jafar by any path, and the inbound half has never
carried one either. The first double-click of `START EVERYTHING.bat` is the
accepting case for the whole route.

## THE CODEX PATCH IS NOT INTEGRATED AND MUST NOT BE COUNTED

Ruled by Jafar 2026-09-06: "Keep any unavailable Codex patch explicitly
unintegrated. Do not count its reported fixes as completed or let locating it
block this delivery work."

A handoff described a patch from base `de158c2c` to `54c676d` on a branch
`codex/ledger-handoff-2026-09-06`. NONE OF IT IS HERE. There is no `.patch`
file anywhere on this filesystem, no `codex/` branch, and `54c676d` is not a
valid object in this repository. Its stated base matches what was HEAD at the
time, which corroborates the description and is not the patch.

So five reported fixes are UNINTEGRATED and none may be counted as done:
narrowed director review, unknown-reporting game and studio splits, evidence
uploaded before result banking, retained material and shader logs, and Core
novel actions requiring exact authorization. THE LAST ONE IS NOT TOUCHED AT
ALL, deliberately: it restricts functionality to close an authority hole, it
would reject every model-proposed novel state change with the live caller
supplying none, and it stays separate until its behaviour and its review are
resolved.

Where a fix here resembles one of those descriptions, it was written here from
this repository's own evidence and is not that patch. The retained material log
is the clear case: `production/d1-probe/ue-material-log.txt` exists because an
engine-specialist added the step after run 23, and it is what explained
`materialEditorCmdExit=1`.

## THE STREET IS TEXTURED, run 25, and queue 123 is DONE

Landed `87b20592`. The colour control quad renders its four bound colours where
it read chroma max 6 of 255 on the two previous runs; the whole frame with the
quad boxes excluded reads max chroma 133 over 873,860 pixels against a previous
whole-frame maximum of 15.

The third reading I set in advance is INVALID and not failed: it sampled a pane
of glass one metre from the camera while the brick it named sat sixteen metres
behind. Queue 137 inspects a named brick surface unobstructed. Nobody may
report that specific check as passed until it does.

## 2026-09-06, ANSWERED BY LANDED RUN 23: THE MATERIAL NEVER COMPILED

Run 23 landed as `de158c2c`, "UE machine probe from 245e368". Read
`production/queue/123` for the working. The one sentence:

    nothing in the scene was ever rendering M_LedgerSurface, so every number
    this project has recorded about BaseColorMap was about the wrong material.

The evidence, and it is a pair that only makes sense together. Every instance
readback is FULL: `midParamReadback=12/12 midScalarReadback=12/12
texResourceValid=12/12 compMaterialIsMid=12/12`. And neither the textures nor
the scalars reach the pixels: a control quad bound to a 2x2 of pure red, green,
blue and yellow renders chroma max 6 of 255 over 11,880 pixels, and two quads
of one size at one distance with tiling 1.00 against 4.00 render an IDENTICAL
9.0-cell checker. A perfect instance whose parameters change nothing means the
engine default material is on screen, and that material ignores instance
parameters entirely.

CANDIDATES A, B AND C ARE ALL REFUTED BY THE READBACK LINE. The tile pair is
what separated D from the rest; nothing else in this repository could tell
"the parameters do not arrive" from "the material does not exist as far as the
renderer is concerned", because the engine default and our own colour default
are both grey checkers.

The mechanism is a lead, not proven: the normal sampler carries a NULL texture
(`materialNormalDefault=none-of-2-candidates materialDefaultsBound=1/2`, both
engine paths failing in UE 5.8), and the generator's own line 161 says "A
texture parameter with no default can fail to compile".
`materialEditorCmdExit=1` beside `materialScriptReturn=0` is still unexplained.

NOT FIXED. A fix is in flight. `materialStatus=MADE` was printed over a
material that never rendered a pixel, so that word must get HARDER to print,
not easier: no compilation errors WITH positive evidence of a valid rendered
result, never the absence of a raised exception.

## AN UNPUSHABLE PROBE RESULT NOW FAILS THE JOB

`.github/workflows/ledger-probe-unreal.yml`, the "Commit the probe result"
step, ended on an echo and fell off the end with status 0. So runs 18 and 22
both reported SUCCESS having banked nothing, and both times the colour was read
as a landing. It now exits 1 on that path. The two accepting paths are
untouched and still exit 0: "nothing to commit", and a push that worked.

This is the other half of the CI rule this project already carries. "Verify a
job's EFFECTS, not its exit code" tells the reader what to do; it says nothing
about the job, and the job's duty is not to report an effect it did not have.

It does NOT make the evidence survive. A failed push still leaves the frames on
the PC. What it buys is that the loss is loud instead of silent, which is the
difference between losing a run and losing a run plus the hour spent reasoning
about numbers that were never written. As first written the step carried
continue-on-error: true, so the exit 1 failed the step and the job stayed
green; amendment A2 of the ruling of 2026-09-06 removed it, and the sentence
above is true from that commit on.

## SUPERSEDED, kept for the reasoning: the cause named before run 23

## 2026-09-06, THE STREET'S CAUSE IS NAMED, and it is not queue 062

Read `production/queue/123-the-sampler-reads-the-engine-default-texture.md`
before touching anything Unreal. The one sentence:

    the base material's colour sampler renders its own default texture,
    /Engine/EngineResources/DefaultTexture, and not the texture the dynamic
    material instance binds to BaseColorMap.

QUEUE 062 IS DISCHARGED AND WAS NOT SUFFICIENT. Its acceptance is met on
landed run 21 (commit 372fd95): `ue-build.txt` line 12 reads
`materialStatus=MADE materialScriptReturn=0 materialConnections=14/14`. The UV
head is wired and the four frames are still untextured. 062's stop rule (no
further Unreal dispatch) is LIFTED: the number it watched did move, 12/14 to
14/14. Wiring the head is what made this fault readable at all, because before
run 21 every sampler read one texel and a bound texture could not be told from
an unbound one.

The eliminations, each read off a committed artifact and not off a memory:

- The sampler IS connected to BaseColor, because the engine checker appears in
  `production/d1-probe/ue-vign_camA_day.png`. An unconnected sampler could not
  put it there.
- The samplers receive VARYING UVs: the checker on the hanging sign has a
  measured vertical period of 13 px over a 125 px face and the pillar strip 20
  px over 104 px, both detrended by a plane fit first. WITHDRAWN THE SAME
  HOUR, and queue 123 carries the correction: this does NOT prove the MID's
  scalar overrides arrive. The three large surfaces that would decide it carry
  no periodic signal at all after detrending (right wall sd 0.08, road sd 0.13,
  pavement sd 0.15), and flat is what a densely tiled checker mips down to AND
  what an untextured surface looks like. Whether any MID parameter of any kind
  reaches the shader is OPEN, which is why the dispatch now reads the scalars
  back as well as the textures.
- Import and assignment are not the fault:
  `production/d1-probe/ue-vignette-verdict.txt` lines 56 to 71 read
  `piecesTextured=563/593`, `texturesImported=36`, every albedo
  `2048x2048/JPEG-BGRA8/srgb=yes` under `albedoParam=BaseColorMap`. The 30
  unassigned pieces are exactly the four ABSENT surfaces, 10 plus 6 plus 10
  plus 4.
- The names are in the asset: `M_LedgerSurface.uasset` carries BaseColorMap,
  NormalMap, RoughnessMap, TilingU and TilingV in its name table.

THE PROOF, and it names a piece rather than averaging a frame.
`east_parade_bay3` is a brick_red piece, 6.00 x 6.20 x 8.00 m, occupying 308 x
226 px of camera A. brick_red reads `surfaceStatus=RESOLVED pieces=41
piecesAssigned=41/41`, so that piece HAS a material instance with
`brick_red.jpg` bound to BaseColorMap. Its wall face over 16,800 pixels renders
mean RGB (64.9, 66.7, 69.5), R/B 0.934, chroma mean 4.6 and max 7. The texture
is mean RGB (141.4, 131.3, 109.6), R/B 1.290, chroma mean 31.9. THE RENDERED
SURFACE IS COOLER THAN NEUTRAL WHERE THE TEXTURE IS WARM. Overcast light can
drain warmth out of a red brown albedo; it cannot invert the channel ordering.

The camera convention that rests on was established, not assumed: cam_A yaw 0
points along +x, found by trying all four axis conventions and counting piece
centres in frame, 474 of 593 for +x against 66, 5 and 0. A previous dispatch
projected cam_A using cam_B's position and yaw, so its region attributions are
wrong and are not to be reused.

The two weaker whole-frame measurements, kept because they were what pointed
here, both stated with what they do NOT reach:

- Maximum chroma 15 over 230,400 pixels sampled of 921,600. This refutes four
  of the twelve albedo files rendering anywhere in frame: brick_red mean chroma
  31 over 41 pieces, wood 42 over 32, roof 69 over 2, sidewalk texel(0,0) 86
  over 5. It does NOT refute the other five near-neutral ones, asphalt 2, kerb
  0, plaster 7, concrete 7, metal 22, which could render at 15 unnoticed. And
  how many of those 80 coloured pieces sit inside camera A's frustum has not
  been counted, so this is strong evidence and not proof.
- 6,714 of 14,400 eight-by-eight blocks below standard deviation 1.0. Nearly
  half the frame dead flat. This one does not depend on which pieces are in
  shot, which is why it is the load-bearing half.

LANDED AND DISPATCHED. The readback and THREE control quads are in
`e569b24d`, and `c84e8faf` appended run 22 to `production/d1-probe/DISPATCH`,
which is the push that runs the probe on Jafar's PC. Capture the sha before
watching: RUN 22 IS `c84e8faf`, and it is watched BY ANCESTRY, is there a
landed run whose commit CONTAINS it, never by branch movement or run name.

What run 22 answers. On the materials done line, read as a pair and never one
alone: `midParamReadback` and `midScalarReadback` over `midReadbackAsked`,
beside `texResourceValid` and `compMaterialIsMid`. Both short is A, no MID
override of any kind arrives. Scalar full with texture short is B. Both full
with the frames still flat is C.

Candidate D is answered by a picture and by nothing else. Quads `tile1` and
`tile4` are one size at one distance differing ONLY in their tiling scalars;
identical, beside full readbacks, means the base material never compiled and
every number about `BaseColorMap` has been about the wrong material. Quad
`colour` carries four saturated colours built in code, no file, no decode.
READ THE QUADS BEFORE THE KEYS, and read `quadBoxPx` to know where to sample.
The quads take about 5 percent of camera A in the left half, so any
whole-frame statistic from run 22 must exclude those boxes first; the right
half, where `east_parade_bay3` is, stays comparable with runs 18 to 21.

Nothing below this line has run an engine.

THE REGISTER AND GALLERY BATCH IS RULED AND AMENDED. Verdict LAND WITH
AMENDMENTS in
`game-design/decision-2026-09-06-ruling-register-link-band-and-gallery.md`. The
blocking amendment refused date-scoped rules: the gate was reading its rulebook
off the specimen, since a filename date is typed by the writer. Replaced by
`LEGACY_LINK_RULES`, three names frozen, never widening to a file dated on or
after 2026-09-06. All four amendments are applied and every selftest is green.

A RESIDENT ERROR ON THAT SAME GATE, recorded because the shape of it recurs.
The resident filed queue 124 claiming a resumed director can never satisfy
`director_cadence`. IT IS REFUTED, by the director and then by the resident
against the code. `verify.py` 3444 to 3455: the state is unruled only when
`ruling_fresh == 0`, so one stamp naming any fresh row clears it, and fixture
a14 is the accepting case for a killed-and-resumed director already. The
resident read `rulingRowsUnruled=1/2` and treated it as a failing bound; the
same footer said `director cadence ok` and the actual red was
`UNTRACKED/ABSENT TOOL(S)`. Rule 2: the same evidence is owed for WHICH number
a gate reads as for the number itself, and an unbounded reading that moves
looks exactly like a bound that is failing.

## Where this is, 2026-09-02: THE STREET RENDERS, and it is a street

Run 152198e landed all four frames and all three gate numbers came good:
`datumMissing=0/845` (521/845 before the rotation fix), the shapes line
`cylRolled=9 cylPitched=32 cylUpright=105` equal to the CoreTests print, and
`unityYaw=65.0 appliedYaw=65.0` so the sun rotation reached the light. The
Unity half of D1b is real for the first time: shared JSON in, four matched
frames out, nothing hand-placed.

ALL FOUR STILLS WERE OPENED, which is where the next finding came from.
cam_A day: parade on the left, shadows away and a little left, consistent
with bearing 25, which is the only thing that could settle the sun
conversion. cam_B day: square to the parade, roofline in frame, wet road
reflecting. cam_A night is the best frame the project has made. cam_B night
FLOODS, and that is queue 035: same rig, two angles, one of them wrong,
which makes it the rig and not the camera.

WHAT IS STILL MISSING, so nobody reads this as done: no character body, so
the scene is NOT YET an admissible (b) scene under D1b; shopfronts are flat
untextured panels; the plates carry the wrong district (queue 028); nothing
of Unreal renders at all yet (queue 027).

## Two decisions Jafar made on 2 September: RULED

Ruling: `game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md`.

**THE TIE-BREAK IS REVERSED AND IT MOVES THE WHOLE PROBE.** Unity now wins
only if the visuals are decisively better FOR UNITY, or if the Unreal loop
fails by non-convergence or hand-edit dependence. Otherwise Unreal wins, on
equal as on better. Named consequence, not softened: Unity ahead in one or
two pairs with Unreal ahead in none is a TIE and goes to Unreal.

So the weight moves from (b) the visual ceiling to (a) the loop. Landing
four admissible pairs through a converging loop is now winning, which makes
queue 032's round-trip printer the decisive instrument rather than a
nice-to-have. It rides 027's first UE dispatch.

**THE PREFERENCE AND THE BLIND LOOK COEXIST BY ORDER.** Write A, B or EQUAL
for each pair on the D8 decomposition, and why, BEFORE any label is
unmasked; the tie-break is applied to that sheet afterwards. Today no blind
look is possible at all, because both engines commit files named after
themselves. Queue 038 is the fix and WAITS for a UE still.

**D11 AND D12 DID NOT REORDER 027. They exposed something worse:** the queue
held twenty-two ready items and not one of them was a moat item. Queue 037
is that item, engine-neutral C# in Core, not blocked by D1, and it takes the
SECOND builder slot of a day ahead of every governance item.

## A correction to carry, from the ruling

The 20-minute UE round trip is run 16's ESTIMATE with cook and capture in
the loop, not a measurement. The measured figure is a 10-minute median over
9 rows taken before either was in it. That gap is exactly why 032 rises.

## Budget: RUNNING, at a measured pace rule

32 percent at 14:40Z on 2 September. The period is NOT a calendar week: the
one-time Tuesday reset restarted the counter and the next reset is the
normal Monday 14:00 CEST, so about 136 hours, of which roughly 14 percent
had elapsed against 32 percent spent. That is 4x over pace.

THE ALLOWANCE IS ABOUT 10 POINTS A DAY, roughly five spawns including the
resident's own turns. The rule and its arithmetic are in
`production/budget.md`. Three parts: two or three builder spawns a day and a
director only on a mandatory trigger; brief with facts inline rather than a
reading list; batch related work into one spawn rather than several.

WORK IS RUNNING AND THE DAILY ALLOWANCE IS RETIRED. Jafar, 2026-09-02: "I
don't care if we get to 80% before monday, we just stop when our budget is
used up". So there is no daily ration; run to the ceiling and stop there.
The 80 percent ceiling still binds and the other 20 percent is his.

IMAGEGEN RUN 1 RAN AND FAILED AT ONE SETUP STEP, AND THE FIX IS LANDED. Run
33654488608 on b8b805f2: the API's per-step conclusions put the only
failure at `The commit this run is measuring`, 0 seconds, and the four work
steps skipped behind it. Cause, from a differential over .github/workflows:
that step ran git without the safe.directory env every other git step on
ledger-pc carries, and the commit step's own git rev-parse succeeded under
it in the same run. The summary that named three causes it never observed
is replaced by tools/runner/step-verdict.sh (three states plus
NO-READABLE-OUTCOME, 32 checks). Ruling:
game-design/decision-2026-09-02-imagegen-run1-stopper-and-run2.md.

A SECOND FAULT IS NAMED AND NOT YET PROVEN: run 1 printed a verdict and
then `staged=0`, so the verdict never reached the committed channel.
Reading: Windows Python ends every stdout line in \r\n and bash keeps the
\r, so `[ -e "$f" ]` looked for a name ending in a carriage return. Run 2
prints every candidate with %q and strips it, which is the measurement.
The vignette-fetch loop is the same shape and has never staged a file in
this tree either (no fetch-verdict.txt, no surfaces/); queue 044 carries it.

## THE ASSETS ARE NOT IN THE FRAME (queue 046, found 2026-09-02)

37 props and 14 generated decals sit in this repository and THE STREET SCENE
USES NEITHER. Measured: `grep -c "base-mesh|BaseMesh"` returns 0 in both
`StreetVignetteHost.cs` and `StreetVignette.cs`, and no C# file names any
generated decal by key. The four frames Jafar has seen are built entirely
from primitive shapes.

BUILT IS NOT RUNNING, and the resident missed it while reporting asset
counts as progress. Jafar found it by asking what the images are FOR.

This outranks generating more pictures. The overnight batch adds 31 files to
a directory nothing reads: worth doing because it is free, but it moves no
number the Meridian Test measures. Queue 046 is what turns the inventory
into a street, and it is also the only way to learn whether a generated
decal looks right AT SIZE, ON A SURFACE, IN THE RAIN.

## In flight

- **THE HOURLY WATCHDOG IS OFF UNTIL MONDAY, AND HERE IS HOW TO PUT IT BACK.**
  Silenced 2026-09-04 on Jafar's instruction. It is `trig_01EA7ybQTcsiFyrTryptqVUi`,
  cron `20 * * * *`, and it is NOT a free reader: `persist_session` is true and
  its payload is a `type: user` message, so every firing delivers a user turn
  into this session and costs a cache read of the whole conversation plus
  output. About 76 firings sat between that instruction and the Monday reset,
  against 3 points of headroom.

  RE-ENABLING IS ARMED, not remembered: `trig_011GMwPxL5vvqrpb8Nxyzedw` is a
  one-shot at 2026-09-08T12:00:00Z that fires into this session and re-enables
  the watchdog first, before anything else. IF THAT ONE-SHOT FAILS, the
  watchdog stays off silently and nothing will say so, which is why this note
  exists: call `update_trigger` on `trig_01EA7ybQTcsiFyrTryptqVUi` with
  `enabled` true and NO prompt field, read it back to confirm, and delete this
  bullet.

  A note on the warning that came back when the one-shot was created: it said
  fired sessions run without connector tools, which would matter because
  re-enabling IS a connector call. It does not apply to a `persist_session`
  trigger. The evidence is the watchdog itself, which carries the same empty
  `mcp_connections` and has been firing into this session since 1 August while
  the session plainly has those tools.

- **MONDAY'S ORDER, queued 2026-09-04, START NOTHING BEFORE THE RESET.**
  Jafar ruled: spend nothing until Monday 14:00 CEST. The order below is
  PROPOSED and is confirmed by a fresh reading of BOTH meters on the day, not
  by this list. If the reading is not comfortable, the order shortens from the
  bottom; it does not start anyway.

  1. **Queue 062 step 2**, the third material status word. Small, and a
     precondition to the next dispatch.
  2. **Unreal run 21.** These two are first because they are the only items
     that end in something Jafar can LOOK AT: four frames that are not flat
     grey. If 21 prints `materialConnections=12/14` again, that is the answer
     and it gets reported, not retried, and D1's hand-edit clause is invoked.
  3. **Queue 080**, the send check that leaves no trace it ran.
  4. **Queue 079**, the queue gate reading `game-design/queue.md`, retired on
     31 August.
  5. **Queue 078**, the inventory of every list that means machine-written.
  6. **Queue 081**, the two small producer-check tidies.

  QUEUE 067, THE TELEGRAM BOT, LEFT THIS LIST ON 2026-09-04: Jafar moved it
  BEFORE the reset so that Monday is a full game day rather than a setup day.
  See the bullet above.

  Items 4 to 7 are all small and all found by grep at zero cost this week,
  which is the argument for doing that kind of looking whenever the meter is
  tight.

## 2026-09-06 04:10Z: THE FIRST DAILY WAKE RAN ITSELF, AND ITS BRIEF IS HELD

The daily trigger fired for the first time and did its own order unaided: read
the inbox, checked the budget, generated the brief from repo state. Nobody
wrote a word of it.

TODAY'S BRIEF IS GENERATED AND NOT SENT. It is kept VERBATIM at
`production/briefs/2026-09-06.md` because the tool's real output is the
evidence; the reasons live here rather than on top of it, since the register
gate correctly refuses a brief with a preamble and the resident learned that
by failing it.

TWO FAULTS IN ITS BUDGET SECTION, both filed:
- IT SAID TWELVE SESSIONS WENT TO THE GAME. ONE DID. The split counts WHICH
  AGENT TYPE ran, not what it built, so nine console passes by
  engine-specialists counted as game work on the most studio-heavy day this
  project has had. That is the number Jafar's item 5 rests on and it pointed
  the wrong way. QUEUE 111.
- IT DID NOT SAY THE DAY IS UNMEASURED. Newest reading 2026-09-05 08:30Z with
  27 sessions since, so the stop condition held and the brief printed only
  "taken yesterday", which reads as reassurance. QUEUE 112.

NO BUILDER WORK STARTED. An unknown budget is not permission.

THE "PASSED THE REGISTER" CLAIM IS CORRECTED, 2026-09-06, amendment A5 of the
ruling on the register's link band. Grepped repo-wide for the SENTENCE and not
the site, per rule 1: six hits, three of them inside the ruling record itself
that names the correction. The three real sites are
`game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md` lines
271 and 432 and `production/queue/095`, and all three now carry the dated
correction. NOW.md was named as a possible fourth and IS NOT ONE: it carries no
such sentence, and what it does say about that message is the paragraph below,
which was already right.

NOTHING HAS COME THROUGH THE BOT. `inbox-read` reports nothing measured, the
`pc-inbox` branch does not exist, and `outbound: records=0`, so the report
written on 2026-09-05 was never sent. That points at the bot not running with
that day's code rather than at the transport, which is untested either way.

## IN FLIGHT: THE ORDER OF WORK, ruled 2026-09-05 section 8

His list is the order; this is only about which files two builders cannot
share.

1. **088 alone, first, reviewed and committed on its own** so it lands early.
   Everything in item 1 stacks on its branch, and Jafar can test the transport
   tonight by sending the bot one message.
2. In parallel after it lands: **089 with 091** (both are the sender on the PC,
   one loop, one file), and **095 with 079's half** (a new tool,
   `producer-check.py`, `run-night.ps1`, the footer's counter). One review for
   the pair.
3. **090 with 104** (both are the bot's input handling), then **094**, then
   **093** when Jafar has two minutes and not before 088, 089 and 090 land.
4. Then **096, 097, 098, 099, 100** with its own stamped ruling, then **101**.
   After 100 lands the studio stops building studio; 101 still runs because it
   is item 5 of his order rather than a new process item.
5. Then the game: **062 step 2, run 21**, the first textured frames to him as
   images through 091. Then **102**, whose content-type choice is a director
   ruling. Then **103**, after 094 and 095.

THE VERIFY FOOTER'S `22 queue items ready` READS THE RETIRED QUEUE (079) and is
NOT TO BE QUOTED until 095 lands its counter.

## THE WEEKEND, RULED BY JAFAR 2026-09-06: GAME WORK ONLY

TWO ITEMS, IN THIS ORDER, AND NOTHING ELSE:
1. FIND THE CAUSE OF THE UNTEXTURED STREET and get Meridian's textures onto it.
   The wire moved to 14/14 and the frames changed; staging ran
   (`stagedTexFiles=102/102 piecesTextured=563/593`); the street still renders
   the ENGINE CHECKER and the cause is UNKNOWN.
2. QUEUE 119, the three unbriefed players. SUPERSEDED THE SAME DAY by Jafar's
   ruling to run the comparison in the studio: the sweep ran
   (production/stranger-test/, queue 127, lieHeard=0/90) and the redesign is
   queue 131, which waits for 129.

EVERYTHING ELSE WAITS FOR MONDAY unless it blocks those two: the remaining
audit items (114 to 118, 120 to 122), all console work, all tooling. ANY NEW
TOOLING OR PROCESS ITEM DISCOVERED THIS WEEKEND GOES TO THE QUEUE AND WAITS. It
does not get built.

SPEND DOWN TO ROUGHLY 75 OF 80 BY SUNDAY EVENING AND STOP THERE. Fable governs
and read 33 on 2026-09-06 at about 04:20Z. FRAMES COME TO HIM AS IMAGES.

THE ONE EXCEPTION, because he ordered it in the same message: the brief
register and the gallery page, since the first brief was wrong and he wants
today's rewritten in the new shape and SENT so he can judge it.

## NOBODY TYPES "CONTINUE" AGAIN, ruled 2026-09-06

A turn ends for the ceiling, a limit, or a genuine blocker. EVERY OTHER ENDING
ARMS THE RESUME: a one-shot three minutes out to take the next item, armed
BEFORE the turn ends, while queue items and budget remain. Rule 13 in
CLAUDE.md and the daily trigger both carry it.

CONVERSATION IS THE POINT OF THE CHANNEL. A message arriving in the inbox while
a run is going is ANSWERED IN THAT SAME RUN, by the Producer, in the register,
and the bot sends it. A QUESTION SITTING UNANSWERED IS A BLOCKING GAP, not a
queue item.

THE BRIEF'S SHAPE WAS WRONG AND IS RULED: images as Telegram images, never as
links; at most two links and never to a repository markdown file, only the
glance, map or gallery; everything else in plain words; and it LEADS WITH WHERE
THE PROJECT STANDS AND WHAT CHANGED FOR THE GAME, not with what was engineered.
Twenty seconds to read and feel informed. Fifteen links to markdown files is
not a director update.

## 2026-09-06: AN OUTSIDE AUDIT FOUND THREE THINGS OUR GATES CERTIFIED GREEN

A different model family audited this project. Jafar verified all three
findings himself and ruled: TREAT THIS AS EVIDENCE ABOUT OUR PROCESS, NOT AS A
SUGGESTION. Filed as queue 113 to 120. THE ORDER IS HIS, P0 FIRST, and it
outranks the 2026-09-05 order below for everything not already in flight.

P0, STOP THE LINE. Queue 113 and 114. `IntentRouter` takes `check`, `effect`
and a magnitude from model JSON; `Checks.Known("none")` is true; and
`Adjudicator.cs:62` is `case Checks.None: break;`, which falls through to Pass
and CANNOT REFUSE ANYTHING. So the model both proposes an action and picks the
check that would have constrained it, then DialogueUI applies the effect to
real state. THE MODEL IS ADJUDICATING, INSIDE THE LAYER THIS PROJECT IS NAMED
FOR. Re-verified in the code by the resident, not taken on report. Our own
CoreTests case that proves checks CAN fail SKIPS `Checks.None`, so the suite
certified the hole by trimming its denominator to the passing cases.

P1: queue 115, canon says nothing is ever wiped and MemoryStore prunes at 600
under a comment saying that is not forgetting; queue 116, the soak printed NOT
GATED and ran on SEVEN agents while being cited for hundreds.

P2: queue 117 groups the evidence that cannot disagree with us (a self-rating
of 93 cited as a premise in D12, a judge calibrated on 48 passes and ZERO
fails, the split of queue 111, the soak citation); queue 118, a verified piece
whose tone gate is pending.

AHEAD OF ANY REMAINING CONSOLE WORK: queue 119, the cheapest test of the
differentiator. Three unbriefed people, one crime, real propagation against
canned responses. Jafar: "If they cannot perceive a difference, that is the
most important finding this project can produce." It is designed so it CANNOT
come out well by construction, which is the opposite of the 117 group.

QUEUE 120 produces our own cost per verified piece against the audit's, which
puts the stated 300 to 500 resident town at 14 to 34 weeks of full budget for
content alone. THE SCOPE DECISION IS A CARD FOR JAFAR, not a change the studio
makes.

ITEM 6 IS UNFINISHED, NOT SOLVED. The wire moved to 14/14 and the frames
changed, and the street still renders the engine checker with 563 of 593 pieces
assigned. THE CAUSE IS UNKNOWN. Keep it open and find it.

BALANCE, ruled the same day: 63 of 106 queue files were infrastructure and 85
of the last 100 commits touched no game path. Mandatory director review is CUT
for documents and routine assets and KEPT for simulation changes and anything
touching Core. CLAUDE.md carries it.

## JAFAR'S STANDING ORDER, 2026-09-05. THIS REPLACES EVERY EARLIER ORDERING.

Readings taken at about 08:30Z after an EARLY RESET: total 7, Fable 8, ceiling
80 on both, higher governs. No crossing this week. The early reset is a REGIME
CHANGE and every rate computed before it is void, as on 1 September.

TWO STANDING RULES OVER THE WHOLE LIST. After item 4 lands, THE STUDIO STOPS
BUILDING STUDIO THIS WEEK and any new process item goes to the queue and waits.
Every brief reports the STUDIO VERSUS GAME split of points.

JUDGED SUNDAY: if Jafar can run the week from one Telegram thread and know what
is happening, the console is done.

1. **Close the Producer loop over Telegram.** Inbound: anything he sends the
   bot lands as a dated file in an inbox and reaches the session through the PC
   channel, never waiting more than a few minutes. Outbound: the Producer
   answers in the register, the check runs on the SENDING side, the bot sends.
   Rulings: every card arrives with option buttons and a tap writes the ruling
   into `production/decision-queue.md`. Images: every verified visual lands as
   an image with one caption line. Readings he taps reach the repo without him.
   ACCEPTING CASE: he sends a question from his phone and gets a
   register-compliant answer back, and he taps a button and the queue shows the
   ruling.

   088's CONTAINER HALF IS IN. The transport has two named holes until queue
   090's pass: a message sent while the PC bot is OFF is skipped at its next
   start and never filed, and a fresh clone of the PC checkout rewrites
   `pc-inbox` from its own disk. The daily trigger now calls the reader
   (`trig_013itgDeay6t41BHEmaYFbAj`, set 2026-09-05T11:38:02Z, recorded whole
   in `production/watchdog-prompt.md`).

   INBOUND CLAUSE AMENDED PENDING JAFAR'S RULING; the proposed sentence and the
   reason are in
   `game-design/decision-2026-09-05-ruling-standing-order-refill-and-the-wake-half.md`
   section 1.4; queue 092 prices the wake.

1b. **Limit visibility.** When a session or weekly limit is hit, the reset time
   is PARSED FROM THE NOTICE and written to a file the bot reads; the bot says
   "studio paused, back at HH:MM" and again when it resumes. A studio silent
   more than two hours with no reset time on file is flagged as a Blocking
   item. The runner SLEEPS until the parsed reset rather than spawning into a
   closed session.

1e. **Part of 1b, and it starts NOW by hand.** When a limit is hit, arm a
   one-shot trigger for the parsed reset whose instruction is to resume the
   current item and continue this order. From the first limit onward, by hand
   until 1b is built. NO RESET SHOULD EVER NEED JAFAR TO RESTART THE STUDIO.

1c. **The brief is GENERATED FROM REPO STATE BY A TOOL** and pushed by the bot
   every morning. Not written by hand in a session.

1d. **A recurring daily trigger** wakes the studio, plans the day and produces
   the brief. THE HOURLY WATCHDOG STAYS OFF in favour of it. Live as
   `trig_013itgDeay6t41BHEmaYFbAj`, 04:00 UTC daily, which is 06:00 CEST, so
   the brief is on his phone before 07:00. The Monday one-shot that would have
   re-enabled the watchdog was DELETED on 2026-09-05.

2. **Nothing reaches him outside Telegram.** The session's own pop-up questions
   become cards. If something can only be answered on the floor, THAT IS A GAP
   TO FILE, not a reason to page him there.

3. **The glance page, phone-first:** overall state as a colour and one dated
   sentence; needs-you count and top item; next visible thing and when; the
   latest image; the budget bar on both meters. Everything else one tap down.

3b. **The glance publishes to GitHub Pages** so it opens on his phone. IF PAGES
   IS REFUSED FOR ANY REASON, SAY SO rather than leaving a file he cannot read.

4. **Player-facing systems inventory, as DATA not prose.** One entry per
   system: name, area (moat, world, player-facing, content, studio), status
   (exists, partial, absent), class (cheap to author, taste-bound,
   moat-adjacent), phase, and what blocks it. At minimum: the Ledger notebook,
   HUD, menus, controls, camera, first hour and tutorial, save and load, new
   game, settings, accessibility, subtitles, gamepad, pause, map and minimap,
   inventory, economy and trading, combat, music, SFX, audio mix, loading and
   streaming, failure states and autosave policy, time and calendar display,
   graphics settings including the local-LLM toggle, credits and attributions,
   photo mode, feedback path. THEN RENDER IT AS THE MAP VIEW: every system a
   tile, grouped by area, coloured by status, one screen, phone-first, tap a
   tile for status, blocker and decisions. It sits BESIDE the glance, not
   inside it: the glance is today, the map is the whole. Then fold the
   inventory into roadmap-v2 as phases. Research on the taste-bound systems is
   coming separately from the planning session.

5. **A weekly planner role, cheapest tier,** whose only job is the larger plan:
   read the roadmap, the map and the week's landed items, and report whether
   the week MOVED THE PROJECT or MAINTAINED THE STUDIO. External evidence Jafar
   cites: practitioners running long autonomous builds report agents that keep
   working, get absorbed in small details and stop improving the project, and
   the fix is a coordinator holding the plan while others do the work. Our
   resident does both jobs. Flag it when several consecutive items are
   self-maintenance.

6. **Then the game:** 062 step 2, run 21. THE FIRST TEXTURED FRAMES COME TO HIM
   AS IMAGES.

7. **The pilot assembly line,** which Phase 0 requires and the queue does not
   contain. Run ONE content type end to end, spec to author to verify to
   integrate to record, and report THE COST PER VERIFIED PIECE IN POINTS with
   the calibration it rests on. This is the number the whole plan rests on and
   nobody has measured it. The studio chooses the content type and says why.

8. **One supervised trial night this week:** a small queue, the runner
   unattended, and a report in the morning on what it did and what broke. THE
   NIGHT RHYTHM IS UNPROVEN until a night has actually run, and
   `production/logs` is empty.

9. **Then the hygiene queue in filed order.**

10. **Meter readings: NO PRESET BUTTONS.** Ask for the exact number and take it
   as typed, numeric keypad where the platform allows, REJECT anything that is
   not an integer rather than rounding it. Presets are for rulings, never for
   measurements. This overrides the button grid the bot shipped with on
   2026-09-04.

11. **A note, not a task.** A widely-shared 2026 build of an impressive Unreal
   world by an autonomous agent used EXISTING assets including MetaHumans and
   ASSEMBLED rather than authored them. Our bias for bought and free Epic
   ecosystem parts over generated ones is confirmed; the studio's job is
   assembly and logic. Relevant to D1 and D2, NO CHANGE to either.

- **SUPERSEDED BY THE ORDER ABOVE: THE CEILING IS CROSSED, DELIBERATELY, ON ONE ITEM. Read 2026-09-04 at
  about 08:30Z: total 82, Fable 83, ceiling 80.** Jafar chose to spend past the
  line on the Telegram bot alone, so that Monday is a full game day. THIS IS
  HIM SPENDING HIS OWN 20 PERCENT AND IT IS HIS TO SPEND. No session may read
  it as the ceiling having gone soft, and the 80 line binds again the moment
  067 is done or its cap is hit.

  HIS CAP, and it is mechanical: one builder, one director review, STOP at 6
  points spent or at the first failed accepting run on the PC, whichever comes
  first. NO FIX LOOPS BEFORE THE RESET: a broken bot waits for Monday. At least
  8 points stay untouched for Monday morning. Checked rather than accepted: the
  governing meter is Fable at 83, so 17 remain to 100, 6 spent lands at 89 and
  leaves 11, clearing the floor of 8.

  SCOPE CUT BY THE RESIDENT, because 067's six acceptance clauses do not fit in
  6 points. Building: the launcher, the config read, a two-way message, an
  unprompted push, and the budget-reading ask with numeric quick-replies for
  both meters. NOT building, and these stay Monday's: gallery images, decision
  buttons that write rulings, voice memos with local transcription. 067's
  acceptance is therefore NOT fully met by this run and the item stays open.

- **SUPERSEDED, kept for the series: NEAR-STOP AT 3 POINTS, read at 00:30Z.**
  Total 77 percent, Fable 76, ceiling 80, about 84 hours to the Monday
  14:00 CEST reset. The higher meter governs and this time it is the TOTAL,
  which is the reverse of 1 September, so no session may infer one meter from
  the other. The limit Jafar hit on the evening of 3 September was the 5-hour
  SESSION limit; the weekly meter did not reset and the arithmetic in
  `production/budget.md` still stands. One builder spawn is a material
  fraction of what is left. Spend nothing without a fresh reading or a direct
  instruction, and prefer zero-cost work: two of today's findings (queue 078
  and 079) were found by grep and cost nothing.

- **THE DATED HAZARD IS DISCHARGED, 2026-09-04.** It said the tree would go
  red at 2026-09-05T09:01Z by itself, because `producer-check.py` measured the
  committed message's deadline against the wall clock. Queue 077 landed and
  the gate now pins each file's clock to the ISO date in its own name. Proven
  at the exact instant rather than inferred: `--gate --now 2026-09-05T09:01`
  reads `PASS filesChecked=1 filesExempt=5 filesWalked=6 filesDatePinned=1/1`,
  the same verdict it gives today and in 2027. Ruled in
  `game-design/decision-2026-09-04-ruling-077-deadline-clock-pin.md`. The
  residue is queue 080: a date is a day, not an instant, and nothing in the
  tree proves the pre-send check ever ran.

- **LANDED 2026-09-03, one commit, ruled in
  `game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md`:**
  the register gate (walks the outbox and the briefs on every verify; its
  accepting artifact is now the served message read at THREE clocks in one run,
  `--gate`, `--now 2026-09-08T12:00` and `--now 2027-06-01T12:00`, all PASS at
  `filesDatePinned=1/1`; the single reading of 3 September was accepting at one
  instant only, ruling of 4 September section 4), the banner law (135 documents
  migrated,
  the retired form refused), the spawn log's tier and turn fields (hook
  REGISTERED, first row NOT YET READ: read it before quoting it), and the UV
  head sweep (nine candidate pin names in one run, not yet dispatched). Open
  holes are queue 073, 074, 075 and the steps added to 024 and 062.

- **THE UNREAL STOP RULE IS DISCHARGED, RUN 21 LANDED 2026-09-05.**
  `materialConnections=14/14`, up from the 12/14 that held across runs 19 and
  20, taken by the FIRST of nine candidate pin names
  (`materialUvHeadTriedAtWorst=1/9`) with `materialUvHeadByPropertyWrite=0/2`,
  so `materialStatus=MADE` is honest and the third status word did not fire.
  THE FRAMES CONFIRM IT INDEPENDENTLY: the flat grey of the last two runs is
  gone and a checkerboard tiles correctly in perspective, which a count cannot
  fake.

  THE STREET IS STILL NOT MERIDIAN AND THE CAUSE IS UNKNOWN. Staging RAN
  (`stagedTexFiles=102/102 piecesTextured=563/593` in
  `ue-vignette-verdict.txt`), so the frames show the engine checker on
  surfaces the verdict says were assigned, which is an UNNAMED fault and the
  next thing to find. The resident first blamed the staging step, having
  grepped `ue-build.txt`, a file that has never carried those keys; the
  correction and both refuted claims are in queue 062. Do not re-derive the
  wrong answer from the old sentence.

- **THE DIRECTOR'S CONSOLE EXISTS AS FAR AS STEP 2.** `production/decision-queue.md`
  is the single home for anything awaiting Jafar and for lighter rulings; the
  legacy `game-design/decisions-pending.md` is RETIRED and carries a pointer.
  The Producer is the only role permitted to address him (CLAUDE.md, and
  `.claude/agents/producer.md` carries the register). Constitution law 12 sets
  evidence beside the sentence for agents and behind it for Jafar, with the
  link REQUIRED rather than optional.

- **THE REGISTER CHECK IS REAL AND IT REFUSED THE RESIDENT FOUR TIMES.** The
  first live Producer message failed on missing options, a missing deadline and
  twice on length before it passed. Pointing at the card instead of restating
  its options is exactly the vagueness a word cap alone teaches, which is why
  the link and the options are floors rather than suggestions.

- **BUDGET: TWO METERS NOW, AND THE HIGHER GOVERNS.** Total was 60 percent at
  10:25Z; Fable was not read. On the only day both were read, 1 September,
  Fable was 41 against a total of 34. Directors run on Fable, builders do not,
  so the meter that moves on reviews is the one this file used to be blind to.
  A row where Fable was not read says `not read`, never zero and never the
  total carried across.

- NOT DISPATCHED AND DELIBERATELY: `production/d1-probe/DISPATCH` is a push
  trigger. Do not touch it in a commit unless an Unreal run is wanted, and the
  stop rule says one is not wanted until 062 lands.

- **DO NOT COMMIT WHILE A BUILDER IS WRITING**, however loudly a stop hook
  asks. That is CLAUDE.md's rule and it exists because the resident once ran a
  checkout over a builder's uncommitted work and cost a whole session.

## THE DASHBOARD IS NOW A HOSTED LIVE PAGE, and it needs writing to

Published 2026-09-02 after Jafar refused to double-click anything to see
current state, in his words: "not running a bat to update a dashboard. your
job is to keep it up to date all the time, that's the whole point."

    https://claude.ai/code/artifact/2c3da7c0-8b8e-4626-8e73-2498acbe6ed8

It holds NO numbers of its own. It subscribes to the artifact document store
at `status/current` and repaints when the document is written. So:

    python3 tools/dashboard/build-dashboard.py --emit-json
    then write tools/dashboard/live-dashboard.json to status/current

WRITE IT AFTER EVERY LANDING. The page reports the age of its numbers and
turns red when the feed stops, which is honest, but a red feed is still a
reader learning nothing. The writer is the resident and nothing automates it
yet: queue 048. Republishing the PAGE is not needed and should not be done
casually; the page changes only when the generator's renderer changes.

The wake subscription on it did NOT register in this session (the artifact
service refuses them here), so nothing tells this session when it is
republished. Do not claim to be watching it.

## THE IMAGE QA, 45 of 45 OPENED, and the answer is a number

Jafar, 2 Sep: "did you view and QA the images and fix/redo if necessary? are
they built and cropped and shaped in a way that they can be used in UE? QA
should be standard procedure." The resident had opened THREE of forty-five
and published the rest. A verifier then opened all 45, plus 18 zoomed crops,
and confirmed the files are byte-identical to the blobs at HEAD, so the
judgements apply to what the engine will load.

    41 of 45 are SCENE PHOTOGRAPHS, 4 of 45 are plates
     1 of 45 usable as is, and it is probe_wall_cfg1, measurement only
    29 of 45 croppable
    15 of 45 need regenerating
     0 of 45 carry a real brand, real person or recognisable face
    12 of 45 carry people or vehicles the negative prompt already bans
     1 more, sign_telephone, is close to GPO kiosk trade dress: a WATCH ITEM
       for a decision record, not a proven breach, and not a builder's call

THE CAUSE IS ONE LINE OF PROMPT, not 45 problems. Sign, fascia, notice and
poster families carry "photograph, straight-on flat elevation, evenly lit"
plus "deserted empty street", which asks for an object standing in a street
and gets one. The four that came out as plates used a prefix ALREADY IN THAT
FILE: "flat orthographic texture sheet, square-on to the surface, the surface
filling the frame edge to edge", with a negative list naming kerb, pavement,
road, sky and roofline. Four of four. Queue 056 moves the rest onto it and
makes the generator REFUSE a prompt with no framing clause.

TWO MORE SHARED CAUSES. All three interiors came back as exterior shopfronts
when they are meant to be cards seen from inside a window. Prominent
SECONDARY text resolves as broken near-words in eight images, against the R1
big-type-only rule already written in that file: HOOK STREATS, HARBOOR
MASTER, BORHOUGH, PORIE SHUOP.

A CLAIM THE RESIDENT PUBLISHED AND HAD TO WITHDRAW: the gallery page said
headlines come out clean and correctly spelled, written after opening three
images. It is corrected on the live page. And the verifier withdrew one of
its own: it read two signs as perspective-distorted, measured the edge slopes
at 0.27 and 0.07 degrees, and refuted itself. Faces are square-on across the
batch to within half a degree; what reads as perspective is a baked 3D lip on
the surrounding frame.

## THE NIGHT'S DISPATCH ORDER, and why it is this way round

`ledger-pc` is ONE machine, so two dispatches contend and the order is a
decision rather than a detail. It is:

1. **UE probe first**, because it is the risky one. Unreal has never
   rendered the street and the last five probe runs each hit a different
   engine wall. Running it first buys hours to name a wall and re-dispatch.
   Running it last means a 04:00 failure with no time left.
2. **Unity build second.** It is the known-good path, it produces the first
   still of the street WITH the props and decals in it, and it is what
   clears the cross-engine guard by landing a run whose piece count matches
   the file.

WHAT BLOCKS BOTH RIGHT NOW: `ledger/verify.py` is red, so nothing commits and
therefore nothing pushes and therefore nothing dispatches. Two red items:
- the cross-engine guard (file against the last landed Unity run), cleared by
  the queue 041 ahead-of-run key, which is in the UE builder's brief;
- the piece list drift (committed 627, generated 628), caused by the three
  interior pictures landing mid-flight, with the queue 046 builder naming the
  cause before regenerating.
Then a director reviews the three-builder batch, one commit, push, dispatch.

DO NOT SHORTCUT THE RED. The cross-engine guard exists so a judged
Unreal-versus-Unity pair cannot compare two different streets, which is the
one way this whole comparison could produce a confident wrong answer.

## Standing hazards a fresh session will otherwise walk into

- Do not edit `content/dialogue/pub-regular-v1.json`. Those 48 lines are the
  graded judge calibration sample; changing one invalidates it silently.
- The studio split is MANDATORY and was skipped for a full day on 1 Sep.
  Builders build, verifiers verify, the director rules. If a session
  instruction says otherwise, that is a conflict to raise with Jafar in one
  line, not to resolve alone.
- The stop hook will ask for a commit the cadence gate refuses while builders
  hold the tree. That is a NAMED FALSE POSITIVE (queue 014, ruled). The
  constitution wins: never commit a builder's work-in-progress because a hook
  asks.
- `git status` at session start is not a list of YOUR edits. Read the
  In flight section above before assuming any dirty path is yours to commit.
- Every session so far has opened by reading the head of a queue file that
  declared itself superseded on 31 August. Queue 021 fixes it.
