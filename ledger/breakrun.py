#!/usr/bin/env python3
"""Reintroduce a defect, watch the test go red, put the source back.

    python3 breakrun.py breaks/framing.json

A test that has never been seen to fail is a claim, not a check. This runs
each break in a spec, rebuilds, and reports whether CoreTests caught it. A
break that SURVIVES is the interesting result: it means the check passes
whether or not the thing works.

Spec format -- a JSON list of objects:

    [{"name": "what defect this is, in words",
      "file": "Assets/Scripts/Core/Framing.cs",
      "old":  "exact text to replace, must appear exactly once",
      "new":  "the broken version"}]

TWO TRAPS THIS HARNESS EXISTS TO AVOID, both of which cost real work:

  **The restore must survive every exit.** An earlier ad-hoc version was
  piped through `head`, took SIGPIPE before its restore line, and left a
  deliberate break sitting in the tree. Hence atexit plus an on-disk
  backup rather than a restore at the bottom of the loop.

  **atexit is not enough on its own.** `atexit` runs on a normal exit and
  on SIGINT, and NOT on SIGTERM -- which is what `timeout` sends. A run
  wrapped in `timeout 120` that overran left a deliberate break sitting in
  the tree, and the next run refused to start because its own baseline was
  red. The failure is self-diagnosing, which is the only reason it cost
  minutes rather than an evening. Hence the explicit signal handlers below.

  **The restore must not preserve mtime.** `shutil.copy2` copies the
  timestamp too, so the restored file looks OLDER than the object files
  built from the broken one -- MSBuild skips the rebuild and the next test
  run executes the BROKEN binary against restored source. That failure
  looks like a mystery regression in code you are staring at and can see
  is correct. `copyfile` plus an explicit touch, everywhere.
"""
import atexit
import json
import os
import shutil
import signal
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
_backups = {}


def _restore_one(path):
    bak = _backups.get(path)
    if bak and os.path.exists(bak):
        shutil.copyfile(bak, path)   # NOT copy2 -- see the module docstring
        os.utime(path, None)
        os.remove(bak)


def restore_all():
    for path in list(_backups):
        _restore_one(path)


atexit.register(restore_all)


def _restore_and_die(signum, _frame):
    """SIGTERM and friends do NOT run atexit handlers.

    `timeout 120 python3 breakrun.py ...` sends SIGTERM, Python dies without
    unwinding, and a deliberate break stays in the working tree. Re-raising
    with the default disposition after restoring keeps the exit status honest
    for whatever is watching."""
    restore_all()
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


for _sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
    try:
        signal.signal(_sig, _restore_and_die)
    except (ValueError, AttributeError):
        pass        # not on this platform, or not the main thread


def back_up(path):
    if path not in _backups:
        bak = path + ".breakbak"
        shutil.copyfile(path, bak)
        _backups[path] = bak


def revert(path):
    shutil.copyfile(_backups[path], path)
    os.utime(path, None)


def run_tests(project):
    p = subprocess.run(["dotnet", "run", "--project", project, "-c", "Release", "--nologo"],
                       cwd=ROOT, capture_output=True, text=True)
    out = p.stdout + p.stderr
    return out, [l.strip() for l in out.splitlines() if l.strip().startswith("FAILED")]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    spec = json.load(open(sys.argv[1]))
    project = sys.argv[2] if len(sys.argv) > 2 else "CoreTests"

    for b in spec:
        back_up(os.path.join(ROOT, b["file"]))

    # A break run only means something against a green baseline: if the tests
    # are already red, every break "goes red" and none of it is evidence.
    out, fails = run_tests(project)
    if fails or "error CS" in out:
        print("BASELINE IS NOT GREEN -- nothing below would mean anything:")
        for f in fails[:5]:
            print("   " + f)
        return 2

    survivors = 0
    for b in spec:
        path = os.path.join(ROOT, b["file"])
        revert(path)
        text = open(path).read()
        n = text.count(b["old"])
        if n != 1:
            print(f"?? ANCHOR MATCHES {n}x, expected 1: {b['name']}")
            survivors += 1
            continue
        with open(path, "w") as fh:
            fh.write(text.replace(b["old"], b["new"]))
        os.utime(path, None)

        out, fails = run_tests(project)
        if "error CS" in out:
            print(f"-- will not compile, which is its own kind of caught: {b['name']}")
        elif fails:
            print(f"RED       {b['name']}")
            print(f"            {fails[0][:150]}")
        else:
            print(f"SURVIVED  {b['name']}")
            survivors += 1

    restore_all()
    print(f"\n{len(spec)} breaks, {survivors} survived")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
