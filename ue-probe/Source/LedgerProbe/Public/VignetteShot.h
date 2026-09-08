// PHASE B: THE STREET, IN UNREAL, PHOTOGRAPHED FOUR TIMES.
//
// One entry point, armed from StartupModule when the command line carries
// -LedgerVignette and never otherwise. A module loads in every host that
// loads it, including the cook commandlet's editor, and run 12 lost a cook
// to a module that did work it was not asked to do.
#pragma once

// CoreMinimal RATHER THAN Containers/UnrealString.h ALONE, since 8
// September: SpawnProbePiece below takes FVector, which is a template alias
// (UE::Math::TVector<double>) in UE5 and therefore cannot be forward
// declared the way UWorld and AActor are. Every translation unit that
// includes this header already includes CoreMinimal.h itself, so this adds
// nothing to any compile that was not already there.
#include "CoreMinimal.h"
#include "Containers/UnrealString.h"

class UWorld;
class AActor;

// THE MESH PIECE KIND, AND WHAT OWNS WHICH HALF OF IT.
//
// A piece of shape "mesh" in production/specs/vignette-pieces.json names a
// held prop in its `asset` field. Twenty-three pieces do, over sixteen assets.
// Until 8 September every one of them was drawn as a BOX of the prop's own
// stated size, counted on the scene line as propStandIns.
//
//   tools/ue/import_prop_meshes.py   makes one static mesh per asset in a
//                                    build step (.github/workflows/
//                                    ledger-mesh-import.yml), at
//                                    /Game/Ledger/Props/SM_<asset>, with
//                                    simple collision, and commits the
//                                    uassets. Never a human in an editor.
//   VignetteShot.cpp's mesh branch   derives that path from the piece's
//                                    `asset` field and NOTHING ELSE, places
//                                    the loaded mesh's own bounds centre at
//                                    the piece's x/y/z at scale 1, and falls
//                                    back to the box when the path resolves
//                                    to nothing.
//
// THE TWO HALVES AGREE BECAUSE A GUARD IN THE CONTAINER SAYS SO: the path is
// built from kPropPackageDir and kPropNamePrefix in VignetteShot.cpp, and
// import_prop_meshes.py --selftest reads those two literals out of that file
// and compares them to its own constants before any dispatch. A path this
// engine builds and nothing resolves returns null in silence.
//
// WHAT THE SCENE LINE NOW SAYS ABOUT IT: propsAsMesh=N/23 and propsAsBox=N/23
// with propFallbackWhy beside them, propCentreWorstMm for how far the worst
// placed mesh's world bounds centre is from the point the file named, and
// propCollisionPrims for the count the walk clip lives on. propStandIns is
// now the FALLBACK count and not the mesh-kind count, so 0/23 means every
// prop in the frame is a real mesh.
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

	// THE CRIME PROBE'S TWO, ruling of 2026-09-08 sections 2 and 4. See
	// VignetteShot.cpp for what each does and why the probe's pieces are
	// kept in a map of their own.
	//
	// ONE HELPER, NOT FIVE: shards, a brick, two stand-in bodies and a yard
	// floor, all placed through the SAME SpawnPiece the 593 street pieces go
	// through, with bInteractive=true. CentreM and SizeM are in the SHARED
	// FILE'S FRAME (x along, y up, z across), not the engine's. Registered in
	// a separate map, so piecesEmitted=593/593 and every vignette counter is
	// untouched by anything spawned here.
	AActor* SpawnProbePiece(UWorld* World, const FString& Name,
	                        const FVector& CentreM, const FVector& SizeM,
	                        const FString& Shape, const FString& Surface);

	// The reverse of FindStreetPiece: the name a hit actor was spawned
	// under, or an empty string when it was not spawned by this module.
	// READ-ONLY. A packaged build gives a spawned StaticMeshActor no label
	// (SpawnPiece calls SetActorLabel under WITH_EDITOR only), so without
	// this an occlusion reading can only name StaticMeshActor_NNN, which
	// names nothing anybody can look up in vignette-pieces.json.
	FString StreetPieceNameOf(const AActor* Actor);
}
