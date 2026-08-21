#!/usr/bin/env bash
#
# The Editor-side character lines, extracted into the verdict.
#
# WHY THIS IS A FILE AND NOT FOUR LINES OF WORKFLOW. The Windows build step is
# within a couple of hundred characters of GitHub's hard expression-length
# limit, and `verify.py` refuses a commit that would push it over — so the
# inline version of this could not be dispatched at all. Anything that needs to
# grow belongs out here.
#
# WHY IT READS `unity.log` AND NOT `player.log`. The character audit runs inside
# `CiBuild` — the Editor, not the player — so grepping the player log for it
# finds nothing and reads exactly like "the audit never ran", which is a
# different fault with a different fix.
#
# WHY THE CAP SAYS SO. This was `head -3`, silently. One audit line plus one
# prefab line per body is four lines at two bodies and seventeen at eight, so
# the moment the cast grew the verdict showed Michelle, Remy and nothing else.
# I read that as "only two of the five bodies produced a prefab" and went
# looking for the bug; `bodyChoices=5`, in the same file, had been right all
# along. A cap nobody is told about is indistinguishable from a finding.
set -uo pipefail

LOG="${1:-build-log/unity.log}"
MAX="${2:-40}"
# `PropPrefab: ` joined 21 Aug — and then evicted the audit within one
# build. The prop pass logs ~90 per-model lines BETWEEN CharacterPrefab
# and CharacterAudit in CiBuild's order, so one shared cap kept the
# prefab lines, filled up on props, and cut every audit line — verdict
# keys `clips/humanoid/importerRan/lastImported` vanished and the key
# manifest caught it minutes after the build landed. One idea, two
# implementations: the summary line was protected from the cap and the
# audit was not. Each family now has its OWN grep and its own cap, so
# volume in one can never evict another.
CHAR_PATTERN="CharacterAudit: |CharacterPrefab: |CharacterMaterials: "
PROP_PATTERN="PropPrefab: "

if [ ! -f "$LOG" ]; then
  echo
  echo "CharacterAudit: (no $LOG — the Editor log is not here to read)"
  exit 0
fi

CHAR_TOTAL=$(grep -cE "$CHAR_PATTERN" "$LOG" || true)
CHAR_TOTAL=${CHAR_TOTAL:-0}
PROP_TOTAL=$(grep -cE "$PROP_PATTERN" "$LOG" || true)
PROP_TOTAL=${PROP_TOTAL:-0}

echo
if [ "$CHAR_TOTAL" -eq 0 ] && [ "$PROP_TOTAL" -eq 0 ]; then
  # THE DENOMINATOR, rule 3b. "No lines" and "the audit ran and had nothing to
  # say" are different states and a blank space cannot tell them apart.
  echo "CharacterAudit: (no line in $(wc -l < "$LOG") log lines — the audit did not run)"
  exit 0
fi

grep -E "$CHAR_PATTERN" "$LOG" | head -"$MAX"
if [ "$CHAR_TOTAL" -gt "$MAX" ]; then
  echo "CharacterAudit: (+$((CHAR_TOTAL - MAX)) more character lines not shown)"
fi
# Props: a handful of per-model lines for spot-reading, then ALWAYS the
# summary — it prints last in the log, exactly where a cap bites.
grep -E "$PROP_PATTERN" "$LOG" | head -8
if [ "$PROP_TOTAL" -gt 8 ]; then
  echo "PropPrefab: (+$((PROP_TOTAL - 8)) more prop lines not shown)"
fi
grep -E "PropPrefab: [0-9]+ prefab" "$LOG" | tail -1
exit 0
