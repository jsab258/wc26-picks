#!/usr/bin/env python3
"""LEDGER image generation - one click, local, permissively licensed.

WHAT THIS IS. Jafar double-clicks `1 MAKE THE PICTURES.bat`. This script does
everything after that: reads the machine probe, chooses the model build and
quantisation from what it found, downloads a self-contained runtime and
weights into a folder outside the repository, generates the first batch of
Meridian signage, and writes a manifest that answers "what made this, under
what licence, with what settings" months from now.

STDLIB ONLY, ON PURPOSE. There is no pip step, no venv, no torch, no CUDA
toolkit. The generator is a static C++ binary (stable-diffusion.cpp, MIT) that
talks to the GPU through Vulkan, which every modern AMD, Intel and NVIDIA
driver on Windows already ships. That removes the entire class of failure the
voice pipeline spent days on, and it means this runs on his existing Python
without installing a single package into it.

WHAT WE KNOW ABOUT THE MACHINE, AND WHAT WE DO NOT. `live-speech-latency.md`
records that the dev machine has an AMD GPU - Jafar has said so twice - and
that DirectML is the shipping baseline because CUDA is not a lever there. We
do NOT know the model or the VRAM. So nothing here assumes a vendor: the
probe reports, `plan()` branches, and the report file says which branch it
took and why.

THE CLICK DECIDES FOR ITSELF. Jafar's bar is "minimal effort, ideally just a
1 click bat", and a run that needs him to paste a command or move a file by
hand has failed it however well it works. Two decisions used to be his and are
now made inside the click:

  * WORTH STARTING AT ALL. `gpu_gate` runs on the probe's answer BEFORE the
    6.7 GB download. No display adapter, or no probe at all, and the run STOPS
    having downloaded nothing - because the CPU path measured 202 seconds an
    image on his machine and capped at 2 of 12, which is seven minutes of his
    time spent to learn what the probe already said. The deliberate slow path
    exists and is a separate .bat (see CPU_BAT); the default path never asks.
  * WHAT IS ALREADY MADE. `run_batch` skips an item whose PNG is on disk and
    passes the blank check, and says so per item and in the summary. Before
    this, a re-run overwrote twelve files including the two he had picked out
    by hand, so "run it again" meant "first go and copy your good ones aside".

TESTING. Everything that can be tested without a GPU is: `--selftest` runs 83
checks - plan() across seven synthetic machines AND the MULTI-ADAPTER machine
in three orders, the prompt builder refusing to drop the content rules, the run
loop with the generator faked, the blank-image check both ways on synthesised
PNGs, the per-image Vulkan VAE rule both ways, the download candidate list both
ways (a 404 falls through, a 401/403 STOPS), the GPU gate both ways THROUGH
main() with the network wired to explode if touched, and the skip both ways (a
good PNG is skipped, a blank one is not). The accepting case comes first
everywhere, because the expensive failure is a check nothing survives.
What CANNOT be tested here is every line that touches Windows, the network or
the GPU - the .bat, the PowerShell probe and every URL are still UNRUN, and
they are named in the report as such. The probe's version-1 crash on a
multi-adapter machine is exactly what that gap costs: it ran on Jafar's PC,
reported NO GPU on a box with a discrete card, and fell back to CPU at 202
seconds an image.

THE EXIT CODE IS NOT THE EVIDENCE. stable-diffusion.cpp#1031, open and
unanswered, has Z-Image on Vulkan writing a blank PNG and exiting success, and
#1673 has --vae-conv-direct producing gibberish on AMD at 1024x1024. Both
produce a file. Both would pass any check that reads a return code. See the
blank-check and VULKAN_VAE_DIRECT_MAX_PX sections below.
"""
import argparse
import ast
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
import zlib

# ---------------------------------------------------------------------------
# WHAT WE FETCH. Every row carries its licence, because a fetch whose licence
# is established afterwards is a fetch whose licence was never established.
#
# CANDIDATES, NOT A URL. This container cannot reach huggingface.co at all
# (403 through the proxy, recorded in content-sourcing.md), so no path below
# was resolved here - they come from stable-diffusion.cpp's own docs and wiki,
# which WERE read here from raw.githubusercontent. A single URL that is one
# rename stale is a dead one-click; a list that prints what each candidate
# answered is a diagnosis. See `fetch_one`.
# ---------------------------------------------------------------------------
# THE PROMPT FILE'S SCHEMA. Bumped to 2 on 25 Aug when the negative-prompt
# channel, the per-item seed and the per-item cfg arrived. It is checked rather
# than assumed because these two files travel to another machine together and a
# half-pulled clone would otherwise run the new code against the old prompts and
# silently generate the batch the first run already got wrong.
SPEC_SCHEMA = 2

SDCPP_TAG = "master-827-97d2990"          # release read 2026-08-25, published 19 Aug 2026
SDCPP_BASE = f"https://github.com/leejet/stable-diffusion.cpp/releases/download/{SDCPP_TAG}"
SDCPP_ZIPS = {
    "vulkan": (f"{SDCPP_BASE}/sd-master-97d2990-bin-win-vulkan-x64.zip", 38_784_820),
    "cuda12": (f"{SDCPP_BASE}/sd-master-97d2990-bin-win-cuda12-x64.zip", 336_189_872),
    "cpu":    (f"{SDCPP_BASE}/sd-master-97d2990-bin-win-cpu-x64.zip", 24_054_841),
}
SDCPP_CUDART = (f"{SDCPP_BASE}/cudart-sd-bin-win-cu12-x64.zip", 563_452_046)

HF = "https://huggingface.co"

# THE MODEL. Z-Image-Turbo: 6B, Apache-2.0, 8 steps, and stable-diffusion.cpp's
# own wiki has a page titled "How to Use Z-Image on a GPU with Only 4GB VRAM".
# FLUX.1-schnell is the better-known Apache-2.0 option and is kept below as the
# named next rung, not deleted - it is 12B plus a 4.7B T5 text encoder, so it
# costs roughly three times the download for a machine whose VRAM we do not
# know. Neither model's weights are gated; see `GATED_NOTE`.
QUANTS = {                     # gguf file -> approximate bytes, from the repo listing
    "Q8_0": ("z_image_turbo-Q8_0.gguf", 6_580_000_000),
    "Q6_K": ("z_image_turbo-Q6_K.gguf", 5_260_000_000),
    "Q4_K": ("z_image_turbo-Q4_K.gguf", 3_860_000_000),
    "Q4_0": ("z_image_turbo-Q4_0.gguf", 3_680_000_000),
    "Q3_K": ("z_image_turbo-Q3_K.gguf", 3_140_000_000),
    "Q2_K": ("z_image_turbo-Q2_K.gguf", 2_590_000_000),
}
# CANDIDATES FOR THE 4GB FILE, WHICH IS THE ONE THAT HAD NONE. The header at
# the top of this file promises "CANDIDATES, NOT A URL... a single URL that is
# one rename stale is a dead one-click" - the text encoder and the VAE each had
# a list and the model, the biggest and most important download, was fetched
# from ONE hardcoded URL. Found by the independent licence-and-risk check
# (`game-design/research/imagegen-licence-check.md`, 25 Aug 2026).
#
# WHAT IS AND IS NOT VERIFIED HERE. huggingface.co answers 403 to this
# container - the egress proxy, not a gate - so NOT ONE of these paths was
# resolved from here. `leejet/Z-Image-Turbo-GGUF` is first because it is the
# author of stable-diffusion.cpp, it is what the wiki points at, and a search
# index reported `z_image_turbo-Q4_K.gguf` at 3.86 GB there, matching the size
# below. The other two repositories are PLAUSIBLE REDISTRIBUTORS AND NOTHING
# STRONGER - they are guesses, labelled as guesses. A guess costs one printed
# 404 line, because `fetch_one` prints what every candidate answered; it can
# never cost a silent substitution, because the file that arrives is size
# checked and the URL that served it is written into the manifest.
#
# SPELLING IS LOAD-BEARING AND UNVERIFIABLE FROM HERE. leejet names the K
# quants `Q4_K`; several other repackagers name the identical quant `Q4_K_M`.
# Both spellings are tried at every repository rather than betting the whole
# one-click on one of them.
#
# A GATE STILL STOPS EVERYTHING. Candidates are for renames and outages, not
# for routing round a login: `fetch_one` ABORTS the list on the first 401/403
# and names the candidates it did not try. See `GATED_NOTE`.
MODEL_GGUF_REPOS = [
    "leejet/Z-Image-Turbo-GGUF",   # primary; size corroborated via a search index
    "QuantStack/Z-Image-Turbo-GGUF",   # UNVERIFIED from here - a guess
    "calcuis/z-image-gguf",            # UNVERIFIED from here - a guess
]


def model_urls(quant):
    """Every candidate URL for one quantisation, best first.

    Repo order is confidence order and the spelling variants come second, so
    the first attempt is always the one we have the most evidence for.
    """
    fname = QUANTS[quant][0]
    names = [fname]
    if quant.endswith("_K"):                       # Q4_K -> Q4_K_M, same file
        alt = fname.replace(f"-{quant}.gguf", f"-{quant}_M.gguf")
        if alt not in names:
            names.append(alt)
    return [f"{HF}/{repo}/resolve/main/{n}" for repo in MODEL_GGUF_REPOS for n in names]


MODEL = {
    "name": "Z-Image-Turbo",
    "upstream": "Tongyi-MAI/Z-Image-Turbo",
    "licence": "Apache-2.0",
    "licence_note": "Apache-2.0 model weights; outputs unrestricted. No account, "
                    "no terms to accept, no purchase.",
    "params": "6B DiT + Qwen3-4B text encoder",
    "steps": 8,
    "cfg": 1.0,
}
TEXT_ENCODER = {
    "file": "Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
    "bytes": 2_500_000_000,
    "urls": [f"{HF}/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"],
    "licence": "Apache-2.0 (Qwen3, Alibaba)",
}
VAE = {
    "file": "ae.safetensors",
    "bytes": 335_000_000,
    # WHY THIS URL AND NOT THE OBVIOUS ONE - AND A RETRACTION, because a wrong
    # reason is what the next session will trust.
    #
    # THIS COMMENT USED TO SAY, VERBATIM: "stable-diffusion.cpp's docs send you
    # to black-forest-labs/FLUX.1-schnell for this file, and that repository is
    # gated behind a Hugging Face login and an acceptance click." THAT IS
    # WRONG, and it is quoted rather than deleted so nobody re-derives it from
    # the same plausible half-memory. FLUX.1-**schnell** is Apache-2.0 and
    # UNGATED; FLUX.1-**dev** is the gated, non-commercial one, and the two get
    # confused constantly. The licence check
    # (`game-design/research/imagegen-licence-check.md`) caught it.
    #
    # The URL below does not change and neither does the licence position. The
    # honest reason for it: Comfy-Org/z_image_turbo is the mirror ComfyUI's own
    # Z-Image template uses, it carries the file at the size we expect
    # (335 MB, index-corroborated), and it is a Z-Image-shaped repository, so
    # the autoencoder there is the one this model was packaged with. Apache-2.0
    # in both places, so this is a different distributor of the same
    # permissively licensed file either way. Nothing here is a way round a
    # licence, and nothing here needed to be - which is exactly the fact the
    # old sentence obscured. Recorded here and in the manifest.
    "urls": [f"{HF}/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors",
             f"{HF}/Comfy-Org/z_image/resolve/main/split_files/vae/ae.safetensors"],
    "licence": "Apache-2.0 (Z-Image / FLUX.1 autoencoder)",
}
GATED_NOTE = (
    "STOP - this download needs a Hugging Face login or a terms acceptance.\n"
    "  We never use accounts and never purchase: that is Jafar's decision and\n"
    "  he holds the accounts. Nothing has been worked around. Send the line\n"
    "  above back and we will re-point at an ungated mirror or pick another\n"
    "  model."
)
NEXT_RUNG = ("FLUX.1-schnell (Apache-2.0, 12B + T5-XXL, ~10GB more download) is "
             "the named next rung if Z-Image's lettering is not good enough. "
             "stable-diffusion.cpp runs both; the switch is one field. It is "
             "Apache-2.0 and UNGATED - see the VAE comment above, where the "
             "opposite was asserted and is retracted.")
# THE RUNTIME'S NEXT RUNG, NAMED AND DELIBERATELY NOT WIRED. The same release
# that ships the Vulkan build ships `sd-master-97d2990-bin-win-rocm-7.14.0-x64.zip`
# (189 MB), and `plan()` below knows only cuda12 / vulkan / cpu. Jafar's card is
# AMD, so ROCm is AMD's own compute path rather than the vendor-neutral one and
# may be materially faster - AND it would sidestep both Vulkan bugs this file
# now works around (#1031 blank images, #1673 VAE gibberish) rather than
# defending against them. It is NOT wired because nothing here can measure it,
# the ROCm runtime has its own driver requirements nobody has checked on his
# machine, and adding an untested backend to the fallback chain would put an
# unmeasured path in front of a working one. It is a rung with a name, which is
# what this project asks for instead of a silent "good enough".
RUNTIME_NEXT_RUNG = ("win-rocm-7.14.0-x64 (189 MB, same release) is the named next "
                     "rung for an AMD card if Vulkan is slow or wrong - not wired, "
                     "not measured, conditional on what this probe reports.")

MIN_FREE_DISK_GB = 20

# THE SLOW PATH HAS A NAME AND IS A SEPARATE CLICK, so the default one never
# has to ask. Kept as a constant because three places name the file and a
# rename that misses one of them tells him to double-click something that is
# not there.
CPU_BAT = "2 MAKE THE PICTURES (no graphics card).bat"
# MEASURED, NOT ASSUMED: Jafar's run on 25 Aug 2026 fell back to CPU and took
# 202 seconds for one image, 2 of 12 attempted under the CPU cap - about seven
# minutes of his time to produce two half-size pictures. It is the number the
# gate below spends, and it is quoted to him rather than the word "slow".
CPU_SECONDS_PER_IMAGE = 202


# ---------------------------------------------------------------------------
# PLANNING - the only interesting logic, and the only part testable here.
# ---------------------------------------------------------------------------
def _gb(n):
    return (n or 0) / (1024.0 ** 3)


def normalise_gpus(machine):
    """PowerShell 5.1's ConvertTo-Json serialises a ONE-ELEMENT array as a bare
    object, not as a list of one. A machine with a single graphics card is the
    common case, so the naive read would see `gpus` as a dict and report NO GPU
    FOUND on exactly the machine we most expect. Normalise once, here, and drop
    anything that is not a mapping so a null in the array cannot crash the run.
    """
    g = machine.get("gpus")
    if isinstance(g, dict):
        g = [g]
    elif not isinstance(g, list):
        g = []
    machine["gpus"] = [x for x in g if isinstance(x, dict)]
    return machine["gpus"]


def plan(machine, force_cpu=False):
    """Choose backend, quantisation and runtime flags from the probe.

    Pure function of `machine` so it can be tested without Windows. Every
    branch writes a `reason` into the result: the report prints them, so the
    next run is chosen from what the machine said rather than from what
    somebody assumed it said.

    `force_cpu` is the deliberate slow path (CPU_BAT), and it changes the
    BACKEND ONLY: the CPU batch cap and the half-size scale below are the same
    ones a machine with no GPU gets, because the reason for them - 202 seconds
    an image - is the same reason. Asking for the slow path is not permission
    to spend an hour of his afternoon on it.
    """
    gpus = normalise_gpus(machine)
    reasons = []

    # VRAM. Win32_VideoController.AdapterRAM is a uint32 and saturates at 4GB
    # on every card bigger than that, so the probe reads the registry's
    # qwMemorySize as well and we take the LARGEST plausible figure. A number
    # that is exactly 4.00GB from AdapterRAM alone is treated as UNKNOWN, not
    # as a 4GB card, because those two cases are indistinguishable and only one
    # of them is safe to plan a 6.5GB quant against.
    vram_bytes, vram_source = 0, "none"
    for g in gpus:
        for key in ("vram_bytes_registry", "vram_bytes"):
            v = g.get(key) or 0
            if v > vram_bytes:
                vram_bytes, vram_source = v, key
    vram_gb = _gb(vram_bytes)
    vram_known = True
    if vram_source == "vram_bytes" and abs(vram_bytes - 4294967295) < 4096:
        vram_known, vram_gb = False, 0.0
        reasons.append("VRAM read 4294967295 bytes, which is the uint32 ceiling of "
                       "Win32_VideoController.AdapterRAM and NOT a measurement - "
                       "treating VRAM as unknown")
    elif vram_bytes == 0:
        vram_known = False
        reasons.append("no VRAM figure from any source - treating as unknown")
    else:
        reasons.append(f"VRAM {vram_gb:.1f} GB from {vram_source}")

    # Vendor. Only used to pick the fastest binary; the fallback chain means a
    # wrong guess costs a retry, not the run.
    names = " ".join((g.get("name") or "") for g in gpus).lower()
    if "nvidia" in names or "geforce" in names or "quadro" in names or "rtx" in names:
        vendor = "nvidia"
    elif "amd" in names or "radeon" in names or "firepro" in names:
        vendor = "amd"
    elif "intel" in names or "arc" in names or "iris" in names:
        vendor = "intel"
    elif gpus:
        vendor = "other"
    else:
        vendor = "none"

    if force_cpu:
        backend, chain = "cpu", ["cpu"]
        reasons.append("THE CPU PATH WAS ASKED FOR DELIBERATELY (--force-cpu, which "
                       f"is what \"{CPU_BAT}\" passes). No GPU backend is tried at "
                       f"all, and {vendor} is what the probe reported")
    elif vendor == "nvidia":
        backend, chain = "cuda12", ["cuda12", "vulkan", "cpu"]
        reasons.append("NVIDIA adapter named, so the CUDA build is the fast path; "
                       "Vulkan and CPU stay behind it as fallbacks")
    elif vendor == "none":
        backend, chain = "cpu", ["cpu"]
        reasons.append("the probe found NO display adapter at all - CPU only, and "
                       "this will be slow")
    else:
        backend, chain = "vulkan", ["vulkan", "cpu"]
        reasons.append(f"{vendor} adapter, so Vulkan - it is the one vendor-neutral "
                       "GPU path on Windows and needs no SDK at runtime, the same "
                       "reasoning that made DirectML the speech baseline")
        if vendor == "amd":
            reasons.append("AMD, so the NEXT RUNG applies and is named rather than "
                           "taken: " + RUNTIME_NEXT_RUNG)

    # Quantisation. Bigger is better and bigger is a longer download; the
    # ladder is stated so the choice is legible rather than magic.
    if not vram_known:
        quant, why = "Q4_K", "VRAM unknown, so the safe middle rung"
    elif vram_gb >= 12:
        quant, why = "Q8_0", "12GB+ VRAM takes the top rung"
    elif vram_gb >= 10:
        quant, why = "Q6_K", "10-12GB"
    elif vram_gb >= 7:
        quant, why = "Q4_K", "7-10GB"
    elif vram_gb >= 5:
        quant, why = "Q4_0", "5-7GB"
    elif vram_gb >= 3.4:
        quant, why = "Q3_K", "under 5GB - the wiki's 4GB recipe"
    else:
        quant, why = "Q2_K", "under 3.4GB - lowest rung, lettering will suffer"
    if backend == "cpu":
        quant, why = "Q4_K", "CPU run - quant is a RAM question, not a VRAM one"
    reasons.append(f"quantisation {quant}: {why}")

    # Runtime flags. --offload-to-cpu keeps weights in RAM and pages them in per
    # computation; the wiki says it costs no speed and it is what makes 4GB
    # work at all, so it is on everywhere.
    flags = ["--offload-to-cpu", "--diffusion-fa"]
    if backend != "cpu" and (not vram_known or vram_gb < 8):
        flags += ["--vae-tiling", "--vae-conv-direct"]
    if backend != "cpu" and (not vram_known or vram_gb < 6):
        flags += ["--clip-on-cpu"]
    # --vae-conv-direct IS NOT SAFE AT EVERY SIZE ON VULKAN. It survives here as
    # the plan for the machine and is then decided PER IMAGE by `image_flags`,
    # which is where the width and height exist. Issue #1673, full reasoning at
    # VULKAN_VAE_DIRECT_MAX_PX.
    if backend == "vulkan" and "--vae-conv-direct" in flags:
        reasons.append("--vae-conv-direct is planned for the VRAM, but on Vulkan it "
                       "is dropped for any image larger than 512x512 "
                       f"({VULKAN_VAE_DIRECT_MAX_PX} px) and --vae-on-cpu used instead "
                       "(issue #1673: AMD RADV renders gibberish at 1024x1024 with "
                       "it, clean at 512x512). Every item in this batch is larger "
                       "than that, so on Vulkan it will not be used at all")

    # CPU is a proof of wiring, not a batch. Say so rather than starting a
    # six-hour run he did not ask for.
    scale = 1.0
    limit = None
    if backend == "cpu":
        scale, limit = 0.5, 2
        reasons.append("CPU mode: batch CAPPED AT THE FIRST 2 ITEMS at half size. "
                       "That is a proof the wiring works, not the batch - the "
                       "remaining 10 are listed in the manifest as not attempted")

    ram_gb = _gb(machine.get("ram_bytes"))
    if ram_gb and ram_gb < 16:
        reasons.append(f"RAM {ram_gb:.0f}GB is under 16 - with --offload-to-cpu the "
                       "weights live in RAM, so this may swap")

    free_gb = _gb(machine.get("free_disk_bytes"))
    disk_ok = (free_gb >= MIN_FREE_DISK_GB) if free_gb else None

    return {
        "vendor": vendor, "vram_gb": round(vram_gb, 2), "vram_known": vram_known,
        "backend": backend, "backend_chain": chain,
        "quant": quant, "quant_file": QUANTS[quant][0], "quant_bytes": QUANTS[quant][1],
        "flags": flags, "size_scale": scale, "item_limit": limit,
        "ram_gb": round(ram_gb, 1), "free_disk_gb": round(free_gb, 1),
        "disk_ok": disk_ok, "reasons": reasons,
        "download_bytes": QUANTS[quant][1] + TEXT_ENCODER["bytes"] + VAE["bytes"]
                          + SDCPP_ZIPS[chain[0]][1]
                          + (SDCPP_CUDART[1] if chain[0] == "cuda12" else 0),
    }


# ---------------------------------------------------------------------------
# THE GATE - IS THIS RUN WORTH HIS TIME? Asked BEFORE the download, because
# after it the answer costs 6.7 GB and seven minutes either way.
#
# WHY IT EXISTS. The probe reported NO GPU on Jafar's machine (a version-1 bug,
# fixed), `plan()` correctly chose the CPU path, the CPU cap correctly held the
# batch to 2 of 12 at half size, and every one of those behaved exactly as
# designed - and he still lost seven minutes to a run whose result was known
# before it started. The fix that was shipped was a probe command for him to
# paste and read himself, which is a SECOND DECISION handed back to the person
# whose one-click bar this whole tool exists to respect. His words: "why is
# there a probe as a command? should be a 1 click bat too next time."
#
# So the decision moves inside the click. It is a pure function of the probe's
# answer and it lives here, in the layer the selftest can run, rather than in
# the .bat or the .ps1 - neither of which can be executed where this was
# written, and an unrun decision is the one that decides wrongly in silence.
#
# THIS DOES NOT REPLACE THE CPU CAP OR THE FALLBACK. Both stay exactly as they
# are: the gate is about not STARTING, and the cap is about not running away
# with the afternoon once something has started - including the case where the
# probe found a card and the GPU backend then fails at runtime.
# ---------------------------------------------------------------------------
def gpu_gate(machine, force_cpu=False):
    """Should this run download 6.7 GB and start? Pure, so it is testable.

    Returns a dict; `stop` is the decision and `kind` is which of the three
    situations produced it. `found` travels with it ALWAYS - a zero here is
    the whole point, so it ships with the denominator that says how hard the
    probe looked (`sources`), and "the probe never wrote a file" is a
    different kind from "the probe looked and found none", because they want
    different things from Jafar: re-run vs tell us what card is in there.
    """
    gpus = normalise_gpus(machine)
    g = {"found": len(gpus),
         "names": [str(x.get("name") or "?") for x in gpus],
         "sources": str(machine.get("gpu_sources_tried") or ""),
         "source": str(machine.get("gpu_source") or "unrecorded"),
         "probe": str(machine.get("probe") or "not reported"),
         "forced": bool(force_cpu)}
    if force_cpu:
        g.update(stop=False, kind="forced-cpu",
                 why="the CPU path was asked for deliberately, so the gate does "
                     "not apply - this run is expected to be slow and capped")
    elif not machine.get("probe_file_read", True):
        g.update(stop=True, kind="no-probe-file",
                 why="the machine probe wrote nothing this run, so what is in "
                     "this PC is UNKNOWN - which is not the same as knowing "
                     "there is no card, and neither is a reason to spend 6.7 GB")
    elif not gpus:
        g.update(stop=True, kind="no-adapter",
                 why="the probe ran and found NO display adapter, so the only "
                     "path left is the CPU one, and that is a decision worth "
                     f"{CPU_SECONDS_PER_IMAGE} seconds an image of his time")
    else:
        g.update(stop=False, kind="adapter",
                 why=f"{len(gpus)} display adapter(s) found, so there is a GPU "
                     "path to try and the run is worth starting")
    return g


def format_gate_stop(gate, report_paths):
    """The words he reads in the window that is already open. Formatted HERE
    because this layer is the one with tests: a message written in the .bat
    ships unrun, and an unrun message printing a plausible sentence is the
    silent-instrument failure this project keeps writing rules about.
    """
    L = ["", "=" * 62,
         "STOPPED ON PURPOSE - and NOTHING was downloaded.", "=" * 62]
    A = L.append
    if gate["kind"] == "no-probe-file":
        A("  What happened: the step that looks at this PC produced no report")
        A("  at all, so we do not know what graphics card is in it.")
        A(f"  The probe said: {gate['probe']}")
    else:
        A("  What was found: NO display adapter on this PC.")
        A(f"  The probe looked via: {gate['source']}")
        if gate["sources"]:
            A("  and each source answered:")
            for line in gate["sources"].split(" | "):
                A(f"    {line}")
        else:
            A("  and it recorded NO source log, so that zero carries no")
            A("  denominator - it may mean the probe could not look.")
    A("")
    A("  Why it stopped instead of carrying on:")
    A("    without a card the pictures are drawn by the CPU, which measured")
    A(f"    {CPU_SECONDS_PER_IMAGE} seconds EACH on the last run - about "
      f"{int(round(2 * CPU_SECONDS_PER_IMAGE / 60.0))} minutes for the 2")
    A("    half-size images the CPU cap allows, out of 12. That is your time")
    A("    spent to be told what this report already says, so the download")
    A("    (6.7 GB) and the generating were both skipped.")
    A("")
    A("  WHAT TO SEND BACK - this file, and nothing else:")
    for p in report_paths:
        A(f"    {p}")
    A("")
    A("  IF YOU WANT THE SLOW CPU RUN ANYWAY - it is one click and it is")
    A("  meant to be there, not a workaround:")
    A(f"    double-click  \"{CPU_BAT}\"")
    A("    It downloads 6.7 GB, then makes 2 half-size pictures at about")
    A(f"    {CPU_SECONDS_PER_IMAGE}s each. Nothing else changes.")
    A("=" * 62)
    return L


def check_forbidden(text, forbidden):
    """A prompt naming a real brand is a bug in the prompt file, not in the run.

    Returns the hits. `len(scanned)` travels with it so a clean result cannot be
    confused with a check that never looked - a zero needs its denominator.
    """
    low = " " + text.lower() + " "
    return [t for t in forbidden if t.lower() in low]


def resolve_style(item, style):
    """The prefix/suffix this item gets: the shared pair, overridden per KIND.

    In the JSON rather than in a branch here, because the day somebody adds a
    `label` kind the override has to be theirs to write, not mine to remember.
    A wall texture asked for as a `photograph` comes back as a photograph of a
    wall - with a coping, a corner and a pavement in it, which is exactly what
    `wall_soot_brick` returned on 25 Aug.
    """
    by_kind = (style.get("by_kind") or {}).get(item.get("kind"), {})
    return (by_kind.get("prefix", style.get("prefix", "")),
            by_kind.get("suffix", style.get("suffix", "")))


def build_prompt(item, rules_clause, style):
    """Positive prompt = style prefix + the item + style suffix + THE RULES.

    The rules clause is appended here and nowhere else, and this function
    refuses to return a prompt without it. `content_rules.rules_clause` is data
    in prompts.json precisely so a later editor adding a thirteenth sign cannot
    forget the one sentence that keeps a real brewery's livery off our pub.

    IT IS ALSO THE ONE EXCLUSION CLAUSE ALLOWED IN A POSITIVE PROMPT, and that
    is a measured exception rather than an oversight: at cfg 1.0 sd-cli never
    evaluates the unconditional branch, so a negative prompt is inert and
    moving this clause into it would delete the only anti-brand instruction the
    model receives. `scan_exclusions` exempts it BY NAME and prints that it did.
    """
    if not rules_clause or "no trade marks" not in rules_clause:
        raise ValueError("content rules missing or altered: every prompt must "
                         "carry the no-trade-marks / no-real-person clause")
    prefix, suffix = resolve_style(item, style)
    parts = [prefix.strip(), item["prompt"].strip(), suffix.strip(),
             rules_clause.strip()]
    return ", ".join(p.rstrip(",") for p in parts if p)


def build_negative(item, spec):
    """Negative prompt = negatives.default + negatives.by_kind[kind] + item.

    COMPOSED, NOT REPLACED, so a wall can say what a wall must not have without
    restating the twenty nouns every image must not have. Returns "" when the
    file carries no negatives block at all, which is what a schema-1 file does.
    """
    neg = spec.get("negatives") or {}
    parts = [neg.get("default", ""),
             (neg.get("by_kind") or {}).get(item.get("kind"), ""),
             item.get("negative", "")]
    return ", ".join(p.strip().rstrip(",") for p in parts if p and p.strip())


def item_cfg(item, defaults):
    """cfg for ONE image. Per item because cfg is the switch that decides
    whether the negative prompt is evaluated at all, and that is a per-image
    decision - see `negative_state`."""
    return float(item.get("cfg", defaults.get("cfg", 1.0)))


def item_seed(item, defaults):
    """The seed, EXPLICIT IN THE FILE where it exists.

    It used to be `seed_base + position in the list`, which made every seed a
    function of how many items sat above it: inserting one item re-seeded the
    whole tail, and with a resume rule that regenerates when the recipe changed
    that is a full re-run for a one-line edit. Where an item carries no seed the
    fallback is derived from its ID rather than its position, so it is stable
    under insertion too.
    """
    if "seed" in item:
        return int(item["seed"])
    base = int(defaults.get("seed_base", 0))
    return base + (zlib.crc32(item["id"].encode("utf-8")) % 100000)


def negative_state(cfg, negative):
    """(active, why) for this image's negative prompt. THE HALF THAT MATTERS.

    A negative prompt at cfg 1.0 does NOTHING, and nothing about the command
    line says so - which is the silent-instrument failure exactly: a channel
    that is wired, passed, logged, and never once evaluated.

    MEASURED FROM THE SOURCE, not remembered. stable-diffusion.cpp's
    `resolve_guidance` (src/stable-diffusion.cpp, read 25 Aug 2026) sets
    `use_uncond` only when `img_cfg != txt_cfg`; a model with no image
    conditioning has img_cfg forced to 1.0, so `--cfg-scale 1.0` leaves
    use_uncond false and the negative prompt is never encoded. The shipped
    binary carries that function's own log strings ("3-conditioning CFG is not
    supported with this model", "unconditioned mode, images won't follow the
    prompt (use cfg-scale=1 for distilled models)") in its string table, in
    that order, so this is the build we are running and not just master.

    Z-Image-Turbo is distilled FOR cfg 1.0 - the project's own docs page uses
    1.0 for Turbo and 5.0 for Base - which is why the shipped items sit there
    and why `probe_wall_cfg1`/`probe_wall_cfg2` exist to measure whether this
    model can take cfg > 1 at all.
    """
    if not negative:
        return False, "no negative prompt for this item"
    if abs(cfg - 1.0) < 1e-9:
        return False, ("RECORDED BUT INERT: at cfg 1.0 sd-cli never evaluates "
                       "the unconditional branch (resolve_guidance sets "
                       "use_uncond only when img_cfg != txt_cfg), so this "
                       "negative prompt was not encoded and changed nothing")
    return True, f"active: cfg {cfg} != 1.0, so the unconditional branch runs"


# ---------------------------------------------------------------------------
# THE EXCLUSION SCAN - fault 1, made mechanical.
#
# Every exclusion we wrote went into the POSITIVE prompt, where a diffusion
# model reads the nouns and draws them: `no signage legible` produced a crisp
# sign board reading WEORED S HONJ. This scan is what stops that coming back,
# and it runs over the composed prompt rather than over the item, because the
# clause that did the most damage (`no people, no cars`) lived in the SHARED
# style suffix and would have been invisible to a per-item check.
#
# WHAT IT DELIBERATELY DOES NOT SEE. The lettering a sign actually carries is
# quoted copy - 'NO ADMITTANCE EXCEPT ON BUSINESS' is the words on the board,
# not an instruction to the model - so runs of capitals are stripped before
# scanning. And the content-rules clause is exempt by identity, printed as
# exempt, for the reason in `build_prompt`.
# ---------------------------------------------------------------------------
EXCLUSION_WORDS = ("no", "not", "none", "without", "never", "avoid",
                   "excluding", "devoid", "lacking", "absent", "free of",
                   "minus", "remove")


def _strip_lettering(text):
    """Remove runs of capitals - the copy ON the sign - before scanning."""
    return re.sub(r"[A-Z][A-Z0-9'&. ]{2,}", " ", text)


def scan_exclusions(text, exempt=()):
    """Exclusion words left in a POSITIVE prompt. Returns (hits, scanned_words).

    The denominator travels with the zero: "0 exclusion clauses" beside "0
    words scanned" is a check that never looked, and this file has been caught
    by that shape twice.
    """
    for e in exempt:
        if e:
            text = text.replace(e, " ")
    body = _strip_lettering(text).lower()
    words = re.findall(r"[a-z]+", body)
    hits = []
    for w in EXCLUSION_WORDS:
        if " " in w:
            if w in body:
                hits.append(w)
        elif w in words:
            hits.append(w)
    return hits, len(words)


def validate_spec(spec):
    """Everything wrong with prompts.json, as plain sentences. Empty = valid.

    Runs BEFORE the 6.7 GB download, because a typo in a prompt file should
    cost a printed line rather than half an hour of somebody's evening.
    """
    problems = []
    schema = spec.get("schema")
    if schema != SPEC_SCHEMA:
        problems.append(
            f"prompts.json says schema {schema!r} and this imagegen.py speaks "
            f"schema {SPEC_SCHEMA}. They came from different commits - pull the "
            "repository again so the two files match.")
        return problems                    # every later check assumes schema 2
    rules = (spec.get("content_rules") or {}).get("rules_clause", "")
    style = spec.get("style") or {}
    defaults = spec.get("defaults") or {}
    forbidden = (spec.get("content_rules") or {}).get("forbidden_tokens", [])
    ids = set()
    items = spec.get("items") or []
    if not items:
        problems.append("prompts.json lists no items at all.")
    for i, item in enumerate(items):
        who = item.get("id") or f"item {i} (which has no id)"
        for field in ("id", "kind", "prompt", "width", "height"):
            if not item.get(field):
                problems.append(f"{who}: no {field}.")
        if item.get("id") in ids:
            problems.append(f"{who}: two items share this id, so one would "
                            "overwrite the other's PNG.")
        ids.add(item.get("id"))
        if not item.get("prompt"):
            continue
        try:
            prompt = build_prompt(item, rules, style)
        except ValueError as e:                              # noqa: BLE001
            problems.append(f"{who}: {e}")
            continue
        hits, scanned = scan_exclusions(prompt, exempt=(rules,))
        if hits:
            problems.append(
                f"{who}: the POSITIVE prompt still says {hits} - an exclusion "
                "belongs in `negatives`, because a diffusion model reads the "
                "noun and draws it. That is what put a sign board on "
                "wall_soot_brick.")
        neg = build_negative(item, spec)
        neg_hits, _ = scan_exclusions(neg)
        if neg_hits:
            problems.append(
                f"{who}: the NEGATIVE prompt says {neg_hits}. A negative prompt "
                "is a list of nouns to push away; `no people` in it asks to "
                "push away the phrase `no people`. Write `people`.")
        bad = check_forbidden(prompt + " " + neg, forbidden)
        if bad:
            problems.append(f"{who}: names a real mark: {bad}.")
        if item_cfg(item, defaults) <= 0:
            problems.append(f"{who}: cfg must be greater than zero.")
    return problems


def recipe_of(item, prompt, negative, w, h, cfg, steps, seed, negative_active):
    """The fingerprint that decides SKIP or REGENERATE on the next run.

    It hashes WHAT THE GENERATOR ACTUALLY CONSUMED. That is why `negative` is
    in it only when the negative is ACTIVE: at cfg 1.0 sd-cli never encodes it,
    so an inert negative cannot have changed a single pixel, and hashing it
    anyway would have regenerated twelve good images to produce twelve
    identical ones. A resume key that reruns work it cannot change is a resume
    key nobody will leave switched on.
    """
    parts = [item["id"], prompt, negative if negative_active else "",
             f"{w}x{h}", f"cfg={cfg}", f"steps={steps}", f"seed={seed}"]
    return hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# HOW LONG WILL IT TAKE - measured on the one card this has ever run on.
#
# THREE POINTS, ONE MACHINE, ONE MODEL. Jafar's RX 6700 over Vulkan, Z-Image
# -Turbo Q4_K at 8 steps, 25 Aug 2026: ~90 s at 1024x512, ~100 s at 640x896,
# ~290 s at 1024x1024. That is 172, 174 and 276 seconds per megapixel, so the
# cost per pixel RISES with size and a single rate would under-read the big
# ones by 60%. Interpolated between the anchors, extrapolated on the last
# slope, and it says whose card it came from every time it prints - a number
# from one machine quoted without the machine is how an estimate becomes a
# promise (rule 7).
# ---------------------------------------------------------------------------
COST_ANCHORS = [(1024 * 512, 90.0), (640 * 896, 100.0), (1024 * 1024, 290.0)]
COST_SOURCE = "measured on an RX 6700 / Vulkan / Z-Image-Turbo Q4_K / 8 steps, 25 Aug"


def estimate_seconds(w, h, cfg=1.0):
    """Rough seconds for one image on the measured card. cfg > 1 doubles the
    model evaluations per step (the unconditional branch runs too), so it
    doubles - that half is arithmetic from the algorithm, not a measurement,
    and it is labelled as such wherever it is printed."""
    px = w * h
    pts = sorted(COST_ANCHORS)
    if px <= pts[0][0]:
        est = pts[0][1] * px / pts[0][0]
    elif px >= pts[-1][0]:
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        est = y1 + (px - x1) * (y1 - y0) / (x1 - x0)
    else:
        est = pts[-1][1]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 <= px <= x1:
                est = y0 + (px - x0) * (y1 - y0) / (x1 - x0)
                break
    return est * (2.0 if cfg > 1.0 else 1.0)


# ---------------------------------------------------------------------------
# REPORT - the file we read to choose the next run.
# ---------------------------------------------------------------------------
def format_report(machine, pl, extra=None, publisher=None):
    L = []
    A = L.append
    A("LEDGER - image generation, machine report")
    A("=" * 60)
    A(f"written   {time.strftime('%Y-%m-%d %H:%M:%S')} local")
    A(f"host      {machine.get('hostname', '?')}")
    A(f"os        {machine.get('os', '?')}  ({machine.get('os_build', '?')})")
    A(f"cpu       {machine.get('cpu', '?')}  x{machine.get('cpu_cores', '?')} cores")
    A(f"ram       {_gb(machine.get('ram_bytes')):.1f} GB")
    A(f"free disk {_gb(machine.get('free_disk_bytes')):.1f} GB on {machine.get('disk_letter', '?')}")
    A(f"python    {machine.get('python', '?')}")
    A(f"probe     {machine.get('probe', 'ok')}  (probe version "
      f"{machine.get('probe_version', '1 - PRE-DATES THE MULTI-ADAPTER FIX')})")
    A("")
    gpus = normalise_gpus(machine)
    A(f"GPUs   {len(gpus)} found via {machine.get('gpu_source', 'unrecorded source')}")
    if not gpus:
        A("  NONE FOUND - either there is no display adapter or the probe failed.")
        A("  Those two look identical from here, which is why this line says both.")
        # THE DENOMINATOR. Version 1 printed NONE FOUND on a machine with a
        # discrete card and nothing said how hard it had looked, so the reading
        # was indistinguishable from a machine with no graphics at all.
        tried = machine.get("gpu_sources_tried")
        if tried:
            A("  sources tried, and what each one answered:")
            for line in str(tried).split(" | "):
                A(f"    {line}")
        else:
            A("  and NO SOURCE LOG - this probe did not record where it looked,")
            A("  so NONE FOUND here carries no denominator and proves nothing.")
    for i, g in enumerate(gpus):
        A(f"  [{i}] {g.get('name', '?')}   (from {g.get('source', 'unrecorded source')})")
        A(f"      driver {g.get('driver', '?')}   vendor string {g.get('vendor', '?')}")
        A(f"      AdapterRAM {_gb(g.get('vram_bytes')):.2f} GB "
          f"(uint32, saturates at 4.00)")
        A(f"      registry qwMemorySize {_gb(g.get('vram_bytes_registry')):.2f} GB "
          f"(the one to believe)  [{g.get('vram_match', 'match not recorded')}]")
    A("")
    # "0 registered" and "we could not look" want DIFFERENT actions from Jafar -
    # repair the display driver, or re-run the probe - so they are never printed
    # as the same number.
    A(f"vulkan drivers registered: {machine.get('vulkan_drivers', '?')}")
    A(f"vulkan status:             {machine.get('vulkan_status', 'not reported by this probe')}")
    if machine.get("vulkan_icds"):
        A(f"vulkan ICDs:               {machine.get('vulkan_icds')}")
    A(f"vulkan loader dll:         {machine.get('vulkan_loader', 'not reported by this probe')}")
    A(f"directml dll present:      {machine.get('directml', '?')}")
    A("")
    A("PLAN CHOSEN FROM THE ABOVE")
    A("-" * 60)
    A(f"  vendor        {pl['vendor']}")
    A(f"  vram          {pl['vram_gb']} GB  (known: {pl['vram_known']})")
    A(f"  backend       {pl['backend']}   fallback chain {' -> '.join(pl['backend_chain'])}")
    A(f"  model         {MODEL['name']} {pl['quant']}  ({MODEL['licence']})")
    A(f"  flags         {' '.join(pl['flags'])}")
    A(f"  download      {pl['download_bytes'] / 1e9:.1f} GB one time")
    A(f"  free disk ok  {pl['disk_ok']}  (need {MIN_FREE_DISK_GB} GB)")
    if pl["item_limit"]:
        A(f"  BATCH CAPPED  first {pl['item_limit']} items only - see reasons")
    A("")
    A("  why:")
    for r in pl["reasons"]:
        A(f"    - {r}")
    A("")
    A(f"  next rung (model):   {NEXT_RUNG}")
    A(f"  next rung (runtime): {RUNTIME_NEXT_RUNG}")
    if pl["vendor"] == "amd":
        A("      ^ this machine is the AMD case that rung is for. It is NOT wired "
          "and NOT measured; it is here so the next run has somewhere to go.")
    if extra:
        A("")
        A("RUN")
        A("-" * 60)
        for line in extra:
            A(f"  {line}")
    A("")
    # THIS PARAGRAPH HAS NOW BEEN WRONG IN BOTH DIRECTIONS, AND THE SECOND WAS
    # MINE. It first said "Send this whole file back", which survived the
    # rewrite that was meant to make sending automatic. I replaced that on
    # 26 Aug with "Nothing to send - this run pushes its own report and
    # pictures back", and wrote in the comment beside it that "the run pushed
    # its own results AND told Jafar to paste them".
    #
    # IT DID NOT. `Publisher` was defined, given plain-English failure text for
    # every path, and NEVER INSTANTIATED - `run_batch(... publisher=None)` was
    # its only live call and nothing ever passed one. So the fix for a false
    # sentence was a second false sentence, asserted without running the thing
    # it described. Rule 6 and rule 1 in one paragraph.
    #
    # Both are quoted rather than deleted, because the shape that produced them
    # is the point: this text was WRITTEN as a claim both times. It is now
    # DERIVED - there is no sentence here that can be true while the pusher is
    # off, because the pusher is asked.
    A("SENDING BACK")
    A("-" * 60)
    for line in publisher_paragraph(publisher):
        A(f"  {line}")
    return "\n".join(L) + "\n"


def publisher_paragraph(publisher):
    """What to tell a person about getting the results back here, DERIVED from
    the publisher's own state. Four cases and every one of them is a normal
    outcome; none of them is a sentence somebody typed in advance.

    `None` is its own case and it is the one that bit: it means no publisher
    was constructed at all, which for eleven days was every run.
    """
    if publisher is None:
        return ["NOT WIRED: this run had no sender, so NOTHING was pushed. "
                "Zip the pictures folder named above and send it, and send "
                "this file. (If you are reading this in the repository, the "
                "sender is wired and this line cannot appear.)"]
    if publisher.pushes:
        out = [f"Sent: {publisher.pushes} push(es) to {publisher.branch}, "
               f"{publisher.commits} commit(s) made. The pictures and this "
               "report are already in the project - nothing to paste."]
        if publisher.failures:
            out.append(f"Some pushes failed first ({len(publisher.failures)}); "
                       "they are listed under RUN above. The last one worked.")
        return out
    if publisher.failures:
        return ["Tried to send and could NOT. The pictures are safe on disk. "
                "What went wrong:"] + [f"  {f}" for f in publisher.failures] + \
               ["Zip the pictures folder named above and send it, plus this file."]
    if not publisher.enabled:
        return [f"Sending back is OFF: {publisher.off_reason}",
                "Zip the pictures folder named above and send it, plus this file."]
    return ["Sending back is on and nothing has been pushed yet - this report "
            "was written before the final send. The line printed in the window "
            "after it says which."]


# ---------------------------------------------------------------------------
# FETCH
# ---------------------------------------------------------------------------
def sha256(path, cap_mb=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        read = 0
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            read += len(chunk)
            if cap_mb and read >= cap_mb * (1 << 20):
                return h.hexdigest() + f" (first {cap_mb}MB only)"
    return h.hexdigest()


def fetch_one(urls, dest, expect_bytes, label):
    """Download with resume. Tries every candidate and PRINTS what each said.

    Returns (path, url_used). Raises RuntimeError naming every candidate and
    its status when all fail - a one-click that dies with "download failed" is
    a one-click that costs a round trip to diagnose.
    """
    dest = pathlib.Path(dest)
    if dest.exists() and dest.stat().st_size >= expect_bytes * 0.97:
        print(f"  [have] {label}: {dest.name} ({dest.stat().st_size/1e9:.2f} GB)")
        return dest, "already on disk"
    tried = []
    for url in urls:
        try:
            have = dest.stat().st_size if dest.exists() else 0
            req = urllib.request.Request(url, headers={
                "User-Agent": "ledger-imagegen/1 (+local batch, no account)"})
            if have:
                req.add_header("Range", f"bytes={have}-")
            print(f"  [get ] {label}\n         {url}")
            if have:
                print(f"         resuming from {have/1e9:.2f} GB")
            with urllib.request.urlopen(req, timeout=120) as r:
                total = int(r.headers.get("Content-Length") or 0) + have
                mode = "ab" if (have and r.status == 206) else "wb"
                if mode == "wb":
                    have = 0
                done, mark, t0 = have, time.time(), time.time()
                with open(dest, mode) as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        if time.time() - mark > 10:
                            mark = time.time()
                            pct = (100.0 * done / total) if total else 0
                            rate = (done - have) / max(1e-6, time.time() - t0) / 1e6
                            print(f"         {done/1e9:.2f} GB / {total/1e9:.2f} GB"
                                  f"  {pct:.0f}%  {rate:.0f} MB/s")
            got = dest.stat().st_size
            if expect_bytes and got < expect_bytes * 0.5:
                tried.append(f"{url} -> only {got} bytes, expected ~{expect_bytes}")
                continue
            print(f"  [ok  ] {label}: {got/1e9:.2f} GB")
            return dest, url
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                # A GATE ENDS THE LIST. Falling through to the next candidate
                # after a 401/403 is how a candidate list quietly becomes a way
                # round a login, and this file grew a candidate list for the
                # model on the same day this line was written. We hold no
                # accounts and we do not shop for an unlocked door: stop, say
                # so, and name what was NOT tried so the answer is legible.
                print(f"\n  {url}\n  HTTP {e.code} - GATED.\n{GATED_NOTE}\n")
                tried.append(f"{url} -> HTTP {e.code} GATED (login/terms required)")
                rest = urls[urls.index(url) + 1:]
                if rest:
                    tried.append(f"STOPPED at the gate. NOT tried: {', '.join(rest)}")
                break
            tried.append(f"{url} -> HTTP {e.code}")
        except Exception as e:                                # noqa: BLE001
            tried.append(f"{url} -> {type(e).__name__}: {e}")
    raise RuntimeError(
        f"could not download {label}. Every candidate was tried:\n    "
        + "\n    ".join(tried)
        + "\n  If one of these says GATED, that is a decision for Jafar and we stop"
          " here on purpose.")


def find_exe(root):
    """The release zip's internal layout is not documented and was NOT verified
    here, so we search for the binary rather than assuming a path, and print
    what we found. Older builds call it sd.exe, current docs say sd-cli.exe."""
    root = pathlib.Path(root)
    for name in ("sd-cli.exe", "sd.exe"):
        hits = sorted(root.rglob(name))
        if hits:
            return hits[0]
    listing = [str(p.relative_to(root)) for p in sorted(root.rglob("*.exe"))][:20]
    raise RuntimeError(
        "no sd-cli.exe or sd.exe inside the extracted runtime.\n"
        f"  looked under {root}\n"
        f"  .exe files present ({len(listing)} shown): {listing or 'NONE'}\n"
        "  Send this list back - it means the release layout changed.")


def ensure_runtime(ws, backend):
    url, size = SDCPP_ZIPS[backend]
    zpath = ws / f"sd-{backend}.zip"
    outdir = ws / f"runtime-{backend}"
    if not outdir.exists():
        fetch_one([url], zpath, size, f"stable-diffusion.cpp ({backend}, MIT)")
        outdir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zpath) as z:
            z.extractall(outdir)
        if backend == "cuda12":
            cz = ws / "cudart.zip"
            fetch_one([SDCPP_CUDART[0]], cz, SDCPP_CUDART[1], "CUDA runtime DLLs")
            with zipfile.ZipFile(cz) as z:
                z.extractall(outdir)
    return find_exe(outdir)


# ---------------------------------------------------------------------------
# IS THE PICTURE ACTUALLY A PICTURE - THE EXIT CODE IS NOT THE EVIDENCE
#
# leejet/stable-diffusion.cpp issue #1031, "[BUG] ZImage + VULKAN create a
# blank image" - OPEN since 2 Dec 2025 with no maintainer reply, read here
# 25 Aug 2026 - is OUR EXACT CONFIGURATION: Z-Image through the Vulkan backend.
# The reporter's log loads every model, samples for 61s, decodes the VAE in
# 11s, prints "save result PNG image to 'output.png' (success)", and exits
# zero. The PNG is blank. The same machine renders SD1.4 correctly.
#
# So the generator cannot tell us whether it worked, and the only witness is
# the file. This project has a recorded incident of CI reporting success while
# DELETING the clips it was meant to produce; the standing rule from it is
# verify a job's EFFECTS, not its exit code. Here that means decoding the PNG.
#
# STDLIB ONLY, like everything else in this file: zlib is in the standard
# library, and a non-interlaced 8- or 16-bit PNG is an inflate plus a defilter
# loop. No pip, no Pillow.
# ---------------------------------------------------------------------------

# THE BOUND, AND THE SERIES IT CAME FROM - printed before it was chosen, which
# is this project's rule and not a formality. `--selftest --series` reruns it.
#
# Measured 25 Aug 2026 over ALL 93 PNGs in this repository - reference
# photographs, kit colour maps, app icons, 16-bit normal maps, roughness and
# opacity masks. All 93 decoded; none was undecodable. Luminance spread, sorted
# and abbreviated:
#
#   36 37 42 66 69 70 71 72 72 75 77 82 ... 131 131 ... 160 161 ... 255 (x31)
#
# So the smallest spread any real image reached was 36/255, the median about
# 160, and thirty-one of them saturate at 255. Synthetic uniform frames - black,
# mid-grey, white, and a one-level checkerboard - land at spread 0, stdev 0,
# 1 distinct level, by construction. THERE IS NO MEASURED POPULATION BETWEEN 0
# AND 36, so the bound goes hard against the degenerate end rather than into the
# middle of a gap nobody has data for. 2 levels is a EIGHTEENTH of the smallest
# real image seen and nothing with content in it can get there.
#
# BOTH CONDITIONS, ANDED, and that is a measurement too: the flattest real image
# here (a 16-bit normal map) has stdev 1.64, BELOW the stdev bound - and a
# spread of 75, far above the spread bound. Either test alone would eventually
# call something real blank. A synthetic 8-level ramp, spread 7 stdev 2.3, is
# correctly called varied by both.
BLANK_MAX_SPREAD = 2      # max minus min luminance, 0-255, over the sample
BLANK_MAX_STDEV = 1.0     # and it must be flat, not two adjacent levels of dither

_PNG_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}   # colour type -> channels


def _unfilter_row(ft, line, prev, bpp):
    """PNG per-row filters, RFC 2083 section 6. Mutates `line` in place."""
    n = len(line)
    if ft == 0:
        return
    if ft == 1:                                        # Sub
        for i in range(bpp, n):
            line[i] = (line[i] + line[i - bpp]) & 255
    elif ft == 2:                                      # Up
        for i in range(n):
            line[i] = (line[i] + prev[i]) & 255
    elif ft == 3:                                      # Average
        for i in range(n):
            a = line[i - bpp] if i >= bpp else 0
            line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
    elif ft == 4:                                      # Paeth
        for i in range(n):
            a = line[i - bpp] if i >= bpp else 0
            c = prev[i - bpp] if i >= bpp else 0
            b = prev[i]
            pp = a + b - c
            pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
            pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            line[i] = (line[i] + pr) & 255
    else:
        raise ValueError(f"unknown PNG filter type {ft}")


def png_stats(path, max_samples=20000):
    """Luminance statistics of a PNG, decoded with nothing but zlib.

    EVERY NUMBER HERE IS A STATISTIC OF THE SAMPLE, and the sample carries its
    denominator: `pixels` is the whole image, `sampled` is how many of them
    these numbers describe, `sample_step` is the decimation. min/max/spread are
    EXTREMES over the sample; mean and stdev are its middle and its width;
    `alpha_max` is a peak. A 1024x1024 image is 1M pixels and this is pure
    Python, so it is decimated on a fixed grid - which is why `spread` is the
    load-bearing number and not, say, "how many pixels differ from the first".

    `decoded: False` with a `why` is NOT the same answer as blank. A checker
    that cannot tell "did not look" from "looked and it was empty" is the
    zero-with-no-denominator fault, and blankness is the exact thing being
    asked about here, so the two are kept apart at every layer above.
    """
    out = {"decoded": False, "why": "", "file": pathlib.Path(path).name}
    try:
        raw = pathlib.Path(path).read_bytes()
    except OSError as e:
        out["why"] = f"unreadable: {type(e).__name__}: {e}"
        return out
    out["bytes"] = len(raw)
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        out["why"] = f"not a PNG: first 8 bytes are {raw[:8]!r}"
        return out

    pos, ihdr, idat = 8, None, []
    while pos + 8 <= len(raw):
        ln = int.from_bytes(raw[pos:pos + 4], "big")
        typ = raw[pos + 4:pos + 8]
        body = raw[pos + 8:pos + 8 + ln]
        pos += 12 + ln                                  # length + type + data + crc
        if typ == b"IHDR":
            ihdr = body
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
    if not ihdr or len(ihdr) < 13:
        out["why"] = "no IHDR chunk - the file is not a whole PNG"
        return out
    w = int.from_bytes(ihdr[0:4], "big")
    h = int.from_bytes(ihdr[4:8], "big")
    depth, ctype, interlace = ihdr[8], ihdr[9], ihdr[12]
    out.update(width=w, height=h, bit_depth=depth, colour_type=ctype, pixels=w * h)
    if ctype not in _PNG_CHANNELS or depth not in (8, 16) or interlace != 0 or not w or not h:
        out["why"] = (f"unsupported PNG form: colour type {ctype}, bit depth {depth}, "
                      f"interlace {interlace}, {w}x{h}. This reader handles "
                      "non-interlaced 8/16-bit greyscale and RGB(A), which is what "
                      "stb_image_write - what sd-cli writes with - emits.")
        return out
    if not idat:
        out["why"] = "no IDAT chunk - the file has a header and no pixels"
        return out
    try:
        data = zlib.decompress(b"".join(idat))
    except zlib.error as e:
        out["why"] = f"IDAT will not inflate: {e}"
        return out

    ch = _PNG_CHANNELS[ctype]
    px = depth // 8                                     # bytes per channel
    bpp = ch * px
    stride = w * bpp
    if len(data) < (stride + 1) * h:
        out["why"] = (f"truncated pixel data: {len(data)} bytes inflated, "
                      f"{(stride + 1) * h} expected for {w}x{h}")
        return out

    step = max(1, int(((w * h) / float(max_samples)) ** 0.5))
    lum, amax = [], 0
    prev = bytearray(stride)
    off = 0
    try:
        for y in range(h):
            ft = data[off]
            off += 1
            line = bytearray(data[off:off + stride])
            off += stride
            _unfilter_row(ft, line, prev, bpp)
            if y % step == 0:
                for x in range(0, w, step):
                    i = x * bpp
                    if ch >= 3:
                        r, g, b = line[i], line[i + px], line[i + 2 * px]
                        lum.append((r * 299 + g * 587 + b * 114) // 1000)
                    else:
                        lum.append(line[i])
                    if ch in (2, 4):
                        a = line[i + (ch - 1) * px]
                        if a > amax:
                            amax = a
            prev = line
    except (IndexError, ValueError) as e:
        out["why"] = f"decode failed at row {y}: {type(e).__name__}: {e}"
        return out

    n = len(lum)
    if not n:
        out["why"] = "no pixels sampled"
        return out
    mn, mx = min(lum), max(lum)
    mean = sum(lum) / float(n)
    stdev = (sum((v - mean) ** 2 for v in lum) / float(n)) ** 0.5
    out.update(decoded=True, sampled=n, sample_step=step, min=mn, max=mx,
               spread=mx - mn, mean=round(mean, 2), stdev=round(stdev, 3),
               distinct=len(set(lum)),
               alpha_max=(amax if ch in (2, 4) else None))
    return out


def blank_verdict(st):
    """('varied' | 'blank' | 'unknown', one sentence saying why).

    THREE ANSWERS ON PURPOSE. 'unknown' is not 'varied' and is not a pass: it
    means the file could not be decoded, and it is reported as its own count
    beside the others so a run where the check never worked cannot read as a
    run where the check found nothing wrong.
    """
    if not st.get("decoded"):
        return "unknown", ("could NOT be checked for blankness: "
                           + (st.get("why") or "no reason recorded"))
    if st.get("alpha_max") == 0:
        return "blank", (f"every sampled pixel is fully transparent (alpha max 0 over "
                         f"{st['sampled']} of {st['pixels']} pixels)")
    if st["spread"] <= BLANK_MAX_SPREAD and st["stdev"] <= BLANK_MAX_STDEV:
        return "blank", (f"uniform image: luminance spread {st['spread']}/255 "
                         f"(min {st['min']}, max {st['max']}, stdev {st['stdev']}, "
                         f"{st['distinct']} distinct levels) over {st['sampled']} of "
                         f"{st['pixels']} pixels. That is the shape of "
                         "leejet/stable-diffusion.cpp#1031 - Z-Image on Vulkan "
                         "writing a blank PNG and exiting success.")
    return "varied", (f"luminance spread {st['spread']}/255, stdev {st['stdev']}, "
                      f"{st['distinct']} distinct levels over {st['sampled']} of "
                      f"{st['pixels']} pixels")


# ---------------------------------------------------------------------------
# THE SIZE AT WHICH --vae-conv-direct STOPS BEING SAFE ON THE VULKAN PATH
#
# leejet/stable-diffusion.cpp issue #1673, read here 25 Aug 2026: on AMD Radeon
# (RADV RENOIR) the Vulkan backend produces distorted / gibberish images at
# 1024x1024 WITH --vae-conv-direct, and correct images at 512x512; the
# reporter's own workaround is --vae-on-cpu.
#
# WHY THAT IS US BY DEFAULT AND NOT BY BAD LUCK. Jafar's machine is AMD -
# `live-speech-latency.md` records it and says "CUDA is not a lever" - his VRAM
# is UNKNOWN by construction, because Win32_VideoController.AdapterRAM
# saturates at 4 GB and `plan()` correctly refuses to read that as a
# measurement; and `plan()` turns --vae-conv-direct on whenever VRAM is under
# 8 GB OR UNKNOWN. Two items in prompts.json are 1024x1024. So the default path
# on his hardware walks into a reported silent-wrong-output bug.
#
# THE BOUND IS THE LARGEST SIZE THE ISSUE REPORTS AS GOOD, NOT THE SMALLEST IT
# REPORTS AS BAD. Everything between 512x512 and 1024x1024 is unmeasured by
# anybody, the failure is silent wrong output rather than a crash, and the
# alternative costs speed and not correctness. Every one of the twelve items in
# prompts.json is larger than 512x512, so ON VULKAN --vae-conv-direct WILL NOT
# BE USED AT ALL for this batch - said out loud because a flag that looks live
# and never fires is worse than one that is gone. It stays in the plan because
# the plan describes the machine, and because the CUDA path (where the issue
# does not apply) uses it.
#
# --vae-on-cpu IS REAL AND THAT WAS CHECKED, NOT ASSUMED: the pinned release
# zip was downloaded here on 25 Aug 2026 (38,784,820 bytes, byte-exact against
# SDCPP_ZIPS) and `--vae-on-cpu` is present in sd-cli.exe's string table,
# alongside every other long flag this file passes.
# ---------------------------------------------------------------------------
VULKAN_VAE_DIRECT_MAX_PX = 512 * 512


def image_flags(pl, w, h):
    """Flags for ONE image: (flags, note). The note is None when nothing moved.

    Per image rather than per plan because the fault is a function of the size,
    and the size only exists here.
    """
    flags = list(pl["flags"])
    if pl.get("backend") != "vulkan" or "--vae-conv-direct" not in flags:
        return flags, None
    if w * h <= VULKAN_VAE_DIRECT_MAX_PX:
        return flags, None
    flags = [f for f in flags if f != "--vae-conv-direct"]
    if "--vae-on-cpu" not in flags:
        flags.append("--vae-on-cpu")
    return flags, (f"--vae-conv-direct dropped at {w}x{h} and --vae-on-cpu used "
                   "instead: stable-diffusion.cpp#1673 reports gibberish from that "
                   "flag on AMD RADV Vulkan at 1024x1024 and clean output at "
                   "512x512, and this image is larger than 512x512")


# ---------------------------------------------------------------------------
# SENDING THE PICTURES BACK - the part that used to be Jafar's hands.
#
# HIS WORDS, 25 Aug: "right now it's not really 1 click. I start the bat, then
# I wait for it to finish, then I open the text file, then copy and paste here
# along with images." Every one of those steps is a fault in this design. The
# run now commits and pushes its own output, so he double-clicks once, walks
# away, and the results arrive in the repository.
#
# FOUR RULES IT OBEYS, each of which has cost this project something:
#
#  * STAGE BY NAME, NEVER `git add <directory>`. A build that rendered nothing
#    once committed its stale checkout's six JPEGs as its own evidence, under
#    the sha of the run that failed to make them. Only files this run wrote are
#    named, one at a time.
#  * PUSH INCREMENTALLY. A four-hour run that dies at hour three must have
#    already delivered three hours of work - the same rule as the evidence
#    channel being a file committed by CI. Interval below.
#  * REFUSE, DO NOT GUESS. Wrong branch, no remote, not a clone: say so in one
#    plain sentence and leave the pictures where they are. Pushing somewhere
#    else is worse than not pushing.
#  * NEVER HANG WAITING FOR A HUMAN. `GIT_TERMINAL_PROMPT=0` and
#    `GCM_INTERACTIVE=never` turn a credential prompt into a fast failure with
#    a message, because the whole point is that nobody is watching the window.
#
# EVERY FAILURE PATH PRINTS A SENTENCE A NON-PROGRAMMER CAN ACT ON, and none of
# them stops the generating: the pictures are the deliverable and they are
# already on disk. A push that cannot happen is reported and retried next
# interval.
# ---------------------------------------------------------------------------
EXPECTED_BRANCH = "claude/game-dev-ai-automation-2h67ix"
# HOW MUCH WORK A CRASH MAY COST - a policy, not a measurement, and said so.
# At the measured 90-290 s an image, three images is five to fifteen minutes.
PUBLISH_EVERY_IMAGES = 3
PUBLISH_EVERY_MINUTES = 10.0


class Publisher:
    """Commits and pushes what this run produced. Off is a valid state and it
    always says which one it is in and why."""

    def __init__(self, repo, log, branch=EXPECTED_BRANCH,
                 every_images=PUBLISH_EVERY_IMAGES,
                 every_minutes=PUBLISH_EVERY_MINUTES,
                 retry_pause=20.0, attempts=3, enabled=True):
        self.repo = pathlib.Path(repo) if repo else None
        self.log = log
        self.branch = branch
        self.every_images = every_images
        self.every_minutes = every_minutes
        self.retry_pause = retry_pause
        self.attempts = attempts
        self.enabled = enabled
        self.off_reason = None if enabled else "switched off for this run"
        self.pending = []          # paths staged next time, by NAME
        self.since = 0             # images since the last successful publish
        self.last = time.time()
        self.pushes = 0            # commits actually pushed
        self.commits = 0           # commits made (pushed or not)
        self.failures = []         # plain-English lines, for the summary
        self.checked = False

    # -- plumbing ----------------------------------------------------------
    def _git(self, args, timeout=180):
        env = dict(os.environ)
        # `GIT_TERMINAL_PROMPT=0` STAYS: it is what turns a terminal waiting
        # forever for a username into a fast, named failure, and that is the
        # whole reason an unattended run is safe to leave alone.
        #
        # `GCM_INTERACTIVE=never` IS GONE, 26 Aug, AND THIS IS A HYPOTHESIS
        # RATHER THAN A FINDING. His run failed with "could not read Username
        # for https://github.com" while `REPICK.bat` pushed successfully from
        # the same clone minutes later - so a working credential exists and
        # this process could not reach it. The likeliest reason is that
        # `GCM_INTERACTIVE=never` makes Git Credential Manager decline
        # entirely rather than serve what it has cached, which would explain
        # both halves exactly. Only his machine can settle it; the next run
        # is the test, and the failure text names itself either way.
        env.update(GIT_TERMINAL_PROMPT="0", GIT_PAGER="cat", LC_ALL="C")
        try:
            p = subprocess.run(["git", "-C", str(self.repo)] + args,
                               capture_output=True, text=True, errors="replace",
                               timeout=timeout, env=env)
            return p.returncode, (p.stdout or "") + (p.stderr or "")
        except FileNotFoundError:
            return 127, "git is not installed on this PC"
        except subprocess.TimeoutExpired:
            return 124, f"git {args[0]} took longer than {timeout/60:.0f} minutes"

    def _off(self, why):
        self.enabled = False
        self.off_reason = why
        self.log(f"  SENDING BACK IS OFF: {why}")
        return False

    # -- is this clone one we may push to? ---------------------------------
    def preflight(self):
        """Both outcomes are normal. Called once; the answer is printed."""
        if self.checked:
            return self.enabled
        self.checked = True
        if not self.enabled:
            return self._off(self.off_reason or "switched off for this run")
        if self.repo is None:
            return self._off("the repository folder was not found, so there is "
                             "nowhere to send from. The pictures are still "
                             "written to disk - zip the folder named at the end "
                             "and send that.")
        rc, out = self._git(["rev-parse", "--is-inside-work-tree"], timeout=60)
        if rc == 127:
            return self._off("Git is not installed on this PC. The pictures are "
                             "safe on disk; zip the folder named at the end and "
                             "send that instead.")
        if rc != 0 or "true" not in out:
            return self._off("this folder is not a git clone, so nothing can be "
                             "pushed from it. The pictures are safe on disk - "
                             "zip the folder named at the end and send that.")
        rc, out = self._git(["rev-parse", "--abbrev-ref", "HEAD"], timeout=60)
        here = out.strip().splitlines()[-1] if out.strip() else "?"
        if rc != 0 or here != self.branch:
            return self._off(
                f"this clone is on branch '{here}', and the pictures belong on "
                f"'{self.branch}'. NOTHING was sent, on purpose - pushing to the "
                "wrong branch is worse than not pushing. Switch the clone to "
                f"'{self.branch}' and run this again; the pictures already made "
                "are kept and will be sent then.")
        rc, out = self._git(["remote"], timeout=60)
        if rc != 0 or "origin" not in out.split():
            return self._off("this clone has no 'origin' to send to. The "
                             "pictures are safe on disk.")
        self.log(f"  sending back is ON: branch {self.branch}, every "
                 f"{self.every_images} pictures or {self.every_minutes:.0f} minutes")
        return True

    # -- what to stage -----------------------------------------------------
    def note(self, path):
        """Name ONE file to include in the next commit. Never a directory."""
        if path is None:
            return
        p = pathlib.Path(path)
        if p not in self.pending:
            self.pending.append(p)

    def note_image(self, path):
        self.note(path)
        self.since += 1

    def due(self):
        return (self.since >= self.every_images
                or (time.time() - self.last) / 60.0 >= self.every_minutes)

    def maybe(self, message, force=False):
        if not self.enabled or (not force and not self.due()):
            return None
        return self.publish(message)

    # -- the act ------------------------------------------------------------
    def publish(self, message):
        """Commit the named files and push. Returns 'pushed' / 'committed' /
        'nothing' / 'off', and prints a plain sentence for every one of them."""
        if not self.preflight():
            return "off"
        names = []
        for p in self.pending:
            try:
                rel = pathlib.Path(p).resolve().relative_to(self.repo.resolve())
            except (ValueError, OSError):
                continue                      # outside the repo: not ours to send
            if (self.repo / rel).exists():
                names.append(str(rel).replace("\\", "/"))
        self.pending = []
        if not names:
            self.log("  nothing new to send - no new or changed pictures since "
                     "the last time.")
            return "nothing"
        rc, out = self._git(["add", "--"] + names, timeout=300)
        if rc != 0:
            return self._fail("could not prepare the pictures for sending", out)
        rc, _ = self._git(["diff", "--cached", "--quiet"], timeout=120)
        if rc == 0:
            self.log("  nothing new to send - the pictures on disk are already "
                     "the ones that were sent last time.")
            return "nothing"
        commit = ["commit", "-m", message]
        rc, out = self._git(["config", "user.email"], timeout=60)
        if rc != 0 or not out.strip():
            # A COMMIT NEEDS A NAME AND THIS PC MAY NOT HAVE ONE. Its own
            # identity, not his: nothing here should write somebody's address
            # into a commit they did not make.
            commit = ["-c", "user.name=LEDGER imagegen",
                      "-c", "user.email=imagegen@ledger.local"] + commit
            self.log("  (this PC has no git name set, so the commit is made as "
                     "'LEDGER imagegen' - nothing to fix, just saying so)")
        rc, out = self._git(commit, timeout=300)
        if rc != 0:
            return self._fail("could not save the pictures into this PC's copy "
                              "of the project", out)
        self.commits += 1
        self.since = 0
        for n, attempt in enumerate(range(self.attempts), 1):
            rc, out = self._git(["pull", "--rebase", "origin", self.branch], timeout=600)
            if rc != 0:
                self._git(["rebase", "--abort"], timeout=120)
                if n < self.attempts:
                    self.log(f"  someone else pushed while this ran - trying "
                             f"again ({n} of {self.attempts})")
                    time.sleep(self.retry_pause)
                    continue
                return self._fail(
                    "someone else pushed to the project while this was running, "
                    "and the two could not be merged automatically. The pictures "
                    "are SAFE - they are saved in this PC's copy. Run this again "
                    "later and it will send them.", out)
            rc, out = self._git(["push", "origin", f"HEAD:{self.branch}"], timeout=900)
            if rc == 0:
                self.pushes += 1
                self.last = time.time()
                self.log(f"  SENT: {len(names)} file(s) pushed to {self.branch} "
                         f"({message})")
                return "pushed"
            low = out.lower()
            if ("authentication" in low or "could not read username" in low
                    or "permission denied" in low or "403" in low):
                return self._fail(
                    "this PC could not sign in to GitHub, so the pictures could "
                    "not be sent. They are SAFE - saved in this PC's copy of the "
                    "project. Nothing needs installing; tell Claude and it will "
                    "fetch them another way.", out)
            if n < self.attempts:
                self.log(f"  sending did not go through - trying again "
                         f"({n} of {self.attempts})")
                time.sleep(self.retry_pause)
        return self._fail(
            f"could not send after {self.attempts} tries. The pictures are SAFE "
            "- they are saved in this PC's copy of the project. Run this again "
            "later and it will send everything at once.", out)

    def _fail(self, sentence, detail=""):
        self.log(f"  COULD NOT SEND: {sentence}")
        for line in (detail or "").strip().splitlines()[-6:]:
            self.log(f"      {line}")
        self.failures.append(sentence)
        self.last = time.time()          # do not retry every single image
        return "failed"

    def summary(self):
        if not self.enabled:
            return f"sending back was OFF: {self.off_reason}"
        return (f"sent back {self.pushes} time(s), {self.commits} commit(s) made"
                + (f"; {len(self.failures)} could not be sent" if self.failures else ""))


# ---------------------------------------------------------------------------
# GENERATE
# ---------------------------------------------------------------------------
def round16(n):
    return max(256, int(round(n / 16.0)) * 16)


def load_made(outdir, spec):
    """What is already on disk and WHAT MADE IT - the resume record.

    `made.json` is written after every image, so a run killed by a crash, a
    reboot or a closed window continues from what it actually finished rather
    than from the beginning. It records the RECIPE (see `recipe_of`), which is
    what lets a changed prompt regenerate and an unchanged one skip.

    LEGACY, and it is not hypothetical: the first real run (25 Aug) wrote a
    manifest and no made.json. Rather than treat those twelve as unknown, the
    recipe is reconstructed from the PROMPT THE MANIFEST RECORDED, so an item
    whose prompt has not changed is still skipped. Where the old record cannot
    supply the prompt or the size, the item is unknown and is made again -
    "there is a file" was never the question.
    """
    made, source = {}, "nothing on record"
    mp = pathlib.Path(outdir) / "made.json"
    if mp.exists():
        try:
            made = json.loads(mp.read_text(encoding="utf-8")).get("items", {})
            source = f"made.json, {len(made)} item(s)"
            return made, source
        except Exception as e:                                # noqa: BLE001
            source = f"made.json unreadable ({type(e).__name__}), falling back"
    legacy = pathlib.Path(outdir) / "manifest.json"
    if legacy.exists():
        try:
            old = json.loads(legacy.read_text(encoding="utf-8"))
            by_id = {i["id"]: i for i in spec.get("items", [])}
            d = spec.get("defaults", {})
            n = 0
            for rec in old.get("images", []):
                it = by_id.get(rec.get("id"))
                if not it or rec.get("status") not in ("OK", "SKIPPED"):
                    continue
                if not rec.get("prompt") or rec.get("seed") is None:
                    continue
                made[rec["id"]] = {
                    "recipe": recipe_of(it, rec["prompt"], "",
                                        rec.get("width"), rec.get("height"),
                                        rec.get("cfg", d.get("cfg", 1.0)),
                                        rec.get("steps", d.get("steps", 8)),
                                        rec["seed"], False),
                    "from": "reconstructed from the previous manifest",
                }
                n += 1
            source = f"the previous manifest, {n} item(s) reconstructed"
        except Exception as e:                                # noqa: BLE001
            source = f"previous manifest unreadable ({type(e).__name__})"
    return made, source


def save_made(outdir, made):
    (pathlib.Path(outdir) / "made.json").write_text(json.dumps({
        "_what": "The resume record: what is on disk and which recipe made it. "
                 "Delete this file to have everything made again, or delete one "
                 "PNG to have just that one made again.",
        "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "items": made,
    }, indent=2) + "\n", encoding="utf-8")


def write_progress(outdir, manifest, rows, started, remaining_estimate):
    """PROGRESS.txt - so a long run can be read from the REPOSITORY rather than
    from his screen. It is committed with the pictures; nobody has to be asked
    how far it has got.

    Every line says which of the four states it is in, and the totals carry the
    denominator: `0 failed` beside `of 14` is a fact, `0 failed` on its own is
    not.
    """
    el = (time.time() - started) / 60.0
    L = ["LEDGER imagegen - progress",
         "=" * 58,
         f"batch     {manifest['batch']}",
         f"status    {manifest['status']}",
         f"updated   {time.strftime('%Y-%m-%d %H:%M:%S')} local",
         f"elapsed   {el:.0f} min",
         f"done      {manifest['items_written']} written, "
         f"{manifest['items_skipped']} already there, {manifest['items_failed']} "
         f"failed, of {manifest['items_in_spec']} in the batch",
         f"still to do  {len(manifest['not_attempted'])}"
         + (f", about {remaining_estimate/60.0:.0f} min at the measured rate "
            f"({COST_SOURCE})" if remaining_estimate else ""),
         ""]
    for r in rows:
        L.append(f"  {r}")
    L.append("")
    L.append("Every image is review=pending until a human has looked at it.")
    (pathlib.Path(outdir) / "PROGRESS.txt").write_text("\n".join(L) + "\n",
                                                       encoding="utf-8")


def run_batch(exe, ws, pl, spec, outdir, max_minutes, log, redo=False,
              publisher=None, only=None, limit=None, run_sha="local",
              fail_on_blank=False):
    """Generate the batch. Writes each PNG, rewrites the manifest and the resume
    record as it goes, and hands each finished picture to the publisher, so a
    run killed halfway has already delivered - and can be resumed - rather than
    losing everything it did.

    PER-ITEM SKIP, and why it is not optional. Every re-run used to regenerate
    all twelve and overwrite what was there, so the instruction that went with
    it was "copy fascia_mickeys.png and fascia_ritas_pawn.png aside by hand
    first" - a second decision, handed to the person whose whole requirement is
    that there be only one. An item is left alone when its PNG is on disk, it
    passes the blank check, AND the recipe on record matches the one this run
    would use; anything else is made again and SAID SO, per item and in the
    summary. A BLANK or undecodable one is never skipped, because "a file
    exists" is not the question - "is there a picture there" is, and that is the
    same question #1031 forced this file to start asking of the exit code.
    `redo=True` (--redo) ignores everything on disk; deleting one PNG is the
    per-item version and needs no flag.

    A FAILING IMAGE DOES NOT END THE RUN. It is logged, recorded in the
    manifest and the next one starts - the batch is meant to run for hours with
    nobody watching. The ONE early stop left is the first two BOTH failing with
    nothing written, which is a broken runtime rather than a bad prompt, and it
    says so.
    """
    # The writer owns its directory. main() also makes this, but a function
    # that writes twelve files and a manifest should not depend on a caller
    # having remembered to - that is how the first selftest of it died.
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rules = spec["content_rules"]["rules_clause"]
    forbidden = spec["content_rules"]["forbidden_tokens"]
    style = spec["style"]
    d = spec["defaults"]
    items = spec["items"]

    # THE SELECTION, AND IT IS TWO DIFFERENT QUESTIONS FROM THE CPU CAP.
    # `only` names ids and answers WHICH; `limit` bounds how many pictures this
    # run will GENERATE and answers HOW MANY. They exist for the unattended
    # lane: the first dispatch of a new route proves it on a handful, because a
    # night that produces 31 unproven pictures and a manifest describing them
    # is worse than a night that produces four and a verdict anybody can read.
    #
    # `limit` COUNTS GENERATIONS, NOT POSITIONS IN THE LIST. An item already on
    # disk that passes the skip check cost nothing and does not spend the
    # budget, so `--limit 4` on a batch whose first fourteen are already made
    # generates the next four rather than stopping inside the finished part.
    # That is the whole difference between a flag that proves a route and a
    # flag that quietly proves nothing.
    unknown = []
    if only:
        want = list(dict.fromkeys(only))
        known = {i["id"] for i in items}
        unknown = [o for o in want if o not in known]
        selected = [i for i in items if i["id"] in set(want)]
    else:
        selected = list(items)
    caps_note = []
    if only:
        caps_note.append(f"--only: {len(selected)} of {len(items)} item(s) "
                         "selected by name")
    capped = None
    if pl["item_limit"]:
        capped = (f"CAP: {pl['item_limit']} of {len(selected)} selected item(s) "
                  "attempted (CPU mode)")
        items_run = selected[:pl["item_limit"]]
    else:
        items_run = selected
    if limit is not None:
        caps_note.append(f"--limit: at most {limit} picture(s) GENERATED this "
                         "run; items already on disk that pass the skip check "
                         "do not count against it")

    manifest = {
        "batch": spec["batch_name"],
        "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "RUNNING",
        # WHICH COMMIT THIS RUN IS. Without it, a manifest from last week and a
        # manifest from tonight are the same file to every reader downstream,
        # and "the job carried the commit" reads as "the job made a picture".
        # `imagegen_verdict` refuses a manifest whose sha is not the run's.
        "run": {"sha": run_sha, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "what": "the commit this batch was generated on; 'local' means "
                        "it was run by hand rather than by CI"},
        "generator": {
            "tool": "stable-diffusion.cpp", "tool_licence": "MIT",
            "tool_release": SDCPP_TAG, "backend": pl["backend"],
            "exe": str(exe),
        },
        "model": dict(MODEL, quant=pl["quant"], file=pl["quant_file"]),
        "text_encoder": {k: TEXT_ENCODER[k] for k in ("file", "licence")},
        "vae": {k: VAE[k] for k in ("file", "licence")},
        "machine_plan": {k: pl[k] for k in ("vendor", "vram_gb", "vram_known",
                                            "backend", "quant", "flags")},
        "content_rules": spec["content_rules"]["rules_clause"],
        "rights": ("Model weights Apache-2.0; outputs unrestricted by the model "
                   "licence. No third-party asset was an input. Prompts name only "
                   "in-world Meridian businesses. NOTHING SHIPS UNREVIEWED: every "
                   "image below is review=pending until a human has looked for "
                   "anything resembling a real mark or a real face."),
        "caps": [c for c in [capped, *caps_note,
                             f"resolution scaled x{pl['size_scale']}" if pl["size_scale"] != 1 else None,
                             f"wall-clock cap {max_minutes} min"] if c],
        # THE CHECK THAT DOES NOT TRUST THE EXIT CODE, and its denominators.
        # `checked` is how many PNGs were OPENED AND MEASURED - undecodable
        # ones included, and counted again under their own key - so `blank: 0`
        # cannot be confused with a check that never ran, and a run where the
        # decoder failed on everything cannot read as a run that found nothing
        # wrong. Three answers, three numbers.
        "blank_check": {
            "what": "every written PNG is decoded and its luminance measured; a "
                    "uniform image is the known Vulkan failure "
                    "(leejet/stable-diffusion.cpp#1031: blank PNG, exit success)",
            "bound": f"blank when spread <= {BLANK_MAX_SPREAD}/255 AND stdev <= "
                     f"{BLANK_MAX_STDEV}, or alpha is 0 everywhere sampled",
            "checked": 0, "blank": 0, "undecodable": 0,
            # A DIFFERENT MOMENT, SO A DIFFERENT KEY. `checked` counts PNGs
            # THIS RUN WROTE and then measured. `rechecked` counts PNGs found
            # already on disk and measured to decide whether to skip them, and
            # `remade` is how many of those failed that check and were
            # generated again. Folding them into `checked` would put two
            # moments under one key and make "0 blank" ambiguous about which
            # population it describes.
            "rechecked": 0, "remade": 0,
        },
        # A THIRD REASON TO REMAKE, AND IT IS NOT A BLANK ONE. `remade` above
        # counts pictures that were on disk and were not pictures. These two
        # count pictures that were fine and were made from a DIFFERENT recipe -
        # the prompt changed - or from one nothing recorded. Same action, three
        # different facts, so three numbers rather than one.
        "resume": {"what": "recipe = prompt + negative(if it can act) + size + "
                           "cfg + steps + seed; a match is skipped, a mismatch "
                           "is made again",
                   "record": "", "kept": 0, "prompt_changed": 0, "unrecorded": 0},
        "negatives": {"what": "--negative-prompt is passed whenever an item has "
                              "one; it only ACTS when cfg != 1.0, because sd-cli "
                              "evaluates the unconditional branch only then",
                      "carried": 0, "active": 0, "inert_at_cfg1": 0},
        # THREE DENOMINATORS, BECAUSE THEY ARE THREE DIFFERENT SETS.
        # `items_in_spec` is everything written in prompts.json,
        # `items_selected` is what this run was asked for, and `limit` bounds
        # what it may generate out of that. A count of failures against the
        # wrong one of these is a clean result with a number attached.
        "items_in_spec": len(items),
        "items_selected": len(items_run),
        "selection": {"only": list(only) if only else None, "limit": limit,
                      "selected": len(items_run), "of": len(items),
                      "what": "only = the ids asked for by name; limit = how "
                              "many pictures this run may GENERATE, which "
                              "skipped items do not count against"},
        "items_attempted": 0, "items_written": 0, "items_failed": 0,
        "items_skipped": 0,
        "not_attempted": [i["id"] for i in items
                          if i["id"] not in {x["id"] for x in items_run}],
        "images": [],
    }
    mpath = outdir / "manifest.json"

    def save():
        mpath.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # THE PROMPT FILE IS CHECKED BEFORE ANYTHING IS GENERATED, and a bad one
    # stops the batch rather than producing twelve pictures of the fault. Both
    # outcomes are exercised in the selftest: the live prompts.json is the
    # accepting case, a synthetic broken spec is the rejecting one.
    problems = validate_spec(spec)
    # AN `--only` THAT NAMES NOTHING MUST NOT READ AS A RUN WITH NOTHING TO DO.
    # A typo in a dispatch input is the likeliest way this route fails, and the
    # failure it would otherwise wear is "0 generated, everything fine".
    if unknown:
        problems.append(
            f"--only named {len(unknown)} id(s) that are in no prompt: "
            + ",".join(sorted(unknown))
            + f" (of {len(only)} asked for, against {len(items)} in the spec)")
    if only and not items_run:
        problems.append("--only selected 0 of "
                        f"{len(items)} items, so there is nothing to generate")
    if problems:
        manifest["status"] = "REFUSED"
        manifest["problems"] = problems
        log("  REFUSED TO START: prompts.json is not usable as it stands.")
        for p in problems:
            log(f"    - {p}")
        save()
        return manifest

    made, made_source = load_made(outdir, spec)
    manifest["resume"]["record"] = made_source
    save()
    t_start = time.time()
    rows, consecutive_fail = [], 0

    def progress_rows():
        done = {r["id"]: r for r in manifest["images"]}
        out, todo = [], 0.0
        for it in items_run:
            r = done.get(it["id"])
            w = round16(it["width"] * pl["size_scale"])
            h = round16(it["height"] * pl["size_scale"])
            if r is None:
                est = estimate_seconds(w, h, item_cfg(it, d))
                todo += est
                out.append(f"[pending] {it['id']:<26} {w}x{h}  about {est:.0f}s")
            elif r["status"] == "OK":
                out.append(f"[made]    {it['id']:<26} {w}x{h}  {r.get('seconds', 0):.0f}s")
            elif r["status"] == "SKIPPED":
                out.append(f"[already] {it['id']:<26} left exactly as it was")
            else:
                out.append(f"[FAILED]  {it['id']:<26} {r.get('why', r.get('status'))}"[:110])
        return out, todo

    for n, item in enumerate(items_run, 1):
        # THE UNATTENDED LANE'S STOP, and it is ONE test covering both bad
        # outcomes: a blank PNG and a PNG that could not be read at all. #1031
        # is a known mode, not a surprise; reproducing it thirty more times
        # overnight teaches nothing and costs the night. It is checked here,
        # before the next item starts, rather than inside the failure branch,
        # because an UNDECODABLE image is not routed through that branch and
        # would otherwise be the half this stop never saw.
        if fail_on_blank and (manifest["blank_check"]["blank"]
                              or manifest["blank_check"]["undecodable"]):
            bcs = manifest["blank_check"]
            log(f"  STOPPING (--fail-on-blank): {bcs['blank']} blank and "
                f"{bcs['undecodable']} undecodable of {bcs['checked']} PNG(s) "
                f"this run decoded, after {n-1} of {len(items_run)} item(s). "
                "Nothing else is generated, and the run exits 6.")
            manifest["caps"].append(
                f"--fail-on-blank stopped the run after {n-1} of "
                f"{len(items_run)} item(s): {bcs['blank']} blank, "
                f"{bcs['undecodable']} undecodable of {bcs['checked']} decoded")
            break
        if (time.time() - t_start) / 60.0 > max_minutes:
            log(f"  STOPPING: wall-clock cap of {max_minutes} min reached after "
                f"{n-1} of {len(items_run)} images. The rest are listed in the "
                f"manifest under not_attempted; re-run to continue - nothing "
                f"already made will be made again.")
            break
        prompt = build_prompt(item, rules, style)
        negative = build_negative(item, spec)
        cfg = item_cfg(item, d)
        seed = item_seed(item, d)
        steps = d["steps"]
        neg_active, neg_why = negative_state(cfg, negative)
        bad = check_forbidden(prompt + " " + negative, forbidden)
        # TWO KEYS, TWO FACTS. `seen_on_run` says this run LOOKED at the item;
        # `made_on_run` is set below only when this run actually generated the
        # picture. Folding them into one is how a run that skipped fourteen
        # finished PNGs would read as a run that made fourteen.
        rec = {"id": item["id"], "kind": item["kind"], "binds_to": item["binds_to"],
               "prompt": prompt, "negative": negative,
               "negative_active": neg_active, "negative_note": neg_why,
               "seen_on_run": run_sha,
               "review": "pending"}
        if item.get("probe"):
            rec["probe"] = True
        if negative:
            manifest["negatives"]["carried"] += 1
            manifest["negatives"]["active" if neg_active else "inert_at_cfg1"] += 1
        if bad:
            rec.update(status="REFUSED", why=f"prompt names forbidden mark(s): {bad}")
            manifest["images"].append(rec)
            manifest["items_failed"] += 1
            log(f"  [{n}/{len(items_run)}] REFUSED {item['id']}: {bad}")
            save()
            continue
        w = round16(item["width"] * pl["size_scale"])
        h = round16(item["height"] * pl["size_scale"])
        # FLAGS ARE A FUNCTION OF THE SIZE, NOT ONLY OF THE MACHINE - #1673.
        img_flags, flag_note = image_flags(pl, w, h)
        recipe = recipe_of(item, prompt, negative, w, h, cfg, steps, seed, neg_active)
        rec["recipe"] = recipe
        png = outdir / f"{item['id']}.png"
        # ALREADY MADE? Three questions, not one: is there a file, is there a
        # PICTURE in it, and was it made from THIS prompt. Only all three earn
        # the skip, and each failure is counted under its own name.
        if png.exists() and not redo:
            st = png_stats(png)
            verdict, why = blank_verdict(st)
            manifest["blank_check"]["rechecked"] += 1
            on_record = (made.get(item["id"]) or {}).get("recipe")
            if verdict != "varied":
                manifest["blank_check"]["remade"] += 1
                log(f"  [{n}/{len(items_run)}] {item['id']}  the PNG already here is "
                    f"{verdict.upper()}, so it is NOT skipped - making it again")
                log(f"      {why}")
            elif on_record is None:
                manifest["resume"]["unrecorded"] += 1
                log(f"  [{n}/{len(items_run)}] {item['id']}  nothing on record says "
                    "which prompt made the PNG already here, so it is NOT skipped "
                    "- making it again")
            elif on_record != recipe:
                manifest["resume"]["prompt_changed"] += 1
                log(f"  [{n}/{len(items_run)}] {item['id']}  the prompt or settings "
                    "changed since the PNG already here was made, so it is NOT "
                    "skipped - making it again")
            else:
                rec.update(status="SKIPPED", file=png.name,
                           bytes=png.stat().st_size, sha256=sha256(png),
                           # MEASURED OFF THE FILE, NOT CLAIMED. This run did
                           # not make it, so it cannot say which flags produced
                           # it - only what is in the pixels and what the resume
                           # record says the recipe was.
                           made_by="an earlier run - this run did not make it, so "
                                   "the size below is measured from the file and "
                                   "no flags are recorded for it",
                           width=st.get("width"), height=st.get("height"),
                           why="already on disk, it passed the blank check, and "
                               "the recipe on record is the one this run would use",
                           blank_check={"verdict": verdict, "why": why,
                                        "spread": st.get("spread"),
                                        "stdev": st.get("stdev"),
                                        "distinct": st.get("distinct"),
                                        "sampled": st.get("sampled"),
                                        "pixels": st.get("pixels")})
                manifest["items_skipped"] += 1
                manifest["resume"]["kept"] += 1
                manifest["images"].append(rec)
                log(f"  [{n}/{len(items_run)}] {item['id']}  SKIP, already made "
                    f"({png.stat().st_size/1024:.0f} KB, spread {st.get('spread')}"
                    f"/255) - delete {png.name} to make it again")
                # A SKIPPED PICTURE STILL HAS TO REACH THE PROJECT, and until
                # 26 Aug it did not: only images this run WROTE were handed to
                # the sender, so the run that was dispatched specifically to
                # bank twelve finished pictures skipped all fourteen, pushed
                # the manifest and the report, and left every PNG on the PC.
                # The question the sender answers is "is this picture in the
                # repository", not "did this run make it" - and `note` is
                # idempotent, so one already committed costs an unchanged path
                # in `git add` and nothing else.
                if publisher is not None:
                    publisher.note(png)
                save()
                continue
        # THE SMALL-BATCH STOP, and it sits HERE rather than at the top of the
        # loop on purpose: everything above this line is free (an item already
        # on disk is rechecked and skipped), and the budget being spent is
        # GENERATION. The remaining ids land in not_attempted, which is derived
        # from what was tried, so the manifest says exactly what is left.
        if limit is not None and manifest["items_attempted"] >= limit:
            log(f"  STOPPING: --limit {limit} reached after generating "
                f"{manifest['items_attempted']} picture(s); "
                f"{len(items_run) - n + 1} of {len(items_run)} selected item(s) "
                "are left and are listed in the manifest under not_attempted. "
                "Re-run to continue: nothing already made will be made again.")
            manifest["caps"].append(
                f"--limit {limit} reached: {manifest['items_attempted']} "
                f"generated, {len(items_run) - n + 1} of {len(items_run)} "
                "selected item(s) left")
            break
        cmd = [str(exe),
               "--diffusion-model", str(ws / "models" / pl["quant_file"]),
               "--vae", str(ws / "models" / VAE["file"]),
               "--llm", str(ws / "models" / TEXT_ENCODER["file"]),
               # LONG FORMS ONLY, AND THAT IS A MEASUREMENT. Every flag on
               # this command was checked against the string table of the
               # actual shipped sd-cli.exe, downloaded and unzipped here on
               # 25 Aug. The long forms are all present; the short forms
               # (-p -W -H -s -o -v) are single characters, which `strings`
               # cannot see, so using them would have meant trusting a doc
               # example over the binary. Same command, one less guess.
               "--prompt", prompt,
               # NO --sampling-method ON PURPOSE. The docs' Flux example passes
               # `euler`, but the binary's own help says "default: euler for
               # Flux/SD3/Wan, euler_a otherwise" and the scheduler default is
               # "model-specific" - so sd-cli already knows what Z-Image wants
               # and we do not. The enum could not be read out of the string
               # table, and a wrong sampler name fails EVERY image in the batch.
               # Omitting the flag trades a guess for the maintainer's default.
               "--cfg-scale", str(cfg),
               "--steps", str(steps),
               "--width", str(w), "--height", str(h),
               "--seed", str(seed), "--output", str(png),
               "--verbose"] + img_flags
        # THE NEGATIVE, AND THE FLAG IS VERIFIED RATHER THAN REMEMBERED:
        # `--negative-prompt` is in the string table of the sd-cli.exe this
        # pipeline downloads, followed by its own help text `the negative
        # prompt (default: "")`. It is passed whenever the item has one, and
        # the manifest records whether it could ACT - see `negative_state`.
        if negative:
            cmd += ["--negative-prompt", negative]
        rec.update(width=w, height=h, seed=seed, steps=steps, cfg=cfg,
                   sampler="sd-cli model-specific default (not overridden)",
                   flags=img_flags)
        if flag_note:
            rec["flag_note"] = flag_note
        manifest["items_attempted"] += 1
        est = estimate_seconds(w, h, cfg)
        log(f"  [{n}/{len(items_run)}] {item['id']}  {w}x{h}  seed {seed}  "
            f"cfg {cfg}  about {est:.0f}s")
        if negative and not neg_active:
            log(f"      negative prompt recorded but INERT at cfg {cfg} - "
                "sd-cli only evaluates it when cfg is not 1.0")
        if flag_note:
            log(f"      {flag_note}")
        t0 = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        dt = time.time() - t0
        rec["seconds"] = round(dt, 1)
        # DID IT WORK? THE EXIT CODE CANNOT ANSWER THAT - #1031 exits zero and
        # writes a blank PNG, on this exact model and backend. So there are two
        # gates here and the file is the second one.
        failed = None
        if proc.returncode != 0 or not png.exists():
            tail = (proc.stderr or proc.stdout or "")[-1500:]
            rec.update(status="FAILED", exit_code=proc.returncode, log_tail=tail)
            failed = f"exit {proc.returncode}"
            log(f"      FAILED after {dt:.0f}s, exit {proc.returncode}")
            log("      last output from the generator:")
            for line in tail.strip().splitlines()[-12:]:
                log(f"        {line}")
        else:
            st = png_stats(png)
            verdict, why = blank_verdict(st)
            rec["blank_check"] = {"verdict": verdict, "why": why,
                                  "spread": st.get("spread"), "stdev": st.get("stdev"),
                                  "distinct": st.get("distinct"),
                                  "sampled": st.get("sampled"), "pixels": st.get("pixels")}
            manifest["blank_check"]["checked"] += 1
            if verdict == "unknown":
                manifest["blank_check"]["undecodable"] += 1
            if verdict == "blank":
                manifest["blank_check"]["blank"] += 1
                # NOT COUNTED AS PRODUCED, AND NOT LEFT LOOKING PRODUCED. The
                # file is kept because it is the evidence, and renamed because
                # a blank <id>.png sitting in the output directory is exactly
                # what a later reader would mistake for a delivered image.
                dead = png.with_suffix(".BLANK.png")
                try:
                    png.replace(dead)
                    rec["file"] = dead.name
                except OSError:
                    rec["file"] = png.name
                rec.update(status="FAILED", exit_code=proc.returncode,
                           why="BLANK IMAGE - " + why,
                           log_tail=(proc.stderr or proc.stdout or "")[-1500:])
                failed = "blank image"
                log(f"      FAILED after {dt:.0f}s: THE GENERATOR EXITED "
                    f"{proc.returncode} AND WROTE A BLANK IMAGE.")
                log(f"        {why}")
                log("        This is leejet/stable-diffusion.cpp#1031, open since "
                    "2 Dec 2025: Z-Image on the Vulkan backend can write an empty "
                    "PNG and report success. Nothing is wrong with your machine.")
                log(f"        kept as {rec['file']} so it can be looked at.")
            elif verdict == "unknown":
                log(f"      note: the blank check could not read this PNG - {why}")
                log("        The image is kept and counted as written; it has NOT "
                    "been shown to be good, only not shown to be bad.")
        if failed:
            manifest["images"].append(rec)
            manifest["items_failed"] += 1
            consecutive_fail += 1
            save()
            rows, todo = progress_rows()
            write_progress(outdir, manifest, rows, t_start, todo)
            if manifest["items_failed"] >= 2 and manifest["items_written"] == 0:
                log("  STOPPING: the first two images both failed and none has "
                    "succeeded. Something is wrong with the runtime or the "
                    "weights, and twelve identical failures help nobody. Send "
                    "back the machine report and this log.")
                if manifest["blank_check"]["blank"]:
                    log("  Both were BLANK rather than errors, which is the known "
                        "Vulkan bug (#1031) and not your machine. The named next "
                        "thing to try is in the machine report.")
                break
            log("      the run CONTINUES - one bad picture does not stop the "
                "batch, and the count is in the summary at the end")
            continue
        consecutive_fail = 0
        rec.update(status="OK", bytes=png.stat().st_size, sha256=sha256(png),
                   file=png.name, made_on_run=run_sha)
        manifest["items_written"] += 1
        made[item["id"]] = {"recipe": recipe, "seed": seed, "file": png.name,
                            "when": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "from": "made by this run"}
        save_made(outdir, made)
        bc = rec["blank_check"]
        log(f"      ok  {dt:.0f}s  {png.stat().st_size/1024:.0f} KB  "
            + (f"{bc['verdict']}: spread {bc['spread']}/255, "
               f"{bc['distinct']} levels over {bc['sampled']} of {bc['pixels']} px"
               if bc["spread"] is not None else f"{bc['verdict']}: not decoded"))
        if n == 1:
            est_all = dt * len(items_run) / 60.0
            log(f"      first image took {dt:.0f}s, so the batch projects to "
                f"about {est_all:.0f} min for {len(items_run)} images")
        manifest["images"].append(rec)
        save()
        rows, todo = progress_rows()
        write_progress(outdir, manifest, rows, t_start, todo)
        # SEND IT BACK NOW, NOT AT THE END. Three pictures or ten minutes,
        # whichever comes first: the most a crash can cost is one interval.
        if publisher is not None:
            publisher.note_image(png)
            publisher.note(outdir / "manifest.json")
            publisher.note(outdir / "made.json")
            publisher.note(outdir / "PROGRESS.txt")
            publisher.maybe(f"Meridian pictures: {manifest['items_written']} of "
                            f"{len(items_run)} made")

    # DERIVED, NOT ACCUMULATED. Every break out of the loop above used to have
    # to remember to fill this in, and one of them did not. Reading it off the
    # attempted set makes it true for every exit, including a crash.
    tried = {r["id"] for r in manifest["images"]}
    manifest["not_attempted"] = [i["id"] for i in items if i["id"] not in tried]
    # A SKIPPED ITEM IS PRESENT, so it counts towards DONE - the question this
    # status answers is "is the batch on disk", not "did this run do work".
    # Reading it off written-only would call a re-run of a finished batch
    # INCOMPLETE, which is the opposite of what happened.
    manifest["status"] = ("DONE" if manifest["items_written"]
                          + manifest["items_skipped"] == len(items)
                          else "INCOMPLETE")
    manifest["written"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save()
    rows, todo = progress_rows()
    write_progress(outdir, manifest, rows, t_start, todo)
    return manifest


def write_attribution(outdir, manifest):
    """Provenance travels WITH the files, written by the same run that writes
    them, so the two cannot drift apart."""
    (outdir / "ATTRIBUTION.json").write_text(json.dumps({
        "what": "Generated signage and surface art for Meridian.",
        "made_by": "tools/imagegen (stable-diffusion.cpp, MIT) running "
                   f"{MODEL['name']} {manifest['model'].get('quant')}",
        "model": MODEL["upstream"], "model_licence": MODEL["licence"],
        "model_licence_note": MODEL["licence_note"],
        "text_encoder": TEXT_ENCODER["file"], "text_encoder_licence": TEXT_ENCODER["licence"],
        "vae": VAE["file"], "vae_licence": VAE["licence"],
        "third_party_inputs": "none - no fetched asset was an input to any image",
        "attribution_required": "no - Apache-2.0 weights, outputs unrestricted; "
                                "recorded anyway because this project records "
                                "provenance whether or not a licence compels it",
        "rules": manifest["content_rules"],
        "review": "every image is review=pending in manifest.json until a human "
                  "has looked at it for real marks and real faces",
    }, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# THE COMMITTED EVIDENCE FILE, AND WHY THE ARITHMETIC IS HERE
#
# The unattended lane runs this file on Jafar's PC through
# .github/workflows/ledger-imagegen.yml, and nobody watches it. The only thing
# that comes back is what CI commits, so the run needs one file that says what
# it generated, measured from the bytes, with the commit on line 1.
#
# It lives in this module rather than in that workflow's YAML because a
# formatter written into a `run:` block ships UNRUN, and an unrun formatter
# printing a plausible string is the silent-instrument failure this project has
# a standing rule about. The workflow supplies only the step outcomes and the
# sha; everything that counts, measures or formats is here, under --selftest.
#
# IT RE-MEASURES RATHER THAN BELIEVING THE MANIFEST. Every PNG the manifest
# names is opened and its luminance read AGAIN here. That is not distrust of
# the code above: it is the shape of leejet/stable-diffusion.cpp#1031, where
# the thing that lies is an exit code and the only witness is the file. One
# number believed on somebody else's word is how a night of blank PNGs ships
# with a manifest calling it art.
# ---------------------------------------------------------------------------
VERDICT_NAME = "imagegen-verdict.txt"
# A CAP THAT ANNOUNCES ITSELF. Forty per-picture lines is more than any batch
# this run can generate under the limit the unattended lane uses, and if it
# ever bites the next line says by how much.
VERDICT_SAMPLE_CAP = 40


def output_dir(repo=None, ws=None, out=None):
    """WHERE THE PICTURES GO. ONE IMPLEMENTATION, because --verdict and
    --staged-files have to name the same directory the batch wrote to, and two
    copies of this expression is how a verdict ends up measuring an empty
    folder and reporting a clean nothing."""
    if out:
        return pathlib.Path(out)
    if repo:
        return pathlib.Path(repo) / "ledger/Assets/StreamingAssets/Decals/generated"
    return (pathlib.Path(ws) if ws else pathlib.Path.cwd() / "ledger-imagegen") / "generated"


def _read_manifest(outdir):
    """(manifest|None, state). UNREADABLE IS NOT ABSENT and neither is fine, so
    they are two states rather than one falsy answer."""
    mp = pathlib.Path(outdir) / "manifest.json"
    if not mp.exists():
        return None, "absent"
    try:
        return json.loads(mp.read_text(encoding="utf-8")), "read"
    except Exception as e:                                    # noqa: BLE001
        return None, f"unreadable:{type(e).__name__}"


def _nospace(v):
    """Every reader of a key=value line splits on whitespace and truncates
    silently, so a value never carries a space."""
    return str(v).replace(" ", "-") or "none"


def imagegen_verdict(outdir, sha="local", steps="", out=None, repo=None):
    """Write the evidence file and return 0 only if this run banked pictures.

    LINE 1 NAMES THE COMMIT. Whole-run numbers are on the done line and
    per-picture numbers on the picture lines, because a grep across two lines
    merges two moments silently.

    A RUN THAT GENERATED NOTHING SAYS `NO RUN`, and so does a run whose
    manifest was written on a different commit: "the job carried the commit"
    and "the job made a picture" are different facts, and the second one is the
    only one worth a night.
    """
    outdir = pathlib.Path(outdir)
    out = pathlib.Path(out) if out else outdir / VERDICT_NAME
    man, state = _read_manifest(outdir)
    on_disk = sorted(q for q in outdir.glob("*.png")) if outdir.exists() else []
    manifest_run = ((man or {}).get("run") or {}).get("sha", "none")
    fresh = (manifest_run == sha and sha != "none")

    L = [f"# LEDGER imagegen - {sha} @{int(time.time())}",
         "# Line 1 names the commit this was measured on. No value has a space.",
         "# Every blankness number here was re-measured from the PNG itself, "
         "not copied from the manifest.",
         ""]
    L.append(f"steps {_nospace(steps) or 'none-reported'}")
    L.append(f"manifestRun={_nospace(manifest_run)} thisRun={_nospace(sha)} "
             f"manifestIsThisRun={'yes' if fresh else 'no'} "
             f"manifestState={_nospace(state)} "
             f"batchStatus={_nospace((man or {}).get('status', 'NONE'))} "
             f"outDir={_nospace(outdir.name)}")
    L.append(f"bound blank-when-spread<={BLANK_MAX_SPREAD}/255-AND-"
             f"stdev<={BLANK_MAX_STDEV},-or-alpha-0-everywhere-sampled")

    images = (man or {}).get("images", []) or []
    bc = (man or {}).get("blank_check", {}) or {}
    wrote = sum(1 for r in images if r.get("made_on_run") == sha)
    failed = sum(1 for r in images if r.get("status") == "FAILED")
    skipped = sum(1 for r in images if r.get("status") == "SKIPPED")
    rows, remeasured, remeasured_blank, remeasured_unreadable = [], 0, 0, 0
    missing, total_bytes = [], 0
    for r in images:
        mine = (r.get("made_on_run") == sha)
        fname = r.get("file")
        measured = "not-a-file"
        if fname and r.get("status") in ("OK", "SKIPPED"):
            q = outdir / fname
            if not q.exists():
                missing.append(fname)
                measured = "MISSING-FROM-DISK"
            else:
                st = png_stats(q)
                v, _why = blank_verdict(st)
                remeasured += 1
                total_bytes += q.stat().st_size
                if v == "blank":
                    remeasured_blank += 1
                elif v == "unknown":
                    remeasured_unreadable += 1
                measured = (f"{v}/spread{st.get('spread')}/stdev{st.get('stdev')}"
                            f"/levels{st.get('distinct')}"
                            f"/{st.get('sampled')}of{st.get('pixels')}px"
                            f"/{q.stat().st_size}B")
        elif r.get("status") == "FAILED":
            measured = "no-picture/" + _nospace((r.get("why") or "no-reason")[:60])
        if mine or r.get("status") == "FAILED":
            rows.append(f"image {_nospace(r.get('id', 'NONE'))} "
                        f"status={_nospace(r.get('status', 'NONE'))} "
                        f"madeThisRun={'yes' if mine else 'no'} "
                        f"file={_nospace(fname or 'none')} "
                        f"size={r.get('width', '?')}x{r.get('height', '?')} "
                        f"seconds={r.get('seconds', '?')} "
                        f"remeasured={measured}")
    shown = rows[:VERDICT_SAMPLE_CAP]
    L.extend(shown)
    if len(rows) > len(shown):
        L.append(f"(+{len(rows) - len(shown)}-more-not-shown)")
    if not rows:
        L.append("# no picture line above: this run neither generated nor "
                 "failed a single item")

    blanks_on_disk = [q.name for q in on_disk if q.name.endswith(".BLANK.png")]
    L.append(f"disk pngsInOutDir={len(on_disk)} "
             f"namedByThisManifest={sum(1 for r in images if r.get('file'))} "
             f"blankFilesOnDisk={len(blanks_on_disk)} "
             f"missingFromDisk={len(missing)}")
    if blanks_on_disk:
        L.append("BLANKFILES " + ",".join(sorted(blanks_on_disk)[:20])
                 + (f"-(+{len(blanks_on_disk) - 20}-more-not-shown)"
                    if len(blanks_on_disk) > 20 else "")
                 + " # kept on the runner as evidence and NEVER staged")
    if missing:
        L.append("MISSING " + ",".join(sorted(missing)[:20])
                 + (f"-(+{len(missing) - 20}-more-not-shown)"
                    if len(missing) > 20 else ""))

    # THE VERDICT WORD, AND ITS ORDER IS A DECISION. A run that generated
    # nothing BECAUSE everything came out blank is a blank run, not an idle
    # one, so BLANKS is tested before NO-RUN. Otherwise the loudest finding of
    # the night would hide behind the quietest word for it.
    if man is None:
        word, why = "NO-RUN", f"manifest-{state}-under-{outdir.name}"
    elif not fresh:
        word, why = "NO-RUN", f"manifest-written-by-run-{_nospace(manifest_run)}-not-{_nospace(sha)}"
    elif (bc.get("blank") or bc.get("undecodable")
          or remeasured_blank or remeasured_unreadable):
        word, why = "BLANKS", "leejet-stable-diffusion.cpp#1031-shape"
    elif wrote == 0:
        word = "NO-RUN"
        why = ("nothing-generated-" + ("all-selected-items-were-already-on-disk"
                                       if skipped else "nothing-was-attempted"))
    else:
        word, why = "BANKED", "none"
    if word == "NO-RUN":
        L.append(f"NO RUN - this commit ({sha}) generated no picture: "
                 f"{why.replace('-', ' ')}. Nothing older is being read as this "
                 "run's answer.")
    sel = (man or {}).get("selection", {}) or {}
    L.append(f"done imagegenVerdict={word} why={why} "
             f"wroteThisRun={wrote} failed={failed} skipped={skipped} "
             f"selected={(man or {}).get('items_selected', 0)} "
             f"inSpec={(man or {}).get('items_in_spec', 0)} "
             f"limit={_nospace(sel.get('limit'))} "
             f"blankThisRun={bc.get('blank', 0)} "
             f"undecodableThisRun={bc.get('undecodable', 0)} "
             f"checkedThisRun={bc.get('checked', 0)} "
             f"remade={bc.get('remade', 0)} rechecked={bc.get('rechecked', 0)} "
             f"remeasured={remeasured} remeasuredBlank={remeasured_blank} "
             f"remeasuredUnreadable={remeasured_unreadable} "
             f"missingFromDisk={len(missing)} bytes={total_bytes}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0 if word == "BANKED" else 1


def staged_file_list(outdir, sha="local", repo=None, out=None):
    """The paths the workflow may `git add`, BY NAME.

    Derived from the manifest, and only from a manifest this run wrote, so a
    failed run can never commit its stale checkout's files as its own evidence.
    A stale or missing manifest stages ONLY the verdict, which is the file that
    says the run measured nothing.

    A `.BLANK.png` IS NEVER STAGED. It is kept on the runner because it is the
    evidence, and it is not committed because a uniform image is fully
    described by the four numbers already in the verdict, and because a
    directory of blank PNGs is exactly what a later reader mistakes for art.
    """
    outdir = pathlib.Path(outdir)
    out = pathlib.Path(out) if out else outdir / VERDICT_NAME
    root = pathlib.Path(repo).resolve() if repo else None

    def rel(q):
        q = pathlib.Path(q).resolve()
        if root is None:
            return None
        try:
            return q.relative_to(root).as_posix()
        except ValueError:
            return None

    lines, outside = [], 0
    man, _state = _read_manifest(outdir)
    fresh = ((man or {}).get("run", {}).get("sha") == sha and sha != "none")
    wanted = [out]
    if fresh:
        for name in ("manifest.json", "made.json", "PROGRESS.txt", "ATTRIBUTION.json"):
            wanted.append(outdir / name)
        for r in man.get("images", []):
            f = r.get("file")
            if (r.get("status") in ("OK", "SKIPPED") and f
                    and not f.endswith(".BLANK.png") and (outdir / f).exists()):
                wanted.append(outdir / f)
    for q in wanted:
        if not pathlib.Path(q).exists():
            continue
        r = rel(q)
        if r is None:
            outside += 1
            continue
        lines.append(r)
    return list(dict.fromkeys(lines)), outside


def staged_files(outdir, sha="local", repo=None, out=None):
    """Print what staged_file_list decided, one path per line. THE DECIDING AND
    THE PRINTING ARE SEPARATE so the deciding can be tested: a list function
    returns something a check can count, and a printer returns 0 whatever it
    printed."""
    lines, outside = staged_file_list(outdir, sha, repo, out)
    for line in lines:
        print(line)
    if outside:
        print(f"{outside} path(s) are outside the repository and cannot be "
              "staged; --repo names the repository root", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# SELFTEST - accepting case first.
# ---------------------------------------------------------------------------
def _write_png(path, w, h, pixel, ctype=2):
    """Minimal PNG writer, used ONLY by the selftest so both the good case and
    the blank case can be synthesised here rather than waiting for a GPU."""
    ch = {0: 1, 2: 3, 6: 4}[ctype]
    rows = bytearray()
    for y in range(h):
        rows.append(0)                                   # filter: None
        for x in range(w):
            px = pixel(x, y)
            rows += bytes(px if len(px) == ch else (px * ch)[:ch])

    def chunk(t, d):
        return (len(d).to_bytes(4, "big") + t + d
                + (zlib.crc32(t + d) & 0xffffffff).to_bytes(4, "big"))

    pathlib.Path(path).write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", w.to_bytes(4, "big") + h.to_bytes(4, "big")
                + bytes([8, ctype, 0, 0, 0]))
        + chunk(b"IDAT", zlib.compress(bytes(rows), 6))
        + chunk(b"IEND", b""))


def png_series(root):
    """Print the spread/stdev series over every PNG under `root`, newest rule
    first: the SERIES above the summary, because a bound set from a summary is
    a bound set from nothing. This is what BLANK_MAX_SPREAD was read off."""
    files = [f for f in sorted(pathlib.Path(root).rglob("*.png")) if ".git" not in f.parts]
    print(f"blankness series over {len(files)} PNGs under {root}")
    rows, bad = [], []
    for f in files:
        st = png_stats(f)
        (rows if st.get("decoded") else bad).append((st, f))
    rows.sort(key=lambda r: r[0]["spread"])
    for st, f in rows:
        v, _ = blank_verdict(st)
        print(f"  spread {st['spread']:>3}/255  stdev {st['stdev']:>8.3f}  "
              f"distinct {st['distinct']:>4}  {v:<7} {f}")
    for st, f in bad:
        print(f"  UNDECODABLE  {st['why']}  {f}")
    print(f"  {len(rows)} decoded, {len(bad)} undecodable, "
          f"{sum(1 for st, _ in rows if blank_verdict(st)[0] == 'blank')} called blank")
    if rows:
        sp = [st["spread"] for st, _ in rows]
        print(f"  spread: min {min(sp)}  median {sorted(sp)[len(sp)//2]}  max {max(sp)}")
        print(f"  bound is spread <= {BLANK_MAX_SPREAD} AND stdev <= {BLANK_MAX_STDEV}")
    return 0


def selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  pass  {name}")
        else:
            fail += 1
            print(f"  FAIL  {name}  {detail}")

    print("imagegen selftest")
    print("-" * 60)
    # 1. THE ACCEPTING CASE FIRST. A planner nothing survives is the expensive
    #    failure, so the first assertion is that a normal machine plans a run.
    good = {"hostname": "PC", "ram_bytes": 32 * 1024**3, "free_disk_bytes": 400 * 1024**3,
            "gpus": [{"name": "AMD Radeon RX 6700 XT", "vram_bytes_registry": 12 * 1024**3}]}
    p = plan(good)
    check("accepting case: a 12GB AMD card plans a real run",
          p["backend"] == "vulkan" and p["item_limit"] is None and p["quant"] == "Q8_0", p)

    cases = [
        ("NVIDIA 24GB", {"gpus": [{"name": "NVIDIA GeForce RTX 4090",
                                   "vram_bytes_registry": 24 * 1024**3}]},
         lambda r: r["backend"] == "cuda12" and r["quant"] == "Q8_0"),
        ("AMD 8GB", {"gpus": [{"name": "AMD Radeon RX 6600",
                               "vram_bytes_registry": 8 * 1024**3}]},
         lambda r: r["backend"] == "vulkan" and r["quant"] == "Q4_K"
                   and "--vae-tiling" not in r["flags"]),
        ("AMD 4GB", {"gpus": [{"name": "AMD Radeon RX 570",
                               "vram_bytes_registry": 4 * 1024**3}]},
         lambda r: r["quant"] == "Q3_K" and "--clip-on-cpu" in r["flags"]),
        ("Intel iGPU, no VRAM figure", {"gpus": [{"name": "Intel(R) UHD Graphics 630"}]},
         lambda r: r["backend"] == "vulkan" and not r["vram_known"] and r["quant"] == "Q4_K"),
        ("AdapterRAM uint32 ceiling is NOT a 4GB card",
         {"gpus": [{"name": "AMD Radeon RX 7900 XTX", "vram_bytes": 4294967295}]},
         lambda r: not r["vram_known"] and r["quant"] == "Q4_K"),
        ("probe found nothing", {"gpus": []},
         lambda r: r["backend"] == "cpu" and r["item_limit"] == 2 and r["size_scale"] == 0.5),
    ]
    for name, m, pred in cases:
        r = plan(m)
        check(f"plan: {name}", pred(r), f"got backend={r['backend']} quant={r['quant']} "
                                        f"flags={r['flags']} limit={r['item_limit']}")
        check(f"plan: {name} explains itself", len(r["reasons"]) >= 2)

    spec = json.loads((pathlib.Path(__file__).parent / "prompts.json").read_text())
    rules = spec["content_rules"]["rules_clause"]
    # 2. Every shipped prompt carries the rules and names no real mark.
    hits = 0
    for it in spec["items"]:
        pr = build_prompt(it, rules, spec["style"])
        hits += len(check_forbidden(pr, spec["content_rules"]["forbidden_tokens"]))
        if "no trade marks" not in pr or "no real person" not in pr:
            check(f"prompt {it['id']} carries the rules", False, pr[:120])
            break
    else:
        check(f"all {len(spec['items'])} prompts carry the content rules", True)
    check(f"no prompt names a real mark "
          f"({len(spec['content_rules']['forbidden_tokens'])} tokens scanned "
          f"x {len(spec['items'])} prompts)", hits == 0, f"{hits} hits")
    # 3. The rejecting case: the rules cannot be quietly dropped.
    try:
        build_prompt(spec["items"][0], "make it pretty", spec["style"])
        check("rejecting case: a prompt without the rules clause is refused", False)
    except ValueError:
        check("rejecting case: a prompt without the rules clause is refused", True)
    # 4. And the forbidden scan can actually go red.
    check("rejecting case: the forbidden-mark scan fires on a real brand",
          check_forbidden("a pub sign reading GUINNESS",
                          spec["content_rules"]["forbidden_tokens"]) != [])
    # 5. Report formatting survives a probe that failed - the case most likely
    #    to be hit first and the one that must not throw.
    txt = format_report({"probe": "FAILED: powershell not found", "gpus": []}, plan({}))
    check("report renders when the probe failed", "NONE FOUND" in txt and "cpu" in txt)

    # 5b. THE MULTI-ADAPTER MACHINE - the shape that cost Jafar ten of twelve
    #     images. Version 1 of the probe was only ever tested against ONE
    #     adapter, and every real desktop has several video "controllers": the
    #     card, a Microsoft Basic Display Adapter, sometimes a remote-desktop
    #     or virtual one. Accepting case first: the real card must still be the
    #     one the plan is built on.
    basic = {"name": "Microsoft Basic Display Adapter", "vram_bytes": 0,
             "vram_bytes_registry": 0, "source": "Win32_VideoController (CIM)"}
    rdp = {"name": "Microsoft Remote Display Adapter", "vram_bytes": 0,
           "vram_bytes_registry": 0, "source": "Win32_VideoController (CIM)"}
    card = {"name": "AMD Radeon RX 6700 XT", "vram_bytes": 4294967295,
            "vram_bytes_registry": 12 * 1024**3, "vram_match": "exact name match",
            "source": "Win32_VideoController (CIM)"}
    multi = plan({"gpus": [card, basic, rdp]})
    check("accepting case: three adapters, the real card is the one planned on",
          multi["vendor"] == "amd" and multi["backend"] == "vulkan"
          and multi["vram_known"] and abs(multi["vram_gb"] - 12.0) < 0.01
          and multi["item_limit"] is None, multi)
    # ORDER MUST NOT MATTER. Win32_VideoController returns adapters in whatever
    # order the enumerator gives, and on a machine that has been remoted into,
    # the fake one comes first.
    multi2 = plan({"gpus": [rdp, basic, card]})
    check("three adapters, real card LAST, same plan",
          multi2["vendor"] == "amd" and multi2["vram_known"]
          and abs(multi2["vram_gb"] - 12.0) < 0.01, multi2)
    # One row failing must not lose the others: the probe now appends whatever
    # it could read, and a hole arrives as a null rather than as an empty list.
    holed = plan({"gpus": [basic, None, card]})
    check("one unreadable adapter row does not lose the working ones",
          holed["vendor"] == "amd" and abs(holed["vram_gb"] - 12.0) < 0.01, holed)
    # PINNED, because it is the one multi-adapter case that reads worse than
    # single: if the only 64-bit figure is SMALLER than another adapter's
    # uint32 ceiling, VRAM goes UNKNOWN rather than being believed. That is the
    # conservative direction (smaller quant), and it is asserted so a later
    # change to plan() cannot flip it silently.
    small = {"name": "AMD Radeon RX 570", "vram_bytes_registry": 3 * 1024**3}
    ceiling_only = {"name": "Microsoft Basic Display Adapter", "vram_bytes": 4294967295}
    mixed = plan({"gpus": [small, ceiling_only]})
    check("a ceiling reading beside a smaller real one is treated as UNKNOWN, "
          "not as 4GB", not mixed["vram_known"] and mixed["quant"] == "Q4_K", mixed)
    # The report has to SHOW every adapter, or a wrong plan cannot be diagnosed
    # from the file Jafar sends back.
    txt3 = format_report({"probe": "ok", "probe_version": 2,
                          "gpu_source": "Win32_VideoController (CIM)",
                          "gpus": [card, basic, rdp]}, multi)
    check("report lists every adapter of a three-adapter machine",
          "[0]" in txt3 and "[1]" in txt3 and "[2]" in txt3
          and "Microsoft Basic Display Adapter" in txt3
          and "3 found via Win32_VideoController (CIM)" in txt3, txt3[:400])
    # 5c. A ZERO NEEDS A DENOMINATOR. "NONE FOUND" was printed on a machine with
    #     a discrete card; the fix is that the report says how hard the probe
    #     looked. Both ways round.
    txt4 = format_report({"probe": "ok", "probe_version": 2, "gpus": [],
                          "gpu_source": "none answered",
                          "gpu_sources_tried":
                              "Win32_VideoController (CIM) -> 0 adapter(s) from 3 row(s) "
                              "seen; 3 row(s) unreadable | dxdiag /x -> 0 adapter(s) "
                              "from 0 row(s) seen"},
                         plan({"gpus": []}))
    check("NONE FOUND arrives with the source log that is its denominator",
          "NONE FOUND" in txt4 and "sources tried" in txt4
          and "3 row(s) unreadable" in txt4 and "dxdiag" in txt4, txt4[:400])
    txt5 = format_report({"probe": "partial: video controllers failed", "gpus": []},
                         plan({"gpus": []}))
    check("a report with NO source log says the zero proves nothing "
          "(this is the version-1 shape Jafar sent back)",
          "NO SOURCE LOG" in txt5 and "proves nothing" in txt5
          and "PRE-DATES THE MULTI-ADAPTER FIX" in txt5, txt5[:400])
    # 5d. "we could not tell" and "none registered" need DIFFERENT actions from
    #     Jafar, so they must not render as the same line.
    vk_none = format_report({"gpus": [], "vulkan_drivers": 0,
                             "vulkan_status": "NOT INSTALLED - no Khronos registry key "
                                              "and no vulkan-1.dll",
                             "vulkan_loader": "absent"}, plan({}))
    vk_blind = format_report({"gpus": [], "vulkan_drivers": "unknown",
                              "vulkan_status": "could not tell - the vulkan probe did "
                                               "not complete",
                              "vulkan_loader": "unknown"}, plan({}))
    check("vulkan NOT INSTALLED and vulkan COULD NOT TELL render differently",
          "NOT INSTALLED" in vk_none and "could not tell" in vk_blind
          and "NOT INSTALLED" not in vk_blind, (vk_none[-300:], vk_blind[-300:]))
    # 6. Manifest round-trips.
    m = {"status": "DONE", "images": [{"id": "x", "sha256": "y"}]}
    check("manifest round-trips as json", json.loads(json.dumps(m))["status"] == "DONE")

    # 7. THE RUN LOOP, with the generator faked. This is the half that cannot
    #    be exercised without a GPU, so `subprocess.run` is replaced rather
    #    than skipped - the accounting, the caps and the failure record are
    #    ours and testable, and one of them WAS wrong: a failed image used to
    #    increment `items_failed` and never write its reason into the
    #    manifest, so the file we read to diagnose a bad run held the number
    #    and not the cause. These three checks exist so that cannot come back.
    import tempfile
    import types

    class _Fake:
        """paint='varied' writes a real, varied PNG; 'blank' writes a uniform
        one - which is #1031's failure exactly: EXIT CODE 0 AND A BLANK FILE;
        'stub' writes bytes that are not a decodable PNG. Small fixed size, not
        the requested one: this stands in for the generator, and 64x48 keeps a
        twelve-image selftest under a second."""

        def __init__(self, rc, paint="varied"):
            self.rc, self.paint = rc, paint

        def __call__(self, cmd, **kw):
            if not self.rc:
                out = pathlib.Path(cmd[cmd.index("--output") + 1])
                if self.paint == "blank":
                    _write_png(out, 64, 48, lambda x, y: (0, 0, 0))
                elif self.paint == "stub":
                    out.write_bytes(b"\x89PNG\r\n\x1a\n stub")
                else:
                    _write_png(out, 64, 48,
                               lambda x, y: ((x * 4) % 256, (y * 5) % 256, (x ^ y) % 256))
            return types.SimpleNamespace(returncode=self.rc, stdout="",
                                         stderr="ggml_vulkan: device not found")

    real = subprocess.run
    gpu = plan({"gpus": [{"name": "AMD Radeon RX 6800",
                          "vram_bytes_registry": 16 * 1024**3}]})
    try:
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            subprocess.run = _Fake(0)
            m = run_batch(pathlib.Path("stub"), td, gpu, spec, td / "a", 60, lambda s="": None)
            check("run loop: a clean batch writes every item and says DONE",
                  m["status"] == "DONE" and m["items_written"] == len(spec["items"])
                  and not m["not_attempted"], m["status"])
            check("run loop: every written PNG was CHECKED for blankness, and the "
                  f"count says how many ({m['blank_check']['checked']} of "
                  f"{len(spec['items'])})",
                  m["blank_check"]["checked"] == len(spec["items"])
                  and m["blank_check"]["blank"] == 0
                  and m["blank_check"]["undecodable"] == 0
                  and all(r["blank_check"]["verdict"] == "varied" for r in m["images"]),
                  m["blank_check"])
            subprocess.run = _Fake(1)
            f = run_batch(pathlib.Path("stub"), td, gpu, spec, td / "b", 60, lambda s="": None)
            check("run loop: a failing generator stops after 2 and KEEPS THE REASON",
                  f["items_written"] == 0 and f["items_failed"] == 2
                  and len(f["images"]) == 2 and "log_tail" in f["images"][0]
                  and len(f["not_attempted"]) == len(spec["items"]) - 2,
                  f"{f['items_failed']} failed, {len(f['images'])} records, "
                  f"{len(f['not_attempted'])} unattempted")
            subprocess.run = _Fake(0)
            c = run_batch(pathlib.Path("stub"), td, plan({"gpus": []}), spec,
                          td / "c", 60, lambda s="": None)
            check("run loop: the CPU cap is announced, not silent",
                  any("CAP" in x for x in c["caps"]) and c["items_written"] == 2
                  and len(c["not_attempted"]) == len(spec["items"]) - 2, c["caps"])
            # FIX 1, THE REJECTING CASE, IN THE PLACE IT MATTERS. The generator
            # exits ZERO and writes a blank PNG - #1031 exactly.
            subprocess.run = _Fake(0, "blank")
            b = run_batch(pathlib.Path("stub"), td, gpu, spec, td / "d", 60,
                          lambda s="": None)
            blanks = [r for r in b["images"] if r.get("status") == "FAILED"]
            check("run loop REJECTING CASE: exit 0 + a blank PNG is FAILED, is NOT "
                  "counted as produced, and stops the batch",
                  b["items_written"] == 0 and b["items_failed"] == 2
                  and b["blank_check"]["blank"] == 2
                  and b["blank_check"]["checked"] == 2
                  and b["status"] == "INCOMPLETE"
                  and len(b["not_attempted"]) == len(spec["items"]) - 2,
                  f"written={b['items_written']} failed={b['items_failed']} "
                  f"blank={b['blank_check']}")
            check("run loop: the blank image keeps its REASON, names #1031, and is "
                  "renamed off the delivered name",
                  bool(blanks) and "#1031" in (blanks[0].get("why") or "")
                  and blanks[0]["blank_check"]["verdict"] == "blank"
                  and blanks[0].get("file", "").endswith(".BLANK.png")
                  and (td / "d" / blanks[0]["file"]).exists()
                  and not (td / "d" / (blanks[0]["id"] + ".png")).exists(),
                  blanks[0] if blanks else "no failed record")
            # A PNG THAT CANNOT BE DECODED IS ITS OWN ANSWER, not a pass and not
            # a blank - and it is counted, so "0 blank" can never be a check
            # that never ran.
            subprocess.run = _Fake(0, "stub")
            u = run_batch(pathlib.Path("stub"), td, gpu, spec, td / "e", 60,
                          lambda s="": None)
            check("run loop: an undecodable PNG counts as UNDECODABLE, not as "
                  "blank and not silently as good",
                  u["blank_check"]["undecodable"] == len(spec["items"])
                  and u["blank_check"]["blank"] == 0
                  and u["blank_check"]["checked"] == len(spec["items"])
                  and all(r["blank_check"]["verdict"] == "unknown" for r in u["images"]),
                  u["blank_check"])
    finally:
        subprocess.run = real

    # 8. THE BLANK CHECK IN ISOLATION, BOTH WAYS, ACCEPTING CASE FIRST.
    #    #1031 writes a file and exits zero, so the only witness is the PNG.
    #    Both cases are synthesised here - no GPU, no network, no fixture on
    #    disk that could rot.
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        good = td / "varied.png"
        _write_png(good, 160, 120,
                   lambda x, y: ((x * 7 + y * 3) % 256, (y * 5) % 256, (x ^ y) % 256))
        st = png_stats(good)
        v, why = blank_verdict(st)
        check("blank check ACCEPTING CASE: a varied image is 'varied'",
              v == "varied" and st["decoded"], f"{v}: {why}")
        check("blank check: the numbers carry their denominator "
              f"({st.get('sampled')} sampled of {st.get('pixels')} pixels)",
              st.get("sampled") and st.get("pixels")
              and st["sampled"] <= st["pixels"], st)
        # A faint gradient is a real image and must not be swallowed by the bound.
        gentle = td / "gentle.png"
        _write_png(gentle, 160, 120, lambda x, y: ((100 + x // 20,) * 3))
        gv, gwhy = blank_verdict(png_stats(gentle))
        check("blank check ACCEPTING CASE: a faint 8-level gradient is still "
              "'varied' - the bound sits at the degenerate end, not in the middle",
              gv == "varied", f"{gv}: {gwhy}")
        # ...and now the rejecting cases.
        for name, painter, ct in (("black", lambda x, y: (0, 0, 0), 2),
                                  ("mid-grey", lambda x, y: (127, 127, 127), 2),
                                  ("white", lambda x, y: (255, 255, 255), 2)):
            f = td / f"blank_{name}.png"
            _write_png(f, 160, 120, painter, ctype=ct)
            bv, bwhy = blank_verdict(png_stats(f))
            check(f"blank check REJECTING CASE: a uniform {name} image is 'blank'",
                  bv == "blank", f"{bv}: {bwhy}")
        clear = td / "transparent.png"
        _write_png(clear, 160, 120,
                   lambda x, y: ((x * 3) % 256, (y * 3) % 256, 200, 0), ctype=6)
        tv, twhy = blank_verdict(png_stats(clear))
        check("blank check REJECTING CASE: fully transparent is blank even when "
              "the colour channels vary",
              tv == "blank", f"{tv}: {twhy}")
        for name, blob in (("empty file", b""),
                           ("not a PNG", b"GIF89a and then some"),
                           ("header only", b"\x89PNG\r\n\x1a\n stub")):
            f = td / f"bad_{name.replace(' ', '_')}"
            f.write_bytes(blob)
            uv, uwhy = blank_verdict(png_stats(f))
            check(f"blank check THIRD ANSWER: {name} is 'unknown' - not blank, "
                  "not varied", uv == "unknown", f"{uv}: {uwhy}")
        # And the decoder is not a stub that says 'varied' to everything: it
        # reads back what was written, through a non-trivial filter path.
        st2 = png_stats(good)
        check("blank check: the decoder reads real geometry back "
              f"(160x120, {st2.get('distinct')} distinct levels)",
              st2.get("width") == 160 and st2.get("height") == 120
              and st2.get("distinct", 0) > 20, st2)

    # 9. FIX 2 - #1673: --vae-conv-direct on Vulkan is a function of the SIZE.
    unknown_vram = plan({"gpus": [{"name": "AMD Radeon Graphics"}]})
    check("vae flags ACCEPTING CASE: at 512x512 on Vulkan the planned flags are "
          "used unchanged - the workaround is not applied where the issue says "
          "the output is clean",
          image_flags(unknown_vram, 512, 512)[0] == unknown_vram["flags"]
          and image_flags(unknown_vram, 512, 512)[1] is None,
          image_flags(unknown_vram, 512, 512))
    f1024, note = image_flags(unknown_vram, 1024, 1024)
    check("vae flags REJECTING CASE: at 1024x1024 on Vulkan --vae-conv-direct is "
          "dropped and --vae-on-cpu takes its place, with #1673 named",
          "--vae-conv-direct" not in f1024 and "--vae-on-cpu" in f1024
          and note and "#1673" in note, f"{f1024} / {note}")
    check("vae flags: the AMD machine with UNKNOWN vram - which is Jafar's case "
          "by construction - is the one that would have hit it",
          "--vae-conv-direct" in unknown_vram["flags"]
          and not unknown_vram["vram_known"] and unknown_vram["backend"] == "vulkan",
          unknown_vram["flags"])
    nv = plan({"gpus": [{"name": "NVIDIA GeForce RTX 3060", "vram_bytes_registry": 6 * 1024**3}]})
    check("vae flags: the CUDA path keeps --vae-conv-direct at 1024x1024 - #1673 "
          "is a Vulkan report and the workaround is not spread to backends it "
          "was never about",
          "--vae-conv-direct" in image_flags(nv, 1024, 1024)[0], image_flags(nv, 1024, 1024))
    sizes = {(round16(i["width"]), round16(i["height"])) for i in spec["items"]}
    # THIS ASSERTION WAS "all ... are larger than 512x512" AND THE PROBE PAIR
    # MADE IT FALSE. Both probes are EXACTLY 512x512, so the Vulkan workaround
    # does not fire for them while it fires for all twelve content items. The
    # assertion is kept as a COUNT rather than an "all", because the number is
    # the thing worth watching: a size added below the threshold changes which
    # decoder path an image takes, and an "all" would simply go red without
    # saying what changed.
    #
    # IT DOES NOT INVALIDATE THE PROBE EXPERIMENT: both probes are the same
    # size, so they differ only in the setting under test. It DOES mean a
    # probe result may not transfer to the 1024x1024 walls it stands for —
    # said out loud, because that is a comparison somebody will make.
    takes = [(w, h) for w, h in sizes if image_flags(unknown_vram, w, h)[1]]
    check(f"vae flags: {len(takes)} of {len(sizes)} distinct size(s) take the "
          "Vulkan workaround; the 512x512 probe pair does NOT, and a probe "
          "result therefore may not transfer to the 1024x1024 wall it stands "
          "for - stated because a flag that never fires is worse than one "
          "that is gone",
          len(takes) == len(sizes) - 1 and (512, 512) not in takes, sorted(sizes))

    # 10. FIX 3 - the model GGUF has a candidate list, and a gate still stops.
    for q in QUANTS:
        urls = model_urls(q)
        if len(urls) < 2 or QUANTS[q][0] not in urls[0]:
            check(f"model candidates: {q} has a list, best first", False, urls)
            break
    else:
        check(f"model candidates: all {len(QUANTS)} quants get "
              f"{len(model_urls('Q4_K'))} candidates, the first being leejet's "
              "exact filename", True)
    u = model_urls("Q4_K")
    check("model candidates: the Q4_K / Q4_K_M spelling is tried both ways",
          any(x.endswith("Q4_K.gguf") for x in u)
          and any(x.endswith("Q4_K_M.gguf") for x in u), u)
    check("model candidates: no duplicates, every one a plain HF resolve URL",
          len(set(u)) == len(u) and all(x.startswith(HF + "/") and "/resolve/main/" in x
                                        for x in u), u)

    class _Resp:
        def __init__(self, data):
            self.data, self.i, self.status = data, 0, 200
            self.headers = {"Content-Length": str(len(data))}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, n=-1):
            chunk = self.data[self.i:self.i + (n if n and n > 0 else len(self.data))]
            self.i += len(chunk)
            return chunk

    real_open, seen = urllib.request.urlopen, []

    def fake_open(codes):
        def _u(req, timeout=None):
            seen.append(req.full_url)
            if codes.get(req.full_url):
                raise urllib.error.HTTPError(req.full_url, codes[req.full_url],
                                             "no", {}, None)
            return _Resp(b"z" * 4096)
        return _u

    import io
    import contextlib
    try:
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            a, b = "https://x/one.gguf", "https://x/two.gguf"
            # ACCEPTING CASE FIRST: a 404 on the first candidate is a rename,
            # not a gate, and the list is what makes it survivable.
            seen.clear()
            urllib.request.urlopen = fake_open({a: 404})
            with contextlib.redirect_stdout(io.StringIO()) as cap:
                path, used = fetch_one([a, b], td / "m1.gguf", 4096, "model")
            check("fetch ACCEPTING CASE: a 404 on the first candidate falls "
                  "through to the second, which is the whole point of the list",
                  used == b and path.exists() and seen == [a, b], f"{used} {seen}")
            check("fetch: it prints what every candidate answered",
                  "one.gguf" in cap.getvalue() and "two.gguf" in cap.getvalue())
            # REJECTING CASE: a gate STOPS. It must not shop down the list for
            # an unlocked door - we hold no accounts.
            for code in (401, 403):
                seen.clear()
                urllib.request.urlopen = fake_open({a: code})
                with contextlib.redirect_stdout(io.StringIO()) as cap:
                    try:
                        fetch_one([a, b], td / f"m{code}.gguf", 4096, "model")
                        stopped, msg = False, "no exception"
                    except RuntimeError as e:
                        stopped, msg = True, str(e)
                check(f"fetch REJECTING CASE: HTTP {code} STOPS the run, says "
                      "GATED, and does NOT try the remaining candidates",
                      stopped and seen == [a] and "GATED" in msg
                      and "NOT tried" in msg
                      and "needs a Hugging Face login" in cap.getvalue(),
                      f"tried={seen} msg={msg[:160]}")
    finally:
        urllib.request.urlopen = real_open

    # 11. THE GATE - the decision that used to be a command Jafar had to paste.
    #     ACCEPTING CASE FIRST, and it is the important one: a gate that stops
    #     a machine WITH a graphics card is worse than no gate at all, because
    #     the failure mode is "the one click does nothing, for ever".
    one = {"probe_file_read": True, "gpu_source": "Win32_VideoController (CIM)",
           "gpus": [{"name": "AMD Radeon RX 6700 XT",
                     "vram_bytes_registry": 12 * 1024**3}]}
    g_one = gpu_gate(one)
    check("gate ACCEPTING CASE: one display adapter and the run PROCEEDS",
          g_one["stop"] is False and g_one["kind"] == "adapter"
          and g_one["found"] == 1, g_one)
    g_multi = gpu_gate({"probe_file_read": True, "gpus": [card, basic, rdp]})
    check("gate ACCEPTING CASE: the three-adapter machine proceeds too - the "
          "shape that reported NO GPU on Jafar's PC must not now be stopped by "
          "the fix for it",
          g_multi["stop"] is False and g_multi["found"] == 3, g_multi)
    # THE REAL MACHINE, NOT A HYPOTHESIS. Jafar ran the fixed probe on 25 Aug
    # 2026 and it printed `adapters: 2 via Win32_VideoController (CIM)` - two
    # adapters, from the FIRST source, no fallback needed. That is the exact
    # multi-adapter shape that broke version 1 twice (duplicate-key Add on the
    # second row, and a list accumulated in a child scope), and it is now the
    # gate's happy path as a MEASUREMENT rather than as a guess. Pinned here so
    # a later change to the gate has to walk past his actual machine to break.
    g_real = gpu_gate({"probe_file_read": True, "probe": "ok", "probe_version": 2,
                       "gpu_source": "Win32_VideoController (CIM)",
                       "gpus": [card, basic]})
    check("gate ACCEPTING CASE, MEASURED: Jafar's real reading - 2 adapters via "
          "Win32_VideoController (CIM), 25 Aug - PROCEEDS, and the plan built "
          "from it is a GPU plan with no batch cap",
          g_real["stop"] is False and g_real["found"] == 2
          and plan({"gpus": [card, basic]})["backend"] == "vulkan"
          and plan({"gpus": [card, basic]})["item_limit"] is None, g_real)
    # ...and the rejecting cases, which are what he lost seven minutes to.
    none_found = {"probe_file_read": True, "gpu_source": "none answered",
                  "gpus": [], "probe": "ok",
                  "gpu_sources_tried": "Win32_VideoController (CIM) -> 0 adapter(s) "
                                       "from 3 row(s) seen | dxdiag /x -> 0 "
                                       "adapter(s) from 0 row(s) seen"}
    g_none = gpu_gate(none_found)
    check("gate REJECTING CASE: NO display adapter STOPS the run",
          g_none["stop"] is True and g_none["kind"] == "no-adapter"
          and g_none["found"] == 0, g_none)
    g_noprobe = gpu_gate({"probe_file_read": False,
                          "probe": "machine.json missing at C:\\x\\machine.json"})
    check("gate REJECTING CASE: no probe file at all also STOPS, and is its OWN "
          "kind - 'we could not look' and 'there is nothing there' want "
          "different things from him",
          g_noprobe["stop"] is True and g_noprobe["kind"] == "no-probe-file",
          g_noprobe)
    msg_none = "\n".join(format_gate_stop(g_none, ["C:\\r\\machine-report.txt"]))
    msg_noprobe = "\n".join(format_gate_stop(g_noprobe, ["C:\\r\\machine-report.txt"]))
    check("gate message: says nothing was downloaded, names the report to send "
          "back, names the CPU .bat, and quotes the measured 202s rather than "
          "the word 'slow'",
          "NOTHING was downloaded" in msg_none
          and "C:\\r\\machine-report.txt" in msg_none
          and CPU_BAT in msg_none and str(CPU_SECONDS_PER_IMAGE) in msg_none,
          msg_none[:400])
    check("gate message: the zero arrives with its denominator - every source "
          "the probe tried is printed under it",
          "dxdiag /x -> 0 adapter(s) from 0 row(s) seen" in msg_none
          and "3 row(s) seen" in msg_none, msg_none[:400])
    msg_blind = "\n".join(format_gate_stop(
        gpu_gate({"probe_file_read": True, "gpus": []}), ["r.txt"]))
    check("gate message: with NO source log it says the zero carries no "
          "denominator, instead of asserting there is no card",
          "NO source log" in msg_blind and "denominator" in msg_blind
          and "may mean the probe could not look" in msg_blind, msg_blind[:400])
    check("gate message: the two stops read differently - one says no card, the "
          "other says we could not look",
          "NO display adapter on this PC" in msg_none
          and "NO display adapter on this PC" not in msg_noprobe
          and "no report" in msg_noprobe, msg_noprobe[:400])
    # THE DELIBERATE SLOW PATH still works, and is still capped.
    g_forced = gpu_gate(none_found, force_cpu=True)
    check("gate: --force-cpu on a machine with no card PROCEEDS - the slow run "
          "is available on purpose, it is just never the default",
          g_forced["stop"] is False and g_forced["kind"] == "forced-cpu", g_forced)
    forced_plan = plan(dict(one, ram_bytes=32 * 1024**3), force_cpu=True)
    check("--force-cpu plans the CPU backend even on a 12GB AMD card, and the CPU "
          "CAP IS NOT LIFTED (2 items, half size) - asking for the slow path is "
          "not permission to spend an hour",
          forced_plan["backend"] == "cpu" and forced_plan["backend_chain"] == ["cpu"]
          and forced_plan["item_limit"] == 2 and forced_plan["size_scale"] == 0.5
          and any(CPU_BAT in r for r in forced_plan["reasons"]), forced_plan)

    # 11a. THE FILE THE STOP MESSAGE TELLS HIM TO DOUBLE-CLICK MUST EXIST.
    #      These are TEXT checks on the two .bat files, and they are not a
    #      substitute for running them - nothing here can. They catch the one
    #      failure this layer can see: the message and the files disagreeing
    #      after a rename, which turns the escape hatch into a dead end.
    here = pathlib.Path(__file__).parent
    main_bat = here / "1 MAKE THE PICTURES.bat"
    cpu_bat = here / CPU_BAT
    check("the CPU .bat named in the stop message actually EXISTS beside this "
          "script - a message pointing at a file that is not there is worse "
          "than no message", cpu_bat.is_file(), str(cpu_bat))
    mb = main_bat.read_text(encoding="utf-8", errors="replace") if main_bat.is_file() else ""
    cb = cpu_bat.read_text(encoding="utf-8", errors="replace") if cpu_bat.is_file() else ""
    check("the two .bat files agree on the handoff: one SETS LEDGER_FORCE_CPU "
          "and calls the other, which READS it into --force-cpu (text check - "
          "neither file can be executed here)",
          "LEDGER_FORCE_CPU=1" in cb and "1 MAKE THE PICTURES.bat" in cb
          and "if defined LEDGER_FORCE_CPU set \"PYARGS=--force-cpu\"" in mb
          and "%PYARGS%" in mb, (cb[-200:], "PYARGS" in mb))
    check("the main .bat has a paragraph for exit 5 - the stop is a documented "
          "outcome there, not an unrecognised code (text check)",
          '"%RC%"=="5"' in mb and "STOPPED BEFORE DOWNLOADING" in mb
          and CPU_BAT in mb, '"%RC%"=="5"' in mb)
    # THE .BAT AND THE PYTHON MUST AGREE ABOUT WHO CARRIES THE FILES, because
    # they disagreed for eleven days: the .bat's success paragraph said SEND
    # BACK the report while the python said it had sent it - and neither was
    # right, since nothing was sending. Two texts, one claim, and the pair is
    # what decays. The check reads the success paragraph ONLY: the failure
    # paragraphs must keep saying send-by-hand, because in those cases nothing
    # was pushed.
    done_para = mb.split('if "%RC%"=="0" (')[-1].split(') else if')[0]
    check("the .bat's SUCCESS paragraph does not ask for the report by hand - "
          "the run sends it (text check)",
          "SEND BACK" not in done_para and "NOTHING TO SEND" in done_para,
          done_para[:200])
    check("the .bat still asks for a HUMAN look at the pictures - the one part "
          "no push can do",
          "recognisable face" in done_para, done_para[-200:])
    # AND IT MUST UPDATE ITSELF FIRST. `REPICK.bat` has pulled since the day it
    # was written and this one never did, so a fix landing in the repository
    # could not reach the PC that runs it - the sender was wired here while
    # that machine kept running the copy it had. One idea, two implementations,
    # and the one nobody looked at is the one missing the line.
    check("the .bat pulls before generating - a fix in the repo must reach the "
          "PC that runs it (text check)",
          "git pull origin" in mb and "PULL FAILED" in mb,
          "git pull origin" in mb)
    # AND THE PULL CANNOT DELIVER ITSELF. The first run after this .bat
    # changes is always the OLD copy - which is what happened on 26 Aug: the
    # pull landed in the repository and the run that would have used it was
    # the run without it. So the .bat compares its own timestamp across the
    # pull and re-launches once. Both halves are pinned: the re-launch, and
    # the guard that makes it strictly once, because a loop here is worse
    # than the hole it closes.
    check("the .bat re-launches itself when the pull updates it - a pull "
          "cannot otherwise deliver a change to the puller (text check)",
          "SELFWAS" in mb and "SELFNOW" in mb and 'call "%~f0"' in mb,
          "SELFWAS" in mb)
    check("the re-launch can happen at most once (text check)",
          "LEDGER_RELAUNCHED" in mb and mb.count('call "%~f0"') == 1,
          mb.count('call "%~f0"'))

    # 11b. AND THE GATE THROUGH main(), WITH THE NETWORK BOOBY-TRAPPED. The
    #      check above tests the decision; this tests that the decision is
    #      actually CONSULTED, and before the download rather than after it.
    #      `touched` is the evidence: it records every URL anything asked for.
    real_open2, real_argv = urllib.request.urlopen, sys.argv
    touched = []

    def _tripwire(req, timeout=None):
        touched.append(getattr(req, "full_url", str(req)))
        raise urllib.error.URLError("selftest tripwire: the network was touched")

    def _run_main(machine_obj, extra_args):
        touched.clear()
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            mj = td / "machine.json"
            mj.write_text(json.dumps(machine_obj), encoding="utf-8")
            sys.argv = ["imagegen.py", "all", "--machine", str(mj),
                        "--workspace", str(td / "ws")] + extra_args
            with contextlib.redirect_stdout(io.StringIO()) as cap:
                rc = main()
            files = sorted(p.name for p in (td / "ws").rglob("*") if p.is_file())
            return rc, cap.getvalue(), files

    try:
        urllib.request.urlopen = _tripwire
        disk = {"free_disk_bytes": 400 * 1024**3, "ram_bytes": 32 * 1024**3}
        rc, out, files = _run_main(dict(none_found, **disk), [])
        check("gate through main() REJECTING CASE: no adapter means exit 5, and "
              "NOT ONE BYTE was requested from the network",
              rc == 5 and touched == [] and "STOPPED ON PURPOSE" in out,
              f"rc={rc} touched={touched[:3]}")
        check("gate through main(): it still writes the report it tells him to "
              "send back, and writes no model or runtime file",
              "machine-report.txt" in files
              and not any(f.endswith((".gguf", ".zip", ".safetensors")) for f in files),
              files)
        rc2, out2, _ = _run_main(dict(one, **disk), [])
        check("gate through main() ACCEPTING CASE: one adapter gets PAST the "
              "gate and reaches the download - the gate is not a wall",
              rc2 != 5 and len(touched) > 0 and "STOPPED ON PURPOSE" not in out2,
              f"rc={rc2} touched={touched[:3]}")
        rc3, out3, _ = _run_main(dict(none_found, **disk), ["--force-cpu"])
        check("gate through main(): --force-cpu on the no-adapter machine also "
              "gets past, so the slow path is genuinely reachable in one click",
              rc3 != 5 and len(touched) > 0, f"rc={rc3} touched={touched[:3]}")
    finally:
        urllib.request.urlopen, sys.argv = real_open2, real_argv

    # 12. THE SKIP - a re-run must not overwrite what is already good. He was
    #     told to copy two PNGs aside by hand before re-running; that is the
    #     second decision this exists to remove. ACCEPTING CASE FIRST: an
    #     existing GOOD picture is left alone.
    try:
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            out = td / "batch"
            subprocess.run = _Fake(0)
            first = run_batch(pathlib.Path("stub"), td, gpu, spec, out, 60,
                              lambda s="": None)
            keep = out / (spec["items"][0]["id"] + ".png")
            before = sha256(keep)

            calls = []

            class _Count(_Fake):
                def __call__(self, cmd, **kw):
                    calls.append(pathlib.Path(cmd[cmd.index("--output") + 1]).stem)
                    return _Fake.__call__(self, cmd, **kw)

            subprocess.run = _Count(0)
            logs = []
            # A SENDER THAT RECORDS WHAT IT WAS OFFERED, so the skip path can
            # be asked the question that actually failed on 26 Aug: not "did
            # it skip", which was always right, but "did the pictures still
            # reach the project".
            offered = []

            class _Noting:
                enabled = True
                def note(self, path):
                    offered.append(pathlib.Path(path).name)
                def note_image(self, path):
                    self.note(path)
                def maybe(self, message, force=False):
                    return None

            again = run_batch(pathlib.Path("stub"), td, gpu, spec, out, 60,
                              lambda s="": logs.append(s), publisher=_Noting())
            check("skip ACCEPTING CASE: a second run over a finished batch makes "
                  "NOTHING again - every item is skipped and the generator is "
                  "never called",
                  calls == [] and again["items_skipped"] == len(spec["items"])
                  and again["items_written"] == 0 and again["status"] == "DONE"
                  and first["items_written"] == len(spec["items"]),
                  f"calls={calls} skipped={again['items_skipped']} "
                  f"status={again['status']}")
            check("skip ACCEPTING CASE: the file on disk is BYTE-IDENTICAL "
                  "afterwards - this is the overwrite that cost him his two "
                  "hand-picked fascias",
                  sha256(keep) == before, keep)
            # THE FAULT THIS SELFTEST EXISTS FOR. Every item skipped, and the
            # run that was dispatched to BANK twelve finished pictures pushed
            # the manifest and the report and not one PNG - because only
            # images the run WROTE were handed to the sender. The count is
            # asserted, not just "some picture was offered": one missing name
            # is one picture left on a PC nobody backs up.
            pngs = [o for o in offered if o.endswith(".png")]
            check("skip: EVERY skipped picture is still offered to the sender - "
                  "the question is whether it is in the project, not whether "
                  "this run made it",
                  len(pngs) == len(spec["items"]),
                  "%d of %d offered: %s" % (len(pngs), len(spec["items"]), pngs))

            check("skip: it is ANNOUNCED per item and says how to undo it - a "
                  "silent skip is as bad as a silent overwrite",
                  any("SKIP, already made" in s for s in logs)
                  and any("delete" in s for s in logs)
                  and sum(1 for s in logs if "SKIP" in s) == len(spec["items"]),
                  [s for s in logs[:3]])
            rec = again["images"][0]
            check("skip: the manifest keeps the skipped item's provenance and "
                  "does NOT claim this run made it",
                  rec["status"] == "SKIPPED" and rec["sha256"]
                  and rec["review"] == "pending"
                  and "did not make it" in rec.get("made_by", "")
                  and rec["blank_check"]["verdict"] == "varied", rec)
            check("skip: the counts carry their denominator - rechecked, skipped "
                  "and remade are three numbers, not one",
                  again["blank_check"]["rechecked"] == len(spec["items"])
                  and again["blank_check"]["remade"] == 0
                  and again["blank_check"]["checked"] == 0,
                  again["blank_check"])
            # REJECTING CASE: an existing BLANK png is NOT a made picture. This
            # is #1031's output sitting in the output directory, and skipping it
            # would make the blank check useless the moment it fired once.
            _write_png(keep, 64, 48, lambda x, y: (0, 0, 0))
            calls.clear()
            logs.clear()
            subprocess.run = _Count(0)
            over_blank = run_batch(pathlib.Path("stub"), td, gpu, spec, out, 60,
                                   lambda s="": logs.append(s))
            check("skip REJECTING CASE: an existing BLANK PNG is NOT skipped - it "
                  "is made again, and the run says why",
                  calls == [spec["items"][0]["id"]]
                  and over_blank["items_skipped"] == len(spec["items"]) - 1
                  and over_blank["items_written"] == 1
                  and over_blank["blank_check"]["remade"] == 1
                  and any("is BLANK, so it is NOT skipped" in s for s in logs),
                  f"calls={calls} skipped={over_blank['items_skipped']} "
                  f"remade={over_blank['blank_check']['remade']}")
            # ...and one that cannot be decoded at all is not skipped either:
            # "a file exists" was never the question.
            keep.write_bytes(b"\x89PNG\r\n\x1a\n stub")
            calls.clear()
            subprocess.run = _Count(0)
            over_bad = run_batch(pathlib.Path("stub"), td, gpu, spec, out, 60,
                                 lambda s="": None)
            check("skip REJECTING CASE: an UNDECODABLE PNG is not skipped either "
                  "- it has not been shown to be good, only to exist",
                  calls == [spec["items"][0]["id"]]
                  and over_bad["blank_check"]["remade"] == 1, calls)
            # And the deliberate redo, which is the other half of the promise.
            calls.clear()
            subprocess.run = _Count(0)
            redone = run_batch(pathlib.Path("stub"), td, gpu, spec, out, 60,
                               lambda s="": None, redo=True)
            check("skip: --redo makes all of them again, ignoring what is on disk",
                  len(calls) == len(spec["items"]) and redone["items_skipped"] == 0
                  and redone["items_written"] == len(spec["items"])
                  and redone["blank_check"]["rechecked"] == 0,
                  f"calls={len(calls)} skipped={redone['items_skipped']}")
    finally:
        subprocess.run = real

    # 13. THE UNATTENDED LANE. --only, --limit, --fail-on-blank and the verdict
    #     file exist for one route: .github/workflows/ledger-imagegen.yml runs
    #     this batch on Jafar's PC with nobody watching, and the only thing
    #     that comes back is what CI commits. Every check below is about a
    #     night not being wasted, so every one of them has an accepting case
    #     first and a rejecting case that can actually fire.
    ids = [i["id"] for i in spec["items"]]

    class _Seen(_Fake):
        """A generator that records which items it was asked to make."""

        def __init__(self, rc, paint="varied"):
            _Fake.__init__(self, rc, paint)
            self.seen = []

        def __call__(self, cmd, **kw):
            self.seen.append(pathlib.Path(cmd[cmd.index("--output") + 1]).stem)
            return _Fake.__call__(self, cmd, **kw)

    try:
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            out = td / "lane"
            fake = _Seen(0)
            subprocess.run = fake
            m = run_batch(pathlib.Path("stub"), td, gpu, spec, out, 60,
                          lambda s="": None, only=[ids[1], ids[3]],
                          run_sha="aaaaaaa")
            check("--only ACCEPTING: exactly the two named items are generated, "
                  "and the denominators say selected-of-spec rather than one "
                  "number twice",
                  sorted(fake.seen) == sorted([ids[1], ids[3]])
                  and m["items_written"] == 2 and m["items_selected"] == 2
                  and m["items_in_spec"] == len(ids)
                  and len(m["not_attempted"]) == len(ids) - 2
                  and any("--only" in c for c in m["caps"]),
                  f"seen={fake.seen} selected={m.get('items_selected')} "
                  f"caps={m['caps']}")
            check("--only: the manifest records THIS RUN'S commit, per picture "
                  "and for the batch - without it a manifest from last week "
                  "and one from tonight are the same file",
                  m["run"]["sha"] == "aaaaaaa"
                  and all(r["made_on_run"] == "aaaaaaa" for r in m["images"])
                  and all(r["seen_on_run"] == "aaaaaaa" for r in m["images"]),
                  m["run"])

            # REJECTING CASE: an id that is in no prompt. This is a typo in a
            # dispatch input, and the failure it would otherwise wear is "0
            # generated, everything fine".
            fake2 = _Seen(0)
            subprocess.run = fake2
            bad = run_batch(pathlib.Path("stub"), td, gpu, spec, td / "lane2",
                            60, lambda s="": None, only=["no_such_item_999"],
                            run_sha="aaaaaaa")
            check("--only REJECTING: an id that exists in no prompt REFUSES the "
                  "run, names the id, and generates nothing",
                  bad["status"] == "REFUSED" and fake2.seen == []
                  and any("no_such_item_999" in p for p in bad.get("problems", [])),
                  f"status={bad['status']} seen={fake2.seen} "
                  f"problems={bad.get('problems')}")

            # --limit, on a fresh directory: it bounds GENERATION.
            lim = td / "lim"
            fake3 = _Seen(0)
            subprocess.run = fake3
            l1 = run_batch(pathlib.Path("stub"), td, gpu, spec, lim, 60,
                           lambda s="": None, limit=2, run_sha="aaaaaaa")
            check("--limit ACCEPTING: exactly 2 pictures are generated, the "
                  "rest are named in not_attempted, and the cap is announced",
                  fake3.seen == ids[:2] and l1["items_written"] == 2
                  and len(l1["not_attempted"]) == len(ids) - 2
                  and any("--limit" in c for c in l1["caps"]),
                  f"seen={fake3.seen} written={l1['items_written']} "
                  f"caps={l1['caps']}")
            # THE SEMANTIC THE FLAG IS FOR, and the one a positional cap gets
            # wrong: the second run must generate the NEXT two rather than
            # spending its budget on the two already on disk. A `--limit 4`
            # against a batch whose first fourteen are made must make four
            # pictures, not none.
            fake4 = _Seen(0)
            subprocess.run = fake4
            l2 = run_batch(pathlib.Path("stub"), td, gpu, spec, lim, 60,
                           lambda s="": None, limit=2, run_sha="bbbbbbb")
            check("--limit: a skipped item does NOT spend the budget - the "
                  "second run makes the NEXT two, not none",
                  fake4.seen == ids[2:4] and l2["items_written"] == 2
                  and l2["items_skipped"] == 2,
                  f"seen={fake4.seen} skipped={l2['items_skipped']}")

            # --fail-on-blank, ACCEPTING CASE FIRST: it must not stop a run
            # that is going fine. A guard that cannot tell a good night from a
            # bad one is a ratchet.
            fake5 = _Seen(0)
            subprocess.run = fake5
            g = run_batch(pathlib.Path("stub"), td, gpu, spec, td / "good", 60,
                          lambda s="": None, fail_on_blank=True,
                          run_sha="aaaaaaa")
            check("--fail-on-blank ACCEPTING: a clean batch runs to the end "
                  "with the guard armed",
                  g["items_written"] == len(ids) and g["status"] == "DONE"
                  and g["blank_check"]["blank"] == 0,
                  f"written={g['items_written']} status={g['status']}")
            # REJECTING: exit 0 and a blank file, which is #1031 exactly. One
            # blank stops it - two would already have been stopped by the
            # first-two-failures rule, so the flag has to be provably tighter
            # than the behaviour that was there before it.
            fake6 = _Seen(0, "blank")
            subprocess.run = fake6
            bl = run_batch(pathlib.Path("stub"), td, gpu, spec, td / "blank", 60,
                           lambda s="": None, fail_on_blank=True,
                           run_sha="aaaaaaa")
            check("--fail-on-blank REJECTING: the FIRST blank stops the run, "
                  "and the count ships its denominator",
                  len(fake6.seen) == 1 and bl["blank_check"]["blank"] == 1
                  and bl["blank_check"]["checked"] == 1
                  and bl["items_written"] == 0
                  and len(bl["not_attempted"]) == len(ids) - 1
                  and any("--fail-on-blank" in c for c in bl["caps"]),
                  f"seen={fake6.seen} blank_check={bl['blank_check']}")
            # AND THE HALF THE FAILURE BRANCH CANNOT SEE. An undecodable PNG is
            # counted as written, so a stop wired into the failure path would
            # never fire on it and the night would run to the end on files
            # nothing could read.
            fake7 = _Seen(0, "stub")
            subprocess.run = fake7
            un = run_batch(pathlib.Path("stub"), td, gpu, spec, td / "unread",
                           60, lambda s="": None, fail_on_blank=True,
                           run_sha="aaaaaaa")
            check("--fail-on-blank REJECTING: an UNDECODABLE PNG stops the run "
                  "too, and it is counted apart from blank",
                  len(fake7.seen) == 1 and un["blank_check"]["undecodable"] == 1
                  and un["blank_check"]["blank"] == 0
                  and un["blank_check"]["checked"] == 1,
                  f"seen={fake7.seen} blank_check={un['blank_check']}")

            # ------------------------------------------------------------
            # THE VERDICT FILE CI COMMITS. Accepting case first, on the
            # directory the --only run above actually wrote.
            vpath = out / VERDICT_NAME
            rc = imagegen_verdict(out, "aaaaaaa", "generate=success extra=one")
            text = vpath.read_text(encoding="utf-8")
            done = [x for x in text.splitlines() if x.startswith("done ")][0]
            check("verdict ACCEPTING: a run that generated two pictures is "
                  "BANKED, line 1 names the commit, and the counts are on the "
                  "done line",
                  rc == 0 and text.splitlines()[0].startswith("# LEDGER imagegen - aaaaaaa")
                  and "imagegenVerdict=BANKED" in done and "wroteThisRun=2" in done
                  and "remeasured=2" in done and "remeasuredBlank=0" in done,
                  done)
            check("verdict: NO VALUE CARRIES A SPACE, including the step "
                  "outcomes CI hands in - every reader splits on whitespace "
                  "and truncates silently",
                  "steps generate=success-extra=one" in text
                  and all(len(x.split("=", 1)[1].split()) <= 1
                          for line in text.splitlines()
                          if not line.startswith("#")
                          for x in line.split() if "=" in x),
                  [x for x in text.splitlines() if x.startswith("steps ")])
            check("verdict: per-picture numbers sit on the picture lines and "
                  "whole-run numbers on the done line, never both under one key",
                  sum(1 for x in text.splitlines() if x.startswith("image ")) == 2
                  and "wroteThisRun" not in text.split("done ")[0].split("image ")[-1],
                  [x for x in text.splitlines() if x.startswith("image ")][:1])

            # REJECTING 1: a directory nothing ran in. It must say NO RUN in
            # words, not print a clean zero.
            empty = td / "nothing"
            empty.mkdir()
            rc = imagegen_verdict(empty, "aaaaaaa", "generate=failure")
            etext = (empty / VERDICT_NAME).read_text(encoding="utf-8")
            check("verdict REJECTING: a run that generated nothing says NO RUN "
                  "and fails, with the zero's denominators beside it",
                  rc == 1 and "NO RUN" in etext
                  and "imagegenVerdict=NO-RUN" in etext
                  and "wroteThisRun=0" in etext and "pngsInOutDir=0" in etext,
                  etext.splitlines()[-1])
            # REJECTING 2: the same finished directory read on ANOTHER commit.
            # This is the fault the whole run stamp exists for: last night's
            # pictures committed under tonight's sha as tonight's work.
            rc = imagegen_verdict(out, "ccccccc", "generate=success")
            stale = vpath.read_text(encoding="utf-8")
            check("verdict REJECTING: a manifest written by another commit is "
                  "NO RUN, and names the run that did write it",
                  rc == 1 and "imagegenVerdict=NO-RUN" in stale
                  and "aaaaaaa" in stale.split("done ")[1]
                  and "manifestIsThisRun=no" in stale,
                  [x for x in stale.splitlines() if x.startswith("done ")])
            # REJECTING 3, AND IT IS THE ONE THAT PAYS: the manifest says OK
            # and the file on disk is blank. Everything upstream can be right
            # and the pictures still be empty, because the thing that lies in
            # #1031 is an exit code. A verdict that believed the manifest would
            # be green here.
            _write_png(out / (ids[1] + ".png"), 64, 48, lambda x, y: (0, 0, 0))
            rc = imagegen_verdict(out, "aaaaaaa", "generate=success")
            lied = vpath.read_text(encoding="utf-8")
            check("verdict REJECTING: a manifest that says OK about a file that "
                  "is BLANK ON DISK fails - the verdict re-measures rather than "
                  "believing the run that wrote it",
                  rc == 1 and "imagegenVerdict=BLANKS" in lied
                  and "remeasuredBlank=1" in lied and "remeasured=2" in lied,
                  [x for x in lied.splitlines() if x.startswith("done ")])

            # WHAT CI MAY COMMIT. The list is derived from the manifest, so a
            # picture with no record cannot ride along, and a blank one cannot
            # be committed as art.
            (out / (ids[0] + ".BLANK.png")).write_bytes(
                (out / (ids[1] + ".png")).read_bytes())
            staged, outside = staged_file_list(out, "aaaaaaa", repo=td)
            check("staged files ACCEPTING: the verdict, the manifest, the resume "
                  "record, PROGRESS and both pictures, all by name and all "
                  "relative to the repository",
                  outside == 0 and len(staged) == 6
                  and all((td / x).exists() for x in staged)
                  and sum(1 for x in staged if x.endswith(".png")) == 2
                  and any(x.endswith(VERDICT_NAME) for x in staged),
                  staged)
            check("staged files REJECTING: a .BLANK.png on disk is NEVER staged "
                  "- it is evidence, and a directory of blank PNGs is what a "
                  "later reader mistakes for art",
                  not any(".BLANK.png" in x for x in staged),
                  [x for x in staged if "BLANK" in x])
            stale_staged, _ = staged_file_list(out, "ccccccc", repo=td)
            check("staged files REJECTING: a run whose manifest is not its own "
                  "stages ONLY its verdict - a failed run must not commit the "
                  "checkout's older files as its own evidence",
                  len(stale_staged) == 1 and stale_staged[0].endswith(VERDICT_NAME),
                  stale_staged)
    finally:
        subprocess.run = real

    # 13b. AND THE FLAGS ARE WIRED, which is the fault this file has already
    #      paid for once: `Publisher` was defined, documented and never
    #      constructed. A flag parsed and not passed is the same failure with a
    #      smaller blast radius, and a text check catches it in the container
    #      rather than on the night it mattered.
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    passed = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and getattr(node.func, "id", "") == "run_batch"
                and any(isinstance(k.value, ast.Attribute)
                        and getattr(k.value.value, "id", "") == "a"
                        for k in node.keywords)):
            passed |= {k.arg for k in node.keywords}
    check("WIRED: main passes only, limit, run_sha and fail_on_blank through to "
          "the batch - a flag that is parsed and never used is the Publisher "
          "fault in miniature",
          {"only", "limit", "run_sha", "fail_on_blank"} <= passed, sorted(passed))
    check("WIRED: --verdict and --staged-files reach their functions, and the "
          "exit code the unattended lane reads is in main",
          "imagegen_verdict(od" in src and "staged_files(od" in src
          and "return 6" in src, "")

    # ------------------------------------------------------------------
    # THE SENDER. It had NO coverage and NO call site: `Publisher` was
    # defined, given a plain sentence for every failure path, and never once
    # constructed - `run_batch(... publisher=None)` was its only live call.
    # So every run for eleven days ended with a person carrying files by hand
    # while the report said the run had sent them.
    #
    # The wiring check is FIRST, because it is the one that was missing. It
    # reads this file's own source rather than a fixture: a test that the
    # class behaves correctly is worth nothing while nothing calls it, which
    # is rule 6 and is exactly what happened here.
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    main_fn = next((n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
    live_calls = [n for n in ast.walk(main_fn)] if main_fn else []
    wired = any(isinstance(n, ast.Call)
                and getattr(n.func, "id", "") == "run_batch"
                and any(k.arg == "publisher" for k in n.keywords)
                for n in live_calls)
    check("WIRED: main passes a publisher to run_batch", wired,
          "run_batch is called without publisher= - the sender is dead code")
    made = any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "Publisher"
               for n in live_calls)
    check("WIRED: main constructs a Publisher", made,
          "Publisher is never instantiated on the live path")

    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        bare, clone = td / "origin.git", td / "clone"
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0", LC_ALL="C")
        def git(*args, cwd=None):
            return subprocess.run(["git"] + list(args), cwd=str(cwd or clone),
                                  capture_output=True, text=True, env=env)
        have_git = subprocess.run(["git", "--version"], capture_output=True).returncode == 0
        if not have_git:
            check("sender: git present to test against", False, "git not installed")
        else:
            git("init", "--bare", "-b", EXPECTED_BRANCH, str(bare), cwd=td)
            clone.mkdir()
            git("init", "-b", EXPECTED_BRANCH)
            git("remote", "add", "origin", str(bare))
            git("config", "user.email", "t@t"); git("config", "user.name", "t")
            (clone / "seed.txt").write_text("seed\n")
            git("add", "seed.txt"); git("commit", "-m", "seed")
            git("push", "-u", "origin", EXPECTED_BRANCH)

            # ACCEPTING CASE FIRST, and it goes all the way to a real push -
            # preflight passing proves nothing about whether anything lands.
            said = []
            pub = Publisher(clone, said.append)
            check("sender ACCEPTING: a clone on the right branch preflights",
                  pub.preflight() is True, said)
            shot = clone / "pic.png"
            shot.write_bytes(b"\x89PNG\r\n\x1a\n")
            pub.note_image(shot)
            res = pub.publish("selftest picture")
            check("sender ACCEPTING: it actually pushes", res == "pushed", (res, said))
            landed = subprocess.run(["git", "ls-tree", "-r", "--name-only",
                                     EXPECTED_BRANCH], cwd=str(bare),
                                    capture_output=True, text=True, env=env).stdout
            check("sender ACCEPTING: the file is ON the remote, not just committed",
                  "pic.png" in landed, landed)
            check("sender ACCEPTING: a second publish with nothing new says so",
                  pub.publish("again") == "nothing")
            # AND THE PARAGRAPH THE PERSON READS SAYS SENT - derived, not typed.
            para = " ".join(publisher_paragraph(pub))
            check("report paragraph: a run that pushed says Sent",
                  "Sent:" in para and "paste" in para, para)

            # REJECTING: wrong branch. The pictures must NOT go anywhere.
            git("checkout", "-q", "-b", "some-other-branch")
            said2 = []
            bad = Publisher(clone, said2.append)
            check("sender REJECTING: wrong branch refuses",
                  bad.preflight() is False and "branch" in (bad.off_reason or ""),
                  bad.off_reason)
            check("sender REJECTING: refusing is reported to the person",
                  any("SENDING BACK IS OFF" in x for x in said2), said2)
            check("report paragraph: a refusing run tells him to zip and send",
                  "zip" in " ".join(publisher_paragraph(bad)).lower())

            # REJECTING: not a clone at all.
            plain = td / "plain"; plain.mkdir()
            nope = Publisher(plain, lambda s="": None)
            check("sender REJECTING: a folder that is not a clone refuses",
                  nope.preflight() is False)

        # REJECTING: no repository was found, which is the .bat's own failure
        # mode and must not read as success.
        none = Publisher(None, lambda s="": None)
        check("sender REJECTING: no repository refuses", none.preflight() is False)
        check("report paragraph: OFF is never silent",
              "OFF" in " ".join(publisher_paragraph(none)))
        check("report paragraph: NO publisher is its own case, not 'sent'",
              "NOT WIRED" in " ".join(publisher_paragraph(None)))
        check("sender: switched off by --no-send is a distinct, named state",
              Publisher(None, lambda s="": None, enabled=False).off_reason
              == "switched off for this run")

    print("-" * 60)
    print(f"  {ok} passed, {fail} failed, {ok + fail} checks run")
    return 1 if fail else 0


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="LEDGER local image generation")
    ap.add_argument("command", nargs="?", default="all",
                    choices=["all", "plan", "fetch", "generate"])
    ap.add_argument("--machine", help="machine.json written by the probe")
    ap.add_argument("--workspace", help="where the runtime and weights live "
                                        "(OUTSIDE the repo)")
    ap.add_argument("--repo", help="repository root, for the report and outputs")
    ap.add_argument("--out", help="override the output directory")
    ap.add_argument("--no-send", action="store_true",
                    help="generate but do not commit or push anything back. "
                         "The default is to SEND, because a run nobody is "
                         "watching that ends with files needing to be carried "
                         "by hand has not finished.")
    ap.add_argument("--max-minutes", type=float, default=480.0,
                    help="wall-clock cap. Default 480 (eight hours) because "
                         "the batch this exists for runs OVERNIGHT unattended. "
                         "It was 60, sized for a 14-item test batch, and the "
                         "selftest caught that the moment the file grew to 42 "
                         "items: 66 estimated minutes against a 60-minute cap, "
                         "so a real overnight run would have stopped a third "
                         "of the way in and needed running again. The cap is "
                         "still a backstop against a runaway, not a target.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--series", nargs="?", const=".", metavar="DIR",
                    help="print the blankness series over every PNG under DIR. "
                         "This is the instrument BLANK_MAX_SPREAD was read off; "
                         "it exists so the bound can be re-derived rather than "
                         "believed.")
    ap.add_argument("--dry-run", action="store_true",
                    help="plan and print the exact commands, download nothing")
    ap.add_argument("--force-cpu", action="store_true",
                    help="THE DELIBERATE SLOW PATH. Run on the CPU whatever the "
                         f"probe found, which is what \"{CPU_BAT}\" passes. It "
                         "bypasses the no-GPU stop; it does NOT lift the CPU "
                         "batch cap, because the cap is what keeps a slow run "
                         "from becoming an afternoon.")
    ap.add_argument("--redo", action="store_true",
                    help="regenerate every item even if its PNG is already on "
                         "disk. Without this, an item whose PNG exists and "
                         "passes the blank check is skipped and said so; "
                         "deleting one PNG redoes just that one.")
    # THE UNATTENDED LANE'S FOUR FLAGS. They exist because the batch now runs
    # on Jafar's PC from CI (.github/workflows/ledger-imagegen.yml) with nobody
    # watching, and everything below is about a night not being wasted.
    ap.add_argument("--only",
                    help="comma-separated item ids from prompts.json, and "
                         "ONLY those are generated. An id that is in no prompt "
                         "REFUSES the run rather than quietly selecting "
                         "nothing, because a typo in a dispatch input would "
                         "otherwise wear the words '0 generated, all fine'.")
    ap.add_argument("--limit", type=int,
                    help="stop after this many pictures have been GENERATED. "
                         "Items already on disk that pass the skip check cost "
                         "nothing and do not count against it, so --limit 4 on "
                         "a batch whose first fourteen are made generates the "
                         "next four. This is the flag that proves a new route "
                         "on a handful instead of betting a night on 31.")
    ap.add_argument("--fail-on-blank", action="store_true",
                    help="stop at the first blank or undecodable PNG and exit "
                         "6. #1031 is a KNOWN mode, so reproducing it thirty "
                         "more times overnight teaches nothing and costs the "
                         "night. The one-click .bat does NOT pass this: a "
                         "blank among ten good pictures is a finding for the "
                         "report, not a reason to tell him the run broke.")
    ap.add_argument("--run-sha",
                    default=(os.environ.get("GITHUB_SHA") or "")[:7] or "local",
                    help="the commit this batch is being generated on. It is "
                         "stamped into the manifest so a verdict can refuse a "
                         "manifest some earlier run left behind.")
    ap.add_argument("--verdict", action="store_true",
                    help="write the committed evidence file from what is on "
                         "disk, re-measuring every PNG. Non-zero when the run "
                         "banked nothing or produced a blank.")
    ap.add_argument("--staged-files", action="store_true",
                    help="print, one per line, the paths CI may git add")
    ap.add_argument("--steps", default="",
                    help="step outcomes as key=value pairs with no spaces, "
                         "recorded verbatim in the verdict")
    a = ap.parse_args()

    if a.series:
        return png_series(a.series)
    if a.selftest:
        return selftest()

    # THE TWO READ-ONLY MODES, ANSWERED BEFORE ANYTHING LOOKS AT THE MACHINE.
    # CI calls them after the batch, on a runner where the probe has already
    # been and gone; they must not need a GPU, a weight file or a machine.json
    # to say what is on disk.
    if a.verdict or a.staged_files:
        repo0 = pathlib.Path(a.repo) if (a.repo and a.repo.strip()) else None
        ws0 = (pathlib.Path(a.workspace) if a.workspace
               else pathlib.Path.cwd() / "ledger-imagegen")
        od = output_dir(repo0, ws0, a.out)
        if a.staged_files:
            return staged_files(od, a.run_sha, repo0)
        return imagegen_verdict(od, a.run_sha, a.steps, repo=repo0)

    machine = {}
    if a.machine and pathlib.Path(a.machine).exists():
        try:
            machine = json.loads(pathlib.Path(a.machine).read_text(encoding="utf-8-sig"))
            # WHETHER THE FILE WAS READ IS NOT THE SAME FACT AS WHAT IT SAID.
            # The gate needs to tell "the probe looked and found nothing" from
            # "the probe never wrote anything", and an empty gpus list looks
            # identical either way, so the distinction is recorded here where
            # it is known rather than inferred downstream from a message string.
            machine["probe_file_read"] = True
        except Exception as e:                                # noqa: BLE001
            machine = {"probe": f"machine.json unreadable: {type(e).__name__}: {e}",
                       "probe_file_read": False}
    else:
        machine = {"probe": f"machine.json missing at {a.machine}",
                   "probe_file_read": False}
    machine.setdefault("python", sys.version.split()[0])

    pl = plan(machine, force_cpu=a.force_cpu)
    lines = []

    def log(s=""):
        print(s, flush=True)
        lines.append(s)

    # An empty --repo (the .bat could not find CLAUDE.md) must mean NO
    # repo. pathlib.Path("") is ".", which would scatter output into
    # whatever directory the shell happened to be standing in - the
    # exact fault that made BarkGen's manifest go stale.
    repo = pathlib.Path(a.repo) if (a.repo and a.repo.strip()) else None
    reports = []
    if repo and (repo / "game-design" / "agent-reports").is_dir():
        reports.append(repo / "game-design" / "agent-reports" / "machine-report.txt")
    ws = pathlib.Path(a.workspace) if a.workspace else pathlib.Path.cwd() / "ledger-imagegen"
    ws.mkdir(parents=True, exist_ok=True)
    reports.append(ws / "machine-report.txt")

    outdir = output_dir(repo, ws, a.out)

    # THE SENDER, CONSTRUCTED HERE AND PREFLIGHTED BEFORE ANY GENERATING.
    # It used to be constructed nowhere, which is why eleven days of runs
    # ended with a person copying files by hand. Preflight is called EARLY on
    # purpose: "this clone is on the wrong branch" is a sentence worth having
    # in minute one, not after four hours of pictures that then cannot go
    # anywhere. Both outcomes are normal and both print.
    pub = Publisher(repo, log, enabled=not a.no_send)
    pub.preflight()

    log(format_report(machine, pl, publisher=pub))
    if a.command == "plan" or a.dry_run:
        spec = json.loads((pathlib.Path(__file__).parent / "prompts.json").read_text())
        log("DRY RUN - nothing downloaded. First command would be:")
        it = spec["items"][0]
        # THE FLAGS PRINTED HERE ARE THE ONES THE IMAGE WOULD GET, not the
        # plan's - they differ on Vulkan above 512x512 (#1673), and a dry run
        # that prints a command the real run would not issue is a dry run that
        # lies about the only thing it is for.
        dry_flags, dry_note = image_flags(pl, it["width"], it["height"])
        log("  sd-cli.exe --diffusion-model " + pl["quant_file"] +
            " --vae ae.safetensors --llm " + TEXT_ENCODER["file"] +
            f" -p \"{build_prompt(it, spec['content_rules']['rules_clause'], spec['style'])[:150]}...\"" +
            f" --cfg-scale 1.0 --steps 8 -W {it['width']} -H {it['height']} " +
            " ".join(dry_flags))
        if dry_note:
            log(f"  and per image: {dry_note}")
        log(f"  model would be fetched from the first of {len(model_urls(pl['quant']))} "
            f"candidates: {model_urls(pl['quant'])[0]}")
        for p in reports:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(format_report(machine, pl, lines[-3:]), encoding="utf-8")
            log(f"report written: {p}")
        return 0

    # THE GATE, AND IT IS THE FIRST THING AFTER THE REPORT ON PURPOSE: before
    # the disk check, before the runtime, before one byte of the 6.7 GB. The
    # report has already been printed above, so he sees WHAT was found before
    # he sees what was decided about it.
    gate = gpu_gate(machine, force_cpu=a.force_cpu)
    if gate["stop"]:
        for line in format_gate_stop(gate, reports):
            log(line)
        for p in reports:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(format_report(machine, pl, [
                "RUN STOPPED BEFORE DOWNLOADING ANYTHING.",
                f"reason: {gate['kind']} - {gate['why']}",
                f"display adapters found: {gate['found']}",
                f"probe: {gate['probe']}",
                f"sources tried: {gate['sources'] or 'NONE RECORDED'}",
                "nothing was downloaded and nothing was generated.",
                f"the deliberate CPU path is \"{CPU_BAT}\".",
            ]), encoding="utf-8")
            log(f"report written: {p}")
        return 5

    if pl["disk_ok"] is False:
        log(f"REFUSING TO START: {pl['free_disk_gb']} GB free, and this needs "
            f"{MIN_FREE_DISK_GB} GB. Free some space and double-click again.")
        for p in reports:
            p.write_text(format_report(machine, pl, ["refused: not enough disk"]),
                         encoding="utf-8")
        return 2

    models = ws / "models"
    models.mkdir(parents=True, exist_ok=True)
    fetched = []
    try:
        log(f"Downloading about {pl['download_bytes']/1e9:.1f} GB, once. "
            f"It resumes if interrupted.")
        exe = None
        for backend in pl["backend_chain"]:
            try:
                exe = ensure_runtime(ws, backend)
                pl["backend"] = backend
                break
            except Exception as e:                            # noqa: BLE001
                log(f"  runtime '{backend}' unavailable: {e}")
        if exe is None:
            raise RuntimeError("no generator binary could be obtained for any "
                               "backend - see the lines above for each attempt")
        # THE CAP FOLLOWS THE BACKEND, NOT THE PROBE. `plan()` sets the CPU
        # batch cap when the probe found no GPU; falling BACK to CPU here is
        # the same situation arriving by a different route, and without this
        # it would start a twelve-image full-resolution CPU run - hours of it -
        # while the report still claimed a GPU plan.
        if pl["backend"] == "cpu" and pl["item_limit"] is None:
            pl["item_limit"], pl["size_scale"] = 2, 0.5
            pl["flags"] = ["--offload-to-cpu", "--diffusion-fa"]
            pl["reasons"].append("FELL BACK TO CPU after the GPU backends failed: "
                                 "batch capped at 2 items at half size, same as a "
                                 "machine with no GPU at all")
            log("  NOTE: the GPU backends did not work, so this is a CPU run. "
                "Capping the batch at 2 half-size images - that is a proof the "
                "wiring works, not the batch.")
        log(f"  generator: {exe}")
        q = QUANTS[pl["quant"]]
        p1, u1 = fetch_one(model_urls(pl["quant"]),
                           models / q[0], q[1], f"{MODEL['name']} {pl['quant']}")
        p2, u2 = fetch_one(TEXT_ENCODER["urls"], models / TEXT_ENCODER["file"],
                           TEXT_ENCODER["bytes"], "Qwen3-4B text encoder")
        p3, u3 = fetch_one(VAE["urls"], models / VAE["file"], VAE["bytes"], "VAE")
        for p, u, lic in ((p1, u1, MODEL["licence"]), (p2, u2, TEXT_ENCODER["licence"]),
                          (p3, u3, VAE["licence"])):
            fetched.append({"file": p.name, "bytes": p.stat().st_size, "url": u,
                            "licence": lic, "sha256": sha256(p, cap_mb=64)})
    except Exception as e:                                    # noqa: BLE001
        log("")
        log("SETUP FAILED - nothing was generated. What went wrong:")
        for line in str(e).splitlines():
            log(f"  {line}")
        log("")
        # NAME THE FILE THAT EXISTS. When the .bat could not find the repo the
        # report is in the workspace, and telling him to send a path that was
        # never written is how a clear failure becomes a confusing one.
        for p in reports:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(format_report(machine, pl, lines[-25:]), encoding="utf-8")
        log("Send back this window and: " + ", ".join(str(p) for p in reports))
        return 3

    if a.command == "fetch":
        for p in reports:
            p.write_text(format_report(machine, pl, ["fetch only: weights on disk"]),
                         encoding="utf-8")
        return 0

    outdir.mkdir(parents=True, exist_ok=True)
    spec = json.loads((pathlib.Path(__file__).parent / "prompts.json").read_text())
    only = [x.strip() for x in a.only.split(",") if x.strip()] if a.only else None
    log("")
    log(f"Generating into {outdir}")
    log(f"  {len(only) if only else len(spec['items'])} item(s) selected of "
        f"{len(spec['items'])} in the batch"
        + (f", by name: {','.join(only)}" if only else ""))
    if a.limit is not None:
        log(f"  --limit {a.limit}: at most {a.limit} picture(s) will be "
            "GENERATED this run. Items already on disk are skipped and do not "
            "count against it.")
    if a.fail_on_blank:
        log("  --fail-on-blank: the first blank or unreadable PNG stops the "
            "run and the exit code is 6.")
    for c in ([f"CPU mode: only {pl['item_limit']} items"] if pl["item_limit"] else []):
        log(f"  CAP: {c}")
    if a.redo:
        log("  --redo: everything is made again, including items already on disk.")
    man = run_batch(exe, ws, pl, spec, outdir, a.max_minutes, log, redo=a.redo,
                    publisher=pub, only=only, limit=a.limit,
                    run_sha=a.run_sha, fail_on_blank=a.fail_on_blank)
    man["downloads"] = fetched
    (outdir / "manifest.json").write_text(json.dumps(man, indent=2) + "\n",
                                          encoding="utf-8")
    write_attribution(outdir, man)

    log("")
    log(f"{man['status']}: {man['items_written']} written, {man['items_skipped']} "
        f"skipped, {man['items_failed']} failed, "
        f"{man['items_attempted']} attempted of {man['items_in_spec']} in the batch")
    bc = man["blank_check"]
    log(f"  blank check: {bc['blank']} blank, {bc['undecodable']} undecodable, of "
        f"{bc['checked']} PNGs decoded ({bc['bound']})")
    # THE SKIP IS ANNOUNCED, ALWAYS, INCLUDING WHEN IT IS ZERO. A silent skip
    # is as bad as the silent overwrite it replaces, and "0 skipped" beside the
    # number rechecked is what stops "nothing was skipped" reading the same as
    # "the skip never ran".
    log(f"  already made: {man['items_skipped']} skipped, {bc['remade']} remade "
        f"because what was on disk was blank or unreadable, of {bc['rechecked']} "
        "PNGs found already on disk")
    if man["items_skipped"]:
        log("  Those files were left exactly as they were - anything you picked "
            "out by hand is safe.")
        log("  To make one again: delete its .png and double-click again. "
            "To make them all again: run with --redo.")
    if bc["blank"]:
        log("  A BLANK IMAGE IS NOT A FAILURE OF YOUR MACHINE. It is "
            "leejet/stable-diffusion.cpp#1031, open, unfixed: Z-Image on Vulkan "
            "can write an empty PNG and exit success. Send this back - the next "
            "thing to try is the ROCm build named in the report.")
    if man["not_attempted"]:
        log(f"  not attempted: {', '.join(man['not_attempted'])}")
    log(f"  images and manifest: {outdir}")
    log("  every image is review=pending until a human has looked at it")
    # THE LAST PICTURES GO FIRST, THEN THE REPORT THAT NAMES THE RESULT.
    # Two publishes on purpose: the report cannot describe a push that has not
    # happened yet, and a report saying "nothing pushed yet" is exactly the
    # kind of stale sentence this paragraph exists to stop. So the images are
    # forced out, the outcome is logged, and only then is the report written
    # and sent - which is why it can say "Sent: N push(es)" truthfully.
    pub.note(outdir / "manifest.json")
    pub.note(outdir / "ATTRIBUTION.json")
    pub.maybe(f"Meridian pictures: {man['items_written']} written, "
              f"{man['items_skipped']} already made", force=True)
    for p in reports:
        p.write_text(format_report(machine, pl, lines[-30:], publisher=pub),
                     encoding="utf-8")
        log(f"report written: {p}")
        pub.note(p)
    pub.maybe("Meridian pictures: the machine report for that run", force=True)
    # A BATCH THAT WAS ALREADY ON DISK IS A SUCCESS, NOT "EVERY IMAGE FAILED".
    # Exit 4 means the setup worked and nothing came out of the generator; a
    # run that skipped twelve good PNGs produced nothing and is entirely fine,
    # and the .bat prints a different paragraph for each.
    # AND THE UNATTENDED LANE'S EXIT CODE, LAST, so every file above is
    # already written and sent before the run reports itself red. 6 is
    # unreachable from either .bat: neither passes --fail-on-blank, and a
    # blank there stays a line in the report rather than a broken window.
    if a.fail_on_blank and (man["blank_check"]["blank"]
                            or man["blank_check"]["undecodable"]):
        log(f"  --fail-on-blank: {man['blank_check']['blank']} blank and "
            f"{man['blank_check']['undecodable']} undecodable of "
            f"{man['blank_check']['checked']} PNG(s) decoded this run. "
            "Exiting 6.")
        return 6
    return 0 if (man["items_written"] or man["items_skipped"]) else 4


if __name__ == "__main__":
    sys.exit(main())
