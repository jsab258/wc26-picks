#!/usr/bin/env python3
"""The work queue has enough in it to survive the next build.

    python3 tools/queue-check.py

WHY THIS EXISTS.

`game-design/queue.md` was written on 3 August to stop a specific failure: four
idle gaps of 20, 32, 19 and 28 minutes, each one immediately after dispatching a
build, because the moment after a dispatch is a decision point and re-deriving
priorities from a 400-line roadmap is enough friction to lose to.

It worked, for an hour. Eighteen commits, longest gap eight minutes. Then three
more gaps — 21, 28, 28 — and the cause was not that the rule was forgotten. THE
QUEUE HAD RUN OUT. Every non-CI item had been done, and what remained was
waiting on a build or waiting on Jafar.

The queue emptied because its own instructions guaranteed it would: *"every item
is sized to fit inside one build round trip."* Every item consumable in under
half an hour means an hour of good work exhausts the list, and an empty list
reads exactly like an empty afternoon.

So this counts what is left. It is not a style check — it is the difference
between "I have finished the queue" and "I have finished the project", which
are easy to confuse at the end of a long turn and have very different next
actions.

WHAT IT COUNTS. Items under `## Now` and `## Next` that are NOT marked `*(CI)*`
and NOT under `## Blocked`. Those are the ones that can be picked up this
minute. A queue full of CI-blocked items is a queue that cannot fill the next
twenty-eight minutes, which is precisely the state that produced the gaps.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUEUE = ROOT / "game-design" / "queue.md"

# BELOW THIS, REFILL BEFORE DISPATCHING. Three is not a measured optimum and is
# not presented as one: it is one item to work on plus two behind it, which is
# the smallest number that survives discovering the first is blocked. Rule 2
# says do not invent thresholds — this is a floor on a COUNT rather than a
# bound on a measurement, and the failure it guards is "zero", which needs no
# calibration.
FLOOR = 3


def main():
    if not QUEUE.exists():
        print("queue-check: no queue.md — nothing schedules the next hour")
        return 1

    text = QUEUE.read_text(encoding="utf-8")

    # Only the actionable sections. `## Blocked` is deliberately excluded: an
    # item waiting on somebody else is not work, and counting it is how a queue
    # looks full while being empty.
    body, keep = [], False
    for line in text.split("\n"):
        if line.startswith("## "):
            keep = line.startswith("## Now") or line.startswith("## Next")
            continue
        if keep:
            body.append(line)

    # GROUPED, BECAUSE ITEMS ARE MULTI-LINE. The first version tested each
    # NUMBERED line for the `(CI)` marker, and every marker in the file sits on
    # a continuation line — so no item ever counted as CI-blocked and "ready"
    # was just the item count wearing a more reassuring name. A distinction
    # that can never fire is not a distinction.
    items, current = [], None
    for l in body:
        if re.match(r"^\d+\.\s+\*\*", l.strip()):
            if current is not None:
                items.append(current)
            current = l
        elif current is not None:
            current += "\n" + l
    if current is not None:
        items.append(current)
    ready = [it for it in items if "(CI)" not in it]
    # `## Standing work`, NOT `## Standing`. The first version matched
    # "## Standing rules this file exists to serve" — a section about how to
    # use the queue, not a section of work — and reported the backstop present
    # when there was none. A checker that passes on a prefix collision is worse
    # than no checker: it certifies the exact state it was written to catch.
    standing = "## Standing work" in text

    print(f"queue-check: {len(items)} item(s), {len(ready)} ready to start now, "
          f"standing track {'present' if standing else 'MISSING'}")

    problems = []
    if len(ready) < FLOOR:
        problems.append(f"only {len(ready)} item(s) can be started without waiting on CI "
                        f"(want {FLOOR}) — refill from the roadmap BEFORE the next dispatch")
    # A STANDING TRACK IS THE BACKSTOP. Short items always run out eventually;
    # the queue needs one entry that cannot be completed, so "no short work
    # left" is never the same sentence as "no work left".
    if not standing:
        problems.append("no `## Standing` section — nothing to fall back on when "
                        "the short items run out, which is how the queue emptied on 3 Aug")

    for p in problems:
        print("  " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
