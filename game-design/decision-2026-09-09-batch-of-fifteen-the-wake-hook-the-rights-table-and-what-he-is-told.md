# Ruling: the batch of fifteen, the Stop hook that fails open, the rights table that withholds, and what Jafar is told tonight

STATUS: LOG, 2026-09-09. NOT CURRENT once the commit lands and the blocking
amendments in section 8 are applied; from then the files are the reading copies
and this is the record of why. Director batch review on spawn
`2026-09-09T08:04:25Z`, the same spawn as the morning's two guard rulings
(`decision-2026-09-09-the-hook-comparison-the-ruled-link-and-the-stale-pages.md`),
read-only, no shell. The coordinator is right that `--cadence` reading REVIEWED
off that record is attendance and not review: it rules on the Hook comparison,
the link and the pages, and on nothing else in the 11760 lines. This record is
the review of the rest.

VERDICT: LAND WITH AMENDMENTS. Two are BLOCKING and both are text (section 8,
B1 and B2); the rest are one-line rows and queue items. The wake hook stays in
the batch. The rights table stands as written. Nothing in the batch moves a
gate to make red go away, and the one gate that went from red to green
(`gallery.py`'s accepting case) did so by changing what the page IS, not what
the cap is.

## 0. What was read, what was taken on report

NOTHING WAS RUN. Every count in the coordinator's brief (41 to 87, 10 to 30,
82 to 99, 48 to 79, 143 to 144, 77 to 92, 24/1 to 25/0) is a builder's or the
resident's, printed once by hand, and section 6 is about what makes them print
again. Read at the line this session: `.claude/hooks/wake-drain.sh` in full;
`tools/wake-queue.py` 1 to 1103 and the 78 selftest labels at 1065 to 1334;
`.claude/settings.json` in full; `tools/gallery.py` 1 to 60, 255 to 440 and
950 to 959; `ledger-v2/research/license-allowlist.md` in full;
`.github/workflows/publish-glance.yml` 119 to 128 and 166 to 189;
`tools/runner/cards.py` 170 to 209, 440 to 480 and 662 to 707;
`tools/producer-check.py` 34 to 36, 222 to 265, 472 to 478, 499 to 552 and
the selftest at 1280 to 1539; `tools/imagegen/imagegen.py` 822 to 873, 2986
to 3051, 4424 and 4582 to 4638; `ledger/verify.py` 1177 to 1203 and 1433 to
1474; `tools/road-brightness.py` 1 to 77; `tools/art-recipes/mickeys-blockout.py`
1 to 60; `tools/morning-brief.py` 935 to 955; `tools/runner/executor.py` 897;
`production/ladder.md`; `production/queue/180`; `production/findings.txt`
2100 to 2134 and 2170 to 2202; `production/NOW.md` 127 to 177; today's two
outbox files and the brief; the one receipt under `production/outbound/`
dated today.

NOT READ: the C++ bodies behind the new camera and the control-quad rule
(`VignetteShot.cpp`, `WalkProbe.cpp`); I read the header declaration at
`VignetteShot.h` 111 to 117 and the findings entry that describes the
measurement. `production/d1-probe/DISPATCH` was not opened today, so whether
this push fires an Unreal run is the 04:51 ruling's reading, not mine.

PREMISE CHECK, CLAUDE.md section 0: a late-analog British port street, its
grate, its kerb, a pub, a period atlas. Nothing purchased. The one licence
question in the batch (section 2) is answered by withholding, which is the
allowlist's own default.

## 1. A. The Stop hook: the failure mode is right, and one session it will hit was not modelled

RULED: KEEP IT IN THE BATCH.

WHAT I CHECKED, at the line. The hook blocks on exactly one exit code (10, at
`wake-drain.sh` 127 to 130) and permits on 0, 2, 11, 12, 13, 14 and on every
unmodelled code with the words PERMIT-UNASSESSED (131 to 145). A missing tool
permits and says so (108 to 113). The drain reads the payload in the tested
layer, not in a fourth bash JSON parser (115 to 123). `stop_hook_active` is
honoured at `wake-queue.py` 734 to 744 with no increment and no stamp. The cap
is per record, cumulative, written into the record (746 to 771), and the
accepting case runs the hook AS the hook through bash with the real payload on
stdin (1024 to 1034). The live `settings.json` is the accepting fixture for
registration (1308 to 1316) and `TOOL_SELFTESTS` has the row (`verify.py`
1198), so a deleted registration turns verify red. A usage error exits 64 and
never 2 (218), which is the fault the first run of the suite found. That is
the right shape, both directions watched, accepting first, and the
instruments rules kept.

ONE CORRECTION TO THE BUILDER'S OWN ACCOUNT, so nobody later reads the cap as
the bound. After a block, the very next Stop carries `stop_hook_active=true`
and the drain PERMITS (exit 13). So within one chain the hook blocks ONCE. The
cap of 3 is reached across three separate chains (three turns or three wakes),
not three consecutive stops. That is MORE conservative than the docstring's
"bites first" framing, and it is the statistic the series must be read as:
`blocksBeforeDischarge` counts chains that found the record due. On the PC the
counter does not persist at all, because pc-watcher hard-resets the root
checkout about once a minute (NOW.md 295 to 296); the per-chain flag bounds it
there anyway.

THE SESSION NOBODY MODELLED. The records are tracked under `production/wakes/`
and `settings.json` travels with the repository, so EVERY session in EVERY
checkout drains the same records. `tools/runner/executor.py` runs
`claude -p <prompt> --max-turns N` (line 897) in an isolated worktree to answer
a question Jafar sent from his phone. If the container's daily-brief record is
due and undischarged at that moment, which is the normal state for hours after
an absorbed 04:09 wake, the executor's first Stop is BLOCKED and the model
answering his question is told to produce the day's brief instead. Bounded:
one block, sixty turns. Wrong: the wrong session does the wrong work and the
answer to him may be delayed or bent. The executor has never run (NOW.md 288,
zero inbound messages), so this is latent, not live, and it is not a reason to
pull the hook. It is a reason for the amendment in section 8, A1: an opt-out
the hook honours and prints, set by the executor for its own invocations,
tested both ways, and ARMED WITH THE WAKE QUEUE ITSELF so the mechanism proves
itself on its first real record.

Whether Stop fires at all under `claude -p` is read off the binary the way the
cap was, not remembered; the amendment says so.

THE PRICE, accepted and named: a block writes `blocks` into a tracked file,
the tree is one file dirtier, and `verify-gate.sh` wants a re-run before the
next commit. That only happens at a boundary where a wake was genuinely due.

## 2. B. The rights table: withhold stands, and the hole is in the pattern, not the default

RULED: PUBLISH AS THE TABLE STANDS. 43 cleared of 62 examined, 19 withheld, 0
unclassified is the correct reading of the allowlist.

WHAT I CHECKED. The allowlist's six SHIP-SAFE items are voices, 3D,
characters, faces, music and geodata; there is no 2D-image entry; PROCESS 1
says an untagged output fails the licence gate and PROCESS 2 says a new tool
needs a decision record. `gallery.py` 268 to 277 reads it the same way and
withholds `concepts/*` on that ground (292 to 296). `references/*` and the two
previews that embed reference photographs are withheld on `RIGHTS.md`'s own
words (279 to 291). The cleared rows are original authored coordinates
rasterised here, SVG studies rasterised here, a screenshot of the package's
own HTML, plans drawn from the pub's own JSON, a layout proof in system fonts
whose condition is on the texture and not the proof, and projections of the
CC0-1.0 base meshes the allowlist names under item 2. `rights_of` is first
match wins with default withhold (379 to 388), the world page prints the ref
and sha it read (1195), and a planted withheld file on the page is refused by
the leak check (1042 to 1061). The workflow fetches the art branch by name and
prints whether it came (publish-glance.yml 174 to 189), so the CI reading is
the same as the container's. Sound.

THE HOLE, named rather than papered: the clearing rows clear by NAME PATTERN
against a MOVING ref. "Read at 8ce8173" (264) is a comment; `atlas_ref`
resolves `origin/art/atlas-01` at run time (370 to 376). Default-withhold
catches a file no pattern names. It does not catch a file a later art commit
adds under a name a clearing pattern already matches, `previews/mesh-photo.png`
say, which would publish without anyone looking. Amendment A3: the exact
cleared names at 8ce8173 become data in the tool, and a file that matches a
clearing pattern but is absent from that list is withheld and printed as new
since the table. Non-blocking today provided the resident prints `atlasSha`
and it reads 8ce8173; if it does not, the resident prints the image names
added since and says so in the commit message before the publish fires.

THE CONCEPT BOARDS are a card and a research task, not a table change: whether
output of the OpenAI image service, on whose account, under whose terms as of
the date, may ship as 2D art. That is a decision record under the allowlist's
PROCESS 2 and Jafar's call. Sending Codex's `hook.png` to him by Telegram for
the comparison is review of his own commission's deliverable, not publication,
and needs nothing.

## 3. C. The camera: a composition match is the honest target, and the caveat he needs is a different one

RULED: HONEST ENOUGH, and the caption does NOT carry the field-of-view caveat.
It carries a different one.

WHY THE FOV CAVEAT STAYS IN THE STUDIO. The reference is a drawing. Its right
kerb departs from straight by 21.7 px at worst over 112 columns (findings 2196
to 2199), so no camera matrix exists to derive and "same viewpoint" can only
ever mean the same composition: vanishing point, eye height, kerb line. The one
free parameter is pinned by the 6.0 m bay, and that is not a new assumption
about Codex's drawing, it is THE STREET'S OWN SPEC (`vignette-scene.json` 104,
"judgement on 6 bays at 6.0 m"), applied to the panel. The alternatives are
printed (45 degrees at 5.0 m, 37 at 6.5 m) where a builder will read them. A
degree of vertical field is not something Jafar can act on, and the register
bans the sentence anyway. It belongs in the verdict and in queue 180.

THE CAVEAT HE DOES NEED, per queue 180's own rule ("a thing the panel has and
the street lacks is NAMED"): `Wetness` reaches nothing in this engine (findings
2172 to 2178, three hits, all declarations), and the street has no sky (2114).
The panel is lit BY its sky and its lower half is sky reflected in standing
water. So the first frame at this camera is THE DRY STREET FROM THE SHEET'S
VIEWPOINT WITH NO SKY, and the caption says exactly that in plain words, or the
comparison he is asked to make is rigged the other way. It is not today's
message: no dispatch has run and the frame does not exist.

WHAT THE INSTRUMENT ALSO SETTLED, and it moves rung 1: `road-brightness.py`
on the committed frames printed `roadCause=MATERIAL-ALBEDO` (findings 2119 to
2131): the pale band is the kerb texture (`kerb.jpg` mean 0.7228 against
`asphalt.jpg` 0.2659, rendered over source 0.83, clipHi 0 of 42000 in both
bands). Rule 4 is satisfied in the right order: the number came before the
material was touched, and a kerb texture change is now a justified next step,
not a guess. The control-quad rule (a swatch at column 1274 of 1280 in the new
frame, findings 2180 to 2186) is right and is the kind of thing the instrument
exists to catch; I accept the builder's "tested both ways plus the empty case"
on the CI compile, having read only the declaration.

## 4. D. What he is told: both halves in the headline, the landed half first

RULED. The headline is one sentence and it carries both: what he can now see,
then the two pictures he asked for that are not made. He ordered the visual
half fixed BEFORE any new game rung; a headline that leads with the pages and
buries the pictures in WHAT CHANGED is the tidy-story fault the coordinator
named in his own three refuted claims, one message later. Substance for the
Producer, who keeps the register:

    HEADLINE: Your cards and pages are rebuilt and on their way; the two
    pictures you asked for, the Hook sheet and Mickey's, are not made yet.
    WHAT CHANGED: Every card now comes as its own message with buttons. The
    pages show every picture, newest first, and the map opens on your ladder.
    The Hook file you named was a correction note for a board that already
    existed, so ours will be drawn from the description behind that board;
    Mickey's five views are written and the render has not been run.
    NEEDS YOU: the cards, each in its own message.
    NEXT VISIBLE THING: Mickey's five previews when the render runs; when,
    unknown. The Hook pair: unknown.
    BUDGET: nothing bought.

TWO CONDITIONS ON SENDING IT. It goes AFTER `tools/publish-glance.py --check`
on the three URLs (C1 of the morning ruling) and its pages sentence follows
that reading: "rebuilt and on their way" if a run has reached the deploy,
"rebuilt; the old pages are still the ones you can open" if not. And the four
cards go as their own messages under his item 1, which the cards pass does; the
digest's NEEDS YOU points at them and does not repeat them.

## 5. What else the batch carries, read rather than reported

(a) THE GRATE MESSAGE IN THE OUTBOX IS UNSENT AND ITS HEADLINE IS THE REFUTED
WORD. `production/outbox/2026-09-09-the-grate-readable.unprompted.md` has no
receipt under `production/outbound/` (only the brief has one), so it has not
gone. Its body is honest ("renders near-white and almost flat, so it reads as
a shape and not as metal"). Its headline says "readable". He reads the
headline. And the batch widens `ledger-install-supervisor-task.yml` to fire on
`production/outbox/**` (79 to 86), so this commit's push runs the sweep that
sends it. BLOCKING, B1 in section 8, dictated text.

(b) THE CARD LINK IS ONE THE REGISTER WOULD REFUSE, and nothing checks it.
`card_link` (cards.py 461 to 465) builds `<origin>index.html#card-<id>`.
`norm_url` drops the fragment (producer-check.py 472 to 478) and `site_page`
then compares `index.html` against `""`, `map.html`, `gallery.html`,
`world.html`: no match, `link_ok` False. Today that does not bite only because
`send_cards` (662 to 707) hands the text to `sender` directly and never calls
the check; grep of `cards.py` for `run_check`, `producer-check` and `link_ok`
finds comments and the SITE_ORIGIN assertion (1592 to 1596) and no call. So a
Jafar-facing message class sits outside the gate Jafar ruled on 2026-09-03,
and if it were inside it, its one link would fail. Two fixes: A2, one tuple
entry so the glance's own filename is the glance; and a queue item for a
`card` register in `producer-check` that the cards pass calls, with the rules
that fit a card he dictated the shape of (banned minus counts, linkcap,
linkdest, the six fields present). Non-blocking, because his item 1 dictated
the shape and the message carries its payload in full.

(c) THE COUNTS THE BATCH REPORTS RUN NOWHERE AT COMMIT. `TOOL_SELFTESTS`
(verify.py 1177 to 1199) has seven rows. `cards.py` (87), `gallery.py` (30),
`map.py` (99), `glance.py` (79), `road-brightness.py` (14), `morning-brief.py`
and `producer-check.py --selftest` (92; only `--gate` runs at commit, 1458)
have none. The 2026-09-06 ruling's item 7D asked for three of these and the
batch added one row, for the wake queue. Section 6.

(d) `--spec` LANDED AS DICTATED (B1 of the morning): `spec_file` (822 to
825), the missing-spec refusal with nothing measured and its own exit (869 to
873), `--selftest --spec` (2988 to 2990), the spec line in the report (4638).
The sentinel's `spec=` and `out=` keys I did not read; the resident prints
`--batch-settings` on the sentinel before any push. B2 (the compare spec) is
NOT in the batch and B3 (the media group) is not in the batch, so item 4(a) is
three builder turns away and the message in section 4 says so in his words.

(e) `RULED_LINKS` LANDED AS DICTATED: whole-string equality after the shared
`norm_url` (499 to 511), the generation suffix only on a match (539 to 552),
`linksRuledUsed` on the gate, the digest as the accepting fixture (1280 to
1302), the five rejecting shapes named at 507, `world.html` in `SITE_PAGES`
with the comment citing item 2 (222 to 230), and the deletion rung filed as
queue 184 (249 to 252). Accepted.

(f) THE STALE SENTENCE SURVIVES IN ONE COMMENT. `morning-brief.py` 940 to 945
says "the published pages have never served a byte". The code under it is
right for the stale case too (it promises no page), so this is a comment fix:
A5. `decision-queue.md` 305 and `findings.txt` 1800 already carry the
correction; `queue/139` line 28 is the original finding under a DONE status
and stays.

(g) NOW.md 127 is still headed "READABLE AS IRONWORK" over an entry whose own
last paragraph (148 to 151) says it reads as a shape and not as metal. The
entry is a LOG and the correction is in it, which is the ruled shape; the
heading gains four words so a reader scanning headings is not misled: A6.

(h) The widened `paths:` is inside rule 9: the job queues rather than races
(line 91), it is the cheap PC sweep and not a build, and receipts are written
under `production/outbound/`, not `outbox/`, so the sweep's own commits do not
refire it.

(i) `ue-probe/**`, `ledger/CoreTests` and `vignette-spec-test.cpp` compile
only in CI; this push fires core-tests on ubuntu, which is cheap and proves the
count assertions. The frame needs a dispatch this push does not fire.

## 6. Rows, so the numbers print again

RULED, and it is blocking for every tool that prints green in the container:
the resident runs `--selftest` by hand on `cards.py`, `gallery.py`, `map.py`,
`glance.py`, `road-brightness.py`, `producer-check.py` and `morning-brief.py`,
quotes each count line in the commit message, and adds a `TOOL_SELFTESTS` row
for each that printed `N passed, 0 failed`. A tool that is red in the container
for an environment reason (a missing module, a git ref the container lacks)
gets NO row today and a queue item carrying the printed line, because a row
that is red at every commit is a footer nobody can earn. The helper parses one
shape (1203); a tool that prints another shape is a finding, not a reason to
widen the regex.

## 7. The ladder, asked at close

Pages: BEST AVAILABLE for the text and the count (pictures as files, 15842
bytes against a 250000 cap the glance derived); next rung unchanged from the
2026-09-06 ruling's 7C, the served-page verdict as a committed file, still
open, and C2 of the morning ruling prints its age beside the register. Cards:
FIRST WORKING; next rung is the `card` register in 5(b). Wakes: FIRST WORKING;
next rungs are A1 and a read `blocksBeforeDischarge` series. Rung 1: the
camera is built and unrun; next rung is the dispatch, the kerb texture with
its number, and the wetness that reaches something. The rights table: BEST
AVAILABLE under today's allowlist; next rung is A3 and the concept-board card.

## 8. Amendments

B1, BLOCKING, resident, dictated text, before the commit. In
`production/outbox/2026-09-09-the-grate-readable.unprompted.md` line 1
becomes:

    HEADLINE: The grate is in the picture with nothing across it, and it
    looks like pale plastic, not iron.

Body unchanged. Then `python3 tools/producer-check.py` on the file, printed.

B2, BLOCKING, resident. The message in section 4 is written by the Producer to
the outbox under today's date AFTER the publish `--check` has printed, with its
pages sentence following the reading, and `--gate` is printed before the
commit that carries it.

A1, builder, non-blocking for the commit and BLOCKING before the executor's
first run. `wake-drain.sh` honours `WAKE_DRAIN=off`: PERMIT, exit 0, one stdout
line `wake-drain: PERMIT reason=opted-out dueOnDisk=N/M` so the opt-out is
never silent. `executor.py` sets it in the environment of its `claude -p`
invocation (line 897) and prints that it did on the journal line. Selftest,
accepting first: opted out with a due record on disk permits and prints the
count; not opted out with the same record blocks. Whether Stop fires under
`claude -p` is read off the binary and quoted in the docstring beside the cap.
THEN ARM IT: `python3 tools/wake-queue.py arm --due 2026-09-09T16:00Z --by
director/2026-09-09-batch-ruling --instruction "Land A1 of the batch ruling
(the WAKE_DRAIN opt-out) before Jafar's evening; discharge when the executor
journal prints the opted-out line"`. That record is the mechanism's first real
one, and the next boundary that finds it due is the proof his item 3 asked for.

A2, builder, one line plus one selftest line. `SITE_PAGES` gains
`("index.html", "the-glance")`: `publish-glance.py` publishes `index.html` and
`glance.html` for the one generator (`PAGES` 120), so the glance under its own
filename is the glance. Selftest: `site_page(SITE_ORIGIN + "index.html#card-x")
== "the-glance"`.

A3, queue item, named: "the rights table clears by pattern against a moving
ref". Exact cleared names at 8ce8173 as data; a pattern match absent from the
list is withheld and printed as new since the table; the world page says the
count. Today the resident prints `atlasSha` and confirms 8ce8173.

A4, queue item and card: "may the concept boards ship". CLASS: DECISION, for
Jafar, drafted by the Producer after a builder reads the service's terms as of
the date and records whose account made them. Options: A withhold from the
site and use as reference only; B ship under a decision record naming the
terms; C regenerate in house once the Hook comparison rules. RECOMMENDATION A
until B's record exists. DEFAULT A. DEADLINE no shorter than 2026-09-11 09:00.

A5, resident, comment only, `morning-brief.py` 940 to 945: "the published
pages have never served a byte" becomes "the served pages are stale: the last
deploy known to have answered as ours is 2026-09-07, and eight runs failed
before the deploy step on the morning of 2026-09-09".

A6, resident, NOW.md 127: append " (CORRECTED BELOW: IT RENDERS NEAR-WHITE)"
to the heading.

A7, queue item, named: "the card message is outside the register gate". The
`card` register in `producer-check`, called by the cards pass, per 5(b).

A8, queue item, named: rows refused in section 6, if any, each with its
printed line.

PRE-COMMIT, mechanical: B1 applied and its check printed; section 6 count
lines quoted; A2 applied; `atlasSha` printed; `--batch-settings` on the
imagegen sentinel printed; `python3 ledger/verify.py`, footer from
`ledger/.verify-footer`. Then the push, which fires publish-glance, the PC
sweep and core-tests, and nothing else the 04:51 ruling did not already name.
Then C1's three `--check` lines, then B2.

## 9. What this spawn did not get to

The C++ bodies behind the camera and the control-quad rule are unread. The
wake queue's selftest from line 1104 on is known to me by its labels only. I
did not verify that the seven tools in section 6 print the `N passed, M
failed` shape; the resident's hand runs settle it. And I have not seen a
served page today: everything about the pages in this record is about bytes
in the tree.

<!--RULING spawn=2026-09-09T08:04:25Z-->
