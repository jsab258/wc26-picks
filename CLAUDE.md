# CLAUDE.md — how to work on LEDGER

Read this first, every session. It is not style guidance. **Every rule below
exists because it was broken, and the incident is named so the rule is
believable rather than decorative.**

---

## 1. Never assert what you have not just checked

The single most expensive habit. Four separate incidents in one day.

- I told Jafar the four Lena voice candidates were four different people. They
  were one person four times. **I had read my own code comment instead of my
  own code** — the comment said "sharing a voice defeats casting" and meant it
  about a different axis.
- I told him the Mixamo character drop was the biggest open blocker in the
  project and he should go do it. **It had shipped the day before.** I quoted a
  "STILL OPEN" list dated three days earlier from the middle of a 1,500-line
  file.
- I reported a re-run was in progress that I had never issued.
- I said 30 clips came from the wrong corpus and wrote a commit deleting them.
  They came from the right one.

**The rule.** Before stating a fact about this repo — what exists, what is
wired, what shipped, what a number is — run the command that proves it, in the
same turn. A memory of having checked is not a check. If you cannot check it,
say "I have not verified this."

**Corollary: your own comments and docs are not evidence.** Read the code.

**Second corollary: when you change code, you have changed the comments about
it.** Four in one night, each true when written and quietly false afterwards —
and every one of them misled somebody, usually me:

| said | reality |
|---|---|
| `actions/checkout`: "Nothing here pushes" | I had just added a step that pushes. It failed six times and reported success. |
| `NpcWalker`: a name is "not there at all across the road" | Full at 4m, visible at 11m, while talking range is 3m. |
| `TrafficHost`: "sixteen blocks; a dozen or so reads as a working district" | Written when the game was one district. There are seven. |
| `Tier2Batch`: "never brighter than the cast" | Nothing enforced it, and the crowd used a brighter value than the other spawner. |

A comment is a claim with no test attached, so it decays silently and the decay
is invisible in a diff that does not touch it. **Before finishing a change,
re-read the comments on everything it touched — including the ones you did not
edit — and grep for the claim you have just falsified elsewhere.** The
`persist-credentials: false` comment was eleven lines above the step I broke.

**Third corollary: WHEN YOU FIX A BUG, GREP FOR THE SAME BUG.** The corollary
above is about comments. This is about the fault itself, and on 4 August it was
the single most repeated mistake of the night — three times, each time within an
hour of writing down that it happens:

| fixed | the twin I did not look for |
|---|---|
| `SpeechBubble`'s billboard aim | `NpcWalker` had the identical maths, and its own paragraph admitting nobody had grepped for the second site |
| `verdict-keys` reading a verdict from a build that never ran | `gates.py` counted those same blanks as five quiet runs and moved three gates from live to quiet |
| `TightestGap` measured in 3D against a flat 2.5m radius | the job trace I had written an hour earlier to diagnose it had the same mismatch |

The shape is always: one idea, two implementations, and the one nobody looks at
is the one missing a line. It is not forgetting — I wrote the rule into three
commit messages that night and walked into it anyway. **The fix is mechanical:
the moment a fix works, grep for its distinguishing token** — a method name, a
constant, a string marker — and read every other hit before moving on. The grep
takes ten seconds and each of the three above cost between twenty minutes and a
round trip.

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

## 3. Suspect the instrument first

Three times in one month the tool was the thing at fault:

- `breakrun.py` reverted one file of a two-file spec, so break N leaked into
  break N+1 and a SURVIVED could be reported as RED.
- The corpus diagnostic read 60 *consecutive* rows of a speaker-ordered dataset
  and reported on "the corpus". It had seen one person.
- `BarkGen` wrote its manifest to whatever directory the shell was standing in,
  so the tracked copy silently went stale.
- A gap analysis I ran said alarm propagation was unwired. Reading `NpcWalker`
  showed it already emitted. **The analysis was wrong, not the code.**

- The roadmap said M17.7 still owed "cornices, and doors as geometry". Both had
  been built for weeks, by `GroundFloor`, three lines apart — and I added a
  second door system to Core with four tests before reading it. The call site
  was four lines up in the output of my own grep. A second door would have
  landed on the same wall as the first.

**The rule.** When a result is surprising, check the ruler before the reading.
When your own analysis says something is missing, open the file and look.

**And a DOC saying something is missing is an analysis, not evidence.** The
roadmap is the tiebreak for what to do next; it is not a report on what the
code contains, and its "still open" lists decay exactly like comments do. Grep
is not enough either — grep found the call site and I read past it. Open the
function.

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

## 4. Open the artifact you are shipping

The listening page was published with **six faults**, all invisible from the
Python that generated it and all found in the first sixty seconds of actually
loading it: no viewport tag, no picking UI at all, a fixed bar sitting on top
of the controls, a row that cast a vote when you pressed play, a page that
scrolled sideways, and a `\n` in a non-raw string that killed every control on
the page. Then the *standalone* build silently dropped the speaker ids — the
page published as the fix for "you can't tell these apart" was the page you
could not tell apart on.

**The rule.** If the deliverable is a page, open it in a browser at the size it
will be used. If it is audio, check its duration and metadata. If it is a file,
read it back. `tools/voice-fetch/page_check.py` does this for the listening
page; write the equivalent for anything new.

**ALL of it, and never the gate INSTEAD of the artifact.** Every build commits
four stills. Three separate faults have now been found by a human opening one
of them and none by a gate: a hand lookup that could only see one body tier, a
white capsule drawn over the bought body, and that body lying flat on its back
in the road. In the third case I opened the NIGHT frame to check a window
question, read `playerPrimitive=False` off the done-line, and called the body
confirmed — while the noon frame in the same directory showed it on its back,
magenta. My own checkpoint had said *"LOOK at review_day1_noon.jpg and confirm
a skinned figure"*, and I substituted a passing number for the instruction I
had written myself.

A gate reports what it was built to ask. All twenty in `SimDirector` ask about
what a system ADDED — is it there, is it the right size, did it bind — and not
one asked what the frame LOOKS like, which is why all three faults sailed
through green. So: **read every still, every build, before reading any gate,
and never let a green reading stand in for the frame it claims to describe.**
When a still shows something wrong, the fix is a NUMBER that would have caught
it — `playerPrimitive`, `bodyUp`, `collidingNames` all exist because a picture
found what nothing was measuring.

**And then: LOOKING IS NOT MEASURING.** The night the sim first committed
screenshots, I opened them and condemned four correct things off the back of a
1280x720 JPEG:

- three textures as "off-brief" — rust-red asphalt, mossy paving, ochre brick.
  `SurfaceSpec`'s noir tint had already stripped every one of them. The render
  disagreed with the source files I had judged them from.
- a bench as a sign board mounted wrong. `Plate` was correct and always had been.
- the new vehicle wheels as oversized. Printed, they came out at dia/hi 0.40 and
  dia/len 0.14 for a car — within a few percent of a real one.

Each time I was one step from re-picking assets or "fixing" working geometry.

A picture is excellent evidence that something is WRONG and poor evidence of
WHAT or WHY. It has a resolution, a compression artefact and a palette, and at
street distance in fog those hide more than they show. So: a visual judgement is
a HYPOTHESIS. Before acting on it, make the run print the quantity — the tiled
colour, the ratio, the dimension — and read that. Every one of the four
reversals above was settled by a number in under a minute, and three of them
would have cost a CI round trip and a wrong commit.

## 5. Look before you destroy, and make the guard know the difference

- A cancelled CI run committed its empty output directory and **deleted 24
  clips Jafar had already listened to and picked from.** The step reported
  success.
- The guard I then wrote refused any run producing fewer clips — and would have
  thrown away the *corrected* set for being smaller. A guard that cannot tell a
  regression from an improvement is a ratchet.
- `rm -rf ../../voice-candidates/*` in CI deleted sixteen characters' clips on
  a run that was only asked to fetch three.

**The rule.** Before any delete or overwrite, look at what is there. Scope
destructive commands to exactly what the operation produced. Guards check
*whether the thing succeeded*, not just whether a number went down. And copy
anything a human spent time on somewhere the pipeline cannot reach —
`game-design/picked-clips/` exists for exactly that reason and it paid for
itself within the hour.

## 5b. A guard must be tested on the case it should PASS

Four in one day, and every one of them blocked the good case rather than the
bad one:

| guard | blocked |
|---|---|
| build-ordering by git ancestry | the checkout is shallow, so the test could never succeed and the NEWEST run stopped publishing stills at all |
| `queue-check`'s standing-work test | matched `## Standing rules`, a section about how to use the queue, and certified the backstop it existed to demand |
| the anti-double-spend gate | skipped the paid step correctly, then let the step that COMMITS its output run anyway, fail, and kill the job before the work it was dispatched for |
| the enrichment audit | refused to commit unless every card passed, so a run that fixed 54 of 60 landed nothing |

Every one passed its failure case. Not one had ever been run against its
success case. And every one was reported as a clean exit by the step above it,
so the symptom was always "nothing happened" rather than "something broke".

**The rule.** A guard has two outcomes and shipping it means having watched
BOTH. Before committing one, run it against input it must ACCEPT as well as
input it must reject — and if the accepting case cannot be produced locally,
say so in the commit rather than assuming that half works. `Tier2Gen
--selftest` is the shape to copy: its first assertion is that a good card is
accepted, and that assertion is first precisely because the expensive failure
is a validator nothing survives.

**Corollary, and it is 5b's twin: A GUARD ALSO NEEDS A RUN IN WHICH THE THING
IT ASSERTS CAN HAPPEN.** Rule 5b is about the guard. This is about the world
you point it at, and on 4 August it was the single largest cause of red in the
project — three of the five intermittent gates, found by one table:

| gate | asserts | and the run |
|---|---|---|
| `allegiance` | the street hears about a poach | never poached anyone: the sim recruits Sam and Rocco, and dockside is Joey and Ferko |
| `disposal` + `accident` | being SEEN costs more than not being seen | picked the most crowded spot it could find, which on some runs has nobody in it |
| `perception` | somebody notices you loitering | loitered where 32 people GLANCED and nobody stayed long enough to notice |

Every one passes most of the time, because most runs happen to supply the
condition. That is what makes them dangerous: they fail rarely, for a reason
nobody has named, and rare unexplained red is what teaches everyone to read red
as noise. `tools/gates.py --flaky` exists to find them — it reads every kept run
and reports which gates have ever failed and how often, and it corrected me
within a minute of being written (I had called a 4-in-60 failure "a one-off").

**The fix is always to PLANT the condition, never to loosen the bound.** Set the
standing before pledging, learn the fact into the witness before telling the
lie, put a body at the crowded spot. A probe that only fires on a lucky run is
not a probe, and moving the bound to make it green is the thing rule 2 forbids.

**Corollary: a guard that cannot tell a regression from an improvement is a
ratchet** (rule 5). "Refuse unless perfect" throws away partial success, and
partial success is what real work looks like.

## 6. Built is not running

A gap analysis over 61 public Core APIs found **2 untested and ~40 with no call
site in the game.** Phases 2–4 of M16 were built, tested, and disconnected.
`Brandish` 0. `MayFrisk` 0. `Acquire` 0. `Misattribute` 0 — so the street could
only ever be right about who did it.

The same failure has hit the noise ring and the caption bar before: a system
built, plausible, and never once running.

**The rule.** A feature is not done when Core is tested. It is done when
something calls it and a gate proves the call happened. When you finish a
system, grep for its call sites before saying it is finished.

## 7. Estimates: name what dominates, or do not give a number

Wrong every time today. The causes were always the same two things:

- I benchmarked against a **broken** run (it was fast *because* it was
  cheating), and
- I did not check what was actually blocking — a run sat "pending" behind one
  of *my own* pushes three separate times.

**The rule.** Before giving an ETA, check the thing is actually running and
what is ahead of it in the queue. State what dominates the estimate (here: a
~28-minute CI round trip) and what could blow it up. If you do not know, say
so — that is a better answer than a number you will retract.

## 8. "I will come back to you" requires arming something

Said twice, and both times Jafar had to ask anyway. Ending a turn does not
schedule a wake-up.

**The rule.** If you say you will report back, start a background watcher in
the same turn that will fire on the condition (or a timeout). No watcher, no
promise.

## 9. Do not block yourself

Pushing a commit triggered a full 40-minute corpus fetch, three times, each one
queued in front of the run Jafar was waiting on. Once, the run that would have
*fixed* the problem was queued behind a run of the problem.

**The rule.** Know what your pushes trigger. Expensive jobs are opt-in
(`workflow_dispatch`), concurrency groups are scoped to the expensive job only,
and cheap checks never queue behind a stream.

## 10. Documents

Two failures, opposite directions, same day.

- The roadmap reached 1,525 lines of which ~85% was chronology, and I "audited"
  it by stamping a status banner on the top — certifying the mess.
- Then I over-corrected and split the plan into a second file, so you had to
  open two documents to find out what happens next.

**The rules.**
- Every doc in `game-design/` declares **LIVE / SPEC / LOG** in its first lines.
  `tools/docs-check.py` enforces it, plus: a LOG carries its date and says NOT
  CURRENT, a LIVE carries a verified date, a LIVE plan stays under 400 lines,
  and no LIVE doc contains a diary heading.
- **`roadmap.md` is the tiebreak and contains the plan itself.** Not a pointer
  to the plan. History goes to `roadmap-history.md`.
- A milestone entry is not a title. It states what is in it, why it sits there,
  **what done looks like as something measurable**, dependencies, and risk.

## 11. Scope: do the asked thing

Asked whether a macOS build was *possible*, I built the CI job. Jafar:
*"never asked for a mac build, only if it's possible."*

**The rule.** A question is a question. Answer it, and offer the work
separately.

## 12. If you cannot read the output, fix that before anything else

For one whole night I diagnosed this project by inference, because every
channel out of a CI job was blocked and I kept working around it instead of
repairing it:

- the log API returns a fixed ~4KB **byte** tail, so nothing mid-log is
  reachable and GitHub's own post-job cleanup fills that window every run;
- `get_check_run` returns the step summary EMPTY — and a comment in the
  workflow asserted that channel worked;
- artifacts are on a host this environment denies outright.

So three separate faults were diagnosed from a step's **duration** (2m10s of
retry sleep meaning six failed pushes) and from a branch that had not moved,
and a 291-byte artefact standing in for "the directory was empty". That is
divination, and I did hours of it before doing the ten-minute fix.

**The rule.** A blocked feedback channel is not an inconvenience to route
around, it is the highest-leverage bug on the board — fix it FIRST, and prefer
a channel this environment can definitely read. In this repo that means a file
in the repository. Everything since has been settled in seconds by
`game-design/sim-shots/`.

---

## Project mechanics you will otherwise learn the hard way

**The Game layer does not compile here.** Only `Core` does. Locally you get
`ledger/verify.py` — lint, ShapeCheck (Roslyn, reference-independent
diagnostics only), stale-anchor detection, 2,884 CoreTests, and break-runs.
A type error against a Unity API is invisible until the Windows CI build, which
takes ~28 minutes. **Batch Game-layer changes; never claim a phase is done on a
local green.**

**AND SHAPECHECK WAS DISCARDING SYNTAX ERRORS, WHICH IS THE OPPOSITE FAULT AND
THE CHEAPER ONE.** 4 August: a missing `+` between two adjacent string literals
in `SimDirector` produced `CS1003: Syntax error, ',' expected`, the build died,
the sim never ran, and the question that build was dispatched to answer came
back unanswerable. ShapeCheck had reported ZERO errors on that same file
seconds earlier.

The cause was an ALLOW-LIST: `if (!interesting.Contains(d.Id)) continue`, a set
of diagnostic ids somebody thought to add. That is right for semantic
diagnostics — this compilation has no reference assemblies, so most of them are
noise about types it cannot see. It is indefensible for SYNTAX, which is the
one class that needs no references at all and is the cheapest, most certain
thing a parser can say.

Syntax diagnostics now come from the TREES rather than the compilation:
`SyntaxTree.GetDiagnostics()` returns exactly the parser's own errors, by
construction, with nothing semantic mixed in — no list to maintain and nothing
to forget to add. Tested both ways, and the rejecting case is the real error
put back: it lands on the same line and column CI reported.

The lesson generalises past this file. **An allow-list silently discards
everything nobody thought of, and it looks identical to a clean result.** That
is rule 3b — a zero needs a denominator — wearing a filter's clothes.

**AND "REFERENCE-INDEPENDENT" IS THE PART THAT BITES.** ShapeCheck can run here
precisely because it does not need the assemblies — which means every diagnostic
that requires RESOLVING a name is invisible to it, not just Unity ones. Five
have now each cost a round trip, every one about a name that exists somewhere
other than where it was written:

| | | |
|---|---|---|
| CS0119 | `EvidenceHost.Watched` shadowed `Core.Watched` | `tools/lint-shadow.py` |
| CS0426 | `Mixing.Bus` — `Bus` is a SIBLING of `Mixing`, not nested | `tools/lint-nested.py` |
| CS0120 | a static body reaching an instance member | `tools/lint-static.py` |
| CS0103 | `TrafficHost.BrakeLampsPeak` — **there is no type called `TrafficHost`** | `tools/lint-filetype.py` |
| CS0118 | `Game.Campaign` in a static class — `Game` bound to the NAMESPACE | `tools/lint-namespace.py` |

The fifth is the family's purest form and cost two builds. Inside
`namespace Ledger.Game`, the bare identifier `Game` resolves to that namespace,
so writing `Game.Campaign.Noted(...)` in a class with no `Game` member compiles
the sentence against `Ledger.Game` and fails with "is a namespace but is used
like a variable". `PlayerController` has a real `public GameController Game`
field, which is why the shape reads as normal — and is also the accepting case
any lint for it must pass. The tell is unmistakable and greppable: a namespace
can never be compared to null, so `Game != null` in a file that declares no
`Game` member is the error every time.

The last is the cheapest of the four and the most embarrassing: `TrafficHost.cs`
declares `partial class GameController`, and so do thirteen other Game-layer
files. I took a type name off a FILENAME without opening the file. Measure
before writing the rule — fourteen files in that folder declare no type of
their own name, so it is a systemic trap rather than a slip.

These tools are name-matching rather than type-resolving, so they get written
twice: the first CS0426 version flagged thirteen call sites that compile
perfectly. **The live codebase is the accepting case and it is the best one
available — every hit on today's code is a false positive by definition**, so
the check needs no fixture to be trusted and cannot be fooled by one I wrote.
Run any new lint of this kind against the whole repository before believing it.

**AND RUN IT AGAINST THE ERROR IT WAS WRITTEN FOR, WHICH IS THE HALF THAT GOES
UNRUN.** `lint-filetype` passed the whole repository and then scored ZERO on the
very line that prompted it. The name was in the trap set, the pattern was right,
and the reference never reached either — because it lives inside `$"..."` and
the stripper removed every double-quoted run wholesale.

**`$"..."` IS CODE.** `SimDirector`'s done-line is one interpolated string
hundreds of expressions long and is the largest concentration of Game-layer
static reads in the project. `lint-shadow` had been throwing all of it away
since it was written, with a docstring approving of it — *"a verdict line with
`Traces.` in it is prose that happens to be quoted"*, which is true of a plain
string and false of an interpolated one. Every CS0119 in the done-line was
invisible. One idea, two implementations, and the second was found only because
the rejecting case was actually run.

**THE COST IS NEVER THE ERROR, IT IS THE COMMITS ON TOP OF IT.** CS0426 landed
and three more Game-layer commits went out before the verdict came back, so
three separate answers each moved a round trip further away. When a build comes
back `NO PLAYER LOG`, stop dispatching and fix it first.

**MEASURED PROPERLY ON 4 AUGUST, AND IT IS MUCH WORSE THAN THREE.** One wrong
type name — `TrafficHost.` for `GameController.` — rode **18 commits and killed
4 consecutive builds**. Every one of those builds was dispatched to answer a
different live question: whether the texture extraction worked, whether foot IK
ran, whether the typography change landed, whether the loiter guard held. All
four came back `NO PLAYER LOG` and answered nothing.

The multiplier is auto mode itself. Dispatching in parallel is right and it
means a compile error is not one lost round trip but every round trip until it
is noticed — and `NO PLAYER LOG` looks identical whether the cause is a compile
error or a licence seat, so the instinct is to blame contention and dispatch
again. **Read the COMPILE ERRORS block in the verdict before re-dispatching. It
is printed there for this exact case.**

**You can SEE and READ the game — use it.** Every Windows build commits four
stills and a verdict to `game-design/sim-shots/`, overwritten each run:

    review_day{1,2}_{noon,night}.jpg    what the street actually looks like
    verdict.txt                         the done-line, FAILING GATES, the sky
                                        readings, the places line, glyph and
                                        wardrobe counts, wheel proportions
    runs/<sha7>.txt                     the same verdict, kept per commit

`git pull` and read them. Do NOT try to tail the job log — see rule 12. The
verdict is committed, so `git log -- game-design/sim-shots/verdict.txt` gives a
HISTORY of measurements: that is how the AO ceiling was shown to be sitting
inside its own instrument's noise across five runs. Adding a number to that file
costs one line and pays for itself the first time a gate fails.

**DISPATCH BUILDS IN PARALLEL — BUT NOT MORE THAN ABOUT THREE.** The Windows job
is `workflow_dispatch` with no concurrency group, so nothing queues it, and that
is how a day of serial hypotheses turns into two waves. The limit is not the
runner, it is the **Unity Personal licence**: on 4 August, four builds dispatched
inside twenty minutes and **two of them died on "Activate Unity license", five
seconds in**, contending for a seat.

That failure is expensive out of all proportion because it is SILENT in the only
channel that can be read here. The job still commits a verdict, the verdict says
`NO PLAYER LOG — the sim did not run on this commit`, and that reads exactly like
a Game-layer compile error — the one class of fault that cannot be checked
locally. I read my own correct C# for several minutes before checking the step
list. The activation step now retries once after a pause, and the verdict names
both attempts, so the next occurrence is a line rather than a search. Five round trips on the
upside-down player cost two and a half hours because I sent one question at a
time when I could have sent three. Each run keeps its own `runs/<sha7>.txt`, so
concurrent builds are concurrent ANSWERS rather than one answer overwriting
another.

**`verdict.txt` is the last run to LAND, which is not the newest commit.** Two
builds ran together and the one on the older commit finished second and laid
its output over the newer one's — so the file everything treats as "latest"
held the stale answer, and only the sha on line one said so. Runners here vary
by twenty minutes, so dispatch order tells you nothing about landing order. The
workflow now keeps whichever verdict came from the newer commit and lets the
loser contribute only its `runs/` file. **Check the sha on line 1 anyway**, and
when you dispatched a specific question, read `runs/<sha7>.txt` and not the
default.

**AND A BUILD THAT RENDERED NOTHING STILL COMMITS STILLS — ITS OWN CHECKOUT'S.**
The newer-wins rule above fixed which run's answer survives. It did not fix
what a run is allowed to claim as its answer, and on 4 August that cost the
morning. A build on `c61047f` came back `NO PLAYER LOG` with three compile
errors and its commit — "Sim stills from c61047f" — replaced all six JPEGs and
rewrote `frames.tsv`. It cannot have rendered anything. `git add
game-design/sim-shots` carried the directory it had CHECKED OUT, seven commits
behind the tip, so the branch went backwards and the frames landed indexed
under the sha of the build that failed to make them. **I opened all six and
read them as evidence about that commit.** The `verdict-keys.json` exclusion
was this same fault found earlier on one file, and excluding one file was too
narrow: "everything in the directory" is not a description of what a run
produced. `tools/sim-shots-stage.sh` now names the output — always the verdict
and the per-run copy, the stills only if the sim reached a screenshot, the
ledger only if it wrote one.

So the still-reading rule gains a first step: **read line 1 and the `NO PLAYER
LOG` line before looking at any frame.** A picture in this directory is only
evidence about the commit named beside it if that commit ran.

**Always run `ledger/verify.py` before committing, and PASTE THE FOOTER FROM
THE FILE.** A green run writes `ledger/.verify-footer`; a red run deletes it.

    python3 ledger/verify.py && git commit -F - <<EOF
    ...
    $(cat ledger/.verify-footer)
    EOF

**AND WRITE THE MESSAGE TO A FILE, NOT INTO AN UNQUOTED HEREDOC.** Twice now a
message containing a `backticked` identifier has been fed to `<<EOF` and the
shell has EXECUTED the word, committing a sentence with a hole in it — the
second time inside a paragraph about instruments quietly losing information.
`<<'EOF'` quotes it, but then `$(cat ledger/.verify-footer)` does not expand
either. So: write the prose to a file with no shell in the loop, `cat` the
footer onto the end, and commit with `-F`. Both halves work and neither can eat
a word.

It exists because I put unmeasured test counts in two commit messages, and the
FILE exists because printing "NOT GREEN — do not paste this into a commit
message as if it were" underneath the footer did not stop me doing it a third
time. The message gets written before the check finishes, from a footer already
in the scrollback, and a warning printed afterwards cannot reach a decision
already made. Paste from the file and a red run has nothing to give you.

**HuggingFace and most external hosts are blocked from this container** (403
through the proxy). Anything corpus-related must go through CI, so make each
run maximally informative rather than a single blind attempt.

**Verify a workflow's effects, not just its exit code.** A CI job here has
reported success while: deleting the clips, pushing nothing, producing zero
output for every character it was asked for, and committing a truncated log.

**Branch:** `claude/game-dev-ai-automation-2h67ix`. Never open a PR unless
asked. Never make a purchase or use an account — every purchase is Jafar's.

**Voice sourcing consent rule:** only corpora whose contributors donated their
voices to build speech technology, and **no identifiable public figures, ever.**

---

## AUTO MODE

Jafar's name for it. He will say **"start auto mode"** or **"stop auto mode"**,
and both must work from a cold session — which is why this is here and not only
in a trigger prompt. The container is ephemeral; a file in the repository is the
only thing that survives it.

**What it is.** Continuous autonomous building, around the clock, with a short
plain update six times a day. Not a cycle. Not a cadence. Jafar's words, after
I got it wrong twice: *"non stop, no idle time."*

### Starting it

1. Enable the watchdog: `update_trigger` on **`trig_01EA7ybQTcsiFyrTryptqVUi`**
   with `enabled=true`. Its prompt carries the current work order — read it
   rather than re-deriving one.
2. Begin working immediately. Do not wait for the watchdog to fire; it is not
   the thing that drives the work.
3. Arm something before the turn ends (see below).

### Stopping it

1. `update_trigger` on the watchdog with `enabled=false`.
2. Kill any background watchers (`TaskStop`, or `KillBash` on a running poll).
3. Delete any pending `send_later` with `delete_trigger`, or it will wake the
   loop after you were told to stop.
4. Confirm the working tree is clean and pushed. Auto mode assumes it can be
   interrupted at any moment, so it must never hold uncommitted work.

All three steps matter. Disabling the cron alone leaves a background watcher
that will re-invoke the loop, and it will look like the stop was ignored.

### The four rules that make it continuous

**1. Work until genuinely blocked, not until one task is done.** A turn can
carry hours. Finish something, pick up the next thing, keep going.

**2. Never wait on CI.** Only the Game layer needs the ~28-minute Windows round
trip. Core, CoreTests, the measurement tools, the docs and every Python tool run
here in seconds. Dispatch the build and start the next non-CI item in the SAME
turn. A build in flight is a reason to switch tasks, not to stop.

**`game-design/queue.md` is what you pick up.** This rule was already written,
in these words, and I broke it four times in one afternoon — twenty, thirty-two,
nineteen and twenty-eight minutes of nothing landing, each one right after a
dispatch. The rule was not forgotten; the problem is that *the moment after a
dispatch is a decision point*, and re-deriving priorities from a 400-line
roadmap at the end of a long turn is enough friction to lose to. So the next
items are written down BEFORE the dispatch and taken from the top afterwards,
with no judgement required at the exact point where judgement was failing.
Keep it current: a stale queue is worse than none, because it looks like a plan.

**AND IT MUST NOT BE ABLE TO EMPTY.** The queue fixed the gaps for exactly one
hour — eighteen commits, longest gap eight minutes — and then produced three
more of 21, 28 and 28 minutes. Not because the rule was forgotten. Because the
queue RAN OUT, and its own instruction guaranteed it would: *every item sized to
fit inside one build round trip* means an hour of good work consumes the list.
An empty list reads exactly like an empty afternoon, and the two have completely
different next actions.

So: a `## Standing work` section that never empties — unbuilt milestones, a
system to read for false comments, a still to turn into a number. When `## Now`
has nothing startable, **decompose a standing item into it. That is a refill
signal, not a stop signal.** `tools/queue-check.py` runs inside `verify.py` and
fails the commit when fewer than three items can be started without waiting on
CI, so the queue running thin is something you are told before it costs an hour
rather than something you notice afterwards.

**3. Be woken by the event, not the clock.** Arm it with Bash
`run_in_background: true`, which re-invokes you within seconds of it exiting.
**Watch for a build that CONTAINS the commit you care about** — not for the
branch to move, and not for a run named after the sha you dispatched:

    SHA=$(git rev-parse HEAD)
    for i in $(seq 1 100); do sleep 30
      git fetch -q origin claude/game-dev-ai-automation-2h67ix 2>/dev/null
      git merge-base --is-ancestor "$SHA" origin/claude/game-dev-ai-automation-2h67ix 2>/dev/null \
        && git pull -q --no-rebase origin claude/game-dev-ai-automation-2h67ix 2>/dev/null
      python3 tools/landed.py --contains "$SHA"; rc=$?
      [ $rc = 0 ] && exit 0          # landed WITH an answer
      [ $rc = 3 ] && exit 3          # landed with NOTHING — re-dispatch, do not wait
    done; echo "timed out"; python3 tools/landed.py --contains "$SHA"

**EXIT 3 IS NEW AND IT IS THE ONE THAT WAS COSTING HALF-HOURS.** A build whose
licence activation fails, or whose Game layer will not compile, still commits a
verdict — so the ancestry test says LANDED, correctly, and the old recipe
reported success. On 4 August I read one of those as an answer and went looking
for numbers that were never written. "The build carried your change" and "the
build measured anything" are different facts, and only the second is what a
watcher waits for. `landed.py` now separates them, and prefers the newest run
that MEASURED something over a newer one that did not — the first version
returned on the newest containing run whatever it held, which hid an available
answer behind an empty build the very first time it was tested.

**BOTH OBVIOUS VERSIONS ARE WRONG AND I SHIPPED BOTH INTO THIS FILE.**

The first watched `git ls-remote` for the branch head to change, reasoning that
the job commits stills so the branch advancing IS the build landing. True when
nothing else is pushing. In auto mode I push constantly, and it fired forty
seconds later on MY OWN COMMIT while the verdict still named the previous build.

The second — the one that stood here until 4 August — matched the verdict's
first line against the sha I dispatched. That fixed the forgery problem and
introduced a quieter one: **`workflow_dispatch` does not pin a commit.** It
takes a BRANCH, and the runner checks out whatever that branch points at when
it STARTS. Push twice in the ten minutes a job waits for a runner and it builds
the third commit, not yours.

Measured, not suspected: four builds dispatched at `aa0e906`, `d5b3741`,
`bdcbe3f` and `69e03a6`, and **not one of those four shas was ever built**. The
runs that came back are named after later commits, two of them made by the CI
job committing its own stills. Every watcher armed on those four was waiting
for a file that could not appear — and none of them looked broken, because they
had fired correctly on earlier runs where HEAD happened not to move. A watcher
that works often enough to look right is worse than one that never works.

The question was never "is there a run named X". It is **"is there a run whose
commit CONTAINS X"**, which is an ancestry test and cannot be forged by my own
pushes either: my commits are not descendants of themselves-plus-CI's-work
until CI does the work. `tools/landed.py --contains` is that test, and it names
which run answered so the next step does not need a second lookup.

Cap it around 50 minutes so a dead run cannot hang the loop. If something else
blocks you, `send_later` goes down to one-minute granularity.

**4. Never end a turn without arming something — AND ARMING IS NOT ENDING.**
No watcher, no `send_later`, no pending work means the project has silently
stopped. This is rule 8 with a mechanism attached.

But arming a watcher is the *precondition* for ending a turn, not permission to
end one, and reading it as permission is what survived both repairs. Measured
after the second fix: nine commits in seventy-four minutes with gaps of 2, 5, 3,
**30**, 12, 1, 10, 11. The thirty was a dispatch, a watcher, and a stop — with
four standing items sitting unused on the queue.

So the mechanisms built for this solve the wrong half. `queue-check` guarantees
work is AVAILABLE; nothing can make it be CONSUMED, because no check inside
`verify.py` can see a turn boundary. Availability was never the binding
constraint.

**The rule, and it is a rule because it cannot be a tool: a turn ends only when
nothing is startable.** With a standing section that cannot be completed, that
state does not exist — so after arming a watcher, open `queue.md` and start the
next thing in the same turn. Every time. The watcher is what makes the result
reachable later; it is not the work.

### Jafar asked why twenty-four hours looked like almost nothing

4 August, and he was half right, which is the half that matters. Measured
before answering rather than after: **347 commits and 133 builds in the day**,
so the loop was not idle. And **about a third of those commits were about my
own MEASUREMENTS being wrong rather than about the game**, and **7 of the last
30 builds returned no answer at all** — a compile error or two builds fighting
over the same Unity licence seat, half an hour each, nothing to show.

The one thing he could actually see took the whole day to arrive: the street
went from smooth featureless dummies to people with skin, clothes and a walk.
Everything else was invisible to him, and a lot of it was invisible because it
was me arguing with my own instruments — one nameplate counter has now given
four contradictory readings and no player will ever see it.

**Four rules follow, and they are his, not mine.**

**1. BATCH THE BUILD.** Several changes per dispatch, not one question per
dispatch. A round trip is ~28 minutes whether it carries one change or six.
And **ONE AT A TIME**, which is where the evidence has now landed. The licence
seat is a single Personal activation, and every level of concurrency has cost a
build: four dispatches killed two, three killed one, and TWO killed both —
15:23 on 4 August, `c7329a3` and `2cfe851`, each reporting "first licence
attempt: failure, second: failure". That is three data points in one direction
and none the other way.

Parallel dispatch was never wrong about the goal — it was answering "how do I
stop waiting half an hour per question". Batching answers that better and
costs nothing: six changes in one build is one round trip, six builds is six
chances at the seat. So the two rules are a pair, and the batching one is what
makes this one affordable.

**2. A MEASUREMENT THAT CONTRADICTS ITSELF TWICE GETS DELETED, NOT EXPLAINED.**
The rule this replaces was "measure again with a better instrument", and it is
how one counter consumed four round trips. The second contradiction is the
signal: at that point the cheapest correct move is to delete the number and
keep the behaviour fix, because a metric nobody can interpret is worth less
than the hours it takes to interpret it. Exception, and only this one: the
number is load-bearing for a gate that is currently red.

**3. ORDER THE QUEUE BY WHAT SHOWS ON SCREEN.** Not by what is open, not by
what is nearly finished, not by what I happen to be holding in my head. The
standard is immersion first, so the top of `## Now` is the item a player would
notice, every time. Everything else is below it whatever its state.

**4. EVERY REPORT CARRIES A PICTURE.** He asked "is it just not visible to me"
about a day whose single biggest change is a JPEG sitting in the repository. A
report that describes the street without showing it is making him take my word
for the one thing he can check himself. Send the noon frame with the update —
and where something changed, send the before beside it.

`tools/report-frame.py` finds both, because a rule that depends on remembering
to go and look is a rule that decays and this file is mostly a list of things
that decayed. It walks back to the last commit whose verdict says a sim
actually RAN — a build that died on a licence seat still commits, and one on 4
August committed six stills it could not have made — and it refuses to hand
over a frame rather than offering a stale one. Tested both ways: it finds the
pair on today's repository, and with the verdicts hidden it says do not attach
a picture, say the build produced nothing.

### Why the cron is only a watchdog

**I built the loop wrong twice and the second version sounded reasonable.** The
first was a three-hour cycle. The second was hourly, and I justified it as
"matched to the CI round trip" — it was matched to nothing, and left up to
fifty-nine minutes of idle per hour. Jafar: *"why hourly? i said non stop, no
idle time. there must be a better way."*

The root cause is worth remembering because it will recur: **cron's minimum
interval is one hour**, so I designed around the limit of the tool I had picked
instead of noticing it was the wrong tool. The work is driven by the event chain
above. The cron exists for exactly one case — the chain dying (container
reclaimed, a turn erroring out, a watcher lost) — and restarts it. Without it,
one bad turn ends the project silently.

### Reporting

Six times a day, daytime only: **07:00, 10:00, 13:00, 16:00, 19:00 and 22:00
CEST** — UTC hours 05, 08, 11, 14, 17, 20. Run `date -u +%H` and check before
writing anything. Every other firing works in SILENCE and ends with no
user-facing message. The 07:00 report is the overnight summary.

**It opens with a header line so it can be FOUND**, then five to seven short
plain sentences:

    **LEDGER — 16:00** *(update 4 of 6)*

Then: what got done; where we are on the roadmap (read `roadmap.md`'s screen
table — do not recite from memory, and fix it if it is wrong before quoting it);
what is next; what decision is needed from Jafar, or "nothing needed from you".
Lead with anything visibly broken. **No code block, no template, no shas, no
metric names, no file paths.**

**The header exists because Jafar twice asked where an update was that had
already been sent.** Both times it was there and both times it read as more
conversation — I had followed the rule that it goes last with nothing after it,
which is right, and lost the signal anyway because nothing marked it. A report
he cannot find when scanning back is a report that did not happen, and the fix
is one line rather than more words.

He has said twice that updates were too long and too technical, and once that a
report was buried mid-message and he never saw it. Say *"the player is upside
down"*, not the name of the metric that measured it.

---

## The standard

Jafar: *"it has to be EXCEPTIONALLY GOOD from a game feel and UI/UX point of
view. we don't ship low quality / AI slop here."*

And the framing every plan is judged against: unmistakably deeper than KCD2
while looking unmistakably worse, and at peace with that trade. The moat is
social memory 93, consequence persistence 95, information 90 — against a
best-in-class of 60, 85 and 65. Everything else is in service of it.
