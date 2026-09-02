# Casebook: measurement and statistics

STATUS: LIVE. Verified 2026-09-01.

Moved out of CLAUDE.md on 2026-09-01 by task 013. These are the instrument
faults: thresholds set without a series, a statistic answering a question it
structurally cannot answer, and zeros with no denominator.

The terse rules distilled from these pages are in .claude/rules/instruments.md,
which loads when you edit measurement code. This file is where each of those
bullets came from, and it is worth opening before you set a bound, choose an
aggregator, or read two numbers side by side.

---

<!-- moved verbatim from CLAUDE.md lines 157-415 on 2026-09-01, task 013 -->

## 2. Never set a threshold you have not measured

- `nightNotDarker` compared one noon frame to one night frame and failed at
  0.136 against 0.135. That is a rounding, not a measurement.
- `deedSlotSets` sat ungated for days because I refused to invent a number —
  that refusal was correct, and the fix was to make the run **print the series**
  so a threshold could come from evidence.

**The rule.** If you need a threshold, first make the system report the value,
run it, look, then set it. When a gate is failing, ask whether the instrument
or the subject is wrong before touching either.

**This covers the METRIC and the AGGREGATOR, not just the number.** Both were
got wrong in one night, and neither is a threshold:

- The §4.7 places gate read `alley=53 market=53`, I called the count saturated
  by hearing and re-gated on eye-witnesses only. That was one sample. The alley
  pick had simply happened to stand in the open, and the next run — printing all
  four columns — read 3 / 53 / 3, which is the claim exactly. I had moved a gate
  onto a worse metric to fix a problem that did not exist, and had to move it
  back.
- The AO gate bounded a fraction ABOVE 50% while `MeasureAoOnce` kept the
  MAXIMUM of its rounds. A maximum answers "did the pass ever reach the frame";
  it cannot answer "is the pass everywhere", because it maximises the very
  quantity the ceiling exists to keep small — so adding rounds made it trip on
  its own. One run read 80%; the round series read
  `[26.9 26.4 26.4 22.8 23.0 23.0 5.9 5.9 5.9]`, median 23.

So: choosing WHICH number a gate reads, and which statistic summarises it, needs
the same evidence as choosing the threshold — and one run is not evidence.
Print the series first. When a gate asks two questions, give each the statistic
that answers it, and do not move the bound to make red go away.

**AND A FORK YOU WRITE INTO A COMMENT CAN ITSELF BE FALSE — TWO NUMBERS
DERIVED FROM ONE VARIABLE ARE ONE NUMBER TWICE.** This is not comment decay;
the comment was wrong the day it was written, and being careful is what made it
convincing. `roomQuiet` was 73% of a run, and the paragraph beside it set up the
honest-looking fork: *either* the pulse layer sits at its floor because the
street is quiet, *or* unease sits high because the game is tense, "and they want
opposite fixes". The distribution came back `pulseMedian=0.000
uneaseMedian=1.000`, which reads as both at once, and it is neither.

`MusicModel.Mix` computes ONE variable and derives both layers from it: pulse is
zero for any exposure at or above 0.667 and unease is one at or above 0.8, so
unease at its ceiling FORCES pulse to its floor, arithmetically. Two findings
were one finding double-counted, and the real question — why is exposure at 0.8
for the median sample — had never been asked because the fork looked like it
had already framed everything.

**The check is mechanical and takes a minute: before printing two numbers side
by side as evidence, read the code that produces them and ask whether either
can move while the other stands still.** If it cannot, they are one measurement
and the variable behind them is what to print. Here that was `heatMedian`, and
it is also the number that decides whether the fault is a music problem or a
harness one — a distinction neither of the original two could express.

**AND A LIFETIME COUNT SAMPLED BY A SPARSE SAMPLER FREEZES AT THE LAST SAMPLE.**
A third instant fault, same day, and the first two were about pairs — this one
is a single number that is simply not from the moment it claims.

`namesManagedEver` is a cumulative count of every label ever offered to the
declutter. I captured it inside `CollidingNames`, which runs only when a
screenshot is taken. So it froze at the LAST SHOT while `nameTagsOffered` — a
peak over every frame — kept rising, and the verdict printed **44 offered in one
frame against 28 ever managed**, which cannot both be true because every offer
adds to the managed set.

The tell was the impossibility, not the size: a lifetime total can never be
smaller than a single frame's count of the same thing. **When a number is
CUMULATIVE, read it where the run ends, not inside whatever function happened to
be convenient** — and when a cumulative number sits beside a per-frame peak, ask
whether they were even taken on the same day of the run.

Both of the numbers involved were written the same morning, which is the rule
above doing exactly what it warns about.

**TWO MAXIMA CANNOT BE DIVIDED, AND FOUR PAIRS IN THIS PROJECT WERE.** A peak is
the right statistic for "how bad did it get" and the wrong one for the other
half of a fraction, because the worst instant for the numerator need not be the
worst instant for the denominator. Found on 4 August, four sites in one night:

| printed as | and they were |
|---|---|
| `collidingBubbles=91 bubblesOnScreen=16` | the worst overlap frame and the busiest frame, not the same frame |
| `textFacingAway=70 textVisible=149` | two independent peaks I quoted as "47%" — in a queue item I had written telling myself to read the ratio |
| `deedWitnesses=53 deedEyesOpen=50 deedKnowsYou=41` | three maxima over three possibly different deeds, printed as one event's breakdown |
| `companionRung` vs `companionStreetRung` | **correct** — both taken in one loop over the same witness set, and its comment says why |

The fix is always the same shape: capture the denominator AT THE INSTANT the
numerator peaks, and name it so (`bubblesAtWorst`, `textVisibleAtAway`). The
sweep that found them is mechanical and takes two minutes — **list every field
assigned by a max, then ask which of them are printed next to each other.**
Twenty-two peak fields in `SimDirector`, four bad pairs, one that was right.

**AND THE SAME-INSTANT RULE GOVERNS THE LOG LINE, NOT ONLY THE FRAME. This one
cost a whole afternoon and five wrong answers.** The rule above is about
capturing a denominator at the instant its numerator peaks, and five sites in
`SimDirector` were fixed for it. Every one of those fixes was about the frame.
None of us noticed that a number is also captured by the LINE it is printed on.

`nameTagsOffered` is on the done line, written once at the end of the run.
`namesDistinctPeak` and its family were on the `glyphs` line, which is emitted
on every SCREENSHOT. Same counters, different moments — and the peaks keep
climbing after the last shot. So the done line said 42 and the glyphs line said
13, and I called it an arithmetic impossibility, published four explanations
across four builds, and finally DELETED the counter under the rule that a
measurement contradicting itself twice gets deleted rather than explained.

The rule was right. It was applied to the wrong thing. `OfferedPeak` was never
broken; the reading was, and the reading was mine — I had been running
`grep -o` across the whole verdict file, which happily returns two values from
two different lines and shows no sign that it has done so.

**Two mechanical steps, and they are cheap.** When a number describes the whole
run, print it on the done line — the shot line keeps only what is true of the
shot. And do not read a verdict with `grep -o` again: **`tools/verdict-read.py`
takes the keys you want, prints each with its LINE NUMBER, and refuses with
exit 2 when they do not share one**, saying why. It catches the exact pair that
cost this afternoon, and it exists because a rule that depends on my
remembering to add `-n` is a rule that decays — which is what the rest of this
file is a list of.

**A PEAK CANNOT SEE A MIDDLE AND A MEDIAN CANNOT SEE A TAIL, AND ON 4 AUGUST I
GOT CAUGHT BY BOTH BEFORE BREAKFAST.** The rule above says print the series and
read the median. That is right and it is not sufficient, because the median has
a blind spot of its own and it is exactly the interesting one:

| number | the summary | the truth |
|---|---|---|
| `confabs` | `queue.md` said "was 74" | 74 is the single HIGHEST reading in the project's history. The distribution over 43 runs is 29 / 43 / **49** / 60 / 74. Anything in the low forties — the commonest band there is — would have been reported as conversation collapsing under the crowd change, and "fixed". |
| `billboardStale` | median 0.000, and I wrote "billboards are fine" | `billboardWorstDeg=116.9`, with 38 of 57 stale. The median was correct. Every fault was in the tail, which is the one thing a median structurally cannot show. |

Same morning, opposite directions, and neither was a threshold. **So: which
statistic you read is a choice about which question you are asking, and a
summary is never the evidence.** A peak answers "did it ever"; a median answers
"is this normal"; neither answers the other and a system usually needs both
printed side by side. `tools/gates.py --series <key>` exists for this — it
prints every landed value of a verdict number, newest first, then the recent
window, then all runs, and it puts the raw series ABOVE both summaries on
purpose.

**And beware the regime change, which no statistic survives.** `confabs` read
1–13 under the old flat-road conversation rule and 29–74 under the junction
one, so its all-time median of 34 describes neither test. No aggregate can see
that break. A human looking at the row of numbers sees it in a second, which is
the whole argument for printing the series.

**AND WHEN YOU CATCH ONE, CHECK THE NUMBERS BESIDE IT — 4 August, twice on one
line, four hours apart.** At 07:20 I corrected `queue.md` for quoting `confabs`
74 as a baseline when 74 was the all-time peak. At 11:30 I had spent three
builds and two real code changes chasing `crowdTightest=0.00`, which is a run
MINIMUM: one frame anywhere in nine days — two walkers spawned on the same
waypoint, sampled before either has stepped — pins it at 0.00 for ever and no
later separation can lift it. Its neighbour `crowdGapMedian` had been moving
every build, 0.00 → 0.20 → 0.29 → 0.33 → 0.35, and was the signal the whole
time.

Having the rule written down, quoting it at myself in a commit message, and
correcting somebody else's instance of it that same morning were all
insufficient. **So the mechanical step is the one from rule 1's third
corollary, applied to statistics: the moment you find a peak being read as a
description, look at every other number printed next to it and ask which
question each one answers.** They are usually written by the same hand in the
same hour and they usually share the fault. Both fixes I made underneath the
wrong reasoning were correct on their own terms — that is what makes this hard
to notice, and it is not the same as having been right.

**AND THE NUMBER MOST LIKELY TO BE WRONG IS THE ONE YOU WROTE AN HOUR AGO.**
Three over-conclusions on 4 August, all mine, all published before being
checked, and all three a DIFFERENT statistical mistake:

| number | I said | it was |
|---|---|---|
| `confabs` | baseline 74 | a peak read as a middle |
| `crowdTightest` | separation is broken | a run minimum read as a description |
| `namesTracked=2` | "the declutter manages two labels" — filed as DECISIVE | a last-wins field read as a summary, describing whichever shot ran last |

The third is the instructive one. I had added the adjacent-numbers rule above
four hours earlier and applied it to somebody else's metric that morning — and
did not think to point it at a counter I had written myself twenty minutes
before. **A number you have just written has been read by nobody, including
you.** It has no landed series, no second opinion and no history of being
quoted correctly, which is precisely the state in which a wrong statistic is
most confident and most quotable.

So: before a new number is allowed into a conclusion, say out loud which of
peak / median / last-wins / at-worst it is, and whether that answers the
question being asked of it. It takes one sentence. All three above would have
been caught by it, and two of them cost a build each.

**AND A MINORITY IS INVISIBLE TO EVERY MEDIAN.** Twice inside one hour on
4 August, in two systems, and both times the picture was right and the number
was right and they disagreed:

| the frame showed | the number said | why both were true |
|---|---|---|
| thirty people packed shoulder to shoulder in a block | `crowdGapMedian=0.41`, a healthy street | a median over PAIRS is dominated by the sixty people nowhere near each other; the huddle is a handful of pairs |
| three figures standing in a clean T-pose on Copper Row | `armStreet=10.6 armStreetWorst=14.8`, arms hanging | `armStreet` is a median ACROSS BODIES and the "worst" is the MAXIMUM OVER THOSE MEDIANS — a worst that never stops being a median |

Both had been used to CLOSE their question. The second one closed it that
morning, in writing, and the T-poses were in the stills of the next two builds.

This is not the peak/median confusion above, which is about reading a number as
the wrong statistic. This is a statistic that is exactly what it says and
**structurally cannot see the thing being asked about**: a median describes the
middle, so any fault affecting fewer than half the population is invisible to it
no matter how severe, and dressing it up as a "worst" over frames does not help
if the per-frame value was itself a median.

The tell is the shape of the question. "What does the street look like" is a
median question. **"Is anybody ..." is never a median question** — it is a max,
a decile, or a count, and it needs the denominator from the same instant beside
it. When a picture and a number disagree, ask which fraction of the population
the fault would touch before believing either.

**AND A NUMBER KEEPS ITS NAME WHEN THE QUESTION IT ANSWERS MOVES.** Three in one
night, all mine, all in metrics I had written hours earlier:

| number | asked | then | and I |
|---|---|---|---|
| `liveArmDrop` | worst-ever arm angle, to catch a frozen T-pose | the body started animating, so it caught the peak of a walk cycle | nearly read a correct animation as a fault |
| `nameTagsOffered` | how many labels the declutter has RIGHT NOW | sat on a done line where every neighbour is a peak or a worst | compared it against a peak and wrote a commit about the contradiction |
| `crowdSpeed` | did the walk land at 1.4 | escorts learned to hurry at 2.6, so the mean rises by design | caught it before, which is the only difference worth having |

The instrument does not change when the system does — that is the whole point of
it — so the drift is silent and it points the wrong way twice: a working feature
reads as a regression, and the number that would have said so reads as
agreement. **When you change what a system DOES, re-read what its numbers ASK**,
the same sweep as re-reading its comments, and say in the comment which question
the number is now answering.

**AND A PEAK CANNOT DESCRIBE A STREET, HOWEVER HONEST THE PEAK IS.** 4 August,
six probes, one fault. A peak answers *"did it ever happen"*. It is read as
*"is this how it looks"*, and those diverge the moment anything varies:

| probe | said, across consecutive green runs | and the median said |
|---|---|---|
| `collidingBubbles` | 91, then 16, then 116 | 0.00 over 166 samples |
| `billboardsStale` | 5, then 12, then 27 | 0.000 of 53 tracked |
| `crowdRead` | 24 bodies, then 11, then 6 | the medians moved 19.5 → 2.8 → 3.0 |

The first two were peaks wandering with how many objects happened to be in
shot. **The third is the sharper lesson, because the sample SIZE is part of the
statistic and nothing about the number says so.** I published a conclusion off
the 24-body sample, reversed it off the 6-body one, and withdrew both — two
opposite claims about the same thing in the same hour, each honest arithmetic
on a sample that could not carry it.

The repair is the same every time and it is cheap: **accumulate per instant,
print the median beside the peak, and name what the number is a statistic OF.**
The peak keeps its job — one still with a line printed backwards is the fault —
and stops being asked a question it structurally cannot answer.

Two tells that a reading is about to do this to you: the value swings by an
order of magnitude between runs that changed nothing relevant, or you are about
to compare two runs without knowing which FRAME each came from. `bodyReadWhen`
exists because the same metric read 35.7 and 10.8 with no code change between
them — noon against midnight, quoted side by side as though they were the same
measurement.

<!-- moved verbatim from CLAUDE.md lines 445-536 on 2026-09-01, task 013 -->

## 3b. A ZERO NEEDS A DENOMINATOR, OR IT CANNOT TELL NOTHING FROM FINE

Three separate systems on the morning of 4 August, each reporting a number that
looked like health and meant nothing, and the third one caught only because the
first two had just happened:

| reported | reads as | also consistent with |
|---|---|---|
| `lint-static: 0 static/instance errors` | the codebase is clean | the walker entered no method bodies at all — which it did not, because this codebase is Allman and it compared brace depth against itself on the signature line |
| `soundsAdmitted=0 dropped=0 stolen=0 peak=0` | the street never got busy enough to need a voice budget | `Admit` returns on a null clip BEFORE any counter moves, so silence upstream prints identically |
| `contrastChecked=40 contrastFailing=0 contrastWorst=21.00` | forty labels measured, all pass | `ContrastWorst` only moves for a FAILING pair, so a clean run leaves it at its initialiser — which happens to be the best ratio there is |

The middle one is the sharpest, because the comment directly above those
counters *says* "a budget that never refuses anything is indistinguishable from
one that is not wired" — written about one of the four, and the very next
reading was ambiguous in exactly the way it warned about.

**The rule. Every zero, every "none", every clean result ships with the count of
what was examined.** `lint-static` now prints "354 static bodies walked", `Audio`
has `soundsOffered`, the contrast check has a `contrastTightest` whose default
text is the words "nothing measured" so that case cannot read as clean. It is
the same repair every time and it is one line: **the denominator.**

**AND THE EXEMPLAR IN THAT SENTENCE IS ITSELF THE FAULT — 25 Aug, found by a
lint written to catch this exact shape.** The sentence above is kept as
written, because it is the trap: a rules file can teach the disease as the
cure and read perfectly while doing it.

`lint-static` prints a count of static bodies over EVERY Game file, while its
scan walks only files matching `public partial class` exactly once and with
detected instance members — and drops the rest **with no message**. Measured:
**560 printed against 29 actually scanned, across 14 of 88 files.** Roughly a
19x inflated denominator, and the 531 unexamined bodies are silent. So the
line quoted above as the model of "ship the denominator" ships a denominator
that describes something the tool never looked at.

**The SCOPE is intentional and stays** — the tool exists for partial-spread
invisibility and must not be widened. **The printed NUMBER is the bug**: it
prints the walked denominator plus a named drop clause, so what was skipped is
said out loud rather than folded into the total. `lint-conditional-reach`,
which names its unwalked set, is the model to copy.

**SIX OF SEVEN, NOT SIX OTHERS — this paragraph said "six other lints were
checked and are clean" and that was a claim about a set nobody had counted.**
Swept: `lint-nested` prints `0 nested-type errors (255 top-level Core types
checked)` and exits 0 **byte-identically for a full 88-file sweep and for a
sweep of NOTHING** — its denominator is the REFERENCE set it compares against,
while the Game file count that would actually move is computed and thrown
away. `lint-shadow` re-globs at print time, so one line carries two moments.
Neither is fixed; both are named.

**AND THE SERIES IS WORTH MORE THAN THE FIX.** This number rode **550 landed
commit footers**, ranging **418 -> 560 over two days**, while the walked set
never left **29**. So the footer showed a denominator that CLIMBED — reading
as coverage growing with the codebase — while coverage never moved at all.
**A wrong number that tracks something looks alive**, and that is far harder
to doubt than a wrong number sitting still. When a count only ever goes up
with the repo, ask what it is counting before trusting that it is measuring.

*(560 and 562 are both true four minutes apart: the old tool read every file
THREE times per run, so one printed line could carry three moments. One read
per file per run now.)*

**The lesson is not "that number was wrong".** It is that a denominator can be
larger than the set examined, and when it is, a clean result is not merely
unhelpful — it is a false claim with a number attached, which is the most
convincing kind. **Ask what the denominator COUNTED, not just whether one is
printed.**

**AND A TRUNCATION IS A ZERO WITH THE SAME PROBLEM: IT READS AS A FINDING.**
Same morning, and it cost the longest wrong turn of it. The workflow step that
extracts the character lines into the verdict ended `| head -3`. That was
correct when a build produced one audit line and two prefab lines. The moment
the cast grew to eight bodies it produced seventeen — and the verdict showed
Michelle, Remy and nothing else.

I read that as *three of the five bodies failed to produce a prefab* and went
looking for the bug in `CharacterPrefab`. `bodyChoices=5`, in the same file,
had been right all along. Nothing was broken; a filter had quietly stopped
telling me things and there was no way to tell that from the output.

**The rule is rule 3b's, one layer out: any cap on what gets reported must say
when it bites.** `tools/verdict-characters.sh` prints `(+N more character lines
not shown)` and prints a count of log lines examined when it finds nothing, so
"the audit did not run" and "the audit ran and had nothing to say" stop looking
identical. A cap nobody is told about is indistinguishable from a finding, and
it is worse than a zero, because a zero at least looks like a number somebody
should check.

This is rule 5b's sibling. 5b says a guard must be run against the case it
should PASS. This says a guard's PASS must be legible as a pass rather than as
an absence.
