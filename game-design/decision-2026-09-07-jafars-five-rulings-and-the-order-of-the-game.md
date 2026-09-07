# Jafar's five rulings of 2026-09-07, and the order the game is built in

> **STATUS: LIVE, verified 2026-09-07.** These are his rulings, not a director's, and
> they bind until he replaces them. The four builds they set in motion are
> named in section 7 with what each one still has to prove.

## 0. Why there is a record at all

He gave five rulings and an ordered list of game work in one message, from his
phone, while away from the PC. Four of the five change how the studio reaches
him or how work is verified, which means a session that has not read them will
get his instructions wrong in a way he cannot see. The sixth thing he said,
"No new process beyond rulings 1 to 5", binds this record too: nothing here
invents a mechanism he did not ask for.

## 1. THE MACHINE LAUNCHES THE BUILD, NOT HIM

Verbatim: "I do not launch builds to see if they compile. The runner is on my
PC; use it." A workflow step launches the packaged build in automation, walks
a scripted route, captures a clip and frames, and judges five things: does it
launch, is there a street, is there a walking camera, are the test cards
absent, is collision real. The clip goes to Telegram with a one-line verdict.

WHAT THIS RETIRES. The PLAY THE STREET request sent this morning is WITHDRAWN
and its file is deleted from the outbox in the same commit as this record. It
asked him to smoke-test a build that had never launched, which is precisely
the labour he has now ruled out. And the standing rule underneath it, in his
words: "Human playtesting starts when there is a crime and a consequence to
feel, not before."

THE HONEST READING OF WHY HE HAD TO SAY THIS. He was asked to double-click a
launcher twice today, and the first time it found nothing because the build
lived only inside the runner's swept workspace. Both asks were the studio
using him as an instrument the runner could have been.

## 2. TELEGRAM CANNOT DEPEND ON A WINDOW

Verbatim: "It died at 11:30 today because that window was closed and the only
signal I had was silence." The three daemons become a Windows scheduled task
that starts at logon and restarts on failure. `START EVERYTHING.bat` survives
as the manual fallback only.

INSTALLED WITHOUT HIM, and this is the part that makes it real: the
self-hosted Actions runner is already a permanent service on that machine, so
the install is triggered by a workflow rather than a double-click. An install
that needs him at the keyboard is the same failure in a new coat.

HOW THE STOP WAS ACTUALLY FOUND, because it decides what to build. Nothing
alarmed. It was noticed because a counter that had climbed once per sweep all
morning, `refused=304`, had stopped moving, and the newest record on the
inbox branch was four hours old. Silence is not a signal, and a heartbeat that
lands on the branch he can already read is worth more than a log nobody sees.

## 3. THE MAP OPENS WITH A LADDER

Verbatim: "the steps to a playable loop, in order, with the current one
highlighted, so I can read 'step 2 of 10' in one glance from my phone."
Derived from `production/next-three.json` and the milestone file, NO PROSE
PARSING. Everything else stays below it.

THE BAN ON PROSE PARSING IS NOT STYLE. The map once scraped headings out of
`production/NOW.md`, and the guess about which paragraph was an instruction
put a finished task and a superseded task on his phone as the plan. If an
ordered ladder cannot be derived structurally from those two files, the source
gains an explicit ordered field; structure is added at the source, never
inferred at the reader.

## 4. HE IS REACHED ON TELEGRAM, OR HE IS NOT REACHED

Verbatim: "From now, I communicate only through Telegram. Anything that truly
needs me in the terminal is sent as a Blocking card saying so, in one
sentence. Otherwise I will not open Claude Code and I will not read
transcripts."

WHAT IT CHANGES IN PRACTICE. Terminal output is now working notes with no
reader. A finding that never reaches Telegram did not reach him, and a session
that ends with its result only in the transcript has delivered nothing. The
Blocking route already exists (`.claude/agents/producer.md` carries the
register, `tools/runner/cards.py` refuses to route a Blocking item as FYI by
default), so this ruling adds no mechanism: it removes an assumption.

## 5. A TEST REQUEST MAY CARRY ITS PICTURE

Verbatim: "let the photo path carry a caption for a test request, tested,
rather than sending text without the picture."

THIS OVERTURNS A CALL I MADE THIS MORNING, and the record says so plainly: I
sent him a test request as text and told him I would not bend the photo
instrument to carry it. He has ruled that the instrument should be extended
properly instead. The word "tested" is his and it is the whole difference
between the two positions.

## 6. THE GAME, IN ORDER

His order, and each step is verified by the machine per ruling 1, ends with a
clip on his phone and a green step on the ladder:

1. The walkable street.
2. One crime he can commit there, with a real spatial witness event passed
   into the simulation.
3. One overheard consequence, from a second NPC, in that same build.

Findings go to `production/findings.txt`. Nothing else is in scope.

## 7. WHAT IS IN FLIGHT AGAINST THESE, AND WHAT EACH MUST PROVE

Four builds were started the moment the rulings landed, none of them yet
verified on the machine that matters:

- Ruling 1, the automated playtest step. Must prove five judgments with
  denominators, and the collision one needs a planted case that SHOULD block
  and one that should not, or the number proves nothing.
- Ruling 2, the scheduled task. Must query the task back after installing it,
  because `schtasks` reporting SUCCESS is not evidence a task will ever fire.
  Two supervisors must never run at once.
- Ruling 3, the ladder. Must not show a step as done on evidence it does not
  have; a ladder that shows unproven progress is worse than one that says
  nothing was measured, because he will act on it.
- Ruling 5, the captioned test request and the clip. The overflow case is the
  one that matters: a caption cap that truncates a test request in silence
  would deliver him an instruction with its ending missing.

NONE OF THE ABOVE HAS RUN ON HIS PC. The first workflow run is the accepting
case for rulings 1 and 2, and until it happens this section is a list of
intentions with tests attached.
