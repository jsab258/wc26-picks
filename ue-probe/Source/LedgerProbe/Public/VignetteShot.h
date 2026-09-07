// PHASE B: THE STREET, IN UNREAL, PHOTOGRAPHED FOUR TIMES.
//
// One entry point, armed from StartupModule when the command line carries
// -LedgerVignette and never otherwise. A module loads in every host that
// loads it, including the cook commandlet's editor, and run 12 lost a cook
// to a module that did work it was not asked to do.
#pragma once

class UWorld;

namespace LedgerVignetteShot
{
	// Arms the capture on the core ticker and returns immediately. The
	// engine quits itself when the last shot is measured or when a ceiling
	// bites, and every ceiling that bites is named in the verdict.
	void Start();

	// QUEUE 138 ITEM 1: THE SAME STREET, BUILT FOR SOMEONE TO WALK IN
	// RATHER THAN TO PHOTOGRAPH. Called once, synchronously, from
	// ALedgerGameMode::InitGame, and only on a plain launch: InitGame
	// itself refuses to call this when the command line carries
	// -LedgerVignette, -LedgerShot or -LedgerGoldenTest, so this never
	// runs beside the automation and never adds a second street or a
	// ticking Character to a frame the automation's timing measures.
	// Enables collision on every spawned piece (the automation leaves it
	// off to save simulation time in a frame it is timing) and spawns one
	// APlayerStart at the shared file's own cam_A position, because this
	// project's rule against a hand-edited scene applies to a PlayerStart
	// exactly as it does to a wall.
	void BuildInteractiveStreet(UWorld* World);
}
