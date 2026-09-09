line: engine
spec: The directional light points where the spec asks it to point, and the run
  prints asked beside read for both axes so this can never recur silently.
acceptance: a run whose sun line reads asked -36.0/25.0 and read -36.0/25.0
  with a residual of 0.0 on both axes, and a shadow-edge step measured on the
  same frame that is no longer flat
max_sessions: 1
status: READY 2026-09-09 21:40Z. PROVEN BY ARITHMETIC ON COMMITTED FILES, not
  inferred. This is the largest single defect found on rung 1.

  THE SPEC ASKS FOR A SUN 36 DEGREES ABOVE THE HORIZON AND THE ENGINE RENDERS
  ONE AT 82.

    production/specs/vignette-pieces.json:16, at run 38's own commit 082f0a04
        "sun":{"elevation_deg":36,"azimuth_deg":205}
    VignetteSpec.h:563  SunPitchDeg(e)  = -e             asked pitch = -36.0
    VignetteSpec.h:558  SunYawDeg(a)    = Wrap360(a+180) asked yaw   =  25.0
    the committed verdict  sunPitchYawRead=-82.0/25.0

  YAW AGREES TO THE DECIMAL AND PITCH IS OFF BY EXACTLY 46.0 DEGREES. The yaw
  agreeing is what rules out coincidence and rules out the readback reading a
  different actor: one axis is untouched, the other is displaced by a constant.

  THE MECHANISM, and the fix does not depend on it being right.
  VignetteShot.cpp:1092 spawns GSun through SpawnDirectional, which hands the
  rotation to SpawnActor as the ACTOR rotation and never touches the light
  component. ShotLightNow at 2020 reads the COMPONENT world rotation. A
  constant -46.0 pitch offset at zero yaw offset is the signature of a
  component relative rotation composed under the actor's, and -46 is Unreal's
  default relative rotation on ADirectionalLight's light component, which
  SpawnDirectional never clears. Confirmed numerically through Unreal's own
  FRotator-to-quaternion formulas: actor(-36,25) composed with relative
  (-46,0,0) gives pitch -82.0 yaw 25.0, residual -0.0 on both axes. Whether
  -46 is truly the shipped default is UNVERIFIED here and does not matter:
  setting the component's world rotation explicitly is correct either way.

  WHAT IT COSTS. A 4 m lamp post casts 4/tan(36) = 5.5 m at the asked
  elevation and 4/tan(82) = 0.56 m at the rendered one. A FACTOR OF TEN IN
  SHADOW LENGTH. Queue 197, nothing casts a contact shadow, is explained
  exactly, and so is the sun ladder's shape: a hundredfold of sun moved the
  dark end by 1.06 nulls while blowing highlights by three orders of
  magnitude, which is what a light almost straight down does.

  IT IS NOT THE WHOLE STORY AND THE RECORD SAYS SO. The grid ruling's own
  series has the shadow-edge step at +0.0270 with three fills and no skylight
  and -0.0003 on the same pixels once the captured sky was added. The step was
  killed by ADDING THE SKY, one variable, in-frame. The sun has been at 82
  degrees on both sides of that change, so the sky is what killed the step and
  the elevation is a standing defect that caps how much shadow is available at
  all. Both are real and the run separates them.

  THE FAULT FAMILY IS TWO PARTIES AND ONE UNDOCUMENTED AGREEMENT. The readback
  printed the truth on every run since the key was written. NOBODY EVER
  DIFFERENCED ASKED AGAINST READ. The remedy is the same one the grid ruling
  imposes on the twelve conditions in its C5: print asked beside read, with the
  residual, and refuse rather than report when they disagree.

  ALSO CHECK THE THREE FILL LIGHTS at VignetteShot.cpp:1094 to 1096, spawned
  through the same helper and therefore carrying the same offset. They are
  retired to zero intensity so no pixel moves today, but a comment claiming a
  fill points somewhere it does not is a decayed claim waiting for whoever
  revives them.
