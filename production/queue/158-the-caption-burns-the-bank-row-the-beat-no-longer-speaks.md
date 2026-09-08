line: instrument (the evidence channel)
spec: tools/clip-from-frames.py caption_for prefers lineText, un-tildes it, falls back
  to the bank only when lineText is absent or the none sentinel, and names the source
  it used in the reason, with a whole-run partition by source over frames examined.
acceptance: a frame captioned from what was SAID cannot read the same as a frame
  captioned from the bank, and the counts say which happened
max_sessions: 1
status: DONE 2026-09-08, landed in the same batch as the ruling that filed it.
  Amendment A4 of game-design/decision-2026-09-08-queue-147-the-composed-telling-and-the-clause-the-bank-never-had.md.
  MEASURED: clip-from-frames selftest 36 to 71 checks, 0 failures. The rejecting half
  of rule 5b was run by putting the fault back on a scratch copy: 52 passed, 17 failed,
  with the bank-fallback and refusal rows staying green, which is a guard that tells a
  regression from a fix. New keys clipCaptionsBySource, clipCaptionSpokenVsBank and
  clipCaptionTildeRuns, all printing nothing-measured when captioning never ran.
  THE NUMBER THAT SHOWS WHY IT MATTERED: on today's keys shape 8 of 25 frames are
  captioned and all 8 come from the bank; on the post-port shape all 8 disagree with
  the bank row. Before this change those two runs printed byte-identical evidence.
  ONE FINDING FOR WHOEVER OWNS THE STRIP: at 480x270 the strip holds 3 lines, the live
  bank's worst row wraps to 2, and the composed telling wraps to 3. Zero spare. No
  bound was changed; the printer ships and the next real run supplies the series.
