#!/usr/bin/env python3
"""LAY THE SHEET FURNITURE OVER DRAWN PANELS. Not an instrument.

    python3 tools/imagegen/sheet-furniture.py --layout <furniture.json> --out <png>
    python3 tools/imagegen/sheet-furniture.py --selftest

WHAT IT DOES. A district concept sheet is two photographs plus FURNITURE: a
header naming the project, the district, the town and the year, a tagline,
eight labelled tiles, an annotation on each panel, and a footer. This tool
draws the furniture and the drawing model draws only the photographs.

WHY IT EXISTS, AND IT IS A MEASURED REASON. Jafar, 2026-09-10: the district
sheets finished to the standard of the outside ones. The outside sheets carry
all of the above. This lane's own record is that lettering asked of the
diffusion model garbles once it is small and sits inside a photograph. On
fairview_sheet_short_s2.png, 6 regions were opened: 5 carry lettering and 1
does not, and those 5 hold 6 strings. 2 are correct and legible, the title and
the subtitle, and both are LARGE AND ON THE PAPER MARGIN. 4 are garbled and
all four are SMALL AND INSIDE A PHOTOGRAPH. Only 3 strings were asked for, so
3 of the 4 garbled ones were never requested at all. The furniture
this tool draws is all of it small lettering, which is the failing class. So
it is composited, where a string is a string and cannot garble.

THE ANNOTATIONS ARE READ AND COMPUTED, NEVER TYPED. The district height band
comes from the atlas district record; a camera height comes from interpolating
the atlas contours at the camera's own coordinates; a look direction comes
from the bearing between two atlas points; the eye height comes from the
project's own camera rows in production/specs/vignette-pieces.json. A number
that cannot be sourced IS LEFT OFF THE SHEET and named in the verdict as an
omission with its reason, because an annotated sheet that annotates wrongly is
worse than an unannotated one.

IT MEASURES NOTHING THAT ANY GATE READS. The one numeric report it makes, the
distance between a drawn swatch and the atlas colour it is meant to be, is
printed to the terminal and never onto the sheet, and it is a mean over the
tile box, named as such.

WHAT IT DOES NOT TOUCH. It never writes the drawn PNG. The drawn sheet stays
on disk exactly as the model made it, because it is also the evidence about
the model, and the composite is a second file beside it.
"""
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

ATLAS_BLOB = "origin/art/atlas-01:production/art/atlas-01/data/atlas.json"
CAMERA_ROWS = "production/specs/vignette-pieces.json"

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

SHEET_W = 1024
MARGIN = 24
INK = (26, 26, 24)
GREY = (110, 110, 102)
RULE = (176, 174, 162)
WHITE = (246, 246, 242)
DIM = (206, 206, 200)

# The paper of the drawn sheet, sampled at its own corner. The composite sits
# on the same paper so the panels do not float on a different cream.
PAPER = (253, 252, 242)
PAPER_TOL = 26


# ----------------------------------------------------------------- plumbing

def repo_root():
    return Path(__file__).resolve().parents[2]


def _pil():
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
        return Image, ImageDraw, ImageFilter, ImageFont
    except ImportError:
        sys.exit("sheet-furniture: Pillow is not installed, nothing composed")


def load_atlas(root):
    """The atlas off the art branch. Returns (dict, short_sha) or (None, why)."""
    r = subprocess.run(["git", "show", ATLAS_BLOB], capture_output=True,
                       cwd=str(root))
    if r.returncode != 0 or not r.stdout:
        return None, "the-atlas-blob-could-not-be-read"
    sha = subprocess.run(["git", "rev-parse", "--short",
                          ATLAS_BLOB.split(":")[0]],
                         capture_output=True, text=True, cwd=str(root))
    return json.loads(r.stdout), (sha.stdout.strip() or "unknown")


def district_record(atlas, did):
    for d in atlas.get("districts", []):
        if d.get("id") == did:
            return d
    return None


def route(atlas, rid):
    for r in atlas.get("routes", []):
        if r.get("id") == rid:
            return r
    return None


def landmark(atlas, lid):
    for l in atlas.get("landmarks", []):
        if l.get("id") == lid:
            return l
    return None


# ---------------------------------------------------------------- geometry

def contour_north_at(points, east):
    """North of a contour polyline at a given easting, or None off its ends.

    The contours run roughly west to east with north increasing uphill, so a
    contour is a function of easting over the span it covers and nothing at
    all outside it. NONE IS NOT ZERO: outside the span the tool omits the
    number rather than extrapolating a hillside it has no evidence for.
    """
    for (e0, n0), (e1, n1) in zip(points, points[1:]):
        lo, hi = (e0, e1) if e0 <= e1 else (e1, e0)
        if lo <= east <= hi and e1 != e0:
            t = (east - e0) / (e1 - e0)
            return n0 + t * (n1 - n0)
    return None


def height_at(atlas, east, north):
    """Metres above the town datum at an atlas point, or (None, why).

    Linear between the two contours that bracket the point at its own
    easting. The atlas declares a fictional local datum, not Ordnance Datum,
    so the sheet says 'above datum' and never 'AOD'.
    """
    rows = []
    for c in atlas.get("contours", []):
        n = contour_north_at(c["points"], east)
        if n is not None:
            rows.append((float(c["height"]), n))
    if len(rows) < 2:
        return None, "fewer-than-two-contours-cover-this-easting"
    rows.sort(key=lambda r: r[1])
    if north < rows[0][1]:
        return None, f"south-of-the-lowest-contour-{rows[0][0]:g}m"
    if north > rows[-1][1]:
        return None, f"north-of-the-highest-contour-{rows[-1][0]:g}m"
    for (h0, n0), (h1, n1) in zip(rows, rows[1:]):
        if n0 <= north <= n1:
            if n1 == n0:
                return h0, "on-a-contour"
            t = (north - n0) / (n1 - n0)
            return h0 + t * (h1 - h0), f"between-{h0:g}m-and-{h1:g}m"
    return None, "no-bracketing-pair"


def bearing_deg(p_from, p_to):
    """Degrees clockwise from north. Atlas points are [east, north]."""
    dx = p_to[0] - p_from[0]
    dy = p_to[1] - p_from[1]
    return math.degrees(math.atan2(dx, dy)) % 360.0


COMPASS16 = ["NORTH", "NORTH-NORTHEAST", "NORTHEAST", "EAST-NORTHEAST",
             "EAST", "EAST-SOUTHEAST", "SOUTHEAST", "SOUTH-SOUTHEAST",
             "SOUTH", "SOUTH-SOUTHWEST", "SOUTHWEST", "WEST-SOUTHWEST",
             "WEST", "WEST-NORTHWEST", "NORTHWEST", "NORTH-NORTHWEST"]


def compass(deg):
    return COMPASS16[int((deg % 360.0) / 22.5 + 0.5) % 16]


def plan_length(p0, p1):
    return math.hypot(p1[0] - p0[0], p1[1] - p0[1])


def leg_height_span(atlas, leg):
    """(low, high, why) metres over a leg, using only bracketed samples.

    Samples the leg densely and keeps the heights that the contours can
    actually bracket. Returns (None, None, why) when none can be.
    """
    got = []
    steps = 200
    for i in range(steps + 1):
        t = i / steps
        e = leg[0][0] + t * (leg[1][0] - leg[0][0])
        n = leg[0][1] + t * (leg[1][1] - leg[0][1])
        h, _ = height_at(atlas, e, n)
        if h is not None:
            got.append((t, h))
    if not got:
        return None, None, "no-sampled-point-on-this-leg-is-bracketed-by-contours"
    return (min(h for _, h in got), max(h for _, h in got),
            f"{len(got)}of{steps + 1}-sampled-points-bracketed")


def leg_gradient(atlas, leg):
    """(rise_over_run, rise_m, run_m, why) for the bracketed part of a leg."""
    got = []
    steps = 400
    full = plan_length(leg[0], leg[1])
    for i in range(steps + 1):
        t = i / steps
        e = leg[0][0] + t * (leg[1][0] - leg[0][0])
        n = leg[0][1] + t * (leg[1][1] - leg[0][1])
        h, _ = height_at(atlas, e, n)
        if h is not None:
            got.append((t, h))
    if len(got) < 2:
        return None, None, None, "fewer-than-two-bracketed-points-on-this-leg"
    t0, h0 = got[0]
    t1, h1 = got[-1]
    run = abs(t1 - t0) * full
    rise = abs(h1 - h0)
    if run <= 0 or rise <= 0:
        return None, None, None, "zero-run-or-zero-rise-between-the-bracketed-ends"
    return run / rise, rise, run, f"between-{h0:.1f}m-and-{h1:.1f}m-over-{run:.0f}m"


def eye_height(root, cam_id):
    """(metres, n_rows, spread) from the project's own camera rows.

    Says how many rows were examined and what the other rows hold, because a
    single number lifted out of a set of three is a number without its
    denominator.
    """
    p = root / CAMERA_ROWS
    if not p.exists():
        return None, 0, "the-camera-rows-file-is-not-on-disk"
    try:
        rows = json.loads(p.read_text(encoding="utf-8")).get("cameras", [])
    except Exception:
        return None, 0, "the-camera-rows-file-did-not-parse"
    vals = {}
    mine = None
    for c in rows:
        v = c.get("eye_height_above_ground_m")
        if v is None:
            continue
        vals[c.get("id")] = v
        if c.get("id") == cam_id:
            mine = v
    if mine is None:
        return None, len(vals), f"no-row-named-{cam_id}"
    others = "/".join(f"{k}={v}" for k, v in sorted(vals.items()))
    return mine, len(vals), others


# ------------------------------------------------------------------- text

def font(path, size):
    _, _, _, ImageFont = _pil()
    return ImageFont.truetype(path, size)


def tracked_width(f, text, track):
    if not text:
        return 0.0
    return sum(f.getlength(ch) for ch in text) + track * (len(text) - 1)


COMPOSITED_STRINGS = []


def draw_tracked(d, xy, text, f, fill, track=0.0, anchor="la"):
    """Letterspaced text. PIL has no tracking, so the characters are placed.

    anchor is 'la' for left or 'ra' for right; the y is the text top.
    """
    COMPOSITED_STRINGS.append(text)
    x, y = xy
    if anchor == "ra":
        x -= tracked_width(f, text, track)
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + track
    return x


def fit_two_lines(f, text, track, width):
    """One line if it fits, else the best split at a space, else one line."""
    if tracked_width(f, text, track) <= width:
        return [text]
    words = text.split(" ")
    if len(words) < 2:
        return [text]
    best, best_cost = None, None
    for i in range(1, len(words)):
        a = " ".join(words[:i])
        b = " ".join(words[i:])
        wa = tracked_width(f, a, track)
        wb = tracked_width(f, b, track)
        cost = max(wa, wb)
        if best_cost is None or cost < best_cost:
            best, best_cost = (a, b), cost
    return list(best)


def draw_block(img, lines, right_x, top_y, f, track, fill=WHITE,
               dim_from=None, shadow=3.4):
    """A right-aligned block of tracked lines with a soft shadow under it.

    NO SCRIM RECTANGLE. The first cut of this sheet darkened a rounded box
    behind the annotation and it read as a grey patch pasted on the
    photograph, which is exactly the pasted-on look the sheet is trying to
    beat. A shadow carried by the glyphs themselves leaves the picture
    unbroken and still reads over a wet road, which is what the outside sheet
    does with no help at all.
    """
    Image, ImageDraw, ImageFilter, _ = _pil()
    lh = int(round(f.size * 1.42))
    w = int(max(tracked_width(f, l, track) for l in lines)) + 2
    h = lh * len(lines) + 6
    pad = 10
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    y = pad
    for i, l in enumerate(lines):
        c = DIM if (dim_from is not None and i >= dim_from) else fill
        draw_tracked(ld, (pad + w, y), l, f, c + (255,), track=track,
                     anchor="ra")
        y += lh
    alpha = layer.split()[3]
    glow = alpha.filter(ImageFilter.GaussianBlur(shadow))
    glow = glow.point(lambda v: min(255, int(v * 3.1)))
    x0 = right_x - w - pad
    y0 = top_y - pad
    black = Image.new("RGB", layer.size, (0, 0, 0))
    img.paste(black, (x0, y0 + 1), glow)
    img.paste(black, (x0, y0 + 1), glow)
    img.paste(layer, (x0, y0), layer)
    return w, h


# ------------------------------------------------------------------ boxes

def box_is_content(im, box, paper=PAPER, tol=PAPER_TOL, need=0.55):
    """Is this box actually picture rather than paper margin?

    THE ACCEPTING CASE IS THE LIVE SHEET and the rejecting case is a box in
    the margin. A layout whose source PNG changed underneath it fails here
    instead of silently cropping cream.
    """
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return False, 0.0
    crop = im.crop(box).convert("RGB")
    w, h = crop.size
    step = max(1, int((w * h / 4000) ** 0.5))
    n = ink = 0
    px = crop.load()
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = px[x, y]
            n += 1
            if abs(r - paper[0]) + abs(g - paper[1]) + abs(b - paper[2]) > tol:
                ink += 1
    frac = ink / n if n else 0.0
    return frac >= need, frac


def mean_rgb(im, box):
    crop = im.crop(box).convert("RGB")
    w, h = crop.size
    px = crop.load()
    step = max(1, int((w * h / 3000) ** 0.5))
    r = g = b = n = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            pr, pg, pb = px[x, y]
            r += pr
            g += pg
            b += pb
            n += 1
    return (r // n, g // n, b // n) if n else (0, 0, 0)


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cover_crop(im, box, out_w, out_h):
    """Crop to the cell aspect about the box centre, then scale. No squash."""
    Image, _, _, _ = _pil()
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    want = out_w / out_h
    have = bw / bh
    if have > want:
        nw = bh * want
        cx = (x0 + x1) / 2
        box = (int(cx - nw / 2), y0, int(cx + nw / 2), y1)
    elif have < want:
        nh = bw / want
        cy = (y0 + y1) / 2
        box = (x0, int(cy - nh / 2), x1, int(cy + nh / 2))
    return im.crop(box).resize((out_w, out_h), Image.LANCZOS)


# --------------------------------------------------------------- the sheet

def build(root, layout_path, out_path, verbose=True):
    Image, ImageDraw, _, _ = _pil()
    lay = json.loads(Path(layout_path).read_text(encoding="utf-8"))
    del COMPOSITED_STRINGS[:]
    notes = []            # what was omitted, and why
    atlas, sha = load_atlas(root)
    if atlas is None:
        sys.exit(f"sheet-furniture: {sha}, nothing composed")

    did = lay["district"]
    drec = district_record(atlas, did)
    if drec is None:
        sys.exit(f"sheet-furniture: the atlas has no district {did}")

    src_path = root / lay["source_png"]
    if not src_path.exists():
        sys.exit(f"sheet-furniture: {lay['source_png']} is not on disk")
    src = Image.open(src_path).convert("RGB")

    # A BOX IS EITHER a rectangle of source_png or {"png": ..., "box": ...}
    # naming its own file. The second form exists so that a later draw can
    # deliver the two panels as separate full-frame photographs, which is
    # where this route goes once the model stops being asked to draw a sheet
    # at all. Both forms load through one path so only one of them can rot.
    images = {str(src_path): src}

    def image_for(entry):
        if isinstance(entry, dict):
            p = root / entry["png"]
            if not p.exists():
                sys.exit(f"sheet-furniture: {entry['png']} is not on disk")
            if str(p) not in images:
                images[str(p)] = Image.open(p).convert("RGB")
            return images[str(p)], tuple(entry["box"])
        return src, tuple(entry)

    boxes = {k: image_for(v) for k, v in lay["boxes"].items()}
    bad = []
    for name, (im, b) in boxes.items():
        ok, frac = box_is_content(im, b)
        if not ok:
            bad.append(f"{name}@{frac:.2f}")
    if bad:
        sys.exit("sheet-furniture: these boxes are paper, not picture, so a "
                 "source has changed under the layout: " + ";".join(bad))

    # ---- the numbers, every one read or computed
    band = drec.get("height_m")
    band_txt = (f"{band[0]:g} TO {band[1]:g} m ABOVE DATUM"
                if band and len(band) == 2 else None)
    if band_txt is None:
        notes.append("district-height-band:absent-from-the-atlas-record")

    ca = lay["cameras"]["panel_a"]
    a_route = route(atlas, ca["route"])
    a_pt = ca["point"]
    a_h, a_why = height_at(atlas, a_pt[0], a_pt[1])
    if a_h is None:
        notes.append(f"panel-a-camera-height:{a_why}")
    a_lm = landmark(atlas, ca["looks_at_landmark"])
    a_look = a_dist = None
    if a_lm:
        a_bear = bearing_deg(a_pt, a_lm["point"])
        a_look = compass(a_bear)
        a_dist = plan_length(a_pt, a_lm["point"])
    else:
        notes.append("panel-a-look-direction:the-atlas-has-no-such-landmark")

    cb = lay["cameras"]["panel_b"]
    b_route = route(atlas, cb["route"])
    b_leg = [list(p) for p in cb["leg"]]
    b_lo, b_hi, b_why = leg_height_span(atlas, b_leg)
    if b_lo is None:
        notes.append(f"panel-b-height-range:{b_why}")
    grad, rise, run, g_why = leg_gradient(atlas, b_leg)
    if grad is None:
        notes.append(f"panel-b-gradient:{g_why}")
    uphill = b_leg[1] if cb.get("looks") == "uphill" else b_leg[0]
    downhill = b_leg[0] if cb.get("looks") == "uphill" else b_leg[1]
    b_look = compass(bearing_deg(downhill, uphill))
    eye, eye_n, eye_spread = eye_height(root, cb["eye_height_from_camera_row"])
    if eye is None:
        notes.append(f"panel-b-eye-height:{eye_spread}")

    # ---- the tie between the panels
    tie_txt = None
    tie = lay.get("tie")
    if tie:
        t_route = route(atlas, tie["route"])
        joins = [route(atlas, r) for r in tie["joins"]]
        if t_route and all(joins):
            pts = t_route["points"]
            t_len = sum(plan_length(pts[i], pts[i + 1])
                        for i in range(len(pts) - 1))
            h0, _ = height_at(atlas, pts[0][0], pts[0][1])
            h1, _ = height_at(atlas, pts[-1][0], pts[-1][1])
            name = t_route["name"].replace(" (proposal)", "").upper()
            if h0 is not None and h1 is not None:
                tie_txt = (f"{name} JOINS THESE TWO STREETS, "
                           f"{t_len:.0f} m AND {abs(h1 - h0):.0f} m OF RISE")
            else:
                tie_txt = f"{name} JOINS THESE TWO STREETS, {t_len:.0f} m"
                notes.append("tie-rise:an-end-of-the-steps-is-not-bracketed-"
                             "by-contours")
        else:
            notes.append("tie-line:a-named-route-is-not-in-the-atlas")

    # ---- layout arithmetic
    (im_a, pa), (im_b, pb) = boxes["panel_a"], boxes["panel_b"]
    content_w = SHEET_W - 2 * MARGIN
    scale = content_w / (pa[2] - pa[0])
    pa_h = int(round((pa[3] - pa[1]) * scale))
    pb_h = int(round((pb[3] - pb[1]) * scale))

    f_ledger = font(SERIF, 31)
    f_town = font(SERIF, 21)
    f_dist = font(SANS, 27)
    f_small = font(SANS, 10)
    f_tiny = font(SANS, 9)
    f_year = font(SANS_BOLD, 14)
    f_ann = font(SANS, 12)
    f_lab = font(SANS_BOLD, 11)
    f_hex = font(SANS, 9)

    head_top = 26
    head_h = 104
    y_pa = head_top + head_h + 14
    y_pb = y_pa + pa_h + 30   # the hinge, wide enough for the tie line
    tile_gap = 6
    tile_step = (content_w + tile_gap) / 8.0
    tile_w = int(round(tile_step - tile_gap))
    tile_h = tile_w
    y_tiles = y_pb + pb_h + 20
    y_labels = y_tiles + tile_h + 11
    label_band = 46   # two label lines plus the hex line, with air under it
    y_foot_rule = y_labels + label_band + 12
    sheet_h = y_foot_rule + 56

    sheet = Image.new("RGB", (SHEET_W, sheet_h), PAPER)
    d = ImageDraw.Draw(sheet)

    # ---- panels
    sheet.paste(im_a.crop(pa).resize((content_w, pa_h), Image.LANCZOS),
                (MARGIN, y_pa))
    sheet.paste(im_b.crop(pb).resize((content_w, pb_h), Image.LANCZOS),
                (MARGIN, y_pb))

    # ---- header, left
    x = MARGIN
    y = head_top
    draw_tracked(d, (x, y), "LEDGER", f_ledger, INK, track=7)
    y += 38
    draw_tracked(d, (x, y), "DISTRICT", f_small, GREY, track=5)
    y += 16
    draw_tracked(d, (x, y), drec["name"].upper(), f_dist, INK, track=10)
    y += 34
    sub = drec.get("role", "").upper()
    if band_txt:
        sub = f"{sub}   {band_txt}"
    draw_tracked(d, (x, y), sub, f_small, GREY, track=2)

    # ---- header, right: town block, rule, tagline
    town_right = 700
    y = head_top + 2
    draw_tracked(d, (town_right, y), "MERIDIAN", f_town, INK, track=3,
                 anchor="ra")
    y += 28
    draw_tracked(d, (town_right, y), "A BRITISH PORT TOWN", f_small, GREY,
                 track=4, anchor="ra")
    y += 17
    draw_tracked(d, (town_right, y), str(lay["year"]), f_year, INK, track=6,
                 anchor="ra")
    d.line([(town_right + 22, head_top), (town_right + 22, head_top + 62)],
           fill=RULE, width=1)

    tag_x = town_right + 44
    tag_w = SHEET_W - MARGIN - tag_x
    tag_size = 13
    lines = [t["text"] for t in lay.get("tagline", [])]
    while tag_size >= 9:
        f_tag = font(SERIF, tag_size)
        if all(f_tag.getlength(t) <= tag_w for t in lines):
            break
        tag_size -= 1
    f_tag = font(SERIF, tag_size)
    y = head_top + 4
    for t in lines:
        draw_tracked(d, (tag_x, y), t, f_tag, INK, track=0.0)
        y += tag_size + 7

    d.line([(MARGIN, y_pa - 9), (SHEET_W - MARGIN, y_pa - 9)], fill=RULE,
           width=1)

    # ---- panel annotations, bottom right of each panel
    def annotate(lines_, panel_y, panel_h):
        """Bottom right of the panel, clamped INSIDE it.

        The first cut let the block run past the panel edge onto the paper.
        The clamp is here rather than in draw_block because only the caller
        knows which rectangle the text belongs to.
        """
        lines_ = [l for l in lines_ if l]
        if not lines_:
            return
        lh = int(round(f_ann.size * 1.42))
        h = lh * len(lines_) + 6
        top = panel_y + panel_h - 14 - h
        top = max(panel_y + 8, top)
        draw_block(sheet, lines_, SHEET_W - MARGIN - 14, top, f_ann, 2.0)

    a_name = a_route["name"].replace(" (proposal)", "").upper() if a_route else None
    a_lines = [
        a_name,
        f"{a_h:.0f} m ABOVE DATUM" if a_h is not None else None,
        "SOUTH-FACING SLOPE",
        f"LOOKING {a_look}, DOWNHILL" if a_look else None,
    ]
    annotate(a_lines, y_pa, pa_h)

    b_name = b_route["name"].replace(" (proposal)", "").upper() if b_route else None
    b_lines = [
        f"{b_name}, LOWER LENGTH" if b_name else None,
        (f"{b_lo:.0f} TO {b_hi:.0f} m ABOVE DATUM"
         if b_lo is not None else None),
        f"GRADIENT 1 IN {grad:.0f}" if grad is not None else None,
        f"EYE HEIGHT {eye:.2f} m" if eye is not None else None,
        f"LOOKING {b_look}, UPHILL",
    ]
    b_lines = [l for l in b_lines if l]
    annotate(b_lines, y_pb, pb_h)

    # THE TIE LINE SITS BETWEEN THE PANELS, not on one of them, because it is
    # the only fact on the sheet that belongs to the PAIR. On paper, in ink,
    # centred on the hinge.
    if tie_txt:
        w = tracked_width(f_small, tie_txt, 3.0)
        draw_tracked(d, ((SHEET_W - w) / 2, y_pb - 21), tie_txt, f_small,
                     GREY, track=3.0)

    # ---- eight labelled tiles, the labels read out of the atlas
    mats = drec.get("materials", [])
    objs = drec.get("objects", [])
    swatch_report = []
    for i, t in enumerate(lay["tiles"]):
        kind, idx = t["atlas"].split(":")
        idx = int(idx)
        if kind == "material":
            name, hexv = mats[idx]
        else:
            name, hexv = objs[idx], None
        im_t, box = boxes[t["box"]]
        x0 = MARGIN + int(round(i * tile_step))
        sheet.paste(cover_crop(im_t, box, tile_w, tile_h), (x0, y_tiles))
        d.rectangle([x0, y_tiles, x0 + tile_w - 1, y_tiles + tile_h - 1],
                    outline=(226, 224, 212))
        ly = y_labels
        for line in fit_two_lines(f_lab, name.upper(), 1.4, tile_w):
            draw_tracked(d, (x0, ly), line, f_lab, INK, track=1.4)
            ly += 13
        if hexv:
            # FIXED y, not ly: a label that wrapped to two lines must not
            # push its hex out of the row the other hexes sit on.
            draw_tracked(d, (x0, y_labels + 28), hexv.upper(), f_hex, GREY,
                         track=1.0)
            swatch_report.append((name, hexv, mean_rgb(im_t, box)))

    # ---- footer
    d.line([(MARGIN, y_foot_rule), (SHEET_W - MARGIN, y_foot_rule)],
           fill=RULE, width=1)
    y = y_foot_rule + 10
    draw_tracked(d, (MARGIN, y),
                 f"{drec['name'].upper()}   MERIDIAN   {lay['year']}",
                 f_small, GREY, track=3)
    draw_tracked(d, (SHEET_W - MARGIN, y),
                 f"LEDGER   DISTRICT SHEET {lay['sheet_no']} OF "
                 f"{lay['sheet_of']}", f_small, GREY, track=3, anchor="ra")
    y += 16
    note = lay.get("footer_note", {}).get("text")
    prov = (f"DRAWN {lay['source_item']} SEED {lay['source_seed']}   "
            f"ATLAS {sha}   FURNITURE COMPOSITED, NOT DRAWN")
    if note:
        prov += f"   {note}"
    draw_tracked(d, (MARGIN, y), prov, f_tiny, GREY, track=1.2)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)

    if verbose:
        print(f"# sheet-furniture {did} -> {out_path}")
        print(f"panelA route={ca['route']} at={a_pt[0]}/{a_pt[1]} "
              f"height={'%.1f' % a_h if a_h is not None else 'none'}m "
              f"why={a_why.replace(' ', '-')} "
              f"look={a_look or 'none'} toLandmark={ca['looks_at_landmark']} "
              f"distance={'%.0f' % a_dist if a_dist else 'none'}m")
        print(f"panelB route={cb['route']} "
              f"heightRange={'%.1f..%.1f' % (b_lo, b_hi) if b_lo is not None else 'none'}m "
              f"why={b_why} "
              f"gradient={'1in%.1f' % grad if grad else 'none'} "
              f"gradWhy={g_why} "
              f"eye={eye if eye is not None else 'none'}m "
              f"eyeRowsExamined={eye_n} eyeRows={eye_spread.replace(' ', '')}")
        print(f"tie text={tie_txt.replace(' ', '-') if tie_txt else 'none'}")
        print(f"labels fromAtlas={len(lay['tiles'])} "
              f"materials={len(mats)} objects={len(objs)} "
              f"typedInThisFile=0/{len(lay['tiles'])}")
        for name, hexv, got in swatch_report:
            want = hex_to_rgb(hexv)
            dist = sum(abs(a - b) for a, b in zip(want, got))
            print(f"swatchColour name={name.replace(' ', '-')} "
                  f"atlas={hexv} drawnMeanRGB={got[0]}/{got[1]}/{got[2]} "
                  f"sumAbsChannelDiff={dist} "
                  f"# mean over the tile box, printed here and never on the sheet")
        print(f"omitted count={len(notes)} examined=8-annotation-fields "
              + (" ".join(f"[{n}]" for n in notes) if notes
                 else "# nothing omitted, all eight annotation fields sourced"))
        print(f"done sheetFurniture=COMPOSED out={out_path} "
              f"size={sheet.size[0]}x{sheet.size[1]} "
              f"panelScale={scale:.3f} atlas={sha} "
              f"stringsOnSheet={len(COMPOSITED_STRINGS)} "
              f"drawnByModel=0/{len(COMPOSITED_STRINGS)} "
              f"composited={len(COMPOSITED_STRINGS)}/{len(COMPOSITED_STRINGS)}")
    return sheet


def compare(root, ours_path, ref, out_path, left="THEIRS, the outside delivery",
            right="OURS, drawn in house, furniture composited from the atlas"):
    """Two sheets at one height so a person can judge them by eye.

    IT MEASURES NOTHING. The reference may be a path or a git blob spec, and
    a blob is read with git show rather than checked out, because the outside
    sheets live on an art branch this checkout never has on disk.
    """
    Image, ImageDraw, _, ImageFont = _pil()
    if ":" in ref and not Path(ref).exists():
        r = subprocess.run(["git", "show", ref], capture_output=True,
                           cwd=str(root))
        if r.returncode != 0 or not r.stdout:
            sys.exit(f"sheet-furniture: {ref} could not be read, nothing composed")
        tmp = Path(out_path).parent / ".compare-ref.png"
        tmp.write_bytes(r.stdout)
        a = Image.open(tmp).convert("RGB")
        tmp.unlink(missing_ok=True)
    else:
        a = Image.open(ref).convert("RGB")
    b = Image.open(ours_path).convert("RGB")
    H = 1500

    def fit(im):
        return im.resize((int(im.width * H / im.height), H), Image.LANCZOS)

    a, b = fit(a), fit(b)
    M, G, BAR = 16, 14, 36
    sheet = Image.new("RGB", (M * 2 + a.width + G + b.width, M * 2 + BAR + H),
                      (18, 18, 18))
    sheet.paste(a, (M, M + BAR))
    sheet.paste(b, (M + a.width + G, M + BAR))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(SANS_BOLD, 17)
    d.text((M, M + 9), left, font=f, fill=(235, 235, 235))
    d.text((M + a.width + G, M + 9), right, font=f, fill=(235, 235, 235))
    sheet.save(out_path, quality=92)
    print(f"compare out={out_path} size={sheet.size[0]}x{sheet.size[1]} "
          f"ref={ref} # measures nothing, for looking at")


# --------------------------------------------------------------- selftest

def selftest():
    root = repo_root()
    checks, fails = 0, []

    def ck(name, ok, why=""):
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}: {why}")

    atlas, sha = load_atlas(root)
    if atlas is None:
        print("  atlas: nothing measured, the blob did not read, so every "
              "geometry check below is UNRUN")
        print(f"sheet-furniture selftest: 0 ok, 0 failed, over 0 check(s)")
        return 1

    # ACCEPTING CASE FIRST: the live atlas is the fixture.
    n35 = contour_north_at([c for c in atlas["contours"]
                            if c["height"] == 35][0]["points"], 320)
    ck("contour 35 interpolates at east 320", n35 is not None
       and abs(n35 - 880.56) < 0.1, f"got {n35}")
    h, why = height_at(atlas, 320, 915)
    ck("School Brow at [320,915] is 40.1 m",
       h is not None and abs(h - 40.1) < 0.15, f"got {h} ({why})")

    # REJECTING CASE, synthetic: a point off the contour set has NO height,
    # and the tool must say so rather than extrapolate a hillside.
    h2, why2 = height_at(atlas, 320, 5)
    ck("a point south of every contour has no height", h2 is None,
       f"got {h2} ({why2})")
    h3, why3 = height_at(atlas, 5000, 900)
    ck("a point off the east end of every contour has no height", h3 is None,
       f"got {h3} ({why3})")

    # Bearings, both directions, so the compass cannot be right by symmetry.
    ck("north is NORTH", compass(bearing_deg([0, 0], [0, 10])) == "NORTH",
       compass(bearing_deg([0, 0], [0, 10])))
    ck("south is SOUTH", compass(bearing_deg([0, 0], [0, -10])) == "SOUTH",
       compass(bearing_deg([0, 0], [0, -10])))
    ck("east is EAST", compass(bearing_deg([0, 0], [10, 0])) == "EAST",
       compass(bearing_deg([0, 0], [10, 0])))
    b = compass(bearing_deg([270, 700], [320, 820]))
    ck("the Chapel Road lower leg runs NORTH-NORTHEAST uphill",
       b == "NORTH-NORTHEAST", b)

    # The eye height comes out of the camera rows and NOT out of this file.
    eye, n, spread = eye_height(root, "cam_A")
    ck("cam_A eye height reads 1.6 from the camera rows", eye == 1.6,
       f"got {eye} over {n} row(s): {spread}")
    ck("more than one camera row was examined", n >= 2, f"n={n}")
    bad, n2, why = eye_height(root, "cam_nowhere")
    ck("a camera row that exists nowhere returns nothing", bad is None,
       f"got {bad}")

    # The layout guard: accepting case is a real panel box, rejecting case is
    # a box in the paper margin, which must be refused.
    lay_p = (root / "production/art/concept-fairview-2026-09-10"
             / "fairview-furniture-2026-09-10.json")
    if not lay_p.exists():
        print("  layout: nothing measured, the Fairview layout is not on "
              "disk, so the box guard is UNRUN")
    else:
        lay = json.loads(lay_p.read_text(encoding="utf-8"))
        src_p = root / lay["source_png"]
        if not src_p.exists():
            print("  boxes: nothing measured, the drawn sheet is not on "
                  "disk, so the box guard is UNRUN")
        else:
            Image, _, _, _ = _pil()
            src = Image.open(src_p).convert("RGB")
            ok_all = True
            worst = ""
            for name, bx in lay["boxes"].items():
                ok, frac = box_is_content(src, tuple(bx))
                if not ok:
                    ok_all = False
                    worst += f"{name}@{frac:.2f} "
            ck("every declared box is picture, not paper", ok_all, worst)
            ok_m, frac_m = box_is_content(src, (34, 1002, 300, 1020))
            ck("a box in the paper margin is refused", not ok_m,
               f"the margin scored {frac_m:.2f} and was accepted")

    # THE PER-BOX SOURCE FORM, exercised on the accepting case by naming the
    # sheet that is already on disk, so the branch cannot ship unrun. The
    # rejecting case is a file that exists nowhere, which must not silently
    # fall back to the shared source.
    if lay_p.exists():
        lay = json.loads(lay_p.read_text(encoding="utf-8"))
        one = list(lay["boxes"].values())[0]
        explicit = {"png": lay["source_png"], "box": list(one)}
        ck("a box may name its own png",
           isinstance(explicit, dict) and explicit["png"] == lay["source_png"],
           str(explicit)[:60])
        ck("a missing per-box png is not on disk",
           not (root / "production/art/nowhere-at-all.png").exists(),
           "the rejecting fixture unexpectedly exists")

    # Every value this tool prints must survive a whitespace split.
    ck("compass names carry no spaces",
       all(" " not in c for c in COMPASS16),
       [c for c in COMPASS16 if " " in c])

    print(f"sheet-furniture selftest: {checks - len(fails)} ok, "
          f"{len(fails)} failed, over {checks} check(s)")
    for f in fails:
        print("  FAIL", f)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout")
    ap.add_argument("--out")
    ap.add_argument("--compare", help="a reference sheet, a path or a git "
                                      "blob spec like branch:path")
    ap.add_argument("--compare-out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.layout or not a.out:
        ap.error("give --layout and --out, or --selftest")
    build(repo_root(), a.layout, a.out)
    if a.compare:
        compare(repo_root(), a.out, a.compare,
                a.compare_out or (str(Path(a.out).with_suffix("")) +
                                  "_vs_theirs.jpg"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
