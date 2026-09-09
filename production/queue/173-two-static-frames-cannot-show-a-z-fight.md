line: instrument (the z-fight reading)
spec: The z-fight instrument compares renders that can actually differ when the depth
  test ties: a moving or dithered camera, two sub-pixel offsets, or a pair of frames
  from different world positions. And tools/grate-zfight.py says in its own value that
  a flicker of zero over a static pair rules nothing out.
acceptance: a planted tie is detected by the flicker half, not only by the speckle half,
  and the nothing-measured wording distinguishes "no tie" from "this pair could not
  have shown one"
max_sessions: 1
status: READY 2026-09-09. Found by reading the first real output rather than by review.
  THE RULING SAID flicker is the evidence and speckle is context, because the control
  rectangle sits at a different distance and angle over asphalt and all three
  differences reduce its speckle. That reasoning is right about the control and wrong
  about the pair: BOTH FRAMES COME FROM A CAMERA THAT DID NOT MOVE OVER STATIC
  GEOMETRY, so a depth-test tie is DETERMINISTIC and reproduces identically in both.
  Flicker of zero is exactly what a stable tie looks like.
  SO THE EVIDENCE HALF CANNOT FIRE ON THE CASE IT WAS BUILT FOR, and run 35 printed
  zfightFlickerFired=no over a pair that could not have shown a flicker whatever the
  depth test did. The tool is not wrong; its wording lets a reader take a structural
  zero for a measurement, which is CLAUDE.md rule 3b applied to a guard rather than to
  a count.
  THE SMALLEST HONEST FIX IS THE WORDING, and it costs nothing: a static pair prints
  the flicker densities with a note that a stable tie is invisible to them. The larger
  fix is a pair that can differ, and only that one turns the instrument into evidence.
