# The picture batch — what Meridian needs, and what batch 1 proved

> **STATUS: SPEC.** Written 2026-08-26, the day batch 1's fourteen pictures
> first reached the repository and were opened. Every rule below is a reading
> of a specific file in `ledger/Assets/StreamingAssets/Decals/generated/`, not
> a preference. Supersedes nothing; the bar is `visual-bar-spec.md` and the
> sequence is Jafar's (visual first).

---

## 0. The one thing that decides whether any of this is worth running

**NOTHING IN THE GAME NAMES `Decals/generated`.** Grepped across all 186 Game
files: zero references. Fourteen pictures are in the repository and no code
loads one. Generating two hundred more changes nothing on screen.

That is rule 6 — built is not running — sitting in front of the whole batch,
and it makes the ORDER non-negotiable:

1. **Wire ONE picture into the street and see it in a committed frame.**
2. Then specify the batch.
3. Then run the batch.

Doing 3 before 1 is how a four-hour unattended run produces a folder nobody
looks at. `fascia_mickeys.png` is the candidate — it is the best picture in
batch 1 and it has an obvious home.

**WHERE IT GOES, read from the code rather than guessed.** Shop fascias today
are `StreetFurniture` building a plaster box at scale 2.6 x 0.34 x 0.06 and
lettering it with `WorldBuilder.Letter` (a `TextMesh`). A generated fascia
replaces the plaster material with the picture and drops the `Letter` call —
the geometry, the placement and the yaw already exist and are already correct.
So the wiring is small, and the picture is 1024x512 against a board whose
aspect is 2.6:0.34 = 7.6:1, which does not match and is the first real
question: either the board gets taller or the pictures get wider.

---

## 1. What batch 1 actually proved, by opening it

Four of fourteen read closely. **Two are usable, two are not, and the split is
not random — it is flat-on decals against tiling surfaces.**

| file | verdict |
|---|---|
| `fascia_mickeys` | **Excellent.** Gold signwriting on maroon, period lamps, tiled stallriser, `MICKEY'S` perfectly legible. At the bar. |
| `notice_ferry_times` | **Half.** `MERIDIAN FERRY` flawless; twenty timetable rows illegible. And it is a photograph of a sign in a street — post, kerb, shopfronts, depth of field — not a flat sheet. |
| `wall_soot_brick` | **Rejected.** Carries `Rao Hiau` in white on a dark brick, top right. The nonsense-signage fault, still live. |
| `wall_salt_render` | **Rejected.** A WHITE BORDER around the whole image — a framed picture of a wall, which tiles a white grid across every building. Also riveted metal cladding, not render. |

### The three rules that follow

**R1. BIG TYPE ONLY. A line of small text is a line of noise.** Measured on the
same picture: a two-word title at ~60px cap height is flawless and twenty rows
at ~10px are glyph-shaped marks. This is the model at this size, not a bad
seed — it reproduces Jafar's own reading of the first run. So a notice is
specified as a TITLE plus BLOCKS (a ruled grid, a dense paragraph read as
texture), never as rows a player is meant to read. **Anything a player must
actually read is real type set over a generated blank board**, which is the
only route to legible timetables and is a separate, cheap, deterministic job.

**R2. A SURFACE THAT TILES NEEDS A TILING CHECK, AND THERE ISN'T ONE.** The
blank check reads `wall_salt_render` at spread 242/255 and calls it healthy —
correctly, because it answers *is this picture blank* and nothing answers
*does this tile*. A border is a small fraction of the pixels; so is a seam.
**Build the check before the batch**: compare the first N pixel rows against
the last N (and the same for columns), report the edge difference per item,
and refuse an item whose opposite edges do not meet. The accepting fixture is
`fascia_mickeys` (which never tiles and should be exempt by kind, not by
luck); the rejecting fixture is `wall_salt_render`, which is on disk and free.

**R3. WALLS ARE NOT PROVEN AND MUST NOT RIDE A LONG RUN.** Both wall items
failed, in two different ways, and the negative channel that was supposed to
prevent one of them **has never once been tested against a frame that had the
fault** — see `prompts.json`'s probe notes for the full account of that
mistake. Until a wall comes back clean AND tiles, the batch contains fascias,
signs, notices and posters only. Walls get their own short experiment first:
**the same picture that failed, seed 8036 at 1024, with cfg 2.0 so the
negative is live.** One image, about two minutes.

---

## 2. What Meridian needs

Counts are for a town of seven districts. They are sized so no single item is
load-bearing — a picture that comes back wrong is dropped, not fixed.

**FASCIAS — the shopfront name boards.** The proven kind, and the one with a
home in the code. ~24: the pub, pawnbroker, fish market, laundry (batch 1's
four, already good), plus chandler, ironmonger, butcher, baker, greengrocer,
newsagent, betting shop, chip shop, cafe, barber, chemist, off-licence,
haberdasher, cobbler, tobacconist, garage, taxi office, funeral director,
amusement arcade, launderette. **In-world names only, no real trade marks, no
identifiable person** — the rules clause is in `prompts.json` and every prompt
carries it.

**SIGNS — the smaller mounted plates.** ~12: baths, marquee, `OPEN ALL NITE`
(batch 1's three), plus ferry, harbour master, weighbridge, public telephone,
gentlemen, left luggage, no waiting, private mooring, way out, taxis.

**NOTICES AND POSTERS — the paper layer, and R1 governs them.** ~16: dock
regulations, ferry board, gig bill (batch 1's three), plus tide table, fly
posters, missing cat, jumble sale, darts league, coach excursions, bingo,
council notice, planning notice, election bill, cinema bill, wanted notice,
church fete. **Every one specified as a bold title over blocks.**

**WALLS AND SURFACES — blocked on R2 and R3.** The list exists and does not
run yet: stock brick, painted render, pebbledash, glazed brick, dock concrete,
corrugated iron, terrace brick, rendered gable.

That is **~52 items** for the first real run, all of them the two kinds that
are already working, at roughly 100–290 seconds each on the measured card —
call it **three to four hours**, which is exactly the unattended shape the
sender was built for and has now been proven to deliver incrementally.

---

## 3. What must be true before the long run starts

Each of these is small and each has failed once already, which is why it is
listed rather than assumed.

- [ ] **One picture visible in a committed frame.** Not "wired" — *seen*.
- [ ] **The tiling check exists and both fixtures pass/fail as intended** (R2).
- [ ] **The aspect question settled**: board 7.6:1 against picture 2:1.
- [ ] **The wall experiment run** (R3) — one image, and it decides whether the
      wall list joins this batch or waits for the next.
- [ ] **A resumed run proven**: kill it halfway and restart, and it must skip
      what it made and continue. The skip path and the sender were BOTH wrong
      about this on 26 Aug — everything skipped, and not one picture pushed —
      so it is a watched behaviour now, not a believed one.

**Nothing here needs Jafar except the double-click.** Everything above is
authoring, checking and wiring on this side.
