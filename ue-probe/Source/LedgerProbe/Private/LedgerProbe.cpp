// The game module, and the golden test that runs inside it.
//
// A Game target's binary is a game, so the test cannot be a main(). It runs
// at module startup, writes its result to a file the CI step reads, and asks
// the engine to quit. Headless: the workflow passes -nullrhi -unattended
// -nosplash, so nothing opens a window on Jafar's machine.
//
// THE RESULT GOES TO A FILE, NOT TO THE LOG. UE's log is noisy, interleaved
// and truncated by the harness that reads it; a file the step opens by name
// is the same evidence-channel rule the rest of this project runs on, and it
// is why the sim's verdict is a file rather than a log tail.
#include "LedgerProbe.h"
#include "Perception.h"
#include "FrameStats.h"
#include "VignetteShot.h"

#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformProcess.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/DateTime.h"
#include "Containers/Ticker.h"
#include "UnrealClient.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"

// THE STILL'S DEPENDENCIES, AND EVERY ONE OF THEM IS A COST ON THE CYCLE
// THIS PROBE EXISTS TO MEASURE. Engine, World and PlayerController are the
// world and the view; CameraActor is the placed camera of step 3;
// DrawDebugHelpers is the only way to put known colour into a frame in a
// project that deliberately has no Content directory; the two ImageWrapper
// headers decode the PNG this run is about to commit, because a file-exists
// check is not a measurement.
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraActor.h"
#include "DrawDebugHelpers.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"
#include "Modules/ModuleManager.h"

#include <cmath>
#include <cstdlib>
#include <string>
#include <vector>

using namespace LedgerCore;

namespace
{
	std::vector<FString> SplitPipe(const FString& Line)
	{
		TArray<FString> Parts;
		Line.ParseIntoArray(Parts, TEXT("|"), false);
		std::vector<FString> Out;
		for (const FString& P : Parts) Out.push_back(P);
		return Out;
	}

	double D(const FString& S) { return FCString::Atod(*S); }
	bool   B(const FString& S) { return S == TEXT("1"); }

	// THE TABLE IS LOOKED FOR IN SEVERAL PLACES AND THE ONE USED IS NAMED.
	// A packaged build's ProjectDir is the STAGED project, not the source
	// tree, so a single hard-coded location works in exactly one of the two
	// ways this binary gets run. Searching is fine; searching silently is
	// not, which is why the result file says which path answered.
	FString FindGoldenTable(FString& OutTried)
	{
		TArray<FString> Candidates;
		Candidates.Add(FPaths::Combine(FPaths::ProjectDir(), TEXT("perception-golden.txt")));
		Candidates.Add(FPaths::Combine(FPaths::ProjectContentDir(), TEXT("perception-golden.txt")));
		Candidates.Add(FPaths::Combine(FPaths::LaunchDir(), TEXT("perception-golden.txt")));
		Candidates.Add(FPaths::Combine(
			FPaths::GetPath(FPlatformProcess::ExecutablePath()), TEXT("perception-golden.txt")));
		for (const FString& C : Candidates)
		{
			OutTried += TEXT(" ") + FPaths::ConvertRelativePathToFull(C).Replace(TEXT(" "), TEXT("~"));
			if (FPaths::FileExists(C)) { return C; }
		}
		return FString();
	}

	// THE EVIDENCE CHANNEL, REPRODUCED ON THE UE SIDE. Task 007, step 1.
	//
	// This is the question D1 actually turns on, and it is not a performance
	// question. Unity's loop costs what it costs partly because the answer
	// has to travel through CI to be readable at all; if UE cannot produce
	// the same committed, traceable file, then D1 is comparing an
	// instrumented engine against an uninstrumented one and the comparison
	// is worthless whichever way it lands.
	//
	// FOUR PROPERTIES HAVE TO SURVIVE THE MOVE and each one is here because
	// breaking it cost this project a day:
	//   line 1 names the commit, so a stale file cannot pass as a fresh one;
	//   no value contains a space, because every reader splits on whitespace
	//     and truncates silently when one does;
	//   whole-run numbers sit on the done line, never split across lines a
	//     grep would merge;
	//   a run that measured nothing says so rather than staying quiet.
	//
	// The commit comes in on the command line rather than being discovered,
	// because a game binary has no business running git and a sha it guessed
	// would be a provenance line with no provenance.
	void WriteVerdict(long Rows, long Bad, long Unknown, const FString& GoldenUsed, double Tol)
	{
		FString Sha;
		if (!FParse::Value(FCommandLine::Get(), TEXT("LedgerCommit="), Sha) || Sha.IsEmpty())
		{
			Sha = TEXT("SHA-UNKNOWN");
		}
		Sha = Sha.Replace(TEXT(" "), TEXT("~"));

		const FString Path = FPaths::Combine(FPaths::ProjectDir(), TEXT("ue-verdict.txt"));
		TArray<FString> Out;
		Out.Add(FString::Printf(TEXT("# UE probe verdict %s @%lld"),
		                        *Sha, (long long)FDateTime::UtcNow().ToUnixTimestamp()));
		Out.Add(TEXT("# Line 1 names the commit this was measured on, as the Unity verdict does."));
		Out.Add(TEXT(""));

		if (Rows == 0)
		{
			// NO RUN, said in words. A run that measured nothing must not
			// leave a file that reads like a clean one.
			Out.Add(TEXT("NO RUN - the golden table was empty or unreadable, so nothing was measured on this commit."));
		}
		else
		{
			// The done line: whole-run numbers only, no spaces in any value.
			Out.Add(FString::Printf(
				TEXT("perceptionRows=%ld perceptionMismatches=%ld perceptionUnknownFns=%ld ")
				TEXT("perceptionTolerance=%g probeTest=%s goldenTable=%s"),
				Rows, Bad, Unknown, Tol,
				Bad == 0 ? TEXT("PASS") : TEXT("FAIL"),
				GoldenUsed.IsEmpty() ? TEXT("NONE-FOUND")
				                     : *FPaths::GetCleanFilename(GoldenUsed)));
		}
		Out.Add(TEXT("verdictReached=end"));
		FFileHelper::SaveStringToFile(FString::Join(Out, TEXT("\n")) + TEXT("\n"), *Path);
	}

	// TASK 007 STEPS 2 AND 3: ONE STILL, OFFSCREEN, MEASURED IN PIXELS.
	//
	// THE DELIVERABLE IS THE CHANNEL, NOT A PRETTY FRAME. A grey box
	// photographed correctly, with provenance and a number, beats a
	// good-looking screenshot nothing can trace.
	//
	// IT IS -RenderOffScreen AND NOT -nullrhi, WHICH ARE OPPOSITE THINGS.
	// nullrhi means no rendering at all, which is correct for the golden
	// test above and useless here; RenderOffScreen renders with no window.
	// Getting that backwards looks like success and produces nothing, or
	// produces a black frame that a file-exists check calls a pass. The two
	// are separate invocations on purpose, each with its own switch, so the
	// golden path that already works cannot be disturbed by the half that
	// is still being proved.
	//
	// A FILE-EXISTS CHECK IS NOT A MEASUREMENT, so this decodes the PNG it
	// is about to commit and prints statistics over its pixels. A blank or
	// uniform frame reports shotStatus=BLANK and the step that runs it
	// exits non-zero. What each number is a statistic OF is written beside
	// the emit and repeated as a comment line in the verdict itself.
	//
	// THIS CANNOT RUN AT MODULE STARTUP AND THAT IS THE WHOLE DESIGN. The
	// golden test writes a file and quits because it touches nothing but
	// arithmetic. A screenshot needs a world, a view and rendered frames,
	// so this is a small state machine on the core ticker: wait for a
	// world, place a camera and draw something with known colour into it,
	// let the renderer settle, ask, wait, measure, exit. Every phase has a
	// wall-clock ceiling and every ceiling that bites is named in the
	// verdict rather than reported as a generic failure.
	enum class EShotPhase : uint8
	{
		WaitWorld,
		Settle,
		WaitFileA,
		WaitFileB,
		Finished
	};

	FTSTicker::FDelegateHandle GShotTicker;
	EShotPhase GShotPhase   = EShotPhase::WaitWorld;
	int32      GShotTicks   = 0;      // cumulative ticker calls since startup
	double     GShotStart   = 0.0;    // seconds, when the ticker was armed
	double     GPhaseStart  = 0.0;    // seconds, when the current phase began
	FString    GShotAsked;            // absolute path handed to the engine
	FString    GShotCamLine = TEXT("shotCamPlaced=NOT-REACHED");
	FString    GShotAttempt = TEXT("NONE");
	FString    GShotNote    = TEXT("none");
	int64      GSizeAskedPath = -1;   // last polled size of the requested path
	int64      GSizeFoundPath = -1;   // last polled size of whatever was found

	// Ceilings, in seconds, on a hang. Not targets, and each one prints the
	// phase it killed so a slow world and a world that never came cannot
	// read alike.
	const double kWorldCeiling  = 45.0;
	const double kSettleSeconds = 2.0;
	const double kFileCeiling   = 25.0;

	// A FILE THAT EXISTS IS NOT A FILE THAT IS FINISHED. The engine writes
	// the PNG on the game thread between two of these ticks, so a poll can
	// land on a half-written file and the decode would then report
	// UNDECODABLE for a screenshot that was perfectly fine a millisecond
	// later. Two consecutive polls agreeing on a non-zero size is the cheap
	// version of waiting for the writer, and it costs one frame.
	bool SizeSettled(const FString& Path, int64& Tracker)
	{
		const int64 Size = IFileManager::Get().FileSize(*Path);
		if (Size <= 0) { Tracker = -1; return false; }
		const bool bSame = (Size == Tracker);
		Tracker = Size;
		return bSame;
	}

	FString AbsProject(const TCHAR* Leaf)
	{
		return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), Leaf));
	}

	FString NoSpaces(const FString& In) { return In.Replace(TEXT(" "), TEXT("~")); }

	FString ShotSha()
	{
		FString Sha;
		if (!FParse::Value(FCommandLine::Get(), TEXT("LedgerCommit="), Sha) || Sha.IsEmpty())
		{
			Sha = TEXT("SHA-UNKNOWN");
		}
		return NoSpaces(Sha);
	}

	// THE GAME WORLD, ASKED FOR RATHER THAN ASSUMED. GWorld would do today
	// and is a guess about tomorrow; a world context of type Game is the
	// thing actually being looked for and the loop says so.
	UWorld* GameWorld()
	{
		if (!GEngine) { return nullptr; }
		for (const FWorldContext& Ctx : GEngine->GetWorldContexts())
		{
			if (Ctx.WorldType == EWorldType::Game && Ctx.World() != nullptr)
			{
				return Ctx.World();
			}
		}
		return nullptr;
	}

	// THE VERDICT. Same four properties as the golden one: line 1 names the
	// commit, no value carries a space, whole-run numbers sit on one line,
	// and a run that measured nothing says the words.
	void WriteShotVerdict(const FString& DoneLine, const FString& Art)
	{
		TArray<FString> Out;
		Out.Add(FString::Printf(TEXT("# UE probe shot %s @%lld"),
		                        *ShotSha(), (long long)FDateTime::UtcNow().ToUnixTimestamp()));
		Out.Add(TEXT("# Line 1 names the commit this was measured on, as the Unity verdict does."));
		Out.Add(TEXT("# shotMeanLuma: mean over EVERY pixel of the committed file, 0 to 1,"));
		Out.Add(TEXT("#   luma=(0.299R+0.587G+0.114B)/255, the same weights the Unity sim uses."));
		Out.Add(TEXT("# shotMinLuma/shotMaxLuma: extremes over the same pixel set."));
		Out.Add(TEXT("# shotNonBlackPct: percent of shotPixels with any channel above zero."));
		Out.Add(TEXT("# shotDistinctBuckets: distinct 5-bit-per-channel colour buckets, of 32768."));
		Out.Add(TEXT("# A shot status of WROTE needs a decoded file with more than one bucket"));
		Out.Add(TEXT("#   and at least one non-black pixel. Anything else is BLANK, UNDECODABLE"));
		Out.Add(TEXT("#   or NO-FILE, and the step that ran this exits non-zero for all three."));
		Out.Add(TEXT("# NO COMMENT IN THIS HEADER WRITES A KEY WITH AN EQUALS AND A VALUE."));
		Out.Add(TEXT("#   This explanation used to spell the key out in full with WROTE beside"));
		Out.Add(TEXT("#   it, and the step that gates on this file takes the FIRST match for"));
		Out.Add(TEXT("#   that key: the gate read WROTE out of the explanation, above the"));
		Out.Add(TEXT("#   measured line, and could not have failed whatever the frame was."));
		Out.Add(TEXT("#   Keys are named in prose here and measured below, never both."));
		Out.Add(TEXT(""));
		Out.Add(GShotCamLine);
		Out.Add(DoneLine);
		if (!Art.IsEmpty())
		{
			Out.Add(TEXT("# ascii-luma of the committed frame, 48x27 cells, top row first."));
			Out.Add(Art);
		}
		Out.Add(TEXT("shotReached=end"));
		const FString Body = FString::Join(Out, TEXT("\n")) + TEXT("\n");

		// WRITTEN WHERE BOTH KINDS OF RUN CAN BE FOUND. A packaged build's
		// ProjectDir is the staged tree; the step looks in both and says
		// which answered, exactly as the golden result is collected.
		FFileHelper::SaveStringToFile(Body, *AbsProject(TEXT("ue-shot-verdict.txt")));
		const FString BesideExe = FPaths::Combine(
			FPaths::GetPath(FPlatformProcess::ExecutablePath()), TEXT("ue-shot-verdict.txt"));
		FFileHelper::SaveStringToFile(Body, *BesideExe);
	}

	void FinishShot(const FString& DoneLine, const FString& Art)
	{
		GShotPhase = EShotPhase::Finished;
		WriteShotVerdict(DoneLine, Art);
		FPlatformMisc::RequestExit(false);
	}

	// DECODE THE FILE THAT IS ABOUT TO BE COMMITTED, not the buffer the
	// engine had in memory. OnScreenshotCaptured would hand over the pixels
	// directly and would also SUPPRESS the engine's own file write, which
	// would leave a measurement with no artifact beside it. Reading the
	// artifact back is rule 4 and it makes the two the same thing.
	bool DecodeBgra(const FString& PngPath, TArray64<uint8>& OutBgra, int32& OutW, int32& OutH)
	{
		TArray<uint8> Compressed;
		if (!FFileHelper::LoadFileToArray(Compressed, *PngPath) || Compressed.Num() == 0)
		{
			// EVERY REFUSAL NAMES ITSELF. A note left at its default would
			// make "the file would not open" and "the decoder said no" the
			// same sentence in the verdict, and they have different fixes.
			GShotNote = TEXT("file-would-not-load-or-was-empty");
			return false;
		}
		IImageWrapperModule* Mod =
			FModuleManager::Get().LoadModulePtr<IImageWrapperModule>(FName("ImageWrapper"));
		if (Mod == nullptr) { GShotNote = TEXT("imagewrapper-module-missing"); return false; }
		TSharedPtr<IImageWrapper> Wrapper = Mod->CreateImageWrapper(EImageFormat::PNG);
		if (!Wrapper.IsValid()) { GShotNote = TEXT("no-png-wrapper"); return false; }
		if (!Wrapper->SetCompressed(Compressed.GetData(), (int64)Compressed.Num()))
		{
			GShotNote = TEXT("setcompressed-refused-the-bytes");
			return false;
		}
		OutW = Wrapper->GetWidth();
		OutH = Wrapper->GetHeight();
		if (OutW <= 0 || OutH <= 0) { GShotNote = TEXT("decoded-size-was-zero"); return false; }
		if (!Wrapper->GetRaw(ERGBFormat::BGRA, 8, OutBgra))
		{
			GShotNote = TEXT("getraw-refused");
			return false;
		}
		return OutBgra.Num() >= (int64)OutW * (int64)OutH * 4;
	}

	// MEASURE, THEN JUDGE, AND THE MATHS IS NOT WRITTEN HERE.
	//
	// Every number and every character of the done line comes from
	// FrameStats.h, which has no Unreal type in it and is compiled and RUN
	// by ue-probe/tests/frame-stats-test.cpp with g++ before any dispatch.
	// This layer supplies pixels and live state and nothing else, which is
	// the standing rule for a project whose top layer does not compile
	// locally: a formatter that ships unrun and prints a plausible string is
	// the silent-instrument failure, and the blank guard is a formatter with
	// a verdict attached.
	//
	// The series is printed whatever the verdict says, because the next
	// bound anybody sets on frame content has to come from real runs.
	void MeasureAndFinish(const FString& PngPath, double WaitedSeconds)
	{
		const int64 Bytes = IFileManager::Get().FileSize(*PngPath);
		const std::string Attempt(TCHAR_TO_UTF8(*GShotAttempt));
		const std::string File(TCHAR_TO_UTF8(*NoSpaces(FPaths::GetCleanFilename(PngPath))));
		TArray64<uint8> Bgra;
		int32 W = 0, H = 0;
		if (!DecodeBgra(PngPath, Bgra, W, H))
		{
			// A FILE THAT WILL NOT DECODE IS NOT A FRAME, and it is a
			// different fact from no file at all, so it gets its own status
			// rather than being folded into either neighbour.
			FinishShot(FString::Printf(
				TEXT("shotStatus=UNDECODABLE shotAttempt=%s shotFile=%s shotBytes=%lld ")
				TEXT("shotPixels=0 shotSecondsWaited=%.2f shotTicks=%d shotNote=%s"),
				*GShotAttempt, *NoSpaces(FPaths::GetCleanFilename(PngPath)),
				(long long)Bytes, WaitedSeconds, GShotTicks, *GShotNote),
				FString());
			return;
		}

		const LedgerFrame::FrameStats Stats =
			LedgerFrame::Measure((const unsigned char*)Bgra.GetData(), W, H);
		const std::string Done = LedgerFrame::DoneLine(
			Stats, Attempt, File, (long long)Bytes, WaitedSeconds, GShotTicks,
			std::string(TCHAR_TO_UTF8(*GShotNote)));
		const std::string Art = LedgerFrame::AsciiLuma((const unsigned char*)Bgra.GetData(), W, H);

		// ONE NAME FOR THE FILE THE STEP COLLECTS, whatever produced it.
		// HighResShot picks its own path under Saved/Screenshots and
		// RequestScreenshot writes where it was told; the step should not
		// have to know which won, so the winner is copied to the fixed name
		// and the verdict says where it came from.
		const FString Fixed = AbsProject(TEXT("ue-shot.png"));
		if (PngPath != Fixed)
		{
			IFileManager::Get().Copy(*Fixed, *PngPath, true, true);
		}
		FinishShot(FString(UTF8_TO_TCHAR(Done.c_str())), FString(UTF8_TO_TCHAR(Art.c_str())));
	}

	// THE NEWEST PNG UNDER A DIRECTORY, NAMED. HighResShot chooses its own
	// filename, so the file has to be found rather than assumed, and an
	// unordered pick would let an older screenshot from a previous run pass
	// as this one. The project's Saved tree is cleared by the workflow
	// before the run, and this takes the newest regardless.
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

	// SOMETHING TO PHOTOGRAPH, BUILT FROM CODE AND NO ASSETS. The probe
	// project has no Content directory by design, so the frame's contents
	// cannot come from a mesh. Two independent paths put known colour into
	// the frame: debug geometry, which travels through the scene renderer,
	// and on-screen debug messages, which travel through the viewport
	// canvas. If one of them turns out not to reach an offscreen frame the
	// other still does, and one round trip learns which.
	void PlaceCameraAndDrawContent(UWorld* World)
	{
		if (World == nullptr)
		{
			GShotCamLine = TEXT("shotCamPlaced=NO-WORLD shotCamReason=no-game-world-context-appeared");
			return;
		}
		APlayerController* PC = World->GetFirstPlayerController();
		if (PC == nullptr)
		{
			GShotCamLine = TEXT("shotCamPlaced=NO-PC shotCamReason=world-without-a-player-controller");
		}
		else
		{
			// TASK 007 STEP 3: A PLACED CAMERA, AND THE PLACEMENT IS READ
			// BACK. Asking for a transform and printing the transform you
			// asked for is not evidence that anything moved. The view point
			// is read from the controller AFTER the switch and both are
			// printed with the distance between them.
			const FVector  Want(0.0, 0.0, 180.0);
			const FRotator WantRot(-10.0, 0.0, 0.0);
			ACameraActor* Cam = World->SpawnActor<ACameraActor>(
				ACameraActor::StaticClass(), Want, WantRot);
			if (Cam != nullptr)
			{
				PC->SetViewTarget(Cam);
			}
			FVector  GotLoc = FVector::ZeroVector;
			FRotator GotRot = FRotator::ZeroRotator;
			PC->GetPlayerViewPoint(GotLoc, GotRot);
			GShotCamLine = FString::Printf(
				TEXT("shotCamPlaced=%s shotCamAskedXYZ=%.1f/%.1f/%.1f shotCamReadXYZ=%.1f/%.1f/%.1f ")
				TEXT("shotCamDeltaCm=%.2f shotCamAskedPitchYaw=%.1f/%.1f shotCamReadPitchYaw=%.1f/%.1f ")
				TEXT("shotWorld=%s"),
				Cam != nullptr ? TEXT("yes") : TEXT("SPAWN-FAILED"),
				Want.X, Want.Y, Want.Z, GotLoc.X, GotLoc.Y, GotLoc.Z,
				FVector::Dist(Want, GotLoc), WantRot.Pitch, WantRot.Yaw,
				GotRot.Pitch, GotRot.Yaw, *NoSpaces(World->GetMapName()));
		}

		// A CROSS, A BOX AND A GRID IN FRONT OF THE VIEW, in colours nothing
		// else in an empty map produces. Persistent, so they survive every
		// frame between here and the capture.
		const FVector Eye(0.0, 0.0, 180.0);
		const FVector Centre = Eye + FVector(600.0, 0.0, -40.0);
		DrawDebugBox(World, Centre, FVector(120.0, 120.0, 120.0), FColor(255, 80, 40), true, -1.0f, 0, 12.0f);
		DrawDebugLine(World, Centre + FVector(0, -400, -160), Centre + FVector(0, 400, -160),
		              FColor(60, 220, 255), true, -1.0f, 0, 14.0f);
		DrawDebugLine(World, Centre + FVector(0, 0, -300), Centre + FVector(0, 0, 300),
		              FColor(255, 240, 60), true, -1.0f, 0, 14.0f);
		for (int32 I = -4; I <= 4; ++I)
		{
			DrawDebugLine(World, Eye + FVector(200, I * 120.0, -160), Eye + FVector(1600, I * 120.0, -160),
			              FColor(90, 200, 90), true, -1.0f, 0, 6.0f);
			DrawDebugLine(World, Eye + FVector(200 + (I + 4) * 175.0, -480, -160),
			              Eye + FVector(200 + (I + 4) * 175.0, 480, -160),
			              FColor(90, 200, 90), true, -1.0f, 0, 6.0f);
		}

		// The canvas path. Twenty lines rather than one so that a frame
		// carrying only this still has pixels to count.
		if (GEngine != nullptr)
		{
			GEngine->bEnableOnScreenDebugMessages = true;
			for (int32 I = 0; I < 20; ++I)
			{
				GEngine->AddOnScreenDebugMessage(
					(uint64)(1000 + I), 300.0f, FColor(255, 255, 0),
					FString::Printf(TEXT("LEDGER D1 UE PROBE SHOT %s LINE %02d"), *ShotSha(), I));
			}
		}
	}

	bool ShotTick(float)
	{
		++GShotTicks;
		const double Now = FPlatformTime::Seconds();
		if (GShotStart == 0.0) { GShotStart = Now; GPhaseStart = Now; }

		switch (GShotPhase)
		{
		case EShotPhase::WaitWorld:
		{
			UWorld* World = GameWorld();
			const bool bTimedOut = (Now - GPhaseStart) > kWorldCeiling;
			if (World == nullptr && !bTimedOut) { return true; }
			// A WORLD THAT NEVER CAME IS NOT A REASON TO SKIP THE CAPTURE.
			// The question this run exists to answer is whether a still can
			// be taken and committed at all; a black frame with a named
			// reason is a finding, a run that stopped early is not.
			if (World == nullptr) { GShotNote = TEXT("world-ceiling-bit-at-45s"); }
			PlaceCameraAndDrawContent(World);
			GShotPhase = EShotPhase::Settle;
			GPhaseStart = Now;
			return true;
		}
		case EShotPhase::Settle:
		{
			if ((Now - GPhaseStart) < kSettleSeconds || GShotTicks < 10) { return true; }
			GShotAsked = AbsProject(TEXT("ue-shot.png"));
			IFileManager::Get().Delete(*GShotAsked, false, true, true);
			// ATTEMPT A: FScreenshotRequest, the first of the two candidates
			// the spec named. bShowUI is false: the viewport read includes
			// the scene and the debug canvas, which is everything drawn
			// above, and the Slate path is the one with more moving parts.
			// AN ABSOLUTE PATH ON PURPOSE: a relative one is resolved
			// against the engine's screenshot directory, which would put the
			// file somewhere the step is not looking and read as no file.
			FScreenshotRequest::RequestScreenshot(GShotAsked, false, false);
			GShotAttempt = TEXT("FScreenshotRequest::RequestScreenshot");
			GShotPhase = EShotPhase::WaitFileA;
			GPhaseStart = Now;
			return true;
		}
		case EShotPhase::WaitFileA:
		{
			if (SizeSettled(GShotAsked, GSizeAskedPath))
			{
				MeasureAndFinish(GShotAsked, Now - GShotStart);
				return false;
			}
			if ((Now - GPhaseStart) < kFileCeiling) { return true; }
			// ATTEMPT B: the other candidate. Both are documented, neither
			// had ever been run here, and the spec says the first build to
			// try must print which one it used and whether a file appeared.
			// Running both in one dispatch answers that in one round trip
			// instead of two.
			GShotNote = TEXT("requestScreenshot-wrote-nothing-in-25s");
			UWorld* ExecWorld = GameWorld();
			if (GEngine != nullptr && ExecWorld != nullptr)
			{
				GEngine->Exec(ExecWorld, TEXT("HighResShot 960x540"));
				GShotAttempt = TEXT("HighResShot");
			}
			else
			{
				// A SECOND CANDIDATE THAT COULD NOT BE TRIED IS NOT A
				// CANDIDATE THAT FAILED, and the two must not read alike.
				GShotAttempt = TEXT("HighResShot-NOT-TRIED-no-world");
			}
			GShotPhase = EShotPhase::WaitFileB;
			GPhaseStart = Now;
			return true;
		}
		case EShotPhase::WaitFileB:
		{
			// THE FIRST CANDIDATE IS STILL CHECKED HERE. A slow write that
			// landed just after its ceiling bit would otherwise be reported
			// as no file at all while the file sat on disk, which is the
			// instrument lying about the thing it is watching.
			if (SizeSettled(GShotAsked, GSizeAskedPath))
			{
				GShotAttempt = TEXT("FScreenshotRequest::RequestScreenshot-late");
				MeasureAndFinish(GShotAsked, Now - GShotStart);
				return false;
			}
			int32 Count = 0;
			const FString Newest = NewestPngUnder(
				FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()), Count);
			if (!Newest.IsEmpty() && SizeSettled(Newest, GSizeFoundPath))
			{
				MeasureAndFinish(Newest, Now - GShotStart);
				return false;
			}
			if ((Now - GPhaseStart) < kFileCeiling) { return true; }
			// NOTHING MEASURED, IN WORDS, WITH THE DENOMINATOR OF THE SEARCH:
			// two named places were looked in and this is how many PNGs the
			// recursive one held.
			FinishShot(FString::Printf(
				TEXT("shotStatus=NO-FILE shotAttempt=%s shotPlacesSearched=2 shotPngsUnderSaved=%d ")
				TEXT("shotPixels=0 shotSecondsWaited=%.2f shotTicks=%d ")
				TEXT("shotNote=nothing-measured-neither-candidate-wrote-a-file"),
				*GShotAttempt, Count, Now - GShotStart, GShotTicks),
				FString());
			return false;
		}
		default:
			return false;
		}
	}

	void StartShot()
	{
		GShotTicker = FTSTicker::GetCoreTicker().AddTicker(
			FTickerDelegate::CreateStatic(&ShotTick), 0.0f);
	}

	void RunGoldenTest()
	{
		FString Tried;
		const FString Found      = FindGoldenTable(Tried);
		const FString GoldenPath = Found.IsEmpty()
			? FPaths::Combine(FPaths::ProjectDir(), TEXT("perception-golden.txt")) : Found;
		const FString OutPath    = FPaths::Combine(FPaths::ProjectDir(), TEXT("golden-result.txt"));

		// A BREADCRUMB, WRITTEN BEFORE ANY WORK. Run 6 exited 3 in six seconds
		// with no file at all, and "the module never loaded" and "the module
		// loaded and the test died" looked identical from the outside. They
		// have completely different next actions. This costs one write and
		// makes them distinguishable: no file means startup was never reached,
		// a file holding only this line means it was reached and the test
		// did not finish.
		FFileHelper::SaveStringToFile(
			FString::Printf(TEXT("moduleStartup=reached projectDir=%s goldenPath=%s\ngoldenTried:%s\nprobeTest=FAIL reason=test-did-not-finish\n"),
			                *FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()).Replace(TEXT(" "), TEXT("~")),
			                Found.IsEmpty() ? TEXT("NONE-FOUND")
			                                : *FPaths::ConvertRelativePathToFull(Found).Replace(TEXT(" "), TEXT("~")),
			                *Tried),
			*OutPath);

		FString Contents;
		if (!FFileHelper::LoadFileToString(Contents, *GoldenPath))
		{
			FFileHelper::SaveStringToFile(
				FString::Printf(TEXT("perceptionGolden=UNREADABLE path=%s\nprobeTest=FAIL reason=golden-table-not-found\n"), *GoldenPath),
				*OutPath);
			return;
		}

		TArray<FString> Lines;
		Contents.ParseIntoArrayLines(Lines);

		long Rows = 0, Bad = 0, Unknown = 0;
		const double Tol = 1e-9;
		FString Detail;

		for (const FString& Line : Lines)
		{
			if (Line.IsEmpty() || Line.StartsWith(TEXT("#"))) continue;
			const std::vector<FString> F = SplitPipe(Line);
			if (F.size() < 3) continue;
			++Rows;
			const FString& Fn = F[0];
			double Got = 0.0, Want = 0.0;

			if (Fn == TEXT("MotionFactor"))             { Got = Perception::MotionFactor(D(F[1])); Want = D(F[2]); }
			else if (Fn == TEXT("ConeWeight"))          { Got = Perception::ConeWeight(D(F[1]));   Want = D(F[2]); }
			else if (Fn == TEXT("LightFactor"))         { Got = Perception::LightFactor(D(F[1]));  Want = D(F[2]); }
			else if (Fn == TEXT("FacingIsReadable"))    { Got = Perception::FacingIsReadable(D(F[1]), D(F[2])) ? 1 : 0; Want = D(F[3]); }
			else if (Fn == TEXT("InSight"))             { Got = Perception::InSight(D(F[1]), D(F[2]), D(F[3]), B(F[4]), D(F[5])) ? 1 : 0; Want = D(F[6]); }
			else if (Fn == TEXT("IdRung"))              { Got = Perception::IdRung(D(F[1]), D(F[2]), D(F[3]), B(F[4]), B(F[5])); Want = D(F[6]); }
			else if (Fn == TEXT("SymmetryPredictsSeen")){ Got = Perception::SymmetryPredictsSeen(D(F[1]), D(F[2]), D(F[3]), D(F[4]), B(F[5])) ? 1 : 0; Want = D(F[6]); }
			else { ++Unknown; --Rows; continue; }

			if (FMath::Abs(Got - Want) > Tol)
			{
				++Bad;
				if (Bad <= 10)
				{
					Detail += FString::Printf(TEXT("  MISMATCH %s got=%.17g want=%.17g <- %s\n"), *Fn, Got, Want, *Line);
				}
			}
		}

		WriteVerdict(Rows, Bad, Unknown, Found, Tol);

		FString Result;
		// A GOLDEN FILE THAT LOADED NOTHING MUST NOT READ AS AGREEMENT.
		if (Rows == 0)
		{
			Result = FString::Printf(TEXT("perceptionGolden=0 rows read from %s\nprobeTest=FAIL reason=golden-table-empty\n"), *GoldenPath);
		}
		else
		{
			Result = Detail;
			if (Unknown > 0)
			{
				Result += FString::Printf(TEXT("  note: %ld row(s) named a function this build does not implement\n"), Unknown);
			}
			Result += FString::Printf(TEXT("perceptionRows=%ld perceptionMismatches=%ld tolerance=%g\n"), Rows, Bad, Tol);
			Result += FString::Printf(TEXT("probeTest=%s\n"), Bad == 0 ? TEXT("PASS") : TEXT("FAIL"));
		}
		FFileHelper::SaveStringToFile(Result, *OutPath);
	}

}

// THE MODULE CLASS SITS OUTSIDE THE ANONYMOUS NAMESPACE ON PURPOSE.
// IMPLEMENT_PRIMARY_GAME_MODULE expands to code that names this type at file
// scope; an internal-linkage class would probably still resolve, and
// "probably" is not worth a 25-minute round trip to find out.
class FLedgerProbeModule : public FDefaultGameModuleImpl
{
public:
	virtual void StartupModule() override
	{
		// THE TEST RUNS ONLY WHEN ASKED, AND THAT IS NOT FUSSINESS.
		//
		// Moving this module to PostConfigInit made the golden test work in
		// the game and simultaneously broke the cook, because a module loads
		// in EVERY host that loads it, and one of those hosts is the cook
		// commandlet's editor. So the cook started, loaded this module, ran
		// the test, and was told to quit before it had cooked anything.
		// The failure read as "cooking was unsuccessful", which was true and
		// gave no hint that the saboteur was the test.
		//
		// A switch the workflow passes only for the game run separates them
		// with no guessing about which host we are in. IsRunningCommandlet
		// would also work today and would be a guess about tomorrow.
		// TWO INVOCATIONS, TWO SWITCHES, AND NEITHER IS THE DEFAULT. A
		// module with no switch does nothing at all, which is what the cook
		// commandlet needs from it.
		// PHASE B, AND IT IS ITS OWN SWITCH FOR THE SAME REASON THE OTHER
		// TWO ARE. -LedgerShot photographs debug geometry in an empty map,
		// which is the capture path's own accepting case, and it stays
		// because it is the fastest way to separate "the capture path is
		// broken" from "the street would not build". -LedgerVignette builds
		// the shared street from the shared JSON and photographs it four
		// times. Neither is the default: a module handed no switch does
		// nothing at all, which is what the cook commandlet needs from it.
		if (FParse::Param(FCommandLine::Get(), TEXT("LedgerVignette")))
		{
			LedgerVignetteShot::Start();
			return;
		}
		if (FParse::Param(FCommandLine::Get(), TEXT("LedgerShot")))
		{
			StartShot();
			return;
		}
		if (!FParse::Param(FCommandLine::Get(), TEXT("LedgerGoldenTest")))
		{
			return;
		}
		RunGoldenTest();
		// Ask the engine to quit rather than sitting in a game loop on
		// somebody's desktop. The workflow also passes -unattended.
		FPlatformMisc::RequestExit(false);
	}
};

IMPLEMENT_PRIMARY_GAME_MODULE(FLedgerProbeModule, LedgerProbe, "LedgerProbe");
