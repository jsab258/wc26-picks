#!/usr/bin/env python3
"""Draw the Parade's night identity from data/parade-night.json.

Jafar asked for the Parade redesigned without drink AS A DESIGN TASK WITH
PICTURES. A photoreal concept sheet needs the image lane and this commission
may not start a run, so this produces the pictures it CAN produce here: a
measured night elevation of the frontage sequence and a timeline of the
street's discharges. Both are drawn from the data file, both are SVG and PNG
from one geometry pass, and neither is a render.

The photoreal sheet is specified instead, in
`data/parade-night-sheet-2026-09-10.json`, in the schema the local image lane
already reads. NOTHING WAS DISPATCHED.

Run from the repository root:
    python3 production/art/mickeys-cars/author/draw_parade_night.py
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[2]
OUT = PKG / "drawings"
DATA = PKG / "data" / "parade-night.json"

sys.path.insert(0, str(HERE))
from draw_cab_office import Sheet, frame, para, INK, PAPER, FAINT, MID, RED, BLUE, GREEN  # noqa: E402

WARM = (232, 186, 108)
COLD = (206, 226, 232)
NEON = (224, 106, 74)
DARK = (44, 44, 50)
WET = (62, 66, 72)


def night_elevation(D):
    units = D["frontages"]["units"]
    total = sum(u["width_m"] for u in units)
    PX = 22.0
    ox, oy = 90, 560
    sh = Sheet("parade-night-elevation", int(total * PX) + 200, 720, "", "")

    def P(x, h):
        return ox + x * PX, oy - h * PX

    frame(sh, "THE PARADE AT 22.50, WITHOUT DRINK",
          "nine units on Tivoli Street, and the light they make between them",
          f"1 metre = {PX:.1f} px. Frontage sequence and light sources only. "
          f"NOT A RENDER and not a layout: D13 governs how the street is drawn.",
          source="data/parade-night.json",
          script="author/draw_parade_night.py")

    # night sky and wet pavement
    sh.rect(*P(-1.0, 12.0), *P(total + 1.0, 0.0), col=DARK, wid=0, fill=DARK)
    sh.rect(*P(-1.0, 0.0), *P(total + 1.0, -2.6), col=WET, wid=0, fill=WET)

    x = 0.0
    lit_units = 0
    for u in units:
        w = u["width_m"]
        st = u["storeys"]
        top = 4.2 if st == 1 else 7.4
        # the carcass
        sh.rect(*P(x, 0.0), *P(x + w, top), col=(70, 66, 66), wid=2,
                fill=(76, 70, 68))
        # the ground floor window, lit or not
        lit = bool(u["light"]) and u["id"] not in ("recordshop", "chemist")
        if lit:
            lit_units += 1
        warm = any("warm" in s for s in u["light"])
        col = WARM if warm else COLD
        if u["id"] in ("recordshop",):
            col = (52, 50, 54)
        if u["id"] == "chemist":
            col = (92, 84, 70)
        if u["id"] == "amusements":
            col = (150, 96, 168)
        sh.rect(*P(x + 0.4, 0.7), *P(x + w - 0.4, 3.0), col=(40, 38, 38), wid=2,
                fill=col)
        # the spill on the wet pavement, drawn as a widening pool
        if lit:
            sh.poly([P(x + 0.4, 0.0), P(x + w - 0.4, 0.0),
                     P(x + w + 0.5, -2.4), P(x - 0.5, -2.4)],
                    col=col, wid=0, fill=tuple(int(c * 0.42 + WET[i] * 0.58)
                                               for i, c in enumerate(col)))
        # fascia and name
        sh.rect(*P(x + 0.2, 3.0), *P(x + w - 0.2, 3.75), col=(36, 34, 34), wid=2,
                fill=(58, 40, 42))
        short = u["name"].replace("THE ", "")
        sh.text(*P(x + w / 2, 3.14), short, size=10, bold=True,
                col=(226, 214, 196), anchor="middle")
        # upper floor windows
        if st == 2:
            for k in range(int(w // 3.0)):
                ux = x + 1.0 + k * 3.0
                sh.rect(*P(ux, 4.5), *P(ux + 1.0, 6.1), col=(48, 46, 46), wid=1,
                        fill=(60, 58, 62))
        x += w

    # the cinema canopy, because it is the one thing that oversails the pavement
    cx = 0.0
    for u in units:
        if u["id"] == "tivoli":
            sh.rect(*P(cx, 3.9), *P(cx + u["width_m"], 4.3), col=(40, 38, 38),
                    wid=2, fill=(70, 62, 58))
            for k in range(24):
                lx, ly = P(cx + 0.4 + k * (u["width_m"] - 0.8) / 23.0, 3.86)
                on = (k % 8) != 3
                sh.circle(lx, ly, 3, col=WARM if on else (70, 66, 66), wid=1,
                          fill=WARM if on else (70, 66, 66))
            sh.text(*P(cx + 0.4, 4.60),
                    "CANOPY: 24 LAMPS, 19 WORKING", size=9, col=WARM)
            break
        cx += u["width_m"]

    # the two objects that connect this street to Mickey's Cars
    tel_x = 0.0
    for u in units:
        if u["id"] == "coleys":
            break
        tel_x += u["width_m"]
    tx, ty = P(tel_x - 0.35, 1.4)
    sh.rect(tx - 5, ty - 9, tx + 5, ty + 9, col=NEON, wid=2, fill=(80, 52, 46))
    sh.line(tx, ty + 9, tx, P(tel_x - 0.35, 0.0)[1], col=NEON, wid=1,
            dash="4,3")
    lx, ly = P(tel_x + 1.9, 8.6)
    sh.line(tx, ty - 9, lx, ly + 6, col=NEON, wid=1, dash="4,3")
    sh.text(lx, ly, "THE CAB TELEPHONE", size=11, bold=True, col=NEON,
            anchor="middle")
    sh.text(lx, ly + 15, "a steel hood, no dial, one office",
            size=9, col=NEON, anchor="middle")
    sh.text(lx, ly + 28, "the atlas's own taxi landline notice, made an object",
            size=9, col=NEON, anchor="middle")

    # the queue, as a row of figures on the wet
    qx = 0.0
    for u in units:
        if u["id"] == "coleys":
            for k in range(11):
                fx, fy = P(qx + 0.4 + k * 0.62, -0.35)
                sh.rect(fx - 4, fy - 26, fx + 4, fy, col=(24, 24, 28), wid=0,
                        fill=(24, 24, 28))
            sh.text(*P(qx + 3.0, -1.95),
                    "THE CHIP SHOP QUEUE AT 22.52, ELEVEN DEEP, IN THE WET",
                    size=10, col=(238, 232, 220), bold=True, anchor="middle")
            break
        qx += u["width_m"]

    para(sh, 44, 150,
         f"LIT UNITS {lit_units} OF {len(units)}. Take the brewery signs out of a 1990 "
         f"nightlife street and half its illuminated signage goes with them. What is "
         f"left is FOOD AND FILM: fluorescent behind shop glass, a cinema canopy, one "
         f"small neon, sodium overhead. That is a better lighting brief than a row of "
         f"internally lit drink signs, not a worse one, and it is the whole argument "
         f"of this sheet.", width=138, size=11, bold=True)
    return sh.save()


def night_clock(D):
    """A VERTICAL timeline, not a horizontal one, and the reason is a reading.

    The first draft spaced twelve events linearly in time from 19.30 to 03.00.
    Eight of the twelve fall between 22.30 and 00.15, so the labels piled on
    top of each other and four were unreadable. THE CLUSTERING IS THE POINT OF
    THE DESIGN, so the drawing must not be the thing that hides it: the events
    are listed down the page at even spacing, with the real gap in minutes
    printed beside each one so the crush is a number instead of a collision.
    """
    ev = D["the_clock"]["events"]
    day = D["day_before_night"]["events"]
    sh = Sheet("parade-night-clock", 1660, 1200, "", "")
    frame(sh, "THE PARADE'S CLOCK",
          "a service yard by day, a street of discharges by night",
          "Times are AUTHORED and hang on two sourced facts and one studio "
          "ruling, all three named on the sheet.",
          source="data/parade-night.json",
          script="author/draw_parade_night.py")

    def tmin(t):
        h, m = t.split(":")
        h = int(h)
        if h < 12:
            h += 24
        return h * 60 + int(m)

    big = {"22:30", "22:50", "23:30"}

    # THE DAY COLUMN. The atlas row's fifth clause, daytime cleaning and
    # deliveries preceding the night queues, is one of the three that survive
    # D17 and it had no material until this sheet.
    dx = 90
    dy = 178
    drail = dx + 56
    sh.text(dx, dy - 40, "THE DAY BEFORE IT", size=15, bold=True, col=GREEN)
    sh.text(dx, dy - 22,
            "propped doors, crates on the pavement, and nobody queueing",
            size=10, col=MID)
    sh.line(drail, dy - 8, drail, dy + len(day) * 76 + 4, col=GREEN, wid=2)
    for i, (t, what, where) in enumerate(day):
        yy = dy + i * 76
        sh.circle(drail, yy, 5, col=GREEN, wid=2, fill=PAPER)
        sh.text(dx + 44, yy + 5, t, size=12, bold=True, col=GREEN, anchor="end")
        para(sh, drail + 16, yy + 5, what, width=52, size=10, col=INK, lead=14)
        sh.text(drail + 16, yy + 62, where, size=9, col=FAINT)

    x = 700
    y = 178
    rail = x + 66
    sh.text(x, y - 40, "AND THE NIGHT", size=15, bold=True, col=RED)
    sh.text(x, y - 22, "three discharges, and everything else absorbs them",
            size=10, col=MID)
    sh.line(rail, y - 8, rail, y + len(ev) * 62 + 4, col=INK, wid=2)
    for i, (t, what, where) in enumerate(ev):
        yy = y + i * 62
        gap = tmin(t) - tmin(ev[i - 1][0]) if i else 0
        col = RED if t in big else INK
        sh.circle(rail, yy, 8 if t in big else 5, col=col, wid=3 if t in big else 2,
                  fill=PAPER)
        sh.text(x + 50, yy + 5, t, size=14 if t in big else 12, bold=True,
                col=col, anchor="end")
        if i:
            sh.text(x + 50, yy - 22, f"+{gap} min", size=9, col=FAINT,
                    anchor="end")
        para(sh, rail + 18, yy + 5, what, width=62,
             size=12 if t in big else 11, col=col, bold=t in big, lead=16)
        sh.text(1590, yy + 5, where, size=10, col=MID, anchor="end")

    y2 = 850
    sh.text(90, y2, "WHAT THE CLOCK IS BUILT ON", size=13, bold=True)
    y2 = para(sh, 90, y2 + 24,
              "SOURCED: bus deregulation from 26 October 1986 thinned evening and "
              "Sunday services across the country, sourced by this project on "
              "2026-09-08. SOURCED: the first British multiplex opened on 23 "
              "November 1985 with ten screens and took over a million admissions in "
              "its first year, and admissions had bottomed at 54 million in 1984 "
              "across 1,246 screens, which is what the Tivoli is shabby because of. "
              "SOURCED: the Entertainments (Increased Penalties) Act 1990 received "
              "Royal Assent on 13 July 1990 and raised the penalties for unlicensed "
              "parties, which is the period's own nightlife story and has nothing to "
              "do with drink. RULED: the studio decided on 2026-09-09 that the last "
              "bus out of Meridian goes about half past ten, because the walk home "
              "through a dark port town is where the game happens.",
              width=68, size=11)
    y2 = 990
    sh.text(700, y2, "AND THIS IS THE CONSEQUENCE", size=13, bold=True, col=RED)
    para(sh, 700, y2 + 24,
         "After 22.30 every person on this street either walks home through a dark "
         "port town or finds a telephone. There are exactly two telephones on the "
         "Parade: the public box, which the project already owns as "
         "E3_telephone_kiosk, and a direct line in a steel hood screwed to the wall "
         "between the cinema and the chip shop, with no dial on it, which rings one "
         "office. THE ATLAS PUT A TAXI LANDLINE NOTICE ON THIS STREET BEFORE ANYBODY "
         "PROPOSED A CAB OFFICE.", width=100, size=11, col=RED)
    return sh.save()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    D = json.load(open(DATA))
    made = [night_elevation(D), night_clock(D)]
    print(f"paradeDrawingsWritten={len(made)} into {OUT.relative_to(REPO)}")
    for m in made:
        print("  " + m)
    print("generationRunsStarted=0 imagesGenerated=0 "
          "(nothing measured: the run is the resident's and this commission "
          "may not start one)")


if __name__ == "__main__":
    main()
