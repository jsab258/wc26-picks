line: infrastructure (the Producer loop, inbound)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 1, inbound clause
acceptance: one real message sent from his phone lands as a dated file on a committed branch and is read back in the container, printing inboundLatencySec from the Telegram message timestamp to the commit instant; a message from a chat that is not the configured one writes NO file and raises the existing ignored counter; a failed push leaves the message on disk and reports inboxPending=N rather than dropping it; the reader prints delivered=N/M seen and the words "nothing measured" when no message has ever arrived; and `python3 tools/pc-watcher.py --once` still completes a full pass afterwards
max_sessions: 1
status: READY 2026-09-05. FIRST of item 1, and the other five wait on its transport. instrument-builder, finished on the PC.

## Read this before designing anything, because the mechanism already exists

Measured by reading `tools/pc-watcher.py` on 2026-09-05, not from a README.

- It runs on Jafar's PC as a polling loop, default 60 seconds, floor 10
  (`main`, the `--seconds` argument and the `time.sleep(max(10, ...))`).
- Every pass does `git fetch -q origin claude/game-dev-ai-automation-2h67ix`
  then `git reset --hard <that sha>` (`resync`). Untracked files survive that
  reset. Tracked ones do not.
- Results travel back on ONE branch, `pc-results`, force-pushed by `publish`,
  which stages a NAMED list of paths, commits, pushes, then re-fetches and
  compares shas so a push that sent nothing is caught.
- `deliver_before_discard` runs BEFORE the reset: if the local HEAD is a commit
  on neither the work branch nor `pc-results`, it force-pushes it to
  `pc-results`, and IF THAT PUSH FAILS THE WHOLE PASS STOPS and retries next
  minute. So anything else that commits inside that clone can wedge the job
  channel.

Two consequences that decide the design:

1. THE INBOX MUST NOT RIDE ON `pc-results`. Its tip is rewritten from a tree
   that is the work branch plus the named produced paths, so any file that got
   there by another route and is not in that list disappears at the next job.
2. THE BOT MUST NOT COMMIT IN THE WATCHER'S CLONE, for the wedge above.

The route is therefore a single-writer branch of its own, pushed either from a
second clone or through a temp index, and the file must say WHICH was chosen
and why. Whichever it is, no interactive git, no editor, no credential prompt
(`tools/lint-bat-editor.py` is the standing guard, and the 26 August incident
is the precedent).

## The half that does not work, said plainly

Nothing on that PC can call into this container. The container has outbound
HTTPS through a proxy and no inbound anything. A turn in this session begins
only when a trigger fires or when Jafar types. The live trigger is
`trig_013itgDeay6t41BHEmaYFbAj`, daily at 04:00 UTC; the hourly watchdog
`trig_01EA7ybQTcsiFyrTryptqVUi` is disabled.

SO THE TRANSPORT DELIVERS IN ABOUT A MINUTE AND THE WAKE DOES NOT. While the
studio is asleep, worst case is the next daily trigger, up to 24 hours. That is
the finding, and no wording in this file may soften it.

Three routes to close it, none of them a builder's choice to make alone:

- **A, poll while awake.** The session fetches the inbox branch at the top of
  every turn and at every dispatch boundary. Costs one git fetch. Delivers in
  minutes while the studio is working and never while it sleeps. BUILD THIS
  ONE NOW; it is the half that is free.
- **B, a recurring trigger every few minutes.** Every firing with
  `persist_session` delivers a user turn and costs a cache read of the whole
  conversation plus output. That per-firing cost is UNMEASURED: NOW.md's "about
  76 firings against 3 points of headroom" is a judgement, not a measurement.
  Nothing faster than the daily trigger gets armed until one firing has been
  measured (queue 076 is the rate that would allow it).
- **C, the PC starts a session itself.** `tools/runner/run-night.ps1` already
  runs `claude -p` on that machine, so the CLI is there and a message could
  start a FRESH session within a minute. It does not reach this conversation
  and it spends his points per message. Whether a fresh session may answer him
  is Jafar's call.

## What to build

The bot writes each message from the configured chat as
`production/inbox/<YYYY-MM-DD>T<HHMM>Z-<update_id>.md` carrying the text, the
Telegram `date` as an ISO instant, and NOTHING ELSE: no token, no chat id, no
config path, per the credential rule ruled 2026-09-04.

It pushes to the inbox branch, verifies the effect by re-fetch rather than by
exit code, and keeps unsent files on disk with a count when the push fails.

It replies with one line saying the message is filed and whether the studio is
awake or asleep, so silence is never ambiguous. Until queue 094 lands, awake or
asleep is read from the newest commit time on the work branch, and the line
says which.

The container side is a reader that prints the pending messages, the counts and
the latency, and is called at every dispatch boundary. Built is not running:
name the call site.

## Both halves, accepting first

Accepting: one message really sent from his phone, on the PC, appears on the
branch and is printed by the reader with `inboundLatencySec=<n>` measured from
the message's own timestamp to the commit instant. Not a selftest.

Rejecting, three cases: a message from another chat writes NO file; an
unreachable remote leaves `inboxPending=N` and loses nothing; and a reader run
against a branch with no messages prints the words "nothing measured" with
`delivered=0/0`. Then `python3 tools/pc-watcher.py --once` completes a pass, so
the job channel is proven unwedged.

## Depends on, and what it blocks

Depends on queue 067 (the bot exists and runs on the PC, first pass landed).
Blocks queue 082 (his tapped readings need this transport), 089, 090, 091 and
093. Not blocked by anything.

## MEASURED BY THE RESIDENT 2026-09-05: ONE MORE ROUTE EXISTED, AND IT IS SHUT

A fourth route existed that this file did not name, and it looked like the
whole answer: this session can mint an INBOUND WEBHOOK whose documented
behaviour is that a POST delivers the body into the conversation AND WAKES THE
SESSION IF IDLE. That is exactly the mechanism the wake half needs, and it
would have turned "up to 24 hours asleep" into seconds.

IT IS CLOSED, and this is measured rather than reasoned. A webhook was minted,
and the POST a bot on the PC would make was sent to it:

    POST <the fire url>, Content-Type: application/json, no signature
    http_status=401
    body: unauthorized

The credential it hands back is SEALED to one named service and cannot be
opened by anything else, so no bot, script or curl on Jafar's PC can sign a
delivery. The webhook was removed again rather than left live, because an open
inbound capability nothing can use is a liability with no upside.

WHAT THIS SETTLES. The three routes already in this file are the whole field,
and the honest position stands: the transport half is a minute, the WAKE half
is not solvable in minutes today without either arming a recurring trigger
whose per-firing cost is unmeasured (queue 076 is that measurement) or letting
the PC start a fresh session that does not reach this conversation. Do not
spend another pass looking for a fifth route; this is the one that looked most
promising and it answers 401.
