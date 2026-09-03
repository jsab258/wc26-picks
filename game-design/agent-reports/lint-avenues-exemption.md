# lint-avenues: the exemption removed, and two holes underneath it

> **STATUS: LOG, 2026-08-25. NOT CURRENT** once the queued
> `streetmap-nameof-scaled-vs-raw` ruling lands: the nine deferred sites and
> every count quoted for them describe the code at `b7d232ba` and are expected
> to change. The instrument itself is LIVE.

Agent: instrument-builder. Files owned and changed: `tools/lint-avenues.py`
only. Nothing committed. `ledger/Assets/Scripts/Core/StreetMap.cs` was READ
and not touched.

---

## The headline

The guard now sweeps its own subject, and it is **RED on the live codebase**,
reporting **9 unaccounted raw avenue reads in 3 methods** — `NameOf`,
`AddressOf` and `DistancePenalty`. That is the guard working. It printed
`0 raw avenue reads (183 files)` before.

**The exemption was not the only thing hiding the fault. It was one of three,
and removing it alone would still have printed zero.** The other two were found
by running the rejecting case, and each of them independently made `NameOf`
invisible:

| hole | what it did |
|---|---|
| `OWNER = "StreetMap.cs"` skipped wholesale | the subject was outside the denominator |
| pattern was `\bAvenues[XZ]\s*\[` | `NameOf` reads through an ALIAS and contains no such text — **0 matches** |
| every read counted alike | `.Length`, a null check and `ScaleAbout(...)` would all have been findings, making the guard a ratchet |

The middle one is the sharp one. `NameOf` never writes `AvenuesX[`:

```csharp
var cross = northSouth ? d.AvenuesZ : d.AvenuesX;
if (near < cross[0] - 14 || near > cross[cross.Length - 1] + 14) continue;
var line = northSouth ? d.AvenuesX : d.AvenuesZ;
    if (Math.Abs(line[i] - coord) < 0.001) return names[i];
```

The coordinate is read off `cross` and `line`. The old pattern scores **zero**
on that block. This is asserted in the selftest (`NOTE` line) so it cannot be
re-derived as "the exemption was the bug".

---

## The rule I chose

Every mention of the tables is classified into exactly one of five classes,
and only one of them is a fault.

| class | test | why it is not a fault |
|---|---|---|
| `declaration` | bare name (no `.` before it) followed by `=`, `,` or `;` | authoring the table is not reading it — `public double[] AvenuesX, AvenuesZ;`, `AvenuesX = new double[] { -40, ... }` |
| `transform` | the read sits inside the argument list of `ScaleAbout(` on that line | **this is the transform being applied.** It is what the owner file exists to do |
| `structural` | `.Length`, `== null`, `!= null` | touches no coordinate at all |
| `origin` | an indexed read compared only against the literal `0` | `ScaleAbout(v, 0, k) == v * k`, so **zero is the fixed point of the transform** and `d.AvenuesX[i] == 0` means the same thing in both frames. Only zero. A comparison against any other literal is classed `raw` |
| `raw` | anything else | an unscaled coordinate value escapes |

**Why this admits the transform.** `BoundsOf`, `CentreOf`, the junction grid,
the block rectangles and `OnOuterRing` are all `transform` — 16 reads, every
one of them inside a `ScaleAbout(` call. The owner keeps its raw access
because the class is defined by what happens to the value on the line, not by
which file it is in.

**Why it rejects `NameOf`.** `Math.Abs(line[i] - coord)` puts an unscaled
table entry next to a coordinate that arrived from outside. No `ScaleAbout`,
not `.Length`, not compared to zero. `raw`.

Aliases are followed — both `var name = <table>` and
`foreach (var v in <table>)` — scoped by brace depth, because that is the only
way to see `NameOf` at all.

---

## The part a pattern honestly cannot decide, so it is not pretended

Two shapes, side by side:

```
NameOf        if (near < cross[0] - 14 || near > cross[^1] + 14)
DistrictFor   if (x >= d.AvenuesX[0] - 20 && x <= d.AvenuesX[^1] + 20)
```

They are the **same shape** — a raw extent compared against a parameter. One
is a bug and the other is correct by design, and the difference is entirely in
the CALLER: `DistrictFor`'s only caller is `MigrateAddresses`, which passes
`place.X/Z` at line 923, and line 927 is where those get scaled. Read, not
assumed:

```csharp
var d = DistrictFor(place.X, place.Z);   // 923 — authored frame
...
place.X = ScaleAbout(place.X, cx, kx);   // 927 — becomes map frame here
```

**A lint claiming to tell these two apart by pattern would be inventing an
answer.** That is why the first author reached for a whole-file exemption:
there genuinely is no local discriminator. The mistake was not noticing that
the exemption's scope — a file — was ~200x wider than the thing it needed to
excuse.

So the accounting is per SITE, in `RAW_OK`, and it is checked **both ways**:

- a `raw` read in a method not on the list **fails** — a new fault cannot be
  absorbed, which is what an allow-list normally does silently;
- a list entry matching **no** site **fails as STALE** — a reason whose subject
  was renamed or fixed gets re-read instead of standing for ever. (A reason on
  the reach ledger decays exactly like a comment; three were wrong on 4 Aug.)

Two entries, each checked against code:

| method | reason |
|---|---|
| `MassOverlaps` | compares avenues against `BuiltMasses` — an authored unscaled table 80 lines up in the same file, holding one entry, the pub at `(-8, 8)`. Both sides authored frame. |
| `DistrictFor` | answers which district an AUTHORED coordinate is in; sole caller passes pre-scale values (923 vs 927). |

`NameOf`, `AddressOf` and `DistancePenalty` are **deliberately not on the
list.** They are the live fault.

---

## Selftest — ACCEPTING CASE FIRST, both outcomes watched

```
$ python3 tools/lint-avenues.py --selftest
lint-avenues selftest — ACCEPTING CASES FIRST
  ACCEPT 1/7  the transform read inside StreetMap.cs: 0 findings over 1 read(s), 1 classed transform
  ACCEPT 2/7  a null guard: 0 findings over 2 read(s), 2 classed structural
  ACCEPT 3/7  a length guard: 0 findings over 1 read(s), 1 classed structural
  ACCEPT 4/7  a comment quoting the fault: 0 findings over 0 read(s) — prose is not code
  ACCEPT 5/7  `AvenuesX[i] == 0`: 0 findings over 1 read(s), 1 classed origin (zero is the fixed point of ScaleAbout)
  ACCEPT 6/7  a ledgered authored-frame read (DistrictFor): 0 findings over 1 read(s), 1 classed raw and accounted for
  ACCEPT 7/7  the declarator and the table initialiser: 0 findings over 3 mention(s), 3 classed declaration — authoring the table is not reading it
  --- rejecting cases ---
  REJECT 1/4  the tour camera's raw read: 1 finding over 2 read(s), owner NOT exempt (no file is)
  REJECT 2/4  synthetic NameOf-shaped ALIAS comparison inside StreetMap.cs: 2 findings over 3 read(s) at lines 7,10
  REJECT 3/4  synthetic `foreach` value alias used on LATER lines inside its body: 2 findings over 2 read(s) at lines 8,9 (regression: this read 0 while the alias died at its own `{`)
  REJECT 4/4  a ledger entry matching no site is STALE, not silently kept: 2 reported (DistrictFor, MassOverlaps)
  NOTE        the pre-rewrite pattern `Avenues[XZ][` matches 0 line(s) of that fixture — it could not see the fault even with the exemption removed
lint-avenues: selftest ok (7 accepting, 4 rejecting)
EXIT=0
```

Accepting case 1 is first and is the one that matters: **if the transform read
inside the owner file did not pass, this would be a ratchet.** Accepting case 6
is the other ratchet guard — a ledgered authored-frame read must be admitted.

**Rejecting fixtures are synthetic.** `ZzSyntheticPlateProbe` and
`ZzSyntheticNearestProbe` exist nowhere in the project (checked: `grep -r Zz`
finds only this tool). Neither is pinned to `NameOf`, so fixing `NameOf` —
which is queued — cannot break the tool. Three fixtures in this project had to
be unpinned from real subjects for exactly that reason.

### A third outcome: the instrument itself failing

```
$ python3 tools/lint-avenues.py   # with SCAN pointed at an empty directory
lint-avenues: 0 file(s) swept, owner StreetMap.cs NOT FOUND under <path> — NOTHING MEASURED about the file the fault lives in; NOTHING MEASURED — no avenue table read found at all, which is not the same as clean
  raw reads accounted for by RAW_OK: 0 in 2 listed method(s) — DistrictFor, MassOverlaps
  EXIT 2 — the sweep did not reach its subject. This is not a pass; 0 file(s) were walked and 0 mention(s) found.
EXIT=2
```

Exit codes are distinct per outcome: **0 clean, 1 findings, 2 the sweep never
reached its subject.** The first version of this branch returned **0** — a
broken instrument reading as a clean sweep, which is the same fault as the
exemption one layer down. It also crashed with a `ValueError` traceback on the
path formatting; both fixed.

---

## What the tool says about the live codebase

```
$ python3 tools/lint-avenues.py
lint-avenues: 185 file(s) swept, owner StreetMap.cs INCLUDED in the sweep, no file exempt; 94 avenue table mention(s) classified — 18 declaration, 16 transform, 31 structural, 2 origin, 27 raw
  raw reads accounted for by RAW_OK: 18 in 2 listed method(s) — DistrictFor, MassOverlaps
  9 UNACCOUNTED raw avenue read(s):
    ledger/Assets/Scripts/Core/StreetMap.cs:1127: [NameOf] if (near < cross[0] - 14 || near > cross[cross.Length - 1] + 14) continue;
    ledger/Assets/Scripts/Core/StreetMap.cs:1127: [NameOf] if (near < cross[0] - 14 || near > cross[cross.Length - 1] + 14) continue;
    ledger/Assets/Scripts/Core/StreetMap.cs:1131: [NameOf] if (Math.Abs(line[i] - coord) < 0.001) return names[i];
    ledger/Assets/Scripts/Core/StreetMap.cs:1152: [AddressOf] double d = Math.Abs(ax - x) + DistancePenalty(dist, z, northSouth: true);
    ledger/Assets/Scripts/Core/StreetMap.cs:1153: [AddressOf] if (d < bestD) { bestD = d; best = NameOf(ax, true, z); }
    ledger/Assets/Scripts/Core/StreetMap.cs:1157: [AddressOf] double d = Math.Abs(az - z) + DistancePenalty(dist, x, northSouth: false);
    ledger/Assets/Scripts/Core/StreetMap.cs:1158: [AddressOf] if (d < bestD) { bestD = d; best = NameOf(az, false, x); }
    ledger/Assets/Scripts/Core/StreetMap.cs:1170: [DistancePenalty] double lo = cross[0], hi = cross[cross.Length - 1];
    ledger/Assets/Scripts/Core/StreetMap.cs:1170: [DistancePenalty] double lo = cross[0], hi = cross[cross.Length - 1];
  Each is an unscaled table entry meeting a scaled coordinate. Use StreetMap.BoundsOf / StreetMap.CentreOf, or — if the site genuinely works in the authored frame — add it to RAW_OK with a reason read off the CALLER.
EXIT=1
```

**Every hit is in `StreetMap.cs`. The other 184 files are clean, and that is
now a statement over a denominator that includes the subject.**

### The surprise worth reading: the fault is WIDER than the finding said

The finding named `NameOf`. The tool finds **three** methods, and the two
extras are not incidental:

- **`AddressOf` (1152–1158)** compares every raw `ax` / `az` against the query
  `x` / `z` to pick the NEAREST street. This is the FALLBACK — the path taken
  whenever `NameOf` returns null, which by the finding's own measurement is
  **96 of 97 junctions**. So the fallback that catches every failure of
  `NameOf` is wrong in the same direction, and it is the code actually
  producing nearly every address string in the game.
- **`DistancePenalty` (1170)** is the tie-break `AddressOf` uses to stop a
  Hook position being told it is on a Copper Row street. It compares raw
  extents against a scaled `along`. Districts far from the origin get a penalty
  computed in the wrong frame, so the disambiguation it exists for is not
  reliable at exactly the distances it was written for.

`AddressOf` feeds `AddressesSetBack` / `AddressDriftWorst` and, per the
`NameOf` doc comment, the plates at junctions and the witness lines read from
the same table so "the city can never tell the player one name and a character
another". All three sites are one frame bug. **Whoever takes the queued
`StreetMap.NameOf` ruling should be told the blast radius is three methods, not
one** — fixing `NameOf` alone leaves the fallback and the tie-break wrong, and
the lint will stay red and correctly so.

I did not touch `StreetMap.cs`.

---

## Grep for the same bug: other lints that exempt their own subject

The distinguishing token is not the string `OWNER` — it is **a denominator
larger than the set actually examined.** I read all eight `lint-*.py` and ran
each.

### `tools/lint-static.py` — the same fault, and worse. NOT FIXED (not my file).

`main()` prints, today:

```
lint-static: 0 static/instance errors (75 instance members across 2 partial class(es), 560 static bodies walked)
```

`560 static bodies walked` is `sum(static_bodies(f) for f in files)` over **all
88 Game files**. But `scan()` calls `collect()`, and `collect()` keeps only
files where `PARTIAL = r"\bpublic\s+partial\s+class\s+(\w+)"` matches **exactly
once**; a file declaring **zero** partial classes is dropped with no message at
all (`if len(names) != 1: if names: print(...); continue`). `scan()` then
iterates only `owners`.

Measured, not inferred:

```
Game .cs files                : 88
files collect() attributed    : 14
files never entered           : 74
static bodies PRINTED         : 560   <- the denominator lint-static prints
static bodies ACTUALLY scanned: 29
unexamined static bodies      : 531 (95% of the printed denominator)
```

**The tool prints a denominator 19x the set it examined.** This is the exact
shape of the avenues fault: a clean zero over a count of things that were not
looked at. It is arguably worse, because the avenues line at least named its
exemption; this one names nothing, and `static_bodies`' own docstring says the
number exists so that "a checker that scans NOTHING also reports zero" is
distinguishable — which is precisely what it fails to deliver. CLAUDE.md cites
this tool's "354 static bodies walked" as the exemplar fix for rule 3b.

Note it is not necessarily a coverage bug — restricting to partial classes may
be the intended scope for CS0120 attribution. **The instrument bug is the
printed number, not the scope.** The honest line is `29 static bodies walked in
14 of 88 Game files (74 skipped: no `public partial class`)`.

Recommend a separate brief for whoever owns `lint-static.py`. I did not change
it.

### Clean on this axis

| tool | line it prints | verdict |
|---|---|---|
| `lint-filetype` | `191 file(s) scanned, 465 type(s) declared, 13 filename(s) that are not types` | denominator matches the swept set |
| `lint-namespace` | `191 file(s) scanned, 4 namespace segment(s) in scope` | fine |
| `lint-nested` | `255 top-level Core types checked` | fine; nested-type exclusion is by brace depth and documented |
| `lint-shadow` | `285 type(s), 88 Game file(s)` | sweeps all Game files; Core is the SOURCE of names, not an exemption |
| `lint-conditional-reach` | names its unwalked set explicitly — `N conditional type(s) in M unwalked Core/Editor file(s)` | **already does the right thing**, and is the model |
| `lint-unreached` | `UNITY` set is documented as reflection the tool admits it cannot see | a stated blind spot, not a hidden one |

`gamecheck.py` and `slopcheck.py` already stale-check their allow-lists in both
directions ("THE ALLOW-LIST IS THE DANGEROUS PART AND IT IS BUILT TO FAIL BOTH
WAYS"), which is the pattern `RAW_OK` follows.

---

## Two bugs the rejecting case found in my own tool

Both would have shipped as silent zeros. Neither was found by reading.

1. **`for (...)` parsed as a method declaration.** `METHOD` did not require a
   modifier keyword, so `for (int i = 0; i < line.Length; i++)` matched, reset
   the alias scope mid-method, and `line[i]` — the actual `NameOf` fault —
   stopped being a read. Fixed by requiring at least one of
   `public|private|static|...`.

2. **Every `foreach` alias died at its own opening brace.** The alias was
   recorded at `depth + 1`, but the prune runs at the top of the next line,
   *before* that line's `{` has been counted — so `depth(2) < d0(3)` deleted it
   immediately. **`AddressOf` reported CLEAN because of this**, which is the
   whole failure mode of this task happening to me while I was fixing it. Fixed
   with an `armed` flag: an alias is only prunable once the depth it lives at
   has actually been reached. `REJECT 3/4` is a named regression test for it.

Both are recorded in comments beside the code they fixed.

---

## DEFERRAL (added after the coordinator's ruling, 25 Aug)

The lint was correctly red, and that red blocked **every commit in the
project**. The fix is Core, changes `AddressOf` strings feeding gossip, breaks
three CoreTests, and is queued for a director ruling — so it cannot land
tonight, and a guard that blocks all work until an unrulable fix arrives is the
ratchet this project has hit four times in one day.

The nine sites are now deferred through a ledger. **Not through `RAW_OK`.**

### Why a SECOND ledger and not the existing one

`RAW_OK` means *"read the caller, this is correct in the authored frame."*
The new `DEFERRED` means *"this is broken, we know, and it is queued."* Folding
them together would have printed **nine known faults as eighteen clean reads** —
an allow-list silently absorbing what nobody re-reads, which is the exact
disease this rewrite was commissioned to cure. So they are separate dicts,
counted separately, and printed on separate lines that cannot be summed by
accident:

```
  raw reads LEGITIMATE (RAW_OK, authored frame): 18 in 2 method(s) — DistrictFor, MassOverlaps
  raw reads DEFERRED KNOWN FAULTS (NOT clean, NOT fixed): 9 in 3 method(s) — AddressOfx4, DistancePenaltyx2, NameOfx3 — queue=streetmap-nameof-scaled-vs-raw deferred-since=2026-08-25
      AddressOf: the nearest-street FALLBACK, taken whenever NameOf returns null — 96 of 97 junctions — and wrong in the same direction
      DistancePenalty: the tie-break AddressOf uses to keep a Hook position off a Copper Row street; compares raw extents against a scaled `along`
      NameOf: compares a SCALED coordinate against the UNSCALED table via the `cross`/`line` aliases; only the founding cross at (0,0) matches
  (185 files walked, owner INCLUDED)
  0 UNACCOUNTED raw avenue reads over 94 mention(s) in 185 file(s), owner included — but 9 KNOWN FAULT(S) ARE DEFERRED, NOT FIXED. This is not a clean sweep; it is a clean sweep MINUS a named debt (streetmap-nameof-scaled-vs-raw).
```

Exit 0, so commits are unblocked. Values carry no spaces (`AddressOfx4`,
`queue=streetmap-nameof-scaled-vs-raw`).

### Three checks keep the debt from rotting, not one

The count is pinned per method — `NameOf 3`, `AddressOf 4`,
`DistancePenalty 2`, measured at `b7d232ba`, not chosen to fit.

| when | what happens |
|---|---|
| the ruling lands and the fault is **fixed** | the entry matches no site → **RED** until the entry is REMOVED. Confirmed: `REJECT 5/6` |
| the fault is **partly** fixed (4 sites → 3) | count moved → **RED**, entry must be re-read. Confirmed: `REJECT 6/6` |
| the fault **grows** (a 5th `AddressOf` site) | count moved → **RED**. Deferring a method never defers whatever is written into it next |
| a **new** method reads raw | unlisted → **RED** as before. Confirmed: `REJECT 1/6`, `2/6`, `3/6` still trip on synthetic methods |

**Confirmed with the nine listed**: the live run reports **0 stale**, because
the ledger's 3/4/2 matches the code's 3/4/2 exactly. The stale check the
coordinator asked about still holds.

### THE DEFERRAL IS INVISIBLE IN THE VERIFY FOOTER, AND I CANNOT FIX IT FROM MY FILE

This is the most important thing in this report. Measured, not assumed:

```
lint exit code seen by verify: 0  (0 => verify takes the GREEN path)
verify footer will read: 0 raw avenue reads (185 files)
```

`ledger/verify.py:912-914` builds that string itself:

```python
m = re.search(r"\((\d+) files walked", out)
return True, ("0 raw avenue reads (%s files)" % m.group(1) if m
              else "0 raw avenue reads")
```

The capture group is `(\d+)` — **digits only**. There is no way to carry the
word "deferred" through it from my side, and suppressing the token only makes
it worse (bare `0 raw avenue reads`, still zero, now with no denominator).

So **every commit message from tonight forward will carry `0 raw avenue reads
(185 files)` while nine known faults sit deferred.** That is precisely "a
deferral that reads like a pass", one layer up, in the channel a person
actually reads. **`verify.py`'s owner must carry the deferred count into the
footer** — e.g. `0 raw avenue reads, 9 DEFERRED (185 files)`. I did not edit
`verify.py`; it is not my file.

---

## Verify — final state after the deferral

```
$ python3 ledger/verify.py ; echo "VERIFY_EXIT=$?"
VERIFY_EXIT=1

$ cat ledger/.verify-footer
NO FOOTER FILE ON DISK
```

**There is no footer to paste, and that is the designed behaviour: a red run
deletes `ledger/.verify-footer`.** Reported from disk, as asked — the absence
IS the reading. The log's footer block ends `NOT GREEN — do not paste this into
a commit message as if it were.`

Ran four times across the night. In the final run the footer holds **exactly
one** red item, and it is not mine:

| footer item | mine? |
|---|---|
| `DIRECTOR NOT SPAWNED: 674 changed line(s) (234 tracked + 440 untracked in 1 new file(s)) vs 100 threshold under Assets/Scripts` | **no** — the process gate awaiting the resident's batch review. **I changed zero lines under `Assets/Scripts`**; those 674 are the other agent's |
| `0 raw avenue reads (185 files)` | mine, now GREEN — **and see handed-on item 1: it hides the nine deferred faults** |
| `docs 101/101 clean` | mine — my own report file failed the docs gate on the run before (no `STATUS` banner) and I fixed it. Rule 4: open the artifact you are shipping |
| `0 static/instance errors (75 members, 560 bodies)` | not mine, and **that 560 is handed-on item 2** |

**No bound was loosened to make red go away.** The nine faults are not
suppressed; they are named, dated, counted, tied to a queue item, and printed
on their own line as `DEFERRED KNOWN FAULTS (NOT clean, NOT fixed)`. The lint
returns RED the moment any of them is fixed, partly fixed, or joined by a
tenth.

**Earlier runs, for honesty about attribution.** Run 1 also showed
`reach FAILED — 2 unreached` and `CoreTests RED: FAILED: the rejecting case
walked the same twenty tokens — 28.`; both were gone by run 2. `git diff` shows
that assertion as a **deleted line** in `ledger/CoreTests/Program.cs`, which
another agent was editing live. `git status` confirms the only file I changed is
`tools/lint-avenues.py`.

`verify.py`'s own avenue selftest half passed in every run — no
`AVENUE LINT BROKEN` in any footer.

---

## One thing I fixed inside my own file for `verify.py`'s sake, and one I did not

`ledger/verify.py:912` reads the green denominator out of this tool by grep:

```python
m = re.search(r"\((\d+) files walked", out)
return True, ("0 raw avenue reads (%s files)" % m.group(1) if m
              else "0 raw avenue reads")
```

The rewrite changed that wording, so the **green** footer would have silently
fallen through to a bare `0 raw avenue reads` **with no denominator** — rule 3b
regressing one layer up, in the channel that rides into every commit message.
Caught by simulating verify's regex against the new output rather than assuming.
The tool now always prints `(185 files walked, owner INCLUDED)`, and both of
verify's paths were re-simulated:

```
verify footer would read: 0 raw avenue reads (185 files)
verify red-path first .cs: line: ...StreetMap.cs:1127: [NameOf] if (near < cross[0] - 14
```

**NOT fixed, because `verify.py` is not my file — a finding for its owner.**
The red path does this:

```python
first = next((l.strip() for l in out.splitlines() if ".cs:" in l), "see lint-avenues")
return False, "RAW AVENUE READ (unscaled coordinates): " + first[:90]
```

It reports **one** line, truncated to 90 characters, out of **nine** findings,
and says neither the count nor that it truncated. The footer currently reads
`... if (near < cross[0] - 14 || near > ` — cut mid-expression, with no `(+8
more not shown)` and no `9 findings`. That is the `| head -3` fault from
CLAUDE.md, in the verify footer: a cap that does not announce it bit reads as
the whole finding. Whoever owns `verify.py` should carry the count.


---

# HANDED ON — three items that must survive this agent

Priority order. **None of these are my files and I changed none of them.**

## 1. `ledger/verify.py` — the deferral is invisible in the footer (NEW, tonight)

Confirmed live, not simulated. Tonight's footer reads:

```
0 raw avenue reads (185 files)
```

while **nine known faults sit deferred**. `verify.py:912-914` composes that
string from a `(\d+)` capture — digits only — so nothing from my side can
carry the word "deferred" through it, and suppressing the token only produces a
bare `0 raw avenue reads` with no denominator at all.

Every commit message from tonight forward will therefore assert a clean avenue
sweep that is not clean. **This is "a deferral that reads like a pass" living in
the channel a person actually reads.** The fix is one line in `verify.py`:
read the deferred count out of the tool's output and print e.g.
`0 raw avenue reads, 9 DEFERRED (185 files)`.

## 2. `tools/lint-static.py` — a 19x inflated denominator, and CLAUDE.md cites it as the exemplar

The tool prints:

```
lint-static: 0 static/instance errors (75 instance members across 2 partial class(es), 560 static bodies walked)
```

Measured:

```
Game .cs files                : 88     files collect() attributed    : 14
static bodies PRINTED         : 560    static bodies ACTUALLY scanned: 29
files never entered           : 74     unexamined static bodies      : 531 (95%)
```

`collect()` keeps only files where `PARTIAL = r"\bpublic\s+partial\s+class\s+(\w+)"`
matches exactly once. A file with **zero** partial classes is dropped with **no
message at all** (`if len(names) != 1: if names: print(...); continue`), and
`scan()` then iterates only those 14. The `560` is `sum(static_bodies(f) for f
in files)` over all 88.

The restriction may well be the intended scope for CS0120 attribution. **The
instrument bug is the printed number, not the scope.** An honest line is
`29 static bodies walked in 14 of 88 Game files (74 skipped: no
"public partial class")`.

**This is a rules-file correction as well as a tool fix.** CLAUDE.md §3b cites
this very line — *"`lint-static` now prints '354 static bodies walked'"* — as
the exemplar of the rule-3b repair. The exemplar does not do what the rule
says. That is a director trigger (it touches CLAUDE.md), not a builder edit.

## 3. `ledger/verify.py` — the red path reports 1 finding of 9, truncated, silently

```python
first = next((l.strip() for l in out.splitlines() if ".cs:" in l), "see lint-avenues")
return False, "RAW AVENUE READ (unscaled coordinates): " + first[:90]
```

Tonight's red footer read `... if (near < cross[0] - 14 || near > ` — cut
mid-expression, one line of nine, with no count and no `(+8 more not shown)`.
That is the `| head -3` fault from CLAUDE.md living in the verify footer. Less
urgent than item 1 only because the red path is currently not taken.
