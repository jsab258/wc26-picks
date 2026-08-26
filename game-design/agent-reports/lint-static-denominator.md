# lint-static's denominator — the exemplar of rule 3b was the fault

> **STATUS — LOG, 2026-08-25. NOT CURRENT** once `tools/lint-static.py`
> changes again or the follow-ups in section 7 are taken.
Agent: instrument-builder. Tree `f26ed5fd` + the CLAUDE.md correction.
Files touched: `tools/lint-static.py` ONLY. **Not committed** — the resident
reviews and commits.

---

## 1. The live numbers — the 560/29 measurement CONFIRMED, and one correction

The other builder's reading is right in mechanism and right in every figure
that matters. One correction, and it is about the *moment* rather than the
arithmetic: **the total is a moving number.** Two runs of the OLD tool four
minutes apart, same command, same session:

    lint-static: 0 static/instance errors (75 instance members across 2 partial class(es), 560 static bodies walked)
    lint-static: 0 static/instance errors (75 instance members across 2 partial class(es), 562 static bodies walked)

Another agent is editing `WorldBuilder.cs` in this tree right now. So 560 and
562 are both true and neither is wrong — but the old tool read every file
THREE times per run (`collect`, `static_bodies`, `scan_file`), which means one
printed line could carry three different moments of the same moving file.
That is fixed below as well, and it is a measurement fix, not a speed one.

Measured at one instant, from one set of reads:

| | |
|---|---|
| files offered to the walk | **88** |
| files walked (`scan_file` entered) | **14** |
| files not walked | **74** |
| static bodies offered | **562** |
| static bodies walked | **29** |
| static bodies never opened | **533** |
| classes owned | 2 — `GameController` (9 files), `DialogueUI` (5) |
| instance members collected | 75 |

**19.4x inflation, confirmed.** All 74 drops have ONE cause: the file declares
no `public partial class`. Zero files declare two partial classes; zero owned
classes lack an instance member — so the other two silent-drop paths exist and
have never fired, which is itself worth knowing.

Checked rather than assumed: 15 Game files contain the string `partial class`;
the 15th is a prose mention in a `//` comment at `SimDirector.cs:15318`. No
declaration form (`internal partial`, `sealed partial`) is being missed, so 14
is the right walked set and the scope is exactly what the director ruled it is.

### The landed series — this is what the inflation actually cost

The number rides into every green commit message through the verify footer.
Reading it back out of the commit feed, **550 landed commits carry it**:

    2026-08-25  560 bodies      <- newest
    2026-08-25  559, 559, 557, 557
    2026-08-25  538, 538, 537 x 11
    2026-08-25  532, 532, 532, 531, 531, 531, 531
    2026-08-25  529, 529, 529, 529, 526, 526, 523 x 4
    2026-08-24  522, 522, 522, 521 ...
    ...         418 bodies      <- oldest of the 550

The whole visible range is **418 -> 560**, and the walked set was 29 for all of
it. So the footer showed a denominator that CLIMBED steadily over two days —
reading as coverage growing with the codebase — while actual coverage never
moved at all. That is the specific harm: not a wrong number sitting still, but
a wrong number that *tracks* something and therefore looks alive.

(`75 members` is constant across the newest ~40 and takes only three values —
72, 73, 75 — across all 550. A `gates.py --constant` signal, noted not chased.)

---

## 2. What the line prints now

Live, this run:

    lint-static: 0 static/instance error(s) (75 instance members across 2 partial class(es) in 14 file(s), 29 static bodies walked); 533 static bodies in 74 file(s) NOT SCANNED — outside partial-class scope
      not scanned, by reason: 533 bodies in 74 file(s) declare no `public partial class` — outside this tool's scope by design, a CS0120 hides in a type SPREAD across files; 0 bodies in 0 file(s) declare two partial classes — member attribution would be a guess; 0 bodies in 0 file(s) declare a partial class with no instance member — nothing for a static body to reach
      arithmetic: 29 walked + 533 not scanned = 562 static bodies in 88 file(s) offered

Line 1 carries BOTH halves because a reader greps `lint-static:` and sees line
1 and nothing else — the drop clause is not allowed to live only on a
continuation line a grep will miss. Lines 2 and 3 break the skipped set down
per reason and print the sum, so walked and not-scanned can be checked against
offered without re-deriving either.

**The scope was not touched.** 14 files in, 74 out, exactly as before. The only
change is that the 74 are now said out loud instead of being added to the
total. `tools/lint-conditional-reach.py`'s unwalked-Core/Editor clause is the
style copied; no second style was invented for the same job.

### The structural repairs, not just wording

1. **The count is derived from the walk.** `Reading.walked` is the list
   `scan()` appends to at the moment it hands a file to `scan_file()`.
   `walked_bodies` sums over that list. There is no longer a parallel
   `for f in files` loop beside the walk to drift from it — one idea, one
   implementation, so the two cannot disagree again.
2. **One read per file per run**, shared by the body count, the member
   collection and the scan, so all three numbers on the line come from the
   same moment of a tree that is being edited underneath them.
3. **Named drop reasons**, and the two that are NOT by design
   (`twoPartialClasses`, `noInstanceMember`) name their files with a cap that
   announces itself (`(+N more not shown)`). The by-design 74 need no roll
   call. The `noInstanceMember` path used to be a bare `continue` in `scan()`
   with no record at all.
4. **Distinct exit codes**, and `nothing measured` can no longer read as clean:

       0  walked, no candidate found
       1  at least one CS0120 candidate
       2  NOTHING MEASURED — no Game folder, no `.cs` files, or no file in
          partial-class scope

   The old tool returned **0** for "Game not found" and would have returned 0
   for a walk that entered nothing. Both now print the words *nothing measured*
   and exit 2, and neither string matches verify's pass parse.
5. **SIGPIPE guarded** (`signal.SIG_DFL`), so `| head -1` cannot end a correct
   run in a traceback. It could before; I hit exactly that with my own probe
   script while measuring this.

### One inherited comment was false, found by re-reading what I touched

`INSTANCE`'s comment said *"An instance member: public/internal, NOT static"*.
The regex has only ever matched `public`. Measured before rewriting the words:
**0 `internal` non-static members exist in the 14 walked files today**, so the
gap is real and currently empty. The comment now says what the regex does and
carries that measurement; the pattern was NOT widened, because widening a
name-matcher with nothing to catch is how both earlier lints of this family
started flagging code that compiles.

---

## 3. Which line of `verify.py` reads this tool, and how it was kept fed

**`ledger/verify.py:947`, inside `static_instance()`, and it is the ONLY
machine consumer in the repository:**

    m = re.search(r"\((\d+) instance members.*?(\d+) static bodies walked\)", out)
    return True, ("0 static/instance errors (%s members, %s bodies)" % (m.group(1), m.group(2))
                  if m else "0 static/instance errors")

`tools/gamecheck.py` names `lint-static` in prose only and does not run it.
Nothing else greps the line.

**This was the trap, exactly as briefed.** The regex requires the literal
`\)` immediately after `static bodies walked`, and `.` does not cross newlines.
The obvious rewrite — `29 static bodies in 14 file(s) walked` — would have
MISSED, and verify would have silently fallen through to the bare
`"0 static/instance errors"` with no denominator at all, in every future green
footer, with no red run anywhere to say so. That is rule 3b regressing one
layer up, in the channel people actually read.

**How it is kept fed.** The file count went INSIDE the parenthetical before the
body count, and the drop clause went AFTER the closing paren:

    (75 instance members across 2 partial class(es) in 14 file(s), 29 static bodies walked); 533 static bodies in 74 file(s) NOT SCANNED — ...

`.*?` swallows `across 2 partial class(es) in 14 file(s), ` and the anchor
`(\d+) static bodies walked\)` still lands on `29 ...walked)`. Verified by
running the real consumer, not by reading it:

    >>> verify.static_instance()
    (True, '0 static/instance errors (75 members, 29 bodies)')

**Before this change that same call returned `(75 members, 562 bodies)`.**
The footer that rides into the next commit message is now honest, and the
correction is visible against the 550-commit series above.

**Pinned in both directions by the selftest**, so this cannot decay:
* the summary line still matches the regex, AND the number lifted is the
  WALKED count (not just "something matched");
* the copy of the regex kept in `lint-static.py` (`VERIFY_PARSE`) is asserted
  byte-identical to the one in `verify.py`. If verify changes its parse, the
  selftest names it and says *read verify.py, do not edit this line to match*.

---

## 4. The selftest — 17 checks, ACCEPTING CASE FIRST

`python3 tools/lint-static.py --selftest` (also accepts `--self-test`).
Exit 0 pass, 1 fail. Fixtures are in-memory `_Fake` objects: nothing is written
to disk at any point, so no rejecting case is pinned to a real project file and
doing the work this tool prompts cannot break the tool.

**The selftest went red on its own arithmetic before shipping**, which is the
only reason one of its numbers is measured rather than assumed: I asserted the
two-partial-classes fixture had 1 static body. It has 2 — one in each of its
two partial classes. The tool was right; my expectation was wrong. That is
recorded in a comment beside the line.

    ACCEPTING — the live codebase, which is the best fixture available
      ok    today's Game layer passes — every hit on code that compiles is a false positive by definition   [0 finding(s) over 14 walked file(s)]
      ok    and it examined something — a zero here is the silence rule 3b exists for   [29 static bodies in 14 of 88 file(s) walked]
      ok    the printed denominator IS the walk — walked + not-scanned = offered, in files and in bodies   [29+533=562 bodies, 14+74=88 files]
      ok    ledger/verify.py:947's regex still matches, and lifts the WALKED count into the footer   [groups=('75', '29') walked=29]
      ok    and the copy kept in this file is byte-identical to the one in verify.py (if this fails, verify changed its parse — read it, do not edit this line to match)   [found in verify.py]

    ACCEPTING — synthetic code with nothing wrong
      ok    an instance method using an instance member, and two static methods using neither, all pass   [0 finding(s) of 2 bodies walked]
      ok    and one reached THROUGH a reference is not flagged   [0 finding(s)]

    THE DROP CLAUSE — files inside and outside partial-class scope, in one walk
      ok    both counts are reported and they are RIGHT — 2 bodies in 2 files walked, 4 bodies in 1 file not scanned   [walked 2 bodies/2 files, not scanned 4 bodies/1 files]
      ok    and they SUM to the total mentions   [2+4=6 bodies over 2+1=3 files]
      ok    THE 19x BUG ITSELF — the line says 2 walked, never 6, and names the 4 it did not open   [0 static/instance error(s) (1 instance members across 1 partial class(es) in 2 file(s), 2 static bodies walked); 4 static bodies in 1 file(s) NOT SCANNED — outside partial-class scope]

    THE DROP CLAUSE — the two reasons that are NOT by design
      ok    a file declaring two partial classes is counted under its own reason and NAMED (attribution would be a guess)   [2 bodies in 1 file(s): ['SynthTwo.cs']]
      ok    a partial class with NO instance member is counted under its own reason, not folded into the walk   [1 bodies in 1 file(s), measured=False]

    NOTHING MEASURED — the case that must not read as clean
      ok    an empty walk prints the WORDS, never `0 ... errors`, and does not match verify's pass parse   [lint-static: nothing measured — no `.cs` file under /nowhere]
      ok    and a walk offered files but entering none says so WITH its denominator, and still cannot read as a pass   [lint-static: nothing measured — 0 of 1 file(s) offered are in partial-class scope, so nothing was scanned; 4 static bodies in 1 file(s) NOT SCANNED]

    REJECTING — the CS0120 this tool exists for
      ok    the real CS0120 — a static ALLMAN method reaching an instance member — is caught (the shape the first version could not see)   [2 of 2 uses, members=['Populace']]
      ok    and so are the one-line and expression-bodied forms   [2 of 2]
      ok    a FINDING still ships its denominator — the summary prints beside the hits rather than instead of them   [2 static/instance error(s) (1 instance members across 1 partial class(es) in 2 file(s), 2 static bodies walked); 0 static bodies in 0 file(s) NOT SCANNED — outside partial-class scope]

    lint-static --selftest: PASS — 17 checks, 0 failed
      denominators: live 29 static bodies in 14 of 88 Game file(s) walked, 533 bodies in 74 file(s) not scanned; synthetic 8 fixture file(s), 0 written to disk, 0 project file(s) modified

The four cases the brief required map onto it as: (1) the first three ACCEPTING
checks plus the two DROP CLAUSE blocks; (2) the three REJECTING checks; (3)
`both counts ... and they SUM to the total mentions` plus the two non-by-design
reasons; (4) the two NOTHING MEASURED checks.

The **19x pin is synthetic** on purpose: `2 walked, never 6` cannot be moved by
the project improving, whereas a pin on "88 offered exceeds 14 walked" would go
red the day someone made every Game file partial. The live checks assert the
IDENTITY (walked + not-scanned = offered) instead, which is true in every world.

---

## 5. The denominator sweep — confirmed, with ONE tool the earlier sweep missed

Distinguishing shape, per the brief: **a printed total that counts things the
scan never reached.** Seven other tools read, and the finding loop compared
against the printed denominator in each.

| tool | printed | verdict |
|---|---|---|
| `lint-avenues` | `(185 files walked, owner INCLUDED)`, `0 unaccounted over 94 mention(s) examined in 185 file(s)` | **CLEAN — model.** `scanned` increments inside the walk; exit 2 when the sweep did not reach its subject; deferred debt named in the same sentence. |
| `lint-conditional-reach` | `1 conditional type(s) checked in 88 file(s); 0 in 103 unwalked Core/Editor file(s)` | **CLEAN — model.** Names its unwalked set explicitly. |
| `lint-filetype` | `191 file(s) scanned, 465 type(s) declared, 13 filename(s) that are not types` | **CLEAN.** All three loops open every file in `files`; the trap set is printed beside the scan count. |
| `lint-unreached` | `94 Game-layer files, 351 public methods, 6 that nothing else names` | **CLEAN.** `declared` is the post-filter examined set, and the `BY_WORKFLOW` exclusions are printed by name with their reasons. |
| `lint-namespace` | `191 file(s) scanned, 4 namespace segment(s) in scope` | **CLEAN at file level** — every file is opened. Note only: the check unit is the (file, segment) PAIR and the `declared` skip drops pairs unreported. Measured: **2 of 764 pairs, 0.26%.** Same disease, negligible dose; not worth a change on its own. |
| `lint-shadow` | `285 type(s), 88 Game file(s)` | **CLEAN on this axis** — every Game file is read; the `continue` skips only the inner clash loop. Two smaller nits below. |
| `lint-nested` | `255 top-level Core types checked` | **NOT CLEAN. This one is a real finding.** |

### `tools/lint-nested.py` — the printed denominator cannot see the walk

The sweep is `for f in game_files` over 88 Game files. The printed denominator
is `len(top)` — the set of **Core** types, which is the REFERENCE list, not the
examined set. Probed rather than reasoned about, by calling its own `scan()`
with an empty Game list:

    lint-nested with ZERO game files walked -> prints:
      lint-nested: 0 nested-type errors (255 top-level Core types checked)
    lint-nested normally             -> 255 types, 0 bad, 88 game files walked (NOT PRINTED)

Then the same thing through its real `main()`, with `GAME` pointed at a real
but EMPTY directory — so the dir guard does not fire and the tool believes it
has done its job:

    lint-nested main() with an existing but EMPTY Game dir:
    lint-nested: 0 nested-type errors (255 top-level Core types checked)
      exit = 0

**Byte-identical output and exit code for a full sweep and for a sweep of
nothing.** That is precisely rule 3b: a clean result indistinguishable from one
that examined nothing. The Game file count — the number that WOULD move — is
computed and thrown away.

Second, smaller, same file: `if not CORE.is_dir() or not GAME.is_dir(): print("Core or Game not found"); return 0`
— a never-ran path returning **exit 0**, which verify reads as a pass.
(`lint-static` had the identical line; it now exits 2.)

Not fixed — not my file, as instructed. The repair is two numbers on one line.

### `tools/lint-shadow.py` — two nits, neither the briefed bug

* The print re-globs: `{len(list(GAME.rglob('*.cs')))} Game file(s)`, a SECOND
  glob taken after the walk rather than `len()` of the walked list. Two moments
  under one line. Ordinarily harmless; today the tree is being edited by two
  live agents, which is the case where it is not.
* `if not GAME.is_dir(): print("no Game directory"); return 0` — never-ran
  returns 0, same shape as `lint-nested`'s.

---

## 6. What this confirms and what it overturns

**Confirms:** the director's mechanism reading, and the other builder's 560/29
across 14 of 88. Both correct.

**Confirms with a correction:** the *total* is not a fixed 560 — it is a number
that moves with the tree (560 then 562 four minutes apart), and it had moved
418 -> 560 across the 550 landed footers while the walked set stayed at 29.
The inflation was not static, it was tracking, which is worse.

**Overturns:** every green commit footer in this repo that read
`0 static/instance errors (N members, ~500 bodies)` as evidence that the Game
layer's static bodies were being swept. 550 of them. The true figure was 29.
No CS0120 conclusion is overturned — the tool's *finding* was never wrong, only
its claim about how much it had looked at.

**Also overturns, narrowly:** the earlier sweep's "six other lints clean on
this axis". Six are clean. `lint-nested` is not, and its symptom is the exact
one being fixed here.

---

## 6b. THE NUMBER NOW LOOKS LIKE A COLLAPSE, AND IT IS NOT — read this first

**While this agent was down, a second agent independently read the new
`29 bodies` against the old `562` and flagged it as a possible twentyfold
regression in coverage.** That reaction is correct behaviour and the answer is
that nothing collapsed: the walk has entered exactly 14 files and 29 bodies for
its whole life. Only the LABEL changed.

    before:  562 static bodies walked          <- 533 of them never opened
    after:    29 static bodies walked; 533 static bodies in 74 file(s) NOT SCANNED

The total is still printed. It is on the `arithmetic:` line, correctly named as
what was OFFERED rather than what was walked, and the two are shown adding up:
`29 walked + 533 not scanned = 562 offered`. Nothing was removed from the
output; one number was split into the two numbers it had always been.

This is written down here because the next reader will have the same reaction
to the same number — a large figure dropping to a small one is exactly what a
regression looks like — and should find the answer already written rather than
re-deriving it. It is also the reason the drop clause is on **line 1** beside
the walked count instead of on a continuation line: the two numbers have to
arrive together or the small one reads as a loss.

---

## 6c. CLAUDE.md §3b — left as found, NOT edited by this agent

**I made no edit to `CLAUDE.md`.** The correction was already applied to the
tree I was given, and it is in house style: the false exemplar sentence —
`` `lint-static` now prints "354 static bodies walked" `` — is **still quoted
verbatim** at §3b, with the dated annotation beneath it beginning *"AND THE
EXEMPLAR IN THAT SENTENCE IS ITSELF THE FAULT — 25 Aug"*. Nothing needs doing
there on my account. Stated plainly so it does not fall between us.

Two things in that annotation will decay, and both are for the director rather
than for me:

1. It closes with *"Six other lints were checked and are clean on this axis."*
   **My sweep says six of seven.** `lint-nested` is not clean — see §5, probed
   at `main()` level, byte-identical output and exit 0 for a full sweep and for
   a sweep of nothing. That sentence should say six of seven, or name the
   exception.
2. It quotes *"560 printed against 29 actually scanned"* and *"the 531
   unexamined bodies"*. Those were true when written; the reading is 562/29 and
   533 now, and it moves with every Game-layer commit. Not an error — a
   snapshot of a moving number. Worth the words "at the time of measurement" if
   anyone edits that paragraph for another reason.

---

## 7. Follow-ups that are NOT this agent's files

1. **`ledger/verify.py:947-949`** — the footer can only carry two digit groups,
   so the drop clause does not reach the commit message. `raw_avenues()` two
   functions above already solves this shape: it lifts the deferred count with
   a second `re.search` and appends `", N DEFERRED"`. One line of the same
   kind would let the footer read
   `0 static/instance errors (75 members, 29 of 562 bodies)`. Director's call.
2. **`ledger/verify.py`'s `static_instance()` never runs `--selftest`**, unlike
   `raw_avenues()` which runs `lint-avenues --selftest` first. The selftest now
   pins verify's own parse, so wiring it is the thing that makes the pin fire.
3. **`tools/lint-nested.py`** — finding above.
4. **`tools/lint-shadow.py`** — two nits above.

## 8. Verify — RED, and the red is not mine

`python3 ledger/verify.py` -> **exit 1.**

**`ledger/.verify-footer` DOES NOT EXIST on disk**, which is the correct and
intended state: a green run writes it, a red run deletes it, so there is
nothing to paste and that is the point. Checked with `ls`, not remembered:

    ls: cannot access 'ledger/.verify-footer': No such file or directory

The single red gate is **`DIRECTOR NOT SPAWNED`** — 444 changed lines under
`Assets/Scripts` against a 100-line threshold, 0 `studio-director` rows newer
than the reference commit. That is the coordinator's batch-review gate and the
440-odd lines are the two other agents live in `WorldBuilder.cs`,
`SimDirector.cs` and `Core/ValuePanel.cs`. **I touched nothing under
`ledger/`**; my whole diff is `tools/lint-static.py` plus this report.

The only other non-green token is pre-existing and environmental:
`pwsh steps NOT CHECKED (no PowerShell)`.

**My tool's own line inside that footer, read from the run:**

    0 static/instance errors (75 members, 29 bodies)

Before this change the same position read `(75 members, 562 bodies)`.

`tools/docs-check.py` exits **0**. It caught this report file for having no
`**STATUS —` banner in its first eight lines; the banner was added and it
passes — the report is a LOG, dated, and says NOT CURRENT.

### Key names added

Not a `key=value` channel, but the greppable tokens a reader or a future parse
will look for:

| token | what it is a statistic OF |
|---|---|
| `N static bodies walked` | whole-run total over the set `scan_file()` entered |
| `K static bodies in J file(s) NOT SCANNED` | whole-run total over the complement |
| `not scanned, by reason:` | the same K split three ways, non-by-design reasons naming their files, capped with `(+N more not shown)` |
| `arithmetic: A walked + B not scanned = C ... offered` | the checkable identity |
| `nothing measured` | never-ran, exit 2, cannot read as clean |

No value contains a space that a whitespace split would truncate meaningfully,
and every number on the line is a whole-run total taken from one set of reads
at one moment — no peaks, so nothing needs an at-worst partner.
