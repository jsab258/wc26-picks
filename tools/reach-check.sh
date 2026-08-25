#!/usr/bin/env bash
# THE ONE INVOCATION OF ReachCheck. There is no second copy of this argument
# list, and there used to be two.
#
# WHY THIS FILE EXISTS, dated 25 Aug and not hypothetical. `ledger/verify.py`
# and `.github/workflows/ledger-core-tests.yml` each spelled the reach check
# out by hand. On 17 Aug `--also ledger/Assets/Editor` was added to the
# verify.py copy — the Editor layer is a real consumer, `CharacterPrefab`
# calls Core on every Windows build — and NOT to the workflow copy. From that
# day the two readers were looking at different worlds, and the local one was
# green while CI was red on the same tree.
#
# It cost four consecutive dark CI runs: `Proportion.TryNeckFraction` and
# `Proportion.IsCaricature` landed on 17 Aug called ONLY from
# `Assets/Editor/CharacterPrefab.cs`, so the workflow's smaller scan reported
# them "tested, unwired" and failed — a correct check reading an incomplete
# world, which is rule 3, suspect the instrument first.
#
# One idea, one implementation. Both callers run this file.
#
#   tools/reach-check.sh            # the check
#   tools/reach-check.sh --quiet    # extra flags are forwarded
set -u
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
L="$REPO/ledger"

exec dotnet run -c Release --project "$L/ReachCheck" -- \
  "$L/Assets/Scripts/Core" "$L/Assets/Scripts/Game" \
  --tests "$L/CoreTests" \
  --tests "$L/SimHarness" \
  --tests "$L/BalanceLab" \
  --tests "$L/BarkGen" \
  --tests "$L/Tier2Gen" \
  --also  "$L/Assets/Editor" \
  --allow "$L/ReachCheck/allow.json" \
  "$@"
