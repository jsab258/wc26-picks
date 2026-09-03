# Playtest notes — 29 July 2026

> **STATUS: LOG, 2026-07-29. NOT CURRENT.** A record of what was true on the
> day, kept because the reasoning is worth having. **Do not read it as the
> present state** — for that, `roadmap.md`. Items called "open" here have
> very likely been closed since.

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

**Press F1.** The debug panel now leads with frames per second, the worst
frame in the last three seconds, and which graphics preset is active. Two
numbers rather than one on purpose: an average hides exactly the stalls
that make a game feel bad, and thirty seconds at 120fps with four 200ms
hitches in it averages beautifully and is horrible to play. If the two
numbers are far apart the panel says HITCHING, which is a different
complaint from "slow" and has a different fix.

**And there is a dial now**, in Options → Graphics. Three stops, and the
label tells you what each one gives up rather than just naming itself.
Low drops the light shafts and reflections and shortens the shadows; it
deliberately does **not** empty the street, because a city with no people
in it is not a cheaper version of this game, it is a different and worse
one. If Low is much faster than High, the look is your bottleneck and I
have things to try. If it makes no difference, it is something else and
that is useful too.

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

- **Reflections were contributing nothing, and now I know why.** The probe
  refreshed perfectly and lit nothing: a renderer only samples a reflection
  probe when its bounds sit inside the probe's box, and the road is a few
  very large meshes whose bounds dwarf it, so Unity blended them to the sky
  instead. The shine you could see was direct lamp specular, not
  reflections. A fix is in the build you will be playing — so the question
  for you is simply whether lamps and neon show up **in** the wet road, or
  whether it is just shiny.
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

0. **The F1 numbers**, once, wherever you happen to be standing. That is
   the single most valuable thing in this list because it is the only one I
   cannot get any other way.
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
