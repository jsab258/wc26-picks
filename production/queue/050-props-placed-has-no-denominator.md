line: infrastructure (instruments)
spec: this file, ordered by game-design/decision-2026-09-03-night-batch-of-2-september.md decision A
acceptance: AssetLibrary.PropsPlaced prints a denominator taken from the plan BEFORE any loading, in the shape propsPlaced=N/M, with absent props named and their reason; a fixture where a prefab is deliberately missing reads propsPlaced=N/M with the reason, and an accepting fixture where all resolve reads M/M, both in the tested layer
max_sessions: 1
status: READY 2026-09-03. instrument-builder, small. First in the ruling's order because it is the instrument fault.

## The finding

The sim's done line prints `propsPlaced=1522` town-wide with nothing to count
it against. A number that only counts up cannot say whether it is complete,
and the same word on the street vignette's own line already carries `23/23`
because that instrument was built with its denominator. One idea, two
implementations, and the older one is the blind half.

Ordered FIRST of the six by the 3 September ruling on the reasoning that an
instrument fault outranks the content items behind it: every other reading in
this list is judged using numbers this class of fault can hide.
