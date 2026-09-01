# Task file format (NNN-slug.md)

Front matter, then the brief. One task, one deliverable (waste lesson 3).

    line:          which pipeline (pipelines.md table)
    spec:          path to the spec file driving this task
    acceptance:    the checks that must pass, by name
    max_sessions:  how many continuations before it goes to blocked/

Rules: tasks are sized to finish comfortably inside one session (runner.md
sizing rule). A task too big writes its resumable state file under
production/scratch/<agent>/ and enqueues a continuation task pointing at it.
Two consecutive failures move the task to blocked/ with logs linked; the loop
moves on and blocked items surface in the morning brief.

Standing tasks: a recurring task (the 900 process audit) re-enqueues itself
on completion; the done/ copy carries that week's findings. No scheduler,
no clock, the queue is the only mechanism.

## Before an item moves to done/

Ask the quality-ladder question, which is CLAUDE.md's standing order and
has no other trigger point: is this the best available result, or the first
working one? The next rung is either taken now or written into
production/quality-ladder.md with a name. An aspect whose next rung is
blank is a research task, not a finished aspect.

The ladder used to live in game-design/queue.md, which v2 superseded, so
from 31 Aug the mechanism had a live enforcement clause and no home in the
tree anybody was working in. Nothing announced that.
