# D1: Engine (probe, do not debate)
Date: 2026-08-31. Status: OPEN, probe authorized. Owner: Engineering.
Context: photoreal target, driving later, faces required, big world later, full rebuild authorized. UE5 offers Lumen, Nanite, World Partition, MetaHuman, City Sample crowds and vehicles, all free. Unity holds the working codebase, CI, screenshot instruments, and faster agent iteration loops (C# vs C++ builds; text YAML vs binary uassets).
Choice mechanism: a two-week timeboxed probe, then a decision record citing measurements, never taste.
Probe spec: port the perception core plus its tests to UE5 C++ (transliteration); build one instrumented street scene (screenshot pipeline, frame budget capture); measure (a) agent-loop friction (median edit-build-test cycle time, failed-edit rate on binary assets), (b) visual ceiling reached in the timebox on the same street built in both engines, (c) CI and instrument rebuild cost estimate, (d) faces path (MetaHuman plus Audio2Face vs CC4 plus Audio2Face in Unity).
Decision rule: Unreal wins only if (b) is decisively better and (a) is tolerable for autonomous operation. Ties go to Unity (momentum, instruments, iteration speed). Either way the world stays data-driven: JSON/YAML world source of truth, generators emit engine content, binary assets are build products.
Revisit when: never, absent a gate failure that names this decision.
