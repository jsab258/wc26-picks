#!/usr/bin/env python3
"""THE MAP: a picture of the game, not a report about the repository.

    python3 tools/map.py                      # write map.html at the root
    python3 tools/map.py --selftest           # accepting case FIRST
    python3 tools/map.py --root <dir> --out <f> --now <iso>

WHY THIS PAGE WAS REBUILT, 2026-09-07. Jafar, verbatim, rejecting the previous
version: "It fails my request. It is a dense diagnostic report with tiny text,
clipped lines, raw paths and gate counts." He was right, and the fault was not
the derivations underneath. It was that every derivation was PRINTED IN FULL
ON THE SURFACE. A page whose first screen is a wall of verdict keys answers
the question "what did the instrument read" for a reader who asked "what is
this game, and what can I do with it".

So the surface and the evidence swapped places. The evidence did not go away:
every sha, every verdict key, every file count and every caveat is one tap
down, in a sheet, where the same derivation prints in full. Nothing on the
first screen is a key.

RULING 3, Jafar, 2026-09-07, VERBATIM, AND IT SITS ABOVE EVEN THE FIRST
SCREEN BELOW: "The map needs a ladder at the very top: the steps to a
playable loop, in order, with the current one highlighted, so I can read
'step 2 of 10' in one glance from my phone." So the ladder is now the first
thing on the page, above the three answers this section still describes for
everything beneath it. IT IS PLAIN HTML, NOT SVG: SVG clips a line silently,
which is one of the four faults this page was already rebuilt to fix, and
normal text wraps on its own. WHERE THE STEPS COME FROM, so nobody reaches
for a heading parser a second time: production/next-three.json's own `done`
and `next` arrays are already ordered (Jafar's priority order, confirmed
lower in this file by the selftest's own check that the steps read "control",
then "crime", then "gossip" across the two), and its
`milestone`/`milestoneFrom` fields already name the rung at the top.
Inventing a second, parallel list would only give the two a chance to drift.

WHAT "DONE" MEANS, CORRECTED BY THE RULING OF 2026-09-08 (game-design/
decision-2026-09-08-the-crime-the-witness-and-the-overheard-consequence.md,
section 7). It used to mean nothing here: next-three.json deleted a finished
step instead of marking it, so the current rung was always rung one and the
page could never print the "step 2 of 10" RULING 3 asked for. That file now
carries a `done` array, a finished step MOVES into it, and each done entry is
a CLAIM plus the instrument that proves it: {file, key} pairs whose exact
key=value token this run looks for on a line of that committed file. This
page checks the INSTRUMENT, never the claim. A done entry whose evidence file
is missing or whose key is absent, or a title in both arrays, refuses the
WHOLE ladder with the stale banner and the reason, because a step count on
his phone rests on every done rung being real. With no `done` array at all
the ladder still says so in words instead of a tick nobody measured. See
ladder_rungs() and ladder_html() below.

THE FIRST PHONE SCREEN BELOW THE LADDER ANSWERS EXACTLY THREE THINGS, and
nothing else may compete for it:

    1  WHAT EXISTS NOW. One sentence, and THE STREET FRAME ITSELF, shown
       inline rather than linked. The picture is the answer; the sentence is
       the caption.
    2  WHAT CAN I RUN, AND WHAT DO I PRESS. Only actions with evidence behind
       them, and the probe is separated from a game IN WORDS, because it is
       the confusion this page exists to prevent.
    3  WHAT IS THE NEXT MEANINGFUL GAME MILESTONE. One line.

THE FOUR STATES THIS PAGE KEEPS APART, and it will not merge them for a
tidier layout: code that exists, a harness that passes, a probe that renders,
and a build a person can control. Every one of the six areas below says which
of the four it is in, in words, beside a colour that is never the only signal.

THE STREET IS THE CASE THE OLD PAGE GOT WRONG, and it is the reason for the
one rule here that looks like a loosening. Run 25 put Meridian's own textures
on the street: brick, cobbles, wood and glass are visible in
production/d1-probe/ue-vign_camA_day.png, written on Jafar's PC on commit
288ff51. No committed key measures that yet (quadChroma and shotChromaExQuads
are the two that would, and no run emits either). The old page therefore
printed "nothing measured" over a textured street, which is a false reading of
a true schema. Jafar: "Visible textures in a committed frame ARE EVIDENCE even
though the automated summary key is missing." So the state word for an area is
SEEN, NOT MEASURED when three things hold together, all checked at generation
time: the required keys are absent, a committed artifact from a named run
exists, AND THIS PAGE IS SHOWING IT. An observation whose evidence the reader
cannot see is not offered. The unverified half is printed beside it in the
same breath, never in a different section.

WHERE THE NEXT THREE COME FROM, and what was deleted to make that true. They
are read from production/next-three.json AND FROM NOTHING ELSE. The previous
version parsed headings out of production/NOW.md, which is a long log, and on
the day it was rejected it was offering him a task run 25 had COMPLETED and a
task he had SUPERSEDED that same morning, because a log cannot tell a reader
which paragraph is an instruction. The heading parser is deleted. Jafar: "Use
one small source of current priorities instead of copying the plan into
several documents." Two guards sit under the file: an item whose queue file has
moved to production/queue/done/ or whose status line says DONE or SUPERSEDED is
REFUSED and rendered as a loud stale entry rather than as a task, and an item
that is not named in the file cannot appear at all, which is the half that
catches a supersession leaving the queue file READY (queue 119 is that case
today).

WHAT A CHECKOUT CANNOT ESTABLISH, kept from the previous version because it
was right. Jafar, 2026-09-06: "Scanning the repository cannot establish what
exists on my PC." Availability is a separate axis from category, there is no
"yes" on it, and the only word that can mean his machine is earned by an
artifact HIS MACHINE WROTE. check_no_absence_claim reads the rendered bytes
for a claim wider than this checkout.

SELF-CONTAINED. One file, no server, no build step, no remote script,
stylesheet, font or image. The street frame is embedded as a data URI through
tools/glance.py's encoder, which is the one implementation of "shrink a frame
to fit a byte budget" in this repository, so the publisher carries the picture
without a second file to copy or a second path to break. The disclosure is CSS
:target, so a tap makes no request and needs no JavaScript.

EXIT CODES, distinct per outcome. 0 the page is good. 1 a check bit, and the
page was still written because a stale map is worse than one that says what it
could not derive. 2 nothing measured: no runnable entry point was found at
all, which means the walk is broken rather than that the project has none.
3 the selftest failed. 4 tools/glance.py could not be imported.
"""
import argparse
import datetime
import hashlib
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

TOOL = "tools/map.py"
ROOT = Path(__file__).resolve().parent.parent
OUT_NAME = "map.html"
NOTHING = "nothing measured"

# THE SOURCES, NAMED ONCE, so the page quotes these strings rather than
# carrying a second copy of the paths in prose.
SIM_VERDICT = "game-design/sim-shots/verdict.txt"
UE_VERDICT = "production/d1-probe/ue-vignette-verdict.txt"
UE_BUILD = "production/d1-probe/ue-build.txt"
STUDY = "production/stranger-test/study.txt"
PRIORITIES = "production/next-three.json"
QUEUE_DIR = "production/queue"
QUEUE_DONE_DIR = "production/queue/done"
INVENTORY = "production/systems-inventory.json"
PROBE_WORKFLOW = ".github/workflows/ledger-probe-unreal.yml"
PROBE_SENTINEL = "production/d1-probe/DISPATCH"
PROBE_SOURCE_DIRS = ("ue-probe/Source", "ue-probe/tests", "ue-probe/Config")

# THE FIVE THINGS THIS PAGE DISTINGUISHES, in Jafar's words, 2026-09-06. They
# no longer structure the surface (five headings of prose is what he rejected),
# and they still structure the MATERIAL STATE below, because "a playable build
# appeared" and "a text tool appeared" are different messages to wake a phone
# for. The page says the distinction that matters to a reader in words instead:
# a probe renders and exits, a game is played.
CAT_PROBE = "runnable visual probe"
CAT_PLAYABLE = "playable game build"
CAT_TEXT = "runnable text tool"
CAT_CODE = "implemented code, no usable build"
CAT_UNVERIFIED = "availability not verified"
CATEGORIES = (CAT_PROBE, CAT_PLAYABLE, CAT_TEXT, CAT_CODE, CAT_UNVERIFIED)

# AVAILABILITY, WHICH IS A DIFFERENT AXIS FROM CATEGORY and may never be
# collapsed into it. Only one of these is a statement about his machine, and
# it is the one an artifact written BY his machine earns.
AVAIL_RAN = "ran-on-your-pc"          # an artifact here was written by a run there
AVAIL_UNVERIFIED = "unverified"       # committed here; his copy not visible from here
AVAIL_UNCOMMITTED = "not-committed"   # in this working tree only, so no pull can bring it
# and NOTHING when git could not be asked at all.

# THE WORDS THAT MAY NOT APPEAR, checked on the rendered bytes by
# check_no_absence_claim. Each is a claim about the world made from a scan of
# one checkout. The qualified forms ("not in this checkout") are what this
# page may say, and the check requires the qualifier within the same sentence.
ABSENCE_CLAIMS = (
    "does not exist", "no packaged build exists", "no packaged game build exists",
    "nothing is playable", "does not have", "is not on your pc",
)
CHECKOUT_QUALIFIERS = ("in this checkout", "in this clone", "in this container",
                       "committed here", "from here", "walked here")

# THE ONLY LINKS. The Producer's register allows three destinations and this
# page is one of them, so it may point at the other two and at nothing else. A
# repository markdown link is what Jafar ruled out; check_links counts them.
SIBLINGS = (("index.html", "the glance"), ("gallery.html", "the pictures"))


def load_glance():
    """The phone bar, the git helper and THE IMAGE ENCODER are tools/glance.py's,
    imported rather than copied. Two implementations of "shrink a frame into a
    byte budget" drift, and the copy nobody looks at is the one still emitting
    a 1.8 MB page when the other was fixed."""
    p = ROOT / "tools" / "glance.py"
    spec = importlib.util.spec_from_file_location("glance", p)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    GLANCE = load_glance()
except Exception as exc:                                         # noqa: BLE001
    if __name__ == "__main__":
        sys.stderr.write("map: tools/glance.py could not be imported (%s); "
                         "refusing to reimplement the phone bar\n" % exc)
        sys.exit(4)
    raise ImportError("tools/glance.py could not be imported: %s" % exc)

PAGE_BYTE_CAP = GLANCE.PAGE_BYTE_CAP
MAX_DECLARED_WIDTH_PX = GLANCE.MAX_DECLARED_WIDTH_PX


def load_queue_check():
    """The queue is counted by tools/queue-check.py's count_queue() and not by
    a second walker here. Its own docstring calls itself the ONE queue counter
    in this repository, and ledger/verify.py and tools/morning-brief.py both
    read it, so a third count would be a third answer."""
    p = ROOT / "tools" / "queue-check.py"
    spec = importlib.util.spec_from_file_location("queue_check", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# GEOMETRY. The flow below is SVG, and SVG text does not wrap: a line that
# overruns its box is CLIPPED SILENTLY, which is the exact failure Jafar named
# ("clipped lines"). So every string drawn into the diagram is wrapped HERE,
# in Python, at the same width the box is drawn at, and the box's height is
# then computed from the number of lines that came back. The page cannot draw
# a box smaller than its own text.
#
# The diagram's viewBox is the phone's content width, and its CSS max-width is
# the same number, so it renders 1:1 on a 390 px phone and is never scaled up
# on a desktop. A scaled diagram is one whose font size nobody chose.
# ---------------------------------------------------------------------------
PHONE_WIDTH_PX = 390
BODY_PAD_PX = 14
FLOW_W = PHONE_WIDTH_PX - 2 * BODY_PAD_PX      # 362, the diagram's viewBox
GUTTER_X = 12                                   # where the return arrow runs
NODE_X = 26
NODE_W = FLOW_W - NODE_X - 4
NODE_PAD = 12
NODE_TEXT_W = NODE_W - 2 * NODE_PAD
TITLE_PX = 15
TITLE_LEAD = 19
STATUS_PX = 12
PILL_H = 21
BLOCKER_PX = 12
BLOCKER_LEAD = 15
ARROW_GAP = 30
# THE PILL'S TEXT IS UPPERCASE AND BOLD, which is a WIDER advance than the
# body model above, and getting that wrong is not a rounding: at 0.62em the
# pill drawn for "SEEN, NOT MEASURED" was 150 px for text that needed 167, and
# the last letters sat outside the rounded rectangle on the rendered page.
# Found by looking at a screenshot, not by a check, so the check below now
# carries the pill too and prints the widest one against the box it was drawn
# in. 0.72 is the advance that fits every word in the closed vocabulary at
# 12 px, measured by rendering them.
UPPER_ADVANCE_EM = 0.72
PILL_PAD_PX = 9
# The wrap is modelled, not measured: an average lowercase advance of half the
# font size is the usual approximation for these sans faces. IT SHIPS ITS
# INSTRUMENT: every run prints the widest string it drew, the lines it
# predicted and the box it drew them in, so one look at the rendered page
# corrects this number rather than a guess about it.
AVG_ADVANCE_EM = 0.5

# HOW MANY OF A LIST ARE SHOWN BEFORE THE CAP MUST ANNOUNCE ITSELF.
TOOLS_SHOWN = 8
UNMAPPED_SHOWN = 6
READINGS_SHOWN = 6
NEXT_ASKED = 3


def wrap_text(text, font_px, width_px):
    """The lines this text takes at this font on this width, by greedy word
    wrapping the way a browser does it. An ESTIMATE, named as one everywhere
    it is used, and the ONE implementation: wrap_lines() below counts what
    this returns rather than repeating the arithmetic."""
    cpl = max(1, int(width_px / (font_px * AVG_ADVANCE_EM)))
    lines, cur = [], ""
    for word in str(text).split():
        joined = (cur + " " + word).strip()
        if len(joined) <= cpl or not cur:
            cur = joined
        else:
            lines.append(cur)
            cur = word
    if cur or not lines:
        lines.append(cur)
    return lines


def wrap_lines(text, font_px, width_px):
    return len(wrap_text(text, font_px, width_px))


def cap_text(text, cap):
    """(text, bit, originalLen). A truncation that does not say it bit reads as
    the whole sentence, so the ellipsis ships with it and the caller prints the
    length it cut from."""
    s = " ".join(str(text).split())
    if len(s) <= cap:
        return s, False, len(s)
    return s[:cap].rstrip() + "...", True, len(s)


# HOW LONG A QUOTED LAUNCHER DESCRIPTION MAY BE, SET FROM THE PRINTED SERIES
# AND NOT BEFORE IT. The opening of every .bat banner at the root was measured
# on 2026-09-07 and the lengths are 30, 41, 42, 77, 115, 188 characters (a
# median of about 60 and a peak of 188 on open-dashboard.bat). 120 holds five
# of the six WHOLE, which matters because a sentence cut mid-clause on the
# surface is one of the four faults this page was rejected for, and it clips
# only the sixth, which lives behind a tap where the cap announces itself.
# The run prints every length, so the next reader moves this from evidence.
SENTENCE_CAP = 120

# ---------------------------------------------------------------------------
# THE RUNNABLE WALK. Entry points are the .bat files in the repository ROOT,
# which is the double-click convention here. WALKED, NOT LISTED: a new one
# appears on this page the run after it lands without anybody remembering.
#
# WHAT CHANGED ON THE SURFACE, 2026-09-07. All of them used to be printed on
# the first screen. Jafar's instruction: "The supervisor is an operational tool
# and not a game milestone; individual daemon launchers and the superseded
# human test must not occupy the main game view." So the walk is unchanged and
# the SURFACE is a two-name shortlist, with the rest one tap down and the cap
# announcing itself. The material state still tracks every row, because a new
# launcher landing is still worth a message.
# ---------------------------------------------------------------------------

REM_RX = re.compile(r"^\s*(?:REM|::)\b", re.I)
BANNER_RX = re.compile(r"^\s*REM\s*=====", re.I)
DOTNET_RX = re.compile(r"dotnet\s+run\b[^\n]*?--project\s+\"?[^\"\n]*?[\\/]"
                       r"([A-Za-z0-9_.-]+)", re.I)
PY_RX = re.compile(r"[\"']?%PY%[\"']?\s+\"?[^\"\n]*?[\\/](tools[\\/][^\"\n]+?\.py)", re.I)
HTML_RX = re.compile(r"start\s+\"\"\s+\"[^\"\n]*?[\\/]([A-Za-z0-9_.-]+\.html)\"", re.I)
GIT_RX = re.compile(r"^\s*git\s+(pull|fetch|clone|checkout)\b", re.I | re.M)
EXE_RX = re.compile(r"[\\/]?([A-Za-z0-9_.-]+\.exe)\b", re.I)
NOT_THE_GAME_EXE = ("python.exe", "git.exe", "dotnet.exe", "cmd.exe",
                    "powershell.exe", "pythonw.exe", "explorer.exe")

# THE TWO THE FIRST SCREEN OFFERS, and this is an editorial choice made once,
# here, rather than a scan pretending to have made it. Of the .bat files at the
# root, these are the two that are neither a daemon launcher nor the human test
# Jafar superseded on 2026-09-06. The others are not hidden: the count says how
# many there are and the tap shows them all.
FIRST_SCREEN_TOOLS = ("UPDATE FROM CLAUDE.bat", "START EVERYTHING.bat")


def code_lines(text):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s or REM_RX.match(s) or s.lower().startswith("@echo"):
            continue
        out.append(s)
    return out


# HOW MUCH OF A BANNER IS A DESCRIPTION. The first sentence alone is not
# always one: START EVERYTHING.bat opens "ONE WINDOW.", which is a headline,
# and a card showing it says nothing. So sentences are taken until there are
# 40 characters of them or two have been taken, whichever comes first. The
# number is a measurement of the two banners on the first screen today ("ONE
# WINDOW." is 11 characters and "ONE CLICK: pulls everything Claude has pushed
# since you last looked - tools, scripts, docs - and says what arrived." is
# 114), and the run prints the length it took from every file so the bound can
# be moved from evidence rather than from taste.
ABOUT_MIN_CHARS = 40
ABOUT_MAX_SENTENCES = 2


def one_line_about(text):
    """The opening of a .bat file's own banner, or None. Quoted from the file
    so a description cannot drift from what the file does."""
    lines = text.splitlines()
    said = []
    for i, line in enumerate(lines):
        if not BANNER_RX.match(line):
            continue
        for nxt in lines[i + 1:]:
            s = re.sub(r"^\s*REM\s?", "", nxt).strip()
            if BANNER_RX.match(nxt):
                break
            if s:
                said.append(s)
            elif said:
                break
        break
    if not said:
        for line in lines:
            s = line.strip()
            if s.lower().startswith("title "):
                said = [s[6:].strip()]
                break
    whole = " ".join(said).strip()
    if not whole:
        return None, whole
    parts = [s for s in re.split(r"(?<=[.!?])\s+", whole) if s.strip()]
    taken = []
    for s in parts[:ABOUT_MAX_SENTENCES]:
        taken.append(s.strip())
        if len(" ".join(taken)) >= ABOUT_MIN_CHARS:
            break
    return " ".join(taken).strip(), whole


def csproj_kind(root, rel):
    p = Path(root) / rel
    if not p.is_file():
        hits = sorted(Path(root).rglob(Path(rel).name))
        if not hits:
            return None
        p = hits[0]
    body = p.read_text(encoding="utf-8", errors="replace")
    if "<OutputType>Exe</OutputType>" in body:
        return "console"
    return "library"


def classify(root, text):
    """(label, why, hint). VISUAL only when a player executable EXISTS in this
    tree, so a name in a comment cannot earn the label."""
    lines = code_lines(text)
    body = "\n".join(lines)
    for m in EXE_RX.finditer(body):
        name = m.group(1)
        if name.lower() in NOT_THE_GAME_EXE:
            continue
        if list(Path(root).rglob(name)):
            return "VISUAL", "starts/%s/which-exists-in-this-checkout" % name, None
        return "TEXT", "names/%s/which-is-not-in-this-checkout" % name, None
    m = DOTNET_RX.search(body)
    if m:
        proj = m.group(1)
        kind = csproj_kind(root, "ledger/%s/%s.csproj" % (proj, proj))
        return ("TEXT", "console-project/ledger/%s/%s.csproj/OutputType.Exe/"
                        "no-renderer" % (proj, proj) if kind == "console"
                else "dotnet-project/%s" % proj,
                "dotnet run --project ledger/%s" % proj)
    m = PY_RX.search(body)
    if m:
        return "TEXT", "runs/%s/in-a-console-window" % m.group(1).replace("\\", "/"), None
    m = HTML_RX.search(body)
    if m:
        return "TEXT", "opens/%s/a-page-of-words" % m.group(1), None
    if GIT_RX.search(body):
        return "TEXT", "runs-git/in-a-console-window", None
    return "unknown", "nothing-in-the-file-matched-a-known-launcher", None


def packaged_builds(root):
    """(playerExes, filesWalked). THE DENOMINATOR IS THE POINT: a zero here
    means this checkout holds no player executable, and it can mean nothing
    about a disk this process cannot see."""
    root = Path(root)
    exes, walked = [], 0
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        walked += 1
        if p.suffix.lower() == ".exe" and p.name.lower() not in NOT_THE_GAME_EXE:
            exes.append(p.relative_to(root).as_posix())
    return exes, walked


def tracked_root_bats(root):
    """(names git knows about at the root, whether git could answer at all).

    A .bat sitting in this container that has not been committed is NOT on
    Jafar's PC and he cannot double-click it, so the page may not offer it as
    if he could. WHEN GIT CANNOT ANSWER the second element is False and the
    page prints the words nothing measured for the column rather than calling
    everything untracked, which is what a planted fixture tree would read as.
    """
    out = GLANCE.git(root, "ls-files", "--", "*.bat")
    if not out:
        inside = GLANCE.git(root, "rev-parse", "--is-inside-work-tree")
        return set(), inside == "true"
    return {n for n in out.splitlines() if "/" not in n}, True


def find_runnables(root):
    """(rows, reading). AVAILABILITY IS NOT DERIVED FROM THE CATEGORY and is
    never "yes": git ls-files proves a file is committed in THIS clone."""
    root = Path(root)
    tracked, git_answered = tracked_root_bats(root)
    bats = sorted(p for p in root.glob("*.bat") if p.is_file())
    all_bats = sorted(p for p in root.rglob("*.bat")
                      if p.is_file() and ".git/" not in p.as_posix())
    rows, capped = [], 0
    for p in bats:
        text = p.read_text(encoding="utf-8", errors="replace")
        about, _full = one_line_about(text)
        said, bit, orig = cap_text(about or NOTHING, SENTENCE_CAP)
        capped += 1 if bit else 0
        label, why, hint = classify(root, text)
        if not git_answered:
            avail, availWhy = NOTHING, "git-could-not-be-asked-in-this-tree"
        elif p.name in tracked:
            avail, availWhy = AVAIL_UNVERIFIED, ("committed-in-this-checkout/"
                                                 "a-pull-brings-it/whether-"
                                                 "yours-has-pulled-is-not-"
                                                 "visible-from-here")
        else:
            avail, availWhy = AVAIL_UNCOMMITTED, ("in-the-studio-working-tree-"
                                                  "only/not-committed/so-no-"
                                                  "pull-can-bring-it-yet")
        rows.append({
            "name": p.name, "about": said, "aboutBit": bit,
            "aboutChars": orig, "label": label, "why": why,
            "category": CAT_TEXT if label == "TEXT" else (
                CAT_PROBE if label == "VISUAL" else CAT_UNVERIFIED),
            "hint": hint, "file": p.relative_to(root).as_posix(),
            "avail": avail, "availWhy": availWhy,
            "onFirstScreen": p.name in FIRST_SCREEN_TOOLS,
        })
    exes, walked = packaged_builds(root)
    tally = {}
    for r in rows:
        tally[r["label"]] = tally.get(r["label"], 0) + 1
    return rows, {
        "found": len(rows), "walked": len(bats),
        "batsAnywhere": len(all_bats),
        "batsNotAtRoot": len(all_bats) - len(bats),
        "visual": tally.get("VISUAL", 0), "text": tally.get("TEXT", 0),
        "unknown": tally.get("unknown", 0),
        "onFirstScreen": sum(1 for r in rows if r["onFirstScreen"]),
        "packagedBuildsInCheckout": len(exes), "filesWalkedInCheckout": walked,
        "sentencesCapped": capped,
        "unverifiedAvail": sum(1 for r in rows
                               if r["avail"] == AVAIL_UNVERIFIED),
        "gitAnswered": git_answered,
    }


# ---------------------------------------------------------------------------
# THE PROBE, AND THE THING IT IS NOT.
# ---------------------------------------------------------------------------

WF_NAME_RX = re.compile(r"^name:\s*(.+?)\s*$", re.M)
WF_RUNSON_RX = re.compile(r"^\s*runs-on:\s*\[([^\]]+)\]", re.M)
WF_PATHS_RX = re.compile(r"^\s*paths:\s*\n((?:\s*-\s*'[^']+'\s*\n)+)", re.M)
SHOT_FILE_RX = re.compile(r"\bfile=(\S+\.png)\b")
WIN_RUNNER_RX = re.compile(r"\b([A-Za-z]:/[^\s]*?/_work/[^\s]*)")


def workflow_launch(root, rel=PROBE_WORKFLOW):
    """How the probe is started, read out of the workflow file itself, so a
    workflow that changes its trigger changes this sentence next run."""
    p = Path(root) / rel
    if not p.is_file():
        return {"present": False, "name": None, "runsOn": [], "paths": []}
    text = p.read_text(encoding="utf-8", errors="replace")
    m = WF_NAME_RX.search(text)
    labels = WF_RUNSON_RX.search(text)
    paths = WF_PATHS_RX.search(text)
    return {
        "present": True,
        "name": m.group(1) if m else None,
        "runsOn": [s.strip() for s in labels.group(1).split(",")] if labels else [],
        "paths": re.findall(r"'([^']+)'", paths.group(1)) if paths else [],
        "file": rel,
    }


def visual_probe(root):
    """(row or None, reading) for the runnable visual probe.

    THE EVIDENCE IS AN ARTIFACT WRITTEN BY HIS MACHINE, which is the only kind
    of evidence here that can say anything about his machine: the verdict is
    written by a packaged, cooked Unreal build on the self-hosted runner, line
    1 stamps the commit and the epoch, the capture line counts the frames, and
    the texture root it printed is a Windows actions-runner working directory.
    WHAT IT CANNOT ESTABLISH, and the sheet says so: that the packaged folder
    is still on that disk NOW.
    """
    root = Path(root)
    sha, when = read_stamp(root, UE_VERDICT)
    wrote = read_key(root, UE_VERDICT, "shotsWrote")
    texroot = read_key(root, UE_VERDICT, "texRoot")
    wf = workflow_launch(root)
    vp = Path(root) / UE_VERDICT
    frames = []
    if vp.is_file():
        for line in vp.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("shot ") and "status=WROTE" in line:
                frames += SHOT_FILE_RX.findall(line)
    runner = WIN_RUNNER_RX.search(texroot or "")
    packaged = texroot.rsplit("/", 1)[0] if texroot and "/" in texroot else None
    reading = {
        "verdictPresent": vp.is_file(), "sha": sha, "when": when,
        "framesWrote": wrote, "frameFiles": frames,
        "texRoot": texroot, "runnerPath": runner.group(1) if runner else None,
        "packagedDir": packaged, "workflow": wf,
        "captureSeconds": read_key(root, UE_VERDICT, "captureSeconds"),
    }
    if not (vp.is_file() and sha and frames and runner):
        return None, reading
    row = {
        "name": wf["name"] or "the Unreal street probe",
        "category": CAT_PROBE, "avail": AVAIL_RAN,
        "availWhy": "wrote/%s/on-commit-%s/from-a-windows-actions-runner-work-dir"
                    % (UE_VERDICT, sha),
        "frames": frames, "wrote": wrote or NOTHING.replace(" ", "-"),
        "sha": sha, "when": when, "packagedDir": packaged,
        "captureSeconds": reading["captureSeconds"],
        "sentinel": (wf["paths"] or [PROBE_SENTINEL])[0],
        "runsOn": "+".join(wf["runsOn"]) or NOTHING.replace(" ", "-"),
        "workflowFile": wf.get("file") or PROBE_WORKFLOW,
    }
    return row, reading


# THE MARKERS OF A CONTROLLABLE GAME, counted in the probe's own source. This
# is the derivation behind the sentence "nobody can play it", and it is a
# derivation rather than a sentence somebody typed because the day a pawn
# lands, this page must stop saying it without an edit here. Each entry is
# (name, regex). The count of this tuple IS the denominator printed.
#
# PAWN AND CHARACTER WERE TWO MARKERS UNTIL 2026-09-07 and became one: a
# direct APawn subclass and an ACharacter subclass are not two different
# facts about this project, because Unreal's ACharacter IS an APawn in the
# engine itself. Run 28 landed ALedgerCharacter (`: public ACharacter`), a
# real class the two-marker version could never satisfy the first half of,
# printing 5 of 6 for ever and reading as a permanent gap. Asking one
# question ("is there a pawn to be, of either shape") makes every marker in
# this tuple something this project's own choices can actually satisfy, so
# the denominator means what it says. Fold this back into two if a future
# probe ever wants BOTH an APawn that is not a Character and an ACharacter
# side by side; nothing here has that shape today.
#
# inputBinding ALSO WIDENED THE SAME DAY: BindAxisKey/BindActionKey are the
# calls run 28's code actually makes (`PlayerInputComponent->BindAxisKey(...)`
# in LedgerCharacter.cpp), and \bBindAxis\b never matched "BindAxisKey" (no
# word boundary between "Axis" and "Key"): the marker only read as found
# because SetupPlayerInputComponent's own declaration happened to be in the
# same two files. A marker that passes by a different marker's evidence is
# not testing what its name says.
PLAYER_MARKERS = (
    ("pawnOrCharacterClass", re.compile(
        r"\bpublic\s+APawn\b|:\s*public\s+APawn\b|:\s*public\s+ACharacter\b")),
    ("gameModeClass", re.compile(r":\s*public\s+AGameMode")),
    ("playerStart", re.compile(r"\bAPlayerStart\b")),
    ("inputBinding", re.compile(r"\bSetupPlayerInputComponent\b|"
                                r"\bBindAction(?:Key)?\b|\bBindAxis(?:Key)?\b")),
    ("defaultPawnSetting", re.compile(r"(?i)^\s*DefaultPawnClass\s*=", re.M)),
)
# The one thing the probe DOES borrow, counted separately so the sentence can
# say what it is for rather than only what it is not.
BORROWED_CONTROLLER_RX = re.compile(r"GetFirstPlayerController")
VIEW_TARGET_RX = re.compile(r"SetViewTarget")


def player_markers(root):
    """Does anything in the probe's source make a character a person could
    control? Counted over the probe's own files, with the walk's denominator,
    so "not started" is a reading rather than an opinion."""
    root = Path(root)
    files, blobs = [], []
    for d in PROBE_SOURCE_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix.lower() in (".cpp", ".h", ".cs", ".ini"):
                files.append(p.relative_to(root).as_posix())
                blobs.append(p.read_text(encoding="utf-8", errors="replace"))
    found = {}
    for name, rx in PLAYER_MARKERS:
        found[name] = sum(1 for b in blobs if rx.search(b))
    borrowed = sum(1 for b in blobs if BORROWED_CONTROLLER_RX.search(b))
    aims = sum(1 for b in blobs
               if BORROWED_CONTROLLER_RX.search(b) and VIEW_TARGET_RX.search(b))
    return {
        "filesWalked": len(files), "markers": found,
        "markersAsked": len(PLAYER_MARKERS),
        "markersFound": sum(1 for v in found.values() if v),
        "borrowsController": borrowed, "andOnlyAimsTheCamera": aims,
        "dirs": PROBE_SOURCE_DIRS,
    }


# SOURCE EXISTING AND SOURCE COMPILING ARE DIFFERENT CLAIMS, and markers alone
# cannot tell a syntax error from a working class: this reads the runner's own
# build log rather than assuming a marker match means the engine accepted it.
BUILD_STAMP_RX = re.compile(r"^#\s*UE probe build\s*-\s*([0-9a-f]{7,40})", re.M)


def probe_compiled(root):
    """(compiled, reading). Whether the WHOLE project, including whatever
    player_markers() just found in source, compiled clean on the runner, read
    from production/d1-probe/ue-build.txt's own coldBuildExit key: a full
    recompile is the stronger of the two exits that file prints, because an
    incremental warmBuild can in principle skip a file a real cold build would
    not. NAMES THE COMMIT THE EVIDENCE IS FROM rather than asserting it
    matches this checkout's HEAD, the same way the picture caption below names
    the commit the frame was written on without re-verifying it against
    git rev-parse: an older build recorded here does not silently become
    evidence for source that has changed since.
    """
    p = Path(root) / UE_BUILD
    if not p.is_file():
        return False, {"seen": False, "coldBuildExit": None, "buildSha": None}
    text = p.read_text(encoding="utf-8", errors="replace")
    cold = read_key(root, UE_BUILD, "coldBuildExit")
    m = BUILD_STAMP_RX.search(text)
    return cold == "0", {"seen": cold is not None,
                         "coldBuildExit": cold,
                         "buildSha": m.group(1) if m else None}


# KEYS THAT EXIST NOWHERE IN THIS REPOSITORY, ON PURPOSE. These name what would
# answer "is there a playable build", and because none is ever emitted today
# they are also the selftest's rejecting fixture. Pinning this probe to a key
# that exists would break the tool on the day somebody does the work.
PLAYABLE_KEYS = ("playableSession", "inputRead", "sessionMinutes")


def playable_build(root):
    """THE ROW THAT USED TO LIE. It printed packagedBuilds=0 from an .exe walk
    of this checkout while the page beside it said nothing is playable. The
    walk answers "is a packaged build COMMITTED HERE"; the keys answer "did
    anybody play a session", and no committed key answers the second."""
    root = Path(root)
    exes, walked = packaged_builds(root)
    found = [k for k in PLAYABLE_KEYS
             if key_present(root, SIM_VERDICT, k) or key_present(root, UE_VERDICT, k)]
    probe_row, _ = visual_probe(root)
    return {
        "category": CAT_PLAYABLE, "avail": NOTHING,
        "exesHere": len(exes), "filesWalked": walked,
        "keysFound": len(found), "keysAsked": len(PLAYABLE_KEYS),
        "keys": PLAYABLE_KEYS, "probeRan": bool(probe_row),
        "captureSeconds": read_key(root, UE_VERDICT, "captureSeconds"),
        "shotReached": read_key(root, UE_VERDICT, "shotReached"),
    }


def code_only(root):
    """Counted in this checkout and labelled as such. It says how much is
    written, and it may not say anything about what runs on his machine."""
    root = Path(root)
    projs = sorted((root / "ledger").glob("*/*.csproj")) \
        if (root / "ledger").is_dir() else []
    console = 0
    for p in projs:
        if "<OutputType>Exe</OutputType>" in p.read_text(encoding="utf-8",
                                                         errors="replace"):
            console += 1
    cs = [p for p in root.rglob("*.cs")
          if not {"obj", "bin", ".git"} & set(p.parts)]
    engine = (root / "ledger" / "ProjectSettings" / "ProjectVersion.txt").is_file()
    exes, walked = packaged_builds(root)
    return {"category": CAT_CODE, "avail": AVAIL_UNVERIFIED,
            "projects": len(projs), "console": console,
            "csFiles": len(cs), "enginePresent": engine,
            "exesHere": len(exes), "filesWalked": walked}


# ---------------------------------------------------------------------------
# READERS. One implementation of each.
# ---------------------------------------------------------------------------

GATES_RX = re.compile(r"ALL GATES:(.*)$", re.M)
GATE_RX = re.compile(r"^([A-Za-z]+)\s+([A-Za-z0-9_]+)")
STAMP_RX = re.compile(r"^#[^\n]*?\b([0-9a-f]{7,40})\s+@(\d+)", re.M)


def read_stamp(root, rel):
    """(sha, epoch) from a verdict file's line 1, which by this project's own
    rule names the commit it was measured on. Parsed and never echoed: line 1
    of the simulation verdict carries an em-dash, and quoting it would redden
    the formatting law on a page nobody edited."""
    p = Path(root) / rel
    if not p.is_file():
        return None, None
    m = STAMP_RX.search(p.read_text(encoding="utf-8", errors="replace")[:400])
    return (m.group(1), int(m.group(2))) if m else (None, None)


ACCEPTANCE_RX = re.compile(r"^acceptance:\s*(.*?)(?=^[a-z_]+:\s|\Z)",
                           re.M | re.S)


def read_milestone_acceptance(root, rel):
    """The milestone file's own `acceptance:` field, or None. Read the same
    STRUCTURAL way queue_state() below reads `status:` (a labelled field, not
    a guess about which paragraph is an instruction), so this is not the
    prose parser RULING 3 forbids: it is one named key, from one named file,
    the same way the rest of this file already reads that file's header."""
    if not rel:
        return None
    p = Path(root) / rel
    if not p.is_file():
        return None
    m = ACCEPTANCE_RX.search(p.read_text(encoding="utf-8", errors="replace"))
    return " ".join(m.group(1).split()) if m else None


def read_gates(root, rel=SIM_VERDICT):
    """{gate: verdict} off the LAST ALL GATES line, plus how many there were.
    Last-wins, and named so: a reader who found two would be merging two
    moments."""
    p = Path(root) / rel
    if not p.is_file():
        return {}, {"gateLines": 0, "present": False}
    text = p.read_text(encoding="utf-8", errors="replace")
    hits = GATES_RX.findall(text)
    if not hits:
        return {}, {"gateLines": 0, "present": True}
    out = {}
    for part in hits[-1].split("|"):
        m = GATE_RX.match(part.strip())
        if m:
            out[m.group(2)] = m.group(1)
    return out, {"gateLines": len(hits), "present": True,
                 "stat": "last-wins/the-last-ALL-GATES-line-in-the-file"}


KEY_RX_CACHE = {}


def read_key(root, rel, key):
    """The LAST value of key=value in a file, or None. LAST-WINS, named so
    wherever printed. A key that appears once per shot needs the shot naming
    or it is two moments under one name: write it as "key@token" and the value
    comes from the last line carrying that token."""
    p = Path(root) / rel
    if not p.is_file():
        return None
    key, _, on = key.partition("@")
    rx = KEY_RX_CACHE.get(key)
    if rx is None:
        rx = KEY_RX_CACHE[key] = re.compile(r"\b%s=([^\s]+)" % re.escape(key))
    hits = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if on and on not in line:
            continue
        hits += rx.findall(line)
    return hits[-1] if hits else None


def key_present(root, rel, prefix):
    """Does ANY key beginning with this prefix exist in the file? This is how a
    required question is asked, so the day a run emits the key the area starts
    reading it without an edit here."""
    p = Path(root) / rel
    if not p.is_file():
        return False
    text = p.read_text(encoding="utf-8", errors="replace")
    return re.search(r"\b%s[A-Za-z0-9_]*=" % re.escape(prefix), text) is not None


FRACTION_RX = re.compile(r"^(\d+)/(\d+)$")


def read_fraction(root, rel, key):
    """(numerator, denominator) for a committed N/M reading, or (None, None).

    THE AUDIBILITY READINGS ARE FRACTIONS ON PURPOSE. lieHeard=0/90 is the
    number that stopped the memory area reading as healthy, and a bare 0 could
    not have: the denominator is what says 90 chances were taken and none was
    heard. A key whose value is not N/M comes back as nothing measured rather
    than as a zero.
    """
    v = read_key(root, rel, key)
    if v is None:
        return None, None
    m = FRACTION_RX.match(v.strip())
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


# ---------------------------------------------------------------------------
# THE SIX AREAS AND THE SEVENTH NODE, AS A CHAIN A READER CAN FOLLOW.
#
# Jafar asked for the game as a small set of connected visual areas, with the
# path drawn: player action, witnessed crime, gossip, a noticeable consequence.
# So the areas are ORDERED AS THAT PATH and the diagram draws it, rather than
# being a grid of tiles whose order means nothing.
#
# THE STATE WORD IS DERIVED, never typed, and the vocabulary is closed. In the
# order the rules are applied:
#
#   nothing measured    no committed key answers the question and no artifact
#                       on this page shows it either. Not a health word.
#   seen, not measured  no committed key answers it, AND a committed artifact
#                       from a named run is SHOWN ON THIS PAGE. The reader is
#                       looking at the evidence, so the page says what was
#                       observed and, in the same breath, what is unverified.
#   not started         the thing does not exist in the source yet, counted
#                       over the source (0 of N markers in M files).
#   in source, unproven a source-scanned thing has N of M markers (N > 0) AND
#                       no build log records a clean compile of this project.
#                       Markers alone cannot tell a syntax error from a
#                       working class, so this is as far as a source scan
#                       gets without one.
#   built, not walked   a source-scanned thing has N of M markers (N > 0) AND
#                       a build log records a clean compile. Code existing
#                       and compiling is not a person having launched it and
#                       walked it: that check does not exist in this
#                       repository yet, so this page must not claim it.
#   failing             a named gate in the verdict is not ok.
#   runs, unheard       every named gate ok AND a committed sweep fraction
#                       says a player never hears the result (0 of N).
#   runs, and heard     every named gate ok AND a committed sweep fraction
#                       says the route does reach a spoken line (K of N).
#   runs in text only   every named gate ok, no audibility reading either way,
#                       and no packaged build is committed in this checkout.
#   playable            every named gate ok AND a packaged build is committed
#                       here. No area has printed this; it is here so that the
#                       day one lands, the page says it without an edit.
#
# WHY nothing-measured AND seen-not-measured OUTRANK failing: an unanswered
# question must not read better than an answered one.
#
# WHY runs-and-heard IS NOT A HEALTH WORD EITHER. It says a line was heard IN
# THE TEXT HARNESS, and the blocker beside it says no visual build carries it.
# Four states stay apart on this page: code exists, a harness passes, a probe
# renders, a person controls a build.
# ---------------------------------------------------------------------------

WORD_NOTHING = NOTHING
WORD_SEEN = "seen, not measured"
WORD_NOT_STARTED = "not started"
WORD_UNPROVEN = "in source, unproven"
WORD_BUILT = "built, not walked"
WORD_FAILING = "failing"
WORD_UNHEARD = "runs, unheard"
WORD_HEARD = "runs, and heard"
WORD_HARNESS = "runs in text only"
WORD_PLAYABLE = "playable"

WORD_CLASS = {
    WORD_NOTHING: "s-none", WORD_SEEN: "s-seen",
    WORD_NOT_STARTED: "s-notstarted", WORD_UNPROVEN: "s-unproven",
    WORD_BUILT: "s-built", WORD_FAILING: "s-failing",
    WORD_UNHEARD: "s-unheard", WORD_HEARD: "s-heard",
    WORD_HARNESS: "s-harness", WORD_PLAYABLE: "s-playable",
}

AREAS = (
    {
        "key": "street-and-its-look",
        "name": "the street you see",
        "chain": "where it all happens",
        "asks": "does the street render Meridian's own materials",
        # THE TWO KEYS THAT WOULD MEASURE IT, and neither is emitted by any
        # run. They are two halves: the quad answers "does a texture override
        # reach the sampler", and the frame-excluding-the-quads answers "does
        # it reach the STREET and not only the control". The verdict's own
        # header says any whole-frame statistic from run 25 includes the three
        # control boxes and must exclude them first.
        "needs": ("quadChroma", "shotChromaExQuads"),
        "needsSays": ("no committed key measures the texture yet. quadChroma* "
                      "would carry the colour control quad, shotChromaExQuads* "
                      "the whole frame with the three control boxes excluded, "
                      "each with its pixel count"),
        "needsIn": UE_VERDICT,
        # THE OBSERVATION, AND WHAT IT IS ALLOWED TO CLAIM. Rendered only when
        # the frame it describes is embedded in this page and the record naming
        # the run is in this checkout. An observation whose evidence the reader
        # cannot see is not offered.
        "observedSays": ("brick, cobbles, wood and glass are visible in the "
                         "frame at the top of this page, which the probe run "
                         "stamped below wrote"),
        "observedIn": "production/queue/123-the-sampler-reads-the-engine-"
                      "default-texture.md",
        "unverifiedSays": ("that no surface is still the engine default, and "
                           "how much of the street is textured. The one "
                           "surface check set in advance was invalid: it "
                           "sampled glass a metre away while the brick it "
                           "named sat sixteen metres behind"),
        "blocker": "textured in the frame, and no key measures it",
        "gates": ("lighting", "lamps", "reflect", "bloom", "grain", "vignette",
                  "ao", "post", "framing", "screenshots", "frame", "traffic",
                  "dressing"),
        "readings": ((UE_VERDICT, ("shotsWrote", "piecesTextured",
                                   "materialsStatus",
                                   "shotDistinctBuckets@vign_camA_day")),
                     (UE_BUILD, ("materialCompile", "materialStatus"))),
        "dependsOn": (),
    },
    {
        "key": "player-control",
        "name": "a character you control",
        "chain": "the player action the chain starts from",
        "asks": "is there anybody to be, and anything bound to input",
        # NO GATE AND NO KEY WATCHES THIS, so it is read out of the probe's
        # own source every run.
        "needs": (),
        "needsIn": UE_VERDICT,
        "sourceScan": True,
        # TRUE WHETHER THE SOURCE MARKERS BELOW ARE 0 OR ALL FOUND: this is
        # the one thing no source scan and no build log can prove, and it is
        # the honest gap whichever way the marker count moves next.
        "blocker": "not yet launched from a plain start, and nobody has "
                  "walked it",
        "gates": (),
        "readings": ((UE_VERDICT, ("shotCamPlaced", "captureSeconds")),),
        "dependsOn": ("street-and-its-look",),
    },
    {
        "key": "the-crime-loop",
        "name": "the crime you commit",
        "chain": "the deed the town has to notice",
        "asks": "does a job run, pay and come back at you",
        "needs": (),
        "needsIn": SIM_VERDICT,
        "blocker": "runs in the console harness, not in the street",
        "gates": ("actOne", "actTwo", "actThree", "jobRan", "takingsBanked",
                  "launder", "disguise", "discredit", "law", "suspicionActs",
                  "killings", "blood", "disposal", "threat", "accident",
                  "harm", "carry", "secretReachedDay", "empire", "fall",
                  "allegiance", "budgets", "economy", "ops", "access",
                  "dayJob"),
        "readings": ((SIM_VERDICT, ("jobsDone", "jobsMissed", "takings",
                                    "peakHeat")),),
        "dependsOn": ("player-control",),
    },
    {
        "key": "people-and-their-memory",
        "name": "who saw it, and what they remember",
        "chain": "the witnessed crime",
        "asks": "do they perceive, remember and carry it",
        "needs": (),
        "needsIn": SIM_VERDICT,
        # THE READING THAT STOPPED THIS AREA READING AS HEALTHY. Its twelve
        # gates all say ok, and queue 136 found the page telling Jafar the moat
        # was fine on the day the sweep proved it inaudible. The gates answer
        # "did the machinery turn"; this fraction answers "could a player hear
        # it", and they are different questions.
        "audible": (STUDY, "lieHeard",
                    "a lie the player was caught in changed a spoken line"),
        "alsoAudible": (STUDY, "liveSilent",
                        "recognition beats that stayed silent in the shipped "
                        "build"),
        "blocker": "the machinery turns and nothing you hear changes",
        "gates": ("knowledge", "retelling", "ghost", "provenance", "confab",
                  "companionSight", "perception", "population", "npcsMoved",
                  "crowd", "bodies", "witnessCar"),
        "readings": ((SIM_VERDICT, ("gossipHeat", "knownLeads", "witnesses",
                                    "npcs", "pop")),),
        "dependsOn": ("the-crime-loop",),
    },
    {
        "key": "conversation",
        "name": "what they say about you",
        "chain": "the gossip",
        "asks": "does anything they say point back at what you did",
        "needs": (),
        "needsIn": SIM_VERDICT,
        # THE ONE ROUTE THE SWEEP FOUND THAT SPEAKS. 540 of 3240 spoken lines
        # in the real arm are a response to something the player did, and the
        # first talk about a sighting fires about 6 game minutes after it.
        "audible": (STUDY, "realPointed",
                    "spoken lines that answered something the player did"),
        "alsoAudible": (STUDY, "differ",
                        "spoken lines where the real arm and the canned arm "
                        "said different words"),
        "blocker": "heard in the text harness, in no visual build",
        "gates": ("beats", "claims", "deedClaims", "ui", "font", "phones"),
        "readings": ((SIM_VERDICT, ("checks", "confronts", "labels")),
                     (STUDY, ("firstTalkGameMinutes", "playWindowGameMinutes",
                              "atUtc"))),
        "dependsOn": ("people-and-their-memory",),
    },
    {
        "key": "voice",
        "name": "whether you hear it",
        "chain": "the consequence, made noticeable",
        "asks": "does anybody actually speak a line out loud",
        # NO GATE WATCHES THIS. The gate names are read off the ALL GATES line
        # every run and the unmapped list proves the set was walked.
        "needs": ("speechGate",),
        "needsSays": ("not one gate in the run is a speech gate, so nothing "
                      "watches whether a line is ever spoken aloud"),
        "needsIn": SIM_VERDICT,
        "blocker": "nothing watches whether a line is ever spoken",
        "gates": (),
        "readings": ((SIM_VERDICT, ("speechSpoken", "speechLive",
                                    "speechPlayed", "speechAsked",
                                    "speechVoices")),),
        "dependsOn": ("conversation",),
    },
    {
        "key": "the-worlds-props",
        "name": "the town it happens in",
        "chain": "the content that dresses the street above",
        "asks": "is the town dressed with its own things",
        "needs": (),
        "needsIn": SIM_VERDICT,
        "blocker": "adopted in the harness, not staged in the street",
        "gates": ("places", "household", "worldText", "score", "mix", "preset",
                  "scoreAudible", "ossei"),
        "readings": ((SIM_VERDICT, ("adopted", "refused")),),
        "dependsOn": (),
        "feedsBackInto": "street-and-its-look",
    },
)


def area_states(root, shown_frame=None):
    """(areas, reading). Every word derived, every number named with its file.

    `shown_frame` is the frame THIS PAGE IS EMBEDDING, or None. It is an input
    because the word "seen, not measured" is a claim about what the reader can
    see: without the picture the same area reads nothing measured, and that is
    the coupling rather than an oversight.
    """
    root = Path(root)
    gates, gmeta = read_gates(root)
    exes, filesWalked = packaged_builds(root)
    playable = len(exes) > 0
    scan = player_markers(root)
    compiled, compile_reading = probe_compiled(root)
    scan = dict(scan, compiled=compiled, compileReading=compile_reading)
    mapped = set()
    out = []
    for spec in AREAS:
        named = list(spec["gates"])
        mapped.update(named)
        seen = {g: gates[g] for g in named if g in gates}
        bad = sorted(g for g, v in seen.items() if v.lower() != "ok")
        missing_q = [n for n in spec["needs"]
                     if not key_present(root, spec["needsIn"], n)]
        heard_n = heard_d = None
        heard_why = ""
        if spec.get("audible"):
            f, k, words = spec["audible"]
            heard_n, heard_d = read_fraction(root, f, k)
            heard_why = "%s=%s/%s in %s: %s" % (k, heard_n, heard_d, f, words)
        observed = None
        if spec.get("observedSays") and missing_q:
            record = (Path(root) / spec["observedIn"]).is_file()
            if record and shown_frame:
                observed = spec["observedSays"]

        if missing_q and observed:
            word = WORD_SEEN
            why = ("%s. What no run has measured: %s. 0 of %d key(s) that "
                   "would measure it are in %s: all of %s."
                   % (observed, spec.get("unverifiedSays", "the rest"),
                      len(spec["needs"]), spec["needsIn"],
                      ", ".join(spec["needs"])))
        elif missing_q:
            word = WORD_NOTHING
            why = ("%s. 0 of %d key(s) that would answer it are in %s: all of "
                   "%s." % (spec.get("needsSays", "no committed key answers it"),
                            len(spec["needs"]), spec["needsIn"],
                            ", ".join(spec["needs"])))
        elif spec.get("sourceScan"):
            # THREE STATES, NOT TWO, because "markers found" and "the project
            # compiles" are different claims a source scan cannot conflate.
            # A 2026-09-07 correction: this branch used to read found==0 as
            # WORD_NOT_STARTED and anything else as WORD_HARNESS ("runs in
            # text only"), which was never an honest word for native Unreal
            # source and went straight from untested to FALSE the day markers
            # first landed nonzero: run 28 compiled a real character, game
            # mode, input binding and player start, and the page kept saying
            # "no character, no pawn, no game mode, no player start" beside
            # it. Neither new word claims a person has launched or walked
            # anything; that check does not exist yet, so the AREA'S OWN
            # blocker text (not this why-string) is what still says so.
            found = scan["markersFound"]
            cr = scan["compileReading"]
            if found == 0:
                word = WORD_NOT_STARTED
                why = ("0 of %d marker(s) of a controllable character are in "
                       "the %d probe source file(s) walked under %s."
                       % (scan["markersAsked"], scan["filesWalked"],
                          ", ".join(scan["dirs"])))
            elif scan["compiled"]:
                word = WORD_BUILT
                why = ("%d of %d marker(s) of a controllable character are "
                       "in the %d probe source file(s) walked under %s, and "
                       "%s records a clean compile of the whole project on "
                       "commit %s (coldBuildExit=%s). Nobody has launched "
                       "that build and walked it yet: that is a different "
                       "question, and no instrument answering it is "
                       "committed in this checkout yet."
                       % (found, scan["markersAsked"], scan["filesWalked"],
                          ", ".join(scan["dirs"]), UE_BUILD,
                          cr["buildSha"] or NOTHING, cr["coldBuildExit"]))
            else:
                word = WORD_UNPROVEN
                why = ("%d of %d marker(s) of a controllable character are "
                       "in the %d probe source file(s) walked under %s, but "
                       "%s %s. Markers alone cannot tell a syntax error from "
                       "a working class."
                       % (found, scan["markersAsked"], scan["filesWalked"],
                          ", ".join(scan["dirs"]), UE_BUILD,
                          "carries no coldBuildExit reading" if not
                          cr["seen"] else
                          "records coldBuildExit=%s, not a clean compile"
                          % cr["coldBuildExit"]))
        elif not seen:
            word = WORD_NOTHING
            why = ("none of the %d gate(s) this area names is in %s"
                   % (len(named), SIM_VERDICT))
        elif bad:
            word = WORD_FAILING
            why = "%d of %d named gate(s) not ok: %s" % (len(bad), len(seen),
                                                         ", ".join(bad))
        elif heard_n is not None:
            word = WORD_UNHEARD if heard_n == 0 else WORD_HEARD
            why = ("%d of %d named gate(s) ok in %s, which says the machinery "
                   "turned. What a player could hear is a different question "
                   "and a different file: %s."
                   % (len(seen), len(named), SIM_VERDICT, heard_why))
        elif playable:
            word = WORD_PLAYABLE
            why = ("every one of the %d named gate(s) is ok and a packaged "
                   "build is committed in this checkout" % len(named))
        else:
            word = WORD_HARNESS
            why = ("%d of %d named gate(s) ok in %s, and no packaged build is "
                   "committed in this checkout (0 of %d file(s) walked here). "
                   "That is a statement about this checkout and not about your "
                   "PC." % (len(seen), len(named), SIM_VERDICT, filesWalked))

        pairs = spec["readings"]
        vals, srcs = [], []
        for one_src, keys in pairs:
            srcs.append(one_src)
            vals += [(k, read_key(root, one_src, k)) for k in keys]
        if spec.get("alsoAudible"):
            f, k, words = spec["alsoAudible"]
            if f not in srcs:
                srcs.append(f)
            vals.append((k, read_key(root, f, k)))
        if spec.get("audible"):
            f, k, _w = spec["audible"]
            if f not in srcs:
                srcs.append(f)
            vals.insert(0, (k, read_key(root, f, k)))
        out.append(dict(spec, word=word, why=why, gatesSeen=len(seen),
                        gatesNamed=len(named), gatesBad=len(bad),
                        missing=missing_q, readings=vals,
                        readingsFrom="+".join(srcs), heardNum=heard_n,
                        heardDen=heard_d, observed=observed, scan=scan))
    unmapped = sorted(g for g in gates if g not in mapped)
    words = {}
    for a in out:
        words[a["word"]] = words.get(a["word"], 0) + 1
    sim_sha, sim_when = read_stamp(root, SIM_VERDICT)
    ue_sha, ue_when = read_stamp(root, UE_VERDICT)
    return out, {
        "areas": len(out), "gatesInVerdict": len(gates),
        "gatesMapped": len(mapped & set(gates)), "unmapped": unmapped,
        "gateLines": gmeta.get("gateLines", 0),
        "simPresent": gmeta.get("present", False),
        "simSha": sim_sha, "simWhen": sim_when,
        "ueSha": ue_sha, "ueWhen": ue_when,
        "playable": playable, "exesInCheckout": len(exes),
        "filesWalkedInCheckout": filesWalked, "scan": scan,
        "nothingMeasured": words.get(WORD_NOTHING, 0),
        "seenNotMeasured": words.get(WORD_SEEN, 0),
        "notStarted": words.get(WORD_NOT_STARTED, 0),
        "failing": words.get(WORD_FAILING, 0),
        "unheard": words.get(WORD_UNHEARD, 0),
        "heard": words.get(WORD_HEARD, 0),
        "harnessOnly": words.get(WORD_HARNESS, 0),
    }


# ---------------------------------------------------------------------------
# THE NEXT THREE, FROM ONE SMALL SOURCE AND NOTHING ELSE.
#
# WHAT WAS DELETED HERE, 2026-09-07, and why it could not be repaired. This
# function used to split production/NOW.md on "## ", keep the sections whose
# heading carried the newest date and the word RULED, and read their numbered
# items. On the day the page was rejected that rule produced, as the plan:
# "FIND THE CAUSE OF THE UNTEXTURED STREET", which run 25 had completed hours
# earlier, and "QUEUE 119, the three unbriefed players", which Jafar had
# superseded the same morning. Both were still in the file, because NOW.md is a
# LOG and a log keeps what happened. No parser can tell a finished instruction
# from a live one by looking at its heading.
#
# Jafar: "Use one small source of current priorities instead of copying the
# plan into several documents." That source is production/next-three.json. It
# is read strictly: an unparseable file is nothing measured with the reason,
# never a silent empty list, and every item is checked against its own queue
# file so a completed one cannot render as a task.
# ---------------------------------------------------------------------------

DONE_WORDS = ("DONE", "SUPERSEDED", "DROPPED", "ABANDONED", "COMPLETE",
              "COMPLETED")
STATUS_RX = re.compile(r"^status:\s*([A-Za-z]+)", re.M | re.I)


def queue_state(root, rel):
    """(state, why) for the queue file an item names. The states are:
    ready, done, moved-to-done, missing, none. Only `ready` may render as a
    task; the page refuses the rest loudly rather than showing a finished
    item as the plan."""
    if not rel:
        return "none", "the-item-names-no-queue-file"
    root = Path(root)
    p = root / rel
    name = Path(rel).name
    done_p = root / QUEUE_DONE_DIR / name
    if rel.replace("\\", "/").startswith(QUEUE_DONE_DIR + "/"):
        return "moved-to-done", "the-path-itself-is-under-%s" % QUEUE_DONE_DIR
    if not p.is_file():
        if done_p.is_file():
            return "moved-to-done", ("the-file-is-under-%s-now"
                                     % QUEUE_DONE_DIR)
        return "missing", "no-file-at-%s-in-this-checkout" % rel
    m = STATUS_RX.search(p.read_text(encoding="utf-8", errors="replace"))
    word = (m.group(1).upper() if m else None)
    if word is None:
        return "ready", "no-status-line-in-%s" % rel
    if word in DONE_WORDS:
        return "done", "its-status-line-says-%s" % word
    return "ready", "its-status-line-says-%s" % word


# ---------------------------------------------------------------------------
# A DONE STEP'S EVIDENCE. RULED 2026-09-08, section 7 of the crime ruling. A
# `done` entry in next-three.json is a CLAIM plus the instrument that proves
# it: each {file, key} pair names a committed file and an EXACT key=value
# token that must stand as a whole whitespace-delimited token on one of its
# lines. This page checks the INSTRUMENT, never the claim.
#
# WHOLE TOKEN, NEVER SUBSTRING: collisionStatus=REALLY must not satisfy
# collisionStatus=REAL, and the no-spaces-in-values rule every verdict in this
# repository already follows is what makes splitting on whitespace safe.
#
# A DIFFERENT QUESTION FROM key_present() ABOVE, and both are kept because
# they are asked for different reasons. key_present asks "has any key with
# this PREFIX ever been emitted here", which is how an area asks a question a
# run may not have answered yet. This asks "is this exact reading still in
# this file", which is how a finished step stays proven.
#
# WHY THE TELEGRAM MESSAGE ID IS NOT AN EVIDENCE KEY, for the reader who asks
# why the street step's proof is the walk verdict and not the send. The send
# is published by CI in production/pc-ops/outbox-sweep.txt, whose line reads
# "outbox: sent ... clipRef=production/d1-probe/ue-walk.gif ... messageId=31
# descriptorKind=animation ...". THAT FILE IS OVERWRITTEN BY EVERY LATER
# SWEEP, so a messageId=31 evidence key would pass today and refuse the whole
# ladder tomorrow, putting a stale banner on his phone for a step that really
# is done. Evidence has to be durable or it is a timer. A durable append-only
# send ledger is the next rung and is being added separately; when it exists
# the street entry gains a third evidence pair naming it.
# ---------------------------------------------------------------------------

def evidence_token_found(root, rel, token):
    """(fileExists, found) for ONE exact key=value token in ONE committed
    file. No tally and no wording here: read_done() below owns the counting
    and the refusal string, so there is one place that counts them."""
    p = Path(root) / rel
    if not rel or not p.is_file():
        return False, False
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if token and token in line.split():
            return True, True
    return True, False


def read_done(root, data, next_titles):
    """(entries, tally) for next-three.json's `done` array: the finished
    steps, in order, each with every evidence pair OPENED and searched.

    THE TALLY IS WHOLE-FILE and each number is named by what it counts:
    `claimed` is how many entries the file names, `proven` is how many of
    those had EVERY one of their keys found, `keysFound`/`keysAsked` is the
    pair count underneath, and `refusal` is the FIRST disagreement in file
    order. An absent `done` reads 0/absent and is NOT a refusal: a plan that
    has finished nothing is a plan that has finished nothing. A `done` entry
    that names no evidence at all IS a refusal, because an unproven done rung
    is the invented progress RULING 3 forbids."""
    raw = data.get("done")
    present = isinstance(raw, list)
    # THREE STATES, NEVER TWO. A `done` field that is there but is not a list
    # is not the same fact as no `done` field at all, and reading the second
    # word for the first would be a malformed plan printing as an empty one.
    word = "present" if present else "absent" if raw is None else "not-a-list"
    entries, refusal = [], (None if present or raw is None
                            else "done-is-not-a-list")
    for n, item in enumerate(raw if present else [], start=1):
        e = item if isinstance(item, dict) else {}
        title = str(e.get("title") or NOTHING)
        pairs, why = [], None
        for pair in (e.get("evidence") or []):
            pair = pair if isinstance(pair, dict) else {}
            rel = str(pair.get("file") or "")
            key = str(pair.get("key") or "")
            exists, found = evidence_token_found(root, rel, key)
            pairs.append({"file": rel or NOTHING.replace(" ", "-"),
                          "key": key or NOTHING.replace(" ", "-"),
                          "fileExists": exists, "found": found})
            if why is not None:
                continue
            if not exists:
                why = ("done-step-%d-evidence-missing/%s"
                       % (n, rel or "none-named"))
            elif not found:
                why = "done-step-%d-key-absent/%s" % (n, key or "none-named")
        if not pairs and why is None:
            why = "done-step-%d-evidence-missing/none-named" % n
        # THE STRUCTURAL DISAGREEMENT WINS THE WORDING when both are true: a
        # title standing in both arrays names the edit to make, and its
        # evidence is beside the point until one copy is gone.
        if title in next_titles:
            why = "title-in-both-done-and-next"
        entries.append({
            "title": title, "why": str(e.get("why") or NOTHING),
            "queue": e.get("queue"),
            "doneOn": str(e.get("doneOn") or NOTHING),
            "evidence": pairs,
            "proven": bool(pairs) and all(p["found"] for p in pairs)
            and why is None,
            "refusal": why,
        })
        if refusal is None and why is not None:
            refusal = why
    return entries, {
        "present": present, "word": word, "claimed": len(entries),
        "proven": sum(1 for e in entries if e["proven"]),
        "keysAsked": sum(len(e["evidence"]) for e in entries),
        "keysFound": sum(1 for e in entries for p in e["evidence"]
                         if p["found"]),
        "refusal": refusal,
    }


def next_three(root):
    """(items, reading). Items carry their own refusal, so a stale entry
    renders as a stale entry and never as the plan. The FINISHED steps come
    back on the reading as `done`, read and proved by read_done() above; the
    NEXT_ASKED cap applies to `next` only, because a plan may finish more
    steps than it shows at once."""
    root = Path(root)
    p = root / PRIORITIES
    blank = {"present": False, "parsed": False, "named": 0, "shown": 0,
             "refused": 0, "ruledBy": None, "ruledOn": None,
             "milestone": None, "milestoneFrom": None, "why": "",
             "done": [], "donePresent": False, "doneWord": "absent",
             "doneNamed": 0, "doneProven": 0,
             "doneKeysAsked": 0, "doneKeysFound": 0, "doneRefusal": None}
    if not p.is_file():
        blank["why"] = "no-file-at-%s-in-this-checkout" % PRIORITIES
        return [], blank
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except ValueError as e:                                      # noqa: BLE001
        blank["present"] = True
        blank["why"] = "%s-did-not-parse-as-json/%s" % (PRIORITIES,
                                                        type(e).__name__)
        return [], blank
    if not isinstance(data, dict) or not isinstance(data.get("next"), list):
        blank["present"] = True
        blank["why"] = "%s-carries-no-next-list" % PRIORITIES
        return [], blank
    items = []
    for entry in data["next"]:
        if not isinstance(entry, dict):
            continue
        rel = entry.get("queue")
        state, why = queue_state(root, rel)
        items.append({
            "title": str(entry.get("title") or NOTHING),
            "why": str(entry.get("why") or NOTHING),
            "queue": rel, "state": state, "stateWhy": why,
            "refused": state in ("done", "moved-to-done", "missing"),
        })
    done, tally = read_done(root, data, set(i["title"] for i in items))
    reading = {
        "present": True, "parsed": True, "named": len(items),
        "shown": sum(1 for i in items if not i["refused"]),
        "refused": sum(1 for i in items if i["refused"]),
        "ruledBy": data.get("ruledBy"), "ruledOn": data.get("ruledOn"),
        "milestone": data.get("milestone"),
        "milestoneFrom": data.get("milestoneFrom"),
        "why": "",
        # THE FINISHED STEPS. doneNamed is what the file CLAIMS; doneProven is
        # how many of those claims every named key survived this run.
        "done": done, "donePresent": tally["present"],
        "doneWord": tally["word"],
        "doneNamed": tally["claimed"], "doneProven": tally["proven"],
        "doneKeysAsked": tally["keysAsked"],
        "doneKeysFound": tally["keysFound"],
        "doneRefusal": tally["refusal"],
    }
    return items, reading


NEXT_RULE = (
    "read from %s, which is the one place the current priorities are written "
    "down, and from nothing else. No heading, no log and no queue number "
    "chooses them: a human or a ruling edits that file. An item whose task "
    "file has moved to %s or whose status says DONE is refused here rather "
    "than shown, and an item nobody named there cannot appear at all."
    % (PRIORITIES, QUEUE_DONE_DIR)
)


# ---------------------------------------------------------------------------
# THE LADDER. RULING 3, Jafar, 2026-09-07, verbatim: "a ladder at the very
# top: the steps to a playable loop, in order, with the current one
# highlighted, so I can read 'step 2 of 10' in one glance from my phone.
# Steps done, current, next, derived from next-three.json and the milestone
# file, no prose parsing."
#
# NO PARALLEL LADDER ARRAY WAS ADDED, and that is a choice this file makes
# rather than next-three.json, said here because RULING 3 asked which one was
# chosen. The ordered list RULING 3 asked for already exists in both named
# sources: the `done` and `next` arrays' ORDER already IS the priority order
# (the selftest asserts the steps read "control", then "crime", then "gossip"
# across the two), and `milestone`/`milestoneFrom` already name the rung at
# the top. A second, parallel `ladder` array would only give the two a chance
# to drift.
#
# WHAT "DONE" MEANS, CORRECTED 2026-09-08 and decided once rather than guessed
# per rung. It used to mean nothing that could be shown: next-three.json
# deleted a finished step instead of marking it, so the current rung was
# always rung one and finishing a step moved the page from STEP 1 OF 4 to STEP
# 1 OF 3, which is the opposite of what RULING 3 asked to read. The ruling of
# 2026-09-08 gave that file a `done` array whose entries carry the date and
# the {file, key} evidence read_done() opens and searches. So this ladder
# counts done rungs first, then the next ones, then the goal, and a done rung
# whose evidence this run could not find refuses the WHOLE ladder rather than
# standing as a number on his phone. With no `done` array at all the ladder
# still says so in words rather than a tick nobody measured.
# ---------------------------------------------------------------------------

def ladder_rungs(root, items_all, r3):
    """(rungs, reading). rungs is the climb, in order: the same refusal guard
    queue_state() already applies to a next-three item is reused rung by rung
    here, and once more for the goal, because a stale rung shown as CURRENT
    is the exact fault this page already refuses elsewhere.

    THE `next` HALF IS CAPPED TO NEXT_ASKED, like the next three cards below
    it, so today's climb and those cards name the same steps and a tap from
    one reaches the sheet the other already built; a longer plan is announced
    rather than silently grown past what the reader can tap through. THE
    `done` HALF IS NOT CAPPED: it is the count under "step N of M", and a
    silently dropped finished step would move that N.

    TWO NUMBERING SEQUENCES, KEPT APART ON PURPOSE. `num` is the rung's place
    on the ladder, counting done rungs first, and it is what "STEP N OF M"
    reads. `taskNum` is the item's place in `next`, which is what the task
    cards and their sheets (#t-1 .. #t-3) are keyed by. They were the same
    number until done rungs existed; a rung linking to #t-<num> would now open
    the wrong sheet.
    """
    done = r3.get("done") or []
    items = items_all[:NEXT_ASKED]
    rungs = []
    for d in done:
        rungs.append({
            "num": len(rungs) + 1, "title": d["title"], "state": "done",
            "refused": False, "taskNum": None, "doneOn": d["doneOn"],
            "stateWhy": ("proved-by-%d-evidence-key(s)-on-%s"
                         % (len(d["evidence"]), d["doneOn"])),
        })
    current_set = False
    for n, it in enumerate(items, start=1):
        if it["refused"]:
            state = "stale"
        elif not current_set:
            state, current_set = "current", True
        else:
            state = "next"
        rungs.append({
            "num": len(rungs) + 1, "title": it["title"], "state": state,
            "refused": it["refused"], "stateWhy": it["stateWhy"],
            "taskNum": n, "doneOn": None,
        })
    milestone_from = r3.get("milestoneFrom")
    m_state, m_why = (queue_state(root, milestone_from) if milestone_from
                      else ("none", "no-milestoneFrom-in-%s" % PRIORITIES))
    goal_refused = m_state in ("done", "moved-to-done", "missing")
    rungs.append({
        "num": len(rungs) + 1, "title": r3.get("milestone") or NOTHING,
        "state": "goal", "refused": goal_refused, "stateWhy": m_why,
        "taskNum": None, "doneOn": None,
    })
    # EVERY NAMED STEP IS DONE, SO THE GOAL IS WHAT HE IS ON. Without this
    # the page read "STEP None OF 4" the first time the last named step
    # landed, because `current` is only ever set on a `next` item and there
    # were none left. Caught by the selftest's own accepting case on the live
    # plan, not in review: the run that finished the crime and the overheard
    # consequence emptied `next` in one go.
    #
    # THE GOAL KEEPS ITS OWN STATE WORD. It is marked `goal-current` rather
    # than `current` so the page still says GOAL on that rung and the reader
    # is not told a milestone is a step; the number counts it because he asked
    # to read "step N of M" and with everything below it done the goal is
    # honestly where the climb has reached. A REFUSED goal is left alone: a
    # milestone whose own file says it is finished must not become the
    # current rung of a ladder that is about to refuse itself.
    # ONLY WHEN THERE ARE NO NAMED STEPS LEFT, never when steps exist and are
    # all STALE. A stale step is one this page could not prove; promoting the
    # goal over a plan it cannot read would put a step number on his phone
    # that no evidence supports, which is the invented progress ruling 3
    # exists to forbid. Empty and unprovable are different facts and the
    # rejecting fixture for the second one asserts the ladder still says so.
    if not items and not goal_refused \
            and not any(r["state"] == "current" for r in rungs):
        rungs[-1]["state"] = "goal-current"
    current_num = next((r["num"] for r in rungs
                        if r["state"] in ("current", "goal-current")),
                       None)
    # THE WHOLE LADDER IS REFUSED BY EITHER HALF, and the reason says which:
    # a done rung nobody can prove and a goal whose own file says it is
    # finished both make every number here a fiction, so one flag drives the
    # one banner and the checks read that flag rather than the goal's.
    done_refusal = r3.get("doneRefusal")
    return rungs, {
        "total": len(rungs), "stepsShown": len(items),
        "stepsNamedTotal": len(items_all),
        "capped": len(items_all) > NEXT_ASKED,
        "currentNum": current_num, "goalState": m_state, "goalWhy": m_why,
        "goalRefused": goal_refused,
        "refused": bool(goal_refused or done_refusal),
        "refusedBy": ("goal-state" if goal_refused
                      else "done-evidence" if done_refusal else "none"),
        "refusedWhy": (m_why if goal_refused else done_refusal or "none"),
        "staleCount": sum(1 for r in rungs if r["refused"]),
        # THE DONE HALF, whole-ladder: doneShown is what this ladder drew,
        # doneClaimed what the file named, doneProven how many of those claims
        # every named key survived, and the key pair count underneath.
        "doneShown": len(done), "doneClaimed": r3.get("doneNamed", 0),
        "doneProven": r3.get("doneProven", 0),
        "donePresent": r3.get("donePresent", False),
        "doneKeysAsked": r3.get("doneKeysAsked", 0),
        "doneKeysFound": r3.get("doneKeysFound", 0),
        "doneEntries": done,
        "acceptance": read_milestone_acceptance(root, milestone_from),
        "milestoneFrom": milestone_from,
    }


def ladder_html(rungs, reading):
    """Plain HTML, not SVG: see the module docstring's RULING 3 note. Every
    rung says its own state in words, never colour alone, and a rung this run
    could not verify says so rather than borrowing CURRENT or NEXT. A DONE
    RUNG SAYS THE WORD DONE AND THE DATE IT LANDED, never a glyph alone: a
    tick is unreadable at arm's length and unprovable at any distance."""
    if reading["refused"]:
        why = ("The goal's own file says its status is %s (%s)."
               % (esc(reading["goalState"]), esc(reading["goalWhy"]))
               if reading["goalRefused"] else
               "A step this plan calls finished cannot be proved from this "
               "checkout: %s." % esc(reading["refusedWhy"]))
        return ('<section class="ladder ladderStale" id="ladder">'
                '<p class="ladderHead">THE LADDER IS STALE</p>'
                '<p class="ladderNow">%s Fix the plan before trusting a step '
                'count here.</p>'
                '</section>' % why)
    cur, total = reading["currentNum"], reading["total"]
    if cur:
        head = "STEP %d OF %d" % (cur, total)
        now_line = esc(next(r["title"] for r in rungs if r["num"] == cur))
    else:
        head = "NO CURRENT STEP"
        now_line = "Every named step below is stale; see why on each one."
    rows = []
    for r in rungs:
        if r["refused"]:
            cls, tag = "r-stale", "STATE NOT PROVEN"
            body = "This step cannot be shown: %s." % esc(r["stateWhy"])
        elif r["state"] in ("goal", "goal-current"):
            # THE GOAL RUNG HAS NO TASK SHEET, so it must never fall through
            # to the branch below, which formats a #t-<taskNum> the goal does
            # not have. The first render after every named step landed crashed
            # here on a None, which is why `goal-current` is matched HERE and
            # not treated as a kind of current.
            cls = "r-goal r-goal-current" if r["state"] == "goal-current" \
                else "r-goal"
            tag = "GOAL, AND THE ONE YOU ARE ON" \
                if r["state"] == "goal-current" else "GOAL"
            body = esc(r["title"])
            if reading["acceptance"]:
                body += (' <a class="tap" href="#t-goal">what done looks '
                        'like</a>')
        elif r["state"] == "done":
            cls, tag = "r-done", "DONE"
            body = ('%s <span class="rungOn">finished %s</span>'
                    % (esc(r["title"]), esc(r["doneOn"] or NOTHING)))
        else:
            cls = "r-current" if r["state"] == "current" else "r-next"
            tag = r["state"].upper()
            # #t-<taskNum>, NEVER #t-<num>: the sheets are keyed by the item's
            # place in `next`, and the rung's own number counts done rungs
            # first, so the two parted company the day a done rung existed.
            body = ('%s <a class="tap" href="#t-%d">what it rests on</a>'
                    % (esc(r["title"]), r["taskNum"]))
        rows.append('<li class="rung %s"><span class="tag">%s</span>%s</li>'
                    % (cls, tag, body))
    cap = ""
    if reading["capped"]:
        cap = ('<p class="ladderNote">(+%d more step(s) named, not shown of '
              '%d; see the next three below.)</p>'
              % (reading["stepsNamedTotal"] - reading["stepsShown"],
                 reading["stepsNamedTotal"]))
    # THE NOTE IS THE DONE HALF'S DENOMINATOR IN WORDS. With finished steps
    # named it says how many of the rungs they are and how many evidence keys
    # this run found again; with none named it says the words nothing measured,
    # so an empty plan can never read as a clean one.
    if reading["doneShown"]:
        note = ("Steps already done: %d of %d rung(s) here. Each one carries "
                "the date it landed and the evidence keys that prove it, %d "
                "of %d found again in this checkout by this run. A finished "
                "step moves into the plan's done list and is never deleted, "
                "and a claim this page cannot prove takes the whole ladder "
                "down rather than standing as a number."
                % (reading["doneShown"], reading["total"],
                   reading["doneKeysFound"], reading["doneKeysAsked"]))
    else:
        note = ("Steps already done: %s. The plan's done list names none, so "
               "this page counts none rather than showing a tick nobody "
               "measured." % NOTHING)
    return ('<section class="ladder" id="ladder">'
            '<p class="ladderHead">%s</p>'
            '<p class="ladderNow">%s</p>'
            '<ol class="rungs">%s</ol>%s'
            '<p class="ladderNote">%s</p>'
            '</section>'
            % (esc(head), now_line, "".join(rows), cap, esc(note)))


def goal_sheet(reading):
    """The tap behind the goal rung: what done looks like, quoted from the
    milestone file's own acceptance: field, never typed here."""
    return ('<section class="sheet" id="t-goal"><div class="inner">'
            '<a class="close" href="#map">back to the map</a>'
            '<h3>the goal of this ladder</h3>'
            '<dl><dt>what done looks like</dt><dd>%s</dd>'
            '<dt>its state</dt><dd>%s, because %s</dd>'
            '<dt>how this is chosen</dt><dd>%s</dd></dl>'
            '<a class="close" href="#map">back to the map</a>'
            '</div></section>'
            % (esc(reading["acceptance"] or NOTHING), esc(reading["goalState"]),
               esc(reading["goalWhy"]), esc(NEXT_RULE)))


LADDER_START = "<!-- LADDER START -->"
LADDER_END = "<!-- LADDER END -->"


def ladder_slice(page):
    """The bytes between the ladder's own markers, or "" if either is
    missing. Every check that must not see a raw path or a gate count OUTSIDE
    the ladder, or must confirm one INSIDE it, reads only this slice, never
    the whole page: the rest of the page is allowed both, one tap down."""
    i, j = page.find(LADDER_START), page.find(LADDER_END)
    return page[i:j] if 0 <= i < j else ""


# ---------------------------------------------------------------------------
# THE MATERIAL CHANGE DETECTOR. THE THREE GROUPS' MEANING IS UNCHANGED, and
# may not change: tools/map-notify.py imports material_fields, digest_of,
# changed_groups and decode_fields from this file and reads mapDigest and
# mapFields out of the SERVED page. The three groups are still the three the
# notifier names in words: q1 the list of what you can run, q2 the state an
# area is in, q3 the next three.
#
# q3 NOW ALSO CARRIES EACH ITEM'S LIVE/STALE STATE, added for the ladder:
# without it, a step's queue file flipping to DONE while next-three.json's
# own text sits unedited moved the ladder's CURRENT tag with nothing for
# tools/map-notify.py to see, so "a ladder that moves a step" would never
# wake his phone. This does not change what q3 MEANS (the next three); it
# only stops the group from reading identical when one of them quietly went
# stale.
#
# NOT MATERIAL, deliberately: the generation time, the commit, the page bytes,
# the picture's encoded size, and every number that moves without moving a
# word. A regenerated timestamp must never wake his phone.
# ---------------------------------------------------------------------------

DIGEST_RX = re.compile(r"mapDigest=([0-9a-f]{12})")


def material_fields(rows, areas, items):
    """The canonical material state, as sorted whitespace-free strings."""
    q1 = sorted("%s|%s|%s" % (r["name"].replace(" ", "_"),
                              r["category"].replace(" ", "-"),
                              r["avail"].replace(" ", "-"))
                for r in rows)
    q2 = ["%s|%s" % (a["key"], a["word"].replace(" ", "-").replace(",", ""))
          for a in areas]
    q3 = ["%d|%s|%s" % (i + 1, re.sub(r"\W+", "-", it["title"]).strip("-")[:60],
                        "stale" if it["refused"] else "live")
          for i, it in enumerate(items[:NEXT_ASKED])]
    return {"q1": q1, "q2": q2, "q3": q3}


def digest_of(fields):
    blob = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def previous_digest(path):
    """The digest in the file this run is about to overwrite, or None."""
    p = Path(path)
    if not p.is_file():
        return None
    m = DIGEST_RX.search(p.read_text(encoding="utf-8", errors="replace"))
    return m.group(1) if m else None


def changed_groups(fields, prev_fields):
    if prev_fields is None:
        return None
    return [g for g in ("q1", "q2", "q3") if fields[g] != prev_fields.get(g)]


PREV_FIELDS_RX = re.compile(r"mapFields=([A-Za-z0-9+/=]+)")


def encode_fields(fields):
    import base64
    blob = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return base64.b64encode(blob.encode("utf-8")).decode("ascii")


def decode_fields(page):
    import base64
    m = PREV_FIELDS_RX.search(page or "")
    if not m:
        return None
    try:
        return json.loads(base64.b64decode(m.group(1)).decode("utf-8"))
    except Exception:                                            # noqa: BLE001
        return None


def previous_fields(path):
    p = Path(path)
    if not p.is_file():
        return None
    return decode_fields(p.read_text(encoding="utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# THE SERVED PAGE, WHICH IS NOT THE PAGE THIS RUN WROTE. Every check below
# reads bytes this process just produced, which proves the generator and
# proves nothing about what his phone loads. So the tool REQUESTS the
# published URL and reports what came back, and when the request does not
# complete it says so IN WORDS. The fetch is tools/publish-glance.py's, not a
# second implementation, and the URL is derived from the git remote.
# ---------------------------------------------------------------------------

SERVED_TIMEOUT_SEC = 10
GITHUB_REMOTE_RX = re.compile(r"github\.com[:/]+([^/]+)/([^/\s]+?)(?:\.git)?$")


def pages_url(root):
    """(url, howDerived) for the published copy of this page."""
    out = GLANCE.git(root, "remote", "get-url", "origin") or ""
    m = GITHUB_REMOTE_RX.search(out.strip())
    if not m:
        return None, "no-github-remote-in-this-clone"
    return ("https://%s.github.io/%s/%s" % (m.group(1), m.group(2), OUT_NAME),
            "git-remote-origin/owner.%s/repo.%s/github-pages-project-url-"
            "convention/not-read-back-from-the-pages-api"
            % (m.group(1), m.group(2)))


def load_fetch():
    """tools/publish-glance.py's fetch(), or None with the reason."""
    p = ROOT / "tools" / "publish-glance.py"
    if not p.is_file():
        return None, "tools/publish-glance.py-is-not-in-this-checkout"
    try:
        spec = importlib.util.spec_from_file_location("publish_glance", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.fetch, "tools/publish-glance.py/fetch"
    except Exception as exc:                                     # noqa: BLE001
        return None, "import-failed/%s" % type(exc).__name__


def served_reading(url, how, attempt=True, timeout=SERVED_TIMEOUT_SEC,
                   fetch=None, expect_digest=None):
    """What the published URL answered, or the words nothing measured.
    measured=False means WE DID NOT FIND OUT. It is never rendered as a 404
    and never rendered as ok."""
    r = {"url": url, "how": how, "attempted": bool(attempt and url),
         "measured": False, "status": None, "ctype": "", "bytes": 0,
         "marker": False, "digest": None, "expect": expect_digest,
         "reason": "", "result": NOTHING, "fetcher": ""}
    if not url:
        r["reason"] = how
        return r
    if not attempt:
        r["reason"] = "not-attempted/--no-served-check-was-passed"
        return r
    if fetch is None:
        fetch, why = load_fetch()
        r["fetcher"] = why
        if fetch is None:
            r["reason"] = "no-fetcher/%s" % why
            return r
    else:
        r["fetcher"] = "supplied-by-the-caller"
    res = fetch(url, timeout=timeout)
    if not res.get("measured"):
        r["reason"] = re.sub(r"\s+", " ", res.get("err", "") or
                             "request-did-not-complete").strip()
        return r
    body = res.get("body") or ""
    r.update(measured=True, status=res.get("status"),
             ctype=(res.get("ctype") or "").split(";")[0].strip(),
             bytes=len(body.encode("utf-8")),
             marker=PUBLISHER_MARKER in body)
    m = DIGEST_RX.search(body)
    r["digest"] = m.group(1) if m else None
    if r["status"] == 404:
        r["result"] = "not-published-at-the-derived-url"
    elif r["status"] and 200 <= r["status"] < 300 and not r["marker"]:
        r["result"] = "something-else-is-served-here"
    elif r["status"] and 200 <= r["status"] < 300:
        r["result"] = ("this-run" if r["digest"] == expect_digest
                       else "an-earlier-run")
    else:
        r["result"] = "http-%s" % r["status"]
    return r


def served_sentence(r):
    """THE SAME FACT IN WORDS, because a reader must not have to decode a key
    to learn that nothing was requested."""
    if not r["attempted"]:
        return ("The published page was NOT requested by this run (%s), so "
                "every check ran on the bytes this run generated and nothing "
                "here describes what your phone loads." % r["reason"])
    if not r["measured"]:
        return ("The published page could NOT be requested from where this "
                "page was generated: %s. So the checks ran on the bytes this "
                "run generated, and this run found out nothing about the page "
                "served at %s. The page size is not an answer to that "
                "question." % (r["reason"], r["url"]))
    return ("The published page at %s answered HTTP %s (%s, %d bytes) and it "
            "is %s: served digest %s against this run's %s."
            % (r["url"], r["status"], r["ctype"] or "no-content-type",
               r["bytes"], r["result"], r["digest"] or NOTHING,
               r["expect"] or NOTHING))


# ---------------------------------------------------------------------------
# THE PICTURE. Jafar asked for the latest actual street image SHOWN, not
# linked, and named the frame: production/d1-probe/ue-vign_camA_day.png from
# run 25. It is not hardcoded. The frame is chosen out of the shot lines the
# verdict itself wrote (status=WROTE, file=...), preferring the day camera,
# so a later run that writes different frames moves this picture without an
# edit here; today that choice resolves to exactly the file he named.
#
# HOW IT REACHES THE PUBLISHED SITE. It is embedded as a data URI, through
# tools/glance.py's encoder, which is this repository's one implementation of
# "shrink a frame into a byte budget". So no second file has to be copied into
# _site, no path can go stale, and tools/publish-glance.py needs no change: the
# page it already publishes carries the picture inside it.
# ---------------------------------------------------------------------------

FRAME_DIR = "production/d1-probe"
FRAME_PREFERENCE = ("camA_day", "camB_day", "camA", "camB")


def choose_frame(root, probe_reading):
    """(relPath, why) for the frame to show, or (None, why)."""
    names = list(probe_reading.get("frameFiles") or [])
    if not names:
        return None, ("no shot line in %s carries status=WROTE with a file "
                      "name, so this run had no frame to offer" % UE_VERDICT)
    on_disk = [n for n in names if (Path(root) / FRAME_DIR / n).is_file()]
    if not on_disk:
        return None, ("%s names %d written frame(s) and none of them is a "
                      "file in this checkout under %s"
                      % (UE_VERDICT, len(names), FRAME_DIR))
    for pref in FRAME_PREFERENCE:
        for n in on_disk:
            if pref in n:
                return ("%s/%s" % (FRAME_DIR, n),
                        "the %s frame, chosen from the %d frame(s) %s says "
                        "this run wrote, %d of which are files in this "
                        "checkout" % (pref, len(names), UE_VERDICT,
                                      len(on_disk)))
    return ("%s/%s" % (FRAME_DIR, on_disk[0]),
            "the first of the %d written frame(s) in %s, none of which matched "
            "a preferred camera" % (len(on_disk), UE_VERDICT))


def read_picture(root, probe_reading, budget):
    """The embedded street frame, or the words nothing measured with a reason.

    A MISSING RESIZER IS NAMED AND NEVER PAPERED OVER. Without Pillow the
    glance's encoder returns the source bytes unresized, which for a 1.8 MB PNG
    is a page nobody's phone will load, so it is refused here with the reason
    rather than shipped. The page then says what the frame shows in words and
    says it could not show it, which is honest; a broken image on a phone is
    indistinguishable from a page that failed to load.
    """
    rel, why = choose_frame(root, probe_reading)
    out = {"rel": rel, "why": why, "shown": False, "b64": None, "mime": None,
           "bytes": 0, "quality": None, "how": "", "sourceBytes": 0,
           "budget": budget, "resizer": "none"}
    if rel is None:
        return out
    p = Path(root) / rel
    out["sourceBytes"] = p.stat().st_size
    try:
        import PIL                                              # noqa: F401
        out["resizer"] = "Pillow"
    except ImportError:
        out["how"] = ("Pillow is not installed where this page was generated, "
                      "so the frame could not be resized, and a %d byte source "
                      "will not be embedded whole" % out["sourceBytes"])
        return out
    try:
        b64, mime, n, how, q = GLANCE.encode_image(p, budget)
    except OSError as e:                                         # noqa: BLE001
        out["how"] = "%s could not be read or decoded: %s" % (rel, e)
        return out
    if n > budget:
        out["how"] = ("the smallest encoding tools/glance.py could make was "
                      "%d bytes against a %d byte budget, so it was not "
                      "embedded" % (n, budget))
        out["bytes"] = n
        return out
    out.update(shown=True, b64=b64, mime=mime, bytes=n, quality=q, how=how)
    return out


# ---------------------------------------------------------------------------
# THE PAGE.
# ---------------------------------------------------------------------------

CSS = """
:root { color-scheme: dark light; }
* { box-sizing: border-box; }
body { margin: 0 auto; padding: %(pad)dpx %(pad)dpx 40px; max-width: 620px;
  background: #14161a; color: #e7e9ec;
  font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
  Helvetica, Arial, sans-serif; -webkit-text-size-adjust: 100%%;
  overflow-wrap: break-word; }
a { color: #8fb8ff; }
.ladder { margin: 0 0 22px; }
.ladderHead { font-size: 26px; font-weight: 800; letter-spacing: 0.01em;
  color: #f3f5f7; margin: 0 0 3px; }
.ladderNow { font-size: 17px; font-weight: 600; color: #dbe0e6;
  margin: 0 0 12px; line-height: 1.35; }
.rungs { list-style: none; margin: 0; padding: 0; }
.rung { border-left: 5px solid #4b535d; border-radius: 6px;
  background: #191c21; padding: 9px 11px; margin: 0 0 7px;
  font-size: 14.5px; line-height: 1.4; color: #ccd2d8; }
.rung .tag { display: inline-block; font-size: 10.5px; font-weight: 800;
  letter-spacing: 0.07em; text-transform: uppercase; color: #8a9199;
  margin-right: 6px; }
.r-current { border-left-color: #6fd08c; background: #16241c; }
.r-current .tag { color: #6fd08c; }
.r-goal { border-left-color: #8fb8ff; }
.r-goal .tag { color: #8fb8ff; }
.r-stale { border-left-color: #ff8f8f; background: #241a1a; }
.r-stale .tag { color: #ff8f8f; }
.r-done { border-left-color: #8a9199; }
.r-done .tag { color: #b6bec7; }
.rungOn { color: #8a9199; font-size: 12.5px; white-space: nowrap; }
.ladderNote { font-size: 12.5px; line-height: 1.5; color: #868d95;
  margin: 8px 0 0; }
.ladderStale .ladderHead { color: #ff8f8f; }
.top { display: flex; justify-content: space-between; align-items: baseline;
  font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase;
  color: #7d848c; margin-bottom: 14px; }
.top b { color: #c9ced5; letter-spacing: 0.16em; }
h2 { font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase;
  color: #868d95; margin: 16px 0 8px; font-weight: 700; }
.now { font-size: 21px; line-height: 1.3; font-weight: 600; margin: 0 0 11px;
  color: #f3f5f7; }
.shot { display: block; width: 100%%; height: auto; border-radius: 8px;
  background: #0d0f12; }
.cap { font-size: 13px; line-height: 1.45; color: #99a1a9; margin: 8px 0 0; }
.noshot { border: 1px dashed #565d66; border-radius: 8px; padding: 16px;
  color: #b9c0c8; font-size: 15px; }
.card { border: 1px solid #2b3038; border-left: 5px solid #4b535d;
  border-radius: 8px; background: #191c21; padding: 13px 14px;
  margin: 0 0 12px; }
.card p { margin: 0; }
.card .lab { font-size: 11px; letter-spacing: 0.13em; text-transform: uppercase;
  color: #8a9199; font-weight: 700; margin-bottom: 5px; }
.card .big { font-size: 17px; font-weight: 600; color: #f0f2f4;
  line-height: 1.35; }
.card .sub { font-size: 14.5px; line-height: 1.5; color: #aab1b9;
  margin-top: 6px; }
.card .press { font-size: 14.5px; line-height: 1.5; color: #dbe0e6;
  margin-top: 8px; }
.card .press code { font-family: ui-monospace, SFMono-Regular, Menlo,
  monospace; font-size: 13.5px; color: #ffe9b0; }
.c-probe { border-left-color: #3f8f56; }
.c-noplay { border-left-color: #9a4444; }
.c-tools { border-left-color: #5a6470; }
.c-mile { border-left-color: #8fb8ff; }
.mile { border-left: 5px solid #8fb8ff; padding: 2px 0 2px 12px;
  margin: 16px 0 0; }
.mile .lab { display: block; font-size: 11px; letter-spacing: 0.13em;
  text-transform: uppercase; color: #8a9199; font-weight: 700;
  margin-bottom: 3px; }
.mile .big { font-size: 17px; font-weight: 600; color: #f0f2f4;
  line-height: 1.35; }
.mile .sub { font-size: 14.5px; color: #aab1b9; }
.c-task { border-left-color: #d3a44a; }
.c-stale { border-left-color: #d05a5a; background: #241a1a; }
.task .num { font-size: 12px; letter-spacing: 0.13em; color: #d3a44a;
  font-weight: 700; }
.flow { display: block; width: 100%%; max-width: %(flow)dpx; height: auto;
  margin: 0 auto; }
.nbox { fill: #191c21; stroke-width: 2; }
.ntitle { fill: #f0f2f4; font-weight: 600; }
.nblock { fill: #a7aeb6; }
.narrow { stroke: #5a6470; stroke-width: 2; fill: none; }
.nhead { fill: #5a6470; }
.nback { stroke: #4d545d; stroke-width: 2; fill: none; stroke-dasharray: 4 4; }
.pilltext { font-weight: 700; letter-spacing: 0.04em; fill: #14161a; }
.s-none .nbox { stroke: #6b727a; } .s-none .pill { fill: #99a0a8; }
.s-seen .nbox { stroke: #8fb8ff; } .s-seen .pill { fill: #8fb8ff; }
.s-notstarted .nbox { stroke: #b06a6a; } .s-notstarted .pill { fill: #d09090; }
.s-unproven .nbox { stroke: #9b8fd9; } .s-unproven .pill { fill: #ab9fe0; }
.s-built .nbox { stroke: #3fb0a0; } .s-built .pill { fill: #4fc2b2; }
.s-failing .nbox { stroke: #ff8f8f; } .s-failing .pill { fill: #ff8f8f; }
.s-unheard .nbox { stroke: #d9973c; } .s-unheard .pill { fill: #e5aa55; }
.s-heard .nbox { stroke: #63b97e; } .s-heard .pill { fill: #74cc90; }
.s-harness .nbox { stroke: #c9a25a; } .s-harness .pill { fill: #d7b46a; }
.s-playable .nbox { stroke: #6fd08c; } .s-playable .pill { fill: #6fd08c; }
.legend { font-size: 13px; color: #99a1a9; line-height: 1.5; margin: 12px 0 0; }
.tap { display: block; text-align: center; font-size: 13.5px; color: #8fb8ff;
  text-decoration: none; padding: 12px 0 4px; }
.foot { margin: 30px 0 0; font-size: 13px; color: #7d848c; line-height: 2; }
.foot a { margin-right: 16px; text-decoration: none; }
.sheet { display: none; }
.sheet:target { display: block; position: fixed; top: 0; right: 0; bottom: 0;
  left: 0; background: #14161a; padding: 16px 16px 60px; overflow-y: auto;
  font-size: 15.5px; line-height: 1.55; z-index: 9; }
.sheet .inner { max-width: 620px; margin: 0 auto; }
.sheet h3 { font-size: 20px; margin: 6px 0 4px; color: #f2f4f6; }
.sheet .word { font-size: 14px; font-weight: 700; letter-spacing: 0.06em;
  text-transform: uppercase; margin: 0 0 14px; }
.sheet dt { font-size: 11px; letter-spacing: 0.13em; text-transform: uppercase;
  color: #868d95; margin-top: 18px; font-weight: 700; }
.sheet dd { margin: 5px 0 0; color: #ccd2d8; }
.sheet pre { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular,
  Menlo, monospace; font-size: 12px; line-height: 1.6; color: #aeb5bd;
  margin: 5px 0 0; }
.close { display: inline-block; color: #8fb8ff; text-decoration: none;
  font-size: 16px; min-height: 44px; line-height: 44px; padding: 0 4px;
  font-weight: 600; }
@media (prefers-color-scheme: light) {
  body { background: #f4f6f8; color: #191d22; }
  .ladderHead { color: #0f1216; } .ladderNow { color: #23282e; }
  .rung { background: #ffffff; border-color: #d9dee4; color: #2b3138; }
  .r-current { background: #eafaf0; } .r-stale { background: #fdeeee; }
  .r-done { background: #f2f4f6; } .r-done .tag { color: #5d646c; }
  .rungOn { color: #5d646c; }
  .ladderNote { color: #5d646c; }
  .top { color: #5d646c; } .top b { color: #23282e; }
  h2 { color: #5d646c; }
  .now { color: #0f1216; }
  .cap { color: #545b63; }
  .card { background: #ffffff; border-color: #d9dee4; }
  .card .big { color: #12161a; } .card .sub { color: #4d545c; }
  .card .press { color: #23282e; }
  .card .press code { color: #7a4a00; }
  .card .lab { color: #5d646c; }
  .mile .lab { color: #5d646c; }
  .mile .big { color: #12161a; }
  .mile .sub { color: #4d545c; }
  .c-stale { background: #fdeeee; }
  .nbox { fill: #ffffff; }
  .ntitle { fill: #12161a; } .nblock { fill: #4d545c; }
  .narrow { stroke: #8a929b; } .nhead { fill: #8a929b; }
  .nback { stroke: #8a929b; }
  .legend, .foot { color: #545b63; }
  .noshot { color: #33383e; border-color: #a8b0b8; }
  .sheet:target { background: #f4f6f8; }
  .sheet h3 { color: #12161a; } .sheet dt { color: #5d646c; }
  .sheet dd { color: #2b3138; } .sheet pre { color: #3c434a; }
}
"""

PAGE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>LEDGER map: what exists, what you can run, what is next</title>
<style>%s</style>
</head>
<body id="map">
%s
</body>
</html>
"""


def css():
    return CSS % {"pad": BODY_PAD_PX, "flow": FLOW_W}


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def hours_since(epoch, now):
    if not epoch:
        return None
    return int((now - datetime.datetime.fromtimestamp(
        epoch, datetime.timezone.utc)).total_seconds() // 3600)


def age_words(hrs):
    """A NEGATIVE age is not an age: it means the stamp is ahead of this run's
    clock, which happened the moment the selftest pinned a fixed clock behind a
    real run's epoch and printed "-5 hour(s) ago". A number that reads as an
    age while meaning the opposite is the quiet instrument fault, so the two
    cases have different words."""
    if hrs is None:
        return NOTHING
    if hrs < 0:
        return "stamped %d hour(s) AHEAD of this run's clock" % abs(hrs)
    if hrs < 48:
        return "%d hour(s) ago" % hrs
    return "%d day(s) ago" % (hrs // 24)


# ------------------------------------------------------------- screen one

def now_html(picture, probe, hrs, areas):
    """WHAT EXISTS NOW: one sentence, and the frame itself.

    The sentence is assembled from readings, not typed: the frame count and
    the commit come from the verdict the run wrote, the age from its epoch,
    and the second half from the source scan of the probe's own player
    control files.

    THIS SECOND HALF WAS A LIE FOR A WHOLE DAY, 2026-09-07: the docstring
    above already claimed it came from the scan, but the code ignored the
    variable it had just read and always printed "Nobody to be in it yet."
    A character, a game mode, input binding and a player start compiled on
    the runner (run 28) while this sentence kept saying nobody existed. Now
    it reads scan["markersFound"] like the docstring always said it did.
    """
    street = [a for a in areas if a["key"] == "street-and-its-look"][0]
    scan = street["scan"]
    who = ("Nobody to be in it yet." if scan["markersFound"] == 0 else
          "A character exists in the probe's own source now; nobody has "
          "launched a build and walked it yet.")
    sentence = "A textured street in Meridian, rendered on your PC. %s" % who
    if picture["shown"]:
        shot = ('<img class="shot" alt="the Meridian street, %s" src="data:%s;'
                'base64,%s" width="780">'
                % (esc(picture["rel"]), esc(picture["mime"]),
                   picture["b64"]))
    else:
        shot = ('<p class="noshot">%s: the street frame could not be shown '
                'here. %s</p>' % (esc(NOTHING),
                                  esc(picture["how"] or picture["why"])))
    # THE CAPTION IS THE OBSERVATION AND ITS LIMIT IN ONE BREATH, and it is
    # kept to what fits beside the picture: the run that wrote it, what a
    # person can see in it, and the fact that no key measures it. The file
    # name, the encoded size and the two absent keys are one tap down, because
    # a raw path on the first screen is one of the four faults named.
    if probe:
        cap = ("The probe wrote this on your PC on commit %s, %s. Brick, "
               "cobbles, wood and glass are visible; the bright squares are "
               "measurement controls. No key measures it yet."
               % (probe["sha"], age_words(hrs)))
    else:
        cap = ("%s: %s carries no run this page could read, so nothing here "
               "dates the picture." % (NOTHING, UE_VERDICT))
    return ('<p class="now">%s</p>%s<p class="cap">%s</p>'
            % (esc(sentence), shot, esc(cap)))


def run_html(probe, pb, rows, r1, scan, tail=""):
    """WHAT CAN I RUN, AND WHAT DO I PRESS. Only actions with evidence behind
    them, and the probe is separated from a game IN WORDS, with the source
    scan's denominator in the same sentence as the claim."""
    out = []
    if probe:
        # THIS SENTENCE DECAYED ONCE ALREADY, 2026-09-07: it used to say
        # "Nobody can play it: no character, no pawn, no game mode, no player
        # start" unconditionally, and that went from true to false the day a
        # character, a game mode, input binding and a player start first
        # compiled (run 28), because the sentence was typed rather than
        # derived from scan["markersFound"]. It is derived now, and
        # check_player_control_matches_scan bites if it and the live scan
        # ever disagree again in either direction.
        if scan["markersFound"] == 0:
            sub = ("Nobody can play it: no character, no pawn, no game mode, "
                  "no player start. %d of %d marker(s) of one, over %d "
                  "source file(s). It aims a camera and exits."
                  % (scan["markersFound"], scan["markersAsked"],
                     scan["filesWalked"]))
        else:
            sub = ("This capture still renders offscreen with nobody at the "
                  "controls: %d of %d marker(s) of a controllable character "
                  "are in the probe's own source now, over %d file(s). "
                  "Launching a build and walking it is a different question "
                  "this page does not yet measure."
                  % (scan["markersFound"], scan["markersAsked"],
                     scan["filesWalked"]))
        out.append(
            '<div class="card c-probe" data-avail="%s">'
            '<p class="lab">runs, and it is not a game</p>'
            '<p class="big">The street probe renders %s frames and exits.</p>'
            '<p class="sub">%s</p>'
            '<p class="press">Run it again: push a commit touching '
            '<code>%s</code>.</p></div>'
            % (esc(probe["avail"].replace(" ", "-")), esc(probe["wrote"]),
               esc(sub), esc(probe["sentinel"])))
    else:
        out.append(
            '<div class="card c-probe" data-avail="%s">'
            '<p class="lab">the visual probe</p>'
            '<p class="big">%s.</p>'
            '<p class="sub">%s carries no run this page could read, so there '
            'is nothing here to offer. That is what this checkout holds, not '
            'a statement about your PC.</p></div>'
            % (esc(NOTHING.replace(" ", "-")), esc(NOTHING), esc(UE_VERDICT)))

    out.append(
        '<div class="card c-noplay" data-avail="%s">'
        '<p class="lab">to play</p>'
        '<p class="big">There is nothing to play yet.</p>'
        '<p class="sub">No game executable is committed in this checkout (0 '
        'of %d file(s) walked here), and %d of %d key(s) that would report a '
        'session exist anywhere.</p></div>'
        % (esc(NOTHING.replace(" ", "-")), pb["filesWalked"], pb["keysFound"],
           pb["keysAsked"]))

    out.append(tail)
    picks = [r for r in rows if r["onFirstScreen"]]
    if picks:
        # ONE ROW PER LAUNCHER, and the description is the file's own banner
        # QUOTED AS IT IS WRITTEN. An earlier draft folded them into one
        # sentence and lower-cased the first letter, which turned "ONE WINDOW"
        # into "oNE WINDOW" and then ran two shouted banners together. A
        # description assembled out of somebody else's capitals is not a
        # description.
        press = " or ".join("<code>%s</code>" % esc(r["name"])
                            for r in picks)
        out.append(
            '<div class="card c-tools" data-avail="%s">'
            '<p class="sub">Studio tools, not the game: double-click %s. '
            '%d of %d launcher(s) here, the other %d daemons and one '
            'superseded test; committed here, and whether your copy pulled '
            'them is not visible from here. '
            '<a href="#tools">All %d.</a></p></div>'
            % (esc(AVAIL_UNVERIFIED), press, len(picks), r1["found"],
               r1["found"] - len(picks), r1["found"]))
    else:
        out.append(
            '<div class="card c-tools" data-avail="%s">'
            '<p class="lab">on your PC</p><p class="big">%s.</p>'
            '<p class="sub">No .bat file was found at this checkout\'s root, '
            'so the walk found nothing to offer. That is a broken walk, not '
            'an empty project.</p></div>'
            % (esc(NOTHING.replace(" ", "-")), esc(NOTHING)))
    return "".join(out)


def milestone_html(r3):
    said = r3.get("milestone") or NOTHING
    who = r3.get("ruledBy")
    return ('<p class="mile"><span class="lab">the next milestone</span>'
            '<span class="big">%s.</span> <span class="sub">%s</span></p>'
            % (esc(said[0].upper() + said[1:] if said else NOTHING),
               esc(("Ruled by %s; the three steps to it are below."
                    % who) if who else
                   "Nobody is named as having ruled it.")))


# ------------------------------------------------------------- the diagram

def pill_width(word):
    """The rounded rectangle a status word needs, at the uppercase advance.
    ONE implementation: the drawing and the check both call this, so what is
    measured is what is drawn."""
    # ROUNDED UP, never truncated: int() floors, and a pill one pixel short
    # of its own text is the fault this function was written to end.
    return int(2 * PILL_PAD_PX + len(word) * STATUS_PX * UPPER_ADVANCE_EM
               + 0.9999)


def flow_svg(areas):
    """The chain, drawn. Returns (svg, geometry).

    EVERY STRING IS WRAPPED BEFORE IT IS DRAWN and each box's height comes
    from the lines that came back, because SVG clips silently and a clipped
    line is exactly what was rejected. The geometry is returned so the run can
    print the widest string it drew against the box it drew it in.
    """
    boxes, y = [], 6
    widest = ("", 0, 0)
    for a in areas:
        title = "%s: %s" % (a["name"], a["chain"])
        tlines = wrap_text(title, TITLE_PX, NODE_TEXT_W)
        word = a["word"]
        blocker = a.get("blocker") or ""
        blines = wrap_text(blocker, BLOCKER_PX, NODE_TEXT_W) if blocker else []
        h = (NODE_PAD + len(tlines) * TITLE_LEAD + 8 + PILL_H
             + (6 + len(blines) * BLOCKER_LEAD if blines else 0) + NODE_PAD)
        boxes.append({"a": a, "y": y, "h": h, "title": tlines, "word": word,
                      "blocker": blines})
        for line in tlines:
            if len(line) > widest[1]:
                widest = (line, len(line), TITLE_PX)
        y += h + ARROW_GAP
    total = y - ARROW_GAP + 6
    parts = ['<svg class="flow" viewBox="0 0 %d %d" role="img" '
             'aria-label="the chain from the street to a consequence you can '
             'hear" xmlns="http://www.w3.org/2000/svg">' % (FLOW_W, total)]

    # THE RETURN ARROW, drawn first so the boxes sit over it. The town's
    # content feeds the street it dresses, which is the one edge in this
    # diagram that is not a step in the chain.
    back = [b for b in boxes if b["a"].get("feedsBackInto")]
    if back and boxes:
        b = back[0]
        target = next((x for x in boxes
                       if x["a"]["key"] == b["a"]["feedsBackInto"]), None)
        if target is not None:
            yb, yt = b["y"] + b["h"] / 2.0, target["y"] + target["h"] / 2.0
            parts.append('<path class="nback" d="M%d,%.1f H%d V%.1f H%d"/>'
                         % (NODE_X, yb, GUTTER_X, yt, NODE_X - 8))
            parts.append('<polygon class="nhead" points="%d,%.1f %d,%.1f '
                         '%d,%.1f"/>' % (NODE_X, yt, NODE_X - 9, yt - 5,
                                         NODE_X - 9, yt + 5))

    mid = NODE_X + NODE_W / 2.0
    for i, b in enumerate(boxes):
        a = b["a"]
        if i and not boxes[i - 1]["a"].get("feedsBackInto"):
            y0 = boxes[i - 1]["y"] + boxes[i - 1]["h"]
            parts.append('<path class="narrow" d="M%.1f,%d L%.1f,%d"/>'
                         % (mid, y0 + 3, mid, b["y"] - 9))
            parts.append('<polygon class="nhead" points="%.1f,%d %.1f,%d '
                         '%.1f,%d"/>' % (mid, b["y"] - 2, mid - 6, b["y"] - 11,
                                         mid + 6, b["y"] - 11))
        parts.append('<a href="#a-%s" data-area="%s" class="%s">'
                     % (esc(a["key"]), esc(a["key"]),
                        WORD_CLASS.get(b["word"], "s-none")))
        parts.append('<rect class="nbox" x="%d" y="%d" width="%d" height="%d" '
                     'rx="8"/>' % (NODE_X, b["y"], NODE_W, b["h"]))
        ty = b["y"] + NODE_PAD + TITLE_PX
        for line in b["title"]:
            parts.append('<text class="ntitle" x="%d" y="%d" font-size="%d">'
                         '%s</text>' % (NODE_X + NODE_PAD, ty, TITLE_PX,
                                        esc(line)))
            ty += TITLE_LEAD
        py = ty - TITLE_PX + 8
        pw = pill_width(b["word"])
        parts.append('<rect class="pill" x="%d" y="%d" width="%d" height="%d" '
                     'rx="%d"/>' % (NODE_X + NODE_PAD, py, pw, PILL_H,
                                    PILL_H // 2))
        parts.append('<text class="pilltext" x="%d" y="%d" font-size="%d">%s'
                     '</text>' % (NODE_X + NODE_PAD + PILL_PAD_PX,
                                  py + PILL_H - 6, STATUS_PX,
                                  esc(b["word"].upper())))
        by = py + PILL_H + 6 + BLOCKER_PX
        for line in b["blocker"]:
            parts.append('<text class="nblock" x="%d" y="%d" font-size="%d">'
                         '%s</text>' % (NODE_X + NODE_PAD, by, BLOCKER_PX,
                                        esc(line)))
            by += BLOCKER_LEAD
        parts.append('</a>')
    parts.append('</svg>')
    widest_pill = max((pill_width(b["word"]) for b in boxes), default=0)
    return "".join(parts), {
        "nodes": len(boxes), "svgHeightPx": total, "boxWidthPx": NODE_W,
        "textWidthPx": NODE_TEXT_W, "widestLine": widest[0],
        "widestChars": widest[1], "widestFontPx": widest[2],
        "widestPillPx": widest_pill,
        "widestPillWord": max((b["word"] for b in boxes),
                              key=lambda w: pill_width(w)) if boxes else "",
    }


# ------------------------------------------------------------- the sheets

def readings_text(a):
    vals = [(k, v) for k, v in a["readings"] if v is not None]
    shown = vals[:READINGS_SHOWN]
    out = " ".join("%s=%s" % (k, v) for k, v in shown)
    if len(vals) > READINGS_SHOWN:
        out += " (+%d more not shown of %d)" % (len(vals) - READINGS_SHOWN,
                                                len(vals))
    if not vals:
        return "%s: no reading found in %s" % (NOTHING, a["readingsFrom"])
    return out


def area_sheet(a, areas, r2):
    names = {x["key"]: x["name"] for x in areas}
    deps = ", ".join(names.get(k, k) for k in a.get("dependsOn", ())) or \
        "nothing above it in the chain"
    ev = readings_text(a)
    if a["word"] in (WORD_NOTHING, WORD_SEEN):
        ev = "these are committed and do NOT answer it: " + ev
    gates = ("%d of %d gate(s) this area names are in %s, and %d of them are "
             "not ok" % (a["gatesSeen"], a["gatesNamed"], SIM_VERDICT,
                         a["gatesBad"])) if a["gatesNamed"] else \
        ("this area names no gate in %s: its state is read from the source or "
         "from a key instead" % SIM_VERDICT)
    stamp = []
    for label, sha, when in (("the simulation", r2["simSha"], r2["simWhen"]),
                             ("the street", r2["ueSha"], r2["ueWhen"])):
        if sha and when:
            stamp.append("%s was measured on commit %s" % (label, sha))
        else:
            stamp.append("%s: %s" % (label, NOTHING))
    return ('<section class="sheet %s" id="a-%s"><div class="inner">'
            '<a class="close" href="#map">back to the map</a>'
            '<h3>%s</h3>'
            '<p class="word">%s</p>'
            '<dl><dt>what this asks</dt><dd>%s</dd>'
            '<dt>why it says that</dt><dd>%s</dd>'
            '<dt>the gates behind it</dt><dd>%s</dd>'
            '<dt>the committed readings</dt><dd><pre>%s</pre></dd>'
            '<dt>read from</dt><dd>%s</dd>'
            '<dt>it waits on</dt><dd>%s</dd>'
            '<dt>the runs behind these words</dt><dd>%s</dd></dl>'
            '<a class="close" href="#map">back to the map</a>'
            '</div></section>'
            % (WORD_CLASS.get(a["word"], "s-none"), esc(a["key"]),
               esc(a["name"]), esc(a["word"]), esc(a["asks"]), esc(a["why"]),
               esc(gates), esc(ev), esc(a["readingsFrom"]), esc(deps),
               esc("; ".join(stamp))))


def tools_sheet(rows, r1):
    shown = rows[:TOOLS_SHOWN]
    body = []
    for r in shown:
        body.append('<dt>%s</dt><dd data-avail="%s">%s Availability: %s. '
                    'Derived: %s.</dd>'
                    % (esc(r["name"]), esc(r["avail"].replace(" ", "-")),
                       esc(r["about"]), esc(r["avail"]), esc(r["why"])))
    cap = ""
    if len(rows) > TOOLS_SHOWN:
        cap = ('<p>(+%d more not shown of %d: the list cap bit at %d. Every '
               'count on this page still counts all %d.)</p>'
               % (len(rows) - TOOLS_SHOWN, len(rows), TOOLS_SHOWN, len(rows)))
    return ('<section class="sheet" id="tools"><div class="inner">'
            '<a class="close" href="#map">back to the map</a>'
            '<h3>every launcher at the folder root</h3>'
            '<p>%d file(s) walked at this checkout\'s root, %d of which start '
            'a console program and %d of which matched no known launcher. '
            'Committed here means a pull brings it; whether your copy has '
            'pulled is not visible from here.</p>%s<dl>%s</dl>'
            '<a class="close" href="#map">back to the map</a>'
            '</div></section>'
            % (r1["found"], r1["text"], r1["unknown"], cap, "".join(body)))


def task_sheet(i, it):
    return ('<section class="sheet" id="t-%d"><div class="inner">'
            '<a class="close" href="#map">back to the map</a>'
            '<h3>%d. %s</h3><dl>'
            '<dt>why it is next</dt><dd>%s</dd>'
            '<dt>the task file</dt><dd>%s</dd>'
            '<dt>its state</dt><dd>%s, because %s</dd>'
            '<dt>how this list is chosen</dt><dd>%s</dd></dl>'
            '<a class="close" href="#map">back to the map</a>'
            '</div></section>'
            % (i, i, esc(it["title"]), esc(it["why"]),
               esc(it["queue"] or "none is named"), esc(it["state"]),
               esc(it["stateWhy"]), esc(NEXT_RULE)))


MATERIAL_RULE = (
    "The link is sent again only when one of three things changes: a thing "
    "you can run appears, disappears, changes what kind of thing it is, or "
    "changes its availability word; an area changes its state word; or the "
    "next three change. The generation time, the commit, the page size and "
    "every number that moves without moving a word are NOT material and never "
    "send a message. No previous page is not 'no change': it reads nothing "
    "measured, because a first run cannot tell a stable page from an unseen "
    "one."
)


def about_sheet(model, now, lines):
    pic = model["picture"]
    pic_line = ("shown, %d bytes encoded from a %d byte source at JPEG quality "
                "%s by tools/glance.py; %s"
                % (pic["bytes"], pic["sourceBytes"], pic["quality"], pic["how"])
                ) if pic["shown"] else \
        ("%s: %s" % (NOTHING, pic["how"] or pic["why"]))
    return ('<section class="sheet" id="about"><div class="inner">'
            '<a class="close" href="#map">back to the map</a>'
            '<h3>how this page was made</h3>'
            '<p>Generated by %s at %s UTC from commit %s. Every word above is '
            'read out of a file in the repository at generation time. Nothing '
            'on it is a status anybody typed.</p>'
            '<dl><dt>the picture</dt><dd>%s</dd>'
            '<dt>which bytes were checked</dt><dd>%s</dd>'
            '<dt>what counts as a material change</dt><dd>%s</dd>'
            '<dt>the whole series this run printed</dt><dd><pre>%s</pre></dd>'
            '</dl><a class="close" href="#map">back to the map</a>'
            '</div></section>'
            % (esc(TOOL), esc(now.strftime("%Y-%m-%d %H:%M")),
               esc(model["commit"]), esc(pic_line),
               esc(served_sentence(model["served"])), esc(MATERIAL_RULE),
               esc("\n".join(lines))))


def next_html(items, r3):
    """THE THREE TASK CARDS. A refused item renders as a refusal, never as a
    task: that is the half of "one small source" a file alone cannot enforce."""
    body = []
    for i in range(NEXT_ASKED):
        if i >= len(items):
            body.append(
                '<div class="card c-task task"><p class="num">%d</p>'
                '<p class="big">%s</p><p class="sub">%s names %d item(s), not '
                '%d. A slot filled from anywhere else would be this page '
                'inventing a plan.</p></div>'
                % (i + 1, esc(NOTHING), esc(PRIORITIES), len(items),
                   NEXT_ASKED))
            continue
        it = items[i]
        if it["refused"]:
            body.append(
                '<div class="card c-stale task"><p class="num">%d</p>'
                '<p class="big">This entry is stale and is not shown as a '
                'task.</p><p class="sub">%s names it, and its task file is %s '
                '(%s). Edit %s.</p></div>'
                % (i + 1, esc(PRIORITIES), esc(it["state"]),
                   esc(it["stateWhy"]), esc(PRIORITIES)))
            continue
        body.append(
            '<div class="card c-task task"><p class="num">%d</p>'
            '<p class="big">%s</p><p class="sub">%s</p>'
            '<p><a class="tap" href="#t-%d">what it rests on</a></p></div>'
            % (i + 1, esc(it["title"]), esc(it["why"]), i + 1))
    if len(items) > NEXT_ASKED:
        body.append('<p class="legend">(+%d more named in %s, not shown of '
                    '%d.)</p>' % (len(items) - NEXT_ASKED, esc(PRIORITIES),
                                  len(items)))
    return "".join(body)


def foot_html(r3):
    links = "".join('<a href="%s">%s</a>' % (esc(h), esc(t))
                    for h, t in SIBLINGS)
    src = ("The next three are chosen by %s, last on %s, in one small file "
           "this page reads and nothing else does. Nothing here is scraped "
           "out of a log."
           % (r3.get("ruledBy") or NOTHING, r3.get("ruledOn") or NOTHING))
    return ('<p class="legend">%s</p><p class="foot">%s'
            '<a href="#about">how this page was made</a></p>'
            % (esc(src), links))


def typed_inventory(root):
    """THE TYPED STATUS BOARD, COUNTED AND DISARMED. It carries a status word a
    person types; it sets NO word on this page and never has. Counted behind
    the tap, labelled as typed, so the difference between what somebody wrote
    down and what a run measured is visible rather than quietly gone."""
    p = Path(root) / INVENTORY
    if not p.is_file():
        return {"present": False, "entries": 0, "words": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except ValueError:
        return {"present": True, "entries": 0, "words": {},
                "note": "did-not-parse"}
    ent = data if isinstance(data, list) else (data.get("entries")
                                               or data.get("systems") or [])
    words = {}
    for e in ent:
        w = str(e.get("status", "(none)"))
        words[w] = words.get(w, 0) + 1
    return {"present": True, "entries": len(ent), "words": words}


def build(root, now, out_path=None, served=None):
    """The whole page and the model behind it."""
    root = Path(root)
    rows, r1 = find_runnables(root)
    probe, probe_reading = visual_probe(root)
    pb = playable_build(root)
    code = code_only(root)
    items, r3 = next_three(root)
    ladder, r4 = ladder_rungs(root, items, r3)
    commit = (GLANCE.git(root, "rev-parse", "--short", "HEAD") or NOTHING)

    # THE PICTURE IS ENCODED AGAINST WHAT THE REST OF THE PAGE LEAVES, so the
    # budget is measured rather than guessed: the page is assembled once with
    # no picture, its bytes are the shell, and the frame gets what is left
    # under the cap. Both numbers print on the done line.
    shell_probe = PAGE % (css(), "")
    shell = len(shell_probe.encode("utf-8")) + 8000   # sheets and cards
    picture = read_picture(root, probe_reading, PAGE_BYTE_CAP - shell)
    areas, r2 = area_states(root, shown_frame=picture["rel"]
                            if picture["shown"] else None)

    things = list(rows)
    things.append({"name": (probe["name"] if probe else "the-unreal-probe"),
                   "category": CAT_PROBE,
                   "avail": probe["avail"] if probe else NOTHING})
    things.append({"name": "a-playable-game-build", "category": CAT_PLAYABLE,
                   "avail": NOTHING})
    things.append({"name": "the-source-in-this-checkout",
                   "category": CAT_CODE, "avail": AVAIL_UNVERIFIED})
    q1 = {"probe": probe, "probeReading": probe_reading, "playable": pb,
          "code": code, "things": len(things),
          "probeHours": hours_since(probe["when"], now) if probe else None,
          "ran": sum(1 for t in things if t["avail"] == AVAIL_RAN),
          "unverified": sum(1 for t in things
                            if t["avail"] == AVAIL_UNVERIFIED),
          "notCommitted": sum(1 for t in things
                              if t["avail"] == AVAIL_UNCOMMITTED),
          "unmeasuredAvail": sum(1 for t in things if t["avail"] == NOTHING)}

    fields = material_fields(things, areas, items)
    dig = digest_of(fields)
    prev_f = previous_fields(out_path) if out_path else None
    prev_d = previous_digest(out_path) if out_path else None
    groups = changed_groups(fields, prev_f)
    change = ("nothing-measured" if prev_d is None
              else ("yes" if prev_d != dig else "no"))

    opts = dict({"attempt": False, "url": None, "timeout": SERVED_TIMEOUT_SEC,
                 "fetch": None}, **(served or {}))
    url, how = (opts["url"], "supplied-by-the-caller") if opts["url"] \
        else pages_url(root)
    srv = served_reading(url, how, attempt=opts["attempt"],
                         timeout=opts["timeout"], fetch=opts["fetch"],
                         expect_digest=dig)

    flow, geo = flow_svg(areas)
    model = {"rows": rows, "r1": r1, "areas": areas, "r2": r2,
             "items": items, "r3": r3, "commit": commit, "fields": fields,
             "digest": dig, "prevDigest": prev_d, "change": change,
             "changedGroups": groups, "q1": q1, "things": things,
             "served": srv, "picture": picture, "geo": geo,
             "shellBytes": shell,
             "ladder": dict(r4, rungs=ladder)}
    detail = [
        "picture=%s pictureShown=%s pictureB64Bytes=%d/%d-budget "
        "pictureSourceBytes=%d pictureQuality=%s resizer=%s pictureFrom=%s"
        % (picture["rel"] or NOTHING.replace(" ", "-"),
           "yes" if picture["shown"] else "no", picture["bytes"],
           picture["budget"], picture["sourceBytes"],
           picture["quality"] if picture["quality"] is not None
           else NOTHING.replace(" ", "-"), picture["resizer"], UE_VERDICT),
        "textTools=%d/%d-bat-file(s)-in-this-checkout-root onFirstScreen=%d/%d "
        "unknown=%d/%d batsElsewhere=%d/%d-in-this-checkout gitAnswered=%s "
        "scanScope=this-checkout/never-his-pc"
        % (r1["text"], r1["found"], r1["onFirstScreen"], r1["found"],
           r1["unknown"], r1["found"], r1["batsNotAtRoot"], r1["batsAnywhere"],
           "yes" if r1["gitAnswered"] else "no"),
        "visualProbe=%s probeFramesWrote=%s probeCommit=%s probeAgeHours=%s "
        "probeEvidence=%s probeRunsOn=%s probeSentinel=%s probePackagedDir=%s"
        % ("found" if probe else NOTHING.replace(" ", "-"),
           (probe["wrote"] if probe else NOTHING.replace(" ", "-")),
           (probe["sha"] if probe else NOTHING.replace(" ", "-")),
           ("%d%s" % (q1["probeHours"],
                      "" if (q1["probeHours"] or 0) >= 0
                      else "/stamped-ahead-of-this-runs-clock")
            if probe is not None and q1["probeHours"] is not None
            else NOTHING.replace(" ", "-")),
           UE_VERDICT, (probe["runsOn"] if probe else NOTHING.replace(" ", "-")),
           (probe["sentinel"] if probe else NOTHING.replace(" ", "-")),
           (probe["packagedDir"] if probe and probe["packagedDir"]
            else NOTHING.replace(" ", "-"))),
        # THE SOURCE SCAN behind "nobody can play it", with its denominator.
        "playerMarkersFound=%d/%d-asked probeSourceFilesWalked=%d "
        "borrowsFirstPlayerController=%d ofWhichOnlyAimTheCamera=%d markers=%s"
        % (r2["scan"]["markersFound"], r2["scan"]["markersAsked"],
           r2["scan"]["filesWalked"], r2["scan"]["borrowsController"],
           r2["scan"]["andOnlyAimsTheCamera"],
           "/".join("%s.%d" % (k, v)
                    for k, v in sorted(r2["scan"]["markers"].items()))),
        "playableBuildInThisCheckout=%d/%d-file(s)-walked "
        "playableKeysPresent=%d/%d-asked playableKeys=%s "
        "aboutHisPc=not-derivable-from-a-checkout"
        % (pb["exesHere"], pb["filesWalked"], pb["keysFound"],
           pb["keysAsked"], "/".join(pb["keys"])),
        "codeInThisCheckout=%d-cs-file(s) dotnetProjects=%d consoleOf=%d/%d "
        "engineProject=%s packagedPlayers=%d/%d-file(s)-walked"
        % (code["csFiles"], code["projects"], code["console"],
           code["projects"], "yes" if code["enginePresent"] else "no",
           code["exesHere"], code["filesWalked"]),
        "availRan=%d/%d-things availUnverified=%d/%d availNotCommitted=%d/%d "
        "availNothingMeasured=%d/%d denominatorIs=things-you-could-run"
        % (q1["ran"], q1["things"], q1["unverified"], q1["things"],
           q1["notCommitted"], q1["things"], q1["unmeasuredAvail"],
           q1["things"]),
        "areas=%d nothingMeasured=%d/%d seenNotMeasured=%d/%d notStarted=%d/%d "
        "failing=%d/%d unheard=%d/%d heard=%d/%d harnessOnly=%d/%d"
        % (r2["areas"], r2["nothingMeasured"], r2["areas"],
           r2["seenNotMeasured"], r2["areas"], r2["notStarted"], r2["areas"],
           r2["failing"], r2["areas"], r2["unheard"], r2["areas"],
           r2["heard"], r2["areas"], r2["harnessOnly"], r2["areas"]),
        "gatesMapped=%d/%d-in-%s gateLines=%d/last-wins"
        % (r2["gatesMapped"], r2["gatesInVerdict"], SIM_VERDICT,
           r2["gateLines"]),
        "gatesUnmapped=%s%s"
        % ("/".join(r2["unmapped"][:UNMAPPED_SHOWN]) or NOTHING.replace(" ", "-"),
           (" (+%d-more-not-shown-of-%d)"
            % (len(r2["unmapped"]) - UNMAPPED_SHOWN, len(r2["unmapped"])))
           if len(r2["unmapped"]) > UNMAPPED_SHOWN else ""),
        "simVerdictCommit=%s ueVerdictCommit=%s pageCommit=%s"
        % (r2["simSha"] or NOTHING.replace(" ", "-"),
           r2["ueSha"] or NOTHING.replace(" ", "-"), commit),
        # THE NEXT THREE, AND WHERE THEY CAME FROM. nextSource is the only
        # file this page reads for them; nextRefused is how many named items
        # were stale enough to be refused rather than shown.
        # doneNamed IS WHAT THE FILE CLAIMS, not what this run proved: an
        # absent `done` array reads 0/absent, which is how a plan that has
        # finished nothing is told apart from a plan whose done list this run
        # could not read. What was PROVED is on the ladder line below.
        "nextSource=%s nextPresent=%s nextNamed=%d/%d-asked nextShown=%d "
        "nextRefused=%d doneNamed=%d/%s ruledBy=%s ruledOn=%s "
        "nowMdHeadingParser=deleted"
        % (PRIORITIES, "yes" if r3.get("present") else "no", r3.get("named", 0),
           NEXT_ASKED, r3.get("shown", 0), r3.get("refused", 0),
           r3.get("doneNamed", 0), r3.get("doneWord", "absent"),
           re.sub(r"\s+", "-", str(r3.get("ruledBy") or NOTHING)),
           r3.get("ruledOn") or NOTHING.replace(" ", "-")),
        # THE LADDER, RULING 3 AND THE done ARRAY OF 2026-09-08. WHOLE-RUN
        # NUMBERS, all of them: currentNum is the rung this run highlighted,
        # staleCount/total is a real N of M (every rung's refused flag was
        # read), ladderDoneCount is done rungs DRAWN over done steps CLAIMED
        # by the file, and ladderDoneProven is how many of those claims had
        # every one of their evidence keys found again by this run, with the
        # key pair count beside it. Per-step evidence prints on that step's
        # own map: done<N>= line, never here: one moment per line.
        "ladderTotal=%d ladderStepsShown=%d/%d-named ladderCurrentNum=%s "
        "ladderGoalState=%s ladderGoalRefused=%s ladderStaleCount=%d/%d "
        "ladderDoneCount=%d/%d-claimed ladderDoneProven=%d/%d "
        "ladderDoneKeys=%d/%d-found ladderRefused=%s ladderRefusedWhy=%s"
        % (r4["total"], r4["stepsShown"], r4["stepsNamedTotal"],
           r4["currentNum"] if r4["currentNum"] else NOTHING.replace(" ", "-"),
           r4["goalState"], "yes" if r4["goalRefused"] else "no",
           r4["staleCount"], r4["total"],
           r4["doneShown"], r4["doneClaimed"], r4["doneProven"],
           r4["doneClaimed"], r4["doneKeysFound"], r4["doneKeysAsked"],
           "yes" if r4["refused"] else "no", r4["refusedWhy"]),
        "flowNodes=%d/%d-areas svgHeightPx=%d boxWidthPx=%d textWidthPx=%d "
        "widestLineChars=%d atFontPx=%d wrapModel=avg-advance-0.5em"
        % (geo["nodes"], r2["areas"], geo["svgHeightPx"], geo["boxWidthPx"],
           geo["textWidthPx"], geo["widestChars"], geo["widestFontPx"]),
        "servedPageRequested=%s servedPageResult=%s servedStatus=%s "
        "servedBytes=%d servedDigest=%s..localDigest=%s servedUrl=%s "
        "servedUrlFrom=%s servedFetcher=%s servedReason=%s"
        % ("yes" if srv["attempted"] else "no",
           srv["result"].replace(" ", "-"),
           srv["status"] if srv["status"] is not None
           else NOTHING.replace(" ", "-"), srv["bytes"],
           srv["digest"] or NOTHING.replace(" ", "-"), dig,
           srv["url"] or NOTHING.replace(" ", "-"),
           re.sub(r"\s+", "-", srv["how"]),
           srv["fetcher"] or NOTHING.replace(" ", "-"),
           re.sub(r"\s+", "-", srv["reason"]) or "none"),
        "mapDigest=%s mapDigestPrev=%s mapMaterialChange=%s mapChangedFields=%s"
        % (dig, prev_d or NOTHING.replace(" ", "-"), change,
           ("/".join(groups) if groups else "none") if groups is not None
           else NOTHING.replace(" ", "-")),
    ]
    inv = typed_inventory(root)
    try:
        qc = load_queue_check().count_queue(root)
    except Exception:                                            # noqa: BLE001
        qc = None
    q_counts = ((qc["ready"], qc["blocked"], qc["done"]) if qc
                else (NOTHING.replace(" ", "-"),) * 3)
    detail.append(
        "queueReady=%s queueBlocked=%s queueDone=%s countedBy=tools/"
        "queue-check.py/count_queue chosenBy=%s"
        % (q_counts + (PRIORITIES,)))
    detail.append(
        "typedInventory=%s entriesTyped=%d words=%s setsNoWordOnThisPage=true"
        % (INVENTORY, inv["entries"],
           "/".join("%s.%d" % (w, n) for w, n in sorted(inv["words"].items()))
           or NOTHING.replace(" ", "-")))
    model["inventory"] = inv
    model["detail"] = detail

    sheets = "".join([area_sheet(a, areas, r2) for a in areas]
                     + [task_sheet(i + 1, it)
                        for i, it in enumerate(items[:NEXT_ASKED])
                        if not it["refused"]]
                     + [goal_sheet(r4)]
                     + [tools_sheet(rows, r1), about_sheet(model, now, detail)])
    body = "\n".join([
        # RULING 3: THE LADDER IS THE FIRST THING ON THE PAGE, above even the
        # top bar and "what exists now" below it. Everything that used to be
        # the first screen stays, unmoved, beneath it.
        LADDER_START, ladder_html(ladder, r4), LADDER_END,
        '<div class="top"><b>LEDGER</b><span>%s at %s UTC</span></div>'
        % (esc(commit), esc(now.strftime("%Y-%m-%d %H:%M"))),
        now_html(picture, probe, q1["probeHours"], areas),
        '<h2>what you can run, and what to press</h2>',
        run_html(probe, pb, rows, r1, r2["scan"],
                 tail=milestone_html(r3)),
        '<h2>the game, and the path through it</h2>',
        '<p class="legend">Read it downward: you act, the town sees it, it '
        'talks, and you hear the result. Each box says its state in words as '
        'well as colour. Tap one for its evidence.</p>',
        flow,
        '<h2>the next three, in order</h2>',
        next_html(items, r3),
        foot_html(r3),
        sheets,
        "<!-- Generated by %s at %s UTC -->"
        % (TOOL, now.strftime("%Y-%m-%d %H:%M")),
        "<!-- mapDigest=%s mapFields=%s -->" % (dig, encode_fields(fields)),
    ])
    return PAGE % (css(), body), model


# ---------------------------------------------------------------------------
# THE CHECKS. The container has a browser and somebody looks at the page, which
# is what accepts the design; these are the things a FILE can be asked, and
# they are the ones that earn their place. Each returns (name, ok, printed) and
# every one ships its denominator.
#
# WHAT WAS DROPPED, 2026-09-07, and why. threeQuestions (h2 1/2/3 in order),
# aboveFold (a modelled pixel height of a wall of text), fiveCategories (five
# prose headings) and ruleOnPage (a paragraph of derivation prose) all asserted
# the shape of the page Jafar rejected. A check that pins a rejected design is
# a ratchet against fixing it. The fold is now verified by looking at a
# screenshot at 390x844, which is what it always should have been.
# ---------------------------------------------------------------------------

def check_first_screen(page, model):
    """THE SCREEN BELOW THE LADDER ANSWERS THREE THINGS, IN ORDER, and the
    picture comes before anything that competes with it. RULING 3 put a
    fourth, higher thing above all of it (check_ladder_at_top below checks
    that one); this check is unchanged because it only asserts the RELATIVE
    order of the three marks that were already here, which the ladder does
    not disturb. Order is a fact about the bytes; the height is a fact about
    a browser and is checked by looking."""
    marks = [("whatExistsNow", page.find('class="now"')),
             ("thePicture", max(page.find('class="shot"'),
                                page.find('class="noshot"'))),
             ("whatToPress", page.find("what you can run, and what to press")),
             ("theMilestone", page.find("the next milestone")),
             ("theFlow", page.find('class="flow"'))]
    at = [i for _, i in marks]
    missing = [n for n, i in marks if i < 0]
    ordered = all(a < b for a, b in zip(at, at[1:])) if not missing else False
    return ("firstScreen", not missing and ordered,
            "firstScreenParts=%d/%d inOrder=%s missing=%s order=%s"
            % (len(marks) - len(missing), len(marks),
               "yes" if ordered else "no", "/".join(missing) or "none",
               "/".join(n for n, _ in marks)))


def check_picture(page, model):
    """THE FRAME IS SHOWN, NOT LINKED, or the page says it could not be shown.

    A page that silently drops the picture looks like a page that loaded
    badly, so the failure has words. This does not bite when a resizer is
    absent: that is a fact about the environment and it is reported in the
    reading."""
    pic = model["picture"]
    inline = ('src="data:image/' in page)
    said = pic["shown"] or (NOTHING in page)
    named = (pic["rel"] or "") in page if pic["rel"] else True
    return ("picture", (inline == pic["shown"]) and said and named,
            "pictureShown=%s inlineDataUri=%s frame=%s b64Bytes=%d/%d-budget "
            "resizer=%s namedOnPage=%s"
            % ("yes" if pic["shown"] else "no", "yes" if inline else "no",
               pic["rel"] or NOTHING.replace(" ", "-"), pic["bytes"],
               pic["budget"], pic["resizer"], "yes" if named else "MISSING"))


def check_probe_is_not_a_game(page, model):
    """THE ONE DISTINCTION THIS PAGE EXISTS TO KEEP. An automated probe that
    renders offscreen and exits may never be offered as something a person is
    currently playing. THE SENTENCE IS CONDITIONAL ON THE LIVE SCAN NOW
    (see run_html): a FIXED string is exactly the fault that let this read
    "no character, no pawn, no game mode, no player start" for a day after a
    character, a game mode, input binding and a player start all compiled
    (run 28), so this reads which sentence today's scan calls for and
    requires that one, and separately forbids the old absolute claim once any
    marker exists."""
    scan = model["r2"]["scan"]
    wanted = ("no character, no pawn, no game mode, no player start"
              if scan["markersFound"] == 0 else "nobody at the controls")
    said = wanted in page
    stale_absolute = ("no character, no pawn, no game mode, no player start"
                      in page and scan["markersFound"] > 0)
    return ("probeIsNotAGame",
            (said and not stale_absolute) or not model["q1"]["probe"],
            "playerMarkersFound=%d/%d-asked wantedSentence=%s "
            "wantedSentenceOnPage=%s staleAbsoluteClaimOnPage=%s"
            % (scan["markersFound"], scan["markersAsked"], wanted,
               "yes" if said else "MISSING",
               "yes" if stale_absolute else "no"))


def check_player_control_matches_scan(page, model):
    """A GUARD ADDED AFTER A DECAYED CLAIM SHIPPED, 2026-09-07: this area's
    word went from an honest "not started" to a false "runs in text only" the
    day player_markers() first found something, because the word was only
    ever tested at found==0. This reads TODAY'S LIVE SCAN, not a frozen
    fixture, and requires both that the area's word is the one the live scan
    calls for and that the marker fraction printed on the page is the live
    one, so it bites BOTH if the code disappears again (a regression) and if
    the page's text and the scan ever disagree (a stale claim), which is
    exactly the fault this check exists to catch."""
    ctrl = next(a for a in model["areas"] if a["key"] == "player-control")
    scan = model["r2"]["scan"]
    found = scan["markersFound"]
    if found == 0:
        wanted = WORD_NOT_STARTED
    elif scan["compiled"]:
        wanted = WORD_BUILT
    else:
        wanted = WORD_UNPROVEN
    m = re.search(r"(\d+) of (\d+) marker\(s\) of a controllable character",
                  page)
    printed = (int(m.group(1)), int(m.group(2))) if m else None
    matches_scan = printed == (found, scan["markersAsked"])
    return ("playerControlMatchesScan",
            ctrl["word"] == wanted and matches_scan,
            "areaWord=%s wantedFromLiveScan=%s printedMarkers=%s "
            "liveMarkers=%d/%d-asked matchesScan=%s compiled=%s"
            % (ctrl["word"], wanted,
               "%s/%s" % printed if printed else NOTHING.replace(" ", "-"),
               found, scan["markersAsked"],
               "yes" if matches_scan else "no",
               "yes" if scan["compiled"] else "no"))


def check_every_area_spoken(page, model):
    """Every node prints a word, colour is never the only signal, and an area
    whose word is nothing measured prints those words rather than a gap."""
    n = len(model["areas"])
    on = sum(1 for a in model["areas"]
             if ('>%s<' % html.escape(a["word"].upper(), quote=True)) in page)
    silent = [a["key"] for a in model["areas"] if not a["why"]]
    classed = len(re.findall(r'class="s-[a-z]+"', page))
    return ("areasSpoken", on == n and not silent,
            "areaWordsAsTextOnPage=%d/%d colourClassesDrawn=%d "
            "nothingMeasured=%d/%d seenNotMeasured=%d/%d silent=%d"
            % (on, n, classed, model["r2"]["nothingMeasured"], n,
               model["r2"]["seenNotMeasured"], n, len(silent)))


AREA_SHEET_RX = 'id="a-%s">(.*?)</section>'


def check_no_comforting_bar(page, model):
    """THE RULE THE STREET AND THE MEMORY SWEEP BOTH PAID FOR. An area with no
    committed answer may not carry a health word in its own sheet, and its
    readings must be labelled as not answering. An area whose audibility
    fraction is 0 of N must print that fraction: queue 136 found this page
    reading HARNESS ONLY over lieHeard=0/90.

    THE SHEET IS FOUND BY ITS OWN id and never by a character window: the
    first draft of the old check read 900 characters forward, ran into the next
    area's row, and reported the street carrying a word that belonged to the
    people."""
    bad, examined = [], 0
    for a in model["areas"]:
        unanswered = a["word"] in (WORD_NOTHING, WORD_SEEN)
        zero_heard = a["heardNum"] == 0 and a["heardDen"]
        if not (unanswered or zero_heard):
            continue
        examined += 1
        m = re.search(AREA_SHEET_RX % re.escape(html.escape(a["key"],
                                                            quote=True)),
                      page, re.S)
        if not m:
            bad.append(a["key"] + "/sheet-not-found")
            continue
        sheet = m.group(1)
        if unanswered and (WORD_HARNESS in sheet or WORD_PLAYABLE in sheet
                           or WORD_HEARD in sheet):
            bad.append(a["key"] + "/health-word-in-the-sheet")
        if unanswered and any(v is not None for _, v in a["readings"]) \
                and "do NOT answer it" not in sheet:
            bad.append(a["key"] + "/readings-not-labelled")
        if zero_heard:
            f, k, _w = a["audible"]
            if "%s=0/%d" % (k, a["heardDen"]) not in sheet:
                bad.append(a["key"] + "/zero-without-its-denominator")
    return ("noComfortingBar", not bad,
            "unansweredOrUnheardSheetsExamined=%d/%d-areas faults=%d%s"
            % (examined, len(model["areas"]), len(bad),
               "" if not bad else " (" + ",".join(bad) + ")"))


def check_ladder_at_top(page, model):
    """RULING 3, Jafar, 2026-09-07: the ladder is the first thing on the
    page, above even "what exists now". Order is a fact about the bytes: the
    ladder marker must sit immediately after the opening <body> tag (measured
    at 16 bytes on a real build, for "<body id=\"map\">\\n"), with nothing
    else rendered before it, and the existing top bar and "now" section must
    still follow it."""
    body_at = page.find("<body")
    lad = page.find(LADDER_START)
    top = page.find('class="top"')
    now = page.find('class="now"')
    ok = (body_at >= 0 and 0 <= lad - body_at <= 40
          and top > lad and (now < 0 or now > top))
    return ("ladderAtTop", ok,
            "bodyTagAt=%d ladderMarkerAt=%d bytesBetween=%d/40-allowed "
            "topBarAt=%d nowSectionAt=%d aboveTop=%s"
            % (body_at, lad, lad - body_at, top, now, "yes" if ok else "no"))


def check_ladder_step_count(page, model):
    """"STEP N OF M" ON THE PAGE MATCHES WHAT THIS RUN COMPUTED, or the ladder
    is refused and the page says so instead of a fabricated count. REFUSED,
    NOT JUST goalRefused: since 2026-09-08 an unprovable done rung takes the
    whole ladder down the same way a finished goal does."""
    lad = ladder_slice(page)
    r = model["ladder"]
    if r["refused"]:
        ok = "LADDER IS STALE" in lad
        return ("ladderStepCount", ok,
                "ladderRefusedBy=%s staleBannerShown=%s"
                % (r["refusedBy"], "yes" if ok else "MISSING"))
    if r["currentNum"] is None:
        ok = "NO CURRENT STEP" in lad
        return ("ladderStepCount", ok,
                "currentNum=none noCurrentStepWordingShown=%s"
                % ("yes" if ok else "MISSING"))
    m = re.search(r"STEP (\d+) OF (\d+)", lad)
    ok = bool(m) and int(m.group(1)) == r["currentNum"] \
        and int(m.group(2)) == r["total"]
    return ("ladderStepCount", ok,
            "onPage=%s computedCurrentOfTotal=%s/%s"
            % ("/".join(m.groups()) if m else NOTHING.replace(" ", "-"),
               r["currentNum"], r["total"]))


def check_ladder_done_not_invented(page, model):
    """RULING 3, verbatim: "if nothing in the repository can currently prove
    a step is done then the ladder must say so in words rather than showing
    a green tick nobody measured." Checked on the ladder's own bytes, and a
    literal tick glyph is exactly the invented progress this bites on.

    THE WORDING CLAUSE IS CONDITIONAL SINCE 2026-09-08, and only that clause
    moved. With no done step named, the ladder must still say the words
    nothing measured, so an empty plan cannot read as a clean one. With done
    steps named, "nothing measured" would be the false sentence instead, so
    what is required there is the count with its denominator and every rung
    PROVEN: doneShown must equal doneClaimed and doneProven, or a claim this
    run could not verify would be standing on the ladder as a number. Either
    way a tick glyph is refused."""
    lad = ladder_slice(page)
    r = model["ladder"]
    if r["refused"]:
        return ("ladderDoneHonest", True, "ladder refused; nothing to check")
    said = NOTHING in lad.lower()
    ticks = lad.count("✓")
    shown, claimed, proven = r["doneShown"], r["doneClaimed"], r["doneProven"]
    if shown == 0:
        good, need = said, "the-words-%s" % NOTHING.replace(" ", "-")
    else:
        good = (shown == claimed == proven
                and "%d of %d rung(s)" % (shown, r["total"]) in lad)
        need = "count-with-denominator-and-every-rung-proven"
    return ("ladderDoneHonest", good and ticks == 0,
            "doneShownOnLadder=%d/%d-claimed doneProven=%d/%d-claimed "
            "requiredHere=%s nothingMeasuredWordingOnLadder=%s "
            "invertedTickGlyphsOnLadder=%d/0-allowed"
            % (shown, claimed, proven, claimed, need,
               "yes" if said else "MISSING", ticks))


def check_ladder_no_raw_content(page, model):
    """PHONE FIRST: no raw repository path and no gate count in the ladder's
    own bytes. Both are one tap away in the sheets this run already builds,
    never on the face RULING 3 asked to be readable at arm's length."""
    lad = ladder_slice(page)
    paths = re.findall(r"\bproduction/\S+", lad)
    gates = re.findall(r"\bgate", lad, re.I)
    return ("ladderNoRawContent", not paths and not gates,
            "rawPathsInLadder=%d gateWordsInLadder=%d bytesExamined=%d"
            % (len(paths), len(gates), len(lad)))


def check_ladder_stale_rungs_say_so(page, model):
    """Every rung this run could not verify says so, never CURRENT or NEXT
    borrowed by default. Counted, not just found once: one stale tag on a
    page with three stale rungs is two rungs lying by omission."""
    lad = ladder_slice(page)
    r = model["ladder"]
    if r["refused"]:
        return ("ladderStaleRungsSaySo", True, "ladder refused; nothing to "
                "check inside it")
    tags = lad.count("STATE NOT PROVEN")
    return ("ladderStaleRungsSaySo", tags == r["staleCount"],
            "staleRungsInModel=%d staleTagsOnLadder=%d/%d-needed"
            % (r["staleCount"], tags, r["staleCount"]))


def check_next_three(page, model):
    """THREE SLOTS, FROM ONE SOURCE, AND NO STALE ITEM AS A TASK.

    The refusal is the half a file cannot enforce on its own: an item whose
    queue file is done renders as a stale entry and this bites, so the page
    goes red rather than quietly offering finished work."""
    slots = len(re.findall(r'class="num">(\d)</p>', page))
    refused = model["r3"].get("refused", 0)
    sourced = PRIORITIES in page
    return ("nextThree", slots == NEXT_ASKED and refused == 0 and sourced,
            "slots=%d/%d-asked namedIn=%s named=%d shown=%d refusedAsStale=%d "
            "sourceOnPage=%s parserDeleted=production/NOW.md-heading-parser"
            % (slots, NEXT_ASKED, PRIORITIES, model["r3"].get("named", 0),
               model["r3"].get("shown", 0), refused,
               "yes" if sourced else "MISSING"))


def check_one_priority_source(page, model):
    """ONE SOURCE, AND THE PAGE NAMES IT. The failure this replaces is a page
    that derived a plan from a log; the guard is that the only file named as
    the source of the next three is the small one, and that nothing on the page
    claims NOW.md chooses them."""
    names_priorities = PRIORITIES in page
    names_now = "production/NOW.md" in page
    return ("onePrioritySource", names_priorities and not names_now,
            "prioritySourceNamed=%s nowMdNamedAsASource=%s "
            "sourcesForTheNextThree=1/1"
            % ("yes" if names_priorities else "MISSING",
               "yes-WHICH-IS-THE-FAULT" if names_now else "no"))


def check_material_rule(page, model):
    """What counts as a material change is stated where he can read it, and the
    digest tools/map-notify.py reads out of the SERVED page is in the bytes."""
    stated = MATERIAL_RULE[:60] in page
    dig = bool(DIGEST_RX.search(page))
    fields = decode_fields(page) is not None
    return ("materialRule", stated and dig and fields,
            "materialRuleOnPage=%s mapDigestInBytes=%s mapFieldsDecodable=%s "
            "change=%s"
            % ("yes" if stated else "MISSING", "yes" if dig else "MISSING",
               "yes" if fields else "MISSING", model["change"]))


def check_links(page, model):
    """AT MOST THE LINKS THE REGISTER ALLOWS, and no repository markdown link:
    Jafar ruled those out of anything he reads."""
    hrefs = re.findall(r'href="([^"]+)"', page)
    allowed = {h for h, _ in SIBLINGS} | {"#about", "#map", "#tools"}
    bad = [h for h in hrefs
           if h not in allowed and not re.match(r"^#(a-|t-)", h)]
    md = [h for h in hrefs if h.endswith(".md")]
    return ("links", not bad and not md,
            "hrefsExamined=%d outsideTheAllowList=%d markdownLinks=%d%s"
            % (len(hrefs), len(bad), len(md),
               "" if not bad else " (" + ",".join(bad[:3]) + ")"))


def check_denominators(page, model):
    """EVERY ZERO SHIPS ITS DENOMINATOR, read off the rendered bytes. The zeros
    this page prints are the packaged builds in this checkout, the session keys,
    the player markers in the probe source and the audibility fractions, and
    every one is rendered as N of M inside the sentence naming what M counted."""
    pb = model["q1"]["playable"]
    scan = model["r2"]["scan"]
    exe_zero = "0 of %d file(s) walked here" % pb["filesWalked"]
    key_zero = "%d of %d key(s) that would report" % (pb["keysFound"],
                                                      pb["keysAsked"])
    marker_zero = "%d of %d marker(s)" % (scan["markersFound"],
                                          scan["markersAsked"])
    heard = [a for a in model["areas"] if a["heardNum"] == 0 and a["heardDen"]]
    heard_ok = all("=0/%d" % a["heardDen"] in page for a in heard)
    pairs = re.findall(r"(\d+) of (\d+)", page) + re.findall(r"=(\d+)/(\d+)",
                                                             page)
    ok = (exe_zero in page and key_zero in page and marker_zero in page
          and heard_ok and len(pairs) >= 4)
    return ("denominators", ok,
            "nOfMPairs=%d packagedZero=%s sessionKeyZero=%s playerMarkerZero=%s "
            "audibilityZerosWithDenominator=%d/%d failing=%d/%d"
            % (len(pairs), "yes" if exe_zero in page else "MISSING",
               "yes" if key_zero in page else "MISSING",
               "yes" if marker_zero in page else "MISSING",
               sum(1 for a in heard if "=0/%d" % a["heardDen"] in page),
               len(heard), model["r2"]["failing"], model["r2"]["areas"]))


SENTENCE_SPLIT_RX = re.compile(r"(?<=[.!?])\s+")


def check_no_absence_claim(page, model):
    """THE CHECK JAFAR'S CORRECTION PAID FOR, 2026-09-06. This page is
    generated from a CHECKOUT: a scan here can say a thing is not committed in
    this clone, and it cannot say the thing does not exist. The previous page
    translated one into the other and told him nothing was playable while a
    packaged Unreal probe was writing frames on his PC that same day. So each
    claim shape must carry a scope qualifier IN THE SAME SENTENCE, and the
    denominator is the phrases scanned and the sentences they were scanned
    in."""
    text = re.sub(r"<[^>]+>", " ", page)
    text = re.sub(r"\s+", " ", text)
    sentences = SENTENCE_SPLIT_RX.split(text)
    hits, unqualified = 0, []
    for s in sentences:
        low = s.lower()
        for phrase in ABSENCE_CLAIMS:
            if phrase in low:
                hits += 1
                if not any(q in low for q in CHECKOUT_QUALIFIERS):
                    unqualified.append(phrase.replace(" ", "-"))
    return ("noAbsenceClaim", not unqualified,
            "absencePhrasesScanned=%d/%d-shapes sentencesScanned=%d hits=%d "
            "unqualified=%d%s"
            % (len(ABSENCE_CLAIMS), len(ABSENCE_CLAIMS), len(sentences), hits,
               len(unqualified),
               "" if not unqualified else " (" + ",".join(unqualified[:3]) + ")"))


ALLOWED_AVAIL = (AVAIL_RAN, AVAIL_UNVERIFIED, AVAIL_UNCOMMITTED,
                 NOTHING.replace(" ", "-"))


def check_availability_words(page, model):
    """Every block that offers something prints an availability, and it is one
    of the four words. "yes" is not among them on purpose: this container
    cannot earn it."""
    vals = re.findall(r'data-avail="([^"]+)"', page)
    bad = sorted(set(v for v in vals if v not in ALLOWED_AVAIL))
    return ("availabilityWords", bool(vals) and not bad,
            "availAttrs=%d thingsCounted=%d allowedWords=%d bad=%d%s"
            % (len(vals), model["q1"]["things"], len(ALLOWED_AVAIL), len(bad),
               "" if not bad else " (" + ",".join(bad[:3]) + ")"))


def check_served(page, model):
    """THE PUBLISHED PAGE, not the bytes this run wrote. It bites on exactly
    one thing, and it is the thing only a request can see: the URL answered 2xx
    with a page that is NOT this map. A request that did not complete reads
    nothing measured with the reason; a 404 is reported and does not bite,
    because this URL is derived by convention."""
    s = model["served"]
    bad = (s["measured"] and s["status"] and 200 <= s["status"] < 300
           and not s["marker"])
    return ("servedPage", not bad,
            "servedPageRequested=%s servedPageResult=%s servedStatus=%s "
            "servedMarker=%s servedDigest=%s..localDigest=%s"
            % ("yes" if s["attempted"] else "no",
               s["result"].replace(" ", "-"),
               s["status"] if s["status"] is not None
               else NOTHING.replace(" ", "-"),
               "yes" if s["marker"] else "no",
               s["digest"] or NOTHING.replace(" ", "-"), model["digest"]))


def check_cap_announced(page, model):
    """A cap that does not say it bit reads as a finding. The launcher list is
    the one capped list on this page."""
    bit = len(model["rows"]) > TOOLS_SHOWN
    said = "more not shown" in page
    return ("capAnnounced", (not bit) or said,
            "launchersListed=%d/%d cap=%d capBit=%s announced=%s"
            % (min(len(model["rows"]), TOOLS_SHOWN), len(model["rows"]),
               TOOLS_SHOWN, "yes" if bit else "no", "yes" if said else "no"))


def check_no_clipped_svg_text(page, model):
    """SVG DOES NOT WRAP AND CLIPS SILENTLY, which is one of the four faults
    named in the rejection. Two halves, and the second was added after a
    screenshot showed what the first could not see: the wrapped TITLE lines
    must fit the box, and every status PILL must be wide enough for its own
    uppercase word. The pill half caught nothing when it was written, because
    it was written from a rendered page where the letters were already
    outside the rounded rectangle."""
    geo = model["geo"]
    predicted = geo["widestChars"] * geo["widestFontPx"] * AVG_ADVANCE_EM
    pill_text = (len(geo["widestPillWord"]) * STATUS_PX * UPPER_ADVANCE_EM
                 + 2 * PILL_PAD_PX)
    ok = (predicted <= geo["textWidthPx"]
          and pill_text <= geo["widestPillPx"] + 0.5
          and geo["widestPillPx"] <= geo["textWidthPx"])
    return ("svgTextFits", ok,
            "widestTitlePx=%.0f/%d-box widestChars=%d atFontPx=%d "
            "widestPillWord=%s widestPillNeedsPx=%.0f/%d-drawn nodes=%d "
            "wrapModel=avg-advance-%.2fem pillModel=upper-advance-%.2fem"
            % (predicted, geo["textWidthPx"], geo["widestChars"],
               geo["widestFontPx"],
               geo["widestPillWord"].replace(" ", "-").replace(",", "") or
               NOTHING.replace(" ", "-"),
               pill_text, geo["widestPillPx"], geo["nodes"], AVG_ADVANCE_EM,
               UPPER_ADVANCE_EM))


PUBLISHER_MARKER = "LEDGER map"


def check_publisher_marker(page, model):
    """tools/publish-glance.py asserts this exact string is in the served bytes,
    which is how it tells the map from a second copy of the glance. Another
    tool's assertion about this page, checked from this side too rather than
    discovered when the publish step goes red."""
    n = page.count(PUBLISHER_MARKER)
    return ("publisherMarker", n >= 1,
            "publisherMarker=%d/1-needed-by-tools/publish-glance.py text=%s"
            % (n, PUBLISHER_MARKER.replace(" ", "-")))


THEME_RX = re.compile(r"@media \(prefers-color-scheme:\s*light\)\s*\{", re.I)


def check_theme(page, model):
    """Two halves: the page declares it handles both schemes, and it actually
    paints a light one. The declaration alone is what a dark-only page says."""
    declared = 'content="dark light"' in page or "color-scheme: dark light" in page
    block = THEME_RX.search(page)
    overrides = 0
    if block:
        depth, i = 0, block.end() - 1
        for j in range(i, len(page)):
            if page[j] == "{":
                depth += 1
            elif page[j] == "}":
                depth -= 1
                if depth == 0:
                    overrides = (page[i:j].count("background:")
                                 + page[i:j].count("color:")
                                 + page[i:j].count("fill:")
                                 + page[i:j].count("stroke:"))
                    break
    return ("themeAware", declared and overrides >= 8,
            "colorSchemeDeclared=%s lightOverrides=%d/8-needed"
            % ("yes" if declared else "MISSING", overrides))


def check_stamp(page, model):
    """The publisher reads the generator's own dated sentence out of the served
    bytes (tools/publish-glance.py GENERATED_RX), so it has to be there."""
    ok = bool(re.search(r"Generated by tools/map\.py at \d{4}-\d\d-\d\d "
                        r"\d\d:\d\d UTC", page))
    commit = model["commit"] in page
    return ("stamp", ok and commit,
            "generatedSentence=%s commitOnPage=%s/%s"
            % ("yes" if ok else "MISSING", "yes" if commit else "MISSING",
               model["commit"]))


def shared(fn):
    def wrapped(page, model):
        return fn(page)
    wrapped.__name__ = fn.__name__
    return wrapped


check_viewport = shared(GLANCE.check_viewport)
check_width = shared(GLANCE.check_width)
check_external = shared(GLANCE.check_external)
check_weight = shared(GLANCE.check_weight)
check_formatting = shared(GLANCE.check_formatting)
check_secrets = shared(GLANCE.check_secrets)

CHECKS = (check_ladder_at_top, check_ladder_step_count,
          check_ladder_done_not_invented, check_ladder_no_raw_content,
          check_ladder_stale_rungs_say_so,
          check_first_screen, check_picture, check_probe_is_not_a_game,
          check_player_control_matches_scan,
          check_every_area_spoken, check_no_comforting_bar, check_next_three,
          check_one_priority_source, check_material_rule, check_links,
          check_denominators, check_no_absence_claim, check_availability_words,
          check_served, check_cap_announced, check_no_clipped_svg_text,
          check_theme, check_stamp, check_publisher_marker,
          check_viewport, check_width, check_external, check_weight,
          check_formatting, check_secrets)


def run_checks(page, model):
    return [f(page, model) for f in CHECKS]


# ---------------------------------------------------------------------------
# SELFTEST, ACCEPTING CASE FIRST. The accepting side is the one that goes
# unrun, so it is first and it runs against the LIVE repository, which is the
# only fixture that can go stale under us. Every rejecting fixture is
# synthetic, so doing the work this page asks for can never break the tool.
# ---------------------------------------------------------------------------

FIXTURE_BAT = """@echo off
title planted
REM ===================================================================
REM  A PLANTED FIXTURE. It exists only so the selftest has a runnable
REM  entry point of its own and never has to pin itself to a real one.
REM ===================================================================
%PY% "%REPO%\\tools\\planted.py"
"""
FIXTURE_VERDICT = """# Sim verdict abc1234 @1700000000
SimDirector: ALL GATES: ok knowledge | ok beats | ok places | ok actOne
"""
FIXTURE_PRIORITIES = json.dumps({
    "ruledBy": "a planted fixture", "ruledOn": "2026-01-02",
    "milestone": "a planted milestone",
    "next": [
        {"title": "the first planted thing", "why": "because the fixture says",
         "queue": "production/queue/901-planted-ready.md"},
        {"title": "the second planted thing", "why": "also the fixture",
         "queue": None},
    ]}, indent=1)
FIXTURE_STALE = json.dumps({
    "ruledBy": "a planted fixture", "ruledOn": "2026-01-02",
    "milestone": "a planted milestone",
    "next": [
        {"title": "a thing somebody already finished", "why": "planted",
         "queue": "production/queue/902-planted-done.md"},
    ]}, indent=1)
FIXTURE_QUEUE_READY = "line: planted\nstatus: READY 2026-01-02. Planted.\n"
FIXTURE_QUEUE_DONE = "line: planted\nstatus: DONE 2026-01-02. Planted.\n"
# THE DONE FIXTURES. The live plan is the accepting fixture for a REAL done
# step; these prove the same path, and then the three refusals, on files this
# test wrote. The evidence key planted here exists in no real file and the
# path is one no run writes, so doing the work this page asks for can neither
# satisfy nor break a rejecting fixture.
FIXTURE_EVIDENCE_REL = "production/planted-evidence.txt"
FIXTURE_EVIDENCE = ("# A planted verdict, written by the selftest.\n"
                    "plantedStatus=PROVEN plantedFrames=1/1\n")
FIXTURE_DONE_TITLE = "a planted thing already finished"


def _done_priorities(evidence, title=FIXTURE_DONE_TITLE):
    """FIXTURE_PRIORITIES with one `done` step carrying the evidence given,
    `done` before `next` as the ruling places it. ONE fixture builder for all
    four done cases: the accepting one and the three refusals differ by their
    evidence and their title, and by nothing else, which is what makes the
    difference between them readable."""
    out = {"done": [{"title": title, "why": "planted", "doneOn": "2026-01-02",
                     "queue": "production/queue/901-planted-ready.md",
                     "evidence": evidence}]}
    for k, v in json.loads(FIXTURE_PRIORITIES).items():
        out[k] = v
    return json.dumps(out, indent=1)


def _tree(files):
    import atexit
    import shutil
    import tempfile
    d = Path(tempfile.mkdtemp(prefix="map-"))
    atexit.register(shutil.rmtree, str(d), True)
    for rel, blob in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(blob, encoding="utf-8")
    return d


def load_publisher():
    """tools/publish-glance.py as a module, for its LOCAL SERVER fixture. The
    fetch under test is imported from the same file by served_reading, so there
    is one implementation of "request a URL" and one of "serve bytes for a
    test" in this repository, not two of each."""
    p = ROOT / "tools" / "publish-glance.py"
    spec = importlib.util.spec_from_file_location("publish_glance_fixture", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def selftest():
    passed, failed = 0, []
    now = datetime.datetime(2026, 9, 7, 12, 0, tzinfo=datetime.timezone.utc)
    NOWEB = {"attempt": False}

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s\n         got: %s" % (name, got))

    print("%s --selftest: ACCEPTING CASE FIRST, the live repository\n" % TOOL)
    page, model = build(ROOT, now, served=NOWEB)
    checks = run_checks(page, model)
    bad = [n for n, c, _ in checks if not c]
    ok("the live repository renders the page and every check passes "
       "(%d launcher(s), %d area(s), %d next item(s), %d check(s))"
       % (model["r1"]["found"], model["r2"]["areas"], model["r3"]["named"],
          len(checks)),
       model["r1"]["found"] >= 1 and not bad,
       "failed=%s" % (",".join(bad) or "none"))

    # THE PICTURE, which is the whole of the first answer.
    pic = model["picture"]
    ok("the street frame is chosen from the verdict's own shot lines and "
       "embedded inline (%s, %d bytes at quality %s)"
       % (pic["rel"], pic["bytes"], pic["quality"]),
       pic["shown"] and pic["rel"] == "production/d1-probe/ue-vign_camA_day.png"
       and 'src="data:image/jpeg;base64,' in page,
       "%s / shown=%s" % (pic["rel"], pic["shown"]))
    ok("and the page names the file and the commit the run stamped (%s on %s)"
       % (pic["rel"], model["r2"]["ueSha"]),
       pic["rel"] in page and (model["r2"]["ueSha"] or "zz") in page,
       model["r2"]["ueSha"])

    # THE STREET, which is the reading Jafar named as the page's worst failure.
    street = [a for a in model["areas"] if a["key"] == "street-and-its-look"][0]
    ok("the street reads '%s' and NOT '%s', because the frame is on the page "
       "while the keys are still absent" % (WORD_SEEN, NOTHING),
       street["word"] == WORD_SEEN,
       "%s / missing=%s" % (street["word"], street["missing"]))
    ok("and it still names both keys that would measure it, quadChroma and "
       "shotChromaExQuads, neither of which any run emits",
       all(k in page for k in ("quadChroma", "shotChromaExQuads"))
       and not key_present(ROOT, UE_VERDICT, "quadChroma")
       and not key_present(ROOT, UE_VERDICT, "shotChromaExQuads"),
       street["missing"])
    ok("and it says in the same breath what remains unverified",
       "What no run has measured" in street["why"], street["why"][:120])
    # AND THE COUPLING: no picture, no observation.
    _p2, m2b = build(ROOT, now, served=NOWEB)
    m2b["picture"]["shown"] = False
    areas_nopic, _r = area_states(ROOT, shown_frame=None)
    street2 = [a for a in areas_nopic if a["key"] == "street-and-its-look"][0]
    ok("and with the picture NOT shown the same area falls back to '%s', so "
       "the claim is coupled to the evidence the reader can see" % NOTHING,
       street2["word"] == WORD_NOTHING, street2["word"])

    # THE MEMORY AREA, which queue 136 filed against this page.
    mem = [a for a in model["areas"] if a["key"] == "people-and-their-memory"][0]
    ok("memory reads '%s' and not a health word, because lieHeard=%s/%s says "
       "nothing a player hears changes (%d of %d gates ok)"
       % (mem["word"], mem["heardNum"], mem["heardDen"], mem["gatesSeen"],
          mem["gatesNamed"]),
       mem["word"] == WORD_UNHEARD and mem["heardNum"] == 0,
       "%s heard=%s/%s" % (mem["word"], mem["heardNum"], mem["heardDen"]))
    conv = [a for a in model["areas"] if a["key"] == "conversation"][0]
    ok("and gossip reads '%s' from a different fraction in the same file "
       "(realPointed=%s/%s), so the two routes are not one number twice"
       % (conv["word"], conv["heardNum"], conv["heardDen"]),
       conv["word"] == WORD_HEARD and conv["heardNum"] > 0,
       "%s heard=%s/%s" % (conv["word"], conv["heardNum"], conv["heardDen"]))
    ctrl = [a for a in model["areas"] if a["key"] == "player-control"][0]
    cscan = ctrl["scan"]
    # NOT PINNED TO "not started": that word was RIGHT the day this was
    # written and WRONG the day run 28 compiled a character, a game mode,
    # input binding and a player start, because the branch below it (any
    # nonzero count read as "runs in text only") was never tested against a
    # real nonzero count. This computes what today's live scan calls for the
    # same way area_states() does, so the assertion tracks the honest word
    # instead of freezing the word that happened to be true once.
    wanted_word = (WORD_NOT_STARTED if cscan["markersFound"] == 0
                  else WORD_BUILT if cscan["compiled"] else WORD_UNPROVEN)
    ok("player control reads '%s' from the probe's own source: %d of %d "
       "marker(s) over %d file(s), compiled=%s"
       % (ctrl["word"], cscan["markersFound"], cscan["markersAsked"],
          cscan["filesWalked"], cscan["compiled"]),
       ctrl["word"] == wanted_word and cscan["filesWalked"] >= 5
       and "runs in text only" not in ctrl["word"],
       cscan)
    voice = [a for a in model["areas"] if a["key"] == "voice"][0]
    ok("voice says %s, because no gate in the verdict is a speech gate (%s)"
       % (NOTHING, voice["why"][:60]), voice["word"] == WORD_NOTHING,
       voice["word"])

    # THE STEPS, FROM ONE SOURCE, DONE THEN NEXT. The cap is on `next` only,
    # so what must equal NEXT_ASKED is the two arrays together, not `next`
    # alone: the day the street step moved into `done`, pinning `next` to
    # three would have called a correct plan broken.
    ok("the steps come from %s: %d done and %d next, %d shown, %d refused as "
       "stale"
       % (PRIORITIES, model["r3"]["doneNamed"], model["r3"]["named"],
          model["r3"]["shown"], model["r3"]["refused"]),
       model["r3"]["present"] and model["r3"]["donePresent"]
       and model["r3"]["doneNamed"] + model["r3"]["named"] == NEXT_ASKED
       and model["r3"]["refused"] == 0, model["r3"])
    ok("and production/NOW.md is named nowhere on the page, because the "
       "heading parser that read it is deleted",
       "production/NOW.md" not in page,
       [l for l in page.splitlines() if "NOW.md" in l][:1])
    ok("and the three are the three Jafar ordered, done first then next: "
       "control, then crime, then gossip",
       [d["title"][:12] for d in model["r3"]["done"]]
       + [i["title"][:12] for i in model["items"]]
       == ["Control a ch", "Commit one c", "Overhear the"],
       [d["title"] for d in model["r3"]["done"]]
       + [i["title"] for i in model["items"]])
    # THE EVIDENCE UNDER THE DONE STEP, opened and searched on the LIVE files.
    # This is the accepting case for read_done(): the tool's own claim that a
    # step is finished is only as good as the keys it just found again.
    ok("and every done step's evidence is found again in this checkout "
       "(%d of %d claimed step(s) proven, over %d of %d evidence key(s))"
       % (model["r3"]["doneProven"], model["r3"]["doneNamed"],
          model["r3"]["doneKeysFound"], model["r3"]["doneKeysAsked"]),
       model["r3"]["doneNamed"] >= 1
       and model["r3"]["doneProven"] == model["r3"]["doneNamed"]
       and model["r3"]["doneKeysFound"] == model["r3"]["doneKeysAsked"]
       and model["r3"]["doneKeysAsked"] >= 1
       and model["r3"]["doneRefusal"] is None,
       [(p["file"], p["key"], p["found"])
        for d in model["r3"]["done"] for p in d["evidence"]])

    # RULING 3 AND THE done ARRAY: THE LADDER, on the live repository FIRST,
    # ACCEPTING case. The numbers are DERIVED rather than frozen at 2 of 4:
    # the head printed above is today's series, and the day the crime step
    # landed this read 4 of 4 instead of calling a correct ladder broken.
    #
    # AND THE RUNG AFTER THE DONE ONES IS `current` OR `goal-current`, which
    # is the shape that arrived the night the last two named steps landed in
    # ONE run and emptied `next`. The page then read "STEP None OF 4" and
    # ladder_html crashed formatting a task number the goal does not have.
    # Both are fixed in ladder_rungs and ladder_html; this line is the half
    # that keeps them fixed.
    lad = model["ladder"]
    head = "STEP %s OF %s" % (lad["currentNum"], lad["total"])
    ok("the ladder reads %s, current on '%s', with the finished step below it "
       "as a DONE rung and neither it nor the goal stale today"
       % (head, (lad["rungs"][lad["currentNum"] - 1]["title"][:44]
                 if lad["currentNum"] else NOTHING)),
       lad["doneShown"] >= 1 and not lad["refused"]
       and lad["currentNum"] == lad["doneShown"] + 1
       and lad["total"] == lad["doneShown"] + lad["stepsShown"] + 1
       and [r["state"] for r in lad["rungs"][:lad["doneShown"] + 1]]
       == ["done"] * lad["doneShown"]
       + [("goal-current" if lad["stepsShown"] == 0 else "current")]
       and head in page,
       (head, lad["currentNum"], lad["total"], lad["doneShown"],
        [r["state"] for r in lad["rungs"]]))
    ok("and the done rung says the word DONE and the date it landed, never a "
       "glyph: '%s'"
       % re.sub(r"<[^>]+>", " ",
                [r for r in ladder_slice(page).split("<li")
                 if "DONE" in r][0])[:96].strip(),
       ">DONE<" in ladder_slice(page)
       and all("finished %s" % d["doneOn"] in ladder_slice(page)
               for d in lad["doneEntries"])
       and "✓" not in ladder_slice(page),
       ladder_slice(page)[:400])
    ok("and the ladder's own bytes count the done rungs with their "
       "denominator instead of the words %s, because one IS measured now (%s)"
       % (NOTHING, check_ladder_done_not_invented(page, model)[2]),
       check_ladder_done_not_invented(page, model)[1]
       and "%d of %d rung(s)" % (lad["doneShown"], lad["total"])
       in ladder_slice(page),
       ladder_slice(page)[-400:])
    ok("and the ladder sits above the top bar, which is RULING 3's whole "
       "point: readable before anything else on the page",
       check_ladder_at_top(page, model)[1], check_ladder_at_top(page, model))

    print("\n  THE SERIES this run printed, which is what any bound here "
          "would be read off:\n")
    for line in model["detail"]:
        print("    " + line)
    print("\n    the areas, one row each:")
    for a in model["areas"]:
        print("    %-34s %-20s gates=%d/%d heard=%s"
              % (a["name"], a["word"], a["gatesSeen"], a["gatesNamed"],
                 ("%d/%d" % (a["heardNum"], a["heardDen"]))
                 if a["heardDen"] else NOTHING))
    print("\n    the ladder, as read from %s, done rungs first:" % PRIORITIES)
    for i, d in enumerate(model["r3"]["done"]):
        print("    %d. %-62s [done %s, %d/%d key(s) found]"
              % (i + 1, d["title"][:62], d["doneOn"],
                 sum(1 for p in d["evidence"] if p["found"]),
                 len(d["evidence"])))
        for p in d["evidence"]:
            print("       evidence %s..%s [%s]"
                  % (p["file"], p["key"], "found" if p["found"]
                     else "file-missing" if not p["fileExists"]
                     else "key-absent"))
    for i, it in enumerate(model["items"]):
        print("    %d. %-62s [%s]"
              % (len(model["r3"]["done"]) + i + 1, it["title"][:62],
                 it["state"]))

    print("\n  ACCEPTING 2: a planted tree, so the accepting path is proven "
          "on files this test wrote.\n")
    t = _tree({"PLANTED.bat": FIXTURE_BAT, SIM_VERDICT: FIXTURE_VERDICT,
               PRIORITIES: FIXTURE_PRIORITIES,
               "production/queue/901-planted-ready.md": FIXTURE_QUEUE_READY})
    p2, m2 = build(t, now, served=NOWEB)
    ok("a planted tree finds its one .bat and draws the page "
       "(launchersFound=%d/%d)" % (m2["r1"]["found"], m2["r1"]["walked"]),
       m2["r1"]["found"] == 1
       and not [n for n, c, _ in run_checks(p2, m2) if not c],
       [n for n, c, _ in run_checks(p2, m2) if not c])
    ok("its two planted items come through in order and the third slot says "
       "%s rather than borrowing one" % NOTHING,
       [i["title"] for i in m2["items"]] == ["the first planted thing",
                                             "the second planted thing"]
       and "names 2 item(s), not 3" in p2,
       [i["title"] for i in m2["items"]])
    ok("and with no frame to show, the planted tree's street falls back to %s"
       % NOTHING,
       not m2["picture"]["shown"] and NOTHING in p2, m2["picture"]["why"][:80])
    ok("and with no done list at all the same ladder says %s in words and "
       "counts no rung finished, so an empty plan cannot read as a clean one"
       % NOTHING,
       m2["ladder"]["doneShown"] == 0 and not m2["r3"]["donePresent"]
       and m2["ladder"]["currentNum"] == 1
       and NOTHING in ladder_slice(p2).lower()
       and check_ladder_done_not_invented(p2, m2)[1],
       check_ladder_done_not_invented(p2, m2)[2])

    print("\n  ACCEPTING 2b: A PLANTED DONE STEP, the same path as the live "
          "plan's, on an evidence file this test wrote.\n")
    t_done = _tree({"PLANTED.bat": FIXTURE_BAT, SIM_VERDICT: FIXTURE_VERDICT,
                    PRIORITIES: _done_priorities(
                        [{"file": FIXTURE_EVIDENCE_REL,
                          "key": "plantedStatus=PROVEN"}]),
                    FIXTURE_EVIDENCE_REL: FIXTURE_EVIDENCE,
                    "production/queue/901-planted-ready.md":
                        FIXTURE_QUEUE_READY})
    pdn, mdn = build(t_done, now, served=NOWEB)
    dl = mdn["ladder"]
    ok("a done step whose key IS in its file is proven (%d/%d claimed, %d/%d "
       "key(s)) and the ladder counts done first: the page reads STEP %s OF "
       "%s and every check passes"
       % (dl["doneProven"], dl["doneClaimed"], dl["doneKeysFound"],
          dl["doneKeysAsked"], dl["currentNum"], dl["total"]),
       dl["doneProven"] == 1 and dl["doneKeysFound"] == 1
       and dl["currentNum"] == 2 and dl["total"] == 4
       and "STEP 2 OF 4" in pdn and not dl["refused"]
       and not [n for n, c, _ in run_checks(pdn, mdn) if not c],
       [n for n, c, _ in run_checks(pdn, mdn) if not c])
    ok("and its rung carries the word DONE and the date, never a glyph "
       "(rung 1 = %s)"
       % re.sub(r"<[^>]+>", " ",
                [r for r in ladder_slice(pdn).split("<li")
                 if "DONE" in r][0])[:70].strip(),
       ">DONE<" in ladder_slice(pdn)
       and "finished 2026-01-02" in ladder_slice(pdn)
       and "✓" not in ladder_slice(pdn)
       and dl["rungs"][0]["state"] == "done", ladder_slice(pdn)[:300])

    print("\n  ACCEPTING 3: THE SERVED PAGE, requested over HTTP from a local "
          "server, because checking the bytes we just wrote is not checking "
          "what is published.\n")
    pub = load_publisher()
    srv, base = pub._serve({"/map.html": (200, "text/html; charset=utf-8",
                                          page)})
    try:
        r_ok = served_reading(base + "/map.html", "local-fixture", timeout=5,
                              expect_digest=model["digest"])
        ok("a served copy of THIS run's page is requested, measured and named "
           "as this run (status=%s bytes=%d servedDigest=%s..localDigest=%s)"
           % (r_ok["status"], r_ok["bytes"], r_ok["digest"], model["digest"]),
           r_ok["measured"] and r_ok["result"] == "this-run"
           and r_ok["digest"] == model["digest"], r_ok)
        ok("and check_served passes on it (%s)"
           % check_served(page, dict(model, served=r_ok))[2],
           check_served(page, dict(model, served=r_ok))[1], r_ok)
    finally:
        srv.shutdown()
    url, how = pages_url(ROOT)
    ok("the published URL is DERIVED from the git remote and says so (%s)"
       % url, bool(url) and url.endswith("/" + OUT_NAME) and "git-remote" in how,
       (url, how))

    print("\n  THE NOTIFIER'S CONTRACT, which this rebuild may not break.\n")
    ok("mapDigest and mapFields are both in the bytes and the fields hash to "
       "the digest, which is what tools/map-notify.py asserts of the SERVED "
       "page (%s)" % model["digest"],
       DIGEST_RX.search(page) and decode_fields(page) is not None
       and digest_of(decode_fields(page)) == model["digest"],
       decode_fields(page))
    ok("and the three material groups are still q1, q2 and q3, in that "
       "meaning (q1=%d things, q2=%d areas, q3=%d items)"
       % (len(model["fields"]["q1"]), len(model["fields"]["q2"]),
          len(model["fields"]["q3"])),
       sorted(model["fields"]) == ["q1", "q2", "q3"]
       and len(model["fields"]["q2"]) == len(model["areas"]),
       sorted(model["fields"]))

    print("\n  REJECTING FIXTURES, all synthetic:\n")
    # THE STALE-ITEM GUARD, on a planted done file. Pinning this to a real
    # queue file would break the tool the day somebody finishes that task.
    t_stale = _tree({"PLANTED.bat": FIXTURE_BAT, SIM_VERDICT: FIXTURE_VERDICT,
                     PRIORITIES: FIXTURE_STALE,
                     "production/queue/902-planted-done.md":
                         FIXTURE_QUEUE_DONE})
    ps, ms = build(t_stale, now, served=NOWEB)
    n, c, s = check_next_three(ps, ms)
    ok("an item whose queue file says DONE is REFUSED, rendered as stale, and "
       "bites (%s)" % s,
       not c and ms["items"][0]["refused"] and "is stale" in ps, s)
    # RULING 3: THE LADDER CANNOT PROVE THIS STEP'S STATE, on the same
    # planted tree, so it says so rather than showing a false CURRENT or NEXT.
    # With the one named step stale, there is nothing left to be current.
    ok("the ladder shows a stale step as unable to prove its state, not as "
       "CURRENT or NEXT, and with nothing left it says so instead of a "
       "made-up step number",
       ms["ladder"]["rungs"][0]["refused"]
       and ms["ladder"]["currentNum"] is None
       and "STATE NOT PROVEN" in ps and "NO CURRENT STEP" in ps,
       (ms["ladder"]["rungs"][0], ms["ladder"]["currentNum"]))
    t_moved = _tree({"PLANTED.bat": FIXTURE_BAT, SIM_VERDICT: FIXTURE_VERDICT,
                     PRIORITIES: FIXTURE_STALE,
                     "production/queue/done/902-planted-done.md":
                         FIXTURE_QUEUE_DONE})
    pm, mm = build(t_moved, now, served=NOWEB)
    ok("and so is one whose file has moved to %s (state=%s)"
       % (QUEUE_DONE_DIR, mm["items"][0]["state"]),
       mm["items"][0]["refused"]
       and mm["items"][0]["state"] == "moved-to-done",
       mm["items"][0])
    t_broken = _tree({"PLANTED.bat": FIXTURE_BAT, SIM_VERDICT: FIXTURE_VERDICT,
                      PRIORITIES: "{ this is not json"})
    pbk, mbk = build(t_broken, now, served=NOWEB)
    ok("an unparseable priorities file reads %s with the reason and never an "
       "empty plan (%s)" % (NOTHING, mbk["r3"]["why"]),
       mbk["r3"]["named"] == 0 and "did-not-parse" in mbk["r3"]["why"]
       and NOTHING in pbk, mbk["r3"])

    # THE THREE DONE DISAGREEMENTS, RULED 2026-09-08. Each refuses the WHOLE
    # ladder with the stale banner and NAMES the reason, and none of them may
    # leave a step number on the page: a half-proven ladder is the invented
    # progress RULING 3 forbids, and "step 2 of 4" with one rung unproven is
    # exactly that. All three fixtures are synthetic.
    for label, files, want in (
        ("an evidence file that exists nowhere",
         {PRIORITIES: _done_priorities(
             [{"file": "production/planted-nowhere.txt",
               "key": "plantedStatus=PROVEN"}])},
         "done-step-1-evidence-missing/production/planted-nowhere.txt"),
        ("a key that appears in no file",
         {PRIORITIES: _done_priorities(
             [{"file": FIXTURE_EVIDENCE_REL,
               "key": "zzzNoSuchKeyEverEmitted=NEVER"}]),
          FIXTURE_EVIDENCE_REL: FIXTURE_EVIDENCE},
         "done-step-1-key-absent/zzzNoSuchKeyEverEmitted=NEVER"),
        ("a title standing in both arrays",
         {PRIORITIES: _done_priorities(
             [{"file": FIXTURE_EVIDENCE_REL,
               "key": "plantedStatus=PROVEN"}],
             title="the first planted thing"),
          FIXTURE_EVIDENCE_REL: FIXTURE_EVIDENCE},
         "title-in-both-done-and-next"),
        ("a done field that is there but is not a list",
         {PRIORITIES: json.dumps(
             dict(json.loads(FIXTURE_PRIORITIES), done={"oops": 1}),
             indent=1)},
         "done-is-not-a-list"),
    ):
        base = {"PLANTED.bat": FIXTURE_BAT, SIM_VERDICT: FIXTURE_VERDICT,
                "production/queue/901-planted-ready.md": FIXTURE_QUEUE_READY}
        base.update(files)
        pr, mr = build(_tree(base), now, served=NOWEB)
        lr = mr["ladder"]
        ok("%s refuses the WHOLE ladder, names the reason and prints no step "
           "number (refusedBy=%s refusedWhy=%s doneProven=%d/%d)"
           % (label, lr["refusedBy"], lr["refusedWhy"], lr["doneProven"],
              lr["doneClaimed"]),
           lr["refused"] and lr["refusedBy"] == "done-evidence"
           and lr["refusedWhy"] == want and lr["doneProven"] == 0
           and "THE LADDER IS STALE" in ladder_slice(pr)
           and want in ladder_slice(pr)
           and "STEP " not in ladder_slice(pr)
           and check_ladder_step_count(pr, mr)[1],
           (lr["refusedWhy"], ladder_slice(pr)[:240]))
    # AND THE GOAL'S OWN REFUSAL STILL WINS ITS OWN WORDING, so the two causes
    # cannot be read as one: this one is refused by the goal, not by evidence.
    t_goal = _tree({"PLANTED.bat": FIXTURE_BAT, SIM_VERDICT: FIXTURE_VERDICT,
                    PRIORITIES: json.dumps(
                        dict(json.loads(FIXTURE_PRIORITIES),
                             milestoneFrom="production/queue/902-planted-"
                                           "done.md"), indent=1),
                    "production/queue/901-planted-ready.md":
                        FIXTURE_QUEUE_READY,
                    "production/queue/902-planted-done.md":
                        FIXTURE_QUEUE_DONE})
    pg, mg = build(t_goal, now, served=NOWEB)
    ok("a goal whose own file says DONE still refuses the ladder as before, "
       "and says so with its own reason (refusedBy=%s refusedWhy=%s)"
       % (mg["ladder"]["refusedBy"], mg["ladder"]["refusedWhy"]),
       mg["ladder"]["refused"] and mg["ladder"]["refusedBy"] == "goal-state"
       and mg["ladder"]["goalRefused"]
       and "THE LADDER IS STALE" in ladder_slice(pg)
       and "STEP " not in ladder_slice(pg),
       (mg["ladder"]["refusedBy"], ladder_slice(pg)[:200]))

    # A REJECTING KEY THAT EXISTS NOWHERE, on purpose.
    ok("a required key that exists nowhere keeps an area unanswered",
       not key_present(ROOT, SIM_VERDICT, "zzzNoSuchKeyEverEmitted"),
       "key_present said True for a synthetic key")
    ok("and a key that DOES exist is seen, so the probe is not a ratchet",
       key_present(ROOT, SIM_VERDICT, "speechSpoken"),
       "key_present said False for speechSpoken")
    ok("none of the %d key(s) that would report a playable session exists "
       "anywhere yet (%s)" % (len(PLAYABLE_KEYS), "/".join(PLAYABLE_KEYS)),
       not any(key_present(ROOT, f, k) for k in PLAYABLE_KEYS
               for f in (SIM_VERDICT, UE_VERDICT)),
       [k for k in PLAYABLE_KEYS if key_present(ROOT, SIM_VERDICT, k)])

    # THE MATERIAL CHANGE DETECTOR, all four outcomes.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "map.html"
        pa, ma = build(t, now, out_path=out, served=NOWEB)
        ok("no previous page reads nothing-measured, never 'no change'",
           ma["change"] == "nothing-measured", ma["change"])
        out.write_text(pa, encoding="utf-8")
        _pb2, mb = build(t, now.replace(hour=23), out_path=out, served=NOWEB)
        ok("a regenerated timestamp is NOT a material change (digest %s)"
           % mb["digest"],
           mb["change"] == "no" and mb["digest"] == ma["digest"],
           "%s / %s vs %s" % (mb["change"], mb["digest"], ma["digest"]))
        t2 = _tree({"PLANTED.bat": FIXTURE_BAT, "SECOND THING.bat": FIXTURE_BAT,
                    SIM_VERDICT: FIXTURE_VERDICT, PRIORITIES: FIXTURE_PRIORITIES,
                    "production/queue/901-planted-ready.md":
                        FIXTURE_QUEUE_READY})
        out2 = Path(tmp) / "map2.html"
        out2.write_text(pa, encoding="utf-8")
        _pc, mc = build(t2, now, out_path=out2, served=NOWEB)
        ok("a NEW runnable thing IS a material change, and the changed field "
           "is named (%s)" % ("/".join(mc["changedGroups"] or [])),
           mc["change"] == "yes" and mc["changedGroups"] == ["q1"],
           "%s %s" % (mc["change"], mc["changedGroups"]))
        t3 = _tree({"PLANTED.bat": FIXTURE_BAT, PRIORITIES: FIXTURE_PRIORITIES,
                    "production/queue/901-planted-ready.md":
                        FIXTURE_QUEUE_READY})
        out3 = Path(tmp) / "map3.html"
        out3.write_text(pa, encoding="utf-8")
        _pd, md = build(t3, now, out_path=out3, served=NOWEB)
        ok("an AREA changing state IS a material change (%s)"
           % ("/".join(md["changedGroups"] or [])),
           md["change"] == "yes" and "q2" in (md["changedGroups"] or []),
           "%s %s" % (md["change"], md["changedGroups"]))
        t4 = _tree({"PLANTED.bat": FIXTURE_BAT, SIM_VERDICT: FIXTURE_VERDICT,
                    PRIORITIES: FIXTURE_PRIORITIES.replace(
                        "the first planted thing", "a different first thing"),
                    "production/queue/901-planted-ready.md":
                        FIXTURE_QUEUE_READY})
        out4 = Path(tmp) / "map4.html"
        out4.write_text(pa, encoding="utf-8")
        _pe, me = build(t4, now, out_path=out4, served=NOWEB)
        ok("the NEXT THREE changing IS a material change (%s)"
           % ("/".join(me["changedGroups"] or [])),
           me["change"] == "yes" and me["changedGroups"] == ["q3"],
           "%s %s" % (me["change"], me["changedGroups"]))
        # RULING 3: A STEP TURNING STALE IS ALSO A MATERIAL CHANGE, even when
        # next-three.json's own text does not move one byte: only the queue
        # file behind item 1 flips to DONE. Without this, the ladder's
        # CURRENT tag could move on his phone with nothing for
        # tools/map-notify.py to see, and "a ladder that moves a step" would
        # never wake it.
        t5 = _tree({"PLANTED.bat": FIXTURE_BAT, SIM_VERDICT: FIXTURE_VERDICT,
                   PRIORITIES: FIXTURE_PRIORITIES,
                   "production/queue/901-planted-ready.md":
                       FIXTURE_QUEUE_DONE})
        out5 = Path(tmp) / "map5.html"
        out5.write_text(pa, encoding="utf-8")
        _pf, mf = build(t5, now, out_path=out5, served=NOWEB)
        ok("a step turning stale IS a material change with next-three.json's "
           "own bytes unedited, and the ladder's current rung actually moved "
           "(%s, ladderCurrentNum now %s)"
           % ("/".join(mf["changedGroups"] or []),
              mf["ladder"]["currentNum"]),
           mf["change"] == "yes" and mf["changedGroups"] == ["q3"]
           and mf["ladder"]["rungs"][0]["refused"]
           and mf["ladder"]["currentNum"] == 2,
           "%s %s ladderCurrent=%s" % (mf["change"], mf["changedGroups"],
                                       mf["ladder"]["currentNum"]))

    # THE GUARDS MUST BE ABLE TO GO RED, or they are ratchets.
    n, c, s = check_ladder_at_top(
        page.replace(LADDER_START, "", 1).replace(LADDER_END, "", 1)
        + LADDER_START + "<p>moved</p>" + LADDER_END, model)
    ok("ladderAtTop bites when the ladder is not the first thing on the page",
       not c, s)
    n, c, s = check_ladder_step_count(
        "%sSTEP 9 OF 9%s" % (LADDER_START, LADDER_END), model)
    ok("ladderStepCount bites when the printed step does not match what this "
       "run computed", not c, s)
    n, c, s = check_ladder_done_not_invented(
        "%sit is all done: ✓%s" % (LADDER_START, LADDER_END), model)
    ok("ladderDoneHonest bites on an invented checkmark (%s)" % s, not c, s)
    n, c, s = check_ladder_done_not_invented(
        "%sno wording about done steps here%s" % (LADDER_START, LADDER_END),
        m2)
    ok("and bites when 'not measured' is missing from a ladder with NO done "
       "step named, even without a tick (%s)" % s, not c, s)
    # THE HALF-PROVEN LADDER, which is the failure the done array could
    # introduce and the one the ruling names: a rung claimed done whose
    # evidence this run could not find must not stand as a number. Planted on
    # the LIVE page, whose accepting half passed above.
    n, c, s = check_ladder_done_not_invented(
        page, dict(model, ladder=dict(model["ladder"], doneProven=0)))
    ok("and bites when the ladder shows a done rung this run could not prove, "
       "which is a step count resting on a claim (%s)" % s, not c, s)
    n, c, s = check_ladder_no_raw_content(
        "%ssee production/queue/138-thing.md%s" % (LADDER_START, LADDER_END),
        model)
    ok("ladderNoRawContent bites on a raw repository path inside the ladder",
       not c, s)
    n, c, s = check_ladder_no_raw_content(
        "%s3 of 12 gates ok%s" % (LADDER_START, LADDER_END), model)
    ok("and bites on a gate count inside the ladder", not c, s)
    n, c, s = check_ladder_stale_rungs_say_so(
        "%squiet%s" % (LADDER_START, LADDER_END),
        dict(m2, ladder=dict(m2["ladder"], goalRefused=False, refused=False,
                             staleCount=1)))
    ok("ladderStaleRungsSaySo bites when a stale rung is claimed but the tag "
       "is not on the page", not c, s)
    n, c, s = check_first_screen("<p>nothing at all</p>", m2)
    ok("firstScreen bites when the three answers are not there in order", not c, s)
    n, c, s = check_picture("<p>no picture here</p>",
                            dict(m2, picture=dict(m2["picture"], shown=True,
                                                  rel="x.png")))
    ok("picture bites when the model says shown and no data URI is in the "
       "bytes", not c, s)
    n, c, s = check_probe_is_not_a_game(
        "<p>a great game you can play right now</p>", model)
    ok("probeIsNotAGame bites when the page stops saying nobody can play it",
       not c, s)
    # THE GUARD ADDED FOR THE DECAYED CLAIM, BOTH DIRECTIONS, per the ruling
    # that a check untested on a live regression cannot tell one from an
    # improvement. Both planted on the LIVE model/page (accepting halves
    # already proven above), never on a frozen fixture.
    regressed = dict(model, r2=dict(model["r2"],
                                    scan=dict(model["r2"]["scan"],
                                             markersFound=0)))
    n, c, s = check_player_control_matches_scan(page, regressed)
    ok("playerControlMatchesScan bites if player control regresses to 0 "
       "markers while the page still claims 'built, not walked' (%s)" % s,
       not c, s)
    stale_count_page = page.replace(
        "%d of %d marker(s) of a controllable character"
        % (model["r2"]["scan"]["markersFound"],
           model["r2"]["scan"]["markersAsked"]),
        "0 of %d marker(s) of a controllable character"
        % model["r2"]["scan"]["markersAsked"])
    n, c, s = check_player_control_matches_scan(stale_count_page, model)
    ok("and bites when the printed marker count disagrees with the live "
       "scan even though the area's own word did not change (%s)" % s,
       not c, s)
    n, c, s = check_no_absence_claim(
        "<p>There is no packaged game build exists at all.</p>", m2)
    ok("noAbsenceClaim BITES on an absence claimed without a scope (%s)" % s,
       not c, s)
    n, c, s = check_no_absence_claim(
        "<p>No packaged game build exists in this checkout, which cannot see "
        "your PC.</p>", m2)
    ok("and PASSES the same shape once the sentence names the checkout, so it "
       "is not a ratchet (%s)" % s, c, s)
    n, c, s = check_one_priority_source(
        '<p>read from production/NOW.md and %s</p>' % PRIORITIES, m2)
    ok("onePrioritySource bites when the page names the log as a source",
       not c, s)
    n, c, s = check_availability_words('<p data-avail="yes">x</p>', m2)
    ok("availabilityWords bites on the word yes, which no scan here can earn",
       not c, s)
    fake = dict(AREAS[0], word=WORD_NOTHING, why="planted", gatesSeen=0,
                gatesNamed=0, gatesBad=0, missing=["x"], heardNum=None,
                heardDen=None, readings=[("piecesTextured", "563/593")],
                readingsFrom=UE_VERDICT, scan=model["r2"]["scan"])
    liar = ('<section class="sheet" id="a-street-and-its-look">'
            '<p>runs in text only</p><p>piecesTextured=563/593</p></section>')
    n, c, s = check_no_comforting_bar(liar, dict(m2, areas=[fake]))
    ok("noComfortingBar bites on an unanswered area showing a health word",
       not c, s)
    fake_unheard = dict(AREAS[3], word=WORD_UNHEARD, why="planted", gatesSeen=1,
                        gatesNamed=1, gatesBad=0, missing=[], heardNum=0,
                        heardDen=90, readings=[], readingsFrom=STUDY,
                        scan=model["r2"]["scan"])
    n, c, s = check_no_comforting_bar(
        '<section class="sheet" id="a-people-and-their-memory">'
        '<p>nothing was heard</p></section>',
        dict(m2, areas=[fake_unheard]))
    ok("and bites on a zero heard printed without its denominator", not c, s)
    n, c, s = check_links('<a href="production/NOW.md">x</a>', m2)
    ok("links bites on a repository markdown link", not c, s)
    n, c, s = check_material_rule("<p>nothing</p>", m2)
    ok("materialRule bites when the rule, the digest and the fields are gone",
       not c, s)
    n, c, s = check_cap_announced("<p>quiet</p>",
                                  dict(m2, rows=[{}] * (TOOLS_SHOWN + 4)))
    ok("capAnnounced bites on a truncation that does not say it bit", not c, s)
    n, c, s = check_denominators("<p>0 packaged builds</p>", model)
    ok("denominators bites on a zero printed without what it counted", not c, s)
    n, c, s = check_no_clipped_svg_text(
        "", dict(m2, geo=dict(m2["geo"], widestChars=200, widestFontPx=15,
                              textWidthPx=100)))
    ok("svgTextFits bites on a line predicted wider than its own box", not c, s)
    n, c, s = check_stamp("<p>no stamp</p>", m2)
    ok("stamp bites when the generator's dated sentence is missing", not c, s)
    n, c, s = check_theme('<meta content="dark light">', m2)
    ok("themeAware bites on a page that declares both schemes and paints one",
       not c, s)
    n, c, s = check_publisher_marker("<p>not the map</p>", m2)
    ok("publisherMarker bites when the string publish-glance.py looks for is "
       "gone", not c, s)
    n, c, s = check_next_three('<p class="num">1</p>', m2)
    ok("nextThree bites when a slot is missing", not c, s)
    n, c, s = check_width("<style>.x { min-width: 900px; }</style>", m2)
    ok("width bites on a declaration wider than a phone", not c, s)
    n, c, s = check_external('<script src="https://cdn.example/x.js"></script>',
                             m2)
    ok("external bites on a remote reference", not c, s)
    n, c, s = check_formatting("a \u2014 b <em>c</em>", m2)
    ok("formatting bites on an em-dash and an italic", not c, s)
    n, c, s = check_secrets("token 123456789:AAH" + "x" * 32, m2)
    ok("secrets bites on a token-shaped string", not c, s)
    n, c, s = check_weight("x" * (PAGE_BYTE_CAP + 1), m2)
    ok("weight bites on a page over the byte cap", not c, s)
    n, c, s = check_viewport("<head></head>", m2)
    ok("viewport bites when the meta tag is missing", not c, s)

    print("\n%s --selftest: %s. %d passed, %d failed, over %d check(s)"
          % (TOOL, "PASS" if not failed else "FAILED", passed, len(failed),
             len(CHECKS)))
    for f in failed:
        print("  " + f)
    return 0 if not failed else 3


def parse_now(s):
    t = s.strip().replace("Z", "+00:00")
    d = datetime.datetime.fromisoformat(t)
    if d.tzinfo is None:
        d = d.replace(tzinfo=datetime.timezone.utc)
    return d.astimezone(datetime.timezone.utc)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", default=None)
    ap.add_argument("--now", default=None, help="ISO clock, for the stamp")
    ap.add_argument("--served", default=None,
                    help="the published URL to request; default is derived "
                         "from the git remote")
    ap.add_argument("--no-served-check", action="store_true",
                    help="do not request the published page. The run then says "
                         "so in words and never implies it checked it")
    ap.add_argument("--served-timeout", type=float, default=SERVED_TIMEOUT_SEC)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    root = Path(args.root).resolve()
    out = Path(args.out) if args.out else root / OUT_NAME
    now = parse_now(args.now) if args.now else datetime.datetime.now(
        datetime.timezone.utc)
    page, model = build(root, now, out_path=out, served={
        "attempt": not args.no_served_check, "url": args.served,
        "timeout": args.served_timeout})
    # WRITTEN EVEN WHEN IT IS THIN, and deliberately over the previous page: a
    # stale map that still looks current is worse than one that says what it
    # could not derive. The exit code carries the failure to the caller.
    out.write_text(page, encoding="utf-8")
    checks = run_checks(page, model)
    bad = [n for n, c, _ in checks if not c]
    # PER-ROW NUMBERS ON THE ROW'S LINE, whole-run numbers on the done line. A
    # grep across lines must not be able to read one row's label as the page's.
    for a in model["areas"]:
        print("map: area=%s word=%s gatesOk=%d/%d-named heard=%s/%s "
              "readings=%s"
              % (a["key"], a["word"].replace(" ", "-").replace(",", ""),
                 a["gatesSeen"] - a["gatesBad"], a["gatesNamed"],
                 a["heardNum"] if a["heardNum"] is not None
                 else NOTHING.replace(" ", "-"),
                 a["heardDen"] if a["heardDen"] is not None
                 else NOTHING.replace(" ", "-"),
                 "/".join("%s=%s" % (k, v) for k, v in a["readings"]
                          if v is not None) or NOTHING.replace(" ", "-")))
    # PER-STEP NUMBERS ON THE STEP'S OWN LINE. A done step's evidence is a
    # per-sample reading (which file, which key, was it found), so it belongs
    # here and not on the done line, where a grep would read one step's pairs
    # as the whole ladder's. file..key joined by dots and pairs by commas
    # because every reader of this channel splits on whitespace.
    for i, d in enumerate(model["ladder"]["doneEntries"]):
        found = sum(1 for p in d["evidence"] if p["found"])
        print("map: done%d=%s doneOn=%s proven=%s evidenceFound=%d/%d-pairs "
              "evidence=%s refusal=%s"
              % (i + 1, re.sub(r"\s+", "_", d["title"]),
                 re.sub(r"\s+", "-", d["doneOn"]),
                 "yes" if d["proven"] else "no", found, len(d["evidence"]),
                 ",".join("%s..%s%s" % (p["file"], p["key"],
                                        "" if p["found"] else "/ABSENT")
                          for p in d["evidence"])
                 or NOTHING.replace(" ", "-"),
                 d["refusal"] or "none"))
    for i, it in enumerate(model["items"][:NEXT_ASKED]):
        print("map: next%d=%s state=%s queue=%s"
              % (i + 1, re.sub(r"\s+", "_", it["title"]), it["state"],
                 it["queue"] or "none"))
    if not model["r1"]["found"]:
        code, word = 2, "NOTHING-MEASURED"
    elif bad:
        code, word = 1, "REFUSED"
    else:
        code, word = 0, "DONE"
    print("map: wrote %s %s" % (out, " ".join(s for _, _, s in checks)))
    # THE SAME FACT IN WORDS, on its own line, because "the published page was
    # never requested" must not need a key decoded to be understood.
    print("map: NOTE %s" % served_sentence(model["served"]))
    for line in model["detail"]:
        print("map: " + line)
    # PAGE BYTES ARE THE BYTES THIS RUN WROTE, with the picture's share beside
    # them so no reader can take the page's weight for the shell's.
    print("map: %s pageBytesGenerated=%d/%d-cap ofWhichPictureB64=%d "
          "checksFailed=%d/%d checkedBytes=generated servedPageResult=%s"
          % (word, len(page.encode("utf-8")), PAGE_BYTE_CAP,
             model["picture"]["bytes"], len(bad), len(CHECKS),
             model["served"]["result"].replace(" ", "-")))
    return code


if __name__ == "__main__":
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
