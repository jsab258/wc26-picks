line: infrastructure (instruments)
spec: game-design/decision-2026-09-02-rotation-fix-lands.md, Ruling 3
acceptance: Foot5 rotates its corner offsets by the piece's actual yaw; the litter footprints probed at their true corners; the print shows what changed
max_sessions: 1
status: READY 2026-09-02. Not a landing condition, ruled a queue item.

`Foot5` swaps the footprint half-extents at yaw 90 and probes every other
yaw UNROTATED. Its comment claimed "yaw is 0 or 90 for everything this
scene places", which was already false: `G8_litter` carries an arbitrary
`YawDeg = r0 * 180.0` and is footed. The rotation fix made the swap branch
effectively dead, since no footed family carries yaw 90 any more.

THE ERROR IS BOUNDED AND SMALL, which is why this is a queue item and not a
landing condition: at 45 degrees on the widest piece the true footprint
reaches about 6 cm beyond where its probes look. It cannot move
`datumMissing`, because the probes still land on the piece.

Rotate the corner offsets by the piece's real yaw.

THE STANDING TRAP, ruled in advance: if rotated corners turn out to cross
the kerb step, that is a LITTER FINDING to be fixed in `Scatter` where the
litter is placed, and NEVER a reason to widen the bound. A bound moved to
make a red go away is the ratchet this project has a rule about.
