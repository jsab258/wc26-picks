#!/usr/bin/env python3
"""One idea, one implementation: the self-hosted PATH bootstrap.

WHY THIS EXISTS. That bootstrap was inline in the workflows, and the task
that queued the dedup said it existed TWICE. It existed three times, and the
third copy was a SHORTENED variant missing the diagnostic messages that are
the only part a person acts on. That is the shape this project has a
standing rule about: one idea, two implementations, and the one nobody looks
at is the one missing a line. Nobody looked at the third at all.

WHY IT WAS REWRITTEN, 2026-09-09, AND THE FAULT WAS THIS FILE'S OWN
DENOMINATOR. The Mickey's blockout render was dispatched at 13:29:35Z on
f08b5351 and died in twelve seconds on one line, `pwsh: command not found`,
in the first pwsh step of ledger-art-blender-preview.yml. That workflow was
the one self-hosted workflow of nine that did not call the shared script,
and it was also the one this file's hand-written NEEDS tuple did not name,
so the lint printed `0 problem(s)` about it on every commit of its life.
The zero was honest and useless: ITS DENOMINATOR COUNTED THE HAND LIST AND
NOT THE SET THAT MATTERS, which is the failure mode rule 3b exists for. The
old docstring even said the risk out loud, that a self-hosted workflow the
list does not know about is one the lint cannot hold to the shared script,
and saying it is not catching it.

SO THE HAND LIST'S ROLE IS INVERTED. The set that needs the bootstrap is
DERIVED from the workflows: a job whose `runs-on` names `self-hosted` and
which runs at least one step under pwsh or bash (or under the runner's
default shell, which on Windows is pwsh). The hand list that remains,
EXEMPT, is a list of deliberate exemptions, each carrying a written reason.
The question a reader has to answer changes from "did somebody remember to
add this workflow" to "did somebody write down why this one does not need
it", and only the second question is answerable by looking.

WHAT IT ASSERTS, and it is four things rather than one:
  every workflow DERIVED as needing the bootstrap calls the shared script,
    or is exempted with a written reason;
  no workflow contains an inline copy of it;
  every exemption still describes a workflow that needs it, so a stale
    exemption cannot quietly become a hole; and
  the derivation still sees the nine workflows already known to run on
    `ledger-pc` (DERIVATION_FLOOR), so a regression in the parser below
    cannot read as a clean tree.

Either of the first two alone is insufficient. A workflow can call the
script AND keep a stale inline block above it, which is how a dedup
half-lands.

WHAT IT DOES NOT ASSERT. Whether the script works, or that a PATH was set.
That is the runner's job, and the acceptance criterion for it is a green
dispatch on the PC, not a green lint here. A lint cannot tell you a PATH
was set on a machine it has never seen.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF = os.path.join(REPO, ".github", "workflows")
SCRIPT = os.path.join("tools", "runner", "bootstrap-paths.cmd")

# THE CALL, AND NOT A MENTION OF IT. The trailing guard is why this is not
# the bare search it used to be: ledger-setup-msvc.yml already carries the
# script's path inside a comment, and a commented-out example call in a
# workflow would otherwise read as that workflow calling it.
CALL = re.compile(r"call\s+tools[\\/]runner[\\/]bootstrap-paths\.cmd", re.I)

# The tells of an inline copy. Any one of them in a workflow means the
# block is still there: they are the lines only that bootstrap has. This
# one reads the RAW text on purpose, inline copies living inside `run: |`
# blocks, which the structural reader below deliberately skips.
INLINE_TELLS = (
    'echo C:\\Program Files\\Git\\bin',
    "NO pwsh ON THIS MACHINE",
    "NO bash ON THIS MACHINE",
    ":pwshok",
    ":bashok",
)

# The shells that need the bootstrap: both are absent from this runner's
# stock PATH, which is the whole reason the script exists.
NEEDING_SHELLS = ("pwsh", "bash")

# DELIBERATE EXEMPTIONS, each with a written reason. Empty today, 9 Sep
# 2026: all nine self-hosted workflows call the script. An entry here is a
# claim that a self-hosted workflow does not need the PATH bootstrap, so it
# carries the argument, not just the file name. An entry whose workflow the
# derivation does not flag is reported as stale rather than left standing.
EXEMPT = {
    # "example-workflow.yml": "why this self-hosted workflow needs no pwsh "
    #                         "and no bash, in a sentence",
}

# THE FLOOR UNDER THE DERIVATION, which is the old NEEDS tuple kept for the
# one job a hand list is actually good at: catching a parser that stopped
# seeing things. These nine were each measured as self-hosted on 9 Sep
# 2026. If the derivation stops naming one that is still present, the
# DERIVER is broken and not the tree (rule 3, suspect the instrument
# first). When a workflow genuinely moves off the agent, delete its line
# here in the same change.
DERIVATION_FLOOR = (
    "ledger-art-blender-preview.yml",
    "ledger-build-windows.yml",
    "ledger-imagegen.yml",
    "ledger-install-supervisor-task.yml",
    "ledger-mesh-import.yml",
    "ledger-probe-unreal.yml",
    "ledger-restart-telegram-bot.yml",
    "ledger-setup-msvc.yml",
    "ledger-vignette-fetch.yml",
)

_BLOCK = re.compile(r"^[|>][0-9]*[-+]?\s*(#.*)?$")
_KEY = re.compile(r"^(?P<key>[A-Za-z_][A-Za-z0-9_.\-]*)\s*:(?:\s+(?P<val>.*))?$")


def structural(text):
    """Yield (lineno, indent, key_or_None, text) for every line that is
    YAML
    STRUCTURE, skipping blanks, comments and the contents of block scalars.

    THE BLOCK SCALARS ARE THE POINT. The `run: |` blocks in this repository
    contain the words `shell: bash`, `self-hosted` and `runs-on` in prose,
    in comments and in heredocs, and a plain grep reads a sentence about a
    step as a step. ledger-build-windows.yml line 83 is exactly that
    sentence. Indentation is the only thing that tells them apart, so this
    reader tracks it and nothing downstream greps raw text for structure.
    """
    block_owner = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.replace("\t", "    ").rstrip()
        indent = len(line) - len(line.lstrip(" "))
        bare = line.strip()
        if block_owner is not None:
            if bare == "" or indent > block_owner:
                continue
            block_owner = None
        if bare == "" or bare.startswith("#"):
            continue
        # A sequence item can open a mapping on its own line (`- name: x`),
        # and the mapping's indentation is the column of the key, not of
        # the dash.
        eff = indent
        while bare == "-" or bare.startswith("- "):
            nxt = bare[1:].lstrip()
            eff += len(bare) - len(nxt)
            bare = nxt
            if bare == "":
                break
        m = _KEY.match(bare)
        if not m:
            yield (lineno, eff, None, bare)
            continue
        key = m.group("key")
        val = (m.group("val") or "").strip()
        if _BLOCK.match(val):
            block_owner = eff
            val = ""
        yield (lineno, eff, key, val)


def jobs_of(text):
    """Every job in one workflow, as what this lint needs to know about it.

    Returns a list of dicts: name, labels (the runs-on text as written),
    shells (every declared shell), runSteps, and bareRunSteps (run steps
    that declared no shell, which inherit the runner default: pwsh on
    Windows, so they count as needing it).
    """
    jobs = []
    in_jobs = False
    jobs_indent = None
    cur = None
    collecting = None  # indent of a runs-on whose value continues below
    for lineno, eff, key, val in structural(text):
        if not in_jobs:
            if key == "jobs" and eff == 0:
                in_jobs = True
            continue
        if eff == 0:
            break  # the next top-level key ends the jobs block
        if jobs_indent is None:
            jobs_indent = eff
        if eff == jobs_indent and key is not None:
            cur = {"name": key, "labels": None, "shells": [], "runSteps": 0}
            jobs.append(cur)
            collecting = None
            continue
        if cur is None:
            continue
        if collecting is not None:
            if eff > collecting:
                # A block sequence item or a wrapped flow list: the label
                # text continues on the lines deeper than the runs-on key.
                piece = val if key is None else "%s: %s" % (key, val)
                cur["labels"] = ((cur["labels"] or "") + " " + piece).strip()
                continue
            collecting = None
        if key == "runs-on":
            cur["labels"] = val
            if not val:
                collecting = eff  # a block sequence or a wrapped flow list
        elif key == "shell":
            cur["shells"].append(val.strip().strip('"').strip("'").lower())
        elif key == "run":
            cur["runSteps"] += 1
    for j in jobs:
        j["bareRunSteps"] = max(0, j["runSteps"] - len(j["shells"]))
    return jobs


def classify(jobs):
    """What one workflow's jobs make it, with the reason in words."""
    selfhosted = []
    unresolved = []
    for j in jobs:
        labels = j["labels"]
        has_steps = j["runSteps"] > 0 or bool(j["shells"])
        if labels is None:
            # A job with no runs-on and no run steps is a reusable-workflow
            # call and runs nothing here; with run steps it is unreadable.
            if has_steps:
                unresolved.append(j["name"])
            continue
        if (("${{" in labels or not labels.strip()
             or labels.strip().startswith("*")) and has_steps):
            # An expression, a YAML alias, or a runs-on whose value this
            # reader could not collect. Either way it cannot say self-hosted
            # or not, and fail-open is exactly how today's silence happened.
            unresolved.append(j["name"])
            continue
        if re.search(r"self-hosted", labels, re.I):
            selfhosted.append(j)
    needing = []
    for j in selfhosted:
        kinds = sorted(set(s for s in j["shells"] if s in NEEDING_SHELLS))
        if kinds:
            needing.append((j["name"], "+".join(kinds)))
        elif j["bareRunSteps"] > 0:
            needing.append((j["name"], "default-shell-on-%d-bare-run-step(s)"
                            % j["bareRunSteps"]))
    return selfhosted, needing, unresolved


def calls_in(text):
    """Real call lines only: a `#` before the match makes it a mention."""
    n = 0
    for line in text.splitlines():
        m = CALL.search(line)
        if m and "#" not in line[:m.start()]:
            n += 1
    return n


def scan(wf_dir=WF, repo=REPO, exempt=EXEMPT, floor=DERIVATION_FLOOR):
    problems = []
    try:
        present = sorted(f for f in os.listdir(wf_dir)
                         if f.endswith((".yml", ".yaml")))
    except OSError as e:
        return {"problems": ["the workflow directory %s cannot be read (%s)"
                             % (wf_dir, e.__class__.__name__)],
                "read": [], "jobs": 0, "selfhosted": [], "needing": {},
                "calling": [], "exempted": [], "unresolved": [], "inline": []}
    if not os.path.exists(os.path.join(repo, SCRIPT)):
        problems.append("the shared script %s does not exist" % SCRIPT)
    jobs_total = 0
    selfhosted = []   # (wf, jobname)
    needing = {}      # wf -> [(jobname, why)]
    calling = []
    unresolved = []   # (wf, jobname)
    inline = []
    for f in present:
        text = open(os.path.join(wf_dir, f), encoding="utf-8").read()
        jobs = jobs_of(text)
        jobs_total += len(jobs)
        sh, need, unres = classify(jobs)
        selfhosted += [(f, j["name"]) for j in sh]
        unresolved += [(f, n) for n in unres]
        if need:
            needing[f] = need
        if calls_in(text):
            calling.append(f)
        tells = [t for t in INLINE_TELLS if t in text]
        if tells:
            inline.append((f, tells))
        if not jobs and re.search(r"^jobs\s*:", text, re.M):
            problems.append("%s declares jobs but this lint read none out of "
                            "it, so its classification is nothing measured" % f)
    for f, tells in inline:
        shown = ", ".join(repr(t) for t in tells[:2])
        more = ("" if len(tells) <= 2
                else " (+%d more not shown)" % (len(tells) - 2))
        problems.append("%s still contains an inline copy of the bootstrap "
                        "(found %s%s)" % (f, shown, more))
    exempted = []
    for f in sorted(needing):
        if f in calling:
            continue
        reason = (exempt.get(f) or "").strip()
        if f in exempt and reason:
            exempted.append(f)
            continue
        if f in exempt:
            problems.append("%s is exempted with no written reason, which is "
                            "a hole with a name on it; write the reason or "
                            "call %s" % (f, SCRIPT))
            continue
        why = ", ".join("job=%s/%s" % (n, w) for n, w in needing[f])
        problems.append("%s needs the bootstrap (%s) but does not call %s and "
                        "is not exempted" % (f, why, SCRIPT))
    for f in sorted(exempt):
        if f not in present:
            problems.append("the exemption for %s names no workflow in %s; "
                            "delete the exemption" % (f, wf_dir))
        elif f not in needing:
            problems.append("the exemption for %s is stale: the derivation "
                            "does not find a self-hosted pwsh or bash job in "
                            "it, so the reason no longer applies" % f)
        elif f in calling:
            problems.append("%s is both exempted and calling %s; delete the "
                            "exemption" % (f, SCRIPT))
    for f in floor:
        if f in present and f not in needing:
            problems.append("%s is in DERIVATION_FLOOR but the derivation no "
                            "longer finds a self-hosted pwsh or bash job in "
                            "it; either the parser regressed or the workflow "
                            "moved off the agent and the floor line goes with "
                            "it" % f)
    for f, j in unresolved:
        problems.append("%s job %s has a runs-on this lint cannot resolve, so "
                        "it cannot be held to the shared script; nothing "
                        "measured for that job" % (f, j))
    if not present:
        problems.append("no workflow files in %s; nothing measured" % wf_dir)
    return {"problems": problems, "read": present, "jobs": jobs_total,
            "selfhosted": selfhosted, "needing": needing, "calling": calling,
            "exempted": exempted, "unresolved": unresolved, "inline": inline}


def report(r):
    """The census first, then the verdict. Every zero with its denominator."""
    need = sorted(r["needing"])
    need_and_call = [f for f in need if f in r["calling"]]
    bare = sum(1 for f in need for n, w in r["needing"][f]
               if w.startswith("default-shell"))
    if not r["read"]:
        print("bootstrap-single census: 0 workflow(s) read, nothing measured")
    else:
        print("bootstrap-single census: %d workflow(s) read, %d job(s) in "
              "them, %d job(s) on self-hosted of %d, %d workflow(s) derived "
              "as needing the bootstrap of %d read, %d job(s) needing it only "
              "by the runner default shell, %d job(s) with a runs-on this "
              "lint cannot resolve of %d"
              % (len(r["read"]), r["jobs"], len(r["selfhosted"]), r["jobs"],
                 len(need), len(r["read"]), bare, len(r["unresolved"]),
                 r["jobs"]))
    print("bootstrap-single: %s - %d workflow(s) read, %d call the shared "
          "script, %d named by derivation as needing it, %d/%d needing it "
          "call it, %d/%d exempted with a written reason, %d inline copy(ies) "
          "in %d read, %d problem(s)"
          % ("ok" if not r["problems"] else "RED", len(r["read"]),
             len(r["calling"]), len(need), len(need_and_call), len(need),
             len(r["exempted"]), len(need), len(r["inline"]), len(r["read"]),
             len(r["problems"])))


def _fixture(d, name, body, script=True):
    wf = os.path.join(d, "wf")
    os.makedirs(wf, exist_ok=True)
    if script and not os.path.exists(os.path.join(d, SCRIPT)):
        os.makedirs(os.path.join(d, "tools", "runner"), exist_ok=True)
        open(os.path.join(d, SCRIPT), "w").write("rem\n")
    open(os.path.join(wf, name), "w").write(body)
    return wf


CALL_STEP = """      - name: tool PATH bootstrap (self-hosted parity)
        shell: cmd
        run: |
          call tools\\runner\\bootstrap-paths.cmd
          exit /b %ERRORLEVEL%
"""


def _wf(runs_on="[self-hosted, ledger-pc]", shell="pwsh", call=False,
        extra="", run_body="          echo hi\n"):
    return ("name: fixture\non:\n  workflow_dispatch:\njobs:\n  j:\n"
            "    runs-on: %s\n    steps:\n%s      - name: a step\n"
            "        shell: %s\n        run: |\n%s%s"
            % (runs_on, CALL_STEP if call else "", shell, run_body, extra))


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

    r = scan()
    check("ACCEPTING: today's workflows are clean", r["problems"] == [])
    check("ACCEPTING: something was actually examined",
          len(r["read"]) > 0 and len(r["calling"]) > 0 and r["jobs"] > 0)
    check("ACCEPTING: the derivation found every floor workflow",
          all(f not in r["read"] or f in r["needing"] for f in DERIVATION_FLOOR))
    check("ACCEPTING: the derivation is not just the floor list",
          len(r["needing"]) >= len(DERIVATION_FLOOR))

    with tempfile.TemporaryDirectory() as d:
        wf = _fixture(d, "a.yml", _wf(call=True))
        check("ACCEPTING: self-hosted pwsh workflow that calls the script",
              scan(wf, d, {}, ())["problems"] == [])

        # ACCEPTING: the negative side of the derivation. A hosted runner
        # brings its own pwsh and bash, so demanding the call there would
        # be a false problem, and a lint that fails on the clean case gets
        # switched off.
        wf = _fixture(d, "a.yml", _wf(runs_on="ubuntu-latest", shell="bash"))
        check("ACCEPTING: an ubuntu workflow with a bash step needs nothing",
              scan(wf, d, {}, ())["problems"] == []
              and scan(wf, d, {}, ())["needing"] == {})

        # ACCEPTING: prose inside a `run:` block is prose. This is the case
        # a grep-based deriver gets wrong, and ledger-build-windows.yml has
        # the sentence for real.
        wf = _fixture(d, "a.yml", _wf(
            runs_on="ubuntu-latest",
            run_body="          # every `shell: pwsh` step on [self-hosted] died\n"
                     "          echo 'runs-on: [self-hosted, ledger-pc]'\n"))
        got = scan(wf, d, {}, ())
        check("ACCEPTING: self-hosted named inside a run block is not a job",
              got["problems"] == [] and got["selfhosted"] == [])

        # ACCEPTING: an exemption with a written reason.
        wf = _fixture(d, "a.yml", _wf())
        check("ACCEPTING: exempted with a reason passes",
              scan(wf, d, {"a.yml": "cmd only on this one, by measurement"},
                   ())["problems"] == [])

        # REJECTING 1: calls the script AND keeps an inline copy. This is
        # the half-landed dedup, and the case a call-only check would miss.
        wf = _fixture(d, "a.yml", _wf(call=True, extra="          :pwshok\n"))
        check("rejecting: a leftover inline copy beside the call",
              scan(wf, d, {}, ())["problems"] != [])

        # REJECTING 2: TODAY'S FAULT. Self-hosted, a pwsh step, no call,
        # no exemption. The old lint passed this unless a human had put the
        # file name in a tuple.
        wf = _fixture(d, "a.yml", _wf())
        got = scan(wf, d, {}, ())
        check("rejecting: a self-hosted pwsh workflow with no call",
              got["problems"] != [] and any("a.yml needs the bootstrap" in p
                                            for p in got["problems"]))
        check("rejecting: and it says WHICH job and WHY",
              any("job=j/pwsh" in p for p in got["problems"]))

        # REJECTING 3: the same with bash, which is equally missing from
        # this runner's stock PATH.
        wf = _fixture(d, "a.yml", _wf(shell="bash"))
        check("rejecting: a self-hosted bash workflow with no call",
              any("job=j/bash" in p for p in scan(wf, d, {}, ())["problems"]))

        # REJECTING 4: a run step with no shell at all. On Windows the
        # runner default is pwsh, so this needs the bootstrap too.
        wf = _fixture(d, "a.yml",
                      "jobs:\n  j:\n    runs-on: [self-hosted, ledger-pc]\n"
                      "    steps:\n      - run: echo hi\n")
        check("rejecting: a bare run step inherits pwsh and still needs it",
              any("default-shell-on-1-bare-run-step" in p
                  for p in scan(wf, d, {}, ())["problems"]))

        # REJECTING 5: a commented example call is not a call.
        wf = _fixture(d, "a.yml", _wf(
            extra="          # call tools\\runner\\bootstrap-paths.cmd\n"))
        check("rejecting: a mention of the call in a comment is not a call",
              scan(wf, d, {}, ())["problems"] != []
              and scan(wf, d, {}, ())["calling"] == [])

        # REJECTING 6: an exemption with no reason written.
        wf = _fixture(d, "a.yml", _wf())
        check("rejecting: an exemption with an empty reason",
              any("no written reason" in p
                  for p in scan(wf, d, {"a.yml": "  "}, ())["problems"]))

        # REJECTING 7: a stale exemption, which is how this file's old hand
        # list would have rotted in the other direction.
        wf = _fixture(d, "a.yml", _wf(runs_on="ubuntu-latest"))
        check("rejecting: an exemption for a workflow that does not need it",
              any("is stale" in p for p in
                  scan(wf, d, {"a.yml": "a reason"}, ())["problems"]))
        check("rejecting: an exemption naming no workflow at all",
              any("names no workflow" in p for p in
                  scan(wf, d, {"ghost.yml": "a reason"}, ())["problems"]))

        # REJECTING 8: the floor catches a deriver that stopped seeing a
        # workflow known to be self-hosted.
        check("rejecting: a floor workflow the derivation no longer finds",
              any("DERIVATION_FLOOR" in p for p in
                  scan(wf, d, {}, ("a.yml",))["problems"]))

        # REJECTING 9: a runs-on this lint cannot resolve is unreadable and
        # not clean.
        wf = _fixture(d, "a.yml", _wf(runs_on="${{ matrix.os }}"))
        check("rejecting: an unresolvable runs-on is not a pass",
              any("cannot resolve" in p for p in scan(wf, d, {}, ())["problems"]))

        # REJECTING 9b: a YAML alias hides the labels from this reader too,
        # and an unread label must never read as "not self-hosted".
        wf = _fixture(d, "a.yml", _wf(runs_on="*agent"))
        check("rejecting: a runs-on behind a YAML alias is unreadable",
              any("cannot resolve" in p for p in scan(wf, d, {}, ())["problems"]))

        # REJECTING 10: the shared script itself missing.
        wf = _fixture(d, "a.yml", _wf(call=True))
        os.remove(os.path.join(d, SCRIPT))
        check("rejecting: the shared script is gone",
              any("does not exist" in p
                  for p in scan(wf, d, {}, ())["problems"]))

    print("lint-bootstrap-single selftest: %d ok, %d failed" % (ok, fail))
    return 1 if fail else 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    wf_dir = WF
    repo = REPO
    for a in sys.argv[1:]:
        if a.startswith("--wf-dir="):
            wf_dir = os.path.abspath(a.split("=", 1)[1])
        elif a.startswith("--repo="):
            repo = os.path.abspath(a.split("=", 1)[1])
    r = scan(wf_dir, repo)
    shown = r["problems"][:20]
    for p in shown:
        print("  PROBLEM " + p)
    if len(r["problems"]) > len(shown):
        print("  (+%d more not shown)" % (len(r["problems"]) - len(shown)))
    report(r)
    return 1 if r["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
