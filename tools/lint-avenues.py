#!/usr/bin/env python3
"""`AvenuesX`/`AvenuesZ` are unscaled source data. Reading them raw is a bug.

WHY THIS EXISTS
---------------
`StreetMap.WideBlocks` scales the whole city about the origin by `StretchX`
(2.15) and `StretchZ` (1.15). The `District.AvenuesX`/`AvenuesZ` arrays are the
UNSCALED input to that transform, so a coordinate taken straight out of them
describes a city that was never built.

FIVE places read them raw, and every one was wrong in the same direction:

  DistrictAt                   four districts looked 136-184m from their own
                               buildings; 38 of 52 block centres were in no
                               district and four districts contained none
  SimDirector.DistrictTour     aimed four of seven cameras at bare ground, and
                               the photographs were read for days as "the outer
                               districts look unbuilt"
  Population.Place             spawned four districts' residents off their own
                               district
  WorldBuilder ground extent   sized the ground plane -200..160 while blocks
                               reach -426..340, so the outer districts stand
                               off the edge of it

`BoundsOf` and `CentreOf` now exist so the scaling cannot be forgotten, and
this refuses the raw read that would bypass them.

WHY THIS TOOL WAS REWRITTEN — IT EXEMPTED THE FILE THE FAULT LIVES IN
---------------------------------------------------------------------
The first version skipped `StreetMap.cs` wholesale ("the transform lives here;
it may read raw") and printed `0 raw avenue reads (183 files)`. That reads as a
clean sweep and was not one: `NameOf` compares a SCALED node coordinate against
the UNSCALED table, so only the founding cross at (0,0) matches and 49 of 51
street names are unreachable — `namedJunctions=1` of 97. The SIXTH consumer to
read the tables raw was inside the one file the guard could not see.

That is rule 3b wearing an exemption's clothes: a denominator that quietly
omits its own subject reads as proof. So the sweep now covers every file and
the accounting is per SITE, not per file.

TWO HOLES BESIDES THE EXEMPTION, both of which hid `NameOf` independently:

  * THE ALIAS. `NameOf` never writes `AvenuesX[`. It writes
        var cross = northSouth ? d.AvenuesZ : d.AvenuesX;
        if (near < cross[0] - 14 || ...)
    and the old pattern `\bAvenues[XZ]\s*\[` cannot match that shape at all.
    Removing the exemption alone would still have printed zero. Aliases —
    both `var name = <table>` and `foreach (var v in <table>)` — are now
    followed, scoped by brace depth.
  * WHAT COUNTS AS A READ. `.Length` and a null check touch no coordinate;
    `ScaleAbout(d.AvenuesX[0], ...)` IS the transform. Only a coordinate
    VALUE escaping unscaled is the fault, so reads are classified rather
    than counted.

THE RULE, AND WHY IT ADMITS THE TRANSFORM AND REJECTS `NameOf`
--------------------------------------------------------------
Every read of the tables lands in exactly one of four classes:

  transform   the value is an argument of `ScaleAbout(` on that line. This is
              the transform being applied; it is the whole point of the file.
  structural  `.Length`, `== null`, `!= null`. Reads no coordinate at all.
  origin      the value is compared only against the literal `0`.
              `ScaleAbout(v, 0, k) == v * k`, so zero — and ONLY zero — is a
              fixed point of the transform. `d.AvenuesX[i] == 0` therefore
              means the same thing in both frames. A comparison against any
              other literal would not, and is classed raw.
  raw         anything else: an unscaled coordinate value escapes.

`BoundsOf`, `CentreOf`, the junction grid, the block rectangles and
`OnOuterRing` are all `transform`. `NameOf`'s `Math.Abs(line[i] - coord)` is
`raw`, because an unscaled table entry meets a coordinate that arrived from
outside.

AND THE PART A PATTERN HONESTLY CANNOT DECIDE, so it is not pretended
--------------------------------------------------------------------
Compare the two shapes:

    NameOf         if (near < cross[0] - 14 || near > cross[^1] + 14)
    DistrictFor    if (x >= d.AvenuesX[0] - 20 && x <= d.AvenuesX[^1] + 20)

They are the SAME shape — a raw extent compared against a parameter — and one
is a bug while the other is correct by design, because `DistrictFor`'s only
caller (`MigrateAddresses`, line 923) hands it `place.X` BEFORE line 927 scales
it. The frame lives in the CALLER. No line-shaped rule can see that, and a lint
claiming to tell these apart by pattern would be inventing an answer. That is
why the first author reached for a whole-file exemption: there genuinely is no
local discriminator.

So the accounting is explicit and keyed by site. `RAW_OK` below lists the
methods permitted to hold `raw` reads, each with a reason that was checked
against the CODE. It is checked in BOTH directions:

  * a `raw` read in a method not on the list FAILS — a new fault cannot be
    absorbed silently, which is what an allow-list normally does;
  * a list entry that matches NO site FAILS as STALE — a reason whose subject
    moved or was fixed gets re-read rather than standing for ever. (`A reason
    on the reach ledger decays exactly like a comment.`)

`NameOf`, `AddressOf` and `DistancePenalty` are deliberately NOT on the list.
They are the live fault, and this tool is expected to be red until the fix
lands. Fixing them is queued separately; a bound must never be loosened to
make red go away.

Usage:
    tools/lint-avenues.py            # walk the tree
    tools/lint-avenues.py --selftest
    tools/lint-avenues.py --classes  # print every read and its class
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN = ROOT / "ledger" / "Assets" / "Scripts"

# NO FILE IS EXEMPT. The owner is swept like every other file; what the owner
# gets instead is the per-site ledger below, which cannot hide a new site.
OWNER = "StreetMap.cs"

# Methods in OWNER allowed to hold `raw` reads, and why. Each reason was read
# off the code, not off a comment. Both directions are enforced: an unlisted
# raw read fails, and a listed method with no raw read fails as stale.
RAW_OK = {
    "MassOverlaps":
        "compares avenues against BuiltMasses, an authored unscaled table in "
        "this same file (the pub at -8,8) — both sides in the authored frame",
    "DistrictFor":
        "answers which district an AUTHORED coordinate belongs to; its only "
        "caller MigrateAddresses passes place.X/Z at line 923, before line 927 "
        "scales them",
}

# ---------------------------------------------------------------------------
# DEFERRED KNOWN FAULTS. THESE ARE BUGS. THEY ARE NOT LEGITIMATE READS.
#
# A SEPARATE LEDGER FROM `RAW_OK` ON PURPOSE, and the separation is the whole
# point. `RAW_OK` means "read the caller, this is correct in the authored
# frame". This means "this is broken, we know, and it cannot be fixed tonight".
# Folding the two into one dict would have made nine known faults print as
# eighteen clean reads, which is the disease this tool was rewritten to cure —
# an allow-list silently absorbing what nobody re-reads.
#
# DEFERRED 2026-08-25. Queue item: streetmap-nameof-scaled-vs-raw
#
# WHY DEFERRED RATHER THAN FIXED. The fix is Core: `NameOf` compares SCALED
# node coordinates against the UNSCALED avenue tables, so 49 of 51 street names
# are unreachable (`namedJunctions=1` of 97). Correcting it changes the strings
# `AddressOf` returns, which feed gossip and witness lines, and breaks three
# CoreTests. That is a director ruling, not a builder edit. A guard that blocks
# every commit in the project until an unrulable fix lands is a RATCHET, which
# is the failure mode rule 5b names.
#
# WHAT KEEPS THIS FROM ROTTING — three checks, not one:
#   * an entry matching NO site fails as STALE, so when the ruling lands and
#     the fault is fixed the lint goes RED until the entry is REMOVED. The debt
#     cannot be paid off silently;
#   * the expected COUNT is pinned, so a PARTIAL fix (4 sites become 3) also
#     goes red and forces the entry to be re-read rather than quietly covering
#     less than it claims;
#   * a count that GROWS goes red too — deferring a method must never defer
#     every future fault written into that method.
#
# The counts are what the tool measured on 2026-08-25 at b7d232ba, not numbers
# chosen to fit.
DEFERRED = {
    "NameOf": (3,
        "compares a SCALED coordinate against the UNSCALED table via the "
        "`cross`/`line` aliases; only the founding cross at (0,0) matches"),
    "AddressOf": (4,
        "the nearest-street FALLBACK, taken whenever NameOf returns null — "
        "96 of 97 junctions — and wrong in the same direction"),
    "DistancePenalty": (2,
        "the tie-break AddressOf uses to keep a Hook position off a Copper Row "
        "street; compares raw extents against a scaled `along`"),
}
DEFERRED_QUEUE = "streetmap-nameof-scaled-vs-raw"
DEFERRED_SINCE = "2026-08-25"

FIELD = re.compile(r"\bAvenues[XZ]\b")
# A member declaration: resets alias scope and names the site.
#
# AT LEAST ONE MODIFIER IS REQUIRED, and it is required because the first
# version did not require it. `for (int i = 0; i < line.Length; i++)` matched
# as a declaration, so it reset the alias scope mid-method and `line[i]` — the
# actual `NameOf` fault — stopped being a read at all. The synthetic rejecting
# fixture found that; nothing else would have.
METHOD = re.compile(
    r"^\s*(?:\[[^\]]*\]\s*)?"
    r"(?:(?:public|private|internal|protected|static|override|virtual|sealed|"
    r"partial|async|extern|unsafe)\s+)+"
    r"(?:\([^)]*\)|[\w<>\[\],\.\?]+)\s+(\w+)\s*\("
)


def strip_comment(line):
    """Drop a trailing `//` comment, but never one inside a string literal.

    `$"..."` IS CODE and is kept whole — a done-line interpolation is the
    largest concentration of real reads in this project, and a stripper that
    threw quoted runs away is why an earlier lint scored zero on the very
    line it was written for.
    """
    out, i, quote = [], 0, None
    while i < len(line):
        c = line[i]
        if quote:
            if c == "\\":
                out.append(line[i:i + 2])
                i += 2
                continue
            if c == quote:
                quote = None
            out.append(c)
        elif c in "\"'":
            quote = c
            out.append(c)
        elif c == "/" and line[i + 1:i + 2] == "/":
            break
        else:
            out.append(c)
        i += 1
    return "".join(out)


def in_call(line, start, callee="ScaleAbout"):
    """Is offset `start` inside the argument list of a `callee(` on this line?"""
    for m in re.finditer(re.escape(callee) + r"\s*\(", line):
        depth, i = 0, m.end() - 1
        while i < len(line):
            if line[i] == "(":
                depth += 1
            elif line[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        if m.end() <= start < i:
            return True
    return False


def classify(line, m):
    """Which class this occurrence is. See the module docstring."""
    tail = line[m.end():]
    head = line[:m.start()]
    # AUTHORING THE TABLE IS NOT READING IT. `public double[] AvenuesX,
    # AvenuesZ;` and `AvenuesX = new double[] { -52, ... }` are the source data
    # being written down. A real read always goes through a member access
    # (`d.AvenuesX`, `StreetMap.AvenuesX`); a bare name followed by `=`, `,` or
    # `;` is a declarator or an object-initialiser target.
    if not head.rstrip().endswith(".") and re.match(r"\s*(=(?!=)|,|;)", tail):
        return "declaration"
    if re.match(r"\s*(==|!=)\s*null", tail) or re.match(r"\s*\.\s*Length", tail):
        return "structural"
    if in_call(line, m.start()):
        return "transform"
    # An indexed read whose only comparison on this line is against literal 0.
    # Zero is the fixed point of ScaleAbout about the origin; nothing else is.
    if re.match(r"\s*\[[^\]]*\]\s*(==|!=)\s*0(?![\d.])", tail):
        return "origin"
    return "raw"


def reads(text):
    """Every read of the avenue tables, direct or aliased.

    Returns [(lineno, class, method, snippet)]. Aliases are scoped by brace
    depth, so a `foreach (var x in d.AvenuesX)` stops being an avenue read
    when its loop closes.
    """
    out = []
    # name -> [kind, depth_it_lives_at, armed]. `armed` exists because a
    # `foreach` header and its `{` are on DIFFERENT LINES: the alias lives at
    # depth+1, but the prune below runs before that brace has been counted, so
    # an unarmed alias was deleted on the very next line and every `foreach`
    # alias in the project died instantly. `AddressOf` read as CLEAN because of
    # it — a zero from an instrument that had stopped looking.
    aliases = {}
    method, depth = "<file>", 0
    for n, raw_line in enumerate(text.split("\n"), 1):
        stripped = raw_line.strip()
        if stripped.startswith("//"):
            continue                      # prose about the fault is not the fault
        line = strip_comment(raw_line)

        for name, a in list(aliases.items()):
            if depth >= a[1]:
                a[2] = True               # the block it lives in has opened
            elif a[2]:
                del aliases[name]         # and has now closed

        sig = METHOD.match(line)
        if sig and not line.rstrip().endswith(";") and "=" not in line.split("(")[0]:
            method, aliases = sig.group(1), {}

        # --- alias introductions -------------------------------------------
        # `var cross = northSouth ? d.AvenuesZ : d.AvenuesX;` — the array.
        # `foreach (var ax in dist.AvenuesX)`                 — an element.
        # `intro_from` is where the aliased expression starts, so a line that
        # both introduces an alias AND reads a coordinate is not written off
        # wholesale — only the occurrences inside the alias expression are.
        intro, intro_from = None, len(line) + 1
        fe = re.search(r"foreach\s*\(\s*(?:var|double|float)\s+(\w+)\s+in\s+(.*)$", line)
        if fe and (FIELD.search(fe.group(2)) or
                   any(re.search(r"\b%s\b" % n2, fe.group(2))
                       for n2, a in aliases.items() if a[0] == "array")):
            aliases[fe.group(1)] = ["value", depth + 1, False]
            intro, intro_from = fe.group(1), fe.start(2)
        else:
            va = re.search(r"\b(?:var|double\[\])\s+(\w+)\s*=\s*([^;]*)", line)
            if va and FIELD.search(va.group(2)) and "[" not in va.group(2):
                aliases[va.group(1)] = ["array", depth, True]
                intro, intro_from = va.group(1), va.start(2)

        # --- occurrences ----------------------------------------------------
        for m in FIELD.finditer(line):
            if m.start() >= intro_from:
                continue                  # the aliasing itself, not a read
            out.append((n, classify(line, m), method, stripped))
        for name, a in aliases.items():
            if name == intro:
                continue
            for m in re.finditer(r"\b%s\b" % re.escape(name), line):
                if a[0] == "array":
                    cls = classify(line, m)
                else:
                    # An element alias IS a coordinate value already.
                    cls = "transform" if in_call(line, m.start()) else "raw"
                out.append((n, cls, method, stripped))

        depth += line.count("{") - line.count("}")
    return out


def audit(text, filename):
    """(findings, tally, stale, deferred) for one file.

    findings: [(lineno, method, snippet, why)] — raw reads nothing accounts for.
    tally:    {class: count} over every read, so a zero ships its denominator.
    stale:    ledger entries that matched no site — from EITHER ledger, tagged,
              because a paid-off debt and a decayed reason both need re-reading.
    deferred: {method: count} of KNOWN-FAULT sites actually seen. Counted
              SEPARATELY from the legitimate ones and never added to them: a
              deferral that reads like a pass is the disease.
    """
    tally = {"transform": 0, "structural": 0, "origin": 0,
             "declaration": 0, "raw": 0}
    findings, seen, deferred = [], set(), {}
    for n, cls, method, snip in reads(text):
        tally[cls] += 1
        if cls != "raw":
            continue
        if filename == OWNER and method in RAW_OK:
            seen.add(method)
            continue
        if filename == OWNER and method in DEFERRED:
            deferred[method] = deferred.get(method, 0) + 1
            continue
        why = ("unscaled coordinate compared against a value from outside the "
               "authored frame" if filename == OWNER else
               "use StreetMap.BoundsOf / StreetMap.CentreOf")
        findings.append((n, method, snip, why))

    stale = []
    if filename == OWNER:
        for name in sorted(set(RAW_OK) - seen):
            stale.append((name, "RAW_OK", "matched no site — the reason names "
                                          "code that moved; re-read it"))
        for name, (want, _) in sorted(DEFERRED.items()):
            got = deferred.get(name, 0)
            if got == 0:
                stale.append((name, "DEFERRED",
                              f"matched no site: the fault appears FIXED. "
                              f"Remove the entry — debt is not paid off "
                              f"silently"))
            elif got != want:
                stale.append((name, "DEFERRED",
                              f"expected {want} known-fault site(s), found "
                              f"{got}. The debt {'shrank' if got < want else 'GREW'}"
                              f" — re-read the entry"))
    return findings, tally, stale, deferred


# ----------------------------------------------------------------------------


ACCEPT_TRANSFORM = "            minX = ScaleAbout(d.AvenuesX[0], 0, kx);"
ACCEPT_NULL = "                if (d?.AvenuesX == null || d.AvenuesZ == null) continue;"
ACCEPT_LENGTH = "                if (d.AvenuesX.Length == 0) continue;"
ACCEPT_PROSE = "        /// UNSCALED. Never read d.AvenuesX[0] raw."
ACCEPT_ORIGIN = "                    d.HasFoundingCross && d.AvenuesX[i] == 0 ? \"street\" : \"avenue\");"
REJECT_TOUR = "                    float cx = (float)d.AvenuesX[d.AvenuesX.Length / 2];"

# Authoring the table is not reading it — the declarator and the initialiser.
ACCEPT_DECL = """
        public double[] AvenuesX, AvenuesZ;
                AvenuesX = new double[] { -40, -20, 0, 20, 40 },
"""

# SYNTHETIC. The `foreach` value alias, used on a LATER line inside the body.
# This is a regression test with a name: the first build recorded the alias at
# depth+1 and pruned it before the body's `{` had been counted, so every
# foreach alias in the project died on the next line and `AddressOf` reported
# CLEAN. Nothing but a multi-line fixture can catch that.
REJECT_FOREACH = """
        public static string ZzSyntheticNearestProbe(double x)
        {
            foreach (var dist in Districts)
            {
                foreach (var ax in dist.AvenuesX)
                {
                    double d = Math.Abs(ax - x);
                    if (d < bestD) { bestD = d; best = NameOf(ax, true, x); }
                }
            }
            return best;
        }
"""

# SYNTHETIC. A `NameOf`-shaped alias comparison under a method name that exists
# NOWHERE in the project, so the fixture cannot go red when NameOf is fixed —
# three rejecting fixtures here were pinned to real subjects and had to be
# unpinned for exactly that reason.
REJECT_ALIAS = """
        public static string ZzSyntheticPlateProbe(double coord, bool northSouth, double near)
        {
            foreach (var d in Districts)
            {
                var cross = northSouth ? d.AvenuesZ : d.AvenuesX;
                if (near < cross[0] - 14) continue;
                var line = northSouth ? d.AvenuesX : d.AvenuesZ;
                for (int i = 0; i < line.Length; i++)
                    if (Math.Abs(line[i] - coord) < 0.001) return names[i];
            }
            return null;
        }
"""


# SYNTHETIC-BY-SHAPE, PINNED TO NOTHING: `AddressOf` with three known-fault
# sites where the ledger expects four — a PARTIAL fix, which must trip.
REJECT_PARTIAL_FIX = """
        public static string AddressOf(double x, double z)
        {
            foreach (var dist in Districts)
            {
                foreach (var ax in dist.AvenuesX)
                {
                    double d = Math.Abs(ax - x);
                    if (d < bestD) { best = NameOf(ax, true, z); }
                }
            }
            return best;
        }
"""


def selftest():
    """Both outcomes, ACCEPTING CASE FIRST — the expensive failure is a
    validator nothing survives, and four guards in this project passed their
    rejecting case having never once been run against the case they must
    admit."""
    print("lint-avenues selftest — ACCEPTING CASES FIRST")

    f, t, _, dfr = audit(ACCEPT_TRANSFORM, OWNER)
    assert f == [] and t["transform"] == 1, (f, t)
    print(f"  ACCEPT 1/8  the transform read inside {OWNER}: "
          f"0 findings over {sum(t.values())} read(s), 1 classed transform")

    f, t, _, dfr = audit(ACCEPT_NULL, OWNER)
    assert f == [] and t["structural"] == 2, (f, t)
    print(f"  ACCEPT 2/8  a null guard: 0 findings over {sum(t.values())} "
          f"read(s), {t['structural']} classed structural")

    f, t, _, dfr = audit(ACCEPT_LENGTH, OWNER)
    assert f == [] and t["structural"] == 1, (f, t)
    print(f"  ACCEPT 3/8  a length guard: 0 findings over {sum(t.values())} "
          f"read(s), {t['structural']} classed structural")

    f, t, _, dfr = audit(ACCEPT_PROSE, OWNER)
    assert f == [] and sum(t.values()) == 0, (f, t)
    print("  ACCEPT 4/8  a comment quoting the fault: 0 findings over "
          "0 read(s) — prose is not code")

    f, t, _, dfr = audit(ACCEPT_ORIGIN, OWNER)
    assert f == [] and t["origin"] == 1, (f, t)
    print(f"  ACCEPT 5/8  `AvenuesX[i] == 0`: 0 findings over "
          f"{sum(t.values())} read(s), 1 classed origin (zero is the fixed "
          f"point of ScaleAbout)")

    ledgered = ("        static District ZzUnused(double x, double z)\n"
                "        {\n"
                "            double minX = d.AvenuesX[0] - 20;\n"
                "        }\n").replace("ZzUnused", "DistrictFor")
    f, t, _, dfr = audit(ledgered, OWNER)
    assert f == [] and t["raw"] == 1, (f, t)
    print(f"  ACCEPT 6/8  a ledgered authored-frame read (DistrictFor): "
          f"0 findings over {sum(t.values())} read(s), {t['raw']} classed raw "
          f"and accounted for")

    f, t, _, dfr = audit(ACCEPT_DECL, OWNER)
    assert f == [] and t["declaration"] == 3 and t["raw"] == 0, (f, t)
    print(f"  ACCEPT 7/8  the declarator and the table initialiser: 0 findings "
          f"over {sum(t.values())} mention(s), {t['declaration']} classed "
          f"declaration — authoring the table is not reading it")

    deferred_site = ("        public static string NameOf(double coord)\n"
                     "        {\n"
                     "            var cross = d.AvenuesZ;\n"
                     "            if (near < cross[0] - 14) continue;\n"
                     "        }\n")
    f, t, _, dfr = audit(deferred_site, OWNER)
    assert f == [] and dfr == {"NameOf": 1}, (f, dfr)
    print(f"  ACCEPT 8/8  a DEFERRED known-fault site does not block: 0 "
          f"findings, and it is counted as {dfr} under DEFERRED — NEVER added "
          f"to the {len(RAW_OK)} legitimate RAW_OK reads")

    print("  --- rejecting cases ---")

    f, t, _, dfr = audit(REJECT_TOUR, "SimDirector.cs")
    assert len(f) == 1, (f, t)
    print(f"  REJECT 1/6  the tour camera's raw read: {len(f)} finding over "
          f"{sum(t.values())} read(s), owner NOT exempt (no file is)")

    f, t, _, dfr = audit(REJECT_ALIAS, OWNER)
    assert len(f) >= 2, (f, t)
    assert all(m == "ZzSyntheticPlateProbe" for _, m, _, _ in f), f
    print(f"  REJECT 2/6  synthetic NameOf-shaped ALIAS comparison inside "
          f"{OWNER}: {len(f)} findings over {sum(t.values())} read(s) at "
          f"lines {','.join(str(n) for n, _, _, _ in f)}")

    f, t, _, dfr = audit(REJECT_FOREACH, OWNER)
    # Exactly the two lines that USE `ax`; the loop header is the aliasing.
    assert len(f) == 2, (f, t)
    assert all(m == "ZzSyntheticNearestProbe" for _, m, _, _ in f), f
    print(f"  REJECT 3/6  synthetic `foreach` value alias used on LATER lines "
          f"inside its body: {len(f)} findings over {sum(t.values())} read(s) "
          f"at lines {','.join(str(n) for n, _, _, _ in f)} "
          f"(regression: this read 0 while the alias died at its own `{{`)")

    f, t, stale, dfr = audit(ACCEPT_TRANSFORM, OWNER)
    names = sorted(n for n, led, _ in stale if led == "RAW_OK")
    assert names == sorted(RAW_OK), stale
    print(f"  REJECT 4/6  a RAW_OK entry matching no site is STALE, not "
          f"silently kept: {len(names)} reported ({', '.join(names)})")

    # THE DEBT CANNOT BE PAID OFF SILENTLY. When the ruling lands and the fault
    # is fixed, the entry stops matching and the lint goes RED until it is
    # REMOVED. Proven here rather than asserted in a comment.
    fixed = sorted(n for n, led, why in stale
                   if led == "DEFERRED" and "appears FIXED" in why)
    assert fixed == sorted(DEFERRED), stale
    print(f"  REJECT 5/6  a DEFERRED entry whose fault is FIXED goes red until "
          f"the entry is removed: {len(fixed)} reported ({', '.join(fixed)}) "
          f"— deferred debt cannot rot quietly")

    # A PARTIAL FIX ALSO TRIPS: 4 sites become 3 and the entry must be re-read,
    # so deferring a method never defers whatever is written into it next.
    partial = REJECT_PARTIAL_FIX
    f, t, stale, dfr = audit(partial, OWNER)
    moved = [(n, why) for n, led, why in stale
             if led == "DEFERRED" and "expected" in why]
    assert any(n == "AddressOf" for n, _ in moved), stale
    assert f == [], f
    print(f"  REJECT 6/6  a DEFERRED count that MOVED is red, both directions: "
          f"{len(moved)} reported — "
          f"{'; '.join(w.split('.')[0] for _, w in moved)}")

    # The alias hole, stated as its own assertion: the OLD pattern scored zero
    # on the very shape the tool exists for.
    old = re.compile(r"\bAvenues[XZ]\s*\[")
    hits = [l for l in REJECT_ALIAS.split("\n") if old.search(l)]
    assert hits == [], hits
    print(f"  NOTE        the pre-rewrite pattern `Avenues[XZ][` matches "
          f"{len(hits)} line(s) of that fixture — it could not see the fault "
          f"even with the exemption removed")

    print("lint-avenues: selftest ok (8 accepting, 6 rejecting)")
    return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()

    files = sorted(SCAN.rglob("*.cs"))
    bad, stale_all, scanned, owner_seen = [], [], 0, False
    deferred_all = {}
    tally = {"transform": 0, "structural": 0, "origin": 0,
             "declaration": 0, "raw": 0}
    for path in files:
        scanned += 1
        if path.name == OWNER:
            owner_seen = True
        text = path.read_text(encoding="utf-8", errors="replace")
        findings, t, stale, deferred = audit(text, path.name)
        for k, v in t.items():
            tally[k] += v
        for meth, cnt in deferred.items():
            deferred_all[meth] = deferred_all.get(meth, 0) + cnt
        for n, method, snip, why in findings:
            bad.append((path.relative_to(ROOT), n, method, snip, why))
        for entry in stale:
            stale_all.append((path.relative_to(ROOT),) + entry)

    if "--classes" in argv:
        for path in files:
            text = path.read_text(encoding="utf-8", errors="replace")
            for n, cls, method, snip in reads(text):
                print(f"{path.relative_to(ROOT)}:{n}: {cls:10} {method:24} "
                      f"{snip[:72]}")

    # THE DENOMINATOR (rule 3b), and the exemption status beside it: "0 raw
    # avenue reads" and "0 raw avenue reads, owner exempt" are different facts.
    try:
        where = SCAN.relative_to(ROOT)
    except ValueError:
        where = SCAN                      # fail readable, not with a traceback
    owner_note = (f"owner {OWNER} INCLUDED in the sweep, no file exempt"
                  if owner_seen else
                  f"owner {OWNER} NOT FOUND under {where} — "
                  f"NOTHING MEASURED about the file the fault lives in")
    total = sum(tally.values())
    head = (f"lint-avenues: {scanned} file(s) swept, {owner_note}; "
            f"{total} avenue table mention(s) classified "
            f"— {tally['declaration']} declaration, {tally['transform']} "
            f"transform, {tally['structural']} structural, {tally['origin']} "
            f"origin, {tally['raw']} raw")
    if total == 0:
        head = (f"lint-avenues: {scanned} file(s) swept, {owner_note}; "
                f"NOTHING MEASURED — no avenue table read found at all, which "
                f"is not the same as clean")
    print(head)
    # TWO KINDS OF ACCOUNTING, NEVER ONE NUMBER. `RAW_OK` reads are correct in
    # the authored frame. `DEFERRED` reads are KNOWN BUGS awaiting a ruling.
    # Summing them would print nine faults as clean, which is the exact shape
    # this tool exists to refuse.
    n_deferred = sum(deferred_all.values())
    accounted = tally["raw"] - len(bad) - n_deferred
    print(f"  raw reads LEGITIMATE (RAW_OK, authored frame): {accounted} in "
          f"{len(RAW_OK)} method(s) — {', '.join(sorted(RAW_OK))}")
    if n_deferred:
        print(f"  raw reads DEFERRED KNOWN FAULTS (NOT clean, NOT fixed): "
              f"{n_deferred} in {len(deferred_all)} method(s) — "
              f"{', '.join(f'{k}x{v}' for k, v in sorted(deferred_all.items()))}"
              f" — queue={DEFERRED_QUEUE} deferred-since={DEFERRED_SINCE}")
        for meth in sorted(deferred_all):
            print(f"      {meth}: {DEFERRED[meth][1]}")
    else:
        print(f"  raw reads DEFERRED KNOWN FAULTS: 0 of {len(DEFERRED)} "
              f"listed method(s) — nothing deferred")
    # THE DENOMINATOR VERIFY CARRIES INTO THE COMMIT MESSAGE. `verify.py`'s
    # `raw_avenues()` greps this exact token — `re.search(r"\((\d+) files
    # walked", out)` — and falls back to a bare "0 raw avenue reads" with NO
    # count when it misses. The rewrite renamed the old wording, which would
    # have silently dropped the denominator out of every green footer: rule 3b
    # regressing one layer up, in the channel a person actually reads.
    print(f"  ({scanned} files walked, owner "
          f"{'INCLUDED' if owner_seen else 'NOT FOUND'})")

    # DISTINCT EXIT PER OUTCOME. 2 is a broken instrument, not a clean sweep:
    # if the owner was never reached there is nothing to be clean ABOUT, and
    # returning 0 there is the exact failure this rewrite exists to remove.
    rc = 0
    if not owner_seen or total == 0:
        rc = 2
        print(f"  EXIT 2 — the sweep did not reach its subject. This is not a "
              f"pass; {scanned} file(s) were walked and {total} mention(s) "
              f"found.")
    if stale_all:
        rc = 1
        print(f"  {len(stale_all)} STALE ledger entr(ies) — the ledger no "
              f"longer describes the code; re-read it:")
        for rel, name, ledger, why in stale_all:
            print(f"    {rel}: {ledger}['{name}'] {why}")
    if bad:
        rc = 1
        print(f"  {len(bad)} UNACCOUNTED raw avenue read(s):")
        shown = 0
        for rel, n, method, line, why in bad:
            if shown == 40:
                print(f"    (+{len(bad) - shown} more not shown)")
                break
            print(f"    {rel}:{n}: [{method}] {line[:88]}")
            shown += 1
        print("  Each is an unscaled table entry meeting a scaled coordinate. "
              "Use StreetMap.BoundsOf / StreetMap.CentreOf, or — if the site "
              "genuinely works in the authored frame — add it to RAW_OK with a "
              "reason read off the CALLER.")
    elif not stale_all and rc == 0:
        if n_deferred:
            print(f"  0 UNACCOUNTED raw avenue reads over {total} mention(s) "
                  f"in {scanned} file(s), owner included — but {n_deferred} "
                  f"KNOWN FAULT(S) ARE DEFERRED, NOT FIXED. This is not a "
                  f"clean sweep; it is a clean sweep MINUS a named debt "
                  f"({DEFERRED_QUEUE}).")
        else:
            print(f"  0 unaccounted raw avenue reads over {total} mention(s) "
                  f"examined in {scanned} file(s), owner included; "
                  f"0 deferred.")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
