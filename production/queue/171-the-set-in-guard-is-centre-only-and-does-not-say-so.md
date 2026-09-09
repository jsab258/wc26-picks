line: instrument (the street emitter's own guard)
spec: The set_in guard in ledger/Assets/Scripts/Core/StreetVignette.cs states its scope
  in its own message and, if it is to be a footprint check, reads the edge under the
  footprint rather than under the centre alone.
acceptance: a set_in prop whose centre is over the channel and whose footprint hangs
  over the kerb is either accepted with the overhang NAMED or refused, and the guard's
  message says which of those two things it is doing
max_sessions: 1
status: READY 2026-09-09. Amendment A8 of
  game-design/decision-2026-09-09-the-grate-rises-flush.md.
  THE GUARD, added the same night, throws by name if a set_in prop sits over anything
  but the carriageway or the channel, which is right and fail-closed. IT READS THE EDGE
  GroundAt RETURNS AT THE PROP'S CENTRE. So a prop whose centre is over the channel and
  whose footprint hangs over the kerb passes, WHICH IS EXACTLY WHAT THIS GRATE DOES,
  by 75 um.
  WHY THAT MATTERS MORE THAN 75 um: a set_in prop is DELIBERATELY NOT FOOT-PROBED, by
  the scene file's own rule, because a grate straddles the step between carriageway,
  channel and kerb recess by design and a foot probe over it reports the step as a
  fault. So this guard is the ONLY footprint check a set_in prop ever gets, and it is
  not one. A guard whose scope is narrower than its name is the class this project
  keeps finding: it is not wrong, it is misread, and it is misread because nothing in
  its message says centre.
