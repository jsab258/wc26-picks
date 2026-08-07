#!/usr/bin/env python3
"""THE KEY/VALUE CACHE AS PLAIN TENSORS, so a converted transformer can be
driven step by step without redoing the whole sentence every step.

    python3 tools/voice-live/kv_cache.py --selftest

THE PROBLEM, measured on Jafar's machine rather than assumed. t3's transformer
converts — 503M parameters, agreeing with the original to 4.9e-07 — but only
with `use_cache=False`, because neither ONNX exporter can carry HuggingFace's
`DynamicCache` object through a graph.

Without the cache, every step reprocesses the entire sentence from the
beginning. That is quadratic work for a linear job, and the cost is not
theoretical:

    0.46 s per step x 97 steps  = 45 s for one line of dialogue
    against about 3.7 s of speech, so ~13x slower than real time

A cache is not part of the answer. It is the model remembering what it already
worked out, and the only reason it defeats the exporter is that it arrives as
an OBJECT. The same information as a flat list of tensors — previous keys and
values in, updated keys and values out — exports without complaint, which is
checked here rather than hoped: the shape is exported and run before anything
else in this file is believed.

WHAT THIS DOES NOT DO. It does not make the loop disappear. The game still
drives the model one step at a time and decides when the line is finished;
this only stops each of those steps costing the whole sentence again.
"""
import argparse
import sys

import torch


def find_cache(kwargs):
    """The cache-like argument among a call's keywords, if there is one.

    Recognised by SHAPE rather than by class name: anything holding parallel
    lists of key and value tensors, or offering the legacy tuple-of-pairs
    form. Matching on `DynamicCache` by name is how the last retry ended up
    firing on the real model and not on the stand-in.
    """
    for name, v in (kwargs or {}).items():
        if v is None or hasattr(v, "shape"):
            continue
        if cache_layout(v):
            return name, v
    return None, None


def cache_layout(v):
    """Which shape of cache this is, or None. Named because there are three
    and the code has to say which it found.

    TRANSFORMERS MOVED THE TENSORS. Older releases hang parallel `key_cache`
    and `value_cache` lists off the object; from 4.56 they live in a `layers`
    list whose entries each carry `keys` and `values`. A detector that knows
    only the first shape finds nothing on a current install and — before this
    commit — recorded nothing either, so the whole cache route left no trace
    in the report at all: not a success, not a failure, not attempted.
    """
    if hasattr(v, "key_cache") and hasattr(v, "value_cache"):
        return "key_cache/value_cache"
    layers = getattr(v, "layers", None)
    if layers is not None:
        try:
            if len(layers) and hasattr(layers[0], "keys") and hasattr(layers[0], "values"):
                return "layers[].keys/values"
        except Exception:
            pass
    if hasattr(v, "to_legacy_cache"):
        return "to_legacy_cache()"
    return None


def snapshot_cache(kwargs):
    """(name, tensors) for a call's cache AS IT IS AT THIS INSTANT.

    A CACHE READ AFTER THE CALL IS NOT THE CACHE THE CALL WAS GIVEN, and both
    places that read one were reading it afterwards.

    The model appends the token it is processing to the cache it was handed.
    So a spy that stores the cache OBJECT and reads its tensors later gets a
    cache one token longer than the call received — containing the very token
    the graph is being converted to process. The graph then bakes in a
    position one too far, and every check still passes, because the reference
    run and the ONNX run are both handed the same wrong cache and agree with
    each other perfectly.

    Measured, not reasoned about: it showed up first in this file's own
    selftest as a disagreement that fell off as 1/n — 7.3e-03 at cache length
    5, 3.9e-03 at 9, 2.1e-03 at 20, which is one duplicated token's share of
    the attention and nothing else. The same line was in `export_probe`'s spy.
    One idea, two implementations, and the second is the one nobody looked at.

    Costs nothing. Growth REBINDS (`ly.keys = torch.cat(...)`) rather than
    writing into the existing tensor, so holding the list of tensors is enough
    and no data is copied — checked, at cache length 5: the snapshot still
    reads 5 after a call that takes the object to 6.
    """
    name, cache = find_cache(kwargs)
    if cache is None:
        return None, None
    return name, cache_to_tensors(cache)


def describe(kwargs, args=()):
    """What a call's non-tensor arguments actually are — so a cache that is
    not recognised can be identified from the report instead of by guessing
    at another release's field names."""
    out = {}
    for i, v in enumerate(args or ()):
        # POSITIONAL TOO. A cache handed over unnamed is invisible to a
        # keyword-only sweep, and would look identical to no cache at all.
        if v is None or hasattr(v, "shape"):
            continue
        out[f"positional[{i}]"] = {"type": type(v).__name__,
                                   "layout": cache_layout(v),
                                   "attrs": [a for a in ("key_cache", "value_cache",
                                                         "layers", "to_legacy_cache")
                                             if hasattr(v, a)]}
    for name, v in (kwargs or {}).items():
        if v is None or hasattr(v, "shape"):
            continue
        out[name] = {"type": type(v).__name__,
                     "layout": cache_layout(v),
                     "attrs": [a for a in ("key_cache", "value_cache", "layers",
                                           "to_legacy_cache", "keys", "values")
                               if hasattr(v, a)]}
    return out


def cache_to_tensors(cache):
    """Flatten a cache into [k0, v0, k1, v1, ...]. Empty cache -> []."""
    if cache is None:
        return []
    ks = getattr(cache, "key_cache", None)
    vs = getattr(cache, "value_cache", None)
    if ks is None:
        layers = getattr(cache, "layers", None)
        if layers is not None:
            try:
                ks = [ly.keys for ly in layers]
                vs = [ly.values for ly in layers]
            except Exception:
                ks = vs = None
    if ks is None and hasattr(cache, "to_legacy_cache"):
        legacy = cache.to_legacy_cache()
        ks = [p[0] for p in legacy]
        vs = [p[1] for p in legacy]
    if not ks:
        return []
    out = []
    for k, v in zip(ks, vs):
        out.extend([k, v])
    return out


def tensors_to_cache(flat, like):
    """Rebuild a cache of `like`'s type from [k0, v0, k1, v1, ...].

    A COPY OF THE REAL ONE, WITH ITS TENSORS SWAPPED — not a fresh object.

    Constructing one from scratch threw `IndexError: list index out of range`
    on Jafar's transformers: sixty tensors came OUT of the cache and could not
    be put back into a new one, so the cached export failed and the run
    measured the uncached path for the seventh time.

    Guessing at another release's constructor is what got me here. A cache
    carries bookkeeping this code cannot see — a sequence counter, per-layer
    objects, whatever the next version adds — and the object in hand already
    has all of it, correctly, for this exact model. Copying it and replacing
    the tensors keeps every field right by construction and needs to know
    nothing about the class.

    Falls back through the older shapes so a cache that IS cheap to rebuild
    still is, and raises with the layout named rather than an IndexError from
    somewhere inside a library.
    """
    import copy

    pairs = [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]

    layout = cache_layout(like)
    if layout == "layers[].keys/values":
        fresh = copy.copy(like)
        fresh.layers = [copy.copy(ly) for ly in like.layers]
        if len(fresh.layers) != len(pairs):
            raise ValueError(
                f"cache has {len(fresh.layers)} layers but {len(pairs)} key/value "
                f"pairs were handed back — the flatten and the rebuild disagree")
        for ly, (k, v) in zip(fresh.layers, pairs):
            ly.keys, ly.values = k, v
        return fresh

    if layout == "key_cache/value_cache":
        fresh = copy.copy(like)
        fresh.key_cache = [k for k, _ in pairs]
        fresh.value_cache = [v for _, v in pairs]
        return fresh

    cls = type(like)
    if hasattr(cls, "from_legacy_cache"):
        return cls.from_legacy_cache(tuple(pairs))

    raise ValueError(f"cannot rebuild a cache of type {cls.__name__} — "
                     f"no recognised layout")


def make_cached_wrapper(module, method, tensor_kw_names, const_kwargs,
                        n_positional, cache_name, cache_like):
    """A module whose graph takes and returns cache tensors.

    Inputs:  the real tensor arguments, then every cache tensor.
    Outputs: the model's own outputs, then the UPDATED cache tensors.

    Both halves matter. Taking the cache in is what stops the step redoing the
    sentence; handing it back out is what lets the next step continue — a
    graph that accepts a cache and does not return one is a graph that can
    only ever run once.
    """
    n_cache = len(cache_to_tensors(cache_like))

    class CachedWrapper(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.inner = module

        def forward(self, *a):
            pos = a[:n_positional]
            rest = a[n_positional:]
            named = dict(zip(tensor_kw_names, rest[:len(tensor_kw_names)]))
            flat = list(rest[len(tensor_kw_names):])
            named.update(const_kwargs)
            named["use_cache"] = True
            if flat:
                named[cache_name] = tensors_to_cache(flat, cache_like)
            out = getattr(module, method)(*pos, **named)

            # THE UPDATED CACHE, PULLED BACK OUT AND FLATTENED. Where it lives
            # differs by version — an attribute, a slot in a tuple — so it is
            # searched for rather than assumed to be in a fixed place.
            new = None
            if hasattr(out, "past_key_values"):
                new = out.past_key_values
            elif isinstance(out, (tuple, list)):
                for item in out:
                    if item is not None and not hasattr(item, "shape"):
                        if hasattr(item, "key_cache") or hasattr(item, "to_legacy_cache"):
                            new = item
                            break
            tensors = cache_to_tensors(new)
            head = out.last_hidden_state if hasattr(out, "last_hidden_state") else (
                out[0] if isinstance(out, (tuple, list)) else out)
            return (head, *tensors)

    w = CachedWrapper()
    w._n_cache = n_cache
    return w


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + ("" if ok else f" — {got}"))
        ran.append(what)
        if not ok:
            fails.append(what)

    import tempfile
    import pathlib
    import time
    torch.manual_seed(20260806)
    D, L = 64, 4
    tmp = pathlib.Path(tempfile.mkdtemp())

    class CacheLike:
        """Wears HuggingFace's shape: parallel key and value lists, and the
        legacy constructor the real one has."""
        def __init__(self, ks=None, vs=None):
            self.key_cache = list(ks or [])
            self.value_cache = list(vs or [])

        @classmethod
        def from_legacy_cache(cls, pairs):
            return cls([p[0] for p in pairs], [p[1] for p in pairs])

        def to_legacy_cache(self):
            return tuple(zip(self.key_cache, self.value_cache))

    class Block(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.q = torch.nn.Linear(D, D)
            self.k = torch.nn.Linear(D, D)
            self.v = torch.nn.Linear(D, D)

        def forward(self, x, pk=None, pv=None):
            k, v = self.k(x), self.v(x)
            if pk is not None:
                k = torch.cat([pk, k], dim=1)
                v = torch.cat([pv, v], dim=1)
            a = torch.softmax(self.q(x) @ k.transpose(1, 2) / D ** 0.5, -1)
            return a @ v, k, v

    class Stack(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.blocks = torch.nn.ModuleList([Block() for _ in range(L)])

        def forward(self, inputs_embeds=None, past_key_values=None, use_cache=False):
            ks, vs = [], []
            x = inputs_embeds
            for i, b in enumerate(self.blocks):
                pk = pv = None
                if past_key_values is not None and len(past_key_values.key_cache) > i:
                    pk = past_key_values.key_cache[i]
                    pv = past_key_values.value_cache[i]
                x, k, v = b(x, pk, pv)
                ks.append(k)
                vs.append(v)
            return (x, CacheLike(ks, vs)) if use_cache else (x, None)

    m = Stack().eval()

    # 0. BOTH LAYOUTS, because transformers moved the tensors at 4.56 and a
    # detector that knows only one finds nothing on a current install.
    class NewLayer:
        def __init__(self, k, v):
            self.keys, self.values = k, v

    class NewCache:
        def __init__(self, pairs=()):
            self.layers = [NewLayer(k, v) for k, v in pairs]

        def update(self, k, v, i):
            while len(self.layers) <= i:
                self.layers.append(NewLayer(None, None))
            self.layers[i].keys, self.layers[i].values = k, v

    nc = NewCache([(torch.randn(1, 3, D), torch.randn(1, 3, D)) for _ in range(L)])
    check(cache_layout(nc) == "layers[].keys/values",
          "the newer transformers layout is recognised, not just the older one")
    check(len(cache_to_tensors(nc)) == 2 * L,
          "and flattens to the same tensor list")
    check(cache_layout(object()) is None,
          "and an object that is not a cache is not mistaken for one")
    d = describe({"past_key_values": nc, "x": torch.randn(1, 1)})
    check("past_key_values" in d and d["past_key_values"]["layout"],
          "an unrecognised call can be identified from what describe() reports")

    # 1. THE CACHE IS FOUND BY SHAPE, not by class name.
    seed = CacheLike([torch.randn(1, 3, D) for _ in range(L)],
                     [torch.randn(1, 3, D) for _ in range(L)])
    name, found = find_cache({"inputs_embeds": torch.randn(1, 1, D),
                              "past_key_values": seed, "use_cache": True})
    check(name == "past_key_values" and found is seed,
          "a cache is recognised by holding key and value lists, not by its class name")
    check(find_cache({"inputs_embeds": torch.randn(1, 1, D)})[0] is None,
          "and a call with no cache reports none rather than guessing at one")

    # 2. FLATTEN AND REBUILD HAVE TO ROUND-TRIP, or the model silently sees
    # somebody else's memory.
    flat = cache_to_tensors(seed)
    check(len(flat) == 2 * L, f"a {L}-layer cache flattens to {2 * L} tensors")
    back = tensors_to_cache(flat, seed)
    same = all(torch.equal(a, b) for a, b in
               zip(back.key_cache + back.value_cache, seed.key_cache + seed.value_cache))
    check(same, "and rebuilds to exactly the tensors it came from")

    # 2b. THE NEWER LAYOUT ROUND-TRIPS TOO, and by copying rather than
    # constructing — building a fresh one threw IndexError on the real model.
    nc2 = tensors_to_cache(cache_to_tensors(nc), nc)
    check(len(nc2.layers) == L and all(
        torch.equal(a.keys, b.keys) and torch.equal(a.values, b.values)
        for a, b in zip(nc2.layers, nc.layers)),
        "the newer layout rebuilds by copying, keeping every other field")
    check(nc2 is not nc and nc2.layers[0] is not nc.layers[0],
          "and it is a copy, so writing to it cannot corrupt the model's own cache")
    try:
        tensors_to_cache(cache_to_tensors(nc)[:2], nc)
        mismatch = False
    except ValueError:
        mismatch = True
    check(mismatch,
          "a rebuild with the wrong number of pairs raises and says so, rather "
          "than an IndexError from inside a library")

    # 3. THE POINT OF ALL OF IT: does the cached form actually export?
    w = make_cached_wrapper(m, "forward", ["inputs_embeds"], {}, 0,
                            "past_key_values", seed)
    args = (torch.randn(1, 1, D), *flat)
    ok, why = True, ""
    try:
        with torch.no_grad():
            torch.onnx.export(w, args, str(tmp / "kv.onnx"), opset_version=17,
                              dynamo=False)
    except Exception as e:
        ok, why = False, f"{type(e).__name__}: {e}"
    check(ok, "the cached form EXPORTS, which the cache object never did", why[:110])

    # 4. AND IT HANDS THE UPDATED CACHE BACK, or it can only run once.
    with torch.no_grad():
        out = w(*args)
    check(len(out) == 1 + 2 * L,
          f"and returns the head plus {2 * L} updated cache tensors", f"{len(out)}")
    check(out[1].shape[1] == 4,
          "whose sequence has grown by the one token just processed",
          f"{tuple(out[1].shape)}")

    # 5. IT HAS TO BE FASTER, or none of this was worth doing. Same work both
    # ways: ninety steps of one token.
    with torch.no_grad():
        t0 = time.time()
        seq = torch.randn(1, 1, D)
        for _ in range(90):
            seq = torch.cat([seq, torch.randn(1, 1, D)], dim=1)
            m(inputs_embeds=seq)
        slow = time.time() - t0

        t0 = time.time()
        x, cache = torch.randn(1, 1, D), None
        for _ in range(90):
            h, cache = m(inputs_embeds=x, past_key_values=cache, use_cache=True)
            x = h[:, -1:]
        fast = time.time() - t0
    check(fast < slow,
          f"and it is faster: {slow * 1000:.0f} ms uncached against {fast * 1000:.0f} ms cached",
          f"{slow * 1000:.0f} vs {fast * 1000:.0f} ms")

    # 6. AGAINST A REAL TRANSFORMER, on the version chatterbox pins.
    #
    # Every check above passes on a hand-built stand-in and four runs still
    # came back "IndexError: list index out of range". The stand-in cannot
    # catch a fault in how the probe ASSEMBLES the inputs, because the
    # stand-in is handed them correctly by the test. A real `LlamaModel` is
    # ~2 MB of randomly initialised weights and needs no download, which
    # makes this the cheapest thing here and the one that would have caught
    # it on day one.
    try:
        from transformers import LlamaConfig, LlamaModel
        cfg = LlamaConfig(hidden_size=64, intermediate_size=128,
                          num_hidden_layers=3, num_attention_heads=4,
                          num_key_value_heads=4, vocab_size=100)
        real = LlamaModel(cfg).eval()
        for prm in real.parameters():
            prm.requires_grad_(False)
        step_in = torch.randn(1, 1, 64)
        with torch.no_grad():
            a = real(inputs_embeds=torch.randn(1, 5, 64), use_cache=True)
            b = real(inputs_embeds=step_in, use_cache=True,
                     past_key_values=a.past_key_values)
        rc = b.past_key_values
        rflat = cache_to_tensors(rc)
        check(cache_layout(rc) is not None and len(rflat) == 2 * 3,
              f"a real transformers cache is recognised and flattens to {len(rflat)}")
        rw = make_cached_wrapper(real, "forward", ["inputs_embeds"], {}, 0,
                                 "past_key_values", rc)

        # THE ASSEMBLY, BOTH WAYS. This is the fault four runs could not name.
        wrong = tuple(rflat)                       # keywords dropped
        right = (step_in,) + tuple(rflat)          # keywords carried
        try:
            with torch.no_grad():
                torch.onnx.export(rw, wrong, str(tmp / "wrong.onnx"),
                                  opset_version=17, dynamo=False)
            broke = False
        except Exception:
            broke = True
        check(broke,
              "dropping the tensor keywords from the inputs FAILS, as it did on "
              "Jafar's machine four times")
        ok2, why2 = True, ""
        try:
            with torch.no_grad():
                torch.onnx.export(rw, right, str(tmp / "right.onnx"),
                                  opset_version=17, dynamo=False)
        except Exception as e:
            ok2, why2 = False, f"{type(e).__name__}: {e}"
        check(ok2, "and carrying them EXPORTS a real cached transformer", why2[:110])

        # AND IT HAS TO WORK AT A CACHE LENGTH IT WAS NOT CONVERTED AT, or it
        # can only ever run for one sentence. The cache grows by one every
        # step, so a fixed length here means the graph is unusable from step
        # two onward — which is exactly what "could not check: Got 145,
        # Expected 156" was reporting.
        import onnxruntime as ort
        import numpy as np
        rnames = ["x"] + [f"c{i}" for i in range(len(rflat))]
        raxes = {"x": {0: "b", 1: "t"}}
        for n in rnames[1:]:
            raxes[n] = {0: "b", 2: "past"}
        with torch.no_grad():
            torch.onnx.export(rw, right, str(tmp / "dyn.onnx"), opset_version=17,
                              dynamo=False, input_names=rnames, dynamic_axes=raxes)
        sess = ort.InferenceSession(str(tmp / "dyn.onnx"),
                                    providers=["CPUExecutionProvider"])
        # AND THE CACHE IS SNAPSHOTTED BEFORE THE REFERENCE CALL, NOT AFTER.
        #
        # This check failed at 7.3e-03 and I spent a build believing the
        # dynamic axis was at fault, then a second one on the theory that
        # rotary position had been baked at trace time — which it had not, and
        # passing `position_ids` as an explicit input made the traced length
        # itself WORSE (1.9e-07 to 5.14e-03). Both hypotheses were about the
        # subject. The fault was the instrument, three lines below this one.
        #
        # `real(..., past_key_values=cc)` APPENDS to `cc`. Reading `cc` after
        # it therefore hands ONNX a cache containing the token it is being
        # asked to process, so that token is attended to twice and the graph
        # is blamed for it.
        #
        # The tell was in the series and I printed it before I read it: the
        # error fell off as 1/n — 7.3e-03 at 5, 3.9e-03 at 9, 2.1e-03 at 20,
        # and 7.3/2.1 = 3.5 is exactly 21/6. One duplicated token's share of
        # the attention mass, which is not what a broken axis looks like.
        #
        # The series is still printed, because the number that mattered here
        # was never the worst — it was the SHAPE of the three.
        series = {}
        for n in (5, 9, 20):
            with torch.no_grad():
                seeded = real(inputs_embeds=torch.randn(1, n, 64), use_cache=True)
                cc = seeded.past_key_values
                _, ff = snapshot_cache({"past_key_values": cc})   # BEFORE
                want = real(inputs_embeds=step_in, use_cache=True,
                            past_key_values=cc)[0].numpy()
            check(ff[0].shape[2] == n,
                  f"the cache snapshot at length {n} stays {n} across the call "
                  f"that grows it to {n + 1}")
            feeds = {"x": step_in.numpy()}
            feeds.update({f"c{i}": t.numpy() for i, t in enumerate(ff)})
            got = sess.run(None, feeds)[0]
            series[n] = (float(np.abs(want - got).max())
                         / max(float(np.abs(want).max()), 1e-12))
        traced_len = rflat[0].shape[2]
        feeds0 = {"x": step_in.numpy()}
        feeds0.update({f"c{i}": t.numpy() for i, t in enumerate(rflat)})
        with torch.no_grad():
            want0 = real(inputs_embeds=step_in, use_cache=True,
                         past_key_values=tensors_to_cache(rflat, rc))[0].numpy()
        got0 = sess.run(None, feeds0)[0]
        baseline = (float(np.abs(want0 - got0).max())
                    / max(float(np.abs(want0).max()), 1e-12))
        worst = max(series.values())
        print("        series: traced(%d)=%.1e  " % (traced_len, baseline)
              + "  ".join(f"{n}={v:.1e}" for n, v in series.items()))
        # An absolute bound is right here after all — but only because the
        # instrument is. 1e-04 is three orders above what a correct graph
        # reads and three below the fault it was hiding.
        check(worst <= 1e-4,
              f"and a cache length it was NOT converted at is right too — "
              f"worst {worst:.1e} against {baseline:.1e} at the traced length",
              f"{worst:.2e} vs {baseline:.2e}")
    except ImportError:
        check(True, "real-transformer check skipped: transformers not installed")

    print(f"\nkv-cache --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
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
