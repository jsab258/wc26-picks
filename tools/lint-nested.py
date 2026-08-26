#!/usr/bin/env python3
"""A Core type qualified by another Core type, which is CS0426.

    python3 tools/lint-nested.py
    python3 tools/lint-nested.py --selftest      (--self-test also accepted)

WHY THIS EXISTS.

    Assets\\Scripts\\Game\\Audio.cs(52,43): error CS0426:
    The type name 'Bus' does not exist in the type 'Mixing'

`Bus` is declared BESIDE `Mixing` in `Ledger.Core`, not inside it. I wrote
`Mixing.Bus` five times because the enum is documented in `Mixing.cs`, sits
twenty lines above the class, and is only ever used with it — every reason to
believe it is nested except the one that counts.

WHY NOTHING ELSE CATCHES IT. `ShapeCheck` runs Roslyn with reference-independent
diagnostics only, which is what makes it able to run at all on a side where the
Unity assemblies do not exist. CS0426 is type RESOLUTION and needs those
references, so it is structurally invisible here — this is the class of fault
CLAUDE.md names as the one the Windows build is the first compiler for.

That makes it a twenty-eight-minute round trip, and the cost is not the error.
Three commits went out on top of this one before the verdict came back, so
every build dispatched in that window carried a Game layer that could not
compile and three separate answers moved a round trip further away.

The same shape as `lint-shadow.py`, which exists because CS0119 cost a round
trip in the same way. Both are cheap, mechanical, reference-free checks for
mistakes Roslyn can only report with references it does not have here.

WHAT IT IS NOT. It cannot resolve types either — it matches NAMES. So it only
looks at pairs where BOTH sides are top-level Core types, which is the exact
shape of the mistake and is not a shape legal C# produces: a real nested type
is not also declared at top level.

NESTED TYPES ARE EXCLUDED BY BRACE DEPTH, and that matters — `Perception` has a
nested `Attention` struct, so `Perception.Attention` is correct and must not be
flagged. Only depth-1 declarations (directly inside the namespace) count.

-------------------------------------------------------------------------------
THE PRINTED DENOMINATOR DESCRIBED THE WRONG SET, AND A CLEAN RESULT WAS
THEREFORE UNFALSIFIABLE (26 Aug).

    lint-nested: 0 nested-type errors (255 top-level Core types checked)

That line was BYTE-IDENTICAL, at exit 0, for a full 88-file sweep and for a
sweep of a real but EMPTY Game directory. Probed at `main()` level, both ways,
before anything here was changed. `255` is the REFERENCE set — the Core types
this tool compares against — and the reference set does not move when the walk
collapses to nothing. The count that would have moved, the Game files walked,
was computed and thrown away.

This is `lint-static`'s fault in a different costume, and that one rode **550
landed commit footers climbing 418 -> 560 while the walked set never left 29.**
A denominator describing a set the tool never looked at is not merely
unhelpful; it is a false claim with a number attached, which is the most
convincing kind.

THE REPAIR IS COPIED, NOT INVENTED — `tools/lint-static.py` and
`tools/lint-conditional-reach.py` are the models, and `tools/lint-avenues.py`
supplies the "no file exempt" phrasing:

  * THE COUNTS COME FROM THE WALK. `Reading.walked` is the set the scanner
    appended to itself, never a `for f in files` loop beside it. There is no
    second implementation for the two to drift apart.
  * A CHECKABLE IDENTITY IS PRINTED, so a reader verifies the accounting on
    the line instead of trusting it:
        arithmetic: 88 walked + 0 not walked = 88 .cs file(s) offered
  * THE LADDER IS PRINTED, because file count is not what this check examines.
    A regex that stopped matching leaves 88 files walked and 0 pairs examined,
    and only the second number says so. Rungs narrow left to right: pairs
    examined -> outer name is a Core type -> both sides are, which is the
    finding.
  * NOTHING MEASURED PRINTS THE WORDS and exits 2. It can no longer print
    `0 ... errors`, and its text deliberately does NOT match verify's pass
    parse, so a never-ran sweep cannot reach the footer as a zero.

WHO READS THIS LINE. `nested_types()` in `ledger/verify.py` (line 945 at
`ce37232e`; the LINE drifts, the function does not), and nothing else in the
repo:

    m = re.search(r"\\((\\d+) top-level Core types checked\\)", out)

That regex is PINNED by the selftest below, in both directions: the summary
line still matches it, and the copy kept here is still byte-identical to the
one in `verify.py`. Another lint's rewrite in this project silently dropped the
token its verify parse grepped for, which removes the denominator from every
future GREEN footer without a single red run to say so. The parenthetical is
kept VERBATIM at the end of the head line for that reason; everything new is
appended after it.

EXIT CODES
    0   walked, no candidate found
    1   at least one CS0426 candidate   (verify prints CS0426 WAITING TO HAPPEN)
    2   NOTHING MEASURED — no Core types, no Game folder, or no `.cs` file
        walked. Prints the words, never `0 ... errors`.
"""

import pathlib
import re
import signal
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from capsay import cap as _cap, NOTHING_MEASURED   # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE = ROOT / "ledger" / "Assets" / "Scripts" / "Core"
GAME = ROOT / "ledger" / "Assets" / "Scripts" / "Game"

DECL = re.compile(
    r"^\s*(?:public|internal)?\s*(?:static\s+|sealed\s+|abstract\s+|partial\s+)*"
    r"(?:class|struct|enum|interface)\s+([A-Z]\w*)")
LINE_COMMENT = re.compile(r"//.*")

# A VERBATIM COPY OF the regex in `nested_types()` in `ledger/verify.py`, kept
# here so the selftest can run the real consumer's parse against the real
# line. verify.py is the source of truth and is NOT edited from here; if the
# two ever differ the selftest says so by name, instead of the footer quietly
# losing its denominator.
VERIFY_PARSE = r"\((\d+) top-level Core types checked\)"

# TYPE POSITION ONLY, and the first version's 13 false positives are why.
#
# Matching every `X.Y` where both names are Core types flagged `Campaign.Verdict`,
# `Pressures.Rumor`, `Effects.Rumor` and `KeyKind.Payment` — all of which COMPILE
# TODAY, so all of which are members that happen to share a name with a type.
# A name-only check cannot tell those apart, and the whole live codebase
# compiling makes every hit a false positive by definition. That is the shape
# rule 5b warns about: a checker whose false positives read exactly like the
# thing it was written to find.
#
# The mistake itself only ever occurs where a TYPE is expected, because that is
# the only place a type name can appear. Three such places, and the false
# positives are in none of them:
#
#   <Mixing.Bus, int>     a generic argument
#   Mixing.Bus bus        a parameter or variable declaration
#   Mixing.Bus.Foley      a member reached THROUGH the mis-qualified type
#
# whereas `= Campaign.Verdict` and `== Pressures.Rumor` are values.
QUALIFIED = re.compile(
    # A GENERIC ARGUMENT, WHICH IS NOT THE SAME AS A CALL ARGUMENT. The first
    # narrowing accepted `(` as an opener and flagged `new AccessKey(
    # KeyKind.Payment, 60)` — an enum member in an ordinary method call. So the
    # bracket has to actually be an angle one at one end or the other:
    # `<X.Y, int>` opens with `<`, `<int, X.Y>` closes with `>`.
    r"<\s*([A-Z]\w*)\.([A-Z]\w*)\s*[,>]"
    r"|,\s*([A-Z]\w*)\.([A-Z]\w*)\s*>"
    r"|\b([A-Z]\w*)\.([A-Z]\w*)\s+[a-z_]\w*\s*[,)=;]"  # declaration
    r"|\b([A-Z]\w*)\.([A-Z]\w*)\.[A-Z]")                # member through it

SHOW = 3            # per-line cap on named files; announces itself via capsay


def pairs(line):
    """Every (outer, inner) the pattern found, whichever alternative matched."""
    out = []
    for m in QUALIFIED.finditer(line):
        g = m.groups()
        for i in range(0, len(g), 2):
            if g[i] and g[i + 1]:
                out.append((g[i], g[i + 1]))
    return out


def top_level_types(text):
    """Type names declared directly inside the namespace, by brace depth.

    Depth 1 is inside `namespace Ledger.Core {`. Anything deeper is nested and
    IS reachable as `Outer.Inner`, so including it would flag correct code —
    `Perception.Attention` being the live example.
    """
    names, depth = set(), 0
    for raw in text.split("\n"):
        line = LINE_COMMENT.sub("", raw)
        m = DECL.match(line)
        if m and depth == 1:
            names.add(m.group(1))
        depth += line.count("{") - line.count("}")
    return names


def _read(f):
    """One read per file per run, or None if it could not be read.

    ONE READ PER FILE PER RUN IS A MEASUREMENT RULE, not a performance one. Two
    runs of the OLD `lint-static` four minutes apart printed 560 and 562
    because another agent was editing a file between them: it read every file
    three times, so one printed line carried three moments of a moving tree.
    An unreadable file is a NAMED DROP rather than a traceback or a silent
    skip — it is one of the two ways this walk can fail to cover its offer.
    """
    try:
        return f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


class Reading(object):
    """ONE WHOLE WALK, from one set of file reads at one moment.

    Every number here is a WHOLE-WALK CUMULATIVE TOTAL — not a peak, not a
    sample, not a last-wins — so none of them needs an at-worst partner and
    they are all safe to divide by each other. `bad` is the finding;
    everything else is its denominator.

    `walked` IS THE FIX: it is the list the scanner appended to as it entered
    each file, so the printed count cannot exceed what was opened. The old line
    printed `len(top)` — the REFERENCE set — which does not move when the walk
    collapses to nothing, and so read identically over 88 files and over none.
    """

    def __init__(self, top, core_walked, core_offered, core_dropped,
                 walked, offered, dropped, lines, seen, outer_core, bad):
        self.top = top                  # reference set: top-level Core type names
        self.core_walked = core_walked  # Core files actually read
        self.core_offered = core_offered
        self.core_dropped = core_dropped    # [file] unreadable
        self.walked = walked            # Game files the scanner entered
        self.offered = offered          # every Game file handed to the walk
        self.dropped = dropped          # [file] unreadable, so not walked
        self.lines = lines              # source lines walked (cumulative)
        self.seen = seen                # qualified pairs examined (cumulative)
        self.outer_core = outer_core    # of those, outer name is a Core type
        self.bad = bad                  # [(file, line, "X.Y", inner)] findings

    @property
    def measured(self):
        """Did this walk examine ANYTHING. A walk that entered no Game file, or
        that has no reference set to compare against, must not print
        `0 errors` — which is the whole of rule 3b."""
        return bool(self.walked) and bool(self.top)


def scan(core_files, game_files):
    """Walk both sides and return the Reading. Findings are `.bad`."""
    top = set()
    core_walked, core_dropped = [], []
    for f in core_files:
        text = _read(f)
        if text is None:
            core_dropped.append(f)
            continue
        core_walked.append(f)
        top |= top_level_types(text)

    bad, walked, dropped = [], [], []
    lines = seen = outer_core = 0
    for f in game_files:
        text = _read(f)
        if text is None:
            dropped.append(f)
            continue
        walked.append(f)
        for n, raw in enumerate(text.split("\n"), 1):
            lines += 1
            line = LINE_COMMENT.sub("", raw)
            for outer, inner in pairs(line):
                seen += 1
                if outer not in top:
                    continue
                outer_core += 1
                if inner in top and outer != inner:
                    bad.append((f.name, n, "%s.%s" % (outer, inner), inner))
    return Reading(top, core_walked, list(core_files), core_dropped,
                   walked, list(game_files), dropped, lines, seen, outer_core, bad)


def summary_lines(r, where="", core_where=""):
    """The reading, as the lines to print. THE ARITHMETIC AND THE STRING LIVE
    HERE, where the selftest runs them, rather than in the caller.

    Line 1 carries both halves — what was walked and what was not — because a
    reader greps `lint-nested:` and sees line 1 and nothing else. The
    parenthetical `(N top-level Core types checked)` is kept VERBATIM and at
    the end, because `nested_types()` in `ledger/verify.py` greps for exactly
    that and a
    rewrite that drops it removes the number from every future GREEN footer
    with no red run to say so.
    """
    if not r.offered:
        return ["lint-nested: nothing measured — no `.cs` file%s"
                % (" under " + where if where else "")]
    if not r.top:
        return ["lint-nested: nothing measured — 0 top-level Core type(s) in "
                "the reference set%s, so %d Game file(s) offered had nothing "
                "to be compared against"
                % (" from " + core_where if core_where else "", len(r.offered))]
    if not r.measured:
        return ["lint-nested: nothing measured — 0 of %d Game file(s) offered "
                "were walked (%d unreadable: %s); the reference set holds %d "
                "top-level Core type(s) and was compared against nothing"
                % (len(r.offered), len(r.dropped),
                   _cap(sorted(f.name for f in r.dropped), keep=SHOW, sep=", "),
                   len(r.top))]

    head = ("lint-nested: %d nested-type error(s) of %d qualified pair(s) "
            "examined in %d of %d Game file(s) walked, %d line(s) "
            "(%d top-level Core types checked)"
            % (len(r.bad), r.seen, len(r.walked), len(r.offered), r.lines,
               len(r.top)))

    ladder = ("  ladder, each rung a cumulative count over the whole walk: "
              "%d qualified pair(s) in type position -> %d whose OUTER name is "
              "a top-level Core type -> %d whose inner name is one too, which "
              "is the finding"
              % (r.seen, r.outer_core, len(r.bad)))

    ref = ("  reference set: %d top-level Core type(s) at brace depth 1 from "
           "%d of %d Core file(s) read%s; nested types are EXCLUDED by depth "
           "(`Perception.Attention` is legal and must not be flagged)"
           % (len(r.top), len(r.core_walked), len(r.core_offered),
              " under " + core_where if core_where else "",
              ))
    if r.core_dropped:
        ref += " — %d Core file(s) UNREADABLE and not in the set: %s" % (
            len(r.core_dropped),
            _cap(sorted(f.name for f in r.core_dropped), keep=SHOW, sep=", "))

    drop = ("no file exempt" if not r.dropped else
            "%d file(s) offered but NOT walked, unreadable: %s"
            % (len(r.dropped),
               _cap(sorted(f.name for f in r.dropped), keep=SHOW, sep=", ")))
    arith = ("  arithmetic: %d walked + %d not walked = %d .cs file(s) offered"
             "%s; %s"
             % (len(r.walked), len(r.dropped), len(r.offered),
                " under " + where if where else "", drop))
    return [head, ladder, ref, arith]


# --------------------------------------------------------------------- selftest

class _Fake(object):
    """A fixture file. SYNTHETIC BY CONSTRUCTION — in memory, never on disk, so
    no run of this tool can write under `ledger/`, and no rejecting case is
    pinned to a real project file that improving the project would break.
    Three rejecting fixtures in this project had to be unpinned for exactly
    that: they went red when the code they named got better."""

    def __init__(self, name, text):
        self.name = name
        self._t = text

    def read_text(self, encoding=None, errors=None):
        return self._t


CORE_FIXTURE = [_Fake("SynthMixing.cs", """
namespace Synth.Fixture
{
    public enum SynthBus { Voice, Foley }
    public static class SynthMixing { public static int Budget(SynthBus b) => 4; }
    public static class SynthPerception
    {
        public struct SynthAttention { public double Seconds; }
    }
}
""")]


class _Unreadable(object):
    """A file that raises on read, so the drop clause has something to count."""

    def __init__(self, name):
        self.name = name

    def read_text(self, encoding=None, errors=None):
        raise OSError("synthetic unreadable fixture")


def selftest():
    ran, fails = [], []

    def check(ok, what, detail=""):
        ran.append(what)
        if not ok:
            fails.append(what)
        print("  %s %s%s" % ("ok  " if ok else "FAIL", what,
                             ("   [%s]" % detail) if detail else ""))

    # ============ ACCEPTING FIRST — THE LIVE CODEBASE (rule 5b) ============
    #
    # The expensive failure for a name-matching check is flagging correct code:
    # it gets switched off within a day and takes the real catch with it. The
    # live tree is the best accepting fixture available because CI compiles it,
    # so EVERY hit on today's code is a false positive by definition, and no
    # fixture I wrote could fool this case.
    print("ACCEPTING — the live codebase, which compiles, so every hit is wrong")
    live = None
    if CORE.is_dir() and GAME.is_dir():
        live = scan(sorted(CORE.rglob("*.cs")), sorted(GAME.rglob("*.cs")))
        lines = summary_lines(live, str(GAME), str(CORE))
        check(not live.bad,
              "the live tree passes — 0 finding(s) on code that compiles",
              "%d finding(s) over %d pair(s) examined" % (len(live.bad), live.seen))
        check(live.measured and len(live.walked) > 0 and live.seen > 0,
              "and it reports a TRUE walked count, not the reference set",
              "%d of %d Game file(s) walked, %d line(s), %d pair(s) examined, "
              "%d top-level Core type(s)"
              % (len(live.walked), len(live.offered), live.lines, live.seen,
                 len(live.top)))
        check(len(live.walked) + len(live.dropped) == len(live.offered)
              and live.outer_core <= live.seen and len(live.bad) <= live.outer_core,
              "the identity on the printed line holds, and the ladder narrows",
              "%d+%d=%d files; %d pair(s) >= %d outer-core >= %d bad"
              % (len(live.walked), len(live.dropped), len(live.offered),
                 live.seen, live.outer_core, len(live.bad)))
        text = "\n".join(lines)
        check(("%d of %d Game file(s) walked" % (len(live.walked), len(live.offered)))
              in text and "arithmetic:" in text,
              "the head names the walked set and the identity is printed for a "
              "reader to check rather than trust",
              lines[0][13:])
    else:
        check(False, "the live tree is readable — NOTHING MEASURED without it",
              "no Core or Game directory at %s" % ROOT)

    # THE CONSUMER'S PARSE, BOTH DIRECTIONS.
    print("\nTHE CONSUMER — nested_types() in ledger/verify.py, which greps "
          "this line")
    if live is not None:
        m = re.search(VERIFY_PARSE, "\n".join(summary_lines(live, str(GAME), str(CORE))))
        check(bool(m) and m.group(1) == str(len(live.top)),
              "verify's regex still matches the summary and lifts the reference "
              "count into the footer",
              "groups=%s types=%d" % (m.groups() if m else None, len(live.top)))
    verify_py = ROOT / "ledger" / "verify.py"
    src = verify_py.read_text(encoding="utf-8", errors="replace") if verify_py.is_file() else ""
    check(VERIFY_PARSE in src,
          "and the copy kept in this file is byte-identical to the one in "
          "verify.py (if this fails, verify changed its parse — read it, do "
          "not edit this line to match)",
          "found in %s" % (verify_py.name if src else
                           "%s — verify.py unreadable" % NOTHING_MEASURED))

    # ============ THE PROBE THAT FOUND THE FAULT ============
    print("\nNOTHING MEASURED — the probe that found this bug, which must now "
          "look DIFFERENT")
    empty = "\n".join(summary_lines(scan(CORE_FIXTURE, []), "/nowhere", "/fixture"))
    check("nothing measured" in empty and "error" not in empty
          and not re.search(VERIFY_PARSE, empty),
          "a full reference set against ZERO Game files prints the WORDS, never "
          "`0 ... errors`, and cannot match verify's pass parse",
          empty)
    if live is not None:
        live_head = summary_lines(live, str(GAME), str(CORE))[0]
        check(live_head != empty.splitlines()[0],
              "and the empty sweep's first line is no longer BYTE-IDENTICAL to "
              "the live one, which is exactly what it was before this change",
              "empty: %s" % empty.splitlines()[0][13:])
    no_core = "\n".join(summary_lines(scan([], [_Fake("A.cs", "var x = 1;\n")]),
                                      "/nowhere", "/fixture"))
    check("nothing measured" in no_core and "0 top-level Core type(s)" in no_core
          and not re.search(VERIFY_PARSE, no_core),
          "an empty REFERENCE set says so too — a comparison against nothing "
          "cannot pass",
          no_core)
    both = "\n".join(summary_lines(scan([], []), "/nowhere", "/fixture"))
    check("nothing measured" in both and not re.search(VERIFY_PARSE, both),
          "and so does a sweep of nothing at all", both)

    print("\nTHE DROP CLAUSE — a file offered but not walked is NAMED")
    dropped = scan(CORE_FIXTURE, [_Fake("Good.cs", "var b = SynthBus.Foley;\n"),
                                  _Unreadable("SynthGone.cs")])
    dtext = "\n".join(summary_lines(dropped, "/fixture", "/fixture"))
    check(len(dropped.walked) == 1 and len(dropped.dropped) == 1
          and "1 walked + 1 not walked = 2" in dtext and "SynthGone.cs" in dtext,
          "an unreadable file is counted under its own reason and NAMED, not "
          "folded into the total and not a traceback",
          dtext.splitlines()[-1][2:])
    clean = "\n".join(summary_lines(scan(CORE_FIXTURE,
                                         [_Fake("Good.cs", "var b = SynthBus.Foley;\n")]),
                                    "/fixture", "/fixture"))
    check("no file exempt" in clean and "not walked = 1" in clean,
          "and a walk that dropped nothing says `no file exempt` rather than "
          "leaving the reader to assume it",
          clean.splitlines()[-1][2:])

    # ============ REJECTING — the CS0426 this tool exists for ============
    print("\nREJECTING — the CS0426 this tool exists for (synthetic, unpinned)")
    good = scan(CORE_FIXTURE,
                [_Fake("Good.cs",
                       "var b = SynthBus.Foley;\n"
                       "var a = new SynthPerception.SynthAttention();\n")])
    check("SynthBus" in good.top and "SynthMixing" in good.top
          and "SynthAttention" not in good.top and not good.bad,
          "correct code passes, and a genuinely NESTED type is not mistaken "
          "for a sibling",
          "%d finding(s) over %d pair(s)" % (len(good.bad), good.seen))

    bad = scan(CORE_FIXTURE,
               [_Fake("Bad.cs", "static Dictionary<SynthMixing.SynthBus, int> x;\n")])
    check(len(bad.bad) == 1 and bad.bad[0][2] == "SynthMixing.SynthBus",
          "a sibling qualified by another type IS caught",
          bad.bad[0][2] if bad.bad else "nothing")
    btext = "\n".join(summary_lines(bad, "/fixture", "/fixture"))
    check("1 nested-type error(s)" in btext and "1 of 1 Game file(s) walked" in btext
          and re.search(VERIFY_PARSE, btext),
          "a FINDING still ships its denominator — the summary prints beside "
          "the hits rather than instead of them",
          btext.splitlines()[0][13:])

    # A COMMENT EXPLAINING THE MISTAKE MUST NOT BE THE MISTAKE. The fix for
    # this very bug left `Mixing.Bus` in a comment saying not to write it.
    cmt = scan(CORE_FIXTURE,
               [_Fake("Note.cs",
                      "// `SynthBus`, NOT `SynthMixing.SynthBus`. It is a sibling.\n")])
    check(not cmt.bad,
          "and a comment warning about it is not flagged as it",
          "%d finding(s)" % len(cmt.bad))

    ok = not fails
    print("\nlint-nested --selftest: %s — %d checks, %d failed"
          % ("PASS" if ok else "FAILED", len(ran), len(fails)))
    print("  denominators: live %s; synthetic %d fixture file(s), 0 written to "
          "disk, 0 project file(s) modified"
          % (("%d of %d Game file(s) walked, %d pair(s) examined, %d Core "
              "file(s) read" % (len(live.walked), len(live.offered), live.seen,
                                len(live.core_walked)))
             if live is not None else "%s — no live tree" % NOTHING_MEASURED, 6))
    return 0 if ok else 1


def main():
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # `| head` must not traceback
    except (AttributeError, ValueError):
        pass
    if "--selftest" in sys.argv or "--self-test" in sys.argv:
        return selftest()

    def _rel(p):
        try:
            return str(p.relative_to(ROOT))
        except ValueError:
            return str(p)                 # fail readable, not with a traceback

    if not CORE.is_dir() or not GAME.is_dir():
        # WORDS, NOT A ZERO. This printed nothing about coverage and returned 0,
        # so a missing directory reached verify as a clean run.
        print("lint-nested: nothing measured — %s not found (Core %s, Game %s)"
              % ("Core and Game" if not CORE.is_dir() and not GAME.is_dir()
                 else "Core" if not CORE.is_dir() else "Game",
                 _rel(CORE), _rel(GAME)))
        return 2

    r = scan(sorted(CORE.rglob("*.cs")), sorted(GAME.rglob("*.cs")))
    if r.bad:
        print("lint-nested: %d Core type(s) qualified by another Core type "
              "— this is CS0426 and the Windows build is where you will find out:"
              % len(r.bad))
        for name, line, what, inner in r.bad:
            print("  %s:%d  %s  — '%s' is a SIBLING of that type, "
                  "write '%s' on its own" % (name, line, what, inner, inner))
    for line in summary_lines(r, _rel(GAME), _rel(CORE)):
        print(line)
    if not r.measured:
        return 2
    return 1 if r.bad else 0


if __name__ == "__main__":
    sys.exit(main())
