#!/usr/bin/env python3
"""Which of the shipped animation clips can any code actually reach?

Rule 6 at asset scale. The re-pick audit closed "is the clip on disk the
right motion" — 65 filled, 2 empty, 0 wrong — and the queue's open
remainder was this: *"four of five emptied slots were never playable by
any code; nothing counts which of the 65 any code reaches."* A clip with
no consumer is the animation version of `Brandish` 0 — built, plausible,
and never once running.

WHAT COUNTS AS A CONSUMER, and what deliberately does not:

  controller   the slot's name appears in a string literal in
               `CharacterPrefab.cs` — the Editor pass that builds animator
               states and blend trees. Locomotion and idle-variant slots
               are PLAYED by the speed tree with no runtime literal, so
               for those the controller IS the consumer.
  runtime      the slot's name appears in a string literal in any shipped
               script (Core + Game). This is `NpcWalker` handing a name to
               `Activity`, `React(...)`, the bark gestures — the asks.
  (nothing)    `ClipSheet.cs` is EXCLUDED: the contact sheet draws every
               slot by reading the manifest, which is exactly why it can
               never distinguish a reached clip from a stranded one.

String literals are read with comments stripped and interpolated strings
KEPT — `$"..."` is code (lint-shadow's lesson), and a slot named only in
prose must not count. THE FIRST RUN PROVED PROSE IS THE HAZARD IN THE
OTHER DIRECTION TOO: `sit` matched four files and every one was dialogue
("sit down"), so an any-literal matcher files a stranded state as
playing — the exact wrong answer for a reach report. An ask therefore
only counts on a line that touches the ask machinery (`Activity`,
`React(`, `gesture`) or inside `ActivityForPlaceNear`'s body, which is
the one writer whose returns carry no marker of their own. Today that
is every writer there is; a new writer that uses none of those words
must be added here, and the header prints the marker list so a zero
names its own blind spot (rule 3b).

A slot can therefore land in one of five states:

  PLAYS       an ActivitySlots island, and a writer asks for it
  TREE        consumed by the controller itself — locomotion clips and
              idle variants play by construction, no ask needed
  STATE-ONLY  an ActivitySlots island no writer has ever asked to enter
  DISK-ONLY   filled, and neither the controller nor any writer names it
  EMPTY       the harvest hole (smoke, thinking) — nothing to reach

This is a REPORT, not a gate (rule 2: measure first). The live codebase
is the accepting case: every claim below is checkable by opening the file
it names.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PICKS = ROOT / "ledger" / "Assets" / "Characters" / "_picks.json"
PREFAB = ROOT / "ledger" / "Assets" / "Editor" / "CharacterPrefab.cs"
SCRIPTS = ROOT / "ledger" / "Assets" / "Scripts"
EXCLUDE = {"ClipSheet.cs"}   # the diagnostic that reads ALL slots by design


def strip_comments(cs: str) -> str:
    """Remove // and /* */ comments, keep every string literal's contents.

    A tiny state walk rather than a regex, because `// inside "a string"`
    and `"quote in // comment"` both exist in this codebase and a regex
    got one of them wrong on the first try.
    """
    out = []
    i, n = 0, len(cs)
    in_str = in_line = in_block = False
    while i < n:
        c = cs[i]
        nxt = cs[i + 1] if i + 1 < n else ""
        if in_line:
            if c == "\n":
                in_line = False
                out.append(c)
        elif in_block:
            if c == "*" and nxt == "/":
                in_block = False
                i += 1
        elif in_str:
            out.append(c)
            if c == "\\" and nxt:
                out.append(nxt)
                i += 1
            elif c == '"':
                in_str = False
        else:
            if c == "/" and nxt == "/":
                in_line = True
                i += 1
            elif c == "/" and nxt == "*":
                in_block = True
                i += 1
            else:
                out.append(c)
                if c == '"':
                    in_str = True
        i += 1
    return "".join(out)


def literals(cs: str) -> list[str]:
    """Every double-quoted run in comment-stripped source. Interpolated
    strings keep their quoted parts, which is all the matcher needs."""
    return re.findall(r'"((?:[^"\\]|\\.)*)"', strip_comments(cs))


def slot_in(slot: str, lits: list[str]) -> bool:
    pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(slot) + r"(?![A-Za-z0-9_])")
    return any(pat.search(l) for l in lits)


#: A line is an ASK LINE if it touches the machinery that hands a slot
#: name to a body. `gesture` covers `BarkFor`'s out-parameter writes.
ASK_LINE = re.compile(r"Activity|React\(|gesture")


def ask_lines(cs: str) -> str:
    """The ask-bearing subset of a file: marker STATEMENTS — split on the
    semicolon, not the newline, because `Activity = a ? "x"` continues
    onto marker-less lines and a line filter dropped `lean` from its own
    accepting case on the first run (rule 5b, self-inflicted) — plus the
    whole bodies of the two provider functions whose returns hand back
    bare slot names."""
    stripped = strip_comments(cs)
    kept = [st for st in stripped.split(";") if ASK_LINE.search(st)]
    for fn in ("ActivityForPlaceNear", "BenchSeatNear"):
        m = re.search(r"string " + fn + r".*?\n(.*?)\n        \}",
                      stripped, re.S)
        if m:
            kept.append(m.group(1))
    return "\n".join(kept)


def array_block(cs: str, name: str) -> list[str]:
    """The quoted strings of one `static readonly string[] <name> = {...}`."""
    m = re.search(re.escape(name) + r"\s*=\s*\{(.*?)\}", cs, re.S)
    return re.findall(r'"([^"]+)"', m.group(1)) if m else []


def run() -> int:
    picks = json.loads(PICKS.read_text())
    slots = sorted(picks)
    filled = {s for s in slots if (picks[s] or {}).get("found")}

    prefab_src = strip_comments(PREFAB.read_text())
    prefab_lits = literals(PREFAB.read_text())
    islands = set(array_block(prefab_src, "ActivitySlots"))
    if not islands:
        print("clip-reach: could not parse ActivitySlots out of "
              "CharacterPrefab.cs — the report would misfile every island")
        return 1

    runtime_hits: dict[str, list[str]] = {s: [] for s in slots}
    walked = 0
    for f in sorted(SCRIPTS.rglob("*.cs")):
        if f.name in EXCLUDE:
            continue
        walked += 1
        lits = literals(ask_lines(f.read_text()))
        for s in slots:
            if slot_in(s, lits):
                runtime_hits[s].append(f.name)

    plays, tree, state_only, disk_only, empty = [], [], [], [], []
    for s in slots:
        asked = runtime_hits[s]
        if s not in filled:
            empty.append(s)
        elif s in islands:
            if asked:
                plays.append(s)
            else:
                state_only.append(s)
        elif slot_in(s, prefab_lits):
            tree.append(s)
        elif asked:
            # No controller state — the ask is refused at HasState. The
            # same stranded outcome as disk-only, named separately so the
            # fix (add the state) is legible from the report alone.
            disk_only.append(s + " (ASKED-NO-STATE: " + ",".join(asked) + ")")
        else:
            disk_only.append(s)

    print(f"clip-reach: {len(slots)} slot(s), {len(filled)} filled, "
          f"{walked} shipped script(s) walked, plus CharacterPrefab.cs; "
          f"ask markers: Activity / React( / gesture / "
          f"ActivityForPlaceNear / BenchSeatNear")
    print(f"\nPLAYS ({len(plays)}) — an activity island a writer asks for:")
    for s in plays:
        print(f"  {s:18s} <- {', '.join(runtime_hits[s])}")
    print(f"\nTREE ({len(tree)}) — played by the controller itself "
          f"(locomotion, idle spread):")
    for s in tree:
        print(f"  {s}")
    print(f"\nSTATE-ONLY ({len(state_only)}) — island built, no writer has "
          f"ever asked:")
    for s in state_only:
        print(f"  {s}")
    print(f"\nDISK-ONLY ({len(disk_only)}) — clip ships, nothing names it:")
    for s in disk_only:
        print(f"  {s}")
    print(f"\nEMPTY ({len(empty)}) — the harvest hole: {', '.join(empty)}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
