// UnrealBuildTool target for the D1 probe.
//
// TWO BUILD FAILURES GOT US HERE AND BOTH ARE KEPT, because the second
// invalidated the whole shape rather than a setting:
//
//   attempt 1: "Targets with a unique build environment cannot be built with
//              an installed engine." Five engine-wide overrides removed.
//   attempt 2: "Program targets are not currently supported from this engine
//              distribution." Not a flag. An installed engine cannot build a
//              Program target AT ALL, and no amount of tuning one changes it.
//
// SO IT IS A GAME TARGET, AND THAT IS MORE HONEST RATHER THAN A CONCESSION.
// LEDGER would be a game, not a console program. A Program target linking
// almost nothing was never representative of the cycle D1 is trying to price;
// it was the cheapest thing to compile, which is a different thing from the
// thing worth measuring. The cold build gets slower because the engine is
// really linked now, and that slowness IS the measurement.
using UnrealBuildTool;

public class LedgerProbeTarget : TargetRules
{
	public LedgerProbeTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		// Explicit, because attempt 1 died on exactly this question.
		BuildEnvironment = TargetBuildEnvironment.Shared;
		ExtraModuleNames.Add("LedgerProbe");
	}
}
