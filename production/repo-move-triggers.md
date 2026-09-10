# The scheduled triggers, recorded so a fresh session on `ledger` can re-arm them

STATUS: LIVE, verified 2026-09-10. Written for the move to the new repository,
ruled by Jafar 2026-09-10. It supersedes `production/watchdog-prompt.md` on the
question of WHICH TRIGGER IS LIVE: that file is dated 2026-09-01 and describes
the hourly watchdog, which has been disabled since 2026-09-04.

WHY THIS FILE EXISTS. A trigger's prompt lives in the scheduling system, not in
the repository, so nothing inside the tree can prove what the studio is actually
told to do each morning. When this session's triggers are disabled and a new
session starts on `ledger`, the prompt is gone unless it was written down first.

## The state at the move, read from the scheduler on 2026-09-10

    trig_013itgDeay6t41BHEmaYFbAj  ENABLED   0 4 * * *    the daily wake
    trig_01EA7ybQTcsiFyrTryptqVUi  disabled  20 * * * *   the hourly watchdog
    trig_01JGZTaSpb7zpiASUkc48FoF  disabled  47 * * * *   the continuous build loop

All three bind to the session persisted as `session_01GmRn6ayehpVYDAoQE5DKQo`
in environment `env_01M7wbbwy1jF9xW6jR7e4MkR`. A fourth trigger on the account
belongs to another project entirely and is not ours; leave it alone.

ONE IS ENABLED. The other two are kept here as history because their prompts
carry rulings that are still binding, not because they should be revived. The
continuous build loop in particular was stopped by Jafar on 5 August and its
prompt names an agent identity that no longer applies; do not re-arm it.

## WHAT MUST CHANGE BEFORE RE-ARMING ON `ledger`

Four things, and all four are wrong by construction if the prompt is copied
across unedited:

1. THE BRANCH. The prompt says "push only to
   `claude/game-dev-ai-automation-2h67ix`". On the new repository that branch
   becomes `main`. A prompt that names the old branch will either push nowhere
   or, worse, push to a branch that still exists in the archive.
2. THE SESSION. `persistent_session_id` names this session. A new trigger must
   bind to the new session, or fire into a session that is no longer working.
3. THE ARCHIVE SENTENCE. Add one: the old repository is the archive, every
   commit identifier written in a decision record before 2026-09-10 resolves
   THERE and not here, because moving the large files through history rewrote
   every identifier.
4. THE FOUR BRANCHES. `art/atlas-01`, `pc-inbox` and `pc-results` are carried
   across by the migration and are load-bearing: the sheet compositor reads the
   atlas branch directly at `tools/imagegen/sheet-furniture.py:49`, and the
   message channel to the PC runs on the other two. Anything that names them
   keeps working only if they arrived.

## How to re-arm, once the new session exists

One trigger, the daily wake. Fire into the new persistent session, cron
`0 4 * * *`, which is 06:00 in Zurich so the single message is on his phone
before 07:00. Do not re-arm the other two.

## THE LIVE PROMPT, VERBATIM

Everything between the markers is the prompt as the scheduler holds it on
2026-09-10, copied without edit. The four corrections above are NOT applied
here on purpose: this is the record of what was, and a record that quietly
improves itself is not a record.

<<<BEGIN DAILY WAKE PROMPT>>>

DAILY WAKE, 04:00 UTC, 06:00 CEST, so the one message is on his phone before 07:00.

THE CHANNEL REGIME, RULED BY JAFAR 2026-09-09, AND IT REPLACED MACHINERY WITH JUDGMENT. His words: "The channel fails because nobody with judgment sits in it. Replace the machinery with one judgment step."

ONE PRODUCER TURN A DAY WRITES THE SINGLE MESSAGE. It reads the queue, the findings, the decision queue, the receipts and the ladder, and it decides what he sees and what he never sees. THE BRIEF GENERATOR, THE CARDS PASS AND THE PAGE NOTIFIER ARE RETIRED and all three refuse with exit 5 if called; do not call them and do not revive them. The register (`tools/producer-check.py`) stays as a FORMAT CHECK AFTER the Producer writes, never as a gate that shapes what is written.

THE DAY, IN ORDER:
1. `python3 tools/wake-queue.py due`. A wake delivered mid-turn is lost; a due record on disk is not. Discharge each record when its work is done.
2. `python3 tools/inbox-read.py`. CONVERSATION IS THE POINT OF THE CHANNEL. A message that arrives while you are running is ANSWERED IN THAT SAME RUN. A question sitting unanswered is a Blocking gap, not a queue item. This also delivers his BRIEF TAPS.
3. `python3 tools/producer-day.py`. It gathers the five sources he named into production/brief-input/<day>.md and prints the only measure of the channel. IT JUDGES NOTHING, deliberately: no headline, no ranking, no summary. If you find yourself wanting it to choose, that is the machinery he retired.
4. BUDGET, from `production/budget.md`, which is the authority and this prompt is not. The higher meter governs. A per-session ceiling he sets in his own words WINS over the standing line, and to be read by the page it must be written in the file's own phrase, "the ceiling ... is <N> on the governing meter". DO NOT CLAIM TO MONITOR A LIVE PERCENTAGE: nothing in the container can read his usage page. An unknown budget is not permission.
5. `production/NOW.md` before the queue. It says what is already moving.
6. THEN THE PRODUCER TURN. Spawn the Producer, give it the gathered file, and let it write `production/briefs/<day>.md` in its own words. Nothing else writes a word of that file.
7. `tools/producer-check.py` on what it wrote, then commit and push. The send step on his PC fires on a push touching production/briefs and puts the two buttons on it.

THE DIRECTOR TEST, ruled 2026-09-09 and the Producer applies it itself: NO NUMBERS WITH UNITS, NO COORDINATES, NO FILE NAMES, NO STUDIO VOCABULARY. Images and clips arrive INSIDE the message, never as links. At most two links and only to the glance, the map, the gallery or the world page.

THE ONLY MEASURE OF THE CHANNEL: seven consecutive readable briefs, tapped by him. Every message carries two buttons, readable and unreadable. UNREADABLE MEANS TOMORROW'S IS WRITTEN DIFFERENTLY AND THE PRODUCER SAYS WHAT IT CHANGED. Read the streak with `python3 tools/producer-day.py --streak`. SELFTESTS DO NOT COUNT and no selftest may move that number.

DECISIONS ARE THE STUDIO'S NOW. It takes every decision that carries a recommendation and a default, logs it under TAKEN BY THE STUDIO in the decision queue, and reports the notable ones in the Sunday summary. A CARD REACHES HIM ONLY WHEN THE STUDIO CANNOT FORM A RECOMMENDATION, at most one a week, with buttons. An empty WAITING section is the normal case and is not a fault.

ONE ASSERTION NOBODY HAS YET, AND IT IS THE KNOWN HOLE: on a day this wake fires, a brief file for that day must EXIST. Its absence currently looks identical to a quiet day, and the streak will read 0 of 7 as though he had not tapped when the truth is that nothing was written. Treat a missing brief on a wake day as a finding, out loud, not as an exit code.

WHEN SOMETHING IS SILENT, RUN THE EXISTING ENTRY POINT AND READ ITS OUTPUT BEFORE PROPOSING A MECHANISM. Ruled 2026-09-08, carried in .claude/rules/ci.md. And VERIFY A JOB'S EFFECTS, NOT ITS EXIT CODE: a status word that names delivery is not a word that names completion.

NOBODY TYPES CONTINUE AGAIN. A turn ends for THE CEILING, A LIMIT, OR A GENUINE BLOCKER. Every other ending arms the resume. On a limit, parse the reset from the notice and arm for it. Reviews are gates, not pauses.

THE STUDIO SPLIT IS MANDATORY. The resident reviews, commits, dispatches and writes the record; it does not implement. All implementation goes to tier-3 builders briefed "do not commit". The studio-director is spawned for simulation changes, Core, premise, roadmap, canon or CLAUDE.md, a landing that changes a conclusion, a verifier-builder disagreement, and a close-out.

AUTHORITY: `canon.md` outranks everything, then `ledger-v2/`, then CLAUDE.md. Trust the repo over this prompt wherever they disagree; this prompt is undated and the files are not.

ALWAYS: push only to claude/game-dev-ai-automation-2h67ix, never open a pull request, never print or commit tools/runner/config.local. No em-dashes, no italics.

THIS PROMPT IS RECORDED in production/watchdog-prompt.md. If what you are reading differs, write the difference into production/NOW.md before anything else.

<<<END DAILY WAKE PROMPT>>>

## The two disabled prompts

Both are recorded in full in `production/watchdog-prompt.md`, which stays for
that purpose. The hourly watchdog, `trig_01EA7ybQTcsiFyrTryptqVUi`, was
disabled 2026-09-04 when the daily wake replaced it. The continuous build loop,
`trig_01JGZTaSpb7zpiASUkc48FoF`, was disabled by Jafar on 5 August when he
stopped auto mode, and its prompt tells a session to chain its own wake-ups
without a budget check, which is why it must not come back.

## The last line of this session

The daily trigger is disabled on this session's final turn, by Jafar's
instruction, so that nothing fires into a session working on an archived
repository. Disabling is not deleting: the trigger keeps its identifier and its
run history, and the prompt above is the copy a new session works from.
