// THE D1 PROBE'S TEST: does the C++ transliteration agree with the C# Core.
//
// It reads perception-golden.txt, emitted by ledger/PerceptionGolden from the
// REAL Core as shipped, and checks every row to 1e-9. A port that compiles
// proves nothing, and a port tested against assertions somebody rewrote in
// C++ proves only that two transliterations agree. One source of truth,
// consumed by the thing under test.
//
// IT CARRIES ITS DENOMINATOR. "0 mismatches" is meaningless without the row
// count, and a golden file that failed to load would otherwise pass by having
// nothing to check, so zero rows FAILS loudly.
#include "Perception.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

using namespace LedgerCore;

static std::vector<std::string> Split(const std::string& S, char Sep)
{
	std::vector<std::string> Out;
	std::string Cur;
	std::istringstream Stream(S);
	while (std::getline(Stream, Cur, Sep)) Out.push_back(Cur);
	return Out;
}

static double D(const std::string& S) { return std::strtod(S.c_str(), nullptr); }
static bool   B(const std::string& S) { return S == "1"; }

int main(int Argc, char** Argv)
{
	const char* Path = (Argc > 1) ? Argv[1] : "perception-golden.txt";
	std::ifstream In(Path);
	if (!In)
	{
		std::printf("perceptionGolden=UNREADABLE path=%s\n", Path);
		std::printf("probeTest=FAIL reason=golden-table-not-found\n");
		return 2;
	}

	long Rows = 0, Bad = 0, Unknown = 0;
	const double Tol = 1e-9;
	std::string Line;
	while (std::getline(In, Line))
	{
		if (Line.empty() || Line[0] == '#') continue;
		const std::vector<std::string> F = Split(Line, '|');
		if (F.size() < 3) continue;
		++Rows;
		const std::string& Fn = F[0];
		double Got = 0.0, Want = 0.0;

		if (Fn == "MotionFactor")             { Got = Perception::MotionFactor(D(F[1])); Want = D(F[2]); }
		else if (Fn == "ConeWeight")          { Got = Perception::ConeWeight(D(F[1]));   Want = D(F[2]); }
		else if (Fn == "LightFactor")         { Got = Perception::LightFactor(D(F[1]));  Want = D(F[2]); }
		else if (Fn == "FacingIsReadable")    { Got = Perception::FacingIsReadable(D(F[1]), D(F[2])) ? 1 : 0; Want = D(F[3]); }
		else if (Fn == "InSight")             { Got = Perception::InSight(D(F[1]), D(F[2]), D(F[3]), B(F[4]), D(F[5])) ? 1 : 0; Want = D(F[6]); }
		else if (Fn == "IdRung")              { Got = Perception::IdRung(D(F[1]), D(F[2]), D(F[3]), B(F[4]), B(F[5])); Want = D(F[6]); }
		else if (Fn == "SymmetryPredictsSeen"){ Got = Perception::SymmetryPredictsSeen(D(F[1]), D(F[2]), D(F[3]), D(F[4]), B(F[5])) ? 1 : 0; Want = D(F[6]); }
		else { ++Unknown; --Rows; continue; }

		if (std::fabs(Got - Want) > Tol)
		{
			++Bad;
			// Name the row. A mismatch count with no row is a number nobody
			// can act on; ten is enough to see the pattern.
			if (Bad <= 10) std::printf("  MISMATCH %s got=%.17g want=%.17g <- %s\n", Fn.c_str(), Got, Want, Line.c_str());
		}
	}

	if (Rows == 0)
	{
		std::printf("perceptionGolden=0 rows read from %s\n", Path);
		std::printf("probeTest=FAIL reason=golden-table-empty\n");
		return 2;
	}
	if (Unknown > 0) std::printf("  note: %ld row(s) named a function this build does not implement\n", Unknown);
	std::printf("perceptionRows=%ld perceptionMismatches=%ld tolerance=%g\n", Rows, Bad, Tol);
	std::printf("probeTest=%s\n", Bad == 0 ? "PASS" : "FAIL");
	return Bad == 0 ? 0 : 1;
}
