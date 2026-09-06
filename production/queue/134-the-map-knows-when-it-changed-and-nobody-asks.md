line: production (the channel to Jafar)
spec: Jafar 2026-09-06, "Then send me its link on Telegram whenever it changes
  materially. Same rule as before: if it is not on Telegram, it did not reach
  me."
acceptance: a material change to the map produces a message in
  production/outbox/ carrying the map's link and passing the register gate,
  and a NON-material change produces none; both outcomes watched, the
  accepting case being a real change to a real page
max_sessions: 1
status: READY 2026-09-06. HALF OF HIS ITEM 3 IS UNDELIVERED and this is the
  half. P1: he asked for it in the same breath as the map itself.

## The finding, and it is CLAUDE.md rule 6

`tools/map.py` computes and prints the detector exactly as ruled:

    mapDigest=6f848e188ea7 mapDigestPrev=6f848e188ea7 mapMaterialChange=no
    mapChangedFields=none

The rule is coded rather than judged: three field groups are material, the
runnable set with its labels and on-his-PC states, each area's state word, and
the ordered next-three. A regenerated timestamp is not a change. The previous
state is read out of the page's own HTML comment, so there is no sidecar to
lose and it behaves the same on the PC and in a CI checkout. Its selftest
proves all three change kinds and proves the timestamp does not.

    grep -rn "mapMaterialChange" --include=*.py --include=*.yml .

returns hits in `tools/map.py` and NOWHERE ELSE. Nothing reads the key.

BUILT IS NOT RUNNING. A feature is done when something calls it and a gate
proves the call happened. The detector is a good instrument that no consumer
has ever asked a question of, so the day the map changes materially, nothing
happens.

## What has to exist

A consumer that runs where the map is regenerated, reads `mapMaterialChange`
from the done line, and on `yes` writes a message into `production/outbox/`
with a register suffix, carrying the map's link and naming which of the three
field groups moved. `mapChangedFields=q1/q2` is already printed for exactly
that sentence.

## Two things it must not do

It must not send on `nothing-measured`. That value means no previous page was
found, which is a first run, not a change, and the distinction is deliberate.

It must not equate an outbox file with a delivered message. Queue 127's
neighbouring lesson applies: nothing has ever reached his phone, and the
receipt in `production/outbound/` is the only evidence of delivery.

## The dependency

Worth stating plainly: this is worth building even though the Telegram bot has
never run, because the message being ready is the half the studio owns. But it
cannot be PROVEN until the bot runs, and a green selftest here must not be
reported as "he will be told".
