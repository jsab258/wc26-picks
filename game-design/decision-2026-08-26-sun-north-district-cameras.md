# DIRECTOR RULING — sun-in-the-north finding, panel-repair batch, district cameras (26 Aug 2026)

> **STATUS — LOG, 2026-08-26. NOT CURRENT after the build carrying this
> batch lands and its ref-camera prediction is read.**
> Triggers: builder-batch review before commit; a landing that changes a
> conclusion (the noon sun is in the NORTH, so five of seven district
> cameras have been structurally blind to lit wall for their whole
> series). Verified this session, not quoted: the corpse-quote sweep for
> the false "due south" sentence — zero live copies; survivors are dated
> corrections at `tour-camera-resite.md:91`, `SimDirector.cs:10569` and
> `:10824`, and `convergence-instrument.md:623` is the SHADOW running
> south, which is the corrected physics, not a fifth copy. Also verified:
> `ValuePanel` prints `weather_unknown` in words on unrecorded weather
> (Core, `ValuePanel.cs:245`) with CoreTests pinning both the known and
> unknown case (`Program.cs:13891/13894`); `valueWeathers` emitted at
> `SimDirector.cs:16074`; `lint-static` now carries a walked set and a
> named skip ledger. The sunward arithmetic (`Euler(52,180,0)` →
> sunward `(0,+0.788,+0.616)`, lit needs wall-normal z ≥ 0.487) checks
> by hand. The 418→560 footer series and the district table figures are
> the resident's counts; mechanisms verified, arithmetic not re-measured.

## A. COMMIT AND DISPATCH — the batch is at its boundary. APPROVED.

The repair pass is complete inside the one-cycle cap the previous ruling
set. What makes it commit-worthy rather than merely done:

- The weather join is not a join — same statics, same `Shot` call, no
  time step — and the builder named the case a name-join gets silently
  wrong (the `street` row with no `frames.tsv` twin). That is the
  retraction's exact failure mode designed out rather than patched over.
- Unknown weather prints WORDS, never `r0.00w0.00`. Zero is DRY, and
  dry-vs-wet caused the retraction; a zero here would be the §3b disease.
- The selftest re-pin (`day1_noon` → `day5_noon`) is RATIFIED as a
  fixture correction, not a gate move: `day1_noon` only read right at
  `wet=1.00`, so the old fixture pinned a wet-confounded frame. The
  builder applying the director's retraction to its own test is the
  conduct we want; the justification is in the code, which is where the
  next reader is.
- The dispatch carries a prediction with an identity (regime shots sum
  to `valueShots`' numerator) and named alarms (`3of3` on a re-aimed
  camera indicts the instrument, not the aim). That is what makes this
  build an answer rather than a look.

One build, everything batched: panel repairs, re-aims, aerials. Dispatch
after commit, one at a time per the licence-seat rule.

## B. DISTRICT CAMERAS: RE-AIM ALL FIVE — but only AFTER this build
confirms the ref prediction. The landed series does not outweigh a
structurally blind instrument, and two controls survive the break.

The core fact: this is not flakiness or a rare miss. In an axis-aligned
town with the noon sun in the north, a north-facing camera can NEVER
sample a lit wall at noon. The lit column of those five series is not
data — it is `gates.py --constant`'s case wearing a panel: a reading
that has never moved, for a structural reason, aimed there by a false
sentence. A series produced under a false premise is honest about what
it looked at, but what it looked at was chosen by the falsehood. Rule
5b's corollary applies: plant the condition; never keep a blind probe
for the sake of its history.

What the series is genuinely worth: the NON-lit columns (sky, ground,
shadow bands) are real measurements of the old framing. A re-aim breaks
all of them at once. That cost is made affordable by the two cameras
this ruling explicitly does NOT touch: **Ironside and Gullwing stay
exactly as they are.** They already see lit wall (36 and 88), their
series spans the break, and they become the controls — any cross-break
shift that also appears in Ironside/Gullwing is the world changing; a
shift only in the re-aimed five is the re-aim. Without them the break
would be unreadable; with them it is cheap.

**Sequencing, and it is the decisive part:** the five ref re-aims in
this build are the same mechanism at one-fifth the price. If `ref_1`/
`ref_4` come back with `lit` non-empty, the mechanism is confirmed on
evidence and the district re-aim is dispatched next cycle as a declared
regime change. If a re-aimed ref still reads `litnone@0`, the fault is
NOT the aim, and re-aiming five district cameras would have voided five
series to fix the wrong thing. One build separates those worlds. Wait
for it.

**What the reader of the old rows must be told**, written into the
panel README and the camera code comments at the re-aim commit, in
these terms:

1. The pre-break lit column for these five cameras contains NO
   information. Not "walls were unlit" — the instrument could not see a
   lit wall at noon, ever, by geometry. Any past conclusion quoting a
   district lit reading from these five is void and should be re-derived
   from Ironside/Gullwing rows only.
2. All other pre-break columns describe the OLD aim and may not be
   compared across the break. The break commit is named in the comment.
3. Ironside and Gullwing are the only cross-break comparators, and that
   is why they stay untouched.

## C. `lint-nested` AND `lint-shadow`: ONE NAMED QUEUE ITEM, next
non-CI builder slot. Not this batch — the batch is at its cap and
neither lint is currently convicting or acquitting anything falsely
that we know of; the fault is legibility, not a red.

Both fixes copy the `lint-static` model just landed: print the walked
denominator, name the drop with its reason. For `lint-shadow`
specifically: capture the glob ONCE and derive both the scan and the
print from that one set — one line carrying two moments is the
same-instant rule applied to a log line, already written into rule 2.
Selftest both ways per 5b, live codebase as the accepting fixture.

**The meta-fix rides the same item:** the sweep that found these two
must state its own denominator — N lint tools examined, by name. "Six
others were checked and are clean" was true of an earlier sweep and
this one found two more, which means the earlier sentence is now
exactly the kind of quoted-forward claim §D below is about.

## D. THE SUN FINDING'S PROCESS CONSEQUENCE: one dated sentence added
to rule 1's second corollary, plus a standing verifier task. No new
rule number.

What actually failed: the existing corollary triggers on TOUCHING code
— re-read the comments on what you changed. This sentence was never
edited, only quoted, so no trigger ever fired; four copies propagated
and aimed five instruments. The corrective grep worked the moment it
was run — the token existed — but nothing made anyone run it.

What actually caught it: an instrument printed `litnone@0` and someone
asked why a probe never fires. That is the 5b corollary and the
`--constant` idea doing their job — the catch mechanism already exists
and it is the one that works without anyone remembering anything.

So, two consequences, both cheap:

1. **CLAUDE.md, rule 1 second corollary, one dated sentence:** a
   comment is also QUOTED FORWARD, and correcting the original does not
   correct the copies — when a claim is falsified, grep for the
   SENTENCE across docs and comments, not just the code site, because
   the copies were never touched and never will be. (Resident applies;
   keep it to the one sentence — the file teaches by incident and this
   incident is already named in the ruling record.)
2. **Standing tier-2 task:** extend the `--constant` sweep's scope to
   per-camera panel bands — a band that has never left zero across a
   camera's whole series is an accusation against the camera's AIM or
   premise, not just its wiring. That is the mechanism that caught this
   one, made standing instead of lucky.

No broader "every factual sentence must cite its measurement" rule: it
has no trigger point, and this file's own history says an untriggered
rule decays into decoration.

## NOT RULED ON, by name

- Any visual lever — albedo, aperture, grade, smoothness, fog. The
  "grade settled, aperture open" position stands; nothing here moves it.
- Whether the ref prediction lands, and `ref_5` in particular — that is
  the build's answer, read at the landing, alarms as specified.
- District camera POSITIONS. Only aim is ruled; if any re-aim turns out
  to need a re-site, it comes back as its own question.
- The `valueRungs` pooled-regime wording — adequacy is the
  measurement-auditor's next sweep, not asserted here.
- Implementation detail of the two lint fixes — builder's call,
  reviewed at its own batch.
- The 418→560 footer arithmetic and the district table counts — quoted
  as the resident's; mechanisms verified, numbers not re-measured.
- Anything Jafar-facing; nothing here needs him.

<!--RULING spawn=2026-08-26T00:33:50Z-->
