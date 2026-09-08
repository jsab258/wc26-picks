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
		//
		// InputCore NAMES FKey AND EKeys, which ALedgerCharacter binds
		// directly to (queue 138 item 1: the street's first playable
		// character). Engine almost certainly carries this already as a
		// transitive public dependency, but this project cannot compile
		// locally to prove that, so it is named explicitly rather than
		// trusted through a chain nobody here can see.
		PrivateDependencyModuleNames.AddRange(new string[] { "ImageWrapper", "InputCore" });
		// EXCEPTIONS OFF, AND THIS WAS PRE-RULED BEFORE THE BUILD THAT
		// NEEDED IT. A director reading the Core port on 2026-09-08 found
		// that Suspicion.h throws and CoreGolden.h compiles a try/catch into
		// a module that does not enable exceptions, and ruled the answer in
		// advance: compile the FactNull branch out and print
		// perceptionUnknownFns=4/FactNull-needs-exceptions, NEVER set
		// bEnableExceptions. The build then failed exactly there, with
		// "CoreGolden.h(834,4): error C4530: C++ exception handler used, but
		// unwind semantics are not enabled", and this line is the ruled fix
		// rather than a reaction to it.
		//
		// WHAT IT COSTS, so nobody reads a smaller number as a regression:
		// the four FactNull rows stop being answered and count as Unknown,
		// which the run says in words. Turning exceptions on instead would
		// change a compile setting for the whole module to keep four rows,
		// which is the trade the director refused.
		PublicDefinitions.Add("LEDGER_CORE_NO_EXCEPTIONS=1");
	}
}
