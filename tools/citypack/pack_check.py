#!/usr/bin/env python3
"""Open the pack you are shipping.

The listening page was published with six faults, every one invisible from the
Python that generated it and every one found in the first sixty seconds of
actually loading it. `page_check.py` exists because of that day, and this is the
same check for the city pack: the fetch script can only tell you what it
*believes* it wrote.

Needs no network and no Unity. It reads the committed pack the way
`AssetLibrary` will: by logical name, with the same extensions, from the same
directory — so a file that this passes is a file the game will find.

    python3 tools/citypack/pack_check.py
    python3 tools/citypack/pack_check.py --selftest
"""
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PACK = ROOT / "ledger" / "Assets" / "StreamingAssets" / "CityPack"

# Exactly the names `AssetLibrary` declares as public constants. Kept as a
# literal list rather than parsed out of the C#, because a parser that silently
# matches nothing would make this check pass by finding no work to do.
SURFACES = ["asphalt", "sidewalk", "kerb", "brick_red", "brick_grey", "plaster",
            "concrete", "wood", "roof", "metal", "glass", "window"]

# `LoadPackTexture` tries these three, in this order.
EXTS = (".png", ".jpg", ".jpeg")

_fails = []


def check(ok, what, got=""):
    print(("  ok   " if ok else "  FAIL ") + what + ("" if ok else f" — {got}"))
    if not ok:
        _fails.append(what)


def dimensions(path):
    """Width and height, without an image library. PNG and JPEG only, which is
    what `LoadPackTexture` accepts anyway."""
    b = path.read_bytes()
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", b[16:24])
        return w, h
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1
                continue
            marker = b[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return w, h
            seg = struct.unpack(">H", b[i + 2:i + 4])[0]
            i += 2 + seg
    return None


def audit(pack=None):
    pack = pack or PACK
    textures = pack / "textures"
    if not pack.exists() or not textures.exists():
        # NOT A FAILURE YET. The pack does not exist until M17.6's fetch has
        # run, and a check that goes red for work that has not started teaches
        # people to ignore it. It says so out loud instead.
        print(f"  --   no pack at {pack.relative_to(ROOT)} — "
              "the game falls back to procedural textures (M17.6 not landed)")
        return

    found, sizes = {}, []
    for logical in SURFACES:
        hit = None
        for ext in EXTS:
            p = textures / (logical + ext)
            if p.exists():
                hit = p
                break
        if hit is None:
            check(False, f"{logical} — a texture the game will find", "no file")
            continue
        found[logical] = hit
        # AN EMPTY FILE IS A FILE. The voice pipeline shipped a run that
        # produced zero-byte output and reported success.
        if hit.stat().st_size < 4096:
            check(False, f"{logical} — file has content", f"{hit.stat().st_size} bytes")
            continue
        dim = dimensions(hit)
        if dim is None:
            check(False, f"{logical} — decodes as PNG or JPEG", "unreadable header")
            continue
        w, h = dim
        sizes.append((logical, w, h, hit.stat().st_size))
        # A TILING TEXTURE HAS TO BE SQUARE AND POWER-OF-TWO, or it repeats
        # wrong at the tiling rates in `SurfaceSpec` and looks like a stretched
        # photograph. This is the fault nobody sees in a file listing.
        check(w == h, f"{logical} — square, so it tiles", f"{w}x{h}")
        check(w and (w & (w - 1)) == 0, f"{logical} — power-of-two", f"{w}")
        check(256 <= w <= 2048, f"{logical} — a sane size", f"{w}px")

    if sizes:
        print()
        for logical, w, h, n in sizes:
            print(f"    {logical:<12} {w}x{h}  {n // 1024} KiB")
        print()

    check(len(found) == len(SURFACES),
          f"every one of the {len(SURFACES)} surfaces AssetLibrary asks for is present",
          f"{len(found)} present, missing: "
          + ", ".join(s for s in SURFACES if s not in found))

    # AND WHERE EVERY FILE CAME FROM. A pack with no provenance cannot be
    # shipped, because the licence obligation attaches to the file rather than
    # to whoever remembers downloading it.
    attr_path = pack / "ATTRIBUTION.json"
    check(attr_path.exists(), "the pack records where its files came from",
          "no ATTRIBUTION.json")
    if attr_path.exists():
        attr = json.loads(attr_path.read_text(encoding="utf-8"))
        recorded = attr.get("surfaces", {})
        missing = [s for s in found if s not in recorded]
        check(not missing, "every texture present is attributed",
              ", ".join(missing[:5]))
        unlicensed = [s for s, v in recorded.items() if not v.get("licence")]
        check(not unlicensed, "every attribution names a licence",
              ", ".join(unlicensed[:5]))


def selftest():
    """The check, watched failing on each fault it exists to catch."""
    import tempfile
    global _fails
    passed = failed = 0

    def png(w, h, pad=8192):
        head = (b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR"
                + struct.pack(">II", w, h))
        return head + b"\x00" * pad

    def expect(name, fn):
        global _fails
        nonlocal passed, failed
        _fails = []
        fn()
        if _fails:
            passed += 1
            print(f"  ok   {name}")
        else:
            failed += 1
            print(f"  FAIL {name} — passed on broken input")

    print("pack-check selftest\n")
    with tempfile.TemporaryDirectory() as tmp:
        pack = pathlib.Path(tmp) / "CityPack"
        tex = pack / "textures"
        tex.mkdir(parents=True)

        def writeall(w=1024, h=1024, pad=8192, skip=()):
            for s in SURFACES:
                if s in skip:
                    continue
                (tex / (s + ".png")).write_bytes(png(w, h, pad))
            (pack / "ATTRIBUTION.json").write_text(json.dumps(
                {"surfaces": {s: {"licence": "CC0 1.0 Universal"}
                              for s in SURFACES if s not in skip}}))

        writeall(skip={"roof"})
        expect("a missing surface is caught", lambda: audit(pack))

        writeall(w=1024, h=512)
        expect("a non-square texture is caught", lambda: audit(pack))

        writeall(w=1000, h=1000)
        expect("a non-power-of-two texture is caught", lambda: audit(pack))

        writeall(pad=0)
        expect("an empty file is caught", lambda: audit(pack))

        writeall()
        (pack / "ATTRIBUTION.json").unlink()
        expect("a pack with no provenance is caught", lambda: audit(pack))

        writeall()
        (pack / "ATTRIBUTION.json").write_text(json.dumps(
            {"surfaces": {s: {} for s in SURFACES}}))
        expect("an attribution with no licence is caught", lambda: audit(pack))

        writeall()
        _fails = []
        audit(pack)
        if _fails:
            failed += 1
            print(f"  FAIL a well-formed pack passes — {_fails[0]}")
        else:
            passed += 1
            print("  ok   a well-formed pack passes")

    _fails = []
    print(f"\n{passed}/{passed + failed} checks behave correctly")
    return 1 if failed else 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    print("pack-check — the city pack, read the way the game will read it\n")
    audit()
    print()
    print("pack ok" if not _fails else f"{len(_fails)} problem(s)")
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
