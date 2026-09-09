# Ruling: the art lane's bootstrap, the board's two fields, and the sun the sky drowned

> **STATUS: LOG, 2026-09-09. NOT CURRENT.** Director ruling at spawn
> 2026-09-09T14:24:39Z on a three-piece batch: the derived PATH-bootstrap lint,
> the typed board's `short` and `where` fields with its attribution sentence,
> and `tools/frame-shadow-probe.py` with the light change it argues for. NOT
> CURRENT once the conditions in section 5 are met and the batch is committed.
> BUILDS ON: `game-design/decision-2026-09-09-ruling-typed-systems-inventory.md`
> (12:52Z), whose sections 4 and 8 piece B carries out. OVERTURNS one resident
> ruling, section 3a below.

VERDICT: A APPROVED AS IT STANDS. B APPROVED WITH ONE OVERTURN. C APPROVED IN
PART: the tool and its finding are accepted in full and the light change is
REFUSED AS A SINGLE GUESSED VALUE and ordered as a printed series in the same
dispatch.

## 0. What I could not run

NO BASH IN THIS SPAWN. I executed nothing: not `ledger/verify.py`, not
`tools/lint-bootstrap-single.py`, not its selftest, not `tools/map.py`, not
`tools/frame-shadow-probe.py`, not a grep. Every number in this record is the
builder's, printed in another session, and this ruling converts none of them
into a measurement. Section 5 turns the load-bearing ones into conditions on
the approval, which is the same device the 12:52 ruling used for the same
reason.

What I did instead was read, in full: `tools/lint-bootstrap-single.py`,
`game-design/decision-2026-09-09-ruling-typed-systems-inventory.md`,
`.claude/agent-log.tsv`. In part, at every line this ruling rests on:
`.github/workflows/ledger-art-blender-preview.yml` lines 1 to 132,
`ledger/verify.py` lines 1752 to 1789, `tools/frame-shadow-probe.py` lines 1 to
120, `tools/map.py` around 2253 to 2496, `ue-probe/.../VignetteShot.cpp` at
194, 662 to 699, 1064, 1236 to 1303 and 1464 to 1483,
`ue-probe/.../VignetteSpec.h` 237 to 251 and 423 to 439.

PREMISE CHECK, CLAUDE.md section 0. Nothing in this batch dates the world
anywhere but 1988 to 1992, nothing cites GTA V, nothing proposes a purchase,
no licence entry moves, and no tool enters. Piece C serves the visual half of
the Meridian Test directly: a street where nothing is seated on the ground is
a street a KCD2 player bounces off in the first thirty seconds. No conflict.

## 1. Piece A: approved as it stands, and the standard is now standing

APPROVED AS IT STANDS, no amendments. The bootstrap step sits at position 2,
after the studio checkout and before the first pwsh step, which is where the
script's own header says it must sit because it is a repository file. Both
halves of the fault are repaired in the same change, which is the part that
makes this more than a patch: the workflow now calls the shared script, and
the lint that was supposed to notice no longer reads a list of the workflows
somebody remembered.

What convinced me, in the order it mattered:

1. The third of the three reported runs is the one that counts. A lint that
   goes green on today's tree proves nothing about a fault that was invisible
   yesterday. The PRE-FIX tree going RED and NAMING `ledger-art-blender-preview.yml`
   is the run that says this instrument would have caught the twelve-second
   death, and it is the only run of the three that could have.
2. The derivation FAILS CLOSED in all three places it could have failed open:
   a bare `run:` step with no shell counts as needing the bootstrap because
   the Windows default is pwsh; a `runs-on` behind an expression or a YAML
   alias is reported as unresolvable rather than as not-self-hosted; and a
   workflow that declares jobs the reader could not parse is a problem rather
   than a clean zero. Fail-open is precisely how today's silence happened.
3. The block-scalar reader is not decoration. `ledger-build-windows.yml` has
   the sentence `self-hosted` inside a `run:` block for real, and the selftest
   holds an accepting fixture for it. A grep-based deriver would have replaced
   one wrong denominator with another.
4. `DERIVATION_FLOOR` keeps the hand list for the one job a hand list is good
   at, which is catching a parser that stopped seeing something, and rule 3
   is cited correctly in its comment: a floor workflow that vanishes accuses
   the deriver first.

THE STANDARD, and this sentence is the one a future session applies without
re-deriving it:

**A LINT DERIVES ITS POPULATION FROM THE ARTEFACTS IT CHECKS, NEVER FROM A
HAND-WRITTEN LIST OF THEM; A HAND LIST IS ALLOWED ONLY AS AN EXEMPTION (each
entry carrying a written reason, refused when it names nothing or has gone
stale) OR AS A FLOOR (a set the derivation must still find, so that a parser
regression cannot read as a clean tree), and never as the set being checked.**

It is standing from today, and it applies to every checker under `tools/`,
not only this one. Third denominator fault this week is enough evidence: the
failure is structural and not a lapse. A lint whose hand list IS its
population answers "did somebody remember" and reports it as if it had
answered "is the tree correct", which is rule 3b's fault with a tool around
it.

THE COST I AM ACCEPTING, named so nobody meets it as a surprise. An
unresolvable `runs-on` is now a RED that no exemption can clear, because
`EXEMPT` is consulted only for workflows the derivation already flagged as
needing the bootstrap. The first session that adds a matrix workflow will hit
a red that is not a bootstrap fault. THE FIX IS NOT TO LOOSEN THE BOUND: it is
to teach the reader that shape, or to give unresolvable jobs their own
exemption channel with its own written reason. Queue item A in section 6.

## 2. Piece B: approved, one resident ruling upheld and one overturned

APPROVED. `short` on ten entries and `where` on all 62 non-absent entries and
none of the 7 absent are what section 4 of the 12:52 ruling dictated, the
fixed-set loop is the single implementation that section 8 required, and the
false sentence is gone from the page. The rendered-bytes guard is the right
guard: a sentence computed from `typedBy` and parsed back off the bytes that
shipped cannot be quietly replaced by a hardcoded one, which is the exact
decay the sentence it replaced went through.

### 2a. Resident ruling 2, the collapsing date pair: UPHELD

Upheld, with both branches rung-tested, which is 5b satisfied on the accepting
case first. A pair reading `2026-09-09..2026-09-09` is a format the reader has
to hold in their head, and the pair earns its place only when it carries two
different days. Nothing is lost: the per-tile `typedOn` is one tap down.

### 2b. Resident ruling 1, the engine split moved off the first screen: OVERTURNED IN PART

The resident is RIGHT ABOUT THE PROBLEM and WRONG ABOUT THE FIX, which is the
default this studio applies to a finding, and it applies to a resident's
finding too. "C#", "UE", "Unreal probe" and "repo" are studio vocabulary and
they do not belong in front of Jafar. That is a real fault and I would have
made the same catch.

But the fix moved the FACT when the fault was the WORDS, and the fact is the
one that decides whether this page flatters. Section 4b of the 12:52 ruling
put the split on the first screen for a stated reason: 26 green tiles green in
a codebase Jafar is not looking at, with the engine decision still open, is
exactly the page the whole typing exercise existed to prevent. Moving it one
tap down reproduces that page with a better audit view behind it. Corner marks
alone are worse than either: a mark a reader can see and cannot decode is the
unreadable output of rule 12 on the one screen he reads.

RULED: THE FACT STAYS ON THE FIRST SCREEN, THE VOCABULARY CHANGES. The shape,
computed from the data exactly as the attribution sentence is, and guarded the
same way off the rendered bytes:

    26 tiles are green. 19 of them are read in one build only, 4 in both,
    none in the newer build on its own, 3 are about files rather than play.

Constraints on the wording, which are the ruling and not the prose: no
language name, no engine name, no repository word; every number computed from
`where` over the green tiles only and never typed in; the zero ships its
denominator; and the sentence may not say which of the two builds is better or
which one wins the open decision, because that decision is not this page's to
make. If no register-clean wording can be found that carries all four counts,
the fallback is the smaller true sentence on the first screen (how many green
tiles are read in one build and how many in both) and never the removal of
both. The precise words are the builder's; their presence above the fold is
not negotiable.

### 2c. What 19 of 26 means for how anyone reads the board's green

THE NUMBER GOES IN THIS RECORD BECAUSE IT EXISTED IN NO SESSION BEFORE TODAY:
of 26 green tiles, 19 are a reading of the C# game alone, 4 are measured on
both sides, NONE is the Unreal probe alone, and 3 are files and process.

Three consequences, and they bind:

1. GREEN MEANS "SOMEWHERE IN THE STUDIO'S TWO CODEBASES, USUALLY THE OLDER
   ONE". It does not mean "in the build that will be played". Anybody reading
   a count of green tiles as readiness of the thing Jafar will run is reading
   a number about a different artefact.
2. NO PHASE GATE MAY CITE A COUNT OF GREEN TILES AS EVIDENCE OF THE UNREAL
   SIDE, in any document, from today. The count that would support such a
   claim is `greenWhere` for the probe alone, and it is zero out of 26 with
   its denominator printed. A zero with a denominator is the cheapest
   protection this project has and it is now available for this question.
3. THE OPEN ENGINE DECISION IS NOT INFORMED BY TILE COLOUR AND MAY NOT CITE
   THIS PAGE. The board measures where work has been done, not where it should
   be done, and 19 to 0 is a statement about the studio's history rather than
   about either engine. A decision record that cites the board for this is
   citing its own past effort as evidence about its future.

The fourth consequence is the one for the ladder, section 6: `both` is 4 of
26, and `both` is the only value on that field earned by a measurement on each
side. The next rung of this whole aspect is that number going up, and it will
go up one parity row at a time.

## 3. Piece C: the finding is accepted in full

ACCEPTED, and it is the strongest piece of measurement work this studio has
produced. What makes it strong is not the conclusion, it is the CONTROL: the
same geometry, the same sun, the same direction, the same `SetCastShadows(true)`,
measured on a frame from one commit earlier, moving the shadow-edge step from
+0.0270 to -0.0003. That is a difference of one variable, and it is the only
kind of evidence that can tell "the light rig is wrong" from "shadows are
off", which no amount of looking at either frame could.

Four things I checked rather than took, and all four hold:

- The instrument was checked before the reading and against the engine's own
  numbers, three independent ways, which is rule 3 done in the right order:
  whole-frame mean 0.6717 against 0.6717 at delta 0.0000 over 921600 px, the
  control quads to within 0.42 px, and the skyline at a median of 0.0 px over
  1280 of 1280 columns. All three ship denominators.
- The builder CORRECTED ITS OWN INSTRUMENT mid-run, when the first
  face-orientation tally counted every hit pixel rather than only
  predicted-lit ones and read -0.0534 with 4 of 6 surfaces reversed on a frame
  that plainly has a sun. That is the single most valuable event in the
  report. An uncaught version of that error would have said "no sun" about the
  calibration frame and this ruling would be about the wrong thing.
- The ambient-occlusion answer refuses the flattering shape twice: it reports
  occlusion PRESENT but short-ranged (0.7080 within 15 cm at n=2010, 0.8386 at
  15 to 40 cm at n=371, 0.8738 at 40 to 100 cm at n=85), and it prints n=0 for
  asphalt inside 40 cm rather than a clean zero. A zero there would have been
  a false claim with a number on it.
- The reading of the code is a reading of the code. The sun spawns movable and
  shadow-casting at 1023, every piece sets `SetCastShadow(true)` at 639, and
  the intensity at 1240 is a bare literal `3.0f`, the only light in the file
  with no named constant, beside `kSkyIntensityDay = 1.0f` at 194. I read all
  four sites.

So queue 197's question is ANSWERED: it is the light rig. Shadow casting is
on, occlusion exists and is short-ranged, and the sun is invisible against the
sky that replaced its three fills.

### 3.1. Question 1: the factor of ten is REFUSED as a landed value, and ordered as a series

The naming is APPROVED unconditionally and is not the contested part: a light
whose intensity is the only bare literal in a file of named constants is a
number nobody can find, and the fault is real whatever the value turns out to
be.

THE VALUE IS REFUSED. Not because 30.0f is implausible, but because the run
that would justify it cannot distinguish three explanations, and one of them
is already printed in this repository and is missing from the builder's
argument.

THE THIRD SUSPECT, unnamed in the brief and named here.
`VignetteShot.cpp:1464` reads the camera's post-process settings back and
prints `tonemapRead=camera-postprocess-and-cvars` with
`ppAutoExposureMethod`, `ppAutoExposureBias`, the four `bOverride` flags and
four cvars, and its own note says
`ppNote=this-probe-overrides-nothing/cvars-are-what-is-in-force`. AUTO
EXPOSURE IS IN FORCE AND UNOVERRIDDEN. A tenfold sun raises scene luminance
and eye adaptation pulls the exposure back down, so the shadow-edge step,
which is a difference of lumas in a tonemapped 8-bit frame, can move very much
less than tenfold. A single shot at 30.0f that comes back flat is consistent
with all three of: the sun is still too dim, the skylight owns the exposure,
and the tonemapper ate the change. One dispatch, three surviving
explanations, which is the shape of the four-explanations night that ci.md
already has a rule about.

AND THE 3.0f WAS NEVER A MEASURED NUMBER EITHER. It was tuned against three
directional fills that no longer exist. Replacing 3.0f with 30.0f swaps one
unmeasured literal for another and writes a decision record around it. Rule 2
does not care which of the two is closer.

RULED: THE SAME DISPATCH PRINTS THE SERIES.

- The sun's intensity becomes a FIELD ON THE CONDITION in the shot spec, not a
  named constant in C++. `VignetteSpec.h:242` already carries `Condition` with
  `SunOn`, `Wetness` and `FogDensity` parsed by `NeedBool` and `NeedNum` at
  423 to 437, and `Shot` is already `{Id, CameraId, ConditionId}`. A
  `sun_intensity` field is one parse rung, one use at 1240, and N rows of
  data. Required rather than defaulted, so a condition with an unnamed sun
  intensity refuses loudly instead of inheriting a literal, which is the fault
  being repaired.
- The run renders ONE camera at a ladder of sun intensities spanning the
  builder's proposal and the engine's own default: 3, 10, 30, 100, 300. Five
  frames of an already-built street against one dispatch round trip, and
  ci.md's own rule is that the round trip costs the same carrying one change
  or six.
- ONE EXTRA SHOT TESTS THE SECOND SUSPECT ON THE SAME RUN, at sun 3.0 with the
  sky at 0.35, which is `kSkyIntensityNight`, a value already in use rather
  than one invented for the test. If the step comes back at 3.0 with a dimmer
  sky, the skylight owns the exposure and the answer is that `kSkyIntensityDay`
  comes down, which is the builder's own named alternative, decided by
  measurement in the same run rather than by a second dispatch.
- `tools/frame-shadow-probe.py` then prints the step per frame, and the
  constant is set FROM THE READ SERIES in a following commit. Ship the
  printer, read real runs, set the number, in that order.

THE PREDICTIONS STAND AS WRITTEN and are the acceptance criteria for the
ladder, now read against the curve rather than against one point: the step
must reach at least +0.027 somewhere on the ladder where it now reads -0.0035,
asphalt lit-minus-shadowed must go positive from -0.0131, and
`band.ground.p05` must fall below 0.50 from 0.5776. THE NEW READING THE LADDER
ADDS: if the step is flat across a hundredfold range of sun, no sun intensity
is the answer and the exposure or the sky is, and that is a measured
conclusion rather than a fifth guess.

If the ladder cannot be built, the fallback is NOT a single shot at 30.0f. It
is two shots, 3 and 30, at the same camera and condition, which is the
smallest thing that can still show a slope. A run that cannot show a slope
does not get the dispatch.

### 3.2. Question 2: it dispatches tonight, and it dispatches SECOND

YES TONIGHT, AFTER THE ART RENDER LANDS. NOT FIRST, and this is a scheduling
ruling with a mechanism behind it rather than a preference.
`ledger-art-blender-preview.yml` lines 11 to 16 say the art lane YIELDS rather
than queues: its first step asks GitHub whether any game workflow is in
progress on this repository and, if one is, exits without doing anything.
`ledger-probe-unreal.yml` is a game workflow on the same PC. Dispatching the
probe first therefore does not delay the Mickey's render, it DESTROYS its run,
silently and by design, for the second time today after the twelve-second
death. Jafar asked for that render by name.

THE ORDER, and the resident does not vary it:

1. Commit this batch. It is what unblocks the art lane.
2. Dispatch the Mickey's render and watch by ancestry, per ci.md: capture the
   sha before dispatching and look for a landed run whose commit contains it.
3. The builder pass for the ladder, the spec field and the readback keys.
4. Dispatch the probe once the art run has landed.

If step 3 is not finished tonight, step 4 waits for tomorrow. Nothing is lost
by waiting and one dispatch is lost by hurrying.

### 3.3. Question 3: the four `sun*Read` keys ship in the SAME change

SAME CHANGE. The confound the question worries about is real in general and
absent here, for one reason that has to be stated precisely or a future
session will apply the wrong half of it.

THE NUMBER THE CONCLUSION RESTS ON IS NOT PRODUCED BY THE NEW KEYS. The
shadow-edge step, the per-surface lit-minus-shadowed values and the contact
series all come out of `tools/frame-shadow-probe.py`, an offline tool that
reads committed frames and is calibrated against the engine's own readbacks.
`sunIntensityRead`, `sunCastShadowsRead`, `sunPitchYawRead` and
`sunMobilityRead` are INPUT readbacks: they say what the light actually was,
off the component rather than off the constant, which is the gap the verdict's
`sun=yes fill=3/3` left open by only ever proving that something spawned. An
input readback cannot move an outcome measured by a frozen tool. It can only
tell you which input produced which frame, which is exactly what a ladder
needs.

TWO CONDITIONS THAT MAKE THAT TRUE RATHER THAN ASSERTED:

- `tools/frame-shadow-probe.py` DOES NOT CHANGE ITS MEASUREMENT CODE in the
  same commit as the light change. Frame and shot selection may become
  arguments, since it is hardcoded to `vign_hook_day` and `cam_hook` at lines
  75 and 76 and the ladder needs it pointed at five frames. The maths, the
  luma weights, the tracer and the binning are frozen. If the tool needs a fix
  found during the ladder, that fix lands and re-runs against the OLD frames
  first, and the number it changes is stated.
- EVERY LADDER FRAME PRINTS ITS OWN THREE INSTRUMENT CHECKS before its step is
  quoted: mean luma against the verdict for that frame, the control quads, the
  skyline agreement. A frame whose instrument checks were not run is a frame
  whose step is not evidence, and a ladder is five chances to quote one.

### 3.4. Question 4: this morning's sky landing was a MISS, and it stands

PLAINLY: YES, IT COUNTS AS A MISS. Not a miss of the four predictions, which
were written before the dispatch and all four held, and not a reason to revert
anything. The sky is better than the three fills it replaced and the landing
STANDS. The miss is in the PREDICTION SET: four predictions were written about
the thing being added and none about the thing it was standing in for.

WHAT A FUTURE SESSION SHOULD HAVE ASKED, in one sentence it can apply without
re-deriving it:

**WHEN A CHANGE REPLACES A SOURCE, WRITE ONE PREDICTION PER SURVIVING
CONSUMER OF THAT SOURCE, BECAUSE EVERY NUMBER TUNED AGAINST THE OLD SOURCE
HAS SILENTLY LOST ITS DATUM WHILE KEEPING ITS VALUE.**

The three fills were the sun's calibration context. `3.0f` did not change and
did not need to: what it meant changed, because the thing it was set against
was deleted. That is the same failure family as a threshold whose series moved
underneath it, and it is invisible to a gate because no number moved.

THE SECOND, SHARPER TELL, and it is free: THE BARE LITERAL IN THE FILE YOU ARE
CHANGING IS THE LIST OF CONSUMERS NOBODY HAS CHECKED. `3.0f` at 1240 was the
only light in `VignetteShot.cpp` without a named constant, sitting four lines
from the sky colour being changed, and the diff went past it. A named constant
gets grepped when its neighbour moves; a literal does not.

This is filed as a miss against the sky landing's record and against no
person. The instrument that caught it, `tools/frame-shadow-probe.py`, was
written the same day, which is the studio working correctly at the second
attempt rather than failing at the first.

## 4. What the resident hand-applies, as dictated text, before the commit

H1. `.claude/agent-log.tsv` CARRIES LIVE MERGE-CONFLICT MARKERS and my ruling
stamp names a row in it. Lines 291, 414 and 415 read
`<<<<<<< Updated upstream`, `=======` and `>>>>>>> Stashed changes`. DELETE
THOSE THREE LINES AND NOTHING ELSE. All 122 rows between them (292 to 413,
2026-09-06T14:05:51Z through 2026-09-09T04:51:29Z) are the upstream side and
every one of them is kept; the stashed side contributed no rows between 414
and 415, so nothing is chosen against. Do not resolve this by taking one side
wholesale, which would delete 122 spawn rows and make three days of attendance
unreadable. Look before you destroy.

H2. Nothing else. Pieces A, B and C's committed half go in as the builders
left them.

## 5. The conditions on this approval

Every line pasted into the commit message VERBATIM from the run, not from this
record. I ran nothing, so nothing above is a measurement.

1. `python3 tools/lint-bootstrap-single.py`: the census line and the verdict
   line, both in full. CONDITION: the census must show 9 workflows derived as
   needing the bootstrap and 9 of 9 calling it, with 0 problems. If the
   derived count is not 9, the derivation and `DERIVATION_FLOOR` disagree and
   THIS APPROVAL DOES NOT APPLY until the difference is named.
2. `python3 tools/lint-bootstrap-single.py --selftest`: the final ok and
   failed counts. The planted RED case is inside it, so this run re-proves
   today's fault is caught rather than reporting it from another session.
3. `python3 tools/systems-inventory-check.py`: the `entries=`, `byStatus:` and
   `typedBy:` lines, plus the selftest's passed count with its accepting
   count. CONDITION: `typedBy` must still read director 7 and builder 62
   summing to 69 with untyped 0, unchanged by piece B.
4. `python3 tools/map.py --selftest`: the passed count over its checks, and
   the run's `greenWhere` line. CONDITION: the green split must read 19
   `core-csharp`, 4 `both`, 0 `ue-probe`, 3 `repo`, summing to 26. Section 2c
   of this record quotes those numbers as a conclusion; if the run prints
   anything else, section 2c is wrong and must be corrected in the same commit
   rather than left standing.
5. `python3 tools/frame-shadow-probe.py --selftest`: the 12 of 12 with the
   accepting case first.
6. `python3 tools/docs-check.py`, after this file exists.
7. `python3 ledger/verify.py`, footer pasted FROM `ledger/.verify-footer` and
   never from the scrollback. CONDITION: `director_cadence` must be green with
   this record's stamp; if it is not, the stamp or the spawn row is wrong and
   the commit does not go in on a hand-edited gate.

## 6. The quality ladder at close, and the queue items this ruling files

Best available or first working, per aspect, with the next rung named. None is
blank.

- The bootstrap lint: at "population derived from the artefacts, exemptions
  reasoned, floor under the parser". Next rung: an unresolvable `runs-on` that
  can be exempted with its own written reason, so the first matrix workflow
  does not meet an unclearable red.
- The board: at "typed, attributed and honest about which build its green is
  about". Next rung: `both` above 4 of 26, one measured parity row at a time,
  and above that the tiles Jafar rules himself, which is a tap.
- The shadow probe: at "three separate readings, each calibrated against the
  engine's own numbers on the frame it reads". Next rung: the same three
  readings run automatically on every committed frame, so a light regression
  is caught by the same instrument that found this one instead of by the next
  person who looks.
- The light rig: at "the fault is located and the series is not yet printed".
  Next rung is the ladder itself, and the rung after it is a sun and sky pair
  set from a read curve rather than from a literal.

Queue items this ruling files, numbers the resident's to assign, none started
now:

- A. The unresolvable-`runs-on` exemption channel in
  `tools/lint-bootstrap-single.py`, per section 1.
- B. The sun-intensity ladder: `sun_intensity` on `Condition`, the parse rung,
  the use at 1240, the five ladder rows plus the dim-sky control row, the four
  `sun*Read` keys off the component, and `--frame` selection on
  `tools/frame-shadow-probe.py`. This is the piece that dispatches, and it
  dispatches after the art render lands.
- C. Set `kSunIntensityDay` and, if the control row says so, `kSkyIntensityDay`
  from the read series. Blocked on B.
- D. A prediction-set check for any change that replaces a light or a source:
  one prediction per surviving consumer, per section 3.4.

<!--RULING spawn=2026-09-09T14:24:39Z paths=.github/workflows/ledger-art-blender-preview.yml,tools/lint-bootstrap-single.py,ledger/verify.py,production/systems-inventory.json,tools/systems-inventory-check.py,tools/map.py,map.html,tools/frame-shadow-probe.py,.claude/agent-log.tsv,game-design/decision-2026-09-09-ruling-the-sun-the-bootstrap-and-the-board.md-->
