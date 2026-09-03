> **STATUS: LOG, 2026-08-26. NOT CURRENT** after the next change to
> `tools/prop-dimensions.py`, `tools/prop-reach.py`, `ledger/verify.py`, or
> after any of the readings below is re-measured. Tier-3 builder report; the
> tree was NOT committed by this agent.

# Six fixture pins, unpinned — and what the live readings say now

Follows `confabs-boundary-and-fixture-sweep.md` Part 2. The ruled standing rule:
**an accepting fixture may not assert values of an artifact the project intends
to keep improving.** Four were repaired earlier tonight (`Joe.fbx`,
`police.fbx` as a *rejecting* fixture, `lint-conditional-reach` overwriting
`Audio.cs`, `ref-bench` pinned to `district_hook.jpg`). The auditor found four
more; the director added a sixth mid-task. Five were mine to fix (the seventh,
`shape-check.py:383`, belongs to another agent and was not touched).

Every repair has the same shape, and it is not "widen the bound": **the
fixture's world becomes synthetic, and the live number stays a READING — printed
with its denominator, gated on nothing.**

---

## 1 — `tools/prop-dimensions.py`: `police.fbx`'s size was an accepting bound

**Was** (the whole guard for the array cap, which is this file's entire history
of being silently broken):

    total, size = geometry(CAR_KIT/"police.fbx")
    check(total > 1000, "the vertex cap is lifted, so a model reads whole")
    check(100 < size[2] < 400, "and it has a size")

1430 verts and 309.99997 deep, so **90 units of headroom on a bound whose
failure mode is a factor of 100** — a police re-export at a different FBX unit
scale (the commonest thing on a kit swap) turns `verify.py:489` red and blocks
every commit while saying the READER is broken. `police.fbx` had already been
removed from this file as a *rejecting* fixture; this was a second site using
the same asset for the opposite job, and the first repair grepped for the
pattern rather than the asset name.

**Is now: a real binary FBX that this file WRITES** — `write_synthetic_fbx`,
a 216-vertex lattice (48/12/96, a size no vehicle in the kit has, so nobody can
mistake it for a measurement of a shipped asset). Its expected numbers are
derived from `cap_fixture_verts()`, not typed. It **cannot move because nothing
in the project can edit it**: there is no file on disk to re-export.

Why bytes and not a `Node` tree: `synthetic_car`'s own docstring says it cannot
reach `_bp.parse_fbx`, the byte reader, which is where the cap lives — so that
layer's only fixture was a shipped asset. It now has a frozen one.

**A ladder of three rungs, one contributor toggled (the cap), same run, same
file:**

    ok   the fixture is denser than the DEFAULT cap, so the rungs can differ — 648 doubles against a 64-element default
    ok   CAP LADDER, rung 1 — ACCEPTING: cap lifted, the fixture reads whole — 216 verts (wanted 216), size 48.0/12.0/96.0 (wanted 48.0/12.0/96.0), 5645 bytes written
    ok   CAP LADDER, rung 2 — REJECTING: at the default cap the same bytes read as nothing — 0 verts, 0 part(s) — the `no vertex data` this file shipped
    ok   CAP LADDER — and the two rungs stand apart, so the cap is what made the difference — lifted/default 216/0 verts

The separation rung exists because both expectations are derived from the
fixture, so each alone is near-tautological — the same trap the synthetic car's
separation check was added for.

**The live reading survives, as a reading:**

    .. live kit reading, NOT a bound — 25 model(s) read whole, verts 1171..1908 (median 1470); ambulance=1746v/150/180/325 delivery-flat=1470v/150/135/325 delivery=1546v/150/165/325 firetruck=1746v/150/170/340 (+21 more of 25)

`verts 1171..1908 (median 1470)` is the series the old bound was standing in
for; `1430` (police) sits inside it. It is a **min..max plus median over 25
per-model totals**, taken from the SAME parse as the floors line — the live
reading used to re-parse all 25 models, which was a second walk and two moments
printed as one.

### Two faults found by break-testing this file, not by reading it

- **The squash loop died with `ValueError: max() arg is an empty sequence`** the
  moment a model yielded no parts, so with the historical bug reproduced **the
  cap ladder never ran at all** — a guard unreachable by the case it was written
  for, which is `lint-shadow`'s selftest falling through to the live sweep.
  It is now a legible FAIL per kind and the run continues.
- **The squash verdict now carries its skip clause**: `worst of 5 kinds is truck
  at 0.61 (2 not measurable here: bike.obj, bus.obj)`. Two kinds are examined by
  nothing and the pass line said so nowhere — `lint-static`'s 560-against-29.

Also migrated this file's private `(+N more not shown)` to `tools/capsay.py`,
so the project has one implementation of the truncation notice rather than two.
The count is now of the whole list: `(+17 more of 25)`.

---

## 2 — `ledger/verify.py:1211`: the cast size was a second copy of a C# constant

**Was** `if m.group(1) != "4": return False, "CONVO PROBE found %s cards,
expected 4"` — a copy of `ConvoProbe/Program.cs`'s
`want = new[] { "lena", "rocco", "ada", "sam" }`, in the language that BLOCKS
THE COMMIT rather than the one that states the cast.

**Is now** derived by `_convo_wanted()`, which reads that array out of the one
copy in C# and returns `(ids, why-not)`. The check is **per id, not per count**:

    found = re.findall(r"\bid=(\S+)", out)
    missing = [w for w in want if w not in found]

so a rename says *"no card for ada"* and a fifth character is simply green. A
parse that finds nothing is RED with the words `nothing-measured` — a bound that
could not be derived must not read as a probe of everybody.

**Live:** `40 probe calls staged (4 of 4 card(s) wanted, ids read from
ConvoProbe)` — the denominator is new; the old line was `40 probe calls staged`.

---

## 3 — `tools/prop-reach.py`: three assets pinned by name, and an inverse ratchet

**Was** — every one of these an *accepting* fixture asserting a value of an
artifact the project intends to change:

    check("finds models on disk", len(keys) > 100)
    check("kit is the first directory", "oga_vehicles_bus" in keys)
    check("an exact literal is reached", route.get("city_kit_roads_light_curved") == "exact")
    check("a stem in an array is reached", route.get("base_mesh_park_bench") in ("exact","stem"))
    check("not everything is unreached", <reached> > 20)
    check("the real corpus still has unreached models", <unreached> > 20)

The last is the **inverse ratchet**: at least 21 fetched models must stay
unplaced for ever — sitting ten lines under this file's own paragraph explaining
why the *rejecting* case had to be made synthetic, in those exact words. The
three named assets fail the moment a re-dressing pass stops placing a bench, and
`> 100` forbids ever pruning the corpus.

**Is now: a props tree and a Game file the selftest writes into a tempdir**,
covering every route `classify` can take, plus a deliberate key collision. It
cannot move because no asset, no prune and no re-dressing touches it. The one
live assertion kept is the one that **cannot be fooled by a fixture I wrote** —
every key the landed verdict says the sim instantiated must be reported reached
— and it is safe to be live because it compares this tool against the GAME, not
against an asset: improving the art can only add keys to it.

The old floors are replaced by a rung that asks what they were reaching for
without asking it of the real corpus: `SYNTHETIC LADDER — the routes are not all
one answer — distribution exact=2 stem=1 prefix=1 none=2`.

### What the live corpus reports now — including something the report had wrong

    prop-reach: 228 model file(s) on disk minting 213 key(s) (15 shadowed by 12 key collision(s), last path wins), 74 key(s) named by the Game layer, 139 with no name match (4452 literal(s) scanned)

**The headline used to say "213 model(s) on disk". That is a KEY count wearing a
FILE count's name.** 228 files are on disk; 12 keys are claimed by more than one
file; **15 files are unreachable in the game by any name at all**, because
`PropPrefab` mints one prefab per key and the later path wins. A report whose
whole subject is which files are invisible had 15 invisible files inside its own
denominator — rule 3b's second half, *ask what the denominator COUNTED*.

    routes (count of keys): exact=63 stem=11 prefix=0 none=139

    KEY COLLISIONS — 12 key(s) claimed by 2+ files, 15 file(s) unreachable by any name:
      oga_vehicles_ambulance: 3 files, wins=oga-vehicles/lowpoly-public-transport/Ambulance.obj, shadowed=oga-vehicles/free-low-poly-vehicles-pack/Ambulance.fbx, oga-vehicles/lowpoly-public-transport/Ambulance.fbx
      oga_vehicles_bicycle: 2 files, wins=oga-vehicles/lowpoly-public-transport/Bicycle.obj, shadowed=oga-vehicles/lowpoly-public-transport/Bicycle.fbx
      oga_vehicles_bus: 3 files, wins=oga-vehicles/lowpoly-public-transport/Bus.obj, shadowed=oga-vehicles/free-low-poly-vehicles-pack/Bus.fbx, oga-vehicles/lowpoly-public-transport/Bus.fbx
      oga_vehicles_schoolbus: 2 files, wins=oga-vehicles/lowpoly-public-transport/SchoolBus.obj, shadowed=oga-vehicles/lowpoly-public-transport/SchoolBus.fbx
      oga_vehicles_squareframebicycle: 2 files, wins=oga-vehicles/lowpoly-public-transport/SquareFrameBicycle.obj, shadowed=oga-vehicles/lowpoly-public-transport/SquareFrameBicycle.fbx
      (+7 more of 12 not shown)

**Two live consequences, both new information rather than tidying:**

- **`prop-dimensions` says `bus: first candidate oga_vehicles_bus ships as .obj
  — not measurable here`. Now we know why**: a `Bus.fbx` IS on disk and the
  `.obj` shadows it on the key. The same holds for the ambulance and four
  others. Whether the OBJ or the FBX should win is an art call, not this tool's.
- **`prefix=0`.** That branch of `classify` has never fired on this corpus and
  structurally almost cannot — the remainder after a `kit_` prefix IS the
  normalised stem, which the stem branch matched one line earlier. It is kept
  (a kit whose directory name prefixes another's would reach it) and it is now
  printed, so nobody reads four branches as four exercised paths. The synthetic
  fixture is the only thing that has ever taken it.

**Checked rather than assumed:** `prop-dimensions.kit_key_paths` (an `os.walk`)
and `prop-reach.models` (a sorted `rglob`) are two implementations of the
key-minting idea and could disagree about which file wins. Measured over all 12
colliding keys: **0 disagreements today.** They are still two implementations.

---

## 4 — `tools/shape-check.py:383` — NOT TOUCHED

Another agent's file, and flagged as a hunch rather than an accusation. Left
exactly as found.

---

## 5 (the sixth site, from the director mid-task) — `verify.py`'s own footer fixture, failing live

**Was**, and it was written TONIGHT in the batch whose subject was honest
denominators:

    ok, s = with_out(lint, "checked 191 files, 0 missing-using/collision error(s)")
    say(ok and "191 file(s) walked of 191 present" in s and "UNWALKED" not in s, ...)

The stub supplied WALKED; `lint` counted PRESENT off the live tree. Two agents
added six `.cs` files, the tree went 191 -> 192, and the accepting case failed:
`FOOTER STRINGS BROKEN: 1/35 fixtures failed`. The pinned artifact is **the file
count of the repository itself** — the one thing guaranteed to move.

**Is now** `with_synth_tree(walked, errors=0)`: eight `.cs` files plus one under
`obj/` in a tempdir, so the fixture owns BOTH halves of `N walked of M present`.
`lint(roots=None)` gained a parameter; live callers pass nothing. Three rungs,
and **two of them had no fixture at all before today** — `lint`'s drop clauses
were written, never run:

    ok   lint rung 1 — ACCEPTING: walked == present, so no drop clause and obj/ is excluded from both
    ok   lint rung 2 — a short walk says how many it dropped, and stays green: an unwalked file is not a lint error
    ok   lint rung 3 — a denominator LARGER than the tree is called out by name: the lint-static 560-against-29 shape

**And the break test found a seventh site three lines away, of the same class in
the mirror direction:** the REJECTING fixture stubbed `checked 185 files` against
a live PRESENT, so it asserted the repository holds *more* than 185 `.cs` files —
an inverse ratchet forbidding the tree from shrinking. Moved onto the same
synthetic tree.

`--selftest-strings` now reports **40 passed, 0 failed** (35 before: +3 lint
rungs replacing 1, +3 convo-probe rungs, -1 rejecting lint fixture moved not
added). That count rides into the footer, so it moved from `35 footer-string
fixtures` to `40`.

**Live now green:** `0 lint errors (186 file(s) walked of 192 present; 6 file(s)
of the 2 root(s) given went UNWALKED (Scripts/Editor))`. The 6 unwalked are
`Assets/Editor`, which `lint-usings.main` accepts and ignores — unchanged, still
reported.

---

## The selftests, both ways

**Accepting first, every time.** Rejecting runs are break tests against the
final code: each was produced by editing the tool, running, and restoring —
`diff` confirmed all three files byte-identical afterwards (`ALL THREE RESTORED
IDENTICAL`).

### `prop-dimensions --selftest` — ACCEPTING (exit 0)

    ok   the car kit is on disk to measure against — 25 models walked
    ok   every vehicle yields placed geometry — 0 of 25 unplaced: none
    ok   and none of them uses a rotation or a scale — 0 of 25 rotated or scaled: none
    .. floors, 25 measured: ambulance=0 delivery-flat=0 delivery=0 firetruck=0 garbage-truck=0 hatchback-sports=0 kart-oobi=0 kart-oodi=0 (+17 more of 25)
    ok   ACCEPTING CASE — every vehicle's wheels touch the road (y=0) — worst of 25 is van, 0.00 off the road
    ok   SYNTHETIC LADDER, rung 1 — placed, the fixture's tyres touch the road — 5 parts, floor 0.0, wanted 0.0
    ok   SYNTHETIC LADDER, rung 2 — REJECTING: pooled unplaced, it buries the car — pooled floor -30.0, wanted -30.0 — the number the table used to print
    ok   SYNTHETIC LADDER — and the two rungs stand apart, so the fixture still reproduces the bug — pooled/placed -30.0/0.0, separation 30.0 (needs > 1.0)
    ok   the kind table parses out of Core/Traffic.cs — 7 kinds read
    ok   and the kit mapping out of Game/TrafficHost.cs — 7 kinds mapped
    .. bike: first candidate oga_vehicles_bicycle ships as .obj — not measurable here
    .. bus: first candidate oga_vehicles_bus ships as .obj — not measurable here
    .. squash (1.00 keeps the kit's own proportions): car=0.73/0.70 police=0.72/0.70 taxi=0.75/0.67 truck=0.61/0.87 van=0.68/0.87
    ok   no kit model is squashed past half to fit its kind — worst of 5 kinds is truck at 0.61 (2 not measurable here: bike.obj, bus.obj)
    ok   the fixture is denser than the DEFAULT cap, so the rungs can differ — 648 doubles against a 64-element default
    ok   CAP LADDER, rung 1 — ACCEPTING: cap lifted, the fixture reads whole — 216 verts (wanted 216), size 48.0/12.0/96.0 (wanted 48.0/12.0/96.0), 5645 bytes written
    ok   CAP LADDER, rung 2 — REJECTING: at the default cap the same bytes read as nothing — 0 verts, 0 part(s) — the `no vertex data` this file shipped
    ok   CAP LADDER — and the two rungs stand apart, so the cap is what made the difference — lifted/default 216/0 verts
    .. live kit reading, NOT a bound — 25 model(s) read whole, verts 1171..1908 (median 1470); ambulance=1746v/150/180/325 delivery-flat=1470v/150/135/325 delivery=1546v/150/165/325 firetruck=1746v/150/170/340 (+21 more of 25)

    prop-dimensions selftest ok — 25 kit vehicles measured, 5 kinds squash-checked, 2 synthetic inputs (1 car tree + 1 FBX file, both built here, no asset)

### `prop-dimensions` — REJECTING (`VERT_CAP` back to the default: the bug this file shipped for weeks), exit 1

    FAIL every vehicle yields placed geometry — 24 of 25 unplaced: delivery-flat.fbx, delivery.fbx, firetruck.fbx, garbage-truck.fbx (+20 more of 24)
    FAIL ACCEPTING CASE — every vehicle's wheels touch the road (y=0) — worst of 1 is ambulance, 40.00 off the road
    FAIL kit model for car yields geometry to measure — car_kit_sedan parsed to 0 part(s) — the array cap, or a moved file
    FAIL CAP LADDER, rung 1 — ACCEPTING: cap lifted, the fixture reads whole — 0 verts (wanted 216), size 0.0/0.0/0.0 (wanted 48.0/12.0/96.0), 5645 bytes written
    ok   CAP LADDER, rung 2 — REJECTING: at the default cap the same bytes read as nothing — 0 verts, 0 part(s)
    FAIL CAP LADDER — and the two rungs stand apart, so the cap is what made the difference — lifted/default 0/0 verts
    prop-dimensions selftest 9 problem(s) — 1 kit vehicles measured, 0 kinds squash-checked, 2 synthetic inputs

(Rung 2 staying green is correct and is the point of a ladder: the rejecting
rung is insensitive to the fault, and only the SEPARATION reads it.)

### `prop-reach --selftest` — ACCEPTING (exit 0)

    ok   normalises dashes and case — City-Kit Roads -> city_kit_roads
    ok   SYNTHETIC — the walk mints a key per model file and ignores the rest — 7 file(s) -> 6 key(s), wanted 7 -> 6
    ok   SYNTHETIC — kit is the FIRST directory, however deep the file sits — nested/Beta Two.obj -> synthkit_beta_two; a loose file -> misc_*
    ok   SYNTHETIC — two files claiming one key collide, and the LAST path is the one models() keeps — 1 collision(s), models() kept stem 'alpha', sorted-last file is alpha.obj
    ok   SYNTHETIC — the literal reader finds every composition shape — 6 literal(s) read from one synthetic file
    ok   SYNTHETIC ROUTE — synthkit_alpha is exact — got exact
    ok   SYNTHETIC ROUTE — synthkit_gamma_three is stem — got stem
    ok   SYNTHETIC ROUTE — synthkit_beta_two is none — got none
    ok   SYNTHETIC ROUTE — synth_kit_delta is prefix — got prefix
    ok   SYNTHETIC ROUTE — synthkit_zeta is exact — got exact
    ok   SYNTHETIC ROUTE — misc_loose is none — got none
    ok   SYNTHETIC REJECTING — a key nothing names is unreached — nosuchkit_nosuchmodel_zzz -> none
    ok   SYNTHETIC LADDER — the routes are not all one answer — distribution exact=2 stem=1 prefix=1 none=2
    .. live corpus reading, NOT a bound: 228 file(s) -> 213 key(s) (15 shadowed by 12 collision(s)); routes exact=63 stem=11 prefix=0 none=139; 4452 Game literal(s)
    ok   LIVE — the walk turned files into keys (a zero here is the instrument, not the corpus) — 228 file(s) -> 213 key(s)
    ok   LIVE — there are Game literals to match against (zero would report the whole corpus unreached) — 4452 literal(s)
    ok   LIVE — no key the sim placed is called unreached (50 checked) — 0 false negative(s)
    prop-reach selftest: 16 passed, 0 failed (8 synthetic file(s) + 1 synthetic Game file, built here, no asset)

### `prop-reach` — REJECTING, three faults injected in turn (each exit 1)

    # the stem branch stops firing
    FAIL SYNTHETIC ROUTE — synthkit_gamma_three is stem — got prefix
    # interpolated strings discarded (the lint-shadow fault, ported here)
    FAIL SYNTHETIC — the literal reader finds every composition shape — 5 literal(s) read from one synthetic file
    FAIL SYNTHETIC ROUTE — synthkit_zeta is exact — got none
    # first-path-wins instead of last
    FAIL SYNTHETIC — two files claiming one key collide, and the LAST path is the one models() keeps — 1 collision(s), models() kept stem 'Alpha', sorted-last file is alpha.obj

**I had to fix my own probe to get that third one.** The first version of the
collision rung asserted `scoll[key][-1].name == "Alpha.obj"` — a list that is
sorted by construction, so it says "last wins" no matter what `models()` does,
and it **passed the break test that reversed the resolution outright**. The
fixture's two colliding files now differ in stem CASE, so the winner is
observable in the value the rest of the tool actually uses.

### `verify.py --selftest-strings` — ACCEPTING (40 passed, 0 failed) and REJECTING

    ok   lint rung 1 — ACCEPTING: walked == present, so no drop clause and obj/ is excluded from both
    ok   lint rung 2 — a short walk says how many it dropped, and stays green: an unwalked file is not a lint error
    ok   lint rung 3 — a denominator LARGER than the tree is called out by name: the lint-static 560-against-29 shape
    ok   convo probe: the cast size is READ from the C# want list, so a fifth character is green and carries its denominator
    ok   convo probe: a card that did not load is named, not counted — "the cast grew" and "Ada's card moved" are different findings
    ok   convo probe: a bound that could not be derived is RED and says so — a probe of nobody must not read as a probe of everybody
    footer-string selftest: 40 passed, 0 failed

Break test 1 — the UNWALKED clause silently renamed (the cosmetic edit these
fixtures exist for):

    FAIL lint rung 2 — ... — 0 lint errors (6 file(s) walked of 8 present; 2 file(s) skipped (1 root(s)) (SynthScripts))
    FAIL lint: a short walk is named as a drop, not folded into the total — 3 lint errors (6 file(s) walked of 8 present; ...)
    footer-string selftest: 38 passed, 2 failed

Break test 2 — the derived cast bound reverted to the old `!= "4"`. **This is
the pin itself, reproduced**: a five-character cast goes red.

    FAIL convo probe: the cast size is READ from the C# want list ... — CONVO PROBE found 5 of 5 card(s) named in ConvoProbe/Program.cs; no card for (count-only bound)
    footer-string selftest: 38 passed, 2 failed

---

## The asset-name grep — every hit

Rule 1's third corollary, aimed at asset names rather than at the pattern,
because that is precisely how site 1 was missed the first time.

| name | hits outside the repaired code |
|---|---|
| `police.fbx` | `ref-bench.py:1572`, `hang-report.py:399`, `lint-conditional-reach.py:44`, `prop-dimensions.py:339/341/440` — **all prose**, all describing the unpinning. `tts-benchmark:79` is the word "police" in a character bio. **No live read of the asset anywhere.** |
| `oga_vehicles_bus` | `prop-reach.py:102/322` (prose, quoting the removed fixture); `Game/TrafficHost.cs:555` — real Game code, correct. |
| `city_kit_roads_light_curved` | `prop-reach.py:29/324` (prose); `Game/WorldBuilder.cs:3798/3824/3825/3826` — real Game code. Note **3798 is a Game comment quoting this tool's output** (`reads "exact"`) — still true today (route exact), but it is the quoted-forward shape. |
| `base_mesh_park_bench` | `prop-reach.py:326` (prose); `Game/WorldBuilder.cs:2957` — real Game code. |
| `Joe.fbx` | `ref-bench.py:1572`, `clip-motion.py:440/528`, `hang-report.py:398`, `lint-conditional-reach.py:44` — all prose about the earlier repair. |
| `district_hook` / `district_downtown` | 20+ hits, all in `ref-bench.py` prose plus `verify.py:556` and `SimDirector.cs:10736`. Another agent's file; not touched. |
| `Bus.fbx` | `prop-reach.py:115`, `prop-dimensions.py:238` (prose), `TrafficHost.cs:525` (a comment noting both packs ship one — **now confirmed by the collision report**). |

**No accepting fixture anywhere still reads one of these assets.**

### And a mechanical sweep, with its denominator

Because a short list and an incomplete audit must not look alike:

- **86 Python files parsed**, **58 functions named `*selftest*`**, **350 string
  constants inside them that look like a path**. Of those, **9 name something
  that exists on disk — all in `tools/attribution-check.py`, and all false
  positives**: it builds `game-design/picked-clips/lena.p228.mp3` inside its own
  tempdir. **No other tool names a real asset inside a selftest.**
- Of the **17 verify check functions the footer-string fixtures exercise**,
  exactly **one reads the live filesystem** — `lint`, via `rglob`. That is site
  5, and it was the only possible one of its class among the 40 fixtures.
- **Limits, stated:** the scan is one level deep and does not follow helpers
  (`convo_probe` -> `_convo_wanted` reads a file and would not have shown up —
  it is injectable now), it cannot see NUMBER pins at all (site 5's `191` is not
  path-shaped), and 49 of 55 verify check functions remain un-opened, as the
  auditor's report already said. **This is a floor on the count, not a ceiling.**

---

## The parse trap — how I established the parse still holds

`verify.py` parses these tools' output, so a changed string silently drops a
number from a green footer. All three consumers were **run for real**, not
reasoned about:

    GREEN  prop_dimensions -> prop reader ok (14 checks)
    GREEN  prop_reach      -> prop reach ok, 228 model file(s) on disk minting 213 key(s) (15 shadowed by 12 key collision(s), last path wins), 74 key(s) named by the Game layer, 139 with no name match (4452 literal(s) scanned) [selftest 16 rung(s)]
    GREEN  footer_strings  -> 40 footer-string fixtures (accepting and rejecting)
    GREEN  lint            -> 0 lint errors (186 file(s) walked of 192 present; 6 file(s) of the 2 root(s) given went UNWALKED (Scripts/Editor))

- `prop_dimensions` counts lines beginning `ok`: 12 -> **14** (the two new cap
  rungs; the third and the fixture-density rung are there too — the count moves
  with the file, which is the point).
- `prop_reach` grabbed `rep.splitlines()[0]` and replaced the `prop-reach: `
  prefix; the headline still starts with it.
- **A dead denominator fixed in passing:** `prop_reach` computed
  `n = len([l for l in out.splitlines() if "passed" in l])` **and never used
  it**, so a selftest that ran ZERO rungs and one that ran seventeen reached the
  footer identically — `lint-nested` exiting 0 byte-identically for a full sweep
  and for a sweep of nothing, inside the file that polices it. The footer now
  carries `[selftest 16 rung(s)]`, or `nothing-measured` if the line is gone.
- `convo_probe`'s green string gained `(4 of 4 card(s) wanted, ids read from
  ConvoProbe)`.

---

## Conclusions this confirms or overturns

- **Confirms** the auditor's four, all four at the sites named, and the
  director's sixth. Nothing in their report was overstated.
- **Overturns** `prop-reach`'s own headline: "213 model(s) on disk" was a key
  count. **228 files, 15 unreachable by any name.** Any earlier reasoning about
  "how many models are unused" was over the wrong denominator — the unreached
  figure (139) is unaffected, but the corpus total was 15 short.
- **Overturns, mildly,** the reading that `oga_vehicles_bus` "ships as .obj":
  a `Bus.fbx` is on disk, shadowed on the key. Same for the ambulance.
- **New:** `classify`'s `prefix` branch has never fired on real data
  (`prefix=0`) and is shadowed by the `stem` branch by construction.
- **Unchanged and still true:** `prop-reach.py:227`'s NO LANDED VERDICT line
  remains the model and was not touched.

## Not done / for the director

- `tools/shape-check.py:383` — another agent's file, untouched.
- **12 key collisions are a real art decision** (which of `Bus.obj` /
  `Bus.fbx` should win), not an instrument fault. Reported, gated on nothing.
- `prop-dimensions.kit_key_paths` and `prop-reach.models` remain **two
  implementations of key minting**, agreeing on all 12 winners today. Merging
  them is a follow-up, not this batch.
- **The tree was not committed.**

---

## The footer, read from `ledger/.verify-footer` on disk (green run, exit 0)

The file is written only by a GREEN run and deleted by a red one, so these
fragments exist because verify passed. Read from the file, not from scrollback.
The five fragments this batch moved:

    40 footer-string fixtures (accepting and rejecting)
    0 lint errors (186 file(s) walked of 192 present; 6 file(s) of the 2 root(s) given went UNWALKED (Scripts/Editor))
    prop reader ok (14 checks)
    prop reach ok, 228 model file(s) on disk minting 213 key(s) (15 shadowed by 12 key collision(s), last path wins), 74 key(s) named by the Game layer, 139 with no name match (4452 literal(s) scanned) [selftest 16 rung(s)]
    40 probe calls staged (4 of 4 card(s) wanted, ids read from ConvoProbe)

Before this batch, the same five read: `35 footer-string fixtures` (with
`FOOTER STRINGS BROKEN: 1/35 fixtures failed` on the live tree),
`0 lint errors (185 file(s) walked of 191 present; ...)`, `prop reader ok
(12 checks)`, `prop reach ok, 213 model(s) on disk, 74 named by the Game layer,
139 with no name match (4439 literal(s) scanned)` — no selftest denominator —
and `40 probe calls staged`.

**Whole-run numbers on the footer line; per-rung numbers on the rung lines.**
The footer fragments above are per-RUN counts of checks and files; the
`prop-reach` corpus numbers are counts over one walk of the tree taken at one
instant; `verts 1171..1908 (median 1470)` is a per-model series and stays in the
selftest output where the models are named. Nothing here is a peak.

The full footer also carries other agents' concurrent work (`4163 CoreTests`,
`192 files`, `287 Core type(s)`), which is why the file counts differ from the
numbers quoted in the finding above — the tree grew while this was being fixed,
which is the entire argument for the repair.
