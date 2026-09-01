#!/usr/bin/env python3
"""The mechanical canon gate (ledger-v2/studio-v2/verification.md, gate 1).

    python3 tools/canon-gate.py <file> [file...]     # gate the named files
    python3 tools/canon-gate.py --selftest           # both outcomes

WHAT IT CHECKS, and what it deliberately does not. canon.md holds three
classes of fact. Era artifacts and banned modernity are MECHANICAL: a line
containing a mobile phone or the internet is wrong in 1988 to 1992 no matter
how well written, so a grep can refuse it. Real brands are mechanical the
same way, reusing the imagegen forbidden-token list so there is one list,
not two (one idea, one implementation). TONE IS NOT MECHANICAL and is not
checked here: the D3 register needs the D7 judge, which needs Jafar's
calibration sample. A tool that pretended to check tone would be a claim
with no instrument, which is the exact thing the constitution forbids.

Every refusal names the file, the line number and the word, because a gate
whose red cannot be acted on teaches people to read red as noise. Every
clean result ships its denominator (rule 3b): files and lines examined.

FALSE-POSITIVE DISCIPLINE, learned 26 Aug on this repo: `british rail`
matched inside `British railway sign` and the fix was to reword the prose,
never to loosen the guard. A trade-mark guard that errs toward refusing is
erring the right way. The same holds here: a legitimate sentence ABOUT the
ban ("no mobiles in ordinary pockets" in canon itself) will trip the gate,
so canon.md and the decision register are EXEMPT BY NAME below, and the
exemption is printed whenever it bites.
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

#: Words that cannot exist in 1988-1992 Meridian content. Word-boundary
#: matched, case-insensitive. Each entry names its reason so a refusal
#: teaches rather than scolds.
MODERNITY = {
    "mobile phone": "no mobiles in ordinary pockets (canon, Era)",
    "cell phone": "no mobiles (canon, Era); and 'cell phone' is American",
    "smartphone": "no mobiles (canon, Era)",
    "internet": "no internet (canon, Era)",
    "website": "no internet (canon, Era)",
    "email": "no internet (canon, Era); letters and phone calls",
    "wifi": "no internet (canon, Era)",
    "texted": "no SMS in the window (canon, Era); pagers exist for dealers",
    "text message": "no SMS in the window (canon, Era)",
    "social media": "no internet (canon, Era)",
    "selfie": "no camera phones (canon, Era); one camcorder in town",
    "google": "no internet (canon, Era), and a real brand besides",
    "cctv everywhere": "CCTV is rare: the bank, the off-licence (canon, Era)",
}

#: Paths whose text may legitimately DISCUSS banned things: the law itself,
#: the decisions that made it, and this tool.
EXEMPT = ("canon.md", "ledger-v2/", "legacy/", "tools/canon-gate.py",
          "production/queue/README.md", ".claude/agents/")


def forbidden_brands():
    """The imagegen forbidden-token list, read from the one place it lives.
    An empty list is a FAILURE here, not a pass: a brand gate with no brands
    would wave everything through and look identical to a clean run."""
    p = REPO / "tools" / "imagegen" / "prompts.json"
    toks = json.loads(p.read_text(encoding="utf-8"))["content_rules"]["forbidden_tokens"]
    if not toks:
        raise SystemExit("canon-gate: the forbidden-token list is EMPTY; refusing to run")
    return toks


def gate(paths):
    brands = forbidden_brands()
    checked_files = checked_lines = 0
    hits = []
    exempt_bitten = []
    for path in paths:
        p = pathlib.Path(path)
        rel = str(p.resolve()).replace(str(REPO) + "/", "")
        if any(rel.startswith(e) for e in EXEMPT):
            exempt_bitten.append(rel)
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        checked_files += 1
        for n, line in enumerate(text.splitlines(), 1):
            checked_lines += 1
            low = line.lower()
            for word, why in MODERNITY.items():
                if re.search(r"\b" + re.escape(word) + r"\b", low):
                    hits.append((rel, n, word, why))
            for tok in brands:
                t = tok.strip()
                # WORD-BOUNDED, NOT SUBSTRING, and the difference is one real
                # incident each way. Substring caught 'british rail' inside
                # 'British railway' (26 Aug): annoying, harmless, reword the
                # prose. But substring 'bt ' (British Telecom) matches inside
                # 'debts ', and this is a crime game about a book of
                # uncollectable debts: the guard would ban the premise. The
                # trailing spaces in the imagegen token list were always a
                # crude boundary; this makes the boundary real. The imagegen
                # scanner keeps its own substring semantics for prompts,
                # where 'debt' does not occur; the divergence is named here
                # so nobody unifies them back into the broken shape.
                if t and re.search(r"\b" + re.escape(t) + r"\b", low):
                    hits.append((rel, n, t, "real brand (canon: Brands and law)"))
    for rel in exempt_bitten:
        print(f"  exempt by name, not examined: {rel}")
    for rel, n, word, why in hits:
        print(f"  CANON: {rel}:{n} contains '{word}' - {why}")
    verdict = "RED" if hits else "clean"
    print(f"canon-gate: {verdict} - {len(hits)} finding(s) in {checked_files} file(s), "
          f"{checked_lines} line(s) examined, {len(MODERNITY)} era term(s) and "
          f"{len(brands)} brand token(s) screened")
    return 1 if hits else 0


def selftest():
    import tempfile
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        ok, fail = (ok + 1, fail) if cond else (ok, fail + 1)
        print(f"  {'pass' if cond else 'FAIL'}  {name}  {detail if not cond else ''}")

    print("canon-gate selftest")
    print("-" * 60)
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        good = td / "good.md"
        good.write_text("June leaves a message with the barman. The phone box "
                        "on Quay Street takes tens. Mickey's opens at eleven.\n")
        bad = td / "bad.md"
        bad.write_text("Tom checks his mobile phone.\nShe looks it up on the internet.\n"
                       "A crate of Guinness in the cellar.\n")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_good = gate([str(good)])
        check("ACCEPTING: a clean late-analog paragraph passes", rc_good == 0, buf.getvalue())
        check("accepting: the clean result carries its denominator",
              "line(s) examined" in buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_bad = gate([str(bad)])
        out = buf.getvalue()
        check("REJECTING: mobile phone, internet and a real brand all refuse",
              rc_bad == 1 and out.count("CANON:") == 3, out)
        check("rejecting: every refusal names file, line and reason",
              "bad.md:1" in out and "bad.md:2" in out and "bad.md:3" in out)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_canon = gate([str(REPO / "canon.md")])
        check("EXEMPTION: canon.md itself is exempt BY NAME and says so",
              rc_canon == 0 and "exempt by name" in buf.getvalue())
        debt = td / "debt.md"
        debt.write_text("Mickey left a book of uncollectable debts. No doubt "
                        "the rent is late too.\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_debt = gate([str(debt)])
        check("BOUNDARY: 'debts' and 'doubt' pass, the premise is not a brand",
              rc_debt == 0, buf.getvalue())
        bt = td / "bt.md"
        bt.write_text("He rang from the BT box on the corner.\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_bt = gate([str(bt)])
        check("BOUNDARY: 'BT' alone still refuses", rc_bt == 1, buf.getvalue())
    print("-" * 60)
    print(f"  {ok} passed, {fail} failed")
    return 1 if fail else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    if len(sys.argv) < 2:
        print("usage: canon-gate.py <file> [file...] | --selftest")
        sys.exit(2)
    sys.exit(gate(sys.argv[1:]))
