line: infrastructure
spec: .github/workflows/ledger-art-blender-preview.yml declares
  `runs-on: [self-hosted, windows]` where the other eight self-hosted workflows declare
  `[self-hosted, ledger-pc]`. Pin it to ledger-pc like its neighbours.
acceptance: all nine self-hosted workflows name the same machine label, counted and printed.
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09. `windows` is an automatic runner label, not a machine name. It
  matched today because ledger-pc carries both, so nothing is broken now. The hazard is
  future and quiet: a second Windows runner joining the account would become eligible for
  Blender renders on a machine that has no Blender, and the failure would look like a broken
  recipe rather than a misrouted job.
  FOUND WHILE FIXING A DIFFERENT FAULT in the same file, which is why it is filed rather
  than folded in: the ask was the PATH bootstrap and this is not it.
