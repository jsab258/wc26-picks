line: infrastructure
spec: The art lane's queue step runs as a job step, so by the time it asks whether a game job
  is in progress it is ALREADY holding the self-hosted runner. Decide whether the lane can
  yield before taking the runner at all, and if it cannot, say so in the file with the reason.
acceptance: either the wait happens before the runner is occupied, or the workflow states in
  its own header why that is impossible on this runner and what the holding costs.
max_sessions: 1
status: READY 2026-09-09, ruled in game-design/decision-2026-09-09-ruling-the-settled-exposure-and-the-two-lanes.md. IT IS THE STRUCTURAL VERSION OF QUEUE 213: narrowing
  the wait list reduces how long the runner is held for nothing, and this item asks whether it
  need be held at all.
  Not obviously solvable. A job's steps cannot run before the job is scheduled, so a
  pre-flight would have to live somewhere other than this job. Writing down that it cannot be
  done, with the reason, is an acceptable outcome and is better than the current silence.
