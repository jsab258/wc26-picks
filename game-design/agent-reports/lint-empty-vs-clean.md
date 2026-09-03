# lint-nested and lint-shadow: a clean result that was unfalsifiable

> **STATUS: LOG, 2026-08-26. NOT CURRENT** once `tools/lint-nested.py` or
> `tools/lint-shadow.py` changes again, or once the three items left for
> `ledger/verify.py`'s owner in section 7 are taken. Every count below
> describes the tree at `ce37232e`.

Agent: instrument-builder. Files touched: **`tools/lint-nested.py` and
`tools/lint-shadow.py` ONLY.** Not committed — the resident commits after the
director reviews. `ledger/verify.py`, `tools/capsay.py` and
`tools/shape-check.py` were READ and RUN, never edited.

---

## 1. The probe, before and after — this is the whole finding

Run at `main()` level with the tool's directory globals repointed at a real
but EMPTY directory. Read-only; nothing was written under `ledger/`.

**BEFORE**

    --- lint-nested, GAME = real but EMPTY dir ---
    lint-nested: 0 nested-type errors (255 top-level Core types checked)
    exit = 0
    --- lint-shadow, GAME = real but EMPTY dir ---
    lint-shadow: 0 shadowed Core types (285 type(s), 0 Game file(s))
    exit = 0

`lint-nested`'s line is **byte-identical to the full 88-file sweep, at the same
exit code.** `255` is the REFERENCE set — Core types to compare against — and a
reference set does not move when the walk collapses to nothing. The count that
would have moved was computed and discarded. `lint-shadow` at least printed
`0 Game file(s)`, but still led with `0 shadowed` and still exited 0, so
`verify` lifted a sweep of nothing into a GREEN footer.

**AFTER**

    --- lint-nested, GAME = real but EMPTY dir ---
    lint-nested: nothing measured — no `.cs` file under .../scratchpad/emptygame
    exit = 2
    --- lint-shadow, GAME = real but EMPTY dir ---
    lint-shadow: nothing measured — no `.cs` file under emptygame; the reference
    set holds 285 Core type(s) and was compared against nothing
    exit = 2

Three more never-ran shapes, all measured rather than reasoned:

| repointed | lint-nested | lint-shadow |
|---|---|---|
| CORE empty, GAME live | `nothing measured — 0 top-level Core type(s) in the reference set …, so 88 Game file(s) offered had nothing to be compared against`, exit 2 | `nothing measured — 0 Core type(s) in the reference set …, so 88 Game file(s) offered had nothing to be compared against; check the paths`, exit 2 |
| GAME directory missing | `nothing measured — Game not found (Core …, Game …)`, exit 2 | same shape, exit 2 |
| both empty | `nothing measured`, exit 2 | `nothing measured`, exit 2 |

Nothing in either tool can now print `0 … errors` from a walk that entered no
file, and none of those five texts matches verify's pass parse.

## 2. What each one prints now, and the identity it ships

**`lint-nested`, live, `ce37232e`:**

    lint-nested: 0 nested-type error(s) of 939 qualified pair(s) examined in 88
    of 88 Game file(s) walked, 64247 line(s) (255 top-level Core types checked)
      ladder, each rung a cumulative count over the whole walk: 939 qualified
      pair(s) in type position -> 70 whose OUTER name is a top-level Core type
      -> 0 whose inner name is one too, which is the finding
      reference set: 255 top-level Core type(s) at brace depth 1 from 97 of 97
      Core file(s) read under ledger/Assets/Scripts/Core; nested types are
      EXCLUDED by depth (`Perception.Attention` is legal and must not be flagged)
      arithmetic: 88 walked + 0 not walked = 88 .cs file(s) offered under
      ledger/Assets/Scripts/Game; no file exempt

**`lint-shadow`, live, `ce37232e`:**

    lint-shadow: 0 shadowed Core types (285 type(s), 88 Game file(s)) — that
    file count is the set WALKED, taken from the walk and not from a second
    glob at print time
      ladder, each rung a cumulative count over the whole walk: 418 method
      name(s) declared (distinct per file) -> 0 equal to a Core type name -> 0
      of those also used as a `Name.` qualifier in the same file, which is the
      finding
      reference set: 285 Core type(s) from 97 of 97 Core file(s) read under
      ledger/Assets/Scripts/Core
      arithmetic: 88 walked + 0 not walked = 88 .cs file(s) offered under
      ledger/Assets/Scripts/Game; no file exempt

The repair shape is `lint-static`'s, copied rather than invented, with
`lint-avenues`' "no file exempt" phrasing:

- **Counts come FROM the walk.** `Reading.walked` is the list the scanner
  appended to as it entered each file. There is no second `for f in files` loop
  and no second glob, so there is nothing left for the printed count to
  disagree with.
- **A checkable identity**, so a reader verifies the accounting on the line
  instead of trusting it: `88 walked + 0 not walked = 88 .cs file(s) offered`.
- **A drop clause that names its members**, capped through `capsay` so the cap
  announces itself. An unreadable file is a named drop, not a traceback and not
  a silent skip.
- **A ladder**, because a file count is not what these checks examine. If
  `QUALIFIED` or `MEMBER_DECL` stopped matching tomorrow, "88 files walked"
  would still read as healthy and the second rung would read 0. Each rung is
  named as a CUMULATIVE count over the whole walk — not a peak, not a
  last-wins — so the rungs are safe to divide by each other.
- **`nothing measured` + exit 2** for every never-ran shape.

## 3. Two live readings this instrument produced that nothing could see before

**`lint-shadow`'s middle rung is ZERO on the live tree.** 418 method names
declared, **0** equal to any of the 285 Core type names, therefore 0 reaching
the qualifier test. Cross-checked independently, with a looser regex than the
tool's own (287 Core type names, 121 globally-distinct Game method names,
intersection **0**) — so the reading is not an artefact of `MEMBER_DECL`. This
is rule 5b's corollary as a standing fact rather than a worry: **the second
stage of this check has no live exercise at all**, and the synthetic rejecting
fixture is the only thing that ever runs it. That is an argument for keeping
that fixture, not for widening the tool. The old line could not express this —
`0 shadowed` was consistent with "no collisions" and with "the collision test
never ran", and those need different responses.

**`lint-nested` examines 939 pairs and 70 of them have a Core type on the
outside.** So the check is genuinely meeting the code, at a ratio nothing had
ever printed. If a future edit takes 939 to single digits, the head line says so.

## 4. How I established verify still parses — three ways, one of them the real thing

`ledger/verify.py` greps both tools with a regex — `shadow()` at line 173
and `nested_types()` at line 945 as of `ce37232e`, and the LINE drifts while
the function does not — and a rewrite that drops the
token removes a number from every future GREEN footer with no red run to say
so. I am not permitted to edit `verify.py` and did not.

1. **The real consumer, on the real tool output.** Imported `verify.py` and
   called its own `shadow()` and `nested_types()`, which shell out to the tools
   on disk — no stub anywhere:

       shadow         ok=True   0 shadowed Core types (285 Core type(s) across 88 Game file(s))
       nested_types   ok=True   0 nested-type errors (255 Core types)

   **Both strings are byte-identical to what they produced before this change**,
   so the landed footer series stays comparable across the rewrite — no regime
   change in the commit feed.

2. **The full run, and the footer read from `ledger/.verify-footer` on disk**
   (not scrollback). `verify exit=0`, and the file carries:

       0 shadowed Core types (285 Core type(s) across 88 Game file(s))
       0 nested-type errors (255 Core types)

3. **The parse is pinned inside each tool's selftest, in both directions.**
   Each file keeps `VERIFY_PARSE` as a verbatim copy of verify's regex; the
   selftest asserts (a) that it matches the live summary and lifts the right
   numbers, and (b) that the literal is still present in `verify.py`'s source.
   If verify's owner changes the parse, the selftest names it instead of the
   footer quietly losing a census. `lint-shadow`'s copy is compared as its two
   string halves, because verify wraps that pattern across two literals.

**I also ran the consumer against the outputs it has never seen** — the new
exit-2 path and the finding path — because a guard's behaviour on my new output
is the half that decides whether the fix reaches the footer:

| stubbed tool output | verify says |
|---|---|
| shadow, nothing measured, exit 2 | `ok=False  lint-shadow did not report` |
| shadow, 1 finding, exit 1 | `ok=False  1 shadowed Core types (285 Core type(s) across 88 Game file(s))` |
| nested, nothing measured, exit 2 | `ok=False  CS0426 WAITING TO HAPPEN: see lint-nested` |
| nested, 1 finding, exit 1 | `ok=False  CS0426 WAITING TO HAPPEN: Audio.cs:52 Mixing.Bus …` |

All four are RED, which is the direction that matters: **a never-ran sweep can
no longer reach a green footer by either route.** Two of the sentences
misattribute the cause; that is verify's parse, named in section 7 rather than
edited.

One incidental improvement: `lint-shadow` now prints its summary head on the
FINDING path too, so verify reads the count off the same line as the census
instead of falling through to the count-only fallback. That also makes verify's
own selftest fixture `"lint-shadow: 2 shadowed Core types (285 type(s), 88 Game
file(s))"` describe a string the tool actually emits — before this change, it
never did.

## 5. The selftests, accepting case FIRST

Both are new-or-rebuilt and both lead with the live codebase, which is the best
accepting fixture available: CI compiles this tree, so **every hit on today's
code is a false positive by definition** and no fixture I wrote could fool it.
Rejecting fixtures are synthetic, in memory, never on disk, and use `Synth*`
names that exist nowhere in the project — so doing the work these tools prompt
can never break the tools. (Three rejecting fixtures in this project had to be
unpinned from real files for exactly that.)

**`python3 tools/lint-nested.py --selftest` — 16 checks, 0 failed, exit 0:**

    ACCEPTING — the live codebase, which compiles, so every hit is wrong
      ok   the live tree passes — 0 finding(s) on code that compiles   [0 finding(s) over 939 pair(s) examined]
      ok   and it reports a TRUE walked count, not the reference set   [88 of 88 Game file(s) walked, 64247 line(s), 939 pair(s) examined, 255 top-level Core type(s)]
      ok   the identity on the printed line holds, and the ladder narrows   [88+0=88 files; 939 pair(s) >= 70 outer-core >= 0 bad]
      ok   the head names the walked set and the identity is printed for a reader to check rather than trust   [0 nested-type error(s) of 939 qualified pair(s) examined in 88 of 88 Game file(s) walked, 64247 line(s) (255 top-level Core types checked)]

    THE CONSUMER — nested_types() in ledger/verify.py, which greps this line
      ok   verify's regex still matches the summary and lifts the reference count into the footer   [groups=('255',) types=255]
      ok   and the copy kept in this file is byte-identical to the one in verify.py (if this fails, verify changed its parse — read it, do not edit this line to match)   [found in verify.py]

    NOTHING MEASURED — the probe that found this bug, which must now look DIFFERENT
      ok   a full reference set against ZERO Game files prints the WORDS, never `0 ... errors`, and cannot match verify's pass parse   [lint-nested: nothing measured — no `.cs` file under /nowhere]
      ok   and the empty sweep's first line is no longer BYTE-IDENTICAL to the live one, which is exactly what it was before this change   [empty: nothing measured — no `.cs` file under /nowhere]
      ok   an empty REFERENCE set says so too — a comparison against nothing cannot pass   [lint-nested: nothing measured — 0 top-level Core type(s) in the reference set from /fixture, so 1 Game file(s) offered had nothing to be compared against]
      ok   and so does a sweep of nothing at all   [lint-nested: nothing measured — no `.cs` file under /nowhere]

    THE DROP CLAUSE — a file offered but not walked is NAMED
      ok   an unreadable file is counted under its own reason and NAMED, not folded into the total and not a traceback   [arithmetic: 1 walked + 1 not walked = 2 .cs file(s) offered under /fixture; 1 file(s) offered but NOT walked, unreadable: SynthGone.cs]
      ok   and a walk that dropped nothing says `no file exempt` rather than leaving the reader to assume it   [arithmetic: 1 walked + 0 not walked = 1 .cs file(s) offered under /fixture; no file exempt]

    REJECTING — the CS0426 this tool exists for (synthetic, unpinned)
      ok   correct code passes, and a genuinely NESTED type is not mistaken for a sibling   [0 finding(s) over 0 pair(s)]
      ok   a sibling qualified by another type IS caught   [SynthMixing.SynthBus]
      ok   a FINDING still ships its denominator — the summary prints beside the hits rather than instead of them   [1 nested-type error(s) of 1 qualified pair(s) examined in 1 of 1 Game file(s) walked, 2 line(s) (3 top-level Core types checked)]
      ok   and a comment warning about it is not flagged as it   [0 finding(s)]

    lint-nested --selftest: PASS — 16 checks, 0 failed
      denominators: live 88 of 88 Game file(s) walked, 939 pair(s) examined, 97 Core file(s) read; synthetic 6 fixture file(s), 0 written to disk, 0 project file(s) modified

**`python3 tools/lint-shadow.py --selftest` — 17 checks, 0 failed, exit 0:**

    ACCEPTING — the live codebase, which compiles, so every hit is wrong
      ok   the live tree passes — 0 finding(s) on code that compiles   [0 finding(s) over 418 declaration(s) examined]
      ok   and it reports a TRUE walked count and a TRUE examined count   [88 of 88 Game file(s) walked, 418 declaration(s), 0 clash(es), 285 Core type(s)]
      ok   the identity on the printed line holds, and the ladder narrows   [88+0=88 files; 418 decl(s) >= 0 clash(es) >= 0 bad]
      ok   the parenthetical file count IS the walked set — one line, one moment, no second glob   [0 shadowed Core types (285 type(s), 88 Game file(s)) — that file count is the set WALKED, taken from the walk and not from a second glob at print time]

    THE CONSUMER — shadow() in ledger/verify.py, which greps this line
      ok   verify's regex still matches and still yields ALL THREE groups, so the census keeps reaching the footer   [groups=('0', '285', '88')]
      ok   and the copy kept in this file is byte-identical to the one in verify.py (if this fails, verify changed its parse — read it, do not edit this line to match)   [both halves found in verify.py]

    NOTHING MEASURED — the probe that found this bug, which must now look DIFFERENT
      ok   a full reference set against ZERO Game files prints the WORDS, never `0 shadowed`, and cannot match verify's pass parse   [lint-shadow: nothing measured — no `.cs` file under /nowhere; the reference set holds 2 Core type(s) and was compared against nothing]
      ok   and the empty sweep's line is not the live one with a zero swapped in — before this change it was, at exit 0   [empty: nothing measured — no `.cs` file under /nowhere; the reference set holds 2 Core type(s) and was compared against nothing]
      ok   an empty REFERENCE set says so too — a comparison against nothing cannot pass   [lint-shadow: nothing measured — 0 Core type(s) in the reference set from /fixture, so 1 Game file(s) offered had nothing to be compared against; check the paths]

    THE DROP CLAUSE — a file offered but not walked is NAMED
      ok   an unreadable file is counted under its own reason and NAMED, not folded into the total and not a traceback   [arithmetic: 1 walked + 1 not walked = 2 .cs file(s) offered under /fixture; 1 file(s) offered but NOT walked, unreadable: SynthGone.cs]
      ok   and a walk that dropped nothing says `no file exempt` rather than leaving the reader to assume it   [arithmetic: 1 walked + 0 not walked = 1 .cs file(s) offered under /fixture; no file exempt]

    ACCEPTING — the legal shapes a rename tax would have broken
      ok   a member that collides but never dots the name is legal and passes — and the clash is still COUNTED, so the rung is visible   [0 finding(s), 1 clash(es)]
      ok   a file that only USES the type declares nothing of the name — the commonest case in the project   [0 finding(s)]
      ok   a PROPERTY named after a type still resolves (C#'s `Color Color` rule); the first version reported six of these on a tree that builds   [0 finding(s)]

    REJECTING — the CS0119 this tool exists for (synthetic, unpinned)
      ok   a Game METHOD named after a Core type the same file dots IS caught   [SynthHost.cs/SynthWatched]
      ok   a FINDING still ships its denominator AND still parses — verify reads the count off the same line rather than a hardcoded zero   [1 shadowed Core types (2 type(s), 1 Game file(s)) — that file count is the set WALKED, taken from the walk and not from a second glob at print time]
      ok   and one bad file among three good ones is found without the good three being flagged   [1 finding(s) of 4 file(s) walked, 2 clash(es)]

    lint-shadow --selftest: PASS — 17 checks, 0 failed
      denominators: live 88 of 88 Game file(s) walked, 418 declaration(s) examined, 97 Core file(s) read; synthetic 6 fixture file(s), 0 written to disk, 0 project file(s) modified

`lint-shadow` had **no selftest at all** before this: `--selftest` fell through
to the live sweep, printed a pass and exited 0. A guard that had never run
looked exactly like a guard that had.

## 6. The meta-fix, with its own denominator — and the sweep corrected itself once

CLAUDE.md §3b's "six other lints were checked and are clean on this axis" was
an unchecked claim. **There are EIGHT lints in `tools/`, not seven**, so the
sentence's own denominator was wrong before its content was.

I probed **8 of 8** at `main()` level, repointing every scan root at a real but
empty directory. **After this change, 0 of 8 are byte-identical for empty vs
full.** Six refuse an empty sweep with words and a non-zero exit
(`lint-avenues`, `lint-conditional-reach`, `lint-namespace`, `lint-nested`,
`lint-shadow`, `lint-static`). **Two still exit 0 on a sweep of nothing, and
neither is mine** — see section 7.

**The first version of that probe was itself wrong, and it is the reading I
would have published.** It reported `lint-filetype` and `lint-namespace` as
BYTE-IDENTICAL — which would have been two fresh findings. They were not:
those two hold their scan root as `SCAN = [path, path]`, a LIST, and my filter
only repointed values that were `pathlib.Path`. **Nothing had been repointed,
so both ran the live tree twice and of course agreed.** Rule 3, in the same
hour as writing a tool about it: I checked the ruler before the reading, and
the corrected probe gives the table above. The uncorrected probe is why this
paragraph exists rather than a confident wrong sentence.

Where the coverage claim now lives: each tool's own head line states the set it
walked (`88 of 88 Game file(s) walked`) with the identity beside it, so neither
sentence has to be trusted or quoted forward.

## 7. Left for another owner — named, not edited

**`ledger/verify.py` (its owner is another agent; I only read and ran it):**

1. **`nested_types()` and `static_instance()` both label exit 2 as a compile
   error.** Confirmed by stub, both directions, on the live `verify.py`:

       static_instance  exit2 -> ok=False  CS0120 WAITING TO HAPPEN: see lint-static
       nested_types     exit2 -> ok=False  CS0426 WAITING TO HAPPEN: see lint-nested

   Both tools now use exit 2 for NOTHING MEASURED, so the verdict is RED for
   the right reason with the wrong sentence — it says a compile error is
   waiting when in fact nothing was walked, and those need different responses.
   **One idea, two implementations, same missing line** — fixing one and not
   the other is the shape this project keeps paying for. Suggested, in both:
   `if code == 2: return False, "lint-<x> NOTHING MEASURED — " + first line`
   before the existing `if code != 0`.

2. **`nested_types()` still lifts only the reference count into the footer.**
   The footer reads `0 nested-type errors (255 Core types)`, and 255 is
   precisely the number that could not tell a sweep from a silence. The walked
   count is now printed and available: adding
   `r"in (\d+) of (\d+) Game file\(s\) walked"` as a second search (keeping the
   present one as the fallback) would put the walked set into every landed
   commit footer. **I deliberately did not change the tool's existing token or
   its position**, so this is additive and nothing breaks if it is never taken.

3. `shadow()` ignores the tool's exit code entirely and reaches
   `"lint-shadow did not report"` by accident on the nothing-measured path.
   Correct outcome, unintentional route.

**Elsewhere in `tools/` (not mine, measured not reasoned):**

4. **`tools/lint-unreached.py` prints NOTHING and exits 0 over an empty tree.**
   Live it prints six unreached methods; empty it prints zero bytes at exit 0.
   A silence exiting clean is rule 3b exactly.

5. **`tools/lint-filetype.py` exits 0 over an empty tree** with
   `0 filename-as-type error(s) (0 file(s) scanned, 0 type(s) declared, …)`. It
   does ship its denominator — a human can tell — but it leads with `0 errors`
   and exits 0, so a machine reading the exit code cannot. The cheapest fix is
   `lint-static`'s: words plus exit 2 when `scanned == 0`.

**Residual in my own two, named with a number rather than fixed:**

6. **The two tools strip source differently, and it is 12 pairs wide.**
   `lint-shadow` strips comments AND plain strings and treats `$"…"` as code;
   `lint-nested` strips only `//` comments, so it scans inside string literals.
   Measured: of `lint-nested`'s 939 examined pairs, **927 survive
   `lint-shadow`'s stripper and 12 sit inside string literals** — and none of
   the 12 produced a finding today. Narrowing it would be a scope change to a
   name-matcher with nothing currently to catch, which is how both lints of
   this family started flagging code that compiles; widening it likewise. Left
   as a measured, named gap for the director rather than a silent difference.

7. `_Fake`/`_Unreadable` fixture doubles now exist in three lints. `capsay` is
   the precedent for extracting a shared helper, but that would touch
   `lint-static`, which I do not own. Named, not done.

## 8. What this confirms and what it overturns

- **Overturns** the queue item's implicit reading that `lint-shadow`'s
  `88 Game file(s)` described the walk. It described a *second glob at print
  time*, and `lint-static` printed 560 and 562 four minutes apart for the same
  reason. It now comes from the walk and there is no second glob to disagree.
- **Overturns** `lint-static-denominator.md`'s "`lint-shadow` … CLEAN on this
  axis". Every Game file was indeed read — that half is right — but the printed
  count was not the read set and the empty sweep read as a pass at exit 0.
- **Confirms** that report's `lint-nested` finding exactly, including its
  reproduction, and confirms the corrected "six of seven" is still not the
  whole picture: it is **eight lints, and after this change six refuse an empty
  sweep and two do not**.
- **New, and nothing could see it before:** `lint-shadow`'s collision rung is
  0 on live code, so its qualifier stage is exercised only by the synthetic
  fixture; and `lint-nested` meets the code at 939 pairs, 70 with a Core outer.
