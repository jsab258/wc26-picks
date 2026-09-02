line: infrastructure (content pipeline)
spec: game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md, Ruling 4 and Ruling 8
acceptance: a STATE "running" entry written at job START, stale by that job's own JOB_TIMEOUT, both outcomes fixtured; a probe-the-vignette-library TABLE row with its own JOB_TIMEOUT and ambientcg-types.json in publish's named list; the spec's C10 sentences reconciled to say one thing
max_sessions: 1
status: READY 2026-09-02. One engine-specialist. Item 1 matters the first time Jafar double-clicks while a window is already open.

1. TWO WATCHERS. The refusal of a naive lock file is ENDORSED for the reason
   the builder gave: a crashed window leaves a stale lock and the machine then
   never starts again, which is worse than the problem. The ABSENCE OF ANY
   GUARD is OVERRULED. What exists today is an `index.lock` back-off, and
   because `STATE` is written only when a job ENDS, a second watcher polling
   during an eight-hour batch reads the request as not done and runs the same
   batch again, on the same card, with no git running to trip the back-off.

   The shape with both properties reuses what is there: `STATE` gains a
   `running` entry at job START carrying the request id, the job name and a
   start time. A second watcher seeing a `running` entry YOUNGER than that
   job's `JOB_TIMEOUT` skips the request and prints why, once. An entry older
   than the timeout is stale by the same bound that would have killed the job,
   is ignored, and the line says so. Both outcomes fixtured.

2. THE PROBE ROW. `fetch_vignette.py --probe` answers the two ABSENT lines and
   puts fifteen shutter previews in front of Jafar, which is the quality
   ladder's next rung for the fetch route. It needs a TABLE row, a
   `JOB_TIMEOUT` entry, and `tools/props/ambientcg-types.json` added to
   `publish`'s named list so the answer travels.

3. THE SPEC CONTRADICTS ITSELF ON C10. One sentence says the shutter pick was
   deferred to a probe; the `assets` list names CorrugatedSteel002 at 4K, and
   the code follows the list. Tonight's fetch therefore puts a placeholder
   shutter on disk under a logical name. Reconcile the two sentences so the
   file says one thing, and make sure nobody finds that file later and calls
   the pick made.
