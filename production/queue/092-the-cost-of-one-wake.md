line: infrastructure (the Producer loop, inbound: the wake half)
spec: production/NOW.md item 1 inbound clause as amended by game-design/decision-2026-09-05-ruling-standing-order-refill-and-the-wake-half.md section 1.4; queue 088, "The half that does not work"
acceptance: one night window, bounded by two readings from Jafar of BOTH meters as typed integers at its two ends, with no other work on the account and no other trigger firing inside it, during which a temporary recurring trigger fires with a null prompt (run the 088 reader; answer any pending message through the outbox; otherwise end the turn), printing pointsPerFiring=delta/N with N counted from the session's own turns and not from the schedule, the resolution 1/N named beside it, and the variant named (persist into this session, or a fresh session); a window in which any other spawn or any use of Jafar's own fell is labelled contaminated and the number is REFUSED rather than published; the trigger is deleted at the window's end by a one-shot armed in the same turn that armed it, and a kill-switch file the bot writes on his command disables it at the next firing, both proven; readings that did not arrive print the words "nothing measured" with firings=N and no delta
max_sessions: 1
status: BLOCKS the wake half of item 1. Needs Jafar for one night and two readings. The cadence of the TEST night is his choice on the card; nothing is armed before he rules.

## Why this item exists at all

Item 1 asks that anything Jafar sends the bot reach the session "never waiting
more than a few minutes". The transport half is a minute. THE WAKE HALF IS THE
BLOCKER: nothing on his PC can call into the container, a turn begins only when
a trigger fires or he types, and the only live trigger is daily. Asleep, worst
case is up to 24 hours.

Three routes exist and a fourth was measured shut (the inbound webhook answers
401 to anything the PC can sign; see 088). Of the three, ONLY A FAST RECURRING
TRIGGER closes item 1 as he wrote it. It is not armed, and the reason is that
its cost per firing has never been measured.

## The refusal is honest about what it rests on

There is NO SERIES. Nobody has ever measured what one firing of a recurring
trigger costs, and rule 2 forbids setting a bound without one.

In particular, `production/NOW.md` says 76 firings would have cost real points
against 3 of headroom. THAT IS THE RESIDENT'S JUDGEMENT AND NOT A MEASUREMENT,
and it is used here as evidence for NEITHER expense NOR cheapness. It was
enough to silence a watchdog at the ceiling; it is not enough to refuse the one
route that closes item 1.

Note also what this is NOT: queue 076 prices a TOKEN from the PC's transcripts.
It does not price a FIRING in this session. The two are different quantities
and 076 landing would not answer this question.

## The four things that make arming safe

1. A printed `pointsPerFiring` with its resolution, from a window clean enough
   to divide: no other spawn, no other trigger, no use of the account by Jafar.
2. A phone-side KILL SWITCH. The container cannot read the meter, so a night
   that runs hot has no way to notice by itself. `/stopwake` writes a file on
   the inbox branch; the trigger's prompt reads that file FIRST and disables
   the trigger.
3. A one-shot armed IN THE SAME TURN that arms the test trigger, whose job is
   to delete it at the window's end. A test that can outlive its window is a
   leak, not a test.
4. Jafar chooses the cadence. It is his meter.

## The card's options, for the Producer

- A. A 15-minute null-firing night. 24 firings in six hours, resolution 0.04
  points per firing, and at the resident's unmeasured guess about one point.
- B. An hourly night first. Six firings, resolution 0.17: cheap, and too coarse
  to price a five-minute cadence.
- C. Awake-only this week, no test.

RECOMMENDATION A. DEFAULT C if unruled, BECAUSE THE DEFAULT MAY NOT SPEND.

## One thing to prove before its cost is counted

Whichever variant runs, the FRESH-SESSION one must first prove it can do the
job at all: one firing that reads the inbox and lands an outbox file on the
branch. Nothing in the tree says a non-persisted trigger has the repository or
the tools, and pricing something that cannot work is a number about nothing.
