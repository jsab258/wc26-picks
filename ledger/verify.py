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
    m = re.search(r"checked (\d+) files, (\d+) shape error", out)
    if not m:
        return False, "ShapeCheck did not report (build failure?)"
    return m.group(2) == "0", "%s shape errors (%s files)" % (m.group(2), m.group(1))


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
    only counts down: wiring an API without deleting its entry fails too."""
    code, out = run(["dotnet", "run", "-c", "Release", "--project", str(ROOT / "ReachCheck"),
                     "--", str(ROOT / "Assets" / "Scripts" / "Core"),
                     str(ROOT / "Assets" / "Scripts" / "Game"),
                     "--tests", str(ROOT / "CoreTests"),
                     "--tests", str(ROOT / "SimHarness"),
                     "--tests", str(ROOT / "BalanceLab"),
                     "--tests", str(ROOT / "BarkGen"),
                     "--tests", str(ROOT / "Tier2Gen"),
                     "--allow", str(ROOT / "ReachCheck" / "allow.json")])
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
    rule is verifying my own comment."""
    missing = []
    for proj in sorted(ROOT.glob("*/*.csproj")):
        code, out = run(["git", "ls-files", "--error-unmatch", str(proj)], cwd=str(ROOT))
        if code != 0:
            missing.append(proj.parent.name)
    if missing:
        return False, "UNTRACKED TOOL PROJECT(S): " + ", ".join(missing)
    n = len(list(ROOT.glob("*/*.csproj")))
    return True, "%d tool project(s) tracked" % n


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
SLOP_CEILING = 91


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
    for script in ("probe.py", "export_probe.py"):
        code, out = run(["python3", str(tools / script), "--selftest"])
        m = re.search(r"(\d+) checks", out)
        if code != 0:
            bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
            return False, "VOICE LIVE (%s): %s" % (script, bad[0][:70] if bad else "no report")
        total += int(m.group(1)) if m else 0
    n = total
    if True:
        return True, "voice-live ok (%s checks)" % n
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
    args = ap.parse_args()

    parts, all_ok = [], True
    for fn in (lint, shape, shadow, tools_tracked, reach, shape_files, voice_cast, voice_gen, voice_live, slop,
               card_writing, shipped_cards, convo_probe, queue_depth, docs_shape,
               attribution, game_compiles, nested_types,
               static_instance, filename_as_type, namespace_as_value, workflow_size,
               frame_drift, verdict_keys, verdict_format, save_chaos, soak,
               adversary, stale_anchors, core_tests):
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
