> **STATUS: LOG, 2026-08-25 17:0x UTC. NOT CURRENT** once the findings below
> are acted on. Measurement audit of an unrun instrument, read-only; no file
> in this report was edited by its author.

# Audit — the street-dressing measurement surface (`kitDressing=`)

Nineteen keys, none of them ever printed by a running sim. Audited by reading
`Core/KitDressing.cs`, its tests, all four call sites, and by COMPILING
`KitDressing.cs` standalone against `dotnet 8.0.130` and replaying the live
callers' actual filing shape. Every line quoted below is machine output from
that harness, not a hand-worked example.

## FILES THAT MOVED WHILE I READ THEM

- `ledger/Assets/Scripts/Game/StreetDressing.cs` — **changed twice under me.**
  At my first read (~16:48) `StreetDressing.Build()` had **no call site
  anywhere in the repo**, and `Emit()` set `light.enabled = true`. By ~16:58
  the wiring had landed at `WorldBuilder.cs:340` and `Emit()` had been rewritten
  to `light.enabled = false` + `WorldBuilder.RegisterStreetLight(light)`.
  Everything below is re-verified against md5 `afa314b3…` / 560 lines. **The
  "built is not running" finding for this file is RESOLVED and is recorded here
  only so nobody re-derives it from a stale grep.**
- `ledger/CoreTests/Program.cs` and `tools/lint-conditional-reach.py` are also
  dirty in the working tree. `Core/KitDressing.cs` did NOT move (md5
  `f7a5b328ba83e6972ab5caf2982e36cc` at first and last read).

---

# CONFIRMED — would change a decision

## C1. The emit wrapper makes a token with two `=` in it, and `kitPlaced` becomes unreadable to every naive parser

`ledger/Assets/Scripts/Game/SimDirector.cs:16058`

    $"kitDressing={WorldBuilder.KitTally.Line()} " +

`Line()` (`Core/KitDressing.cs:263-359`) returns **nineteen space-separated
`key=value` tokens**, not one value. Wrapping it in `kitDressing=` therefore
emits:

    kitDressing=kitPlaced=248/320/0 kitFamilies=8/8/11/0unknown kitBy=[...] ...

A parser that splits on whitespace and takes the first `=` — which is what
CLAUDE.md says "every reader in this repo" does, and what any grep anybody
types does — returns:

    kitDressing -> 'kitPlaced=248/320/0'      # a key whose value is a key=value pair
    kitPlaced   -> None                       # the run total is MISSING

`tools/verdict-read.py:476` and `tools/gates.py:194` both use
`(?<![\w])<key>=…`, and `=` is not a word character, so **those two recover
`kitPlaced=248/320/0` correctly**. Nothing else does. `kitDressing` itself is
left holding a nonsense value in every reader.

The sibling this was modelled on does not have the problem:
`Core/LooseEnds.cs:366` `Line()` returns **one value with no `=` in it**
(`Evenings/Empty/[…]/openN/MostofTiers`), which is why
`looseEnds={…}` at `SimDirector.cs:15706` is well-formed. `KitDressing.Line()`
broke that contract.

The test at `ledger/CoreTests/Program.cs:14034` explicitly checks for this
fault — `if (tok.IndexOf('=', eq + 1) >= 0) bad.Add("two \`=\` in one token")` —
and cannot see it, **because the test walks `Line()`'s output and never applies
the `kitDressing=` wrapper the Game layer adds.** The guard and the fault are
one line of C# apart and in different files.

*Cheapest command that settles it:*
`python3 -c "line='kitDressing='+open('frag').read(); print([t for t in line.split() if t.count('=')>1])"`
— or, on the first landed run, `python3 tools/verdict-read.py kitPlaced kitDressing`.

## C2. `kitPlaced=248/320/0` — a `missed=0` that reads as a perfect prop path while 72 sites produced nothing

`Core/KitDressing.cs:270-271` (`placed/offered/missed`), against
`StreetDressing.cs:199-206, 272-280, 405-407, 421-423`.

The class header at `KitDressing.cs:74-78` states the identity
`placed + missed <= offered` and says the placer files `Offered` then "exactly
one of `Placed`/`Missed`". `StreetDressing.cs:42-49` repeats it. **Four live
paths file `Offered` and then NEITHER**, exiting on a `Flagged(...); continue`:

| site | flag | outcome filed |
|---|---|---|
| `StreetDressing.cs:204` | `planter/in_road` | none |
| `StreetDressing.cs:206` | `planter/no_room` | none |
| `StreetDressing.cs:280` | `yard_fence/in_terrace` | none |
| `StreetDressing.cs:407` | `works_cone/off_road` | none |
| `StreetDressing.cs:423` | `works_barrier/off_road` | none |

Harness output for a healthy wired run with realistic refusal rates:

    kitPlaced=248/320/0

248 + 0 ≠ 320. Seventy-two sites are in a third bucket that the key does not
name and cannot show. A reader gets **`missed=0`, which reads as "the prop path
never failed once"** — and it is true — beside an offered count 29% larger than
placed, which reads as the prop path failing. Both readings are wrong; the
difference is geometry refusals in a different key. This is rule 3b's shape
inverted: the zero is real and its denominator is a different population.

The flat per-family keys are worse because they carry no third column at all:

    plantersPlaced=16/40      # 24 refusals, 0 misses
    worksProps=81/99          # 18 refusals, 0 misses
    yardFenceRuns=90/120      # 30 refusals, 0 misses

`plantersPlaced=16/40` is the first landed reading a person will quote. It
reads as "sixty percent of planters failed to load". Nothing failed to load.

**The accepting fixture does not have this shape.** `Program.cs:13803-13854`
files `placed + missed == offered` exactly for all eleven families, and asserts
it at `:13888` (`Check(208 + 19 == 227, …)`). The pinned 25-line expected string
at `:13858-13883` therefore certifies a shape **no live caller produces**. Rule
5b: the accepting case that was run is not the accepting case that will land.

## C3. `worksLampsLit` is arithmetically forced to equal `placed` — it can never print anything but `N/N`

`Core/KitDressing.cs:348` `t.Add("worksLampsLit=" + FlagOver(FlagLit, "works_lamp"));`
against `StreetDressing.cs:442-446` and `:474-499`.

    var go = Stand("works_lamp", …);           // :442
    if (go == null) continue;                  // :444
    if (Emit(go, at)) KitTally.Flagged("works_lamp", KitDressing.FlagLit);   // :446

`Emit`'s only false return is `if (rends.Length == 0) return false;`
(`StreetDressing.cs:478`). But `Stand` (`:530-535`) already returns `null` when
`go.GetComponentsInChildren<Renderer>().Length == 0`, and between the two checks
it destroys **colliders only**. So a non-null `go` guarantees ≥1 renderer,
`Emit` cannot return false, and `Flagged("works_lamp","lit")` fires for every
placed works lamp.

    worksLampsLit=18/18     # harness, healthy run — and it is 18/18 for ANY input

Numerator and denominator are one variable printed twice (the
`pulseMedian=0.000 uneaseMedian=1.000` shape: neither can move while the other
stands still). `FlagOver`'s denominator is `f.Placed`, and the numerator is
called once per `f.Placed`.

**And the flag is now named for a state the code deliberately does not set.**
The current `Emit` (`:495-498`) reads:

    light.enabled = false;
    WorldBuilder.RegisterStreetLight(light);

The lamp is **born dark**. `FlagLit = "lit"` (`KitDressing.cs:146`) now means
"a Light component was constructed and handed to the night sweep". A first
landed `worksLampsLit=18/18` will be read as "every works lamp is emitting" —
the exact claim `StreetDressing.cs:462-463` says this key exists to settle —
and it says nothing about emission at all. This is CLAUDE.md's "a number keeps
its name when the question it answers moves", caught before the first reading
rather than after.

## C4. `kitAmounts`'s planter row is a compile-time literal wearing a measurement's clothes

`StreetDressing.cs:213`

    if (go != null) WorldBuilder.KitTally.Measured("planter", 2.96f * 2.22f);

`2.96f * 2.22f` is constant-folded. Every planter files the same number, so
`AmountCell` (`KitDressing.cs:528-539`) prints:

    kitAmounts=[… planter:105.14/16/0bad/6.57..6.57..6.57 …]

The `min..median..max` triple exists, by its own comment at `KitDressing.cs:512-527`,
to answer *"is any of them wrong"*. For the planter row it is three copies of a
literal and **cannot answer anything**. A reader who has internalised that
comment will read `6.57..6.57..6.57` as sixteen independent measurements
agreeing perfectly — the strongest-looking evidence on the line, and it is a
constant.

Related, same key: **four different units share one channel with no unit
label.** `lamp` files metres of height (`WorldBuilder.cs:3782`),
`signal_head_secondary` files metres of gap (`TrafficHost.cs:1371`),
`yard_fence` files metres of run (`StreetDressing.cs:288`), `planter` files
**square metres** of footprint. Only `yardFenceMetres` names its unit, and it
is the one row whose sum is genuinely meaningful.

## C5. `Amount()` prints `nothing-measured` for the never-offered case, collapsing the two words the file exists to keep apart

`Core/KitDressing.cs:504-510`

    if (!_fam.TryGetValue(family, out f) || (f.Samples == 0 && f.BadSamples == 0))
        return NothingMeasured;

`KitDressing.cs:67-72` states the contract: *"`nothing-offered` means no call
ever named this family… `nothing-measured` means the family ran but no scalar
arrived."* The `TryGetValue` failure branch is the never-offered case and it
returns the wrong word. Harness:

    never offered at all          -> yardFenceMetres=nothing-measured
    offered, placed, no scalar    -> yardFenceMetres=nothing-measured

Identical strings for the two facts the key was built to separate. Today this
fires on every run where `yard_fence` is unreached; from the first landed run it
will fire whenever the yard probe (`YardOf`, `:321`) returns false for every
block. `kitAmounts` (`:299`) has the same collapse one level up: `[nothing-measured]`
means both "no family carried a scalar" and "no family exists".

## C6. `nothing-offered` is invisible to `gates.py --constant`, so nine permanently-dead keys will never be reported as dead

`tools/gates.py:346-347`

    DID_NOT_HAPPEN = {"0", "0.0", "0.00", "0.000", "0.0000",
                      "False", "None", "none", "-1"}

`nothing-offered` and `nothing-measured` are not in it. Verified:
`'nothing-offered' in DID_NOT_HAPPEN → False`.

On the wiring as it stands **today**, the harness says nine of the nineteen keys
print a sentinel every run:

    signPosts=nothing-offered  signPlates=nothing-offered
    namePlatesPainted=nothing-offered  worksClusters=nothing-offered
    worksProps=nothing-offered  worksLampsLit=nothing-offered
    yardFenceRuns=nothing-offered  yardFenceMetres=nothing-measured
    plantersPlaced=nothing-offered

Six of those nine will start moving now that `StreetDressing.Build()` is wired
(`WorldBuilder.cs:340`). **Three will not, ever:** see C7.

Worse for the sweep: `tools/gates.py:341`
`KEY_VALUE = r"(?<![\w])([A-Za-z][\w]*)=([^\s\[\(]+)"` **excludes `[`** from the
value class, so a value that STARTS with a bracket matches nothing. `kitBy`,
`kitByVariant`, `kitAmounts`, `kitFlagsBy`, `kitUnknownBy` and `lampsByKind` —
six of the nineteen, and the six that carry all the per-family detail — are
invisible to `--constant`'s key harvest entirely. That is a property of
`gates.py`, not of `KitDressing`, but it is the reason a dead row in `kitBy`
will never be surfaced by the tool this project relies on for exactly that.

## C7. Three catalogue families have no caller anywhere and never will until signage is built — rule 6, in the direction the brief predicted

`Core/KitDressing.cs:107-109` declares `sign_post`, `sign_plate_name`,
`sign_plate_warning`. Verified: the only hits for those three strings in the
entire repo are inside `KitDressing.cs` itself (lines 107-109, 331, 332, 336).
No Game-layer file names any of them.

So `signPosts`, `signPlates` and `namePlatesPainted` are three of the nineteen
keys that **cannot ever be anything but `nothing-offered`**, and by C6 no tool
will say so. `StreetDressing.cs:18-24` discloses this in prose and calls it
"the honest reading" — which it is, and the disclosure is a comment with no test
attached (CLAUDE.md rule 1, first corollary). The next reader of the verdict has
no comment in front of them.

`namePlatesPainted` additionally has a **name/statistic mismatch** that will bite
the day it is wired: `KitDressing.cs:336` computes
`FlagOver(FlagPainted, "sign_plate_name", "sign_plate_warning")` — the numerator
and denominator both span **both** plate families, while the key name claims name
plates only. If warning plates are never painted they dilute the ratio silently.

## C8. `PlacedOver` over several families reads `any=true` off the first family present, so a partially-wired group prints as fully healthy

`Core/KitDressing.cs:470-480`. `worksProps` (`:343`) sums three families;
`signPlates` (`:332`) sums two. Harness, with only `works_cone` wired:

    worksProps=40/40  worksLampsLit=nothing-offered

`worksProps=40/40` is a perfect score for a roadworks pass that placed **no
barriers and no lamps**. Nothing in that key says two of its three families were
never named. The evidence is in `kitBy`, which by C6 no sweep reads and which
a reader quoting a flat key will not open.

## C9. `kitFamilies`'s three numbers do not share a denominator

`Core/KitDressing.cs:278-279`

    kitFamilies=<placed>/<_fam.Count>/<Catalogue.Length>/<unknown>unknown

The first two count **all** families including names the catalogue does not
know; the third is catalogue-only. The test's own capped case at
`Program.cs:14150` pins the reading:

    kitFamilies=0/11/11/11unknown

Eleven junk names, none of them catalogued. `x/11/11` reads at a glance as
"eleven of eleven expected families were mentioned" — a full house — and is the
opposite. The `11unknown` suffix is the only thing that says so, and it is the
last field of a four-field value.

## C10. The `+Nmore` cap on `kitFlagsBy` bites at nine distinct flag rows, and the ninth row is the flag channel's own evidence

`Core/KitDressing.cs:154` `TailCap = 8`, applied to `FlagRows()` at `:304`.

`KitDressing.cs:149-153` justifies 8 with *"every list this bounds is empty in a
healthy run"*. **That is false for two of the three lists it bounds.**
`FlagRows()` (`:436`) and `AmountRows()` (`:427`) are non-empty in a healthy run
**by design** — the flag channel is the only denominator the class offers for a
flag zero (`:57-65`).

Rows are ordinal by `<family>/<flag>`. The live callers can produce ten distinct
rows: `lamp/district_unlisted` (`WorldBuilder.cs:3528`), `lamp/double_no_axis`
(`:3694`), `lamp/paint_refused` (`:3748`), `planter/in_road`, `planter/no_room`,
`signal_head_secondary/paint_refused` (`TrafficHost.cs:1330`),
`works_barrier/off_road`, `works_cone/off_road`, `works_lamp/lit`,
`yard_fence/in_terrace`. Ordinal order puts `works_lamp/lit` **ninth** and
`yard_fence/in_terrace` **tenth**. Harness with nine distinct rows:

    kitFlagsBy=[lamp/district_unlisted:1,lamp/paint_refused:1,planter/in_road:1,
    planter/no_room:1,signal_head_secondary/paint_refused:1,works_barrier/off_road:1,
    works_cone/off_road:1,works_lamp/lit:1,+1more]/n9

At eight rows nothing is cut (`shown = rows.Count < TailCap ? rows.Count : TailCap`
at `:666` is correct at the boundary). At nine, `yard_fence/in_terrace` goes. At
ten, `works_lamp/lit` goes too — **the row the class header names as the thing
you must read before believing `worksLampsLit`.** The cap does announce itself,
so this is a legibility fault rather than a silent one; it is listed here because
it lands on the one row the design depends on.

Second problem on the same key: `/n<total>` at `:304` is
`Total(f => FlagTotal(f))` — **the sum of all rows, including the ones the cap
just hid.** When the cap bites, the printed rows do not add to `n`, and a reader
dividing one by the other is dividing a shown subset by a full total.

Third: `n` mixes two incompatible meanings. `lit` and `painted` are **properties
of a placed object**; `in_road`, `no_room`, `off_road`, `in_terrace`,
`paint_refused`, `district_unlisted` are **site refusals and fault counters**.
`kitFlagsBy=…/n92` in the harness is 92 flag calls of which 72 are refusals. The
class header (`:57-65`) says "a non-zero `n` says the channel is alive and the
zero is a finding" — but `n` is a run total, so a live planter-refusal channel
makes `n` non-zero and certifies `worksLampsLit=0/12` as a finding even if the
works-lamp flag call site was never written. **The denominator that resolves a
flag zero has to be per-family; the one printed is per-run.**

## C11. The test's token sweep excludes the three lines most likely to break

`ledger/CoreTests/Program.cs:14022-14023`

    var lines = new[] { line, quiet, missLine, oneRun.Line(),
                        manyRuns.Line(), nan.Line(), dirtyLine };

The test builds **ten** `KitDressing` instances. Three are left out of the sweep,
and they are the three that produce the least ordinary strings: `typo`
(`:14126`), `many` (`:14142` — **the only line in the whole test containing a
`+Nmore` cap**) and `blank` (`:14158`). The assertion at `:14051`,
`Check(walked >= 7 * 19, "the space check walked every token of all seven lines")`,
is literally true and is not the claim a reader takes from it.

The brief asked me to verify the sweep's claim against the code rather than its
description. The sweep itself is sound where it reaches: the loop body executes
for every token (`:14026-14049`), an empty token from a double space is caught at
`:14032`, a value containing a space produces a second token with no `=` and is
caught at `:14033`, and `[`/`]` and `(`/`)` balance is counted at `:14039-14048`.
`Safe()` (`:726-739`) is a genuine allow-list — `[a-z0-9_\-.#]`, everything else
folded to `_` — and it is applied to every family, variant and flag name. **I
found no path by which a space can reach a value.** The gap is coverage, not
logic.

---

# NOT FINDINGS — checked and clean, recorded so they are not re-audited

- **Whole-run placement (brief Q2): CORRECT.** `Line()` has exactly one call
  site (`SimDirector.cs:16058`), inside the single `Debug.Log($"SimDirector:
  done. …")` statement that opens at `SimDirector.cs:14603` — no intervening
  `Debug.Log(` between those lines. Every counter is a monotone `++`/`+=` read
  once at that instant. Nothing is on a shot line. The `namesManagedEver`
  freeze-at-last-shot fault cannot occur here.
- **Divisibility (brief Q5): STRUCTURALLY ABSENT.** `KitDressing` assigns **no
  field by max or min** — grep for `Math.Max|Math.Min|Mathf.Max|Mathf.Min|Peak|Worst`
  returns only comments. `AmountCell`'s `min..median..max` are three statistics
  of one sample list computed in one pass at one instant (`:533-538`), printed
  beside their own `n`. The "two maxima cannot be divided" fault has no site here.
  The divisibility problems that DO exist are population mismatches (C2, C3, C8),
  not instant mismatches.
- **Exactly one live instance:** `new Ledger.Core.KitDressing()` appears once
  outside tests, at `WorldBuilder.cs:3491`. The second instance the brief
  mentions is gone. `WorldBuilder.BuildBlock()` (which despite its name builds the
  whole world) is called once, from `GameController.cs:660`, so nothing
  double-counts.
- **Variant strings match the catalogue.** `WorldBuilder.LampModel:3592-3612`
  emits exactly `curved|curved_double|curved_cross|square|square_double|square_cross`
  = `LampVariants` (`KitDressing.cs:121-125`). `TrafficHost.cs:1312/1319/1372`
  emits `"vertical"` = `HeadVariants`. `StreetDressing.PickFence:295-303` emits
  `1x1..1x4` = `FenceVariants`. No live variant falls into the unrecognised tail.
- **`Measured` refuses non-finite input** (`:236`) and counts it as `bad`. The
  sum cannot go `NaN`.
- **`signal_head_secondary` and `works_cluster` are the two families whose
  `placed + missed == offered` actually holds** under the live callers
  (`TrafficHost.cs:1289/1312/1319/1372`; `StreetDressing.cs:394/449`).

---

# SUSPECTED — depends on something I could not see from here

- **S1. `lamp`'s `AmountCell` spread may be a constant too.**
  `WorldBuilder.cs:3782` files `b.max.y - basePos.y` after scaling to a family
  target of 4.99 or 4.44 (`:3595`). If the scale step at `:3737` always succeeds,
  every curved lamp files 4.99 and every square 4.44, and
  `kitAmounts=[lamp:…/4.44..4.99..4.99]` is a two-valued distribution dressed as
  a measurement. The comment at `:3776-3781` says the point is to catch the case
  where `b.size.y > 0.5f` is false and the scale silently does nothing — which is
  a real question, but it is a **count** question ("did any lamp skip the
  scale"), and a min/median/max over 44 near-identical values answers it only if
  the skip happens. Cannot settle without a run. **First landed reading to check.**
- **S2. `signal_head_secondary`'s gap can be negative.** `TrafficHost.cs:1371`
  files `b.min.y - pos.y`. A head seated below the pavement gives a negative
  scalar, which `AmountCell` sums (`:530`). A run with some heads high and some
  buried can sum to near zero and print a plausible total. Format is safe
  (`"-1.20"`, no space); the arithmetic is not. Cannot settle without a run.
- **S3. `StreetDressing.cs` is still being edited.** Both of the changes I caught
  (the `Build()` wiring, and `Emit`'s light state) landed inside ten minutes.
  C2, C3 and C4 are re-verified against md5 `afa314b3…`; if that file has moved
  again, re-run the greps in the "cheapest command" lines before quoting any of
  them.

---

# WHAT THE FIRST LANDED READING WILL LOOK LIKE (brief Q9)

This is the harness's prediction for a healthy first run **with `StreetDressing`
wired**, plus what a reader would wrongly conclude from it. Reproduce with:
compile `Core/KitDressing.cs` standalone and replay the call sites.

| key | healthy first value | the wrong conclusion available from it |
|---|---|---|
| `kitPlaced` | `248/320/0` | "zero misses, the prop path is perfect" AND "72 sites failed" — both wrong; see C2. Also **not greppable** by naive parsers; see C1 |
| `kitFamilies` | `8/8/11/0unknown` | "eight of eleven families mentioned" — true today, but `x/N/11` mixes denominators; see C9 |
| `kitBy` | 8 rows + 3 `nothing-offered` | fine, and invisible to `gates.py --constant`; see C6 |
| `kitByVariant` | lamp all-but-`curved` at `0/0` | "five lamp forms never load" — no: `0/0` is never asked for, `0/N` is asked-and-failed |
| `kitAmounts` | includes `planter:…/6.57..6.57..6.57` | "sixteen planters measured, all identical" — it is one literal; see C4 |
| `kitFlagsBy` | 8-10 rows `/n92` | `n` mixes properties with refusals, and at ≥9 rows the cap eats `works_lamp/lit`; see C10 |
| `kitUnknownBy` | `[none]/0of8` | correct, and the best-formed key on the line |
| `lampVariants` | `1/6` if all lamps are Single | "the district table never branched" — true, but it is `MakeLamp`'s `form` argument, not the table, that decides; check the callers of `MakeLamp` before concluding |
| `lampsByKind` | `[…]/n44of44` | fine; one variable also printed as `lampVariants` and `kitByVariant`, so quoting two of the three as corroboration is one number three times |
| `signPosts` / `signPlates` / `namePlatesPainted` | `nothing-offered` **for ever** | "the sign placer is broken" — nothing was ever wired; see C7 |
| `worksClusters` | `9/9` | fine — the one family whose identity holds |
| `worksProps` | `81/99` | "18 props failed to load" — they were refused off-road; and if two of the three families are unwired it still reads `N/N`; see C2, C8 |
| `worksLampsLit` | `18/18`, always | "every works lamp is emitting" — it cannot print anything else, and the lamps are born dark; see C3 |
| `secondaryHeads` | `6/8` | fine — genuine placed/offered with real misses |
| `yardFenceRuns` | `90/120` | "30 fences failed to load" — refused for standing inside a terrace |
| `yardFenceMetres` | `722.10/90/0bad/3.52..9.44..12.40` | the best-formed value on the line; but `nothing-measured` cannot distinguish never-offered from no-scalar; see C5 |
| `plantersPlaced` | `16/40` | "sixty percent of planters failed" — nothing failed; see C2 |

**The single highest-risk first quote is `plantersPlaced=16/40` or
`worksProps=81/99` being read as a broken prop path, and the second is
`worksLampsLit=18/18` being read as the night-lighting question answered.**

---

# FIXES — 2026-08-25 ~20:00 UTC, instrument-builder

> **STATUS: LOG. This section supersedes the STATUS banner at the top of the
> file for findings C2–C5 and C8–C11.** C1 is PARTLY OPEN and its remaining
> half is owned by another file. Nothing here is committed; the director rules
> and the resident commits.

Files changed: `ledger/Assets/Scripts/Core/KitDressing.cs`,
`ledger/CoreTests/Program.cs`, `ledger/Assets/Scripts/Game/StreetDressing.cs`.
Files deliberately NOT changed: `SimDirector.cs`, `WorldBuilder.cs`,
`TrafficHost.cs`, `tools/**` — other agents are in them.

## The first real series, before and after

Machine output from a standalone replay of the live call sites at realistic
rates — `StreetDressing`, `WorldBuilder.MakeLamp` and `TrafficHost` as they
stand in the tree. 320 sites offered, seventy-two of them refused by geometry,
which is the audit's own headline shape. The same replay drives both readings;
the only difference is the five refusal sites, which is the C2 change at the
call site.

**BEFORE**

    kitPlaced=243/320/5 kitFamilies=8/8/11/0unknown kitBy=[lamp:41/44/3,works_cluster:9/9/0,works_cone:48/60/0,works_barrier:15/21/0,works_lamp:18/18/0,sign_post:nothing-offered,sign_plate_name:nothing-offered,sign_plate_warning:nothing-offered,signal_head_secondary:6/8/2,planter:16/40/0,yard_fence:90/120/0] kitByVariant=[lamp/curved:12/0,lamp/curved_double:9/0,lamp/curved_cross:4/0,lamp/square:11/0,lamp/square_double:5/0,lamp/square_cross:0/3,signal_head_secondary/vertical:6/2,yard_fence/1x1:22/0,yard_fence/1x2:22/0,yard_fence/1x3:23/0,yard_fence/1x4:23/0] kitAmounts=[lamp:200.20/41/0bad/4.44..5.20..5.20,planter:105.14/16/0bad/6.57..6.57..6.57,signal_head_secondary:6.70/6/0bad/1.05..1.11..1.18,yard_fence:722.10/90/0bad/3.52..9.44..12.40] kitFlagsBy=[lamp/district_unlisted:1,lamp/double_no_axis:1,lamp/paint_refused:3,planter/in_road:12,planter/no_room:12,signal_head_secondary/paint_refused:1,works_barrier/off_road:6,works_cone/off_road:12,+2more]/n96 kitUnknownBy=[none]/0of8 lampVariants=5/6 lampsByKind=[curved:12/0,curved_double:9/0,curved_cross:4/0,square:11/0,square_double:5/0,square_cross:0/3]/n41of44 signPosts=nothing-offered signPlates=nothing-offered namePlatesPainted=nothing-offered worksClusters=9/9 worksProps=81/99 worksLampsLit=18/18 secondaryHeads=6/8 yardFenceRuns=90/120 yardFenceMetres=722.10/90/0bad/3.52..9.44..12.40 plantersPlaced=16/40

**AFTER**

    kitPlaced=243/320/5/72refused kitFamilies=8/8/11/0unknown kitBy=[lamp:41/44/3/0refused,works_cluster:9/9/0/0refused,works_cone:48/60/0/12refused,works_barrier:15/21/0/6refused,works_lamp:18/18/0/0refused,sign_post:nothing-offered,sign_plate_name:nothing-offered,sign_plate_warning:nothing-offered,signal_head_secondary:6/8/2/0refused,planter:16/40/0/24refused,yard_fence:90/120/0/30refused] kitByVariant=[lamp/curved:12/0,lamp/curved_double:9/0,lamp/curved_cross:4/0,lamp/square:11/0,lamp/square_double:5/0,lamp/square_cross:0/3,signal_head_secondary/vertical:6/2,yard_fence/1x1:22/0,yard_fence/1x2:22/0,yard_fence/1x3:23/0,yard_fence/1x4:23/0] kitAmounts=[lamp/height:nosum/41/0bad/4.44..5.20..5.20,planter/height:nosum/16/0bad/1.31..1.31..1.31,signal_head_secondary/mountgap:nosum/6/0bad/1.05..1.11..1.18,yard_fence/run:722.10/90/0bad/3.52..9.44..12.40] kitFlagsBy=[lamp/district_unlisted:1,lamp/double_no_axis:1,lamp/paint_refused:3,signal_head_secondary/paint_refused:1,works_lamp/night_light:18]/24calls kitRefusedBy=[planter/in_road:12,planter/no_room:12,works_barrier/off_road:6,works_cone/off_road:12,yard_fence/in_terrace:30]/72sites kitUnknownBy=[none]/0of8 lampVariants=5/6 lampsByKind=[curved:12/0,curved_double:9/0,curved_cross:4/0,square:11/0,square_double:5/0,square_cross:0/3]/n41of44 signPosts=nothing-offered signPlates=nothing-offered namePlatesPainted=nothing-offered worksClusters=9/9 worksProps=81/99/3of3 worksLampsWired=18/18 secondaryHeads=6/8 yardFenceRuns=90/120 yardFenceMetres=722.10/90/0bad/3.52..9.44..12.40 plantersPlaced=16/40

Nineteen keys became twenty (`kitRefusedBy` is new). **The audit's prediction
that the cap would eat `works_lamp/lit` is CONFIRMED by the BEFORE line above,
not merely predicted:** ten distinct flag rows, eight shown, `+2more`, and the
two cut are `works_lamp/lit` and `yard_fence/in_terrace`.

## Finding by finding

| # | what changed | the test that covers it |
|---|---|---|
| **C1** | **PARTLY OPEN — see below.** The token sweep moved out of the test into `KitDressing.BadTokens(fragment, out walked)`, so it takes a STRING and can be pointed at the wrapped form. The class header now states the emit contract. | `Check(wrapped.Count == 1 && wrapped[0].Contains("two \`=\` in one token"), "wrapping the fragment in a key is refused, by name")` — the rejecting case, with the accepting case (20 tokens, 0 bad, over 13 lines) asserted above it |
| **C2** | Third outcome `Refused(family, reason)` in Core, files the outcome AND the reason in one call. The five `StreetDressing` sites (`:216 planter/in_road`, `:218 planter/no_room`, `:309 yard_fence/in_terrace`, `:436 works_cone/off_road`, `:452 works_barrier/off_road`) now call it. `kitPlaced` and every `kitBy` row grew a fourth field; new key `kitRefusedBy=[…]/72sites`. | `Check(208 + 19 + 18 == 245, "placed + missed + refused == offered")`, plus an ALL-REFUSED fixture asserted to differ from the ALL-MISSED one line for line, and the accepting fixture rebuilt to file refusals because **the old fixture certified a shape no live caller produces** |
| **C3** | `FlagLit="lit"` → `FlagNightLight="night_light"`; `worksLampsLit` → `worksLampsWired`. `Emit` now returns false on `bb.size.y <= 0.01f` — `Stand` skips its normalisation under the same threshold, so a model with no measurable height reaches `Emit` and would seat its lens in the road. **Chosen over deleting the key; reasoning below.** | `worksLampsWired=9/12` pinned in the accepting fixture (a value the old code could not produce), `Check(!line.Contains("worksLampsLit"))`, and `worksLampsWired=nothing-flagged/12` for a dead call site |
| **C4** | The planter literal `2.96f * 2.22f` is gone. `StreetDressing` measures the standing object's bounds through a new `WorldBounds` helper and files `stood.size.y`. `kitAmounts` rows are keyed `<family>/<kind>` from a Core table (`height`, `mountgap`, `run`) and an INTENSIVE row prints `nosum` where the meaningless sum was. | `planter/height:nosum/6/0bad/0.07..1.31..1.31` — a fixture where one planter skipped the scale, which a folded literal could never show; plus `Check(!line.Contains("6.57..6.57..6.57"))` |
| **C5** | `Amount()` returns `nothing-offered` when no call named the family and `nothing-measured` only when it ran without a scalar. `kitAmounts` does the same one level up. | `quiet.Contains("yardFenceMetres=nothing-offered")` and `kitAmounts=[nothing-offered]` on the never-ran line, against `missLine.Contains("kitAmounts=[nothing-measured]")` on the same run **in the same assertion block**, so the two words cannot re-converge |
| **C8** | `PlacedOver` over several families appends `<named>of<N>`. `worksProps=81/99/3of3`. | accepting case `worksProps=78/88/3of3` first, then a fixture with only `works_cone` wired asserting `worksProps=40/40/1of3` |
| **C9** | `kitFamilies`'s first two fields are catalogue-scoped, so all three share a denominator. Eleven junk names now print `0/0/11/11unknown`, not `0/11/11/11unknown`. | `typoLine.Contains("kitFamilies=0/0/11/1unknown")` and an explicit `Contains(...) == false` on the old string |
| **C10** | Two caps instead of one. `TailCap`(8) bounds lists of invented names; `RowCap` = `Catalogue.Length + TailCap` bounds the per-family lists, which are non-empty by design. `/n<total>` → `/<total>calls` and `/<total>sites`, so nobody divides shown rows by a run total. Refusals left the flag channel entirely, taking live flag rows from ten to five. | accepting case first: `Check(!line.Contains("more]"), "a healthy populated run loses no per-family row to a cap")`; rejecting case: a 20-flag-row fixture asserting `,+1more]/20calls` |
| **C11** | The hand-listed seven-line array is gone. Every line the test builds — now **13**, including `typo`, `many`, `blank` and a new flooded case — goes through `BadTokens`, and `walked == 13 * 20` is asserted before `bad.Count == 0`. | `Check(lines.Length == 13, …)`, `Check(walked == 13 * 20, …)`, and `BadTokens("")` asserted to be a FINDING rather than a clean sweep |
| C6 | **NOT DONE — out of ownership.** `DID_NOT_HAPPEN` and `KEY_VALUE` live in `tools/gates.py`. `nothing-offered`, `nothing-measured`, `nothing-flagged` and `nothing-refused` are all invisible to `--constant`, and six bracketed keys are invisible to its key harvest. Unchanged and still true. | — |
| C7 | **Left visible, as briefed.** `sign_post` / `sign_plate_name` / `sign_plate_warning` still print `nothing-offered` every run and that is the honest reading. Its SECOND half was a real fault and is fixed: `namePlatesPainted` spanned both plate families while its name claims one, so unpainted warning plates would have diluted it silently. It now reads `sign_plate_name` only — `17/19`, not `17/31`. | `Check(line.Contains("namePlatesPainted=17/19"), "the name-plate ratio is over name plates, which is what it is called")` |

## C1 is half fixed and the other half is not mine to touch

The wrapper is at `SimDirector.cs:16058` and reads

    $"kitDressing={WorldBuilder.KitTally.Line()} " +

`SimDirector.cs` was placed off-limits mid-task, so it is untouched. **The fault
is unchanged in the tree:** the replay above prints
`WRAPPED-FIRST-TOKEN kitDressing=kitPlaced=243/320/5/72refused`. What landed is
the guard and the contract, not the repair.

**The one-line fix, for whoever owns that file:**

    WorldBuilder.KitTally.Line() + " " +

`Line()` returns twenty self-labelling `key=value` tokens (`kitPlaced=`,
`kitBy=`, …), so bare is the correct emission and no label is lost. Do NOT
instead collapse `Line()` to one value: the twenty flat keys exist so
`gates.py --series` can carry each across runs.

## C3 — why the flag was renamed rather than deleted

`Emit`'s only false return was `rends.Length == 0`, and `Stand` already returns
null in that case, so the numerator was called exactly once per denominator —
one variable printed twice, the `pulseMedian`/`uneaseMedian` shape. Two
separable faults were tangled in it:

1. **The name was false.** The lamp is born `enabled = false` and handed to the
   night sweep. `worksLampsLit=18/18` would have been read as "every works lamp
   is emitting" and says nothing about emission. Renaming to `worksLampsWired`
   with `FlagNightLight` makes `18/18` a TRUE statement — eighteen placed lamps,
   eighteen lights registered.
2. **The predicate was vacuous.** `Emit` now returns false when the lamp's
   measured bounds have no height (`<= 0.01f`, the same threshold `Stand` uses
   to skip its normalisation and `MakeLamp` uses at 0.5m). That is a reachable
   state — a mesh that arrives unnormalised passes `Stand` and reaches `Emit` —
   and it is the fault worth catching, because such a lamp would put its lens
   at the road surface.

Deleting the key was the alternative and I rejected it: it is the only counter
on the roadworks light path, and the fault was the NAME plus a vacuous
predicate, not the existence of the measurement.

**The residual, stated so nobody re-derives it as fixed:** on a healthy prefab
`worksLampsWired` will still read `N/N` every run, because the predicate is only
false for a degenerate model. It is no longer *arithmetically* forced, but it is
a near-constant. **Nothing in this repository measures whether these lamps
actually emit at night** — that is `SetLampsEnabled`'s question and belongs
beside `WorldBuilder.LampSweeps`, which is out of my ownership. The stale
comment in `Emit` that claimed `worksLampsLit` was that instrument has been
corrected in place.

## Other conclusions this overturns or confirms

- **CONFIRMS** the audit's C10 prediction, from machine output rather than
  arithmetic: at the live population the cap bit at eight rows and cut
  `works_lamp/lit` and `yard_fence/in_terrace`.
- **CONFIRMS** C2's count exactly: seventy-two refused sites, now printed as
  `kitPlaced=…/72refused` and `kitRefusedBy=…/72sites` — two counts of one
  population, which is the self-check.
- **OVERTURNS** the audit's "what the first landed reading will look like"
  table for eight rows. `plantersPlaced=16/40` no longer stands alone: the
  adjacent `planter:16/40/0/24refused` says nothing failed to load. `worksProps`
  reads `81/99/3of3`. `worksLampsLit` does not exist.
- **STALE ELSEWHERE, not edited (other agents' files):**
  `agent-reports/street-clutter.md:84-94` and `agent-reports/kit-survey.md:175`
  both specify the old key shapes, including `worksLampsLit=N/worksLamps=M` —
  which is itself a two-`=` token, so C1's shape was in the brief that produced
  it.

## Two things I could not do and one I chose not to

- **C6** needs `tools/gates.py`. Out of ownership. The four sentinel words plus
  the six bracketed keys remain invisible to `--constant`, which is the tool
  this project relies on to notice a number that never moved.
- **`BadTokens` is `internal`, not `public`.** A public one is a tested Core API
  with no Game caller, and `tools/reach-check.sh` failed the build for it —
  correctly. `CoreTests` compiles the Core sources into its own assembly, so
  `internal` reaches the test. Every other Core class's fragment could use this
  checker; nothing else does yet.
- **`lampsByKind` still prints `/n41of44`** with an `n` prefix while its
  neighbours now say `calls` and `sites`. It is `placed of offered`, its `of`
  already labels it, and renaming it would have changed a key nobody asked me
  to touch.

## Verify, read off disk

`ledger/.verify-footer` is **ABSENT**, which is what a red run leaves, so there
is no green footer to quote. `python3 ledger/verify.py` reported, in the footer
it printed to stdout:

- `4005 CoreTests` — green. The one assertion that was red (the pinned accepting
  string) now describes the new format; it was widened, not weakened, and eleven
  assertions were added around it.
- `35 on the reach ledger` — green. It was `reach FAILED — 1 unreached` on my
  first run, and that red WAS mine: `KitDressing.BadTokens` was `public`, which
  makes it a tested Core API with no Game caller. Made `internal`; `CoreTests`
  compiles the Core sources into its own assembly, so the test still reaches it.
- `0 shape errors (189 files)`, `Game layer compiles (183 files)`,
  `0 lint errors`, `0 static/instance errors`, `0 filename-as-type errors` —
  green over the edited `StreetDressing.cs`.
- `director cadence ok … REVIEWED` — green (it was `DIRECTOR RAN BUT DID NOT
  RULE` on my first run; a ruling landed while I worked).

**The one remaining red is not mine and I did not touch it:**

    UNTRACKED/ABSENT TOOL(S): tools/hang-report.py(untracked)

`tools/hang-report.py` is another agent's new file, alongside
`agent-reports/sim-hang-e8c5949.md`. `tools/**` is outside my ownership. It
needs `git add`-ing by whoever owns it before verify can go green.

---

## CORRECTION — 2026-08-25 ~20:10 UTC, same author

Two claims in the section above went false within minutes of being written, and
this file is now committed, so they are corrected here rather than edited away —
a reader who finds "the fault is unchanged in the tree" would go and re-fix an
applied fix, which is rule 3's "a doc saying something is missing is an
analysis, not evidence" pointed at my own report.

**C1 IS CLOSED, NOT HALF OPEN.** The owner of `SimDirector.cs` applied the
one-line repair while I was writing. In HEAD (`71316fa1`), line 16257 reads

    WorldBuilder.KitTally.Line() + " " +

so the fragment is emitted bare and `kitPlaced` is a top-level key again. The
section above says "the fault is unchanged in the tree" — that was true at
19:5x and is false now.

**AND THE TWIN SWEEP IS CLEAN, checked rather than assumed.** Fixing a wrapper
means grepping for the same wrapper elsewhere. There is exactly one other
`key={…Line()}` in `SimDirector.cs` — `looseEnds={GameController.LooseEndsTally.Line()}`
at `:15894` — and `LooseEnds.Line()`'s body contains **zero** `=` characters in
any emitted literal, so it returns one value and wrapping it is correct. That
confirms the audit's C1 paragraph from the code rather than quoting it.
`CostTracker.Line()` and `FrameRate.Line()` likewise emit no `=`, and neither
has a Game-layer emit site at all. `KitDressing` was the only site with the
fault.

**VERIFY IS GREEN AND THE FOOTER IS ON DISK.** The section above says
`ledger/.verify-footer` is ABSENT and names `tools/hang-report.py(untracked)`
as the one red. Both have since resolved: the footer was written at
20:03:53 UTC and reports `0 lint errors, 0 shape errors (189 files), 35 on the
reach ledger, Game layer compiles (183 files), … 4005 CoreTests`, with
`19 workflow-named tool(s)` where the red run had 18 — the untracked tool is
tracked. The footer's `director cadence ok (0 changed line(s) …)` is what a
clean tree prints, not a review that was skipped.

**THE WORK IS COMMITTED, BY THE RESIDENT, AT `71316fa1`** ("The street gets
furniture, and the gate that said it was reviewed was lying"). I did not commit
it. All five refusal sites, `WorldBounds`, `FlagNightLight` and the rebuilt
`TestKitDressing` are in HEAD.

**STILL OPEN AND UNCHANGED:** C6 (`tools/gates.py` — the four sentinel words and
the six bracketed keys are invisible to `--constant`), and C3's residual (on a
healthy prefab `worksLampsWired` reads `N/N`; nothing measures whether these
lamps emit at night).
