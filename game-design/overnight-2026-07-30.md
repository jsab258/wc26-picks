# Overnight — 29/30 July 2026: the city gets senses

**M16 Phases 1, 1b, and the Core of 2, 3, 5.** Approved at the start of the
night, built through it.

- **CoreTests: 2299 → 2618 checks.**
- **SimHarness: 71 → 89 checks**, including one new end-to-end scenario.
- **97 deliberate breaks** across seven new spec files, every one confirmed red
  before the code was trusted.
- **Eight new Core files**, one Unity bridge, two legibility layers, one lab.

---

## What is new, in the order it matters

### The senses (`Core/Perception`)

Two things here are not "every game has a cone".

**Light is finally an input.** `LightModel` has computed how lit every spot in
the city is, at every hour, for weeks — and no NPC had ever read it. A walker
under a lamp is now detected at thirty metres and the same walker in a doorway
is not, and both numbers already existed.

**Loudness is relative.** The find of the research pass, from Chaos Theory: a
sound is not audible at a radius, it is audible at a radius *given what is
already happening where the listener is standing*.

```
    r = 1.5m × 2^((loudness − ambient at the listener) / 8)
```

Which makes the clock and the weather tactical for free, because every number
it needs was already being computed for the mixer:

| | carries |
|---|---|
| Footstep, walking, residential 3am | **3.6m** |
| The same footstep, daytime street | **nothing** |
| Suppressed .22, in a busy bar | **nothing** |
| Suppressed .22, residential 3am | **86m** |
| .38 snub, daytime street | **177m** |
| Shouting, in a market | **2.2m** |

### Recognition, which is the mechanic I would defend hardest

The identification ladder is five rungs and **deliberately not monotonic**: a
face reads at eight metres and *recognition* reads at twenty-five, because you
know how a friend walks. So an acquaintance skips rung 3 entirely and **a
stranger can never name you at any distance.**

That needs a three-thousand-person acquaintance graph with real familiarity in
it. We have one. It is now claim 3b in the design doc, because it is the first
mechanic in this project that a bigger team could not simply outspend us on.

And it inverts the tactics: **the dangerous witness is not the closest one, it
is the one who knows you.**

### Observation as a generator, not a list

Seven perceivable slots — precursor, draw, act, victim, actor, flight,
aftermath — each filled by its own test. The spec's six named outcomes are now
*labels for common combinations* rather than a taxonomy I invented, which means
the model produces cases nobody wrote down.

Plus: certainty separated from **willingness** (a witness who was somewhere he
should not have been will not come forward, which makes the answer to a witness
usually not a knife), mutual awareness, the **delivery window** (a witness is a
person walking somewhere for a few minutes and you can follow, pay, threaten or
kill them before they arrive), misattribution, and **hardening** — accuracy
falls while confidence rises, so a witness left alone gets *more* dangerous.

### The street going quiet

The best idea in the legibility design and it costs nothing: the exact inverse
of masking, from the same numbers, needing no animation at all. A crowd going
quiet is the most recognisable "you have been noticed" signal a human being
knows.

**And it closed a loop I did not design so much as notice.** A street that has
gone quiet because it is watching you is a street where your next sound carries
*further*. Being noticed makes you louder. There is a test for it: a suppressed
shot the busy bar would have eaten is heard once the bar goes quiet.

### What the player sees

No meters, no icons, no HUD — Tom Novak runs a bar.

- **The frame breathes.** Lit and the vignette opens and the image cools; in
  shadow it closes and warms. A tenth as strong as Conviction's black-and-white,
  because it has to coexist with the wet-asphalt night rather than fight it.
- **One ring, one moment.** At the instant a sound is made, a single circle at
  the true audible radius after occlusion and masking, then gone. It does not
  expand — an expanding ring reads as a shockwave, and the radius is the answer
  rather than the animation.
- **Attention is read off people**, in four deliberately redundant channels led
  by audio rather than animation, because our bodies are thirteen boxes with no
  faces and betting the most important feedback in the game on the weakest asset
  we own is how this fails.
- **The standoff.** Four tenths of a second of the street ducking and the frame
  tightening, once per person, for the moment somebody meets your eye and you
  both know it. Nothing else may borrow it.

### The arsenal, in Core and not yet on a button

Nineteen objects across seven families, and **not one damage number.** Eleven
lose outright to a man who is ready and armed, because Tom runs a bar. A
revolver leaves no casing and an automatic throws brass. A kitchen knife is
untraceable *by being ordinary*. Only the ligatures cannot be aborted.
Brandishing is the primary use, and a barman with a razor gets the bluff called
where a man with a reputation does not.

Plus blood that is noticed at conversational distance and invisible across a
dark street, provenance that outlives the object, and a coat rather than a grid.

---

## What the night actually taught me

Five things I did not know at the start, all of them found by tests rather than
by thinking.

**1. `Vantage` needed two sightlines, not one.** A test asserting four witnesses
produce four different slot sets got three. One distance and one light level for
"the event" collapses the actor and the victim into a single perception — which
makes *act, no actor* unreachable, and that is Jafar's own headline example. The
model was wrong in the exact place it was designed to be right.

**2. Four tests looked strict and were not**, and break runs found every one: a
count instead of an assertion about any particular weapon; a hard-knowledge cap
raised to 1.0 with nothing noticing because no observation had ever come near
it; notice time deleted entirely because every vantage in the tests had watched
for three seconds; and a frisk cost flattened in the middle rung nothing had
ever compared.

**3. Nothing local compiles the Game layer.** A `double` Core constant landing
in a `float` Unity field cost a build. `lint-usings.py` now catches that class
in three seconds instead of nineteen minutes, and a second rule stops the
superseded witness path coming back into the game by accident.

**4. The harness could lose a break.** `atexit` does not run on SIGTERM, which
is what `timeout` sends, so an overrunning run left a deliberate defect in the
tree. Self-diagnosing, and now guarded.

**5. My own expectations were the thing out of band, twice.** The perception
lab warned about a 1% naming rate, and the warning was about my number rather
than the model — three quarters of witnesses are strangers who can never name
anybody. And I expected a bold man to call the bluff on a pistol; the model
disagreed, rightly. Nerve buys composure in front of a gun, not contempt for it.

---

## Measured rather than asserted

`RunPerceptionLab`, two hundred events, four witnesses each:

| outcome | share |
|---|---|
| sound only | 27.5% |
| nothing | 27.0% |
| act, no actor | 21.3% |
| aftermath | 12.1% |
| **full** | **4.8%** |
| partial / actor-no-act / precursor / flight | 7.4% |

**Partial observation is 95% of outcomes.** If that number were the other way
round the whole join would be decoration and a boolean would do.

Somebody can name the player at **4% of events by day and 1.3% at night** —
**darkness cuts naming by 4.6×**. Accidents are available in 12.5% of
situations and brandishing produces *comply* only 6.5% of the time, so neither
dominance risk in spec §11 is realised.

---

## What is NOT done

- **No weapon is on a button.** The whole arsenal is Core-only, deliberately:
  the plan ships senses first and judges them alone.
- **The witness ghost has no visual.** Designed, tested in Core, and correctly
  not built — it needs a violent act in the Unity layer to have anything to
  show, and building it now would be the sixth system in this project built and
  attached to nothing.
- **Save/load for the new state.** Premature: none of the durable state exists
  in the game yet.
- **The standoff is reported and not yet gated**, because I have not seen it
  fire once and gating on a number I have never observed teaches nothing.
- **Barks are still silent**, and that now costs more than it did yesterday:
  two of the four channels that tell you you have been noticed are voice.
