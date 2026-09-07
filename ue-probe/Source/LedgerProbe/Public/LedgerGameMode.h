// THE GAME MODE FOR A PLAIN LAUNCH, AND ONLY FOR A PLAIN LAUNCH.
//
// Wired in as this project's GlobalDefaultGameMode
// (ue-probe/Config/DefaultEngine.ini), so it loads for every run of the
// packaged binary, automation included: an ini-selected game mode class
// cannot be conditioned on a command line switch. InitGame is where that
// condition is actually made: it checks the same three switches
// LedgerProbe.cpp already gates its own entry points on
// (-LedgerVignette, -LedgerShot, -LedgerGoldenTest) and does nothing
// street-related when one of them is present. The automation's own pawn
// class and street are its business, not this game mode's, and this game
// mode must not become a second writer of either.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "LedgerGameMode.generated.h"

UCLASS()
class ALedgerGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ALedgerGameMode();

	virtual void InitGame(const FString& MapName, const FString& Options,
	                      FString& ErrorMessage) override;
};
