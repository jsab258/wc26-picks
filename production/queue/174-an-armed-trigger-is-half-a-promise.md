line: instrument (the studio's own wake path)
spec: Something checks that a fired trigger's WORK happened, not only that its wake
  was delivered. The smallest form: a trigger whose prompt names an artifact it must
  produce, and a later check that reads for that artifact and says nothing measured
  when it is absent.
acceptance: a wake that fires into a busy session and is absorbed is DETECTED rather
  than reported as SUCCEEDED, and the detection names what was not produced
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09, filed from a live instance the same morning.
  THE INSTANCE: trig_01Lb3XS3RcsAEDTgTfXpwmma fired at 2026-09-09T04:00:57Z with
  last_run.status ROUTINE_RUN_STATUS_SUCCEEDED and ended_reason run_once_fired. The
  turn never arrived, because the session was mid-turn and the wake was absorbed;
  ReadNotifications returned "No queued notifications" fourteen minutes later. Jafar's
  morning brief was not written until the resident noticed the clock.
  THE SHAPE, and it is one this project already has a rule for on another surface:
  .claude/rules/ci.md says verify a job's EFFECTS and not its exit code, because jobs
  have reported success while deleting content and pushing nothing. SUCCEEDED on a
  trigger means the wake was DELIVERED. It does not mean the work happened. Two facts,
  one word.
  AND IT UNDERCUTS CLAUDE.md RULE 8. "I will come back to you requires arming
  something" has been read here as discharged by the arming. It is the first half. The
  second half is a check that what the trigger was for exists, and nothing in this
  project performs it, so every armed resume carries this hole.
  ONE THING THE FIX MUST NOT DO: fire a second trigger to check the first. That is a
  watcher needing a watcher. The cheap shape is an artifact the next session can read,
  not another wake.
