# Image generator — independent licence and feasibility check

> **STATUS: SPEC, 2026-08-25.** Second-opinion verification of the claims the
> one-click image generator (`tools/imagegen/`) rests on, done from primary
> sources before Jafar spends an hour on a 7–10 GB download. Every claim was
> re-derived here rather than relayed. Nothing in `tools/imagegen/` was edited.

## The constraint on this check, stated first

**`huggingface.co` is unreachable from this container** — `curl -I` on a
weights URL returns `HTTP/1.1 403 Forbidden` with a 72-byte body, which is the
egress proxy refusing, not Hugging Face gating. `hf-mirror.com`,
`modelscope.cn`, `docs.comfy.org`, `arxiv.org`, `gitcode.com` and `r.jina.ai`
are all blocked the same way. `api.github.com` returns 403 to the fetcher.

**What that means for every line below:** anything on `github.com` or
`raw.githubusercontent.com` was READ DIRECTLY today and is marked *(read)*.
Anything on Hugging Face was corroborated only through a search index that can
read those pages, and is marked *(index)*. An *(index)* fact is one degree
weaker than a *(read)* one and is labelled as such rather than promoted.

---

## Claim 1 — "Z-Image-Turbo, Apache-2.0, free commercial, outputs unrestricted, no terms"

**TRUE for the licence grant. CANNOT FULLY ESTABLISH that the model card
carries no gate**, because the card could not be loaded from here.

| what | finding | source |
|---|---|---|
| Code + repo licence | `LICENSE` is the verbatim, **unmodified** Apache-2.0 text. Read the first 30 lines and the tail: it ends at the standard `Copyright [yyyy] [name of copyright owner]` boilerplate with **no appended rider, no acceptable-use section, no RAIL-style clause** *(read, 25 Aug 2026)* | https://raw.githubusercontent.com/Tongyi-MAI/Z-Image/main/LICENSE |
| Any separate weights licence in the repo | Repo root is `assets/ src/ .gitignore LICENSE README.md batch_inference.py inference.py pyproject.toml`. **No `MODEL_LICENSE`, no `NOTICE`, no `USE_POLICY`.** GitHub shows the Apache-2.0 badge *(read)* | https://github.com/Tongyi-MAI/Z-Image |
| README licence section | There is none — searched the README for `licen/Apache/commercial/restrict/terms` and it returned nothing. So the weights licence lives only on the model hosts *(read)* | https://raw.githubusercontent.com/Tongyi-MAI/Z-Image/main/README.md |
| Model-card frontmatter, Turbo | `license: apache-2.0`, `library_name: diffusers`, `pipeline_tag: text-to-image`. No `extra_gated_*` field surfaced *(index)* | https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/raw/main/README.md |
| Model-card frontmatter, base model | `--- license: apache-2.0 language: - en pipeline_tag: text-to-image` — this string appears as the indexed TITLE of the raw README, i.e. the index read the file itself *(index)* | https://huggingface.co/Tongyi-MAI/Z-Image/raw/main/README.md |

**Restrictive clauses: none found.** Apache-2.0 has no field-of-use limit, no
commercial restriction, and says nothing about model outputs — so outputs are
unrestricted by this licence.

**Two corrections to how the claim is phrased in the tool:**

1. **"No attribution" is not quite right.** Apache-2.0 §4 requires you to carry
   the licence and NOTICE **when you redistribute the licensed work or a
   derivative of it**. Shipping generated *images* is not redistribution of the
   weights, so no in-game credit is legally owed for the pictures. If we ever
   ship the `.gguf` inside the game build, the attribution obligation attaches.
   Worth one line in the manifest so nobody has to re-derive it.
2. **A licence cannot grant what the licensor does not own.** Apache-2.0
   covers Tongyi's copyright in the weights. It makes no representation about
   third-party rights in scraped training data or in what the model emits.
   Jafar has already ruled on that trade; it is recorded here so the ruling is
   not mistaken for a legal guarantee the licence provides.

### And the licence chain is NOT the one the tool names

`MODEL["upstream"]` says `Tongyi-MAI/Z-Image-Turbo`, but nothing from that
repository is downloaded. What is actually fetched is:

| file | repo actually used | licence relied on |
|---|---|---|
| `z_image_turbo-Q*.gguf` | `leejet/Z-Image-Turbo-GGUF` — a requantisation by the stable-diffusion.cpp author | Apache-2.0 flows down from Tongyi *(index)* |
| `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` | `unsloth/Qwen3-4B-Instruct-2507-GGUF` | Qwen3-4B-Instruct-2507 is `license: apache-2.0` *(index)* |
| `ae.safetensors` | `Comfy-Org/z_image_turbo/split_files/vae/` | Apache-2.0 (FLUX.1-schnell autoencoder lineage) *(index)* |

A repackager cannot add restrictions to an Apache-2.0 work, so the grant
survives; but **the licence of each redistributor's own card was not read
here.** The manifest should record the URL it actually used — it does — and
the licence should be checked against the repo it came from, not the upstream
one it is named after.

---

## Claim 2 — "stable-diffusion.cpp, MIT, self-contained, Vulkan, any vendor, no CUDA"

**MIT: TRUE. Vulkan backend real and shipped: TRUE. "Works on AMD/Intel/NVIDIA
alike": TRUE WITH NAMED EXCEPTIONS, and one of them lands on our exact
configuration.**

- **Licence** *(read, 25 Aug 2026)*: standard MIT in full, "Copyright (c) 2023
  leejet", no added clauses.
  https://raw.githubusercontent.com/leejet/stable-diffusion.cpp/master/LICENSE
- **Backends** *(read)*: README lists CPU / CUDA / **Vulkan** / Metal / OpenCL /
  SYCL with **no experimental or WIP marker on Vulkan**.
- **The binary exists and the tool's constant is byte-exact** *(read)*. Release
  `master-827-97d2990`, published **19 Aug 2026**, ships
  `sd-master-97d2990-bin-win-vulkan-x64.zip` (37 MB) alongside `win-cuda12`
  (321 MB), `win-rocm-7.14.0` (189 MB) and `win-cpu` (22.9 MB). I HEAD-checked
  the download URL: **HTTP 200, Content-Length 38784820** — identical to the
  `38_784_820` in `imagegen.py`. The download is live and pinned correctly.

**The exceptions, all from the project's own tracker** *(read)*:

| issue | state | what it says |
|---|---|---|
| #1031 "[BUG] ZImage + VULKAN create a blank image" | **OPEN since 2 Dec 2025, no maintainer reply** | Z-Image on Vulkan writes a blank PNG and reports success. Same machine renders SD1.4 fine. Reporter had an NVIDIA A1000 6 GB laptop GPU alongside Intel Iris Xe. |
| #1673 "Vulkan produces distorted / gibberish images with `--vae-conv-direct`" | listed **Closed**, updated 21 Jul 2026 (the issue page itself shows no closing comment — state ambiguous) | **AMD Radeon RADV.** Breaks at **1024×1024**, fine at 512×512, fixed by using `--vae-on-cpu` instead. |
| #1637 "sd-cli vulkan just stopped, no error" | OPEN, updated 1 Jul 2026 | silent stop |
| #1818 "Z-Image Q3_K ~2× slower per step since ~build 450" | OPEN, updated 29 Jul 2026 | perf regression on Turing; the build we pin is 827 |

**#1673 is the one that matters to us, and it is a direct hit.**
`plan()` adds `--vae-conv-direct` whenever VRAM is under 8 GB **or unknown**,
and `prompts.json` contains two items at **1024×1024** (`wall_soot_brick`,
`wall_salt_render`). On an AMD card that is precisely the reported failure
shape — and the failure is *silent*: a file is written, it is just wrong. The
named workaround (`--vae-on-cpu`) is already in the tool's vocabulary.

**Also note #1031's failure mode: success exit, blank output.** The tool's
"did it work" check must be a property of the PNG, not the exit code.

---

## Claim 3 — "no account, no token, no terms acceptance"

**CANNOT ESTABLISH BY DIRECT CHECK — every candidate URL is on a host this
container cannot reach.** What can be said:

- All three weights URLs are plain `…/resolve/main/…` links on public,
  non-organisation-gated repositories as far as the index shows. The VAE was
  confirmed present and the right size: `Comfy-Org/z_image_turbo` →
  `split_files/vae/ae.safetensors`, **335 MB** *(index)*, matching the tool's
  `335_000_000`. `leejet/Z-Image-Turbo-GGUF` → `z_image_turbo-Q4_K.gguf`,
  **3.86 GB** *(index)*, matching `3_860_000_000`.
- **The tool's behaviour on a gate is correct and was read here**: `fetch_one`
  catches `HTTPError`, prints `GATED_NOTE` — *"STOP — this download needs a
  Hugging Face login or a terms acceptance… Nothing has been worked around"* —
  and stops. That is the required behaviour and it is implemented.
- **The stable-diffusion.cpp binaries are on GitHub releases and need
  nothing** — verified by HEAD returning 200 above.

**One reason in the code is probably wrong and should be corrected**, because
a wrong reason is what the next session will trust. The VAE comment says
`black-forest-labs/FLUX.1-schnell` "is gated behind a Hugging Face login and an
acceptance click". The evidence says **FLUX.1-schnell is Apache-2.0 and
ungated — FLUX.1-*dev* is the gated, non-commercial one** *(index)*. The chosen
Comfy-Org mirror is fine and verified; only the justification is suspect.

**Two robustness faults found while reading the fetch path:**

1. **The model GGUF is fetched from a SINGLE URL with no fallback**
   (`imagegen.py:893`), even though the file's own header comment promises
   *"CANDIDATES, NOT A URL… A single URL that is one rename stale is a dead
   one-click."* The text encoder and VAE have candidate lists; the 4 GB model —
   the one that matters most — does not.
2. **Filename case is load-bearing and unverified from here.** Other
   redistributors name the same quant `Q4_K_M`; leejet names it `Q4_K`. The
   index agrees with the tool's spelling, but a 404 here costs the whole
   one-click, and it is exactly the class of thing that cannot be checked from
   this container.

---

## Claim 4 — the hardware floor

| source | figure |
|---|---|
| Tongyi upstream README *(read)* | Turbo "fits comfortably within 16G VRAM consumer devices" — that is the **bf16** model |
| stable-diffusion.cpp wiki, "How to Use Z-Image on a GPU with Only 4GB VRAM" *(read)* | Q4_0 or Q3_K model + Qwen3-4B Q4_K_M + `--offload-to-cpu --diffusion-fa` at **1024×512**; `--vae-tiling` and `--vae-conv-direct` for the decode |

**The honest floor: about 4 GB of VRAM, and that number is a claim, not a
measurement.** The wiki page names no GPU, reports no VRAM reading and gives no
timing — it is a recipe, not a benchmark. Nothing here can measure it.

**The real constraint is system RAM, not VRAM.** `--offload-to-cpu` is on in
every branch of `plan()`, and it works by keeping weights in RAM and paging
them to the card per computation. At the default rung that is a 3.9 GB model
plus a 2.5 GB text encoder resident in RAM. The tool already warns under 16 GB
RAM ("this may swap"); that warning is the accurate one.

**Below the floor it degrades correctly**: CPU backend, batch capped at the
first 2 items at half size, described in its own report as "a proof the wiring
works, not the batch". That is the right shape — it will not silently start a
six-hour run.

**One measurement caveat, rule 2.** The quantisation ladder (`≥12 GB → Q8_0`,
`≥10 → Q6_K`, `≥7 → Q4_K`, `≥5 → Q4_0`, `≥3.4 → Q3_K`) is a set of thresholds
nobody has measured — no series was printed and no run informed them. They
choose download size rather than correctness, so the cost of being wrong is a
slow run rather than a wrong answer, but they should be labelled as estimated
until a real machine produces numbers.

---

## Claim 5 — anything else that would make this a bad recommendation

- **Not abandoned.** Release published 19 Aug 2026 (six days ago); issues from
  June–August 2026 are being closed within weeks. Windows x64 binaries exist
  for Vulkan, CUDA 12, ROCm 7.14 and CPU.
- **A rung the tool does not consider: `win-rocm-7.14.0-x64` (189 MB).** If
  Jafar's card turns out to be AMD, ROCm may beat Vulkan and would sidestep the
  Vulkan issues above entirely. `plan()` only knows cuda12 / vulkan / cpu.
  Naming it on the quality ladder costs nothing.
- **Silent-wrong-output is the dominant risk, not licence.** Both #1031 and
  #1673 produce a file and exit zero. Any acceptance check must read the PNG
  (variance, mean, non-blank) rather than the process exit code.
- **Quality on British signage is unverified.** The model advertises bilingual
  English/Chinese text rendering; whether it renders convincing late-analog
  British lettering is an open question that only a first batch answers.
  FLUX.1-schnell is already named as the next rung and is itself Apache-2.0 and
  ungated, so the fallback is real.
- **No licence change found.** Nothing in the sources read today suggests the
  Apache-2.0 grant on Z-Image has been altered since release.

---

## Verdict

**Jafar can run it and can ship what it makes.** The licence position is what
he was told — Apache-2.0, commercial use permitted, outputs unrestricted, no
terms to accept — with the single refinement that attribution attaches if we
ever redistribute the weights themselves, which we do not plan to.

**The risk is not legal, it is silent failure on an unknown GPU.** Three fixes
before he runs it, none large: give the model GGUF a fallback URL list like the
other two files have; drop `--vae-conv-direct` at 1024×1024 (or swap in
`--vae-on-cpu`) because that combination is a reported AMD fault at exactly the
size two of our items use; and check the output PNG is not blank rather than
trusting the exit code, because the known Vulkan bug reports success.
