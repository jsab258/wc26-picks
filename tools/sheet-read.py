#!/usr/bin/env python3
"""Measure the clip contact sheet, so judging the animations is not eyeballing.

WHY. Jafar's question is "does it look real, or are we using wrong animations",
and the contact sheet is the artefact that answers it. But rule 4 is explicit
that LOOKING IS NOT MEASURING: four correct things were condemned off a 1280x720
JPEG in one night, and each was settled by a number in under a minute. A sheet
of 201 tiles is worse, not better — at that size everything is a thumbnail.

So this reads the sheet the renderer produced and prints, per clip:

  * `dark`    — the tile is a black silhouette. A REAL fault, and not about
                the clip: the lighting pass writes RenderSettings.ambientLight
                from the in-game CLOCK every frame, each tile costs a frame,
                and 201 frames is two dawns. Plotted against RENDER ORDER the
                luma traces two clean day/night cycles. 25 of 67 on the 18 Aug
                sheet; the fix (re-assert per tile) has not landed.
  * `small`   — the body covers far less of the tile than its neighbours, so
                the tile cannot be judged whatever the reason. Says nothing
                about WHY: root motion was published as the cause and
                withdrawn — clip-motion's travel column reads `Walking` 0.00
                and `Standing React` 3.1 m/s, so it cannot support that claim.
  * `prone`   — the body lies entirely below the floor line. Not a fault; it
                is why the area and the luma are measured over different
                regions, since cutting the floor off reported a lying body as
                no body.
  * `empty`   — no body at all. Always a fault.

WHAT IT DOES NOT DO. It cannot say whether a walk looks like a walk. That is a
person's judgement and it needs a legible tile to make it, which is exactly
what the first two findings are about: you cannot judge a silhouette.

The tile grid is not guessed. `clips.tsv` ships beside the JPEG and names the
row and column of every slot, so a clip that moves in the sheet cannot be
reported under its neighbour's name.
"""

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "game-design" / "sim-shots"

# These mirror ClipSheet.cs. Read from the image where possible rather than
# trusted blind — a constant that drifts from the renderer is rule 1's comment
# decay wearing a number's clothes, so the tile size is DERIVED and these are
# only the fallback when the sheet is empty.
PHASES_PER_CLIP = 3

# Measured off the sheet's own background rather than assumed. The renderer's
# ambient is 0.55 grey and the floor plane is lighter, so a fixed threshold
# would call the floor a body. The background is whatever colour the modal
# pixel is, and a body pixel is one far enough from it.
BG_TOLERANCE = 26           # 8-bit levels; below this is "same as background"
SMALL_FRACTION = 0.45       # of the median body area across the sheet

# How much darker than the floor plane a pixel must be to count as a body
# lying on it. Wide enough to survive the plane's own shading gradient and the
# body's shadow, narrow enough that a dark suit on a lit floor still counts —
# the two are about 150 levels apart on the 18 Aug sheet (floor ~176, a
# silhouette ~6), so this is nowhere near either edge.
FLOOR_MARGIN = 40

# DARK_LUMA IS SET FROM THE SERIES, NOT INVENTED — and the first version of
# this file invented it (42) and consequently reported "legible 67 of 67" for
# a sheet whose silhouettes are visible from across the room. Two faults, and
# the threshold was the smaller one:
#
#   1. the FLOOR. Every tile has a lit floor plane across its bottom quarter,
#      it differs from the background, so it counted as body — and being the
#      brightest thing in the tile it dragged a silhouette's mean luma from
#      about 6 up to 46, above any sane bound. The floor is excluded now, and
#      by MEASUREMENT rather than by a fraction: the median row luma across all
#      201 tiles is flat down the body and steps up hard where the plane
#      starts (90.0 at y=164, 118.0 at y=166 on the 18 Aug sheet), because the
#      floor is identical in every tile and a body is not.
#   2. only then does a threshold mean anything. With the floor gone the
#      series separates: lit clips sit around 120-170, silhouettes around 12.
DARK_LUMA = 27              # measured; see below and clip-findings.txt
#
# 27 is where READABLE starts, established by printing the whole series and
# then looking at the tiles either side of the boundary at 3x:
#     idle_2   19  — silhouette, only the hair catches light
#     walk_old 25  — still a silhouette; hands and shoes barely there
#     sit_talk 28  — face, shirt, tie and shoes all legible
#     sit      39  — plainly fine
# Two earlier values (42, then 60) were invented rather than measured and each
# was wrong in a different direction: 42 passed all 67 clips on a sheet whose
# silhouettes are visible across a room, 60 failed 54 including ones I had
# just confirmed by eye were fine. Rule 2, twice, on the same afternoon.


def load(sheet, tsv):
    from PIL import Image
    img = Image.open(sheet).convert("RGB")
    rows = []
    for line in tsv.read_text(encoding="utf-8").strip().split("\n")[1:]:
        r, c, slot = line.split("\t")
        rows.append((int(r), int(c), slot))
    if not rows:
        raise SystemExit("sheet-read: clips.tsv named no slots")
    cols = max(c for _, c, _ in rows) + 1
    nrows = max(r for r, _, _ in rows) + 1
    tile_w = img.width // (cols * PHASES_PER_CLIP)
    tile_h = img.height // nrows
    return img, rows, tile_w, tile_h


def pixels(img):
    """Every pixel as (r, g, b), via tobytes.

    getdata() is deprecated in Pillow 12 and its replacement does not exist in
    the versions on the other machines this repo runs on, so neither is safe to
    depend on. tobytes has been stable for a decade and is an order of
    magnitude faster over a 5-megapixel sheet.
    """
    raw = img.tobytes()
    return [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]


def floor_line(img, rows, tw, th):
    """The y within a tile where the floor plane starts, by measurement.

    Returns th (i.e. "no floor found") rather than guessing, so a sheet
    rendered without the plane measures the whole tile instead of silently
    discarding its bottom quarter.
    """
    import statistics
    raw, W = img.tobytes(), img.width
    prof = []
    for y in range(th):
        vals = []
        for r, c, _ in rows:
            for p in range(PHASES_PER_CLIP):
                x0, base = (c * PHASES_PER_CLIP + p) * tw, ((r * th + y) * W + (c * PHASES_PER_CLIP + p) * tw) * 3
                cols = range(0, tw, 4)
                vals.append(sum(raw[base + i * 3] for i in cols) / len(cols))
        prof.append(statistics.median(vals))
    # The step is in the lower half by construction — the body stands ON the
    # plane — and it must be a real step, not the shading gradient down a leg.
    best, best_y = 0.0, th
    for y in range(th // 2, th - 4):
        rise = statistics.median(prof[y + 1:y + 5]) - statistics.median(prof[max(0, y - 4):y + 1])
        if rise > best:
            best, best_y = rise, y
    return best_y if best > 12 else th


def background(img):
    """The sheet's own background colour, as the commonest pixel."""
    counts = {}
    for px in pixels(img.resize((img.width // 8, img.height // 8))):
        counts[px] = counts.get(px, 0) + 1
    return max(counts.items(), key=lambda kv: kv[1])[0]


def measure_tile(img, x, y, w, h, bg, floor_rgb=None):
    """Body pixel count and their mean luma over one region of a phase tile.

    TWO REGIONS, BECAUSE THERE ARE TWO QUESTIONS, and collapsing them to one
    got the answer wrong in both directions inside an hour:

      * "IS THERE A BODY" is asked of the WHOLE tile. Cut at the floor line it
        reported `get_up` as EMPTY — Stand Up begins PRONE, so every pixel of
        it sat in the band that was being discarded, and the tool published an
        absence that was its own blind spot. (`clip-motion.py` kills the
        alternative: Stand Up travels 0.01m along a 0.20m path, Jog Forward
        0.00m along 0.03m. Neither leaves frame. I had read those rows a column
        out — travel is the FOURTH column — and published root motion as the
        cause.)
      * "CAN I READ IT" is asked ABOVE the floor line. The floor is lit and
        differs from the background, so it counts as body and drags a
        silhouette's mean from about 6 up to 46 — which is how the first
        version passed 67 of 67 on a sheet full of silhouettes. Excluding the
        floor by COLOUR instead does not work either: it is a gradient with the
        body's own shadow across it, so only its modal shade goes and the mean
        comes straight back to 47.

    `floor_rgb`, when given, also drops floor-coloured pixels — used only for
    the prone fallback, where the region has to include the floor band.
    """
    body, luma = 0, 0
    for r, g, b in pixels(img.crop((x, y, x + w, y + h))):
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) <= BG_TOLERANCE:
            continue
        if floor_rgb is not None and (abs(r - floor_rgb[0]) + abs(g - floor_rgb[1])
                                      + abs(b - floor_rgb[2])) <= BG_TOLERANCE:
            continue
        body += 1
        luma += (r * 299 + g * 587 + b * 114) // 1000
    return body, (luma / body if body else 0.0)


def measure_area(img, x, y, w, th, floor, bg, floor_luma):
    """Body pixels over the WHOLE tile, floor and background both discounted.

    THE FLOOR IS DISCOUNTED BY GEOMETRY PLUS BRIGHTNESS, not by matching its
    colour. Matching its colour does not work — it is a lit plane with the
    body's own shadow across it, so only its modal shade goes — and cutting it
    off by height does not work either, because a body lying on it is then
    reported as no body at all. Both were tried, in that order, and each
    produced a confident wrong answer.

    So: above the floor line a pixel is body when it differs from the
    background; below it, when it is meaningfully DARKER than the floor. That
    holds however the plane is shaded, because a body on a lit floor is the
    dark thing on it — which is the same fact the eye uses.

    Counting the floor as body is not cosmetic. It is about a quarter of every
    tile, roughly 6,000 pixels against a body's 4,600, so it swamps the
    difference between a body in frame and one barely in it and makes the
    `small` finding meaningless.
    """
    body = 0
    for i, (r, g, b) in enumerate(pixels(img.crop((x, y, x + w, y + th)))):
        if (i // w) < floor:
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > BG_TOLERANCE:
                body += 1
        elif ((r * 299 + g * 587 + b * 114) // 1000 < floor_luma - FLOOR_MARGIN
              and abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > BG_TOLERANCE):
            # DARKER THAN THE FLOOR **AND** NOT THE BACKGROUND. The floor line
            # is one row of blend between plane and background, and background
            # is darker than the plane, so without the second test that row
            # counts as a body in every tile — 110 pixels, enough to stop a
            # genuinely empty tile from ever reading as empty.
            body += 1
    return body


def read(sheet=None, tsv=None, verbose=True):
    sheet = pathlib.Path(sheet or SHOTS / "clips.jpg")
    tsv = pathlib.Path(tsv or SHOTS / "clips.tsv")
    if not sheet.exists() or not tsv.exists():
        # A missing sheet is not a clean sheet (rule 3b).
        print(f"sheet-read: NO SHEET at {sheet.name} — nothing was measured.")
        return None

    img, rows, tw, th, = load(sheet, tsv)
    bg = background(img)
    floor = floor_line(img, rows, tw, th)
    # The floor's own colour, taken from inside the band it occupies. Sampled
    # rather than assumed, for the same reason the background is.
    floor_rgb = bg if floor >= th else background(
        img.crop((0, floor + 4, img.width, min(img.height, floor + 4 + max(2, th // 20)))))
    floor_luma = (floor_rgb[0] * 299 + floor_rgb[1] * 587 + floor_rgb[2] * 114) // 1000

    per_clip = []
    prone = []
    for r, c, slot in rows:
        areas, lumas = [], []
        low = False
        for p in range(PHASES_PER_CLIP):
            x = (c * PHASES_PER_CLIP + p) * tw
            whole = measure_area(img, x, r * th, tw, th, floor, bg, floor_luma)
            above, luma = measure_tile(img, x, r * th, tw, floor, bg)
            # A body entirely below the floor line is lying down, not absent.
            if whole > 0 and above == 0:
                low = True
                _, luma = measure_tile(img, x, r * th, tw, th, bg, floor_rgb)
            areas.append(whole)
            lumas.append(luma)
        if low:
            prone.append(slot)
        # PEAK AREA, MEDIAN LUMA, and each answers a different question
        # (rule 2). "Is the body ever in frame" is a max; "is this tile
        # legible" is a middle — one bright phase of three does not make a
        # clip readable, and one in-frame phase does mean it is not empty.
        per_clip.append({
            "slot": slot, "row": r, "col": c,
            "area": max(areas),
            "luma": sorted(lumas)[len(lumas) // 2],
            "areas": areas,
        })

    areas = sorted(p["area"] for p in per_clip)
    median_area = areas[len(areas) // 2]

    dark, small, empty = [], [], []
    for p in per_clip:
        if p["area"] == 0:
            empty.append(p["slot"])
        elif p["luma"] < DARK_LUMA:
            dark.append(p["slot"])
        elif p["area"] < median_area * SMALL_FRACTION:
            small.append(p["slot"])

    if verbose:
        print(f"sheet-read — {sheet.name}, {img.width}x{img.height}, "
              f"{len(per_clip)} clips, tile {tw}x{th}, background {bg}, "
              f"floor at y={floor} {floor_rgb} luma {floor_luma}"
              + ("" if floor < th else " (none found)"))
        print(f"  median body area {median_area}px, "
              f"luma {min(p['luma'] for p in per_clip):.0f}"
              f"..{max(p['luma'] for p in per_clip):.0f}")
        if prone:
            print(f"  prone ({len(prone)} of {len(per_clip)}, measured whole-tile): "
                  + ", ".join(sorted(prone)))
        for name, group in (("EMPTY", empty), ("DARK", dark), ("SMALL", small)):
            if group:
                print(f"  {name} ({len(group)} of {len(per_clip)}): "
                      + ", ".join(sorted(group)))
        legible = len(per_clip) - len(dark) - len(small) - len(empty)
        print(f"  legible {legible} of {len(per_clip)}")
        # THE SPREAD, WHICH IS THE ACTUAL DIAGNOSTIC. A per-tile bound answers
        # "can I read this one"; it cannot see the fault that produced the dark
        # tiles, because that fault is the sheet not being ONE exposure. The
        # game's lighting pass writes RenderSettings.ambientLight from the
        # clock every frame, the clock advances while 201 tiles render, and the
        # luma over render order traces two clean day/night cycles — 61 at the
        # first clip, 14 in the trough, 77 at the peak. When the ambient is
        # pinned per tile this range collapses, and the range is what says so.
        lo = min(p["luma"] for p in per_clip if p["area"])
        hi = max(p["luma"] for p in per_clip)
        print(f"sheetLegible={legible} sheetDark={len(dark)} "
              f"sheetSmall={len(small)} sheetEmpty={len(empty)} "
              f"sheetClips={len(per_clip)} sheetLuma={lo:.0f}..{hi:.0f}")
    return {"clips": per_clip, "dark": dark, "small": small, "empty": empty,
            "prone": prone, "median_area": median_area}


def selftest():
    """BOTH WAYS, accepting case first.

    Synthesises a sheet whose faults are known by construction: one clip lit,
    one black, one tiny, one absent. The accepting assertion is that the LIT
    clip is reported as neither dark nor small — a checker that flags
    everything would pass a rejecting-only test and be useless.
    """
    from PIL import Image, ImageDraw
    import tempfile

    # WITH A FLOOR BAND, because the real sheet has one and the bug this
    # selftest exists to catch lives entirely inside it: a body lying ON the
    # floor was reported as EMPTY, since the luma region is cut above the floor
    # line. A fixture with no floor cannot reach that code at all — which is
    # the half of rule 5b that goes unrun.
    tw, th, cols, nrows = 110, 220, 5, 1
    floor_y = 165
    img = Image.new("RGB", (tw * cols * PHASES_PER_CLIP, th * nrows), (140, 141, 150))
    d = ImageDraw.Draw(img)
    d.rectangle([0, floor_y, img.width, th], fill=(182, 191, 213))
    slots = ["lit", "black", "tiny", "gone", "prone"]
    for c, slot in enumerate(slots):
        for p in range(PHASES_PER_CLIP):
            x = (c * PHASES_PER_CLIP + p) * tw
            if slot == "lit":
                d.rectangle([x + 35, 40, x + 75, 160], fill=(205, 200, 195))
            elif slot == "black":
                d.rectangle([x + 35, 40, x + 75, 160], fill=(6, 6, 8))
            elif slot == "tiny":
                d.rectangle([x + 52, 140, x + 60, 160], fill=(205, 200, 195))
            elif slot == "prone":
                # Entirely below the floor line, and DARKER than it, which is
                # what a body on a lit plane actually is.
                d.rectangle([x + 20, floor_y + 12, x + 90, floor_y + 44],
                            fill=(58, 56, 54))
            # "gone" draws nothing at all

    tmp = pathlib.Path(tempfile.mkdtemp())
    # CLEANED ON EXIT, HOWEVER THE RUN ENDS — the sibling without this
    # pair leaked 17GB of 68MB temp dirs in a day (verify runs these
    # selftests on every commit) and red-walled the disk mid-verify.
    # Same two lines export-decode.py has carried since its own leak.
    import atexit as _ax, shutil as _sh
    _ax.register(_sh.rmtree, tmp, True)
    sheet, tsv = tmp / "clips.jpg", tmp / "clips.tsv"
    img.save(sheet, quality=95)
    tsv.write_text("row\tcol\tslot\n"
                   + "".join(f"0\t{c}\t{s}\n" for c, s in enumerate(slots)),
                   encoding="utf-8")

    r = read(sheet, tsv, verbose=False)
    bad, checks = [], 0

    # ACCEPTING FIRST.
    checks += 1
    if "lit" in r["dark"] or "lit" in r["small"] or "lit" in r["empty"]:
        bad.append("flagged the well-lit clip, which is the case it must pass")

    # AND THE REGRESSION THIS FIXTURE GREW A FLOOR FOR: a body lying on the
    # floor is lying down, not absent.
    checks += 1
    if "prone" in r["empty"]:
        bad.append("called a body lying on the floor EMPTY — the original bug")
    checks += 1
    if "prone" not in r["prone"]:
        bad.append("did not report the prone body as prone")

    for want, group, name in (("black", r["dark"], "dark"),
                              ("tiny", r["small"], "small"),
                              ("gone", r["empty"], "empty")):
        checks += 1
        if want not in group:
            bad.append(f"missed the {name} clip ({want})")

    # AND the missing-sheet case must not read as clean.
    checks += 1
    if read(tmp / "nope.jpg", tmp / "nope.tsv", verbose=False) is not None:
        bad.append("a missing sheet returned a result instead of saying so")

    for f in (sheet, tsv):
        f.unlink()
    tmp.rmdir()

    if bad:
        for b in bad:
            print(f"  FAIL {b}")
        return 1
    print(f"sheet-read ok ({checks} checks)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sheet")
    ap.add_argument("--tsv")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    return 0 if read(a.sheet, a.tsv) is not None else 1


if __name__ == "__main__":
    sys.exit(main())
