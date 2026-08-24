#!/usr/bin/env python3
"""THE TEMPLATE CLAIM, CHECKED WHERE THE CHANGE HAPPENS — never across repos.

    python3 tools/template-sync.py                    # the check
    python3 tools/template-sync.py --sections         # what it fingerprints
    python3 tools/template-sync.py --stamp --template-sha <sha>
    python3 tools/template-sync.py --stamp --defer <queue-item>
    python3 tools/template-sync.py --selftest         # both ways

WHY. The template repo (`jsab258/game-studio`) drifted from LEDGER's process
sections within HOURS of shipping — it said the resident was Fable while
CLAUDE.md had moved to the hybrid — and the drift was caught by Jafar noticing,
not by any instrument. That is this project's oldest shape: a rule with no
trigger point decays, and the file of record is a list of proofs.

Decision 1 of `game-design/decisions-2026-08-24-shadow-gap-and-template-sync.md`
(decision 2 in that file) picks option (a) in its SAME-REPO shape, and the
shape is the whole point:

  * THIS CHECK NEVER READS THE OTHER REPO. The template checkout exists only in
    one container and not on the Windows runner, so a live cross-repo diff
    would mean something different depending on where verify ran — and a check
    that means different things in different places is not a check.
  * THE MARKER IS THE CLAIM. `.claude/template-sync.txt` records a fingerprint
    of CLAUDE.md's process sections plus either the template commit sha that
    absorbed them, or a named queue item deferring the sync. Nothing else.
  * THE JOB IS THE TRIGGER, NOT THE TRUTH. It cannot know whether the template
    really carries these words. What it CAN do is make the question unavoidable
    at the exact moment the sections change, which is the moment the failure
    needed and did not have.

WHAT IS FINGERPRINTED, and why by anchor rather than by line number. The four
process sections named in the ruling: THE STUDIO SPLIT, THE HYBRID RESIDENT,
REPORTING, AUTO MODE. An anchor is a STRUCTURAL line — a `##`..`####` heading
or a line-initial bold run — whose text begins with the section's name, so the
same words in the middle of a paragraph cannot move a section boundary (there
is a `**REPORTING (same date):**` paragraph and a `### Reporting — RETIRED`
heading in this file today, and both are structural; the first wins and the
tool prints which line it took). A section runs from its anchor to the next
anchor or the next `##` heading, whichever comes first, so the sections are
disjoint and every one prints its own line count.

EVERY ZERO SHIPS ITS DENOMINATOR. A registered section that matches NOTHING is
not silently skipped — a fingerprint over three sections instead of four looks
exactly like a fingerprint over four, so a missing anchor is exit 3, NOTHING
MEASURED, naming the section. The check prints sections found of registered and
lines covered of the file's lines on every run, green or red.

WHITESPACE IS NOT DRIFT. Each line is right-stripped and trailing blank lines
are dropped before hashing, so re-wrapping trailing spaces cannot cost anybody
a red commit — but a changed word does. Both are asserted in `--selftest`.

EXIT CODES, one per outcome, so a caller can tell them apart without parsing
prose. 0 in sync (including a properly named deferral). 1 DRIFT — the sections
changed since the marker was stamped. 2 usage. 3 NOTHING MEASURED — no
CLAUDE.md, or a registered section has no anchor in it. 4 NOTHING RECORDED —
no marker, an unparsable one, or a claim that does not name what it must
(`synced` with no template sha, `deferred` with no queue item).
"""
import argparse
import datetime
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLAUDE_MD = ROOT / "CLAUDE.md"
MARKER = ROOT / ".claude" / "template-sync.txt"
TEMPLATE_REPO = "jsab258/game-studio"

# The process sections, as (marker key, the words an anchor must start with).
# The key is space-free because it is emitted in `key=value` channels; the
# match is upper-cased so a template's `## The studio split` matches too.
SECTIONS = (
    ("THE-STUDIO-SPLIT", "THE STUDIO SPLIT"),
    ("THE-HYBRID-RESIDENT", "THE HYBRID RESIDENT"),
    ("REPORTING", "REPORTING"),
    ("AUTO-MODE", "AUTO MODE"),
)

# A structural line: a heading, or a line-initial bold run. Prose containing the
# same words cannot anchor a section — asserted both ways in the selftest.
_ANCHOR = re.compile(r"^(?:#{2,4}\s+|\*\*)\s*(.+)$")
_HEADING2 = re.compile(r"^##\s")
DIGEST = 16                 # hex chars kept per digest; 64 bits is plenty here
EXIT = {"ok": 0, "drift": 1, "usage": 2, "nothing-measured": 3,
        "nothing-recorded": 4}


def _anchor_text(line):
    """The comparable text of a structural line, or None if it is not one."""
    m = _ANCHOR.match(line)
    if not m:
        return None
    text = m.group(1)
    text = text.replace("*", " ").replace("`", " ").replace("#", " ")
    return " ".join(text.split()).upper()


def sections_of(text, registry=SECTIONS):
    """Split CLAUDE.md into the registered process sections.

    Returns a dict with the bodies, the anchors (1-based line numbers), the
    sections that matched NOTHING, and the line counts — the denominators.
    A section that matched nothing is returned in `missing` and NOT quietly
    dropped: three sections hashed instead of four produce a perfectly
    plausible fingerprint, which is rule 3b wearing a hash's clothes."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    anchors = {}
    for i, line in enumerate(lines):
        at = _anchor_text(line)
        if at is None:
            continue
        for key, words in registry:
            if key in anchors:
                continue                    # FIRST structural match wins
            if at.startswith(words.upper()):
                anchors[key] = i
                break
    starts = sorted(anchors.values())
    bodies, spans = {}, {}
    for key, start in anchors.items():
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if j in starts or _HEADING2.match(lines[j]):
                end = j
                break
        body = [l.rstrip() for l in lines[start:end]]
        while body and not body[-1]:
            body.pop()
        bodies[key] = "\n".join(body)
        spans[key] = (start + 1, end)       # 1-based, end exclusive
    missing = [key for key, _w in registry if key not in anchors]
    covered = sum(end - (start - 1) for start, end in spans.values())
    return {"bodies": bodies, "spans": spans, "missing": missing,
            "covered": covered, "lines": len(lines),
            "found": len(anchors), "registered": len(registry)}


def fingerprint_of(bodies, registry=SECTIONS):
    """Per-section digests and the whole fingerprint, in registry order.

    The ORDER and the KEYS are part of the input, so adding a section to the
    registry is itself a drift that needs a conscious re-stamp — a fingerprint
    that silently absorbs a change to what it covers is no fingerprint."""
    per, roll = {}, hashlib.sha256()
    for key, _words in registry:
        body = bodies.get(key)
        if body is None:
            continue
        d = hashlib.sha256(("%s\n%s" % (key, body)).encode("utf-8")).hexdigest()[:DIGEST]
        per[key] = d
        roll.update(("%s:%s;" % (key, d)).encode("utf-8"))
    return per, roll.hexdigest()[:DIGEST]


def read_marker(text):
    """The recorded claim, as a dict, or None when there is nothing legible.

    `#` comments and blank lines are skipped; `section=` repeats into a list.
    NONE MEANS NOTHING RECORDED, never "fine" — the caller prints those words."""
    if text is None:
        return None
    got = {"section": []}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not key or not _:
            continue
        if key == "section":
            got["section"].append(value)
        else:
            got[key] = value
    return got if got.get("fingerprint") else None


def evaluate(md_text, marker_text, registry=SECTIONS):
    """One reading: (state, exit code, summary line, detail lines).

    ONE IMPLEMENTATION, shared by the live check and every selftest fixture, so
    a fixture cannot pass against a code path the real run does not take."""
    detail = []
    if md_text is None:
        return {"state": "nothing-measured", "exit": EXIT["nothing-measured"],
                "summary": "template-sync: NOTHING MEASURED — no CLAUDE.md at "
                           "%s (0 sections of %d registered read)"
                           % (CLAUDE_MD, len(registry)), "detail": detail}

    s = sections_of(md_text, registry)
    per, fp = fingerprint_of(s["bodies"], registry)
    scope = ("sections=%d/%d lines=%d/%d" % (s["found"], s["registered"],
                                             s["covered"], s["lines"]))
    for key, _w in registry:
        if key in s["spans"]:
            a, b = s["spans"][key]
            detail.append("  %-22s lines %d-%d (%d) sha256=%s"
                          % (key, a, b, b - a + 1, per[key]))
        else:
            detail.append("  %-22s NOT FOUND — no structural anchor in CLAUDE.md"
                          % key)
    if s["missing"]:
        return {"state": "nothing-measured", "exit": EXIT["nothing-measured"],
                "summary": ("template-sync: NOTHING MEASURED — %d of %d process "
                            "section(s) have no anchor in CLAUDE.md: %s (%s). A "
                            "fingerprint over the rest would look identical to a "
                            "whole one."
                            % (len(s["missing"]), s["registered"],
                               ",".join(s["missing"]), scope)),
                "detail": detail, "fingerprint": fp}

    mk = read_marker(marker_text)
    if mk is None:
        return {"state": "nothing-recorded", "exit": EXIT["nothing-recorded"],
                "summary": ("template-sync: NOTHING RECORDED — no legible marker "
                            "at %s, so nobody has ever claimed the template "
                            "carries these sections (%s, fingerprint=%s). Stamp "
                            "it: `python3 tools/template-sync.py --stamp "
                            "--template-sha <sha>` or `--stamp --defer "
                            "<queue-item>`." % (MARKER, scope, fp)),
                "detail": detail, "fingerprint": fp}

    state = mk.get("state", "")
    sha = mk.get("templateSha", "")
    item = mk.get("queueItem", "")
    if state not in ("synced", "deferred"):
        return {"state": "nothing-recorded", "exit": EXIT["nothing-recorded"],
                "summary": ("template-sync: NOTHING RECORDED — the marker's "
                            "state=%s is not `synced` or `deferred`, so it "
                            "claims nothing checkable (%s)."
                            % (state or "<absent>", scope)),
                "detail": detail, "fingerprint": fp}
    if state == "synced" and not re.fullmatch(r"[0-9a-f]{7,40}", sha or ""):
        return {"state": "nothing-recorded", "exit": EXIT["nothing-recorded"],
                "summary": ("template-sync: NOTHING RECORDED — state=synced with "
                            "templateSha=%s. A sync claim with no commit behind "
                            "it cannot be audited later (%s)."
                            % (sha or "<absent>", scope)),
                "detail": detail, "fingerprint": fp}
    if state == "deferred" and (not item or item == "none" or " " in item):
        return {"state": "nothing-recorded", "exit": EXIT["nothing-recorded"],
                "summary": ("template-sync: NOTHING RECORDED — state=deferred "
                            "with queueItem=%s. A deferral that names no item is "
                            "the stale-plan failure the ruling rejected (%s)."
                            % (item or "<absent>", scope)),
                "detail": detail, "fingerprint": fp}

    if mk["fingerprint"] != fp:
        was = {}
        for row in mk.get("section", []):
            got = section_row(row)
            if "key" in got:
                was[got["key"]] = got.get("sha256", "")
        changed = [k for k, _w in registry if per.get(k) != was.get(k)] or \
            ["(marker records no per-section digests)"]
        return {"state": "drift", "exit": EXIT["drift"],
                "summary": ("template-sync: DRIFT — %d of %d process section(s) "
                            "changed since the marker was stamped%s: %s "
                            "(now=%s marker=%s, %s). DISCHARGE, one or the "
                            "other: sync %s now and re-stamp with `python3 "
                            "tools/template-sync.py --stamp --template-sha "
                            "<sha>`, or defer with `--stamp --defer "
                            "<queue-item>` naming a queue item."
                            % (len(changed), s["registered"],
                               " on " + mk.get("stamped", "?"),
                               ",".join(changed), fp, mk["fingerprint"], scope,
                               mk.get("templateRepo", TEMPLATE_REPO))),
                "detail": detail, "fingerprint": fp}

    if state == "deferred":
        note = ("IN SYNC WITH THE MARKER, SYNC DEFERRED — state=deferred "
                "queueItem=%s" % item)
    else:
        note = "IN SYNC — state=synced templateSha=%s" % sha
    return {"state": "ok", "exit": EXIT["ok"],
            "summary": ("template-sync: %s templateRepo=%s fingerprint=%s %s "
                        "stamped=%s"
                        % (note, mk.get("templateRepo", TEMPLATE_REPO), fp,
                           scope, mk.get("stamped", "unstamped"))),
            "detail": detail, "fingerprint": fp}


def marker_text_for(md_text, state, sha=None, item=None, when=None,
                    registry=SECTIONS):
    """The marker file's contents for the CURRENT sections. The sha and the
    fingerprint and nothing else about the other repo — this file must never
    become a second copy of the template's contents."""
    s = sections_of(md_text, registry)
    per, fp = fingerprint_of(s["bodies"], registry)
    when = when or datetime.date.today().isoformat()
    out = [
        "# .claude/template-sync.txt — THE CLAIM, not a copy.",
        "#",
        "# What it records: a fingerprint of CLAUDE.md's process sections, and",
        "# either the %s commit that absorbed them or a named queue item" % TEMPLATE_REPO,
        "# deferring that sync. `template_sync` in ledger/verify.py compares the",
        "# fingerprint and goes RED when they differ, so the question is asked at",
        "# the moment the sections change rather than when somebody notices.",
        "# It NEVER reads the other repo: the template checkout exists in one",
        "# container and not on the Windows runner, and verify must mean the same",
        "# thing everywhere it runs.",
        "#",
        "# Re-stamp with: python3 tools/template-sync.py --stamp --template-sha <sha>",
        "#           or: python3 tools/template-sync.py --stamp --defer <queue-item>",
        "templateRepo=%s" % TEMPLATE_REPO,
        "state=%s" % state,
        "templateSha=%s" % (sha or "none"),
        "queueItem=%s" % (item or "none"),
        "stamped=%s" % when,
        "sections=%d" % len(per),
    ]
    for key, _w in registry:
        if key in per:
            a, b = s["spans"][key]
            # ONE SPACE-FREE VALUE, sub-fields labelled with `:` and joined with
            # `/`. Every reader of a key=value channel splits on whitespace and
            # truncates silently — `crowdBodyWidth=0.45(narrowest 0.39 ...)`
            # returned `0.45(narrowest` and said nothing.
            out.append("section=key:%s/lines:%d/sha256:%s"
                       % (key, b - a + 1, per[key]))
    out.append("fingerprint=%s" % fp)
    return "\n".join(out) + "\n"


def section_row(value):
    """`key:X/lines:N/sha256:H` -> dict. The one parser for that row, so the
    writer above and the drift report below cannot drift apart."""
    got = {}
    for part in value.split("/"):
        name, _, v = part.partition(":")
        if _:
            got[name] = v
    return got


def _read(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def check(verbose=False):
    r = evaluate(_read(CLAUDE_MD), _read(MARKER))
    print(r["summary"])
    if verbose or r["exit"] not in (0,):
        for line in r["detail"]:
            print(line)
    return r["exit"]


def stamp(sha=None, item=None):
    md = _read(CLAUDE_MD)
    if md is None:
        print("template-sync: NOTHING MEASURED — no CLAUDE.md at %s" % CLAUDE_MD)
        return EXIT["nothing-measured"]
    s = sections_of(md)
    if s["missing"]:
        print("template-sync: REFUSING TO STAMP — %d of %d section(s) have no "
              "anchor: %s. Stamping now would record a fingerprint over less "
              "than it claims." % (len(s["missing"]), s["registered"],
                                   ",".join(s["missing"])))
        return EXIT["nothing-measured"]
    state = "synced" if sha else "deferred"
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(marker_text_for(md, state, sha=sha, item=item),
                      encoding="utf-8")
    print("template-sync: STAMPED %s" % MARKER)
    return check(verbose=True)


def show_sections():
    """The same reading as `check`, with the spans printed. It returns the SAME
    exit code on purpose: a second mode that exits 0 while the check is red is
    a green nobody earned."""
    return check(verbose=True)


# ------------------------------------------------------------------- selftest

_MD = """# CLAUDE.md — how to work on THING

Some prose that mentions AUTO MODE and THE STUDIO SPLIT in the middle of a
sentence, which must not anchor anything.

## THE STUDIO SPLIT — WHO DOES WHAT

- The main session is the DIRECTOR.
- Tier 3 builders implement.

**THE HYBRID RESIDENT (24 Aug):** the resident runs on Opus; the director is
an on-demand agent.

**REPORTING (same date):** one plain line each.

## AUTO MODE — THE CEREMONY IS RETIRED

The work continues.

### Reporting — RETIRED

History only.

## The standard

Not a process section.
"""


def selftest():
    """RULE 5b, BOTH WAYS, ACCEPTING FIRST — and the accepting fixture that
    matters is the LIVE repository, because doing the work this tool asks for
    (editing CLAUDE.md, re-stamping) changes the fixture rather than breaking
    it. The rejecting fixtures are synthetic on purpose: a rejecting case
    pinned to a real section would go red the day somebody edits that section,
    which teaches everyone to read red as noise."""
    ok, fails = 0, []

    def check_(name, cond, detail=""):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fails.append(name + (" — " + detail if detail else ""))

    # ---- ACCEPTING 1: the live repository, through the same evaluate().
    live_md, live_marker = _read(CLAUDE_MD), _read(MARKER)
    live = evaluate(live_md, live_marker)
    check_("accepting: the live CLAUDE.md + live marker are IN SYNC",
           live["exit"] == EXIT["ok"], live["summary"])
    ls = sections_of(live_md or "")
    check_("accepting: every registered section has an anchor in the live file "
           "(%d of %d)" % (ls["found"], ls["registered"]), not ls["missing"],
           ",".join(ls["missing"]))
    check_("accepting: every live section covers real lines (%s)"
           % ",".join("%s=%d" % (k, b - a + 1) for k, (a, b) in
                      sorted(ls["spans"].items())),
           all(b - a + 1 > 3 for a, b in ls["spans"].values()))
    check_("accepting: the summary ships its denominators",
           "sections=" in live["summary"] and "lines=" in live["summary"])
    # NO SPACES IN VALUES, in the marker as well as the summary — the marker is
    # a key=value channel too, and the reader that splits on whitespace and
    # truncates in silence is every reader anybody has ever typed.
    check_("accepting: no marker value carries a space",
           all(len(line.split("=", 1)[1].split()) == 1
               for line in marker_text_for(_MD, "synced", sha="1951af1").splitlines()
               if "=" in line and not line.startswith("#")))
    check_("accepting: a section row round-trips through its one parser",
           section_row("key:AUTO-MODE/lines:296/sha256:4bf1ebc0")
           == {"key": "AUTO-MODE", "lines": "296", "sha256": "4bf1ebc0"})

    # ---- ACCEPTING 2: a CHANGED section with a freshly stamped marker.
    changed = _MD.replace("Tier 3 builders implement.",
                          "Tier 3 builders implement, and they do not commit.")
    fresh = evaluate(changed, marker_text_for(changed, "synced", sha="1951af1"))
    check_("accepting: a changed section against a RE-STAMPED marker is green",
           fresh["exit"] == EXIT["ok"], fresh["summary"])

    # ---- ACCEPTING 3: a deferral that names a queue item.
    deferred = evaluate(_MD, marker_text_for(_MD, "deferred",
                                             item="template-sync-hybrid"))
    check_("accepting: state=deferred with a named queue item is green",
           deferred["exit"] == EXIT["ok"], deferred["summary"])
    check_("accepting: the deferral is NAMED in the summary, so a green run "
           "cannot hide it",
           "DEFERRED" in deferred["summary"]
           and "template-sync-hybrid" in deferred["summary"])

    # ---- ACCEPTING 4: whitespace is not drift; a word is.
    ws = _MD.replace("The work continues.", "The work continues.   ")
    check_("accepting: trailing whitespace does not drift",
           evaluate(ws, marker_text_for(_MD, "synced", sha="1951af1"))["exit"]
           == EXIT["ok"])
    # ---- ACCEPTING 5: prose that merely mentions the words anchors nothing.
    check_("accepting: the anchors are structural — prose mentioning the "
           "section names does not move a boundary",
           sections_of(_MD)["spans"]["THE-STUDIO-SPLIT"][0] > 4,
           str(sections_of(_MD)["spans"]))

    # ---- REJECTING 1: a changed section against a STALE marker.
    stale_marker = marker_text_for(_MD, "synced", sha="1951af1")
    drift = evaluate(changed, stale_marker)
    check_("rejecting: a changed section against a stale marker is DRIFT",
           drift["exit"] == EXIT["drift"], drift["summary"])
    check_("rejecting: the drift names WHICH section moved",
           "THE-STUDIO-SPLIT" in drift["summary"], drift["summary"])
    check_("rejecting: it does not accuse the sections that did not move",
           "AUTO-MODE" not in drift["summary"].split("changed since")[1]
           .split("(now=")[0], drift["summary"])
    check_("rejecting: the discharge is stated in the failure message",
           "--template-sha" in drift["summary"] and "--defer" in drift["summary"])

    # ---- REJECTING 2: no marker at all must read as NOTHING RECORDED.
    none_marker = evaluate(_MD, None)
    check_("rejecting: a missing marker is NOTHING RECORDED, not clean",
           none_marker["exit"] == EXIT["nothing-recorded"]
           and "NOTHING RECORDED" in none_marker["summary"],
           none_marker["summary"])
    check_("rejecting: an unparsable marker (no fingerprint line) is the same",
           evaluate(_MD, "# just a comment\nstate=synced\n")["exit"]
           == EXIT["nothing-recorded"])

    # ---- REJECTING 3: a SYNTHETIC section key that exists nowhere. Pinned to
    # a key no file will ever contain, so doing the work cannot break the tool.
    synth = SECTIONS + (("THE-SECTION-THAT-EXISTS-NOWHERE",
                         "THE SECTION THAT EXISTS NOWHERE"),)
    missing = evaluate(_MD, marker_text_for(_MD, "synced", sha="1951af1"), synth)
    check_("rejecting: a registered section with no anchor is NOTHING MEASURED",
           missing["exit"] == EXIT["nothing-measured"], missing["summary"])
    check_("rejecting: it names the section that was not found",
           "THE-SECTION-THAT-EXISTS-NOWHERE" in missing["summary"])
    check_("rejecting: NOTHING MEASURED reads differently from NOTHING RECORDED",
           "NOTHING MEASURED" in missing["summary"]
           and "NOTHING MEASURED" not in none_marker["summary"])

    # ---- REJECTING 4: claims that name nothing checkable.
    bad_defer = marker_text_for(_MD, "deferred", item=None)
    check_("rejecting: state=deferred naming no queue item is refused",
           evaluate(_MD, bad_defer)["exit"] == EXIT["nothing-recorded"])
    bad_sync = marker_text_for(_MD, "synced", sha=None).replace(
        "state=deferred", "state=synced")
    check_("rejecting: state=synced with templateSha=none is refused",
           evaluate(_MD, bad_sync)["exit"] == EXIT["nothing-recorded"],
           evaluate(_MD, bad_sync)["summary"])
    check_("rejecting: no CLAUDE.md at all is NOTHING MEASURED",
           evaluate(None, stale_marker)["exit"] == EXIT["nothing-measured"])

    # ---- the exit-code contract, asserted rather than documented.
    check_("exit codes: five outcomes, five distinct codes",
           len(set(EXIT.values())) == 5)
    check_("exit codes: only `ok` is 0",
           EXIT["ok"] == 0 and all(v != 0 for k, v in EXIT.items() if k != "ok"))

    print("template-sync selftest: %d passed, %d failed" % (ok, len(fails)))
    for f in fails:
        print("  FAILED " + f)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sections", action="store_true",
                    help="print what is fingerprinted, with line spans")
    ap.add_argument("--stamp", action="store_true",
                    help="record the current sections in the marker")
    ap.add_argument("--template-sha", default=None,
                    help="the template commit that absorbed them (state=synced)")
    ap.add_argument("--defer", default=None, metavar="QUEUE-ITEM",
                    help="record the sync as deferred to a named queue item")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if args.sections:
        return show_sections()
    if args.stamp:
        if bool(args.template_sha) == bool(args.defer):
            print("usage: --stamp needs exactly one of --template-sha <sha> or "
                  "--defer <queue-item>")
            return EXIT["usage"]
        if args.defer and " " in args.defer:
            print("usage: --defer takes a space-free queue-item token "
                  "(use dashes); every reader of a key=value channel splits on "
                  "whitespace")
            return EXIT["usage"]
        return stamp(sha=args.template_sha, item=args.defer)
    return check()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:              # `| head` must not end in a traceback
        try:
            sys.stdout.close()
        finally:
            sys.exit(0)
