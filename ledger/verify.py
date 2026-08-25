#!/usr/bin/env python3
"""Run the local checks and print the footer that goes in a commit message.

    python3 ledger/verify.py                  # everything
    python3 ledger/verify.py --breaks voice   # and a break spec too

WHY THIS EXISTS, and it is not tidiness.

Twice in one night I ended a commit message with a check count I had not
read — "2764 CoreTests" when it was 2742, "2877" when it was 2883. Both
times the work was fine and the claim was decoration typed from memory, and
both times I only noticed because I happened to run the suite again
afterwards.

That is the same defect this project keeps finding in its own code: a
success recorded before the success happened. A number in a commit message
is a claim about a measurement, and the fix for an unreliable measurement is
never "be more careful" — it is to take the reading from the instrument
instead of from memory.

So the footer comes from here, and if a check is red this prints the failure
instead of a number.
"""
import argparse
import datetime
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def core_tests():
    code, out = run(["dotnet", "run", "-c", "Release", "--project", str(ROOT / "CoreTests")])
    m = re.search(r"All (\d+) checks passed", out)
    if m:
        return True, "%s CoreTests" % m.group(1)
    fails = [l.strip() for l in out.splitlines() if l.strip().startswith("FAILED")]
    if fails:
        return False, "CoreTests RED: " + fails[0][:120]
    return False, "CoreTests did not report a count (build failure?)"


def shape():
    # NO `--nologo`. It is not a `dotnet run` option, so it is forwarded to
    # the APP — where it becomes args[0] and ShapeCheck dutifully tries to
    # enumerate a directory called "--nologo". The exception it threw was
    # reported here as "did not report", which is this script working exactly
    # as intended: it refused to print a green footer for a check that had
    # not actually run. First use, first catch.
    code, out = run(["dotnet", "run", "-c", "Release", "--project", str(ROOT / "ShapeCheck"),
                     "--", str(ROOT / "Assets" / "Scripts"),
                     str(ROOT / "Assets" / "Editor")])
    m = re.search(r"checked (\d+) files, (\d+) shape error\(s\)"
                  r"(?: \((\d+) with conditional code)?", out)
    if not m:
        return False, "ShapeCheck did not report (build failure?)"
    # THE CONDITIONAL COUNT TRAVELS INTO THE FOOTER. Code behind `#if` was
    # not parsed at all until 8 August, so "0 errors in 169 files" was true
    # and covered 380 lines it had never read. Naming the number here means a
    # symbol quietly dropping out shows up as a count moving.
    cond = (", %s with conditional code" % m.group(3)) if m.group(3) else ""
    return m.group(2) == "0", "%s shape errors (%s files%s)" % (
        m.group(2), m.group(1), cond)


def lint():
    # ASSETS/EDITOR TOO. It was checked by nothing: lint and ShapeCheck both
    # scanned only Assets/Scripts, so `CiBuild.cs` — the entry point the whole
    # Windows pipeline runs through — had never been linted or shape-checked,
    # and a typo in it costs a full twenty-eight-minute round trip to find.
    code, out = run(["python3", str(ROOT / "lint-usings.py"),
                     str(ROOT / "Assets" / "Scripts"), str(ROOT / "Assets" / "Editor")])
    m = re.search(r"checked (\d+) files, (\d+) missing-using", out)
    if not m:
        return False, "lint did not report"
    return m.group(2) == "0", "%s lint errors" % m.group(2)


def shadow():
    """A Game method must not be named after a Core type the file uses.

    Cost one CS0119 and three round trips on 4 August: `EvidenceHost.Watched`
    shadowed `Ledger.Core.Watched`, which the same file calls eighty lines
    below, and the error landed on a line nobody had touched. Only Core
    compiles here, so the Game layer's first compiler is twenty-five minutes
    away — every cheap static catch is worth a round trip.
    """
    code, out = run(["python3", str(ROOT.parent / "tools" / "lint-shadow.py")])
    m = re.search(r"lint-shadow: (\d+) shadowed Core types", out)
    if m:
        return True, "0 shadowed Core types"
    m = re.search(r"lint-shadow: (\d+) Game member", out)
    if m:
        return False, "%s SHADOWED CORE TYPE(S) — see tools/lint-shadow.py" % m.group(1)
    return False, "lint-shadow did not report"


def reach():
    """Layer 1 of the testing system: does anything actually call it.

    The gap analysis that found `Brandish` 0, `MayFrisk` 0 and `Misattribute` 0
    was done by hand, once, in an afternoon. This is it in a second, as a graph
    walk from every Core member the Game names — so a helper called by a
    running method counts as running, which the first version got wrong.

    The ledger in `ReachCheck/allow.json` carries a typed reason per entry and
    only counts down: wiring an API without deleting its entry fails too.

    THE ARGUMENT LIST USED TO BE SPELLED OUT HERE AND AGAIN IN THE WORKFLOW,
    AND THEY DRIFTED. On 17 Aug `--also Assets/Editor` was added to THIS copy
    — the Editor layer is a real consumer, `CharacterPrefab` calls Core on
    every Windows build — and not to `.github/workflows/ledger-core-tests.yml`.
    From that day the two readers walked different worlds: local verify green,
    CI red, on the same tree. It cost four consecutive dark CI runs, because
    `Proportion.TryNeckFraction` and `Proportion.IsCaricature` are called ONLY
    from the Editor and the workflow's smaller scan called them unwired.

    So there is now ONE invocation, in `tools/reach-check.sh`, and both callers
    run it. Rule 1's third corollary: one idea, two implementations, and the
    one nobody looks at is the one missing a line."""
    code, out = run(["bash", str(ROOT.parent / "tools" / "reach-check.sh")])
    m = re.search(r"reach ok — (\d+) on the ledger", out)
    if m:
        return True, "%s on the reach ledger" % m.group(1)
    m = re.search(r"reach FAILED — .*", out)
    return False, m.group(0) if m else "reach-check did not report (build failure?)"


def tools_tracked():
    """Every tool project CI runs is actually committed.

    THE TOOL WAS RIGHT AND THE REPOSITORY WAS EMPTY. `ledger/.gitignore` held
    `*.csproj` plus a hand-kept allowlist of four negations, so `ReachCheck`,
    `BalanceLab` and `BarkGen` were written, built and tested here and never
    committed. CI ran `dotnet run --project ledger/ReachCheck` against a
    directory with a Program.cs and no project and went red with "Couldn't find
    a project to run" — a build failure that says nothing about the build.

    Local green and CI red with no code difference between them is the worst
    shape a failure can take, and it cost every core-tests run for an evening.
    The ignore rule is now anchored so it cannot swallow a subdirectory; this
    checks the outcome rather than trusting the rule, because verifying the
    rule is verifying my own comment.

    AND THE SAME FAULT MOVED ONE LAYER OUT ON 25 AUG. This function checked
    `*.csproj` and nothing else, so it could not see that a workflow now
    invokes `tools/ci-checks.sh` and `tools/reach-check.sh` by path — and an
    uncommitted script produces the identical shape: local green, CI red,
    "No such file or directory", no code difference between them. Rule 1's
    third corollary is mechanical, so it is applied here rather than
    remembered: every `tools/*.py` and `tools/*.sh` NAMED IN A WORKFLOW is
    checked for being both on disk and tracked.

    The denominator is printed. "0 untracked" beside nothing walked is the
    zero this project keeps being fooled by."""
    missing = []
    for proj in sorted(ROOT.glob("*/*.csproj")):
        code, out = run(["git", "ls-files", "--error-unmatch", str(proj)], cwd=str(ROOT))
        if code != 0:
            missing.append(proj.parent.name)

    # Every tool a workflow runs by path. Referenced-but-absent is reported
    # too: a workflow naming a file that does not exist is the same red.
    # TRANSITIVELY. `ledger-core-tests.yml` names only `tools/ci-checks.sh`,
    # which names `tools/reach-check.sh` — and an untracked file two hops out
    # breaks CI exactly as loudly as one hop out. The first version of this
    # walk stopped at one hop and caught one of the two new scripts, which is
    # the same "one idea, the copy nobody looks at" shape it exists to stop.
    repo = ROOT.parent
    pat = re.compile(r"tools/[A-Za-z0-9_./-]+\.(?:py|sh)")
    wf = sorted((repo / ".github" / "workflows").glob("*.yml"))
    refs, queue = set(), []
    for f in wf:
        queue += pat.findall(f.read_text(encoding="utf-8"))
    while queue:
        ref = queue.pop()
        if ref in refs:
            continue
        refs.add(ref)
        src = repo / ref
        if src.exists():
            queue += pat.findall(src.read_text(encoding="utf-8", errors="replace"))
    for ref in sorted(refs):
        if not (repo / ref).exists():
            missing.append(ref + "(absent)")
            continue
        code, out = run(["git", "ls-files", "--error-unmatch", ref], cwd=str(repo))
        if code != 0:
            missing.append(ref + "(untracked)")

    n = len(list(ROOT.glob("*/*.csproj")))
    if missing:
        return False, "UNTRACKED/ABSENT TOOL(S): " + ", ".join(missing)
    return True, "%d tool project(s) + %d workflow-named tool(s) in %d workflow(s) tracked" % (
        n, len(refs), len(wf))


def clip_audit():
    """The animation clips we ship are what their filenames say, as far as a
    file can prove it — and the debt counts down.

    WHY THIS EXISTS. Jafar asked whether the people in the stills are moving
    right or whether we are playing the wrong animations. Half of that needs
    a frame. The other half does not: two slots holding the SAME BYTES means
    one is playing the other's motion, and that is a hash comparison rather
    than a judgement. `shoved` and `talk` were byte-identical when this was
    written, from two DIFFERENT harvest names that both matched exactly, so
    every name-based check in the pipeline passed them.

    TWO CHECKS, NOT ONE, and they answer different questions. `--selftest`
    says the reader still works at all — it has an accepting case (the live
    harvest must parse) and a rejecting case (a rig with no take must not
    read as a moving clip). The count says today's clips are no worse than
    the recorded debt. A green selftest with a rising count is a working
    instrument reporting a real regression, and the two must not be able to
    stand in for each other.

    THE LEDGER IS A CEILING, NOT A TARGET. It can only be lowered, and the
    file says why each entry is still open. Raising it to make red go away is
    the move rule 2 forbids."""
    tools = ROOT.parent / "tools"
    code, out = run(["python3", str(tools / "clip-motion.py"), "--selftest", "--quiet"])
    # READ THE KEYS, DO NOT MATCH THE LINE. The first version of this pinned
    # the whole line — `clipFindings=(\d+) duplicates=(\d+) frozen=(\d+)
    # clipsRead=(\d+)` — so adding `stillByDesign` between the third and
    # fourth broke it. It failed loudly, which is the only reason this is a
    # footnote rather than an afternoon: a positional reader that silently
    # returns the wrong field is the `grep -o` fault, and this one could not.
    #
    # Keyed lookups instead, so a new field is a new field rather than a
    # breakage, and a MISSING one is still named.
    keys = dict(re.findall(r"\b(clipFindings|duplicates|frozen|clipsRead)=(\d+)", out))
    want = ("clipFindings", "duplicates", "frozen", "clipsRead")
    absent = [k for k in want if k not in keys]
    if absent:
        return False, "clip-motion did not report " + ", ".join(absent)
    found, dups, frozen, read = (int(keys[k]) for k in want)
    if "SELFTEST PASSED" not in out:
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
        return False, "CLIPS: " + (bad[0][:90] if bad else "selftest did not pass")

    # A ZERO NEEDS A DENOMINATOR (rule 3b): "no duplicates" and "no clips
    # were read" are the same finding count and opposite facts.
    if read == 0:
        return False, "CLIPS: no clip read at all — the harvest folders are empty"

    ledger = ROOT.parent / "game-design" / "clip-findings.txt"
    if not ledger.exists():
        return False, "CLIPS: no clip-findings.txt to measure against"
    lm = re.search(r"^clipFindings=(\d+)", ledger.read_text(encoding="utf-8"), re.M)
    if not lm:
        return False, "CLIPS: clip-findings.txt carries no count"
    allowed = int(lm.group(1))
    if found > allowed:
        return False, ("CLIP DEBT ROSE: %d finding(s) against %d allowed "
                       "(%d duplicate, %d frozen)" % (found, allowed, dups, frozen))
    if found < allowed:
        return False, ("CLIP DEBT FELL to %d from %d — lower the number in "
                       "game-design/clip-findings.txt and say which one closed"
                       % (found, allowed))
    return True, "clips ok (%d read, %d known finding(s))" % (read, found)


def picker_selftest():
    """The clip picker refuses to put one file in two slots.

    Separate from `clip_audit` on purpose: that one checks what LANDED, this
    one checks the thing that lands it, and a re-pick happens on a machine
    this container never sees. If the picker's duplicate check breaks, the
    next harvest silently reintroduces the fault the audit exists to catch,
    and the audit would be measuring a ceiling nobody is defending."""
    tool = ROOT.parent / "tools" / "mixamo-pick" / "pick_animations.py"
    code, out = run(["python3", str(tool), "--selftest"])
    if code != 0 or "SELFTEST PASSED" not in out:
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("  FAIL")]
        return False, "PICKER: " + (bad[0][8:98] if bad else "selftest did not pass")
    return True, "clip picker ok"


def sheet_read():
    """The contact-sheet reader still separates a legible tile from a silhouette.

    Selftest only, deliberately. The LANDED sheet currently has 25 dark tiles
    of 67 and that is a known, recorded finding with a fix already written —
    gating on it would block every commit until a Windows round trip lands,
    which is rule 5b's ratchet. What must not regress is the READER: it has
    been wrong in both directions in one afternoon (a threshold of 42 passed a
    sheet full of silhouettes, 60 failed clips I had just confirmed by eye),
    so the thing worth guarding is that it still tells the two apart."""
    tool = ROOT.parent / "tools" / "sheet-read.py"
    code, out = run(["python3", str(tool), "--selftest"])
    if code != 0:
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
        return False, "SHEET: " + (bad[0][5:98] if bad else "selftest did not pass")
    return True, out.strip().split("\n")[-1].replace("sheet-read ok", "sheet reader ok")


def prop_dimensions():
    """The prop reader still reads a model whole, and assembles its parts.

    IT WAS BROKEN TWICE AND SILENT BOTH TIMES, which is why it is in here now
    rather than being a script somebody remembers to run. It set a module
    global that `parse_fbx` had turned into a default argument, so every FBX
    was read at a 21-vertex cap and eleven of the twelve car-kit models
    printed `no vertex data` — which reads as a fact about the files. And it
    pooled vertices from meshes that do not share a frame, so every vehicle
    measured 30 units taller than it is, uniformly, with the extra 30 buried
    under the road.

    Neither could fail. A tool that returns a plausible number for the wrong
    reason has no failing case at all — the only thing that catches it is an
    assertion about the WORLD, and the selftest's is that a car's wheels are
    on the ground."""
    tool = ROOT.parent / "tools" / "prop-dimensions.py"
    code, out = run(["python3", str(tool), "--selftest"])
    if code != 0:
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
        return False, "PROPS: " + (bad[0][5:98] if bad else "selftest did not pass")
    n = len([l for l in out.splitlines() if l.strip().startswith("ok")])
    return True, "prop reader ok (%d checks)" % n


def prop_reach():
    """Do the fetched kit models have a caller — the reach ledger, for art.

    REPORTS A COUNT, RATCHETS NOTHING. An unused model is not a fault: the
    fetches are deliberately broad, and a guard that failed the build for one
    would be the ratchet rule 5 forbids — it cannot tell "we fetched more than
    we needed" from "a kit stopped being placed".

    What CAN fail is the instrument, and the check it runs is the one that
    cannot be fooled by a fixture: every prop key the last landed sim actually
    instantiated must be reported as reached. A reach tool that has drifted
    from `TryInstantiateProp`'s normalisation would fail that immediately, and
    a fixture written by the same hand as the tool would not catch it.
    """
    tool = ROOT.parent / "tools" / "prop-reach.py"
    code, out = run(["python3", str(tool), "--selftest"])
    if code != 0:
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAILED")]
        return False, "PROP REACH: " + (bad[0][7:98] if bad else "selftest did not pass")
    code, rep = run(["python3", str(tool)])
    head = rep.splitlines()[0] if rep.strip() else "prop-reach produced no report"
    n = len([l for l in out.splitlines() if "passed" in l])
    unreached = [l.strip() for l in rep.splitlines()
                 if l.strip().startswith("ENTIRE KIT UNREACHED")]
    tail = (" — " + unreached[0]) if unreached else ""
    return True, head.replace("prop-reach: ", "prop reach ok, ") + tail


def ref_bench():
    """The visual-bar benchmark's instrument, not its verdict.

    REPORTS NOTHING HERE AND GATES NOTHING, on purpose. `tools/ref-bench.py`
    compares our stills against the five GTA V reference frames, and 202 of its
    272 readings are currently outside the reference range — gating on that
    would fail every commit until M17.10 finishes, which is the ratchet rule 5
    forbids wearing an ambition's clothes. The report is read by a person; what
    is checked here is that the instrument still works.

    ITS SELFTEST IS WORTH RUNNING BECAUSE THE TOOL ALREADY CAUGHT ITSELF ONCE.
    Built to spec, its edge-density row scored `district_downtown` — a frame
    containing nothing but film grain — above all five references, and the
    grain-immune row it grew in response scores the same frame below all five.
    The check that pins that down is in there: a synthetic field of pure noise
    must read dense to the edge metric and flat to GROUND PATCH. If those two
    ever agree on noise, the paragraph in the docstring warning everyone not to
    read one without the other has quietly stopped being true, and the number
    that steers V2 has stopped meaning anything.

    The rest is rule 3b and rule 5b: a missing directory must say NOTHING
    MEASURED with its file count, a truncated JPEG must be named rather than
    dropped, and the accepting case is the live directories — which is the one
    fixture nobody can fake, because doing the work is what changes it."""
    tool = ROOT.parent / "tools" / "ref-bench.py"
    code, out = run(["python3", str(tool), "--selftest"])
    m = re.search(r"selftest: (\d+) passed, (\d+) failed", out)
    if not m:
        return False, "REF BENCH: selftest did not report"
    if m.group(2) != "0":
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAILED")]
        return False, "REF BENCH: " + (bad[0][7:98] if bad else "selftest failed")
    return True, "%s ref-bench checks (%s failed)" % (m.group(1), m.group(2))


def decal_ink():
    """What each decal set lays down — the instrument, not a verdict on it.

    GATES THE SELFTEST, REPORTS THE REST, the same split as `ref_bench` and for
    the same reason. `tools/decal-ink.py` measures the ink, coverage, mask
    detection and multiply floor of every fetched decal set; which sets are
    worth what weight is a judgement made by a person off that table, and a
    guard that failed the build when a texture came back darker than last time
    would be the ratchet rule 5 forbids.

    WHAT IS CHECKED IS THAT THE INSTRUMENT STILL AGREES WITH THE GAME. Three of
    its assertions are about `DecalLayer.cs` rather than about pixels: the road
    loop still places at strength 0.8, the wall loop at 0.7/0.55, and `LoadSet`
    still retints a detected mask to 89. Every number the tool prints scales
    with those, so a change there that this tool did not follow would silently
    re-scale the whole series — and the series is what the pick weights were
    derived from. The roster and the weights are read out of the C# for the same
    reason: a table describing sets the game no longer names is worse than none.

    THE ACCEPTING FIXTURE IS THE LIVE BANK, which is the one nobody can fake —
    the sets are tracked, the game reads the same bytes, and doing the work this
    tool prompts (fetching a set, moving one between pools) changes the fixture
    rather than breaking it. The rejecting fixtures are synthetic and cover the
    three faults that are invisible in the game: a dimension mismatch, which
    makes `LoadSet` keep an opaque alpha and stamp a solid rectangle; a set with
    no image at all; and a missing bank, which must say NOTHING MEASURED with a
    denominator rather than print an empty table and exit clean (rule 3b)."""
    tool = ROOT.parent / "tools" / "decal-ink.py"
    code, out = run(["python3", str(tool), "--selftest"])
    m = re.search(r"selftest: (\d+) passed, (\d+) failed", out)
    if not m:
        return False, "DECAL INK: selftest did not report"
    if m.group(2) != "0":
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAILED")]
        return False, "DECAL INK: " + (bad[0][7:98] if bad else "selftest failed")
    code, rep = run(["python3", str(tool)])
    summary = [l for l in rep.splitlines() if l.startswith("decalInk scope=summary")]
    tail = ""
    if summary:
        got = dict(t.split("=", 1) for t in summary[0].split()[1:] if "=" in t)
        tail = (" — %s set(s), %s unnamed" % (got.get("setsExamined", "?"),
                                              got.get("unnamed", "?")))
    return True, "%s decal-ink checks (%s failed)%s" % (m.group(1), m.group(2), tail)


def powershell_steps():
    """Do the workflow's pwsh steps parse.

    The Windows workflow is the only thing that can tell me anything about the
    game, and shell mistakes INSIDE it have twice taken that channel out rather
    than the thing it was checking — most recently a Verdict step that printed
    "no failing gates" for a run whose checkout had failed. Rule 12 says the
    blocked channel is the highest-leverage bug on the board; this is the part
    of it that can be checked without a runner.

    A DENOMINATOR ON THE SKIP, and this one is not cosmetic. pwsh is a global
    dotnet tool, so a fresh container does not have it, and "the workflow's
    PowerShell is fine" must never be indistinguishable from "no PowerShell
    existed to check it with". The skip goes in the FOOTER, so a commit made
    without the check says so in its own message.
    """
    tool = ROOT.parent / "tools" / "ps-check.py"
    code, out = run(["python3", str(tool), "--quiet"])
    if "NO POWERSHELL" in out:
        return True, ("pwsh steps NOT CHECKED (no PowerShell — "
                      "dotnet tool install --global PowerShell)")
    if code != 0:
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
        return False, "PWSH: " + (bad[0][5:98] if bad else "a workflow step did not parse")
    n = out.strip().split()
    count = n[2] if len(n) > 2 else "?"
    return True, f"pwsh steps parse ({count} step(s))"


def backend_compiles():
    """Does the speech backend compile against the real onnxruntime assembly.

    `Game/OnnxSpeech.cs` is the only Game-layer file that touches no Unity
    type — it speaks to onnxruntime and to Core and nothing else. So the one
    question that used to need a ~28-minute Windows round trip is answerable
    here in seconds, against the library's own 210 KB managed assembly.

    IT FOUND TWO REAL ERRORS the first time it ran, in code nothing had ever
    compiled: an `int * uint` that widens to long, and a tensor constructor
    taking a shape the wrong way round.

    A DENOMINATOR ON THE SKIP. Without the cached assembly this cannot run,
    and "the backend compiles" must not read the same as "nothing was
    compiled" — so the skip says so and names the missing file."""
    dll = ROOT / ".onnx-cache" / "Microsoft.ML.OnnxRuntime.dll"
    if not dll.exists():
        code, out = run(["python3", str(ROOT.parent / "tools" / "fetch-onnxruntime.py"),
                         "--dest", str(ROOT / ".onnx-cache"), "--managed-only"])
    if not dll.exists():
        return True, "backend compile SKIPPED (no onnxruntime assembly cached)"
    # BOTH PROJECTS, because they compile the same backend into different
    # shells: BackendCheck answers "does the game's code build" and
    # SpeechBench is the console that PROVES the bound path on the PC — a
    # bench that stopped compiling is a residency question nobody can ask.
    for proj, name in (("BackendCheck", "backend"), ("SpeechBench", "bench")):
        code, out = run(["dotnet", "build", "-c", "Release", "-v", "q",
                         "--nologo", str(ROOT / proj)])
        if "Build succeeded" not in out:
            errs = sorted({l.split("): ")[-1].split(" [")[0]
                           for l in out.splitlines() if "error CS" in l})
            return False, ("SPEECH " + name.upper() + " WILL NOT COMPILE: "
                           + "; ".join(errs[:2]))
    return True, "speech backend + bench compile"


def voice_assets():
    """The vocabulary and the voices can reach the build.

    `speechVocab=none speechVoices=0` was true for every build until now, and
    neither reads as a failure — a game that cannot see its own voices looks
    exactly like a game that prefers the bank. So the staging is checked here
    rather than discovered in a verdict twenty-eight minutes later."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "stage-voice-assets.py"),
                     "--selftest"])
    m = re.search(r"stage-voice-assets --selftest: PASS — (\d+) checks", out)
    if m:
        n = re.search(r"(\d+) of (\d+)", out)
        return True, "voice assets ok (%s checks%s)" % (
            m.group(1), ", %s voices stageable" % n.group(1) if n else "")
    bad = next((l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")),
               "did not report")
    return False, "VOICE ASSETS: " + bad[:110]


def voices_into_build():
    """The step that puts the graphs into a build a person can run.

    Every other piece of live speech has been proven for days — the graphs
    convert, the card runs them, the ear approved the voice — while every
    build ever downloaded reported `no t3-prefill.onnx` and fell back to the
    bank, because the 4.5 GB of graphs cannot travel through CI and nothing
    copied them in afterwards. The tool that closes that gap is checked here
    for the reason its neighbour above is: a delivery step that silently does
    nothing looks exactly like a game that prefers the bank."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "put-voices-in-build.py"),
                     "--selftest"])
    m = re.search(r"put-voices-in-build --selftest: PASS — (\d+) checks", out)
    if m:
        return True, "voices-into-build ok (%s checks)" % m.group(1)
    bad = next((l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")),
               "did not report")
    return False, "VOICES INTO BUILD: " + bad[:110]


def conditional_reach():
    """A Game type behind `#if` must be named by something other than itself.

    `OnnxSpeech` was written, compiled against the real runtime, and
    constructed by nothing — `Audio.Backend` was null and always would have
    been. It survived a Windows build that PASSED, because a null backend and
    a working backend with no model produce the same verdict.

    Nothing could have caught it: the reach check asks about calls INTO Core,
    ShapeCheck reports diagnostics and an uncalled class is not one, and every
    tool that skips disabled regions skipped the file entirely."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "lint-conditional-reach.py")])
    m = re.search(r"lint-conditional-reach: (\d+) unreachable, (\d+) conditional", out)
    if not m:
        return False, "conditional-reach did not report"
    return m.group(1) == "0", ("%s unreachable behind #if (%s type(s) checked)"
                               % (m.group(1), m.group(2)))


def pc_watcher():
    """The job runner on Jafar's machine, checked here rather than there.

    It executes named jobs on a desktop I cannot see, so its refusals matter
    more than its successes: an unknown job, a missing id, a damaged request.
    All three are checked, and so is the table pointing only at files that
    exist — an entry naming a script nobody wrote fails minutes away on his
    machine instead of instantly here."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "pc-watcher.py"),
                     "--selftest"])
    m = re.search(r"pc-watcher --selftest: PASS — (\d+) checks", out)
    if m:
        return True, "pc-watcher ok (%s checks)" % m.group(1)
    bad = next((l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")),
               "did not report")
    return False, "PC WATCHER: " + bad[:110]


def card_writing():
    """The generator's writing rules, run without spending anything.

    `Tier2Gen` is the only tool here that costs money to exercise properly, so
    its validator was the one nobody could run: a rule added to it went
    straight to a CI job with an API key and sixty cards riding on it. The
    failure that shape produces is the expensive one — every card rejected, an
    empty output directory, and the money already gone.

    `--selftest` runs the writing rules against cards built to pass and cards
    built to fail, with no key and in about a second. Its first execution
    caught two faults in ITSELF and none in the code, which is the usual
    ratio: hand-built test input was a second model of what the API returns
    and disagreed with the real parser about whether 54 is a double."""
    code, out = run(["dotnet", "run", "--project", str(ROOT / "Tier2Gen"), "--", "--selftest"])
    m = re.search(r"all writing rules behave — (\d+) failure", out)
    if m:
        n = len([l for l in out.splitlines() if l.strip().startswith("ok ")])
        return True, "%d card-writing rules" % n
    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
    return False, "CARD WRITING RED: " + (bad[0][:120] if bad else "no verdict (build failure?)")


def shipped_cards():
    """The cards the GAME loads are the cards we edited.

    WHY THIS EXISTS, and it cost the only money this project has spent.

    `Tier2Batch` loads `Application.streamingAssetsPath/tier2-batch-1.json`.
    The enrichment run — the API spend Jafar authorised on 3 August, 54 cards
    given the example lines they lacked plus period texture — writes
    `game-design/tier2-batch-1.json` and NOTHING copied it across. So the
    shipped copy still had six cards with lines where the design copy had
    sixty, and every one of those new voices was sitting in a folder the
    runtime never opens. Rule 6 with a receipt attached: built, paid for, not
    running.

    It was invisible because both files exist, both parse, both are tracked,
    and the audit tool takes a path — so every check anybody ran was pointed
    at the copy that was right.

    This compares CONTENT rather than bytes: the two are allowed to differ in
    formatting, and a whitespace diff failing the build would be a checker
    nobody trusts within a week."""
    import json
    design = ROOT.parent / "game-design" / "tier2-batch-1.json"
    shipped = ROOT / "Assets" / "StreamingAssets" / "tier2-batch-1.json"
    if not design.exists() or not shipped.exists():
        return False, "SHIPPED CARDS RED: one of the two copies is missing"
    try:
        a = json.loads(design.read_text(encoding="utf-8"))
        b = json.loads(shipped.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, "SHIPPED CARDS RED: %s" % e
    if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
        # WHICH cards, because "they differ" sends somebody diffing 190KB.
        byid = {c.get("id"): c for c in a}
        drift = sorted(i for i, c in {c.get("id"): c for c in b}.items()
                       if json.dumps(byid.get(i), sort_keys=True)
                       != json.dumps(c, sort_keys=True))
        return False, ("SHIPPED CARDS RED: the game loads StreamingAssets and it "
                       "disagrees with game-design on %d card(s): %s"
                       % (len(drift), ", ".join(drift[:5])))
    return True, "%d cards shipped as edited" % len(a)


def queue_depth():
    """There is enough on the queue to survive the next build.

    The queue was written to stop four idle gaps and it worked for an hour:
    eighteen commits, longest gap eight minutes. Then three more gaps — 21, 28,
    28 — because THE QUEUE HAD RUN OUT. Its own instructions guaranteed that:
    every item sized to fit inside one round trip means an hour of good work
    consumes the list, and an empty list reads exactly like an empty afternoon.

    So the depth is checked where every other claim in this project is checked,
    at commit time, and the failure it names is the one that actually happened:
    nothing left that can be started without waiting on CI."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "queue-check.py")])
    m = re.search(r"(\d+) item\(s\), (\d+) ready", out)
    if not m:
        return False, "queue-check did not report"
    if code != 0:
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("only ")
               or l.strip().startswith("no `")]
        return False, "QUEUE TOO THIN: " + (bad[0][:100] if bad else "see queue-check")
    return True, "%s queue items ready" % m.group(2)


def game_compiles():
    """THE GAME LAYER, COMPILED, HERE, IN SIX SECONDS.

    This is the check this project has never had and has paid for daily. The
    Game layer's first compiler was a ~28-minute Windows build, so a wrong type
    name was not one lost round trip but every round trip until somebody
    noticed — measured at 18 commits and 4 consecutive dead builds for a single
    bad name, each build dispatched to answer a different question and each
    coming back `NO PLAYER LOG`.

    It compiles against Unity's OWN reference assemblies from NuGet, so these
    are real signatures rather than a name-matcher's opinion. See
    `tools/gamecheck.py` for the four uGUI shims and the one allow-listed
    reference-assembly gap, and for why that allow-list fails in both
    directions."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "gamecheck.py")])
    if code != 0:
        first = next((l.strip() for l in out.splitlines()
                      if ".cs(" in l or "NO LONGER OCCUR" in l), "see gamecheck")
        return False, "GAME LAYER DOES NOT COMPILE: " + first[:110]
    m = re.search(r"(\d+) files", out)
    return True, "Game layer compiles (%s files)" % (m.group(1) if m else "?")


def docs_shape():
    """Every doc in `game-design/` declares LIVE/SPEC/LOG and stays scannable.

    THE TOOL EXISTED AND NOTHING RAN IT. CLAUDE.md says in as many words that
    `tools/docs-check.py` enforces the documents rule, and it was never wired
    into this file — so it only ever ran when somebody thought to type it.
    Nobody did for long enough that `queue.md` reached 536 lines against its
    own 400-line cap, and every `verify.py` in between reported green.

    That is rule 6 pointed at a tool rather than at the game: built, tested,
    plausible, and never once executing where it mattered. It is also why the
    cap exists at all — a live plan nobody can scan is the 1,525-line roadmap
    that got a status banner stapled on it instead of being fixed.

    Reported like every other check, so the count is in the footer and a drift
    is a number somebody reads rather than a thing somebody remembers."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "docs-check.py")])
    m = re.search(r"(\d+)/(\d+) clean", out)
    if code != 0:
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
        return False, "DOCS: " + (bad[0][5:105].strip() if bad else "see docs-check")
    if not m:
        return False, "docs-check did not report"
    return True, "docs %s" % m.group(0)


def template_sync():
    """CLAUDE.md's process sections, against the claim that the template carries them.

    THE INCIDENT, 24 Aug. The template repo (`jsab258/game-studio`) drifted from
    LEDGER's process sections within HOURS of shipping — it still said the
    resident was Fable while CLAUDE.md had moved to the hybrid — and it was
    caught by Jafar reading it, not by any instrument. Every other mechanism
    considered (a dailies review, a standing queue item, syncing on demand) is
    list-based or clock-based; this file is a list of proofs that a rule with no
    trigger point decays, and "sync on demand" IS the incident.

    SAME-REPO ON PURPOSE, and that is the design decision rather than a
    convenience: `tools/template-sync.py` fingerprints the four process sections
    (THE STUDIO SPLIT, THE HYBRID RESIDENT, REPORTING, AUTO MODE) and compares
    against `.claude/template-sync.txt`, which records the fingerprint plus
    either the template commit that absorbed it or a named queue item deferring
    it. It NEVER reads the other repo — that checkout exists in this container
    and not on the Windows runner, and a check that means different things in
    different places is not a check. The marker is the claim; the job here is to
    force the claim to be MADE, at the moment the sections change.

    THE CHECK RUNS BEFORE THE SELFTEST, deliberately. The selftest's first
    accepting fixture is the live pair, so a real drift would fail it too — and
    reporting a drift as "the checker is broken" sends the next session reading
    the tool instead of the marker. Red for the tree comes first; red for the
    instrument comes second; green needs both.

    A DEFERRAL IS GREEN AND LOUD. `state=deferred` passes, and its queue item is
    named in the footer of every commit made while it stands, so a deferral
    nobody discharges is visible in the commit feed rather than resting in a
    file nobody opens."""
    tool = str(ROOT.parent / "tools" / "template-sync.py")
    code, out = run(["python3", tool])
    head = next((l.strip() for l in out.splitlines()
                 if l.startswith("template-sync:")), "")
    if not head:
        return False, "TEMPLATE SYNC READ NOTHING: " + (out.strip()[:110] or "no output")
    if code != 0:
        return False, head[:400]
    scode, sout = run(["python3", tool, "--selftest"])
    m = re.search(r"selftest: (\d+) passed, (\d+) failed", sout)
    if not m:
        return False, "TEMPLATE SYNC CHECK BROKEN: selftest did not report"
    if m.group(2) != "0":
        bad = [l.strip() for l in sout.splitlines() if l.strip().startswith("FAILED")]
        return False, "TEMPLATE SYNC CHECK BROKEN: " + (bad[0][7:110] if bad
                                                        else "selftest failed")
    # A COMPACT FOOTER, BUILT FROM THE TOOL'S OWN TOKENS rather than retyped:
    # the state, its subject, and the denominators that make the zero readable.
    got = dict(t.split("=", 1) for t in head.split() if t.count("=") == 1)
    state = got.get("state", "?")
    subject = ("deferred to %s" % got.get("queueItem", "?")) if state == "deferred" \
        else "synced at %s" % got.get("templateSha", "?")
    return True, ("template sync %s (%s, %s sections, fingerprint %s, %s fixtures)"
                  % (state.upper() if state == "deferred" else "ok", subject,
                     got.get("sections", "?"), got.get("fingerprint", "?"),
                     m.group(1)))


def attribution():
    """Every third-party asset is accounted for in THIRD-PARTY.md.

    THE SECOND TOOL FOUND BY THE SAME SWEEP AS `docs_shape`, and the one with
    a licence attached rather than a style rule. Its own opening paragraph says
    the original breach — 19 cast voices from a CC BY 4.0 corpus with no
    attribution file anywhere — "survived because nothing in the plan owned it
    and nothing in CI looked for it". That stayed true OF THE CHECK for five
    days: it was never wired in here, so it only ran when somebody typed it.

    Nobody did, and it was red the whole time. A font had been shipping since
    31 July while THIRD-PARTY.md's font section still read "NOTHING SHIPS, AND
    THAT IS A BUG". The licence file did travel with the font, because the
    fetcher writes it — what was wrong was the record, and for a licence the
    record is the part that has to be right."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "attribution-check.py")])
    if code != 0:
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
        return False, "ATTRIBUTION: " + (bad[0][5:105].strip() if bad else "see attribution-check")
    n = len(re.findall(r"^\s+ok\s", out, re.M))
    return True, "%d attribution check(s)" % n


def nested_types():
    """A Core type qualified by another Core type — CS0426.

    `Mixing.Bus` where `Bus` is a SIBLING of `Mixing`, not nested in it. Roslyn
    reports it instantly and ShapeCheck cannot, because CS0426 is type
    resolution and ShapeCheck runs reference-independent diagnostics only —
    which is the very property that lets it run at all on a side with no Unity
    assemblies.

    So it was a twenty-eight-minute round trip, and the cost was not the error:
    three commits went out on top of it before the verdict said the sim had
    never run. Same shape and same remedy as `lint-shadow`, which exists
    because CS0119 cost a round trip the same way."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "lint-nested.py")])
    if code != 0:
        first = next((l.strip() for l in out.splitlines() if ".cs:" in l), "see lint-nested")
        return False, "CS0426 WAITING TO HAPPEN: " + first[:90]
    m = re.search(r"\((\d+) top-level Core types checked\)", out)
    return True, ("0 nested-type errors (%s Core types)" % m.group(1) if m
                  else "0 nested-type errors")


def filename_as_type():
    """A filename used as a type name — CS0103.

    `SimDirector` read `TrafficHost.BrakeLampsPeak`. There is no type called
    `TrafficHost`: that file declares `partial class GameController`, like
    thirteen others in the Game layer. The build came back NO PLAYER LOG and
    three commits were already sitting on top of it.

    Fourth member of the family that exists because ShapeCheck runs
    reference-independent diagnostics only — CS0119 (`lint-shadow`), CS0426
    (`nested_types`), CS0120 (`static_instance`) and now this. It needs no type
    resolution at all: it is a set difference between the filenames somebody
    might mistake for a type and the type names that exist.

    Writing it found a fault in `lint-shadow` too. Both stripped every
    double-quoted run before scanning, and `$"..."` IS CODE — so both were
    blind to `SimDirector`'s done-line, which is one interpolated string
    hundreds of expressions long and the largest concentration of Game-layer
    static reads in the project. The new check scored zero on the very line
    that prompted it until that was fixed."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "lint-filetype.py")])
    if code != 0:
        first = next((l.strip() for l in out.splitlines() if ".cs:" in l), "see lint-filetype")
        return False, "CS0103 WAITING TO HAPPEN: " + first[:90]
    m = re.search(r"\((\d+) file\(s\) scanned, (\d+) type\(s\) declared, (\d+) filename", out)
    return True, ("0 filename-as-type errors (%s files, %s filenames that are not types)"
                  % (m.group(1), m.group(3)) if m else "0 filename-as-type errors")


def namespace_as_value():
    """A namespace used as a value — CS0118.

    `ViolenceHost` is a static class with no game in scope and contained
    `if (Game != null && Game.Campaign != null)`. Inside `namespace
    Ledger.Game` the bare name `Game` binds to the NAMESPACE, so two builds
    came back NO PLAYER LOG and ten commits piled up on a branch that did not
    compile.

    Fifth member of the reference-resolution family, and the one that looks
    most normal: `PlayerController` has a real `public GameController Game;`
    and reads `Game.Harm` correctly three lines apart. What makes it an error
    in one file and legal in another is whether the enclosing type declares a
    member of that name — a per-file fact no reader checks.

    Reads only the positions no namespace can occupy: compared to null, `?.`,
    `?[`, incremented. `Game.Campaign` is deliberately NOT read, because that
    is what a namespace qualifier looks like and `Ledger.Core.Violence` is one
    on hundreds of lines."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "lint-namespace.py")])
    if code != 0:
        first = next((l.strip() for l in out.splitlines() if ".cs:" in l), "see lint-namespace")
        return False, "CS0118 WAITING TO HAPPEN: " + first[:90]
    m = re.search(r"\((\d+) file\(s\) scanned, (\d+) namespace segment", out)
    return True, ("0 namespace-as-value errors (%s files, %s segments in scope)"
                  % (m.group(1), m.group(2)) if m else "0 namespace-as-value errors")



def raw_avenues():
    """A raw read of `AvenuesX`/`AvenuesZ` — the unscaled source arrays.

    `WideBlocks` scales the city about the origin, so a coordinate taken
    straight out of those arrays describes a city that was never built. FIVE
    places did it and all five were wrong the same way: `DistrictAt` looked
    136-184m from four districts' own buildings, the district tour aimed four
    of seven cameras at bare ground, `Population.Place` spawned their residents
    elsewhere, and the ground plane was sized -200..160 while blocks reach
    -426..340.

    A rule would not have caught it — `ScaleAbout`'s own docstring already says
    it exists so the grid, the blocks and the addresses "cannot disagree", and
    it was written by the hand that then read the arrays raw in four other
    files. So `StreetMap.BoundsOf`/`CentreOf` do the scaling and this refuses
    the read that bypasses them.

    Both halves are run: the selftest proves the check still works, and the
    tree is the accepting case — every hit on today's code would be a
    regression by construction, so a clean sweep needs no fixture to trust."""
    tool = str(ROOT.parent / "tools" / "lint-avenues.py")
    code, out = run(["python3", tool, "--selftest"])
    if code != 0:
        first = next((l.strip() for l in out.splitlines()
                      if "Error" in l or "assert" in l), "see lint-avenues --selftest")
        return False, "AVENUE LINT BROKEN: " + first[:110]
    code, out = run(["python3", tool])
    if code != 0:
        first = next((l.strip() for l in out.splitlines() if ".cs:" in l), "see lint-avenues")
        return False, "RAW AVENUE READ (unscaled coordinates): " + first[:90]
    m = re.search(r"\((\d+) files walked", out)
    return True, ("0 raw avenue reads (%s files)" % m.group(1) if m
                  else "0 raw avenue reads")


def static_instance():
    """A static method reaching an instance member — CS0120.

    The THIRD reference-resolution error in one morning, after CS0119
    (`lint-shadow`) and CS0426 (`nested_types`). `GameController` is spread
    across fourteen files, so a method cannot see from its own file whether
    what it touches is static, and `static` is the reflex modifier for
    anything that looks like a pure mapping. `ApplyDetailToCrowd` looked
    exactly like one and its whole job was the instance's own population.

    THE CHECKER'S OWN FIRST VERSION MISSED IT. It walked braces from the
    signature line, which in Allman carries none, so it closed every body
    before entering it — and passed a three-case self-test in which every
    fixture was written on one line. It reported zero against the exact file
    that had produced the error. That is why its self-test now contains the
    real method's shape, and why this wiring went in only after running it
    against the pre-fix file and getting back lines 129 and 132 — the two
    the Windows build had reported."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "lint-static.py")])
    if code != 0:
        first = next((l.strip() for l in out.splitlines() if ".cs:" in l), "see lint-static")
        return False, "CS0120 WAITING TO HAPPEN: " + first[:90]
    m = re.search(r"\((\d+) instance members.*?(\d+) static bodies walked\)", out)
    return True, ("0 static/instance errors (%s members, %s bodies)" % (m.group(1), m.group(2))
                  if m else "0 static/instance errors")


def workflow_size():
    """Can the Windows build still be DISPATCHED.

    A comment took the build step past GitHub's expression-length limit and
    `workflow_dispatch` started returning 422 — no Windows build at all, which
    is the only way to compile the Game layer and the only readable channel out
    of CI.

    It belongs here rather than nowhere because of WHEN the 422 is raised: at
    dispatch, not at commit. The commit that breaks it is green, lands, and the
    breakage is found by whoever next tries to build — which in this project is
    a person waiting on a twenty-eight-minute round trip that will never start.
    Checked here, it is a red line before the commit exists.

    The bound is the largest step that has ever dispatched successfully, not
    the number in GitHub's message: theirs is 21000 and a 23184-character block
    dispatched fine all morning, so their accounting is not this one and
    guessing at it would be inventing a threshold."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "workflow-size.py")])
    if code != 0:
        first = next((l.strip() for l in out.splitlines() if ".yml:" in l), "see workflow-size")
        return False, "WORKFLOW STEP TOO LARGE TO DISPATCH: " + first[:90]
    m = re.search(r"largest step (\d+) chars \((\d+) under", out)
    return True, ("workflow steps ok (%s under the dispatch ceiling)" % m.group(2)
                  if m else "workflow steps ok")


def convo_probe():
    """The conversation probe finds the real cards, without spending anything.

    This is the one tool here that costs Jafar money, and its whole job is to
    pull four character cards out of C# verbatim string literals and hand them
    to the real prompt builder. Every way that can go wrong produces a
    PLAUSIBLE TRANSCRIPT OF THE WRONG THING — a complete-looking run, a written
    file, and a bill.

    Its dry mode found three such faults before a call was made: an off-by-one
    that dropped the `#` and silently discarded every card; a name match on
    "Lena" against a card headed "Lena Moreau", which would have probed three
    characters and a market trader; and a spoken-lines check that knew only one
    of the two conventions in this repo and reported three good cards as
    voiceless."""
    code, out = run(["dotnet", "run", "--project", str(ROOT / "ConvoProbe"), "--", "--dry"],
                    cwd=str(ROOT.parent))
    m = re.search(r"(\d+) card\(s\), (\d+) scripted turns each = (\d+) calls", out)
    if not m:
        return False, "CONVO PROBE did not report (build failure?)"
    if m.group(1) != "4":
        return False, "CONVO PROBE found %s cards, expected 4" % m.group(1)
    voiceless = [l.split()[0] for l in out.splitlines() if "lines=NO" in l]
    if voiceless:
        return False, "CONVO PROBE: no spoken lines for " + ", ".join(voiceless[:3])
    return True, "%s probe calls staged" % m.group(3)


def shape_files():
    """Layer 2 of the testing system, for the half that lives in files.

    `TextShape` covers every line the game generates and CoreTests sweeps it.
    This covers the clips and the manifests, where a fault is never a compile
    error and never a failing assertion — it is a clip that plays as silence,
    or two characters cast with the same throat."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "shape-check.py")])
    if "shape ok" in out:
        return True, "shape ok (clips, barks, manifests)"
    m = re.search(r"(\d+) problem\(s\)", out)
    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
    return False, "SHAPE: %s%s" % (m.group(1) + " problem(s): " if m else "",
                                   bad[0][:90] if bad else "did not report")


def slop():
    """Every player-facing word against the signs-of-AI-writing list.

    Jafar saw one em dash in a bark and asked whether the dialogue had been
    run through the humanizer. It had not. Then, when I came back having
    checked em dashes: "em dash is just one sign, you need to run everything
    through /humanizer." Both corrections were right, and the second is the
    one worth a guard — checking the tell you happen to have in mind is how
    you certify a body of text as clean.

    A RATCHET ON THE BACKLOG, not a wall. The bark bank and the Tier-2 cards
    are at zero and must stay there. The Game layer's authored narration
    carries 116 spaced em dashes, which is a real backlog and not something to
    fail the build over — but the number may only ever go DOWN. That makes new
    slop a red commit while leaving the existing debt payable in any order,
    which is the difference between a guard and the ratchet rule 5 warns
    about."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "slopcheck.py")])
    m = re.search(r"slopcheck: (\d+) hit\(s\) across (\d+) patterns and (\d+)", out)
    if not m:
        return False, "slopcheck did not report"
    hits, pats, strings = int(m.group(1)), m.group(2), m.group(3)
    if hits > SLOP_CEILING:
        return False, ("SLOP: %d hit(s), above the %d ceiling — new AI-writing "
                       "tells landed" % (hits, SLOP_CEILING))
    return True, "slop %d/%d (%s patterns, %s strings)" % (hits, SLOP_CEILING, pats, strings)


# THE CEILING ONLY EVER COMES DOWN, AND IT CAME DOWN THE SAME DAY IT WAS SET.
# 117 counted debug output and rich-text ledger rows as writing. With the three
# populations separated it is 93 — 92 spaced em dashes in prose and one stray
# ellipsis character, every other surface at zero and all nineteen other
# patterns at zero everywhere.
#
# Two numbers were quoted for this before the tool settled it: 116 from a scan
# that counted logs, and 88 from an ad-hoc script with a slightly different
# context window. Neither was the instrument. 93 is what the instrument says,
# and the instrument is what the ceiling tracks — which is the whole argument
# for having one.
# 91 -> 88 ON 13 AUGUST, AND THE THREE CAME OFF THE BARK BANK RATHER THAN
# THE BACKLOG. Four bark lines had been edited to carry em dashes; the bank
# they are enumerated into was stale, so `strings_from_barks` read the OLD
# punctuation and scored the bank at zero while the code sat at four. A stale
# artefact hid a violation from the guard that owns it, and the same staleness
# orphaned four recordings — one cause, two guards blind, neither able to see
# the other. Regenerating showed the bank at 4, and taking the dashes back out
# of `StreetVoice` fixed both at once: the bank returns to zero, the 2,010
# clips are correct again, and nothing needs re-rendering.
SLOP_CEILING = 88


def voice_live():
    """The live-dialogue probe's own checks, run on every commit.

    It cannot answer its question here — that needs a GPU and a stranger's
    hardware is the whole point — so what gets checked is everything that
    DECIDES the answer: that every backend is probed and reports why it is
    missing rather than throwing, that the listening page gives a failed
    route an honest "nothing rendered" instead of a dead player, and that a
    real bark is found to compare against.

    Wired in because the last tool whose GPU path went unrun shipped with a
    NameError on its working line and cost Jafar a two-hour batch he had
    already started."""
    tools = ROOT.parent / "tools" / "voice-live"
    total = 0
    skipped = []

    # ONE WAY TO LOAD THE MODEL, ENFORCED. `ChatterboxTTS.__init__` builds a
    # watermarker that is None on a machine without `pkg_resources`, so the
    # constructor dies before any work starts. `diagnose_watermarker` has
    # fixed that for a year — for whichever files remembered to call it.
    # `export-decode.py` was written beside them, did not, and died on Jafar's
    # machine after two successful exports and several minutes of loading.
    # Same fault, cure in the same directory, second occurrence. A rule that
    # depends on remembering is a rule that decays, so this is a check.
    stray = []
    for f in sorted(tools.glob("*.py")):
        if f.name == "export_probe.py":
            continue                       # where the one loader lives
        if "ChatterboxTTS.from_pretrained" in f.read_text(encoding="utf-8"):
            stray.append(f.name)
    if stray:
        return False, ("LOADS THE MODEL DIRECTLY, bypassing the watermarker "
                       "guard: " + ", ".join(stray))
    # `stft_patch.py` is here because its checks are the ones that can go
    # quietly wrong: it substitutes a computation, and a substitute that
    # exports while computing something else is worse than the blocker it
    # replaces. `fixture.py` is here because a stand-in that stops failing the
    # way the real thing fails certifies the probe against nothing.
    # `sampler-reference.py` is here for the newest and least visible risk in
    # this whole route. `Core/SpeechLoop` reimplements chatterbox's token
    # sampler in C#, because the loop it sits in cannot be exported — and
    # every way of getting a sampler wrong still produces speech. Wrong
    # temperature, a penalty applied in the wrong direction, a filter the model
    # does not use: all of them yield a voice saying the words and sounding
    # slightly off, with no error anywhere. This runs the model's real
    # HuggingFace processors so the C# side has something to be identical TO.
    for script in ("probe.py", "export_probe.py", "stft_patch.py", "fixture.py",
                   "kv_cache.py", "sampler-reference.py", "vocoder.py",
                   "speak.py", "precompute-voices.py", "tokenizer-reference.py",
                   "export-for-game.py", "export-decode.py", "check-graphs.py",
                   "time-the-shape.py", "speak-a-few.py", "probe-step-costs.py",
                   "convert-fp16.py", "bench-binding.py", "hear-chunks.py"):
        if not (tools / script).exists():
            continue
        code, out = run(["python3", str(tools / script), "--selftest"])
        m = re.search(r"(\d+) (?:checks|cases)", out)
        # A SCRIPT NEEDING TORCH CANNOT RUN EVERYWHERE, and a missing import is
        # not a failing check. Skipped and SAID, rather than counted as a pass
        # — a gate that goes quiet when its subject is absent reads as green.
        # A SKIP MUST NOT READ AS A PASS, and `vocoder.py` skips on
        # chatterbox rather than on torch — it needs the real class, which
        # only the package has. Named in the footer either way.
        if code != 0 and "ModuleNotFoundError" in out and "torch" in out:
            skipped.append(script)
            continue
        if code != 0:
            bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
            return False, "VOICE LIVE (%s): %s" % (script, bad[0][:70] if bad else "no report")
        total += int(m.group(1)) if m else 0
    n = total
    if True:
        note = (", %d skipped without torch: %s" % (len(skipped), " ".join(skipped))
                if skipped else "")
        return True, "voice-live ok (%s checks%s)" % (n, note)
    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
    return False, "VOICE LIVE: " + (bad[0][:90] if bad else "did not report")


def voice_gen():
    """M17.2: the bark renderer's own self-test, run on every commit.

    It cannot render here — chatterbox needs a GPU and lives on Jafar's
    machine — so everything that DECIDES a render is what gets checked: which
    slots are real lines rather than the pair slots the game assembles at run
    time, that every slot has an authored direction, that the six street
    voices carry an equal share, and that no two renders collide on a name.

    Wired in here rather than left as a command somebody remembers, because a
    self-test nobody runs is rule 6 wearing a lab coat. It also guards the
    finding the whole batch size rests on: 2,268 of the bank's 2,604 lines are
    `telling || reply` concatenations of lines that already exist, so the real
    batch is 336. If somebody adds a pair slot under a new name, or an atomic
    slot with no direction, this goes red on the commit that did it rather
    than after a night of rendering the wrong thing."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "voice-gen" / "ledger_voice_gen.py"),
                     "--selftest"])
    m = re.search(r"(\d+) checks, (\d+) renders", out)
    n, renders = (m.group(1), m.group(2)) if m else ("0", "0")
    if code == 0:
        return True, "voice-gen ok (%s checks, %s-line batch)" % (n, renders)
    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
    return False, "VOICE GEN: " + (bad[0][:90] if bad else "did not report")


def barks_current():
    """The bark bank must still be the lines the code actually speaks.

    THREE RECORDINGS WERE DELETED BY A PUNCTUATION PASS AND NOTHING SAID SO.
    `barks.json` is not authored — its own header says "enumerated from
    Core/StreetVoice.cs" — and `VoiceBank.ClipName` keys a clip by (voice,
    EXACT text). So changing "Sorry, in a hurry." to "Sorry — in a hurry."
    does not edit a recording, it orphans one and asks for a clip that was
    never rendered. Found 13 August from the other end: a build reported
    seven misses that were not composed lines, and all of them were this.

    The cause is worth naming because it will recur. `slop()` above exists to
    drive em dashes OUT of player-facing text, and it worked — somebody
    edited four bark lines to satisfy it. Two guards, pulling on the same
    strings, and the one that owns the audio had no idea the other existed.

    So: run the enumerator into a temporary file and compare. Naming the
    drifted lines matters more than the count, because the fix differs — a
    reworded line needs rendering, a line deleted from the code needs its
    clips retiring, and a count of four cannot tell you which you have.
    """
    import json
    import tempfile
    barks = ROOT.parent / "game-design" / "barks.json"
    if not barks.exists():
        return False, "BARKS: game-design/barks.json is missing"
    with tempfile.TemporaryDirectory() as tmp:
        fresh = pathlib.Path(tmp) / "barks.json"
        code, out = run(["dotnet", "run", "-c", "Release",
                         "--project", str(ROOT / "BarkGen"), "--", str(fresh)])
        if code != 0 or not fresh.exists():
            return False, "BARKS: the enumerator did not run — " + out[-90:].strip()
        try:
            was = json.loads(barks.read_text(encoding="utf-8"))
            now = json.loads(fresh.read_text(encoding="utf-8"))
        except ValueError as e:
            return False, "BARKS: unreadable — %s" % e

    def lines_of(doc):
        out = set()
        for slot in doc.get("slots", []):
            for line in slot.get("lines", []):
                out.add(" ".join(line.split()))
        return out

    committed, current = lines_of(was), lines_of(now)
    added, dropped = current - committed, committed - current
    if added or dropped:
        first = sorted(added)[0] if added else sorted(dropped)[0]
        return False, ("BARKS: %d line(s) in the code are not in the bank and "
                       "%d in the bank are no longer spoken — their clips are "
                       "orphaned and the new ones have none. Re-run "
                       "`dotnet run --project ledger/BarkGen` and render. "
                       "First: %s" % (len(added), len(dropped), first[:60]))
    return True, "barks current (%d lines enumerated, 0 drifted)" % len(current)


def voice_cast():
    """M17.3: a principal whose cast voice cannot reach them.

    `VoiceBank.VoiceFor` falls back to the crowd pool for an unknown id rather
    than throwing, which is right for robustness and means a MISCAST principal
    is an entirely silent bug. Two were found this way — `# Hal` carrying id
    `halvard` against a cast voice named `hal`, and `# Sera Kest` carrying id
    `sera` against `kest`. Both clips had been fetched weeks earlier and could
    never play.

    Fails on breakage (an alias pointing at no voice, a cast voice with no
    clip). REPORTS the not-yet-cast, because that is M17.3's remaining work and
    a check that is red for a known reason is one people learn to skip."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "voice-cast-check.py")])
    m = re.search(r"(\d+) principal\(s\) not cast yet", out)
    todo = m.group(1) if m else "0"
    if code == 0:
        return True, "voice cast ok (%s uncast principal(s))" % todo
    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("- ")]
    return False, "VOICE CAST: " + (bad[-1][:90] if bad else "did not report")


def save_chaos():
    """Layer 4 of the testing system: what a save does when it is not a save.

    `SaveCodec` had twenty CoreTests and every one of them wrote a file and read
    it back, which proves the codec agrees with ITSELF — the one property a save
    on a player's disk cannot be relied on to have. The interesting file is
    truncated by a full disk, half-written by a crash, hand-edited, or produced
    by a build that no longer exists, and none of those look like `Capture`'s
    output.

    Six real faults on its first run, all of them reachable by a player:

      `Fact` dereferenced a null subject      -> NRE escaped Restore entirely
      `GossipMill.Get(null)`                  -> ArgumentNullException, likewise
      a save with no `day`                    -> loaded into day 0, silently
      `(int)d` on 9.2e18                      -> jobsMissed = MINUS two billion
      `"dirty": -1e308`                       -> an unseizable, broke player
      `"patience": 0.6e999`                   -> Infinity; the outfit never
                                                 loses patience again

    The first two matter most: the front end catches `SaveIncompatibleException`
    and nothing else, so both of those were a stack trace on the load screen.

    Runs the default seed here. The gate is per-property per-family rather than
    per-sample — 300 samples asserted individually is 300 lines of green saying
    one thing, which is the mistake that took CoreTests to 14,953 checks."""
    code, out = run(["dotnet", "run", "-c", "Release", "--project", str(ROOT / "SaveChaos")])
    m = re.search(r"save chaos ok — all (\d+) checks passed", out)
    if m:
        return True, "%s save-chaos checks" % m.group(1)
    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAILED")]
    if bad:
        return False, "SAVE CHAOS: " + bad[0][7:97]
    return False, "save chaos did not report (build failure?)"


def soak():
    """Layer 4's other half: five hundred days, twice, and does it match.

    `BalanceLab` already drives this loop for four hundred weeks a policy and
    asks whether the numbers are GOOD. This asks whether they are NUMBERS —
    determinism (same seed, identical per-day digest, naming the first divergent
    day), no NaN or negative anywhere in five hundred days, and a printed growth
    series for everything that accumulates.

    THE GROWTH SERIES IS WHY IT EXISTS, and it found a leak on its first run:
    `SuspicionTracker.Reasons` climbed to 684 entries over 499 days, strictly
    monotonically, at +1.363 a day. The rumour counts in the same run oscillated
    between 9 and 74 — gossip decays — and the CONTRAST is what made one legible
    as a leak and the other as traffic. Neither is visible from a total.

    Two seconds, so it runs on every commit rather than nightly."""
    code, out = run(["dotnet", "run", "-c", "Release", "--project", str(ROOT / "Soak")])
    m = re.search(r"soak ok — all (\d+) checks passed", out)
    if m:
        return True, "%s soak checks (500 days x2)" % m.group(1)
    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAILED")]
    if bad:
        return False, "SOAK: " + bad[0][7:100]
    return False, "soak did not report (build failure?)"


def adversary():
    """Layer 5: the two places where text nobody wrote becomes an action.

    `IntentRouter.Validate` is the one function in this project written as a
    security boundary — *"anything not provably a member of the offered set
    becomes speech"* — and a boundary nobody has attacked is a boundary nobody
    has tested. It holds: no verb outside the catalogue was ever routed, through
    injection, fenced JSON, casing games or prose wrapped around the payload.

    TWO FINDINGS, AND THE FIRST WAS MINE. Every family asserts something is
    REFUSED, so a router that refused everything would score perfectly — and the
    first run printed `routed=0` down the whole column, which I read as a clean
    sweep. It is equally the shape of a fuzzer that never reached the code. The
    positive controls added next failed immediately, and the one that failed was
    the CONTROL: it asserted "pay them off" routes, when the router deliberately
    refuses a verb whose arguments it cannot fill for free. Suspect the
    instrument first.

    The real finding is small and public: `ResponseValidator` cut a reply to
    `MaxChars` and then appended an ellipsis, so the one thing that constant
    promises was false by exactly one character for every endless sentence a
    model produced. Measured at 901, not reasoned about."""
    code, out = run(["dotnet", "run", "-c", "Release", "--project", str(ROOT / "Adversary")])
    m = re.search(r"adversary ok — all (\d+) checks passed", out)
    if m:
        return True, "%s adversary checks" % m.group(1)
    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAILED")]
    if bad:
        return False, "ADVERSARY: " + bad[0][7:100]
    return False, "adversary did not report (build failure?)"


def verdict_keys():
    """Every measurement the verdict is supposed to carry is still in it.

    `verdict.txt` is the only channel out of CI this environment can read, and
    it is assembled by a grep in the workflow over a log the sim prints. Every
    link breaks QUIETLY: a `Debug.Log` reworded and the grep stops matching, a
    metric dropped in a refactor, a gate that stops being evaluated and takes
    its clause with it, an edited pattern that loses an alternation. In all of
    them the verdict still arrives, still says `pass=True`, and is simply
    missing the number that would have said otherwise.

    That is this project's oldest defect shape — a success recorded because the
    thing that would have failed was never asked. So the keys are committed and
    compared: a key that disappears is an error, a key that appears is offered
    to the manifest with `--learn` so growth is a decision.

    Checks the QUESTIONS, not the answers. `pass=True` is the gates' job."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "verdict-keys.py")])
    # ANCHORED ON THE TAIL, which is the part that means something. The line
    # gained an `N always + M gate-only` prefix when the checker learned to tell
    # a gate label from a measurement, and the old pattern — which began at
    # `present` — stopped matching and reported "did not report" while the tool
    # underneath was perfectly healthy. A parser is a claim about another
    # program's output and decays the moment that output is edited.
    m = re.search(r"(\d+) required, (\d+) missing, (\d+) new", out)
    if not m:
        return False, "verdict-keys did not report"
    if code != 0:
        gone = [l.strip()[5:] for l in out.splitlines() if l.strip().startswith("GONE")]
        demoted = [l.strip()[8:] for l in out.splitlines() if l.strip().startswith("DEMOTED")]
        if gone:
            return False, "VERDICT KEYS GONE: " + ", ".join(gone[:4])
        return False, "VERDICT KEYS NOW GATE-ONLY: " + ", ".join(demoted[:4])
    tail = "" if m.group(3) == "0" else ", %s new (run --learn)" % m.group(3)
    return True, "%s verdict keys%s" % (m.group(1), tail)


def verdict_format():
    """The verdict is space-separated `key=value`, and one value broke it.

    `crowdBodyWidth` was emitted as `0.45(narrowest 0.39 broadest 0.53)` and
    every reader in the project — including `verdict-read.py` itself — happily
    returned `0.45(narrowest` with no sign anything had gone wrong. A rule in
    CLAUDE.md would not have caught it: that value was written an hour after
    reading the rules that morning.

    NOT WIRED UNTIL A VERDICT PROVED IT GREEN, deliberately, and that took two
    builds. It reported a hit on the last landed verdict for a fault already
    corrected in the emitter, so wiring it then would have blocked every commit
    until CI came back — rule 5b's exact failure, a guard that has never been
    run against the case it must PASS. `--selftest` is now the standing version
    of that check: it asserts the accepting case FIRST and the rejecting case
    second, so the two halves cannot rot apart.

    Both are run here. The selftest says the lint still works at all; the lint
    says the newest measuring run is well-formed. A green selftest with no
    verdict to read is still worth having — it is the half that does not depend
    on CI."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "verdict-read.py"),
                     "--selftest"])
    if code != 0:
        first = next((l.strip() for l in out.splitlines() if "FAILED" in l),
                     "see verdict-read --selftest")
        return False, "VERDICT LINT BROKEN: " + first[:110]
    code, out = run(["python3", str(ROOT.parent / "tools" / "verdict-read.py"),
                     "--lint"])
    if code != 0:
        first = next((l.strip() for l in out.splitlines() if l.strip().startswith("line ")),
                     "see verdict-read --lint")
        return False, "VERDICT VALUE WITH A SPACE IN IT: " + first[:110]
    return True, "verdict format ok (selftest + newest run)"


def verdict_dupkeys():
    """One key, two values — the write-time half of the verdict-read guard.

    `verdict-read.py` refuses when the keys you ASK FOR do not share a line.
    That protects reads routed through it and nothing else, and nobody had ever
    asked the file as a whole which of its keys are ambiguous.

    MEASURED on the landed verdict, not suspected: `collidingWorldText` read 5
    on the glyphs line and 9 on the done line of the same run, and `clean=`
    appeared TWICE on the done line with 310 and 0. A `grep -o` returns
    whichever it reaches first, silently. Both are repaired in the emitter by
    the commit that adds this.

    ONLY THE SELFTEST IS GATED, AND THAT IS THE POINT OF RULE 5b'S COROLLARY.
    The landed verdict still carries the collisions, because it came from the
    build BEFORE the repair — so gating on the file would go red on arrival and
    block every commit until a twenty-eight-minute round trip landed. Exactly
    the shape `verdict_format` above had to learn. So: the selftest must pass
    (the tool works), the file is REPORTED with its counts (rule 3b — the
    denominator ships with the zero), and gating waits for a verdict that
    proves the accepting case exists. That step is written down in
    `game-design/queue.md`, not left to be remembered."""
    tool = str(ROOT.parent / "tools" / "verdict-dupkeys.py")
    code, out = run(["python3", tool, "--selftest"])
    if code != 0:
        first = next((l.strip() for l in out.splitlines() if "Error" in l or "assert" in l),
                     "see verdict-dupkeys --selftest")
        return False, "VERDICT DUPKEY CHECK BROKEN: " + first[:110]
    # ABSOLUTE, BECAUSE `run` STANDS IN `ledger/`. The first version passed no
    # path and the tool's own relative default resolved against the wrong
    # directory, so the footer read "cannot read ... No such file" and the
    # check still returned ok — a tool reporting on nothing, which is the
    # `BarkGen` manifest fault (rule 3) reproduced within the hour of reading
    # about it. `verdict.txt` is not tracked between builds, so ABSENT is a
    # normal state and says so distinctly from EMPTY.
    verdict = ROOT.parent / "game-design" / "sim-shots" / "verdict.txt"
    if not verdict.exists():
        return True, "dupkeys ok (selftest); no landed verdict to read"
    code, out = run(["python3", tool, str(verdict)])
    head = next((l.strip() for l in out.splitlines()
                 if l.startswith("verdict-dupkeys:")), "")
    if not head or "cannot read" in head:
        return False, "DUPKEY CHECK READ NOTHING: " + (head or out.strip())[:110]
    return True, head.replace("verdict-dupkeys: ", "dupkeys ok (selftest); landed verdict: ")


def gate_detail_ceiling():
    """No nineteenth gate that cannot name its own failure.

    `dayJob` failed 84 times across 308 runs and never printed a reason,
    because its table entry is a bare `("dayJob", dayJobOk)`. It went
    undiagnosed for months not through neglect but because there was nothing
    to read — and the moment it was given its three operands, the tracer
    beside it named the cause in one landing.

    SimDirector's gate table already carries that argument, written for ONE
    gate and applied to one. Eighteen were left. This does not demand they be
    fixed — each needs its condition read and its operands chosen, which is
    judgement rather than a rename — it refuses a NINETEENTH.

    A ceiling on a COUNT and not a list of blessed names, because a list
    decays: it wants editing on every rename and an entry nobody re-reads is
    the reach ledger's own failure mode. An integer cannot go stale and can
    only be lowered."""
    tool = str(ROOT.parent / "tools" / "gate-detail.py")
    code, out = run(["python3", tool, "--selftest"])
    if code != 0:
        return False, "GATE DETAIL CHECK BROKEN: " + out.strip()[:110]
    code, out = run(["python3", tool])
    head = next((l.strip() for l in out.splitlines()
                 if l.startswith("gate-detail:")), "")
    if code != 0:
        return False, head[:170] or "gate-detail failed with no message"
    return True, head.replace("gate-detail: ", "gates ")


def runs_map_to_commits():
    """Two checks about run files and commits, and the second one is the point.

    THE FAULT: six tools ordered runs by commit with `sha in have` — exact
    equality between `git log --format=%h` and a run file's stem. Git sizes
    that abbreviation to whatever stays unambiguous, and as this repository
    grew it went from SEVEN characters to EIGHT while run files kept seven.
    Every one of those comparisons stopped matching: 0 of 333 run files
    against 400 commits, measured 24 Aug. Nothing failed, because unmatched
    runs fall into a fallback sorted by SHA, which is sorted by nothing, and
    every tool kept printing plausible numbers.

    AND MY FIRST GUARD FOR IT COULD NOT HAVE CAUGHT IT. I wrote one that
    counts prefix matches and called it the fix. Tested against the exact
    broken state it passed identically — 122 hits either way — because a
    PREFIX match is happy to compare an eight-character hash to a
    seven-character stem. That is the whole repair; `%H` merely makes it
    unconditional. A guard whose rejecting case does not exist is rule 5b's
    own failure, so it is replaced rather than kept for the comfort of it.

    What actually broke is an invariant nobody stated: the abbreviation git
    hands out is the same width as the names we file runs under. That is
    checkable, it has a real rejecting case (it is FALSE today — 8 against 7),
    and it is what would have fired the day it changed. It is a WARNING and
    not a failure, because the tools use prefix matching now and are immune;
    it exists so the next person who writes `==` against a stem is told.
    """
    runs = ROOT.parent / "game-design" / "sim-shots" / "runs"
    if not runs.is_dir():
        return True, "no runs directory yet"
    stems = {p.stem for p in runs.glob("*.txt")}
    if not stems:
        return True, "no run files yet"
    code, out = run(["git", "-C", str(ROOT.parent), "log", "--format=%H", "-400"])
    if code != 0 or not out.strip():
        return True, f"runs ok ({len(stems)} file(s), no git history to check against)"
    log = out.split()
    hit = sum(1 for full in log for stem in stems if full.startswith(stem))
    if hit == 0:
        return False, (f"NO RUN FILE MATCHES ANY COMMIT: {len(stems)} run file(s) "
                       f"against {len(log)} commit(s) — the naming convention and "
                       f"the log format have diverged entirely.")
    # The invariant that actually broke, reported rather than gated.
    ab, abbrev = run(["git", "-C", str(ROOT.parent), "log", "--format=%h", "-1"])
    stem_len = len(next(iter(stems)))
    note = ""
    if ab == 0 and abbrev.strip():
        n = len(abbrev.strip())
        if n != stem_len:
            note = (f"; NOTE abbrev is {n} chars and run files are {stem_len} — "
                    f"compare by PREFIX, never by equality")
    return True, f"runs map to commits ({hit} of {len(stems)} within {len(log)}){note}"


def verdict_emit_dupkeys():
    """The same fault, caught in the SOURCE instead of one round trip later.

    `verdict_dupkeys` above reads the landed verdict. That is correct and it is
    a quarter of an hour too late: the collision is written in C#, dispatched,
    built, committed and pulled before anything can see it.

    MEASURED, on the commit this ships beside. Wiring `Core/DoorSwing` added
    `doors={DoorHost.Count}/...` to the done line, and `doors=` was already
    there — `WorldBuilder.Doors`, three hundred lines further down the SAME
    `Debug.Log`. Nothing would have failed. The damage is not to the new key
    but to the OLD one, which had been readable for weeks and would silently
    have stopped being. It was caught by eye, and this file is a list of what
    happens when a rule depends on that.

    GATED ON BOTH HALVES, unlike its landed-verdict sibling, and that is the
    difference rule 5b asks about: the accepting case EXISTS here. The two real
    hits — `Traffic: wheels` under `dia/hi=`, and three sub-records sharing
    `eyes=`/`noticed=`/`considered=` on the places line — are repaired in the
    same commit, so the whole repository reads zero today and any new one is a
    red. There is no baseline list to decay."""
    tool = str(ROOT.parent / "tools" / "verdict-emit-dupkeys.py")
    code, out = run(["python3", tool, "--selftest"])
    if code != 0:
        first = next((l.strip() for l in out.splitlines()
                      if "Error" in l or "assert" in l),
                     "see verdict-emit-dupkeys --selftest")
        return False, "EMIT DUPKEY CHECK BROKEN: " + first[:110]
    code, out = run(["python3", tool, str(ROOT / "Assets" / "Scripts")])
    head = next((l.strip() for l in out.splitlines()
                 if l.startswith("verdict-emit-dupkeys:")), "")
    if not head:
        return False, "EMIT DUPKEY CHECK READ NOTHING: " + out.strip()[:110]
    if code != 0:
        hits = [l.strip() for l in out.splitlines() if " — emitted twice" in l]
        return False, "SAME KEY EMITTED TWICE ON ONE LINE: " + "; ".join(hits)[:160]
    return True, head.replace("verdict-emit-dupkeys: ", "emit dupkeys ok (")\
                    .replace(" same-line duplicate key(s) (", ", ") + ")"


def frame_drift():
    """Layer 3 of the testing system: the instrument that reads the render.

    SUSPECT THE INSTRUMENT FIRST. `tools/frame-drift.py` answers "what moved in
    the picture since the last build", and the expected answer is "nothing much"
    — which is also exactly what it would print if it were broken, if the sim
    had written no ledger, or if it were comparing the new file against itself.
    A tool whose failure mode is indistinguishable from its success mode gets
    believed, so its self-test is run here rather than trusted.

    Twenty-one checks, and the ones that matter are the negative space: a
    missing new ledger must be an ERROR and not a quiet zero, a dropped shot
    must be named, and a change of one part in twenty-five must survive the
    formatting."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "frame-drift.py"), "--selftest"])
    m = re.search(r"selftest: (\d+) passed, (\d+) failed", out)
    if not m:
        return False, "frame-drift selftest did not report"
    return m.group(2) == "0", "%s frame-drift checks (%s failed)" % (m.group(1), m.group(2))


def stale_anchors():
    """Every break's anchor, checked for a single exact match.

    NEARLY FREE, and it finds the thing a break run reports as a survivor and
    nobody looks twice at. An anchor whose source has moved on matches zero
    times, so the break never runs — and `breakrun.py` counts that as a
    survivor in a list of survivors, which is where it goes to die.

    Sweeping all of them after the harness fix found three, in specs nobody
    had reason to suspect: two in `exposure` where the aperture line gained a
    daytime term, one in `perception` where a literal 0.35 became
    `StillBelow`. Both changes were right; the specs had simply rotted around
    them. That is three checks the project believed it had."""
    import json
    bad = []
    for spec in sorted((ROOT / "breaks").glob("*.json")):
        try:
            entries = json.loads(spec.read_text(encoding="utf-8"))
        except ValueError as e:                       # noqa: BLE001
            bad.append("%s unparseable: %s" % (spec.name, e))
            continue
        for i, b in enumerate(entries):
            src = ROOT / b["file"]
            n = src.read_text(encoding="utf-8").count(b["old"]) if src.exists() else 0
            if n != 1:
                bad.append("%s[%d] matches %dx" % (spec.name, i, n))
    if bad:
        return False, "STALE ANCHORS: " + "; ".join(bad[:4])
    return True, "0 stale anchors"


# --------------------------------------------------------- director cadence
# CLAUDE.md, THE HYBRID RESIDENT (24 Aug). The resident session runs on Opus;
# Fable is the on-demand `studio-director`. These four constants are the whole
# contract, in one place, because the check and its fixtures must not be able
# to disagree about it.
DIRECTOR_MIN_LINES = 100                      # MORE than this is "substantial"
DIRECTOR_SCRIPTS = "ledger/Assets/Scripts/"   # git paths are repo-root relative
DIRECTOR_LOG = ".claude/agent-log.tsv"
DIRECTOR_AGENT = "studio-director"


def _git(repo, *args):
    """git stdout ONLY, uncontaminated — deliberately not `run()` above.

    `run()` returns stdout+stderr concatenated, which is right for a build log
    and wrong here: one `hint:` or `warning:` line from git lands in the middle
    of a `--numstat` parse and gets counted as a file. The numbers this feeds
    decide whether a commit is blocked, so the channel is kept clean."""
    p = subprocess.run(["git", "-C", str(repo)] + list(args),
                       capture_output=True, text=True)
    return p.returncode, p.stdout


def _cadence_epoch(text):
    """One ISO8601 UTC stamp -> epoch seconds, or None when it cannot be dated.

    UNDATEABLE IS ABSENT, NEVER FRESH. The expensive direction of a lenient
    parser here is a corrupt row certifying a review that never happened, so
    anything this cannot read is counted as an unparsable row and excluded
    from the freshness count rather than guessed at."""
    s = (text or "").strip()
    if not s:
        return None
    if s.endswith(("Z", "z")):                       # 3.9/3.10 fromisoformat
        s = s[:-1] + "+00:00"                        # cannot read a bare Z
    for attempt in (s, s.replace(" ", "T", 1)):
        try:
            dt = datetime.datetime.fromisoformat(attempt)
        except ValueError:
            continue
        if dt.tzinfo is None:        # the log's own contract is UTC (log-agent.sh)
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.timestamp()
    return None


def _cadence_read(repo):
    """The reading, as a dict — ONE implementation, shared by the check, the
    `--cadence` printer and every fixture in the selftest.

    What each number is a statistic OF, because a number whose statistic is
    unnamed is the thing this project keeps mis-reading:

      changed   CUMULATIVE total of PENDING lines against HEAD under
                `ledger/Assets/Scripts/` — `tracked` + `untracked`, and the
                ONLY number compared against the threshold
      tracked   CUMULATIVE adds+dels over the staged+unstaged diff vs HEAD
      untracked LINES in untracked files under Assets/Scripts — a component
                of `changed` since 24 Aug, not a footnote to it (see below)
      rows      COUNT of data rows in the agent log — the denominator every
                zero below is meaningless without
      since     COUNT of `studio-director` rows dated strictly AFTER HEAD's
                commit time; the numerator, taken from the same read of the
                same file as `rows`
      stale     COUNT of `studio-director` rows dated at or before HEAD
      unparsed  COUNT of rows that could not be dated — treated as ABSENT

    WHY UNTRACKED CONTENT IS COUNTED RATHER THAN NOTED — the gate's largest
    hole, closed 24 Aug after a sibling repo found the same shape. A file git
    has never been told about is invisible to `git diff HEAD` ENTIRELY, so a
    brand-new 300-line module under Assets/Scripts read `0 changed line(s) ...
    under threshold, review not required` and exited 0, while printing a NOTE
    naming the 300 lines it had just declined to count. Reproduced on a fixture
    repo before this was written: `changed=0 untracked=300 state=ok exit=0`.

    THE WINDOW, measured rather than assumed, because it decides how often this
    bites: `git diff HEAD` DOES see a new file once it is STAGED (300/0 in
    --numstat) and sees nothing at all before that. So the blind spot is
    exactly "verify run before `git add`" — which is the documented order
    (`python3 ledger/verify.py && git commit -F -`) and the studio's standing
    builder handoff, where tier 3 leaves a new module uncommitted AND unstaged
    for the director to review. Checked against the last 60 commits: 8 were
    substantial, 1 introduced a new Scripts file (230 lines), and that one also
    carried 129 lines of edits to existing files, so NO commit in recorded
    history was actually misclassified. The hole is real, reproducible, and had
    not yet fired — which is the state in which it is cheapest to close.

    The bound is unchanged and did not need to change, because the SERIES it
    came from already counts new files at full size: per-commit lines under
    Scripts over the last 60 commits are 37 zeroes, 19..81, then
    107 128 130 132 302 352 359 415, and the one commit in those 60 that
    introduced a new Scripts file contributed all 230 of its lines to that
    distribution. Counting a pending new file as zero made the gate's input a
    different population from the bound's evidence; this makes them the same
    measurement.

    KNOWN BLIND SPOT, stated rather than discovered later: a director row
    newer than HEAD proves a spawn happened after the last commit, not that it
    reviewed THESE lines. It cannot distinguish those, and it is not trying
    to — the failure it exists for is the review that never happened at all.
    """
    repo = pathlib.Path(repo)
    r = {"changed": 0, "tracked": 0, "files": 0, "binary": 0, "rows": 0,
         "since": 0, "stale": 0, "unparsed": 0, "unparsed_dir": 0,
         "untracked": 0, "untracked_files": 0, "untracked_binary": 0,
         "unreadable": 0, "log": True, "newest_dir": "", "head_iso": "",
         "state": "ok"}

    code, out = _git(repo, "show", "-s", "--format=%ct", "HEAD")
    head_ct = None
    if code == 0 and out.strip().isdigit():
        head_ct = int(out.strip())
        r["head_iso"] = datetime.datetime.fromtimestamp(
            head_ct, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if head_ct is None:
        r["state"] = "nohead"
        r["summary"] = ("director cadence: no HEAD commit — nothing measured "
                        "(0 changed lines, 0 log rows examined)")
        r["ok"] = True
        return r

    code, out = _git(repo, "diff", "HEAD", "--numstat")
    for line in out.splitlines():
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        adds, dels, path = cols[0], cols[1], "\t".join(cols[2:])
        # A rename printed as `a/{x => y}/f.cs` only matches when the literal
        # prefix survives it. Pure renames carry 0/0 lines anyway, so the
        # worst case is a rename OUT of Scripts reading as 0 — noted, not
        # papered over.
        if DIRECTOR_SCRIPTS not in path:
            continue
        r["files"] += 1
        if adds == "-" or dels == "-":           # binary: no line count exists
            r["binary"] += 1
            continue
        r["tracked"] += int(adds) + int(dels)

    # THE ENUMERATOR IS THE ONE ALREADY HERE, and that is the point. A sibling
    # repo's twin of this gate walked `git status --porcelain`, which COLLAPSES
    # a new directory into ONE non-file entry (`?? NewMod/`) — so a 300-line
    # module in a new folder counted as a single path with no lines, and only
    # `-uall` expands it. `ls-files --others` has no directory mode unless
    # asked for one, so it expands BY CONSTRUCTION: measured both ways on a
    # fixture repo before this comment was written —
    #   status --porcelain      -> `?? ledger/Assets/Scripts/NewMod/`
    #   status --porcelain -uall-> `?? ledger/Assets/Scripts/NewMod/Big.cs`
    #   ls-files --others       -> `ledger/Assets/Scripts/NewMod/Big.cs`
    # One idea, one implementation: this loop already existed and already
    # enumerated correctly; what was missing was that its total never reached
    # the threshold comparison.
    code, out = _git(repo, "ls-files", "--others", "--exclude-standard")
    for rel in out.splitlines():
        if DIRECTOR_SCRIPTS not in rel:
            continue
        r["untracked_files"] += 1
        try:
            data = (repo / rel).read_bytes()
        except OSError:                          # a symlink to a dir, a race
            r["unreadable"] += 1                 # counted, never silently 0
            continue
        # BINARY IS 0 LINES AND SAYS SO, the same treatment `--numstat`'s "-"
        # gets three lines up. Now that this number BLOCKS commits, decoding a
        # .dll or a .png with errors="replace" and calling the result "lines"
        # would be a false RED — the direction rule 5b says is the expensive
        # one, since this gate can block every commit in the project.
        if b"\x00" in data:
            r["binary"] += 1
            r["untracked_binary"] += 1
            continue
        r["untracked"] += len(data.decode("utf-8", "replace").splitlines())

    # THE GATED TOTAL, named as the sum it is. Both components print beside it
    # in the summary as one paired reading, so "0 changed" can never again mean
    # "0 counted and 300 declined".
    r["changed"] = r["tracked"] + r["untracked"]

    log = repo / DIRECTOR_LOG
    if not log.exists():
        r["log"] = False
    else:
        first = True
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            cols = line.split("\t")
            if first and cols[0].strip() == "when":
                first = False                      # the header is not a row
                continue
            first = False
            r["rows"] += 1
            when = cols[0] if cols else ""
            agent = cols[1].strip().lower() if len(cols) > 1 else ""
            ts = _cadence_epoch(when)
            if ts is None:
                r["unparsed"] += 1
                if agent == DIRECTOR_AGENT:
                    r["unparsed_dir"] += 1
                continue
            if agent != DIRECTOR_AGENT:
                continue
            if ts > head_ct:
                r["since"] += 1
            else:
                r["stale"] += 1
            if not r["newest_dir"] or ts > _cadence_epoch(r["newest_dir"]):
                r["newest_dir"] = when.strip()

    substantial = r["changed"] > DIRECTOR_MIN_LINES
    if substantial and not r["log"]:
        r["state"] = "logmissing"
    elif substantial and r["since"] == 0:
        r["state"] = "unspawned"
    r["ok"] = r["state"] == "ok"
    r["summary"] = _cadence_summary(r)
    return r


def _cadence_summary(r):
    """One line, and it ALWAYS carries the denominators (rule 3b).

    Three zeroes live in this reading and each would read as health on its
    own: no changed lines, no director rows, no log rows. So every branch
    prints the changed count beside its threshold and the director count
    beside the number of rows examined — and a log with no rows at all says
    "nothing measured" in those words, because "we looked at eight rows and
    found no director" and "we looked at nothing" are different facts with
    different next actions."""
    # THE PAIRED READING: the gated total and BOTH its components in one
    # entry, always, including when a component is zero. Printed unconditionally
    # because the hole this closed was exactly a reader taking "0 changed
    # line(s)" for "nothing is pending" while 300 untracked lines sat beside it
    # in a note — two keys whose relationship the reader had to remember.
    lines = ("%d changed line(s) (%d tracked + %d untracked in %d new file(s)) "
             "vs %d threshold under Assets/Scripts" % (
                 r["changed"], r["tracked"], r["untracked"],
                 r["untracked_files"], DIRECTOR_MIN_LINES))
    if not r["log"]:
        rows = "agent log ABSENT (%s) — nothing measured" % DIRECTOR_LOG
    elif r["rows"] == 0:
        rows = "0 log rows examined — nothing measured (log has no rows)"
    else:
        rows = "%d director row(s) since HEAD of %d log row(s) examined" % (
            r["since"], r["rows"])
    notes = ""
    if r["unparsed"]:
        notes += "; %d unparsable row(s) treated as absent (%d studio-director)" % (
            r["unparsed"], r["unparsed_dir"])
    # The old note here said untracked lines "are invisible to `git diff HEAD`
    # — stage them to be counted". That sentence was true when written and
    # became false the moment they were counted; it is deleted rather than
    # edited, because the split in `lines` above now says it with numbers.
    if r["binary"]:
        notes += ("; %d binary file(s) counted as 0 lines (%d of them untracked)"
                  % (r["binary"], r["untracked_binary"]))
    if r["unreadable"]:
        notes += "; %d untracked file(s) UNREADABLE, counted as 0 lines" % r["unreadable"]

    if r["state"] == "logmissing":
        return ("DIRECTOR LOG MISSING: %s, %s — an absent instrument is not "
                "compliance; spawn studio-director and let the hook write the "
                "row%s" % (lines, rows, notes))
    if r["state"] == "unspawned":
        seen = ""
        if r["stale"]:
            seen = " (%d director row(s) in the log, all older; newest %s vs HEAD %s)" % (
                r["stale"], r["newest_dir"] or "?", r["head_iso"])
        return ("DIRECTOR NOT SPAWNED: %s, %s%s — spawn studio-director for the "
                "batch review, then re-run verify%s" % (lines, rows, seen, notes))
    # THE WORD TRACKS THE NUMBER IT NAMES. "REVIEWED" is a claim about director
    # rows, so it is computed from `since` and not from the line count — a mutant
    # that disables the gate printed "REVIEWED" beside `0 director rows` while
    # this read the changed lines instead, which is the same defect as two
    # numbers derived from one variable, wearing an adjective.
    if r["changed"] > DIRECTOR_MIN_LINES:
        verdict = "over threshold, REVIEWED" if r["since"] else "over threshold"
    else:
        verdict = "under threshold, review not required"
    return "director cadence ok (%s, %s; %s)%s" % (lines, verdict, rows, notes)


def _cadence_fixture(work, name, added, rows, log=True, in_scripts=True,
                     untracked=0, untracked_binary=0):
    """One throwaway repo: a commit at a PINNED time, then a pending change.

    The commit date is pinned so "newer than HEAD" is arithmetic rather than a
    race with the wall clock — a fixture that passes because the test ran fast
    is a fixture that will fail on a slow machine and teach everyone to re-run
    the suite until it goes green."""
    d = work / name
    (d / "ledger" / "Assets" / "Scripts").mkdir(parents=True)
    (d / "game-design").mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GIT_AUTHOR_DATE="%d +0000" % CADENCE_FIXED_CT,
               GIT_COMMITTER_DATE="%d +0000" % CADENCE_FIXED_CT,
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    subprocess.run(["git", "init", "-q", "-b", "main", str(d)],
                   capture_output=True, text=True)
    target = (d / "ledger" / "Assets" / "Scripts" / "Sim.cs") if in_scripts \
        else (d / "game-design" / "notes.md")
    target.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(d), "add", "-A"], capture_output=True, text=True)
    subprocess.run(["git", "-C", str(d), "commit", "-q", "-m", "base"],
                   capture_output=True, text=True, env=env)
    if added:
        with target.open("a", encoding="utf-8") as fh:
            fh.write("".join("line %d\n" % i for i in range(added)))
    # THE HOLE, REPRODUCED BY CONSTRUCTION: a brand-NEW DIRECTORY, never added,
    # holding the lines. Not a new file in an existing folder — the directory
    # is what `git status --porcelain` collapses to one entry, and a fixture
    # that used an existing folder would pass against the broken version.
    if untracked or untracked_binary:
        u = d / "ledger" / "Assets" / "Scripts" / "NewMod"
        u.mkdir(parents=True, exist_ok=True)
        if untracked:
            (u / "New.cs").write_text(
                "".join("new %d\n" % i for i in range(untracked)), encoding="utf-8")
        if untracked_binary:
            # NUL bytes with plenty of \n around them: decoded as text this
            # would read as `untracked_binary` lines, which is the false RED.
            (u / "Blob.dll").write_bytes(b"\x00\xff\n" * untracked_binary)
    if log is not None and log is not False:
        p = d / DIRECTOR_LOG
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("when\tagent\n" + "".join("%s\t%s\n" % (w, a) for w, a in rows),
                     encoding="utf-8")
    return d


# FAIL READABLE: one exit code per outcome for `--cadence`, so a caller can
# tell "no fresh director row" from "the log is not there" without parsing
# prose. Asserted in the selftest, not just written down here.
CADENCE_EXIT = {"ok": 0, "nohead": 0, "unspawned": 1, "logmissing": 2}

CADENCE_FIXED_CT = 1700000000          # 2023-11-14T22:13:20Z, the fixtures' HEAD
CADENCE_FRESH = "2023-11-14T23:13:20Z"  # +1h  — after HEAD
CADENCE_STALE = "2023-11-14T21:13:20Z"  # -1h  — before HEAD


def _cadence_selftest():
    """Rule 5b, both ways, on a temp repo — ACCEPTING CASES FIRST.

    The accepting cases go first because this guard can block every commit in
    the project: the expensive failure here is not a review that slips through,
    it is a validator nothing survives. Two of the accepting cases exist only
    because of that — a large diff OUTSIDE Assets/Scripts, and a fresh row
    written with an offset instead of a Z.

    Returns (passed, failed, lines)."""
    import atexit
    import shutil
    import tempfile
    work = pathlib.Path(tempfile.mkdtemp(prefix="director-cadence-"))
    # CLEANED ON EXIT, HOWEVER THE RUN ENDS. The pair of lines below is the
    # one `frame-drift.py` carries: the sibling that lacked it leaked 17GB of
    # temp dirs in a day, because verify runs these selftests on every commit.
    atexit.register(shutil.rmtree, work, True)

    lines, passed, failed = [], 0, 0

    def say(cond, label, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            lines.append("  ok   " + label)
        else:
            failed += 1
            lines.append("  FAIL " + label + (" — " + detail if detail else ""))

    d = _cadence_fixture(work, "a1-small-no-director", 5,
                         [(CADENCE_FRESH, "systems-builder")])
    a1 = _cadence_read(d)
    say(a1["ok"] and a1["state"] == "ok",
        "ACCEPT small diff with no director row", a1["summary"])
    say("5 changed line(s) (5 tracked + 0 untracked in 0 new file(s)) "
        "vs 100 threshold" in a1["summary"]
        and "1 log row(s) examined" in a1["summary"],
        "ACCEPT summary carries both denominators and the tracked/untracked split",
        a1["summary"])

    d = _cadence_fixture(work, "a2-large-fresh", 150,
                         [(CADENCE_STALE, "systems-builder"),
                          (CADENCE_FRESH, "studio-director")])
    a2 = _cadence_read(d)
    say(a2["ok"] and a2["since"] == 1 and "REVIEWED" in a2["summary"],
        "ACCEPT large diff with a fresh director row", a2["summary"])

    d = _cadence_fixture(work, "a3-exactly-100", 100, [])
    a3 = _cadence_read(d)
    say(a3["ok"] and a3["changed"] == 100,
        "ACCEPT exactly 100 changed lines (the bound is MORE than 100)", a3["summary"])

    d = _cadence_fixture(work, "a4-large-outside", 500, [], in_scripts=False)
    a4 = _cadence_read(d)
    say(a4["ok"] and a4["changed"] == 0,
        "ACCEPT 500 lines outside Assets/Scripts", a4["summary"])

    d = _cadence_fixture(work, "a5-small-no-log", 5, [], log=False)
    a5 = _cadence_read(d)
    say(a5["ok"] and "nothing measured" in a5["summary"],
        "ACCEPT small diff with no log, and it says nothing measured", a5["summary"])

    d = _cadence_fixture(work, "a6-offset-stamp", 150,
                         [("2023-11-14T23:13:20.482+00:00", "studio-director")])
    a6 = _cadence_read(d)
    say(a6["ok"] and a6["since"] == 1,
        "ACCEPT a fresh row stamped +00:00 with fractional seconds", a6["summary"])

    # THE COLLAPSED-DIRECTORY PAIR, ACCEPTING SIDE FIRST (24 Aug). Counting
    # untracked content is a NEW WAY FOR THIS GATE TO GO RED, and this gate
    # blocks every commit in the project — so the small-new-module case is
    # asserted before the large one, and a binary blob is asserted not to be
    # decoded into hundreds of imaginary lines.
    d = _cadence_fixture(work, "a7-small-untracked-dir", 5,
                         [(CADENCE_FRESH, "systems-builder")], untracked=5)
    a7 = _cadence_read(d)
    say(a7["ok"] and a7["changed"] == 10 and a7["untracked"] == 5
        and a7["untracked_files"] == 1
        and "10 changed line(s) (5 tracked + 5 untracked in 1 new file(s))" in a7["summary"],
        "ACCEPT a SMALL new untracked directory, counted and split in the line",
        a7["summary"])

    d = _cadence_fixture(work, "a8-untracked-binary", 5, [], untracked_binary=400)
    a8 = _cadence_read(d)
    say(a8["ok"] and a8["changed"] == 5 and a8["untracked"] == 0
        and a8["untracked_binary"] == 1 and "binary file(s) counted as 0 lines" in a8["summary"],
        "ACCEPT a 400-line-looking untracked BINARY as 0 lines, and say so",
        a8["summary"])

    # REJECTING — the states the escalation rule actually decays into.
    d = _cadence_fixture(work, "r1-101-no-director", 101,
                         [(CADENCE_FRESH, "instrument-builder")])
    r1 = _cadence_read(d)
    say(not r1["ok"] and r1["state"] == "unspawned" and r1["changed"] == 101,
        "REJECT 101 changed lines with no director row", r1["summary"])

    d = _cadence_fixture(work, "r2-stale-only", 150,
                         [(CADENCE_STALE, "studio-director"),
                          (CADENCE_STALE, "studio-director")])
    r2 = _cadence_read(d)
    say(not r2["ok"] and r2["since"] == 0 and r2["stale"] == 2
        and "all older" in r2["summary"],
        "REJECT large diff with only STALE director rows", r2["summary"])

    d = _cadence_fixture(work, "r3-empty-log", 150, [])
    r3 = _cadence_read(d)
    say(not r3["ok"] and r3["rows"] == 0 and "nothing measured" in r3["summary"],
        "REJECT large diff with a header-only log", r3["summary"])
    # RULE 3b, ASSERTED RATHER THAN HOPED FOR: examined-nothing and
    # examined-rows-found-no-director must not print the same sentence.
    say("nothing measured" in r3["summary"] and "nothing measured" not in r1["summary"],
        "REJECT 0-rows-examined reads differently from no-director-found",
        r3["summary"] + " || " + r1["summary"])

    d = _cadence_fixture(work, "r4-no-log", 150, [], log=False)
    r4 = _cadence_read(d)
    say(not r4["ok"] and r4["state"] == "logmissing"
        and "an absent instrument is not compliance" in r4["summary"],
        "REJECT large diff with the log file missing", r4["summary"])

    d = _cadence_fixture(work, "r5-unparsable", 150,
                         [("yesterday afternoon", "studio-director")])
    r5 = _cadence_read(d)
    say(not r5["ok"] and r5["unparsed_dir"] == 1 and "unparsable" in r5["summary"],
        "REJECT a director row whose timestamp cannot be dated", r5["summary"])

    # THE HOLE ITSELF, as it was found: a 300-line module in a NEW UNTRACKED
    # DIRECTORY, nothing staged, no director row. Against the version shipped
    # before 24 Aug this fixture read `changed=0 state=ok exit=0` with a note
    # naming the 300 lines — verified by running it, not assumed.
    d = _cadence_fixture(work, "r6-untracked-dir-300", 0,
                         [(CADENCE_FRESH, "instrument-builder")], untracked=300)
    r6 = _cadence_read(d)
    say(not r6["ok"] and r6["state"] == "unspawned" and r6["changed"] == 300
        and r6["tracked"] == 0 and r6["untracked"] == 300,
        "REJECT a 300-line module in a NEW UNTRACKED DIRECTORY (git diff HEAD "
        "cannot see it at all)", r6["summary"])

    # AND THE SUM, not merely the substitution: neither half crosses 100 alone.
    # Without this, a version that counted untracked INSTEAD of tracked — or
    # took the max of the two — would pass r6 and still miss the real batch.
    d = _cadence_fixture(work, "r7-split-60-60", 60,
                         [(CADENCE_STALE, "studio-director")], untracked=60)
    r7 = _cadence_read(d)
    say(not r7["ok"] and r7["state"] == "unspawned" and r7["changed"] == 120
        and r7["tracked"] == 60 and r7["untracked"] == 60,
        "REJECT 60 tracked + 60 untracked = 120, where neither half crosses 100",
        r7["summary"])

    # The exit-code contract, asserted rather than documented: every accepting
    # case exits 0, and the two reds are DISTINCT from each other.
    say(all(CADENCE_EXIT[x["state"]] == 0 for x in (a1, a2, a3, a4, a5, a6, a7, a8)),
        "every accepting case exits 0")
    say(CADENCE_EXIT[r1["state"]] == 1 and CADENCE_EXIT[r4["state"]] == 2
        and len(set(CADENCE_EXIT.values())) == 3,
        "the two reds carry different exit codes (1 unspawned, 2 log missing)",
        "%s vs %s" % (r1["state"], r4["state"]))

    return passed, failed, lines


def director_cadence():
    """The director gets spawned for a substantial change, or the commit blocks.

    WHY, in the owner's words on 24 Aug: "no point in having a fable director
    if it's never called upon." The HYBRID RESIDENT section makes escalation
    mechanical rather than judged — builder-batch review before commit, queue
    reordering, a landing that changes a conclusion, anything touching the
    premise. A mandatory review with no instrument decays into an optional one,
    and this file is a list of rules that decayed exactly that way.

    So: RED when a substantial change (more than DIRECTOR_MIN_LINES = 100
    changed lines under Assets/Scripts, staged+unstaged, adds+dels summed) is
    pending and the agent log holds no `studio-director` row newer than HEAD's
    commit. A MISSING log is RED too on a substantial diff — the instrument
    being absent must not read as compliance, which is the same fault as a zero
    with no denominator.

    WHERE THE 100 CAME FROM, measured before it was written down rather than
    defended afterwards: per-commit changed lines under `ledger/Assets/Scripts`
    over the last 60 commits are 37 zeroes, then 19 21 22 23 29 35 36 38 46 48
    48 49 55 58 81, then 107 128 130 132 302 352 359 415. Nothing at all lands
    between 81 and 107, so the bound sits in a real gap in this project's own
    distribution: eight commits in sixty are "substantial", and the largest
    thing it calls small is 81 lines.

    The fixture suite runs FIRST and its accepting cases run before its
    rejecting ones, because a broken version of this check blocks every commit
    in the project rather than letting one through."""
    passed, failed, lines = _cadence_selftest()
    if failed:
        first = next((l.strip() for l in lines if l.strip().startswith("FAIL")), "?")
        return False, ("DIRECTOR CADENCE CHECK BROKEN: %d/%d fixtures failed — %s"
                       % (failed, passed + failed, first[:120]))
    r = _cadence_read(ROOT.parent)
    return r["ok"], r["summary"] + " [%d/%d selftest fixtures]" % (passed, passed + failed)


def breaks(spec):
    path = ROOT / "breaks" / (spec if spec.endswith(".json") else spec + ".json")
    if not path.exists():
        return False, "no such break spec: %s" % path.name
    code, out = run(["python3", "breakrun.py", str(path)])
    m = re.search(r"(\d+) breaks, (\d+) survived", out)
    if not m:
        return False, "break run did not report (baseline red?)"
    stale = out.count("ANCHOR MATCHES")
    label = "%s/%s breaks RED" % (int(m.group(1)) - int(m.group(2)), m.group(1))
    if stale:
        label += ", %d STALE ANCHOR(S)" % stale
    return m.group(2) == "0" and stale == 0, "%s: %s" % (path.stem, label)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--breaks", action="append", default=[],
                    help="also run this break spec (repeatable)")
    ap.add_argument("--selftest", action="store_true",
                    help="run director_cadence's fixture suite, both ways, and exit")
    ap.add_argument("--cadence", action="store_true",
                    help="print the director-cadence reading for this tree and exit")
    args = ap.parse_args()

    # THE CHEAP MODES MUST SURVIVE A PIPE. `--cadence | head -1` is the way
    # anybody will actually read this, and a correct run that ends in a
    # BrokenPipeError traceback costs twenty minutes before somebody notices it
    # worked. The full run is left alone: it is not a pipe-into-head tool.
    if args.selftest or args.cadence:
        try:
            import signal
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        except (ImportError, AttributeError, ValueError):
            pass

    if args.selftest:
        passed, failed, lines = _cadence_selftest()
        for l in lines:
            print(l)
        print("director-cadence selftest: %d passed, %d failed" % (passed, failed))
        return 0 if failed == 0 else 1

    if args.cadence:
        r = _cadence_read(ROOT.parent)
        print(r["summary"])
        return CADENCE_EXIT[r["state"]]        # 0 green / 1 unspawned / 2 no log

    parts, all_ok = [], True
    for fn in (director_cadence,
               lint, shape, shadow, tools_tracked, reach, shape_files, voice_cast, voice_gen, barks_current, voice_live, voice_assets, voices_into_build, pc_watcher, slop,
               card_writing, shipped_cards, convo_probe, queue_depth, docs_shape,
               template_sync,
               attribution, game_compiles, backend_compiles, conditional_reach, nested_types,
               static_instance, raw_avenues, filename_as_type, namespace_as_value, workflow_size,
               powershell_steps, sheet_read, prop_dimensions, prop_reach, ref_bench,
               decal_ink,
               frame_drift, verdict_keys, verdict_format, verdict_dupkeys,
               verdict_emit_dupkeys, runs_map_to_commits, gate_detail_ceiling,
               save_chaos, soak,
               adversary, stale_anchors, clip_audit, picker_selftest, core_tests):
        ok, text = fn()
        all_ok &= ok
        parts.append(text)
    for spec in args.breaks:
        ok, text = breaks(spec)
        all_ok &= ok
        parts.append(text)

    footer = ", ".join(parts) + "."
    print()
    print("--- verification footer ---")
    print(footer)
    print("---------------------------")

    # A RED RUN LEAVES NOTHING TO PASTE, which is the only version of this that
    # works. The line below has said "do not paste this into a commit message as
    # if it were" for weeks, and on 3 August I pasted one anyway — the third
    # time an unmeasured footer has reached a commit message, and the second
    # after the footer was introduced specifically to stop that.
    #
    # It fails the same way every time: the message gets written BEFORE the
    # check finishes, from a footer already sitting in the scrollback, and a
    # warning printed after the fact cannot reach a decision already made.
    #
    # So the file is the handle. Green writes it; red DELETES it. `cat` it into
    # the commit message and a red run cannot produce one, because there is
    # nothing there — the failure mode stops being a thing to remember and
    # becomes a thing that cannot happen.
    stamp = ROOT / ".verify-footer"
    if all_ok:
        stamp.write_text(footer + "\n", encoding="utf-8")
    else:
        print("NOT GREEN — do not paste this into a commit message as if it were.")
        stamp.unlink(missing_ok=True)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
