# Ruling: the walk clip's route, and the process on his PC that never restarted. LAND THE CODE WITH AMENDMENTS, HOLD THE MESSAGE

> **STATUS: LOG, 2026-09-07. NOT CURRENT** once the amended commit lands
> and the bot on his PC restarts onto the code this record is about.
> Director ruling at spawn 2026-09-07T21:57:03Z
> (`.claude/agent-log.tsv` line 343) on the uncommitted tree after
> `7cb06cd6`: 542 changed lines against the 100 threshold, three files plus
> a sidecar, 0 director rows newer than the reference before this one. The
> builder row is line 342, `2026-09-07T21:37:22Z instrument-builder`. NOT
> CURRENT once the amended commit lands; from then the files are the reading
> copies and this is the record of why.

VERDICT: LAND THE CODE WITH AMENDMENTS. HOLD THE MESSAGE AND ITS SIDECAR OUT
OF THIS COMMIT. Two block, two ride the same pass, and one decision about
tonight is made in section 5.

- B1. A sidecar that exists and cannot be OPENED is read as "no sidecar" and
  the message goes out as bare text. `_read` returns None for every OSError
  and `read_media_ref` treats None as the ordinary case. Section 3.
- B2. The message does not land in this commit, for two independent
  reasons. It is about 1108 characters against the 1024 caption cap, so the
  code shipping beside it would refuse it. And the bot on his PC is running
  the code it loaded before the sidecar existed, so that bot would send it as
  bare text and write the receipt that blocks the clip for ever. Section 2.
- A1. No single selftest row would fail if the sweep refused every clip.
  Section 1.
- A2. Three sentences in the message overstate or blur. Section 4.

What was asked and is upheld: the wire is reached in the code (section 1);
a clip that cannot be sent refuses with its size and never degrades to words
(section 3); both-keys, no-key and unknown-key sidecars refuse (section 3);
the rewrite launders nothing I can see (section 4). "Nothing needs you" is
not true tonight as the tree stands, and section 5 says what makes it true.

## 0. What was read, what was not run, and what I was told

No shell, no git, no Windows in this seat. Read whole: `tools/runner/
outbox.py` (2544 lines; the clip branch 748 to 881, `read_media_ref` 463 to
495, `_read` 641 to 647, `_size_refusal` 1074 to 1093, `video_arrival` 1109
to 1125, the sidecar selftest 1985 to 2142); `tools/runner/telegram-bot.py`
`send_video`/`send_animation` 274 to 323, `send_params` 326 to 340,
`sweep_outbox` 862 to 883, `poll_forever` 1091 to 1120, `outbox_pass` 1227
to 1296, `video_pass` 1328 to 1371, the wiring rows 1844 to 1972; `tools/
supervise.py` 40 to 240, 430 to 550, 600 to 800; the message, its sidecar,
`production/d1-probe/ue-walk-verdict.txt` whole; three stills
(`ue-walk_02_after_clear`, `_03_before_blocked`, `_04_after_blocked`);
`production/outbox/README.md`; `production/decision-queue.md`;
`production/NOW.md`; `production/inbox/2026-09-07T0550Z-79313218.md`; all
eight receipts and one of the 312 refusal records under
`production/outbound/`; `START EVERYTHING.bat`; the 16:59:26Z and 20:41:08Z
rulings by section; `tools/producer-check.py` 100 to 130 and 225 to 300.

NOT RUN HERE: `ledger/verify.py`, either selftest (the 86 to 99 and 102 to
104 counts are the resident's), `producer-check.py` on the message, `git
log`. The message's character count is a hand count of the file, line by
line, and is stated as about 1108; the resident prints the exact number
(section 6).

THE STATUS FILE I WAS QUOTED IS NOT IN THIS CHECKOUT. `production/pc-ops/`
holds one file, `scheduled-task-verify.txt` (`8881917 @1788814939`, about
21:02Z). The install workflow copies `game-design/pc-jobs/supervisor-
status.txt` to `production/pc-ops/supervisor-status.txt` (workflow 169 to
171, 259) and no copy is here. The line "telegram-bot uptime 36505s with 0
stops" is the coordinator's reading, used below as reported; it happens to
be the fact that decides section 2, and it cuts against the batch whichever
instant it was read at.

## 1. Question 1: is the wire reached this time

IN THE CODE, YES, BY READING. `Bot.poll_forever` calls `self.sweep_outbox()`
every poll (1113); `sweep_outbox` calls `outbox_pass` at most every 120
seconds (872 to 876); `outbox_pass` builds `video_sender` and passes it as a
keyword to `outbox.sweep` (1263 to 1285); `sweep` picks `video_sender` when
the sidecar names a clip (792), calls it with the full path and the text
(819), and reads the answer through `video_arrival` (832). Nothing types a
command line anywhere on that path. The closure routes `.gif` to
`send_animation` and everything else to `send_video` (1274 to 1275), which
post `sendAnimation` and `sendVideo` respectively (322, 299). Rule 6 is met
in the source.

THE ROWS DO NOT DISCRIMINATE THE COMPOSITION. `accept/ruling1-the-sweep-is-
given-a-video-sender-too` (1883) asserts the keyword is callable. `accept/
ruling1-the-sweeps-own-closure-routes-a-gif-as-well` (1955) calls the
closure by hand with `walk.gif`. Both pass whether or not `sweep` ever calls
the closure. The row that proves the sweep's branch is in outbox.py
(`accept/a-message-naming-a-clip-is-sent-as-one-captioned-clip`, 2023) and
it drives `sweep` with a stub, never through `outbox_pass`. So the pair
proves each half; no row proves the join. A1 (section 6) is the join: one
message with a clip sidecar in a fixture outbox, `outbox_pass` called with
`send_animation` stubbed at module scope, the stub asserted to have received
the fixture's gif path and the text, and the receipt read back as `receipt:
sent-with-clip`. It fails if either half regresses, which is the property
the two existing rows lack.

ON HIS PC, NO, AND NOT BECAUSE OF THIS DIFF. Section 2.

## 2. The process that never restarted, and why the message must wait

THE BOT RUNS THE CODE IT LOADED WHEN IT STARTED. `supervise.py` says so in
its own words (`resync_once`, 442 to 446): "the bot deliberately runs no
git, so it runs whatever code was on disk when it started ... a bot started
from an older checkout cannot send anything, however long it stays up". The
supervisor resyncs the checkout ONCE, before spawning (668), and its loop
restarts a child only on exit (729 to 741). `tools/pc-watcher.py` hard-resets
the checkout every minute, which updates the files on disk and nothing in
memory. Grep of `supervise.py` and `telegram-bot.py` for `mtime`, `reload`,
`__file__` comparisons: nothing that watches the source.

WHEN THE RUNNING BOT STARTED. The reported uptime of 36505 s puts the start
between about 10:54Z (if read at the 21:02Z install run) and 11:49Z (if read
at this spawn). The receipts `2026-09-07T111851Z-reply-22` to `-24` show a
bot instance replying at 11:18Z to 11:19Z, and the 20:41Z ruling records a
console close at about 11:30; a restart at about 11:49Z fits every reading.
Either bound is BEFORE `3c7a88e7` (16:19Z), the reference of the 16:59:26Z
ruling, whose section 6 reviewed the sidecar, `read_photo_ref` and the
`photo_sender` wiring as new in that uncommitted batch. So the bot on his PC
has no sidecar logic at all: not the photo half, not the clip half.

WHAT THAT BOT DOES WITH THE MESSAGE AS COMMITTED. Its sweep reads the `.md`,
runs the CURRENT `producer-check.py` from disk in a subprocess (the register
passes, as the resident says), and calls `sender(text)`. A plain text message
arrives on his phone saying "Fifteen frames of a scripted route" with no
frames, and `receipt: sent` is written. When the bot is finally restarted on
the new code, `receipt_is_valid` reads that receipt and files the message
under `already` (713 to 719). The clip never goes. That is the exact outcome
the resident's question 4 names, and the new code cannot prevent it because
the new code is not the code running.

AND THE NEW CODE WOULD REFUSE IT ANYWAY. The message is about 1108
characters; `CAPTION_CAP` is 1024; the clip branch refuses an over-cap
message rather than truncating it (778 to 791), correctly. The answer
register carries no word cap, so passing the register said nothing about the
caption cap, and the resident measured the message against the rules it
enforces and not against the number its own code enforces. Rule 4: the
artifact was not opened against the instrument that will read it.

RULED: the message and its sidecar are held out of this commit. Section 5
says how the clip gets to him.

## 3. Questions 4 and 5: refusal, never degradation

THE CLIP PATH REFUSES LIKE THE PHOTO PATH, CONFIRMED. `_size_refusal` names a
missing file with its path, a zero-byte file, and an oversized file with its
MEASURED bytes and the limit (1083 to 1093); `video_refusal` is that with
`VIDEO_MAX_BYTES` (1102 to 1106); the sweep writes a refusal record and
`continue`s before any sender is called (804 to 817). No sender wired refuses
(792 to 803). A platform answer with no `video` or `animation` descriptor
writes a HOLD (837 to 847), so a clip filed as a document is neither
receipted nor retried into a duplicate. Selftest rows exist for missing
(2096), oversized (2113), no sender (2082), document (2140). The gif here is
1642282 bytes by the verdict's own `clipBytes`, under both the 8 MB stitcher
ceiling and the 50 MB send ceiling; no `.gitattributes` exists, so the PC's
copy is the file and not a pointer.

BOTH, NEITHER, UNKNOWN: ALL REFUSE. `read_media_ref` returns a reason when
more than one of `photo`/`clip` is populated (486 to 489), when neither is
(490 to 493, which is also the unknown-key case, since an unknown key
populates neither), when the file is empty or has no `key: value` line
(481 to 483). The sweep turns every reason into a refusal record and never
reaches `sender(text)` (748 to 763). Rows: both (2126), no photo line (1993).

THE HOLE, B1. `_read` catches every `OSError` and returns None (641 to 647).
`read_media_ref` reads None as "no sidecar" and returns the ordinary case
(478 to 480). So a sidecar that exists and cannot be opened (a directory of
that name, a permission fault, a file locked mid-write by the watcher's
minute-by-minute hard reset) is indistinguishable from an absent one, and
the message goes out as bare text with a `receipt: sent`. That is the one
direction ruling 5 forbids, in the one function this batch extends. It
predates the batch and the resident asked about it by name; the fix is
three lines and one row (section 6).

A RESIDUAL, FILED AND NOT BLOCKING. `git reset --hard` writes files in index
order; `...answer.md` sorts before `...answer.photo.txt`, so for a moment
during a reset the message exists and its sidecar does not. The sweep reads
the sidecar last, after a subprocess that takes hundreds of milliseconds, so
the window is a stalled reset between two adjacent writes. Named in 7c so
the next reader does not rediscover it.

## 4. Questions 2 and 3: the message against the verdict

Read against `ue-walk-verdict.txt` on `de4ad4d`. Line by line:

- "launches" / "launched cleanly in twelve seconds": `launchStatus=LAUNCHED
  launchExitCode=0 launchWaitSeconds=11.81`. The 11.81 s is the wait until
  the verdict file appeared, which is the whole run, not the launch. "Ran
  start to finish in twelve seconds" is the plain form. A2, optional.
- "the street is whole" / "All 593 pieces": `sceneStatus=WHOLE
  piecesEmitted=593/593 skipped=0`. True.
- "moved 618 cm": `walkCameraDistanceCm=618.2`. True.
- "bright measurement squares ... absent here, none of the three":
  `testCardsSpawned=0/3 testCardsStatus=ABSENT`. True of the frames, and the
  verdict header says the 0 is "by construction on this path". A reading
  that cannot come out otherwise is not one of "five readings taken from the
  measurements". A2: say the squares are not in these frames and were not
  asked for on this route, or drop the sentence.
- "walked 100 cm into a named terrace wall and stopped there":
  `collisionBlockedApproachClearanceCm=150.0 collisionBlockedDistanceCm=100.0
  collisionBlockedWallName=east_parade_bay0`. It started 150 cm from the
  wall, moved 100 cm and stopped, 50 cm short, which is a capsule radius. "100
  cm into a wall" reads as penetration on a literal reading. A2: "walked 100
  cm at a named terrace wall and stopped short of it" or "up to".
- "while the open pavement let it run the full 618 cm":
  `collisionClearDistanceCm=618.2 collisionClearStat=same-measurement-as-
  walkCameraDistanceCm/one-variable`. The sentence reuses the number already
  given and says "the full", so it does not present a second measurement.
  Honest, and one word short of explicit. A2: "the same 618 cm it had already
  covered on the open pavement". Rule 2's "one number twice" is satisfied
  when the reader can see it is the same number, and a non-technical reader
  cannot see that from "the full".
- "the only judgment with a deliberate failure planted beside it": true,
  `collisionStatusNote=needs-both-the-accepting-and-the-planted-case`.
- "first cuts on an instrument that has now run exactly once": the verdict's
  own words (`first-run-of-this-instrument/not-a-tuned-bound`). True.
- "Fifteen frames": `walkSeqFramesWrote=15/16 clipFramesUsed=15`. True; the
  sixteenth was not written and nothing in the message claims it.
- "your PC walked it and judged it on its own": the runner is
  `JAFAR-DESKTOP\Jafar` per the install evidence. True.
- The stills: `_03_before_blocked` shows the pavement with cladding and
  glazing on the right; `_04_after_blocked` shows the camera hard against
  wood cladding, moved right and no further. `_02_after_clear` is the far
  end of the open footway, textured brick and cobbles. The pictures agree
  with the words, and the numbers, not the pictures, are the evidence.

THE REWRITE. I cannot see the refused draft; no refusal record for this
stem exists under `production/outbound/` (the refusal happened in the
container). Read on its own terms, "which is your ruling working" and
"taken from the measurements rather than from whether it went green" are
plain restatements, not laundering. The one claim that a rewrite could have
softened, the collision pair, is treated above.

"NOTHING NEEDS YOU." False tonight as the tree stands: the clip cannot reach
him until the bot on his PC is restarted (section 2). True if the studio
takes the restart itself (section 5). The sentence is written to be true at
the instant the message is sent, or it is removed.

THE QUESTION THIS ANSWERS HAS BEEN OPEN SIXTEEN HOURS. `production/inbox/
2026-09-07T0550Z-79313218.md`: "tell me what the town looks like right now
and whether anything needs me today". The only outbound records since are
three bot replies at 11:18Z to 11:19Z. Rule 13: a question sitting
unanswered is a Blocking gap, not a queue item. That is why section 5 sends
the words tonight through the bot that exists, rather than holding them for
the bot that does not yet.

## 5. Tonight: how the clip reaches him, decided

THE SHAPE: TWO MESSAGES, NOT ONE. Ruling 1's sentence is "the clip goes to
Telegram with a one-line verdict". A 1100-character caption was never its
shape, and the caption cap is the instrument saying so.

1. THE WORDS, NOW. `production/outbox/2026-09-07-the-walk.answer.md`, no
   sidecar, the current text with A2 applied. The bot running on his PC
   sends plain text correctly (eight of eight receipts on the branch are
   that path, `receipt: sent`), so this arrives within about three minutes
   of the push: one watcher reset, one 120 s sweep. It answers his 05:50Z
   question tonight.
2. THE CLIP, AFTER THE RESTART. `production/outbox/2026-09-07-the-walk-
   clip.answer.md` with the existing sidecar, its body ONE LINE, well under
   the cap, for example "The walk, fifteen frames, the wall at the end is
   the one that stopped it." plus the map link, which the answer register's
   link floor requires. It is committed only after the evidence in item 4
   below, because the old bot would send it as text and receipt it.
3. THE RESTART, BY THE STUDIO. Three routes were weighed:
   - a. Two clicks by Jafar (close the LEDGER window, double-click START
     EVERYTHING). Certain and immediate, and it pages him to the floor at
     midnight his time for something the studio can do, against his own
     standing order 2 of 2026-09-05.
   - b. A remote restart: a `workflow_dispatch` job on his runner, as his
     account, that stops the ONE python process whose command line names
     `tools\runner\telegram-bot.py` and lets the supervisor restart it on the
     code on disk (`note_exit` resets the ladder at 36505 s of uptime, wait 5
     s; one exit against a give-up rule of five in thirty minutes). Its
     evidence file carries `botProcessesFound=N` with PIDs, refuses on 0 or
     more than 1, `botOldPid`, `botNewPid`, `waitedSec`, and the copied
     supervisor status. It also runs the supervisor's restart path for real
     for the first time, which its own header says has never happened.
   - c. The bot exits itself when its source changes on disk, and the
     supervisor restarts it. The class fix, and it cannot help tonight
     because the running bot lacks it.
   RULED: b tonight, c filed first in the queue, a only as the fallback the
   Producer writes into the 04:00Z brief if b has not landed with its
   evidence by then. b and c are studio work with their own builder and
   their own ruling; this record dictates their behaviour (7a, 7b) and does
   not cover their diffs.
4. THE EVIDENCE THAT THE NEW CODE RUNS, before item 2 is committed: any ONE
   of `production/pc-ops/supervisor-status.txt` landed with `telegram-
   botStarts=2` or more, or `telegram-botUptimeSec` smaller than the age of
   this batch's commit; or a `receipt: sent-with-photo` or `sent-with-clip`
   on the pc-inbox branch; or the restart job's file with `botNewPid` set.
   A sentence in chat is not one of these.
5. ARM IT. The turn that pushes the restart job arms a one-shot to read its
   evidence file and commit item 2; nothing here ends on "then send the
   clip".

## 6. The amendments, stated as behaviour, and what the resident prints

B1, `tools/runner/outbox.py`, `read_media_ref`, BLOCKS. Absence and
unreadability are told apart: when the sidecar path does not exist
(`os.path.lexists` false) the ordinary case returns; when it exists and
`_read` returns None the function returns a reason naming the path and "it
exists but could not be read", and the sweep refuses on it exactly as it
refuses the other reasons. One row in the outbox selftest, rejecting case:
the sidecar path created as a DIRECTORY (an `OSError` on open on every
platform), the message committed beside it, the sweep run with a text sender
that records calls, asserted zero calls, one refusal, and "could not be
read" in the clause. The accepting case is the existing sidecar rows, which
must stay green.

B2, the outbox, BLOCKS. `2026-09-07-the-walk-clip.answer.md` and its
`.photo.txt` are NOT in this commit. The words go as section 5 item 1 under
a name with no sidecar; the clip goes as item 2 after item 4.

A1, `tools/runner/telegram-bot.py` selftest, rides the pass. The join row of
section 1: a fixture from `outbox._fixture_repo`, the good message committed
with a `clip:` sidecar naming a gif written into the fixture, `send_animation`
replaced at module scope by a recorder returning `{"message_id": N,
"animation": {...}}`, `outbox_pass(_Creds(), fixture, say)` called, then
asserted: the recorder was called once with the fixture's gif path and the
message text, the receipt exists and reads `receipt: sent-with-clip`, and
`done_line` carries `captionedClipsSent=1`. Name it for the fault:
`accept/ruling1-a-clip-message-reaches-sendAnimation-through-outbox_pass`.

A2, the words message, rides the pass. Section 4's five wording points: the
run time, the test-card sentence, "into" to "at ... and stopped short of
it", the 618 made explicitly the same number, and "Nothing needs you" true
at send time or absent. The register is run on the result; the exact
character count is printed beside the register line even though the words
message carries no sidecar, so the number exists in the record.

Before the commit the resident prints:

1. `grep -n "lexists\|could not be read" tools/runner/outbox.py`: B1 at its
   line, and the new row's name in the selftest.
2. `grep -n "through-outbox_pass" tools/runner/telegram-bot.py`: A1.
3. `python3 tools/runner/outbox.py --selftest | tail -3` and the same for
   `telegram-bot.py`: the count lines, both with one more case than the
   resident quoted (100 and 105), exit 0.
4. `python3 -c "print(len(open('production/outbox/2026-09-07-the-walk.answer.md').read().strip()))"`
   and `producer-check.py --kind answer` on it: the number and SEND.
5. `ls production/outbox/ | grep walk`: exactly one file, no sidecar.
6. `python3 ledger/verify.py`, footer FROM `ledger/.verify-footer`; the
   cadence line names this record and row `2026-09-07T21:57:03Z`.
7. The sha, captured BEFORE the push, then the receipt for the words
   message watched for by ancestry on the pc-inbox branch.

## 7. Filed and waiting (names, not work)

a. THE BOT RESTARTS ITSELF WHEN ITS CODE CHANGES, FIRST IN THE QUEUE. At
   import the bot records a digest of every module it loaded from
   `tools/runner/`; once per poll, after `sweep_outbox`, it compares; when
   any differs AND uptime is at least 600 s it prints one line naming the
   changed files and exits with a distinct code so `supervise.py` restarts it
   on the new code. The 600 s gate bounds it to three exits in the
   supervisor's 1800 s window against a give-up rule of five, so the ladder
   is never touched and never loosened. Selftest in the policy layer:
   unchanged, changed at 601 s, changed at 599 s with a printed deferral.
   The same class applies to `pc-watcher.py` and `executor.py`; one item,
   the bot first because it is the channel.
b. THE REMOTE RESTART JOB, section 5 item 3b, dictated there. Its own
   ruling with a's.
c. THE RESET ORDERING WINDOW, section 3. A sidecar that sorts before its
   message, or a message that names its sidecar, closes it; not tonight.
d. THE REFUSAL PILE. 312 records under `production/outbound/` for one file,
   `2026-09-03-batch-landed-and-the-wait.unprompted.md`, because the clause
   carries "-16.2 hour(s)", a number that moves every pass, so the hash that
   was meant to make an unchanged refusal cost one push for ever makes a
   changed one every two minutes. Beside queue 141, which makes the hold a
   named outcome; this is the reason the pile grows meanwhile.
e. THE STATUS COPY. `production/pc-ops/supervisor-status.txt` is written by
   the install workflow only, so the studio's view of the daemons is as old
   as the last install run. The restart job in b copies it too; a's item
   should make the bot's own start count reach the branch.
f. THE ANSWER REGISTER MEASURES NO CAPTION. A message that names an
   attachment is measured against `CAPTION_CAP` only on the sending side.
   `producer-check.py` could read the sidecar beside the file it checks and
   refuse in the container, where the writer can still fix it. Filed, not
   dictated: it widens the register, and the register is Jafar's.

<!--RULING spawn=2026-09-07T21:57:03Z-->
