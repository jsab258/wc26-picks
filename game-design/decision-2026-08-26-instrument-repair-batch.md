# DIRECTOR RULING — instrument-repair batch: series ordering, gate-detail ceiling, lint-red semantics, fixture unpin (26 Aug 2026)

> **STATUS — LOG, 2026-08-26. NOT CURRENT after the ordered `confabs`
> re-read lands and after the fixture-pin sweep reports its count.**
> Trigger: builder-batch review before commit (mandatory). Verified this
> session, not quoted: `run_corpus()` reads the FULL history with no `-N`
> and routes unplaceable runs to a NAMED bucket with its own cap notice
> (`tools/gates.py:181-248`, `:170-178`); the roadmap-history correction
> is in place, quoted not deleted (`roadmap-history.md:2932-2938`);
> `_lint_red` keys on the structural test — red without a `.cs:` line is
> "refused to look", not a finding — and its comment carries the measured
> seven-tool series including the exit-1 `lint-namespace` case
> (`ledger/verify.py:60-99`); the fourth real-asset pin and its verbatim
> re-derivation trap are recorded in `ref-bench.py` (`:254-260`,
> `:1556-1563`); the twin `-400` is confirmed still present at
> `verdict-keys.py:247`, exactly as reported. NOT re-measured: the
> 228-of-329 misordering count, the 18.7-vs-10.7 adjacent-step figures,
> the 73-red/22.6% `jobRan` history, the 12x placement timing — method
> and printed series accepted as builder-measured, spot-checked for
> internal consistency only.

## A. COMMIT — APPROVED.

Verify green with the counts named (35 footer fixtures, 113/113 docs,
4104 CoreTests, 108 ref-bench checks), nothing under
`ledger/Assets/Scripts`, so no build dispatch rides on this. One
reviewed commit for the whole batch. Two properties tipped it beyond
"green, therefore yes": every repair made a guard STRICTER or a
denominator honest (ceiling 18→31 because the tool could finally see;
`356 of 356 within 2403; unplaced=0; expect all 356` where the old line
measured its own blind spot), and no bound moved to make anything
quieter. The self-corrections — two builders catching their own probe
faults before the number reached a report, and the resident naming its
own forwarded false claim about `lint-unreached` — are the tier system
working, and the `lint-unreached` correction is the sharper one: a full
line of healthy-shaped zeros is rule 3b's disease wearing a pass, worse
than silence, and it is now on the record correctly.

## B. THE `confabs` REGIME-BREAK CLAIM — ORDER THE MEASUREMENT, DO NOT RE-LITIGATE PROSE.

The claim decomposes, and its halves have different exposure. The
DISTRIBUTION half (1–13 old band, 29–74 new band, all-time median 34
describing neither) is order-independent and stands. The BOUNDARY half —
where the break sits in the series — was derived from a corpus that was
70% sha-ordered past position ~107, so it is exactly the class of
order-dependent history the repair puts at risk. The lesson the
paragraph teaches ("no statistic survives a regime change; print the
series") does not depend on either half and stands regardless.

Ruling: a tier-2 verifier (measurement-auditor) runs the REPAIRED
`gates.py --series confabs` and reports whether the two bands and the
boundary hold on true commit order, cross-checked against the commit
that changed the conversation rule — the break is a code event, so the
boundary is checkable against a sha, not just eyeballed. If the reading
contradicts CLAUDE.md's sentence, the correction touches CLAUDE.md and
therefore comes back through the next mandatory director spawn, folded
per the one-decision-one-spawn rule — quoted-and-corrected in place, not
silently rewritten. Nobody quotes the break's LOCATION until that lands.
The re-read is one command on a tool this batch just fixed; there is no
cheaper decisive measurement available and no excuse to skip it.

## C. NAMED TWINS — QUEUED WITH NAMES, ONE PROMOTED.

1. **`verdict-keys.py:247`'s `-400`** goes to the TOP of the next
   instrument batch, not into this one. It is the same fault class just
   fixed, `place_runs` is already importable, and "latent, works today"
   is precisely the state the gates.py window was in before the repo
   grew past 400 commits. It is not a red and does not jump the batch
   boundary — but it does not wait behind anything discretionary either.
   Rule 1's third corollary found it; leaving it unnamed on a queue
   would be the corollary half-applied.
2. **Three copies of the VALUE grammar.** The consolidation target is
   already named in the code (`tools/verdictfmt.py`, per the comment at
   `gates.py:278-279`). Queue item, instrument-builder, ordinary
   priority. The two `verdict-read.py` copies currently agree with the
   canonical one; the risk is drift, not present fault.
3. **No machine-readable regime marker** — this one I promote, because
   it bears on a standing ruling: a regime change no statistic survives
   must be legible to the reader of the series, and today all eight
   declarations are C# comments, which is a claim with no test attached
   in a project whose file this is. The DESIGN is the builder's (a
   verdict key, a ledger line — instrument-builder specs it under
   instruments.md's grammar rules); the REQUIREMENT is ruled now: a
   declared regime change must be visible to `--series` output without
   opening source. Queue it named, next instrument batch.

## D. THE FIXTURE-PIN CLASS — SWEEP ONCE NOW; PROMOTION TO A STANDING LINT IS CONDITIONAL ON THE COUNT.

Both framings in the question are true and neither decides it. It WAS a
discipline failure — three unpins in one night, none swept, corollary on
the books. But this file's whole argument is that discipline with a
landed failure series gets a mechanism: the corollary was written into
three commit messages on 4 August and walked into three times that same
night. Four instances of one class, the fourth blocking every commit, is
a landed series.

Ruling in two steps, cheapest decisive measurement first:
1. A tier-2 sweep NOW enumerates every remaining fixture assertion
   pinned to a mutable live artifact (anything under
   `game-design/sim-shots/` or regenerated asset output referenced from
   a selftest's ACCEPTING case). Fifth instance found → fixed in the
   sweep's wake, per the corollary.
2. If the sweep finds ANY hit beyond the four known, the check becomes a
   standing lint, written to instruments.md's own standard: the live
   repository post-sweep is the accepting fixture, a synthetic pin the
   rejecting one, both watched. If it finds zero, the one-time sweep
   plus this recorded rule suffices — a standing lint guarding an empty
   class is maintenance without a payer, and the decision is recorded
   here so the NEXT instance re-opens it with a series of five rather
   than a fresh argument.

The underlying rule is ratified as standing either way: **an accepting
fixture may not assert values of an artifact the project intends to keep
improving.** The live tree is the accepting case for "does the tool run
today"; a frozen copy is the accepting case for "are the numbers right".
`ref-bench.py` now says this verbatim precisely so nobody re-derives the
pin; that sentence is the rule, and this ruling makes it apply beyond
that one file.

## NOT RULED ON

- The truth value of the `confabs` regime-break boundary — a measurement
  is ordered (B); concluding before it lands would be asserting what I
  have not checked.
- The 18 pre-existing bare gates behind the gate-detail ceiling: the
  ratchet correctly refuses a 14th NEW one and demands nothing of the
  stock; each of the 18 needs its own diagnosis and that work is not
  scheduled by this ruling.
- The regime-marker MECHANISM (verdict key vs. ledger line vs. anything
  else) — requirement ruled in C.3, design deliberately left to the
  builder spec.
- Whether order-dependent conclusions OTHER than the `confabs` claim
  were drawn from the scrambled window. The report flagged only the one;
  a broader audit of past series-based conclusions is a possible tier-2
  task and I am neither ordering nor dismissing it here — B's landing
  will say whether the class warrants it.
- Anything about game behaviour, the visual bar, or dispatch: nothing in
  this batch touches `ledger/Assets/Scripts` and no build question is
  open on it.

<!--RULING spawn=2026-08-26T03:10:21Z-->
