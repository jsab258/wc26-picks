line: production (the probe's own bodies)
spec: BindSurfaces runs inside BuildScene, before any probe piece exists, so the
  witness, the second NPC, the shards, the brick and the yard floor all carry the
  engine default material. The crime verdict prints probePiecesMaterialBound=0/21
  with the reason rather than leaving it to be noticed in a frame.
acceptance: an export binds a surface's EXISTING material instance to an actor spawned
  after BuildScene, and probePiecesMaterialBound reads 21/21
max_sessions: 1
status: READY 2026-09-08. Filed by the director ruling
  game-design/decision-2026-09-08-crimeprobe-the-grate-and-the-art-line.md,
  section 7, which files names rather than work.
