# Voice casting — superseded sections

> **STATUS — LOG, 2026-07-31. NOT CURRENT.** Sections cut out of the live
> casting doc and the design doc once they had been overtaken: a first
> round of picks that the British decision voided, an accent map that a
> later one replaced, a sourcing total revised twice, and the design doc's
> diary entry for 2026-07-29. Kept because the reasoning is worth having.
> **For who is actually cast, `voice-casting.md`.**

## 19. What changed on 2026-07-29 (and what it means for this document)

`roadmap.md` carries the build state; this section records only what
affects the DESIGN as written above.

**§6 systems — the street now shows the gossip.** Pairs stop, square off
at conversational distance, and break off when the player walks up if the
talk was about him. That is the first time the belief network has been
visible without opening a panel, and it is the single largest change to how
§2's premise reads in play.

**§6 — suspicion now becomes behaviour in a verified build.** Someone at
0.80 steps into the player's path; someone at 0.50 compares notes with a
neighbour. Both were written long ago and neither had ever executed.

**§14 agency — violence is still not a verb, and that is now an explicit
open decision** rather than an implicit deferral. See
`decisions-pending.md`.

**§15 production — the mocap line is optional, the Mixamo line is not.**
Motion matching is built and waits on a corpus that Mixamo does not sell;
Mixamo's free models and clips remain the outstanding animation item and
cost nothing.

**§8/§17 — nothing in the fiction changed.** No character, place, act or
ending was altered. The work was the layer between the writing and the
screen, which is exactly where this document said the gap was.


---

## PICKS — round 1, VCTK, 2026-07-31

Jafar's choices from the thirty candidates. Recorded here rather than left in
a browser's local storage, because the page's copy button did not work and a
decision that exists only on one phone is not a decision the project has.

| character | take | notes |
|---|---|---|
| Lena | candidate-01 | |
| Sam | candidate-05 | |
| Sera Kest | candidate-05 | |
| crowd — male, young (`crowd_m1`) | candidate-01 | |
| crowd — female, young (`crowd_f1`) | candidate-01 | |

**Five of nineteen cast.** The remaining fourteen had no candidates to choose
from — see `decisions-pending.md` for why and what the options are.


---


---

## ACCENT MAP v2 — english base (2026-07-31)

Supersedes the American table above. The city is British; see
`setting-britain-2026-07-31.md` for why and what else it changes.

| character | accent |
|---|---|
| Lena | english |
| Rocco | english |
| Mara Ellis | english |
| Tobias Reese | english |
| Sera Kest | english |
| Sam | scottish |
| Ada | english |
| Vesna | northernirish |
| Marla | english |
| Joey | scottish |
| Rita | scottish |
| Hal | english |
| Father Emil | irish |
| crowd m1/m3, f1/f3 | english |
| crowd m2, f2 | scottish |

**The round-1 picks are void.** Lena 01, Sam 05, Kest 05 and both crowd picks
were filled by VCTK's American speakers — that exact filter is why only five
of nineteen filled at all. They are kept in `voice-candidates/` until the
replacement round lands, so there is something rather than nothing.


---

## Total to source — REVISED DOWN 2026-07-28, from 37 to 19

The three-clips-per-principal plan was written before the direction test
came back, and it is wrong in a way worth stating rather than quietly
fixing.

**Common Voice contributors read neutral sentences.** A "grave" clip is not
something that corpus contains, so the mood variants were never sourceable
from it in the first place. What the benchmark actually proved is that
**chatterbox's exaggeration control does moods** — Jafar heard it himself on
`same_line_BORED.wav` against `same_line_GRAVE.wav`.

So the reference clip decides **identity** and the exaggeration parameter
decides **direction**. One clip per character.

| | clips |
|---|---|
| 5 principals × 1 | 5 |
| 8 street × 1 | 8 |
| 6 crowd × 1 | 6 |
| **Total** | **19 clips, ~11s each ≈ 3.5 minutes of audio** |

Direction, as parameters rather than recordings:

| Stage direction | exaggeration |
|---|---|
| bored | 0.25 |
| neutral | 0.5 |
| warm | 0.6 |
| grave | 0.7 |
| urgent | 0.85 |

That table lives in `tools/voice-fetch/ledger_voice_fetch.py` so it exists
in exactly one place, and the fetcher writes it into `casting.json` beside
the clips.

---


---

## The five picks made on 2026-07-30 are void

They were selected with `accent="american"` as a hard filter, which in VCTK
matches only the handful of Americans in it. Under the British decision they
are the wrong accent. The listening was not wasted — it proved the pipeline end
to end and calibrated what usable quality sounds like — but the picks go back
in the pot.

**Delegated by Jafar 2026-07-28** ("you decide"). Engine is **chatterbox**,
decided on the direction test — see `production-plan-audio-art.md` §1i.
