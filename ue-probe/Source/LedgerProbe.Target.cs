// UnrealBuildTool target for the D1 probe. C# by UBT's convention, and it
// lives OUTSIDE ledger/Assets so the Unity-layer linters never see it.
//
// BUILD ATTEMPT 1 FAILED HERE, AND THE ERROR NAMED THE RULE EXACTLY:
// "Targets with a unique build environment cannot be built with an installed
// engine." A launcher-installed Unreal ships prebuilt engine binaries, so it
// can only build targets that use the SHARED build environment; the moment a
// target changes an ENGINE-WIDE setting it needs the engine recompiled, which
// an installed engine will not do.
//
// The first version set bCompileAgainstEngine, bCompileAgainstCoreUObject,
// bCompileAgainstApplicationCore, bBuildDeveloperTools and bUseMallocProfiler
// to trim what gets linked. Every one of those is engine-wide, and together
// they were the unique environment. They are gone; the defaults for a Program
// target already exclude the engine, so the trimming was buying almost
// nothing and costing the entire build.
//
// This is not a workaround. Jafar's machine has an installed engine and that
// is the configuration D1 is measuring, so a target that only builds against
// a source engine would be measuring a machine nobody has.
using UnrealBuildTool;

public class LedgerProbeTarget : TargetRules
{
	public LedgerProbeTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Program;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		// EXPLICIT, not inherited: the whole failure was about which
		// environment this target asks for, so it says which one out loud.
		BuildEnvironment = TargetBuildEnvironment.Shared;
		LinkType = TargetLinkType.Monolithic;
		LaunchModuleName = "LedgerProbe";
		bIsBuildingConsoleApplication = true;
	}
}
