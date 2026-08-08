#!/usr/bin/env python3
"""MAKE A CHARACTER SAY SOMETHING, WITH MY LOOP INSTEAD OF THE MODEL'S.

    python3 tools/voice-live/speak.py --text "the docks, midnight"
    python3 tools/voice-live/speak.py --selftest

WHAT THIS IS FOR, and it is the first thing in this whole effort that can be
LISTENED to.

Everything so far has been measured: the transformer agrees to 6.5e-07, the
vocoder to 3.5e-06, the sampler matches HuggingFace's processors to 1e-05.
None of that answers the question the game actually asks — does the loop I
rebuilt produce speech a person would accept? A pipeline can be correct at
every join and still sound wrong, and no number in the report would say so.

So this drives chatterbox with `Core/SpeechLoop`'s logic instead of its own,
and writes two files:

    speak-out/model.wav   chatterbox's `generate()`, untouched — the CONTROL
    speak-out/ours.wav    the same voice and words, my loop and my sampler

BOTH, ALWAYS, AND THAT IS THE WHOLE DESIGN. A single file cannot be judged:
this model is not great at every line, and a mediocre take would read as my
loop being broken while a good one would prove nothing about it. Two files
from the same voice and the same sentence turn "does it sound right" into
"do these sound like the same person doing the same job", which an ear can
answer in five seconds and no metric can answer at all.

WHY PYTHON AND NOT C#. This is the reference the C# has to match, not a
replacement for it. `SpeechLoop.Pick` is reimplemented here line for line —
same order of operations, same constants — so if this sounds right and the
game does not, the fault is in the port and not in the design. Writing it
twice is the point.

WHAT IT DOES NOT DO. It does not use the exported ONNX graphs; it drives the
pytorch model. That is deliberate for a first listen — it isolates ONE
variable, the loop, and the graphs are already checked numerically against
pytorch to six decimal places. Swapping the transformer for the ONNX session
is the next step and it changes nothing here.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CLIPS = ROOT / "game-design" / "picked-clips"
OUT = ROOT / "tools" / "voice-live" / "speak-out"

# `tts.py generate(...)` defaults, read from the installed package rather than
# recalled. The same numbers `Core/SpeechPlan` carries, and the reason they are
# repeated here rather than imported is that this file is the SECOND
# implementation on purpose — a shared constant would hide a divergence.
TEMPERATURE = 0.8
REPETITION_PENALTY = 1.2
MIN_P = 0.05
TOP_P = 1.0
CFG_WEIGHT = 0.5
MAX_STEPS = 1000
STOP_SPEECH_TOKEN = 6562
FIRST_NON_ACOUSTIC = 6561


def pick(logits, seen, rng):
    """`Core/SpeechLoop.Pick`, in Python. Same order, same constants.

    Kept deliberately close to the C# — including the sorted-order layout —
    so the two can be read side by side. The draw differs because the random
    generators differ, which is stated in `SpeechLoop`'s header and is why a
    live line can never byte-match a baked one.
    """
    import math

    v = list(logits)
    for i in seen:
        # HuggingFace's RepetitionPenaltyLogitsProcessor: divide a positive
        # logit, MULTIPLY a negative one. Dividing throughout would make an
        # unlikely token more likely.
        v[i] = v[i] / REPETITION_PENALTY if v[i] > 0 else v[i] * REPETITION_PENALTY
    v = [x / TEMPERATURE for x in v]

    order = sorted(range(len(v)), key=lambda i: -v[i])
    top = v[order[0]]
    probs = [math.exp(v[i] - top) for i in order]

    keep = len(order)
    if 0 < MIN_P <= 1.0:
        floor = MIN_P * probs[0]
        keep = 0
        while keep < len(probs) and probs[keep] >= floor:
            keep += 1
    kept = sum(probs[:keep])
    if 0 < TOP_P < 1.0:
        acc, n = 0.0, 0
        while n < keep:
            acc += probs[n]
            n += 1
            if acc >= TOP_P * kept:
                break
        keep, kept = n, acc
    keep = max(keep, 1)

    draw = rng.random() * kept
    walk = 0.0
    for i in range(keep):
        walk += probs[i]
        if draw <= walk:
            return order[i]
    return order[keep - 1]


def generate_ours(model, text, seed):
    """chatterbox's transformer, driven by my loop.

    Mirrors `t3.inference`'s setup exactly — the same conditioning, the same
    start token, the same classifier-free guidance — and replaces only the
    sampling and the stopping.
    """
    import random
    import torch
    import torch.nn.functional as F
    from chatterbox.tts import punc_norm

    t3 = model.t3
    hp = t3.hp
    device = model.device

    # THE WHOLE FUNCTION RUNS IN INFERENCE MODE, NOT JUST THE LOOP.
    #
    # `generate()` — which runs first, as the control — does its work under
    # `torch.inference_mode()`, and tensors produced there are marked: they
    # cannot be used by anything that might record gradients. The first
    # version wrapped only the sampling loop, so `prepare_input_embeds` ran
    # outside and touched the conditioning `generate()` had left behind:
    #
    #     RuntimeError: Inference tensors cannot be saved for backward.
    #
    # It is not a real autograd need — nothing here trains — it is the setup
    # step being in ordinary mode. The read is worth keeping: the error names
    # backward passes and there is no backward pass anywhere in this file.
    with torch.inference_mode():
        return _generate_ours(model, t3, hp, device, text, seed, punc_norm, F)


def _generate_ours(model, t3, hp, device, text, seed, punc_norm, F):
    import random
    import torch

    text = punc_norm(text)
    tt = model.tokenizer.text_to_tokens(text).to(device)
    if CFG_WEIGHT > 0.0:
        tt = torch.cat([tt, tt], dim=0)
    tt = F.pad(tt, (1, 0), value=hp.start_text_token)
    tt = F.pad(tt, (0, 1), value=hp.stop_text_token)

    embeds, _len_cond = t3.prepare_input_embeds(
        t3_cond=model.conds.t3, text_tokens=tt,
        speech_tokens=hp.start_speech_token * torch.ones_like(tt[:, :1]),
        cfg_weight=CFG_WEIGHT)

    from chatterbox.models.t3.inference.t3_hf_backend import T3HuggingfaceBackend
    patched = T3HuggingfaceBackend(
        config=t3.cfg, llama=t3.tfmr, speech_enc=t3.speech_emb,
        speech_head=t3.speech_head, alignment_stream_analyzer=None)

    bos = torch.tensor([[hp.start_speech_token]], dtype=torch.long, device=device)
    bos_embed = t3.speech_emb(bos) + t3.speech_pos_emb.get_fixed_embedding(0)
    inputs_embeds = torch.cat([embeds, torch.cat([bos_embed, bos_embed])], dim=1)

    rng = random.Random(seed)
    seen, tokens = set(), []
    past = None
    stop = "step ceiling"
    # Already inside inference mode from the caller; nested is a no-op and is
    # left because it documents where the expensive part is.
    with torch.inference_mode():
        for step in range(MAX_STEPS):
            out = patched(inputs_embeds=inputs_embeds, past_key_values=past,
                          use_cache=True, return_dict=True)
            past = out.past_key_values
            row = out.logits[:, -1, :]
            # Classifier-free guidance: steer away from the unconditional row.
            logits = row[0] + CFG_WEIGHT * (row[0] - row[1])

            tok = pick(logits.float().cpu().tolist(), seen, rng)
            if tok == STOP_SPEECH_TOKEN:
                stop = "finished"
                break
            # Fed back even when it is not kept — the model's history has to
            # contain every token it sampled, only the AUDIO drops the
            # non-acoustic ones.
            if tok < FIRST_NON_ACOUSTIC:
                tokens.append(tok)
            seen.add(tok)

            nxt = torch.tensor([[tok]], dtype=torch.long, device=device)
            emb = t3.speech_emb(nxt) + t3.speech_pos_emb.get_fixed_embedding(step + 1)
            inputs_embeds = torch.cat([emb, emb])

    return tokens, stop, step + 1


def to_wav(model, tokens):
    import torch
    with torch.inference_mode():
        wav, _ = model.s3gen.inference(
            speech_tokens=torch.tensor(tokens, device=model.device),
            ref_dict=model.conds.gen)
    return wav.squeeze(0).detach().cpu().numpy()


def reference(voice="rocco"):
    """The reference clip for a named cast member.

    DELEGATED TO `export_probe.reference`, WHICH ALREADY DID THIS. I wrote a
    second one here, and it was worse: it looked in a `picked-clips/rocco/`
    subdirectory that does not exist, fell back to the whole folder, and
    returned the alphabetically first file — Ada. It would have produced a
    perfectly good comparison in the wrong person's voice with nothing to
    show for it but one line of output nobody had reason to doubt.

    One idea, two implementations, and the second is the one that is wrong.
    There is now one.
    """
    import export_probe
    return export_probe.reference(voice)


def voices():
    """Every cast member with a clip, for the error message."""
    if not CLIPS.exists():
        return []
    return sorted({p.name.split(".")[0] for p in CLIPS.iterdir()
                   if p.is_file() and p.suffix.lower() in (".wav", ".mp3", ".flac")})


def cmd_speak(text, seed, voice):
    import time
    import torch
    import soundfile as sf
    from chatterbox.tts import ChatterboxTTS
    from chatterbox.models.s3gen.const import S3GEN_SR

    # THE WATERMARKER MUST NOT BE ABLE TO STOP THIS, AND THAT FIX ALREADY
    # EXISTED. `chatterbox.tts.__init__` calls
    # `perth.PerthImplicitWatermarker()` eagerly, the name is None on this
    # install, and the model cannot even load — `TypeError: 'NoneType' object
    # is not callable`. `export_probe` diagnosed and stubbed this weeks ago;
    # `fixture.py`'s own docstring lists "a watermarker that stopped the run"
    # as one of the six harness faults that cost six round trips. I hit it a
    # seventh time by not reusing the fix.
    #
    # Diagnosed BEFORE being worked around, and the diagnosis is printed:
    # working around a failure you have not identified is how a workaround
    # becomes a second bug.
    import export_probe

    # THE VOCABULARY, WHILE WE ARE HERE. `copy_tokenizer` lives in the export
    # probe and only ran from the export bat, so a run of THIS one — which has
    # chatterbox loaded and the file on disk — brought nothing back. It is
    # 25 KB and the last piece of the pipeline that has to TRAVEL rather than
    # be built, so every path that can fetch it should.
    tok = export_probe.copy_tokenizer()
    if tok.get("copied"):
        print(f"  vocabulary: {tok.get('type')}, {tok.get('vocab')} tokens, "
              f"{tok.get('merges')} merges -> tools/voice-live/tokenizer.json")
    else:
        print(f"  vocabulary: NOT copied — {tok.get('why')}")

    note = export_probe.diagnose_watermarker()
    if note:
        print(f"  watermarker: {note}")
        print("  (post-processing on finished audio, not part of generation — "
              "stubbed so the model can load)")

    ref = reference(voice)
    if ref is None:
        print(f"  no clip for '{voice}' under {CLIPS}.")
        print(f"  cast with clips: {' '.join(voices()) or '(none)'}")
        return 1
    print(f"  voice: {voice}  ({ref.name})")
    print("  loading the model (a minute or two the first time)...")
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = export_probe.load_model(dev)
    model.prepare_conditionals(str(ref))
    OUT.mkdir(parents=True, exist_ok=True)

    # THE CONTROL FIRST. If this one is poor, nothing about the other file
    # means anything, and knowing that before listening saves an argument.
    print("\n  1/2  the model's own generate() — the control")
    t0 = time.time()
    with torch.inference_mode():
        wav = model.generate(text).squeeze(0).cpu().numpy()
    sf.write(str(OUT / "model.wav"), wav, model.sr)
    print(f"       {len(wav) / model.sr:.1f}s of audio in {time.time() - t0:.1f}s"
          f"  ->  speak-out/model.wav")

    print("\n  2/2  the same words through MY loop and MY sampler")
    t1 = time.time()
    # CAUGHT, NOT THROWN, AND THE CONTROL SURVIVES EITHER WAY.
    #
    # Three runs in a row died in this half and each one ended in a wall of
    # traceback under a line saying "It ran but produced nothing" — which is
    # true and unhelpful, because `model.wav` had in fact been written and was
    # sitting there usable. A half that fails should say which half, say that
    # the other one landed, and print the cause in one line with the detail
    # underneath rather than instead.
    try:
        tokens, stop, steps = generate_ours(model, text, seed)
    except Exception as e:
        import traceback
        print(f"       MY HALF FAILED: {type(e).__name__}: {e}")
        print(f"       The control DID land — speak-out/model.wav is {len(wav) / model.sr:.1f}s")
        print("       of real audio and worth listening to on its own. Send me")
        print("       the lines below and this is one more thing ruled out.")
        print("       " + "-" * 60)
        traceback.print_exc()
        return 1
    took = time.time() - t1
    print(f"       {steps} steps, stopped: {stop}, {len(tokens)} acoustic tokens")
    if not tokens:
        print("       nothing to decode — no audio written for this half.")
        return 1
    ours = to_wav(model, tokens)
    sf.write(str(OUT / "ours.wav"), ours, S3GEN_SR)
    print(f"       {len(ours) / S3GEN_SR:.1f}s of audio in {took:.1f}s"
          f"  ->  speak-out/ours.wav")

    print("\n  ------------------------------------------------------------")
    print("  LISTEN TO BOTH. The question is not whether it is a good take —")
    print("  this model has bad days on any given line. It is whether the two")
    print("  sound like the SAME PERSON doing the SAME JOB. If they do, the")
    print("  loop the game will run is right and the rest is plumbing.")
    print("  ------------------------------------------------------------")
    return 0


def selftest():
    """The sampler, without the model. Everything else here needs weights."""
    fails, ran = [], []

    def check(ok, what, got=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + ("" if ok else f" — {got}"))
        ran.append(what)
        if not ok:
            fails.append(what)

    import random

    # THE SAME CASES `sampler-reference.py` CHECKS THE C# AGAINST. This file is
    # the second implementation on purpose, so it gets held to the same
    # reference rather than to itself.
    # ONE GENERATOR, ADVANCED. The first version built a fresh `Random(1)`
    # inside the comprehension, so it drew the identical token two hundred
    # times and reported one reachable token out of eight. The sampler was
    # fine; the test was reseeding it every call.
    rng = random.Random(1)
    flat = [1.0] * 8
    drawn = {pick(flat, set(), rng) for _ in range(200)}
    check(len(drawn) == 8, "on a flat distribution every token is reachable",
          str(len(drawn)))

    peaked = [0.0] * 8
    peaked[3] = 20.0
    only = {pick(peaked, set(), rng) for _ in range(200)}
    check(only == {3}, "and on a confident one min-p cuts the tail away",
          str(sorted(only)))

    close = [0, 0, 2.0, 1.9, 0, 0, 0, 0]
    check(pick(close, set(), random.Random(3)) == 2,
          "the likeliest token wins when nothing has been said")
    check(pick(close, {2}, random.Random(3)) == 3,
          "and loses once it has — the penalty reorders")
    neg = [-2.0, -2.1] + [-40.0] * 6
    check(pick(neg, {0}, random.Random(3)) == 1,
          "penalising a NEGATIVE logit pushes it down, not up")

    # THE VOICE IS THE ONE ASKED FOR, which is the check the first version
    # could not have passed: it looked in a `rocco/` folder that does not
    # exist, fell back to the whole directory and returned Ada.
    r = reference("rocco")
    check(r is None or r.name.split(".")[0] == "rocco",
          "asking for rocco gets rocco, not whoever sorts first",
          str(r))
    check(reference("nobody-by-that-name") is None,
          "and an uncast name gets nothing rather than a substitute")
    check(len(voices()) > 1 or not CLIPS.exists(),
          f"the cast with clips is listed for the error message: {len(voices())}")

    # THE WATERMARKER STUB, ON THE CASE IT MUST LET THROUGH.
    #
    # This is what stopped the first real run: `chatterbox.tts.__init__` calls
    # `perth.PerthImplicitWatermarker()` eagerly and the name is None, so the
    # model cannot load at all. The stub existed in `export_probe` and I did
    # not reuse it. Checked here rather than trusted, and checked in the
    # direction that matters — that after the fix the thing chatterbox calls
    # is callable and returns the audio unchanged.
    import export_probe
    note = export_probe.diagnose_watermarker()
    try:
        import perth
        maker = perth.PerthImplicitWatermarker
        check(maker is not None and callable(maker),
              "after diagnosis the watermarker is callable — which is the whole "
              f"reason the model can load ({note or 'the real one works'})")
        same = [0.1, -0.2, 0.3]
        check(maker().apply_watermark(same, sample_rate=24000) is same,
              "and it hands the audio straight back, so nothing is altered by "
              "a stub standing in for post-processing")
    except ImportError:
        check(True, "perth is not installed here — nothing to stub, and the "
                    "diagnosis says so rather than pretending")

    print(f"\nspeak --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks (the sampler only; the rest needs the weights)")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="I was on the docks when it happened. "
                                      "Ask anyone who was there.")
    ap.add_argument("--seed", type=int, default=20260807)
    ap.add_argument("--voice", default="rocco",
                    help="cast id — the clip is game-design/picked-clips/<id>.*")
    ap.add_argument("--selftest", action="store_true")
    # `--fromtemp` IS THE BAT'S, NOT A USER'S, AND IT HAS TO BE ACCEPTED HERE.
    #
    # `3 HEAR IT SPEAK.bat` copies itself to %TEMP% and relaunches with
    # `--fromtemp` — it has to, because a `git pull` rewriting a script cmd.exe
    # is reading by byte offset is how a bat once printed the tail of a URL
    # from its own replacement. The relaunched copy then forwards `%*` so a
    # user's `--text` reaches this file, and `%*` in cmd is ALWAYS the original
    # argument list: `shift` does not change it. So the marker comes along.
    #
    # THE FIX IS HERE AND NOT IN THE BAT, deliberately. The bat copies itself
    # BEFORE it pulls, so a change to it takes effect one run later — the trap
    # already written down in `export_probe.py`, which cost three runs there.
    # Python is read after the pull, so this lands on the very next run. The
    # bat is fixed too, and that fix is the belt to this file's braces.
    ap.add_argument("--fromtemp", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    try:
        return cmd_speak(a.text, a.seed, a.voice)
    except ImportError as e:
        print(f"  cannot speak: {e}")
        print("  This needs chatterbox and soundfile installed — the bat does it.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
