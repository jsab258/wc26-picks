<!--RULING spawn=2026-09-10T06:30:10Z-->
# LOG: ruling on the four-lane batch, 2026-09-10

> **STATUS: LOG, 2026-09-10. NOT CURRENT** once the conditions in
> section 7 are met and the batch is committed. Decision record.
> Binding on the resident for this commit.
Author: tier-1 director spawned 2026-09-10T06:30:10Z (row 503 of
`.claude/agent-log.tsv`, read this session: the row reads
`2026-09-10T06:30:10Z` TAB `studio-director`).

Scope: four lanes, 2831 changed lines, reported at a clean boundary by four
builders. Five questions put to me, plus the print-before-commit conditions.

## 0. What I verified and what I did not

Written from the builders' reports. Every count, every measured value and
every "all green" below is ON THE BUILDER'S REPORT, UNVERIFIED BY ME unless
a line in this section says otherwise. I have no shell in this spawn: I cannot
run the suites and cannot open the stills. That is why section 7 exists. The
conditions ARE the verification, deferred to the resident and made printable.
A count in this ruling is a CLAIM TO BE CHECKED, not a finding. If a printed
number differs from the number recorded here, the commit is blocked until the
difference is written into this file.

What I verified personally this session, by reading the files:
1. `game-design/decision-2026-09-09-ruling-the-grid-batch-review.md` exists,
   carries `<!--RULING spawn=2026-09-09T21:28:40Z-->` at line 627, and states
   the seven-frame finding at line 29 ("THE FINDING THAT OUTRANKS THE REST OF
   THIS FILE") and at line 543 (C4). Amendment 1 has a real target and the
   sentence it corrects is really there.
2. The nine-group claim is TRUE and I did not take it on trust.
   `ue-probe/tests/vignette-spec-test.cpp` line 548 carries vign_camA_day's
   own fields: `"cam_A", "overcast_day", 1.5723, "east_footway"`. So
   vign_camA_day does carry overcast_day, exactly as the builder said, and by
   applied fields alone it would join the group.
3. The correction is implemented as described.
   `ue-probe/Source/LedgerProbe/Public/VignetteSpec.h` line 2522, `SampleKey`,
   prefixes `cam.<CameraId>` to the applied fields; the comment at 2513 to
   2521 states the nine-versus-seven reading; and the group is DISCOVERED by
   scanning for the largest shared fingerprint (lines 2562 to 2584), not
   hardcoded. The header's own words: "Seven is a reading, never a constant."
4. The test asserts the seven BY NAME, which is what I was about to demand.
   vignette-spec-test.cpp lines 2599 to 2608 assert
   `nullSeriesSamples=7/of=25/` and `nullSeriesMeasured=25/of=25/` and the id
   string `vign_hook_day;vign_grid_sky100_sun003;vign_fog_maxop0450;
   vign_wet_000;vign_wet_060;vign_wet_100;vign_grid_null_repeat` in shot
   order. The emit names its statistic (`spread-is-max-minus-min-over-the-
   group`), ships denominators, announces its id cap as
   `/+N-more-not-shown`, prints `nothing-measured` on an empty run, and a
   planted loud-noise fixture is asserted to produce
   `nullSeriesVerdict=NO-READ`. This is the standard the rest of the batch
   should be held to.
5. ONE FAULT I FOUND MYSELF, in lane 1, unasserted by anyone. Section 9.

Premise check against CLAUDE.md section 0: none of the four lanes contradicts
the premise. Meridian is late-analog, 1988 to 1992, and the moat is social
memory, consequence persistence and information. Lanes 1 and 4 are
instruments and geometry, lane 2 is the studio's own channel, lane 3 is the
only lane touching world content and `canon.md` outranks it. Condition 11
makes the resident print the canon check rather than assert it.

## 1. The batch: APPROVED WITH AMENDMENTS

Approved with the five amendments in section 2 and conditional on every item
in section 7 being PRINTED before the commit. Not approved as landed, not
approved as verified.

Why not a plain approval. Three of the four lanes overturned something they
were built on top of: lane 1 corrected the ruling that authorised it, lane 2
overturned a standing fact about every brief receipt ever written, lane 3
disclosed a contamination that I introduced. A batch that corrects its own
authority is the good case, not the bad one, but the corrections have to land
in the RECORD and not only in the code, or the next session reads the stale
authority and re-derives the error. That is what the amendments are for.

Why not a refusal. Nothing here weakens an instrument. Lane 1 NARROWS a
group from nine to seven, which tightens a noise floor. Lane 4 SPLITS a
bucket and in the same change surfaces two real faults of 370 mm and 810 mm
that the old predicate hid. Lane 2 replaces a swallowed exception with a
measured latency. Each of those moves in the direction a gate is supposed to
move. A refusal would be a refusal of the corrections, which is the one thing
I will not do.

## 2. Amendments, exact text

Apply verbatim. Do not paraphrase.

**Amendment 1, to `game-design/decision-2026-09-09-ruling-the-grid-batch-review.md`.**
Append, under a heading `## CORRECTION 2026-09-10`:

> CORRECTION 2026-09-10. The sentence in this record stating that seven
> frames share identical rendering inputs was wrong as written. By applied
> fields alone the largest identical group is NINE, because vign_camA_day and
> vign_camB_day also carry overcast_day: their applied fields match and their
> pictures do not. Camera id is a rendering input. The null-spread fingerprint
> now includes the camera id and the test asserts seven of twenty-five, named
> individually. A spread computed over the nine would have reported a CAMERA
> difference as a noise floor, which is the failure mode this record exists to
> prevent. The correction is upheld by the director's ruling of 2026-09-10;
> this record remains the authority for everything else in it.

**Amendment 2, to the Fairview sheet (lane 3), in its first lines.**

> DRAFT. Originality UNPROVEN. This sheet was authored with third-party
> prompt text in view: the pass-2 file it was told to copy its shape from
> embeds that prompt verbatim in its source block, and the instruction to use
> that file came from the director, not the author. The verbatim substring
> test reports 0 of 48 rows failing; that test cannot see paraphrase, which is
> the failure mode exposure produces, and it has never been run against a case
> it must catch. Two rows are named by the author as places an echo could be
> suspected. Read 0 of 48 as NOTHING MEASURED about originality until the
> conditions in decision-2026-09-10-ruling-the-four-lane-batch.md section 5
> are met.

**Amendment 3, beside every brief receipt field written before the lane-2 fix,
and in any document that quotes one.**

> Brief receipt fields fileCommit and outboundLatencySec written before
> <fix-commit> are INSTRUMENT FAULTS, not facts. BriefReceipts.sent unpacked
> two values from a call returning three inside a bare except, so every such
> receipt reported fileCommit=none and outboundLatencySec=nothing-measured
> regardless of what happened. Read them as nothing measured, NOT as not
> committed and NOT as not sent. Do not back-fill values that were never
> recorded.

Replace `<fix-commit>` with the actual short sha once the commit exists.
Annotate; do not rewrite the historical receipt values.

**Amendment 4, to the burial gate's emit and to queue 228's answer.**
The fourth CONTACT bucket is granted (section 6). `propFullyBuried=11/40` is
RETIRED as a standalone key. Its replacement ships with this note beside it:

> Bucket set changed 2026-09-10: SUNK / CONTACT / CLEAR / NO-DATUM. The
> previous propFullyBuried=11/40 counted resting-on and sunk-into together
> because the predicate was half-open and fired on a coincident face. The new
> split is a RECLASSIFICATION, not a regression; the two awnings at 370 mm and
> 810 mm of real penetration stay in SUNK and the gate stays red on them.

**Amendment 5, to `VignetteSpec.h` `NullSeriesLine`, found by me this session
and not on any builder's report (section 9).** The key
`nullSeriesTiedGroups` does not count tied groups. It counts tied FRAMES: the
loop at lines 2568 to 2579 increments once per measured frame whose group
equals the running best, so a single rival group of seven frames prints
`nullSeriesTiedGroups=7` and reads as seven rival groups. Either divide by the
group size or rename the key to `nullSeriesTiedFrames`, and assert it in the
test on a fixture that PLANTS a tie. Nothing in the repo asserts this key
today: one grep hit, the emit itself.

## 3. Question 2: the seven-versus-nine correction is RIGHT

Upheld, and upheld on evidence I read myself rather than on the report
(section 0, items 2 and 3). Three reasons, in order of weight.

First, the fingerprint's job is to identify frames whose PICTURES must be
identical, and the camera id changes the view matrix, so it is a rendering
input by definition. Grouping by applied fields alone was the instrument
reading the wrong variable. Per rule 3, suspect the instrument first: the
builder did, and found it.

Second, the direction is the one that proves good faith. A null spread
computed over a group containing a real difference reports that difference as
noise, and a noise floor inflated by a camera delta would then ABSORB genuine
regressions silently. Narrowing nine to seven tightens the bound. Rule 2's
prohibition is on moving a bound to make red go away; this moves a bound in
the direction that makes red POSSIBLE. If the builder had widened the group to
nine and raised the floor, I would have refused it on the spot.

Third, it is stated as a falsifiable claim with a named mechanism, two named
frames and a count with a denominator. That is what a finding should look
like, and the claim survived the check.

On the rejecting run I was going to demand, the position has changed because I
read the test. The camera's presence in the fingerprint is ALREADY guarded in
substance: the fixture at vignette-spec-test.cpp line 2587 fills
`F.CameraId` from the live spec, so deleting `cam.` from `SampleKey` makes the
discovered group NINE and the assertion `nullSeriesSamples=7/of=25/` fails.
The guard exists; what is missing is the PROOF that it bites. So the demand
becomes the cheapest decisive measurement instead of a new test: mutate
`SampleKey` to drop the camera, run vignette-spec-test once, paste the red
line showing `9/of=25`, revert the mutation, re-run green. Two runs, one
minute, and the camera term is then proven load-bearing rather than asserted
to be. Condition 3.

## 4. Question 3: how far the receipt correction reaches

It reaches every claim whose evidence was a brief receipt field, and it
reaches them ASYMMETRICALLY. This is the part most likely to be got wrong in
the next session, so it is stated as two rules.

**Void in the negative direction.** Any claim of the form "the brief was not
committed", "no brief has landed", "the outbound path never ran" or "latency
is unmeasurable" that rests on fileCommit=none or
outboundLatencySec=nothing-measured is now void. Those were not observations.
A bare except swallowing an arity mismatch produces a CONSTANT, and a constant
is not a measurement. Per rule 3b, a zero needs a denominator or it cannot
tell nothing from fine; these fields had neither, and the word "none" was
doing the work of a finding.

**Not established in the positive direction.** The fix does not retroactively
prove that earlier briefs WERE committed. Exactly one brief has a measured
receipt: 9 September, committed, latency 64 seconds, ON THE BUILDER'S REPORT,
UNVERIFIED BY ME. Every earlier receipt is genuinely nothing measured and must
be annotated as such (amendment 3), not upgraded. Replacing a false negative
with an unearned positive is the same class of error facing the other way.

**Specific re-reads the resident must perform.** Anywhere in the 7 and 8
September silent-channel work where a receipt field was cited, the citation is
struck and the conclusion re-derived from the entry point instead.
`.claude/rules/ci.md` already records that four explanations were refuted by
one measurement and that a fifth guess was made from four receipts when
sixteen were available; if any of those receipts were brief receipts, that
episode is now partly an INSTRUMENT fault and not only a reasoning fault, and
the casebook entry gains one line saying so. The ci.md standing rule is
strengthened by this, not weakened: the entry point is cheaper than the
argument, and the argument there was conducted against a field that could only
ever print one value.

**Any bound derived from those numbers is void** and must be re-derived from a
printed series (rule 2). If a latency threshold, a staleness window or a retry
count was ever set with reference to outboundLatencySec, it was set against
nothing-measured and has to be reset after the printer runs on real traffic.

**Required structural fix, not optional.** The bare except goes, or it narrows
to the one exception it is entitled to catch, and the receipt writer FAILS
LOUDLY on an arity mismatch. Test it on the accepting case first, then plant a
return-arity change and show it raises. An instrument that cannot tell a broken
call from a clean send is the silent-instrument failure in its purest form, and
it survived here long enough to make a standing fact out of a stack-unpack bug.
That is the incident worth one line in
`ledger-v2/studio-v2/casebook-measurement.md`.

## 5. Question 4: the originality test does NOT survive, and what makes the next one clean

The test does not survive, and the sheet does.

The finding stands as a true statement about the wrong quantity. Zero of
forty-eight rows failing a VERBATIM SUBSTRING test is a fact about verbatim
substrings. The risk created by having the contaminating phrasing in view is
PARAPHRASE, and a substring test is blind to it by construction. So 0 of 48 is
not evidence of originality; it is a clean result from an instrument that was
not pointed at the hazard. Per rule 3b it needs the extra half: what did the
denominator COUNT. It counted rows checked for exact overlap, not rows checked
for derivation.

The contamination is mine. I told the author to copy the spec's shape from the
pass-2 file, and that file embeds Codex's hook prompt verbatim in its source
block. The record names that, in writing, because a contamination attributed to
the author would teach the wrong lesson. The author disclosing it unprompted
and naming the two suspect rows is the behaviour I want repeated, and it is the
reason the sheet is kept rather than thrown away.

Ruling: the Fairview sheet LANDS, marked per amendment 2, as a working draft
whose originality is unproven. The artifact is useful. The claim is withdrawn.

What makes the next one clean, in order:
1. **A shape-only skeleton.** Extract the structure of the pass-2 file into a
   clean template with all third-party prompt text stripped, and make that
   skeleton the ONLY file the author may open for shape. The contaminated
   source is not opened again for this purpose.
2. **A paraphrase measure with a printed series first.** Keep the substring
   test and add, per row, a similarity against the contaminating text: longest
   common token run plus an n-gram overlap. Print the whole series across all
   48 rows, read it, THEN set the bound. In that order, no exceptions (rule 2).
3. **A catching run.** Plant a row copied from the contaminating source and
   show the test reports it. Until that rejecting run exists, the accepting
   result prints the words "nothing measured" beside it, not a zero.
4. **Blind rewrite of the two suspect rows.** An author who has not opened the
   contaminated file rewrites those two rows from the form bible, atlas and
   research alone. If the two versions converge, the phrasing was forced by
   the subject and the suspicion is discharged on evidence. If they diverge,
   the original rows were echoes and they are replaced.
5. **Quality ladder, per the close-out question.** 8 of 48 rows carrying
   INVENTED with gaps named is honest and is the first working result, not the
   best available. The next rung is explicit: name, for each INVENTED row, the
   research that would replace invention with a source. A blank next rung is a
   research task, not a finished aspect.

## 6. Question 5: the burial gate, and the fourth bucket

The CONTACT bucket is GRANTED. Queue 228's card 1 is upheld.

The reasoning is the half that matters: the same missing half that exonerates
the console also HID two real faults. A predicate that cannot distinguish
resting-on from sunk-into was reporting coverAbMm=0.00 for two pre-existing
awnings that penetrate a toplight by 370 mm and a door spandrel by 810 mm.
That is what makes this a genuine instrument repair and not special pleading
for one prop, and the builder was right to present it that way. An exoneration
that arrives alone is an argument; an exoneration that arrives with two new
reds is a measurement.

The predicate, stated so it cannot drift:
- penetration greater than zero, or overlap volume greater than zero: SUNK.
  The existing buried case. The two awnings live here and the gate stays red.
- penetration exactly zero, overlap volume exactly zero, and separation within
  the coincidence tolerance: CONTACT. Resting on. The console at y=3.500000
  lives here.
- separation greater than the tolerance: CLEAR.
- no datum under the footprint: NO-DATUM, kept separate and never folded into
  CLEAR. A placement metric ships in two halves, distance to the datum and
  whether the datum exists, and eight blocks once hung over open sea at
  foot-gap 0.00 exactly because that half was missing.

Conditions:
- The coincidence tolerance is set from a PRINTED SERIES of measured
  separations, not chosen. Print it, read it, then set it.
- Tested from both sides. Plant a coincident face and show it lands in
  CONTACT. Plant a one-micron penetration and show it lands in SUNK. A bucket
  boundary tested from one side only is a ratchet, not a guard.
- The half-open predicate is NOT widened anywhere else in the codebase to make
  any other number go away. Paste the diff of every bound touched.
- The breakdown is printed per the axis placement actually varies on, not per
  camera.
- `propFullyBuried=11/40` is retired per amendment 4 and replaced by propSunk,
  propContact, propClear and propNoDatum, each over the same printed
  denominator, with the sum shown so a reader can see nothing was dropped. No
  spaces in the values: use `/` and `..` for structure. Whole-run numbers on
  the done line, per-sample numbers on the sample line, never both under one
  key.

The five pinned literals repaired to read their counts: approved, each on the
condition that its catching run is printed (reported as tested on the case it
must catch, ON THE BUILDER'S REPORT, UNVERIFIED BY ME). A pinned literal
repaired without a catching run is an unrun guard wearing the costume of a
fixed one.

## 7. Conditions the resident must PRINT before committing

All printable. None requires judgement. A condition that cannot be printed is
not on this list.

1. `python3 ledger/verify.py` green, and the footer pasted FROM
   `ledger/.verify-footer`, never from the scrollback. Includes the CLAUDE.md
   word-count line.
2. Every reported count re-run and pasted AS THE TOOL EMITS IT, with the
   command beside it: vignette-spec-test 292 checks; frame-stats 108/0;
   core-port 2517/0; CoreTests 4315; brief rows 46; bot 132; outbox 115. Each
   zero prints its denominator. Any number differing from this ruling blocks
   the commit until the difference is written into this file.
3. Lane 1, the camera-term mutation run, both halves (section 3): with `cam.`
   dropped from `SampleKey`, the RED line showing `nullSeriesSamples=9/of=25`;
   with it restored, the green line showing `7/of=25` and the seven ids in
   shot order. Also paste `nullSeriesTiedGroups` and confirm it reads 0 today,
   because at any other value the key is uninterpretable until amendment 5
   lands.
4. Queue 231's staging bound: the four judged pairs printed BY NAME from the
   accepting run, and the rejecting fixture's red line.
5. Lane 2: the three planted regressions, each red line pasted; the pair
   picture-dropped-by-wiring red and picture-never-there green; and one real
   receipt read FROM THE FILE showing fileCommit=<sha> and
   outboundLatencySec=<n>. Also the line proving brief.py calls outbox's photo
   path rather than sending on its own.
6. Lane 3: the row count and the INVENTED-row count taken from the sheet
   itself, plus either the catching run on a planted copied row or the words
   "nothing measured" printed beside 0 of 48.
7. Lane 4: the gate line printing consoleInsideCornice, penetration in mm,
   overlap volume, the shared plane y, and the four bucket keys with their
   denominator and sum. Plus the two awnings now reading 370 mm and 810 mm
   where they read 0.00. Plus, for each of the five repaired literals, the red
   line from the case it must catch.
8. Rule 6 call-site greps, pasted: `SampleKey`, the CONTACT bucket key, and
   brief.py's call into outbox. Built is not running.
9. Rule 1 sentence greps, pasted with hit counts and file lists: "seven
   frames", "identical rendering inputs", "fileCommit=none",
   "propFullyBuried". Read every hit, fix every copy. Note that
   `VignetteSpec.h` line 2450 still narrates the review's by-hand seven as
   "WHAT THE REVIEW FOUND" and is correct in context; do not edit it into
   disagreement with the corrected record.
10. The diff lines touching ANY bound or threshold in this batch, each with a
    one-line justification, and an explicit statement that no bound was
    loosened.
11. Lane 3 canon check: print the `canon.md` lines bearing on Fairview and
    confirm the sheet contradicts none of them. `canon.md` outranks the sheet.
12. A one-line statement that the five amendments in section 2 are applied,
    naming the file and line for each.
13. The cadence gate's own numbers, pasted: rulingStamps, rulingFresh,
    rulingStale, rulingUnmatched. THIS ruling's stamp must land in FRESH and
    not in UNMATCHED. See section 8: I got the stamp format wrong once already,
    and an unmatched stamp clears nothing while looking like a ruling on disk.

## 8. The fault in this record, found by checking my own work

Recorded because it is the same class of fault the batch above is full of.

I first wrote this file's stamp as
`<!--RULING spawn=2026-09-10T06:30:10Z-studio-director-->`, appending the agent
name to the timestamp. That is unparseable. In `ledger/verify.py`,
`RULING_KV = re.compile(r"([A-Za-z][A-Za-z0-9_]*)=(\S+)")` captures the whole
non-space value, and `_cadence_epoch` (line 3147) strips a trailing `Z` to
`+00:00` and hands the result to `datetime.datetime.fromisoformat`, which
rejects `2026-09-10T06:30:10+00:00-studio-director`. It returns None, and
`_cadence_rulings` counts the stamp as `unmatched`, documented at line 3229 as
"NOT counted as a ruling, in the direction that can only refuse".

So the ruling would have sat on disk, complete and readable, clearing nothing,
and the commit would have stayed blocked for a reason nobody would have
connected to this file. `production/findings.txt` line 241 records the same
class of error already: an unmatched stamp reading
`<!--RULING spawn=studio-director-->`, an agent name where a timestamp belongs.
I made the hybrid of it.

The stamp is now the bare ISO value `2026-09-10T06:30:10Z`, matching row 503 of
`.claude/agent-log.tsv` verbatim. Two things I could not check without a shell,
both folded into condition 13: that the row is NEWER than the reference commit
the gate compares against, and that the gate actually counts this stamp as
fresh. Read the gate's printed numbers, not this paragraph.

## 9. The fault I found in lane 1, which no builder reported

`NullSeriesLine` in `ue-probe/Source/LedgerProbe/Public/VignetteSpec.h`, lines
2566 to 2596, read this session:

```
if (N > Best) { Best = N; BestKey = K; Ties = 0; }
else if (N == Best && K != BestKey) { ++Ties; }
```

The loop is over FRAMES, so every frame of a rival group increments `Ties`.
One rival group of seven frames prints `nullSeriesTiedGroups=7`, which reads as
seven rival groups: the key's name is not what the number is a statistic of,
which is the first bullet of `.claude/rules/instruments.md`. It is LATENT
today, because the live spec has one largest group, so the key should print 0
and condition 3 makes the resident prove that. It becomes a live misreading the
first time a second group ties, which is exactly when a reader would be
depending on it. Nothing asserts the key: one grep hit across the whole repo,
the emit itself. Amendment 5 fixes the name or the arithmetic and asserts it on
a planted tie.

This does not change the ruling on question 2. It is a separate, smaller fault
in good code, and it is the kind of thing that is only ever found by reading
the arithmetic rather than the report about the arithmetic.

## 10. What stays open after this commit

Queued, named, not folded into this change:
- The paraphrase measure and the blind rewrite of the two suspect Fairview
  rows (section 5, items 2 to 4).
- Re-deriving any bound ever set from a brief-receipt latency (section 4).
- The casebook line for the swallowed-arity receipt fault, in
  `ledger-v2/studio-v2/casebook-measurement.md`.
- The INVENTED-row research task for the 8 named gaps.
- Amendment 5's tie-counter repair, if it is not taken inside this commit.
