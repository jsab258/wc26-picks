#!/usr/bin/env python3
"""WHERE THE SIM GOT TO WHEN IT PRODUCED NO DONE LINE — position first, tails last.

    python3 tools/hang-report.py --log sim-run/player.log \
        --exit sim-run/sim-exit.txt --crumbs sim-run/sim-out/stall.txt
    python3 tools/hang-report.py --selftest

WHY THIS EXISTS.

`e8c5949` carried the first visible change in days and came back with no done
line. The instrument that fired told us this much:

    hangTail=[...]  hangTailLines=111  hangTailOwn=19  hangSimLines=4

Nineteen structural lines, of which the four the sim wrote itself were
`simulating 11 day(s)`, the companion line, `staged deed #1` and two witness
accounts — all from the START of an eleven-day run. Then engine warnings and
silence. A tail answers "what was printed last"; the question is "where did it
stop", and those are different questions. A tail of a log is not a position in
a run. 7 of 352 kept runs are in this class, so it is a recurring shape.

WHAT THIS PRINTS AND IN WHAT ORDER, because the order is the fix:

  1. THE OUTCOME, ON EVERY RUN.  `simExit=`/`simTimedOut=`/`simWaitSeconds=`
     come from a file the sim step writes. That step has always KNOWN whether
     it killed the sim or the sim exited and it threw the answer away, so
     "killed at 24 minutes" and "crashed with an exit code" arrived looking
     identical — a force kill writes nothing to player.log either way.
     `simWaitSeconds` is also the first wall-clock total this project has ever
     printed for a sim run, which is the series the in-sim watchdog's bound
     needs before it can be anything but provisional.
  2. THE CLASSIFICATION, when there is no done line. One bracketed sentence.
  3. THE POSITION, finest source first: the stall breadcrumb
     (`SimDirector.Phase`, half-second resolution, a FILE that survives the
     force kill), then `dayMark` (once per in-game noon, in player.log).
  4. THE TAILS, unchanged in shape and demoted to last, each with a count of
     what it showed out of what there was.

WHAT IT REFUSES TO DO.

A run that reached no breadcrumb prints the WORDS `no heartbeat — the sim did
not reach the first one`, never a zero and never an empty value: "died before
the first beat" and "the heartbeat is not wired" are different facts and a
`hangPhase=` with nothing after it makes them identical. Same for a missing
exit record, and same for a breadcrumb file whose lines this reader cannot
parse — which is the emitter-drift case, and it is called out by name rather
than reported as absence, because the emitter lives in the Game layer and
`gamecheck` can prove it COMPILES but nothing here can prove what it PRINTS.

EXIT CODES, distinct per outcome:
    0   a done line is present — nothing to diagnose (the accepting case)
    10  no done line, and a position was found
    11  no done line and NO position at all
    2   the log itself could not be read
    3   --selftest failed

ONE IMPLEMENTATION PER IDEA. The three tails used to be three greps inside
`tools/sim-shots-commit.sh`, which runs on the Windows runner and is
untestable from here. They are here now, with the same filters and the same
key names, so nothing that reads a verdict has to change and the logic has a
selftest. Do not re-add them to the shell.
"""
import argparse
import os
import re
import signal
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The words that must appear when a source produced nothing. Named constants
# because the selftest asserts on them and a message this tool words one way
# and its test another is a test of nothing.
NO_CRUMB = "no heartbeat — the sim did not reach the first one"
NO_DAYMARK = "no dayMark — the sim never reached an in-game noon"
NO_EXIT = "no record — the sim step did not report, so it may not have run"

# OUR LINES ARE SHAPED `TypeName: ...` — every one comes from a Debug.Log in a
# class that prefixes itself. Unity's do not: the IK warning starts with a verb
# and the format one with a quote. Structural rather than a list of engine
# strings to keep up to date, because an allow-list silently discards
# everything nobody thought of.
OWN_LINE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*: ")
DONE_LINE = "SimDirector: done."

# The breadcrumb, as `SimDirector.Phase` writes it. Parsed structurally — every
# `key=value` after the start of the line — rather than by a fixed field order,
# so adding a field to the emitter cannot silently stop this matching. What it
# DOES require is named in CRUMB_REQUIRED, and a file of lines missing those is
# reported as drift rather than as absence.
CRUMB_REQUIRED = ("at", "phase", "pass", "frames", "day", "crumb")
KV = re.compile(r"([A-Za-z][A-Za-z0-9_]*)=(\S+)")
DAYMARK = re.compile(r"SimDirector: dayMark day=(\d+) at=([0-9.]+)s frames=(\d+)")


def emitter_fields(text):
    """The keys the breadcrumb emit block actually writes, or None if there is
    no emit block at all.

    A CHECK ON `"pass=" in source` WOULD PASS ON A FILE WITH NO EMITTER IN IT —
    `pass=` appears on the done line, `day=` in `dayMark`, `at=` in both. That
    is the allow-list fault in a different costume: a test that cannot fail is
    a test of nothing. So this reads the interpolated string handed to
    `AppendAllText(CrumbFile, ...)` and nothing else.
    """
    i = text.find("AppendAllText(CrumbFile,")
    if i < 0:
        return None
    block = text[i:i + 400]
    end = block.find(");")
    if end >= 0:
        block = block[:end]
    return set(re.findall(r"([A-Za-z][A-Za-z0-9_]*)=\{", block))


def _quiet_pipe():
    """A correct report that ends in a BrokenPipeError traceback costs twenty
    minutes before anybody notices it worked."""
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass


def read_lines(path):
    """Every line, or None when the file is not there — which is a different
    fact from a file with nothing in it and is kept different all the way out."""
    if not path:
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read().replace("\r", "").split("\n")
    except OSError:
        return None


# ── the exit record ──────────────────────────────────────────────────────────

def exit_facts(lines):
    """The sim step's own account of how the process ended.

    Returns a dict of the keys it wrote, or {} when there is no record. The
    step writes them; this only reads, so a key it does not know about rides
    through rather than being dropped.
    """
    if lines is None:
        return {}
    facts = {}
    for line in lines:
        m = re.fullmatch(r"\s*([A-Za-z][A-Za-z0-9_]*)=(\S*)\s*", line)
        if m and m.group(2):
            facts[m.group(1)] = m.group(2)
    return facts


def outcome_line(facts):
    """ONE LINE, because these four are one moment — the instant the wait ended.

    Split across lines a reader greping for two of them silently gets two
    moments as one, which is the afternoon `verdict-read.py` exists for.
    """
    if not facts:
        return "simExit=[%s]" % NO_EXIT
    order = ["simTimedOut", "simExit", "simWaitSeconds", "simWaitLimit"]
    parts = [f"{k}={facts[k]}" for k in order if k in facts]
    parts += [f"{k}={v}" for k, v in sorted(facts.items()) if k not in order]
    return " ".join(parts)


# ── the breadcrumb ───────────────────────────────────────────────────────────

def parse_crumbs(lines):
    """Every parseable breadcrumb, with the count of lines it had to look at.

    Returns (crumbs, lines_read, first_unparsed). `lines_read` is the
    denominator: 0 crumbs out of 1 line (the header alone) and 0 out of 57 are
    completely different runs and read identically without it.
    """
    if lines is None:
        return [], 0, None
    crumbs, read, bad = [], 0, None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        read += 1
        kv = dict(KV.findall(line))
        if all(k in kv for k in CRUMB_REQUIRED):
            crumbs.append(kv)
        elif bad is None:
            bad = line
    return crumbs, read, bad


def crumb_block(crumbs, read, bad, present, waited):
    """The position, and every number named for what it is a statistic of."""
    out = []
    if not present:
        # ABSENT IS NOT EMPTY. No file at all means the sim never reached
        # `Begin`, which truncates it — a fact worth its own sentence.
        out.append("hangCrumbFile=[absent — the sim never reached SimDirector.Begin, "
                   "which creates it]")
        return out, False
    out.append(f"hangCrumbs={len(crumbs)}/{read}")
    if bad is not None and not crumbs:
        out.append("hangCrumbDrift=[%d line(s) present, none parsed — the emitter and "
                   "this reader disagree; %s expected]" % (read, "/".join(CRUMB_REQUIRED)))
        out.append("hangCrumbBad| " + bad[:200])
        return out, False
    if not crumbs:
        out.append(f"hangCrumb=[{NO_CRUMB}]")
        return out, False

    last = crumbs[-1]
    at = float(last["at"])
    out.append("hangPhase=" + last["phase"])          # last-wins: the stage ENTERED
    out.append("hangPass=" + last["pass"])            # cumulative: Update passes done
    out.append("hangFrames=" + last["frames"])        # cumulative: engine frames
    out.append("hangDay=" + last["day"])              # in-game day / the day it stops at
    if "hr" in last:
        out.append("hangHour=" + last["hr"])
    out.append(f"hangAt={at:.1f}s")                   # last-wins: wall clock at that crumb
    if waited is not None:
        # THE WEDGE, AS ONE ENTRY CARRYING BOTH MOMENTS. Silence from the last
        # breadcrumb to the end of the wait: large means it stopped dead, small
        # means it was still moving when the runner shot it.
        out.append(f"hangSilent={max(0.0, waited - at):.1f}s/{waited:.0f}s")
    else:
        out.append("hangSilent=[unknown — no exit record, so the end of the wait "
                   "has no time]")

    gaps = []
    for a, b in zip(crumbs, crumbs[1:]):
        try:
            gaps.append((float(b["at"]) - float(a["at"]), float(a["at"])))
        except ValueError:
            continue
    if gaps:
        worst, where = max(gaps)
        # PAIRED READING: the value and where it happened, one entry. A worst
        # gap with no position is a number nobody can act on.
        out.append(f"hangCrumbGapWorst={worst:.1f}s@at:{where:.1f}s")
        out.append("hangCrumbGapMedian=%.2fs" % statistics.median(g for g, _ in gaps))
    else:
        out.append("hangCrumbGap=[one breadcrumb only — no gap to measure]")
    return out, True


# ── dayMark, which already existed and keeps its job ─────────────────────────

def daymark_block(log_lines, cap=13):
    """The rate through in-game days. NOT a position, and it cannot be one.

    `SampleDayShape` fires on `Hour == 12` EXACTLY, and `GameController.Update`
    caps the clock step at 2 real seconds — so a frame can advance the world by
    up to 40 in-game minutes and a slow enough run steps straight over noon
    without ever logging. Silence here therefore has two causes and the
    breadcrumb above has one; read them in that order.
    """
    out = []
    marks = []
    for line in log_lines:
        m = DAYMARK.search(line)
        if m:
            marks.append((int(m.group(1)), float(m.group(2)), int(m.group(3))))
    out.append(f"hangDayMarks={len(marks)}/{len(log_lines)}")   # found / lines examined
    if not marks:
        out.append(f"hangDayMark=[{NO_DAYMARK}]")
        return out, False
    day, at, frames = marks[-1]
    out.append(f"hangLastDay={day}")
    out.append(f"hangLastDayAt={at:.0f}s")
    out.append(f"hangLastDayFrames={frames}")
    shown = marks[:cap]
    series = ",".join(f"d{d}:{a:.0f}" for d, a, _ in shown)
    if len(marks) > cap:
        series += f",+{len(marks) - cap}_more_not_shown"
    out.append(f"hangDaySecs=[{series}]")
    return out, True


# ── the tails, moved here from the shell unchanged in shape ──────────────────

def tail_block(log_lines, own_cap, sim_cap, raw_cap):
    body = [l for l in log_lines if l != ""]
    own = [l for l in body if OWN_LINE.match(l)]
    sim = [l for l in body if l.startswith("SimDirector: ")]
    out = ["hangTail=[the sim produced no done line; three tails follow — "
           "structural, sim-only, raw]",
           f"hangTailLines={len(body)}",
           f"hangTailOwn={len(own)}",
           f"hangSimLines={len(sim)}"]

    def emit(prefix, rows, cap):
        # EVERY CAP ANNOUNCES ITSELF. A `| head -3` here once read as "three of
        # five systems failed" when nothing was broken, so the count shown and
        # the count there are both printed even when the cap does not bite.
        kept = rows[-cap:] if cap else rows
        hidden = len(rows) - len(kept)
        note = f"[{len(kept)} of {len(rows)} shown"
        note += f", +{hidden} not shown]" if hidden else "]"
        out.append(f"{prefix}| {note}")
        out.extend(f"{prefix}| {r}" for r in kept)

    emit("hangOwn", own, own_cap)
    emit("hangSim", sim, sim_cap)
    emit("hangTail", body, raw_cap)
    return out


def classify(facts, log_lines):
    """One sentence saying which kind of ending this was."""
    if not facts:
        return ("[no exit record — the sim step did not report; the log has "
                "%d line(s)]" % len(log_lines))
    if facts.get("simTimedOut") == "yes":
        return ("[killed at the %ss wait — the sim was still running when the "
                "runner shot it]" % facts.get("simWaitLimit", "?"))
    code = facts.get("simExit", "?")
    if code == "3":
        return ("[the in-sim watchdog gave up and quit cleanly before the "
                "external kill — see hangPhase]")
    if code == "0":
        return "[the sim exited 0 with no done line — it quit before Finish ran]"
    return f"[the sim exited {code} with no done line — a crash, not a timeout]"


def report(log_lines, crumb_lines, exit_lines, own_cap, sim_cap, raw_cap):
    """The whole report as (lines, exit_code). Pure, so the selftest can drive
    it without a filesystem for anything but the fixtures."""
    facts = exit_facts(exit_lines)
    out = [outcome_line(facts)]
    if any(DONE_LINE in l for l in log_lines):
        # THE ACCEPTING CASE, AND IT IS FIRST HERE FOR THE SAME REASON IT IS
        # FIRST IN THE SELFTEST: the expensive failure is a diagnostic that
        # fires on healthy runs, and nobody would notice for weeks.
        return out, 0
    out.append("hangClass=" + classify(facts, log_lines))
    waited = None
    try:
        waited = float(facts["simWaitSeconds"])
    except (KeyError, ValueError):
        waited = None
    crumbs, read, bad = parse_crumbs(crumb_lines)
    block, got_crumb = crumb_block(crumbs, read, bad, crumb_lines is not None, waited)
    out += block
    marks, got_mark = daymark_block(log_lines)
    out += marks
    out += tail_block(log_lines, own_cap, sim_cap, raw_cap)
    return out, (10 if (got_crumb or got_mark) else 11)


# ── selftest ─────────────────────────────────────────────────────────────────

TAIL_PREFIXES = ("hangOwn| ", "hangSim| ", "hangTail| ", "hangCrumbBad| ")
KV_LINE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*=\S+( [A-Za-z][A-Za-z0-9_]*=\S+)*$")


def space_free(lines):
    """A VERDICT VALUE MAY NOT CONTAIN A SPACE — every reader splits on
    whitespace and truncates silently, which once turned
    `0.45(narrowest 0.39 broadest 0.53)` into `0.45(narrowest`.

    Bracketed runs are values the readers consume whole, so they are stripped
    first, exactly as `verdict-keys.py` strips them. Tail lines carry raw log
    text behind a `|` and are not key=value at all.
    """
    bad = []
    for line in lines:
        if not line or line.startswith(TAIL_PREFIXES):
            continue
        flat = line
        while True:
            stripped = re.sub(r"\[[^\[\]]*\]", "X", flat)
            if stripped == flat:
                break
            flat = stripped
        if not KV_LINE.match(flat):
            bad.append(line)
    return bad


def selftest():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        note = ("  — " + str(detail)) if (detail and not cond) else ""
        print(("  PASS  " if cond else "  FAIL  ") + name + note)
        if not cond:
            ok = False

    # SYNTHETIC FIXTURES, AUTHORED HERE. Never a real project file: two
    # rejecting fixtures in this repo were pinned to `Joe.fbx` and
    # `police.fbx` and had to be unpinned, because a fixture pinned to a real
    # asset goes red when the PROJECT improves.
    healthy_log = [
        "GfxDevice: creating device client",
        "SimDirector: simulating 11 day(s)",
        "SimDirector: dayMark day=1 at=19s frames=307",
        "SimDirector: dayMark day=2 at=91s frames=2810",
        "Setting and getting Body Position/Rotation, IK Goals",
        "SimDirector: done. errors=0 npcsMoved=True pass=True",
        "SimDirector: ALL GATES green",
    ]
    stalled_log = [
        "GfxDevice: creating device client",
        "WorldBuilder: capsule meshes 0 [none]",
        "SimDirector: simulating 11 day(s)",
        "SimDirector: companion — June walks with you (loyalty 0.80)",
        "SimDirector: staged deed #1 (64 considered, 3 got something)",
        "Setting and getting Body Position/Rotation, IK Goals",
        "'R8_SRGB' is not supported. RenderTexture::GetTemporary fallbacks",
    ]
    crumbs_ok = [
        "# stall breadcrumbs — 11 day(s) requested",
        "at=1.500 phase=begin/done pass=0 frames=41 day=1/12 hr=8 crumb=1",
        "at=2.001 phase=update/stages pass=30 frames=71 day=1/12 hr=8 crumb=2",
        "at=2.502 phase=update/samplers pass=60 frames=101 day=1/12 hr=9 crumb=3",
        "at=3.004 phase=update/acttwo pass=90 frames=131 day=1/12 hr=9 crumb=4",
        "",
    ]
    exit_killed = ["simTimedOut=yes", "simExit=killed", "simWaitSeconds=1451",
                   "simWaitLimit=1440"]
    exit_clean = ["simTimedOut=no", "simExit=0", "simWaitSeconds=812",
                  "simWaitLimit=1440"]

    print("hang-report --selftest")
    print()
    print("CASE 1 (ACCEPTING, and it is first on purpose): a log WITH a done line.")
    lines, code = report(healthy_log, crumbs_ok, exit_clean, 40, 12, 12)
    for l in lines:
        print("      " + l)
    check("exit 0", code == 0, f"got {code}")
    check("prints NO hang diagnostics at all",
          not any("hang" in l for l in lines),
          "; ".join(l for l in lines if "hang" in l))
    check("still prints the run's outcome, so simWaitSeconds lands a series",
          any(l.startswith("simTimedOut=no simExit=0 simWaitSeconds=812") for l in lines))
    check("no value carries a space", not space_free(lines), str(space_free(lines)))
    print()

    print("CASE 2: no done line, breadcrumbs and dayMarks present.")
    lines, code = report(stalled_log, crumbs_ok, exit_killed, 40, 12, 12)
    for l in lines:
        print("      " + l)
    check("exit 10", code == 10, f"got {code}")
    check("leads with the outcome then the classification",
          lines[0].startswith("simTimedOut=yes") and lines[1].startswith("hangClass=["))
    check("the position comes before the tails",
          lines.index("hangPhase=update/acttwo") < lines.index("hangTailLines=7"))
    check("the last breadcrumb's phase is the one reported",
          "hangPhase=update/acttwo" in lines)
    check("silence is the wait minus the last breadcrumb",
          "hangSilent=1448.0s/1451s" in lines,
          [l for l in lines if l.startswith("hangSilent")])
    check("breadcrumbs ship their denominator", "hangCrumbs=4/4" in lines)
    check("a cap that does NOT bite still prints its denominator",
          "hangOwn| [5 of 5 shown]" in lines and "hangSim| [3 of 3 shown]" in lines)
    check("dayMark is absent here and says so, with its denominator",
          f"hangDayMark=[{NO_DAYMARK}]" in lines and "hangDayMarks=0/7" in lines)
    check("no value carries a space", not space_free(lines), str(space_free(lines)))
    print()

    print("CASE 3: no done line, NO breadcrumb file, NO dayMark — the honest case.")
    lines, code = report(stalled_log, None, exit_killed, 40, 12, 12)
    for l in lines:
        print("      " + l)
    check("exit 11 — a different outcome from case 2, and a different code",
          code == 11, f"got {code}")
    check("says the breadcrumb file was ABSENT, in words",
          any("hangCrumbFile=[absent" in l for l in lines))
    check("says the dayMark words too", any(NO_DAYMARK in l for l in lines))
    check("prints NO position key at all — not a zero, not an empty value",
          not any(l.split("=")[0] in ("hangPhase", "hangPass", "hangFrames",
                                      "hangAt", "hangDay", "hangHour",
                                      "hangLastDay") for l in lines))
    check("no value carries a space", not space_free(lines), str(space_free(lines)))
    print()

    print("CASE 4: the breadcrumb file exists but this reader cannot parse it "
          "(emitter drift).")
    lines, code = report(stalled_log,
                         ["# stall breadcrumbs", "at=9.0 stage=update/tick tick=3"],
                         exit_killed, 40, 12, 12)
    for l in lines:
        print("      " + l)
    check("exit 11 — drift is not a position", code == 11, f"got {code}")
    check("names it drift rather than absence",
          any("hangCrumbDrift=[" in l for l in lines))
    check("counts the lines it could not parse", "hangCrumbs=0/1" in lines)
    check("does NOT print the no-heartbeat words, which would be a lie",
          not any(NO_CRUMB in l for l in lines))
    check("no value carries a space", not space_free(lines), str(space_free(lines)))
    print()

    print("CASE 5: no exit record at all.")
    lines, code = report(stalled_log, crumbs_ok, None, 40, 12, 12)
    for l in lines:
        print("      " + l)
    check("says so in words", any(NO_EXIT in l for l in lines))
    check("prints no simTimedOut / simWaitSeconds rather than a zero",
          not any(l.startswith(("simTimedOut", "simWaitSeconds")) for l in lines))
    check("and silence is unknown rather than invented",
          any(l.startswith("hangSilent=[unknown") for l in lines))
    print()

    print("CASE 6: the caps announce themselves.")
    long_log = [f"Filler{i}: line {i}" for i in range(60)] + \
               [f"SimDirector: step {i}" for i in range(20)] + \
               ["engine noise"] * 5
    lines, _ = report(long_log, None, exit_killed, 40, 12, 12)
    caps = [l for l in lines if " of " in l and "shown" in l]
    for l in caps:
        print("      " + l)
    check("the structural tail says how many it hid",
          any(l.startswith("hangOwn| [40 of 80 shown, +40 not shown]") for l in caps))
    check("the sim tail says how many it hid",
          any(l.startswith("hangSim| [12 of 20 shown, +8 not shown]") for l in caps))
    check("the raw tail says how many it hid",
          any(re.match(r"hangTail\| \[12 of 85 shown, \+73 not shown\]", l) for l in caps))
    print()

    print("CASE 7: the live emitter still speaks this reader's language.")
    src = ROOT / "ledger" / "Assets" / "Scripts" / "Game" / "SimDirector.cs"
    text = src.read_text(encoding="utf-8") if src.exists() else ""
    # THE LIVE CODEBASE IS THE ACCEPTING FIXTURE. Nothing here can RUN the
    # Game layer, so the one thing that can be checked is that the emitter
    # still contains every field this parser requires — the exact fault
    # `verdict-keys.py` exists for, one layer down.
    emitted = emitter_fields(text)
    missing = [k for k in CRUMB_REQUIRED if emitted is None or k not in emitted]
    check("SimDirector.cs's breadcrumb emit block writes every field this reader "
          "requires", src.exists() and not missing,
          f"emit block {emitted}, missing {missing}")
    # REJECTING FIXTURE, SYNTHETIC: an emitter that dropped a field must be
    # caught. Pinned to no real file, so improving SimDirector cannot fail it.
    fake_src = ('System.IO.File.AppendAllText(CrumbFile,\n'
                '    $"at={at:0.000} phase={phase} pass={_updatePasses} "\n'
                '    + $"frames={Time.frameCount}\\n");')
    check("and an emitter that dropped `crumb=` would be caught",
          "crumb" not in (emitter_fields(fake_src) or set())
          and "phase" in (emitter_fields(fake_src) or set()),
          str(emitter_fields(fake_src)))
    check("and a file with no emit block at all reads as None, not as empty",
          emitter_fields("int pass=3; day=4; crumb=5;") is None)
    check("and still emits the dayMark shape this reader matches",
          "SimDirector: dayMark day=" in text)
    # REJECTING FIXTURE, SYNTHETIC. Pinned to nothing real, so doing the work
    # this tool prompts can never break the tool.
    fake = ["# stall breadcrumbs", "at=1.0 phase=x pass=0 frames=1 day=1/2 hr=8"]
    got, _, bad = parse_crumbs(fake)
    check("and a breadcrumb missing `crumb=` is rejected, not half-read",
          got == [] and bad is not None)
    print()

    print("ALL PASSED" if ok else "SELFTEST FAILED")
    return 0 if ok else 3


def main():
    _quiet_pipe()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--log", help="player.log")
    ap.add_argument("--exit", dest="exitfile", help="sim-exit.txt from the sim step")
    ap.add_argument("--crumbs", help="sim-out/stall.txt, the stall breadcrumb")
    ap.add_argument("--own-cap", type=int, default=40)
    ap.add_argument("--sim-cap", type=int, default=12)
    ap.add_argument("--raw-cap", type=int, default=12)
    ap.add_argument("--outcome-only", action="store_true",
                    help="just the simExit line — for the branch where there is "
                         "no player.log at all, which is the run where how the "
                         "process ended is the ONLY thing anybody can know")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.outcome_only:
        print(outcome_line(exit_facts(read_lines(a.exitfile))))
        return 0
    if not a.log:
        print("hang-report: --log is required (or --selftest)", file=sys.stderr)
        return 2
    log = read_lines(a.log)
    if log is None:
        print("hang-report: cannot read %s" % a.log, file=sys.stderr)
        return 2
    lines, code = report(log, read_lines(a.crumbs), read_lines(a.exitfile),
                         a.own_cap, a.sim_cap, a.raw_cap)
    for l in lines:
        print(l)
    return code


if __name__ == "__main__":
    sys.exit(main())
