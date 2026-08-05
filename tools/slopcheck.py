#!/usr/bin/env python3
"""EVERY PLAYER-FACING WORD, AGAINST THE FULL SIGNS-OF-AI-WRITING LIST.

    python3 tools/slopcheck.py            # the report
    python3 tools/slopcheck.py -v         # every hit, not just the counts
    python3 tools/slopcheck.py --selftest # the guard, both ways

WHY. Jafar, 5 August, on seeing an em dash in a bark: *"that sounds like AI
slop. did you run /humanizer on all dialogue text?"* No, I had not. Then,
when I came back having checked em dashes only: *"em dash is just one sign,
you need to run everything through /humanizer."*

He is right both times. An em dash is one of twenty-nine patterns, and
checking the one that happened to be visible is how you conclude a body of
text is clean because the tell you looked for was the tell you had in mind.

WHAT IT SCANS — and the denominator is the point, per rule 3b, because "no
slop found" and "nothing was examined" print identically otherwise:

  the bark bank        every atomic line, the ones the street actually says
  the Tier-2 cards     generated characters, the largest body of model prose
  the character cards  Lena, Rocco, Ada, Sam
  the Game layer       every authored string a player can read

WHAT IT CANNOT SEE, said out loud rather than quietly skipped. Three of the
list's patterns are not mechanical and this tool does not pretend otherwise:
elegant variation (synonym cycling across sentences), soulless rhythm (every
sentence the same length), and generic-positive-conclusion, which needs to
know what a conclusion is. Those need a person. The report says so at the
bottom instead of implying the absence of a finding is a clean bill.

A LOG LINE IS NOT DIALOGUE, and conflating them is how the first version of
this scan reported "131 em dashes in your writing" when 18 of them were
`PopulationHost: CityPlan is unbalanced`. Debug strings are separated and
counted separately, because a false alarm about writing is worse than none:
it teaches people to ignore the tool.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# THE PATTERNS, from the Wikipedia signs-of-AI-writing list by way of the
# humanizer skill, restricted to the ones that MEAN something in a game's
# dialogue and narration. Title-case headings and inline-header lists cannot
# occur in a spoken line, so including them would only pad the report.
PATTERNS = [
    ("significance inflation",
     r"\b(stands as|serves as|is a testament|a testament to|pivotal moment|"
     r"underscor\w+ (?:the|its)|reflects? broader|marking a (?:new|major|key)|"
     r"represents a shift|key turning point|evolving landscape|indelible mark|"
     r"deeply rooted|setting the stage for)\b"),
    ("superficial -ing tail",
     r",\s+(highlighting|underscoring|emphasizing|ensuring|reflecting|symbolizing|"
     r"contributing to|cultivating|fostering|encompassing|showcasing)\b"),
    ("promotional",
     r"\b(boasts a|nestled|in the heart of|breathtaking|must-visit|renowned for|"
     r"stunning (?:views|beauty)|rich (?:cultural|tapestry|history) )\b"),
    ("vague attribution",
     r"\b(experts (?:argue|believe|say)|observers have|industry reports|"
     r"some critics argue|several sources|it is widely (?:believed|regarded))\b"),
    ("AI vocabulary",
     r"\b(delve|tapestry|testament|vibrant|pivotal|showcase|underscore\w*|"
     r"intricacies|interplay|garner\w*|multifaceted|myriad|seamless|"
     r"leverage the|navigate the complex|robust (?:framework|solution))\b"),
    ("copula avoidance",
     r"\b(serves as a|stands as a|functions as a|represents a|boasts \w+|"
     r"features a range)\b"),
    ("negative parallelism",
     r"\b(not only\b.{0,40}\bbut also|not just\b.{0,40}\bit'?s\b|"
     r"it'?s not (?:just|merely) .{0,30}, it'?s)\b"),
    ("false range",
     r"\bfrom \w+ (?:and \w+ )?to \w+, from \w+"),
    ("filler phrase",
     r"\b(in order to|due to the fact that|at this point in time|"
     r"in the event that|has the ability to|it is important to note)\b"),
    ("excessive hedging",
     r"\b(could potentially|might possibly|may perhaps|it could be argued that)\b"),
    ("authority trope",
     r"\b(the real question is|at its core|what really matters|"
     r"the heart of the matter|the deeper issue)\b"),
    ("signposting",
     r"\b(let'?s dive|let'?s explore|let'?s break (?:this|it) down|"
     r"here'?s what you need to know|without further ado)\b"),
    ("chatbot artifact",
     r"\b(i hope this helps|certainly!|of course!|you'?re absolutely right|"
     r"would you like me to|let me know if)\b"),
    ("knowledge-cutoff hedge",
     r"\b(as of my last|up to my last training|while specific details are|"
     r"based on available information)\b"),
    # SPACED EM DASHES ONLY, AND THE DISTINCTION IS THE WHOLE POINT.
    #
    # " — " is the prose tell: a parenthetical or a pivot between two thoughts,
    # the thing LLMs reach for and the thing Wikipedia's list is about.
    #
    # An em dash with NO space before it is a different mark doing a different
    # job: a word cut off mid-utterance. "sorry, I mean—", "see— hang on",
    # "you want a ticket or— sorry, sorry". Ten of those are in the Tier-2
    # cards and one card's speech style is literally "trailing off mid-sentence
    # with 'sorry, I mean—'". Flattening them would delete the characterisation
    # they exist to carry, and a check that cannot tell a tell from a technique
    # is a check people learn to overrule — which is worse than not having it.
    ("em dash", r"\s—\s"),
    ("en dash", r"–"),
    ("curly quote", r"[‘’“”]"),
    ("ellipsis char", r"…"),
    ("emoji", r"[\U0001F300-\U0001FAFF☀-➿]"),
]

# NOT MECHANICAL. Named so the report cannot be read as a full pass.
UNCHECKABLE = [
    "elegant variation (synonym cycling across sentences)",
    "soulless rhythm (every sentence the same length and shape)",
    "generic positive conclusions (needs to know what a conclusion is)",
]

# A LOG LINE IS NOT DIALOGUE.
LOGLIKE = re.compile(r"^[A-Z]\w+:\s")

# EXACT STRINGS THAT NAME THE PATTERNS IN ORDER TO FORBID THEM. The prompt
# rules list the banned words, so any scan of the source finds them there —
# and they are the opposite of slop. Matched as exact substrings rather than
# by file, so moving the rule does not silently widen the exemption, and a
# stale entry is reported rather than left to hide the next real hit.
ALLOW = [
    "- Talk like a person, not a writer: contractions, plain words, sentences "
    "that can trail off. Say 'is' and 'has', never 'serves as' or 'boasts'. No "
    "dashes, no neat lists of three, no 'it's not just X, it's Y', and never "
    "words like delve, tapestry, testament, vibrant, crucial, pivotal, showcase.",
    " the way a person tells you what happened, plainly. No dashes, no lists of "
    "three, no words like tapestry, testament, delve, pivotal.",
]


def strings_from_cs():
    """Authored strings a player can read, from the Game and Core layers."""
    out = []
    for p in sorted((ROOT / "ledger/Assets/Scripts").rglob("*.cs")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        for s in re.findall(r'"([^"\\\n]{20,})"', txt):
            out.append((f"{p.name}", s))
    return out


def strings_from_barks():
    f = ROOT / "game-design/barks.json"
    if not f.exists():
        return []
    d = json.loads(f.read_text(encoding="utf-8"))
    out = []
    for s in d.get("slots", []):
        if any("||" in ln for ln in s["lines"]):
            continue          # pair slots are the same lines twice
        for ln in s["lines"]:
            out.append((f"barks/{s['id']}", ln))
    return out


def strings_from_cards():
    out = []
    f = ROOT / "game-design/tier2-batch-1.json"
    if f.exists():
        def walk(o, where):
            if isinstance(o, str) and len(o) >= 20:
                out.append((where, o))
            elif isinstance(o, list):
                for x in o:
                    walk(x, where)
            elif isinstance(o, dict):
                for k, v in o.items():
                    walk(v, f"{where}/{k}" if len(where) < 40 else where)
        walk(json.loads(f.read_text(encoding="utf-8")), "tier2")
    return out


def scan(items):
    hits, allowed = {}, 0
    for where, s in items:
        if s in ALLOW:
            allowed += 1
            continue
        for name, pat in PATTERNS:
            if re.search(pat, s, re.I):
                hits.setdefault(name, []).append((where, s))
    return hits, allowed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    cs = strings_from_cs()
    dialogue = [(w, s) for w, s in cs if not LOGLIKE.match(s)]
    logs = [(w, s) for w, s in cs if LOGLIKE.match(s)]
    barks = strings_from_barks()
    cards = strings_from_cards()

    surfaces = [("the bark bank", barks), ("Tier-2 cards", cards),
                ("Game/Core authored text", dialogue)]

    total = 0
    for label, items in surfaces:
        hits, allowed = scan(items)
        n = sum(len(v) for v in hits.values())
        total += n
        print(f"\n  {label}: {len(items)} strings examined, {n} hit(s)"
              + (f", {allowed} prompt-rule line(s) exempt" if allowed else ""))
        if not hits:
            print("      nothing on any of the %d patterns" % len(PATTERNS))
        for name in sorted(hits, key=lambda k: -len(hits[k])):
            print(f"      {len(hits[name]):4d}  {name}")
            if args.verbose:
                for where, s in hits[name][:6]:
                    print(f"            [{where}] {s[:76]}")

    print(f"\n  ({len(logs)} debug/log strings excluded — not player-facing)")
    print("\n  NOT CHECKED, because these are not mechanical:")
    for u in UNCHECKABLE:
        print(f"      - {u}")
    print(f"\nslopcheck: {total} hit(s) across {len(PATTERNS)} patterns and "
          f"{len(barks) + len(cards) + len(dialogue)} player-facing strings")
    return 0


def selftest():
    """RULE 5b: the case it must catch AND the case it must pass."""
    fails, ran = [], []

    def check(ok, what):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}")
        ran.append(what)
        if not ok:
            fails.append(what)

    slop = [("fake", "This stands as a testament to the vibrant tapestry of the region, "
                     "showcasing its rich cultural heritage.")]
    hits, _ = scan(slop)
    check(len(hits) >= 3, f"a slop sentence trips several patterns ({sorted(hits)})")

    clean = [("fake", "Bread's gone up again. Again."),
             ("fake", "I didn't hear that. Understand me, I didn't hear it."),
             ("fake", "Twenty years I stood that door. Rain never once asked how I was doing.")]
    hits, _ = scan(clean)
    check(not hits, f"real dialogue from this game passes ({sorted(hits)})")

    # THE ALLOW-LIST MUST NOT GO STALE. Same rule as gamecheck.py: an entry
    # that stops matching is a hole waiting for the next real hit.
    everything = {s for _, s in strings_from_cs()}
    stale = [a for a in ALLOW if a not in everything]
    check(not stale, f"every allow-list entry still exists in the source "
                     f"({len(ALLOW)} entries, {len(stale)} stale)")

    check(LOGLIKE.match("PopulationHost: CityPlan is unbalanced") is not None,
          "a debug line is recognised as a debug line")
    check(LOGLIKE.match("Bread's gone up again. Again.") is None,
          "a bark is not mistaken for a debug line")

    n = len(strings_from_barks())
    check(n > 300, f"the bark bank is actually being read ({n} lines)")

    print(f"\nslopcheck --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
