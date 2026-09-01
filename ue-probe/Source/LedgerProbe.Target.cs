// UnrealBuildTool target for the D1 probe. C# by UBT's convention, and it
// lives OUTSIDE ledger/Assets so the Unity-layer linters never see it: those
// tools parse C# expecting Unity idioms, and a UBT target file would read to
// them as a malformed Game-layer type.
using UnrealBuildTool;

public class LedgerProbeTarget : TargetRules
{
	public LedgerProbeTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Program;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		LinkType = TargetLinkType.Monolithic;
		LaunchModuleName = "LedgerProbe";
		// A console program, not a game: no engine, no editor, no renderer.
		// The point is to time an EDIT-BUILD-TEST cycle on ported logic, and
		// linking the whole engine would measure the engine's link time
		// instead of ours.
		bBuildDeveloperTools = false;
		bUseMallocProfiler = false;
		bCompileAgainstEngine = false;
		bCompileAgainstCoreUObject = false;
		bCompileAgainstApplicationCore = false;
		bIsBuildingConsoleApplication = true;
	}
}
