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
import re
import statistics
import subprocess
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

    print("\n  ROUTING DRIFT (--routing-drift), both named traps PLANTED:\n")
    droot = pathlib.Path(tempfile.mkdtemp(prefix="spawn-cost-drift-"))
    (droot / ".claude" / "agents").mkdir(parents=True)
    (droot / ".claude" / "agents" / "worker.md").write_text(
        "---\nname: worker\nmodel: opus\n---\nbody\n", encoding="utf-8")
    turns_log = droot / TURNS_LOG
    turns_log.parent.mkdir(parents=True, exist_ok=True)
    turns_log.write_text(
        "\t".join(COLUMNS) + "\n"
        # TRAP 1: one agentId, SIX snapshot rows, climbing turns. Summed,
        # this alone would read 45+68+83+105+122+162=585 turns for one
        # spawn; last-wins must read 162.
        + "2026-09-01T00:00:00Z\tworker\topus\t45\t80\tclimb1\n"
        + "2026-09-01T00:01:00Z\tworker\topus\t68\t120\tclimb1\n"
        + "2026-09-01T00:02:00Z\tworker\topus\t83\t150\tclimb1\n"
        + "2026-09-01T00:03:00Z\tworker\topus\t105\t190\tclimb1\n"
        + "2026-09-01T00:04:00Z\tworker\topus\t122\t220\tclimb1\n"
        + "2026-09-01T00:05:00Z\tworker\topus\t162\t290\tclimb1\n"
        # A genuine disagreement: declared opus, ran fable.
        + "2026-09-02T00:00:00Z\tworker\tfable\t9\t15\tdisagree1\n"
        # TRAP 2: a built-in type with no definition file on disk.
        + "2026-09-02T01:00:00Z\tgeneral-purpose\topus\t30\t50\tnodecl1\n",
        encoding="utf-8")
    d = routing_drift(droot)
    ok("distinct agentId count is 3, one per agentId, not one per row",
       d["distinct"] == 3, d["distinct"])
    ok("TRAP 1: last-wins reads 162 turns for the climbing spawn, never "
       "the 585-turn sum of all six snapshots",
       d["agreements"] == 1, d["agreements"])   # climb1 agrees: opus==opus
    ok("TRAP 2: general-purpose (no definition) is excluded from the "
       "numerator, not counted as a disagreement",
       d["noDeclaration"] == 1 and d["noDeclarationNames"] == ["general-purpose"],
       (d["noDeclaration"], d["noDeclarationNames"]))
    ok("the one real disagreement (declared opus, ran fable) is bucketed "
       "with its 9 turns, not the climbing spawn's 162 or 585",
       d["buckets"] == [{"declared": "opus", "ran": "fable", "agents": 1,
                        "turns": 9, "whenMin": "2026-09-02T00:00:00Z",
                        "whenMax": "2026-09-02T00:00:00Z"}],
       d["buckets"])
    ok("totalTurns is 162+9+30=201, never 585+9+30 from summing the "
       "climbing snapshots", d["totalTurns"] == 201, d["totalTurns"])
    d_missing = routing_drift(pathlib.Path(tempfile.mkdtemp(prefix="spawn-cost-nolog-")))
    ok("NEVER-RAN: no turns log at all reads rows=None, not an empty drift",
       d_missing.get("rows") is None, d_missing)
    ok("with no git repository at all, committed model reads as unknown and "
       "nothing is excluded as pre-ruling (0 of 3 agentIds)",
       d["preRuling"] == 0, d["preRuling"])
    shutil.rmtree(droot, ignore_errors=True)

    print("\n  PRE-RULING (the director's correction, 2026-09-10): a row "
          "CANNOT violate a declaration that postdates it, PLANTED:\n")
    proot = pathlib.Path(tempfile.mkdtemp(prefix="spawn-cost-preruling-"))

    def run_git(*args):
        subprocess.run(["git", "-C", str(proot)] + list(args),
                       capture_output=True, text=True, check=True)
    (proot / ".claude" / "agents").mkdir(parents=True)
    worker_md = proot / ".claude" / "agents" / "worker.md"
    worker_md.write_text("---\nname: worker\nmodel: opus\n---\nbody\n",
                         encoding="utf-8")
    run_git("init", "-q")
    run_git("config", "user.email", "t@t")
    run_git("config", "user.name", "t")
    run_git("add", "-A")
    run_git("commit", "-q", "-m", "worker: opus, the committed declaration")
    # THE RECLASSIFICATION, uncommitted, exactly as the live ruling left the
    # real nine definitions: working tree says sonnet, HEAD still says opus.
    worker_md.write_text("---\nname: worker\nmodel: sonnet\n---\nbody\n",
                         encoding="utf-8")
    ptlog = proot / TURNS_LOG
    ptlog.parent.mkdir(parents=True, exist_ok=True)
    ptlog.write_text(
        "\t".join(COLUMNS) + "\n"
        # PLANTED: ran opus, long before the reclassification -- compliance
        # with the rule as it THEN stood (declared opus, ran opus), not a
        # disagreement with the rule as it stands now (declared sonnet).
        + "2020-01-01T00:00:00Z\tworker\topus\t50\t90\told1\n",
        encoding="utf-8")
    dp = routing_drift(proot)
    ok("a row predating its agent's reclassification lands in preRuling "
       "(1 row, 50 turns), not the violation count",
       dp["preRuling"] == 1 and dp["preRulingTurns"] == 50, dp)
    ok("and it is NOT counted as an agreement either (it was never judged "
       "against the new declaration at all)", dp["agreements"] == 0,
       dp["agreements"])
    ok("and the violation buckets are empty: the ONLY row on file is the "
       "pre-ruling one", dp["buckets"] == [] and dp["disagreeAgents"] == 0,
       (dp["buckets"], dp["disagreeAgents"]))
    shutil.rmtree(proot, ignore_errors=True)

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


# -------------------------------------------- E4: declared vs ran (a join)
# 2026-09-10 routing ruling, director follow-up: `.claude/agent-log.tsv`'s
# model column (log-agent.sh, same day) records what was ASKED FOR -- the
# SubagentStart payload's own `.model` field if the harness ever supplies
# one, else a `.claude/spawn-intent` sidecar, else the agent definition's
# own `model:` line -- NEVER what actually ran. What ran is recorded
# separately, at SubagentStop, in THIS file's `tier` column, keyed by
# `agentId`. Declared-versus-ran is therefore a JOIN on `agentId`, which is
# the reason that column is on both files, not a read of either alone.


def _declared_models(repo):
    """name -> declared `model:` value, front matter only, from the CURRENT
    `.claude/agents/*.md` files.

    A DELIBERATELY SMALLER READER than `ledger/verify.py`'s `_agent_model_
    defs` (the four-value gate, E1), which also classifies nonAgent/
    noModel/dupModel in detail for refusing a bad definition. This only
    needs a name-to-value map to compare against a RAN tier, and importing
    `ledger/verify.py` as a module from here was avoided on purpose: this
    session was told not to run that file, and keeping this a second,
    narrower, explicitly-justified reader is the safer reading of that
    instruction rather than sharing one through an import."""
    d = pathlib.Path(repo) / ".claude" / "agents"
    out = {}
    try:
        entries = sorted(d.glob("*.md"))
    except OSError:
        entries = []
    for f in entries:
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        if not lines or lines[0].strip() != "---":
            continue
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        for ln in (lines[1:end] if end else lines[1:]):
            m = re.match(r"^model:(.*)$", ln)
            if m:
                out[f.stem.strip().lower()] = m.group(1).strip()
                break
    return out


def _committed_model(repo, name):
    """The `model:` value committed at HEAD for agent `name`, or None when
    the file does not exist there or carries no recognisable line.

    Read via `git show HEAD:...` rather than the working tree, because the
    question this answers is "did the declaration change since the last
    commit", and that question needs BOTH snapshots."""
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), "show",
             "HEAD:.claude/agents/%s.md" % name],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    lines = p.stdout.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    for ln in (lines[1:end] if end else lines[1:]):
        m = re.match(r"^model:(.*)$", ln)
        if m:
            return m.group(1).strip()
    return None


def _ruling_cutovers(repo, decl):
    """name -> epoch seconds after which its CURRENT declared model applies,
    or None when there is none (every row in the turns log may be judged
    against it).

    A ROW BEFORE ITS AGENT'S CUTOVER CANNOT VIOLATE A RULE THAT DID NOT YET
    EXIST FOR THAT AGENT (the director's correction, 2026-09-10): the
    fable and opus disagreements below are real because producer,
    studio-director and the opus-declared builders have carried that exact
    declaration since before any logged spawn, so every row is fairly
    judged against it. Nine OTHER definitions (planner, content-wrangler
    and world-designer among them) were reclassified in the SAME session
    that built this check, so their pre-reclassification runs are being
    compared against a rule that postdates them -- a retroactive judgement,
    not a violation.

    MEASURED PER AGENT, NOT BY ONE GLOBAL TIMESTAMP: a single cutoff would
    also erase the two real buckets, since every one of their rows predates
    today's table edit too. What actually distinguishes them is whether
    THIS agent's declaration changed, checked against `git show HEAD:...`
    rather than the file's own mtime -- `producer.md` was edited again on
    2026-09-09 for a reason unrelated to its `model:` line (still `fable`
    both before and after), and a bare mtime comparison would have misread
    that edit as a reclassification it was not."""
    out = {}
    for name, cur in decl.items():
        committed = _committed_model(repo, name)
        if committed is None or committed == cur:
            out[name] = None
            continue
        f = pathlib.Path(repo) / ".claude" / "agents" / (name + ".md")
        try:
            out[name] = f.stat().st_mtime
        except OSError:
            out[name] = None
    return out


def _epoch(s):
    """One ISO8601 UTC stamp -> epoch seconds, or None. Mirrors
    `ledger/verify.py`'s `_cadence_epoch` in shape (same project, same
    contract: a bare `Z` offset, UTC assumed), kept as a second small
    reader rather than an import for the same reason `_declared_models`
    is its own reader and not a call into `ledger/verify.py`."""
    s = (s or "").strip()
    if not s:
        return None
    if s.endswith(("Z", "z")):
        s = s[:-1] + "+00:00"
    try:
        return datetime.datetime.fromisoformat(s).timestamp()
    except ValueError:
        return None


def routing_drift(repo=None):
    """DECLARED (what the definition asks for, TODAY) versus RAN (the LAST
    SubagentStop snapshot per `agentId`), joined on that column.

    THREE TRAPS MEASURED AND NAMED, each asserted against in the selftest
    so none can return silently:

      LAST-WINS, NEVER SUMMED. `agent-turns.tsv` writes one row per
      SubagentStop, and a spawn nudged past `maxTurns` writes SEVERAL rows
      for the SAME agentId with climbing turn counts (45, 68, 83, 105, 122,
      162 was a real sequence). Summed, that inflates one spawn's turns
      sixfold and the whole file's turns by roughly 2000 of 10407. This
      keeps only the LAST row written for each agentId (`read_log`'s own
      file order, which is chronological) and nothing else.

      NO DECLARATION, NO DISAGREEMENT. `general-purpose` and any other
      built-in `agent_type` with no `.claude/agents/<type>.md` on disk has
      nothing to compare against, and is counted in its OWN bucket, never
      as a violation (rule 3b: a fact this reader cannot judge is not the
      same fact as one it judged clean).

      PRE-RULING, NOT A VIOLATION. A row whose `when` predates its agent's
      OWN `_ruling_cutovers` entry is compliance with the rule as it THEN
      stood, not a disagreement with the rule as it stands now, and is
      counted in `preRuling` instead (see `_ruling_cutovers`'s own
      docstring for why this is per-agent and not one global timestamp,
      and why `preRuling` IS NOT ZERO AND NEVER WILL BE: the ruling
      reclassified nine definitions on the day it landed, so every run
      before that day was judged by a different table, permanently, and
      folding those rows back into the violation count the day this gap
      is "fixed" would be the exact fault this bucket exists to prevent).

    A FIRST DRAFT OF THIS FUNCTION MISSED THE THIRD TRAP and reported 37 of
    163 agents where the honest number was 24 of 163: it compared every
    historical row against TODAY's declaration with no notion that the
    declaration itself had a start date, so `planner`, `content-wrangler`
    and `world-designer`'s pre-reclassification opus runs read as
    violations of a rule that did not exist yet. Caught the same day by
    the director reading this function's own output against a hand tally
    that had excluded them correctly by knowing, by hand, which roles had
    just changed.

    Returns a dict, or `{"rows": None}` when the turns log could not be
    read at all."""
    base = pathlib.Path(repo) if repo else REPO
    decl = _declared_models(base)
    cutovers = _ruling_cutovers(base, decl)
    rows, _short, _unmeasured = read_log(log_path(base))
    if rows is None:
        return {"rows": None}
    last = {}
    for r in rows:
        if r.get("agentId") and r["agentId"] != "unknown":
            last[r["agentId"]] = r        # LAST occurrence wins: file order
    no_decl = []
    agreements = 0
    pre_ruling_rows = []
    pairs = {}                             # (declared, ran) -> [row, ...]
    for r in last.values():
        agent = r["agent"].strip().lower()
        ran = r["tier"].split("+")[0]             # strip a +mixed suffix
        d = decl.get(agent)
        if d is None:
            no_decl.append(agent)
            continue
        cutover = cutovers.get(agent)
        if cutover is not None:
            e = _epoch(r["when"])
            if e is None or e < cutover:
                # UNDATEABLE COUNTS AS PRE-RULING TOO: a row this reader
                # cannot place in time cannot be shown to postdate the
                # cutover either, and the safe direction (rule 5b) is the
                # one that never inflates a violation count.
                pre_ruling_rows.append(r)
                continue
        if d == ran:
            agreements += 1
            continue
        pairs.setdefault((d, ran), []).append(r)
    buckets = []
    disagree_agents = disagree_turns = 0
    for (d, ran), entries in pairs.items():
        n = len(entries)
        turns = sum(r["turns"] for r in entries)
        whens = sorted(r["when"] for r in entries)
        disagree_agents += n
        disagree_turns += turns
        buckets.append({"declared": d, "ran": ran, "agents": n,
                        "turns": turns, "whenMin": whens[0],
                        "whenMax": whens[-1]})
    buckets.sort(key=lambda b: -b["agents"])
    total_turns = sum(r["turns"] for r in last.values())
    return {"rows": True, "distinct": len(last), "agreements": agreements,
            "noDeclaration": len(no_decl),
            "noDeclarationNames": sorted(set(no_decl)),
            "preRuling": len(pre_ruling_rows),
            "preRulingTurns": sum(r["turns"] for r in pre_ruling_rows),
            "buckets": buckets, "disagreeAgents": disagree_agents,
            "disagreeTurns": disagree_turns, "totalTurns": total_turns}


def report_routing_drift(d):
    """The printed form of `routing_drift()`'s dict. Every number says what
    it is a statistic OF (rule: instruments.md), and the three that could
    be mistaken for each other -- violations, preRuling, noDeclaration --
    print as three separate counts so none can stand in for another (the
    director's own framing, 2026-09-10)."""
    if d.get("rows") is None:
        print("spawn-cost --routing-drift: %s (no turns log at %s)"
              % (NOTHING_MEASURED, log_path()))
        return 2
    print("spawn-cost --routing-drift: declared (today's .claude/agents/*.md) "
         "vs ran (last SubagentStop snapshot), joined on agentId")
    print("  distinct agentId(s) in the turns log, last-wins per id: %d"
          % d["distinct"])
    print("  agreements (declared == ran): %d" % d["agreements"])
    print("  preRuling=%d (%d turns): rows that predate the ruling for "
          "THEIR agent, compliance with the rule as it then stood, never a "
          "violation. NOT ZERO AND NEVER WILL BE: the 2026-09-10 ruling "
          "reclassified nine definitions the day it landed, so every run "
          "before that day was judged by a different table, permanently -- "
          "folding these rows back into the violation count would be the "
          "exact fault this bucket exists to prevent."
          % (d["preRuling"], d["preRulingTurns"]))
    print("  noDeclaration=%d excluded from the numerator (no .claude/"
          "agents/<type>.md on disk, so nothing to disagree with): %s"
          % (d["noDeclaration"],
             cap(d["noDeclarationNames"], keep=3) if d["noDeclarationNames"]
             else "none"))
    # DIRECTION DECIDES THE WORD, and the ruling is explicit about which
    # direction it restricts: "a spawn cannot override it upward without a
    # written reason". Downward is permitted and needs no reason. So a row that
    # ran BELOW its declared tier is not a violation of anything; it is a
    # SILENT DEMOTION, which matters for a different reason (a director
    # declared fable that ran opus was not the model the ruling asks for) and
    # must not be counted as rule-breaking. Only an upward run with no
    # resolving reason breaks the ruling as written.
    RANK = {"haiku": 0, "sonnet": 1, "opus": 2, "fable": 3}
    up, down = [], []
    for b in d["buckets"]:
        r_dec, r_ran = RANK.get(b["declared"], -1), RANK.get(b["ran"], -1)
        (up if r_ran > r_dec else down).append(b)
    if not d["buckets"]:
        print("  0 disagreement(s) of %d agent(s) examined" % d["distinct"])
    for b in down:
        print("  SILENT DEMOTION declared %s, ran %s (DOWNWARD, permitted "
              "without a reason): %d agent(s), %d turns, %s..%s"
              % (b["declared"], b["ran"], b["agents"], b["turns"],
                 b["whenMin"], b["whenMax"]))
    for b in up:
        print("  VIOLATION declared %s, ran %s (UPWARD, needs a resolving "
              "reason): %d agent(s), %d turns, %s..%s"
              % (b["declared"], b["ran"], b["agents"], b["turns"],
                 b["whenMin"], b["whenMax"]))
    print("  upwardWithoutReason=%d of %d bucket(s), which is what the ruling "
          "forbids; downwardUnrecorded=%d, which it permits"
          % (len(up), len(d["buckets"]), len(down)))
    print("  declared-versus-ran disagreements after the ruling, BOTH "
          "DIRECTIONS: %d of %d agent(s) (%.0f%%), "
          "%d of %d turn(s) (%.0f%%)"
          % (d["disagreeAgents"], d["distinct"],
             100.0 * d["disagreeAgents"] / d["distinct"] if d["distinct"] else 0,
             d["disagreeTurns"], d["totalTurns"],
             100.0 * d["disagreeTurns"] / d["totalTurns"]
             if d["totalTurns"] else 0))
    return 0


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
    ap.add_argument("--routing-drift", action="store_true",
                    help="declared (definition) vs ran (turns log), joined "
                         "on agentId -- see routing_drift()")
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
    if args.routing_drift:
        return report_routing_drift(routing_drift())
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
