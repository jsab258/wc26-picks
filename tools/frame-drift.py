#!/usr/bin/env python3
"""Layer 3, PIXELS: what moved in the render since the last build.

    python3 tools/frame-drift.py OLD.tsv NEW.tsv     # the drift block
    python3 tools/frame-drift.py --selftest          # check the instrument

WHY THIS EXISTS, and it is the most expensive lesson in CLAUDE.md rule 4.

Four times in one night I condemned correct work from a 1280x720 JPEG: three
textures that `SurfaceSpec`'s noir tint had already neutralised, a bench I read
as a sign board mounted wrong, and a set of wheels that measured within a few
percent of a real car. Each time I was one commit from re-picking assets or
"fixing" working geometry, and each time a printed number settled it in under a
minute.

The lesson was not "look harder". A picture has a resolution, a compression
artefact and a palette, and at street distance in fog those hide more than they
show — so a visual judgement is a HYPOTHESIS and the question "does this look
off?" has no answer. The question with an answer is **what moved**, and nothing
in this project could answer it, because the twenty frames every run fingerprints
went to `player.log` and the sim-out JSON — the two channels this environment
cannot read.

So the sim now writes one row per shot to `sim-out/frames.tsv`, the build commits
it to `game-design/sim-shots/frames.tsv`, and this compares the two. `git log`
on that file then gives the same history of measurements that showed the AO
ceiling sitting inside its own instrument's noise across five runs.

IT REPORTS AND DOES NOT GATE, on purpose and for now.

A drift tolerance is a threshold, and rule 2 says a threshold you have not
measured is a rounding wearing a measurement's clothes — `nightNotDarker`
failed at 0.136 against 0.135 for exactly that reason. Nobody knows yet how much
a mean luminance moves between two runs of the same commit on a software
rasteriser. So this prints the deltas and the noise floor stays unwritten until
two runs of unchanged code have said what it is. That is the `deedSlotSets`
move: make the run print the series, then set the number from evidence.
"""
import pathlib
import sys

FIELDS = ["meanLuma", "maxLuma", "brightPct", "satPct", "satStrength"]

# A field's units, and how many decimals are worth printing. Luminance is 0..1
# and a percentage is 0..100, so one shared format would print either noise or
# nothing depending on which row you were reading.
DECIMALS = {"meanLuma": 3, "maxLuma": 3, "brightPct": 2, "satPct": 2,
            "satStrength": 2}


def read(path):
    """A ledger as {shot: {field: float}}, in file order.

    Tolerant of a MISSING file and of a file with only a header, because both
    are the normal state on the first run and neither is an error. Not tolerant
    of a row it cannot parse — that is the instrument being wrong, and rule 3
    says suspect the instrument first, which is hard to do if it swallows its
    own bad input.
    """
    rows, order, bad = {}, [], []
    p = pathlib.Path(path)
    if not p.exists():
        return rows, order, bad
    header = None
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        if header is None:
            header = cells
            continue
        if len(cells) != len(header):
            bad.append(f"{p.name}:{n} has {len(cells)} cells, header has {len(header)}")
            continue
        row, shot = {}, cells[0]
        for key, cell in zip(header[1:], cells[1:]):
            if key not in FIELDS:
                continue          # meanRgb/brightRgb are colours, carried not compared
            try:
                row[key] = float(cell)
            except ValueError:
                bad.append(f"{p.name}:{n} {key}={cell!r} is not a number")
        rows[shot] = row
        order.append(shot)
    return rows, order, bad


def drift(old_path, new_path):
    """The block that goes into verdict.txt."""
    old, _, bad_old = read(old_path)
    new, order, bad_new = read(new_path)
    out = []

    for problem in bad_old + bad_new:
        out.append(f"FrameLedger: MALFORMED {problem}")

    if not new:
        # LOUD, because the silent version of this is the failure this whole
        # file exists to prevent: a ledger that stopped being written reads
        # exactly like a render that stopped changing.
        out.append("FrameDrift: NO NEW LEDGER — the sim wrote no frames.tsv. "
                   "This is not 'nothing moved'; it is 'nothing was measured'.")
        return out, 1

    if not old:
        out.append(f"FrameDrift: first ledger, {len(new)} shot(s), nothing to compare "
                   "against yet. The next run is the one that can answer this.")
        for shot in order:
            out.append("FrameDrift:   " + shot + " " + fmt_row(new[shot]))
        return out, 0

    gone = [s for s in old if s not in new]
    fresh = [s for s in order if s not in old]
    shared = [s for s in order if s in old]

    out.append(f"FrameDrift: {len(shared)} shot(s) compared, {len(fresh)} new, "
               f"{len(gone)} gone. REPORTED, NOT GATED — the run-to-run noise "
               "floor has not been measured yet.")
    if fresh:
        out.append("FrameDrift:   new shots: " + ", ".join(fresh))
    if gone:
        # A shot that stopped being taken is a bigger deal than one that moved,
        # and it is invisible in a per-field diff.
        out.append("FrameDrift:   SHOTS NO LONGER TAKEN: " + ", ".join(sorted(gone)))

    # Biggest movers first. A twenty-row table sorted by shot name buries the
    # one row that matters under nineteen that did not move.
    ranked = sorted(shared, key=lambda s: -worst(old[s], new[s]))
    for shot in ranked:
        a, b = old[shot], new[shot]
        parts = []
        for f in FIELDS:
            if f not in a or f not in b:
                continue
            d = DECIMALS[f]
            delta = b[f] - a[f]
            parts.append(f"{f}={b[f]:.{d}f}({delta:+.{d}f})")
        out.append("FrameDrift:   " + shot + " " + " ".join(parts))
    return out, 0


def worst(a, b):
    """How far this shot moved, as a fraction of its own previous value.

    RELATIVE, NOT ABSOLUTE, and the two disagree hard here. `meanLuma` lives
    around 0.25 and `brightPct` around 1.4, so ranking on raw deltas would put
    every bright-fraction wobble above a luminance change four times its size.
    Guarded against a previous value of zero, which `brightPct` genuinely is on
    a night frame with no lamps in it.
    """
    m = 0.0
    for f in FIELDS:
        if f not in a or f not in b:
            continue
        base = abs(a[f])
        rel = abs(b[f] - a[f]) / base if base > 1e-9 else abs(b[f] - a[f])
        m = max(m, rel)
    return m


def fmt_row(row):
    return " ".join(f"{f}={row[f]:.{DECIMALS[f]}f}" for f in FIELDS if f in row)


def selftest():
    """SUSPECT THE INSTRUMENT FIRST (rule 3), so the instrument gets checked.

    `breakrun.py` reverted one file of a two-file spec and turned a SURVIVED
    into a RED. The corpus diagnostic read sixty consecutive rows of a
    speaker-ordered dataset and reported on "the corpus" having seen one person.
    A comparison tool that silently reports "nothing moved" is the same class of
    fault and would be believed, because nothing moving is the expected answer.
    """
    import tempfile
    ok, fails = 0, []

    def check(label, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fails.append(label)

    d = pathlib.Path(tempfile.mkdtemp())
    head = ("shot\tmeanLuma\tmaxLuma\tbrightPct\tsatPct\tsatStrength\t"
            "meanRgb\tbrightRgb\n")

    def write(name, body):
        p = d / name
        p.write_text("# comment\n" + head + body, encoding="utf-8")
        return str(p)

    a = write("a.tsv", "day1_noon\t0.250\t0.981\t1.42\t3.10\t0.41\t60,64,70\t250,250,250\n"
                       "day1_night\t0.126\t0.900\t0.30\t1.00\t0.38\t30,34,40\t200,200,210\n")
    b = write("b.tsv", "day1_noon\t0.260\t0.981\t1.42\t3.10\t0.41\t60,64,70\t250,250,250\n"
                       "day1_night\t0.126\t0.900\t0.30\t1.00\t0.38\t30,34,40\t200,200,210\n")

    rows, order, bad = read(a)
    check("reads both rows", len(rows) == 2)
    check("keeps file order", order == ["day1_noon", "day1_night"])
    check("no false malformed", bad == [])
    check("parses a float", abs(rows["day1_noon"]["meanLuma"] - 0.250) < 1e-9)
    check("ignores colour columns", "meanRgb" not in rows["day1_noon"])

    lines, code = drift(a, b)
    text = "\n".join(lines)
    check("clean compare exits 0", code == 0)
    # THE CENTRAL CLAIM: a change of one part in twenty-five must be VISIBLE.
    # A tool that rounds this away is worse than no tool, because its silence
    # would be read as a verdict.
    check("sees a +0.010 move", "+0.010" in text)
    check("prints the new value", "meanLuma=0.260" in text)
    # And the mover must SORT ABOVE the shot that did not move, or a real
    # change arrives at the bottom of a twenty-row table.
    check("ranks the mover first",
          text.index("day1_noon meanLuma") < text.index("day1_night meanLuma"))

    same, code = drift(a, a)
    check("identical ledgers exit 0", code == 0)
    check("identical ledgers show +0.000", "+0.000" in "\n".join(same))

    # A MISSING NEW LEDGER IS NOT 'NOTHING MOVED'. This is the case the whole
    # tool would otherwise fail silently on.
    lines, code = drift(a, str(d / "nope.tsv"))
    check("missing new ledger is an error", code == 1)
    check("missing new ledger says so", "NO NEW LEDGER" in "\n".join(lines))

    lines, code = drift(str(d / "nope.tsv"), a)
    check("missing old ledger is fine", code == 0)
    check("first run says so", "first ledger" in "\n".join(lines))

    # A shot that stopped being taken.
    c = write("c.tsv", "day1_noon\t0.250\t0.981\t1.42\t3.10\t0.41\t60,64,70\t250,250,250\n")
    lines, _ = drift(a, c)
    check("names a dropped shot", "SHOTS NO LONGER TAKEN: day1_night" in "\n".join(lines))
    lines, _ = drift(c, a)
    check("names a new shot", "new shots: day1_night" in "\n".join(lines))

    # Malformed input is reported rather than swallowed.
    bent = d / "bent.tsv"
    bent.write_text(head + "day1_noon\tnotanumber\t0.9\t1.0\t1.0\t0.1\t1,1,1\t2,2,2\n",
                    encoding="utf-8")
    _, _, bad = read(str(bent))
    check("reports a non-numeric cell", any("not a number" in x for x in bad))
    short = d / "short.tsv"
    short.write_text(head + "day1_noon\t0.1\n", encoding="utf-8")
    _, _, bad = read(str(short))
    check("reports a short row", any("cells" in x for x in bad))

    # `worst` must be relative, or brightPct's small numbers dominate the rank.
    check("worst is relative",
          worst({"meanLuma": 0.20}, {"meanLuma": 0.22})
          > worst({"brightPct": 40.0}, {"brightPct": 41.0}))
    check("worst survives a zero base",
          worst({"brightPct": 0.0}, {"brightPct": 0.5}) == 0.5)

    print(f"frame-drift selftest: {ok} passed, {len(fails)} failed")
    for f in fails:
        print("  FAILED " + f)
    return 1 if fails else 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if len(sys.argv) != 3:
        print(__doc__.splitlines()[2].strip())
        return 2
    lines, code = drift(sys.argv[1], sys.argv[2])
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
