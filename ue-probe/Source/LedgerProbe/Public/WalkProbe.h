// RULING 1 FROM JAFAR, 2026-09-07, VERBATIM: "I do not launch builds to see
// if they compile. The runner is on my PC; use it. Add a workflow step that
// launches the packaged build in automation, walks a scripted route through
// the street, captures a short clip and frames and judges them: does it
// launch, is there a street, is there a walking camera, are the test cards
// absent, is collision real." This module is that walk.
//
// One entry point, armed from StartupModule when the command line carries
// -LedgerWalk and never otherwise, exactly as the other three automation
// switches are (VignetteShot.h, LedgerProbe.cpp). -LedgerWalk is NOT one of
// the three switches ALedgerGameMode::InitGame checks, so a walk run falls
// through to the SAME branch a genuine human launch takes: the default
// ALedgerCharacter spawns, collision is on, and
// LedgerVignetteShot::BuildInteractiveStreet runs unmodified. See
// WalkProbe.cpp's own header comment for where each of the five judgments'
// numbers comes from.
#pragma once

namespace LedgerWalkProbe
{
	// Arms the walk on the core ticker and returns immediately. The engine
	// quits itself when the route finishes or a ceiling bites, and every
	// ceiling that bites is named in the verdict.
	void Start();
}
