# AI-driven production feasibility, condensed (full report: research/full/, Jafar exports)

Scoped originally at a GTA-like; retained here is what survives the pivot to LEDGER.

1. Architecture: the world's source of truth is text data (JSON/YAML) plus generator scripts; engine scenes are build products. This is what makes any engine workable for agents and what makes expansion additive. Holds regardless of D1's outcome.
2. Density techniques, all agent-drivable: modular kits and kitbashing, trim sheets, decal layering (grime, posters, wear carry photoreal frames), rule-based scattering, fake-interior window shaders, HLOD/impostors. Interiors: a small real set plus faked windows is the AAA norm.
3. Geodata shortcut: OSM/Overture footprints and road graph as skeleton, self-generated geometry, attribution, fictionalized layout. Never ship Google 3D tiles.
4. Asset stack: Blender headless (bpy) as the processing hub for import, cleanup, retopo, UV, LOD, collision at batch scale; local TRELLIS for props; paid Meshy/Tripo only when convenience pays; buy hero assets at the CC0 ceiling; local SDXL/Flux for tileable PBR sets.
5. Faces and voice: Audio2Face-3D (MIT) batch over the corpus; hundreds of distinct voices via the local pipeline; precompute all fixed lines, reserve runtime generation for live conversation.
6. Precompute doctrine: build-time generation converts one-off spend into a permanent static library (barks, radio, signage, backstories) with zero per-player cost; runtime LLM plus renderer share one GPU, so budgets are measured, not assumed (already proven once at 38 tokens per second against 25 needed).
7. Honest limits: art-direction coherence needs an enforced bible and calibrated judges; game feel is hand-tuned on bought foundations; performance and memory need budgets from day one; no netcode.
8. Platform and legal: purely AI-generated assets carry no US copyright, protect via code, arrangement, brand; Steam requires disclosure of player-facing generative content, not coding tools; roughly a fifth of 2025 Steam releases disclosed AI, so the company is normal.
