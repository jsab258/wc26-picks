# Ruling: the lookup that lied, and the art line in-house. LAND WITH AMENDMENTS; RUN 3 WAITS FOR SIX SMALL ONES

> STATUS: LIVE, verified 2026-09-08. A reference, not a plan: a ruling read
> clause by clause by the resident and the next builder, so the scannability
> cap does not apply. Director ruling at spawn 2026-09-08T21:38:35Z
> (`.claude/agent-log.tsv` line 381) on the uncommitted batch over
> `b5a5d019`, the newest commit in `.git/logs/HEAD` (line 525, a fast-forward
> from origin at 1788901311, which is 2026-09-08T21:01:51Z). The batch touches
> `tools/` and `.claude/`, both in `DIRECTOR_WORK` (verify.py 2791, 2799).

VERDICT: LAND WITH AMENDMENTS. Strand 1's reconciliation is sound about the
INSTRUMENT and not yet about the ENGINE, and the new instrument has five holes
that would each turn a healthy run 3 into a false reading; the code lands now
and the run 3 dispatch waits for a builder pass of six named changes, none
larger than a screen. Strand 2's research is honest where it is labelled and
unlabelled where it is most confident; the delivery lands with one wrong
location corrected, one wrong consequence relabelled, and the new agent brief
brought back to two rulings it contradicts (Jafar's tier model, canon on
CCTV). Both card defaults stand; Card 2 must say which shop it moves.

## 0. What was read, what was not run

THIS SEAT HAS NO SHELL. Read, Glob, Grep and WebSearch only, whatever the
brief assumed. So:

- `import_prop_meshes.py --selftest` was NOT run here. I counted the new
  rows from the source: section E2 has 7 `ok(` calls (lines 770 to 796), E3
  has 6 (802 to 829), and section G gained 1 (880 to 883); 67 + 14 = 81,
  which agrees with the brief. Whether they PASS is the resident's print.
- `tools/canon-gate.py` was NOT run here. I did what the gate does by hand:
  one ripgrep over `production/art/atlas-02/` for the gate's 13 era terms
  (canon-gate.py 39 to 53) and the 45 brand tokens in
  `tools/imagegen/prompts.json` 69 to 113, word-bounded, case-insensitive,
  which is the gate's own regex shape (canon-gate.py 105 and 120). ZERO hits
  over 6 files and 1342 lines (334 + 216 + 210 + 179 + 182 + 221). That is a
  prediction of the gate's answer, not the gate's answer.
- Three outside checks by WebSearch, each a search-channel summary and named
  as such where used: the 1994 amendment to the spirits Order (section 2.2),
  the shape `EditorAssetLibrary.list_assets` returns (section 1.2, H1), and
  what blocks on an asynchronous `AssetImportTask` (section 1.2, H6).

Read whole: `import_prop_meshes.py` (1553 lines), `ue-mesh-import.txt`,
queue 154, `world-designer.md`, `canon-gate.py`, all five research files,
`DELIVERY.md`, `D14`, the previous ruling. Read by the lines cited:
`ledger-mesh-import.yml` 177, 228 to 234, 255 to 257, 345 to 359, 374 to
400; `vignette-pieces.json` 489, 512 to 531; `vignette-scene.json` 35 to
172; `canon.md` 10 to 11, 34, 47 to 48; `organization.md` 37 to 62;
`log-agent.sh`; `agent-turns.tsv` 95 to 98; `decision-queue.md` 1 to 125;
`art-collaboration.md` 1 to 65; `ue-mesh-import.json` by grep (`reportLines`
is `[]` at line 139).

## 1. Strand 1, the mesh import

### 1.1 The reconciliation: sound about the ruler, open about the engine

The three facts are `propGltfCanTranslate=3/3`, `propImportVia=none-of-2-
candidates` with `propImported=0/16`, and `propNote=none` (the manifest's
`reportLines` is empty, so nothing was appended by any `except`). The
builder's reading, verified against the code: `_try` (907 to 921) returns
`(None, none-of-N)` when every route RETURNS None, and appends to `report`
only when a route RAISES. A route ending in `load_asset(path)` returns None
for a path that does not resolve, without raising. So the three facts are
exactly what a route that ran and then failed its own lookup would print.
SOUND, and the fault is the instrument's: it could not tell "made nothing"
from "made something I did not look for".

What ELSE fits the same three facts, said so run 3 is read against all of
them and not against the builder's favourite:

1. The import made an asset under a name or folder other than
   `/Game/Ledger/Props/SM_<asset>` (the builder's hypothesis).
2. The import made NOTHING and logged rather than raised. A commandlet
   import that fails inside the engine writes to the log; the Python call
   returns normally. Same three facts.
3. The import is asynchronous and completed after the lookup (the
   director's first shape from the previous batch). Same three facts.

`propUassetsOnDisk=0` (verdict line 14) discriminates none of these: the
task carried `save=False` and nothing loaded, so nothing was ever saved.

RULED: the reconciliation stands as a diagnosis of run 2's instrument. The
sentence in the brief, "a route that ran, translated and imported reported
itself as REFUSED", is one word too strong: "imported" is the hypothesis
run 3 exists to test. Queue 154's own wording (lines 24 to 28, "raised
nothing while the asset did not load at the expected path, which is now
measured rather than inferred") is the correct form and is the one the
record keeps. A6 puts the correction beside run 1's in `findings.txt`,
because that is where the first wrong reading lives and a correction that
lives in a queue file's status line is not beside the claim it corrects.

### 1.2 The fix: right shape, five holes that each make a healthy run read red

The four moves are right and verified: `_import_one` (1191 to 1299) runs its
own loop and records `routeRan` before any lookup (1261); `via_task` reads
`imported_object_paths` (1224 to 1228); `before` and `after` snapshots make
`new` the measurement (1210, 1264 to 1265); `import_asset_with_result` is
tried ahead of `import_asset` (1251 to 1253). Then, from reading rather
than running:

H1. THE SNAPSHOT'S SHAPE IS UNCHECKED AND THE RESOLVER ASSUMES IT.
`resolve_imported` compares each entry to `PACKAGE_DIR/SM_x` (1122, 1129).
`_list_package` takes `EditorAssetLibrary.list_assets` first (1153 to 1155)
and the registry's `package_name` second (1157 to 1160). The second is a
package name. The first: the search-channel summary of the Python API page
says package names (`/Game/Folder/Asset`); my own recollection of 5.x is
object paths (`/Game/Folder/Asset.Asset`). Two sources disagree and neither
is a run. If the object-path shape comes back, a PERFECT import at the exact
path fails `exact-path` (the string differs), fails
`exact-name-different-folder` (`SM_X.SM_X` is not `SM_X`), and is caught by
`name-contains-the-asset-id`, whose docstring (405 to 408) says that reading
"means the import worked and run 2's lookup was the entire fault". A healthy
run would then print a conclusion about run 2 that the run did not measure.
Fix in A1: normalise every snapshot entry by dropping a `.Name` suffix
before comparing, print the first raw entry as
`propImportSnapshotShape=<entry>` so run 3 says which shape this engine
returns, and plant BOTH shapes in E2 as accepting rows that resolve
`exact-path`.

H2. A SIBLING PACKAGE THAT SORTS FIRST ENDS THE ASSET. `new` is sorted
(1265). `name-contains-the-asset-id` takes the FIRST leaf containing the id
(1134 to 1136). A glTF import through the generic pipeline can make a
material or texture package beside the mesh, and one named after the same
file sorts before `SM_` at the letter M. That leaf loads as a non-StaticMesh,
`isinstance` fails (1291), and the function RETURNS (1296) rather than trying
the next leaf. A mesh that imported perfectly beside its own material would
be recorded `loaded-as-MaterialInstanceConstant` and counted as failed. Fix
in A1: load every entry in `new`, keep the StaticMesh ones, resolve among
those, and carry the classes that appeared per asset in the manifest.

H3. THE SECOND SUCCESSFUL RUN READS AS TOTAL FAILURE. The workflow stages
`ue-probe/Content/Ledger/Props/SM_*.uasset` by name and commits them (353),
and `.gitignore` names neither the directory nor the extension. On the first
run after a success, the checkout already holds every `SM_x`; `before`
contains it; `new` is empty even though `replace_existing=True` re-imported
it; every asset reads `nothing-appeared`; the status word is
NOTHING-IMPORTED on an engine that just did the job. Fix in A2: before the
loop, for each asset whose `object_path` loads, delete it and count
`propImportPreexistingDeleted=N/asked`. Rule 5 is satisfied: the deletion is
scoped to the exact paths this script names, on a build product this script
makes, and the workflow stages only files that exist afterwards, so a failed
re-import leaves the committed uassets untouched in git.

H4. THE SAVE IGNORES WHERE THE MESH WAS FOUND. `save_asset(package_path
(asset_id))` (1357) saves the contract path whatever `loadedFrom` says. In
the one world the resolver exists for, the mesh sits elsewhere, the save
fails, `propSaved` stays 0 and the word is PARTIAL with the cause visible
only in the manifest. Fix in A3, and it is a route rather than a bound so it
may ride on a measurement run: when the resolution is
`exact-name-different-folder` or `name-contains-the-asset-id`, rename the
found asset to `package_path(asset_id)` with `EditorAssetLibrary.rename_asset`
BEFORE the save, and count `propImportRenamed=N/asked`. Never under the weak
rule (H5). `propImportResolvedVia` is tallied before the rename, so the
measurement survives the remedy.

H5. `only-package-that-appeared` IS SAFE TO REPORT AND UNSAFE TO COUNT. The
world in which it misattributes is exactly the world the instrument was
built to detect: asset N-1's asynchronous import completing inside asset N's
window. That straggler carries N-1's name, fails every name rule against N,
and is the only package that appeared, so N is credited with N-1's mesh,
`imported` goes up by one, and `bounds_reading` compares N's spec box
against N-1's geometry, which prints as a scale bug in a run where no scale
was wrong. The status word cannot reach IMPORTED that way today (the save at
the contract path fails, H4), but `propImported` would be a wrong number on
the line. RULED: the rule stays as a label; an asset resolved by it alone is
a FAILURE `appeared-unnamed/<leaf>` and is tallied under
`propImportAppearedUnnamed=N/asked`; its bounds are still read and written
to the manifest under the leaf's own name, never under the asset's.
Discriminator, not hedge, once it cannot count.

H6. `propImportWaitChanged=0` IS SILENCE, NOT A RULE-OUT. Both waits in
`_wait_for_registry` (1177 to 1184) are registry scans of what is already on
disk or already registered; neither spans an asynchronous Interchange import,
and `wait_for_completion` returns at once when the initial scan is done, so
`waitTaken` will read N/N on any run where a route made nothing. Above zero
is real evidence (something appeared during a delay). Zero says the registry
did not learn anything during a scan that waited for nothing. The verdict
token itself overclaims: `propImportWaitMeans=above-zero-is-an-async-import/
zero-rules-it-out` (446), and so does the docstring at 415 to 416 and the E3
comment at 817. A0 corrects the words tonight. The wait that DOES span the
import, per the AssetImportTask documentation as summarised by the search
channel: "if the import was asynchronous, this will block until the results
are ready", said of the task's get-objects call, with an is-async-import-
complete query beside it. A1 uses both, guarded by `hasattr` and printing
whether each exists, so run 3 prints the task's own word on whether it was
asynchronous. For the Interchange routes, `via_interchange_result` discards
the return value (1240 to 1241), which is the one handle that API offers;
A1 keeps it and prints its type and any attribute whose name contains
`wait`, `done` or `complete`, calling a `wait_until_done` if one exists.

H7, minor, wording only: `propImportRouteRan` is LAST-WINS over the routes
(`routeRan` is overwritten per route, 1261) and `appeared` is cumulative over
routes (`before_set` is taken once, 1211). Say so in the docstring; the key
name stays because the workflow greps it (389 to 392).

### 1.3 Selftest

81 by count, unrun here. A0 changes no counted row (the E3 checks assert on
the Taken and Changed keys, not on the Means token). A1, A2 and A5 add rows:
two snapshot shapes resolving `exact-path`; a material package beside the
mesh resolving to the mesh; the pre-existing case; and the weak rule's
existing row (784 to 787) re-expected so the rule is named and the asset is
not counted. The resident prints the new count with exit 0 (section 5).

### 1.4 Queue 154, DEAD: stands

The item's own condition ("if the engine cannot translate glTF headlessly")
was refuted by `propGltfCanTranslate=3/3`. One caveat, recorded so the item
is not revived for the wrong reason: if run 3 prints `nothing-appeared=16`
beside `3/3`, the fault is the commandlet's import path and not the format,
and an FBX would take the same path through the same AssetTools. The next
item in that world is about the invocation, not Blender.

### 1.5 Dispatch and reading order

The code lands now; the dispatch of run 3 waits for A1 to A5 in a second
commit. Alone on the runner, as the previous ruling said. Read in this
order, before any message: `propImportStatus`, `propImportResolvedVia`,
`propImportedNames`, `propImportSnapshotShape`, `propImportTaskAsync`,
`propImportPreexistingDeleted`, `propImportRenamed`,
`propImportAppearedUnnamed`, `propImportWaitChanged`, `propAcceptingCase`,
then `propBoundsWorstMm` and the manifest opened. NO BOUND is set from run
3: it prints the engine-versus-spec series for the first time (rule 2), and
the next ruling sets the number from it.

## 2. Strand 2, the art line in-house

### 2.1 Who made it, and the brief that has never run

`.claude/agent-log.tsv` is appended by the SubagentStart hook from
`agent_type` (log-agent.sh 38). It has NO `world-designer` row. The rows in
the window are `content-wrangler` at 21:00:50Z (378) and 21:24:50Z (380),
and `agent-turns.tsv` 98 records a content-wrangler on opus, 49 turns,
stopped 21:26:27Z. So atlas-02 was delivered by a content-wrangler, which
has Bash (content-wrangler.md 4) and could run the gate its delivery says it
ran. `art-collaboration.md` line 59, "staffed by the world-designer role",
is not true yet, and the brief itself is a definition with zero spawns
(rule 6). Corrections dictated in A7:

- `model: sonnet` (world-designer.md 5). Jafar, 24 Aug: "Tier 2 and 3
  should be opus" (organization.md 41 to 42). The 5 September ruling counted
  "sonnet 1" (dialogue-writer) and ruled nothing on it. DEFAULT `opus`,
  which is his ruling applied; a DECISION card offers sonnet for
  research-only commissions if he wants the spend saved. A default that
  runs overnight is a decision, and the one on record is his.
- `tools:` carries no Bash, and the delivery convention requires
  `canon-gate.py over what you wrote` (dispatch.md 12). Without a shell the
  designer can only claim the gate. Add Bash.
- "No mobiles, no internet, no CCTV" (33) contradicts canon line 34, "CCTV
  rare: the bank and the off-licence, tape recycled weekly". The brief that
  says canon outranks it may not misquote canon. Use canon's words.
- "SEPARATE CHECKOUT" (49 to 52; art-collaboration.md 20) cannot be true of
  an in-house spawn. Add the in-house clause: the designer writes only under
  `production/art/<commission>/` in the studio checkout, and the resident
  prints `git status --porcelain` before committing to prove the do-not-touch
  list held. That is the one command DELIVERY.md 58 says exists.

### 2.2 The labels: honest where present, absent where most confident

Sampled and checked:

- Every CITED (project file) number in the pub file (51 to 57) is in
  `vignette-scene.json`: bay 6.0 and depth 8.0 (92 to 93), storeys 3.40 and
  2.80 (94), footway 2.0 (77 to 81), kerb 0.125 (49 to 50), channel 0.255
  (43), pitch 35 (99), eaves 6.30 (104), threshold +0.100 (81), stallriser
  0.60 (153), transom 2.40 (157), fascia bottom 2.85 (159), shop door 0.900
  by 2.040 (165 to 166), side door 0.838 by 1.981 (171 to 172). All
  fourteen agree.
- The firkin: 9 gal x 4.54609 = 40.915 L; x 1.01 = 41.3 kg; 75 lb = 34.0
  kg, less than the beer alone; 72 kg full means a 30.7 kg empty; 22 lb =
  10.0 kg; 10 + 41.3 = 51 kg. Every step reproduces, both inputs the answer
  leans on (empty weight, density) are named, and the contradiction is
  printed. This is the best paragraph in the delivery and the pattern the
  rest should follow.
- The holes are holes: pool table, cellar headroom, hi-vis date, what a
  1990 trawlerman wore, last bus time, fares, a real measured plan. None is
  a thin patch; each names what was searched.

THE THIN PATCH IS NOT IN THE HOLES. Section 0 of the pub file (21) says
"Every line carries one of four labels and no line carries none." It does
not: the paragraphs headed CONSEQUENCE, WHAT THIS MEANS, 1990 EYE and WHAT
IT LOOKS LIKE carry no label (pub 118 to 122, 266 to 268, 273 to 274, 279 to
281; hillside 54 to 57, 134 to 136; household 46 to 48, 156 to 160;
transport 37 to 43, 56 to 60), and they are the sentences a builder will
actually use. One is wrong. Pub file 273 to 274: "an optic in 1990 pours a
gill fraction, and any UI that says 25 ml is wrong by four years." The
citation says imperial measures ceased after 31 December 1994; it does not
say metric was absent before. The search channel's summary of SI 1994/1883
says that amendment substituted ", 1/6 gill, 25 ml or 35 ml" for the words
"and 1/6 gill or 25 ml", which means 25 ml was already in the 1988 Order's
text before 1994. Same channel, same weakness, so the ruling is not that the
file is wrong; it is that the consequence is unsupported and becomes HOLE 9
(read SI 1988/2039 as made). Hillside 148 to 158 shows the right form:
mechanism CITED, alterations ASSUMED, flagged HOLE 4. A8 labels every
consequence paragraph in place, DERIVED or ASSUMED, so the file's own rule
about itself is true.

One date to fix while there: clothing 140 cites a "2 September 2026 search"
in a file written 8 September. Say which.

### 2.3 Search-summary sourcing: what it may carry, and the next rung

RULED. The five files are a SPEC-station input and are good enough to build
on for three classes of fact: a dated boundary (an Act, a launch, a rename),
a number corroborated from a second direction or by printed arithmetic (the
census against the ONS series; the firkin), and the project's own scene
file. They are NOT good enough for a single-summary dimension or price that
lands on a mesh or a prop: at AUTHOR, any such number is treated as ASSUMED
whatever its label says, and the two files that say PARTIAL at the top stay
partial. Re-sourcing is the next rung, not a precondition: queue 156, a CI
fetch job where the network is, for the three targets the delivery names.
Two conditions on that item, written now so nobody finds them later: the
job extracts FACTS into a research file and commits no page image, because
the repository is public and a catalogue scan is somebody's copyright; and
every line it upgrades is marked `CITED/read` so a later reader can tell a
page read from a page summarised.

### 2.4 The withheld URL: the right trade

The screened token is `shell` (prompts.json 107); the garment's period name
is the article's slug; the file keeps host, claim, date and a one-hit search
(clothing 137 to 145). That is "reword, never loosen" applied to a URL, and
the reword loses nothing a reader needs to verify. Accepted.

### 2.5 The canon gate: what the delivery claims and what still needs printing

- NO EXEMPTION WAS ADDED: `EXEMPT` (canon-gate.py 57 to 74) has no
  `production/art` entry, `MODERNITY` is 13 terms, and the brand list is the
  imagegen file's 45. Whether either file CHANGED in this batch is `git diff
  --stat` on both, which the resident prints (expected: nothing).
- THE FINAL GATE RUN WAS OVER A SHORTER FILE. DELIVERY.md 191 says 1304
  lines examined; the six files are 1342 today; the 37-line section at 185
  to 221 is the section that describes the gate run, so it was written
  after it, and 1304 + 37 + one table line is 1342. The clean result is
  therefore a claim about a DELIVERY.md that no longer exists. My grep over
  all 1342 lines finds nothing, so the re-run should be clean, and the
  resident prints it.
- NOTHING WAS TRADED AWAY by rewording: the four classes listed at 203 to
  213 preserve meaning (verified: hillside 56 "a mass-market saloon",
  transport 51 "BR's passenger sectors" with the article URLs intact), and
  the one real loss is the disclosed URL.
- ONE HIT THE GATE WOULD GIVE THAT NOBODY RAN IT OVER: `decision-queue.md`
  73, "the shell taken from the street's own scene file". `shell` is a
  screened brand token and the queue is not an exempt path. One word, A9.

### 2.6 The cards: both defaults stand, one must say what it moves

CARD 1, free house, DEFAULT FREE HOUSE by 2026-09-11 (decision-queue.md 30
to 50): STANDS. Canon 47 to 48 says Mickey left him the pub; an inheritance
is a freehold; a tenancy passing on death needs the brewery's consent, a
fact canon does not carry, so the tied option would be inventing canon to
get a richer lever. The lever a free house gives is not weaker, it is
inverted: in 1990 to 1992 the player is COURTED, and an offer that cannot be
refused is a crime-sim pressure too.

CARD 2, two bays, DEFAULT TWO BAYS by 2026-09-11 (53 to 74): STANDS, WITH A
CORRECTION THE CARD MUST CARRY. The built street letters bays 0, 1, 2 and 4
(`decal_00_fascia_mickeys` x 6, `decal_01_fascia_fish_market` x 12,
`decal_02_fascia_ritas_pawn` x 18, `decal_03_fascia_steam_laundry` x 30;
vignette-pieces.json 512 to 515); bays 3 (x 24) and 5 (x 36) carry no
fascia. Under the bay card's default A (bay 0), a two-bay Mickey's takes
bays 0 and 1 and the FISH MARKET MOVES to bay 3, one field in
`vignette-scene.json`; under B (bay 2) it takes bays 2 and 3 and only the
fascia swap already on the bay card moves. Three bays under A swallows
Rita's Pawn as well. A default that silently deletes a shop the street
already has is a decision nobody made; the card says it. The "rooms survive"
sub-default (68 to 71) is accepted as part of the card: visible, reversible,
and canon-consistent.

THE BAY CARD ITSELF IS NOT IN THE QUEUE. The previous ruling (section 4.1)
ordered it; `decision-queue.md` WAITING holds four cards and it is not one
of them. Card 2 depends on it. A10 routes it tonight, same deadline.

### 2.7 The beer drop: right finding, wrong location

The pub needs a pavement drop and the street has none: TRUE. "A gully grate
and two manholes in the footway" (DELIVERY.md 142 to 143): FALSE. The grate
is `east_channel` (pieces 489) and both manholes are `east_carriageway` and
`west_carriageway` (522 to 523); the footway has none of the three, which
makes the finding stronger, not weaker. A11 corrects the sentence; queue 155
names the piece, blocked on Cards 2 and the bay card because its x depends
on both.

### 2.8 The review file

The convention (art-collaboration.md 40 to 42) returns a review as
`production/art/atlas-02/REVIEW.md` on the studio branch. This record is the
review; A12 dictates the file, which points here.

## 3. The quality ladder at close

| aspect | current rung | next rung, from resources we have |
|---|---|---|
| Prop import, the mesh route | Run 2: engine says it can translate 3 of 3; nothing loaded back; the lookup could not tell why. | Run 3 with A0 to A5: what appeared, under what name, whether the task was asynchronous by its own word, the bounds series printed for the first time; then the bound. |
| Art research, atlas-02 | First working, and it says so: five files, search-channel summaries, labels honest where present. | Consequence paragraphs labelled (A8); the CI fetch job (156) upgrading lines to CITED/read; the two PARTIAL files filled. |
| The world-designer role | A brief with zero spawns; its first commission was done by another agent. | Spawned as itself on the next commission, on opus, with Bash, from a checkout clause that is true. |
| Mickey's | Two cards and a bay card, defaults set, nothing laid out. | The three rulings in; then the SPEC station for the pub against the pub file, with the beer drop in the bill of materials. |

## 4. Filed, names not work

Queue files in the shape of 154, resident's read:

- 155 `a-pavement-beer-drop-for-the-pub`: a hatch about 1100 by 1100 mm in
  the 2.0 m footway at the pub's frontage, clear of the 0.125 m kerb and the
  0.255 m channel, over a cellar floor about 2.4 m below the road crown.
  BLOCKED on the bay card and Card 2, which fix its x.
- 156 `re-source-atlas-02-where-the-network-is`: the CI fetch job for the
  Argos catalogues on archive.org, the CAMRA heritage guides and ONS CZMT;
  facts extracted, no page images committed, upgraded lines marked
  `CITED/read`.
- One DECISION card, not a queue item: may research-only art commissions run
  on sonnet. Default opus until he answers.

## 5. Before the commit the resident prints

1. `python3 tools/ue/import_prop_meshes.py --selftest`: 81 checks, 0
   failures, exit 0, after A0.
2. `grep -n "zero-rules-it-out" tools/ue/import_prop_meshes.py`: zero hits.
3. `python3 tools/canon-gate.py production/art/atlas-02/DELIVERY.md
   production/art/atlas-02/research/*.md production/art/atlas-02/REVIEW.md
   production/decision-queue.md`: clean, with the line count (about 1342 plus
   the review and the queue).
4. `git diff --stat tools/canon-gate.py tools/imagegen/prompts.json`: no
   lines.
5. `git status --porcelain`: every path under `production/art/atlas-02/` or
   in this batch's named files; nothing under `.github/workflows/`,
   `production/d1-probe/DISPATCH`, `production/next-three.json` or
   `ledger-v2/studio-v2/`.
6. `grep -n "no CCTV\|model: sonnet" .claude/agents/world-designer.md`: zero
   hits.
7. `grep -c "^### " production/decision-queue.md` before and after A10: up
   by one, and the bay card's DEFAULT line present.
8. `python3 tools/docs-check.py` clean on this record.
9. `python3 ledger/verify.py`, footer FROM `ledger/.verify-footer`; the
   cadence line names this record and row `2026-09-08T21:38:35Z`.
10. For run 3, in its own later commit: the sha captured BEFORE the request
    push, the run watched by ancestry, the verdict read in the order of
    section 1.5 and the manifest opened before any message.

## 6. The amendments, in one place

- A0, TONIGHT, resident, dictated, `tools/ue/import_prop_meshes.py`: at 446
  the value becomes `above-zero-is-an-async-import/zero-is-not-a-rule-out/the-wait-is-a-registry-scan`;
  at 415 to 416 "ABOVE ZERO IS THE ASYNC HYPOTHESIS CONFIRMED; zero rules it
  out" becomes "ABOVE ZERO IS THE ASYNC HYPOTHESIS CONFIRMED; zero is not a
  rule-out, because the wait is a registry scan and not a wait on the
  import"; at 817 to 818 the check name becomes "a wait that changed nothing
  is silence, not a rule-out, and still names the route that ran".
- A1, BLOCKS THE RUN 3 DISPATCH, builder, same file: (a) `resolve_imported`
  and `_list_package` drop a trailing `.Name` from every entry and the first
  raw entry prints as `propImportSnapshotShape=`; (b) `_import_one` loads
  every entry in `new`, keeps the StaticMesh ones, resolves among those, and
  the manifest carries `appearedClasses` per asset; (c) `via_task` records
  `is_async_import_complete()` before and after a `get_objects()` call, both
  guarded by `hasattr` with the two names printed as present or absent
  (`propImportTaskApi=`), tallied as `propImportTaskAsync=`; (d)
  `via_interchange_result` keeps its return value, prints its type name and
  the attribute names containing `wait`, `done` or `complete`, and calls
  `wait_until_done` if that attribute exists. Selftest rows, accepting
  first: both snapshot shapes resolve `exact-path`; a material package beside
  the mesh resolves to the mesh.
- A2, SAME PASS: before the loop, delete every asset whose `object_path`
  already loads and print `propImportPreexistingDeleted=N/asked`; selftest
  row for the tally string.
- A3, SAME PASS: rename to the contract path under the two name rules only,
  before the save, printed as `propImportRenamed=N/asked`.
- A4, SAME PASS, wording: `propImportRouteRan` docstring says last-wins over
  routes and cumulative `appeared`.
- A5, SAME PASS: `only-package-that-appeared` is a failure
  `appeared-unnamed/<leaf>`, tallied `propImportAppearedUnnamed=N/asked`,
  bounds read into the manifest under the leaf's name; the E2 row at 784 to
  787 re-expected accordingly.
- A6, dictated, `production/findings.txt`, appended beside the run 1 entry:
  "RUN 2 CORRECTION, 2026-09-08. `propImportVia=none-of-2-candidates` beside
  `propNote=none` and `propGltfCanTranslate=3/3` was the lookup, not the
  engine: `_try` treated a None return as a refusal and both routes ended in
  `load_asset(object_path)`, which returns None without raising for a path
  that does not resolve. Whether the import made an asset elsewhere, made
  nothing and logged, or completed after the lookup is what run 3 measures
  (`propImportResolvedVia`, `propImportedNames`, `propImportTaskAsync`)."
- A7, dictated, `.claude/agents/world-designer.md`: line 5 `model: opus`;
  line 4 adds `Bash`; line 33 becomes "No mobiles, no internet; CCTV rare,
  the bank and the off-licence, as canon says."; after line 52 add "IN-HOUSE
  CLAUSE, ruled 2026-09-08: a spawned designer has no separate checkout. You
  write only under `production/art/<commission>/` in the studio checkout,
  and the resident prints `git status --porcelain` before committing to
  prove this list held." And `game-design/art-collaboration.md` line 59:
  "staffed by the world-designer role" becomes "delivered on 2026-09-08 by a
  content-wrangler spawn under this convention (the spawn log has no
  world-designer row that day); the `world-designer` role in
  `.claude/agents/` staffs it from the next commission", plus the same
  in-house clause after section 2.
- A8, dictated, the five research files: every paragraph headed CONSEQUENCE,
  WHAT THIS MEANS, 1990 EYE, WHAT IT LOOKS LIKE or WHY IT IS WORTH HAVING
  gains a label in its first word, DERIVED where it follows from a cited
  line by stated reasoning and ASSUMED otherwise; pub 273 to 274 becomes
  "HOLE 9: whether 25 ml was already a lawful measure in 1990 needs SI
  1988/2039 read as made; the 1994 amendment's wording suggests it was", and
  section 7 gains the row; clothing 140 names the actual search date.
- A9, dictated, `production/decision-queue.md` 73: "the shell taken from"
  becomes "the carcass taken from".
- A10, dictated, `production/decision-queue.md`, a new WAITING card "Which
  bay is Mickey's?" in the shape of Card 2, options A (bay 0, the lettering;
  the bar-back and shop-shelves cards swap x) and B (bay 2, the bar back;
  the two fascias swap x), RECOMMENDATION A, DEFAULT A by 2026-09-11,
  EVIDENCE the previous ruling's section 4.1. And Card 2 gains, after its
  option A: "Under the bay card's A this takes bays 0 and 1 and moves the
  fish market fascia to bay 3, the unlettered one; under B it takes bays 2
  and 3 and moves nothing else. Three bays under A takes Rita's Pawn too."
- A11, dictated, `production/art/atlas-02/DELIVERY.md` 142 to 143: "have a
  gully grate and two manholes in the footway and no beer drop" becomes
  "have a gully grate in the channel and two manholes in the carriageway,
  and nothing at all in the footway; no beer drop anywhere".
- A12, dictated, `production/art/atlas-02/REVIEW.md`, new: "STATUS: LOG.
  Reviewed 2026-09-08 by director ruling
  `game-design/decision-2026-09-08-the-lookup-that-lied-and-the-art-line-in-house.md`,
  section 2. Accepted as a SPEC-station input under the sourcing rule in
  its section 2.3, with amendments A8 and A11 applied in place. Next rung:
  queue 156."

What is pulled out, said plainly: the token that says zero rules anything
out; the weak resolver rule as a COUNT; `model: sonnet`; "no CCTV"; "in the
footway"; the 25 ml consequence as a fact; the word "shell" in the queue.
Nothing else is refused. Nothing in this batch weakens an instrument or
moves a bound, and where this record could not print a number (the
selftest, the gate), it says so and names who does.

<!--RULING spawn=2026-09-08T21:38:35Z-->
