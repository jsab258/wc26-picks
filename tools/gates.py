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

# THE COUNT PREFIX IS OPTIONAL, BECAUSE THE LINE GAINED ONE ON 18 AUGUST AND
# EVERY KEPT RUN BEFORE THAT DOES NOT HAVE IT. SimDirector now prints
# "FAILING GATES: 4 of 72: jobRan, dayJob, ..." so a red build states its own
# denominator; the 198 runs already on disk say "FAILING GATES: jobRan, ...".
# Without the optional group this tool read "4 of 72: jobRan" as a GATE NAME
# and duly reported a new gate that had failed once in 198 runs, flagged as
# "rare, and rare is the dangerous kind" — its own warning, fired at itself.
#
# That is rule 1's second corollary exactly: changing the line changed what
# reads it, and the reader was three files away. Both formats parse now, and
# they have to, because the history is the whole point of this tool.
FAILING = re.compile(r"FAILING GATES:\s*(?:\d+ of \d+:\s*)?(.+)")
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
    # FULL SHAS AND A PREFIX MATCH, because `%h` GREW AND SILENTLY BROKE THIS.
    #
    # This used `--format=%h` and compared it to the run file's stem with `in`.
    # Git chooses the abbreviation length dynamically — enough characters to
    # stay unambiguous — and as this repository grew it went from seven to
    # EIGHT. Run files are named with seven. So the comparison stopped
    # matching anything at all: measured 24 Aug, 333 run files against 400
    # commits, ZERO matched.
    #
    # Nothing failed. Every run simply fell into the "older than the log
    # window" bucket below, which is sorted by SHA — that is, by nothing —
    # and this function's own docstring says commit order is the only order in
    # which "how long ago" means anything. So every `last N runs ago` and
    # every recent-window rate has been arbitrary since the day the
    # abbreviation grew, and it looked exactly like working output.
    #
    # `%H` is the full hash and never changes length; the run file's stem is a
    # prefix of it. That comparison cannot rot.
    have = {p.stem: p for p in RUNS.glob("*.txt")}
    log = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H", "-400"],
                         capture_output=True, text=True).stdout.split()
    out, seen = [], set()
    for full in log:
        for stem in have:
            if stem in seen:
                continue
            if full.startswith(stem):
                out.append((stem, have[stem]))
                seen.add(stem)
                break
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

# THE VERDICT'S VALUE GRAMMAR, AND THERE IS NOW ONE COPY OF IT IN THIS FILE.
#
# A verdict value is a RUN of either whole bracket groups or non-space, non-
# bracket characters. Brackets and parentheses are consumed WHOLE because they
# are the sanctioned way to write a value containing spaces
# (`measureWorstWhere=[nothing measured]`), and the obvious alternative —
# whole-group OR `\S+` — loses the race whenever the value starts with a digit
# and returns `0.45(narrowest`. The reasoning is `verdict-read.py:463-475`;
# this is the same expression.
#
# IT WAS WRITTEN TWICE IN THIS FILE AND THE TWO COPIES DISAGREED. `series()`
# had the correct run-of-either; `KEY_VALUE`, which is what `--constant`
# harvests with, had `[^\s\[\(]+` — a class that EXCLUDES `[`, so a value that
# starts with a bracket matched nothing at all and the key was invisible.
# Measured over the 326 kept runs: 110 keys were missing from the harvest, and
# one of them was `findingKinds`, which the old harvest reported as a permanent
# `none` because the 17 runs where it says `[absurdScale:1@pallet]` could not
# match. One idea, two implementations, and the one nobody looked at was the
# one missing a line — so there is one now.
#
# STILL THREE COPIES ACROSS tools/: this one, and two in `verdict-read.py`
# (`main` and `spaced_values`). A shared `tools/verdictfmt.py` is the right
# home; that file is not this agent's to touch, so the duplication is REPORTED
# rather than half-removed.
VALUE = r"(?:\[[^\]]*\]|\([^)]*\)|[^\s\[\(])+"


def key_pattern(key):
    """`key=<value>` anchored so `notoriety` cannot match `notorietyPeak`."""
    return r"(?<![\w])" + re.escape(key) + r"=(" + VALUE + r")"


# EVERY `key=value` IN A VERDICT, harvested with the grammar above. Note what
# consuming brackets whole does to the harvest: `k=1.4[lit=14.34% all=64,58,44]`
# now yields `k` only, where the old class yielded `all=64,58,44` as though
# `all` were a top-level verdict key. Seventeen such phantom keys disappeared.
KEY_VALUE = r"(?<![\w])([A-Za-z][\w]*)=(" + VALUE + r")"


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
    # THE SAME VALUE GRAMMAR `verdict-read.py` USES, COPIED DELIBERATELY.
    #
    # The first version of the categorical fix matched `[^\s\[\(]+`, which
    # cannot read `reliabilityRead=[Fine after 0]` at all — the value STARTS
    # with a bracket, so nothing matches and the tool says the key does not
    # exist. That is the same false sentence this whole function was fixed for,
    # an hour later, in the fix itself: one idea, two implementations, and the
    # second one written without looking at the first.
    #
    # Brackets are the sanctioned form for a value with spaces, so a reader
    # that cannot consume them cannot read a large part of the verdict. The
    # comment beside the original in `verdict-read.py` also records that the
    # obvious version — whole-group OR non-space — loses the race whenever the
    # value starts with a digit. A RUN of either is what holds.
    pat = re.compile(key_pattern(key))
    # AND IF THE NAME MEANS TWO THINGS, SAY SO BEFORE PRINTING ANY OF IT.
    #
    # `search` takes the FIRST match in the whole file. That is fine while a
    # name is unique and silently wrong when it is not, and `npcs` was not:
    # the done line carried a population of 42 and the frame gate carried
    # 9.48ms of per-frame cost, so this printed a column with `42` scattered
    # through the milliseconds and no sign that two quantities had been
    # merged. `checks` and `rigs` were the same shape.
    #
    # The emitter is fixed — those three timings are `npcsMs`, `checksMs`,
    # `rigsMs` now — but the hazard is structural and the next reused name
    # would land here again. `verdict-read.py` has refused to answer across
    # two lines since the day it was written; this is that idea in the tool
    # that actually reads the trend, and it WARNS rather than refuses because
    # the older half of a series is often still worth looking at once you know
    # what happened to it.
    hits = []
    ambiguous = []
    for sha, path in runs:
        text = read(path)
        found = pat.findall(text)
        if found:
            hits.append((sha, found[0]))
        distinct = {f for f in found}
        if len(distinct) > 1:
            ambiguous.append((sha, sorted(distinct)[:3]))

    if ambiguous:
        sha, vals = ambiguous[0]
        print(f"gates --series {key}: AMBIGUOUS — this name carries more than "
              f"one value in {len(ambiguous)} of {len(runs)} run(s).")
        print(f"  {sha} has {', '.join(vals)} — the series below takes the "
              "FIRST match in each")
        print("  file, so it may be mixing two different quantities. "
              "`tools/verdict-read.py --collisions`")
        print("  lists every such name with its line numbers.\n")

    if not hits:
        print(f"gates --series {key}: no landed run carries that name.")
        print(f"  {len(runs)} runs read. Check the spelling against a verdict, or the")
        print("  number may never have reached the verdict — see tools/verdict-reach.py.")
        return 1

    # A VALUE THAT IS A WORD IS STILL A SERIES, and refusing it was the tool
    # doing the exact thing it exists to prevent. Until 5 August this matched
    # NUMBER only, so `--series inquiry` — the single most important series in
    # the project, the law's stage across every run ever kept — answered "no
    # landed run carries that name". That sentence is false and it is the
    # expensive kind of false: it reads as a spelling mistake or a number that
    # never reached the verdict, which is what I went looking for. Rule 3b in
    # the instrument's own voice — an absence dressed as a finding.
    #
    # And the categorical keys are where a series pays best, because the thing
    # a word series shows is the REGIME CHANGE, which the numeric path's own
    # closing paragraph says no statistic can see. `inquiry` is None for sixty
    # runs and then Procedure, and that transition IS the reading.
    try:
        xs = [float(v) for _, v in hits]
    except ValueError:
        return words(key, hits)
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


def words(key, hits):
    """The series of a verdict value that is a word rather than a number.

    A median of `None, None, Procedure` is not a thing, so the summary here is
    the one a word series actually supports: how many runs said each value, and
    WHERE IT CHANGED. The transition is the whole reading — `inquiry` sat on
    None for sixty runs and the four Procedures are every time the law has ever
    opened a case, which is a fact about four specific commits and not about a
    distribution.

    The transitions are printed newest-first like the series, and each one names
    the run where the NEW value first appears reading backwards, so the sha is
    the commit to go and read.
    """
    vals = [v for _, v in hits]
    print(f"{key}: {len(vals)} landed run(s), newest first")
    print()
    print("  " + "  ".join(vals))
    print()
    print(f"  newest {vals[0]}   ({hits[0][0]})")

    tally = {}
    for v in vals:
        tally[v] = tally.get(v, 0) + 1
    order = sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))
    print("  seen:  " + "   ".join(f"{v} x{n}" for v, n in order))

    # NEWEST-FIRST, so hits[i] is LATER than hits[i+1] and a difference between
    # them is a change that happened AT hits[i].
    changes = [(hits[i][0], hits[i + 1][1], hits[i][1])
               for i in range(len(hits) - 1) if hits[i][1] != hits[i + 1][1]]
    print()
    if not changes:
        print(f"  NEVER CHANGED across all {len(vals)} runs — every one says {vals[0]}.")
        print("  A value that has only ever been one thing is rule 5b's corollary")
        print("  aimed at a reading: whatever is gated on the OTHER values has")
        print("  never executed. See --constant.")
    else:
        print(f"  changed {len(changes)} time(s), newest first:")
        for sha, was, now in changes[:12]:
            print(f"    {sha}  {was} -> {now}")
        if len(changes) > 12:
            print(f"    (+{len(changes) - 12} older changes not shown)")
        print()
        print("  READ THE SERIES, NOT THE TALLY. A count of each value says nothing")
        print("  about when the test changed underneath it, and for a word that is")
        print("  usually the only question — a value that appears four times in the")
        print("  four newest runs is a new capability, not a one-in-thirty event.")
    return 0


# Values that mean "this did not happen". A key stuck on one of these across
# every run is the shape worth reading; a key stuck on a number that is not one
# of these is usually a constant somebody printed, which is noise here.
DID_NOT_HAPPEN_NUMBERS = {"0", "0.0", "0.00", "0.000", "0.0000", "-1"}

# THE WORDS, AND THE FOUR NEW ONES ARE THE WHOLE REASON THIS SWEEP CAN SEE THE
# DRESSING SURFACE AT ALL.
#
# `nothing-offered`, `nothing-measured`, `nothing-flagged` and `nothing-refused`
# are the project's deliberate way of distinguishing *no call was ever made*
# from *a real zero* — rule 3b's repair, in words rather than a number, so a
# never-ran branch cannot read as clean (`Core/KitDressing.cs:103-111`;
# `ledger/verify.py:2218` and `verdict-read.py:407` use the same convention).
# They were absent here, which defeated this tool at exactly the place it is
# most needed: a key sitting at `nothing-offered` for a hundred runs IS a
# permanently-dead branch, and `--constant` read the word as a value that had
# changed and moved on. Audit finding C6, `game-design/agent-reports/
# kit-dressing-audit.md`.
#
# They are kept apart from the numbers because they behave differently below:
# a WORD is allowed to carry its denominator (`nothing-flagged/12`), a zero is
# not (`0/12` is a ratio whose other half moves and means something else).
DID_NOT_HAPPEN_WORDS = {"False", "None", "none",
                        "nothing-offered", "nothing-measured",
                        "nothing-flagged", "nothing-refused"}

# The union, under the name the rest of the project greps for.
DID_NOT_HAPPEN = DID_NOT_HAPPEN_NUMBERS | DID_NOT_HAPPEN_WORDS

# `[a:1,b:2,+3more]` — the emitter's own announced cap. It is not a row, and a
# reader that treats it as one silently drops the whole key out of the row
# sweep, which is a cap biting a cap.
CAP_FIELD = re.compile(r"^\+\d+more$")


def unwrap(value):
    """Strip enclosing bracket or paren pairs that wrap the WHOLE value.

    `[none]` -> `none`, `(0.1,0.2)` -> `0.1,0.2`, `[[none]]` -> `none` (which
    `textFlatWorst` really does emit, once, in 171 runs). Bounded, because an
    unbounded loop over attacker-shaped input is a hang and this reads files a
    Windows runner wrote.
    """
    for _ in range(4):
        if len(value) > 1 and ((value[0] == "[" and value[-1] == "]")
                               or (value[0] == "(" and value[-1] == ")")):
            value = value[1:-1]
        else:
            break
    return value


def split_fields(text, sep=","):
    """Split on `sep` at bracket depth zero — `split_gates`' idea for rows."""
    out, depth, cur = [], 0, []
    for ch in text:
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth -= 1
        if ch == sep and depth <= 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return [f for f in out if f]


def did_not_happen(value):
    """Does this value MEAN the thing it measures has not occurred?

    THREE READINGS, AND EACH ONE IS A SHAPE THE VERDICT ACTUALLY EMITS. It is a
    parse, not a guess at intent — the judgement of whether a dead branch is a
    fault counter doing its job or a system nobody wired stays a person's, which
    is what `constant`'s docstring promises.

      1. THE WHOLE VALUE, brackets stripped. `0`, `False`, `[none]`,
         `[nothing-offered]`.
      2. A SENTINEL WORD CARRYING ITS DENOMINATOR — `nothing-flagged/12`,
         `[none]/0of8`. The word is the value; the number after it is the
         denominator rule 3b demands beside every zero, and it MOVES while the
         branch stays dead (twelve lamps placed, then nineteen, and not one flag
         call either time). Only a WORD gets this reading: `0/12` is a ratio,
         its other half is a real measurement, and treating it as never-happened
         would swallow most of the verdict.
      3. A BRACKETED LIST WHOSE EVERY ROW IS DEAD —
         `[sign_post:nothing-offered,sign_plate_name:nothing-offered]`. A list
         of dead rows is dead; one live row makes the key live, and the dead
         rows inside it are what the row sweep in `constant` reports separately.
    """
    whole = unwrap(value)
    if whole in DID_NOT_HAPPEN:
        return True
    if unwrap(whole.split("/", 1)[0]) in DID_NOT_HAPPEN_WORDS:
        return True
    if value.startswith("[") and value.endswith("]"):
        fields = [f for f in split_fields(whole) if not CAP_FIELD.match(f)]
        if fields:
            return all(did_not_happen(f.partition(":")[2] or f) for f in fields)
    return False


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
# AND THE AUDIO REASONS WERE WRONG, WHICH THIS TOOL FOUND BY ITS OWN RULE.
# Seven keys carried "no audio device on the runner", and on 24 Aug five of
# them MOVED — `soundsOffered=6 soundsAdmitted=6 soundsPeak=1
# soundsPeakBus=Impact`, with `simAudible` still False. Both cannot be true of
# a device, and they are not about one: `Audio.Admit` is a BUDGET decision
# made in C#, and it runs whether or not anything can be heard. Nothing had
# ever offered it a sound, which is a completely different fact and the one
# the `Audio` comment warns about in its own words — "a budget that never
# refuses anything is indistinguishable from one that is not wired".
#
# Its first customers arrived by accident: wiring `Core/DoorSwing` put an
# `Audio.Impact` on each latch, and `doorSwing=376/6/6/0/1` against
# `soundsOffered=6 soundsAdmitted=6 soundsPeakBus=Impact` is the same six
# events seen from both ends. The keys still at zero keep an entry, with the
# reason they actually have.
EXPLAINED_ZEROS = {
    "soundsDropped": "the BUDGET runs regardless of a device; six sounds were "
                     "offered and six admitted, so it has never had to refuse "
                     "one — read soundsOffered before reading this as health",
    "soundsNoClip": "same as soundsDropped: too little traffic to refuse "
                    "anything yet, not an absent device",
    "soundsStolen": "same as soundsDropped: a steal needs a full bus, and the "
                    "peak is one",
    "speechNoAudio": "no audio device on the runner; read simAudible first",
    "simAudible": "the runner has no audio device — this is the key that says so",
    "windowsShopLit": "last-wins, written after midnight when every shop is "
                      "shut by design; read windowsShopLitAtShot",
    "walkersPrimitive": "last-wins over a once-a-second pass; read "
                        "walkersPrimitiveEver",
    # THREE ENTRIES LEFT THIS TABLE ON 24 AUG BECAUSE THEIR KEYS STARTED
    # MOVING, which is this tool's own rule catching three of its own claims.
    # `huddleTalking` and `bodyCrowdEligible` expired as GOOD news — the mob
    # holds a conversation now and the crowd has an eligible real body, and
    # both reasons said those were zero by construction. `offRoad` expired as
    # a fault: a vehicle left the tarmac ONCE in the recent window and the
    # series is back to zero, so it belongs to `--flaky` rather than here.
    # An explanation for a key that is no longer stuck is noise, and this
    # block prints every time.
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
    "stemsUnbound": "a fault counter doing its job",
    "unbound": "a fault counter doing its job",
    "textNoText": "a fault counter doing its job",
    "bodyGrantsFailed": "a fault counter doing its job",
    "walkerBodiesFailed": "a fault counter doing its job",
    "bodySkinnedEver": "the paint path is skipped when a model arrives "
                       "textured; read bodyKeptMats beside it",
    "groundless": "false is the ASSERTED value — nobody with no grounds "
                  "gets to search you, and the gate requires it",
    "contradiction": "the FIRST denouncement is kept uncontradicted on "
                     "purpose; the contradicted branch is blowbackContradiction "
                     "and reads 0.90 in all 46 runs",
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

    AND IT WAS BLIND IN THE TWO PLACES IT IS MOST NEEDED (audit finding C6).
    A key stuck on the word `nothing-offered` — the project's deliberate way of
    saying no call was ever made — read as a value that had changed, and a key
    whose value starts with `[` was not harvested at all. Both are fixed above:
    `DID_NOT_HAPPEN_WORDS` carries the four sentinels, `VALUE` is the one value
    grammar, and `scan` reads the ROWS inside a bracketed list so a dead family
    inside a live key is reportable. What did NOT change is the judgement: this
    still cannot tell a fault counter from an unentered branch and still does
    not try.
    """
    runs = ordered_runs()
    texts = [(sha, read(path)) for sha, path in runs]
    constant_report(texts, minimum_runs=minimum_runs)
    # EXIT 0 WHATEVER IT FINDS. This is a READING, not a gate: a dead branch is
    # a thing to go and look at, and failing a commit on one would block the
    # commit that wires it up.
    return 0


class Scan:
    """What one sweep over a set of verdicts found. Pure data, no printing.

    THE ARITHMETIC LIVES WHERE THE TEST CAN REACH IT. `--constant` used to be
    one function that globbed the runs directory, counted, and printed, so the
    only way to exercise it was to have a runs directory — which means the
    accepting and rejecting cases can only be produced by the project being in
    a particular state, and rule 5b's four blocked guards are what that costs.
    `scan()` takes TEXT. The selftest hands it verdicts it authored.
    """

    def __init__(self):
        self.runs = 0
        self.values = {}        # key -> set of every value seen
        self.key_runs = {}      # key -> how many runs carry it  (its denominator)
        self.rows = {}          # (key, row name) -> set of every row value seen
        self.row_runs = {}      # same -> how many runs carry that row
        self.bracket_keys = set()   # keys whose value is a bracketed list
        self.row_keys = set()       # ... of which parse as `name:value` rows
        self.capped_keys = set()    # ... whose emitter said `+Nmore`


def scan(texts):
    """Harvest every key, and every ROW inside every bracketed key.

    THE ROW HALF IS THE OTHER HALF OF FINDING C6. A flat key can go dead and be
    reported; a FAMILY inside `kitBy=[lamp:41/44/0/0refused,sign_post:nothing-
    offered]` cannot, because the key as a whole is moving. The audit's words:
    "a dead row in `kitBy` will never be surfaced by the tool this project
    relies on for exactly that". Rows are `name:value` at bracket depth zero.

    A field matching `+Nmore` is the EMITTER'S OWN ANNOUNCED CAP, not a row.
    Dropping the key on seeing one would be this tool silently losing a whole
    family because the emitter told the truth about a cap, so the key is kept,
    the field is not counted as a row, and `capped_keys` records that rows were
    hidden from this sweep upstream — which the report prints.
    """
    s = Scan()
    for _, text in texts:
        s.runs += 1
        here, rows_here = {}, {}
        for k, v in re.findall(KEY_VALUE, text):
            here.setdefault(k, set()).add(v)
            if not (v.startswith("[") and v.rfind("]") > 0):
                continue
            s.bracket_keys.add(k)
            fields = split_fields(unwrap(v[:v.rfind("]") + 1]))
            capped = [f for f in fields if CAP_FIELD.match(f)]
            fields = [f for f in fields if not CAP_FIELD.match(f)]
            if capped:
                s.capped_keys.add(k)
            if not fields or not all(":" in f for f in fields):
                continue
            s.row_keys.add(k)
            for f in fields:
                name, _, val = f.partition(":")
                rows_here.setdefault((k, name), set()).add(val)
        for k, vs in here.items():
            s.values.setdefault(k, set()).update(vs)
            s.key_runs[k] = s.key_runs.get(k, 0) + 1
        for rk, vs in rows_here.items():
            s.rows.setdefault(rk, set()).update(vs)
            s.row_runs[rk] = s.row_runs.get(rk, 0) + 1
    return s


def constant_report(texts, minimum_runs=20, out=print):
    """Print the sweep. Returns the `Scan` so a test can assert on it."""
    s = scan(texts)

    # NEVER-EXAMINED PRINTS THE WORDS. `0 keys stuck` and `no verdict was ever
    # opened` are the same sentence to a reader skimming, and the second one is
    # the tool being broken. rule 3b: the default text for never-ran is the
    # words, so that case cannot read as clean.
    if s.runs == 0:
        out("gates --constant: nothing measured — 0 measuring run(s) read, "
            "0 key(s) harvested.")
        out("  Either no verdict has landed or every kept run says NO PLAYER "
            "LOG. This is not a clean result.")
        return s
    if s.runs < minimum_runs:
        out(f"gates --constant: nothing measured — only {s.runs} measuring "
            f"run(s) kept, {len(s.values)} key(s) harvested.")
        out(f"  A key that has not varied over fewer than {minimum_runs} runs "
            f"has not been given a chance to.")
        return s

    stuck = sorted(k for k, vs in s.values.items()
                   if all(did_not_happen(v) for v in vs))
    known = EXPLAINED_ZEROS
    fresh = [k for k in stuck if k not in known]
    settled = [k for k in stuck if k in known]

    def shown(key):
        """The value, and the KEY'S OWN DENOMINATOR beside it.

        `a3clean=0` over 326 runs and `a3clean=0` over 7 runs are different
        claims and the old output printed them identically. A key present in a
        handful of runs has had a handful of chances to move, which is the
        sample-size half of `crowdRead` — the metric that produced two opposite
        published conclusions in one hour off a 24-body and a 6-body sample.
        """
        vs = sorted(s.values[key])
        v = vs[0] if len(vs) == 1 else "/".join(vs[:3]) + ("..." if len(vs) > 3 else "")
        return f"{key}={v}", f"in {s.key_runs[key]}/{s.runs} runs"

    out(f"gates --constant: {s.runs} measuring run(s) read, {len(s.values)} "
        f"key(s) harvested, {len(stuck)} that have never been anything but "
        f"zero/false/none/nothing-* — {len(fresh)} unexamined, "
        f"{len(settled)} already explained.")
    out(f"  ({len(s.bracket_keys)} of those keys carry a bracketed list; "
        f"{len(s.row_keys)} of those parse as name:value rows, giving "
        f"{len(s.rows)} row(s) swept below.)")
    out("Read each one and ask which it is: a fault counter doing its job, "
        "or a branch nothing has ever entered.\n")

    # THIN EVIDENCE IS SEPARATED, NOT DROPPED. Everything still prints: a
    # filter here would be this tool doing what rule 3b's truncation warning
    # forbids. The boundary is `minimum_runs`, the number this function already
    # applies to the whole corpus, used at the granularity where it bites —
    # not a new bound. Measured over the 326 kept runs before it was written:
    # the stuck keys' own run counts are 7, 8, 9, 9, then 59 and up, so it
    # separates four keys from sixty-eight and the gap is real rather than
    # chosen.
    thick = [k for k in fresh if s.key_runs[k] >= minimum_runs]
    thin = [k for k in fresh if s.key_runs[k] < minimum_runs]
    for k in thick:
        val, den = shown(k)
        out(f"  {val:<44} {den}")
    if thin:
        out(f"\n  ---- {len(thin)} of the {len(fresh)} carried by fewer than "
            f"{minimum_runs} runs — too few chances to move to be called "
            f"constant ----")
        for k in thin:
            val, den = shown(k)
            out(f"  {val:<44} {den}")

    if settled:
        out(f"\n  ---- {len(settled)} already read and understood; "
            f"the reason is in the code, not here ----")
        for k in settled:
            val, den = shown(k)
            out(f"  ({val} — {known[k]}) {den}")

    # A KEY THAT LEAVES THE LIST IS A REASON THAT HAS EXPIRED. If somebody
    # explains a zero and it later starts moving, the explanation is stale and
    # nobody would ever be told — the same decay the reach ledger's reasons
    # have, which this project has now been bitten by three times.
    gone = sorted(k for k in known if k not in stuck)
    if gone:
        out(f"\n  ---- {len(gone)} explained key(s) NO LONGER STUCK — the "
            f"reason has expired and wants deleting ----")
        for k in gone:
            where = (f"now {sorted(s.values[k])[:4]} in {s.key_runs[k]}/{s.runs} runs"
                     if k in s.values else "no longer in any kept verdict")
            out(f"  {k} moved: {known[k]}  [{where}]")

    # THE ROWS. A separate block because it answers a different question, with
    # its own denominator: `0 dead rows` beside `177 rows swept` is a reading,
    # and `0 dead rows` on its own is indistinguishable from a sweep that
    # opened nothing.
    dead_rows = sorted(rk for rk, vs in s.rows.items()
                       if all(did_not_happen(v) for v in vs))
    out(f"\n  ---- rows inside bracketed keys: {len(dead_rows)} never anything "
        f"but zero/false/none/nothing-*, of {len(s.rows)} row(s) swept across "
        f"{len(s.row_keys)} key(s) ----")
    if not dead_rows:
        out("  none — every row that was swept has moved at least once. "
            "(Not a cap: no row list is truncated by this tool.)")
    for key, name in dead_rows:
        vs = sorted(s.rows[(key, name)])
        v = vs[0] if len(vs) == 1 else "/".join(vs[:3])
        out(f"  {key}[{name}]={v:<28} in {s.row_runs[(key, name)]}/{s.runs} runs")
    if s.capped_keys:
        out(f"  ({len(s.capped_keys)} bracketed key(s) printed their own "
            f"`+Nmore` cap in at least one run, so rows exist that no sweep "
            f"here can see: {', '.join(sorted(s.capped_keys))})")
    return s


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
    # THE RECENT WINDOW, AND THE DOCSTRING ABOVE ARGUES FOR IT WITHOUT HAVING
    # IT. That paragraph says "a rate with no recency is a claim about the
    # present made entirely out of the past" and the fix applied was HOW LONG
    # AGO — which is recency of the last failure, not a rate for the present.
    # The gap bit on 24 Aug: `dayJob` printed `27.0% ... last 3 run(s) ago`,
    # which reads as chronically broken AND live, and I was one step from
    # investigating it as such. Over the most recent 36 runs it is 8.3%.
    # `frame` is worse — 47.2% lifetime against 8.3% recent — because most of
    # its failures are the software-rasteriser era that no longer exists.
    #
    # A lifetime rate spanning a regime change describes neither regime. This
    # is the same repair `--series` already has, where the recent window is
    # printed ABOVE the all-runs one on purpose.
    RECENT = 40
    counts, newest, ago, recent = {}, {}, {}, {}
    recent_n = min(RECENT, total)
    for i, (sha, path) in enumerate(runs):        # i == runs since, newest first
        m = FAILING.search(read(path))
        if not m:
            continue
        for g in split_gates(m.group(1)):
            name = g.split("[", 1)[0].strip()
            counts[name] = counts.get(name, 0) + 1
            if i < recent_n:
                recent[name] = recent.get(name, 0) + 1
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

    # RANKED BY THE RECENT RATE, not the lifetime one: the question this tool
    # is asked is "what is flaky NOW", and ordering by a number that includes
    # a dead regime answers a different one.
    print(f"gate failures across {total} kept run(s), newest commit first "
          f"(recent = the last {recent_n}):")
    for name, n in sorted(live.items(),
                          key=lambda kv: -(recent.get(kv[0], 0) / max(1, recent_n))):
        pct = 100.0 * n / total
        r = recent.get(name, 0)
        rpct = 100.0 * r / max(1, recent_n)
        when = "the newest run" if ago[name] == 0 else f"{ago[name]} run(s) ago"
        note = "  <- rare, and rare is the dangerous kind" if r <= 2 else ""
        # The recent rate FIRST, because it is the one that describes today.
        # DRIFT IN BOTH DIRECTIONS, and the worsening one matters more.
        # A gate improving is good news that the lifetime rate hides; a gate
        # GETTING WORSE is a live regression that the lifetime rate buries
        # under all the runs from before it started. `claims` is the case:
        # 7.5% lifetime, 15.0% recent, and only the second number is about
        # the code as it stands today.
        drift = ""
        if n >= 5 and rpct * 2 < pct:
            drift = f"  <- improving: {pct:.0f}% lifetime is mostly an older regime"
        elif r >= 3 and rpct > pct * 1.5:
            drift = f"  <- WORSENING: {rpct:.0f}% recent against {pct:.0f}% lifetime"
        print(f"  recent {r:2}/{recent_n} {rpct:5.1f}%   lifetime {n:3}/{total} "
              f"{pct:5.1f}%   {name:14} last {when}, e.g. {newest[name]}{note}{drift}")

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
    # `%H` truncated to the run-file convention, not `%h` — see
    # `ordered_runs`. The abbreviation grew to eight characters and every
    # `sha in have` test against a seven-character stem silently stopped
    # matching, here as everywhere else it was written.
    log = [f"{h[:7]}\t{rest}" for h, _, rest in
           (l.partition("\t") for l in subprocess.run(
               ["git", "-C", str(ROOT), "log", "--format=%H\t%s", "-60"],
               capture_output=True, text=True).stdout.splitlines())]
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


# ---- THE SELFTEST'S FIXTURES -----------------------------------------------
#
# SYNTHETIC, AND THAT IS NOT A CONVENIENCE. Three rejecting fixtures in this
# project were pinned to real files and had to be unpinned, because a fixture
# pinned to a real subject goes red the day the PROJECT improves — doing the
# work the tool prompts must never break the tool. Nothing below names a real
# verdict, a real run, or a real key that only exists today; the shapes are
# copied from `Core/KitDressing.cs`'s emit, which is what the sweep will meet.
#
# Twenty verdicts, because `constant_report` refuses to summarise fewer than
# `minimum_runs`=20 and the accepting case has to get past that.
def _fixture_runs():
    """Twenty synthetic verdicts, newest first. What each key is FOR:

      selftestMoved      MOVED, plain numbers            -> must NOT be reported
      selftestFilled     `nothing-offered` then `17/19`  -> must NOT be reported
                         (a family that starts empty and later fills — the
                         realistic shape, and the one a naive word-match eats)
      selftestDead       `nothing-offered` every run     -> MUST be reported
      selftestFlagDead   `nothing-flagged/12` .. `/19`   -> MUST be reported
                         (the word carrying a denominator that MOVES)
      selftestRowsMove   `[a:1,b:2]` -> `[a:2,b:2]`      -> key must NOT be
                         reported, and row `a` must not be either
      selftestRowsDead   `[a:nothing-offered,b:0]`       -> MUST be reported,
                         and both rows with it
      selftestMixedRows  `[live:41/44,dead:nothing-offered]` with `live`
                         moving  -> the KEY must not be reported and the ROW
                         `dead` must be: the whole point of the row sweep
      selftestCapped     `[a:1,b:2,+3more]`              -> the cap is not a
                         row, and the key stays in the sweep
      selftestZeroRatio  `0/40` every run                -> must NOT be
                         reported. A REAL ZERO CARRYING ITS DENOMINATOR IS A
                         MEASUREMENT, not a dead branch: forty sites were
                         offered and looked at. The sentinel words exist
                         precisely to be distinguishable from this, and a
                         classifier that reads a leading `0` as never-happened
                         re-collapses the distinction C6 is about — and would
                         swallow most of the verdict, where `n/m` is the
                         commonest shape there is.
    """
    runs = []
    for i in range(20):
        newest = (i == 0)
        runs.append((f"fix{i:04d}", " ".join([
            "# Sim verdict — fix @1787000000",
            f"selftestMoved={i}",
            "selftestFilled=" + ("17/19" if i < 3 else "nothing-offered"),
            "selftestDead=nothing-offered",
            f"selftestFlagDead=nothing-flagged/{12 + i}",
            f"selftestRowsMove=[a:{1 + (i % 2)},b:2]",
            "selftestRowsDead=[a:nothing-offered,b:0]",
            f"selftestMixedRows=[live:{40 + i}/44,dead:nothing-offered]",
            "selftestCapped=[a:1,b:2,+3more]",
            "selftestZeroRatio=0/40",
            "pass=True" if newest else "pass=True",
        ])))
    return runs


def selftest():
    """Both outcomes, ACCEPTING CASE FIRST.

    The expensive failure for a sweep like this is not that it misses a dead
    key. It is that it calls a LIVE key dead, because then every reading it
    prints is suspect and the next person stops opening it — and four guards in
    this project passed their failure case, had never been run against the case
    they must accept, and each one blocked the good case rather than the bad.

    So: what must NOT be reported is asserted first, then what must be, then
    the denominators, then the never-examined wording.
    """
    ok = True

    def bad(msg):
        nonlocal ok
        ok = False
        print("gates --selftest: " + msg)

    lines = []
    s = constant_report(_fixture_runs(), out=lines.append)
    text = "\n".join(lines)
    reported = {ln.strip().split("=", 1)[0].strip("(")
                for ln in lines if ln.startswith("  ") and "=" in ln}

    # ---- 1. THE ACCEPTING CASE: A KEY THAT MOVED IS NOT CALLED CONSTANT ----
    for key, why in (("selftestMoved", "plain numbers 0..19"),
                     ("selftestFilled", "`nothing-offered` in 17 runs and "
                                        "`17/19` in 3 — a family that filled"),
                     ("selftestRowsMove", "bracketed rows that change"),
                     ("selftestMixedRows", "one live row and one dead one"),
                     ("selftestZeroRatio", "`0/40` — a real zero carrying the "
                                           "denominator rule 3b asks for")):
        if key in reported:
            bad(f"FAILED THE CASE IT MUST ACCEPT — {key} ({why}) was reported "
                f"as never having moved.")
    if ("selftestRowsMove", "a") in [rk for rk in s.rows if
                                     all(did_not_happen(v) for v in s.rows[rk])]:
        bad("FAILED THE CASE IT MUST ACCEPT — the row selftestRowsMove[a] "
            "changes 1<->2 and was called dead.")

    # ---- 2. A SENTINEL WORD IN EVERY RUN IS REPORTED ----
    for key, why in (("selftestDead", "`nothing-offered` in all 20 runs"),
                     ("selftestFlagDead", "`nothing-flagged/N` in all 20 runs, "
                                          "denominator moving 12..31"),
                     ("selftestRowsDead", "every row dead")):
        if key not in reported:
            bad(f"FAILED THE CASE IT MUST REJECT — {key} ({why}) was not "
                f"reported. This is exactly finding C6.")

    # ---- 3. ROWS: a dead family inside a LIVE key is surfaced ----
    dead_rows = {rk for rk, vs in s.rows.items()
                 if all(did_not_happen(v) for v in vs)}
    if ("selftestMixedRows", "dead") not in dead_rows:
        bad("FAILED — the dead row inside a moving bracketed key was not "
            "surfaced, which is the half of C6 the flat keys cannot reach.")
    if ("selftestMixedRows", "live") in dead_rows:
        bad("FAILED THE CASE IT MUST ACCEPT — the live row inside the same "
            "key was called dead.")
    if "selftestCapped" not in s.row_keys or "selftestCapped" not in s.capped_keys:
        bad("FAILED — `+3more` was read as a row name, or the announced cap "
            "was not recorded; either way a whole key drops out of the sweep.")
    if ("selftestCapped", "+3more") in s.rows:
        bad("FAILED — the emitter's own cap marker was harvested as a row.")

    # ---- 4. THE DENOMINATORS, and the never-examined wording ----
    for want in (f"{s.runs} measuring run(s) read", "key(s) harvested",
                 "row(s) swept", "in 20/20 runs"):
        if want not in text:
            bad(f"FAILED — the report does not print `{want}`. A zero with no "
                f"denominator cannot tell nothing from fine.")
    empty = []
    constant_report([], out=empty.append)
    if "nothing measured" not in "\n".join(empty):
        bad("FAILED — a sweep over no runs must print the words `nothing "
            "measured`, not a clean-looking zero.")
    thin = []
    constant_report(_fixture_runs()[:3], out=thin.append)
    if "nothing measured" not in "\n".join(thin):
        bad("FAILED — three runs is not a corpus and must print the words.")

    if ok:
        print(f"gates --selftest: ok — over {s.runs} synthetic verdicts and "
              f"{len(s.values)} keys:")
        print("  ACCEPTS (not reported): selftestMoved, selftestFilled "
              "(nothing-offered -> 17/19), selftestRowsMove, selftestMixedRows")
        print("  REPORTS: selftestDead, selftestFlagDead (nothing-flagged/12"
              "..31), selftestRowsDead")
        print(f"  rows: {len(dead_rows)} dead of {len(s.rows)} swept across "
              f"{len(s.row_keys)} bracketed key(s), including "
              "selftestMixedRows[dead] inside a key that moves")
        print("  denominators print per key; 0 runs and 3 runs both print "
              "`nothing measured`")
    return 0 if ok else 2


def main():
    if "--selftest" in sys.argv:
        return selftest()
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

    # Same repair as above: full hash, truncated to the stem convention.
    log = [f"{h[:7]}\t{rest}" for h, _, rest in
           (l.partition("\t") for l in subprocess.run(
               ["git", "-C", str(ROOT), "log", "--format=%H\t%s", "-400"],
               capture_output=True, text=True).stdout.splitlines())]

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
