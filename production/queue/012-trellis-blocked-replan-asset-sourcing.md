line: content (asset production)
spec: this file; ledger-v2/research/license-allowlist.md is law
acceptance: steps 3 and 4 of game-design/decision-2026-09-01-production-prep-sequence.md,
            namely the CC0 fetch-clean-tag route proven end to end on five items and
            then a first full overnight batch driven from the vignette bill of materials
max_sessions: 2
status: BLOCKED 2026-09-01. Hardware, not effort: the machine has an AMD
        Radeon and no NVIDIA card, and TRELLIS kernels are CUDA. Contingent
        on the bill of materials showing a gap the free libraries cannot
        fill; unblocks only by a purchase Jafar has not authorised, or by a
        different tool that runs without CUDA.

RE-POINTED 2026-09-01 by the production-prep-sequence ruling. The AMD
image-to-3D probe this task was originally about is DEMOTED to contingent:
it happens only if the bill of materials shows gaps the free libraries
cannot fill. Probing a capability before knowing whether we need it is the
kind of curiosity this week cannot afford.

TRELLIS CANNOT RUN ON JAFAR'S PC AND THAT IS A HARDWARE FACT.

The meshgen probe answered 3 of 8 requirements met, and the first failure is
not fixable by installing anything: the machine has an AMD Radeon RX 6700 and
a Parsec virtual adapter, no NVIDIA card at all. TRELLIS kernels are CUDA.
There is no CUDA on AMD. VRAM is a second, independent blocker at 9.98 GB
against upstream's stated 16 GB minimum.

So the plan sentence "image to 3D, local, free" is WRONG as written, and it
was written by me before the probe existed. The idea it serves survives: move
asset production off Claude tokens and onto the machine. The route has to
change.

WHAT IS STILL AVAILABLE, all allowlisted and all free:
- CC0 libraries: Poly Haven, ambientCG, the Sketchfab CC0 filter. Downloads,
  no GPU, and the pipeline's own local backend already answers YES (Blender
  4.2.1 present, 92 GB free). This is a real overnight batch: fetch, clean,
  LOD, tag, manifest.
- The existing imagegen pipeline, which already works on this hardware and
  produces reference images.

WHAT IS NOT AVAILABLE: Meshy and Tripo are paid tiers and no purchase is
authorised. A cloud GPU is a purchase. An NVIDIA card is a purchase. All
three are Jafar's decision and none may be assumed.

TWO OF THE PROBE'S NEGATIVES ARE STALE and must not be repeated as current.
It read game-design/agent-reports/machine-report.txt, last updated 26 August.
Since then MSVC was installed and verified 3 of 3 components by CI on that
same machine (production/d1-probe/msvc-setup.txt), so "no C++ compiler" and
"vswhere absent" are both out of date. "No bash" is PATH-scoped: git lives at
C:\Program Files\Git\cmd, so bash is at C:\Program Files\Git\bin and the CI
bootstrap finds it there every run.

FIX THE STALENESS TOO: the probe must print the AGE of every input it reads
and refuse to present a reading older than a few days as current. A machine
report that quotes six-day-old absences beside a fresh header is the same
provenance fault as a still committed by a build that rendered nothing.
