line: infrastructure (instruments)
spec: this file
acceptance: .glb in ASSET_SUFFIXES; the 37 base-mesh files produce a line rather than silence; the stray-file sweep sees .glb anywhere in the repo; a fixture proves an unattributed .glb is REFUSED
max_sessions: 1

`tools/attribution-check.py` line 106 lists the suffixes it sweeps for.
`.glb` is not among them. So the 37 meshes under
`ledger/Assets/Props/base-mesh` produce NO LINE AT ALL, neither ok nor fail,
and the "The Base Mesh" token is never actually checked. The stray-file
sweep is equally blind to a .glb anywhere in the repo.

THE COMMENT DIRECTLY BESIDE THAT SET IS THE WHOLE LESSON. It records that
Radiance and OpenEXR were added on 24 August "BECAUSE THEY WERE MISSING AND
THE CHECK WAS SILENT ABOUT IT". The identical fault, found once, fixed for
two formats, and nobody swept the set for a third. That is rule 1's third
corollary exactly: when you fix a bug, grep for the same bug. An allow-list
silently discards everything nobody thought of, and it looks identical to a
clean result.

It matters now rather than in principle. The vignette bill of materials has
a model-class line (a period car), and any model landing today is invisible
to the one sweep whose job is noticing other people's files in this
repository. A licence check that cannot see the asset class we are about to
start fetching is not a licence check.

Fix the set, and while there, sweep the set itself against what the project
actually holds rather than adding one suffix and moving on.
