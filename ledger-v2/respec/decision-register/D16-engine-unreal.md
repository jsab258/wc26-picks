# D16: the engine is Unreal

STATUS: DECIDED 2026-09-10 by Jafar, dictated and recorded by the resident.
Premise level: it settles which engine the game is, which every later
technical decision hangs from. Closes the D1 engine probe on its evidence.

## The decision

**Unreal. D1's probe is closed on the evidence.**

Unity becomes THE LEGACY REFERENCE BUILD. Its assets, its game scripts and
its dead probe projects are ARCHIVED, NOT DELETED, per ruling 3 of the same
message.

## What survives, and it is not a courtesy

**The C# Core stays as the source of truth the C++ port is checked against.**
That is the whole reason the archive is not a deletion: a port with no
reference is a rewrite, and a rewrite is how behaviour drifts without anyone
being able to name the moment.

These keep running and are not archived:
CoreTests, Soak, SaveChaos, PerceptionGolden, StrangerTest.

## Why this was decidable now

The probe answered what it was built to answer. The Unreal side reached a
built street with placed prop meshes, a captured sky, a directional sun whose
asked elevation now arrives, a pinned exposure that removes adaptation, and
an evidence channel that commits its own frames and verdict. The remaining
faults are ordinary engineering rather than open questions about the engine.

## What it does NOT license

It does not license deleting the Unity work, and ruling 3 says so in one
line: archive, never delete, everything retired under legacy/ with an index
naming what it was and why it stopped.

## One consequence, found the same day and recorded here rather than filed

`tools/dashboard/build-dashboard.py --selftest` reports 1 failure, and it is
this decision's doing rather than a defect:

    FAIL D1 countdown derives from the real dates: nothing-measured
         no 'kicked off <date>, ends <date>' line in production/d1-probe/plan.md

The check exists to stop a countdown to the D1 engine decision being typed by
hand instead of derived. D1 IS NOW DECIDED, by this record, so there is nothing
left to count down to and the plan file has no kickoff line to read. The check
is correct, its subject is gone, and it will report nothing-measured for ever
until it is retired.

It is left standing on purpose for now: a nothing-measured that says so in words
is the honest state, and removing a check the same day its subject closed is how
a gate quietly loses coverage nobody notices. It is retired when the D1 probe
directory is archived, not before, and this paragraph is the reason the next
reader will find when they wonder why one selftest is red.
