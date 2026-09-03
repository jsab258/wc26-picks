#!/usr/bin/env python3
"""WHAT A SPAWN COST, PER TIER AND PER TURN, INSTEAD OF PER SPAWN.

    python3 tools/spawn-cost.py --report              # read the turns log
    python3 tools/spawn-cost.py --transcripts DIR     # the series, from disk
    python3 tools/spawn-cost.py --hook                # SubagentStop, stdin JSON
    python3 tools/spawn-cost.py --selftest            # accepting case FIRST

WHY IT EXISTS. Every estimate in this project rests on "a spawn costs 1.5 to 2
points", which averages a 12-turn fable median with a 45-turn opus median
(transcripts on the build machine, 2026-09-03)
and is why the estimates here are consistently low. `.claude/agent-log.tsv`
records one row per spawn and nothing else, so the average is the only
statistic it can support. Jafar asked on 2026-09-03 for model tier and turn
count at SubagentStop, "so calibration is per tier and turns rather than per
spawn".

WHAT SubagentStop CAN ACTUALLY SEE, established from files rather than
assumed, because inventing a field the hook cannot fill is the silent failure
this whole tool is aimed at. The event and its payload are defined in the
Claude Code binary at /opt/claude-code/bin/claude:

    hook_event_name  "SubagentStop"
    stop_hook_active  agent_id  agent_transcript_path  agent_type
    last_assistant_message (optional)   background_tasks (optional)
    ... plus the common fields: session_id, transcript_path, cwd,
    prompt_id, permission_mode, effort

THERE IS NO MODEL FIELD AND NO TURN COUNT FIELD. Both are DERIVED, and from
the one field that makes deriving them possible: `agent_transcript_path`. The
subagent's own transcript is JSONL, one object per line, and every assistant
line carries `message.model` and `message.id`. So:

    tier   = the model family of the MODAL assistant message (most lines),
             mapped opus / fable / sonnet. Marked `+mixed` when more than one
             family appears, because a fallback mid-run is a different animal
             from a clean run and must not average silently into either.
    turns  = COUNT of DISTINCT `message.id` among assistant lines. One API
             assistant message is written to the transcript as several lines
             when it carries thinking, text and a tool call, so the line count
             runs about 1.8x the turn count here. Both are recorded: `turns`
             is what `maxTurns` bounds, `alines` is what anybody grepping the
             transcript will count, and a reader who confuses them is off by
             most of a factor of two.

THE TIER AND THE TURNS ARE READ AT THE SAME INSTANT, off one read of one file
at the moment the subagent stopped. The transcripts live under ~/.claude and
do not survive the container; the row in the repository does.

EXIT CODES, distinct per outcome. 0 a reading was printed. 1 the log or the
directory could not be read. 2 nothing measured: no rows, no transcripts.
3 the selftest failed. The --hook mode ALWAYS exits 0: a broken audit trail
must never be able to stop the work it only describes.
"""
import argparse
import datetime
import json
import os
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

# ONE IMPLEMENTATION PER IDEA: the truncation notice and the never-measured
# words already exist in this repo and are imported, never re-typed.
sys.path.insert(0, str(HERE))
from capsay import cap, NOTHING_MEASURED                          # noqa: E402

TURNS_LOG = ".claude/agent-turns.tsv"
COLUMNS = ("when", "agent", "tier", "turns", "alines", "agentId")

# THE TIERS THIS STUDIO DECLARES, read off `.claude/agents/*.md` on
# 2026-09-03: 11 agents on opus, 2 on fable, 1 on sonnet. A tier in this list
# with no rows prints the words "nothing measured" rather than 0, because a
# tier nobody has spawned and a tier that ran 0 turns are different facts.
KNOWN_TIERS = ("opus", "fable", "sonnet")
TIER_OF = {"opus": "opus", "fable": "fable", "sonnet": "sonnet",
           "haiku": "haiku"}
# Claude Code writes `<synthetic>` as the model of a message it generated
# itself (an interrupt notice, a refusal). It is not a tier and its lines are
# not turns; a spawn whose transcript is nothing but synthetic lines produced
# NOTHING, and must not read as a one-turn opus spawn.
SYNTHETIC = "<synthetic>"
NO_TIER = "no-model"


def tier_of_model(model):
    """The tier a model name belongs to. Unknown names keep their own name
    rather than being bucketed into a tier they were never in."""
    if not model or model == SYNTHETIC:
        return None
    low = model.lower()
    for key, tier in TIER_OF.items():
        if key in low:
            return tier
    return "other:" + low.replace(" ", "-")


def read_transcript(path):
    """One transcript, at one instant. Returns the whole reading as a dict.

    PURE ARITHMETIC IN THE TESTED LAYER: the hook shim below calls this and
    formats nothing itself, so nothing that computes a number here ships
    unrun.
    """
    r = {"turns": 0, "alines": 0, "tier": NO_TIER, "families": {},
         "unparsed": 0, "lines": 0, "synthetic": 0, "path": str(path),
         "synth_text": ""}
    ids = set()
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        r["tier"] = NOTHING_MEASURED
        return r
    for line in text.splitlines():
        if not line.strip():
            continue
        r["lines"] += 1
        try:
            d = json.loads(line)
        except ValueError:
            r["unparsed"] += 1          # COUNTED, never silently dropped
            continue
        if d.get("type") != "assistant":
            continue
        m = d.get("message") or {}
        model = m.get("model")
        if model == SYNTHETIC:
            r["synthetic"] += 1
            # WHY A SPAWN PRODUCED NOTHING IS THE HALF THAT MATTERS. 149 of
            # the 453 subagent transcripts on this machine hold exactly one
            # synthetic line reading "You've hit your session limit", which is
            # a spawn that was started, cost a slot, and did no work. Counted
            # as a 0-turn spawn with no reason it reads as a quiet agent.
            if not r["synth_text"]:
                c = m.get("content")
                if isinstance(c, list):
                    c = " ".join(str(b.get("text", "")) for b in c
                                 if isinstance(b, dict))
                r["synth_text"] = str(c or "")[:70].replace("\n", " ")
            continue
        r["alines"] += 1
        if m.get("id"):
            ids.add(m["id"])
        fam = tier_of_model(model)
        if fam:
            r["families"][fam] = r["families"].get(fam, 0) + 1
    # turns = distinct API assistant messages. An assistant line with no
    # message.id (older transcripts) still counts as a turn of its own, or a
    # whole run of them would collapse to 0.
    r["turns"] = len(ids) if ids else r["alines"]
    if r["families"]:
        modal = max(r["families"].items(), key=lambda kv: kv[1])[0]
        r["tier"] = modal + ("+mixed" if len(r["families"]) > 1 else "")
    return r


# ------------------------------------------------------------------ the log

def log_path(root=None):
    return pathlib.Path(root or REPO) / TURNS_LOG


def append_row(row, root=None):
    """One row, appended. The header is written only when the file is absent,
    so this file is append-only by construction (rule 5)."""
    p = log_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or not p.stat().st_size:
        p.write_text("\t".join(COLUMNS) + "\n", encoding="utf-8")
    # A TAB IN A VALUE WOULD SPLIT THE ROW, the same fault as a space in a
    # verdict value: every reader of this file splits on tabs.
    clean = [str(v).replace("\t", " ").replace("\n", " ").replace("\r", " ")
             for v in row]
    with p.open("a", encoding="utf-8") as fh:
        fh.write("\t".join(clean) + "\n")
    return p


def read_log(path):
    """(rows, short, unmeasured). THREE BUCKETS, not two, because they are
    three different facts and a reader that merged them would print a clean
    denominator over a set it never examined:

      rows        a spawn with a tier and a turn count
      short       a row this reader cannot parse, including the 2-column rows
                  in `.claude/agent-log.tsv` written before this tool existed.
                  Padding one would invent a turn count.
      unmeasured  a spawn that WAS recorded and whose transcript was already
                  gone at SubagentStop. It happened; its turns are unknown;
                  it must not sit in a median as a zero.
    """
    rows, short, unmeasured = [], 0, 0
    p = pathlib.Path(path)
    if not p.exists():
        return None, 0, 0
    for i, line in enumerate(p.read_text(encoding="utf-8",
                                         errors="replace").splitlines()):
        if not line.strip():
            continue
        cols = line.split("\t")
        if i == 0 and cols[0].strip() == "when":
            continue
        if len(cols) < len(COLUMNS):
            short += 1
            continue
        d = dict(zip(COLUMNS, cols))
        if d["tier"] == NOTHING_MEASURED or d["turns"] == NOTHING_MEASURED:
            unmeasured += 1
            continue
        try:
            d["turns"] = int(d["turns"])
            d["alines"] = int(d["alines"])
        except ValueError:
            short += 1
            continue
        if d["turns"] < 0:
            unmeasured += 1
            continue
        rows.append(d)
    return rows, short, unmeasured


# --------------------------------------------------------------- the reading

def by_tier(rows):
    """{tier: [rows]} for every tier in KNOWN_TIERS plus any tier the rows
    actually carry. A KNOWN tier with no rows is present and EMPTY, so the
    report can print the words rather than a zero."""
    out = {t: [] for t in KNOWN_TIERS}
    for r in rows:
        out.setdefault(r["tier"].split("+")[0], []).append(r)
    return out


def tier_line(tier, rows):
    """One tier's reading, and every statistic says what it is a statistic OF.

    NO SPACES IN ANY VALUE: this line is a key=value channel and every reader
    of one splits on whitespace.
    """
    if not rows:
        return ("%-8s spawns=0/%s turnsMedian=%s turnsPeak=%s turnsTotal=%s"
                % (tier, NOTHING_MEASURED, NOTHING_MEASURED, NOTHING_MEASURED,
                   NOTHING_MEASURED))
    turns = sorted(r["turns"] for r in rows)
    peak = max(rows, key=lambda r: r["turns"])
    # THE PEAK CARRIES THE SPAWN IT CAME FROM, at the instant it peaked: a
    # peak with no owner cannot be looked up, and the next reader re-derives
    # it from a different window and gets a different number.
    return ("%-8s spawns=%d turnsMedian=%d turnsPeak=%d@%s turnsTotal=%d "
            "alinesTotal=%d turnsMin=%d"
            % (tier, len(rows), int(statistics.median(turns)), peak["turns"],
               (peak.get("agentId") or peak.get("agent") or "unknown")[:18],
               sum(turns), sum(r["alines"] for r in rows), turns[0]))


def report(rows, short, source, spawn_rows=None, unmeasured=0):
    """Every zero here ships the denominator that produced it."""
    print("spawn-cost: source=%s" % source)
    if rows is None:
        print("  %s: no turns log at %s. The SubagentStop hook that writes it "
              "is not registered in .claude/settings.json, so no spawn has "
              "recorded a tier or a turn count yet." % (NOTHING_MEASURED,
                                                        TURNS_LOG))
        return 2
    if not rows:
        print("  %s: the log exists and carries 0 usable row(s) (%d short or "
              "unparseable, %d recorded but unmeasurable)"
              % (NOTHING_MEASURED, short, unmeasured))
        return 2
    groups = by_tier(rows)
    print("  %d spawn(s) with a tier and a turn count, %d recorded but "
          "unmeasurable (transcript already gone), %d short or unparseable"
          % (len(rows), unmeasured, short))
    if spawn_rows is not None:
        # THE PAIRED READING: how many of the spawns the START log counted
        # produced a stop row at all. Two files, one denominator, and the gap
        # is interrupted spawns plus everything spawned before the hook.
        print("  coverage: %d of %d spawn(s) in %s carry a turn record"
              % (len(rows), spawn_rows, ".claude/agent-log.tsv"))
    for tier in sorted(groups, key=lambda t: (t not in KNOWN_TIERS, t)):
        print("  " + tier_line(tier, groups[tier]))
    allturns = sorted(r["turns"] for r in rows)
    print("  ALL TIERS TOGETHER, which is the statistic every estimate in this "
          "project has been using: spawns=%d turnsMean=%.1f turnsMedian=%d "
          "turnsPeak=%d" % (len(allturns), sum(allturns) / len(allturns),
                            int(statistics.median(allturns)), max(allturns)))
    print("  the mean above is the number that hides the tiers; the per-tier "
          "medians are what a per-tier estimate reads")
    return 0


# --------------------------------------------------------- the printer first

def series(directory, limit=0):
    """THE PRINTER THAT COMES BEFORE ANY BOUND. Every transcript under
    `directory`, one line each, then the same per-tier reading.

    This is how the first real series was read on 2026-09-03: the hook was not
    registered yet, and a bound guessed before the series is a rounding in a
    measurement's clothes."""
    d = pathlib.Path(directory)
    every = sorted(d.rglob("*.jsonl")) if d.is_dir() else []
    # ONLY THE SPAWNS. The parent session transcript sits beside them and is
    # not a spawn: it read 5,754 turns into the first run of this printer and
    # took the opus peak with it. Excluded BY NAME with its count, because an
    # exclusion nobody prints is the same as a cap nobody announces.
    files = [f for f in every if f.parent.name == "subagents"]
    excluded = [f for f in every if f.parent.name != "subagents"]
    if not files:
        print("spawn-cost --transcripts: %s, no .jsonl under %s"
              % (NOTHING_MEASURED, directory))
        return 2
    shown = files if not limit else files[:limit]
    rows = []
    for f in files:
        t = read_transcript(f)
        rows.append({"when": datetime.datetime.utcfromtimestamp(
                        f.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "agent": "unknown", "tier": t["tier"],
                     "turns": t["turns"], "alines": t["alines"],
                     "agentId": f.stem, "why": t["synth_text"]})
    print("spawn-cost --transcripts: %s" % directory)
    if excluded:
        print("  %d transcript(s) EXCLUDED as not-a-spawn (outside a "
              "subagents/ directory): %s"
              % (len(excluded), cap([f.stem for f in excluded], keep=2,
                                    width=30, sep=", ")))
    # TWO NUMBERS, NOT ONE, because they are two different facts and the
    # first version of this line printed the larger one under the smaller
    # one's sentence: a spawn can hit the limit AFTER doing work, and 21 of
    # these did. `noticed` is who saw the wall; `dead` is who never moved.
    noticed = [r for r in rows if "limit" in r.get("why", "")]
    dead = [r for r in noticed if r["turns"] == 0]
    if noticed:
        print("  %d of %d spawn(s) carry a session-limit notice, and %d of "
              "those %d produced NO turn at all: a spawn slot spent on "
              "nothing. Example notice: %s"
              % (len(noticed), len(files), len(dead), len(noticed),
                 cap(sorted({r["why"] for r in noticed}), keep=1, width=60)))
    print("  %d transcript(s) walked%s"
          % (len(files),
             "" if not limit else ", %d shown (+%d more not shown of %d)"
             % (len(shown), len(files) - len(shown), len(files))))
    for r in sorted(rows, key=lambda r: -r["turns"])[:len(shown)]:
        print("    %-24s tier=%-12s turns=%-4d alines=%d"
              % (r["agentId"][:24], r["tier"], r["turns"], r["alines"]))
    if limit and len(files) > len(shown):
        print("    (+%d more not shown of %d)" % (len(files) - len(shown),
                                                  len(files)))
    print("")
    # THE TRANSCRIPTS CARRY NO AGENT TYPE. `agent_type` is a hook field and
    # nothing else writes it, so this series is per TIER only. Said out loud
    # rather than left for a reader to notice the column is always `unknown`.
    print("  the agent TYPE is not in a transcript: it is a SubagentStop hook "
          "field, so this series is per tier and per turn only")
    return report(rows, 0, "transcripts:" + str(directory))


# ------------------------------------------------------------------ the hook

def hook(stdin_text, root=None, now=None):
    """SubagentStop. Returns (row, why) with row None when nothing was
    written. NEVER RAISES: the caller exits 0 whatever happens here."""
    try:
        d = json.loads(stdin_text)
    except ValueError:
        return None, "stdin is not JSON"
    if not isinstance(d, dict):
        return None, "stdin is not an object"
    agent = (d.get("agent_type") or "").strip()
    if not agent:
        # NOTHING PARSED, NOTHING WRITTEN: a row with an empty agent column
        # reads as "an agent with no name ran", which is a finding; the truth
        # is that the hook could not tell, and those must not look alike.
        return None, "no agent_type in the payload"
    tpath = d.get("agent_transcript_path") or ""
    if tpath and pathlib.Path(tpath).exists():
        t = read_transcript(tpath)
    else:
        # THE FIELD IS OPTIONAL AND THE FILE MAY BE GONE. Record the spawn
        # with the words, never with a 0 that reads as a spawn that did
        # nothing.
        t = {"turns": NOTHING_MEASURED, "alines": NOTHING_MEASURED,
             "tier": NOTHING_MEASURED}
    when = (now or datetime.datetime.now(datetime.timezone.utc)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    row = (when, agent, t["tier"], t["turns"], t["alines"],
           d.get("agent_id") or "unknown")
    append_row(row, root)
    return row, "appended"


# ------------------------------------------------------------------ selftest

# ACCEPTING FIRST. The expensive failure is a reader that cannot see a normal
# spawn, which would send every future estimate back to the flat average this
# tool exists to replace.
def _jsonl(entries):
    return "\n".join(json.dumps(e) for e in entries) + "\n"


GOOD_TRANSCRIPT = _jsonl([
    {"type": "user", "message": {"role": "user", "content": "go"}},
    {"type": "assistant", "message": {"id": "m1", "model": "claude-opus-5"}},
    {"type": "assistant", "message": {"id": "m1", "model": "claude-opus-5"}},
    {"type": "assistant", "message": {"id": "m2", "model": "claude-opus-5"}},
])
FABLE_TRANSCRIPT = _jsonl([
    {"type": "assistant", "message": {"id": "f1", "model": "claude-fable-5"}},
])
SYNTH_ONLY = _jsonl([
    {"type": "assistant", "message": {"id": "s1", "model": "<synthetic>"}},
])
MIXED = _jsonl([
    {"type": "assistant", "message": {"id": "x1", "model": "claude-opus-5"}},
    {"type": "assistant", "message": {"id": "x2", "model": "claude-opus-5"}},
    {"type": "assistant", "message": {"id": "x3", "model": "claude-fable-5"}},
])


def _tmp(text, name="t.jsonl"):
    import atexit
    import shutil
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp(prefix="spawn-cost-"))
    atexit.register(shutil.rmtree, str(d), True)
    p = d / name
    p.write_text(text, encoding="utf-8")
    return p


def selftest():
    passed, failed = 0, []

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s\n         got: %r" % (name, got))

    print("spawn-cost --selftest: ACCEPTING CASES FIRST\n")
    t = read_transcript(_tmp(GOOD_TRANSCRIPT))
    ok("a normal opus transcript reads as opus", t["tier"] == "opus", t["tier"])
    ok("two distinct message ids over three assistant lines is 2 turns, "
       "3 alines", (t["turns"], t["alines"]) == (2, 3), (t["turns"], t["alines"]))
    tf = read_transcript(_tmp(FABLE_TRANSCRIPT))
    ok("a fable transcript reads as fable", tf["tier"] == "fable", tf["tier"])
    tm = read_transcript(_tmp(MIXED))
    ok("a transcript that changed model mid-run is marked mixed, not averaged "
       "into one tier", tm["tier"] == "opus+mixed", tm["tier"])

    print("\n  THE CASES A ZERO WOULD LIE ABOUT:\n")
    ts = read_transcript(_tmp(SYNTH_ONLY))
    ok("a transcript of nothing but synthetic lines is %s, never a one-turn "
       "spawn" % NO_TIER, ts["tier"] == NO_TIER and ts["turns"] == 0,
       (ts["tier"], ts["turns"]))
    tb = read_transcript(_tmp("{not json\n" + GOOD_TRANSCRIPT))
    ok("a malformed line is COUNTED as unparsed, not dropped in silence",
       tb["unparsed"] == 1 and tb["turns"] == 2, (tb["unparsed"], tb["turns"]))
    tn = read_transcript("/nonexistent/agent.jsonl")
    ok("a transcript that is not there reads as the words",
       tn["tier"] == NOTHING_MEASURED, tn["tier"])
    ok("a tier with no rows prints the words, never 0",
       NOTHING_MEASURED in tier_line("sonnet", []), tier_line("sonnet", []))
    ok("and the words carry no space, because this is a key=value line",
       " " not in tier_line("sonnet", []).split("spawns=")[1].split()[0],
       tier_line("sonnet", []))

    print("\n  THE HOOK, both ways:\n")
    import tempfile
    root = pathlib.Path(tempfile.mkdtemp(prefix="spawn-cost-root-"))
    import atexit
    import shutil
    atexit.register(shutil.rmtree, str(root), True)
    tp = _tmp(GOOD_TRANSCRIPT, "agent-abc.jsonl")
    row, why = hook(json.dumps({"hook_event_name": "SubagentStop",
                                "agent_type": "systems-builder",
                                "agent_id": "agent-abc",
                                "agent_transcript_path": str(tp)}), root)
    ok("a real SubagentStop payload appends one row carrying tier and turns",
       row is not None and row[1] == "systems-builder" and row[2] == "opus"
       and row[3] == 2, (row, why))
    rows, short, unmeas = read_log(log_path(root))
    ok("and the row reads back with its tier and its turn count",
       len(rows) == 1 and rows[0]["tier"] == "opus" and rows[0]["turns"] == 2,
       rows)
    ok("the header names every column it writes",
       log_path(root).read_text().splitlines()[0].split("\t") == list(COLUMNS),
       log_path(root).read_text().splitlines()[0])
    row2, why2 = hook("{ not json", root)
    ok("malformed stdin writes nothing and says why", row2 is None, (row2, why2))
    row3, why3 = hook(json.dumps({"hook_event_name": "SubagentStop"}), root)
    ok("a payload with no agent_type writes nothing rather than a nameless row",
       row3 is None, (row3, why3))
    row4, _ = hook(json.dumps({"agent_type": "planner",
                               "agent_transcript_path": "/gone.jsonl"}), root)
    ok("a missing transcript records the words, never turns=0",
       row4 is not None and row4[2] == NOTHING_MEASURED, row4)
    rows, short, unmeas = read_log(log_path(root))
    ok("the unmeasurable row is COUNTED in its own bucket, never as a "
       "0-turn spawn in a median",
       len(rows) == 1 and unmeas == 1 and short == 0,
       (len(rows), unmeas, short))

    print("\n  THE OLD LOG SHAPE, which must not be padded into invented data:\n")
    old = root / "old.tsv"
    old.write_text("when\tagent\n2026-09-03T10:00:00Z\tplanner\n",
                   encoding="utf-8")
    rows, short, unmeas = read_log(old)
    ok("a 2-column row from .claude/agent-log.tsv is counted short, not "
       "given a turn count", rows == [] and short == 1, (rows, short))

    print("\nspawn-cost --selftest: %s. %d passed, %d failed"
          % ("PASS" if not failed else "FAILED", passed, len(failed)))
    for f in failed:
        print("  " + f)
    return 0 if not failed else 3


def _spawn_rows(root=None):
    """How many rows the SubagentStart log carries, for the coverage pair."""
    p = pathlib.Path(root or REPO) / ".claude" / "agent-log.tsv"
    if not p.exists():
        return None
    n = 0
    for i, line in enumerate(p.read_text(encoding="utf-8",
                                         errors="replace").splitlines()):
        if not line.strip():
            continue
        if i == 0 and line.split("\t")[0].strip() == "when":
            continue
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--log", default=None, help="turns log to read")
    ap.add_argument("--transcripts", default=None,
                    help="directory of subagent .jsonl transcripts")
    ap.add_argument("--limit", type=int, default=0,
                    help="print at most N transcript lines (the cap announces "
                         "when it bites)")
    ap.add_argument("--hook", action="store_true",
                    help="SubagentStop: read the payload on stdin, append one "
                         "row, and ALWAYS exit 0")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.hook:
        try:
            hook(sys.stdin.read())
        except Exception:                                        # noqa: BLE001
            pass
        return 0
    if args.transcripts:
        return series(args.transcripts, args.limit)
    path = args.log or log_path()
    rows, short, unmeasured = read_log(path)
    return report(rows, short, str(path), _spawn_rows(), unmeasured)


if __name__ == "__main__":
    # A correct run that ends in a BrokenPipeError traceback costs twenty
    # minutes before anybody notices it worked.
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
