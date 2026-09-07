// PHASE B: THE STREET, IN UNREAL, PHOTOGRAPHED FOUR TIMES.
//
// One entry point, armed from StartupModule when the command line carries
// -LedgerVignette and never otherwise. A module loads in every host that
// loads it, including the cook commandlet's editor, and run 12 lost a cook
// to a module that did work it was not asked to do.
#pragma once

#include "Containers/UnrealString.h"

class UWorld;
class AActor;

namespace LedgerVignetteShot
{
	// Arms the capture on the core ticker and returns immediately. The
	// engine quits itself when the last shot is measured or when a ceiling
	// bites, and every ceiling that bites is named in the verdict.
	void Start();

	// QUEUE 138 ITEM 1: THE SAME STREET, BUILT FOR SOMEONE TO WALK IN
	// RATHER THAN TO PHOTOGRAPH. Called once, synchronously, from
	// ALedgerGameMode::InitGame, and only on a plain launch: InitGame
	// itself refuses to call this when the command line carries
	// -LedgerVignette, -LedgerShot or -LedgerGoldenTest, so this never
	// runs beside the automation and never adds a second street or a
	// ticking Character to a frame the automation's timing measures.
	// Enables collision on every spawned piece (the automation leaves it
	// off to save simulation time in a frame it is timing) and spawns one
	// APlayerStart at the shared file's own cam_A position, because this
	// project's rule against a hand-edited scene applies to a PlayerStart
	// exactly as it does to a wall.
	//
	// -LedgerWalk (WalkProbe.cpp) TAKES THIS SAME BRANCH AND IS NOT NAMED
	// HERE. InitGame's own switch check does not know -LedgerWalk exists,
	// so a walk run falls through to this call exactly as a human launch
	// does; that absence of a change is the thing keeping the walk probe
	// from disturbing either the interactive path or the three automation
	// switches above, and it is recorded here so the next reader of this
	// function does not go looking for a fourth branch that was never
	// added on purpose.
	void BuildInteractiveStreet(UWorld* World);

	// THE WALK PROBE'S THREE READS, QUEUE ###. Every one exposes a global
	// this file already maintains for the vignette path; none of them is
	// recomputed or re-derived for the reader, because a second copy of a
	// count is how two numbers meant to be one drift apart.

	// The scene line BuildScene already writes: piecesEmitted=N/M and
	// every count beside it, e.g. "sceneStatus=NOTHING-EMITTED
	// piecesEmitted=0/0" before any street is built. Read, not recomputed.
	FString StreetSceneLine();

	// How many control-quad actors THIS PROCESS actually spawned.
	// BuildScene only calls SpawnControlQuads when bInteractive is false,
	// and BuildInteractiveStreet always passes true, so this reads 0 on
	// the walk path by construction; it is exposed as a MEASUREMENT of the
	// running program rather than trusted as a fact about the source,
	// because a sentence about code is not a reading of it.
	int32 ControlQuadsSpawnedCount();

	// A spawned street piece, by the exact name vignette-pieces.json gave
	// it, or nullptr when the street was never built or the name is not
	// among its pieces. Returns the actor BuildScene actually spawned, so
	// a caller measuring its bounds reads the ENGINE's placement of it
	// (after scale and rotation), never the file's numbers a second time.
	AActor* FindStreetPiece(const FString& Name);
}
