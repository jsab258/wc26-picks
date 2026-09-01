using UnrealBuildTool;

public class LedgerProbe : ModuleRules
{
	public LedgerProbe(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.NoSharedPCHs;
		PrivatePCHHeaderFile = "Public/LedgerProbe.h";
		// Core only. Every dependency added here is time added to every
		// cycle this exists to measure.
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "Projects" });
	}
}
