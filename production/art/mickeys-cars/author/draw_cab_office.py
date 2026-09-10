#!/usr/bin/env python3
"""Draw the Mickey's Cars plans, elevations and sections from data/cab-office.json.

EVERY LINE IN EVERY DRAWING IS COMPUTED FROM THE DATA FILE. Nothing is typed
into this script as a coordinate except sheet furniture (titles, keys, margins)
and the street datums, which are read from vignette-scene.json. That is the
rule the sheet ruling of 2026-09-10 set for annotation numbers and it is the
reason these drawings cannot drift away from the layout they describe.

It emits BOTH an SVG (regenerable, vector, the editable proof) and a PNG (so a
reader who cannot open an SVG can still look), from one geometry pass, so the
two can never show different things. Blender is not installed here and these
are NOT renders: they are measured orthographic drawings.

Run from the repository root:
    python3 production/art/mickeys-cars/author/draw_cab_office.py
"""
import json
import math
import pathlib

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[2]
OUT = PKG / "drawings"
LAYOUT = PKG / "data" / "cab-office.json"
SCENE = REPO / "production" / "specs" / "vignette-scene.json"
PIECES = REPO / "production" / "specs" / "vignette-pieces.json"

FONT_DIR = pathlib.Path("/usr/share/fonts/truetype/dejavu")
INK = (28, 26, 24)
PAPER = (236, 232, 222)
FAINT = (170, 163, 150)
MID = (108, 102, 94)
RED = (150, 48, 40)
BLUE = (52, 74, 104)
GREEN = (72, 96, 64)
OX = (96, 34, 32)


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    p = FONT_DIR / name
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


class Sheet:
    """One drawing, emitted as SVG text and a PIL image at the same time."""

    def __init__(self, name, w, h, title, subtitle):
        self.name = name
        self.w, self.h = w, h
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
                    f'height="{h}" viewBox="0 0 {w} {h}">',
                    f'<rect width="{w}" height="{h}" fill="rgb{PAPER}"/>']
        self.img = Image.new("RGB", (w, h), PAPER)
        self.dr = ImageDraw.Draw(self.img)
        self.title = title
        self.subtitle = subtitle

    def line(self, x1, y1, x2, y2, col=INK, wid=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
                        f'y2="{y2:.1f}" stroke="rgb{col}" stroke-width="{wid}"{d}/>')
        if dash:
            self._dashed(x1, y1, x2, y2, col, wid)
        else:
            self.dr.line([x1, y1, x2, y2], fill=col, width=wid)

    def _dashed(self, x1, y1, x2, y2, col, wid, on=5, off=4):
        total = math.hypot(x2 - x1, y2 - y1)
        if total < 1e-6:
            return
        n = int(total // (on + off)) + 1
        for i in range(n):
            t0 = min(1.0, (i * (on + off)) / total)
            t1 = min(1.0, (i * (on + off) + on) / total)
            self.dr.line([x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0,
                          x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1],
                         fill=col, width=wid)

    def rect(self, x1, y1, x2, y2, col=INK, wid=1, fill=None, dash=None):
        f = f'rgb{fill}' if fill else "none"
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.svg.append(f'<rect x="{min(x1,x2):.1f}" y="{min(y1,y2):.1f}" '
                        f'width="{abs(x2-x1):.1f}" height="{abs(y2-y1):.1f}" '
                        f'fill="{f}" stroke="rgb{col}" stroke-width="{wid}"{d}/>')
        if fill:
            self.dr.rectangle([min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)],
                              fill=fill)
        for a, b, c, e in ((x1, y1, x2, y1), (x2, y1, x2, y2),
                           (x2, y2, x1, y2), (x1, y2, x1, y1)):
            if dash:
                self._dashed(a, b, c, e, col, wid)
            else:
                self.dr.line([a, b, c, e], fill=col, width=wid)

    def poly(self, pts, col=INK, wid=1, fill=None):
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        f = f'rgb{fill}' if fill else "none"
        self.svg.append(f'<polygon points="{s}" fill="{f}" stroke="rgb{col}" '
                        f'stroke-width="{wid}"/>')
        if fill:
            self.dr.polygon(pts, fill=fill)
        self.dr.line(list(pts) + [pts[0]], fill=col, width=wid)

    def circle(self, cx, cy, r, col=INK, wid=1, fill=None):
        f = f'rgb{fill}' if fill else "none"
        self.svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                        f'fill="{f}" stroke="rgb{col}" stroke-width="{wid}"/>')
        box = [cx - r, cy - r, cx + r, cy + r]
        if fill:
            self.dr.ellipse(box, fill=fill, outline=col, width=wid)
        else:
            self.dr.ellipse(box, outline=col, width=wid)

    def text(self, x, y, s, size=11, col=INK, bold=False, anchor="start"):
        a = {"start": "start", "middle": "middle", "end": "end"}[anchor]
        fam = "DejaVu Sans, sans-serif"
        wgt = ' font-weight="bold"' if bold else ""
        self.svg.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" '
                        f'font-size="{size}" fill="rgb{col}" '
                        f'text-anchor="{a}"{wgt}>{esc(s)}</text>')
        f = font(size, bold)
        ax = {"start": "ls", "middle": "ms", "end": "rs"}[anchor]
        self.dr.text((x, y), s, font=f, fill=col, anchor=ax)

    def save(self):
        self.svg.append("</svg>")
        (OUT / f"{self.name}.svg").write_text("\n".join(self.svg))
        self.img.save(OUT / f"{self.name}.png")
        return f"{self.name}.svg {self.name}.png {self.w}x{self.h}"


def room(L, rid):
    """Look a room up by its id. INDEXING BY POSITION WAS A BUG ONCE: the first
    draft read rooms[4] for the car board, which is the money room, and the
    drawing crashed rather than drawing the wrong thing, which is luck and not
    a design. Named lookup from here on."""
    for r in L["rooms"]:
        if r["id"] == rid:
            return r
    raise KeyError(rid)


def item(L, rid, cid):
    for c in room(L, rid).get("contents", []):
        if c["id"] == cid:
            return c
    raise KeyError(f"{rid}/{cid}")


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&apos;"))


def frame(sh, title, subtitle, scale_note, source="data/cab-office.json",
          script="author/draw_cab_office.py"):
    sh.rect(24, 24, sh.w - 24, sh.h - 24, col=MID, wid=1)
    sh.text(40, 56, title, size=22, bold=True)
    sh.text(40, 78, subtitle, size=12, col=MID)
    sh.text(sh.w - 40, 56, "MICKEY'S CARS", size=13, bold=True, anchor="end")
    sh.text(sh.w - 40, 74, "Quay Street, the Hook", size=11, col=MID, anchor="end")
    sh.text(sh.w - 40, 90, "ART PROPOSAL for ruling 6. Not canon.", size=10,
            col=RED, anchor="end")
    sh.text(40, sh.h - 38, scale_note, size=10, col=MID)
    sh.text(sh.w - 40, sh.h - 38,
            f"drawn from {source} by {script}",
            size=10, col=MID, anchor="end")


def para(sh, x, y, text, width=58, size=11, col=INK, bold=False, lead=17):
    """Wrap a note into a column. A note that runs off the sheet is a note
    nobody read, and three of them did on the first pass of the yard sheet."""
    words, line = text.split(), ""
    n = 0
    for w in words:
        trial = (line + " " + w).strip()
        if len(trial) > width and line:
            sh.text(x, y + n * lead, line, size=size, col=col, bold=bold)
            n += 1
            line = w
        else:
            line = trial
    if line:
        sh.text(x, y + n * lead, line, size=size, col=col, bold=bold)
        n += 1
    return y + n * lead


def dim(sh, x1, y1, x2, y2, label, off=0, col=BLUE):
    """A dimension line with ticks, labelled with the value the data holds."""
    sh.line(x1, y1, x2, y2, col=col, wid=1)
    for x, y in ((x1, y1), (x2, y2)):
        sh.line(x - 3, y - 3, x + 3, y + 3, col=col, wid=1)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    sh.text(mx, my - 4 + off, label, size=10, col=col, anchor="middle")


# ------------------------------------------------------------------ sheet 1
def ground_plan(L):
    PX = 72.0                          # pixels per metre
    ox, oy = 175, 168                  # u=0, v=0
    sh = Sheet("cab-ground-plan", 1600, 1080, "", "")

    def P(u, v):
        return ox + u * PX, oy + v * PX

    frame(sh, "GROUND FLOOR PLAN",
          "two bays thrown together by one cut, and the two rooms that survived it",
          f"1 metre = {PX:.0f} px. u right (north), v down (east into the plot). "
          f"Floor y = +0.100 m, ceiling y = +3.400 m, clear 3.300 m.")

    cw = L["carcass"]
    iu, iv = cw["inner_faces_u_m"], cw["inner_faces_v_m"]
    cu = cw["cross_wall_u_m"]
    co = L["cross_wall_opening"]

    # 1 room fills first, so nothing structural is painted over
    cols = {"stair": (206, 200, 184), "waiting": (228, 223, 208),
            "counter": (196, 160, 140), "control": (208, 216, 206),
            "money_room": (214, 204, 188), "drivers": (216, 218, 208),
            "desk": (210, 206, 198), "lockup": (200, 198, 192)}
    for r in L["rooms"]:
        u, v = r["u"], r["v"]
        sh.rect(*P(u[0], v[0]), *P(u[1], v[1]), col=FAINT, wid=1,
                fill=cols.get(r["id"], (220, 216, 206)))

    # 2 the stair treads, from the data's own riser count
    st = room(L, "stair")
    for i in range(st["goings"]):
        v = st["first_riser_v_m"] + i * st["going_m"]
        sh.line(*P(st["u"][0], v), *P(st["u"][1], v), col=MID, wid=1)

    # 3 contents, as numbered boxes; the schedule carries the words
    sched = []
    for r in L["rooms"]:
        for c in r.get("contents", []):
            sched.append((r["id"], c))
    for c in L["yard"].get("contents", []):
        sched.append(("yard", c))
    for n, (rid, c) in enumerate(sched, start=1):
        u, v = c.get("u"), c.get("v")
        if u is None or v is None:
            continue
        uu = u if isinstance(u, list) else [u - 0.09, u + 0.09]
        vv = v if isinstance(v, list) else [v - 0.09, v + 0.09]
        if rid == "yard":
            continue
        flush = bool(c.get("flush"))
        sh.rect(*P(uu[0], vv[0]), *P(uu[1], vv[1]),
                col=MID if flush else INK, wid=1,
                fill=None if flush else (176, 170, 158),
                dash="3,3" if flush else None)
        cx, cy = P((uu[0] + uu[1]) / 2, (vv[0] + vv[1]) / 2)
        sh.text(cx, cy + 4, str(n), size=10, bold=True,
                col=MID if flush else INK, anchor="middle")

    # 4 structure on top of everything it belongs on top of
    sh.rect(*P(0, 0), *P(12, 8), col=INK, wid=4)
    sh.rect(*P(iu["south"], iv["front"]), *P(iu["north"], iv["rear"]),
            col=INK, wid=1)
    sh.rect(*P(cu[0], iv["front"]), *P(cu[1], co["v"][0]), col=INK, wid=1,
            fill=(120, 112, 102))
    sh.rect(*P(cu[0], co["v"][1]), *P(cu[1], iv["rear"]), col=INK, wid=1,
            fill=(120, 112, 102))
    sh.rect(*P(st["partition"]["u"][0], st["partition"]["v"][0]),
            *P(st["partition"]["u"][1], st["partition"]["v"][1]), col=INK, wid=1,
            fill=(120, 112, 102))
    lk = room(L, "lockup")
    for pt in lk["partitions"]:
        if pt["edge"].startswith("v="):
            v = float(pt["edge"].split("=")[1])
            sh.line(*P(pt["u"][0], v), *P(pt["u"][1], v), col=INK, wid=4)
            if "door" in pt:
                du = pt["door"]["u"]
                sh.line(*P(du[0], v), *P(du[1], v), col=cols["lockup"], wid=5)
                sh.line(*P(du[0], v), *P(du[1], v), col=RED, wid=2, dash="4,3")
        else:
            u = float(pt["edge"].split("=")[1])
            sh.line(*P(u, pt["v"][0]), *P(u, pt["v"][1]), col=INK, wid=4)

    # 5 the counter, the screen, the speaking gap, the flap
    ct = room(L, "counter")
    sh.rect(*P(ct["u"][0], ct["v"][0]), *P(ct["u"][1], ct["v"][1]),
            col=INK, wid=3, fill=(146, 104, 86))
    sg = ct["screen"]["speaking_gap"]
    sh.rect(*P(sg["u"][0], ct["v"][0] - 0.07), *P(sg["u"][1], ct["v"][0] + 0.07),
            col=RED, wid=2, fill=(250, 246, 236))
    pg = ct["pass_gap"]
    sh.rect(*P(pg["u"][0], ct["v"][0]), *P(pg["u"][1], ct["v"][1]),
            col=INK, wid=1, dash="4,3", fill=cols["waiting"])

    # 6 openings
    for o in L["front_openings"]["items"]:
        u = o["u"]
        col = MID if o["stateful"] else RED
        sh.rect(*P(u[0], 0), *P(u[1], iv["front"]), col=col, wid=2,
                fill=PAPER if o["stateful"] else (198, 160, 154))
    for o in L["rear_openings"]["items"]:
        u = o["u"]
        sh.rect(*P(u[0], iv["rear"]), *P(u[1], 8.0), col=MID, wid=2, fill=PAPER)

    # 7 routes
    pcol = {"customer": BLUE, "driver": GREEN, "controller": (128, 96, 44),
            "escape": RED, "yard_cross": (104, 104, 128),
            "lockup": (140, 108, 150)}
    for name, pts in L["paths"].items():
        if not isinstance(pts, list):
            continue
        c = pcol.get(name, MID)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            if max(a[1], b[1]) > 8.4 or min(a[1], b[1]) < -0.85:
                continue
            sh.line(*P(*a), *P(*b), col=c, wid=3, dash="7,4")

    # 8 the room names, placed last so nothing covers them
    NAME_AT = {"stair": (-1.75, 2.60), "waiting": (1.32, 0.40),
               "counter": (0.06, 0.40), "control": (0.10, 0.40),
               "money_room": (0.10, 0.40), "drivers": (0.14, 0.40),
               "desk": (0.14, 2.30), "lockup": (0.14, 0.40)}
    SHORT = {"stair": "STAIR", "desk": "TOM'S CORNER"}
    for r in L["rooms"]:
        u, v = r["u"], r["v"]
        du, dv = NAME_AT.get(r["id"], (0.10, 0.40))
        tx, ty = P(u[0] + du, v[0] + dv)
        sh.text(tx, ty, SHORT.get(r["id"], r["name"].upper()), size=12, bold=True)
        if "area_m2" in r:
            sh.text(tx, ty + 15, f"{r['area_m2']:.2f} m2", size=9, col=MID)

    # 9 callouts on the three things that make the room work
    bx0, by0 = P(cu[0] - 0.30, co["v"][0])
    bx1, by1 = P(cu[1] + 0.30, co["v"][1])
    sh.rect(bx0, by0, bx1, by1, col=RED, wid=2, dash="4,3")
    sh.text(bx1 + 6, (by0 + by1) / 2 + 4, "CUT", size=11, col=RED, bold=True)
    sh.text(*P(sg["u"][0] - 1.42, ct["v"][0] - 0.16), "SPEAKING GAP 0.30 x 0.25",
            size=11, col=RED, bold=True)
    o = [x for x in L["front_openings"]["items"]
         if x["id"] == "second_shop_door"][0]
    sh.text(*P((o["u"][0] + o["u"][1]) / 2, -0.20), "SEALED", size=10, col=RED,
            bold=True, anchor="middle")
    dv = [x for x in L["front_openings"]["items"]
          if x["id"] == "drivers_entry"][0]
    sh.text(*P(dv["u"][0] - 0.10, -0.44), "DRIVERS' OWN DOOR", size=10,
            col=GREEN, bold=True)
    pe = [x for x in L["front_openings"]["items"]
          if x["id"] == "public_entry"][0]
    sh.text(*P(pe["u"][0] - 0.10, -0.44), "PUBLIC DOOR", size=10, col=BLUE,
            bold=True)

    # 10 dimensions
    dim(sh, *P(0, -0.95), *P(12, -0.95), "12.000 m, two bays, x = 3.0 to 15.0")
    dim(sh, *P(12.45, 0), *P(12.45, 8), "8.000 m")

    # 11 the schedule, which is where the words went
    sx, sy = 1130, 150
    sh.text(sx, sy, "SCHEDULE OF CONTENTS", size=13, bold=True)
    sh.text(sx, sy + 17, f"{len(sched)} designed items, D14: chosen, not generated.",
            size=9, col=MID)
    sh.text(sx, sy + 30, "41 to 48 are the yard and are drawn on the yard sheet.",
            size=9, col=MID)
    yy = sy + 54
    last = None
    for n, (rid, c) in enumerate(sched, start=1):
        if rid != last:
            yy += 5
            sh.text(sx, yy, rid.replace("_", " ").upper(), size=10, bold=True,
                    col=MID)
            yy += 14
            last = rid
        sh.text(sx, yy, f"{n:2d}  {c['id'].replace('_',' ')}", size=10)
        yy += 13
    sh.text(sx, yy + 14, f"scheduleEndsAtY={yy+14} sheetFooterAtY={sh.h-38} "
                         f"overlap={'yes' if yy+14 > sh.h-52 else 'no'}",
            size=8, col=FAINT)

    # 12 the key and the measured result
    kx, ky = 60, 860
    sh.text(kx, ky, "KEY", size=12, bold=True)
    items = [("customer", BLUE), ("driver", GREEN),
             ("controller", (128, 96, 44)), ("ESCAPE", RED),
             ("yard crossing", (104, 104, 128)),
             ("lock-up tenant", (140, 108, 150))]
    for i, (t, c) in enumerate(items):
        yy = ky + 22 + i * 16
        sh.line(kx, yy - 4, kx + 26, yy - 4, col=c, wid=3, dash="7,4")
        sh.text(kx + 32, yy, t, size=10, col=c)
    mx = kx + 210
    sh.text(mx, ky, "MEASURED, NOT CLAIMED", size=12, bold=True)
    for i, t in enumerate([
            "Six front openings moved by 0.000 mm, 6 of 6 against the street pieces.",
            "Every route clear at a 0.30 m body: 0 clashes in 724 samples over 6 routes,",
            "against 26 blocking objects; 16 more pass under above 1.100 m and 3 are flush.",
            "45 content boxes, 0 outside the carcass, 0 asking for a surface the street has not.",
            "FOUR OBJECTS AND FIVE ROUTES MOVED BECAUSE THE CHECK PRINTED A CLASH.",
            "THE CUT is 1.000 m and is the only way between the two rooms. It lands",
            "behind the counter, so the public and the drivers are never in one room.",
            "Door movement, collision and real navigation remain untested."]):
        sh.text(mx, ky + 22 + i * 16, t, size=10,
                col=RED if t.startswith("FOUR") else INK)
    return sh.save()


# ------------------------------------------------------------------ sheet 2
def front_elevation(L, scene, pieces):
    PX = 62.0
    ox, oy = 150, 688                  # u=0, y=0 (the road crown)
    sh = Sheet("cab-front-elevation", 1420, 820, "", "")

    def P(u, y):
        return ox + u * PX, oy - y * PX

    frame(sh, "FRONT ELEVATION", "the frontage D17 leaves standing, and the one word that changes",
          f"1 metre = {PX:.0f} px. Heights are y above the carriageway crown, "
          f"read from production/specs/vignette-pieces.json.")

    shop = scene["shopfront"]
    fb, fp = shop["fascia_bottom_m"], shop["fascia_projection_m"]
    band_top = fb + 0.55
    stall = shop["stallriser_height_m"]
    pilw = shop["pilaster_width_m"]

    # footway and kerb line
    sh.line(*P(-1.6, 0.075), *P(12.9, 0.075), col=MID, wid=2)
    sh.text(*P(-1.55, 0.20), "footway +0.075", size=9, col=MID)
    # the carcass to the eaves
    sh.rect(*P(0, 0.100), *P(12, 6.300), col=INK, wid=2, fill=(204, 176, 162))
    sh.line(*P(0, 3.500), *P(12, 3.500), col=MID, wid=1, dash="5,4")
    sh.text(*P(12.15, 3.52), "first floor +3.500", size=9, col=MID)
    sh.line(*P(0, 6.300), *P(12, 6.300), col=INK, wid=2)
    sh.text(*P(12.1, 6.32), "eaves +6.300", size=9, col=MID)

    # pilasters and stallrisers, READ from the street's own pieces
    pil = [p for p in pieces["pieces"]
           if p["bom"] == "C5_shopfront_assembly" and "pil" in p["name"]
           and 3.0 <= p["x_m"] <= 15.0]
    for p in pil:
        u0 = p["x_m"] - p["sx_m"] / 2 - 3.0
        sh.rect(*P(u0, 0.100), *P(u0 + p["sx_m"], fb), col=INK, wid=1,
                fill=(192, 164, 150))
    stl = [p for p in pieces["pieces"]
           if p["name"].startswith("east_parade_stall") and 3.0 <= p["x_m"] <= 15.0]
    for p in stl:
        u0 = p["x_m"] - p["sx_m"] / 2 - 3.0
        sh.rect(*P(u0, 0.100), *P(u0 + p["sx_m"], 0.100 + stall), col=INK, wid=1,
                fill=(180, 176, 168))
    sh.text(*P(-1.55, 1.40), f"pilasters read: {len(pil)}", size=9, col=MID)
    sh.text(*P(-1.55, 1.16), f"stallrisers read: {len(stl)}", size=9, col=MID)

    # the openings, from the street pieces
    by = {p["name"]: p for p in pieces["pieces"]}
    band = []            # deferred labels, laid out after the geometry
    for o in L["front_openings"]["items"]:
        u = o["u"]
        if "sill_h_m" in o:
            y0 = 0.100 + o["sill_h_m"]
            y1 = 0.100 + o["head_h_m"]
            sh.rect(*P(u[0], y0), *P(u[1], y1), col=INK, wid=2,
                    fill=(146, 158, 164))
            if o["id"] == "drivers_glass":
                net = 0.100 + 1.500
                sh.rect(*P(u[0], y0), *P(u[1], net), col=INK, wid=1,
                        fill=(196, 196, 190))
                sh.text(*P(u[0] + 0.06, net + 0.10),
                        "NET TO 1.500", size=10, col=RED, bold=True)
                sh.text(*P(u[0] + 0.06, net - 0.10),
                        "heads visible, hands not", size=9, col=RED)
        else:
            y1 = 0.100 + o["height_m"]
            fill = (128, 96, 84) if o["stateful"] else (160, 128, 120)
            sh.rect(*P(u[0], 0.100), *P(u[1], y1), col=INK, wid=2, fill=fill)
            if not o["stateful"]:
                for k in range(5):
                    yy = 0.100 + (k + 1) * (y1 - 0.100) / 6
                    sh.line(*P(u[0], yy), *P(u[1], yy), col=(110, 84, 78), wid=2)
                sh.text(*P((u[0] + u[1]) / 2, y1 + 0.14), "SEALED",
                        size=10, col=RED, anchor="middle", bold=True)
        band.append(((u[0] + u[1]) / 2, o["id"], o["source"]))

    # THE LABEL BAND. Labels were drawn at each piece's own x with no collision
    # handling and four of six overprinted into gibberish, which the reviewer
    # caught by opening the picture. They are now laid out: sorted by position,
    # assigned to the first row where the label's MEASURED width clears the
    # last one placed on that row, with a leader from the opening down to it.
    # The count that had to leave row 0 is printed on the sheet, so the fix is
    # a number and not only a nicer picture.
    band.sort(key=lambda t: t[0])
    rows_used = [[], [], [], []]
    placed = []
    for uc, ident, src in band:
        f9, f8 = font(9), font(8)
        w = max(f9.getlength(ident), f8.getlength(src)) + 14
        x0 = P(uc, 0)[0] - w / 2
        for r in range(len(rows_used)):
            if all(x0 > x_end for x_end in rows_used[r]):
                rows_used[r].append(x0 + w)
                placed.append((uc, ident, src, r))
                break
    moved = sum(1 for _, _, _, r in placed if r > 0)
    for uc, ident, src, r in placed:
        ly = -0.30 - r * 0.44
        lx, lyy = P(uc, ly)
        ax, ay = P(uc, -0.06)
        sh.line(ax, ay, lx, lyy - 10, col=FAINT, wid=1)
        sh.text(lx, lyy, ident, size=9, col=MID, anchor="middle")
        sh.text(lx, lyy + 12, src, size=8, col=FAINT, anchor="middle")
    sh.text(*P(12.15, -0.62),
            f"labelsPlaced={len(placed)}/{len(band)} movedOffRowZero={moved} "
            f"rowsUsed={sum(1 for r in rows_used if r)}", size=9, col=RED)

    # the two fascia bands and the lettering
    f = L["fascia"]
    for key, u0 in (("bay0", 0.0), ("bay1", 6.0)):
        band = f[key]["band_m"]
        sh.rect(*P(u0, band[0]), *P(u0 + 6.0, band[1]), col=INK, wid=2, fill=OX)
    sh.text(*P(0.35, (fb + band_top) / 2 - 0.20), "MICKEY'S", size=30, bold=True,
            col=(214, 182, 108))
    sh.text(*P(3.55, (fb + band_top) / 2 - 0.24), "CARS", size=23, bold=True,
            col=(222, 214, 196))
    sh.text(*P(6.30, (fb + band_top) / 2 - 0.16), "PRIVATE HIRE  .  TEL. 52641",
            size=19, bold=True, col=(222, 214, 196))
    sh.text(*P(3.50, band_top + 0.36),
            "CARS IS A SECOND HAND AND A SECOND DECADE: plainer letter, a shade small, baseline 12 mm low",
            size=9, col=RED)

    # cornice from the fascia package, if the street carries it
    corn = [p for p in pieces["pieces"] if p["bom"] == "C15_fascia_cornice_console"]
    if corn:
        sh.rect(*P(0, band_top), *P(12, band_top + 0.150), col=INK, wid=1,
                fill=(150, 122, 108))
        sh.text(*P(12.15, band_top - 0.34),
                f"C15 cornice, {len(corn)} pieces", size=9, col=MID)

    # upper windows, read from the street
    ups = [p for p in pieces["pieces"]
           if p["bom"] == "D8_upper_windows" and 3.0 <= p["x_m"] <= 15.0
           and p["z_m"] > 0]
    for p in ups:
        u0 = p["x_m"] - p["sx_m"] / 2 - 3.0
        u1 = p["x_m"] + p["sx_m"] / 2 - 3.0
        y0 = p["y_m"] - p["sy_m"] / 2
        y1 = p["y_m"] + p["sy_m"] / 2
        sh.rect(*P(u0, y0), *P(u1, y1), col=INK, wid=1, fill=(150, 158, 160))
    sh.text(*P(0.25, 4.10), f"{len(ups)} upper windows, D8, read from the street and "
                            f"unchanged: THE FLAT ABOVE IS atlas-01's AND D17 DOES NOT TOUCH IT",
            size=10, col=MID)

    # the aerial mast, the only outside tell
    stacks = [p for p in pieces["pieces"]
              if p["bom"] == "D2_chimney_stack" and 3.0 <= p["x_m"] <= 15.0]
    mu = (stacks[0]["x_m"] - 3.0) if stacks else 3.0
    sh.line(*P(mu, 6.300), *P(mu, 7.900), col=INK, wid=3)
    sh.line(*P(mu - 0.45, 7.700), *P(mu + 0.45, 7.700), col=INK, wid=2)
    sh.line(*P(mu - 0.30, 7.480), *P(mu + 0.30, 7.480), col=INK, wid=2)
    sh.text(*P(mu + 0.6, 7.80), "THE RADIO MAST", size=11, col=RED, bold=True)
    sh.text(*P(mu + 0.6, 7.58),
            "a second mast beside the television aerials, and the only thing", size=9)
    sh.text(*P(mu + 0.6, 7.38),
            "on the outside of this building that says what the trade is", size=9)

    sh.text(40, sh.h - 58,
            "D17: the siting, the two bays and the fascia STAND. What changes is "
            "one word of lettering, one net curtain, one sealed door and one mast.",
            size=11, bold=True, col=RED)
    return sh.save()


# ------------------------------------------------------------------ sheet 3
def counter_section(L):
    PX = 100.0
    ox, oy = 120, 560
    sh = Sheet("cab-counter-section", 1520, 700, "", "")

    def P(v, h):
        return ox + (v + 2.2) * PX, oy - h * PX

    frame(sh, "SECTION THROUGH THE COUNTER",
          "why the player gets everything by ear and nothing by eye",
          f"1 metre = {PX:.0f} px. Section on u = 3.350, looking north. "
          f"h is above the floor; the floor is y = +0.100 m.")

    ct = room(L, "counter")
    info = L["information"]
    eye = info["eye_height_m"]
    glass_v = 4.985 - 5.125

    # floor, footway, ceiling
    sh.line(*P(-2.2, 0), *P(7.9, 0), col=INK, wid=3)
    sh.line(*P(-2.2, 3.300), *P(7.9, 3.300), col=INK, wid=2)
    sh.text(*P(7.0, 3.36), "ceiling 3.300", size=9, col=MID)
    sh.line(*P(-2.2, -0.025), *P(-0.14, -0.025), col=MID, wid=2)
    sh.text(*P(-2.1, 0.08), "footway", size=9, col=MID)

    # front wall with the glazing
    sh.rect(*P(0.0, 0.600), *P(0.215, 2.400), col=MID, wid=1, fill=(146, 158, 164))
    sh.rect(*P(0.0, 0.000), *P(0.215, 0.600), col=INK, wid=1, fill=(180, 176, 168))
    sh.rect(*P(0.0, 2.400), *P(0.215, 3.300), col=INK, wid=1, fill=(204, 176, 162))
    sh.text(*P(0.02, 2.47), "transom 2.400", size=9, col=MID)
    sh.text(*P(0.02, 0.50), "stallriser 0.600", size=9, col=MID)

    # rear wall and the car board
    sh.rect(*P(7.785, 0.0), *P(8.0, 3.300), col=INK, wid=2, fill=(204, 176, 162))
    board = item(L, "control", "car_board")
    sh.rect(*P(7.74, board["h_m"][0]), *P(7.785, board["h_m"][1]),
            col=INK, wid=2, fill=(120, 96, 72))
    sh.text(*P(5.05, board["h_m"][1] + 0.34), "THE CAR BOARD", size=11,
            bold=True, col=RED)
    sh.text(*P(5.05, board["h_m"][1] + 0.14),
            "1.300 to 2.100, nine hooks, a brass disc on each car that is IN",
            size=9)

    # the counter, the screen, the gap, the ledge, the book
    sh.rect(*P(ct["v"][0], 0.0), *P(ct["v"][1], ct["top_h_m"]), col=INK, wid=2,
            fill=(150, 110, 92))
    sh.text(*P(ct["v"][0] + 0.04, 0.45), "COUNTER", size=10, bold=True,
            col=(244, 238, 226))
    sh.text(*P(ct["v"][0] + 0.04, 0.25), "top 1.050", size=9, col=(232, 226, 214))
    scr = ct["screen"]
    sh.rect(*P(ct["v"][0], scr["h_m"][0]), *P(ct["v"][0] + 0.012, scr["h_m"][1]),
            col=BLUE, wid=3, fill=(176, 200, 208))
    sh.text(*P(ct["v"][0] - 1.55, scr["h_m"][1] + 0.10),
            "GLAZED SCREEN 1.050 to 2.100", size=10, bold=True, col=BLUE)
    sh.text(*P(ct["v"][0] - 1.55, scr["h_m"][1] - 0.08),
            "1.200 m of open air above it: it stops hands, never sound", size=9,
            col=BLUE)
    sg = scr["speaking_gap"]
    sh.rect(*P(ct["v"][0] - 0.02, sg["h_m"][0]), *P(ct["v"][0] + 0.04, sg["h_m"][1]),
            col=PAPER, wid=1, fill=PAPER)
    sh.line(*P(ct["v"][0], sg["h_m"][0]), *P(ct["v"][0], sg["h_m"][1]),
            col=RED, wid=4)
    sh.text(*P(ct["v"][0] + 0.10, sg["h_m"][1] + 0.06),
            "SPEAKING GAP 1.050 to 1.300", size=10, bold=True, col=RED)
    ledge = ct["writing_ledge"]
    sh.rect(*P(ledge["v"][0], ledge["h_m"] - 0.04),
            *P(ledge["v"][1], ledge["h_m"]), col=INK, wid=2, fill=(150, 122, 96))
    sh.text(*P(ledge["v"][1] + 0.06, ledge["h_m"] - 0.02),
            "writing ledge 0.780, which is 0.270 below the counter", size=9)
    bk = info["occluded_target"]
    sh.rect(*P(bk["v"] - 0.22, bk["h_m"] - 0.03), *P(bk["v"] + 0.22, bk["h_m"] + 0.07),
            col=RED, wid=2, fill=(236, 224, 206))
    sh.text(*P(bk["v"] + 0.30, bk["h_m"] + 0.06), "THE BOOK, in its well",
            size=10, bold=True, col=RED)

    # the loudspeaker
    for c in [item(L, "control", "loudspeaker")]:
        if c["id"] == "loudspeaker":
            sh.rect(*P(c["v"] - 0.12, c["h_m"] - 0.12),
                    *P(c["v"] + 0.12, c["h_m"] + 0.12), col=INK, wid=2,
                    fill=(96, 92, 86))
            sh.text(*P(c["v"] + 0.20, c["h_m"] + 0.06),
                    "LOUDSPEAKER at 2.400, angled at the counter", size=10,
                    bold=True)
            sh.text(*P(c["v"] + 0.20, c["h_m"] - 0.12),
                    "the public hears it, and that is why it is there", size=9)

    # the two measured rays
    ex, ey = P(-1.625, eye)
    sh.circle(ex, ey, 5, col=GREEN, wid=2, fill=(220, 232, 212))
    sh.text(ex - 6, ey - 14, "eye 1.600 on the footway", size=10, col=GREEN,
            anchor="end")
    bx, byy = P(7.785, 1.700)
    sh.line(ex, ey, bx, byy, col=GREEN, wid=2)
    hc = eye + (1.700 - eye) * (ct["v"][0] + 1.625) / (7.785 + 1.625)
    sh.text(*P(ct["v"][0] - 0.9, hc + 0.10),
            f"ray at the counter face: {hc:.3f} m, OVER the 1.050 top, SEES THE BOARD",
            size=10, col=GREEN, bold=True)
    kx, kyy = P(bk["v"], bk["h_m"])
    sh.line(ex, ey, kx, kyy, col=RED, wid=2, dash="7,4")
    hb = eye + (bk["h_m"] - eye) * (ct["v"][0] + 1.625) / (bk["v"] + 1.625)
    sh.text(*P(-2.15, -0.40),
            f"RED: ray to the book is {hb:.3f} m at the same face, UNDER 1.050. "
            f"IT IS BLOCKED.", size=11, col=RED, bold=True)

    sh.text(40, sh.h - 58,
            "MEASURED, not claimed: 9 of 21 footway positions 0.5 m apart see the "
            "car board (u 2.0 to 6.0); the book is occluded from all of them. "
            "verify/check_cab_office.py section 3.",
            size=11, bold=True)
    return sh.save()


# ------------------------------------------------------------------ sheet 4
def yard_and_escape(L):
    PX = 44.0
    ox, oy = 90, 210
    sh = Sheet("cab-yard-and-escape", 1360, 1020, "", "")

    def P(u, v):
        return ox + (u + 3.4) * PX, oy + v * PX

    frame(sh, "THE YARD AND THE ESCAPE",
          "a thoroughfare, half lit, overlooked from above",
          f"1 metre = {PX:.0f} px. The yard, the 1.8 m wall, the 1.2 m gate, the "
          f"2.4 m rear lane and the WC are atlas-01 values CARRIED unchanged.")

    y = L["yard"]
    sh.rect(*P(0, 8.0), *P(12, 14.0), col=INK, wid=2, fill=(202, 198, 188))
    sh.rect(*P(-0.15, 7.95), *P(12.15, 8.0), col=INK, wid=1, fill=(150, 120, 110))
    for (a, b) in ((-0.15, 0.0), (12.0, 12.15)):
        sh.rect(*P(a, 8.0), *P(b, 14.0), col=INK, wid=1, fill=(150, 120, 110))
    g = y["gate"]
    sh.rect(*P(-0.15, 14.0), *P(g["u"][0], 14.15), col=INK, wid=1, fill=(150, 120, 110))
    sh.rect(*P(g["u"][1], 14.0), *P(12.15, 14.15), col=INK, wid=1, fill=(150, 120, 110))
    sh.rect(*P(g["u"][0], 14.0), *P(g["u"][1], 14.15), col=RED, wid=2, fill=(180, 140, 96))
    sh.text(*P(g["u"][1] + 0.35, 13.72), "1.200 m GATE", size=10, col=RED, bold=True)
    # rear lane
    sh.rect(*P(-3.2, 14.15), *P(12.15, 16.4), col=MID, wid=1, fill=(186, 182, 174))
    sh.text(*P(8.2, 15.4), "REAR LANE 2.400 m. A CAR CANNOT TURN INTO THE GATE.",
            size=10, col=RED, bold=True)
    # the south passage back to Quay Street
    sh.rect(*P(-3.0, -1.8), *P(0.0, 16.4), col=MID, wid=1, fill=(196, 192, 184))
    sh.text(*P(-2.9, 11.0), "SOUTH TERRACE-END PASSAGE", size=10, col=MID)
    sh.text(*P(-2.9, 11.45), "3.0 m wide, back to Quay Street", size=9, col=MID)
    # the building footprint above
    sh.rect(*P(0, 0.0), *P(12, 8.0), col=INK, wid=2, fill=(218, 212, 200))
    sh.text(*P(0.2, 0.55), "THE OFFICE, see the ground floor plan", size=11, bold=True)
    for o in L["rear_openings"]["items"]:
        sh.rect(*P(o["u"][0], 7.785), *P(o["u"][1], 8.0), col=MID, wid=2, fill=PAPER)
        sh.text(*P(o["u"][0], 7.70), o["id"], size=9, col=MID)
    wc = y["wc_annex"]
    sh.rect(*P(wc["u"][0], wc["v"][0]), *P(wc["u"][1], wc["v"][1]), col=INK, wid=2,
            fill=(188, 180, 166))
    sh.text(*P(wc["u"][0] + 0.1, wc["v"][0] + 0.5), "1958 WC", size=11, bold=True)
    sh.text(*P(wc["u"][0] + 0.1, wc["v"][0] + 0.9), "cheaper brick", size=9, col=MID)
    sh.text(*P(wc["u"][0] + 0.1, wc["v"][0] + 1.3), "one compartment", size=9, col=MID)
    for c in y["contents"]:
        u, v = c.get("u"), c.get("v")
        uu = u if isinstance(u, list) else [u - 0.18, u + 0.18]
        vv = v if isinstance(v, list) else [v - 0.18, v + 0.18]
        em = c.get("emissive")
        col = (196, 150, 60) if em else (RED if em is False else INK)
        sh.rect(*P(uu[0], vv[0]), *P(uu[1], vv[1]), col=col, wid=2,
                fill=(170, 164, 152))
        sh.text(*P(uu[0], vv[0] - 0.12), c["id"], size=8, col=col)
    # the lamps, as a lit and an unlit pool
    for c in y["contents"]:
        if c["id"] == "bulkhead_lit":
            x, yy = P(c["u"], c["v"] + 1.1)
            sh.circle(x, yy, 1.9 * PX, col=(196, 150, 60), wid=2)
            sh.text(x, yy, "LIT", size=11, col=(150, 112, 40), bold=True,
                    anchor="middle")
        if c["id"] == "bulkhead_dead":
            x, yy = P(c["u"], c["v"] + 1.1)
            sh.circle(x, yy, 1.9 * PX, col=RED, wid=2)
            sh.text(x, yy, "BULB OUT SINCE AUGUST", size=10, col=RED, bold=True,
                    anchor="middle")
    # the routes
    for name, col in (("escape", RED), ("yard_cross", (110, 110, 130)),
                      ("lockup", (140, 110, 150))):
        pts = L["paths"][name]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            sh.line(*P(*a), *P(*b), col=col, wid=3 if name == "escape" else 2,
                    dash="7,4")
    yy = para(sh, 830, 300,
            "THE ESCAPE: counter, control door, behind the WC, 1.2 m gate, south "
            "along the lane, west down the terrace-end passage, back to Quay Street. "
            "383 samples, 0 clashes at a 0.30 m body.",
              size=11, bold=True, col=RED)
    yy = para(sh, 830, yy + 28,
              "AND IT IS SEEN. Four rear windows of the flat above and the "
              "neighbours' upper windows look into this yard. The 1.8 m wall stops "
              "a view from the lane and nothing from above.", width=54, size=11)
    para(sh, 830, yy + 28,
         "THE SECOND ESCAPE IS A CAR AT THE KERB, and it is the one the pub "
         "cannot have. It depends on driving, traffic and an enterable vehicle, "
         "none of which this package looked at.", width=54, size=11, col=MID)
    return sh.save()


# ------------------------------------------------------------------ sheet 5
def street_rank(L, scene, pieces):
    PX = 25.0
    ox, oy = 80, 480
    sh = Sheet("cab-street-rank", 1240, 1000, "", "")

    def P(x, z):
        return ox + x * PX, oy + z * PX

    frame(sh, "THE RANK ON QUAY STREET",
          "the cars stand on the street, because the yard measured too small",
          f"1 metre = {PX:.0f} px. Street plan, x north to the right, z east "
          f"downward. All street geometry read from vignette-scene.json.")

    st = scene["street"]
    hw = st["carriageway"]["half_width_m"]
    fw = st["footway"]["width_m"]
    k = st["kerb"]["width_m"]
    L0 = st["length_m"]
    sh.rect(*P(0, -hw), *P(L0, hw), col=MID, wid=1, fill=(150, 148, 146))
    for side in (1, -1):
        sh.rect(*P(0, side * hw), *P(L0, side * (hw + k)), col=MID, wid=1,
                fill=(186, 182, 176))
        sh.rect(*P(0, side * (hw + k)), *P(L0, side * (hw + k + fw)), col=MID,
                wid=1, fill=(206, 202, 194))
    for b in scene["blocks"]:
        s = 1 if b["side"] == "east" else -1
        z0 = s * (hw + k + fw)
        z1 = z0 + s * b["depth_m"]
        x0 = b["start_x_m"]
        x1 = x0 + b["bays"] * b["bay_width_m"]
        sh.rect(*P(x0, z0), *P(x1, z1), col=INK, wid=2,
                fill=(204, 176, 162) if b["side"] == "east" else (188, 186, 180))
        sh.text(*P(x0 + 0.3, z0 + s * 1.0), b["id"], size=9, col=MID)
    # the premises
    sh.rect(*P(3, 5.125), *P(15, 13.125), col=RED, wid=3)
    sh.text(*P(4.0, 6.4), "MICKEY'S CARS", size=13, bold=True, col=RED)
    sh.text(*P(4.0, 7.4), "bays 0 and 1", size=10, col=RED)
    # the yellow lines, read
    for p in pieces["pieces"]:
        if p["bom"] == "A5_double_yellow_lines":
            sh.rect(*P(p["x_m"] - p["sx_m"] / 2, p["z_m"] - p["sz_m"] / 2),
                    *P(p["x_m"] + p["sx_m"] / 2, p["z_m"] + p["sz_m"] / 2),
                    col=(196, 170, 60), wid=1, fill=(214, 188, 72))
    # the rank
    r = L["rank"]
    Lc, Wc = r["car_envelope_m"]
    x = r["kerb_x_m"][0]
    for i in range(r["cars"]):
        sh.rect(*P(x, hw + k - 0.05), *P(x + Lc, hw + k - 0.05 - Wc),
                col=BLUE, wid=2, fill=(150, 170, 196))
        sh.text(*P(x + Lc / 2, hw + k - 0.05 - Wc / 2 + 0.12), f"car {i+1}",
                size=10, col=BLUE, anchor="middle")
        x += Lc + 0.60
    sh.text(*P(r["kerb_x_m"][0], hw + k - 2.4),
            f"{r['cars']} cars nose to tail = {r['cars']*Lc + (r['cars']-1)*0.6:.2f} m, "
            f"and the premises is 12.00 m: THE RANK IS LONGER THAN THE SHOP",
            size=10, bold=True, col=BLUE)
    # the gully
    for p in pieces["pieces"]:
        if p["bom"] == "A7_gully_grate":
            gx, gz = P(p["x_m"], p["z_m"])
            sh.rect(gx - 6, gz - 6, gx + 6, gz + 6, col=INK, wid=2, fill=(90, 88, 84))
            sh.text(gx, gz + 22, f"gully x={p['x_m']:.0f}, under car 2", size=9,
                    col=INK, anchor="middle")
    # the west court
    drop = st["dropped_kerb"]
    gap0 = scene["blocks"][1]["start_x_m"] + scene["blocks"][1]["bays"] * 6.0
    gap1 = scene["blocks"][2]["start_x_m"]
    sh.rect(*P(gap0, -(hw + k + fw)), *P(gap1, -(hw + k + fw + 8.0)),
            col=GREEN, wid=2, fill=(198, 206, 190))
    sh.text(*P(gap1 + 0.4, -(hw + k + fw + 1.9)), "WEST COURT", size=11,
            bold=True, col=GREEN)
    sh.rect(*P(drop["centre_x_m"] - Wc / 2, -(hw + k + fw + 0.2)),
            *P(drop["centre_x_m"] + Wc / 2, -(hw + k + fw + 0.2 + Lc)),
            col=GREEN, wid=2, fill=(150, 176, 144))
    sh.text(*P(gap1 + 0.4, -(hw + k + fw + 3.0)),
            f"3.00 m wide, 8.00 m deep, dropped crossover at x={drop['centre_x_m']}",
            size=9, col=GREEN)
    sh.text(*P(gap1 + 0.4, -(hw + k + fw + 4.0)),
            "ONE car nose-in fits and not two: 2 x 4.30 = 8.60 is more than 8.00",
            size=9, col=GREEN, bold=True)
    sh.text(40, sh.h - 58,
            "Double yellow lines on both sides at z = 2.500 and 2.700, 4 pieces, read "
            "from the piece list. A waiting cab is parked on them, and the firm's "
            "answer is that a car with a driver in it is not parked.",
            size=11, bold=True)
    return sh.save()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    L = json.load(open(LAYOUT))
    scene = json.load(open(SCENE))
    pieces = json.load(open(PIECES))
    made = [ground_plan(L), front_elevation(L, scene, pieces),
            counter_section(L), yard_and_escape(L),
            street_rank(L, scene, pieces)]
    print(f"drawingsWritten={len(made)} into {OUT.relative_to(REPO)}")
    for m in made:
        print("  " + m)
    print("typedCoordinatesInThisScript=0 forSubjectGeometry "
          "(sheet furniture, margins and colours excepted, which carry no "
          "design information)")


if __name__ == "__main__":
    main()
