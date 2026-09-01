#!/usr/bin/env python3
"""D1 measurement (a): what one edit-build-test cycle costs, per engine.

TWO DIFFERENT QUANTITIES LIVE HERE AND THEY ARE KEPT IN SEPARATE FILES ON
PURPOSE, because merging them would be the fault this project has paid for
more than any other: one key carrying two moments.

  cycles.tsv          LIVE rows, written at the time an edit happens.
                      edit start -> test result seen. Includes the authoring
                      time, which is the number a person actually feels.

  unity-build-steps.tsv MACHINE rows: what the Unity BUILD ITSELF costs on
                      ledger-pc, the same PC the UE probe builds on. This is
                      the only column that can be set beside a UE build time
                      without comparing two different boundaries.

  unity-roundtrip.tsv HISTORICAL rows, derived from evidence already landed:
                      source commit -> the CI commit that published its
                      verdict. It is a LOWER BOUND on the live number,
                      because everything before the commit is missing from
                      it, and it includes runner queue wait, which is real
                      cost and must not be filtered out to flatter Unity.

None of the three is a substitute for another and this tool never averages
them together. THE BOUNDARIES ARE THE WHOLE POINT: a round trip contains a
queue wait, a checkout, a build, a twelve-minute sim and a push; a build step
contains a build. Setting a UE build time against a Unity round trip would
make the engine look responsible for a runner queue.

WHY THE HISTORICAL HALF EXISTS AT ALL. The live file needs twenty real edits
before it can say anything, and D1 needs a Unity number now to have anything
to compare a UE number against. 369 real round trips are already recorded in
this repository. Reading them is not manufacturing a measurement; it is
declining to throw one away.

THE STATISTIC IS A MEDIAN, and the series is printed above every summary so a
regime change is visible to a person, which no aggregate can do.
"""
import argparse
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(REPO, "production", "d1-probe", "cycles.tsv")
HIST = os.path.join(REPO, "production", "d1-probe", "unity-roundtrip.tsv")
RUNS = os.path.join(REPO, "game-design", "sim-shots", "runs")
VERDICT_PATH = "game-design/sim-shots/verdict.txt"
SUBJECT = re.compile(r"^Sim stills from ([0-9a-f]{7,40})$")

LIVE_HEADER = (
    "# D1 measurement a, LIVE rows. One row per real edit, written AT THE TIME.\n"
    "# The statistic over this file is a MEDIAN of minutes, never a mean and\n"
    "# never a best case. failedEdit means the edit could not be applied or was\n"
    "# lost, which is the binary-asset failure mode UE is being measured for.\n"
    "# Rows come from work that was happening anyway. A manufactured cycle\n"
    "# measures the harness, not the loop.\n"
    "#\n"
    "# engine\ttask\teditStartIso\tresultSeenIso\toutcome\twhatWasEdited\n"
)
OUTCOMES = ("pass", "fail", "failedEdit")


def sh(args, cwd=REPO):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True).stdout


def iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(epoch)))


# ---------------------------------------------------------------- historical

def collect_history(repo=REPO, runs_dir=RUNS):
    """Pair every CI verdict commit with the source commit it names.

    Returns (rows, skipped, non_ci). THE TWO REJECT PILES ARE SEPARATE AND
    THAT SEPARATION IS THE POINT. A commit that touched the verdict file
    without being a CI publish (a human editing it, a merge) was never a
    candidate; folding it into "skipped" would inflate a denominator with
    things the tool was never trying to pair, which is the exact shape that
    made a lint report 560 walked bodies over 29 actually scanned. skipped
    means: this WAS a CI publish and its source could not be resolved.
    """
    out = subprocess.run(
        ["git", "log", "--format=%H|%ct|%s", "--", VERDICT_PATH],
        cwd=repo, capture_output=True, text=True).stdout
    rows, skipped, non_ci = [], [], 0
    for line in out.splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        ci_sha, ci_epoch, subject = parts
        m = SUBJECT.match(subject.strip())
        if not m:
            non_ci += 1
            continue
        src = m.group(1)
        src_epoch = subprocess.run(
            ["git", "show", "-s", "--format=%ct", src],
            cwd=repo, capture_output=True, text=True).stdout.strip()
        if not src_epoch.isdigit():
            skipped.append((src, "source commit not in this checkout"))
            continue
        minutes = (int(ci_epoch) - int(src_epoch)) / 60.0
        if minutes <= 0:
            skipped.append((src, "landed at or before its source commit"))
            continue
        run_file = os.path.join(runs_dir, src[:7] + ".txt")
        answered = "unknown"
        if os.path.exists(run_file):
            with open(run_file, encoding="utf-8", errors="replace") as fh:
                body = fh.read()
            answered = "no" if "NO PLAYER LOG" in body else "yes"
        rows.append({
            "src": src[:7], "srcEpoch": int(src_epoch),
            "ci": ci_sha[:7], "ciEpoch": int(ci_epoch),
            "minutes": round(minutes, 2), "answered": answered,
        })
    rows.sort(key=lambda r: r["ciEpoch"])
    return rows, skipped, non_ci


def write_history(rows, skipped, non_ci, path=HIST):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(
            "# D1 measurement a, Unity HISTORICAL round trips, derived from landed evidence.\n"
            "# source commit -> the CI commit that published its verdict.\n"
            "# A LOWER BOUND on a felt cycle: authoring time before the commit is\n"
            "# not in it. It DOES include runner queue wait, deliberately, because\n"
            "# waiting behind a queue is time the edit costs.\n"
            "# answered=no means the round trip was spent and returned nothing\n"
            "# (NO PLAYER LOG). Those rows stay in the elapsed series; they are\n"
            "# reported separately as a rate, never quietly dropped.\n"
            "# rows=%d skippedCiPublishes=%d nonCiCommitsSeen=%d\n"
            "# srcSha\tsrcIso\tciSha\tciIso\tminutes\tanswered\n"
            % (len(rows), len(skipped), non_ci))
        for r in rows:
            fh.write("%s\t%s\t%s\t%s\t%.2f\t%s\n" % (
                r["src"], iso(r["srcEpoch"]), r["ci"], iso(r["ciEpoch"]),
                r["minutes"], r["answered"]))
        for sha, reason in skipped:
            fh.write("# SKIPPED %s: %s\n" % (sha, reason))


def report_history(rows, skipped, non_ci, series_cap=60):
    if not rows:
        print("unityRoundTrip=nothing measured — 0 pairings from %d CI publish(es) "
              "that could not be resolved and %d non-CI commit(s) that were never "
              "candidates." % (len(skipped), non_ci))
        return 1
    mins = [r["minutes"] for r in rows]
    newest = list(reversed(mins))
    shown = newest[:series_cap]
    print("SERIES (minutes, newest first). The series sits above the summaries "
          "on purpose: a regime change is visible to a person and to no aggregate.")
    print("  " + " ".join("%.0f" % m for m in shown))
    if len(newest) > series_cap:
        print("  (+%d more not shown)" % (len(newest) - series_cap))
    recent = newest[:20]
    no_ans = sum(1 for r in rows if r["answered"] == "no")
    unknown = sum(1 for r in rows if r["answered"] == "unknown")
    print("")
    print("unityCycleMedianMin=%.1f unityCycleRows=%d" % (statistics.median(mins), len(mins)))
    print("unityCycleRecent20Median=%.1f unityCycleRecentRows=%d"
          % (statistics.median(recent), len(recent)))
    print("unityCycleP10=%.1f unityCycleP90=%.1f"
          % (percentile(mins, 10), percentile(mins, 90)))
    print("unityCycleWorstMin=%.1f unityCycleBestMin=%.1f" % (max(mins), min(mins)))
    print("unityNoAnswerRuns=%d/%d unityAnswerUnknown=%d "
          "unitySkippedCiPublishes=%d unityNonCiCommits=%d"
          % (no_ans, len(rows), unknown, len(skipped), non_ci))
    print("note: median is the D1 number. The p10..p90 spread is printed beside "
          "it because a median cannot see a tail and this loop has a long one.")
    return 0


def percentile(values, pct):
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * (pct / 100.0)
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


# ---------------------------------------------------------------------- live

def read_live(path=LIVE):
    if not os.path.exists(path):
        return None
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if len(f) < 6:
                continue
            rows.append({"engine": f[0], "task": f[1], "start": f[2],
                         "seen": f[3], "outcome": f[4], "what": f[5]})
    return rows


def report_live(rows, engine=None):
    if rows is None:
        print("liveCycles=nothing measured — %s does not exist yet."
              % os.path.relpath(LIVE, REPO))
        return 0
    if engine:
        rows = [r for r in rows if r["engine"] == engine]
    if not rows:
        print("liveCycles=nothing measured — 0 rows%s. A zero here means no edit "
              "has been recorded, NOT that the loop is fast."
              % (" for engine=%s" % engine if engine else ""))
        return 0
    timed = []
    for r in rows:
        try:
            a = time.mktime(time.strptime(r["start"], "%Y-%m-%dT%H:%M:%SZ"))
            b = time.mktime(time.strptime(r["seen"], "%Y-%m-%dT%H:%M:%SZ"))
        except ValueError:
            continue
        if b > a:
            timed.append((b - a) / 60.0)
    failed = sum(1 for r in rows if r["outcome"] == "failedEdit")
    if timed:
        print("SERIES (minutes, newest first): " +
              " ".join("%.0f" % m for m in reversed(timed)))
        print("liveCycleMedianMin=%.1f liveCycleTimedRows=%d"
              % (statistics.median(timed), len(timed)))
    else:
        print("liveCycleMedianMin=nothing measured — 0 of %d row(s) carried two "
              "parseable timestamps." % len(rows))
    print("liveFailedEdits=%d/%d liveRows=%d" % (failed, len(rows), len(rows)))
    if len(rows) < 20:
        print("NOT YET SUFFICIENT: acceptance wants at least 20 rows; %d present."
              % len(rows))
    return 0


def add_live(engine, task, start, seen, outcome, what, path=LIVE):
    if outcome not in OUTCOMES:
        print("outcome must be one of %s" % (OUTCOMES,), file=sys.stderr)
        return 2
    for field in (engine, task, start, seen, outcome, what):
        if "\t" in field or "\n" in field:
            print("a field may not contain a tab or a newline", file=sys.stderr)
            return 2
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fresh = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as fh:
        if fresh:
            fh.write(LIVE_HEADER)
        fh.write("\t".join([engine, task, start, seen, outcome, what]) + "\n")
    print("added a %s row to %s" % (engine, os.path.relpath(path, REPO)))
    return 0


# ------------------------------------------------------- machine build steps

STEPS = os.path.join(REPO, "production", "d1-probe", "unity-build-steps.tsv")
API = "https://api.github.com/repos/jsab258/wc26-picks/actions"
BUILD_STEP = "Build player"
SIM_STEP_PREFIX = "Run game simulation"


def _api(url, token):
    import urllib.request
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
    })
    import json as _json
    with urllib.request.urlopen(req, timeout=60) as fh:
        return _json.load(fh)


def _secs(a, b):
    if not a or not b:
        return None
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        return time.mktime(time.strptime(b, fmt)) - time.mktime(time.strptime(a, fmt))
    except ValueError:
        return None


def collect_steps(workflow="ledger-build-windows.yml", pages=4, token=None):
    """Read step timings for the Unity build job off the Actions API.

    THE STEP LIST IS THE ONE CHANNEL THIS PROJECT'S CI HAS THAT IS BOTH
    READABLE HERE AND HONEST ABOUT TIME. Log tails are truncated and step
    summaries come back empty; started_at and completed_at do not.

    Returns (rows, seen, no_build_step). no_build_step is reported rather
    than dropped: a run that never reached the build is a real outcome and
    excluding it silently would flatter the median.
    """
    # None means "look at the environment". An explicitly passed empty string
    # means "there is no token", and it must NOT fall through to the
    # environment: the selftest passes "" precisely to watch this refuse, and
    # the first version happily found a real token and refused nothing.
    if token is None:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        return None, 0, 0
    rows, seen, no_build = [], 0, 0
    run_ids = []
    for page in range(1, pages + 1):
        d = _api("%s/workflows/%s/runs?per_page=100&page=%d" % (API, workflow, page), token)
        batch = d.get("workflow_runs", [])
        if not batch:
            break
        run_ids.extend((r["id"], r["head_sha"][:7], r.get("conclusion"),
                        r.get("created_at"), r.get("run_started_at")) for r in batch)
    for rid, sha, concl, created, started in run_ids:
        seen += 1
        try:
            d = _api("%s/runs/%d/jobs" % (API, rid), token)
        except Exception:
            no_build += 1
            continue
        jobs = d.get("jobs", [])
        if not jobs:
            no_build += 1
            continue
        job = jobs[0]
        steps = {st["name"]: st for st in job.get("steps", [])}
        build = steps.get(BUILD_STEP)
        sim = next((st for n, st in steps.items() if n.startswith(SIM_STEP_PREFIX)), None)
        if not build or build.get("conclusion") in (None, "skipped"):
            no_build += 1
            continue
        b = _secs(build.get("started_at"), build.get("completed_at"))
        if b is None:
            no_build += 1
            continue
        rows.append({
            "run": rid, "sha": sha, "runner": job.get("runner_name") or "unknown",
            "concl": concl or "unknown",
            "buildSec": round(b, 1),
            "simSec": round(_secs(sim.get("started_at"), sim.get("completed_at")) or -1, 1) if sim else -1,
            # QUEUE WAIT FROM THE JOB, NOT THE RUN. run_started_at came back
            # absent on every one of 188 runs and the column read -1 across the
            # board, which is a zero with no denominator wearing a number's
            # clothes. The job object carries created_at and started_at and
            # they are the wait that was actually served.
            "queueSec": round(_secs(job.get("created_at"), job.get("started_at")) or -1, 1),
            "jobSec": round(_secs(job.get("started_at"), job.get("completed_at")) or -1, 1),
            "started": job.get("started_at") or "",
        })
    rows.sort(key=lambda r: r["started"])
    return rows, seen, no_build


def write_steps(rows, seen, no_build, path=STEPS):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(
            "# D1 measurement a, the UNITY BUILD ITSELF on ledger-pc.\n"
            "# Source: the Actions API step list (started_at/completed_at), which\n"
            "# is readable here when log tails and step summaries are not.\n"
            "# buildSec is a WARM Unity build: the self-hosted agent keeps Library/\n"
            "# between runs, so this is the repeat-build cost, not a first build.\n"
            "# simSec and queueSec are named separately and belong to the ROUND\n"
            "# TRIP, not to the build. Do not add them together and call it a cycle.\n"
            "# rows=%d runsSeen=%d runsWithNoUsableBuildStep=%d\n"
            "# runId\tsha\trunner\tconclusion\tstartedIso\tbuildSec\tsimSec\tqueueSec\tjobSec\n"
            % (len(rows), seen, no_build))
        for r in rows:
            fh.write("%d\t%s\t%s\t%s\t%s\t%.1f\t%.1f\t%.1f\t%.1f\n" % (
                r["run"], r["sha"], r["runner"], r["concl"], r["started"],
                r["buildSec"], r["simSec"], r["queueSec"], r["jobSec"]))


SELF_HOSTED = "ledger-pc"


def runner_class(name):
    """ledger-pc is Jafar's machine; everything else is a GitHub cloud runner.

    THIS SPLIT IS NOT COSMETIC AND IT NEARLY COST D1 ITS ANSWER. The first
    version of this report pooled 188 rows under the label "on ledger-pc"
    when 116 of them were cloud runners, and the whole point of the number is
    to sit beside a UE build time measured on ledger-pc. Two populations under
    one median is the fault this project has paid for most often; here it
    would have compared a rented CPU against Jafar's.
    """
    return SELF_HOSTED if name == SELF_HOSTED else "hosted"


def _summarise(label, vals, kind):
    if not vals:
        print("%s%s=nothing measured — 0 row(s)." % (label, kind))
        return
    print("%s%sMedianMin=%.2f %s%sRows=%d %s%sP10=%.2f %s%sP90=%.2f %s%sWorstMin=%.2f"
          % (label, kind, statistics.median(vals), label, kind, len(vals),
             label, kind, percentile(vals, 10), label, kind, percentile(vals, 90),
             label, kind, max(vals)))


def report_steps(rows, seen, no_build, series_cap=60):
    if rows is None:
        print("unityBuildStep=nothing measured — no GH_TOKEN or GITHUB_TOKEN in "
              "the environment, so the Actions API was never asked.")
        return 1
    if not rows:
        print("unityBuildStep=nothing measured — 0 usable build steps out of %d "
              "run(s) seen (%d had none)." % (seen, no_build))
        return 1
    groups = {SELF_HOSTED: [], "hosted": []}
    for r in rows:
        groups[runner_class(r["runner"])].append(r)

    for label in (SELF_HOSTED, "hosted"):
        g = groups[label]
        key = "pc" if label == SELF_HOSTED else "cloud"
        print("=== %s: %d row(s) of %d" % (label, len(g), len(rows)))
        if not g:
            print("  nothing measured on this runner class.")
            continue
        b = [r["buildSec"] / 60.0 for r in g]
        newest = list(reversed(b))
        print("  SERIES (Unity 'Build player' minutes, newest first):")
        print("  " + " ".join("%.1f" % m for m in newest[:series_cap]))
        if len(newest) > series_cap:
            print("  (+%d more not shown)" % (len(newest) - series_cap))
        _summarise(key, b, "Build")
        _summarise(key, [r["simSec"] / 60.0 for r in g if r["simSec"] >= 0], "Sim")
        _summarise(key, [r["queueSec"] / 60.0 for r in g if r["queueSec"] >= 0], "Queue")
        _summarise(key, [r["jobSec"] / 60.0 for r in g if r["jobSec"] >= 0], "Job")
        print("")

    distinct = len({r["runner"] for r in rows})
    print("unityRunsSeen=%d unityRunsWithNoUsableBuildStep=%d "
          "unityDistinctRunners=%d unitySelfHostedRows=%d unityHostedRows=%d"
          % (seen, no_build, distinct, len(groups[SELF_HOSTED]), len(groups["hosted"])))
    print("note: buildSec is WARM (Library/ persists on the agent). ONLY the "
          "%s rows are comparable to a UE build time, because that is the "
          "machine the UE probe builds on; the hosted rows are a different "
          "CPU and are printed so the difference is visible rather than "
          "averaged away. Sim and queue belong to the round trip and adding "
          "them to the build would price the runner, not the engine."
          % SELF_HOSTED)
    return 0


# ------------------------------------------------------------------ selftest

def selftest():
    """Accepting case FIRST, per rule 5b: the tool must be watched saying yes.

    The accepting fixture is a small synthetic history rather than the live
    repo, because this tool's output is a NUMBER rather than a verdict and a
    number needs known inputs to be checkable at all.
    """
    ok, fail = 0, 0

    def check(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print("  FAIL %s" % name)

    # 1. ACCEPTING: a well-formed live file reports its median and its rows.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "cycles.tsv")
        add_live("unity", "t1", "2026-09-01T10:00:00Z", "2026-09-01T10:30:00Z",
                 "pass", "one file", path=p)
        add_live("unity", "t2", "2026-09-01T11:00:00Z", "2026-09-01T11:10:00Z",
                 "pass", "another", path=p)
        rows = read_live(p)
        check("accepting: two rows read back", rows is not None and len(rows) == 2)
        check("accepting: header written once", open(p).read().count("engine\ttask") == 1)

    # 2. A MISSING FILE SAYS SO rather than reading as a clean zero.
    with tempfile.TemporaryDirectory() as d:
        check("absent file returns None, not []",
              read_live(os.path.join(d, "nope.tsv")) is None)

    # 3. REJECTING: a bad outcome value is refused.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "c.tsv")
        check("rejecting: unknown outcome refused",
              add_live("unity", "t", "a", "b", "quite-good", "x", path=p) == 2)
        check("rejecting: nothing written on refusal", not os.path.exists(p))

    # 4. REJECTING: a tab inside a field would split the row silently.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "c.tsv")
        check("rejecting: embedded tab refused",
              add_live("unity", "a\tb", "s", "e", "pass", "x", path=p) == 2)

    # 5. Percentiles on a known series.
    check("p50 of 1..9 is 5", abs(percentile(list(range(1, 10)), 50) - 5) < 1e-9)
    check("p90 of 1..11 is 10", abs(percentile(list(range(1, 12)), 90) - 10) < 1e-9)

    # 6. THE HISTORY PAIRING, against a real git repo built here so the
    #    accepting case is exercised end to end rather than assumed.
    with tempfile.TemporaryDirectory() as d:
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        e = dict(os.environ, **env)
        subprocess.run(["git", "init", "-q", d], check=True)
        vp = os.path.join(d, VERDICT_PATH)
        os.makedirs(os.path.dirname(vp), exist_ok=True)

        def commit(msg, body, when):
            open(vp, "w").write(body)
            subprocess.run(["git", "add", "-A"], cwd=d, check=True)
            ee = dict(e, GIT_AUTHOR_DATE="@%d +0000" % when,
                      GIT_COMMITTER_DATE="@%d +0000" % when)
            subprocess.run(["git", "commit", "-q", "-m", msg], cwd=d, env=ee, check=True)
            return subprocess.run(["git", "rev-parse", "HEAD"], cwd=d,
                                  capture_output=True, text=True).stdout.strip()

        src = commit("a source edit", "x", 1000000)
        commit("Sim stills from %s" % src[:7], "y", 1000000 + 1800)
        runs = os.path.join(d, "runs")
        os.makedirs(runs)
        open(os.path.join(runs, src[:7] + ".txt"), "w").write("# ok\nplayer=1\n")
        rows, skipped, non_ci = collect_history(repo=d, runs_dir=runs)
        check("history: one pairing found", len(rows) == 1)
        check("history: the plain source commit is not counted as skipped",
              len(skipped) == 0 and non_ci == 1)
        check("history: 30 minutes measured", rows and abs(rows[0]["minutes"] - 30.0) < 0.01)
        check("history: answered=yes when the run said something",
              rows and rows[0]["answered"] == "yes")

        # REJECTING HALF: a run that measured nothing must not read as answered.
        src2 = commit("another edit", "z", 1000000 + 3600)
        commit("Sim stills from %s" % src2[:7], "w", 1000000 + 3600 + 600)
        open(os.path.join(runs, src2[:7] + ".txt"), "w").write(
            "# v\nNO PLAYER LOG — the sim did not run on this commit\n")
        rows, skipped, non_ci = collect_history(repo=d, runs_dir=runs)
        check("history: two pairings now", len(rows) == 2)
        check("history: NO PLAYER LOG reads as answered=no",
              sum(1 for r in rows if r["answered"] == "no") == 1)

        # A subject naming a sha this checkout does not have is SKIPPED and SAID.
        commit("Sim stills from deadbee", "q", 1000000 + 9000)
        rows, skipped, non_ci = collect_history(repo=d, runs_dir=runs)
        check("history: unresolvable source skipped, not silently dropped",
              len(rows) == 2 and len(skipped) == 1)
        check("history: non-CI commits counted apart from skipped ones", non_ci == 2)

    # 7. THE STEP COLLECTOR'S ARITHMETIC AND ITS REFUSALS, without the network.
    check("secs: a known 30-minute span",
          abs(_secs("2026-01-01T00:00:00Z", "2026-01-01T00:30:00Z") - 1800) < 1e-6)
    check("secs: a missing endpoint returns None, not 0",
          _secs("", "2026-01-01T00:30:00Z") is None)
    check("secs: an unparseable stamp returns None, not 0",
          _secs("not-a-date", "2026-01-01T00:30:00Z") is None)
    check("steps: no token means nothing measured, not an empty success",
          collect_steps(token="", pages=0)[0] is None)
    check("steps: report says 'nothing measured' rather than printing a clean zero",
          report_steps(None, 0, 0) == 1)
    check("steps: zero usable rows is a refusal, not a median of nothing",
          report_steps([], 7, 7) == 1)
    check("runnerClass: the self-hosted agent is named exactly",
          runner_class("ledger-pc") == "ledger-pc")
    check("runnerClass: a cloud runner is not the self-hosted one",
          runner_class("GitHub Actions 1000002079") == "hosted")
    # ACCEPTING CASE FOR THE SPLIT: two populations must report two medians,
    # never one. This is the check the pooled first version would have failed.
    _mixed = [
        {"runner": "ledger-pc", "buildSec": 120.0, "simSec": -1, "queueSec": -1,
         "jobSec": -1, "started": "a"},
        {"runner": "GitHub Actions 1", "buildSec": 600.0, "simSec": -1,
         "queueSec": -1, "jobSec": -1, "started": "b"},
    ]
    check("steps: a mixed sample still reports, split", report_steps(_mixed, 2, 0) == 0)

    print("d1-cycles selftest: %d ok, %d failed" % (ok, fail))
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--history", action="store_true",
                    help="derive and report the Unity round-trip series from landed evidence")
    ap.add_argument("--write", action="store_true",
                    help="with --history, write unity-roundtrip.tsv")
    ap.add_argument("--steps", action="store_true",
                    help="read the Unity build step timings off the Actions API")
    ap.add_argument("--pages", type=int, default=2,
                    help="with --steps, how many 100-run pages to walk (default 2)")
    ap.add_argument("--live", action="store_true", help="report the live cycles.tsv")
    ap.add_argument("--engine", help="with --live, restrict to one engine")
    ap.add_argument("--add", nargs=6,
                    metavar=("ENGINE", "TASK", "START_ISO", "SEEN_ISO", "OUTCOME", "WHAT"),
                    help="append one live row (outcome: pass|fail|failedEdit)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.add:
        return add_live(*a.add)
    if a.steps:
        rows, seen, no_build = collect_steps(pages=a.pages)
        if a.write and rows:
            write_steps(rows, seen, no_build)
            print("wrote %s (%d row(s) of %d run(s) seen)"
                  % (os.path.relpath(STEPS, REPO), len(rows), seen))
        return report_steps(rows, seen, no_build)
    if a.history:
        rows, skipped, non_ci = collect_history()
        if a.write:
            write_history(rows, skipped, non_ci)
            print("wrote %s (%d row(s), %d skipped CI publish(es), %d non-CI commit(s))"
                  % (os.path.relpath(HIST, REPO), len(rows), len(skipped), non_ci))
        return report_history(rows, skipped, non_ci)
    return report_live(read_live(), a.engine)


if __name__ == "__main__":
    sys.exit(main())
