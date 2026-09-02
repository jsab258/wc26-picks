line: infrastructure (instruments)
spec: game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md, Ruling 2 and Ruling 9
acceptance: every path under CLAUDE.md's "Where the rest of this file went" exists and carries at least one "moved verbatim from CLAUDE.md" marker, with the per-file marker count printed; docs-check walks the casebooks, the three carried framework docs and legacy/ for the banner and verified-date rules, printing its walked count beside the game-design/ one; the 400-line cap is NOT applied to a casebook and the code says why; accepting case the live tree, rejecting case a pointer to a path with no marker
max_sessions: 1
status: READY 2026-09-02. One instrument-builder. This is the condition the CLAUDE.md cut landed UNDER, not a nice-to-have.

The cut is safer than the file it replaced and IT IS NOT YET SAFE. It is
quietly undone if either of two things happens, and tonight neither has an
instrument:

1. THE POINTERS ROT. CLAUDE.md now ends in a list of paths. A pointer to a
   document that does not carry the thing pointed at is worse than no
   pointer, because it reads as coverage. The project's only data point here
   is L23: an enforcement clause pointed at a superseded file for a day and
   nothing announced it.
2. THE CASEBOOKS DECAY. `tools/docs-check.py` walks `game-design/` only and
   prints `ledger-v2/` as NOT WALKED, so the three new casebooks, the three
   carried framework documents and `legacy/` are under no banner rule, no
   verified-date rule and no check of any kind.

Two checks, ONE function in `ledger/verify.py`.

(a) For every path listed under CLAUDE.md's `## Where the rest of this file
went`: the path exists, and it carries at least one `moved verbatim from
CLAUDE.md` marker. Print the marker count PER FILE, not a total, so a
destination that received one passage and a destination that received six
do not read alike.

(b) Widen `docs-check.py` to walk `ledger-v2/studio-v2/casebook-*.md`,
`operations.md`, `organization.md`, `runner.md` and `legacy/`. Print the
walked count beside the existing `game-design/` count so the denominator
says which tree it describes. DO NOT apply the 400-line LIVE-plan cap to a
casebook: they are LOG-sized by design, that is the whole point of moving
the incidents there rather than deleting them, and the code should say so in
words rather than leaving the next reader to wonder why the cap is absent.

Accepting case: the live tree. Rejecting case: a pointer to a path with no
marker.
