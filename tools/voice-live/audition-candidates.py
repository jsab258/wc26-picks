#!/usr/bin/env python3
"""RENDER ONE WORD WITH EVERY CANDIDATE, SO A PICK CANNOT PAD.

    python tools/voice-live/audition-candidates.py --who rocco
    python tools/voice-live/audition-candidates.py --selftest

WHY. Rendering "No." in all 23 cast voices found four that take 1.4 to 2.0
seconds over a word the other nineteen say in under one — Rocco among them,
and the token count moves with the duration, so the model is GENERATING more
rather than the decoder stretching it. The conditioning is the variable, so
the reference clip is the lever.

Which means a casting decision has a property nobody could hear when it was
made. Jafar picked Rocco on timbre, correctly, from a page that could not
tell him this candidate would put half a second of vowel in front of every
short line. The street is mostly interjections, so that is most of what the
game will ever say.

WHAT THIS DOES. For each candidate clip on the shortlist it conditions the
model on that clip, speaks one short word, and reports how long the render
came out. Then it speaks a real line with the ones that behaved, into a
single file, in a printed order. So the listening pass happens over
candidates that are already known not to pad, and the ear is asked the
question only an ear can answer.

THE SHORT WORD IS THE MEASUREMENT AND THE LONG LINE IS THE AUDITION, and
they are separate on purpose. Duration against text length is the only
reading that separated the four bad voices from the nineteen good ones —
`headMs` and `parts` were printed for all 23 and neither did. A one-word
line is the case where that reading is unambiguous: there is no pause
between words for it to mistake for a filler.

IT DOES NOT PICK. It narrows. Which voice a character has is Jafar's, and
this exists so that choice is made from options that all work.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "tools" / "voice-fetch" / "ledger-voices-out"
OUT = ROOT / "game-design" / "voice-live"
WORD = "No."
LINE = "Seen the van again. Thursday, same as last Thursday."
GAP_SECONDS = 0.6


def candidates(who, root=None):
    """Every candidate clip for a character, in shortlist order.

    Ordered by the NUMBER in the filename rather than by string sort, so
    candidate 10 does not land between 1 and 2 — the numbers are what Jafar
    types and what `--install` looks up, and a listing that renumbers them
    would make a pick mean something different to each side.
    """
    base = (root or CANDIDATES) / who
    if not base.is_dir():
        return []
    found = []
    for q in base.iterdir():
        if not q.is_file() or q.suffix.lower() != ".wav":
            continue
        stem = q.stem
        if not stem.startswith("candidate-"):
            continue
        try:
            n = int(stem.split("-", 1)[1])
        except ValueError:
            continue
        found.append((n, q))
    found.sort()
    return found


def pads(seconds, median):
    """Whether a render is long enough to be carrying a filler.

    THE BOUND IS THE MEASURED DISTRIBUTION, NOT A GUESS. Twenty-three
    renders of "No." came in at 0.56 shortest, 0.84 median, 2.04 longest,
    and the four Jafar's fault lives in sit at 1.40 and above — 1.67x the
    median and up, with a clean gap below them at 1.20. Half again as long
    as the middle is inside that gap, and it is stated as a multiple of the
    run's OWN median rather than a constant so a different word or a faster
    machine does not silently move it.
    """
    return seconds > median * 1.5


def report(rows):
    """The table, and which candidates survive it."""
    if not rows:
        return [], "no candidates"
    secs = sorted(r[1] for r in rows)
    median = secs[len(secs) // 2]
    clean = [r for r in rows if not pads(r[1], median)]
    return clean, median


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", default="rocco")
    ap.add_argument("--word", default=WORD)
    ap.add_argument("--line", default=LINE)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    found = candidates(a.who)
    if not found:
        print(f"  no candidates for '{a.who}' under {CANDIDATES / a.who}")
        print("  run the fetcher for that character first.")
        return 1
    print(f"  {len(found)} candidate(s) for {a.who}")

    try:
        import numpy as np
        import soundfile as sf
        import torch
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import export_probe
        from chatterbox.models.s3gen.const import S3GEN_SR
    except ImportError as e:
        print(f"  cannot run: {e}")
        print("  This needs chatterbox and its weights — run it from the")
        print("  environment the export bat built.")
        return 2

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = export_probe.load_model(dev)

    # THE CLIP THAT IS ACTUALLY CAST, MEASURED IN THE SAME BREATH.
    #
    # The first audition said none of Rocco's six candidates pad: 0.44 to
    # 0.82s, median 0.68. The 23-voice sweep said Rocco takes 1.40s over the
    # same word. Same character, same text, twice the duration — so one of
    # the two runs is not measuring what it claims.
    #
    # TWO THINGS DIFFER AND ONLY ONE CAN BE THE CAUSE. The sweep goes through
    # the exported graphs and our own sampler with precomputed conditioning;
    # this goes through chatterbox's `generate()` with the candidate file. It
    # also reads a different FILE — the installed clip is
    # `picked-clips/rocco.p227.mp3` and the shortlist holds
    # `candidate-01.wav`. Measuring the installed clip HERE holds the code
    # path fixed and moves only the file, which is the whole experiment.
    #
    # If it lands near the candidates, the clip is innocent and the padding
    # belongs to our pipeline. If it lands near 1.40s, the installed file is
    # not what the shortlist offered and the fix is a re-install.
    installed = None
    clips_dir = ROOT / "game-design" / "picked-clips"
    if clips_dir.is_dir():
        hits = sorted(q for q in clips_dir.iterdir()
                      if q.is_file() and q.name.split(".")[0] == a.who)
        installed = hits[0] if hits else None

    rows = []
    if installed is not None:
        model.prepare_conditionals(str(installed))
        with torch.inference_mode():
            wav = model.generate(a.word).squeeze(0).cpu().numpy()
        secs = len(wav) / model.sr
        print(f"    INSTALLED {installed.name}: \"{a.word}\" in {secs:.2f}s")
        rows_installed = secs
    else:
        rows_installed = None
        print(f"    (no installed clip for {a.who} to compare against)")

    for n, clip in found:
        model.prepare_conditionals(str(clip))
        with torch.inference_mode():
            wav = model.generate(a.word).squeeze(0).cpu().numpy()
        secs = len(wav) / model.sr
        rows.append((n, secs, clip))
        print(f"    candidate {n:2d}: \"{a.word}\" in {secs:.2f}s")

    clean, median = report(rows)
    print(f"\n  median {median:.2f}s — a candidate over {median * 1.5:.2f}s "
          f"is carrying a filler")
    if not clean:
        # A REFUSAL THAT SAYS SO. Every candidate padding is a real answer
        # about this speaker and must not read as "nothing to listen to".
        print(f"  ! EVERY candidate for {a.who} pads. That is a finding about")
        print(f"    the speaker rather than the pick — fetch more with")
        print(f"    --candidates, or this character needs a different voice.")
        return 1
    print(f"  {len(clean)} of {len(rows)} do not pad: "
          + ", ".join(str(r[0]) for r in clean))

    # AND NOW THE PART ONLY AN EAR CAN DO, over survivors only.
    pieces, order = [], []
    gap = np.zeros(int(GAP_SECONDS * S3GEN_SR), dtype=np.float32)
    for n, secs, clip in clean:
        model.prepare_conditionals(str(clip))
        with torch.inference_mode():
            wav = model.generate(a.line).squeeze(0).cpu().numpy()
        pieces.append(wav.astype(np.float32))
        pieces.append(gap)
        order.append(n)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"audition-{a.who}.wav"
    sf.write(str(dest), np.concatenate(pieces), S3GEN_SR)
    # THE ORDER GOES IN A FILE, NOT ONLY IN THE LOG.
    #
    # The first run of this worked, wrote its wav, and its findings never
    # arrived: the sampler prints a progress line per step and the result
    # file's cap evicted every line the tool had written. A 28-second
    # audition with no list of which candidate is which is unusable — Jafar
    # cannot say "number 4" about audio he cannot index.
    #
    # A log is a channel with a length limit somebody else controls; a file
    # in the repository is the one this project can always read. So the
    # answer is written where it cannot be crowded out, and the log keeps a
    # copy for whoever is watching the window.
    note = OUT / f"audition-{a.who}.txt"
    lines = [f"audition for {a.who} — \"{a.word}\" timed, then \"{a.line}\"",
             f"median {median:.2f}s, padding above {median * 1.5:.2f}s", ""]
    if rows_installed is not None:
        lines.append(f"  INSTALLED {installed.name}: {rows_installed:.2f}s"
                     + ("  PADS" if pads(rows_installed, median) else ""))
        lines.append("")
    for n, secs, _ in rows:
        mark = "  " if not pads(secs, median) else "  PADS"
        lines.append(f"  candidate {n:2d}: {secs:.2f}s{mark}")
    lines.append("")
    lines.append("in the wav, in this order, " + str(GAP_SECONDS)
                 + "s apart: " + ", ".join(str(o) for o in order))
    note.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n  wrote {dest.name} — candidates in this order: "
          + ", ".join(str(o) for o in order))
    print(f"  and {note.name}, which a log cap cannot evict")
    print(f"  {GAP_SECONDS}s between each. Pick by sound; they all behave.")
    return 0


def selftest():
    import shutil
    import tempfile
    ok = fails = 0

    def check(cond, what, detail=""):
        nonlocal ok, fails
        if cond:
            ok += 1
            print(f"  ok   {what}")
        else:
            fails += 1
            print(f"  FAIL {what}" + (f" — {detail}" if detail else ""))

    print("audition-candidates — narrowing a shortlist by measurement:")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="ledger-audition-"))
    try:
        d = tmp / "rocco"
        d.mkdir(parents=True)
        for n in (1, 2, 10, 3):
            (d / f"candidate-{n:02d}.wav").write_bytes(b"x")
        (d / "notes.txt").write_bytes(b"x")
        got = [n for n, _ in candidates("rocco", root=tmp)]
        check(got == [1, 2, 3, 10],
              "CANDIDATES COME BACK IN NUMBER ORDER, so 10 does not sort "
              "between 1 and 2 — the number IS what gets typed as the pick",
              str(got))
        check(candidates("nobody", root=tmp) == [],
              "and a character with no shortlist returns nothing rather "
              "than failing")

        # The bound, both ways, against the real distribution it came from.
        rows = [(1, 0.56), (2, 0.84), (3, 0.88), (4, 1.40)]
        clean, median = report(rows)
        check([r[0] for r in clean] == [1, 2, 3],
              "A CANDIDATE HALF AGAIN LONGER THAN THE MEDIAN IS REFUSED — "
              "1.40s against a 0.84s middle is Rocco's actual fault",
              f"median {median}")
        check(len(clean) == 3,
              "AND THE ONES THAT BEHAVE ALL SURVIVE, which is the half that "
              "matters: a bound that refused everything would end casting "
              "while looking like caution")
        check(not pads(0.84, 0.84) and pads(1.30, 0.84),
              "the bound sits between them and is a multiple of the run's "
              "own median, not a constant that a slower word would trip")
        clean2, _ = report([])
        check(clean2 == [], "and an empty shortlist is empty, not an error")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\naudition-candidates --selftest: "
          f"{'PASS' if not fails else str(fails) + ' FAILED'} "
          f"— {ok + fails} checks")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
