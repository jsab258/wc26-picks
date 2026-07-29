# Playtest notes — 29 July 2026

For the first play session. Written to make an hour of your time worth more
than an hour of mine, so it is mostly about **what to look at** and **what I
cannot find out without you.**

## Getting it running

The build is a GitHub Actions artifact: open the latest run of **LEDGER
Windows build** on `claude/game-dev-ai-automation-2h67ix`, download
`LEDGER-Windows.zip`, unzip anywhere, run `LEDGER.exe`. Windows will warn
about an unsigned binary; that is expected and there is nothing to buy to
fix it.

**Every run uploads a playable build whether the gates pass or not.** A red
tick means the simulation's own quality checks failed, not that the game
failed to compile. If you want the most recently *fully green* one, take the
newest run with a green tick; otherwise the newest run at all is fine and
will differ only in the specific thing that was red.

## The one number I cannot get

**Frame rate.** CI runs on a machine with no GPU, so every performance
figure in the logs comes from a software rasteriser and means nothing. The
sim reports ~300ms a frame; on real hardware it might be 3ms or it might be
30. I have no way to find out.

If it is bad, the two things most likely responsible are the 362 volumetric
light shafts and the shadow pass on the bodies, both of which have cheap
dials. Tell me the number and roughly what is on screen and I can act on it.

## What to look at, in rough order of how much it tells me

**1. Walk down Hook Street at night, in the rain, and just look.**
This is the whole art bet in one shot: wet asphalt, lamp shafts, the
tonemap, the vignette, the grain. Every part of it was dead until last
night — the post stack had never executed a single frame since it was
written — so this view has literally never been seen by anyone at the
settings it now runs at. It is the thing I am least able to judge and most
likely to have got wrong.

**2. Watch two people talking, then walk up to them.**
Pairs stop, turn in, and stand at conversational distance, shoulders angled
rather than square-on. If they were talking about *you*, they break off and
look away. If they were not, they carry on while you walk straight through
them — that conditionality is the point, and if every pair hushes it is a
proximity trigger and I have got it wrong.

**3. Watch a crowd walk past.** Bodies are thirteen boxes in a joint
hierarchy, not a bought skeleton. They will not be mistaken for people. The
question is only whether the street reads as *populated* — and specifically
whether everyone looks like the same person at different sizes, or like
different people.

**4. Trigger an authored beat and see whether the camera does anything.**
A push-in and a held frame, and it should give way the instant you touch the
stick. If you notice the camera taking over, it is too strong; if you notice
nothing at all, tell me, because as of this morning that layer had also
never run.

## What I already know is wrong or unproven

- **Reflections may contribute nothing visible.** The gate says the probe
  wakes, refreshes and obeys its rate limit, and also that removing it
  changes not one pixel of the frame. I have an experiment in the next build
  to find out which end is broken. If the wet road looks flat rather than
  reflective, that is this.
- **Nobody has ever attended an authored beat in a verified run.** Fixed
  twice this morning; unconfirmed as I write.
- **Combat exists and is deliberately unwired.** Violence is deferred by
  design (roadmap M11) — present as something that has happened to you, not
  something you do. If that feels like a hole while playing, say so, because
  it is a decision and decisions can be revisited.
- **The barks are silent.** The voice bank needs about fifteen minutes of
  listening from you to pick two voices. Until then people's mouths are shut.

## What would help most

Blunt reactions, not bug reports. I can find bugs; I cannot find out whether
it is any good.

Specifically:

1. **Does the street feel like a place?** Not "does it look good" — whether
   it feels like somewhere people live.
2. **Did you ever feel watched, or talked about?** That is the entire
   premise. If the gossip network is invisible in play, then it does not
   matter that it is the best-tested thing in the project.
3. **Where were you bored?** The most useful sentence you can give me.
4. **Anything that felt cheap or fake.** You will notice these in seconds
   and I cannot see them at all.

## What I am not asking for

Do not hunt for bugs and do not read the logs. Thirty-odd automated gates do
that on every build and they are better at it than a person is. Your time is
worth more spent on the things no test can answer.
