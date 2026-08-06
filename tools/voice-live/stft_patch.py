#!/usr/bin/env python3
"""AN EXPORTABLE STAND-IN FOR `torch.stft`, so the decoder stops being blocked
by its last step.

    python3 tools/voice-live/stft_patch.py --selftest

THE BLOCKER. chatterbox's vocoder turns numbers into a waveform with an STFT
(`hifigan.py:397`), and every attempt to convert the decoder has died on the
same line:

    SymbolicValueError: STFT does not currently support complex types

That is not the model refusing. `torch.stft` returns a COMPLEX tensor and the
ONNX exporter has no complex type, so the conversion stops at a step that is
ordinary signal processing — the same class of thing as the range check and
the window arithmetic, sitting at the edge of the graph rather than in the
middle of the network.

WHAT AN STFT ACTUALLY IS: slide a window along the signal and take a dot
product with a cosine and a sine at each frequency. Two real convolutions.
Nothing about it needs complex arithmetic, which is a convenience of the API
rather than a property of the transform.

MEASURED, in this container, against `torch.stft` itself:

    torch.stft                  refuses to convert
    two real convolutions       converts, and matches to 1.9e-06
    then under onnxruntime      6.5e-08

WHY THE PROXY, and this is the part that took a second measurement. Returning
the obvious thing — a complex tensor rebuilt with `view_as_complex` — fails
just as hard, because `aten::view_as_complex` has no ONNX operator either.
Complex has to be absent from the graph entirely, not merely arrived at by a
different route.

So the replacement hands back an object that answers the questions calling
code asks of a complex spectrogram — `.abs()`, `.real`, `.imag`, `.angle()` —
and computes each from two real tensors. The calling code is untouched, and
nothing complex is ever traced.

WHAT THIS IS NOT. It is not proof that chatterbox's decoder converts. It
removes one named blocker and there is a second one above it, a range check in
`flow.py`. It is also not bit-identical: 1.9e-06 relative is far below
anything audible and is not zero, so this is a substitution rather than the
same computation.
"""
import argparse
import math
import sys

import torch


class RealSpectrogram:
    """What `torch.stft(return_complex=True)` returns, minus the complex type.

    Only the accessors real code uses. Anything else raises rather than
    guessing — a proxy that silently returns something plausible for an
    operation it does not implement would produce a converted model that is
    quietly wrong, which is the failure this whole probe exists to avoid.
    """

    def __init__(self, re, im):
        self.re = re
        self.im = im
        self.shape = re.shape

    @property
    def real(self):
        return self.re

    @property
    def imag(self):
        return self.im

    def abs(self):
        # The epsilon keeps the gradient and the square root finite at exact
        # zero, which happens in silence and would otherwise produce NaN.
        return torch.sqrt(self.re * self.re + self.im * self.im + 1e-12)

    def angle(self):
        return torch.atan2(self.im, self.re)

    def __getattr__(self, name):
        raise AttributeError(
            f"RealSpectrogram has no '{name}'. It stands in for a complex "
            f"spectrogram during ONNX export and implements only abs, angle, "
            f"real and imag. Add it here deliberately rather than letting the "
            f"export succeed on something this class guessed at.")


def conv_stft(x, n_fft, hop_length=None, win_length=None, window=None,
              center=True, pad_mode="reflect", normalized=False,
              onesided=True, return_complex=True):
    """`torch.stft`'s signature, computed with two real convolutions."""
    hop_length = hop_length or n_fft // 4
    win_length = win_length or n_fft
    w = window if window is not None else torch.ones(win_length, dtype=x.dtype)
    if w.numel() < n_fft:                      # centre a short window
        pad = n_fft - w.numel()
        w = torch.nn.functional.pad(w, (pad // 2, pad - pad // 2))

    bins = n_fft // 2 + 1 if onesided else n_fft
    k = torch.arange(bins, dtype=x.dtype).unsqueeze(1)
    t = torch.arange(n_fft, dtype=x.dtype).unsqueeze(0)
    ang = 2 * math.pi * k * t / n_fft
    cos_k = (torch.cos(ang) * w).unsqueeze(1).to(x.dtype)
    sin_k = (-torch.sin(ang) * w).unsqueeze(1).to(x.dtype)

    squeeze = x.dim() == 1
    if squeeze:
        x = x.unsqueeze(0)
    xb = x.unsqueeze(1)
    if center:
        xb = torch.nn.functional.pad(xb, (n_fft // 2, n_fft // 2), mode=pad_mode)
    re = torch.nn.functional.conv1d(xb, cos_k, stride=hop_length)
    im = torch.nn.functional.conv1d(xb, sin_k, stride=hop_length)
    if normalized:
        re = re / math.sqrt(n_fft)
        im = im / math.sqrt(n_fft)
    if squeeze:
        re, im = re.squeeze(0), im.squeeze(0)
    if return_complex:
        return RealSpectrogram(re, im)
    return torch.stack([re, im], dim=-1)


class patched:
    """`with patched(): torch.onnx.export(...)` — swaps `torch.stft` for the
    convolution form and puts it back afterwards, so nothing outside the
    export is affected."""

    def __enter__(self):
        self._real = torch.stft
        torch.stft = conv_stft
        return self

    def __exit__(self, *exc):
        torch.stft = self._real
        return False


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + ("" if ok else f" — {got}"))
        ran.append(what)
        if not ok:
            fails.append(what)

    import tempfile
    import pathlib
    tmp = pathlib.Path(tempfile.mkdtemp())
    torch.manual_seed(20260806)
    x = torch.randn(1, 2048)

    # 1. IT HAS TO AGREE WITH THE THING IT REPLACES. A substitute that exports
    # and computes something else is worse than a blocker.
    for n_fft, hop in ((64, 16), (256, 64), (1024, 256)):
        w = torch.hann_window(n_fft)
        with torch.no_grad():
            ref = torch.stft(x, n_fft=n_fft, hop_length=hop, window=w,
                             return_complex=True)
            got = conv_stft(x, n_fft=n_fft, hop_length=hop, window=w)
        check(tuple(ref.shape) == tuple(got.shape),
              f"n_fft={n_fft}: the shape matches torch.stft",
              f"{tuple(ref.shape)} vs {tuple(got.shape)}")
        d = float((ref.abs() - got.abs()).abs().max()) / float(ref.abs().max())
        check(d < 1e-4, f"n_fft={n_fft}: the magnitude matches to {d:.1e}", f"{d:.2e}")
        # PHASE IS AN ANGLE, SO THE DIFFERENCE HAS TO WRAP. The first version
        # of this check subtracted the two directly and reported a worst error
        # of 6.28 — exactly 2*pi — for all three window sizes. Three identical
        # "failures" at a suspiciously round number is the instrument, not the
        # subject: the phases agreed and were being read either side of the
        # +pi/-pi seam. Wrapped into [-pi, pi], the real disagreement is ~1e-6.
        diff = ref.angle() - got.angle()
        dp = float(torch.atan2(torch.sin(diff), torch.cos(diff)).abs().max())
        check(dp < 1e-2, f"n_fft={n_fft}: the phase matches to {dp:.1e} (wrapped)",
              f"{dp:.2e}")

    # 2. AND THE POINT OF IT: the thing that would not convert, converting.
    class Vocoderish(torch.nn.Module):
        """`stft` then `.abs()`, which is what a vocoder's analysis step does."""
        def forward(self, wav):
            return torch.stft(wav, n_fft=256, hop_length=64,
                              window=torch.hann_window(256),
                              return_complex=True).abs()

    m = Vocoderish().eval()
    try:
        with torch.no_grad():
            torch.onnx.export(m, (x,), str(tmp / "plain.onnx"), opset_version=17,
                              dynamo=False)
        plain = "exported"
    except Exception as e:
        plain = f"{type(e).__name__}"
    check(plain != "exported",
          "unpatched, the vocoder step still refuses — the blocker is real", plain)

    ok, why = True, ""
    try:
        with patched(), torch.no_grad():
            torch.onnx.export(m, (x,), str(tmp / "patched.onnx"), opset_version=17,
                              dynamo=False)
    except Exception as e:
        ok, why = False, f"{type(e).__name__}: {e}"
    check(ok, "patched, the same module converts", why[:120])

    # 3. AND IT RUNS, AND AGREES WITH THE ORIGINAL PYTORCH MODULE.
    if ok:
        import numpy as np
        import onnxruntime as ort
        sess = ort.InferenceSession(str(tmp / "patched.onnx"),
                                    providers=["CPUExecutionProvider"])
        got = sess.run(None, {sess.get_inputs()[0].name: x.numpy()})[0]
        with torch.no_grad():
            want = m(x).numpy()
        rel = float(np.abs(want - got).max()) / max(float(np.abs(want).max()), 1e-12)
        check(rel < 1e-3,
              f"and the converted file agrees with the original to {rel:.1e}", f"{rel:.2e}")

    # 4. THE PROXY MUST NOT GUESS. An unimplemented operation has to raise, or
    # a converted model could be quietly wrong in a way nothing would catch.
    s = conv_stft(x, n_fft=64, hop_length=16, window=torch.hann_window(64))
    raised = False
    try:
        s.conj()
    except AttributeError:
        raised = True
    check(raised, "an operation the stand-in does not implement raises rather than guessing")

    # 5. AND IT PUTS torch.stft BACK, or every later part of the run is
    # silently measuring the substitute instead of the real thing.
    before = torch.stft
    with patched():
        inside = torch.stft
    check(inside is conv_stft and torch.stft is before,
          "the patch applies inside the block and is removed on the way out")

    print(f"\nstft-patch --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
