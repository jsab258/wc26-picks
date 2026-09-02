using UnrealBuildTool;

public class LedgerProbe : ModuleRules
{
	public LedgerProbe(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		// A game module's minimum. Every dependency beyond these is time
		// added to every cycle this project exists to measure.
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
		// ImageWrapper DECODES THE STILL THIS PROBE COMMITS, and it is the
		// difference between a measurement and a file-exists check. Task 007
		// step 2 has to prove a frame is not blank, which means reading its
		// pixels back out of the artifact that will be committed rather than
		// trusting that a call returned. Private, because nothing outside
		// this module needs it, and named here so the cost of the extra
		// module is visible in the build numbers D1 is comparing.
		PrivateDependencyModuleNames.AddRange(new string[] { "ImageWrapper" });
	}
}
