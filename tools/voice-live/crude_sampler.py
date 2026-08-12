"""THE CRUDE SAMPLER THE MEASUREMENT TOOLS SHARE — one copy, on purpose.

`time-a-line` and `speak-a-few` each carried their own `pick()`, and both were
missing the repetition penalty that EVERY real sampler in the model's package
applies (`inference` and `inference_turbo` both use 1.2). That absence is not a
detail: its textbook symptom is runaway generation, and a five-line listening
test produced exactly that — Ada to the 1001-token ceiling — which I then
blamed on removing classifier-free guidance. The experiment had conflated the
sampler and the guidance, and the conclusion "guidance is not removable" was
published on the strength of it.

One idea, two implementations, and both were wrong the same way. Hence this
module: the penalty exists in exactly one place, and the tools that time and
the tools that listen sample identically.

STILL NOT THE SHIPPED SAMPLER. `Core/SpeechLoop` is, and it matches the
model's own processors to 1e-5 — it has carried the repetition penalty from
the start, which is why the game was never exposed to the fault the tools had.
This one stays deliberately simple: temperature, min-p, the guidance combine,
and now the penalty, because the penalty changes HOW MANY steps a line runs
and a timing tool without it measures lines that cannot happen.
"""

REPETITION_PENALTY = 1.2


def penalise(np, row, said, penalty=REPETITION_PENALTY):
    """HF's convention, applied to already-said tokens: a positive logit is
    divided by the penalty and a negative one multiplied, so 'less likely'
    comes out regardless of sign. Getting the sign branch wrong makes
    repetition MORE likely for negative logits, which is why this is shared
    and checked rather than retyped."""
    if not said:
        return row
    idx = np.fromiter(said, dtype=np.int64)
    vals = row[idx]
    row[idx] = np.where(vals > 0, vals / penalty, vals * penalty)
    return row


def pick(np, logits, rng, rows, said):
    """A token, cheaply. Guidance combine + temperature + min-p + repetition
    penalty. `said` is the set of tokens already sampled this line; the caller
    adds each pick to it."""
    v = logits.reshape(rows, -1)
    x = (v[0] + 0.5 * (v[0] - v[1]) if rows > 1 else v[0]).astype(np.float64).copy()
    x = penalise(np, x, said)
    x = x / 0.8
    x = x - x.max()
    p = np.exp(x)
    p[p < 0.05 * p.max()] = 0.0        # min_p, roughly
    s = p.sum()
    if s <= 0:
        return int(np.argmax(x))
    return int(rng.choice(len(p), p=p / s))
