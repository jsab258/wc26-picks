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

So: a type declared inside a conditional block must be NAMED IN CODE somewhere
other than its own file. That is a weak claim — naming is not calling — but it
is exactly the distance between "this exists" and "this is reachable", and it
is the distance that was missing. Anything stronger needs a compiler with the
symbol defined, which `ledger/BackendCheck` does for compilation and cannot do
for reachability.

IN CODE, not in prose. The naming search strips comments and plain strings
(`lint-shadow.strip_comments`, imported rather than re-written) because a
paragraph explaining why `OnnxSpeech` is called `OnnxSpeech` is not a caller,
and this whole file exists because a type that only EXISTED read as a type
that RAN. Measured before the rule was tightened: `Audio.cs` mentions the name
three times, one of them a doc comment, two of them code — so today's
repository passes either way and the tighter rule costs nothing here.

WHY THE REJECTING FIXTURE IS SYNTHETIC (25 Aug, third site of a fixed fault).
This selftest used to build its rejecting case by OVERWRITING `Game/Audio.cs`
on disk — mutate, measure, restore in a `finally`. Two faults in one:

  * A `finally` does not run on SIGTERM, SIGKILL, an OOM kill or a container
    reclaim, and this container has rolled its own checkout back three times
    in one day. Any of those leaves a CORRUPTED TRACKED SOURCE FILE in the
    working tree, with every `OnnxSpeech` in it renamed. `ledger/breakrun.py`
    is the mature version of that manoeuvre — on-disk `.breakbak`, atexit AND
    signal handlers, the backup gitignored — and this file had none of it.
  * A fixture pinned to a real project file goes red WHEN THE PROJECT
    IMPROVES. `Joe.fbx` and `police.fbx` were unpinned for exactly this
    (`game-design/agent-reports/fixture-unpinning.md`); `ref-bench` paid for
    it first. Rewire `Audio` and the rejecting case reads "the tool broke".

The fixture is now three synthetic `.cs` files written to a TEMP DIRECTORY,
naming types that exist nowhere in this project. Nothing under `ledger/` is
read for it and nothing under `ledger/` is written at any point in any run —
enforced, not asserted: `arm_write_sentry()` installs a `sys.addaudithook`
that REFUSES any write, mkdir, rename or unlink whose path lands under
`ledger/`, and the selftest probes that sentry in both directions.

EXIT CODES
    0   walked, nothing unreachable   (selftest: both cases as expected)
    1   at least one unreachable type (selftest: a check failed)
    2   NOTHING MEASURED — no files to walk, or the shared stripper is gone
    3   a write under `ledger/` was attempted and refused
"""
import argparse
import atexit
import os
import pathlib
import re
import shutil
import signal
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
GAME = ROOT / "ledger" / "Assets" / "Scripts" / "Game"
# Walked for DECLARATIONS only. Neither holds a `#if` today (measured: 0 of
# 101 files), and both are printed as a denominator by `audit` so the day one
# appears is a line rather than a silence.
UNWALKED = (ROOT / "ledger" / "Assets" / "Scripts" / "Core",
            ROOT / "ledger" / "Assets" / "Editor")
LEDGER = ROOT / "ledger"

SHOW = 3            # per-line cap on named-by files; announces itself below


# ---------------------------------------------------------------- write sentry

class LedgerWriteRefused(RuntimeError):
    """A tool in `tools/` tried to write under `ledger/`. It does not get to."""


# COUNTS, so the sentry's own zero has a denominator: "0 under ledger/" beside
# "N write(s) seen" distinguishes a sentry that refused nothing from a sentry
# that saw nothing because it was armed too late or watching the wrong event.
_sentry = {"armed": False, "writes": 0, "refused": 0, "last": ""}

_WRITE_EVENTS = ("os.mkdir", "os.rmdir", "os.remove", "os.rename", "os.replace",
                 "os.truncate", "os.link", "os.symlink", "os.chmod", "os.utime",
                 "shutil.copyfile", "shutil.copymode", "shutil.copystat",
                 "shutil.move", "shutil.unpack_archive")


def _under_ledger(path):
    """ONE implementation of 'is this path inside the guarded region', used by
    the hook and by the selftest's coverage check — a second copy is the site
    nobody fixes when the first one learns something."""
    try:
        full = os.path.abspath(os.fsdecode(os.fspath(path)))
    except (TypeError, ValueError):
        return None
    ledger = str(LEDGER.resolve())
    return full == ledger or full.startswith(ledger + os.sep)


def _opens_for_write(mode, flags):
    if mode:
        return any(c in mode for c in "wax+")
    try:
        f = int(flags)
    except (TypeError, ValueError):
        return False
    return bool(f & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))


def arm_write_sentry():
    """Refuse, at the interpreter, any write whose path lands under `ledger/`.

    An audit hook fires BEFORE the operation, so raising here means the write
    never happens — the rejecting probe in the selftest cannot leave a file
    behind even when it is the sentry itself being tested.

    WHAT IT DOES NOT COVER, said out loud because a guard whose scope is
    guessed at is a guard read as covering more than it does: in-process
    writes only. A subprocess would be invisible to it; this tool spawns
    none, and `audit()` opens files for reading only.
    """
    if _sentry["armed"]:
        return

    def hook(event, args):
        if event == "open":
            path, mode, flags = args
            if not _opens_for_write(mode, flags):
                return
            paths = (path,)
        elif event in _WRITE_EVENTS:
            paths = args
        else:
            return
        _sentry["writes"] += 1
        for p in paths:
            if not isinstance(p, (str, bytes, os.PathLike)):
                continue            # a file descriptor, or an int mode
            if _under_ledger(p):
                _sentry["refused"] += 1
                _sentry["last"] = os.path.abspath(os.fsdecode(os.fspath(p)))
                raise LedgerWriteRefused(
                    "%s under ledger/ refused: %s — this tool writes its "
                    "fixtures to a temp directory" % (event, _sentry["last"]))

    sys.addaudithook(hook)
    _sentry["armed"] = True


def sentry_line(note=""):
    """Both numbers are CUMULATIVE over the whole process, read at the moment
    this is called — so the footer's count includes the selftest's own probe
    and the mid-run one does not. Same counter, two moments, and the note is
    what stops a reader taking the second for the first."""
    return ("write sentry: %s write event(s) seen so far, %s refused under "
            "ledger/%s%s"
            % (_sentry["writes"], _sentry["refused"],
               " (last: %s)" % _sentry["last"] if _sentry["last"] else "",
               " — " + note if note else ""))


# ---------------------------------------------------------------------- parsing

_strip = None


def strip_comments(text):
    """ONE IMPLEMENTATION PER IDEA. `tools/lint-shadow.py` already owns this
    parser — comments out, plain strings out, `$"..."` interpolation contents
    KEPT because those are code — and it is imported rather than copied. A
    second stripper is the site nobody fixes when the first one learns
    something, which is how `lint-shadow` spent months throwing away the
    largest concentration of Game-layer static reads in the project."""
    global _strip
    if _strip is None:
        import importlib.util
        src = ROOT / "tools" / "lint-shadow.py"
        if not src.is_file():
            raise FileNotFoundError(src)
        spec = importlib.util.spec_from_file_location("lint_shadow", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _strip = mod.strip_comments
    return _strip(text)


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

    Both exclusions — nested, and declared outside any `#if` — are pinned by
    rung 1 of the synthetic ladder, which declares one of each and asserts the
    examined set is exactly `[SynthBackend]`.
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


def _capped(names):
    """A CAP THAT SAYS WHEN IT BIT. A `| head -3` that outgrew its input once
    read as 'three of five systems failed' when nothing was broken."""
    shown = ", ".join(names[:SHOW])
    extra = len(names) - SHOW
    return shown + (" (+%d more not shown)" % extra if extra > 0 else "")


class Audit(object):
    """The reading. `bad` is the finding, the rest is its denominator.

    Every field is a WHOLE-WALK total, not a peak or a sample: `types` is the
    complete list of conditional types examined this run, `files` the complete
    set walked. Nothing here is a maximum, so nothing here needs an at-worst
    partner.
    """

    def __init__(self, bad, types, files, outside_types, outside_files):
        self.bad = bad                      # unreachable-type sentences
        self.types = types                  # [(typename, filename)] examined
        self.files = files                  # count of .cs walked
        self.outside_types = outside_types  # conditional types NOT walked
        self.outside_files = outside_files  # files they were looked for in


def audit(say, root=None):
    """Walk `root` (default: the Game layer) and report unreachable types."""
    # ARMED HERE, not only in main(). FOUND BY RUNNING IT: the sentry used to
    # be armed in main() alone, so importing this module and calling selftest()
    # directly — which is how it was driven under a kill harness — left the
    # guarantee switched off while every line of output still claimed it. The
    # safety property has to travel with the function that needs it, not with
    # the CLI entry point. Idempotent, so repeated calls install one hook.
    arm_write_sentry()
    root = GAME if root is None else root
    live = root == GAME
    bad = []
    files = sorted(root.rglob("*.cs"))
    # rglob, not glob: the Game folder has no subdirectory today, so the two
    # walks return the same set — and a check whose walk stops at the first new
    # folder is a silence waiting to happen. No count is written here on
    # purpose: the file total moves under this tool (a builder added one
    # between two runs of it this afternoon), so the denominator belongs on the
    # summary line where it is measured, not in a comment that decays.
    texts = {f: f.read_text(encoding="utf-8", errors="replace") for f in files}
    code = {f: strip_comments(t) for f, t in texts.items()}
    examined = []

    for f in files:
        for t in conditional_types(texts[f]):
            examined.append((t, f.name))
            word = re.compile(r"\b%s\b" % re.escape(t))
            in_code = [g for g in files if g != f and word.search(code[g])]
            in_prose = [g for g in files
                        if g != f and g not in in_code and word.search(texts[g])]
            if in_code:
                say("  ok    %s (%s) is named in code by %d of %d other file(s): %s"
                    % (t, f.name, len(in_code), len(files) - 1,
                       _capped([g.name for g in in_code])))
            elif in_prose:
                # A DIFFERENT DIAGNOSIS FROM 'nothing names it', and it needs
                # to read differently: the name is in the repository, in prose,
                # which is the exact state that makes an absent caller look
                # present to a human grepping for it.
                bad.append("%s in %s is behind #if and is named ONLY in comments "
                           "or plain strings (%s) — prose is not a caller"
                           % (t, f.name, _capped([g.name for g in in_prose])))
                say("  FAIL  " + bad[-1])
            else:
                bad.append("%s in %s is behind #if and nothing else names it — "
                           "it can never run" % (t, f.name))
                say("  FAIL  " + bad[-1])

    # THE DENOMINATOR OF THE DENOMINATOR. `1 type(s) checked` is a true and
    # very small number, and the reason it is small is a property of the
    # codebase (one type behind one `#if`), not of the walk. These two counts
    # say so: if a conditional type ever appears in Core or Editor — which
    # this walk does not cover, because a Core type is named from Game by
    # design and the claim would not hold there — it stops being invisible.
    out_types, out_files = [], 0
    if live:
        for d in UNWALKED:
            if not d.is_dir():
                continue
            for f in sorted(d.rglob("*.cs")):
                out_files += 1
                out_types += ["%s(%s)" % (t, f.name)
                              for t in conditional_types(
                                  f.read_text(encoding="utf-8", errors="replace"))]

    if not files:
        # NOT '0 unreachable'. A walk with nothing in it must not print the
        # same sentence as a clean walk, and must not match the shape
        # `verify.py` reads as a pass.
        say("lint-conditional-reach: nothing measured — no .cs file under %s"
            % root)
    else:
        tail = ""
        if live:
            tail = ("; %d conditional type(s) in %d unwalked Core/Editor file(s)%s"
                    % (len(out_types), out_files,
                       ": " + _capped(out_types) if out_types else ""))
        say("lint-conditional-reach: %d unreachable, %d conditional type(s) "
            "checked in %d file(s) under %s%s"
            % (len(bad), len(examined), len(files), root.name, tail))
    return Audit(bad, examined, len(files), out_types, out_files)


# ------------------------------------------------------------------- fixtures

FIXTURE_HEADER = ("// SYNTHETIC FIXTURE, written by tools/lint-conditional-reach.py\n"
                  "// --selftest into a temp directory. Not a project file: no name\n"
                  "// in it exists anywhere in this repository, so doing the work\n"
                  "// this tool prompts can never break the tool.\n")

BACKEND = FIXTURE_HEADER + """#if SYNTH_FIXTURE_SYMBOL
using System;

namespace Synth.Fixture
{
    /// Behind the switch, exactly like OnnxSpeech. This is the subject.
    public class SynthBackend
    {
        public static SynthBackend Open()
        {
            return new SynthBackend();
        }

        /// NESTED, and named nowhere else on purpose — the Gauss case. Its
        /// reachability is its parent's, so it must not be examined at all.
        struct SynthNoise
        {
            public float Level;
        }
    }
}
#endif
"""

HOST = FIXTURE_HEADER + """using System;

namespace Synth.Fixture
{
    /// TOP-LEVEL AND UNCONDITIONAL, and named nowhere else on purpose. If the
    /// `#if` test broke open, this is what would start being flagged.
    public class SynthHost
    {
        public void Wire()
        {
%s
        }
    }
}
"""

# ONE CONTRIBUTOR TOGGLED PER RUNG, and it is the reference: code, prose, or
# nothing. Everything else about the fixture is identical between rungs, so a
# difference between rungs is the reference and nothing else.
RUNGS = {
    "code":    "            var backend = SynthBackend.Open();",
    "comment": "            // SynthBackend.Open() is what would go here.",
    "none":    "            return;",
}


def build_fixture(where, reference):
    where.mkdir(parents=True, exist_ok=True)
    (where / "SynthBackend.cs").write_text(BACKEND, encoding="utf-8")
    (where / "SynthHost.cs").write_text(HOST % RUNGS[reference], encoding="utf-8")
    return where


# ------------------------------------------------------------------- selftest

def selftest():
    arm_write_sentry()          # see audit(); do not rely on main() for this
    fails, ran = [], []

    def check(ok, what, got=""):
        print(("  ok    " if ok else "  FAIL  ") + what + ("   [%s]" % got if got else ""))
        ran.append(what)
        if not ok:
            fails.append(what)

    # ================= ACCEPTING CASES FIRST =================
    # The expensive failure for a checker is not missing a fault, it is
    # rejecting everything, being switched off, and taking its reason for
    # existing with it. So the first thing asserted is that good input passes.

    print("ACCEPTING — the live codebase, which is the best fixture available")
    quiet = []
    live = audit(quiet.append)
    check(not live.bad,
          "today's Game layer passes",
          "%d unreachable of %d examined over %d file(s)"
          % (len(live.bad), len(live.types), live.files)
          + ("; " + "; ".join(live.bad[:2]) if live.bad else ""))
    check(live.files > 0 and len(live.types) > 0,
          "and it examined something — a zero here is the silence this check exists to break",
          "%d conditional type(s) [%s] in %d file(s)"
          % (len(live.types), _capped(["%s(%s)" % t for t in live.types]) or "nothing measured",
             live.files))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="cond-reach-fixture-"))
    atexit.register(shutil.rmtree, tmp, True)
    print("\nSYNTHETIC LADDER (built here, in %s — no project file is read or written)" % tmp)

    r1 = audit(lambda _s: None, build_fixture(tmp / "rung1-code", "code"))
    check(not r1.bad,
          "rung 1 ACCEPTING — a conditional type named in CODE elsewhere passes",
          "%d unreachable of %d examined over %d file(s)"
          % (len(r1.bad), len(r1.types), r1.files))
    check([t for t, _ in r1.types] == ["SynthBackend"],
          "rung 1 — and the nested SynthNoise and the unconditional SynthHost are "
          "not examined at all (the Gauss rule, and the #if rule)",
          "examined %s of 3 type(s) declared"
          % (_capped(["%s(%s)" % t for t in r1.types]) or "nothing measured"))

    # ================= REJECTING CASES =================
    print("\nREJECTING — the same fixture with one contributor toggled")

    r2 = audit(lambda _s: None, build_fixture(tmp / "rung2-none", "none"))
    check(len(r2.bad) == 1 and "SynthBackend" in r2.bad[0] and "nothing else names it" in r2.bad[0],
          "rung 2 REJECTING — with the reference deleted, SynthBackend is reported "
          "unreachable (the state OnnxSpeech shipped in)",
          "%d unreachable of %d examined: %s"
          % (len(r2.bad), len(r2.types), (r2.bad[0][:90] if r2.bad else "nothing flagged")))

    r3 = audit(lambda _s: None, build_fixture(tmp / "rung3-comment", "comment"))
    check(len(r3.bad) == 1 and "ONLY in comments" in r3.bad[0],
          "rung 3 REJECTING — a mention in a COMMENT is not reach, and says so "
          "differently from 'nothing names it'",
          "%d unreachable of %d examined: %s"
          % (len(r3.bad), len(r3.types), (r3.bad[0][:90] if r3.bad else "nothing flagged")))

    # THE RUNGS MUST STAND APART. Both expectations above are literals rather
    # than values derived from the fixture, so they cannot drift together the
    # way prop-dimensions' did — but a fixture that stopped declaring a
    # conditional type at all would make rung 1 pass over an empty walk, and
    # this is the line that says so.
    check([len(r1.bad), len(r2.bad), len(r3.bad)] == [0, 1, 1]
          and len(r1.types) == len(r2.types) == len(r3.types) == 1,
          "the ladder separates — one type examined at every rung, unreachable "
          "0/1/1 across code/none/comment",
          "examined %d/%d/%d, unreachable %d/%d/%d"
          % (len(r1.types), len(r2.types), len(r3.types),
             len(r1.bad), len(r2.bad), len(r3.bad)))

    # ================= THE SENTRY, BOTH WAYS =================
    # It is a guard, so it gets rule 5b too. Accepting: the fixture writes
    # above all went through it. Rejecting: an attempted write under ledger/
    # must be refused — and because an audit hook fires BEFORE the operation,
    # a working sentry cannot leave the probe file behind.
    print("\nWRITE SENTRY — the proof that nothing under ledger/ is touched")
    check(_sentry["armed"] and _sentry["writes"] > 0 and _sentry["refused"] == 0,
          "ACCEPTING — the fixture's own writes went through it untouched",
          sentry_line())

    probe = LEDGER / ".conditional-reach-write-probe.tmp"
    refused = False
    try:
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write("this must never be written\n")
    except LedgerWriteRefused:
        refused = True
    except OSError as exc:                      # not the outcome under test
        refused = False
        print("  ..    probe raised %s rather than being refused" % exc.__class__.__name__)
    left = probe.exists()
    if left:                                    # only reachable if the sentry failed
        os.remove(probe)
    check(refused and not left,
          "REJECTING — a write to a path under ledger/ is refused, and no file is left",
          "refused=%s fileLeftBehind=%s path=%s" % (refused, left, probe.name))
    # AND THE HISTORICAL TARGET IS INSIDE THE GUARDED REGION. The probe above
    # proves the sentry refuses writes under ledger/; this says the file this
    # selftest used to overwrite is one of them. Asked as a path question, not
    # by opening the file — a probe that truncates Audio.cs to prove Audio.cs
    # cannot be truncated is the fault, performed.
    check(_under_ledger(GAME / "Audio.cs") is True,
          "and Game/Audio.cs — the file this selftest used to overwrite — is "
          "inside that guarded region",
          str(GAME / "Audio.cs"))

    ok = not fails
    print("\nlint-conditional-reach --selftest: %s — %d checks, %d failed"
          % ("PASS" if ok else "FAILED", len(ran), len(fails)))
    print("  denominators: live %d conditional type(s) over %d Game file(s); "
          "synthetic 3 rung(s) x 2 file(s) in a temp dir, 0 project file(s) touched"
          % (len(live.types), live.files))
    # The note is CONDITIONAL: printed under a sentry that refused nothing it
    # would explain away a zero as a probe that never fired, which is the
    # break-E state and the one thing this line must not smooth over.
    print("  " + sentry_line(
        "that refusal is this selftest's own probe; a real run refusing "
        "anything exits 3" if _sentry["refused"] else
        "NO PROBE WAS REFUSED — the sentry saw nothing, which is not the same "
        "as nothing having been written"))
    return 0 if ok else 1


def main():
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # `| head` must not traceback
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    arm_write_sentry()
    try:
        if a.selftest:
            return selftest()
        r = audit(print)
        if not r.files:
            return 2
        return 1 if r.bad else 0
    except LedgerWriteRefused as exc:
        print("lint-conditional-reach: REFUSED — %s" % exc)
        return 3
    except FileNotFoundError as exc:
        print("lint-conditional-reach: nothing measured — the shared comment "
              "stripper is missing (%s)" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
