line: production (the milestone after the street)
spec: Jafar 2026-09-06: "After this batch, the next game milestone is one
  playable visual crime-and-consequence loop. Use the now-textured street to
  move toward that."
acceptance: a person other than Jafar can start something on his PC, commit one
  crime on the textured Meridian street, be seen, and HEAR the town react,
  without reading any instructions from this repository
max_sessions: 3
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06. THE NEXT MILESTONE. Everything below is assembly of
  parts that now exist separately; almost nothing here is new invention, and
  that is the point.

## Why this is now possible and was not this morning

Three things landed today and they are the three halves of this loop.

THE STREET IS VISUAL. Run 25 put Meridian's own textures on it: brick,
cobbles, wood, glass. Queue 123. It renders from `vignette-pieces.json`
through a packaged Unreal build on Jafar's PC, with nothing hand-placed.

THE CRIME LOOP RUNS. `OperationSetup.Build` and `Operations.Read`/`Run` produce
a job, witnesses and a takings figure, and `ledger/StrangerTest` drives the
whole thing end to end from real player choices. It is text today, and the
systems behind it are not.

AND WE KNOW WHICH CONSEQUENCE CHANNEL ACTUALLY SPEAKS. This is the part that
would otherwise have been guessed. The sweep measured, over the harness's own
combinations: caught lies did not change the spoken responses and recognition
stayed below threshold, WHILE OVERHEARD GOSSIP IS A SEPARATE WORKING ROUTE TO
AUDIBLE CONSEQUENCE. `ReportOverheard` never reads the stance ladder; first
talk about the player fires about 6 game minutes after a sighting, which is
seconds of real time, with several chances inside half an hour of play.

SO THE LOOP IS BUILT ON THE CHANNEL THAT WORKS. Do not build it on Lena's
recognition: that needs three to five nights and cannot speak inside thirty
minutes at the shipped constants. Build it on being seen and overhearing it,
and treat anything else as a bonus.

## The shape, and it is deliberately one of everything

One street, the one that is textured. One crime, from the existing content.
One way to be seen or not seen. One pair of people to walk past. One line the
player overhears that is causally about them.

WHAT MAKES IT A LOOP rather than a scene: what the player did has to be
recoverable from what they hear. If the player takes the coat, fewer witnesses
file, and the street should be quieter. That difference IS the milestone, and
it is measurable before any person plays it.

## What has to be found out first, in order

1. WHAT CAN ACTUALLY BE PLAYED. PARTLY ANSWERED ALREADY, from the probe's own
   source rather than from assumption: it defines NO character, NO pawn, NO
   game mode of its own and NO player start. It borrows the engine's first
   player controller solely to aim the screenshot camera, and the build is
   launched offscreen and unattended.

   So the honest phrase is that there is NO ONE TO PLAY AS, which is a
   different and smaller problem than "nothing is playable". A packaged build
   launched plainly may well hand a person a flying default camera, and Jafar
   may already have flown through the street. What is missing is a character,
   a controller bound to input, and something to act on.

   That is the smallest first deliverable of this milestone and it is a known
   quantity, not a research question. Do it before anything else here.
2. HOW A CRIME AND A SPOKEN LINE REACH UNREAL AT ALL. Core is C# and the probe
   is C++. Today the only thing crossing that line is a JSON scene file. Name
   the smallest bridge that carries one crime and one line of overheard speech,
   and do not build a general one.
3. WHETHER GOSSIP CAN BE HEARD. `ReportOverheard` ducks an audio bed and prints
   a line. In a visual build it needs a voice or a caption and two people
   standing close enough. Queue 135's nameless-pin finding is unrelated; this
   is a staging and density question and the sweep already named it as such.

## What must NOT happen

Do not widen this into a general engine bridge, a dialogue system or a save
format. One crime, one street, one consequence a person can hear.

Do not measure it by whether the machinery ran. Every gate in this repository
already says the simulation runs, and the sweep still found the moat inaudible.
The reading is what a person hears.

And do not put a human in front of it early. Jafar has ruled that human
playtesting waits for a visual build, and queue 131 says why the last attempt
could not have worked: one crime cannot reach the mechanism it was testing.
