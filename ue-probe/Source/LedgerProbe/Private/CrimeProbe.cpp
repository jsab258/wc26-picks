// THE CRIME, THE WITNESS AND THE OVERHEARD CONSEQUENCE. -LedgerCrime.
//
// Ruling: game-design/decision-2026-09-08-the-crime-the-witness-and-the-
// overheard-consequence.md. A half-brick through a shop window, committed
// twice: once in a witness's sight and once with a terrace between her and
// it, which is the rule-5b pair. What she saw is decided by Observe.Resolve
// on real traced geometry, filed as a memory, carried to a second NPC by the
// ported GossipMill.Tick with a real together predicate, and spoken by him at
// the rung she actually reached.
//
// WHY ALedgerGameMode NEEDS NO CHANGE, AND NEITHER DO THE THREE EXISTING
// SWITCHES. InitGame checks the command line for -LedgerVignette,
// -LedgerShot and -LedgerGoldenTest and has never heard of -LedgerCrime, so a
// crime run falls through to the SAME branch a genuine human launch takes:
// DefaultPawnClass stays ALedgerCharacter and
// LedgerVignetteShot::BuildInteractiveStreet(GetWorld()) runs unmodified,
// collision on, PlayerStart at cam_A. A plain launch with no switch is
// bit-for-bit unaffected: Start() below is called from one place and only
// when the switch is present. Checked by reading LedgerGameMode.cpp and
// LedgerProbe.cpp before writing this file, not assumed from their names.
//
// WHERE EVERY DECISION IN THIS RUN IS MADE, WHICH IS NOT HERE. CrimeProbe.h
// carries the arithmetic, the selection and every printed string, because
// this project's top layer does not compile in the container that writes it
// and a formatter shipped unrun is the quietest instrument fault there is
// (.claude/rules/instruments.md, 25 August). g++ compiles and RUNS that
// header's Selftest before any dispatch, and this file calls the same
// Selftest at Start so its result is a number on the verdict rather than a
// claim in a comment. What is left here is what only a running engine can
// answer: where an actor is, what a trace hit, what a screenshot contains.
//
// TWO CORRECTIONS THIS FILE CARRIES AGAINST THE RULING, both measured:
//
//   1. THE VICTIM SIGHTLINE IS CAPTURED BEFORE THE DEED. Once
//      east_parade_glass0 is hidden with its collision off, a trace from the
//      witness's eye to the window centre passes through the empty pane and
//      hits east_parade_interior0 behind it, so victimOccluded would read yes
//      and the ACCEPTING case would print as a rejection. Every vantage is
//      therefore read at the before_crime milestone with the glass standing,
//      the deed follows, and each witness line says victimVantageAt=
//      before-the-deed/glass-standing.
//
//   2. actorBlocker=<piece name> NEEDS AN EXPORT THAT DID NOT EXIST.
//      SpawnPiece calls SetActorLabel under WITH_EDITOR only, so in a
//      packaged build a hit actor answers GetName() with StaticMeshActor_NNN.
//      LedgerVignetteShot::StreetPieceNameOf is the reverse of the
//      name-to-actor lookup that already existed; it mutates nothing.
//
// AND ONE PLACE THE RULING CONTRADICTS ITSELF. Section 4 item 7's example
// prints overheardLineIds=cw-ws-r3-02,cw-ov-r3-01, which one seed cannot
// produce: seed = Day * 31 + Hour is 43 at D1 12:00 and 43 % 3 is 1 for both
// contexts, so the pair is cw-ws-r3-02,cw-ov-r3-02. The RULE is followed and
// the seed, the modulus and the picked index are all printed so a reader can
// check the arithmetic rather than take this comment's word for it.
//
// WHAT THIS RUN DOES NOT DO, so nobody looks for it: no third NPC, no second
// crime kind, no night, no rain, no Mixamo body, no voice, no sound, no
// StreetVoice composition, no Attention accumulator (SecondsWatching is this
// probe's own count and RungFloor is 0, both printed), no suspicion
// consequences, no save file, no memory loading, and no yard in the street's
// own JSON.
#include "CrimeProbe.h"

#include "VignetteShot.h"
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
#include "CollisionQueryParams.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"

#include <string>
#include <vector>

using namespace LedgerCore;

namespace
{
	// ---- ceilings and durations, none of them a threshold ----------------
	const double kWorldCeiling          = 45.0;
	const double kPawnCeiling           = 30.0;
	const double kSettleAfterSpawn      = 0.5;
	const double kSettleAfterTeleport   = 0.5;
	// THE APPROACH IS THE CLIP'S OWN MATERIAL and the witness's watching
	// time, both at once: she accrues SecondsWatching for exactly as long as
	// her trace to him holds, which is what Perception.NoticeSeconds
	// documents as belonging there. Two seconds of ordinary movement input,
	// which the walk probe measured at about 2 m/s, is four metres of street.
	const double kApproachSeconds       = 2.0;
	const double kShotFileCeiling       = 15.0;
	const double kSeqFileCeiling        = 5.0;

	const TCHAR* kGlassA = TEXT("east_parade_glass0");
	const TCHAR* kGlassB = TEXT("east_parade_glass1");

	// The bank, found the same way the piece list is (VignetteShot.cpp's
	// FindSpec): a packaged build's ProjectDir is the STAGED project, not the
	// source tree, so one hard-coded location works in exactly one of the two
	// ways this binary gets run. Searching is fine; searching silently is
	// not, so the candidates tried are printed.
	const TCHAR* kBankLeaf = TEXT("crime-witness-v1.json");
	const TCHAR* kBankRepoPath = TEXT("content/dialogue/crime-witness-v1.json");

	// ---- phases ----------------------------------------------------------
	enum class ECrimePhase : uint8
	{
		WaitWorld, WaitPawn, SettleAfterSpawn, PlaceProps,
		ShotStart,
		ApproachA, PlaceForA, SettleA, MeasureA, ShotBeforeA, SeqBeforeA,
		CommitA, SeqAfterA, ShotAfterA, Round1,
		MoveW1ToYard, ApproachB, PlaceForB, SettleB, MeasureB, ShotBeforeB,
		SeqBeforeB, CommitB, SeqAfterB, ShotAfterB, Round2,
		MoveToOverhear, SettleOverhear, OverheardHold, ShotOverheard,
		Done
	};

	FTSTicker::FDelegateHandle GTicker;
	ECrimePhase GPhase      = ECrimePhase::WaitWorld;
	double      GPhaseStart = 0.0;
	double      GRunStart   = 0.0;
	double      GLastTick   = 0.0;
	int32       GTicks      = 0;
	FString     GFinishReason = TEXT("process-completed-normally");

	APawn*  GPawn = nullptr;
	AActor* GW1Body = nullptr;
	AActor* GN2Body = nullptr;
	AActor* GYardFloor = nullptr;
	AActor* GGlass[2] = { nullptr, nullptr };

	int32 GBodiesSpawned = 0, GShardsSpawned = 0, GBricksSpawned = 0, GFloorSpawned = 0;
	int32 GProbePiecesAsked = 0;

	// ---- what the run measured -------------------------------------------
	std::vector<LedgerCrime::Reading> GReadings;
	LedgerCrime::CrimeReading GCrime[2];
	LedgerCrime::RoundReading GRound1, GRound2;
	LedgerCrime::OverheardReading GOverheard;
	LedgerCrime::SelftestResult GSelftest;
	std::string GBankText;
	std::vector<std::string> GBankTried;
	// TWO STRINGS OFF ONE ROW, queue 157: the sentence she SAYS and the clause
	// the mill FILES. Both are on the verdict's bank line, because a reader who
	// can see only one cannot tell which one got spliced.
	std::string GSummaryText = "none", GReplyText = "none", GSummaryClause = "none";
	int GAchievedRung = 0;

	// THE RUMOUR THE MILL ACTUALLY CARRIED, queue 147. GossipMill::Tick hands
	// the LISTENER'S OWN COPY back on the event (Gossip.cs 386 to 398: the
	// heard rumour at the decayed confidence, not the speaker's), and
	// GossipDirector.cs 587 composes from exactly that copy. So this is what
	// the exchange is built from, and it is a handle on the object in n2's
	// Rumors rather than a reconstruction of it.
	RumorPtr GCarried;

	// SECONDS WATCHING, MEASURED, one accumulator per witness per crime. The
	// ticker adds this frame's delta for a witness whose sightline to the
	// actor holds RIGHT NOW, which is what Witnesses.cs 178 to 192 says
	// belongs in the field. -1 means the accumulators are off.
	int    GWatchSlot = -1;
	double GSeconds[2][2] = { { 0.0, 0.0 }, { 0.0, 0.0 } };
	int    GWatchTicks[2] = { 0, 0 };

	// ---- the mill --------------------------------------------------------
	GameTime GNow(1, 12, 0);
	std::shared_ptr<SocialGraph> GGraph;
	std::shared_ptr<GossipMill>  GMill;
	GossiperPtr GW1, GN2;

	// ---- the shot in flight, one at a time -------------------------------
	bool    GShotInFlight        = false;
	bool    GSeqInFlight         = false;
	FString GShotPath;
	FString GShotName;
	bool    GShotUsedHighRes     = false;
	bool    GShotTriedHighResOne = false;
	int64   GShotSizeTracker     = -1;
	double  GShotWaitStart       = 0.0;
	std::vector<std::string> GShotLines;
	int32   GShotsAttempted = 0, GShotsWrote = 0;
	double  GLastSeqCaptureTime = 0.0;
	int32   GSeqRequested = 0, GSeqWrote = 0, GSeqForced = 0;
	std::vector<std::string> GSeqKeys;

	// WHICH BEAT A SEQUENCE FRAME WAS TAKEN ON, carried on the frame's own
	// keys line for tools/clip-from-frames.py to caption from. Set at phase
	// transitions and read at capture, so a frame can never claim a beat that
	// was not running when the shutter opened.
	std::string GBeat = "start", GBeatSpeaker = "none", GBeatLineId = "none";
	// THE WORDS ON THE FRAME, and where they came from. A composed telling is
	// not in the bank and cannot be captioned by id, so the text rides on the
	// keys line beside the id.
	std::string GBeatLineText, GBeatLineTextSource;
	bool GBeatHeard = false;

	// ---- small engine helpers, the same shapes WalkProbe.cpp uses --------
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

	FString ExeDir(const TCHAR* Leaf)
	{
		return FPaths::Combine(FPaths::GetPath(FPlatformProcess::ExecutablePath()), Leaf);
	}

	FString CrimeSha()
	{
		FString Sha;
		if (!FParse::Value(FCommandLine::Get(), TEXT("LedgerCommit="), Sha) || Sha.IsEmpty())
		{
			Sha = TEXT("SHA-UNKNOWN");
		}
		return Sha.Replace(TEXT(" "), TEXT("~"));
	}

	// BOTH PLACES, for the reason the walk verdict names: a packaged build's
	// ProjectDir is the staged project and the workflow step looks in three
	// candidates, so writing one file to one of them is a coin toss.
	void SaveBoth(const FString& Leaf, const FString& Body)
	{
		FFileHelper::SaveStringToFile(Body, *AbsProject(*Leaf));
		FFileHelper::SaveStringToFile(Body, *ExeDir(*Leaf));
	}

	std::string Utf8(const FString& S) { return std::string(TCHAR_TO_UTF8(*S)); }
	FString Un(const std::string& S)   { return FString(UTF8_TO_TCHAR(S.c_str())); }

	// ---- the two frames, converted in exactly one place ------------------
	//
	// The shared file's frame is x along, y up, z across; the engine's X is
	// x*100, its Y is z*100 and its Z is y*100. VignetteShot.cpp's SpawnPiece
	// is the other converter and it is the one this matches.
	FVector ToUE(const LedgerCrime::P3& P)
	{
		return FVector((float)(P.X * 100.0), (float)(P.Z * 100.0), (float)(P.Y * 100.0));
	}

	LedgerCrime::P3 ToStreet(const FVector& V)
	{
		return LedgerCrime::P3((double)V.X / 100.0, (double)V.Z / 100.0, (double)V.Y / 100.0);
	}

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

	// DECODE THE FILE THAT IS ABOUT TO BE COMMITTED, not a buffer the engine
	// held in memory: rule 4, read the artifact you are shipping. A fourth
	// copy of this decode; the other three are in LedgerProbe.cpp,
	// VignetteShot.cpp and WalkProbe.cpp, and this change's scope does not
	// reach into any of their capture paths to merge them.
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

	// MEASURE, THEN JUDGE, WITH THE MATHS COMING FROM FrameStats.h, which g++
	// runs before this file compiles.
	std::string MeasureShotFile(const FString& Path, const FVector& Loc, bool& OutWrote)
	{
		OutWrote = false;
		const int64 Bytes = IFileManager::Get().FileSize(*Path);
		const std::string ShotNameUtf8(TCHAR_TO_UTF8(*GShotName));
		char Head[192];
		std::snprintf(Head, sizeof(Head), "crimeShot=%s crimeShotAtXYZcm=%.1f/%.1f/%.1f ",
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
		FScreenshotRequest::RequestScreenshot(GShotPath, false, false);
	}

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
		std::snprintf(Head, sizeof(Head), "crimeShot=%s crimeShotAtXYZcm=%.1f/%.1f/%.1f ",
			ShotNameUtf8.c_str(), Loc.X, Loc.Y, Loc.Z);
		OutLine = std::string(Head) + "shotStatus=NO-FILE shotNote=neither-candidate-wrote-a-file-in-"
		        + std::to_string((int)Ceiling) + "s";
		return true;
	}

	void WriteSeqKeys();

	// ONE SEQUENCE FRAME, REQUESTED NOW, whatever the phase. Its keys row is
	// written when the shutter opens rather than when the file lands, so the
	// beat on the row is the beat that was running at the moment of capture;
	// a row naming a frame that never wrote simply matches no file when the
	// stitcher globs, which is the harmless direction.
	bool BeginSeqFrame(double Now, bool bForced)
	{
		if (GSeqRequested >= LedgerCrime::kMaxSeqFrames) { return false; }
		const FString Leaf = FString::Printf(TEXT("ue-crimeseq_%03d.png"), GSeqRequested);
		GShotName = FString::Printf(TEXT("seq%03d"), GSeqRequested);
		ShotBegin(AbsProject(*Leaf), Now);
		GSeqInFlight = true;
		GSeqKeys.push_back(LedgerCrime::SeqKeyLine(Utf8(Leaf), GBeat, GBeatSpeaker,
		                                           GBeatLineId, GBeatLineText,
		                                           GBeatLineTextSource, GBeatHeard));
		WriteSeqKeys();
		++GSeqRequested;
		if (bForced) { ++GSeqForced; }
		GLastSeqCaptureTime = Now;
		return true;
	}

	// Pumps a sequence frame already in flight and, when none is, starts one
	// if the interval has passed. A COOLDOWN AGAINST THE LAST CAPTURE rather
	// than an absolute schedule, so a slow attempt cannot cause a burst of
	// catch-up frames afterwards.
	void MaybeCaptureSequence(double Now)
	{
		if (GShotInFlight) { return; }
		if (GSeqInFlight)
		{
			const FVector Loc = (GPawn != nullptr) ? GPawn->GetActorLocation() : FVector::ZeroVector;
			std::string Line;
			if (ShotPump(Now, Loc, kSeqFileCeiling, /*bCountsTowardShotsWrote=*/false, Line))
			{
				GSeqInFlight = false;
			}
			return;
		}
		if (GLastSeqCaptureTime == 0.0) { GLastSeqCaptureTime = Now; return; }
		if ((Now - GLastSeqCaptureTime) < LedgerCrime::kSeqIntervalSeconds) { return; }
		BeginSeqFrame(Now, /*bForced=*/false);
	}

	// A FORCED FRAME AS ITS OWN PHASE, so the cut either side of each deed is
	// not left to a cooldown that might or might not have expired. Returns
	// true while it is still working.
	bool RunForcedSeqPhase(ECrimePhase NextPhase, double Now)
	{
		if (!GSeqInFlight)
		{
			if (!BeginSeqFrame(Now, /*bForced=*/true))
			{
				GPhase = NextPhase; GPhaseStart = Now;
			}
			return true;
		}
		const FVector Loc = (GPawn != nullptr) ? GPawn->GetActorLocation() : FVector::ZeroVector;
		std::string Line;
		if (ShotPump(Now, Loc, kSeqFileCeiling, /*bCountsTowardShotsWrote=*/false, Line))
		{
			GSeqInFlight = false;
			GPhase = NextPhase;
			GPhaseStart = Now;
		}
		return true;
	}

	bool RunShotPhase(const TCHAR* Name, const TCHAR* Leaf, ECrimePhase NextPhase, double Now)
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

	// ---- traces ----------------------------------------------------------
	//
	// THE NAME A TRACE HIT, AND WHAT IT MEANS WHEN THERE IS NONE. An actor
	// this module did not spawn (the pawn, a light, the world) has no piece
	// name, and printing the engine's StaticMeshActor_NNN is better than
	// printing nothing, so the fallback is named rather than blank.
	std::string BlockerName(const AActor* Hit)
	{
		if (Hit == nullptr) { return "none"; }
		const FString Named = LedgerVignetteShot::StreetPieceNameOf(Hit);
		if (!Named.IsEmpty()) { return Utf8(Named); }
		return "unnamed/" + Utf8(Hit->GetName());
	}

	// One line trace against the street's own collision. The target is
	// ignored (the question is what is BETWEEN, not whether the target is
	// solid) and so is the looker's own body, which the eye point sits inside
	// by construction.
	bool TraceBlocked(UWorld* World, const FVector& From, const FVector& To,
	                  const AActor* IgnoreA, const AActor* IgnoreB,
	                  std::string& OutBlocker, double& OutLenCm)
	{
		OutBlocker = "none";
		OutLenCm = (double)FVector::Dist(From, To);
		if (World == nullptr) { return false; }
		// DEFAULT CONSTRUCTED AND THEN SET, which is the plainest form of
		// this type there is: a tagged constructor and the SCENE_QUERY_STAT
		// macro are both conveniences whose exact shape is not worth a
		// 25-minute round trip to find out about.
		FCollisionQueryParams Params;
		Params.bTraceComplex = false;
		if (IgnoreA != nullptr) { Params.AddIgnoredActor(IgnoreA); }
		if (IgnoreB != nullptr) { Params.AddIgnoredActor(IgnoreB); }
		FHitResult Hit;
		const bool bHit = World->LineTraceSingleByChannel(Hit, From, To, ECC_Visibility, Params);
		if (!bHit) { return false; }
		OutBlocker = BlockerName(Hit.GetActor());
		OutLenCm = (double)FVector::Dist(From, Hit.ImpactPoint);
		return true;
	}

	// THE GROUND UNDER A POINT, MEASURED, NEVER TYPED. The east footway is
	// cambered (its litter sits at y 0.087 to 0.098 against a nominal ground
	// top of 0.075) and the yard has no ground plane at all until this probe
	// spawns one, so every height in this run comes from a downward trace and
	// the ones that found nothing say so.
	bool GroundYAt(UWorld* World, double StreetX, double StreetZ, double& OutY,
	               std::string& OutOn)
	{
		OutY = 0.0;
		OutOn = "nothing-found";
		if (World == nullptr) { return false; }
		const FVector From = ToUE(LedgerCrime::P3(StreetX, 4.0, StreetZ));
		const FVector To   = ToUE(LedgerCrime::P3(StreetX, -2.0, StreetZ));
		FCollisionQueryParams Params;
		Params.bTraceComplex = false;
		if (GPawn != nullptr) { Params.AddIgnoredActor(GPawn); }
		FHitResult Hit;
		if (!World->LineTraceSingleByChannel(Hit, From, To, ECC_Visibility, Params)) { return false; }
		OutY = (double)Hit.ImpactPoint.Z / 100.0;
		OutOn = BlockerName(Hit.GetActor());
		return true;
	}

	// ---- placing things --------------------------------------------------
	AActor* SpawnBox(UWorld* World, const FString& Name, const LedgerCrime::P3& CentreM,
	                 double SX, double SY, double SZ, const TCHAR* Surface)
	{
		return LedgerVignetteShot::SpawnProbePiece(
			World, Name,
			FVector((float)CentreM.X, (float)CentreM.Y, (float)CentreM.Z),
			FVector((float)SX, (float)SY, (float)SZ),
			TEXT("box"), Surface);
	}

	AActor* SpawnBody(UWorld* World, const FString& Name, double StreetX, double StreetZ,
	                  double GroundY)
	{
		return LedgerVignetteShot::SpawnProbePiece(
			World, Name,
			FVector((float)StreetX, (float)(GroundY + LedgerCrime::kBodyHeightM * 0.5), (float)StreetZ),
			FVector((float)LedgerCrime::kBodyDiameterM, (float)LedgerCrime::kBodyHeightM,
			        (float)LedgerCrime::kBodyDiameterM),
			TEXT("cyl"), TEXT("cloth_dark"));
	}

	// A BODY MOVES BY ITS OWN TRANSFORM, not by a second spawn: W1 stands at
	// P1 for crime A and at P2 for crime B, and spawning her twice would put
	// two shopkeepers in the frame and two entries in the probe map.
	void MoveBody(UWorld* World, AActor* Body, double StreetX, double StreetZ)
	{
		if (Body == nullptr) { return; }
		double GroundY = 0.0;
		std::string On;
		if (!GroundYAt(World, StreetX, StreetZ, GroundY, On)) { GroundY = 0.1; }
		Body->SetActorLocation(ToUE(LedgerCrime::P3(
			StreetX, GroundY + LedgerCrime::kBodyHeightM * 0.5, StreetZ)));
	}

	void FaceBody(AActor* Body, const LedgerCrime::P3& Toward)
	{
		if (Body == nullptr) { return; }
		const LedgerCrime::P3 At = ToStreet(Body->GetActorLocation());
		const double Yaw = LedgerCrime::YawToFace(At, Toward);
		Body->SetActorRotation(FRotator(0.0f, (float)Yaw, 0.0f));
	}

	void TeleportPawn(UWorld* World, double StreetX, double StreetZ, double YawDeg)
	{
		if (GPawn == nullptr) { return; }
		double GroundY = 0.0;
		std::string On;
		if (!GroundYAt(World, StreetX, StreetZ, GroundY, On)) { GroundY = 0.1; }
		// A GENEROUS NAMED CLEARANCE ABOVE THE MEASURED GROUND rather than a
		// second copy of the capsule's half height: gravity settles the rest
		// on the first tick, exactly as BuildInteractiveStreet's own player
		// start does, and a spawn that starts too low would not correct
		// itself the same way.
		const double kClearAboveGroundM = 1.1;
		GPawn->TeleportTo(ToUE(LedgerCrime::P3(StreetX, GroundY + kClearAboveGroundM, StreetZ)),
		                  FRotator(0.0f, (float)YawDeg, 0.0f), false, true);
	}

	// ---- the vantage, read off the engine --------------------------------
	//
	// EVERY NUMBER HERE IS A MEASUREMENT OF THE RUNNING WORLD: the witness's
	// own transform, the pawn's own bounds, two line traces. Nothing is taken
	// from the ruling's arithmetic, which is printed separately as the
	// prediction this run is read against.
	LedgerCrime::Reading MeasureVantage(UWorld* World, const std::string& WitnessId,
	                                    const std::string& EventId, AActor* Body,
	                                    AActor* Glass, double SecondsWatching)
	{
		LedgerCrime::Reading R;
		R.WitnessId = WitnessId;
		R.EventId = EventId;
		R.SecondsWatching = SecondsWatching;
		if (Body == nullptr || GPawn == nullptr) { R.FiledReason = "nothing-measured"; return R; }

		// The body's own bounds give its feet; the eye sits 1.6 m above them.
		const FBox BodyBox = Body->GetComponentsBoundingBox();
		const LedgerCrime::P3 Feet = ToStreet(FVector(
			BodyBox.GetCenter().X, BodyBox.GetCenter().Y, BodyBox.Min.Z));
		R.WitnessAt = Feet;
		R.EyeAt = LedgerCrime::P3(Feet.X, Feet.Y + LedgerCrime::kEyeHeightM, Feet.Z);
		R.WitnessYawDeg = (double)Body->GetActorRotation().Yaw;

		// The actor's head, from the pawn's OWN bounds rather than a second
		// copy of ALedgerCharacter's capsule half height.
		const FBox PawnBox = GPawn->GetComponentsBoundingBox();
		const FVector HeadUE(PawnBox.GetCenter().X, PawnBox.GetCenter().Y, PawnBox.Max.Z - 10.0f);
		R.ActorHeadAt = ToStreet(HeadUE);
		R.ActorYawDeg = (double)GPawn->GetActorRotation().Yaw;

		// The window centre, read off the actor the street actually spawned,
		// after scale and rotation, never the file's numbers a second time.
		const FVector EyeUE = ToUE(R.EyeAt);
		R.ActorMetres = LedgerCrime::Metres(R.EyeAt, R.ActorHeadAt);
		R.ActorOffAxisDeg = LedgerCrime::OffAxisDeg(R.EyeAt, R.WitnessYawDeg, R.ActorHeadAt);
		R.bActorOccluded = TraceBlocked(World, EyeUE, HeadUE, Body, GPawn,
		                                R.ActorBlocker, R.ActorTraceLenCm);

		// NO WINDOW, NO VICTIM HALF. The per-tick watching accumulator calls
		// this for the actor half alone, and a trace to the world origin sixty
		// times a second measures nothing while costing a query each time.
		if (Glass == nullptr)
		{
			R.VictimBlocker = "no-window-asked-for";
			return R;
		}
		const FVector VictimUE = Glass->GetComponentsBoundingBox().GetCenter();
		R.VictimAt = ToStreet(VictimUE);
		R.VictimMetres = LedgerCrime::Metres(R.EyeAt, R.VictimAt);
		R.VictimOffAxisDeg = LedgerCrime::OffAxisDeg(R.EyeAt, R.WitnessYawDeg, R.VictimAt);
		R.bVictimOccluded = TraceBlocked(World, EyeUE, VictimUE, Body, Glass,
		                                 R.VictimBlocker, R.VictimTraceLenCm);
		return R;
	}

	// THE ACCUMULATOR. Called every tick while a crime's watching window is
	// open: a witness accrues this frame's delta only while her sightline to
	// the actor holds right now, which is the definition Perception.cs 65
	// carries and the one Witnesses.cs says belongs in the field.
	void AccrueWatching(UWorld* World, double Delta)
	{
		if (GWatchSlot < 0 || GWatchSlot > 1) { return; }
		AActor* Bodies[2] = { GW1Body, GN2Body };
		++GWatchTicks[GWatchSlot];
		for (int I = 0; I < 2; ++I)
		{
			if (Bodies[I] == nullptr || GPawn == nullptr) { continue; }
			const LedgerCrime::Reading R = MeasureVantage(
				World, I == 0 ? "w1" : "n2", "watch", Bodies[I], nullptr, 0.0);
			const bool bSees = Perception::InSight(R.ActorMetres, R.ActorOffAxisDeg,
			                                       LedgerCrime::kLightLevel, R.bActorOccluded, 1.4);
			if (bSees) { GSeconds[GWatchSlot][I] += Delta; }
		}
	}

	// ---- the deed --------------------------------------------------------
	void CommitDeed(UWorld* World, int Index)
	{
		LedgerCrime::CrimeReading& C = GCrime[Index];
		C.Id = (Index == 0) ? "A" : "B";
		C.PieceName = Index == 0 ? Utf8(FString(kGlassA)) : Utf8(FString(kGlassB));
		if (GPawn != nullptr)
		{
			C.ActorAt = ToStreet(GPawn->GetActorLocation());
			C.ActorYawDeg = (double)GPawn->GetActorRotation().Yaw;
		}
		AActor* Glass = GGlass[Index];
		if (Glass == nullptr)
		{
			C.bPieceFound = false;
			C.WhyNot = "piece-not-in-the-street-BuildScene-spawned";
			return;
		}
		C.bPieceFound = true;
		// READ BEFORE, ACT, READ AFTER. A hide that did not take and a hide
		// that was never needed are different facts, and only the pair can
		// tell them apart.
		C.bHiddenBefore = Glass->IsHidden();
		Glass->SetActorHiddenInGame(true);
		Glass->SetActorEnableCollision(false);
		C.bHiddenAfter = Glass->IsHidden();
		C.bCollisionAfter = Glass->GetActorEnableCollision();

		// The glass's own bounds give the window foot; the shards are laid on
		// the footway in front of it and each one sits on the ground a
		// downward trace found, never on a typed height.
		const FBox GlassBox = Glass->GetComponentsBoundingBox();
		const LedgerCrime::P3 Centre = ToStreet(GlassBox.GetCenter());
		for (int I = 0; I < LedgerCrime::ShardOffsetCount(); ++I)
		{
			double DX = 0.0, DZ = 0.0;
			LedgerCrime::ShardOffset(I, DX, DZ);
			const double SX = Centre.X + DX, SZ = Centre.Z + DZ;
			double GroundY = 0.0;
			std::string On;
			if (!GroundYAt(World, SX, SZ, GroundY, On)) { continue; }
			const FString Name = FString::Printf(TEXT("probe_shard_%s%d"),
				Index == 0 ? TEXT("a") : TEXT("b"), I);
			if (SpawnBox(World, Name,
			             LedgerCrime::P3(SX, GroundY + LedgerCrime::kShardSY * 0.5, SZ),
			             LedgerCrime::kShardSX, LedgerCrime::kShardSY, LedgerCrime::kShardSZ,
			             TEXT("glass")) != nullptr)
			{
				++C.Shards;
				++GShardsSpawned;
			}
		}
		{
			const double BX = Centre.X;
			const double BZ = LedgerCrime::kBrickInsideZ;
			double GroundY = 0.0;
			std::string On;
			if (GroundYAt(World, BX, BZ, GroundY, On))
			{
				const FString Name = FString::Printf(TEXT("probe_brick_%s"),
					Index == 0 ? TEXT("a") : TEXT("b"));
				if (SpawnBox(World, Name,
				             LedgerCrime::P3(BX, GroundY + LedgerCrime::kBrickSY * 0.5, BZ),
				             LedgerCrime::kBrickSX, LedgerCrime::kBrickSY, LedgerCrime::kBrickSZ,
				             TEXT("brick_grey")) != nullptr)
				{
					++C.Bricks;
					++GBricksSpawned;
				}
			}
			else
			{
				C.WhyNot = "no-ground-under-the-brick-point";
			}
		}
	}

	// ---- the bank --------------------------------------------------------
	bool LoadBank()
	{
		TArray<FString> Candidates;
		Candidates.Add(FPaths::Combine(FPaths::ProjectDir(), kBankLeaf));
		Candidates.Add(FPaths::Combine(FPaths::ProjectContentDir(), kBankLeaf));
		Candidates.Add(FPaths::Combine(FPaths::LaunchDir(), kBankLeaf));
		Candidates.Add(FPaths::Combine(FPaths::GetPath(FPlatformProcess::ExecutablePath()), kBankLeaf));
		Candidates.Add(FPaths::Combine(FPaths::ProjectDir(), TEXT(".."), kBankRepoPath));
		for (const FString& C : Candidates)
		{
			const FString Full = FPaths::ConvertRelativePathToFull(C);
			GBankTried.push_back(Utf8(Full.Replace(TEXT(" "), TEXT("~"))));
			if (!FPaths::FileExists(C)) { continue; }
			FString Contents;
			if (!FFileHelper::LoadFileToString(Contents, *C)) { continue; }
			GBankText = Utf8(Contents);
			GOverheard.BankPath = Utf8(Full.Replace(TEXT(" "), TEXT("~")));
			GOverheard.bBankRead = true;
			return true;
		}
		GOverheard.BankPath = "not-found";
		GOverheard.WhyNot = "bank-not-found-beside-the-binary-or-the-project";
		return false;
	}

	// ---- the mill --------------------------------------------------------
	struct TogetherByDistance
	{
		double PairMetres(const std::string& A, const std::string& B) const
		{
			AActor* PA = (A == "w1") ? GW1Body : ((A == "n2") ? GN2Body : nullptr);
			AActor* PB = (B == "w1") ? GW1Body : ((B == "n2") ? GN2Body : nullptr);
			if (PA == nullptr || PB == nullptr) { return -1.0; }
			return (double)FVector::Dist(PA->GetActorLocation(), PB->GetActorLocation()) / 100.0;
		}

		bool operator()(const std::string& A, const std::string& B) const
		{
			const double M = PairMetres(A, B);
			return M >= 0.0 && M <= LedgerCrime::kTalkRangeM;
		}
	};

	double PairMetresNow(const std::string& A, const std::string& B)
	{
		TogetherByDistance T;
		return T.PairMetres(A, B);
	}

	void RunGossipRound(int Index, LedgerCrime::RoundReading& Out)
	{
		Out.Round = Index;
		Out.SpeakerId = "w1";
		Out.ListenerId = "n2";
		Out.PairMetres = PairMetresNow("w1", "n2");
		Out.bTogether = Out.PairMetres >= 0.0 && Out.PairMetres <= LedgerCrime::kTalkRangeM;
		Out.Tie = GMill ? GMill->Tie("w1", "n2") : 0.0;
		Out.HopDecay = GMill ? GMill->HopDecay : 0.0;
		Out.MinShare = GMill ? GMill->MinConfidenceToShare : 0.0;
		if (GW1)
		{
			Out.RumoursHeld = (int)GW1->Rumors.size();
			// THE STRONGEST TELLING THE SPEAKER HOLDS AS THE ROUND OPENS,
			// which is the number Tick multiplies by tie and hop decay.
			for (std::vector<RumorPtr>::size_type I = 0; I < GW1->Rumors.size(); ++I)
			{
				if (GW1->Rumors[I]->Confidence > Out.ConfidenceIn)
				{
					Out.ConfidenceIn = GW1->Rumors[I]->Confidence;
				}
			}
		}
		if (!GMill) { Out.bRan = false; return; }
		const std::vector<GossipEvent> Events =
			GMill->Tick(GNow, GossipMill::TogetherFn(TogetherByDistance()));
		for (std::vector<GossipEvent>::size_type I = 0; I < Events.size(); ++I)
		{
			if (Events[I].FromId != "w1" || Events[I].ToId != "n2") { continue; }
			++Out.Passed;
			if (Events[I].RumorRef)
			{
				Out.ConfidencePassed = Events[I].RumorRef->Confidence;
				Out.Hops = Events[I].RumorRef->Hops;
				// WHAT THE OVERHEARD BEAT WILL BE COMPOSED FROM. Last one
				// wins, which is the same rumour every time here: one topic,
				// one pair, one hop per round.
				GCarried = Events[I].RumorRef;
			}
			Out.bContradiction = Events[I].Contradiction;
			Out.bExposure = Events[I].Exposure;
		}
		// READ BACK OFF THE LISTENER'S OWN MEMORY, never recomputed from the
		// formula: the number that matters is the one that landed in the file
		// this run commits.
		if (Out.Passed > 0 && GN2 && GN2->Memory && !GN2->Memory->Events.empty())
		{
			Out.HeardImportance = GN2->Memory->Events[GN2->Memory->Events.size() - 1].Importance;
		}
		Out.bRan = true;
	}

	// ---- the files this run commits --------------------------------------
	void WriteSeqKeys()
	{
		TArray<FString> Out;
		Out.Add(FString::Printf(TEXT("# UE crime sequence keys %s @%lld"),
		                        *CrimeSha(), (long long)FDateTime::UtcNow().ToUnixTimestamp()));
		Out.Add(TEXT("# One line per sequence frame. tools/clip-from-frames.py --frame-keys reads"));
		Out.Add(TEXT("#   this and burns the bank's text for lineId on frames whose heard is yes."));
		for (std::vector<std::string>::size_type I = 0; I < GSeqKeys.size(); ++I)
		{
			Out.Add(Un(GSeqKeys[I]));
		}
		SaveBoth(TEXT("ue-crimeseq-keys.txt"), FString::Join(Out, TEXT("\n")) + TEXT("\n"));
	}

	int WriteMemoryFiles()
	{
		int Wrote = 0;
		GossiperPtr Two[2] = { GW1, GN2 };
		const TCHAR* Leaves[2] = { TEXT("ue-crime-memory-w1.md"), TEXT("ue-crime-memory-n2.md") };
		for (int I = 0; I < 2; ++I)
		{
			if (!Two[I] || !Two[I]->Memory) { continue; }
			// THE MARKDOWN IS THE ARTEFACT OF "PERMANENTLY REMEMBER" and it
			// comes out of MemoryStore::ToMarkdown, the ported function, not
			// out of a formatter written here.
			SaveBoth(Leaves[I], Un(Two[I]->Memory->ToMarkdown()));
			++Wrote;
		}
		return Wrote;
	}

	void WriteBreadcrumb(const TCHAR* Phase)
	{
		TArray<FString> Out;
		Out.Add(FString::Printf(TEXT("# UE crime probe %s @%lld"),
		                        *CrimeSha(), (long long)FDateTime::UtcNow().ToUnixTimestamp()));
		Out.Add(TEXT("# Line 1 names the commit this was measured on, as the Unity verdict does."));
		Out.Add(TEXT(""));
		Out.Add(FString::Printf(TEXT("crimePhaseReached=%s"), Phase));
		Out.Add(TEXT("crimeReached=in-progress"));
		SaveBoth(TEXT("ue-crime-verdict.txt"), FString::Join(Out, TEXT("\n")) + TEXT("\n"));
	}

	std::string SummariesDenominator()
	{
		int N = 0;
		if (GMill)
		{
			const std::vector<GossiperPtr>& Agents = GMill->Agents();
			for (std::vector<GossiperPtr>::size_type I = 0; I < Agents.size(); ++I)
			{
				if (Agents[I]) { N += (int)Agents[I]->Rumors.size(); }
			}
		}
		return LedgerCrime::Int(N);
	}

	void WriteFinalVerdict()
	{
		const Deed DeedA = LedgerCrime::MakeDeed("crime_a", "player", Utf8(FString(kGlassA)));

		TArray<FString> Out;
		Out.Add(FString::Printf(TEXT("# UE crime probe %s @%lld"),
		                        *CrimeSha(), (long long)FDateTime::UtcNow().ToUnixTimestamp()));
		Out.Add(TEXT("# Line 1 names the commit this was measured on, as the Unity verdict does."));
		Out.Add(TEXT("# Ruling 2026-09-08, the crime, the witness and the overheard consequence."));
		Out.Add(TEXT("#   launchStatus is added by the workflow step from this file's presence, its"));
		Out.Add(TEXT("#   last crimePhaseReached and the process's exit code, because only something"));
		Out.Add(TEXT("#   watching from outside can tell a hang from a crash from a clean exit."));
		Out.Add(TEXT("# THE SCENE: the same piecesEmitted=N/M counters BuildScene emits, read back,"));
		Out.Add(TEXT("#   never recomputed. probe* counts are THIS module's own pieces, which are"));
		Out.Add(TEXT("#   not street pieces and are never in GByName."));
		Out.Add(TEXT("# THE WITNESS: every witness= line is one witness at one crime, measured off"));
		Out.Add(TEXT("#   the engine (two line traces, the actor's own bounds, an accumulated"));
		Out.Add(TEXT("#   watching time) and decided by Observe.Resolve, the transliterated C#."));
		Out.Add(TEXT("#   THE VANTAGE IS READ BEFORE THE DEED, with the glass standing: hiding the"));
		Out.Add(TEXT("#   pane first would let the trace through the empty frame onto the interior"));
		Out.Add(TEXT("#   wall and print the accepting case as a rejection."));
		Out.Add(TEXT("# THE MILL: gossipRound= lines are the rule-5b pair. Round 1 is the same two"));
		Out.Add(TEXT("#   people too far apart to talk; round 2 is the same two in the yard. Nothing"));
		Out.Add(TEXT("#   about the rumour changes between them except where they are standing."));
		Out.Add(TEXT("# THE LINE IS COMPOSED, NOT PICKED, since queue 147. The bank at"));
		Out.Add(TEXT("#   content/dialogue/crime-witness-v1.json still supplies the rung and the id"));
		Out.Add(TEXT("#   by the seed the game uses, Day*31+Hour, and the seed, the modulus and the"));
		Out.Add(TEXT("#   picked index are printed so that pick can still be checked. What the two"));
		Out.Add(TEXT("#   of them SAY is then built by the ported StreetVoice.Exchange around the"));
		Out.Add(TEXT("#   summary the mill actually carried. overheardReplyMode says which, with"));
		Out.Add(TEXT("#   the count of beats in each mode; the telling is the composed beat and the"));
		Out.Add(TEXT("#   answer is a literal from the HEARER'S disposition band, which is the C#'s"));
		Out.Add(TEXT("#   own accounting at StreetVoice.cs 289 to 295 and not a softening of it."));
		Out.Add(TEXT("# EVERY ZERO SHIPS ITS DENOMINATOR AND EVERY CAP ANNOUNCES ITSELF."));
		Out.Add(TEXT(""));

		// 1. The scene, and this module's own pieces.
		Out.Add(LedgerVignetteShot::StreetSceneLine());
		Out.Add(Un("probeFloor=" + LedgerCrime::Int(GFloorSpawned) + "/1"
		           " probeFloorNote=not-a-street-piece/the-street-owes-a-yard-behind-the-crossover"
		           " probeBodies=" + LedgerCrime::Int(GBodiesSpawned) + "/2"
		           " probeShards=" + LedgerCrime::Int(GShardsSpawned) + "/16"
		           " probeBricks=" + LedgerCrime::Int(GBricksSpawned) + "/2"
		           " probePiecesMaterialBound=0/" + LedgerCrime::Int(GProbePiecesAsked)
		         + " probePiecesMaterialNote=BindSurfaces-runs-inside-BuildScene/these-spawn-after-it"
		           " probePiecesNote=not-street-pieces/never-in-GByName"));

		// 2. The inputs, once, each beside the C# line it came from.
		Out.Add(Un("crimeGameTime=D1/12:00 crimeGameTimeSource=GameTime.cs-9-22"
		           " crimeLightLevel=" + LedgerCrime::F2(LedgerCrime::kLightLevel)
		         + " crimeLightLevelSource=Perceivers.cs-69-71/overcast_day-night-0-lanterns-off"
		           " crimeAmbientFloor=" + LedgerCrime::F1(LedgerCrime::kAmbientFloor)
		         + " crimeAmbientFloorSource=Perception.cs-228/AmbientDaytimeStreet"
		           " crimeLoudness=" + LedgerCrime::F1(DeedA.Loudness)
		         + " crimeLoudnessSource=Perception.cs-244/LoudBottleSmash"
		           " castTie=" + LedgerCrime::F2(LedgerCrime::kTie)
		         + " castTieSource=GossipDirector.cs-127-128"
		           " castFamiliarityW1=" + LedgerCrime::F2(LedgerCrime::kFamiliarity)
		         + " castFamiliarityN2=" + LedgerCrime::F2(LedgerCrime::kFamiliarity)
		         + " castFamiliaritySource=Witnesses.cs-142/strangers"
		           " castRungFloor=0 castRungFloorSource=Perception.Attention-out-of-scope"
		           " castAlertness=0 castBodies=cylinder-stand-in/no-mixamo-body-in-ue-probe"));
		Out.Add(Un(LedgerCrime::DeedInputsLine(DeedA)));

		// THE PREDICTION THE FIRST RUN IS READ AGAINST, ruling section 2. Hand
		// arithmetic from the piece list, printed so a disagreement between it
		// and the measurements above is a finding rather than a surprise.
		Out.Add(TEXT("crimePrediction=w1/A/actorM=2.28/victimM=2.15/victimOffAxisDeg=28.2")
		        TEXT("/faceDeg=69.4/rung=3/certainty=0.94/audibleRadiusM=13.1")
		        TEXT(" crimePredictionOccluded=w1/B,n2/A,n2/B/blocker=west_south_bay2")
		        TEXT("/audibleRadiusM=1.9/slots=none")
		        TEXT(" crimePredictionSource=ruling-section-2/hand-arithmetic-not-a-measurement"));

		// 3. The two deeds.
		for (int I = 0; I < 2; ++I) { Out.Add(Un(LedgerCrime::CrimeLine(GCrime[I]))); }

		// 4. The four witness readings, the per-sample moment.
		Out.Add(Un("witnessReadings=" + LedgerCrime::Int((int)GReadings.size()) + "/4"));
		if (GReadings.empty())
		{
			Out.Add(TEXT("NOTHING MEASURED - no vantage reached the resolver on this commit."));
		}
		// ONE DEED PER CRIME, NOT ONE FOR BOTH. The two are the same act at
		// the same loudness and differ only in which window they name, but the
		// hearing half of Resolve reads the deed the witness was resolved
		// against, so the line is printed against the same one.
		const Deed DeedB = LedgerCrime::MakeDeed("crime_b", "player", Utf8(FString(kGlassB)));
		for (std::vector<LedgerCrime::Reading>::size_type I = 0; I < GReadings.size(); ++I)
		{
			Out.Add(Un(LedgerCrime::WitnessLine(GReadings[I],
				GReadings[I].EventId == "A" ? DeedA : DeedB)));
		}

		// 5. The mill, whole run.
		Out.Add(Un("witnessesOffered=" + LedgerCrime::Int(GMill ? GMill->WitnessesOffered() : 0)
		         + " witnessesDropped=" + LedgerCrime::Int(GMill ? GMill->WitnessesDropped() : 0)
		         + "/" + LedgerCrime::Int(GMill ? GMill->WitnessesOffered() : 0)
		         + " summariesSayingPlayer=" + LedgerCrime::Int(GMill ? GMill->SummariesSaying("player") : 0)
		         + "/" + SummariesDenominator() + "-rumours"
		         + " summariesSayingPlayerStat=whole-run/every-agent-every-rumour"
		           " gossipSuspicionPorted=no/SuspicionTracker-out-of-scope"));

		// 6. The two rounds.
		Out.Add(Un(LedgerCrime::GossipRoundLine(GRound1)));
		Out.Add(Un(LedgerCrime::GossipRoundLine(GRound2)));

		// 7. The overheard beat, and the prose on its own line under it.
		Out.Add(Un(LedgerCrime::OverheardLine(GOverheard)));
		Out.Add(Un(LedgerCrime::OverheardTextLine(GOverheard)));

		// 8. Memory, whole run.
		const int W1Events = (GW1 && GW1->Memory) ? (int)GW1->Memory->Events.size() : 0;
		const int N2Events = (GN2 && GN2->Memory) ? (int)GN2->Memory->Events.size() : 0;
		Out.Add(Un("memoryW1Events=" + LedgerCrime::Int(W1Events)
		         + " memoryN2Events=" + LedgerCrime::Int(N2Events)
		         + " memoryFiles=" + LedgerCrime::Int(WriteMemoryFiles()) + "/2"
		           " memoryFilePrefix=ue-crime-memory-"));

		// 9. The three combined readings. Each needs both halves.
		Out.Add(Un("witnessStatus=" + LedgerCrime::WitnessStatus(GReadings)
		         + " witnessStatusNote=w1-filed-on-A-with-a-rung/w1-empty-on-B-occluded/n2-empty-on-both"
		           " gossipStatus=" + LedgerCrime::GossipStatus(GRound1, GRound2)
		         + " gossipStatusNote=round-1-not-together-passed-0/round-2-together-passed-1"
		           " combinedReadings=3/3"
		           " combinedReadingsNote=overheardStatus-is-on-the-overheard-line-above/never-printed-twice"));

		// 10. The frames.
		Out.Add(Un("crimeFramesRequested=" + LedgerCrime::Int(GShotsAttempted) + "/"
		         + LedgerCrime::Int(LedgerCrime::kMilestoneCount)
		         + " crimeFramesWrote=" + LedgerCrime::Int(GShotsWrote) + "/"
		         + LedgerCrime::Int(LedgerCrime::kMilestoneCount)));
		if (GShotLines.empty())
		{
			Out.Add(TEXT("NOTHING MEASURED - no frame reached the measuring step on this commit."));
		}
		for (std::vector<std::string>::size_type I = 0; I < GShotLines.size(); ++I)
		{
			Out.Add(Un(GShotLines[I]));
		}
		Out.Add(Un("crimeSeqFramesRequested=" + LedgerCrime::Int(GSeqRequested) + "/"
		         + LedgerCrime::Int(LedgerCrime::kMaxSeqFrames)
		         + " crimeSeqFramesWrote=" + LedgerCrime::Int(GSeqWrote) + "/"
		         + LedgerCrime::Int(LedgerCrime::kMaxSeqFrames)
		         + " crimeSeqIntervalSeconds=" + LedgerCrime::F1(LedgerCrime::kSeqIntervalSeconds)
		         + " crimeSeqForcedAtDeeds=" + LedgerCrime::Int(GSeqForced) + "/"
		         + LedgerCrime::Int(LedgerCrime::kForcedAtDeeds)
		         + " crimeSeqCapNote=32-is-a-clock-cap-not-a-target"
		           " crimeSeqKeysFile=ue-crimeseq-keys.txt"));

		// The instrument's own selftest, and the watching accumulator's
		// denominators. A run that measured nothing says so here too.
		Out.Add(Un("crimeSelftestChecks=" + LedgerCrime::Int(GSelftest.Checks)
		         + " crimeSelftestFailed=" + LedgerCrime::Int(GSelftest.Failed) + "/"
		         + LedgerCrime::Int(GSelftest.Checks)
		         + " crimeSelftestFirstFailure=" + GSelftest.FirstFailure
		         + " crimeSelftestNote=CrimeProbe.h-decisions-and-strings/run-again-here-on-the-machine"));
		Out.Add(Un("watchTicksA=" + LedgerCrime::Int(GWatchTicks[0])
		         + " watchTicksB=" + LedgerCrime::Int(GWatchTicks[1])
		         + " watchSecondsW1A=" + LedgerCrime::F2(GSeconds[0][0])
		         + " watchSecondsN2A=" + LedgerCrime::F2(GSeconds[0][1])
		         + " watchSecondsW1B=" + LedgerCrime::F2(GSeconds[1][0])
		         + " watchSecondsN2B=" + LedgerCrime::F2(GSeconds[1][1])
		         + " watchStat=accumulated-while-InSight-to-the-actor-held/Perception.cs-65"));
		// THE ROW'S TWO STRINGS, SIDE BY SIDE AND AT THE SAME MOMENT, queue 157.
		// bankSummaryText is what she SAYS; bankSummaryClause is what the mill
		// FILED and therefore what both splices carried. A reader holding only
		// one of them cannot tell which was spliced, which is how the sentence
		// reached a committed memory file unnoticed. The shape says
		// nothing-measured when no witness_summary was picked at all, so a
		// never-ran run cannot read as a missing clause.
		const std::string ClauseShapeValue = (GSummaryClause == "none")
			? std::string("nothing-measured/no-witness-summary-was-picked")
			: LedgerCrime::ClauseShape(GSummaryClause);
		Out.Add(Un("bankTried=" + LedgerCrime::Int((int)GBankTried.size())
		         + " bankFrom=" + GOverheard.BankPath
		         + " bankSummaryText=" + LedgerCrime::NoSpaces(GSummaryText)
		         + " bankSummaryClause=" + LedgerCrime::NoSpaces(GSummaryClause)
		         + " bankSummaryClauseShape=" + LedgerCrime::NoSpaces(ClauseShapeValue)
		         + " bankReplyText=" + LedgerCrime::NoSpaces(GReplyText)
		         + " bankTextNote=spaces-become-dashes-in-a-value/the-bank-file-holds-the-prose"
		           "/these-are-the-BANK-rows-at-the-rung/the-clause-is-what-the-mill-filed"
		           "/the-sentence-is-what-she-said/what-was-said-is-on-the-overheardTellText-line"));
		Out.Add(FString::Printf(TEXT("crimeTicks=%d crimeSeconds=%.2f crimeFinishReason=%s"),
		                        GTicks, FPlatformTime::Seconds() - GRunStart, *GFinishReason));

		Out.Add(TEXT("crimePhaseReached=done"));
		Out.Add(TEXT("crimeReached=end"));
		SaveBoth(TEXT("ue-crime-verdict.txt"), FString::Join(Out, TEXT("\n")) + TEXT("\n"));
		WriteSeqKeys();
	}

	void Finish()
	{
		GPhase = ECrimePhase::Done;
		WriteFinalVerdict();
		FPlatformMisc::RequestExit(false);
	}

	// ---- the props -------------------------------------------------------
	void PlaceProps(UWorld* World)
	{
		GProbePiecesAsked = 1 + 2 + 16 + 2;

		// THE YARD FLOOR FIRST: nothing else in the yard has anything to
		// stand on. ground_plot_2 ends at x 21 and ground_plot_3 starts at x
		// 24, and the gap between them is the only place a person can stand
		// with a terrace between them and a shop window.
		GYardFloor = SpawnBox(World, TEXT("probe_yard_floor"),
			LedgerCrime::P3(LedgerCrime::kYardX, LedgerCrime::kYardY, LedgerCrime::kYardZ),
			LedgerCrime::kYardSX, LedgerCrime::kYardSY, LedgerCrime::kYardSZ, TEXT("concrete"));
		if (GYardFloor != nullptr) { ++GFloorSpawned; }

		double GY = 0.0;
		std::string On;
		if (!GroundYAt(World, LedgerCrime::kW1AX, LedgerCrime::kW1AZ, GY, On)) { GY = 0.1; }
		GW1Body = SpawnBody(World, TEXT("probe_body_w1"),
		                    LedgerCrime::kW1AX, LedgerCrime::kW1AZ, GY);
		if (GW1Body != nullptr) { ++GBodiesSpawned; }

		if (!GroundYAt(World, LedgerCrime::kN2X, LedgerCrime::kN2Z, GY, On)) { GY = 0.1; }
		GN2Body = SpawnBody(World, TEXT("probe_body_n2"),
		                    LedgerCrime::kN2X, LedgerCrime::kN2Z, GY);
		if (GN2Body != nullptr) { ++GBodiesSpawned; }

		FaceBody(GW1Body, LedgerCrime::P3(LedgerCrime::kCrimeAX, 0.0, LedgerCrime::kCrimeAZ));
		// N2 faces +z, up the yard, by the ruling: he is not looking at
		// anything and the terrace is between him and both windows anyway.
		if (GN2Body != nullptr) { GN2Body->SetActorRotation(FRotator(0.0f, 90.0f, 0.0f)); }

		GGlass[0] = LedgerVignetteShot::FindStreetPiece(kGlassA);
		GGlass[1] = LedgerVignetteShot::FindStreetPiece(kGlassB);
	}

	// ---- filing what a witness got ---------------------------------------
	void ResolveAndFile(int Index)
	{
		const std::string EventId = (Index == 0) ? "A" : "B";
		const std::string VictimId = Index == 0 ? Utf8(FString(kGlassA)) : Utf8(FString(kGlassB));
		const Deed D = LedgerCrime::MakeDeed(Index == 0 ? "crime_a" : "crime_b", "player", VictimId);

		for (std::vector<LedgerCrime::Reading>::size_type I = 0; I < GReadings.size(); ++I)
		{
			LedgerCrime::Reading& R = GReadings[I];
			if (R.EventId != EventId) { continue; }
			LedgerCrime::Resolve(R, D);
			if (!R.bFiled) { continue; }

			// THE RUNG SHE ACTUALLY REACHED DECIDES THE WORDS, both of them.
			// The row's sentence is what she says out loud; the row's clause is
			// what Witness files and what the heard memory repeats. Neither may
			// claim more than the rung she reached, and the bank's spec holds
			// both to the same ceiling.
			if (R.O.Rung > GAchievedRung) { GAchievedRung = R.O.Rung; }
			std::string Id, Text, Clause, Speaker, Why;
			int Variants = 0;
			const int Seed = LedgerCrime::Seed(GNow);
			// THE SENTINEL LIVES IN THE HEADER, where the test that refuses to
			// compose from it lives: two copies of this string would let the
			// producer drift away from the check and the beat would speak a
			// diagnostic.
			std::string Summary = LedgerCrime::UnreadableSummaryPrefix() + GOverheard.WhyNot;
			if (LedgerCrime::BankPick(GBankText, "witness_summary", R.O.Rung, Seed,
			                          Id, Text, Clause, Speaker, Variants, Why))
			{
				// TWO STRINGS, TWO JOBS, queue 157. The SENTENCE is what she
				// says out loud and is the fallback the composer speaks when it
				// refuses. The CLAUSE is what the mill files as the Summary,
				// because both consumers splice it: Gossip.h 586 after "I heard
				// from the shopkeeper that ", and StreetVoice's templates into
				// the middle of a sentence. Filing the sentence is what shipped
				// "I heard from the shopkeeper that He looked straight at me
				// before he ran." in production/d1-probe/ue-crime-memory-n2.md.
				GSummaryText = Text;
				GSummaryClause = Clause.empty() ? std::string("none") : Clause;
				// THE DECISION AND ITS WORDING ARE IN THE HEADER, where g++ runs
				// them: a row with no clause refuses by name through the
				// sentinel the composer already refuses on, and never falls back
				// to the sentence.
				std::string WhyClause;
				Summary = LedgerCrime::SummaryToFile(Id, Clause, WhyClause);
				if (WhyClause != "none") { GOverheard.WhyNot = WhyClause; }
				GOverheard.SummaryId = Id;
				GOverheard.Variants = Variants;
				GOverheard.VariantPicked = LedgerCrime::VariantIndex(Seed, Variants);
				GOverheard.SeedValue = Seed;
				GOverheard.IdRung = R.O.Rung;
			}
			else
			{
				GOverheard.WhyNot = Why;
				GOverheard.SeedValue = Seed;
				GOverheard.IdRung = R.O.Rung;
			}
			if (GMill)
			{
				// A first-hand sighting enters the network at the certainty
				// the resolver measured, which is what everything downstream
				// inherits.
				const Fact Content(std::string("player"), std::string("broke_a_window"), VictimId);
				GMill->Witness(R.WitnessId, Content, Summary, /*bSensitive=*/false, GNow,
				               R.O.Certainty, /*bIndelible=*/false);
			}
		}
	}

	// ---- the ticker ------------------------------------------------------
	bool Tick(float)
	{
		++GTicks;
		const double Now = FPlatformTime::Seconds();
		if (GRunStart == 0.0) { GRunStart = Now; GPhaseStart = Now; GLastTick = Now; }
		const double Delta = Now - GLastTick;
		GLastTick = Now;
		UWorld* World = GameWorld();

		// THE WATCHING CLOCK RUNS UNDER EVERY PHASE INSIDE A CRIME'S WINDOW,
		// including the seconds the pawn stands at the window while a
		// milestone frame is being written: she is looking at him then too,
		// and pretending otherwise would understate the one number the
		// accepting case turns on.
		if (GWatchSlot >= 0) { AccrueWatching(World, Delta); }

		switch (GPhase)
		{
		case ECrimePhase::WaitWorld:
		{
			if (World == nullptr && (Now - GPhaseStart) <= kWorldCeiling) { return true; }
			if (World == nullptr)
			{
				GFinishReason = TEXT("world-ceiling-bit-at-45s");
				Finish();
				return false;
			}
			WriteBreadcrumb(TEXT("world-found"));
			GPhase = ECrimePhase::WaitPawn;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::WaitPawn:
		{
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
			WriteBreadcrumb(TEXT("pawn-found"));
			GPhase = ECrimePhase::SettleAfterSpawn;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::SettleAfterSpawn:
		{
			if ((Now - GPhaseStart) < kSettleAfterSpawn) { return true; }
			GPhase = ECrimePhase::PlaceProps;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::PlaceProps:
		{
			PlaceProps(World);
			LoadBank();
			// The pawn starts at S, facing down the street: +x, which is yaw 0
			// in this engine and in the shared file alike.
			TeleportPawn(World, LedgerCrime::kStartX, LedgerCrime::kStartZ, 0.0);
			WriteBreadcrumb(TEXT("props-placed"));
			GBeat = "start"; GBeatSpeaker = "none"; GBeatLineId = "none"; GBeatHeard = false;
			GPhase = ECrimePhase::ShotStart;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::ShotStart:
			return RunShotPhase(TEXT("start"), TEXT("ue-crime_00_start.png"),
			                    ECrimePhase::ApproachA, Now);
		case ECrimePhase::ApproachA:
		{
			if (GWatchSlot != 0) { GWatchSlot = 0; GBeat = "approach_a"; }
			if (GPawn != nullptr && !GSeqInFlight)
			{
				GPawn->AddMovementInput(GPawn->GetActorForwardVector(), 1.0f);
			}
			MaybeCaptureSequence(Now);
			if ((Now - GPhaseStart) < kApproachSeconds) { return true; }
			GPhase = ECrimePhase::PlaceForA;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::PlaceForA:
		{
			// AT THE WINDOW, FACING IT. Yaw 90 is +z in this engine and in
			// the shared file, which is across the footway into the glass.
			// A1, ruled 2026-09-08: the keys file records the CUT the clip
			// will show. clip-from-frames.py reads only heard and lineId from a
			// row, so a new beat name changes no caption and no selftest.
			GBeat = "at_window_a";
			TeleportPawn(World, LedgerCrime::kCrimeAX, LedgerCrime::kCrimeAZ, 90.0);
			GPhase = ECrimePhase::SettleA;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::SettleA:
		{
			MaybeCaptureSequence(Now);
			if ((Now - GPhaseStart) < kSettleAfterTeleport) { return true; }
			GPhase = ECrimePhase::MeasureA;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::MeasureA:
		{
			// BEFORE THE DEED, WITH THE GLASS STANDING. See this file's
			// header: measuring after the hide inverts the accepting case.
			GReadings.push_back(MeasureVantage(World, "w1", "A", GW1Body, GGlass[0],
			                                   GSeconds[0][0]));
			GReadings.push_back(MeasureVantage(World, "n2", "A", GN2Body, GGlass[0],
			                                   GSeconds[0][1]));
			WriteBreadcrumb(TEXT("vantage-a-measured"));
			GPhase = ECrimePhase::ShotBeforeA;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::ShotBeforeA:
			return RunShotPhase(TEXT("before_crime_a"), TEXT("ue-crime_01_before_crime_a.png"),
			                    ECrimePhase::SeqBeforeA, Now);
		case ECrimePhase::SeqBeforeA:
			return RunForcedSeqPhase(ECrimePhase::CommitA, Now);
		case ECrimePhase::CommitA:
		{
			GBeat = "deed_a";
			CommitDeed(World, 0);
			ResolveAndFile(0);
			GWatchSlot = -1;
			WriteBreadcrumb(TEXT("crime-a-committed"));
			GPhase = ECrimePhase::SeqAfterA;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::SeqAfterA:
			return RunForcedSeqPhase(ECrimePhase::ShotAfterA, Now);
		case ECrimePhase::ShotAfterA:
			return RunShotPhase(TEXT("after_crime_a"), TEXT("ue-crime_02_after_crime_a.png"),
			                    ECrimePhase::Round1, Now);
		case ECrimePhase::Round1:
		{
			// THE ACCEPTING HALF OF THE GOSSIP PAIR'S OPPOSITE: the same two
			// people, the same rumour, the same tie, and nineteen metres of
			// street between them. Nothing may pass.
			RunGossipRound(1, GRound1);
			WriteBreadcrumb(TEXT("gossip-round-1"));
			GPhase = ECrimePhase::MoveW1ToYard;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::MoveW1ToYard:
		{
			MoveBody(World, GW1Body, LedgerCrime::kW1BX, LedgerCrime::kW1BZ);
			FaceBody(GW1Body, LedgerCrime::P3(LedgerCrime::kCrimeBX, 0.0, LedgerCrime::kCrimeBZ));
			GPhase = ECrimePhase::ApproachB;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::ApproachB:
		{
			if (GWatchSlot != 1) { GWatchSlot = 1; GBeat = "approach_b"; }
			if (GPawn != nullptr && !GSeqInFlight)
			{
				// WALKING ON, +x, the direction the street runs. The pawn was
				// left facing the window, so the direction is named rather
				// than taken from its forward vector.
				GPawn->AddMovementInput(FVector(1.0f, 0.0f, 0.0f), 1.0f);
			}
			MaybeCaptureSequence(Now);
			if ((Now - GPhaseStart) < kApproachSeconds) { return true; }
			GPhase = ECrimePhase::PlaceForB;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::PlaceForB:
		{
			// A1, ruled 2026-09-08: the keys file records the CUT the clip
			// will show. clip-from-frames.py reads only heard and lineId from a
			// row, so a new beat name changes no caption and no selftest.
			GBeat = "at_window_b";
			TeleportPawn(World, LedgerCrime::kCrimeBX, LedgerCrime::kCrimeBZ, 90.0);
			GPhase = ECrimePhase::SettleB;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::SettleB:
		{
			MaybeCaptureSequence(Now);
			if ((Now - GPhaseStart) < kSettleAfterTeleport) { return true; }
			GPhase = ECrimePhase::MeasureB;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::MeasureB:
		{
			GReadings.push_back(MeasureVantage(World, "w1", "B", GW1Body, GGlass[1],
			                                   GSeconds[1][0]));
			GReadings.push_back(MeasureVantage(World, "n2", "B", GN2Body, GGlass[1],
			                                   GSeconds[1][1]));
			WriteBreadcrumb(TEXT("vantage-b-measured"));
			GPhase = ECrimePhase::ShotBeforeB;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::ShotBeforeB:
			return RunShotPhase(TEXT("before_crime_b"), TEXT("ue-crime_03_before_crime_b.png"),
			                    ECrimePhase::SeqBeforeB, Now);
		case ECrimePhase::SeqBeforeB:
			return RunForcedSeqPhase(ECrimePhase::CommitB, Now);
		case ECrimePhase::CommitB:
		{
			GBeat = "deed_b";
			CommitDeed(World, 1);
			ResolveAndFile(1);
			GWatchSlot = -1;
			WriteBreadcrumb(TEXT("crime-b-committed"));
			GPhase = ECrimePhase::SeqAfterB;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::SeqAfterB:
			return RunForcedSeqPhase(ECrimePhase::ShotAfterB, Now);
		case ECrimePhase::ShotAfterB:
			return RunShotPhase(TEXT("after_crime_b"), TEXT("ue-crime_04_after_crime_b.png"),
			                    ECrimePhase::Round2, Now);
		case ECrimePhase::Round2:
		{
			RunGossipRound(2, GRound2);
			// THE REPLY, AT THE RUNG SHE REACHED AND NEVER ABOVE IT.
			{
				// NO CLAUSE ON AN OVERHEARD ROW, BY DESIGN: n2's reply is
				// spoken whole and never filed as anybody's Summary, so there
				// is nothing for a splice to get wrong. Clause comes back empty
				// here and nothing reads it.
				std::string Id, Text, Clause, Speaker, Why;
				int Variants = 0;
				const int Seed = LedgerCrime::Seed(GNow);
				if (LedgerCrime::BankPick(GBankText, "overheard", GAchievedRung, Seed,
				                          Id, Text, Clause, Speaker, Variants, Why))
				{
					GReplyText = Text;
					GOverheard.ReplyId = Id;
					GOverheard.Variants = Variants;
					GOverheard.VariantPicked = LedgerCrime::VariantIndex(Seed, Variants);
					GOverheard.SeedValue = Seed;
				}
				else if (GOverheard.WhyNot == "none") { GOverheard.WhyNot = Why; }
			}
			// AND THE EXCHANGE IS COMPOSED, queue 147. The bank above supplied
			// the rung and the id, which is what run 32 measured and what a
			// composed line would otherwise delete; this builds the sentence
			// the two of them actually say, around the summary the mill
			// carried, through the ported StreetVoice.Exchange. A refusal
			// falls back to the bank rows and says why on the verdict.
			GOverheard.Reply = LedgerCrime::ComposeOverheard(
				GCarried, GW1, GN2, LedgerCrime::Seed(GNow),
				GSummaryText == "none" ? std::string() : GSummaryText,
				GReplyText == "none" ? std::string() : GReplyText);
			GOverheard.Events = GRound2.Passed;
			WriteBreadcrumb(TEXT("gossip-round-2"));
			GPhase = ECrimePhase::MoveToOverhear;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::MoveToOverhear:
		{
			// THE PLAYER STANDS IN EARSHOT, facing into the yard: yaw -90 is
			// -z, which is where the two of them are.
			TeleportPawn(World, LedgerCrime::kOverhearX, LedgerCrime::kOverhearZ, -90.0);
			GPhase = ECrimePhase::SettleOverhear;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::SettleOverhear:
		{
			MaybeCaptureSequence(Now);
			if ((Now - GPhaseStart) < kSettleAfterTeleport) { return true; }
			// MEASURED FROM THE PAWN TO EACH BODY, in metres, against the
			// earshot the game itself uses.
			if (GPawn != nullptr && GW1Body != nullptr)
			{
				GOverheard.PlayerToW1M = (double)FVector::Dist(
					GPawn->GetActorLocation(), GW1Body->GetActorLocation()) / 100.0;
			}
			if (GPawn != nullptr && GN2Body != nullptr)
			{
				GOverheard.PlayerToN2M = (double)FVector::Dist(
					GPawn->GetActorLocation(), GN2Body->GetActorLocation()) / 100.0;
			}
			GBeat = "overheard";
			GBeatSpeaker = "w1";
			GBeatLineId = GOverheard.SummaryId;
			GBeatLineText = GOverheard.Reply.TellText;
			GBeatLineTextSource = LedgerCrime::BeatTextSource(GOverheard.Reply, /*bTell=*/true);
			GBeatHeard = GOverheard.Heard();
			GPhase = ECrimePhase::OverheardHold;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::OverheardHold:
		{
			// TWO BEATS, THE WAY THE GAME STAGES THEM: her telling, then his
			// reply a beat later, at GossipDirector's own i * 2.1 seconds.
			if ((Now - GPhaseStart) >= LedgerCrime::kSayAfterSeconds && GBeatSpeaker != "n2")
			{
				GBeatSpeaker = "n2";
				GBeatLineId = GOverheard.ReplyId;
				GBeatLineText = GOverheard.Reply.ReplyText;
				GBeatLineTextSource = LedgerCrime::BeatTextSource(GOverheard.Reply, /*bTell=*/false);
			}
			MaybeCaptureSequence(Now);
			if ((Now - GPhaseStart) < LedgerCrime::kOverheardHoldSeconds) { return true; }
			GPhase = ECrimePhase::ShotOverheard;
			GPhaseStart = Now;
			return true;
		}
		case ECrimePhase::ShotOverheard:
			return RunShotPhase(TEXT("overheard"), TEXT("ue-crime_05_overheard.png"),
			                    ECrimePhase::Done, Now);
		case ECrimePhase::Done:
		default:
			Finish();
			return false;
		}
	}
}

namespace LedgerCrimeProbe
{
	void Start()
	{
		// THE INSTRUMENT'S OWN SELFTEST, RUN ON THE MACHINE THAT RUNS THE
		// PROBE, not only in the container that wrote it. The accepting case
		// is the live decision path; a failure here is printed on the verdict
		// beside everything the run measured, so a decision layer that broke
		// between the container and Jafar's PC cannot pass quietly.
		GSelftest = LedgerCrime::Selftest();

		GGraph = std::make_shared<SocialGraph>();
		GGraph->Link("w1", "n2", LedgerCrime::kTie);
		GMill = std::make_shared<GossipMill>(GGraph);
		// DISPLAY NAMES ARE ARCHETYPES, NOT CAST. Canon's cast baseline is
		// pending and a probe does not mint one; the heard memory line reads
		// "I heard from the shopkeeper that ...".
		GW1 = std::make_shared<Gossiper>("w1", "the shopkeeper",
		                                 std::shared_ptr<MemoryStore>(),
		                                 std::shared_ptr<KnowledgeBase>(), "day");
		GN2 = std::make_shared<Gossiper>("n2", "the lad in the yard",
		                                 std::shared_ptr<MemoryStore>(),
		                                 std::shared_ptr<KnowledgeBase>(), "day");
		GMill->Add(GW1);
		GMill->Add(GN2);

		WriteBreadcrumb(TEXT("start-called"));
		GTicker = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&Tick), 0.0f);
	}
}
