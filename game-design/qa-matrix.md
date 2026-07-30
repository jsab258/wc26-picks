# QA matrix — the human test plan (P9)

Layered ON the automated harness, not beside it: every row here is something
the 1451 CoreTests, the 71-check SimHarness, ShapeCheck, the lint and the CI
sim's ~30 gates CANNOT establish, mostly because they are questions about how
the game FEELS or how a human reads it. Where an automated gate half-covers a
row, the row says so, so a playtest spends its time where automation is blind.

Format: DO / EXPECT / automation coverage. Tick what passed, note what
surprised you — the surprises are the yield.

## 1. The first week (Act I)

- **DO** play days 1–3 without touching the night life. **EXPECT** the bar
  runs, Lena teaches, the tour ends at a cellar door she doesn't open, the
  runner's first ask reads as Mickey's arrangement rather than a quest prompt.
  *(Automation: PP flags fire; nobody has judged the PROSE in situ.)*
- **DO** take the first drop bare-faced, then talk to Ada next morning.
  **EXPECT** the street's mood word moves within a day or two, and somebody
  SAYS something that traces back to being seen. *(Automation: heat math
  yes; whether the causality is legible to a person, no.)*
- **DO** lie to two different people about the same night. **EXPECT** the
  contradiction surfaces as suspicion in later talk, not as a meter.
- **DO** lose the week on purpose (skip jobs, stay hot). **EXPECT** the
  verdict screen reads fair — you can name the mistakes that did it.
- **PACING QUESTION (roadmap):** does the week feel like seven days of
  building dread, or a checklist? Automation cannot answer this at all.

## 2. The open city (day 8+)

- **DO** read the day-8 teaser, then walk all three districts. **EXPECT**
  Copper Row reads as a market quarter, Ironside as work-by-day/empty-by-
  night, the Hook as home turf.
- **DO** buy or squeeze your first business; establish one racket; hire one
  person. **EXPECT** each steps through people (dialogue verbs), never a
  management screen.
- **DO** squeeze hard for four or five days. **EXPECT** the district gets
  audibly poorer — supplier prices, the bar's take, somebody saying the
  street can't pay. *(Automation: the numbers move; the QUESTION is whether
  you can feel the loop without reading a panel.)*
- **DO** get exposed until the Fall fires. **EXPECT** three days gone, cash
  seized, the street KNOWS (no more guessing), wounds/purses/debts advanced
  three days, and the run afterwards feels post-scandal, not reset.

## 3. Act II — the seven pressure points (THE open playtest question)

Nobody has seen these fire in a long human campaign; the sim proves they CAN
fire, not that they land at the right MOMENTS.

- **DO** build to two arms noticing you. **EXPECT** PP1 reads as "it isn't
  one rival anymore," not as a status change.
- **DO** let the machine's letter arrive (PP2). **EXPECT** the injunction
  names three real options, and paying Hal — either way — works and
  reopens the till. *(New since audit: both verbs exist now.)*
- **DO** keep one day-life friendship above warm while running a crew, and
  never attend an evening. **EXPECT** the collision still finds you (the
  doorstep variant, at the bar, after dark). *(New since audit.)*
- **DO** reach the Table. **EXPECT** all three answers offered when your
  standing supports the counter; refusing is never gated. *(New.)*
- **PACING QUESTION:** do the seven arrive spread across days 8–18, or
  bunched? Automation cannot see bunching.

## 4. Act III — the audit

- **DO** open the act with an empire. **EXPECT** the letter is frightening
  in a procedural way; Reese sits in the bar nine-to-six and speaks in
  words, not numbers (counts as words, dates as dates).
- **DO** save and reload mid-audit. **EXPECT** Reese still exists, the
  daily item is still answerable, the closing date holds. *(Automation
  covers state; a human confirms the SCENE resumes coherently.)*
- **DO** reach the last day with two calls and people worth calling.
  **EXPECT** "There is not time for another" lands after the second call.
- **DO** refuse Ellis's deal in a campaign with a managed landscape (leash,
  buy quiet, discredit). **EXPECT** "Both" is reachable the hard way.
  *(Measured at ~6% of cautious campaigns; a human should confirm it reads
  as EARNED, not lucky.)*
- **ROADMAP QUESTION:** play one campaign with NO empire to the audit —
  the inspector should still be a scene, not an inert man at a table. This
  is the known thin spot; report what it feels like.

## 5. The Fall + the record (new balance, decided 2026-07-28)

- **DO** fall once, then reach the audit. **EXPECT** the street is quiet
  about you (rumors died with the arrest) but the inspection reads HARDER —
  the record is on file. Kingdom through a post-Fall audit should feel
  genuinely hard; the deflect road should feel like the only wide door.
- **JUDGE:** is x1.15 the right weight? The lab says it barely touches
  cautious campaigns and bites aggressive ones. Your hands will know.

## 6. Saves (P2, new)

- **DO** "Keep a copy" before a risky night, ruin the night, then reopen
  the copy from the main menu. **EXPECT** the copy lists its day, opens
  exactly there, and the autosave line is untouched by the reopening.
- **DO** kill the process mid-save (task manager during a save toast, if
  you can time it). **EXPECT** the game reopens from either the save or
  its backup — never a dead file, never a silent new game.
- **DO** corrupt the autosave by hand (open the json, delete half). 
  **EXPECT** the water-damage line, the copy underneath opening, and the
  bad file kept beside it as `.corrupt`.
- **DO** start a New game with copies in the drawer. **EXPECT** the copies
  survive and stay openable.

## 7. Options + accessibility (P4 slice)

- **DO** move every slider and toggle mid-game. **EXPECT** volume and
  sensitivity apply immediately; text size applies to panels opened after
  the change (and SAYS so on the screen); colourblind-safe swaps the
  debit/held colours everywhere including the ledger.
- **DO** rebind every action, including into conflicts. **EXPECT** the
  previous owner loses the key, nothing becomes unreachable, the list
  shows every action the game listens for. *(Automation: the smoke test
  now asserts the list's completeness; a human confirms the BINDINGS work.)*

## 8. Phones and distance (M10)

- **DO** ring a place at the wrong hour; ring somebody who isn't a regular
  anywhere; leave word with whoever answers. **EXPECT** the message
  travels as gossip (with all its risks), not as delivery.
- **DO** run the last audit day down the phone. **EXPECT** both calls work
  from a phone box, and reaching one person is not reaching another.

## 9. Perception (M16 Phase 1)

Everything here is verified automatically EXCEPT the three questions at the
bottom, which are the only ones that matter and the only ones a test cannot
answer.

- **Automated, machinery:** a lit walker is detected at greater range than one
  in shadow (measured in the scene at 23:00 by probing twelve points for the
  brightest and darkest spots, not asserted in a unit test); a sound behind a
  wall is not heard; a sound under the ambient floor is not heard.
- **Automated, behaviour:** somebody's head turns toward the player during the
  run; a staged thirty-second loiter draws at least one of them; a staged door
  slam at 3am has somebody walk toward it. All three fire after day ten, in the
  open city, so the probe cannot vote on the week's outcome.
- **Automated, legibility:** the vignette measurably changes with the light on
  the player; the noise ring's radius equals the acoustic model's rather than a
  copied constant.
- **DO** stand under a lamp at 3am for a minute, then stand in a doorway for a
  minute. **EXPECT** those to feel different — heads turn in the first and not
  the second.
- **DO** run past somebody at night, then walk past the same person.
  **EXPECT** a difference, with nothing said about it.
- **DO** make a noise at 3am, then the same noise at noon. **EXPECT** the ring
  to be much bigger at night, and somebody to come at night and nobody at noon.

**The three a test cannot answer, and they are the point:**

1. **Is the visibility readout findable?** After twenty minutes, did you have
   any sense of when you were exposed? Invisible means it is not working;
   noticing it *as an effect* means it is too strong.
2. **Was anything unfair?** If somebody noticed you and you could not work out
   why, that is the exact failure this whole design exists to avoid.
3. **Sound off, then picture off.** The four attention channels are supposed to
   be redundant — any two enough. If either pass leaves you unable to tell you
   were noticed, one of them is decoration.

## 10. The one-hour smoke (before any long session)

Boot → new game → talk to Lena → take one drop → sleep → read the morning
card → open every panel with its key → Escape out of each → pause →
Keep a copy → quit to menu → Continue. Fifteen minutes; if anything in that
chain snags, stop and report before investing an evening.
