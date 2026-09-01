#!/usr/bin/env python3
"""READ NUMBERS OUT OF A VERDICT, AND REFUSE TO COMPARE TWO FROM DIFFERENT LINES.

    python3 tools/verdict-read.py nameTagsOffered namesDistinctPeak
    python3 tools/verdict-read.py --run d05e8cd ikDropMedian ikPlantedDropMedian

WHY THIS EXISTS, AND IT IS THE MOST EXPENSIVE HOUR OF 4 AUGUST.

I spent an afternoon calling one pair of nameplate numbers an arithmetic
impossibility — 42 against 13, then 40 against 9 — publishing four explanations
across four builds, disproving each with the next, and finally DELETING a
counter that was never broken.

They were on different log lines. One is written on the done line at the end of
the run; the other on the `glyphs` line, which is emitted on every screenshot.
Same counters, two moments, and the peaks go on climbing after the last shot.
Nothing ever contradicted anything.

The tool was the cause. `grep -o 'a=[0-9]*\\|b=[0-9]*' verdict.txt` happily
returns one value from line 19 and another from line 69 and gives NO SIGN that
it has done so — the output looks exactly like two numbers from one reading.
That is rule 3 in its purest form: when a result is surprising, check the ruler
before the reading, and here the ruler was a shell one-liner.

CLAUDE.md already said a peak's denominator must come from the same INSTANT as
its numerator, and five sites had been fixed for the frame version of that.
Nobody noticed that the LOG LINE is part of the instant too. This makes that
mechanical instead of remembered.

WHAT IT REFUSES. If the keys asked for do not all appear on one line, it says
so, names the lines, and exits 2 — because the answer to "are these two
comparable" is no, and printing them side by side would be the exact mistake
this file exists to stop.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "game-design" / "sim-shots"


def run_stamp_of_text(first_line):
    """The stamp itself, over TEXT, so the selftest can drive it without
    inventing files on disk — the same split `lint_text` has."""
    m = re.search(r"@(\d{6,})", first_line or "")
    return int(m.group(1)) if m else 0


def run_stamp(path):
    """The run's OWN timestamp, off its header line, not the file's mtime.

    `# Sim verdict — <sha7> @<epoch>` is written by the build that produced
    it, so it travels with the content. Returns 0 when the header is absent,
    which sorts such a file last rather than dropping it silently.
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
    except OSError:
        return 0
    return run_stamp_of_text(first)


def newest_measuring_run():
    """The newest per-run verdict whose sim actually ran.

    A build that dies on a licence seat or a compile error still commits a
    verdict, so "newest file" and "newest answer" are different questions —
    the same distinction `landed.py` had to learn.

    NEWEST BY THE RUN'S OWN STAMP, NOT BY FILE MTIME, AND THAT DISTINCTION
    COST A WRONG ANSWER TODAY.
    ---------------------------------------------------------------------
    This sorted by `st_mtime`. Mtime is a property of this container's disk,
    not of the run: a fresh clone, a `git checkout`, or the `git reset --hard`
    that repairs a container rollback rewrites every file's mtime to roughly
    the same instant, in whatever order git happened to write them.

    The container rolled back twice in one session — the fifth and sixth times
    this project has seen it — and after the repair this function returned a
    run from seventeen days earlier. It printed the filename it had chosen,
    which is the only reason it was caught, and it presented that run's numbers
    as the answer to a question about the newest build.

    That is the exact class this whole file exists to prevent, one layer down:
    a confident wrong answer with nothing in the output marking it as a
    choice. The header stamp cannot drift, because the build that measured the
    run is what wrote it.
    """
    runs = sorted((SHOTS / "runs").glob("*.txt"), key=run_stamp, reverse=True)
    for p in runs:
        if "NO PLAYER LOG" not in p.read_text(encoding="utf-8", errors="replace"):
            return p
    return None


def lint_text(text):
    """The lint itself, over TEXT rather than a file.

    Split out so `--selftest` can drive it with a line it must reject and a
    line it must ACCEPT. Rule 5b: a guard has two outcomes and shipping it
    means having watched both, and the accepting half is the one that never
    gets run — four guards in one day blocked the good case rather than the
    bad one, every one of them having passed its failure case.
    """
    bad = []
    for n, line in enumerate(text.split("\n"), 1):
        if "=" not in line:
            continue
        # INNERMOST FIRST, REPEATEDLY, because groups nest: `perception[...
        # ringPaint[ledger=1.18 ...] ...]`. One pass leaves the outer group's
        # closing bracket stranded on whatever key came last, which is three of
        # the five hits the previous version reported. Loop until it stops
        # changing.
        # AND REPLACED WITH SOMETHING THAT IS NOT A BRACKET. Substituting `[]`
        # for the inner group leaves a pair the next pass matches and rewrites
        # to itself, so the loop reaches a fixpoint with the OUTER group still
        # standing. A space has no such problem.
        flat = line
        for _ in range(8):
            once = re.sub(r"\[[^\[\]]*\]", " ", flat)
            if once == flat:
                break
            flat = once
        for m in re.finditer(r"(?<![\w])([A-Za-z][\w]*)=([^\s]+)", flat):
            v = m.group(2)
            if v.count("(") != v.count(")") or v.count("[") != v.count("]"):
                bad.append(f"line {n}: {m.group(1)}={v} …")
    return bad


def spaced_values(text):
    """VALUES WRITTEN AS `key=[a b c]` — the hole `lint_text` above cannot see.

    WHY THIS IS A SECOND FUNCTION AND NOT A FLAG ON THE FIRST. `lint_text`
    flattens every `[...]` group to a space BEFORE it looks at anything, then
    reports values whose brackets or parens do not balance. So it detects an
    UNBALANCED DELIMITER, which is what `0.45(narrowest 0.39 …)` happens to
    produce — it has never detected a space. Anything written as `key=[a b c]`
    is DELETED by the flattening pass and checked by nothing, and five live
    keys were sitting in that blind spot: `bodyAlbedo`, `rounds`,
    `worstWorldPair`, `gapWhy`, `massInRoad`, `speechVoicesWhy`.

    AND ITS ACCEPTING FIXTURE ENSHRINED THE BLINDNESS. `SELFTEST_GOOD` carries
    `places=[alley=3 market=53]` and `ao[rounds=[28.1 18.0] …]` and asserts they
    must be ACCEPTED — so the one case that would have exposed the hole was
    written into the guard as required behaviour. Rule 5b says a guard needs its
    accepting case run; this is the other edge of it, an accepting case chosen
    so wide that it certifies the fault.

    THE DISTINCTION THE FORMAT ACTUALLY MAKES, and it is not "brackets are
    fine":

      * `frame[mean=471.0ms gameShare=3.23%]` — GROUP syntax, a name followed
        by a bracket with no `=`. The bracket is a namespace of its own and the
        spaces inside it separate its members. Legal, and flagging it is the
        forty-hit false alarm the first lint produced.
      * `bodyAlbedo=[0.01 0.05 …]` — a VALUE that happens to start with a
        bracket. It lives in the flat `key=value` namespace `gates.py --series`
        reads, and a reader that is not bracket-aware returns `[0.01`.
        `verdict-read` and `gates.py --series` ARE bracket-aware, which is why
        this survived; every grep anybody types is not.

    So: only `key=[...]` is examined, nested groups inside it are stripped
    first (they are judged on their own entry), and a space in what remains is
    the fault.

    Returns (hits, examined) — the denominator ships with the zero, because "no
    spaced values" and "found no bracketed values at all" are the two readings
    this whole file exists to keep apart.
    """
    hits, examined = [], 0
    for n, line in enumerate(text.split("\n"), 1):
        for m in re.finditer(r"(?<![\w])([A-Za-z][\w]*)=\[", line):
            depth, end = 0, len(line) - 1
            for j in range(m.end() - 1, len(line)):
                if line[j] == "[":
                    depth += 1
                elif line[j] == "]":
                    depth -= 1
                    if depth == 0:
                        end = j
                        break
            examined += 1
            inner = line[m.end():end]
            for _ in range(8):
                once = re.sub(r"\[[^\[\]]*\]", "", inner)
                if once == inner:
                    break
                inner = once
            if " " in inner or "\t" in inner:
                hits.append((n, m.group(1), line[m.start():end + 1]))
    return hits, examined


def collisions(text):
    """ONE KEY, TWO MEANINGS — and it corrupted a series for months.

    The verdict is one namespace. `npcs` was a POPULATION on the done line and
    a MILLISECOND TIMING inside the frame gate, so `tools/gates.py --series
    npcs` printed a column with `42` scattered through the milliseconds and no
    sign that two different quantities had been merged. `checks` and `rigs`
    were the same, a count and a timing each.

    This tool already had what it takes to see it — it prints line numbers and
    refuses when requested keys do not share one — and nobody ever pointed it
    at the whole file. That is the shape of most of the faults in this
    project: the instrument existed and the sweep did not.

    THE TEST IS DIFFERING VALUES, NOT DIFFERING LINES. A verdict legitimately
    repeats a key: the gate block and the done line both print `gatesChecked`,
    and the frame gate appears verbatim in the FAILING GATES line. Those are
    one number written twice and are fine. A key that reads `42` in one place
    and `9.48` in another is two numbers wearing one name, and only the second
    is a fault.

    AND ONLY THE LINES TOOLS READ BY NAME, WHICH TOOK TWO NARROWINGS. The
    first version swept the whole file: 69 hits, of which about three were
    real. Most of a verdict is per-thing lines — one per character
    (`avatar=AdamAvatar`), one per sky sample (`density=0.0127`), one per clip
    — where repeating a key with a different value is the format doing its
    job. Filtering on `SimDirector:` barely helped, because the sim logs its
    diagnostics under that prefix too. Only three lines are the shared
    namespace: the gate block, the done line, and the failing-gates line.

    AND A KEY INSIDE A BRACKETED GROUP IS SCOPED TO IT. The done line carries
    `clean=308 dirty=0` at the top level and `[... crew=2 clean=0 dirty=247]`
    in the empire group, which is two namespaces and not a collision — so the
    groups are flattened away first, exactly as the space lint above does it.
    What is left is the flat `key=value` space that `gates.py --series` reads,
    and that is the only place one name may mean one thing.

    NOT PART OF `--lint`, AND THAT IS THE POINT OF THIS PARAGRAPH. Wired into
    the lint it reports 24 names on a healthy verdict, and about twenty of
    them are deliberate: a gate group is prose in brackets, so
    `disposal[seen=True risk=0.85 unseen=False risk=0.30]` reuses `risk`
    on purpose and `why`, `near`, `peak`, `staged` and `tightest` are short
    local names inside their own gates. Blocking a commit on those is rule 5's
    ratchet — a guard that cannot tell a fault from the format working.

    So the DETECTION lives here and the WARNING lives at the point of use:
    `gates.py --series <key>` is the tool that reads flat and file-wide, and
    it now says when a name is ambiguous instead of silently returning
    whichever match came first. Run this with `--collisions` to see the whole
    list.
    """
    seen = {}
    for n, line in enumerate(text.split("\n"), 1):
        if "=" not in line:
            continue
        if not any(k in line for k in ("SimDirector: ALL GATES:",
                                       "SimDirector: done.",
                                       "SimDirector: FAILING GATES:")):
            continue
        for m in re.finditer(r"(?<![\w])([A-Za-z][\w]*)=([^\s\]]+)", line):
            seen.setdefault(m.group(1), []).append((n, m.group(2)))
    out = []
    for key, hits in sorted(seen.items()):
        values = {v for _n, v in hits}
        if len(values) < 2:
            continue
        where = ", ".join(f"line {n}: {v}" for n, v in hits[:3])
        out.append(f"KEY COLLISION {key} has {len(values)} different "
                   f"values in one verdict — {where}")
    return out


# A LINE THAT MUST BE REJECTED AND A LINE THAT MUST BE ACCEPTED. Both are real
# shapes from real verdicts: the first is the emitter fault of 4 August that
# made this tool return `0.45(narrowest`, and the second is a nested gate group,
# which is the format working as intended and is what a naive lint flags forty
# times.
SELFTEST_BAD = "crowdBodyWidth=0.45(narrowest 0.39 broadest 0.53) crowdGap=0.41"
# AND THE PAIR FOR `spaced_values`, both lifted from real verdicts. The
# accepting one is a gate group (spaces legal inside `name[...]`) beside the
# repaired shapes of tonight's six keys; the rejecting one is `bodyAlbedo`
# exactly as it landed on 14f964a, which the lint above passes without a
# murmur.
SPACED_GOOD = ("frame[mean=471.0ms gameShare=3.23%] "
               "bodyAlbedo=[0.01/0.05/+13more/of29/vsWardrobeMax:0.46] "
               "gapWhy=[no-two-vehicles-shared-a-directed-edge-at-this-instant] "
               "massInRoad=[hook:x@0-over-1.5m/hook:z@0-over-1.5m] "
               "groundAlbedoBy=[asphalt:0.412/sidewalk:0.437] groundAlbedoOf=2/4")
SPACED_BAD = ("bodyAlbedo=[0.01 0.05 0.06 (+13 more) vs wardrobe max 0.46] "
              "crowdGap=0.41")
SELFTEST_GOOD = ("sky ok=True frame[mean=471.0ms gameShare=3.23% "
                 "ao[rounds=[28.1 18.0] drop=0.0123]] places=[alley=3 market=53] "
                 "crowdBodyWidth=0.45/0.39..0.53")


def selftest():
    """Run the lint against both outcomes and say which one failed.

    THE ACCEPTING ASSERTION IS FIRST, deliberately, copying `Tier2Gen
    --selftest`: the expensive failure mode for a validator is not that it
    misses something, it is that nothing survives it and the run lands nothing.
    """
    # WHICH RUN GETS READ, BOTH WAYS, BECAUSE MTIME LIED ONCE ALREADY.
    #
    # `run_stamp` reads the header the build wrote; the old version sorted by
    # file mtime, which is a property of this container's disk. A container
    # rollback plus the `git reset --hard` that repairs it rewrites every mtime
    # at once, and this function returned a run seventeen days stale while
    # presenting it as the newest answer.
    #
    # Rejecting case FIRST here because it is the one that regressed: a run
    # whose header is newer must win even when its file is the oldest on disk.
    ok = True
    if run_stamp_of_text("# Sim verdict — abc1234 @1787247881") != 1787247881:
        ok = False
        print("verdict-read --selftest: run stamp not read from the header")
    if run_stamp_of_text("# Sim verdict — abc1234") != 0:
        ok = False
        print("verdict-read --selftest: a header with no stamp must sort last, "
              "not crash or win")
    if not (run_stamp_of_text("# Sim verdict — a @1787247881")
            > run_stamp_of_text("# Sim verdict — b @1787003600")):
        ok = False
        print("verdict-read --selftest: newer header must outrank older header")

    good = lint_text(SELFTEST_GOOD)
    if good:
        ok = False
        print("verdict-read --selftest: FAILED THE CASE IT MUST ACCEPT — a "
              "well-formed line with nested gate groups was flagged:")
        for b in good:
            print("  " + b)
    bad = lint_text(SELFTEST_BAD)
    if not bad:
        ok = False
        print("verdict-read --selftest: FAILED THE CASE IT MUST REJECT — "
              "`crowdBodyWidth=0.45(narrowest 0.39 …)` passed, and that is the "
              "exact value this lint was written for.")
    # THE SPACED-VALUE HALF, ACCEPTING CASE FIRST for the same reason as above.
    sgood, sgoodn = spaced_values(SPACED_GOOD)
    if sgood or sgoodn != 4:
        ok = False
        print("verdict-read --selftest: FAILED THE CASE spaced_values MUST "
              "ACCEPT — %d flagged of %d bracketed values examined (expected "
              "0 of 4):" % (len(sgood), sgoodn))
        for n, k, v in sgood:
            print("  line %d: %s" % (n, v[:90]))
    sbad, sbadn = spaced_values(SPACED_BAD)
    if not sbad:
        ok = False
        print("verdict-read --selftest: FAILED THE CASE spaced_values MUST "
              "REJECT — `bodyAlbedo=[0.01 0.05 …]` passed, and that is the "
              "exact value that landed on 14f964a and read back as `[0.01`.")
    if ok:
        print("verdict-read --selftest: ok — rejects a swallowed space, "
              "accepts nested gate groups; spaced_values rejects %s "
              "(%d hit), accepts %d bracketed values in the good line"
              % (sbad[0][1] if sbad else "nothing", len(sbad), sgoodn))
    return 0 if ok else 2


def lint(run):
    """FLAG ANY VALUE THAT BREAKS THE VERDICT'S OWN FORMAT.

    The file is space-separated `key=value` and every reader assumes it. On
    4 August `crowdBodyWidth` was emitted as `0.45(narrowest 0.39 broadest
    0.53)` and this tool returned `0.45(narrowest` without a murmur — the exact
    class of quietly-wrong answer it exists to prevent, happening to itself.

    A RULE IN CLAUDE.md WOULD NOT HAVE STOPPED IT, because I wrote that value
    an hour after reading the rules that morning. This is the mechanism: an
    unbalanced bracket or parenthesis in what the reader took to be a value
    means a space was swallowed, and the run says so instead of the next person
    finding it by squinting at a number.
    """
    # THE FILE HAS TWO FORMATS AND THE FIRST VERSION OF THIS KNEW ONE.
    #
    # Top-level `key=value` pairs, AND bracketed gate groups —
    # `frame[mean=471.0ms gameShare=3.23%]` — where the whole bracket is one
    # value and spaces inside it are the format working as intended. Linting
    # without that produced forty-one hits, forty of them the last key inside a
    # group carrying the group's closing bracket. Rule 3, on a tool written to
    # enforce rule 3, found by running it before shipping it rather than after.
    #
    # So groups are removed first and what remains is the top level.
    bad = lint_text(run.read_text(encoding="utf-8", errors="replace"))
    if not bad:
        return 0
    print("verdict-read: %d value(s) with a space inside them — the file is "
          "space-separated key=value and every reader assumes it:" % len(bad))
    for b in bad:
        print("  " + b)
    return 2


def main():
    argv = sys.argv[1:]
    run = None
    if "--selftest" in argv:
        return selftest()
    if "--run" in argv:
        i = argv.index("--run")
        run = SHOTS / "runs" / f"{argv[i + 1]}.txt"
        del argv[i:i + 2]
    if "--file" in argv:
        # ANY VERDICT-SHAPED FILE, NOT ONLY THE UNITY ONES.
        #
        # This reader was wired to game-design/sim-shots because that was the
        # only place a verdict had ever been written. The UE probe now writes
        # one too, and the D1 question it exists to answer is precisely
        # whether the EXISTING readers keep working across the move. They
        # could not even be pointed at the file, which is a smaller finding
        # than a format incompatibility and would have read as the same
        # thing if nobody had tried it.
        #
        # The same-line rule and every refusal below are unchanged and apply
        # to whatever file is named. That is the part that had to survive.
        i = argv.index("--file")
        run = Path(argv[i + 1])
        if not run.exists():
            print("verdict-read: nothing measured — no file at %s" % run)
            return 2
        del argv[i:i + 2]
    if "--spaced" in argv:
        # NOT GATED, AND THAT IS DELIBERATE (rule 2: no bound before a series).
        # This prints the whole series off the newest measuring run so the
        # number can be set from evidence once a repaired verdict has landed.
        run = newest_measuring_run()
        if run is None:
            print("verdictSpaced=nothing-measured — no verdict with a run in it")
            return 0
        text = run.read_text(encoding="utf-8", errors="replace")
        hits, examined = spaced_values(text)
        print("# %s" % run.name)
        print("verdictSpaced=%d/%d  (values written `key=[..]` carrying a "
              "space, of bracketed values examined)" % (len(hits), examined))
        for n, k, v in hits[:20]:
            print("  line %-5d %s" % (n, v[:110]))
        if len(hits) > 20:
            print("  (+%d more not shown)" % (len(hits) - 20))
        return 0
    if "--lint" in argv:
        run = run or newest_measuring_run()
        if run is None or not run.exists():
            print("verdict-read: no run has measured anything — nothing to lint")
            return 0
        return lint(run)
    if "--collisions" in argv:
        run = run or newest_measuring_run()
        if run is None or not run.exists():
            print("verdict-read: no run has measured anything")
            return 0
        hits = collisions(run.read_text(encoding="utf-8", errors="replace"))
        print(f"verdict-read --collisions on {run.name}: "
              f"{len(hits)} name(s) carrying more than one value")
        for h in hits:
            print("  " + h)
        print("\n  Most of these are deliberate: a gate group is prose in "
              "brackets and\n  reuses short local names. What matters is a "
              "name somebody would ask\n  `gates.py --series` for — that tool "
              "reads flat and file-wide, and it\n  warns on its own now.")
        return 0

    keys = argv
    if not keys:
        print(__doc__.strip().split("\n\n")[1])
        return 2

    if run is None:
        run = newest_measuring_run()
    if run is None or not run.exists():
        print("verdict-read: no run has measured anything — nothing to read")
        return 1

    text = run.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    # WHERE EACH KEY IS, not just what it says. `key=` anchored on a word
    # boundary so `notoriety` does not match `notorietyPeak` — a substring hit
    # would reintroduce exactly the class of quiet wrong answer this exists to
    # stop, one layer down.
    found = {}
    for n, line in enumerate(lines, 1):
        for k in keys:
            # BRACKETS, PARENTHESES, OR A RUN OF NON-SPACE. A value with a
            # space in it breaks the verdict's own format, and this tool
            # returned the first word of one — `0.45(narrowest` — without a
            # murmur, which is exactly the silent-wrong-answer this file exists
            # to prevent. The emitter is fixed; this is the belt to its braces,
            # because the next person to write a value with a space in it will
            # not read this comment first.
            # AND THE FIRST FIX FOR IT DID NOT WORK, which is the point of
            # this line. Alternating whole-bracket-group OR non-space only
            # helps when the value STARTS with a bracket; `0.45(narrowest
            # 0.39 broadest 0.53)` starts with a digit, so `\S+` won the
            # race and returned `0.45(narrowest` again. A RUN of
            # either — brackets consumed whole, everything else
            # character by character — is what actually holds.
            m = re.search(r"(?<![\w])" + re.escape(k)
                          + r"=((?:\[[^\]]*\]|\([^)]*\)|[^\s\[\(])+)", line)
            if m:
                found.setdefault(k, []).append((n, m.group(1)))

    missing = [k for k in keys if k not in found]
    for k in missing:
        print(f"MISSING  {k}  — not in {run.name}")

    print(f"# {run.name}: {lines[0]}")
    for k in keys:
        for n, v in found.get(k, []):
            print(f"  line {n:>4}  {k}={v}")

    # THE WHOLE POINT. Two numbers from two lines are two readings, and the
    # only honest thing to do with them is refuse to put them side by side.
    where = {k: {n for n, _ in v} for k, v in found.items()}
    shared = set.intersection(*where.values()) if len(where) == len(keys) and where else set()
    if missing:
        return 1
    if len(keys) > 1 and not shared:
        print()
        print("NOT COMPARABLE: these keys never appear together on one line.")
        print("A verdict carries several log statements written at different")
        print("moments — the done line once at the end of the run, the glyphs")
        print("line on every screenshot. Peaks keep climbing between them, so")
        print("two values from two lines are two readings and their difference")
        print("means nothing. This is the exact mistake that cost 4 August an")
        print("afternoon and a deleted counter.")
        return 2
    if len(keys) > 1:
        print(f"\ncomparable: all {len(keys)} keys share line {sorted(shared)[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
