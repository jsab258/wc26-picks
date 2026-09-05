# Ruling: queue 062 step 2, the third status word, lands and run 21 is authorised on it

> **STATUS: LOG, 2026-09-05. NOT CURRENT.** Director ruling at spawn 2026-09-05T16:15:44Z
> on the builder's step 2 diff to `tools/ue/make_base_material.py` and on
> `production/queue/062-uv-chain-head-refuses-to-wire.md`. Scope is those
> two files ONLY; the other builders live in this tree (`ledger/verify.py`,
> `tools/producer-check.py`, `tools/queue-check.py`, `tools/runner/*.py`,
> `tools/glance.py`, the Pages workflow) were not read and are not ruled on
> here. NOT CURRENT once the dictated edits in section 7 are applied and the
> batch is committed; from then the file, the queue item and `production/NOW.md`
> are the reading copies.

VERDICT: APPROVED. The rejecting case is real, the added key is adopted, the
spelling holds against the only committed record of it, the three verdict
lines obey the format law, and RUN 21 IS AUTHORISED ON THIS CODE once it is
committed and the two conditions in section 5 are recorded. One attribution
fault in a docstring is dictated (D1), the queue item gains its step 2
section (D2), and the commit message carries the selftest's own summary line
(section 6).

## 0. What was read, and what was not run

This director has Read, Glob, Grep and Write and no shell. The selftest was
NOT executed here; every fixture below was traced by hand through the code as
it stands, and the trace is named as a trace. Read in full:
`tools/ue/make_base_material.py` (1109 lines), queue 062, section 4 and
section 8 of the 3 September batch ruling, `.claude/agent-log.tsv` lines 255
to 263. Read in part: `.github/workflows/ledger-probe-unreal.yml` at every
line matching `ue-material|materialStatus|materialScriptReturn` (lines 288
to 310 and 1061 to 1069); `production/d1-probe/ue-build.txt` lines 10 to 13;
`ue-probe/Source/LedgerProbe/Public/SurfaceBind.h` lines 61 to 65;
`production/NOW.md` lines 145 to 165 and 372 to 380; `production/budget.md`
lines 416 to 426; `tools/docs-check.py` lines 125 to 146.

Counted. `checks += 1` sites in `selftest()`: 32, of which one is inside a
loop of 2 (the scalars) and one inside a loop of 8 (the status cases), so a
green run prints `40 check(s)`. The builder's "30 to 40" agrees with that
count. Grep `materialStatus` across the tree: 9 files, none under `tools/`
except the script itself. Grep `ue-build.txt|ue-material` under `tools/`: 1
file, the script itself. Grep `materialUvHead` outside the script,
`game-design/` and the queue: the workflow's own NO-LINE fallback, DISPATCH
prose, run 20's verdict line (which predates the keys), `budget.md` and
`NOW.md` prose. Grep `property-write` across the tree: 7 hits, 5 in the
script and 2 in the 3 September ruling.

Taken on report and named so: that the selftest exited 0 on the builder's
machine; that five planted conditions each went red and were reverted with
the file restored byte-identical. Section 6 turns the first into a printed
line in the commit; the second is not reproducible here and is not relied on.

## 1. The rejecting case is real

`material_status` (lines 263 to 271) reads its clauses in this order: not
saved, parameters short, `asked <= 0 or wired < asked`, THEN
`prop_write_heads > 0`, then `MADE`. So:

- With the count at zero and 14 of 14, the fourth clause is false and the
  function falls through to `MADE`. The selftest's rejecting case (lines 706
  to 713) does not hand-type the zero: it counts `good_heads`, two records
  whose via is `pin_token("", "")`, through `property_write_heads`, gets
  `(0, 2, "0/2")`, and requires `MADE` with return 0. Traced: `pin_token`
  yields `out.empty..in.empty`, which does not end in `property-write-took`,
  so the count is 0. Real.
- The branch cannot fire on a short run: `wired < asked` returns `PARTIAL`
  before the property-write clause is reached. Selftest line 519 plants
  exactly that shape (13 of 14 with one property-write head) and requires
  `PARTIAL`. Traced: it does.
- In `main()` the count comes from the head RECORDS (line 1057), never from a
  flag. On the pin route the via is `pin_token(...)` (line 959) and cannot
  carry the suffix. On the last-resort route `ok = wrote is True` (line 968)
  and `_write_input_property` returns True only when `_reads_back` is True
  (line 883), so a head is counted only when a named pin refused it AND the
  graph reads back connected. That is the ruled meaning of the count.

The 14 of 14 that the third word needs cannot be reached by a run that made
fewer than 14 connections, and a 14 of 14 with both heads by pin prints
`MADE`. One overclaim has not been swapped for another.

## 2. The added key is adopted, not tolerated

`materialUvHeadByPropertyWrite=N/M` was not in the 3 September ruling, which
ordered a parameter, one line in `main()` and two selftest cases. RULING: it
is IN SCOPE and it stays, for three standing reasons.

1. Rule 2 owes evidence for WHICH number a gate reads. The status word now
   turns on a number that, without this key, would exist only inside the
   process. Printing the deciding number beside the word it decided is the
   repair this project has made four times under other names.
2. Rule 3b. `0/2` on a `MADE` line is the reading that proves the new branch
   did not fire; `nothing-measured` is the reading that says the heads never
   ran. Without the key those two are the same absence.
3. The formatter is in the tested layer and was run over all three shapes
   (lines 755, 785, 808), which is the instrument rule about arithmetic and
   strings living where the tests run.

The builder's claim about readers HOLDS as of this tree. The workflow appends
`(Get-Content $matOut -Raw).Trim()` verbatim (line 305); it writes
`materialStatus` itself only in its two no-run fallbacks (lines 295, 306) and
mentions it once in a comment (line 1065); nothing in it branches on the
value. No tool under `tools/` reads `ue-build.txt` or `ue-material.txt`. A
new key on a line nothing parses costs nothing and is read by the only reader
that matters, a verifier with the four frames beside it.

One rule 1 fault, dictated in D1: the docstring at lines 74 to 77 says the
key was "Ruled 2026-09-03". It was not; the word and the return were. From
this ruling on the attribution is true, and the docstring says which ruling
ordered which.

## 3. The spelling did not drift

`property_write_via` (line 203) builds
`none-of-%d-candidates..then.property-write-%s` with `took`, `unavailable`
or `refused`. With nine candidates that is
`none-of-9-candidates..then.property-write-refused` and `..unavailable`,
character for character the two strings section 4 of the 3 September ruling
quotes at line 330. That quotation is the only committed record of the step 1
spelling readable from here (no shell, no git), and it matches.

The suffix the counter keys on is `PROP_WRITE_TOOK = "property-write-took"`
and the producer spells `property-write-` plus `took` as a literal rather than
using the constant; that is a drift hazard, and selftest line 660 to 670 is
the guard for it: `property_write_via(9, True)` must end in the constant and
the other two must not. Traced: it does and they do not.

The run 19 and 20 literal, `materialNote=texcoord-to-maskU-refused/texcoord-to-maskV-refused`
(ue-build.txt line 12), is kept as a PREFIX by `uv_head_note`, which yields
`texcoord-to-maskU-refused-after-9-candidates`; selftest lines 647 to 652
guard the prefix. A grep for the run 20 token finds a run 21 refusal.

## 4. The three verdict lines

Traced from the fixtures, not run. The formatter is nineteen `key=%s` pairs
separated by single spaces; the values that could carry a space are the two
engine default paths (`.replace(" ", "~")`), the notes (joined by `/`) and
the candidate pin names (selftest line 557 refuses any carrying a space or an
equals). The selftest checks one equals per token programmatically on all
three lines (763, 792, 815).

- PARTIAL line: `materialUvHeadVia=both.none-of-9-candidates..then.property-write-unavailable`,
  `materialUvHeadTriedAtWorst=9/9`, `materialUvHeadReadback=0/2..unreadable2`,
  `materialUvHeadByPropertyWrite=0/2`, `materialDefaultsBound=1/2`. Every zero
  carries its denominator and the unreadable count is beside the no rather
  than folded into it.
- MADE line: `materialScriptReturn=0`, `materialConnections=14/14`,
  `materialUvHeadVia=both.out.empty..in.empty`,
  `materialUvHeadReadback=2/2..unreadable0`,
  `materialUvHeadByPropertyWrite=0/2`, `materialNote=none`.
- WIRED-BY-PROPERTY-WRITE line: `materialScriptReturn=2`,
  `materialConnections=14/14`,
  `materialUvHeadVia=maskU.out.empty..in.empty/maskV.none-of-9-candidates..then.property-write-took`,
  `materialUvHeadByPropertyWrite=1/2`.

`nothing-measured`: `uv_head_fields([])` returns it in all three positions
(the middle one as `nothing-measured/9`) and `property_write_heads([])`
returns `(0, 0, "nothing-measured")`; both checked at value level (lines 720,
746). No fixture prints a whole line in that shape. Not blocking: the
formatter is a `%` substitution and cannot alter a value on its way through.

Named, not fixed today: the `CREATE-FAILED` line at line 918 carries no
`materialScriptReturn` and none of the UV keys. Pre-existing, adjacent, and a
verifier reading run 21 must know it. Queue note in D2; it is not opened
before run 21.

## 5. The stop rule, ruled explicitly

The rule (3 September, carried in 062): `materialConnections` is the reading;
if it holds across two consecutive landed runs, no further dispatch until the
wire is fixed. It held at 12/14 across runs 19 and 20 and fired. The 3
September ruling, section 4, then authorised exactly one dispatch, run 21, on
two conditions: the third-state amendment has landed, and Jafar has lifted
"wait for now".

RULING: RUN 21 IS AUTHORISED ON THIS CODE, once this file is committed and
the sha is captured before dispatch. Condition one is met by the commit this
ruling approves. Condition two is met on the launching agent's report that
Jafar has ordered item 6 run; today's 09:02:36Z ruling placed "062 step 2,
run 21, the first textured frames to him as images" at item 5 of the standing
order. His words are not in the tree under that report: before dispatch the
resident records the date and the words as given in
`production/decision-queue.md` RULED, or, if the words were not kept, the
sentence "Jafar lifted wait on 2026-09-05; words not kept". A decision that
lives only in a brief decays into a preference.

The number the rule reads, and what it is a statistic of: `materialConnections`
is a cumulative count over the 14 connections asked for in ONE run; across
runs it is last-wins, because the asset is deleted and regenerated every run
(lines 908 to 913). It is the fraction, never the word, that the rule reads.

What run 21 must print for the rule to fire AGAIN: `materialConnections=12/14`,
under any status word and any via. That is a third consecutive landed run at
the same fraction. Per the 3 September ruling it is the answer: no scripted
route wires the head, D1's hand-edit clause is invoked, it is reported as an
answer and NOT retried. The via field then says which of the two hypotheses
died: `..property-write-refused` or `..unavailable` beside
`materialUvHeadTriedAtWorst=9/9`.

The other readings, so nobody has to rule from the log tail:

- `14/14 materialStatus=MADE materialScriptReturn=0`: the fraction moved and
  the first arm of 062's acceptance is met on a landed run. The frames are
  still read by a verifier (the still gate), and `materialUvHeadVia` names the
  pin pair so the sweep can be cut to one name next time.
- `14/14 materialStatus=WIRED-BY-PROPERTY-WRITE materialScriptReturn=2` with
  `materialUvHeadByPropertyWrite=1/2` or `2/2`: the fraction moved, the rule
  does not fire, and 062 is met ONLY when a verifier reads the four frames
  and sees tiling. Flat frames beside this word are a new finding (the write
  reaches the graph and not the shader) and no run 22 goes on this script
  without a director: a landing that changes a conclusion.
- `13/14`: moved, not met; the via names which head took. One further
  dispatch only with a changed instrument, and 21 to 22 holding at 13/14
  fires the rule again.
- `materialStatus=NO-LINE`, `NO-TOOL` or `CREATE-FAILED`: nothing measured on
  the wire. It neither discharges nor re-fires the rule and does not count as
  a landed reading of the fraction; re-dispatch needs a director.

Which of the three words run 21 prints is unknowable from this container:
`main()` needs `import unreal`. That is why the sweep exists.

## 6. The commit

APPROVED for these two files as part of the batch; the other files in the
tree carry their own review and this stamp does not cover them. Before the
commit the resident runs `python3 tools/ue/make_base_material.py --selftest`
AFTER applying D1 and pastes its summary line into the commit message
verbatim. It must read `40 check(s), 0 failure(s)`; any other pair and this
approval does not apply, because the builder's exit 0 is a report and the
pasted line is the reading. Stage by name. `production/d1-probe/DISPATCH` is
touched only by the dispatch step that follows, with the sha captured first.

## 7. Dictated edits, applied by the resident before the commit

D1. `tools/ue/make_base_material.py`, lines 77 to 78, replace
`Ruled 2026-09-03; MADE is unchanged and still means every head taken by a named pin.`
with:

    The word and the return were ruled 2026-09-03; the printed count was
    added under game-design/decision-2026-09-05-ruling-062-step-2-third-
    status-word.md. MADE is unchanged and still means every head taken by a
    named pin.

D2. `production/queue/062-uv-chain-head-refuses-to-wire.md`, append:

    ## STEP 2 LANDED 2026-09-05, RUN 21 AUTHORISED

    `material_status` takes the property-write head count; 14 of 14 with it
    above zero prints `materialStatus=WIRED-BY-PROPERTY-WRITE` and
    `materialScriptReturn=2`; 14 of 14 with `materialUvHeadByPropertyWrite=0/2`
    still prints `MADE`. Selftest 30 to 40 checks, both cases from head
    records. The deciding count is printed as `materialUvHeadByPropertyWrite`,
    adopted by the ruling. Ruling and the reading table for run 21:
    game-design/decision-2026-09-05-ruling-062-step-2-third-status-word.md,
    section 5. The rule fires again on `materialConnections=12/14`.

    NOTE, not before run 21: the `CREATE-FAILED` line in `main()` carries no
    `materialScriptReturn` and no UV keys. A verifier reading that word reads
    it as nothing measured. Fix when the file is next open.

D3. `production/NOW.md`, the bullet beginning
`**THE UNREAL STOP RULE IS STILL IN FORCE`, append one sentence:

    Step 2 landed 2026-09-05 and run 21 is authorised on it (ruling
    game-design/decision-2026-09-05-ruling-062-step-2-third-status-word.md,
    section 5, which carries the reading table).

## 8. The quality ladder at close

Unchanged from the 3 September ruling, section 8, and restated so it is not
lost: the file is at "a measurement replacing a guess", which is the right
rung for a question this container cannot answer. The next rung is run 21's
reading. The rung after it is the still gate reading tiling rather than a
status word, and the rung after that is a sweep cut to the one pin pair the
run named. None of those is blank.

<!--RULING spawn=2026-09-05T16:15:44Z paths=tools/ue/make_base_material.py,production/queue/062-uv-chain-head-refuses-to-wire.md,production/NOW.md,game-design/decision-2026-09-05-ruling-062-step-2-third-status-word.md-->
