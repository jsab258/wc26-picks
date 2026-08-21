#!/usr/bin/env python3
"""WHAT IS ACTUALLY INSIDE EACH ANIMATION CLIP WE SHIP.

WHY THIS EXISTS. Jafar asked the question no number in this project
answers: "does it look real, or are we using the wrong animations?"
Every still we commit is a street at 1280x720 where a person is forty
pixels tall, so the honest answer was that nobody could tell.

THIS TOOL DOES NOT ANSWER THAT QUESTION. It answers a narrower one that
needs no picture and no judgement: is the file that landed in a slot a
plausible animation at all. The picture half is `ClipSheet`, which
renders every clip on a real body in Unity -- because Unity REBUILDS
the rig on import and this reader sees the file as shipped, which is
the same reason `body-proportions.py` refuses a model the build
measures happily. Where the two disagree the build wins.

WHAT IT CHECKS, AND WHY EACH ONE NEEDS NO INTERPRETATION.

  DUPLICATE CONTENT. Two slots holding the same bytes means at least
  one of them is playing the wrong animation, and no amount of looking
  at the filename can tell you which. This is a hash comparison: it is
  a fact, not a reading. `shoved` and `talk` were byte-identical when
  this was written, and `_picks.json` records that the picker matched
  two DIFFERENT harvest names exactly -- so the collision was made
  upstream, by the bulk harvester, and clip identity in that harvest
  cannot be trusted on the strength of a filename.

  A FROZEN ROOT. Mixamo puts `mixamorig:Hips` at the top of the
  hierarchy with no parent, so its own translation and rotation curves
  ARE the body's world motion; there is nowhere else for the motion to
  hide, and this tool checks that the hips are the root before saying
  so. A clip whose hips neither move nor turn across its whole length
  is a body animated from the waist up. That is legitimate for a
  gesture and impossible for a death or a walk start.

WHAT IT DELIBERATELY DOES NOT DO. It does not guess which animation a
clip "really is". Hip height is not comparable across clips -- a stand
up starts on the floor and legitimately reads 8cm -- and Euler ranges
inflate on wrap, so a walk can read 130 degrees of hip roll. Two
readings that looked like findings died on exactly those two facts
before this docstring was written. The series is printed; the verdict
belongs to the frame.

THE BOUNDS CAME OFF THE PRINTED SERIES (rule 2), not off a guess: run
with `--series` to see it again. Across 52 clips the frozen set sits at
under 1cm and under 2 degrees while the next clip up is several times
both, on both axes at once.
"""

import argparse
import collections
import hashlib
import importlib.util
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHARACTERS = os.path.join(HERE, "..", "ledger", "Assets", "Characters")
CLIP_FOLDERS = ("A", "B", "C", "D")

#: FBX ktime units in one second. A format constant, not a measurement.
KTIME_PER_SECOND = 46186158000.0

#: Animation curves run to thousands of keys, so the shared parser's
#: bind-pose-sized cap would skip every one unread and this tool would
#: report "no motion" for a clip full of it -- a zero with no
#: denominator, rule 3b. Big enough for the longest clip we hold
#: (`phone_box`, 1,166 keys) with room to spare.
CURVE_KEYS = 20000

#: A root is FROZEN when it neither moves nor turns. Both bounds are
#: read off the series below and both must be under for a clip to
#: count, because either alone has a legitimate case: a body can turn
#: on the spot without travelling, and can be carried without turning.
FROZEN_CM = 1.0
FROZEN_DEG = 2.0

#: SLOTS WHERE A FROZEN ROOT IS THE CORRECT ANSWER, not a finding.
#:
#: The frozen rule catches a clip animated from the waist up, and for a walk
#: that is decisive. For a body lying still on the floor it is the definition
#: of the clip, and on 21 August the ledger proved it the expensive way: the
#: second re-pick replaced `lie_still` — a corpse whose hips travelled 2.18m —
#: with `Laying Idle`, 0.36cm over 12.50s, which is exactly right. The debt
#: ROSE, 2 to 3, because the slot got BETTER, and the ratchet correctly
#: refused the commit.
#:
#: That is rule 5's ratchet: a guard that cannot tell a regression from an
#: improvement. The fix is not to raise the allowed number — that is the move
#: rule 2 forbids — it is to stop asking a question this slot cannot fail.
#:
#: DELIBERATELY ONE ENTRY. `lean` and `block_end` are NOT here: leaning and
#: ending a block are transitions a body performs, and their stillness is
#: arguable rather than definitional. `STAYS` in the picker is the wrong list
#: to reuse — it asks whether a body TRAVELS, and a talking clip stays put
#: while its hips still shift and turn. This asks whether the root moves at
#: all, which is a stricter and different question.
STILL_BY_DEFINITION = {"lie_still"}


def _load_parser():
    """The FBX reader from `body-proportions.py`, loaded by path because
    that filename is not an importable identifier."""
    spec = importlib.util.spec_from_file_location(
        "body_proportions", os.path.join(HERE, "body-proportions.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BP = _load_parser()


def _unit_scale(root):
    """Centimetres per unit, read from the file rather than assumed.
    Mixamo ships 1.0 and centimetres; reading a 140cm stride as metres
    would report a walk at 140 m/s, which is the kind of wrong that
    looks like a physics bug rather than a units bug."""
    gs = root.find("GlobalSettings")
    p70 = gs.find("Properties70") if gs is not None else None
    if p70 is None:
        return 1.0
    for p in p70.find_all("P"):
        if p.props and p.props[0] == "UnitScaleFactor":
            nums = [v for v in p.props if isinstance(v, float)]
            if nums:
                return nums[-1]
    return 1.0


def _index(root):
    """{object id: node}, plus the connection lists in both directions."""
    objs = root.find("Objects")
    by_id = {}
    if objs is not None:
        for c in objs.children:
            if c.props and isinstance(c.props[0], int):
                by_id[c.props[0]] = c
    out, into = {}, {}
    conns = root.find("Connections")
    if conns is not None:
        for c in conns.children:
            pr = c.props
            if len(pr) < 3:
                continue
            kind, child, parent = pr[0], pr[1], pr[2]
            prop = pr[3] if len(pr) > 3 else None
            out.setdefault(child, []).append((kind, parent, prop))
            into.setdefault(parent, []).append((kind, child, prop))
    return by_id, out, into


def _name(node):
    """The FBX name, which arrives NUL-separated from its class."""
    if len(node.props) > 1 and isinstance(node.props[1], str):
        return node.props[1].split("\x00")[0]
    return ""


def _keys(curve):
    """(ktimes, values) for one AnimationCurve, or None."""
    times, values = curve.find("KeyTime"), curve.find("KeyValueFloat")
    if times is None or values is None:
        return None
    t = times.props[0] if times.props else None
    v = values.props[0] if values.props else None
    if not t or not v:
        return None
    return t, v


def _channels(by_id, into, model_id, prop_name):
    """{axis: (ktimes, values)} for one animated property of one model."""
    found = {}
    for kind, child, prop in into.get(model_id, []):
        node = by_id.get(child)
        if node is None or node.name != "AnimationCurveNode" or prop != prop_name:
            continue
        for _k, curve_id, axis in into.get(child, []):
            curve = by_id.get(curve_id)
            if curve is None or curve.name != "AnimationCurve" or not axis:
                continue
            keys = _keys(curve)
            if keys is not None:
                found[axis[-1].upper()] = keys
    return found


def measure(path):
    """Everything this reader can say about one clip file."""
    root, _version = BP.parse_fbx(path, max_array=CURVE_KEYS)
    scale = _unit_scale(root)
    by_id, out, into = _index(root)

    hips = [i for i, n in by_id.items()
            if n.name == "Model" and _name(n).endswith(":Hips")]
    if not hips:
        return {"error": "no mixamorig:Hips"}
    hip = hips[0]

    # THE ROOT CLAIM IS CHECKED, NOT ASSUMED. Everything below reads the
    # hips' LOCAL curves as world motion, which is only true while the
    # hips have no Model parent. A different exporter could nest them,
    # and then a frozen reading would mean "the parent is doing it".
    parented = any(kind == "OO" and by_id.get(p) is not None
                   and by_id[p].name == "Model"
                   for kind, p, _prop in out.get(hip, []))
    if parented:
        return {"error": "hips are parented -- local curves are not world motion"}

    trans = _channels(by_id, into, hip, "Lcl Translation")
    rot = _channels(by_id, into, hip, "Lcl Rotation")
    if not trans and not rot:
        return {"error": "hips carry no curves"}

    spans = list(trans.values()) + list(rot.values())
    t0 = min(min(t) for t, _v in spans)
    t1 = max(max(t) for t, _v in spans)
    duration = (t1 - t0) / KTIME_PER_SECOND

    def rng(channels, axis, factor=1.0):
        keys = channels.get(axis)
        if keys is None:
            return 0.0
        _t, v = keys
        return (max(v) - min(v)) * factor

    moved_cm = max(rng(trans, a, scale) for a in "XYZ") if trans else 0.0
    turned_deg = max(rng(rot, a) for a in "XYZ") if rot else 0.0

    # Travel is FIRST-TO-LAST and horizontal; path is the sum of the
    # steps. They answer different questions -- a clip that walks out
    # and back has travel near zero and a long path -- and printing one
    # as the other is how a pacing clip reads as a standing one.
    def ends(axis):
        keys = trans.get(axis)
        if keys is None:
            return 0.0
        _t, v = keys
        return (v[-1] - v[0]) * scale / 100.0

    xs = trans.get("X", (None, [0.0]))[1]
    zs = trans.get("Z", (None, [0.0]))[1]
    steps = min(len(xs), len(zs))
    path = sum(math.hypot((xs[i + 1] - xs[i]) * scale / 100.0,
                          (zs[i + 1] - zs[i]) * scale / 100.0)
               for i in range(steps - 1))

    keycount = max(len(t) for t, _v in spans)

    # HIP HEIGHT, IN CENTIMETRES, AND IT IS THE MOST USEFUL NUMBER HERE.
    #
    # CLAUDE.md warns that hip HEIGHT is not comparable between clips, and
    # that is right about the question it was written for: you cannot tell
    # WHICH animation a clip is from its hip height, because a stand-up
    # legitimately starts at 8cm. It is decisive for a much narrower question
    # — is the body UPRIGHT or ON THE FLOOR — and that question is what caught
    # a whole class of wrong clips on 18 August:
    #
    #     walk         Walking          95cm      upright, as it should be
    #     jog          Jog Forward       7cm      a body on the floor
    #     lie_still    Lying Down       96cm      upright
    #     collapse     Dying           103cm      upright, and flat across the
    #                                             whole clip, so it never falls
    #
    # jog and lie_still are each other, confirmed independently by the contact
    # sheet. The median is the posture; min and max say whether it CHANGES,
    # which is how Knocked Out (6..104) reads correctly as a fall and Dying
    # (102.60..102.67) reads as a man standing perfectly still.
    hip_y = trans.get("Y")
    hips_cm = sorted(v * scale for v in hip_y[1]) if hip_y else []
    return {
        "hipLow": hips_cm[0] if hips_cm else 0.0,
        "hipCm": hips_cm[len(hips_cm) // 2] if hips_cm else 0.0,
        "hipHigh": hips_cm[-1] if hips_cm else 0.0,
        "duration": duration,
        "travel": math.hypot(ends("X"), ends("Z")),
        "path": path,
        "bob": rng(trans, "Y", scale),
        "movedCm": moved_cm,
        "turnedDeg": turned_deg,
        "keys": keycount,
        "frozen": moved_cm < FROZEN_CM and turned_deg < FROZEN_DEG,
    }


def clips():
    """(slot, mixamo name, path) for every clip FBX in the harvest."""
    found = []
    for folder in CLIP_FOLDERS:
        d = os.path.join(CHARACTERS, folder)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith(".fbx"):
                continue
            slot = f.split("__")[0]
            mixamo = f.split("__")[1].rsplit("_", 1)[0] if "__" in f else f
            found.append((slot, mixamo, os.path.join(d, f)))
    return found


def duplicates():
    """[[ (slot, mixamo), ... ]] for every group of byte-identical clips."""
    groups = collections.defaultdict(list)
    for slot, mixamo, path in clips():
        with open(path, "rb") as fh:
            groups[hashlib.sha256(fh.read()).hexdigest()].append((slot, mixamo))
    return [v for v in groups.values() if len(v) > 1]


def report():
    rows = []
    for slot, mixamo, path in clips():
        r = measure(path)
        r["slot"], r["mixamo"] = slot, mixamo
        rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--series", action="store_true",
                    help="print every clip, not only the findings")
    ap.add_argument("--quiet", action="store_true",
                    help="findings only, for use inside verify.py")
    args = ap.parse_args()

    rows = report()
    if not rows:
        print("no clips found under %s" % os.path.normpath(CHARACTERS))
        return 2
    read = [r for r in rows if "error" not in r]

    if args.series or not args.quiet:
        print("%-14s %-26s %6s %7s %7s %8s %8s %14s" %
              ("slot", "mixamo clip", "secs", "movecm", "turn°", "travel m",
               "path m", "hip cm lo/md/hi"))
        order = sorted(rows, key=lambda r: (r.get("movedCm", 0.0),
                                            r.get("turnedDeg", 0.0)))
        for r in order:
            if "error" in r:
                print("%-14s %-26s   %s" % (r["slot"], r["mixamo"][:26], r["error"]))
                continue
            print("%-14s %-26s %6.2f %7.2f %7.1f %8.2f %8.2f %14s%s" %
                  (r["slot"], r["mixamo"][:26], r["duration"], r["movedCm"],
                   r["turnedDeg"], r["travel"], r["path"],
                   "%.0f/%.0f/%.0f" % (r["hipLow"], r["hipCm"], r["hipHigh"]),
                   "   FROZEN ROOT" if r["frozen"] else ""))
        print()

    findings = 0
    dups = duplicates()
    print("%d clips read, %d declined" % (len(read), len(rows) - len(read)))
    if dups:
        findings += len(dups)
        print("DUPLICATE CONTENT — one slot in each group plays the wrong clip,")
        print("and the filename cannot say which. Re-fetch both:")
        for group in dups:
            print("    " + " == ".join("%s (%s)" % (s, m) for s, m in group))
    else:
        print("no two clips share content")

    frozen = [r for r in read
              if r["frozen"] and r["slot"] not in STILL_BY_DEFINITION]
    # AND THE EXEMPTED ONES ARE PRINTED, NOT SWALLOWED. An exemption nobody is
    # told about is indistinguishable from a finding that was never made — the
    # `head -3` fault in a filter's clothing. Saying which slot was excused and
    # what it read means a slot going still for the WRONG reason still shows
    # up, as a line somebody can read, rather than vanishing from the count.
    excused = [r for r in read
               if r["frozen"] and r["slot"] in STILL_BY_DEFINITION]
    if frozen:
        findings += len(frozen)
        print("FROZEN ROOT — the hips neither move nor turn across the whole")
        print("clip, so the body is animated from the waist up:")
        for r in sorted(frozen, key=lambda r: r["slot"]):
            print("    %-14s %-28s %.2fcm %.1f° over %.2fs"
                  % (r["slot"], r["mixamo"][:28], r["movedCm"],
                     r["turnedDeg"], r["duration"]))
    else:
        print("no frozen roots in %d clips" % len(read))
    for r in sorted(excused, key=lambda r: r["slot"]):
        print("    still by definition, not counted: %-12s %-24s "
              "%.2fcm %.1f° over %.2fs"
              % (r["slot"], r["mixamo"][:24], r["movedCm"],
                 r["turnedDeg"], r["duration"]))

    # THE MACHINE-READABLE LINE, AND IT CARRIES ITS DENOMINATOR (rule 3b).
    # `clipFindings=0` out of two clips read and out of fifty-two are very
    # different claims and the number alone cannot tell them apart.
    # `stillByDesign` is on it for the same reason: the exemption is part of
    # how the count was reached, so it belongs beside the count.
    print("clipFindings=%d duplicates=%d frozen=%d stillByDesign=%d clipsRead=%d"
          % (findings, len(dups), len(frozen), len(excused), len(read)))

    if args.selftest:
        return selftest(rows)
    return 1 if findings else 0


def selftest(rows):
    """BOTH CASES, because a guard is shipped only when both have been
    watched run (rule 5b)."""
    failures = []
    read = [r for r in rows if "error" not in r]

    # ACCEPTING: the harvest as it stands must read as ordinary clips.
    # A reader that rejects everything and a working one look identical
    # from a summary line.
    if len(read) < 40:
        failures.append("only %d of %d clips parsed -- the reader is the fault"
                        % (len(read), len(rows)))
    for r in read:
        if not (0.2 <= r["duration"] <= 60.0):
            failures.append("%s: %.2fs is not a clip length" % (r["slot"], r["duration"]))
        if r["keys"] < 2:
            failures.append("%s: %d keys is a pose, not an animation" % (r["slot"], r["keys"]))
        if r["travel"] > 30.0:
            failures.append("%s: %.1fm of travel -- unit scale is being read wrong"
                            % (r["slot"], r["travel"]))

    # REJECTING: a body model carries a rig and no take, and it must not
    # come back looking like a healthy clip. It reads as FROZEN with two
    # keys -- the rig's rest values -- which is the right answer and is
    # NOT the same as being declined: `measure` returns numbers for it.
    # Written that way round on purpose, because the frozen rule is what
    # this file's whole finding rests on and pointing it at a body with
    # no animation is the one input we know the answer for.
    body = os.path.join(CHARACTERS, "Joe.fbx")
    if os.path.isfile(body):
        r = measure(body)
        if "error" in r:
            failures.append("a rig with no take could not be read at all: %s"
                            % r["error"])
        elif not r["frozen"]:
            failures.append("a rig with no take was measured as a moving clip")
        elif r["keys"] > 2:
            failures.append("a rig with no take produced %d keys" % r["keys"])
    else:
        failures.append("no body model to test the rejecting case against")

    print()
    if failures:
        for f in failures:
            print("  FAIL: %s" % f)
        print("SELFTEST FAILED -- %d failure(s)" % len(failures))
        return 1
    print("SELFTEST PASSED -- %d clips read, %d declined, rejecting case held"
          % (len(read), len(rows) - len(read)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
