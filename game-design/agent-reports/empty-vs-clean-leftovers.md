# The three leftovers: a run that measured nothing, reported as a finding

> **STATUS — LOG, 2026-08-26. NOT CURRENT** after the next change to
> `ledger/verify.py`, `tools/lint-filetype.py` or `tools/lint-unreached.py`,
> or once the items left for other owners in section 8 are taken. Every
> number below describes the tree at `c03ead22` plus these three files.

Agent: instrument-builder. Files touched: **`ledger/verify.py`,
`tools/lint-filetype.py`, `tools/lint-unreached.py` ONLY.** Not committed —
the resident commits after the director reviews. `tools/gates.py`,
`tools/gate-detail.py`, `tools/lint-namespace.py`, `tools/lint-avenues.py`,
`tools/lint-nested.py`, `tools/lint-static.py`, `tools/capsay.py` and
`ledger/Assets/**` were READ and RUN, never edited.

---

## 1. The series, before and after — this is the whole finding

**The probe.** `tools/` was copied over a tree with no `Assets/`
(`scratchpad/emptytree/`), every lint was run there for real, and its real
exit code and real output were handed to the `verify.py` wrapper that
consumes it. Only `run()` is stubbed; every other line is verify's own.
Nothing was written under `ledger/`.

Seven wrappers consume a `tools/lint-*.py`. **All seven, one table, one run
— not the two the brief named:**

**BEFORE**

    nested_types       tool exit=2 -> RED   CS0426 WAITING TO HAPPEN: see lint-nested
    static_instance    tool exit=2 -> RED   CS0120 WAITING TO HAPPEN: see lint-static
    filename_as_type   tool exit=0 -> GREEN 0 filename-as-type errors (0 files, 0 filenames that are not types)
    namespace_as_value tool exit=1 -> RED   CS0118 WAITING TO HAPPEN: see lint-namespace
    shadow             tool exit=2 -> RED   lint-shadow did not report
    conditional_reach  tool exit=2 -> RED   conditional-reach did not report
    raw_avenues        tool exit=2 -> RED   RAW AVENUE READ (unscaled coordinates): see lint-avenues

**AFTER**

    nested_types       tool exit=2 -> RED  lint-nested NOTHING MEASURED (exit 2, no source line named — it refused to look, so this is NOT CS0426): lint-nested: nothing measured — Core and Game not found (...)
    static_instance    tool exit=2 -> RED  lint-static NOTHING MEASURED (exit 2, no source line named — it refused to look, so this is NOT CS0120): lint-static: nothing measured — no Game folder at (...)
    filename_as_type   tool exit=2 -> RED  lint-filetype NOTHING MEASURED (exit 2, no source line named — it refused to look, so this is NOT CS0103): lint-filetype: nothing measured — no `.cs` file under (...)
    namespace_as_value tool exit=1 -> RED  lint-namespace NOTHING MEASURED (exit 1, no source line named — it refused to look, so this is NOT CS0118): lint-namespace: NO NAMESPACES FOUND — the check did not run
    shadow             tool exit=2 -> RED  lint-shadow did not report: lint-shadow: nothing measured — Core and Game not found (...)
    conditional_reach  tool exit=2 -> RED  conditional-reach did not report: lint-conditional-reach: nothing measured — no .cs file under (...)
    raw_avenues        tool exit=2 -> RED  lint-avenues NOTHING MEASURED (exit 2, no source line named — it refused to look, so this is NOT RAW AVENUE READ (unscaled coordinates)): lint-avenues: 0 file(s) swept, owner StreetMap.cs NOT FOUND (...)

Four of the seven claimed a compile error over a sweep that never happened;
one reported **GREEN**; two were honest but mute, flattening the tool's own
sentence to four words that read the same whether it refused or crashed.

**ONE IMPLEMENTATION, five call sites.** `_lint_red(code, out, finding, tool)`
in `ledger/verify.py` replaces the same three copied lines at
`nested_types`, `static_instance`, `filename_as_type`, `namespace_as_value`
and `raw_avenues`. The measured series above is pasted into the comment above
it, so the next reader gets the evidence rather than the conclusion.

**IT DOES NOT KEY ON EXIT 2, and that is the load-bearing detail.**
`lint-namespace` prints *"NO NAMESPACES FOUND — the check did not run"* and
exits **1**. A repair keyed on `if code == 2` — which is what the brief and
the sibling report both suggested — would have fixed two of the four and left
the third reporting a CS0118 that does not exist. The test that holds for all
of them is structural: **a lint that goes red without naming a `.cs:` line has
found nothing, whatever it exited with.**

---

## 2. `lint-filetype` — what it prints now

**On the live tree (exit 0):**

    lint-filetype: 0 filename-as-type error(s) (191 file(s) scanned, 465 type(s) declared, 13 filename(s) that are not types)
      ladder, each rung a cumulative count over the whole sweep: 9592 qualified reference(s) `Name.Member` in code -> 3497 whose `Name` is a filename in this project -> 0 whose filename declares no type, which is the finding
      not in the trap set, by reason, FIRST MATCH WINS in this order: 159 declare a type of their own name — the normal case, nothing to mistake [AccessSetup, Acoustics, Acquaintance (+156 more of 159)]; 11 are a member name somewhere, so `Name.` is a member access and compiles [ActOne, ActThree, ActTwo (+8 more of 11)]; 8 sit under Core/, where filenames collide with GameController properties by the dozen and a name-matcher cannot tell them apart [Access, Companionship, Homicide (+5 more of 8)]
      arithmetic: 13 trap(s) + 159 declaresType + 11 memberName + 8 underCore = 191 distinct filename stem(s); 191 stem(s) + 0 file(s) dropped as a duplicate filename stem [none] = 191 file(s) scanned

**Line 1 is byte-identical to what it printed before** — a landed series does
not get reworded, it gets added to. Lines 2-4 are new: the ladder (what was
examined at each rung, cumulative over the sweep), the trap set's complement
broken down by reason, and two identities a reader checks on the line.

**On an empty tree (exit 2):**

    lint-filetype: nothing measured — no `.cs` file under ledger/Assets/Scripts, ledger/Assets/Editor

**Three states now exit 2**, each printing what it DID count:

| state | line |
|---|---|
| no files | ``nothing measured — no `.cs` file under <roots>`` |
| files, no type declarations | `nothing measured — 1 file(s) read and 0 type declaration(s) found in any of them, so there is nothing to difference the filenames against` |
| files, types, **empty trap set** | `nothing measured — the trap set is empty: 0 of 1 distinct filename stem(s) name something that declares no type (1 type declaration(s) seen), so this sweep could not have found an error` |

The third is the quiet one and it is why the tool's own comment
(*"0 errors over an empty trap set means the convention changed, not that the
code is clean"*) was not enough: it printed the number and exited 0 anyway, and
the consumer reads the exit code.

**Exit codes: 0 swept and clean, 1 a CS0103 waiting to happen, 2 nothing
measured.** None of the three nothing-measured lines can match verify's pass
parse — asserted in the selftest, because a refusal a consumer's parse accepts
is the whole fault.

**A silent collapse was found and is now counted.** `stems.setdefault(f.stem, f)`
drops the second file of any repeated filename stem; the loser was never
counted anywhere. **0 today over 191 files**, and printed, so the day it stops
being 0 somebody is told.

---

## 3. `lint-unreached` — the brief's premise was wrong, the fault was real

**THE BRIEF AND `lint-empty-vs-clean.md` §7.4 BOTH SAY IT "PRINTS NOTHING AT
ALL AT EXIT 0" OVER AN EMPTY TREE. IT DOES NOT.** Re-run with the sibling
report's own probe — the HEAD file exec'd with its directory globals repointed
at a real empty directory:

    HEAD lint-unreached, globals repointed at an EMPTY dir:
      exit=0, 193 byte(s) of stdout
      'lint-unreached: 0 Game-layer files, 0 public methods, 0 that nothing else names.\nA name-matcher cannot see reflection, SendMessage or an inspector binding — read each one before believing it.\n\n'

193 bytes, not zero. **The real shape is worse than the reported one**: it
printed a full line of zeros in exactly the wording a healthy sweep uses, so
an empty tree and a clean layer were byte-similar and both exited 0. "Prints
nothing" would at least look like a broken tool.

Recorded rather than quietly corrected because it is rule 3 twice over: a
report saying something is missing is an ANALYSIS, and the second reader
(me, briefed from it) would have inherited it unchecked.

**On the live tree (exit 0), after:**

    lint-unreached: 6 public method name(s) that nothing else in the layer names (351 distinct name(s) from 426 declaration(s) in 94 file(s) walked: 88 under ledger/Assets/Scripts/Game, 6 under ledger/Assets/Editor)
      not examined, by reason: 13 declaration(s) of 1 name(s) are Unity lifecycle callbacks the engine invokes with no reference anywhere [Reset x13]; 62 declaration(s) of 23 name(s) repeat a name already declared — this tool asks about NAMES, so a repeat whose twin IS called reads as reached and no site of it is ever reported [Build x14, Ensure x8, Get x6, Report x6 (+19 more of 23)]
      arithmetic: 351 distinct + 13 Unity lifecycle + 62 repeat = 426 declaration(s) matched in 94 file(s) walked
      not counted as a finding: 2 name(s) reached from outside the codebase — BuildMac at ledger/Assets/Editor/CiBuild.cs:27 (-executeMethod in ledger-build-mac.yml); BuildWindows at ledger/Assets/Editor/CiBuild.cs:14 (-executeMethod in ledger-build-windows.yml)
      A name-matcher cannot see reflection, SendMessage or an inspector binding — read each one before believing it.

      ledger/Assets/Scripts/Game/PlayerCar.cs:180: AddressNow
      ledger/Assets/Scripts/Game/CoatHost.cs:159: Arrested
      ledger/Assets/Scripts/Game/NpcWalker.cs:712: ClearDetour
      ledger/Assets/Scripts/Game/OnnxSpeech.cs:927: DecodeChunk
      ledger/Assets/Scripts/Game/SaveSlots.cs:134: DeleteAll
      ledger/Assets/Scripts/Game/Audio.cs:1269: StopWorker

**On an empty tree (exit 2):**

    lint-unreached: nothing measured — no `.cs` file under ledger/Assets/Scripts/Game, ledger/Assets/Editor

**The old line said three things and two of them were false.** Confirmed by
probe against the live tree before anything was changed, and the numbers are
the brief's exactly:

    files walked: 94 = 88 Game + 6 Assets/Editor    (all 94 called "Game-layer")
    declarations matched: 426
      silently dropped as a Unity lifecycle name:  13   (every one of them `Reset`)
      silently collapsed onto an earlier same name: 62   (23 names; `Build` x14)
      distinct names examined:                     351   <- printed as "351 public methods"
    arithmetic: 351 + 13 + 62 = 426

**And the collapse is a blind spot, not only a bad denominator.** This tool
asks about NAMES. `Build` is declared 14 times; if thirteen were dead and one
called, the name reads as reached and no site of it is ever reported. That is
now printed with its size. **None of today's six findings is affected — all
six are singly declared**, checked by name.

**Exit codes: 0 the sweep ran and reported (with findings or without — this is
a reading, not a gate, and the commit that WIRES one of these must not be
blocked), 2 nothing measured. Never 1.**

**Same six findings before and after**, diffed:

    IDENTICAL findings before/after the rewrite: 6 of 6

**And it went from 38.5s to 0.23s.** Two whole-corpus regex sweeps per name,
351 times. Declaration counts now come from the single parse that already ran
and mentions from one tokenised pass — the same arithmetic, one implementation
of each. A 38-second hand-run tool is a tool nobody runs.

---

## 4. Was there a third exit-2 misreport? Two, and no consumer outside verify

- **`namespace_as_value`** — third site, **exit 1**, `lint-namespace` prints
  "NO NAMESPACES FOUND — the check did not run" and verify called it CS0118.
- **`raw_avenues`** — fourth site, exit 2, verify called it a raw unscaled
  coordinate read.
- **`shadow` and `conditional_reach`** reached an honest sentence by accident
  (their pass-parse simply fails to match); both now carry the tool's own
  words instead of four mute ones.

**Nothing outside `ledger/verify.py` consumes these tools' exit codes** —
grepped across `.github/workflows/*.yml`, `tools/*.sh` and every `.py`: the
eight other hits are prose in docstrings. The two workflows run
`ledger/lint-usings.py` only.

---

## 5. How I proved verify still parses

Three independent ways, because a changed string silently drops a number from
every future GREEN footer and nothing goes red when it does.

1. **`VERIFY_PARSE` is pinned inside `tools/lint-filetype.py`**, byte-identical
   to the literal in `ledger/verify.py`, and the selftest asserts BOTH that it
   matches the live line (with the right capture groups) and that the literal
   is still present in `verify.py`'s source:

       ok   ledger/verify.py's regex still matches the live line, and lifts the SCANNED and TRAP counts into the footer
            groups=('191', '465', '13') files=191 traps=13
       ok   and the copy kept in this file is byte-identical to the one in verify.py (if this fails, verify changed its parse — read it, do not edit this line to match)
            found in verify.py

2. **String fixtures in `verify.py`'s own `--selftest-strings`**, which runs in
   the main tuple on every commit, no subprocess: a clean sweep must lift both
   denominators (`191 files, 13 filenames that are not types`), and a real
   CS0103 must still read as a finding.

3. **End to end**: the full `ledger/verify.py` run in section 7.

**Four naked zeros were fixed while I was in there.** `nested_types`,
`static_instance`, `filename_as_type` and `namespace_as_value` each fell back
to a bare `"0 X errors"` when the tool's line stopped matching — a zero with
no denominator, in the channel that rides into commit messages. All four now
print `nothing-measured — lint-X printed no census`, the shape `shadow`
already used.

---

## 6. The selftests, ACCEPTING CASE FIRST — both outcomes watched

**`lint-filetype --selftest`: PASS — 14 checks, 0 failed.** Order: live tree
clean (the accepting fixture no fixture of mine can fake, since every hit on
today's code is a false positive by definition) → it examined something → the
identities → verify's parse both directions → synthetic accepting (a file that
declares its own type; a trap named in a comment and a plain string) → the
three nothing-measured states → only then the rejecting cases: the real
CS0103 in plain code, and the same one inside `$"..."`, which is the form that
scored zero on the very line that prompted this tool.

    lint-filetype --selftest: PASS — 14 checks, 0 failed
      denominators: live 191 file(s) scanned, 465 type(s) declared, 13 trap(s), 9592 qualified reference(s) examined; synthetic 7 fixture file(s), 0 written to disk, 0 project file(s) modified

**It can go red.** The historical bug put back — `INTERP.sub(" ", text)`,
throwing interpolated strings away — in a copy under scratchpad:

      ok   a filename with no type, read as a type in plain code, is caught
      FAIL and so is one inside `$"..."`, which IS code and which the first version threw away wholesale
           []
      FAIL a FINDING still ships its denominator — the summary prints beside the hits, not instead of them
    lint-filetype --selftest: FAILED — 14 checks, 2 failed

**`lint-unreached --selftest`: PASS — 12 checks, 0 failed.** Same order: live
sweep examined something → the arithmetic identity → the per-root breakdown
(the fix for "94 Game-layer files") → synthetic accepting (a method called from
another file, and one called through a reference, are not reported) → nothing
measured → rejecting (a public method nothing names IS reported; two
declarations of one name are collapsed, and both the collapse and the
first-site-only cap announce themselves).

    lint-unreached --selftest: PASS — 12 checks, 0 failed
      denominators: live 426 declaration(s) over 94 file(s) (ledger/Assets/Scripts/Game=88, ledger/Assets/Editor=6), 351 distinct name(s), 6 finding(s); synthetic 5 fixture file(s), 0 written to disk, 0 project file(s) modified

**It went red on me before it passed**, which is the only reason I trust it:
the twin fixture caught my own double-count (`SynthTwin x3` printed for two
declarations — `decls[n] + repeats[n]` where `decls[n]` already counts them
all). Found by the suite, not by a reader, before the number reached this
report.

    FAIL two declarations of one name are COLLAPSED — and the collapse is printed with its size
    lint-unreached --selftest: FAILED — 12 checks, 1 failed

**Both selftests are dispatched at the top of `main()` and RETURNED FROM** —
`lint-shadow`'s fell through to the live sweep and exited 0, so a guard that
had never run looked exactly like one that passed. Every rejecting fixture is
synthetic, in memory, `Synth*`-named, never on disk: wiring up a real method or
renaming a real file cannot break these tests.

**`lint-filetype --selftest` now runs inside `verify.py` on every commit** —
sweep first, selftest second. The order is the point: run the guard first and
a REAL CS0103 comes back as "the lint is broken", because the selftest asserts
the live tree is clean. A finding must report as a finding.

---

## 7. `ledger/verify.py` — the run

**`python3 ledger/verify.py` — NOT GREEN, and `ledger/.verify-footer` does
not exist on disk, which is the file doing its job.** Read from disk after the
run:

    $ cat ledger/.verify-footer
    cat: ledger/.verify-footer: No such file or directory

**The single red is `ref_bench`, and it is not mine.** `tools/ref-bench.py` is
unmodified in the working tree (`git status` clean for it) and its selftest
fails as its own separate process, with zero of my code involved:

    $ python3 tools/ref-bench.py --selftest
    ref-bench selftest: 98 passed, 3 failed
      FAILED accepting: district_hook is NOT low-content (groundMean:0.547>0.543)
      FAILED accepting: district_hook's inputs are inside every bound it is judged by (groundP90 0.770 in 0.233..0.831, groundMean 0.547 in 0.142..0.543)
      FAILED accepting: district_hook's line says lowContent=none ratioUnreadable=none
    EXIT=1

**Cause, measured:** HEAD is `b63e271f` "Sim stills from c03ead2", which
replaced `game-design/sim-shots/district_hook.jpg` at 02:29 UTC. The previous
green `.verify-footer` on disk was written at 02:10 UTC. `ref-bench`'s
ACCEPTING fixtures are pinned to that live still, so the build landing moved
one reading 0.004 past a bound (`groundMean 0.547` against a `0.142..0.543`
range) and the tool's accepting case broke because the work was done. That is
the trap this studio names out loud — a fixture pinned to a real asset breaks
when the asset improves — and it now blocks every commit until somebody rules
on the bound. **Director call, not mine: it is another owner's file and rule 2
forbids moving a bound to make red go away.**

**Every check touching my three files is green, run directly on the live
tree:**

    ref_bench          False REF BENCH: accepting: district_hook is NOT low-content (groundMean:0.547>0.543) (+2 more of 3)
    nested_types       True  0 nested-type errors (255 Core types)
    static_instance    True  0 static/instance errors (75 members, 29 bodies)
    filename_as_type   True  0 filename-as-type errors (191 files, 13 filenames that are not types)
    namespace_as_value True  0 namespace-as-value errors (191 files, 4 segments in scope)
    raw_avenues        True  0 raw avenue reads, 9 DEFERRED (185 files)
    shadow             True  0 shadowed Core types (285 Core type(s) across 88 Game file(s))
    conditional_reach  True  0 unreachable behind #if (1 type(s) checked)

**And the two footer numbers that moved:** `27 footer-string fixtures
(accepting and rejecting)` — **17 at `c03ead22`, ten added here** (4 accepting,
6 rejecting), counted by `say(` calls in both versions rather than from
memory — and
`0 filename-as-type errors (191 files, 13 filenames that are not types)`,
unchanged to the digit, which is the point of pinning the parse.

`python3 tools/docs-check.py` — **112/112 clean**, including this report (111
before it existed).

Other agents' work is uncommitted in this tree (`tools/gates.py`,
`tools/gate-detail.py`, `game-design/queue.md`, `.claude/agent-log.tsv`); none
of it is mine and none of it is red.

---

## 8. Left for another owner — named, not edited

1. **`tools/lint-namespace.py` returns 1 for "the check did not run"** (no
   namespaces found), which is a nothing-measured state wearing a finding's
   exit code. verify now reads it correctly by structure, but the tool should
   exit 2 with the words like its siblings. **Measured on the empty-tree copy,
   all eight:** `lint-static`, `lint-nested`, `lint-shadow`,
   `lint-conditional-reach` and `lint-avenues` exit 2 with the words;
   `lint-filetype` and `lint-unreached` exited 0 and now exit 2 with the words
   (**seven of eight**); `lint-namespace` does refuse, but with exit 1 and its
   own wording, and it is the eighth.
2. **`lint-unreached` is wired into nothing.** It is a hand-run reading, so no
   footer carries it and no series lands. Now that it costs 0.23s instead of
   38s, a `--selftest`-guarded wrapper in verify is cheap — but it should be a
   READING, not a gate, and verify has no shape for that today. Director call.
3. **`nested_types()` still lifts only the reference count** (`255 Core types`)
   into the footer while the walked set is now printed by the tool — item 2 of
   `lint-empty-vs-clean.md` §7, still open, deliberately not taken here: it
   changes a landed footer number and belongs in the same review as the
   nested/shadow rewrite.
4. **`_Fake` fixture doubles now exist in five lints** (static, nested, shadow,
   filetype, unreached). `capsay` is the precedent for extraction; it would
   touch four files I do not own. Named, not done.
5. **The silent first-wins collapse, grepped for its twin.** `setdefault(k, v)`
   used as "first wins" appears at two other sites, both read: `tools/gates.py:137`
   (a sha-prefix index — ambiguity already called out in that tool's own NOTE)
   and `tools/verdict-reach.py:248` (`stranded.setdefault(key, head)`, where the
   value is only a witness line for display and each key prints its own row).
   Neither inflates a denominator the way the two I own did. Both are other
   owners' files; named, not touched.
6. **`lint-filetype`'s trap set is a per-file name-match**, so a stem excluded
   because it is a member name ANYWHERE is excluded everywhere (11 today).
   Measured and printed rather than narrowed — narrowing a name-matcher with
   nothing currently to catch is how both earlier lints of this family started
   flagging code that compiles.

---

## 9. What this confirms and what it overturns

- **Overturns** `lint-empty-vs-clean.md` §7.4 and this brief's item 3:
  `lint-unreached` did NOT print nothing over an empty tree. It printed 193
  bytes reading `0 Game-layer files, 0 public methods, 0 that nothing else
  names` at exit 0 — the same wording a healthy sweep uses, which is the worse
  of the two shapes.
- **Overturns** the implicit "two sites" framing of the exit-2 fix. There were
  **four** misreports in `verify.py`, and one of them (`namespace_as_value`)
  exits 1, so the obvious `if code == 2` repair would have left it in place.
- **Overturns** "`lint-filetype` exits 0 on an empty tree, and a human can
  tell" as the whole of that finding: the human-readable zeros were there,
  but `verify.py` printed **GREEN** over them, so the only consumer that
  decides anything could not tell at all.
- **Confirms** `lint-empty-vs-clean.md` §7.1 exactly, including both quoted
  strings, and confirms its §7.5 (`lint-filetype` exit 0) and the brief's
  arithmetic for `lint-unreached` (94 = 88 + 6; 351 + 13 + 62 = 426) to the
  digit.
- **Confirms** that the live codebase is the accepting fixture worth having:
  both new selftests pass on it, and both went red first — one on a
  reintroduced historical bug, one on a real arithmetic slip of mine.
- **New, and nothing could see it before:** `lint-unreached`'s NAME-level
  question is blind to 62 declarations of 23 names, `Build` fourteen times
  over; and `lint-filetype`'s ladder meets the code at 9592 qualified
  references, 3497 of them on a filename.
