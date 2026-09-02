line: infrastructure (content pipeline)
spec: this file
acceptance: a workflow_dispatch job on the ledger-pc runner that runs the image batch and commits its outputs by name with attribution from the same run; a NO RUN line when it generates nothing; the same route proven for meshgen
max_sessions: 1
status: READY 2026-09-02. engine-specialist, small. HIGHEST LEVERAGE ITEM IN THE QUEUE per point spent.

## The finding, and it is a planning fault rather than a technical one

The week plan of 2026-09-02 allotted five days entirely to Claude-priced
work and scheduled ZERO local generation. Jafar caught it. Local compute on
his machine costs NOTHING against the weekly ceiling, runs overnight while
nobody is working, and the project has been treating it as a thing to get to
later rather than the free lane it is.

## What is already sitting there, ready, costing nothing to run

- `tools/imagegen/prompts.json`, schema 2, **45 entries written**: shopfront
  fascias, harbour and station signage, council and dock notices, gig and
  bingo and election posters, wall materials. Only **14 PNGs exist** under
  `ledger/Assets/StreamingAssets/Decals/generated/`, so roughly 31 have
  never been generated.
- `tools/meshgen`, proven: 37 props in 54 seconds on 2026-09-01.
- `tools/props/fetch_vignette.py`, proven through its own workflow.

## The gap, which is one workflow

`make-the-pictures` and `make-the-props` are in `tools/pc-watcher.py`'s job
table with 9 hour timeouts, but that channel needs the watcher RUNNING on
his PC and `pc-results` has not moved since 14 August, so it is unproven.
The channel that IS proven is the self-hosted `ledger-pc` runner: three
workflows target it and `ledger-vignette-fetch.yml` shows the exact shape,
including why `workflow_dispatch` alone is not enough on a non-default
branch and what this repo does about it.

There is no imagegen workflow. Write one, modelled on that file.

## Why this is worth a builder slot before almost anything else

It costs about 2 points ONCE and then every generation run for the rest of
the project is free. Nothing else in the queue has that shape.

## Do not

Do not run a bulk batch before the route is proven on a small one. The
generator has a known Vulkan blank-PNG mode, so a night that produces 400
blank files is a night wasted and a manifest full of lies. `imagegen.py`
carries `blank_verdict`; the run must fail on blanks and print the count
with its denominator.
