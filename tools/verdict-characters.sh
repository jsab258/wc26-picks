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
# `PropPrefab: ` joined 21 Aug: `furniture=0` was diagnosed BLIND because
# the prop pipeline's own log lines never reached the verdict — the one
# readable channel (rule 12). The summary line and per-model lines both
# match the prefix.
PATTERN="CharacterAudit: |CharacterPrefab: |CharacterMaterials: |PropPrefab: "

if [ ! -f "$LOG" ]; then
  echo
  echo "CharacterAudit: (no $LOG — the Editor log is not here to read)"
  exit 0
fi

TOTAL=$(grep -cE "$PATTERN" "$LOG" || true)
TOTAL=${TOTAL:-0}

echo
if [ "$TOTAL" -eq 0 ]; then
  # THE DENOMINATOR, rule 3b. "No lines" and "the audit ran and had nothing to
  # say" are different states and a blank space cannot tell them apart.
  echo "CharacterAudit: (no line in $(wc -l < "$LOG") log lines — the audit did not run)"
  exit 0
fi

grep -E "$PATTERN" "$LOG" | head -"$MAX"
if [ "$TOTAL" -gt "$MAX" ]; then
  echo "CharacterAudit: (+$((TOTAL - MAX)) more character lines not shown)"
fi
# THE PROP SUMMARY, ALWAYS. It is printed AFTER ~90 per-model lines, so the
# cap above cuts precisely the one line that says how many prefabs were
# written and how many files would not import — the number `furniture=`
# needs beside it. Grepped again on its own so the cap cannot eat it.
grep -E "PropPrefab: [0-9]+ prefab" "$LOG" | tail -1
exit 0
