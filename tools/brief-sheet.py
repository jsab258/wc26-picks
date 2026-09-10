#!/usr/bin/env python3
"""COMPOSE TWO PICTURES SIDE BY SIDE FOR THE BRIEF. Not an instrument.

    python3 tools/brief-sheet.py rung1
    python3 tools/brief-sheet.py hook --ours <png>
    python3 tools/brief-sheet.py --selftest

IT MEASURES NOTHING AND MUST NEVER BE READ AS EVIDENCE. Jafar ruled on
2026-09-09 that no new instrument is built for the art lane this week,
because what exists is enough to judge by eye. This is the "by eye" half:
it puts two pictures at one scale so a person can look at them. Every
number in this project comes from somewhere else.

WHY IT EXISTS AT ALL. game-design/sim-shots/rung1_vs_reference.jpg was
composed by hand inside a session on 2026-09-09 and nothing could rebuild
it. A picture that goes in front of Jafar every day and cannot be
regenerated is a picture that silently goes stale, and the same day's work
found two separate cases of exactly that decay.

THE REFERENCE PANEL BOX IS NOT INVENTED HERE. x 11..1013, y 662..1279 of
the 1024x1536 sheet. It agrees with the bounds already recorded in
production/specs/vignette-scene.json on the cam_hook entry, which were
written when cam_hook was placed FROM that panel. Queue 220 carries the
remaining half, making that the single machine-readable source so this
constant can be deleted rather than maintained. Until then the two are
checked against each other by --selftest rather than trusted.

THE CROP MATTERS AND HAS BEEN WRONG. An earlier crop of (0,768,1024,1536)
took 32 per cent swatch strip and near-white caption band and dropped 106
rows off the top of the photograph, which produced a false claim about the
two pictures' bright ends. That is why the box is stated, checked and
commented rather than passed around.
"""
import argparse, json, re, sys, subprocess
from pathlib import Path

REF_BLOB = "origin/art/atlas-01:production/art/atlas-01/concepts/hook.png"
REF_BOX = (11, 662, 1013, 1279)          # x0, y0, x1, y1 of the street photo
OURS_RUNG1 = "production/d1-probe/ue-vign_hook_day.png"
OUT_DIR = Path("game-design/sim-shots")
GUTTER, MARGIN, BAR = 10, 14, 34


def _pil():
    try:
        from PIL import Image, ImageDraw
        return Image, ImageDraw
    except ImportError:
        sys.exit("brief-sheet: Pillow is not installed, nothing composed")


def ref_box_from_scene(path="production/specs/vignette-scene.json"):
    """The bounds the repo already carries, read back out of cam_hook's note.

    Returns None when the note cannot be parsed. NONE IS NOT ZERO: the
    caller prints "nothing measured" rather than treating a parse failure
    as agreement.
    """
    p = Path(path)
    if not p.exists():
        return None
    try:
        scene = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    for cam in scene.get("cameras", []):
        if cam.get("id") != "cam_hook":
            continue
        m = re.search(r"x\s+(\d+)\s+to\s+(\d+)\s+and\s+y\s+(\d+)\s+to\s+(\d+)",
                      cam.get("note", ""))
        if m:
            x0, x1, y0, y1 = (int(g) for g in m.groups())
            return (x0, y0, x1, y1)
    return None


def fetch_ref(dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "show", REF_BLOB], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return None
    dest.write_bytes(r.stdout)
    return dest


def compose(left_img, left_label, right_img, right_label, out: Path):
    Image, ImageDraw = _pil()
    h = max(left_img.height, right_img.height)
    h = min(h, 900)

    def fit(im):
        w = int(im.width * h / im.height)
        return im.resize((w, h), Image.LANCZOS)

    a, b = fit(left_img), fit(right_img)
    W = MARGIN * 2 + a.width + GUTTER + b.width
    H = MARGIN * 2 + BAR + h
    sheet = Image.new("RGB", (W, H), (16, 16, 16))
    sheet.paste(a, (MARGIN, MARGIN + BAR))
    sheet.paste(b, (MARGIN + a.width + GUTTER, MARGIN + BAR))
    d = ImageDraw.Draw(sheet)
    d.text((MARGIN, MARGIN + 8), left_label, fill=(238, 238, 238))
    d.text((MARGIN + a.width + GUTTER, MARGIN + 8), right_label,
           fill=(238, 238, 238))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=92)
    return sheet


def selftest():
    checks, fails = 0, []

    def ck(name, ok, why=""):
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}: {why}")

    ck("box is ordered", REF_BOX[0] < REF_BOX[2] and REF_BOX[1] < REF_BOX[3],
       f"{REF_BOX}")
    ck("box is inside a 1024x1536 sheet",
       REF_BOX[2] <= 1024 and REF_BOX[3] <= 1536, f"{REF_BOX}")
    scene_box = ref_box_from_scene()
    if scene_box is None:
        # A never-ran case says so in words. It is not a pass and not a zero.
        print("  cam_hook note: nothing measured, the note did not parse, so "
              "the constant in this file is UNCHECKED against the repo's copy")
    else:
        # ACCEPTING CASE FIRST: the live repo is the fixture, and the two
        # sources may differ by one pixel at each far edge because one is an
        # inclusive bound and the other exclusive.
        ck("cam_hook note agrees within 1 px",
           all(abs(a - b) <= 1 for a, b in zip(REF_BOX, scene_box)),
           f"file={REF_BOX} scene={scene_box}")
        # REJECTING CASE, synthetic: a box that agrees with nothing must fail
        # the same comparison, or the comparison is not testing anything.
        bogus = (0, 768, 1024, 1536)
        ck("a wrong box is rejected",
           not all(abs(a - b) <= 1 for a, b in zip(bogus, scene_box)),
           f"bogus={bogus} was accepted against scene={scene_box}")
    print(f"brief-sheet selftest: {checks - len(fails)} ok, {len(fails)} "
          f"failed, over {checks} check(s)")
    for f in fails:
        print("  FAIL", f)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", nargs="?",
                    choices=["rung1", "hook", "district", "stack"])
    ap.add_argument("--ours")
    ap.add_argument("--ref", help="the reference sheet for district mode")
    ap.add_argument("--left", help="label over the left picture")
    ap.add_argument("--right", help="label over the right picture")
    ap.add_argument("--name", help="output filename under game-design/sim-shots")
    ap.add_argument("--stack", nargs="*", default=None,
                    help="stack these jpgs into one brief picture, in order")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.what == "stack":
        Image, ImageDraw = _pil()
        paths = [Path(x) for x in (a.stack or [])]
        missing = [str(x) for x in paths if not x.exists()]
        if not paths:
            sys.exit("brief-sheet: stack needs at least one jpg, none given")
        if missing:
            # NAMED, not counted: a picture silently dropped from the brief
            # is the fault this whole composite exists to avoid.
            sys.exit("brief-sheet: not on disk, nothing composed: "
                     + ";".join(missing))
        W = 1600
        ims = [Image.open(x).convert("RGB") for x in paths]
        ims = [i.resize((W, int(i.height * W / i.width)), Image.LANCZOS)
               for i in ims]
        GAP = 18
        H = sum(i.height for i in ims) + GAP * (len(ims) - 1)
        sheet = Image.new("RGB", (W, H), (16, 16, 16))
        d = ImageDraw.Draw(sheet)
        y = 0
        for n, i in enumerate(ims):
            sheet.paste(i, (0, y))
            y += i.height
            if n < len(ims) - 1:
                d.line([(0, y + GAP // 2), (W, y + GAP // 2)],
                       fill=(90, 90, 90), width=2)
                y += GAP
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUT_DIR / (a.name or "brief_stack.jpg")
        sheet.save(out, quality=90)
        print(f"brief-sheet stacked {len(ims)} picture(s) into {out} "
              f"({out.stat().st_size} bytes, {sheet.size[0]}x{sheet.size[1]})")
        return 0
    if not a.what:
        ap.error("say what to compose, or pass --selftest")

    Image, _ = _pil()
    tmp = Path(".brief-sheet-ref.png")
    if fetch_ref(tmp) is None:
        sys.exit("brief-sheet: the reference blob could not be read, nothing "
                 "composed")
    ref_full = Image.open(tmp).convert("RGB")

    if a.what == "district":
        # ANY district, not just the Hook. The reference is named on the
        # command line because there are seven of them and hardcoding one
        # was what made the hook mode un-reusable.
        if not a.ref or not Path(a.ref).exists():
            sys.exit("brief-sheet: district needs --ref naming a reference sheet")
        if not a.ours or not Path(a.ours).exists():
            sys.exit("brief-sheet: district needs --ours naming a drawn sheet")
        out = OUT_DIR / (a.name or "district_theirs_vs_ours.jpg")
        compose(Image.open(a.ref).convert("RGB"), a.left or "THEIRS",
                Image.open(a.ours).convert("RGB"), a.right or "OURS", out)
        tmp.unlink(missing_ok=True)
        print(f"brief-sheet wrote {out} ({out.stat().st_size} bytes)")
        return 0
    if a.what == "rung1":
        ours_path = a.ours or OURS_RUNG1
        if not Path(ours_path).exists():
            sys.exit(f"brief-sheet: {ours_path} is not on disk, nothing composed")
        out = OUT_DIR / "rung1_vs_reference.jpg"
        compose(ref_full.crop(REF_BOX), "THE REFERENCE",
                Image.open(ours_path).convert("RGB"),
                "WHAT WE RENDER TODAY, same street, same viewpoint", out)
    else:
        if not a.ours or not Path(a.ours).exists():
            sys.exit("brief-sheet: hook needs --ours pointing at a drawn sheet")
        out = OUT_DIR / "hook_theirs_vs_ours.jpg"
        compose(ref_full, "THEIRS, three passes",
                Image.open(a.ours).convert("RGB"), "OURS, two passes, best of four seeds", out)
    tmp.unlink(missing_ok=True)
    print(f"brief-sheet wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
