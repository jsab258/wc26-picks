line: studio (the art line's runner path)
spec: A5 of the 2026-09-08 ruling. ledger-art-blender-preview.yml lines 168 to 183
  make six plain git calls on a self-hosted Windows runner whose checkout is owned
  by NETWORK SERVICE while the steps run as Jafar. The first would die on dubious
  ownership and the render would be lost silently, which is exactly what happened
  to the mesh import on 2026-09-08. It also has NO EVIDENCE FILE AT ALL, and the
  2>/dev/null || true at line 174 is the second silence.
acceptance: every git call carries -c safe.directory='*' and the env triple, the step
  publishes a key=value file naming its commit whatever happens, and the swallowed
  error at 174 is a named refusal
max_sessions: 1
status: LANDED 2026-09-09 as a precondition of the Mickey's blockout dispatch, which the
  2026-09-08 ruling section 5 required to go first. The GIT_CONFIG triple plus
  -c safe.directory='*' is on every git call, the commit and gate steps are
  if: always() so a failed render still publishes, the swallowed 2>/dev/null || true is a
  named refusal, and the run writes a key=value verdict naming its commit whatever happens.
  UNRUN UNTIL THE FIRST DISPATCH: none of it has executed on the machine.
  PRIOR READY 2026-09-08. Filed by the director ruling
  game-design/decision-2026-09-08-crimeprobe-the-grate-and-the-art-line.md,
  section 7, which files names rather than work.
