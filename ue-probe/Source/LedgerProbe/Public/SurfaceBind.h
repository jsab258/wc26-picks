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
#include <cmath>
#include <cstdio>
#include <cstdlib>
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

	// A SEARCH THAT FAILED MUST SAY WHERE IT LOOKED. `texRoot=NOT-FOUND` with
	// nothing beside it cost run 19 a whole round trip: the four directories
	// the binary checked were known only to the binary, so the answer to "is
	// the pack in the wrong place or is the search in the wrong place" was
	// not in the evidence at all.
	//
	// THE SEPARATOR IS A COMMA AND NOT A SLASH. Every candidate here is
	// itself a path full of slashes, so a slash-joined list of paths cannot
	// be split back into the paths it was made from. No spaces, because every
	// reader of this file splits on whitespace.
	//
	// THE CAP ANNOUNCES WHEN IT BITES and is silent when it does not, which
	// is this project's rule: a cap nobody is told about is indistinguishable
	// from a finding.
	inline std::string PathListValue(const std::vector<std::string>& Paths, size_t Cap)
	{
		if (Paths.empty()) { return "nothing-tried"; }
		std::string Out;
		size_t Shown = 0;
		for (size_t I = 0; I < Paths.size() && Shown < Cap; ++I, ++Shown)
		{
			if (Shown > 0) { Out += ","; }
			Out += LedgerVignette::NoSpaces(Paths[I]);
		}
		if (Paths.size() > Shown)
		{
			char Tail[64];
			std::snprintf(Tail, sizeof(Tail), ",+%d-more-not-shown",
			              (int)(Paths.size() - Shown));
			Out += Tail;
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

	// ---- THE FOUR SURFACE NAMES THE PACK CANNOT ANSWER FOR ---------------
	//
	// WHAT THIS SECTION IS AND WHY IT IS NOT A FETCH. The street names sixteen
	// surfaces and the pack carries a file for twelve. Until this section
	// existed the piece loop below SKIPPED every piece whose surface did not
	// resolve, so thirty pieces got no material instance at all and rendered
	// the engine's default: ten card decals, ten multiply decals, six shop
	// interiors and four runs of yellow road paint. The Unity host paints all
	// thirty and has always painted them, by rules that are written down in
	// its own source, and the four missing rules are re-read here rather than
	// invented:
	//
	//   card, multiply      NOT LIBRARY SURFACES AT ALL. They are the two
	//                       DECAL BLEND MODES, declared in words at
	//                       ledger/Assets/Scripts/Core/StreetVignette.cs:57
	//                       and refused at 1651 if they are anything else.
	//                       The picture comes from the piece's own asset
	//                       field under StreamingAssets/Decals. Asking the
	//                       texture root for card.png asks for a file that by
	//                       design can never exist, which is why those two
	//                       surfaces print a blend note here rather than a
	//                       candidate list.
	//   paint_yellow        ProceduralOnly at AssetLibrary.cs:1613, so a pack
	//                       file for it is DELIBERATELY ignored and it renders
	//                       from the SurfaceSpec tint. Dropping a
	//                       paint_yellow.jpg into the pack would make the two
	//                       engines render one surface from two different
	//                       inputs, which is the single thing D1 exists to
	//                       avoid.
	//   interior            No pack file, and Unity needs none: it generates
	//                       from the tint and BORROWS its normal and roughness
	//                       from the window surface by the explicit rule at
	//                       AssetLibrary.cs:611, mapsFrom = logical ==
	//                       Interior ? Window : logical.
	//
	// WHY THE NUMBERS ARE HERE AND WHAT STOPS THEM DRIFTING. Unreal has no
	// way to read a C# table at runtime, so these are a SECOND READER of
	// AssetLibrary.SurfaceSpec and not a second opinion: every value below is
	// the literal from that switch, and tools/surface-tint-check.py parses
	// both files and refuses a disagreement. It is wired into ledger/verify.py
	// as surface_tint_agreement, so it runs before every commit; a grep for
	// its name is what proves that rather than this sentence.
	//
	// IT COMPARES TINTS ONLY. Smoothness, emission, tiling and pattern cross
	// this same boundary and are NOT compared, which the tool prints on its own
	// pass line. Do not read a green from it as a green about the whole table.
	//
	// THIS COMMENT PREVIOUSLY OVER-CLAIMED TWICE and is corrected here rather
	// than quietly rewritten: it said the tool refused "any disagreement" when
	// it compares tints, and that it ran "in the container, before a dispatch"
	// when for the first hour of its life NOTHING CALLED IT AT ALL. A comment
	// promising a guard is not a guard, and it is worse than no guard, because
	// a reader who believes it does not check.
	inline int ProceduralSurfaceCount() { return 2; }

	// THE TINT, IN GAMMA sRGB, WHICH IS THE SPACE THE LITERALS ARE IN. A
	// Unity shader property declared as a Color is converted from gamma to
	// linear on upload, so (0.78, 0.66, 0.18) is a gamma number and every
	// other colour this project shares (the lantern, the practicals) is
	// stated the same way and converted the same way.
	inline const char* ProceduralSurfaceName(int I)
	{
		const char* N[2] = {"interior", "paint_yellow"};
		return (I >= 0 && I < 2) ? N[I] : "out-of-range";
	}

	inline void ProceduralSurfaceTint(int I, double& R, double& G, double& B)
	{
		const double T[2][3] = {{0.18, 0.13, 0.08}, {0.78, 0.66, 0.18}};
		const int J = (I >= 0 && I < 2) ? I : 0;
		R = T[J][0]; G = T[J][1]; B = T[J][2];
	}

	// SMOOTHNESS, FROM THE SAME SWITCH, AND IT BECOMES A ROUGHNESS TEXEL.
	// The base material exposes a roughness MAP and no roughness scalar, so a
	// surface with no pack roughness file gets a flat one built from this
	// number by the same rule AssetLibrary.ResolveGloss uses in reverse
	// (alpha = 255 - roughness, so smoothness and roughness are complements).
	inline double ProceduralSurfaceSmoothness(int I)
	{
		const double S[2] = {0.10, 0.05};
		return (I >= 0 && I < 2) ? S[I] : 0.10;
	}

	inline int ProceduralSurfaceIndex(const std::string& Surface)
	{
		for (int I = 0; I < ProceduralSurfaceCount(); ++I)
		{
			if (Surface == ProceduralSurfaceName(I)) { return I; }
		}
		return -1;
	}

	// THE TWO GRADES EVERY UNITY ALBEDO IS MULTIPLIED BY, AND WHY THEY ARE
	// IN THIS CALCULATION. AssetLibrary.BuildMaterial sets mat.color =
	// BaseColour(logical, textured), which is TextureGrade for any surface
	// carrying a texture, times GroundGrade for the four ground surfaces.
	// Every surface in that host therefore renders its albedo DARKENED, and
	// the Unreal base material has no colour parameter to darken it with, so
	// for the surfaces this section paints the product is baked into the
	// texel. Taken in LINEAR, because that is where Unity's shader takes it.
	//
	// WHAT THIS DOES NOT DO, said here rather than left to be found: the
	// twelve surfaces that resolve from the pack are still bound at full
	// brightness on this side, because baking a grade into a 2048x2048 jpeg
	// is per-texel work on every import and a colour parameter on the base
	// material is the right answer to it. So these two surfaces are now
	// closer to the Unity pair than the twelve around them, the gap is named
	// on the materials line as gradeAppliedTo, and it is one number, not a
	// taste.
	inline void TextureGrade(double& R, double& G, double& B)
	{
		R = 0.74; G = 0.76; B = 0.80;
	}

	inline double GroundGrade() { return 0.55; }

	// THE GROUND FAMILY, AssetLibrary.WetSurfaces, character for character.
	// Neither surface this section paints is in it, and the rule is
	// implemented rather than assumed away: the day a ground surface needs a
	// tint the arithmetic is already right.
	inline bool IsGroundSurface(const std::string& Surface)
	{
		return Surface == "asphalt" || Surface == "sidewalk"
		    || Surface == "kerb" || Surface == "concrete";
	}

	// ONE TEXEL, THE WHOLE OF A PROCEDURAL SURFACE'S ALBEDO ON THIS SIDE.
	//
	// WHAT IT IS A STATISTIC OF: nothing. It is a computed value, printed
	// beside the two inputs it came from so a reader can recompute it.
	//
	// WHAT IT IS NOT. Unity's procedural albedo for paint_yellow is this
	// colour on every texel (the flat pattern), so that one matches; for
	// interior it is this colour with a 0.10 amplitude noise over it, so the
	// Unreal interior is the same colour with no grain in it. NAMED on the
	// surface line as tintPattern, because a flat card where the pair has
	// grain is a difference a judge can see and must not have to discover.
	struct Texel
	{
		int R, G, B;
		Texel() : R(0), G(0), B(0) {}
	};

	inline Texel ProceduralAlbedoTexel(const std::string& Surface)
	{
		Texel T;
		const int I = ProceduralSurfaceIndex(Surface);
		if (I < 0) { return T; }
		double Tr = 0.0, Tg = 0.0, Tb = 0.0;
		ProceduralSurfaceTint(I, Tr, Tg, Tb);
		double Gr = 0.0, Gg = 0.0, Gb = 0.0;
		TextureGrade(Gr, Gg, Gb);
		if (IsGroundSurface(Surface))
		{
			Gr *= GroundGrade(); Gg *= GroundGrade(); Gb *= GroundGrade();
		}
		// THE BYTE FIRST, BECAUSE UNITY STORES THE TINT AS A BYTE. Color32
		// rounds the float literal into a texel and the shader then reads
		// that texel, so the product starts from 199/255 and not from 0.78.
		const double Br = (double)LedgerVignette::ByteOf(Tr) / 255.0;
		const double Bg = (double)LedgerVignette::ByteOf(Tg) / 255.0;
		const double Bb = (double)LedgerVignette::ByteOf(Tb) / 255.0;
		T.R = LedgerVignette::ByteOf(LedgerVignette::LinearToSrgb(
			LedgerVignette::SrgbToLinear(Br) * LedgerVignette::SrgbToLinear(Gr)));
		T.G = LedgerVignette::ByteOf(LedgerVignette::LinearToSrgb(
			LedgerVignette::SrgbToLinear(Bg) * LedgerVignette::SrgbToLinear(Gg)));
		T.B = LedgerVignette::ByteOf(LedgerVignette::LinearToSrgb(
			LedgerVignette::SrgbToLinear(Bb) * LedgerVignette::SrgbToLinear(Gb)));
		return T;
	}

	// THE ROUGHNESS TEXEL FOR A SURFACE WITH NO ROUGHNESS FILE. LINEAR data,
	// never sRGB: a roughness is a number and a gamma curve would bend it.
	inline int ProceduralRoughnessTexel(const std::string& Surface)
	{
		const int I = ProceduralSurfaceIndex(Surface);
		if (I < 0) { return 255; }
		const double Rough = 1.0 - ProceduralSurfaceSmoothness(I);
		return LedgerVignette::ByteOf(Rough);
	}

	// WHICH SURFACE'S MAPS A SURFACE WEARS. AssetLibrary.cs:611 in one line,
	// and it is the reason a lit shop interior reads as glass with a room
	// behind it rather than as a flat card: the interior takes the window's
	// normal and roughness, which is also what keeps the Unity material's
	// keyword set intact.
	inline std::string MapsFrom(const std::string& Surface)
	{
		return (Surface == "interior") ? std::string("window") : Surface;
	}

	// ---- THE TWO DECAL BLENDS, WHICH ARE NOT SURFACES --------------------
	inline bool IsDecalBlend(const std::string& Surface)
	{
		return Surface == "card" || Surface == "multiply";
	}

	inline bool IsMultiplyBlend(const std::string& Surface)
	{
		return Surface == "multiply";
	}

	// THE IMAGE A CARD DECAL ASKS FOR. The Unity host's rule, at
	// StreetVignetteHost.EmitDecal: <Decals>/<id>.png for a card, and a SET
	// DIRECTORY for a multiply (a colour map beside an opacity map, joined by
	// DecalLayer.LoadSet). One extension and no search, because there is one
	// generator and it writes png.
	inline std::string DecalCardLeaf(const std::string& Id)
	{
		return Id + ".png";
	}

	// AND HOW SHINY AN OPAQUE PICTURE IS. StreetVignetteHost.EmitDecal sets
	// _Glossiness 0.08 on a card so a painted signboard takes the street's
	// light like the fascia behind it instead of glowing, and a roughness map
	// is the only way to say that to the base material here. The literal is
	// the Unity host's, read out of it, and checked against it by
	// tools/surface-tint-check.py in the container.
	inline double DecalCardSmoothness() { return 0.08; }

	inline int DecalCardRoughnessTexel()
	{
		return LedgerVignette::ByteOf(1.0 - DecalCardSmoothness());
	}

	// ---- THE ONE THING NO NUMBER IN THIS CONTAINER CAN ANSWER ------------
	//
	// WHICH WAY ROUND THE ENGINE'S PLANE READS ITS UVS. The Unity host draws a
	// decal on DecalLayer.Quad, whose winding the piece list states in words;
	// this side draws it on /Engine/BasicShapes/Plane, and nothing here knows
	// that mesh's uv layout. A lettered fascia arriving mirrored or upside
	// down is the failure, and it is a PICTURE fault that no count can see.
	//
	// So it is a lever rather than a guess: both flips are off, both are
	// printed on the decals done line, and if the first frame shows mirrored
	// lettering the fix is one word here and not a hunt through an emitter.
	// Rule 2 forbids calling either value anything better than the starting
	// point, and the frame is what moves it.
	inline bool DecalFlipRows() { return false; }
	inline bool DecalFlipCols() { return false; }

	// THE CROP, SPLIT OFF THE ASSET STRING, AND IT FAILS CLOSED.
	//
	// The one parser for this is StreetVignette.SplitAsset, tested in Core,
	// and this is the second reader of the same rule: `generated/x#u0,v0,u1,v1`
	// is an image path and a rectangle of it, u then v, v FROM THE BOTTOM, no
	// fragment meaning the whole image. A fragment that is not four numbers
	// returns bOk false and the caller refuses rather than guessing a
	// rectangle, which is what Core does too.
	//
	// WHY THE CROP MATTERS AT ALL: the generated pictures are photographs of
	// a thing IN a street, so fascia_fish_market is a whole shopfront with a
	// pavement and a sky in it. Pasting all of it on a fascia band puts a
	// photograph of a street on a street.
	struct DecalAsset
	{
		std::string Id;
		double U0, V0, U1, V1;
		bool   bOk;
		bool   bCropped;
		DecalAsset() : U0(0), V0(0), U1(1), V1(1), bOk(false), bCropped(false) {}
	};

	inline bool ParseCropNumber(const std::string& S, double& Out)
	{
		if (S.empty()) { return false; }
		for (size_t I = 0; I < S.size(); ++I)
		{
			const char C = S[I];
			const bool bDigit = (C >= '0' && C <= '9');
			if (!bDigit && C != '.' && C != '-' && C != '+'
			    && C != 'e' && C != 'E') { return false; }
		}
		Out = std::strtod(S.c_str(), 0);
		return true;
	}

	inline DecalAsset SplitDecalAsset(const std::string& Asset)
	{
		DecalAsset D;
		D.Id = Asset;
		if (Asset.empty()) { return D; }
		const size_t Hash = Asset.find('#');
		if (Hash == std::string::npos) { D.bOk = true; return D; }
		D.Id = Asset.substr(0, Hash);
		D.bCropped = true;
		const std::string Frag = Asset.substr(Hash + 1);
		std::string Part;
		std::vector<std::string> Parts;
		for (size_t I = 0; I <= Frag.size(); ++I)
		{
			if (I == Frag.size() || Frag[I] == ',')
			{
				Parts.push_back(Part);
				Part.clear();
				continue;
			}
			Part += Frag[I];
		}
		if (Parts.size() != 4) { return D; }
		double V[4] = {0, 0, 1, 1};
		for (int I = 0; I < 4; ++I)
		{
			if (!ParseCropNumber(Parts[(size_t)I], V[I])) { return D; }
		}
		D.U0 = V[0]; D.V0 = V[1]; D.U1 = V[2]; D.V1 = V[3];
		D.bOk = true;
		return D;
	}

	// THE RECTANGLE IN TEXELS, AND THE ROW ORDER IS THE WHOLE OF IT.
	//
	// The crop's v is measured from the BOTTOM of the image and a decoded
	// image's rows arrive TOP DOWN, so the first row of the crop is at
	// (1 - v1) * Height and not at v0 * Height. Getting that backwards would
	// put the sky of a shopfront photograph on a fascia and nothing in a
	// count could see it, which is why it is computed here and asserted
	// against a planted case in the g++ test.
	//
	// IT CLAMPS AND SAYS SO. A rectangle that reaches past the image, or one
	// that is the wrong way round, gives at least one texel rather than a
	// zero-sized upload, and bClamped is what separates a crop that fitted
	// from one that was made to fit.
	struct CropPx
	{
		int  X, Y, W, H;
		bool bClamped;
		CropPx() : X(0), Y(0), W(0), H(0), bClamped(false) {}
	};

	inline CropPx CropPixels(const DecalAsset& D, int ImageW, int ImageH)
	{
		CropPx C;
		if (ImageW <= 0 || ImageH <= 0) { return C; }
		double U0 = D.U0, U1 = D.U1, V0 = D.V0, V1 = D.V1;
		if (U1 < U0) { const double T = U0; U0 = U1; U1 = T; C.bClamped = true; }
		if (V1 < V0) { const double T = V0; V0 = V1; V1 = T; C.bClamped = true; }
		if (U0 < 0.0) { U0 = 0.0; C.bClamped = true; }
		if (V0 < 0.0) { V0 = 0.0; C.bClamped = true; }
		if (U1 > 1.0) { U1 = 1.0; C.bClamped = true; }
		if (V1 > 1.0) { V1 = 1.0; C.bClamped = true; }
		int X0 = (int)(U0 * (double)ImageW + 0.5);
		int X1 = (int)(U1 * (double)ImageW + 0.5);
		// THE FLIP, ONCE, HERE. v from the bottom into a top-down row index.
		int Y0 = (int)((1.0 - V1) * (double)ImageH + 0.5);
		int Y1 = (int)((1.0 - V0) * (double)ImageH + 0.5);
		if (X0 < 0) { X0 = 0; }
		if (Y0 < 0) { Y0 = 0; }
		if (X1 > ImageW) { X1 = ImageW; }
		if (Y1 > ImageH) { Y1 = ImageH; }
		if (X1 <= X0) { X1 = X0 + 1; C.bClamped = true; }
		if (Y1 <= Y0) { Y1 = Y0 + 1; C.bClamped = true; }
		if (X1 > ImageW) { X0 = ImageW - 1; X1 = ImageW; }
		if (Y1 > ImageH) { Y0 = ImageH - 1; Y1 = ImageH; }
		C.X = X0; C.Y = Y0; C.W = X1 - X0; C.H = Y1 - Y0;
		return C;
	}

	// ---- WHICH ROUTE PAINTS A PIECE, DECIDED IN ONE PLACE ----------------
	//
	// THE FAULT THIS REPLACES WAS ONE LINE: a piece whose surface did not
	// resolve to a pack file got `continue` and no material instance at all.
	// Four routes now, and a piece takes exactly one of them, so the tally
	// below adds up to the pieces examined and a reader can see which rule
	// painted what.
	enum EPaintRoute
	{
		Paint_None = 0,        // nothing painted it, and the reason is counted
		Paint_Pack,            // the pack answered for this surface
		Paint_Tint,            // built in code from the SurfaceSpec tint
		Paint_DecalCard,       // the piece's own picture, opaque
		Paint_DecalMultiply    // the piece's own picture, as a stain
	};

	inline const char* PaintRouteName(EPaintRoute R)
	{
		switch (R)
		{
		case Paint_Pack:           return "pack";
		case Paint_Tint:           return "tint";
		case Paint_DecalCard:      return "decal-card";
		case Paint_DecalMultiply:  return "decal-multiply";
		default:                   return "none";
		}
	}

	// THE DECISION, AND THE ORDER IS LOAD-BEARING. A decal blend is tested
	// FIRST, because card and multiply are not library surfaces and a bind
	// record for them can only ever be absent; then the procedural table,
	// because paint_yellow is ProceduralOnly and a pack file for it must be
	// ignored even if one appears; then the pack.
	inline EPaintRoute RouteFor(const std::string& Surface, bool bIsDecalPiece,
	                            bool bBindResolved)
	{
		if (bIsDecalPiece || IsDecalBlend(Surface))
		{
			return IsMultiplyBlend(Surface) ? Paint_DecalMultiply : Paint_DecalCard;
		}
		if (ProceduralSurfaceIndex(Surface) >= 0) { return Paint_Tint; }
		return bBindResolved ? Paint_Pack : Paint_None;
	}

	// ---- WHAT THE RUN PAINTED, AND WHAT IT DID NOT -----------------------
	//
	// WHOLE-RUN COUNTERS, one increment per piece, and the identity the
	// verdict can be checked against is Painted + Unpainted == Examined. Every
	// reason a piece went unpainted is its own counter, because "the pack has
	// no file" and "the image was not staged" and "no modulate material
	// exists" are three findings with three different next actions.
	struct PaintTally
	{
		int Examined;
		int Pack, Tint, DecalCard, DecalMultiply;
		int NoBind, NoActor, NoComponent, NoInstance;
		int DecalImageMissing, DecalCropRefused, DecalNoStainMaterial;
		int Hidden;
		PaintTally() : Examined(0), Pack(0), Tint(0), DecalCard(0), DecalMultiply(0),
		               NoBind(0), NoActor(0), NoComponent(0), NoInstance(0),
		               DecalImageMissing(0), DecalCropRefused(0),
		               DecalNoStainMaterial(0), Hidden(0) {}
	};

	inline int PaintedCount(const PaintTally& T)
	{
		return T.Pack + T.Tint + T.DecalCard + T.DecalMultiply;
	}

	inline int UnpaintedCount(const PaintTally& T)
	{
		return T.NoBind + T.NoActor + T.NoComponent + T.NoInstance
		     + T.DecalImageMissing + T.DecalCropRefused + T.DecalNoStainMaterial;
	}

	// THE SEGMENT THAT CARRIES THE NUMBER THIS WHOLE SECTION EXISTS FOR.
	// piecesUnpainted over the pieces EXAMINED, never over what the file
	// asked for: a run that died halfway must not divide by a denominator it
	// never reached. A run that examined nothing prints the words.
	inline std::string PaintRouteSegment(const PaintTally& T)
	{
		if (T.Examined <= 0)
		{
			return std::string(" piecesUnpainted=nothing-measured"
			                   " piecesPainted=nothing-measured"
			                   " paintRoutes=nothing-measured"
			                   " paintRouteNote=the-piece-loop-examined-no-piece");
		}
		char Buf[700];
		std::snprintf(Buf, sizeof(Buf),
			" piecesPainted=%d/%d piecesUnpainted=%d/%d"
			" paintRoutes=pack.%d/tint.%d/decal-card.%d/decal-multiply.%d"
			" paintUnpaintedWhy=no-pack-file.%d/no-actor.%d/no-component.%d"
			"/instance-refused.%d/decal-image-missing.%d/decal-crop-refused.%d"
			"/decal-needs-a-stain-material.%d"
			" decalQuadsHidden=%d/%d"
			" paintRouteStat=cumulative-over-the-pieces-this-run-examined"
			" paintRouteRule=decal-blend-first/then-the-procedural-table/then-the-pack"
			" paintIdentity=painted-plus-unpainted-equals-examined",
			PaintedCount(T), T.Examined, UnpaintedCount(T), T.Examined,
			T.Pack, T.Tint, T.DecalCard, T.DecalMultiply,
			T.NoBind, T.NoActor, T.NoComponent, T.NoInstance,
			T.DecalImageMissing, T.DecalCropRefused, T.DecalNoStainMaterial,
			T.Hidden, T.DecalCard + T.DecalMultiply + T.DecalImageMissing
			        + T.DecalCropRefused + T.DecalNoStainMaterial);
		return std::string(Buf);
	}

	// ---- ONE LINE PER DECAL PIECE ----------------------------------------
	//
	// PER-SAMPLE NUMBERS ONLY. Which image a quad asked for, what the decoder
	// said it IS, the rectangle that was cut out of it and how big that came
	// out, because "the decal is on the wall" and "the right part of the
	// picture is on the wall" are different facts and only the second one is
	// worth a fascia.
	struct DecalResult
	{
		std::string Piece, Blend, Id, Note, LoadedAs;
		int  FullW, FullH;
		CropPx Crop;
		bool bCropAsked, bLoaded, bPainted, bHidden;
		DecalResult() : FullW(0), FullH(0), bCropAsked(false), bLoaded(false),
		                bPainted(false), bHidden(false) {}
	};

	inline std::string DecalLine(const DecalResult& D)
	{
		std::string Out = "decal=" + LedgerVignette::NoSpaces(D.Piece);
		char Buf[520];
		std::snprintf(Buf, sizeof(Buf),
			" decalBlend=%s decalImage=%s decalStatus=%s",
			LedgerVignette::NoSpaces(D.Blend).c_str(),
			LedgerVignette::NoSpaces(D.Id).c_str(),
			D.bPainted ? "PAINTED" : (D.bHidden ? "HIDDEN" : "NOT-PAINTED"));
		Out += Buf;
		if (D.bLoaded)
		{
			std::snprintf(Buf, sizeof(Buf),
				" decalLoadedAs=%dx%d/%s decalCropPx=x%d..%d/y%d..%d"
				" decalCropSize=%dx%d decalCropAsked=%s decalCropClamped=%s",
				D.FullW, D.FullH,
				D.LoadedAs.empty() ? "unknown"
				                   : LedgerVignette::NoSpaces(D.LoadedAs).c_str(),
				D.Crop.X, D.Crop.X + D.Crop.W, D.Crop.Y, D.Crop.Y + D.Crop.H,
				D.Crop.W, D.Crop.H,
				D.bCropAsked ? "yes" : "whole-image",
				D.Crop.bClamped ? "YES" : "no");
			Out += Buf;
		}
		else
		{
			Out += " decalLoadedAs=not-loaded decalCropPx=not-loaded"
			       " decalCropSize=not-loaded decalCropAsked=not-loaded"
			       " decalCropClamped=not-loaded";
		}
		Out += " decalRowOrder=crop-v-from-the-bottom/image-rows-top-down";
		Out += " decalNote=" + LedgerVignette::NoSpaces(D.Note);
		return Out;
	}

	// AND THE DECAL PASS'S OWN DONE LINE. A pass that reached no decal says
	// so in words: 0 of 0 reads exactly like twenty that worked.
	inline std::string DecalsDoneLine(const std::vector<DecalResult>& All,
	                                  const std::string& Root, int RootFiles,
	                                  const std::vector<std::string>& Tried)
	{
		int Painted = 0, Loaded = 0, Hidden = 0, Cards = 0, Multiplies = 0;
		for (size_t I = 0; I < All.size(); ++I)
		{
			if (All[I].bPainted) { ++Painted; }
			if (All[I].bLoaded)  { ++Loaded; }
			if (All[I].bHidden)  { ++Hidden; }
			if (IsMultiplyBlend(All[I].Blend)) { ++Multiplies; } else { ++Cards; }
		}
		std::string Line;
		if (All.empty())
		{
			Line = "decalsStatus=NOT-REACHED decalsPainted=nothing-measured"
			       " decalsLoaded=nothing-measured decalsHidden=nothing-measured"
			       " decalsNote=the-decal-pass-reached-no-piece";
		}
		else
		{
			char Buf[640];
			std::snprintf(Buf, sizeof(Buf),
				"decalsStatus=%s decalsPainted=%d/%d decalsLoaded=%d/%d"
				" decalsHidden=%d/%d decalsByBlend=card.%d/multiply.%d"
				" decalsStat=cumulative-over-the-decal-pieces-in-the-shared-file"
				" decalsCardRule=the-image-cropped-at-decode-and-bound-opaque"
				" decalsMultiplyRule=a-stain-needs-a-modulate-material-and-this-build-has-one-opaque-base"
				" decalsMultiplyNote=drawn-in-unity-and-hidden-here/the-pair-differs-by-the-grime-until-that-material-exists",
				(Painted == (int)All.size()) ? "ALL"
				                            : (Painted == 0 ? "NONE" : "PARTIAL"),
				Painted, (int)All.size(), Loaded, (int)All.size(),
				Hidden, (int)All.size(), Cards, Multiplies);
			Line = Buf;
		}
		Line += " decalRoot=" + (Root.empty() ? std::string("NOT-FOUND")
		                                      : LedgerVignette::NoSpaces(Root));
		char Tail[180];
		std::snprintf(Tail, sizeof(Tail),
			" decalRootFiles=%d decalFlip=rows.%s/cols.%s"
			" decalFlipNote=a-starting-point-not-a-measurement/the-engine-plane-uv-"
			"winding-is-unknown-here-and-the-frame-answers-it",
			RootFiles, DecalFlipRows() ? "yes" : "no", DecalFlipCols() ? "yes" : "no");
		Line += Tail;
		Line += " decalRootTried=" + PathListValue(Tried, 8);
		return Line;
	}

	// ---- WHAT THE INSTANCE HOLDS, ASKED RATHER THAN ASSUMED --------------
	//
	// THE ENGINE'S OPINION IS A MEASUREMENT. A dynamic material instance can
	// be handed a texture and two scalars and still render the base
	// material's own defaults, and until now nothing in this project has
	// asked an instance what it holds. The engine layer sets a parameter and
	// asks for it straight back in the same statement pair; what the answer
	// MEANS, and every count and string built from it, is decided here where
	// g++ runs it before a dispatch.
	//
	// THE TEXTURE AND THE SCALAR ARE A PAIR AND NEITHER IS READ ALONE. They
	// take different paths into the render proxy, so a full scalar readback
	// beside a short texture one is a finding about the texture path and two
	// short ones are a finding about every path. They are not one number
	// twice, which is the whole reason both are asked for.
	//
	// PER SURFACE, ON THE FIRST INSTANCE MADE FOR IT. 563 pieces would print
	// 563 identical answers to a question that is about the material.
	//
	// WHAT IT CANNOT SEE, SAID PLAINLY RATHER THAN LEFT TO BE ASSUMED: this
	// is the GAME thread's copy of the parameter. A value that lands here and
	// never reaches the render proxy still reads back same-pointer, which is
	// exactly why the control quads below ship in the same dispatch: they are
	// the render side of the same question and they answer in a picture.
	struct Readback
	{
		bool bAsked = false;          // a parameter was actually set on an instance
		bool bTexSame = false;        // what came back IS the pointer that went in
		bool bScalarSame = false;     // BOTH tiling scalars came back as they went in
		bool bResourceValid = false;  // Tex->GetResource() read AFTER UpdateResource
		bool bCompIsMid = false;      // the component renders the instance we made
		// WHAT CAME BACK WHEN IT WAS NOT WHAT WENT IN. The engine's own path
		// name, because "not the same pointer" does not say whether the
		// answer was null, the parent's default texture or something else,
		// and those are three different next actions.
		std::string TexGot  = "not-asked";
		std::string CompGot = "not-asked";
		double SetU = 0.0, GotU = 0.0;
		double SetV = 0.0, GotV = 0.0;
	};

	// ONE TOLERANCE, NAMED, BECAUSE THE ENGINE STORES A FLOAT AND THE FILE
	// CARRIES A DOUBLE. 21.0 survives that trip exactly and 1.371 does not,
	// so an exact comparison would print a mismatch that belongs to the
	// conversion rather than to the engine.
	inline double ScalarEpsilon() { return 1e-4; }

	inline bool ScalarMatches(double Set, double Got)
	{
		const double A = (Set < 0.0) ? -Set : Set;
		const double D = (Set > Got) ? (Set - Got) : (Got - Set);
		return D <= ScalarEpsilon() * ((A > 1.0) ? A : 1.0);
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
		// BORROWED MAPS ARE COUNTED APART FROM FOUND ONES, and that is not
		// pedantry: mapsFound is "this surface's own candidate answered" and
		// the interior's normal and roughness are the WINDOW's files, bound by
		// the rule at AssetLibrary.cs:611. Folding them into MapFound would
		// move mapsFound from 36/48 to 38/48 and change what that number
		// means without changing its name, which is the quietest way there is
		// to lose a reading.
		bool        MapBorrowed[3] = {false, false, false};
		std::string BorrowedFrom;         // the surface the maps came from
		// WHICH RULE PAINTED THIS SURFACE, and the tint it was painted with.
		// Empty Route means the material pass never reached a piece of it.
		std::string Route;
		Texel       Tint;
		bool        bTintBuilt = false;
		double      TileU = 0.0;          // the last piece's tiling, as a sample
		double      TileV = 0.0;
		// WHAT THE FIRST INSTANCE OF THIS SURFACE ANSWERED WHEN ASKED. Kept
		// on the same record the per-surface line and the run totals are both
		// built from, so a total and its lines cannot disagree.
		Readback    Read;
	};

	inline bool IsResolved(const Bound& B) { return B.MapFound[0]; }

	// THE READBACK, PER SURFACE, ON THE SURFACE'S OWN LINE. Per-sample
	// numbers on the sample line; the run's totals are on the done line
	// below and NO KEY MEANS TWO THINGS ON TWO LINES, which is why the
	// scalar reading is midTilingReadback here and midScalarReadback there:
	// one is a word about one surface and the other is a count over the run,
	// and a grep that found either under one name would take whichever line
	// it reached first.
	//
	// A SURFACE NOTHING WAS SET ON PRINTS THE WORDS. A `no` here would say
	// the engine answered wrongly, and "nothing was asked" is a different
	// fact with a different next action.
	inline std::string ReadbackFields(const Readback& R)
	{
		if (!R.bAsked)
		{
			return " midTexReadback=not-asked midTilingReadback=not-asked"
			       " midTexResource=not-asked midCompMaterial=not-asked"
			       " midTilingSetGot=not-asked";
		}
		const std::string TexWord = R.bTexSame
			? std::string("same-pointer")
			: ("OTHER/" + LedgerVignette::NoSpaces(R.TexGot));
		const std::string CompWord = R.bCompIsMid
			? std::string("is-the-instance-we-made")
			: ("OTHER/" + LedgerVignette::NoSpaces(R.CompGot));
		char Buf[220];
		std::snprintf(Buf, sizeof(Buf),
			" midTilingReadback=%s midTexResource=%s"
			" midTilingSetGot=U.%.4f..%.4f/V.%.4f..%.4f",
			R.bScalarSame ? "same-value" : "DIFFERENT",
			R.bResourceValid ? "valid" : "NULL",
			R.SetU, R.GotU, R.SetV, R.GotV);
		return " midTexReadback=" + TexWord + Buf + " midCompMaterial=" + CompWord;
	}

	// THE RUN'S READBACK TOTALS, COUNTED OVER THE SURFACES A PARAMETER WAS
	// ACTUALLY SET ON. That denominator is not the number of surfaces the
	// street asked for: a surface with no albedo file never reaches an
	// instance, and folding it into the denominator would report a bind that
	// never happened as a bind that failed. Both denominators are printed,
	// so neither reading is available only by subtraction.
	//
	// A RUN THAT SET NOTHING PRINTS THE WORDS RATHER THAN A ZERO. `0/0` and
	// "no instance was ever made" read alike to a grep, and this is the
	// difference between an engine that answered wrongly and a pass that
	// never ran.
	inline std::string ReadbackDoneSegment(const std::vector<Bound>& All)
	{
		int Asked = 0, Tex = 0, Scalar = 0, Res = 0, Comp = 0;
		for (size_t I = 0; I < All.size(); ++I)
		{
			if (!All[I].Read.bAsked) { continue; }
			++Asked;
			if (All[I].Read.bTexSame)        { ++Tex; }
			if (All[I].Read.bScalarSame)     { ++Scalar; }
			if (All[I].Read.bResourceValid)  { ++Res; }
			if (All[I].Read.bCompIsMid)      { ++Comp; }
		}
		char Buf[520];
		if (Asked == 0)
		{
			std::snprintf(Buf, sizeof(Buf),
				" midReadbackAsked=0/%d midParamReadback=nothing-measured"
				" midScalarReadback=nothing-measured texResourceValid=nothing-measured"
				" compMaterialIsMid=nothing-measured"
				" midReadbackNote=no-surface-reached-an-instance/nothing-was-set-so-nothing-was-read-back",
				(int)All.size());
			return std::string(Buf);
		}
		std::snprintf(Buf, sizeof(Buf),
			" midReadbackAsked=%d/%d midParamReadback=%d/%d midScalarReadback=%d/%d"
			" texResourceValid=%d/%d compMaterialIsMid=%d/%d"
			" midReadbackStat=per-surface/first-instance-of-that-surface/game-thread-copy-not-the-render-proxy"
			" midReadbackPairRule=both-full-is-candidate-C/scalar-full-and-texture-short-is-B/both-short-is-A",
			Asked, (int)All.size(), Tex, Asked, Scalar, Asked,
			Res, Asked, Comp, Asked);
		return std::string(Buf);
	}

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
		// WHICH OF THE THREE KINDS OF SURFACE THIS IS, ASKED ONCE. A decal
		// blend has no library file by design and a candidate list beside it
		// is a lie with three filenames in it; a procedural surface's albedo
		// is a texel this run computed, and naming the file it did not look
		// for says nothing.
		const bool bBlend = IsDecalBlend(B.Surface);
		const bool bProcedural = (ProceduralSurfaceIndex(B.Surface) >= 0);
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
			else if (B.MapBorrowed[M])
			{
				// THE BORROW IS NAMED WITH THE SURFACE IT CAME FROM, because
				// a normal map on the interior that nobody can attribute is
				// indistinguishable from the interior having its own.
				std::snprintf(Buf, sizeof(Buf),
					" %sFile=%s %sLoadedAs=%dx%d/%s %sParam=%s %sBorrowedFrom=%s",
					MapName(M), LedgerVignette::NoSpaces(B.MapFile[M]).c_str(),
					MapName(M), B.MapW[M], B.MapH[M],
					B.MapLoadedAs[M].empty() ? "unknown"
					                         : LedgerVignette::NoSpaces(B.MapLoadedAs[M]).c_str(),
					MapName(M), MapParam(M), MapName(M),
					LedgerVignette::NoSpaces(B.BorrowedFrom).c_str());
			}
			else if (bBlend)
			{
				std::snprintf(Buf, sizeof(Buf),
					" %sFile=NOT-A-LIBRARY-SURFACE %sTried=nothing/%s-is-a-decal-blend-mode-"
					"and-the-picture-comes-from-the-piece-own-asset-field",
					MapName(M), MapName(M), LedgerVignette::NoSpaces(B.Surface).c_str());
			}
			else if (bProcedural && M == 0)
			{
				std::snprintf(Buf, sizeof(Buf),
					" %sFile=BUILT-IN-CODE %sTried=nothing/this-surface-is-ProceduralOnly-"
					"or-has-no-pack-file-and-the-unity-host-generates-it-from-the-tint",
					MapName(M), MapName(M));
			}
			else
			{
				std::snprintf(Buf, sizeof(Buf),
					" %sFile=ABSENT %sTried=%s",
					MapName(M), MapName(M), CandidateList(B.Surface, M).c_str());
			}
			Out += Buf;
		}
		// THE ROUTE AND THE TEXEL, ON THE LINE THAT NAMES THE SURFACE THEY
		// BELONG TO. A tint nobody can read off the verdict is a number only
		// the source says, and the source is not evidence.
		{
			char Buf[320];
			if (B.bTintBuilt)
			{
				double Tr = 0.0, Tg = 0.0, Tb = 0.0, Gr = 0.0, Gg = 0.0, Gb = 0.0;
				const int ProcIdx = ProceduralSurfaceIndex(B.Surface);
				if (ProcIdx >= 0) { ProceduralSurfaceTint(ProcIdx, Tr, Tg, Tb); }
				TextureGrade(Gr, Gg, Gb);
				std::snprintf(Buf, sizeof(Buf),
					" surfaceRoute=%s tintTexel=%d.%d.%d tintFrom=spec.%.2f.%.2f.%.2f"
					"/grade.%.2f.%.2f.%.2f%s tintPattern=flat-here/%s"
					" roughnessTexel=%d",
					B.Route.empty() ? "none" : LedgerVignette::NoSpaces(B.Route).c_str(),
					B.Tint.R, B.Tint.G, B.Tint.B, Tr, Tg, Tb, Gr, Gg, Gb,
					IsGroundSurface(B.Surface) ? "/groundGrade.0.55" : "",
					B.Surface == "interior" ? "unity-adds-a-0.10-noise-over-it"
					                        : "unity-is-flat-too",
					ProceduralRoughnessTexel(B.Surface));
			}
			else
			{
				std::snprintf(Buf, sizeof(Buf),
					" surfaceRoute=%s tintTexel=not-built tintFrom=not-built"
					" tintPattern=not-built roughnessTexel=not-built",
					B.Route.empty() ? "none" : LedgerVignette::NoSpaces(B.Route).c_str());
			}
			Out += Buf;
		}
		char Tail[200];
		std::snprintf(Tail, sizeof(Tail),
			" tileUVsample=%.2fx%.2f surfaceReason=%s",
			B.TileU, B.TileV, LedgerVignette::NoSpaces(B.Reason).c_str());
		Out += Tail;
		// WHAT THE INSTANCE ANSWERED, ON THE LINE THAT NAMES THE SURFACE IT
		// WAS ASKED ABOUT. A readback with no surface name beside it cannot
		// say which texture was in the question.
		Out += ReadbackFields(B.Read);
		return Out;
	}

	// THE WHOLE-RUN LINE FOR THE MATERIAL PASS. Every tally is computed here,
	// from the same vector the per-surface lines were printed from, so a
	// total and its lines cannot disagree.
	//
	// A PASS THAT BOUND NOTHING SAYS THE WORDS. `surfacesResolved=0/16` with
	// a base material that never loaded and `0/16` with sixteen missing files
	// are different findings, and materialBase is what separates them.
	// TexRootTried is the candidate directories the engine side actually
	// asked the file system about, in the order it asked. The top layer
	// supplies membership and order; the joining, the cap and the words are
	// here, where they are run by g++ before any dispatch.
	inline std::string MaterialsDoneLine(const std::vector<Bound>& All,
	                                     const std::string& BaseMaterialPath,
	                                     bool bBaseLoaded,
	                                     const std::string& TexRoot,
	                                     int TexRootFiles,
	                                     const std::vector<std::string>& TexRootTried,
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
		const int Needed = std::snprintf(Buf, sizeof(Buf),
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
		std::string Line(Buf);
		// SNPRINTF TRUNCATES SILENTLY, and a cut line reads as a short one:
		// the keys past the cut simply are not there, which is exactly what a
		// feature that never ran looks like. The buffer is a cap, so it
		// announces itself when it bites and stays quiet when it does not.
		if (Needed < 0 || (size_t)Needed >= sizeof(Buf))
		{
			Line += " materialsLineCut=yes/at-1100-chars";
		}
		// THE SEARCH PATH GOES ON THE SAME WHOLE-RUN LINE AS ITS RESULT.
		// texRoot says what answered; texRootTried says what was asked, so
		// NOT-FOUND names the directories rather than leaving a reader to
		// read them out of the source of a binary they cannot run. Appended
		// as a string rather than formatted into the buffer above, because
		// four absolute Windows paths are what would push that buffer over.
		Line += " texRootTried=" + PathListValue(TexRootTried, 8);
		// THE RUN'S READBACK TOTALS, COUNTED FROM THE SAME VECTOR THE
		// SURFACE LINES WERE PRINTED FROM. Appended rather than formatted
		// into the buffer above for the reason texRootTried is: the buffer is
		// a cap and a cut line reads as a short one.
		Line += ReadbackDoneSegment(All);
		return Line;
	}

	// ---- THE CONTROL QUADS, WHICH ARE THE ACCEPTING CASE -----------------
	//
	// WHY A CONTROL AT ALL. Every reading in this pass so far is a rejecting
	// one: the street is grey, the bay that carries brick_red renders cooler
	// than neutral where its albedo is warm. Nothing has ever shown this
	// material path WORKING, so there is no accepting case to compare a
	// failure against, and a diagnosis with no accepting case is a lead.
	//
	// WHY THREE AND NOT ONE. The open question is which of an instance's
	// parameters reaches the shader, and one quad answers only the texture
	// half:
	//
	//   colour  a texture BUILT IN CODE, four saturated colours, no file, no
	//           decode and no dependency on the texture root. Four colours on
	//           it means a texture override reaches the sampler and the fault
	//           is in the imported textures or their resources. A grey
	//           checker on it means no texture override reaches the shader.
	//   tile1   no texture override at all, the base material's own default
	//           texture, tiled once.
	//   tile4   the same, with the tiling scalars at four.
	//
	// tile1 AND tile4 SIDE BY SIDE ARE THE SCALAR HALF, AND THEY ARE THE
	// RENDER SIDE OF IT. The readback above can only see the game thread's
	// copy. Two quads of ONE size at ONE distance showing checkers of
	// DIFFERENT cell counts is a scalar override reaching the render proxy;
	// the same cell count on both is either the scalars not arriving or the
	// base material not rendering at all, and both of those are findings
	// about the material rather than about the texture. This is the reading
	// the withdrawn elimination tried to take from two street pieces of
	// unknown world size.
	//
	// PLACED FROM THE CAMERA'S OWN NUMBERS, never from a hard-coded spot, so
	// a camera moved in the spec file takes its controls with it.
	inline int ControlQuadCount() { return 3; }

	inline const char* ControlQuadId(int I)
	{
		const char* N[3] = {"colour", "tile1", "tile4"};
		return (I >= 0 && I < 3) ? N[I] : "out-of-range";
	}

	// THE TILING EACH QUAD ASKS FOR. colour is at one so its four texels are
	// four quadrants and not a chequer of them; tile1 and tile8 differ ONLY
	// here, which is what makes the pair readable.
	// FOUR AND NOT EIGHT, AND THE REASON IS THE MIP CHAIN. A checker tiled
	// densely enough mips down to flat grey, which is the same thing an
	// untextured surface looks like and is exactly the ambiguity that made
	// the street's own cell counts unreadable. Four repeats across a 0.70 m
	// quad at 3.5 m is about thirty pixels a tile in a 1280x720 frame, which
	// is far too coarse to filter away and still four times the other quad.
	inline double ControlQuadTiling(int I)
	{
		const double T[3] = {1.0, 1.0, 4.0};
		return (I >= 0 && I < 3) ? T[I] : 1.0;
	}

	inline bool ControlQuadBindsTexture(int I) { return I == 0; }

	// WHICH SHOTS MAY SEE THE CONTROLS, AND WHY THE ANSWER IS NOT "ALL OF
	// THEM". The quads are an INSTRUMENT: three swatches standing in the
	// carriageway that prove a material instance can be told from the street
	// around it. They are placed 3.5 m in front of the FIRST shot's camera
	// and nothing in that placement knows any other camera exists, so a
	// second camera pointed anywhere near the same stretch of road
	// photographs them. cam_hook, the rung 1 viewpoint, is exactly that
	// case: vignette-spec-test measures one quad's left edge landing at
	// column 1274 of a 1280 wide frame, which is an instrument standing in
	// the picture a person is being asked to judge a street by.
	//
	// So the rule is one line and it lives here, where the test runs, rather
	// than as a condition buried in the shot loop: the controls are visible
	// ONLY in the frames of the camera they were placed from. Every other
	// shot sees the street. This is the same reasoning that already skips
	// them for an interactive build, generalised from one flag to the
	// camera identity that actually decides it.
	inline bool ControlQuadsVisibleFor(const std::string& ShotCameraId,
	                                   const std::string& ControlCameraId)
	{
		if (ShotCameraId.empty() || ControlCameraId.empty()) { return false; }
		return ShotCameraId == ControlCameraId;
	}

	// AND WHAT THE RUN SAYS IT DID, formatted here for the same reason.
	// WHOLE-RUN NUMBERS: how many shots were taken, how many of them had the
	// controls hidden, and the ids of those shots, so "the swatches were not
	// in that frame" is a reading rather than a belief. A run that took no
	// shot prints the words rather than a clean zero.
	inline std::string ControlQuadVisibilityLine(int Shots, int Hidden,
	                                             const std::string& HiddenIds)
	{
		if (Shots <= 0)
		{
			return std::string("controlQuadVisibility=nothing-measured "
			                   "controlQuadHiddenOn=none controlQuadShots=0 "
			                   "controlQuadVisibilityStat=no-shot-reached-the-loop");
		}
		// 512 AND NOT 160. The first version of this line was truncated by
		// snprintf at 160 bytes and g++ said so; a formatter that silently
		// drops its own stat suffix is the quiet instrument failure this
		// project keeps paying for, so the buffer is sized past the longest
		// string this can produce (about 210 bytes plus the ids).
		char Buf[512];
		std::snprintf(Buf, sizeof(Buf),
		              "controlQuadVisibility=hidden-for-every-shot-whose-camera-is-not-"
		              "the-one-they-were-placed-from controlQuadHidden=%d/%d "
		              "controlQuadHiddenOn=%s controlQuadVisibilityStat=cumulative-over-"
		              "the-shots-this-run-took",
		              Hidden, Shots, HiddenIds.empty() ? "none" : HiddenIds.c_str());
		return std::string(Buf);
	}

	// STATED CONVENTIONS, PRINTED BESIDE THE NUMBERS THEY PRODUCED. None of
	// these is a measured bound. The distance is far enough that a 0.70 m
	// quad is about a sixth of the frame height and near enough that the
	// four colours are unmistakable in a 1280x720 still.
	inline double ControlQuadAheadM()  { return 3.5; }
	inline double ControlQuadSizeM()   { return 0.70; }
	inline double ControlQuadPitchM()  { return 1.00; }  // centre to centre
	inline double ControlQuadFirstM()  { return 0.50; }  // first centre off the axis

	// THE ROW SITS TO THE CAMERA'S LEFT, AND THAT IS A DECISION ABOUT THE
	// EVIDENCE FRAME rather than about the engine. At cam_A the right of the
	// frame is the shopfront the street is read for and the left is open
	// carriageway, so the controls stand over the carriageway and leave the
	// half a reader is judging the street from alone. Negative is left,
	// because the camera's right is the file's +z after the yaw.
	inline double ControlQuadOffsetM(int I)
	{
		return -(ControlQuadFirstM() + ControlQuadPitchM() * (double)I);
	}

	// WHERE ONE QUAD GOES, IN BOTH FRAMES AT ONCE. The metres are the file's
	// frame and are what the projection below reads; the centimetres are the
	// engine's and are what the emitter spawns at. The conversion happens
	// HERE so the top layer, which no test in this container can run, never
	// does arithmetic.
	//
	// THE ROTATION IS THE ENGINE'S AND IS DERIVED, NOT GUESSED. A pitch of
	// +90 takes the plane's local +Z, which is its normal, onto world -X, and
	// the yaw then turns that onto the reverse of the camera's own forward,
	// so the quad faces the camera at any yaw. Under the same pair the
	// plane's local X lands on world up and its local Y on the camera's
	// right, which is the frame the corners below are taken in.
	struct QuadPlace
	{
		std::string Id;
		double XM = 0.0, YM = 0.0, ZM = 0.0;        // file frame, metres
		double XCm = 0.0, YCm = 0.0, ZCm = 0.0;     // engine frame, centimetres
		double EnginePitchDeg = 90.0, EngineYawDeg = 0.0, EngineRollDeg = 0.0;
		double SizeM = 0.0, TileU = 1.0, TileV = 1.0;
		bool   bBindTexture = false;
	};

	inline double DegToRad(double D) { return D * 3.14159265358979323846 / 180.0; }

	inline QuadPlace ControlQuadPlace(const LedgerVignette::Camera& C, int I)
	{
		QuadPlace Q;
		Q.Id = ControlQuadId(I);
		Q.SizeM = ControlQuadSizeM();
		Q.TileU = ControlQuadTiling(I);
		Q.TileV = ControlQuadTiling(I);
		Q.bBindTexture = ControlQuadBindsTexture(I);
		const double Yaw = DegToRad(C.YawDeg);
		// THE CAMERA'S OWN AXES IN THE FILE'S FRAME. Engine yaw turns about
		// up, so forward is (cos,0,sin) and right is (-sin,0,cos) in the
		// file's (x, y, z) with y up.
		const double Fx = std::cos(Yaw), Fz = std::sin(Yaw);
		const double Rx = -std::sin(Yaw), Rz = std::cos(Yaw);
		const double Ahead = ControlQuadAheadM();
		const double Off = ControlQuadOffsetM(I);
		Q.XM = C.X + Fx * Ahead + Rx * Off;
		Q.ZM = C.Z + Fz * Ahead + Rz * Off;
		// CENTRED ON THE VIEW AXIS RATHER THAN AT A FIXED HEIGHT. The file's
		// camera pitch is positive DOWN, so the axis has fallen by
		// Ahead*tan(pitch) at the row's distance and a quad at eye height
		// would sit above the middle of the frame.
		Q.YM = C.GroundY + C.EyeHeightM - Ahead * std::tan(DegToRad(C.PitchDeg));
		Q.XCm = Q.XM * 100.0;
		Q.YCm = Q.ZM * 100.0;   // the file's z is the engine's Y
		Q.ZCm = Q.YM * 100.0;   // the file's y is the engine's Z
		Q.EnginePitchDeg = 90.0;
		Q.EngineYawDeg = C.YawDeg;
		Q.EngineRollDeg = 0.0;
		return Q;
	}

	// ---- WHERE IT LANDS ON THE FRAME -------------------------------------
	//
	// A PINHOLE PROJECTION AND NOTHING MORE, and it is named as a model
	// rather than a reading: it is the same camera the spec file describes,
	// with no lens, no aspect constraint beyond the fov conversion the
	// emitter already uses, and no engine in the loop. It says where the quad
	// SHOULD land so a reader can find it in the still; the still is what
	// says what colour it is.
	struct ScreenAt
	{
		double Px = 0.0, Py = 0.0;
		double ForwardM = 0.0;
		bool   bAhead = false;
	};

	inline ScreenAt ProjectFilePoint(const LedgerVignette::Camera& C,
	                                 double XM, double YM, double ZM, int W, int H)
	{
		ScreenAt S;
		const double Yaw = DegToRad(C.YawDeg);
		// THE ENGINE'S PITCH IS POSITIVE UP AND THE FILE'S IS POSITIVE DOWN,
		// which is the same negation PlaceCamera does before it hands the
		// rotation to the engine.
		const double Pitch = DegToRad(-C.PitchDeg);
		const double Ex = C.X, Ey = C.GroundY + C.EyeHeightM, Ez = C.Z;
		const double Dx = XM - Ex, Dy = YM - Ey, Dz = ZM - Ez;
		const double Fx = std::cos(Pitch) * std::cos(Yaw);
		const double Fz = std::cos(Pitch) * std::sin(Yaw);
		const double Fy = std::sin(Pitch);
		const double Rx = -std::sin(Yaw), Rz = std::cos(Yaw), Ry = 0.0;
		const double Ux = -std::sin(Pitch) * std::cos(Yaw);
		const double Uz = -std::sin(Pitch) * std::sin(Yaw);
		const double Uy = std::cos(Pitch);
		const double Fwd = Dx * Fx + Dy * Fy + Dz * Fz;
		const double Rgt = Dx * Rx + Dy * Ry + Dz * Rz;
		const double Upd = Dx * Ux + Dy * Uy + Dz * Uz;
		S.ForwardM = Fwd;
		S.bAhead = (Fwd > 0.001);
		if (!S.bAhead) { return S; }
		const double TanH = std::tan(DegToRad(
			LedgerVignette::HorizontalFovDeg(C.FovVerticalDeg, W, H) * 0.5));
		const double TanV = std::tan(DegToRad(C.FovVerticalDeg * 0.5));
		S.Px = (double)W * (0.5 + 0.5 * (Rgt / Fwd) / TanH);
		S.Py = (double)H * (0.5 - 0.5 * (Upd / Fwd) / TanV);
		return S;
	}

	// THE BOX IS THE BOUNDING BOX OF FOUR PROJECTED CORNERS, not a width
	// scaled off the centre: the quad is flat and off-axis, so its projection
	// is a quadrilateral and a symmetric box round the centre would be a
	// drawing rather than a measurement. cornersAhead ships beside it,
	// because a box computed from two corners in front and two behind is not
	// a box.
	struct ScreenBox
	{
		bool   bMeasured = false;
		double CxPx = 0.0, CyPx = 0.0;
		double X0 = 0.0, X1 = 0.0, Y0 = 0.0, Y1 = 0.0;
		double DistM = 0.0;
		int    CornersAhead = 0;
		int    CornersInFrame = 0;
	};

	inline ScreenBox ControlQuadBox(const LedgerVignette::Camera& C,
	                                const QuadPlace& Q, int W, int H)
	{
		ScreenBox B;
		const double Yaw = DegToRad(C.YawDeg);
		const double Rx = -std::sin(Yaw), Rz = std::cos(Yaw);
		const double Half = Q.SizeM * 0.5;
		const ScreenAt Mid = ProjectFilePoint(C, Q.XM, Q.YM, Q.ZM, W, H);
		B.DistM = Mid.ForwardM;
		B.CxPx = Mid.Px;
		B.CyPx = Mid.Py;
		if (!Mid.bAhead) { return B; }
		for (int S = 0; S < 4; ++S)
		{
			const double SideSign = (S == 0 || S == 1) ? 1.0 : -1.0;
			const double UpSign   = (S == 0 || S == 2) ? 1.0 : -1.0;
			const ScreenAt P = ProjectFilePoint(
				C, Q.XM + Rx * Half * SideSign,
				Q.YM + Half * UpSign,
				Q.ZM + Rz * Half * SideSign, W, H);
			if (!P.bAhead) { continue; }
			if (B.CornersAhead == 0)
			{
				B.X0 = B.X1 = P.Px;
				B.Y0 = B.Y1 = P.Py;
			}
			else
			{
				if (P.Px < B.X0) { B.X0 = P.Px; }
				if (P.Px > B.X1) { B.X1 = P.Px; }
				if (P.Py < B.Y0) { B.Y0 = P.Py; }
				if (P.Py > B.Y1) { B.Y1 = P.Py; }
			}
			++B.CornersAhead;
			if (P.Px >= 0.0 && P.Px <= (double)W && P.Py >= 0.0 && P.Py <= (double)H)
			{
				++B.CornersInFrame;
			}
		}
		B.bMeasured = (B.CornersAhead == 4);
		return B;
	}

	// ---- DOES THIS SHOT'S OWN WHOLE-FRAME NUMBERS INCLUDE THE INSTRUMENT --
	//
	// A1(d), amendment 1 of
	// game-design/decision-2026-09-09-ruling-the-grid-batch-review.md, and it
	// is a DECLARATION ON THE SAMPLE LINE rather than a coverage measurement.
	// The distinction is the whole point. shotMeanLuma, the exposure bands and
	// band.ground are means over every pixel of the frame, so on the camera
	// the control quads were placed from they include three saturated swatches
	// standing in the carriageway, and the reader of a grid cell has no way to
	// tell from the line which frames carry them. The earlier ruling dictated
	// this as a literal string with pixel boxes and a percentage measured once
	// for one camera at one field of view; the review narrowed it, because a
	// measurement frozen as a literal inside an emit is a number nobody can
	// re-measure. So the boxes are PROJECTED HERE, by ControlQuadPlace and
	// ProjectFilePoint, the same two functions the tests exercise, from
	// whatever camera the file carries.
	//
	// WHAT THE PERCENTAGE IS AND IS NOT. It is the union of the three
	// projected boxes, clipped to the frame, over the frame area: an AT-MOST
	// bound on how much of the picture the swatches can own, and it overstates
	// that coverage because a bounding box is not a quad and three boxes that
	// overlap are counted once only through their union. It is not a pixel
	// readback, nothing here looked at a frame, and the key says so in its own
	// stat string. Covering the frame is what a still answers.
	//
	// IT FAILS CLOSED ON IDENTITY. A shot whose camera or control camera did
	// not answer prints nothing-measured rather than "no", because "no" is a
	// claim about a frame and silence is not.
	inline std::string ShotControlQuadLine(const LedgerVignette::Camera& ShotCam,
	                                       const std::string& ControlCameraId,
	                                       int QuadsSpawned,
	                                       bool bWholeFrameKeysOnThisLine,
	                                       int W, int H)
	{
		const std::string Key = "shotWholeFrameIncludesControlQuads=";
		if (!bWholeFrameKeysOnThisLine)
		{
			return Key + "nothing-measured/this-line-carries-no-whole-frame-keys";
		}
		if (ShotCam.Id.empty() || ControlCameraId.empty())
		{
			return Key + "nothing-measured/no-camera-identity-answered";
		}
		if (QuadsSpawned <= 0)
		{
			return Key + "no/no-control-quads-were-spawned-in-this-build";
		}
		if (!ControlQuadsVisibleFor(ShotCam.Id, ControlCameraId))
		{
			return Key + "no/hidden-for-this-camera";
		}
		// THE QUADS ARE VISIBLE ONLY IN THE FRAMES OF THE CAMERA THEY WERE
		// PLACED FROM, which ControlQuadsVisibleFor has just established, so
		// the placement camera and the shooting camera are the same camera and
		// the projection below is taken from the one this shot used.
		double X0 = 0.0, X1 = 0.0, Y0 = 0.0, Y1 = 0.0;
		int Boxed = 0;
		const int Asked = ControlQuadCount();
		for (int I = 0; I < Asked; ++I)
		{
			const QuadPlace P = ControlQuadPlace(ShotCam, I);
			const ScreenBox B = ControlQuadBox(ShotCam, P, W, H);
			if (!B.bMeasured) { continue; }
			if (Boxed == 0) { X0 = B.X0; X1 = B.X1; Y0 = B.Y0; Y1 = B.Y1; }
			else
			{
				if (B.X0 < X0) { X0 = B.X0; }
				if (B.X1 > X1) { X1 = B.X1; }
				if (B.Y0 < Y0) { Y0 = B.Y0; }
				if (B.Y1 > Y1) { Y1 = B.Y1; }
			}
			++Boxed;
		}
		std::string Out = Key
			+ "yes/whole-frame-keys-on-this-line-include-them"
			  "/boxes=see-controlQuadVisibility-and-the-quad-lines"
			  "/PROJECTED-BOXES-NOT-MEASURED-COVERAGE";
		char Buf[520];
		if (Boxed == 0)
		{
			std::snprintf(Buf, sizeof(Buf),
				" shotControlQuadsBoxed=0/of=%d/quads-with-four-corners-ahead"
				" shotControlQuadsBoxPx=nothing-measured/no-quad-projected-with-all-four-"
				"corners-ahead shotControlQuadsAtMostPctOfFrame=nothing-measured"
				" shotControlQuadsBoxStat=per-sample/projected-by-ControlQuadPlace-and-"
				"ProjectFilePoint/not-a-pixel-readback",
				Asked);
			Out += Buf;
			return Out;
		}
		const double CX0 = X0 < 0.0 ? 0.0 : (X0 > (double)W ? (double)W : X0);
		const double CX1 = X1 < 0.0 ? 0.0 : (X1 > (double)W ? (double)W : X1);
		const double CY0 = Y0 < 0.0 ? 0.0 : (Y0 > (double)H ? (double)H : Y0);
		const double CY1 = Y1 < 0.0 ? 0.0 : (Y1 > (double)H ? (double)H : Y1);
		const double Area = (CX1 - CX0) * (CY1 - CY0);
		const double Frame = (double)W * (double)H;
		const double Pct = (Frame > 0.0 && Area > 0.0) ? (Area * 100.0 / Frame) : 0.0;
		std::snprintf(Buf, sizeof(Buf),
			" shotControlQuadsBoxed=%d/of=%d/quads-with-four-corners-ahead"
			" shotControlQuadsBoxPx=x%.0f..%.0f/y%.0f..%.0f shotControlQuadsFrame=%dx%d"
			" shotControlQuadsAtMostPctOfFrame=%.2f"
			" shotControlQuadsBoxStat=per-sample/union-of-the-projected-boxes-clipped-to-"
			"the-frame/AT-MOST-because-a-box-is-not-a-quad/projected-by-ControlQuadPlace-"
			"and-ProjectFilePoint/not-a-pixel-readback",
			Boxed, Asked, X0, X1, Y0, Y1, W, H, Pct);
		Out += Buf;
		return Out;
	}

	// ---- THE FOUR COLOURS ------------------------------------------------
	//
	// SATURATED AND FAR APART, ON PURPOSE. The frame this is read against
	// tops out at chroma 15 and the warmest albedo in the pack means 32, so
	// a control that renders at chroma 20 would prove nothing. Every one of
	// these is at the corner of the cube: whatever the light and the tone
	// mapper do to them, four channel orderings this far apart cannot all
	// collapse onto the neutral grey the street is rendering now.
	inline int ControlColourCount() { return 4; }

	inline void ControlColour(int I, int& R, int& G, int& B)
	{
		const int V[4][3] = {{255, 0, 0}, {0, 255, 0}, {0, 0, 255}, {255, 255, 0}};
		const int J = (I >= 0 && I < 4) ? I : 0;
		R = V[J][0]; G = V[J][1]; B = V[J][2];
	}

	inline const char* ControlColourName(int I)
	{
		const char* N[4] = {"red", "green", "blue", "yellow"};
		return (I >= 0 && I < 4) ? N[I] : "out-of-range";
	}

	// THE BUFFER ORDER, AND IT IS NAMED AS THE BUFFER'S rather than as the
	// screen's. Texel 0 is the first in the row-major upload, which is the
	// texture's own origin; which screen corner that lands on depends on the
	// mesh's UV layout and this header does not assert one. The reading the
	// run needs is that four saturated colours appear at all.
	inline const char* ControlTexelSlot(int I)
	{
		const char* N[4] = {"texel0", "texel1", "texel2", "texel3"};
		return (I >= 0 && I < 4) ? N[I] : "out-of-range";
	}

	inline std::string ControlColoursValue()
	{
		std::string Out;
		for (int I = 0; I < ControlColourCount(); ++I)
		{
			int R = 0, G = 0, B = 0;
			ControlColour(I, R, G, B);
			char Buf[64];
			std::snprintf(Buf, sizeof(Buf), "%s%s.%s.%d.%d.%d",
			              I > 0 ? "/" : "", ControlTexelSlot(I),
			              ControlColourName(I), R, G, B);
			Out += Buf;
		}
		return Out;
	}

	// ---- WHAT THE EMITTER ANSWERED FOR ONE QUAD --------------------------
	//
	// The top layer fills this in with live state only: whether an actor
	// came back, whether the instance was made, what the engine said when
	// asked for the parameter back, and WHERE THE ACTOR ACTUALLY IS, read
	// off the actor rather than repeated from the request. Every count,
	// difference and word below is computed here.
	struct QuadResult
	{
		bool bSpawned = false;
		bool bMidMade = false;
		bool bTexMade = false;
		bool bTexResource = false;
		bool bTexReadback = false;
		bool bCompIsMid = false;
		bool bRead = false;                    // the actor answered for its transform
		double ReadXCm = 0.0, ReadYCm = 0.0, ReadZCm = 0.0;
		std::string Note = "none";
	};

	inline double QuadDeltaCm(const QuadPlace& P, const QuadResult& R)
	{
		if (!R.bRead) { return -1.0; }
		const double Dx = R.ReadXCm - P.XCm;
		const double Dy = R.ReadYCm - P.YCm;
		const double Dz = R.ReadZCm - P.ZCm;
		return std::sqrt(Dx * Dx + Dy * Dy + Dz * Dz);
	}

	// ONE LINE PER QUAD. Per-sample numbers only; the run's totals are on the
	// quads' own done line below.
	inline std::string ControlQuadLine(const LedgerVignette::Camera& C,
	                                   const QuadPlace& P, const QuadResult& R,
	                                   int W, int H)
	{
		const ScreenBox B = ControlQuadBox(C, P, W, H);
		const double Delta = QuadDeltaCm(P, R);
		std::string Out = "controlQuad=" + LedgerVignette::NoSpaces(P.Id);
		char Head[520];
		std::snprintf(Head, sizeof(Head),
			" quadStatus=%s quadMid=%s quadTexture=%s quadTexResource=%s"
			" quadTexReadback=%s quadCompMaterial=%s quadTiling=%.2fx%.2f quadSizeM=%.2f",
			R.bSpawned ? "SPAWNED" : "SPAWN-FAILED",
			R.bMidMade ? "made" : "NOT-MADE",
			P.bBindTexture ? (R.bTexMade ? "2x2-built-in-code/BGRA8/srgb.yes/filter.nearest"
			                             : "2x2-BUILD-FAILED")
			               : "none-bound/the-base-material-default",
			P.bBindTexture ? (R.bTexResource ? "valid" : "NULL") : "not-asked",
			P.bBindTexture ? (R.bTexReadback ? "same-pointer" : "OTHER-OR-NULL") : "not-asked",
			R.bCompIsMid ? "is-the-instance-we-made" : "OTHER",
			P.TileU, P.TileV, P.SizeM);
		Out += Head;
		// ASKED AND READ BACK, BOTH, because asking for a transform and
		// printing the transform you asked for is not evidence that anything
		// moved. An actor that did not answer prints the words rather than
		// repeating the request as though it were a reading.
		char Where[320];
		if (R.bRead)
		{
			std::snprintf(Where, sizeof(Where),
				" quadAskedXYZcm=%.1f/%.1f/%.1f quadReadXYZcm=%.1f/%.1f/%.1f"
				" quadDeltaCm=%.2f",
				P.XCm, P.YCm, P.ZCm, R.ReadXCm, R.ReadYCm, R.ReadZCm, Delta);
		}
		else
		{
			std::snprintf(Where, sizeof(Where),
				" quadAskedXYZcm=%.1f/%.1f/%.1f quadReadXYZcm=not-read"
				" quadDeltaCm=not-read",
				P.XCm, P.YCm, P.ZCm);
		}
		Out += Where;
		char Screen[420];
		std::snprintf(Screen, sizeof(Screen),
			" quadOn=%s/%dx%d quadCentrePx=%.0f/%.0f quadBoxPx=x%.0f..%.0f/y%.0f..%.0f"
			" quadDistM=%.2f quadCornersAhead=%d/4 quadCornersInFrame=%d/4"
			" quadProjection=pinhole-from-the-spec-camera/not-an-engine-readback",
			LedgerVignette::NoSpaces(C.Id).c_str(), W, H,
			B.CxPx, B.CyPx, B.X0, B.X1, B.Y0, B.Y1,
			B.DistM, B.CornersAhead, B.CornersInFrame);
		Out += Screen;
		Out += " quadTexels=" + ControlColoursValue();
		Out += std::string(" quadReads=") + (P.bBindTexture
			? "four-colours-means-a-texture-override-reaches-the-sampler/checker-means-it-does-not"
			: "cell-count-against-the-other-tile-quad/differing-means-the-scalars-reach-the-shader");
		Out += " quadNote=" + LedgerVignette::NoSpaces(R.Note);
		return Out;
	}

	// THE QUADS' OWN DONE LINE. Whole-run numbers only, and a pass that
	// spawned nothing says the words rather than printing a clean 0/0.
	inline std::string ControlQuadsDoneLine(const std::vector<QuadResult>& All,
	                                        bool bBaseLoaded)
	{
		const int Asked = ControlQuadCount();
		int Spawned = 0, Mids = 0;
		for (size_t I = 0; I < All.size(); ++I)
		{
			if (All[I].bSpawned) { ++Spawned; }
			if (All[I].bMidMade) { ++Mids; }
		}
		if (All.empty())
		{
			char Buf[420];
			std::snprintf(Buf, sizeof(Buf),
				"controlQuadsStatus=NOT-REACHED controlQuads=nothing-measured/%d"
				" controlQuadMids=nothing-measured controlQuadColours=%s"
				" controlQuadsNote=the-control-pass-never-ran",
				Asked, ControlColoursValue().c_str());
			return std::string(Buf);
		}
		char Buf[520];
		std::snprintf(Buf, sizeof(Buf),
			"controlQuadsStatus=%s controlQuads=%d/%d controlQuadMids=%d/%d"
			" controlQuadBase=%s controlQuadColours=%s"
			" controlQuadsStat=counts-over-the-controls-this-build-asks-for"
			" controlQuadsRule=the-colour-quad-answers-the-texture-path/the-two-tile-quads-answer-the-scalar-path",
			(Spawned == Asked && Mids == Asked) ? "ALL"
			                                    : (Spawned == 0 ? "NONE" : "PARTIAL"),
			Spawned, Asked, Mids, Asked,
			bBaseLoaded ? "loaded" : "MISSING",
			ControlColoursValue().c_str());
		return std::string(Buf);
	}
}
