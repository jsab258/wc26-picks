# The UE evidence channel: spec

STATUS: SPEC. Written 2026-09-01.

What LEDGER's Unity side does, and what the UE side has to do before D1 can
be decided on anything.

## What the channel is, in one paragraph

Every Windows build commits a text verdict whose first line names the commit
it was measured on, a per-run copy keyed by short sha, and a small number of
stills. Nothing else in this project has ever been readable: log tails are
truncated, step summaries come back empty, artifact hosts are blocked. The
committed file is the whole feedback loop, and every rule around it exists
because a specific failure cost a day.

## The four properties that must survive the move

1. PROVENANCE. Line 1 names the commit. A run that measured nothing writes
   the words rather than letting an older file stand under a newer name.
2. STAGED BY NAME. Never `git add <directory>`. A failed run otherwise
   commits its stale checkout's files as its own evidence, which happened
   and cost a morning of reading pictures that could not have been rendered.
3. NO SPACES IN A VALUE. The file is space-separated key=value and every
   reader splits on whitespace. Structure goes in `/` and `..`.
4. WHOLE-RUN NUMBERS ON THE DONE LINE, per-sample numbers on the sample
   line. Never one key carrying two moments.

If those four hold, `tools/verdict-read.py`, `verdict-keys.py`, `gates.py`
and `landed.py` keep working unchanged, and the instrument inventory's
estimate of what would be rebuilt stays honest.

## The UE-specific constraints, researched rather than assumed

RENDERING HEADLESS IS `-RenderOffScreen`, NOT `-nullrhi`. They are opposite
things and the probe currently uses the wrong one for this purpose: nullrhi
means no rendering at all, which is right for the golden test and useless
for a still. ledger-pc has a real GPU and runs a twelve-minute Unity sim
producing JPEGs, so offscreen with hardware should be available; the fallback
on Windows without acceleration is WARP software rasterisation, which is far
too slow for real time but can render individual frames, which is exactly
what this channel needs.

Known hazard from the same research: Vulkan offscreen has been reported to
crash, and the reports are on Linux. The probe is Windows and D3D, so this
should not apply, and it is written down so the next reader knows the
question was asked rather than skipped.

NAMED UNCERTAINTY, NOT YET CHECKED: the exact capture call. Candidates are
`FScreenshotRequest::RequestScreenshot` and the `HighResShot` console
command. Both are documented; neither has been run here. The first build to
attempt a still must print which one it used and whether a file appeared,
because "the call returned" and "a picture exists" are different facts.

## The order of work, cheapest informative step first

1. A verdict file and nothing else. No rendering, no camera, no RHI. Prove
   the file lands, names its commit, and reads clean through
   verdict-read.py. This can ride the existing golden test.
2. One still, offscreen, of whatever the default map contains. Prove a file
   appears and can be committed. Content is irrelevant at this stage.
3. A placed camera and a named frame, matching the Unity still convention.
4. Only then, anything about how the street looks.

Steps 1 and 2 answer D1. Steps 3 and 4 are measurement b and belong to the
reference street, not here.

## What would close this as a negative

If a UE run cannot commit a traceable verdict from the self-hosted agent
after a fair attempt, that is a finding and it is written as one. It does not
become "Unity wins" by default: D1 gives ties to Unity, and a tie is a
MEASURED tie. An unmeasurable UE side closes D1 UNRESOLVED.
