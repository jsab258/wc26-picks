"""One file, no server, no network — the page as it has to arrive on a phone.

The repo page uses relative <audio src>, which needs a web server. A phone
opening a link needs the audio INSIDE the document, so every clip becomes a
data: URI. That is what forces the trim: all 114 clips whole would be 10 MB
of mp3 and 13.5 MB once base64 has added a third.
"""
import base64, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from mp3trim import trim
import ledger_voice_fetch as L

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "voice-candidates"
PER = int(sys.argv[1]) if len(sys.argv) > 1 else 4
SECS = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
OUT = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path("listen-standalone.html")

made, raw, kept = {}, 0, 0
for c in L.CAST:
    files = []
    for i, f in enumerate(sorted((SRC / c["id"]).glob("candidate-*.mp3"))[:PER], 1):
        raw += f.stat().st_size
        data, secs = trim(f, SECS)
        kept += len(data)
        files.append(dict(
            n=i, seconds=round(secs, 1),
            file="data:audio/mpeg;base64," + base64.b64encode(data).decode("ascii")))
    made[c["id"]] = files

L.PICKS = pathlib.Path("/tmp/standalone-picks.txt")
tmp = pathlib.Path("/tmp/standalone-build"); tmp.mkdir(exist_ok=True)
L.build_page(L.CAST, made, tmp, "vctk (parquet mirror)")
html = (tmp / "listen.html").read_text(encoding="utf-8")
OUT.write_text(html, encoding="utf-8")
print(f"{sum(len(v) for v in made.values())} clips, {PER} per character, {SECS:g}s each")
print(f"mp3 {raw/1e6:.1f} MB -> trimmed {kept/1e6:.1f} MB -> page {OUT.stat().st_size/1e6:.1f} MB")
