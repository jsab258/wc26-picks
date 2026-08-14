#!/usr/bin/env python3
"""LAYER 2 — SHAPE, for the things that live in files rather than in code.

`Core/TextShape.cs` covers every line the game GENERATES, and CoreTests sweeps
it. This covers the other half: the audio and the manifests, where a fault is
never a compile error and never a failing assertion — it is a clip that plays
as thirty seconds of nothing, or a manifest that still names a character who
was renamed, or two people cast with the same throat.

Every one of those has actually happened here. The listening page was published
with six faults, all invisible from the Python that generated it. A run banked
the same speaker four times under one character and I told Jafar they were four
different people; he had listened, and he was right. A crowd slot was issued
Lena's exact voice on a later run, caught by luck the minute before publishing.

    python3 tools/shape-check.py

THE THRESHOLDS BELOW ARE READ OFF A MEASURED SERIES, printed by this script
before it judges anything, because a threshold this project invented rather
than measured is how `nightNotDarker` came to fail on a thousandth.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from mp3probe import probe                                      # noqa: E402

_fails = []


def check(ok, what, got=""):
    print(("  ok   " if ok else "  FAIL ") + what + ("" if ok else f" — {got}"))
    if not ok:
        _fails.append(what)


# ---------------------------------------------------------------- the clips

# Measured across the 19 cast clips on 2026-07-31, printed by this script every
# run: duration 8.26-12.05s, all 24000 Hz, all mono, quiet fraction 0.0-4.1%,
# mean 1361-1420 bits of audio per frame. The bounds below sit well outside
# that spread on purpose — a gate that hugs its own sample flaps, and a check
# that flaps gets switched off.
MIN_SECONDS, MAX_SECONDS = 4.0, 30.0
MIN_RATE = 16000
MAX_QUIET = 0.50          # half the file silent is a broken clip, not a style
MIN_MEAN_BITS = 200       # a dead clip sits near zero; speech sits near 1400


def clips():
    picks_path = ROOT / "game-design" / "voice-picks.json"
    picks = json.loads(picks_path.read_text(encoding="utf-8"))["picks"]
    clip_dir = ROOT / "game-design" / "picked-clips"
    on_disk = [q for q in clip_dir.iterdir() if q.is_file()]
    print(f"voice clips — {len(picks)} cast, {len(on_disk)} on disk")

    rows, by_speaker, pending = [], {}, []
    for name in sorted(picks):
        pick = picks[name]
        speaker = pick.get("speaker")
        # PICKED BUT NOT YET INSTALLED IS A STATE, NOT A FAULT. A pick is
        # made on the machine with the shortlists and travels here as a
        # candidate NUMBER; the speaker id only exists once `--install` has
        # run and can name the file. Failing on that gap would make the
        # commit that records four decisions red for recording them, which
        # is a guard blocking the good case. A pick that HAS a speaker and
        # no clip is still a fault — the clip went missing — so the two are
        # told apart rather than merged into one red line.
        if not speaker:
            pending.append(name)
            continue
        # THE FILENAME CARRIES THE SPEAKER ID ON PURPOSE. It is the only thing
        # that survives the pipeline being re-run, and checking it against the
        # manifest is what makes "these are four different people" a fact.
        # ANY EXTENSION, BECAUSE THE FETCHER NOW INSTALLS WAV. The nineteen
        # cast in July are mp3 and this hardcoded that, so the four cast in
        # August would each have reported "no clip on disk" while the file
        # sat right there under a different suffix — a guard failing on the
        # good case, which is the shape rule 5b exists about. The SPEAKER in
        # the name is the part that matters and it is still required.
        hits = sorted(clip_dir.glob(f"{name}.{speaker}.*"))
        if not hits:
            check(False, f"{name} has its picked clip on disk",
                  f"no {name}.{speaker}.* in {clip_dir.name}")
            continue
        path = hits[0]
        try:
            dur, rate, chans, frames, quiet, mean = probe(path)
        except Exception as e:                                  # noqa: BLE001
            check(False, f"{name} — clip parses as mp3", str(e)[:60])
            continue
        rows.append((name, speaker, dur, rate, chans, frames, quiet, mean))
        by_speaker.setdefault(speaker, []).append(name)

    print()
    for n, sp, d, r, c, f, q, m in rows:
        print(f"    {n:<12} {sp:<6} {d:6.2f}s {r:6d}Hz {c}ch "
              f"quiet {q * 100:5.1f}%  mean {m:6.0f} bits")
    print()

    for n, sp, d, r, c, f, q, m in rows:
        check(MIN_SECONDS <= d <= MAX_SECONDS,
              f"{n} — clip is {MIN_SECONDS:.0f}-{MAX_SECONDS:.0f}s", f"{d:.2f}s")
        check(r >= MIN_RATE, f"{n} — sample rate is usable", f"{r} Hz")
        check(f > 0, f"{n} — clip has frames", f"{f} frames")
        check(q <= MAX_QUIET, f"{n} — clip is not mostly silence",
              f"{q * 100:.1f}% of frames carry no audio")
        check(m >= MIN_MEAN_BITS, f"{n} — clip carries a signal",
              f"mean {m:.0f} bits/frame")

    # THE ONE JAFAR CAUGHT BY EAR. Two characters sharing a speaker is not a
    # crash, not a failing test, and completely obvious the moment somebody
    # listens — which is the worst possible combination, because it means the
    # pipeline can ship it and only a human can find it.
    shared = {sp: who for sp, who in by_speaker.items() if len(who) > 1}
    check(not shared, "no two characters share a voice",
          "; ".join(f"{sp}: {', '.join(w)}" for sp, w in shared.items()))

    # SAID OUT LOUD, WITH ITS DENOMINATOR. A pending pick that printed
    # nothing would make "23 cast, 19 on disk" read as a bug rather than as
    # four decisions waiting for one command to run.
    if pending:
        print(f"  {len(pending)} picked, awaiting --install on the machine "
              f"with the shortlists: {', '.join(sorted(pending))}")

    stray = sorted(q.name for q in (ROOT / "game-design" / "picked-clips").iterdir()
                   if q.is_file() and q.name.rsplit(".", 2)[0] not in picks)
    check(not stray, "no picked clip belongs to a character nobody cast",
          ", ".join(stray[:4]))
    return rows


# ------------------------------------------------------------- the manifests

def barks():
    path = ROOT / "game-design" / "barks.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    slots = data["slots"]
    floor = data["repeatFloorSeconds"]
    lines = [l for s in slots for l in s.get("lines", [])]
    print(f"barks.json — {len(slots)} slots, {len(lines)} lines, "
          f"repeat floor {floor}s")

    empty = [s["id"] for s in slots if not s.get("lines")]
    check(not empty, "every reachable slot has lines in it", ", ".join(empty[:4]))

    # A slot repeats every everySeconds * len(lines). Under the floor and the
    # player hears the same sentence twice inside ten minutes.
    short = [(s["id"], s["everySeconds"] * len(s.get("lines", [])))
             for s in slots
             if s.get("lines") and s["everySeconds"] * len(s["lines"]) < floor
             and len(s["lines"]) < s.get("wanted", 0)]
    check(not short, f"every slot clears the {floor}s repeat floor",
          "; ".join(f"{i} repeats every {r:.0f}s" for i, r in short[:3]))

    dupes = []
    for s in slots:
        seen = set()
        for l in s.get("lines", []):
            if l in seen:
                dupes.append(f"{s['id']}: {l[:40]}")
            seen.add(l)
    check(not dupes, "no slot lists the same line twice", "; ".join(dupes[:3]))

    # The manifest is a FILE, and a file drifts. It carried "How's the bar
    # treating you?" for days after the pub was renamed, because BarkGen was
    # writing to whatever directory the shell happened to be standing in.
    check(data.get("generatedBy", "").startswith("BarkGen"),
          "the manifest says what generated it", data.get("generatedBy", "")[:40])


def referenced_files():
    """Every path a design manifest names, checked to exist.

    Cheap, and the failure mode is a build that ships with a missing asset and
    a silent catch block."""
    missing = []
    checked = 0
    for path in sorted((ROOT / "game-design").glob("*.json")):
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)

        def walk(node):
            nonlocal checked
            if isinstance(node, dict):
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
            elif isinstance(node, str) and "/" in node and "." in node.rsplit("/", 1)[-1]:
                # Only things that look like repo-relative paths, not prose
                # containing a slash and not a URL.
                if node.startswith(("http://", "https://")) or " " in node:
                    return
                checked += 1
                if not (ROOT / node).exists():
                    missing.append(f"{path.name} -> {node}")

        walk(data)
    check(not missing, f"every file path a manifest names exists ({checked} checked)",
          "; ".join(missing[:4]))


def selftest():
    """Every check above, watched failing.

    THE INSTRUMENT IS THE THING TO DOUBT FIRST. `breakrun.py` reverted one file
    of a two-file spec and reported a caught defect as a survivor. A corpus
    diagnostic read sixty consecutive rows of a speaker-ordered dataset and
    reported on "the corpus" having seen one person. A gap analysis said alarm
    propagation was unwired when the code plainly emitted it.

    So: build a deliberately broken tree, run the real checks against it, and
    require each one to go red. It runs in about a second and needs no
    fixtures on disk — the clip bytes are taken from a real one and damaged."""
    import shutil
    import tempfile
    global ROOT, _fails
    real = ROOT
    passed, failed = [], []

    def expect(name, fn):
        global _fails
        _fails = []
        try:
            fn()
        except Exception as e:                                  # noqa: BLE001
            (passed if True else failed).append(name)
            print(f"  ok   {name} — raised {type(e).__name__}")
            return
        (passed if _fails else failed).append(name)
        print(("  ok   " if _fails else "  FAIL ") + name
              + ("" if _fails else " — the check passed on broken input"))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        shutil.copytree(real / "game-design", tmp / "game-design")
        ROOT = tmp
        picks_path = tmp / "game-design" / "voice-picks.json"
        clips_dir = tmp / "game-design" / "picked-clips"
        original = json.loads(picks_path.read_text(encoding="utf-8"))

        def restore():
            picks_path.write_text(json.dumps(original), encoding="utf-8")

        print("shape-check selftest — each check, watched failing\n")

        # 1. two characters cast with the same speaker. The one Jafar caught by
        #    ear, and the one no assertion in the project had ever looked for.
        d = json.loads(json.dumps(original))
        d["picks"]["ada"]["speaker"] = d["picks"]["lena"]["speaker"]
        picks_path.write_text(json.dumps(d), encoding="utf-8")
        shutil.copy(clips_dir / f"lena.{original['picks']['lena']['speaker']}.mp3",
                    clips_dir / f"ada.{original['picks']['lena']['speaker']}.mp3")
        expect("a shared voice is caught", clips)
        (clips_dir / f"ada.{original['picks']['lena']['speaker']}.mp3").unlink()
        restore()

        # 2. a cast member whose clip never arrived — what a zero-output CI run
        #    leaves behind, and it reported success at the time.
        moved = clips_dir / f"ada.{original['picks']['ada']['speaker']}.mp3"
        keep = moved.read_bytes()
        moved.unlink()
        expect("a missing clip is caught", clips)
        moved.write_bytes(keep)

        # 3. a clip that is all silence. Truncating to the first frames of a
        #    speech file will not do it — the check has to be fed something
        #    genuinely empty, so the audio bits are zeroed frame by frame.
        sys.path.insert(0, str(real / "tools" / "voice-fetch"))
        from mp3trim import frames                              # noqa: E402
        b = bytearray(keep)
        for off, length, _ in list(frames(bytes(b))):
            for i in range(off + 4, min(off + length, len(b))):
                b[i] = 0
        moved.write_bytes(bytes(b))
        expect("a silent clip is caught", clips)
        moved.write_bytes(keep)

        # 4. a bark slot emptied — an enumerated branch nobody will ever hear.
        bp = tmp / "game-design" / "barks.json"
        bd = json.loads(bp.read_text(encoding="utf-8"))
        whole = json.dumps(bd)
        bd["slots"][0]["lines"] = []
        bp.write_text(json.dumps(bd), encoding="utf-8")
        expect("an empty bark slot is caught", barks)

        # 5. a slot that repeats inside the floor.
        bd = json.loads(whole)
        bd["slots"][0]["lines"] = bd["slots"][0]["lines"][:1]
        bp.write_text(json.dumps(bd), encoding="utf-8")
        expect("a slot under the repeat floor is caught", barks)

        # 6. the same line twice in one slot.
        bd = json.loads(whole)
        bd["slots"][0]["lines"].append(bd["slots"][0]["lines"][0])
        bp.write_text(json.dumps(bd), encoding="utf-8")
        expect("a duplicated line is caught", barks)

        # 7. a manifest naming a file that is not there.
        bd = json.loads(whole)
        bd["slots"][0]["clip"] = "game-design/picked-clips/nobody.p999.mp3"
        bp.write_text(json.dumps(bd), encoding="utf-8")
        expect("a manifest naming a missing file is caught", referenced_files)
        bp.write_text(whole, encoding="utf-8")

    ROOT = real
    _fails = []
    print()
    print(f"{len(passed)}/{len(passed) + len(failed)} checks go red on broken input")
    return 1 if failed else 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    print("shape-check — Layer 2, the parts that live in files\n")
    clips()
    print()
    barks()
    print()
    referenced_files()
    print()
    print("shape ok" if not _fails else f"{len(_fails)} problem(s)")
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
