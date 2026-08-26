#!/usr/bin/env python3
"""EVERY CAP ANNOUNCES ITSELF — the one implementation, imported, not copied.

    from capsay import cap, NOTHING_MEASURED

WHY IT IS ITS OWN FILE.

Swept on 26 August: `ledger/verify.py` held **50 red-path messages that
truncate their finding list, and 2 of them carried a count**. So 48 red lines
read identically whether the run had one fault or forty. The worked example is
`verdict_keys`: it kept four key names and dropped the number, while
`tools/verdict-keys.py` one process boundary underneath was already printing
"N measurement(s) STOPPED BEING REPORTED". A run losing 4 measurements and a
run losing 40 produced the same sentence.

That is CLAUDE.md's own `| head -3` incident — a filter that outgrew its input,
showed three of seventeen character lines, and was read as *"three of the five
bodies failed to produce a prefab"* when nothing was broken — happening 48
times inside the tool that enforces the rule against it.

The reason it is a MODULE rather than a helper in each tool is the other rule
this project keeps paying for: one idea, two implementations, and the one
nobody looks at is the one missing a line. `SpeechBubble`'s billboard aim and
`NpcWalker`'s identical maths; `verdict-keys` and `gates.py` counting the same
blanks two ways; `TightestGap` and the job trace written an hour apart with the
same 3D-vs-flat mismatch. A truncation notice that exists twice will one day
say `(+N more)` in one tool and nothing in the other, and the tool that says
nothing is the one somebody reads.

A ZERO STILL NEEDS ITS DENOMINATOR (rule 3b), so the empty case does not
return "" — it returns `NOTHING_MEASURED`, whose text is the words "nothing
measured" with no space in it, because every channel in this project is
split on whitespace and truncates silently when a value contains one.

    python3 tools/capsay.py --selftest      # accepting case first
"""
import sys

# NO SPACES. The verdict file and the verify footer are both `key=value`
# channels split on whitespace, and `crowdBodyWidth=0.45(narrowest 0.39 ...)`
# once came back as `0.45(narrowest` with nothing saying it had been cut.
NOTHING_MEASURED = "nothing-measured"

TRUNC = "..."        # ASCII: this text reaches Windows CI consoles too


def cap(items, keep=1, width=90, sep="; ", tail=NOTHING_MEASURED, strip=0,
        last=False):
    """`keep` of `items`, each capped at `width` characters, and ALWAYS the
    count of what the cap ate.

        ["a", "b", "c"], keep=1   ->  "a (+2 more of 3)"
        ["a"],           keep=1   ->  "a"
        [],                       ->  tail  (default: the words, not a blank)

    A cap that did NOT bite prints no clause — a truncation notice on an
    untruncated list is its own kind of lie, and would train readers to skip
    the clause that matters.

    `strip` drops a fixed leading prefix from each kept item; a dozen callers
    wrote `bad[0][8:98]` to skip one. `last=True` reads from the END of the
    list, which several callers did deliberately because the tool underneath
    prints its summary after its detail. Both are arguments rather than
    slices at the call site, because a slice at the call site is exactly how
    48 sites came to drop their count.

    THE COUNT IS OF `items` AS HANDED IN, and of nothing else. If a caller
    slices before calling, this can only report the slice — so callers pass
    the whole list and let this do the cutting. That is the whole contract.
    """
    if not items:
        return tail
    seq = list(items)
    chosen = seq[-keep:] if last else seq[:keep]
    shown = []
    for it in chosen:
        s = str(it)[strip:]
        shown.append(s[:width] + (TRUNC if len(s) > width else ""))
    text = sep.join(shown)
    dropped = len(seq) - len(chosen)
    if dropped > 0:
        text += " (+%d more of %d)" % (dropped, len(seq))
    return text


def selftest(fn=None):
    """Both outcomes watched, ACCEPTING FIRST.

    Rule 5b: the expensive failure is a validator nothing survives, so the
    first assertions here are the cases this must let through untouched — a
    list that fits, a single item, a prefix stripped — and only then the cases
    where the clause must appear. A version that asserted only "the clause
    appears" would pass a `cap` that stamped `(+0 more of 1)` on everything.
    """
    # THE SUITE ITSELF NEEDS A REJECTING CASE, or it is a validator nothing
    # survives one layer up: a suite that cannot go red proves nothing when it
    # is green. `--broken` runs these same assertions against a `cap` that
    # never announces its truncation — the exact fault this module exists to
    # stop — and the suite must fail on it. The accepting fixture is the real
    # `cap`; the rejecting one is synthetic and lives nowhere else, so doing
    # the work this module prompts can never break the test.
    cap_ = fn or cap
    ok, bad = 0, []

    def want(label, got, expect):
        nonlocal ok
        if got == expect:
            ok += 1
            print("  ok   %-46s %r" % (label, got))
        else:
            bad.append("%s: got %r, wanted %r" % (label, got, expect))
            print("  FAIL %-46s %r  wanted %r" % (label, got, expect))

    print("capsay selftest — ACCEPTING CASES FIRST (a cap that bites on")
    print("everything is the validator nothing survives)\n")

    # ---- ACCEPTING: the cap must not bite, and must not say it did.
    want("one item, keep=1 — no clause", cap_(["only one"]), "only one")
    want("two items, keep=4 — no clause",
         cap_(["a", "b"], keep=4, sep=", "), "a, b")
    want("item shorter than width — no ellipsis",
         cap_(["short"], width=90), "short")
    want("strip removes the tool's own prefix",
         cap_(["  FAIL: boom"], strip=8), "boom")
    want("exactly at width — no ellipsis", cap_(["x" * 10], width=10), "x" * 10)

    # ---- REJECTING: the cap bit, and must say so with the denominator.
    want("four items, keep=1", cap_(["a", "b", "c", "d"]),
         "a (+3 more of 4)")
    want("five items, keep=4",
         cap_(["a", "b", "c", "d", "e"], keep=4, sep=", "),
         "a, b, c, d (+1 more of 5)")
    want("last=True reads from the end",
         cap_(["a", "b", "c"], last=True), "c (+2 more of 3)")
    want("one char over width", cap_(["x" * 11], width=10), "x" * 10 + TRUNC)

    # ---- NEVER MEASURED: must not read as clean, must not read as empty.
    want("empty list gives the words", cap_([]), NOTHING_MEASURED)
    want("empty list, caller's own words",
         cap_([], tail="did not report"), "did not report")
    want("the words carry no space", " " in NOTHING_MEASURED, False)

    print("\n%d passed, %d failed" % (ok, len(bad)))
    for b in bad:
        print("  " + b)
    return 1 if bad else 0


def _never_announces(items, keep=1, width=90, sep="; ", tail=NOTHING_MEASURED,
                     strip=0, last=False):
    """THE REJECTING FIXTURE: the fault as it stood in 48 places on 26 Aug —
    the first item, correctly sliced, and not one word about the rest."""
    if not items:
        return tail
    seq = list(items)
    chosen = seq[-keep:] if last else seq[:keep]
    return sep.join(str(i)[strip:][:width] for i in chosen)


if __name__ == "__main__":
    # A correct run that ends in a BrokenPipeError traceback costs twenty
    # minutes before anybody notices it worked.
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    if "--broken" in sys.argv:
        # MUST GO RED. Exit 0 here means the suite cannot see the fault.
        rc = selftest(_never_announces)
        print("\n--broken: the suite %s the un-announcing cap"
              % ("REFUSED" if rc else "ACCEPTED — THE SUITE IS BLIND"))
        sys.exit(0 if rc else 1)
    sys.exit(selftest())
