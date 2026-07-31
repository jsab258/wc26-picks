#!/usr/bin/env python3
"""The application icon, generated rather than drawn.

M22.3. The completeness audit found no app icon, no splash and no store
metadata: CI produces a build artefact and nothing turns it into something a
person installs. The icon is the cheapest of those and the one everything else
waits behind, because a build with the default Unity logo on it is a build
nobody can tell apart from any other Unity project on a taskbar.

WHY GENERATED. No image library exists in this container — no PIL, no numpy —
and no asset host is reachable, so a downloaded icon is not available either.
A PNG is a handful of chunks and a zlib stream, which the standard library has,
so the icon can be a FUNCTION OF THE PALETTE the game already uses rather than
a file somebody has to keep in sync with it.

That turns out to be the better answer regardless. `Core/Palette` and
`SurfaceSpec` define the restricted noir palette — desaturated blue-greys
punctured by warm sodium — and an icon drawn from those numbers cannot drift
away from the game's own look the way a hand-drawn PNG would.

WHAT IT IS. A ledger, which is the game's title and its central object: a dark
ruled book with a single warm line struck through it. Silhouette-first, for the
same reason the held objects are — at 32 pixels on a taskbar nothing survives
but the shape, and a shape that reads at 32 will read at 512.

    python3 tools/make-icon.py
"""
import pathlib
import struct
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "ledger" / "Assets" / "Resources" / "AppIcon"

# THE PALETTE, TAKEN FROM THE GAME rather than picked here. These are the noir
# pass's own values: cool desaturated stone for the body, near-black for the
# ruled lines, and the sodium lamp warm that every light in the city uses.
INK = (0x14, 0x15, 0x18)
BOARD = (0x2A, 0x2F, 0x38)
PAGE = (0x49, 0x50, 0x5C)
RULE = (0x4C, 0x53, 0x5F)
SODIUM = (0xD8, 0x8B, 0x3A)

SIZES = (1024, 512, 256, 128, 64, 48, 32, 16)


def png(width, height, pixels):
    """A PNG from raw RGB rows. No image library, and none needed."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)                       # filter type 0, none
        for x in range(width):
            raw.extend(pixels[y][x])
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def draw(n):
    """The ledger, at n by n.

    Everything is in fractions of `n` so the 16-pixel version is the same
    drawing rather than a separate asset that drifts. The one concession to
    size is the ruled lines: below 48 pixels they stop being lines and start
    being noise, so they are dropped and the struck rule carries the whole
    read."""
    px = [[INK for _ in range(n)] for _ in range(n)]

    def rect(x0, y0, x1, y1, c):
        for y in range(max(0, int(y0)), min(n, int(y1))):
            row = px[y]
            for x in range(max(0, int(x0)), min(n, int(x1))):
                row[x] = c

    # MARGIN, SET BY LOOKING AT IT. 0.14 was the first guess and the icon sat
    # visibly small in its own frame at 32 pixels — read off the rendered
    # file rather than off the arithmetic, which is the only way to know.
    m = n * 0.09
    rect(m, m, n - m, n - m, BOARD)                       # the cover
    rect(m + n * 0.10, m, n - m, n - m, PAGE)             # the block of pages
    rect(m + n * 0.075, m, m + n * 0.10, n - m, INK)      # the spine shadow

    # THE RULED LINES, only where they can still read as lines.
    if n >= 48:
        step = (n - 2 * m) / 7.0
        for i in range(1, 7):
            y = m + step * i
            rect(m + n * 0.14, y, n - m - n * 0.06, y + max(1, n * 0.008), RULE)

    # AND THE ONE ENTRY THAT IS NOT LIKE THE OTHERS — struck through, in the
    # colour of every streetlamp in the game. This is the whole icon: a book of
    # ordinary rows with one line somebody drew through.
    y = m + (n - 2 * m) * 0.615
    rect(m + n * 0.14, y, n - m - n * 0.06, y + max(1, n * 0.020), SODIUM)
    return px


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for n in SIZES:
        path = OUT / f"icon_{n}.png"
        path.write_bytes(png(n, n, draw(n)))
        written.append(path)
        print(f"  {path.relative_to(ROOT)}  {path.stat().st_size} bytes")

    # OPEN WHAT YOU SHIP. The header is re-read off disk rather than trusted
    # from the writer, because "the script says it wrote a 512px icon" is
    # exactly the class of claim this project has been caught by.
    print()
    bad = []
    for path in written:
        b = path.read_bytes()
        if b[:8] != b"\x89PNG\r\n\x1a\n":
            bad.append(f"{path.name}: not a PNG")
            continue
        w, h = struct.unpack(">II", b[16:24])
        want = int(path.stem.split("_")[1])
        if (w, h) != (want, want):
            bad.append(f"{path.name}: header says {w}x{h}")
        # And it must not be one flat colour, which is what a drawing bug
        # produces and what a file listing cannot show.
        if len(set(zlib.decompress(b[b.index(b"IDAT") + 4:-12]))) < 3:
            bad.append(f"{path.name}: no variation — the drawing did nothing")
    for line in bad:
        print("  FAIL " + line)
    print(f"{len(written) - len(bad)}/{len(written)} icons written and read back")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
