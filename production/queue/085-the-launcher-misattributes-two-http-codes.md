line: infrastructure (the PC launchers)
spec: game-design/decision-2026-09-04-ruling-067-telegram-bot-first-pass.md, section 7
acceptance: HTTP 403 and HTTP 409 each print their own sentence naming the real cause; proven by two planted responses against the scripted stand-in, plus the five existing failure phrases still printing unchanged
max_sessions: 1
status: READY 2026-09-04. instrument-builder, small. THE LIKELIEST FIRST-RUN FAILURE IS IN HERE, so it outranks its size if the first double-click goes wrong.

## The fault

`START THE TELEGRAM BOT.bat` prints a five-line table mapping the bot's
phrases to causes, and the five phrases match the code exactly. Two real
outcomes fall outside it and get misattributed:

- HTTP 403, which is what Telegram returns when Jafar has NOT pressed Start
  in the chat with his bot. That is the single likeliest failure on a first
  run. It does not match `chat not found` or `chat_id`, so it falls through to
  the generic arm and prints `Telegram said no (HTTP 403: ...)`. The launcher
  table then points him at "refused the chat id", so he goes and checks a chat
  id that is perfectly correct.
- HTTP 409, which is what Telegram returns when TWO copies of the bot poll at
  once. Double-clicking the .bat twice is an obvious thing to do. Same
  misattribution.

Neither is a leak and both are readable, which is why this is a queue item
rather than a stopper. But sending someone to check a correct value is worse
than saying nothing, because it costs them the one thing a failure message is
supposed to save.

## The fix, one clause each

`tools/runner/telegram-bot.py` around line 122, beside the existing chat arm:
403 says he has not pressed Start in the chat and names that as the fix; 409
says another copy of the bot is already running and to close the other window.
Then the launcher's table gains the two phrases, and the phrases must stay
mutually distinguishable at a glance.

## On "no overlapping words"

The ruling notes that claim, made in the builder's report and repeated by me,
is literally false: the five phrases share ordinary words. What is true, and
what should be preserved, is that no two of them share their DISTINGUISHING
phrase. State it that way in future rather than as an absolute.
