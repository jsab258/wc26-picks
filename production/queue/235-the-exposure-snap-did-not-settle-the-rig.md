line: instruments
spec: Two photographs of one unchanged scene are the same picture, which the
  rig still cannot do, so that every cross-frame number it prints is void.
acceptance: rigDeterminism=IDENTICAL with rigDiffPixels=0/921600 on a run whose
  shot list contains both night and day conditions
max_sessions: 2
status: READY 2026-09-10 08:30Z. THE ACCEPTANCE TEST BUILT FOR THIS CAUGHT IT,
  which is the good half and the reason this is a queue item and not a disaster.

  THE READING, from the run on 83dec336:
    rigDeterminism=DIFFERS rigDiffPct=100.00 rigDiffPixels=921600/921600
    rigMeanLumaFirst=0.6102 rigMeanLumaRepeat=0.9562 rigMeanLumaDelta=+0.3460
    rigMaxAbsChannelDiff=177/255 rigRepeatOf=vign_camA_day rigRepeatAfterShots=25/25
  The FIRST shot of the run and the SAME camera and condition photographed again
  as the last thing the run does differ by a THIRD OF THE LUMA RANGE, on every
  pixel, with a worst channel difference of 177 of 255. That is not drift. That
  is a different picture.

  SO EVERY CROSS-FRAME NUMBER IN THIS RUN IS VOID, exactly as in run 38, and the
  twelve-cell sky grid CANNOT BE READ FROM IT. The whole point of the grid was
  to find the sky level, and the run that was supposed to answer it says its own
  numbers are not comparable. Nothing is concluded about sky level from this run.

  THE EXPOSURE SNAP DID NOT FIX WHAT IT WAS BUILT FOR. AutoExposureSpeedUp and
  SpeedDown at 10000 were landed to make adaptation instant. Adaptation is still
  visibly incomplete: five frames of twenty five are blown, at up to
  604972/921600 pixels clipped, and one frame is nearly black at 0.0623.

  THE ORDER IS THE EVIDENCE AND IT IS PARTIAL, stated as partial rather than
  rounded up into a theory. Blown frames sit at shots 3, 5, 10, 12 and 17.
  THREE OF THE FIVE IMMEDIATELY FOLLOW A DARK FRAME: shot 2 night 0.1112 then
  shot 3 at 0.9402; shot 4 night 0.0384 then shot 5 at 0.9591; shot 16 at
  0.0623 then shot 17 at 0.9695. That is the signature of an adaptation that has
  not come back from darkness. IT DOES NOT EXPLAIN SHOTS 10 AND 12, which follow
  ordinary day frames at 0.6241 and 0.6203, so the mechanism is not established
  and a second cause is live.

  WHAT NOT TO DO. Do not raise the snap speed again on the strength of this: the
  rate is already 10000 and the fault survived it, so the next change must be
  read off a printed series rather than guessed. Do not reorder the shot list to
  avoid dark frames, which hides the fault rather than fixing it and would also
  break C6's requirement that shot order is not monotone in sky.

  THE HONEST NEXT RUNG is to pin the exposure rather than its rate, which needs
  AutoExposureMinBrightness and MaxBrightness set equal, and which queue 219
  already names. The cost is that the rig can then never judge an adaptation
  moment, and that cost was accepted in writing when the rate was snapped.
