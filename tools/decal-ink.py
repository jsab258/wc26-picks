#!/usr/bin/env python3
"""WHAT EACH DECAL SET ACTUALLY LAYS DOWN — the numbers behind DecalLayer.

    python3 tools/decal-ink.py             # the table, every set on disk
    python3 tools/decal-ink.py --set X     # one set, named
    python3 tools/decal-ink.py --selftest  # check the instrument

WHY. `DecalLayer.RoadWeight` picks one road texture over another by a series of
nine "ink" numbers written into its comment, and `LoadSet` decides three
different things about a set — is its colour map really a mask, does it have an
opacity map at all, how dark can it get — from arithmetic explained in prose
beside it. Every one of those numbers was measured once, by hand, in a session
nobody can re-run. A comment is a claim with no test attached (CLAUDE.md rule 1,
second corollary); these ones steer what the street looks like, and the next
person to fetch a texture has no way to place it in the series except by
trusting a paragraph.

This is that measurement as a tool. It reads the ROSTER AND THE WEIGHTS OUT OF
`DecalLayer.cs` rather than keeping its own copy, so the table cannot describe a
set the game no longer names, and it prints the ink series in the exact units
the comment quotes — which is how the comment stays checkable.

IT REPRODUCES THE HAND MEASUREMENT, which is the only reason to believe either.
Run 24 Aug 2026 against the shipped 2K files, every road number identical to the
series in `RoadWeight`'s comment to three decimals (ManholeCover011 0.372,
AsphaltDamageSet001 0.113, SurfaceImperfections003 0.071, 012 0.061,
RoadLines004 0.045, 018 0.041, 011 0.014, 010 0.009, 007 0.006), the wall series
identical to the one measured for `WallWeight` (Moss001 0.197, SI001 0.072,
Leaking005 0.053, SI007 0.013, Scratches003 0.013, of which `LoadSet`'s own
comment quotes the first), the mask separations identical (Leaking005 174,
RoadLines018 206, ManholeCover011 236) and the floors identical (SI003 0.543,
SI012 0.479, and on walls SI001 0.619, SI007 and Scratches003 0.544). Two
implementations, one answer.

IT ALSO CORRECTED ONE OF THEM, which is the better argument for it. `RoadSets`'
comment called RoadLines001 "the highest ink of any road set in the bank"; it is
0.187 at road strength against ManholeCover011's 0.372, and the 0.231 it quoted
was in raw units the rest of the paragraph does not use. The claim was true of
the RoadLines family and false as written, and it stood for as long as nobody
could re-run the measurement.

--------------------------------------------------------------------------
WHAT IT MEASURES, AND WHAT EACH NUMBER IS A STATISTIC OF.

The shader is `Assets/Resources/LedgerDecal.shader`, one line of it:

    mul = lerp(1, rgb, a * strength)   ->   1 - a*strength*(1 - rgb)

so a decal MULTIPLIES the surface under it and `a*strength*(1-rgb)` is the
darkening it lays down, per pixel, per channel.

  ink        MEAN over every pixel of alpha*(1-luma)*strength — the average
             darkening the set delivers across its whole quad. This is the
             number the pick weights are derived from, and the mean is right
             for that question: a weight decides how much of the street a set
             covers, so what matters is what it does on average, not at worst.
  meanAlpha  MEAN alpha. Beside `ink` because the two move together for a
             mask set and independently for a colour one, and a set can carry
             ink either by covering a lot faintly or a little blackly.
  cover50    FRACTION of pixels with alpha above 0.5. The other half of the
             sentence above: Leaking005 and Moss001 differ by 4x in ink and by
             130x in coverage, and a wall covered in one does not look like a
             wall covered in the other at any weight.
  floor      MINIMUM over pixels of the multiplier — the darkest the set can
             take a surface. A minimum, so ONE pixel sets it (rule 2's
             `crowdTightest`), which is why `floorP01` prints beside it: the
             1st percentile is what a viewer sees as the dark part of the mark.
  floorReach 1 - strength. The darkest multiply mode can go AT ALL, at this
             strength, for a fully opaque fully black pixel. `floor`'s
             denominator: 0.54 means nothing until you know 0.20 was reachable.
  maskDelta  MAXIMUM over pixels of |luma(Color) - Opacity.r|, in 0..255. This
             is `LoadSet`'s mask-as-colour test, printed rather than asserted:
             0 means the set banks ONE grayscale image under both names and
             `LoadSet` retints it, anything else means a genuine colour map.
             A maximum is the right statistic here and the only one that is —
             the test is "are these identical everywhere", and a mean of the
             differences would call a set with one clean half a mask.

ALL OF IT AFTER `LoadSet`'s TRANSFORMS, not on the raw files, because the raw
files are not what the shader samples. A mask set is measured with its rgb
already replaced by MASK_TINT and its alpha already taken from the mask; a set
with no opacity map is measured with alpha = 255 - luma. The tool follows the
loader branch for branch and prints which one it took (`alphaFrom`), so a set
that changes branch when it is refetched says so.

--------------------------------------------------------------------------
THE THREE THINGS THAT MUST NOT BE SWALLOWED (rule 3b — a zero needs a
denominator, and a filter that stops reporting is worse than a zero).

  * NO DIRECTORY. The whole point of `DecalLayer` is that a missing fetch is
    not an error, so this must not print an empty table and exit clean either.
    It prints NOTHING MEASURED with the path it looked at and the count of
    directories it found there, and exits 2.
  * A DIMENSION MISMATCH IS A FAULT, NOT A SKIP, and it is invisible in the
    game. `LoadSet` only merges the opacity map when `op.width == tex.width`;
    when they differ it silently keeps the colour map's own alpha, which for an
    RGB source is 255 EVERYWHERE — a solid opaque rectangle stamped on the
    road, reported by nothing. Any set in that state is printed with `alphaFrom
    =opaqueRect!` and counted in `mismatched=` on the summary.
  * A SET ON DISK THAT THE GAME NAMES NOWHERE is listed with role=unnamed and
    counted. It is not an error — the fetches are deliberately broad — but an
    unnamed set is a fetched thing with no consumer, and rule 6 says that state
    should be visible rather than quiet.

--------------------------------------------------------------------------
WHAT IT DOES NOT KNOW. Ink is a proxy for "how much does this darken", not for
"is this the right mark for a British port town". RoadLines001 has more ink than
seven of the nine road sets and was dropped from the roster anyway, because its
ink was all background — the tool cannot see that and a person could in one
glance. Read the table beside the texture, never instead of it (rule 4: LOOKING
IS NOT MEASURING, and its converse).
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DECALS = ROOT / "ledger" / "Assets" / "StreamingAssets" / "Decals" / "ambientcg"
LAYER = ROOT / "ledger" / "Assets" / "Scripts" / "Game" / "DecalLayer.cs"

IMG_EXTS = (".png", ".jpg")

# The strengths `Place` is called with, from DecalLayer's two loops. NOT free
# numbers and not this tool's to choose — the selftest greps the C# for them, so
# a change there fails here rather than quietly re-scaling every number below.
ROAD_STRENGTH = 0.8         # the road loop's Place(..., size, 0.8f)
WALL_STRENGTH = 0.7         # the wall loop's streak strength; damp is 0.55
WALL_DAMP_STRENGTH = 0.55   # scales every wall number by 0.79, ranks nothing

# `LoadSet`'s MaskTint, as a byte. 89 = 0.35*255, one and a half stops.
MASK_TINT = 89


def _where(path):
    """A path as the reader knows it — repo-relative when it is in the repo,
    absolute when the selftest has pointed the tool at a temporary bank."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


class Unreadable(Exception):
    """An image that would not open or decode. Carried, never swallowed — a
    table that quietly drops a set reports a smaller bank as a cleaner one."""


# ------------------------------------------------------------- reading the C#

def _strip_cs(text):
    """Comments out, so a roster quoted in prose cannot be read as code.

    `verdict-emit-dupkeys.py` learned this the expensive way and its docstring
    says why: DecalLayer's own comments quote `"RoadLines001"` twice while
    explaining why it is NOT in the roster, and a regex over the raw file would
    put it back in."""
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def roster():
    """{set: role} from DecalLayer's RoadSets and WallSets arrays.

    Read out of the source rather than copied, so this tool cannot describe a
    roster the game has stopped having. A set named in neither is not in here;
    `sets_on_disk` is what supplies the ones with no consumer."""
    src = _strip_cs(LAYER.read_text(encoding="utf-8"))
    out = {}
    for field, role in (("RoadSets", "road"), ("WallSets", "wall")):
        m = re.search(r"\b%s\s*=\s*\{(.*?)\}" % field, src, re.S)
        if not m:
            raise Unreadable("DecalLayer.cs: no %s array found" % field)
        for name in re.findall(r'"([^"]+)"', m.group(1)):
            out[name] = role
    return out


def weights(method):
    """{set: weight} plus {"default": n} from a `switch` in DecalLayer.

    Returns None when the method does not exist, which is a real answer: a pool
    with no weight function picks uniformly, and the table says so rather than
    printing a column of 1s that look deliberate."""
    src = _strip_cs(LAYER.read_text(encoding="utf-8"))
    m = re.search(r"static int %s\s*\([^)]*\)\s*\{(.*?)\n        \}" % method,
                  src, re.S)
    if not m:
        return None
    body = m.group(1)
    out = {n: int(v) for n, v in
           re.findall(r'case\s+"([^"]+)"\s*:\s*return\s+(\d+)\s*;', body)}
    d = re.search(r"default\s*:\s*return\s+(\d+)\s*;", body)
    out["default"] = int(d.group(1)) if d else 1
    return out


# ------------------------------------------------------------------ measuring

def _np():
    import numpy
    return numpy


def pick_files(d):
    """The colour and opacity files `LoadSet` would pick, by its own rules.

    ITS RULES, not better ones: lowercase name contains "color"/"colour" wins,
    else "opacity", and with no colour map at all the FIRST image in the
    directory is taken as the main texture. The C# reads `Directory.GetFiles`,
    whose order is not specified; this sorts, and prints `alphaFrom=any!` in the
    one case where the difference could matter — a set with no colour map, of
    which the bank currently has none."""
    colour = opacity = first = None
    for f in sorted(d.iterdir()):
        n = f.name.lower()
        if not n.endswith(IMG_EXTS):
            continue
        if "color" in n or "colour" in n:
            colour = f
        elif "opacity" in n:
            opacity = f
        if first is None:
            first = f
    return colour, opacity, first


def _luma(np, rgb):
    """`LoadSet`'s luminance, byte for byte: integer 30/59/11 over 100, with
    C#'s truncating division. Not Rec.709 and not floating point — the mask test
    is an EQUALITY against these values, so a fifth of a level of drift would
    turn a mask into a colour map."""
    r = rgb[..., 0].astype(np.int32)
    g = rgb[..., 1].astype(np.int32)
    b = rgb[..., 2].astype(np.int32)
    return (r * 30 + g * 59 + b * 11) // 100


def measure(d, strength):
    """One set directory, through `LoadSet`'s branches, as numbers.

    Raises Unreadable for anything that stops it being measured; the caller
    names it in the table and counts it in the summary."""
    from PIL import Image, ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = False     # a half-written PNG must fail
    np = _np()

    colour, opacity, first = pick_files(d)
    main = colour or first
    if main is None:
        raise Unreadable("no .png or .jpg in the directory")
    try:
        img = Image.open(main)
        img = img.convert("RGB")
        img.load()
    except Exception as exc:                    # noqa: BLE001 — named, not hidden
        raise Unreadable("%s: %s" % (main.name, exc))
    rgb = np.asarray(img, dtype=np.uint8)
    h, w = rgb.shape[0], rgb.shape[1]
    lum = _luma(np, rgb)

    mask_delta = None
    if opacity is None:
        # LoadSet's no-opacity branch: darkness IS the stain.
        alpha = 255 - lum
        source = "invLuma"
    else:
        try:
            op = Image.open(opacity)
            op = op.convert("RGB")
            op.load()
        except Exception as exc:                # noqa: BLE001
            raise Unreadable("%s: %s" % (opacity.name, exc))
        oa = np.asarray(op, dtype=np.uint8)
        if oa.shape[0] != h or oa.shape[1] != w:
            # THE SILENT ONE. LoadSet skips the merge and leaves the colour
            # map's own alpha, which for an RGB source is opaque everywhere.
            alpha = np.full((h, w), 255, dtype=np.int32)
            source = "opaqueRect!"
            mask_delta = -1
        else:
            alpha = oa[..., 0].astype(np.int32)
            mask_delta = int(np.abs(lum - alpha).max())
            source = "opacity"
            if mask_delta == 0:
                lum = np.full_like(lum, MASK_TINT)   # the retint, exactly
                source = "opacity/masked"

    a = alpha.astype(np.float64) / 255.0
    l = lum.astype(np.float64) / 255.0
    darken = a * strength * (1.0 - l)
    mul = 1.0 - darken
    return {
        "px": int(h) * int(w),
        "dims": "%dx%d" % (w, h),
        "alphaFrom": source,
        "maskOnly": mask_delta == 0,
        "maskDelta": mask_delta,
        "ink": float(darken.mean()),
        "meanAlpha": float(a.mean()),
        "meanLuma": float(l.mean()),
        "cover50": float((alpha > 127).mean()),
        "floor": float(mul.min()),
        "floorP01": float(np.percentile(mul, 1.0)),
        "floorReach": 1.0 - strength,
        "colour": main.name,
        "opacity": opacity.name if opacity is not None else "-",
    }


def sets_on_disk():
    if not DECALS.is_dir():
        return None
    return sorted(p for p in DECALS.iterdir() if p.is_dir())


# -------------------------------------------------------------------- report

def report(only=None):
    known = roster()
    pools = {"road": (ROAD_STRENGTH, weights("RoadWeight")),
             "wall": (WALL_STRENGTH, weights("WallWeight"))}

    dirs = sets_on_disk()
    if dirs is None:
        print("decal-ink: NOTHING MEASURED — no decal directory at %s"
              % _where(DECALS))
        print("decalInk scope=summary setsExamined=0 pixelsExamined=0 "
              "dirsFound=0 nothingMeasured=yes")
        return 2
    if only is not None:
        dirs = [p for p in dirs if p.name == only]
        if not dirs:
            print("decal-ink: no set called %s (of %d on disk)"
                  % (only, len(sets_on_disk())))
            return 2

    rows, bad = [], []
    for d in dirs:
        role = known.get(d.name, "unnamed")
        strength = pools[role][0] if role in pools else ROAD_STRENGTH
        try:
            m = measure(d, strength)
        except Unreadable as exc:
            bad.append((d.name, str(exc)))
            rows.append({"set": d.name, "role": role, "px": 0, "why": str(exc)})
            continue
        m["set"] = d.name
        m["role"] = role
        m["strength"] = strength
        w = pools[role][1] if role in pools else None
        m["weight"] = None if w is None else w.get(d.name, w["default"])
        rows.append(m)

    print("DECAL INK — %d set(s) under %s" % (len(rows), _where(DECALS)))
    print("ink = mean(alpha*(1-luma))*strength, the darkening the shader lays "
          "down per pixel.")
    print("READ ink WITH cover50: the same ink spread over half a quad and over "
          "a fiftieth of one")
    print("are not the same mark. floor is a MINIMUM (one pixel sets it); "
          "floorP01 is the dark part")
    print("a viewer sees. Roads measured at strength %.2f, walls at %.2f "
          "(damp %.2f scales all of"
          % (ROAD_STRENGTH, WALL_STRENGTH, WALL_DAMP_STRENGTH))
    print("them by 0.79 and reorders none). A set the game names NOWHERE has no "
          "pool and no")
    print("strength of its own, so it is measured at the road one and its ink "
          "is comparable to")
    print("the road pool's — `strength=` on every machine line below says which "
          "was used.")
    print()
    head = ("%-26s %-8s %-14s %6s %6s %7s %6s %6s %6s  %s"
            % ("set", "role", "alphaFrom", "ink", "mAlpha", "cover50",
               "floor", "flrP01", "delta", "dims"))
    print(head)
    print("-" * len(head))
    for r in sorted(rows, key=lambda r: (-r.get("ink", -1.0), r["set"])):
        if r["px"] == 0:
            print("%-26s %-8s %-14s  UNREADABLE — %s"
                  % (r["set"], r["role"], "-", r["why"]))
            continue
        print("%-26s %-8s %-14s %6.3f %6.3f %7.3f %6.3f %6.3f %6s  %s"
              % (r["set"], r["role"], r["alphaFrom"], r["ink"], r["meanAlpha"],
                 r["cover50"], r["floor"], r["floorP01"],
                 "-" if r["maskDelta"] is None else r["maskDelta"], r["dims"]))

    # ---- the pools, in the units the C# comments quote, with the share each
    # weight actually buys. This block is what makes RoadWeight's series
    # re-derivable rather than remembered.
    for role in ("road", "wall"):
        pool = [r for r in rows if r["role"] == role and r["px"]]
        if not pool:
            continue
        wmap = pools[role][1]
        total = sum(r["weight"] or 0 for r in pool) if wmap else 0
        print()
        print("%s pool — %d set(s), strength %.2f, %s"
              % (role.upper(), len(pool), pools[role][0],
                 "weighted pick" if wmap else "UNIFORM pick (no weight function)"))
        for r in sorted(pool, key=lambda r: -r["ink"]):
            share = ("%5.1f%%" % (100.0 * r["weight"] / total)) if total else "    -"
            print("    %-26s ink=%.3f  weight=%-4s share=%s  cover50=%.3f"
                  % (r["set"], r["ink"],
                     "-" if r["weight"] is None else r["weight"], share,
                     r["cover50"]))
        if total:
            print("    ink spread %.1fx over %d sets; pick spread %.1fx"
                  % (max(r["ink"] for r in pool)
                     / max(1e-9, min(r["ink"] for r in pool)), len(pool),
                     max(r["weight"] for r in pool)
                     / max(1, min(r["weight"] for r in pool))))

    unnamed = [r["set"] for r in rows if r["role"] == "unnamed"]
    mismatched = [r["set"] for r in rows if r.get("alphaFrom") == "opaqueRect!"]
    masked = [r["set"] for r in rows if r.get("maskOnly")]
    px = sum(r.get("px", 0) for r in rows)
    print()
    if unnamed:
        print("NAMED BY NOTHING (fetched, no consumer — rule 6): %s"
              % ", ".join(unnamed))
    if mismatched:
        print("DIMENSION MISMATCH — LoadSet keeps the colour map's own alpha "
              "for these, so they")
        print("draw as SOLID opaque rectangles: %s" % ", ".join(mismatched))
    for name, why in bad:
        print("UNREADABLE %s — %s" % (name, why))
    print()
    for r in sorted(rows, key=lambda r: r["set"]):
        if not r["px"]:
            print("decalInk set=%s role=%s px=0 unreadable=yes" % (r["set"], r["role"]))
            continue
        print("decalInk set=%s role=%s alphaFrom=%s strength=%.2f ink=%.4f "
              "meanAlpha=%.4f meanLuma=%.4f cover50=%.4f floor=%.4f "
              "floorP01=%.4f floorReach=%.4f maskDelta=%s weight=%s px=%d "
              "dims=%s"
              % (r["set"], r["role"], r["alphaFrom"], r["strength"], r["ink"],
                 r["meanAlpha"], r["meanLuma"], r["cover50"], r["floor"],
                 r["floorP01"], r["floorReach"],
                 "none" if r["maskDelta"] is None else r["maskDelta"],
                 "none" if r["weight"] is None else r["weight"],
                 r["px"], r["dims"]))
    print("decalInk scope=summary setsExamined=%d pixelsExamined=%d "
          "namedRoad=%d namedWall=%d unnamed=%d masked=%d mismatched=%d "
          "unreadable=%d"
          % (len(rows), px,
             len([r for r in rows if r["role"] == "road"]),
             len([r for r in rows if r["role"] == "wall"]),
             len(unnamed), len(masked), len(mismatched), len(bad)))
    return 1 if (bad or mismatched) else 0


# ------------------------------------------------------------------ selftest

def selftest():
    """ACCEPTING CASE FIRST (rule 5b). The live decal bank is the fixture, and
    it is the one nobody can fake: the sets are tracked, the game reads the same
    bytes, and doing the work this tool prompts — fetching a set, renaming a
    roster — changes the fixture rather than breaking it."""
    global DECALS, LAYER
    import contextlib
    import io
    import shutil
    import tempfile

    ok, fails = 0, []

    def check(name, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fails.append(name)

    def run(*args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = report(*args)
        return code, buf.getvalue()

    np = _np()
    from PIL import Image

    # ---- 1. ACCEPTING: the live bank produces a whole table.
    code, text = run()
    disk = sets_on_disk() or []
    check("accepting: the live bank reports clean", code == 0)
    check("accepting: every set on disk has a machine line",
          all(("decalInk set=%s " % p.name) in text for p in disk))
    check("accepting: the summary carries its denominators",
          "setsExamined=%d" % len(disk) in text and "pixelsExamined=" in text)
    check("accepting: pixels examined is a real count",
          int(text.split("pixelsExamined=")[1].split()[0]) > 10 ** 7)
    check("accepting: no machine token carries a space or splits",
          all(tok.count("=") == 1 for line in text.splitlines()
              if line.startswith("decalInk ") for tok in line.split()[1:]))
    check("accepting: both pools print their share arithmetic",
          "ROAD pool" in text and "WALL pool" in text)
    check("accepting: the cover50 caveat rides beside ink",
          "READ ink WITH cover50" in text)
    check("accepting: an unnamed set is named as such",
          ("unnamed=0" in text) or "NAMED BY NOTHING" in text)

    # ---- 2. THE ROSTER AND THE WEIGHTS COME FROM THE C#, NOT FROM HERE.
    known = roster()
    check("roster: the road pool is read out of DecalLayer",
          len([k for k, v in known.items() if v == "road"]) >= 5)
    check("roster: the wall pool is read out of DecalLayer",
          len([k for k, v in known.items() if v == "wall"]) >= 3)
    check("roster: a set quoted only in a comment is NOT read as rostered",
          "RoadLines001" in LAYER.read_text(encoding="utf-8")
          and "RoadLines001" not in known)
    rw = weights("RoadWeight")
    check("weights: RoadWeight is parsed with its default",
          rw is not None and rw.get("default") == 1
          and rw.get("AsphaltDamageSet001") == 6)
    check("weights: a method that does not exist returns None, not {}",
          weights("NoSuchWeightFunction") is None)

    # THE STRENGTHS ARE THE C#'s, AND THIS IS THE ONLY THING KEEPING THEM SO.
    # Every number in the table scales with them; a change in DecalLayer that
    # this file did not follow would re-scale the whole series silently, which
    # is the comment-decay fault one layer down.
    cs = LAYER.read_text(encoding="utf-8")
    check("strength: the road loop still places at 0.8",
          "pos, Quaternion.Euler(90f, yaw, 0), size, 0.8f)" in cs)
    check("strength: the wall loop still places at 0.7/0.55",
          "streak ? 0.7f : 0.55f" in cs)
    check("tint: LoadSet still retints masks to 89",
          "const byte MaskTint = 89;" in cs)

    # ---- 3. THE ARITHMETIC, on shapes with an answer known in advance.
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="decal-ink-"))
    try:
        def put(name, colour, opacity=None, opsize=None):
            d = tmp / name
            d.mkdir()
            Image.fromarray(colour, "RGB").save(d / ("%s_2K-PNG_Color.png" % name))
            if opacity is not None:
                img = Image.fromarray(opacity, "RGB")
                if opsize:
                    img = img.resize(opsize, Image.NEAREST)
                img.save(d / ("%s_2K-PNG_Opacity.png" % name))
            return d

        white = np.full((64, 64, 3), 255, np.uint8)
        black = np.zeros((64, 64, 3), np.uint8)
        opaque = np.full((64, 64, 3), 255, np.uint8)
        # OPAQUE, BUT NOT MASK-IDENTICAL. A fully white colour map beside a
        # fully white opacity map is byte-identical, so `LoadSet` correctly
        # calls it a mask and retints it — which makes it useless as a fixture
        # for the identity case. One pixel off breaks the identity and changes
        # nothing else, and the tool caught this before the tool shipped.
        nearly = opaque.copy()
        nearly[0, 0] = 254

        m = measure(put("WhiteOpaque", white, nearly), 0.8)
        check("white is the multiply identity: ink 0 over a real denominator",
              m["ink"] == 0.0 and m["px"] == 4096)
        check("white: floor is 1.0 and floorReach still says 0.2",
              m["floor"] == 1.0 and abs(m["floorReach"] - 0.2) < 1e-9)

        m = measure(put("BlackOpaque", black, opaque), 0.8)
        check("black opaque: ink is exactly the strength",
              abs(m["ink"] - 0.8) < 1e-9)
        check("black opaque: floor reaches the mode's floor",
              abs(m["floor"] - 0.2) < 1e-9)
        check("black opaque: cover50 is 1.0", m["cover50"] == 1.0)

        half = np.full((64, 64, 3), 128, np.uint8)
        m = measure(put("BlackHalfAlpha", black, half), 0.8)
        check("half alpha halves the ink", abs(m["ink"] - 0.8 * 128 / 255) < 1e-9)
        # 127/255 = 0.498 and 128/255 = 0.502, so the bar falls between two
        # bytes and both sides of it are checked. Named because "above 0.5" and
        # "at least half" are different questions and only one is being asked.
        check("cover50 admits alpha 128, which is above a half", m["cover50"] == 1.0)
        m = measure(put("BlackJustUnder", black,
                        np.full((64, 64, 3), 127, np.uint8)), 0.8)
        check("cover50 refuses alpha 127, which is under it", m["cover50"] == 0.0)

        strip = np.zeros((64, 64, 3), np.uint8)
        strip[:32] = 255
        m = measure(put("HalfCovered", black, strip), 0.8)
        check("cover50 counts the covered half", abs(m["cover50"] - 0.5) < 1e-9)

        grey = np.full((64, 64, 3), 100, np.uint8)
        m = measure(put("MaskTwice", grey, grey), 0.8)
        check("a mask shipped twice is detected", m["maskOnly"] and m["maskDelta"] == 0)
        check("a detected mask is measured RETINTED, not raw",
              m["alphaFrom"] == "opacity/masked"
              and abs(m["ink"] - (100 / 255) * 0.8 * (1 - 89 / 255)) < 1e-9)

        m = measure(put("RealTint", np.full((64, 64, 3), 200, np.uint8), grey), 0.8)
        check("a genuine colour map is not called a mask",
              not m["maskOnly"] and m["maskDelta"] == 100)

        # THE LOADER'S FILENAME RULE IS A LANDMINE AND THIS IS WHERE IT IS
        # WRITTEN DOWN. `LoadSet` classifies by SUBSTRING — a name containing
        # "color" or "colour" is the colour map, checked BEFORE "opacity" — so
        # a set whose ID contains either word has its Opacity file classified as
        # a second colour map, loses its alpha entirely and falls to the
        # inverse-luma branch. No set in the bank is named that way; this fixture
        # was, by accident, and it took the identity check down with it.
        m = measure(put("RealColour", np.full((64, 64, 3), 200, np.uint8), grey), 0.8)
        check("a set NAMED '...Colour' loses its opacity map to the name rule",
              m["alphaFrom"] == "invLuma")

        noop = tmp / "NoOpacity"
        noop.mkdir()
        Image.fromarray(grey, "RGB").save(noop / "NoOpacity_2K-PNG_Color.png")
        m = measure(noop, 0.7)
        check("no opacity map falls back to inverse luma, and says so",
              m["alphaFrom"] == "invLuma"
              and abs(m["meanAlpha"] - (255 - 100) / 255) < 1e-9)

        # ---- 4. REJECTING: the three things that must not be swallowed.
        m = measure(put("Mismatched", black, opaque, opsize=(32, 32)), 0.8)
        check("rejecting: a dimension mismatch is named, not merged",
              m["alphaFrom"] == "opaqueRect!")
        check("rejecting: and it is measured as the solid rectangle it draws",
              m["cover50"] == 1.0 and abs(m["ink"] - 0.8) < 1e-9)

        empty = tmp / "EmptySet"
        empty.mkdir()
        (empty / "notes.txt").write_text("no images here")
        try:
            measure(empty, 0.8)
            check("rejecting: a set with no image raises", False)
        except Unreadable:
            check("rejecting: a set with no image raises", True)

        keep = DECALS
        DECALS = tmp
        code, text = run()
        check("rejecting: a bank of synthetic sets exits 1 for the mismatch",
              code == 1)
        check("rejecting: the mismatch is spelled out, not just flagged",
              "DIMENSION MISMATCH" in text and "mismatched=1" in text)
        check("rejecting: the unreadable set is named with a reason",
              "UNREADABLE EmptySet" in text and "unreadable=1" in text)
        check("rejecting: none of these sets is in the roster, and it says so",
              "NAMED BY NOTHING" in text)
        check("rejecting: a pool with no members prints no share table",
              "ROAD pool" not in text)

        DECALS = tmp / "no-such-directory"
        code, text = run()
        check("rejecting: a missing bank says NOTHING MEASURED", code == 2
              and "NOTHING MEASURED" in text)
        check("rejecting: and it still ships a denominator",
              "setsExamined=0" in text and "pixelsExamined=0" in text)
        DECALS = keep

        # ---- 5. The set filter, and its own denominator.
        code, text = run("ManholeCover011")
        check("--set names one set", code == 0 and "setsExamined=1" in text)
        code, text = run("NotASet")
        check("--set on a name that is not there says how many there are",
              code == 2 and "of %d on disk" % len(disk) in text)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("decal-ink selftest: %d passed, %d failed" % (ok, len(fails)))
    for f in fails:
        print("  FAILED " + f)
    return 1 if fails else 0


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    only = None
    if "--set" in args:
        i = args.index("--set")
        if i + 1 >= len(args):
            print("usage: decal-ink.py [--set NAME | --selftest]")
            print("  --set needs a set name")
            return 2
        only = args[i + 1]
        args = args[:i] + args[i + 2:]
    if args:
        print("usage: decal-ink.py [--set NAME | --selftest]")
        print("  unknown argument(s): %s" % " ".join(args))
        return 2
    return report(only)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:             # `| head` must not end in a traceback
        try:
            sys.stdout.close()
        finally:
            sys.exit(0)
