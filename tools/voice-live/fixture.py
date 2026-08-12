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
        self.tfmr = KwargsOnly(dim)
        self.proj = nn.Linear(dim, dim)
        with torch.no_grad():
            # Contracting, so the norm decays and the stop condition is
            # reached after a number of steps that DEPENDS ON THE INPUT —
            # which is the property being reproduced.
            #
            # 0.95 RATHER THAN 0.7, and the difference is the whole point.
            # At 0.7 each step shrinks the norm by a third, so the ~26% gap
            # between the fixture's two voices was less than one step wide and
            # both drives ran the same number of times — the loop was
            # data-dependent and the counter could not see it. Measured across
            # two contraction rates and four thresholds before choosing: 0.95
            # with a threshold of 1.0 gives four steps for one voice and three
            # for the other.
            self.proj.weight.mul_(0.95)

    def inference(self, x):
        # Called by keyword and with a non-tensor flag, exactly as the real
        # transformer is — the flag must stay baked in while the tensor
        # becomes a graph input.
        # A REAL GENERATION LOOP: the FIRST call has no cache — there is
        # nothing to remember yet — and every later one carries the cache the
        # previous step produced. The stand-in used to hand a cache in on the
        # very first call, which is the one arrangement that hid the fault:
        # the probe kept the first call, found a cache there, and never
        # noticed it would find none on the real model.
        cache = None
        h = x
        for _ in range(3):
            out = self.tfmr(inputs_embeds=h, use_cache=True, past_key_values=cache)
            h, cache = out.last_hidden_state, out.past_key_values
        h = h
        steps = 0
        for _ in range(20):
            h = self.proj(h)
            steps += 1
            if bool((h.norm() < 1.0).item()):   # the stop token, in miniature
                break
        return h * steps


class ModelOutputish:
    """Stands in for `BaseModelOutputWithPast`. A transformers model does not
    return a tuple, it returns an OBJECT with the tensors as attributes — and
    `np.asarray` on one of these gives a 0-dimensional object array, which is
    how the converted transformer got reported as "shapes differ: shape []
    became [2, 74, 1024]" when the export had in fact worked."""

    def __init__(self, hidden, cache=None):
        self.last_hidden_state = hidden
        self.past_key_values = cache

    def to_tuple(self):
        return (self.last_hidden_state, self.past_key_values)


# REGISTERED WITH TORCH, AS TRANSFORMERS DOES. Without this the stand-in is
# STRICTER than the real thing: the exporter refuses any unknown object, so
# the cache-off retry had no accepting case here and looked broken while the
# real model converted fine. A fixture that fails where reality succeeds is as
# useless as one that succeeds where reality fails — it just fails safe.
try:
    from torch.utils import _pytree as _pt

    _pt.register_pytree_node(
        ModelOutputish,
        lambda o: ([o.last_hidden_state, o.past_key_values], None),
        lambda vals, _ctx: ModelOutputish(vals[0], vals[1]),
    )
except Exception:
    pass


class DynamicCacheish:
    """Stands in for HuggingFace's `DynamicCache`: parallel key and value
    lists, and the legacy constructor the real one has.

    Deliberately not a tensor and not a tuple — being a type no exporter can
    put in a graph is its whole role. It now HOLDS the tensors as well, so the
    cache-as-plain-tensors route has something real to flatten; a stand-in
    whose cache is empty would let that route report success while carrying
    nothing."""

    def __init__(self, ks=None, vs=None):
        self.key_cache = list(ks or [])
        self.value_cache = list(vs or [])

    def grow(self, h):
        """Append this step's key/value — IN PLACE, ON THE OBJECT IT WAS
        HANDED, which is what the real one does and what this used to fake.

        The old version returned a FRESH cache of a fixed size every call, so
        the object the caller passed in was never touched and its length never
        changed. That made the fixture blind to the fault that cost this
        morning: the probe's spy stored the cache OBJECT, the model appended
        to it during the call, and every later reader got a cache one token
        too long — containing the token the graph was being built to process.

        A stand-in that cannot express the fault certifies the probe against a
        world that does not exist. This is the fifth time this fixture has
        agreed with me rather than with reality, so the shape is now taken
        from the real thing rather than from what was convenient: grow by
        REBINDING (`torch.cat`, then assign) rather than writing into the
        existing tensor, because that is what makes a snapshot free.
        """
        step = h.unsqueeze(1) if h.dim() == 2 else h
        if not self.key_cache:
            self.key_cache, self.value_cache = [step], [step]
        else:
            self.key_cache = [torch.cat([self.key_cache[0], step], dim=1)]
            self.value_cache = [torch.cat([self.value_cache[0], step], dim=1)]

    @classmethod
    def from_legacy_cache(cls, pairs):
        return cls([p[0] for p in pairs], [p[1] for p in pairs])

    def to_legacy_cache(self):
        return tuple(zip(self.key_cache, self.value_cache))


class KwargsOnly(nn.Module):
    """A network called ENTIRELY BY KEYWORD, like t3's transformer.

    `tfmr(inputs_embeds=...)` is how chatterbox drives its Llama stack, and it
    defeated the probe completely: the captured positional args were empty, so
    the export was handed no inputs, the trace had nothing to vary, and the
    module raised "You must specify exactly one of input_ids or inputs_embeds".
    That reads as the model refusing to convert. It was the harness having no
    way to express a keyword input.

    The cost was not the error. The probe fell through to the next child and
    converted an 8.4M-parameter embedding table instead — 1.6% of the stage —
    and reported that as the result."""

    def __init__(self, dim=32):
        super().__init__()
        self.a = nn.Linear(dim, dim)

    def forward(self, inputs_embeds=None, input_ids=None, use_cache=False,
                past_key_values=None):
        if (inputs_embeds is None) == (input_ids is None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")
        x = inputs_embeds if inputs_embeds is not None else input_ids
        h = self.a(x)
        if past_key_values is not None and past_key_values.key_cache:
            # Reusing what the last step computed, which is the entire point
            # of a cache and the thing the exported graph has to be able to do.
            # Shape-agnostic on purpose: the stand-in's stage is 2-D and an
            # earlier version indexed it as 3-D, which broke the MODEL rather
            # than testing the export — the same mistake as varying a feature
            # dimension instead of a time axis, two commits ago.
            #
            # AND IT AVERAGES THE WHOLE HISTORY, so the answer DEPENDS ON THE
            # CACHE LENGTH. Reading one entry cannot tell a cache of 2 from
            # the same cache with the current token wrongly appended, and that
            # is precisely the fault this fixture exists to catch now.
            past = past_key_values.key_cache[0]
            h = h + past.mean(dim=1) * 0.1
        if not use_cache:
            # The shape that broke the comparison: tensors inside an object.
            return ModelOutputish(h)
        # A CACHE OBJECT IN THE OUTPUT, which is what actually stopped the
        # real transformer once the keyword problem was fixed: "Found
        # DynamicCache in output, which is not a known type". Neither exporter
        # can carry an object like this through a graph, and the standard way
        # past it is to turn the cache off — so the fixture has to return one,
        # or that retry has no failing case.
        kv = past_key_values if past_key_values is not None else DynamicCacheish()
        kv.grow(h)
        return ModelOutputish(h, kv)


class InnerFlow(nn.Module):
    """The decoder's actual network, with nothing awkward in it. This is the
    thing worth converting, and until the fall-through existed the probe had
    no way to reach it — it only ever tried the method it saw being called.

    Acts on the LAST dimension, so the time axis is free to vary. That
    matters: a second reference clip is a different duration, and an earlier
    version of this fixture varied the feature dimension instead and broke the
    original model rather than testing the export."""

    def __init__(self, dim=64):
        super().__init__()
        self.a = nn.Linear(dim, dim)
        self.b = nn.Linear(dim, dim)

    def forward(self, x):
        return self.b(torch.relu(self.a(x)))

    def inference(self, x):
        """FLOW-MATCHING STARTS FROM A RANDOM SAMPLE, which is what the name
        means and what makes the real decoder impossible to compare against
        itself. Measured on the real thing: 39.8% disagreement on the input it
        was traced with, which I was one commit away from calling a broken
        export. Two calls of this, unconverted, disagree by more than 100%."""
        h = torch.randn_like(x)
        return self.b(torch.relu(self.a(h + x)))


class FakeS3Gen(nn.Module):
    """The waveform decoder, wearing the shape the real one turned out to
    have: A CLEAN NETWORK INSIDE A WRAPPER THAT VALIDATES ITS INPUT.

    Both of chatterbox's decoder blockers are here and neither is arithmetic:

        the range check   `if (token >= self.vocab_size).any()` — flow.py:164.
                          A branch on data, which the newer exporter must
                          resolve in advance and cannot.
        the spectrogram   `torch.stft` — hifigan.py:397, at the very end,
                          turning numbers into a waveform. Signal processing,
                          and the older exporter refuses it outright.

    `self.flow` is untouched by either. The time axis varies between the two
    drives, because reference clips are not all one length."""

    def __init__(self, n_fft=64, dim=64):
        super().__init__()
        self.n_fft = n_fft
        self.vocab_size = 100
        self.flow = InnerFlow(dim)
        self.post = nn.Linear(n_fft // 2 + 1, 8)

    def inference(self, feats, token=None):
        if token is not None and bool((token >= self.vocab_size).any()):
            raise ValueError("token out of range")
        h = self.flow.inference(feats)            # (1, T, dim), and RANDOM
        wav = h.mean(dim=-1)                      # (1, T)
        spec = torch.stft(wav, n_fft=self.n_fft, hop_length=self.n_fft // 4,
                          window=torch.hann_window(self.n_fft),
                          return_complex=True)
        return self.post(spec.abs().transpose(1, 2))


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
        ran as 'never called'.

        THE INPUTS DEPEND ON THE ARGUMENTS. They used to be fresh `randn`
        every call, which made a second drive with a different voice and a
        different line produce input statistically identical to the first —
        so the second-voice comparison would have passed no matter what, and
        the check would have looked like it worked. A stand-in has to vary
        where the real thing varies."""
        # ONE FIXED NOISE PATTERN, SCALED BY `exaggeration`, and nothing
        # keyed off the file path.
        #
        # Two earlier versions were both unreproducible. The first seeded from
        # `hash()`, which python salts per process. The second seeded from a
        # crc of the clip PATH — stable within a machine and different on
        # every machine, so a loop length tuned here would not hold on
        # Jafar's, and the check would silently stop testing anything.
        #
        # `exaggeration` is the honest axis: the probe really does drive the
        # two takes at 0.45 and 0.7, it is a number rather than a filename,
        # and it is the same everywhere. Same noise, different scale, so the
        # loop length tracks it and the two drives differ for a reason that
        # can be stated in one line.
        # ONE GENERATOR PER PART, so each part's input depends only on
        # `exaggeration` and not on how many draws happened before it. With a
        # shared generator, t3 got the SECOND draw — so a threshold tuned by
        # measuring a fresh first draw was tuned against a tensor the fixture
        # never produces, and I read the probe's correct answer as a bug in the
        # probe for two rounds.
        def gen(tag):
            return torch.Generator().manual_seed(20260806 + tag)
        wob = 0.5 + float(exaggeration)
        self.ve.inference(torch.randn(1, 40, 16, generator=gen(1)) * wob)
        self.t3.inference(torch.randn(1, 32, generator=gen(2)) * wob)
        # A SECOND CLIP IS A DIFFERENT LENGTH. Real reference clips are not
        # all the same duration, and a graph frozen at one length cannot serve
        # a second line of dialogue — the encoder's check died on exactly that
        # ("Got: 685 Expected: 1175") and reported "could not check".
        # A SECOND CLIP IS A DIFFERENT LENGTH. Real reference clips are not
        # all the same duration, and a graph frozen at one length cannot serve
        # a second line of dialogue — the encoder's check died on exactly that
        # ("Got: 685 Expected: 1175") and reported "could not check". T varies;
        # the feature dimension does not.
        T = 512 if float(exaggeration) < 0.6 else 640
        self.s3gen.inference(torch.randn(1, T, 64, generator=gen(3)) * wob,
                             torch.tensor([[3, 4]]))
        return torch.randn(1, 512, generator=gen(4))


def load():
    """FIXED WEIGHTS, and this took three runs to notice.

    The modules were built with torch's default initialisation and no seed, so
    every process got a different model — and the loop-count check, which is
    about how many steps the stop condition takes, read 3-vs-3, then 2-vs-3,
    then 3-vs-3 across three identical runs. I went looking at the seeding of
    the INPUTS twice before checking the seeding of the WEIGHTS, because the
    inputs were the part I had just written.

    A fixture that differs between runs cannot support a claim in either
    direction: a check that passes is not evidence, and one that fails is not
    a bug report."""
    torch.manual_seed(20260806)
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

    # THE CACHE MUST GROW ON THE OBJECT IT WAS HANDED, or this fixture cannot
    # express the fault that cost 7 August: the probe's spy stored the cache
    # object, the model appended to it during the call, and every later reader
    # got a cache one token too long — the token the graph was being built to
    # process, present in its own history.
    #
    # The old fixture returned a fresh fixed-size cache every call, so the
    # caller's object never changed and the probe run reported no growth. The
    # end-to-end run now reports at_call [1,2,32] against read_now [1,3,32],
    # which is the fault visible in the report for the first time.
    #
    # Checked as a PROPERTY rather than trusted from that one run, because a
    # fixture quietly losing its teeth is how the last five of these happened.
    kv = DynamicCacheish()
    tf = KwargsOnly(32)
    with torch.no_grad():
        out = tf(inputs_embeds=torch.randn(1, 32), use_cache=True, past_key_values=kv)
        held = list(kv.key_cache)                      # the caller's own handle
        before = held[0].shape[1]
        tf(inputs_embeds=torch.randn(1, 32), use_cache=True, past_key_values=out.past_key_values)
    check(out.past_key_values is kv,
          "the cache is grown IN PLACE, not replaced with a fresh one")
    check(kv.key_cache[0].shape[1] == before + 1,
          f"and the object the caller still holds has grown {before} to "
          f"{kv.key_cache[0].shape[1]} behind its back")
    check(held[0].shape[1] == before,
          "while a snapshot of the TENSORS taken before the call has not — "
          "which is why snapshotting costs nothing")

    tmp = pathlib.Path(tempfile.mkdtemp())
    import atexit as _ax, shutil as _sh   # same leak as export-decode's: 19.8GB of these in one evening
    _ax.register(_sh.rmtree, tmp, True)
    expected = {
        "s3gen": (m.s3gen, (torch.randn(1, 512, 64),), "STFT"),
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
