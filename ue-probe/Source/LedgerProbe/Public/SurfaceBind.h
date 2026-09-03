// PHASE C: WHICH SURFACE GOT A TEXTURE, IN A FILE THAT COMPILES WITHOUT
// UNREAL.
//
// WHAT THIS IS FOR. The street's 593 pieces carry sixteen surface names and
// the shared city pack carries a file per surface. Binding them is engine
// work; deciding WHICH FILE a surface asks for, counting what resolved and
// printing the answer is not, and it lives here for the standing reason: in
// a project whose top layer does not compile locally, a formatter written
// there ships UNRUN, and an unrun formatter printing a plausible string is
// the quietest instrument fault there is.
//
// THE FILENAME RULE IS THE UNITY HOST'S RULE, READ OUT OF IT RATHER THAN
// INVENTED HERE. AssetLibrary.LoadPackTexture tries `<logical><ext>` under
// StreamingAssets/CityPack/textures for `.png`, `.jpg`, `.jpeg` IN THAT
// ORDER; ResolveNormal and ResolveGloss try `<logical>_n<ext>` and
// `<logical>_r<ext>` the same way. D1 is a comparison, and an engine that
// picked a different file for the same surface name would not be comparing
// anything. There is one mapping and this is a second READER of it, not a
// second copy: the surface names come out of the shared pieces file and the
// suffixes are the three above.
//
// A PHASE C THAT RENDERS AND CANNOT SAY WHAT IT FAILED TO LOAD IS WORTH LESS
// THAN ONE THAT LOADS LESS AND SAYS SO. Every absent surface is NAMED with
// the candidates that were tried and how many pieces wear it, and every zero
// ships the count of what was examined.
//
// WHAT EACH NUMBER IS A STATISTIC OF:
//   Pieces          pieces in the shared file carrying this surface name
//   PiecesAssigned  of those, how many actually got a material instance
//   Resolved        surfaces whose ALBEDO file was found, decoded and bound
//   LoadedAs        what the decoder said the file IS, not what its name says
#pragma once

#include "VignetteSpec.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

namespace LedgerSurface
{
	// THE EXTENSION ORDER IS THE UNITY HOST'S, character for character.
	inline int ExtCount() { return 3; }
	inline const char* Ext(int I)
	{
		const char* E[3] = {".png", ".jpg", ".jpeg"};
		return (I >= 0 && I < 3) ? E[I] : "";
	}

	// THE THREE MAPS A SURFACE CAN CARRY, named once. The suffix is what the
	// pack's filenames use; the parameter is what the base material exposes,
	// and the two are printed together so a mismatch is visible from the
	// verdict rather than only from a grey frame.
	inline int MapCount() { return 3; }
	inline const char* MapSuffix(int I)
	{
		const char* S[3] = {"", "_n", "_r"};
		return (I >= 0 && I < 3) ? S[I] : "";
	}
	inline const char* MapParam(int I)
	{
		const char* P[3] = {"BaseColorMap", "NormalMap", "RoughnessMap"};
		return (I >= 0 && I < 3) ? P[I] : "";
	}
	inline const char* MapName(int I)
	{
		const char* N[3] = {"albedo", "normal", "roughness"};
		return (I >= 0 && I < 3) ? N[I] : "";
	}

	// EVERY FILENAME A SURFACE WOULD ACCEPT FOR ONE MAP, in the order they
	// are tried. Printed into the verdict for an absent surface, so "not
	// found" says what was looked for rather than leaving a reader to guess.
	inline std::vector<std::string> Candidates(const std::string& Surface, int MapIndex)
	{
		std::vector<std::string> Out;
		for (int E = 0; E < ExtCount(); ++E)
		{
			Out.push_back(Surface + MapSuffix(MapIndex) + Ext(E));
		}
		return Out;
	}

	inline std::string CandidateList(const std::string& Surface, int MapIndex)
	{
		const std::vector<std::string> C = Candidates(Surface, MapIndex);
		std::string Out;
		for (size_t I = 0; I < C.size(); ++I)
		{
			if (I > 0) { Out += "/"; }
			Out += C[I];
		}
		return Out;
	}

	// WHAT THE FILE ASKED FOR, WHICH IS THE DENOMINATOR. Derived from the
	// pieces rather than hard-coded, so a surface added to the street next
	// week enlarges the denominator instead of vanishing from the report.
	// Sorted, so two runs print their surfaces in the same order.
	struct Ask
	{
		std::string Surface;
		int         Pieces = 0;
	};

	inline std::vector<Ask> SurfacesAsked(const std::vector<LedgerVignette::Piece>& Pieces)
	{
		std::vector<Ask> Out;
		for (size_t I = 0; I < Pieces.size(); ++I)
		{
			const std::string& S = Pieces[I].Surface;
			if (S.empty()) { continue; }
			bool bFound = false;
			for (size_t J = 0; J < Out.size(); ++J)
			{
				if (Out[J].Surface == S) { ++Out[J].Pieces; bFound = true; break; }
			}
			if (!bFound)
			{
				Ask A;
				A.Surface = S;
				A.Pieces = 1;
				Out.push_back(A);
			}
		}
		for (size_t I = 0; I + 1 < Out.size(); ++I)
		{
			for (size_t J = I + 1; J < Out.size(); ++J)
			{
				if (Out[J].Surface < Out[I].Surface) { std::swap(Out[I], Out[J]); }
			}
		}
		return Out;
	}

	// HOW MANY TIMES A TEXTURE REPEATS ACROSS A PIECE.
	//
	// THE ENGINE'S BASIC SHAPES CARRY 0..1 UVS, so a 42 metre carriageway
	// with no tiling shows ONE asphalt tile stretched forty-two metres, which
	// is not a photograph of a road. The two largest dimensions of the piece
	// are the ones a camera in the street sees: a 42.0 x 0.3 x 2.7 road slab
	// is seen along 42 and across 2.7, and its 0.3 thickness is the edge.
	// THIS IS A SIMPLIFICATION AND IS NAMED AS ONE on the verdict: it is not
	// per-face UVs, and a piece whose visible face is its smallest pair will
	// tile wrongly. MetresPerTile is a stated convention, not a measured
	// bound; it is printed beside the numbers it produced.
	struct Tiling
	{
		double U = 1.0;
		double V = 1.0;
	};

	inline Tiling TilingFor(const LedgerVignette::Piece& P, double MetresPerTile)
	{
		Tiling T;
		if (MetresPerTile <= 0.0) { return T; }
		double D[3] = {P.SX, P.SY, P.SZ};
		for (int I = 0; I < 3; ++I) { if (D[I] < 0.0) { D[I] = -D[I]; } }
		std::sort(D, D + 3);            // ascending, so D[2] and D[1] are the pair
		const double A = D[2], B = D[1];
		T.U = (A > 0.0) ? (A / MetresPerTile) : 1.0;
		T.V = (B > 0.0) ? (B / MetresPerTile) : 1.0;
		if (T.U < 1.0) { T.U = 1.0; }   // never below one repeat: a fraction of
		if (T.V < 1.0) { T.V = 1.0; }   // a tile is a crop, not a surface
		return T;
	}

	// ONE SURFACE'S OUTCOME. Status is set by the caller because the ways to
	// fail are different facts with different next actions: a file that is
	// not in the pack, a file the decoder refused, and a base material that
	// never loaded are three separate findings and none of them is "the
	// texture did not help".
	struct Bound
	{
		std::string Surface;
		int         Pieces = 0;           // pieces in the file wearing this surface
		int         PiecesAssigned = 0;   // of those, how many got an instance
		std::string Status = "NOT-REACHED";
		std::string Reason = "none";
		bool        MapFound[3] = {false, false, false};
		std::string MapFile[3];
		int         MapW[3] = {0, 0, 0};
		int         MapH[3] = {0, 0, 0};
		std::string MapLoadedAs[3];       // what the DECODER said it is
		double      TileU = 0.0;          // the last piece's tiling, as a sample
		double      TileV = 0.0;
	};

	inline bool IsResolved(const Bound& B) { return B.MapFound[0]; }

	// ONE LINE PER SURFACE. Per-surface numbers only; the run's totals are on
	// the done line below, so no key means two different things on two lines.
	//
	// A SURFACE THAT RESOLVED PRINTS WHAT EACH MAP LOADED AS, not what its
	// filename claims. An `.hdr` that imports as a 2D texture and a `.jpg`
	// that decodes at half size are both invisible to a name.
	inline std::string SurfaceLine(const Bound& B)
	{
		char Head[420];
		std::snprintf(Head, sizeof(Head),
			"surface %s surfaceStatus=%s pieces=%d piecesAssigned=%d/%d",
			LedgerVignette::NoSpaces(B.Surface).c_str(),
			LedgerVignette::NoSpaces(B.Status).c_str(),
			B.Pieces, B.PiecesAssigned, B.Pieces);
		std::string Out(Head);
		for (int M = 0; M < MapCount(); ++M)
		{
			char Buf[420];
			if (B.MapFound[M])
			{
				std::snprintf(Buf, sizeof(Buf),
					" %sFile=%s %sLoadedAs=%dx%d/%s %sParam=%s",
					MapName(M), LedgerVignette::NoSpaces(B.MapFile[M]).c_str(),
					MapName(M), B.MapW[M], B.MapH[M],
					B.MapLoadedAs[M].empty() ? "unknown"
					                         : LedgerVignette::NoSpaces(B.MapLoadedAs[M]).c_str(),
					MapName(M), MapParam(M));
			}
			else
			{
				std::snprintf(Buf, sizeof(Buf),
					" %sFile=ABSENT %sTried=%s",
					MapName(M), MapName(M), CandidateList(B.Surface, M).c_str());
			}
			Out += Buf;
		}
		char Tail[200];
		std::snprintf(Tail, sizeof(Tail),
			" tileUVsample=%.2fx%.2f surfaceReason=%s",
			B.TileU, B.TileV, LedgerVignette::NoSpaces(B.Reason).c_str());
		Out += Tail;
		return Out;
	}

	// THE WHOLE-RUN LINE FOR THE MATERIAL PASS. Every tally is computed here,
	// from the same vector the per-surface lines were printed from, so a
	// total and its lines cannot disagree.
	//
	// A PASS THAT BOUND NOTHING SAYS THE WORDS. `surfacesResolved=0/16` with
	// a base material that never loaded and `0/16` with sixteen missing files
	// are different findings, and materialBase is what separates them.
	inline std::string MaterialsDoneLine(const std::vector<Bound>& All,
	                                     const std::string& BaseMaterialPath,
	                                     bool bBaseLoaded,
	                                     const std::string& TexRoot,
	                                     int TexRootFiles,
	                                     int PiecesInFile,
	                                     int TexturesImported,
	                                     int MidsCreated,
	                                     double MetresPerTile)
	{
		int Resolved = 0, Assigned = 0, PiecesUnderResolved = 0, MapsFound = 0, MapsAsked = 0;
		std::string Absent;
		for (size_t I = 0; I < All.size(); ++I)
		{
			MapsAsked += MapCount();
			for (int M = 0; M < MapCount(); ++M) { if (All[I].MapFound[M]) { ++MapsFound; } }
			Assigned += All[I].PiecesAssigned;
			if (IsResolved(All[I]))
			{
				++Resolved;
				PiecesUnderResolved += All[I].Pieces;
			}
			else
			{
				if (!Absent.empty()) { Absent += "/"; }
				Absent += LedgerVignette::NoSpaces(All[I].Surface);
			}
		}
		if (Absent.empty()) { Absent = "none"; }
		const int Asked = (int)All.size();
		char Buf[1100];
		std::snprintf(Buf, sizeof(Buf),
			"materialsStatus=%s materialBase=%s materialBasePath=%s "
			"surfacesAsked=%d surfacesResolved=%d/%d surfacesAbsent=%s "
			"mapsFound=%d/%d texturesImported=%d midsCreated=%d "
			"piecesTextured=%d/%d piecesUnderResolvedSurfaces=%d/%d "
			"texRoot=%s texRootFiles=%d metresPerTile=%.2f "
			"tilingModel=two-largest-dimensions/not-per-face-uvs "
			"materialsStat=counts-over-what-the-shared-file-asked-for",
			Asked == 0 ? "NOTHING-ASKED"
			           : (!bBaseLoaded ? "NO-BASE-MATERIAL"
			                           : (Resolved == Asked ? "ALL"
			                                                : (Resolved == 0 ? "NONE" : "PARTIAL"))),
			bBaseLoaded ? "loaded" : "MISSING",
			LedgerVignette::NoSpaces(BaseMaterialPath).c_str(),
			Asked, Resolved, Asked, Absent.c_str(),
			MapsFound, MapsAsked, TexturesImported, MidsCreated,
			Assigned, PiecesInFile, PiecesUnderResolved, PiecesInFile,
			TexRoot.empty() ? "NOT-FOUND" : LedgerVignette::NoSpaces(TexRoot).c_str(),
			TexRootFiles, MetresPerTile);
		return std::string(Buf);
	}
}
