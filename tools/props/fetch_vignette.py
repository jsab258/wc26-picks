#!/usr/bin/env python3
"""The vignette's CC0 surface fetch: pick here, transfer there.

    python3 tools/props/fetch_vignette.py --plan       # no network, runs anywhere
    python3 tools/props/fetch_vignette.py --probe      # needs the host: ask, do not download
    python3 tools/props/fetch_vignette.py --fetch      # needs the host: take the plan
    python3 tools/props/fetch_vignette.py --verdict    # what landed, as a committed file
    python3 tools/props/fetch_vignette.py --staged-files
    python3 tools/props/fetch_vignette.py --selftest

THE MACHINE THAT RUNS THE NETWORK MODES IS Jafar's PC, THROUGH
.github/workflows/ledger-vignette-fetch.yml, and no click of his is needed:
a self-hosted runner labelled `ledger-pc` has been up continuously and three
workflows already reach it. Touching production/d1-probe/FETCH-VIGNETTE runs
this file there.

WHY --verdict AND --staged-files LIVE HERE RATHER THAN IN THAT WORKFLOW.
Measurement arithmetic and formatting belong where the tests run: a formatter
written into a YAML `run:` block ships UNRUN, and an unrun formatter printing a
plausible string is the silent-instrument failure this project has a standing
rule about. So the workflow supplies only the step outcomes and the commit sha,
and everything that counts, measures or formats is here, under --selftest.

WHY THE MODES SPLIT WHERE THEY DO. Measured 2026-09-01 rather than assumed:
ambientcg.com, api.polyhaven.com and api.sketchfab.com all answer CONNECT 403
at this container's egress proxy, whose README says to report a policy denial
and not route around it. So the machine that can reach the library does the
transferring and this container does the deciding, which is also the cheaper
half: `--plan` resolves every target against the catalogue already committed
at tools/citypack/catalogue.json and costs no run at all.

WHAT --probe IS FOR, AND IT IS THE HALF THAT PAYS. The committed catalogue is
a complete list of ambientCG MATERIALS and nothing else, so an absence in it
is evidence about materials and about nothing else. AsphaltDamageSet001 is on
disk in this repo, came from ambientCG, and is not in that file. Two of the
five bill-of-materials lines came back absent from the material list, and
neither can be called a real gap until the other types have been asked. A
probe run pulls every type at once and writes it down, because the voice
pipeline spent fifteen runs guessing at a corpus it could have asked once.

NOTHING HERE DELETES. Files are written under production/assets/vignette and
that directory is never cleaned by this tool; a cleanup glob one directory too
wide has already cost this project sixteen characters' worth of reviewed
content in one run.
"""
import argparse
import io
import json
import os
import pathlib
import struct
import sys
import time
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = ROOT / "production" / "specs" / "vignette-fetch-01.json"
CATALOGUE = ROOT / "tools" / "citypack" / "catalogue.json"
PROBE_OUT = ROOT / "tools" / "props" / "ambientcg-types.json"
DEST = ROOT / "production" / "assets" / "vignette" / "surfaces"
VERDICT = ROOT / "production" / "assets" / "vignette" / "fetch-verdict.txt"

API = "https://ambientcg.com/api/v2/full_json"

# The types ambientCG publishes, asked one at a time so a count of zero for
# one type cannot be confused with the endpoint failing for all of them.
TYPES = ["Material", "Decal", "Atlas", "3DModel", "HDRI", "Substance",
         "Terrain", "Brush", "PlainTexture"]

# The open questions --probe exists to close, as id substrings. Kept as data
# so the answer lands in a committed file rather than in a log tail this
# environment cannot read past.
QUESTIONS = ["pebble", "roughcast", "stucco", "render", "dash",
             "tarmac", "patch", "repair", "crack", "damage",
             "shutter", "corrugat", "asphalt", "paving", "pavement"]

# Every map channel worth keeping, and the name each lands under. NormalGL and
# not NormalDX: OpenGL tangent space is green-up, and the DX map embosses every
# mortar line the wrong way. AmbientOcclusion and Displacement are kept HERE
# and deliberately not in CityPack, whose loader looks only for _n and _r --
# see the consumer_warning on A2 in the spec.
MAPS = {"color": "Color", "normalgl": "NormalGL", "roughness": "Roughness",
        "ambientocclusion": "AmbientOcclusion", "displacement": "Displacement"}

CC0_TEXT = "CC0 1.0 Universal"


def _citypack():
    """Borrow the download helpers rather than growing a second copy.

    One idea, two implementations is this project's most repeated fault, and
    fetch_textures.py's get/sizes_of/link_for have already survived three
    rounds of the ambientCG API being wrong in a new way."""
    sys.path.insert(0, str(ROOT / "tools" / "citypack"))
    import fetch_textures                                        # noqa: E402
    return fetch_textures


def load_spec():
    return json.loads(SPEC.read_text(encoding="utf-8"))


def image_dims(blob):
    """Width, height and channel count from the file's own header.

    The bill of materials' dims policy is measured at ingest, never invented,
    so the manifest carries what the bytes say and not what a page claimed."""
    if blob[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", blob[16:24])
        depth, colour = blob[24], blob[25]
        ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(colour, 0)
        return int(w), int(h), ch
    if blob[:2] == b"\xff\xd8":
        i = 2
        while i < len(blob) - 9:
            if blob[i] != 0xFF:
                i += 1
                continue
            m = blob[i + 1]
            if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", blob[i + 5:i + 9])
                return int(w), int(h), blob[i + 9]
            if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
                i += 2
                continue
            i += 2 + struct.unpack(">H", blob[i + 2:i + 4])[0]
    return None


def plan(spec=None, catalogue=None):
    """Resolve every target against the committed catalogue. NO NETWORK.

    Prints one line per bill-of-materials line with its verdict and the
    evidence behind it, and ends with the denominator, because a hit rate
    without one cannot tell 'the library does not have it' from 'nobody
    looked'."""
    spec = spec or load_spec()
    if catalogue is None:
        if not CATALOGUE.exists():
            print(f"no {CATALOGUE.relative_to(ROOT)}, nothing to plan against")
            return 1
        catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    cat = {a["id"]: a for a in catalogue.get("assets", [])}
    print(f"plan, {len(cat)} ambientCG asset(s) in the committed catalogue, "
          f"note '{catalogue.get('note')}', type=Material ONLY")
    print("        an absence below is an absence from MATERIALS and from "
          "nothing else; --probe asks the other types\n")

    asked = resolved = missing = 0
    jobs = []
    for t in spec["targets"]:
        if t["verdict"] == "NOT-A-FETCH-LINE":
            print(f"  {t['bom_id']:<32} skipped, the BOM marks it BLOCKED")
            continue
        asked += 1
        if not t["assets"]:
            missing += 1
            why = t.get("probe_first") or t.get("blocked_on") or t["verdict"]
            print(f"  {t['bom_id']:<32} NO ASSET NAMED  ({t['verdict']})")
            print(f"  {'':<32}   next: {why if isinstance(why, str) else why[0]}")
            continue
        ok = True
        for a in t["assets"]:
            entry = cat.get(a["id"])
            if entry is None:
                print(f"  {t['bom_id']:<32} NOT IN CATALOGUE: {a['id']}")
                ok = False
                continue
            sizes = entry.get("sizes", [])
            if a["resolution"] not in sizes:
                print(f"  {t['bom_id']:<32} {a['id']} does NOT publish "
                      f"{a['resolution']}, it publishes {', '.join(sizes)}")
                ok = False
                continue
            print(f"  {t['bom_id']:<32} {a['id']} -> {a['logical']} "
                  f"@ {a['resolution']}  (publishes {len(sizes)}: {', '.join(sizes)})")
            jobs.append((t, a))
        resolved += 1 if ok else 0
        missing += 0 if ok else 1

    print(f"\n{asked} target(s) asked, {resolved} resolved to a named asset at "
          f"a published resolution, {missing} not")
    print(f"{len(jobs)} download job(s) planned")
    if resolved == 0:
        print("NOTHING RESOLVED, that is a finding about the plan, not a pass.")
        return 1
    return 0


def probe():
    """Ask the library everything at once. Downloads no asset."""
    ft = _citypack()
    out = {"_": "What ambientCG answered, per type, metadata only. Written by "
                "tools/props/fetch_vignette.py --probe on the machine that can "
                "reach the host. An id list, not a look: previews are recorded "
                "as URLs so a person picks by eye, once.",
           "types": {}, "questions": {}}
    every = {}
    for kind in TYPES:
        got, offset, limit, note = [], 0, 200, "complete"
        while offset < 6000:
            url = (API + f"?type={kind}&limit={limit}&offset={offset}"
                   + "&include=downloadData")
            try:
                data = json.loads(ft.get(url))
            except Exception as e:                               # noqa: BLE001
                note = f"stopped at offset {offset}: {type(e).__name__}: {e}"
                break
            assets = data.get("foundAssets") if isinstance(data, dict) else None
            if not assets:
                note = f"ended at offset {offset}"
                break
            fresh = 0
            for a in assets:
                aid = a.get("assetId") if isinstance(a, dict) else None
                if not aid or aid in every:
                    continue
                fresh += 1
                every[aid] = kind
                got.append({"id": aid, "type": kind, "sizes": ft.sizes_of(a),
                            "preview": f"https://ambientcg.com/view?id={aid}"})
            if fresh == 0 or len(assets) < limit:
                note = ("offset ignored, same page returned" if fresh == 0
                        else "complete")
                break
            offset += limit
        out["types"][kind] = {"count": len(got), "note": note, "assets": got}
        print(f"  {kind:<14} {len(got):5d} asset(s)  [{note}]")

    for q in QUESTIONS:
        hits = [{"id": a["id"], "type": a["type"], "sizes": a["sizes"],
                 "preview": a["preview"]}
                for t in out["types"].values() for a in t["assets"]
                if q in a["id"].lower()]
        out["questions"][q] = {"count": len(hits), "hits": hits[:40]}
        shown = ", ".join(h["id"] for h in hits[:8])
        more = f" (+{len(hits) - 8} more not shown)" if len(hits) > 8 else ""
        print(f"  ? {q:<12} {len(hits):4d}  {shown}{more}")

    PROBE_OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    total = sum(t["count"] for t in out["types"].values())
    print(f"\n{total} asset(s) across {len(TYPES)} type(s) -> "
          f"{PROBE_OUT.relative_to(ROOT)}")
    if total == 0:
        print("THE LIBRARY ANSWERED WITH NOTHING, a finding, not a pass.")
        return 1
    return 0


def fetch():
    """Take the plan. Every file measured and attributed by this same run."""
    spec = load_spec()
    if plan(spec) != 0:
        print("the plan does not resolve, nothing is downloaded")
        return 1
    ft = _citypack()
    DEST.mkdir(parents=True, exist_ok=True)
    manifest_path = DEST / "ATTRIBUTION.json"
    manifest = {"note": "Sources for every file in this directory, written by "
                        "the same run that wrote the files so the two cannot "
                        "drift apart. THIRD-PARTY.md carries the human copy "
                        "under the token 'vignette-surfaces'.",
                # THE RUN THAT WROTE IT, NAMED, and every surface carries the
                # same stamp. Without it a checkout's older manifest reads as
                # this run's answer, which is the provenance fault the whole
                # evidence channel exists to prevent: the manifest is a
                # TRACKED file, so it is restored by the checkout whether or
                # not this run downloaded anything.
                "run": run_stamp(),
                "surfaces": {}}
    if manifest_path.exists():
        try:
            manifest["surfaces"] = json.loads(
                manifest_path.read_text(encoding="utf-8")).get("surfaces", {})
        except ValueError:
            pass

    jobs = [(t, a) for t in spec["targets"] for a in t["assets"]]
    ids = [a["id"] for _, a in jobs]
    written, failed = 0, []
    for (t, a) in jobs:
        res = a["resolution"]
        links = ft.links_for([a["id"]], res)
        link = links.get(a["id"])
        if not link:
            failed.append(f"{a['id']}: no {res} link from the list endpoint")
            print(f"  {a['logical']:<14} FAILED no {res} link")
            continue
        if res.split("-")[0] not in link:
            failed.append(f"{a['id']}: link does not carry {res} ({link})")
            print(f"  {a['logical']:<14} REFUSED link is not {res}")
            continue
        try:
            blob = ft.get(link, timeout=300)
            files, dims = {}, {}
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                inside = z.namelist()
                for n in inside:
                    low = n.lower()
                    if not low.endswith((".jpg", ".png")):
                        continue
                    for key, name in MAPS.items():
                        if key in low and name not in files:
                            ext = ".jpg" if low.endswith(".jpg") else ".png"
                            data = z.read(n)
                            out = DEST / f"{a['logical']}_{name}{ext}"
                            out.write_bytes(data)
                            files[name] = out.name
                            dims[name] = image_dims(data)
                if "Color" not in files:
                    raise ValueError("no colour map among " + ", ".join(inside[:8]))
        except Exception as e:                                   # noqa: BLE001
            failed.append(f"{a['id']}: {type(e).__name__}: {e}")
            print(f"  {a['logical']:<14} FAILED {type(e).__name__}: {e}")
            continue
        manifest["surfaces"][a["logical"]] = {
            "assetId": a["id"], "source": "ambientCG", "licence": CC0_TEXT,
            "url": f"https://ambientcg.com/view?id={a['id']}",
            "resolution": res, "bomLine": t["bom_id"],
            # Per surface, not only per file: a manifest merged across runs
            # otherwise cannot say which entries THIS run banked, and
            # "N surfaces attributed" would count files nobody fetched today.
            "fetchedOnRun": run_stamp()["sha"],
            "files": files,
            "measured": {k: (f"{v[0]}x{v[1]}x{v[2]}ch" if v else "unreadable")
                         for k, v in dims.items()},
            "missing": [m for m in t.get("maps_wanted", []) if m not in files],
        }
        written += len(files)
        got = ", ".join(f"{k} {dims[k][0]}x{dims[k][1]}" if dims[k] else k
                        for k in files)
        gap = [m for m in t.get("maps_wanted", []) if m not in files]
        print(f"  {a['logical']:<14} ok {a['id']} {len(blob) / 1e6:.1f} MB "
              f"-> {got}" + (f"  NOT IN ZIP: {', '.join(gap)}" if gap else ""))

    manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"\n{len(ids)} asset(s) asked, {written} file(s) written, "
          f"{len(failed)} failure(s)")
    for f in failed:
        print(f"  FAILED {f}")
    if written == 0:
        print("NOTHING WAS WRITTEN, this run failed whatever is on disk.")
        return 1
    return 1 if failed else 0


def run_stamp():
    """Who wrote this, on which commit. GITHUB_SHA is set by Actions itself,
    needs no git on PATH and cannot be empty in a real run; 'local' is the
    honest answer anywhere else and is never mistaken for a commit."""
    sha = (os.environ.get("GITHUB_SHA") or "")[:7] or "local"
    return {"sha": sha, "at": int(time.time()),
            "by": "tools/props/fetch_vignette.py --fetch"}


def _manifest(dest=DEST):
    p = pathlib.Path(dest) / "ATTRIBUTION.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def _on_disk(dest=DEST):
    """Every image file actually sitting in the destination. The denominator
    for everything the manifest claims."""
    d = pathlib.Path(dest)
    if not d.exists():
        return []
    return sorted(p for p in d.iterdir()
                  if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png"))


def verdict(sha="local", steps="", dest=DEST, out=VERDICT):
    """The committed evidence file: what landed, measured from the bytes.

    LINE 1 NAMES THE COMMIT, values carry no spaces, whole-run numbers sit on
    the done line and per-surface numbers on the surface lines, because a grep
    across two lines merges two moments silently.

    IT RE-MEASURES rather than believing the manifest: every file is opened and
    its dimensions read from its own header, and a file on disk that the
    manifest does not name is reported as UNATTRIBUTED, which is the one
    failure this directory can have that nothing else would notice.
    """
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    man = _manifest(dest)
    disk = _on_disk(dest)
    stamp = (man or {}).get("run", {}) if isinstance(man, dict) else {}
    manifest_sha = stamp.get("sha", "none")
    fresh = (manifest_sha == sha and sha != "none")

    L = [f"# vignette surface fetch - {sha} @{int(time.time())}",
         "# Line 1 names the commit this was measured on. No spaces in any value.",
         "# Every number here is measured from the files on disk, not copied "
         "from the manifest.",
         ""]
    L.append(f"steps {steps or 'none-reported'}")
    L.append(f"manifestRun={manifest_sha} thisRun={sha} "
             f"manifestIsThisRun={'yes' if fresh else 'no'}")

    named, rows, total_bytes = set(), [], 0
    surfaces = (man or {}).get("surfaces", {}) if isinstance(man, dict) else {}
    this_run = 0
    for logical, s in sorted(surfaces.items()):
        files = s.get("files", {})
        got = []
        for kind, fname in sorted(files.items()):
            named.add(fname)
            p = pathlib.Path(dest) / fname
            if not p.exists():
                got.append(f"{kind}/MISSING-FROM-DISK")
                continue
            blob = p.read_bytes()
            total_bytes += len(blob)
            dims = image_dims(blob)
            got.append(f"{kind}/{dims[0]}x{dims[1]}x{dims[2]}ch"
                       if dims else f"{kind}/UNREADABLE-HEADER")
        if s.get("fetchedOnRun") == sha:
            this_run += 1
        rows.append(f"surface {logical} id={s.get('assetId', 'NONE')} "
                    f"licence={(s.get('licence') or 'NONE').replace(' ', '-')} "
                    f"res={s.get('resolution', 'NONE')} bom={s.get('bomLine', 'NONE')} "
                    f"run={s.get('fetchedOnRun', 'unstamped')} "
                    f"files={len(files)} measured={','.join(got) or 'none'}")
    L.extend(rows)

    unattributed = [p.name for p in disk if p.name not in named]
    L.append(f"filesOnDisk={len(disk)} filesNamedByManifest={len(named)} "
             f"unattributed={len(unattributed)}")
    if unattributed:
        L.append("UNATTRIBUTED " + ",".join(sorted(unattributed)[:20])
                 + (f" (+{len(unattributed) - 20}-more-not-shown)"
                    if len(unattributed) > 20 else ""))

    if man is None:
        L.append("NOTHING MEASURED - no ATTRIBUTION.json exists under "
                 f"{pathlib.Path(dest).name}, so this run banked nothing and "
                 "no older file is being read as its answer.")
        L.append("done fetchVerdict=NOTHING-MEASURED surfaces=0 filesOnDisk="
                 f"{len(disk)} bytes=0 surfacesThisRun=0")
        out.write_text("\n".join(L) + "\n", encoding="utf-8")
        print("\n".join(L))
        return 1
    if not fresh:
        L.append("STALE - the manifest on disk was written by run "
                 f"{manifest_sha}, not by {sha}. Nothing here was measured on "
                 "this commit; do not read it as this run's answer.")
    L.append(f"done fetchVerdict="
             f"{'BANKED' if (fresh and this_run and not unattributed) else 'NOT-BANKED'} "
             f"surfaces={len(surfaces)} surfacesThisRun={this_run} "
             f"filesOnDisk={len(disk)} filesNamedByManifest={len(named)} "
             f"unattributed={len(unattributed)} bytes={total_bytes}")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0 if (fresh and this_run and not unattributed) else 1


def staged_files(sha="local", dest=DEST, out=VERDICT):
    """The paths the workflow may `git add`, one per line, BY NAME.

    Derived from the manifest, so a file that arrived without attribution is
    never staged: the obligation and the bytes travel together or not at all.
    A stale manifest stages nothing except the verdict, which is what says the
    run measured nothing.
    """
    rel = pathlib.Path(out).relative_to(ROOT).as_posix()
    lines = [rel]
    man = _manifest(dest)
    if isinstance(man, dict) and man.get("run", {}).get("sha") == sha:
        d = pathlib.Path(dest)
        lines.append((d / "ATTRIBUTION.json").relative_to(ROOT).as_posix())
        for s in man.get("surfaces", {}).values():
            for fname in s.get("files", {}).values():
                if (d / fname).exists():
                    lines.append((d / fname).relative_to(ROOT).as_posix())
    for line in lines:
        print(line)
    return 0


def selftest():
    """Accepting case first, on the live spec and the live catalogue.

    The rejecting fixture is synthetic and names an id that exists nowhere, so
    doing the work this tool asks for can never break the tool."""
    bad = 0
    spec = load_spec()
    rc = plan(spec)
    print(f"\nACCEPT: the committed spec against the committed catalogue -> {rc}")
    if rc != 0:
        print("  FAIL: the live pair must plan cleanly"); bad = 1

    fake = {"targets": [{"bom_id": "fixture", "verdict": "PRESENT-BY-ID",
                         "assets": [{"id": "NoSuchAsset999",
                                     "resolution": "4K-JPG",
                                     "logical": "fixture"}]}]}
    rc = plan(fake)
    print(f"\nREJECT: an id that exists nowhere -> {rc}")
    if rc == 0:
        print("  FAIL: a missing id must not plan"); bad = 1

    cat = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    real = spec["targets"][0]["assets"][0]["id"]
    fake2 = {"targets": [{"bom_id": "fixture", "verdict": "PRESENT-BY-ID",
                          "assets": [{"id": real, "resolution": "16K-JPG",
                                      "logical": "fixture"}]}]}
    rc = plan(fake2, cat)
    print(f"\nREJECT: a real id at a resolution it does not publish -> {rc}")
    if rc == 0:
        print("  FAIL: an unpublished resolution must not plan"); bad = 1

    png = (b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + struct.pack(">II", 2048, 1024)
           + bytes([8, 2]))
    got = image_dims(png)
    print(f"\nMEASURE: a 2048x1024 RGB PNG header reads {got}")
    if got != (2048, 1024, 3):
        print("  FAIL: dims must come from the file's own header"); bad = 1

    # THE VERDICT, BOTH OUTCOMES, ON A SYNTHETIC DIRECTORY. The accepting
    # fixture is a real 2x1 PNG named by a manifest stamped with the run;
    # the rejecting fixtures are a directory with no manifest at all (which
    # must print the words NOTHING MEASURED rather than a clean zero) and a
    # file on disk that no manifest names, which is the one failure this
    # directory can have that nothing else in the project would see.
    import tempfile
    png = (b"\x89PNG\r\n\x1a\x0a" + b"\x00" * 8 + struct.pack(">II", 2, 1)
           + bytes([8, 2]))
    with tempfile.TemporaryDirectory() as d:
        dd = pathlib.Path(d) / "surfaces"
        dd.mkdir()
        out = pathlib.Path(d) / "fetch-verdict.txt"
        rc = verdict("aaaaaaa", "fetch=skipped", dd, out)
        text = out.read_text(encoding="utf-8")
        print(f"\nREJECT: an empty destination -> {rc}")
        if rc == 0 or "NOTHING MEASURED" not in text:
            print("  FAIL: a run that measured nothing must say so and fail"); bad = 1
        if "filesOnDisk=0" not in text:
            print("  FAIL: the zero must ship its denominator"); bad = 1

        (dd / "road_asphalt_Color.png").write_bytes(png)
        (dd / "ATTRIBUTION.json").write_text(json.dumps({
            "run": {"sha": "aaaaaaa"},
            "surfaces": {"road_asphalt": {
                "assetId": "Asphalt012", "licence": CC0_TEXT,
                "resolution": "4K-JPG", "bomLine": "A2_road_asphalt_maps_upgrade",
                "fetchedOnRun": "aaaaaaa",
                "files": {"Color": "road_asphalt_Color.png"}}}}), encoding="utf-8")
        rc = verdict("aaaaaaa", "fetch=0", dd, out)
        text = out.read_text(encoding="utf-8")
        print(f"\nACCEPT: one attributed, measured file -> {rc}")
        if rc != 0 or "fetchVerdict=BANKED" not in text:
            print("  FAIL: an attributed file measured on this run must pass"); bad = 1
        if "measured=Color/2x1x3ch" not in text:
            print("  FAIL: dims must be re-measured from the file's own header"); bad = 1
        if " " in text.split("surface road_asphalt ")[1].split("licence=")[1].split()[0]:
            print("  FAIL: no value may contain a space"); bad = 1

        rc = verdict("bbbbbbb", "fetch=0", dd, out)
        print(f"\nREJECT: the same directory read on a different commit -> {rc}")
        if rc == 0 or "STALE" not in out.read_text(encoding="utf-8"):
            print("  FAIL: a manifest from another run must not pass as this one"); bad = 1

        (dd / "stowaway_Color.png").write_bytes(png)
        rc = verdict("aaaaaaa", "fetch=0", dd, out)
        print(f"\nREJECT: a file on disk that no manifest names -> {rc}")
        if rc == 0 or "unattributed=1" not in out.read_text(encoding="utf-8"):
            print("  FAIL: an unattributed file must fail the verdict"); bad = 1

    print("\nselftest " + ("FAILED" if bad else "ok"))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true",
                    help="resolve targets against the committed catalogue, no network")
    ap.add_argument("--probe", action="store_true",
                    help="ask ambientCG for every type and the open questions")
    ap.add_argument("--fetch", action="store_true", help="take the plan")
    ap.add_argument("--verdict", action="store_true",
                    help="write the committed evidence file from what is on disk")
    ap.add_argument("--staged-files", action="store_true",
                    help="print, one per line, the paths the fetch attributed")
    ap.add_argument("--sha", default=(os.environ.get("GITHUB_SHA") or "")[:7] or "local",
                    help="the commit this run is measuring, 7 chars")
    ap.add_argument("--steps", default="",
                    help="step outcomes as key=value pairs, no spaces, "
                         "for example plan=0,probe=0,fetch=1,attribution=0")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.staged_files:
        return staged_files(a.sha)
    if a.verdict:
        return verdict(a.sha, a.steps)
    if a.probe:
        return probe()
    if a.fetch:
        return fetch()
    return plan()


if __name__ == "__main__":
    sys.exit(main())
