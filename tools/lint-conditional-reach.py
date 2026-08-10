#!/usr/bin/env python3
"""A FILE BEHIND `#if` STILL NEEDS SOMEBODY TO CALL IT.

    python3 tools/lint-conditional-reach.py
    python3 tools/lint-conditional-reach.py --selftest

`Game/OnnxSpeech.cs` was written, compiled against the real runtime, and
constructed by nothing. `Audio.Backend` was null and always would have been.
It survived a Windows build that PASSED, because a null backend and a working
backend with no model produce exactly the same verdict.

NOTHING COULD HAVE CAUGHT IT. The reach check walks the Game layer for calls
into Core; this is a Game type with no caller, which it does not ask about.
ShapeCheck now parses conditional code but only reports diagnostics, and an
uncalled class is not a diagnostic. And the file is behind `#if LEDGER_ONNX`,
so every tool that skips disabled regions skipped it entirely.

So: a type declared inside a conditional block must be NAMED somewhere other
than its own file. That is a weak claim — naming is not calling — but it is
exactly the distance between "this exists" and "this is reachable", and it is
the distance that was missing. Anything stronger needs a compiler with the
symbol defined, which `ledger/BackendCheck` does for compilation and cannot do
for reachability.

The accepting case is today's repository. The rejecting case is buildable:
remove the one reference and it fails, which the selftest does.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
GAME = ROOT / "ledger" / "Assets" / "Scripts" / "Game"


def conditional_types(text):
    """TOP-LEVEL types declared inside a `#if` region of one file.

    NESTED ONES ARE NOT THE QUESTION, and the first version asked about them
    anyway: it flagged `Gauss`, a private struct inside `OnnxSpeech` that
    generates the decoder's noise and is used ten lines below its own
    declaration. A helper inside a class does not need an outside caller — its
    reachability is its parent's. Only a type nothing outside its file can
    name is the fault this looks for.

    Depth is counted in braces rather than parsed, which is enough here: this
    codebase is Allman, so a namespace opens at depth 0 and its types sit at
    depth 1. Anything deeper is nested in something.
    """
    out, cond, depth = [], 0, 0
    for line in text.splitlines():
        st = line.strip()
        if st.startswith("#if"):
            cond += 1
        elif st.startswith("#endif"):
            cond = max(0, cond - 1)
        elif cond > 0 and depth <= 1:
            m = re.match(r"(?:public |internal |sealed |static |abstract |partial )*"
                         r"(?:class|struct|interface|enum)\s+(\w+)", st)
            if m:
                out.append(m.group(1))
        if not st.startswith("//"):
            depth += line.count("{") - line.count("}")
    return out


def audit(say):
    bad = []
    files = sorted(GAME.glob("*.cs"))
    checked = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        types = conditional_types(text)
        if not types:
            continue
        for t in types:
            checked += 1
            # NAMED ANYWHERE ELSE IN THE GAME LAYER. A type only its own file
            # mentions cannot be constructed by anything, whatever the symbol.
            others = [g for g in files
                      if g != f and re.search(r"\b%s\b" % re.escape(t),
                                              g.read_text(encoding="utf-8"))]
            if others:
                say(f"  ok    {t} ({f.name}) is named by "
                    f"{', '.join(g.name for g in others[:3])}")
            else:
                bad.append(f"{t} in {f.name} is behind #if and nothing else "
                           f"names it — it can never run")
                say(f"  FAIL  {bad[-1]}")
    # A DENOMINATOR. Zero conditional types and zero unreachable ones print
    # the same otherwise, and this whole file exists because of that shape.
    say(f"lint-conditional-reach: {len(bad)} unreachable, "
        f"{checked} conditional type(s) checked in {len(files)} Game file(s)")
    return bad


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(("  ok    " if ok else "  FAIL  ") + what + (f"   [{got}]" if got else ""))
        ran.append(what)
        if not ok:
            fails.append(what)

    quiet = []
    bad = audit(quiet.append)
    check(not bad, "today's Game layer passes", "; ".join(bad[:2]))
    check(any("conditional type(s) checked" in l and " 0 conditional" not in l
              for l in quiet),
          "and it actually examined something — a zero here would be the same "
          "silence the check exists to break",
          quiet[-1] if quiet else "no output")

    # THE REJECTING CASE, BUILT BY REMOVING THE ONE REFERENCE. This is the
    # exact state the repository was in before the backend was wired up.
    target = GAME / "Audio.cs"
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(original.replace("OnnxSpeech", "NothingAtAll"),
                          encoding="utf-8")
        bad2 = audit(lambda _s: None)
        check(any("OnnxSpeech" in b for b in bad2),
              "and with its only caller removed, OnnxSpeech is reported "
              "unreachable", "; ".join(bad2[:1]) or "nothing flagged")
    finally:
        target.write_text(original, encoding="utf-8")

    print(f"\nlint-conditional-reach --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    return 1 if audit(print) else 0


if __name__ == "__main__":
    sys.exit(main())
