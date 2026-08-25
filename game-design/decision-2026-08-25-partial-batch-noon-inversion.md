# Decision — batch commit, noon inversion, stale CLAUDE.md, yard_fence, brief shape, ref stills

> **STATUS — LOG, 2026-08-25. NOT CURRENT after the items below land.** It
> records the ruling, not the state. Banner reformatted by the resident for
> `docs-check`; not one word of the ruling changed, so the stamp still
> attests what it attested.

Director ruling against landing `71316fa` (clean: simTimedOut=no simExit=0,
verdict line 1 names the commit — checked). Evidence opened this session:
verdict.txt lines 1/87/88, both day-1 frames, `Core/ValuePanel.cs`,
`WorldBuilder.Letter` call sites, `SimDirector` ValuePanel wiring (20
references), `sim-shots-stage.sh:207` and `sim-shots-commit.sh:42` both
carrying `ref_*.jpg`, `queue.md` items.

NOTE: the original brief said the five cameras did not exist. The resident
corrected this mid-review and I verified the correction in code before
ruling — R1 is complete and wired. Ruling A below is against the true
state, and F is the decision the builder correctly declined to make.

## A. COMMIT THE BATCH NOW.

The rule-6 objection does not survive the call-site grep, which I ran:
`WorldBuilder.Letter` is NOT an uncalled helper — it is already the live
implementation behind `StreetFurniture.cs:635/663/762` and the fascia name
at `WorldBuilder.cs:1755`. The unification replaced running code and is
exercised on the next build. `ValuePanel` is a FINISHED instrument, not an
orphan panel: Core arithmetic under CoreTests, five player-height cameras
wired in SimDirector, both stills scripts carrying the new frames.

The cadence-(a) concern dissolves with the corrected premise: the next
dispatch carries five new frames and ten new done-line keys — a visible,
readable change. What remains partial is the nameplates half only:
helper landed, plates not placed. That resumed brief goes to the top of
`## Now` and rides the same dispatch. RESUMED, not restarted.

Also ratified from this batch: the builder's written prediction for the
first ValuePanel landing (`1of3` on dry noon stills, "if 3of3, suspect
the instrument first") is exactly the discipline rules 2 and 3 ask for,
and its twin-site catch (`refPlaced=5/5` with no committed `ref_*.jpg`)
was the grep-for-the-same-bug rule doing its job before a build paid.

## B. THE NOON-INVERSION READING: RATIFIED AS A NARROWING, WITH TWO EDGES.

I opened both frames. Night: correct — dark sky, dark ground, sodium
points, one amber pool. Noon: the sky reads darker than the ground, which
is inverted for ANY daylight including overcast — under overcast the sky
is the brightest thing in frame — so the finding of fault stands.

Two corrections before it drives work:
1. "Localises to the daylight path, away from FilmGrade generally" is a
   HYPOTHESIS, not established. Right-at-night/wrong-at-noon is equally
   consistent with a grade nonlinearity that only bites at daylight input
   levels. The ValuePanel series is precisely what distinguishes these;
   that is why the lever stays barred.
2. The noon frame is a RAINING frame under a storm dome. ValuePanel
   samples must carry the weather/sky state, or the series will mix
   regimes and no statistic will survive it (rule 2, regime change).

The restraint — lever barred until a printed series, aperture moves ONCE
off evidence — is exactly right. Ratified as written in queue.md.

## C. CLAUDE.MD: BOTH STALE SPOTS ARE RULED STALE. FIX BOTH.

(i) "Two candidate fixes, neither built" is false as of today: the
stronger candidate (the artifact test — a stamped RULING record newer
than the reference commit) is built, live in `director_cadence`, and has
now passed rule 5b in the wild on real events: it refused an actual
unreviewed batch (my own unstamped ruling) and accepted a stamped one.
Correct the paragraph by APPENDING the outcome with today's date, keeping
the original text quoted — this file's own convention: quote the error so
it cannot be re-derived.

(ii) The watchdog dailies check has the identical hole and gets the
IDENTICAL fix: it must test for a ruling artifact (`decision-*.md` stamp)
in the window, not a `studio-director` row. A row is attendance. Ruling:
move it to the artifact test, and implement it by CALLING the same parse
the commit gate uses — one implementation, not a twin missing a line
(rule 1, third corollary). A stamped ruling on any topic satisfies it;
that is acceptable, because what the watchdog guards is "the director
tier completes reviews", and a second bespoke record type is a second
thing to decay.

## D. YARD_FENCE: QUEUE ITEM, NOT A SHIP-BLOCKER FOR THE DRESSING CLOSE —
## BUT IT CANNOT SURVIVE THE VISUAL-BAR CLOSE.

Verified: 166/169 placed, 163 on the 3.52m 1x1, zero on 1x2/1x3, three
on 1x4. That is a monoculture and it is the "one lamp everywhere" tell.
It does not block the dressing close-out: the close stands on 736/739
zero-missed, and the alternative to 163 identical panels was zero panels.

First step on the queue item, and it is rule 3: SUSPECT THE PROBE. "The
yard-depth probe classifies nearly every site as shallow" is a claim
about the probe or about the yards, and nobody has printed the yard-depth
series to say which. Print the distribution of measured yard depths per
site; if the yards genuinely cluster at ~3.5m, the mid-length VARIANTS
are wrong for this town and the fix is content, not placement code.
Done looks like: at least three panel variants placed, per-variant counts
printed, no variant over ~70% of sites. Tie it to M17.10, where it IS
blocking.

## E. YES TO THE STANDING LINE; HOLD THE CEILING AT 70.

Three losses and every recovery pointing one way is a series; adopt it.
The standing line in every tier-3 brief: name the deliverable file path
in the brief's first paragraph, and the builder WRITES THE FILE before
finishing investigation — skeleton first, improve in place. Additionally:
a brief whose discovery is expected to eat more than half the budget gets
SPLIT — a discovery brief whose deliverable is the notes file, then a
build brief carrying those notes.

The ceiling stays at 70. The evidence says the lever is brief shape, not
budget: both raised-ceiling builders still stopped mid-task, so raising
again purchases more of the same failure mode. A builder that stops at 70
with the file written is a resume; at 90 with nothing written it is a
loss. Do not raise without a new measured reason.

## F. REF STILLS RIDE ALONGSIDE THE AERIALS FIRST; AERIALS ARE DEMOTED
## ONLY AFTER THE REPLACEMENT HAS LANDED A READING.

The builder was right to hand this up. Ruling in two steps:

1. NOW: the five `ref_*` frames ride alongside everything existing.
   +0.57 MB/commit is a real cost and it is accepted for the interim,
   because the alternative is retiring an instrument in the same commit
   that introduces its untested successor — the exact shape this project
   refuses ("any plan that begins by weakening an instrument"). The
   ref cameras have never committed a frame; until one lands and is
   READ, they are a claim.

2. AFTER the first landing in which the ref frames arrive and I (or the
   resident at review) confirm they frame what they claim: cut the
   aerials to ONE noon aerial per run, kept permanently as the layout
   witness. The overhead view is how blocks-over-open-sea and the fence
   monoculture become visible to a human; street height cannot see
   layout, so zero aerials is not on the table. Net storage after the
   cut is roughly neutral against the measured +115 KB/frame, and the
   judgement frames for the VISUAL BAR become the player-height set,
   which is where GTA-V-on-PS3 is judged anyway.

## NOT RULED ON

- The translucent light-cone pyramids visible in the night frame — an
  observation from my own reading, handed to the queue as a look, not a
  finding.
- The 2.35:1 exposure item and the ambient-fill work already queued.
- The stall (candidate B) beyond accepting this landing as its closure
  evidence — one clean run is one sample; the flaky tooling watches it.
- The Fable-usage share this session.
- The 5° pitch and standoff judgements inside the ref cameras — named by
  the builder, printed by `valueHorizon`; they get ruled on when the
  series exists, not before.

<!--RULING spawn=2026-08-25T20:43:22Z-->
