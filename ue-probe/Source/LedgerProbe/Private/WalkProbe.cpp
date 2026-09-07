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
// THE CLIP. Unreal's own Movie Render Pipeline needs a Level Sequence asset
// and this project ships no content directory by design (see
// VignetteShot.cpp); wiring it in for one probe would be a new asset type
// and a new plugin dependency, neither verifiable until the next Windows
// build, so this file does not use it. This file writes FRAMES ONLY, in two
// kinds: five named milestones (ue-walk_NN_*.png, the evidence) and a
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
	const int32  kTotalShots = 5;

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
		BlockedWalk, ShotAfterBlocked, Done
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
		Out.Add(TEXT("# THE CLIP: this file writes two kinds of frame. ue-walk_NN_*.png is the"));
		Out.Add(TEXT("#   evidence, five named milestones, untouched by the clip. ue-walkseq_NNN.png"));
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
			                     EWalkPhase::Done, Now);
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
