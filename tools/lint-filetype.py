#!/usr/bin/env python3
"""A FILENAME IS NOT A TYPE NAME, and in this project it usually is not.

    python3 tools/lint-filetype.py              # the sweep
    python3 tools/lint-filetype.py --selftest   # accepting case FIRST

WHY THIS EXISTS. `SimDirector` referenced `TrafficHost.BrakeLampsPeak`. There is
no type called `TrafficHost` anywhere in the codebase: `TrafficHost.cs` declares
`partial class GameController`, like thirteen other files in the Game layer.
The build came back NO PLAYER LOG with `CS0103: The name 'TrafficHost' does not
exist in the current context`, and by then three more commits were sitting on
top of it.

WHY NOTHING LOCAL CAUGHT IT. CS0103 is a name-RESOLUTION error, and ShapeCheck
runs reference-independent diagnostics only — the same blind spot that already
cost a round trip each for CS0119 (`lint-shadow`), CS0426 (`lint-nested`) and
CS0120 (`lint-static`). This is the fourth member of that family and the
cheapest to check, because it needs no type resolution at all: it is a set
difference between the filenames somebody might mistake for types and the type
names that actually exist.

MEASURED BEFORE BEING WRITTEN, so this is a real trap and not a tidy rule.
Fourteen of the Game layer's files declare no type of their own name —
AccessHost, ActOne, ActThreeHost, DirectorHost, IntentBridge, OperationHost,
OsseiSetup, PhoneSetup, PhoneUI, PlanUI, PopulationHost, PurseSetup,
TrafficHost, UiSmokeTest. Every one of them is a `GameController` partial or a
class under another name, and every one of them reads like a type at a call
site. (That sentence is history and the number moves: the sweep PRINTS the
trap set's size every run, because a rule quoting fourteen for ever is the
comment decay this project keeps paying for. 13 on 26 Aug — `ActOne` acquired
a member of its own name.)

SCOPE, AND IT IS DELIBERATELY NARROW. Only identifiers that ARE a filename stem
somewhere in the project and are NOT a declared type anywhere. That is the exact
mistake being made. A wider check — "every capitalised identifier must resolve"
— would need the compiler this file exists to work without, and would drown in
Unity's own types.

RULE 5b: THE LIVE CODEBASE IS THE ACCEPTING CASE. Every hit on today's code is
a false positive by definition, because the project compiles in CI. Run it over
everything, expect zero, and only then trust a red.

WHAT THE 26 AUG REWRITE CHANGED, AND WHY IT IS THE SAME BUG AS THE ONE ABOVE.
This tool exited **0 over an empty tree**, printing
`0 filename-as-type error(s) (0 file(s) scanned, 0 type(s) declared, 0
filename(s) that are not types)` — a human reading that line can see the
zeros, and `ledger/verify.py`, which reads it with a regex, reported
**GREEN: 0 filename-as-type errors (0 files, 0 filenames that are not
types)**. Measured, not reasoned: the tool was copied over a tree with no
`Assets/` and the wrapper was fed its real output.

So a run that could not look was indistinguishable from a run that found
nothing wrong, in the only channel that decides whether a commit lands. Three
states now exit 2 with the words `nothing measured`, each printing what it DID
count, and the sweep prints its walked/skipped breakdown with a checkable
identity — the shape `lint-static`, `lint-nested` and `lint-avenues` already
carry.

EXIT CODES. 0 swept and clean; 1 found a CS0103 waiting to happen; 2 NOTHING
MEASURED — no files, no declared types, or an empty trap set. A reader chasing
a CS0103 that does not exist is exactly the wrong turn, so 2 must never be
printed by anybody as a finding.
"""
import re
import signal
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN = [ROOT / "ledger" / "Assets" / "Scripts", ROOT / "ledger" / "Assets" / "Editor"]

# EVERY CAP ANNOUNCES ITSELF, and there is ONE implementation of that idea in
# this repository — `tools/capsay.py`. Imported rather than copied: a second
# `(+N more)` is the site that one day forgets to say it bit.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from capsay import cap as _cap, NOTHING_MEASURED   # noqa: E402

# A VERBATIM COPY OF THE REGEX IN `ledger/verify.py:filename_as_type`, kept here
# so the selftest can run the real consumer's parse against the real line, and
# can say by NAME when the two have drifted. verify.py is the source of truth
# and is not edited from here. A rewrite that silently changed this line would
# drop the denominator out of every future GREEN footer with no red run to say
# so — which is what happened to `lint-shadow`'s census, byte-identical in 259
# landed commit messages.
VERIFY_PARSE = r"\((\d+) file\(s\) scanned, (\d+) type\(s\) declared, (\d+) filename"

# Any type declaration. `partial` and access modifiers are skipped by the
# pattern rather than enumerated, so a new modifier does not silently disable
# the check.
DECL = re.compile(r"\b(?:class|struct|interface|enum|record)\s+([A-Za-z_]\w*)")

# `Foo.Bar` where Foo starts with a capital — a static access or a type
# qualifier. The negative lookbehind drops `something.Foo.Bar`, which is a
# member chain and not a type reference.
USE = re.compile(r"(?<![\w.])([A-Z]\w*)\s*\.\s*[A-Za-z_]\w*")

# Comments and plain strings carry type names in prose constantly — every
# paragraph in this project does — and none of them compile.
COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
PLAIN = re.compile(r'(?<!\$)"(?:[^"\\]|\\.)*"')

# INTERPOLATED STRINGS ARE CODE, AND THE FIRST VERSION OF THIS THREW THEM AWAY.
#
# The lint scored zero on the very line that prompted it. `TrafficHost` was in
# the trap set, the regex was right, and the reference never reached either —
# because it lives inside `$"...{TrafficHost.BrakeLampsPeak}..."` and the
# stripper removed every double-quoted run wholesale.
#
# That is not a corner. `SimDirector`'s done-line is one interpolated string
# hundreds of expressions long, and it is where most of this project's
# Game-layer statics are read. A check blind to `$"..."` is blind to the place
# the mistake actually happens.
#
# Caught only because rule 5b was applied: the accepting case passed, and the
# REJECTING case — the real error, put back — passed too. A lint that returns
# zero on everything is not a lint. The selftest below keeps that rejecting
# case in the interpolated form for exactly this reason.
INTERP = re.compile(r'\$"(?:[^"\\]|\\.)*"', re.S)
BRACED = re.compile(r"\{([^{}]*)\}")


def code_only(text):
    """Comments and plain string literals blanked; the EXPRESSIONS inside
    interpolated strings kept, because they are compiled."""
    text = COMMENT.sub(" ", text)
    text = INTERP.sub(lambda m: " ".join(BRACED.findall(m.group(0))), text)
    return PLAIN.sub(" ", text)

# A property, field or method DECLARATION — `public static Foo Bar` / `Bar =>` /
# `Bar {`. Deliberately loose: this set is only ever used to EXCLUDE, so a false
# member costs a missed error and a missed member costs a false alarm, and the
# second is far more expensive in a check people have to trust.
MEMBER = re.compile(
    r"\b(?:public|internal|protected|private)\s+(?:static\s+|readonly\s+|"
    r"virtual\s+|override\s+|abstract\s+|partial\s+|const\s+|new\s+)*"
    r"[\w<>\[\],?\.]+\s+([A-Z]\w*)\s*(?:=>|\{|;|=|\()")


def IS_CORE(path):
    """Core filenames collide with `GameController` property names constantly —
    `Empire`, `Harm`, `Suspicion`, `Traffic` and fourteen others. Excluding the
    folder is cruder than resolving the name and is the honest trade: this check
    is worth having only if it never cries wolf."""
    return "Core" in path.parts


def sources():
    for root in SCAN:
        if root.exists():
            yield from sorted(root.rglob("*.cs"))


def _rel(f):
    try:
        return str(f.relative_to(ROOT))
    except (ValueError, AttributeError):
        return getattr(f, "name", str(f))    # fail readable, not with a traceback


# THE ORDER IS PART OF THE ARITHMETIC. A stem can be several of these at once —
# `Traffic` declares a type AND is a member name AND sits under Core — so the
# breakdown only sums to the whole if each stem is counted once, under the FIRST
# reason that fits. The order is printed with the numbers so a reader can check
# it rather than take it on trust.
REASONS = [
    ("declaresType", "declare a type of their own name — the normal case, "
                     "nothing to mistake"),
    ("memberName", "are a member name somewhere, so `Name.` is a member access "
                   "and compiles"),
    ("underCore", "sit under Core/, where filenames collide with GameController "
                  "properties by the dozen and a name-matcher cannot tell them "
                  "apart"),
]


class Reading(object):
    """One sweep. THE TALLY AND THE ARITHMETIC LIVE HERE, next to the selftest
    that runs them, rather than in the printer or in verify."""

    def __init__(self, bad, offered, declared, stems, members, traps, reasons,
                 pairs, stem_pairs, dupes):
        self.bad = bad                  # the findings: (file, line, name, owner)
        self.offered = offered          # every .cs file handed to the scan
        self.declared = declared        # distinct type names declared anywhere
        self.stems = stems              # distinct filename stem -> first file
        self.members = members          # distinct member names, for exclusion
        self.traps = traps              # stem -> file, the set searched FOR
        self.reasons = reasons          # reason -> [stem], each stem counted once
        self.pairs = pairs              # `Name.Member` references examined (cumulative)
        self.stem_pairs = stem_pairs    # ... of those, whose Name is a filename
        self.dupes = dupes              # stem -> [files], collapsed by first-wins

    @property
    def measured(self):
        """Three ways this sweep can have examined nothing: no files, no type
        declarations to difference against, or an empty trap set. The third is
        the quiet one — a full walk of a real tree that could not have produced
        a finding, which is precisely rule 3b's `0 errors` over nothing."""
        return bool(self.offered) and bool(self.declared) and bool(self.traps)

    @property
    def dropped_files(self):
        return sum(len(v) - 1 for v in self.dupes.values())


def scan(files):
    offered = list(files)
    declared, stems, dupes = set(), {}, {}
    for f in offered:
        text = f.read_text(encoding="utf-8", errors="replace")
        declared.update(DECL.findall(text))
        # FIRST WINS, AND IT USED TO WIN SILENTLY. `stems.setdefault` collapses
        # two files of the same name onto one owner, and the loser was never
        # counted anywhere — the same silent-collapse shape found in
        # `lint-unreached` the same night. 0 on 26 Aug, and it is PRINTED, so
        # the day it stops being 0 somebody is told rather than left with a
        # denominator that quietly describes fewer files than it names.
        if f.stem in stems:
            dupes.setdefault(f.stem, [stems[f.stem]]).append(f)
        else:
            stems[f.stem] = f

    code, members = {}, set()
    for f in offered:
        code[f] = code_only(f.read_text(encoding="utf-8", errors="replace"))
        members.update(MEMBER.findall(code[f]))

    # THE TRAP SET, AND THE FIRST VERSION OF IT WAS WRONG — which the live
    # codebase said immediately, exactly as rule 5b promises.
    #
    # v1 took every filename that is not a type. That flagged hundreds of lines
    # that compile perfectly, because C# capitalises PROPERTIES too: `Suspicion`,
    # `Empire`, `ActThree`, `Harm` and fourteen more are Core filenames AND
    # `GameController` property names, so `Empire.Businesses` is a property
    # chain and not a type reference. A capitalised identifier before a dot
    # cannot be told from a type without resolution, which is the thing this
    # file exists to work without.
    #
    # So the set is narrowed to what the actual mistake was: a GAME-LAYER file
    # named like a type, that declares no type, whose name is also not a member
    # anywhere. Those thirteen — AccessHost, TrafficHost, PhoneUI and the rest —
    # are `GameController` partials and there is nothing they could legitimately
    # qualify. Core filenames are excluded outright, because that is where the
    # property collisions live.
    #
    # Printed even when zero, because it is the DENOMINATOR: "0 errors" over an
    # empty trap set means the convention changed, not that the code is clean,
    # and those look identical without the number. Since 26 Aug an empty trap
    # set does not merely print — it exits 2, because no reader downstream
    # distinguished the two on their own.
    reasons = {k: [] for k, _ in REASONS}
    traps = {}
    for s, f in sorted(stems.items()):
        if s in declared:
            reasons["declaresType"].append(s)
        elif s in members:
            reasons["memberName"].append(s)
        elif IS_CORE(f):
            reasons["underCore"].append(s)
        else:
            traps[s] = f

    bad, pairs, stem_pairs = [], 0, 0
    for f in offered:
        for i, line in enumerate(code[f].splitlines(), 1):
            for name in USE.findall(line):
                pairs += 1
                if name in stems:
                    stem_pairs += 1
                if name in traps:
                    bad.append((_rel(f), i, name, traps[name].name))
    return Reading(bad, offered, declared, stems, members, traps, reasons,
                   pairs, stem_pairs, dupes)


def summary_lines(r, where=""):
    """The reading, as the lines to print.

    Line 1 carries the head verify parses and is BYTE-IDENTICAL to the line
    this tool has printed since it was written — a landed series does not get
    reworded, it gets added to. Lines 2-4 are the addition: the ladder (what
    was examined at each rung), the trap set's complement broken down by
    reason, and an identity a reader checks on the line without re-deriving
    anything.
    """
    if not r.offered:
        return ["lint-filetype: nothing measured — no `.cs` file%s"
                % (" under " + where if where else "")]
    if not r.declared:
        return ["lint-filetype: nothing measured — %d file(s) read and 0 type "
                "declaration(s) found in any of them, so there is nothing to "
                "difference the filenames against"
                % len(r.offered)]
    if not r.traps:
        # DELIBERATELY WORDED SO IT CANNOT MATCH `VERIFY_PARSE` — the selftest
        # asserts that. A nothing-measured line that a consumer's pass-parse
        # accepts is the whole fault this rewrite exists for.
        return ["lint-filetype: nothing measured — the trap set is empty: 0 of "
                "%d distinct filename stem(s) name something that declares no "
                "type (%d type declaration(s) seen), so this sweep could not "
                "have found an error"
                % (len(r.stems), len(r.declared))]

    head = ("lint-filetype: %d filename-as-type error(s) "
            "(%d file(s) scanned, %d type(s) declared, "
            "%d filename(s) that are not types)"
            % (len(r.bad), len(r.offered), len(r.declared), len(r.traps)))

    ladder = ("  ladder, each rung a cumulative count over the whole sweep: "
              "%d qualified reference(s) `Name.Member` in code -> %d whose "
              "`Name` is a filename in this project -> %d whose filename "
              "declares no type, which is the finding"
              % (r.pairs, r.stem_pairs, len(r.bad)))

    parts = []
    for key, why in REASONS:
        names = r.reasons[key]
        parts.append("%d %s [%s]" % (len(names), why,
                                     _cap(names, keep=3, sep=", ", width=28)))
    dup_clause = ("%d file(s) dropped as a duplicate filename stem [%s]"
                  % (r.dropped_files,
                     _cap(sorted(r.dupes), keep=3, sep=", ", width=28,
                          tail="none")))
    return [head,
            ladder,
            "  not in the trap set, by reason, FIRST MATCH WINS in this order: "
            + "; ".join(parts),
            "  arithmetic: %d trap(s) + %s = %d distinct filename stem(s); "
            "%d stem(s) + %s = %d file(s) scanned"
            % (len(r.traps),
               " + ".join("%d %s" % (len(r.reasons[k]), k) for k, _ in REASONS),
               len(r.stems), len(r.stems), dup_clause, len(r.offered))]


# --------------------------------------------------------------------- selftest

class _Fake(object):
    """A fixture file. SYNTHETIC BY CONSTRUCTION — in memory, never on disk, and
    named `Synth*` so no rejecting case is pinned to a real project file. Fixing
    the project must never be able to break the test that guards it."""

    def __init__(self, name, text, parts=("Synth", "Game")):
        self.name = name
        self.stem = name[:-3] if name.endswith(".cs") else name
        self.parts = parts
        self._t = text

    def read_text(self, encoding=None, errors=None):
        return self._t


# A file named like a type that declares none — a `GameController` partial, the
# real shape of all thirteen live traps.
SYNTH_HOST = _Fake("SynthHost.cs", """
namespace Synth.Fixture
{
    public partial class SynthController
    {
        public static int BrakeLampsPeak = 3;
    }
}
""")

# A file that declares the type it is named after: the normal case, and the one
# a wrong version of this check would flag.
SYNTH_TYPE = _Fake("SynthMeter.cs", """
namespace Synth.Fixture
{
    public class SynthMeter
    {
        public static int Reading = 1;
    }
}
""")


def selftest():
    ran, fails = [], []

    def check(ok, label, detail=""):
        ran.append(label)
        if not ok:
            fails.append(label)
        print("  %-4s %s%s" % ("ok" if ok else "FAIL", label,
                               ("\n         " + str(detail)) if detail else ""))

    print("lint-filetype --selftest — ACCEPTING CASES FIRST (rule 5b: the")
    print("expensive failure is a validator nothing survives)\n")

    # ================= ACCEPTING: THE LIVE TREE =================
    # Every hit on today's code is a false positive BY DEFINITION, because CI
    # compiles this code. That makes the repository the best accepting fixture
    # available and one no fixture of mine can fake.
    print("ACCEPTING — the live repository, which compiles in CI")
    live = scan(sources())
    lines = summary_lines(live, str(SCAN[0]))
    check(not live.bad,
          "the live tree is clean — every hit here would be a false positive",
          "%d finding(s) over %d file(s)" % (len(live.bad), len(live.offered)))
    check(live.measured and live.pairs > 0 and live.traps,
          "and it EXAMINED something — a zero over nothing is the silence "
          "rule 3b exists for",
          "%d qualified reference(s), %d trap(s), %d type(s) declared"
          % (live.pairs, len(live.traps), len(live.declared)))

    # AN IDENTITY, NOT A NUMBER: it cannot break by the project improving, and
    # it is the same check a reader makes on the printed arithmetic line.
    check(len(live.traps) + sum(len(v) for v in live.reasons.values())
          == len(live.stems)
          and len(live.stems) + live.dropped_files == len(live.offered),
          "the printed denominator IS the walk — traps + reasons = stems, "
          "stems + duplicates = files scanned",
          "%d+%d=%d stems, %d+%d=%d files"
          % (len(live.traps), sum(len(v) for v in live.reasons.values()),
             len(live.stems), len(live.stems), live.dropped_files,
             len(live.offered)))
    check(live.stem_pairs <= live.pairs and len(live.bad) <= live.stem_pairs,
          "and the ladder's rungs only narrow — each one is a subset of the "
          "one above it",
          "%d pairs >= %d on a filename >= %d findings"
          % (live.pairs, live.stem_pairs, len(live.bad)))

    # ================= THE CONSUMER'S PARSE, BOTH DIRECTIONS =================
    m = re.search(VERIFY_PARSE, "\n".join(lines))
    check(bool(m) and m.group(1) == str(len(live.offered))
          and m.group(3) == str(len(live.traps)),
          "ledger/verify.py's regex still matches the live line, and lifts the "
          "SCANNED and TRAP counts into the footer",
          "groups=%s files=%d traps=%d"
          % (m.groups() if m else None, len(live.offered), len(live.traps)))
    verify_py = ROOT / "ledger" / "verify.py"
    src = verify_py.read_text(encoding="utf-8") if verify_py.is_file() else ""
    check(VERIFY_PARSE in src,
          "and the copy kept in this file is byte-identical to the one in "
          "verify.py (if this fails, verify changed its parse — read it, do "
          "not edit this line to match)",
          "found in %s" % (verify_py.name if src
                           else "%s — verify.py unreadable" % NOTHING_MEASURED))

    # ================= ACCEPTING: SYNTHETIC =================
    print("\nACCEPTING — synthetic code with nothing wrong")
    good = scan([SYNTH_TYPE, _Fake("SynthUser.cs", """
namespace Synth.Fixture
{
    public class SynthUser
    {
        public void Read() { int a = SynthMeter.Reading; }
    }
}
""")])
    check(not good.bad,
          "a file that DOES declare its own type is not a trap, and reading it "
          "is not an error",
          "%d finding(s), %d trap(s)" % (len(good.bad), len(good.traps)))

    prose = scan([SYNTH_HOST, SYNTH_TYPE, _Fake("SynthProse.cs", '''
namespace Synth.Fixture
{
    public class SynthProse
    {
        // SynthHost.BrakeLampsPeak is named here in a comment and compiles nowhere.
        public string Say() { return "SynthHost.BrakeLampsPeak"; }
    }
}
''')])
    check(not prose.bad and "SynthHost" in prose.traps,
          "a trap named in a COMMENT and in a plain string is not flagged, "
          "while still being in the trap set",
          "%d finding(s), traps=%s" % (len(prose.bad), sorted(prose.traps)))

    # ================= NOTHING MEASURED — THE FAULT THIS REWRITE FIXES ========
    print("\nNOTHING MEASURED — three states that must not read as clean")
    empty = "\n".join(summary_lines(scan([]), "/nowhere"))
    check("nothing measured" in empty and "error(s)" not in empty
          and not re.search(VERIFY_PARSE, empty),
          "an empty sweep prints the WORDS, never `0 ... error(s)`, and cannot "
          "match verify's pass parse",
          empty)
    typeless = "\n".join(summary_lines(scan([_Fake("SynthBlank.cs", "// nothing here\n")])))
    check("nothing measured" in typeless and "1 file(s) read" in typeless
          and not re.search(VERIFY_PARSE, typeless),
          "a sweep that read files but found no type declaration says so WITH "
          "its denominator",
          typeless)
    # A tree of one file that declares its own type: nothing could ever be a
    # trap, so the sweep is structurally incapable of a finding.
    notraps = "\n".join(summary_lines(scan([SYNTH_TYPE])))
    check("nothing measured" in notraps and "0 of 1 distinct filename" in notraps
          and not re.search(VERIFY_PARSE, notraps),
          "and an EMPTY TRAP SET — a full walk that could not have found "
          "anything — is nothing measured too, with what it did count",
          notraps)

    # ================= REJECTING — the CS0103 this tool exists for ===========
    print("\nREJECTING — the real error, put back")
    plain = scan([SYNTH_HOST, SYNTH_TYPE, _Fake("SynthDirector.cs", """
namespace Synth.Fixture
{
    public class SynthDirector
    {
        public void Emit() { int n = SynthHost.BrakeLampsPeak; }
    }
}
""")])
    check(len(plain.bad) == 1 and plain.bad[0][2] == "SynthHost",
          "a filename with no type, read as a type in plain code, is caught",
          "%s" % (plain.bad,))

    # THE FORM THAT SCORED ZERO ON THE VERY LINE THAT PROMPTED THIS TOOL.
    interp = scan([SYNTH_HOST, SYNTH_TYPE, _Fake("SynthVerdict.cs", '''
namespace Synth.Fixture
{
    public class SynthVerdict
    {
        public string Done() { return $"lamps={SynthHost.BrakeLampsPeak} ok"; }
    }
}
''')])
    check(len(interp.bad) == 1 and interp.bad[0][2] == "SynthHost",
          "and so is one inside `$\"...\"`, which IS code and which the first "
          "version threw away wholesale",
          "%s" % (interp.bad,))
    finding = summary_lines(interp)
    check(len(finding) == 4 and "1 filename-as-type error(s)" in finding[0]
          and re.search(VERIFY_PARSE, finding[0]),
          "a FINDING still ships its denominator — the summary prints beside "
          "the hits, not instead of them",
          finding[0][15:])

    ok = not fails
    print("\nlint-filetype --selftest: %s — %d checks, %d failed"
          % ("PASS" if ok else "FAILED", len(ran), len(fails)))
    print("  denominators: live %d file(s) scanned, %d type(s) declared, "
          "%d trap(s), %d qualified reference(s) examined; synthetic %d fixture "
          "file(s), 0 written to disk, 0 project file(s) modified"
          % (len(live.offered), len(live.declared), len(live.traps),
             live.pairs, 7))
    return 0 if ok else 1


def main():
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # `| head` must not traceback
    except (AttributeError, ValueError):
        pass
    # DISPATCHED FIRST AND RETURNED FROM, because `lint-shadow`'s `--selftest`
    # fell through to the live sweep and exited 0 — a guard that had never run
    # looked exactly like one that passed, for as long as it existed.
    if "--selftest" in sys.argv or "--self-test" in sys.argv:
        return selftest()

    r = scan(sources())
    for path, line, name, owner in r.bad:
        print("%s:%d: `%s.` is not a type — %s declares no type of that name "
              "(CS0103)" % (path, line, name, owner))
    for line in summary_lines(r, ", ".join(_rel(p) for p in SCAN)):
        print(line)
    if not r.measured:
        return 2
    return 1 if r.bad else 0


if __name__ == "__main__":
    sys.exit(main())
