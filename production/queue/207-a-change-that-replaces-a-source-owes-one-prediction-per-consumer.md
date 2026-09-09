line: process
spec: A change that replaces a light, a source or any shared input writes ONE PREDICTION PER
  SURVIVING CONSUMER before it is dispatched, not one prediction per thing changed. Build the
  check that asks for them: given a change touching a named source, enumerate what reads that
  source and require the dispatch entry to name each one.
acceptance: the sky change of 2026-09-09 is the accepting fixture and must FAIL the check as
  it was written, because it named four predictions and no consumer; a rewritten entry naming
  the sun as a consumer passes.
max_sessions: 1
status: READY 2026-09-09, item D of
  game-design/decision-2026-09-09-ruling-the-sun-the-bootstrap-and-the-board.md section 3.4.
  THE INCIDENT IS ITS OWN BEST ARGUMENT. The sky dispatch carried four predictions written
  before the run and ALL FOUR HELD. It was still a miss, because the prediction SET was
  wrong: nothing asked what a captured sky does to a directional light tuned against three
  fills, and the sun went dark with every prediction green.
  THE FREE TELL, worth keeping in the check's own words: the bare literal in the file you are
  changing is the list of consumers nobody checked. kSunIntensityDay did not exist; 3.0f did.
