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


def conv_istft(real, imag, n_fft, hop_length=None, win_length=None,
               window=None, center=True, length=None):
    """`torch.istft`, computed with two TRANSPOSED convolutions.

    THE OTHER HALF, AND IT IS THE HALF THAT SHIPS. The forward transform above
    was written for the audio TOKENISER, which — established on 7 August by
    reading `tts.py` — runs once per voice, offline, and never needs to be in
    a graph at all. The transform that actually has to convert is this one:
    `hifigan.decode` ends with an inverse STFT, and it is the step that turns
    the decoder's mel spectrogram into a waveform. Without it the converted
    model produces a picture of the sound.

    Takes real and imaginary parts SEPARATELY rather than a complex tensor,
    because that is how the model already holds them — `hifigan._istft` builds
    `real = magnitude*cos(phase)` and `img = magnitude*sin(phase)` and only
    then calls `torch.complex`. Substituting here means complex numbers never
    enter the graph, which is the whole problem: ONNX has no complex type, and
    the previous attempt failed trying to impersonate one
    ("'RealSpectrogram' object is not subscriptable").

    Overlap-add, in three steps and all three are standard ONNX operators:

      1. the inverse DFT as a fixed matrix, folded into the kernel;
      2. `conv_transpose1d` at `hop_length`, which IS overlap-add;
      3. divide by the overlapped window energy, the same normalisation
         `torch.istft` applies, computed the same way.

    chatterbox's vocoder uses `n_fft=16, hop_len=4` — read from
    `hifigan.py`'s `istft_params`, not assumed — so these are small kernels
    and the cost is negligible next to the 112M-parameter decoder in front.
    """
    hop_length = hop_length or n_fft // 4
    win_length = win_length or n_fft
    w = window if window is not None else torch.ones(win_length, dtype=real.dtype)
    if w.numel() < n_fft:
        pad = n_fft - w.numel()
        w = torch.nn.functional.pad(w, (pad // 2, pad - pad // 2))
    w = w.to(real.dtype)

    squeeze = real.dim() == 2
    if squeeze:
        real, imag = real.unsqueeze(0), imag.unsqueeze(0)

    # THE KERNEL GEOMETRY COMES FROM `n_fft`, NEVER FROM THE INPUT'S SHAPE.
    #
    # This read `real.shape[1]`, which is the same number and is a TRACED
    # value, so the convolution weights became input-dependent and the export
    # died with "ONNX export of convolution for kernel of unknown shape". A
    # kernel is part of the graph, not part of the data; anything that decides
    # its size has to be a Python integer at trace time.
    bins = n_fft // 2 + 1
    k = torch.arange(bins, dtype=real.dtype).unsqueeze(1)
    t = torch.arange(n_fft, dtype=real.dtype).unsqueeze(0)
    ang = 2 * math.pi * k * t / n_fft

    # HERMITIAN SYMMETRY, AND THE TWO BINS THAT ARE NOT DOUBLED. A one-sided
    # spectrum omits the negative frequencies; reconstructing means counting
    # each of them twice — EXCEPT DC and, for an even n_fft, Nyquist, which
    # have no partner. Getting that wrong is a small, plausible-sounding error
    # that would survive every shape check.
    #
    # BUILT FROM A PYTHON LIST rather than by writing into a tensor. The
    # in-place version traced two `index_put` operations into the graph for
    # what is a constant.
    half = [2.0] * bins
    half[0] = 1.0
    if n_fft % 2 == 0:
        half[-1] = 1.0
    scale = torch.tensor(half, dtype=real.dtype).unsqueeze(1)

    cos_k = ((torch.cos(ang) * scale / n_fft) * w).unsqueeze(1)
    sin_k = ((-torch.sin(ang) * scale / n_fft) * w).unsqueeze(1)

    frames = torch.nn.functional.conv_transpose1d(real, cos_k, stride=hop_length) \
        + torch.nn.functional.conv_transpose1d(imag, sin_k, stride=hop_length)

    # The window energy at every sample, by overlap-adding w^2 with the same
    # geometry. Ones in, so this depends only on the window and the hop.
    ones = torch.ones(1, 1, real.shape[2], dtype=real.dtype)
    norm = torch.nn.functional.conv_transpose1d(
        ones, (w * w).view(1, 1, n_fft), stride=hop_length)
    frames = frames / torch.clamp(norm, min=1e-11)

    if center:
        frames = frames[..., n_fft // 2: frames.shape[-1] - n_fft // 2]
    if length is not None:
        frames = frames[..., :length]
    out = frames.squeeze(1)
    return out.squeeze(0) if squeeze else out


class patched:
    """`with patched(): torch.onnx.export(...)` — swaps `torch.stft` and
    `torch.istft` for the convolution forms and puts them back afterwards, so
    nothing outside the export is affected.

    `torch.istft` IS SWAPPED TOO, and it was not before. The forward transform
    alone got `s3gen` as far as a mel spectrogram and no further; the report
    read "exported and runs" for the flow and the waveform step was never in
    it.
    """

    def __enter__(self):
        self._stft, self._istft = torch.stft, torch.istft
        self._complex = torch.complex
        self._var = torch.view_as_real
        torch.stft = conv_stft
        torch.istft = _istft_shim
        # AND `view_as_real`, WHICH IS THE THIRD DOOR. `hifigan._stft` does
        # not read `.real`/`.imag` off the spectrogram — it calls
        # `torch.view_as_real(spec)` and then subscripts `[..., 0]` and
        # `[..., 1]`. That is why the earlier attempt died with
        # "'RealSpectrogram' object is not subscriptable": the proxy answered
        # the questions I imagined the model asking rather than the ones it
        # asks. Found by building the real vocoder with random weights and
        # exporting it, which needs no download and took a minute.
        torch.view_as_real = _view_as_real_shim
        # `torch.complex` TOO, OR COMPLEX COMES BACK IN BY THE FRONT DOOR.
        # Swapping `torch.istft` alone left the export failing on
        # `aten::complex`, because `hifigan._istft` builds its complex tensor
        # FIRST and only then calls istft:
        #
        #     real = magnitude * cos(phase); img = magnitude * sin(phase)
        #     torch.istft(torch.complex(real, img), ...)
        #
        # So the complex value exists as a traced operation before the
        # substituted function ever sees it. Pairing the two keeps the type out
        # of the graph entirely, which is the only thing that works — a lesson
        # this file already recorded once, about `view_as_complex`.
        torch.complex = _complex_shim
        return self

    def __exit__(self, *exc):
        torch.stft, torch.istft = self._stft, self._istft
        torch.complex = self._complex
        torch.view_as_real = self._var
        return False


def _view_as_real_shim(spec):
    """`torch.view_as_real`, for the proxy. Real tensors pass through to the
    original, so a model mixing both is not broken by the patch."""
    if isinstance(spec, RealSpectrogram):
        return torch.stack([spec.re, spec.im], dim=-1)
    return _ORIGINAL_VIEW_AS_REAL(spec)


_ORIGINAL_VIEW_AS_REAL = torch.view_as_real


def _complex_shim(real, imag, out=None):
    """`torch.complex`, kept out of the graph. Returns the same proxy the
    forward transform produces, so the two shims compose."""
    return RealSpectrogram(real, imag)


def _istft_shim(spec, n_fft, hop_length=None, win_length=None, window=None,
                center=True, normalized=False, onesided=None, length=None,
                return_complex=False):
    """`torch.istft`'s signature, forwarding to the two-real-tensor form.

    Accepts either a real complex tensor or the `RealSpectrogram` the forward
    shim produces, so a model that round-trips through both is not required to
    know which it is holding.
    """
    if isinstance(spec, RealSpectrogram):
        re, im = spec.re, spec.im
    elif spec.is_complex():
        re, im = spec.real, spec.imag
    else:
        re, im = spec[..., 0], spec[..., 1]
    return conv_istft(re, im, n_fft, hop_length, win_length, window,
                      center=center, length=length)


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
    import atexit as _ax, shutil as _sh   # same leak as export-decode's: 19.8GB of these in one evening
    _ax.register(_sh.rmtree, tmp, True)
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

    # 3b. THE INVERSE, WHICH IS THE HALF THAT SHIPS.
    #
    # The forward transform gets the decoder as far as a mel spectrogram — a
    # picture of the sound. `hifigan.decode` ends with an inverse STFT and that
    # is the step that makes a waveform, so without this the converted model
    # produces something nobody can listen to.
    #
    # CHATTERBOX'S OWN SETTINGS FIRST. `hifigan.py`'s `istft_params` is
    # `{"n_fft": 16, "hop_len": 4}` — read, not assumed — and it is far smaller
    # than the sizes above, so it goes first rather than being represented by a
    # convenient round number.
    for n_fft, hop in ((16, 4), (64, 16), (256, 64)):
        w = torch.hann_window(n_fft)
        with torch.no_grad():
            spec = torch.stft(x, n_fft=n_fft, hop_length=hop, win_length=n_fft,
                              window=w, return_complex=True)
            want = torch.istft(spec, n_fft, hop, n_fft, window=w)
            back = conv_istft(spec.real, spec.imag, n_fft, hop, n_fft, window=w)
        n = min(want.shape[-1], back.shape[-1])
        check(tuple(want.shape) == tuple(back.shape),
              f"istft n_fft={n_fft}: the shape matches torch.istft",
              f"{tuple(want.shape)} vs {tuple(back.shape)}")
        d = float((want[..., :n] - back[..., :n]).abs().max()) / float(want.abs().max())
        check(d < 1e-4, f"istft n_fft={n_fft}: the waveform matches to {d:.1e}",
              f"{d:.2e}")

    # AND THE ROUND TRIP, which is the thing a listener would actually hear.
    # Agreeing with `torch.istft` on ITS OWN forward transform does not prove
    # the two halves here compose — they could share a convention that neither
    # shares with the signal.
    w16 = torch.hann_window(16)
    with torch.no_grad():
        sp = conv_stft(x, n_fft=16, hop_length=4, win_length=16, window=w16)
        rt = conv_istft(sp.re, sp.im, 16, 4, 16, window=w16)
    n = min(x.shape[-1], rt.shape[-1])
    rt_err = float((x[..., :n] - rt[..., :n]).abs().max()) / float(x.abs().max())
    check(rt_err < 1e-4,
          f"and forward-then-inverse returns the original signal to {rt_err:.1e}",
          f"{rt_err:.2e}")

    # 3c. THE INVERSE CONVERTS, WHICH THE ORIGINAL DOES NOT.
    class Vocoderish2(torch.nn.Module):
        """magnitude and phase in, waveform out — `hifigan._istft` exactly."""
        def forward(self, mag, phase):
            real = mag * torch.cos(phase)
            img = mag * torch.sin(phase)
            return torch.istft(torch.complex(real, img), 16, 4, 16,
                               window=torch.hann_window(16))

    m2 = Vocoderish2().eval()
    mag = torch.rand(1, 9, 64) + 0.1
    ph = torch.randn(1, 9, 64)
    try:
        with torch.no_grad():
            torch.onnx.export(m2, (mag, ph), str(tmp / "istft_plain.onnx"),
                              opset_version=17, dynamo=False)
        plain2 = "exported"
    except Exception as e:
        plain2 = f"{type(e).__name__}"
    check(plain2 != "exported",
          "unpatched, the waveform step refuses too — this blocker is real as well",
          plain2)

    ok2, why2 = True, ""
    try:
        with patched(), torch.no_grad():
            torch.onnx.export(m2, (mag, ph), str(tmp / "istft_patched.onnx"),
                              opset_version=17, dynamo=False)
    except Exception as e:
        ok2, why2 = False, f"{type(e).__name__}: {e}"
    check(ok2, "patched, the waveform step converts", why2[:120])

    if ok2:
        import numpy as np
        import onnxruntime as ort
        s2 = ort.InferenceSession(str(tmp / "istft_patched.onnx"),
                                  providers=["CPUExecutionProvider"])
        names = [i.name for i in s2.get_inputs()]
        got2 = s2.run(None, {names[0]: mag.numpy(), names[1]: ph.numpy()})[0]
        with torch.no_grad():
            want2 = m2(mag, ph).numpy()
        r2 = float(np.abs(want2 - got2).max()) / max(float(np.abs(want2).max()), 1e-12)
        check(r2 < 1e-3,
              f"and the converted waveform agrees with pytorch's to {r2:.1e}",
              f"{r2:.2e}")

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
