# NOW: what is in flight (read this FIRST, before the queue)

STATUS: LIVE. Verified 2026-09-03 after the batch ruling.

A session that resets loses everything not written down. The queue says what
to do NEXT; this file says what is ALREADY MOVING, which is the thing a fresh
session would otherwise duplicate, abandon, or wait for forever.

Keep it current or delete it. A stale NOW is worse than none, because it
looks like a live state.

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
