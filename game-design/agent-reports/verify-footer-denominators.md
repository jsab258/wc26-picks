> **STATUS: LOG, 2026-08-26. NOT CURRENT after the next change to
> `ledger/verify.py`, `tools/shape-check.py` or `tools/capsay.py`.** Builder
> report. Work landed in the tree, NOT committed — the director reviews and
> the resident commits.

# The footer that rides into every commit message now carries its denominators

Fixes for all three findings in `denominator-sweep.md`. Files changed:
`ledger/verify.py`, `tools/shape-check.py`, and one new file
`tools/capsay.py` (staged so `tools_tracked` sees it; not committed).

---

## The headline, and it is a pair

Five footer fragments that were **byte-identical across 259 landed commits**
now carry a live denominator, read from disk after a green run:

    0 lint errors (185 file(s) walked of 191 present; 6 file(s) of the
        2 root(s) given went UNWALKED (Scripts/Editor))
    0 shadowed Core types (285 Core type(s) across 88 Game file(s))
    0 stale anchors (205 anchor(s) in 22 break spec(s))
    clip picker ok (65 shipped name(s) read, 64 accepted, posture screen
        9 accepted/5 refused, 137 of 145 pattern(s) match a catalogued name)
    voice cast ok (0 uncast of 7 tier-1 principal(s); 17 cast voice(s),
        2 alias(es), 23 clip(s))
    shape ok (23 clip(s) cast/23 probed, 42 bark slot(s)/2604 line(s),
        manifest paths nothing-measured of 1 path-shaped in 7 file(s))

Two of those numbers — `205 anchors in 22 specs` and `185 of 191` — match
the sweep's independently-measured values exactly, which is the only
cross-check available for a number nobody has read before.

**The sixth fragment is the interesting one.** `shape ok (clips, barks,
manifests)` did not merely lack a denominator; the noun "manifests" was a
claim over **zero examined paths**, and it now reads
`manifest paths nothing-measured`. That word is in a green footer on
purpose: rule 3b's own prescription, so a clean sweep over nothing cannot
read as a clean sweep.

---

## 1 — the four that already had their number, plus the two that had none

| fragment | now carries | where the number came from |
|---|---|---|
| `0 lint errors` | `185 file(s) walked of 191 present` + a **measured** drop clause | `m.group(1)`, which was captured and discarded |
| `0 shadowed Core types` | `285 Core type(s) across 88 Game file(s)` | the tool's own parenthetical, previously ignored by a hardcoded literal |
| `voice cast ok (0 uncast ...)` | `0 uncast of 7 tier-1 principal(s); 17 cast voice(s), 2 alias(es), 23 clip(s)` | `voice-cast-check.py`'s header line |
| `clip picker ok` | three censuses, both rule-5b outcomes | `shipped names:` / `posture screen:` / `patterns:` lines the picker already printed |
| `0 stale anchors` | `205 anchor(s) in 22 break spec(s)` | counted inside the walk that does the work |
| `shape ok (clips, barks, manifests)` | six counts | a new `shape-check:` census line (finding 2) |

### A NEW FINDING, and it is the one worth reading

Fixing `lint()` meant asking what its 185 actually counted. **It counts
`ledger/Assets/Scripts` only.** `ledger/lint-usings.py::main` reads
`sys.argv[1]` and never looks at `argv[2]`, so the second root verify passes
has been **accepted and silently discarded since the day it was added** — 185
walked, 191 present, the 6 unwalked being `Assets/Editor`.

The comment sitting directly above that call said:

> *"ASSETS/EDITOR TOO. It was checked by nothing: lint and ShapeCheck both
> scanned only Assets/Scripts, so `CiBuild.cs` — the entry point the whole
> Windows pipeline runs through — had never been linted or shape-checked"*

That is **true of ShapeCheck** (which takes both roots and uses them: its
footer reads `191 files`) and **false of lint-usings**. Rule 1's second
corollary, live. The paragraph is kept quoted in the code rather than
deleted, because it was plausible to everyone who read it including whoever
wrote the argument list.

**The clause is DERIVED, not written.** `present` is counted at the call
site; `walked` comes from the tool; when they agree the clause disappears on
its own, so fixing `lint-usings.py` cannot leave a stale sentence behind. The
fix itself belongs in `ledger/lint-usings.py`, which this agent does not own —
**this is a live open item for whoever does.**

This is a second walk of the *file list*, not a second implementation of the
*lint*. It answers only "what did that denominator count", which is exactly
the question rule 3b's `lint-static` incident turned on (560 printed against
29 scanned).

---

## 2 — the manifest check: `ok` over zero paths

`tools/shape-check.py::referenced_files`. Two separate repairs:

**The walk was one level deep.** `.glob` -> `.rglob`, measured before and
after so the widening is a fact rather than a hope:

    glob :  files=4  strings=12345  pathShaped=1  checked=0  droppedSpace=1
    rglob:  files=7  strings=13442  pathShaped=1  checked=0  droppedSpace=1

**Three more files, 1,097 more strings, zero change to any verdict.** I
widened it anyway: one of the three unwalked files is literally
`game-design/voice-conds/manifest.json`, and the function's own sentence is
"every path a design manifest names". But the widening is not the fix — the
fault was that nothing said the walk had stopped.

**`checked == 0` no longer prints `ok`.** It prints the words and the
arithmetic, and `check()` is deliberately not called, because this is neither
a pass nor a fail:

    ---- every file path a manifest names exists: nothing-measured — 0 path(s)
         checked (1 path-shaped string(s) of 13442 in 7 .json file(s) walked
         under game-design/; 1 dropped for a space, 0 for a URL)

Both drops are now counted separately (space, URL). It is **not** turned into
a failure: nothing is broken, the manifests genuinely name no repo-relative
paths today, and failing would be the ratchet rule 5 forbids.

`shape-check` now ends with a `key=value` census line, no spaces in any value:

    shape-check: ok clipsCast=23 clipsProbed=23 clipsPending=0 barkSlots=42
    barkLines=2604 manifestFiles=7 manifestStrings=13442 manifestPathShaped=1
    manifestPaths=nothing-measured manifestDropped=1 problems=0

and `verify.py::shape_files` **requires** it. A green exit with no census is
now red, because that state is indistinguishable from a green exit over an
empty tree — and both printed `shape ok` before.

---

## 3 — the 48 truncations: all 48 reached, mechanically verified

**One implementation, in `tools/capsay.py`, imported by both tools.** The
first draft was a private `_cap` inside `verify.py`; that would have been two
implementations of `(+N more)` in two tools, which is the shape this project
has paid for three times (`SpeechBubble`/`NpcWalker`,
`verdict-keys`/`gates.py`, `TightestGap`/the job trace). `verify.py` imports
it as `_cap` so the call sites read the same.

**Coverage, checked mechanically rather than claimed.** Taking the brief's 48
line numbers against `HEAD`'s file, resolving each to its enclosing function,
and asking whether that function now routes through `_cap`:

    the brief's 48 sites, gone verbatim from the new file:   48 of 48
    distinct functions those sites live in:                  38
    of those 38 functions, now containing no _cap call:       0
    _cap( call sites in ledger/verify.py:                    58

The extra 10 are sites the brief did not list, found by grepping the
distinguishing token: `stale_anchors`, `barks_current`, `voice_gen`,
`shipped_cards`, `sheet_read`, `_cadence_selftest`'s own FAIL line, and the
inner `voice_live` per-script path. Two shapes were converted:

* `bad[0][:90]` and `bad[0][8:98]` -> `_cap(bad, strip=8, width=90, ...)`
* `next((... for l in out ...), "fallback")` -> a **list** plus `_cap`. This
  was the larger silent class: it kept one hit and discarded every other with
  nothing saying so.

**The worked example from the brief, before and after.** `verdict_keys` kept
four names and dropped the number while `verdict-keys.py` underneath was
already printing `N measurement(s) STOPPED BEING REPORTED`:

    before:  VERDICT KEYS GONE: a, b, c, d
    after:   VERDICT KEYS GONE: a, b, c, d (+36 more of 40)

### The two accepting fixtures did not regress

* **`shipped_cards`** (HEAD:642) printed `%d card(s)` and then `drift[:5]`.
  The `%d` is untouched; the slice now goes through `_cap`, so the count
  appears in both the sentence and the clause.
* **`_cadence_selftest`** (HEAD:3298) emits into a **`key=value`** channel,
  where `_cap`'s ` (+N more of M)` clause would inject spaces and truncate
  every reader. `_cap` was deliberately **not** applied there. Instead the
  count rides as its own whitespace-free token:
  `bad=%s badCount=%d scanned=%d want=%d`.

### One more hole found while sweeping

`sheet_read`'s **green** path took the last line of the tool's output
verbatim, so a tool exiting 0 with no output contributed an **empty fragment**
to the footer — a comma with nothing between it and the next, which reads as a
check that passed. It now requires the tool's `sheet-read ok (N checks)`
summary and prints `nothing-measured` otherwise.

### What I did NOT convert, and why

| site | what it is | left because |
|---|---|---|
| `_cadence_agents`' `splitlines()[:20]` | a front-matter READ window, not an output cap | it is an input heuristic; `agentFilesRead=` already ships beside it. **Residual: a `model:` line at line 21 would be silently counted as non-fable.** Named, not fixed |
| five `next((l ...), "")` picking a uniquely-prefixed SUMMARY line (`template-sync:`, `gate-detail:`, `verdict-dupkeys:`, `verdict-emit-dupkeys:`) | a selector, not a truncation of a finding list | each tool prints exactly one such line; a `(+N more)` clause there would be noise. **Residual: if a tool ever printed two, one is dropped in silence** |
| `_cadence_selftest`'s `bad=` | a `key=value` channel | see above — spaces are forbidden; solved with `badCount=` |

---

## How I established every parse still holds

This was the stated trap and it is where most of the checking went. **Every
string I touched, run through its real consumer, in this tree:**

| string changed | its consumer | how proved |
|---|---|---|
| `shape-check`'s new census line + the `ok` -> `---- nothing-measured` swap + the widened check label | `verify.py::shape_files` | called the real function against the real subprocess: returns `shape ok (23 clip(s) cast/23 probed, 42 bark slot(s)/2604 line(s), manifest paths nothing-measured of 1 path-shaped in 7 file(s))` |
| same | `tools/ci-checks.sh` (runs `shape-check` and `--selftest`) | read it: its only `grep` is inside its own selftest fixtures; the real table uses **exit codes** and a 120-line cap that announces itself. Ran `bash tools/ci-checks.sh --selftest` -> **15/15**. Output length 156 / 451 lines, against the 156 / 452 measured in its own comment — the cap's bite is unchanged |
| `shape-check`'s `check()` now accepting a list | `tools/shape-check.py --selftest` | ran it: **7/7 checks go red on broken input**, and its manifest fixture exercises the non-zero branch: `FAIL every file path a manifest names exists (1 checked of 2 path-shaped, 13443 string(s), 7 file(s))` |
| every changed **footer** fragment | `.claude/hooks/verify-gate.sh` | read it: the hook uses the footer's **existence and mtime only** and never parses its content. Ran `bash .claude/hooks/selftest.sh` -> **41 passed, 0 failed** |
| the regexes verify uses over `lint-usings`, `lint-shadow`, `voice-cast-check`, `pick_animations`, `shape-check` | `verify.py` itself | each check function called individually against the live tool, then the whole of `python3 ledger/verify.py` — **exit 0** |

**One live instance of the trap, caught by re-running.** Another agent
modified `tools/lint-shadow.py` while this work was in flight. Its output
line is what `verify::shadow` parses for the new census, so the parse was
re-run against the edited tool after the fact:

    lint-shadow: 0 shadowed Core types (285 type(s), 88 Game file(s))
      reference set: 285 Core type(s) from 97 of 97 Core file(s) read ...
      arithmetic: 88 walked + 0 not walked = 88 .cs file(s) offered ...

    verify::shadow -> (True, '0 shadowed Core types (285 Core type(s)
                              across 88 Game file(s))')

**Still parses, and the two agree**: 285 and 88 in verify's footer are the
same 285 and 88 the tool's own arithmetic line accounts for. The
parenthetical is OPTIONAL in the pattern for exactly this reason — if that
tool ever drops it, the footer says `nothing-measured` rather than
inventing a census.

**And the regex changes are guarded from now on**, which is the part that
does not depend on anybody remembering: `footer_strings()` is in the main
check tuple and feeds each formatter the output shape it expects. A tool
changing one word of its line turns verify **red** instead of quietly
reverting a green footer to a noun.

---

## Selftests, accepting case first, both outcomes watched

### `tools/capsay.py --selftest` — 12 fixtures, accepting five first

    capsay selftest — ACCEPTING CASES FIRST (a cap that bites on
    everything is the validator nothing survives)

      ok   one item, keep=1 — no clause                   'only one'
      ok   two items, keep=4 — no clause                  'a, b'
      ok   item shorter than width — no ellipsis          'short'
      ok   strip removes the tool's own prefix            'boom'
      ok   exactly at width — no ellipsis                 'xxxxxxxxxx'
      ok   four items, keep=1                             'a (+3 more of 4)'
      ok   five items, keep=4                             'a, b, c, d (+1 more of 5)'
      ok   last=True reads from the end                   'c (+2 more of 3)'
      ok   one char over width                            'xxxxxxxxxx...'
      ok   empty list gives the words                     'nothing-measured'
      ok   empty list, caller's own words                 'did not report'
      ok   the words carry no space                       False

    12 passed, 0 failed      (exit 0)

**The suite also has a rejecting case, because a suite that cannot go red
proves nothing when it is green.** `--broken` runs the same assertions
against a synthetic `cap` that never announces — the fault exactly as it
stood in 48 places:

      ok   one item, keep=1 — no clause                   'only one'
      ...
      FAIL four items, keep=1          'a'  wanted 'a (+3 more of 4)'
      FAIL five items, keep=4          'a, b, c, d'  wanted 'a, b, c, d (+1 more of 5)'
      FAIL last=True reads from the end 'c'  wanted 'c (+2 more of 3)'
      FAIL one char over width         'xxxxxxxxxx'  wanted 'xxxxxxxxxx...'

    8 passed, 4 failed
    --broken: the suite REFUSED the un-announcing cap      (exit 0)

The five accepting assertions still pass under `--broken`, which is the
point: they pin the "cap did not bite, so say nothing" behaviour that a
paranoid version would break.

### `python3 ledger/verify.py --selftest-strings` — 17 fixtures, six accepting first

    ok   lint: a clean walk carries its file count and claims no drop
    ok   shadow: the census survives the parse
    ok   voice cast: the finding keeps its denominator beside it
    ok   picker: all three censuses reach the footer
    ok   shape: three nouns became three counts, and the empty walk says so
    ok   stale anchors: a spec that matches once passes AND counts
    ok   lint: a short walk is named as a drop, not folded into the total
    ok   lint: a tool that printed nothing is not a pass
    ok   shadow: a NON-zero count is no longer hardcoded to zero
    ok   shadow: a tool that stopped printing its census says so
    ok   voice cast: exit 0 with no census is not a pass
    ok   picker: three missing censuses print three sets of words
    ok   shape: `shape ok` with no census cannot pass — the 259-commit fault
    ok   shape: a real problem still reports as one
    ok   stale anchors: a stale anchor reports N OF the walked total
    ok   stale anchors: an empty breaks/ is not `0 stale anchors`
    ok   capsay: the shared cap announces its bite and its empty case

    footer-string selftest: 17 passed, 0 failed      (exit 0)

**The live accepting fixture is the verify run itself** — every one of these
formatters is also called for real, against the real tools, in the same
process. What is synthetic is only what the live tree cannot produce on
demand: a red tool, a tool that went quiet, and an empty `breaks/`. The
synthetic fixtures name nothing that exists, so doing the work these checks
prompt cannot break them.

**And the suite was watched failing on the real fault.** A scratch copy of
`verify.py` with the two original faults put back — `shape ok (clips, barks,
manifests)` and the hardcoded `return True, "0 shadowed Core types"`:

    FAIL shadow: the census survives the parse — 0 shadowed Core types
    FAIL shadow: a NON-zero count is no longer hardcoded to zero — 0 shadowed Core types
    FAIL shape: three nouns became three counts, and the empty walk says so
         — shape ok (clips, barks, manifests)
    FAIL shape: `shape ok` with no census cannot pass — the 259-commit fault
         — shape ok (clips, barks, manifests)
    ...
    10 passed, 7 failed

    footer_strings -> (False, 'FOOTER STRINGS BROKEN: 7/17 fixtures failed
    — FAIL lint: a clean walk carries its file count ... (+6 more of 7)')

That last line is the deliverable checking itself: **the red message about
truncation is itself truncated, and says so.**

---

## The footer, read from `ledger/.verify-footer` on disk

`python3 ledger/verify.py` -> **exit 0**, 3,823 bytes written to
`ledger/.verify-footer` at 01:55, re-run after this report landed so the
footer on disk describes the final tree (`docs 109/109 clean` counts it).
Read back from the file, not from scrollback. The fragments this work
changed:

    17 footer-string fixtures (accepting and rejecting)
    0 lint errors (185 file(s) walked of 191 present; 6 file(s) of the 2 root(s) given went UNWALKED (Scripts/Editor))
    0 shadowed Core types (285 Core type(s) across 88 Game file(s))
    shape ok (23 clip(s) cast/23 probed, 42 bark slot(s)/2604 line(s), manifest paths nothing-measured of 1 path-shaped in 7 file(s))
    voice cast ok (0 uncast of 7 tier-1 principal(s); 17 cast voice(s), 2 alias(es), 23 clip(s))
    sheet reader ok (7 checks)
    0 stale anchors (205 anchor(s) in 22 break spec(s))
    clip picker ok (65 shipped name(s) read, 64 accepted, posture screen 9 accepted/5 refused, 137 of 145 pattern(s) match a catalogued name)

`DIRECTOR NOT SPAWNED` did not appear — the run read
`director cadence ok ... REVIEWED`, so it had already been cleared. **The
run is fully green.** `tools/capsay.py` is **staged** (`git add`) so
`tools_tracked` sees it; nothing is committed.

---

## Keys and names added

| name | where | what it is a statistic of |
|---|---|---|
| `tools/capsay.py::cap` | new module | the one truncation formatter; `(+N more of M)` is a COUNT of what the cap ate from the list as handed in |
| `tools/capsay.py::NOTHING_MEASURED` | new module | the words, no space, for the never-ran case |
| `shape-check: clipsCast/clipsProbed/clipsPending` | `tools/shape-check.py` census line | COUNTS over one run; `cast` vs `probed` diverging is the state that once hid two characters sharing one voice |
| `shape-check: barkSlots/barkLines` | same | COUNTS over one run |
| `shape-check: manifestFiles/manifestStrings/manifestPathShaped/manifestPaths/manifestDropped` | same | COUNTS over one walk; `manifestPaths` carries the WORDS when it is zero |
| `shape-check: problems` | same | COUNT of failing checks |
| `badCount` | `verify.py::_cadence_selftest` | COUNT of spend-token failures, beside a `bad=` list capped at 3 |
| `footer_strings` | `verify.py` main tuple | COUNT of footer-string fixtures that passed, both directions |
| `--selftest-strings` | `verify.py` flag | the same suite with its per-fixture lines |

---

## What this confirms and what it overturns

**Confirms**, with numbers where there were none: `denominator-sweep.md`'s
finding 1 (six identical strings), finding 2 (`0 checked + 1 dropped = 1
path-shaped of 12,345 in 4 of 7 files` — reproduced exactly, and 7 of 7 after
widening), and finding 3's arithmetic (48 sites, 2 already carrying a count,
across 38 functions).

**Overturns nothing in the sweep.** It adds one conclusion the sweep did not
reach, because it was one layer further down: **`0 lint errors` covered 185
of 191 files, and the 6 it missed are exactly the set the comment beside it
claimed coverage of.** Nobody could have known that from the footer, because
the footer had no number in it — which is the whole argument.

## Open, for whoever owns the file

1. **`ledger/lint-usings.py::main` reads `sys.argv[1]` only.** Six files
   under `Assets/Editor` — including `CiBuild.cs` — are passed and never
   walked. The footer now says so on every commit; the fix is one loop.
   *Note before fixing:* `core_type_names(root)` is derived from the same
   single root, so a naive per-root loop would run `check_core_using` against
   an empty Core-type set for `Assets/Editor`. The two roots need one shared
   `core_names`, not two independent runs.
2. **`_cadence_agents` reads only the first 20 lines** of each agent
   definition looking for `model:`. Silent if one sits lower.
