# Playtest notes — 30 July 2026

> **STATUS — LOG, 2026-07-30. NOT CURRENT.** A record of what was true on the
> day, kept because the reasoning is worth having. **Do not read it as the
> present state** — for that, `roadmap.md`. Items called "open" here have
> very likely been closed since.

Second session. The 29th's notes still apply for everything about the art, the
frame rate and the crowd; **this file is only about what changed overnight.**

## What changed: the city has senses now

M16 Phase 1. Until last night no NPC in this game could see or hear anything —
the lighting model computed how lit every spot was and nobody read it, and the
audio layer played footsteps nobody heard. Both are wired.

**What that means in play:**

- **People notice you, and light decides how far away.** Stand under a lamp on
  Hook Street and somebody across the road will turn their head. Stand in a
  doorway ten metres from the same person and they will not. That is one
  number, `LightModel`'s, finally being read by somebody other than the
  renderer.
- **Standing about is a thing.** Half a minute in one spot and you are
  loitering, and it draws attention faster than walking does. Crossing a
  street is free.
- **Running at night is different from running at noon.** Same action, and the
  street reads it differently. Nobody is told this and nothing announces it.
- **Noise carries a distance that depends on the hour and the weather.** This
  is the part I would most like you to feel. A sound is not loud or quiet in
  the abstract — it is loud or quiet *relative to what is already happening
  where the listener is standing*. So:
  - A footstep at 3am in a residential street carries about **3.6 metres**.
  - The same footstep on a daytime street carries **nothing at all**.
  - Rain shortens everything, which makes rain cover.
- **Somebody will walk toward a noise.** This is the one I think will land
  hardest, because it needs no interface at all. If somebody starts coming
  toward where you just made a sound, you will know exactly what happened.

## The one piece of interface, and it is not an icon

You have no HUD for any of this and you are not getting one. Tom Novak runs a
bar; he does not have a visibility meter.

Instead **the frame breathes.** Step under a lamp and the corners of the image
lift very slightly and the picture cools; step into a doorway and it closes in
and warms. It is about a tenth as strong as the black-and-white trick Splinter
Cell: Conviction used, deliberately, because it has to coexist with the
wet-asphalt night rather than fight it.

**The question for you: is it findable?** Not "did you like it" — whether after
twenty minutes you had any sense of when you were exposed. If it is invisible
it is not doing its job, and if you noticed it *as an effect* it is too strong.
I cannot judge this from here and it is the single most likely thing in this
build to be wrong.

## What to look at, in order of how much it tells me

**1. Walk down Hook Street at 3am and stop under a lamp for a minute.**
Then do the same thing in a doorway. If those two feel the same, the whole
night's work is not reaching you.

**2. Run past somebody at night, then walk past the same person.**
The difference should be legible without a word being said.

**3. Make a noise and watch what happens.** Then make the same noise in the
middle of the day and watch nothing happen.

**4. The frame, per above.**

## What is NOT in this build

Being honest about the boundary, because half of M16 is Core-only and cannot
be played yet:

- **No weapons.** The whole arsenal is written and tested — nineteen objects,
  the threat verb, carrying, blood, provenance — and **none of it is wired to
  a button.** Deliberate: the plan ships senses first and judges them alone.
- **The witness ghost is not in.** The thing that shows you what somebody
  believes is designed and tested in Core and has no visual yet.
- **The noise ring works now — three bugs, and a build says so.** It took the
  cooldown being spent by footsteps too quiet to draw, the circle being built
  standing on its edge, and finally the discovery that a line renderer created at
  runtime has no material at all in this build. CI now renders the frame twice
  and counts the pixels that changed rather than counting objects, and it reads
  1.4% of the frame. **So: make a loud noise at night and a single circle should
  appear on the road at the true distance the sound carried, once, and fade.**
  What I want from you is not whether it is there but whether it *teaches* — after
  three or four of them, do you have any feel for how far a slammed door goes at
  3am versus at noon? If it is still a mystery, the device has failed at the only
  job it has.
- **Barks are still silent**, so when somebody notices you they will not say
  anything. That is still the fifteen minutes of listening I need from you, and
  it now costs more than it did yesterday: two of the four channels that tell
  you you have been noticed are voice.

## What would help most

Same as last time, plus one:

0. **The F1 numbers.** Still the only thing I cannot get any other way, and now
   there is a second reason: perception runs for every walker within
   forty-five metres, six times a second. If this build is meaningfully slower
   than yesterday's, that is the cause and I need to know.
1. **Did you ever feel watched?** Yesterday this was a question about the
   gossip network being invisible. Today it is a question about whether the
   senses are legible.
2. **Was anything unfair?** If somebody noticed you and you could not work out
   why, that is the most important sentence you can give me — it is the exact
   failure mode this whole design is built to avoid.
3. **Where were you bored?**
