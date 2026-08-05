#!/usr/bin/env python3
"""RENDER THE BARK BANK TO AUDIO — the generator half of 17.2.

    python3 tools/voice-gen/ledger_voice_gen.py --plan       # free, no model
    python3 tools/voice-gen/ledger_voice_gen.py --selftest   # free, no network
    python3 tools/voice-gen/ledger_voice_gen.py --rate 20    # THE FIRST RUN
    python3 tools/voice-gen/ledger_voice_gen.py --all        # the batch

WHY THIS EXISTS. 17.2 had a fetcher for sourcing reference clips and a
benchmark for choosing an engine, and nothing that turns a line plus a
reference clip plus a direction into game audio. That was the whole gap, and
the roadmap had it filed as a casting problem.

WHAT IS ALREADY DECIDED, so none of it is re-litigated here:

  engine     chatterbox, offline, local, $0 — production-plan-audio-art §1i.
             It was the only one of four to pass the direction test, and the
             verdict was Jafar's ears, not a metric.
  identity   comes from the reference clip, NEVER from the engine's own voice
             ("don't like the actual voice"). Nineteen VCTK speakers who
             donated to speech research sit in game-design/picked-clips/.
  direction  comes from chatterbox's exaggeration parameter, bored 0.25
             through urgent 0.85.

THE NUMBER THAT COLLAPSED. The bark bank holds 2,604 lines and 2,268 of them
are PAIR slots — strings of the form "telling || reply" whose halves are
already present as atomic lines, enumerated so a human could review distinct
conversations. `BarkGen.Answer()` picks an opener and a reply INDEPENDENTLY at
run time, so those 2,268 strings are never spoken as written. Rendering them
would be seven times the work, and every file would be a line the game cannot
play. **336 lines is the real batch**, and `--plan` prints the split so nobody
has to take that on trust.

TWO THINGS THIS TOOL WILL NOT DO.

It never deletes and never overwrites without being told. CLAUDE.md rule 5 is
a CI run that committed an empty directory over 24 clips Jafar had already
listened to and picked from, and reported success. Rendering is resumable by
SKIPPING what exists; `--force` prints what it is about to replace, and counts
it, before it replaces anything.

And it does not pretend the direction map is measured. Rule 2 says never set a
number you have not measured, and the exaggeration values below cannot be
measured from this container — there is no GPU and the model is not here. So
they are AUTHORED, they are printed beside the brief they came from by
`--plan`, and `--rate` deliberately renders one line from each direction band
so the first thing anybody hears is whether the bands are distinguishable at
all. That is the measurement, named and deferred rather than skipped.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BARKS = ROOT / "game-design" / "barks.json"
CLIPS = ROOT / "game-design" / "picked-clips"

# THE SIX STREET VOICES. Barks carry no speaker — they are lines any passer-by
# says, which is why the bank has no `speaker` field and why an earlier reading
# of this task as "which characters get a voice" was aimed at the wrong thing.
CROWD = ["crowd_f1", "crowd_f2", "crowd_f3", "crowd_m1", "crowd_m2", "crowd_m3"]

# AUTHORED, NOT MEASURED — see the module docstring. The scale is chatterbox's
# own: 0.25 is bored, 0.85 is urgent. Each value is a claim about how the line
# is said, and every one should be argued with after the first listen.
DIRECTION = {
    "exchange.tell.doubtful":         0.35,  # hedging, does not want to own it
    "exchange.tell.secondhand":       0.40,  # passing it on, no stake
    "exchange.tell.certain":          0.55,  # they saw it themselves
    "exchange.answer.neutral":        0.35,
    "exchange.answer.greedy":         0.55,  # already working out the angle
    "exchange.answer.loyal":          0.50,
    "exchange.answer.nervous":        0.65,  # wants the subject changed
    "recognition.comments_plain":     0.40,
    "recognition.comments_sensitive": 0.50,
    "recognition.avoids":             0.30,  # said to the pavement, half heard
    "recognition.refuses":            0.60,
    "recognition.confronts":          0.80,  # the loudest thing in the game
    "ambient.open.slump":             0.35,
    "ambient.open.feud":              0.60,
    "ambient.open.injured":           0.55,
    "ambient.open.prices":            0.45,
    "ambient.open.night":             0.30,
    "ambient.open.ordinary":          0.35,
    # A REPLY IS CALMER THAN ITS OPENER, one band down, because the second
    # person has not just decided the subject is worth raising.
    "ambient.reply.slump":            0.30,
    "ambient.reply.feud":             0.55,
    "ambient.reply.injured":          0.50,
    "ambient.reply.prices":           0.40,
    "ambient.reply.night":            0.25,
    "ambient.reply.ordinary":         0.30,
}

PAIR_SEP = "||"


def load_slots():
    if not BARKS.exists():
        return [], []
    data = json.loads(BARKS.read_text())
    atomic, pair = [], []
    for s in data.get("slots", []):
        (pair if is_pair(s) else atomic).append(s)
    return atomic, pair


def is_pair(slot):
    """A PAIR SLOT IS A REVIEW ARTEFACT, NOT A PLAYBACK UNIT.

    Detected from the lines rather than the id, because the id convention
    (`exchange.pair.*`, `ambient.pair.*`) is a naming habit and the separator
    is the actual fact. If somebody adds a pair slot under a new name this
    still catches it; if somebody renames the ids this still catches it.
    """
    return any(PAIR_SEP in ln for ln in slot.get("lines", []))


def plan(atomic, pair, voices_per_line):
    """Every line that will be rendered, with its voice and direction.

    DETERMINISTIC BY POSITION, not by hash — a re-run must produce the exact
    same assignment or skipping-what-exists re-renders the world under new
    names. Slot order comes from the JSON array and lines from within it, so
    both are stable.

    AND THE COUNTER IS GLOBAL, NOT PER SLOT, which is a correction to the
    first version of this function. Every slot holds 14 lines and there are 6
    voices; 14 % 6 = 2, so a per-slot counter handed the first two voices an
    extra line in EVERY slot and the spread came out [48 48 48 48 72 72]. Two
    of the six street voices would have carried half again as much of the
    street as the others, for a reason nobody chose.

    Worse, the self-test passed it, because I had written the evenness bound
    loose enough to accept exactly the gap it produced. That is rule 2 in its
    purest form — a threshold set to make a reading green rather than from
    what the reading should be. 336 lines over 6 voices is 56 each with no
    remainder, so the honest bound is equality, and it is asserted as such.
    """
    jobs = []
    g = 0
    for slot in atomic:
        sid = slot["id"]
        ex = DIRECTION.get(sid)
        for i, line in enumerate(slot.get("lines", [])):
            for m in range(voices_per_line):
                # +m, so the k voices for one line are always k DISTINCT
                # voices for any k <= len(CROWD). A stride wider than 1 looks
                # tidier and collides at k=6.
                voice = CROWD[(g + m) % len(CROWD)]
                jobs.append({
                    "slot": sid,
                    "index": i,
                    "line": line,
                    "voice": voice,
                    "exaggeration": ex,
                    "file": f"{sid}.{i:03d}.{voice}.wav",
                })
            g += 1
    return jobs


def unmapped(atomic):
    """Slots with no direction. A LINE WITH NO DIRECTION IS NOT A DEFAULT, it
    is a slot somebody added and nobody voiced, and it must not render at a
    silently-chosen number."""
    return [s["id"] for s in atomic if DIRECTION.get(s["id"]) is None]


def cmd_plan(args):
    atomic, pair = load_slots()
    if not atomic and not pair:
        print(f"voice-gen: no bark bank at {BARKS} — nothing to plan")
        return 1

    na = sum(len(s["lines"]) for s in atomic)
    npair = sum(len(s["lines"]) for s in pair)
    jobs = plan(atomic, pair, args.voices_per_line)

    print(f"  bark bank            {na + npair} lines in {len(atomic) + len(pair)} slots")
    print(f"  PAIR slots           {len(pair):3d} slots, {npair} lines — assembled at run time, "
          f"rendering NONE")
    print(f"  atomic slots         {len(atomic):3d} slots, {na} lines — the real batch")
    print(f"  voices per line      {args.voices_per_line} of {len(CROWD)} street voices")
    print(f"  RENDERS              {len(jobs)}")
    print()

    missing = unmapped(atomic)
    if missing:
        print("  SLOTS WITH NO DIRECTION — refusing to guess one:")
        for m in missing:
            print(f"    {m}")
        print()

    if args.verbose:
        print("  direction map, with the brief each value is a claim about:")
        for slot in atomic:
            brief = re.sub(r"\s+", " ", slot.get("brief", ""))[:64]
            print(f"    {DIRECTION.get(slot['id'], '  ?'):>5}  {slot['id']:<34} {brief}")
        print()

    have = sum(1 for j in jobs if (args.out / j["file"]).exists()) if args.out.exists() else 0
    print(f"  already rendered     {have} of {len(jobs)}   (a re-run renders {len(jobs) - have})")
    return 1 if missing else 0


def cmd_selftest(args):
    """EVERYTHING EXCEPT THE MODEL. No network, no GPU, no chatterbox.

    This is the shape `tools/voice-fetch/` proved: its 22 checks touch nothing
    remote, which is the only reason any of it could be trusted from a
    container where the download itself cannot be tested. The same applies
    here one layer along — the render cannot run here, so everything that
    DECIDES a render is what gets checked.
    """
    fails, ran = [], []

    def check(ok, what):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}")
        ran.append(what)
        if not ok:
            fails.append(what)

    atomic, pair = load_slots()
    check(len(atomic) > 0, f"the bark bank loads ({len(atomic)} atomic slots)")
    check(len(pair) > 0, f"pair slots are recognised ({len(pair)} found)")

    # THE FINDING THIS TOOL IS BUILT ON, asserted rather than remembered.
    check(all(PAIR_SEP not in ln for s in atomic for ln in s["lines"]),
          "no atomic slot contains a pair separator")
    check(all(any(PAIR_SEP in ln for ln in s["lines"]) for s in pair),
          "every pair slot contains the separator")

    # AND THE ACCEPTING CASE, rule 5b — the half that goes unrun. A pair line's
    # halves must ALREADY EXIST as atomic lines, or dropping the pair slots
    # would drop content instead of duplication, and this tool would be
    # deleting work rather than saving it.
    atomic_lines = {ln.strip() for s in atomic for ln in s["lines"]}
    covered = 0
    sampled = 0
    for s in pair:
        for ln in s["lines"][:20]:
            sampled += 1
            halves = [h.strip() for h in ln.split(PAIR_SEP)]
            if all(h in atomic_lines for h in halves):
                covered += 1
    check(sampled > 0 and covered == sampled,
          f"every sampled pair line is two existing atomic lines ({covered}/{sampled})")

    check(not unmapped(atomic),
          f"every atomic slot has an authored direction ({len(DIRECTION)} mapped)")
    check(all(0.2 <= v <= 0.9 for v in DIRECTION.values()),
          "every direction sits inside chatterbox's 0.25-0.85 range")

    jobs = plan(atomic, pair, 1)
    check(len(jobs) == sum(len(s["lines"]) for s in atomic),
          f"one voice per line renders each line exactly once ({len(jobs)})")
    check(len({j["file"] for j in jobs}) == len(jobs),
          "no two renders collide on a filename")

    # DETERMINISM, which is what makes resume safe: the same call twice must
    # assign the same voice to the same line, or a re-run silently re-renders
    # everything under new names and the directory doubles.
    check([j["file"] for j in plan(atomic, pair, 1)] == [j["file"] for j in jobs],
          "the plan is deterministic across calls")

    # EQUALITY, NOT A TOLERANCE. 336 lines over 6 voices divides exactly, so
    # any gap at all is an assignment bug — and the first version of this
    # check carried a tolerance wide enough to accept the [48 48 48 48 72 72]
    # the first version of `plan` produced. A bound chosen to make a reading
    # pass is the fault CLAUDE.md rule 2 exists for, and I wrote one into the
    # guard for it.
    spread = {}
    for j in jobs:
        spread[j["voice"]] = spread.get(j["voice"], 0) + 1
    check(len(spread) == len(CROWD) and len(set(spread.values())) == 1,
          f"all {len(CROWD)} street voices carry an equal share ({sorted(spread.values())})")

    for k in (2, 3, 6):
        multi = plan(atomic, pair, k)
        check(len(multi) == k * len(jobs), f"{k} voices per line scales the batch ({len(multi)})")
        check(len({j["file"] for j in multi}) == len(multi),
              f"no filename collisions at {k} voices per line")
        per_line = {}
        for j in multi:
            per_line.setdefault((j["slot"], j["index"]), set()).add(j["voice"])
        check(all(len(v) == k for v in per_line.values()),
              f"every line gets {k} DISTINCT voices, never the same one twice")

    # THE REFERENCE CLIPS THE RENDER WILL NEED. A denominator, rule 3b: "0
    # missing" and "nothing was checked" must not print the same way.
    want = set(CROWD)
    found = {p.name.split(".")[0] for p in CLIPS.glob("*.mp3")} if CLIPS.exists() else set()
    check(want <= found,
          f"all {len(want)} street reference clips are on disk "
          f"({len(found)} clips present, missing: {sorted(want - found) or 'none'})")

    # COUNTED, NOT TYPED. The first version printed a hardcoded "13 checks"
    # while running 14 — a number in the output that no longer described the
    # thing it was next to, which is what most of CLAUDE.md is about.
    print()
    print(f"voice-gen --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks, none of which touch the network or the model")
    return 0 if not fails else 1


def render_one(job, out_dir, model):
    """One line to one file. Returns seconds taken, or None if skipped."""
    dest = out_dir / job["file"]
    if dest.exists():
        return None
    t0 = time.time()
    wav = model.generate(job["line"],
                         audio_prompt_path=str(job["ref"]),
                         exaggeration=job["exaggeration"])
    import torchaudio  # noqa: F401  — only ever imported on a real render
    torchaudio.save(str(dest), wav, model.sr)
    return time.time() - t0


def load_model():
    """Imported here and nowhere else, so every free mode runs without it."""
    try:
        from chatterbox.tts import ChatterboxTTS
    except ImportError:
        print("voice-gen: chatterbox is not installed in this environment.")
        print("  This is expected in CI and in the dev container — the render")
        print("  runs on Jafar's machine. --plan and --selftest work here.")
        return None
    return ChatterboxTTS.from_pretrained(device="cuda")


def cmd_rate(args):
    """THE FIRST RUN, and the only number nobody has.

    Prints the SERIES before any summary, on purpose. CLAUDE.md rule 2: a
    median cannot see a tail and a mean cannot see a warm-up, and the FIRST
    render includes loading the model, so a mean over a short run is mostly
    that load. The series makes the shape obvious in one glance.

    It renders one line per direction band rather than the first N lines, so
    the first thing anybody listens to answers the question the direction map
    cannot answer from here: are the bands actually distinguishable.
    """
    atomic, pair = load_slots()
    jobs = plan(atomic, pair, 1)
    by_dir = {}
    for j in jobs:
        by_dir.setdefault(j["exaggeration"], j)
    sample = list(by_dir.values())[:args.n]
    for j in sample:
        j["ref"] = CLIPS / next(iter(sorted(p.name for p in CLIPS.glob(j["voice"] + ".*"))), "")

    model = load_model()
    if model is None:
        print(f"\n  the sample it WOULD have rendered: {len(sample)} lines, "
              f"one per direction band, {sorted(by_dir)}")
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    series = []
    for j in sample:
        took = render_one(j, args.out, model)
        if took is not None:
            series.append(took)
            print(f"  {took:6.2f}s  ex={j['exaggeration']}  {j['slot']}  {j['line'][:52]}")

    if not series:
        print("voice-gen --rate: every sampled line already existed. Nothing measured.")
        return 0

    ordered = sorted(series)
    med = ordered[len(ordered) // 2]
    total = len(plan(atomic, pair, args.voices_per_line))
    print()
    print(f"  series (render order) : {[round(s, 2) for s in series]}")
    print(f"  first render          : {series[0]:.2f}s  <- includes model load, not typical")
    print(f"  median                : {med:.2f}s")
    print(f"  FULL BATCH PROJECTION : {total} renders x {med:.2f}s = "
          f"{total * med / 3600:.1f} hours")
    return 0


def cmd_all(args):
    atomic, pair = load_slots()
    missing = unmapped(atomic)
    if missing:
        print(f"voice-gen: {len(missing)} slot(s) have no direction — refusing to render "
              f"at a guessed number. Run --plan.")
        return 1

    jobs = plan(atomic, pair, args.voices_per_line)
    for j in jobs:
        j["ref"] = CLIPS / next(iter(sorted(p.name for p in CLIPS.glob(j["voice"] + ".*"))), "")

    args.out.mkdir(parents=True, exist_ok=True)
    existing = [j for j in jobs if (args.out / j["file"]).exists()]

    # RULE 5, AND IT IS THE ONE THAT COST 24 CLIPS. Nothing is replaced
    # silently, and the count is printed BEFORE the work rather than after.
    if existing and args.force:
        print(f"voice-gen: --force will REPLACE {len(existing)} existing render(s).")
        for j in existing[:5]:
            print(f"    {j['file']}")
        if len(existing) > 5:
            print(f"    (+{len(existing) - 5} more)")
        for j in existing:
            (args.out / j["file"]).unlink()
    elif existing:
        print(f"voice-gen: skipping {len(existing)} already rendered "
              f"(--force to replace them)")

    model = load_model()
    if model is None:
        return 2

    done, series = 0, []
    for n, j in enumerate(jobs, 1):
        took = render_one(j, args.out, model)
        if took is not None:
            done += 1
            series.append(took)
            if done % 25 == 0:
                med = sorted(series)[len(series) // 2]
                left = (len(jobs) - n) * med / 60
                print(f"  {n}/{len(jobs)}  median {med:.2f}s  ~{left:.0f} min left")

    manifest = args.out / "barks-manifest.json"
    manifest.write_text(json.dumps(
        {"renders": [{k: v for k, v in j.items() if k != "ref"} for j in jobs]}, indent=1))
    print(f"voice-gen: {done} rendered, {len(jobs) - done} already present, "
          f"manifest at {manifest}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", action="store_true", help="what would render, no model needed")
    ap.add_argument("--selftest", action="store_true", help="everything except the model")
    ap.add_argument("--rate", type=int, dest="n", metavar="N",
                    help="render N lines, one per direction band, and print the rate")
    ap.add_argument("--all", action="store_true", help="render the batch, resumable")
    ap.add_argument("--voices-per-line", type=int, default=1,
                    help="how many of the six street voices each line is rendered in")
    ap.add_argument("--force", action="store_true", help="replace existing renders")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--out", type=Path,
                    default=ROOT / "ledger" / "Assets" / "Resources" / "voice" / "barks")
    args = ap.parse_args()

    if args.selftest:
        return cmd_selftest(args)
    if args.n:
        return cmd_rate(args)
    if args.all:
        return cmd_all(args)
    return cmd_plan(args)


if __name__ == "__main__":
    sys.exit(main())
