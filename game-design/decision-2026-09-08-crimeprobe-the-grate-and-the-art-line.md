# Ruling: CrimeProbe, the grate and the art line. LAND WITH AMENDMENTS, DISPATCH IN TWO PUSHES, PULL THE PREVIEW OUT

> **STATUS: LIVE, verified 2026-09-08.** A reference, not a plan: a ruling
> read clause by clause by the resident and the next builder, so the
> scannability cap does not apply. Director ruling at spawn
> 2026-09-08T19:06:52Z (`.claude/agent-log.tsv` line 374) on the uncommitted
> four-strand batch over `6e16c321`, the newest commit in `.git/logs/HEAD`
> (line 514, 2026-09-08T18:15:47Z). Escalated because CrimeProbe is a
> SIMULATION change and `director_cadence` refuses the commit without this.

VERDICT: LAND WITH AMENDMENTS. Strand 1 lands with two dictated lines and
three findings carried to the next run. Strand 2's rewrite is true in every
instrument claim and overstates one fact about his engine; its replacement
instrument is right and has one hole in the caller, which BLOCKS the mesh
import dispatch and nothing else. Strand 3 is complete for its workflow and
one other workflow has the same shape. Strand 4's recipe is right to print
the conflict; the attribution row's wording is true today and its PATH is
wider than its claim. The push is split in two and the preview render is
pulled out of both.

## 0. What was read, what was not run

THIS SEAT HAS NO SHELL. Read, Glob and Grep only. So the two selftests were
NOT run here, whatever the brief assumed. What I can say about them:

- `crimeSelftestChecks=57`: I counted the `Expect` calls in
  `CrimeProbe.h` `Selftest()` from the source: 12 (accepting case) + 7
  (occluded case) + 3 (seed) + 9 (bank scanner) + 4 (value rules) + 16
  (eight shards, two checks each) + 6 (combined readings) = 57. The count
  agrees with the brief. Whether they PASS is the resident's `g++` line and
  the verdict's own `crimeSelftestFailed=` key on the machine; I did not
  reproduce it and this record does not claim it.
- I re-did the accepting case's arithmetic by hand from the constants in
  the header, since that I can do: actor 2.275 m (prints 2.28), victim
  2.150 m (2.15), victim off-axis 28.2 degrees, face angle 69.4 degrees.
  All four agree with the `Expect` strings, so the fixture is the ruling's
  geometry and not a number typed to pass.
- `run-recipe.py --selftest` 45/45: unrun here for the same reason.

Read whole: `CrimeProbe.h` (957), `CrimeProbe.cpp` (1514), the crime ruling,
`ledger-mesh-import.yml`, `ledger-art-blender-preview.yml`,
`quay-street-mickeys-walk.py`, `production/findings.txt`, D15. Read by the
lines cited: `VignetteShot.cpp` 588 to 969 and 2420 to 2494, `Gossip.h`
221 to 235, 394 to 408 and 525 to 604, `Perception.cpp` 1 to 80,
`import_prop_meshes.py` 545 to 569, 826 to 907 and 1040 to 1084,
`attribution-check.py` 150 to 196 and 440 to 513, `run-recipe.py` 300 to
480, `clip-from-frames.py` by grep, every workflow by grep for `runs-on`,
`git rev-parse`, `safe.directory`, `set +e` and `GITHUB_SHA`.

## 1. Strand 1, the crime

### 1.1 The engine's numbers against the ruling's: the right way round

YES, and the crime ruling already says so about itself. Its section 0 reads
"Rule 2: the instrument prints every one; none is trusted from this page",
and section 2 ends "A disagreement between prediction and print is the
finding." The verdict prints the ruling's arithmetic under its own name,
`crimePrediction=... crimePredictionSource=ruling-section-2/hand-arithmetic-not-a-measurement`
(CrimeProbe.cpp 980 to 984), so the run is read AGAINST it, never required
to equal it.

The two specific numbers, checked rather than taken:

- `pairMetres` 19.2 not 19.1. P1 (9.0, 4.7) to PN (22.5, -8.9): dx 13.5,
  dz 13.6, root of 367.21 is 19.163, and `F1` prints 19.2. The ruling's
  19.1 was a truncation of the same arithmetic. The bodies' centres differ
  in height by about a centimetre (footway at about 0.09 against the yard
  floor's top at 0.10), which does not reach the first decimal.
- `summariesSayingPlayer=0/2-rumours` not `/1`. `SummariesDenominator`
  (CrimeProbe.cpp 904 to 916) sums `Rumors.size()` over every agent, and
  `Tick` pushes a NEW `Rumor` onto the listener (Gossip.h 581 to 585), so
  after round 2 there are two rumour objects in the mill. `SummariesSaying`
  (Gossip.h 394 to 408) walks the same set, so numerator and denominator
  are one fraction over one population and not two numbers from one
  variable. The bank's 24 lines contain the word "player" nowhere (read
  lines 12 to 35 of the bank), so 0 is the expected numerator.

No edit to the crime ruling. This record is the correction; its sections 4.5
and 4.6 stay as the prediction they were.

### 1.2 Round 1 between crime A and crime B: it changes nothing the pair proves

The not-together case is reachable only there: once W1 is on the yard floor
for crime B she is 1.4 m from N2 for the rest of the run. Read against the
ported `Tick` (Gossip.h 525 to 604): the not-together path is a `continue`
at line 549 BEFORE the speaker's held rumours are touched, so round 1
mutates nothing; `GNow` is D1 12:00 for both rounds and nothing in the
ported lines reads time; the rumour set between the rounds changes only if
W1 files on crime B, and `GossipStatus` demands `Passed == 1` (CrimeProbe.h
797) so a blind witness who filed would print NOT-PROVEN on the gossip
reading at the same moment `WitnessStatus` prints it, which is the coupling
wanted. What the pair proves is exactly what section 3 planted: the same
two people, the same rumour, the same tie, and only `together` differing.

What it does NOT prove, said so nobody reads more into it: anything about
time. Both rounds are one game minute, and the rule-5b pair here is over
distance alone.

### 1.3 Two seconds walked, then a teleport: honest, with two corrections

The method is within the ruling (section 2, "teleported as the walk
teleports") and the two seconds of movement are the builder's addition for
the clip and for `SecondsWatching`. Two things the brief says that the tree
does not bear out:

- "Both the walked distance and the final position are printed." THE WALKED
  DISTANCE IS NOT PRINTED. A grep of `CrimeProbe.cpp` for `walked`,
  `approachWalked` and `approachM` returns nothing; the positions on the
  verdict are the six `crimeShotAtXYZcm` and the two `actorAtXYZcm`. The
  displacement from S to C_A is bounded by the `start` and
  `before_crime_a` shot positions, but the walked-versus-teleported split
  is unmeasured. It matters more than it looks: the pawn takes movement
  input only while no sequence frame is in flight (CrimeProbe.cpp 1258,
  `!GSeqInFlight`), so with a capture every 0.4 s and a file-settle wait
  inside each, the walked part may be well under the 4 m the comment at
  line 107 estimates.
- The keys file cannot see the cut. `GBeat` stays `approach_a` through
  `PlaceForA` and `SettleA` (it changes only at 1257 and 1305), so every
  frame after the teleport still claims to be the approach.

RULED: acceptable for run 1, with A1 applied before dispatch and A2 on the
next builder pass. Section 5's viewer sees the start, some movement, a cut
to the window, the window gone in the next frame, and the words in the
yard. A cut is what 0.4 s sampling makes of a teleport and the deed itself
is already a cut by ruling; the clip stays honest as long as nothing calls
the approach a walk, and the verdict does not.

### 1.4 `probePiecesMaterialBound=0/21`: accepted for this run, with the next rung named

The reason printed is true: `BindSurfaces()` runs inside `BuildScene`
(VignetteShot.cpp 969) over `GSpec.Pieces`, and `PlaceProps` runs from the
ticker later (CrimeProbe.cpp 1241), so the yard floor, both bodies, sixteen
shards and two bricks carry the basic shape's default material. The 21 is
the ASKED count (`GProbePiecesAsked = 1 + 2 + 16 + 2`, line 1099) and the
line says so by its denominator. Not misleading: the ruling accepted
cylinder stand-ins in words, `castBodies=cylinder-stand-in/no-mixamo-body-in-ue-probe`
is on the verdict, and a grey cylinder on a textured street reads as what
it is. The next rung is small and named in section 6.

### 1.5 `Perception::LoudRemark` has no caller: no change

It is a ported constant with a golden row (`CoreGolden.h` 659,
`perception-golden.txt` 1230), which is the whole of what section 1 of the
crime ruling asked of it. Rule 6 is about features that claim to run; a
constant proven equal across engines is not one. The overheard beat uses
6 m earshot to both speakers because the ruling named that rule
(GossipDirector.cs 247, 577 to 578) and not `LoudRemark`.

### 1.6 Three findings the brief did not ask about

F1. A TYPED NUMBER IN THE LAYER THAT SAYS IT HAS NONE. `1.4` is passed as
`SubjectSpeed` to `InSight` at CrimeProbe.h 408 and 410 and CrimeProbe.cpp
680. It is not from the C# (`WalkSpeed` is 4.0, Perception.h 30), it is not
printed, and the header's section on placements says "every one is the
ruling's own number". Measured effect on this run: `InSight` reads the
speed only against `StillBelow` 0.35 in the peripheral band (Perception.cpp
41), and W1 faces the crime point with the pawn about 16 degrees off her
axis at S against an acuity half-angle of 30, so the number is INERT for
this geometry. It is still a typed input where the pawn's velocity is one
call away. A3 covers it.

F2. THE FOUR LADDER ROWS THE CRIME RULING ORDERED ARE ABSENT. Section 7
named them ("Crime", "Witness", "Overheard line", "NPC body"); a grep of
`production/quality-ladder.md` for crime, witness, overheard, mixamo,
stand-in and cylinder finds only the Information-layer row. Dictated in
section 6; documents commit on the resident's read.

F3. THE SEVEN FILED NAMES ARE NOT IN THE QUEUE. The ruling's "FILED, NAMES
NOT WORK" list (yard, StreetVoice.Exchange, Attention, SuspicionTracker,
held body, crowd voice, Arsenal row): a grep of `production/queue/` for
yard, Arsenal, StreetVoice, SuspicionTracker and Perception.Attention hits
only 054, the double-yellows item. Queue 140 to 143 are about other things.
Dictated in section 7.

Checked and clean, so nobody re-checks: `-LedgerCrime` at one site
(LedgerProbe.cpp 815); `SpawnProbePiece` called at CrimeProbe.cpp 554 and
564 only; `GByName.Add` at one site (VignetteShot.cpp 822);
`StreetPieceNameOf` adds to neither map; the `Gossiper` constructor makes
its own `MemoryStore` and `KnowledgeBase` when passed null (Gossip.h 233 to
234), so `Start()`'s two null shared pointers do not crash `Tick`; the
`Witness` call's argument order matches the declaration (Gossip.h 444 to
446); the seed 43 picks index 1 in both contexts, `cw-ws-r3-02` and
`cw-ov-r3-02`, which is the rule and not the ruling's example; the
`heardMemoryImportance` 0.36 is `Clamp(0.4512 * 0.8, 0.2, 0.85)` at
Gossip.h 587; the crime-clip step passes `--frame-keys` and `--bank`
(ledger-probe-unreal.yml 1760) and commits `ue-crime.gif` (1944); every
probe step is `if: always()`, so a DISPATCH push runs the whole 180-minute
job.

## 2. Strand 2, the grate

### 2.1 The rewritten finding: true where it measures, one sentence too far

Verified against the tree, line by line: the run asks
`InterchangeManager.can_translate_source_data()` on three real .glb files
(import_prop_meshes.py 879 to 888, over `asked[:3]` at 996) and does so at
998, BEFORE the import loop begins at 1001; `propGltfCanTranslate=N/M` and
`propGltfImporter` print at 1065 to 1071; the four words are asserted
distinct at 566 to 568; run 1's exact reading is planted at 555 to 559 and
asserted different from the no-plugin case; the runner scan lists plugins
by name, by content and by Interchange name (ledger-mesh-import.yml 200 to
213). All as the finding says.

THE SENTENCE TO SOFTEN: "it ships inside the Interchange plugins,
`InterchangeAssets` and `InterchangeEditor`" is a statement about his 5.8
install that no command has checked, written in the same entry that
records rule 1 being broken on the same file. The true form: the glTF
translator in recent Unreal belongs to the Interchange framework, whose
plugin files need not carry GLTF in the name at all, and WHICH plugin names
his engine has is what `propInterchangePlugins=` prints on run 2. A4a
carries the wording.

### 2.2 The replacement instrument: right, with one hole in the caller

`gltf_verdict` is sound and tested. THE HOLE IS AT 1061 to 1062:

    importer_plugins = [n for n in plugin_names
                        if "GLTF" in n.upper() and "EXPORT" not in n.upper()]

Only a GLTF-named plugin counts as an importer candidate. An engine whose
only importer is Interchange, enabled and refusing the file, therefore
prints `ABSENT/exporter-only`, which is run 1's misreading wearing the new
key. The selftest cannot see it because the filter is inline and untested;
`gltf_verdict(True, ["InterchangeGLTF"], 0, 3)` at 560 tests a list the
caller can never build. A4 is the fix and it BLOCKS THE MESH IMPORT
DISPATCH: the gate pulls `propGltfImporter` to the top of the run's reading
(ledger-mesh-import.yml 382), and a word that can be wrong in the one case
the strand exists to distinguish may not lead.

### 2.3 `-EnablePlugins=`: the right lever

Names only, taken from the disk scan and never typed (ledger-mesh-import.yml
228 to 234); the uproject is read and not written, so the probe's cook is
unchanged; the engine's own answer about what took travels back as
`propGltfPluginsEnabled` from `get_enabled_plugin_names()` (893 to 894),
which is a different fact from a file on disk and the comment says so.
One trim: drop `InterchangeTests` from `$want`. A test plugin buys nothing
here and every plugin is load time on a step already capped at nine
minutes. Non-blocking.

### 2.4 The Blender GLB-to-FBX fallback: correctly not built

Rule 3 (the instrument first) and rule 11 (adjacent work is named, not
done). Until `propGltfCanTranslate` has a reading nobody knows whether a
fallback is needed. Note for whoever builds it: an FBX route re-opens the
axis and scale question the spec-box check closed at 0.0000 mm per axis on
the GLBs, so it needs its own bounds reading against the same spec box.
Queue name in section 7.

## 3. Strand 3, the evidence fault

### 3.1 Complete for `ledger-mesh-import.yml`

Counted from the file, not the brief: TWELVE git invocations on eleven
lines carry `-c safe.directory='*'` (292, 340, 341, 347, 349, 351, 353,
354, 355, 358 twice, 359). The brief's "nine" is wrong by count and right
in substance: every one carries it. Both bash steps also carry the
`GIT_CONFIG_COUNT/KEY_0/VALUE_0` triple (277 to 279, 332 to 334). The
verdict step is `set +e` with the reason in words (281 to 285), the sha
falls back to `${GITHUB_SHA}` and prints `shaFrom=` (292 to 300), the file
is written on every path and re-checked for emptiness (316 to 318), and the
gate reads the file rather than the exit code. One cosmetic: the fallback
inside `MSG` at 354 escapes its quotes, so a git-refused run would commit
as `mesh import from "abc1234"` with the quotes in the message. Harmless;
tidy when the file is next open.

### 3.2 The same shape elsewhere: one workflow

Nine workflows run on the self-hosted runner (grep `runs-on`: setup-msvc,
build-windows, probe-unreal, art-blender-preview, imagegen, mesh-import,
restart-telegram-bot, install-supervisor-task, vignette-fetch). Eight carry
the env triple on their bash git steps (setup-msvc 268, build-windows 579,
probe-unreal 1802, imagegen 320 and 471, restart-telegram-bot 238,
install-supervisor-task 554 and 586, vignette-fetch 144), and the pwsh git
calls I found in install-supervisor-task carry `-c safe.directory=*`
inline (217, 458).

ONE DOES NOT: `ledger-art-blender-preview.yml`, the commit step at 168 to
183. A bash step, on `[self-hosted, windows]`, six plain git calls, no env
triple, no `-c`, and no evidence file at all: its only channel is the push
to the art branch. Its first git call (`git config user.name`, 170) would
die on dubious ownership under the shell's default `-e`, and the render
just made would be lost with no committed word about it. Its
`git add -A -- ...*.png 2>/dev/null || true` at 174 would also hide the
same error if `config` had not died first. A5 names the fix; it is NOT this
batch (section 5).

## 4. Strand 4, the art line

### 4.1 `bayHintConflict=`: the recipe is right to print and not resolve

The conflict is real and I read it off the piece file rather than the
recipe's claim. Glazing centres sit at x 6.869 + 6n, so
`decal_00_fascia_mickeys` at x 6 is bay 0 (vignette-pieces.json 512) and
`decal_05_interior_bar_back` at x 18 is bay 2 (517), where
`decal_02_fascia_ritas_pawn` also sits at x 18 (514). A pawnbroker's window
with a bar back behind it. The placement comes from
`production/specs/vignette-scene.json` 577 to 580, which is this studio's
own authoring. D15's amendment of 2026-09-08 (option C, Mickey's never
moved, the built street is Quay Street in the Hook) leaves WHICH BAY "a
small authored choice" and does not decide it, so the recipe deciding it
would have been a session inventing canon. Printing the default and where
it came from (`bayDefaultFrom=fascia-decal/...`) is the correct shape.

RULED: a card to Jafar through the Producer, two options, default A:

- A. Bay 0 is Mickey's, where the lettering already is. The bar-back card
  moves from x 18 to x 6 and the shop-shelves card from x 6 to x 18, two
  fields in `vignette-scene.json`, and the piece list regenerates.
- B. Bay 2 is Mickey's, where the bar back already is. The Mickey's and
  Rita's Pawn fascias swap x.

Recommendation A: a fascia is what a player reads from the street and what
the crime's witness names; the interior card is a generated 768x512 image
that moves by one field. Until he rules, the recipe's default of bay 0
stands and says so on every run. Not this batch.

### 4.2 The `production/art` attribution row: true today, and its path is wider than its claim

THE CLAIM: "Blender previews of this project's own piece list, rendered by
a recipe under tools/art-recipes from primitives plus allowlisted props
that carry their own attribution." Checked: the recipe's surfaces are
greys from `SURFACE_GREY` with one colour from the file; the props are the
.glb files under `ledger/Assets/Props/base-mesh`, which
`ledger/Assets/Props/base-mesh/THIRD-PARTY.md` records as CC0 1.0 from The
Base Mesh; `_add_mesh` keeps whatever material the GLB carries, and CC0
base meshes are untextured. So the row is true for a preview rendered
today.

WHAT WOULD MAKE IT FALSE, three things, and the comment names one:

1. A recipe that binds fetched textures. Named in the comment. Right.
2. A recipe that imports from anywhere but base-mesh. `MESH_DIR_REL` is
   fixed at line 66 today; a change there, or a piece file naming an asset
   under `oga-vehicles` (a different licence, attributed on the other side
   of the check), is the trigger. Not named. Add it.
3. THE ONE THAT WILL HAPPEN FIRST: the row's key is `production/art` and
   the check matches by prefix (`under()`, attribution-check.py 448 and
   478). `tools/art-deliveries.py` line 31 puts an outside artist's
   delivery under `production/art/<commission>/DELIVERY.md`, in the same
   tree. The first delivered paint-over PNG is classified "ours" by this
   row and never asked for a licence. A licensing row that says a picture
   is ours when a human outside the studio drew it is the exact decayed
   claim the 7 September correction on `production/d1-probe` was about.

Also the comment's "contains no third-party pixel at all" overstates: the
sixteen CC0 meshes are outside geometry, attributed anyway. Say "no
third-party texture; the only outside content is CC0 geometry, attributed
in ledger/Assets/Props/base-mesh/THIRD-PARTY.md". A6 carries the wording;
the path fix is a tool change and goes to the queue by name.

## 5. Dispatch: two pushes, and the preview comes out

The brief says one push fires a crime run, a mesh import and a preview
render. In the tree I read, `production/d1-probe/DISPATCH` has no crime
line yet, `production/pc-ops/mesh-import.request` still reads run 1's line
(`reason=pilot-package-one-the-drainage-grate date=2026-09-08`), and
`production/pc-ops/art-preview.request` does not exist. So the three
dispatches are a proposal and not yet a fact, which is the right order.

RULED:

1. PUSH ONE: THE CRIME RUN. After A1 (two dictated lines) and the resident's
   prints in section 8. Append the run 26 line to `DISPATCH`, capture the
   sha BEFORE pushing, watch by ancestry. First reads, in this order and
   before any message: `crimeSelftestFailed`, `launchStatus`,
   `witnessStatus`, `gossipStatus`, `overheardStatus`, then all six stills
   opened and the GIF played, then the numbers beside each word.
2. PUSH TWO: THE MESH IMPORT, after A4 lands, in its own commit. Two
   reasons and either suffices. The runner is ONE machine and the probe job
   holds it for up to 180 minutes, so the two evidence files would land
   hours apart and be read as one batch; and A4 blocks the word the gate
   puts first. Ancestry, not order, decides which run a uasset belongs to:
   if the import lands before the probe starts, the probe checks out the
   tip and cooks the props, which is fine and is said here so nobody reads
   it as drift.
3. THE PREVIEW RENDER IS PULLED OUT OF BOTH. Do not add
   `art-preview.request` in this batch; if a builder added it, remove it.
   Three reasons: the job yields to any running game workflow by design
   (ledger-art-blender-preview.yml 86 to 124), so fired beside a crime run
   it loses its run for certain; its commit step has the run-1 fault
   (section 3.2) and would lose the render even if it ran; and it checks
   out `art/<commission>` (130), a branch no ref in this clone names.
   Dispatch it alone, after A5, when no game job is running.

ON "NO FURTHER CHANNEL WORK THIS WEEK". The sentence is in no file I can
read; `production/decision-queue.md` and `production/inbox/` carry no such
ruling and the nearest recorded form is `production/findings.txt` line 189,
Jafar's "no process work beyond what is listed here". Ruling on that
wording: the mesh-import workflow fix is the one exception rule 12 makes,
a blocked evidence channel is the highest-leverage bug on the board, it was
the minimum needed to READ a game run, and it ships. The art-preview fix is
process work on the line Jafar put lowest on 2026-09-08 (the yml header)
and it waits in the queue. The resident records his exact words and their
date under RULED THIS WEEK in `production/decision-queue.md` so the next
director rules on a sentence and not on a paraphrase.

## 6. The quality ladder at close

Best available or first working? Strand 1 is the first working and says so
in its own verdict keys; the rungs above it are named and none is blank.
Rows for `production/quality-ladder.md`, dictated, resident's read:

| aspect | current rung | next rung, from resources we have |
|---|---|---|
| Crime (the deed) | A hidden glass piece with collision off, read back after the call; eight shard boxes and a brick box on traced ground; a forced sequence frame either side so the break reads as a cut. | A projectile that crosses the frames and a break sound in a clip format that carries sound; `Observe.DeedFor` over an `Arsenal` row for a half-brick so the `Deed` is the game's and not hand-built. |
| Witness (the decision) | `Observe.Resolve` on two real line traces, the actor's own bounds and an accumulated watching time; the vantage read before the deed with the glass standing; the pawn's speed a typed 1.4. | `Perception.Attention` ported so `SecondsWatching` and `RungFloor` come from the accumulator; the pawn's measured velocity in place of the typed speed; the walked and teleported halves of the approach printed. |
| Overheard line | A bank pick at the achieved rung, seeded `Day*31+Hour`, burnt as a caption on the heard frames. | `StreetVoice.Exchange` ported so the reply is composed from what was actually carried; a crowd voice by `VoiceBank` hash. |
| NPC body | A 0.4 by 1.75 m cylinder carrying the engine's default material, moved by its own transform. | The surface bound at spawn through the material instances `BindSurfaces` already made; then a held Mixamo body with an idle (queue 028). |

## 7. Filed, names not work

Queue files, numbered from the next free (140 to 143 exist), in the shape
of 143 (line, spec, acceptance, max_sessions, status), resident's read:

- 144 `the-street-owes-a-yard-behind-the-west-crossover`: ground_plot_2 ends
  at x 21 and ground_plot_3 starts at x 24; the crime probe spawns its own
  floor there and prints `probeFloorNote=` so the street owns it next.
- 145 `bind-a-surface-on-a-probe-piece`: an export that binds a surface's
  existing material instance to an actor spawned after `BuildScene`, so
  `probePiecesMaterialBound` can read 21/21.
- 146 `the-probes-typed-speed-and-the-approach-split`: A2 and A3 together,
  since both are the same file and the same verdict line.
- 147 `port-streetvoice-exchange-so-the-reply-is-composed`.
- 148 `port-perception-attention-so-watching-comes-from-the-accumulator`.
- 149 `port-suspiciontracker-and-consequences-one-and-two`.
- 150 `a-crowd-voice-by-voicebank-hash-and-a-clip-format-with-sound`.
- 151 `an-arsenal-row-for-a-half-brick-so-deedfor-replaces-the-hand-built-deed`.
- 152 `art-preview-commit-step-dies-on-dubious-ownership`: A5, with the
  `2>/dev/null || true` at 174 named as the second silence.
- 153 `the-production-art-row-absorbs-deliveries`: under `production/art`,
  only `*/previews/` is ours; a delivery is somebody's and is classified by
  its own row; the check learns the shape rather than a list.
- 154 `blender-glb-to-fbx-fallback-for-the-prop-import`: BLOCKED on a
  reading of `propGltfCanTranslate`; carries the axis and scale note from
  section 2.4.
- The held body is queue 028 already, per the crime ruling; no new file.

And one card, not a queue item: section 4.1, which bay is Mickey's, through
the Producer with the two options and the default.

## 8. Before the commit the resident prints

1. `grep -n "GBeat = \"at_window" ue-probe/Source/LedgerProbe/Private/CrimeProbe.cpp`:
   two hits, one in `PlaceForA` and one in `PlaceForB` (A1).
2. The `g++ -std=c++11 -Wall -Wextra` line over `CrimeProbe.h` and its
   selftest, with `crimeSelftestChecks=57 crimeSelftestFailed=0/57` FROM
   THE OUTPUT, since this record did not run it.
3. `python3 tools/ue/import_prop_meshes.py --selftest`: the count, with
   the two new rows from A4 named in it, exit 0.
4. `python3 tools/art-recipes/run-recipe.py --selftest`: 45 of 45 or the
   new count, exit 0.
5. `python3 tools/attribution-check.py`: the `ours production/art:` line
   with the A6 wording, exit 0.
6. `grep -rn "InterchangeAssets" production/findings.txt`: zero hits after
   A4a, or the softened sentence only.
7. `ls production/pc-ops/`: no `art-preview.request`.
8. `python3 tools/docs-check.py` clean on this record.
9. `python3 ledger/verify.py`, footer FROM `ledger/.verify-footer`; the
   cadence line names this record and row `2026-09-08T19:06:52Z`.
10. The sha captured BEFORE the DISPATCH push; the run watched by ancestry;
    the verdict opened and every `*Status` word read beside its number and
    every still opened before any message is written.

## 9. The amendments, in one place

- A1, BEFORE DISPATCH, dictated, two lines in `CrimeProbe.cpp`: in
  `case ECrimePhase::PlaceForA` add `GBeat = "at_window_a";` before the
  `TeleportPawn` call at 1272, and in `case ECrimePhase::PlaceForB` add
  `GBeat = "at_window_b";` before the call at 1356. `clip-from-frames.py`
  reads only `heard` and `lineId` from a keys row (212 to 221), so a new
  beat name changes no caption and no selftest.
- A2, NEXT BUILDER PASS on the probe: per crime, print `approachWalkedM=`,
  `approachTeleportedM=` and `approachWalkSeconds=` from the pawn's
  location at the start of the approach, at its end and after the
  teleport.
- A3, NEXT BUILDER PASS, same file: the pawn's measured velocity in place
  of the literal 1.4 at CrimeProbe.h 408 and 410 and CrimeProbe.cpp 680,
  printed on the witness line as `subjectSpeedMps=`; until then the
  literal is named once as a constant with `typed-not-measured` beside it.
- A4, BLOCKS PUSH TWO, builder, `tools/ue/import_prop_meshes.py`: a pure
  `importer_candidates(names)` returning the names containing GLTF or
  INTERCHANGE and not EXPORT, used at 1061; two selftest rows, accepting
  first: `["GLTFExporter", "InterchangeEditor"]` yields one candidate;
  `["GLTFExporter"]` yields none. Drop `InterchangeTests` from `$want` in
  the workflow in the same change.
- A4a, dictated, `production/findings.txt`: replace "In modern Unreal the
  glTF IMPORTER does not live in a plugin whose filename contains GLTF at
  all: it ships inside the Interchange plugins, `InterchangeAssets` and
  `InterchangeEditor`." with "In recent Unreal the glTF translator belongs
  to the Interchange framework, whose plugin files need not carry GLTF in
  the name at all; which plugin names his 5.8 install actually has is what
  `propInterchangePlugins=` prints on run 2."
- A5, QUEUE 152, not this batch: the env triple and `-c safe.directory='*'`
  on every git call in `ledger-art-blender-preview.yml` 168 to 183, and
  the `2>/dev/null || true` at 174 replaced by a named refusal.
- A6, dictated, `tools/attribution-check.py` line 179 value: "Blender
  previews only, under production/art/*/previews: renders of this
  project's own piece list by a recipe under tools/art-recipes, greys from
  the recipe plus the CC0 base meshes attributed in
  ledger/Assets/Props/base-mesh/THIRD-PARTY.md; a DELIVERY under the same
  commission is somebody's and is not covered by this row". And in the
  comment above it, "contains no third-party pixel at all" becomes "carries
  no third-party texture; the only outside content is CC0 geometry,
  attributed", plus the second trigger: a recipe importing from anywhere
  but base-mesh.

Nothing in this batch weakens an instrument, moves a bound, or was
concluded from a number nobody printed; where this record could not print
one (the two selftests), it says so and names who does.

<!--RULING spawn=2026-09-08T19:06:52Z-->
