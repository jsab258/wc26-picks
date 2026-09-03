line: infrastructure (the imagegen evidence channel) and production (the scene's crops)
spec: this file, ordered by game-design/decision-2026-09-03-night-batch-of-2-september.md decision C, which keeps queue 056 OPEN until this lands
acceptance: (1) a usableFraction per image on the imagegen verdict, over a denominator of the batch, answering "does the artwork reach the edge of the frame" rather than "is it blank", with NO BOUND until a series has been printed; (2) the four wrong crop rectangles in production/specs/vignette-scene.json recomputed from the regenerated plates by measuring the artwork's extent, not by guessing
max_sessions: 1
status: READY 2026-09-03. engine-specialist. Carries the half of 056 that was not met.

## Why the crops are four and not ten

MEASURED, by applying every crop to its regenerated plate and looking at the
result, which is the only way this could have been known. SIX OF TEN ARE
STILL CORRECT and must not be touched: fascia_mickeys (MICKEY'S reads
perfectly), the three interiors (all three now show genuine interiors, which
is the interior rewrite working), notice_ferry_times and
notice_dock_regulations.

Wrong, and why:
- `fascia_fish_market`: the crop now returns blue tile with no lettering. It
  was cutting a fascia band out of a shopfront photograph and there is no
  photograph any more.
- `fascia_steam_laundry`: STEAM LAUNDRY reads correctly but is clipped top
  and bottom.
- `poster_gig_bill`: the headline is cut off at both edges.
- `fascia_ritas_pawn`: reads BRITHH WORIKER. THIS IS NOT A CROP FIX. It is a
  generation failure and its uv is to be left alone; regenerate the plate.

THE RESIDENT NEARLY DELETED ALL TEN. The first reading of this was "the
regeneration invalidated the crops, ten numbers to remove", stated to Jafar
before anything was opened. Looking first is what turned a destructive
instinct into four measurements. Rule 5, on a day it would have cost six
working crops.

## The measurement half

`usableFraction` answers the question the blank guard cannot: a picture can be
vividly non-blank and still be a photograph of a sign in a street. It has
nowhere to live today, which is why 41 of 45 images were wrong for weeks with
every gate green. No bound in this item: ship the printer, read runs, set the
number from evidence.
