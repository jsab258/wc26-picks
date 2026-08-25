# Local image generation — the one-click build

> **STATUS — LOG, 2026-08-25.** A build account, true on the day it was
> written and **NOT CURRENT** thereafter: nothing below has been run on
> Windows or on a GPU. The first real run is the measurement, and it will
> date this file. Deliverables: `tools/imagegen/`.
>
> **Updated the same day with section 7** — an independent licence-and-risk
> check (`game-design/research/imagegen-licence-check.md`) found five faults,
> three of them able to waste a whole hour of Jafar's time, and all five are
> now fixed. The untested list in section 4 has NOT shrunk on account of it.

---

## 0. What was asked and what exists

Jafar approved rung 4 of the image ladder personally — a permissively licensed
model, run locally on his Windows PC — and set the effort budget in his own
words: *"yes but minimal effort. ideally just a 1 click bat"*. The hard
constraint is **his time**, not our cleverness. He double-clicks once; every
other decision is ours to make inside that click.

Shipped, none of it committed:

| file | what |
|---|---|
| `tools/imagegen/1 MAKE THE PICTURES.bat` | the one click |
| `tools/imagegen/probe-machine.ps1` | reads the machine, writes `machine.json` |
| `tools/imagegen/imagegen.py` | plan → fetch → generate → manifest. Stdlib only |
| `tools/imagegen/prompts.json` | the batch, the style block, the content rules as DATA |
| `tools/imagegen/README.md` | thirty seconds, for him |

---

## 1. The decision that shaped everything: we do not know his GPU

`game-design/live-speech-latency.md` line 171 records it in the file's own
words — *"The dev machine has an **AMD GPU** — Jafar has said so twice and it
is recorded here so it stops being re-asked"* — and, two lines later, *"CUDA is
not a lever for this machine"*. That is the strongest evidence available and it
is still not a model number or a VRAM figure.

So the design does not branch on an assumption, it branches on a
**measurement**, and the measurement is step one of the click:

- `probe-machine.ps1` uses CIM, not `wmic` (removed from current Windows 11).
- It reports **two** VRAM numbers per adapter and refuses to reconcile them.
  `Win32_VideoController.AdapterRAM` is a uint32: every card above 4 GB reports
  exactly `4294967295`, which is indistinguishable from a real 4 GB card. The
  registry's `HardwareInformation.qwMemorySize` is 64-bit and right. `plan()`
  treats a bare `4294967295` as **UNKNOWN**, not as 4 GB, and says so in the
  report — planning a 6.5 GB quantisation against a uint32 ceiling is the exact
  shape of a number read as a measurement when it is an artefact of its
  container.
- Every probe step is individually wrapped, and a failure writes a note into
  `probe` rather than an empty field. **"No GPU found" and "the probe crashed"
  look identical downstream and only one of them means buy a graphics card**,
  so the report prints both sentences on that line.

The report lands at `game-design/agent-reports/machine-report.txt` — inside the
repository, so we read it by pulling, with no copy-paste asked of him. If the
`.bat` cannot find `CLAUDE.md` (it looks two levels up, then at
`%USERPROFILE%\wc26-picks`), it says so and writes to the workspace instead.

---

## 2. The stack, and why it is not the obvious one

**The obvious build is Python + PyTorch + diffusers + a CUDA wheel.** On this
machine that is: a multi-GB torch install, a vendor-specific wheel index, a
`torch-directml` variant pinned to an old torch for the non-NVIDIA path, and a
pip step that can fail in a dozen ways on a machine we cannot see. It also
lands on top of an existing speech environment that took days to stabilise.

**What is shipped instead:** `stable-diffusion.cpp` (leejet, **MIT**), a static
C++ binary that reaches the GPU through **Vulkan** — the one vendor-neutral GPU
path on Windows, which is the same argument that made DirectML the speech
baseline. Consequences worth stating:

- **No pip, no venv, no torch, no CUDA toolkit, no driver install.** Nothing is
  installed into his Python; the driver script is **stdlib only**, so any
  Python 3.8+ runs it and the environment cannot be disturbed.
- Everything lives in `%USERPROFILE%\ledger-imagegen`, **outside the
  repository** — a 7–10 GB drop can never be committed by accident, and undo is
  deleting one folder.
- The release read from GitHub on 25 Aug (`master-827-97d2990`, published 19
  Aug 2026) ships `win-vulkan-x64` at 38 MB, `win-cuda12-x64`, and
  `win-cpu-x64` at 24 MB. **The plan takes CUDA on NVIDIA** (it is the best
  available result on that hardware) **and Vulkan on everything else**, with a
  fallback chain `primary → vulkan → cpu` where each attempt prints why it was
  abandoned.

### The model

**Z-Image-Turbo (Tongyi-MAI), Apache-2.0.** 6B DiT plus a Qwen3-4B text
encoder, 8 steps, cfg 1.0. stable-diffusion.cpp's own wiki has a page titled
*"How to Use Z-Image on a GPU with Only 4GB VRAM"*, which is the property that
matters when the VRAM figure may come back unknown.

| artefact | source | licence |
|---|---|---|
| diffusion model | `leejet/Z-Image-Turbo-GGUF` (Q2_K 2.6 GB → Q8_0 6.6 GB) | Apache-2.0 |
| text encoder | `unsloth/Qwen3-4B-Instruct-2507-GGUF` Q4_K_M (~2.5 GB) | Apache-2.0 |
| VAE | `Comfy-Org/z_image_turbo` `split_files/vae/ae.safetensors` (335 MB) | Apache-2.0 |
| runtime | `leejet/stable-diffusion.cpp` release zip | MIT |

**FLUX.1 [schnell] was the brief's candidate and is the named next rung, not
the pick.** Its licence checks out — Apache-2.0, commercial use explicit — but
it is 12B plus a 4.7 GB T5-XXL text encoder, roughly three times the download,
for a machine whose VRAM we do not know. It stays in the code as a one-field
switch if Z-Image's lettering disappoints.

### A gate, and the honest way round it

stable-diffusion.cpp's docs send you to `black-forest-labs/FLUX.1-schnell` for
the VAE. **That repository is gated behind a Hugging Face login and an
acceptance click.** We do not use accounts. The file used instead is the
**ungated `Comfy-Org` mirror that ComfyUI's own Z-Image template uses**, and
the autoencoder is Apache-2.0 in both places — so this is a different
distributor of the same permissively licensed file, not a way round a licence.
It is written into the code comment, the manifest and this file so nobody
re-derives it, and **it is Jafar's call to overrule.**

Where a gate cannot be side-stepped, `fetch_one` prints `GATED`, the URL, and
a fixed paragraph: *we never use accounts and never purchase; nothing has been
worked around; send this line back.* It then **stops.**

---

## 3. The batch is content, not a demo image

Twelve items, and every one of them is a hole the street has today.
`WorldBuilder.BuildNeon` iterates `NeonSigns` as `(placeId, colour, word)` and
builds **a coloured emissive cube** — the word is in the data and nothing draws
it. `Dressing.HasFascia(Premises)` decides which buildings carry a signboard
band and what sits on it is a tinted plate.

- **4 fascias** — Mickey's (the `bar_door` pub), Rita's pawnshop, Hook Street
  fish market, the steam laundry. Every name is a real `HookMap` place.
- **3 sign faces** — `MARQUEE`, `OPEN ALL NITE`, `BATHS`, copied **exactly**
  from the `NeonSigns` table, so the output binds to an existing call site
  rather than to a folder nobody reads.
- **3 notices and posters** — a harbour board notice, a flyposted gig bill, a
  ferry timetable behind scratched perspex.
- **2 grimy walls** — soot-blackened stock brick with salt bloom; blistered
  render with rust bleed.

Each record carries `binds_to`, naming the code site it is for. **That is the
half that decides whether this was a fetch or a feature** — files on disk with
a manifest are not content in the game, and this project has 150 of 213 fetched
models named by no line of code to prove it. Wiring `BuildNeon` to sample these
PNGs is the next task and it is not in this drop.

### The content rules are data

`prompts.json` carries `content_rules.rules_clause` and a 45-token
`forbidden_tokens` list. `build_prompt()` appends the clause to every prompt
and **raises if it has been altered or removed**; `check_forbidden()` scans the
finished prompt. A model asked for *"a British high street in 1989"* will
happily paint a real brewery's livery on a pub, so we never ask for one —
in-world brands only, which is better content anyway.

Every image is `review: pending` in the manifest. Apache-2.0 weights make the
**licence** answerable; only a human looking makes the **content** answerable.

---

## 4. What was tested here, and what was not

No Windows, no GPU, no Hugging Face (403 through the proxy — only
`raw.githubusercontent.com` answers). So the split is stated rather than
implied.

**Tested, 49 checks, `python3 tools/imagegen/imagegen.py --selftest`**
(22 of them before the section 7 hardening pass, 27 added by it):

- the **accepting case first** — a 12 GB AMD card plans a real, uncapped run;
- seven machine shapes: NVIDIA 24 GB, AMD 8 GB, AMD 4 GB, Intel iGPU with no
  VRAM figure, the uint32 ceiling, a probe that found nothing, a probe that
  crashed. Each gets the right backend, quantisation and flags, and each
  explains itself in the report;
- a single-GPU `machine.json` — PowerShell 5.1 serialises a one-element array
  as a bare object, which would have read as NO GPU FOUND on exactly the
  machine we most expect;
- all 12 prompts carry the content rules; no prompt names a real mark
  (45 tokens × 12 prompts scanned, and the count is printed beside the zero);
- **the rejecting cases**: a prompt stripped of its rules is refused, and the
  forbidden scan fires on a real brand;
- the run loop against a faked generator — a clean batch, a generator that
  fails every time, and the CPU cap;
- **the blank-image check, both ways, on PNGs synthesised in the test** — a
  varied image and a faint 8-level gradient are accepted; uniform black,
  uniform mid-grey, uniform white and a fully-transparent RGBA are each called
  blank; an empty file, a non-PNG and a header-only file are called *unknown*,
  which is a third answer and not a pass;
- **the same check inside the run loop**, which is where it has to work: a fake
  generator that exits **zero** and writes a uniform PNG produces
  `items_written: 0`, two FAILED records naming issue #1031, the files renamed
  `<id>.BLANK.png`, and the batch stopped after two;
- **the per-image Vulkan VAE rule, both ways** — 512×512 keeps the planned
  flags, 1024×1024 drops `--vae-conv-direct` for `--vae-on-cpu`, and the CUDA
  path keeps it because #1673 is a Vulkan report;
- **the download candidate list, both ways** — a 404 on the first candidate
  falls through to the second, and a 401/403 **stops**, prints the gate note,
  and does not try the rest.

**The run-loop tests found a real bug and are shipped because of it.** A FAILED
image incremented `items_failed` and never wrote its record, so the manifest
would have held `items_failed: 2` with `images: []` — the number without the
cause, in the one file we read to diagnose a bad run. `not_attempted` had the
twin fault: it was filled in on one break path out of three, so a run that
stopped early reported an empty list with ten items untouched. It is now
derived from the attempted set after the loop, which no exit path can get
wrong.

A third fault came out of reading the fallback chain rather than out of a
test: the CPU batch cap was applied by `plan()` when the **probe** found no
GPU, but a run that FELL BACK to CPU because Vulkan failed kept the GPU plan —
twelve full-resolution images on a CPU, hours of it, while the report still
claimed a GPU. The cap now follows the backend actually obtained.

**NOT tested, and this is the honest list:**

| untested | what the first run will likely expose |
|---|---|
| the `.bat` itself | quoting, the `for /f` python search, `%~dp0` resolution. Most likely failure: a path with a space we did not quote |
| `probe-machine.ps1` | registry key shape for `qwMemorySize` (byte[] vs int64 is handled; the *adapter index* matching is by `DriverDesc` and may not match), and `-ExecutionPolicy Bypass` if a group policy overrides it |
| every URL | **huggingface.co is unreachable from here.** File names come from stable-diffusion.cpp's docs and wiki (read here) and from search results (not). A rename means a 404, which is why each artefact takes a candidate LIST and prints what every candidate answered |
| ~~the release zip's layout~~ | **now VERIFIED — see below** |
| the embeddable-Python fallback | python.org is blocked here, so those three URLs are guesses. It only runs if he has no Python at all, which is unlikely — the speech venv is tried first |
| ~~every CLI flag~~ | **now VERIFIED against the binary — see below.** What remains untested is whether the low-VRAM flags BEHAVE on his card; `--diffusion-fa` is the first suspect if Vulkan errors |
| **the images** | whether a 6B model at Q4 can letter "MERIDIAN HARBOUR BOARD" legibly at all. That is the open question the batch exists to answer |
| the blank check **against a real generated PNG** | it has only ever seen PNGs this repository already contains and PNGs the selftest synthesises. What sd-cli writes when #1031 fires — all-black, all-white, or transparent — is unknown; all three are covered, and a fourth shape nobody has described is not |
| `--vae-on-cpu` **behaving** | the flag is verified PRESENT in the shipped binary's string table (below), which is not the same as verified to produce a correct picture on his card. Speed is the expected cost and nobody has measured it |
| the ROCm build | named as the next rung, deliberately not wired, never run by anybody here |

### Two rows moved out of that table, because the runtime WAS reachable

`github.com` release assets answer from this container even though Hugging Face
does not, so 38 MB of it was actually fetched and opened:

- **`ensure_runtime` works end to end.** The zip downloaded, extracted, and
  `find_exe` returned `sd-cli.exe` — top level, no `bin/Release/` prefix, and
  `sd-server.exe`, `stable-diffusion.dll` and a 50 MB `ggml-vulkan.dll` sit
  beside it. The docs' path (`.\bin\Release\sd-cli.exe`) is the build tree,
  not the release, which is exactly why the code searches instead of assuming.
- **Every long flag on the generate command was checked against the string
  table of that binary**: `--diffusion-model --vae --llm --prompt --cfg-scale
  --steps --width --height --seed --output --verbose --offload-to-cpu
  --diffusion-fa --vae-tiling --vae-conv-direct --clip-on-cpu`, all present.
  The command now uses **long forms only** — the short forms the docs use
  (`-p -W -H -s -o -v`) are single characters that `strings` cannot see, so
  using them would have meant trusting a doc example over the binary.
- **And `--sampling-method euler` was DROPPED as a result.** The docs' Flux
  example passes it; the binary's own help says *"default: euler for
  Flux/SD3/Wan, euler_a otherwise"* and the scheduler default is
  *"model-specific"*. The enum could not be read out of the string table, and a
  wrong sampler name fails **every** image in the batch. sd-cli knows what
  Z-Image wants and we do not, so the flag is omitted and the manifest records
  that it was not overridden.

The first version of that flag check was itself broken and said every flag was
absent: `grep -qxF "$f"` read `--diffusion-model` as its own options. The
instrument, not the subject — which is the reason the result got a second look
rather than a commit.

**Do not read this as "it works".** It is a script whose logic is tested and
whose Windows, network and GPU surfaces are not.

---

## 5. Two things needing a decision, neither urgent

1. **`attribution-check.py` will count these PNGs under the ambientCG row.**
   `ledger/Assets/StreamingAssets/Decals` is WATCHED with the token
   `ambientCG`, and the sweep matches by path containment — so twelve
   generated files would land inside somebody else's licence row and inflate
   its count. The right fix is an `OURS` entry for
   `Decals/generated` with a provenance sentence, mirroring the `AppIcon`
   row. **Not done here** because the classification is a judgement: the VCTK
   precedent says synthesis does not launder an obligation, and the reason it
   does not apply is that the weights are Apache-2.0 with unrestricted outputs
   and **no third-party asset was an input**. That reasoning should be
   ratified, not assumed. Meanwhile provenance travels with the files:
   `ATTRIBUTION.json` and `manifest.json` are written by the same run that
   writes the PNGs, so they cannot drift apart.
2. **The quality ladder** gains a rung with a name: *local image generation —
   current rung Z-Image-Turbo Q4/Q8 at 8 steps; next rung FLUX.1-schnell
   (Apache-2.0, and **ungated** — see section 7 fix 4) or a higher
   quantisation, decided by reading the first batch's lettering.* An aspect
   whose next rung is blank is a research task; this one is not blank.
   **And a second rung, for the runtime rather than the model:**
   `win-rocm-7.14.0-x64` (189 MB, same pinned release). His card is AMD, ROCm
   is AMD's own compute path rather than the vendor-neutral one, and it would
   sidestep both Vulkan bugs in section 7 rather than defending against them.
   It is NOT wired: nothing here can measure it, its driver requirements on his
   machine are unchecked, and putting an unmeasured backend in front of a
   working one is how a one-click stops being one. It is conditional on what
   the probe reports — if the report says AMD and the run is slow or wrong,
   that is the next thing to try.

---

## 6. What he gets back from the first run

1. `game-design/agent-reports/machine-report.txt` — GPU name, driver, both
   VRAM readings, CPU, RAM, free disk, Vulkan driver count, DirectML presence,
   and the plan with a `why:` line for every branch it took.
2. `ledger/Assets/StreamingAssets/Decals/generated/` — up to 12 PNGs,
   `manifest.json` (model, licence, quantisation, backend, per-image prompt,
   seed, size, steps, duration, sha256, `review: pending`), and
   `ATTRIBUTION.json`.
3. A window that either says DONE and where the files are, or names exactly
   what failed and what to send back. **There is no path on which it prints
   nothing and exits zero** — that is the recorded failure this project has
   already paid for once. **And since section 7, no path on which it says DONE
   over an empty picture either**: the generator's own exit code is no longer
   accepted as evidence that an image exists.

---

## 7. The independent check, and the five faults it fixed (25 Aug, same day)

`game-design/research/imagegen-licence-check.md` re-derived every claim this
build rests on from primary sources before Jafar spends an hour on a 7–10 GB
download. **The licence position held**: Apache-2.0, commercial use permitted,
outputs unrestricted, nothing to accept, no account — with the one refinement
that attribution attaches only if we ever redistribute the *weights*, which we
do not plan to. It also found five faults. All five are fixed; none of them was
a redesign.

**The risk was never legal. It is silent wrong output on an unknown GPU** — and
two of the three serious faults produce a file and exit zero.

### Fix 1 — a known bug writes a blank image and exits SUCCESS

`leejet/stable-diffusion.cpp` issue **#1031, "[BUG] ZImage + VULKAN create a
blank image", OPEN since 2 Dec 2025 with no maintainer reply.** Read directly
today, not relayed: the reporter's log loads every model, samples for 61s,
decodes the VAE in 11s, prints `save result PNG image to 'output.png'
(success)` and exits zero. **The PNG is blank.** The same machine renders SD1.4
correctly. That is our exact configuration — Z-Image through Vulkan.

So the generator cannot be its own witness, and this project has already paid
for that lesson once: a CI job reported success while **deleting** the clips it
was dispatched to produce. Every image is now **decoded and measured** after it
is written, stdlib only (`zlib` plus a defilter loop — no pip, no Pillow):

- a **blank** image is `status: FAILED` with the reason, is **not** counted in
  `items_written`, does **not** land in the manifest as a success, is renamed
  `<id>.BLANK.png` so it cannot be mistaken for a delivered image, and counts
  toward the existing "two failures and nothing succeeded, stop" rule — because
  a configuration that blanks one image will blank twelve;
- the manifest carries `blank_check: {checked, blank, undecodable}` — **a zero
  ships its denominator**, so "0 blank" can never be confused with a check that
  never ran;
- **`unknown` is a third answer.** A PNG that cannot be decoded is reported as
  unchecked, not as blank and not as good. The image is kept and counted, with
  the line *"it has NOT been shown to be good, only not shown to be bad."*

**The bound came from a printed series, not from a guess.** `--series` measures
every PNG under a directory; over all **93 PNGs in this repository** — reference
photographs, kit colour maps, 16-bit normal maps, roughness and opacity masks,
app icons — all 93 decoded and the luminance spreads sorted read

    36 37 42 66 69 70 71 72 72 75 77 82 … 131 131 … 160 161 … 255 (×31)

so the smallest real image sits at **36/255** and the median near 160.
Synthetic uniform frames land at spread 0, stdev 0, one distinct level. **There
is no measured population between 0 and 36**, so the bound sits hard against the
degenerate end — `spread ≤ 2 AND stdev ≤ 1.0` — an eighteenth of the smallest
real reading. The two conditions are ANDed because that is a measurement too:
the flattest real image here (a 16-bit normal map) has stdev **1.64**, below the
stdev bound, and a spread of 75, far above the spread one. Either test alone
would eventually call something real blank.

**Both ways, in the selftest, on PNGs it synthesises itself:**

| case | verdict |
|---|---|
| varied image (160×120, 248 distinct levels) | `varied` — **accepting case, first** |
| faint 8-level gradient, spread 7 | `varied` — the bound does not swallow a soft picture |
| uniform black / uniform mid-grey / uniform white | `blank` ×3 |
| RGBA with varying colour and alpha 0 everywhere | `blank` |
| empty file / non-PNG bytes / header-only stub | `unknown` ×3, not blank, not varied |
| **the run loop**: fake generator exits **0** and writes a uniform PNG | `items_written: 0`, two FAILED records naming #1031, files renamed `.BLANK.png`, batch stopped |
| **the run loop**: fake generator writes varied PNGs | DONE, 12 of 12 checked, 0 blank, 0 undecodable |

### Fix 2 — the AMD 1024×1024 VAE bug, which we hit BY DEFAULT

Issue **#1673**, also read directly: on **AMD Radeon (RADV RENOIR)** the Vulkan
backend renders **gibberish at 1024×1024 with `--vae-conv-direct`** and correct
images at 512×512; the reporter's own workaround is `--vae-on-cpu`.

This was not bad luck, it was the default path. His machine is AMD
(`live-speech-latency.md`: *"CUDA is not a lever for this machine"*), his VRAM
is **unknown by construction** because `AdapterRAM` saturates at 4 GB and
`plan()` correctly refuses to read that as a measurement — and `plan()` turns
`--vae-conv-direct` on whenever VRAM is under 8 GB **or unknown**. Two prompts
are 1024×1024. The whole batch was walking into a reported silent-wrong-output
bug on his exact vendor.

Flags are now decided **per image**, where the size exists, and the reason with
its issue number sits in the code where nobody can re-enable it by accident.
**The bound is the largest size the issue reports as GOOD, not the smallest it
reports as bad**: everything between 512×512 and 1024×1024 is unmeasured by
anybody, the failure is silent rather than loud, and the alternative costs speed
and not correctness. Every one of the twelve items is larger than 512×512, so
**on Vulkan `--vae-conv-direct` will not be used at all for this batch** — said
out loud, in the code and in the machine report, because a flag that looks live
and never fires is worse than one that is gone. The CUDA path keeps it.

**`--vae-on-cpu` is real, and that was checked rather than assumed.** The pinned
release zip was downloaded here today — `sd-master-97d2990-bin-win-vulkan-x64.zip`,
**38,784,820 bytes, byte-exact against the constant in `imagegen.py`** — and
`--vae-on-cpu` is present in `sd-cli.exe`'s string table beside every other long
flag this tool passes. Adding a flag the binary does not know would have failed
all twelve images.

### Fix 3 — the 4 GB download had ONE URL and no fallback

The file's own header promises *"CANDIDATES, NOT A URL… a single URL that is one
rename stale is a dead one-click"*. The text encoder and the VAE each had a
list; **the model — the biggest and most important file — was fetched from one
hardcoded URL.** It now takes six candidates: three repositories × both
spellings of the K quants (`Q4_K` and `Q4_K_M`, which different repackagers name
differently), best first.

Honest about what that is: **huggingface.co answers 403 to this container**, so
not one path was resolved from here. `leejet/Z-Image-Turbo-GGUF` is first
because it is the author of stable-diffusion.cpp and a search index reported the
matching 3.86 GB size there; the other two repositories are **labelled in the
code as guesses**. A guess costs one printed 404 line, never a silent
substitution — `fetch_one` prints what every candidate answered and the manifest
records the URL that actually served the file.

**The gate is stronger, not weaker.** A candidate list is exactly how a fetcher
quietly starts shopping for an unlocked door, so `fetch_one` now **aborts the
list on the first 401/403**, prints the standing note — *"we never use accounts
and never purchase… nothing has been worked around"* — and names the candidates
it did **not** try. Tested both ways: a 404 falls through to the next candidate
and downloads; a 401 and a 403 each stop, with only the first URL ever
attempted.

### Fix 4 — a wrong reason in the code, quoted rather than deleted

The VAE comment said, verbatim: *"stable-diffusion.cpp's docs send you to
black-forest-labs/FLUX.1-schnell for this file, and that repository is gated
behind a Hugging Face login and an acceptance click."* **That is wrong.**
FLUX.1-**schnell** is Apache-2.0 and ungated; FLUX.1-**dev** is the gated,
non-commercial one, and the two are confused constantly. Harmless in effect —
the URL and the licence position do not change — but a wrong reason sends the
next reader somewhere pointless, and it also made our own named next rung look
unreachable when it is not. The retracted sentence is quoted in the code so it
cannot be re-derived from the same plausible half-memory, and the honest reason
for the mirror is written beside it.

### Fix 5 — a rung to record, not to build

`win-rocm-7.14.0-x64` (189 MB) ships in the same pinned release and `plan()`
knows only cuda12 / vulkan / cpu. **Not wired** — see section 5, item 2. It is
now named in `plan()`'s reasons when the probe reports AMD, printed in the
machine report as *next rung (runtime)*, and on the quality ladder.

### What this did NOT change

Everything free, no account, no purchase, no terms accepted; the gate still
stops the run and says so. **The untested list in section 4 has not shrunk — it
grew by three rows**: the blank check has never seen a real generated PNG, only
this repository's and the selftest's synthetic ones; `--vae-on-cpu` is verified
present in the binary but not verified to render well or fast on his card; and
the ROCm build has never been run by anybody here. **The `.bat` and the whole
Windows path remain untested.** The first real run is still the measurement.
