# Street nameplates, and the unified lettering helper

> **STATUS: LOG, 2026-08-25.** Builder report (systems-builder) on rulings C
> and D of `decision-dressing-batch.md`. Landed in `1ea2c48a` (swept into that
> commit alongside another agent's `ValuePanel` work; the tree was clean at
> the time of writing). NOT CURRENT once the first build carrying it lands and
> its verdict is read.

## 1. The unified helper, and where the two old copies went

**`WorldBuilder.Letter`, `WorldBuilder.cs:2251`.** Signature:

    public static int Letter(string name, Vector3 at, string text, float yaw,
                             float charSize, Color colour, bool bothSides,
                             float proud, out TextMesh front,
                             Transform parent = null)

It returns **how many faces got the depth-testing material, 0..2** — not a
success flag and not a count of labels. Zero is reachable: `WorldText.Adopt`
refuses when `Hidden/LedgerText` is absent from the build and then leaves
Unity's `ZTest Always` material in place, which is the shader that put
garbled glyphs over the skyline in this project's first committed still.

**The two copies it replaced, and what each contributed:**

| was | now |
|---|---|
| the fascia trade-name block, `WorldBuilder.cs` (~1725 before the edit) — single-sided, cream ink, threw away `Adopt`'s return | one `Letter` call at `WorldBuilder.cs:1755` |
| `StreetFurniture.Label` — double-sided, enamel ink, carried the reverse-face-cull paragraph the fascia copy did not have | a three-line shim at `StreetFurniture.cs:760` that calls `Letter` |

They differed on exactly three things and nothing else, and all three are now
arguments: `bothSides` (a fascia's back is inside somebody's front room), the
ink colour, and `proud`. `proud` was hardcoded `0.05` in both — correct for
the 5cm primitive boards they were written for, and it would have **buried
every name inside the mesh** on the 0.31m-deep kit blade. That was a live
trap waiting for the third copy, which is precisely the director's argument
for doing the extraction first.

`Label` was kept as a named shim rather than inlined because its one
remaining caller (`Plate`, for the BUS/TAXI plates) differs only in `size`;
every other argument is a house convention that belongs in one place in that
file rather than transcribed twice.

`WallPlate` was **deleted**, not kept — after the change it was pure
indirection, a second name for one idea, which is the thing this task exists
to remove. Its two call sites now go straight to `NamePlate`.

## 2. The grep proving there is no third copy

    $ grep -rn "AddComponent<TextMesh>()" ledger/Assets/Scripts/
    Game/SpeechBubble.cs:165:  b._text = go.AddComponent<TextMesh>();
    Game/WorldBuilder.cs:2267:      var tm = go.AddComponent<TextMesh>();     <-- inside Letter
    Game/NpcWalker.cs:641:     npc._label = labelGo.AddComponent<TextMesh>();

    $ grep -rn "WorldText.Adopt(" ledger/Assets/Scripts/
    Game/WorldBuilder.cs:2280:      if (WorldText.Adopt(tm)) adopted++;       <-- inside Letter
    Game/NpcWalker.cs:680:     WorldText.Adopt(npc._label);

**One static-world-lettering implementation.** The two survivors are a
different idiom and are deliberately not folded in — both are DYNAMIC labels
attached to a moving body and rewritten every frame, where `Letter` builds
once and never touches the object again. Stating that explicitly so the
absence does not read as a missed twin: `SpeechBubble` additionally does not
adopt at all, and `SpeechBubble.cs:173-193` already carries the reason
(`Hidden/LedgerText` also sets `Cull Back`, which a bubble must not have).
Checked, not assumed.

    $ grep -rn "new Ledger.Core.KitDressing\|new KitDressing" ledger/Assets/Scripts/
    Game/WorldBuilder.cs:3598:  new Ledger.Core.KitDressing();

**Exactly one instance**, as required.

## 3. Where the plates mount, and how the sites are chosen

`StreetFurniture.NamePlate` (`StreetFurniture.cs:566`), four call sites, all
inside `BuildNamePlates`:

* **Wall-mounted at terrace corners** (`:309`, `:311`) — the pre-existing
  quadrant probe is unchanged: four corners are tried until one has a wall
  whose two junction-facing faces are both exposed, the NS name goes on the
  wall you see walking that street and the EW name round the corner, 1.6m
  from the corner each way at 2.7m up.
* **On the clustered low post** (`:327`, `:329`) — the fallback for a
  junction with no corner building, which is also what a council does.

**The plate is `road-sign-object-street` and the pole is not.** The survey
measured the blade at 0.31 x 0.44 x 1.42m — 3.2:1, a British nameplate — and
REJECTED `road-sign-street`, the tall crossblade on a 3.5m pole, as the
American form. Nothing here reaches for the pole, and `NamePlate`'s header
says so in those terms so a later reader cannot re-derive it the other way.

**Oriented by measurement, never by an assumed FBX axis order.** The blade is
stood through `StreetDressing.Stand` (made `internal` for this — see §7), its
world bounds are encapsulated, and if the long horizontal extent came out
ACROSS the wall instead of along it, it gets a quarter turn **about the
mounting point** so it stays where it was hung. That is `Stand`'s own
discipline of re-reading bounds after every transform, applied to the axis
order rather than the scale, and it means the code is correct whichever way
the importer lays the model out — a fact this container cannot read and the
build can. The turn is counted (`blade_turned`), so the verdict says which
way it landed.

**Seated by its middle, not its foot.** `Stand` puts a prop's bottom on
`at.y`, which is right for a cone and wrong for a plate hung at a height, so
the anchor is dropped by half the blade's true height (0.44m — the FBX's own
6.00 units x the kit's measured 0.074 m/unit, from `tools/prop-dimensions.py`,
re-run this session: `road-sign-object-street  32 verts  4.25 x 6.00 x 19.25`).

## 4. Do they letter? Measured, and the answer has three outcomes

**Yes — and the fit is measured at runtime rather than assumed.** The kit
ships a flat palette texture, so the blade carries no glyphs and never could;
a blade placed as-is is a blank white board, which reads as a fault. The
lettering is `WorldBuilder.Letter`.

The two faces are two `Letter` calls rather than one `bothSides` call, on
purpose: the front is created first so its **rendered width** can be read off
its renderer bounds, and the back is created afterwards at whatever size that
reading settled on. The width is projected onto the wall axis, so it is the
extent that actually has to fit.

Three outcomes, all flagged, because "it fitted" and "nothing measured it"
must not print alike:

| flag | means |
|---|---|
| `text_fitted` | the rendered width was read and fitted inside 90% of the blade |
| `text_shrunk` | it was read, it overran, `characterSize` was scaled down to fit |
| `text_unmeasured` | the renderer had no bounds yet — a TextMesh generates its mesh lazily, so this is a live possibility rather than a defensive branch, and it is the reading that would send the next person here |

**The starting size is derived, not invented:** `InkPerMetre = 0.05f / 2.2f`,
from the one lettering value in that file that has actually shipped and been
looked at (the wall nameplate lettered its 2.2m board at 0.05). It is
explicitly a starting value and not a bound, and the comment says why: **it
has never been seen carrying a long name.** Until the Core fault in §6 is
fixed, every plate this game has ever rendered read "Hook Street" or "Quay
Street" — eleven characters. The tables hold 51 names up to eighteen
("Morning After Lane"). The fit measurement is what makes the size
trustworthy, and the flag series is what lets the next reader set the ratio
from evidence instead.

## 5. The done-line fragment my calls produce

**Not predicted — measured**, by replaying the exact call sequence against
the real `StreetMap` through `KitDressing` itself in a scratch console
project, and printing `Line()`. Three worlds:

    blade in build, text measurable
      kitPlaced=2/194/0/192refused
      kitBy=[...,sign_plate_name:2/194/0/192refused,...]
      kitFlagsBy=[sign_plate_name/painted:2,sign_plate_name/text_fitted:2]/4calls
      kitRefusedBy=[sign_plate_name/junction_unnamed:192]/192sites
      signPlates=2/194/1of2
      namePlatesPainted=2/2

    blade MISSING from the build
      kitPlaced=0/194/2/192refused
      kitFlagsBy=[sign_plate_name/board_lettered:2,sign_plate_name/text_fitted:2]/4calls
      namePlatesPainted=0/0

    blade in build, TextMesh bounds unreadable
      kitFlagsBy=[sign_plate_name/painted:2,sign_plate_name/text_unmeasured:2]/4calls

`sign_plate_name` stops printing `nothing-offered`, which was the ordered
outcome. Every token carries exactly one `=` and no spaces (checked
mechanically in the same replay).

### The impossibility I built and killed

The first replay printed **`namePlatesPainted=2/0`** — a numerator above its
own denominator. `FlagOver(painted, sign_plate_name)` divides painted flags
by PLACED plates, and I was flagging `painted` for the lettered fallback
board too, so a run with no kit model claimed two painted plates over zero
placed. That is the `44 offered against 28 ever managed` shape exactly. The
flag is now scoped to a blade that actually stood, and a lettered fallback
board files `board_lettered` instead — a real and different fact, with its
own row rather than a share of a key whose name claims something else.

I would not have seen this without running the replay. A predicted done line
would have looked fine.

## 6. THE FINDING — 96 of 97 junctions cannot say what they are

**This is the most important thing in this report and it is NOT fixed here.**

Measured by compiling `Assets/Scripts/Core` alone into a scratch console
project and counting (no Unity needed):

    junctions=97  namedJunctions=1  distinctStreetNames=2
    names: Hook Street / Quay Street
    namesInTable=51

`StreetMap.NamesAt` returns names for **exactly one junction in the entire
city** — the founding cross at (0,0). The tables hold 51 street names across
seven districts and 49 of them are unreachable at any real coordinate.

**The cause.** `StreetMap.NameOf` compares SCALED node coordinates against
the UNSCALED district avenue tables:

    if (Math.Abs(line[i] - coord) < 0.001) return names[i];

Nodes are built at `ScaleAbout(d.AvenuesX[i], 0, 2.15)`, so only `0` — which
scaling about the origin leaves fixed — can ever match. `DistancePenalty` and
`AddressOf`'s nearest-street fallback read the tables raw the same way. With
the tables scaled, the same census reads **`namedJunctions=97`, 51 distinct
names**.

**This is the SIXTH consumer of those tables to read them raw.** `BoundsOf`'s
comment already names five (`DistrictAt`, `SimDirector.DistrictTour`,
`Population.Place`, the ground extent, the address migration) under the
heading *"One idea, five implementations, and the four nobody looked at were
the four missing a line."* This is the fifth one nobody looked at.

**And the guard written for exactly this fault cannot see it.**
`tools/lint-avenues.py:54` reads

    OWNER = "StreetMap.cs"          # the transform lives here; it may read raw

The exemption is right for `BoundsOf`, which owns and applies the transform.
It is wrong for `NameOf`, which is a plain consumer that happens to live in
the same file — and the lint cannot tell those apart. It reports **`0 raw
avenue reads (184 files)`** every run, which is a clean result over a
denominator that excludes the one place the fault is.

**Why I did not fix it.** It is Core, outside my ownership; the fix changes
`AddressOf`'s output, which feeds gossip and witness lines — moat systems I
was not briefed on; it breaks three assertions in `CoreTests/Program.cs`,
which my brief fences off (and those three pass today only because they feed
RAW coordinates, and `NamesAt` is tested against `j2_2` — the one node where
raw and scaled coincide, which is rule 5b's corollary exactly); and it
changes a conclusion in the director's own ruling C, which CLAUDE.md makes a
mandatory director spawn rather than a builder's call.

**What I did instead — the instrument.** An unnamed junction is now filed as
`Offered` + `Refused("junction_unnamed")` rather than silently skipped, two
sites per junction. So the verdict carries

    kitRefusedBy=[sign_plate_name/junction_unnamed:192]/192sites

**every run**, with its denominator. Without it the key would print
`sign_plate_name:2/2/0/0refused`, which reads as a placer that hardly ran,
when the truth is a placer that ran at every junction in the city and was
given a name at one of them. The Core fault is now legible in the channel
everybody already reads, which is worth more than my having quietly patched
it — and rules the director rather than me.

**Ruling C's premise needs restating.** "The game has named streets and no
way to read a name off the street" is not quite it: `BuildNamePlates` has
been placing lettered plates for as long as it has existed, and the landed
verdicts say `signs=59 wallPlates=2` — two plates, at the one junction that
can name itself. The hole is in the lookup, not the signage.

## 7. What I did not do, and why

* **`road-sign-empty` / `sign_post` — DROPPED.** Item three, and the
  coordinator's instruction was to drop it. It is also the one piece that
  would have needed an invented colour: `Stand` takes a `Color`, and unlike
  the blade (which reuses `StreetDressing`'s landed `BarrierWhite`, an
  off-white already shipped and looked at on a prop from this kit under this
  grade) I have no measured grey for a galvanised post. Rule 2 says do not
  invent it. The primitive `Post` still stands under the clustered plates.
* **`road-sign-object-warning` — DROPPED, and I did not touch it.** The
  director ruled the post-mounted `road-sign-warning` REJECTS outright and
  the loose plate is conditional on a still, not on a number. Re-measured for
  the record: `7.73 x 13.38 x 13.38` — symmetric top-to-bottom, so a US MUTCD
  diamond and not a British triangle, which is what the ruling turns on.
* **`StreetMap.NameOf` — NOT fixed.** §6.
* **`kitAmounts` for the plates** — I file no `Measured` scalar.
  `sign_plate_name` is not in `KitDressing.AmountKinds`, so a sample would
  print `sign_plate_name/unknown:<sum>/...` with a meaningless sum of
  character sizes, and fixing that means editing `Core/KitDressing.cs`, which
  my brief fences off. Named as adjacent work below.

### Adjacent work, with names (rule 11)

1. **`NameOf` scaling** — the Core fix, plus the three raw-coordinate
   assertions in `CoreTests/Program.cs`. Needs a director ruling first
   because it changes address strings.
2. **`lint-avenues` OWNER exemption** — narrow it from "the file" to "the
   methods that apply the transform", or the guard keeps certifying the one
   file that has the fault.
3. **`sign_plate_name/lettersize` in `KitDressing.AmountKinds`** — one row,
   declared `nosum`, so the fitted character size can be filed as a series
   and `InkPerMetre` set from evidence.
4. **`sign_post` from `road-sign-empty`** — blocked only on a measured post
   colour.
5. **The pub-sign board** (`road-sign-empty-hanging`) — already on the
   quality ladder; `Letter` is now the helper it needs, and the `proud`
   argument is why it will not repeat the buried-glyph trap.

## 8. What I ran locally

* `python3 ledger/verify.py` — **RED, and not on my files.** See §9.
* `dotnet run --project GameCheck` from `ledger/` — binds all three of my
  files with **no errors** (only pre-existing `CS0162` unreachable-code
  warnings from the `TownPlanEnabled` const branches). Errors it does report
  are `RenderSettings.customReflectionTexture` shim gaps in `SkyEnvironment`
  and `WetReflections`, files I did not touch.
* Scratch Core console project (`Assets/Scripts/Core/**` + the four
  engine-free Game files, same includes as `CoreTests.csproj`) for the
  junction census in §6 and the `KitDressing.Line()` replay in §5.
* `python3 tools/prop-dimensions.py road-sign-object-street` etc. for the
  blade, post and warning-plate dimensions.

## 9. The verify footer

**`ledger/.verify-footer` DOES NOT EXIST ON DISK, so I have no footer to
quote.** A green run writes it and a red run deletes it; per the rule that
the footer is read from the file and never from scrollback, I am not pasting
the scrollback footer as if it were one.

**The red is isolated and it is not code — 50 of verify's 51 checks pass.**
Established two independent ways. First by splitting my run's footer into its
81 comma-separated check segments and diffing them against the last committed
green footer (`1ea2c48a`'s own commit message). Then confirmed by importing
`verify.py` as a module and calling each of its 51 check functions
individually, printing ok/RED per check — **one RED, `template_sync`**, and
fifty ok. Both agree:

    template-sync: DRIFT — 1 of 4 process section(s) changed since the
    marker was stamped on 2026-08-25: THE-HYBRID-RESIDENT
    (now=8e2fa98b9d793081 marker=...) sections=4/4 lines=453/1478.
    DISCHARGE one or the other: sync jsab258/game-studio now and re-stamp
    with `python3 tools/template-sync.py --stamp --template-sha <sha>`
    or defer with `--stamp --defer <queue-item>` naming a queue item

That is `CLAUDE.md`'s hybrid-resident process section drifting from the
studio template. **`CLAUDE.md` is modified in the working tree as this is
written, and `.claude/agents/systems-builder.md` and `instrument-builder.md`
were modified earlier in the session** — the coordinator raising this role's
turn ceiling from 45 to 70. None of them is mine; I touched no process
document. **It needs a stamp or a deferral, not a code change**, and that is
the resident's call rather than a builder's:

    python3 tools/template-sync.py --stamp --template-sha <sha>     # or
    python3 tools/template-sync.py --stamp --defer <queue-item>

Every other segment that differs from the green baseline differs benignly:
the cadence counters (the tree is clean now, so `0 changed lines` and `review
not required`), the Fable-spend readings, and `docs 99/99 clean` — up from
98/98 because this report added a doc and it passes `docs-check`.

**On a clean tree.** `git status` shows no modification of mine; my work
landed in `1ea2c48a`, so this reading describes HEAD rather than any
uncommitted change of mine.

**Every check that names my files reads clean:** `0 lint errors`, `0 shape
errors (190 files)`, `0 shadowed Core types`, `0 nested-type errors`, `0
static/instance errors (75 members, 559 bodies)`, `0 filename-as-type
errors`, `0 namespace-as-value errors`, `reach ok`, `Game layer compiles (184
files)`, `4049 CoreTests`, `0 raw avenue reads (184 files)` — that last one
being the check §6 shows cannot see the fault it was written for.

**An earlier red in this session was also not mine, and I proved it rather
than assuming it.** That run failed on `1 lint errors` at
`ledger/Assets/Scripts/Core/ValuePanel.cs:195`, an UNTRACKED file belonging
to another agent working concurrently. I stashed my three files and re-ran
`lint-usings.py`: the error persisted. It reads `0 lint errors` now that the
other agent has fixed it.

**Whoever commits next must re-run `verify.py` and read `.verify-footer`
themselves. Do not take a green from me — I never saw one.**

I did not dispatch a build and did not commit.

## 10. Honest limits on everything above

* **No frame has been seen.** Rule 4 says the artifact gets opened, and the
  newest verdict (`e8c5949`) is a hang with no done line and no stills, so
  there is nothing to open that describes this code. Every visual claim here
  — that the blade reads as a nameplate, that the ink is legible at street
  distance, that the paint survives the noir grade — is a HYPOTHESIS until a
  still lands. The numbers in §5 are arithmetic, not pictures.
* **The Game layer does not compile in this container.** `GameCheck` binds
  against shims and is a much stronger signal than ShapeCheck, but it is not
  Unity. Anything needing a real `TextMesh` at runtime — specifically the
  renderer-bounds read behind the fit measurement — is untested until CI.
  That is exactly why `text_unmeasured` exists as its own flag rather than
  as a silent fallback.
* **`text_unmeasured` is the outcome I most expect to see first.** If the
  first build's `kitFlagsBy` carries it, the fit read back nothing and the
  plates are wearing the derived `InkPerMetre` size — legible, probably, but
  unverified, and the fix is to defer the read rather than to change the
  size.
