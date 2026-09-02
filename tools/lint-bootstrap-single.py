#!/usr/bin/env python3
"""One idea, one implementation: the self-hosted PATH bootstrap.

WHY THIS EXISTS. That bootstrap was inline in the workflows, and the task
that queued the dedup said it existed TWICE. It existed three times, and the
third copy was a SHORTENED variant missing the diagnostic messages that are
the only part a person acts on. That is the shape this project has a
standing rule about: one idea, two implementations, and the one nobody looks
at is the one missing a line. Nobody looked at the third at all.

WHAT IT ASSERTS, and it is two things rather than one:
  every workflow that needs the bootstrap CALLS the shared script; and
  no workflow contains an inline copy of it.

Either alone is insufficient. A workflow can call the script AND keep a
stale inline block above it, which is how a dedup half-lands.

WHAT IT DOES NOT ASSERT. Whether the script works. That is the runner's job
and the acceptance criterion for it is a green dispatch of BOTH workflows,
not a green lint here. A lint cannot tell you a PATH was set on a machine
it has never seen.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF = os.path.join(REPO, ".github", "workflows")
SCRIPT = os.path.join("tools", "runner", "bootstrap-paths.cmd")
CALL = re.compile(r"call\s+tools[\\/]runner[\\/]bootstrap-paths\.cmd", re.I)

# The tells of an inline copy. Any one of them in a workflow means the
# block is still there: they are the lines only that bootstrap has.
INLINE_TELLS = (
    'echo C:\\Program Files\\Git\\bin',
    "NO pwsh ON THIS MACHINE",
    "NO bash ON THIS MACHINE",
    ":pwshok",
    ":bashok",
)

# Workflows that run on the self-hosted agent need it. Named rather than
# guessed, so adding a workflow is a deliberate decision here.
NEEDS = ("ledger-build-windows.yml", "ledger-probe-unreal.yml",
         "ledger-setup-msvc.yml",
         # The fourth job on `ledger-pc`, 2 Sep: the D1b vignette CC0
         # surface fetch. Named here in the same change that adds the
         # workflow, because a self-hosted workflow this list does not
         # know about is one the lint cannot hold to the shared script.
         "ledger-vignette-fetch.yml")


def scan(wf_dir=WF, needs=NEEDS, repo=REPO):
    problems = []
    present = sorted(f for f in os.listdir(wf_dir) if f.endswith((".yml", ".yaml")))
    if not os.path.exists(os.path.join(repo, SCRIPT)):
        problems.append("the shared script %s does not exist" % SCRIPT)
    calls = 0
    for f in present:
        text = open(os.path.join(wf_dir, f), encoding="utf-8").read()
        has_call = bool(CALL.search(text))
        inline = [t for t in INLINE_TELLS if t in text]
        if has_call:
            calls += 1
        if f in needs and not has_call:
            problems.append("%s runs on the self-hosted agent but does not call %s" % (f, SCRIPT))
        if inline:
            problems.append("%s still contains an inline copy of the bootstrap (found %s)"
                            % (f, ", ".join(repr(t) for t in inline[:2])))
    return problems, present, calls


def selftest():
    """Accepting case first: the live workflows ARE the accepting fixture."""
    import tempfile
    ok = fail = 0

    def check(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print("  FAIL %s" % name)

    probs, present, calls = scan()
    check("ACCEPTING: today's workflows are clean", probs == [])
    check("ACCEPTING: something was actually examined", len(present) > 0 and calls > 0)

    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "tools", "runner"))
        open(os.path.join(d, SCRIPT), "w").write("rem\n")
        wf = os.path.join(d, "wf")
        os.makedirs(wf)
        good = "steps:\n  run: |\n    call tools\\runner\\bootstrap-paths.cmd\n"
        open(os.path.join(wf, "a.yml"), "w").write(good)
        check("ACCEPTING: a workflow that only calls the script passes",
              scan(wf, ("a.yml",), d)[0] == [])

        # REJECTING 1: calls the script AND keeps an inline copy. This is
        # the half-landed dedup, and the case a call-only check would miss.
        open(os.path.join(wf, "a.yml"), "w").write(good + "    :pwshok\n")
        check("rejecting: a leftover inline copy beside the call",
              scan(wf, ("a.yml",), d)[0] != [])

        # REJECTING 2: a workflow that needs it and does not call it.
        open(os.path.join(wf, "a.yml"), "w").write("steps:\n  run: echo hi\n")
        check("rejecting: a self-hosted workflow with no call",
              scan(wf, ("a.yml",), d)[0] != [])

        # REJECTING 3: the shared script itself missing.
        os.remove(os.path.join(d, SCRIPT))
        open(os.path.join(wf, "a.yml"), "w").write(good)
        check("rejecting: the shared script is gone",
              any("does not exist" in p for p in scan(wf, ("a.yml",), d)[0]))

    print("lint-bootstrap-single selftest: %d ok, %d failed" % (ok, fail))
    return 1 if fail else 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    problems, present, calls = scan()
    for p in problems:
        print("  PROBLEM " + p)
    print("bootstrap-single: %s — %d workflow(s) read, %d call the shared script, "
          "%d named as needing it, %d problem(s)"
          % ("ok" if not problems else "RED", len(present), calls, len(NEEDS), len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
