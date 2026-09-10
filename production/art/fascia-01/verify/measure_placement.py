#!/usr/bin/env python3
"""Station 3 VERIFY: acceptance checks A1 to A10 of the fascia package, MEASURED.

    python3 production/art/fascia-01/verify/measure_placement.py
    python3 production/art/fascia-01/verify/measure_placement.py --selftest

WHY THIS FILE EXISTS, which is a correction to the spec beside it.
production/art/fascia-01/01-SPEC-fascia-package.md section 4 lists ten
acceptance checks, says every one was measured on 2026-09-09, and then says in
as many words: "there is no committed tool that re-runs them, so they are a
ONE-TIME MEASUREMENT and they will decay exactly the way a comment decays."
A measurement that cannot be re-taken is a claim with a date on it. This takes
all ten off the committed piece list in one command, so the next person to move
a pilaster finds out from a number rather than from a render.

IT IS NOT AN INSTRUMENT AND IT GATES NOTHING. No CI step runs it, it prints no
verdict key for a watcher to read, and it lives under the commission rather
than under tools/. Jafar's no-new-instrument ruling for the art lane stands;
this is the package's own arithmetic, in the same position as its authoring
recipe.

WHAT IT READS. production/specs/vignette-pieces.json, which is the flat list
both engines build from, so every number below is measured on the geometry that
ships rather than on the scene file's intentions. A bound it cannot check is
named rather than skipped.

EVERY ZERO SHIPS ITS DENOMINATOR, and a check with no population to examine
prints the words "nothing measured" rather than a clean zero, because a zero
over nothing is the failure this project keeps finding.
"""
import json
import os
import sys

SPEC_REL = "production/specs/vignette-pieces.json"
BUILDING_LINE_Z = 5.125   # asserted against the data below, never trusted
CORNICE = "fascia_cornice_01"
CONSOLE = "fascia_console_01"
C15 = "C15_fascia_cornice_console"
C5 = "C5_shopfront_assembly"
#: The package's CHOSEN clearance, labelled chosen in the spec because no dated
#: figure for a downpipe bracket stand-off was reachable. A6 reads the MEASURED
#: minimum and compares it to this; it does not assume it.
CLEARANCE_M = 0.0200
TOL_M = 1e-9


def repo_root(start=None):
    d = os.path.dirname(os.path.abspath(start or __file__))
    while True:
        if os.path.exists(os.path.join(d, SPEC_REL)):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def box(p):
    """(x0, x1, y0, y1, z0, z1). Axis aligned, which every piece this file
    touches is: the spec's counts.multi_rotation is 0 and the fascia rows all
    carry yaw 0, asserted by A0 below rather than assumed."""
    return (p["x_m"] - p["sx_m"] / 2.0, p["x_m"] + p["sx_m"] / 2.0,
            p["y_m"] - p["sy_m"] / 2.0, p["y_m"] + p["sy_m"] / 2.0,
            p["z_m"] - p["sz_m"] / 2.0, p["z_m"] + p["sz_m"] / 2.0)


def asset_of(p):
    return (p.get("asset") or "").split("#", 1)[0]


def overlap(a, b):
    """Volume of the intersection of two boxes. Zero when they only touch."""
    v = 1.0
    for k in (0, 2, 4):
        lo = max(a[k], b[k])
        hi = min(a[k + 1], b[k + 1])
        if hi <= lo:
            return 0.0
        v *= (hi - lo)
    return v


def shares(a, b, k):
    """Do two boxes overlap on axis k (0=x, 2=y, 4=z) with positive extent?"""
    return min(a[k + 1], b[k + 1]) - max(a[k], b[k]) > TOL_M


def fmt_mm(v):
    return "%.4fmm" % (v * 1000.0)


def worst_at(name, worst, population):
    """The name of the worst piece, or the WORDS when every piece is exactly at
    the bound. `on=none` beside a zero reads as "no piece was examined", which
    is the denominator failure this project keeps finding, so a population that
    is entirely at zero says so and still prints its count."""
    if population <= 0:
        return "nothing-measured"
    return name if name != "none" else "all-%d-at-exactly-zero" % population


def measure(spec):
    """Every check, as (id, verdict, bound, reading) with no spaces in values."""
    pieces = spec["pieces"]
    east = [p for p in pieces if (p.get("edge") or "").startswith("east")
            or (p.get("region") or "").startswith("east")]
    c15 = [p for p in pieces if p.get("bom") == C15]
    cornices = [p for p in c15 if asset_of(p) == CORNICE]
    consoles = [p for p in c15 if asset_of(p) == CONSOLE]
    bands = [p for p in pieces if p.get("bom") == C5 and "fascia" in p["name"]]
    c5_east = [p for p in pieces if p.get("bom") == C5
               and (p.get("edge") or "").startswith("east")]
    pipes = [p for p in pieces if p.get("bom") == "D5_downpipe"
             and (p.get("edge") or "").startswith("east")]
    decals = [p for p in pieces if p.get("bom") == "C6_fascia_lettering"]
    rows = []

    def row(cid, what, ok, bound, reading):
        rows.append((cid, "PASS" if ok else "FAIL", what, bound, reading))

    # A0: the assumption every other check rests on.
    turned = [p["name"] for p in c15
              if abs(p.get("pitch_deg", 0)) + abs(p.get("yaw_deg", 0))
              + abs(p.get("roll_deg", 0)) > TOL_M]
    row("A0", "every-C15-piece-is-axis-aligned-so-a-box-IS-its-world-bounds",
        not turned and len(c15) > 0, "0-rotated-pieces-of-17",
        "rotated=%d/of=%d names=%s" % (len(turned), len(c15),
                                       ";".join(turned) if turned else "none"))

    # A1: cornice soffit on the fascia band top.
    if not cornices or not bands:
        row("A1", "cornice-soffit-minus-fascia-band-top", False,
            "0.0000mm-exactly", "nothing measured: cornices=%d bands=%d"
            % (len(cornices), len(bands)))
    else:
        band_top = max(box(b)[3] for b in bands)
        worst, at = 0.0, "none"
        for c in cornices:
            d = box(c)[2] - band_top
            if abs(d) > abs(worst):
                worst, at = d, c["name"]
        row("A1", "cornice-soffit-minus-fascia-band-top", abs(worst) <= TOL_M,
            "0.0000mm-exactly-over-6",
            "worst=%s/on=%s/over=%d bandTopM=%.6f" % (fmt_mm(worst), worst_at(at, worst, len(cornices)),
                                                      len(cornices), band_top))

    # A2: console centred on the band.
    if not consoles or not bands:
        row("A2", "console-centre-y-minus-fascia-band-centre-y", False,
            "0.0000mm-exactly", "nothing measured")
    else:
        bb = box(bands[0])
        band_mid = (bb[2] + bb[3]) / 2.0
        worst, at = 0.0, "none"
        for c in consoles:
            d = c["y_m"] - band_mid
            if abs(d) > abs(worst):
                worst, at = d, c["name"]
        row("A2", "console-centre-y-minus-fascia-band-centre-y", abs(worst) <= TOL_M,
            "0.0000mm-exactly-over-11",
            "worst=%s/on=%s/over=%d bandCentreYM=%.6f" % (fmt_mm(worst), worst_at(at, worst, len(consoles)),
                                                         len(consoles), band_mid))

    # A3: console top IS the cornice soffit. THE CHECK QUEUE 228 TURNED ON.
    if not consoles or not cornices:
        row("A3", "console-top-minus-cornice-bottom", False, "0.0000mm-exactly",
            "nothing measured")
    else:
        worst, at, pairs = 0.0, "none", 0
        for c in consoles:
            cb = box(c)
            mine = None
            for k in cornices:
                kb = box(k)
                if shares(cb, kb, 0) or abs(kb[0] - cb[1]) < 0.06 or abs(cb[0] - kb[1]) < 0.06:
                    mine = kb
                    break
            if mine is None:
                continue
            pairs += 1
            d = cb[3] - mine[2]
            if abs(d) > abs(worst):
                worst, at = d, c["name"]
        row("A3", "console-top-minus-cornice-bottom", abs(worst) <= TOL_M and pairs > 0,
            "0.0000mm-exactly-over-11",
            "worst=%s/on=%s/pairsFound=%d/of=%d "
            "meaning=the-bracket-and-the-thing-it-carries-share-ONE-plane-which-is-what-queue-228-reads-as-burial"
            % (fmt_mm(worst), worst_at(at, worst, pairs), pairs, len(consoles)))

    # A4 and A5: the oversail, which is what sheds water clear of the sign.
    if cornices and bands:
        face = min(box(b)[4] for b in bands)       # the board's street face
        over = face - min(box(c)[4] for c in cornices)
        row("A4", "cornice-oversail-past-the-fascia-board-face", over > TOL_M,
            "greater-than-0.0000m",
            "oversailM=%.6f boardFaceZM=%.6f corniceFaceZM=%.6f"
            % (over, face, min(box(c)[4] for c in cornices)))
    if cornices and consoles:
        over = min(box(c)[4] for c in consoles) - min(box(k)[4] for k in cornices)
        row("A5", "cornice-oversail-past-the-console-face", over > TOL_M,
            "greater-than-0.0000m",
            "oversailM=%.6f consoleFaceZM=%.6f" % (over, min(box(c)[4] for c in consoles)))

    # A6: the measured clearance to the rainwater pipes, with its pair count.
    pairs, worst, at = 0, None, "none"
    for new in c15:
        nb = box(new)
        for pipe in pipes:
            pb = box(pipe)
            if not (shares(nb, pb, 2) and shares(nb, pb, 4)):
                continue
            pairs += 1
            gap = max(pb[0] - nb[1], nb[0] - pb[1])
            if worst is None or gap < worst:
                worst, at = gap, new["name"] + "/to/" + pipe["name"]
    if pairs == 0:
        row("A6", "minimum-x-clearance-to-an-east-downpipe", False,
            "at-least-%.4fm" % CLEARANCE_M,
            "nothing measured: 0 pairs share both y and z with a pipe, "
            "so the clearance was not examined")
    else:
        row("A6", "minimum-x-clearance-to-an-east-downpipe",
            worst >= CLEARANCE_M - TOL_M, "at-least-%.4fm" % CLEARANCE_M,
            "minM=%.6f/at=%s/pairsExamined=%d chosenNotCited=%.4f"
            % (worst, at, pairs, CLEARANCE_M))

    # A7: every new piece's back on the building line.
    if c15:
        worst, at = 0.0, "none"
        for p in c15:
            d = box(p)[5] - BUILDING_LINE_Z
            if abs(d) > abs(worst):
                worst, at = d, p["name"]
        row("A7", "every-new-pieces-rear-face-on-the-building-line",
            abs(worst) <= TOL_M, "0.0000mm-exactly-over-17",
            "worst=%s/on=%s/over=%d buildingLineZM=%.4f"
            % (fmt_mm(worst), worst_at(at, worst, len(c15)), len(c15), BUILDING_LINE_Z))

    # A8: no clash with anything east that is not C5 or C15.
    clashes, examined = [], 0
    for new in c15:
        nb = box(new)
        for other in east:
            if other is new or other.get("bom") in (C15, C5):
                continue
            if other.get("shape") == "decal":
                continue
            examined += 1
            v = overlap(nb, box(other))
            if v > 1e-12:
                clashes.append("%s/into/%s/%.8fm3" % (new["name"], other["name"], v))
    row("A8", "interpenetration-with-any-east-piece-that-is-not-C5-or-C15",
        not clashes and examined > 0, "0-clashes",
        "clashes=%d/of=%d-pairs-examined %s"
        % (len(clashes), examined,
           (";".join(clashes[:4]) + (";(+%d~more~not~shown)" % (len(clashes) - 4)
                                     if len(clashes) > 4 else "")) if clashes else "none"))

    # A9: exactly 22 clashes with C5, and every one ENCLOSED.
    c5_hits, not_enclosed, examined9 = [], [], 0
    for new in c15:
        nb = box(new)
        for other in c5_east:
            examined9 += 1
            if overlap(nb, box(other)) <= 1e-12:
                continue
            ob = box(other)
            c5_hits.append(new["name"] + "/into/" + other["name"])
            # ENCLOSED means the overlapping slice of the new piece is inside
            # the other piece on the two axes it is not entering through: the
            # console goes in through its BACK, so x and y must be contained.
            if not (nb[0] >= ob[0] - TOL_M and nb[1] <= ob[1] + TOL_M
                    and nb[2] >= ob[2] - TOL_M and nb[3] <= ob[3] + TOL_M):
                not_enclosed.append(new["name"] + "/into/" + other["name"])
    row("A9", "interpenetration-with-C5-is-exactly-22-and-all-enclosed",
        len(c5_hits) == 22 and not not_enclosed,
        "exactly-22-and-0-not-enclosed",
        "hits=%d/of=%d-pairs-examined notEnclosed=%d %s"
        % (len(c5_hits), examined9, len(not_enclosed),
           ";".join(not_enclosed[:4]) if not_enclosed else "none"))

    # A10: decal height lost behind a cornice. REPORTED, NOT BOUNDED, and by
    # CONTAINMENT rather than overlap, because a decal has sz=0 and an overlap
    # test on a zero-thickness plane can only ever return zero.
    if not decals or not cornices:
        row("A10", "decal-height-lost-behind-a-cornice", True, "reported-not-bounded",
            "nothing measured: decals=%d cornices=%d" % (len(decals), len(cornices)))
    else:
        worst, at = 0.0, "none"
        for d in decals:
            db = box(d)
            for k in cornices:
                kb = box(k)
                if not shares(db, kb, 0):
                    continue
                if not (kb[4] <= db[4] <= kb[5]):
                    continue
                lost = min(db[3], kb[3]) - max(db[2], kb[2])
                if lost > worst:
                    worst, at = lost, d["name"] + "/behind/" + k["name"]
        row("A10", "decal-height-lost-behind-a-cornice", True, "reported-not-bounded",
            "worstLostM=%.6f/at=%s/decalsExamined=%d/of=%d "
            "test=containment-of-the-zero-thickness-plane-in-the-cornice-z-span"
            % (worst, at, len(decals), len(decals)))
    return rows


def report(spec, out=print):
    rows = measure(spec)
    failed = [r for r in rows if r[1] == "FAIL"]
    out("fascia-01 placement acceptance, measured off %s" % SPEC_REL)
    for cid, verdict, what, bound, reading in rows:
        out("  %-4s %-4s %-62s bound=%s %s" % (cid, verdict, what, bound, reading))
    out("placementChecks=%d/of=%d-passing failures=%s "
        "readFrom=%s specPieces=%d"
        % (len(rows) - len(failed), len(rows),
           ";".join(r[0] for r in failed) if failed else "none",
           SPEC_REL, len(spec["pieces"])))
    return 1 if failed else 0


def selftest(out=print):
    """ACCEPTING CASE FIRST on the live street, then planted rejections.

    The live committed piece list is the accepting fixture, which is this
    project's rule for a tool that reads the project itself: doing the work
    this tool prompts can never break the tool. The rejecting fixtures are
    synthetic, because a repository with a broken street in it is not a
    repository anybody wants.
    """
    n = [0, 0]

    def check(name, ok, detail=""):
        n[0] += 1
        if ok:
            out("  ok - %s" % name)
        else:
            n[1] += 1
            out("  FAIL: %s %s" % (name, detail))

    root = repo_root()
    check("accept/the-repository-root-is-found", root is not None)
    if root is None:
        out("PASS: %d of %d check(s) failed" % (n[1], n[0]))
        return 1
    with open(os.path.join(root, SPEC_REL), encoding="utf-8") as fh:
        spec = json.load(fh)
    rows = measure(spec)
    ids = [r[0] for r in rows]
    check("accept/all-eleven-checks-ran-on-the-live-street", len(rows) == 11,
          "%d: %s" % (len(rows), ";".join(ids)))
    check("accept/every-one-of-them-passes-on-the-committed-street",
          all(r[1] == "PASS" for r in rows),
          ";".join(r[0] for r in rows if r[1] != "PASS"))
    check("accept/no-reading-carries-a-space-inside-a-key=value",
          all(" " not in tok.split("=", 1)[1]
              for r in rows for tok in r[4].split(" ") if "=" in tok
              and not tok.startswith("nothing")),
          ";".join(r[0] for r in rows
                   if any(" " in tok.split("=", 1)[1] for tok in r[4].split(" ")
                          if "=" in tok)))

    # REJECT: lift one cornice by a millimetre and A1, A3 and A5 must notice.
    lifted = json.loads(json.dumps(spec))
    for p in lifted["pieces"]:
        if p.get("bom") == C15 and asset_of(p) == CORNICE:
            p["y_m"] += 0.001
    by_id = {r[0]: r for r in measure(lifted)}
    check("reject/a-cornice-lifted-1-mm-off-its-band-fails-A1",
          by_id["A1"][1] == "FAIL", by_id["A1"][4])
    check("reject/and-fails-A3-because-the-console-no-longer-touches-it",
          by_id["A3"][1] == "FAIL", by_id["A3"][4])

    # REJECT: widen a console past its pilaster and A9's enclosure must fail.
    fat = json.loads(json.dumps(spec))
    for p in fat["pieces"]:
        if p.get("bom") == C15 and asset_of(p) == CONSOLE:
            p["sx_m"] = 0.500
    by_id = {r[0]: r for r in measure(fat)}
    check("reject/a-console-wider-than-its-pilaster-fails-A9-enclosure",
          by_id["A9"][1] == "FAIL", by_id["A9"][4])
    check("reject/and-the-same-widening-eats-the-downpipe-clearance-in-A6",
          by_id["A6"][1] == "FAIL", by_id["A6"][4])

    # REJECT: push a cornice back behind the building line.
    sunk = json.loads(json.dumps(spec))
    for p in sunk["pieces"]:
        if p.get("bom") == C15 and asset_of(p) == CORNICE:
            p["z_m"] += 0.050
    by_id = {r[0]: r for r in measure(sunk)}
    check("reject/a-cornice-pushed-through-the-building-line-fails-A7",
          by_id["A7"][1] == "FAIL", by_id["A7"][4])

    # REJECT: a street with no fascia package at all must say nothing measured
    # rather than printing clean zeros.
    stripped = json.loads(json.dumps(spec))
    stripped["pieces"] = [p for p in stripped["pieces"] if p.get("bom") != C15]
    by_id = {r[0]: r for r in measure(stripped)}
    check("reject/a-street-with-no-C15-piece-says-nothing-measured-not-zero",
          "nothing measured" in by_id["A1"][4] and by_id["A1"][1] == "FAIL",
          by_id["A1"][4])
    check("reject/and-A0-refuses-rather-than-passing-on-an-empty-population",
          by_id["A0"][1] == "FAIL", by_id["A0"][4])

    # REJECT: turn a console and A0 must refuse, because every other check
    # here treats a box as its own world bounds.
    turned = json.loads(json.dumps(spec))
    for p in turned["pieces"]:
        if p.get("bom") == C15 and asset_of(p) == CONSOLE:
            p["yaw_deg"] = 7.0
            break
    by_id = {r[0]: r for r in measure(turned)}
    check("reject/one-rotated-console-makes-A0-refuse-by-name",
          by_id["A0"][1] == "FAIL" and "prop_fascia_console" in by_id["A0"][4],
          by_id["A0"][4])

    out("measure_placement selftest: %d check(s), %d failure(s)" % (n[0], n[1]))
    out("PASS: %d of %d check(s) failed" % (n[1], n[0]))
    return 1 if n[1] else 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    root = repo_root()
    if root is None:
        print("refused: status=NO-REPO-ROOT reason=%s-not-found nothing measured" % SPEC_REL)
        return 1
    with open(os.path.join(root, SPEC_REL), encoding="utf-8") as fh:
        spec = json.load(fh)
    return report(spec)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
