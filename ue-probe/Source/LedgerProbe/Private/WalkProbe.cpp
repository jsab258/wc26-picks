// RULING 1 FROM JAFAR, 2026-09-07: "I do not launch builds to see if they
// compile. The runner is on my PC; use it." This drives -LedgerWalk: the
// same pawn a person would control, in the same interactive street a
// person would walk, scripted through a short route and photographed along
// it, so the answer to "does it work" comes from the runner rather than
// from a colour on a CI page.
//
// WHY ALedgerGameMode NEEDS NO CHANGE AND NEITHER DO THE THREE EXISTING
// SWITCHES. ALedgerGameMode::InitGame checks the command line for
// -LedgerVignette, -LedgerShot and -LedgerGoldenTest and does nothing
// street-related when it finds one; it has never heard of -LedgerWalk, so a
// walk run falls through to the SAME branch a genuine human launch takes:
// DefaultPawnClass stays ALedgerCharacter (the constructor's own default,
// untouched) and LedgerVignetteShot::BuildInteractiveStreet(GetWorld())
// runs exactly as it does for a person, collision on, PlayerStart at
// cam_A. A plain launch with no switch at all is bit-for-bit unaffected:
// Start() below returns immediately when -LedgerWalk is absent, which is
// every case that mattered before this file existed. Checked by reading
// LedgerGameMode.cpp before writing this file, not assumed from its name.
//
// WHERE EACH OF THE FIVE JUDGMENTS' NUMBERS COMES FROM:
//   1. DOES IT LAUNCH is NOT decided in this file. A process that hangs
//      never runs the code that would say so, and a process that crashes
//      may not get to write anything at all; only the thing watching the
//      process from outside can tell a hang from a crash from a clean
//      exit. This file's only contribution is WriteBreadcrumb below,
//      called at each milestone BEFORE the risky work that milestone
//      guards, so a crash's LAST reached milestone survives it on disk.
//      The workflow step reads this file's presence, its last
//      walkPhaseReached, and whether walkReached=end is the last line, and
//      combines those with the process's own exit code and a wall-clock
//      kill to write launchStatus.
//   2. IS THERE A STREET reads LedgerVignetteShot::StreetSceneLine(), the
//      SAME piecesEmitted=N/M counters BuildScene already emits for the
//      vignette path. Not recomputed: a street built once is counted once.
//   3. IS THERE A WALKING CAMERA reads the pawn's own GetActorLocation()
//      before and after a scripted AddMovementInput phase, the same public
//      API a human Character responds to. This file asserts nothing about
//      a frame; only about where the pawn was.
//   4. ARE THE TEST CARDS ABSENT reads
//      LedgerVignetteShot::ControlQuadsSpawnedCount(), which the vignette
//      module only ever increments when BuildScene is called with
//      bInteractive=false. BuildInteractiveStreet always passes true, so
//      this reads 0 on this path by construction, and it is READ rather
//      than asserted from that sentence, because a sentence about the
//      source is not a measurement of the running program.
//   5. IS COLLISION REAL is a PLANTED pair, per rule 5b (a guard is tested
//      on the case it should pass and on a case the fault it watches for
//      can actually happen in): an accepting case (the open footway ahead
//      of the spawn point, walked with no help from anything but ordinary
//      movement input) and a rejecting case (the pawn is teleported to a
//      measured clearance in front of a NAMED real street piece,
//      east_parade_bay0, a full-height terrace carcass looked up by name
//      from the same GByName map BuildScene fills, and walked straight at
//      it). Both distances are printed; STOPPED/MOVED below is a coarse,
//      NAMED first-cut, not a bound tuned from a series this instrument
//      has never produced before, and the file says so at the line.
//
// THE SIXTH AND SEVENTH MILESTONES, ADDED 2026-09-09: THE GRATE, AIMED AT.
// Run 34 measured prop_drainage_grate_01_0 as a placed mesh with collision at
// the running surface (propsAsMesh=22/23, propPlacedWithCollision=22/22,
// propFullyBuried=0/23, propBurialSubject=.../via=loaded-asset/collision=YES/
// topM=-0.0650) and NOT ONE OF THE FIVE MILESTONES BELOW POINTS AT IT: the
// piece is 0.3999 m square at x=12.0, z=2.8 on the east channel and the walk
// route runs past it. A verdict saying a piece is there with no frame showing
// it is rule 4 pointed the other way round. See the block above AimAtGrate
// for why there are two frames of it and not one.
//
// THE CLIP. Unreal's own Movie Render Pipeline needs a Level Sequence asset
// and this project ships no content directory by design (see
// VignetteShot.cpp); wiring it in for one probe would be a new asset type
// and a new plugin dependency, neither verifiable until the next Windows
// build, so this file does not use it. This file writes FRAMES ONLY, in two
// kinds: seven named milestones (ue-walk_NN_*.png, the evidence) and a
// SEQUENCE along the route (ue-walkseq_NNN.png, enough of them that played
// back they read as motion rather than a slideshow). Turning the sequence
// into ONE GIF is tools/clip-from-frames.py's job, done with Pillow, which
// `ledger-v2/research/license-allowlist.md` does not govern: that file
// scopes itself to "verify weights license, not code license" and every
// entry in it is a generative model or a shipped game asset, not a Python
// utility encoding this project's own render output as a diagnostic. See
// that tool's own header for the full reasoning; this file only produces
// its input and never writes a GIF itself.
#include "WalkProbe.h"

#include "VignetteShot.h"
#include "VignetteSpec.h"
#include "SurfaceBind.h"
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
// THE SAME INCLUDE CrimeProbe.cpp USES FOR FCollisionQueryParams, copied from
// the translation unit next door that already compiles on the runner rather
// than guessed at, because this file's own compile is 17 to 33 minutes away.
#include "CollisionQueryParams.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"

#include <string>
#include <vector>

namespace
{
	// ---- timing, all ceilings on a hang and never targets --------------
	const double kWorldCeiling         = 45.0;
	const double kPawnCeiling          = 30.0;
	const double kSettleAfterSpawn     = 0.5;
	// THE CLEAR WALK IS SPLIT IN TWO so a frame can be taken at its
	// midpoint; each half runs this long, so the whole accepting-case walk
	// is 2x this, matched against the Unity/UE frame-timing convention of
	// naming the number rather than letting a reader infer it.
	const double kClearHalfSeconds     = 1.5;
	const double kTeleportSettleSeconds = 0.5;
	const double kBlockedSeconds       = 3.0;
	const double kShotFileCeiling      = 15.0;

	// HOW FAR IN FRONT OF THE NAMED WALL THE REJECTING CASE STARTS. The
	// footway sits on the -Y (smaller-z-in-the-file) side of this piece,
	// verified from production/specs/vignette-pieces.json: the footway
	// centres at z=4.13m and east_parade_bay0 centres at z=9.125m, so this
	// plant always approaches from the box's Min.Y face.
	const double kApproachClearanceCm  = 150.0;

	// A COARSE FIRST-CUT, NOT A BOUND READ OFF A SERIES. Rule 2 asks for a
	// printed series before a threshold; this is the first run this
	// instrument has ever produced, so there is no series yet to read one
	// off. MOVED/STUCK and STOPPED/PASSED-THROUGH below are named splits
	// wide enough that no plausible walk speed or capsule radius change
	// would flip them by accident, and the raw distances are printed
	// beside every one of them so a reader never has to trust the word.
	const double kStuckFloorCm         = 50.0;

	const TCHAR* kWallName = TEXT("east_parade_bay0");
	// SEVEN SINCE 2026-09-09, WAS FIVE. The five route milestones plus the
	// two grate frames below; walkFramesRequested=N/7 reads against this.
	const int32  kTotalShots = 7;

	// ---- THE GRATE SHOT: WHERE IT STANDS AND WHY ------------------------
	//
	// TWO FRAMES OF ONE STATIC CAMERA, AND THAT IS THE WHOLE REASON FOR THE
	// SEVENTH. The grate's top face is exactly coincident with the channel
	// and carriageway top faces over about 0.16 square metres, and whether
	// that TIES in the depth test is answered by tools/grate-zfight.py, which
	// reads a speckle density AND a FRAME-TO-FRAME FLICKER density against a
	// same-area control rectangle on plain carriageway in the same frame.
	// Flicker needs two frames of the SAME view: one still cannot produce it,
	// and every ue-walkseq frame is from a different place. So this takes two
	// from one camera that does not move between them, and whatever temporal
	// jitter the renderer applies between two ticks is what a tie shimmers
	// through.
	//
	// EVERY OFFSET BELOW IS FROM THE ENGINE'S OWN PLACED BOUNDS OF THE GRATE
	// (GetComponentsBoundingBox, after scale and rotation), never from the
	// spec file a second time.
	const TCHAR* kGrateName = TEXT("prop_drainage_grate_01_0");

	// ---- THE CANDIDATE STANDPOINTS, TRACED BEFORE ANY OF THEM SHOOTS -----
	//
	// WHY THERE IS A LIST AND NOT ONE STANDPOINT. Run 35 aimed from row 00
	// below and printed grateShotStatus=AIMED, grateRectStatus=MEASURED and
	// walkFramesWrote=7/7 over a frame in which the east kerb's pedestrian
	// guard railing (E8, posts at x=10/12/14/16 m in the plane z=3.375 m, one
	// of them at the grate's own x) stands between the camera and the piece,
	// and nothing asked what was in the line. The camera arithmetic was right
	// to two decimals; that was never the question.
	// So every row is TRACED first (TraceGrateFrom below), the first one
	// whose subject rays are all clear is taken, and if none is clear the
	// shot is REFUSED with the blocker named rather than writing a picture of
	// the obstruction.
	//
	// EVERY ROW IS AN OFFSET FROM THE PIECE'S OWN PLACED BOUNDS, never a
	// world coordinate: Across is across the street (+Y is the footway side,
	// the sign vignette-scene.json's east footway camera at z=4.0 m against
	// this piece at z=2.8 m establishes, the same fact the blocked-walk plant
	// above relies on), Along is up the channel, Eye is above the piece's own
	// placed top face.
	//
	// THE ORDER IS DELIBERATE AND IT IS NOT A BOUND. Row 00 is run 35's exact
	// geometry, so a clear line from it reproduces that framing unchanged;
	// the rows after it deviate further and further, and the nearly-overhead
	// one is last because the control rectangle MeasureGrateAim projects sits
	// 80 cm toward the crown and a very steep or road-side standpoint can put
	// it off frame, which that function already prints as
	// grateRectStatus=OFF-FRAME. No threshold is read off a series here: the
	// choice is "the first with a clear line", and every row's clear count
	// and blockers are printed whether it was tried or not.
	struct FGrateStand { double AcrossCm; double AlongCm; double EyeCm; };
	const FGrateStand kGrateStands[] = {
		{  130.0,    0.0, 125.0 },  // 00 run 35's own: 1.80 m standoff, down 43.9 deg
		{   85.0,    0.0, 120.0 },  // 01 closer from the footway, steeper
		{   45.0,    0.0, 125.0 },  // 02 closer still
		{   60.0,  110.0, 125.0 },  // 03 oblique, up the channel
		{   60.0, -110.0, 125.0 },  // 04 oblique, down the channel
		{ -120.0,    0.0, 120.0 },  // 05 from the carriageway side
		{  -70.0,    0.0, 115.0 },  // 06 from the carriageway, closer
		{   15.0,    0.0, 130.0 },  // 07 nearly overhead, the last resort
	};
	const int32 kGrateStandCount =
		(int32)(sizeof(kGrateStands) / sizeof(kGrateStands[0]));
	// TEN RAYS PER STANDPOINT, and the count is named so the traced total has
	// a denominator: five on the subject rectangle (the decision), four on
	// the placed top face's corners and one to the placed bounds centre
	// (context). TraceGrateFrom below is the only place that fills them.
	const int32 kGrateRaysPerStand = 10;
	// ONE CENTIMETRE, AND WHAT IT IS A CLEARANCE FROM. This piece's top face
	// lies IN the pitched road plane, measured at 0.000 mm offset at three
	// points (game-design/decision-2026-09-09-the-grate-rises-flush.md), so a
	// ray ending exactly on the face ends inside a plane it shares with an
	// opaque neighbour and can register that neighbour at its own endpoint.
	// Any positive lift escapes that plane into open air; 10 mm is the
	// clearance this project already declares for coplanar opaque pairs
	// (vignette-scene.json standoff_m 0.01, "a clearance rather than a
	// dimension"). It is not a bound and nothing is compared against it.
	// CORRECTED 2026-09-09: the sentence this replaces said one centimetre
	// stays inside the recess the carriageway's lip makes over this piece.
	// THERE IS NO LIP AND NO RECESS. That reading came from run 35's
	// deepestMm=65.01, which is the road CROWN 2.745 m away in z and not
	// cover over this piece, an identification the flush ruling had already
	// corrected hours earlier.
	const double kGrateRayLiftCm    = 1.0;
	// FRAMING, DERIVED AND NOT GUESSED. At 40 degrees vertical on 960x540 the
	// horizontal field is 65.9 degrees, so the frame is 2.33 m wide where the
	// grate is: a 0.3999 m piece is 17 percent of the frame width, about 165
	// px across, and about 114 px down after the 43.9 degree foreshortening.
	const double kGrateVFovDeg      = 40.0;
	const int32  kGrateShotW        = 960;
	const int32  kGrateShotH        = 540;
	// THE SUBJECT RECTANGLE, INSET AND BIASED TOWARD THE KERB. Inset because
	// the projected outline of a square is a quadrilateral and its axis
	// aligned pixel box would include road outside the piece. Biased +7 cm
	// toward the kerb because the double yellow's bands end at z=2.75 m and
	// the piece spans 2.60 to 3.00 m: a rect centred on the piece would carry
	// a paint EDGE into the subject and a paint edge reads as speckle. 22 cm
	// square centred at z=2.87 m spans 2.76 to 2.98 m, inside the piece and
	// clear of the paint.
	const double kGrateSubjOffsetCm = 7.0;
	const double kGrateSubjHalfCm   = 11.0;
	// NINE BY NINE OVER THAT SAME RECTANGLE, AND NINE IS NOT A ROUND NUMBER.
	// The five voting rays are a SAMPLE of the subject rectangle with 110 mm
	// between samples, and the occluder class that actually exists here is the
	// east kerb's guard railing: infill bars 25 mm at 0.333 m spacing, posts
	// 50 mm at 2.0 m spacing. From row 00 the railing plane sits at t=0.589 of
	// the way to the target, so a 25 mm bar casts about a 42 mm shadow on the
	// subject plane and a 50 mm post about 85 mm: both NARROWER THAN THE
	// SAMPLE SPACING, so the vote can miss a bar lying across the picture.
	// Nine samples across 22 cm are 27.5 mm apart, which resolves the 42 mm
	// shadow. IT IS COUNTED AND IT DOES NOT VOTE: the selection is still the
	// five subject rays and still the first clear row, and this is the printed
	// series a future selection predicate would be set from (rule 2: ship the
	// printer, read real runs, then set the bound, in that order).
	const int32  kGrateSubjGridN    = 9;
	// THE CONTROL, ON PLAIN CARRIAGEWAY IN THE SAME FRAME. 80 cm toward the
	// crown from the piece's centre is z=2.00 m: past the channel course
	// (2.745 to 3.0 m) and 45 cm clear of the double yellow's inner band
	// (2.45 m), so it is asphalt with nothing coincident under it. Its pixel
	// rectangle is the SUBJECT'S OWN width and height, so the two are the
	// same area by construction rather than by a second calculation.
	const double kGrateCtrlAcrossCm = 80.0;
	const double kGrateSettleSeconds = 0.5;

	// ---- THE SEQUENCE: THE CLIP, AS OPPOSED TO THE FIVE MILESTONES -------
	//
	// THE FIVE ue-walk_NN_*.png ABOVE ARE THE EVIDENCE AND STAY EXACTLY AS
	// THEY ARE. A slideshow of five stills is not a clip; this is the part
	// that makes the route read as motion, and tools/clip-from-frames.py
	// (Pillow, no new dependency; see that file's own header for the
	// license-allowlist reasoning) stitches ONLY the ue-walkseq_*.png names
	// below into one GIF. Kept in its own name prefix so the workflow step
	// can hand the stitcher a glob without touching the milestones.
	//
	// 0.4 SECONDS BETWEEN ATTEMPTS, CHOSEN FROM WHAT THE ROUTE ACTUALLY
	// TAKES, NOT TUNED BLIND. The two walking segments together run
	// kClearHalfSeconds*2 + kBlockedSeconds = 6.0s; at 0.4s that is up to 15
	// samples across the whole route, enough that consecutive frames show a
	// small step rather than a jump, without asking the offscreen capture
	// path (a screenshot request plus a settle poll, the same mechanism the
	// five milestones already use) to run more often than it can keep up
	// with. Playback speed is a SEPARATE choice the stitcher makes; see
	// tools/clip-from-frames.py for why the GIF plays faster than this.
	const double kSeqInterval    = 0.4;
	// A SHORT CEILING, NOT THE MILESTONES' 15s. A sequence frame that stalls
	// only costs this route one sample; the milestones already prove the
	// capture path works at all, so a slow sequence attempt is skipped
	// rather than allowed to eat into the walking time it is meant to be
	// photographing.
	const double kSeqFileCeiling = 5.0;
	// THE CAP, AND WHAT IT IS A CAP ON. 6.0s of walking at a 0.4s interval
	// asks for 15 samples; 16 leaves one to spare and is a safety cap on a
	// clock, not a target this run is expected to hit exactly. It announces
	// itself on the done line as walkSeqFramesRequested=N/16.
	const int32  kMaxSeqFrames   = 16;

	enum class EWalkPhase : uint8
	{
		WaitWorld, WaitPawn, SettleAfterSpawn,
		ShotStart, ClearWalkA, ShotMidClear, ClearWalkB, ShotAfterClear,
		TeleportToWall, SettleAfterTeleport, ShotBeforeBlocked,
		BlockedWalk, ShotAfterBlocked,
		AimGrate, SettleAfterAim, ShotGrateA, ShotGrateB, RestoreView, ConfirmRestore,
		Done
	};

	FTSTicker::FDelegateHandle GTicker;
	EWalkPhase GPhase      = EWalkPhase::WaitWorld;
	double     GPhaseStart = 0.0;
	double     GRouteStart = 0.0;
	int32      GTicks      = 0;

	APawn* GPawn = nullptr;
	FVector GClearDir   = FVector::ForwardVector;
	FVector GBlockedDir = FVector::RightVector;

	FVector GClearStartLoc   = FVector::ZeroVector;
	FVector GClearEndLoc     = FVector::ZeroVector;
	FVector GBlockedStartLoc = FVector::ZeroVector;
	FVector GBlockedEndLoc   = FVector::ZeroVector;

	bool bPawnFound = false, bClearWalked = false, bTeleported = false, bBlockedWalked = false;
	FString GFinishReason = TEXT("process-completed-normally");
	bool GWallFound = false;

	// ---- the grate aim: one camera, reused by both grate frames --------
	AActor*       GGrateActor = nullptr;
	ACameraActor* GGrateCam   = nullptr;
	AActor*       GViewBefore = nullptr;
	FString GGrateLine =
		TEXT("grateShotStatus=NOT-REACHED grateShotReason=the-route-never-got-past-the-blocked-walk");
	FString GGrateRectLine    = TEXT("grateRectStatus=NOT-REACHED");
	FString GGrateRestoreLine = TEXT("grateViewRestoreStatus=NOT-REACHED");
	// ONE FLAG DECIDES WHETHER FRAMES 05 AND 06 HAPPEN AT ALL, set true only
	// by the one path in AimAtGrate that found a clear line and took the
	// view; every other path leaves it false and names its reason here, and
	// the reason is printed against BOTH frames that were not taken.
	bool    bGrateShootable = false;
	FString GGrateSkipWhy   = TEXT("the-route-never-reached-the-grate-phases/nothing-measured");
	// ONE LINE PER STANDPOINT TRIED, in the order tried, each carrying its own
	// clear counts and the named blocker of every ray that was stopped. Empty
	// means no standpoint was traced, which prints the words nothing measured
	// rather than an empty series.
	TArray<FString> GGrateCandLines;
	// A CUMULATIVE COUNT OF RAYS ACTUALLY CAST, over the standpoints actually
	// tried. Its denominator is kGrateStandCount*kGrateRaysPerStand, and it
	// reads short of that on purpose whenever the search stopped early at a
	// clear standpoint.
	int32 GGrateRaysTraced = 0;
	// A SECOND CUMULATIVE COUNT, FOR THE COVERAGE GRID ONLY, AND IT IS KEPT
	// APART ON PURPOSE. The grid casts kGrateSubjGridN squared rays per
	// standpoint tried and the vote casts kGrateRaysPerStand; one total over
	// both would let either number borrow the other's denominator, so this one
	// is counted, printed and named separately (grateSubjGridRaysTraced) and
	// its denominator is kGrateStandCount*kGrateSubjGridN*kGrateSubjGridN.
	int32 GGrateGridRaysTraced = 0;

	// ---- the shot-in-flight, one at a time, reused across all five -----
	bool    GShotInFlight        = false;
	FString GShotPath;
	FString GShotName;
	bool    GShotUsedHighRes     = false;
	bool    GShotTriedHighResOne = false;
	int64   GShotSizeTracker     = -1;
	double  GShotWaitStart       = 0.0;
	std::vector<std::string> GShotLines;
	int32   GShotsAttempted = 0, GShotsWrote = 0;

	// ---- the sequence-in-flight. Mutually exclusive in time with the
	// milestone capture above (movement phases and Shot* phases never
	// overlap in this one ticker), so it reuses ShotBegin/ShotPump/GShotPath
	// and the rest of that scratch state rather than duplicating it; only
	// the book-keeping below (when the last one fired, how many so far) is
	// its own.
	bool   GSeqInFlight       = false;
	double GLastSeqCaptureTime = 0.0;   // 0.0 means "not yet armed"
	int32  GSeqRequested = 0, GSeqWrote = 0;

	UWorld* GameWorld()
	{
		if (!GEngine) { return nullptr; }
		for (const FWorldContext& Ctx : GEngine->GetWorldContexts())
		{
			if (Ctx.WorldType == EWorldType::Game && Ctx.World() != nullptr) { return Ctx.World(); }
		}
		return nullptr;
	}

	FString AbsProject(const TCHAR* Leaf)
	{
		return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), Leaf));
	}

	FString WalkSha()
	{
		FString Sha;
		if (!FParse::Value(FCommandLine::Get(), TEXT("LedgerCommit="), Sha) || Sha.IsEmpty())
		{
			Sha = TEXT("SHA-UNKNOWN");
		}
		return Sha.Replace(TEXT(" "), TEXT("~"));
	}

	// A FILE THAT EXISTS IS NOT A FILE THAT IS FINISHED. Two consecutive
	// polls agreeing on a non-zero size is the cheap version of waiting
	// for the writer and it costs one frame, the same pattern every other
	// capture in this codebase uses.
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

	// DECODE THE FILE THAT IS ABOUT TO BE COMMITTED, not a buffer the
	// engine held in memory: rule 4, read the artifact you are shipping.
	// A third copy of this exact decode exists in LedgerProbe.cpp and
	// VignetteShot.cpp; not refactored here because this is a new, small
	// feature and touching either of those files' own capture paths is
	// out of this change's scope.
	bool DecodeBgra(const FString& PngPath, TArray64<uint8>& OutBgra, int32& OutW, int32& OutH,
	                FString& OutNote)
	{
		TArray<uint8> Compressed;
		if (!FFileHelper::LoadFileToArray(Compressed, *PngPath) || Compressed.Num() == 0)
		{
			OutNote = TEXT("file-would-not-load-or-was-empty");
			return false;
		}
		IImageWrapperModule* Mod =
			FModuleManager::Get().LoadModulePtr<IImageWrapperModule>(FName("ImageWrapper"));
		if (Mod == nullptr) { OutNote = TEXT("imagewrapper-module-missing"); return false; }
		TSharedPtr<IImageWrapper> Wrapper = Mod->CreateImageWrapper(EImageFormat::PNG);
		if (!Wrapper.IsValid()) { OutNote = TEXT("no-png-wrapper"); return false; }
		if (!Wrapper->SetCompressed(Compressed.GetData(), (int64)Compressed.Num()))
		{
			OutNote = TEXT("setcompressed-refused-the-bytes");
			return false;
		}
		OutW = Wrapper->GetWidth();
		OutH = Wrapper->GetHeight();
		if (OutW <= 0 || OutH <= 0) { OutNote = TEXT("decoded-size-was-zero"); return false; }
		if (!Wrapper->GetRaw(ERGBFormat::BGRA, 8, OutBgra)) { OutNote = TEXT("getraw-refused"); return false; }
		return OutBgra.Num() >= (int64)OutW * (int64)OutH * 4;
	}

	// MEASURE, THEN JUDGE, WITH THE MATHS COMING FROM FrameStats.h, WHICH
	// g++ RUNS BEFORE THIS FILE COMPILES. This layer supplies pixels and
	// live state and nothing else, per the standing rule for a project
	// whose top layer does not compile locally.
	std::string MeasureShotFile(const FString& Path, const FVector& Loc, bool& OutWrote)
	{
		OutWrote = false;
		const int64 Bytes = IFileManager::Get().FileSize(*Path);
		// CONVERTED TO std::string BEFORE THE VARARG CALL, not handed to
		// std::snprintf's %s straight out of the TCHAR_TO_UTF8 macro: this
		// codebase's own idiom (used throughout VignetteShot.cpp) is to bind
		// that macro's result to a named std::string first and read its
		// buffer back with .c_str(), and matching it here removes any
		// question about a temporary's lifetime crossing a C varargs call.
		const std::string ShotNameUtf8(TCHAR_TO_UTF8(*GShotName));
		char Head[192];
		std::snprintf(Head, sizeof(Head), "walkShot=%s walkShotAtXYZcm=%.1f/%.1f/%.1f ",
			ShotNameUtf8.c_str(), Loc.X, Loc.Y, Loc.Z);
		TArray64<uint8> Bgra;
		int32 W = 0, H = 0;
		FString Note;
		if (!DecodeBgra(Path, Bgra, W, H, Note))
		{
			return std::string(Head) + "shotStatus=" + (Bytes > 0 ? "UNDECODABLE" : "NO-FILE")
			     + " shotBytes=" + std::to_string(Bytes)
			     + " shotNote=" + std::string(TCHAR_TO_UTF8(*Note));
		}
		const LedgerFrame::FrameStats St =
			LedgerFrame::Measure((const unsigned char*)Bgra.GetData(), W, H);
		OutWrote = !St.Blank;
		return std::string(Head) + LedgerFrame::PixelLine(St) + " shotBytes=" + std::to_string(Bytes);
	}

	void ShotBegin(const FString& Path, double Now)
	{
		GShotPath = Path;
		GShotUsedHighRes = false;
		GShotTriedHighResOne = false;
		GShotSizeTracker = -1;
		GShotWaitStart = Now;
		IFileManager::Get().Delete(*Path, false, true, true);
		// AN ABSOLUTE PATH ON PURPOSE, as every other capture in this
		// codebase uses one: a relative one resolves against the engine's
		// screenshot directory, which is not where this step is looking.
		FScreenshotRequest::RequestScreenshot(GShotPath, false, false);
	}

	// TWO CANDIDATES, THE SAME PAIR VignetteShot.cpp and LedgerProbe.cpp
	// already proved out: RequestScreenshot first, HighResShot once if the
	// first writes nothing inside Ceiling. Returns true when this shot is
	// FINISHED, whichever way; false while still waiting. CEILING IS A
	// PARAMETER, NOT THE CONSTANT, because the five milestones and the
	// many sequence frames have different costs of a slow attempt: a
	// milestone is worth waiting kShotFileCeiling (15s) for, one sequence
	// sample is not worth stalling the walk it is meant to be
	// photographing, so it gets kSeqFileCeiling (5s) and is skipped rather
	// than chased.
	bool ShotPump(double Now, const FVector& Loc, double Ceiling, bool bCountsTowardShotsWrote,
	              std::string& OutLine)
	{
		bool bReady = false;
		if (!GShotUsedHighRes)
		{
			bReady = SizeSettled(GShotPath, GShotSizeTracker);
		}
		else
		{
			int32 Count = 0;
			const FString Newest = NewestPngUnder(
				FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()), Count);
			if (!Newest.IsEmpty() && SizeSettled(Newest, GShotSizeTracker))
			{
				IFileManager::Get().Copy(*GShotPath, *Newest, true, true);
				IFileManager::Get().Delete(*Newest, false, true, true);
				bReady = true;
			}
		}
		if (bReady)
		{
			bool bWrote = false;
			OutLine = MeasureShotFile(GShotPath, Loc, bWrote);
			if (bWrote && bCountsTowardShotsWrote) { ++GShotsWrote; }
			if (bWrote && !bCountsTowardShotsWrote) { ++GSeqWrote; }
			return true;
		}
		if ((Now - GShotWaitStart) < Ceiling) { return false; }
		if (!GShotUsedHighRes && !GShotTriedHighResOne)
		{
			GShotUsedHighRes = true;
			GShotTriedHighResOne = true;
			GShotWaitStart = Now;
			GShotSizeTracker = -1;
			if (GEngine != nullptr) { GEngine->Exec(GameWorld(), TEXT("HighResShot 960x540")); }
			return false;
		}
		const std::string ShotNameUtf8(TCHAR_TO_UTF8(*GShotName));
		char Head[192];
		std::snprintf(Head, sizeof(Head), "walkShot=%s walkShotAtXYZcm=%.1f/%.1f/%.1f ",
			ShotNameUtf8.c_str(), Loc.X, Loc.Y, Loc.Z);
		OutLine = std::string(Head) + "shotStatus=NO-FILE shotNote=neither-candidate-wrote-a-file-in-"
		        + std::to_string((int)Ceiling) + "s";
		return true;
	}

	// ONE HELPER FOR ALL FIVE CAPTURE POINTS, so the two-candidate
	// fallback and the decode-and-measure step exist once rather than
	// five times. Kicks the request off on the first tick this phase
	// runs, pumps it on every tick after, and advances GPhase once it is
	// done, whichever way it finished.
	bool RunShotPhase(const TCHAR* Name, const TCHAR* Leaf, EWalkPhase NextPhase, double Now)
	{
		if (!GShotInFlight)
		{
			GShotName = Name;
			ShotBegin(AbsProject(Leaf), Now);
			GShotInFlight = true;
			return true;
		}
		const FVector Loc = (GPawn != nullptr) ? GPawn->GetActorLocation() : FVector::ZeroVector;
		std::string Line;
		if (ShotPump(Now, Loc, kShotFileCeiling, /*bCountsTowardShotsWrote=*/true, Line))
		{
			GShotLines.push_back(Line);
			++GShotsAttempted;
			GShotInFlight = false;
			GPhase = NextPhase;
			GPhaseStart = Now;
		}
		return true;
	}

	// THE CLIP'S OWN CAPTURE, RUN INSIDE A WALKING PHASE RATHER THAN AS ONE
	// OF ITS OWN. Called every tick a movement phase runs; it either pumps a
	// sequence frame already in flight (holding the character still for
	// that one tick, exactly as a milestone capture does) or applies this
	// tick's movement input and, if enough time has passed since the last
	// attempt, starts the next one. A COOLDOWN AGAINST THE LAST CAPTURE,
	// NOT A FIXED SCHEDULE: measuring from "time since the last frame"
	// rather than from an absolute route clock means a slow attempt (or a
	// milestone capture that ran long before this phase started) cannot
	// cause a BURST of catch-up frames once movement resumes; it just
	// resumes the same 0.4s spacing from wherever it left off.
	void ApplyMovementAndMaybeCaptureSequence(const FVector& Dir, double Now)
	{
		if (GSeqInFlight)
		{
			const FVector Loc = (GPawn != nullptr) ? GPawn->GetActorLocation() : FVector::ZeroVector;
			std::string Line;
			if (ShotPump(Now, Loc, kSeqFileCeiling, /*bCountsTowardShotsWrote=*/false, Line))
			{
				GSeqInFlight = false;
			}
			// NO MOVEMENT INPUT THIS TICK. The character holds its pose for
			// the photo, the same trade a milestone capture already makes;
			// it resumes walking as soon as this one settles or gives up.
			return;
		}
		if (GPawn != nullptr) { GPawn->AddMovementInput(Dir, 1.0f); }
		if (GLastSeqCaptureTime == 0.0)
		{
			// PRIMED, NOT CAPTURED, ON THE FIRST CALL. A raw platform
			// timestamp compared against 0.0 would always look like "an
			// interval has passed", which would fire a capture on the very
			// first tick of movement, duplicating the ShotStart milestone
			// almost exactly.
			GLastSeqCaptureTime = Now;
			return;
		}
		if ((Now - GLastSeqCaptureTime) < kSeqInterval) { return; }
		if (GSeqRequested >= kMaxSeqFrames) { return; }
		GShotName = FString::Printf(TEXT("seq%03d"), GSeqRequested);
		ShotBegin(AbsProject(*FString::Printf(TEXT("ue-walkseq_%03d.png"), GSeqRequested)), Now);
		GSeqInFlight = true;
		++GSeqRequested;
		GLastSeqCaptureTime = Now;
	}

	// ---- THE GRATE: WHAT IS IN THE WAY, TRACED BEFORE ANYTHING SHOOTS ---
	//
	// COPIED FROM CrimeProbe.cpp, NOT INVENTED. That file's BlockerName and
	// TraceBlocked pair is how run 32 proved one crime was seen and one was
	// not: actorOccluded=no/actorBlocker=none against
	// actorOccluded=yes/actorBlocker=west_south_bay2. A second mechanism for
	// the same question is how two answers start disagreeing, so this is the
	// same channel (ECC_Visibility), the same bTraceComplex=false, the same
	// "ignore the target, because the question is what is BETWEEN", and the
	// same named fallback when the hit actor is not a street piece: a
	// packaged build answers GetName() with StaticMeshActor_NNN, because
	// SpawnPiece calls SetActorLabel under WITH_EDITOR only, and
	// LedgerVignetteShot::StreetPieceNameOf is the reverse lookup that turns
	// it back into a name a reader can act on.
	FString GrateBlockerNameOf(const AActor* Hit)
	{
		if (Hit == nullptr) { return TEXT("none"); }
		const FString Named = LedgerVignetteShot::StreetPieceNameOf(Hit);
		const FString Raw = Named.IsEmpty()
			? (FString(TEXT("unnamed/")) + Hit->GetName()) : Named;
		// NO SPACES IN A key=value VALUE, the same guard WalkSha applies to
		// the commit: every reader of this file splits on whitespace.
		return Raw.Replace(TEXT(" "), TEXT("~"));
	}

	// ONE LINE TRACE, FAIL-CLOSED. The grate itself is ignored (the question
	// is what stands BETWEEN, and the target is solid by construction); the
	// PAWN IS NOT IGNORED, because the view target here is a spawned camera
	// metres away from the pawn, so a body standing in the line would be
	// photographed exactly like any other obstruction and must read as one.
	// A missing world returns BLOCKED with a named reason rather than false,
	// because "there was no world to ask" must never read as "the line was
	// clear".
	bool GrateLineBlocked(UWorld* World, const FVector& From, const FVector& To,
	                      FString& OutBlocker)
	{
		OutBlocker = TEXT("none");
		if (World == nullptr)
		{
			OutBlocker = TEXT("nothing-measured/no-world-to-trace-in");
			return true;
		}
		FCollisionQueryParams Params;
		Params.bTraceComplex = false;
		if (GGrateActor != nullptr) { Params.AddIgnoredActor(GGrateActor); }
		FHitResult Hit;
		if (!World->LineTraceSingleByChannel(Hit, From, To, ECC_Visibility, Params))
		{
			return false;
		}
		OutBlocker = GrateBlockerNameOf(Hit.GetActor());
		return true;
	}

	// TEN RAYS FROM ONE STANDPOINT, AND WHICH FIVE OF THEM DECIDE.
	//
	// s0 to s4 are the SUBJECT RECTANGLE's own centre and four corners, the
	// same rectangle MeasureGrateAim projects and tools/grate-zfight.py
	// reads, so the decision is made on the pixels the verdict actually
	// names. f0 to f3 are the placed top face's four corners and b is the
	// placed bounds centre; both are CONTEXT and neither votes, because this
	// piece is set into the road and a placed piece's own edge can honestly
	// sit under the slab that covers it (run 35: buried=40.0pct by
	// ground_east_carriageway) while the rectangle being photographed is
	// wide open. b is inside the piece's own solid by definition, so with the
	// piece ignored it reports whatever shares that volume.
	struct FGrateRays
	{
		int32   SubjClear     = 0;
		int32   FaceClear     = 0;
		bool    bCentreClear  = false;
		bool    bHaveSubjBlkr = false;
		FString SubjBlocker   = TEXT("none");
		FString BlockedRays   = TEXT("");
	};

	FGrateRays TraceGrateFrom(UWorld* World, const FVector& From, const FBox& Box)
	{
		FGrateRays R;
		const FVector C  = Box.GetCenter();
		const double  Zc = (double)Box.Max.Z + kGrateRayLiftCm;
		const double  Sy = (double)C.Y + kGrateSubjOffsetCm;
		const double  H  = kGrateSubjHalfCm;
		const FVector Targets[kGrateRaysPerStand] = {
			FVector((float)C.X,       (float)Sy,       (float)Zc),
			FVector((float)(C.X - H), (float)(Sy - H), (float)Zc),
			FVector((float)(C.X + H), (float)(Sy - H), (float)Zc),
			FVector((float)(C.X + H), (float)(Sy + H), (float)Zc),
			FVector((float)(C.X - H), (float)(Sy + H), (float)Zc),
			FVector((float)Box.Min.X, (float)Box.Min.Y, (float)Zc),
			FVector((float)Box.Max.X, (float)Box.Min.Y, (float)Zc),
			FVector((float)Box.Max.X, (float)Box.Max.Y, (float)Zc),
			FVector((float)Box.Min.X, (float)Box.Max.Y, (float)Zc),
			FVector((float)C.X,       (float)C.Y,       (float)C.Z),
		};
		const TCHAR* Labels[kGrateRaysPerStand] = {
			TEXT("s0"), TEXT("s1"), TEXT("s2"), TEXT("s3"), TEXT("s4"),
			TEXT("f0"), TEXT("f1"), TEXT("f2"), TEXT("f3"), TEXT("b")
		};
		for (int32 I = 0; I < kGrateRaysPerStand; ++I)
		{
			FString Blocker;
			const bool bBlocked = GrateLineBlocked(World, From, Targets[I], Blocker);
			++GGrateRaysTraced;
			if (bBlocked)
			{
				if (!R.BlockedRays.IsEmpty()) { R.BlockedRays += TEXT(";"); }
				R.BlockedRays += FString::Printf(TEXT("%s..%s"), Labels[I], *Blocker);
				if (I < 5 && !R.bHaveSubjBlkr)
				{
					R.bHaveSubjBlkr = true;
					R.SubjBlocker = Blocker;
				}
			}
			else if (I < 5) { ++R.SubjClear; }
			else if (I < 9) { ++R.FaceClear; }
			else            { R.bCentreClear = true; }
		}
		if (R.BlockedRays.IsEmpty()) { R.BlockedRays = TEXT("none"); }
		return R;
	}

	// ---- THE COVERAGE COUNT: 81 CELLS OVER THE SAME SUBJECT RECTANGLE ----
	//
	// WHAT THIS IS FOR AND WHAT IT IS NOT FOR. The vote above is five rays 110
	// mm apart; this is kGrateSubjGridN squared rays 27.5 mm apart over the
	// SAME rectangle, so the two answers can be compared on the chosen row and
	// the question "is the vote sampled or measured" gets a number instead of
	// an argument. It is COUNTED AND NOT VOTED: nothing here is read by the
	// selection, no status word turns on it, and the cells are counted in
	// their own total (GGrateGridRaysTraced) so neither count borrows the
	// other's denominator.
	//
	// Cells is COUNTED IN THE LOOP rather than written as 81, so the
	// denominator printed is the number of cells actually examined and can
	// never be larger than the set walked. The first blocked cell is the first
	// in scan order, which is along the channel (I, world X) inside across the
	// street (J, world Y), and both are printed with the blocker so the reader
	// can tell a bar across the middle from a corner clipped by a post.
	struct FGrateGrid
	{
		int32   Clear   = 0;            // cells with a clear line to the lifted face
		int32   Cells   = 0;            // cells actually walked, the denominator
		int32   FirstI  = -1;           // first blocked cell, along the channel
		int32   FirstJ  = -1;           // first blocked cell, across the street
		FString Blocker = TEXT("none"); // what stopped that first blocked cell
	};

	// THE SPACING, DERIVED FROM THE RECTANGLE AND WRITTEN ONCE: nine samples
	// inclusive of both edges of a 22 cm square are 2.75 cm apart. The loop
	// below steps by this and the candidate line prints this, so the number a
	// reader sees is the number the rays were cast on and not a second copy
	// of 2.75 that could drift from it.
	double GrateSubjGridSpacingCm()
	{
		return (kGrateSubjGridN > 1)
			? (kGrateSubjHalfCm * 2.0 / (double)(kGrateSubjGridN - 1)) : 0.0;
	}

	FGrateGrid GridCoverageFrom(UWorld* World, const FVector& From, const FBox& Box)
	{
		FGrateGrid G;
		const FVector C  = Box.GetCenter();
		const double  Zc = (double)Box.Max.Z + kGrateRayLiftCm;
		const double  Sy = (double)C.Y + kGrateSubjOffsetCm;
		const double  H  = kGrateSubjHalfCm;
		const double  Step = GrateSubjGridSpacingCm();
		for (int32 J = 0; J < kGrateSubjGridN; ++J)
		{
			for (int32 I = 0; I < kGrateSubjGridN; ++I)
			{
				const FVector T((float)(C.X - H + Step * (double)I),
				                (float)(Sy  - H + Step * (double)J),
				                (float)Zc);
				FString Blocker;
				const bool bBlocked = GrateLineBlocked(World, From, T, Blocker);
				++GGrateGridRaysTraced;
				++G.Cells;
				if (!bBlocked) { ++G.Clear; }
				else if (G.FirstI < 0)
				{
					G.FirstI  = I;
					G.FirstJ  = J;
					G.Blocker = Blocker;
				}
			}
		}
		return G;
	}

	// ONE ANGLE DIFFERENCE, WRAPPED ONCE, IN ONE PLACE. Both the pitch and the
	// yaw difference below need the same wrap and a second copy is where two
	// readings of the same idea start disagreeing. A result near plus or minus
	// 180 in yaw means the control point is BEHIND the camera, which this
	// reports honestly as a very large off-axis angle rather than hiding it.
	double WrapDeg180(double D)
	{
		while (D >  180.0) { D -= 360.0; }
		while (D < -180.0) { D += 360.0; }
		return D;
	}

	// ---- THE GRATE: AIM, READ THE AIM BACK, THEN PHOTOGRAPH IT TWICE ----
	//
	// THE CAMERA IS A SPAWNED ACameraActor AND A SetViewTarget, WHICH IS THE
	// MECHANISM VignetteShot.cpp's PlaceCamera ALREADY USES for all four
	// vignette stills, copied rather than invented: the pawn's own camera is
	// a 3.5 m spring arm reading the controller's rotation, so aiming it at a
	// 0.40 m square would photograph the square from 5 m away behind an
	// invisible body. The capture path is unchanged: ShotBegin/ShotPump, the
	// same two candidates and the same decode-and-measure as the other five.
	void AimAtGrate()
	{
		const int32 RayBudget = kGrateStandCount * kGrateRaysPerStand;
		// THE COVERAGE GRID'S OWN BUDGET, AND IT IS A DIFFERENT DENOMINATOR
		// FROM RayBudget. 81 cells per standpoint tried against ten voting rays
		// per standpoint tried: two counts of two different things, printed
		// under two names, neither one divisible by the other's total.
		const int32 GridBudget = kGrateStandCount * kGrateSubjGridN * kGrateSubjGridN;
		UWorld* World = GameWorld();
		if (World == nullptr)
		{
			GGrateLine = FString::Printf(
				TEXT("grateShotStatus=NO-WORLD ")
				TEXT("grateShotReason=the-game-world-vanished-between-ticks ")
				TEXT("grateOccluded=nothing-measured grateBlocker=nothing-measured ")
				TEXT("grateCandidatesTried=0/%d grateRaysTraced=0/%d ")
				TEXT("grateSubjGridRaysTraced=0/%d"),
				kGrateStandCount, RayBudget, GridBudget);
			GGrateSkipWhy = TEXT("no-world-to-trace-in-or-shoot-from/nothing-measured");
			return;
		}
		GGrateActor = LedgerVignetteShot::FindStreetPiece(kGrateName);
		if (GGrateActor == nullptr)
		{
			GGrateLine = FString::Printf(
				TEXT("grateShotStatus=NOTHING-MEASURED grateShotName=%s ")
				TEXT("grateShotReason=name-not-among-the-pieces-BuildScene-spawned ")
				TEXT("grateOccluded=nothing-measured grateBlocker=nothing-measured ")
				TEXT("grateCandidatesTried=0/%d grateRaysTraced=0/%d ")
				TEXT("grateSubjGridRaysTraced=0/%d"),
				kGrateName, kGrateStandCount, RayBudget, GridBudget);
			GGrateSkipWhy = FString::Printf(
				TEXT("no-piece-named-%s-to-trace-to/nothing-measured"), kGrateName);
			return;
		}
		// THE ENGINE'S OWN BOUNDS, AFTER SCALE AND ROTATION, NOT THE FILE'S
		// NUMBERS A SECOND TIME. The same read the blocked-walk plant makes.
		const FBox   Box  = GGrateActor->GetComponentsBoundingBox();
		const FVector C   = Box.GetCenter();
		const double TopZ = (double)Box.Max.Z;
		const FVector AimAt((float)C.X, (float)C.Y, (float)TopZ);
		// THE CONTROL POINT, READ OFF THE SAME ARITHMETIC MeasureGrateAim USES
		// AND NOT A SECOND COPY OF IT: the centre of the control rectangle, 80
		// cm toward the crown at the placed top face's height. This file
		// measures the ANGLE to it per candidate and prints it; whether its
		// rectangle lands inside the frame is still MeasureGrateAim's own
		// answer, on the chosen standpoint only, as grateRectStatus.
		const FVector CtrlPt((float)C.X, (float)(C.Y - kGrateCtrlAcrossCm), (float)TopZ);
		// THE TWO HALF-FIELDS THE ANGLES ARE PRINTED AGAINST, derived from the
		// camera this phase actually sets up (kGrateVFovDeg on kGrateShotW by
		// kGrateShotH through the one converter in VignetteSpec.h) rather than
		// typed as numbers beside it. NOTHING IS COMPARED AGAINST THEM HERE:
		// they travel on the same line as the angle so a reader of one row has
		// the pair in hand and never has to remember a field from elsewhere.
		const double HalfVDeg = kGrateVFovDeg * 0.5;
		const double HalfHDeg = LedgerVignette::HorizontalFovDeg(
			kGrateVFovDeg, kGrateShotW, kGrateShotH) * 0.5;

		// TRACE, THEN CHOOSE, THEN SHOOT, AND IN THAT ORDER BECAUSE RUN 35
		// SHOT FIRST. Every standpoint in kGrateStands is traced to the ten
		// points TraceGrateFrom names; the FIRST whose five subject rays are
		// all clear is taken and the search stops there, so a clear row 00
		// costs ten traces and reproduces run 35's framing exactly. Every row
		// tried prints its own line (grateCand= below), clear counts and the
		// named blocker of every ray that was stopped, so a refusal is
		// diagnosable without another run.
		int32      Chosen = -1, Tried = 0;
		FVector    CamLoc = FVector::ZeroVector;
		FRotator   CamRot = FRotator::ZeroRotator;
		FGrateRays Rays;
		FString    FirstBlocker = TEXT("none");
		for (int32 I = 0; I < kGrateStandCount; ++I)
		{
			const FVector Stand((float)(C.X + kGrateStands[I].AlongCm),
			                    (float)(C.Y + kGrateStands[I].AcrossCm),
			                    (float)(TopZ + kGrateStands[I].EyeCm));
			// THE ROTATION IS DERIVED FROM THE TWO POINTS, never a pitch
			// guessed and hoped to land: whatever the placed piece's top
			// turns out to be, this points at it.
			const FRotator StandRot = (AimAt - Stand).Rotation();
			const FGrateRays R = TraceGrateFrom(World, Stand, Box);
			++Tried;
			const bool bClear = (R.SubjClear == 5);
			// THE FRAMING ANGLES, MEASURED AND NOT ARGUED, AND THEY DECIDE
			// NOTHING. Same two points, two rotations: the camera axis is the
			// one this row would be aimed along, and the other is the line to
			// the control rectangle's centre. The difference is reported per
			// axis because the frame has two half-fields, and it is the angle
			// to the centre of that rectangle, NOT a test of whether the
			// rectangle is in frame. The series exists so the selection
			// predicate can be set from real runs instead of trigonometry.
			const FRotator CtrlRot  = (CtrlPt - Stand).Rotation();
			const double   OffPitch = WrapDeg180((double)CtrlRot.Pitch - (double)StandRot.Pitch);
			const double   OffYaw   = WrapDeg180((double)CtrlRot.Yaw   - (double)StandRot.Yaw);
			// THE DENSE COUNT, CAST AFTER THE VOTE AND READ BY NOTHING. Its
			// rays go to GGrateGridRaysTraced, never to GGrateRaysTraced, and
			// bClear above is already decided before this line runs.
			const FGrateGrid Grid = GridCoverageFrom(World, Stand, Box);
			const FString GridFirstCell = (Grid.FirstI < 0)
				? FString(TEXT("none"))
				: FString::Printf(TEXT("%02d/%02d"), Grid.FirstI, Grid.FirstJ);
			// ROW 00 IS THE ONE RUN 35 USED, so its blocker is the one named
			// on a refusal: it answers "what was in that photograph".
			if (I == 0) { FirstBlocker = R.SubjBlocker; }
			GGrateCandLines.Add(FString::Printf(
				TEXT("grateCand=%02d grateCandOffsetAcrossAlongEyeCm=%.1f/%.1f/%.1f ")
				TEXT("grateCandAtXYZcm=%.1f/%.1f/%.1f grateCandPitchDeg=%.1f ")
				TEXT("grateCandStandoffCm=%.1f grateCandSubjectRaysClear=%d/5 ")
				TEXT("grateCandFaceRaysClear=%d/4 grateCandCentreRayClear=%s ")
				TEXT("grateCandOccluded=%s grateCandBlocker=%s grateCandBlockedRays=%s ")
				TEXT("grateCandCtrlOffPitchDeg=%.1f grateCandCtrlOffYawDeg=%.1f ")
				TEXT("grateCandHalfVDeg=%.1f grateCandHalfHDeg=%.1f ")
				TEXT("grateCandFramingStat=angle-to-the-control-rectangles-CENTRE-from-the-")
				TEXT("camera-axis/not-a-rect-in-frame-test/printed-so-the-selection-rule-can-")
				TEXT("be-set-from-a-series ")
				TEXT("grateCandSubjGridClear=%d/%d grateCandSubjGridSpacingCm=%.2f ")
				TEXT("grateCandSubjGridFirstBlockedCellAlongAcross=%s ")
				TEXT("grateCandSubjGridFirstBlocker=%s ")
				TEXT("grateCandSubjGridStat=counted-over-the-cells-walked/not-voted-on/")
				TEXT("the-selection-is-still-grateCandSubjectRaysClear-and-first-clear-wins ")
				TEXT("grateCandChosen=%s"),
				I, kGrateStands[I].AcrossCm, kGrateStands[I].AlongCm, kGrateStands[I].EyeCm,
				Stand.X, Stand.Y, Stand.Z, StandRot.Pitch,
				FVector::Dist(Stand, AimAt), R.SubjClear, R.FaceClear,
				R.bCentreClear ? TEXT("yes") : TEXT("no"),
				bClear ? TEXT("no") : TEXT("yes"), *R.SubjBlocker, *R.BlockedRays,
				OffPitch, OffYaw, HalfVDeg, HalfHDeg,
				Grid.Clear, Grid.Cells, GrateSubjGridSpacingCm(),
				*GridFirstCell, *Grid.Blocker,
				bClear ? TEXT("yes") : TEXT("no")));
			if (bClear)
			{
				Chosen = I;
				CamLoc = Stand;
				CamRot = StandRot;
				Rays   = R;
				break;
			}
		}

		// A SHOT WHOSE SUBJECT IS OCCLUDED REFUSES AND NAMES THE BLOCKER.
		// Run 35's frame 05 has the guard railing's post and mid rail across
		// the subject rectangle, filed under every green key this probe owns,
		// and the only thing that stops that recurring is this branch: no camera is spawned, no
		// view target is taken, and frames 05 and 06 are not written.
		if (Chosen < 0)
		{
			GGrateLine = FString::Printf(
				TEXT("grateShotStatus=REFUSED-OCCLUDED grateShotName=%s ")
				TEXT("grateOccluded=yes grateBlocker=%s ")
				TEXT("grateBlockerFrom=cand00/first-blocked-subject-ray ")
				TEXT("grateBoundsCentreXYZcm=%.1f/%.1f/%.1f grateBoundsTopZcm=%.2f ")
				TEXT("grateBoundsSizeXYZcm=%.1f/%.1f/%.1f ")
				TEXT("grateCandidatesTried=%d/%d grateCandidatesBlocked=%d/%d ")
				TEXT("grateRaysTraced=%d/%d grateFramesNotTaken=2/2 ")
				TEXT("grateSubjGridRaysTraced=%d/%d ")
				TEXT("grateSubjGridRaysStat=cumulative-over-the-standpoints-actually-tried/")
				TEXT("81-cells-each/counted-apart-from-grateRaysTraced-so-neither-borrows-the-")
				TEXT("others-denominator ")
				TEXT("grateRayLiftCm=%.1f ")
				TEXT("grateRayLiftStat=clearance-above-the-placed-top-face/not-a-bound/")
				TEXT("the-face-is-coplanar-with-the-road-plane-at-0.000mm ")
				TEXT("grateShotReason=no-standpoint-had-a-clear-line-to-the-subject-rectangle/")
				TEXT("a-photograph-of-the-obstruction-is-not-a-photograph-of-the-piece ")
				TEXT("grateOccludedStat=decided-on-the-five-subject-rectangle-rays-per-standpoint/")
				TEXT("face-corners-and-bounds-centre-are-context-and-do-not-vote"),
				kGrateName, *FirstBlocker,
				C.X, C.Y, C.Z, TopZ,
				Box.GetSize().X, Box.GetSize().Y, Box.GetSize().Z,
				Tried, kGrateStandCount, Tried, Tried,
				GGrateRaysTraced, RayBudget,
				GGrateGridRaysTraced, GridBudget,
				kGrateRayLiftCm);
			GGrateRectLine = FString::Printf(
				TEXT("grateRectStatus=NOTHING-MEASURED ")
				TEXT("grateRectReason=the-shot-was-refused-so-no-camera-was-aimed-and-no-rectangle-")
				TEXT("exists-to-read/blocker=%s"), *FirstBlocker);
			GGrateSkipWhy = FString::Printf(
				TEXT("subject-occluded/blocker=%s/standpoints-tried=%d-of-%d/no-clear-line"),
				*FirstBlocker, Tried, kGrateStandCount);
			return;
		}

		if (GGrateCam == nullptr)
		{
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			GGrateCam = World->SpawnActor<ACameraActor>(
				ACameraActor::StaticClass(), CamLoc, CamRot, Params);
		}
		else
		{
			GGrateCam->SetActorLocationAndRotation(CamLoc, CamRot);
		}
		if (GGrateCam == nullptr)
		{
			GGrateLine = TEXT("grateShotStatus=SPAWN-FAILED ")
			             TEXT("grateShotReason=the-world-refused-to-spawn-a-camera-actor ")
			             TEXT("grateOccluded=no grateBlocker=none");
			GGrateSkipWhy = TEXT("the-world-refused-to-spawn-a-camera-actor/nothing-measured");
			return;
		}
		if (UCameraComponent* CC = GGrateCam->GetCameraComponent())
		{
			// VERTICAL TO HORIZONTAL, THROUGH THE CONVERTER IN VignetteSpec.h
			// THAT g++ ALREADY RUNS: this engine's FieldOfView is horizontal
			// and the framing arithmetic above is vertical, and a second copy
			// of that conversion in this file is how two cameras meant to
			// match stop matching.
			CC->SetFieldOfView((float)LedgerVignette::HorizontalFovDeg(
				kGrateVFovDeg, kGrateShotW, kGrateShotH));
			CC->SetAspectRatio((float)kGrateShotW / (float)kGrateShotH);
			CC->SetConstraintAspectRatio(true);
		}
		APlayerController* PC = World->GetFirstPlayerController();
		if (PC == nullptr)
		{
			GGrateLine = TEXT("grateShotStatus=NO-CONTROLLER ")
			             TEXT("grateShotReason=no-first-player-controller-to-take-the-view ")
			             TEXT("grateOccluded=no grateBlocker=none");
			GGrateSkipWhy = TEXT("no-first-player-controller-to-take-the-view/nothing-measured");
			return;
		}
		// CAPTURED, NOT ASSUMED, so the restore below puts back what was
		// actually there rather than what this file believes was there.
		GViewBefore = PC->GetViewTarget();
		PC->SetViewTarget(GGrateCam);
		// THE ONLY PATH THAT SHOOTS. grateOccluded=no and grateBlocker=none
		// here are the accepting case of the same pair CrimeProbe prints, read
		// off the standpoint this camera is actually standing on.
		bGrateShootable = true;
		GGrateLine = FString::Printf(
			TEXT("grateShotStatus=AIMED grateShotName=%s ")
			TEXT("grateOccluded=no grateBlocker=none grateSubjectRaysClear=%d/5 ")
			TEXT("grateFaceRaysClear=%d/4 grateCentreRayClear=%s grateBlockedRays=%s ")
			TEXT("grateCandChosen=%02d grateCandidatesTried=%d/%d grateCandidatesBlocked=%d/%d ")
			TEXT("grateRaysTraced=%d/%d ")
			TEXT("grateOccludedStat=decided-on-the-five-subject-rectangle-rays-of-the-chosen-")
			TEXT("standpoint/face-corners-and-bounds-centre-are-context-and-do-not-vote ")
			TEXT("grateRaysStat=cumulative-over-the-standpoints-actually-tried/ten-each/")
			TEXT("the-search-stops-at-the-first-clear-one ")
			TEXT("grateSubjGridRaysTraced=%d/%d ")
			TEXT("grateSubjGridRaysStat=cumulative-over-the-standpoints-actually-tried/")
			TEXT("81-cells-each/counted-apart-from-grateRaysTraced-so-neither-borrows-the-")
			TEXT("others-denominator ")
			TEXT("grateRayLiftCm=%.1f ")
			TEXT("grateRayLiftStat=clearance-above-the-placed-top-face/not-a-bound/")
			TEXT("the-face-is-coplanar-with-the-road-plane-at-0.000mm ")
			TEXT("grateBoundsCentreXYZcm=%.1f/%.1f/%.1f grateBoundsTopZcm=%.2f ")
			TEXT("grateBoundsSizeXYZcm=%.1f/%.1f/%.1f ")
			TEXT("grateCamAskedXYZcm=%.1f/%.1f/%.1f grateCamAskedPitchYaw=%.1f/%.1f ")
			TEXT("grateCamStandoffCm=%.1f grateCamVFovDeg=%.1f grateCamHFovDeg=%.1f"),
			kGrateName,
			Rays.SubjClear, Rays.FaceClear, Rays.bCentreClear ? TEXT("yes") : TEXT("no"),
			*Rays.BlockedRays, Chosen, Tried, kGrateStandCount, Tried - 1, Tried,
			GGrateRaysTraced, RayBudget,
			GGrateGridRaysTraced, GridBudget,
			kGrateRayLiftCm,
			C.X, C.Y, C.Z, TopZ,
			Box.GetSize().X, Box.GetSize().Y, Box.GetSize().Z,
			CamLoc.X, CamLoc.Y, CamLoc.Z, CamRot.Pitch, CamRot.Yaw,
			FVector::Dist(CamLoc, AimAt), kGrateVFovDeg,
			LedgerVignette::HorizontalFovDeg(kGrateVFovDeg, kGrateShotW, kGrateShotH));
	}

	// FOUR CORNERS OF A HORIZONTAL SQUARE, PROJECTED, AND THE AXIS-ALIGNED
	// PIXEL BOX THAT CONTAINS THEM. Returns false if ANY corner refuses to
	// project, because a box built from three of four corners is a box over
	// the wrong pixels and would be a silent instrument.
	bool ProjectSquare(APlayerController* PC, double CX, double CY, double CZ, double HalfCm,
	                   FVector2D& OutMin, FVector2D& OutMax)
	{
		const double Dx[4] = { -1.0,  1.0, 1.0, -1.0 };
		const double Dy[4] = { -1.0, -1.0, 1.0,  1.0 };
		for (int32 I = 0; I < 4; ++I)
		{
			FVector2D S(0.0, 0.0);
			const FVector W((float)(CX + Dx[I] * HalfCm), (float)(CY + Dy[I] * HalfCm), (float)CZ);
			if (!PC->ProjectWorldLocationToScreen(W, S, false)) { return false; }
			if (I == 0) { OutMin = S; OutMax = S; }
			else
			{
				OutMin.X = FMath::Min(OutMin.X, S.X);
				OutMin.Y = FMath::Min(OutMin.Y, S.Y);
				OutMax.X = FMath::Max(OutMax.X, S.X);
				OutMax.Y = FMath::Max(OutMax.Y, S.Y);
			}
		}
		return true;
	}

	// READ THE AIM BACK AND SAY WHERE THE TWO RECTANGLES LANDED, ONE TICK
	// AFTER THE CAMERA WAS TAKEN, because a view point read on the same tick
	// the view target changed can still be the old camera's.
	//
	// THE RECTANGLES ARE EMITTED AS FRACTIONS OF THE FRAME, not pixels: this
	// capture path has two candidates (a viewport screenshot and a 960x540
	// HighResShot) and they need not be the same size, so a pixel box would
	// be right for one and wrong for the other. tools/grate-zfight.py
	// multiplies these by the image's OWN width and height.
	void MeasureGrateAim()
	{
		UWorld* World = GameWorld();
		APlayerController* PC = (World != nullptr) ? World->GetFirstPlayerController() : nullptr;
		if (PC == nullptr || GGrateActor == nullptr || GGrateCam == nullptr)
		{
			GGrateRectLine = TEXT("grateRectStatus=NOTHING-MEASURED ")
			                 TEXT("grateRectReason=no-controller-or-no-aim-to-read-back");
			return;
		}
		FVector  GotLoc = FVector::ZeroVector;
		FRotator GotRot = FRotator::ZeroRotator;
		PC->GetPlayerViewPoint(GotLoc, GotRot);
		int32 VpW = 0, VpH = 0;
		PC->GetViewportSize(VpW, VpH);
		if (VpW <= 0 || VpH <= 0)
		{
			GGrateRectLine = FString::Printf(
				TEXT("grateRectStatus=NOTHING-MEASURED grateRectReason=viewport-size-read-%d-by-%d ")
				TEXT("grateCamReadXYZcm=%.1f/%.1f/%.1f grateCamReadPitchYaw=%.1f/%.1f"),
				VpW, VpH, GotLoc.X, GotLoc.Y, GotLoc.Z, GotRot.Pitch, GotRot.Yaw);
			return;
		}
		const FBox    Box  = GGrateActor->GetComponentsBoundingBox();
		const FVector C    = Box.GetCenter();
		const double  TopZ = (double)Box.Max.Z;

		FVector2D SubMin(0.0, 0.0), SubMax(0.0, 0.0);
		const bool bSub = ProjectSquare(PC, C.X, C.Y + kGrateSubjOffsetCm, TopZ,
		                                kGrateSubjHalfCm, SubMin, SubMax);
		FVector2D CtrCentre(0.0, 0.0);
		const bool bCtr = PC->ProjectWorldLocationToScreen(
			FVector((float)C.X, (float)(C.Y - kGrateCtrlAcrossCm), (float)TopZ), CtrCentre, false);
		if (!bSub || !bCtr)
		{
			GGrateRectLine = FString::Printf(
				TEXT("grateRectStatus=NOTHING-MEASURED ")
				TEXT("grateRectReason=projection-refused-subject=%s-control=%s ")
				TEXT("grateCamReadXYZcm=%.1f/%.1f/%.1f grateCamReadPitchYaw=%.1f/%.1f"),
				bSub ? TEXT("ok") : TEXT("no"), bCtr ? TEXT("ok") : TEXT("no"),
				GotLoc.X, GotLoc.Y, GotLoc.Z, GotRot.Pitch, GotRot.Yaw);
			return;
		}
		// THE CONTROL IS THE SUBJECT'S OWN PIXEL BOX, MOVED. Same area by
		// construction and not by a second calculation that could disagree.
		const double HalfW = (double)(SubMax.X - SubMin.X) * 0.5;
		const double HalfH = (double)(SubMax.Y - SubMin.Y) * 0.5;
		const double CtrX0 = (double)CtrCentre.X - HalfW, CtrX1 = (double)CtrCentre.X + HalfW;
		const double CtrY0 = (double)CtrCentre.Y - HalfH, CtrY1 = (double)CtrCentre.Y + HalfH;
		const bool bInFrame =
			SubMin.X >= 0.0 && SubMin.Y >= 0.0 && SubMax.X <= (double)VpW && SubMax.Y <= (double)VpH &&
			CtrX0 >= 0.0 && CtrY0 >= 0.0 && CtrX1 <= (double)VpW && CtrY1 <= (double)VpH;
		GGrateRectLine = FString::Printf(
			TEXT("grateRectStatus=%s grateRectFrameWH=%d/%d ")
			TEXT("grateSubjectRectFrac=%.4f/%.4f/%.4f/%.4f grateControlRectFrac=%.4f/%.4f/%.4f/%.4f ")
			TEXT("grateSubjectRectPx=%.0f/%.0f grateRectPixelsEach=%.0f ")
			TEXT("grateSubjectIs=grate-top-face-inset-and-clear-of-the-yellow ")
			TEXT("grateControlIs=plain-carriageway-%.0fcm-toward-the-crown/same-pixel-area ")
			TEXT("grateCamReadXYZcm=%.1f/%.1f/%.1f grateCamReadPitchYaw=%.1f/%.1f ")
			TEXT("grateRectNote=fractions-of-the-frame/multiply-by-the-image-own-size"),
			bInFrame ? TEXT("MEASURED") : TEXT("OFF-FRAME"), VpW, VpH,
			(double)SubMin.X / VpW, (double)SubMin.Y / VpH,
			(double)SubMax.X / VpW, (double)SubMax.Y / VpH,
			CtrX0 / VpW, CtrY0 / VpH, CtrX1 / VpW, CtrY1 / VpH,
			HalfW * 2.0, HalfH * 2.0, HalfW * 2.0 * HalfH * 2.0,
			kGrateCtrlAcrossCm,
			GotLoc.X, GotLoc.Y, GotLoc.Z, GotRot.Pitch, GotRot.Yaw);
	}

	// PUT THE VIEW BACK WHERE IT WAS. The process exits seconds later, but a
	// probe that leaves the player looking through its own camera is a probe
	// whose next reader inherits its idea of the scene; and it is RESTORED TO
	// THE CAPTURED TARGET rather than to the pawn this file assumes was
	// there. Read back one tick later by ConfirmRestore below.
	void RestoreViewTarget()
	{
		UWorld* World = GameWorld();
		APlayerController* PC = (World != nullptr) ? World->GetFirstPlayerController() : nullptr;
		if (PC == nullptr || GViewBefore == nullptr)
		{
			GGrateRestoreLine = TEXT("grateViewRestoreStatus=NOTHING-MEASURED ")
			                    TEXT("grateViewRestoreReason=nothing-was-captured-to-restore");
			return;
		}
		PC->SetViewTarget(GViewBefore);
		GGrateRestoreLine = TEXT("grateViewRestoreStatus=ASKED grateViewRestoreRead=not-yet-read");
	}

	void ConfirmViewRestore()
	{
		UWorld* World = GameWorld();
		APlayerController* PC = (World != nullptr) ? World->GetFirstPlayerController() : nullptr;
		if (PC == nullptr || GViewBefore == nullptr) { return; }
		const AActor* Now = PC->GetViewTarget();
		GGrateRestoreLine = FString::Printf(
			TEXT("grateViewRestoreStatus=%s grateViewRestoreWas=%s ")
			TEXT("grateViewRestoreNowIsTheProbeCamera=%s"),
			(Now == GViewBefore) ? TEXT("RESTORED") : TEXT("NOT-RESTORED"),
			(GViewBefore == static_cast<AActor*>(GPawn)) ? TEXT("the-pawn") : TEXT("not-the-pawn"),
			(Now == static_cast<AActor*>(GGrateCam)) ? TEXT("yes") : TEXT("no"));
	}

	// WRITTEN AT EACH MILESTONE, BEFORE THE WORK THAT MILESTONE GUARDS. A
	// crash between two milestones leaves the LAST one on disk, which is
	// what tells the workflow step "started but crashed at X" apart from
	// "never started" and from "finished". Overwritten, not appended: one
	// current phase, not a growing log a later reader has to scan for the
	// last line.
	void WriteBreadcrumb(const TCHAR* Phase)
	{
		TArray<FString> Out;
		Out.Add(FString::Printf(TEXT("# UE walk probe %s @%lld"),
		                        *WalkSha(), (long long)FDateTime::UtcNow().ToUnixTimestamp()));
		Out.Add(TEXT("# Line 1 names the commit this was measured on, as the Unity verdict does."));
		Out.Add(TEXT(""));
		Out.Add(FString::Printf(TEXT("walkPhaseReached=%s"), Phase));
		Out.Add(TEXT("walkReached=in-progress"));
		const FString Body = FString::Join(Out, TEXT("\n")) + TEXT("\n");
		FFileHelper::SaveStringToFile(Body, *AbsProject(TEXT("ue-walk-verdict.txt")));
		FFileHelper::SaveStringToFile(Body, *FPaths::Combine(
			FPaths::GetPath(FPlatformProcess::ExecutablePath()), TEXT("ue-walk-verdict.txt")));
	}

	void WriteFinalVerdict()
	{
		TArray<FString> Out;
		Out.Add(FString::Printf(TEXT("# UE walk probe %s @%lld"),
		                        *WalkSha(), (long long)FDateTime::UtcNow().ToUnixTimestamp()));
		Out.Add(TEXT("# Line 1 names the commit this was measured on, as the Unity verdict does."));
		Out.Add(TEXT("# Ruling 1, Jafar, 2026-09-07: this replaces human smoke-testing. Five"));
		Out.Add(TEXT("#   judgments; judgment 1 (launch) is added by the workflow step from this"));
		Out.Add(TEXT("#   file's own presence, its last walkPhaseReached and its exit code, because"));
		Out.Add(TEXT("#   only something watching the process from outside can tell a hang from a"));
		Out.Add(TEXT("#   crash from a clean exit. Judgments 2-5 are below."));
		Out.Add(TEXT("# JUDGMENT 2, streetStatus / sceneStatus line: the SAME piecesEmitted=N/M"));
		Out.Add(TEXT("#   counters BuildScene emits for the vignette path, read back, not"));
		Out.Add(TEXT("#   recomputed."));
		Out.Add(TEXT("# JUDGMENT 3, walkCamera*: GetActorLocation() before and after a scripted"));
		Out.Add(TEXT("#   AddMovementInput phase down the open footway. walkCameraDistanceCm is"));
		Out.Add(TEXT("#   the ACCEPTING-CASE distance and is reused, not remeasured, as"));
		Out.Add(TEXT("#   collisionClearDistanceCm below: they are one variable."));
		Out.Add(TEXT("# JUDGMENT 4, testCardsSpawned=N/M: M is LedgerSurface::ControlQuadCount(),"));
		Out.Add(TEXT("#   the count the automation path would spawn; N is what THIS process"));
		Out.Add(TEXT("#   actually spawned, which is 0 by construction on this path."));
		Out.Add(TEXT("# JUDGMENT 5, collision*: a PLANTED pair per rule 5b. collisionClear* is the"));
		Out.Add(TEXT("#   accepting case (the open footway); collisionBlocked* is the rejecting"));
		Out.Add(TEXT("#   case, walked straight at east_parade_bay0, a full-height terrace carcass"));
		Out.Add(TEXT("#   looked up by name from the street BuildScene actually spawned. STOPPED,"));
		Out.Add(TEXT("#   PASSED-THROUGH, MOVED and STUCK are coarse first-cut splits, not bounds"));
		Out.Add(TEXT("#   read off a series (rule 2): this instrument has never run before this"));
		Out.Add(TEXT("#   commit, so the raw *DistanceCm numbers beside every word are the"));
		Out.Add(TEXT("#   evidence, not the word."));
		Out.Add(TEXT("# THE GRATE, frames 05 and 06 and every grate* key below: ONE CAMERA aimed"));
		Out.Add(TEXT("#   at prop_drainage_grate_01_0 from the pavement side, photographed TWICE"));
		Out.Add(TEXT("#   without moving. Frame 05 is the picture of Jafar's accepting case, which"));
		Out.Add(TEXT("#   run 34 measured (propsAsMesh, propPlacedWithCollision, propFullyBuried)"));
		Out.Add(TEXT("#   and no frame showed. The PAIR exists because the piece's top face is"));
		Out.Add(TEXT("#   coincident with the channel and carriageway top faces, and whether that"));
		Out.Add(TEXT("#   ties in the depth test is read by tools/grate-zfight.py as a speckle AND"));
		Out.Add(TEXT("#   a frame-to-frame flicker density, against the same-area control rectangle"));
		Out.Add(TEXT("#   named on the grateRect line. THE CONTROL IS THE DENOMINATOR: no bound is"));
		Out.Add(TEXT("#   set here, and this file decides nothing about the tie. It supplies the"));
		Out.Add(TEXT("#   two frames and the two rectangles as FRACTIONS of the frame."));
		Out.Add(TEXT("# AND IT TRACES BEFORE IT SHOOTS, since run 35. That run printed"));
		Out.Add(TEXT("#   grateShotStatus=AIMED, grateRectStatus=MEASURED and walkFramesWrote=7/7"));
		Out.Add(TEXT("#   over a frame in which the east kerb's pedestrian guard railing (E8,"));
		Out.Add(TEXT("#   posts at x=10/12/14/16 m in the plane z=3.375 m, one of them at the"));
		Out.Add(TEXT("#   grate's own x) stands between the camera and the piece, and nothing"));
		Out.Add(TEXT("#   asked what was in the line. The camera arithmetic was right. Each"));
		Out.Add(TEXT("#   standpoint in the table is now line-traced to ten points first (five on"));
		Out.Add(TEXT("#   the subject rectangle, which decide; four top-face corners and the"));
		Out.Add(TEXT("#   bounds centre, which are context), the first with five clear subject"));
		Out.Add(TEXT("#   rays is taken, and grateOccluded / grateBlocker are the same pair"));
		Out.Add(TEXT("#   CrimeProbe prints. With no clear standpoint the shot is REFUSED with"));
		Out.Add(TEXT("#   the blocker named and frames 05 and 06 are NOT written."));
		Out.Add(TEXT("# THE CLIP: this file writes two kinds of frame. ue-walk_NN_*.png is the"));
		Out.Add(TEXT("#   evidence, seven named milestones (five route, two grate), untouched by"));
		Out.Add(TEXT("#   the clip. ue-walkseq_NNN.png"));
		Out.Add(TEXT("#   is the SEQUENCE (walkSeqFramesRequested/Wrote below), which"));
		Out.Add(TEXT("#   tools/clip-from-frames.py (Pillow, no new dependency; see its own header)"));
		Out.Add(TEXT("#   stitches into one GIF outside this process. This file never writes a GIF."));
		Out.Add(TEXT(""));

		Out.Add(LedgerVignetteShot::StreetSceneLine());

		if (bClearWalked)
		{
			const double D = (double)FVector::Dist(GClearStartLoc, GClearEndLoc);
			Out.Add(FString::Printf(
				TEXT("walkCameraStartXYZcm=%.1f/%.1f/%.1f walkCameraEndXYZcm=%.1f/%.1f/%.1f ")
				TEXT("walkCameraDistanceCm=%.1f walkCameraSeconds=%.2f ")
				TEXT("walkCameraStat=accepting-case/open-footway walkCameraStatus=%s"),
				GClearStartLoc.X, GClearStartLoc.Y, GClearStartLoc.Z,
				GClearEndLoc.X, GClearEndLoc.Y, GClearEndLoc.Z,
				D, kClearHalfSeconds * 2.0,
				D > kStuckFloorCm ? TEXT("MOVED") : TEXT("STUCK")));
			Out.Add(FString::Printf(
				TEXT("collisionClearDistanceCm=%.1f collisionClearSeconds=%.2f ")
				TEXT("collisionClearStat=same-measurement-as-walkCameraDistanceCm/one-variable ")
				TEXT("collisionClearStatus=%s"),
				D, kClearHalfSeconds * 2.0, D > kStuckFloorCm ? TEXT("MOVED") : TEXT("STUCK")));
		}
		else
		{
			Out.Add(FString::Printf(
				TEXT("walkCameraStatus=NOTHING-MEASURED walkCameraReason=%s"), *GFinishReason));
			Out.Add(FString::Printf(
				TEXT("collisionClearStatus=NOTHING-MEASURED collisionClearReason=%s"), *GFinishReason));
		}

		bool bBlockedOk = false;
		if (!bTeleported)
		{
			Out.Add(FString::Printf(
				TEXT("collisionBlockedStatus=NOTHING-MEASURED collisionBlockedReason=%s ")
				TEXT("collisionBlockedWallName=%s collisionBlockedWallFound=%s"),
				*GFinishReason, kWallName, GWallFound ? TEXT("yes") : TEXT("no")));
		}
		else if (bBlockedWalked)
		{
			const double BD = (double)FVector::Dist(GBlockedStartLoc, GBlockedEndLoc);
			bBlockedOk = BD < (kApproachClearanceCm - 20.0);
			Out.Add(FString::Printf(
				TEXT("collisionBlockedWallName=%s collisionBlockedApproachClearanceCm=%.1f ")
				TEXT("collisionBlockedStartXYZcm=%.1f/%.1f/%.1f collisionBlockedEndXYZcm=%.1f/%.1f/%.1f ")
				TEXT("collisionBlockedDistanceCm=%.1f collisionBlockedSeconds=%.2f ")
				TEXT("collisionBlockedStat=first-run-of-this-instrument/not-a-tuned-bound ")
				TEXT("collisionBlockedStatus=%s"),
				kWallName, kApproachClearanceCm,
				GBlockedStartLoc.X, GBlockedStartLoc.Y, GBlockedStartLoc.Z,
				GBlockedEndLoc.X, GBlockedEndLoc.Y, GBlockedEndLoc.Z,
				BD, kBlockedSeconds,
				bBlockedOk ? TEXT("STOPPED") : TEXT("PASSED-THROUGH")));
		}
		else
		{
			Out.Add(FString::Printf(
				TEXT("collisionBlockedStatus=NOTHING-MEASURED ")
				TEXT("collisionBlockedReason=teleported-but-the-blocked-walk-never-completed/%s"),
				*GFinishReason));
		}

		// THE COMBINED READING. Rule 5b: a guard proves nothing unless BOTH
		// the case it should pass and the case it should catch actually ran.
		const bool bClearOk = bClearWalked
			&& (double)FVector::Dist(GClearStartLoc, GClearEndLoc) > kStuckFloorCm;
		const bool bBothRan = bClearWalked && bTeleported && bBlockedWalked;
		Out.Add(FString::Printf(
			TEXT("collisionStatus=%s collisionStatusNote=needs-both-the-accepting-and-the-planted-case/rule-5b"),
			(bClearOk && bBlockedOk) ? TEXT("REAL")
				: (bBothRan ? TEXT("NOT-PROVEN") : TEXT("NOTHING-MEASURED"))));

		Out.Add(FString::Printf(
			TEXT("testCardsSpawned=%d/%d testCardsStatus=%s"),
			LedgerVignetteShot::ControlQuadsSpawnedCount(), LedgerSurface::ControlQuadCount(),
			LedgerVignetteShot::ControlQuadsSpawnedCount() == 0 ? TEXT("ABSENT") : TEXT("PRESENT")));

		Out.Add(FString::Printf(
			TEXT("walkFramesRequested=%d/%d walkFramesWrote=%d/%d"),
			GShotsAttempted, kTotalShots, GShotsWrote, kTotalShots));
		if (GShotLines.empty())
		{
			Out.Add(TEXT("NOTHING MEASURED - no frame reached the measuring step on this commit."));
		}
		else
		{
			for (const std::string& Line : GShotLines) { Out.Add(FString(UTF8_TO_TCHAR(Line.c_str()))); }
		}

		// THE GRATE'S THREE LINES: where the camera was put, where the two
		// rectangles landed, and whether the view target this phase borrowed
		// went back. Each one carries its own NOTHING-MEASURED reason when
		// the route never reached it, so an absent picture never reads as a
		// picture with nothing in it.
		Out.Add(GGrateLine);
		// THE SERIES, ONE LINE PER STANDPOINT ACTUALLY TRIED, IN THE ORDER
		// TRIED. No bound is read off it: the chosen row is simply the first
		// with five clear subject rays, and a row that was never reached
		// prints nothing rather than a zero, which is why the count of rows
		// is printed on the grate line above against kGrateStandCount.
		if (GGrateCandLines.Num() == 0)
		{
			Out.Add(FString::Printf(
				TEXT("grateCandStatus=NOTHING-MEASURED grateCandidatesTried=0/%d ")
				TEXT("grateCandReason=no-standpoint-was-traced-on-this-commit/nothing-measured"),
				kGrateStandCount));
		}
		else
		{
			for (const FString& CandLine : GGrateCandLines) { Out.Add(CandLine); }
		}
		Out.Add(GGrateRectLine);
		Out.Add(GGrateRestoreLine);

		// THE CLIP'S OWN INPUT. walkSeqFramesRequested is over kMaxSeqFrames
		// (16, a safety cap on a clock, named so it announces itself if it
		// ever bites); walkSeqFramesWrote is the OUT of those that actually
		// decoded and were not blank. Named ue-walkseq_NNN.png, collected by
		// the workflow step and handed to tools/clip-from-frames.py, which
		// is the only thing that turns them into the GIF; this file never
		// writes one.
		Out.Add(FString::Printf(
			TEXT("walkSeqFramesRequested=%d/%d walkSeqFramesWrote=%d/%d walkSeqIntervalSeconds=%.1f ")
			TEXT("walkSeqCeilingSeconds=%.1f walkSeqNamePrefix=ue-walkseq_"),
			GSeqRequested, kMaxSeqFrames, GSeqWrote, kMaxSeqFrames,
			kSeqInterval, kSeqFileCeiling));

		// SAME KEY THE BREADCRUMBS USE, so the workflow step's one reader can
		// take walkPhaseReached off either kind of file without a special
		// case for "the route actually finished".
		Out.Add(TEXT("walkPhaseReached=done"));
		Out.Add(TEXT("walkReached=end"));
		const FString Body = FString::Join(Out, TEXT("\n")) + TEXT("\n");
		FFileHelper::SaveStringToFile(Body, *AbsProject(TEXT("ue-walk-verdict.txt")));
		FFileHelper::SaveStringToFile(Body, *FPaths::Combine(
			FPaths::GetPath(FPlatformProcess::ExecutablePath()), TEXT("ue-walk-verdict.txt")));
	}

	void Finish()
	{
		GPhase = EWalkPhase::Done;
		WriteFinalVerdict();
		FPlatformMisc::RequestExit(false);
	}

	bool Tick(float)
	{
		++GTicks;
		const double Now = FPlatformTime::Seconds();
		if (GRouteStart == 0.0) { GRouteStart = Now; GPhaseStart = Now; }

		switch (GPhase)
		{
		case EWalkPhase::WaitWorld:
		{
			UWorld* World = GameWorld();
			if (World == nullptr && (Now - GPhaseStart) <= kWorldCeiling) { return true; }
			if (World == nullptr)
			{
				GFinishReason = TEXT("world-ceiling-bit-at-45s");
				Finish();
				return false;
			}
			WriteBreadcrumb(TEXT("world-found"));
			GPhase = EWalkPhase::WaitPawn;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::WaitPawn:
		{
			UWorld* World = GameWorld();
			APlayerController* PC = (World != nullptr) ? World->GetFirstPlayerController() : nullptr;
			APawn* P = (PC != nullptr) ? PC->GetPawn() : nullptr;
			if (P == nullptr && (Now - GPhaseStart) <= kPawnCeiling) { return true; }
			if (P == nullptr)
			{
				GFinishReason = TEXT("pawn-ceiling-bit-at-30s-no-player-controller-or-pawn");
				Finish();
				return false;
			}
			GPawn = P;
			bPawnFound = true;
			WriteBreadcrumb(TEXT("pawn-found"));
			GPhase = EWalkPhase::SettleAfterSpawn;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::SettleAfterSpawn:
		{
			if ((Now - GPhaseStart) < kSettleAfterSpawn) { return true; }
			// THE ACCEPTING CASE'S DIRECTION IS READ FROM THE PAWN, NEVER
			// ASSUMED. Whatever cam_A's yaw is on the day this runs, the
			// pawn was rotated to match it at spawn, and this is that
			// rotation's own forward vector.
			GClearDir = GPawn->GetActorForwardVector();
			GClearStartLoc = GPawn->GetActorLocation();
			GPhase = EWalkPhase::ShotStart;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::ShotStart:
			return RunShotPhase(TEXT("start"), TEXT("ue-walk_00_start.png"),
			                     EWalkPhase::ClearWalkA, Now);
		case EWalkPhase::ClearWalkA:
		{
			ApplyMovementAndMaybeCaptureSequence(GClearDir, Now);
			if ((Now - GPhaseStart) < kClearHalfSeconds) { return true; }
			GPhase = EWalkPhase::ShotMidClear;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::ShotMidClear:
			return RunShotPhase(TEXT("mid_clear"), TEXT("ue-walk_01_mid_clear.png"),
			                     EWalkPhase::ClearWalkB, Now);
		case EWalkPhase::ClearWalkB:
		{
			ApplyMovementAndMaybeCaptureSequence(GClearDir, Now);
			if ((Now - GPhaseStart) < kClearHalfSeconds) { return true; }
			GClearEndLoc = GPawn->GetActorLocation();
			bClearWalked = true;
			GPhase = EWalkPhase::ShotAfterClear;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::ShotAfterClear:
			return RunShotPhase(TEXT("after_clear"), TEXT("ue-walk_02_after_clear.png"),
			                     EWalkPhase::TeleportToWall, Now);
		case EWalkPhase::TeleportToWall:
		{
			WriteBreadcrumb(TEXT("clear-walk-done"));
			AActor* Wall = LedgerVignetteShot::FindStreetPiece(kWallName);
			if (Wall == nullptr)
			{
				GWallFound = false;
				GFinishReason = FString::Printf(
					TEXT("wall-actor-not-found-name=%s"), kWallName);
				Finish();
				return false;
			}
			GWallFound = true;
			// THE ENGINE'S OWN BOUNDS, MEASURED AFTER SCALE AND ROTATION,
			// NOT THE FILE'S NUMBERS A SECOND TIME (rule 4).
			const FBox WallBox = Wall->GetComponentsBoundingBox();
			const FVector Cur = GPawn->GetActorLocation();
			const double TargetY = (double)WallBox.Min.Y - kApproachClearanceCm;
			const double TargetX = (double)WallBox.GetCenter().X;
			const FVector Target((float)TargetX, (float)TargetY, Cur.Z + 30.0f);
			GPawn->TeleportTo(Target, GPawn->GetActorRotation(), false, true);
			GBlockedDir = FVector::RightVector;
			bTeleported = true;
			GPhase = EWalkPhase::SettleAfterTeleport;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::SettleAfterTeleport:
		{
			if ((Now - GPhaseStart) < kTeleportSettleSeconds) { return true; }
			GBlockedStartLoc = GPawn->GetActorLocation();
			GPhase = EWalkPhase::ShotBeforeBlocked;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::ShotBeforeBlocked:
			return RunShotPhase(TEXT("before_blocked"), TEXT("ue-walk_03_before_blocked.png"),
			                     EWalkPhase::BlockedWalk, Now);
		case EWalkPhase::BlockedWalk:
		{
			ApplyMovementAndMaybeCaptureSequence(GBlockedDir, Now);
			if ((Now - GPhaseStart) < kBlockedSeconds) { return true; }
			GBlockedEndLoc = GPawn->GetActorLocation();
			bBlockedWalked = true;
			GPhase = EWalkPhase::ShotAfterBlocked;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::ShotAfterBlocked:
			return RunShotPhase(TEXT("after_blocked"), TEXT("ue-walk_04_after_blocked.png"),
			                     EWalkPhase::AimGrate, Now);
		// ---- THE GRATE, LAST ON PURPOSE. Every collision and walk number
		// above is already measured and written by the time this runs, so a
		// camera this phase spawns, a view target it takes, or a crash inside
		// it cannot change any of them.
		case EWalkPhase::AimGrate:
		{
			WriteBreadcrumb(TEXT("blocked-walk-done"));
			AimAtGrate();
			// THE REFUSAL PATH, AND IT SKIPS BOTH GRATE FRAMES. Nothing was
			// spawned and no view target was taken on any path that leaves
			// bGrateShootable false, so jumping straight to Done cannot leave
			// the view on a probe camera; the two frames that were not taken
			// say why in the same place every other frame reports, so an
			// absent picture never reads as a picture with nothing in it.
			if (!bGrateShootable)
			{
				const std::string Why(TCHAR_TO_UTF8(*GGrateSkipWhy));
				GShotLines.push_back(
					"walkShot=grate_a shotStatus=NOT-TAKEN shotNote=" + Why);
				GShotLines.push_back(
					"walkShot=grate_b shotStatus=NOT-TAKEN shotNote=" + Why);
				GGrateRestoreLine = TEXT("grateViewRestoreStatus=NOT-NEEDED ")
				                    TEXT("grateViewRestoreReason=no-view-target-was-taken-because-")
				                    TEXT("the-shot-was-refused/nothing-to-restore");
				WriteBreadcrumb(TEXT("grate-refused"));
				GPhase = EWalkPhase::Done;
				GPhaseStart = Now;
				return true;
			}
			GPhase = EWalkPhase::SettleAfterAim;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::SettleAfterAim:
		{
			if ((Now - GPhaseStart) < kGrateSettleSeconds) { return true; }
			MeasureGrateAim();
			WriteBreadcrumb(TEXT("grate-aimed"));
			GPhase = EWalkPhase::ShotGrateA;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::ShotGrateA:
			return RunShotPhase(TEXT("grate_a"), TEXT("ue-walk_05_grate_a.png"),
			                     EWalkPhase::ShotGrateB, Now);
		// THE SAME CAMERA, NOT MOVED BETWEEN THE TWO. This is the pair
		// tools/grate-zfight.py reads its flicker density from; if anything
		// ever moves the camera between these two phases, the flicker half of
		// that instrument stops measuring z-fighting and starts measuring the
		// move, and the grateCamRead numbers on the rect line are what would
		// show it.
		case EWalkPhase::ShotGrateB:
			return RunShotPhase(TEXT("grate_b"), TEXT("ue-walk_06_grate_b.png"),
			                     EWalkPhase::RestoreView, Now);
		case EWalkPhase::RestoreView:
		{
			RestoreViewTarget();
			GPhase = EWalkPhase::ConfirmRestore;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::ConfirmRestore:
		{
			ConfirmViewRestore();
			GPhase = EWalkPhase::Done;
			GPhaseStart = Now;
			return true;
		}
		case EWalkPhase::Done:
		default:
			Finish();
			return false;
		}
	}
}

namespace LedgerWalkProbe
{
	void Start()
	{
		WriteBreadcrumb(TEXT("start-called"));
		GTicker = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&Tick), 0.0f);
	}
}
