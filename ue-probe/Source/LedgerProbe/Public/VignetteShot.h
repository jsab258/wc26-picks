// PHASE B: THE STREET, IN UNREAL, PHOTOGRAPHED FOUR TIMES.
//
// One entry point, armed from StartupModule when the command line carries
// -LedgerVignette and never otherwise. A module loads in every host that
// loads it, including the cook commandlet's editor, and run 12 lost a cook
// to a module that did work it was not asked to do.
#pragma once

namespace LedgerVignetteShot
{
	// Arms the capture on the core ticker and returns immediately. The
	// engine quits itself when the last shot is measured or when a ceiling
	// bites, and every ceiling that bites is named in the verdict.
	void Start();
}
