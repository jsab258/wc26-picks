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

TESTING. Everything that can be tested without a GPU is: `--selftest` runs
plan() across seven synthetic machines, checks the prompt builder refuses to
drop the content rules, round-trips the manifest, and asserts the accepting
case (a good machine plans a real run) FIRST, because the expensive failure
is a planner nothing survives. What CANNOT be tested here is every line that
touches Windows, the network or the GPU. Those are named in the report.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile

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
    # THE GATE, AND WHY THIS URL AND NOT THE OBVIOUS ONE. stable-diffusion.cpp's
    # docs send you to black-forest-labs/FLUX.1-schnell for this file, and that
    # repository is gated behind a Hugging Face login and an acceptance click.
    # We do not use accounts. Comfy-Org/z_image_turbo is the ungated mirror that
    # ComfyUI's own Z-Image template uses, and the autoencoder is Apache-2.0 in
    # both places - so this is a different distributor of the same permissively
    # licensed file, not a way round a licence. Recorded here and in the
    # manifest so nobody has to re-derive it.
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
             "stable-diffusion.cpp runs both; the switch is one field.")

MIN_FREE_DISK_GB = 20


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


def plan(machine):
    """Choose backend, quantisation and runtime flags from the probe.

    Pure function of `machine` so it can be tested without Windows. Every
    branch writes a `reason` into the result: the report prints them, so the
    next run is chosen from what the machine said rather than from what
    somebody assumed it said.
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

    if vendor == "nvidia":
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


def build_prompt(item, rules_clause, style):
    """Positive prompt = style prefix + the item + style suffix + THE RULES.

    The rules clause is appended here and nowhere else, and this function
    refuses to return a prompt without it. `content_rules.rules_clause` is data
    in prompts.json precisely so a later editor adding a thirteenth sign cannot
    forget the one sentence that keeps a real brewery's livery off our pub.
    """
    if not rules_clause or "no trade marks" not in rules_clause:
        raise ValueError("content rules missing or altered: every prompt must "
                         "carry the no-trade-marks / no-real-person clause")
    parts = [style.get("prefix", "").strip(), item["prompt"].strip(),
             style.get("suffix", "").strip(), rules_clause.strip()]
    return ", ".join(p.rstrip(",") for p in parts if p)


def check_forbidden(text, forbidden):
    """A prompt naming a real brand is a bug in the prompt file, not in the run.

    Returns the hits. `len(scanned)` travels with it so a clean result cannot be
    confused with a check that never looked - a zero needs its denominator.
    """
    low = " " + text.lower() + " "
    return [t for t in forbidden if t.lower() in low]


# ---------------------------------------------------------------------------
# REPORT - the file we read to choose the next run.
# ---------------------------------------------------------------------------
def format_report(machine, pl, extra=None):
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
    A(f"probe     {machine.get('probe', 'ok')}")
    A("")
    A("GPUs")
    gpus = normalise_gpus(machine)
    if not gpus:
        A("  NONE FOUND - either there is no display adapter or the probe failed.")
        A("  Those two look identical from here, which is why this line says both.")
    for i, g in enumerate(gpus):
        A(f"  [{i}] {g.get('name', '?')}")
        A(f"      driver {g.get('driver', '?')}   vendor string {g.get('vendor', '?')}")
        A(f"      AdapterRAM {_gb(g.get('vram_bytes')):.2f} GB "
          f"(uint32, saturates at 4.00)")
        A(f"      registry qwMemorySize {_gb(g.get('vram_bytes_registry')):.2f} GB "
          f"(the one to believe)")
    A("")
    A(f"vulkan drivers registered: {machine.get('vulkan_drivers', '?')}")
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
    A(f"  next rung: {NEXT_RUNG}")
    if extra:
        A("")
        A("RUN")
        A("-" * 60)
        for line in extra:
            A(f"  {line}")
    A("")
    A("Send this whole file back. It is what chooses the model for the next run.")
    return "\n".join(L) + "\n"


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
                print(f"\n  {url}\n  HTTP {e.code} - GATED.\n{GATED_NOTE}\n")
                tried.append(f"{url} -> HTTP {e.code} GATED (login/terms required)")
            else:
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
# GENERATE
# ---------------------------------------------------------------------------
def round16(n):
    return max(256, int(round(n / 16.0)) * 16)


def run_batch(exe, ws, pl, spec, outdir, max_minutes, log):
    """Generate the batch. Writes each PNG and rewrites the manifest as it goes,
    so a run killed halfway leaves a truthful record of what it did make rather
    than nothing at all."""
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
    capped = None
    if pl["item_limit"]:
        capped = f"CAP: {pl['item_limit']} of {len(items)} items attempted (CPU mode)"
        items_run = items[:pl["item_limit"]]
    else:
        items_run = items

    manifest = {
        "batch": spec["batch_name"],
        "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "RUNNING",
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
        "caps": [c for c in [capped,
                             f"resolution scaled x{pl['size_scale']}" if pl["size_scale"] != 1 else None,
                             f"wall-clock cap {max_minutes} min"] if c],
        "items_in_spec": len(items),
        "items_attempted": 0, "items_written": 0, "items_failed": 0,
        "not_attempted": [i["id"] for i in items[len(items_run):]],
        "images": [],
    }
    mpath = outdir / "manifest.json"

    def save():
        mpath.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    save()
    t_start = time.time()
    for n, item in enumerate(items_run, 1):
        if (time.time() - t_start) / 60.0 > max_minutes:
            log(f"  STOPPING: wall-clock cap of {max_minutes} min reached after "
                f"{n-1} of {len(items_run)} images. The rest are listed in the "
                f"manifest under not_attempted; re-run to continue.")
            break
        prompt = build_prompt(item, rules, style)
        bad = check_forbidden(prompt, forbidden)
        rec = {"id": item["id"], "kind": item["kind"], "binds_to": item["binds_to"],
               "prompt": prompt, "review": "pending"}
        if bad:
            rec.update(status="REFUSED", why=f"prompt names forbidden mark(s): {bad}")
            manifest["images"].append(rec)
            manifest["items_failed"] += 1
            log(f"  [{n}/{len(items_run)}] REFUSED {item['id']}: {bad}")
            save()
            continue
        w = round16(item["width"] * pl["size_scale"])
        h = round16(item["height"] * pl["size_scale"])
        seed = d["seed_base"] + n
        png = outdir / f"{item['id']}.png"
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
               "--cfg-scale", str(d["cfg"]),
               "--steps", str(d["steps"]),
               "--width", str(w), "--height", str(h),
               "--seed", str(seed), "--output", str(png),
               "--verbose"] + pl["flags"]
        rec.update(width=w, height=h, seed=seed, steps=d["steps"], cfg=d["cfg"],
                   sampler="sd-cli model-specific default (not overridden)",
                   flags=pl["flags"])
        manifest["items_attempted"] += 1
        log(f"  [{n}/{len(items_run)}] {item['id']}  {w}x{h}  seed {seed}")
        t0 = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        dt = time.time() - t0
        rec["seconds"] = round(dt, 1)
        if proc.returncode != 0 or not png.exists():
            tail = (proc.stderr or proc.stdout or "")[-1500:]
            rec.update(status="FAILED", exit_code=proc.returncode, log_tail=tail)
            manifest["images"].append(rec)
            manifest["items_failed"] += 1
            log(f"      FAILED after {dt:.0f}s, exit {proc.returncode}")
            log("      last output from the generator:")
            for line in tail.strip().splitlines()[-12:]:
                log(f"        {line}")
            save()
            if manifest["items_failed"] >= 2 and manifest["items_written"] == 0:
                log("  STOPPING: the first two images both failed and none has "
                    "succeeded. Something is wrong with the runtime or the "
                    "weights, and twelve identical failures help nobody. Send "
                    "back the machine report and this log.")
                break
            continue
        rec.update(status="OK", bytes=png.stat().st_size, sha256=sha256(png),
                   file=png.name)
        manifest["items_written"] += 1
        log(f"      ok  {dt:.0f}s  {png.stat().st_size/1024:.0f} KB")
        if n == 1:
            est = dt * len(items_run) / 60.0
            log(f"      first image took {dt:.0f}s, so the batch projects to "
                f"about {est:.0f} min for {len(items_run)} images")
        manifest["images"].append(rec)
        save()

    # DERIVED, NOT ACCUMULATED. Every break out of the loop above used to have
    # to remember to fill this in, and one of them did not. Reading it off the
    # attempted set makes it true for every exit, including a crash.
    tried = {r["id"] for r in manifest["images"]}
    manifest["not_attempted"] = [i["id"] for i in items if i["id"] not in tried]
    manifest["status"] = ("DONE" if manifest["items_written"] == len(items)
                          else "INCOMPLETE")
    manifest["written"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save()
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
# SELFTEST - accepting case first.
# ---------------------------------------------------------------------------
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
        def __init__(self, rc):
            self.rc = rc

        def __call__(self, cmd, **kw):
            if not self.rc:
                out = pathlib.Path(cmd[cmd.index("--output") + 1])
                out.write_bytes(b"\x89PNG\r\n\x1a\n stub")
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
    finally:
        subprocess.run = real

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
    ap.add_argument("--max-minutes", type=float, default=60.0)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="plan and print the exact commands, download nothing")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    machine = {}
    if a.machine and pathlib.Path(a.machine).exists():
        try:
            machine = json.loads(pathlib.Path(a.machine).read_text(encoding="utf-8-sig"))
        except Exception as e:                                # noqa: BLE001
            machine = {"probe": f"machine.json unreadable: {type(e).__name__}: {e}"}
    else:
        machine = {"probe": f"machine.json missing at {a.machine}"}
    machine.setdefault("python", sys.version.split()[0])

    pl = plan(machine)
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

    outdir = (pathlib.Path(a.out) if a.out else
              (repo / "ledger/Assets/StreamingAssets/Decals/generated" if repo
               else ws / "generated"))

    log(format_report(machine, pl))
    if a.command == "plan" or a.dry_run:
        spec = json.loads((pathlib.Path(__file__).parent / "prompts.json").read_text())
        log("DRY RUN - nothing downloaded. First command would be:")
        it = spec["items"][0]
        log("  sd-cli.exe --diffusion-model " + pl["quant_file"] +
            " --vae ae.safetensors --llm " + TEXT_ENCODER["file"] +
            f" -p \"{build_prompt(it, spec['content_rules']['rules_clause'], spec['style'])[:150]}...\"" +
            f" --cfg-scale 1.0 --steps 8 -W {it['width']} -H {it['height']} " +
            " ".join(pl["flags"]))
        for p in reports:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(format_report(machine, pl, lines[-3:]), encoding="utf-8")
            log(f"report written: {p}")
        return 0

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
        p1, u1 = fetch_one([f"{HF}/leejet/Z-Image-Turbo-GGUF/resolve/main/{q[0]}"],
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
    log("")
    log(f"Generating {len(spec['items'])} images into {outdir}")
    for c in ([f"CPU mode: only {pl['item_limit']} items"] if pl["item_limit"] else []):
        log(f"  CAP: {c}")
    man = run_batch(exe, ws, pl, spec, outdir, a.max_minutes, log)
    man["downloads"] = fetched
    (outdir / "manifest.json").write_text(json.dumps(man, indent=2) + "\n",
                                          encoding="utf-8")
    write_attribution(outdir, man)

    log("")
    log(f"{man['status']}: {man['items_written']} written, {man['items_failed']} failed, "
        f"{man['items_attempted']} attempted of {man['items_in_spec']} in the batch")
    if man["not_attempted"]:
        log(f"  not attempted: {', '.join(man['not_attempted'])}")
    log(f"  images and manifest: {outdir}")
    log("  every image is review=pending until a human has looked at it")
    for p in reports:
        p.write_text(format_report(machine, pl, lines[-30:]), encoding="utf-8")
        log(f"report written: {p}")
    return 0 if man["items_written"] else 4


if __name__ == "__main__":
    sys.exit(main())
