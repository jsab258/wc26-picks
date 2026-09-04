line: infrastructure (the Telegram bot)
spec: found by the resident 2026-09-04 running the ruling's own three commands; recorded in section 0 of game-design/decision-2026-09-04-ruling-067-telegram-bot-first-pass.md
acceptance: a planted crash inside a library frame prints the innermost frame that belongs to this project, and still prints no exception message; both halves watched, and the withholding of the message must not regress
max_sessions: 1
status: READY 2026-09-04. instrument-builder, small.

## What the run actually printed

The last-net arm added on 2026-09-04 walks to the innermost traceback frame.
The ruling expected the planted crash to print `telegram-bot.py line 567`.
It printed:

    09:01:57  CRASHED: UnicodeDecodeError at <frozen codecs> line 322.

The line number did not drift; the FILE is different, which the ruling did not
anticipate. A decode error's innermost frame is inside the codecs module.

## Why it matters beyond cosmetics

The same is true of the exception the net was written FOR. The director traced
the one library exception whose message carries the token: `InvalidURL`,
raised inside `http/client.py` by `_validate_path` when a token contains a
space or a tab. Its innermost frame is that library, so a real token-carrying
crash would print `client.py line 1300` and never point at the bot at all.

So the net does its first job, withholding the secret, and does its second
job, saying where to look, poorly. The type name carries most of the value and
`UnicodeDecodeError` was genuinely diagnostic; the location was not.

## The fix

Walk OUTWARD from the innermost frame to the first one whose filename is
inside this repository, and print that; keep the innermost type name. If no
frame belongs to the repo, say so in those words rather than printing a
library path as though it were ours.

DO NOT start printing the exception message as part of this. The withholding
is the whole point of the arm and a fix that reintroduces the message has
undone the net while appearing to improve it.

## Both halves

Accepting: the planted `--send-file` crash prints a `telegram-bot.py` line.
Rejecting: a crash whose frames are all library still prints something honest
and still shows no message. And in every case, `Traceback` must appear zero
times in the output, which is the assertion that must not regress.
