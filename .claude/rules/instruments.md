---
description: Rules for any file that emits metrics, verdict keys, probes, or gates
globs: ["**/verdict*", "**/*probe*", "**/*gate*", "**/*metric*", "tools/**"]
---

# Instrument code

Loaded when editing measurement code, because instrument faults are the
quietest class there is: a broken feature shows; a broken instrument shows
you the wrong world.

- **Say what the number is a statistic OF** — peak / median / last-wins /
  cumulative / at-worst — in the name or the comment beside the emit.
- **Every zero ships its denominator.** "0 failing" prints beside "N
  examined"; never-ran prints the words "nothing measured".
- **Every cap announces itself**: `(+N more not shown)`.
- **No spaces in `key=value` values** — every reader splits on whitespace
  and truncates silently. Use `/` and `..` for structure.
- **Whole-run numbers on the done line; per-sample numbers on the sample
  line.** Never both moments under one key, never one pair split across
  lines a grep will silently merge.
- **A numerator's denominator is captured at the instant the numerator
  peaks**, and named so (`xAtWorst`).
- **A new bound needs a printed series first.** Ship the printer, read
  real runs, then set the number from evidence — in that order.
- **Selftest ships with the tool, accepting case first.** For tools that
  check the project itself, the live codebase is the accepting fixture,
  and the rejecting fixture is synthetic (a key that exists nowhere), so
  doing the work the tool prompts can never break the tool.
- **Before concluding from two numbers, read the code that produces them**
  and ask whether either can move while the other stands still — two
  numbers derived from one variable are one number twice.
