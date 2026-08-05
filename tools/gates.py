#!/usr/bin/env python3
"""Which gates are failing, across every verdict that has landed.

    python3 tools/gates.py          # the last 12 runs, newest commit first
    python3 tools/gates.py 30       # the last 30

WHY THIS EXISTS.

`landed.py` answers "did this commit come back". It does not answer the
question that actually matters at the end of a night: **of the runs that came
back, which ones are red and what is red about them.**

Six builds ran concurrently on 3 August. Reading six verdicts by hand means six
greps for `FAILING GATES`, in commit order worked out from a separate `git log`,
and the report rule this serves — *"check what LANDED, not what reported
success"* and *"lead with anything visibly broken"* — has to be obeyed at the
exact hour when doing six of anything by hand gets skipped.

It orders by COMMIT, not by file time. `verdict.txt` is the last run to LAND and
not the newest commit, and the same is true of the runs directory: a build
dispatched earlier on an older commit routinely finishes second. Sorting by
mtime would put a stale answer at the top of the list, which is the mistake this
repo keeps paying for in a new place each time.

It reports the gate NAMES verbatim, because they carry their own numbers. That
is deliberate in `SimDirector` — a gate that can only say its own name costs a
twenty-minute round trip to learn why — and it means this tool needs no
knowledge of what any gate means.

Exit status is 0 whatever it finds. A red run is a thing to read, not a thing to
fail a commit on: the commit that FIXES a red run would be blocked by it.
"""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS = ROOT / "game-design" / "sim-shots" / "runs"

# What the job writes when the build produced no player. Quoted, not
# paraphrased — see tools/verdict-keys.py, which matches the same marker.
NO_SIM = "NO PLAYER LOG"

FAILING = re.compile(r"FAILING GATES:\s*(.+)")
PASS = re.compile(r"\bpass=(True|False)\b")


def read(path):
    # errors="replace": these are written by a Windows runner and carry bytes
    # this side does not assume. A tool that throws on its own input is a tool
    # nobody runs twice.
    return path.read_text(encoding="utf-8", errors="replace")


def split_gates(line):
    """Split a FAILING GATES list on commas that separate gates.

    Gate names embed their own numbers in brackets — `law[denounced=2 marks=2]`
    — and those brackets contain commas. Splitting naively cuts a gate in half
    and reports two gates that do not exist, which is worse than not splitting
    at all.
    """
    out, depth, cur = [], 0, []
    for ch in line:
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth -= 1
        if ch == "," and depth <= 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur).strip())
    return [g for g in out if g]


def ordered_runs():
    """Every kept run, NEWEST COMMIT FIRST.

    `glob` returns files in whatever order the filesystem gives, and sorting
    those by name sorts by sha, which is sorting by nothing. Commit order is
    the only order in which "how long ago" means anything, so it is built once
    here and both readers use it.

    Runs whose commit is older than the log window are appended at the end,
    oldest-ish, rather than dropped — a run that fell off the log is still
    evidence about the past, and silently discarding it would make the counts
    disagree with the runs directory for no visible reason.
    """
    have = {p.stem: p for p in RUNS.glob("*.txt")}
    log = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h", "-400"],
                         capture_output=True, text=True).stdout.split()
    out, seen = [], set()
    for sha in log:
        if sha in have:
            out.append((sha, have[sha]))
            seen.add(sha)
    out.extend((s, p) for s, p in sorted(have.items()) if s not in seen)
    # A BUILD THAT NEVER RAN A SIM IS NOT A RUN, and counting it as one makes
    # every gate look quieter than it is.
    #
    # Five builds on 4 August produced an eleven-line verdict — two on a Unity
    # licence seat, three on a compile error — and each one says so in words.
    # They have no gates in them, so they can never contribute a failure, and
    # leaving them in pushes "last N runs ago" up by one apiece and dilutes
    # every rate in the table. The first reading after those five showed the
    # live section EMPTY, which is a pleasant thing to be told by an instrument
    # that had just been handed five blanks.
    #
    # Exactly the repair made to `verdict-keys` an hour earlier, in this same
    # session, for the same reason — and rule 1's corollary says to grep for the
    # claim you have just falsified elsewhere, which I did not.
    return [(s, p) for s, p in out if NO_SIM not in read(p)]


NUMBER = r"[-+]?\d+(?:\.\d+)?"


def series(key):
    """Every landed value of one verdict number, newest run first.

    WHY, AND IT IS THE MOST EXPENSIVE HABIT IN THIS PROJECT WRITTEN AS A
    COMMAND. `queue.md` told me to read the incoming crowd build against
    "`confabs` was 74". 74 is the single highest reading in the project's
    history. The actual distribution over 43 runs of the current test is
    min 29, quartiles 43 / 49 / 60 — so the baseline is 49, and any reading
    in the low forties would have been reported as conversation collapsing
    under the crowd change, with a fix then applied to working code.

    A peak standing in for a description. CLAUDE.md names that fault twice
    and neither warning stopped it, because the failure is not forgetting —
    it is that getting the series means a loop over a hundred verdicts and
    quoting the one number already on the page does not. So this is the loop.

    IT PRINTS THE WHOLE SERIES, not just the summary, and that is the part
    that matters rather than the quartiles. The all-time median of `confabs`
    is 23, which is a number describing nothing: the older runs were a
    different test — a flat road rule before junctions — reading 1 to 13. No
    statistic can see that break and every statistic is ruined by it. A
    reader looking at the series sees it immediately.
    """
    runs = ordered_runs()
    pat = re.compile(r"\b" + re.escape(key) + r"=(" + NUMBER + r")\b")
    hits = []
    for sha, path in runs:
        m = pat.search(read(path))
        if m:
            hits.append((sha, float(m.group(1))))

    if not hits:
        print(f"gates --series {key}: no landed run carries that name.")
        print(f"  {len(runs)} runs read. Check the spelling against a verdict, or the")
        print("  number may never have reached the verdict — see tools/verdict-reach.py.")
        return 1

    xs = [v for _, v in hits]
    print(f"{key}: {len(xs)} landed run(s), newest first")
    print()
    print("  " + "  ".join(f"{v:g}" for v in xs))
    print()
    if len(xs) < 5:
        print(f"  n={len(xs)} — TOO FEW TO SUMMARISE. The values above are the evidence;")
        print("  a median of four things is not a baseline. Quote the runs, not a statistic.")
        return 0

    import statistics
    # THE RECENT WINDOW LEADS, and the all-time line is the one carrying the
    # warning — the first version printed them the other way round, which puts
    # the most misusable number on the most-read line. Ten is a display width,
    # not a claim about where a regime starts; the series above is the evidence
    # and this is a convenience over it.
    recent = xs[:10]
    print(f"  newest {xs[0]:g}")
    print(f"  last {len(recent)}:  min {min(recent):g}   median "
          f"{statistics.median(recent):g}   max {max(recent):g}"
          f"      <- compare a landing run against THIS")
    srt = sorted(xs)
    q = statistics.quantiles(srt, n=4)
    print(f"  all {len(xs)}:  min {srt[0]:g}   quartiles {q[0]:g} / "
          f"{statistics.median(srt):g} / {q[2]:g}   max {srt[-1]:g}")
    print()
    print("  READ THE SERIES BEFORE EITHER SUMMARY, and distrust the all-runs line.")
    print("  If the old values sit in a different band from the new ones the test")
    print("  itself changed, and an average across that break describes nothing.")
    print("  `confabs` is the live example: 1-13 under the old flat-road rule and")
    print("  29-74 under the junction one, for an all-time median belonging to")
    print("  neither. No statistic can see that break. The series makes it obvious.")
    return 0


KEY_VALUE = r"(?<![\w])([A-Za-z][\w]*)=([^\s\[\(]+)"

# Values that mean "this did not happen". A key stuck on one of these across
# every run is the shape worth reading; a key stuck on a number that is not one
# of these is usually a constant somebody printed, which is noise here.
DID_NOT_HAPPEN = {"0", "0.0", "0.00", "0.000", "0.0000",
                  "False", "None", "none", "-1"}


# ZEROS SOMEBODY HAS ALREADY READ AND UNDERSTOOD, with a one-line reason and
# a pointer to where the real one lives.
#
# WHY THIS EXISTS. `--constant` printed sixty-one keys and its own docstring
# says telling a fault counter from an unentered branch "needs to know what the
# number is FOR, which is a person's job". Fine — but a person did that job for
# several of them, wrote the reasoning into the code where it belongs, and the
# tool went on printing all sixty-one every time. A warning nobody can clear
# stops being a warning, and the sixty-second entry would have arrived as one
# more line in a block already being scrolled past.
#
# THE REASON HERE IS DELIBERATELY ONE LINE. The real account is a paragraph in
# the file that owns the number, because that is where somebody chasing it will
# be standing; duplicating it here would be one idea with two implementations
# and this file would be the copy that decays. What this buys is the
# distinction between "nobody has looked" and "somebody looked".
#
# AND AN EXPLAINED KEY THAT STARTS MOVING IS REPORTED, because a reason is a
# claim and claims decay — the reach ledger has now had three reasons go stale
# describing work that had already been done.
EXPLAINED_ZEROS = {
    "soundsOffered": "no audio device on the runner; read simAudible first",
    "soundsAdmitted": "no audio device on the runner; read simAudible first",
    "soundsDropped": "no audio device on the runner; read simAudible first",
    "soundsNoClip": "no audio device on the runner; read simAudible first",
    "soundsStolen": "no audio device on the runner; read simAudible first",
    "soundsPeak": "no audio device on the runner; read simAudible first",
    "soundsPeakBus": "no audio device on the runner; read simAudible first",
    "speechPlayed": "no audio device, and the voice bank does not exist yet",
    "speechNoAudio": "no audio device on the runner; read simAudible first",
    "simAudible": "the runner has no audio device — this is the key that says so",
    "windowsShopLit": "last-wins, written after midnight when every shop is "
                      "shut by design; read windowsShopLitAtShot",
    "walkersPrimitive": "last-wins over a once-a-second pass; read "
                        "walkersPrimitiveEver",
    "huddleTalking": "measured 4 Aug and it is the FINDING — the mob is not a "
                     "conversation",
    "huddleDetour": "measured 4 Aug and it is the FINDING — the mob is not an "
                    "obstacle",
    "huddleWaiting": "measured 4 Aug and it is the FINDING — the mob is not a "
                     "host waiting",
    "deedWaitedDays": "zero is the goal: the escort is recruited near, so the "
                      "wait never fires",
    "fontless": "a fault counter doing its job since 17.9 shipped",
    "errors": "a fault counter doing its job",
    "idLeaks": "a fault counter doing its job",
    "blankLabels": "a fault counter doing its job",
    "panelsBad": "a fault counter doing its job",
    "contrastFailing": "a fault counter; read contrastChecked beside it",
    "offRoad": "a fault counter doing its job — no vehicle leaves the tarmac",
    "stemsUnbound": "a fault counter doing its job",
    "unbound": "a fault counter doing its job",
    "textNoText": "a fault counter doing its job",
    "bodyGrantsFailed": "a fault counter doing its job",
    "walkerBodiesFailed": "a fault counter doing its job",
    "playerPrimitive": "false is correct — the player is not a capsule",
    "primitive": "false is correct — see playerPrimitive",
}


def constant(minimum_runs=20):
    """READINGS WHOSE SUBJECT HAS NEVER OCCURRED, across every kept run.

    THE MIRROR OF `--flaky`, AND IT FOUND SOMETHING ON ITS FIRST RUN.
    `--flaky` asks which gates have ever gone red, because a gate that fails
    rarely for an unnamed reason teaches everyone to read red as noise. This
    asks the opposite question: which numbers have NEVER been anything but
    zero.

    `inquiry=None` in a hundred and thirty-one runs — every verdict this
    project has kept. So the detective has never once opened an investigation
    into the player, and everything gated on that stage has never been
    exercised: the paper naming you (`pressNamed=0`), the redirect having
    something to relieve (`redirectRelief=0.00`), and whatever else reads it.
    Not one verdict shows this. It is only visible across all of them.

    MOST OF WHAT THIS PRINTS IS HEALTHY AND THAT IS THE POINT. `errors=0`,
    `idLeaks=0`, `blankLabels=0`, `panelsBad=0` are fault counters and a
    permanent zero is them working. The tool cannot tell those from a branch
    nobody has entered, and it does not try — that judgement needs to know what
    the number is FOR, which is a person's job. What it removes is the part
    nobody can do by hand: noticing that a number never moved.

    Rule 5b's corollary is about gates needing a run in which the thing they
    assert can happen. This is the same corollary aimed at readings, where it
    is worse: a gate that never fires at least stays green and honest, while a
    reading whose subject never occurs prints a number that looks like
    coverage.
    """
    runs = ordered_runs()
    if len(runs) < minimum_runs:
        print(f"gates --constant: only {len(runs)} measuring run(s) kept; "
              f"a key that has not varied over fewer than {minimum_runs} has "
              f"not been given a chance to. Nothing to say yet.")
        return 0
    seen = {}
    for _, path in runs:
        for k, v in re.findall(KEY_VALUE, read(path)):
            seen.setdefault(k, set()).add(v)
    stuck = sorted(k for k, vs in seen.items()
                   if len(vs) == 1 and next(iter(vs)) in DID_NOT_HAPPEN)
    known = EXPLAINED_ZEROS
    fresh = [k for k in stuck if k not in known]
    settled = [k for k in stuck if k in known]
    print(f"gates --constant: {len(runs)} runs, {len(seen)} keys, "
          f"{len(stuck)} that have never been anything but zero/false/none — "
          f"{len(fresh)} unexamined, {len(settled)} already explained.")
    print("Read each one and ask which it is: a fault counter doing its job, "
          "or a branch nothing has ever entered.\n")
    for k in fresh:
        print(f"  {k}={next(iter(seen[k]))}")
    if settled:
        print(f"\n  ---- {len(settled)} already read and understood; "
              f"the reason is in the code, not here ----")
        for k in settled:
            print(f"  ({k}={next(iter(seen[k]))} — {known[k]})")
    # A KEY THAT LEAVES THE LIST IS A REASON THAT HAS EXPIRED. If somebody
    # explains a zero and it later starts moving, the explanation is stale and
    # nobody would ever be told — the same decay the reach ledger's reasons
    # have, which this project has now been bitten by three times.
    gone = sorted(k for k in known if k not in stuck)
    if gone:
        print(f"\n  ---- {len(gone)} explained key(s) NO LONGER STUCK — the "
              f"reason has expired and wants deleting ----")
        for k in gone:
            print(f"  {k} moved: {known[k]}")
    return 0


def flaky():
    """Which gates have gone red, how often, and HOW LONG AGO.

    WHY. Four gates went red on one run each while passing on either side, and
    each time the first question was "is this new, or has it done this before?"
    — answered three separate times by hand-grepping the runs directory. A
    question asked three times in one night is a command.

    It matters more than it sounds. A gate that fails rarely for a reason
    nobody has named is worse than one that fails always: it trains everybody
    to read red as noise, and that is how a real failure walks through.

    THE FIRST VERSION HAD NO TIME AXIS AND THAT MADE IT LIE. It reported
    `bodies 6/64, 9.4%` beside `claims 22/64` and I wrote "bodies is the
    biggest untouched one" onto the queue off the back of it. All six `bodies`
    failures are from a hundred-minute window on 3 August — the runs during
    which the upside-down player was being diagnosed and repaired — and every
    one of the forty-odd runs since has passed it. It is not the most neglected
    gate in the project; it is the most thoroughly fixed thing in it.

    A rate with no recency is a claim about the present made entirely out of
    the past, and it pointed me at a solved problem while `claims` was failing
    on the newest run in the directory. So every gate now carries how many runs
    have passed since it last went red, and the ones that have gone quiet say
    so in words rather than being ranked as though they were live.

    Reports rates and recency, not verdicts. One in sixty may be a world state
    the probe does not guarantee or a real bug that needs sixty runs to show —
    this cannot tell those apart and does not pretend to.
    """
    if not RUNS.is_dir():
        print("gates: no runs directory yet")
        return 0
    runs = ordered_runs()
    if not runs:
        print("gates: no run files yet")
        return 0

    total = len(runs)
    counts, newest, ago = {}, {}, {}
    for i, (sha, path) in enumerate(runs):        # i == runs since, newest first
        m = FAILING.search(read(path))
        if not m:
            continue
        for g in split_gates(m.group(1)):
            name = g.split("[", 1)[0].strip()
            counts[name] = counts.get(name, 0) + 1
            if name not in newest:
                newest[name] = sha
                ago[name] = i

    if not counts:
        print(f"gates: no failures in {total} kept run(s)")
        return 0

    # QUIET IS A JUDGEMENT AND IT NEEDS A NUMBER. Ten clean runs is roughly a
    # night's dispatching here, which is long enough that a gate still failing
    # for a live reason would have shown it. It is a reading aid, not a
    # threshold anything depends on — nothing branches on it but the wording.
    QUIET = 10
    live = {k: v for k, v in counts.items() if ago[k] < QUIET}
    quiet = {k: v for k, v in counts.items() if ago[k] >= QUIET}

    print(f"gate failures across {total} kept run(s), newest commit first:")
    for name, n in sorted(live.items(), key=lambda kv: -kv[1]):
        pct = 100.0 * n / total
        when = "the newest run" if ago[name] == 0 else f"{ago[name]} run(s) ago"
        note = "  <- rare, and rare is the dangerous kind" if n <= 2 else ""
        print(f"  {n:3}/{total}  {pct:5.1f}%  {name:14} last {when}, e.g. {newest[name]}{note}")

    if quiet:
        print(f"\n  quiet — nothing red in the last {QUIET}+ runs. Fixed, or the "
              f"condition has not recurred:")
        for name, n in sorted(quiet.items(), key=lambda kv: ago[kv[0]]):
            pct = 100.0 * n / total
            print(f"  {n:3}/{total}  {pct:5.1f}%  {name:14} "
                  f"last {ago[name]} run(s) ago, at {newest[name]}")
    return 0


def pending():
    """Commits that have no verdict yet — what is still in flight.

    WHY. `gates.py` answers "of the runs that came back, which are red".
    Overnight the more urgent question is the other one: **which of the things I
    dispatched have not come back at all.** I answered it by hand a dozen times
    in one night with the same `for sha in ...; do git show ...` loop, and a
    question asked a dozen times is a command — the same reasoning that produced
    `--flaky`.

    It matters beyond convenience. The rule is *"check what LANDED, not what
    reported success"*, and the failure mode it guards against is working hard
    on something that silently is not landing. A commit with no verdict is
    invisible to every other tool here: `gates.py` skips it, `verdict-keys`
    skips it, and the branch moving proves nothing because I push constantly.

    Walks back from HEAD and stops at the first commit that HAS a verdict —
    everything newer is either building, queued, or was never dispatched, and
    this cannot tell those apart. It says so rather than guessing.
    """
    if not RUNS.is_dir():
        print("gates: no runs directory yet")
        return 0
    have = {p.stem for p in RUNS.glob("*.txt")}
    log = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h\t%s", "-60"],
                         capture_output=True, text=True).stdout.splitlines()
    waiting = []
    for entry in log:
        sha, _, subject = entry.partition("\t")
        if sha in have:
            print(f"{len(waiting)} commit(s) with no verdict, newest first. "
                  f"Last answered: {sha}  {subject[:52]}")
            break
        waiting.append((sha, subject))
    else:
        print(f"{len(waiting)} commit(s) with no verdict — none of the last 60 has one")
    for sha, subject in waiting:
        print(f"  ....  {sha}  {subject[:58]}")
    if not waiting:
        print("  nothing in flight — every commit back to the last verdict is answered")
    else:
        print("  building, queued, or never dispatched — this cannot tell those apart.")
    return 0


def main():
    if "--constant" in sys.argv:
        return constant()
    if "--flaky" in sys.argv:
        return flaky()
    if "--pending" in sys.argv:
        return pending()
    if "--series" in sys.argv:
        i = sys.argv.index("--series")
        if i + 1 >= len(sys.argv):
            print("gates --series: needs a verdict key, e.g. --series confabs")
            return 2
        return series(sys.argv[i + 1])
    count = 12
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print(f"gates: '{sys.argv[1]}' is not a number of runs")
            return 2

    if not RUNS.is_dir():
        print("gates: no runs directory yet")
        return 0
    have = {p.stem: p for p in RUNS.glob("*.txt")}
    if not have:
        print("gates: no run files yet")
        return 0

    log = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h\t%s", "-400"],
                         capture_output=True, text=True).stdout.splitlines()

    shown = 0
    red = 0
    for entry in log:
        sha, _, subject = entry.partition("\t")
        if sha not in have:
            continue
        text = read(have[sha])
        # NAMED, NOT SKIPPED — the opposite of what `flaky()` does with the
        # same file, and on purpose.
        #
        # A build whose sim never ran dilutes a RATE, so the flakiness table
        # drops it. But "this commit's build never produced a sim" is exactly
        # what you want to be told when reading the last few runs, and the
        # first version of this loop printed it as `??? ` — indistinguishable
        # from a verdict this tool failed to parse. Two of those in a row is
        # how ninety minutes went into diagnosing a licence failure as a
        # compile error.
        #
        # Third site of one blindness tonight, and found by grepping for it
        # rather than by tripping over it, which is the corollary working.
        if NO_SIM in text:
            print(f"NOSIM {sha}  {subject[:58]}")
            print("        the build produced no player — licence or compile, see the verdict")
            shown += 1
            if shown >= count:
                break
            continue
        m = PASS.search(text)
        verdict = m.group(1) if m else "?"
        fails = FAILING.search(text)
        mark = "PASS" if verdict == "True" else "RED " if verdict == "False" else "??? "
        if verdict != "True":
            red += 1
        print(f"{mark} {sha}  {subject[:58]}")
        if fails:
            for g in split_gates(fails.group(1)):
                print(f"        {g}")
        shown += 1
        if shown >= count:
            break

    if shown == 0:
        print("gates: none of the recent commits has a verdict")
        return 0
    print()
    print(f"{shown} run(s) read, {red} not green. Newest commit first — NOT newest to land.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
