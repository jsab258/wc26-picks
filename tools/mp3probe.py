"""How loud is an mp3, without decoding it.

WHY THIS IS NOT `just decode it`. There is no decoder in this container —
no ffmpeg, no numpy, no soundfile, no pydub — and adding one to satisfy a
check means CI installs it too. But the question a shape check actually asks
about a voice clip is not "what does it sound like", it is "is there anything
in here at all", and that one is answerable from the bitstream.

Every Layer III frame carries `part2_3_length` in its side info: the number of
bits the encoder spent on the actual audio for that granule, before any
padding. Digital silence costs almost nothing to encode, so a silent frame's
part2_3_length collapses toward zero while the frame keeps its constant CBR
size on disk. The file size tells you nothing; this tells you everything the
check needs.

MPEG-1 has two granules per frame and 9-bit `main_data_begin`; MPEG-2/2.5 has
one granule and 8 bits. The VCTK clips this was written for are 24 kHz, which
is MPEG-2, so the LSF path is the one under test — the MPEG-1 path is written
from the spec and is exercised only if a 44.1 kHz clip ever arrives.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "voice-fetch"))
from mp3trim import frames                                      # noqa: E402


class Bits:
    """MSB-first bit reader over a bytes slice."""

    def __init__(self, b):
        self.b, self.pos = b, 0

    def read(self, n):
        v = 0
        for _ in range(n):
            byte = self.b[self.pos >> 3]
            v = (v << 1) | ((byte >> (7 - (self.pos & 7))) & 1)
            self.pos += 1
        return v


def frame_bits(b, off, ver, channels):
    """Bits the encoder spent on audio in this frame. None if unreadable."""
    # 4-byte header, plus 2 bytes of CRC when the protection bit is CLEAR.
    side = off + 4 + (2 if not (b[off + 1] & 0x01) else 0)
    granules = 2 if ver == 3 else 1
    need = {(3, 1): 17, (3, 2): 32, (2, 1): 9, (2, 2): 17}.get((ver, channels))
    if need is None or side + need > len(b):
        return None
    r = Bits(b[side:side + need])
    r.read(9 if ver == 3 else 8)                      # main_data_begin
    r.read(channels if ver == 3 else channels * 0 + (1 if channels == 1 else 2))
    if ver == 3:                                      # scfsi, MPEG-1 only
        for _ in range(channels):
            r.read(4)
    total = 0
    for _ in range(granules):
        for _ in range(channels):
            total += r.read(12)                       # part2_3_length
            r.read(9)                                 # big_values
            r.read(8)                                 # global_gain
            r.read(9 if ver == 3 else 9)              # scalefac_compress
            if r.read(1):                             # window_switching_flag
                r.read(2); r.read(1)
                for _ in range(2):
                    r.read(5)
                for _ in range(3):
                    r.read(3)
            else:
                for _ in range(3):
                    r.read(5)
                r.read(4)
                r.read(3)
            if ver == 3:
                r.read(1)                             # preflag, MPEG-1 only
            r.read(1)                                 # scalefac_scale
            r.read(1)                                 # count1table_select
    return total


def probe(path):
    """(duration_s, rate_hz, channels, frames, quiet_fraction, mean_bits)."""
    b = pathlib.Path(path).read_bytes()
    dur, rate, chans, spent, n = 0.0, 0, 0, [], 0
    for off, length, secs in frames(b):
        ver = (b[off + 1] >> 3) & 0x03
        si = (b[off + 2] >> 2) & 0x03
        mode = (b[off + 3] >> 6) & 0x03
        chans = 1 if mode == 3 else 2
        rate = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000],
                0: [11025, 12000, 8000]}[ver][si]
        # THE FIRST FRAME IS NOT AUDIO when it is a Xing/Info header: it is a
        # zero-payload frame carrying the VBR table, and counting it as silence
        # makes every well-formed file look 1/300th quiet.
        tag = b[off:off + length]
        if n == 0 and (b"Xing" in tag[:64] or b"Info" in tag[:64]):
            n += 1
            continue
        dur += secs
        n += 1
        bits = frame_bits(b, off, ver, chans)
        if bits is not None:
            spent.append(bits)
    if not spent:
        return dur, rate, chans, n, 1.0, 0.0
    # A frame under this many bits of audio has nothing in it.
    #
    # READ OFF THE MEASURED SERIES, not picked. Across the 19 cast clips a
    # speech frame spends 1,100-2,500 bits and averages ~1,400; the quiet ones
    # come in at 0-30. Forty sits in a gap two orders of magnitude wide, which
    # is the only kind of threshold worth having.
    #
    # And it was checked rather than assumed: dumping the per-frame series for
    # crowd_m3 puts every quiet frame in two runs, at 87-94 and 181-188 out of
    # 395 — the pauses between the three VCTK utterances the clip was spliced
    # from. It finds silence exactly where silence provably is.
    quiet = sum(1 for s in spent if s < 40) / len(spent)
    return dur, rate, chans, n, quiet, sum(spent) / len(spent)


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        d, r, c, n, q, m = probe(arg)
        print(f"{pathlib.Path(arg).name:<26} {d:6.2f}s {r:6d}Hz {c}ch "
              f"{n:5d} frames  quiet {q * 100:5.1f}%  mean {m:6.0f} bits")
