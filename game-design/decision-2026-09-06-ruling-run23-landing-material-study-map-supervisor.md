# Ruling: the run 23 landing (material, study, map, supervisor). LAND WITH AMENDMENTS

> **STATUS: LOG, 2026-09-06.** Director ruling at spawn 2026-09-06T14:33:03Z
> on the uncommitted tree of four builders and the resident: the material
> generator and its workflow (engine-specialist), the queue 119 sweep
> (systems-builder), the map rewrite (instrument-builder), the supervisor
> (engine-specialist), and the resident's queue, NOW.md, DISPATCH and outbox
> edits. NOT CURRENT once the amended commit lands; from then the files are
> the reading copies and this is the record of why.

VERDICT: LAND WITH AMENDMENTS. Three amendments block the push, because the
push IS the dispatch of Unreal run 24 (`production/d1-probe/DISPATCH` is a
push trigger) and each of the three is a known way for this batch to print a
word the tree cannot back. All three sit in the two files one builder already
owns, so they are ONE engine-specialist pass and no new spawn class:

- A1. `tools/ue/make_base_material.py`: `compile_verdict` may return OK only
  when the log slice it read has a non-zero denominator AND both compile
  markers were seen, on top of the two conditions it already has. Section 7.
- A2. `.github/workflows/ledger-probe-unreal.yml`: delete `continue-on-error:
  true` from the step "Commit the probe result". With it in place the new
  `exit 1` fails the STEP and the JOB stays green, which is the same colour
  that was read as a landing on runs 18 and 22. NOW.md's sentence "AN
  UNPUSHABLE PROBE RESULT NOW FAILS THE JOB" is false as the tree stands.
  Section 12.
- A3. Same workflow, the new step "Retain the material compile evidence":
  add `continue-on-error: true` under its `if: always()`, and make
  `$ErrorActionPreference = "Continue"` the first line of its `run` block,
  as every other pwsh step in that file does. Its comment says "Never fails
  the job"; GitHub's pwsh default is `stop`, so today it can. Section 12.

Four dictated text corrections (A4, section 15) go by the resident's hand
under the one-line allowance. Five findings are FILED AND WAIT FOR MONDAY
under Jafar's weekend order of 2026-09-06 ("any new tooling or process item
discovered this weekend goes to the queue and waits"), and section 16 names
each so it can be filed in one line. Queue 132 is one of them: it is a real
hole and it does NOT block this landing (section 10).

Nothing here has run an engine and no browser has rendered the map. Every
number below is read off a committed file, the coordinator's verify footer,
or one PNG I opened; none is a measurement I took.

## 0. What was read, what was not run, and what I was told

Read in full or in the named ranges: `tools/ue/make_base_material.py` 400
to 760, 1000 to 1060, 1590 to 1670, 1880 to 2279; the builder's pre-edit copy
`make_base_material.py.bak` in the shared scratchpad (grepped, lines 428,
760, 912 to 913, 998, 1014 to 1019, 1033 to 1034); `ledger-probe-unreal.yml`
1 to 844 and 1000 to 1140; `ledger/verify.py` 862 to 893, 1777 to 1807, 2873
to 2981, 3300 to 3339, 5495 to 5510, 5695 to 5712 and the function list at
6138 to 6147; `ledger/StrangerTest/Program.cs` 780 to 874 and the grep of
its selftest sites; `ledger/StrangerTest/Sweep.cs` 1 to 110 and 833 to 923;
`production/stranger-test/study.txt`, `study-sweep.txt`, `study-curve.txt`
whole; `tools/map.py` 380 to 500, 1252 to 1320, 1640 to 1728; `map.html`
line 78; `.github/workflows/publish-glance.yml` whole; `tools/supervise.py`
1 to 70 and 686 to 745; `START EVERYTHING.bat` whole; `production/queue/123`
and 127 to 132 whole; `production/NOW.md` whole; the outbox answer;
`production/d1-probe/DISPATCH`, `ue-build.txt` 1 to 16,
`ue-vignette-verdict.txt` whole, `ue-verdict.txt`; `.claude/agent-log.tsv`
whole (294 lines); `.git/logs/HEAD` 405 to 430; the ruling of queue 113 for
shape. `production/systems-inventory.json` was counted, not read.

OPENED: `production/d1-probe/ue-vign_camA_day.png`, the run 23 frame.

NOTHING WAS RUN. This spawn has no shell. I could not run a selftest, could
not `git diff`, and could not read pre-edit code out of git; the pre-edit
material script is the builder's `.bak` copy and I say so where I rely on
it. The coordinator ran `ledger/verify.py` over the whole tree and sent the
footer; where I quote it, it is theirs. The one red in it is this record.

PREMISE, CLAUDE.md section 0 and constitution: late-analog Meridian, moat
first. This batch is the street's cause on the visual leg of the Meridian
Test and the first measurement of the moat on the social leg; nothing
purchased, no licence entry, no retired bar cited. The study drives the
shipped session through its own `IUi` rather than a copy (Sweep.cs 27 to
31), which is the constitution's classification-not-adjudication law
applied to an instrument. Nothing here contradicts the premise.

THE SPLIT FOR THIS SPAWN: game 2 (material, study), studio 2 (map,
supervisor), basis spawns, points unmeasured.

## 1. The reference and the stamp

The cadence gate's reference is the newest commit touching the reviewed
scope, `_cadence_pathspec()` (verify.py 2941 to 2957). The footer names it:
`de158c2c@2026-09-06T10:45:56Z`, and `.git/logs/HEAD` line 429 confirms
`de158c2c` is HEAD, fast-forwarded at 14:02:24Z from a runner commit made
after `245e368`'s 10:41:50Z dispatch.

`.claude/agent-log.tsv` rows after that instant: lines 288 to 294, of which
exactly ONE is `studio-director`, line 294, `2026-09-06T14:33:03Z`. That is
this spawn and the one stamp at the foot of this record. The footer read
`0 director row(s) newer than the reference of 292 log row(s) examined`
because it ran before the row was written; the file now has 293 rows.

A correction to what I was told, per rule 1: the row `2026-09-06T09:13:12Z`
is NOT stamped in any record. The grep of `RULING spawn=2026-09-06` over
`game-design/` finds three stamps, `05:53:25Z` (queue 113), `07:22:43Z` and
`09:03:18Z` (the register ruling). It is older than the reference, so the
gate does not ask for it and this record does not take it.

## 2. Conclusion 1: the street's material never compiled

The chain, each link read off `ue-vignette-verdict.txt` for `245e368`:

- line 89: `midReadbackAsked=12/16 midParamReadback=12/12
  midScalarReadback=12/12 texResourceValid=12/12 compMaterialIsMid=12/12`.
  Candidates A, B and C each predicted at least one of those short. None is.
- lines 90 to 92: three quads spawned, `quadMid=made`, boxes printed BEFORE
  the frame was read: colour at x488..614, tile1 at x309..437, tile4 at
  x130..261, all y298..422, tilings 1.00, 1.00 and 4.00.
- THE FRAME, which I opened. At those three boxes the run 23 day frame
  shows three grey checkers of one visible cell size, and no red, green,
  blue or yellow in the colour quad's box. Looking is not measuring (rule
  4): the chroma figures in queue 123 (mean 3.7, max 6 over 11,880 pixels)
  and the 9.0-cell count were produced by the resident's session
  measurement and NO COMMITTED TOOL PRINTS THEM. They agree with what the
  frame shows, and they stay the resident's numbers until a tool in the
  tree emits them (section 16, item d).

A material instance whose texture and scalar overrides all read back and
none of which reaches a pixel is not a parameter fault; a compiled
M_LedgerSurface with the UV chain wired 14/14 (`ue-build.txt` line 12)
cannot render tiling 1.00 and 4.00 identically. The engine's fallback for a
material that failed to translate is its default material, a grey checker
that ignores instance parameters. D is the only candidate on the table that
predicts every line above at once. RULED: the evidence carries the claim as
the best available explanation, and the run 24 acceptance in DISPATCH (a
to d, written before the run, with the bay3 window's R/B 0.934 and chroma
max 7 as the before-number) is the proof. It is not proven until that run
lands; nobody may quote it as proven before then.

## 3. Conclusion 2: a second compile error nobody could see

Checked against the pre-edit script in the scratchpad `.bak`, not against
the builder's description. Line 1018 to 1019: the roughness sampler was
built with `st.SAMPLERTYPE_LINEAR_GRAYSCALE` and handed `colour_default`,
the same object line 1014 gave the colour sampler. Lines 1033 to 1034:
`defaults_bound = (1 if colour_default ...) + (1 if normal_default ...)`,
over a hand-typed denominator of 2 for three samplers, and line 760 of the
same file ASSERTED `materialDefaultsBound=1/2` in its selftest. So the key
could not have named the roughness fault: its denominator did not contain
the sampler. That half of the claim is established by reading.

The other half is a prediction about the engine. Unreal derives a sampler
type from a texture's compression setting and sRGB flag, and refuses a
sampler whose declared type differs ("Sampler type is X, should be Y for
Z" is a material translation error, and the new `is_compile_diagnostic`
matches exactly that phrase, lines 479 to 485). LINEAR_GRAYSCALE is derived
only from TC_Grayscale; `/Engine/EngineResources/DefaultTexture` is not a
grayscale texture, so the mismatch holds WHETHER OR NOT that texture is
sRGB, which is the one property in the builder's sentence I could not
verify from here. The normal sampler's null texture is on the landed line
(`materialNormalDefault=none-of-2-candidates`) and is the first error.

What run 24 proves and does not prove: it runs the NEW graph, so its
diagnostics slice speaks about the fixed material, not the old one. The
mechanism (that run 23's graph carried these two specific errors) stays a
named lead with an engine rule behind it. Section 16, item e, names the
one-run experiment that would close it; it is not worth a round trip today.

## 4. Conclusion 3: the selftest that never ran

`ue_material_selftest` is in `verify.py` (862 to 893) and in the function
list at 6147. Its docstring says the selftest ran nowhere before today, the
footer calls the row new, and the tool's own selftest asserted a wrong
denominator (section 3) for as long as it existed. I could not read the
pre-edit `verify.py`, so "never wired" is the builder's claim corroborated
by the coordinator's reading of the footer, not mine. The gate as written
is sound: a missing tool is red by name (876 to 877), a missing summary
line is red with the exit code (883 to 889), and the count is read off the
tool's own line (890 to 893). First green earns distrust; section 9 is the
distrust.

## 5. Conclusion 4: the log nobody read

Read off the build step, which the batch did not change: `material.log` is
read at lines 307 to 310 ONLY inside the `else` of `if (Test-Path
$matOut)`, the path where the script wrote no verdict; `material.err` is
read on no path in that step. Both existed for every run from 18 on and
`materialEditorCmdExit=1` sat unexplained beside `materialScriptReturn=0`
on `ue-build.txt` line 11 to 12. Confirmed. The new step at 557 to 585
keeps the last 120 lines of stdout and first 60 of stderr with both caps
announced, plus the script's own section, into
`production/d1-probe/ue-material-log.txt`, which the commit step stages by
name at 1116 to 1117. The step needs A3 to be what its comment says.

## 6. What A1, A2 and A3 have in common

Each is the same shape as the fault the batch exists to end: a word or a
colour that can be printed without the thing it claims. MADE without a
denominator (A1), a green job over a lost run (A2), "never fails" over a
step that can (A3). None is the builders' carelessness; A2 is the
resident's own change and A3 is the parity every other step carries. They
block because the push dispatches the run, and a run read through any of
the three would cost the hour this project has already paid three times.

## 7. Question (b): is COMPILE-UNPROVEN the right shape

Yes, and here is the structural check the brief asked for.

`material_status` (660 to 720) reaches `STATUS_MADE` only past `compile_word
== COMPILE_OK` (716). `compile_verdict` (530 to 549) returns OK only when
`errors` is not None, `errors == 0`, and `instructions` is an int above
zero. `errors` is None unless `_read_editor_log` returned lines (1883 to
1921: every failure path returns None, never an empty list read as clean).
`instructions` is None unless the statistics API answered an int (1924 to
1968: no exception path returns a number). `recompile_material`'s
exception is caught into a NOTE (2151 to 2154) and feeds neither. So the
absence of an exception contributes nothing to either input of the only
clause that can say MADE. The selftest ratchet at 1036 to 1045 walks all
twelve (defaults, compile) combinations and fails if MADE appears anywhere
but (3, OK); the run 23 input row at 1006 asserts PARTIAL; the
defaults-full-channel-silent row at 1010 asserts COMPILE-UNPROVEN. And
UNPROVEN returns 2 (734), which the workflow does not gate on (no exit
follows `materialEditorCmdExit` at 304), so the cook and the four frames
arrive either way, exactly as DISPATCH says. RULED: the word is the honest
fallback and not a comfort. It is a non-pass with the same return as every
other non-pass, and it says which channel was silent on the same line.

TWO ROUTES REMAIN BY WHICH OK CAN BE PRINTED OVER NOTHING, and A1 closes
both. They are visible on the line today and invisible in the word, which
is the wrong way round for a word people read.

(i) `compile_scan` on an EMPTY slice returns `(0, 0, [])`. `compile_verdict`
never sees the denominator, so `errors=0, examined=0` with a non-zero
instruction count is OK, and the line reads `materialCompileErrors=0/0
materialCompile=OK`. A zero without a denominator is rule 3b's exact
sentence. The selftest's compile cases (1606 to 1614) cannot see this
because the function has no `examined` argument to feed.

(ii) `log_slice` with no BEGIN marker returns the WHOLE log (494 to 514,
and the selftest at 1590 to 1595 asserts it). That is right for counting
diagnostics, which fails closed. It is wrong for OK: a slice that carries
neither marker has not been shown to be this material's compile, and
`materialCompileMarkers=begin.NO/end.NO` beside `materialCompile=OK` is a
pass over an unlocated log. In this workflow the risk is small (`Saved` is
cleared before the cold build at 234 to 240, so the newest `.log` is this
session's), and small is not structural.

A1, stated as behaviour so the engine-specialist writes the code: OK
requires errors read AND `errors == 0` AND `examined > 0` AND both markers
seen AND instructions above zero; ERRORS stays as it is, reachable without
markers; everything else is UNPROVEN. `compile_verdict` is computed ONCE in
`main()` and that one value goes to both `compile_fields` and
`material_status` (today it is called twice, at 2195 and 2212, which is
one number computed twice and will drift). The `materialCompileRule=` token
names the new condition. Selftest, accepting case first, then rejecting:
(0, 187, marks yes/yes) OK; (0, 0, yes/yes) UNPROVEN; (0, 40, NO/yes)
UNPROVEN; (0, 40, yes/NO) UNPROVEN; (3, 40, NO/NO) ERRORS; and the ratchet
loop at 1036 unchanged. The footer's count moves from 93 by the number of
cases added, and the builder states that number rather than this record
guessing it.

## 8. Question (c): is the study's finding reported honestly

Yes, in the tree. The test I applied to every sentence: does it say what
the session EMITTED, or what a person would PERCEIVE.

- `Sweep.cs` 19 to 25: "Nothing here scores an arm, prefers an arm, or
  reports a preference. It counts what is countable." `study-sweep.txt`
  line 2: "No line is a preference." Every line in both study files is a
  count over a printed denominator.
- Queue 127, "What this does NOT say": "It does not say people would prefer
  the canned arm. Nobody has played either ... carries ZERO evidence about
  what a person would perceive or enjoy." The biases section names three
  and says which way each cuts.
- The three sub-findings (128, 129, 130) are each one number over one
  denominator with the code site named (`lieCaughtAtLiveCadence=0/5`,
  `Gossip.cs` 381 and 483, suspicion 0.060 in both arms).

ONE PLACE SLIDES, queue 131, and it is dictated back (section 15, A4.3).
"ONE CRIME CANNOT CROSS THE SPEAKING THRESHOLD AT ANY HONEST TUNING" claims
a sweep over tunings; the sweep varied paths (108 of 108) and decay (on,
off), and held every constant at its shipped value. What was measured is
that the highest one-crime pressure anywhere in the space is 0.324 against
a Comments rung of 0.42 (`study-curve.txt` A, `study-sweep.txt` per-path
lines: every `pressure=` is 0.324 or below). "Any tuning" is not a finding
about the game; moving the rung to 0.30 crosses on crime 1, and whether
that is honest is a design question the numbers do not answer. The second
sentence, "no participant walking that scenario could have heard the
mechanism whichever arm they were in", is true in the direction it is used
(zero emission implies zero perception) but does not name WHICH mechanism:
the sweep shows the real arm saying a pointed line in 540 of 3240, so the
scenario did reach a mechanism, and it was not Lena's stance ladder, which
is the one 119 was written to test.

The inference the study rests on, that 108 is the whole path space and not
a sample, is asserted at `Sweep.cs` 38 to 53 and TESTED at 870 to 881: a
two-pass script against its single-pass twin, every spoken line equal.
That is the right shape and it is the reason "enumeration, not sample" may
be written.

## 9. Question (d): the guards, read

Material generator (93 checks, footer green, first ever). The accepting
row is 985: `(True, 3, 3, 14, 14, 0, 3, 3, COMPILE_OK, STATUS_MADE, 0)`.
The rejecting rows 1006 to 1018 cover run 23's own inputs, a silent
channel, a diagnostic outranking the property-write word, and a zero
denominator on the defaults. The ratchet (1036 to 1045) is a check and not
a comment. The formatter lines are built and inspected for one `=` per
token (1652 to 1655) and for the words that must be on them (1657 to
1661), including `materialDefaultsBound=1/3`, which is the corrected
denominator on run 23's own inputs. What the 93 do NOT contain is the two
cases of section 7, which is why the first green is not enough and A1 adds
them. They also cannot contain the engine: whether the TGA import lands a
`T_LedgerDefault*` asset, whether `get_statistics` exists under that name
in 5.8, and whether `log_flush` plus `project_log_dir` yield a readable
file are all UNRUN, and DISPATCH lists exactly those three, which is the
honest statement.

Map (36 checks, NOT in the verify footer, and that is a deliberate split
and not the material fault). `publish-glance.yml` runs `tools/map.py
--selftest` at line 221 on every push touching `tools/map.py` or any of
its inputs (56 to 91). `check_no_comforting_bar` (1287 to 1318) finds the
area's row by its own `data-area` attribute (the first draft's 900
character window is named in its docstring as the fault it replaced),
and bites on a health word in an unmeasured row or on readings not
labelled "do NOT answer it". Rejecting fixture at 1677 to 1689: an
unmeasured street row carrying "harness only" and `piecesTextured=563/593`,
asserted red. Accepting case: the live build over the real tree, where the
street reads nothing measured (`map.html` line 78, `visual=0/6 text=6/6
unknown=0/6 onHisPc=5/6 packagedBuilds=0`).

CAN THE STREET REPORT HEALTH BY ANY ROUTE TODAY: no. Its `needs` (451) are
`quadChroma`, `quadColoursSeen`, `materialCompiles`, looked for in
`UE_VERDICT = production/d1-probe/ue-vignette-verdict.txt` (80, 456, 618
to 619), and nothing writes any of the three there. TWO THINGS TO NAME
RATHER THAN LEAVE. First, the comment at 449 to 450 ("The day a run emits
one of these keys, this area starts reading it with no edit here") is
false for the material key: the generator prints `materialCompile=` (no
s) into `ue-material.txt`, which the workflow folds into `ue-build.txt`, a
file the map does not read. Dictated as A4.5. Second, `needs` is a
PRESENCE check, not a value check: the day `materialCompiles=UNPROVEN`
appeared in that file, the street would leave nothing measured and take
its word from the gates. That is the comforting bar one key away, and it
is filed (section 16, item b), not built, under the weekend order.

The trigger-path residual the coordinator raised: a commit that breaks a
page tool without touching a trigger path lands green and stays broken
until the next publish. RULED: not worth closing inside this batch. The
four tools' inputs are all trigger paths, `tools/map.py` itself is one,
and the failure mode is a stale page rather than a wrong number. It is
worth one line in the queue for Monday (section 16, item c), because four
selftests that take seconds belong in the commit gate on principle.

Supervisor (34 checks, footer green). Accepting first (694 to 703): a
daemon that stays up is never restarted and its line says RUNNING.
Rejecting (723 to 740): a planted crash loop reaches `gaveup` on the Nth
exit and not before, the reason carries count, window and code, and a
given-up child is never due again. The ladder is asserted as a series (719
to 721). Its own docstring (36 to 47) says the numbers are unmeasured and
the process half has never run where it was written, which is right. ONE
STALE NUMBER: `START EVERYTHING.bat` line 55 says the selftest "passes 24
of 24 cases"; the footer says 34. A count in a comment decays; dictated
out as A4.4.

Stranger (6) and study (5). `Program.cs` 794 to 796 prints the beat
identity line with both denominators and returns 1 on any failure; the two
planted differences (a missing beat, an option change) are asserted
caught. `StudySelftest` (844 to 923): the pressure mirror on fourteen rung
probes, then a PLANTED mirror error asserted caught (864 to 868), the
re-plan twin, the multi-day copy against the shipped session's day one,
and the no-spaces rule. The mirror check is the one that matters most,
because the whole curve file is a second implementation of
`StreetVoice.Stance`, and it is checked on every sample the sweep takes
(`mirrorOk=1944/1944`, `36/36`). Sound.

## 10. Question (e): the gate that reads half its tool

Verified by reading. `verify.py` 1792 to 1807: `code, out = run(...)`; `code`
is never read again; the regex matches only `stranger-test selftest: N
passed, M failed (...)`. `Program.cs` 829 to 834: `--selftest` runs
`Selftest()` then `StudySelftest()` and returns 1 if either failed. So a
study failure prints `study selftest: 4 passed, 1 failed` and exit 1, the
gate matches the other line's `0 failed`, and the footer reads
`stranger-test arms identical over 4 script(s), 2 planted difference(s)
caught`, which is the exact line the coordinator's footer shows. Queue 132
is correct, and its acceptance fixture at 5501 to 5506 does not contain the
study line either, so the accepting case has never been the whole tool.

DOES IT BLOCK THIS LANDING: NO. Two reasons, both stated. The study's
finding does not rest on the gate; it rests on the two committed study
files and their own printed self-checks, and the coordinator's footer
shows both suites passing on this tree today. And Jafar's weekend order is
explicit that a tooling item discovered this weekend is filed and waits
unless it blocks the two game items; 132 blocks neither. What this record
does is fix the acceptance so Monday's builder does not have to invent it:
the gate reads BOTH summary lines, treats a missing line or a non-zero
exit as red naming which suite, and the footer carries both sets of
denominators, for example `stranger-test arms identical over 4 script(s),
2 planted difference(s) caught; study selftest N passed over 14 rung
probe(s), exit 0`. Fixtures: the accepting one carries both lines and
exit 0; a rejecting one carries a green beat line, a red study line and
exit 1, and is asserted red with the word "study" in it.

## 11. Conclusions 5, 6 and 7

5 (the moat fires and is inaudible). `lieHeard=0/90` over `lieCaught=90/648`,
`liveSilent=1944/1944`, `cannedPointed=3240/3240` against `realPointed=
540/3240`, all on `study.txt` line 1 with the same numbers repeated at the
foot of `study-sweep.txt`. The chain per path (seed 107 block) shows the
mechanism firing (`contra=1 susp=0.176`) and the last line `chatter` on
every row. The claim is what the numbers say and is phrased as emission.
CARRIED, with 127's own caveat that the harness substitutes the plain band
where the build is silent, which flatters the real arm and is the right
choice for a controlled comparison.

6 (queue 119 could not reach its mechanism). CARRIED for Lena's stance
ladder at the shipped constants over the whole path space, and NOT carried
as "at any tuning"; A4.3 corrects the sentence. The design that follows
(five nights, a control night, 129 first) is the right shape and is not
built today.

7 (nothing playable). `map.html` line 78 prints `visual=0/6 packagedBuilds=0`
and the inventory carries 13 entries with `"status": "exists"` (counted by
grep, 13 of 13 hits in one file). Both are true and they answer different
questions: `exists` in queue 098's schema is a statement about code in the
tree, and the map's word "harness only" is the statement about a build.
The map prints both and lets neither stand for the other, which is
correct. "Nothing in this repository is playable" is one word too strong:
six text runnables exist and one of them is a play session; what does not
exist is any visual runnable or any packaged build. Say that.

## 12. The exit 1, and the step that says it never fails

The commit step (1010 to 1139): `if: always()`, `continue-on-error: true`
(1012), `set -u`, the two accepting paths `exit 0` (1118, 1124), and the
new `exit 1` at 1139 after "could not push the probe result". With
`continue-on-error: true`, the step's outcome is failure and the job's
conclusion is success; the run is green. That is the colour that was
misread twice. A2 deletes line 1012. Rule 6 check: the step has no `id`,
it is the last step, and nothing references its outcome, so nothing else
moves. A failed `git commit` will then also fail the job, which is
correct: a commit that did not happen is not a landed run.

The retain step (557 to 585) has `if: always()` and neither
`continue-on-error` nor the `$ErrorActionPreference = "Continue"` line that
every other pwsh step in the file opens with (111, 204, 621, 793). Its
commands are individually guarded and I found no terminating error in
them by reading; "never fails the job" is still a claim the step does not
carry, and the file has already paid once for a copied step missing its
second half. A3 adds both lines.

## 13. Scope

The supervisor. `production/outbox/2026-09-06-pc-processes-one-window.
answer.md` is the Producer's answer and the inbound question is not in the
tree (`production/inbox/` holds only its README), so rule 11 cannot be
checked against Jafar's words. What justifies the build under the weekend
order is the answer's own first sentence: the bot has never run on his PC,
and the bot is the only sender, so the frames that item 1 of the order
says must reach him as images cannot until something keeps it up. That is
on the path of the game item and it lands. The answer says the restart
numbers are unmeasured, which is true and is the right register.

The study. Jafar's 2026-09-06 ruling ("Run the comparison yourself")
converted 119's evening into the sweep; NOW.md line 411 still lists 119 as
weekend item 2 unqualified. A4.2 corrects it.

Everything else in the tree is the asked thing.

## 14. Quality ladder: best available, or first working

Material: best available for the word. The next rung is not blank: run 24
itself, read in DISPATCH's order (defaults, compile, word, log file), and
then the quad chroma as a COMMITTED key from the binary (section 16, d),
so the frame's own numbers stop being a session measurement. The rung after
that is the HDRI and the wet, which is Phase C proper, and it does not
start until bay3 renders brick.

Study: best available for what a program can say about the moat. Next
rung is 129 (the re-tell guard, both sites), because every multi-day
number taken before it is measuring floating point, then 131's five-night
shape, then 128 and 130, which are design and are Jafar's cards.

Map: first working, honestly labelled. Next rung is value-checked `needs`
and the material key in the file the map reads (section 16, b).

Supervisor: first working by construction; its accepting case is the
first double-click, per its own docstring, and the series it prints is
what sets the numbers.

## 15. Dictated text (A4), for the resident's hand

A4.1 `production/NOW.md`, the section "AN UNPUSHABLE PROBE RESULT NOW FAILS
THE JOB". After A2 the heading is true. Append one sentence to its first
paragraph: `As first written the step carried continue-on-error: true, so
the exit 1 failed the step and the job stayed green; amendment A2 of the
ruling of 2026-09-06 removed it, and the sentence above is true from that
commit on.`

A4.2 `production/NOW.md` line 411. Replace `2. QUEUE 119, the three
unbriefed players.` with `2. QUEUE 119, the three unbriefed players.
SUPERSEDED THE SAME DAY by Jafar's ruling to run the comparison in the
studio: the sweep ran (production/stranger-test/, queue 127, lieHeard=0/90)
and the redesign is queue 131, which waits for 129.`

A4.3 `production/queue/131`. Replace `ONE CRIME CANNOT CROSS THE SPEAKING
THRESHOLD AT ANY HONEST TUNING.` with `ONE CRIME CANNOT CROSS THE SPEAKING
THRESHOLD ON ANY OF THE 108 PATHS AT THE SHIPPED CONSTANTS: the highest
one-crime pressure anywhere in the sweep is 0.324 against a Comments rung
of 0.42, decay on or off. Nothing here swept a constant, so nothing here
says what a retuned ladder would do.` And replace `no participant walking
that scenario could have heard the mechanism whichever arm they were in`
with `no participant walking that scenario could have heard Lena's stance
ladder speak, whichever arm they were in; the real arm did say a pointed
line in 540 of 3240, so the scenario reached a mechanism, and it was not
the one 119 was written to test`.

A4.4 `START EVERYTHING.bat` line 55. Replace `which has a selftest that
runs there and passes 24 of 24 cases.` with `which has a selftest that runs
there; ledger/verify.py prints its count on every run.`

A4.5 `tools/map.py` lines 449 to 450. Replace `The day a run emits one of
these keys, this area starts reading it with no edit here.` with `The day
a run emits one of these keys INTO THAT FILE, this area reads it. The
generator's materialCompile= goes to ue-build.txt under a different name,
so an edit here is needed before that key counts; filed.`

## 16. Filed and waiting for Monday (names, not work)

a. Queue 132, the stranger gate reads the exit code and both suite lines.
   Acceptance dictated in section 10. Studio, small.
b. The map's `needs` are presence checks; make them value checks, and read
   `materialCompile` from `ue-build.txt` or have the vignette binary emit
   it into the verdict the map reads. Studio, small.
c. The four page tools' selftests (`glance`, `map`, `gallery`,
   `publish-glance`) into `verify.py`, so a break that touches no trigger
   path is red at commit time. Studio, seconds each.
d. The vignette binary prints `quadChromaMean` and `quadChromaMax` over
   each `quadBoxPx` from the decoded PNG, in `FrameStats.h` where g++ runs
   it before dispatch, so the numbers in queue 123 become a committed key
   and the map's `quadChroma` need is met by the tool and not by hand.
   GAME PATH, engine-specialist, rides run 25.
e. The mechanism proof for run 23's graph: one editor pass that builds the
   OLD graph (null normal, LINEAR_GRAYSCALE roughness on the colour
   default) under the NEW instrument and commits its diagnostics slice, so
   "two compile errors" is printed by an engine rather than inferred.
   Research-class; only if run 24 leaves the question open.

## 17. What the resident prints before the commit

1. The engine-specialist's A1 to A3 diff, read against sections 7 and 12,
   and the builder's stated new selftest count.
2. `python3 ledger/verify.py`, footer pasted FROM `ledger/.verify-footer`.
   Expected: `ue material generator ok (N checks)` with N above 93 by the
   builder's stated number; `supervise selftest ok (34 checks, 0 failed)`;
   `stranger-test arms identical over 4 script(s), 2 planted
   difference(s) caught` (unchanged until 132 lands); the cadence line
   pairing this record with row `2026-09-06T14:33:03Z`; `workflow steps
   ok` and `pwsh steps parse` still green after A2 and A3.
3. `grep -n "continue-on-error" .github/workflows/ledger-probe-unreal.yml`:
   the commit step's line is gone and the retain step's is present.
4. `grep -rn "24 of 24\|AT ANY HONEST TUNING\|with no edit here" --include=*.bat --include=*.md --include=*.py .`
   returns nothing outside this record.
5. The commit message names this record and states: run 24 is dispatched
   by this push, the branch is FROZEN until a landed run contains this
   commit (runs 18 and 22 were lost to exactly that), and the stranger
   gate hole (132) is known and waits.

<!--RULING spawn=2026-09-06T14:33:03Z-->
