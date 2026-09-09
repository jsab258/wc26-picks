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
#include "SurfaceBind.h"

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
// UBodySetup and its AggGeom, for READING BACK how many simple collision
// primitives the imported prop mesh actually carries. A mesh with none
// renders perfectly and lets a walking Character straight through it.
#include "PhysicsEngine/BodySetup.h"
#include "Engine/PointLight.h"
#include "Components/PointLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/ExponentialHeightFog.h"
#include "Components/ExponentialHeightFogComponent.h"
// QUEUE 186: THE SKY. ASkyLight is the ambient and the reflection source;
// ASkyAtmosphere is the visible sky it captures. ASkyAtmosphere is declared
// at the bottom of Components/SkyAtmosphereComponent.h in this engine and
// has no header of its own, which is the one include here nothing in this
// container can check.
#include "Engine/SkyLight.h"
#include "Components/SkyLightComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerStart.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "HAL/IConsoleManager.h"
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
	// ---- QUEUE 186: THE SKY, AND WHY IT IS THIS SKY ---------------------
	//
	// WHAT WAS MEASURED FIRST, because none of the numbers below mean
	// anything without it. The day frame's top band reads 249.5/250.0/250.5
	// mean RGB over 8858 pixels and the night frame's SAME band reads
	// 188.4/179.6/179.3. Those two channel orders are the two fog
	// inscattering colours set eighty lines below: day 0.55/0.58/0.62 is
	// R<G<B and night 0.06/0.05/0.05 is R>G=B. THE FAR FIELD IN EVERY FRAME
	// THIS PROJECT HAS SHOT IS THE HEIGHT FOG, lifted to near white by auto
	// exposure. The scene line called it none-black and it was never black.
	//
	// WHY AN ATMOSPHERE AND A CAPTURED SKYLIGHT, and not the HDRI the shared
	// file names. A USkyLightComponent takes a CUBE texture and this engine
	// builds none at runtime; the pack's belfast_open_field_2k.hdr is a
	// long-lat Radiance file that would need resampling into six faces AND a
	// staging step to reach a packaged binary, which is three unverifiable
	// links instead of one. A SkyAtmosphere needs no asset at all, and a
	// SkyLight capturing it makes the thing that is SEEN and the thing that
	// is REFLECTED the same object, which an HDRI ambient beside an
	// atmosphere backdrop would not. The HDRI is the next rung and this run
	// prints whether the file is even reachable so that rung is a fact
	// rather than a guess.
	//
	// THE FOUR ATMOSPHERE NUMBERS ARE A STARTING POINT AND SAY SO. Rule 2
	// forbids calling them anything better: no series exists. Rayleigh is
	// cut because Rayleigh is the blue and Meridian is not blue; Mie is
	// raised because Mie is the pale haze an overcast sky is made of;
	// anisotropy is dropped toward zero because a forward-scattering halo is
	// a clear-sky look and the reference is flat; multi-scattering is taken
	// to its top because that is what fills a shaded sky. Every one is
	// printed and the sky band series is what moves them next run.
	const float kSkyRayleighScale   = 0.004f;   // engine default 0.0331
	const float kSkyMieScale        = 0.040f;   // engine default 0.003996
	const float kSkyMieAnisotropy   = 0.05f;    // engine default 0.8
	const float kSkyMultiScattering = 1.0f;     // engine default 1.0, named anyway
	// THE SKYLIGHT'S INTENSITY, day and night. The engine's own default is
	// 1.0 and the day value is left there deliberately: this is the first
	// run in which a captured sky lights anything here, and starting
	// anywhere but the engine's default would make the frame a statement
	// about a number I chose rather than about the mechanism. Night is
	// lower because the atmosphere with the sun off is nearly black anyway
	// and the lanterns are meant to own that frame.
	const float kSkyIntensityDay   = 1.0f;
	const float kSkyIntensityNight = 0.35f;
	// HOW MUCH OF THE FAR FIELD THE HEIGHT FOG MAY STILL OWN, now that
	// something else is behind it. DERIVED, WITH ITS UNKNOWN NAMED. The
	// current far field measures 0.980 luma and the reference panel's sky
	// measures 0.808 (p50, 48800 px, Codex's Hook sheet, same luma weights).
	// If the atmosphere renders at S and the fog covers fraction M, the far
	// field is M*0.980 + (1-M)*S; S is the unknown and for S between 0.60
	// and 0.70 the M that lands on 0.81 is between 0.55 and 0.39. 0.45 sits
	// inside that range. IT IS NOT A MEASURED BOUND, it is one number
	// derived from two measured ones and one unknown, and the printed sky
	// band series is what replaces the unknown next run.
	const float kFogMaxOpacityWithSky = 0.45f;
	// THE HDRI THE SHARED FILE NAMES, LOOKED FOR AND NOT BOUND. The pack
	// lives under the Unity tree and the workflow stages CityPackTextures by
	// name; nothing stages this, so NOT-FOUND is the expected answer and it
	// is worth having as a fact rather than as an assumption.
	const TCHAR* kSkyHdriExt = TEXT(".hdr");
	// HOW FAR A DECAL QUAD IS LIFTED OFF THE SURFACE IT SITS ON. Not in the
	// file: the file describes a decal, which has no thickness and no
	// z-fighting, and this engine is drawing it as a quad until Phase C.
	// One centimetre is a millimetre-scale artefact at any distance the two
	// cameras see, and it is printed so nobody has to find it in code.
	const float kDecalLiftCm = 1.0f;

	// ---- queue 059: what it takes to ask whether a light reached a pixel --
	//
	// THE PROBE GRID. The peak sample region is a cell of this grid and the
	// verdict prints the cell and its pixel rectangle, so a reader knows
	// WHERE the contribution landed without opening the frame. Eight by four
	// over 1280x720 is a 160x180 cell, which is about the size a lantern's
	// pool of light covers at this camera distance. It is a reporting
	// resolution, not a bound.
	const int32 kProbeGridCols = 8;
	const int32 kProbeGridRows = 4;
	// A CEILING ON THE PASS, NOT A TARGET, AND IT ANNOUNCES WHEN IT BITES.
	// Every probe frame is a screenshot round trip and the file ceiling above
	// is 25 seconds, so a machine that stops writing files could otherwise
	// spend fourteen of them here. When this bites, the lights it cost are
	// counted on the light-pass line and the status reads PARTIAL-BUDGET-BIT.
	const double kLightProbeBudgetSeconds = 240.0;
	// ONE SCRATCH NAME FOR EVERY PROBE FRAME, deleted when the run ends.
	const TCHAR* kProbePngLeaf = TEXT("ue-lightprobe.png");

	// ---- phase C: the pack's maps and the one asset a script had to make --
	//
	// THE BASE MATERIAL IS A BUILD PRODUCT, NOT A HAND-MADE ASSET. Unreal
	// compiles materials in the editor and a packaged game can only INSTANCE
	// one, so Phase C needs exactly one binary asset;
	// tools/ue/make_base_material.py makes it in the cook step and the cook
	// carries it in through +DirectoriesToAlwaysCook=(Path="/Game/Ledger").
	// If it is not there this run says so on the materials line and the
	// street still renders untextured: a missing material is a finding, not
	// a black frame.
	const TCHAR* kBaseMaterialPath = TEXT("/Game/Ledger/M_LedgerSurface.M_LedgerSurface");
	// HOW MANY METRES ONE TILE OF A PACK TEXTURE COVERS. A convention, named
	// and printed, not a measured bound: the pack ships no scale and this is
	// the first value of a series nothing has printed yet.
	const double kMetresPerTile = 2.0;

	enum class EPhase : uint8
	{
		WaitWorld, Build, ApplyShot, Warm, Timed, Ask, WaitFile, Done
	};

	Spec        GSpec;
	std::string GSpecErr = "not-read";
	FString     GSpecPath;
	std::vector<std::string> GSpecTried;

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
	// QUEUE 186. Both are written by ApplyCondition and by nothing else, the
	// same rule the sun, the fills and the fog already live under.
	ASkyLight*      GSky        = nullptr;
	ASkyAtmosphere* GAtmosphere = nullptr;
	// WRITE-ON-CHANGE, AND BOTH HALVES COUNTED. ApplyCondition is re-entered
	// every tick while a condition settles, so a recapture written per tick
	// is a rebuild asked for four times over. GSkyAppliedId is the last
	// condition the sky was written for; the two counters are what prove the
	// guard is doing its job rather than being trusted to.
	std::string GSkyAppliedId = "none-yet";
	int32       GApplyCalls   = 0;
	int32       GSkyWrites    = 0;
	// THE HDRI THE SHARED FILE NAMES: looked for, measured, NOT bound.
	std::string GHdriFoundAt    = "NOT-LOOKED-FOR";
	long long   GHdriBytes      = 0;
	std::string GHdriDetectedAs = "not-read";
	ACameraActor* GCam = nullptr;
	TArray<APointLight*> GLanterns;
	TArray<APointLight*> GWindows;
	TMap<FString, AStaticMeshActor*> GByName;
	// A SEPARATE MAP FOR THE CRIME PROBE'S OWN PIECES, ruling of 2026-09-08
	// section 2. Shards, a brick, two stand-in bodies and a yard floor are
	// NOT street pieces: they are not in vignette-pieces.json, nothing
	// regenerates them and no count of the street may include them. Keeping
	// them out of GByName is what leaves piecesEmitted=593/593, propStandIns,
	// the surface binds and every other vignette counter reading exactly what
	// they read before this map existed.
	TMap<FString, AStaticMeshActor*> GProbeByName;
	// THE NAMES OF THE LIGHTS, IN THE ORDER THEY WERE SPAWNED. A per-light
	// reading whose subject is called "light 3" is not attributable to
	// anything in the file, so the piece name the lantern hangs under and the
	// lit_bays name the practical sits in are kept beside the pointers.
	std::vector<std::string> GLanternNames;
	std::vector<std::string> GWindowNames;

	// ---- the light pass ---------------------------------------------------
	bool    GProbing        = false;
	int32   GProbeSeq       = -1;     // -1 is the control, then 0..N-1
	bool    GProbeVisWas    = true;   // CAPTURED, never assumed, before a toggle
	double  GProbeStarted   = 0.0;    // when the first probe of the run began
	double  GProbeSpent     = 0.0;    // cumulative seconds inside the pass
	TArray64<uint8> GRefBgra;         // the reference frame, kept to diff against
	int32   GRefW = 0, GRefH = 0;
	std::string GRefShotId;
	std::vector<std::string> GLightLines;
	int GProbed = 0, GEligible = 0, GReached = 0, GSkippedOff = 0;
	int GSkippedBudget = 0, GProbeNoFile = 0, GRestoreMismatch = 0;
	int GShotsProbed = 0, GControls = 0;
	FString GToneLine = TEXT("tonemapRead=NOT-REACHED");

	// ---- the material pass -------------------------------------------------
	FString GTexRoot;
	int32   GTexRootFiles = 0;
	// WHERE THE SEARCH LOOKED, kept because `texRoot=NOT-FOUND` on its own
	// cannot say whether the pack or the search is in the wrong place.
	std::vector<std::string> GTexRootTried;
	UMaterialInterface* GBaseMaterial = nullptr;
	std::vector<LedgerSurface::Bound> GBinds;
	int32 GTexturesImported = 0, GMidsCreated = 0;
	std::string GMaterialsLine =
		"materialsStatus=NOT-REACHED materialsNote=the-material-pass-never-ran";

	// ---- the control quads, which are this pass's accepting case ---------
	// One extra plane per control in front of the camera the first shot
	// uses. They carry no street data and are not pieces: they exist so that
	// a frame can show what a WORKING material instance looks like beside
	// the street that is not showing one.
	std::vector<LedgerSurface::QuadResult> GQuads;
	std::vector<std::string> GQuadLines;
	// THE CONTROL QUAD ACTORS THEMSELVES, KEPT so that a shot which is not
	// the one they were placed for can hide them. They are an instrument, and
	// vignette-spec-test measures one of them reaching column 1274 of
	// cam_hook's 1280 wide frame, which is an instrument standing in the
	// picture rung 1 is judged by. The RULE is LedgerSurface::
	// ControlQuadsVisibleFor and lives in the header the test compiles; this
	// is only its call site and its tally.
	TArray<AStaticMeshActor*> GQuadActors;
	int32 GQuadVisShot = -1;      // the shot index the visibility was last written for
	int   GQuadShotsSeen = 0;     // shots that reached the write, over which the tally is taken
	int   GQuadHidden = 0;        // of those, how many had the controls hidden
	std::string GQuadHiddenIds;

	std::string GQuadDone =
		"controlQuadsStatus=NOT-REACHED controlQuads=nothing-measured"
		" controlQuadsNote=the-control-pass-never-ran";
	UTexture2D* GControlTex = nullptr;

	// DECLARED HERE, DEFINED BELOW. BuildScene calls them and is written
	// above them, and the pack import needs DecodeBgra's neighbours to be in
	// scope.
	void BindSurfaces();
	// QUEUE 186. Defined beside the texture search it borrows its candidate
	// list from; declared here because BuildScene calls it.
	void LookForNamedHdri();
	void SpawnControlQuads(UWorld* World, UStaticMesh* Plane);

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
	//
	// UNTIL RUN 19 THIS LIST WENT NOWHERE. It was filled, assigned to a
	// global and never printed, so a piece list that could not be found named
	// nothing at all; the search that does print its candidates is the golden
	// table's, in LedgerProbe.cpp. It is emitted below now, through the same
	// tested formatter the texture root uses.
	FString FindSpec(std::vector<std::string>& OutTried)
	{
		TArray<FString> Candidates;
		Candidates.Add(FPaths::Combine(FPaths::ProjectDir(), TEXT("vignette-pieces.json")));
		Candidates.Add(FPaths::Combine(FPaths::ProjectContentDir(), TEXT("vignette-pieces.json")));
		Candidates.Add(FPaths::Combine(FPaths::LaunchDir(), TEXT("vignette-pieces.json")));
		Candidates.Add(FPaths::Combine(
			FPaths::GetPath(FPlatformProcess::ExecutablePath()), TEXT("vignette-pieces.json")));
		for (const FString& C : Candidates)
		{
			const FString Full = FPaths::ConvertRelativePathToFull(C);
			OutTried.push_back(std::string(TCHAR_TO_UTF8(*Full)));
			if (FPaths::FileExists(C)) { return C; }
		}
		return FString();
	}

	// FINDS, LOADS AND PARSES THE SHARED STREET FILE, ONCE PER RUN. Both
	// entry points that need the street (the automation's Start() and the
	// interactive BuildInteractiveStreet() below) call this and fill the
	// same GSpec/GSpecPath/GSpecErr/GSpecTried globals either way, so a
	// reader asking "which file answered" gets one answer whichever entry
	// point ran. A run only ever takes one of the two paths, so nothing
	// here has to guard against being called twice.
	//
	// ON FAILURE, GSceneLine CARRIES THE REASON in the exact shape the
	// automation verdict already prints it, and the caller decides what to
	// do with a street that could not be read: the automation writes a
	// verdict and quits, the interactive path logs it and leaves the
	// player standing in whatever the level would otherwise be.
	bool LoadSpec()
	{
		// THE C NUMERIC LOCALE, SET BEFORE ANYTHING IS PARSED. Under a
		// comma-decimal locale strtod reads "1.5" as 1, and every coordinate
		// in this street would lose its fraction while every count stayed
		// green. The g++ test asserts the same thing on the same file.
		std::setlocale(LC_NUMERIC, "C");

		GSpecPath = FindSpec(GSpecTried);
		if (GSpecPath.IsEmpty())
		{
			// AND IT SAYS WHERE IT LOOKED, on the line a reader already has.
			GSceneLine = "sceneStatus=NOTHING-EMITTED piecesEmitted=0/0"
			             " sceneNote=piece-list-not-found-beside-the-binary-or-the-project"
			             " specTried=" + LedgerSurface::PathListValue(GSpecTried, 8);
			return false;
		}
		FString Contents;
		if (!FFileHelper::LoadFileToString(Contents, *GSpecPath))
		{
			GSceneLine = "sceneStatus=NOTHING-EMITTED piecesEmitted=0/0"
			             " sceneNote=piece-list-found-but-would-not-open specFrom="
			           + std::string(TCHAR_TO_UTF8(*NoSp(GSpecPath)));
			return false;
		}
		const std::string Text(TCHAR_TO_UTF8(*Contents));
		if (!ParseSpec(Text, GSpec, GSpecErr))
		{
			// A FILE THAT WILL NOT PARSE IS A DIFFERENT FACT FROM A FILE THAT
			// IS NOT THERE, and the reason is what says which.
			GSceneLine = "sceneStatus=NOTHING-EMITTED piecesEmitted=0/0 sceneNote="
			           + std::string(TCHAR_TO_UTF8(*NoSp(FString(UTF8_TO_TCHAR(GSpecErr.c_str())))))
			           + " specFrom=" + std::string(TCHAR_TO_UTF8(*NoSp(GSpecPath)));
			return false;
		}
		return true;
	}

	// GUARDS THE ONE CALLER THAT MATTERS: ALedgerGameMode::InitGame runs
	// once per process for a plain launch, and there is no reason for a
	// second call today, but a guard here costs one bool and stops the
	// street from ever being spawned twice if that ever changes.
	bool GInteractiveBuilt = false;

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

	// ---- THE MESH PIECE KIND'S PATH CONTRACT -----------------------------
	//
	// tools/ue/import_prop_meshes.py writes one static mesh per held prop the
	// street names, at kPropPackageDir/kPropNamePrefix<asset>, and its
	// --selftest READS THESE TWO LITERALS OUT OF THIS FILE and compares them
	// to its own constants. That check runs in the container before any
	// dispatch, which is the only reason the two can be trusted to agree: a
	// path this file builds and nothing resolves returns null silently, the
	// piece falls back to a box, and the frame looks like a street with a
	// crate in it instead of a crate.
	const TCHAR* kPropPackageDir = TEXT("/Game/Ledger/Props");
	const TCHAR* kPropNamePrefix = TEXT("SM_");

	// The piece's own `asset` field and nothing else decides the path. A
	// hyphen is the one character an asset id may carry that a package name
	// may not, and the Python maps it the same way; every other illegal
	// character is refused by the importer BEFORE an asset is made, so a
	// piece naming one cannot have a uasset to find here.
	FString PropObjectPath(const std::string& AssetId)
	{
		FString Name = FString(kPropNamePrefix) + FString(UTF8_TO_TCHAR(AssetId.c_str()));
		Name.ReplaceInline(TEXT("-"), TEXT("_"));
		return FString(kPropPackageDir) + TEXT("/") + Name + TEXT(".") + Name;
	}

	// THE MESH, OR NULL, AND NULL IS A MEASUREMENT. Loading a cooked asset
	// that was never cooked is the likeliest failure on this route and it is
	// indistinguishable from a missing GLB unless the reason is carried out,
	// so the caller gets one and puts it on the verdict.
	UStaticMesh* LoadPropMesh(const std::string& AssetId, std::string& WhyNot)
	{
		if (AssetId.empty()) { WhyNot = "piece-names-no-asset"; return nullptr; }
		const FString Path = PropObjectPath(AssetId);
		UStaticMesh* M = LoadObject<UStaticMesh>(nullptr, *Path);
		if (M == nullptr)
		{
			// THE ASSET, NOT THE PATH. Four full object paths overran the
			// scene line's segment buffer, and snprintf truncates in
			// silence; propPackageDir and propNamePattern are on the same
			// line, so the path is derivable from this and shorter.
			WhyNot = "no-uasset-for-" + AssetId;
			return nullptr;
		}
		return M;
	}

	// WHAT THE LOADED ASSET SAYS ABOUT COLLISION. ASKED HERE, DECIDED IN THE
	// TESTED HEADER, amendment A5 of the ruling of 2026-09-08 (queue 161).
	//
	// WHAT THIS REPLACES AND WHY. PropCollisionPrims returned a COUNT of
	// aggregate elements, and a count reads 0 for two opposite facts: an
	// asset with no body setup under it, where nothing answered the question,
	// and an asset whose body setup holds zero simple elements, which a
	// complex-as-simple trace flag makes perfectly solid against a capsule.
	// The tally on the verdict then called both of them no collision. The
	// rule is now LedgerVignette::ReadPropCollision, which g++ runs in the
	// container over every case including the two nothing here can plant, and
	// this function does nothing but ask the engine the four questions it can
	// answer.
	//
	// THE IMPORTER READS THE SAME FOUR THINGS OFF A SAVED ASSET IN AN EDITOR
	// (tools/ue/import_prop_meshes.py collidable_word) and calls the
	// no-body-setup case NO rather than UNKNOWN. Different population, and
	// ruled UNKNOWN on this side because a null body setup at runtime is also
	// what a reader gets when nothing has built one yet. Written down in the
	// header beside the rule so the divergence reads as a decision.
	LedgerVignette::EPropCollisionRead PropCollisionOf(UStaticMesh* M)
	{
		if (M == nullptr) { return LedgerVignette::PropCollision_Unknown; }
		UBodySetup* BS = M->GetBodySetup();
		const bool bHasBody = (BS != nullptr);
		const int Elements = bHasBody ? BS->AggGeom.GetElementCount() : 0;
		const bool bComplexAsSimple =
			bHasBody && BS->CollisionTraceFlag == CTF_UseComplexAsSimple;
		// GEOMETRY UNDER THE FLAG, because complex-as-simple over an empty
		// mesh stops nothing. Read off the mesh's OWN bounds, which is the
		// same question the importer asks as boundsUu-nonzero and the same
		// call the pivot correction above already makes on this pointer.
		const FVector Extent = M->GetBounds().BoxExtent;
		const bool bGeometry = (Extent.X > 0.0 || Extent.Y > 0.0 || Extent.Z > 0.0);
		return LedgerVignette::ReadPropCollision(bHasBody, Elements, bComplexAsSimple,
		                                         bGeometry);
	}

	AStaticMeshActor* SpawnPiece(UWorld* World, UStaticMesh* Mesh, const Piece& P,
	                             const FVector& ScaleUU, bool bInteractive)
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
			// CreatePrimitive-style collision is not wanted in the timed
			// automation pass: 593 bodies cost simulation time in a frame
			// that pass is timing. A person walking this same street needs
			// exactly the opposite, or a Character's capsule falls straight
			// through a pavement with NoCollision on it and the whole
			// deliverable is a screen showing the sky forever. QueryOnly is
			// enough for a capsule sweep and costs nothing physics does.
			C->SetCollisionEnabled(bInteractive ? ECollisionEnabled::QueryOnly
			                                     : ECollisionEnabled::NoCollision);
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
	//
	// bInteractive IS NAMED AT EVERY CALL SITE, NEVER DEFAULTED: it turns
	// collision on for every spawned piece and skips the materials-test
	// control quads, both of which are wrong to add to a frame the
	// automation is timing and both of which are required for a person to
	// walk here at all. The automation's own call (Tick's WaitWorld case)
	// passes false; ALedgerGameMode's (LedgerVignetteShot::BuildInteractiveStreet,
	// this file) passes true.
	void BuildScene(UWorld* World, bool bInteractive)
	{
		int Boxes = 0, Cyls = 0, Planes = 0, Props = 0, Decals = 0, Skipped = 0, Emitted = 0;
		std::string Note = "none";

		// ---- THE MESH PIECE KIND'S OWN INSTRUMENT ------------------------
		// Props counts every mesh-kind piece that got an actor of any sort;
		// Meshes counts the ones that got a LOADED PROP MESH, and StandIns
		// the ones that fell back to a box. Meshes + StandIns == Props is the
		// identity the verdict can be checked against, and StandIns is what
		// now goes to SceneLine's propStandIns, whose denominator is the mesh
		// piece count: 0/23 means every prop is real, 23/23 means the import
		// step never ran.
		int Meshes = 0, StandIns = 0;
		// THE COLLISION TALLY AND ITS NAMES, KEPT BY THE TESTED HEADER. Its
		// denominator is Placed(), the readings actually taken, never the 23
		// the file asked for: a denominator larger than the set examined
		// turns a clean result into a false claim with a number on it.
		LedgerVignette::PropCollisionTally CollisionTally;
		// WHICH PROP NAMES GOT A REAL ASSET, so the burial reading below can
		// say whether a row's bounds came from the loaded mesh or from the
		// box stand-in. At most one entry per mesh piece.
		std::vector<std::string> FromAssetNames;
		// AND THE NAMED SUBJECT'S OWN READING, CAPTURED AT THE INSTANT IT WAS
		// ASKED. A6's subject is one piece, and the run's tally of twenty-three
		// cannot answer a question about one of them. The default says there
		// was no asset to ask rather than printing a word that would read as
		// a measurement of the box stand-in.
		std::string SubjectCollision = "no-asset-to-read";
		// PLACEMENT, MEASURED AGAINST THE BOX IT REPLACED, AT WORST over the
		// placed meshes with the piece it was worst ON captured at the same
		// instant. Two halves, because they answer different questions and
		// only one of them survives rotation:
		//   Centre: how far the placed mesh's WORLD bounds centre is from the
		//           x_m/y_m/z_m the file named. Valid at every rotation,
		//           because rotating about the bounds centre leaves the
		//           centre where it was, and it is the number the contract in
		//           vignette-scene.json's held_props.pivot_note is about.
		//   Size:   whether the loaded mesh is the size the spec box was.
		//           ONLY COMPARABLE on an axis-aligned piece: a world AABB
		//           around a mesh yawed 20 degrees is legitimately bigger
		//           than the box, so the comparable count ships its own
		//           denominator rather than letting two of twenty-three
		//           rotated props read as a size fault.
		double WorstCentreMm = 0.0, WorstSizeMm = 0.0;
		std::string WorstCentreOn = "nothing-measured";
		std::string WorstSizeOn = "nothing-measured";
		int SizeComparable = 0;
		// WHY A PIECE FELL BACK, capped, and the cap announces itself.
		std::vector<std::string> FellBack;

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
			if (P.Shape == "box") { A = SpawnPiece(World, Cube, P, Scale, bInteractive); if (A) ++Boxes; }
			else if (P.Shape == "cyl")
			{
				// THE CYLINDER'S AXIS IS LOCAL +y IN THE FILE'S FRAME, which
				// under this mapping is local +Z, and that is this engine's
				// cylinder's own axis. Height is sy_m and the diameter is
				// sx_m and sz_m, so the same scale vector is correct for
				// both shapes and no special case is needed.
				A = SpawnPiece(World, Cyl, P, Scale, bInteractive); if (A) ++Cyls;
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
				A = SpawnPiece(World, Plane, Q, QScale, bInteractive);
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
				// THE MESH PIECE KIND, WHICH IS A REAL MESH WHEN THE IMPORT
				// STEP RAN AND THE BOX STAND-IN WHEN IT DID NOT.
				//
				// The GLBs under ledger/Assets/Props/base-mesh become uassets
				// in a build step, by tools/ue/import_prop_meshes.py, never by
				// a human in an editor. This engine still has no runtime
				// importer and does not need one: the piece names an asset,
				// the path is derived from that name alone, and a path that
				// resolves to nothing falls back to the box this branch used
				// to always spawn, COUNTED AND NAMED, so a missing import can
				// never read as a loaded model.
				std::string WhyNot;
				UStaticMesh* PropMesh = LoadPropMesh(P.Asset, WhyNot);
				if (PropMesh != nullptr)
				{
					// SCALE 1, AND NEVER ANYTHING ELSE. The dims policy in
					// production/specs/vignette-scene.json forbids inventing a
					// size, and tools/ue/import_prop_meshes.py --selftest has
					// MEASURED that each spec box is its GLB's own dimensions
					// (worst 0.0000 mm over 16 assets): so the mesh is already
					// the size the street drew, and passing Scale here would
					// square it.
					A = SpawnPiece(World, PropMesh, P, FVector(1.0f, 1.0f, 1.0f), bInteractive);
					if (A != nullptr)
					{
						// THE PIVOT CORRECTION, FROM THE ENGINE'S OWN READING
						// OF THE MESH AND NOT FROM A CONVENTION. The file
						// names where the prop's BOUNDING BOX CENTRE goes;
						// the source pivots are measured to be all over the
						// place (awning_02's origin is at its top-back,
						// the posters are centred, drainage_grate_01 hangs
						// 15 mm below its origin, the rest stand on it), so
						// the correction is the mesh's own local bounds
						// centre, which the engine hands back, rotated into
						// the actor's frame the same way the decal lift above
						// is. Scale is 1 here, which is the only reason this
						// offset needs no scale term.
						const FVector LocalCentre = PropMesh->GetBounds().Origin;
						A->AddActorWorldOffset(
							A->GetActorRotation().RotateVector(-LocalCentre));

						// READ BACK WHERE IT LANDED. 1 uu is 1 cm, so uu * 10
						// is mm.
						FVector WOrg(0, 0, 0), WExt(0, 0, 0);
						A->GetActorBounds(false, WOrg, WExt);
						const FVector WantUU(P.X * 100.0, P.Z * 100.0, P.Y * 100.0);
						const double CentreMm = (WOrg - WantUU).Size() * 10.0;
						if (CentreMm > WorstCentreMm || WorstCentreOn == "nothing-measured")
						{
							WorstCentreMm = CentreMm;
							WorstCentreOn = NoSpaces(P.Name);
						}

						// THE SIZE HALF, ON AXIS-ALIGNED PIECES ONLY.
						const double AbsYaw = P.YawDeg < 0 ? -P.YawDeg : P.YawDeg;
						const bool bQuarter = (AbsYaw > 89.0 && AbsYaw < 91.0)
						                   || (AbsYaw > 269.0 && AbsYaw < 271.0);
						const bool bHalf = (AbsYaw < 1.0) || (AbsYaw > 179.0 && AbsYaw < 181.0)
						                || (AbsYaw > 359.0);
						if (P.PitchDeg == 0.0 && P.RollDeg == 0.0 && (bQuarter || bHalf))
						{
							double WantX = P.SX * 100.0, WantY = P.SZ * 100.0;
							const double WantZ = P.SY * 100.0;
							if (bQuarter) { const double T = WantX; WantX = WantY; WantY = T; }
							const double DX = (WExt.X * 2.0 - WantX) * 10.0;
							const double DY = (WExt.Y * 2.0 - WantY) * 10.0;
							const double DZ = (WExt.Z * 2.0 - WantZ) * 10.0;
							double Worst = DX < 0 ? -DX : DX;
							const double AY = DY < 0 ? -DY : DY;
							const double AZ = DZ < 0 ? -DZ : DZ;
							if (AY > Worst) { Worst = AY; }
							if (AZ > Worst) { Worst = AZ; }
							++SizeComparable;
							if (Worst > WorstSizeMm || WorstSizeOn == "nothing-measured")
							{
								WorstSizeMm = Worst;
								WorstSizeOn = NoSpaces(P.Name);
							}
						}

						// COLLISION, READ OFF THE ASSET RATHER THAN TRUSTED
						// FROM THE IMPORT STEP'S OWN VERDICT, AND
						// THREE-VALUED: YES, NO, or UNKNOWN for an asset that
						// answered nothing. The tally and the string are the
						// tested header's.
						const LedgerVignette::EPropCollisionRead Read =
							PropCollisionOf(PropMesh);
						CollisionTally.Add(P.Name, Read);
						FromAssetNames.push_back(P.Name);
						if (P.Name == LedgerVignette::BurialSubjectName())
						{
							SubjectCollision = LedgerVignette::PropCollisionWord(Read);
						}

						++Meshes; ++Props;
					}
					else
					{
						WhyNot = "spawn-refused";
					}
				}
				if (A == nullptr)
				{
					// THE BOX STAND-IN, UNCHANGED, AND STILL THE RIGHT
					// FALLBACK. A box of the prop's OWN stated size holds the
					// space so the frame stays comparable to the Unity pair.
					A = SpawnPiece(World, Cube, P, Scale, bInteractive);
					if (A != nullptr)
					{
						++Boxes; ++Props; ++StandIns;
						if (FellBack.size() < 4)
						{
							FellBack.push_back(NoSpaces(P.Name) + "=" + NoSpaces(WhyNot));
						}
					}
				}
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
			if (L != nullptr)
			{
				GLanterns.Add(L);
				GLanternNames.push_back(NoSpaces(P.Name));
			}
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
			if (L != nullptr)
			{
				GWindows.Add(L);
				GWindowNames.push_back(NoSpaces(GSpec.Windows.LitNames[I]));
			}
			else { ++WindowsUnplaced; }
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
			// QUEUE 186: THE SKY, SPAWNED HERE AND WRITTEN ONLY BY
			// ApplyCondition, exactly as the fog above it is.
			//
			// ORDER MATTERS AND IS NOT COSMETIC: the atmosphere is the thing
			// the sky light captures, so it exists first. A sky light that
			// captures before there is anything to capture holds a black
			// cubemap, which is the exact failure the fill-light constant
			// block above named ("it cannot come back black the way a sky
			// light with nothing to capture can") before any of this existed.
			GAtmosphere = World->SpawnActor<ASkyAtmosphere>(
				ASkyAtmosphere::StaticClass(), FVector(0, 0, 0), FRotator::ZeroRotator, Params);
			MakeMovable(GAtmosphere);
			GSky = World->SpawnActor<ASkyLight>(
				ASkyLight::StaticClass(), FVector(0, 0, 300), FRotator::ZeroRotator, Params);
			MakeMovable(GSky);
			// FOUND BY COMPONENT CLASS, NOT BY THE ACTOR'S NAMED GETTER,
			// which is the rule this file already follows for the fog and
			// for the same reason: a named accessor has been renamed across
			// engine versions and this container cannot compile one line of
			// this file to find out.
			if (GSky != nullptr)
			{
				if (USkyLightComponent* SC = GSky->FindComponentByClass<USkyLightComponent>())
				{
					// CAPTURED SCENE, IN REAL TIME. The thing that is SEEN
					// and the thing that is REFLECTED are then the same
					// object, which is the whole reason this is not an HDRI
					// ambient standing behind an unrelated backdrop.
					SC->SourceType = ESkyLightSourceType::SLS_CapturedScene;
					SC->bRealTimeCapture = true;
					SC->SetIntensity(0.0f);
					SC->MarkRenderStateDirty();
				}
			}
		}

		// StandIns, NOT Props, IS WHAT propStandIns MEANS. Its denominator in
		// SceneLine is the mesh piece count, so 0/23 reads "every prop is a
		// real mesh" and 23/23 reads "the import step did not reach this
		// build". Passing Props here, as this call did while every mesh piece
		// was a box, would have made those two indistinguishable the moment
		// one prop became real.
		GSceneLine = SceneLine(GSpec, Emitted, Boxes, Cyls, Planes, StandIns, Decals,
		                       GLanterns.Num(), GWindows.Num(), Skipped, Note);

		// ---- THE MESH ROUTE'S OWN SEGMENT, APPENDED --------------------
		// Appended rather than folded into SceneLine because SceneLine is the
		// tested header's shared shape and both engines read it; these keys
		// are this engine's mesh route and nothing in Unity has them.
		//
		// NOT ONE NUMBER AND NOT ONE CHARACTER OF THIS STRING IS DECIDED
		// HERE, amendment A5 of the ruling of 2026-09-08. The tally, the
		// arithmetic and the formatting are LedgerVignette::PropMeshSegment,
		// which g++ compiles and RUNS in the container before any dispatch;
		// this block supplies membership, order and live state. The version
		// this replaces built its own string in this file, which nothing here
		// can compile, and shipped three faults in one eight-line stretch for
		// three landed runs.
		{
			// THE PLACED BOUNDS OF EVERY PIECE, READ BACK OFF THE ENGINE AND
			// NEVER RECOMPUTED FROM THE FILE. This is the half of the
			// placement metric propCentreWorstMm cannot see: a piece sits
			// 0.00 mm from where the file put it and is still inside the
			// road. GByName holds exactly the actors this BuildScene spawned,
			// so the population is the street's own pieces and nothing the
			// crime probe added to its separate map.
			std::vector<LedgerVignette::PlacedBox> Placed;
			Placed.reserve(GSpec.Pieces.size());
			for (size_t I = 0; I < GSpec.Pieces.size(); ++I)
			{
				const Piece& P = GSpec.Pieces[I];
				AStaticMeshActor** Found =
					GByName.Find(FString(UTF8_TO_TCHAR(P.Name.c_str())));
				if (Found == nullptr || *Found == nullptr) { continue; }
				FVector WOrg(0, 0, 0), WExt(0, 0, 0);
				(*Found)->GetActorBounds(false, WOrg, WExt);
				LedgerVignette::PlacedBox B;
				B.Name = P.Name; B.Edge = P.Edge; B.Region = P.Region;
				B.bProp = (P.Shape == "mesh");
				for (size_t K = 0; K < FromAssetNames.size(); ++K)
				{
					if (FromAssetNames[K] == P.Name) { B.bFromAsset = true; break; }
				}
				// BACK INTO THE FILE'S FRAME AND INTO METRES, which is the
				// only frame the tested header knows and the frame every
				// number in vignette-pieces.json is in: (X,Y,Z) uu is
				// (x,z,y) m, so the engine's Z is the file's y and 1 uu is
				// 1 cm. Inverting the one conversion this file does at spawn,
				// rather than carrying a second convention into the header.
				B.MinX = (WOrg.X - WExt.X) / 100.0; B.MaxX = (WOrg.X + WExt.X) / 100.0;
				B.MinY = (WOrg.Z - WExt.Z) / 100.0; B.MaxY = (WOrg.Z + WExt.Z) / 100.0;
				B.MinZ = (WOrg.Y - WExt.Y) / 100.0; B.MaxZ = (WOrg.Y + WExt.Y) / 100.0;
				Placed.push_back(B);
			}
			LedgerVignette::PropSegmentIn Seg;
			Seg.MeshPiecesInFile = ShapeCount(GSpec.Pieces, "mesh");
			Seg.PlacedAsMesh = Meshes;
			Seg.PlacedAsBox = StandIns;
			Seg.FellBackOn = FellBack;
			Seg.PackageDir = TCHAR_TO_UTF8(kPropPackageDir);
			Seg.NamePrefix = TCHAR_TO_UTF8(kPropNamePrefix);
			Seg.CentreWorstMm = WorstCentreMm;
			Seg.CentreWorstOn = WorstCentreOn;
			Seg.SizeWorstMm = WorstSizeMm;
			Seg.SizeWorstOn = WorstSizeOn;
			Seg.SizeComparable = SizeComparable;
			Seg.Collision = CollisionTally;
			Seg.SubjectCollision = SubjectCollision;
			Seg.Burials = LedgerVignette::ReadBurials(Placed);
			Seg.bInteractive = bInteractive;
			GSceneLine += " ";
			GSceneLine += LedgerVignette::PropMeshSegment(Seg);
		}
		// THE SPAWNS THAT ARE NOT PIECES, READ BACK RATHER THAN ASSUMED. A
		// null here is why a frame would be black, and it is a different
		// fault from an empty street.
		char Buf[420];
		std::snprintf(Buf, sizeof(Buf),
			" sun=%s fill=%d/3 fog=%s"
			" lampGain=%.2f fogGain=%.2f"
			" lightUnits=unitless/not-candelas decalLiftCm=%.1f decalModel=quad/phase-C-owns-the-decal",
			GSun ? "yes" : "SPAWN-FAILED",
			(GFillA ? 1 : 0) + (GFillB ? 1 : 0) + (GFillC ? 1 : 0),
			GFog ? "yes" : "SPAWN-FAILED",
			kLampGainUnitless, kFogDensityGain, kDecalLiftCm);
		GSceneLine += Buf;
		// ---- QUEUE 186: LOOK FOR THE HDRI THE SHARED FILE NAMES --------
		//
		// Done here, once, while the spec is loaded, and NOT bound to
		// anything. The reading rides the sky segment, which is taken when
		// the line is READ rather than now: see SkySegmentNow below.
		LookForNamedHdri();
		// PHASE C, AFTER EVERY PIECE IS SPAWNED AND NAMED. It reads GByName,
		// so it cannot run before the pieces are in it.
		BindSurfaces();
		// AND THE CONTROLS AFTER IT, because they instance the base material
		// BindSurfaces loads. A control quad in front of the camera is not a
		// piece and is not counted as one: the scene line's denominators come
		// off the file and none of them moves.
		//
		// SKIPPED FOR A PERSON WALKING HERE. The three colour-swatch planes
		// exist only to prove a material instance can be told apart from the
		// street around it in a photograph; standing them in front of the
		// player's own spawn point would be the first thing anyone sees, and
		// it answers a materials question nobody playing is asking.
		if (!bInteractive)
		{
			SpawnControlQuads(World, Plane);
		}
		else
		{
			GQuadDone = "controlQuadsStatus=SKIPPED controlQuads=nothing-measured"
			            " controlQuadsNote=interactive-build-does-not-spawn-the-materials-test-quads";
		}
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

	// IS THE SKY STRUCTURALLY THERE. Both actors and both components, asked
	// at the moment of the question and never remembered from the spawn: a
	// sky light with no atmosphere captures a black scene, and the two
	// halves fail independently.
	bool SkyIsWhole()
	{
		if (GSky == nullptr || GAtmosphere == nullptr) { return false; }
		return GSky->FindComponentByClass<USkyLightComponent>() != nullptr
		    && GAtmosphere->FindComponentByClass<USkyAtmosphereComponent>() != nullptr;
	}

	// THE ONLY WRITER OF THE SUN, THE FILL, THE FOG AND THE SKY. Every
	// condition change writes all of them, so no setting can carry over from
	// the previous shot and be attributed to this one.
	//
	// THE FILLS ARE RETIRED WHEN THE SKY IS WHOLE, AND ONLY THEN. Two
	// sources of ambient light in one scene is the fault this file's own
	// header calls the one this project has paid for twice, and a captured
	// sky is a strictly better statement of the same thing than three
	// directional lights standing in for an ambient mode. But a sky that
	// failed to spawn must not take the street's light away with it, so the
	// retirement is conditional on the structure being there and the scene
	// line prints which of the two happened.
	//
	// WHAT THIS CANNOT SEE, said here rather than discovered later: a sky
	// light whose capture comes back BLACK is structurally whole and would
	// retire the fills anyway. Nothing in this process can read the captured
	// cubemap's brightness. What answers it is the frame, and the sky and
	// ground bands on every shot line are that answer.
	void ApplyCondition(const Condition& C)
	{
		++GApplyCalls;
		const FLinearColor DaySky(0.42f, 0.46f, 0.52f, 1.0f);
		const FLinearColor NightSky(0.05f, 0.05f, 0.07f, 1.0f);
		const FLinearColor Sky = C.SunOn ? DaySky : NightSky;
		const bool bWhole = SkyIsWhole();
		SetDirectional(GSun, FLinearColor(0.95f, 0.96f, 1.0f, 1.0f), C.SunOn ? 3.0f : 0.0f);
		// THE FILLS AT ZERO ALSO STOP THEM BEING SUNS. A directional light
		// is an atmosphere sun light by default in this engine, so three
		// fills left burning would put up to two extra sun discs in the sky
		// the atmosphere renders. Zeroing them is one change that answers
		// two problems, and it is why no atmosphere-sun property is touched
		// anywhere in this file.
		const float FillScale = bWhole ? 0.0f : 1.0f;
		SetDirectional(GFillA, Sky, kFillSky * FillScale);
		SetDirectional(GFillB, Sky * 0.75f, kFillEquator * FillScale);
		SetDirectional(GFillC, Sky * 0.45f, kFillGround * FillScale);
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
				// AND THE FOG STOPS OWNING THE FAR FIELD, which is the
				// measurement that started this: with nothing behind it the
				// fog saturates at the far plane and IS the sky in every
				// frame this project has shot. Capped only when there is
				// something behind it to see; with no sky the fog keeps the
				// far field it has always had, so a failed spawn does not
				// also silently change the fog.
				F->SetFogMaxOpacity(bWhole ? kFogMaxOpacityWithSky : 1.0f);
			}
		}
		// ---- THE SKY, WRITTEN ON CHANGE AND NOT PER TICK ---------------
		//
		// This function is re-entered every tick while a condition settles.
		// A recapture per tick is a rebuild asked for four times, and the
		// count of asks against the count of writes rides the scene line so
		// nobody has to take this comment's word for it.
		if (bWhole && GSkyAppliedId != C.Id)
		{
			GSkyAppliedId = C.Id;
			++GSkyWrites;
			if (USkyAtmosphereComponent* A =
			        GAtmosphere->FindComponentByClass<USkyAtmosphereComponent>())
			{
				// PALE, FLAT AND LOW CONTRAST, which is what the reference
				// sheet's sky is and what a British overcast is. The four
				// values are named constants with their reasons at the top
				// of this file; none of them is measured and the verdict
				// says so.
				A->SetRayleighScatteringScale(kSkyRayleighScale);
				A->SetMieScatteringScale(kSkyMieScale);
				A->SetMieAnisotropy(kSkyMieAnisotropy);
				A->SetMultiScatteringFactor(kSkyMultiScattering);
			}
			if (USkyLightComponent* SC = GSky->FindComponentByClass<USkyLightComponent>())
			{
				SC->SetIntensity(C.SunOn ? kSkyIntensityDay : kSkyIntensityNight);
				// RECAPTURED EXPLICITLY ON THE CHANGE. Real-time capture
				// refreshes on its own, but a shot is photographed a fixed
				// number of frames after the condition changes and a sky
				// still carrying the previous condition would be attributed
				// to this one.
				SC->RecaptureSky();
			}
		}
	}

	// ---- QUEUE 186: WHAT THE SKY ACTUALLY IS, READ WHEN IT IS ASKED ------
	//
	// skyModel and ambientModel used to be two literals inside a format
	// string in BuildScene. One of them was false and no run could have said
	// so, because a literal in a printf cannot be wrong about the world in
	// any way a test can catch. Both words now come out of
	// LedgerVignette::SkySegment, which g++ runs before any dispatch, from
	// state READ BACK off the components.
	//
	// AND IT IS TAKEN HERE RATHER THAN AT BUILD TIME, which is not a detail:
	// BuildScene runs BEFORE any condition is applied, so a reading taken
	// there would report fillsRetiredToZero=no and skyWrites=0/of=0 on every
	// run for ever, and both would be stale rather than wrong-in-a-visible-
	// way. This runs when a verdict asks for the line, by which time every
	// condition the run applied has been applied.
	std::string SkySegmentNow()
	{
		LedgerVignette::SkyIn In;
		In.bSkyLightActor   = (GSky != nullptr);
		In.bAtmosphereActor = (GAtmosphere != nullptr);
		if (GSky != nullptr)
		{
			if (USkyLightComponent* SC = GSky->FindComponentByClass<USkyLightComponent>())
			{
				In.bSkyLightComponent   = true;
				In.SourceTypeRead       = (int)SC->SourceType;
				In.bRealTimeCaptureRead = (SC->bRealTimeCapture != 0);
				In.SkyIntensityRead     = (double)SC->Intensity;
			}
		}
		if (GAtmosphere != nullptr)
		{
			In.bAtmosphereComponent =
				(GAtmosphere->FindComponentByClass<USkyAtmosphereComponent>() != nullptr);
		}
		if (GFog != nullptr)
		{
			if (UExponentialHeightFogComponent* F =
			        GFog->FindComponentByClass<UExponentialHeightFogComponent>())
			{
				In.bFogComponent     = true;
				In.FogDensityRead    = (double)F->FogDensity;
				In.FogMaxOpacityRead = (double)F->FogMaxOpacity;
			}
		}
		In.FillsSpawned = (GFillA ? 1 : 0) + (GFillB ? 1 : 0) + (GFillC ? 1 : 0);
		// RETIRED IS READ OFF THE LIGHT, NEVER PREDICTED FROM THE RULE THAT
		// SETS IT. ApplyCondition zeroes the fills when the sky is whole;
		// asking the fill what its intensity IS is a different statement
		// from repeating the condition under which it should be zero, and
		// the two disagreeing is exactly what this key exists to show.
		In.bFillsRetired = false;
		if (GFillA != nullptr)
		{
			if (ULightComponent* LC = GFillA->GetLightComponent())
			{
				In.bFillsRetired = (LC->Intensity <= 0.0f) && In.Whole();
			}
		}
		In.ApplyCalls = (int)GApplyCalls;
		In.SkyWrites  = (int)GSkyWrites;
		// THE NAME COMES OUT OF THE SHARED FILE, not out of this file. The
		// condition block has always carried it and nothing has ever read it;
		// printing what was asked for beside what became of it is what turns
		// "the probe never binds the HDRI" from an analysis into a reading.
		In.HdriAsked = GSpec.Conditions.empty() ? std::string("none")
		                                       : GSpec.Conditions[0].Hdri;
		if (In.HdriAsked.empty()) { In.HdriAsked = "none"; }
		In.HdriFoundAt    = GHdriFoundAt;
		In.HdriBytes      = GHdriBytes;
		In.HdriDetectedAs = GHdriDetectedAs;
		In.HdriBoundAs    = "NOTHING/a-skylight-takes-a-cube-and-this-engine-builds-none-at-runtime";
		return LedgerVignette::SkySegment(In);
	}

	// ONE PRODUCER FOR THE LINE ALL FOUR VERDICTS PRINT. The vignette, the
	// walk and the crime runs each print the street's scene line, and a sky
	// appended in one of those places and not the others would be three
	// answers to one question.
	std::string SceneLineWithSky()
	{
		return GSceneLine + " " + SkySegmentNow();
	}

	// A CVAR THIS ENGINE VERSION DOES NOT CARRY PRINTS THE WORD `absent`.
	// A missing cvar read as 0 is the same string a disabled feature prints,
	// and the two are different facts.
	FString CVarIntOrAbsent(const TCHAR* Name)
	{
		if (IConsoleVariable* V = IConsoleManager::Get().FindConsoleVariable(Name))
		{
			return FString::Printf(TEXT("%d"), V->GetInt());
		}
		return TEXT("absent");
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
				// WHAT THE TONE MAPPER IS SET TO, READ BACK RATHER THAN
				// ASSUMED, because a clipped ground plane is a question about
				// exposure and this probe overrides nothing. The camera's own
				// post-process values are printed WITH their override flags,
				// since a value that is not overridden is not the value in
				// force; the cvars beside them are what actually decides, and
				// a cvar this engine version does not have prints `absent`
				// rather than a zero that would read as "off".
				const FPostProcessSettings& PP = CC->PostProcessSettings;
				GToneLine = FString::Printf(
					TEXT("tonemapRead=camera-postprocess-and-cvars ")
					TEXT("ppAutoExposureMethod=%d ppAutoExposureBias=%.3f ")
					TEXT("ppAutoExposureMinBrightness=%.4f ppAutoExposureMaxBrightness=%.4f ")
					TEXT("ppOverridesMethod/Bias/Min/Max=%d/%d/%d/%d ")
					TEXT("cvarDefaultAutoExposure=%s cvarDefaultAutoExposureMethod=%s ")
					TEXT("cvarEyeAdaptationMethodOverride=%s cvarExtendDefaultLuminanceRange=%s ")
					TEXT("tonemapStat=last-camera-placement/one-per-run ")
					TEXT("ppNote=this-probe-overrides-nothing/cvars-are-what-is-in-force"),
					(int32)PP.AutoExposureMethod, PP.AutoExposureBias,
					PP.AutoExposureMinBrightness, PP.AutoExposureMaxBrightness,
					PP.bOverride_AutoExposureMethod ? 1 : 0,
					PP.bOverride_AutoExposureBias ? 1 : 0,
					PP.bOverride_AutoExposureMinBrightness ? 1 : 0,
					PP.bOverride_AutoExposureMaxBrightness ? 1 : 0,
					*CVarIntOrAbsent(TEXT("r.DefaultFeature.AutoExposure")),
					*CVarIntOrAbsent(TEXT("r.DefaultFeature.AutoExposure.Method")),
					*CVarIntOrAbsent(TEXT("r.EyeAdaptation.MethodOverride")),
					*CVarIntOrAbsent(TEXT("r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange")));
				// ---- QUEUE 186: WHAT, IF ANYTHING, THE ROAD CAN REFLECT --
				//
				// A sky that lights a scene and a sky that is MIRRORED in
				// wet stone are two different renderer paths, and only the
				// second is what the reference panel's lower half is made
				// of. Which paths this build has is not a thing to reason
				// about from documentation: these four cvars decide it and
				// the run can simply read them. `absent` is a real answer
				// and different from 0, which is why CVarIntOrAbsent exists.
				//
				// HOW TO READ THEM. reflectionMethod 1 is Lumen and 2 is
				// screen space in this engine's numbering; a 0 means the
				// only reflection any surface gets is the sky light's own
				// cubemap. skylightRealTimeReflectionCapture is the one that
				// decides whether the cubemap this run captures is used for
				// reflections at all, and a 0 there would mean the sky lights
				// the street and NOTHING mirrors it.
				GToneLine += FString::Printf(
					TEXT(" cvarReflectionMethod=%s cvarDynamicGI=%s ")
					TEXT("cvarSkyLightRealTimeReflectionCapture=%s cvarSkyAtmosphere=%s ")
					TEXT("reflectStat=cvars-read-at-the-last-camera-placement/one-per-run ")
					TEXT("reflectNote=these-say-which-reflection-paths-exist/NOT-that-any-surface-is-wet"),
					*CVarIntOrAbsent(TEXT("r.ReflectionMethod")),
					*CVarIntOrAbsent(TEXT("r.DynamicGlobalIlluminationMethod")),
					*CVarIntOrAbsent(TEXT("r.SkyLight.RealTimeReflectionCapture")),
					*CVarIntOrAbsent(TEXT("r.SkyAtmosphere")));
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
		Out.Add(TEXT("# a shot status of WROTE needs a decoded file with more than one bucket and"));
		Out.Add(TEXT("#   at least one non-black pixel. BLANK, UNDECODABLE and NO-FILE are the three"));
		Out.Add(TEXT("#   ways it fails, and the step exits non-zero for all three with the evidence"));
		Out.Add(TEXT("#   still committed."));
		Out.Add(TEXT("# QUEUE 059, THE TWO MEASUREMENTS RUN 17 DID NOT HAVE. Its lantern count read"));
		Out.Add(TEXT("#   four of four and answered `were four lights created`, while both night"));
		Out.Add(TEXT("#   frames were black; its mean luma read 0.5030 over a day frame whose ground"));
		Out.Add(TEXT("#   plane was entirely clipped. Neither number could see it. These can:"));
		Out.Add(TEXT("# shotClipHiAny/shotClipHiAll/shotClipLoAll: COUNTS of pixels at the top and"));
		Out.Add(TEXT("#   bottom of the 8-bit range over shotPixels, never a mean. shotLumaBands is"));
		Out.Add(TEXT("#   eight equal luma bands, band 0 darkest: a printed series, not a bound."));
		Out.Add(TEXT("# band.skyTop / band.skyCentre / band.ground: THREE GEOMETRIC BANDS of THIS"));
		Out.Add(TEXT("#   frame, named for what they COVER and not for what is in them. skyTop is"));
		Out.Add(TEXT("#   the top eighth full width and carries roofline as well as sky; skyCentre"));
		Out.Add(TEXT("#   is the middle fifth of it; ground is the bottom fifth. Each ships its own"));
		Out.Add(TEXT("#   pixel count as its denominator and its own rectangle in pixels, and a"));
		Out.Add(TEXT("#   rectangle covering no pixel reads NOTHING-MEASURED rather than dark."));
		Out.Add(TEXT("#   meanRGB is printed because a sky and a fog inscattering colour are told"));
		Out.Add(TEXT("#   apart by CHANNEL ORDER: before the sky landed, the day far field read"));
		Out.Add(TEXT("#   249.5/250.0/250.5 and the night one 188.4/179.6/179.3, which are the day"));
		Out.Add(TEXT("#   and night fog colours and not a sky. A printed series, not a bound."));
		Out.Add(TEXT("# bandGroundOverSky: one ratio of two measured means. A ground LIT by a sky"));
		Out.Add(TEXT("#   and a ground MIRRORING one both raise it; the ground band's own spread is"));
		Out.Add(TEXT("#   what separates them, because a mirror adds variation and a lamp does not."));
		Out.Add(TEXT("# skyModel / ambientModel: READ BACK off the components after the write. Both"));
		Out.Add(TEXT("#   were hardcoded literals in a format string until 2026-09-09 and one of"));
		Out.Add(TEXT("#   them was false. skyWrites=N/of=M is write-on-change: M is how many times"));
		Out.Add(TEXT("#   ApplyCondition ran and N how many times the sky was rewritten, and N<M is"));
		Out.Add(TEXT("#   the point rather than a fault. skyHdriBoundAs says NOTHING on purpose:"));
		Out.Add(TEXT("#   this run looks for the HDRI the shared file names and binds none of it."));
		Out.Add(TEXT("# light lines: one per probed light, the SAME camera, condition and frame"));
		Out.Add(TEXT("#   counts as its shot with that one light switched off. deltaMeanFull is the"));
		Out.Add(TEXT("#   whole frame, deltaMeanPeak is the named grid cell in peakRegion, and both"));
		Out.Add(TEXT("#   halves of every difference are printed beside it (meanOn.. and meanOff..)."));
		Out.Add(TEXT("# THE CONTROL LINE TOGGLES NOTHING and is this run's own noise floor. A"));
		Out.Add(TEXT("#   lantern whose histogram does not clear the control's did not light the"));
		Out.Add(TEXT("#   frame. No threshold is set here: read the series, set the bound after."));
		Out.Add(TEXT("# NO BOUND IN THIS RUN. lampGain and fogGain are unchanged first values and"));
		Out.Add(TEXT("#   the picture is not to be fixed before it is measured."));
		Out.Add(TEXT("# PHASE C, MATERIALS. One surface line per surface the shared file asked for,"));
		Out.Add(TEXT("#   with what each map LOADED AS rather than what its filename claims, and the"));
		Out.Add(TEXT("#   candidates tried for every map that is not there. The base material is a"));
		Out.Add(TEXT("#   BUILD PRODUCT made by tools/ue/make_base_material.py in the cook step: no"));
		Out.Add(TEXT("#   human opens the editor, which is D1 measurement (a) in one line."));
		Out.Add(TEXT("#   materialBase reads MISSING when the cook did not carry the asset, and"));
		Out.Add(TEXT("#   every surface below is then untextured however many maps decoded."));
		Out.Add(TEXT("# PHASE C, THE READBACK. Each surface line carries what the material"));
		Out.Add(TEXT("#   instance answered when asked for the texture and the two tiling"));
		Out.Add(TEXT("#   scalars straight back, and the materials line carries the run's"));
		Out.Add(TEXT("#   totals over the surfaces a parameter was actually set on. It is the"));
		Out.Add(TEXT("#   GAME thread's copy: a value that lands there and never reaches the"));
		Out.Add(TEXT("#   render proxy still reads back as the same pointer."));
		Out.Add(TEXT("# PHASE C, THE CONTROL QUADS. Three planes of one size at one distance"));
		Out.Add(TEXT("#   in front of the first shot's camera, off the same base material,"));
		Out.Add(TEXT("#   carrying no street data. The first binds a 2x2 texture built in code"));
		Out.Add(TEXT("#   from four saturated colours, with no file and no decode; the other"));
		Out.Add(TEXT("#   two bind no texture at all and differ only in their tiling scalars."));
		Out.Add(TEXT("#   Four colours on the first means a texture override reaches the"));
		Out.Add(TEXT("#   sampler. Two different cell counts on the other two means the scalar"));
		Out.Add(TEXT("#   overrides reach the shader. THE FRAME IS WHAT ANSWERS, not a count:"));
		Out.Add(TEXT("#   the quad lines say only where to look and what was asked for."));
		Out.Add(TEXT("#   The controls occupy their printed boxes, so any whole-frame statistic"));
		Out.Add(TEXT("#   taken from this run includes them and must exclude those boxes first."));
		Out.Add(TEXT("# NO COMMENT IN THIS HEADER WRITES A KEY WITH AN EQUALS AND A VALUE."));
		Out.Add(TEXT("#   Run 19 spelled this key out with MISSING beside it up here and"));
		Out.Add(TEXT("#   measured it as loaded down there, which tools/verdict-dupkeys.py"));
		Out.Add(TEXT("#   reads as one key with two values in one run. Every reader here"));
		Out.Add(TEXT("#   greps, and one of them takes the FIRST match. Keys are named in"));
		Out.Add(TEXT("#   prose above and measured below, never both."));
		Out.Add(TEXT(""));
		Out.Add(FString(UTF8_TO_TCHAR(SceneLineWithSky().c_str())));
		Out.Add(GCamLine);
		Out.Add(GToneLine);
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
		for (size_t I = 0; I < GBinds.size(); ++I)
		{
			Out.Add(FString(UTF8_TO_TCHAR(LedgerSurface::SurfaceLine(GBinds[I]).c_str())));
		}
		if (GBinds.empty())
		{
			Out.Add(TEXT("# no surface line: the material pass did not reach a surface."));
		}
		Out.Add(FString(UTF8_TO_TCHAR(GMaterialsLine.c_str())));
		// THE CONTROLS, AFTER THE SURFACES THEY ARE THE CONTROL FOR. One line
		// per quad with its own placement and where it should land on the
		// frame, then the pass's own totals. A run that spawned none of them
		// still prints the done line, which says so in words.
		for (size_t I = 0; I < GQuadLines.size(); ++I)
		{
			Out.Add(FString(UTF8_TO_TCHAR(GQuadLines[I].c_str())));
		}
		if (GQuadLines.empty())
		{
			Out.Add(TEXT("# no control quad line: the control pass reached no quad."));
		}
		Out.Add(FString(UTF8_TO_TCHAR(GQuadDone.c_str())));
		// AND WHETHER THE CONTROLS WERE IN THE FRAME OR NOT, per shot,
		// formatted in the tested header.
		Out.Add(FString(UTF8_TO_TCHAR(LedgerSurface::ControlQuadVisibilityLine(
			GQuadShotsSeen, GQuadHidden, GQuadHiddenIds).c_str())));
		if (GLightLines.empty())
		{
			Out.Add(TEXT("# no light was probed on this commit; the pass line below says why."));
		}
		else
		{
			for (size_t I = 0; I < GLightLines.size(); ++I)
			{
				Out.Add(FString(UTF8_TO_TCHAR(GLightLines[I].c_str())));
			}
		}
		Out.Add(FString(UTF8_TO_TCHAR(LedgerFrame::LightProbeDoneLine(
			GProbed, GEligible, GReached, GSkippedOff, GSkippedBudget, GProbeNoFile,
			GRestoreMismatch, GShotsProbed, (int)GSpec.Shots.size(),
			kLightProbeBudgetSeconds, GProbeSpent,
			kWarmFrames + kTimedFrames, GControls).c_str())));
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
		// THE PROBE'S SCRATCH FRAME IS NOT EVIDENCE AND DOES NOT SURVIVE THE
		// RUN. Scoped to exactly the one file this pass wrote.
		IFileManager::Get().Delete(*AbsProject(kProbePngLeaf), false, true, true);
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

	// ---- queue 059 (a): the lights this pass can ask about ---------------
	//
	// ONE ORDER, ONE PLACE. The lanterns first and the practicals after, and
	// every accessor below reads that one order, so a light's index on its
	// verdict line and the light this code toggled cannot drift apart.
	int32 ProbeTargetCount()
	{
		return GLanterns.Num() + GWindows.Num();
	}

	APointLight* ProbeLight(int32 I)
	{
		if (I < 0) { return nullptr; }
		if (I < GLanterns.Num()) { return GLanterns[I]; }
		const int32 J = I - GLanterns.Num();
		return (J < GWindows.Num()) ? GWindows[J] : nullptr;
	}

	std::string ProbeId(int32 I)
	{
		if (I >= 0 && I < GLanterns.Num())
		{
			return (size_t)I < GLanternNames.size() ? GLanternNames[(size_t)I]
			                                        : std::string("lantern-unnamed");
		}
		const int32 J = I - GLanterns.Num();
		if (J >= 0 && (size_t)J < GWindowNames.size()) { return GWindowNames[(size_t)J]; }
		return std::string("light-unnamed");
	}

	const char* ProbeKind(int32 I)
	{
		return (I < GLanterns.Num()) ? "lantern" : "practical";
	}

	// A SHOT IS PROBED IF ITS CONDITION HAS ANY OF THESE LIGHTS ON. Probing a
	// condition that turned the lanterns off would measure a difference of
	// zero and print it beside the word lantern, which is exactly the false
	// reading this item exists to stop.
	bool ShouldProbeShot(const Shot& S)
	{
		const Condition* C = FindCondition(S.ConditionId);
		if (C == nullptr) { return false; }
		return (C->LanternsOn && GLanterns.Num() > 0) || (C->WindowsOn && GWindows.Num() > 0);
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
		// AND WHAT THE TONE MAPPER DID TO THIS FRAME, as counts with their
		// denominator at both ends. shotMeanLuma=0.5030 sat over a day frame
		// whose whole ground plane was clipped, because a mean cannot see
		// clipping; these keys can, and the eight luma bands are the series a
		// bound gets read off later rather than invented now.
		Line += " ";
		Line += LedgerFrame::ExposureLine(
			LedgerFrame::MeasureExposure((const unsigned char*)Bgra.GetData(), W, H));
		// AND WHAT THE SKY AND THE GROUND ARE IN THIS FRAME, QUEUE 186.
		// shotMeanLuma is a mean over the whole picture and cannot tell a
		// sky that arrived from a fog colour that never left; three named
		// geometric bands can, and their channel means are what separate a
		// sky's colour from an inscattering colour. Per-sample keys on the
		// sample line, because these are statistics of THIS frame.
		{
			const unsigned char* Px = (const unsigned char*)Bgra.GetData();
			const LedgerFrame::BandStats SkyTop = LedgerFrame::MeasureBand(
				Px, W, H, "skyTop", 0.0, 0.0, 1.0, LedgerFrame::SkyTopY1());
			const LedgerFrame::BandStats SkyCentre = LedgerFrame::MeasureBand(
				Px, W, H, "skyCentre", LedgerFrame::SkyCentreX0(), 0.0,
				LedgerFrame::SkyCentreX1(), LedgerFrame::SkyTopY1());
			const LedgerFrame::BandStats Ground = LedgerFrame::MeasureBand(
				Px, W, H, "ground", 0.0, LedgerFrame::GroundY0(), 1.0, 1.0);
			Line += " ";
			Line += LedgerFrame::SkyBandLine(SkyTop, SkyCentre, Ground);
		}
		GShotLines.push_back(Line);
		if (GArt.empty())
		{
			GArt = LedgerFrame::AsciiLuma((const unsigned char*)Bgra.GetData(), W, H);
		}
		// THE REFERENCE HALF OF EVERY DIFFERENCE THIS SHOT IS ABOUT TO TAKE.
		// Kept only when the shot is going to be probed, and dropped
		// otherwise, so no later probe can diff against another shot's frame.
		if (ShouldProbeShot(S))
		{
			GRefBgra = MoveTemp(Bgra);
			GRefW = W; GRefH = H;
			GRefShotId = S.Id;
		}
		else
		{
			GRefBgra.Empty();
			GRefW = 0; GRefH = 0;
			GRefShotId.clear();
		}
	}

	FString ShotPngPath(const Shot& S)
	{
		return AbsProject(*FString::Printf(TEXT("ue-%s.png"), UTF8_TO_TCHAR(S.Id.c_str())));
	}

	// ONE SCRATCH PATH, OVERWRITTEN BY EVERY PROBE AND DELETED AT THE END.
	// A probe frame is half of a difference and the difference is the
	// finding, so fourteen of them are not evidence worth committing; the
	// step stages by name and would not collect them in any case.
	FString ProbePngPath()
	{
		return AbsProject(kProbePngLeaf);
	}

	void EmitLightLine(const Shot& S, int32 Seq, const char* Status,
	                   const LedgerFrame::LightDelta& D, const std::string& Note)
	{
		const std::string Id = (Seq < 0) ? std::string("control_no_toggle") : ProbeId(Seq);
		const char* Kind = (Seq < 0) ? "control" : ProbeKind(Seq);
		GLightLines.push_back(LedgerFrame::LightDeltaLine(
			Id, Kind, Seq + 1, ProbeTargetCount(), S.Id, S.CameraId, S.ConditionId,
			Status, D, Note));
	}

	// ADVANCE TO THE NEXT THING TO PHOTOGRAPH, OR END THE PASS.
	//
	// Sequence -1 is the CONTROL: the same camera, the same condition, the
	// same frame counts and NOTHING TOGGLED. Its delta against the reference
	// is this run's own noise floor, which is why no epsilon had to be
	// invented for "did this light reach a pixel".
	//
	// A LIGHT ALREADY OFF IN THIS CONDITION IS NOT PHOTOGRAPHED. Toggling it
	// would measure a difference of zero and print it beside the word
	// lantern, which is the false reading this whole item exists to stop.
	bool BeginNextProbe(const Shot& S)
	{
		while (true)
		{
			++GProbeSeq;
			if (GProbeSeq == -1)
			{
				++GControls;
				GProbeStarted = FPlatformTime::Seconds();
				return true;
			}
			if (GProbeSeq >= ProbeTargetCount()) { return false; }
			APointLight* L = ProbeLight(GProbeSeq);
			ULightComponent* LC = (L != nullptr) ? L->GetLightComponent() : nullptr;
			if (LC == nullptr)
			{
				EmitLightLine(S, GProbeSeq, "NO-LIGHT-COMPONENT", LedgerFrame::LightDelta(),
				              "the-spawned-actor-carried-no-light-component");
				continue;
			}
			// READ BACK WHAT THE CONDITION LEFT, never assume it.
			const bool bOn = LC->IsVisible();
			if (!bOn)
			{
				++GSkippedOff;
				EmitLightLine(S, GProbeSeq, "SKIPPED-ALREADY-OFF", LedgerFrame::LightDelta(),
				              "off-in-this-condition/nothing-to-difference");
				continue;
			}
			++GEligible;
			if (GProbeSpent >= kLightProbeBudgetSeconds)
			{
				// THE CAP ANNOUNCES WHEN IT BITES, and the loop keeps
				// counting the rest so the denominator stays true.
				++GSkippedBudget;
				continue;
			}
			GProbeVisWas = bOn;
			LC->SetVisibility(false);
			GProbeStarted = FPlatformTime::Seconds();
			return true;
		}
	}

	// PUT BACK WHAT WAS CAPTURED, THEN READ IT BACK. A probe that restores a
	// value it guessed at leaves the run's evidence frames lit by the
	// probe's idea of the scene, and a restore nobody read back is a claim.
	void RestoreProbeLight()
	{
		if (GProbeSeq < 0) { return; }
		APointLight* L = ProbeLight(GProbeSeq);
		ULightComponent* LC = (L != nullptr) ? L->GetLightComponent() : nullptr;
		if (LC == nullptr) { return; }
		LC->SetVisibility(GProbeVisWas);
		if (LC->IsVisible() != GProbeVisWas) { ++GRestoreMismatch; }
	}

	// THE DIFFERENCE, TAKEN IN THE TESTED HEADER. On is the reference frame,
	// which had this light lit; Off is the frame just taken with it dark.
	void MeasureProbe(const Shot& S, const FString& Path, bool bHaveFile)
	{
		GProbeSpent += FPlatformTime::Seconds() - GProbeStarted;
		LedgerFrame::LightDelta NoPair;
		if (!bHaveFile)
		{
			++GProbeNoFile;
			EmitLightLine(S, GProbeSeq, "NO-FILE", NoPair, std::string(TCHAR_TO_UTF8(*GNote)));
			return;
		}
		TArray64<uint8> Bgra;
		int32 W = 0, H = 0;
		std::string Note("none");
		if (!DecodeBgra(Path, Bgra, W, H, Note))
		{
			++GProbeNoFile;
			EmitLightLine(S, GProbeSeq, "UNDECODABLE", NoPair, Note);
			return;
		}
		if (GRefBgra.Num() == 0 || W != GRefW || H != GRefH)
		{
			EmitLightLine(S, GProbeSeq, "NOT-COMPARABLE", NoPair,
			              "probe-and-reference-differ-in-size-or-the-reference-is-gone");
			return;
		}
		const LedgerFrame::LightDelta D = LedgerFrame::MeasureLightDelta(
			(const unsigned char*)GRefBgra.GetData(), (const unsigned char*)Bgra.GetData(),
			W, H, kProbeGridCols, kProbeGridRows);
		if (GProbeSeq >= 0)
		{
			++GProbed;
			// REACHED THE FRAME means at least one pixel rose by at least one
			// eight-bit code value. It is the first edge of the printed
			// histogram and not a tuned bound; the control line beside it is
			// what says whether that edge means anything in this run.
			if (D.RoseAtLeast[0] > 0) { ++GReached; }
		}
		EmitLightLine(S, GProbeSeq, "MEASURED", D, "none");
	}

	bool StartLightProbe(const Shot& S)
	{
		if (!ShouldProbeShot(S)) { return false; }
		if (GRefBgra.Num() == 0 || GRefShotId != S.Id)
		{
			EmitLightLine(S, -1, "NO-REFERENCE", LedgerFrame::LightDelta(),
			              "the-reference-frame-did-not-decode/nothing-to-difference-against");
			return false;
		}
		GProbing = true;
		GProbeSeq = -2;
		++GShotsProbed;
		if (!BeginNextProbe(S)) { GProbing = false; return false; }
		return true;
	}

	// WHAT HAPPENS WHEN A FRAME LANDS, IN ONE PLACE. The reference path and
	// the probe path differ only in what they measure, and a second copy of
	// this would drift the moment either changed.
	void AfterFrame(bool bHaveFile)
	{
		const Shot& S = GSpec.Shots[GShotIndex];
		if (GProbing)
		{
			MeasureProbe(S, GAskedPath, bHaveFile);
			RestoreProbeLight();
			if (BeginNextProbe(S))
			{
				// THE SAME FRAME COUNTS AS THE REFERENCE, which is why the
				// series is cleared: Timed stops when it holds 24 samples,
				// and a series left full from the reference would send the
				// probe to the camera after no settling at all.
				GFrameMs.clear();
				GPhase = EPhase::Warm;
				return;
			}
			GProbing = false;
			GRefBgra.Empty();
			GRefW = 0; GRefH = 0; GRefShotId.clear();
			++GShotIndex;
			GPhase = EPhase::ApplyShot;
			return;
		}
		MeasureShot(S, GAskedPath, bHaveFile);
		if (bHaveFile && StartLightProbe(S))
		{
			GFrameMs.clear();
			GPhase = EPhase::Warm;
			return;
		}
		++GShotIndex;
		GPhase = EPhase::ApplyShot;
	}

	// ---- PHASE C: THE PACK'S MAPS, IMPORTED AT RUNTIME -------------------
	//
	// MEASURE THE ASSET BEFORE PLACING IT, AND SAY WHAT IT LOADED AS. A file
	// is not what its extension claims: the decoder is asked what the bytes
	// are and the answer is printed beside the size it came back at, because
	// an import assumption that goes unread is this project's most expensive
	// recurring fault.
	//
	// THE FILENAME RULE IS THE UNITY HOST'S, read out of SurfaceBind.h,
	// which is the tested layer. Nothing here decides which file a surface
	// wants; this code only asks the disk and the decoder, and hands the
	// answers back to be counted and formatted where the tests run.
	const TCHAR* ImageFormatName(EImageFormat F)
	{
		switch (F)
		{
		case EImageFormat::PNG:  return TEXT("PNG");
		case EImageFormat::JPEG: return TEXT("JPEG");
		case EImageFormat::BMP:  return TEXT("BMP");
		case EImageFormat::EXR:  return TEXT("EXR");
		default:                 return TEXT("UNRECOGNISED");
		}
	}

	// THE TEXTURE ROOT IS LOOKED FOR IN NAMED PLACES AND THE ONE THAT
	// ANSWERED IS PRINTED, exactly as the spec file is. A packaged build runs
	// from Packaged/Windows and the checkout sits four directories above it;
	// a staged copy beside the exe is tried first so the step can choose to
	// carry the pack rather than reach for it.
	//
	// THE FIRST TWO CANDIDATES ARE THE CONTRACT. The workflow copies the
	// pack to `CityPackTextures` beside the staged project and beside the
	// binary, by name, exactly as it copies the piece list, and this search
	// is not widened to guess at a repository layout from a packaged binary.
	// Run 19 found nothing in all four because nothing had ever created the
	// first two and a packaged exe is not four directories under a checkout.
	//
	// EVERY CANDIDATE IS RECORDED WHETHER OR NOT IT ANSWERED. `NOT-FOUND`
	// with no list beside it cost run 19 a round trip: the question is which
	// of the pack and the search is in the wrong place, and only the list
	// answers it. The joining and the cap are in SurfaceBind.h, where g++
	// runs them before a dispatch.
	FString FindTexRoot(int32& OutFiles, std::vector<std::string>& OutTried)
	{
		const FString ExeDir = FPaths::GetPath(FPlatformProcess::ExecutablePath());
		TArray<FString> Cands;
		Cands.Add(AbsProject(TEXT("CityPackTextures")));
		Cands.Add(FPaths::ConvertRelativePathToFull(FPaths::Combine(ExeDir, TEXT("CityPackTextures"))));
		Cands.Add(AbsProject(TEXT("../ledger/Assets/StreamingAssets/CityPack/textures")));
		Cands.Add(FPaths::ConvertRelativePathToFull(FPaths::Combine(
			ExeDir, TEXT("../../../../ledger/Assets/StreamingAssets/CityPack/textures"))));
		// RECORDED AS IT IS ASKED, and the search still stops at the first
		// answer: a list of every candidate whether or not it was reached
		// would be named wrongly, since `tried` and `would have tried next`
		// are different facts. On a run that finds the pack the list ends
		// with the directory that answered.
		OutFiles = 0;
		for (int32 I = 0; I < Cands.Num(); ++I)
		{
			OutTried.push_back(std::string(TCHAR_TO_UTF8(*Cands[I])));
			if (!IFileManager::Get().DirectoryExists(*Cands[I])) { continue; }
			TArray<FString> Found;
			IFileManager::Get().FindFiles(Found, *(Cands[I] / TEXT("*.*")), true, false);
			if (Found.Num() == 0) { continue; }
			OutFiles = Found.Num();
			return Cands[I];
		}
		return FString();
	}

	UTexture2D* ImportTexture(const FString& FullPath, bool bSrgb,
	                          int32& OutW, int32& OutH, FString& OutLoadedAs)
	{
		OutW = 0; OutH = 0;
		OutLoadedAs = TEXT("not-read");
		TArray<uint8> Bytes;
		if (!FFileHelper::LoadFileToArray(Bytes, *FullPath) || Bytes.Num() == 0)
		{
			OutLoadedAs = TEXT("file-would-not-load-or-was-empty");
			return nullptr;
		}
		IImageWrapperModule* Mod =
			FModuleManager::Get().LoadModulePtr<IImageWrapperModule>(FName("ImageWrapper"));
		if (Mod == nullptr) { OutLoadedAs = TEXT("imagewrapper-module-missing"); return nullptr; }
		// WHAT THE BYTES ARE, ASKED RATHER THAN INFERRED FROM THE SUFFIX.
		const EImageFormat Fmt = Mod->DetectImageFormat(Bytes.GetData(), (int64)Bytes.Num());
		TSharedPtr<IImageWrapper> Wrapper = Mod->CreateImageWrapper(Fmt);
		if (!Wrapper.IsValid())
		{
			OutLoadedAs = FString::Printf(TEXT("no-wrapper-for-%s"), ImageFormatName(Fmt));
			return nullptr;
		}
		if (!Wrapper->SetCompressed(Bytes.GetData(), (int64)Bytes.Num()))
		{
			OutLoadedAs = FString::Printf(TEXT("%s-setcompressed-refused"), ImageFormatName(Fmt));
			return nullptr;
		}
		const int32 W = Wrapper->GetWidth();
		const int32 H = Wrapper->GetHeight();
		TArray64<uint8> Raw;
		if (W <= 0 || H <= 0 || !Wrapper->GetRaw(ERGBFormat::BGRA, 8, Raw))
		{
			OutLoadedAs = FString::Printf(TEXT("%s-getraw-refused"), ImageFormatName(Fmt));
			return nullptr;
		}
		UTexture2D* Tex = UTexture2D::CreateTransient(W, H, PF_B8G8R8A8);
		if (Tex == nullptr)
		{
			OutLoadedAs = FString::Printf(TEXT("%s-createtransient-returned-null"), ImageFormatName(Fmt));
			return nullptr;
		}
		// COLOUR SPACE IS SET BY WHAT THE MAP IS FOR, not by what the file
		// is: a normal or a roughness map read as sRGB is wrong by a gamma
		// curve, and the verdict prints which each one was treated as.
		Tex->SRGB = bSrgb;
		// KEPT ALIVE EXPLICITLY. A transient texture whose only reference is
		// a dynamic material instance is exactly the shape of object this
		// engine collects between two ticks.
		Tex->AddToRoot();
		void* Dest = Tex->GetPlatformData()->Mips[0].BulkData.Lock(LOCK_READ_WRITE);
		FMemory::Memcpy(Dest, Raw.GetData(), (SIZE_T)Raw.Num());
		Tex->GetPlatformData()->Mips[0].BulkData.Unlock();
		Tex->UpdateResource();
		OutW = W; OutH = H;
		OutLoadedAs = FString::Printf(TEXT("%s-BGRA8/srgb=%s"),
		                              ImageFormatName(Fmt), bSrgb ? TEXT("yes") : TEXT("no"));
		return Tex;
	}

	// QUEUE 186: IS THE NAMED HDRI EVEN REACHABLE FROM THIS BINARY.
	//
	// NOTHING IS BOUND HERE AND NOTHING MAY BE. A USkyLightComponent takes a
	// cube texture and this engine builds none at runtime, so a decoded
	// long-lat Radiance image would have nowhere to go. What this answers is
	// the ONE question the next rung turns on: whether the file the shared
	// condition block has always named can be opened from a packaged build
	// at all, or whether that rung needs a staging step in the workflow
	// first. Asking it costs one file-exists and one format detect; guessing
	// it costs a round trip on his PC.
	//
	// THE CANDIDATE LIST MIRRORS FindTexRoot's, deliberately, because the
	// pack and the sky would be staged by the same kind of step and a
	// different search would answer a different question. EVERY CANDIDATE IS
	// RECORDED whether or not it answered, for the reason run 19 established:
	// NOT-FOUND with no list beside it does not say whether the file or the
	// search is in the wrong place.
	void LookForNamedHdri()
	{
		if (GSpec.Conditions.empty() || GSpec.Conditions[0].Hdri.empty())
		{
			GHdriFoundAt = "NOT-LOOKED-FOR/the-shared-file-named-no-hdri";
			return;
		}
		const FString Leaf = FString(UTF8_TO_TCHAR(GSpec.Conditions[0].Hdri.c_str()))
		                   + FString(kSkyHdriExt);
		const FString ExeDir = FPaths::GetPath(FPlatformProcess::ExecutablePath());
		TArray<FString> Cands;
		Cands.Add(AbsProject(*(FString(TEXT("SkyHdri/")) + Leaf)));
		Cands.Add(FPaths::ConvertRelativePathToFull(
			FPaths::Combine(ExeDir, TEXT("SkyHdri"), *Leaf)));
		Cands.Add(AbsProject(*(FString(TEXT("../ledger/Assets/Resources/")) + Leaf)));
		Cands.Add(FPaths::ConvertRelativePathToFull(FPaths::Combine(
			ExeDir, TEXT("../../../../ledger/Assets/Resources"), *Leaf)));
		std::string Tried;
		for (int32 I = 0; I < Cands.Num(); ++I)
		{
			if (!Tried.empty()) { Tried += ";"; }
			Tried += NoSpaces(std::string(TCHAR_TO_UTF8(*Cands[I])));
			if (!IFileManager::Get().FileExists(*Cands[I])) { continue; }
			GHdriFoundAt = NoSpaces(std::string(TCHAR_TO_UTF8(*Cands[I])));
			GHdriBytes   = (long long)IFileManager::Get().FileSize(*Cands[I]);
			// WHAT THE BYTES ARE, ASKED RATHER THAN INFERRED FROM THE SUFFIX,
			// the same rule ImportTexture follows. The enum VALUE is printed
			// beside the name because this file's ImageFormatName knows four
			// formats and Radiance is not one of them: UNRECOGNISED/enum=8
			// and UNRECOGNISED/enum=-1 are different answers and the number
			// is what separates them.
			TArray<uint8> Head;
			if (FFileHelper::LoadFileToArray(Head, *Cands[I]) && Head.Num() > 0)
			{
				IImageWrapperModule* Mod =
					FModuleManager::Get().LoadModulePtr<IImageWrapperModule>(FName("ImageWrapper"));
				if (Mod != nullptr)
				{
					const EImageFormat Fmt =
						Mod->DetectImageFormat(Head.GetData(), (int64)Head.Num());
					// THE NAME IS TURNED INTO AN std::string BEFORE THE
					// FORMAT CALL rather than handed to a variadic as a
					// conversion temporary, which is the shape this file
					// already uses everywhere it crosses that boundary.
					const std::string FmtName(TCHAR_TO_UTF8(ImageFormatName(Fmt)));
					char B[160];
					std::snprintf(B, sizeof(B), "%s/enum=%d", FmtName.c_str(), (int)Fmt);
					GHdriDetectedAs = NoSpaces(std::string(B));
				}
				else { GHdriDetectedAs = "imagewrapper-module-missing"; }
			}
			else { GHdriDetectedAs = "file-would-not-load-or-was-empty"; }
			return;
		}
		GHdriFoundAt = "NOT-FOUND/tried=" + Tried;
	}

	// BIND EVERY SURFACE THE SHARED FILE ASKED FOR, and count what did not
	// answer. A Phase C that renders and cannot say what it failed to load is
	// worth less than one that loads less and says so.
	void BindSurfaces()
	{
		GBaseMaterial = LoadObject<UMaterialInterface>(nullptr, kBaseMaterialPath);
		GTexRoot = FindTexRoot(GTexRootFiles, GTexRootTried);
		const std::vector<LedgerSurface::Ask> Asked = LedgerSurface::SurfacesAsked(GSpec.Pieces);
		// One imported texture per map per surface, kept beside its bind so
		// no file is decoded twice for the 150 pieces that share a surface.
		TArray<UTexture2D*> Maps;
		Maps.SetNumZeroed((int32)Asked.size() * LedgerSurface::MapCount());
		for (size_t I = 0; I < Asked.size(); ++I)
		{
			LedgerSurface::Bound B;
			B.Surface = Asked[I].Surface;
			B.Pieces  = Asked[I].Pieces;
			if (GTexRoot.IsEmpty())
			{
				B.Status = "ABSENT";
				B.Reason = "no-texture-root-found-in-any-named-candidate";
				GBinds.push_back(B);
				continue;
			}
			// A MAP THAT WOULD NOT DECODE IS RECORDED WITHOUT DISQUALIFYING
			// THE SURFACE. A broken roughness map is not a reason to leave
			// the road untextured; only a missing or broken ALBEDO is, and
			// the difference is which of these two strings ends up where.
			std::string DecodeFail;
			for (int32 M = 0; M < LedgerSurface::MapCount(); ++M)
			{
				const std::vector<std::string> Cands = LedgerSurface::Candidates(B.Surface, M);
				for (size_t C = 0; C < Cands.size() && !B.MapFound[M]; ++C)
				{
					const FString Full = GTexRoot / FString(UTF8_TO_TCHAR(Cands[C].c_str()));
					if (IFileManager::Get().FileSize(*Full) <= 0) { continue; }
					int32 W = 0, H = 0;
					FString LoadedAs;
					// ONLY THE ALBEDO IS sRGB. The normal and roughness maps
					// are data, not colour.
					UTexture2D* Tex = ImportTexture(Full, M == 0, W, H, LoadedAs);
					B.MapFile[M] = Cands[C];
					B.MapLoadedAs[M] = TCHAR_TO_UTF8(*LoadedAs);
					B.MapW[M] = W; B.MapH[M] = H;
					if (Tex != nullptr)
					{
						B.MapFound[M] = true;
						Maps[(int32)I * LedgerSurface::MapCount() + M] = Tex;
						++GTexturesImported;
					}
					else
					{
						// A FILE THAT IS THERE AND WILL NOT DECODE IS A
						// DIFFERENT FACT from a file that is not there, and
						// the decoder's own words are the reason.
						if (!DecodeFail.empty()) { DecodeFail += "/"; }
						DecodeFail += std::string(LedgerSurface::MapName(M)) + "-"
						            + std::string(TCHAR_TO_UTF8(*LoadedAs));
					}
				}
			}
			if (!B.MapFound[0])
			{
				// THE ALBEDO IS WHAT DECIDES. Not there and there-but-broken
				// are two findings with two next actions, and the decoder's
				// own words are what separates them.
				B.Status = DecodeFail.empty() ? "ABSENT" : "UNDECODABLE";
				B.Reason = DecodeFail.empty() ? "no-candidate-file-under-texRoot" : DecodeFail;
			}
			else if (GBaseMaterial == nullptr)
			{
				B.Status = "NO-BASE-MATERIAL";
				B.Reason = "the-maps-decoded-but-there-is-nothing-to-instance";
			}
			else
			{
				B.Status = "RESOLVED";
				// A SURFACE CAN BE RESOLVED AND STILL HAVE LOST A MAP, and
				// the reason says which one rather than reading as clean.
				B.Reason = DecodeFail.empty() ? "none" : ("albedo-ok/lost-" + DecodeFail);
			}
			GBinds.push_back(B);
		}

		// ONE INSTANCE PER PIECE, because the tiling is the piece's own size
		// and two pieces of one surface are rarely one size.
		for (size_t P = 0; P < GSpec.Pieces.size(); ++P)
		{
			const Piece& Pc = GSpec.Pieces[P];
			int32 Idx = -1;
			for (size_t I = 0; I < GBinds.size(); ++I)
			{
				if (GBinds[I].Surface == Pc.Surface) { Idx = (int32)I; break; }
			}
			if (Idx < 0 || GBinds[(size_t)Idx].Status != "RESOLVED") { continue; }
			AStaticMeshActor** Found = GByName.Find(FString(UTF8_TO_TCHAR(Pc.Name.c_str())));
			if (Found == nullptr || *Found == nullptr) { continue; }
			UStaticMeshComponent* Comp = (*Found)->GetStaticMeshComponent();
			if (Comp == nullptr) { continue; }
			UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(GBaseMaterial, *Found);
			if (Mid == nullptr) { continue; }
			for (int32 M = 0; M < LedgerSurface::MapCount(); ++M)
			{
				UTexture2D* Tex = Maps[Idx * LedgerSurface::MapCount() + M];
				if (Tex == nullptr) { continue; }
				Mid->SetTextureParameterValue(
					FName(UTF8_TO_TCHAR(LedgerSurface::MapParam(M))), Tex);
			}
			const LedgerSurface::Tiling T = LedgerSurface::TilingFor(Pc, kMetresPerTile);
			Mid->SetScalarParameterValue(FName(TEXT("TilingU")), (float)T.U);
			Mid->SetScalarParameterValue(FName(TEXT("TilingV")), (float)T.V);
			Comp->SetMaterial(0, Mid);
			++GMidsCreated;
			++GBinds[(size_t)Idx].PiecesAssigned;
			GBinds[(size_t)Idx].TileU = T.U;
			GBinds[(size_t)Idx].TileV = T.V;

			// THE READBACK, ONCE PER SURFACE, ON THE FIRST INSTANCE MADE FOR
			// IT. The engine is asked for the parameter straight back, in the
			// same few statements that set it, so nothing in between can
			// explain a difference. 563 pieces would print 563 identical
			// answers to a question that is about the material.
			//
			// NOTHING HERE DECIDES ANYTHING. The comparison, the tolerance,
			// the counts and every printed string are in SurfaceBind.h where
			// g++ runs them before this file is compiled; this supplies the
			// live state and nothing else.
			//
			// WHAT IT CANNOT SEE: this is the game thread's copy. A value
			// that lands here and never reaches the render proxy still reads
			// back same-pointer, which is what the control quads answer.
			LedgerSurface::Readback& RB = GBinds[(size_t)Idx].Read;
			if (!RB.bAsked)
			{
				RB.bAsked = true;
				UTexture2D* Albedo = Maps[Idx * LedgerSurface::MapCount() + 0];
				const FName AlbedoParam(UTF8_TO_TCHAR(LedgerSurface::MapParam(0)));
				UTexture* Back = Mid->K2_GetTextureParameterValue(AlbedoParam);
				RB.bTexSame = (Back != nullptr && Back == (UTexture*)Albedo);
				if (Back == nullptr)
				{
					RB.TexGot = "null";
				}
				else
				{
					// THE ENGINE'S OWN PATH NAME. "Not the same pointer"
					// cannot say whether the answer was the parent's default
					// texture or something else, and those have different
					// next actions.
					const FString Path = Back->GetPathName();
					RB.TexGot = std::string(TCHAR_TO_UTF8(*Path));
				}
				// AFTER UpdateResource, WHICH RAN IN ImportTexture. A texture
				// with no render resource is bound to nothing however good
				// the pointer is.
				RB.bResourceValid = (Albedo != nullptr && Albedo->GetResource() != nullptr);
				RB.SetU = T.U;
				RB.SetV = T.V;
				RB.GotU = (double)Mid->K2_GetScalarParameterValue(FName(TEXT("TilingU")));
				RB.GotV = (double)Mid->K2_GetScalarParameterValue(FName(TEXT("TilingV")));
				RB.bScalarSame = LedgerSurface::ScalarMatches(RB.SetU, RB.GotU)
				              && LedgerSurface::ScalarMatches(RB.SetV, RB.GotV);
				UMaterialInterface* CompMat = Comp->GetMaterial(0);
				RB.bCompIsMid = (CompMat == (UMaterialInterface*)Mid);
				if (CompMat == nullptr)
				{
					RB.CompGot = "null";
				}
				else
				{
					const FString CompPath = CompMat->GetPathName();
					RB.CompGot = std::string(TCHAR_TO_UTF8(*CompPath));
				}
			}
		}

		GMaterialsLine = LedgerSurface::MaterialsDoneLine(
			GBinds, TCHAR_TO_UTF8(kBaseMaterialPath), GBaseMaterial != nullptr,
			TCHAR_TO_UTF8(*GTexRoot), GTexRootFiles, GTexRootTried,
			(int)GSpec.Pieces.size(),
			GTexturesImported, GMidsCreated, kMetresPerTile);
	}

	// ---- THE CONTROL QUADS -------------------------------------------------
	//
	// A 2x2 TEXTURE BUILT IN CODE. No file, no decoder, no texture root: if
	// this one renders its colours and the pack's textures do not, the fault
	// is downstream of the decode; if neither renders, the fault is not in
	// the pack at all. Every colour and the buffer order come out of
	// SurfaceBind.h, so the verdict names the same four colours the memcpy
	// wrote rather than a second copy of them typed here.
	UTexture2D* MakeControlTexture()
	{
		UTexture2D* Tex = UTexture2D::CreateTransient(2, 2, PF_B8G8R8A8);
		if (Tex == nullptr) { return nullptr; }
		Tex->SRGB = true;
		// NEAREST, BECAUSE A 2x2 BILINEAR TEXTURE IS A GRADIENT RATHER THAN
		// FOUR COLOURS. The reading survives either filter, since a blend of
		// four saturated corners is still nothing like a grey checker, but
		// four flat quadrants can be sampled with one patch.
		Tex->Filter = TF_Nearest;
		// KEPT ALIVE EXPLICITLY, for the reason the imported textures are: a
		// transient texture whose only reference is a material instance is
		// the shape of object this engine collects between two ticks.
		Tex->AddToRoot();
		uint8 Px[16];
		for (int32 I = 0; I < LedgerSurface::ControlColourCount(); ++I)
		{
			int R = 0, G = 0, B = 0;
			LedgerSurface::ControlColour(I, R, G, B);
			Px[I * 4 + 0] = (uint8)B;   // the platform data is BGRA
			Px[I * 4 + 1] = (uint8)G;
			Px[I * 4 + 2] = (uint8)R;
			Px[I * 4 + 3] = 255;
		}
		void* Dest = Tex->GetPlatformData()->Mips[0].BulkData.Lock(LOCK_READ_WRITE);
		FMemory::Memcpy(Dest, Px, sizeof(Px));
		Tex->GetPlatformData()->Mips[0].BulkData.Unlock();
		Tex->UpdateResource();
		return Tex;
	}

	// THE CONTROLS STAND IN FRONT OF THE CAMERA THE FIRST SHOT USES, read out
	// of the file rather than named here, so a spec whose first shot moves
	// takes its controls with it. Which camera answered is printed on every
	// quad line.
	const Camera* ControlCamera()
	{
		if (GSpec.Cameras.empty()) { return nullptr; }
		for (size_t I = 0; I < GSpec.Cameras.size() && !GSpec.Shots.empty(); ++I)
		{
			if (GSpec.Cameras[I].Id == GSpec.Shots[0].CameraId) { return &GSpec.Cameras[I]; }
		}
		return &GSpec.Cameras[0];
	}

	// THREE PLANES, ONE SIZE, ONE DISTANCE. The placement, the rotation, the
	// projection and every printed string are in SurfaceBind.h; this asks the
	// engine for actors and reads back what it got.
	void SpawnControlQuads(UWorld* World, UStaticMesh* Plane)
	{
		const Camera* C = ControlCamera();
		if (World == nullptr || Plane == nullptr || C == nullptr || GBaseMaterial == nullptr)
		{
			// NOTHING SPAWNED IS A FINDING AND IT NAMES WHICH OF THE FOUR
			// THINGS WAS MISSING: no plane mesh in the build and no base
			// material to instance are different next actions, and neither is
			// "the control quads did not help".
			GQuadDone = LedgerSurface::ControlQuadsDoneLine(GQuads, GBaseMaterial != nullptr);
			GQuadDone += std::string(" controlQuadsMissing=world.")
			           + (World == nullptr ? "NO" : "yes")
			           + "/plane." + (Plane == nullptr ? "NO" : "yes")
			           + "/camera." + (C == nullptr ? "NO" : "yes")
			           + "/base." + (GBaseMaterial == nullptr ? "NO" : "yes");
			return;
		}
		for (int32 I = 0; I < LedgerSurface::ControlQuadCount(); ++I)
		{
			const LedgerSurface::QuadPlace P = LedgerSurface::ControlQuadPlace(*C, I);
			LedgerSurface::QuadResult R;
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			AStaticMeshActor* A = World->SpawnActor<AStaticMeshActor>(
				AStaticMeshActor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
			if (A != nullptr)
			{
				R.bSpawned = true;
				// MOBILITY BEFORE THE TRANSFORM, for the reason SpawnPiece
				// sets it: a spawned StaticMeshActor is static mobility and
				// cannot be moved, and a static actor with no built lighting
				// renders unlit.
				MakeMovable(A);
				UStaticMeshComponent* Comp = A->GetStaticMeshComponent();
				if (Comp != nullptr)
				{
					Comp->SetMobility(EComponentMobility::Movable);
					Comp->SetStaticMesh(Plane);
					Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
					// A CONTROL CASTS NO SHADOW. It is not part of the street
					// and a shadow of it falling across the road would be a
					// change to the frame the street is measured in.
					Comp->SetCastShadow(false);
				}
				GQuadActors.Add(A);
				A->SetActorScale3D(FVector((float)P.SizeM, (float)P.SizeM, 1.0f));
				A->SetActorLocationAndRotation(
					FVector(P.XCm, P.YCm, P.ZCm),
					FRotator((float)P.EnginePitchDeg, (float)P.EngineYawDeg,
					         (float)P.EngineRollDeg));
				// READ BACK, NEVER ASSUMED. A transform that was asked for is
				// not a transform that took.
				const FVector Got = A->GetActorLocation();
				R.bRead = true;
				R.ReadXCm = (double)Got.X;
				R.ReadYCm = (double)Got.Y;
				R.ReadZCm = (double)Got.Z;
				UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(GBaseMaterial, A);
				if (Mid != nullptr)
				{
					R.bMidMade = true;
					if (P.bBindTexture)
					{
						if (GControlTex == nullptr) { GControlTex = MakeControlTexture(); }
						if (GControlTex != nullptr)
						{
							R.bTexMade = true;
							const FName Param(UTF8_TO_TCHAR(LedgerSurface::MapParam(0)));
							Mid->SetTextureParameterValue(Param, GControlTex);
							UTexture* Back = Mid->K2_GetTextureParameterValue(Param);
							R.bTexReadback = (Back != nullptr && Back == (UTexture*)GControlTex);
							R.bTexResource = (GControlTex->GetResource() != nullptr);
						}
					}
					// THE SCALARS GO ON EVERY CONTROL, INCLUDING THE COLOUR
					// ONE. tile1 and tile8 differ in nothing else, which is
					// what makes the pair readable.
					Mid->SetScalarParameterValue(FName(TEXT("TilingU")), (float)P.TileU);
					Mid->SetScalarParameterValue(FName(TEXT("TilingV")), (float)P.TileV);
					if (Comp != nullptr)
					{
						Comp->SetMaterial(0, Mid);
						R.bCompIsMid = (Comp->GetMaterial(0) == (UMaterialInterface*)Mid);
					}
				}
#if WITH_EDITOR
				A->SetActorLabel(FString(TEXT("control_quad_"))
				                 + FString(UTF8_TO_TCHAR(P.Id.c_str())));
#endif
			}
			GQuads.push_back(R);
			GQuadLines.push_back(
				LedgerSurface::ControlQuadLine(*C, P, R, kShotW, kShotH));
		}
		GQuadDone = LedgerSurface::ControlQuadsDoneLine(GQuads, GBaseMaterial != nullptr);
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
			BuildScene(World, /*bInteractive=*/false);
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
			// THE CONTROLS ARE HIDDEN FOR EVERY SHOT BUT THEIR OWN, and the
			// write happens ONCE PER SHOT rather than once per settle tick,
			// because this phase is re-entered while the condition settles
			// and a per-tick write is both a lie in the tally and a rebuild
			// asked for four times. A run with no quads spawned counts
			// nothing, so the verdict line reads nothing-measured rather
			// than claiming a hide that had nothing to hide.
			if (GQuadVisShot != GShotIndex && GQuadActors.Num() > 0)
			{
				GQuadVisShot = GShotIndex;
				const Camera* QuadCam = ControlCamera();
				const bool bShow = LedgerSurface::ControlQuadsVisibleFor(
					S.CameraId, QuadCam != nullptr ? QuadCam->Id : std::string());
				for (int32 QI = 0; QI < GQuadActors.Num(); ++QI)
				{
					if (GQuadActors[QI] != nullptr)
					{
						GQuadActors[QI]->SetActorHiddenInGame(!bShow);
					}
				}
				++GQuadShotsSeen;
				if (!bShow)
				{
					++GQuadHidden;
					if (!GQuadHiddenIds.empty()) { GQuadHiddenIds += ";"; }
					GQuadHiddenIds += S.Id;
				}
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
			GAskedPath = GProbing ? ProbePngPath() : ShotPngPath(S);
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
					AfterFrame(true);
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
					AfterFrame(true);
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
			AfterFrame(false);
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
		if (!LoadSpec())
		{
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

	// QUEUE 138 ITEM 1. See VignetteShot.h for the call-site contract; this
	// is what it does.
	void BuildInteractiveStreet(UWorld* World)
	{
		if (GInteractiveBuilt) { return; }
		if (World == nullptr) { return; }
		GInteractiveBuilt = true;

		if (!LoadSpec())
		{
			UE_LOG(LogTemp, Error, TEXT("LedgerProbe interactive street: %s"),
			       *FString(UTF8_TO_TCHAR(GSceneLine.c_str())));
			return;
		}

		BuildScene(World, /*bInteractive=*/true);

		// LIGHT IT. BuildScene spawns the sun and the three fill lights at
		// zero intensity (ApplyCondition is their one owner, named at the
		// top of this file) and the automation only ever turns them on by
		// applying one of the file's named conditions per shot; this path
		// has no shots, so it has to call the same owner directly or a
		// person would be walking a street lit only by the lanterns and
		// window practicals, which are the ones NOT zeroed at spawn.
		// overcast_day is conditions[0] in the shared file and the
		// condition the automation's own first shot uses, so this is not a
		// second opinion about which light is "the" street light.
		const Condition* Day = FindCondition("overcast_day");
		if (Day != nullptr) { ApplyCondition(*Day); }
		else if (!GSpec.Conditions.empty()) { ApplyCondition(GSpec.Conditions[0]); }
		else
		{
			UE_LOG(LogTemp, Error,
			       TEXT("LedgerProbe interactive street: the shared file named no condition at all"));
		}

		// PLACE THE PLAYER. cam_A is the shared file's own first camera and
		// the position the automation photographs from a human eye height
		// on the east footway; starting a person there rather than at an
		// invented coordinate is the same "no second opinion about the
		// street" rule PlaceCamera already follows for the automation
		// camera. Spawned rather than hand-placed: this project's rule
		// against a hand-edited scene applies to a PlayerStart exactly as
		// it does to a wall, and /Engine/Maps/Entry is an engine map this
		// project does not own to edit.
		const Camera* StartCam = FindCamera("cam_A");
		if (StartCam == nullptr && !GSpec.Cameras.empty()) { StartCam = &GSpec.Cameras[0]; }
		if (StartCam == nullptr)
		{
			UE_LOG(LogTemp, Error,
			       TEXT("LedgerProbe interactive street: the shared file named no camera to start the player at"));
			return;
		}
		// A GENEROUS NAMED CLEARANCE ABOVE THE GROUND, NOT A MEASURED
		// CAPSULE HALF-HEIGHT. ALedgerCharacter sets its own capsule to
		// 34x88 (LedgerCharacter.cpp), but matching that number here
		// exactly would be a second copy of it that could drift from the
		// first; a spawn that starts clear of the pavement and falls the
		// rest of the way under gravity does not need to match it, and a
		// spawn that starts too LOW would not correct itself the same way.
		const float kClearAboveGroundM = 1.1f;
		const FVector At(StartCam->X * 100.0, StartCam->Z * 100.0,
		                 (StartCam->GroundY + kClearAboveGroundM) * 100.0);
		// FACING DOWN THE STREET, AT THE SAME YAW cam_A USES. The file's
		// yaw is already this engine's yaw with no conversion, exactly as
		// PlaceCamera uses it above; no pitch or roll on a PlayerStart, the
		// character stands upright.
		const FRotator Facing(0.0f, (float)StartCam->YawDeg, 0.0f);
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		APlayerStart* PStart = World->SpawnActor<APlayerStart>(
			APlayerStart::StaticClass(), At, Facing, Params);
		// READ BACK, NEVER ASSUMED: a spawn that returned null is a
		// GameMode with nowhere to start a player, and this is the one
		// line that would say so.
		UE_LOG(LogTemp, Log,
		       TEXT("LedgerProbe interactive street: playerStart=%s at %s facing yaw %.1f, street pieces=%d"),
		       PStart != nullptr ? TEXT("spawned") : TEXT("SPAWN-FAILED"),
		       *At.ToString(), Facing.Yaw, (int32)GSpec.Pieces.size());
	}

	// THE WALK PROBE'S THREE READS. Declared in VignetteShot.h; each one
	// returns a global this same translation unit already maintains, so a
	// walk run and a vignette run can never report two different counts
	// for one fact. None of the three builds anything: a run that never
	// called BuildScene reads GSceneLine's untouched default
	// ("piecesEmitted=0/0"), GQuads empty, and GByName empty, which is
	// exactly the "nothing measured" state a caller that starts too early
	// ought to see.
	FString StreetSceneLine()
	{
		return FString(UTF8_TO_TCHAR(SceneLineWithSky().c_str()));
	}

	int32 ControlQuadsSpawnedCount()
	{
		return (int32)GQuads.size();
	}

	AActor* FindStreetPiece(const FString& Name)
	{
		AStaticMeshActor* const* Found = GByName.Find(Name);
		return (Found != nullptr) ? static_cast<AActor*>(*Found) : nullptr;
	}

	// THE CRIME PROBE'S ONE HELPER, NOT FIVE. Ruling of 2026-09-08 section 2:
	// a thin export over the SpawnPiece this file already uses for all 593
	// street pieces, so a shard, a brick, a stand-in body and the yard floor
	// are placed by the same code path, with the same frame mapping, the same
	// movable mobility and the same interactive collision as a kerbstone.
	//
	// CentreM AND SizeM ARE IN THE SHARED FILE'S OWN FRAME (x along, y up, z
	// across), exactly as a Piece states them, and NOT in the engine's. The
	// one place that converts between the two is SpawnPiece, three hundred
	// lines above; a second converter at a call site is how two frames drift
	// apart, and this probe's whole geometry would then be wrong in a way no
	// count could see.
	//
	// bInteractive=true, ALWAYS: every caller of this is a person-scale
	// object in a street somebody is walking and tracing through. The
	// automation's collision-off saving applies to a frame it is timing, and
	// nothing here is in one.
	//
	// THE SURFACE IS RECORDED AND NOT BOUND. BindSurfaces runs once inside
	// BuildScene, over GSpec.Pieces, long before any of these exist, so a
	// piece spawned here carries the mesh's default material. The crime
	// verdict prints that as probePiecesMaterialBound=0/N with the reason
	// rather than leaving a reader to wonder why a shard is grey.
	AActor* SpawnProbePiece(UWorld* World, const FString& Name,
	                        const FVector& CentreM, const FVector& SizeM,
	                        const FString& Shape, const FString& Surface)
	{
		if (World == nullptr) { return nullptr; }
		UStaticMesh* Cube = LoadShape(TEXT("/Engine/BasicShapes/Cube.Cube"));
		UStaticMesh* Cyl  = LoadShape(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
		const bool bCyl = (Shape == TEXT("cyl"));
		UStaticMesh* Mesh = bCyl ? Cyl : Cube;
		if (Mesh == nullptr) { return nullptr; }

		// QUALIFIED, not leaned on the using-directive inside the unnamed
		// namespace three hundred lines above: this function is outside that
		// block and the leak of a using-directive out of an unnamed namespace
		// is a rule most readers would have to look up.
		LedgerVignette::Piece P;
		P.Name    = std::string(TCHAR_TO_UTF8(*Name));
		P.Shape   = bCyl ? "cyl" : "box";
		P.Surface = std::string(TCHAR_TO_UTF8(*Surface));
		P.X = CentreM.X; P.Y = CentreM.Y; P.Z = CentreM.Z;
		P.SX = SizeM.X;  P.SY = SizeM.Y;  P.SZ = SizeM.Z;
		// The same scale mapping BuildScene uses for a box and a cylinder
		// alike: the engine's basic shapes are one metre, so the scale IS the
		// size, and the cylinder's axis is local +Z which is the file's +y.
		const FVector Scale((float)P.SX, (float)P.SZ, (float)P.SY);
		AStaticMeshActor* A = SpawnPiece(World, Mesh, P, Scale, /*bInteractive=*/true);
		if (A == nullptr) { return nullptr; }
		GProbeByName.Add(Name, A);
		return static_cast<AActor*>(A);
	}

	// THE NAME A TRACE HIT, WHICH IS THE HALF OF AN OCCLUSION READING THAT
	// SAYS ANYTHING. SpawnPiece only calls SetActorLabel under WITH_EDITOR,
	// so in a packaged build every one of these actors answers GetName() with
	// StaticMeshActor_NNN and a verdict saying actorBlocker=StaticMeshActor_213
	// names nothing a reader can look up. FindStreetPiece is name-to-actor
	// only, so this is its reverse and it is the reason this export exists.
	//
	// READ-ONLY, AND BOTH MAPS. It adds to neither, so the ruling's own
	// check (one grep for the street map's single Add call) still finds
	// exactly one site, in BuildScene. The probe map is searched
	// second so a street piece can never be shadowed by a probe piece of the
	// same name, and a blocker that IS a probe piece (the yard floor, a
	// stand-in body) names itself rather than falling through to the engine's
	// number.
	FString StreetPieceNameOf(const AActor* Actor)
	{
		if (Actor == nullptr) { return FString(); }
		for (TMap<FString, AStaticMeshActor*>::TConstIterator It(GByName); It; ++It)
		{
			if (It.Value() == Actor) { return It.Key(); }
		}
		for (TMap<FString, AStaticMeshActor*>::TConstIterator It(GProbeByName); It; ++It)
		{
			if (It.Value() == Actor) { return It.Key(); }
		}
		return FString();
	}
}
