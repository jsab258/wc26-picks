line: infrastructure (instruments)
spec: game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md, Ruling 3
acceptance: a WATCHED row for the generated decals with a token not already in THIRD-PARTY.md; a THIRD-PARTY.md section per content-sourcing.md 4.6 (model, weights licence, training-data claim, review state, and that 14 images are review=pending); a fixture proving a generated PNG under the ambientCG row is REFUSED without that section; plus the printed sub-source reading below
max_sessions: 1
status: READY 2026-09-02. One instrument-builder. Instance THREE of the same fault.

`ledger/Assets/StreamingAssets/Decals/generated/` holds 14 model-generated
PNGs (Z-Image-Turbo, Apache-2.0 weights per `tools/imagegen/README.md`), every
one marked `review=pending` in its manifest, and all 14 are counted under the
ambientCG token because they sit inside a watched directory. `THIRD-PARTY.md`
has ZERO hits for "generated", "Z-Image" and "Apache".

NOTHING UNLICENSED SHIPPED and the outputs are unrestricted. The RECORD is
wrong, in exactly the way the OpenGameArt record was wrong, which makes this
the third instance of one fault: a watched row's token silently absorbing a
second source underneath it.

So the deliverable is not only the row. THE MECHANICAL FORM OF THE AUDIT THAT
FOUND IT, as a printed reading and NOT a gate: for every watched directory
row, list its immediate subdirectories that are neither a watched row
themselves nor named in that row's machine-written manifest. Print first. Gate
from what it prints, in a later item, once there is a series to argue from.
