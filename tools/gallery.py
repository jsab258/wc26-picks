#!/usr/bin/env python3
"""THE GALLERY: the newest frames first, dated, ALL of them, as published files.

    python3 tools/gallery.py                  # write gallery.html + world.html
    python3 tools/gallery.py --selftest       # accepting case FIRST
    python3 tools/gallery.py --out <f> --world-out <f> --assets-dir <d>

WHAT IT IS. Jafar, 2026-09-06: "Add a gallery page beside the glance: the
latest frames and clips, biggest first, nothing else." AMENDED BY HIM ON
2026-09-09, item 2, verbatim: "The gallery shows the newest images first,
dated, all of them, not two embedded files." and "The town atlas from
art/atlas-01 belongs in the gallery as a world page, not on the map." Those
three sentences are the whole specification of this tool, and two of them
changed what it does:

  ORDER. Newest first is the ruled ORDER. Biggest first was the ruled LAYOUT
  and it survives as a layout (the newest picture is the hero, full width,
  the rest two to a row), because the newest picture is the hero either way.
  They are not the same rule and they are two checks: check_newest_first
  reads the dates off the rendered page in document order, check_biggest_first
  reads the widths the same way.

  ALL OF THEM, WHICH MEANT THE END OF EMBEDDING. Every picture used to be
  base64-embedded into the HTML, so the page's byte budget WAS the picture
  budget: on 2026-09-09 the run printed picturesShown=37/49-found
  notShown=12 pageBytes=1000108/1000000-budget, twelve pictures dropped for
  bytes and the page at 100 percent of its cap. It also took the whole site
  down: the publish workflow runs this tool's selftest as a gate, the
  accepting case (the live repository) went red on pageBytes, and runs 41 to
  48 published nothing at all. THE PICTURES ARE NOW FILES. The HTML carries
  relative <img src=...> into a directory this tool writes and names in a
  manifest the publisher reads, so the page is text (about 20 KB measured)
  and the picture count is bounded by the pictures, not by the bytes.

WHAT THE BUDGET IS NOW, AND WHAT IT IS NOT. The HTML is held to
tools/glance.py's PAGE_BYTE_CAP (250000, which its comment derives as two
seconds of a 1 Mbit/s link). That is a cap on TEXT and it has ten times the
headroom over the measured page. The PICTURES have no cap yet and this run
prints the series instead: every file's bytes, the total, and the file count.
A bound on that total would be a number nobody has measured, so it is printed
and not gated, and `loading="lazy"` on everything below the hero means the
phone fetches what he scrolls to rather than the whole set.

THE WORLD PAGE. world.html is the town atlas, read out of the art/atlas-01
branch WITHOUT merging it (git show <ref>:<path>), and it prints the commit it
read them at, so the page says which version of the atlas it shows. It is
separate from gallery.html on purpose and each says which it is: the gallery
is the latest frames from runs, newest first; the world page is the town as
drawn, grouped by subject, all from one commit, so it has no date order to
show.

THE LICENCE ALLOWLIST IS LAW, so the atlas ships through a rights table.
production/art/atlas-01/PROVENANCE.md and .../references/RIGHTS.md are the
authorities, they are read at the same commit as the pictures, and
RIGHTS_RULES below carries one row per family those two documents describe,
with the reason in the row. THE DEFAULT IS WITHHOLD: a file no row names is
not published and is counted as unclassified, so an atlas that grows cannot
quietly publish something nobody cleared. Every run prints cleared over
examined and the withheld count with its reasons, and the page says the same
thing where he can read it.

WHAT IT CANNOT SEE. Whether a picture is any good, whether it shows what the
brief says it shows, or whether it is the picture Jafar meant. It knows the
date, the bytes, the order and the rights row. It embeds no video: no video
file exists under the walked directories today (measured, and the count is
printed with its denominator every run), so "clips" is a printed zero and not
a claim that there are none.

EXIT CODES, distinct per outcome. 0 both pages are good. 1 a check failed or a
picture could not be published, and the pages were still written because a
stale gallery is worse than one that says what it holds. 2 nothing measured:
no image file at all under any walked directory. 3 the selftest failed. 4
tools/glance.py could not be imported.
"""
import argparse
import base64
import datetime
import fnmatch
import html
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

TOOL = "tools/gallery.py"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_NAME = "gallery.html"
WORLD_NAME = "world.html"
ASSETS_NAME = "gallery-img"
MANIFEST_NAME = "manifest.json"
GLANCE_LINK = ("index.html", "back to the glance")


def load_glance():
    """The phone-first bar, the image encoder and the git helper are
    tools/glance.py's, imported rather than copied. tools/map.py does the same
    thing for the same reason: two implementations of "how wide is a phone"
    drift, and the copy nobody looks at is the one that keeps passing."""
    p = ROOT / "tools" / "glance.py"
    spec = importlib.util.spec_from_file_location("glance", p)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    GLANCE = load_glance()
except Exception as exc:                                         # noqa: BLE001
    # AS A PROGRAM this is exit 4; AS AN IMPORT it is an ImportError. Calling
    # sys.exit() here would raise SystemExit inside whatever imported this
    # file, and tools/morning-brief.py imports it: a missing sibling would
    # then kill the brief writer instead of being reported as a source it
    # could not read.
    if __name__ == "__main__":
        sys.stderr.write("gallery: tools/glance.py could not be imported "
                         "(%s); refusing to reimplement the encoder and the "
                         "phone bar\n" % exc)
        sys.exit(4)
    raise ImportError("tools/glance.py could not be imported: %s" % exc)

CAPSAY = None
try:
    _spec = importlib.util.spec_from_file_location(
        "capsay", str(ROOT / "tools" / "capsay.py"))
    CAPSAY = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(CAPSAY)
except Exception:                                                # noqa: BLE001
    CAPSAY = None
NOTHING = CAPSAY.NOTHING_MEASURED if CAPSAY else "nothing-measured"
NOTHING_WORDS = "nothing measured"

# WHERE THE PICTURES ARE, measured rather than assumed: on 2026-09-09 there
# were 49 image files, 18 png under production/d1-probe (the Unreal frames,
# the newest in the repository) and 31 jpg under game-design/sim-shots;
# production/frames exists in tools/glance.py's list and holds nothing yet. A
# directory that does not exist is counted and named, never silently skipped.
SOURCES = ("production/d1-probe", "production/frames", "game-design/sim-shots")
IMAGE_SUFFIXES = GLANCE.IMAGE_SUFFIXES
# NOT PUBLISHED, COUNTED. The day a clip lands, this prints a non-zero beside
# its denominator and the foot line says how many were not shown, rather than
# the page quietly being frames only for ever.
CLIP_SUFFIXES = (".mp4", ".webm", ".gif", ".mov")

# THE WIDTHS ARE THE GLANCE'S ARITHMETIC, NOT NEW NUMBERS. 780 is twice the
# 390 logical px of the phones in use, which is tools/glance.py's stated figure
# and its IMAGE_WIDTH_PX. Every FILE is written at that one width, because one
# file per picture is what stops the publish set doubling; the hero is laid out
# across the page and the rest two to a row, and `data-w` carries the slot each
# is laid out in so check_biggest_first can read the layout off the page.
FILE_WIDTH_PX = GLANCE.IMAGE_WIDTH_PX
COLUMNS = 2
HERO_WIDTH_PX = FILE_WIDTH_PX
REST_WIDTH_PX = FILE_WIDTH_PX // COLUMNS

# THE HTML BUDGET IS THE GLANCE'S, BECAUSE THIS PAGE IS NOW TEXT. The pictures
# are files, so they are not in this number; the measured page is about 20 KB
# against this cap. The picture bytes are printed as a series instead of gated,
# because no run has yet read what a sensible total is.
PAGE_BYTE_CAP = GLANCE.PAGE_BYTE_CAP
MAX_DECLARED_WIDTH_PX = GLANCE.MAX_DECLARED_WIDTH_PX
# HOW MANY PICTURES LOAD EAGERLY. The hero and nothing else: everything below
# it is lazy, so a phone on a weak link pays for what he scrolls to. Printed
# every run with its denominator.
EAGER_PICTURES = 1

# A REAL 8 by 8 PNG, 77 bytes, for the selftest to plant. Synthetic to the last
# byte: a rejecting fixture pinned to a real frame breaks the day somebody
# renders a better frame, which is the failure instruments.md names.
FIXTURE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAFElEQVR4nGPUsIliwAaYsIoO"
    "WgkAmcoAzpfIFcsAAAAASUVORK5CYII=")


# --------------------------------------------------------------- the pictures

def committed_epochs(root, dirs):
    """{repo-relative path: commit epoch} for every image git knows about.

    COMMIT TIME, NOT FILE TIME, for the reason tools/glance.py gives: in a
    fresh checkout every file's mtime is the moment of the clone, so an mtime
    sort would order the gallery by whatever the filesystem wrote last. The
    newest commit touching a path wins, which is what "latest" means here.
    """
    out = {}
    if not dirs:
        return out
    log = GLANCE.git(root, "log", "--format=commit %ct", "--name-only", "-300",
                     "--", *dirs)
    when = None
    for line in log.splitlines():
        if line.startswith("commit "):
            when = int(line.split()[1])
            continue
        rel = line.strip()
        if when is None or not rel or rel in out:
            continue
        if pathlib.Path(rel).suffix.lower() in IMAGE_SUFFIXES:
            out[rel] = when
    return out


def find_pictures(root):
    """(shots newest-first, reading) where reading carries every denominator.

    The reading is a dict and not a sentence, so the caller decides what to
    print where: whole-run numbers on the done line, per-picture numbers on the
    picture's own line. tools/morning-brief.py reads this function rather than
    walking the directories a second time, so the returned keys are a
    contract."""
    root = pathlib.Path(root)
    present = [d for d in SOURCES if (root / d).is_dir()]
    absent = [d for d in SOURCES if d not in present]
    files, clips = [], []
    for d in present:
        for p in sorted((root / d).rglob("*")):
            if not p.is_file():
                continue
            suf = p.suffix.lower()
            if suf in IMAGE_SUFFIXES:
                files.append(p)
            elif suf in CLIP_SUFFIXES:
                clips.append(p)
    epochs = committed_epochs(root, present)
    shots, by_commit = [], 0
    for p in files:
        rel = p.relative_to(root).as_posix()
        if rel in epochs:
            when, how = epochs[rel], "commit"
            by_commit += 1
        else:
            when, how = int(p.stat().st_mtime), "mtime"
        shots.append({"path": p, "rel": rel, "when": when, "dated": how})
    # NEWEST FIRST, and the tie-break is the path so the order is stable: two
    # frames committed in one commit share an epoch, and an unstable order
    # would make two runs of the same tree produce different pages.
    shots.sort(key=lambda s: (-s["when"], s["rel"]))
    return shots, {
        "dirsWalked": len(present), "dirsNamed": len(SOURCES),
        "dirsAbsent": absent, "imagesFound": len(shots),
        "datedByCommit": by_commit, "datedByMtime": len(shots) - by_commit,
        "clipsFound": len(clips),
        "clipSuffixes": len(CLIP_SUFFIXES),
    }


# ----------------------------------------------------------------- the atlas

ATLAS_DIR = "production/art/atlas-01"
# THE REF NAMES TRIED, IN ORDER, and the one that answered is printed. A clone
# that never fetched the art branch has none of them, which is a measured
# absence and not a failure of this tool: the world page then says the words
# nothing measured and the gallery is unaffected.
ATLAS_REFS = ("origin/art/atlas-01", "refs/remotes/origin/art/atlas-01",
              "art/atlas-01")
PROVENANCE_DOC = ATLAS_DIR + "/PROVENANCE.md"
RIGHTS_DOC = ATLAS_DIR + "/references/RIGHTS.md"
ALLOWLIST_DOC = "ledger-v2/research/license-allowlist.md"

# THE RIGHTS TABLE. One row per family PROVENANCE.md and references/RIGHTS.md
# describe, read on 2026-09-09 at origin/art/atlas-01 (8ce8173). FIRST MATCH
# WINS and THE DEFAULT IS WITHHOLD, so a file no row names is not published.
# The pattern is matched against the path BELOW production/art/atlas-01.
#
# WHY THE CONCEPTS ARE WITHHELD, which is the row that will be argued with.
# PROVENANCE.md's own first table row says they came from the "Built-in OpenAI
# image_gen service" and names no licence for the output; the allowlist has no
# 2D image entry at all (grepped, 2026-09-09: items 1 to 6 are voices, 3D,
# characters, faces, music and geodata) and no decision record in
# ledger-v2/respec/decision-register/ names that tool. PROCESS 1 of the
# allowlist is "every asset and generated output carries a license tag;
# untagged fails the license gate", so these fail it. They are 8 of the 18
# withheld and the page says so; a decision record naming the tool's licence is
# what would move them, and that is a ruling, not a change to this table.
RIGHTS_RULES = (
    ("previews/reference-hull.png", False,
     "it embeds the dated third-party reference evidence (a 1981 photograph "
     "under another person's copyright and council map extracts) that "
     "references/RIGHTS.md says has no established reuse licence",
     RIGHTS_DOC),
    ("previews/reference-kasbah.png", False,
     "it embeds the council statement's photograph and map extract, and "
     "references/RIGHTS.md states the same research-only boundary applies to "
     "the embedded copies", RIGHTS_DOC),
    ("references/*", False,
     "references/RIGHTS.md calls this whole directory reference evidence and "
     "not a cleared library, and establishes no reuse licence for the "
     "photographs and map extracts in it", RIGHTS_DOC),
    ("concepts/*", False,
     "PROVENANCE.md names the generating tool and no licence for its output, "
     "the licence allowlist has no entry for 2D image generation and no "
     "decision record names the tool, so the allowlist's own process rule "
     "fails an untagged output", ALLOWLIST_DOC),
    ("previews/atlas-overview.png", True,
     "original authored coordinates in data/atlas.json, drawn and rasterised "
     "in this repository", PROVENANCE_DOC),
    ("previews/gameplay-overlay.png", True,
     "original authored coordinates in data/atlas.json, drawn and rasterised "
     "in this repository", PROVENANCE_DOC),
    ("previews/hook-detail.png", True,
     "original authored coordinates in data/atlas.json, drawn and rasterised "
     "in this repository", PROVENANCE_DOC),
    ("previews/district-*-plan.png", True,
     "original authored coordinates in data/atlas.json, drawn and rasterised "
     "in this repository", PROVENANCE_DOC),
    ("previews/mickeys-*.png", True,
     "drawn plans and elevations from the pub's own JSON, commission work in "
     "this repository", PROVENANCE_DOC),
    ("previews/fascia_mickeys-*.png", True,
     "an original layout proof in system fonts; RIGHTS.md asks for the "
     "lettering to be outlined and its export rights checked before it ships "
     "as a game texture, which is a condition on the texture and not on "
     "showing the proof", RIGHTS_DOC),
    ("previews/mesh-*.png", True,
     "projections of the studio's CC0-1.0 base mesh files, which the licence "
     "allowlist names as ship-safe", RIGHTS_DOC),
    ("previews/target-*.png", True,
     "original SVG design studies rasterised in this repository",
     PROVENANCE_DOC),
    ("previews/evidence-revisions.png", True,
     "original SVG design studies rasterised in this repository",
     PROVENANCE_DOC),
    ("previews/town-work-and-home.png", True,
     "original SVG design studies rasterised in this repository",
     PROVENANCE_DOC),
    ("previews/hook-uses.png", True,
     "original SVG design studies rasterised in this repository",
     PROVENANCE_DOC),
    ("previews/asset-audit-phone.png", True,
     "a headless browser screenshot of this package's own HTML",
     PROVENANCE_DOC),
)
UNCLASSIFIED_REASON = ("no row of this tool's rights table names it, and the "
                       "default is to withhold rather than to publish "
                       "something nobody cleared")

# THE WORLD PAGE'S GROUPS, in reading order. The atlas is all one commit, so it
# has no date order to show and is grouped by subject instead; the last group
# catches anything the others do not, so a new cleared picture is shown rather
# than silently dropped, and its count is printed.
WORLD_GROUPS = (
    ("the town, as drawn",
     ("previews/atlas-overview.png", "previews/gameplay-overlay.png",
      "previews/town-work-and-home.png")),
    ("the seven districts", ("previews/district-*-plan.png",)),
    ("the Hook, in detail", ("previews/hook-*.png",)),
    ("Mickey's, the pub", ("previews/mickeys-*.png",
                           "previews/fascia_mickeys-*.png")),
    ("the props, projected from the studio meshes", ("previews/mesh-*.png",)),
    ("the surfaces being matched", ("previews/target-*.png",)),
    ("the rest of the atlas", ("*",)),
)


def git_out(root, *args):
    """git, returning (stdout, ok). tools/glance.py's git() swallows the
    failure into an empty string, which cannot tell "the ref is absent" from
    "the file is empty", and those are different facts here."""
    try:
        p = subprocess.run(["git", "-C", str(root), *args],
                           capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return b"", False
    return p.stdout, p.returncode == 0


def atlas_ref(root):
    """(ref, sha, refsTried) for the art branch, or (None, None, n)."""
    for ref in ATLAS_REFS:
        out, ok = git_out(root, "rev-parse", "--verify", "--quiet", ref)
        if ok and out.strip():
            return ref, out.decode().strip(), len(ATLAS_REFS)
    return None, None, len(ATLAS_REFS)


def rights_of(rel_in_atlas):
    """(cleared, reason, source, ruleIndex). FIRST MATCH WINS, DEFAULT WITHHOLD.

    Pure, so the selftest exercises both outcomes without a git ref: the
    accepting fixture is the live list of atlas paths and the rejecting one is
    a synthetic name no row can match (instruments.md)."""
    for i, (pattern, cleared, reason, source) in enumerate(RIGHTS_RULES):
        if fnmatch.fnmatch(rel_in_atlas, pattern):
            return cleared, reason, source, i
    return False, UNCLASSIFIED_REASON, TOOL, None


def atlas_pictures(root):
    """(entries, reading). Entries are the CLEARED atlas pictures in world
    order; the reading carries cleared over examined, the withheld rows with
    their reasons, the ref and the sha, so no zero here is without its
    denominator."""
    ref, sha, tried = atlas_ref(root)
    reading = {"ref": ref, "sha": sha, "refsTried": tried, "examined": 0,
               "cleared": 0, "withheld": [], "unclassified": 0,
               "rightsDocs": 0, "rightsDocsAsked": 2, "groups": 0,
               "ungrouped": 0, "bytes": 0}
    if ref is None:
        return [], reading
    out, ok = git_out(root, "ls-tree", "-r", "--name-only", ref, "--",
                      ATLAS_DIR)
    if not ok:
        reading["ref"] = None
        return [], reading
    names = [n for n in out.decode("utf-8", "replace").splitlines() if n]
    # THE TWO RIGHTS DOCUMENTS ARE READ AT THE SAME COMMIT AS THE PICTURES, and
    # counted: a rights table quoting documents this run never opened is a
    # claim, not a check.
    for doc in (PROVENANCE_DOC, RIGHTS_DOC):
        blob, got = git_out(root, "show", "%s:%s" % (ref, doc))
        if got and blob.strip():
            reading["rightsDocs"] += 1
    images = [n for n in names
              if pathlib.Path(n).suffix.lower() in IMAGE_SUFFIXES]
    cleared = []
    for n in sorted(images):
        rel = n[len(ATLAS_DIR) + 1:]
        reading["examined"] += 1
        ok_rights, reason, source, rule = rights_of(rel)
        if ok_rights:
            reading["cleared"] += 1
            cleared.append({"rel": n, "inAtlas": rel, "reason": reason,
                            "source": source})
        else:
            reading["withheld"].append({"inAtlas": rel, "why": reason,
                                        "source": source})
            if rule is None:
                reading["unclassified"] += 1
    # GROUPED BY SUBJECT, first matching group wins, and the last group takes
    # whatever the others did not so nothing cleared is dropped.
    groups, placed = [], set()
    for title, patterns in WORLD_GROUPS:
        rows = [e for e in cleared
                if e["inAtlas"] not in placed
                and any(fnmatch.fnmatch(e["inAtlas"], p) for p in patterns)]
        for e in rows:
            placed.add(e["inAtlas"])
        if rows:
            groups.append({"title": title, "rows": rows})
    reading["groups"] = len(groups)
    reading["ungrouped"] = len(cleared) - len(placed)
    entries = []
    for g in groups:
        for e in g["rows"]:
            e["group"] = g["title"]
            entries.append(e)
    reading["groupRows"] = groups
    return entries, reading


def atlas_blob(root, ref, rel):
    blob, ok = git_out(root, "show", "%s:%s" % (ref, rel))
    return blob if ok else None


# -------------------------------------------------------------- the publisher

def publish_bytes(dest_dir, name, blob):
    dest_dir.mkdir(parents=True, exist_ok=True)
    p = dest_dir / name
    p.write_bytes(blob)
    return len(blob)


def encode_to_bytes(path_or_blob, suffix):
    """The FILE BYTES for one picture, at FILE_WIDTH_PX, through the glance's
    encoder and not a second copy of it.

    tools/glance.py owns "resize to a phone width and pick the first quality
    that fits a budget". It returns base64 because it was written to embed, so
    this decodes it: the resizing, the width and the quality ladder stay in the
    one place that has them. The budget passed is deliberately enormous, so the
    encoder takes its best quality: the byte pressure that used to live here is
    gone now that the picture is a file rather than part of the page.
    """
    import tempfile
    tmp = None
    try:
        if isinstance(path_or_blob, (bytes, bytearray)):
            tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            tmp.write(path_or_blob)
            tmp.close()
            path = pathlib.Path(tmp.name)
        else:
            path = path_or_blob
        saved = GLANCE.IMAGE_WIDTH_PX
        try:
            GLANCE.IMAGE_WIDTH_PX = FILE_WIDTH_PX
            b64, mime, _n, how, quality = GLANCE.encode_image(path, 1 << 40)
        finally:
            GLANCE.IMAGE_WIDTH_PX = saved
        blob = base64.b64decode(b64)
        if quality is None:
            # NO RESIZER: the glance hands back the original bytes, so the
            # published file keeps the original suffix and the run says the
            # pictures were not resized rather than naming a jpeg that is a png.
            return blob, suffix.lower().lstrip("."), None, how
        return blob, "jpg", quality, how
    finally:
        if tmp is not None:
            try:
                pathlib.Path(tmp.name).unlink()
            except OSError:
                pass


def safe_stem(rel):
    """A file name a URL can carry, derived from the source path so the
    published name still says where the picture came from. The source suffix is
    dropped because the published suffix is decided by what the encoder wrote,
    and a name ending .png.jpg is a lie about one of the two."""
    rel = re.sub(r"\.(?:png|jpe?g)$", "", rel, flags=re.I)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", rel.replace("/", "-"))
    return re.sub(r"-+", "-", stem).strip("-.")[:90] or "picture"


def publish_pictures(shots, dest_dir, prefix, source=None, root=None,
                     ref=None):
    """Write every picture as a file. Returns (kept, series, reading).

    NOTHING IS DROPPED FOR BYTES ANY MORE, which is the whole point of the
    change: the only way a picture does not arrive is that it could not be read
    or encoded, and that row says which and why with its own reason. Per
    picture numbers are on the picture's row; whole-run numbers are in the
    reading.
    """
    kept, series = [], []
    total = 0
    for i, s in enumerate(shots):
        name = "%s-%03d-%s" % (prefix, i + 1, safe_stem(
            s["inAtlas"] if source == "atlas" else s["rel"]))
        try:
            if source == "atlas":
                blob = atlas_blob(root, ref, s["rel"])
                if blob is None:
                    raise OSError("the-atlas-ref-would-not-yield-this-blob")
                src_bytes = len(blob)
                data, ext, quality, how = encode_to_bytes(
                    blob, pathlib.Path(s["rel"]).suffix)
            else:
                src_bytes = s["path"].stat().st_size
                data, ext, quality, how = encode_to_bytes(
                    s["path"], s["path"].suffix)
        except Exception as exc:                                 # noqa: BLE001
            series.append({"rel": s.get("rel"), "bytes": 0, "kept": False,
                           "why": "unpublishable/%s" % type(exc).__name__,
                           "srcBytes": 0, "name": None})
            continue
        fname = "%s.%s" % (name, ext)
        wrote = publish_bytes(dest_dir, fname, data)
        total += wrote
        row = {"rel": s.get("rel"), "name": fname, "bytes": wrote,
               "srcBytes": src_bytes, "quality": quality, "kept": True,
               "how": how}
        series.append(row)
        kept.append(dict(s, name=fname, bytes=wrote, srcBytes=src_bytes,
                         quality=quality))
    reading = {"published": len(kept), "notPublished": len(shots) - len(kept),
               "bytes": total, "asked": len(shots),
               "srcBytes": sum(r["srcBytes"] for r in series),
               "resizer": "Pillow" if has_resizer() else "none"}
    return kept, series, reading


def has_resizer():
    try:
        import PIL                                               # noqa: F401
        return True
    except ImportError:
        return False


# ------------------------------------------------------------------- the page

CSS = """*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#0f1114;color:#c8ccd2;
 font:14px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
body{padding:6px}
img{display:block;width:100%%;height:auto;border-radius:6px;background:#191c21}
figure{margin:0 0 6px}
figcaption{font-size:11px;color:#8d949d;padding:3px 2px 0;
 display:flex;justify-content:space-between;gap:6px}
figcaption .what{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hero figcaption{font-size:12px}
.grid{display:grid;grid-template-columns:repeat(%d,1fr);gap:6px}
.band{font-size:12px;color:#8d949d;margin:10px 2px 6px;line-height:1.5}
.band b{color:#c8ccd2;font-weight:600}
.foot{margin:10px 2px 4px;font-size:12px;color:#8d949d;line-height:1.6}
.foot a{color:#7fb2ff;text-decoration:none;margin-right:10px}
"""

PAGE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>LEDGER: %s</title>
<style>%s</style>
</head>
<body id="%s">
%s
</body>
</html>
"""


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def day(epoch):
    return datetime.datetime.fromtimestamp(
        epoch, datetime.timezone.utc).strftime("%Y-%m-%d")


def fig_tag(shot, url_prefix, width, cls="", eager=False, when="", what=""):
    """One picture, its file and its date.

    `data-w` carries the slot width this picture is laid out in and
    `data-when` the epoch it is dated by, because both ruled properties (the
    layout and the ORDER) are facts about the page and must be measurable from
    the page rather than from the model that meant to render it.
    """
    return ('<figure%s data-w="%d" data-when="%d">'
            '<img src="%s/%s" alt="%s" loading="%s" decoding="async">'
            '<figcaption><span class="when">%s</span>'
            '<span class="what">%s</span></figcaption></figure>'
            % ((' class="%s"' % cls) if cls else "", width,
               shot.get("when", 0), esc(url_prefix), esc(shot["name"]),
               esc(what or shot.get("rel") or shot["name"]),
               "eager" if eager else "lazy", esc(when), esc(what)))


def gallery_body(kept, reading, pub, url_prefix, world_exists):
    """THE LATEST FRAMES, NEWEST FIRST, DATED, ALL OF THEM."""
    body = []
    for i, s in enumerate(kept):
        cls = "hero" if i == 0 else ""
        body.append(fig_tag(s, url_prefix,
                            HERO_WIDTH_PX if i == 0 else REST_WIDTH_PX,
                            cls=cls, eager=i < EAGER_PICTURES,
                            when=day(s["when"]),
                            what=s["rel"].rsplit("/", 1)[-1]))
    grid = "".join(body[1:])
    out = [body[0] if body else "", '<div class="grid">%s</div>' % grid
           if grid else ""]
    return "".join(x for x in out if x)


def gallery_foot(kept, reading, pub, world_exists, atlas):
    """ONE FOOT LINE: the links, and every count with its denominator. The
    count is the truncation notice instruments.md requires: a page holding 37
    of 49 pictures reads as a repository with 37 pictures."""
    links = ['<a href="%s">%s</a>' % (esc(GLANCE_LINK[0]), esc(GLANCE_LINK[1]))]
    if world_exists:
        links.append('<a href="%s">the town atlas</a>' % esc(WORLD_NAME))
    if reading["imagesFound"]:
        line = ("%d of %d picture(s) shown, newest first, each dated by the "
                "commit that wrote it (%d of %d dated that way, the rest by "
                "file time)."
                % (len(kept), reading["imagesFound"], reading["datedByCommit"],
                   reading["imagesFound"]))
        if pub["notPublished"]:
            line += (" (+%d more not shown: they could not be published, see "
                     "the run's own rows.)" % pub["notPublished"])
        if reading["clipsFound"]:
            line += (" %d clip(s) not shown: nothing here publishes video yet."
                     % reading["clipsFound"])
    else:
        line = ("%s: no picture found under the %d directory(ies) walked."
                % (NOTHING_WORDS, reading["dirsWalked"]))
    return '<p class="foot">%s<span>%s</span></p>' % ("".join(links),
                                                      esc(line))


def world_body(groups, url_prefix, atlas):
    """THE TOWN AS DRAWN, grouped by subject, every group saying its count.

    THE FIRST PICTURE OF THE FIRST GROUP IS THE HERO and everything after it
    sits two to a row, which is the gallery's layout unchanged: the widths in
    document order still never increase, so check_biggest_first reads this page
    the same way it reads the other one.
    """
    out, first = [], True
    for g in groups:
        out.append('<p class="band"><b>%s</b> %d picture(s).</p>'
                   % (esc(g["title"]), len(g["rows"])))
        rows = []
        for e in g["rows"]:
            rows.append(fig_tag(e, url_prefix,
                                HERO_WIDTH_PX if first else REST_WIDTH_PX,
                                cls="hero" if first else "",
                                eager=first, when=atlas["day"],
                                what=e["inAtlas"]))
            if first:
                out.append(rows.pop())
                first = False
        if rows:
            out.append('<div class="grid">%s</div>' % "".join(rows))
    return "".join(out)


def world_foot(atlas, pub):
    """THE PROVENANCE AND THE RIGHTS COUNT, where he can read them: which
    commit of which branch these pictures are, how many were cleared out of how
    many examined, and how many were withheld and why."""
    links = ['<a href="%s">the latest frames</a>' % esc(OUT_NAME),
             '<a href="%s">%s</a>' % (esc(GLANCE_LINK[0]),
                                      esc(GLANCE_LINK[1]))]
    if not atlas["ref"]:
        line = ("%s: the art branch is not in this checkout, so no atlas "
                "picture was examined (0 of %d ref name(s) tried answered)."
                % (NOTHING_WORDS, atlas["refsTried"]))
        return '<p class="foot">%s<span>%s</span></p>' % ("".join(links),
                                                          esc(line))
    why = {}
    for w in atlas["withheld"]:
        why[w["why"]] = why.get(w["why"], 0) + 1
    reasons = "; ".join("%d because %s" % (n, r)
                        for r, n in sorted(why.items(), key=lambda kv: -kv[1]))
    line = ("The town as drawn, read from %s at commit %s on %s, which is the "
            "version shown. %d of %d atlas picture(s) are cleared for "
            "publication and %d are withheld: %s. The two rights documents "
            "read at that same commit are %s and %s (%d of %d found)."
            % (atlas["ref"], atlas["sha"][:7], atlas["day"], atlas["cleared"],
               atlas["examined"], len(atlas["withheld"]),
               reasons or NOTHING_WORDS, PROVENANCE_DOC, RIGHTS_DOC,
               atlas["rightsDocs"], atlas["rightsDocsAsked"]))
    if atlas["unclassified"]:
        line += (" %d of those have no rights row at all and are withheld by "
                 "default." % atlas["unclassified"])
    return '<p class="foot">%s<span>%s</span></p>' % ("".join(links),
                                                       esc(line))


def stamp_comment(now, tool=TOOL):
    """The generator's dated sentence, in a COMMENT rather than on the page.

    tools/publish-glance.py reads "Generated by tools/<tool>.py at <date>
    <time> UTC" out of the served bytes and prints it as pageGeneratedAt, so
    the sentence has to be in the file. Jafar ruled this page carries pictures,
    so it is in the file and not on the screen. A regex over the body finds it
    either way; a reader sees pictures.
    """
    return "<!-- Generated by %s at %s UTC -->" % (
        tool, now.strftime("%Y-%m-%d %H:%M"))


def build(root, now, assets_dir=None, url_prefix=ASSETS_NAME, budget=None):
    """Both pages, their files, and the model behind them.

    THE FILES ARE WRITTEN HERE, under `assets_dir`, and every name is recorded
    in the manifest the publisher reads. The publisher must not have to guess
    which files a page references: a src naming a file nobody copies is a
    broken image on his phone, which is the 404 this repository has already
    paid for once.
    """
    root = pathlib.Path(root)
    assets = pathlib.Path(assets_dir) if assets_dir else (root / ASSETS_NAME)
    shots, reading = find_pictures(root)
    kept, series, pub = publish_pictures(shots, assets, "shot")

    atlas_rows, atlas = atlas_pictures(root)
    atlas["day"] = NOTHING_WORDS
    if atlas["sha"]:
        out, ok = git_out(root, "show", "-s", "--format=%ct", atlas["ref"])
        if ok and out.strip():
            atlas["day"] = day(int(out.strip()))
    akept, aseries, apub = publish_pictures(
        atlas_rows, assets, "atlas", source="atlas", root=root,
        ref=atlas["ref"]) if atlas_rows else ([], [], {
            "published": 0, "notPublished": 0, "bytes": 0, "asked": 0,
            "srcBytes": 0, "resizer": "Pillow" if has_resizer() else "none"})
    by_name = {e["inAtlas"]: e for e in akept}
    groups = []
    for g in atlas.get("groupRows", []):
        rows = [by_name[e["inAtlas"]] for e in g["rows"]
                if e["inAtlas"] in by_name]
        if rows:
            groups.append({"title": g["title"], "rows": rows})

    gal = PAGE % ("the gallery", CSS % COLUMNS, "gallery", "\n".join([
        stamp_comment(now),
        gallery_body(kept, reading, pub, url_prefix, bool(akept)),
        gallery_foot(kept, reading, pub, bool(akept), atlas)]))
    world = PAGE % ("the town atlas", CSS % COLUMNS, "world", "\n".join([
        stamp_comment(now),
        world_body(groups, url_prefix, atlas),
        world_foot(atlas, apub)]))

    manifest = {
        "tool": TOOL,
        "generatedAt": now.strftime("%Y-%m-%dT%H:%MZ"),
        "pages": [OUT_NAME, WORLD_NAME],
        "assetsDir": url_prefix,
        "files": [{"name": r["name"], "bytes": r["bytes"],
                   "source": r["rel"]} for r in series + aseries
                  if r["kept"]],
    }
    (assets).mkdir(parents=True, exist_ok=True)
    (assets / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1),
                                        encoding="utf-8")
    model = dict(reading, shown=len(kept), shots=kept, series=series,
                 pub=pub, atlas=atlas, atlasShown=len(akept),
                 atlasSeries=aseries, atlasPub=apub, groups=groups,
                 manifest=manifest, assetsDir=assets, urlPrefix=url_prefix,
                 resizer="Pillow" if has_resizer() else "none",
                 budget=budget or PAGE_BYTE_CAP)
    return gal, world, model


# ----------------------------------------------------------------- the checks

def shared(fn):
    def wrapped(page, model):
        return fn(page)
    wrapped.__name__ = fn.__name__
    return wrapped


check_viewport = shared(GLANCE.check_viewport)
check_width = shared(GLANCE.check_width)
check_formatting = shared(GLANCE.check_formatting)
check_secrets = shared(GLANCE.check_secrets)

W_RE = re.compile(r'data-w="(\d+)"')
WHEN_RE = re.compile(r'data-when="(\d+)"')
SRC_RE = re.compile(r'<img[^>]*\ssrc="([^"]+)"')
# A REFERENCE THIS PAGE CANNOT CONTROL: a scheme, a protocol-relative host or
# a parent-directory escape out of the published set.
REMOTE_SRC_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.I)


def check_newest_first(page, model):
    """THE RULED ORDER, READ OFF THE RENDERED PAGE. Jafar, 2026-09-09: "the
    gallery shows the newest images first". The dates in document order must
    never increase, which is checked on the bytes that ship rather than
    asserted about the list that built them. The world page is one commit, so
    it has no date order: it prints that instead of a check nothing could
    fail."""
    whens = [int(w) for w in WHEN_RE.findall(page)]
    if model.get("kind") == "world":
        return ("newestFirst", True,
                "worldPage=grouped-by-subject-not-by-date "
                "pictures=%d datesAllFromOneCommit=%s"
                % (len(whens), model["atlas"]["sha"][:7]
                   if model["atlas"]["sha"] else NOTHING))
    rises = [i for i in range(1, len(whens)) if whens[i] > whens[i - 1]]
    ok = not rises and len(whens) == model["shown"]
    return ("newestFirst", ok,
            "dateRises=%d/%d picture(s) in document order datesOnPage=%d/%d"
            "-published newest=%s oldest=%s"
            % (len(rises), len(whens), len(whens), model["shown"],
               day(whens[0]) if whens else NOTHING,
               day(whens[-1]) if whens else NOTHING))


def check_biggest_first(page, model):
    """THE EARLIER RULED LAYOUT, STILL MEASURED ON THE BYTES. Widths in
    document order must never increase and there is exactly one hero per
    section. Newest first (above) is the ORDER and this is the LAYOUT: they are
    different rules and this one survives because the newest picture is the
    hero either way."""
    widths = [int(w) for w in W_RE.findall(page)]
    rises = [i for i in range(1, len(widths)) if widths[i] > widths[i - 1]]
    heroes = page.count('class="hero"')
    wanted = 1 if widths else 0
    ok = not rises and heroes == wanted
    return ("biggestFirst", ok,
            "widthRises=%d/%d picture(s) in document order heroes=%d/%d "
            "widths=%s" % (len(rises), len(widths), heroes, wanted,
                           "/".join(str(w) for w in widths[:6])
                           + ("+%d" % (len(widths) - 6) if len(widths) > 6
                              else "") or NOTHING))


def check_every_picture_dated(page, model):
    """DATED, RULED. Every picture on the page carries a visible date, not a
    derivable one, and the count is read off the rendered bytes."""
    figs = len(re.findall(r"<figure\b", page))
    dates = len(re.findall(r'class="when">(\d{4}-\d\d-\d\d|nothing measured)<',
                           page))
    return ("everyPictureDated", figs == dates and (figs > 0 or
            NOTHING_WORDS in page),
            "picturesOnPage=%d datesOnPage=%d/%d-needed datedByCommit=%d/%d"
            % (figs, dates, figs, model.get("datedByCommit", 0),
               model.get("imagesFound", 0)))


def check_images_resolve(page, model, out_dir=None):
    """EVERY <img src> NAMES A FILE THAT IS THERE, counted both ways.

    THE PUBLISHED SET IS THE DENOMINATOR OF THIS CHECK. A src naming a file
    the publisher does not copy is a broken image on his phone; a published
    file no page references is weight nobody asked for. Both directions are
    counted and the missing ones are named, because "some images are broken" is
    not a finding anybody can act on.
    """
    # RESOLVED BESIDE THE ASSETS DIRECTORY, NOT BESIDE THE PAGE FILE. The
    # publisher writes the page into a temporary directory and the pictures
    # straight into the publish directory, so resolving against the page's own
    # parent reported 92 of 92 references broken on a publish where every one
    # of them was fine. The src is "<prefix>/<name>" and the file is
    # "<assetsDir>/<name>", so the directory the src is relative TO is the
    # assets directory's parent. Caught by running the publisher, not by
    # reading this function.
    base = pathlib.Path(out_dir) if out_dir else pathlib.Path(
        model["assetsDir"]).parent
    srcs = [s for s in SRC_RE.findall(page) if not s.startswith("data:")]
    found, missing = 0, []
    for s in srcs:
        if (base / s).is_file():
            found += 1
        else:
            missing.append(s)
    published = {f["name"] for f in model["manifest"]["files"]}
    referenced = {s.split("/")[-1] for s in srcs}
    return ("imagesResolve", found == len(srcs) and not missing,
            "imageRefsResolved=%d/%d-referenced missing=%s "
            "publishedFiles=%d referencedOfThem=%d/%d"
            % (found, len(srcs), "/".join(missing[:3]) or "none",
               len(published), len(referenced & published), len(published)))


def check_no_external_ref(page, model):
    """NO HOST WE DO NOT CONTROL, and relative files are not that.

    tools/glance.py's check_external is kept for the glance, where every
    picture is a data URI and any src with a scheme is the fault. This page
    ships FILES, so the question here is different and in two halves: no src
    may name a scheme or a protocol-relative host, and no src may climb out of
    the published set with "..". Measured before it was written: glance's
    REMOTE pattern already requires a scheme or a leading //, so a relative
    src does not trip it; what it cannot do is tell a local file that EXISTS
    from one that does not, which check_images_resolve above is for.
    """
    srcs = SRC_RE.findall(page)
    remote = [s for s in srcs if REMOTE_SRC_RE.match(s)
              and not s.startswith("data:")]
    escapes = [s for s in srcs if s.startswith("../") or "/../" in s]
    hrefs = re.findall(r'href="([^"]+)"', page)
    remote_href = [h for h in hrefs if REMOTE_SRC_RE.match(h)]
    return ("externalRefs", not remote and not escapes and not remote_href,
            "externalSrcs=%d/%d-img-src(s)-examined parentEscapes=%d "
            "externalHrefs=%d/%d-href(s)-examined%s"
            % (len(remote), len(srcs), len(escapes), len(remote_href),
               len(hrefs),
               "" if not (remote or escapes or remote_href)
               else " (" + ",".join((remote + escapes + remote_href)[:3]) + ")"))


def check_weight(page, model):
    """THE HTML, WHICH IS ALL THIS CAP IS NOW. The pictures are files and are
    counted separately: the page that used to be 1000108 bytes of base64 is
    text now, and this prints it against the glance's measured cap."""
    n = len(page.encode("utf-8"))
    cap = model["budget"]
    return ("pageBytes", n <= cap,
            "pageBytes=%d/%d cap (%.0f%% of it, %d picture(s), "
            "pictureBytesNotInThisNumber=%d)"
            % (n, cap, 100.0 * n / cap,
               len(re.findall(r"<figure\b", page)),
               model["pub"]["bytes"] + model["atlasPub"]["bytes"]))


def check_back_link(page, model):
    """One link home, and on the gallery one link sideways to the world page
    when there is a world page to link to: a tap into a 404 is the failure this
    counts against."""
    home = len(re.findall(r'href="%s"' % re.escape(GLANCE_LINK[0]), page))
    if model.get("kind") == "world":
        sideways = len(re.findall(r'href="%s"' % re.escape(OUT_NAME), page))
        return ("backLink", home == 1 and sideways == 1,
                "backLink=%d/1 href(s)-to-%s toTheFrames=%d/1"
                % (home, GLANCE_LINK[0], sideways))
    want = 1 if model["atlasShown"] else 0
    sideways = len(re.findall(r'href="%s"' % re.escape(WORLD_NAME), page))
    return ("backLink", home == 1 and sideways == want,
            "backLink=%d/1 href(s)-to-%s toTheWorldPage=%d/%d-wanted"
            % (home, GLANCE_LINK[0], sideways, want))


def check_nothing_else(page, model):
    """NOTHING ELSE, RULED, AND WHAT THE 2026-09-09 AMENDMENT ADDED.

    The gallery still carries pictures and one foot line: no headings, no
    tables, no navigation beyond the links in that foot. Dates are now ruled on
    every picture, so a figcaption is not commentary; it is the date. The world
    page carries one band line per subject group, because Jafar ruled the atlas
    is a world page and a reader has to be told which group he is looking at,
    and the count of those bands is checked against the groups this run
    actually built rather than left open.
    """
    body = page.split("<body id=", 1)[-1]
    extra = re.findall(r"<(h[1-6]|table|ul|ol|nav|section|blockquote)\b", body)
    paras = len(re.findall(r"<p\b", body))
    bands = len(re.findall(r'<p class="band"', body))
    allowed = 1 + (len(model["groups"]) if model.get("kind") == "world" else 0)
    return ("nothingElse", not extra and paras <= allowed
            and bands == allowed - 1,
            "commentaryElements=%d paragraphs=%d/%d-allowed(the-foot%s) "
            "bands=%d/%d-groups tagsExamined=%d"
            % (len(extra), paras, allowed,
               "+one-per-group" if allowed > 1 else "", bands, allowed - 1,
               len(re.findall(r"<\w+", body))))


def check_count_announced(page, model):
    """A CAP THAT DOES NOT SAY IT BIT READS AS A FINDING, and a zero without
    its denominator cannot tell nothing from fine. The gallery foot prints the
    shown count against the found count every run; the world foot prints
    cleared against examined and the withheld count."""
    if model.get("kind") == "world":
        a = model["atlas"]
        said = re.search(r"(\d+) of (\d+) atlas picture\(s\) are cleared",
                         page)
        ok = bool(said) if a["examined"] else NOTHING_WORDS in page
        return ("countAnnounced", bool(ok),
                "footSaysRights=%s cleared=%d/%d-examined withheld=%d "
                "unclassified=%d"
                % (said.group(0).replace(" ", "-") if said else NOTHING,
                   a["cleared"], a["examined"], len(a["withheld"]),
                   a["unclassified"]))
    said = re.search(r"(\d+) of (\d+) picture\(s\) shown", page)
    bit = model["pub"]["notPublished"] > 0
    announced = "not shown" in page
    ok = bool(said) if model["imagesFound"] else NOTHING_WORDS in page
    if bit:
        ok = ok and announced
    return ("countAnnounced", bool(ok),
            "footSaysCount=%s notPublished=%d/%d announced=%s"
            % (said.group(0).replace(" ", "-") if said else NOTHING,
               model["pub"]["notPublished"], model["imagesFound"], announced))


def check_rights_stated(page, model):
    """THE LICENCE ALLOWLIST IS LAW, so the world page says what it cleared and
    what it withheld, and nothing withheld is on the page.

    The second half is the one that matters: it reads the rendered bytes for
    the NAME of every withheld file, because a rights table that is right and a
    page that ships the file anyway is the silent failure here.
    """
    a = model["atlas"]
    if model.get("kind") != "world":
        return ("rightsStated", True,
                "notTheWorldPage=gallery.html atlasPicturesHere=0/%d-cleared"
                % a["cleared"])
    leaked = [w["inAtlas"] for w in a["withheld"]
              if safe_stem(w["inAtlas"]) in page]
    stated = ("cleared for publication" in page) if a["examined"] \
        else NOTHING_WORDS in page
    docs = a["rightsDocs"] == a["rightsDocsAsked"] or not a["ref"]
    return ("rightsStated", stated and not leaked and docs,
            "cleared=%d/%d-examined withheld=%d withheldFilesOnPage=%d/0"
            "-allowed rightsDocsRead=%d/%d statedOnPage=%s"
            % (a["cleared"], a["examined"], len(a["withheld"]), len(leaked),
               a["rightsDocs"], a["rightsDocsAsked"],
               "yes" if stated else "MISSING"))


def check_lazy_loading(page, model):
    """The hero loads eagerly and everything below it is lazy, so a phone on a
    weak link pays for what he scrolls to. Counted, because "it is lazy" is the
    sort of claim that decays into one forgotten attribute."""
    figs = len(re.findall(r"<figure\b", page))
    lazy = len(re.findall(r'loading="lazy"', page))
    eager = len(re.findall(r'loading="eager"', page))
    want_eager = min(EAGER_PICTURES, figs)
    return ("lazyLoading", lazy + eager == figs and eager == want_eager,
            "lazy=%d eager=%d/%d-wanted pictures=%d/%d-withAnAttribute"
            % (lazy, eager, want_eager, figs, lazy + eager))


CHECKS = (check_newest_first, check_biggest_first, check_every_picture_dated,
          check_images_resolve, check_no_external_ref, check_count_announced,
          check_rights_stated, check_lazy_loading, check_nothing_else,
          check_back_link, check_weight, check_viewport, check_width,
          check_formatting, check_secrets)


def run_checks(page, model, out_dir=None):
    out = []
    for f in CHECKS:
        if f is check_images_resolve:
            out.append(f(page, model, out_dir))
        else:
            out.append(f(page, model))
    return out


# --------------------------------------------------------------- the selftest

def _tree(files, mtimes=None):
    import atexit
    import shutil
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp(prefix="gallery-"))
    atexit.register(shutil.rmtree, str(d), True)
    for rel, blob in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
        if mtimes and rel in mtimes:
            import os
            os.utime(p, (mtimes[rel], mtimes[rel]))
    return d


def _out(tmp, name):
    return pathlib.Path(tmp) / name


def selftest():
    import tempfile
    passed, failed = 0, []
    now = datetime.datetime(2026, 9, 9, 7, 0)

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s\n         got: %s" % (name, got))

    print("%s --selftest: ACCEPTING CASE FIRST, the live repository\n" % TOOL)
    live = pathlib.Path(tempfile.mkdtemp(prefix="gallery-live-"))
    gal, world, model = build(ROOT, now, assets_dir=live / ASSETS_NAME)
    (live / OUT_NAME).write_text(gal, encoding="utf-8")
    (live / WORLD_NAME).write_text(world, encoding="utf-8")
    gmodel, wmodel = dict(model, kind="gallery"), dict(model, kind="world")
    gchecks = run_checks(gal, gmodel, out_dir=live)
    wchecks = run_checks(world, wmodel, out_dir=live)
    gbad = [n for n, c, _ in gchecks if not c]
    wbad = [n for n, c, _ in wchecks if not c]
    ok("the live repository renders the gallery and every check passes "
       "(%d picture(s) of %d found, %d check(s))"
       % (model["shown"], model["imagesFound"], len(gchecks)),
       model["shown"] >= 1 and not gbad, "failed=%s" % (",".join(gbad) or "none"))
    ok("EVERY picture found is published, none dropped for bytes "
       "(publishedFiles=%d/%d-found notPublished=%d)"
       % (model["shown"], model["imagesFound"], model["pub"]["notPublished"]),
       model["shown"] == model["imagesFound"]
       and model["pub"]["notPublished"] == 0,
       "%d of %d" % (model["shown"], model["imagesFound"]))
    ok("the world page renders and every check passes (%d atlas picture(s) "
       "cleared of %d examined, %d check(s))"
       % (model["atlasShown"], model["atlas"]["examined"], len(wchecks)),
       not wbad, "failed=%s" % (",".join(wbad) or "none"))
    ok("every <img src> on both pages resolves to a file in the publish "
       "directory (%s | %s)"
       % (check_images_resolve(gal, gmodel, live)[2],
          check_images_resolve(world, wmodel, live)[2]),
       check_images_resolve(gal, gmodel, live)[1]
       and check_images_resolve(world, wmodel, live)[1])
    ordered, _reading = find_pictures(ROOT)
    ok("the newest pictures are the newest IN THE ORDER, by commit time and "
       "not by file time (datedByCommit=%d/%d), and the page's own dates never "
       "increase (%s)"
       % (model["datedByCommit"], model["imagesFound"],
          check_newest_first(gal, gmodel)[2]),
       check_newest_first(gal, gmodel)[1]
       and [s["rel"] for s in ordered[:3]]
       == [s["rel"] for s in model["shots"][:3]],
       [s["rel"] for s in ordered[:3]])
    print("\n  THE SERIES this run printed, which is what a bound on the "
          "published bytes would be read off:\n")
    for row in (model["series"] + model["atlasSeries"])[:10]:
        print("    %-54s %7d bytes from %8d source q=%s %s"
              % ((row["rel"] or "?")[-54:], row["bytes"], row["srcBytes"],
                 row["quality"], "published" if row["kept"]
                 else "NOT-PUBLISHED/" + row["why"]))
    rows = len(model["series"]) + len(model["atlasSeries"])
    if rows > 10:
        print("    (+%d more row(s) not shown of %d)" % (rows - 10, rows))
    print("    publishedFiles=%d publishedBytes=%d sourceBytes=%d "
          "galleryHtmlBytes=%d worldHtmlBytes=%d resizer=%s"
          % (model["shown"] + model["atlasShown"],
             model["pub"]["bytes"] + model["atlasPub"]["bytes"],
             model["pub"]["srcBytes"] + model["atlasPub"]["srcBytes"],
             len(gal.encode("utf-8")), len(world.encode("utf-8")),
             model["resizer"]))
    # THE RIGHTS TABLE ON THE LIVE LIST, AS A READING AND AN ASSERTION. The
    # assertion is the one thing that must hold whatever the branch holds: no
    # withheld file may be on the page. The counts are printed beside it,
    # because a clone that never fetched the art branch measures none and must
    # say so rather than read as clean.
    a = model["atlas"]
    print("    atlasRef=%s atlasSha=%s rightsCleared=%d/%d-examined "
          "withheld=%d unclassified=%d rightsDocsRead=%d/%d"
          % (a["ref"] or "missing-in-this-checkout",
             (a["sha"] or NOTHING)[:7], a["cleared"], a["examined"],
             len(a["withheld"]), a["unclassified"], a["rightsDocs"],
             a["rightsDocsAsked"]))
    ok("no withheld atlas file reaches the world page (%s)"
       % check_rights_stated(world, wmodel)[2],
       check_rights_stated(world, wmodel)[1])

    # ACCEPTING 2: A SYNTHETIC TREE, ordered by file time because git knows
    # nothing about it. Three planted pictures and the order is the fixture's
    # own mtimes rather than the repository's history.
    t = _tree({"production/d1-probe/a.png": FIXTURE_PNG,
               "production/d1-probe/b.png": FIXTURE_PNG,
               "game-design/sim-shots/c.png": FIXTURE_PNG},
              {"production/d1-probe/a.png": 1000,
               "production/d1-probe/b.png": 3000,
               "game-design/sim-shots/c.png": 2000})
    t_out = pathlib.Path(tempfile.mkdtemp(prefix="gallery-syn-"))
    p2, w2, m2 = build(t, now, assets_dir=t_out / ASSETS_NAME)
    (t_out / OUT_NAME).write_text(p2, encoding="utf-8")
    m2g = dict(m2, kind="gallery")
    order = [s["rel"].rsplit("/", 1)[-1] for s in m2["shots"]]
    ok("a tree git knows nothing about orders by file time, newest first "
       "(datedByMtime=%d/%d): %s" % (m2["datedByMtime"], m2["imagesFound"],
                                     "/".join(order)),
       order == ["b.png", "c.png", "a.png"], order)
    ok("and its three files are on disk and its three srcs resolve (%s)"
       % check_images_resolve(p2, m2g, t_out)[2],
       check_images_resolve(p2, m2g, t_out)[1])
    ok("and its widths never increase down the page (%s)"
       % check_biggest_first(p2, m2g)[2], check_biggest_first(p2, m2g)[1])
    ok("and every picture on it carries a visible date (%s)"
       % check_every_picture_dated(p2, m2g)[2],
       check_every_picture_dated(p2, m2g)[1])

    print("\n  REJECTING FIXTURES, all synthetic:\n")
    # REJECTING 1: NOTHING TO SHOW. The page must say the words, not render an
    # empty frame that on a phone looks like a page that failed to load.
    empty = _tree({"production/d1-probe/notes.txt": b"hello\n"})
    e_out = pathlib.Path(tempfile.mkdtemp(prefix="gallery-empty-"))
    p3, w3, m3 = build(empty, now, assets_dir=e_out / ASSETS_NAME)
    m3g = dict(m3, kind="gallery")
    ok("a tree with no picture at all renders the words '%s' rather than an "
       "empty page (imagesFound=%d/%d dir(s) walked)"
       % (NOTHING_WORDS, m3["imagesFound"], m3["dirsWalked"]),
       m3["shown"] == 0 and NOTHING_WORDS in p3 and "<img" not in p3,
       p3[-200:])
    ok("and that page still carries exactly one link back (%s)"
       % check_back_link(p3, m3g)[2], check_back_link(p3, m3g)[1])
    # REJECTING 1b: a tree with no art branch says so on the world page rather
    # than rendering an empty atlas.
    w3m = dict(m3, kind="world")
    ok("a tree with no art branch says the words on the world page and "
       "examines nothing (%s)" % check_count_announced(w3, w3m)[2],
       m3["atlas"]["ref"] is None and NOTHING_WORDS in w3
       and check_count_announced(w3, w3m)[1], w3[-260:])

    # REJECTING 2: A BROKEN IMAGE REFERENCE. The file is deleted out from under
    # the page, which is exactly the shape of the publisher not copying it.
    broken_dir = pathlib.Path(tempfile.mkdtemp(prefix="gallery-broken-"))
    p4, w4, m4 = build(t, now, assets_dir=broken_dir / ASSETS_NAME)
    victim = sorted((broken_dir / ASSETS_NAME).glob("shot-*"))[0]
    victim.unlink()
    name, good, said = check_images_resolve(p4, dict(m4, kind="gallery"),
                                           broken_dir)
    ok("a page whose picture file is missing from the publish directory is "
       "refused by imagesResolve, and the missing file is NAMED", not good,
       said)

    # REJECTING 3: THE ORDER CHECK CAN FAIL. A guard that cannot go red on a
    # bad page is a ratchet, so a page with dates that grow is planted.
    # THE LAST PICTURE IS THE ONE TO AGE FORWARD: bumping the FIRST one keeps
    # the order non-increasing and the fixture then passes a page that is still
    # correctly ordered, which is a rejecting case that rejects nothing. It did
    # exactly that on the first run of this suite.
    last = list(WHEN_RE.finditer(p2))[-1]
    rising = (p2[:last.start()] + 'data-when="%d"' % (int(last.group(1))
                                                      + 10 ** 6)
              + p2[last.end():])
    ok("a page whose dates GROW down the page is refused by newestFirst",
       not check_newest_first(rising, m2g)[1],
       check_newest_first(rising, m2g)[2])
    wide = p2.replace('data-w="%d"' % HERO_WIDTH_PX,
                      'data-w="%d"' % (REST_WIDTH_PX // 2), 1)
    ok("a page whose widths GROW down the page is refused by biggestFirst",
       not check_biggest_first(wide, m2g)[1],
       check_biggest_first(wide, m2g)[2])
    # REJECTING 4: commentary is refused.
    chatty = p2.replace('<p class="foot">',
                        '<h2>what changed today</h2><p class="foot">')
    ok("a page carrying a heading is refused by nothingElse",
       not check_nothing_else(chatty, m2g)[1],
       check_nothing_else(chatty, m2g)[2])
    # REJECTING 5: a picture with no date is refused.
    undated = re.sub(r'<span class="when">[^<]*</span>', "", p2, count=1)
    ok("a picture with no visible date is refused by everyPictureDated",
       not check_every_picture_dated(undated, m2g)[1],
       check_every_picture_dated(undated, m2g)[2])
    # REJECTING 6: a host we do not control is refused, and a relative file is
    # NOT. Both halves, because a check that refuses every src would pass this
    # page's own pictures into the fault column.
    remote = p2.replace('src="%s/' % ASSETS_NAME,
                        'src="https://example.invalid/', 1)
    ok("an src naming a host we do not control is refused by externalRefs",
       not check_no_external_ref(remote, m2g)[1],
       check_no_external_ref(remote, m2g)[2])
    ok("and the real page's own relative srcs are NOT refused by it (%s)"
       % check_no_external_ref(p2, m2g)[2],
       check_no_external_ref(p2, m2g)[1])
    escape = p2.replace('src="%s/' % ASSETS_NAME, 'src="../../etc/', 1)
    ok("an src climbing out of the published set is refused by externalRefs",
       not check_no_external_ref(escape, m2g)[1],
       check_no_external_ref(escape, m2g)[2])

    # REJECTING 7: THE RIGHTS TABLE, BOTH WAYS, ON PURE INPUTS. The accepting
    # side is the live atlas list above; these are the synthetic names.
    unknown = rights_of("previews/a-picture-nobody-has-classified.png")
    hull = rights_of("references/hull-west-dock-1981.jpg")
    concept = rights_of("concepts/hook.png")
    plan = rights_of("previews/district-hook-plan.png")
    ok("an atlas file no rights row names is WITHHELD by default, and the "
       "reason says so", unknown[0] is False and unknown[3] is None,
       unknown[1][:60])
    ok("the third-party photograph is withheld and its reason names "
       "references/RIGHTS.md", hull[0] is False and hull[2] == RIGHTS_DOC,
       hull[1][:70])
    ok("the AI concepts are withheld and the reason names the licence "
       "allowlist", concept[0] is False and concept[2] == ALLOWLIST_DOC,
       concept[1][:70])
    ok("and an authored district plan IS cleared, so the table is not a "
       "blanket refusal", plan[0] is True, plan[1][:70])
    # REJECTING 8: a withheld file planted onto the world page is caught.
    if model["atlas"]["withheld"]:
        victim_name = model["atlas"]["withheld"][0]["inAtlas"]
        leak = world.replace("</body>", '<img src="%s/%s">'
                             % (ASSETS_NAME, safe_stem(victim_name)))
        ok("a withheld atlas file planted onto the world page is refused by "
           "rightsStated", not check_rights_stated(leak, wmodel)[1],
           check_rights_stated(leak, wmodel)[2])
    else:
        print("    nothing measured: no withheld atlas file in this checkout, "
              "so the leak fixture had nothing to plant (atlasRef=%s)"
              % (model["atlas"]["ref"] or "missing"))

    print("\n%s --selftest: %s. %d passed, %d failed, over %d check(s) and "
          "%d rejecting fixture(s)"
          % (TOOL, "PASS" if not failed else "FAILED", passed, len(failed),
             len(CHECKS), 8))
    for f in failed:
        print("  " + f)
    return 0 if not failed else 3


# -------------------------------------------------------------------- the CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", default=None)
    ap.add_argument("--world-out", default=None,
                    help="where world.html goes; beside --out by default")
    ap.add_argument("--assets-dir", default=None,
                    help="where the picture FILES go; <out dir>/%s by default"
                         % ASSETS_NAME)
    ap.add_argument("--url-prefix", default=None,
                    help="what the page's src attributes say; the assets "
                         "directory name by default")
    ap.add_argument("--now", default=None, help="ISO clock, for the stamp")
    ap.add_argument("--budget", type=int, default=PAGE_BYTE_CAP)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    root = pathlib.Path(args.root).resolve()
    out = pathlib.Path(args.out) if args.out else root / OUT_NAME
    world_out = (pathlib.Path(args.world_out) if args.world_out
                 else out.parent / WORLD_NAME)
    assets = (pathlib.Path(args.assets_dir) if args.assets_dir
              else out.parent / ASSETS_NAME)
    prefix = args.url_prefix or assets.name
    now = (datetime.datetime.fromisoformat(args.now) if args.now
           else datetime.datetime.now(datetime.timezone.utc))
    gal, world, model = build(root, now, assets_dir=assets, url_prefix=prefix,
                              budget=args.budget)
    # WRITTEN EVEN WHEN IT IS THIN, and deliberately over the previous file:
    # tools/map.py's rule, for its reason. A stale gallery that still looks
    # current is worse than one that says it holds nothing.
    out.write_text(gal, encoding="utf-8")
    world_out.write_text(world, encoding="utf-8")
    gchecks = run_checks(gal, dict(model, kind="gallery"),
                         out_dir=assets.parent)
    wchecks = run_checks(world, dict(model, kind="world"),
                         out_dir=assets.parent)
    bad = [("gallery/" + n) for n, c, _ in gchecks if not c] \
        + [("world/" + n) for n, c, _ in wchecks if not c]
    # PER-PICTURE NUMBERS ON THE PICTURE'S LINE. A grep across lines must not
    # be able to read one picture's bytes as the run's total.
    for row in model["series"] + model["atlasSeries"]:
        print("gallery: shot=%s bytes=%d srcBytes=%d %s"
              % (row["rel"], row["bytes"], row["srcBytes"],
                 ("published=%s quality=%s" % (row["name"], row["quality"]))
                 if row["kept"] else "notPublished=%s" % row["why"]))
    if model["dirsAbsent"]:
        print("gallery: dirsAbsent=%s of the %d named"
              % (",".join(model["dirsAbsent"]), model["dirsNamed"]))
    for w in model["atlas"]["withheld"]:
        print("gallery: atlasWithheld=%s source=%s" % (w["inAtlas"],
                                                       w["source"]))
    # THE EXIT CODE IS DECIDED FIRST AND THE WORD IS DERIVED FROM IT, so the
    # two can never disagree. They did once: a run that dropped 34 of 36
    # pictures printed the word DONE beside exit 1.
    lost = model["pub"]["notPublished"] + model["atlasPub"]["notPublished"]
    if not model["imagesFound"]:
        code, word = 2, "NOTHING-MEASURED"
    elif bad or lost:
        code, word = 1, "REFUSED"
    else:
        code, word = 0, "DONE"
    print("gallery: wrote %s %s" % (out, " ".join(s for _, _, s in gchecks)))
    print("gallery: wrote %s %s" % (world_out,
                                    " ".join(s for _, _, s in wchecks)))
    a = model["atlas"]
    # WHOLE-RUN NUMBERS ON THE DONE LINE, and every zero beside what it counted.
    print("gallery: %s picturesShown=%d/%d-found dirsWalked=%d/%d "
          "clipsFound=%d/%d-suffixes-examined datedByCommit=%d/%d "
          "notPublished=%d publishedFiles=%d publishedBytes=%d assetsDir=%s "
          "sourceBytes=%d galleryHtmlBytes=%d/%d-budget worldHtmlBytes=%d "
          "atlasRef=%s atlasSha=%s atlasCleared=%d/%d-examined "
          "atlasWithheld=%d atlasUnclassified=%d rightsDocsRead=%d/%d "
          "resizer=%s checksFailed=%d/%d"
          % (word, model["shown"], model["imagesFound"], model["dirsWalked"],
             model["dirsNamed"], model["clipsFound"], len(CLIP_SUFFIXES),
             model["datedByCommit"], model["imagesFound"], lost,
             model["shown"] + model["atlasShown"],
             model["pub"]["bytes"] + model["atlasPub"]["bytes"], assets,
             model["pub"]["srcBytes"] + model["atlasPub"]["srcBytes"],
             len(gal.encode("utf-8")), args.budget,
             len(world.encode("utf-8")),
             a["ref"] or "missing-in-this-checkout",
             (a["sha"] or NOTHING)[:7], a["cleared"], a["examined"],
             len(a["withheld"]), a["unclassified"], a["rightsDocs"],
             a["rightsDocsAsked"], model["resizer"],
             len(bad), len(CHECKS) * 2))
    if bad:
        print("gallery: checksFailed=%s" % ",".join(bad))
    if lost:
        print("gallery: %d picture(s) could not be published at all. The rows "
              "above name each one and why; this is not the same fact as "
              "'the repository has that many pictures'." % lost)
    return code


if __name__ == "__main__":
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
