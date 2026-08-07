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
        if hasattr(v, "key_cache") and hasattr(v, "value_cache"):
            return name, v
        if hasattr(v, "to_legacy_cache"):
            return name, v
    return None, None


def cache_to_tensors(cache):
    """Flatten a cache into [k0, v0, k1, v1, ...]. Empty cache -> []."""
    if cache is None:
        return []
    ks = getattr(cache, "key_cache", None)
    vs = getattr(cache, "value_cache", None)
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

    Uses the class's own constructor path where it has one, because a cache
    carries bookkeeping — a sequence-length counter, a layer index — that a
    hand-built object would not have and whose absence surfaces hundreds of
    lines later as a wrong answer rather than an error.
    """
    pairs = tuple((flat[i], flat[i + 1]) for i in range(0, len(flat), 2))
    cls = type(like)
    if hasattr(cls, "from_legacy_cache"):
        return cls.from_legacy_cache(pairs)
    obj = cls()
    if hasattr(obj, "key_cache"):
        obj.key_cache = [p[0] for p in pairs]
        obj.value_cache = [p[1] for p in pairs]
    return obj


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
