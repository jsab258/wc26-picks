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
play. **336 atomic lines, of which 335 render** — one is "...", a real bark
that is silence and that the game plays by playing no clip. `--plan` prints
every one of those numbers so none of them has to be taken on trust.

TWO THINGS THIS TOOL WILL NOT DO.

It never deletes and never overwrites without being told. CLAUDE.md rule 5 is
a CI run that committed an empty directory over 24 clips Jafar had already
listened to and picked from, and reported success. Rendering is resumable by
SKIPPING what exists; `--force` prints what it is about to replace, and counts
it, before it replaces anything.

THE DIRECTION MAP WAS AUTHORED AND IS NOW CONFIRMED. Rule 2 says never set a
number you have not measured, and these could not be measured from this
container — no GPU, no model. So they shipped as a named guess, `--rate`
sampled one line per band rather than the first twenty so the first listen
would answer it, and on 5 August Jafar listened to bands 0.25, 0.30, 0.45,
0.60 and 0.80 and said they sound good.

That is the deferred measurement actually being taken rather than quietly
forgotten, which is the half of rule 2 that usually goes missing. The values
are still open to argument; they are no longer unverified.
"""
import argparse
import hashlib
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

# AUTHORED, THEN CONFIRMED BY EAR ON 5 AUGUST — see the module docstring. The
# scale is chatterbox's own: 0.25 is bored, 0.85 is urgent. Five bands were
# rendered and listened to (0.25, 0.30, 0.45, 0.60, 0.80) and they read as
# different people in different moods, which is the whole question.
#
# This comment said "AUTHORED, NOT MEASURED" for as long as that was true and
# stopped being true the moment somebody listened. A comment that survives the
# fact it describes is most of what CLAUDE.md is a list of, so it is updated
# in the same commit as the listening rather than the next time anybody
# happens to read it.
#
# Each value is still a claim about how a line is said and still open to
# argument. It is no longer unverified.
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

# A renderable line needs at least one letter or digit. Anything else is a
# beat the game plays as silence, not a clip to generate.
HAS_WORDS = re.compile(r"[A-Za-z0-9]")


def load_slots():
    if not BARKS.exists():
        return [], []
    # UTF-8, SAID OUT LOUD, AND IT WAS IN THE AUDIO BEFORE IT WAS SAID.
    #
    # `read_text()` with no encoding uses the platform default, which is UTF-8
    # here and cp1252 on Jafar's Windows box. So the first real run on his
    # machine handed the model
    #     "Bit of nonsense going about â€” the new owner..."
    # where the bark says "—". Not a console artefact: the string itself was
    # decoded wrong, so those three characters were rendered into the wave.
    #
    # It could not happen on the machine the tool was written on, which is the
    # whole shape of it — a default that differs per platform is a bug that
    # only exists on somebody else's computer, and the only reason this was
    # caught is that the render prints the line it is speaking.
    data = json.loads(BARKS.read_text(encoding="utf-8"))
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
            # A LINE WITH NO WORDS IN IT IS SILENCE, AND SILENCE IS NOT A CLIP.
            # `recognition.avoids` holds "..." — a real bark, somebody looking
            # away and not answering — and the first run spent twelve seconds
            # rendering it into a wave of nothing. The game plays that beat by
            # playing NO clip, so there is nothing to generate.
            #
            # Skipped rather than failed. A guard that refuses the whole batch
            # over one correct line is the ratchet CLAUDE.md rule 5 warns
            # about: it cannot tell a regression from a thing that was always
            # meant to be that way. `--plan` prints the count instead, so the
            # skip is visible rather than silent.
            if not HAS_WORDS.search(line):
                continue
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
    skipped = sum(1 for s in atomic for ln in s["lines"] if not HAS_WORDS.search(ln))
    print(f"  atomic slots         {len(atomic):3d} slots, {na} lines — the real batch")
    if skipped:
        print(f"  wordless             {skipped} line(s) skipped — silence, "
              f"the game plays these by playing no clip")
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

    stamps = load_stamps(args.out)
    st = {}
    for j in jobs:
        k = state_of(j, args.out, stamps)
        st[k] = st.get(k, 0) + 1
    print(f"  on disk and correct  {st.get('fresh', 0)}")
    if st.get("stale"):
        print(f"  STALE                {st['stale']} — the text, voice or direction "
              f"changed since these were made; they WILL be re-rendered")
    if st.get("unknown"):
        print(f"  unknown provenance   {st['unknown']} — rendered before the ledger "
              f"existed, so nothing says what they were made from; re-rendered")
    print(f"  to render            {st.get('missing', 0) + st.get('stale', 0) + st.get('unknown', 0)}"
          f" of {len(jobs)}")

    # FILES NOTHING PLANS TO PLAY. Five of these landed in the first batch:
    # rate-test clips whose names stopped matching when skipping the wordless
    # line shifted every voice assignment after it. Harmless to the game,
    # which only ever looks up planned names — and invisible, which is the
    # problem. An orphan is either dead weight or evidence that the plan
    # changed under a finished batch, and both are things to be told about.
    if args.out.exists():
        planned = {j["file"] for j in jobs}
        orphans = sorted(q.name for q in args.out.glob("*.wav") if q.name not in planned)
        if orphans:
            print(f"  ORPHANS              {len(orphans)} file(s) on disk that nothing "
                  f"plans to play:")
            for o in orphans[:6]:
                print(f"                         {o}")
            if len(orphans) > 6:
                print(f"                         (+{len(orphans) - 6} more)")
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

    # THE MOJIBAKE GUARD. UTF-8 read as cp1252 has an unmistakable signature —
    # "â€”" for an em-dash, "â€™" for an apostrophe — and the first real run on
    # Windows put exactly that into the model's mouth. Asserted on the loaded
    # strings rather than on the call, because the call is what was wrong and
    # checking my own fix by reading my own line is not a check.
    mojibake = [ln for s in atomic for ln in s["lines"]
                if "â€" in ln or "Ã" in ln]
    check(not mojibake,
          f"no line was decoded as cp1252 ({len(mojibake)} mojibake line(s))")

    # AND A LINE WITH NOTHING TO SAY. `recognition.avoids` holds "...", which
    # took twelve seconds to render into a wave of nothing. It is a real bark —
    # somebody looking away and not answering — but it is SILENCE, and silence
    # is a thing the game should play by playing no clip at all.
    speechless = [ln for s in atomic for ln in s["lines"] if not HAS_WORDS.search(ln)]
    rendered = {j["line"] for j in plan(atomic, pair, 1)}
    check(speechless and not (set(speechless) & rendered),
          f"wordless lines are skipped, not rendered "
          f"({len(speechless)} skipped: {speechless[:3]})")

    check(not unmapped(atomic),
          f"every atomic slot has an authored direction ({len(DIRECTION)} mapped)")
    check(all(0.2 <= v <= 0.9 for v in DIRECTION.values()),
          "every direction sits inside chatterbox's 0.25-0.85 range")

    jobs = plan(atomic, pair, 1)
    # RENDERABLE lines, not all lines — the wordless one is deliberately not
    # among them, and comparing against the raw total is how this check went
    # red on a correct skip a minute after the skip was added.
    renderable = sum(1 for s in atomic for ln in s["lines"] if HAS_WORDS.search(ln))
    check(len(jobs) == renderable,
          f"one voice per line renders each speakable line exactly once "
          f"({len(jobs)} of {sum(len(s['lines']) for s in atomic)} lines)")
    check(len({j["file"] for j in jobs}) == len(jobs),
          "no two renders collide on a filename")

    # DETERMINISM, which is what makes resume safe: the same call twice must
    # assign the same voice to the same line, or a re-run silently re-renders
    # everything under new names and the directory doubles.
    check([j["file"] for j in plan(atomic, pair, 1)] == [j["file"] for j in jobs],
          "the plan is deterministic across calls")

    # THE BOUND IS DERIVED FROM THE ARITHMETIC, EVERY TIME IT IS ASKED.
    #
    # This has now been wrong in both directions in one afternoon, which is
    # why it is computed rather than typed. First it was a tolerance loose
    # enough to accept [48 48 48 48 72 72] — a bound picked to make a reading
    # green, the exact thing rule 2 forbids. Then it was hard equality, which
    # was right for 336 renders over 6 voices and went red the moment skipping
    # the wordless line made it 335.
    #
    # An N that divides by V admits a perfect split and anything else is a
    # bug; an N that does not can be off by at most one, and demanding better
    # would be demanding the impossible. So the tightest TRUE bound is
    # `1 if N % V else 0`, and writing it that way means it can never again be
    # loosened to pass or left too tight to be satisfiable.
    spread = {}
    for j in jobs:
        spread[j["voice"]] = spread.get(j["voice"], 0) + 1
    allowed = 1 if len(jobs) % len(CROWD) else 0
    gap = max(spread.values()) - min(spread.values()) if spread else -1
    check(len(spread) == len(CROWD) and gap == allowed,
          f"all {len(CROWD)} voices share {len(jobs)} renders as evenly as "
          f"{len(jobs)} allows (gap {gap}, tightest possible {allowed}) "
          f"{sorted(spread.values())}")

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

    # THE FOUR RESUME STATES, on real files in a temp directory, because this
    # is the check that would have let five corrupted clips ship. Rule 5b: the
    # accepting case (fresh) is asserted alongside the rejecting ones.
    import tempfile, shutil
    tmp = Path(tempfile.mkdtemp())
    try:
        j = plan(atomic, pair, 1)[0]
        check(state_of(j, tmp, {}) == "missing", "a clip that is not there is 'missing'")
        (tmp / j["file"]).write_bytes(b"x")
        check(state_of(j, tmp, {}) == "unknown",
              "a clip with no ledger entry is 'unknown', not assumed good")
        st = {j["file"]: stamp(j)}
        check(state_of(j, tmp, st) == "fresh", "a clip matching its ledger is 'fresh'")
        moved = dict(j); moved["line"] = j["line"] + " and then some"
        check(state_of(moved, tmp, st) == "stale", "changing the TEXT makes it 'stale'")
        redir = dict(j); redir["exaggeration"] = 0.99
        check(state_of(redir, tmp, st) == "stale", "changing the DIRECTION makes it 'stale'")
        othervoice = dict(j); othervoice["voice"] = "crowd_m3"
        check(stamp(othervoice) != stamp(j), "the voice is part of what a clip was made from")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # THE BATCH LOOP ITSELF, WALKED END TO END. This is the check that was
    # missing when `--all` shipped with a NameError on its working line: every
    # other mode runs without a model, so every other mode was tested, and the
    # one the tool exists for was not. Rule 5b, aimed at the author.
    tmp2 = Path(tempfile.mkdtemp())
    try:
        class A2:
            pass
        a2 = A2()
        a2.out, a2.voices_per_line, a2.force, a2.dry_run = tmp2, 1, False, True
        import io as _io, contextlib as _c
        buf = _io.StringIO()
        with _c.redirect_stdout(buf):
            rc1 = cmd_all(a2)
            rc2 = cmd_all(a2)
        made = len(list(tmp2.glob("*.wav")))
        check(rc1 == 0 and rc2 == 0, f"the batch runs twice without erroring ({rc1}, {rc2})")
        check(made == len(plan(atomic, pair, 1)),
              f"the first pass renders every job ({made})")
        check("0 rendered" in buf.getvalue(),
              "the second pass renders nothing, because the ledger says so")
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)

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
    # THE RENDER COUNT GOES IN THE SUMMARY so `verify.py` can read it instead
    # of carrying its own copy. It carried "336-line batch" as a literal, and
    # skipping the wordless line made that 335 — a number typed from memory in
    # the footer whose entire reason for existing is that I once typed
    # "2764 CoreTests" when it was 2742.
    print(f"voice-gen --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks, {len(jobs)} renders, none of which touch the "
          f"network or the model")
    return 0 if not fails else 1


def stamp(job):
    """What this clip was rendered FROM. Text, voice and direction — change any
    of the three and the wave on disk is wrong."""
    key = f"{job['line']}\x00{job['voice']}\x00{job['exaggeration']}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def load_stamps(out_dir):
    f = out_dir / "rendered.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def save_stamps(out_dir, stamps):
    (out_dir / "rendered.json").write_text(
        json.dumps(stamps, indent=1, sort_keys=True), encoding="utf-8")


def state_of(job, out_dir, stamps):
    """fresh / stale / unknown / missing — and the middle two are the point.

    THE FIRST VERSION SKIPPED ON THE FILENAME ALONE, and the filename is
    `{slot}.{index}.{voice}.wav`, which says nothing about the words. So when
    the em-dash encoding bug was fixed and the bark text changed, the clips
    already on disk kept their names, kept being skipped, and would have
    SHIPPED with `â€"` spoken into them. Jafar's second rate run rendered five
    lines instead of twenty for exactly this reason and the five it skipped
    were the corrupted ones.

    That is CLAUDE.md rule 5 in its purest form: a resume that cannot tell
    "already correct" from "already wrong" is not a resume, it is a way to
    make a bad artefact permanent. So what a clip was rendered from is written
    down beside it, and anything that disagrees is re-rendered.

    `unknown` is its own state rather than being folded into `stale`, because
    a clip with no record is not evidence of anything — it predates the
    ledger — and saying so is the difference between a fact and a guess.
    """
    if not (out_dir / job["file"]).exists():
        return "missing"
    had = stamps.get(job["file"])
    if had is None:
        return "unknown"
    return "fresh" if had == stamp(job) else "stale"


class DryModel:
    """A renderer that writes a placeholder instead of audio.

    THE ONLY PATH THAT NEEDED A GPU WAS THE ONLY PATH NEVER EXECUTED HERE, and
    it shipped with a `NameError` in it — `stamps` used and never defined — on
    the line that does the actual work. `--plan` and `--selftest` both passed,
    because neither of them enters this loop.

    That is rule 5b aimed at myself: a guard has two outcomes and shipping it
    means having watched both, and I had watched every path except the one the
    tool exists for. It cost Jafar a failed two-hour batch he had already
    pressed the key on.

    So the batch loop can now be walked end to end with no model, no GPU and
    no download. It proves nothing about the AUDIO. It proves the code around
    the audio runs, which is the part that was broken."""
    sr = 24000
    dry = True

    def generate(self, text, audio_prompt_path=None, exaggeration=None):
        return None


def render_one(job, out_dir, model, stamps):
    """One line to one file. Returns seconds taken, or None if skipped."""
    if state_of(job, out_dir, stamps) == "fresh":
        return None
    dest = out_dir / job["file"]
    t0 = time.time()
    wav = model.generate(job["line"],
                         audio_prompt_path=str(job["ref"]),
                         exaggeration=job["exaggeration"])
    if getattr(model, "dry", False):
        dest.write_bytes(b"DRY RUN - not audio")
    else:
        import torchaudio  # noqa: F401  — only ever imported on a real render
        # 16-BIT PCM, NOT torchaudio's DEFAULT 32-BIT FLOAT. The first batch
        # shipped as format 3 IEEE float: 87 MB for 335 clips where the same
        # audio is 43 MB as ordinary PCM, and Python's own `wave` module
        # cannot even open it ("unknown format: 3"), which is how it was
        # noticed — a check that opens the artefact found what nothing else
        # was measuring.
        #
        # Nothing audible is lost. These are 24 kHz mono speech clips with a
        # 2.5-second median; 16-bit is the format every game engine expects
        # and the one Unity would quantise to on import regardless.
        #
        # THE EXISTING 335 ARE DELIBERATELY NOT CONVERTED. They are correct
        # audio, and git already holds the 87 MB permanently — rewriting them
        # would add 43 MB MORE to history to save space in the working tree
        # only. The cost is already paid; this stops it being paid twice.
        torchaudio.save(str(dest), wav, model.sr,
                        encoding="PCM_S", bits_per_sample=16)
    stamps[job["file"]] = stamp(job)
    return time.time() - t0


def load_model():
    """Imported here and nowhere else, so every free mode runs without it.

    IT NAMES THE DEVICE, because a rate with no device beside it cannot be
    read at all. The engine benchmark measured chatterbox at about 6x slower
    than real time on a CPU, and a GPU moves that by more than an order of
    magnitude — so "24 seconds a line" means "leave it running overnight" or
    "it is already finished" depending entirely on a fact the number does not
    carry. Rule 3b: the reading ships with what produced it.

    The first version hardcoded device="cuda", which at least fails loudly on
    a machine without one. Falling silently back to CPU and reporting a rate
    is the failure that wastes a night, so this reports the fall rather than
    taking it quietly."""
    try:
        from chatterbox.tts import ChatterboxTTS
    except ImportError:
        print("voice-gen: chatterbox is not installed in this environment.")
        print("  This is expected in CI and in the dev container — the render")
        print("  runs on Jafar's machine. --plan and --selftest work here.")
        return None, None
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        name = torch.cuda.get_device_name(0) if device == "cuda" else "no CUDA device"
    except Exception as e:
        device, name = "cpu", f"torch would not report ({e})"

    print(f"  device: {device.upper()} — {name}")
    if device == "cpu":
        # NOT A WARNING, BECAUSE IT IS NOT A FAULT. The first version of this
        # message shouted WARNING and told him a GPU would be faster, which
        # is true, useless, and sends him hunting for a driver that cannot
        # exist: production-plan-audio-art §1g settled this on 28 July — his
        # card is AMD, PyTorch has no Windows AMD backend, ROCm is Linux only.
        # CPU is the expected state here and always was.
        #
        # The plan also records somebody reading "gpu: none detected" as a
        # PATH problem and chasing it. A message that implies a fix exists,
        # when none does, is how that happens twice.
        print("  This is the CPU, which is correct here and not a fault — the")
        print("  card is AMD and PyTorch has no Windows AMD backend (decided")
        print("  28 July, production-plan-audio-art §1g). Nothing to fix.")
    return ChatterboxTTS.from_pretrained(device=device), device


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

    model, device = load_model()
    if model is None:
        print(f"\n  the sample it WOULD have rendered: {len(sample)} lines, "
              f"one per direction band, {sorted(by_dir)}")
        return 2

    stamps = load_stamps(args.out)
    args.out.mkdir(parents=True, exist_ok=True)
    series = []
    for j in sample:
        took = render_one(j, args.out, model, stamps)
        if took is not None:
            series.append(took)
            print(f"  {took:6.2f}s  ex={j['exaggeration']}  {j['slot']}  {j['line'][:52]}")

    save_stamps(args.out, stamps)
    if not series:
        print("voice-gen --rate: every sampled line was already correct on disk. "
              "Nothing measured — delete the folder to force a fresh timing.")
        return 0
    # HOW MANY IT ACTUALLY DID, because the banner promised twenty and Jafar's
    # second run rendered five. A sample size is part of the statistic and
    # nothing in the old output said what it was.
    if len(series) < len(sample):
        print(f"\n  NOTE: {len(series)} of {len(sample)} sampled lines were rendered; "
              f"the rest were already correct on disk.")

    ordered = sorted(series)
    med = ordered[len(ordered) // 2]
    total = len(plan(atomic, pair, args.voices_per_line))
    print()
    print(f"  series (render order) : {[round(s, 2) for s in series]}")
    print(f"  first render          : {series[0]:.2f}s  <- includes model load, not typical")
    print(f"  median                : {med:.2f}s")
    print(f"  FULL BATCH PROJECTION : {total} renders x {med:.2f}s = "
          f"{total * med / 3600:.1f} hours   ON {device.upper()}")
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
    stamps = load_stamps(args.out)

    # THE FOUR STATES, NOT "DOES THE FILE EXIST". This block still said
    # "skipping 10 already rendered" after the ledger went in — the ledger was
    # wired into `--rate` and this path kept its old filename test, so the ten
    # clips it was about to skip were exactly the ten the ledger had just
    # classified as unknown provenance. Two implementations of one idea, and
    # the one nobody looked at was the one missing the line.
    by_state = {}
    for j in jobs:
        by_state.setdefault(state_of(j, args.out, stamps), []).append(j)
    fresh = by_state.get("fresh", [])
    stale = by_state.get("stale", []) + by_state.get("unknown", [])

    # THE MODEL LOADS BEFORE ANYTHING IS DELETED, and the first version of
    # this function got that backwards — it unlinked the existing renders
    # under --force and THEN discovered whether chatterbox was installed. On a
    # machine without it that is a command which deletes a night of audio,
    # renders nothing, and exits.
    #
    # Which is rule 5 exactly, in the file whose own docstring points at rule
    # 5. The CI run that cost 24 picked clips did the same thing in the same
    # order: destroy first, find out afterwards. Nothing may be removed until
    # the thing that would replace it is known to exist.
    if args.dry_run:
        model, device = DryModel(), "dry-run"
        print("  DRY RUN — walking every job, writing placeholders, no audio")
    else:
        model, device = load_model()
    if model is None:
        if fresh and args.force:
            print(f"  ({len(fresh)} correct render(s) NOT deleted — "
                  f"nothing could have replaced them)")
        return 2

    # RULE 5 AGAIN, the other half: nothing is replaced silently, and the
    # count is printed BEFORE the work rather than after. `--force` is only
    # about the clips that are ALREADY CORRECT — stale and unknown ones are
    # re-rendered without asking, because leaving them is the bug.
    if fresh and args.force:
        print(f"voice-gen: --force will REPLACE {len(fresh)} correct render(s).")
        for j in fresh[:5]:
            print(f"    {j['file']}")
        if len(fresh) > 5:
            print(f"    (+{len(fresh) - 5} more)")
        for j in fresh:
            stamps.pop(j["file"], None)
    elif fresh:
        print(f"voice-gen: {len(fresh)} already correct, skipping "
              f"(--force to redo them)")
    if stale:
        print(f"voice-gen: {len(stale)} stale or unrecorded — re-rendering these")

    done, series = 0, []
    for n, j in enumerate(jobs, 1):
        took = render_one(j, args.out, model, stamps)
        if took is not None:
            done += 1
            series.append(took)
            if done % 25 == 0:
                med = sorted(series)[len(series) // 2]
                left = (len(jobs) - n) * med / 60
                print(f"  {n}/{len(jobs)}  median {med:.2f}s  ~{left:.0f} min left")
                # SAVED AS IT GOES, not at the end. Two hours of rendering
                # behind a single write at the finish means one crash, one
                # closed window or one power cut turns every clip on disk back
                # into "unknown provenance" and the next run redoes all of it.
                save_stamps(args.out, stamps)

    save_stamps(args.out, stamps)
    manifest = args.out / "barks-manifest.json"
    # UTF-8 ON THE WAY OUT TOO. Same default, same platform split: the
    # manifest carries the bark text, so writing it in cp1252 would put the
    # mojibake back into the file the game reads even after the render is
    # right. `ensure_ascii=False` keeps the em-dash an em-dash rather than
    # an escape, so the file stays readable by a person.
    manifest.write_text(json.dumps(
        {"renders": [{k: v for k, v in j.items() if k != "ref"} for j in jobs]},
        indent=1, ensure_ascii=False), encoding="utf-8")
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
    ap.add_argument("--dry-run", action="store_true",
                    help="walk the whole batch with no model, to exercise the code path")
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
