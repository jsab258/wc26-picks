// THE EDITOR TARGET EXISTS SO THE PROJECT CAN BE COOKED.
//
// Run 8's cook died in two seconds on "Editor target not found!". Cooking
// is not a build step in Unreal, it is a commandlet run inside the editor,
// so UAT refuses before it starts unless the project declares an editor
// target. Nothing about the game target was wrong; there was simply no
// second target for the tool to launch.
//
// It carries the same Shared build environment as the game target, for the
// same reason: an installed engine can only build shared-environment
// targets, and an installed engine is the configuration Jafar has and
// therefore the one D1 must measure.
using UnrealBuildTool;

public class LedgerProbeEditorTarget : TargetRules
{
	public LedgerProbeEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		BuildEnvironment = TargetBuildEnvironment.Shared;
		ExtraModuleNames.Add("LedgerProbe");
	}
}
