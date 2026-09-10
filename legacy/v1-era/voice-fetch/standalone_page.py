"""One file, no server, no network — the page as it has to arrive on a phone.

The repo page uses relative <audio src>, which needs a web server. A phone
opening a link needs the audio INSIDE the document, so every clip becomes a
data: URI. That is what forces the trim: all 114 clips whole would be 10 MB
of mp3 and 13.5 MB once base64 has added a third.
"""
import base64, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from mp3trim import trim
import ledger_voice_fetch as L

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "voice-candidates"
PER = int(sys.argv[1]) if len(sys.argv) > 1 else 4
SECS = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
OUT = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path("listen-standalone.html")

def metadata_from_page(path):
    """Speaker id, age and accent, read back out of the committed page.

    THE STANDALONE PAGE IS THE ONE ANYBODY ACTUALLY OPENS, and the first
    version of it dropped every speaker id on the floor — it rebuilt the
    `files` dicts from the mp3s on disk and never carried the metadata across.
    So the page I published as the fix for "you cannot tell these apart" was
    itself the page you could not tell apart on. The browser check caught it
    by finding empty ids where it expected distinct ones.

    The CI page next to the clips already has them, so they are parsed back
    rather than lost or re-fetched.
    """
    out = {}
    if not path.exists():
        return out
    html = path.read_text(encoding="utf-8")
    for cid, body in re.findall(r'<section id="([a-z0-9_]+)">(.*?)</section>',
                                html, re.S):
        rows = []
        for meta in re.findall(r'class=meta>([^<]*)', body):
            bits = [b.strip() for b in meta.split("&middot;")]
            rows.append(dict(
                speaker=bits[1] if len(bits) > 1 else "",
                age=bits[2].replace("age ", "") if len(bits) > 2 else "",
                accent=bits[3] if len(bits) > 3 else ""))
        out[cid] = rows
    return out


meta = metadata_from_page(SRC / "listen.html")
made, raw, kept = {}, 0, 0
for c in L.CAST:
    files = []
    for i, f in enumerate(sorted((SRC / c["id"]).glob("candidate-*.mp3"))[:PER], 1):
        raw += f.stat().st_size
        data, secs = trim(f, SECS)
        kept += len(data)
        m = (meta.get(c["id"]) or [{}] * 99)[i - 1] if meta.get(c["id"]) else {}
        files.append(dict(
            n=i, seconds=round(secs, 1),
            speaker=m.get("speaker", ""), age=m.get("age", ""),
            accent=m.get("accent", ""),
            file="data:audio/mpeg;base64," + base64.b64encode(data).decode("ascii")))
    made[c["id"]] = files

L.PICKS = pathlib.Path("/tmp/standalone-picks.txt")
tmp = pathlib.Path("/tmp/standalone-build"); tmp.mkdir(exist_ok=True)
L.build_page(L.CAST, made, tmp, "vctk (parquet mirror)")
html = (tmp / "listen.html").read_text(encoding="utf-8")
OUT.write_text(html, encoding="utf-8")
print(f"{sum(len(v) for v in made.values())} clips, {PER} per character, {SECS:g}s each")
print(f"mp3 {raw/1e6:.1f} MB -> trimmed {kept/1e6:.1f} MB -> page {OUT.stat().st_size/1e6:.1f} MB")
# SAY IT HERE TOO. A standalone page that quietly lost the speaker ids is the
# exact failure this whole day was about.
_missing = [cid for cid, fs in made.items()
            if fs and not all(f.get("speaker") for f in fs)]
print("speaker ids on every clip" if not _missing
      else f"MISSING SPEAKER IDS: {', '.join(_missing[:8])}")
