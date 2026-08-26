#!/usr/bin/env python3
"""A static method in a partial class reaching an instance member of it: CS0120.

    python3 tools/lint-static.py
    python3 tools/lint-static.py --selftest       (--self-test also accepted)

WHY THIS EXISTS.

    Assets\\Scripts\\Game\\PopulationHost.cs(129,17): error CS0120:
    An object reference is required for the non-static field, method, or
    property 'GameController.Populace'

`GameController` is spread across a dozen partial files. A method written in
one of them cannot see, from that file alone, whether the members it touches
are static — and `static` is the reflex modifier for anything that looks like a
pure mapping. `ApplyDetailToCrowd` looked exactly like one: a settings value in,
a cap out. The one thing it touches is the instance's own population.

THE THIRD REFERENCE-RESOLUTION ERROR IN ONE MORNING, after CS0119 (a Game
method shadowing a Core type) and CS0426 (a Core type qualified by another).
All three are invisible to ShapeCheck for the same structural reason: it runs
reference-independent diagnostics, which is exactly what lets it run at all on
a side with no Unity assemblies. All three cost a twenty-eight-minute round
trip, and each one blocked every build dispatched after it.

WHAT IT DOES. Collects the instance members declared across every partial of a
class, then flags a `static` method in the same class that names one of them.

WHAT IT CANNOT DO, said plainly because a checker that overclaims is worse than
none: it matches NAMES, not symbols. A local variable, a parameter, or an
unrelated type's member with the same name reads identically. So it only
considers members whose names are distinctive enough to be worth the risk —
and the live codebase is the proof, because today's code compiles and therefore
every hit on it is a false positive by definition. That is the accepting case
the two earlier lints of this family each failed before passing.

-------------------------------------------------------------------------------
THE DENOMINATOR WAS NINETEEN TIMES THE SET EXAMINED, AND CLAUDE.md CITED THIS
LINE AS THE EXEMPLAR OF THE RULE THAT FORBIDS IT (25 Aug).

    lint-static: 0 static/instance errors (75 instance members across 2 partial
    class(es), 562 static bodies walked)

`562 static bodies walked` was summed over EVERY Game file. The walk enters
only files declaring `public partial class` whose class shows an instance
member — measured that morning: **29 bodies in 14 files of 88, so 533 bodies
in 74 files were counted as walked and never opened.** Rule 3b exists to stop
a clean result being indistinguishable from an empty one, and this line was
making a 5%-coverage sweep read as a whole-layer sweep. `CLAUDE.md` §3b quoted
it as the FIX.

Two structural repairs, not one wording change:

  * THE COUNT IS DERIVED FROM THE WALK. `Reading.walked` is the set
    `scan_file()` was actually called on — recorded by the scanner, not
    re-derived by a parallel `for f in files` loop beside it. One idea, one
    implementation; the two can no longer disagree because there is no second
    one to drift.
  * THE SKIPPED SET IS NAMED OUT LOUD, per reason, on the same line a reader
    greps. `tools/lint-conditional-reach.py` already does this for its
    unwalked Core/Editor dirs and is the style copied here rather than a
    second one invented.

THE SCOPE ITSELF IS INTENTIONAL AND STAYS (director ruling, 25 Aug). This tool
exists for PARTIAL-SPREAD INVISIBILITY: a CS0120 hides where a type is spread
across files nobody reads together. A self-contained class is not what it asks
about, and widening it is not the fix. The 74 files are correctly unexamined —
they were just being counted as examined.

EVERY FILE IS READ ONCE PER RUN, and that is a measurement rule rather than a
performance one. Two runs of the OLD tool four minutes apart on 25 Aug printed
560 and 562, because another agent was editing `WorldBuilder.cs` between them.
The old code read every file three times (`collect`, `static_bodies`,
`scan_file`), so one printed line could carry three different moments of a
moving tree.

WHO READS THIS LINE. `ledger/verify.py:947`, and nothing else in the repo:

    m = re.search(r"\\((\\d+) instance members.*?(\\d+) static bodies walked\\)", out)

That regex is PINNED by the selftest below, in both directions: the summary
line still matches it, and the copy kept here is still byte-identical to the
one in `verify.py`. Another lint's rewrite in this project silently dropped the
token its verify parse grepped for, which removed the denominator from every
future GREEN footer without a single red run to say so.

EXIT CODES
    0   walked, no candidate found        (selftest: every check as expected)
    1   at least one CS0120 candidate     (selftest: a check failed)
    2   NOTHING MEASURED — no Game folder, no `.cs` files, or no file in
        partial-class scope. Prints the words, never `0 ... errors`.
"""

import pathlib
import re
import signal
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME = ROOT / "ledger" / "Assets" / "Scripts" / "Game"

PARTIAL = re.compile(r"\bpublic\s+partial\s+class\s+(\w+)")
LINE_COMMENT = re.compile(r"//.*")
# An instance member: `public`, NOT static, a type, then a name.
#
# THE COMMENT HERE USED TO SAY "public/internal" AND THE REGEX HAS ONLY EVER
# MATCHED `public` — a false claim about coverage, inherited and corrected on
# 25 Aug rather than rewritten around. Measured before changing the words, not
# after: **0 `internal` non-static members exist in the 14 walked files
# today**, so the gap is real and currently empty. Widening the pattern with
# nothing to catch would be an untested change to a name-matcher, which is how
# both earlier lints of this family started flagging code that compiles.
INSTANCE = re.compile(
    r"^\s*public\s+(?!static\b)(?!partial\b)(?!class\b)(?!enum\b)(?!struct\b)"
    r"(?:readonly\s+)?[\w<>,\[\]\?\.]+\s+(\w+)\s*(?:\{|=|;)")
STATIC_METHOD = re.compile(
    r"^\s*(?:public|internal|private|protected)?\s*static\s+"
    r"[\w<>,\[\]\?\.]+\s+(\w+)\s*\(")

SHOW = 3            # per-line cap on named files; announces itself in _capped

# A VERBATIM COPY OF `ledger/verify.py:947`, kept here so the selftest can run
# the real consumer's parse against the real line. verify.py is the source of
# truth and is not edited from here; if the two ever differ, the selftest says
# so by name instead of the footer quietly losing its denominator.
VERIFY_PARSE = r"\((\d+) instance members.*?(\d+) static bodies walked\)"

# The three ways a file offered to the walk does not get walked. The first is
# BY DESIGN (see the header); the other two are silences that a person has to
# act on, so they are named with their files rather than counted.
BY_DESIGN = "noPartialClass"
REASONS = {
    BY_DESIGN: "declare no `public partial class` — outside this tool's scope "
               "by design, a CS0120 hides in a type SPREAD across files",
    "twoPartialClasses": "declare two partial classes — member attribution "
                         "would be a guess",
    "noInstanceMember": "declare a partial class with no instance member — "
                        "nothing for a static body to reach",
}


def strip_comments(text):
    return "\n".join(LINE_COMMENT.sub("", l) for l in text.split("\n"))


def _capped(names):
    """A CAP THAT SAYS WHEN IT BIT. A `| head -3` that outgrew its input once
    read as 'three of five systems failed' when nothing was broken."""
    shown = ", ".join(names[:SHOW])
    extra = len(names) - SHOW
    return shown + (" (+%d more not shown)" % extra if extra > 0 else "")


def read_all(files):
    """ONE READ PER FILE PER RUN, so every count below is from ONE MOMENT.

    The tree moves under this tool: on 25 Aug two runs four minutes apart read
    560 and 562 static bodies while another agent edited `WorldBuilder.cs`. The
    old code read each file three times, so a single printed line could carry
    three different moments of the same file.
    """
    return {f: strip_comments(f.read_text(encoding="utf-8", errors="replace"))
            for f in files}


def static_bodies(code):
    """How many static method bodies this ALREADY-STRIPPED text has.

    Takes text rather than a file so it counts the same read the walk used. A
    declaration with no body (`static extern void Foo();`) is not a body and is
    not counted — the same test `scan_file` uses to refuse to enter one.
    """
    n = 0
    for line in code.split("\n"):
        if STATIC_METHOD.match(line) and not (
                "{" not in line and "=>" not in line and line.rstrip().endswith(";")):
            n += 1
    return n


def collect(files, code):
    """(class -> instance member names, class -> files, file -> skip reason).

    A file declaring TWO partial classes is skipped rather than guessed at:
    members would be attributed to whichever was declared first, and a wrong
    member list is how a name-matching checker starts flagging correct code.
    No Game file does this today; the reason is COUNTED rather than printed
    inline so that the day one appears it lands in the drop clause instead of
    scrolling past above it.
    """
    members, owners, skipped = {}, {}, {}
    for f in files:
        names = set(PARTIAL.findall(code[f]))
        if len(names) != 1:
            skipped[f] = "twoPartialClasses" if names else BY_DESIGN
            continue
        cls = names.pop()
        owners.setdefault(cls, []).append(f)
        for line in code[f].split("\n"):
            hit = INSTANCE.match(line)
            if hit:
                members.setdefault(cls, set()).add(hit.group(1))
    return members, owners, skipped


def named_in(text, names):
    """Which of `names` this text uses UNQUALIFIED.

    `Foo.Bar` is somebody else's Bar; a bare `Bar` is ours.
    """
    return [n for n in names
            if re.search(r"(?<![\w.])" + re.escape(n) + r"\b", text)]


def body_of(line):
    """The part of a method's opening line that is already its body.

    A ONE-LINE BODY IS STILL A BODY, and the first version of this file could
    not see one: it noted the method, added the line's braces — which for
    `static void Wrong() { Populace.X = 3; }` net to zero — and `continue`d
    past the only line that mattered. The self-test's rejecting case said
    `nothing` where it should have said `Populace`.

    Both single-line shapes start after a token: a block body after `{`, an
    expression body after `=>`. Parameters are deliberately NOT scanned — a
    parameter named after an instance member shadows it, which compiles.
    """
    if "{" in line:
        return line[line.index("{") + 1:]
    if "=>" in line:
        return line[line.index("=>") + 2:]
    return ""


def scan_file(f, code, cls, names):
    """Every unqualified use of `names` inside a static method body.

    THE BRACE IS NOT ON THE SIGNATURE LINE. This codebase is Allman, so
    `public static void ApplyDetailToCrowd()` carries no `{` at all — the
    first version compared depth against itself on that line, found them
    equal, and closed the body before it had opened. It reported zero
    against the exact file that produced the CS0120.

    So the state is two things, not one: the depth OUTSIDE the method, and
    whether the body has actually opened yet. Only once it has can a
    depth comparison mean anything.
    """
    lines = code.split("\n")
    hits = []
    brace = 0
    outside = None      # brace depth outside the static method; None when not in one
    opened = False      # has the method's `{` been seen
    expr = False        # an `=>` body, which ends at its first `;` and has no braces
    for n, line in enumerate(lines, 1):
        moved = line.count("{") - line.count("}")
        if outside is None:
            if not STATIC_METHOD.match(line):
                brace += moved
                continue
            # `static extern void Foo();` and friends have no body at all.
            # Entering one would scan the whole rest of the file as if inside it.
            if "{" not in line and "=>" not in line and line.rstrip().endswith(";"):
                brace += moved
                continue
            outside = brace
            opened = "{" in line
            expr = "=>" in line and not opened
            text = body_of(line)
        else:
            text = line
            if not opened and "{" in line:
                opened = True
        for name in named_in(text, names):
            hits.append((f.name, n, cls, name))
        brace += moved
        if expr:
            if ";" in text:
                outside, expr = None, False
        elif opened and brace <= outside:
            outside = None
    return hits


class Reading(object):
    """ONE WHOLE WALK, taken from one set of file reads at one moment.

    Every number here is a WHOLE-WALK TOTAL — not a peak, not a sample, not a
    last-wins — so nothing needs an at-worst partner. `bad` is the finding and
    everything else is its denominator.

    `walked` IS THE FIX: it is the set of files `scan()` actually handed to
    `scan_file()`, appended by the scanner itself. The old line summed bodies
    over `files` in a loop beside the walk, so the printed denominator counted
    533 bodies the walk never opened. A count taken from the walk cannot
    inflate past the walk.
    """

    def __init__(self, bad, members, owners, walked, offered, bodies, skipped):
        self.bad = bad              # [(file, line, class, member)] findings
        self.members = members      # class -> instance member names
        self.owners = owners        # class -> files declaring it
        self.walked = walked        # files scan_file() was entered on
        self.offered = offered      # every file handed to the walk
        self.bodies = bodies        # file -> static bodies in it, one read each
        self.skipped = skipped      # file -> reason it was not walked

    @property
    def walked_bodies(self):
        return sum(self.bodies[f] for f in self.walked)

    @property
    def offered_bodies(self):
        return sum(self.bodies[f] for f in self.offered)

    @property
    def dropped_bodies(self):
        return self.offered_bodies - self.walked_bodies

    def by_reason(self, reason):
        """(files, bodies) dropped for one named reason."""
        fs = [f for f, r in self.skipped.items() if r == reason]
        return fs, sum(self.bodies[f] for f in fs)

    @property
    def measured(self):
        """Did this walk examine ANYTHING. A walk that entered no file must not
        print `0 errors`, which is the whole of rule 3b."""
        return bool(self.walked)


def scan(files, code=None):
    """Walk `files` and return the Reading. Findings are `.bad`."""
    code = read_all(files) if code is None else code
    bodies = {f: static_bodies(code[f]) for f in files}
    members, owners, skipped = collect(files, code)
    bad, walked = [], []
    for cls, fs in owners.items():
        names = members.get(cls, set())
        if not names:
            # NOT a silent `continue` any more: the class has no instance
            # member, so there is nothing for a static body to reach, and its
            # files land in the drop clause under their own reason.
            for f in fs:
                skipped[f] = "noInstanceMember"
            continue
        for f in fs:
            walked.append(f)
            bad.extend(scan_file(f, code[f], cls, names))
    return Reading(bad, members, owners, walked, list(files), bodies, skipped)


def summary_lines(r, where=""):
    """The reading, as the lines to print. THE ARITHMETIC AND THE STRING LIVE
    HERE, where the selftest runs them, rather than in the caller.

    Line 1 carries BOTH halves — what was walked and what was not — because a
    reader greps `lint-static:` and sees line 1 and nothing else. Lines 2 and 3
    break the skipped set down per reason and print the sum, so `walked` and
    `not scanned` can be checked against `offered` without re-deriving either.
    """
    if not r.offered:
        return ["lint-static: nothing measured — no `.cs` file%s"
                % (" under " + where if where else "")]
    if not r.measured:
        return ["lint-static: nothing measured — 0 of %d file(s) offered are in "
                "partial-class scope, so nothing was scanned; %d static bodies "
                "in %d file(s) NOT SCANNED"
                % (len(r.offered), r.offered_bodies, len(r.offered))]

    head = ("lint-static: %d static/instance error(s) "
            "(%d instance members across %d partial class(es) in %d file(s), "
            "%d static bodies walked); %d static bodies in %d file(s) NOT "
            "SCANNED — outside partial-class scope"
            % (len(r.bad), sum(len(v) for v in r.members.values()),
               len(r.owners), len(r.walked), r.walked_bodies,
               r.dropped_bodies, len(r.skipped)))

    parts = []
    for reason, why in REASONS.items():
        fs, n = r.by_reason(reason)
        # NAMED, not just counted, for the two reasons a person must act on;
        # the by-design 74 need no roll call. The cap announces itself.
        named = ("" if reason == BY_DESIGN or not fs
                 else " [%s]" % _capped(sorted(f.name for f in fs)))
        parts.append("%d bodies in %d file(s) %s%s" % (n, len(fs), why, named))
    return [head,
            "  not scanned, by reason: " + "; ".join(parts),
            "  arithmetic: %d walked + %d not scanned = %d static bodies in "
            "%d file(s) offered" % (r.walked_bodies, r.dropped_bodies,
                                    r.offered_bodies, len(r.offered))]


# --------------------------------------------------------------------- selftest

class _Fake(object):
    """A fixture file. SYNTHETIC BY CONSTRUCTION — in memory, never on disk, so
    no run of this tool can write under `ledger/` and no rejecting case is
    pinned to a real project file that improving the project would break."""

    def __init__(self, name, text):
        self.name = name
        self._t = text

    def read_text(self, encoding=None, errors=None):
        return self._t


OWNER_A = _Fake("SynthA.cs", """
namespace Synth.Fixture
{
    public partial class SynthOwner
    {
        public SynthPopulation Populace { get; private set; }

        public void Uses()
        {
            Populace.NearCap = 3;
        }
    }
}
""")

OWNER_B = _Fake("SynthB.cs", """
namespace Synth.Fixture
{
    public partial class SynthOwner
    {
        public static int Pure(int a)
        {
            return a + 1;
        }

        public static int Terse(int a) => a + 1;
    }
}
""")

# OUTSIDE THE SCOPE ON PURPOSE: not partial, so the walk never enters it. Four
# static bodies, which is what the old line would have added to `walked`.
LONER = _Fake("SynthLoner.cs", """
namespace Synth.Fixture
{
    public class SynthLoner
    {
        public static int One() { return 1; }
        public static int Two() { return 2; }
        public static int Three() { return 3; }
        public static int Four() => 4;
    }
}
""")

TWO_CLASSES = _Fake("SynthTwo.cs", """
namespace Synth.Fixture
{
    public partial class SynthOwner
    {
        public static int Ambiguous() { return 1; }
    }

    public partial class SynthOther
    {
        public static int AlsoAmbiguous() { return 2; }
    }
}
""")

NO_MEMBERS = _Fake("SynthBare.cs", """
namespace Synth.Fixture
{
    public partial class SynthBare
    {
        public static int Lonely() { return 1; }
    }
}
""")


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(("  ok    " if ok else "  FAIL  ") + what + ("   [%s]" % got if got else ""))
        ran.append(what)
        if not ok:
            fails.append(what)

    # ==================== ACCEPTING CASES FIRST (rule 5b) ====================
    # The expensive failure for a checker is not missing a fault, it is
    # rejecting everything, being switched off, and taking its reason for
    # existing with it. So the first thing asserted is that good input passes.

    print("ACCEPTING — the live codebase, which is the best fixture available")
    live_files = sorted(GAME.rglob("*.cs")) if GAME.is_dir() else []
    live = scan(live_files)
    lines = summary_lines(live, str(GAME))
    check(GAME.is_dir() and not live.bad,
          "today's Game layer passes — every hit on code that compiles is a "
          "false positive by definition",
          "%d finding(s) over %d walked file(s)" % (len(live.bad), len(live.walked)))
    check(live.measured and live.walked_bodies > 0,
          "and it examined something — a zero here is the silence rule 3b exists for",
          "%d static bodies in %d of %d file(s) walked"
          % (live.walked_bodies, len(live.walked), len(live.offered)))

    # THE BUG, PINNED ON THE LIVE TREE: the number printed is the count over the
    # set the scanner entered, not a sum over every file beside it. This is an
    # identity (it cannot break by the project improving) — the SIZE of the gap
    # is pinned synthetically below, where improving the project cannot move it.
    check(live.walked_bodies == sum(live.bodies[f] for f in live.walked)
          and live.walked_bodies + live.dropped_bodies == live.offered_bodies
          and len(live.walked) + len(live.skipped) == len(live.offered),
          "the printed denominator IS the walk — walked + not-scanned = offered, "
          "in files and in bodies",
          "%d+%d=%d bodies, %d+%d=%d files"
          % (live.walked_bodies, live.dropped_bodies, live.offered_bodies,
             len(live.walked), len(live.skipped), len(live.offered)))

    # THE CONSUMER'S PARSE, BOTH DIRECTIONS. Another lint's rewrite in this
    # project silently dropped the token its verify parse grepped for, which
    # would have removed the denominator from every future GREEN footer with
    # no red run to say so.
    m = re.search(VERIFY_PARSE, "\n".join(lines))
    check(bool(m) and m.group(2) == str(live.walked_bodies),
          "ledger/verify.py:947's regex still matches, and lifts the WALKED "
          "count into the footer",
          "groups=%s walked=%d" % (m.groups() if m else None, live.walked_bodies))
    verify_py = ROOT / "ledger" / "verify.py"
    src = verify_py.read_text(encoding="utf-8") if verify_py.is_file() else ""
    check(VERIFY_PARSE in src,
          "and the copy kept in this file is byte-identical to the one in "
          "verify.py (if this fails, verify changed its parse — read it, do "
          "not edit this line to match)",
          "found in %s" % (verify_py.name if src else "NOTHING MEASURED — verify.py unreadable"))

    print("\nACCEPTING — synthetic code with nothing wrong")
    good = scan([OWNER_A, OWNER_B])
    check(not good.bad,
          "an instance method using an instance member, and two static methods "
          "using neither, all pass",
          "%d finding(s) of %d bodies walked" % (len(good.bad), good.walked_bodies))

    # `other.Populace` is somebody else's, and must not be flagged.
    qual = scan([OWNER_A, _Fake("SynthQual.cs", """
namespace Synth.Fixture
{
    public partial class SynthOwner
    {
        public static void Fine(SynthOwner g)
        {
            g.Populace.NearCap = 3;
        }
    }
}
""")])
    check(not qual.bad,
          "and one reached THROUGH a reference is not flagged",
          "%d finding(s)" % len(qual.bad))

    # ================= THE DROP CLAUSE, WHICH IS THE FIX =================
    print("\nTHE DROP CLAUSE — files inside and outside partial-class scope, in one walk")
    mixed = scan([OWNER_A, OWNER_B, LONER])
    out_files, out_bodies = mixed.by_reason(BY_DESIGN)
    check(len(mixed.walked) == 2 and mixed.walked_bodies == 2
          and len(out_files) == 1 and out_bodies == 4,
          "both counts are reported and they are RIGHT — 2 bodies in 2 files "
          "walked, 4 bodies in 1 file not scanned",
          "walked %d bodies/%d files, not scanned %d bodies/%d files"
          % (mixed.walked_bodies, len(mixed.walked), out_bodies, len(out_files)))
    check(mixed.walked_bodies + mixed.dropped_bodies == mixed.offered_bodies == 6
          and len(mixed.walked) + len(mixed.skipped) == len(mixed.offered) == 3,
          "and they SUM to the total mentions",
          "%d+%d=%d bodies over %d+%d=%d files"
          % (mixed.walked_bodies, mixed.dropped_bodies, mixed.offered_bodies,
             len(mixed.walked), len(mixed.skipped), len(mixed.offered)))
    # THE REGRESSION PIN, and it is synthetic so improving the project cannot
    # move it: the old line printed the OFFERED total under the word `walked`.
    text = "\n".join(summary_lines(mixed))
    check("2 static bodies walked" in text and "6 static bodies walked" not in text
          and "4 static bodies in 1 file(s) NOT SCANNED" in text,
          "THE 19x BUG ITSELF — the line says 2 walked, never 6, and names the 4 "
          "it did not open",
          text.splitlines()[0][13:])

    print("\nTHE DROP CLAUSE — the two reasons that are NOT by design")
    two = scan([OWNER_A, OWNER_B, TWO_CLASSES])
    tf, tb = two.by_reason("twoPartialClasses")
    # tb IS 2, NOT 1, AND THE FIRST VERSION OF THIS LINE SAID 1 — the fixture
    # declares one static body in EACH of its two partial classes. The selftest
    # went red on its own arithmetic before the tool ever shipped, which is the
    # only reason that number is measured rather than assumed.
    check(len(tf) == 1 and tb == 2 and "SynthTwo.cs" in "\n".join(summary_lines(two)),
          "a file declaring two partial classes is counted under its own reason "
          "and NAMED (attribution would be a guess)",
          "%d bodies in %d file(s): %s" % (tb, len(tf), [f.name for f in tf]))
    bare = scan([NO_MEMBERS])
    bf, bb = bare.by_reason("noInstanceMember")
    check(len(bf) == 1 and bb == 1 and not bare.measured,
          "a partial class with NO instance member is counted under its own "
          "reason, not folded into the walk",
          "%d bodies in %d file(s), measured=%s" % (bb, len(bf), bare.measured))

    # ================= NOTHING MEASURED PRINTS WORDS =================
    print("\nNOTHING MEASURED — the case that must not read as clean")
    empty = "\n".join(summary_lines(scan([]), "/nowhere"))
    check("nothing measured" in empty and "error" not in empty
          and not re.search(VERIFY_PARSE, empty),
          "an empty walk prints the WORDS, never `0 ... errors`, and does not "
          "match verify's pass parse",
          empty)
    none_in_scope = "\n".join(summary_lines(scan([LONER]), "/nowhere"))
    check("nothing measured" in none_in_scope
          and "4 static bodies in 1 file(s) NOT SCANNED" in none_in_scope
          and not re.search(VERIFY_PARSE, none_in_scope),
          "and a walk offered files but entering none says so WITH its "
          "denominator, and still cannot read as a pass",
          none_in_scope)

    # ================= REJECTING — the tool's actual job =================
    print("\nREJECTING — the CS0120 this tool exists for")
    allman = scan([OWNER_A, _Fake("SynthC.cs", """
namespace Synth.Fixture
{
    public partial class SynthOwner
    {
        public static void ApplyDetailToCrowd()
        {
            if (Populace == null) return;
            Populace.NearCap = 3;
        }
    }
}
""")])
    check(len(allman.bad) == 2 and all(h[3] == "Populace" for h in allman.bad),
          "the real CS0120 — a static ALLMAN method reaching an instance member "
          "— is caught (the shape the first version could not see)",
          "%d of 2 uses, members=%s"
          % (len(allman.bad), sorted({h[3] for h in allman.bad})))

    one_liner = scan([OWNER_A, _Fake("SynthE.cs", """
namespace Synth.Fixture
{
    public partial class SynthOwner
    {
        public static void Wrong() { Populace.NearCap = 3; }
        public static void AlsoWrong() => Populace.NearCap = 4;
    }
}
""")])
    check(len(one_liner.bad) == 2,
          "and so are the one-line and expression-bodied forms",
          "%d of 2" % len(one_liner.bad))
    check(len(summary_lines(one_liner)) == 3
          and "2 static/instance error(s)" in summary_lines(one_liner)[0]
          and "2 static bodies walked" in summary_lines(one_liner)[0],
          "a FINDING still ships its denominator — the summary prints beside "
          "the hits rather than instead of them",
          summary_lines(one_liner)[0][13:])

    ok = not fails
    print("\nlint-static --selftest: %s — %d checks, %d failed"
          % ("PASS" if ok else "FAILED", len(ran), len(fails)))
    print("  denominators: live %d static bodies in %d of %d Game file(s) walked, "
          "%d bodies in %d file(s) not scanned; synthetic %d fixture file(s), "
          "0 written to disk, 0 project file(s) modified"
          % (live.walked_bodies, len(live.walked), len(live.offered),
             live.dropped_bodies, len(live.skipped), 8))
    return 0 if ok else 1


def main():
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # `| head` must not traceback
    except (AttributeError, ValueError):
        pass
    if "--selftest" in sys.argv or "--self-test" in sys.argv:
        return selftest()
    if not GAME.is_dir():
        print("lint-static: nothing measured — no Game folder at %s" % GAME)
        return 2
    files = sorted(GAME.rglob("*.cs"))
    r = scan(files)
    if r.bad:
        print("lint-static: %d static method(s) reaching an instance member "
              "— this is CS0120 and the Windows build is where you will find out:"
              % len(r.bad))
        for name, line, cls, member in r.bad:
            print("  %s:%d  '%s' is an instance member of %s" % (name, line, member, cls))
    for line in summary_lines(r, str(GAME)):
        print(line)
    if not r.measured:
        return 2
    return 1 if r.bad else 0


if __name__ == "__main__":
    sys.exit(main())
