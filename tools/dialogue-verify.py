#!/usr/bin/env python3
"""Mechanical verification for dialogue banks (station 3 of the pipeline).

    python3 tools/dialogue-verify.py <bank.json>     # gate one bank
    python3 tools/dialogue-verify.py --selftest      # both outcomes

Three checks, each mechanical, each named in the spec that drives the bank.
Tone is deliberately absent: it belongs to the D7 judge after calibration,
and a tool pretending to measure tone would be a claim with no instrument.

1. RUNG DISCIPLINE. A line knows its relationship rung and may not address
   the player above it. stranger: no Novak, Tom or Toma. novak: no Tom or
   Toma as address. tom: no Toma. The check is word-boundary, case aware
   for the names, and it reads the RUNG ORDER from the bank file rather
   than carrying its own copy (one idea, one implementation).
2. REPETITION. No two lines whose token overlap (Jaccard, after stopword
   strip and lowercasing) reaches 0.6. The threshold came from reading the
   existing bark corpus, where near-twins are the first thing a player
   notices; it is a bound a future series can move, and the score of the
   worst pair is printed every run so that series exists.
3. LICENSE TAG. The bank carries a non-empty license field, because the
   license gate fails untagged content and a bank is content.

Every clean result prints its denominators: lines read, pairs compared.
"""
import itertools
import json
import pathlib
import re
import sys

NAMES = {"stranger": ["novak", "tom", "toma"],
         "novak": ["tom", "toma"],
         "tom": ["toma"]}
STOP = set("a an the and or but so of to in on at for with by from is are was were be "
           "you your he she it they we i me my his her its their this that there here "
           "then than as if not no yes do does did done have has had".split())


def tokens(text):
    return [w for w in re.findall(r"[a-z']+", text.lower()) if w not in STOP]


def check_bank(path, threshold=0.6):
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    lines = d["lines"]
    problems = []
    for ln in lines:
        banned = NAMES.get(ln["rung"], [])
        for name in banned:
            if re.search(r"\b" + name + r"\b", ln["text"], re.IGNORECASE):
                problems.append(f"RUNG: {ln['id']} ({ln['rung']}) addresses '{name}', "
                                f"a rung it does not have")
    worst = (0.0, None, None)
    pairs = 0
    for a, b in itertools.combinations(lines, 2):
        pairs += 1
        ta, tb = set(tokens(a["text"])), set(tokens(b["text"]))
        if not ta or not tb:
            continue
        j = len(ta & tb) / len(ta | tb)
        if j > worst[0]:
            worst = (j, a["id"], b["id"])
        if j >= threshold:
            problems.append(f"REPEAT: {a['id']} and {b['id']} overlap {j:.2f} "
                            f"(bound {threshold})")
    if not str(d.get("license", "")).strip():
        problems.append("LICENSE: the bank carries no license tag; the license "
                        "gate fails untagged content")
    for p in problems:
        print(f"  {p}")
    print(f"dialogue-verify: {'RED' if problems else 'clean'} - "
          f"{len(problems)} finding(s) over {len(lines)} line(s), {pairs} pair(s) "
          f"compared, worst overlap {worst[0]:.2f} ({worst[1]}/{worst[2]})")
    return 1 if problems else 0


def selftest():
    import tempfile, io, contextlib
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        ok, fail = (ok + 1, fail) if cond else (ok, fail + 1)
        print(f"  {'pass' if cond else 'FAIL'}  {name}  {detail if not cond else ''}")

    print("dialogue-verify selftest")
    print("-" * 60)
    with tempfile.TemporaryDirectory() as td:
        good = pathlib.Path(td) / "good.json"
        good.write_text(json.dumps({"license": "original-work", "lines": [
            {"id": "a1", "rung": "stranger", "context": "greeting",
             "text": "Evening. You will be the one that got the pub."},
            {"id": "a2", "rung": "tom", "context": "greeting",
             "text": "Tom! Get in out of the weather, the dominoes want a fourth."}]}))
        bad = pathlib.Path(td) / "bad.json"
        bad.write_text(json.dumps({"license": "", "lines": [
            {"id": "b1", "rung": "stranger", "context": "greeting",
             "text": "Evening Tom, nice to meet a total stranger."},
            {"id": "b2", "rung": "tom", "context": "greeting",
             "text": "The harbour wall is long and grey and cold tonight friend."},
            {"id": "b3", "rung": "tom", "context": "greeting",
             "text": "The harbour wall is long and grey and cold this evening friend."}]}))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check_bank(str(good))
        check("ACCEPTING: a clean two-line bank passes", rc == 0, buf.getvalue())
        check("accepting: denominators printed (lines, pairs, worst)",
              "pair(s) compared, worst overlap" in buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check_bank(str(bad))
        out = buf.getvalue()
        check("REJECTING: rung violation, near-twin and missing license all refuse",
              rc == 1 and "RUNG: b1" in out and "REPEAT: b2 and b3" in out
              and "LICENSE:" in out, out)
    print("-" * 60)
    print(f"  {ok} passed, {fail} failed")
    return 1 if fail else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    if len(sys.argv) < 2:
        print("usage: dialogue-verify.py <bank.json> | --selftest")
        sys.exit(2)
    sys.exit(check_bank(sys.argv[1]))
