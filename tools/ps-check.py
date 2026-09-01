#!/usr/bin/env python3
"""Parse every `shell: pwsh` step in the workflows with PowerShell's own parser.

WHY THIS EXISTS. The Windows workflow is the only channel that can tell me
anything about the game, and twice now a shell mistake inside it has taken that
channel out rather than the thing it was checking:

  * a bash step used `nullglob` on a literal path, so `cp` always ran, died
    under `-e` on the first build that rendered no contact sheet, and took the
    verdict AND the COMPILE ERRORS block with it;
  * the Verdict step printed "no failing gates" for a run whose *checkout*
    failed — no repository, no Unity, no sim — because the placeholder written
    for exactly that case only ever reached a variable nobody printed.

Both were found from the outside, hours later, by reading a build that had
already been wasted. Neither needed Unity, a runner, or Windows to find: the
first is shell semantics and the second is four lines of branch logic.

The blocker was always that nothing here could RUN PowerShell. It turns out
`dotnet tool install --global PowerShell` works in this container in about
twenty seconds, which makes every pwsh step in the workflow locally parseable —
so a step that cannot even be parsed stops being something a twenty-eight
minute round trip discovers.

WHAT IT CHECKS, AND WHAT IT DOES NOT. This is a PARSE, not an execution: it
catches unbalanced braces, a broken string, a malformed pipeline — the class
that kills a step outright. It cannot catch a step that runs and does the wrong
thing; that needs a fixture, and the Verdict step has one (see --selftest).

`${{ ... }}` is a GitHub expression, not PowerShell, and is substituted for a
quoted placeholder before parsing — otherwise every step using one would be a
false positive and the check would have to be switched off, which is how checks
die.

AND IF PWSH IS ABSENT IT SAYS SO RATHER THAN PASSING. A checker that cannot run
must not be indistinguishable from a checker that ran and found nothing — that
is rule 3b, and it is the reason this prints the number of steps parsed.
"""

import argparse
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FLOWS = ROOT / ".github" / "workflows"

# STANDALONE SCRIPTS A WORKFLOW CALLS, named rather than globbed.
#
# THIS LIST EXISTS BECAUSE A MOVE CAN DELETE COVERAGE SILENTLY. The Blender
# setup was a `shell: pwsh` step and was parsed here every run. On 1 Sep it
# outgrew GitHub's dispatch ceiling (25,259 chars against a measured 23,184)
# and its 411 lines moved into a file - and the moment they did, this sweep
# stopped seeing them while still reporting "0 problems". Nothing about that
# reads as a loss: the count goes DOWN by one step and every remaining step
# still passes. A shell mistake in that file would then reach the runner
# exactly as the two faults in this tool's docstring did.
#
# Named and not globbed, for the reason lint-bootstrap-single names its
# workflows: adding a script to the sweep should be a decision somebody made,
# and a missing entry here is then a visible omission rather than a glob that
# quietly matched nothing.
SCRIPTS = ("tools/runner/setup-blender.ps1",)

# dotnet puts its global tools here and it is not on PATH by default in a
# fresh container, so look for it directly before giving up.
EXTRA_PATH = pathlib.Path.home() / ".dotnet" / "tools"

# A GitHub expression is not PowerShell. Substituted rather than stripped, so
# `if (${{ inputs.x }} -eq 1)` stays a syntactically complete sentence.
EXPR = re.compile(r"\$\{\{[^}]*\}\}")

PARSE = r"""
$src = [System.IO.File]::ReadAllText($args[0])
$errors = $null
[void][System.Management.Automation.Language.Parser]::ParseInput(
    $src, [ref]$null, [ref]$errors)
if ($errors) {
  foreach ($e in $errors) {
    Write-Output ("{0}:{1}: {2}" -f $e.Extent.StartLineNumber,
                                   $e.Extent.StartColumnNumber, $e.Message)
  }
  exit 1
}
exit 0
"""


def sweep(scratch, *files):
    """Remove the scratch files, tolerating a nested call having got there
    first — selftest() calls check(), and both used to rmdir the same
    directory, so the second one died on a directory that was already gone."""
    for f in files:
        f.unlink(missing_ok=True)
    try:
        scratch.rmdir()
    except FileNotFoundError:
        pass
    except OSError:
        pass                      # something else is in it; leave it alone


def pwsh():
    """The pwsh executable, or None. Checks the dotnet tools dir too."""
    found = shutil.which("pwsh")
    if found:
        return found
    candidate = EXTRA_PATH / "pwsh"
    return str(candidate) if candidate.exists() else None


def steps(path):
    """Every (name, body) for a step declaring `shell: pwsh` in one workflow.

    Hand-rolled rather than via a YAML library, for the same reason
    workflow-steps.py is: the run block is a literal scalar whose indentation
    IS the content, and a round trip through a YAML loader has already been
    observed to normalise it. What ships is what gets parsed.
    """
    out = []
    lines = path.read_text(encoding="utf-8").split("\n")
    i = 0
    while i < len(lines):
        if not re.match(r"^\s*- name: ", lines[i]):
            i += 1
            continue
        name = lines[i].split("- name:", 1)[1].strip()
        indent = len(lines[i]) - len(lines[i].lstrip())
        # Walk this step's keys, looking for `shell: pwsh` and `run: |`.
        j, is_pwsh, body, run_indent = i + 1, False, None, None
        while j < len(lines):
            cur = lines[j]
            if cur.strip() and (len(cur) - len(cur.lstrip())) <= indent:
                break
            if re.match(r"^\s*shell:\s*pwsh\s*$", cur):
                is_pwsh = True
            m = re.match(r"^(\s*)run:\s*\|", cur)
            if m:
                run_indent = len(m.group(1)) + 2
                collected, k = [], j + 1
                while k < len(lines):
                    nxt = lines[k]
                    if nxt.strip() and (len(nxt) - len(nxt.lstrip())) < run_indent:
                        break
                    collected.append(nxt[run_indent:] if len(nxt) >= run_indent else "")
                    k += 1
                body = "\n".join(collected)
                j = k - 1
            j += 1
        if is_pwsh and body is not None:
            out.append((name, body))
        i = j
    return out


def check(verbose=True):
    """Parse every pwsh step. Returns (steps_parsed, [problem strings]).

    Callers must ask pwsh() themselves before trusting a zero — see main(),
    which had this exact bug: --quiet suppressed the NO POWERSHELL line, so a
    container without PowerShell reported "0 steps parsed, 0 problems" and
    verify.py wrote it into the footer as a pass. The docstring at the top of
    this file warns about precisely that, and the warning was written the same
    hour the bug was. One idea, two implementations, and the one nobody looks
    at is the one missing a line."""
    exe = pwsh()
    if not exe:
        return 0, []

    scratch = ROOT / "ledger" / ".ps-check"
    scratch.mkdir(exist_ok=True)
    parser = scratch / "parse.ps1"
    parser.write_text(PARSE, encoding="utf-8")

    parsed, problems = 0, []
    target = scratch / "step.ps1"

    def parse_one(label, text):
        nonlocal parsed
        parsed += 1
        target.write_text(EXPR.sub("'__gh_expr__'", text), encoding="utf-8")
        r = subprocess.run([exe, "-NoProfile", "-File", str(parser), str(target)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            for line in r.stdout.strip().split("\n"):
                problems.append(f"{label} :: {line}")
        elif verbose:
            print(f"  ok   {label} ({len(text.splitlines())} lines)")

    for flow in sorted(FLOWS.glob("*.yml")):
        for name, body in steps(flow):
            parse_one(f"{flow.name} :: {name}", body)
    # A NAMED SCRIPT THAT IS NOT THERE IS A PROBLEM, never a quiet skip: the
    # whole point of the list is that its entries stop being parsed the moment
    # somebody moves or renames one, and that must be said out loud.
    scripts = 0
    for rel in SCRIPTS:
        path = ROOT / rel
        if not path.exists():
            problems.append(f"{rel} :: NAMED IN ps-check.SCRIPTS BUT NOT ON DISK")
            continue
        scripts += 1
        parse_one(rel, path.read_text(encoding="utf-8"))
    sweep(scratch, parser, target)
    return parsed, problems


def selftest():
    """BOTH WAYS (rule 5b), and the accepting case is first on purpose.

    The expensive failure mode for a checker like this is not missing a bug —
    it is rejecting everything, being switched off, and taking its own reason
    for existing with it.
    """
    exe = pwsh()
    if not exe:
        print("ps-check --selftest: no pwsh, so neither case was run.")
        return 1

    scratch = ROOT / "ledger" / ".ps-check"
    scratch.mkdir(exist_ok=True)
    parser = scratch / "parse.ps1"
    parser.write_text(PARSE, encoding="utf-8")
    target = scratch / "step.ps1"

    def parse(text):
        target.write_text(EXPR.sub("'__gh_expr__'", text), encoding="utf-8")
        return subprocess.run([exe, "-NoProfile", "-File", str(parser), str(target)],
                              capture_output=True, text=True)

    checks, bad = 0, []

    # ACCEPTING — ordinary PowerShell, and a GitHub expression in the middle of
    # it, which is the shape that would make a naive checker unusable.
    for good in ('if ($x) { Write-Host "hi" } else { Write-Host "no" }',
                 'if ("${{ inputs.days }}" -eq "11") { Write-Host ok }',
                 '$a = @(); $a += 1; $a | ForEach-Object { Write-Host $_ }'):
        checks += 1
        if parse(good).returncode != 0:
            bad.append(f"rejected valid PowerShell: {good[:48]}")

    # REJECTING — an unclosed brace and an unterminated string, the two that
    # actually kill a step.
    for broken in ('if ($x) { Write-Host "hi"',
                   'Write-Host "unterminated'):
        checks += 1
        if parse(broken).returncode == 0:
            bad.append(f"accepted broken PowerShell: {broken[:48]}")

    # AND THE REAL WORKFLOW, which is the best accepting case available: every
    # step in it is shipping today, so a hit here is a false positive by
    # definition (the same argument the lint-* tools are built on).
    parsed, problems = check(verbose=False)
    checks += 1
    if problems:
        bad.extend(problems)
    if parsed == 0:
        bad.append("parsed zero steps — the extractor found nothing to check")

    sweep(scratch, parser, target)

    if bad:
        for b in bad:
            print(f"  FAIL {b}")
        return 1
    print(f"ps-check ok ({checks} checks, {parsed} workflow step(s) parsed)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    # THE ABSENCE IS PRINTED WHATEVER --quiet SAYS. A checker that could not
    # run must never be summarised as one that ran and found nothing, and the
    # verbosity flag is not allowed a say in that.
    if not pwsh():
        print("ps-check: NO POWERSHELL — nothing was parsed, which is not the "
              "same as nothing being wrong.")
        print("  dotnet tool install --global PowerShell   # ~20s, then retry")
        return 2

    parsed, problems = check(verbose=not a.quiet)
    if parsed == 0:
        print("ps-check: NO POWERSHELL STEPS FOUND — the extractor matched "
              "nothing, which is a fault in this tool, not a clean workflow.")
        return 1
    if problems:
        for p in problems:
            print(f"  FAIL {p}")
        print(f"ps-check — {len(problems)} problem(s) in {parsed} step(s)")
        return 1
    # The count stays the THIRD token of this line: ledger/verify.py reads it
    # positionally and prints it into the commit footer.
    print(f"ps-check — {parsed} pwsh block(s) parsed "
          f"({parsed - len(SCRIPTS)} workflow step(s), {len(SCRIPTS)} named "
          f"script(s)), 0 problems")
    return 0


if __name__ == "__main__":
    sys.exit(main())
