# Casebook: claims, artifacts and guards

STATUS: LIVE. Verified 2026-09-01.

These passages were the bulk of CLAUDE.md until 2026-09-01, when task 013 cut
that file to standing rules plus pointers on Jafar's finding that a
16,000-word file read at the start of every session is a file nobody holds in
their head.

NOTHING HERE IS ADVICE. Every rule below exists because a specific failure
cost a specific day, and the named incident is the reason the rule is
believable rather than decorative. That is why the incidents moved intact
instead of being summarised: a rule with no incident attached decays into a
slogan people read past, which is the failure this whole file is a list of.

The one-line versions live in CLAUDE.md. Read them there; read the incident
here when you are about to do the thing.

---

### Why every rule below carries an incident (the original preamble)

<!-- moved verbatim from CLAUDE.md lines 23-43 on 2026-09-01, task 013 -->

> **THE V2 RESPEC IS THE SOURCE OF TRUTH — 2026-08-31, Jafar.** The package
> at `ledger-v2/` (entry point `ledger-v2/handoff/HANDOFF.md`) supersedes all
> prior roadmaps, design docs and specs; on any conflict between this file's
> project-specific claims and `ledger-v2/`, the package wins. `canon.md` at
> the repo root outranks everything once Jafar approves it; violating canon
> is a gate failure, not a style note. Two laws the package makes binding:
> **the license allowlist** (`ledger-v2/research/license-allowlist.md`) is
> law — nothing ships that is not on it, new tools enter only via a decision
> record naming the weights license; and **the formatting law** — no
> em-dashes and no italic text in project documents written from 31 Aug on
> (this file's older text is corrected opportunistically, not rewritten
> wholesale, so the incident record keeps its original wording).
> The epistemics below — never assert unchecked, thresholds from printed
> series, every zero ships a denominator, open the artifact, guards tested
> both ways — are carried forward by the v2 constitution and remain in force.

Read this first, every session. It is not style guidance. **Every rule below
exists because it was broken, and the incident is named so the rule is
believable rather than decorative.**

---

<!-- moved verbatim from CLAUDE.md lines 45-71 on 2026-09-01, task 013 -->

## 0. WHAT LEDGER IS, because this file never said and I invented an answer

**A British port town, LATE-ANALOG — the eighties and nineties.** Landlines,
payphones, answering machines, cash, paper. No mobiles, no internet.

On 14 August I called it "a 1950s port town" four times in one conversation,
in a planning discussion, while telling Jafar which character models suited
it. He had corrected this "like ten times" before. The setting is stated
plainly in `design-doc.md` line 8 and DECIDED in `agency-model.md`; I had
also read the phrase "the setting is LATE-ANALOG, the eighties and nineties"
in the voice fetcher THAT MORNING and quoted it back in my own commit.

So this was not a stale document or a forgotten decision. Every source was
correct and I asserted over all of them — rule 1, applied to the premise
rather than to a fact, which is worse: a wrong number gets caught by the next
measurement, and a wrong PREMISE quietly re-frames every judgement made on
top of it. I was about to plan an art pass around the wrong decade.

It is at the top of this file because the fix for "remember it finally" is
not remembering. Everything below is a rule about process; nothing said what
the game was, so nothing I read every session could contradict me.

Two more that belong with it, for the same reason:

- **Nothing is purchased.** Characters and animations come from Mixamo with
  Jafar's account and a token he supplies. When something is missing the
  answer is to fetch it, never to price it.

<!-- moved verbatim from CLAUDE.md lines 84-155 on 2026-09-01, task 013 -->

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

**AND A COMMENT DOES NOT ONLY DECAY — IT IS QUOTED FORWARD, WHICH IS WORSE
BECAUSE NOBODY EVER TOUCHED IT. 26 Aug: "`UpdateSun` puts the noon sun due
SOUTH".** Measured, it is `Euler(52,180,0)` -> sunward `(0,+0.788,+0.616)`:
the noon sun is in the NORTH, so in an axis-aligned town only north-facing
walls are ever lit. That one sentence had been copied into **four documents
and five camera placements**, and every camera reading `litnone@0` was aimed
at the shaded side because of it. The rule above catches a comment falsified
by an edit to the code beside it. **Nothing edited this one** — it was
re-quoted because it sounded authoritative, and each copy made the next more
credible. It was caught only because an instrument printed `litnone@0` and
somebody asked why. **So: grep for the SENTENCE, not the site.** When a claim
turns out false, the copies are not near the code it describes; they are in
whatever a later reader was writing at the time.

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

<!-- moved verbatim from CLAUDE.md lines 417-443 on 2026-09-01, task 013 -->

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

<!-- moved verbatim from CLAUDE.md lines 538-593 on 2026-09-01, task 013 -->

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

<!-- moved verbatim from CLAUDE.md lines 595-611 on 2026-09-01, task 013 -->

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

<!-- moved verbatim from CLAUDE.md lines 613-690 on 2026-09-01, task 013 -->

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

**AND THE SAME COROLLARY AIMED AT A READING IS WORSE, because a reading cannot
go red.** `tools/gates.py --constant` is `--flaky`'s mirror: it reads every kept
verdict and lists the keys that have NEVER been anything but zero. First run,
sixty of them across 131 runs — and one was `inquiry=None`, meaning the
detective has never once opened an investigation into the player in the entire
recorded history of this project. Everything gated on that stage has therefore
never executed: the paper naming you, the redirect having anything to relieve.
`summonsTaken=0` was another, and its cause was a `Public` flag set on three
phone lines, saved, restored, and read by nothing at all.

**AND THE INQUIRY HALF OF THAT IS NOW STALE, which is the paragraph proving
its own point. Read 24 Aug: `inquiry=Manhunt`.** The detective opens
investigations and escalates them to the loudest state the game has, so
"everything gated on that stage has never executed" would send the next
session at work that is already running. What is STILL zero is narrower and
more interesting: `summonsTaken=0` and `redirectRelief=0.00` sit at zero
while the inquiry reaches Manhunt — so the phone-line cause above stands and
the inquiry cause does not, and the two were being read as one thing.
(`findingKinds=none` is NOT part of this: it belongs to `SceneAudit`, where
`clean=True findings=0` is a fault counter doing its job. Checked, after
guessing otherwise.)

Most of what it prints is healthy — `errors=0` and `idLeaks=0` are fault
counters doing their job — and the tool cannot tell those from a branch nobody
has entered. **That judgement needs to know what the number is FOR, which is a
person's job. What the tool removes is the part a person cannot do: noticing
that a number never moved.**

**The fix is always to PLANT the condition, never to loosen the bound.** Set the
standing before pledging, learn the fact into the witness before telling the
lie, put a body at the crowded spot. A probe that only fires on a lucky run is
not a probe, and moving the bound to make it green is the thing rule 2 forbids.

**Corollary: a guard that cannot tell a regression from an improvement is a
ratchet** (rule 5). "Refuse unless perfect" throws away partial success, and
partial success is what real work looks like.

<!-- moved verbatim from CLAUDE.md lines 692-704 on 2026-09-01, task 013 -->

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
