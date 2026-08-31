# D2: Faces move
Date: 2026-08-31. Status: APPROVED direction, implementation pending D1.
Context: the moat is conversation; the most-viewed surface is a talking face at close range; current characters import with blendShapes off and lip sync appears nowhere in legacy docs. The decision entered via a shopping list, the wrong door.
Choice: all conversational characters get blendshape-capable heads. Driving layer: NVIDIA Audio2Face-3D (open-sourced 2025-09-24, MIT), batch over the generated clip corpus, streamed for live speech as a later step. Rig source per D1: MetaHuman if Unreal (free under 1M revenue, usable outside Unreal, never used to train AI models per its addendum), Character Creator 4 if Unity (one-off cost in D6 budget).
Consequences: character import pipeline re-enables blendshapes; crowd-only NPCs may keep static faces at distance LODs.
Instrument: a talking-head test scene; judge-scored naturalness sample; Jafar feel check in Phase 2.
