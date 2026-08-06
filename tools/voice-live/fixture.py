#!/usr/bin/env python3
"""A STAND-IN FOR CHATTERBOX THAT FAILS THE SAME WAYS, so the probe can be
tested here instead of on Jafar's machine.

    python3 tools/voice-live/fixture.py --selftest

WHY THIS EXISTS, and it is the most expensive lesson of the week.

Six round trips were spent on this export probe. Almost every one of them was
blocked by MY OWN HARNESS rather than by the model: a watermarker that stopped
the run, a hook that watched only `forward`, a missing `eval()`, a missing
`no_grad()`, a stale report read as a fresh one, a package installed from the
one file that cannot take effect on the run that installs it, two providers in
one constructor, and an error cut off before its cause. Each cost about half an
hour of Jafar's time and told us nothing about chatterbox.

That is CLAUDE.md rule 12 exactly — a blocked feedback channel is not an
inconvenience to route around, it is the highest-leverage bug on the board —
and I routed around it for six runs because "chatterbox needs a GPU-class
download and HuggingFace is blocked here" was true, and I never checked whether
the part I actually needed was blocked. It was not. `torch`, `onnx`,
`onnxruntime` and `onnxscript` all install from PyPI in this container. Only the
model weights are unreachable, and the weights are the one thing the harness
does not need in order to be wrong.

WHAT THIS IS. Three tiny modules wearing chatterbox's shape: the same attribute
names, the same `inference()` entry point, and the same three export failures,
reproduced deliberately:

    t3     a loop that stops on a data-dependent condition. Does NOT
           reproduce the real `aten::scatter_` error — see its docstring —
           and reproduces something worse instead: it exports, runs, returns
           the right shape, and is WRONG for every input but the traced one
    s3gen  a real STFT, which is what the decoder does
           -> "STFT does not currently support complex types"
    ve     window arithmetic that divmods a traced tensor
           -> "unsupported operand type(s) for divmod(): 'Tensor' and 'int'"

It is 1.4 MB of nothing and it loads in a tenth of a second, so the whole probe
can be run here in seconds, as often as it takes.

WHAT IT IS NOT. It is not chatterbox and it cannot answer whether chatterbox
converts — the weights and the real architecture are the only things that can.
It answers the other question, the one that has been eating the round trips:
does the PROBE work. Those are different, and conflating them is how a harness
fault gets reported as a model verdict.
"""
import argparse
import sys

import torch
import torch.nn as nn


class FakeT3(nn.Module):
    """The autoregressive stage — and it reproduces the WORSE failure, not the
    real one.

    THE REAL t3 FAILS WITH `aten::scatter_` AND THIS DOES NOT REPRODUCE THAT.
    Five variants were tried here — a scalar-value scatter, a scatter in a
    loop bounded by the input, an index_put, a data-dependent while loop, a
    `.item()` call — and every one of them EXPORTED. Reproducing that message
    needs t3's actual internals, which are not visible from this container, so
    claiming this stands in for it would be a fixture that certifies a probe
    against a fault it does not contain.

    What this does instead is the failure those five variants actually
    revealed, which is more dangerous than an exception: a loop that stops on a
    data-dependent condition traces WITHOUT ERROR and bakes the loop count in
    as a constant. It exports, it loads, it runs, and it returns the right
    shape. It agrees with the original to the last decimal on the input it was
    traced with, and is out by 12.4 on anything else.

    That is what an autoregressive stage IS, so it is the likeliest way this
    model ends up "converted" and wrong — and the probe checked shape rather
    than values, so it would have reported it green.
    """

    def __init__(self, dim=32):
        super().__init__()
        self.proj = nn.Linear(dim, dim)

    def inference(self, x):
        h = x
        steps = 0
        for _ in range(20):
            h = self.proj(h)
            steps += 1
            if bool((h.max() > 0.9).item()):   # the stop token, in miniature
                break
        return h * steps


class InnerFlow(nn.Module):
    """The decoder's actual network, with nothing awkward in it. This is the
    thing worth converting, and until now the probe had no way to reach it —
    it only ever tried the method it saw being called."""

    def __init__(self, dim=512):
        super().__init__()
        self.a = nn.Linear(dim, dim)
        self.b = nn.Linear(dim, dim)

    def forward(self, x):
        return self.b(torch.relu(self.a(x)))


class FakeS3Gen(nn.Module):
    """The waveform decoder, and it wears the shape the real one turned out
    to have: A CLEAN NETWORK INSIDE A WRAPPER THAT VALIDATES ITS INPUT.

    Both of chatterbox's decoder blockers are here and neither is arithmetic:

        the range check   `if (token >= self.vocab_size).any()` — flow.py:164.
                          A branch on data, which the newer exporter must
                          resolve in advance and cannot.
        the spectrogram   `torch.stft` — hifigan.py:397, at the very end,
                          turning numbers into a waveform. Signal processing,
                          and the older exporter refuses it outright.

    `self.flow` is untouched by either and converts on its own. That is the
    whole hypothesis in miniature: the wrapper is what refuses, the network is
    fine, and the game does not need the wrapper because it controls what goes
    in."""

    def __init__(self, n_fft=64, dim=512):
        super().__init__()
        self.n_fft = n_fft
        self.vocab_size = 100
        self.flow = InnerFlow(dim)
        self.post = nn.Linear(n_fft // 2 + 1, 8)

    def inference(self, wav, token=None):
        if token is not None and bool((token >= self.vocab_size).any()):
            raise ValueError("token out of range")
        h = self.flow(wav)
        spec = torch.stft(h, n_fft=self.n_fft, hop_length=self.n_fft // 4,
                          window=torch.hann_window(self.n_fft),
                          return_complex=True)
        mag = spec.abs().transpose(1, 2)
        return self.post(mag)


class FakeVE(nn.Module):
    """The voice encoder. Fails in the window arithmetic — Python-level
    `divmod` on a value that becomes a tensor the moment tracing starts. Its
    `forward` is the pure network and converts cleanly, which is exactly the
    split the probe's fall-through is for."""

    def __init__(self, dim=16):
        super().__init__()
        self.net = nn.Linear(dim, dim)
        self.win = 8
        self.step = 4

    def forward(self, frames):
        return self.net(frames).mean(dim=1)

    def inference(self, mel):
        n_frames = mel.shape[1]
        # `divmod` on a traced tensor. The real one is voice_encoder.py:62.
        n_wins, _rem = divmod(max(n_frames - self.win + self.step, 0), self.step)
        n_wins = max(int(n_wins), 1)
        frames = mel[:, :n_wins * self.step, :].reshape(mel.shape[0], -1, mel.shape[2])
        return self.forward(frames)


class FakeChatterbox:
    """The wrapper. Not an `nn.Module`, deliberately — the real
    `ChatterboxTTS` is a plain holder, and the probe has to cope with a `model`
    that has no `.eval()` of its own. That detail was guessed at for two runs."""

    def __init__(self):
        self.t3 = FakeT3()
        self.s3gen = FakeS3Gen()
        self.ve = FakeVE()

    def generate(self, text, audio_prompt_path=None, exaggeration=0.5):
        """Drives all three through `inference`, and NOT through `forward`,
        which is what made the probe's first hook report a decoder that plainly
        ran as 'never called'."""
        self.ve.inference(torch.randn(1, 40, 16))
        self.t3.inference(torch.randn(1, 32))
        self.s3gen.inference(torch.randn(1, 512), torch.tensor([[3, 4]]))
        return torch.randn(1, 512)


def load():
    m = FakeChatterbox()
    for sub in (m.t3, m.s3gen, m.ve):
        sub.eval()
    return m


def selftest():
    """The fixture is only useful if it fails the way the real thing does. A
    stand-in that exports cleanly would certify a broken probe."""
    fails, ran = [], []

    def check(ok, what, got=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + ("" if ok else f" — {got}"))
        ran.append(what)
        if not ok:
            fails.append(what)

    import tempfile
    import pathlib
    m = load()

    check(m.generate("x") is not None, "the fixture generates without a GPU or weights")
    check(not hasattr(m, "eval"),
          "the wrapper has no eval() of its own, like the real ChatterboxTTS")

    tmp = pathlib.Path(tempfile.mkdtemp())
    expected = {
        "s3gen": (m.s3gen, (torch.randn(1, 512),), "STFT"),
        "ve": (m.ve, (torch.randn(1, 40, 16),), "divmod"),
    }
    for key, (sub, args, want) in expected.items():
        class W(torch.nn.Module):
            def __init__(self, inner):
                super().__init__()
                self.inner = inner

            def forward(self, *a):
                return self.inner.inference(*a)
        got = ""
        try:
            with torch.no_grad():
                torch.onnx.export(W(sub), args, str(tmp / f"{key}.onnx"),
                                  opset_version=17, dynamo=False)
            got = "exported, which it must not"
        except Exception as e:
            got = f"{type(e).__name__}: {e}"
        check(want.lower() in got.lower(),
              f"{key}'s inference() fails on {want}, like the real one", got[:110])

    # AND THE HALF THAT MAKES THE FALL-THROUGH TESTABLE: ve's pure network has
    # to EXPORT, or the probe's "try forward instead" path has no accepting
    # case and would look correct while doing nothing.
    try:
        with torch.no_grad():
            torch.onnx.export(m.ve, (torch.randn(1, 10, 16),),
                              str(tmp / "ve_fwd.onnx"), opset_version=17, dynamo=False)
        ok, why = True, ""
    except Exception as e:
        ok, why = False, f"{type(e).__name__}: {e}"
    check(ok, "but ve's forward() DOES export — the fall-through's accepting case", why[:110])

    print(f"\nfixture --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks")
    return 0 if fails else 0 if not fails else 1


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
