#!/usr/bin/env python3
"""Check the brand bible against its spec and against canon.

WHY THIS SHIPS WITH THE CONTENT AND NOT AFTER IT. A brand bible with no
check is a document that decays the first time somebody adds a ninth entry,
and this project's record is mostly of documents that decayed silently.

THE MINTED NAMES ARE READ FROM canon.md, NOT FROM A LIST IN HERE. canon.md
records four brands as already minted; if this file kept its own copy of
those four, the copy would be the thing that decays, and it would decay in
the direction of agreeing with whatever the bible said. Reading the source
means a rename in either place is caught, which is the whole point.

WHAT IT DOES NOT CHECK. Whether a brand is any good, whether the register
rings true, whether the town feels British. Those are judgement and belong
to a person or to the judge, per D7. This is the mechanical half: fields
present, ids unique, dates inside the window, every entry placeable, and the
canon names untouched.
"""
import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = os.path.join(REPO, "content", "brands", "brand-bible-v1.json")
CANON = os.path.join(REPO, "canon.md")

REQUIRED = ("id", "name", "kind", "founded", "register", "physical",
            "says", "neverConfuse", "license")
KINDS = ("club", "paper", "radio", "television", "pub", "cinema", "body", "ferry")

# HOW THE MINTED LIST IS READ, and why this is code rather than a regex.
#
# Two regex attempts got it wrong in opposite directions on the same real
# sentence. canon.md writes it as a wrapped bullet whose list ends
# mid-line, with more prose after it:
#
#     - Minted: Mickey's (the pub), the Tivoli (cinema), Meridian Harbour
#       Board, Meridian Ferry. The brand bible still owes: the football
#       club, the local paper, ...
#
# Stopping at the line end split "Meridian Ferry" and produced a brand
# called "Meridian". Stopping at the last period on the line swallowed the
# owes-list and produced seven names including "the pirate radio station".
# Both returned a plausible COUNT, which is what made each convincing: the
# right number of wrong names.
#
# So it is four explicit steps that can each be tested: take the bullet and
# its wrapped continuation lines, normalise the whitespace, cut at the first
# sentence break, then split on commas. A brand name contains no ". ".
MINTED_PREFIX = "- Minted:"
SENTENCE_BREAK = ". "


def minted_from_canon(path=CANON):
    """Pull the minted brand names out of canon.md itself.

    Returns (names, note). names is None when the line cannot be found,
    which must be a FAILURE and never an empty pass: "canon lists nothing"
    and "I could not read canon" look identical otherwise, and one of them
    means the check did not run.
    """
    if not os.path.exists(path):
        return None, "canon.md not found at %s" % path
    lines = open(path, encoding="utf-8").read().split("\n")
    idx = next((i for i, l in enumerate(lines) if l.strip().startswith(MINTED_PREFIX)), None)
    if idx is None:
        return None, "canon.md has no '- Minted:' line; the source of truth could not be read"
    # The bullet, plus any indented continuation lines that belong to it.
    chunk = [lines[idx].strip()[len(MINTED_PREFIX):]]
    for l in lines[idx + 1:]:
        if not l.strip() or l.lstrip().startswith("- ") or l.startswith("#"):
            break
        if l[:1].isspace():
            chunk.append(l.strip())
        else:
            break
    body = " ".join(" ".join(chunk).split())
    # Cut at the first sentence break: the list ends, prose continues.
    cut = body.find(SENTENCE_BREAK)
    if cut != -1:
        body = body[:cut]
    body = body.rstrip(".")
    # "Mickey's (the pub), the Tivoli (cinema), Meridian Harbour Board, Meridian Ferry"
    names = []
    for part in body.split(","):
        part = part.strip()
        if not part:
            continue
        part = re.sub(r"\s*\([^)]*\)\s*$", "", part).strip()
        if part:
            names.append(part)
    return names, "read %d minted name(s) from canon.md" % len(names)


def check_bible(data, minted, window=(1988, 1992)):
    """Return a list of problem strings. Empty means clean."""
    problems = []
    brands = data.get("brands")
    if not isinstance(brands, list) or not brands:
        return ["the file holds no 'brands' list, or it is empty"]

    seen = {}
    for i, b in enumerate(brands):
        who = b.get("id") or ("entry %d" % i)
        for f in REQUIRED:
            v = b.get(f)
            if v is None or (isinstance(v, str) and not v.strip()):
                problems.append("%s: field '%s' missing or empty" % (who, f))
        if b.get("kind") and b["kind"] not in KINDS:
            problems.append("%s: kind '%s' is not one of %s" % (who, b["kind"], ", ".join(KINDS)))
        f = b.get("founded")
        if isinstance(f, int):
            if f > window[1]:
                problems.append("%s: founded %d is after the window closes (%d)" % (who, f, window[1]))
        elif f is not None:
            problems.append("%s: founded is not a year" % who)
        # PLACEABLE OR NOT FINISHED. A brand with no physical presence
        # cannot be signed, printed or parked anywhere, so it is a note
        # rather than a brand.
        phys = (b.get("physical") or "").strip()
        if phys and len(phys) < 40:
            problems.append("%s: 'physical' is too thin to place (%d chars)" % (who, len(phys)))
        if b.get("id") in seen:
            problems.append("%s: duplicate id, also at entry %d" % (who, seen[b["id"]]))
        elif b.get("id"):
            seen[b["id"]] = i

    # THE CANON NAMES, character for character.
    names = [b.get("name", "") for b in brands]
    for m in minted:
        if m not in names:
            problems.append("canon minted name '%s' is not in the bible; "
                            "renaming a canon brand is a canon violation, not an edit" % m)
    return problems


def selftest():
    """Accepting case first, then each rejection, per rule 5b."""
    ok = fail = 0

    def check(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print("  FAIL %s" % name)

    good = {"brands": [{
        "id": "x", "name": "The Meridian Argus", "kind": "paper", "founded": 1871,
        "register": "the Argus", "says": "s", "neverConfuse": "n", "license": "l",
        "physical": "a masthead, yellow vendor boards, and a late edition with the results",
    }]}
    check("ACCEPTING: a complete entry passes",
          check_bible(good, ["The Meridian Argus"]) == [])

    import copy
    for field in REQUIRED:
        bad = copy.deepcopy(good)
        del bad["brands"][0][field]
        check("rejecting: missing '%s' is caught" % field,
              any(field in p for p in check_bible(bad, [])))

    bad = copy.deepcopy(good); bad["brands"][0]["founded"] = 1998
    check("rejecting: a founding after the window", check_bible(bad, []) != [])
    bad = copy.deepcopy(good); bad["brands"][0]["kind"] = "podcast"
    check("rejecting: a kind outside the list", check_bible(bad, []) != [])
    bad = copy.deepcopy(good); bad["brands"][0]["physical"] = "a sign"
    check("rejecting: a physical too thin to place", check_bible(bad, []) != [])
    bad = copy.deepcopy(good); bad["brands"].append(copy.deepcopy(good["brands"][0]))
    check("rejecting: a duplicate id", check_bible(bad, []) != [])
    check("rejecting: a renamed canon brand",
          check_bible(good, ["Mickey's"]) != [])
    check("rejecting: an empty file is not clean", check_bible({"brands": []}, []) != [])

    # Reading canon: the failure case must be a FAILURE, not an empty pass.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "canon.md")
        open(p, "w").write("# canon\nno such line here\n")
        names, note = minted_from_canon(p)
        check("rejecting: canon with no Minted line returns None, not []", names is None)
        open(p, "w").write("- Minted: Mickey's (the pub), the Tivoli (cinema), A Board.\n")
        names, note = minted_from_canon(p)
        check("ACCEPTING: three names parsed, parentheticals stripped",
              names == ["Mickey's", "the Tivoli", "A Board"])
        # THE REAL SHAPE canon.md uses: a wrapped bullet whose list ends
        # mid-line with prose after it. Both earlier parsers failed on this
        # exact text, in opposite directions, so it is the fixture.
        open(p, "w").write(
            "## Brands and law\n"
            "- Every brand is fictional.\n"
            "- Minted: Mickey's (the pub), the Tivoli (cinema), Meridian Harbour Board, Meridian\n"
            "  Ferry. The brand bible still owes: the football club, the local paper, the pirate\n"
            "  radio station, the regional TV channel.\n"
            "\n## OPEN\n")
        names, note = minted_from_canon(p)
        check("ACCEPTING: a wrapped bullet ending mid-line yields exactly the four minted",
              names == ["Mickey's", "the Tivoli", "Meridian Harbour Board", "Meridian Ferry"])
        # THE LIVE FILE IS THE BEST ACCEPTING FIXTURE THERE IS, because it
        # is the text this tool actually has to read, and no fixture I write
        # can be fooled in the same way twice.
        live, _ = minted_from_canon()
        check("ACCEPTING: the live canon.md yields four names, none containing a full stop",
              live is not None and len(live) == 4 and not any("." in n for n in live))
        check("rejecting: a missing canon.md returns None",
              minted_from_canon(os.path.join(d, "gone.md"))[0] is None)

    print("brand-verify selftest: %d ok, %d failed" % (ok, fail))
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default=BIBLE)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    if not os.path.exists(a.file):
        print("brand-verify: nothing measured — %s does not exist."
              % os.path.relpath(a.file, REPO))
        return 1
    data = json.load(open(a.file, encoding="utf-8"))
    minted, note = minted_from_canon()
    if minted is None:
        print("brand-verify: REFUSED — %s. The canon names could not be read, so "
              "this run cannot tell a clean bible from an unchecked one." % note)
        return 2
    problems = check_bible(data, minted)
    n = len(data.get("brands", []))
    for p in problems:
        print("  PROBLEM " + p)
    print("brand-verify: %s — %d entry(ies) checked against %d required field(s), "
          "%d canon minted name(s) (%s), %d problem(s)"
          % ("clean" if not problems else "RED", n, len(REQUIRED), len(minted), note, len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
