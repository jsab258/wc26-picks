# tools/meshgen - the local prop pipeline

**LIVE. Verified 2026-09-01.** The code is the source of truth; this file
exists because `trellis_mesh` refuses with a sentence pointing at it, and a
refusal citing a document that does not exist is its own small fault.

## What it does

Grinds a named batch of prop specs into cleaned, measured, LOD'd,
licence-tagged GLB meshes plus a manifest. Three stages, and only some of them
can run on any given machine:

1. **IMAGE** - `tools/imagegen` makes the reference image. Only the `trellis`
   backend needs this.
2. **MESH** - TRELLIS (microsoft/TRELLIS, MIT) turns that image into geometry.
   NVIDIA only. Never yet run by anyone on this project.
3. **CLEAN** - Blender headless measures, normalises, decimates to an LOD chain
   and exports GLB. Vendor neutral, and the only stage the `local` backend
   uses.

Stdlib Python only. Nothing is installed into Jafar's Python, no model API is
ever called, and no run needs a person present.

Two batches ship in `specs/`: `props-local-01.json` (37 existing repository
meshes, `local` backend, Blender only) and `props-trellis-01.json` (12 new
props, `trellis` backend, blocked on hardware).

## What to click

`1 MAKE THE PROPS.bat` - one double click, then walk away. It pulls the
project, runs both probes, decides which backend this PC can run, stops with a
list if it can run none, and otherwise works through the batch skipping
anything already done.

`2 JUST LOOK AT THIS PC (one minute).bat` - the same probe with the making
switched off. It makes nothing, downloads nothing and installs nothing. It
writes the machine report and says what could run here.

Kill switch: create the file `production\STOP` in the repository. It is checked
between every item and every stage, and everything finished so far is kept and
counted.

Command line equivalent, for anyone not on Windows:

    python3 tools/meshgen/meshgen.py probe --repo . --machine <machine.json> --tools <tools.json>
    python3 tools/meshgen/meshgen.py run   --repo . --spec tools/meshgen/specs/props-local-01.json
    python3 tools/meshgen/meshgen.py verify --repo .
    python3 tools/meshgen/meshgen.py --selftest
    python3 tools/meshgen/meshgen.py --series ledger/Assets/Props

## What the probe checks

It reads two files written by the probes (`machine.json` from imagegen's
hardware probe, `tools.json` from `probe-tools.ps1`) and reports every
requirement with what it wanted, what it found and what would fix it. A probe
that did not run is reported as NOT MEASURED, not as an empty machine.

**local backend:** Blender on PATH or in a standard install location, and free
disk for the exports.

**trellis backend:** an NVIDIA GPU; at least 16 GB VRAM; the CUDA toolkit
(`nvcc`); MSVC to build the CUDA submodules on Windows; a POSIX shell, because
upstream ships `setup.sh`; Python 3.8+; git, for a recursive submodule clone;
and free disk for the environment, the model and the build trees.

On Jafar's PC that comes back CANNOT RUN, and the numbers behind that are in
the code header: an AMD Radeon RX 6700 with 9.98 GB and no Visual Studio. Four
independent blockers, each sufficient alone.

## What fails, and what to do about it

Exit codes, matching the paragraphs the .bat prints:

| code | meaning | what to do |
|---|---|---|
| 0 | done | read the manifest counts, not the word "done" |
| 2 | not enough free disk | the number is in the log |
| 3 | stopped during setup, nothing made | the reason is in the log |
| 4 | the run happened and every item failed | send back the last 20 lines |
| 5 | cannot run here, nothing was made | the missing pieces are listed with fixes; this is a real answer, not a crash |
| 6 | stopped by the kill switch | delete `production\STOP` |
| 7 | the licence gate refused | something is untagged or names a banned tool; each one is named |
| 8 | the batch spec is unusable | usually a half updated project; run it again |

**"Blender is not on this machine"** - install it from blender.org. Free, no
account, and it is the only thing the `local` backend needs.

**"TRELLIS is not installed"** - this pipeline deliberately does not install
it. Upstream is a conda environment plus CUDA submodules that must be COMPILED,
and an unattended build that half succeeds is worse than none. Upstream's own
README, read 2026-09-01, says "The code is currently tested only on Linux" and
sends Windows users to issue #3, "not fully tested", and it says "An NVIDIA GPU
with at least 16GB of memory is necessary". Installing it is: clone with
`--recurse-submodules`, then run upstream's `setup.sh` in a POSIX shell inside
a conda environment, then put a `ledger_runner.py` at the root of that checkout
taking `--image`, `--out` and `--seed`. That is a decision with a person
present, on a machine that passes the probe, and nobody here has done it.

**`ship_ok=false` in the manifest** - the output exists and may not ship. TRELLIS
is the live case: the allowlist row says MIT flat, while upstream's README names
submodules under other licences (diffoctreerast, from INRIA
diff-gaussian-rasterization; a modified FlexiCubes under an NVIDIA source
licence), and the mesh extraction path is the one that touches them. The
allowlist's PROCESS clause 2 requires a decision record citing the weights
licence before that ships.

To authorise a tool, a decision record under `game-design/decision-*.md`,
`ledger-v2/respec/decision-register/*.md` or `production/specs/decision-*.md`
must carry the marker `TOOL-DECISION: <tool>` **alone on its own line, starting
at column 0**. Discussing a tool authorises nothing, deliberately: the previous
version of this gate accepted any decision file mentioning the tool near the
word "licence", and the director's review OF THIS PIPELINE would have
authorised TRELLIS the moment it landed. Markers inside fenced code blocks are
ignored, so a document explaining the format cannot authorise anything either.

## The selftest

`python3 tools/meshgen/meshgen.py --selftest` runs every check in this
directory that can run without a GPU, Blender, Windows or PowerShell, accepting
case first in every section. It ends by naming what it could NOT cover: TRELLIS,
Blender and both .bat files never execute in this container, and the first run
on Jafar's PC is their accepting case.
