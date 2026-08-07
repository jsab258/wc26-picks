#!/usr/bin/env python3
"""COMPUTE EACH CAST MEMBER'S VOICE ONCE, SO THE GAME NEVER HAS TO.

    python3 tools/voice-live/precompute-voices.py            # every cast clip
    python3 tools/voice-live/precompute-voices.py --voice rocco
    python3 tools/voice-live/precompute-voices.py --selftest

WHY THIS EXISTS, and it removes a third of the shipping problem.

`ChatterboxTTS.prepare_conditionals(wav_fpath)` reads a reference clip and
produces the conditioning that `generate()` then reuses for EVERY line. Read
in `tts.py` rather than assumed: nothing in it depends on the text. It runs
the voice encoder, the audio tokeniser and `embed_ref` — and all three were
reported as conversion problems:

    ve refused by DirectML            "The parameter is incorrect"
    ve frozen at one clip length      the graph would not take a variable one
    s3tokenizer's STFT                would not export at all
    speaker_encoder's fft_rfft        no ONNX operator

None of that matters if they never run on a player's machine. A cast member's
reference clip is a file we ship; their conditioning is therefore a CONSTANT,
computable once, here, on any machine with the weights, and shipped as data
beside the recordings. The four failures above stop being blockers and become
build-time details.

WHAT COMES OUT. One `.npz` per voice under `game-design/voice-conds/`,
holding the tensors `t3` and `s3gen` need, plus a manifest naming which clip
each came from and how large it is. Small — a speaker embedding is 256
floats, and the prompt tokens are 150.

WHAT THIS DOES NOT DECIDE. The `exaggeration` knob multiplies into
`emotion_adv` and `generate()` rebuilds that per call, so it is NOT baked in
here; the game can still set it per line. Saved at the model's own default so
a caller that never touches it gets the model's behaviour.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CLIPS = ROOT / "game-design" / "picked-clips"
OUT = ROOT / "game-design" / "voice-conds"


def clips():
    """Every cast clip, as (voice id, path). One per voice."""
    if not CLIPS.exists():
        return []
    seen, out = set(), []
    for p in sorted(CLIPS.iterdir()):
        if not p.is_file() or p.suffix.lower() not in (".wav", ".mp3", ".flac"):
            continue
        vid = p.name.split(".")[0]
        if vid in seen:
            continue
        seen.add(vid)
        out.append((vid, p))
    return out


def flatten(obj, prefix=""):
    """Every tensor in a nested structure, as {name: array}.

    WALKED RATHER THAN LISTED. `Conditionals` holds a `T3Cond` dataclass and a
    plain dict, and both have changed shape between chatterbox releases. A
    hand-written list of field names is a second model of somebody else's
    structure and goes stale silently — the same fault as a comment. Whatever
    tensors are in there get saved, under the path they were found at, so the
    loader can put them back where they came from.
    """
    import torch

    out = {}
    if obj is None:
        return out
    if isinstance(obj, torch.Tensor):
        out[prefix or "value"] = obj.detach().cpu().numpy()
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
        return out
    if isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}[{i}]"))
        return out
    fields = getattr(obj, "__dict__", None)
    if fields:
        for k, v in fields.items():
            if k.startswith("_"):
                continue
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    return out


def cmd_run(only):
    import json
    import time
    import numpy as np
    import torch
    from chatterbox.tts import ChatterboxTTS

    import export_probe
    note = export_probe.diagnose_watermarker()
    if note:
        print(f"  watermarker: {note} (stubbed — it is not used here at all)")

    # THE VOCABULARY COMES WITH IT, because the bat says it does and a bat
    # that promises something the script does not do is the same fault as a
    # stale comment. Both are things that can only be fetched from a machine
    # with the weights, so one trip should bring both.
    tok = export_probe.copy_tokenizer()
    if tok.get("copied"):
        print(f"  vocabulary: {tok.get('type')}, {tok.get('vocab')} tokens, "
              f"{tok.get('merges')} merges -> tools/voice-live/tokenizer.json")
    else:
        print(f"  vocabulary: NOT copied — {tok.get('why')}")

    todo = [(v, p) for v, p in clips() if only is None or v == only]
    if not todo:
        print(f"  nothing to do: no clip for '{only}' under {CLIPS}"
              if only else f"  no clips under {CLIPS}")
        return 1

    print(f"  {len(todo)} voice(s) to compute, once each.")
    print("  loading the model...")
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=dev)
    OUT.mkdir(parents=True, exist_ok=True)

    manifest = {}
    for vid, path in todo:
        t0 = time.time()
        model.prepare_conditionals(str(path))
        tensors = {}
        tensors.update(flatten(model.conds.t3, "t3"))
        tensors.update(flatten(model.conds.gen, "gen"))
        if not tensors:
            # A ZERO NEEDS A DENOMINATOR. An empty file would load fine and
            # produce a voiceless character, and nothing would say why.
            print(f"  {vid:10} FAILED — the conditioning held no tensors at all")
            return 1
        dest = OUT / f"{vid}.npz"
        np.savez_compressed(str(dest), **tensors)
        kb = dest.stat().st_size / 1024
        manifest[vid] = {
            "clip": path.name,
            "tensors": {k: list(v.shape) for k, v in sorted(tensors.items())},
            "kilobytes": round(kb, 1),
        }
        print(f"  {vid:10} {len(tensors)} tensors, {kb:6.1f} KB, "
              f"{time.time() - t0:4.1f}s  <- {path.name}")

    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    total = sum(m["kilobytes"] for m in manifest.values())
    print(f"\n  {len(manifest)} voice(s), {total / 1024:.1f} MB total, "
          f"in {OUT.relative_to(ROOT)}")
    print("  This is what ships instead of the voice encoder. The game reads")
    print("  these and never runs that stage at all.")
    return 0


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + ("" if ok else f" — {got}"))
        ran.append(what)
        if not ok:
            fails.append(what)

    found = clips()
    check(len(found) > 1 or not CLIPS.exists(),
          f"one clip per cast member is found: {len(found)}")
    check(len({v for v, _ in found}) == len(found),
          "and exactly one per voice — a second clip for the same person would "
          "make the output depend on which sorted first")

    try:
        import torch
    except ImportError:
        check(True, "flatten not checked: torch is not installed — 0 of 4")
        print(f"\nprecompute-voices --selftest: "
              f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks")
        return 1 if fails else 0

    # THE WALKER, ON THE SHAPES IT WILL ACTUALLY MEET. `Conditionals` is a
    # dataclass holding a dataclass and a dict, so all three nestings are
    # exercised rather than the flat case alone.
    class Cond:
        def __init__(self):
            self.speaker_emb = torch.zeros(1, 256)
            self.emotion_adv = torch.zeros(1, 1, 1)
            self.name = "not a tensor"
            self._private = torch.zeros(9)

    got = flatten({"t3": Cond(), "gen": {"prompt": torch.zeros(1, 150),
                                         "pair": [torch.zeros(2), torch.zeros(3)]}})
    check(sorted(got) == ["gen.pair[0]", "gen.pair[1]", "gen.prompt",
                          "t3.emotion_adv", "t3.speaker_emb"],
          "every tensor is found through dataclasses, dicts and lists",
          str(sorted(got)))
    check("t3.name" not in got, "and a non-tensor field is left out")
    check("t3._private" not in got,
          "as is a private one — saving it would ship somebody's internals")
    check(flatten(None) == {} and flatten("text") == {},
          "nothing in, nothing out, without throwing")

    print(f"\nprecompute-voices --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default=None)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--fromtemp", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    try:
        return cmd_run(a.voice)
    except ImportError as e:
        print(f"  cannot run: {e}")
        print("  This needs chatterbox and its weights — run it from the same")
        print("  environment the export bat built.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
