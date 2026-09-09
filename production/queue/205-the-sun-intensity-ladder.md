line: engine and art, jointly
spec: sun_intensity becomes a required field on Condition in ue-probe VignetteSpec.h, parsed
  beside Wetness, and used at VignetteShot.cpp:1240 in place of the bare literal 3.0f. One
  camera renders a ladder at 3, 10, 30, 100 and 300, plus ONE control row at sun 3.0 with the
  sky intensity down to 0.35, which tests the second suspect in the same run. The verdict
  gains sunIntensityRead, sunCastShadowsRead, sunPitchYawRead and sunMobilityRead, read OFF
  THE COMPONENT and never off the constant. tools/frame-shadow-probe.py gains --frame so one
  tool reads every rung.
acceptance: one committed run prints the shadow-edge step against sun intensity as a SERIES,
  and the series either shows a slope or it does not. A run that cannot show a slope does not
  set a constant.
max_sessions: 2
status: READY 2026-09-09, item B of
  game-design/decision-2026-09-09-ruling-the-sun-the-bootstrap-and-the-board.md section 3.1,
  UNBLOCKED at 15:36Z when the art render landed. Its ordering rule is the art lane's yield:
  the probe is a game workflow and starting it destroys any art render in flight.
  WHY A LADDER AND NOT THE FACTOR OF TEN A BUILDER PROPOSED. Auto exposure is in force and
  unoverridden, printed by the probe itself as
  ppNote=this-probe-overrides-nothing/cvars-are-what-is-in-force, so a tonemapped luma step
  can move far less than the light does. ONE SHOT AT 30 COMING BACK FLAT IS CONSISTENT WITH
  ALL THREE OF a dim sun, a bright sky and the tonemapper, and would settle nothing.
  MEASURED GROUND THE LADDER STARTS FROM: sun 3.0 against three directional fills bought a
  shadow-edge step of +0.0270; the same sun against the captured sky buys -0.0003.
  FALLBACK IF THE LADDER CANNOT BE BUILT: two shots, 3 and 30. Not one.
