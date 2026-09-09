line: instrument (the z-fight reading)
spec: Three fixes in tools/grate-zfight.py. (i) rects_from_verdict reads
  grateRectStatus before it reads grateSubjectRectFrac and grateControlRectFrac, and
  refuses with that status named when it is not MEASURED. (ii) the tool says which
  reach its rectangles cover, because they sit wholly inside the channel course and the
  carriageway strip is unmeasured. (iii) rect_px snaps the control's integer size to
  the subject's within 1 px and keeps refusing beyond that.
acceptance: an OFF-FRAME pair refuses with OFF-FRAME named rather than with a
  mismatched-area message, and a 1-px integer-rounding difference no longer refuses,
  proved by a fixture in both directions
max_sessions: 1
status: READY 2026-09-09. Amendment A5 of
  game-design/decision-2026-09-09-the-railing-in-the-line.md, filed here for the same
  reason as queue 176.
  ITEM (iii) IS ON ITS THIRD RECORD WITHOUT EVER BEING CARRIED OUT. It was amendment 4
  of game-design/decision-2026-09-09-grate-camera-and-zfight.md, which predicted the
  fault before the run: the tool rounds each rectangle's four fractions independently
  while the probe builds the control from the subject's own half-width, so the true
  sizes match and the integers need not. At about 94.6 by 62.8 pixels the odds both
  integer sizes agree are roughly one in three. The 03:55 ruling found it unapplied.
  It is unapplied still.
  ITEM (i) IS THE ONE THAT CAN MISLEAD RATHER THAN REFUSE: an OFF-FRAME pair gets
  clamped by rect_px and then usually refused for a mismatched area, so the reader is
  told the wrong reason for the right refusal.
  THE STANDING RULE THIS ITEM EXISTS TO ENFORCE, written into the record on the night
  it failed twice: a non-blocking amendment is not recorded until it has a queue
  number, and a close-out that does not check for the numbers is how a ruling decays
  into a preference.
