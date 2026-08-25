# DIRECTOR RULING — ValuePanel first firing (b7d232b), the three-item batch, and the §3b exemplar (25 Aug 2026)

> **STATUS — LOG, 2026-08-25. NOT CURRENT after the completed-panel landing
> (weather-carried, refs re-aimed) is read.**
> Triggers: builder-batch review before commit; a landing that changes a
> conclusion; CLAUDE.md. Verified this session, not quoted: `frames.tsv`
> weather columns (day1_noon wet=1.00, day5_noon wet=0.00, all `ref_*`
> dry) confirming the resident's retraction; `tools/lint-static.py` —
> `static_bodies()` summed over ALL files at `main()` line 313 while
> `scan()` walks only single-partial-class files with detected instance
> members, so the printed denominator counts bodies never walked. The
> 560/29/14-of-88 figures are the resident's count; I verified the
> MECHANISM in code, not the arithmetic — the mechanism alone convicts
> the printed line.

## A. COMMIT NOW; DISPATCH AFTER ONE PANEL-REPAIR PASS, capped at one cycle.

**Commit:** the three-item batch is APPROVED-TO-COMMIT — this row supplies
the cadence. The two builder refusals are both RATIFIED as correct
tier-3 conduct: the avenue-lint builder refusing my `RAW_OK` instruction
(nine known faults must not print as clean reads — the `DEFERRED` ledger
with per-method pins is the right shape, and catching the verify footer
asserting a clean sweep was the best find in the batch), and the
yard-depth builder's third cause (tiling remainder in deep yards) plus
its correction of my wrong grep. The wires fix is the model batch item:
twin found before review, material derived rather than shared-edited,
numbers cited, measured dry at 2.77 wire/sky before and the fix's own
instrument after.

**Dispatch:** not yet. Dispatching now buys a reading we already know we
will re-take: weather not carried per ValuePanel sample (the exact
regime-mixing that produced the retracted §3 sentence), and three of
five ref cameras sampling zero lit-wall pixels, so two of three R0
orderings print `?`. Both repairs are small instrument work, and the ref
series is ONE landing old — re-aiming now is the cheapest regime change
it will ever have. Order to the builders, same dispatch:

1. `rain`/`wet` carried on every ValuePanel sample row (the sim already
   holds them — `frames.tsv` proves it — so this is an emit, not a join).
2. Re-aim `ref_1/ref_4/ref_5` (the `litnone@0` three) so all five test
   all three orderings; `?` stays the honest print for any that still
   miss.
3. The wires, avenue lint and yard-depth instrument ride the same build.
   Cadence rule (a) is satisfied by the wires.

**Cap: one dispatch cycle.** If the panel repairs are not green by the
next natural boundary, dispatch without them — the blind spots are named
in the landing record and the reading gets read with its caveats rather
than the visible fix waiting on instrument perfection.

## B. CLAUDE.md §3b — the exemplar commits the fault it teaches. CORRECT
BOTH; the SCOPE is intentional and stands.

The finding is CONFIRMED in code (see banner). Two corrections, ordered:

1. **The tool.** The coverage line prints the denominator of what
   `scan()` actually walked — static bodies in files belonging to
   scanned classes — and a second clause naming the drop with its
   reason: `N static bodies in M files outside partial-class scope, not
   scanned`. That is §3b's own cap-announcement sibling applied to the
   tool §3b cites. Its selftest gains the case: a non-partial-class file
   with a static body must NOT inflate the walked count.
2. **CLAUDE.md §3b.** House style — the false sentence is kept, quoted,
   so it cannot be re-derived: the `"354 static bodies walked"` exemplar
   gains a dated annotation that on 25 Aug the exemplar itself was found
   printing a denominator ~19x what it examined, because the count
   summed files the scan never entered. The rule stands; its exemplar
   was the disease wearing the cure's sentence. A denominator counts
   what was EXAMINED, not what exists.

**Scope ruling: intentional.** The tool's stated WHY is CS0120 born of
PARTIAL spread — a member invisible from the file being edited. A
single-file class shows its members on the same page; extending the scan
there answers a question nobody has been burned by. Do not extend it.
Fix what the sentence claims, not what the tool does.

## C. `NameOf`/`AddressOf`/`DistancePenalty` — ALL THREE TOGETHER, ONE
Core batch, taken as round-trip filler, not now.

**Together:** one idea, three implementations — splitting them is the
rule-1-third-corollary shape, and with the fallback taken at 96 of 97
junctions a partial fix churns nearly every gossip string TWICE. One
batch, one string change, one test update.

**When:** it is Core-only (fully testable locally) and touches the
information moat, but Jafar's sequence is visual first. It is exactly
what the never-wait-on-CI rule exists for: the named queue item is taken
while the panel-repair dispatch is in flight. Not before this commit,
not into this batch.

**The three red CoreTests:** before any expectation moves, the builder
states for each whether it pinned the FAULTY behaviour (fixture updates
with the fix) or a CONTRACT (in which case the change gets a second look
before landing). Updating a fixture that enshrined a bug is not moving a
gate; the sentence distinguishing the two goes in the commit.

## D. THE PLAN ORDER DOES NOT CHANGE — the landing CONFIRMS it and
sharpens the sequencing inside R0. Next is a measurement, and it is
already mostly ordered.

R0 (value structure) already precedes ground decals and surface history
(plan-replacement ruling, this file's predecessor record §1–2). What the
landing adds is proof at eye level, dry, with denominators: an 8x source
spread rendering flat at ~0.85 means ground surface history is invisible
BY MEASUREMENT, not by argument. Standing consequences, none new:
decals stay blocked; wall-side history stays exempt and may ride any
dispatch; no lever moves on one run.

**The next measurement, in order:** (1) the §A panel repairs — weather
per sample and the three re-aims — because the fork cannot be read
through a regime-mixed, third-blind panel; (2) the attribution batch
already in flight (per-material ray distance, gloss A/B, fogOff rung,
MeanTexLuma), whose items are the daylight-vs-grade discriminators; (3)
only if the builders show those cannot separate aperture from grade at
daylight levels does a new discriminator get specified — and its spec
requirement is written now: it must be a number that moves ONE way under
an aperture fault and the OTHER under a grade nonlinearity, or it is two
hypotheses reading one variable. The "grade model settled, aperture
value open" ruling stands unless that measurement contradicts it — the
fork the resident names open is the VALUE-path fork, and it is settled
by the landed series, not by re-litigating the model here.

## E. The three handed-up items, ruled separately.

1. **`aerial-metal-mirror` — INTO THE CURRENT BATCH.** Same cause, same
   derived material, one call site: this is rule 1's third corollary at
   the moment it applies — the fix works, the grep found the twin, the
   twin gets the fix before the batch closes. Measured by the same
   instrument family as the wires (mast/sky ratio or the wires' own
   emit extended). If it turns out to need more than applying the
   derived material, it drops back to a named queue item rather than
   growing the batch.
2. **`column-green-shared` — NAMED QUEUE ITEM, not this batch.** Three
   private near-blacks in one family is one idea in three
   implementations, but no fault is claimed and no still convicts it.
   The builder following the house idiom instead of inventing a fourth
   was right. Consolidate to one shared constant when that family is
   next touched; the queue row carries the three file names so it is
   findable.
3. **Verify's red path — FIX NOW, next non-CI builder slot.** One
   finding of nine shown, cut at 90 chars, no count, no `(+N more)`: the
   unannounced cap living inside the enforcement tool is the §3b/3b-
   sibling disease at the highest-leverage site there is — the first red
   it truncates buys a wrong diagnosis at commit time, which is rule 12
   territory (a blocked feedback channel outranks feature work). All
   findings print, or the cap announces itself with the count; no
   silent 90-char cut. Selftest both ways: N findings all shown, N>cap
   announces.

## NOT RULED ON, by name

- The ValuePanel numbers as a settled series — one landing; the panel's
  own record says suggestive, not proven, and that stands.
- Any lever: aperture, grade, albedo, smoothness, fog, skyline geometry.
  Nothing here authorizes one.
- The 560/29/14-of-88 arithmetic (mechanism verified in code; counts not
  re-measured by me — the resident's figures are quoted as the
  resident's).
- The `NameOf` replacement string design and whether the three CoreTests
  pinned bug or contract — that is the builder's stated-in-commit call,
  reviewed at its own batch.
- Which exact compositions the re-aimed refs should match — R1's spec
  and the builder's judgement, reviewed at the landing.
- Anything Jafar-facing; nothing here needs him.

<!--RULING spawn=2026-08-25T22:07:11Z-->
