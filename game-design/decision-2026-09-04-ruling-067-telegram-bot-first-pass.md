# Ruling: queue 067 first pass, the Telegram bot, one builder, one review

> **STATUS: LOG, 2026-09-04.** Director ruling on the one-builder batch
> pending in the tree at spawn 2026-09-04T08:45:21Z: `START THE TELEGRAM
> BOT.bat`, `tools/runner/telegram-bot.py`, `tools/runner/botconfig.py`,
> `tools/runner/README.md`, nothing committed. NOT CURRENT once the batch is
> committed; from then the committed files, `production/NOW.md` and the queue
> items named in section 9 are the reading copies and this is their history.
Reviewed by reading past the ceiling (total 82, Fable 83, ceiling 80, Jafar's
own 20 percent, his cap: 6 points, no fix loops before Monday). Section 0
says what was and was not measured.

VERDICT: APPROVE, CONDITIONAL. Land as one commit WITH the dictated net in
section 8.1 applied verbatim and its three printed runs appended to section 0
by the resident before the commit. If the net is not applied, the ruling is
REJECT and what comes out is the whole batch, all four files: a bot with a
known unscrubbed path to stderr does not sit on the PC beside the token. The
net is dictated text and costs no builder pass. Nothing else in this ruling
is ordered before Monday; everything else is a queue item with a name.

## 0. What was measured, and by whom

This spawn ran nothing: it has no shell. Every count below is by reading.
`tools/runner/config.local` was not opened, globbed or grepped; it is not in
this container and the review did not look for it.

Counted by reading: 33 `OUT.say` sites in `telegram-bot.py`; 13 bare
`print` sites across the two files, of which 1 is the printer inside
`Console.say` and 12 are selftest or usage text reachable only with synthetic
secrets (the selftest asserts it never opened the real file); 0 uses of
`logging`, 0 writes to `sys.stderr`, 0 uses of `traceback`; 6 `raise` sites
in `call()`, 1 bare re-raise in `skip_backlog`, all carrying composed messages
with no URL; 29 selftest check sites, 17 in `telegram-bot.py` and 12 in
`botconfig.py`, each traced by hand against the code it exercises; 5 `:trypy`
blocks across 5 launchers, the 6 executable lines identical in all 5; 10
budget readings in this week's printed series, 1 on a button of the proposed
grid; 1 ban-list hit in the 7 fixed Telegram strings (the word `repo` in the
budget read-back, the `run internals` rule); 0 invocations of `--send` or
`--send-file` anywhere in the repo outside the two files' own usage lines
(grep over the whole tree, 6 hits, all usage text or the flag parser).

Read in the standard library, not the builder's comments: `http.client`
`_validate_path` at `/usr/lib/python3.12/http/client.py` lines 1296 to 1302,
identical in 3.10, 3.11 and 3.13, raises `InvalidURL` with `{url!r}` in its
message, and the `url` there is the request selector, which for this bot is
`/bot<token>/<method>`.

RESIDENT APPENDS HERE, before the commit, the printed output of the three
runs in section 8.1, verbatim, including the exit codes. Until they are here
the condition in the verdict is not met.

APPENDED BY THE RESIDENT 2026-09-04, three runs, rejecting case watched FIRST.

Run 1, the plant. `printf '\xff' > production/scratch/not-utf8.bin` then
`--send-file` on it:

    09:01:57  CRASHED: UnicodeDecodeError at <frozen codecs> line 322. The message is withheld in case it carries the token. Send Claude this line as it is.
    exit=1

and a second run of the same command piped to `grep -c Traceback` printed `0`.
So the net fires, the interpreter's traceback never reaches the screen, and no
exception message is shown.

ONE DEVIATION FROM THIS RULING'S EXPECTATION, reported rather than smoothed
over. Section 8.1 expected `telegram-bot.py line 567`. The net walks to the
INNERMOST frame, and for a decode error that frame is inside the codecs
module, so it printed `<frozen codecs> line 322`. The line number did not
move; the FILE is different, which this ruling did not anticipate.

It matters more than a cosmetic slip, because the same is true of the case
that motivated the net: `http.client.InvalidURL` is raised inside
`http/client.py`, so a real token-carrying crash would print that library's
path too, never the bot's. The net therefore does its FIRST job, which is to
withhold the secret, and does its SECOND job, which is to say where to look,
poorly: it names the library that raised rather than the bot line that called.
The type name is still the useful half and `UnicodeDecodeError` is diagnostic.
NOT FIXED HERE, because Jafar's cap forbids another pass before Monday and
changing dictated text is not the resident's call. Filed as queue 086.

Run 2, accepting, `--selftest`:

    botconfig selftest: 12 passed, 0 failed (12 case(s) run: 8 accepting, 4 rejecting; fixtures under /tmp/botconfig-selftest-bchnaqc5, the real config.local was never opened)
    exit=0

no `CRASHED` line, and the tally states in its own words that the real
`config.local` was never opened.

Run 3, accepting, `--send hi`, proving the net did not swallow the case the
ConfigError arm owns:

    09:02:14  CANNOT START: config.local not found at /home/user/wc26-picks/tools/runner/config.local
    09:02:14  The file is tools\runner\config.local on this PC. It wants two lines:
    09:02:14      TELEGRAM_TOKEN=<the token BotFather gave you>
    09:02:14      CHAT_ID=<your numeric chat id>
    09:02:14  Nothing here has printed or will print what is in it.
    exit=1

no `CRASHED` line. Both outcomes of the net are therefore watched: it fires on
the planted crash and stays silent on the two cases that are not crashes.

## 1. The credential rule: does the scrubber claim survive the code

The claim was "one scrubber on every printed line, and the token rides inside
every API URL so an unscrubbed traceback is the real leak path."

The second half is true and the builder acted on it: `call()` never puts the
URL into a message. Its six raises carry `type(e).__name__`, an HTTP code, or
Telegram's own description. `HTTPError`, `URLError`, `socket.timeout`,
`socket.error` and `OSError` are all caught and converted. `--send-file`
prints the path and the character count, never the body. `log_budget` writes
numbers only. `banner()` prints the route the value came by (`key/CHAT_ID`,
`shape/bare-line`), never the value. The chat id comparison in `handle()`
prints neither side. Every line the BOT prints does pass `redact`.

The first half is false of one path, and the resident found the same path
independently: the `__main__` block catches `KeyboardInterrupt` and nothing
else, so any exception that is not `ApiError` reaches the interpreter, whose
default excepthook prints a traceback to stderr. That printer is not
`Console.say` and nothing scrubs it. A default traceback shows source text,
not local values, so the token reaches it only through an exception MESSAGE
that embeds the URL. There is exactly one such message in the code the bot
calls, and it is not hypothetical: `http.client.InvalidURL`, raised by
`_validate_path` when the request path contains any character in
`[\x00-\x20\x7f]`. `putrequest` runs it on every request, it is an
`HTTPException` and not an `OSError`, so neither of `call()`'s except arms
sees it, and its message quotes `/bot<token>/getMe` whole. The trigger is a
token value with an internal space or tab. `botconfig.parse` strips both ends
of the value and never the middle, and the `key/` route does not shape-check
the value, so a paste that wrapped mid-token reaches the wire as pasted.
Narrow, real, and the token comes out of it minus one space.

One correction to the resident's reading (rule 3, the instrument): the
selftest string `HTTP Error 401 for https://api.telegram.org/bot.../getMe`
is a fixture the builder typed, not an observed urllib form. `HTTPError.__str__`
is `HTTP Error 401: Unauthorized` with no URL. The URL-carrying form that
exists in the library is `InvalidURL` above, and it is the one the net must
cover.

Why the net withholds the message rather than scrubbing it: `InvalidURL`
formats the path with `!r`. A space survives repr, so an exact-match scrub
would catch it; a tab becomes the two characters backslash and `t`, so
`redact` would miss it and the token would print with one character changed.
The type name and the innermost file and line are enough to diagnose from,
so the message is withheld outright. That is section 8.1.

RULING: the scrubber claim does not survive as stated; the exposure is one
narrow path; the net closes it with dictated text; the batch lands only with
the net. Everything else in this section is evidence that the builder took
the rule seriously, and it is recorded so nobody reads the reject-condition
as a verdict on the work.

## 2. The budget reading lands only on the PC

The bot writes `budgetTotalPct=.. budgetFablePct=.. governing=..
governingPct=.. ceilingPct=80 headroomPct=..` to
`production/logs/telegram-budget.log`, which `.gitignore` line 96 ignores,
and echoes the same numbers to Jafar's chat.

RULING: acceptable for this weekend, and the item cannot close on it. The
weekend's reading has almost no information value (the meters are known to
be 82 and 83 and reset Monday); its value is proof that the two-question
capture works end to end, which the accepting run on the PC establishes
whether or not the file travels. Making the file non-ignored would not have
made it reach a session either: a file on Jafar's disk needs a push, and the
one lesson this repo has about git inside a launcher (26 Aug, an editor that
nobody was watching) means the push path is a design, not a flag flip. So
un-ignoring now buys nothing and costs a decision made in a hurry.

Constraints for the Monday item, written here so the builder does not
rediscover them: the self-hosted runner checks out its own copy under
`C:\actions-runner-ledger`, not Jafar's checkout, so a runner job cannot read
the log by relative path; any git call the bot makes must be one that cannot
open an editor; the log line is already `key=value` with no spaces, so the
consumer is a grep; and the line should gain `source=button` or
`source=typed` (inferable: the text equals a button label or it does not),
because that is the series section 6 needs.

## 3. The send path does not call producer-check

The 3 September ruling, in the Producer's brief lines 88 to 90 and 137 to
139, says the bot "becomes the send path and calls the check itself" the day
it lands. 067 repeats it as the one rule that makes the bot the channel.

RULING: not a violation of the ruling's substance, a deviation from its
letter, recorded here so it is a decision and not a drift. The substance is
that no Producer message reaches Jafar unchecked. This weekend no Producer
message goes through the bot: there are 0 invocations of `--send` or
`--send-file` in the repo, the Producer's messages still go outbox, resident,
by-hand check, and the commit gate still refuses an outbox file that fails
the register. A human at a keyboard could type `--send-file` on an unchecked
file; the same human could read the file aloud today. The gap is unchanged in
size, not opened. The item cannot close without the wiring.

Two things the Monday item must settle, because the README's sentence "wiring
the check in is a one-place change" in `send()` is wrong and a builder will
follow it:

- `send()` carries the bot's own prompts (`BUDGET_Q`, `HELP`, `OPENING`, the
  echo) as well as Producer messages, and the prompts fail the register's
  shape by construction. The check belongs on the content class that IS a
  Producer message: `--send-file` from the outbox today, the brief and the
  Blocking push when they exist. Wire it there, and grep the check's done
  line for `rulesEnforced=` (3 September, amendment 1).
- Whether the bot's fixed strings are Producer voice or console chrome. Read
  against the ban list, they carry one hit: `repo` in the budget read-back.
  Option (a): chrome, exempt from the register like the dashboard's labels,
  reviewed once for tone at commit. Option (b): Producer voice, written by
  that role and checked once by a fixture at commit. Recommendation: (a),
  with the one word fixed when the string is next touched; a bot that says
  "2 of 2: the FABLE meter" is a form, not a report. This touches the
  register, so it is Jafar's call on Monday, not this spawn's.

Also for Monday: `producer-check.py` and `capsay.py` must run on the PC. By
reading, `producer-check.py` imports the standard library only; `capsay.py`
was not read and the Monday builder checks it.

## 4. The scope cut, and the item stays open

067 has six acceptance clauses. What was built: the launcher, the config
reader, the loop, a two-way message, an unprompted push, and the budget ask
with buttons for both meters. Against the six: clause 1 (a Blocking item
pushed within a minute of routing) is not built, only the `--send` a human
would use to do it; clause 2 (morning brief) not built; 3 (gallery) not
built; 4 (decision cards writing rulings) not built; 5 (budget) half built,
since "at most twice a day and only when the next batch would approach the
ceiling" is not there and the bot asks on every start; 6 (notes and voice)
not built. And by the item's own words, nothing is proven until the double
click on the PC, so even the built half stands UNRUN today.

RULING: the cut was right and the item stays OPEN. The substrate had to come
first because every clause stacks on it and the credential rule had to be got
right before anything else was allowed near the file. 067's own status line
is now stale against NOW.md (it still says do not touch before Monday 14:00
CEST; Jafar overrode that at about 08:30Z and NOW.md records it). Section
8.2 dictates the replacement line. The acceptance line is not edited.

## 5. The fifth `:trypy`

Correcting the premise first: `tools/lint-bootstrap-single.py` objects to
inline copies of the self-hosted PATH bootstrap in workflow YAML. It does not
know `:trypy` exists, and it will not go red on this batch. The reason it
exists is the argument, not the lint: one idea, several implementations, and
the copy nobody looks at is the one missing a line. Checked: the six
executable lines are identical in all five copies today, so there is no drift
yet, only a count of five.

RULING: convention-matching was the right call mid-pass under a no-fix-loop
cap; the debt is filed, section 9, item 084: extract to
`tools/runner/find-python.cmd`, every launcher calls it, and a lint of the
same two-sided shape as bootstrap-single (every launcher calls it, no
launcher inlines it). Small. Not before Monday.

## 6. The button span

`0 5 10 20 / 30 40 50 60 / 70 75 80 85 / 90 95 100`, chosen for a first run
near zero. The first click is third in Monday's order, after two items have
spent, so the first reading will not be near zero either. The printed series
this week (`production/budget.md` and NOW.md): 34 and 41 on 1 September, 38,
32, 52, 60, 77 and 76 at 00:30Z on the 4th, 82 and 83 at 08:30Z. One of ten
lands on a button. The meter reports integers; a 5-step grid catches a fifth
of them at best, and near the ceiling a 5-point rounding turns 82 into
"exactly on" or "5 over", which are different decisions.

RULING: plausible, not measured, and no change now. The honest input near the
ceiling is the typed integer, which the parser accepts, and the placeholder
already says so; the grid's job is to make the far-from-ceiling answer one
tap. The real value of this half of the batch is the structure (two meters,
governing, headroom, one greppable line), not the buttons. The bot's own log
becomes the series once `source=` is in it (section 2), and the grid is
reconsidered after a week of readings, not before.

## 7. The failure messages, the selftest, and the bug

The five phrases the launcher names are exactly the five the code produces:
`config.local not found`, `no key matching`, `refused the token`, `refused
the chat id`, `Could not reach Telegram`. "No overlapping words" is false
literally (`token`, `config.local`, `refused` recur) and true of the phrases a
reader is told to look for. RULING: distinguishable by a non-technical reader
at the window, because the launcher translates each phrase into one plain
sentence and tells him to send the line as it is.

Two messages the launcher's list does not cover, both readable on their own
because they carry Telegram's wording, both queue 085: the most likely
first-run failure, Jafar not having pressed Start, arrives from `sendMessage`
as HTTP 403 `Forbidden: bot can't initiate conversation with a user`, which
`call()` maps to `telegram` and prints as `Telegram said no`, while the
launcher attributes that situation to `refused the chat id`; and a second
double-click gets HTTP 409 from `getUpdates` and stops with `Telegram said
no (HTTP 409: Conflict ...)`. Mapping 403 to the `chat` kind is one clause on
line 122. Not a leak, not blocking, not before Monday. The 403 and 409
wordings are from knowledge of the Bot API, not from a run here; Monday's
click is the measurement.

Selftest: 29 check sites counted and traced, 17 plus 12; every expected
string follows from the code as written. The bare-token bug is real and the
fix is belt and braces: `TOKEN_SHAPE.match(line)` catches it, and so would
`not KEY_NAME.match(key)` alone, since the key part would start with a digit.
One imprecision, no action: the `leak2.local` fixture's comment says its
values are shaped like neither, but `-tail` is inside the token character
class, so that value is accepted as a token and the failure path exercised is
the chat id one. The assertion (nothing from the file in the message) still
holds over the same `_missing` function.

The claim of 29 passing is the builder's; this spawn could not run it. The
resident's `--selftest` run in section 8.1 is the measurement.

## 8. Dictated edits, applied in the same commit

8.1 `tools/runner/telegram-bot.py`, two hunks, one file.

(i) The `__main__` block at the end of the file becomes, exactly:

    if __name__ == "__main__":
        try:
            sys.exit(main(sys.argv))
        except KeyboardInterrupt:
            OUT.say("stopped from the keyboard")
            sys.exit(0)
        except Exception as e:                                    # noqa: BLE001
            # THE LAST NET, ruled 2026-09-04. Without this arm an unexpected
            # exception prints the interpreter's own traceback to stderr, and
            # that printer is not Console.say. http.client.InvalidURL quotes
            # the whole request path, token included, when the token carries
            # a space or a tab; repr escapes a tab, so an exact-match scrub of
            # that message could miss it. The message is therefore withheld:
            # the type and the line are enough to diagnose from.
            tb = e.__traceback__
            while tb.tb_next is not None:
                tb = tb.tb_next
            OUT.say("CRASHED: %s at %s line %d. The message is withheld in "
                    "case it carries the token. Send Claude this line as it "
                    "is." % (type(e).__name__,
                             os.path.basename(tb.tb_frame.f_code.co_filename),
                             tb.tb_lineno))
            sys.exit(1)

(ii) In the module docstring, the two lines

    EXIT CODES. 0 stopped cleanly. 1 it could not start, and the window says why.
    3 selftest failed.

become these two lines, so that no line number below them moves:

    EXIT CODES. 0 stopped cleanly. 1 it could not start or it crashed; the window
    says which. 3 selftest failed.

Then three runs, no network needed, output pasted into section 0. The net
must be watched both ways (rule 5b): planted first, then the two accepting
cases.

    mkdir -p production/scratch
    printf '\xff' > production/scratch/not-utf8.bin
    python3 tools/runner/telegram-bot.py --send-file production/scratch/not-utf8.bin; echo exit=$?

Expected: one timestamped line beginning `CRASHED: UnicodeDecodeError at
telegram-bot.py line 567` (567 is the line of `body = fh.read().strip()` as
the file stands; if it moved, the printed number is that line's new number),
`exit=1`, and the word `Traceback` nowhere in the output.
`UnicodeDecodeError` is a `ValueError`, not an `OSError`, so the
`--send-file` arm does not catch it; that is the plant, and it happens before
any config is read.

    python3 tools/runner/telegram-bot.py --selftest; echo exit=$?

Expected: both tally lines, `exit=0`, no `CRASHED` line.

    python3 tools/runner/telegram-bot.py --send hi; echo exit=$?

Expected: `CANNOT START: config.local not found at ...`, `exit=1`, no
`CRASHED` line: the ConfigError arm still owns its case and the net did not
swallow it.

8.2 `production/queue/067-telegram-bot-on-the-pc.md`, the `status:` line
replaced by this one line:

    status: OPEN, FIRST PASS BUILT 2026-09-04 AND UNRUN. Jafar overrode the Monday order at about 08:30Z and spent past the ceiling on this item alone (NOW.md). Landed: the launcher, the config reader, the loop, two-way messages, an unprompted push, the budget ask for both meters. Proven: nothing until the first double-click on the PC, which is the accepting run and the stop point if it fails. Not built, queued by name: the reading reaching the repo (082), the send path calling producer-check (083), and clauses 1 to 4 and 6 of the acceptance line. Ruling: game-design/decision-2026-09-04-ruling-067-telegram-bot-first-pass.md. tools/runner/config.local is read by the bot at runtime and by nothing else; never print, echo, cat, grep for a value, commit or quote it.

8.3 `tools/runner/README.md`, in the STILL MISSING paragraph, the sentence

    `send()` in `telegram-bot.py` is the single choke point every outgoing
    message goes through, so wiring the check in is a one-place change.

is replaced by

    `send()` carries the bot's own prompts as well as Producer messages, and
    the prompts fail the register's shape by construction, so the check is
    wired on the Producer content class (`--send-file` from the outbox, later
    the brief and the Blocking push), not inside `send()`. Ruled 2026-09-04,
    section 3 of the ruling named in queue 067.

## 9. Queue items the resident files

Numbers suggested; 082 to 085 were free at 08:45Z, and the 077 collision says
renumber rather than argue.

- 082 telegram-bot: the budget reading reaches the repo by itself, with the
  section 2 constraints and the `source=button|typed` field. Small to medium;
  the push path is the design work.
- 083 telegram-bot: the send path calls producer-check on the Producer
  content class, greps `rulesEnforced=`, and the chrome-or-voice question for
  the bot's fixed strings goes to Jafar as a decision card. Small once the
  decision is made.
- 084 launchers: one `:trypy`, in `tools/runner/find-python.cmd`, five
  callers, and a two-sided lint. Small.
- 085 telegram-bot: HTTP 403 maps to the `chat` kind, 409 gets its own
  sentence, and the launcher's list gains both. One clause and two lines.

The remaining 067 clauses stay in 067; they are its acceptance, not new
items.

## 10. Quality ladder at close

First working, not best available, and it is not even first running until
Monday's click. The next rungs are named above. The rung that matters most
for the studio is 082, because a reading no session can read is the thing
this week was blocked on, and the bot as built moves it from Jafar's memory
to Jafar's disk, which is one step and not the last.

<!--RULING spawn=2026-09-04T08:45:21Z-->
