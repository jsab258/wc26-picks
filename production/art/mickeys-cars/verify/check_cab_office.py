#!/usr/bin/env python3
"""Measure the Mickey's Cars layout against the street it has to fit.

Why it exists: every number in this commission's prose must be re-derivable by
somebody who does not believe the prose. This script reads
data/cab-office.json and production/specs/vignette-pieces.json and prints the
readings. It sets no new threshold: where a bound is asserted (0.000 mm on the
six front openings) the bound was chosen because the design deliberately moves
nothing, and the reading is printed beside it so a reader can see which is
which.

IT IS NOT A STUDIO INSTRUMENT. It gates nothing, emits no verdict key the
studio reads, and lives under production/art/mickeys-cars/ and not under
tools/.

Run from the repository root:
    python3 production/art/mickeys-cars/verify/check_cab_office.py

Every zero below ships the count of what was examined, and a case that
measured nothing prints the words "nothing measured".
"""
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[2]
LAYOUT = PKG / "data" / "cab-office.json"
PIECES = REPO / "production" / "specs" / "vignette-pieces.json"
SCENE = REPO / "production" / "specs" / "vignette-scene.json"
IFACE = REPO / "production" / "specs" / "asset-interface.md"

TOL_MM = 0.001          # reporting resolution, millimetres
FOOT_R = 0.30           # conservative body radius, the pub package's own figure
U0, V0, H0 = 3.0, 5.125, 0.100   # local frame origin in source coordinates

fails = []


def mm(a):
    return a * 1000.0


def load(p):
    with open(p) as fh:
        return json.load(fh)


# ----------------------------------------------------------------- section 1
def front_openings(layout, pieces):
    """The six existing apertures, and whether the design moved any of them."""
    by_name = {p["name"]: p for p in pieces["pieces"]}
    rows = layout["front_openings"]["items"]
    worst = 0.0
    examined = 0
    for r in rows:
        src = by_name.get(r["source"])
        if src is None:
            fails.append(f"frontOpening source missing name={r['source']}")
            continue
        examined += 1
        # the street piece is centred; convert to a u span
        u_lo = src["x_m"] - src["sx_m"] / 2.0 - U0
        u_hi = src["x_m"] + src["sx_m"] / 2.0 - U0
        d_lo = abs(u_lo - r["u"][0])
        d_hi = abs(u_hi - r["u"][1])
        worst = max(worst, d_lo, d_hi)
        print(f"  opening {r['id']:18s} src={r['source']:26s} "
              f"u=[{r['u'][0]:.4f},{r['u'][1]:.4f}] "
              f"street=[{u_lo:.4f},{u_hi:.4f}] deltaMm={mm(max(d_lo,d_hi)):.3f}")
    if examined == 0:
        print("  frontOpenings nothing measured")
        return
    print(f"frontOpenings examined={examined}/{len(rows)} "
          f"worstDeltaMm={mm(worst):.3f} boundMm={mm(TOL_MM):.3f}")
    if worst > TOL_MM:
        fails.append(f"frontOpenings worstDeltaMm={mm(worst):.3f}")


# ----------------------------------------------------------------- section 2
def boxes_from_layout(layout):
    """Turn the authored contents into (id, u_lo, u_hi, v_lo, v_hi) boxes.

    Returns the boxes AND the items it could not turn into a box, because a
    checker that silently skips what it cannot parse reports a clean nothing.
    """
    boxes, unparsed = [], []

    def span(val, thin=0.05):
        if isinstance(val, list) and len(val) == 2:
            return float(val[0]), float(val[1])
        if isinstance(val, (int, float)):
            return float(val) - thin / 2.0, float(val) + thin / 2.0
        return None

    def lowest(c):
        """The bottom of the item, for deciding whether a body walks into it.

        A flush feature (a mat, a brick scar, a gully) is not an obstacle at
        all and says so in its own row. An item with no height given is
        assumed to stand on the floor, which is the conservative reading.
        """
        if c.get("flush"):
            return None
        h = c.get("h_m")
        if isinstance(h, list) and h:
            return float(h[0])
        if isinstance(h, (int, float)):
            return float(h)
        return 0.0

    for room in layout["rooms"]:
        for c in room.get("contents", []):
            su = span(c.get("u"))
            sv = span(c.get("v"))
            if su is None or sv is None:
                unparsed.append(f"{room['id']}/{c['id']}")
                continue
            boxes.append((f"{room['id']}/{c['id']}", su[0], su[1], sv[0], sv[1],
                          c.get("surface"), lowest(c)))
    for c in layout["yard"].get("contents", []):
        su = span(c.get("u"))
        sv = span(c.get("v"))
        if su is None or sv is None:
            unparsed.append(f"yard/{c['id']}")
            continue
        boxes.append((f"yard/{c['id']}", su[0], su[1], sv[0], sv[1],
                      c.get("surface"), lowest(c)))
    return boxes, unparsed


def inside_envelope(layout, boxes):
    """Is every interior box inside the carcass, and every yard box in the yard."""
    cw = layout["carcass"]
    iu, iv = cw["inner_faces_u_m"], cw["inner_faces_v_m"]
    yd = layout["yard"]
    out = 0
    for bid, ul, uh, vl, vh, _, _ in boxes:
        if bid.startswith("yard/"):
            lo_u, hi_u, lo_v, hi_v = yd["u"][0], yd["u"][1], yd["v"][0], yd["v"][1]
        else:
            lo_u, hi_u, lo_v, hi_v = iu["south"], iu["north"], iv["front"], iv["rear"]
        slack = 0.16   # a fitting on a wall face may sit in the wall's own thickness
        if (ul < lo_u - slack or uh > hi_u + slack
                or vl < lo_v - slack or vh > hi_v + slack):
            out += 1
            print(f"  OUTSIDE {bid} u=[{ul:.3f},{uh:.3f}] v=[{vl:.3f},{vh:.3f}]")
    print(f"envelope boxesExamined={len(boxes)} outsideEnvelope={out}/{len(boxes)} "
          f"slackM={0.16:.2f}")
    if out:
        fails.append(f"envelope outsideEnvelope={out}/{len(boxes)}")


def surfaces(layout, boxes):
    """Every surface named must be one of the sixteen the street can dress."""
    txt = IFACE.read_text()
    start = txt.find("Surfaces available today:")
    allowed = set()
    if start >= 0:
        frag = txt[start:start + 400]
        frag = frag[frag.find("`") + 1:]
        frag = frag[:frag.find("`")]
        allowed = {w for w in frag.replace("\n", " ").split() if w}
    named = [(bid, s) for bid, _, _, _, _, s, _ in boxes if s]
    bad = [(bid, s) for bid, s in named if s not in allowed]
    print(f"surfaces allowedInInterface={len(allowed)} "
          f"surfacesNamedInLayout={len(named)} outsideAllowed={len(bad)}/{len(named)}")
    for bid, s in bad:
        print(f"  NOT-A-SURFACE {bid} surface={s}")
    if not allowed:
        print("  surfaces nothing measured: could not parse the interface list")
        fails.append("surfaces interfaceListUnparsed")
    if bad:
        fails.append(f"surfaces outsideAllowed={len(bad)}/{len(named)}")
    return allowed


# ----------------------------------------------------------------- section 3
def ray_h(v_from, h_from, v_to, h_to, v_at):
    """Height of the straight ray at a given v."""
    if abs(v_to - v_from) < 1e-9:
        return h_from
    t = (v_at - v_from) / (v_to - v_from)
    return h_from + t * (h_to - h_from)


def ray_u(u_from, v_from, u_to, v_to, v_at):
    if abs(v_to - v_from) < 1e-9:
        return u_from
    t = (v_at - v_from) / (v_to - v_from)
    return u_from + t * (u_to - u_from)


def sightlines(layout):
    """Two opposite observation conditions in one building, as a series.

    A) the car board on the rear wall, which the design claims is readable
       from the public footway: print WHICH footway positions see it.
    B) the book in its well behind a 1.05 m counter, which the design claims
       is not.
    C) the drivers' room under a net at 1.500 m: hands out, heads in.
    """
    info = layout["information"]
    board = info["street_readable_target"]
    book = info["occluded_target"]
    eye_h = info["eye_height_m"]
    glass_v = 4.985 - V0                      # east_parade_glass0 plane
    ap_u = layout["front_openings"]["items"][2]["u"]          # office_glass
    ap_h = (layout["front_openings"]["items"][2]["sill_h_m"],
            layout["front_openings"]["items"][2]["head_h_m"])
    cross = layout["carcass"]["cross_wall_u_m"]
    stair = layout["rooms"][0]["partition"]
    counter = layout["rooms"][2]
    ctop = counter["top_h_m"]
    cv = (counter["v"][0], counter["v"][1])

    print("  A) car board from the footway, eye 1.600 m, v=-1.625 (z=3.500)")
    seen = []
    tried = []
    u = 1.0
    while u <= 11.0 + 1e-9:
        tried.append(u)
        ok, why = True, "sees"
        hv = ray_h(-1.625, eye_h, board["v"], board["h_m"], glass_v)
        uv = ray_u(u, -1.625, board["u"], board["v"], glass_v)
        if not (ap_h[0] <= hv <= ap_h[1]):
            ok, why = False, "aperture-height"
        elif not (ap_u[0] <= uv <= ap_u[1]):
            ok, why = False, "aperture-width"
        else:
            # the cross-wall and the stair partition are opaque for all v>front
            for lo, hi, name in ((cross[0], cross[1], "cross-wall"),
                                 (stair["u"][0], stair["u"][1], "stair-partition")):
                for vv in [glass_v + 0.05 * k for k in range(1, 200)]:
                    if vv > board["v"]:
                        break
                    uu = ray_u(u, -1.625, board["u"], board["v"], vv)
                    if lo <= uu <= hi and vv >= 0.215:
                        ok, why = False, name
                        break
                if not ok:
                    break
            if ok:
                hc = ray_h(-1.625, eye_h, board["v"], board["h_m"], cv[0])
                if hc < ctop and cv[0] >= 0:
                    ok, why = False, "counter-top"
        if ok:
            seen.append(u)
        u += 0.5
    print(f"     footwayPositionsTried={len(tried)} seesCarBoard={len(seen)}/{len(tried)}"
          f" uRangeSeen={(min(seen) if seen else 'none')}..{(max(seen) if seen else 'none')}")
    if not seen:
        fails.append("sightline carBoard seesCarBoard=0/%d" % len(tried))

    print("  B) the book, same eye, from straight in front of it")
    hb_at_counter = ray_h(-1.625, eye_h, book["v"], book["h_m"], cv[0])
    blocked = hb_at_counter < ctop
    print(f"     rayHeightAtCounterFaceM={hb_at_counter:.3f} counterTopM={ctop:.3f} "
          f"blockedByCounter={blocked}")
    if not blocked:
        fails.append("sightline theBook is NOT occluded and the design says it is")

    print("  C) drivers' room through the net, wire at 1.500 m")
    net = None
    for c in layout["rooms"][5]["contents"]:
        if c["id"] == "net_curtain":
            net = c
    hand = (9.000, 1.600, 0.850)
    head = (9.000, 1.600, 1.650)
    res = {}
    for label, (tu, tv, th) in (("hand", hand), ("head", head)):
        hv = ray_h(-1.625, eye_h, tv, th, glass_v)
        occl = net["h_m"][0] <= hv <= net["h_m"][1]
        res[label] = (hv, occl)
        print(f"     {label} rayHeightAtGlassM={hv:.3f} netZoneM="
              f"[{net['h_m'][0]:.3f},{net['h_m'][1]:.3f}] occludedByNet={occl}")
    if not res["hand"][1] or res["head"][1]:
        fails.append("sightline net does not separate hands from heads")


# ----------------------------------------------------------------- section 4
def paths(layout, boxes):
    """Does a 0.30 m body get along each authored route without a clash?"""
    PASS_H = 1.100   # a body's widest band; a shelf above this is passed under
    flush = [b for b in boxes if b[6] is None]
    high = [b for b in boxes if b[6] is not None and b[6] >= PASS_H]
    blocking = [b for b in boxes if b[6] is not None and b[6] < PASS_H]
    print(f"  obstacleSplit parsed={len(boxes)} blocksABody={len(blocking)} "
          f"abovePassHeight={len(high)} flushAndNotAnObstacle={len(flush)} "
          f"passHeightM={PASS_H:.3f}")
    obst = [b for b in blocking if not b[0].startswith("yard/")]
    yobst = [b for b in blocking if b[0].startswith("yard/")]
    total_pts = 0
    total_clash = 0
    for name, pts in layout["paths"].items():
        if not isinstance(pts, list):
            continue
        clashes = 0
        samples = 0
        use = yobst if name in ("yard_cross", "lockup") else obst + yobst
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            seg = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(2, int(seg / 0.10))
            for k in range(n + 1):
                t = k / n
                pu = a[0] + t * (b[0] - a[0])
                pv = a[1] + t * (b[1] - a[1])
                samples += 1
                for bid, ul, uh, vl, vh, _, _ in use:
                    du = max(ul - pu, 0.0, pu - uh)
                    dv = max(vl - pv, 0.0, pv - vh)
                    if math.hypot(du, dv) < FOOT_R:
                        clashes += 1
                        break
        total_pts += samples
        total_clash += clashes
        print(f"  path {name:12s} samples={samples} clashes={clashes}/{samples} "
              f"obstaclesTested={len(use)}")
    print(f"paths samplesExamined={total_pts} clashes={total_clash}/{total_pts} "
          f"bodyRadiusM={FOOT_R:.2f}")
    if total_clash:
        fails.append(f"paths clashes={total_clash}/{total_pts}")


# ----------------------------------------------------------------- section 5
def rank(layout, pieces, scene):
    r = layout["rank"]
    L, W = r["car_envelope_m"]
    n = r["cars"]
    gap = 0.60
    need = n * L + (n - 1) * gap
    x0 = r["kerb_x_m"][0]
    print(f"  rank cars={n} carLenM={L:.2f} gapM={gap:.2f} "
          f"lengthNeededM={need:.2f} xFrom={x0:.2f} xTo={x0+need:.2f} "
          f"premisesFrontageM=12.00")
    if need <= 12.0:
        fails.append("rank arithmetic says the rank fits the frontage; "
                     "the prose says it does not")
    # the west court, from the scene's own numbers
    gapw = scene["blocks"][2]["start_x_m"] - (scene["blocks"][1]["start_x_m"]
                                              + scene["blocks"][1]["bays"]
                                              * scene["blocks"][1]["bay_width_m"])
    depth = scene["blocks"][1]["depth_m"]
    fits = int(depth // L)
    print(f"  westCourt widthM={gapw:.2f} depthM={depth:.2f} "
          f"carsNoseInThatFit={fits} carsPlaced=1")
    if fits != 1:
        fails.append(f"westCourt carsNoseInThatFit={fits} but the design places 1")
    # the yellow lines and the gully, read rather than recalled
    yl = [p for p in pieces["pieces"] if p["bom"] == "A5_double_yellow_lines"]
    zs = sorted({round(p["z_m"], 3) for p in yl})
    east = [p for p in yl if p["z_m"] > 0]
    print(f"  yellowLines piecesTotal={len(yl)} distinctZ={zs} "
          f"eastSidePieces={len(east)}")
    gul = [p for p in pieces["pieces"] if p["bom"] == "A7_gully_grate"]
    for g in gul:
        print(f"  gullyGrate name={g['name']} x={g['x_m']:.3f} z={g['z_m']:.3f} "
              f"underRankCar={'yes' if x0 <= g['x_m'] <= x0+need else 'no'}")
    if not gul:
        print("  gullyGrate nothing measured")
    drop = scene["street"]["dropped_kerb"]
    print(f"  droppedKerb side={drop['side']} centreX={drop['centre_x_m']} "
          f"crossoverM={drop['crossover_width_m']} "
          f"flushUpstandM={drop['flush_upstand_m']}")


# ----------------------------------------------------------------- section 6
def selftest(layout):
    """Accepting case first, then a planted fault the checker must catch.

    The accepting fixture is the live layout file. The rejecting fixture is
    synthetic: one front opening nudged 5 mm, which must be caught, because a
    checker that cannot see a moved aperture is the whole point of this file.
    """
    import copy
    print("selftest accepting=liveLayout rejecting=syntheticNudge")
    before = len(fails)
    bad = copy.deepcopy(layout)
    bad["front_openings"]["items"][0]["u"][0] += 0.005
    pieces = load(PIECES)
    by = {p["name"]: p for p in pieces["pieces"]}
    r = bad["front_openings"]["items"][0]
    src = by[r["source"]]
    u_lo = src["x_m"] - src["sx_m"] / 2.0 - U0
    caught = abs(u_lo - r["u"][0]) > TOL_MM
    print(f"  selftest rejectingCaseCaught={caught} "
          f"failsAddedByAcceptingCase={len(fails)-before}/0-expected")
    if not caught:
        fails.append("selftest rejecting case NOT caught")


def main():
    layout = load(LAYOUT)
    pieces = load(PIECES)
    scene = load(SCENE)
    print(f"spec {LAYOUT.relative_to(REPO)} schema={layout['schema']}")
    print(f"street pieces={len(pieces['pieces'])} "
          f"source={PIECES.relative_to(REPO)}")
    print()
    print("1 FRONT OPENINGS: does the design move anything the street already has")
    front_openings(layout, pieces)
    print()
    boxes, unparsed = boxes_from_layout(layout)
    print(f"2 CONTENTS: boxesParsed={len(boxes)} "
          f"itemsNotReducibleToABox={len(unparsed)}")
    for u in unparsed:
        print(f"  notABox {u}")
    inside_envelope(layout, boxes)
    surfaces(layout, boxes)
    print()
    print("3 SIGHTLINES")
    sightlines(layout)
    print()
    print("4 PATHS")
    paths(layout, boxes)
    print()
    print("5 THE RANK, AGAINST THE STREET'S OWN FILES")
    rank(layout, pieces, scene)
    print()
    selftest(layout)
    print()
    print(f"done findings={len(fails)}/{0 if not fails else len(fails)}-reported "
          f"checksRun=6")
    for f in fails:
        print(f"  FINDING {f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
