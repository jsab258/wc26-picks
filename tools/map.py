#!/usr/bin/env python3
"""THE MAP: three questions, in order, and nothing else competes for space.

    python3 tools/map.py                      # write map.html at the root
    python3 tools/map.py --selftest           # accepting case FIRST
    python3 tools/map.py --root <dir> --out <f> --now <iso>

WHAT IT IS. Jafar, 2026-09-06, verbatim: "I have no overview. I do not know
what is playable, what is done, or what is next, and I found out about the
stranger test by reading a transcript. Fix the map so it answers those three
questions at a glance, phone-first." So this page answers exactly three
questions, in his order:

    1. WHAT CAN I RUN TODAY, AND HOW      above the fold, always
    2. WHAT STATE IS EACH AREA IN         one honest word and one number
    3. WHAT ARE THE NEXT THREE THINGS     with the rule that chose them

THE INDICTMENT IS THE SPECIFICATION. A thing he can run on his own PC was
built, shipped, and he learned about it from a transcript. So question 1 is
DERIVED FROM THE TREE every run: the .bat files at the repository root are
walked, not listed, and a new one appears on this page the run after it lands
without anybody remembering to add it.

WHAT REPLACED THE TILE GRID, and why. This file used to render every entry of
production/systems-inventory.json as a coloured tile. That page answered "how
many systems are there" with a status field a person types, and Jafar has now
said in his own words that it did not give him an overview. A typed status
board decays; worse, it reads as health. The grid is gone from the page. The
inventory is still read, and it appears only as a denominator behind the tap,
labelled as typed rather than measured, because it may not set a state word.
The previous renderer is in git history at commit de158c2c if it is wanted.

NOTHING ON THIS PAGE IS TYPED. Every runnable thing, every state word, every
next item and every number is read out of a file in this repository at
generation time, and the line carrying it names that file. Where nothing
measures a thing, the page prints the words "nothing measured" and says what
key would answer it. A comforting bar over an unmeasured area is the exact
fault this page exists to end: see THE STREET below.

THE STREET IS THE WORKED EXAMPLE. production/d1-probe/ue-vignette-verdict.txt
prints materialsStatus=PARTIAL and piecesTextured=563/593, which read as a
street most of the way to textured. They are counts of what the STAGING
pipeline did, and no committed key measures whether the frame shows the bound
textures at all. So the street's look reads "nothing measured", names the key
that would answer it, and prints those staging counts underneath as readings
that do NOT answer it. An area cannot report health from a number that cannot
see the fault.

SELF-CONTAINED, because tools/publish-glance.py puts this on GitHub Pages
beside index.html and gallery.html: one file, no server, no build step, no
remote script, stylesheet, font or image. The taps are CSS :target, so opening
one makes no request and needs no JavaScript. The only links are the two
sibling pages the Producer's register allows; a repository markdown link is
refused by a check, because Jafar ruled those out of anything he reads.

EXIT CODES, distinct per outcome. 0 the page is good. 1 a check bit, and the
page was still written because a stale map is worse than one that says what it
could not derive. 2 nothing measured: no runnable entry point was found at all,
which means the walk is broken rather than that the project has none. 3 the
selftest failed. 4 tools/glance.py could not be imported.
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
NOW_FILE = "production/NOW.md"
QUEUE_DIR = "production/queue"
INVENTORY = "production/systems-inventory.json"

# THE ONLY LINKS. The Producer's register allows three destinations and this
# page is one of them, so it may point at the other two and at nothing else. A
# repository markdown link is what Jafar ruled out; check_links counts them.
SIBLINGS = (("index.html", "the glance"), ("gallery.html", "the pictures"))


def load_glance():
    """The phone-first bar and the git helper are tools/glance.py's, imported
    rather than copied. Two implementations of "how wide is a phone" drift, and
    the copy nobody looks at is the one that keeps passing at 360 after the
    rule became 340. tools/gallery.py imports the same module for the same
    reason."""
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
# THE GEOMETRY. Question 1 is above the fold and that is the hard constraint,
# so its height is arithmetic from the constants the stylesheet is generated
# from, printed against its budget every run, and never a browser measurement.
#
# 390 CSS px is the logical width of the phones in use (iPhone 12 through 15
# are 390 or 393) and is tools/glance.py's stated figure. Safari on those
# phones leaves about 659 to 664 px between its toolbars; 640 is below the
# smallest, so a block that fits here fits on the phone and the error can only
# be in the direction of extra room.
# ---------------------------------------------------------------------------
PHONE_WIDTH_PX = 390
ONE_SCREEN_PX = 640
BODY_PAD_PX = 8
HEAD_PX = 16
H2_PX = 15
H2_GAP_PX = 4
LINE_PX = 15
SMALL_LINE_PX = 14
ROW_GAP_PX = 7
SECTION_GAP_PX = 10
BODY_FONT_PX = 13
SMALL_FONT_PX = 11
# The wrap is modelled, not measured: an average lowercase advance of half the
# font size is the usual approximation for these sans faces. IT SHIPS ITS
# INSTRUMENT: every run prints the worst row, its predicted lines and the
# slack, so one look at the page corrects this one number rather than a guess.
AVG_ADVANCE_EM = 0.5

# HOW LONG A DERIVED SENTENCE MAY BE. Not a taste setting: the "what it is"
# line is quoted out of a .bat file's own banner and those run to paragraphs.
# 96 characters is about two lines at BODY_FONT_PX on a 390 px phone by the
# arithmetic above. When it bites the page prints the ellipsis, and the run
# prints the cut length beside the original, so the bound can be read off real
# runs rather than defended.
SENTENCE_CAP = 96
ITEM_CAP = 110
# HOW MANY OF A LIST ARE SHOWN BEFORE THE CAP MUST ANNOUNCE ITSELF.
RUNNABLE_SHOWN = 8
UNMAPPED_SHOWN = 6
READINGS_SHOWN = 5
NEXT_ASKED = 3


def wrap_lines(text, font_px, width_px):
    """How many lines this text takes at this font on this width, by greedy
    word wrapping the way a browser does it. An ESTIMATE, named as one
    everywhere it is used."""
    cpl = max(1, int(width_px / (font_px * AVG_ADVANCE_EM)))
    lines, cur = 0, ""
    for word in str(text).split():
        joined = (cur + " " + word).strip()
        if len(joined) <= cpl or not cur:
            cur = joined
        else:
            lines += 1
            cur = word
    return max(1, lines + (1 if cur else 0))


def cap_text(text, cap):
    """(text, bit, originalLen). A truncation that does not say it bit reads as
    the whole sentence, so the ellipsis ships with it and the caller prints the
    length it cut from."""
    s = " ".join(str(text).split())
    if len(s) <= cap:
        return s, False, len(s)
    return s[:cap].rstrip() + "...", True, len(s)


# ---------------------------------------------------------------------------
# QUESTION 1: WHAT CAN I RUN TODAY, AND HOW.
#
# WALKED, NOT LISTED. The entry points are the .bat files in the repository
# ROOT directory, which is the double-click convention here: the root is what
# Jafar sees when he opens the folder, and every tool ladder lives under
# tools/ where it belongs to a job rather than to him. A .bat that lands at the
# root appears on this page the next run.
#
# VISUAL OR TEXT IS DERIVED FROM WHAT THE FILE STARTS, not from its name.
# Jafar, 2026-09-06, has said he will not spend evenings on a text harness
# "while the game has no playable build", so this label is the distinction he
# is deciding with and it may not be decoration. The rule, in the order it is
# applied, and every rung names the bytes it matched:
#   VISUAL  the file starts a program that draws the game: a packaged player
#           executable that EXISTS in this tree, an Unreal package, a Unity
#           player. Checked against the tree, so a name in a comment cannot
#           earn the label.
#   TEXT    everything else that starts something: a dotnet console project
#           (Microsoft.NET.Sdk with OutputType Exe), a python script, a git
#           command, or a browser opened on an .html page of words.
#   unknown nothing matched. The row says so rather than guessing, because a
#           wrong label here is the one that costs him an evening.
# ---------------------------------------------------------------------------

REM_RX = re.compile(r"^\s*(?:REM|::)\b", re.I)
BANNER_RX = re.compile(r"^\s*REM\s*=====", re.I)
DOTNET_RX = re.compile(r"dotnet\s+run\b[^\n]*?--project\s+\"?[^\"\n]*?[\\/]"
                       r"(ledger[\\/][A-Za-z0-9_.-]+)", re.I)
PY_RX = re.compile(r"[\"']?%PY%[\"']?\s+\"?[^\"\n]*?[\\/](tools[\\/][^\"\n]+?\.py)", re.I)
HTML_RX = re.compile(r"start\s+\"\"\s+\"[^\"\n]*?[\\/]([A-Za-z0-9_.-]+\.html)\"", re.I)
GIT_RX = re.compile(r"^\s*git\s+(pull|fetch|clone|checkout)\b", re.I | re.M)
EXE_RX = re.compile(r"[\\/]?([A-Za-z0-9_.-]+\.exe)\b", re.I)
# .exe names a windows launcher rather than the game, so they are named here
# and excluded: matching them as VISUAL would label the python finder a game.
NOT_THE_GAME_EXE = ("python.exe", "git.exe", "dotnet.exe", "cmd.exe",
                    "explorer.exe", "powershell.exe", "unity.exe")


def code_lines(text):
    """The file with its comment lines removed. A launch command inside a REM
    is documentation, and on 2026-09-06 one of them ("start ... STUDIO
    MACHINE.bat", inside the autostart hook writer) would have been read as the
    thing the file starts."""
    return "\n".join(l for l in text.splitlines()
                     if not REM_RX.match(l) and ">>" not in l)


def one_line_about(text):
    """The file's own first banner sentence. The .bat files here all carry a
    REM ===== banner written for Jafar, so the page quotes the author rather
    than a description this renderer invented."""
    lines = text.splitlines()
    start = None
    for i, l in enumerate(lines):
        if BANNER_RX.match(l):
            start = i + 1
            break
    if start is None:
        return "", 0
    body = []
    for l in lines[start:]:
        if BANNER_RX.match(l):
            break
        if not REM_RX.match(l):
            break
        s = re.sub(r"^\s*(?:REM|::)\s?", "", l).rstrip()
        if not s.strip():
            if body:
                break
            continue
        body.append(s.strip())
    joined = " ".join(body)
    m = re.search(r"[.!?](\s|$)", joined)
    sentence = joined[:m.end()].strip() if m else joined
    if len(sentence) < 25 and len(joined) > len(sentence):
        rest = joined[len(sentence):]
        m2 = re.search(r"[.!?](\s|$)", rest)
        sentence = (sentence + " " + (rest[:m2.end()] if m2 else rest)).strip()
    return sentence, len(joined)


def csproj_kind(root, rel):
    """(kind, why) for a dotnet project path, read from the .csproj on disk."""
    d = root / rel.replace("\\", "/")
    hits = sorted(d.glob("*.csproj")) if d.is_dir() else []
    if not hits:
        return None, "no-csproj-under/%s" % rel.replace("\\", "/")
    body = hits[0].read_text(encoding="utf-8", errors="replace")
    sdk = "Microsoft.NET.Sdk" in body
    exe = "<OutputType>Exe</OutputType>" in body
    if sdk and exe:
        return "TEXT", "console-project/%s/OutputType.Exe/no-renderer" \
            % hits[0].relative_to(root).as_posix()
    return None, "unrecognised-csproj/%s" % hits[0].relative_to(root).as_posix()


def classify(root, text):
    """(label, why, action_hint). Every rung names the bytes it matched."""
    code = code_lines(text)
    for m in EXE_RX.finditer(code):
        name = m.group(1)
        if name.lower() in NOT_THE_GAME_EXE:
            continue
        found = list(root.rglob(name))
        if found:
            return ("VISUAL", "starts/%s/which-exists-in-this-tree" % name, None)
        return ("unknown", "names/%s/which-is-not-in-this-tree" % name, None)
    m = DOTNET_RX.search(code)
    if m:
        rel = m.group(1)
        kind, why = csproj_kind(root, rel)
        if kind:
            # THE DISPLAY FORM CARRIES SPACES ON PURPOSE. It is prose on the
            # page and never a key=value value; nothing on the done line
            # prints it, so the no-spaces rule does not apply and a command a
            # person retypes must be the command that works.
            return (kind, why, "dotnet run --project %s"
                    % rel.replace("\\", "/"))
        return ("unknown", why, None)
    m = PY_RX.search(code)
    if m:
        return ("TEXT", "runs/%s/in-a-console-window" % m.group(1).replace("\\", "/"),
                None)
    m = HTML_RX.search(code)
    if m:
        return ("TEXT", "opens/%s/a-page-of-words-and-numbers" % m.group(1), None)
    if GIT_RX.search(code):
        return ("TEXT", "runs-git/in-a-console-window", None)
    return ("unknown", "no-launch-command-matched", None)


def packaged_builds(root):
    """Is there a playable build in this tree at all? The denominator behind
    every VISUAL zero on the page, and the reason the label can be trusted."""
    exes = [p for p in root.rglob("*.exe")
            if p.name.lower() not in NOT_THE_GAME_EXE and ".git/" not in
            p.as_posix()]
    return exes


def tracked_root_bats(root):
    """(names git knows about at the root, whether git could answer at all).

    A .bat sitting in this container that has not been committed is NOT on
    Jafar's PC and he cannot double-click it, so the page may not offer it as
    if he could. This is not a hypothetical: START EVERYTHING.bat appeared in
    this working tree at 14:12 on 2026-09-06 while this tool was being written,
    untracked, and the first draft listed it beside the five he has.

    WHEN GIT CANNOT ANSWER the second element is False and the page prints the
    words nothing measured for the column rather than calling everything
    untracked, which is what a planted fixture tree would otherwise read as."""
    out = GLANCE.git(root, "ls-files", "--", "*.bat")
    if not out:
        inside = GLANCE.git(root, "rev-parse", "--is-inside-work-tree")
        return set(), inside == "true"
    return {n for n in out.splitlines() if "/" not in n}, True


def find_runnables(root):
    """(rows newest-first-by-name, reading). The rows are the .bat files in the
    root directory, walked. The reading carries every denominator."""
    root = Path(root)
    tracked, git_answered = tracked_root_bats(root)
    bats = sorted(p for p in root.glob("*.bat") if p.is_file())
    all_bats = sorted(p for p in root.rglob("*.bat")
                      if p.is_file() and ".git/" not in p.as_posix())
    rows, capped = [], 0
    for p in bats:
        text = p.read_text(encoding="utf-8", errors="replace")
        about, full = one_line_about(text)
        said, bit, orig = cap_text(about or NOTHING, SENTENCE_CAP)
        capped += 1 if bit else 0
        label, why, hint = classify(root, text)
        rows.append({
            "name": p.name, "about": said, "aboutBit": bit,
            "aboutChars": orig, "label": label, "why": why,
            "how": "double-click it", "hint": hint,
            "file": p.relative_to(root).as_posix(),
            # ON-HIS-PC, the third fact each row carries. "yes" means git has
            # it and a pull puts it there; "not-yet" means it exists only in
            # the studio's checkout; nothing measured means git could not be
            # asked, and is never rendered as "not-yet".
            "onHisPc": ("yes" if p.name in tracked else "not-yet")
            if git_answered else NOTHING,
        })
    exes = packaged_builds(root)
    tally = {}
    for r in rows:
        tally[r["label"]] = tally.get(r["label"], 0) + 1
    on_pc = sum(1 for r in rows if r["onHisPc"] == "yes")
    return rows, {
        "found": len(rows), "walked": len(bats),
        "batsAnywhere": len(all_bats),
        "batsNotAtRoot": len(all_bats) - len(bats),
        "visual": tally.get("VISUAL", 0), "text": tally.get("TEXT", 0),
        "unknown": tally.get("unknown", 0),
        "packagedBuilds": len(exes),
        "sentencesCapped": capped,
        "onHisPc": on_pc, "gitAnswered": git_answered,
    }


# ---------------------------------------------------------------------------
# QUESTION 2: WHAT STATE IS EACH AREA IN.
#
# THE STATE WORD IS DERIVED AND THE MEMBERSHIP IS NAMED. An area names a set of
# gates from the simulation's own ALL GATES line and, where it has one, a
# question that a committed key would have to answer. The gates' verdicts and
# the keys' presence are read every run; only which gate belongs to which area
# is written here, and that list ships its denominator (gatesMapped=N/M) with
# the unmapped names printed, so a gate added tomorrow announces itself instead
# of quietly falling out of every area.
#
# THE WORDS, and the order of the rule:
#   nothing measured  no named gate is present, OR a required question has no
#                     committed key. This is not a health word and it never
#                     reads as one.
#   failing           a named gate is present and its verdict is not "ok".
#   harness only      every named gate is ok, and no playable build exists in
#                     this tree. This is where the whole project sits today and
#                     saying it plainly is the point.
#   playable          every named gate is ok AND a packaged build exists. No
#                     area has ever printed this word; it is here so that the
#                     day one does, the page says it without an edit.
#
# WHY nothing-measured OUTRANKS failing. An unanswered question must not read
# better than an answered one, and the street is why: materialsStatus=PARTIAL
# with piecesTextured=563/593 is a staging count that cannot see a material
# that never compiled, so an area allowed to average them would print health
# over a street rendering the engine default.
# ---------------------------------------------------------------------------

WORD_NOTHING = NOTHING
WORD_FAILING = "failing"
WORD_HARNESS = "harness only"
WORD_PLAYABLE = "playable"

AREAS = (
    {
        "key": "street-and-its-look",
        "name": "the street and its look",
        "asks": "does the street render Meridian's materials",
        # NO COMMITTED KEY ANSWERS THIS. The control quads are in the frame
        # (controlQuad= lines, run 23) and the verdict prints the RULE for
        # reading them, quadReads=four-colours-means-a-texture-override-reaches
        # -the-sampler, without ever printing the reading. So the question is
        # unanswered and the area says so. The day a run emits one of these
        # keys INTO THAT FILE, this area reads it. The generator's
        # materialCompile= goes to ue-build.txt under a different name, so an
        # edit here is needed before that key counts; filed.
        "needs": ("quadChroma", "quadColoursSeen", "materialCompiles"),
        "needsSays": ("no committed key measures whether the frame shows the "
                      "bound textures. The control quads are IN the frame and "
                      "the verdict prints the rule for reading them "
                      "(quadReads=), never the reading"),
        "needsIn": UE_VERDICT,
        "gates": ("lighting", "lamps", "reflect", "bloom", "grain", "vignette",
                  "ao", "post", "framing", "screenshots", "frame", "traffic",
                  "dressing"),
        # Printed underneath, LABELLED AS NOT ANSWERING IT.
        "readings": (UE_VERDICT, ("shotDistinctBuckets@vign_camA_day",
                                  "materialsStatus", "piecesTextured",
                                  "sceneStatus", "piecesEmitted")),
    },
    {
        "key": "people-and-their-memory",
        "name": "the people and their memory",
        "asks": "do they perceive, remember and gossip",
        "needs": (),
        "needsIn": SIM_VERDICT,
        "gates": ("knowledge", "retelling", "ghost", "provenance", "confab",
                  "companionSight", "perception", "population", "npcsMoved",
                  "crowd", "bodies", "witnessCar"),
        "readings": (SIM_VERDICT, ("gossipHeat", "knownLeads", "witnesses",
                                   "npcs", "pop")),
    },
    {
        "key": "conversation",
        "name": "conversation",
        "asks": "can the player hold a real spoken exchange",
        "needs": (),
        "needsIn": SIM_VERDICT,
        "gates": ("beats", "claims", "deedClaims", "ui", "font", "phones"),
        "readings": (SIM_VERDICT, ("checks", "confronts", "labels")),
    },
    {
        "key": "voice",
        "name": "voice",
        "asks": "does anybody actually speak a line",
        # NO GATE WATCHES THIS. None of the simulation's gates is a speech
        # gate: the names are read off the ALL GATES line every run and the
        # unmapped list below proves the set was walked rather than assumed.
        "needs": ("speechGate",),
        "needsSays": ("not one of the gates in the run is a speech gate, so "
                      "nothing watches whether a line is ever spoken"),
        "needsIn": SIM_VERDICT,
        "gates": (),
        "readings": (SIM_VERDICT, ("speechSpoken", "speechLive",
                                   "speechPlayed", "speechAsked",
                                   "speechVoices")),
    },
    {
        "key": "the-crime-loop",
        "name": "the crime loop",
        "asks": "does a job run, pay and come back at you",
        "needs": (),
        "needsIn": SIM_VERDICT,
        "gates": ("actOne", "actTwo", "actThree", "jobRan", "takingsBanked",
                  "launder", "disguise", "discredit", "law", "suspicionActs",
                  "killings", "blood", "disposal", "threat", "accident",
                  "harm", "carry", "secretReachedDay", "empire", "fall",
                  "allegiance", "budgets", "economy", "ops", "access",
                  "dayJob"),
        "readings": (SIM_VERDICT, ("jobsDone", "jobsMissed", "takings",
                                   "peakHeat")),
    },
    {
        "key": "the-worlds-props",
        "name": "the world's props",
        "asks": "is the town dressed with its own things",
        "needs": (),
        "needsIn": SIM_VERDICT,
        "gates": ("places", "household", "worldText", "score", "mix", "preset",
                  "scoreAudible", "ossei"),
        "readings": (SIM_VERDICT, ("adopted", "refused")),
    },
)

GATES_RX = re.compile(r"ALL GATES:(.*)$", re.M)
GATE_RX = re.compile(r"^([A-Za-z]+)\s+([A-Za-z0-9_]+)")
STAMP_RX = re.compile(r"^#[^\n]*?\b([0-9a-f]{7,40})\s+@(\d+)", re.M)


def read_stamp(root, rel):
    """(sha, epoch) from a verdict file's line 1, which by the project's own
    rule names the commit it was measured on. Parsed with a regex and never
    echoed: line 1 of the simulation verdict carries an em-dash, and quoting it
    would redden the formatting law on a page nobody edited."""
    p = Path(root) / rel
    if not p.is_file():
        return None, None
    m = STAMP_RX.search(p.read_text(encoding="utf-8", errors="replace")[:400])
    return (m.group(1), int(m.group(2))) if m else (None, None)


def read_gates(root, rel=SIM_VERDICT):
    """{gate: verdict} off the LAST ALL GATES line in the file, plus how many
    such lines there were. Last-wins, and named so: the file is rewritten per
    run but a reader who found two would otherwise be merging two moments."""
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
    """The LAST value of key=value in a file, or None.

    LAST-WINS, and named so wherever it is printed. A reading whose key appears
    once per shot needs the shot naming or it is two moments under one name:
    write the key as "shotDistinctBuckets@vign_camA_day" and the value is taken
    from the last line that also carries that token, so the number and the
    frame it describes arrive together. shotDistinctBuckets alone read 19 of
    32768 on the first run of this tool, which is the WET NIGHT frame, and
    would have been read as the day street.
    """
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
    required question is asked, so that the day a run emits the key the area
    starts reading it without an edit here."""
    p = Path(root) / rel
    if not p.is_file():
        return False
    text = p.read_text(encoding="utf-8", errors="replace")
    return re.search(r"\b%s[A-Za-z0-9_]*=" % re.escape(prefix), text) is not None


def area_states(root):
    """(areas, reading). Every word derived, every number named with its file."""
    root = Path(root)
    gates, gmeta = read_gates(root)
    playable = len(packaged_builds(root)) > 0
    mapped = set()
    out = []
    for spec in AREAS:
        named = [g for g in spec["gates"]]
        mapped.update(named)
        seen = {g: gates[g] for g in named if g in gates}
        bad = sorted(g for g, v in seen.items() if v.lower() != "ok")
        missing_q = [n for n in spec["needs"]
                     if not key_present(root, spec["needsIn"], n)]
        if missing_q:
            word, why = WORD_NOTHING, (
                "%s. What would answer it: any of %s in %s"
                % (spec.get("needsSays", "no committed key answers it"),
                   "/".join(spec["needs"]), spec["needsIn"]))
        elif not seen:
            word, why = WORD_NOTHING, (
                "none of the %d gate(s) this area names is in %s"
                % (len(named), SIM_VERDICT))
        elif bad:
            word, why = WORD_FAILING, ("%d of %d named gate(s) not ok: %s"
                                       % (len(bad), len(seen), ",".join(bad)))
        elif playable:
            word, why = WORD_PLAYABLE, "every named gate ok and a build exists"
        else:
            word, why = WORD_HARNESS, (
                "%d of %d named gate(s) ok in %s, and no playable build exists "
                "in this tree" % (len(seen), len(named), SIM_VERDICT))
        src, keys = spec["readings"]
        vals = [(k, read_key(root, src, k)) for k in keys]
        out.append(dict(spec, word=word, why=why, gatesSeen=len(seen),
                        gatesNamed=len(named), gatesBad=len(bad),
                        missing=missing_q, readings=vals, readingsFrom=src))
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
        "playable": playable,
        "nothingMeasured": words.get(WORD_NOTHING, 0),
        "failing": words.get(WORD_FAILING, 0),
        "harnessOnly": words.get(WORD_HARNESS, 0),
    }


# ---------------------------------------------------------------------------
# QUESTION 3: WHAT ARE THE NEXT THREE THINGS.
#
# THE RULE IS ON THE PAGE because "why those three" is half the answer. It is
# read out of production/NOW.md, which is where the standing order is ruled,
# and never out of the queue's file numbers: the queue holds 97 ready items and
# its lowest three numbers (002, 004, 006) are from three weeks ago. A list
# sorted by a number nobody uses for priority is an invented plan.
#
# WHEN THE RULING NAMES FEWER THAN THREE, THE PAGE SAYS SO. Today's ruling says
# "TWO ITEMS, IN THIS ORDER, AND NOTHING ELSE", so the third slot prints the
# words "nothing measured" with the reason. Filling it from the queue would be
# this page inventing a plan, which is the one thing Jafar asked it not to do.
# ---------------------------------------------------------------------------

NEXT_RULE = (
    "read from production/NOW.md: of the sections whose heading carries a "
    "date, the ones carrying the NEWEST date and the word RULED or ORDER, in "
    "document order, and from each its numbered items in their printed order. "
    "Everything else in that file is a report of what happened, not an "
    "instruction. Where the ruling names fewer than three, the empty slot says "
    "so rather than being filled from the queue."
)
DATE_RX = re.compile(r"\b(20\d\d-\d\d-\d\d)\b")
RULING_RX = re.compile(r"\b(RULED|ruled|ORDER|order)\b")
ITEM_RX = re.compile(r"^(\d+)\.\s+(.*)$")
QNUM_RX = re.compile(r"(?i)\bqueue\s*[- ]?(\d{2,3})\b")


def next_items(root):
    """(items, reading). Items are ordered and carry the heading that ruled
    them, so the page can print WHY those and not others."""
    root = Path(root)
    p = root / NOW_FILE
    if not p.is_file():
        return [], {"nowPresent": False, "sections": 0, "dated": 0,
                    "ruling": 0, "named": 0, "newest": None}
    text = p.read_text(encoding="utf-8", errors="replace")
    chunks = re.split(r"^## ", text, flags=re.M)[1:]
    secs = []
    for c in chunks:
        head = c.splitlines()[0].strip()
        d = DATE_RX.findall(head)
        secs.append({"head": head, "body": c, "date": max(d) if d else None,
                     "ruling": bool(RULING_RX.search(head))})
    dated = [s for s in secs if s["date"]]
    newest = max((s["date"] for s in dated), default=None)
    chosen = [s for s in dated
              if s["date"] == newest and s["ruling"]]
    items = []
    for s in chosen:
        for line in s["body"].splitlines():
            m = ITEM_RX.match(line)
            if not m:
                continue
            said, bit, orig = cap_text(re.sub(r"\*\*", "", m.group(2)),
                                       ITEM_CAP)
            qn = QNUM_RX.search(m.group(2))
            qfile, qstatus = None, None
            if qn:
                hits = sorted((root / QUEUE_DIR).glob(qn.group(1) + "-*.md")) \
                    if (root / QUEUE_DIR).is_dir() else []
                if hits:
                    qfile = hits[0].relative_to(root).as_posix()
                    sm = re.search(r"^STATUS:\s*([^\n.]+)",
                                   hits[0].read_text(encoding="utf-8",
                                                     errors="replace"), re.M)
                    qstatus = sm.group(1).strip() if sm else None
            items.append({"text": said, "bit": bit, "chars": orig,
                          "from": s["head"], "queue": qfile,
                          "status": qstatus})
    return items, {"nowPresent": True, "sections": len(secs),
                   "dated": len(dated), "ruling": len(chosen),
                   "named": len(items), "newest": newest,
                   "headings": [s["head"] for s in chosen]}


# ---------------------------------------------------------------------------
# THE MATERIAL CHANGE DETECTOR.
#
# Jafar wants the link sent when this page changes MATERIALLY, so "materially"
# is defined here in code rather than judged by whoever is looking. The
# material fields are exactly three, and they are the three questions:
#   q1  the set of runnable things and each one's VISUAL or TEXT label
#   q2  each area's state word
#   q3  the ordered next-three
# NOT MATERIAL, deliberately: the generation time, the commit, the page bytes,
# and every number that moves without moving a word (piecesTextured 563 to 564
# is not a message). A regenerated timestamp must never wake his phone.
#
# WHERE THE PREVIOUS READING COMES FROM: the page itself. The digest is written
# into map.html as a comment, so the run about to overwrite it reads its
# predecessor out of the file on disk. No sidecar state file to lose, and it
# works the same on the PC and in a CI checkout. NO PREVIOUS PAGE IS NOT "no
# change": it prints nothing-measured, because a first run cannot tell a stable
# page from an unseen one.
# ---------------------------------------------------------------------------

DIGEST_RX = re.compile(r"mapDigest=([0-9a-f]{12})")


def material_fields(rows, areas, items):
    """The canonical material state, as sorted whitespace-free strings."""
    q1 = sorted("%s|%s|%s" % (r["name"].replace(" ", "_"), r["label"],
                              r["onHisPc"].replace(" ", "-"))
                for r in rows)
    q2 = ["%s|%s" % (a["key"], a["word"].replace(" ", "-")) for a in areas]
    q3 = ["%d|%s" % (i + 1, re.sub(r"\W+", "-", it["text"]).strip("-")[:60])
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
# THE PAGE. Every px in the stylesheet is one of the constants above, so the
# height this file computes is the height the browser lays out.
# ---------------------------------------------------------------------------

CSS = """
:root { color-scheme: dark light; }
* { box-sizing: border-box; }
body { margin: 0; padding: %(pad)dpx; background: #14161a; color: #e9e9ea;
  font: %(font)dpx/1.32 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
  sans-serif; -webkit-text-size-adjust: 100%%; overflow-wrap: anywhere; }
.head { display: flex; justify-content: space-between; align-items: baseline;
  height: %(head)dpx; line-height: %(head)dpx; }
h1 { font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase;
  color: #cfd3d8; margin: 0; font-weight: 700; }
.head .n { font-size: 10px; color: #8b9198; }
h2 { font-size: 11px; letter-spacing: 0.09em; text-transform: uppercase;
  color: #8b9198; margin: %(sgap)dpx 0 %(h2g)dpx; height: %(h2)dpx;
  line-height: %(h2)dpx; font-weight: 700; }
h2 b { color: #cfd3d8; font-weight: 700; }
.row { margin: 0 0 %(rgap)dpx; }
.t { font-weight: 600; color: #f2f3f4; }
.s { font-size: %(small)dpx; color: #9aa0a8; display: block; }
.how { font-size: %(small)dpx; color: #cfd3d8; }
.tag { display: inline-block; border-radius: 4px; padding: 0 5px;
  font-size: 10px; font-weight: 700; letter-spacing: 0.06em;
  vertical-align: 1px; margin-right: 5px; }
.TEXT { background: #3a3f47; color: #dfe3e8; }
.VISUAL { background: #1c6b33; color: #eaffef; }
.unknown { background: #7a1f1f; color: #ffe9e9; }
.w { font-weight: 700; }
.w-playable { color: #6fd08c; }
.w-harness { color: #d7b46a; }
.w-failing { color: #ff8f8f; }
.w-nothing { color: #9aa0a8; }
.n3 { margin: 0 0 %(rgap)dpx; }
.n3 .k { color: #7fb2ff; font-weight: 700; margin-right: 4px; }
.foot { margin: %(sgap)dpx 0 0; font-size: 10px; color: #767c84; }
.foot a { color: #7fb2ff; text-decoration: none; margin-right: 12px; }
.sheet { display: none; }
.sheet:target { display: block; position: fixed; top: 0; right: 0; bottom: 0;
  left: 0; background: #14161a; padding: 14px 12px 28px; overflow-y: auto;
  font-size: 13px; line-height: 1.4; }
.sheet h3 { font-size: 16px; margin: 0.2rem 0 0.6rem; }
.sheet dt { font-size: 10px; letter-spacing: 0.09em; text-transform: uppercase;
  color: #8b9198; margin-top: 0.7rem; }
.sheet dd { margin: 0.15rem 0 0; }
.sheet pre { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular,
  Menlo, monospace; font-size: 11px; color: #b9bec5; margin: 0.3rem 0 0; }
.close { display: inline-block; color: #7fb2ff; text-decoration: none;
  font-size: 13px; padding: 6px 0; }
@media (prefers-color-scheme: light) {
  body { background: #f6f7f9; color: #1b1e22; }
  h1 { color: #2c3238; }
  .head .n, h2, .s, .foot { color: #5a6068; }
  .t { color: #101317; }
  .how { color: #333940; }
  .TEXT { background: #dfe3e8; color: #23282e; }
  .unknown { background: #ffd7d7; color: #7a1f1f; }
  .w-harness { color: #8a6a15; }
  .w-failing { color: #a51f1f; }
  .w-nothing { color: #5a6068; }
  .w-playable { color: #1c6b33; }
  .sheet:target { background: #f6f7f9; }
  .sheet dt { color: #5a6068; }
  .sheet pre { color: #3a4047; }
}
"""

PAGE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>LEDGER map: what you can run, where it stands, what is next</title>
<style>%s</style>
</head>
<body id="map">
%s
</body>
</html>
"""


def css():
    return CSS % {"pad": BODY_PAD_PX, "font": BODY_FONT_PX, "head": HEAD_PX,
                  "h2": H2_PX, "h2g": H2_GAP_PX, "rgap": ROW_GAP_PX,
                  "sgap": SECTION_GAP_PX, "small": SMALL_FONT_PX}


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def word_class(word):
    return {WORD_PLAYABLE: "w-playable", WORD_HARNESS: "w-harness",
            WORD_FAILING: "w-failing"}.get(word, "w-nothing")


def q1_html(rows, reading):
    if not rows:
        return ('<h2>1 <b>what you can run today</b></h2>'
                '<p class="row"><span class="t">%s</span><span class="s">no '
                '.bat file was found in the repository root, so the walk found '
                'nothing to offer. That is a broken walk, not an empty '
                'project.</span></p>' % esc(NOTHING))
    shown = rows[:RUNNABLE_SHOWN]
    body = []
    for r in shown:
        if r["onHisPc"] == "yes":
            how = "double-click %s" % r["name"]
        elif r["onHisPc"] == "not-yet":
            how = ("double-click %s, but NOT YET: it is not committed, so it "
                   "is not on your PC until it lands" % r["name"])
        else:
            how = ("double-click %s. Whether it is on your PC is %s: git could "
                   "not be asked here" % (r["name"], NOTHING))
        # OR WHAT TO TYPE, where the file starts something a person could run
        # straight. Derived in classify() from the project it launches, so it
        # cannot name a project that is not there.
        if r["hint"]:
            how += ", or type: %s" % r["hint"]
        body.append(
            '<p class="row" data-run="%s"><span class="tag %s">%s</span>'
            '<span class="t">%s</span>'
            '<span class="s">%s</span>'
            '<span class="s how">%s</span></p>'
            % (esc(r["onHisPc"]), esc(r["label"]), esc(r["label"]),
               esc(r["name"]), esc(r["about"]), esc(how)))
    more = ""
    if len(rows) > len(shown):
        more = ('<p class="row"><span class="s">(+%d more not shown of %d '
                'found)</span></p>' % (len(rows) - len(shown), len(rows)))
    tail = ('<p class="row"><span class="s">%d of %d walked are TEXT: they '
            'print words in a console window. VISUAL is %d of %d, because no '
            'packaged game build exists in this tree (%d found). %d of %d are '
            'committed and so are on your PC after a pull. The label is read '
            'from what each file starts, not from its name.</span></p>'
            % (reading["text"], reading["found"], reading["visual"],
               reading["found"], reading["packagedBuilds"],
               reading["onHisPc"], reading["found"]))
    return ('<h2>1 <b>what you can run today</b></h2>%s%s%s'
            % ("".join(body), more, tail))


def age_sentence(reading):
    """HOW OLD THE RUN BEHIND THE WORDS IS, in plain words with its commit.

    A state word derived from a three-day-old run reads as today unless the
    page says otherwise, which is the stale-reading fault this project has
    already been bitten by. NO BOUND IS SET ON THE AGE here: nobody has printed
    a series of these ages yet, so the number is printed and not judged.
    """
    bits = []
    for label, sha, when in (("the simulation", reading["simSha"],
                              reading["simWhen"]),
                             ("the street", reading["ueSha"],
                              reading["ueWhen"])):
        if not sha or not when:
            bits.append("%s: %s" % (label, NOTHING))
            continue
        hours = (datetime.datetime.now(datetime.timezone.utc)
                 - datetime.datetime.fromtimestamp(
                     when, datetime.timezone.utc)).total_seconds() / 3600.0
        bits.append("%s was measured on commit %s, %d hour(s) ago"
                    % (label, sha, int(hours)))
    return "The run behind these words: " + "; ".join(bits) + "."


def q2_html(areas, reading):
    body = []
    for a in areas:
        vals = [(k, v) for k, v in a["readings"] if v is not None]
        nums = " ".join("%s=%s" % (k, v) for k, v in vals[:READINGS_SHOWN])
        # THE CAP SAYS WHEN IT BITES. Four readings out of six read as "these
        # are the numbers there are", which is the finding-shaped truncation
        # instruments.md names.
        if len(vals) > READINGS_SHOWN:
            nums += " (+%d more not shown of %d)" % (len(vals) - READINGS_SHOWN,
                                                     len(vals))
        if vals:
            ev = "%s, from %s" % (nums, a["readingsFrom"])
            if a["word"] == WORD_NOTHING:
                ev = ("these exist and do NOT answer it: %s, from %s"
                      % (nums, a["readingsFrom"]))
        else:
            ev = "%s: no reading found in %s" % (NOTHING, a["readingsFrom"])
        body.append(
            '<p class="row" data-area="%s"><span class="t">%s</span> '
            '<span class="w %s">%s</span>'
            '<span class="s">%s</span>'
            '<span class="s">%s</span></p>'
            % (esc(a["key"]), esc(a["name"]), word_class(a["word"]),
               esc(a["word"]), esc(a["why"]), esc(ev)))
    tail = ('<p class="row"><span class="s">%d area(s): %d say %s, %d failing, '
            '%d harness only. Words are derived from %d of %d gate(s) in %s; '
            'no status anybody typed sets a word here. %s</span></p>'
            % (reading["areas"], reading["nothingMeasured"], NOTHING,
               reading["failing"], reading["harnessOnly"],
               reading["gatesMapped"], reading["gatesInVerdict"], SIM_VERDICT,
               esc(age_sentence(reading))))
    return '<h2>2 <b>what state each area is in</b></h2>%s%s' \
        % ("".join(body), tail)


def q3_html(items, reading):
    body = []
    for i in range(NEXT_ASKED):
        if i < len(items):
            it = items[i]
            if it["queue"]:
                extra = '<span class="s">%s%s</span>' % (
                    esc(it["queue"]),
                    esc(", STATUS: " + it["status"]) if it["status"] else "")
            else:
                extra = ('<span class="s">no queue file is named by this '
                         'item, so there is no task file behind it</span>')
            body.append('<p class="n3"><span class="k">%d</span>'
                        '<span class="t">%s</span>%s</p>'
                        % (i + 1, esc(it["text"]), extra))
        else:
            body.append('<p class="n3"><span class="k">%d</span>'
                        '<span class="w w-nothing">%s</span>'
                        '<span class="s">the ruling names %d item(s), not %d. '
                        'A third filled from the queue would be this page '
                        'inventing a plan.</span></p>'
                        % (i + 1, esc(NOTHING), len(items), NEXT_ASKED))
    if len(items) > NEXT_ASKED:
        body.append('<p class="n3"><span class="s">(+%d more named by the '
                    'ruling, not shown of %d)</span></p>'
                    % (len(items) - NEXT_ASKED, len(items)))
    src = reading.get("headings") or []
    where = ("; ".join(h for h in src[:2])) if src else NOTHING
    tail = ('<p class="n3"><span class="s">Why these: %s Ruled by: %s</span>'
            '</p>' % (esc(NEXT_RULE), esc(where)))
    return '<h2>3 <b>the next three</b></h2>%s%s' % ("".join(body), tail)


def about_html(model, now, lines):
    return ('<section class="sheet" id="about">'
            '<a class="close" href="#map">close</a>'
            '<h3>how this page was made</h3>'
            '<p>Generated by %s at %s UTC from commit %s. Every number above '
            'names the file it was read from. Nothing on this page is a status '
            'anybody typed.</p>'
            '<dl><dt>what counts as a material change</dt><dd>%s</dd>'
            '<dt>the readings behind it</dt><dd><pre>%s</pre></dd></dl>'
            '<a class="close" href="#map">close</a></section>'
            % (esc(TOOL), esc(now.strftime("%Y-%m-%d %H:%M")),
               esc(model["commit"]), esc(MATERIAL_RULE),
               esc("\n".join(lines))))


MATERIAL_RULE = (
    "The link is sent again only when one of three things changes: a runnable "
    "thing appears, disappears or changes its VISUAL/TEXT label; an area "
    "changes its state word; or the next-three changes. The generation time, "
    "the commit and every number that moves without moving a word are NOT "
    "material and never send a message. No previous page is not 'no change': "
    "it reads nothing measured, because a first run cannot tell a stable page "
    "from an unseen one."
)


def foot_html():
    links = "".join('<a href="%s">%s</a>' % (esc(h), esc(t))
                    for h, t in SIBLINGS)
    return ('<p class="foot">%s<a href="#about">how this page was made</a></p>'
            % links)


def q1_height(rows, reading):
    """The height of the title plus question 1, in CSS px, from the same
    constants the stylesheet is generated from. A sum, not a sample, and the
    printed line says computed-not-measured."""
    w = PHONE_WIDTH_PX - 2 * BODY_PAD_PX
    h = BODY_PAD_PX + HEAD_PX + SECTION_GAP_PX + H2_PX + H2_GAP_PX
    for r in rows[:RUNNABLE_SHOWN]:
        h += LINE_PX * wrap_lines(r["label"] + " " + r["name"], BODY_FONT_PX, w)
        h += SMALL_LINE_PX * wrap_lines(r["about"], SMALL_FONT_PX, w)
        h += SMALL_LINE_PX * wrap_lines("double-click " + r["name"],
                                        SMALL_FONT_PX, w)
        h += ROW_GAP_PX
    return h


def worst_row(rows):
    """The row closest to overflowing, with its predicted lines. A PEAK, named
    as one: the median row fits and would hide the only case that matters."""
    w = PHONE_WIDTH_PX - 2 * BODY_PAD_PX
    worst = (NOTHING, 0)
    for r in rows:
        n = wrap_lines(r["about"], SMALL_FONT_PX, w)
        if n > worst[1]:
            worst = (r["name"].replace(" ", "_"), n)
    return worst


def typed_inventory(root):
    """THE TYPED STATUS BOARD, COUNTED AND DISARMED.

    production/systems-inventory.json carries a status word per system that a
    person types. It used to be the whole of this page and Jafar has now said
    it did not give him an overview, so it sets NO word here. It is still
    counted, behind the tap, labelled as typed, so that the difference between
    what somebody wrote down and what a run measured is visible rather than
    quietly gone. Counted and not validated: tools/systems-inventory-check.py
    owns validation and this page reads no word from the file, so a second
    validator here would be a second implementation of one idea.
    """
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


def build(root, now, out_path=None):
    """The whole page and the model behind it."""
    root = Path(root)
    rows, r1 = find_runnables(root)
    areas, r2 = area_states(root)
    items, r3 = next_items(root)
    commit = (GLANCE.git(root, "rev-parse", "--short", "HEAD") or NOTHING)
    fields = material_fields(rows, areas, items)
    dig = digest_of(fields)
    prev_f = previous_fields(out_path) if out_path else None
    prev_d = previous_digest(out_path) if out_path else None
    groups = changed_groups(fields, prev_f)
    if prev_d is None:
        change = "nothing-measured"
    elif prev_d != dig:
        change = "yes"
    else:
        change = "no"
    model = {"rows": rows, "r1": r1, "areas": areas, "r2": r2,
             "items": items, "r3": r3, "commit": commit, "fields": fields,
             "digest": dig, "prevDigest": prev_d, "change": change,
             "changedGroups": groups, "q1Px": q1_height(rows, r1),
             "worstRow": worst_row(rows)}
    detail = [
        "runnableFound=%d/%d-bat-file(s)-in-the-root visual=%d/%d text=%d/%d "
        "unknown=%d/%d onHisPc=%d/%d packagedBuilds=%d "
        "batsElsewhere=%d/%d-in-the-whole-tree gitAnswered=%s"
        % (r1["found"], r1["walked"], r1["visual"], r1["found"], r1["text"],
           r1["found"], r1["unknown"], r1["found"], r1["onHisPc"],
           r1["found"], r1["packagedBuilds"],
           r1["batsNotAtRoot"], r1["batsAnywhere"],
           "yes" if r1["gitAnswered"] else "no"),
        "areas=%d nothingMeasured=%d/%d failing=%d/%d harnessOnly=%d/%d"
        % (r2["areas"], r2["nothingMeasured"], r2["areas"], r2["failing"],
           r2["areas"], r2["harnessOnly"], r2["areas"]),
        "gatesMapped=%d/%d-in-%s gateLines=%d/last-wins"
        % (r2["gatesMapped"], r2["gatesInVerdict"], SIM_VERDICT,
           r2["gateLines"]),
        "gatesUnmapped=%s%s"
        % ("/".join(r2["unmapped"][:UNMAPPED_SHOWN]) or NOTHING.replace(" ", "-"),
           (" (+%d more not shown of %d)"
            % (len(r2["unmapped"]) - UNMAPPED_SHOWN, len(r2["unmapped"])))
           if len(r2["unmapped"]) > UNMAPPED_SHOWN else ""),
        "simVerdictCommit=%s ueVerdictCommit=%s pageCommit=%s"
        % (r2["simSha"] or NOTHING.replace(" ", "-"),
           r2["ueSha"] or NOTHING.replace(" ", "-"), commit),
        "nextNamed=%d/%d-asked newestRulingDate=%s ruledSections=%d/%d-dated"
        % (r3["named"], NEXT_ASKED, r3["newest"] or NOTHING.replace(" ", "-"),
           r3["ruling"], r3["dated"]),
        "q1HeightPx=%d/%d-budget-at-%dwide computed-not-measured "
        "worstAboutLines=%d-on-%s" % (model["q1Px"], ONE_SCREEN_PX,
                                      PHONE_WIDTH_PX, model["worstRow"][1],
                                      model["worstRow"][0]),
        "mapDigest=%s mapDigestPrev=%s mapMaterialChange=%s mapChangedFields=%s"
        % (dig, prev_d or NOTHING.replace(" ", "-"), change,
           ("/".join(groups) if groups else "none") if groups is not None
           else NOTHING.replace(" ", "-")),
    ]
    inv = typed_inventory(root)
    # THE QUEUE'S OWN COUNT, through the one counter this repository has, and
    # printed to back the next-three rule rather than to choose the items. 97
    # ready items whose lowest three numbers are from three weeks ago is the
    # evidence that a file-number sort would be an invented plan.
    try:
        qc = load_queue_check().count_queue(root)
    except Exception:                                            # noqa: BLE001
        qc = None
    detail.append(
        "queueReady=%s queueBlocked=%s queueDone=%s countedBy=tools/"
        "queue-check.py/count_queue chosenBy=the-ruling-not-the-file-numbers"
        % ((qc["ready"], qc["blocked"], qc["done"]) if qc else
           ((NOTHING.replace(" ", "-"),) * 3)))
    detail.append(
        "typedInventory=%s entriesTyped=%d words=%s "
        "setsNoWordOnThisPage=true"
        % (INVENTORY, inv["entries"],
           "/".join("%s.%d" % (w, n) for w, n in sorted(inv["words"].items()))
           or NOTHING.replace(" ", "-")))
    model["inventory"] = inv
    model["detail"] = detail
    body = "\n".join([
        '<div class="head"><h1>LEDGER</h1><span class="n">%s at %s UTC</span>'
        '</div>' % (esc(commit), esc(now.strftime("%Y-%m-%d %H:%M"))),
        q1_html(rows, r1),
        q2_html(areas, r2),
        q3_html(items, r3),
        foot_html(),
        about_html(model, now, detail),
        "<!-- Generated by %s at %s UTC -->"
        % (TOOL, now.strftime("%Y-%m-%d %H:%M")),
        "<!-- mapDigest=%s mapFields=%s -->" % (dig, encode_fields(fields)),
    ])
    return PAGE % (css(), body), model


# ---------------------------------------------------------------------------
# THE CHECKS. The container has no browser, so phone-first is checked on the
# things a FILE can be asked, and then somebody opens it. Each returns
# (name, ok, printed) and every one ships its denominator. Six are the
# sibling's and are imported from tools/glance.py rather than retyped.
# ---------------------------------------------------------------------------

def check_three_questions(page, model):
    """EXACTLY THREE, IN ORDER. A fourth block is the thing that competes for
    space, and an out-of-order page answers a question he did not ask first."""
    heads = re.findall(r"<h2>(\d)\s", page)
    return ("threeQuestions", heads == ["1", "2", "3"],
            "questions=%s/1-2-3-in-order h2Count=%d/3"
            % ("/".join(heads) or NOTHING.replace(" ", "-"), len(heads)))


def check_above_fold(page, model):
    """Question 1 must end above the fold. Arithmetic from the constants the
    stylesheet is generated from, never a browser measurement."""
    h = model["q1Px"]
    return ("aboveFold", h <= ONE_SCREEN_PX,
            "q1HeightPx=%d/%d-budget rows=%d/%d-shown at %dwide "
            "computed-not-measured" % (h, ONE_SCREEN_PX,
                                       min(len(model["rows"]), RUNNABLE_SHOWN),
                                       len(model["rows"]), PHONE_WIDTH_PX))


def check_every_area_spoken(page, model):
    """Every area prints a word, and an area whose word is nothing measured
    prints those words on the page rather than an empty space."""
    n = len(model["areas"])
    on = sum(1 for a in model["areas"]
             if ('>%s<' % html.escape(a["word"], quote=True)) in page)
    silent = [a["key"] for a in model["areas"] if not a["why"]]
    return ("areasSpoken", on == n and not silent,
            "areaWordsOnPage=%d/%d nothingMeasured=%d/%d silent=%d"
            % (on, n, model["r2"]["nothingMeasured"], n, len(silent)))


AREA_ROW_RX = "<p class=\"row\" data-area=\"%s\">(.*?)</p>"


def check_no_comforting_bar(page, model):
    """THE RULE THE STREET PAID FOR. An area whose word is nothing measured may
    not carry a health word IN ITS OWN ROW, and its readings must be labelled
    as not answering the question. Measured on the rendered bytes.

    THE ROW IS FOUND BY ITS OWN data-area ATTRIBUTE and never by a character
    window after the area's name: the first draft read 900 characters forward,
    ran into the NEXT area's row, and reported the street carrying a health
    word that belonged to the people. A window that spans two rows is the
    same-instant-same-line fault in a regex.
    """
    bad, examined = [], 0
    for a in model["areas"]:
        if a["word"] != WORD_NOTHING:
            continue
        examined += 1
        m = re.search(AREA_ROW_RX % re.escape(html.escape(a["key"],
                                                          quote=True)),
                      page, re.S)
        if not m:
            bad.append(a["key"] + "/row-not-found")
            continue
        row = m.group(1)
        if WORD_HARNESS in row or WORD_PLAYABLE in row:
            bad.append(a["key"] + "/health-word-in-the-row")
        if any(v is not None for _, v in a["readings"]) and \
                "do NOT answer it" not in row:
            bad.append(a["key"] + "/readings-not-labelled")
    return ("noComfortingBar", not bad,
            "unmeasuredRowsExamined=%d/%d-areas faults=%d%s"
            % (examined, len(model["areas"]), len(bad),
               "" if not bad else " (" + ",".join(bad) + ")"))


def check_next_three(page, model):
    """Three slots always, filled or explicitly empty. A page showing two rows
    where three were asked for reads as a plan with two items in it."""
    slots = len(re.findall(r'class="k">(\d)</span>', page))
    named = model["r3"]["named"]
    empty = page.count('the ruling names')
    return ("nextThree", slots == NEXT_ASKED,
            "slots=%d/%d-asked named=%d emptySlotsExplained=%d rule=on-the-page"
            % (slots, NEXT_ASKED, named, empty))


def check_rule_printed(page, model):
    """The derivation rule for the next three is ON the page, because "why
    those three" is half of the answer he asked for."""
    ok = NEXT_RULE[:60] in page
    return ("ruleOnPage", ok, "nextRuleOnPage=%s ruleChars=%d"
            % ("yes" if ok else "MISSING", len(NEXT_RULE)))


def check_material_rule(page, model):
    """What counts as a material change is stated where he can read it, and
    the digest that decides it is in the bytes."""
    stated = MATERIAL_RULE[:60] in page
    dig = bool(DIGEST_RX.search(page))
    return ("materialRule", stated and dig,
            "materialRuleOnPage=%s digestInBytes=%s change=%s"
            % ("yes" if stated else "MISSING", "yes" if dig else "MISSING",
               model["change"]))


def check_links(page, model):
    """AT MOST THE LINKS THE REGISTER ALLOWS, and no repository markdown link.
    Jafar ruled markdown links out of anything he reads, so a page that grew
    one is refused rather than shipped."""
    hrefs = re.findall(r'href="([^"]+)"', page)
    allowed = {h for h, _ in SIBLINGS} | {"#about", "#map"}
    bad = [h for h in hrefs if h not in allowed]
    md = [h for h in hrefs if h.endswith(".md")]
    return ("links", not bad and not md,
            "hrefsExamined=%d outsideTheAllowList=%d/%d-destinations "
            "markdownLinks=%d%s"
            % (len(hrefs), len(bad), len(allowed), len(md),
               "" if not bad else " (" + ",".join(bad[:3]) + ")"))


def check_denominators(page, model):
    """EVERY ZERO SHIPS ITS DENOMINATOR. The zeros this page can print are the
    VISUAL count and the failing count; both are rendered as N of M, and this
    reads the rendered bytes to prove it."""
    pairs = re.findall(r"(\d+) of (\d+)", page) + \
        re.findall(r"(\d+)/(\d+)", page)
    visual_pair = "VISUAL is %d of %d" % (model["r1"]["visual"],
                                          model["r1"]["found"])
    return ("denominators", visual_pair in page and len(pairs) >= 3,
            "nOfMPairs=%d visualZeroHasDenominator=%s failing=%d/%d"
            % (len(pairs), "yes" if visual_pair in page else "MISSING",
               model["r2"]["failing"], model["r2"]["areas"]))


def check_cap_announced(page, model):
    """A cap that does not say it bit reads as a finding. When the runnable
    list is longer than what is shown, the page says so with its denominator."""
    bit = len(model["rows"]) > RUNNABLE_SHOWN
    said = "more not shown" in page
    return ("capAnnounced", (not bit) or said,
            "runnableShown=%d/%d cap=%d bit=%s announced=%s"
            % (min(len(model["rows"]), RUNNABLE_SHOWN), len(model["rows"]),
               RUNNABLE_SHOWN, "yes" if bit else "no",
               "yes" if said else "no"))


# tools/publish-glance.py's mapIsItsOwnStampedPage check asserts this exact
# string is in the served bytes, which is how the publisher tells the map from
# a second copy of the glance. It is another tool's assertion about this page,
# so it is checked from this side too rather than discovered when the publish
# step goes red.
PUBLISHER_MARKER = "LEDGER map"


def check_publisher_marker(page, model):
    n = page.count(PUBLISHER_MARKER)
    return ("publisherMarker", n >= 1,
            "publisherMarker=%d/1-needed-by-tools/publish-glance.py text=%s"
            % (n, PUBLISHER_MARKER.replace(" ", "-")))


THEME_RX = re.compile(r"@media \(prefers-color-scheme:\s*light\)\s*\{",
                      re.I)


def check_theme(page, model):
    """THEME-AWARE, ASKED FOR AND MEASURED ON THE BYTES. Two halves: the page
    declares it handles both schemes, and it actually paints a light one. The
    declaration alone is what a dark-only page says, so the count of light
    overrides ships beside it and a zero cannot pass."""
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
                    overrides = page[i:j].count("background:") + \
                        page[i:j].count("color:")
                    break
    return ("themeAware", declared and overrides >= 4,
            "colorSchemeDeclared=%s lightOverrides=%d/4-needed"
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

CHECKS = (check_three_questions, check_above_fold, check_every_area_spoken,
          check_no_comforting_bar, check_next_three, check_rule_printed,
          check_material_rule, check_links, check_denominators,
          check_cap_announced, check_theme, check_stamp,
          check_publisher_marker,
          check_viewport, check_width,
          check_external, check_weight, check_formatting, check_secrets)


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
FIXTURE_NOW = """# NOW

## 2026-01-01: A REPORT, not an instruction

1. this must never be read as a next item

## 2026-01-02, RULED: two things and nothing else

1. the first planted thing
2. the second planted thing, which is queue 119
"""
FIXTURE_VERDICT = """# Sim verdict abc1234 @1700000000
SimDirector: ALL GATES: ok knowledge | ok beats | ok places | ok actOne
"""


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


def selftest():
    passed, failed = 0, []
    now = datetime.datetime(2026, 9, 6, 12, 0, tzinfo=datetime.timezone.utc)

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s\n         got: %s" % (name, got))

    print("%s --selftest: ACCEPTING CASE FIRST, the live repository\n" % TOOL)
    page, model = build(ROOT, now)
    checks = run_checks(page, model)
    bad = [n for n, c, _ in checks if not c]
    ok("the live repository renders the page and every check passes "
       "(%d runnable, %d area(s), %d next item(s), %d check(s))"
       % (model["r1"]["found"], model["r2"]["areas"], model["r3"]["named"],
          len(checks)),
       model["r1"]["found"] >= 1 and not bad,
       "failed=%s" % (",".join(bad) or "none"))
    ok("RUN THE STRANGER TEST.bat is on the page, which is the thing he "
       "learned about from a transcript",
       any(r["name"] == "RUN THE STRANGER TEST.bat" for r in model["rows"]),
       [r["name"] for r in model["rows"]])
    st = [r for r in model["rows"]
          if r["name"] == "RUN THE STRANGER TEST.bat"]
    ok("and it is labelled TEXT, derived from the project it starts (%s)"
       % (st[0]["why"] if st else NOTHING),
       bool(st) and st[0]["label"] == "TEXT",
       st[0]["label"] if st else NOTHING)
    street = [a for a in model["areas"] if a["key"] == "street-and-its-look"][0]
    ok("the street's look says the words nothing measured, because no "
       "committed key answers whether the material renders (%s)" % street["why"],
       street["word"] == WORD_NOTHING and NOTHING in page,
       street["word"])
    ok("and its staging counts are on the page labelled as NOT answering it",
       "do NOT answer it" in page and "piecesTextured" in page,
       [k for k, v in street["readings"] if v is not None])
    voice = [a for a in model["areas"] if a["key"] == "voice"][0]
    ok("voice says nothing measured, because no gate in the verdict is a "
       "speech gate (%s)" % voice["why"],
       voice["word"] == WORD_NOTHING, voice["word"])

    print("\n  THE SERIES this run printed, which is what any bound here "
          "would be read off:\n")
    for line in model["detail"]:
        print("    " + line)
    print("\n    the runnable walk, one row each:")
    for r in model["rows"]:
        print("    %-30s %-8s %s" % (r["name"][:30], r["label"], r["why"]))
    print("\n    the areas, one row each:")
    for a in model["areas"]:
        print("    %-28s %-16s gates=%d/%d %s"
              % (a["name"], a["word"], a["gatesSeen"], a["gatesNamed"],
                 a["why"][:70]))
    print("\n    the next items the ruling named:")
    for i, it in enumerate(model["items"]):
        print("    %d. %s [%s]" % (i + 1, it["text"][:70],
                                   it["queue"] or "no-queue-file-named"))
    if not model["items"]:
        print("    " + NOTHING)

    print("\n  ACCEPTING 2: a planted tree, so the accepting path is proven "
          "on files this test wrote.\n")
    t = _tree({"PLANTED.bat": FIXTURE_BAT, NOW_FILE: FIXTURE_NOW,
               SIM_VERDICT: FIXTURE_VERDICT})
    p2, m2 = build(t, now)
    ok("a planted tree finds its one .bat, labels it TEXT and draws the page "
       "(runnableFound=%d/%d)" % (m2["r1"]["found"], m2["r1"]["walked"]),
       m2["r1"]["found"] == 1 and m2["rows"][0]["label"] == "TEXT"
       and not [n for n, c, _ in run_checks(p2, m2) if not c],
       [n for n, c, _ in run_checks(p2, m2) if not c])
    ok("the newest RULED section supplies the items and the older REPORT "
       "section is ignored (named=%d, newest=%s)"
       % (m2["r3"]["named"], m2["r3"]["newest"]),
       [i["text"] for i in m2["items"]] ==
       ["the first planted thing",
        "the second planted thing, which is queue 119"],
       [i["text"] for i in m2["items"]])
    ok("and slot 3 says the words nothing measured rather than borrowing "
       "from the queue", "the ruling names 2 item(s), not 3" in p2,
       p2[-300:])

    print("\n  REJECTING FIXTURES, all synthetic:\n")
    empty = _tree({"README.md": "nothing here\n"})
    p3, m3 = build(empty, now)
    ok("a tree with NO runnable entry point says so instead of drawing an "
       "empty list (runnableFound=%d/%d)" % (m3["r1"]["found"],
                                             m3["r1"]["walked"]),
       m3["r1"]["found"] == 0 and NOTHING in p3 and 'class="tag' not in p3,
       p3[:200])
    ok("and every area in that tree says nothing measured (%d/%d)"
       % (m3["r2"]["nothingMeasured"], m3["r2"]["areas"]),
       m3["r2"]["nothingMeasured"] == m3["r2"]["areas"],
       [(a["key"], a["word"]) for a in m3["areas"]])
    ok("and its next-three says the ruling named none",
       m3["r3"]["named"] == 0 and "the ruling names 0 item(s), not 3" in p3,
       m3["r3"])

    # A REJECTING KEY THAT EXISTS NOWHERE, on purpose. Pinning this to a real
    # key would break the tool the day somebody emits it, which is the failure
    # .claude/rules/instruments.md names.
    ok("a required key that exists nowhere keeps an area at nothing measured",
       not key_present(ROOT, SIM_VERDICT, "zzzNoSuchKeyEverEmitted"),
       "key_present said True for a synthetic key")
    ok("and a key that DOES exist is seen, so the probe is not a ratchet",
       key_present(ROOT, SIM_VERDICT, "speechSpoken"),
       "key_present said False for speechSpoken")

    # THE MATERIAL CHANGE DETECTOR, all three outcomes.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "map.html"
        pa, ma = build(t, now, out_path=out)
        ok("no previous page reads nothing-measured, never 'no change'",
           ma["change"] == "nothing-measured", ma["change"])
        out.write_text(pa, encoding="utf-8")
        pb, mb = build(t, now.replace(hour=23), out_path=out)
        ok("a regenerated timestamp is NOT a material change (digest %s)"
           % mb["digest"], mb["change"] == "no" and mb["digest"] == ma["digest"],
           "%s / %s vs %s" % (mb["change"], mb["digest"], ma["digest"]))
        t2 = _tree({"PLANTED.bat": FIXTURE_BAT,
                    "SECOND THING.bat": FIXTURE_BAT,
                    NOW_FILE: FIXTURE_NOW, SIM_VERDICT: FIXTURE_VERDICT})
        out2 = Path(tmp) / "map2.html"
        out2.write_text(pa, encoding="utf-8")
        pc, mc = build(t2, now, out_path=out2)
        ok("a NEW runnable thing IS a material change, and the changed field "
           "is named (%s)" % ("/".join(mc["changedGroups"] or [])),
           mc["change"] == "yes" and mc["changedGroups"] == ["q1"],
           "%s %s" % (mc["change"], mc["changedGroups"]))
        t3 = _tree({"PLANTED.bat": FIXTURE_BAT, NOW_FILE: FIXTURE_NOW})
        out3 = Path(tmp) / "map3.html"
        out3.write_text(pa, encoding="utf-8")
        pd, md = build(t3, now, out_path=out3)
        ok("an AREA changing state IS a material change (%s)"
           % ("/".join(md["changedGroups"] or [])),
           md["change"] == "yes" and "q2" in (md["changedGroups"] or []),
           "%s %s" % (md["change"], md["changedGroups"]))
        t4 = _tree({"PLANTED.bat": FIXTURE_BAT, SIM_VERDICT: FIXTURE_VERDICT,
                    NOW_FILE: FIXTURE_NOW.replace("the first planted thing",
                                                  "a different first thing")})
        out4 = Path(tmp) / "map4.html"
        out4.write_text(pa, encoding="utf-8")
        pe, me = build(t4, now, out_path=out4)
        ok("the NEXT-THREE changing IS a material change (%s)"
           % ("/".join(me["changedGroups"] or [])),
           me["change"] == "yes" and me["changedGroups"] == ["q3"],
           "%s %s" % (me["change"], me["changedGroups"]))

    # THE GUARDS MUST BE ABLE TO GO RED, or they are ratchets.
    n, c, s = check_three_questions("<h2>1 <b>a</b></h2><h2>3 <b>b</b></h2>",
                                    m2)
    ok("threeQuestions bites on a page missing question 2", not c, s)
    n, c, s = check_above_fold("", dict(m2, q1Px=ONE_SCREEN_PX + 1))
    ok("aboveFold bites on a question 1 taller than the screen", not c, s)
    fake_area = dict(AREAS[0], word=WORD_NOTHING, why="planted", gatesSeen=0,
                     gatesNamed=0, gatesBad=0, missing=["x"],
                     readings=[("piecesTextured", "563/593")],
                     readingsFrom=UE_VERDICT)
    liar = ('<p class="row" data-area="street-and-its-look">'
            '<span class="t">the street and its look</span>'
            '<span class="w">harness only</span>'
            '<span class="s">piecesTextured=563/593</span></p>')
    n, c, s = check_no_comforting_bar(liar, dict(m2, areas=[fake_area],
                                                 r2=dict(m2["r2"],
                                                         nothingMeasured=1)))
    ok("noComfortingBar bites on an unmeasured area showing a health word",
       not c, s)
    n, c, s = check_links('<a href="production/NOW.md">x</a>', m2)
    ok("links bites on a repository markdown link", not c, s)
    n, c, s = check_rule_printed("<p>nothing</p>", m2)
    ok("ruleOnPage bites when the derivation rule is not printed", not c, s)
    n, c, s = check_material_rule("<p>nothing</p>", m2)
    ok("materialRule bites when the rule and the digest are absent", not c, s)
    n, c, s = check_cap_announced("<p>quiet</p>",
                                  dict(m2, rows=[{}] * (RUNNABLE_SHOWN + 4)))
    ok("capAnnounced bites on a truncation that does not say it bit", not c, s)
    n, c, s = check_stamp("<p>no stamp</p>", m2)
    ok("stamp bites when the generator's dated sentence is missing", not c, s)
    n, c, s = check_theme('<meta content="dark light">', m2)
    ok("themeAware bites on a page that declares both schemes and paints only "
       "one", not c, s)
    n, c, s = check_publisher_marker("<p>not the map</p>", m2)
    ok("publisherMarker bites when the string publish-glance.py looks for is "
       "gone", not c, s)
    n, c, s = check_next_three('<span class="k">1</span>', m2)
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
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    root = Path(args.root).resolve()
    out = Path(args.out) if args.out else root / OUT_NAME
    now = parse_now(args.now) if args.now else datetime.datetime.now(
        datetime.timezone.utc)
    page, model = build(root, now, out_path=out)
    # WRITTEN EVEN WHEN IT IS THIN, and deliberately over the previous page: a
    # stale map that still looks current is worse than one that says what it
    # could not derive. The exit code carries the failure to the caller.
    out.write_text(page, encoding="utf-8")
    checks = run_checks(page, model)
    bad = [n for n, c, _ in checks if not c]
    # PER-ROW NUMBERS ON THE ROW'S LINE, whole-run numbers on the done line. A
    # grep across lines must not be able to read one row's label as the page's.
    for r in model["rows"]:
        print("map: runnable=%s label=%s onHisPc=%s why=%s file=%s"
              % (r["name"].replace(" ", "_"), r["label"],
                 r["onHisPc"].replace(" ", "-"), r["why"], r["file"]))
    for a in model["areas"]:
        print("map: area=%s word=%s gatesOk=%d/%d-named readings=%s"
              % (a["key"], a["word"].replace(" ", "-"),
                 a["gatesSeen"] - a["gatesBad"], a["gatesNamed"],
                 "/".join("%s=%s" % (k, v) for k, v in a["readings"]
                          if v is not None) or NOTHING.replace(" ", "-")))
    for i, it in enumerate(model["items"][:NEXT_ASKED]):
        print("map: next%d=%s queue=%s" % (i + 1,
                                           re.sub(r"\s+", "_", it["text"]),
                                           it["queue"] or "none"))
    if not model["r1"]["found"]:
        code, word = 2, "NOTHING-MEASURED"
    elif bad:
        code, word = 1, "REFUSED"
    else:
        code, word = 0, "DONE"
    print("map: wrote %s %s" % (out, " ".join(s for _, _, s in checks)))
    for line in model["detail"]:
        print("map: " + line)
    print("map: %s pageBytes=%d/%d-cap checksFailed=%d/%d"
          % (word, len(page.encode("utf-8")), PAGE_BYTE_CAP, len(bad),
             len(CHECKS)))
    return code


if __name__ == "__main__":
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
