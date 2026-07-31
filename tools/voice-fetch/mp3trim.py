"""Cut an MPEG-1/2 Layer III file at a frame boundary. No decoder needed.

An mp3 is a sequence of self-describing frames. Each starts with 11 sync bits
and carries its own bitrate, sample rate and padding, from which the frame's
byte length and duration follow. Keeping whole frames up to a time budget and
dropping the rest is a valid, playable file — no re-encode, so no second
generation of lossy artefacts on a clip somebody is judging a VOICE from.
"""
BITRATES = {  # V1L3, V2L3 (kbps), indexed by the 4-bit field
    3: [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0],
    2: [0,8,16,24,32,40,48,56,64,80,96,112,128,144,160,0],
    0: [0,8,16,24,32,40,48,56,64,80,96,112,128,144,160,0],
}
RATES = {3: [44100,48000,32000], 2: [22050,24000,16000], 0: [11025,12000,8000]}
SPF = {3: 1152, 2: 576, 0: 576}   # samples per frame, layer III


def frames(b):
    i = 0
    # Skip an ID3v2 tag if present; its size is 4 syncsafe bytes.
    if b[:3] == b"ID3":
        i = 10 + int.from_bytes(bytes(x & 0x7F for x in b[6:10]), "big")
    n = len(b)
    while i + 4 <= n:
        if b[i] != 0xFF or (b[i + 1] & 0xE0) != 0xE0:
            i += 1
            continue
        ver = (b[i + 1] >> 3) & 0x03          # 3=MPEG1, 2=MPEG2, 0=MPEG2.5
        layer = (b[i + 1] >> 1) & 0x03        # 1 = Layer III
        bi = (b[i + 2] >> 4) & 0x0F
        si = (b[i + 2] >> 2) & 0x03
        pad = (b[i + 2] >> 1) & 0x01
        if layer != 1 or ver == 1 or bi in (0, 15) or si == 3:
            i += 1
            continue
        rate = RATES[ver][si]
        kbps = BITRATES[ver][bi]
        length = (144000 * kbps // rate if ver == 3
                  else 72000 * kbps // rate) + pad
        if length <= 4:
            i += 1
            continue
        yield i, length, SPF[ver] / rate
        i += length


def trim(path, seconds):
    b = path.read_bytes()
    start, spent, end = None, 0.0, None
    first = True
    for off, length, dur in frames(b):
        if first:
            first = False
            # DROP THE XING/INFO FRAME. It is a silent header frame carrying
            # the ORIGINAL frame count, and browsers read the duration from
            # it — so a trimmed clip kept announcing its old length and drew
            # a seek bar twice as long as the audio. Without it the stream is
            # plain CBR and the duration falls out of bytes over bitrate,
            # which is the truth.
            if b[off:off + length].find(b"Xing") >= 0 \
                    or b[off:off + length].find(b"Info") >= 0:
                continue
        if start is None:
            start = off
        if spent + dur > seconds:
            end = off
            break
        spent += dur
    if start is None:
        return b, 0.0                 # not parseable — hand back the original
    return b[start:end] if end else b[start:], spent
