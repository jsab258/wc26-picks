line: infrastructure (instruments, the evidence channel)
spec: game-design/decision-2026-09-03-texture-staging-and-the-still-gate-ratchet.md, rulings A and E
acceptance: a lint refusing any key=value inside a COMMENT line of a verdict-shaped file, run over the emitters AND over the committed evidence; shipped with its selftest, accepting case first per the standing rule; it carries the rejecting case ruling A could not run
max_sessions: 1
status: READY 2026-09-03. instrument-builder. This is the item that stops the ratchet recurring.

## The incident that paid for it

`LedgerProbe.cpp` wrote its own explanation into the evidence file's header:

    # shotStatus=WROTE needs a decoded file with more than one bucket ...

and the workflow gated on `Select-String "shotStatus=(\S+)" | Select-Object -First 1`.
The first match in the landed file is that comment. So the still gate had been
reading WROTE out of its own explanation and COULD NOT HAVE FAILED, whatever
the frame was. The same pair existed for `captureStatus`.

A gate that cannot fail is worse than no gate: it spends a run and returns a
green that nobody can question.

## WHY THE OBVIOUS SWEEP WOULD HAVE BANKED A FALSE CLEAN RESULT

This is the part worth reading twice. `tools/verdict-dupkeys.py` looks like
the instrument for this and is ANTI-CORRELATED with the fault. Its line 144:

    if len({frozenset(v) for v in values.values()}) < 2:
        continue  # same values everywhere: repeated, not ambiguous

The header said `WROTE` and the measured line said `WROTE`, so the value sets
matched and the tool stayed silent. It goes quiet EXACTLY when the header
quotes the passing value, which is EXACTLY when the ratchet exists. Pointing
dupkeys at `production/d1-probe/` and reporting its silence would have been a
clean result from a tool that cannot see this shape.

That is why the dupkeys work folds into queue 029 BEHIND this item, and why it
is not the sweep.

## The named next rung, so the aspect is not blank

The gate readers still live in YAML where no test can reach them.
`tools/ue/make_base_material.py` just showed the correct shape by moving its
status decision into a tested layer; the readers should follow it there.
