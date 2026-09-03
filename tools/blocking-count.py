#!/usr/bin/env python3
"""BLOCKING PUSHES PER WEEK. THE COUNTER SHIPS FIRST, THE THRESHOLD LATER.

    python3 tools/blocking-count.py              # the series, from the record
    python3 tools/blocking-count.py --selftest   # accepting case FIRST
    python3 tools/blocking-count.py --record F   # read another record

WHY THIS EXISTS AND WHY IT HAS NO GATE IN IT. Jafar ruled on 2026-09-03 that
more than two Blocking pushes in a week is a process fault to be investigated,
not a tolerance to raise. That is a bound, and this project's rule 2 says a
bound is read off a printed series and never chosen first: make the system
print the number, look at what it printed over real weeks, then set it. So
this prints the series and enforces NOTHING. The candidate bound is quoted at
the bottom of the report as a candidate, next to the number of weeks actually
recorded, which is the thing that decides whether it can be set yet.

WHAT IT READS. production/interrupt-log.tsv, the durable record every routed
interrupt appends to. Classes and routing: production/interrupt-classes.md.

NOTHING MEASURED IS NOT ZERO, and on the day this was written the record has
no rows at all, so the report says the words. A 0 would claim a week with no
Blocking pushes; an empty record claims a week nobody wrote down. Only one of
those is good news and they must never print the same.

TWO FIGURES, TWO MOMENTS, AND THEY DO NOT SHARE A LINE. Per-week numbers are
on the week's own line. Whole-record numbers (totals, the peak and the median
of the per-week series, the disputes) are on the done line, named for the
statistic they are: a peak answers "did it ever", a median answers "is this
normal", and a reader greping across two lines would otherwise read two
moments as one.

EXIT CODES, distinct per outcome. 0 a series was printed. 1 the selftest
failed. 2 the record could not be read at all (missing file, unreadable), which
is not a clean result. 3 the record exists and has NO ROWS: nothing measured.
Three is not a failure, it is the outcome that must not be confused with a
quiet week, and it is separate from 0 for exactly that reason.
"""
import argparse
import datetime
import importlib.util
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
RECORD = "production/interrupt-log.tsv"
CLASSES_DOC = "production/interrupt-classes.md"


def _load(path, name):
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:                                            # noqa: BLE001
        return None


_capsay = _load(REPO / "tools" / "capsay.py", "capsay")
if _capsay is None:
    sys.stderr.write("blocking-count: tools/capsay.py could not be imported; "
                     "refusing to print a capped series with no truncation "
                     "notice behind it\n")
    sys.exit(4)
cap, NOTHING = _capsay.cap, _capsay.NOTHING_MEASURED

# THE CLASSES, from the ruling. Anything outside this set is counted as
# unknown and NAMED, never folded into a bucket: an allow-list that silently
# drops what nobody thought of reads exactly like a clean result.
CLASSES = ["BLOCKING", "DECISION", "REVIEW", "FYI"]
DISPUTE_VALUES = ["none", "producer-said-blocking", "resident-said-blocking"]

# THE CANDIDATE BOUND, QUOTED AND NOT ENFORCED. It is here as a string so that
# grepping for the number finds this comment and not a comparison.
CANDIDATE_BOUND = ("Jafar 2026-09-03: more than two Blocking pushes in a week "
                   "is a process fault to be investigated, not a tolerance to "
                   "raise. NOT ENFORCED HERE and not a gate: the printed "
                   "series is what a bound gets read off")
WEEKS_SHOWN = 12        # the series cap. capsay announces when it bites.


def iso_week(d):
    """The ISO week label a date falls in. One implementation, used by the
    tally and by the selftest, so a fixture can never be labelled by a
    different rule from the live record."""
    y, w, _ = d.isocalendar()
    return "%04d-W%02d" % (y, w)


def parse(text):
    """PURE. (rows, unparsed) from the record's text.

    A row is date/class/channel/subject/dispute/link, tab separated. Comment
    lines and the header are skipped and counted separately. A row this cannot
    read is UNPARSED and is reported with its line number; it is never dropped,
    because a dropped row makes a busy week look like a quiet one.
    """
    rows, unparsed, skipped = [], [], 0
    for n, line in enumerate(text.splitlines(), 1):
        raw = line.rstrip("\n")
        if not raw.strip() or raw.lstrip().startswith("#"):
            skipped += 1
            continue
        cells = [c.strip() for c in raw.split("\t")]
        if cells and cells[0].lower() == "date":
            skipped += 1
            continue
        if len(cells) < 5:
            unparsed.append((n, "fewer than 5 tab-separated cells"))
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[0]):
            unparsed.append((n, "first cell is not an ISO date"))
            continue
        try:
            d = datetime.date.fromisoformat(cells[0])
        except ValueError:
            unparsed.append((n, "unreadable date"))
            continue
        rows.append({"date": d, "class": cells[1].upper(), "channel": cells[2],
                     "subject": cells[3], "dispute": cells[4],
                     "link": cells[5] if len(cells) > 5 else "-", "line": n})
    return rows, unparsed, skipped


def tally(rows):
    """PURE. The per-week series and the whole-record statistics.

    weeksRecorded counts weeks that HAVE a row. weeksSpanned counts the
    calendar weeks from the first row to the last, so the gap between the two
    is visible: a week with no row is a week nobody recorded, NOT a week with
    zero Blocking pushes, and the median below is over recorded weeks only.
    Saying which is the difference between "we are calm" and "nobody wrote
    anything down".
    """
    weeks = {}
    unknown = []
    for r in rows:
        w = iso_week(r["date"])
        bucket = weeks.setdefault(w, {c: 0 for c in CLASSES})
        bucket.setdefault("UNKNOWN", 0)
        bucket.setdefault("rows", 0)
        bucket.setdefault("disputed", 0)
        bucket["rows"] += 1
        if r["class"] in CLASSES:
            bucket[r["class"]] += 1
        else:
            bucket["UNKNOWN"] += 1
            unknown.append("line%d:%s" % (r["line"], r["class"] or "empty"))
        if r["dispute"] and r["dispute"] != "none":
            bucket["disputed"] += 1
    order = sorted(weeks)
    series = [(w, weeks[w]) for w in order]
    blocking = [weeks[w]["BLOCKING"] for w in order]
    peak_week, peak = ("", None)
    if blocking:
        peak = max(blocking)
        # THE DENOMINATOR AT THE INSTANT THE NUMERATOR PEAKS: the week that
        # held the peak travels with it as one value, never as a second key a
        # reader has to remember to pair up.
        peak_week = order[blocking.index(peak)]
    med = None
    if blocking:
        s = sorted(blocking)
        mid = len(s) // 2
        med = s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2.0
    spanned = None
    if rows:
        first, last = min(r["date"] for r in rows), max(r["date"] for r in rows)
        spanned = (last - first).days // 7 + 1
    return {"series": series, "weeksRecorded": len(order),
            "weeksSpanned": spanned, "blockingTotal": sum(blocking),
            "blockingPeak": peak, "blockingPeakWeek": peak_week,
            "blockingMedian": med, "unknown": unknown,
            "disputesTotal": sum(weeks[w]["disputed"] for w in order),
            "rows": len(rows)}


def fmt_week(w, b):
    """One week's line. PER-WEEK NUMBERS ONLY: nothing whole-record appears
    here, because a grep across lines would read the two moments as one."""
    return ("week=%s blocking=%d decision=%d review=%d fyi=%d unknownClass=%d "
            "disputed=%d rowsInWeek=%d"
            % (w, b["BLOCKING"], b["DECISION"], b["REVIEW"], b["FYI"],
               b.get("UNKNOWN", 0), b.get("disputed", 0), b["rows"]))


def fmt_done(t, unparsed, record_name, skipped):
    """The done line. WHOLE-RECORD NUMBERS ONLY, each named for the statistic
    it is. Values carry no spaces: the peak is value@position in one token."""
    if t["rows"] == 0:
        # DISPUTES GET THE WORDS TOO, not a 0. Nobody has recorded a
        # Producer-versus-resident disagreement about a class, and a 0 here
        # would claim agreement that was never observed.
        return ("blocking-count: blockingPerWeek=%s weeksRecorded=%s "
                "disputesTotal=%s rowsWalked=0 rowsUnparsed=%d nonRowLines=%d "
                "recordsRead=1 record=%s"
                % (NOTHING, NOTHING, NOTHING, len(unparsed), skipped,
                   record_name))
    disputes = ("%d" % t["disputesTotal"])
    peak = "%d@%s" % (t["blockingPeak"], t["blockingPeakWeek"])
    med = ("%g" % t["blockingMedian"])
    return ("blocking-count: blockingTotal=%d blockingPerWeekPeak=%s "
            "blockingPerWeekMedian=%s weeksRecorded=%d weeksSpanned=%s "
            "rowsWalked=%d rowsUnparsed=%d unknownClass=%d disputesTotal=%s "
            "recordsRead=1 record=%s"
            % (t["blockingTotal"], peak, med, t["weeksRecorded"],
               t["weeksSpanned"], t["rows"], len(unparsed), len(t["unknown"]),
               disputes, record_name))


def render(t, unparsed, record_name, skipped):
    """The whole report as lines. PURE, so the selftest reads what a run
    prints rather than a paraphrase of it."""
    out = []
    a = out.append
    a("blocking-count: the series, from %s" % record_name)
    a("")
    if t["rows"] == 0:
        a("  %s. The record exists and carries no rows: no interrupt has been "
          "routed through it yet, so no week has been recorded. This is NOT "
          "zero Blocking pushes in a week; it is no week measured."
          % NOTHING)
        a("  %d non-row line(s) (comments and the header) were read and "
          "skipped, %d line(s) could not be parsed." % (skipped, len(unparsed)))
        a("  Producer-versus-resident disagreements about what is Blocking: "
          "%s. The dispute column exists and no row has ever been written to "
          "it, so nothing has disagreed and nothing has agreed either."
          % NOTHING)
    else:
        shown = t["series"][-WEEKS_SHOWN:]
        for w, b in shown:
            a("  " + fmt_week(w, b))
        if len(t["series"]) > WEEKS_SHOWN:
            a("  " + cap(["%s" % w for w, _ in t["series"]],
                         keep=WEEKS_SHOWN, sep=","))
        gap = (t["weeksSpanned"] or 0) - t["weeksRecorded"]
        a("")
        a("  %d week(s) recorded of %s calendar week(s) spanned%s. A week with "
          "no row is a week NOBODY RECORDED, not a week with zero Blocking "
          "pushes, and the median below is over recorded weeks only."
          % (t["weeksRecorded"], t["weeksSpanned"],
             "" if gap <= 0 else ", so %d week(s) in the span carry no row at "
             "all" % gap))
        if t["unknown"]:
            a("  %d row(s) carry a class outside %s and are counted as "
              "unknownClass, never folded: %s"
              % (len(t["unknown"]), "/".join(CLASSES),
                 cap(t["unknown"], keep=4, sep=", ")))
        if t["disputesTotal"] == 0:
            a("  disputesTotal=0 over %d row(s) walked: the rows exist and "
              "none of them records a Producer-versus-resident disagreement "
              "about the class." % t["rows"])
    if unparsed:
        a("  %d unparsed row(s), reported rather than dropped: %s"
          % (len(unparsed), cap(["line%d:%s" % u for u in unparsed], keep=4,
                                sep=", ")))
    a("")
    a("  THE BOUND IS NOT SET AND IS NOT ENFORCED HERE.")
    a("  %s" % CANDIDATE_BOUND)
    a("  weeks available to read it off: %s"
      % (t["weeksRecorded"] if t["rows"] else NOTHING))
    a("")
    a(fmt_done(t, unparsed, record_name, skipped))
    return out


# ------------------------------------------------------------------- selftest

# THE ACCEPTING FIXTURE IS THE LIVE RECORD (it must parse, whatever it holds)
# plus this populated one, which exercises the arithmetic the live record
# cannot yet: two weeks, a peak, a median, a dispute. Synthetic, and its
# subjects exist nowhere, so doing the work this tool measures cannot break it.
POPULATED = """# comment line
date\tclass\tchannel\tsubject\tdispute\tlink
2026-08-31\tBLOCKING\tpush\tsynthetic-fixture-one\tnone\t-
2026-09-01\tBLOCKING\tpush\tsynthetic-fixture-two\tproducer-said-blocking\t-
2026-09-02\tDECISION\tbrief\tsynthetic-fixture-three\tnone\t-
2026-09-02\tFYI\tconsole\tsynthetic-fixture-four\tnone\t-
2026-09-08\tBLOCKING\tpush\tsynthetic-fixture-five\tnone\t-
2026-09-09\tREVIEW\tweekly\tsynthetic-fixture-six\tnone\t-
"""

# REJECTING FIXTURES, all synthetic. A class that exists nowhere, a row that
# cannot be read, and a record with no rows at all.
UNKNOWN_CLASS = ("date\tclass\tchannel\tsubject\tdispute\tlink\n"
                 "2026-09-01\tMARINATING\tpush\tsynthetic-nowhere\tnone\t-\n")
MALFORMED = ("date\tclass\tchannel\tsubject\tdispute\tlink\n"
             "2026-09-01\tBLOCKING\tpush\n"
             "not-a-date\tBLOCKING\tpush\tsynthetic\tnone\t-\n")
EMPTY = "# only comments\ndate\tclass\tchannel\tsubject\tdispute\tlink\n"


def selftest(repo=None):
    """Both outcomes, ACCEPTING CASE FIRST."""
    repo = pathlib.Path(repo or REPO)
    passed, failed = 0, []

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s\n         got: %s" % (name, got))

    print("blocking-count --selftest: ACCEPTING CASE FIRST\n")

    live = repo / RECORD
    ok("the live record exists at %s" % RECORD, live.is_file(), str(live))
    ltext = live.read_text(encoding="utf-8") if live.is_file() else ""
    lrows, lunp, lskip = parse(ltext)
    ok("the live record parses with no unparsed row (%d row(s), %d non-row "
       "line(s))" % (len(lrows), lskip), not lunp, lunp)
    ok("the classes doc it points at exists",
       (repo / CLASSES_DOC).is_file(), CLASSES_DOC)

    rows, unp, skip = parse(POPULATED)
    t = tally(rows)
    ok("a populated record counts 6 rows over 2 weeks",
       len(rows) == 6 and t["weeksRecorded"] == 2,
       (len(rows), t["weeksRecorded"]))
    ok("per-week Blocking counts are right (2 then 1)",
       [b["BLOCKING"] for _, b in t["series"]] == [2, 1],
       [(w, b["BLOCKING"]) for w, b in t["series"]])
    ok("the peak carries the week it happened in, as one value",
       t["blockingPeak"] == 2 and t["blockingPeakWeek"] == iso_week(
           datetime.date(2026, 8, 31)),
       (t["blockingPeak"], t["blockingPeakWeek"]))
    ok("the median is over recorded weeks only", t["blockingMedian"] == 1.5,
       t["blockingMedian"])
    ok("a dispute row is counted (1 of 6)", t["disputesTotal"] == 1,
       t["disputesTotal"])
    done = fmt_done(t, unp, "fixture", skip)
    ok("the done line names each statistic and its denominator",
       all(k in done for k in ("blockingPerWeekPeak=", "blockingPerWeekMedian=",
                               "weeksRecorded=", "rowsWalked=")), done)
    # THIS ASSERTION USED TO BE VACUOUS AND THAT IS WORTH THE COMMENT. It read
    # `all("=" not in tok or " " not in tok for tok in done.split())`, and
    # after splitting on whitespace NO TOKEN CAN CONTAIN A SPACE, so it was
    # true of every possible input including a broken one. A check that passes
    # by not looking, inside the instrument written to stop exactly that.
    # Found by a director reading it 2026-09-03. It now parses the line the way
    # a reader does: split on whitespace, and every token that carries an `=`
    # must have a non-empty value with nothing after it that a second split
    # would strand.
    toks = done.split()
    kv = [x for x in toks if "=" in x]
    ok("every key on the done line has a non-empty value, and no value is split",
       bool(kv) and all(x.split("=", 1)[1] != "" for x in kv)
       and " =" not in done and "= " not in done,
       "%d key=value token(s): %s" % (len(kv), done))
    weekline = fmt_week(*t["series"][0])
    ok("the week line carries per-week numbers and no whole-record one",
       "rowsInWeek=" in weekline and "weeksRecorded" not in weekline
       and "Total" not in weekline, weekline)

    print("\n  REJECTING FIXTURES, all synthetic:\n")
    rows, unp, skip = parse(EMPTY)
    t0 = tally(rows)
    text = "\n".join(render(t0, unp, "fixture", skip))
    ok("a record with no rows prints the words nothing measured, never 0",
       NOTHING in text and "blocking=0" not in text, text.splitlines()[:4])
    ok("and its done line carries the words too, with rowsWalked=0",
       NOTHING in fmt_done(t0, unp, "fixture", skip)
       and "rowsWalked=0" in fmt_done(t0, unp, "fixture", skip),
       fmt_done(t0, unp, "fixture", skip))
    ok("the disagreement figure is the WORDS when nothing records one",
       "disputesTotal=%s" % NOTHING in fmt_done(t0, unp, "fixture", skip)
       and "disputesTotal=0" not in fmt_done(t0, unp, "fixture", skip),
       fmt_done(t0, unp, "fixture", skip))

    rows, unp, skip = parse(UNKNOWN_CLASS)
    tu = tally(rows)
    ok("a class that exists nowhere is counted as unknownClass and named",
       len(tu["unknown"]) == 1 and tu["blockingTotal"] == 0,
       (tu["unknown"], tu["blockingTotal"]))
    ok("and it appears in the report rather than being folded away",
       any("unknownClass" in l for l in render(tu, unp, "fixture", skip)),
       render(tu, unp, "fixture", skip))

    rows, unp, skip = parse(MALFORMED)
    ok("a short row and a bad date are UNPARSED, reported, never dropped",
       len(rows) == 0 and len(unp) == 2, (len(rows), unp))
    ok("and the unparsed count reaches the done line",
       "rowsUnparsed=2" in fmt_done(tally(rows), unp, "fixture", skip),
       fmt_done(tally(rows), unp, "fixture", skip))

    # THE CAP MUST ANNOUNCE. 20 weeks of rows against a 12 week window.
    many = ["date\tclass\tchannel\tsubject\tdispute\tlink"]
    d = datetime.date(2026, 1, 5)
    for i in range(20):
        many.append("%s\tFYI\tconsole\tsynthetic-week-%d\tnone\t-"
                    % ((d + datetime.timedelta(days=7 * i)).isoformat(), i))
    rows, unp, skip = parse("\n".join(many))
    tm = tally(rows)
    text = "\n".join(render(tm, unp, "fixture", skip))
    ok("a series longer than the %d week window says the cap bit" % WEEKS_SHOWN,
       "more of 20" in text, [l for l in text.splitlines() if "more of" in l])

    ok("a real zero still ships its denominator (0 disputes over N rows)",
       any("disputesTotal=0 over" in l for l in
           render(tally(parse(POPULATED.replace("producer-said-blocking",
                                                "none"))[0]), [], "fixture", 2)),
       "")

    print("\nblocking-count --selftest: %s. %d passed, %d failed"
          % ("PASS" if not failed else "FAILED", passed, len(failed)))
    for f in failed:
        print("  " + f)
    return 0 if not failed else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    path = pathlib.Path(args.record) if args.record else REPO / RECORD
    if not path.is_file():
        print("blocking-count: %s, no record at %s. Nothing has been read, "
              "which is not the same as nothing having happened."
              % (NOTHING, path))
        return 2
    rows, unparsed, skipped = parse(path.read_text(encoding="utf-8",
                                                   errors="replace"))
    name = str(path.relative_to(REPO)) if str(path).startswith(str(REPO)) \
        else str(path)
    for line in render(tally(rows), unparsed, name, skipped):
        print(line)
    return 0 if rows else 3


if __name__ == "__main__":
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
