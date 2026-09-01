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

	void RunGoldenTest()
	{
		const FString GoldenPath = FPaths::Combine(FPaths::ProjectDir(), TEXT("perception-golden.txt"));
		const FString OutPath    = FPaths::Combine(FPaths::ProjectDir(), TEXT("golden-result.txt"));

		// A BREADCRUMB, WRITTEN BEFORE ANY WORK. Run 6 exited 3 in six seconds
		// with no file at all, and "the module never loaded" and "the module
		// loaded and the test died" looked identical from the outside. They
		// have completely different next actions. This costs one write and
		// makes them distinguishable: no file means startup was never reached,
		// a file holding only this line means it was reached and the test
		// did not finish.
		FFileHelper::SaveStringToFile(
			FString::Printf(TEXT("moduleStartup=reached projectDir=%s\nprobeTest=FAIL reason=test-did-not-finish\n"),
			                *FPaths::ConvertRelativePathToFull(FPaths::ProjectDir())),
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
		RunGoldenTest();
		// Ask the engine to quit rather than sitting in a game loop on
		// somebody's desktop. The workflow also passes -unattended.
		FPlatformMisc::RequestExit(false);
	}
};

IMPLEMENT_PRIMARY_GAME_MODULE(FLedgerProbeModule, LedgerProbe, "LedgerProbe");
