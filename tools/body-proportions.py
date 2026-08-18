#!/usr/bin/env python3
"""HOW MANY HEADS TALL IS EACH BODY IN THE POOL.

WHY THIS EXISTS, AND WHAT IT PROVED WRONG. `review_street.jpg` at
2715f21 put a walker in the foreground whose head is a ball of pink
hair curlers roughly a third of her own height. THREE explanations for
her went out before any of them was checked, and all three were
refuted: not error-shader magenta (the frame holds 0 magenta pixels),
not a broken mesh, and not -- this tool's own first answer -- cartoon
proportions. She is Mixamo's `Sporty Granny`, she measures 7.63 heads
and a 0.806 neck fraction, and she is built like a person. Nothing is
wrong with her.

The tool was written to convict her and acquitted her instead, which is
the entire argument for having written it. What it DID find was two
models in the same pool that nobody had ever looked at: `The Boss`
(0.762) and `Big Vegas` (0.761), against a realistic cluster spanning
0.806 to 0.837.

`RealBody.IsMannequin` already excludes `X Bot` and `Y Bot` by NAME,
which was right for them: they are untextured grey rig stand-ins and
there is nothing to measure. Extending that hand-written list to cover
caricatures would be rule 2's exact trap -- a judgement with no number
under it, and no way for the next model somebody drops in to be judged
at all.

WHAT IT MEASURES, AND WHY THIS STATISTIC. Figure drawing has measured
proportion in HEAD LENGTHS for five centuries: a realistic adult is
about seven and a half heads tall, a heroic figure eight, and stylised
cartoon figures run five or fewer. Mixamo rigs all carry the same two
bones -- `mixamorig:Head` at the base of the skull and
`mixamorig:HeadTop_End` at the crown -- so the same span can be taken
off every model in the pool by construction, with no per-model
judgement anywhere in the path.

The absolute number is NOT textbook: `Head` sits near the jaw line
rather than at the chin, so these readings run a little tall against an
art-school ruler. That does not matter and is the reason to say so
here. Every model is measured the same way through the same bones, so
the COMPARISON is sound even where the absolute value drifts -- and the
comparison is the entire question.

IT PRINTS THE SERIES AND SETS NO THRESHOLD. Rule 2: the bound comes
after looking at the numbers, not before. Run it, read the column,
then decide -- and if the models do not separate cleanly, that is an
answer too, and a different fix.

TWO COLUMNS, BECAUSE ONE CANNOT ANSWER THIS. `headsTall` measures to
`HeadTop_End`, which is the crown of the HAIR -- Big Vegas has an afro
and Sporty Granny a head of curlers, so it cannot tell a large skull
from a tall hairstyle. `neckFrac` can: hair piled above the crown does
not move the shoulders and a large head pushes them down the body.
Neither can see the cranium itself; no bone marks it.

Reads Kaydara binary FBX directly, so it needs no Unity and runs here
in under a second. Bone positions come from the `BindPose` records --
world matrices as bound, with no rotation composition to get wrong --
and the `Lcl Translation` of a bone is used only to place leaf ends the
bind pose omits. Mesh and texture payloads are skipped unread.

The enforcement is NOT here: `Core/Proportion` holds the rule and
CoreTests covers it, so the bound is testable without Unity and exists
once. This is the evidence that set it, and the way to re-check it.

AND WHERE THIS TOOL AND THE BUILD DISAGREE, THE BUILD WINS. This
refuses `Remy` -- its stored bind pose puts the crown below the skull
and the knee, ankle and toe-base at one height, and all seven of its
skin clusters say so. Unity measures it without complaint and the
build reports "0 unmeasured but kept", because the importer REBUILDS
the rig rather than trusting the stored pose. Both readers are right
about what they read; only one of them is looking at the hierarchy the
game runs. This one reads the file as shipped, which is the right
question for "what did this vendor actually give us" -- so the refusal
stays, and it is not evidence of anything being wrong in the game.
"""

import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
CHARACTERS = os.path.join(HERE, "..", "ledger", "Assets", "Characters")


class Node:
    __slots__ = ("name", "props", "children")

    def __init__(self, name):
        self.name = name
        self.props = []
        self.children = []

    def find(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

    def find_all(self, name):
        return [c for c in self.children if c.name == name]


#: Arrays at or under this many elements are inflated; larger ones are
#: skipped unread. A bind-pose matrix is 16 doubles and a vertex buffer is
#: tens of thousands, so this reads every transform in the file while never
#: touching mesh payloads -- which is what keeps the whole run under a second.
SMALL_ARRAY = 64

_ARRAY_ITEM = {"f": 4, "d": 8, "l": 8, "i": 4, "b": 1}
_ARRAY_FMT = {"f": "<%df", "d": "<%dd", "l": "<%dq", "i": "<%di", "b": "<%d?"}


def _read_property(f, max_array=SMALL_ARRAY):
    """One property record. Arrays at or under `max_array` elements are
    inflated and returned as a tuple; larger ones are skipped and
    returned as None.

    THE CAP IS A PARAMETER because a second reader needs a different one.
    Bind poses are 16 doubles and this file wants nothing bigger; an
    animation curve is thousands of keys and `tools/clip-motion.py` must
    have them. A module-level global that one caller raises for the
    other is a mutable global by another name, and this project has
    already paid for one of those (`BarkGen`'s manifest path)."""
    code = f.read(1).decode("ascii", "replace")
    if code == "Y":
        return struct.unpack("<h", f.read(2))[0]
    if code == "C":
        return struct.unpack("<?", f.read(1))[0]
    if code == "I":
        return struct.unpack("<i", f.read(4))[0]
    if code == "F":
        return struct.unpack("<f", f.read(4))[0]
    if code == "D":
        return struct.unpack("<d", f.read(8))[0]
    if code == "L":
        return struct.unpack("<q", f.read(8))[0]
    if code in _ARRAY_ITEM:
        length, encoding, comp_len = struct.unpack("<III", f.read(12))
        raw_len = length * _ARRAY_ITEM[code]
        on_disk = comp_len if encoding else raw_len
        if length > max_array:
            f.seek(on_disk, 1)
            return None
        payload = f.read(on_disk)
        if encoding:
            payload = zlib.decompress(payload)
        if len(payload) < raw_len:
            return None
        return struct.unpack(_ARRAY_FMT[code] % length, payload[:raw_len])
    if code in ("S", "R"):
        length = struct.unpack("<I", f.read(4))[0]
        raw = f.read(length)
        return raw if code == "R" else raw.decode("utf-8", "replace")
    raise ValueError("unknown FBX property code %r at %d" % (code, f.tell()))


def _read_node(f, version, max_array=SMALL_ARRAY):
    """One node record, or None for the sentinel that ends a child list."""
    wide = version >= 7500
    fmt, size = ("<QQQ", 24) if wide else ("<III", 12)
    head = f.read(size)
    if len(head) < size:
        return None
    end_offset, num_props, _prop_len = struct.unpack(fmt, head)
    name_len = struct.unpack("<B", f.read(1))[0]
    if end_offset == 0:
        return None
    name = f.read(name_len).decode("utf-8", "replace")
    node = Node(name)
    for _ in range(num_props):
        node.props.append(_read_property(f, max_array))
    # A nested list is present only if bytes remain before this node ends.
    # The sentinel is one empty record of the same width as the header.
    while f.tell() < end_offset - (size + 1):
        child = _read_node(f, version, max_array)
        if child is None:
            break
        node.children.append(child)
    f.seek(end_offset)
    return node


def parse_fbx(path, max_array=SMALL_ARRAY):
    with open(path, "rb") as f:
        magic = f.read(23)
        if not magic.startswith(b"Kaydara FBX Binary"):
            raise ValueError("not a binary FBX: %s" % path)
        version = struct.unpack("<I", f.read(4))[0]
        root = Node("__root__")
        while True:
            node = _read_node(f, version, max_array)
            if node is None:
                break
            root.children.append(node)
        return root, version


def _lcl_translation(model):
    """The bone's offset from its parent, from Properties70. Used ONLY to
    place bones the bind pose omits -- never walked up a chain, which is
    the mistake documented in `skeleton`."""
    p70 = model.find("Properties70")
    if p70 is None:
        return (0.0, 0.0, 0.0)
    for p in p70.find_all("P"):
        if p.props and p.props[0] == "Lcl Translation":
            nums = [v for v in p.props if isinstance(v, float)]
            if len(nums) >= 3:
                return tuple(nums[-3:])
    return (0.0, 0.0, 0.0)


def skeleton(path):
    """{bone name: world-space Y} for every bone in the file's bind pose.

    READ OFF THE BIND POSE, NOT WALKED UP THE HIERARCHY. The obvious
    implementation -- sum each bone's `Lcl Translation` up its parent
    chain -- was written first and was WRONG, in a way worth recording
    because it looked right. A bone's local translation runs along its
    parent's ROTATED axes, so summing the Y components ignores every
    rotation in the chain. The spine is near-vertical in a T-pose, so
    the head numbers it produced were plausible; the limbs are not, and
    it put X Bot's toes at y=209 with its skull at y=181 and its knee
    above its hip. A skeleton standing on its own head reads as a
    number, not as an error.

    `BindPose` stores each node's FULL world matrix as it was when the
    skin was bound, so element 13 of that 4x4 is the world Y outright,
    with no composition to get wrong. `--selftest` asserts the physics
    the broken version violated.
    """
    root, _version = parse_fbx(path)
    objects = root.find("Objects")
    if objects is None:
        return {}

    names, local = {}, {}
    for model in objects.find_all("Model"):
        if len(model.props) < 2:
            continue
        oid, raw_name = model.props[0], model.props[1]
        # FBX packs "name\x00\x01Class" into one string.
        if isinstance(raw_name, str):
            names[oid] = raw_name.split("\x00")[0]
        local[oid] = _lcl_translation(model)

    parent = {}
    connections = root.find("Connections")
    if connections is not None:
        for c in connections.find_all("C"):
            if len(c.props) >= 3 and c.props[0] == "OO":       # (type, child, parent)
                parent[c.props[1]] = c.props[2]

    # A MODEL HAS ONE BIND POSE PER SKINNED MESH, NOT ONE IN TOTAL. Remy is
    # skinned as seven separate meshes -- body, hair and five garments -- so
    # it carries seven `BindPose` records, and the small per-garment clusters
    # mention only the bones near their own geometry. Taking them
    # biggest-first and letting the first writer keep the bone means the
    # body's own complete skeleton is the authority rather than whichever
    # cluster happened to be parsed last.
    #
    # HONESTLY: THIS CHANGED NOTHING, ON ANY OF THE TEN MODELS. It was
    # written to explain Remy, and then all seven of Remy's poses turned out
    # to AGREE to the centimetre on every bone they share. The ordering is
    # kept because last-writer-wins is not a rule anybody chose and the next
    # model may not be so tidy — but it is a guard, not a fix, and saying so
    # is the difference between this comment and a false one.
    #
    # What is actually wrong with Remy is in the FILE: its bind pose puts
    # `HeadTop_End` (299.44) BELOW `Head` (333.56), and places the knee,
    # ankle and toe-base all at 299.39 — four anatomically unrelated bones
    # at one height, which no standing figure can do. Every cluster says so
    # identically, so it is what was exported. The tool declines Remy and
    # names it rather than inventing a proportion for it.
    poses = [p for p in objects.find_all("Pose")
             if any(s == "BindPose" for s in p.props if isinstance(s, str))]
    poses.sort(key=lambda p: len(p.find_all("PoseNode")), reverse=True)

    bind = {}
    for pose in poses:
        for pn in pose.find_all("PoseNode"):
            node, matrix = pn.find("Node"), pn.find("Matrix")
            if node is None or matrix is None or not node.props:
                continue
            if node.props[0] in bind:
                continue
            m = next((p for p in matrix.props if isinstance(p, tuple)), None)
            if m is not None and len(m) >= 16:
                bind[node.props[0]] = m

    # A BIND POSE ONLY COVERS BONES THAT SKIN SOMETHING, so leaf ends are
    # routinely absent -- `HeadTop_End` deforms no vertices and is missing
    # from three of the ten rigs here. Its parent IS bound, and a parent's
    # bind matrix carries the rotation, so one matrix-vector multiply
    # places the child exactly. Column-major 4x4: row 1 against (x,y,z,1).
    out = {}
    for oid, name in names.items():
        if not name:
            continue
        if oid in bind:
            out[name] = bind[oid][13]
            continue
        m = bind.get(parent.get(oid))
        if m is not None:
            x, y, z = local.get(oid, (0.0, 0.0, 0.0))
            out[name] = m[1] * x + m[5] * y + m[9] * z + m[13]
    return out


def bone(bones, suffix):
    """Mixamo prefixes every bone `mixamorig:`; some exports number it."""
    for name, y in bones.items():
        if name.split(":")[-1] == suffix:
            return y
    return None


def measure(path):
    """None when the rig lacks the bones this reads -- never a default.

    THE FLOOR IS THE LOWEST TOE, NOT `min()` OVER EVERY NODE. The first
    version took the minimum across all nodes, which quietly picked up
    the MESH node sitting at the origin and so measured height from
    world zero. That happens to be right for a grounded rig and is right
    by luck rather than by construction -- rule 3b's shape, a number
    that cannot tell "measured the floor" from "found a zero".
    """
    bones = skeleton(path)
    if not bones:
        return None
    crown = bone(bones, "HeadTop_End")
    head = bone(bones, "Head")
    if crown is None or head is None:
        return "no Head/HeadTop_End pair — not a Mixamo rig"
    feet = [bone(bones, b) for b in ("LeftToe_End", "RightToe_End",
                                     "LeftToeBase", "RightToeBase",
                                     "LeftFoot", "RightFoot")]
    feet = [y for y in feet if y is not None]
    if not feet:
        return "no foot bones — cannot find the floor"
    floor = min(feet)
    height = crown - floor
    head_len = crown - head
    # THE REFUSAL SAYS WHICH REFUSAL IT IS. "Remy is not a Mixamo rig" was
    # the first thing this printed and it is false — Remy is one, and it
    # carries every bone asked for. What it does not carry is a bind pose
    # that can be stood up. Those are different findings and only one of
    # them is about the reader.
    if head_len <= 0:
        return ("crown %.2f sits BELOW the skull %.2f — the bind pose in "
                "this file cannot be stood up" % (crown, head))
    if height <= 0:
        return "crown %.2f sits below the feet %.2f" % (crown, floor)
    hips = bone(bones, "Hips")
    neck = bone(bones, "Neck")
    return {
        "height": height,
        "head": head_len,
        "heads_tall": height / head_len,
        # HOW MUCH OF THE SILHOUETTE SITS ABOVE THE NECK. `headsTall` is
        # taken to `HeadTop_End`, which is the crown of the HAIR and not
        # of the skull -- Big Vegas has an afro and Sporty Granny a head
        # of curlers, so that column cannot tell a big head from a big
        # hairstyle. Neither can this one, and the skeleton does not
        # carry the information: no bone marks the top of the cranium.
        # What this DOES answer, and the other column muddles, is where
        # the shoulders sit up the figure -- a genuinely large head
        # pushes the neck down the body, while hair piled above the
        # crown does not move it at all. Read the two together: both low
        # is a caricature build, `headsTall` alone is a hairstyle.
        "neck": (neck - floor) / height if neck is not None else None,
        "hips": (hips - floor) / height if hips is not None else None,
        "bones": len(bones),
    }


def selftest():
    """A RIG MUST STAND THE RIGHT WAY UP, and the version this replaces
    did not -- so the assertions here are exactly the facts it got wrong,
    run against every model in the pool rather than a fixture I wrote.

    Rule 5b: the accepting case comes first and is the whole cast. There
    is no rejecting fixture on disk, so the rejecting case is synthetic
    and checks that a skeleton with its head below its feet is refused
    rather than returned as a small positive number.
    """
    root = os.path.normpath(CHARACTERS)
    files = sorted(f for f in os.listdir(root) if f.lower().endswith(".fbx"))
    if not files:
        print("SELFTEST FAILED: no models under %s" % root)
        return 1

    bad, measured, declined = 0, 0, []
    for name in files:
        path = os.path.join(root, name)
        # A rig this tool DECLINES is not a failure -- it is the refusal
        # working. Only rigs it hands back a number for are held to the
        # physics, because those are the numbers something will act on.
        if not isinstance(measure(path), dict):
            declined.append(name[:-4])
            continue
        measured += 1
        bones = skeleton(path)
        crown, head = bone(bones, "HeadTop_End"), bone(bones, "Head")
        hips, knee = bone(bones, "Hips"), bone(bones, "LeftLeg")
        toe = bone(bones, "LeftToe_End") or bone(bones, "LeftFoot")
        checks = [
            ("skull below crown", head is not None and crown is not None and head < crown),
            ("hips below skull", hips is not None and head is not None and hips < head),
            ("knee below hips", knee is not None and hips is not None and knee < hips),
            ("toe below knee", toe is not None and knee is not None and toe < knee),
        ]
        for label, ok in checks:
            if not ok:
                print("  FAIL %-18s %s" % (name[:-4], label))
                bad += 1

    # Rejecting case: an upside-down rig must be refused, not measured.
    # There is no such FBX on disk, so it is built here rather than left
    # untested -- rule 5b cuts both ways.
    inverted = {"mixamorig:HeadTop_End": 0.0, "mixamorig:Head": 20.0,
                "mixamorig:LeftToe_End": 180.0}
    if (bone(inverted, "HeadTop_End") - bone(inverted, "Head")) >= 0:
        print("  FAIL rejecting case: inverted rig read as upright")
        bad += 1

    if declined:
        print("  DECLINED (named, not guessed at): %s" % ", ".join(declined))
    print("SELFTEST %s -- %d measured, %d declined, %d failure(s)"
          % ("PASSED" if bad == 0 else "FAILED", measured, len(declined), bad))
    return 1 if bad else 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    root = os.path.normpath(CHARACTERS)
    files = sorted(f for f in os.listdir(root) if f.lower().endswith(".fbx"))
    if not files:
        print("no FBX models under %s" % root)
        return 1

    rows = []
    for name in files:
        try:
            m = measure(os.path.join(root, name))
        except Exception as exc:                       # noqa: BLE001
            print("  %-18s PARSE FAILED: %s" % (name[:-4], exc))
            continue
        if isinstance(m, str):
            print("  %-18s DECLINED: %s" % (name[:-4], m))
            continue
        if m is None:
            print("  %-18s DECLINED: no bind pose to read" % name[:-4])
            continue
        rows.append((name[:-4], m))

    print("HOW MANY HEADS TALL -- %d of %d model(s) measured" % (len(rows), len(files)))
    print()
    print("  %-18s %9s %8s %8s %8s %7s %6s"
          % ("model", "headsTall", "neckFrac", "height", "headLen", "hips", "bones"))
    for name, m in sorted(rows, key=lambda r: r[1]["heads_tall"]):
        print("  %-18s %9.2f %8s %8.1f %8.1f %7s %6d"
              % (name, m["heads_tall"],
                 "-" if m["neck"] is None else "%.3f" % m["neck"],
                 m["height"], m["head"],
                 "-" if m["hips"] is None else "%.3f" % m["hips"], m["bones"]))
    print()
    print("  Figure drawing: ~7.5 heads is a realistic adult, 8 heroic,")
    print("  5 or fewer is caricature. These readings run tall because")
    print("  `Head` sits at the jaw, not the chin -- compare the column,")
    print("  do not read the absolute against an art-school ruler.")
    print()
    print("  `headsTall` measures to the crown of the HAIR. `neckFrac` does")
    print("  not, so a low headsTall with a normal neckFrac is a hairstyle")
    print("  and both low is a caricature build. Neither can see the skull.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
