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

# WHERE THE CAMERA STOOD. Carried, never compared as a field — a camera that
# moved is not a render that changed, and telling those two apart is the whole
# job of the block below.
POSE = ["camX", "camZ", "camYaw"]

# WHAT COUNTS AS THE SAME VANTAGE, AND WHAT A MATCHED PAIR ACTUALLY AGREES TO.
# Both measured, not chosen — rule 2, and the first version of this number was
# a rounding that would have made the tool dismiss every real change.
#
# 50 landed ledgers give 49 CONSECUTIVE pairs, so both buckets below see the
# same amount of code change between them; splitting all-pairs instead biases
# the matched bucket toward temporally-adjacent runs and is how I first read
# this backwards.
#
#     street, camera in the same place   n=135   median 0.0020  p90 0.0100
#     street, camera moved               n=899   median 0.0130  p90 0.0650
#     district tour, pinned by construction
#                                        n=329   median 0.0020  p90 0.0050
#
# A factor of 6.5 in both the median and the p90, from the camera alone. And
# the tour rows are the answer to "would pinning help": they are the only shots
# in the ledger whose pose cannot move, and they are the quietest thing in it.
POSE_SAME_M = 0.5      # the clustering in camX/camZ is far tighter than this
POSE_SAME_DEG = 1.0    # yaw is quantised to whole degrees in the ledger

# AND IT IS NOT A NOISE FLOOR, WHICH IS WHAT I FIRST CALLED IT. Every pair in
# that 135 spans two CONSECUTIVE COMMITS, so the 0.010 contains render noise and
# whatever those builds actually changed, mixed. It answers "how far does a
# fixed-vantage frame normally move between two builds" and nothing more —
# exceeding it means larger than a normal build step, not larger than noise.
#
# A real noise floor needs the same commit built twice and this project has
# never done it; the block above already distinguishes that case and would say
# so. Naming this `LUMA_FLOOR` would have been rule 2's fault one layer up: a
# number whose NAME claims more than the measurement behind it, which is how
# `crowdTightest` and `confabs` both went wrong.
LUMA_STEP_P90 = 0.010  # p90 of the 135 pose-matched consecutive-landing pairs


def commit_of(path):
    """The commit the build wrote this ledger from, if it is stamped.

    WHY IT MATTERS ENOUGH TO PRINT. A drift block between two DIFFERENT commits
    is signal plus noise and cannot be read as either. The second run of this
    ledger came back with `meanLuma` moving 0.060 and `satPct` moving 14.66, and
    a checkpoint had already described that run as "the one that gives the
    run-to-run noise floor" — it was not: the commit in between removed a large
    white capsule from the middle of every frame, so most of that delta is the
    fix working.

    A noise floor needs the SAME commit built twice. Nothing in the ledger said
    which commit produced it, so nothing could have caught that; now the header
    carries it and the block says plainly which case you are looking at.
    """
    p = pathlib.Path(path)
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("# commit "):
            return line[len("# commit "):].strip()
        if not line.startswith("#"):
            break
    return None


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
            if key not in FIELDS and key not in POSE:
                continue          # meanRgb/brightRgb are colours, carried not compared
            try:
                row[key] = float(cell)
            except ValueError:
                bad.append(f"{p.name}:{n} {key}={cell!r} is not a number")
        rows[shot] = row
        order.append(shot)
    return rows, order, bad


def vantage(a, b):
    """Did the camera stand in the same place for both of these rows?

    Returns (comparable, note). `comparable` is None when the pose was never
    recorded, which is a THIRD answer and not a synonym for either of the other
    two: ledgers written before the pose columns existed cannot be conditioned
    at all, and saying "same vantage" about them would be inventing agreement.

    WHY A DELTA WITHOUT THIS IS UNREADABLE. Across 50 landed ledgers every
    street shot's brightness tracks where the camera happened to be standing:
    `day2_noon` correlates -0.678 with camX and **-0.803 with yaw**, `day8_noon`
    -0.795 with yaw, `day5_noon` -0.817. Which way you face at noon decides how
    much sky and sun-facing wall is in the frame, so yaw is at least as strong a
    confound as position — and the first version of this analysis looked only at
    camX and missed it.

    The camera moves because the shot follows the GAME: the player walks a
    different route when the crowd, the day job or the steering changes, and the
    step-back loop adds up to twelve metres on top. None of that is a render
    change, and all of it lands in `meanLuma`.
    """
    if not all(k in a and k in b for k in POSE):
        return None, "pose not recorded"
    dx, dz = abs(a["camX"] - b["camX"]), abs(a["camZ"] - b["camZ"])
    dyaw = abs(((a["camYaw"] - b["camYaw"]) + 180.0) % 360.0 - 180.0)
    if dx < POSE_SAME_M and dz < POSE_SAME_M and dyaw < POSE_SAME_DEG:
        return True, "same vantage"
    moved = (dx * dx + dz * dz) ** 0.5
    return False, f"CAMERA MOVED {moved:.1f}m yaw {dyaw:.0f}deg"


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

    ca, cb = commit_of(old_path), commit_of(new_path)
    if ca and cb and ca == cb:
        what = (f"SAME COMMIT {ca[:7]} BUILT TWICE — every delta below IS the "
                "noise floor, and a Layer 3 tolerance may be derived from it.")
    elif ca and cb:
        # THE SPREAD IS A CAMERA CONFOUND, NOT NOISE — and I published it as
        # noise first, which would have made this tool far too conservative,
        # then published the confound itself half-measured, which is the part
        # worth keeping here.
        #
        # First reading: `day2_noon` spans 0.424-0.503 over twelve runs, I
        # called it a +-0.07 noise floor, and correlating luma against camX
        # gave -0.893. That was the right idea from too small a sample and only
        # one axis. Over all 50 landed ledgers it is -0.678 against camX and
        # **-0.803 against YAW**, which the first pass never looked at and which
        # is the stronger term on several shots (day5_noon -0.817, day8_noon
        # -0.795). Obvious in hindsight: which way you face at noon decides how
        # much sky is in the frame.
        #
        # The floor itself needed the same correction. Selecting pose-matched
        # pairs out of ALL pairs biases them toward temporally-adjacent runs,
        # so they see less code change and look artificially quiet — I read the
        # pinned district shots as the NOISIEST in the ledger off exactly that
        # mistake. Restricted to CONSECUTIVE landings, so both buckets span the
        # same code:
        #
        #     street, same vantage    n=135  median 0.0020  p90 0.0100
        #     street, camera moved    n=899  median 0.0130  p90 0.0650
        #     district tour, pinned   n=329  median 0.0020  p90 0.0050
        #
        # Like-for-like at a matched vantage, shadowStrength 0.85 reads about
        # +0.010 against 0.93 — a real effect at the edge of this instrument
        # rather than the +0.07 the unconditioned numbers appeared to show.
        what = (f"{ca[:7]} -> {cb[:7]}, DIFFERENT COMMITS — these deltas are the "
                "change plus the noise. Each row below says whether the camera "
                "stood in the same place for both, because a shot's brightness "
                "tracks its vantage harder than it tracks any render change "
                "(day2_noon correlates -0.68 with camX and -0.80 with yaw over "
                "50 runs): pose-matched consecutive landings agree to 0.010 at "
                "the p90 and pose-moved ones to 0.065, on the same code. Read "
                "the same-vantage rows and the moved ones cannot be read as "
                "either; a camera that walked took a different photograph, not "
                "a different render.")
    else:
        what = ("commits unstamped, so these deltas cannot be told apart from "
                "a code change.")
    out.append(f"FrameDrift: {len(shared)} shot(s) compared, {len(fresh)} new, "
               f"{len(gone)} gone. REPORTED, NOT GATED — {what}")
    if fresh:
        out.append("FrameDrift:   new shots: " + ", ".join(fresh))
    if gone:
        # A shot that stopped being taken is a bigger deal than one that moved,
        # and it is invisible in a per-field diff.
        out.append("FrameDrift:   SHOTS NO LONGER TAKEN: " + ", ".join(sorted(gone)))

    # HOW MANY OF THESE ROWS CAN ACTUALLY BE READ — the denominator, applied to
    # a comparison rather than to a count (rule 3b). "20 shots compared" and
    # "20 shots compared, 3 of them from the same vantage" are the same
    # sentence to a reader and completely different evidence, and the first
    # version of this block printed only the first one.
    verdicts = {s: vantage(old[s], new[s]) for s in shared}
    fixed = sum(1 for c, _ in verdicts.values() if c is True)
    unknown = sum(1 for c, _ in verdicts.values() if c is None)
    if shared:
        if unknown == len(shared):
            out.append("FrameDrift:   POSE NOT RECORDED on either ledger — nothing "
                       "below can be conditioned on where the camera stood.")
        else:
            out.append(f"FrameDrift:   {fixed} of {len(shared)} shot(s) taken from the "
                       f"SAME VANTAGE and comparable; {len(shared) - fixed - unknown} "
                       f"moved, {unknown} unrecorded. A typical build-to-build step at "
                       f"a fixed vantage is {LUMA_STEP_P90:.3f} at the p90.")
            # NAMED, not just counted. A quiet comparable row does not sort to the
            # top — only a loud one does — so without this the nine rows worth
            # reading are scattered through twenty-nine and have to be found by
            # eye every time. In practice they are the seven teleported district
            # frames, whose pose is fixed by construction, plus day1_noon and
            # day1_night, taken before the sim has diverged enough to move the
            # player: the only photometric series this project has.
            if fixed:
                out.append("FrameDrift:   comparable: "
                           + ", ".join(s for s in shared if verdicts[s][0] is True))

    # Biggest movers first, but a READABLE mover outranks an unreadable one
    # however large the unreadable one is — the ranking exists so a real change
    # does not arrive at the bottom of a twenty-row table, and a delta from a
    # camera that walked eight metres is not a real change, it is a different
    # photograph.
    def rank(s):
        comparable, _ = verdicts[s]
        loud = comparable is True and abs(new[s].get("meanLuma", 0.0)
                                          - old[s].get("meanLuma", 0.0)) > LUMA_STEP_P90
        return (0 if loud else 1, -worst(old[s], new[s]))

    for shot in sorted(shared, key=rank):
        a, b = old[shot], new[shot]
        comparable, note = verdicts[shot]
        parts = []
        for f in FIELDS:
            if f not in a or f not in b:
                continue
            d = DECIMALS[f]
            delta = b[f] - a[f]
            parts.append(f"{f}={b[f]:.{d}f}({delta:+.{d}f})")
        tail = note
        if comparable is True and "meanLuma" in a and "meanLuma" in b:
            dl = abs(b["meanLuma"] - a["meanLuma"])
            tail = ("same vantage, BIGGER THAN A NORMAL BUILD STEP"
                    if dl > LUMA_STEP_P90 else "same vantage, a normal build step")
        out.append("FrameDrift:   " + shot + " " + " ".join(parts) + "  [" + tail + "]")
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
    # CLEANED ON EXIT, HOWEVER THE RUN ENDS — the sibling without this
    # pair leaked 17GB of 68MB temp dirs in a day (verify runs these
    # selftests on every commit) and red-walled the disk mid-verify.
    # Same two lines export-decode.py has carried since its own leak.
    import atexit as _ax, shutil as _sh
    _ax.register(_sh.rmtree, d, True)
    head = ("shot\tmeanLuma\tmaxLuma\tbrightPct\tsatPct\tsatStrength\t"
            "meanRgb\tbrightRgb\n")

    def write(name, body):
        p = d / name
        p.write_text("# comment\n" + head + body, encoding="utf-8")
        return str(p)

    # THE COMMIT STAMP, and both cases it distinguishes. A block that cannot
    # tell "same commit twice" from "two different commits" invites exactly the
    # misreading that happened once already: a run-to-run delta being taken for
    # a noise floor when the code in between had removed a white capsule from
    # every frame.
    same_a = d / "same_a.tsv"
    same_a.write_text("# commit abc1234def\n" + head +
                      "day1_noon\t0.250\t0.981\t1.42\t3.10\t0.41\t60,64,70\t250,250,250\n",
                      encoding="utf-8")
    same_b = d / "same_b.tsv"
    same_b.write_text("# commit abc1234def\n" + head +
                      "day1_noon\t0.251\t0.981\t1.42\t3.10\t0.41\t60,64,70\t250,250,250\n",
                      encoding="utf-8")
    check("reads a commit stamp", commit_of(str(same_a)) == "abc1234def")
    check("no stamp is None", commit_of(str(d / "nope.tsv")) is None)
    txt = "\n".join(drift(str(same_a), str(same_b))[0])
    check("same commit says it IS the noise floor", "IS the noise floor" in txt)
    diff_b = d / "diff_b.tsv"
    diff_b.write_text("# commit 9999999aaa\n" + head +
                      "day1_noon\t0.251\t0.981\t1.42\t3.10\t0.41\t60,64,70\t250,250,250\n",
                      encoding="utf-8")
    txt = "\n".join(drift(str(same_a), str(diff_b))[0])
    check("different commits are flagged", "DIFFERENT COMMITS" in txt)
    check("different commits refuse the floor", "cannot be read as either" in txt)

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

    # THE VANTAGE TEST, BOTH OUTCOMES AND THE THIRD ONE. Rule 5b: a guard
    # ships only when its ACCEPTING case has been watched too, and this one has
    # three answers rather than two — a ledger with no pose columns must not be
    # quietly counted as agreement.
    #
    # The accepting case is first on purpose: the expensive failure here is a
    # conditioner that marks everything unreadable, which looks exactly like a
    # render that never changes.
    posehead = ("shot\tmeanLuma\tmaxLuma\tbrightPct\tsatPct\tsatStrength\t"
                "meanRgb\tbrightRgb\tcamX\tcamZ\tcamYaw\n")

    def posewrite(name, luma, x, z, yaw, commit="abc1234def"):
        q = d / name
        q.write_text(f"# commit {commit}\n" + posehead +
                     f"day1_noon\t{luma}\t0.981\t1.42\t3.10\t0.41\t"
                     f"60,64,70\t250,250,250\t{x}\t{z}\t{yaw}\n",
                     encoding="utf-8")
        return str(q)

    still_a = posewrite("still_a.tsv", "0.250", "2.7", "18.8", "162")
    still_b = posewrite("still_b.tsv", "0.290", "2.8", "18.9", "162", "9999999aaa")
    txt = "\n".join(drift(still_a, still_b)[0])
    check("same vantage is ACCEPTED", "same vantage" in txt)
    check("a real change at a matched vantage is called out",
          "BIGGER THAN A NORMAL BUILD STEP" in txt)
    check("the readable count is printed", "1 of 1 shot(s) taken from the" in txt)

    quiet_b = posewrite("quiet_b.tsv", "0.253", "2.7", "18.8", "162", "9999999aaa")
    check("a small move at a matched vantage says so",
          "a normal build step" in "\n".join(drift(still_a, quiet_b)[0]))

    # REJECTING: the camera walked, so the delta is a different photograph.
    walked = posewrite("walked.tsv", "0.290", "-4.1", "11.9", "115", "9999999aaa")
    txt = "\n".join(drift(still_a, walked)[0])
    check("a moved camera is named", "CAMERA MOVED" in txt)
    check("a moved camera is not called readable",
          "NORMAL BUILD STEP" not in txt)
    check("a moved camera reports the distance", "m yaw" in txt)
    # Yaw alone is enough, and it is the axis the first analysis missed.
    turned = posewrite("turned.tsv", "0.290", "2.7", "18.8", "252", "9999999aaa")
    check("yaw alone disqualifies a pair",
          "CAMERA MOVED" in "\n".join(drift(still_a, turned)[0]))
    check("yaw wraps the short way round",
          vantage({"camX": 0.0, "camZ": 0.0, "camYaw": 359.6},
                  {"camX": 0.0, "camZ": 0.0, "camYaw": 0.2})[0] is True)

    # THE THIRD ANSWER: no pose columns at all. `a`/`b` are the old fixtures.
    txt = "\n".join(drift(a, b)[0])
    check("an unposed ledger is neither accepted nor rejected",
          "POSE NOT RECORDED" in txt)
    check("an unposed row says so", "[pose not recorded]" in txt)
    check("an unposed pair is not called same vantage", "same vantage" not in txt)

    # A READABLE MOVER OUTRANKS A LOUDER UNREADABLE ONE.
    two_a = d / "two_a.tsv"
    two_a.write_text("# commit abc1234def\n" + posehead +
                     "pinned\t0.250\t0.981\t1.42\t3.10\t0.41\t60,64,70\t250,250,250\t0\t0\t90\n"
                     "roamed\t0.250\t0.981\t1.42\t3.10\t0.41\t60,64,70\t250,250,250\t0\t0\t90\n",
                     encoding="utf-8")
    two_b = d / "two_b.tsv"
    two_b.write_text("# commit 9999999aaa\n" + posehead +
                     "pinned\t0.270\t0.981\t1.42\t3.10\t0.41\t60,64,70\t250,250,250\t0\t0\t90\n"
                     "roamed\t0.900\t0.981\t1.42\t3.10\t0.41\t60,64,70\t250,250,250\t40\t40\t270\n",
                     encoding="utf-8")
    txt = "\n".join(drift(str(two_a), str(two_b))[0])
    check("a readable mover ranks above a louder unreadable one",
          txt.index("FrameDrift:   pinned ") < txt.index("FrameDrift:   roamed "))

    check("pose columns are kept out of the compared fields",
          "camX=" not in txt.split("FrameDrift:   pinned ")[1].split("\n")[0])

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
