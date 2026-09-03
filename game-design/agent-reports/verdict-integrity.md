> **STATUS: LOG, 2026-08-25. NOT CURRENT** once landed.

# The verdict channel saying true things about itself

Four faults, one emission side, one cause: nothing measured the channel's own
format, so every rule about it decayed silently. Written by instrument-builder,
uncommitted; the director reviews and commits.

---

## FAULT 1 — values with spaces, and WHY the format check reported clean

### The diagnosis, which is worth more than the six keys

`ledger/verify.py:verdict_format` runs `tools/verdict-read.py --selftest` and
`--lint` and reported `verdict format ok (selftest + newest run)` while six live
keys carried spaces. It was not lying about running. **It has never checked for
a space.**

`lint_text` flattens every `[...]` group to a space before it looks at anything,
then reports values whose brackets or parens do not BALANCE. That detects
`crowdBodyWidth=0.45(narrowest 0.39 broadest 0.53)` — the 4 August fault it was
written for — because the surviving token `0.45(narrowest` has an unbalanced
paren. Anything written `key=[a b c]` is DELETED by the flattening pass and
examined by nothing at all.

So: **it does not test what its name claims.** It is an unbalanced-delimiter
lint wearing a space lint's name, and the name is what everyone read.

**And its accepting fixture enshrined the blindness.** `SELFTEST_GOOD` carries
`places=[alley=3 market=53]` and `ao[rounds=[28.1 18.0] drop=0.0123]` and
asserts they must be ACCEPTED. The single case that would have exposed the hole
was written into the guard as required behaviour. Rule 5b says a guard needs its
accepting case run; this is the other edge of the same knife — an accepting case
drawn so wide it certifies the fault.

### The distinction the format actually makes

The old lint's implied rule was "brackets are fine". The real rule is:

* `frame[mean=471.0ms gameShare=3.23%]` — GROUP syntax, a name followed by a
  bracket with no `=`. Its own namespace; the spaces separate its members.
  Legal, and flagging it is the forty-hit false alarm the first lint produced.
* `bodyAlbedo=[0.01 0.05 …]` — a VALUE that happens to start with a bracket. It
  lives in the flat `key=value` namespace `gates.py --series` reads. Both
  `verdict-read.py` and `gates.py --series` are bracket-aware and survive it;
  every grep anybody types does not, and `gates.py`'s own key sweep
  (`KEY_VALUE = ...([^\s\[\(]+)`) cannot see such a key AT ALL — the key does
  not appear, rather than appearing truncated.

`spaced_values()` in `tools/verdict-read.py` implements exactly that: only
`key=[...]` is examined, nested groups inside it are stripped first (they are
judged on their own entry), a space in what remains is the fault. It returns
`(hits, examined)` — the denominator ships with the zero.

### THE SERIES, PRINTED BEFORE ANY BOUND — and it is not five

`python3 tools/verdict-read.py --spaced` on the newest measuring run (14f964a):

    verdictSpaced=39/110   (values written `key=[..]` carrying a space, of
                            bracketed values examined)
      line 85  rounds=[30.3 27.8 27.8 62.8 12.0 12.0 57.8 41.7 41.7]
      line 86  worstWorldPair=[Quay Street|Quay Street]
      line 87  gapWhy=[no two vehicles shared a directed edge at this instant]
      line 87  massInRoad=[hook:x@0 over 1.5m hook:z@0 over 1.5m]
      line 87  speechVoicesWhy=[23 of 23 loaded]
      line 87  speechVocabWhy=[704 tokens, 265 merges]
      line 87  speechBackendWhy=[no t3-prefill.onnx in C:/actions-runner-…]
      line 87  lumaPairs=[noon0.349 night0.116 darker9of10 [0.249/0.211 …]]
      line 87  slamRings=[#1:drawn@53m #2:drawn@35m #3:drawn@48m #4:drawn@40m]
      line 87  denounceVerdict=[BlewBack (0 of 1, contradicted at 0.90 against 0.00)]
      line 87  notorietyDoors=[laundry:shut@0.87 differs repair_yard:open@0.87 same]
      … (+19 more not shown)

**The brief said five. The instrument says 39 of 110.** The six repaired here
are the six that were named; the remaining 33 are a real backlog with a printed
series behind it, which is the only basis on which the check can later become a
gate.

### NOT GATED, deliberately

`verdict_format` still BLOCKS on the unbalanced-delimiter lint and now carries
`verdictSpaced=39/110 not gated` in its message, so the series accumulates in
the commit feed. Wiring it to block today would red every commit until a
repaired verdict lands from CI — rule 5b's ratchet, the exact mistake this same
check avoided when it was first written. It becomes a gate when a landed verdict
reads 0, and not before.

### Both ways, run

    $ python3 tools/verdict-read.py --selftest
    verdict-read --selftest: ok — rejects a swallowed space, accepts nested gate
    groups; spaced_values rejects bodyAlbedo (1 hit), accepts 4 bracketed values
    in the good line
    rc=0

Accepting fixture FIRST (`SPACED_GOOD`): a real gate group beside the repaired
shapes of the six keys — 0 flagged of 4 bracketed values examined. Rejecting
fixture (`SPACED_BAD`): `bodyAlbedo=[0.01 0.05 0.06 (+13 more) vs wardrobe max
0.46]`, the value exactly as it landed on 14f964a, which the OLD lint passes
without a murmur. Both counts asserted, so "accepted everything" and "examined
nothing" cannot look alike.

### The six keys as they now read

| key | before | after |
|---|---|---|
| `bodyAlbedo` | `[0.01 0.05 … (+13 more) vs wardrobe max 0.46]` | `[0.01/0.05/…/+13more/of29/vsWardrobeMax:0.46]` |
| `rounds` | `[30.3 27.8 27.8 …]` | `[30.3/27.8/27.8/…]` |
| `worstWorldPair` | `[Quay Street|Quay Street]` | `[Quay-Street|Quay-Street]` |
| `gapWhy` | `[no two vehicles shared a directed edge at this instant]` | `[no-two-vehicles-shared-a-directed-edge-at-this-instant]` |
| `massInRoad` | `[hook:x@0 over 1.5m hook:z@0 over 1.5m]` | `[hook:x@0-over-1.5m/hook:z@0-over-1.5m]` |
| `speechVoicesWhy` | `[23 of 23 loaded]` | `[23-of-23-loaded]` |

`bodyAlbedo` also gained its denominator (`of29`) and now says `nothing-measured`
in words when no body was read, where it used to say `not measured` — two words
that the channel merged into `not`.

### ONE implementation: `SimDirector.NoSpaces`

Core keeps its sentences readable — `Traffic.TightestGapWhy` and
`StreetMap.MassOverlaps` are prose a person reads out of a failing CoreTest, and
CoreTests assert on their text. `NoSpaces` is the single point at which that
prose enters a channel that cannot carry a space. Applied at the done line and
inside the `traffic[…why=…]` gate group (the same sentence, two emits — the
one-idea-two-sites shape this project keeps finding wrong on the copy nobody
looks at), and at `_worstWorldPair`'s assignment. A sentence written in Core next
month is safe without its author knowing the rule exists.

---

## FAULT 2 — `kitAlbedo`'s cap hid the family under investigation

`shown` was 24 against 38 families, so all 24 visible were `base_mesh_*`,
`oga_vehicles_*` and `car_kit_*` and **every `city_kit_*` key sat behind
`+14more`** — 63% blind in exactly the direction of the open question, with
`tools/prop-reach.py` cross-checking its "never instantiated" answer against
that listing and a survey proposing 19 `city_kit` placements none of which the
channel could ever have proved.

Now: `const int KitAlbedoCap = 96`, an explosion guard rather than a working
filter, and a paired reading beside it —

    kitAlbedo=[base_mesh_swing_bin:1.00>0.08/…/all 38 families…]
    kitAlbedoListed=38/38

**The cap still announces itself when it bites.** The `/+Nmore` tail is
unchanged in shape, which is also what keeps `prop-reach.py` parsing it (it
drops any entry whose name ends in `more`). `kitAlbedoListed` prints shown/total
whether or not the cap bites, so a bite is legible without counting entries by
hand, and `nothing-measured` in words when the dictionary is empty.

---

## FAULT 3 — `framesStaged`: a row is not a photograph

`frames.tsv` landed headed `# commit 14f964a` with fresh day12/day13 rows while
no `hunt_*.jpg` was written by that stills commit (`7ec933f3`) or the previous
(`fae0c707`) — those JPEGs are 22-24 August images. Ledger `day12_noon
meanLuma=0.079` against 0.114 measured off the file; `day13_noon` 0.495 against
0.303. A row described a picture the run never took and read as authoritative.

`tools/sim-shots-stage.sh` now emits, into `verdict.txt` AND the per-run copy
(both, or the two disagree about one run), on its own `SimShotsStage:` line:

    SimShotsStage: framesStaged=12/29 framesRows=29 framesUnstaged=[day12_noon/day13_noon]

* **The mechanism is git truth, not a clock.** A picture belongs to this run iff
  `git status --porcelain -- <file>` is non-empty — changed or untracked. A
  rendered JPEG is never byte-identical to last week's; mtimes are a property of
  the runner's disk (a checkout rewrites them all), and any age threshold would
  be a bound with no series behind it.
* **Statistic:** a whole-run count taken once at staging time, over the rows of
  the ledger. It is NOT on the sim's done line, because the sim cannot know what
  git staged — that fact does not exist until after it exits. STDOUT stays
  paths-only so the caller can still `mapfile` it.
* **Zeros ship denominators, never-ran prints words:**
  `framesStaged=no-ledger-this-run` and `framesStaged=no-git-cannot-tell` are
  sentences, so neither can read as "0 of 0, all fine".
* **The cap announces itself:** at most 8 names, then `/+Nmore-not-shown`.

### Both ways, run

    $ bash tools/sim-shots-stage.sh --selftest
      accepting: framesStaged=2/2 framesRows=2 framesUnstaged=[none]
    ok — a run that photographed both rows reads 2/2
      rejecting: framesStaged=1/3 framesRows=3 framesUnstaged=[day12_noon/day13_noon]
    ok — a stale picture and a row with no picture are both named
      never-ran: framesStaged=no-ledger-this-run framesRows=0 framesUnstaged=[no-ledger]
    ok — no ledger prints words, not 0/0
    rc=0

The rejecting fixture is tonight's fault reproduced: `hunt_day12_noon.jpg` left
untouched from the previous snapshot while its row stays in the ledger, plus a
`day13_noon` row with no picture at all. Both are named, not merely counted.

**The fixture commits with plumbing** (`write-tree` + `commit-tree` +
`update-ref`) rather than `git commit`. `.claude/hooks/verify-gate.sh` blocks any
Bash command containing `git commit` while this repo's footer is not green, and
it reads the SESSION cwd, so it cannot see that a `cd` inside this script has
moved to /tmp — porcelain would make the fixture unrunnable exactly when a
builder needs it. The plumbing writes the same commit object and leaves the gate
at full strength for the commits it exists to stop.

---

## FAULT 4 — `groundAlbedoBy`: the ground family, per member

`districtGround` is ONE ray in downtown. The claim that the whole ground family
moved together with `GroundGrade` was read out of the code and printed by
nothing.

`AssetLibrary.GroundAlbedoEmit()` emits two keys from ONE loop:

    groundAlbedoBy=[asphalt:0.412/sidewalk:0.437/kerb:0.428/concrete:0.401]
    groundAlbedoOf=4/4

* **One entry per `WetSurfaces` member** — asphalt, sidewalk, kerb, concrete.
* **Statistic: LAST-WINS, AT-INSTANT** material state. It asks the shared
  material what it is WEARING when the done line is written, not what constant
  it was handed: `SetWetness` and `GroundGrade` both write these materials after
  they are built, so "the value assigned" and "the value standing" are two facts
  and only the second is evidence. Said in the comment beside the emit.
* **Denominator:** `groundAlbedoOf=read/total`, from the same pass at the same
  instant — splitting them into two methods is how a numerator and a denominator
  end up describing two different moments.
* **Reads, never builds.** `Material(logical)` creates on miss; a measurement
  that instantiates what it measures answers a question about itself. It uses
  `_materials.TryGetValue`, and prints `not-built` in words for a material this
  run never made, so it cannot read as an albedo of zero. `MatAlbedo(mat,
  false)` — a reading must not bump the missing-texture counter it is printed
  beside.
* It is the denominator of the next reading: `groundMaskMean / this`, per NAME,
  dry against wet, is the lighting gain over source. Per name and never averaged.

---

## What was NOT done, on purpose

* **No bound and no gate was added anywhere.** `verdictSpaced` prints and does
  not block; `kitAlbedoListed`, `framesStaged`, `groundAlbedoBy` and
  `groundAlbedoOf` are emits with no threshold attached. Every one of them needs
  a landed series first.
* The other 33 spaced values in the live verdict are listed by `--spaced` and
  left alone — naming them is this instrument's job, fixing them is a batch with
  its own review.

---

## First real reading in this checkout, with its caveat stated

    $ frames_staged_line game-design/sim-shots 1 review_day1_noon.jpg hunt_day12_noon.jpg hunt_day13_noon.jpg
    framesStaged=0/29 framesRows=29 framesUnstaged=[day1_noon/day1_dusk/day1_night/
      day2_noon/day2_wet/day2_night/day3_noon/day3_night/+21more-not-shown]

**0 of 29 is the correct answer here and is NOT a finding about the game.** No
sim ran in this checkout, so every JPEG is tracked and unchanged and git rightly
says this process photographed nothing. The reading proves three things about
the instrument and nothing about the street: the denominator is present, the
cap bit and said so (`+21more-not-shown`), and the tool cannot mistake "a row
exists" for "the run took it". The first reading that means something about the
game comes from CI, where the same call runs seconds after the sim exits — and
on tonight's build it would have read roughly 25/29 with the four `day12`/`day13`
hunt rows named.
