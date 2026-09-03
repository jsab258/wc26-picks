# DIRECTOR RULING — district re-aim batch, `valueRungs` family pooling, day5_noon perpendicular (26 Aug 2026)

> **STATUS: LOG, 2026-08-26. NOT CURRENT after the build carrying the
> re-aim lands and its Identity A/B and four alarms are read.**
> Triggers: builder-batch review before commit; a verifier-grade finding
> (B) needing a director call. Verified this session, not quoted: the
> `az = 34f` default and the `az = 0f` control override at
> `SimDirector.cs:11283/11316`; the c5a75c9 verdict line 92 — refs lit at
> 307/383/13/162/156 rays, `valueShots=23/23`, `valueRungs=30/53`,
> exactly FIVE district rows at `litnone@0` (hook, copper, downtown,
> strip, fairview) with ironside 37 and gullwing 82 lit rays; the family
> `sky` medians districts 0.371..0.425 vs refs 0.596..0.698, disjoint,
> gap 0.171; `lit>gnd` holds on refs 1/2/4/5 and fails only on ref_3
> (13 rays); the +68.0-per-camera / +340.0 total and 53→63 denominator
> arithmetic by hand; the day5_noon single perpendicular at
> `SimDirector.cs:12764`. NOT re-measured: the frontage ranking (copper
> 284m .. fairview 70m) — method named (`StreetMap.Blocks`,
> half-frustum, 120m), accepted as builder-measured; the downtown
> slot-25 replay of `BuildSkyline`. A grep-display artifact showing `/`
> for `///` was chased to ground twice by direct Read — the file is
> clean; noted so the next reader does not re-flag it.

## A. COMMIT AND DISPATCH — APPROVED.

The conditional this batch waited on resolved on the evidence side: three
refs that read zero now read lit wall, the weather identity summed to
23/23 exactly, no alarm fired, and the one miss (`lit>gnd` holding) is in
the direction of the subject being better than predicted — the instrument
confirmed, not excused. The change itself is one character of behaviour
with both controls byte-identical, two pre-declared identities either of
which voids the reading, four alarms that each name which way to suspect,
and the weak camera (fairview, 70m frontage, a third of its peers) named
BEFORE the build rather than after. That is the shape a re-aim of five
landed series has to have, and it has it. Commit after review, dispatch;
if other Game-layer work is ready inside this dispatch cycle it rides the
same build per the batching rule, but nothing waits on it.

The overturned "FOUR of seven" sentence: the verdict itself says five
(downtown is `litnone@0`), so the correction to FIVE is ratified — that
was rule-1 comment decay caught by replaying the artifact, which is the
system working.

One watch item, not a blocker: ref_3 carries 13 lit rays where its peers
carry 156–383. Any rung flip on ref_3 alone is thin evidence and should
be read against its ray count before being quoted.

**The separate-spawn trade is ratified.** Two agents killed by session
limits tonight, 329 finished lines, no file overlap with the in-flight
verify-footer work: banking green work immediately is the habit that has
made every rollback free. One extra spawn was the cheaper side.

## B. `valueRungs` — SPLIT BY CAMERA FAMILY, AFTER this build lands. RULED.

The finding is confirmed disjoint on the artifact (0.425 vs 0.596, gap
0.171). `sky`'s median is a function of camera family, so `sky>lit` asks
a different question of an aerial row than a street row, and a pooled
`valueRungs` is a statistic of nothing nameable — the instruments rule
("say what the number is a statistic OF") cannot be satisfied for it.

- **The tally splits into two keys, one per family, each with its own
  denominator. The pooled key RETIRES** — it is the sum of the two and a
  derived copy would be one idea twice. Caveat-and-keep is refused: a
  caveat lives in prose and decays; the split lives in the emit.
- **Sequenced AFTER this build, not inside it.** Identity B predicts the
  POOLED denominator at exactly 63; changing the instrument in the same
  commit as the subject change would confound the identity built to
  validate that change, and no plan begins by altering an instrument
  mid-measurement. Split in the next instrument batch, with the 26 Aug
  break already declared, which makes this the cheapest moment the
  series will ever offer.
- Until the split lands, the queued standing caveat holds: no pooled
  `valueRungs` is quoted as a street reading, by anyone, in any report.
- The builder's conduct — flagging the confound rather than acting on a
  cause it could not separate — is exactly right and is the precedent.

**Explicitly NOT ruled: the cause.** Height and occlusion are confounded
with pitch and one run at one weather tag cannot separate them. That is
a measurement to design, not a ruling to make, and it goes to the queue
as a named research task, not into anyone's comment as an explanation.

## C. day5_noon — QUEUE IT, NAMED. Do not fold it silently.

`SimDirector.cs:12764` takes one of the two perpendiculars, so for a
given eye and road the street camera can never face the other way down
the same street — the same disease as the district sign fault in a
different body, and rule 1's third corollary says this grep was owed the
moment the first fix worked. It does not ride this commit: it is a
different camera family with its own series, and it deserves its own
prediction-first treatment (which way SHOULD it face — sunward logic
says the lit choice is derivable, not arbitrary). It may well BE the
next camera pass; it enters that pass as a named queue item with the
frame it must fix, not as an unnamed passenger. Note for the fixer: once
lit, day5_noon joins the STREET family and belongs to the street tally
from B's split, never the aerial one.

## Not ruled on

- The cause of the family `sky` disjointness (see B — research task).
- The frontage metres and the slot-25 skyline replay (accepted with
  method named; not independently re-measured).
- The verify-footer work in flight — different files, different batch,
  its own review when it lands.
- Whether `lit>gnd` holding on the refs moves any visual-bar conclusion
  — that reading belongs to the landed build, not to this ruling.

<!--RULING spawn=2026-08-26T01:29:12Z-->
