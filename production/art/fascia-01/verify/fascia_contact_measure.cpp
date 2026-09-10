// STATION 3 VERIFY for the fascia package: the measurement queue 228 asks for
// FIRST, and it is not the one the burial gate answers.
//
// WHAT THIS IS AND WHAT IT IS NOT. It is not an instrument. It gates nothing,
// prints no verdict key, is wired into no build, and lives under
// production/art/fascia-01/ beside the package's own authoring recipe rather
// than under tools/ or ue-probe/. Jafar's ruling of 2026-09-09 is that no new
// instrument is built for the art lane this week, and this obeys it: it is one
// measurement taken once, the same status as author/make_fascia_mouldings.py.
//
// WHY IT HAD TO BE WRITTEN. Queue 228 says, in as many words, that the
// measurement to make first is WHETHER THE CONSOLE'S OWN BOUNDS SIT INSIDE THE
// CORNICE'S BOUNDS, which is a different question from the one the gate
// answers. The gate answers: what fraction of a prop's own FOOTPRINT has its
// TOP inside another placed piece's bounds, and how far the covering piece's
// top stands above that top. Those are both facts about what is OVER the prop.
// Neither of them can tell RESTING ON from SUNK INTO, because in both cases
// something sits above the prop's top.
//
// THE MISSING HALF, WHICH IS THE WHOLE FINDING. For a prop top T and a
// straddling cover spanning [Cmin, Cmax]:
//   the gate prints   Cmax - T, how much cover stands above me;
//   nothing prints    T - Cmin, HOW FAR OF ME IS INSIDE IT.
// T - Cmin is the penetration. It is zero exactly when the cover's underside
// and the prop's top are the same plane, which is what a bracket carrying a
// cornice IS. This file prints both halves and the AABB intersection volume
// with them, because a volume of zero is the unarguable form of the same
// statement.
//
// THE PREDICATE IS NOT REIMPLEMENTED HERE. This includes
// ue-probe/Source/LedgerProbe/Public/VignetteSpec.h and calls its
// BurialCandidates, SpecBoxBounds and ReadBurialCell, so the straddle test
// asked here is the same code the engine run asks, down to the half-open
// interval. A second copy of a predicate is the site nobody fixes; the header
// says so itself and this file takes it at its word.
//
//   g++ -std=c++11 -O1 -Wall -I ue-probe/Source/LedgerProbe/Public \
//       -o fascia_contact_measure \
//       production/art/fascia-01/verify/fascia_contact_measure.cpp
//   ./fascia_contact_measure production/specs/vignette-pieces.json
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "VignetteSpec.h"

using namespace LedgerVignette;

namespace
{
	// ONE PAIR, AND EVERY NUMBER THAT SEPARATES RESTING FROM SUNK.
	struct ContactRead
	{
		std::string On, By;
		double PropTopM;
		double CoverMinM, CoverMaxM;
		double CoverAboveMm;    // Cmax - T, WHICH IS THE NUMBER THE GATE PRINTS
		double PenetrationMm;   // T - Cmin, WHICH IS THE NUMBER NOTHING PRINTS
		double OverlapVolM3;    // the two world AABBs, intersected
		bool   bInsideX, bInsideY, bInsideZ;  // prop's own span inside the cover's
		int    Cells;           // cells of the prop's footprint this cover straddles
	};

	double Span(double AMin, double AMax, double BMin, double BMax)
	{
		const double Lo = AMin > BMin ? AMin : BMin;
		const double Hi = AMax < BMax ? AMax : BMax;
		return Hi > Lo ? Hi - Lo : 0.0;
	}

	bool Within(double AMin, double AMax, double BMin, double BMax)
	{
		return AMin >= BMin - 1e-9 && AMax <= BMax + 1e-9;
	}
}

int main(int argc, char** argv)
{
	const char* SpecPath = (argc > 1) ? argv[1] : "production/specs/vignette-pieces.json";
	std::ifstream In(SpecPath, std::ios::binary);
	if (!In)
	{
		std::printf("FAILED: cannot open %s\n", SpecPath);
		return 2;
	}
	std::ostringstream Buf;
	Buf << In.rdbuf();
	const std::string Text = Buf.str();

	Spec S;
	std::string Err;
	if (!ParseSpec(Text, S, Err))
	{
		std::printf("FAILED: %s did not parse: %s\n", SpecPath, Err.c_str());
		return 2;
	}

	std::vector<PlacedBox> All;
	All.reserve(S.Pieces.size());
	for (size_t I = 0; I < S.Pieces.size(); ++I)
	{
		All.push_back(SpecBoxBounds(S.Pieces[I]));
	}
	std::printf("spec=%s pieces=%d/of=%d-in-the-header\n",
	            SpecPath, (int)All.size(), S.HeaderPieces);

	// EVERY PROP, EVERY PIECE THAT STRADDLES ITS TOP, BOTH HALVES.
	std::vector<ContactRead> Reads;
	int PropsExamined = 0, PropsWithCover = 0;
	for (size_t I = 0; I < All.size(); ++I)
	{
		if (!All[I].bProp) { continue; }
		++PropsExamined;
		const PlacedBox& P = All[I];
		std::vector<size_t> Cand;
		BurialCandidates(All, I, Cand);
		// Per covering piece, how many cells of this prop's footprint it
		// straddles, asked through the header's own cell reader.
		const int Side = BurialGridSide();
		std::vector<int> CellsPer(Cand.size(), 0);
		for (int IX = 0; IX < Side; ++IX)
		{
			for (int IZ = 0; IZ < Side; ++IZ)
			{
				const double CX = BurialCellX(P, IX), CZ = BurialCellZ(P, IZ);
				for (size_t K = 0; K < Cand.size(); ++K)
				{
					const PlacedBox& C = All[Cand[K]];
					if (!C.SpansXZ(CX, CZ)) { continue; }
					if (C.MinY <= P.MaxY) { ++CellsPer[K]; }
				}
			}
		}
		bool bAny = false;
		for (size_t K = 0; K < Cand.size(); ++K)
		{
			if (CellsPer[K] <= 0) { continue; }
			bAny = true;
			const PlacedBox& C = All[Cand[K]];
			ContactRead R;
			R.On = P.Name; R.By = C.Name;
			R.PropTopM = P.MaxY;
			R.CoverMinM = C.MinY; R.CoverMaxM = C.MaxY;
			R.CoverAboveMm = (C.MaxY - P.MaxY) * 1000.0;
			R.PenetrationMm = (P.MaxY - C.MinY) * 1000.0;
			R.OverlapVolM3 = Span(P.MinX, P.MaxX, C.MinX, C.MaxX)
			               * Span(P.MinY, P.MaxY, C.MinY, C.MaxY)
			               * Span(P.MinZ, P.MaxZ, C.MinZ, C.MaxZ);
			R.bInsideX = Within(P.MinX, P.MaxX, C.MinX, C.MaxX);
			R.bInsideY = Within(P.MinY, P.MaxY, C.MinY, C.MaxY);
			R.bInsideZ = Within(P.MinZ, P.MaxZ, C.MinZ, C.MaxZ);
			R.Cells = CellsPer[K];
			Reads.push_back(R);
		}
		if (bAny) { ++PropsWithCover; }
	}

	std::printf("propsExamined=%d propsWithACoverOverTheirTop=%d/of=%d coverPairs=%d\n",
	            PropsExamined, PropsWithCover, PropsExamined, (int)Reads.size());
	if (Reads.empty())
	{
		std::printf("coverPairs=nothing-measured/0 "
		            "no-prop-in-this-file-has-a-piece-straddling-its-top\n");
		return 0;
	}

	std::printf("\nEVERY COVER PAIR, both halves, no cap:\n");
	std::printf("  %-28s %-32s %9s %9s %9s %11s %s\n",
	            "on", "by", "propTopM", "coverAbMm", "penetrMm", "overlapM3", "propSpanInsideCover(x/y/z)");
	int Contacts = 0, Sunk = 0;
	double WorstPen = -1.0; std::string WorstPenOn = "none", WorstPenBy = "none";
	for (size_t I = 0; I < Reads.size(); ++I)
	{
		const ContactRead& R = Reads[I];
		// RESTING OR SUNK, AND THE BOUND IS NOT A TOLERANCE. Zero is zero
		// here: the piece list is quantised to six decimals of a metre, so a
		// coincident face is exactly coincident and 1e-9 m separates a face
		// contact from anything a reader could call a penetration.
		const bool bContact = R.PenetrationMm <= 1e-6;
		if (bContact) { ++Contacts; } else { ++Sunk; }
		if (R.PenetrationMm > WorstPen)
		{
			WorstPen = R.PenetrationMm; WorstPenOn = R.On; WorstPenBy = R.By;
		}
		std::printf("  %-28s %-32s %9.6f %9.2f %9.2f %11.8f %s/%s/%s %s cells=%d/400\n",
		            R.On.c_str(), R.By.c_str(), R.PropTopM,
		            R.CoverAboveMm, R.PenetrationMm, R.OverlapVolM3,
		            R.bInsideX ? "in" : "out", R.bInsideY ? "in" : "out",
		            R.bInsideZ ? "in" : "out",
		            bContact ? "RESTING-ON" : "SUNK-INTO", R.Cells);
	}

	std::printf("\ncontactPairs=%d/of=%d sunkPairs=%d/of=%d "
	            "penetrationWorstMm=%.2f/on=%s/by=%s/at-worst-over-every-cover-pair\n",
	            Contacts, (int)Reads.size(), Sunk, (int)Reads.size(),
	            WorstPen, WorstPenOn.c_str(), WorstPenBy.c_str());
	std::printf("penetrationStat=prop-top-minus-cover-bottom/"
	            "the-half-the-burial-gate-does-not-print/"
	            "zero-means-the-two-faces-are-one-plane-and-none-of-the-prop-is-inside-the-cover\n");
	std::printf("coverAboveStat=cover-top-minus-prop-top/"
	            "the-half-the-burial-gate-DOES-print-as-deepestMm/"
	            "it-is-the-covers-own-height-above-me-and-not-a-depth-of-mine\n");

	// THE PACKAGE'S OWN QUESTION, ASKED BY NAME, so that a reader does not
	// have to pick the fascia rows out of the table above.
	int FasciaPairs = 0, FasciaContacts = 0;
	double FasciaWorstPen = 0.0, FasciaWorstVol = 0.0;
	for (size_t I = 0; I < Reads.size(); ++I)
	{
		if (Reads[I].On.find("fascia_console") == std::string::npos) { continue; }
		if (Reads[I].By.find("fascia_cornice") == std::string::npos) { continue; }
		++FasciaPairs;
		if (Reads[I].PenetrationMm <= 1e-6) { ++FasciaContacts; }
		if (Reads[I].PenetrationMm > FasciaWorstPen) { FasciaWorstPen = Reads[I].PenetrationMm; }
		if (Reads[I].OverlapVolM3 > FasciaWorstVol) { FasciaWorstVol = Reads[I].OverlapVolM3; }
	}
	if (FasciaPairs == 0)
	{
		std::printf("consoleInsideCornice=nothing-measured/0 "
		            "no-console-and-cornice-pair-is-in-this-file\n");
		return 0;
	}
	std::printf("consoleUnderCornicePairs=%d consoleRestingOnCornice=%d/of=%d "
	            "consolePenetrationWorstMm=%.6f consoleOverlapVolWorstM3=%.8f "
	            "consoleInsideCornice=%s\n",
	            FasciaPairs, FasciaContacts, FasciaPairs,
	            FasciaWorstPen, FasciaWorstVol,
	            (FasciaContacts == FasciaPairs && FasciaWorstVol <= 1e-12) ? "NO" : "YES");
	return 0;
}
