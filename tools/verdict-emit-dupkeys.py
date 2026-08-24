#!/usr/bin/env python3
"""Two keys with one name, caught BEFORE the round trip.

WHY THIS EXISTS, AND WHY IT IS NOT `verdict-dupkeys.py`
------------------------------------------------------
`tools/verdict-dupkeys.py` reads the LANDED verdict and reports keys that are
ambiguous in it.  That is the right check and it is one Windows round trip too
late: the collision is written in C#, dispatched, built for a quarter of an
hour, committed, pulled, and only then visible.  This reads the SOURCE and
answers the same question in a second.

MEASURED, on the commit this shipped beside.  Wiring `Core/DoorSwing` added
`doors={DoorHost.Count}/...` to the done line.  `doors=` was already there —
`WorldBuilder.Doors`, the count of door geometry built — three hundred lines
further down the SAME `Debug.Log`.  Nothing would have failed.  The verdict
would have carried two `doors=` values and `verdict-read.py` would have handed
back whichever came first, which is the exact quietly-wrong answer that tool
exists to prevent.  And the damage is not to the new key: it is to the OLD one,
which had been readable for weeks and would silently stop being.

It was caught by eye, and this file is a list of what happens when a rule
depends on that.

WHAT A COLLISION IS HERE
------------------------
Exactly what `verdict-read.py` would confuse, and that is not a guess — it is
that tool's own regex, `(?<![\\w])KEY=`.  Two consequences worth stating
because both were measured rather than assumed:

  * `dia/hi=0.40` DOES collide with `hi=1.45`.  A slash is not a word
    character, so a search for `hi=` matches inside it.  `TrafficHost`'s wheel
    line carried that pair and `Traffic: wheels` is named in CLAUDE.md's own
    table of ambiguous readings.  Renamed to `diaPerHi=` / `diaPerLen=`.
  * a key repeated across SEPARATE `Debug.Log` calls is not this tool's
    business.  Those land on different verdict lines, which is the cross-line
    case `verdict-dupkeys.py` already covers with its family test.  This one
    asks only: does one emitted LINE carry one name twice.

COMMENTS ARE NOT CODE — AND THE FIRST VERSION OF THIS TOOL GOT IT WRONG
-----------------------------------------------------------------------
Run before comment stripping, it reported `captions` duplicated on the done
line.  There is ONE `captions=` in the whole file.  The other was in the
comment three lines above it, explaining what the number is for, and quoting
the key to do so: `// ITEMISED for the same reason the ring is: "captions=0"`.

This project has the mirror of that written down twice already — `$"..."` IS
code and `lint-shadow` threw the done line away for years because it looked
like prose; and slopcheck counted a comment that QUOTED a banned phrase as a
use of it.  So the scanner tracks strings, verbatim strings, interpolated
strings, char literals, line comments and block comments in one pass, blanking
comments to spaces of equal length so every line number stays exact.

AND AN INTERPOLATION HOLE IS NOT LITERAL TEXT.  `$"n={Lookup["a=1"]}"` emits
whatever `Lookup` returns, not `a=1`, so `{...}` spans are removed before the
keys are read — balanced, and honouring `{{`/`}}`.

RUN AGAINST THE ERROR IT WAS WRITTEN FOR, WHICH IS THE HALF THAT GOES UNRUN
---------------------------------------------------------------------------
`lint-filetype` passed the whole repository and then scored zero on the very
line that prompted it.  So `--selftest` asserts, in order: a clean call is
ACCEPTED (rule 5b, and it is first on purpose); the real `doors=` collision is
REJECTED; a comment quoting a key does not count; an interpolation hole does
not count; and `dia/hi=` beside `hi=` DOES count.

The live codebase is the accepting case and it is the best one available.
There is no baseline list, because there is nothing left to baseline: the two
real hits are fixed in the same commit that adds this.  A list of blessed
collisions would decay exactly like the reasons on the reach ledger do.

Usage:
    tools/verdict-emit-dupkeys.py [root]     default: ledger/Assets/Scripts
    tools/verdict-emit-dupkeys.py --selftest
"""

import collections
import pathlib
import re
import sys

DEFAULT_ROOT = "ledger/Assets/Scripts"
EMITTERS = ("Debug.Log", "Debug.LogWarning", "Debug.LogError")

# verdict-read.py's own rule, so this cannot disagree with the reader it
# protects. A key starts where a word character does not precede it.
KEY = re.compile(r"(?<![\w])([A-Za-z]\w+)=")


def blank_comments(src):
    """Return `src` with every comment replaced by spaces, same length.

    Same length matters: line and column numbers stay exact, and the paren
    walker below can run on the result and still point at real source.
    """
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == '"':
            verbatim = i > 0 and src[i - 1] == "@"
            i += 1
            while i < n:
                if verbatim:
                    if src[i] == '"':
                        if i + 1 < n and src[i + 1] == '"':
                            i += 2
                            continue
                        break
                else:
                    if src[i] == "\\":
                        i += 2
                        continue
                    if src[i] == '"':
                        break
                i += 1
            i += 1
            continue
        if c == "'":
            i += 1
            while i < n and src[i] != "'":
                i += 2 if src[i] == "\\" else 1
            i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                out[i] = " "
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            while i < n and not (src[i] == "*" and i + 1 < n and src[i + 1] == "/"):
                if src[i] != "\n":
                    out[i] = " "
                i += 1
            for j in range(i, min(i + 2, n)):
                out[j] = " "
            i += 2
            continue
        i += 1
    return "".join(out)


def call_literals(src, open_paren):
    """From the index of `(`, walk to its match; return the literal strings
    inside as (text, interpolated) pairs."""
    depth, i, n = 0, open_paren, len(src)
    lits = []
    while i < n:
        c = src[i]
        if c == '"':
            interp = i > 0 and src[i - 1] in "$@" and (
                src[i - 1] == "$" or (i > 1 and src[i - 2] == "$"))
            j, buf = i + 1, []
            while j < n:
                if src[j] == "\\":
                    buf.append(src[j:j + 2])
                    j += 2
                    continue
                if src[j] == '"':
                    break
                buf.append(src[j])
                j += 1
            lits.append(("".join(buf), interp))
            i = j + 1
            continue
        if c == "'":
            i += 1
            while i < n and src[i] != "'":
                i += 2 if src[i] == "\\" else 1
            i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return lits, i
        i += 1
    return lits, i


_BRACE = re.compile(r"\{[^{}]*\}")


def strip_holes(text):
    """Remove `{...}` interpolation holes, innermost first, honouring {{ }}."""
    text = text.replace("{{", "\x01").replace("}}", "\x02")
    prev = None
    while prev != text:
        prev = text
        text = _BRACE.sub("\x00", text)
    return text.replace("\x01", "{").replace("\x02", "}")


def findings_in(src, name="<src>"):
    """(path, line, segment, [duplicated keys]) for every emitted line."""
    clean = blank_comments(src)
    out = []
    for m in re.finditer(r"\b(?:" + "|".join(re.escape(e) for e in EMITTERS)
                         + r")\s*\(", clean):
        lits, _ = call_literals(clean, m.end() - 1)
        text = "".join(strip_holes(t) if interp else t for t, interp in lits)
        for seg, part in enumerate(text.split("\\n")):
            counts = collections.Counter(
                k for k in KEY.findall(part) if len(k) > 1)
            dup = sorted(k for k, v in counts.items() if v > 1)
            if dup:
                out.append((name, clean[:m.start()].count("\n") + 1, seg, dup))
    return out, sum(1 for _ in re.finditer(
        r"\b(?:" + "|".join(re.escape(e) for e in EMITTERS) + r")\s*\(", clean))


def selftest():
    # 1. THE ACCEPTING CASE FIRST, because the expensive failure is a
    #    validator nothing survives.
    ok = 'Debug.Log($"SimDirector: done. a={x} b={y} cLong={z}");'
    f, n = findings_in(ok)
    assert f == [], f
    assert n == 1, n

    # 2. The real one: `doors=` twice on one enormous done line.
    bad = ('Debug.Log($"SimDirector: done. doors={DoorHost.Count} " +\n'
           '          $"other={q} " +\n'
           '          $"doors={WorldBuilder.Doors} ");')
    f, _ = findings_in(bad)
    assert [x[3] for x in f] == [["doors"]], f

    # 3. A comment QUOTING a key is prose. Measured: this exact shape made the
    #    first version report `captions` where the file has one.
    com = ('Debug.Log(\n'
           '    // ITEMISED for the same reason the ring is: "captions=0"\n'
           '    $"captions={n} hushes={h}");')
    f, _ = findings_in(com)
    assert f == [], f

    # 3b. ...and a block comment likewise.
    blk = 'Debug.Log(/* captions=0 is not a use */ $"captions={n}");'
    assert findings_in(blk)[0] == [], findings_in(blk)[0]

    # 4. An interpolation HOLE is not literal text.
    hole = 'Debug.Log($"n={Lookup["a=1"]} a={x}");'
    assert findings_in(hole)[0] == [], findings_in(hole)[0]

    # 5. A slash does not separate keys for `verdict-read.py`, so it must not
    #    separate them here. `dia/hi=` really does collide with `hi=`.
    slash = 'Debug.Log($"Traffic: wheels hi={hi:0.00} dia/hi={r:0.00}");'
    assert [x[3] for x in findings_in(slash)[0]] == [["hi"]], findings_in(slash)[0]

    # 6. Separate calls are separate LINES — the cross-line case belongs to
    #    verdict-dupkeys.py, not here.
    two = 'Debug.Log($"a x={1}");\nDebug.Log($"b x={2}");'
    assert findings_in(two)[0] == [], findings_in(two)[0]

    # 7. `\n` inside one call starts a new emitted line.
    nl = r'Debug.Log($"x={a}\nx={b}");'
    assert findings_in(nl)[0] == [], findings_in(nl)[0]

    print("verdict-emit-dupkeys: selftest ok (7 checks, accepting case first)")
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT)
    files = sorted(root.rglob("*.cs"))
    hits, calls = [], 0
    for p in files:
        f, n = findings_in(p.read_text(encoding="utf-8"), str(p))
        hits += f
        calls += n
    for path, line, seg, dup in hits:
        where = f"{path}:{line}" + (f" (segment {seg})" if seg else "")
        print(f"{where}: {' '.join(dup)} — emitted twice on one line")
    # Rule 3b: the denominator, so "nothing found" cannot read the same as
    # "nothing was examined".
    print(f"verdict-emit-dupkeys: {len(hits)} same-line duplicate key(s) "
          f"({calls} log call(s) across {len(files)} file(s))")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
