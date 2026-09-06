#!/usr/bin/env python3
"""THE GALLERY: the latest frames and clips, biggest first, nothing else.

    python3 tools/gallery.py                  # write gallery.html at the root
    python3 tools/gallery.py --selftest       # accepting case FIRST
    python3 tools/gallery.py --out <f> --now <iso> --budget <bytes>

WHAT IT IS. Jafar, 2026-09-06, verbatim: "Add a gallery page beside the glance:
the latest frames and clips, biggest first, nothing else." So this is a THIRD
page, published beside index.html and map.html, and its whole specification is
that sentence. No commentary, no metrics, no navigation beyond one link back.
tools/glance.py and tools/map.py are the pattern and the house style; six of
the checks below are imported from the glance rather than retyped.

BIGGEST FIRST IS A LAYOUT RULE AND IT IS CHECKED. The newest picture is the
hero, full width; everything after it is two to a row. `check_biggest_first`
reads the rendered widths out of the page in document order and refuses a page
whose widths ever increase, so the ruled property is measured on the bytes that
ship rather than asserted in this docstring.

WHAT DECIDES HOW MANY PICTURES. The byte budget and nothing else. There is no
count cap, because a count nobody has measured is a number pretending to be a
bound: this run prints the whole series (each picture's encoded bytes, the
running total, and what did not fit) and a count bound can be read off real
runs later if the scroll turns out to be too long. When the budget bites, the
page says so in its foot line, with its denominator, because a gallery that
silently stops at six of thirty-one reads as "there are only six pictures".

WHAT IT CANNOT SEE. It does not know whether a picture is any good, whether it
shows what the brief says it shows, or whether it is the picture Jafar meant.
It knows the file's date, its bytes and its order. And it embeds no video: no
video file exists under the walked directories today (measured, and the count
is printed with its denominator every run), so "clips" is a printed zero and
not a claim that there are none.

EXIT CODES, distinct per outcome. 0 the page is good. 1 a check failed, or a
picture was dropped for want of a resizer, and the page was still written
because a stale gallery is worse than one that says what it holds. 2 nothing
measured: no image file at all under any walked directory. 3 the selftest
failed. 4 tools/glance.py could not be imported.
"""
import argparse
import base64
import datetime
import html
import importlib.util
import pathlib
import re
import sys

TOOL = "tools/gallery.py"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_NAME = "gallery.html"
SIBLING = ("index.html", "back to the glance")


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

# WHERE THE PICTURES ARE, measured on 2026-09-06 rather than assumed: 4 png
# under production/d1-probe (the Unreal vignette frames, the newest images in
# the repository), 31 jpg under game-design/sim-shots, and production/frames
# exists in tools/glance.py's list but holds nothing yet. A directory that does
# not exist is counted and named, never silently skipped.
SOURCES = ("production/d1-probe", "production/frames", "game-design/sim-shots")
IMAGE_SUFFIXES = GLANCE.IMAGE_SUFFIXES
# NOT EMBEDDED, COUNTED. The day a clip lands, this prints a non-zero beside
# its denominator and the foot line says how many were not shown, rather than
# the page quietly being frames only for ever.
CLIP_SUFFIXES = (".mp4", ".webm", ".gif", ".mov")

# THE WIDTHS ARE THE GLANCE'S ARITHMETIC, NOT NEW NUMBERS. 780 is twice the 390
# logical px of the phones in use, which is tools/glance.py's stated figure and
# its IMAGE_WIDTH_PX. The hero spans the page, so it gets 780. The rest sit two
# to a row, so each is half of it.
HERO_WIDTH_PX = GLANCE.IMAGE_WIDTH_PX
COLUMNS = 2
REST_WIDTH_PX = HERO_WIDTH_PX // COLUMNS

# THE PAGE BUDGET, DERIVED FROM THE GLANCE'S MEASURED RATE AND SAID OUT LOUD.
# tools/glance.py caps itself at 250000 bytes, which its comment derives as two
# seconds on a weak but usable mobile link of 1 Mbit/s (125000 bytes/second).
# That rate is the measured thing and it is reused; what differs is the errand.
# The glance is opened while he is doing something else; the gallery is opened
# ON PURPOSE to look at pictures, so it is allowed eight seconds of the same
# link instead of two. Every run prints the weight against this budget and the
# per-picture series behind it, so the number can be replaced by a reading.
LINK_BYTES_PER_SEC = GLANCE.PAGE_BYTE_CAP // 2
GALLERY_SECONDS = 8
PAGE_BYTE_CAP = LINK_BYTES_PER_SEC * GALLERY_SECONDS
MAX_DECLARED_WIDTH_PX = GLANCE.MAX_DECLARED_WIDTH_PX

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
    picture's own line."""
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


def pack(shots, budget, shell_bytes):
    """Encode newest first until the budget is spent. Returns (kept, series).

    THE CAP BITES HERE AND IT IS THE ONLY CAP. Each picture's encoded size is
    recorded on its own row with the running total AT THAT MOMENT, which is the
    denominator that matters when one does not fit: `usedAtDrop` is captured at
    the instant that drop happens and named so.

    A PICTURE THAT DOES NOT FIT IS SKIPPED, NOT A FULL STOP. This used to break
    out of the loop on the first overflow, and the failure that would have
    caused is worth writing down: with no Pillow on the runner every picture
    embeds at full size, the newest one is a 1.1 MB png, so the FIRST picture
    would overflow, the page would hold nothing, the selftest would go red and
    the publish step would take the glance and the map off his phone with it.
    Skipping keeps the page honest and thin instead, and the foot line and the
    exit code both say how many went missing and why.
    """
    kept, series, used = [], [], shell_bytes
    dropped_for = None
    for i, s in enumerate(shots):
        width = HERO_WIDTH_PX if not kept else REST_WIDTH_PX
        room = budget - used
        try:
            b64, mime, n, how, quality = encode(s["path"], width, room)
        except OSError as exc:
            series.append({"rel": s["rel"], "bytes": 0, "kept": False,
                           "why": "unreadable/%s" % type(exc).__name__})
            continue
        if n > room:
            if dropped_for is None:
                # THE FIRST DROP, WITH THE DENOMINATOR AT THE INSTANT IT BIT,
                # not at the end of the run: they differ, and the one that
                # explains the drop is this one.
                dropped_for = {"rel": s["rel"], "bytes": n, "room": room,
                               "usedAtDrop": used, "index": i}
            series.append({"rel": s["rel"], "bytes": n, "kept": False,
                           "why": "over-budget"})
            continue
        used += n
        kept.append(dict(s, b64=b64, mime=mime, bytes=n, width=width,
                         quality=quality, how=how))
        series.append({"rel": s["rel"], "bytes": n, "kept": True,
                       "usedAfter": used, "width": width})
    return kept, {"series": series, "used": used, "budget": budget,
                  "droppedAt": dropped_for,
                  "notShown": len(shots) - len(kept)}


def encode(path, width, budget):
    """One picture as a data URI at `width`, through the glance's encoder.

    tools/glance.py owns "resize to a phone width and pick the first quality
    that fits". This function only chooses the width, because the glance's
    encoder takes one from its module constant. Swapping the constant around
    the call is ugly and it is deliberate: the alternative is a second copy of
    the encoder, which is the thing instruments.md forbids.
    """
    saved = GLANCE.IMAGE_WIDTH_PX
    try:
        GLANCE.IMAGE_WIDTH_PX = width
        return GLANCE.encode_image(path, max(budget, 0))
    finally:
        GLANCE.IMAGE_WIDTH_PX = saved


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
.hero{margin:0 0 6px}
.grid{display:grid;grid-template-columns:repeat(%d,1fr);gap:6px}
.foot{margin:10px 2px 4px;font-size:12px;color:#8d949d}
.foot a{color:#7fb2ff;text-decoration:none;margin-right:10px}
"""

PAGE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>LEDGER: the gallery</title>
<style>%s</style>
</head>
<body id="gallery">
%s
</body>
</html>
"""


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def img_tag(shot, cls=""):
    """One picture. `data-w` carries the width it was encoded at, which is what
    check_biggest_first reads: the rendered order is a fact about the page and
    must be measurable from the page."""
    return ('<img%s data-w="%d" alt="%s" src="data:%s;base64,%s">'
            % ((' class="%s"' % cls) if cls else "", shot["width"],
               esc(shot["path"].stem), shot["mime"], shot["b64"]))


def foot(shown, found, clips, packed):
    """ONE LINE, and it is the only text on the page: the link back, and the
    count with its denominator. The count is not a metric about the game, it is
    the truncation notice instruments.md requires: without it a page holding
    six of thirty-one pictures reads as a repository with six pictures."""
    bits = ['<a href="%s">%s</a>' % (esc(SIBLING[0]), esc(SIBLING[1]))]
    if found:
        line = "%d of %d shown" % (shown, found)
        if packed["notShown"]:
            line += " (+%d more not shown, the page budget bit)" % packed["notShown"]
        if clips:
            line += ", %d clip(s) not shown: nothing here embeds video yet" % clips
        bits.append(esc(line))
    else:
        bits.append(esc("nothing measured: no picture found"))
    return '<p class="foot">%s</p>' % "".join(
        b if b.startswith("<a") else "<span>%s</span>" % b for b in bits)


def stamp_comment(now):
    """The generator's dated sentence, in a COMMENT rather than on the page.

    tools/publish-glance.py reads "Generated by tools/<tool>.py at <date>
    <time> UTC" out of the served bytes and prints it as pageGeneratedAt, so
    the sentence has to be in the file. Jafar ruled this page carries nothing
    but pictures, so it is in the file and not on the screen. A regex over the
    body finds it either way; a reader sees pictures.
    """
    return "<!-- Generated by %s at %s UTC -->" % (
        TOOL, now.strftime("%Y-%m-%d %H:%M"))


def build(root, now, budget=PAGE_BYTE_CAP):
    shots, reading = find_pictures(root)
    shell = len(PAGE % (CSS % COLUMNS, "")) + 400      # style, foot, stamp
    kept, packed = pack(shots, budget, shell)
    body = [stamp_comment(now)]
    if kept:
        body.append(img_tag(kept[0], "hero"))
        rest = kept[1:]
        if rest:
            body.append('<div class="grid">%s</div>'
                        % "".join(img_tag(s) for s in rest))
    body.append(foot(len(kept), reading["imagesFound"], reading["clipsFound"],
                     packed))
    page = PAGE % (CSS % COLUMNS, "\n".join(body))
    model = dict(reading, shown=len(kept), shots=kept, packed=packed,
                 resizer="Pillow" if has_resizer() else "none")
    return page, model


# ----------------------------------------------------------------- the checks

def shared(fn):
    def wrapped(page, model):
        return fn(page)
    wrapped.__name__ = fn.__name__
    return wrapped


check_viewport = shared(GLANCE.check_viewport)
check_width = shared(GLANCE.check_width)
check_external = shared(GLANCE.check_external)
check_formatting = shared(GLANCE.check_formatting)
check_secrets = shared(GLANCE.check_secrets)

W_RE = re.compile(r'data-w="(\d+)"')


def check_biggest_first(page, model):
    """THE RULED PROPERTY, MEASURED ON THE BYTES. Widths in document order must
    never increase, and there is exactly one hero. Read from the page and not
    from the model, because the model is what we meant to render."""
    widths = [int(w) for w in W_RE.findall(page)]
    rises = [i for i in range(1, len(widths)) if widths[i] > widths[i - 1]]
    heroes = page.count('class="hero"')
    ok = not rises and heroes == (1 if widths else 0)
    return ("biggestFirst", ok,
            "widthRises=%d/%d picture(s) in document order heroes=%d/%d "
            "widths=%s" % (len(rises), len(widths), heroes,
                           1 if widths else 0,
                           "/".join(str(w) for w in widths[:6])
                           + ("+%d" % (len(widths) - 6) if len(widths) > 6
                              else "") or NOTHING))


def check_weight(page, model):
    n = len(page.encode("utf-8"))
    return ("pageBytes", n <= PAGE_BYTE_CAP,
            "pageBytes=%d/%d cap (%.0f%% of it, %d picture(s))"
            % (n, PAGE_BYTE_CAP, 100.0 * n / PAGE_BYTE_CAP, model["shown"]))


def check_back_link(page, model):
    n = len(re.findall(r'href="%s"' % re.escape(SIBLING[0]), page))
    return ("backLink", n == 1, "backLink=%d/1 href(s)-to-%s" % (n, SIBLING[0]))


def check_nothing_else(page, model):
    """NOTHING ELSE, ruled. The page may carry pictures and one foot line, so
    the count of text-bearing elements outside the foot must be zero. Headings,
    paragraphs and lists are what "commentary" would arrive as."""
    body = page.split('<body id="gallery">', 1)[-1]
    extra = re.findall(r"<(h[1-6]|table|ul|ol|nav|section|blockquote)\b", body)
    paras = len(re.findall(r"<p\b", body))
    return ("nothingElse", not extra and paras <= 1,
            "commentaryElements=%d paragraphs=%d/1-allowed(the-foot) "
            "tagsExamined=%d" % (len(extra), paras,
                                 len(re.findall(r"<\w+", body))))


def check_count_announced(page, model):
    """A CAP THAT DOES NOT SAY IT BIT READS AS A FINDING. When pictures were
    dropped the foot must say so; when none were, the foot still prints the
    count against its denominator."""
    said = re.search(r"(\d+) of (\d+) shown", page)
    bit = model["packed"]["notShown"] > 0
    announced = "not shown" in page
    ok = bool(said) if model["imagesFound"] else NOTHING in page or \
        "nothing measured" in page
    if bit:
        ok = ok and announced
    return ("countAnnounced", bool(ok),
            "footSaysCount=%s notShown=%d/%d announced=%s"
            % (said.group(0).replace(" ", "-") if said else NOTHING,
               model["packed"]["notShown"], model["imagesFound"], announced))


CHECKS = (check_biggest_first, check_count_announced, check_nothing_else,
          check_back_link, check_weight, check_viewport, check_width,
          check_external, check_formatting, check_secrets)


def run_checks(page, model):
    return [f(page, model) for f in CHECKS]


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


def selftest():
    passed, failed = 0, []
    now = datetime.datetime(2026, 9, 6, 7, 0)

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s\n         got: %s" % (name, got))

    print("%s --selftest: ACCEPTING CASE FIRST, the live repository\n" % TOOL)
    page, model = build(ROOT, now)
    checks = run_checks(page, model)
    bad = [n for n, c, _ in checks if not c]
    ok("the live repository renders a gallery and every check passes "
       "(%d picture(s) of %d found, %d check(s))"
       % (model["shown"], model["imagesFound"], len(checks)),
       model["shown"] >= 1 and not bad,
       "failed=%s" % (",".join(bad) or "none"))
    ok("the newest picture is the hero and it is the widest (%s at %d px)"
       % (model["shots"][0]["rel"] if model["shots"] else NOTHING,
          model["shots"][0]["width"] if model["shots"] else 0),
       bool(model["shots"]) and model["shots"][0]["width"] == HERO_WIDTH_PX,
       model["shots"][0]["width"] if model["shots"] else NOTHING)
    # THE ORDER IS READ FROM THE ORDER, NOT FROM WHAT SURVIVED THE BUDGET.
    # model["shots"] is the KEPT list, so on a runner with no Pillow (where
    # every picture embeds at full size and the big ones are skipped) this
    # assertion would go red and take the workflow step down with it, which
    # contradicts that step's own "not fatal" comment. find_pictures() is the
    # ordering, and the ordering is the ruled property.
    ordered, _reading = find_pictures(ROOT)
    ok("the four Unreal frames are the newest four IN THE ORDER, by commit "
       "time and not by file time (datedByCommit=%d/%d, read from "
       "find_pictures and not from what the budget kept)"
       % (model["datedByCommit"], model["imagesFound"]),
       all("d1-probe" in s["rel"] for s in ordered[:4]),
       [s["rel"] for s in ordered[:4]])
    # WHETHER THEY ALSO SURVIVED, PRINTED BESIDE THE RESIZER AND NEVER FAILING.
    # Without Pillow they will not survive, and that is a fact about the
    # runner rather than a fault in the page: tools/gallery.py's own exit 1 and
    # publish-glance's NOTE already carry it. Reported here so the suite cannot
    # be read as saying the newest frames are on the page when they are not.
    kept_rels = {s["rel"] for s in model["shots"]}
    newest_kept = sum(1 for s in ordered[:4] if s["rel"] in kept_rels)
    print("    reading, not an assertion: newestFourKept=%d/4 resizer=%s "
          "picturesShown=%d/%d%s"
          % (newest_kept, model["resizer"], model["shown"],
             model["imagesFound"],
             "" if newest_kept == 4 else
             " (the newest frames did NOT fit; with resizer=none that is the "
             "cause, and gallery.py exits 1 saying so)"))
    print("\n  THE SERIES this run printed, which is what a count bound would "
          "be read off:\n")
    for row in model["packed"]["series"][:12]:
        print("    %-52s %7d bytes %s" % (row["rel"], row["bytes"],
                                          "kept" if row["kept"]
                                          else "NOT-SHOWN/" + row["why"]))
    if len(model["packed"]["series"]) > 12:
        print("    (+%d more row(s) not shown of %d)"
              % (len(model["packed"]["series"]) - 12,
                 len(model["packed"]["series"])))

    # ACCEPTING 2: A SYNTHETIC TREE, ordered by file time because git knows
    # nothing about it. Three planted pictures, newest first, and the order is
    # the fixture's own mtimes rather than the repository's history.
    t = _tree({"production/d1-probe/a.png": FIXTURE_PNG,
               "production/d1-probe/b.png": FIXTURE_PNG,
               "game-design/sim-shots/c.png": FIXTURE_PNG},
              {"production/d1-probe/a.png": 1000,
               "production/d1-probe/b.png": 3000,
               "game-design/sim-shots/c.png": 2000})
    p2, m2 = build(t, now)
    order = [s["rel"].rsplit("/", 1)[-1] for s in m2["shots"]]
    ok("a tree git knows nothing about orders by file time, newest first "
       "(datedByMtime=%d/%d): %s" % (m2["datedByMtime"], m2["imagesFound"],
                                     "/".join(order)),
       order == ["b.png", "c.png", "a.png"], order)
    ok("and its widths never increase down the page (%s)"
       % check_biggest_first(p2, m2)[2],
       check_biggest_first(p2, m2)[1])

    print("\n  REJECTING FIXTURES, all synthetic:\n")
    # REJECTING 1: NOTHING TO SHOW. The page must say the words, not render an
    # empty frame that on a phone looks like a page that failed to load.
    empty = _tree({"production/d1-probe/notes.txt": b"hello\n"})
    p3, m3 = build(empty, now)
    ok("a tree with no picture at all renders the words 'nothing measured' "
       "rather than an empty page (imagesFound=%d/%d dir(s) walked)"
       % (m3["imagesFound"], m3["dirsWalked"]),
       m3["shown"] == 0 and "nothing measured" in p3
       and "<img" not in p3, p3[-200:])
    ok("and that page still carries exactly one link back",
       check_back_link(p3, m3)[1], check_back_link(p3, m3)[2])

    # REJECTING 2: THE BUDGET BITES AND THE PAGE SAYS SO. A budget of one byte
    # over the shell fits nothing, so every picture is dropped and the foot
    # must announce it.
    p4, m4 = build(t, now, budget=len(PAGE % (CSS % COLUMNS, "")) + 401)
    ok("a budget too small to hold anything drops every picture and the foot "
       "announces it (notShown=%d/%d)"
       % (m4["packed"]["notShown"], m4["imagesFound"]),
       m4["shown"] == 0 and m4["packed"]["notShown"] == m4["imagesFound"]
       and "not shown" in p4, p4[-260:])
    ok("and the drop recorded the budget used AT THE INSTANT it bit, named so",
       (m4["packed"]["droppedAt"] or {}).get("usedAtDrop") is not None,
       m4["packed"]["droppedAt"])

    # REJECTING 3: THE ORDER CHECK CAN FAIL. A guard that cannot go red on a
    # bad page is a ratchet, so a page with widths that grow is planted.
    rising = p2.replace('data-w="%d"' % HERO_WIDTH_PX,
                        'data-w="%d"' % (REST_WIDTH_PX // 2), 1)
    ok("a page whose widths GROW down the page is refused by biggestFirst",
       not check_biggest_first(rising, m2)[1],
       check_biggest_first(rising, m2)[2])
    # REJECTING 4: commentary is refused.
    chatty = p2.replace('<p class="foot">',
                        '<h2>what changed today</h2><p class="foot">')
    ok("a page carrying a heading is refused by nothingElse",
       not check_nothing_else(chatty, m2)[1],
       check_nothing_else(chatty, m2)[2])
    # REJECTING 5: an unannounced truncation is refused.
    silent = p4.replace("not shown, the page budget bit", "")
    ok("a truncation that does not say it bit is refused by countAnnounced",
       not check_count_announced(silent, m4)[1],
       check_count_announced(silent, m4)[2])

    print("\n%s --selftest: %s. %d passed, %d failed, over %d check(s) and "
          "%d rejecting fixture(s)"
          % (TOOL, "PASS" if not failed else "FAILED", passed, len(failed),
             len(CHECKS), 5))
    for f in failed:
        print("  " + f)
    return 0 if not failed else 3


# -------------------------------------------------------------------- the CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", default=None)
    ap.add_argument("--now", default=None, help="ISO clock, for the stamp")
    ap.add_argument("--budget", type=int, default=PAGE_BYTE_CAP)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    root = pathlib.Path(args.root).resolve()
    out = pathlib.Path(args.out) if args.out else root / OUT_NAME
    now = (datetime.datetime.fromisoformat(args.now) if args.now
           else datetime.datetime.now(datetime.timezone.utc))
    page, model = build(root, now, args.budget)
    # WRITTEN EVEN WHEN IT IS THIN, and deliberately over the previous file:
    # tools/map.py's rule, for its reason. A stale gallery that still looks
    # current is worse than one that says it holds nothing.
    out.write_text(page, encoding="utf-8")
    checks = run_checks(page, model)
    bad = [n for n, c, _ in checks if not c]
    packed = model["packed"]
    # PER-PICTURE NUMBERS ON THE PICTURE'S LINE. A grep across lines must not
    # be able to read one picture's bytes as the page's.
    for row in packed["series"]:
        print("gallery: shot=%s bytes=%d %s"
              % (row["rel"], row["bytes"],
                 ("kept usedAfter=%d width=%d" % (row["usedAfter"],
                                                  row["width"]))
                 if row["kept"] else "notShown=%s" % row["why"]))
    if model["dirsAbsent"]:
        print("gallery: dirsAbsent=%s of the %d named"
              % (",".join(model["dirsAbsent"]), model["dirsNamed"]))
    # THE EXIT CODE IS DECIDED FIRST AND THE WORD IS DERIVED FROM IT, so the
    # two can never disagree. They did: a run with no resizer that dropped 34
    # of 36 pictures printed the word DONE beside exit 1, and a grep for the
    # word would have read that run as a success.
    starved = bool(packed["notShown"]) and model["resizer"] == "none"
    if not model["imagesFound"]:
        code, word = 2, "NOTHING-MEASURED"
    elif bad or starved:
        code, word = 1, "REFUSED"
    else:
        code, word = 0, "DONE"
    # WHOLE-RUN NUMBERS ON THE DONE LINE, and every zero beside what it counted.
    print("gallery: wrote %s %s" % (out, " ".join(s for _, _, s in checks)))
    print("gallery: %s picturesShown=%d/%d-found dirsWalked=%d/%d "
          "clipsFound=%d/%d-suffixes-examined datedByCommit=%d/%d "
          "pageBytes=%d/%d-budget notShown=%d resizer=%s checksFailed=%d/%d"
          % (word,
             model["shown"], model["imagesFound"], model["dirsWalked"],
             model["dirsNamed"], model["clipsFound"], len(CLIP_SUFFIXES),
             model["datedByCommit"], model["imagesFound"],
             len(page.encode("utf-8")), args.budget, packed["notShown"],
             model["resizer"], len(bad), len(CHECKS)))
    if starved:
        print("gallery: %d picture(s) were dropped with NO RESIZER installed. "
              "Pillow is absent, so every picture was embedded at its full "
              "size and the budget bit early. This is a fixable cause and it "
              "is not the same fact as 'the repository has that many pictures'."
              % packed["notShown"])
    return code


if __name__ == "__main__":
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
