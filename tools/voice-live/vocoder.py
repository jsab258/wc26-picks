#!/usr/bin/env python3
"""THE VOCODER, CONVERTED AND CHECKED AGAINST THE REAL MODEL.

    python3 tools/voice-live/vocoder.py --selftest

WHAT THIS ANSWERS. `s3gen`'s flow decoder converts and produces a mel
spectrogram — a picture of the sound. `hifigan` is the step that turns that
into a waveform, and it is the last piece of the pipeline that would not
convert: `torch.stft`, `torch.istft`, `torch.complex` and `torch.view_as_real`
all appear in it, and ONNX has no complex type.

`stft_patch` replaces those four. This checks the replacement against the
thing it replaces, on the ACTUAL `HiFTGenerator` rather than on a stand-in.

NO DOWNLOAD, WHICH IS THE POINT. The class is in the installed package and its
constructor takes plain defaults, so a randomly-initialised one has the exact
architecture, the exact shapes and the exact awkward operations — everything
that decides whether it converts. Only the trained weights are missing, and
weights are the one thing conversion does not care about. Same trick as
building a real `LlamaModel` to catch the cache assembly bug: minutes here
instead of a ~28-minute round trip on Jafar's machine.

THE ONE THING THAT HAD TO CHANGE FOR THIS TO BE CHECKABLE AT ALL.

`HiFTGenerator.inference` is not deterministic. Its source module is the "NSF"
of a neural source-filter vocoder and it adds Gaussian noise by design — run it
twice on the same mel and the waveforms are 0.448 apart, which is the same
magnitude as a completely broken conversion. The first comparison here read
0.46 and looked like a serious correctness failure; the original disagreeing
with itself by 0.448 is what that number actually was.

So the source signal is computed OUTSIDE the graph and handed in. That makes
the graph deterministic and comparable — and it is also the right shipping
shape, because the game then owns the noise and can seed it per line, which is
`VoiceBank`'s determinism rule reaching the last stage of the pipeline.
"""
import argparse
import sys


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + ("" if ok else f" — {got}"))
        ran.append(what)
        if not ok:
            fails.append(what)

    try:
        import numpy as np
        import torch
        import onnxruntime as ort
        from chatterbox.models.s3gen.hifigan import HiFTGenerator
        from chatterbox.models.s3gen.f0_predictor import ConvRNNF0Predictor
        from chatterbox.models.s3gen.const import S3GEN_SR
    except ImportError as e:
        # A DENOMINATOR ON THE SKIP. "chatterbox is not installed" and "the
        # vocoder converts" must not print the same way.
        print(f"  skipped: {e} — 0 of 6 checks run, the vocoder was not built")
        print("\nvocoder --selftest: SKIPPED — 0 checks")
        return 0

    import pathlib
    import tempfile
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from stft_patch import patched

    tmp = pathlib.Path(tempfile.mkdtemp())
    # CLEANED ON EXIT, HOWEVER THE RUN ENDS — the sibling without this
    # pair leaked 17GB of 68MB temp dirs in a day (verify runs these
    # selftests on every commit) and red-walled the disk mid-verify.
    # Same two lines export-decode.py has carried since its own leak.
    import atexit as _ax, shutil as _sh
    _ax.register(_sh.rmtree, tmp, True)
    torch.manual_seed(20260807)
    # THE SHIPPED CONFIGURATION, NOT THE CLASS DEFAULTS. `S3Token2Wav` builds
    # this vocoder with explicit arguments and every one of them differs from
    # the default: the upsample rates are [8,5,3] against [8,8], which changes
    # the sample rate the source signal runs at and the length of everything
    # downstream. Built from defaults this file proved a NEIGHBOURING vocoder
    # converts. Caught by measuring the noise shapes for the decode export and
    # finding 256 samples per mel frame where the shipped one has 480.
    gen = HiFTGenerator(
        sampling_rate=S3GEN_SR,
        upsample_rates=[8, 5, 3],
        upsample_kernel_sizes=[16, 11, 7],
        source_resblock_kernel_sizes=[7, 7, 11],
        source_resblock_dilation_sizes=[[1, 3, 5], [1, 3, 5], [1, 3, 5]],
        f0_predictor=ConvRNNF0Predictor(),
    ).eval()
    for p in gen.parameters():
        p.requires_grad_(False)

    def source(feat):
        """The random half, kept outside the graph."""
        f0 = gen.f0_predictor(feat)
        s = gen.f0_upsamp(f0[:, None]).transpose(1, 2)
        s, _, _ = gen.m_source(s)
        return s.transpose(1, 2)

    class Decode(torch.nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, feat, src):
            return self.inner.decode(x=feat, s=src)

    dec = Decode(gen).eval()
    mel = torch.randn(1, 80, 40)

    # 1. THE NOISE IS REAL, AND NAMING IT IS WHY THE REST MEANS ANYTHING.
    with torch.no_grad():
        f0 = gen.f0_predictor(mel)
        s1 = gen.f0_upsamp(f0[:, None]).transpose(1, 2)
        a1, _, _ = gen.m_source(s1)
        b1, _, _ = gen.m_source(s1)
    spread = float((a1 - b1).abs().max()) / max(float(a1.abs().max()), 1e-12)
    check(spread > 1e-3,
          f"the vocoder's source module is random by design — {spread:.2f} apart "
          f"on the same input, which is what a 'failed' conversion looked like",
          f"{spread:.2e}")

    with torch.no_grad():
        src = source(mel)
        want = dec(mel, src).numpy()
        again = dec(mel, src).numpy()
    check(float(np.abs(want - again).max()) == 0.0,
          "and with the source handed in, the original repeats exactly — so a "
          "disagreement from here is the conversion and nothing else")

    # 2. UNPATCHED IT REFUSES. The rejecting case, run rather than assumed.
    try:
        with torch.no_grad():
            torch.onnx.export(dec, (mel, src), str(tmp / "plain.onnx"),
                              opset_version=17, dynamo=False)
        plain = "exported"
    except Exception as e:
        plain = type(e).__name__
    check(plain != "exported",
          "unpatched, the real vocoder still refuses to convert", plain)

    # 3. PATCHED IT CONVERTS.
    ok, why = True, ""
    try:
        with patched(), torch.no_grad():
            torch.onnx.export(
                dec, (mel, src), str(tmp / "hift.onnx"), opset_version=17,
                dynamo=False, input_names=["mel", "src"],
                dynamic_axes={"mel": {0: "b", 2: "t"}, "src": {0: "b", 2: "s"}})
    except Exception as e:
        ok, why = False, f"{type(e).__name__}: {e}"
    check(ok, "patched, the REAL vocoder converts", why[:130])
    if not ok:
        print(f"\nvocoder --selftest: {len(fails)} FAILED — {len(ran)} checks")
        return 1

    sess = ort.InferenceSession(str(tmp / "hift.onnx"),
                                providers=["CPUExecutionProvider"])
    got = sess.run(None, {"mel": mel.numpy(), "src": src.numpy()})[0]
    rel = float(np.abs(want - got).max()) / max(float(np.abs(want).max()), 1e-12)
    check(rel < 1e-4,
          f"and the waveform agrees with pytorch's to {rel:.1e}", f"{rel:.2e}")

    # 4. AT LENGTHS IT WAS NOT CONVERTED AT, or it can only ever say one
    # sentence. Printed as a series: the shape of the three is the answer, and
    # a single length cannot show a frozen axis.
    series = {}
    for n in (25, 61, 90):
        m2 = torch.randn(1, 80, n)
        with torch.no_grad():
            s2 = source(m2)
            w2 = dec(m2, s2).numpy()
        g2 = sess.run(None, {"mel": m2.numpy(), "src": s2.numpy()})[0]
        series[n] = (float(np.abs(w2 - g2).max())
                     / max(float(np.abs(w2).max()), 1e-12), g2.shape[-1])
    print("        series: traced(40)=%.1e  " % rel
          + "  ".join(f"{n}={v:.1e}({smp}smp)" for n, (v, smp) in series.items()))
    worst = max(v for v, _ in series.values())
    check(worst < 1e-4,
          f"and at three lengths it was NOT converted at, worst {worst:.1e}",
          f"{worst:.2e}")

    print(f"\nvocoder --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks against the real HiFTGenerator")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
