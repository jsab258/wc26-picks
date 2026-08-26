#!/usr/bin/env python3
"""A Game-layer member must not be named after a Core type the file uses.

    python3 tools/lint-shadow.py
    python3 tools/lint-shadow.py --selftest      (--self-test also accepted)

WHY THIS EXISTS.

On 4 August the Windows build failed three times over about ninety minutes on
one line:

    EvidenceHost.cs(229,21): error CS0119: 'EvidenceHost.Watched(Vector3,
    IEnumerable<NpcWalker>)' is a method, which is not valid in the given context

`Ledger.Core.Watched` is a type. `EvidenceHost` calls `Watched.WouldTalkToPolice`
eighty lines below. Adding a public static method called `Watched` to that class
shadowed the type inside it, and the error landed on a line nobody had touched.

The cost is the point. **Only `Core` compiles in this container** — the Game
layer's first compiler is a Windows CI runner twenty-five minutes away — so a
name collision that any IDE would underline in red instead consumed three round
trips, two of which were spent misdiagnosing it as a Unity licence failure
because the verdict for a failed build said nothing about why.

The verdict carries compile errors now, which turns the next one into a
two-minute fix. This is the other half: catching it here costs nothing at all.

WHAT IT CHECKS, AND WHAT IT DELIBERATELY DOES NOT.

C# name resolution is genuinely complicated and this is a lint, not a compiler.
It flags exactly one pattern, the one that has actually cost time:

    a Game file declares a member (method, property or field) whose bare name
    equals a Core TYPE name, and that same file uses that name as a qualifier
    — `Watched.Something` — somewhere in its text.

Both halves are required. A Game member named `Traces` in a file that never
writes `Traces.` is legal and harmless; a file that only uses `Traces.Acquire`
and declares nothing of that name is the normal case and by far the commonest.
Requiring the collision AND the use keeps this from becoming a rename tax on
every sensible identifier in the project.

It reads text rather than parsing C#. ShapeCheck already owns real syntax, and a
regex that is honest about being a regex beats a half-parser that is not.

-------------------------------------------------------------------------------
ONE LINE, TWO MOMENTS — AND A ZERO THAT COULD NOT TELL A SWEEP FROM A SILENCE
(26 Aug). Two faults, both in the summary line rather than in the check.

    lint-shadow: 0 shadowed Core types (285 type(s), 88 Game file(s))

  * THE `88` WAS A SECOND GLOB, RUN AT PRINT TIME:
    `len(list(GAME.rglob("*.cs")))`, evaluated after the walk had finished
    rather than taken from it. So one printed line carried two moments of a
    tree that moves under this tool — `lint-static` printed 560 and 562 four
    minutes apart for exactly this reason, because it read every file three
    times and another agent was editing one of them. Both numbers were "true"
    and the line was not. The count now comes from the walk itself, and there
    is no second glob left to disagree with it.

  * AN EMPTY GAME DIRECTORY PRINTED `0 shadowed Core types (285 type(s), 0
    Game file(s))` AND EXITED 0 — a sweep of nothing, reported as a pass, and
    `ledger/verify.py` lifted it into a GREEN footer. A zero from a walk that
    entered no file is not a clean result; it is an absence wearing one's
    clothes (rule 3b). It prints the WORDS now and exits 2.

  * AND `--selftest` WAS SILENTLY IGNORED: the flag fell through to the live
    sweep, which printed a pass and exited 0, so a guard that had never run
    looked exactly like a guard that had. There is a real one below, accepting
    case first.

The repair shape is copied from `tools/lint-static.py` and
`tools/lint-conditional-reach.py` rather than invented, and `lint-avenues`
supplies the "no file exempt" phrasing: counts derived FROM the walk, a drop
clause naming what was not walked and why, a checkable identity
(`88 walked + 0 not walked = 88 offered`), and a ladder — because "88 files
walked" would still read as healthy if `MEMBER_DECL` stopped matching and the
tool examined no declarations at all.

WHO READS THIS LINE. `shadow()` in `ledger/verify.py` (line 173 at
`ce37232e`; the LINE drifts, the function does not), and nothing else in the
repo:

    m = re.search(r"lint-shadow: (\\d+) shadowed Core types"
                  r"(?: \\((\\d+) type\\(s\\), (\\d+) Game file\\(s\\)\\))?", out)

That regex is PINNED by the selftest below, in both directions: the head still
matches it and still yields all three groups, and the copy kept here is still
byte-identical to the one in `verify.py`. Everything new is appended AFTER the
parenthetical, never inside it — another lint's rewrite in this project
silently dropped the token its verify parse grepped for, which removes the
denominator from every future GREEN footer with no red run to say so.

EXIT CODES
    0   walked, no collision found
    1   at least one CS0119 candidate
    2   NOTHING MEASURED — no Core types, no Game folder, or no `.cs` file
        walked. Prints the words, never `0 ... shadowed`.
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

# `public sealed class Foo`, `static class Foo`, `enum Foo`, `struct Foo`.
TYPE_DECL = re.compile(
    r"^\s*(?:public|internal)?\s*(?:static\s+|sealed\s+|abstract\s+|partial\s+)*"
    r"(?:class|struct|enum|interface)\s+([A-Z][A-Za-z0-9_]*)",
    re.M,
)

# METHODS ONLY, AND THE NARROWING IS THE WHOLE CORRECTNESS OF THIS TOOL.
#
# The first version flagged any member and reported six on a tree that has
# compiled hundreds of times: `public Wallet Wallet { get; }`, `public Campaign
# Campaign { get; }`, `public readonly FramedBeat Beat`. All legal. A field or
# property shadowing a type still resolves — the simple name binds to the
# member, and `Wallet.Balance` reaches the same member it would have anyway
# (C#'s "Color Color" rule), while `Beat.Abort()` reaches `FramedBeat.Abort`.
#
# A METHOD cannot. `Watched` as a method makes the simple name a method GROUP,
# and a method group cannot be dotted at all — so `Watched.WouldTalkToPolice` is
# CS0119 with no exception and no ambiguity. That is the only case this can
# prove without a compiler, so it is the only case it flags.
#
# Rule 5b, and it nearly went out wrong: the reject case passed on the first
# run and I was one commit from shipping a guard that blocked six good files.
# "Refuse unless perfect" is the ratchet, and a lint that fails a tree which
# demonstrably builds is exactly that.
MEMBER_DECL = re.compile(
    r"^\s*(?:public|internal|protected)\s+(?:static\s+|virtual\s+|override\s+|"
    r"abstract\s+|new\s+|async\s+|sealed\s+)*"
    r"[A-Za-z_][A-Za-z0-9_<>,\[\]\.\?]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    re.M,
)

# A VERBATIM COPY OF the regex in `shadow()` in `ledger/verify.py`, kept here
# so the selftest can run the real consumer's parse against the real line.
# verify.py is the source of truth and is NOT edited from here; if the two
# ever differ the selftest says so by name, instead of the footer quietly
# losing its census.
VERIFY_PARSE = (r"lint-shadow: (\d+) shadowed Core types"
                r"(?: \((\d+) type\(s\), (\d+) Game file\(s\)\))?")

SHOW = 3            # per-line cap on named files; announces itself via capsay


def strip_comments(text):
    """Comments mention type names constantly and none of it is code.

    Without this, every paragraph in this project explaining why `Watched` is
    called `Watched` would read as a use of it. Strings go too: a verdict line
    with `Traces.` in it is prose that happens to be quoted.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"^\s*///.*$", " ", text, flags=re.M)
    text = re.sub(r"//.*$", " ", text, flags=re.M)
    # PLAIN strings only. `$"..."` IS CODE and throwing it away made this check
    # blind to the place the mistake actually happens.
    #
    # The docstring above says "a verdict line with `Traces.` in it is prose
    # that happens to be quoted". True of a plain string; FALSE of an
    # interpolated one, and `SimDirector`'s done-line is a single interpolated
    # string hundreds of expressions long — the largest concentration of
    # Game-layer static reads in the project. Every CS0119 in it was invisible
    # here.
    #
    # Found on 4 August while writing `lint-filetype`, which scored zero on the
    # very line that prompted it for exactly this reason, and then found the
    # same fault sitting in this file. One idea, two implementations.
    text = re.sub(r'\$"(?:\\.|[^"\\])*"',
                  lambda m: " ".join(re.findall(r"\{([^{}]*)\}", m.group(0))),
                  text, flags=re.S)
    text = re.sub(r'(?<!\$)"(?:\\.|[^"\\])*"', '""', text)
    return text


def _read(f):
    """One read per file per run, or None if it could not be read.

    ONE READ PER FILE PER RUN IS A MEASUREMENT RULE, not a performance one, and
    the print-time re-glob this file used to end on was the same fault one
    level up: a count taken at a different moment from the walk it describes.
    An unreadable file is a NAMED DROP rather than a traceback or a silent skip.
    """
    try:
        return strip_comments(f.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None


class Reading(object):
    """ONE WHOLE WALK, from one set of file reads at one moment.

    Every number here is a WHOLE-WALK CUMULATIVE TOTAL — not a peak, not a
    sample, not a last-wins — so they are all safe to print beside each other
    and none needs an at-worst partner. `bad` is the finding; everything else
    is its denominator.

    `walked` IS THE FIX: it is the list the scanner appended to as it entered
    each file. The old line printed `len(list(GAME.rglob("*.cs")))`, evaluated
    at PRINT time — a second glob, a second moment, and a number that could
    disagree with the walk it was printed as describing.
    """

    def __init__(self, types, core_walked, core_offered, core_dropped,
                 walked, offered, dropped, decls, clashes, bad):
        self.types = types              # reference set: Core type names
        self.core_walked = core_walked  # Core files actually read
        self.core_offered = core_offered
        self.core_dropped = core_dropped
        self.walked = walked            # Game files the scanner entered
        self.offered = offered          # every Game file handed to the walk
        self.dropped = dropped          # [file] unreadable, so not walked
        self.decls = decls              # method names declared, distinct per
                                        # file, summed over the walk (cumulative)
        self.clashes = clashes          # of those, names equal to a Core type
        self.bad = bad                  # [(path, name)] findings

    @property
    def measured(self):
        """Did this walk examine ANYTHING. A walk that entered no Game file, or
        that has no reference set to compare against, must not print
        `0 shadowed` — which is the whole of rule 3b."""
        return bool(self.walked) and bool(self.types)


def scan(core_files, game_files, rel=None):
    """Walk both sides and return the Reading. Findings are `.bad`."""
    rel = rel or (lambda p: getattr(p, "name", str(p)))
    types = set()
    core_walked, core_dropped = [], []
    for f in sorted(core_files, key=lambda p: str(getattr(p, "name", p))):
        text = _read(f)
        if text is None:
            core_dropped.append(f)
            continue
        core_walked.append(f)
        types.update(TYPE_DECL.findall(text))

    bad, walked, dropped = [], [], []
    decls = clashes = 0
    for f in sorted(game_files, key=lambda p: str(getattr(p, "name", p))):
        code = _read(f)
        if code is None:
            dropped.append(f)
            continue
        walked.append(f)
        members = set(MEMBER_DECL.findall(code))
        decls += len(members)
        clash = members & types
        clashes += len(clash)
        for name in sorted(clash):
            # ...and the file has to actually USE it as a qualifier, or the
            # shadowing is invisible and harmless.
            if re.search(r"(?<![A-Za-z0-9_.])" + re.escape(name) + r"\s*\.", code):
                bad.append((rel(f), name))
    return Reading(types, core_walked, list(core_files), core_dropped,
                   walked, list(game_files), dropped, decls, clashes, bad)


def summary_lines(r, where="", core_where=""):
    """The reading, as the lines to print. THE ARITHMETIC AND THE STRING LIVE
    HERE, where the selftest runs them, rather than in the caller.

    The head keeps `lint-shadow: N shadowed Core types (T type(s), F Game
    file(s))` VERBATIM and first, because `shadow()` in `ledger/verify.py` greps
    exactly
    that and lifts all three numbers into the footer. `F` is now the WALKED
    count rather than a fresh glob, so the parenthetical describes the same
    moment as the rest of the line.
    """
    if not r.types:
        return ["lint-shadow: nothing measured — 0 Core type(s) in the "
                "reference set%s, so %d Game file(s) offered had nothing to be "
                "compared against; check the paths"
                % (" from " + core_where if core_where else "", len(r.offered))]
    if not r.offered:
        return ["lint-shadow: nothing measured — no `.cs` file%s; the reference "
                "set holds %d Core type(s) and was compared against nothing"
                % (" under " + where if where else "", len(r.types))]
    if not r.measured:
        return ["lint-shadow: nothing measured — 0 of %d Game file(s) offered "
                "were walked (%d unreadable: %s); the reference set holds %d "
                "Core type(s) and was compared against nothing"
                % (len(r.offered), len(r.dropped),
                   _cap(sorted(getattr(f, "name", str(f)) for f in r.dropped),
                        keep=SHOW, sep=", "),
                   len(r.types))]

    head = ("lint-shadow: %d shadowed Core types (%d type(s), %d Game file(s))"
            " — that file count is the set WALKED, taken from the walk and not "
            "from a second glob at print time"
            % (len(r.bad), len(r.types), len(r.walked)))

    ladder = ("  ladder, each rung a cumulative count over the whole walk: "
              "%d method name(s) declared (distinct per file) -> %d equal to a "
              "Core type name -> %d of those also used as a `Name.` qualifier "
              "in the same file, which is the finding"
              % (r.decls, r.clashes, len(r.bad)))

    ref = ("  reference set: %d Core type(s) from %d of %d Core file(s) read%s"
           % (len(r.types), len(r.core_walked), len(r.core_offered),
              " under " + core_where if core_where else ""))
    if r.core_dropped:
        ref += " — %d Core file(s) UNREADABLE and not in the set: %s" % (
            len(r.core_dropped),
            _cap(sorted(getattr(f, "name", str(f)) for f in r.core_dropped),
                 keep=SHOW, sep=", "))

    drop = ("no file exempt" if not r.dropped else
            "%d file(s) offered but NOT walked, unreadable: %s"
            % (len(r.dropped),
               _cap(sorted(getattr(f, "name", str(f)) for f in r.dropped),
                    keep=SHOW, sep=", ")))
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


class _Unreadable(object):
    """A file that raises on read, so the drop clause has something to count."""

    def __init__(self, name):
        self.name = name

    def read_text(self, encoding=None, errors=None):
        raise OSError("synthetic unreadable fixture")


CORE_FIXTURE = [_Fake("SynthCore.cs", """
namespace Synth.Fixture
{
    public static class SynthWatched
    {
        public static bool WouldTalkToPolice() { return true; }
    }

    public sealed class SynthWallet { public int Balance; }
}
""")]

# THE REAL CS0119, WITH SYNTHETIC NAMES: a Game method named after a Core type
# the same file dots. `EvidenceHost.Watched` in the incident.
SHADOWING = _Fake("SynthHost.cs", """
namespace Synth.Fixture
{
    public class SynthHost
    {
        public static bool SynthWatched(int a) { return a > 0; }

        public void Use()
        {
            if (SynthWatched.WouldTalkToPolice()) { }
        }
    }
}
""")

# COLLIDES BUT NEVER DOTS IT — legal, and flagging it would be the rename tax.
COLLIDES_ONLY = _Fake("SynthQuiet.cs", """
namespace Synth.Fixture
{
    public class SynthQuiet
    {
        public static bool SynthWatched(int a) { return a > 0; }
    }
}
""")

# DOTS IT BUT DECLARES NOTHING OF THE NAME — the normal case, and the commonest.
USES_ONLY = _Fake("SynthUser.cs", """
namespace Synth.Fixture
{
    public class SynthUser
    {
        public void Use() { var x = SynthWatched.WouldTalkToPolice(); }
    }
}
""")

# A PROPERTY, NOT A METHOD: C#'s "Color Color" rule makes this legal, and the
# first version of this tool reported six of these on a tree that compiles.
PROPERTY = _Fake("SynthProp.cs", """
namespace Synth.Fixture
{
    public class SynthProp
    {
        public SynthWallet SynthWallet { get; private set; }
        public int Read() { return SynthWallet.Balance; }
    }
}
""")


def selftest():
    ran, fails = [], []

    def check(ok, what, detail=""):
        ran.append(what)
        if not ok:
            fails.append(what)
        print("  %s %s%s" % ("ok  " if ok else "FAIL", what,
                             ("   [%s]" % detail) if detail else ""))

    def rel(p):
        return getattr(p, "name", str(p))

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
              "%d finding(s) over %d declaration(s) examined"
              % (len(live.bad), live.decls))
        check(live.measured and len(live.walked) > 0 and live.decls > 0,
              "and it reports a TRUE walked count and a TRUE examined count",
              "%d of %d Game file(s) walked, %d declaration(s), %d clash(es), "
              "%d Core type(s)" % (len(live.walked), len(live.offered),
                                   live.decls, live.clashes, len(live.types)))
        check(len(live.walked) + len(live.dropped) == len(live.offered)
              and live.clashes <= live.decls and len(live.bad) <= live.clashes,
              "the identity on the printed line holds, and the ladder narrows",
              "%d+%d=%d files; %d decl(s) >= %d clash(es) >= %d bad"
              % (len(live.walked), len(live.dropped), len(live.offered),
                 live.decls, live.clashes, len(live.bad)))
        # THE RE-GLOB, PINNED. The old head printed a fresh
        # `len(list(GAME.rglob("*.cs")))` at print time; this asserts the
        # number in the parenthetical is the WALK's, by identity.
        text = "\n".join(lines)
        check(("(%d type(s), %d Game file(s))" % (len(live.types), len(live.walked)))
              in text and "not from a second glob at print time" in text,
              "the parenthetical file count IS the walked set — one line, one "
              "moment, no second glob",
              lines[0][13:])
    else:
        check(False, "the live tree is readable — NOTHING MEASURED without it",
              "no Core or Game directory at %s" % ROOT)

    # THE CONSUMER'S PARSE, BOTH DIRECTIONS.
    print("\nTHE CONSUMER — shadow() in ledger/verify.py, which greps this line")
    if live is not None:
        m = re.search(VERIFY_PARSE,
                      "\n".join(summary_lines(live, str(GAME), str(CORE))))
        check(bool(m) and m.group(1) == "0" and m.group(2) == str(len(live.types))
              and m.group(3) == str(len(live.walked)),
              "verify's regex still matches and still yields ALL THREE groups, "
              "so the census keeps reaching the footer",
              "groups=%s" % (m.groups() if m else None,))
    verify_py = ROOT / "ledger" / "verify.py"
    src = verify_py.read_text(encoding="utf-8", errors="replace") if verify_py.is_file() else ""
    # verify wraps the pattern across two string literals; compare the halves.
    halves = [r"lint-shadow: (\d+) shadowed Core types",
              r"(?: \((\d+) type\(s\), (\d+) Game file\(s\)\))?"]
    check(all(h in src for h in halves),
          "and the copy kept in this file is byte-identical to the one in "
          "verify.py (if this fails, verify changed its parse — read it, do "
          "not edit this line to match)",
          "both halves found in %s" % (verify_py.name if src else
                                       "%s — verify.py unreadable" % NOTHING_MEASURED))

    # ============ THE PROBE THAT FOUND THE FAULT ============
    print("\nNOTHING MEASURED — the probe that found this bug, which must now "
          "look DIFFERENT")
    empty = "\n".join(summary_lines(scan(CORE_FIXTURE, []), "/nowhere", "/fixture"))
    check("nothing measured" in empty and "0 shadowed" not in empty
          and not re.search(VERIFY_PARSE, empty),
          "a full reference set against ZERO Game files prints the WORDS, "
          "never `0 shadowed`, and cannot match verify's pass parse",
          empty)
    if live is not None:
        check(summary_lines(live, str(GAME), str(CORE))[0] != empty.splitlines()[0],
              "and the empty sweep's line is not the live one with a zero "
              "swapped in — before this change it was, at exit 0",
              "empty: %s" % empty.splitlines()[0][13:])
    no_core = "\n".join(summary_lines(scan([], [USES_ONLY]), "/nowhere", "/fixture"))
    check("nothing measured" in no_core and "0 Core type(s)" in no_core
          and not re.search(VERIFY_PARSE, no_core),
          "an empty REFERENCE set says so too — a comparison against nothing "
          "cannot pass", no_core)

    print("\nTHE DROP CLAUSE — a file offered but not walked is NAMED")
    dropped = scan(CORE_FIXTURE, [USES_ONLY, _Unreadable("SynthGone.cs")])
    dtext = "\n".join(summary_lines(dropped, "/fixture", "/fixture"))
    check(len(dropped.walked) == 1 and len(dropped.dropped) == 1
          and "1 walked + 1 not walked = 2" in dtext and "SynthGone.cs" in dtext,
          "an unreadable file is counted under its own reason and NAMED, not "
          "folded into the total and not a traceback",
          dtext.splitlines()[-1][2:])
    clean = "\n".join(summary_lines(scan(CORE_FIXTURE, [USES_ONLY]),
                                    "/fixture", "/fixture"))
    check("no file exempt" in clean,
          "and a walk that dropped nothing says `no file exempt` rather than "
          "leaving the reader to assume it", clean.splitlines()[-1][2:])

    # ============ ACCEPTING — the three shapes that must NOT be flagged =====
    print("\nACCEPTING — the legal shapes a rename tax would have broken")
    quiet = scan(CORE_FIXTURE, [COLLIDES_ONLY])
    check(not quiet.bad and quiet.clashes == 1,
          "a member that collides but never dots the name is legal and passes "
          "— and the clash is still COUNTED, so the rung is visible",
          "%d finding(s), %d clash(es)" % (len(quiet.bad), quiet.clashes))
    user = scan(CORE_FIXTURE, [USES_ONLY])
    check(not user.bad and user.clashes == 0,
          "a file that only USES the type declares nothing of the name — the "
          "commonest case in the project", "%d finding(s)" % len(user.bad))
    prop = scan(CORE_FIXTURE, [PROPERTY])
    check(not prop.bad,
          "a PROPERTY named after a type still resolves (C#'s `Color Color` "
          "rule); the first version reported six of these on a tree that builds",
          "%d finding(s)" % len(prop.bad))

    # ============ REJECTING — the CS0119 this tool exists for ============
    print("\nREJECTING — the CS0119 this tool exists for (synthetic, unpinned)")
    caught = scan(CORE_FIXTURE, [SHADOWING], rel=rel)
    check(len(caught.bad) == 1 and caught.bad[0][1] == "SynthWatched",
          "a Game METHOD named after a Core type the same file dots IS caught",
          "%s" % ("/".join(caught.bad[0]) if caught.bad else "nothing"))
    ctext = "\n".join(summary_lines(caught, "/fixture", "/fixture"))
    check("lint-shadow: 1 shadowed Core types" in ctext
          and re.search(VERIFY_PARSE, ctext)
          and re.search(VERIFY_PARSE, ctext).group(1) == "1",
          "a FINDING still ships its denominator AND still parses — verify "
          "reads the count off the same line rather than a hardcoded zero",
          ctext.splitlines()[0][13:])
    mixed = scan(CORE_FIXTURE, [SHADOWING, COLLIDES_ONLY, USES_ONLY, PROPERTY],
                 rel=rel)
    check(len(mixed.bad) == 1 and len(mixed.walked) == 4,
          "and one bad file among three good ones is found without the good "
          "three being flagged",
          "%d finding(s) of %d file(s) walked, %d clash(es)"
          % (len(mixed.bad), len(mixed.walked), mixed.clashes))

    ok = not fails
    print("\nlint-shadow --selftest: %s — %d checks, %d failed"
          % ("PASS" if ok else "FAILED", len(ran), len(fails)))
    print("  denominators: live %s; synthetic %d fixture file(s), 0 written to "
          "disk, 0 project file(s) modified"
          % (("%d of %d Game file(s) walked, %d declaration(s) examined, %d "
              "Core file(s) read" % (len(live.walked), len(live.offered),
                                     live.decls, len(live.core_walked)))
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
        except (ValueError, AttributeError):
            return str(getattr(p, "name", p))     # fail readable, no traceback

    if not GAME.is_dir() or not CORE.is_dir():
        print("lint-shadow: nothing measured — %s not found (Core %s, Game %s)"
              % ("Core and Game" if not CORE.is_dir() and not GAME.is_dir()
                 else "Core" if not CORE.is_dir() else "Game",
                 _rel(CORE), _rel(GAME)))
        return 2

    r = scan(sorted(CORE.rglob("*.cs")), sorted(GAME.rglob("*.cs")), rel=_rel)
    if r.bad:
        print("lint-shadow: %d Game member(s) shadow a Core type the same file "
              "uses:" % len(r.bad))
        for path, name in r.bad:
            print("  %s: declares `%s`, and uses `%s.` — CS0119 waiting to happen"
                  % (path, name, name))
        print("  Rename the Game member. Only Core compiles here; this is a")
        print("  twenty-five minute round trip if it reaches CI.")
    for line in summary_lines(r, _rel(GAME), _rel(CORE)):
        print(line)
    if not r.measured:
        return 2
    return 1 if r.bad else 0


if __name__ == "__main__":
    sys.exit(main())
