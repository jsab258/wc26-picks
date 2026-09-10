# Third-party models: The Base Mesh

37 of the 39 .glb in this directory are CC0 1.0 from The Base Mesh
(https://thebasemesh.com), fetched via the M3-org GitHub mirror
(https://github.com/M3-org/base-meshes) by tools/props/fetch_visual.py.

37 file(s) at last fetch.

## The 2 that are NOT third party, added 2026-09-09

This heading exists because the sentence above used to read "Every .glb in this
directory", and the first in-house mesh to land here made that a false
licensing claim. The licence allowlist
(ledger-v2/research/license-allowlist.md) says every asset carries a licence
tag and an untagged asset fails the gate, so the two below are tagged here
rather than left to be covered by a row that does not cover them.

- `fascia_cornice_01.glb`
- `fascia_console_01.glb`

LEDGER's own work. Authored 2026-09-09 by
`production/art/fascia-01/author/make_fascia_mouldings.py`, which writes the
glTF from two explicit (depth, height) profile point lists in that file.
Nothing was fetched, nothing was purchased, no model weights were run, no
third-party geometry, texture or byte is in either file: both contain only
positions, normals, UVs and indices computed from those numbers, plus one
untextured material with no image. The spec that names every dimension and its
source is `production/art/fascia-01/01-SPEC-fascia-package.md`.

WHAT WOULD MAKE THIS SECTION FALSE, stated so a later reader can check it
rather than trust it: a profile traced from somebody else's drawing, or a
texture or UV set imported from anywhere. Neither has happened; the profiles
are dimensioned from British shopfront design guidance (cited in the spec,
prose guidance rather than copied geometry) and from the brick module the
street's own scene file already carries.
