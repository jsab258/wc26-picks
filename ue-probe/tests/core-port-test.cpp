// THE PORTED SIMULATION, COMPILED AND RUN HERE, AGAINST A TABLE THE REAL C#
// WROTE.
//
// WHY THIS EXISTS. The Unreal module cannot be compiled in the container that
// writes it, so anything put there ships UNRUN and the first thing that finds
// out whether it works is a 25-minute round trip on Jafar's PC. The standing
// rule from 25 August is therefore that measurement arithmetic and the
// decisions live where the tests run, and the crime slice is written to that
// rule: Perception, Observation, GameTime, MemoryStore, Suspicion and Gossip
// under LedgerCore have no Unreal type in them, so this file compiles them
// with g++ and runs them before any dispatch.
//
// THE EXPECTATIONS ARE NOT MINE. Every expected value in
// ue-probe/perception-golden.txt is emitted by ledger/PerceptionGolden, which
// compiles the REAL Ledger.Core as shipped and asks it. A port checked
// against numbers its author typed would prove only that the author and the
// port agree; this proves the two ENGINES agree, which is the whole of D1.
//
// WHAT IT CANNOT SEE, said plainly rather than left to be assumed: nothing
// here proves an actor spawns, that a trace hits a terrace, or that a memory
// file lands in a commit. Those are the crime run's business. This proves
// that given the same inputs the C++ answers what the C# answered.
//
//   g++ -std=c++11 -O1 -Wall -I ue-probe/Source/LedgerProbe/Public
//       -I ue-probe/tests/unreal-shim -o /tmp/core-port-test
//       ue-probe/tests/core-port-test.cpp
//       ue-probe/Source/LedgerProbe/Private/Perception.cpp
//   /tmp/core-port-test ue-probe/perception-golden.txt
#include "CoreGolden.h"

#include <cstdio>
#include <fstream>
#include <map>
#include <string>
#include <vector>

using namespace LedgerCore;
using namespace LedgerCore::Golden;

static int gChecks = 0;
static int gFailed = 0;

static void Check(bool Ok, const std::string& What)
{
	++gChecks;
	if (!Ok) { ++gFailed; std::printf("  FAIL %s\n", What.c_str()); }
}

static void Loud(bool Ok, const std::string& What)
{
	Check(Ok, What);
	std::printf("  %s %s\n", Ok ? "ok  " : "FAIL", What.c_str());
}

int main(int argc, char** argv)
{
	const char* Path = argc > 1 ? argv[1] : "ue-probe/perception-golden.txt";
	const double Tol = 1e-9;

	std::ifstream In(Path);
	if (!In.good())
	{
		// NOTHING MEASURED SAYS SO. A missing table must not read the same as
		// a table that agreed.
		std::printf("core-port-test: nothing measured, no golden table at %s\n", Path);
		std::printf("core-port-test: 0 check(s), 1 failure(s)\n");
		return 2;
	}

	// Per function: rows read, rows that disagreed, rows this build does not
	// implement. Every zero below ships the denominator beside it.
	std::map<std::string, int> Rows, Bad, Unknown;
	std::vector<std::string> Order;
	long TotalRows = 0, TotalBad = 0, TotalUnknown = 0;
	std::vector<std::string> Detail;

	std::string Line;
	while (std::getline(In, Line))
	{
		if (!Line.empty() && Line[Line.size() - 1] == '\r') { Line.erase(Line.size() - 1); }
		if (Line.empty() || Line[0] == '#') continue;
		const std::vector<std::string> F = SplitPipe(Line);
		if (F.size() < 3) continue;
		const std::string& Fn = F[0];
		if (Rows.find(Fn) == Rows.end()) { Order.push_back(Fn); Rows[Fn] = 0; Bad[Fn] = 0; Unknown[Fn] = 0; }

		const Answer A = Evaluate(F);
		if (!A.Known)
		{
			++Unknown[Fn]; ++TotalUnknown;
			if (Detail.size() < 10) { Detail.push_back("UNKNOWN-ROW " + Line); }
			continue;
		}
		++Rows[Fn]; ++TotalRows;
		const std::string& Want = F[F.size() - 1];
		if (!Agrees(A.Got, Want, Tol))
		{
			++Bad[Fn]; ++TotalBad;
			if (Detail.size() < 10)
			{
				Detail.push_back("MISMATCH " + Fn + " got=" + A.Got + " want=" + Want + " <- " + Line);
			}
		}
		++gChecks;
		if (!Agrees(A.Got, Want, Tol)) { ++gFailed; }
	}

	std::printf("  golden table: %s\n", Path);
	for (std::vector<std::string>::size_type I = 0; I < Order.size(); ++I)
	{
		const std::string& Fn = Order[I];
		std::printf("    %-22s rows=%d mismatches=%d/%d unknown=%d\n",
		            Fn.c_str(), Rows[Fn], Bad[Fn], Rows[Fn], Unknown[Fn]);
	}
	for (std::vector<std::string>::size_type I = 0; I < Detail.size(); ++I)
	{
		std::printf("    %s\n", Detail[I].c_str());
	}

	// A TABLE THAT LOADED NOTHING MUST NOT READ AS AGREEMENT.
	Loud(TotalRows > 0, "the golden table produced rows to check");
	Loud(TotalBad == 0, "every row the C# emitted is answered the same way here");
	// EVERY ROW IS ANSWERED. A function the table asks about and this build
	// does not implement is a hole in the port, not a neutral fact, and it
	// would otherwise be invisible: an unanswered row cannot fail.
	Loud(TotalUnknown == 0, "no row in the table names a function this build cannot answer");

	// ---- rule 5b: the accepting case is above, and these must REJECT ----
	//
	// A comparison that cannot fail is not a comparison. Each of these plants
	// the condition and checks the harness says no.
	{
		std::vector<std::string> F = SplitPipe("MotionFactor|4|1");
		const Answer A = Evaluate(F);
		Loud(A.Known && Agrees(A.Got, "1", Tol), "a good row agrees");
		Loud(!Agrees(A.Got, "1.5", Tol), "a corrupted expected disagrees");
	}
	{
		const Answer A = Evaluate(SplitPipe("NoSuchFunction|1|2"));
		Loud(!A.Known, "a row naming a function nobody implements reports unknown");
	}
	{
		const Answer A = Evaluate(SplitPipe("Scenario|gossip_crime|noSuchKey|0"));
		Loud(!A.Known, "a scenario key nothing produces reports unknown, not zero");
	}
	{
		Loud(!Agrees("1", "1.000000002", Tol), "the tolerance is a bound and not a shrug");
		Loud(Agrees("full", "full", Tol), "two identical strings agree");
		Loud(!Agrees("full", "Full", Tol), "a string answer compares exactly");
	}
	{
		const std::string S = "a line with a|pipe and\na newline";
		Loud(Unescape(Escape(S)) == S, "the table's escaping round-trips");
		Loud(Escape(S).find(' ') == std::string::npos, "no escaped value carries a space");
	}
	{
		// The formatter the memory markdown is built from, on the value that
		// separates C#'s rule from printf's.
		Loud(FormatTwoDecimals(0.125) == "0.13", "0.125 rounds the way C# rounds it, not the way printf does");
		char Buf[32]; std::snprintf(Buf, sizeof(Buf), "%.2f", 0.125);
		Loud(std::string(Buf) == "0.12", "and printf really does disagree, so the rule is doing work");
	}
	{
		// A2, THE SECOND MEASUREMENT, AND IT CHANGED THE PORT. One ulp below
		// a half is where a fifteen-significant-digit render and a
		// shortest-round-trip render part company, and the golden table's two
		// BitDecrement rows say C# answers 0.13 and 0.14. The first two
		// checks are those answers; the third is the rejecting half, the
		// proof that the rule the port used to carry really does give a
		// different buffer on this input, so the change was load-bearing and
		// not a tidy-up.
		const double A = 0.12499999999999999;   // Math.BitDecrement(0.125)
		const double B = 0.13499999999999998;   // Math.BitDecrement(0.135)
		Loud(FormatTwoDecimals(A) == "0.13", "one ulp below 0.125 still prints 0.13, as C# does");
		Loud(FormatTwoDecimals(B) == "0.14", "one ulp below 0.135 still prints 0.14, as C# does");
		Loud(ShortestRoundTrip(A) != FifteenSignificantDigits(A),
		     "the two candidate rules really do differ here, so the first step matters");
		Loud(FifteenSignificantDigits(A) == "0.125",
		     "and fifteen significant digits is the buffer .NET rounds");
	}
	{
		// The scenarios each produce readings at all. A scenario that built
		// nothing would make every one of its rows unknown rather than wrong,
		// which the total above catches, but naming the count here is what
		// makes the denominator readable.
		int Named = 0, Empty = 0;
		for (int Ix = 0; ScenarioNames(Ix) != 0; ++Ix)
		{
			++Named;
			if (Scenario(ScenarioNames(Ix)).empty()) { ++Empty; }
		}
		std::printf("    scenarios=%d empty=%d/%d\n", Named, Empty, Named);
		Loud(Named > 0 && Empty == 0, "every named scenario builds and reads back");
	}

	std::printf("core-port-test: %d check(s), %d failure(s) over %ld golden row(s), "
	            "%ld mismatch(es), %ld unanswered\n",
	            gChecks, gFailed, TotalRows, TotalBad, TotalUnknown);
	return gFailed == 0 ? 0 : 2;
}
