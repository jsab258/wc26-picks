#!/usr/bin/env python3
"""Every principal has a voice that can actually reach them.

M17.3. `VoiceBank.VoiceFor` is deliberately forgiving: an id that is not in the
cast set draws from the crowd pool instead of throwing, so the game never dies
because somebody was not cast. The cost of that kindness is that a MISCAST
principal is completely silent as a bug — they simply sound like a passer-by,
and nothing anywhere says so.

That is not hypothetical. Reconciling the two lists by hand found two
characters whose cast voice had been fetched weeks earlier and could never
play:

    CastTier1 card "# Hal"        id halvard   cast as hal
    CastTier1 card "# Sera Kest"  id sera      cast as kest

Both clips were sitting in `game-design/picked-clips/`. Both drew crowd voices.

WHY A TEXT CHECK AND NOT A UNIT TEST. The two facts live on opposite sides of
the layer line — the ids are in `Assets/Scripts/Game/CastTier1.cs` and the cast
set is in `Assets/Scripts/Core/VoiceBank.cs` — and CoreTests cannot see the
Game layer. Duplicating the id list into Core to make it testable would create
exactly the drift this check exists to catch. So it reads BOTH real files, the
way `attribution-check.py` reads the real directories.

    python3 tools/voice-cast-check.py
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TIER1 = ROOT / "ledger" / "Assets" / "Scripts" / "Game" / "CastTier1.cs"
VOICEBANK = ROOT / "ledger" / "Assets" / "Scripts" / "Core" / "VoiceBank.cs"
CLIPS = ROOT / "game-design" / "picked-clips"

# Principals the design has decided may draw from the crowd pool. EMPTY ON
# PURPOSE: a name belongs here only when somebody has decided that character
# should sound like anyone else, and writing that decision down is the point.
POOLED_BY_DESIGN = set()


def tier1_ids():
    """Every id in the tier-1 cast file, with the card name it belongs to."""
    text = TIER1.read_text(encoding="utf-8")
    # `# Name` on one line and `id: xxx` on the next is the card format.
    return re.findall(r"#\s*([A-Za-z][A-Za-z '\-]*)\r?\nid:\s*(\w+)", text)


def voicebank():
    """The cast set and the alias map, read from the source rather than
    duplicated here — a copy is a thing that goes stale."""
    text = VOICEBANK.read_text(encoding="utf-8")

    block = re.search(r"Cast\s*=\s*new HashSet<string>\s*\{(.*?)\};", text, re.S)
    cast = set(re.findall(r'"(\w+)"', block.group(1))) if block else set()

    alias = {}
    ablock = re.search(r"Alias\s*=\s*\n?\s*new Dictionary<string, string>\s*\{(.*?)\};",
                       text, re.S)
    if ablock:
        for a, b in re.findall(r'\{\s*"(\w+)"\s*,\s*"(\w+)"\s*\}', ablock.group(1)):
            alias[a] = b
    return cast, alias


def fetcher_ids():
    """The ids the voice fetcher can actually go and get clips for.

    Read from its SOURCE rather than imported: the fetcher pulls in a
    corpus library this environment cannot reach, and a check that cannot
    run where it is written is a check that decays.
    """
    import re as _re
    p = ROOT / "tools" / "voice-fetch" / "ledger_voice_fetch.py"
    if not p.exists():
        return set()
    return set(_re.findall(r'dict\(id="([a-z0-9_]+)"',
                           p.read_text(encoding="utf-8")))


def main():
    problems, unvoiced = [], []
    fetch_ids = fetcher_ids()

    cards = tier1_ids()
    cast, alias = voicebank()
    clips = {p.name.split(".")[0] for p in CLIPS.glob("*.mp3")} if CLIPS.exists() else set()

    print(f"voice-cast — {len(cards)} tier-1 principals, {len(cast)} cast voices, "
          f"{len(alias)} alias(es), {len(clips)} clip(s)\n")

    for name, ident in cards:
        name = name.strip()
        resolved = alias.get(ident, ident)
        if resolved in cast:
            via = f" (via {ident} -> {resolved})" if resolved != ident else ""
            # AND THE CLIP HAS TO EXIST. Being in the cast set is a claim; a
            # file in picked-clips is the thing that plays.
            if clips and resolved not in clips:
                problems.append(f"{name}: cast as '{resolved}' but no clip in picked-clips")
                print(f"  FAIL {name:<14} cast '{resolved}' has no clip")
            else:
                print(f"  ok   {name:<14} -> {resolved}{via}")
        elif ident in POOLED_BY_DESIGN:
            print(f"  ok   {name:<14} pooled by design")
        else:
            # UNFINISHED WORK, NOT A BREAK. M17.3 is "cast the named characters
            # with no voice", and these are exactly that list. Failing on them
            # would paint the build red for a reason everybody already knows,
            # and this project has a precedent for what that does: the font gate
            # was deliberately left reporting rather than gating, because "a
            # check that is red for a known reason is a check people learn to
            # skip". Loud, counted, and not fatal.
            # AND WHICH STAGE IT IS STUCK AT, because "not cast yet" is
            # several different jobs wearing one label and only one of
            # them is anybody's next action. On 13 Aug all four of these
            # had no entry in the FETCHER — so no clip could be fetched,
            # no voice could be picked, and the TODO read like a queue
            # item somebody was ignoring rather than an unreachable one.
            stage = ("awaiting a fetch and a pick" if ident in fetch_ids
                     else "NOT FETCHABLE — no entry in the voice fetcher")
            unvoiced.append(f"{name} (id '{ident}') — {stage}")
            print(f"  TODO {name:<14} id '{ident}' draws a crowd voice — {stage}")

    # A CAST VOICE NOBODY CAN REACH is the other half of the same fault, and it
    # is the half that found `hal` and `kest`. A clip was fetched, a speaker was
    # chosen, and no id in the game resolves to it.
    reachable = {alias.get(i, i) for _, i in cards}
    print()
    for voice in sorted(cast):
        if voice in reachable:
            continue
        # Crowd pool ids and principals defined outside tier 1 (Rocco, Ada, Sam,
        # Ellis and the rest are spawned directly) are reachable by their own
        # name, so only report a cast voice matching NOTHING at all.
        print(f"  note {voice:<14} not a tier-1 id (spawned elsewhere, or spare)")

    # AN ALIAS THAT POINTS NOWHERE is a broken map wearing a working one's
    # clothes — it would resolve an id to a voice that does not exist and fall
    # through to the pool exactly like no alias at all.
    for src, dst in sorted(alias.items()):
        if dst not in cast:
            problems.append(f"alias {src} -> {dst}, which is not a cast voice")
            print(f"  FAIL alias {src} -> {dst} is not in the cast set")

    print()
    if unvoiced:
        print(f"{len(unvoiced)} principal(s) not cast yet (M17.3, reported not gated):")
        for u in unvoiced:
            print(f"  - {u}")
    print(f"{len(problems)} problem(s)")
    for p in problems:
        print(f"  - {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
