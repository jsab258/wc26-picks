using UnrealBuildTool;

public class LedgerProbe : ModuleRules
{
	public LedgerProbe(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		// A game module's minimum. Every dependency beyond these is time
		// added to every cycle this project exists to measure.
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
	}
}
