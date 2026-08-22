#!/usr/bin/env python3
"""Every measurement the verdict is supposed to carry is still in it.

    python3 tools/verdict-keys.py            # check the committed verdict
    python3 tools/verdict-keys.py --learn    # add any NEW keys to the manifest

WHY THIS EXISTS.

`game-design/sim-shots/verdict.txt` is the only channel out of CI this
environment can read, and it is assembled by a grep in the workflow over a log
the sim prints. Every link in that chain can break QUIETLY:

  - a `Debug.Log` line gets reworded and the grep stops matching it
  - a metric is dropped from the done-line during a refactor
  - a gate stops being evaluated and its clause vanishes with it
  - the grep pattern is edited and loses an alternation

In every one of those cases the verdict still arrives, still says `pass=True`,
and is simply missing the number that would have said otherwise. Nothing about
it looks wrong. That is the exact shape of the faults this project keeps
finding — a success recorded because the thing that would have failed was never
asked.

So the keys are COMMITTED and compared. A key that disappears fails the build;
a key that is added is offered to the manifest with `--learn` rather than
silently accepted, so growth is a decision and loss is an error.

THIS DOES NOT CHECK THE VALUES. `pass=True` is the sim's job and the gates'
job. This checks only that the questions are still being ASKED — which is the
half nobody was checking, and the half that cannot be noticed by reading a
verdict that looks complete.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# WHAT THE JOB WRITES WHEN A RUN MEASURED NOTHING. Quoted from
# sim-shots-commit.sh rather than paraphrased — a marker this tool matches
# loosely is a marker that stops matching the day somebody rewords the
# sentence. TWO spellings, because the committer has two branches: no
# player.log at all ("NO PLAYER LOG"), and a player.log that exists but
# holds no sim lines — the first desktop-session run on Jafar's PC booted
# the player, logged a display failure, and wrote the SECOND spelling,
# which this tool had never seen: every sim key came back GONE against a
# verdict that only ever contained the character survey.
NO_SIM = ("NO PLAYER LOG", "(no SimDirector lines matched)")

VERDICT = ROOT / "game-design" / "sim-shots" / "verdict.txt"
MANIFEST = ROOT / "game-design" / "sim-shots" / "verdict-keys.json"

# Keys whose absence is expected in some runs and is not a fault. FAILING GATES
# only appears when something failed, and the per-shot drift lines only appear
# once a previous ledger exists.
OPTIONAL = {"FAILING GATES"}


def keys_in(text):
    """Every `name=` in the verdict, plus the distinctive line prefixes.

    The `name=` form covers the done-line and the gate labels, which is where
    the measurements live. The prefixes cover the lines that carry no `=` of
    their own and would otherwise vanish without trace.
    """
    # BRACKETED RUNS ARE VALUES, NOT KEY SPACE. `homTopics=[the_hook.trouble
    # =yes,player.killed_june=true]` carries fact keys with the VICTIM'S NAME
    # in them, and this findall used to read those as verdict keys — so the
    # manifest churned every run somebody different died, and two rebaselines
    # were done believing the emitter was at fault. Innermost first,
    # repeatedly, replaced with a space — the same loop `verdict-read.py`
    # already had, and the drift between the two parsers was this bug.
    flat = text
    while True:
        stripped = re.sub(r"\[[^\[\]]*\]", " ", flat)
        if stripped == flat:
            break
        flat = stripped
    found = set(re.findall(r"([A-Za-z][A-Za-z0-9_]*)=", flat))
    for prefix in ("SimDirector: done.", "SimDirector: sky ", "SimDirector: glyphs ",
                   "SimDirector: windowGlow", "SceneAudit:", "Traffic: wheels ",
                   "CharacterAudit:", "CharacterPrefab:", "FrameDrift:",
                   "brandished a cosh"):
        if prefix in text:
            found.add(prefix)
    return found


def split_keys(text):
    """Keys that are always reported, and keys that only appear when a gate FAILS.

    A GATE LABEL IS NOT A MEASUREMENT CHANNEL, and this checker could not tell
    the difference. `FAILING GATES:` prints the label of every gate that went
    red, and those labels carry numbers — so a key inside one is reported ONLY
    on the runs where its gate failed.

    The harm gate went GREEN and `feudBlocks`, `feudLive`, `roccoUntreated` and
    `sampled` all vanished with its label. This file called that four
    measurements silently dropped and failed the build. It was four measurements
    silently PASSING.

    That is the worse kind of false alarm: a checker that goes red on good news
    gets rebaselined on reflex, and the next time it is right nobody looks. So
    the two kinds are recorded separately — a key first seen outside the gate
    line must keep appearing, and a key only ever seen inside one is allowed to
    come and go with its gate.

    ALL GATES IS NO LONGER THE SAME CLASS — PROMOTED 4 AUGUST ON EVIDENCE.

    The sim now prints every gate's label on every run, green or red, because
    35 of the 39 quantities inside those labels were unreadable on a passing
    run. That makes them always-present, so this file COULD require them — and
    requiring them would be a real ratchet: deleting `atRecruit` from a label
    would then be caught.

    It did not, at first, and the reason was rule 2: promoting ninety-odd keys
    on the strength of ZERO landed runs is setting a threshold nobody has
    measured. Two readings settled it.

    FIRST, six landed runs now carry an `ALL GATES` line and all 207 of its
    keys appear in every one. That is suggestive and not sufficient — six runs
    of a similar world can all be alike.

    SECOND, and this is the one that decided it: the SOURCE says the keys are
    structural. Twenty gate labels do contain ternaries, which is what made me
    hesitate — but every one of them is inside a VALUE (`{(traffic != null ?
    x : -1)}`), so `vehicles=` prints unconditionally and only its number
    changes. Not one label emits a whole `key=` fragment conditionally, which
    is the shape that could make a key vanish.

    So they are always present by construction rather than by luck, and
    requiring them is a real ratchet: deleting `atRecruit` from a label now
    fails the build instead of quietly removing a diagnostic.
    """
    # `FAILING GATES` ONLY. `ALL GATES` prints every run and its keys are
    # structural, so it is an always-line — and leaving it in the gate class
    # after promoting its keys made every one of them report as DEMOTED,
    # because "required always, present conditionally" is exactly what that
    # warning means. Both halves of the promotion or neither.
    gate_lines, other_lines = [], []
    for line in text.split("\n"):
        (gate_lines if "FAILING GATES" in line else other_lines).append(line)
    always = keys_in("\n".join(other_lines))
    conditional = keys_in("\n".join(gate_lines)) - always
    return always, conditional


def classify_over_history():
    """The same split, taken over EVERY committed verdict rather than the latest.

    ONE RUN CANNOT DO THIS, and trying was the first version of the fix. The
    current verdict has the harm gate green, so its four keys appear nowhere in
    it — rebaselining off that run would drop them from the manifest entirely
    and the check meant to notice them vanishing would never look for them
    again. Reclassifying every currently-absent key as conditional instead would
    be worse: a genuinely dropped metric gets quietly relabelled as an alarm
    that simply is not sounding.

    The history settles it without inference. CLAUDE.md already notes that
    `git log -- verdict.txt` is a series of measurements — that is how the AO
    ceiling was shown to sit inside its own instrument's noise across five runs.
    A key that has EVER been reported outside a gate label is a measurement and
    must keep coming; one only ever seen inside a label belongs to its gate.

    Falls back to the working tree if git is unavailable, and says so rather
    than silently classifying everything as always-required.
    """
    always, conditional = set(), set()
    try:
        shas = subprocess.run(
            ["git", "log", "--format=%H", "--", str(VERDICT)],
            cwd=str(ROOT), capture_output=True, text=True, check=True,
        ).stdout.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None
    for sha in shas:
        blob = subprocess.run(
            ["git", "show", f"{sha}:game-design/sim-shots/verdict.txt"],
            # DECODED LENIENTLY, like the main read above it. These blobs
            # were written by a Windows job and carry a section sign in the
            # places line, so a strict decode dies on one byte and takes the
            # whole history with it.
            cwd=str(ROOT), capture_output=True,
            encoding="utf-8", errors="replace",
        )
        if blob.returncode != 0:
            continue
        a, c = split_keys(blob.stdout)
        always |= a
        conditional |= c
    # A key seen outside a gate label even ONCE is a measurement. The union
    # order matters: `conditional` is only what has never appeared anywhere else.
    return always, conditional - always



def newest_run_text():
    """The verdict from the NEWEST COMMIT, which is not the latest to land.

    WHY THIS IS NOT `verdict.txt`. CLAUDE.md states the hazard in its own
    words: *"verdict.txt is the last run to LAND, which is not the newest
    commit."* Runners here vary by twenty minutes, so a build dispatched
    earlier on an older commit routinely finishes second and lays its output
    over a newer one's.

    For reading a number that is a nuisance. For `--learn` it is a RATCHET
    RUNNING BACKWARDS, and it is the same fault that was found in the CI job
    an hour ago: `--learn` takes "what is live" from this file, so learning
    off a stale verdict DELETES every key added since that commit — and a key
    deleted from the manifest is a measurement that can go missing for ever
    without anything saying so. The guard erases its own baseline, which is
    strictly worse than having no guard, because the absence now looks
    deliberate.

    `runs/<sha7>.txt` is one verdict per commit and the shas are orderable, so
    the newest one is a fact rather than a guess. Falls back to `verdict.txt`
    when there are no run files or no git — and returns which it used, because
    a tool that quietly picks a different input than the one you think it read
    is how three separate nights got diagnosed off the wrong number.
    """
    runs = ROOT / "game-design" / "sim-shots" / "runs"
    if not runs.is_dir():
        return None, "no runs directory"
    have = {p.stem: p for p in runs.glob("*.txt")}
    if not have:
        return None, "no run files"
    try:
        log = subprocess.run(
            ["git", "log", "--format=%h", "-400"],
            cwd=str(ROOT), capture_output=True, text=True, check=True,
        ).stdout.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, "no git"
    # A RUN THAT NEVER RAN IS NOT A RUN WITH NOTHING IN IT.
    #
    # On 4 August a build died on "Activate Unity license" — four dispatched at
    # once, and the licence server refused the fourth. The job still committed a
    # verdict, eleven lines long, saying in as many words: "NO PLAYER LOG — the
    # sim did not run on this commit." That file was the newest commit's, so
    # this returned it, and every one of 466 keys came back GONE.
    #
    # The alarm was total, instant, and about nothing. Worse, it is the exact
    # ratchet rule 5 warns about pointed at a manifest: `--learn` against that
    # file would have erased the entire baseline, and a key deleted from the
    # manifest is a measurement that can vanish for ever with nothing to say so.
    #
    # I spent several minutes reading my own C# for a compile error that was
    # never there, which is what an instrument that cannot tell "not measured"
    # from "measured zero" costs every time. Skip and keep walking back.
    skipped = []
    for sha in log:                      # newest first
        if sha not in have:
            continue
        text = have[sha].read_text(encoding="utf-8", errors="replace")
        if any(m in text for m in NO_SIM):
            skipped.append(sha)
            continue
        note = sha if not skipped else f"{sha} (skipped {len(skipped)} no-sim: {', '.join(skipped)})"
        return text, note
    if skipped:
        return None, f"no commit has a verdict with a sim in it — {len(skipped)} ran no sim"
    return None, "no run file matches any recent commit"

def main():
    learn = "--learn" in sys.argv
    if not VERDICT.exists():
        print("verdict-keys: no verdict.txt yet — nothing to check")
        return 0

    text = VERDICT.read_text(encoding="utf-8", errors="replace")

    # AND IF THAT BUILD NEVER RAN A SIM, THERE IS NOTHING TO CHECK.
    #
    # A build that dies on "Activate Unity license" still commits a verdict —
    # eleven lines, saying so in words. Checking a manifest of 466 measurements
    # against it reports 465 of them GONE, which is a total alarm about nothing
    # and cost me several minutes reading my own C# for a compile error that was
    # never there. A guard that cannot tell "not measured" from "measured zero"
    # is the ratchet rule 5 warns about, and this is the third instrument tonight
    # with that shape.
    #
    # Not silent: it says which commit produced nothing, because a build that
    # fails to build is worth knowing about even though it is not this tool's
    # business to fail on.
    if any(m in text for m in NO_SIM):
        print(f"verdict-keys: the landed verdict ran no sim "
              f"({VERDICT.name} line 1: {text.splitlines()[0].strip()}) — nothing to check")
        newer, why = newest_run_text()
        if newer is None:
            return 0
        print(f"verdict-keys: checking the newest commit that DID run one instead — {why}")
        text = newer

    # LEARNING USES THE NEWEST COMMIT'S RUN; CHECKING USES WHAT LANDED.
    #
    # They want different things. A check should ask "is the thing that just
    # landed complete", and the answer is about that run. `--learn` rewrites
    # the baseline, and rewriting it from a stale run deletes keys — see
    # `newest_run_text`.
    source = "verdict.txt"
    if "--learn" in sys.argv:
        newer, why = newest_run_text()
        if newer is not None:
            text, source = newer, f"runs/{why}.txt"
        else:
            print(f"verdict-keys: learning from verdict.txt ({why})")
    always, conditional = split_keys(text)
    present = always | conditional

    def write(manifest_always, manifest_conditional):
        MANIFEST.write_text(json.dumps({
            "always": sorted(manifest_always),
            "conditional": sorted(manifest_conditional),
        }, indent=1) + "\n", encoding="utf-8")

    if not MANIFEST.exists():
        write(always, conditional)
        print(f"verdict-keys: manifest seeded with {len(present)} key(s)")
        return 0

    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # THE OLD FLAT LIST STILL READS. A format change that made every existing
    # manifest unreadable would force a rebaseline, and a rebaseline is exactly
    # the moment a genuine loss slips through unnoticed. A flat list is treated
    # as "all always-required", which is what it meant, and the first `--learn`
    # sorts it into the two kinds.
    if isinstance(raw, list):
        req_always, req_conditional = set(raw), set()
    else:
        req_always = set(raw.get("always", []))
        req_conditional = set(raw.get("conditional", []))

    # A conditional key going missing is its gate passing, which is the good
    # outcome and not a finding.
    missing = sorted(k for k in req_always - present if k not in OPTIONAL)
    # AND A KEY THAT MOVED THE OTHER WAY IS A REAL LOSS. Something that used to
    # be reported every run and now only shows up when its gate fails has
    # stopped being a measurement and become an alarm — quieter, and quietly
    # worse. Caught by comparing against `always`, not against `present`.
    demoted = sorted(k for k in req_always & conditional if k not in OPTIONAL)
    added = sorted(present - req_always - req_conditional)

    if learn:
        # RECONCILE, DO NOT ONLY ADD. The first version unioned the manifest
        # with what it saw, so a key that was RENAMED stayed required for ever
        # and the check went permanently red for a rename it could never
        # forgive. Caught on its first real encounter: the window probe's `rgb=`
        # became `all=`/`face=`, which is exactly a rename.
        #
        # `--learn` means "this verdict is the new baseline", so the manifest
        # becomes what is actually present. The protection is that it is
        # explicit and manual — nothing learns on its own, and an accidental
        # loss still fails until somebody decides otherwise.
        # A CONDITIONAL KEY IS NOT FORGOTTEN JUST BECAUSE ITS GATE IS GREEN
        # TODAY. Rebaselining off a run where the harm gate passed would drop
        # its four keys from the manifest entirely, and the check that is meant
        # to notice them disappearing would never look for them again.
        # OVER THE HISTORY WHEN GIT CAN SUPPLY IT, because a single run cannot
        # tell a gate-only key from a dropped one — see `classify_over_history`.
        hist_always, hist_conditional = classify_over_history()
        if hist_always is None:
            print("verdict-keys: no git history available — classifying from this run only")
            write(always, conditional | (req_conditional - always))
        else:
            # THE CURRENT RUN DEFINES WHAT IS LIVE; HISTORY ONLY SAYS WHICH KEYS
            # ARE GATE-ONLY. Taking `always` from history too resurrects the
            # dead: `rgb` was renamed to `all`/`face` builds ago and came
            # straight back as a required key that can never be satisfied — the
            # permanently-red rename this file already learned once and wrote a
            # comment about. History is the right source for the ONE question a
            # single run cannot answer, and the wrong source for everything else.
            write(always, (hist_conditional | req_conditional) - always)
        note = []
        if added:
            note.append(f"+{len(added)} new ({', '.join(added[:5])})")
        if missing:
            note.append(f"-{len(missing)} dropped ({', '.join(missing[:5])})")
        if demoted:
            note.append(f"{len(demoted)} now gate-only ({', '.join(demoted[:5])})")
        print(f"verdict-keys: rebaselined from {source} — " + ("; ".join(note) if note else "no change"))
        return 0

    for k in demoted:
        print(f"  DEMOTED {k}  (was reported every run, now only when its gate fails)")
    print(f"verdict-keys: {len(always)} always + {len(conditional)} gate-only present, "
          f"{len(req_always)} required, {len(missing)} missing, {len(added)} new")
    for k in added:
        # NEW IS NOT AN ERROR, it is an unrecorded decision. Printed so somebody
        # runs --learn on purpose rather than the manifest drifting behind.
        print(f"  new  {k}  (run --learn to record it)")
    for k in missing:
        print(f"  GONE {k}")
    if missing:
        print(f"{len(missing)} measurement(s) STOPPED BEING REPORTED — a verdict "
              "missing a number reads exactly like one where the number was fine.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
