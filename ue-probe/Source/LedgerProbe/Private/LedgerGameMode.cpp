#include "LedgerGameMode.h"

#include "LedgerCharacter.h"
#include "VignetteShot.h"

#include "GameFramework/DefaultPawn.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

ALedgerGameMode::ALedgerGameMode()
{
	DefaultPawnClass = ALedgerCharacter::StaticClass();
}

void ALedgerGameMode::InitGame(const FString& MapName, const FString& Options,
                                FString& ErrorMessage)
{
	Super::InitGame(MapName, Options, ErrorMessage);

	// THE THREE SWITCHES THAT ALREADY OWN A RUN. -LedgerVignette times a
	// whole engine frame over exactly 593 pieces and -LedgerShot times the
	// same capture path on debug geometry; a second, collision-enabled
	// street built here for either one would double the actor count under
	// a number this project already compares against Unity's, and a
	// ticking Character in either frame is a cost that comparison has
	// never carried. -LedgerGoldenTest wants no world at all. Any of the
	// three restores exactly what an UNSET game mode handed the engine
	// before this file existed: ADefaultPawn, and no street built from
	// here (the automation still builds its own, on its own ticker, from
	// LedgerVignetteShot::Start()).
	const bool bAutomationRun =
		FParse::Param(FCommandLine::Get(), TEXT("LedgerVignette")) ||
		FParse::Param(FCommandLine::Get(), TEXT("LedgerShot")) ||
		FParse::Param(FCommandLine::Get(), TEXT("LedgerGoldenTest"));
	if (bAutomationRun)
	{
		DefaultPawnClass = ADefaultPawn::StaticClass();
		return;
	}

	// A PLAIN LAUNCH: the ONE case this game mode acts on. The street is
	// built here, synchronously, before any player logs in, rather than on
	// the core-ticker LedgerVignetteShot::Start() uses for the automation
	// path, because InitGame runs before PostLogin/RestartPlayer in every
	// case UE defines. That ordering removes the race a ticker armed at
	// module PostConfigInit would otherwise run against "has the map
	// finished loading and has a player been restarted yet": this call
	// cannot lose that race because the thing it would be racing has not
	// started when InitGame runs. See VignetteShot.cpp's
	// BuildInteractiveStreet for what it builds and how it lights and
	// starts the player.
	LedgerVignetteShot::BuildInteractiveStreet(GetWorld());
}
