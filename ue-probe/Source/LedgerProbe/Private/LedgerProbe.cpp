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

#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformProcess.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/DateTime.h"

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
