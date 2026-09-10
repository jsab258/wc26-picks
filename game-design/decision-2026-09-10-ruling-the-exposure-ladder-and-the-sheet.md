<!--RULING spawn=2026-09-10T09:48:19Z-->
# LOG: ruling on the exposure ladder and the district sheet, 2026-09-10

> **STATUS: LOG, 2026-09-10. NOT CURRENT** once the conditions in section 9
> are printed and the batch is committed. Decision record, binding on the
> resident for this commit.

Author: tier-1 director, stamp above naming row 515 of
`.claude/agent-log.tsv`, read this session (`2026-09-10T09:48:19Z` TAB
`studio-director`, the newest director row in the log at the time of writing).

Scope: 2050 changed lines, two lanes, both reported at a clean boundary. Six
questions put to me plus the print-before-commit conditions.

STAMP NOTE for the resident. The stamp is the BARE timestamp. A predecessor
wrote `spawn=<iso>Z-studio-director`; the cadence reader's `_cadence_epoch`
only rewrites a value that ENDS in Z, so the appended name left the Z in the
middle, `fromisoformat` refused it, and the ruling counted UNMATCHED while
sitting on disk clearing nothing. That cost a spawn. Do not decorate the
stamp.

Scope of my verification: I read `.claude/agent-log.tsv` for the spawn row,
`ledger/verify.py` for the stamp reader, and `tools/docs-check.py` for this
banner's form. I have no Bash in this spawn. EVERY COUNT BELOW IS ON THE
BUILDERS' REPORTS AND UNVERIFIED BY ME: 2050 changed lines, 383 of 383, the
355 baseline, 108 of 108, 4319, 32 of 32, 0.6102 / 0.9562, 0.1112 / 0.0384,
-36.0 / 25.0, six lettering regions, two correct and four garbled,
typedInThisFile=0/8, omitted=2. Section 9 makes re-printing them a condition
of the commit. I rule on them as reported because that is the cheapest
decisive path: if a re-print disagrees with a number below, the ruling that
rests on it is void and the batch comes back.

---

## 1. Premise check first

Section 0 of CLAUDE.md: Meridian, a British port town, LATE-ANALOG, working
window 1988 to 1992, landlines and paper, no mobiles and no internet. The
moat is social memory, consequence persistence and information. The visual
target is photoreal, wet, overcast, grimy Britain, and the instrument is the
Meridian Test.

Neither lane contradicts the premise. Lane one is determinism in the
instrument that photographs the world, which serves Meridian Test item 1
(thirty minutes without bouncing off the visuals) by making the evidence
channel readable at all. Lane two is a concept sheet, a production artefact
rather than a shipped one, and it serves nothing in the test directly; it is
approved on the owner's explicit request, not on a pillar.

One premise exposure in lane two that the builder did not report on: a sheet
printing street nameplates, a header and a tagline is printing CANON, and a
composited string is a string somebody chose. Condition 9.8 covers it.

## 2. Question 1: the batch

APPROVED WITH AMENDMENTS. Both lanes are approved in substance. The
amendments are dictated in sections 3 to 8 and the conditions in section 9.
Nothing in this batch sets a constant, which is why it can be approved at
all: it is two instruments and an artefact, not a tuning.

The most important thing either builder did today is the thing neither was
asked to do. Lane one printed `ladderVerdict=SERIES-ONLY` and refused to call
the result agreement, because no bound on the first-to-repeat difference has
been measured. Lane two MEASURED THE ROUTE instead of taking my
recommendation, and the measurement overturned a belief this lane had written
down twice. Both are the behaviour the standing order asks for and both are
recorded here so the next session can cite them.

Dictated amendment text, to be pasted where noted.

AMENDMENT A, into the ladder's own documentation beside `ladderVerdict`:

    ladderVerdict stays SERIES-ONLY until a bound on the first-to-repeat
    difference has been measured from printed runs across the full
    camera-by-condition matrix, not one pair. Replacing SERIES-ONLY with a
    pass or fail before that series exists is a rule 2 violation and is
    refused in review. The bound is set from the series, in that order.

AMENDMENT B, into the condition-schema documentation beside `exposure_pin`:

    exposure_pin is REQUIRED and stays required. An optional field
    defaulting to zero makes "the writer chose auto exposure" and "the
    writer forgot the key" the same bytes, and a readback cannot
    distinguish them. The readback therefore prints an explicit
    auto-versus-pinned flag and never infers auto from the value 0.000.

AMENDMENT C, into the sheet's footer, appended to the existing disclosure:

    Lettering on this sheet is composited, not generated. Annotation
    numbers are computed from the atlas; typed-in-this-file count is zero.
    Strings present that were not requested are listed below with a count.

AMENDMENT D, into whichever spec document carries the old lettering belief,
replacing it rather than sitting beside it: the text of section 7 below, and
the old belief struck with a pointer to this ruling. Rule 1's last clause
applies: grep for the SENTENCE of the old belief, not the site, and strike
every copy. It was written down twice that the builder found; the count of
copies actually struck goes in the commit message.

## 3. Question 2: one pin cannot serve both, and the shape of the fix

The core question is not which value to pin. It is whether the SCHEMA is
wrong or whether a MEASUREMENT IS MISSING. Those need different work and only
one of them is cheap.

The builder is right that the four rungs differ from the day reference by the
pin alone, so any value chosen from this ladder reproduces the DAY level. It
is also right that there is no night target to match: 0.1112 and 0.0384 at
83dec33 sit far below where every unclamped day frame settled, which is what
a frame photographed mid-adaptation looks like. A number read off an unsettled
frame is not a target, it is a timestamp.

RULING: ONE PIN, PER CONDITION. No second field. No night rung set in this
batch.

`exposure_pin` is a CONDITION field, and each condition already carries its
own time of day. The schema therefore already expresses a different pin for
night than for day; a second field buys nothing except a second place for the
two values to disagree. The ladder varies the pin within one condition, which
is what a ladder is for, and that does not make the field day-only.

What is actually missing is a settled night reference, and it cannot be
obtained by arithmetic from anything now on disk. This is the same fault as
the instruction I issued and withdrew an hour ago: I asked for a pinned value
to be derived from a printed series of tonemapped 8-bit output luma when the
setting is a scene-luminance input, and no arithmetic connects them. Scaling
a chosen day pin by the ratio of two night lumas would be that same error in
a different hat, and it is FORBIDDEN here by name so that a later session
cannot reinvent it as an optimisation.

The night pin is therefore a RESEARCH RUNG and goes to the queue with a name:
"settled night exposure reference". Its shape, dictated so the next brief does
not have to invent it:

1. Hold the night condition and render the same camera repeatedly, printing
   the output luma series per frame, until the series stops moving. Print the
   series. Do not set anything.
2. From that series, state HOW MANY frames settling takes and what the
   settled level is, naming the statistic (last-wins, not peak, not mean).
   If it does not settle, that is the finding and it outranks the pin.
3. Only then run a night rung set, four rungs at the same spacing, and only
   then choose a night pin.

Until step 3 lands, night conditions carry `exposure_pin=0.000` and are
explicitly NOT determinism-gated. A gate covering a condition whose reference
does not exist is a gate reading a number nobody measured.

Secondary amendment, on the determinism failure itself. The reported evidence
is rigMeanLumaFirst=0.6102 against rigMeanLumaRepeat=0.9562 on ONE camera and
ONE condition. Rule 3b: that finding has no denominator. How many
camera-by-condition pairs were compared? If the answer is one, then "every
cross-frame number in that run is void" is an inference from a sample of one,
and it may be generous or it may be understating the damage. Condition 9.9
requires the full matrix printed with its count, because the shape of the
spread across pairs decides whether this is adaptation carry-over between
conditions (expected to show on the pairs that follow a different condition)
or something worse.

## 4. Question 6: exposure_pin being required

RULING: REQUIRED IS RIGHT. Keep it. Taken out of order because section 3
depends on it.

The builder's reasoning is sound and it is rule 3b in other clothing. The
safe value is zero, so an optional field defaulting to zero produces a
readback that cannot tell a deliberate auto-exposure choice from a dropped
key. That is the silent-instrument failure: the number is present, plausible
and meaningless. Twenty-two conditions each carrying an explicit 0.000 is a
one-time cost, grep-reviewable, and it buys a readback that means something
on every row for ever.

Three amendments.

First, the four-field readback on the SHOT line must include an explicit
auto-versus-pinned flag as one of the four fields, not leave auto to be
inferred from 0.000. If it already does, the builder names which field it is;
if it does not, that is the amendment. Putting the readback on the shot line
rather than the run line is correct and matches the instruments rule:
per-sample numbers on the sample line.

Second, the run line prints the denominator of the pin itself, as two keys:
the count of conditions carrying a pin and the count whose pin is non-zero.
A zero shipped without its denominator cannot tell nothing from fine. No
spaces in emitted values.

Third, "required" must be ENFORCED, not documented. A condition missing the
key fails loudly at load, and the guard is exercised on both outcomes per
rule 5b: the accepting case is the live 22 conditions, the rejecting case is
a synthetic condition with the key deleted. Both watched, accepting first.

## 5. Question 3: the compositing decision

The core question: a composited sheet is no longer one generated artefact, so
what is it, and what does comparing it to the outside sheets prove?

RULING: COMPOSITING IS THE RIGHT STANDARD FOR A CONCEPT SHEET, and it changes
what the comparison is evidence for. Both halves matter.

Why it is right. A concept sheet's job is to carry correct information to a
human: which landmark is which, what a street is called, which annotation
number points where. Those are facts with a source of truth, and the atlas is
it. A diffusion model cannot type, and asking it to reproduce facts it cannot
represent is asking an instrument for a number it does not hold. A sheet with
`typedInThisFile=0/8` and every annotation number computed from the atlas is
strictly better evidence than a model-lettered sheet that happens to read
correctly, because the computed one cannot drift when the atlas changes and
the lettered one can. The planted failure is the part that makes me believe
it: a bad camera station and a missing landmark id produced omitted=2 and NO
INVENTED NUMBERS. That is the accepting-and-rejecting pair rule 5b asks for,
on the path that matters most.

What it changes. The comparison against the outside sheets is now evidence
for PARITY OF PRESENTATION and nothing more. It is specifically NOT evidence
that our generator can produce a finished sheet, and those two have been
getting conflated. Anybody who later cites this sheet as proof of generation
capability is citing a composite.

And there is a prior question the lane has not answered, which decides
whether "finished to the standard of the outside ones" is even the right
frame: WERE THE OUTSIDE SHEETS COMPOSITED OR MODEL-LETTERED? I have not
checked and it is on nobody's report. Condition 9.6. The consequence branches:

- If the outside sheets are composited, the district sheets now match them by
  construction, Jafar's request is satisfied on its own terms, and the footers
  of all of them should carry the same disclosure.
- If the outside sheets are model-lettered AND legible at small sizes inside
  photographic content, then the lettering rule in section 7 is refuted by our
  own back catalogue and must be re-derived before the next spec cites it.
  That outcome is more interesting than this batch and would be the finding of
  the day.

Either way the sheet is approved. The branch decides what the next spec may
claim, not whether this commit lands.

## 6. Question 4: overriding one of Jafar's defaults

RULING: THAT WAS YOURS TO TAKE, and it was taken the right way. Approved,
with one obligation attached.

"Take every default" and "finish the sheets to the standard of the outside
ones" are not two instructions in conflict. "Take every default" is an
instruction about WHO DECIDES: do not come back to me for each choice. It is
a tie-breaker for choices the owner has not determined. "Finished to the
standard of the outside ones" DETERMINES the choice, because the outside
sheets are labelled. There is no tie left for the default to break. Taking
the later and more specific sentence is the correct reading of a single
message, and logging it is what makes it reviewable rather than a preference.

The limit of this authority, stated so it is not stretched:

    A default may be overridden only when a more specific sentence in the
    SAME message determines the same choice. It may never be overridden
    because the director judges the non-default result better. That second
    move is a premise change and escalates.

The obligation. The override is surfaced in the next Producer report as one
line quoting both of Jafar's sentences and naming the call. Not a question, a
notification, and reporting to Jafar is the Producer's alone. A default
overridden silently is exactly how a premise drifts, and section 0 of
CLAUDE.md exists because drift happened here four times in one conversation
across four sources that were each correct.

## 7. Question 5: the lettering rule, replacement text

The old belief is REFUTED: legibility does not track the number of strings
requested. Replacement, for the next spec author. This is Amendment D and it
REPLACES the old text rather than sitting beside it.

    LETTERING RULE, set 2026-09-10 from six measured regions in one drawn
    sheet. Legibility tracks GLYPH SIZE in the rendered frame and WHETHER
    THE STRING SITS IN FLAT MARGIN SPACE OR INSIDE DEPICTED PHOTOGRAPHIC
    CONTENT. Measured: 2 of 6 regions correct, both large and on the
    margin; 4 of 6 garbled, all small and inside a photograph, one street
    nameplate reading GHVAJS. String count did not separate the two
    groups. Size and placement did.

    MAY be asked of the model: nothing load-bearing. At most large display
    lettering in flat margin space, and only where a wrong glyph is
    cosmetic. Every such string is still read back off the opened artefact
    before the sheet is called done.

    MUST be composited: every small string, every string inside depicted
    content, every street nameplate, every identifier, every number, and
    every label a reader would act on. Numbers are computed from the
    source of truth and never typed; typed-in-this-file count is printed
    and the standard is zero.

    THE MODEL WILL LETTER THINGS NOBODY ASKED FOR. Three of the four
    garbled strings were never requested. The request for unlabelled rows
    sat in the NEGATIVE half, which at cfg 1.0 is NEVER EVALUATED, so it
    bought nothing and the model captioned a garden gate. Suppression of
    unrequested lettering is not achievable by asking. It is achieved by
    compositing over, by masking the region, or by cropping. Therefore
    every sheet is inspected for UNREQUESTED strings and the count found is
    reported beside the count requested.

    DENOMINATOR AND STANDING: 6 regions, 1 sheet, 1 model, 1 cfg value.
    This is a rule for the next spec author, not a law. It is re-measured
    when the sheet count reaches four, and the re-measurement is named in
    the queue as a rung rather than left implicit.

The cfg-1.0 clause is the most valuable line in this batch for anyone writing
prompts, because it explains a whole class of "the model ignored my
instruction" reports as the instruction never having been read. Grep for other
specs that put requirements in a negative prompt and list them. That is
ADJACENT, so it goes to the queue with a name and does not enter this change:
"negative-half requirements audit".

## 8. The four repaired literals

Repairing a pinned literal into a stated invariant rather than bumping it is
the right instinct, and the named example is a good one: `ProbeShots == 20 AND
ProbeAtHook == 20` failing at 32 of 32 while the invariant held is a guard
that cannot tell a regression from an improvement, which is a ratchet. The new
form, `ProbeShots > 0 AND ProbeAtHook == ProbeShots`, states the invariant and
cannot be satisfied by a count moving. Approved.

But a literal relaxed into an inequality is ALSO the exact shape of the
forbidden move under rule 2, a bound moved to make red go away, and the two
are distinguishable only by evidence. So, as a condition and not a suggestion:
each of the four gets a PLANTED REJECTION. For the named one, plant a probe
shot that is not at hook and show the guard fails; `> 0` is also tested at
zero. A guard with no demonstrated rejecting case is a comment. All four are
listed with before, after, and the invariant the new form states, in the
commit message.

The `expPin`-in-the-fingerprint catch is approved and is the subtlest good
call in lane one: without it the eight ladder rows form an identical-input
group of nine and the ladder's DELIBERATE spread is published as the run's
noise floor, which would have poisoned the very bound section 3 defers.
Amendment: the fingerprint's field list is printed in the run output, so a
future field added without inclusion is visible rather than silent.

## 9. Conditions the resident must PRINT before committing

Each is a printed artefact in this session's scrollback, not a recollection.
If any cannot be printed, the batch does not commit and the reason goes to the
queue.

9.1 `python3 ledger/verify.py` green, and the footer pasted FROM
`ledger/.verify-footer`, never from the scrollback.

9.2 The three reported counts re-run and pasted: vignette-spec-test 383 of
383, frame-stats 108 of 108, CoreTests 4319. Plus the 355-to-383 delta named:
which 28 tests are new, by name or by file. A baseline that moves without a
named delta is a baseline that can absorb a deletion.

9.3 Call-site grep for `exposure_pin` and `expPin`, rule 6, showing four
distinct call sites with counts: the write, the shot-line readback, the
fingerprint inclusion, and the 22 conditions carrying an explicit value. The
22 is printed as a count from the grep, not asserted.

9.4 The ladder output opened and read as text, rule 4: 12 shot lines present,
8 ladder rows, 4 rungs by 2 halves, each row showing both halves and the
signed difference, and `ladderVerdict=SERIES-ONLY` literally present. Read
the rows before reading any verdict.

9.5 The sheet PNG OPENED, rule 4, all eight composited labels read back by
eye, and the count of UNREQUESTED strings found in the rendered sheet reported
beside the count requested. A green annotation count is not the frame it
claims to describe.

9.6 For each outside sheet, whether its lettering was model-generated or
composited, with a count of sheets examined. This decides section 5's branch.

9.7 The planted omission evidence re-printed with BOTH outcomes and a
denominator: the rejecting case (bad station, missing id, omitted=2, and 2 OF
HOW MANY) and the accepting case (good station, omitted=0 against the same
denominator). Accepting case first.

9.8 Every visible string on the sheet checked against `canon.md` and against
the 1988 to 1992 window, FAIRVIEW included. Print the canon grep. A
composited string is a string somebody chose, and canon outranks every agent.

9.9 The determinism matrix: first and repeat luma for every
camera-by-condition pair compared, with the count of pairs, replacing the
single 0.6102 / 0.9562 pair. No spaces in emitted values.

9.10 `python3 tools/docs-check.py` and `python3 tools/goal-block-check.py`.

9.11 The guard runs from section 4 (synthetic condition with `exposure_pin`
deleted, rejected; the live 22, accepted) and from section 8 (four planted
rejections).

## 10. The quality ladder at close

Best available, or first working? Both lanes are FIRST WORKING and both know
it, which is why they are approved. The next rungs, named, so neither aspect
closes with a blank.

LANE ONE next rung: a measured bound on the first-to-repeat difference across
the full matrix, then a day pin chosen from the series, then the settled night
exposure reference in section 3 and a night rung set. Three rungs, in that
order, the first two cheap and the third a research task.

LANE TWO next rung: the legibility verdict is currently an EYEBALL, and "I
read it and it looked right" is the instrument deciding whether our lettering
works. Replace it with a mechanical check: OCR the rendered sheet and diff
against the intended strings, printing matched, garbled and UNREQUESTED counts
with the region count as denominator. Then the six-region finding gets
re-measured on four sheets instead of one. Any OCR tool enters only through a
decision record naming its weights licence, because THE LICENCE ALLOWLIST IS
LAW and there is no exception for a tool that only measures.

## 11. What was refused

Nothing in this batch. For the record of what WOULD have been refused: a
pinned constant chosen this session from the tonemapped output series, which
is what I asked for an hour ago and withdrew, because no arithmetic connects
an 8-bit output luma to a scene-luminance input and this project already
recorded that the adapted exposure is never read by this process. The builder
was right to come back with a ladder. A director's instruction is not
evidence either.
