// PHASE B: THE SHARED STREET BUILT FROM THE SHARED JSON, LIT TWO WAYS, AND
// PHOTOGRAPHED FROM THE TWO NAMED CAMERAS.
//
// WHAT MAKES THE FRAME ADMISSIBLE, which is the only reason any of this is
// as careful as it is. D1b requires every object in each engine to arrive
// from one shared JSON through a generator, and forbids a hand-edited scene
// or a hand-made uasset. So: nothing here is authored. Every actor's class,
// position, size and rotation comes out of production/specs/vignette-pieces.json,
// which Ledger.Core wrote from production/specs/vignette-scene.json; the
// reader is VignetteSpec.h, which has no Unreal type in it and is compiled
// and RUN by g++ before this is ever dispatched. This file contributes
// actors, lights and pixels, and NOT ONE DIMENSION.
//
// THE FRAME CONVERSION, DONE ONCE, HERE.
//   The file's frame: x along the street, y up, z across with +z east; yaw
//   is a bearing from +x turning toward +z; pitch is about +x and positive
//   tips the +z end down; roll is about +z and lays a cylinder along the
//   street; sizes are FULL sizes in metres, not half extents; the position
//   is the CENTRE of the piece.
//   This engine: X forward, Y right, Z up, centimetres, and FRotator's
//   Pitch is about Y, Yaw about Z, Roll about X.
//   So (X,Y,Z) = (x, z, y) * 100, and
//      Yaw = yaw_deg, Roll = -pitch_deg, Pitch = roll_deg.
//   Each of those three lines was derived from the convention rather than
//   tried: the file's yaw takes +x toward +z, which under this mapping is
//   +X toward +Y and is exactly a positive Unreal yaw; the file's pitch
//   takes +y toward +z, which is +Z toward +Y and is a NEGATIVE Unreal
//   roll; the file's roll takes +x toward +y, which is +X toward +Z and is
//   a positive Unreal pitch.
//   THE COMPOSITION ORDER IS UNEXERCISED and the reader proves it every
//   run: counts.multi_rotation is 0, so no piece in this scene carries two
//   non-zero rotations at once and the two engines cannot differ on the
//   order they compose them in. The run PRINTS that count rather than
//   trusting it, because the day it stops being zero this comment is wrong.
//
// WHAT IS DELIBERATELY NOT HERE. No textures, no materials, no HDRI: Phase
// C owns those and an untextured frame is the honest state of Phase B. The
// twenty-three prop pieces are boxes of the prop's own stated size, counted
// and named as stand-ins on the verdict so nobody reads a placed box as a
// loaded model, and the twenty decals are flat quads for the same reason.
// The sky is black, which is a Phase C hole and is named on the scene line
// rather than left for a reader to notice.
//
// ONE OWNER PER GLOBAL, WHICH THIS PROJECT HAS PAID FOR TWICE. ApplyCondition
// below is the ONLY writer of the fog, the sun and the ambient fill, and it
// writes all three every time a condition changes. Two writers on one render
// setting is how a fog calibration was lost for a week.
#include "VignetteShot.h"
#include "VignetteSpec.h"
#include "FrameStats.h"

#include "CoreMinimal.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/DateTime.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformTime.h"
#include "Containers/Ticker.h"
#include "Modules/ModuleManager.h"
#include "UnrealClient.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/PointLight.h"
#include "Components/PointLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/ExponentialHeightFog.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"

#include <clocale>
#include <string>
#include <vector>

namespace
{
	using namespace LedgerVignette;

	// ---- the shot's dimensions, and what they are ----------------------
	//
	// 1280x720 is the Unity host's ShotWidth and ShotHeight, character for
	// character, because a pair judged at two resolutions is not a pair.
	const int32 kShotW = 1280;
	const int32 kShotH = 720;
	// THE SAME WARM AND TIMED COUNTS THE UNITY HOST USES, for the same
	// reason: the first frames after a condition change compile shader
	// variants, which is a real cost and not the one a comparison is about.
	const int32 kWarmFrames  = 8;
	const int32 kTimedFrames = 24;

	// CEILINGS ON A HANG, NOT TARGETS. Each one prints the phase it killed,
	// so a slow world and a world that never came cannot read alike.
	const double kWorldCeiling = 45.0;
	const double kFileCeiling  = 25.0;
	const double kSettleAfterCondition = 0.5;

	// UNITY POINT LIGHT INTENSITY IS NOT UNREAL CANDELAS, and this number is
	// the first value of a series that has never been printed. The file says
	// intensity 3.2 for a sodium lantern, which is a Unity number; this
	// engine's point lights are in candelas by default and in a unitless
	// legacy scale when told to be. The lights are set to Unitless so the
	// two numbers are at least the same KIND of number, and this gain is
	// what multiplies the file's value. Rule 2 forbids calling it anything
	// better than a starting point: no series exists yet, the verdict prints
	// the value applied, and the first night frame is what a bound comes
	// from.
	const float kLampGainUnitless = 1.0f;
	// AND THE FOG. Unity's fogDensity is an exponential-squared coefficient
	// per metre; this engine's height fog density is a different
	// parameterisation entirely. Named, applied, printed, and NOT called
	// equivalent.
	const float kFogDensityGain = 1.0f;
	// THE AMBIENT FILL. Unity's host sets AmbientMode.Trilight with a sky, an
	// equator and a ground colour; this engine has no ambient mode, so the
	// same three colours arrive as three directional lights from above, from
	// the side and from below. It is the same statement about ambient light
	// made with the tool this engine has, it needs no captured sky and no
	// asset, and it cannot come back black the way a sky light with nothing
	// to capture can. It is NAMED on the scene line as a model so nobody
	// reads it as a physical sky.
	const float kFillSky = 0.55f, kFillEquator = 0.35f, kFillGround = 0.18f;
	// HOW FAR A DECAL QUAD IS LIFTED OFF THE SURFACE IT SITS ON. Not in the
	// file: the file describes a decal, which has no thickness and no
	// z-fighting, and this engine is drawing it as a quad until Phase C.
	// One centimetre is a millimetre-scale artefact at any distance the two
	// cameras see, and it is printed so nobody has to find it in code.
	const float kDecalLiftCm = 1.0f;

	enum class EPhase : uint8
	{
		WaitWorld, Build, ApplyShot, Warm, Timed, Ask, WaitFile, Done
	};

	Spec        GSpec;
	std::string GSpecErr = "not-read";
	FString     GSpecPath;
	FString     GSpecTried;

	FTSTicker::FDelegateHandle GTicker;
	EPhase  GPhase       = EPhase::WaitWorld;
	int32   GTicks       = 0;      // cumulative ticker calls since armed
	int32   GPhaseTicks  = 0;      // ticks inside the current phase
	double  GStart       = 0.0;
	double  GPhaseStart  = 0.0;
	double  GLastTick    = 0.0;
	int32   GShotIndex   = 0;
	bool    GUseHighRes  = false;  // set once, after candidate A fails once
	bool    GTriedHighResThisShot = false;
	int64   GSizeTracker = -1;
	FString GAskedPath;
	FString GNote        = TEXT("none");

	std::vector<double> GFrameMs;                 // the current shot's series
	std::vector<std::string> GShotLines;          // one per shot, in order
	std::string GSceneLine = "sceneStatus=NOTHING-EMITTED piecesEmitted=0/0";
	std::string GArt;                             // ascii luma of the first frame that decoded
	int32 GWrote = 0, GBlank = 0, GNoFile = 0;

	AActor* GSceneRoot = nullptr;
	ADirectionalLight* GSun = nullptr;
	ADirectionalLight* GFillA = nullptr;
	ADirectionalLight* GFillB = nullptr;
	ADirectionalLight* GFillC = nullptr;
	AExponentialHeightFog* GFog = nullptr;
	ACameraActor* GCam = nullptr;
	TArray<APointLight*> GLanterns;
	TArray<APointLight*> GWindows;
	TMap<FString, AStaticMeshActor*> GByName;

	FString NoSp(const FString& In) { return In.Replace(TEXT(" "), TEXT("~")); }

	// MOBILITY LIVES ON THE ROOT COMPONENT, NOT ON THE ACTOR. AActor has no
	// SetMobility; AStaticMeshActor happens to, and a light does not. It is
	// not cosmetic: a spawned light defaults to a mobility that needs BUILT
	// lighting, and this project has no built lighting and never will in a
	// runtime-generated scene, so a static light would simply not light
	// anything and the frame would come back black with every count green.
	void MakeMovable(AActor* A)
	{
		if (A == nullptr) { return; }
		if (USceneComponent* Root = A->GetRootComponent())
		{
			Root->SetMobility(EComponentMobility::Movable);
		}
	}

	FString AbsProject(const TCHAR* Leaf)
	{
		return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), Leaf));
	}

	FString ShaFromCommandLine()
	{
		FString Sha;
		if (!FParse::Value(FCommandLine::Get(), TEXT("LedgerCommit="), Sha) || Sha.IsEmpty())
		{
			Sha = TEXT("SHA-UNKNOWN");
		}
		return NoSp(Sha);
	}

	// THE SPEC IS LOOKED FOR IN SEVERAL PLACES AND THE ONE USED IS NAMED,
	// exactly as the golden table is. A packaged build's ProjectDir is the
	// STAGED project, not the source tree, so one hard-coded location works
	// in exactly one of the two ways this binary gets run. Searching is
	// fine; searching silently is not.
	FString FindSpec(FString& OutTried)
	{
		TArray<FString> Candidates;
		Candidates.Add(FPaths::Combine(FPaths::ProjectDir(), TEXT("vignette-pieces.json")));
		Candidates.Add(FPaths::Combine(FPaths::ProjectContentDir(), TEXT("vignette-pieces.json")));
		Candidates.Add(FPaths::Combine(FPaths::LaunchDir(), TEXT("vignette-pieces.json")));
		Candidates.Add(FPaths::Combine(
			FPaths::GetPath(FPlatformProcess::ExecutablePath()), TEXT("vignette-pieces.json")));
		for (const FString& C : Candidates)
		{
			OutTried += TEXT(" ") + NoSp(FPaths::ConvertRelativePathToFull(C));
			if (FPaths::FileExists(C)) { return C; }
		}
		return FString();
	}

	UWorld* GameWorld()
	{
		if (!GEngine) { return nullptr; }
		for (const FWorldContext& Ctx : GEngine->GetWorldContexts())
		{
			if (Ctx.WorldType == EWorldType::Game && Ctx.World() != nullptr) { return Ctx.World(); }
		}
		return nullptr;
	}

	FLinearColor LinearFromGamma(double R, double G, double B)
	{
		// THE FILE STATES ITS COLOUR SPACE AND THIS ENGINE'S LIGHTS TAKE
		// LINEAR. The conversion is SrgbToLinear in the tested header, not a
		// pow(2.2) written here, and the verdict names both spaces.
		return FLinearColor((float)SrgbToLinear(R), (float)SrgbToLinear(G), (float)SrgbToLinear(B), 1.0f);
	}

	// ---- the street ----------------------------------------------------

	UStaticMesh* LoadShape(const TCHAR* Path)
	{
		return LoadObject<UStaticMesh>(nullptr, Path);
	}

	AStaticMeshActor* SpawnPiece(UWorld* World, UStaticMesh* Mesh, const Piece& P,
	                             const FVector& ScaleUU)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AStaticMeshActor* A = World->SpawnActor<AStaticMeshActor>(
			AStaticMeshActor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
		if (A == nullptr) { return nullptr; }
		// A SPAWNED StaticMeshActor IS STATIC MOBILITY AND CANNOT BE MOVED,
		// and a scene lit only by movable lights needs movable geometry
		// anyway: a static actor with no built lighting renders unlit.
		// Setting this BEFORE the transform is not optional.
		MakeMovable(A);
		UStaticMeshComponent* C = A->GetStaticMeshComponent();
		if (C != nullptr)
		{
			C->SetMobility(EComponentMobility::Movable);
			C->SetStaticMesh(Mesh);
			// CreatePrimitive-style collision is not wanted here: 593 bodies
			// cost simulation time in a frame this run is timing.
			C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			C->SetCastShadow(true);
		}
		A->SetActorScale3D(ScaleUU);
		A->SetActorLocationAndRotation(
			FVector(P.X * 100.0, P.Z * 100.0, P.Y * 100.0),
			FRotator((float)P.RollDeg, (float)P.YawDeg, (float)-P.PitchDeg));
#if WITH_EDITOR
		A->SetActorLabel(UTF8_TO_TCHAR(P.Name.c_str()));
#endif
		return A;
	}

	APointLight* SpawnPointLight(UWorld* World, const FVector& AtUU, const FLinearColor& Colour,
	                             float RangeM, float Intensity, bool bShadows)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		APointLight* L = World->SpawnActor<APointLight>(
			APointLight::StaticClass(), AtUU, FRotator::ZeroRotator, Params);
		if (L == nullptr) { return nullptr; }
		MakeMovable(L);
		UPointLightComponent* C = Cast<UPointLightComponent>(L->GetLightComponent());
		if (C != nullptr)
		{
			// UNITLESS RATHER THAN CANDELAS, so the file's Unity-shaped
			// number is at least the same kind of number. Named on the
			// verdict; not called equivalent.
			C->SetIntensityUnits(ELightUnits::Unitless);
			C->SetAttenuationRadius(RangeM * 100.0f);
			C->SetLightColor(Colour);
			C->SetIntensity(Intensity);
			C->SetCastShadows(bShadows);
		}
		return L;
	}

	ADirectionalLight* SpawnDirectional(UWorld* World, const FRotator& Rot, bool bShadows)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ADirectionalLight* L = World->SpawnActor<ADirectionalLight>(
			ADirectionalLight::StaticClass(), FVector(0, 0, 3000), Rot, Params);
		if (L == nullptr) { return nullptr; }
		MakeMovable(L);
		if (ULightComponent* C = L->GetLightComponent())
		{
			C->SetCastShadows(bShadows);
			C->SetIntensity(0.0f);
		}
		return L;
	}

	void SetDirectional(ADirectionalLight* L, const FLinearColor& Colour, float Intensity)
	{
		if (L == nullptr) { return; }
		if (ULightComponent* C = L->GetLightComponent())
		{
			C->SetLightColor(Colour);
			C->SetIntensity(Intensity);
		}
	}

	// BUILD THE WHOLE STREET ONCE. Every count is captured as it happens and
	// the denominator comes off the FILE, before any spawning, so a run that
	// dies halfway still prints what it was asked for.
	void BuildScene(UWorld* World)
	{
		int Boxes = 0, Cyls = 0, Planes = 0, Props = 0, Decals = 0, Skipped = 0, Emitted = 0;
		std::string Note = "none";

		UStaticMesh* Cube  = LoadShape(TEXT("/Engine/BasicShapes/Cube.Cube"));
		UStaticMesh* Cyl   = LoadShape(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
		UStaticMesh* Plane = LoadShape(TEXT("/Engine/BasicShapes/Plane.Plane"));
		// A MISSING BASIC SHAPE IS THE ONE FAILURE THAT WOULD LOOK LIKE AN
		// EMPTY STREET AND HAS NOTHING TO DO WITH THE STREET. The engine's
		// basic shapes are only in a packaged build because DefaultGame.ini
		// asks for the directory to be cooked; if that is undone, this says
		// which mesh was missing rather than reporting 0 of 593 pieces.
		if (Cube == nullptr || Cyl == nullptr || Plane == nullptr)
		{
			Note = std::string("basic-shape-missing/cube=") + (Cube ? "yes" : "NO")
			     + "/cylinder=" + (Cyl ? "yes" : "NO") + "/plane=" + (Plane ? "yes" : "NO")
			     + "/is-Engine-BasicShapes-in-DirectoriesToAlwaysCook";
		}

		for (size_t I = 0; I < GSpec.Pieces.size(); ++I)
		{
			const Piece& P = GSpec.Pieces[I];
			// SIZES ARE FULL SIZES IN METRES AND THE ENGINE'S BASIC SHAPES
			// ARE ONE METRE, so the scale IS the size. That is a fact about
			// the meshes, and it is asserted rather than assumed: a cube of
			// 100 uu scaled by sx_m is sx_m metres across only while the
			// mesh is 100 uu, and the verdict's placement instrument is what
			// would catch it if the engine ever changed them.
			const FVector Scale((float)P.SX, (float)P.SZ, (float)P.SY);
			AStaticMeshActor* A = nullptr;
			if (P.Shape == "box") { A = SpawnPiece(World, Cube, P, Scale); if (A) ++Boxes; }
			else if (P.Shape == "cyl")
			{
				// THE CYLINDER'S AXIS IS LOCAL +y IN THE FILE'S FRAME, which
				// under this mapping is local +Z, and that is this engine's
				// cylinder's own axis. Height is sy_m and the diameter is
				// sx_m and sz_m, so the same scale vector is correct for
				// both shapes and no special case is needed.
				A = SpawnPiece(World, Cyl, P, Scale); if (A) ++Cyls;
			}
			else if (P.Shape == "decal")
			{
				// A DECAL IS A QUAD UNTIL PHASE C. sz_m is zero and the
				// engine's plane is 100 uu square in its local XY with the
				// normal on +Z; the file says the quad is sx_m by sy_m with
				// its normal on -z before rotation, so the plane is turned
				// to face -z and scaled in the two axes that are left.
				Piece Q = P;
				// TURNING THE PLANE ONTO THE FILE'S FACING, AND THE SIGN IS
				// THE WHOLE OF IT. The engine's plane spans its local X and
				// Y with the normal on local +Z, which under this mapping is
				// the file's local +y. The file says the quad is sx_m by
				// sy_m with its normal on -z before rotation. A quarter turn
				// about the file's x takes +y onto -z, and the file's pitch
				// is exactly that turn, so the pitch goes DOWN by 90 and not
				// up: up by 90 lands the normal on +z, which is the same
				// plane facing backwards, and an untextured quad facing away
				// is culled or lit from behind. The in-plane axes come out
				// right either way, which is why the sign would not show in
				// a count.
				Q.PitchDeg = P.PitchDeg - 90.0;
				const FVector QScale((float)P.SX, (float)P.SY, 1.0f);
				A = SpawnPiece(World, Plane, Q, QScale);
				if (A)
				{
					// A CO-PLANAR QUAD Z-FIGHTS WITH THE SURFACE UNDER IT,
					// and this is the emitter's decision rather than the
					// file's, so it is a named constant and it is printed.
					// The file puts a ground decal at the ground level
					// because it is describing a decal, and this engine has
					// no decal here yet: Phase C replaces the quad with a
					// real deferred decal and this lift goes with it.
					A->AddActorWorldOffset(
						A->GetActorRotation().RotateVector(FVector(0.0f, 0.0f, 1.0f)) * kDecalLiftCm);
					++Planes; ++Decals;
				}
			}
			else if (P.Shape == "mesh")
			{
				// A STAND-IN, COUNTED AND NAMED. The prop pipeline's models
				// are .glb files Unity imports at build time; this engine has
				// no runtime importer and Phase C owns that. A box of the
				// prop's OWN stated size holds the space so the frame is
				// comparable, and `propStandIns` on the scene line is what
				// stops anybody reading it as a loaded model.
				A = SpawnPiece(World, Cube, P, Scale);
				if (A) { ++Boxes; ++Props; }
			}
			else
			{
				// A SHAPE THIS EMITTER DOES NOT KNOW IS COUNTED, NOT
				// IGNORED. The g++ test asserts the file contains none, so
				// reaching this is a schema change nobody told the emitter
				// about.
				++Skipped;
				continue;
			}
			if (A == nullptr) { ++Skipped; continue; }
			++Emitted;
			GByName.Add(FString(UTF8_TO_TCHAR(P.Name.c_str())), A);
		}

		// H4: A POINT LIGHT UNDER EVERY EMISSIVE PIECE, which is what the
		// file's lantern block says in as many words: one point light 0.05 m
		// below the centre of each emissive piece.
		const FLinearColor Lamp = LinearFromGamma(GSpec.Lantern.R, GSpec.Lantern.G, GSpec.Lantern.B);
		for (size_t I = 0; I < GSpec.Pieces.size(); ++I)
		{
			const Piece& P = GSpec.Pieces[I];
			if (!P.Emissive) { continue; }
			APointLight* L = SpawnPointLight(
				World, FVector(P.X * 100.0, P.Z * 100.0, (P.Y - 0.05) * 100.0),
				Lamp, (float)GSpec.Lantern.RangeM,
				(float)GSpec.Lantern.Intensity * kLampGainUnitless, true);
			if (L != nullptr) { GLanterns.Add(L); }
		}

		// H5: THE WINDOW PRACTICALS, AT THE NAMES THE FILE LISTS AND NOWHERE
		// ELSE. Not "every piece whose name contains _interior": that rule is
		// what the Unity host had, and by 2 September it also matched three
		// decal cards. The file resolves lit_bays to names in Core and both
		// engines light the names.
		const FLinearColor Warm = LinearFromGamma(GSpec.Windows.R, GSpec.Windows.G, GSpec.Windows.B);
		int WindowsUnplaced = 0;
		for (size_t I = 0; I < GSpec.Windows.LitNames.size(); ++I)
		{
			AStaticMeshActor** Found = GByName.Find(FString(UTF8_TO_TCHAR(GSpec.Windows.LitNames[I].c_str())));
			if (Found == nullptr || *Found == nullptr) { ++WindowsUnplaced; continue; }
			const FVector At = (*Found)->GetActorLocation() + FVector(0, 0, 40.0f);
			APointLight* L = SpawnPointLight(World, At, Warm,
				(float)GSpec.Windows.ShopRangeM,
				(float)GSpec.Windows.ShopIntensity * kLampGainUnitless, false);
			if (L != nullptr) { GWindows.Add(L); } else { ++WindowsUnplaced; }
		}
		if (WindowsUnplaced > 0)
		{
			// APPENDED, NOT ASSIGNED. A missing basic shape and an unplaced
			// practical are two findings and the second must not erase the
			// first, which is the one that explains an empty street.
			if (Note == "none") { Note.clear(); } else { Note += "/"; }
			Note += "practicals-unplaced=" + std::to_string(WindowsUnplaced)
			      + "-of-" + std::to_string((int)GSpec.Windows.LitNames.size());
		}
		if (Note.empty()) { Note = "none"; }

		// THE SUN, THE FILL AND THE FOG, SPAWNED HERE AND WRITTEN ONLY BY
		// ApplyCondition. One owner per global.
		GSun   = SpawnDirectional(World, FRotator((float)SunPitchDeg(GSpec.SunElevationDeg),
		                                          (float)SunYawDeg(GSpec.SunAzimuthDeg), 0.0f), true);
		GFillA = SpawnDirectional(World, FRotator(-80.0f,  20.0f, 0.0f), false);
		GFillB = SpawnDirectional(World, FRotator(-10.0f, 200.0f, 0.0f), false);
		GFillC = SpawnDirectional(World, FRotator( 60.0f,  90.0f, 0.0f), false);
		{
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			GFog = World->SpawnActor<AExponentialHeightFog>(
				AExponentialHeightFog::StaticClass(), FVector(0, 0, 0), FRotator::ZeroRotator, Params);
			MakeMovable(GFog);
		}

		GSceneLine = SceneLine(GSpec, Emitted, Boxes, Cyls, Planes, Props, Decals,
		                       GLanterns.Num(), GWindows.Num(), Skipped, Note);
		// THE SPAWNS THAT ARE NOT PIECES, READ BACK RATHER THAN ASSUMED. A
		// null here is why a frame would be black, and it is a different
		// fault from an empty street.
		char Buf[420];
		std::snprintf(Buf, sizeof(Buf),
			" sun=%s fill=%d/3 fog=%s skyModel=none-black/phase-C-owns-the-hdri"
			" lampGain=%.2f fogGain=%.2f ambientModel=trilight-3-directional/not-a-captured-sky"
			" lightUnits=unitless/not-candelas decalLiftCm=%.1f decalModel=quad/phase-C-owns-the-decal",
			GSun ? "yes" : "SPAWN-FAILED",
			(GFillA ? 1 : 0) + (GFillB ? 1 : 0) + (GFillC ? 1 : 0),
			GFog ? "yes" : "SPAWN-FAILED",
			kLampGainUnitless, kFogDensityGain, kDecalLiftCm);
		GSceneLine += Buf;
	}

	const Camera* FindCamera(const std::string& Id)
	{
		for (size_t I = 0; I < GSpec.Cameras.size(); ++I)
			if (GSpec.Cameras[I].Id == Id) return &GSpec.Cameras[I];
		return nullptr;
	}

	const Condition* FindCondition(const std::string& Id)
	{
		for (size_t I = 0; I < GSpec.Conditions.size(); ++I)
			if (GSpec.Conditions[I].Id == Id) return &GSpec.Conditions[I];
		return nullptr;
	}

	// THE ONLY WRITER OF THE SUN, THE FILL AND THE FOG. Every condition
	// change writes all of them, so no setting can carry over from the
	// previous shot and be attributed to this one.
	void ApplyCondition(const Condition& C)
	{
		const FLinearColor DaySky(0.42f, 0.46f, 0.52f, 1.0f);
		const FLinearColor NightSky(0.05f, 0.05f, 0.07f, 1.0f);
		const FLinearColor Sky = C.SunOn ? DaySky : NightSky;
		SetDirectional(GSun, FLinearColor(0.95f, 0.96f, 1.0f, 1.0f), C.SunOn ? 3.0f : 0.0f);
		SetDirectional(GFillA, Sky, kFillSky);
		SetDirectional(GFillB, Sky * 0.75f, kFillEquator);
		SetDirectional(GFillC, Sky * 0.45f, kFillGround);
		for (int32 I = 0; I < GLanterns.Num(); ++I)
			if (ULightComponent* L = GLanterns[I]->GetLightComponent()) L->SetVisibility(C.LanternsOn);
		for (int32 I = 0; I < GWindows.Num(); ++I)
			if (ULightComponent* L = GWindows[I]->GetLightComponent()) L->SetVisibility(C.WindowsOn);
		if (GFog != nullptr)
		{
			// FOUND BY CLASS RATHER THAN BY AN ACCESSOR. The actor's named
			// getter has been renamed across engine versions and this
			// container cannot compile a single line of this file; a lookup
			// by component class is the API least likely to have moved.
			if (UExponentialHeightFogComponent* F =
			        GFog->FindComponentByClass<UExponentialHeightFogComponent>())
			{
				F->SetFogDensity((float)C.FogDensity * kFogDensityGain);
				F->SetFogInscatteringColor(C.SunOn ? FLinearColor(0.55f, 0.58f, 0.62f, 1.0f)
				                                   : FLinearColor(0.06f, 0.05f, 0.05f, 1.0f));
				F->SetFogHeightFalloff(0.02f);
			}
		}
	}

	// PLACE THE CAMERA AND READ THE PLACEMENT BACK. Asking for a transform
	// and printing the transform you asked for is not evidence that anything
	// moved.
	FString GCamLine = TEXT("shotCamPlaced=NOT-REACHED");
	double  GEyeY = 0.0;
	FString GCamEdge = TEXT("none");

	void PlaceCamera(UWorld* World, const Camera& C)
	{
		if (World == nullptr)
		{
			// A WORLD THAT WENT AWAY BETWEEN TWO TICKS IS A FINDING, and it
			// must not read as a camera that was placed at the origin.
			GCamLine = TEXT("shotCamPlaced=NO-WORLD shotCamReason=the-game-world-vanished-between-ticks");
			return;
		}
		// EYE HEIGHT IS MEASURED FROM THE PAVEMENT UNDER THE CAMERA and the
		// pavement level comes OUT OF THE FILE. The footway falls 1 in 40,
		// so a camera at a fixed y stands at a different height on each side
		// of the street and the matched pair is not matched at all.
		GEyeY = C.GroundY + C.EyeHeightM;
		GCamEdge = FString(UTF8_TO_TCHAR(C.GroundEdge.c_str()));
		const FVector Want(C.X * 100.0, C.Z * 100.0, GEyeY * 100.0);
		// PITCH IS NEGATED AND FOV IS CONVERTED. The file's camera pitch is
		// positive DOWN, as Unity's is; this engine's is positive up. The
		// file's fov is VERTICAL, as Unity's is; this engine's is
		// HORIZONTAL, and handing 60 straight over would photograph a third
		// of the street the Unity frame shows.
		const FRotator WantRot((float)-C.PitchDeg, (float)C.YawDeg, 0.0f);
		if (GCam == nullptr)
		{
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			GCam = World->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), Want, WantRot, Params);
		}
		else
		{
			GCam->SetActorLocationAndRotation(Want, WantRot);
		}
		if (GCam != nullptr)
		{
			if (UCameraComponent* CC = GCam->GetCameraComponent())
			{
				CC->SetFieldOfView((float)HorizontalFovDeg(C.FovVerticalDeg, kShotW, kShotH));
				CC->SetAspectRatio((float)kShotW / (float)kShotH);
				CC->SetConstraintAspectRatio(true);
			}
		}
		FVector GotLoc = FVector::ZeroVector;
		FRotator GotRot = FRotator::ZeroRotator;
		if (APlayerController* PC = World->GetFirstPlayerController())
		{
			if (GCam != nullptr) { PC->SetViewTarget(GCam); }
			PC->GetPlayerViewPoint(GotLoc, GotRot);
		}
		GCamLine = FString::Printf(
			TEXT("shotCamPlaced=%s shotCamAskedXYZcm=%.1f/%.1f/%.1f shotCamReadXYZcm=%.1f/%.1f/%.1f ")
			TEXT("shotCamDeltaCm=%.2f shotCamAskedPitchYaw=%.1f/%.1f shotCamReadPitchYaw=%.1f/%.1f ")
			TEXT("shotWorld=%s"),
			GCam != nullptr ? TEXT("yes") : TEXT("SPAWN-FAILED"),
			Want.X, Want.Y, Want.Z, GotLoc.X, GotLoc.Y, GotLoc.Z,
			FVector::Dist(Want, GotLoc), WantRot.Pitch, WantRot.Yaw,
			GotRot.Pitch, GotRot.Yaw, *NoSp(World->GetMapName()));
	}

	// ---- the verdict ----------------------------------------------------

	void WriteVerdict(const std::string& DoneLine)
	{
		TArray<FString> Out;
		Out.Add(FString::Printf(TEXT("# UE vignette shot %s @%lld"),
		                        *ShaFromCommandLine(), (long long)FDateTime::UtcNow().ToUnixTimestamp()));
		Out.Add(TEXT("# Line 1 names the commit this was measured on, as the Unity verdict does."));
		Out.Add(TEXT("# THE STREET IS BUILT FROM production/specs/vignette-pieces.json AND NOTHING ELSE."));
		Out.Add(TEXT("#   Nothing here is authored: every position, size and rotation came out of that"));
		Out.Add(TEXT("#   file, which Ledger.Core wrote from the shared scene json. Untextured on"));
		Out.Add(TEXT("#   purpose: materials, the props and the HDRI are Phase C and Phase D."));
		Out.Add(TEXT("# frameMedianMs: MEDIAN of 24 engine frame deltas after 8 discarded warm-up"));
		Out.Add(TEXT("#   frames, in milliseconds. NOT the Unity host's number even though both are a"));
		Out.Add(TEXT("#   median of 24 after 8: Unity times one Camera.Render plus GL.Flush and this"));
		Out.Add(TEXT("#   times a whole engine frame. frameStat on each line names which one it is."));
		Out.Add(TEXT("# shotMeanLuma: mean over EVERY pixel of the committed file, 0 to 1,"));
		Out.Add(TEXT("#   luma=(0.299R+0.587G+0.114B)/255, the same weights the Unity sim uses."));
		Out.Add(TEXT("# shotNonBlackPct: percent of shotPixels with any channel above zero."));
		Out.Add(TEXT("# shotDistinctBuckets: distinct 5-bit-per-channel colour buckets, of 32768."));
		Out.Add(TEXT("# status=WROTE needs a decoded file with more than one bucket and at least one"));
		Out.Add(TEXT("#   non-black pixel. BLANK, UNDECODABLE and NO-FILE are the three ways it fails"));
		Out.Add(TEXT("#   and the step exits non-zero for all three with the evidence still committed."));
		Out.Add(TEXT(""));
		Out.Add(FString(UTF8_TO_TCHAR(GSceneLine.c_str())));
		Out.Add(GCamLine);
		if (GShotLines.empty())
		{
			Out.Add(TEXT("NOTHING MEASURED - no shot reached the measuring step on this commit."));
		}
		else
		{
			for (size_t I = 0; I < GShotLines.size(); ++I)
			{
				Out.Add(FString(UTF8_TO_TCHAR(GShotLines[I].c_str())));
			}
		}
		Out.Add(FString(UTF8_TO_TCHAR(DoneLine.c_str())));
		if (!GArt.empty())
		{
			Out.Add(TEXT("# ascii-luma of the FIRST frame that decoded, 48x27 cells, top row first."));
			Out.Add(FString(UTF8_TO_TCHAR(GArt.c_str())));
		}
		Out.Add(TEXT("shotReached=end"));
		const FString Body = FString::Join(Out, TEXT("\n")) + TEXT("\n");
		FFileHelper::SaveStringToFile(Body, *AbsProject(TEXT("ue-vignette-verdict.txt")));
		FFileHelper::SaveStringToFile(Body, *FPaths::Combine(
			FPaths::GetPath(FPlatformProcess::ExecutablePath()), TEXT("ue-vignette-verdict.txt")));
	}

	void Finish(const std::string& DoneLine)
	{
		GPhase = EPhase::Done;
		WriteVerdict(DoneLine);
		FPlatformMisc::RequestExit(false);
	}

	void FinishNormally()
	{
		Finish(CaptureDoneLine(GWrote, (int)GSpec.Shots.size(), GBlank, GNoFile,
		                       FPlatformTime::Seconds() - GStart, GTicks));
	}

	bool DecodeBgra(const FString& PngPath, TArray64<uint8>& OutBgra, int32& OutW, int32& OutH,
	                std::string& OutNote)
	{
		TArray<uint8> Compressed;
		if (!FFileHelper::LoadFileToArray(Compressed, *PngPath) || Compressed.Num() == 0)
		{
			OutNote = "file-would-not-load-or-was-empty";
			return false;
		}
		IImageWrapperModule* Mod =
			FModuleManager::Get().LoadModulePtr<IImageWrapperModule>(FName("ImageWrapper"));
		if (Mod == nullptr) { OutNote = "imagewrapper-module-missing"; return false; }
		TSharedPtr<IImageWrapper> Wrapper = Mod->CreateImageWrapper(EImageFormat::PNG);
		if (!Wrapper.IsValid()) { OutNote = "no-png-wrapper"; return false; }
		if (!Wrapper->SetCompressed(Compressed.GetData(), (int64)Compressed.Num()))
		{
			OutNote = "setcompressed-refused-the-bytes";
			return false;
		}
		OutW = Wrapper->GetWidth();
		OutH = Wrapper->GetHeight();
		if (OutW <= 0 || OutH <= 0) { OutNote = "decoded-size-was-zero"; return false; }
		if (!Wrapper->GetRaw(ERGBFormat::BGRA, 8, OutBgra)) { OutNote = "getraw-refused"; return false; }
		return OutBgra.Num() >= (int64)OutW * (int64)OutH * 4;
	}

	// A FILE THAT EXISTS IS NOT A FILE THAT IS FINISHED. Two consecutive
	// polls agreeing on a non-zero size is the cheap version of waiting for
	// the writer and it costs one frame.
	bool SizeSettled(const FString& Path, int64& Tracker)
	{
		const int64 Size = IFileManager::Get().FileSize(*Path);
		if (Size <= 0) { Tracker = -1; return false; }
		const bool bSame = (Size == Tracker);
		Tracker = Size;
		return bSame;
	}

	FString NewestPngUnder(const FString& Dir, int32& OutCount)
	{
		TArray<FString> Found;
		IFileManager::Get().FindFilesRecursive(Found, *Dir, TEXT("*.png"), true, false, false);
		OutCount = Found.Num();
		FString Best;
		FDateTime BestTime = FDateTime::MinValue();
		for (const FString& F : Found)
		{
			const FDateTime T = IFileManager::Get().GetTimeStamp(*F);
			if (Best.IsEmpty() || T > BestTime) { Best = F; BestTime = T; }
		}
		return Best;
	}

	// MEASURE THE FILE THAT IS ABOUT TO BE COMMITTED, not the buffer the
	// engine had in memory, and let the maths and the string come from the
	// tested header.
	void MeasureShot(const Shot& S, const FString& PngPath, bool bHaveFile)
	{
		const double VFov = FindCamera(S.CameraId) ? FindCamera(S.CameraId)->FovVerticalDeg : 0.0;
		const double HFov = HorizontalFovDeg(VFov, kShotW, kShotH);
		const double Median = MedianMs(GFrameMs);
		if (!bHaveFile)
		{
			++GNoFile;
			GShotLines.push_back(ShotLine(S.Id, S.CameraId, S.ConditionId, GEyeY,
				TCHAR_TO_UTF8(*GCamEdge), Median, kTimedFrames, kWarmFrames,
				kShotW, kShotH, VFov, HFov, 0, "NO-FILE", "none",
				std::string(TCHAR_TO_UTF8(*GNote))));
			return;
		}
		const int64 Bytes = IFileManager::Get().FileSize(*PngPath);
		TArray64<uint8> Bgra;
		int32 W = 0, H = 0;
		std::string Note(TCHAR_TO_UTF8(*GNote));
		if (!DecodeBgra(PngPath, Bgra, W, H, Note))
		{
			++GNoFile;
			GShotLines.push_back(ShotLine(S.Id, S.CameraId, S.ConditionId, GEyeY,
				TCHAR_TO_UTF8(*GCamEdge), Median, kTimedFrames, kWarmFrames,
				0, 0, VFov, HFov, (long long)Bytes, "UNDECODABLE",
				TCHAR_TO_UTF8(*FPaths::GetCleanFilename(PngPath)), Note));
			return;
		}
		const LedgerFrame::FrameStats St =
			LedgerFrame::Measure((const unsigned char*)Bgra.GetData(), W, H);
		if (St.Blank) { ++GBlank; } else { ++GWrote; }
		// THE PIXEL STATISTICS RIDE ON THE SAME LINE AS THE SHOT'S OWN KEYS,
		// through the tested formatter, so the frame and the numbers about it
		// cannot be separated by a grep.
		std::string Line = ShotLine(S.Id, S.CameraId, S.ConditionId, GEyeY,
			TCHAR_TO_UTF8(*GCamEdge), Median, kTimedFrames, kWarmFrames,
			W, H, VFov, HFov, (long long)Bytes,
			St.Blank ? "BLANK" : "WROTE",
			TCHAR_TO_UTF8(*FPaths::GetCleanFilename(PngPath)), Note);
		// PER-SAMPLE NUMBERS ON THE SAMPLE LINE. FrameStats' own done line
		// carries whole-run keys (seconds waited, ticks) that would be a lie
		// four times over on four shot lines, so the pixel statistics come
		// through PixelLine, which carries only what is true of THIS frame.
		Line += " ";
		Line += LedgerFrame::PixelLine(St);
		GShotLines.push_back(Line);
		if (GArt.empty())
		{
			GArt = LedgerFrame::AsciiLuma((const unsigned char*)Bgra.GetData(), W, H);
		}
	}

	FString ShotPngPath(const Shot& S)
	{
		return AbsProject(*FString::Printf(TEXT("ue-%s.png"), UTF8_TO_TCHAR(S.Id.c_str())));
	}

	bool Tick(float)
	{
		++GTicks;
		++GPhaseTicks;
		const double Now = FPlatformTime::Seconds();
		if (GStart == 0.0) { GStart = Now; GPhaseStart = Now; GLastTick = Now; }
		const double Delta = Now - GLastTick;
		GLastTick = Now;

		switch (GPhase)
		{
		case EPhase::WaitWorld:
		{
			UWorld* World = GameWorld();
			if (World == nullptr && (Now - GPhaseStart) <= kWorldCeiling) { return true; }
			if (World == nullptr)
			{
				// A WORLD THAT NEVER CAME IS A FINDING, and it is a different
				// one from a street that would not build.
				GSceneLine = "sceneStatus=NOTHING-EMITTED piecesEmitted=0/"
				           + std::to_string(GSpec.HeaderPieces)
				           + " sceneNote=world-ceiling-bit-at-45s";
				Finish(CaptureDoneLine(0, 0, 0, 0, Now - GStart, GTicks));
				return false;
			}
			BuildScene(World);
			// UNCAP THE FRAME RATE BEFORE ANYTHING IS TIMED. A frame time
			// measured against a 60 Hz cap is a measurement of the cap, and
			// it would read as a suspiciously round 16.67 in the verdict.
			if (GEngine != nullptr)
			{
				GEngine->Exec(World, TEXT("t.MaxFPS 0"));
				GEngine->Exec(World, TEXT("r.VSync 0"));
			}
			GPhase = EPhase::ApplyShot;
			GPhaseStart = Now; GPhaseTicks = 0;
			return true;
		}
		case EPhase::ApplyShot:
		{
			if (GShotIndex >= (int32)GSpec.Shots.size()) { FinishNormally(); return false; }
			const Shot& S = GSpec.Shots[GShotIndex];
			const Camera* C = FindCamera(S.CameraId);
			const Condition* Cond = FindCondition(S.ConditionId);
			if (C == nullptr || Cond == nullptr)
			{
				// A SHOT NAMING A CAMERA OR A CONDITION THE FILE DOES NOT
				// CARRY IS COUNTED, not skipped in silence.
				++GNoFile;
				GShotLines.push_back(ShotLine(S.Id, S.CameraId, S.ConditionId, 0.0, "none",
					-1.0, kTimedFrames, kWarmFrames, kShotW, kShotH, 0.0, 0.0, 0,
					"NO-SUCH-CAMERA-OR-CONDITION", "none", "nothing-measured"));
				++GShotIndex;
				return true;
			}
			ApplyCondition(*Cond);
			PlaceCamera(GameWorld(), *C);
			GFrameMs.clear();
			GNote = TEXT("none");
			GTriedHighResThisShot = false;
			GSizeTracker = -1;
			if ((Now - GPhaseStart) < kSettleAfterCondition) { return true; }
			GPhase = EPhase::Warm;
			GPhaseStart = Now; GPhaseTicks = 0;
			return true;
		}
		case EPhase::Warm:
		{
			// WARM-UP FRAMES ARE DISCARDED, and they are discarded for a
			// named reason: the first frames after a condition change compile
			// shader variants, which is a real cost and not the one a
			// comparison is about.
			if (GPhaseTicks < kWarmFrames) { return true; }
			GPhase = EPhase::Timed;
			GPhaseStart = Now; GPhaseTicks = 0;
			return true;
		}
		case EPhase::Timed:
		{
			if ((int32)GFrameMs.size() < kTimedFrames)
			{
				GFrameMs.push_back(Delta * 1000.0);
				return true;
			}
			GPhase = EPhase::Ask;
			GPhaseStart = Now; GPhaseTicks = 0;
			return true;
		}
		case EPhase::Ask:
		{
			const Shot& S = GSpec.Shots[GShotIndex];
			GAskedPath = ShotPngPath(S);
			IFileManager::Get().Delete(*GAskedPath, false, true, true);
			GSizeTracker = -1;
			if (!GUseHighRes)
			{
				// CANDIDATE A, AND AN ABSOLUTE PATH ON PURPOSE: a relative
				// one resolves against the engine's screenshot directory,
				// which would put the file where nothing is looking and read
				// as no file at all.
				FScreenshotRequest::RequestScreenshot(GAskedPath, false, false);
			}
			else
			{
				if (GEngine != nullptr)
				{
					GEngine->Exec(GameWorld(), *FString::Printf(TEXT("HighResShot %dx%d"), kShotW, kShotH));
				}
			}
			GPhase = EPhase::WaitFile;
			GPhaseStart = Now; GPhaseTicks = 0;
			return true;
		}
		case EPhase::WaitFile:
		{
			if (!GUseHighRes)
			{
				if (SizeSettled(GAskedPath, GSizeTracker))
				{
					MeasureShot(GSpec.Shots[GShotIndex], GAskedPath, true);
					++GShotIndex;
					GPhase = EPhase::ApplyShot;
					GPhaseStart = Now; GPhaseTicks = 0;
					return true;
				}
			}
			else
			{
				int32 Count = 0;
				const FString Newest = NewestPngUnder(
					FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()), Count);
				if (!Newest.IsEmpty() && SizeSettled(Newest, GSizeTracker))
				{
					// ONE NAME FOR THE FILE THE STEP COLLECTS, whatever
					// produced it: HighResShot picks its own filename under
					// Saved and the step should not have to know which
					// candidate won.
					IFileManager::Get().Copy(*GAskedPath, *Newest, true, true);
					IFileManager::Get().Delete(*Newest, false, true, true);
					MeasureShot(GSpec.Shots[GShotIndex], GAskedPath, true);
					++GShotIndex;
					GPhase = EPhase::ApplyShot;
					GPhaseStart = Now; GPhaseTicks = 0;
					return true;
				}
			}
			if ((Now - GPhaseStart) < kFileCeiling) { return true; }
			if (!GUseHighRes && !GTriedHighResThisShot)
			{
				// CANDIDATE B, TRIED ONCE AND THEN ADOPTED FOR THE WHOLE RUN.
				// Both are documented and neither has ever produced a file on
				// this machine, so one dispatch answers which works rather
				// than two; trying A first on every shot afterwards would
				// cost 25 wasted seconds per shot for no new information.
				GNote = TEXT("requestScreenshot-wrote-nothing-in-25s/switched-to-HighResShot");
				GUseHighRes = true;
				GTriedHighResThisShot = true;
				GPhase = EPhase::Ask;
				GPhaseStart = Now; GPhaseTicks = 0;
				return true;
			}
			GNote = GUseHighRes ? TEXT("neither-candidate-wrote-a-file-in-25s")
			                    : TEXT("requestScreenshot-wrote-nothing-in-25s");
			MeasureShot(GSpec.Shots[GShotIndex], GAskedPath, false);
			++GShotIndex;
			GPhase = EPhase::ApplyShot;
			GPhaseStart = Now; GPhaseTicks = 0;
			return true;
		}
		default:
			return false;
		}
	}
}

namespace LedgerVignetteShot
{
	void Start()
	{
		// THE C NUMERIC LOCALE, SET BEFORE ANYTHING IS PARSED. Under a
		// comma-decimal locale strtod reads "1.5" as 1, and every coordinate
		// in this street would lose its fraction while every count stayed
		// green. The g++ test asserts the same thing on the same file.
		std::setlocale(LC_NUMERIC, "C");

		FString Tried;
		GSpecPath = FindSpec(Tried);
		GSpecTried = Tried;
		if (GSpecPath.IsEmpty())
		{
			GSceneLine = "sceneStatus=NOTHING-EMITTED piecesEmitted=0/0"
			             " sceneNote=piece-list-not-found-beside-the-binary-or-the-project";
			GPhase = EPhase::Done;
			WriteVerdict("captureStatus=NOTHING-MEASURED shotsWrote=0/0 shotsBlank=0/0"
			             " shotsNoFile=0/0 captureSeconds=0.00 captureTicks=0");
			FPlatformMisc::RequestExit(false);
			return;
		}
		FString Contents;
		if (!FFileHelper::LoadFileToString(Contents, *GSpecPath))
		{
			GSceneLine = "sceneStatus=NOTHING-EMITTED piecesEmitted=0/0"
			             " sceneNote=piece-list-found-but-would-not-open";
			GPhase = EPhase::Done;
			WriteVerdict("captureStatus=NOTHING-MEASURED shotsWrote=0/0 shotsBlank=0/0"
			             " shotsNoFile=0/0 captureSeconds=0.00 captureTicks=0");
			FPlatformMisc::RequestExit(false);
			return;
		}
		const std::string Text(TCHAR_TO_UTF8(*Contents));
		if (!ParseSpec(Text, GSpec, GSpecErr))
		{
			// A FILE THAT WILL NOT PARSE IS A DIFFERENT FACT FROM A FILE THAT
			// IS NOT THERE, and the reason is what says which.
			GSceneLine = "sceneStatus=NOTHING-EMITTED piecesEmitted=0/0 sceneNote="
			           + std::string(TCHAR_TO_UTF8(*NoSp(FString(UTF8_TO_TCHAR(GSpecErr.c_str())))));
			GPhase = EPhase::Done;
			WriteVerdict("captureStatus=NOTHING-MEASURED shotsWrote=0/0 shotsBlank=0/0"
			             " shotsNoFile=0/0 captureSeconds=0.00 captureTicks=0");
			FPlatformMisc::RequestExit(false);
			return;
		}
		GPhase = EPhase::WaitWorld;
		GTicker = FTSTicker::GetCoreTicker().AddTicker(
			FTickerDelegate::CreateStatic(&Tick), 0.0f);
	}
}
