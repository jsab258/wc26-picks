# Ruling: the run 24 landing (the instrument made the fault). LAND WITH AMENDMENTS

> **STATUS: LOG, 2026-09-06.** Director ruling at spawn 2026-09-06T15:38:47Z
> on the uncommitted tree after run 24 landed as `1ee090f8`: the material
> generator (engine-specialist, the only code file, 720 changed lines), and
> the resident's DISPATCH run 25 entry, the rewritten head of queue 123, and
> new queue items 134 and 135. Escalated because the landing changes a
> conclusion and overturns a claim the resident made to Jafar. NOT CURRENT
> once the amended commit lands; from then the files are the reading copies
> and this is the record of why.

VERDICT: LAND WITH AMENDMENTS. One amendment blocks the push, because the
push IS the dispatch of Unreal run 25 (`production/d1-probe/DISPATCH` is a
push trigger) and without it the run can print a word the evidence cannot
back:

- A1. `tools/ue/make_base_material.py`: the accepting case for the
  statistics channel must be a TWIN, a material this script makes and
  recompiles in this process the same way, read through the same call,
  outside the compile markers, never saved and deleted after the reading.
  The engine-material reading stays and is printed under its own key, and
  it gates nothing. Section 4 says why a cached engine material is not the
  accepting case for the zero it is asked to license, and section 10 states
  A1 as behaviour.
- A2, rides the same builder pass and does not block on its own: three
  label fixes in the tested layer and one docstring, section 10.
- A3, dictated text for the resident's hand: DISPATCH, queue 123, NOW.md and
  one row in `ledger-v2/studio-v2/learning.md`, section 10.

Everything else in the tree lands as written. Queue 134 and 135 are
documents and commit on the resident's read.

Nothing here has run an engine since `1ee090f8`. The whole editor-side half
of this diff (everything below `selftest()` in the script) is unverifiable
until run 25, and the 128 green checks do not stand in for it: section 8
lists what they cover and what they cannot.

## 0. What was read, what was not run, and what I was told

Read whole: `tools/ue/make_base_material.py` (2858 lines, in three pages);
`production/d1-probe/ue-build.txt` (run 24, sha 1e751f6);
`production/d1-probe/ue-material-log.txt` (run 24's editor log, all three
sections); `production/d1-probe/DISPATCH`; `production/queue/123`, `134`,
`135`; the ruling of 14:33:03Z for shape; `production/NOW.md` 1 to 70;
`.claude/agents/producer.md` 18 to 92; `ledger-v2/studio-v2/learning.md` 36
to 77 and its row index; `.claude/agent-log.tsv` 290 to 300 plus the grep
of every studio-director row; `.github/workflows/ledger-probe-unreal.yml`
301 to 306, 476 to 478, 551 to 555, 604 to 608 by grep.

Read for one purpose: the pre-edit copy `make_base_material.py.bak` in the
session scratchpad. It is the PRE-RUN-24 script (no `derived_sampler_type`
in it; `NORMAL_DEFAULTS` still holds both engine paths at 156 to 159;
`_first_that_loads` at 875 to 883 calls `load_asset` with no registry
check). It confirms the probe cost and it cannot show me the run 24
catch-all, because the code that ran run 24 is at `1e751f6` and this spawn
has no git. So the old `str(compression).split(".")[-1]` and its branches
are the builder's description, corroborated by the keys (section 2), and I
say so wherever I lean on them.

NOTHING WAS RUN. No shell. The verify numbers in this record are the
coordinator's, quoted: `ue material generator ok (128 checks)`, `docs
146/146 clean`, `4291 CoreTests`, `Game layer compiles (191 files)`, and
the one red, `DIRECTOR NOT SPAWNED: 720 changed line(s) vs 100 threshold`,
which this record's stamp clears.

PREMISE, CLAUDE.md section 0: late-analog Meridian, the moat first, photoreal
wet grimy Britain as the visual bar. This landing is the street's material,
on the visual leg of the Meridian Test. Nothing purchased, no licence entry,
no retired bar cited. Nothing here contradicts the premise.

## 1. The reference and the stamp

The reference is the code commit `1ee090f8@2026-09-06T15:08:49Z`. Rows in
`.claude/agent-log.tsv` newer than that instant: line 297
(engine-specialist 15:19:24Z), 298 (engine-specialist 15:32:46Z), 299
(studio-director 15:38:47Z). Exactly ONE studio-director row. That is this
spawn and the one stamp at the foot of this record.

The row `2026-09-06T14:33:03Z` (line 294) is older than the reference and
is already stamped by the ruling of that name; the gate does not ask for it
and this record does not take it.

## 2. The finding, checked against the keys and the log

What run 24's COMMITTED evidence establishes, each item read off the file:

- `ue-build.txt` line 12: `materialNormalDefault=generated../Game/Ledger/
  T_LedgerDefaultNormal..asked.NORMAL..derives.LINEAR_COLOR`,
  `materialDefaultsDetail=...NormalMap.generated.TYPE-MISMATCH...`,
  `materialDefaultsBound=2/3`, and `materialNote=T_LedgerDefaultNormal-
  derives-LINEAR_COLOR-not-NORMAL/RoughnessMap-engine-default-derives-COLOR-
  not-LINEAR_COLOR`. No `compression_settings-refused` and no
  `compression_settings-not-available` note, so the script's own write of
  TC_NORMALMAP raised nothing and the enum member resolved.
- `ue-material-log.txt` 115 to 117: the importer, on that exact TGA,
  `LogInterchangePipeline: Display: Auto-detected normal map`.
- `ue-material-log.txt` 113 to 114 and 124 to 125: the two `LoadAsset
  failed` Errors for `/Engine/EngineMaterials/DefaultNormal` and
  `/Engine/EngineResources/DefaultTextureNormal`; 128: `Failure - 2
  error(s), 1 warning(s)`; 126: the one warning is LogObjectTools. The
  errors in the summary are the two candidate lookups and nothing else.
- Line 35: `rhiname="Null"`. Lines 111 and 120: the script ran from
  15:06:50.401 to 15:06:51.075. Line 12 of `ue-build.txt`:
  `materialCompileInstructions=pixel.0..vertex.0 materialCompileSamplers=0
  materialCompileErrors=0/8 materialCompileMarkers=begin.yes/end.yes
  materialCompile=UNPROVEN`.

So: a texture two independent writers set to TC_Normalmap read back as
deriving LINEAR_COLOR, and `main()` declared the sampler with the derived
type (`_sampler_enum(unreal, got or asked)`, line 2693 today and the same
expression in the builder's account of run 24). The instrument's misread
became the sampler's declaration. That much is on the record.

What is INFERENCE, and how it gets measured. "The old parse fell into the
catch-all" is the best available explanation, not a reading: run 24 printed
the derived type and never the value it derived it from. The alternative,
that the texture really was TC_Default at read time, needs two silent
failures at once (the importer's auto-detect not persisting AND
`set_editor_property` doing nothing without raising, when a raise would
have printed `-refused`). Run 25 prints the value, its `repr`, and the route
that read it (`materialCompressionReadback`, and the log's `str=`/`repr=`
line). `NormalMap.NORMALMAP.via.enum-identity` confirms the finding;
`NormalMap.DEFAULT` on that key withdraws it and says the texture, not the
reading, was wrong. That condition is dictated into DISPATCH (A3.1) so the
run is read by a rule written before it.

"All three textures took the catch-all" is the SAME observation restated,
not a second one. For TC_Default the engine's own answer IS the default
branch (`Color` if sRGB, else `LinearColor`), so colour and roughness print
the same word whether a named branch or a catch-all produced it. The claim
reduces to: the one texture that could have hit a named branch did not.
True as far as the keys go, and worth one sentence in queue 123 and
DISPATCH saying it is one observation (A3.2).

## 3. Question 1: the catch-all gate, and whether None can be silently wrong

Traced from `derived_sampler_type` (342 to 378) outward, every path a None
takes:

- `_texture_reading` (2182 to 2209) returns `(None, leaf, via, srgb)`.
- `_resolve_default` (2333 to 2365), engine candidate: `got == asked` is
  False, the candidate is REFUSED, a note is appended, and the generated
  path runs. Generated (`_generate_default_texture`, 2326 to 2330): the
  texture is returned with `got` None and a note naming leaf and via.
- `main()` line 2691 to 2693: `_sampler_enum(unreal, got or asked)`. A None
  `got` falls to `asked`, the declared entry of `MAP_SAMPLER_TYPES`. So a
  refusal never becomes an enum value; the sampler is declared with the
  type this file intended.

And every refusal is on the line three times: `default_via` prints
`derives.unknown` (392); `defaults_field` (409 to 414) counts it unbound
and names it; `compression_field` prints the leaf as UNRECOGNISED with its
route. And `material_status` line 904 makes any short defaults count
PARTIAL before the compile word is even consulted, so no run with a refused
reading can print MADE, whatever the compile channel says. RULED: refusing
is correct, and a None cannot declare a wrong type by any path in this
file.

What the gate does NOT close, by design and said plainly: a NON-None wrong
derivation is still declared. `got or asked` takes `got` whenever it
exists, which is the run 24 mechanism and is still the mechanism, because
the design is "declare what the texture derives so the compile cannot lose
on a mismatch". A real leaf that is wrong (identity resolving to a member
nobody expected) would be declared. It cannot be silent: TYPE-MISMATCH on
the detail key, PARTIAL on the status, and now the leaf and the route on
the readback key. That is what the readback key was built for. Accepted.

Two labels are less than the keys beside them, and they are A2 because the
pair is the design and one key on its own should still read right:
`defaults_field` prints TYPE-MISMATCH both for "derived a different type"
and for "derived nothing" (v[2] None), and `compression_field` prints the
leaf as UNRECOGNISED when the via is `nothing-measured` or
`readback-refused` (line 445, `r[1] or "UNRECOGNISED"`), which its own
docstring at 434 to 436 says is not the same fact.

One pre-existing path, named and not blocking: `_sampler_enum` returning
None (2212 to 2234) leaves the expression on the engine's default sampler
type with only a note (`-sampler-type-not-available`, 2669). Nothing in the
status turns on it. It is caught one channel down, by the compile
diagnostics, and it is older than this diff.

The branch order (365 to 378) is the engine's `GetSamplerTypeForTexture`
as I remember it: Normalmap, Grayscale by sRGB, Alpha, Masks,
DistanceFieldFont, default by sRGB. The file's header says Epic's reference
answers 403 through the proxy, so this is recollection agreeing with the
builder's, not a check. The virtual-texture variants are not modelled and
no texture here is virtual. And the live enum decides (2103 to 2125; 2206
to 2208; selftest 1759 to 1765): a leaf this file has never heard of still
takes the engine's default branch when the engine vouches for it, so the
gate does not make this file the authority over the engine.

## 4. Question 2: the control, and what a zero beside it is allowed to mean

STRUCTURAL, from `compile_verdict` (707 to 721): ERRORS first, on any
diagnostic. `instructions is None` is UNPROVEN. `instructions <= 0` is
NO-SHADER only when `control_instructions is not None and
control_instructions > 0`, else UNPROVEN. A non-zero count goes on to the
log conditions and never sees the control (rows 1944 and 1945 assert OK
with control 187 and with control 0). Selftest rows 1936 to 1939 and 1948
to 1949 walk exactly the four cells that matter: zero with no control,
zero with control zero, zero with control 187, and a refused statistics
call with control 187. NO-SHADER is reachable only past a positive control;
UNPROVEN is reachable whenever the control is silent or zero. The two words
have NOT collapsed. `material_status` 906 maps NO-SHADER to NOT-COMPILED
and 1965 to 1971 asserts it. Sound.

SEMANTIC, and this is A1. What does the control prove? `_statistics_control`
(2462 to 2497) loads an engine material by path and reads its statistics.
That material carries whatever shader map the derived-data cache holds for
it. A non-zero from it proves `get_statistics` returns a number WHEN A
SHADER MAP IS PRESENT. Our material was created and recompiled in this
process 0.67 seconds before the read, in a commandlet with a null RHI, and
no engine tick runs between `recompile_material` (2709) and the read
(2717). If this editor compiles material shaders asynchronously, our shader
map is not there at read time whether or not the graph is good, and the
line prints `pixel.0` beside `control.187`, which the rule calls NO-SHADER,
which the status calls NOT-COMPILED, whose own comment (530 to 537) says
"this material does not render and the material step is where to look".
The cook then compiles the same graph for the target platform on its own
schedule, and the frames show brick. The builder's `_shader_api_names`
docstring (2500 to 2508) names this exact possibility, and the verdict rule
does not account for it.

Rule 5b, applied: the accepting case for "a material recompiled here yields
a count here" is a material recompiled here. A cached engine material is an
accepting case for a different sentence. Hence the TWIN: a second material
this script makes, wires trivially, recompiles the same way and reads
through the same call, in the same process, outside our compile markers so
its diagnostics can never count as ours. The four outcomes, each
informative:

    twin > 0, ours > 0      OK (the log conditions permitting)
    twin > 0, ours = 0      NO-SHADER, and now the word is sound
    twin = 0 or absent      UNPROVEN, and the engine reading beside it says
                            whether the channel is alive for anything
                            (cached > 0) or dead here (0 or absent)
    ours > 0 at all         OK path regardless, as today

The third row is the one that names the next rung without another argument:
twin zero beside an engine reading above zero is "this commandlet compiles
asynchronously or not at all", and the move is a wait-for-compile call if
`_shader_api_names` finds one, or the commandlet's rendering allowance on
the invocation, which is a workflow change and is filed (section 12), not
built. Twin zero beside engine zero is "the channel is dead in this
process", same next rung, different first suspect.

Is the async reading itself verified? No. It is my reading of the engine
and it is exactly the kind of engine fact this container cannot check. If
the editor compiles synchronously here, the twin costs one trivial compile
and changes nothing. If it does not, the twin is the difference between a
true word and a false one. Fail-closed either way: a twin that cannot be
made prints the control as not-available and the word is UNPROVEN, which
is where the run would have been with no control at all. Nothing true is
lost by adding it and one false NOT-COMPILED is prevented.

One smaller fault in the same function, also A1: the loop returns on the
first control whose statistics are not None, INCLUDING a zero (2495 to
2496). A first control answering zero ends the search and a later one that
would answer 187 is never asked, so "dead" can be printed over a live
channel; and the count of controls asked is not on the line, which is a
zero without its denominator. The engine reading tries all of them, keeps
the first non-zero, and prints `answered.A/T`.

A note on the registry gate the controls now depend on: `does_asset_exist`
at script time needs the registry to have scanned `/Engine` content. Run
24's colour default loaded `/Engine/EngineResources/DefaultTexture` through
`load_asset`, whose miss message names the registry, so the registry had
engine content at that moment. Probably fine, unverified, and the twin does
not depend on it at all, which is one more reason it is the gating control.

## 5. Question 3: the resident's overstatement, and whether the correction is complete

THE SENTENCE, grepped rather than the site: `pixel.0`, `vertex.0`, `proves
candidate D`, `candidate D`, `instruction count`, `never compiled`, `no
shader`, over the whole tree. Outside the script, the hits are DISPATCH 504
to 510 and queue 123 lines 42 to 57, both of which are the CORRECTION, and
queue 123 line 8 with NOW.md 12 to 45, which attribute candidate D to run
23's quads, correctly. No copy of the overstatement survives anywhere in
the tree, and queue 123's status line (7 to 11) says D is answered by run
23. In the record, the correction is complete.

In the same neighbourhood two sentences are now false as standing
statements, and they are dictated (A3.5, A3.6): queue 123 lines 109 to 110,
"Unexplained and plausibly the same event: `materialEditorCmdExit=1`", and
NOW.md 36 to 40, "the normal sampler carries a NULL texture ...
`materialEditorCmdExit=1` ... is still unexplained". Both were run 23's
state; run 24 explained the exit (section 2) and gave the normal sampler a
generated texture. NOW.md carries no run 24 entry at all, and its own line
9 says a stale NOW is worse than none.

THE CHANNEL. `producer.md` 54 to 57: no self-correction narrative goes to
Jafar; the lesson goes to `ledger-v2/studio-v2/learning.md`, and he gets
one line only if the outcome changed for him. Did it? He was told the
instruction count proved the material never compiled. The truth is that run
23's quads proved it and the count corroborates. The material never
compiled, the street is untextured, the fix is in flight: identical for
him. RULED: no line to Jafar; one row in learning.md, dictated as A3.7.
`production/outbox/` holds no run 24 message today (one file, the
pc-processes answer), so whatever he was told went by a path the tree does
not carry. That is a channel-discipline observation about the resident and
it is noted, not ruled, because it was not asked.

## 6. Question 4: the deleted probes, and the prediction as accountability

THE COST IS REAL AND THE GATE REMOVES IT INDEPENDENTLY OF THE LISTS. The
pre-run-24 `_first_that_loads` (bak 875 to 883) called `load_asset` on
every candidate; run 24's log shows the two misses as the only Error lines
and the whole of the summary's error count (section 2). The new
`_first_that_loads` (2075 to 2100) asks `does_asset_exist` first, which
says nothing on a miss, and reports every candidate it skipped. So the
question "delete or keep" is a question about what the slot's DEFAULT
should be, not about cost, and it splits:

- ROUGHNESS, right by construction. The engine colour candidates resolve to
  an sRGB TC_Default texture, which derives COLOR against a slot declared
  LINEAR_COLOR; run 24's own note says so
  (`RoughnessMap-engine-default-derives-COLOR-not-LINEAR_COLOR`). A
  candidate the type check refuses every time is a note, not a default.
- NORMAL, right by principle. The reading lost is "does this engine version
  have DefaultNormal", and the project does not need it: the generated
  default owns the slot, its derived type is checked in the selftest
  against the declared one (1800 to 1814), and no engine version can move
  an asset this script writes. The two paths are preserved in the comment
  (211 to 224) for the day someone wants the reading back, and with the
  gate in place that reading is now free. Restoring it is a measurement, as
  the comment says.
- COLOUR keeps its probe, and for run 25 that is right for a reason the
  builder did not state: `/Engine/EngineResources/DefaultTexture` is an
  engine-authored texture with a known compression (TC_Default, sRGB), so
  its `materialCompressionReadback` line is an accepting case for the
  enum-identity route on a texture this script did not write. Keep it
  through run 25. AFTER run 25, file (section 12, a): that texture is a
  grey checker, which is what the engine's fallback material also looks
  like (queue 123 line 90 and NOW.md 33 to 34 both say so), so "our
  material on its default" and "the engine's fallback" are the same picture
  in a frame. A generated flat mid-grey separates them by eye and by a
  period measurement. Queue, named, not built.

THE PREDICTION. "materialEditorCmdExit should now read 0; if it is still 1
the log tail says what else is in the summary" is the right shape: written
before the run, with its falsifier and where to read it (section 2 of the
committed log file). Two things it should say and does not, dictated
(A3.3). First, it rests on the engine failing a commandlet on errors and
not on warnings, which no run here has measured; the LogObjectTools
warning at line 126 stays, so a 1 with zero errors in the summary is that
assumption failing and not this ruling. Second, exit 0 checks the SMALLEST
claim in the entry, the probe cost. The ruling's main claim, that the
reading and not the texture was wrong, is checked by
`materialCompressionReadback` reading `NormalMap.NORMALMAP` with
`materialDefaultsBound=3/3`, and a prediction that names the wrong key as
its own check is accountability pointed at the easy target. With those two
sentences in, RULED: it is a sound way to hold itself to account, and it is
the way this project asks for.

## 7. Question 5: the run 25 DISPATCH entry

The acceptance (512 to 527) is ordered control first, instruction count
second, then the two frame items and the defaults count, and 526 to 527
says that with the control silent the count says nothing and the frames
judge. Nothing in it promises that a non-zero count alone settles the
question. What it says in the OTHER direction is wrong: 516 to 517,
"WITHOUT THIS, the instruction count is evidence in neither direction". A
non-zero count stands on its own, because nothing but a compiled shader
produces one, and the code treats it so (section 4). What the control
licenses is the ZERO. Dictated (A3.4), and after A1 the item names the
twin.

Two smaller sentences, dictated with it: 466 to 467 "A spelling like
TC_NORMALMAP: 1 leaves the tail NORMALMAP: 1>" mixes two spellings; the
tail of `<TextureCompressionSettings.TC_NORMALMAP: 1>` after
`split(".")[-1]` is `TC_NORMALMAP: 1>`, and the same sentence sits in queue
123 at 21 to 22. And 455, "RUN 24 IS HOW WE KNOW", is one word past the
evidence: run 24 is how we know the DECLARATION was wrong; run 25 is how we
find out whether the reading or the texture made it so (section 2).

## 8. What 128 green checks cover, and what they cannot

Covered, in the container, and I read the cases rather than the count:
`compression_leaf` on eleven spellings including the four run 24 could
have been handed (1730 to 1749); `derived_sampler_type` on 21 rows, both
ways, including the refusals (1681 to 1727); the live-enum gate (1753 to
1765); `compression_field` on three shapes (1768 to 1787); the generated
defaults deriving their declared types (1800 to 1814); `compile_verdict` on
18 rows with the control column (1916 to 1962); NO-SHADER reaching
NOT-COMPILED (1965 to 1971); the MADE ratchet over all sixteen (defaults,
compile) cells (1237 to 1247); every formatter line checked for one `=`
per token.

NOT covered, and not coverable from here, all of it run 25: what UE 5.8
answers for `compression_settings` and by which route (identity, int, or
parse); whether `does_asset_exist` is quiet and true at script time;
whether `get_statistics` returns a non-zero for anything in this
commandlet; whether the editor compiles synchronously here; whether the
twin can be created, recompiled and deleted without a log line; whether
the summary reads Success and the exit 0.

And one thing that is not in this tree at all. The acceptance's frame items
(DISPATCH 519 to 523: the quad's chroma against "max 6 of 255 today", bay3
against "R/B 0.933") are session measurements by the resident. The ruling
of 14:33:03Z, section 16 item d, named a committed instrument for them
(`quadChromaMean` and `quadChromaMax` per `quadBoxPx` from the binary, in
`FrameStats.h`) and said it rides run 25. It is in no queue file and not
in `ue-probe/` (grep `quadChroma`: no hits in either). Under the weekend
order it waits; it is named again here (section 12, c) so Monday files it,
and run 25's frame numbers are read knowing no tool prints them.

## 9. Scope, and the ladder

ASKED: the misread fix, the control, the probes, the DISPATCH entry, the
queue 123 correction. All of it is the asked thing. Queue 134 (the map's
change detector has no consumer, a rule 6 finding) and 135 (fourteen of
fourteen by a nameless pin) are findings filed with names and a moving
number each; both land as documents, and 135 rightly says not to lower the
count.

ADJACENT, named and not done: the flat-grey colour default (a); the
commandlet's rendering allowance (b); the quad chroma instrument (c). The
twin is the one adjacent thing pulled into this change, because the word
this change introduces depends on it.

THE LADDER. The reading route is best available: identity before integer
before parse, all three printed, the value and its repr in the log, the
live enum deciding. The compile word is first working until A1, best
available after it, and its next rung is not blank: a wait-for-compile call
if the name enumeration finds one, else the invocation flag. The default
textures are best available for two slots and the colour slot's next rung
is (a). The frame half of the acceptance is a hand measurement, and its
next rung is (c).

## 10. The amendments, stated as behaviour

A1, `tools/ue/make_base_material.py`, engine-specialist, BLOCKS THE PUSH.

1. After the END marker is logged (2752) and before the editor log is read
   (2755): delete any `/Game/Ledger/M_LedgerControlTwin` left by a previous
   run (the pattern at 2532 to 2537), create the twin with the same
   `create_asset` call as ours, connect one constant vector expression to
   `MP_BASE_COLOR` through `connect_material_property`, call
   `recompile_material` on it, read it through `_material_statistics` with
   the label `twin`, then `delete_asset` it and append a report line saying
   whether the delete took and whether `does_asset_exist` is False after
   it. NEVER saved. Every step guarded; a refused step names itself in the
   `from.` value and the control is None.
2. `compile_verdict(..., control_instructions=<the twin's pixel count>)`.
   The function itself does not change.
3. `compile_fields`: `materialCompileControl=pixel.N..vertex.N..from.<twin
   path or the named absence>` carries the twin. A NEW key,
   `materialCompileChannel=pixel.N..vertex.N..from.<engine path>..
   answered.A/T`, carries the engine-material reading: all T candidates
   asked, the first non-zero kept, `not-available` when none returned a
   number, and it gates nothing. `materialCompileControlIs=` names the twin
   in its text. The `materialCompileRule=` token is unchanged.
4. Docstrings that say what the control is: the COMPILE_NO_SHADER block
   (571 to 577), `_statistics_control`, the STATUS_NOT_COMPILED comment
   (530 to 537, which now reads "no shader map readable for this material
   at read time, beside a twin recompiled the same way that had one"), and
   `compile_fields` 735 (add NO-SHADER to the list) and 751 to 759.
5. Selftest: the passing line carries both keys; one accepting and one
   rejecting shape for the channel formatter (`answered.1/4`, `answered.0/4`,
   `not-available`). The builder states the new count; this record does not
   guess it.

A2, same file, same pass, does not block on its own (if the pass lands
without it, it goes to the queue by name):

1. `defaults_field` prints `TYPE-UNKNOWN` when the derived type is None and
   keeps `TYPE-MISMATCH` for a real mismatch; one row each in the selftest.
2. `compression_field` prints the leaf as `none` when the via is
   `nothing-measured` or `readback-refused`, and `UNRECOGNISED` only when a
   value was read and nothing in it is a leaf; one row each.
3. The `_statistics_control` loop change is A1.3 and is listed here only so
   the pair is visible.

A3, dictated text, the resident's hand under the one-line allowance, each
an exact replacement.

A3.1 DISPATCH 466 to 467. Replace `A spelling like TC_NORMALMAP: 1 leaves
the tail NORMALMAP: 1> which matches no named branch, so the catch-all
answered LINEAR_COLOR.` with `A spelling like
<TextureCompressionSettings.TC_NORMALMAP: 1> leaves the tail TC_NORMALMAP: 1>,
which matches no named branch, so the catch-all answered LINEAR_COLOR. That
is the best available explanation and not yet a measurement: run 24 printed
the derived type and never the value it derived it from. This run prints
both. NormalMap.NORMALMAP on materialCompressionReadback confirms it;
NormalMap.DEFAULT on that key withdraws it and says the texture, not the
reading, was wrong on run 24.`

A3.2 DISPATCH 469 to 471, append after `hid the normal.`: `That is the same
observation as the paragraph above and not a second one: for TC_DEFAULT the
engine's own answer IS the default branch, so colour and roughness print
the same word whichever route produced it.` Queue 123 lines 24 to 28, the
same sentence appended.

A3.3 DISPATCH 495 to 499, append after `says what else is in it.`: `The
prediction rests on the engine failing a commandlet on errors and not on
warnings, which no run here has measured; the LogObjectTools warning stays,
so a 1 with zero errors in the summary is that assumption failing and not
this ruling. And exit 0 checks the smallest claim in this entry. The check
on the misread is materialCompressionReadback reading NormalMap.NORMALMAP
beside materialDefaultsBound=3/3.`

A3.4 DISPATCH 514 to 517, item 1. Replace with: `1. materialCompileControl=
pixel.N with N above zero, where the control is a TWIN: a second material
this script makes and recompiles in this process the same way, read through
the same call, outside our compile markers, never saved and deleted after
the reading (amendment A1 of the ruling of 2026-09-06 on this landing). A
cached engine material answers from the derived-data cache and says nothing
about whether a material compiled here has a shader map at read time.
WITHOUT THIS, a ZERO instruction count is evidence in neither direction; a
non-zero count stands on its own, because nothing but a compiled shader
produces one. materialCompileChannel=pixel.N..from.<engine material>..
answered.A/T is printed beside it and gates nothing: it says whether the
call returns a number for anything in this editor.` And at 526 to 527,
append: `If the twin reads zero and the channel reads above zero, this
commandlet compiles asynchronously or not at all, and the next rung is a
wait-for-compile call or the commandlet's rendering allowance on the
invocation, which is a workflow change and is filed, not built.` And at 530,
replace `an answered zero beside a working channel` with `an answered zero
beside a twin that answered above zero in the same process`. And at 455,
replace `AND RUN 24 IS HOW WE KNOW` with `AND RUN 24 IS THE EVIDENCE; RUN 25
IS THE MEASUREMENT`.

A3.5 Queue 123 lines 21 to 22, the tail sentence, as A3.1 without the
run 25 clauses. Line 99, under the heading `## The mechanism, still a lead
and not yet proven`, insert: `RUN 23'S STATE, kept for the record and
superseded by the RUN 24 section above.` Lines 109 to 110, replace
`Unexplained and plausibly the same event: `materialEditorCmdExit=1` printed
beside `materialScriptReturn=0` and `materialStatus=MADE`.` with `EXPLAINED
BY RUN 24'S LOG: `materialEditorCmdExit=1` was the editor's own summary
counting the two failed engine candidate lookups as errors, and nothing to
do with the material.`

A3.6 NOW.md 36 to 40, replace the paragraph with: `The mechanism, from run
24 (`1ee090f8`): the normal sampler was declared with a type the script
MISREAD off its own generated texture, and the two missing engine
candidates were the whole of the editor's error summary, which is what
`materialEditorCmdExit=1` was. Both are fixed in the tree; run 25 is the
measurement. What run 24 did NOT prove: `materialCompileInstructions=pixel.0`
has never had an accepting case, so candidate D stands on run 23's quads
and on nothing else yet. RUN 25 DISPATCHED 2026-09-06 from <sha>; the branch
is FROZEN until a landed run contains it.` The resident fills the sha from
the commit it makes.

A3.7 `ledger-v2/studio-v2/learning.md`, one row after L35:
`| L36 | 2026-09-06 | the resident told Jafar that run 24's pixel shader
instruction count of zero PROVED the base material never compiled. That
channel had never printed a non-zero number for any material, the editor
ran headless with a null RHI, and samplers, pixel and vertex read zero
together, which is also what no shader map at read time looks like. The
builder refused the sentence | no-change note: rules 2 and 3b already cover
it. What is recorded is the discriminator: before a zero from a new channel
is called a proof, name the run on which that channel printed anything
else. Candidate D stands on run 23's control quads, so the outcome for
Jafar did not change and no line goes to him | production/queue/123-the-
sampler-reads-the-engine-default-texture.md; production/d1-probe/DISPATCH
run 25; game-design/decision-2026-09-06-ruling-run24-landing-the-instrument-
made-the-fault.md |`

## 11. What the resident prints before the commit

1. The engine-specialist's A1 (and A2) diff, read against sections 4 and 3,
   with the builder's stated new selftest count.
2. `python3 ledger/verify.py`, footer pasted FROM `ledger/.verify-footer`.
   Expected: `ue material generator ok (N checks)` with N above 128 by the
   stated number; the cadence line pairing this record with row
   `2026-09-06T15:38:47Z`; `docs` clean with this record counted; every
   other line as in the footer quoted in section 0.
3. `grep -rn "NORMALMAP: 1>" production/ game-design/` returns nothing
   outside this record.
4. `grep -rn "still unexplained\|plausibly the same event" production/NOW.md
   production/queue/123*` returns nothing.
5. `grep -n "materialCompileChannel\|M_LedgerControlTwin"
   tools/ue/make_base_material.py` returns the emit, the twin's make and
   delete, and the selftest check.
6. `grep -c "| L36 |" ledger-v2/studio-v2/learning.md` returns 1.
7. The commit message names this record and states: run 25 is dispatched by
   this push; the branch is FROZEN until a landed run contains this commit
   (runs 18 and 22 were lost to exactly that); and the frame half of run
   25's acceptance is read by hand because no committed tool prints it.

## 12. Filed and waiting (names, not work)

a. The base colour default becomes a generated flat mid-grey, so a piece on
   our material's default and a piece on the engine's fallback material are
   different pictures. After run 25, because the engine texture is run 25's
   accepting case for the compression readback on a texture this script did
   not write. GAME PATH, engine-specialist, small.
b. The material step's invocation gets the commandlet's rendering allowance
   IF run 25 prints the twin at zero. `.github/workflows/ledger-probe-
   unreal.yml` line 303. Studio, one flag, one round trip, and only on that
   reading.
c. The quad chroma instrument, the ruling of 14:33:03Z section 16 item d,
   still unfiled: `quadChromaMean` and `quadChromaMax` per `quadBoxPx` from
   the binary, in `FrameStats.h` where g++ runs it. GAME PATH.
d. `learning.md` carries two rows labelled L32 (lines 73 and 74). One-line
   renumber, whoever next opens the file.

<!--RULING spawn=2026-09-06T15:38:47Z-->
