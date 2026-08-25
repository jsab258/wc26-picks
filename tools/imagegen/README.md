# Make the pictures — read this in thirty seconds

**Double-click `1 MAKE THE PICTURES.bat`. That is the whole thing.**
It asks you nothing. Leave it running and come back.

| | |
|---|---|
| **First run takes** | 20 min to a couple of hours — most of it is a 7–10 GB download that happens once and resumes if you stop it |
| **Installs into** | `%USERPROFILE%\ledger-imagegen` — outside the repo. Nothing system-wide, nothing in Program Files, nothing added to your Python, your Unity or the speech setup |
| **To undo everything** | delete that one folder |
| **Costs** | nothing. No account, no login, no token, no purchase |
| **You get back** | 12 PNGs + `manifest.json` in `ledger\Assets\StreamingAssets\Decals\generated\`, and `game-design\agent-reports\machine-report.txt` |

**Send back `machine-report.txt`.** It says what your graphics card is, and
that is what picks the model for the next run — we genuinely do not know your
GPU, so this run is also the measurement.

### What it makes

The signage the street already asks for and currently draws as blank coloured
rectangles: four shop fascias (Mickey's, Rita's pawnshop, the fish market, the
steam laundry), three sign faces using the exact words already in the code
(MARQUEE, OPEN ALL NITE, BATHS), three notices and posters, and two grimy wall
textures. Meridian, British port town, late-analog 80s/90s.

### The model

**Z-Image-Turbo, Apache-2.0** — free for commercial use, outputs unrestricted,
no terms to accept. It runs through stable-diffusion.cpp (MIT), a single
self-contained binary that talks to your card through Vulkan, so it works on
AMD, Intel and NVIDIA alike and needs no CUDA and no drivers installed.

**If any download ever asks for a login, the script stops and says so.** We do
not use accounts and do not buy anything — that is your call, not ours.

### The two rules baked into every prompt

1. **No real person.** No faces, no likenesses.
2. **No real trade marks or brand livery.** Invented in-world names only.
   Every 1980s British advert is still in copyright, and trade mark was the one
   claim Getty actually won in *[2025] EWHC 2863 (Ch)*.

They live in `prompts.json` as data, and `imagegen.py` refuses to build a
prompt that has lost them. **Nothing ships unreviewed** — every image is
`review: pending` in the manifest until a human has looked. If one comes out
with something that looks like a real company or a real face, say so and it
gets binned.

### If it goes wrong

It fails loudly on purpose. Whatever it prints in that window is the diagnosis
— send back the last 20 lines plus `machine-report.txt`. "It did nothing" is
the one outcome the script is written to make impossible.

**And it does not believe the generator when it says it worked.** There is a
known open bug in stable-diffusion.cpp — issue #1031, this exact model on this
exact backend — where it writes a completely blank picture and reports success.
Every image is opened and measured after it is made; a blank one is reported as
FAILED, is not counted, and is renamed `<name>.BLANK.png` so it cannot be
mistaken for a delivered image. If you see that, nothing is wrong with your
machine — send it back and the next thing to try is named in the report.

### For whoever picks this up next

- `probe-machine.ps1` — reads the machine, writes `machine.json`, never guesses.
- `imagegen.py` — plan, fetch, generate, manifest. **Stdlib only, no pip.**
  `python imagegen.py --selftest` runs 49 checks with no GPU and no network,
  including both halves of the blank-image check (a varied image accepted, a
  uniform one rejected) and both halves of the gate (a 404 falls through to the
  next candidate, a 401/403 stops the run).
  `python imagegen.py --series <dir>` prints the blankness measurement over
  every PNG under a directory — the series the bound was read off.
  `python imagegen.py plan --machine machine.json` prints the plan and
  downloads nothing.
- `prompts.json` — the batch, the style block, the content rules.
- Next rung if the lettering disappoints: FLUX.1-schnell (also Apache-2.0,
  **ungated** — *dev* is the gated one, *schnell* is not; ~3x the download).
  stable-diffusion.cpp runs both; it is one field.
- Next rung for the runtime on an AMD card: the `win-rocm-7.14.0-x64` build in
  the same release. Named, deliberately not wired, and not measured by anybody
  here — it is what to try if Vulkan turns out slow or wrong.
