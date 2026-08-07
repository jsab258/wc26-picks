#!/usr/bin/env python3
"""THE C# SAMPLER, CHECKED AGAINST THE ONE IT IS COPYING.

    python3 tools/voice-live/sampler-reference.py            # print the cases
    python3 tools/voice-live/sampler-reference.py --selftest  # check they hold

WHY THIS EXISTS. `Core/SpeechLoop.Pick` reimplements chatterbox's token
sampler in C#, because the loop it sits in cannot be exported to ONNX — the
number of steps depends on the words. A reimplementation of a sampler is the
worst kind of thing to get wrong: every mistake still produces speech. Wrong
temperature, a penalty applied in the wrong direction, a filter the model does
not use — all of them yield a voice, saying the words, sounding slightly off,
with no error anywhere and nothing to grep for.

The first draft of that file had four constants wrong and was missing
classifier-free guidance entirely, and it would have run.

So the reference implementation is asked directly. `transformers` ships the
exact processors `t3.py` builds — RepetitionPenaltyLogitsProcessor,
MinPLogitsWarper, TopPLogitsWarper — and this runs them over fixed logits in
the fixed order the model uses, then prints which tokens survive and what
their weights are. Those numbers are pasted into `TestSpeechLoop` as literals.

WHAT IS COMPARED IS THE SURVIVING SET AND THE ORDER, NOT THE DRAWN TOKEN.
Python and C# have different random number generators, so the same seed draws
differently and always will — that is stated in `SpeechLoop`'s header and it is
why a live line can never byte-match a baked one. What CAN be identical is the
distribution the draw is made from, and that is the whole of the sampler.
"""
import argparse
import json
import sys

CASES = [
    # (name, logits, already-said tokens)
    ("flat", [1.0] * 8, []),
    ("confident", [0.0, 0.0, 0.0, 20.0, 0.0, 0.0, 0.0, 0.0], []),
    ("two close, nothing said", [0.0, 0.0, 2.0, 1.9, 0.0, 0.0, 0.0, 0.0], []),
    ("two close, leader already said", [0.0, 0.0, 2.0, 1.9, 0.0, 0.0, 0.0, 0.0], [2]),
    # THE NEGATIVE CASE, and it is the one that catches the obvious bug.
    # A penalty implemented as a plain divide makes -2.0 into -1.67, which is
    # MORE likely, so the penalty rewards what it exists to discourage across
    # the whole negative half of the range.
    ("negative logits, leader already said",
     [-2.0, -2.1, -40.0, -40.0, -40.0, -40.0, -40.0, -40.0], [0]),
    ("a graded spread", [3.0, 2.5, 2.0, 1.0, 0.0, -1.0, -5.0, -20.0], []),
    ("a graded spread with two said", [3.0, 2.5, 2.0, 1.0, 0.0, -1.0, -5.0, -20.0], [0, 2]),
]

# tts.py generate(...) defaults, read from the installed package.
TEMPERATURE = 0.8
REPETITION_PENALTY = 1.2
MIN_P = 0.05
TOP_P = 1.0


def reference(logits, said):
    """chatterbox's own order: penalty, temperature, min-p, top-p, softmax."""
    import torch
    from transformers import (LogitsProcessorList, MinPLogitsWarper,
                              RepetitionPenaltyLogitsProcessor, TopPLogitsWarper)

    scores = torch.tensor([logits], dtype=torch.float32)
    ids = torch.tensor([said], dtype=torch.long) if said else torch.zeros((1, 0), dtype=torch.long)

    scores = RepetitionPenaltyLogitsProcessor(penalty=REPETITION_PENALTY)(ids, scores)
    if TEMPERATURE != 1.0:
        scores = scores / TEMPERATURE
    scores = MinPLogitsWarper(min_p=MIN_P)(ids, scores)
    scores = TopPLogitsWarper(top_p=TOP_P)(ids, scores)

    probs = torch.softmax(scores, dim=-1)[0]
    # A filtered-out token is set to -inf, so its probability is exactly zero.
    kept = [i for i, p in enumerate(probs.tolist()) if p > 0.0]
    kept.sort(key=lambda i: -probs[i].item())
    return kept, [round(probs[i].item(), 6) for i in kept]


def rows():
    out = []
    for name, logits, said in CASES:
        kept, weights = reference(logits, said)
        out.append({"case": name, "logits": logits, "said": said,
                    "kept": kept, "weights": weights})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    try:
        data = rows()
    except ImportError as e:
        # A DENOMINATOR ON THE SKIP. "transformers is not installed" and "every
        # case passed" must not print the same way — that is rule 3b, and this
        # file exists because of a fault that looked exactly like health.
        print(f"  skipped: {e} — 0 of {len(CASES)} cases checked")
        return 0

    if a.json:
        print(json.dumps(data, indent=2))
        return 0

    for r in data:
        print(f"  {r['case']}")
        print(f"      said={r['said']}  kept={r['kept']}")
        print(f"      weights={r['weights']}")

    if a.selftest:
        bad = []
        for r in data:
            if not r["kept"]:
                bad.append(f"{r['case']}: nothing survived the filters")
            # The leader must change when the leader has already been said and
            # a close rival has not. If this stops holding, the penalty has
            # stopped doing anything and every check built on it is vacuous.
        lead_clean = next(x for x in data if x["case"] == "two close, nothing said")
        lead_said = next(x for x in data if x["case"] == "two close, leader already said")
        if lead_clean["kept"][0] == lead_said["kept"][0]:
            bad.append("the repetition penalty did not change the leader — "
                       "the reference itself is not doing anything")
        neg = next(x for x in data if x["case"] == "negative logits, leader already said")
        if neg["kept"][0] != 1:
            bad.append(f"penalising a negative logit did not demote it: kept={neg['kept']}")
        for b in bad:
            print(f"  FAIL  {b}")
        print(f"\nsampler-reference --selftest: "
              f"{'PASS' if not bad else str(len(bad)) + ' FAILED'} — {len(data)} cases")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
