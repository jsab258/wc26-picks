#!/usr/bin/env python3
"""LEDGER prop pipeline - local, unattended, zero Claude tokens.

WHAT THIS IS. Jafar double-clicks "1 MAKE THE PROPS.bat" and walks away. This
script does everything after that: reads the two machine probes, DECIDES which
mesh backend (if any) this PC can actually run, and then grinds a named batch
of prop specs into cleaned, LOD'd, licence-tagged meshes with a manifest. It
never calls a model API, never asks a question, never needs a person. That is
the whole point: the expensive resource is Claude usage, and this converts prop
production into GPU-and-CPU hours on a machine that is otherwise idle.

STDLIB ONLY, ON PURPOSE - same reasoning as imagegen.py. There is no pip step
here. The heavy tools (Blender, and TRELLIS if it can run) are separate
processes this script drives and measures; nothing is installed into Jafar's
Python.

THE THREE STAGES, and which of them can run where:

  1 IMAGE    tools/imagegen (already built, already proven on his RX 6700 -
             14 images, Vulkan, 26 Aug). Only needed by the trellis backend.
  2 MESH     TRELLIS (microsoft/TRELLIS, MIT), image -> 3D. NVIDIA ONLY.
  3 CLEAN    Blender headless: measure, normalise, decimate to an LOD chain,
             export GLB. Vendor-neutral, runs on anything Blender runs on.

THE ANSWER THIS SCRIPT WAS BUILT TO BE ABLE TO GIVE IS "NO". Measured from the
files in this repository rather than assumed: Jafar's PC is an AMD Radeon RX
6700 with 9.98 GB (game-design/agent-reports/machine-report.txt, 26 Aug) and
has no Visual Studio at all (production/d1-probe/ue-machine.txt, 1 Sep).
microsoft/TRELLIS's own README (read 2026-09-01 from raw.githubusercontent)
requires an NVIDIA GPU with at least 16 GB, a CUDA toolkit to compile its
submodules, and ships a bash `setup.sh`; it says "The code is currently tested
only on Linux" and points Windows users at issue #3, "not fully tested". That
is four independent blockers, each sufficient on its own. So the probe below
will say CANNOT RUN on that machine, in those words, naming each one - and it
says it in under a minute having downloaded nothing, because a pipeline that
half-installs a CUDA stack overnight and reports success is the failure this
project has already paid for twice.

WHAT IT CAN DO ON THAT SAME MACHINE TONIGHT is stage 3 over meshes that
already exist: 179 FBX and 37 GLB of CC0 kit sit in ledger/Assets/Props with
no measured bounds, no LODs, no pivot convention and no engine-neutral export,
while D1 has the engine undecided and both candidates want GLB. That batch
needs Blender and nothing else, costs no downloads and no tokens, and is the
`local` backend below.

THE INSTRUMENT DISCIPLINE THIS FILE OWES (CLAUDE.md rules 2, 3b, 5, 5b, 6):
  * Every count ships its denominator. "12 done" is meaningless; "12 done,
    3 failed, 25 not attempted, of 40 in the batch" is a measurement. The
    manifest status is INCOMPLETE unless every item is accounted for.
  * The exit code is not the evidence. Blender exits 0 having written nothing
    at all if a script raises after the export call; every output is opened,
    parsed and measured before it counts as done (`glb_stats`, `mesh_verdict`).
  * The mesh floor was read off a printed series, not invented. `--series`
    over the 37 base-mesh GLBs gave 36..4182 verts and 20..4492 triangles;
    MESH_MIN_VERTS sits at 24, below every real prop in the library, so it can
    only ever catch an empty export. Re-derive it with `--series` rather than
    believing this sentence.
  * Destructive steps scope to exactly what this run produced. Nothing here
    deletes a directory; a redo overwrites named files for one named item.

WHAT CANNOT BE TESTED WHERE THIS WAS WRITTEN, said plainly rather than implied:
there is no GPU, no Blender, no Windows and no PowerShell in this container.
So `--selftest` covers the manifest, the resume, the licence gate, the probe
decisions, the GLB reader and the refusals - with the mesh stage injected as a
fake - and it covers NOT ONE LINE of TRELLIS, Blender or the .bat's control
flow. Those three are UNRUN. The .bat is checked as text only.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import struct
import subprocess
import sys
import time

SPEC_SCHEMA = 1
TOOL_VERSION = "meshgen 1"

# ---------------------------------------------------------------------------
# EXIT CODES. The .bat prints a paragraph per code and the selftest asserts the
# two agree, because a code nobody explains is a window Jafar has to send back.
# ---------------------------------------------------------------------------
EXIT_OK = 0
EXIT_DISK = 2
EXIT_SETUP = 3
EXIT_ALL_FAILED = 4
EXIT_CANNOT_RUN = 5
EXIT_STOPPED = 6
EXIT_LICENCE = 7
EXIT_SPEC = 8

# ---------------------------------------------------------------------------
# THE BOUNDS, AND WHERE EACH NUMBER CAME FROM.
# ---------------------------------------------------------------------------
# From `--series ledger/Assets/Props/base-mesh` over 37 hand-authored CC0 props
# (1 Sep 2026): verts 36 (awning_01) .. 4182 (mesh_bin), triangles 20 .. 4492.
# The floor sits BELOW the smallest real prop on purpose: its job is to catch an
# export that wrote an empty scene, not to judge quality.
MESH_MIN_VERTS = 24
MESH_MIN_TRIS = 12
# Same series: largest real prop 3.31 m (skip), smallest 0.10 m (drain cover).
# A prop outside these is a UNIT error (the classic cm/m and inch/m mixups),
# which is worth catching before anything is placed against it.
MESH_MIN_DIM_M = 0.005
MESH_MAX_DIM_M = 100.0

# TRELLIS's own stated requirement, quoted rather than chosen by us:
# "An NVIDIA GPU with at least 16GB of memory is necessary."
#   - github.com/microsoft/TRELLIS README, read 2026-09-01.
TRELLIS_MIN_VRAM_GB = 16.0
TRELLIS_MIN_DISK_GB = 40.0      # ESTIMATE, labelled: torch+CUDA env plus a
                                # 1.2B model plus build trees. Not measured.
LOCAL_MIN_DISK_GB = 2.0

# ---------------------------------------------------------------------------
# THE LICENCE TABLE. ledger-v2/research/license-allowlist.md is LAW; this is
# that law in a form a program can refuse with, and it points back at the file
# so the two cannot silently disagree - the allowlist stays the source, this
# stays the enforcement.
# ---------------------------------------------------------------------------
ALLOWLIST_DOC = "ledger-v2/research/license-allowlist.md"

TOOLS = {
    # tool key: (display, code licence, weights licence, allowlist line, caveat)
    "blender": ("Blender", "GPL-3.0 (the tool; it places no condition on the "
                "geometry it exports)", "n/a - not a model",
                "not a content source; a processor", ""),
    "trellis": ("TRELLIS (microsoft/TRELLIS)", "MIT (models and the majority "
                "of the code)", "MIT (TRELLIS-image-large)",
                "allowlist SHIP-SAFE 2: TRELLIS/TRELLIS 2 (MIT)",
                # THE CAVEAT IS NOT DECORATION. TRELLIS's README says out loud:
                # "TRELLIS models and the majority of the code are licensed
                # under the MIT License. The following submodules may have
                # different licenses" - naming diffoctreerast (derived from
                # INRIA's diff-gaussian-rasterization) and a modified FlexiCubes
                # (NVIDIA source licence). The allowlist row says "TRELLIS
                # (MIT)" flat. Those are not the same claim, and the mesh
                # extraction path is the one that touches the submodules. This
                # needs a decision record before any TRELLIS output ships;
                # until one exists, `licence_check` marks every trellis row
                # ship_ok=false and says why.
                "MIT covers the models and most code. The README names "
                "submodules under other licences (diffoctreerast, derived from "
                "INRIA diff-gaussian-rasterization; modified FlexiCubes, NVIDIA "
                "source licence). Needs a decision record naming which "
                "submodules the mesh path actually loads before output ships."),
    "imagegen": ("stable-diffusion.cpp + Z-Image-Turbo", "MIT (sd.cpp)",
                 "Apache-2.0 (Z-Image-Turbo weights; outputs unrestricted)",
                 "in use since 25 Aug; manifest at "
                 "ledger/Assets/StreamingAssets/Decals/generated", ""),
    "handmade": ("existing repository asset", "n/a", "n/a",
                 "source's own row in THIRD-PARTY.md", ""),
}

# NEVER SHIP, from the allowlist's own section of that name. A backend or a
# source naming any of these is refused mechanically rather than argued about.
BANNED = {
    "hunyuan3d": "allowlist NEVER SHIP 3: territory-excluded licence (EU/UK/KR)",
    "luma": "allowlist NEVER SHIP 2: Luma Genie outputs",
    "genie": "allowlist NEVER SHIP 2: Luma Genie outputs",
    "meshy": "allowlist SHIP-SAFE 2: paid tiers ONLY, and no purchase is "
             "authorised here - every purchase is Jafar's",
    # THE KEY IS THE WORD ANYBODY WOULD ACTUALLY WRITE. It was "tripo-service",
    # which no spec would ever contain, so the ban could not fire: a rejecting
    # case that rejects nothing. The suffix was presumably guarding "tripod",
    # and banned_hits's word-boundary regex already does that job, checked both
    # ways in the selftest. "TripoSR" (MIT, a different thing from the paid
    # service) does not match either, which is correct and also checked.
    "tripo": "allowlist SHIP-SAFE 2: Tripo paid tiers ONLY, and no "
             "purchase is authorised here",
    "xtts": "allowlist NEVER SHIP 1: non-commercial weights",
    "f5-tts": "allowlist NEVER SHIP 1: non-commercial weights",
    "suno": "allowlist NEVER SHIP 6",
    "udio": "allowlist NEVER SHIP 6",
}

# A licence string on a SOURCE asset must be one we can actually build on.
SOURCE_LICENCES_OK = {"CC0-1.0", "CC-BY-4.0", "CC-BY-3.0", "MIT", "Apache-2.0",
                      "generated - no third-party input"}


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gb(n):
    return round((n or 0) / (1024.0 ** 3), 2)


# ---------------------------------------------------------------------------
# THE GLB READER. Stdlib, no dependencies, and it exists because "Blender
# exited 0" is not evidence that a mesh was written - the same lesson the image
# pipeline learned from stable-diffusion.cpp#1031 writing blank PNGs and
# reporting success.
# ---------------------------------------------------------------------------
def glb_json(path):
    """The JSON chunk of a .glb, or a ValueError saying exactly what is wrong."""
    b = pathlib.Path(path).read_bytes()
    if len(b) < 20:
        raise ValueError(f"only {len(b)} bytes - not a GLB, probably an empty export")
    magic, ver, length = struct.unpack_from("<4sII", b, 0)
    if magic != b"glTF":
        raise ValueError(f"magic is {magic!r}, not b'glTF' - this is not a GLB")
    if ver != 2:
        raise ValueError(f"GLB version {ver}, and this reader speaks version 2")
    if length != len(b):
        raise ValueError(f"header says {length} bytes and the file is {len(b)} - "
                         "TRUNCATED, which is what an interrupted export looks like")
    off, js = 12, None
    while off + 8 <= len(b):
        clen, ctype = struct.unpack_from("<I4s", b, off)
        off += 8
        if off + clen > len(b):
            raise ValueError("a chunk runs past the end of the file - truncated")
        if ctype == b"JSON":
            js = json.loads(b[off:off + clen].decode("utf-8"))
        off += clen
    if js is None:
        raise ValueError("no JSON chunk in the container")
    return js


def _ident():
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def _mul(a, b):
    o = [0.0] * 16
    for r in range(4):
        for c in range(4):
            o[r * 4 + c] = sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4))
    return o


def _node_matrix(n):
    """A node's local transform, row-major.

    glTF stores `matrix` COLUMN-major, so it is transposed on the way in. This
    is not a detail: getting it wrong is silent, because a wrong transpose still
    produces plausible numbers.
    """
    m = n.get("matrix")
    if m and len(m) == 16:
        return [m[0], m[4], m[8], m[12],
                m[1], m[5], m[9], m[13],
                m[2], m[6], m[10], m[14],
                m[3], m[7], m[11], m[15]]
    t = n.get("translation") or [0, 0, 0]
    q = n.get("rotation") or [0, 0, 0, 1]
    s = n.get("scale") or [1, 1, 1]
    x, y, z, w = q
    rot = [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0,
           2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0,
           2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0,
           0, 0, 0, 1]
    scl = [s[0], 0, 0, 0, 0, s[1], 0, 0, 0, 0, s[2], 0, 0, 0, 0, 1]
    tr = [1, 0, 0, t[0], 0, 1, 0, t[1], 0, 0, 1, t[2], 0, 0, 0, 1]
    return _mul(tr, _mul(rot, scl))


def glb_stats(path):
    """Vertices, triangles and WORLD-SPACE bounds of a GLB.

    THE NODE TRANSFORMS ARE THE WHOLE POINT, and skipping them is the trap. The
    first version of this read accessor min/max straight out of the file and
    reported traffic_cone_01.glb as 0.004 x 0.003 x 0.005 metres - because the
    scale lives on the node, not in the buffer. Composed properly it is
    0.401 x 0.450 x 0.347, which is a traffic cone. Fourteen of the 37 files in
    ledger/Assets/Props/base-mesh are affected, so a placement decision taken on
    the naive read would have been wrong by two orders of magnitude on a third
    of the library, and nothing about the number would have looked wrong.

    Returns a dict of statistics OF ONE FILE (not a series, not a peak).
    """
    js = glb_json(path)
    acc = js.get("accessors") or []
    nodes = js.get("nodes") or []
    meshes = js.get("meshes") or []
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    verts = tris = prims = 0
    positioned = 0                # primitives whose POSITION accessor carried
                                  # min/max; the denominator for the bounds

    def walk(i, parent, depth):
        nonlocal verts, tris, prims, positioned
        if depth > 64 or i >= len(nodes):
            return                # a cyclic or malformed graph must not hang
        n = nodes[i]
        m = _mul(parent, _node_matrix(n))
        mi = n.get("mesh")
        if mi is not None and mi < len(meshes):
            for pr in meshes[mi].get("primitives") or []:
                prims += 1
                ai = (pr.get("attributes") or {}).get("POSITION")
                if ai is None or ai >= len(acc):
                    continue
                a = acc[ai]
                verts += int(a.get("count") or 0)
                ii = pr.get("indices")
                if ii is not None and ii < len(acc):
                    tris += int(acc[ii].get("count") or 0) // 3
                mn, mx = a.get("min"), a.get("max")
                if not mn or not mx or len(mn) < 3 or len(mx) < 3:
                    continue
                positioned += 1
                for cx in (mn[0], mx[0]):
                    for cy in (mn[1], mx[1]):
                        for cz in (mn[2], mx[2]):
                            for k, v in enumerate((
                                    m[0] * cx + m[1] * cy + m[2] * cz + m[3],
                                    m[4] * cx + m[5] * cy + m[6] * cz + m[7],
                                    m[8] * cx + m[9] * cy + m[10] * cz + m[11])):
                                lo[k] = min(lo[k], v)
                                hi[k] = max(hi[k], v)
        for c in n.get("children") or []:
            walk(c, m, depth + 1)

    scenes = js.get("scenes") or [{}]
    scene = scenes[js.get("scene", 0)] if js.get("scene", 0) < len(scenes) else scenes[0]
    for r in scene.get("nodes") or []:
        walk(r, _ident(), 0)

    have = positioned > 0
    dims = [round(hi[k] - lo[k], 4) for k in range(3)] if have else None
    return {
        "file": os.path.basename(str(path)),
        "bytes": os.path.getsize(str(path)),
        "verts": verts,
        "tris": tris,
        "primitives": prims,
        "primitives_with_bounds": positioned,   # the denominator for `dims`
        "meshes": len(meshes),
        "nodes": len(nodes),
        "materials": len(js.get("materials") or []),
        "images": len(js.get("images") or []),
        "dims_m": dims,
        "min_m": [round(v, 4) for v in lo] if have else None,
        "max_m": [round(v, 4) for v in hi] if have else None,
        # Pivot convention: base-centred means y_min ~ 0 and x/z centred.
        "base_y": round(lo[1], 4) if have else None,
    }


def mesh_verdict(st):
    """(ok, reason). The artifact check, and it must be able to say both."""
    if st["verts"] < MESH_MIN_VERTS or st["tris"] < MESH_MIN_TRIS:
        return False, (f"degenerate: {st['verts']} verts / {st['tris']} tris, "
                       f"floor is {MESH_MIN_VERTS}/{MESH_MIN_TRIS} (read off the "
                       f"37-file base-mesh series, smallest real prop 36/20)")
    if not st["dims_m"]:
        return False, (f"no POSITION accessor carried min/max over "
                       f"{st['primitives']} primitive(s), so nothing could be "
                       "measured - bounds unknown, not zero")
    biggest = max(st["dims_m"])
    if biggest < MESH_MIN_DIM_M:
        return False, (f"largest dimension {biggest} m is under {MESH_MIN_DIM_M} m "
                       "- a unit error, or an export in millimetres")
    if biggest > MESH_MAX_DIM_M:
        return False, (f"largest dimension {biggest} m is over {MESH_MAX_DIM_M} m "
                       "- a unit error, or an export in centimetres")
    return True, (f"{st['verts']} verts, {st['tris']} tris, "
                  f"{st['dims_m'][0]}x{st['dims_m'][1]}x{st['dims_m'][2]} m")


def series(root):
    """Print the measurement series over every GLB under a directory.

    This is the instrument the floors above were read off. It ships so the
    bound can be re-derived rather than believed - rule 2: print the series,
    look, then set the number.
    """
    root = pathlib.Path(root)
    files = sorted(root.rglob("*.glb"))
    print(f"meshgen --series over {root}")
    if not files:
        print("  NOTHING MEASURED - no .glb files under that directory")
        return 2
    vs, ts, ds, bad = [], [], [], 0
    for p in files:
        try:
            st = glb_stats(p)
        except Exception as e:                                   # noqa: BLE001
            bad += 1
            print(f"  {p.name:36s} UNREADABLE: {e}")
            continue
        ok, why = mesh_verdict(st)
        vs.append(st["verts"])
        ts.append(st["tris"])
        if st["dims_m"]:
            ds.append(max(st["dims_m"]))
        print(f"  {p.name:36s} verts={st['verts']:7d} tris={st['tris']:7d} "
              f"dims={st['dims_m']} base_y={st['base_y']} "
              f"{'ok' if ok else 'REFUSED: ' + why}")

    def summarise(name, xs):
        if not xs:
            print(f"  {name}: NOTHING MEASURED")
            return
        s = sorted(xs)
        print(f"  {name}: n={len(s)} min={s[0]} median={s[len(s) // 2]} max={s[-1]}")

    print(f"\n  {len(files)} file(s) found, {bad} unreadable")
    summarise("verts", vs)
    summarise("tris", ts)
    summarise("largest dimension (m)", ds)
    return 0


# ---------------------------------------------------------------------------
# THE PROBE, AND THE REFUSAL. Both machine files are read here and nowhere
# else: `machine.json` from tools/imagegen/probe-machine.ps1 (GPU, VRAM, RAM,
# disk - reused rather than re-implemented, because a second copy of adapter
# detection is a second copy of its bugs) and `tools.json` from
# tools/meshgen/probe-tools.ps1 (the toolchain this pipeline needs and that one
# does not look for).
# ---------------------------------------------------------------------------
def normalise_gpus(machine):
    """PowerShell 5.1 serialises a one-element array as a bare object, so a
    machine with a single card reads as a dict. imagegen.py hit this exact
    thing; normalise once, drop anything that is not a mapping."""
    g = machine.get("gpus")
    if isinstance(g, dict):
        g = [g]
    elif not isinstance(g, list):
        g = []
    return [x for x in g if isinstance(x, dict)]


def vram_gb(machine):
    """(gb, source, known). The registry figure wins where it exists.

    Win32_VideoController.AdapterRAM is a uint32 and saturates at 4 GB, so a
    reading of exactly 4294967295 is NOT a 4 GB card, it is a card too big to
    measure that way - and treating it as 4 GB would be a measurement invented
    out of an overflow. Same rule imagegen.py applies, same reason.
    """
    best, src = 0, "none"
    for g in normalise_gpus(machine):
        for key in ("vram_bytes_registry", "vram_bytes"):
            v = g.get(key) or 0
            if v > best:
                best, src = v, key
    if src == "vram_bytes" and abs(best - 4294967295) < 4096:
        return 0.0, "AdapterRAM uint32 ceiling - NOT a measurement", False
    if best == 0:
        return 0.0, "no VRAM figure from any source", False
    return gb(best), src, True


def nvidia_gpu(machine):
    """The NVIDIA adapter, or None. Named rather than a boolean so the report
    can print WHICH card answered."""
    for g in normalise_gpus(machine):
        n = (g.get("name") or "").lower()
        if any(t in n for t in ("nvidia", "geforce", "quadro", "rtx", "tesla")):
            return g
    return None


def req(what, need, found, ok, fix=""):
    return {"what": what, "need": need, "found": found, "ok": bool(ok), "fix": fix}


def probe(machine, tools):
    """Which backends can run on THIS machine, and for each requirement that
    fails, what is missing and what would fix it.

    Pure function of the two probe files, so every branch is testable without
    Windows. Nothing here downloads, installs or writes.
    """
    tools = tools or {}
    gpus = normalise_gpus(machine)
    vg, vsrc, vknown = vram_gb(machine)
    nv = nvidia_gpu(machine)
    free = gb(machine.get("free_disk_bytes"))
    probe_read = bool(machine.get("probe_file_read"))
    tools_read = bool(tools.get("probe_file_read"))

    trellis = [
        req("an NVIDIA GPU", "NVIDIA adapter (TRELLIS is CUDA-only)",
            (nv or {}).get("name") or (f"{len(gpus)} adapter(s), none NVIDIA: "
                                       + ", ".join((g.get('name') or '?') for g in gpus)
                                       if gpus else "no adapter found by the probe"),
            nv is not None,
            "an NVIDIA card, or a different backend. There is no CUDA on AMD, "
            "and TRELLIS's kernels are CUDA."),
        req("VRAM", f"at least {TRELLIS_MIN_VRAM_GB:.0f} GB (TRELLIS README, "
            "read 2026-09-01: 'An NVIDIA GPU with at least 16GB of memory is "
            "necessary')",
            f"{vg:.2f} GB from {vsrc}" if vknown else f"UNKNOWN ({vsrc})",
            vknown and vg >= TRELLIS_MIN_VRAM_GB,
            "a bigger card. This bound is upstream's number, not ours - we have "
            "measured nothing below it because we cannot."),
        req("CUDA toolkit", "nvcc on PATH (TRELLIS compiles submodules)",
            tools.get("nvcc") or "not found", bool(tools.get("nvcc")),
            "install the CUDA Toolkit (11.8 or 12.2 are the tested versions)"),
        req("C++ compiler", "MSVC (cl.exe) to build the CUDA submodules on "
            "Windows",
            tools.get("msvc") or "not found", bool(tools.get("msvc")),
            "Visual Studio Build Tools with the C++ workload. "
            "production/d1-probe/ue-machine-read.md records this same gap "
            "blocking the UE C++ half, so it is one install for two problems."),
        req("a POSIX shell", "bash, because TRELLIS ships setup.sh and the "
            "README says 'The code is currently tested only on Linux'; Windows "
            "is issue #3, 'not fully tested'",
            tools.get("bash") or "not found", bool(tools.get("bash")),
            "Git for Windows provides bash. Note that this requirement is a "
            "warning about the whole route, not a missing binary: nobody here "
            "has run TRELLIS on Windows and upstream does not claim it works."),
        req("python 3.8+", "for the trellis environment",
            tools.get("python_version") or "not found",
            _ver_at_least(tools.get("python_version"), (3, 8)),
            "any Python 3.8 or newer"),
        req("git", "clone --recurse-submodules",
            tools.get("git") or "not found", bool(tools.get("git")), "install git"),
        req("free disk", f"about {TRELLIS_MIN_DISK_GB:.0f} GB (ESTIMATE, not "
            "measured: torch+CUDA env, a 1.2B model, build trees)",
            f"{free:.1f} GB on {machine.get('disk_letter') or '?'}",
            free >= TRELLIS_MIN_DISK_GB,
            "free some space, or point the workspace at another drive"),
    ]
    local = [
        req("Blender", "blender on PATH or in a standard install location",
            tools.get("blender") or "not found", bool(tools.get("blender")),
            "install Blender from blender.org - free, no account, GPL. It is "
            "the only thing this backend needs."),
        req("free disk", f"{LOCAL_MIN_DISK_GB:.0f} GB for the exports",
            f"{free:.1f} GB on {machine.get('disk_letter') or '?'}",
            free >= LOCAL_MIN_DISK_GB, "free some space"),
    ]
    out = {
        "machine_read": probe_read,
        "tools_read": tools_read,
        "vram_gb": vg,
        "vram_known": vknown,
        "vram_source": vsrc,
        "adapters": len(gpus),
        "adapter_names": [g.get("name") for g in gpus],
        "gpu_sources_tried": machine.get("gpu_sources_tried") or "NONE RECORDED",
        "free_disk_gb": free,
        "backends": {
            "trellis": {"reqs": trellis, "ok": all(r["ok"] for r in trellis)},
            "local": {"reqs": local, "ok": all(r["ok"] for r in local)},
        },
    }
    # A PROBE THAT NEVER RAN IS NOT A MACHINE WITH NOTHING ON IT. Both files
    # missing means every requirement above reads "not found" for the same
    # uninformative reason, and refusing on that would be refusing on an
    # absence of evidence. It still refuses - but it says WHICH.
    if not probe_read or not tools_read:
        for b in out["backends"].values():
            b["ok"] = False
        out["unmeasured"] = ("the machine probe did not run"
                             if not probe_read else "") + \
                            ("" if tools_read else
                             ("; " if not probe_read else "") +
                             "the toolchain probe did not run")
    return out


def _ver_at_least(s, want):
    if not s:
        return False
    m = re.match(r"(\d+)\.(\d+)", str(s))
    return bool(m) and (int(m.group(1)), int(m.group(2))) >= want


def choose_backend(pr, asked):
    """(backend, why). `asked` comes from the spec, never from a guess.

    It does NOT silently fall back from trellis to local: those two backends
    make different things out of different inputs, and quietly making the other
    one is how a run reports success for work nobody asked for.
    """
    b = pr["backends"].get(asked)
    if b is None:
        return None, f"the spec asks for backend {asked!r}, which does not exist"
    if b["ok"]:
        return asked, f"backend {asked} has everything it needs"
    missing = [r["what"] for r in b["reqs"] if not r["ok"]]
    return None, (f"backend {asked} CANNOT RUN on this machine: missing "
                  + ", ".join(missing))


def format_probe_report(machine, tools, pr, spec=None, extra=None):
    """The report file. Written to the repository, not just the console -
    a console this environment cannot read is not a channel (rule 12)."""
    L = []
    a = L.append
    a("LEDGER - prop pipeline (meshgen), machine report")
    a("=" * 64)
    # THE MARKER GOES FIRST, like `NO PLAYER LOG` in the sim verdict. A report
    # written where no probe ran describes NOTHING, and the one way that costs
    # a morning is somebody reading it later as evidence about a real machine.
    if pr.get("unmeasured"):
        a("NO PROBE DATA - " + pr["unmeasured"] + ".")
        a("Nothing below describes a real machine. This file is evidence that "
          "the probe did not run, and evidence of nothing else.")
        a("=" * 64)
    a(f"written   {utcnow()}")
    a(f"host      {machine.get('hostname') or 'unknown'}")
    a(f"os        {machine.get('os') or 'unknown'}  ({machine.get('os_build') or '?'})")
    a(f"cpu       {machine.get('cpu') or 'unknown'}  x{machine.get('cpu_cores') or '?'} cores")
    a(f"ram       {gb(machine.get('ram_bytes')):.1f} GB")
    a(f"free disk {pr['free_disk_gb']:.1f} GB on {machine.get('disk_letter') or '?'}")
    a(f"machine probe read: {pr['machine_read']}   toolchain probe read: {pr['tools_read']}")
    if pr.get("unmeasured"):
        a(f"  NOT MEASURED: {pr['unmeasured']} - every 'not found' below may mean "
          "'nobody looked'")
    a("")
    a(f"GPUs   {pr['adapters']} found  (sources tried: {pr['gpu_sources_tried']})")
    for n in pr["adapter_names"]:
        a(f"  - {n}")
    a(f"vram   {pr['vram_gb']:.2f} GB from {pr['vram_source']} "
      f"(known: {pr['vram_known']})")
    a("")
    a("TOOLCHAIN")
    a("-" * 64)
    for k in ("blender", "blender_version", "python", "python_version", "conda",
              "nvcc", "cuda_version", "msvc", "bash", "git", "nvidia_smi",
              "torch", "torch_cuda"):
        if k in (tools or {}):
            a(f"  {k:16s} {tools.get(k)}")
    if tools and tools.get("notes"):
        for n in (tools["notes"] if isinstance(tools["notes"], list) else [tools["notes"]]):
            a(f"  note: {n}")
    a("")
    a("CAN THIS MACHINE RUN IT?")
    a("-" * 64)
    for name, b in sorted(pr["backends"].items()):
        good = sum(1 for r in b["reqs"] if r["ok"])
        a(f"  backend {name}: {'YES' if b['ok'] else 'NO'}  "
          f"({good} of {len(b['reqs'])} requirements met)")
        for r in b["reqs"]:
            a(f"      [{'ok ' if r['ok'] else 'NO '}] {r['what']}")
            a(f"            need : {r['need']}")
            a(f"            found: {r['found']}")
            if not r["ok"] and r["fix"]:
                a(f"            fix  : {r['fix']}")
        a("")
    if spec:
        a(f"BATCH     {spec.get('batch_name')} - {len(spec.get('items') or [])} item(s), "
          f"backend {spec.get('backend')}")
    a(f"LICENCE   every output carries tool, weights licence and source "
      f"provenance; the law is {ALLOWLIST_DOC}")
    for line in (extra or []):
        a(str(line))
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# THE SPEC
# ---------------------------------------------------------------------------
def validate_spec(spec, repo=None):
    """Everything wrong with a batch spec, as plain sentences. Empty = valid.

    Runs before anything is made, because a typo should cost a printed line and
    not four hours of a machine's night.
    """
    p = []
    if spec.get("schema") != SPEC_SCHEMA:
        p.append(f"spec says schema {spec.get('schema')!r} and this meshgen speaks "
                 f"{SPEC_SCHEMA}. They came from different commits - pull again.")
        return p
    if not spec.get("batch_name"):
        p.append("no batch_name, so the manifest could not name itself.")
    backend = spec.get("backend")
    if backend not in ("local", "trellis"):
        p.append(f"backend {backend!r} is not one of local, trellis.")
    items = spec.get("items") or []
    if not items:
        p.append("the spec lists no items at all.")
    seen = set()
    for i, it in enumerate(items):
        who = it.get("id") or f"item {i} (which has no id)"
        for f in ("id", "category", "source"):
            if not it.get(f):
                p.append(f"{who}: no {f}.")
        if it.get("id") in seen:
            p.append(f"{who}: two items share this id, so one would overwrite "
                     "the other's mesh.")
        seen.add(it.get("id"))
        if it.get("id") and not re.fullmatch(r"[a-z0-9_]+", str(it["id"])):
            p.append(f"{who}: id must be lower case, digits and underscores - it "
                     "becomes a directory name and a Unity/Unreal asset name.")
        src = it.get("source") or {}
        kind = src.get("kind")
        if backend == "local" and kind != "file":
            p.append(f"{who}: backend local needs source.kind 'file', got {kind!r}.")
        if backend == "trellis" and kind != "image":
            p.append(f"{who}: backend trellis needs source.kind 'image', got {kind!r}.")
        if kind == "file":
            if not src.get("path"):
                p.append(f"{who}: source.kind file with no path.")
            elif repo and not (pathlib.Path(repo) / src["path"]).exists():
                p.append(f"{who}: source file does not exist: {src['path']}")
            if src.get("licence") not in SOURCE_LICENCES_OK:
                p.append(f"{who}: source licence {src.get('licence')!r} is not one "
                         f"this pipeline will build on. {ALLOWLIST_DOC} is the law.")
            if not src.get("credit"):
                p.append(f"{who}: no source.credit. CC0 needs no credit by law and "
                         "gets one anyway - that is the project's rule.")
        if kind == "image":
            if not src.get("image_id"):
                p.append(f"{who}: source.kind image with no image_id naming the "
                         "imagegen item that makes it.")
            # A GENERATED MESH HAS NO SCALE UNTIL SOMEBODY GIVES IT ONE.
            # TRELLIS normalises its output into a unit cube, so an item with
            # no target height would export a prop of arbitrary size and every
            # measurement downstream would be measuring the normalisation.
            if not it.get("target_height_m"):
                p.append(f"{who}: backend trellis needs target_height_m - its "
                         "output is normalised into a unit cube and has no "
                         "real-world size at all until one is stated.")
        h = it.get("target_height_m")
        if h is not None and not (MESH_MIN_DIM_M <= float(h) <= MESH_MAX_DIM_M):
            p.append(f"{who}: target_height_m {h} is outside "
                     f"{MESH_MIN_DIM_M}..{MESH_MAX_DIM_M} m.")
        for name, ratio in (it.get("lods") or spec.get("default_lods") or {}).items():
            if not (0 < float(ratio) <= 1.0):
                p.append(f"{who}: LOD {name} ratio {ratio} must be in (0, 1].")
    banned = banned_hits(json.dumps(spec).lower())
    for b, why in banned:
        p.append(f"the spec names {b!r}: {why}")
    return p


def banned_hits(text):
    """Banned tools named in a blob of text, matched on WORD BOUNDARIES.

    The first version used `in`, and the selftest caught it on the shipped
    trellis spec: the word "studio" contains "udio", so a batch was refused for
    naming a music service it does not mention. That is the same fault as the
    CS0426 lint that flagged thirteen call sites which compile perfectly - a
    name-matching check needs boundaries or it is a rejecting case that fires
    on the accepting one.
    """
    low = text.lower()
    hits = []
    for b, why in sorted(BANNED.items()):
        if re.search(r"(?<![a-z0-9])" + re.escape(b) + r"(?![a-z0-9])", low):
            hits.append((b, why))
    return hits


def recipe_of(item, spec, backend, tool_versions):
    """The fingerprint that decides SKIP or REDO on the next run.

    It hashes WHAT THE PIPELINE CONSUMED: the item as written, the LOD ladder,
    the backend, and the versions of the tools that did the work. A Blender
    upgrade therefore redoes the batch, which is correct - the output is not
    the same output.
    """
    payload = {
        "item": item,
        "backend": backend,
        "lods": item.get("lods") or spec.get("default_lods"),
        "tools": tool_versions,
        "meshgen": TOOL_VERSION,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# THE LICENCE GATE. Untagged output fails. This is the allowlist's PROCESS
# clause 1 made mechanical: "Every asset and generated output carries a license
# tag; untagged fails the license gate."
# ---------------------------------------------------------------------------
LICENCE_FIELDS = ("tool", "tool_licence", "weights_licence", "source",
                  "source_licence", "source_credit", "output_licence",
                  "produced", "allowlist")


def licence_row(item, spec, backend, tool_versions, decision_records):
    """The tag that ships with one output. Written by the same code that writes
    the mesh, so the two cannot drift apart."""
    src = item.get("source") or {}
    if backend == "local":
        tool_key = "handmade"
        chain = [TOOLS["handmade"], TOOLS["blender"]]
        source = src.get("path", "")
        source_licence = src.get("licence", "")
        credit = src.get("credit", "")
        out_lic = (f"derivative of {source_licence} source; the source's "
                   "obligation travels with it")
    else:
        tool_key = "trellis"
        chain = [TOOLS["imagegen"], TOOLS["trellis"], TOOLS["blender"]]
        source = f"imagegen item {src.get('image_id', '')}"
        source_licence = "generated - no third-party input"
        credit = "generated by tools/imagegen (Z-Image-Turbo, Apache-2.0)"
        out_lic = ("project-owned geometry; model weights permissive, outputs "
                   "unrestricted by the weights licence")
    caveats = [c for (_d, _c, _w, _a, c) in chain if c]
    row = {
        "tool": " -> ".join(d for (d, _c, _w, _a, _v) in chain),
        "tool_licence": "; ".join(f"{d}: {c}" for (d, c, _w, _a, _v) in chain),
        "weights_licence": "; ".join(f"{d}: {w}" for (d, _c, w, _a, _v) in chain),
        "source": source,
        "source_licence": source_licence,
        "source_credit": credit,
        "output_licence": out_lic,
        "produced": utcnow(),
        "allowlist": TOOLS[tool_key][3] + f" (law: {ALLOWLIST_DOC})",
        "tool_versions": tool_versions,
        "caveats": caveats,
    }
    # SHIPPABLE IS NOT THE SAME FACT AS PRODUCED. A caveat with no decision
    # record behind it means the file may exist and may not ship, and the
    # manifest says which - rather than a person discovering it at release.
    if caveats and not decision_records.get(tool_key):
        row["ship_ok"] = False
        row["ship_blocked_by"] = (
            f"{TOOLS[tool_key][0]} carries a licence caveat and no decision "
            f"record authorises it. The allowlist's PROCESS clause 2 requires "
            f"one: 'New tool adoption requires a decision record citing the "
            f"weights license.' To authorise it, a decision record must carry "
            f"the line '{DECISION_MARKER} {tool_key}' alone, at the start of a "
            f"line. Mentioning the tool is not authorising it.")
    else:
        row["ship_ok"] = True
    return row


# THE AUTHORISATION MARKER. A document that MENTIONS a tool and a document
# that AUTHORISES it are different things and must stop looking alike, so the
# test is a literal marker somebody typed on purpose, not prose about the tool
# sitting near the word licence.
#
# The version this replaces was `if key in t and "licen" in t`, and it was
# defeated by the DIRECTOR'S REVIEW OF THIS PIPELINE: that document discusses
# trellis and licences at length, so the moment it landed the gate would have
# read it as authorisation and flipped every TRELLIS output to ship_ok=true
# with no real record ever written. A gate that its own review paperwork
# satisfies is worse than no gate.
#
# WHY THE MARKER IS ANCHORED TO A WHOLE LINE, which is the part that is easy
# to get wrong twice: that same ruling contains the string
# "TOOL-DECISION: trellis" inside a sentence explaining the format, in
# backticks, mid-line. A plain substring test would therefore have been
# defeated by the same document as the prose test it replaced. So the marker
# must be the entire line, starting at column 0, and fenced code blocks are
# removed before matching - an EXAMPLE of the marker is not the marker.
DECISION_MARKER = "TOOL-DECISION:"
DECISION_GLOBS = ["ledger-v2/respec/decision-register/*.md",
                  "game-design/decision-*.md", "production/specs/decision-*.md"]
DECISION_MARKER_RE = re.compile(
    r"^TOOL-DECISION:[ \t]+([A-Za-z0-9][A-Za-z0-9._-]*)[ \t]*$", re.MULTILINE)
_FENCE_RE = re.compile(r"^[ \t]*(?:```|~~~).*?(?:^[ \t]*(?:```|~~~)[ \t]*$|\Z)",
                       re.MULTILINE | re.DOTALL)


def find_decision_records(repo):
    """Which tools a decision record AUTHORISES: {tool key: path to the record}.

    The test is the literal line `TOOL-DECISION: <tool>` and nothing else, so
    that neither "we decided that at some point" nor a document that merely
    discusses the tool can stand in for a record. See DECISION_MARKER_RE above
    for why it is anchored to a whole line rather than matched as a substring.

    An unrecognised tool name is KEPT rather than dropped: a marker with a typo
    in it should show up in the manifest as a record for something nobody has
    heard of, not read as no record at all.
    """
    out = {}
    if not repo:
        return out
    repo = pathlib.Path(repo)
    for g in DECISION_GLOBS:
        for p in sorted(repo.glob(g)):        # sorted: first record wins, stably
            try:
                t = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in DECISION_MARKER_RE.finditer(_FENCE_RE.sub("", t)):
                out.setdefault(m.group(1).lower(), str(p.relative_to(repo)))
    return out


def licence_check(manifest):
    """(problems, caveats, examined). Problems are refusals; caveats are named
    and counted. The denominator ships with both."""
    problems, caveats = [], []
    rows = manifest.get("items") or []
    examined = 0
    for r in rows:
        if r.get("status") != "done":
            continue
        examined += 1
        lic = r.get("licence") or {}
        missing = [f for f in LICENCE_FIELDS if not lic.get(f)]
        if missing:
            problems.append(f"{r.get('id')}: UNTAGGED - missing {', '.join(missing)}")
            continue
        hits = banned_hits(json.dumps(lic))
        for b, why in hits:
            problems.append(f"{r.get('id')}: names a banned tool/source {b!r}: {why}")
        if lic.get("source_licence") not in SOURCE_LICENCES_OK:
            problems.append(f"{r.get('id')}: source licence "
                            f"{lic.get('source_licence')!r} is not on the allowlist")
        if not lic.get("ship_ok"):
            caveats.append(f"{r.get('id')}: {lic.get('ship_blocked_by') or 'ship_ok false'}")
    return problems, caveats, examined


# ---------------------------------------------------------------------------
# THE STAGES. Each is a function of (item, paths) returning a dict, and each is
# INJECTABLE so the batch loop can be tested here with the GPU and Blender
# faked. The real ones drive external processes and cannot run in this
# container - that is stated in the module docstring and in the selftest
# output, not implied.
# ---------------------------------------------------------------------------
class StageError(Exception):
    """A stage that failed for a reason worth printing. Carries the reason."""


def _run(cmd, timeout, log, label):
    """Run a child process and return (rc, tail). The tail is kept because a
    tool's own last words are the diagnosis; the exit code rarely is."""
    log(f"      $ {' '.join(str(c) for c in cmd)}")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as e:
        raise StageError(f"{label}: executable not found ({e})")
    except subprocess.TimeoutExpired:
        raise StageError(f"{label}: still running after {timeout}s - killed. "
                         "A hung stage is a night with nothing in it.")
    tail = "\n".join((p.stdout or "").splitlines()[-12:] +
                     (p.stderr or "").splitlines()[-12:])
    return p.returncode, tail


def blender_clean(item, spec, src_path, item_dir, tools, log, timeout=1800):
    """Stage 3: Blender headless. Import, measure, normalise, decimate, export.

    THE EXIT CODE IS NOT THE EVIDENCE. Blender exits 0 when a Python script
    raises after the last import, and it exits 0 having written nothing when a
    file it was pointed at contained no mesh. So this reads the result JSON the
    script writes and the caller measures every GLB afterwards.
    """
    blender = tools.get("blender")
    if not blender:
        raise StageError("Blender is not on this machine - the local backend "
                         "cannot run. Install it from blender.org (free, no "
                         "account) and click again.")
    script = pathlib.Path(__file__).parent / "blender" / "clean_lod.py"
    result = item_dir / "blender-result.json"
    lods = item.get("lods") or spec.get("default_lods") or {"LOD0": 1.0}
    cmd = [blender, "--background", "--factory-startup", "--python", str(script),
           "--", "--in", str(src_path), "--out-dir", str(item_dir),
           "--id", str(item["id"]),
           "--lods", ",".join(f"{k}={v}" for k, v in sorted(lods.items())),
           "--result", str(result)]
    if item.get("target_height_m"):
        cmd += ["--target-height", str(item["target_height_m"])]
    if item.get("pivot", spec.get("default_pivot", "base-centre")):
        cmd += ["--pivot", str(item.get("pivot", spec.get("default_pivot",
                                                          "base-centre")))]
    rc, tail = _run(cmd, timeout, log, "blender")
    if not result.exists():
        raise StageError(f"blender exited {rc} and wrote no result file. "
                         f"Its last words:\n{tail}")
    data = json.loads(result.read_text(encoding="utf-8"))
    if not data.get("ok"):
        raise StageError(f"blender reported: {data.get('error')}")
    return data


def trellis_mesh(item, spec, image_path, item_dir, ws, tools, log, timeout=3600):
    """Stage 2: image -> mesh, TRELLIS, local, MIT.

    UNRUN. Not one line of this has executed anywhere: no machine reachable
    from here has an NVIDIA GPU, and the probe refuses the backend before this
    is ever called. It is written so the route EXISTS the day a qualifying
    machine does, and it is deliberately thin - it drives a runner script
    inside the TRELLIS environment rather than reimplementing the pipeline.

    It also does NOT install TRELLIS. An unattended CUDA-extension build that
    half succeeds is the exact "reports success while broken" failure this
    project keeps paying for; the probe says what is missing, the README says
    how to install it, and the install is a decision with a person present.
    """
    root = ws / "TRELLIS"
    runner = root / "ledger_runner.py"
    if not runner.exists():
        raise StageError(
            f"TRELLIS is not installed at {root}. This pipeline does not "
            "install it: it is a conda environment plus CUDA submodules that "
            "must be COMPILED, and an unattended build that half works is "
            "worse than none. See tools/meshgen/README.md, which names every "
            "step and quotes upstream's own Linux-only warning.")
    py = tools.get("trellis_python") or tools.get("python") or sys.executable
    out = item_dir / f"{item['id']}_raw.glb"
    cmd = [py, str(runner), "--image", str(image_path), "--out", str(out),
           "--seed", str(item.get("seed", 0))]
    rc, tail = _run(cmd, timeout, log, "trellis")
    if rc != 0 or not out.exists():
        raise StageError(f"trellis exited {rc} and left no mesh at {out}. "
                         f"Its last words:\n{tail}")
    return {"raw": str(out)}


def imagegen_image(item, spec, images_dir, repo, tools, log, timeout=3600):
    """Stage 1: the reference image, delegated to the pipeline that already
    exists and already works on this machine (14 images, Vulkan, 26 Aug).

    It is a DELEGATION and not a second implementation on purpose: the content
    rules (no real marks, no real faces), the blank-image check and the resume
    all live in imagegen.py and have 83 tests. A copy of them here would be a
    second place for them to be wrong.
    """
    src = item.get("source") or {}
    want = images_dir / f"{src.get('image_id')}.png"
    if want.exists():
        return {"image": str(want), "made": False}
    ig = pathlib.Path(repo) / "tools" / "imagegen" / "imagegen.py"
    spec_file = pathlib.Path(repo) / (spec.get("image_spec") or "")
    if not ig.exists() or not spec_file.exists():
        raise StageError(f"no image at {want} and imagegen could not be run "
                         f"(imagegen.py: {ig.exists()}, image spec "
                         f"{spec.get('image_spec')}: {spec_file.exists()})")
    py = tools.get("python") or sys.executable
    cmd = [py, str(ig), "all", "--spec", str(spec_file), "--out", str(images_dir),
           "--no-send"]
    rc, tail = _run(cmd, timeout, log, "imagegen")
    if not want.exists():
        raise StageError(f"imagegen exited {rc} and there is still no image at "
                         f"{want}. Its last words:\n{tail}")
    return {"image": str(want), "made": True}


# ---------------------------------------------------------------------------
# THE BATCH
# ---------------------------------------------------------------------------
def stop_file(repo, ws):
    """The kill switch, matching production/STOP in the night runner: one file,
    one meaning, checked between every item and every stage."""
    if repo and (pathlib.Path(repo) / "production" / "STOP").exists():
        return str(pathlib.Path(repo) / "production" / "STOP")
    if ws and (pathlib.Path(ws) / "STOP").exists():
        return str(pathlib.Path(ws) / "STOP")
    return None


def outputs_ok(row, outdir):
    """Is this item's work actually on disk and actually a mesh?

    The resume rule opens every file it is about to skip. A manifest row saying
    'done' beside a truncated GLB is exactly the state an interrupted run
    leaves behind, and trusting the row would make the interruption permanent
    and invisible.
    """
    files = (row.get("outputs") or {})
    if not files:
        return False, "no outputs recorded"
    for name, rel in sorted(files.items()):
        p = outdir / rel
        if not p.exists():
            return False, f"{name} missing at {rel}"
        try:
            st = glb_stats(p)
        except Exception as e:                                   # noqa: BLE001
            return False, f"{name} unreadable: {e}"
        ok, why = mesh_verdict(st)
        if not ok:
            return False, f"{name} {why}"
    return True, f"{len(files)} output(s) on disk and measured"


def run_batch(spec, backend, outdir, ws, repo, tools, log, *, max_minutes=480.0,
              redo=False, stages=None, decision_records=None, now=time.time):
    """The loop. Resumable, interruptible, and it counts everything.

    THE MANIFEST IS WRITTEN AFTER EVERY ITEM, not at the end. A run that is
    killed at item 12 of 40 must leave a manifest saying 12, and a manifest
    written once at the end says nothing at all about the run that mattered.
    """
    stages = stages or {}
    do_image = stages.get("image", imagegen_image)
    do_mesh = stages.get("mesh", trellis_mesh)
    do_clean = stages.get("clean", blender_clean)
    decision_records = decision_records if decision_records is not None else \
        find_decision_records(repo)
    items = spec.get("items") or []
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    ws = pathlib.Path(ws) if ws else outdir
    images_dir = pathlib.Path(spec.get("images_dir") or (ws / "images"))
    tool_versions = {k: tools.get(k + "_version") or tools.get(k)
                     for k in ("blender", "python") if tools.get(k)}
    tool_versions["backend"] = backend

    previous = {}
    man_path = outdir / "manifest.json"
    if man_path.exists():
        try:
            for r in (json.loads(man_path.read_text(encoding="utf-8")).get("items") or []):
                previous[r.get("id")] = r
        except Exception as e:                                   # noqa: BLE001
            log(f"  the previous manifest could not be read ({e}) - every item "
                "will be re-verified from its files rather than from the row")

    man = {
        "schema": SPEC_SCHEMA,
        "batch": spec.get("batch_name"),
        "backend": backend,
        "written": utcnow(),
        "meshgen": TOOL_VERSION,
        "tool_versions": tool_versions,
        "allowlist": ALLOWLIST_DOC,
        "decision_records": decision_records,
        "items_in_spec": len(items),
        "items": [],
        "counts": {},
        "caps": [],
    }
    started = now()
    deadline = started + max_minutes * 60.0
    done = skipped = failed = 0
    stopped = None
    attempted = 0

    for idx, item in enumerate(items):
        sf = stop_file(repo, ws)
        if sf:
            stopped = f"the kill switch {sf} exists"
            break
        if now() > deadline:
            stopped = (f"the wall-clock cap of {max_minutes:g} minutes was "
                       "reached")
            break
        iid = item["id"]
        item_dir = outdir / iid
        recipe = recipe_of(item, spec, backend, tool_versions)
        prev = previous.get(iid)
        if prev and not redo and prev.get("recipe") == recipe:
            ok, why = outputs_ok(prev, outdir)
            if ok:
                log(f"  [{idx + 1}/{len(items)}] {iid}: SKIPPED - {why}")
                row = dict(prev)
                row["status"] = "done"
                row["skipped_on"] = utcnow()
                man["items"].append(row)
                skipped += 1
                _write_manifest(man, man_path, spec, done, skipped, failed,
                                attempted, stopped, started, now)
                continue
            log(f"  [{idx + 1}/{len(items)}] {iid}: redoing - {why}")
        elif prev and prev.get("recipe") != recipe and not redo:
            log(f"  [{idx + 1}/{len(items)}] {iid}: redoing - the recipe changed "
                f"({prev.get('recipe')} -> {recipe})")

        attempted += 1
        row = {"id": iid, "category": item.get("category"), "recipe": recipe,
               "started": utcnow(), "stages": {}}
        try:
            item_dir.mkdir(parents=True, exist_ok=True)
            if backend == "trellis":
                img = do_image(item, spec, images_dir, repo, tools, log)
                row["stages"]["image"] = img
                if stop_file(repo, ws):
                    raise StageError("stopped by the kill switch between stages")
                raw = do_mesh(item, spec, pathlib.Path(img["image"]), item_dir,
                              ws, tools, log)
                row["stages"]["mesh"] = raw
                src_path = pathlib.Path(raw["raw"])
            else:
                src_path = pathlib.Path(repo or ".") / item["source"]["path"]
                if not src_path.exists():
                    raise StageError(f"source file not found: {src_path}")
                row["stages"]["source"] = {"path": str(item["source"]["path"]),
                                           "bytes": src_path.stat().st_size}
            if stop_file(repo, ws):
                raise StageError("stopped by the kill switch between stages")
            cleaned = do_clean(item, spec, src_path, item_dir, tools, log)
            row["stages"]["clean"] = {k: v for k, v in cleaned.items()
                                      if k != "outputs"}
            outputs = cleaned.get("outputs") or {}
            if not outputs:
                raise StageError("the clean stage reported success and named no "
                                 "output files")
            measured, rel_outputs = {}, {}
            for name, p in sorted(outputs.items()):
                p = pathlib.Path(p)
                st = glb_stats(p)
                ok, why = mesh_verdict(st)
                if not ok:
                    raise StageError(f"{name}: {why}")
                measured[name] = st
                rel_outputs[name] = str(p.relative_to(outdir)).replace("\\", "/")
                row.setdefault("sha256", {})[name] = sha256_file(p)
            _check_lod_ladder(measured)
            row["outputs"] = rel_outputs
            row["measured"] = measured
            row["licence"] = licence_row(item, spec, backend, tool_versions,
                                         decision_records)
            row["status"] = "done"
            row["finished"] = utcnow()
            lod0 = measured.get("LOD0") or list(measured.values())[0]
            log(f"  [{idx + 1}/{len(items)}] {iid}: done - {len(rel_outputs)} LOD(s), "
                f"{lod0['verts']} verts, {lod0['dims_m']} m"
                + ("" if row["licence"]["ship_ok"] else "  [SHIP BLOCKED: see licence]"))
            done += 1
        except StageError as e:
            row["status"] = "failed"
            row["error"] = str(e)
            row["finished"] = utcnow()
            failed += 1
            log(f"  [{idx + 1}/{len(items)}] {iid}: FAILED - {e}")
        except Exception as e:                                   # noqa: BLE001
            row["status"] = "failed"
            row["error"] = f"{type(e).__name__}: {e}"
            row["finished"] = utcnow()
            failed += 1
            log(f"  [{idx + 1}/{len(items)}] {iid}: FAILED - {type(e).__name__}: {e}")
        man["items"].append(row)
        _write_manifest(man, man_path, spec, done, skipped, failed, attempted,
                        stopped, started, now)

    _write_manifest(man, man_path, spec, done, skipped, failed, attempted,
                    stopped, started, now)
    return man


def _check_lod_ladder(measured):
    """An LOD chain that does not get cheaper is not an LOD chain.

    Decimation is the one stage whose failure is invisible in the file: a
    modifier that did not apply exports a perfect copy of LOD0 under the name
    LOD2, and every count downstream reads as success.
    """
    names = sorted(n for n in measured if re.fullmatch(r"LOD\d+", n))
    for a, b in zip(names, names[1:]):
        if measured[b]["tris"] > measured[a]["tris"]:
            raise StageError(f"{b} has MORE triangles than {a} "
                             f"({measured[b]['tris']} > {measured[a]['tris']}) - "
                             "the decimation did not apply")


def _write_manifest(man, path, spec, done, skipped, failed, attempted, stopped,
                    started, now):
    """Counts with their denominator, every time, and a status that cannot say
    DONE over a partial batch."""
    total = man["items_in_spec"]
    accounted = done + skipped + failed
    not_attempted = total - accounted
    man["counts"] = {
        "done": done, "skipped": skipped, "failed": failed,
        "attempted": attempted, "not_attempted": not_attempted,
        "in_spec": total,
    }
    man["elapsed_minutes"] = round((now() - started) / 60.0, 2)
    man["written"] = utcnow()
    if stopped:
        man["status"] = f"STOPPED {accounted}/{total}"
        man["stopped_because"] = stopped
    elif not_attempted:
        man["status"] = f"INCOMPLETE {accounted}/{total}"
    elif failed:
        man["status"] = f"COMPLETE WITH FAILURES {done + skipped}/{total}"
    else:
        man["status"] = f"DONE {accounted}/{total}"
    if not_attempted > 0:
        man["caps"] = [f"(+{not_attempted} more item(s) in the batch not "
                       f"attempted on this run)"]
    problems, caveats, examined = licence_check(man)
    man["licence_gate"] = {
        "examined": examined,
        "problems": problems,
        "caveats": caveats,
        "note": ("0 problems over 0 examined rows is not a pass - the examined "
                 "count is the denominator" if examined == 0 else ""),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    return man


def write_attribution(outdir, man):
    """The credit file beside the meshes, written by the same run that writes
    them so they cannot drift apart."""
    rows = []
    for r in man.get("items") or []:
        if r.get("status") != "done":
            continue
        lic = r.get("licence") or {}
        rows.append({"id": r["id"], "files": sorted((r.get("outputs") or {}).values()),
                     "source": lic.get("source"), "licence": lic.get("source_licence"),
                     "credit": lic.get("source_credit"),
                     "made_by": lic.get("tool"), "ship_ok": lic.get("ship_ok")})
    doc = {
        "what": "Meshes produced by tools/meshgen. Every row names its source, "
                "that source's licence and the tools that touched it.",
        "law": ALLOWLIST_DOC,
        "batch": man.get("batch"),
        "written": utcnow(),
        "items": rows,
        "items_attributed": len(rows),
        "items_in_batch": man.get("items_in_spec"),
    }
    p = pathlib.Path(outdir) / "ATTRIBUTION.json"
    p.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# SENDING THE ANSWER BACK. A report that stays on his PC is not a channel this
# project can read (rule 12), and the whole value of the probe is that WE get
# to see what it found. Files are staged BY NAME, never `git add <dir>`: a run
# that failed has otherwise committed its stale checkout as its own evidence.
# ---------------------------------------------------------------------------
class Publisher:
    def __init__(self, repo, log, enabled=True):
        self.repo = pathlib.Path(repo) if repo else None
        self.log = log
        self.enabled = enabled and self.repo is not None
        self.branch = None
        self.why = "" if self.enabled else "no repository found" if not repo else "--no-send"

    def _git(self, *args, timeout=180):
        env = dict(os.environ, GIT_EDITOR="true", GIT_MERGE_AUTOEDIT="no",
                   GIT_TERMINAL_PROMPT="0")
        p = subprocess.run(["git"] + list(args), cwd=str(self.repo), env=env,
                           capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")

    def preflight(self):
        """Early, on purpose: 'this clone cannot push' is worth knowing in
        minute one, not after four hours of meshes that then go nowhere."""
        if not self.enabled:
            self.log(f"  SENDING BACK IS OFF ({self.why}). Whatever is produced "
                     "will need carrying by hand.")
            return False
        rc, out = self._git("rev-parse", "--abbrev-ref", "HEAD")
        self.branch = out.strip() if rc == 0 else None
        if not self.branch or self.branch == "HEAD":
            self.enabled = False
            self.why = f"the clone is not on a branch (got {self.branch!r})"
            self.log(f"  SENDING BACK IS OFF: {self.why}")
            return False
        self.log(f"  sending back is ON: branch {self.branch}")
        return True

    def send(self, paths, message):
        if not self.enabled:
            return False
        rel = []
        for p in paths:
            p = pathlib.Path(p)
            if p.exists():
                try:
                    rel.append(str(p.relative_to(self.repo)))
                except ValueError:
                    pass                      # outside the repo: not ours to commit
        if not rel:
            self.log("  nothing to send: none of the outputs are inside the repo")
            return False
        rc, out = self._git("add", "--", *rel)
        if rc != 0:
            self.log(f"  git add failed: {out.strip()[:300]}")
            return False
        rc, out = self._git("commit", "-m", message)
        if rc != 0 and "nothing to commit" in out:
            self.log("  nothing changed since the last send")
            return True
        if rc != 0:
            self.log(f"  git commit failed: {out.strip()[:300]}")
            return False
        rc, out = self._git("push", "origin", f"HEAD:{self.branch}")
        if rc != 0:
            self.log(f"  PUSH FAILED: {out.strip()[:300]}")
            self.log(f"  the work is committed locally on {self.branch}; it needs "
                     "pushing by hand or on the next run.")
            return False
        self.log(f"  SENT: {len(rel)} file(s) to {self.branch}")
        return True


def load_json(path, label):
    """(data, read). `read` is a separate fact from what the file said: 'the
    probe looked and found nothing' and 'the probe never ran' are different
    machines and must not print the same."""
    if not path:
        return {"probe": f"no {label} path given", "probe_file_read": False}, False
    p = pathlib.Path(path)
    if not p.exists():
        return {"probe": f"{label} missing at {path}", "probe_file_read": False}, False
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception as e:                                       # noqa: BLE001
        return {"probe": f"{label} unreadable: {type(e).__name__}: {e}",
                "probe_file_read": False}, False
    if not isinstance(d, dict):
        return {"probe": f"{label} is not an object", "probe_file_read": False}, False
    d["probe_file_read"] = True
    return d, True


def main(argv=None):
    ap = argparse.ArgumentParser(description="LEDGER local prop pipeline")
    ap.add_argument("command", nargs="?", default="run",
                    choices=["run", "probe", "plan", "verify"])
    ap.add_argument("--machine", help="machine.json from imagegen's probe")
    ap.add_argument("--tools", help="tools.json from probe-tools.ps1")
    ap.add_argument("--repo", help="repository root")
    ap.add_argument("--workspace", help="scratch, OUTSIDE the repo")
    ap.add_argument("--spec", help="batch spec json (default: the local batch)")
    ap.add_argument("--out", help="override the output directory")
    ap.add_argument("--max-minutes", type=float, default=480.0,
                    help="wall-clock cap. A backstop against a runaway, not a "
                         "target; the batch is meant to run overnight.")
    ap.add_argument("--redo", action="store_true",
                    help="redo every item, including ones already on disk")
    ap.add_argument("--no-send", action="store_true",
                    help="do not commit or push the report and manifest back")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--series", nargs="?", const=".", metavar="DIR",
                    help="print the mesh measurement series over every GLB "
                         "under DIR. This is what the floors were read off.")
    a = ap.parse_args(argv)

    if a.series:
        return series(a.series)
    if a.selftest:
        return selftest()

    here = pathlib.Path(__file__).resolve().parent
    repo = pathlib.Path(a.repo) if (a.repo and a.repo.strip()) else None
    if repo is None and (here.parent.parent / "CLAUDE.md").exists():
        repo = here.parent.parent
    ws = pathlib.Path(a.workspace) if a.workspace else (
        pathlib.Path.home() / "ledger-meshgen")
    ws.mkdir(parents=True, exist_ok=True)

    machine, mread = load_json(a.machine, "machine.json")
    tools, tread = load_json(a.tools, "tools.json")
    lines = []

    def log(s=""):
        print(s, flush=True)
        lines.append(str(s))

    spec_path = pathlib.Path(a.spec) if a.spec else here / "specs" / "props-local-01.json"
    spec, spec_ok = ({}, False)
    if spec_path.exists():
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec_ok = True
        except Exception as e:                                   # noqa: BLE001
            log(f"the batch spec {spec_path} is not readable JSON: {e}")
    else:
        log(f"the batch spec {spec_path} does not exist")

    pr = probe(machine, tools)
    reports = []
    if repo:
        reports.append(repo / "production" / "mesh-reports" / "mesh-machine-report.txt")
    reports.append(ws / "mesh-machine-report.txt")

    pub = Publisher(repo, log, enabled=not a.no_send)
    pub.preflight()

    outdir = (pathlib.Path(a.out) if a.out else
              (repo / (spec.get("out_dir") or "content/props") if repo
               else ws / "props"))

    def write_reports(extra):
        text = format_probe_report(machine, tools, pr, spec if spec_ok else None,
                                   extra)
        for p in reports:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            log(f"report written: {p}")
        return text

    log(format_probe_report(machine, tools, pr, spec if spec_ok else None))

    if not spec_ok:
        write_reports(["REFUSED: no usable batch spec, so nothing was attempted."])
        return EXIT_SPEC
    problems = validate_spec(spec, repo)
    if problems:
        log("")
        log(f"REFUSED TO START: the batch spec has {len(problems)} problem(s) "
            f"over {len(spec.get('items') or [])} item(s):")
        for pb in problems:
            log(f"  - {pb}")
        write_reports(["REFUSED: spec problems"] + [f"  - {x}" for x in problems])
        return EXIT_SPEC

    if a.command == "verify":
        man_path = outdir / "manifest.json"
        if not man_path.exists():
            log(f"NOTHING MEASURED - no manifest at {man_path}")
            return EXIT_LICENCE
        man = json.loads(man_path.read_text(encoding="utf-8"))
        probs, caveats, examined = licence_check(man)
        log(f"licence gate: {len(probs)} problem(s), {len(caveats)} caveat(s), "
            f"over {examined} completed item(s) of {man.get('items_in_spec')} in "
            f"the batch")
        for x in probs + caveats:
            log(f"  - {x}")
        if examined == 0:
            log("  0 problems over 0 rows is not a pass. Nothing has been made yet.")
            return EXIT_LICENCE
        return EXIT_LICENCE if probs else EXIT_OK

    backend, why = choose_backend(pr, spec.get("backend"))
    log("")
    log(why)
    if a.command == "probe":
        runnable = [b for b, v in pr["backends"].items() if v["ok"]]
        extra = [f"backends that can run here: {', '.join(runnable) or 'NONE'}",
                 f"the batch {spec.get('batch_name')} asks for "
                 f"{spec.get('backend')}: {'YES' if backend else 'NO'}", why]
        write_reports(extra)
        pub.send(reports, f"meshgen probe: {spec.get('backend')} "
                          f"{'runnable' if backend else 'CANNOT RUN'} on "
                          f"{machine.get('hostname') or 'this PC'}")
        return EXIT_OK if backend else EXIT_CANNOT_RUN

    if backend is None:
        log("")
        log("=" * 64)
        log("STOPPED BEFORE MAKING ANYTHING - on purpose. Nothing was")
        log("downloaded, installed or written except this report.")
        for r in pr["backends"][spec.get("backend")]["reqs"]:
            if not r["ok"]:
                log(f"  MISSING: {r['what']}")
                log(f"     need : {r['need']}")
                log(f"     found: {r['found']}")
                log(f"     fix  : {r['fix']}")
        log("=" * 64)
        write_reports(["RUN STOPPED BEFORE MAKING ANYTHING.", why])
        pub.send(reports, f"meshgen: {spec.get('backend')} cannot run on "
                          f"{machine.get('hostname') or 'this PC'}")
        return EXIT_CANNOT_RUN

    need = TRELLIS_MIN_DISK_GB if backend == "trellis" else LOCAL_MIN_DISK_GB
    if pr["free_disk_gb"] and pr["free_disk_gb"] < need:
        log(f"REFUSING TO START: {pr['free_disk_gb']:.1f} GB free and this needs "
            f"{need:.0f} GB.")
        write_reports([f"refused: not enough disk ({pr['free_disk_gb']:.1f} GB)"])
        return EXIT_DISK

    sf = stop_file(repo, ws)
    if sf:
        log(f"STOPPED: the kill switch {sf} exists. Delete it to allow a run.")
        write_reports([f"stopped: kill switch {sf}"])
        return EXIT_STOPPED

    if a.command == "plan":
        log("")
        log(f"PLAN - {spec['batch_name']}, backend {backend}, "
            f"{len(spec['items'])} item(s) into {outdir}")
        for it in spec["items"]:
            src = it.get("source") or {}
            log(f"  {it['id']:28s} {it.get('category','?'):14s} "
                f"{src.get('path') or src.get('image_id')}")
        write_reports([f"plan only: {len(spec['items'])} item(s), nothing made"])
        return EXIT_OK

    log("")
    log(f"Making {len(spec['items'])} item(s) into {outdir}")
    log(f"  kill switch: {(repo / 'production/STOP') if repo else (ws / 'STOP')} "
        "(create it to stop between items)")
    man = run_batch(spec, backend, outdir, ws, repo, tools, log,
                    max_minutes=a.max_minutes, redo=a.redo)
    att = write_attribution(outdir, man)
    c = man["counts"]
    log("")
    log(f"{man['status']}: {c['done']} made, {c['skipped']} skipped, "
        f"{c['failed']} failed, {c['not_attempted']} not attempted, "
        f"of {c['in_spec']} in the batch")
    for cap in man.get("caps") or []:
        log(f"  CAP: {cap}")
    lg = man["licence_gate"]
    log(f"licence gate: {len(lg['problems'])} problem(s) and {len(lg['caveats'])} "
        f"caveat(s) over {lg['examined']} completed item(s)"
        + (f" - {lg['note']}" if lg.get("note") else ""))
    for x in lg["problems"] + lg["caveats"]:
        log(f"  - {x}")
    write_reports([man["status"]] + lines[-12:])
    pub.send(reports + [outdir / "manifest.json", att],
             f"meshgen {spec['batch_name']}: {man['status']}")

    if lg["problems"]:
        return EXIT_LICENCE
    if man.get("stopped_because"):
        return EXIT_STOPPED
    if c["attempted"] and c["done"] == 0 and c["failed"] == c["attempted"]:
        return EXIT_ALL_FAILED
    return EXIT_OK


# ---------------------------------------------------------------------------
# THE SELFTEST. Accepting case first everywhere, because the expensive failure
# is a check nothing survives - four guards in this project have blocked the
# good case rather than the bad one, and every one of them passed its failure
# case.
#
# WHAT IT CANNOT SEE, said here rather than implied by a passing count: no GPU,
# no Blender, no Windows and no PowerShell exist in the container this runs in.
# So TRELLIS, Blender and both .bat files are UNRUN. What is tested of them is
# the SEAM - that the flags meshgen passes are the flags the Blender script
# accepts, that the .bat explains every exit code this file can return, and
# that the specs validate. That is the largest testable part of an untestable
# thing, and it is not the same as coverage.
# ---------------------------------------------------------------------------
def _synth_glb(path, verts=100, tris=50, dims=(1.0, 2.0, 1.0), node_scale=1.0,
               with_bounds=True, break_it=None):
    """A minimal but REAL GLB: header, JSON chunk, correct total length.

    The reader only ever looks at the JSON chunk, so a fixture needs no buffer
    to exercise it honestly - and the real files in ledger/Assets/Props are the
    accepting case for everything a synthetic fixture cannot prove.
    """
    half = [d / (2.0 * node_scale) for d in dims]
    acc = [{"count": verts, "type": "VEC3", "componentType": 5126}]
    if with_bounds:
        acc[0]["min"] = [-half[0], 0.0, -half[2]]
        acc[0]["max"] = [half[0], half[1] * 2, half[2]]
    acc.append({"count": tris * 3, "type": "SCALAR", "componentType": 5125})
    js = {
        "asset": {"version": "2.0"},
        "accessors": acc,
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "nodes": [{"mesh": 0, "scale": [node_scale, node_scale, node_scale]}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
        "materials": [{"name": "m"}],
    }
    blob = json.dumps(js).encode("utf-8")
    blob += b" " * ((4 - len(blob) % 4) % 4)
    body = struct.pack("<I4s", len(blob), b"JSON") + blob
    magic = b"glTF" if break_it != "magic" else b"XXXX"
    total = 12 + len(body)
    if break_it == "length":
        total += 40                     # header claims more than the file has
    head = struct.pack("<4sII", magic, 2, total)
    data = head + body
    if break_it == "nojson":
        data = struct.pack("<4sII", b"glTF", 2, 12 + 8) + struct.pack("<I4s", 0, b"BIN\x00")
    if break_it == "tiny":
        data = b"glTF"
    pathlib.Path(path).write_bytes(data)
    return path


def selftest():                                                  # noqa: C901
    passed = failed = 0
    notes = []

    def ok(name, cond, got=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  ok   {name}")
        else:
            failed += 1
            print(f"  FAIL {name}" + (f" - {got}" if got else ""))

    def refuses(name, fn, must_say=""):
        """A rejecting case: it must raise, and the reason must be legible."""
        nonlocal passed, failed
        try:
            fn()
        except Exception as e:                                   # noqa: BLE001
            if must_say and must_say.lower() not in str(e).lower():
                failed += 1
                print(f"  FAIL {name} - refused but said {e!r}, wanted {must_say!r}")
            else:
                passed += 1
                print(f"  ok   {name}")
            return
        failed += 1
        print(f"  FAIL {name} - accepted input it must refuse")

    import tempfile
    here = pathlib.Path(__file__).resolve().parent
    repo = here.parent.parent
    print("meshgen selftest - accepting case first in every section\n")

    # -- A. the GLB reader, on REAL files first -----------------------------
    print("A. the GLB reader")
    real_dir = repo / "ledger/Assets/Props/base-mesh"
    lamp = real_dir / "lamp_post_01.glb"
    cone = real_dir / "traffic_cone_01.glb"
    if lamp.exists():
        st = glb_stats(lamp)
        ok("a real repository GLB parses and measures",
           st["verts"] == 3475 and abs(st["dims_m"][1] - 3.002) < 0.01, str(st))
        ok("its pivot is measured too (lamp post stands on y=0)",
           abs(st["base_y"]) < 0.01, str(st["base_y"]))
        good, why = mesh_verdict(st)
        ok("and it passes the mesh verdict", good, why)
    else:
        notes.append(f"{lamp} is absent - the real-file accepting case was SKIPPED")
    if cone.exists():
        st = glb_stats(cone)
        # THE FAULT THIS CHECK EXISTS FOR: reading accessor min/max without the
        # node transform reports this cone as 0.004 x 0.003 x 0.005 metres.
        ok("node transforms are composed, not skipped (traffic cone is ~0.45 m, "
           "not ~0.003 m)", 0.3 < st["dims_m"][1] < 0.6, str(st["dims_m"]))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        p = _synth_glb(tmp / "good.glb", verts=100, tris=50, dims=(1, 2, 1))
        st = glb_stats(p)
        ok("a synthetic GLB reads back its own counts",
           st["verts"] == 100 and st["tris"] == 50, str(st))
        p2 = _synth_glb(tmp / "scaled.glb", dims=(1, 3, 1), node_scale=0.001)
        ok("a node scale of 0.001 still measures 3 m",
           abs(glb_stats(p2)["dims_m"][1] - 3.0) < 0.01,
           str(glb_stats(p2)["dims_m"]))
        refuses("a file that is not a GLB is refused",
                lambda: glb_stats(_synth_glb(tmp / "bad.glb", break_it="magic")),
                "not a GLB")
        refuses("a truncated GLB is refused by name",
                lambda: glb_stats(_synth_glb(tmp / "trunc.glb", break_it="length")),
                "TRUNCATED")
        refuses("a container with no JSON chunk is refused",
                lambda: glb_stats(_synth_glb(tmp / "nojson.glb", break_it="nojson")),
                "no JSON chunk")
        refuses("an empty export is refused",
                lambda: glb_stats(_synth_glb(tmp / "tiny.glb", break_it="tiny")),
                "not a GLB")

        # -- B. the verdict, both ways --------------------------------------
        print("\nB. the mesh verdict")
        good, why = mesh_verdict(glb_stats(_synth_glb(tmp / "v_ok.glb")))
        ok("a normal prop is accepted", good, why)
        good, why = mesh_verdict(glb_stats(_synth_glb(tmp / "v_deg.glb", verts=4, tris=1)))
        ok("a degenerate mesh is refused with its floor named",
           not good and "floor" in why, why)
        good, why = mesh_verdict(glb_stats(_synth_glb(tmp / "v_nb.glb", with_bounds=False)))
        ok("no bounds reads as unknown, NOT as zero",
           not good and "not zero" in why, why)
        good, why = mesh_verdict(glb_stats(_synth_glb(tmp / "v_big.glb", dims=(1, 500, 1))))
        ok("a 500 m prop is refused as a unit error", not good and "unit" in why, why)
        good, why = mesh_verdict(glb_stats(_synth_glb(tmp / "v_sm.glb", dims=(0.001, 0.001, 0.001))))
        ok("a millimetre prop is refused as a unit error", not good and "unit" in why, why)

    # -- C. the probe -------------------------------------------------------
    print("\nC. the probe, and the refusal it exists to be able to give")
    good_machine = {"probe_file_read": True, "hostname": "SYNTH",
                    "free_disk_bytes": 200 * 1024 ** 3, "disk_letter": "C:",
                    "gpus": [{"name": "NVIDIA GeForce RTX 4090",
                              "vram_bytes_registry": 24 * 1024 ** 3}]}
    good_tools = {"probe_file_read": True, "nvcc": "C:\\cuda\\nvcc.exe",
                  "msvc": "C:\\vs\\cl.exe", "bash": "C:\\git\\bash.exe",
                  "git": "C:\\git\\git.exe", "python_version": "3.11.5",
                  "blender": "C:\\blender.exe", "blender_version": "Blender 4.2.1"}
    pr = probe(good_machine, good_tools)
    ok("a qualifying machine CAN run trellis", pr["backends"]["trellis"]["ok"],
       str([r["what"] for r in pr["backends"]["trellis"]["reqs"] if not r["ok"]]))
    ok("and can run local", pr["backends"]["local"]["ok"])

    # HIS ACTUAL MACHINE, from the two probe files already in this repository:
    # game-design/agent-reports/machine-report.txt (26 Aug) and
    # production/d1-probe/ue-machine-read.md (1 Sep).
    jafar = {"probe_file_read": True, "hostname": "JAFAR-DESKTOP",
             "free_disk_bytes": int(92.3 * 1024 ** 3), "disk_letter": "C:",
             "cpu": "AMD Ryzen 5 5600X 6-Core Processor",
             "gpus": [{"name": "Parsec Virtual Display Adapter",
                       "vram_bytes_registry": 0, "vram_bytes": 0},
                      {"name": "AMD Radeon RX 6700",
                       "vram_bytes_registry": int(9.98 * 1024 ** 3),
                       "vram_bytes": 4294967295}]}
    jafar_tools = {"probe_file_read": True, "nvcc": "", "msvc": "", "bash": "",
                   "git": "C:\\git.exe", "python_version": "3.12.4",
                   "blender": "", "nvidia_smi": ""}
    pj = probe(jafar, jafar_tools)
    missing = [r["what"] for r in pj["backends"]["trellis"]["reqs"] if not r["ok"]]
    ok("the real machine CANNOT run trellis", not pj["backends"]["trellis"]["ok"])
    ok("and every blocker is named, not just the first",
       {"an NVIDIA GPU", "VRAM", "CUDA toolkit", "C++ compiler"} <= set(missing),
       str(missing))
    ok("the VRAM figure is the registry one, not the uint32 ceiling",
       abs(pj["vram_gb"] - 9.98) < 0.05, str(pj["vram_gb"]))
    ok("without Blender the local backend is refused too",
       not pj["backends"]["local"]["ok"])
    pj2 = probe(jafar, dict(jafar_tools, blender="C:\\blender.exe"))
    ok("WITH Blender the local backend runs on that same machine",
       pj2["backends"]["local"]["ok"],
       str([r["what"] for r in pj2["backends"]["local"]["reqs"] if not r["ok"]]))
    ceiling = probe({"probe_file_read": True, "free_disk_bytes": 10 ** 12,
                     "gpus": [{"name": "NVIDIA Thing", "vram_bytes": 4294967295}]},
                    good_tools)
    ok("a uint32 VRAM ceiling is UNKNOWN, not 4 GB",
       not ceiling["vram_known"] and not ceiling["backends"]["trellis"]["ok"],
       ceiling["vram_source"])
    single = probe({"probe_file_read": True, "free_disk_bytes": 10 ** 12,
                    "gpus": {"name": "NVIDIA X", "vram_bytes_registry": 24 * 1024 ** 3}},
                   good_tools)
    ok("a single adapter serialised as an object (PowerShell) is still seen",
       single["adapters"] == 1 and single["backends"]["trellis"]["ok"])
    none_read = probe({}, {})
    ok("probes that never ran refuse everything AND say which did not run",
       not none_read["backends"]["local"]["ok"]
       and "machine probe did not run" in none_read.get("unmeasured", "")
       and "toolchain probe did not run" in none_read.get("unmeasured", ""),
       none_read.get("unmeasured"))
    rep = format_probe_report(jafar, jafar_tools, pj)
    ok("the report names the missing pieces and their fixes",
       "blender.org" in rep and "16GB" in rep and "0 of" not in rep.split("backend local")[0][-40:],
       "")
    ok("the report ships denominators (N of M requirements met)",
       re.search(r"\(\d+ of \d+ requirements met\)", rep) is not None)

    # -- D. backend choice --------------------------------------------------
    print("\nD. choosing a backend")
    b, why = choose_backend(pj2, "local")
    ok("an available backend is chosen", b == "local", why)
    b, why = choose_backend(pj, "trellis")
    ok("an unavailable one is refused and says what is missing",
       b is None and "CANNOT RUN" in why, why)
    b, why = choose_backend(pj2, "trellis")
    ok("asking for trellis does NOT silently fall back to local",
       b is None, str(b))

    # -- E. the spec --------------------------------------------------------
    print("\nE. the batch specs")
    local_spec = json.loads((here / "specs/props-local-01.json").read_text())
    trellis_spec = json.loads((here / "specs/props-trellis-01.json").read_text())
    probs = validate_spec(local_spec, repo)
    ok(f"the shipped local batch validates ({len(local_spec['items'])} items)",
       not probs, "; ".join(probs[:3]))
    probs = validate_spec(trellis_spec, repo)
    ok(f"the shipped trellis batch validates ({len(trellis_spec['items'])} items)",
       not probs, "; ".join(probs[:3]))
    ok("every local source file exists on disk",
       all((repo / it["source"]["path"]).exists() for it in local_spec["items"]),
       "missing: " + str([it["id"] for it in local_spec["items"]
                          if not (repo / it["source"]["path"]).exists()][:3]))
    img_spec = json.loads((here / "specs/prop-images-01.json").read_text())
    img_ids = {i["id"] for i in img_spec["items"]}
    ok("every trellis item names an image the image spec makes",
       all(it["source"]["image_id"] in img_ids for it in trellis_spec["items"]),
       str([it["source"]["image_id"] for it in trellis_spec["items"]
            if it["source"]["image_id"] not in img_ids]))

    def broken(**kw):
        s = json.loads(json.dumps(local_spec))
        s.update(kw)
        return s

    for name, mutate, want in [
        ("a schema mismatch", lambda s: s.update({"schema": 99}), "schema"),
        ("two items sharing an id",
         lambda s: s["items"].append(dict(s["items"][0])), "share this id"),
        ("a source file that does not exist",
         lambda s: s["items"][0]["source"].update({"path": "nope/missing.glb"}),
         "does not exist"),
        ("a source licence that is not on the allowlist",
         lambda s: s["items"][0]["source"].update({"licence": "all rights reserved"}),
         "not one this pipeline"),
        ("a source with no credit",
         lambda s: s["items"][0]["source"].update({"credit": ""}), "credit"),
        ("an id that cannot be a directory name",
         lambda s: s["items"][0].update({"id": "Lamp Post!"}), "lower case"),
        ("an LOD ratio outside (0,1]",
         lambda s: s["items"][0].update({"lods": {"LOD0": 4.0}}), "must be in"),
        ("a banned tool named anywhere in the spec",
         lambda s: s.update({"batch_name": "hunyuan3d trial"}), "NEVER SHIP"),
    ]:
        s = json.loads(json.dumps(local_spec))
        mutate(s)
        probs = validate_spec(s, repo)
        ok(f"REFUSED: {name}", any(want.lower() in p.lower() for p in probs),
           "; ".join(probs[:2]) or "accepted it")
    s = json.loads(json.dumps(trellis_spec))
    s["items"][0].pop("target_height_m")
    probs = validate_spec(s, repo)
    ok("REFUSED: a trellis item with no target height (its output is unit-less)",
       any("unit cube" in p for p in probs), "; ".join(probs[:2]) or "accepted it")

    # THE TRIPO BAN, BOTH WAYS AND ACCEPTING CASE FIRST. The BANNED key was
    # "tripo-service", a string no spec would ever contain, so the ban could
    # not fire on the word anybody actually writes and the rejecting case
    # rejected nothing. The key is now "tripo"; what keeps a tripod out of it
    # is banned_hits's word boundary, not the suffix, so both are checked here
    # rather than reasoned about.
    ok("ACCEPTED: a spec about a tripod, which is a stand and not a service",
       not any("tripo" in x.lower() for x in validate_spec(
           broken(batch_name="tripod props"), repo)),
       str(validate_spec(broken(batch_name="tripod props"), repo)[:2]))
    ok("ACCEPTED: TripoSR, which is MIT and a different thing from the paid "
       "service", not banned_hits("source: TripoSR"),
       str(banned_hits("source: TripoSR")))
    ok("REFUSED: Tripo, spelled the way anybody would actually write it",
       [b for b, _w in banned_hits("backend: Tripo cloud")] == ["tripo"],
       str(banned_hits("backend: Tripo cloud")))
    probs = validate_spec(broken(batch_name="Tripo trial"), repo)
    ok("REFUSED: and a spec naming it is refused by the allowlist line",
       any("SHIP-SAFE 2" in x for x in probs),
       "; ".join(probs[:2]) or "accepted it")

    # -- F. the batch loop, with the making faked ---------------------------
    print("\nF. the batch: resume, counts, the kill switch, the LOD ladder")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        out = tmp / "out"
        ws = tmp / "ws"
        ws.mkdir()
        clock = [1000.0]

        def now():
            return clock[0]

        made = []

        def fake_clean(item, spec, src, item_dir, tools, log, tris=None):
            made.append(item["id"])
            outputs = {}
            for i, (name, ratio) in enumerate(sorted((item.get("lods") or
                                                      spec["default_lods"]).items())):
                outputs[name] = str(_synth_glb(item_dir / f"{item['id']}_{name}.glb",
                                               verts=int(400 * ratio),
                                               tris=int(200 * ratio)))
            return {"blender": "fake 4.2", "outputs": outputs}

        spec3 = {"schema": 1, "batch_name": "t", "backend": "local",
                 "default_lods": {"LOD0": 1.0, "LOD1": 0.5},
                 "items": [{"id": f"p{i}", "category": "street",
                            "source": {"kind": "file", "path": f"src{i}.glb",
                                       "licence": "CC0-1.0", "credit": "Somebody"}}
                           for i in range(3)]}
        for i in range(3):
            _synth_glb(tmp / f"src{i}.glb")
        tools = {"blender": "fake", "blender_version": "4.2"}
        man = run_batch(spec3, "local", out, ws, tmp, tools, lambda *_: None,
                        stages={"clean": fake_clean}, decision_records={}, now=now)
        ok("a clean run reports done with its denominator",
           man["counts"] == {"done": 3, "skipped": 0, "failed": 0, "attempted": 3,
                             "not_attempted": 0, "in_spec": 3}, str(man["counts"]))
        ok("and its status names the fraction", man["status"] == "DONE 3/3",
           man["status"])
        ok("every output was measured, not just written",
           all(r["measured"]["LOD0"]["verts"] == 400 for r in man["items"]),
           str(man["items"][0].get("measured")))
        ok("the LOD ladder gets cheaper",
           man["items"][0]["measured"]["LOD1"]["tris"] <
           man["items"][0]["measured"]["LOD0"]["tris"])
        before = {p.name: p.read_bytes() for p in out.rglob("*.glb")}

        made.clear()
        man2 = run_batch(spec3, "local", out, ws, tmp, tools, lambda *_: None,
                         stages={"clean": fake_clean}, decision_records={}, now=now)
        ok("a second run SKIPS what is already done", man2["counts"]["skipped"] == 3
           and man2["counts"]["done"] == 0 and not made, str(man2["counts"]))
        after = {p.name: p.read_bytes() for p in out.rglob("*.glb")}
        ok("and does not touch a single byte of it", before == after)

        spec4 = json.loads(json.dumps(spec3))
        spec4["items"][1]["lods"] = {"LOD0": 1.0}
        made.clear()
        man3 = run_batch(spec4, "local", out, ws, tmp, tools, lambda *_: None,
                         stages={"clean": fake_clean}, decision_records={}, now=now)
        ok("a changed recipe redoes exactly that item",
           made == ["p1"] and man3["counts"]["skipped"] == 2, str(made))

        (out / "p0" / "p0_LOD0.glb").write_bytes(b"glTF" + b"\x00" * 40)
        made.clear()
        man4 = run_batch(spec4, "local", out, ws, tmp, tools, lambda *_: None,
                         stages={"clean": fake_clean}, decision_records={}, now=now)
        ok("a corrupted output is redone even though the manifest said done",
           made == ["p0"], str(made))

        def fake_fail(item, spec, src, item_dir, tools, log):
            if item["id"] == "p1":
                raise StageError("the fake stage refused on purpose")
            return fake_clean(item, spec, src, item_dir, tools, log)

        man5 = run_batch(spec3, "local", out, ws, tmp, tools, lambda *_: None,
                         redo=True, stages={"clean": fake_fail},
                         decision_records={}, now=now)
        ok("one failure is counted, named and does not stop the batch",
           man5["counts"]["failed"] == 1 and man5["counts"]["done"] == 2
           and "COMPLETE WITH FAILURES" in man5["status"], str(man5["counts"]))
        ok("and the failing item carries its reason",
           "refused on purpose" in
           [r.get("error", "") for r in man5["items"] if r["status"] == "failed"][0])

        # THE KILL SWITCH, matching production/STOP in the night runner.
        (tmp / "production").mkdir(exist_ok=True)
        (tmp / "production" / "STOP").write_text("stop")
        man6 = run_batch(spec3, "local", out, ws, tmp, tools, lambda *_: None,
                         redo=True, stages={"clean": fake_clean},
                         decision_records={}, now=now)
        ok("the kill switch stops the batch before the first item",
           man6["counts"]["done"] == 0 and "STOPPED" in man6["status"], man6["status"])
        ok("and says which file stopped it",
           "STOP" in (man6.get("stopped_because") or ""), man6.get("stopped_because"))
        ok("a stopped run never reports DONE", "DONE" not in man6["status"])
        ok("and announces what it did not attempt",
           any("not attempted" in c for c in man6["caps"]), str(man6["caps"]))
        (tmp / "production" / "STOP").unlink()

        big = json.loads(json.dumps(spec3))
        big["items"] = [dict(spec3["items"][0], id=f"q{i}") for i in range(40)]
        for i in range(40):
            big["items"][i]["source"] = dict(spec3["items"][0]["source"],
                                             path=f"src0.glb")
        calls = [0]

        def slow_clean(item, spec, src, item_dir, tools, log):
            calls[0] += 1
            if calls[0] >= 12:
                # The cap bites AFTER the twelfth item completes, which is the
                # case worth testing: the twelfth is done and counted, the
                # thirteenth is never started.
                clock[0] += 10_000
            return fake_clean(item, spec, src, item_dir, tools, log)

        man7 = run_batch(big, "local", tmp / "out2", ws, tmp, tools, lambda *_: None,
                         max_minutes=60, stages={"clean": slow_clean},
                         decision_records={}, now=now)
        ok("a batch of 40 that completes 12 reports 12/40, never 'done'",
           man7["status"].startswith("STOPPED 12/40"), man7["status"])
        ok("and the cap announces itself with the number not attempted",
           any("+28" in c for c in man7["caps"]), str(man7["caps"]))

        def bad_ladder(item, spec, src, item_dir, tools, log):
            outputs = {"LOD0": str(_synth_glb(item_dir / "a.glb", verts=400, tris=200)),
                       "LOD1": str(_synth_glb(item_dir / "b.glb", verts=800, tris=400))}
            return {"outputs": outputs}

        man8 = run_batch(spec3, "local", tmp / "out3", ws, tmp, tools,
                         lambda *_: None, stages={"clean": bad_ladder},
                         decision_records={}, now=now)
        ok("a decimation that did not apply is caught by the ladder check",
           man8["counts"]["failed"] == 3
           and "did not apply" in man8["items"][0]["error"],
           man8["items"][0].get("error"))

        # -- G. the licence gate --------------------------------------------
        print("\nG. the licence gate")
        probs, caveats, examined = licence_check(man)
        ok("a clean local batch passes the gate over a named denominator",
           not probs and examined == 3, f"{probs} over {examined}")
        ok("and its rows carry every required field",
           all(all(man["items"][0]["licence"].get(f) for f in LICENCE_FIELDS)
               for _ in [0]), str(sorted(man["items"][0]["licence"])))
        ok("the source credit rides into the tag",
           "Somebody" in man["items"][0]["licence"]["source_credit"])
        stripped = json.loads(json.dumps(man))
        stripped["items"][0]["licence"].pop("weights_licence")
        p2, _c, _e = licence_check(stripped)
        ok("REFUSED: an untagged output", any("UNTAGGED" in x for x in p2), str(p2))
        banned = json.loads(json.dumps(man))
        banned["items"][0]["licence"]["tool"] = "Hunyuan3D 2.0"
        p3, _c, _e = licence_check(banned)
        ok("REFUSED: a banned tool in the tag", any("banned" in x for x in p3), str(p3))
        badlic = json.loads(json.dumps(man))
        badlic["items"][0]["licence"]["source_licence"] = "research only"
        p4, _c, _e = licence_check(badlic)
        ok("REFUSED: a source licence that is not on the allowlist",
           any("allowlist" in x for x in p4), str(p4))
        empty = {"items": []}
        _p, _c, e0 = licence_check(empty)
        ok("zero rows examined is reported as zero examined, not as a pass", e0 == 0)
        ok("and the manifest says so in words",
           "denominator" in (man7["licence_gate"].get("note") or "")
           or man7["licence_gate"]["examined"] > 0,
           str(man7["licence_gate"]))

        tspec = {"schema": 1, "batch_name": "t2", "backend": "trellis",
                 "default_lods": {"LOD0": 1.0},
                 "items": [{"id": "x1", "category": "street", "target_height_m": 2.0,
                            "source": {"kind": "image", "image_id": "prop_x"}}]}
        row_no_rec = licence_row(tspec["items"][0], tspec, "trellis", {}, {})
        ok("a TRELLIS output with no decision record is tagged NOT SHIPPABLE",
           row_no_rec["ship_ok"] is False and "decision record" in
           row_no_rec["ship_blocked_by"], str(row_no_rec.get("ship_blocked_by"))[:80])
        ok("and the submodule licence caveat travels with it",
           any("FlexiCubes" in c for c in row_no_rec["caveats"]),
           str(row_no_rec["caveats"])[:120])
        row_rec = licence_row(tspec["items"][0], tspec, "trellis", {},
                              {"trellis": "ledger-v2/respec/decision-register/Dx.md"})
        ok("with a decision record it is shippable", row_rec["ship_ok"] is True)
        ok("and the refusal names the exact marker that would authorise it, "
           "so this is not a gate nothing can satisfy",
           f"{DECISION_MARKER} trellis" in row_no_rec["ship_blocked_by"],
           row_no_rec["ship_blocked_by"][-90:])

        # -- THE DECISION MARKER: what counts as a record ---------------------
        # ACCEPTING CASE FIRST: a file carrying the marker on its own line.
        # Then the rejecting case, and the rejecting fixture is THE REAL
        # DIRECTOR'S REVIEW OF THIS PIPELINE, copied out of the tree rather
        # than written here. That document defeated the previous gate, which
        # took any decision file mentioning the tool near the word "licence" -
        # so it would have authorised TRELLIS the day it landed. A fixture
        # written here could be wrong in exactly the way the code was.
        with tempfile.TemporaryDirectory() as dtmp:
            dtmp = pathlib.Path(dtmp)
            acc, rej, fen = (dtmp / "a" / "game-design", dtmp / "r" / "game-design",
                             dtmp / "f" / "game-design")
            for d in (acc, rej, fen):
                d.mkdir(parents=True)
            (acc / "decision-trellis-weights.md").write_text(
                "# TRELLIS submodule weights\n\nThe mesh path loads "
                "diffoctreerast and a modified FlexiCubes.\n\n"
                f"{DECISION_MARKER} trellis\n", encoding="utf-8")
            recs = find_decision_records(acc.parent)
            ok("ACCEPTED: a decision file carrying the marker on its own line "
               "is a record, and the gate names which file",
               recs == {"trellis": "game-design/decision-trellis-weights.md"},
               str(recs))
            ok("and an output of that tool is then shippable",
               licence_row(tspec["items"][0], tspec, "trellis", {},
                           recs)["ship_ok"] is True)

            ruling = repo / ("game-design/decision-2026-09-01-meshgen-batch-"
                             "and-budget.md")
            if ruling.exists():
                text = ruling.read_text(encoding="utf-8", errors="replace")
                (rej / ruling.name).write_text(text, encoding="utf-8")
                got = find_decision_records(rej.parent)
                ok("REFUSED: the director's review of this very pipeline, the "
                   "real file from the tree, which discusses trellis and "
                   "licences throughout, authorises nothing", got == {}, str(got))
                # WHY THAT FILE AND NOT A SYNTHETIC ONE: it also quotes the
                # marker in a sentence explaining the format, so a plain
                # substring test would have been defeated by the same document
                # as the prose test it replaced. This asserts the fixture is
                # still the hard case; if the quote is ever edited out, this
                # goes red and says the rejecting case has gone soft.
                ok("and it is the HARD rejecting case: it quotes the marker in "
                   "prose, so a substring test would still accept it",
                   f"{DECISION_MARKER} trellis" in text)
            else:
                notes.append(f"{ruling} is absent - the REAL rejecting fixture "
                             "for the decision marker was SKIPPED, and a "
                             "synthetic one was NOT substituted")
            (fen / "decision-how-to-authorise.md").write_text(
                "# How to authorise a tool\n\nWrite this line:\n\n```\n"
                f"{DECISION_MARKER} trellis\n```\n\nThat is the whole "
                "mechanism, and it cites the weights licence.\n",
                encoding="utf-8")
            got = find_decision_records(fen.parent)
            ok("REFUSED: the marker inside a fenced code block, so a document "
               "EXPLAINING the format cannot authorise anything", got == {},
               str(got))
            (fen / "decision-mentions-it.md").unlink(missing_ok=True)
            (fen / "decision-how-to-authorise.md").write_text(
                "# Notes\n\nSomebody should write the line "
                f"`{DECISION_MARKER} trellis` into a real record one day.\n",
                encoding="utf-8")
            got = find_decision_records(fen.parent)
            ok("REFUSED: the marker with prose in front of it on the same "
               "line, which is how a document talks ABOUT the mechanism",
               got == {}, str(got))
            ok("and a repository path that does not exist yields no records "
               "rather than an exception",
               find_decision_records(dtmp / "nothing") == {})

        # The live tree, with its denominator. This asserts a property that
        # stays true whether or not a record exists yet, so writing the real
        # TRELLIS record cannot break the tool: whatever it returns must be
        # backed by a marker actually present at the start of a line.
        live = find_decision_records(repo)
        scanned = sum(len(list(repo.glob(g))) for g in DECISION_GLOBS)
        backed = all(DECISION_MARKER_RE.search(_FENCE_RE.sub(
            "", (repo / f).read_text(encoding="utf-8", errors="replace")))
            for f in live.values())
        ok(f"over the live tree, every authorisation is backed by a real marker "
           f"({scanned} decision documents scanned, {len(live)} tool(s) "
           f"authorised: {'/'.join(sorted(live)) or 'none'})",
           scanned > 0 and backed, str(live))
        att = write_attribution(out, man)
        doc = json.loads(pathlib.Path(att).read_text())
        ok("the attribution file is written beside the meshes with both counts",
           doc["items_attributed"] == 3 and doc["items_in_batch"] == 3,
           str(doc.get("items_attributed")))

    # -- H. the seams that cannot be executed here --------------------------
    print("\nH. the seams: Blender, the .bat files, the formatting law")
    bl = here / "blender/clean_lod.py"
    src = bl.read_text(encoding="utf-8")
    try:
        compile(src, str(bl), "exec")
        ok("the Blender script compiles", True)
    except SyntaxError as e:                                     # noqa: BLE001
        ok("the Blender script compiles", False, str(e))
    import ast
    tree = ast.parse(src)
    accepted = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    accepted.add(k.value)
    # Every flag the driver emits must be one the script's parser knows. One
    # renamed flag between these two files is a whole night lost, and it is the
    # only thing about an unrunnable script that CAN be checked from here.
    driver = pathlib.Path(__file__).read_text(encoding="utf-8")
    emitted = set(re.findall(r'"(--[a-z-]+)"', driver.split("def blender_clean")[1]
                             .split("def trellis_mesh")[0]))
    emitted -= {"--background", "--factory-startup", "--python"}
    unknown = {f for f in emitted if f[2:] not in accepted}
    ok("every flag the driver passes to Blender is one the script accepts",
       not unknown, f"unknown: {sorted(unknown)}; script knows {sorted(accepted)}")
    ns = {}
    exec(compile(src.split("def ensure_addon")[0], "clean_lod", "exec"), ns)
    parsed = ns["parse_args"](["--in", "a", "--out-dir", "b", "--id", "c",
                               "--result", "d", "--lods", "LOD0=1.0"])
    ok("the Blender arg parser accepts the driver's real argument list",
       parsed["in"] == "a" and parsed["lods"] == "LOD0=1.0", str(parsed))
    refuses("and refuses a flag it does not know",
            lambda: ns["parse_args"](["--in", "a", "--out-dir", "b", "--id", "c",
                                      "--result", "d", "--nonsense", "x"]),
            "unknown flag")
    refuses("and refuses a missing required flag",
            lambda: ns["parse_args"](["--in", "a"]), "required")

    bat = (here / "1 MAKE THE PROPS.bat").read_text(encoding="utf-8", errors="replace")
    ok("the .bat guards git against opening an editor", "GIT_EDITOR" in bat)
    codes = [EXIT_DISK, EXIT_SETUP, EXIT_ALL_FAILED, EXIT_CANNOT_RUN,
             EXIT_STOPPED, EXIT_LICENCE, EXIT_SPEC]
    missing_codes = [c for c in codes if f'"{c}"' not in bat]
    ok("the .bat has a paragraph for every exit code this file can return",
       not missing_codes, f"unexplained: {missing_codes}")
    ok("the .bat names the kill switch by the same path the code checks",
       "production\\STOP" in bat and 'STOP").exists()' in driver)
    for named in ("probe-tools.ps1", "meshgen.py",
                  "tools\\imagegen\\probe-machine.ps1"):
        ok(f"the .bat points at a file that exists: {named}",
           named in bat and (here / named.split("\\")[-1]).exists()
           or (repo / named.replace("\\", "/")).exists(), named)
    # EVERY PATH THIS FILE CITES MUST EXIST, and the check is UNCONDITIONAL.
    # trellis_mesh refused with a sentence pointing at tools/meshgen/README.md
    # while no such file existed, and the README check here was written as
    # `if it exists` - so the absence was silent, which is a citation to
    # nothing certified by a check that skipped itself. Generalised past the
    # one file, because the next false citation will be to a different one.
    cited = sorted(set(re.findall(r"tools/meshgen/[A-Za-z0-9_.-]+", driver)))
    missing = [c for c in cited if not (repo / c).exists()]
    ok(f"every path meshgen.py cites in its own messages exists "
       f"({len(cited)} cited, {len(missing)} missing)", not missing, str(missing))
    readme = (here / "README.md").read_text(encoding="utf-8", errors="replace") \
        if (here / "README.md").exists() else ""
    ok("and the README says what trellis_mesh's refusal promises it says: "
       "the install steps and upstream's own Linux-only warning",
       "setup.sh" in readme and "tested only on Linux" in readme,
       f"{len(readme)} chars")

    probe_bat = (here / "2 JUST LOOK AT THIS PC (one minute).bat").read_text(
        encoding="utf-8", errors="replace")
    ok("the look-only .bat sets the variable the main one reads",
       "LEDGER_MESHGEN_PROBE_ONLY" in probe_bat
       and "LEDGER_MESHGEN_PROBE_ONLY" in bat)
    ok("and calls the main one rather than copying it",
       "1 MAKE THE PROPS.bat" in probe_bat)

    # THE FORMATTING LAW (binding since 31 Aug): no em-dashes in anything
    # written from that date. This file, the specs, the .bat files and the
    # Blender script are all new, so all of them are in scope.
    ours = [pathlib.Path(__file__), bl, here / "1 MAKE THE PROPS.bat",
            here / "2 JUST LOOK AT THIS PC (one minute).bat",
            here / "probe-tools.ps1", here / "specs/props-local-01.json",
            here / "specs/props-trellis-01.json",
            here / "specs/prop-images-01.json", here / "README.md"]
    # A MISSING SHIPPED FILE IS A FINDING, NOT AN EXCEPTION. Reading the list
    # unconditionally is the point (the README's absence used to be silent),
    # but an unguarded read_text here ends the whole selftest in a stack trace
    # and takes the other 99 results with it. So the absence is counted and
    # named, and the formatting sweep says how many files it actually read.
    absent = [p.name for p in ours if not p.exists()]
    ok(f"every one of the {len(ours)} files this pipeline ships is present",
       not absent, "ABSENT: " + str(absent))
    dashed = [p.name for p in ours if p.exists()
              and "\u2014" in p.read_text(encoding="utf-8", errors="replace")]
    ok(f"no em-dashes in the {len(ours) - len(absent)} shipped files READ "
       f"({len(absent)} absent, not read)", not dashed, str(dashed))

    print("")
    for n in notes:
        print(f"  note: {n}")
    print(f"\nmeshgen selftest: {passed} passed, {failed} failed, "
          f"{passed + failed} checks run")
    print("  NOT COVERED HERE, and it is the expensive half: TRELLIS, Blender "
          "and both .bat files never execute in this container. No GPU, no "
          "Blender, no Windows, no PowerShell. The first run on Jafar's PC is "
          "their accepting case.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
