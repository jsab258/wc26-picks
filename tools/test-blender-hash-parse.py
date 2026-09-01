#!/usr/bin/env python3
"""Run the Blender setup step's hash parse against fixtures, in real PowerShell.

WHY THIS EXISTS. The setup workflow downloads ~360 MB and decides whether to
unpack it from a hash it reads off download.blender.org. That decision has two
ways to be wrong and only one of them is loud:

  * it accepts nothing, prints `checksum=not-published`, and the download goes
    unverified for ever - which is what the MSI run of 1 Sep reported after
    reading a single URL;
  * it accepts the WRONG hash. Blender publishes one combined
    blender-<version>.sha256 per release, sha256sum format, a line per
    platform archive. A parse that greps the first 64 hex characters in that
    body returns the linux tarball's hash, compares it against the windows
    zip, and STOPS a perfectly good download with a MISMATCH it invented.

Neither is visible from the container this was written in: there is no Windows
and download.blender.org is blocked here. What IS checkable is the parse, and
the parse is the part with the branch in it.

IT RUNS THE SHIPPED TEXT, NOT A COPY. The function is pulled out of
tools/runner/setup-blender.ps1, so a change there that this file does not know
about cannot pass by being tested against a stale duplicate. One idea, one
implementation.

IT USED TO READ THE WORKFLOW YAML, and that sentence is corrected rather than
quietly edited: the step outgrew GitHub's dispatch ceiling on 1 Sep and its
411 lines moved into that script. An extractor pointed at the old location
would have found nothing, and "found nothing" is why the failure below is
loud.

WHAT IT DOES NOT CHECK: whether download.blender.org actually serves either
file, whether the zip exists, or anything about extraction. Those need the
network and a Windows runner, and the first dispatch is their accepting case.
"""
import importlib.util
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ps-check.py has a hyphen in its name, so it is loaded by path rather than
# imported. What is reused from it is pwsh(), which knows to look in the dotnet
# tools directory as well as on PATH - one implementation of "where is
# PowerShell", not two.
_spec = importlib.util.spec_from_file_location("pscheck", ROOT / "tools" / "ps-check.py")
ps_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ps_check)

SCRIPT = ROOT / "tools" / "runner" / "setup-blender.ps1"
FUNC = "Get-PublishedHash"

WANT = "blender-4.5.13-windows-x64.zip"
ZIPHASH = "a" * 64
LINUXHASH = "b" * 64
COMBINED = (
    "%s  blender-4.5.13-linux-x64.tar.xz\n"
    "%s  blender-4.5.13-windows-x64.zip\n"
    "%s  blender-4.5.13-macos-arm64.dmg\n" % (LINUXHASH, ZIPHASH, "c" * 64))
PERFILE = "%s  %s\n" % (ZIPHASH, WANT)
BARE = "  %s  \n" % ZIPHASH
HTML404 = ("<html><head><title>404 Not Found</title></head><body>"
           "<p>id %s not here</p></body></html>" % ("d" * 64))

CASES = [
    # (label, body, expected, why this case exists)
    ("ACCEPTING: the combined per-release file picks OUR archive's line",
     COMBINED, ZIPHASH,
     "a first-64-hex grep would return the linux hash and invent a mismatch"),
    ("ACCEPTING: a per-file .sha256 in sha256sum format",
     PERFILE, ZIPHASH, "the shape the MSI run went looking for"),
    ("ACCEPTING: a per-file .sha256 that is a bare hash",
     BARE, ZIPHASH, "some mirrors publish the hash with no filename"),
    ("REJECTING: a 404 page with 64 hex characters mid-sentence",
     HTML404, "", "an unanchored match would treat an error page as a hash"),
    ("REJECTING: an empty body",
     "", "", "nothing read must not read as a hash"),
    ("REJECTING: the combined file with no line for our archive",
     "%s  blender-4.5.13-linux-x64.tar.xz\n" % LINUXHASH, "",
     "the wanted file is absent, so the answer is nothing, not the neighbour"),
]


def extract_function():
    """The function's text, straight out of the script that ships it."""
    if not SCRIPT.exists():
        return None, "the script that ships the parse is not at %s" % SCRIPT
    lines = SCRIPT.read_text(encoding="utf-8").split("\n")
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^(\s*)function\s+%s\b" % FUNC, ln):
            start = i
            break
    if start is None:
        return None, ("%s exists but declares no `function %s`" % (SCRIPT.name, FUNC))
    indent = len(lines[start]) - len(lines[start].lstrip())
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == "}" and (len(lines[j]) - len(lines[j].lstrip())) == indent:
            return "\n".join(lines[start:j + 1]), None
    return None, "found `function %s` but no closing brace at its indentation" % FUNC


def main():
    exe = ps_check.pwsh()
    if not exe:
        print("blender-hash-parse: NO POWERSHELL, so 0 of %d fixture(s) ran. "
              "Install it with: dotnet tool install --global PowerShell" % len(CASES))
        return 1
    func, err = extract_function()
    if func is None:
        print("blender-hash-parse: COULD NOT READ THE SHIPPED FUNCTION - %s" % err)
        print("  0 of %d fixture(s) ran. This is a failure, not a skip: the "
              "test cannot silently stop covering the parse." % len(CASES))
        return 1

    scratch = ROOT / "ledger" / ".ps-check"
    scratch.mkdir(exist_ok=True)
    script = scratch / "hash-parse.ps1"
    body = [func, ""]
    for i, (_, fixture, _, _) in enumerate(CASES):
        lit = fixture.replace("'", "''")
        body.append("$b%d = @'\n%s\n'@" % (i, lit))
        body.append("Write-Output (\"RESULT%d=\" + (%s $b%d '%s'))" % (i, FUNC, i, WANT))
    script.write_text("\n".join(body) + "\n", encoding="utf-8")
    r = subprocess.run([exe, "-NoProfile", "-File", str(script)],
                       capture_output=True, text=True)
    got = dict(re.findall(r"^RESULT(\d+)=(.*)$", r.stdout, re.M))
    script.unlink(missing_ok=True)

    ok = fail = 0
    for i, (label, _, expect, why) in enumerate(CASES):
        actual = got.get(str(i))
        if actual is None:
            fail += 1
            print("  FAIL %s (the fixture produced no RESULT line)" % label)
            continue
        if actual.strip() == expect:
            ok += 1
            print("  ok   %s" % label)
        else:
            fail += 1
            print("  FAIL %s\n         expected %r, got %r - %s"
                  % (label, expect, actual.strip(), why))
    if r.returncode != 0 and fail == 0:
        print("  note: pwsh exited %d; stderr: %s" % (r.returncode, r.stderr.strip()[:200]))
    print("blender-hash-parse: %d ok, %d failed, %d fixture(s) run against the "
          "function extracted from %s" % (ok, fail, len(CASES), SCRIPT.name))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
