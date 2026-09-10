# 252. Carry the tier numbers into the brief, which is the half of the routing ruling that is not wired

STATUS: READY, 2026-09-10. Jafar's routing ruling has two halves. The
enforcement half landed today. THIS IS THE OTHER HALF AND IT IS NOT BUILT.

## What he asked for

"Measurement: turns and spawns per tier in every brief, the two meters side by
side on Sunday; points are mine and are not estimated. The test is unchanged:
the Fable meter below the total meter within a week."

## What exists and what does not

EXISTS: `tools/spawn-cost.py` reads the `tier` column of
`.claude/agent-turns.tsv` and prints turns and spawns per tier. It also prints
`--routing-drift`, which joins declared against ran.

DOES NOT EXIST, and these are the whole item:

- A WEEK WINDOW. The tool reports all time. His words are "the week's spawns",
  and an all-time number cannot answer a weekly test: it moves too slowly to
  show a change and it never returns to zero.
- ANY PATH INTO THE BRIEF. `tools/producer-day.py` gathers five sources into
  `production/brief-input/<day>.md` and none of them is a tier number. THE
  BRIEF HAS NEVER SEEN ONE. So the numbers exist and nothing carries them to
  him, which is the same as not having them.
- THE SUNDAY PAIR. The two meters side by side are HIS readings. Nothing in the
  container can read them, so the Sunday summary has to carry a slot he fills,
  not a number the studio invents.

## POINTS ARE NOT ESTIMATED, and this is the clause to defend

He said it in the ruling itself: "points are mine and are not estimated." The
container cannot read his usage meters and this project already has a standing
rule against claiming to monitor a live percentage. So the brief reports TURNS
and SPAWNS, which are measured, and leaves points to him.

The failure mode to guard against is specific: a brief with a slot for a points
figure invites somebody to derive one from turns. A turn is not a point and no
arithmetic here connects them. If the slot must exist, it carries his last
reported reading with its date, or the words "nothing measured".

## THE RISK THAT MATTERS MORE THAN THE FEATURE

FIVE numbers in this ruling's own implementation were wrong before they were
right, and EVERY ONE OF THEM OVERSTATED:

1. `spawn-cost.py` summed cumulative snapshots, inflating the log by about
   2000 turns of 10407 and turning 163 agents into 189.
2. A sweep counted `general-purpose` as a violation when it has no declaration
   to violate.
3. One window had three answers, 12 rows/1167 turns, then 6/582, and the truth
   was 4 distinct agents/415 turns.
4. The drift join counted compliance as violation, because three definitions
   were reclassified an hour after the runs it was judging.
5. Both drift buckets were labelled VIOLATION when both are DOWNWARD, which the
   ruling permits. The headline overstated by 100 percent: the true count of
   what the ruling forbids is `upwardWithoutReason=0`.

THIS IS THE INSTRUMENT THAT REPORTS HIS TEST, and its demonstrated default
direction is up. So when the first weekly report says Fable has separated from
total, the question is not only whether routing worked. It is whether the
instrument still overstates. Before this item ships a number to him, re-derive
one figure by hand and print both.

## Done looks like

`spawn-cost.py` takes a window, defaulting to seven days, and prints turns and
spawns per tier over it with the denominator beside every zero, including a
tier that was never spawned, which must read "nothing measured" and not stay
silent. `KNOWN_TIERS` currently has no `haiku` at all, and three agents are now
haiku, so this bites on the first run.

`producer-day.py` gathers that line into the day's brief input as a sixth
source, named as such.

The Sunday summary carries the two meters as HIS readings with their date.

## Dependencies and risk

Depends on nothing; the schema landed today. The risk is stated above and it is
the instrument, not the feature.
