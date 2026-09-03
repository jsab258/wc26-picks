line: infrastructure (documents)
spec: game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md, ruling 2(b)
acceptance: `OLD_RE`, the definition of the retired em-dash banner at banner position, lives in `tools/docs-check.py`; `tools/migrate-status-banner.py` imports it from there; deleting the migration script leaves docs-check and verify green; docs-check.py carries zero literal em-dash characters, the Python unicode escape for U+2014 (backslash, u, 2014) being the only permitted spelling; both selftests and the live corpus pass unchanged
max_sessions: 1
status: READY 2026-09-03. instrument-builder, small.

## Why

One implementation of the retired form is right. The owner is wrong: the
permanent checker, wired into verify through `docs_shape`, imports its
definition from a one-shot migration script, so deleting the script after it
has done its only job turns docs-check red (exit 4) and verify with it. A
permanent instrument must not depend on a transient tool. The migration
script's header now says it may not be deleted; this item makes that sentence
unnecessary.

## While the file is open

`tools/docs-check.py` is the checker that refuses an em-dash banner and it
prints an em-dash in the first line of its own output (line 121), in its NOT
WALKED line (213), in three check strings (181, 189, 190) and in seven
comments: twelve lines. Constitution law 11 corrects old text
opportunistically, and the file being open for the import inversion is the
opportunity. Replace each with a colon, a comma or a full stop. The fixtures
must not change: the rejecting fixtures already spell the character as the
Python unicode escape for U+2014 (backslash, u, 2014), and that stays,
because the refusal has to name the character it refuses. The regex in
`OLD_RE`, once moved, is spelled the same way, so the checker's source
carries no literal em-dash at all.
