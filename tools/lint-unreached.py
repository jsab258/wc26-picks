#!/usr/bin/env python3
"""PUBLIC GAME-LAYER METHODS THAT NOTHING CALLS.

    python3 tools/lint-unreached.py             # the reading
    python3 tools/lint-unreached.py --selftest  # accepting case FIRST

WHY THIS EXISTS, AND IT IS THE LARGEST THING FOUND ON 4 AUGUST.

`GameController.RecordKilling` is the only path into `HomicideBook`. It has no
callers. So the register is empty in every run, `Pressure` returns zero,
`Stage` returns `Inquiry.None`, and `inquiry=None` in all 131 kept verdicts —
which means the paper naming you, the redirect having anything to relieve,
`Police.ForcesActThree` and `Police.BarsQuietExit` have between them never
executed once in the recorded history of this project.

One missing call, a whole stage of the game, and NOTHING WAS ASKING.
`ReachCheck` answers exactly this question — "does anything actually call it" —
for public CORE APIs, and the reach ledger has thirty-five entries because of
it. `RecordKilling` is Game-layer, so it was never in scope. The ledger is the
Core half of a question nobody asks about the other half, and the biggest hole
turned out to be on the side with no instrument.

WHY IT IS A GREP AND NOT A GRAPH WALK. `ReachCheck` can walk a graph because
the Game layer NAMES the Core members it uses and the roots are obvious. The
Game layer's own roots are not: Unity calls `Awake`, `Update`, `OnDisable` and
a dozen others with no reference anywhere, `SendMessage` and the inspector can
reach anything, and a graph walk that did not know all of them would report
half the codebase as dead. So this asks the narrow question it can answer
honestly — is this NAME mentioned anywhere else in the layer — and says out
loud that a name-matcher cannot see reflection.

THE LIVE CODEBASE IS THE ACCEPTING CASE, which is the discipline the seven
`lint-*` tools already follow: every hit on today's code is either a real
finding or a false positive worth suppressing by name, and there is no fixture
to be fooled by. Run it, read every hit, and add the Unity lifecycle and the
genuinely-by-design ones to the skip list with a reason.

--------------------------------------------------------------------------
WHAT THE 26 AUG REWRITE CHANGED. Three faults, all in one printed line, all
the shape rule 3b names: a number that describes something other than what
was walked.

    files walked: 94 = 88 Game + 6 Assets/Editor    (all 94 called "Game-layer")
    declarations matched: 426
      silently dropped as a Unity lifecycle name:  13   (all of them `Reset`)
      silently collapsed onto an earlier same name: 62   (23 names, `Build` x14)
      distinct names examined:                     351   <- printed as
                                                            "351 public methods"
    arithmetic: 351 + 13 + 62 = 426

So the denominator named a layer six of its files are not in, and counted
distinct NAMES while calling them declarations — 75 of 426 declarations were
dropped or collapsed with no line saying so. The repair was already inside
this same file: the 2 workflow exclusions ARE printed by name. One idea, two
implementations, and the one nobody looked at was the one missing the line.

AND THE COLLAPSE IS A BLIND SPOT, NOT ONLY A DENOMINATOR. This tool asks about
NAMES. `Build` is declared 14 times; if thirteen of those are dead and one is
called, the name reads as reached and all fourteen disappear. That is now
printed as a reason with its size, because a limit nobody is told about is
indistinguishable from a finding.

AND IT TOOK 38 SECONDS, which is why a hand-run tool stays unrun. Two regex
sweeps of the whole 3MB corpus PER NAME, 351 times. The declaration counts now
come from the single parse that already ran, and mentions from one tokenised
pass — same arithmetic, one implementation of each, ~1s.

EXIT CODES. 0 the sweep ran and reported (WITH findings or without — this is a
reading, not a gate: the commit that WIRES one of these must not be blocked by
a check that fails on the list). 2 NOTHING MEASURED — no files, or no public
declaration matched at all. Never 1: nothing here is a gate.
"""
import collections
import pathlib
import re
import signal
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME = ROOT / "ledger" / "Assets" / "Scripts" / "Game"
EDITOR = ROOT / "ledger" / "Assets" / "Editor"
ROOTS = (GAME, EDITOR)

# EVERY CAP ANNOUNCES ITSELF, one implementation, imported not copied.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from capsay import cap as _cap, NOTHING_MEASURED   # noqa: E402

# UNITY CALLS THESE AND NO SOURCE FILE MENTIONS THEM. Not a suppression list
# for awkward findings — a list of names the engine invokes by convention, which
# is precisely the reflection this tool says it cannot see.
#
# IT IS A DROP, SO IT IS PRINTED. On 26 Aug it removed 13 declarations, every
# one of them `Reset` — thirteen project methods that this tool cannot say
# anything about either way. Counted and named in the summary rather than
# `continue`d in silence.
UNITY = {
    "Awake", "Start", "OnEnable", "OnDisable", "OnDestroy", "Update",
    "LateUpdate", "FixedUpdate", "OnGUI", "OnApplicationQuit",
    "OnApplicationFocus", "OnApplicationPause", "OnDrawGizmos",
    "OnTriggerEnter", "OnTriggerExit", "OnCollisionEnter", "OnCollisionExit",
    "OnRenderImage", "OnPreRender", "OnPostRender", "OnValidate", "Reset",
    "OnBecameVisible", "OnBecameInvisible", "OnAnimatorMove", "OnAnimatorIK",
    "OnControllerColliderHit", "OnMouseDown", "OnGizmosSelected",
}

# CALLED BY NAME FROM OUTSIDE THE CODEBASE ENTIRELY. The Windows workflow runs
# `-executeMethod Ledger.Editor.CiBuild.BuildWindows`, which is reflection from
# a YAML file — the exact blind spot this tool declares in its own docstring.
# Named here rather than dropped silently, and PRINTED, because a cap nobody is
# told about is indistinguishable from a finding. This clause is the model the
# rest of the 26 Aug rewrite copied.
BY_WORKFLOW = {"BuildWindows": "-executeMethod in ledger-build-windows.yml",
               "BuildMac": "-executeMethod in ledger-build-mac.yml"}

DECL = re.compile(
    r"^\s*public\s+(?:static\s+|virtual\s+|override\s+|async\s+|partial\s+|new\s+|"
    r"sealed\s+|unsafe\s+)*[\w<>,\[\]\?\.]+\s+(\w+)\s*\(", re.M)

# EVERY MENTION ANYWHERE, minus the declarations themselves. A method called
# through a local alias, a delegate or an interface still spells its own name
# somewhere, and one that never appears twice is the shape worth reading.
#
# ONE TOKENISED PASS, not one regex per name. `(?<![\w])NAME(?![\w])` and "the
# `\w+` tokens of the corpus" accept exactly the same occurrences — a name
# glued to a digit or an underscore is one token in both readings — so this is
# the same measurement made once instead of 351 times.
WORD = re.compile(r"\w+")


def sources():
    for d in ROOTS:
        if d.exists():
            yield from sorted(d.rglob("*.cs"))


def _rel(p):
    try:
        return str(p.relative_to(ROOT))
    except (ValueError, AttributeError):
        return getattr(p, "name", str(p))     # fail readable, not a traceback


class Reading(object):
    """One sweep, and every number on it is CUMULATIVE over the whole sweep —
    there is no per-file or peak statistic in this tool. THE TALLY AND THE
    ARITHMETIC LIVE HERE, where the selftest runs them."""

    def __init__(self, files, per_root, decls, unity, repeats, first, unreached,
                 excluded):
        self.files = files              # every .cs handed to the scan
        self.per_root = per_root        # root name -> file count, so "94
                                        # Game-layer files" cannot be said again
        self.decls = decls              # name -> declaration count (all of them)
        self.unity = unity              # name -> count, dropped as lifecycle
        self.repeats = repeats          # name -> extra declarations collapsed
        self.first = first              # name -> (file, line) reported for it
        self.unreached = unreached      # [(name, file, line)] the findings
        self.excluded = excluded        # [(name, file, line)] BY_WORKFLOW

    @property
    def matched(self):
        """Every declaration the pattern matched, dropped ones included."""
        return sum(self.decls.values()) + sum(self.unity.values())

    @property
    def distinct(self):
        return len(self.decls)

    @property
    def collapsed(self):
        return sum(self.repeats.values())

    @property
    def measured(self):
        return bool(self.files) and self.matched > 0


def scan(files):
    files = list(files)
    text = {p: p.read_text(encoding="utf-8", errors="replace") for p in files}

    per_root = collections.OrderedDict()
    for d in ROOTS:
        per_root[_rel(d)] = sum(1 for p in files if str(p).startswith(str(d)))
    stray = len(files) - sum(per_root.values())
    if stray:
        per_root["outside the named roots"] = stray

    decls = collections.Counter()
    unity = collections.Counter()
    repeats = collections.Counter()
    first = {}
    for p, s in text.items():
        for m in DECL.finditer(s):
            name = m.group(1)
            if name in UNITY:
                unity[name] += 1
                continue
            decls[name] += 1
            if name in first:
                # FIRST WINS AND IT USED TO WIN SILENTLY — `setdefault`. The
                # later site is never printed, so the count of what it swallowed
                # is the only way a reader knows the list is one site per NAME
                # and not one per method.
                repeats[name] += 1
            else:
                first[name] = (p, s.count("\n", 0, m.start()) + 1)

    mentions = collections.Counter()
    for s in text.values():
        mentions.update(WORD.findall(s))

    unreached, excluded = [], []
    for name in sorted(decls):
        # A NAME IS REACHED IF IT IS SPELLED MORE OFTEN THAN IT IS DECLARED.
        # Declarations of the same name across files all count, so a name
        # declared 14 times needs 15 mentions — which is the blind spot the
        # `repeats` clause exists to print, not to hide.
        if mentions[name] > decls[name] + unity[name]:
            continue
        p, line = first[name]
        (excluded if name in BY_WORKFLOW else unreached).append(
            (name, _rel(p), line))
    return Reading(files, per_root, decls, unity, repeats, first, unreached,
                   excluded)


CAVEAT = ("A name-matcher cannot see reflection, SendMessage or an inspector "
          "binding — read each one before believing it.")


def summary_lines(r, where=""):
    """The reading, as the lines to print. Every count is cumulative over the
    sweep; there is no peak or median here to confuse one for.

    Line 1 says what was FOUND and what was WALKED, because a reader greps
    `lint-unreached:` and sees line 1 and nothing else — and the walked half
    now names its roots rather than calling six Editor files "Game-layer".
    """
    if not r.files:
        return ["lint-unreached: nothing measured — no `.cs` file%s"
                % (" under " + where if where else "")]
    if not r.matched:
        return ["lint-unreached: nothing measured — %d file(s) read and 0 "
                "public method declaration(s) matched in any of them, so "
                "nothing was examined for reach" % len(r.files)]

    head = ("lint-unreached: %d public method name(s) that nothing else in the "
            "layer names (%d distinct name(s) from %d declaration(s) in %d "
            "file(s) walked: %s)"
            % (len(r.unreached), r.distinct, r.matched, len(r.files),
               ", ".join("%d under %s" % (n, w) for w, n in r.per_root.items())))

    unity_names = ["%s x%d" % (n, c) for n, c in sorted(r.unity.items())]
    # `decls[n]` IS ALREADY EVERY DECLARATION OF THAT NAME — `repeats[n]` is
    # `decls[n] - 1`, so adding them prints each site nearly twice. Caught by
    # the twin fixture below (it said `SynthTwin x3` for two declarations)
    # before this tool was ever run for a report.
    repeat_names = ["%s x%d" % (n, r.decls[n])
                    for n, c in sorted(r.repeats.items(), key=lambda kv: -kv[1])]
    drops = [
        "%d declaration(s) of %d name(s) are Unity lifecycle callbacks the "
        "engine invokes with no reference anywhere [%s]"
        % (sum(r.unity.values()), len(r.unity),
           _cap(unity_names, keep=4, sep=", ", width=24, tail="none")),
        "%d declaration(s) of %d name(s) repeat a name already declared — this "
        "tool asks about NAMES, so a repeat whose twin IS called reads as "
        "reached and no site of it is ever reported [%s]"
        % (r.collapsed, len(r.repeats),
           _cap(repeat_names, keep=4, sep=", ", width=24, tail="none")),
    ]

    lines = [head,
             "  not examined, by reason: " + "; ".join(drops),
             "  arithmetic: %d distinct + %d Unity lifecycle + %d repeat = %d "
             "declaration(s) matched in %d file(s) walked"
             % (r.distinct, sum(r.unity.values()), r.collapsed, r.matched,
                len(r.files))]
    if r.excluded:
        lines.append("  not counted as a finding: %d name(s) reached from "
                     "outside the codebase — %s"
                     % (len(r.excluded),
                        _cap(["%s at %s:%d (%s)" % (n, f, l, BY_WORKFLOW[n])
                              for n, f, l in r.excluded],
                             keep=4, sep="; ", width=120)))
    lines.append("  " + CAVEAT)
    return lines


def finding_lines(r):
    """One line per finding, and the MULTIPLICITY beside it — a name declared
    more than once is reported at its first site only, which is a cap and
    therefore says so."""
    out = []
    for name, rel, line in r.unreached:
        n = r.decls[name]
        more = ("" if n == 1 else
                "   (declared %dx; first site shown, +%d more not shown)"
                % (n, n - 1))
        out.append("  %s:%d: %s%s" % (rel, line, name, more))
    return out


# --------------------------------------------------------------------- selftest

class _Fake(object):
    """A fixture file. SYNTHETIC BY CONSTRUCTION — in memory, never on disk,
    `Synth*` names that exist nowhere in the project, so no rejecting case is
    pinned to a real file and doing the work this tool prompts (wiring a
    method up) can never break the tool."""

    def __init__(self, name, text):
        self.name = name
        self._t = text

    def __str__(self):
        return self.name

    def read_text(self, encoding=None, errors=None):
        return self._t


CALLER = _Fake("SynthCaller.cs", """
namespace Synth.Fixture
{
    public class SynthCaller
    {
        public void Run()
        {
            SynthUsed();
            var t = new SynthThing();
            t.SynthAlsoUsed(1);
        }
    }
}
""")

DECLARER = _Fake("SynthThing.cs", """
namespace Synth.Fixture
{
    public class SynthThing
    {
        public void SynthUsed() { }
        public int SynthAlsoUsed(int a) { return a; }
        public void SynthOrphan() { }
        public void Reset() { }
    }
}
""")

TWIN_A = _Fake("SynthTwinA.cs", """
namespace Synth.Fixture
{
    public class SynthTwinA
    {
        public void SynthTwin() { }
    }
}
""")

TWIN_B = _Fake("SynthTwinB.cs", """
namespace Synth.Fixture
{
    public class SynthTwinB
    {
        public void SynthTwin() { }
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

    print("lint-unreached --selftest — ACCEPTING CASES FIRST (rule 5b: the")
    print("expensive failure is a validator nothing survives)\n")

    # ================= ACCEPTING: THE LIVE TREE =================
    print("ACCEPTING — the live repository")
    live = scan(sources())
    lines = summary_lines(live, ", ".join(_rel(d) for d in ROOTS))
    check(live.measured and live.matched > 0 and live.distinct > 0,
          "the live sweep EXAMINED something — a reading over nothing is the "
          "silence rule 3b exists for",
          "%d declaration(s), %d distinct name(s), %d file(s)"
          % (live.matched, live.distinct, len(live.files)))
    check(live.distinct + sum(live.unity.values()) + live.collapsed
          == live.matched,
          "the printed arithmetic IS an identity — distinct + Unity + repeat = "
          "declarations matched",
          "%d+%d+%d=%d" % (live.distinct, sum(live.unity.values()),
                           live.collapsed, live.matched))
    check(sum(live.per_root.values()) == len(live.files)
          and len(live.per_root) > 1,
          "and the walked count is broken down PER ROOT — six Editor files "
          "were being called Game-layer",
          ", ".join("%s=%d" % kv for kv in live.per_root.items()))
    check(all(n not in live.decls for n in UNITY & set(live.unity)),
          "a dropped lifecycle name is not also counted as examined",
          "dropped: %s" % sorted(live.unity))
    check(len(live.unreached) <= live.distinct
          and all(n not in BY_WORKFLOW for n, _, _ in live.unreached),
          "and the workflow-reached names are excluded from the findings and "
          "listed separately",
          "%d finding(s), %d excluded" % (len(live.unreached),
                                          len(live.excluded)))

    # ================= ACCEPTING: SYNTHETIC =================
    print("\nACCEPTING — synthetic code where everything is called")
    good = scan([CALLER, DECLARER])
    names = [n for n, _, _ in good.unreached]
    check("SynthUsed" not in names and "SynthAlsoUsed" not in names,
          "a method called from another file is NOT reported, and neither is "
          "one called through a reference",
          "findings: %s" % names)
    check(good.unity.get("Reset") == 1 and "Reset" not in good.decls,
          "a Unity lifecycle name is dropped, COUNTED and named rather than "
          "`continue`d in silence",
          "unity=%s" % dict(good.unity))

    # ================= NOTHING MEASURED =================
    print("\nNOTHING MEASURED — the case that must not read as clean")
    empty = "\n".join(summary_lines(scan([]), "/nowhere"))
    check("nothing measured" in empty and "0 public method name(s)" not in empty,
          "an empty sweep prints the WORDS, not a line of zeros that reads as "
          "a clean layer",
          empty)
    blank = "\n".join(summary_lines(scan([_Fake("SynthBlank.cs", "// nothing\n")])))
    check("nothing measured" in blank and "1 file(s) read" in blank,
          "a sweep that read files and matched no declaration says so WITH its "
          "denominator",
          blank)

    # ================= REJECTING — the fault this tool exists for ============
    print("\nREJECTING — a public method nothing names")
    check(any(n == "SynthOrphan" for n, _, _ in good.unreached),
          "a public method mentioned nowhere but its own declaration IS "
          "reported — the `RecordKilling` shape",
          "findings: %s" % [n for n, _, _ in good.unreached])

    twins = scan([TWIN_A, TWIN_B])
    twin_summary = "\n".join(summary_lines(twins) + finding_lines(twins))
    check(twins.collapsed == 1 and "SynthTwin x2" in twin_summary,
          "two declarations of one name are COLLAPSED — and the collapse is "
          "printed with its size, because it is this tool's blind spot",
          [l for l in twin_summary.splitlines() if "repeat" in l][0][:150])
    check("declared 2x; first site shown, +1 more not shown" in twin_summary,
          "and the finding line announces the cap rather than showing one site "
          "as though it were the only one",
          [l for l in twin_summary.splitlines() if "SynthTwin" in l][-1])

    ok = not fails
    print("\nlint-unreached --selftest: %s — %d checks, %d failed"
          % ("PASS" if ok else "FAILED", len(ran), len(fails)))
    print("  denominators: live %d declaration(s) over %d file(s) (%s), %d "
          "distinct name(s), %d finding(s); synthetic %d fixture file(s), 0 "
          "written to disk, 0 project file(s) modified"
          % (live.matched, len(live.files),
             ", ".join("%s=%d" % kv for kv in live.per_root.items()),
             live.distinct, len(live.unreached), 5))
    return 0 if ok else 1


def main():
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # `| head` must not traceback
    except (AttributeError, ValueError):
        pass
    # DISPATCHED FIRST AND RETURNED FROM: `lint-shadow`'s `--selftest` fell
    # through to the live sweep and exited 0, so a guard that had never run
    # looked exactly like one that passed.
    if "--selftest" in sys.argv or "--self-test" in sys.argv:
        return selftest()

    r = scan(sources())
    for line in summary_lines(r, ", ".join(_rel(d) for d in ROOTS)):
        print(line)
    if not r.measured:
        return 2
    print()
    for line in finding_lines(r):
        print(line)
    # EXIT 0 WHATEVER IT FINDS. This is a reading, not a gate: the commit that
    # WIRES one of these would be blocked by a check that failed on the list.
    # Exit 2 above is the other half — "could not look" is not "found nothing".
    return 0


if __name__ == "__main__":
    sys.exit(main())
