line: production (the moat, and the first measurement of it)
spec: Jafar 2026-09-06, "Run the comparison yourself, at whatever scale your
  own tooling supports, and report the result with its confidence and its
  biases."
acceptance: a landed change after which a player who is seen committing a
  crime, and who then lies about it, hears something in the town that a player
  who told the truth would not hear; measured over the same sweep, so the
  number that moves is lieHeard, today 0 of 90
max_sessions: 2
status: READY 2026-09-06. P0 on the moat. THE SUPPORTED FINDING, in Jafar's
  own words and no stronger: "In the tested scenarios, caught lies did not
  change the spoken responses, and recognition stayed below threshold.
  Overheard gossip provides a separate working route to audible consequences."
  Three mechanisms each work and the chain between two of them is inaudible;
  the third route works.

## What was measured

1,296 sessions, 648 per arm, over 108 of 108 distinct player paths and 6 of 6
seeds. THAT IS EXHAUSTIVE COVERAGE OF THE CHOSEN HARNESS COMBINATIONS, ruled
by Jafar 2026-09-06, and it is NOT the whole space a player could walk. The
harness offers three jobs, three hours, two approaches, two coats and three
answers; a shipped game offers more, and the sweep says nothing about what is
outside the grid it enumerated.

## The three numbers

    lieHeard=0/90        in 90 path-seeds the lie WAS caught, suspicion moved
                         0.060 to 0.176, and not one of the five spoken lines
                         differed from the same path played truthfully
    liveSilent=1944/1944 in the SHIPPED build, every recognition beat in every
                         path in every seed is below the Comments rung, so
                         Lena and the passer-by say nothing at all, 648 of 648
                         sessions
    on-topic             canned arm 3240/3240 lines, real arm 540/3240

The arm without perception, memory or propagation is on topic six times more
often, and there is no beat in the grid where the real arm is pointed and the
canned arm is not. STATE THAT AS FREQUENCY AND NOTHING MORE. Ruled by Jafar
2026-09-06: a higher on-topic rate is NOT evidence that the canned arm is
better, more enjoyable, or preferable. Nobody has played either arm, and the
sweep cannot speak to enjoyment at all.

## Why that is not a tuning problem

The mechanism is cumulative by design and the arithmetic is sound. Lena's
pressure crosses the 0.42 Comments rung on crime 2 without decay and crime 3
with it, which is the morning of day 4 or day 5. That is a design that needs
days, exactly as Jafar's hypothesis said, and it is not far off.

The fault is that nothing between "the mechanism fired" and "the player could
hear it" carries the signal. Suspicion moves, the contradiction is detected,
the rumour propagates with a true causal chain behind it, and every line the
player actually hears falls in the same plain neighbourly band.

## The three sub-faults, each filed separately

- 128, a lie is uncatchable at the live tick rate
- 129, the gossip re-tell guard leaks on a floating point bit
- 130, telling the truth earns nothing

## What this does NOT say

It does not say people would prefer the canned arm. Nobody has played either.
The study measures what the shipped session EMITS over every path a
participant could walk, with high confidence because it is an enumeration
rather than a sample, and it carries ZERO evidence about what a person would
perceive or enjoy. Human playtesting waits for a visual build, which is
Jafar's ruling and is not reopened here.

## The biases, all of which flatter the real arm

Witnesses come from a four-person roster and 36 sightings were dropped because
only 2 of 4 agents are awake at any offered hour. The harness's gossip is
ungated by co-location where the live game gates on it. The harness substitutes
the plain band where the live game would be SILENT, which makes both arms
speak equally often and is right for a controlled comparison and wrong as a
picture of the build.
