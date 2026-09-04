# tools/runner: TWO DIFFERENT RUNNERS, and the name is the problem

READ THIS FIRST. This project has two things called "the runner" and
confusing them cost a wrong critical path on 2026-09-01:

1. THE CI BUILD AGENT. C:\actions-runner-ledger on Jafar's PC, label
   `ledger-pc`, a GitHub Actions self-hosted runner listening for jobs. It
   is what the numbered .bat files here SET UP. Dispatched remotely, it
   builds, runs the sim, captures stills and commits them back, and it
   needs nothing from Jafar. This is how machine-side work has happened
   since 22 Aug.
2. THE NIGHT LOOP. run-night.bat and run-night.ps1 here, written
   2026-08-31: a local loop launching Claude sessions against
   production/queue/. For continuous autonomous development. NOT required
   for CI work, and not a prerequisite for anything the build agent can do.

If a task says "the runner", it is ambiguous and should be rejected at
spec until it names which one.

The NUMBERED bats and the .txt notes are the v1 Unity build-runner setup for
the self-hosted CI runner (ledger-pc): untouched, still what CI builds run
on. The files below are the v2 OVERNIGHT LOOP, a different machine-sized
thing that happens to share the folder because runner.md names these paths.

# The night runner (ledger-v2/studio-v2/runner.md made concrete)

Written on the container, executed on Jafar's Windows PC. The PowerShell has
never run where it was written (no PowerShell in this container; the verify
footer names that lint NOT CHECKED), so the first Windows run is its
accepting test and should be watched, per rule 5b.

- run-night.bat   one click, manual start
- run-night.ps1   the loop; -Register adds the 23:30 Task Scheduler entry
- dispatch.md     the fixed prompt every worker session receives
- production/STOP kill switch, checked between iterations

To validate on the PC, in this order: queue ONE trivial task, run
run-night.bat, watch the whole iteration; only then -Register the schedule.
The runner never touches main; it works on night/YYYYMMDD and the
integrator merges what passes gates. Escalations (email, dead-man ping)
stay off until wanted, per runner.md.

# The Telegram bot, and THE CANONICAL SPELLING of config.local

Written 2026-09-04 for queue 067, narrowed to five things by Jafar's one-pass
cap. Standard library only, so nothing new enters the licence allowlist.

- `START THE TELEGRAM BOT.bat` at the repo root, the one double-click
- `telegram-bot.py`  the bot, the send path, and an offline selftest
- `botconfig.py`     reads config.local and never says what it found

## THE CANONICAL SPELLING, so that no future session has to guess

`tools/runner/config.local`, on the PC, gitignored, two lines:

    TELEGRAM_TOKEN=<the token BotFather gave you>
    CHAT_ID=<your numeric chat id>

That is what to write in a new one. The reader ACCEPTS MORE THAN THAT on
purpose, because the file was created before anybody wrote a format down:
`TELEGRAM_BOT_TOKEN`, `BOT_TOKEN`, `TOKEN` and `TELEGRAM_CHAT_ID`, `CHAT_ID`,
`CHAT`, case-insensitively, with `=` or `:`, quotes stripped, blank lines and
`#` or `;` comments ignored, a UTF-8 or UTF-16 byte order mark handled, and a
last-resort fallback that recognises the two values by their SHAPE when the
file carries no key names at all. One hardcoded spelling would have been a
coin flip settled only by a failed run on Jafar's PC, and there are no fix
loops before a Monday reset.

Nothing prints it. A failure names the key spellings it looked for and the
COUNT of lines it read, which is a denominator and not a leak, and every line
the bot prints is scrubbed of both values first, because the token travels
inside every API URL and one unscrubbed traceback would burn it.

## What works today, and what is deliberately absent

Works: it starts and keeps running, it answers anything Jafar types, it pushes
a message he did not ask for, and it asks for BOTH budget meters with numeric
quick-replies, writing the reading to `production/logs/telegram-budget.log`,
which is gitignored and therefore cannot travel into a commit.

Not built, and named here so nobody reads their absence as a failure: gallery
images with captions, decision cards whose buttons write into
`production/decision-queue.md`, typed notes and voice memos with local
transcription. Those are the rest of queue 067.

## The send path, for an unprompted push

    python3 tools/runner/telegram-bot.py --send "one line"
    python3 tools/runner/telegram-bot.py --send-file production/outbox/NAME.unprompted.md

Sent as PLAIN TEXT with no parse mode. Telegram's Markdown parser rejects a
message with an unbalanced underscore or bracket in it with an HTTP 400, and a
Blocking item that fails to send because of a punctuation mark is the failure
this channel exists to prevent. Links therefore arrive as visible URLs.

STILL MISSING, and it is queue 067's central rule rather than a detail: the
send path does NOT yet call `tools/producer-check.py` itself. It was outside
the five things this pass was allowed to build. `send()` carries the bot's own
prompts as well as Producer messages, and the prompts fail the register's
shape by construction, so the check is wired on the Producer content class
(`--send-file` from the outbox, later the brief and the Blocking push), not
inside `send()`. Ruled 2026-09-04, section 3 of the ruling named in queue 067.
Until it is wired, the check is still run by hand and forgetting is still
possible.

## What has never run where it was written

Every Telegram call in `telegram-bot.py`. External hosts are blocked from the
build container, so the network half is UNVERIFIABLE UNTIL IT RUNS ON THE PC,
exactly like every .bat here. What did run: `--selftest`, which covers the
config reader and the message arithmetic, and a scripted conversation against
a stand-in for Telegram. The first double-click is the accepting case.
