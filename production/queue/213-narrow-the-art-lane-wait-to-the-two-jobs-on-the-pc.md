line: infrastructure
spec: The art lane's queue step waits on all five game workflows. Wait only on the two that
  run on ledger-pc (probe-unreal, build-windows); keep QUERYING and PRINTING all five, so the
  evidence loses nothing and only the sleeping narrows.
acceptance: a poll prints all five statuses while the wait count names only the pc ones, and
  a planted in-progress reading on a hosted workflow does NOT extend the wait.
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09, ruled in game-design/decision-2026-09-09-ruling-the-settled-exposure-and-the-two-lanes.md and QUEUED RATHER THAN APPLIED because that ruling
  permitted it in the landing commit only if it were literally one line. It is not: the busy
  accumulation, the per-poll print and the series string all carry the count, so narrowing
  means splitting "seen" from "waited on" in three places.
  THE REASON IS SHARPER THAN THE ONE FIRST OFFERED. The art job itself runs on
  [self-hosted, ledger-pc], so the poll loop sleeps WHILE HOLDING the runner. Waiting on a
  GitHub-hosted job is a lock held while sleeping: it buys the game lane nothing and actively
  delays the two pc jobs the wait exists to yield to. That is negative, not neutral, and its
  sign needs no series.
  STATED IN ADVANCE SO IT IS NOT READ AS A BUG: narrowed, with one runner serving one job at
  a time, the loop should read clear on the first poll essentially always and the yield
  becomes a 30 second no-op. That is correct. If a pc name ever reads in progress WHILE this
  step executes, that is a finding and not a wait, because it means more than one runner is
  registered.
