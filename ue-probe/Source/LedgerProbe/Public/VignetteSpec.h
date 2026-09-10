// THE SHARED STREET, READ IN A FILE THAT COMPILES WITHOUT UNREAL.
//
// WHAT THIS IS FOR. D1 compares two engines, and the comparison is only
// worth running if every difference in a judged pair is a RENDERER
// difference. So the layout is done ONCE, in Ledger.Core, and written to
// production/specs/vignette-pieces.json; Unity consumes the plan in memory
// and Unreal consumes that file. NOTHING HERE DECIDES A DIMENSION. If a
// number reaches the Unreal scene that is not in the file, that is a bug in
// this header.
//
// WHY IT HAS NO UNREAL TYPE IN IT, ruled standing on 25 August after the
// third instance: measurement arithmetic and formatting live where the tests
// run. This project's top layer does not compile in the container that
// writes it, so a parser or a formatter written there ships UNRUN, and an
// unrun formatter printing a plausible string is the silent-instrument
// failure. Everything that can be wrong about READING the street and about
// PRINTING what was read is therefore here, in plain C++, and
// ue-probe/tests/vignette-spec-test.cpp compiles and runs it with g++
// against the REAL committed file before anything is dispatched. The Unreal
// module supplies actors, lights and pixels and nothing else.
//
// WHAT EACH NUMBER IS A STATISTIC OF, said once, here, and repeated into the
// verdict as comment lines:
//   FrameMedianMs   MEDIAN of TimedFrames game-thread frame deltas, taken
//                   after WarmFrames discarded frames, in milliseconds. Not
//                   a mean, not a peak, and not the same statistic as the
//                   Unity host's Camera.Render() wall time: this one is a
//                   whole engine frame. Named so on every line it appears.
//   PiecesEmitted   count of actors this run actually spawned, over the
//                   count the file asked for, which is its denominator.
#pragma once

#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <algorithm>
#include <map>
#include <string>
#include <vector>

namespace LedgerVignette
{
	// ---- the smallest JSON reader that can read OUR file ----------------
	//
	// A HAND-ROLLED READER IS A LIABILITY AND THIS ONE IS BOUNDED ON
	// PURPOSE. The alternative was Unreal's FJsonSerializer, which would
	// have put the parse in the layer this container cannot compile or run,
	// and the first time anybody found out whether it read the file would
	// have been a 25-minute round trip. This reads the general grammar
	// (objects, arrays, strings with escapes, numbers, true/false/null) and
	// is exercised by g++ against the actual 167 KB committed file, its 593
	// pieces and its escape cases, before any dispatch.
	struct Value;
	typedef std::vector<Value> Array;
	typedef std::vector<std::pair<std::string, Value> > Object;

	enum EType { T_NULL, T_BOOL, T_NUM, T_STR, T_ARR, T_OBJ };

	struct Value
	{
		EType       Type;
		bool        Bool;
		double      Num;
		std::string Str;
		Array       Arr;
		Object      Obj;
		Value() : Type(T_NULL), Bool(false), Num(0.0) {}

		// A MISSING KEY IS NOT A ZERO. Every reader below hands back a
		// found flag, and every caller in this header turns a false into a
		// named error rather than a default, for the same reason
		// StreetVignette.Read throws: a default lets two engines quietly
		// build two different streets.
		const Value* Find(const char* Key) const
		{
			for (size_t I = 0; I < Obj.size(); ++I)
				if (Obj[I].first == Key) return &Obj[I].second;
			return 0;
		}
	};

	struct Reader
	{
		const std::string& S;
		size_t             P;
		std::string        Err;
		Reader(const std::string& InS) : S(InS), P(0) {}

		void Skip()
		{
			while (P < S.size() && (S[P] == ' ' || S[P] == '\t' || S[P] == '\n' || S[P] == '\r')) ++P;
		}
		bool Fail(const char* Why)
		{
			if (Err.empty())
			{
				char Buf[160];
				std::snprintf(Buf, sizeof(Buf), "%s at byte %llu", Why, (unsigned long long)P);
				Err = Buf;
			}
			return false;
		}
		bool ReadString(std::string& Out)
		{
			if (P >= S.size() || S[P] != '"') return Fail("expected-a-string");
			++P;
			Out.clear();
			while (P < S.size() && S[P] != '"')
			{
				if (S[P] == '\\')
				{
					++P;
					if (P >= S.size()) return Fail("string-ended-inside-an-escape");
					char C = S[P++];
					if (C == 'n') Out += '\n';
					else if (C == 't') Out += '\t';
					else if (C == 'r') Out += '\r';
					else if (C == 'b') Out += '\b';
					else if (C == 'f') Out += '\f';
					else if (C == 'u')
					{
						// ONLY THE BASIC LATIN RANGE IS DECODED, and anything
						// above it is replaced with '?' rather than mangled.
						// Our writer escapes control characters and nothing
						// else, so this path is reached by a hostile file and
						// not by ours; it must not crash and must not
						// silently produce a different string.
						if (P + 4 > S.size()) return Fail("truncated-unicode-escape");
						unsigned Code = 0;
						for (int I = 0; I < 4; ++I)
						{
							char H = S[P + I];
							Code <<= 4;
							if (H >= '0' && H <= '9') Code |= (unsigned)(H - '0');
							else if (H >= 'a' && H <= 'f') Code |= (unsigned)(H - 'a' + 10);
							else if (H >= 'A' && H <= 'F') Code |= (unsigned)(H - 'A' + 10);
							else return Fail("bad-hex-in-unicode-escape");
						}
						P += 4;
						Out += (Code < 128 ? (char)Code : '?');
					}
					else Out += C;  // covers \" \\ \/ and anything else
				}
				else Out += S[P++];
			}
			if (P >= S.size()) return Fail("string-was-never-closed");
			++P;
			return true;
		}
		bool ReadValue(Value& Out)
		{
			Skip();
			if (P >= S.size()) return Fail("file-ended-where-a-value-was-expected");
			char C = S[P];
			if (C == '{')
			{
				++P; Out.Type = T_OBJ;
				Skip();
				if (P < S.size() && S[P] == '}') { ++P; return true; }
				for (;;)
				{
					Skip();
					std::string Key;
					if (!ReadString(Key)) return false;
					Skip();
					if (P >= S.size() || S[P] != ':') return Fail("expected-a-colon-after-a-key");
					++P;
					Value V;
					if (!ReadValue(V)) return false;
					Out.Obj.push_back(std::make_pair(Key, V));
					Skip();
					if (P < S.size() && S[P] == ',') { ++P; continue; }
					if (P < S.size() && S[P] == '}') { ++P; return true; }
					return Fail("expected-a-comma-or-a-closing-brace");
				}
			}
			if (C == '[')
			{
				++P; Out.Type = T_ARR;
				Skip();
				if (P < S.size() && S[P] == ']') { ++P; return true; }
				for (;;)
				{
					Value V;
					if (!ReadValue(V)) return false;
					Out.Arr.push_back(V);
					Skip();
					if (P < S.size() && S[P] == ',') { ++P; continue; }
					if (P < S.size() && S[P] == ']') { ++P; return true; }
					return Fail("expected-a-comma-or-a-closing-bracket");
				}
			}
			if (C == '"')
			{
				Out.Type = T_STR;
				return ReadString(Out.Str);
			}
			if (std::strncmp(S.c_str() + P, "true", 4) == 0)  { P += 4; Out.Type = T_BOOL; Out.Bool = true;  return true; }
			if (std::strncmp(S.c_str() + P, "false", 5) == 0) { P += 5; Out.Type = T_BOOL; Out.Bool = false; return true; }
			if (std::strncmp(S.c_str() + P, "null", 4) == 0)  { P += 4; Out.Type = T_NULL; return true; }
			if (C == '-' || (C >= '0' && C <= '9'))
			{
				size_t Start = P;
				if (S[P] == '-') ++P;
				while (P < S.size() && ((S[P] >= '0' && S[P] <= '9') || S[P] == '.'
				       || S[P] == 'e' || S[P] == 'E' || S[P] == '+' || S[P] == '-')) ++P;
				// THE C LOCALE IS NAMED RATHER THAN ASSUMED. strtod under a
				// comma-decimal locale reads "1.5" as 1 and would put every
				// piece in this street a metre from where the file puts it,
				// with every count green. The module sets LC_NUMERIC to C
				// before it parses and this header's test asserts it.
				Out.Type = T_NUM;
				Out.Num = std::strtod(S.substr(Start, P - Start).c_str(), 0);
				return true;
			}
			return Fail("unrecognised-value");
		}
	};

	// ---- the street, as this engine needs it ---------------------------

	struct Piece
	{
		std::string Bom, Name, Shape, Surface, Asset, Edge, Region;
		double X, Y, Z, SX, SY, SZ, PitchDeg, YawDeg, RollDeg;
		bool   Emissive;
		Piece() : X(0), Y(0), Z(0), SX(0), SY(0), SZ(0),
		          PitchDeg(0), YawDeg(0), RollDeg(0), Emissive(false) {}
	};

	struct Camera
	{
		std::string Id, GroundEdge;
		double X, Z, EyeHeightM, YawDeg, PitchDeg, FovVerticalDeg, GroundY;
		bool   GroundFound;
		Camera() : X(0), Z(0), EyeHeightM(0), YawDeg(0), PitchDeg(0),
		           FovVerticalDeg(60), GroundY(0), GroundFound(false) {}
	};

	// A LIGHTING CONDITION, AND SINCE QUEUE 205 THE TWO INTENSITIES THAT
	// LIGHT IT. Until 2026-09-09 the sun was the bare literal 3.0f at
	// VignetteShot.cpp:1240, the only light in that file with no named
	// constant, and the sky was kSkyIntensityDay or kSkyIntensityNight
	// picked by SunOn. Neither number was ever measured, and the 3.0f was
	// tuned against three directional fills that the captured sky retired
	// on the morning of 9 September: its value stood while the thing it
	// was set against was deleted. Both now come out of the shared file.
	// REQUIRED, NOT DEFAULTED: see the parse below.
	// UNITLESS, the same unitless the scene line already prints as
	// lightUnits=unitless/not-candelas.
	struct Condition
	{
		std::string Id, Hdri;
		bool   SunOn, LanternsOn, WindowsOn;
		double Wetness, FogDensity, SunIntensity, SkyIntensity;
		// A4, 2026-09-09: HOW MUCH OF THE FAR FIELD THE HEIGHT FOG MAY OWN,
		// out of the shared file instead of out of
		// `const float kFogMaxOpacityWithSky = 0.45f` in VignetteShot.cpp. A
		// sky behind an opaque fog is invisible, and queue 186 names this cap
		// in its own text as something that must come down in the same change
		// as the sky. REQUIRED, like the two intensities: see the parse.
		double FogMaxOpacity;
		// QUEUE 235: THE EXPOSURE THIS CONDITION ASKS TO BE PHOTOGRAPHED AT,
		// IN THE ENGINE'S AutoExposureMinBrightness UNITS, AND ZERO MEANS
		// LEAVE THE ENGINE ALONE.
		//
		// A POSITIVE VALUE sets AutoExposureMinBrightness AND MaxBrightness
		// to it, which is what removes adaptation: with the two clamps equal
		// the histogram's own answer cannot move the exposure at all.
		// ZERO OR LESS asks for nothing, the overrides are not written, and
		// the condition renders exactly as it did before this field existed.
		// Every condition that was in the file before queue 235 carries 0.0
		// for that reason.
		//
		// THE UNITS ARE NOT A FRAME LUMA AND NO ARITHMETIC CONNECTS THEM.
		// shotMeanLuma is the mean of a tonemapped 8-bit picture; this is a
		// scene-luminance input read by the renderer before the tonemap. The
		// value a run should use is therefore READ OFF A LADDER, one row per
		// candidate, and not computed from any committed luma.
		double ExposurePin;
		Condition() : SunOn(false), LanternsOn(false), WindowsOn(false),
		              Wetness(0), FogDensity(0), SunIntensity(0), SkyIntensity(0),
		              FogMaxOpacity(0), ExposurePin(0) {}
	};

	struct Shot { std::string Id, CameraId, ConditionId; };

	struct Lamp
	{
		std::string ColourSpace;
		double R, G, B, RangeM, Intensity;
		Lamp() : R(0), G(0), B(0), RangeM(0), Intensity(0) {}
	};

	struct Practicals
	{
		std::string ColourSpace;
		double R, G, B, ShopIntensity, ShopRangeM, FlatIntensity, FlatRangeM;
		int    ShopCards, FlatCards;
		std::vector<std::string> LitNames, FlatLitNames;
		Practicals() : R(0), G(0), B(0), ShopIntensity(0), ShopRangeM(0),
		               FlatIntensity(0), FlatRangeM(0), ShopCards(0), FlatCards(0) {}
	};

	struct Spec
	{
		std::string        Schema;
		int                HeaderPieces;
		int                HeaderMultiRotation;
		std::vector<Piece> Pieces;
		std::vector<Camera>    Cameras;
		std::vector<Condition> Conditions;
		std::vector<Shot>      Shots;
		Lamp       Lantern;
		Practicals Windows;
		double     SunElevationDeg, SunAzimuthDeg;
		std::string AheadOfRun;   // "none" when the file is not declared ahead
		int         AheadPiecesThen;
		Spec() : HeaderPieces(0), HeaderMultiRotation(-1),
		         SunElevationDeg(0), SunAzimuthDeg(0),
		         AheadOfRun("none"), AheadPiecesThen(0) {}
	};

	// THE SCHEMA THIS READER UNDERSTANDS. A consumer that does not
	// recognise the string REFUSES rather than guesses, which is the same
	// fail-closed rule the C# reader follows and the reason a schema bump
	// cannot silently half-work in one engine.
	inline const char* SchemaWanted() { return "ledger.vignette-pieces/1"; }

	inline bool Need(const Value& O, const char* Key, const Value*& Out, std::string& Err,
	                 const char* Where)
	{
		Out = O.Find(Key);
		if (Out == 0)
		{
			Err = std::string("missing key ") + Key + " in " + Where;
			return false;
		}
		return true;
	}

	inline bool NeedNum(const Value& O, const char* Key, double& Out, std::string& Err,
	                    const char* Where)
	{
		const Value* V = 0;
		if (!Need(O, Key, V, Err, Where)) return false;
		if (V->Type != T_NUM) { Err = std::string("key ") + Key + " in " + Where + " is not a number"; return false; }
		Out = V->Num;
		return true;
	}

	inline bool NeedStr(const Value& O, const char* Key, std::string& Out, std::string& Err,
	                    const char* Where)
	{
		const Value* V = 0;
		if (!Need(O, Key, V, Err, Where)) return false;
		if (V->Type == T_NULL) { Out.clear(); return true; }   // "asset":null is JSON, not a string
		if (V->Type != T_STR) { Err = std::string("key ") + Key + " in " + Where + " is not a string"; return false; }
		Out = V->Str;
		return true;
	}

	inline bool NeedBool(const Value& O, const char* Key, bool& Out, std::string& Err,
	                     const char* Where)
	{
		const Value* V = 0;
		if (!Need(O, Key, V, Err, Where)) return false;
		if (V->Type != T_BOOL) { Err = std::string("key ") + Key + " in " + Where + " is not a boolean"; return false; }
		Out = V->Bool;
		return true;
	}

	inline bool ParseSpec(const std::string& Text, Spec& Out, std::string& Err)
	{
		Err.clear();
		Reader R(Text);
		Value Root;
		if (!R.ReadValue(Root)) { Err = "piece list unreadable: " + R.Err; return false; }
		if (Root.Type != T_OBJ) { Err = "piece list is not an object"; return false; }
		if (!NeedStr(Root, "schema", Out.Schema, Err, "root")) return false;
		if (Out.Schema != SchemaWanted())
		{
			Err = "piece list schema is " + Out.Schema + ", expected " + SchemaWanted();
			return false;
		}
		const Value* Counts = 0;
		if (!Need(Root, "counts", Counts, Err, "root")) return false;
		double D = 0;
		if (!NeedNum(*Counts, "pieces", D, Err, "counts")) return false;
		Out.HeaderPieces = (int)D;
		if (!NeedNum(*Counts, "multi_rotation", D, Err, "counts")) return false;
		Out.HeaderMultiRotation = (int)D;

		const Value* Ahead = Root.Find("ahead_of_unity_run");
		if (Ahead != 0)
		{
			if (!NeedStr(*Ahead, "run", Out.AheadOfRun, Err, "ahead_of_unity_run")) return false;
			if (!NeedNum(*Ahead, "pieces_then", D, Err, "ahead_of_unity_run")) return false;
			Out.AheadPiecesThen = (int)D;
		}

		const Value* Lan = 0;
		if (!Need(Root, "lantern", Lan, Err, "root")) return false;
		if (!NeedStr(*Lan, "colour_space", Out.Lantern.ColourSpace, Err, "lantern")) return false;
		if (!NeedNum(*Lan, "r", Out.Lantern.R, Err, "lantern")) return false;
		if (!NeedNum(*Lan, "g", Out.Lantern.G, Err, "lantern")) return false;
		if (!NeedNum(*Lan, "b", Out.Lantern.B, Err, "lantern")) return false;
		if (!NeedNum(*Lan, "range_m", Out.Lantern.RangeM, Err, "lantern")) return false;
		if (!NeedNum(*Lan, "intensity", Out.Lantern.Intensity, Err, "lantern")) return false;

		const Value* WP = 0;
		if (!Need(Root, "window_practicals", WP, Err, "root")) return false;
		if (!NeedStr(*WP, "colour_space", Out.Windows.ColourSpace, Err, "window_practicals")) return false;
		if (!NeedNum(*WP, "r", Out.Windows.R, Err, "window_practicals")) return false;
		if (!NeedNum(*WP, "g", Out.Windows.G, Err, "window_practicals")) return false;
		if (!NeedNum(*WP, "b", Out.Windows.B, Err, "window_practicals")) return false;
		if (!NeedNum(*WP, "shop_intensity", Out.Windows.ShopIntensity, Err, "window_practicals")) return false;
		if (!NeedNum(*WP, "shop_range_m", Out.Windows.ShopRangeM, Err, "window_practicals")) return false;
		if (!NeedNum(*WP, "flat_intensity", Out.Windows.FlatIntensity, Err, "window_practicals")) return false;
		if (!NeedNum(*WP, "flat_range_m", Out.Windows.FlatRangeM, Err, "window_practicals")) return false;
		if (!NeedNum(*WP, "shop_cards", D, Err, "window_practicals")) return false;
		Out.Windows.ShopCards = (int)D;
		if (!NeedNum(*WP, "flat_cards", D, Err, "window_practicals")) return false;
		Out.Windows.FlatCards = (int)D;
		const Value* LitN = 0;
		if (!Need(*WP, "lit_names", LitN, Err, "window_practicals")) return false;
		for (size_t I = 0; I < LitN->Arr.size(); ++I) Out.Windows.LitNames.push_back(LitN->Arr[I].Str);
		const Value* FlatN = 0;
		if (!Need(*WP, "flat_lit_names", FlatN, Err, "window_practicals")) return false;
		for (size_t I = 0; I < FlatN->Arr.size(); ++I) Out.Windows.FlatLitNames.push_back(FlatN->Arr[I].Str);

		const Value* Sun = 0;
		if (!Need(Root, "sun", Sun, Err, "root")) return false;
		if (!NeedNum(*Sun, "elevation_deg", Out.SunElevationDeg, Err, "sun")) return false;
		if (!NeedNum(*Sun, "azimuth_deg", Out.SunAzimuthDeg, Err, "sun")) return false;

		const Value* Cams = 0;
		if (!Need(Root, "cameras", Cams, Err, "root")) return false;
		for (size_t I = 0; I < Cams->Arr.size(); ++I)
		{
			const Value& O = Cams->Arr[I];
			Camera C;
			if (!NeedStr(O, "id", C.Id, Err, "camera")) return false;
			if (!NeedNum(O, "x_m", C.X, Err, "camera")) return false;
			if (!NeedNum(O, "z_m", C.Z, Err, "camera")) return false;
			if (!NeedNum(O, "eye_height_above_ground_m", C.EyeHeightM, Err, "camera")) return false;
			if (!NeedNum(O, "yaw_deg", C.YawDeg, Err, "camera")) return false;
			if (!NeedNum(O, "pitch_deg", C.PitchDeg, Err, "camera")) return false;
			if (!NeedNum(O, "fov_vertical_deg", C.FovVerticalDeg, Err, "camera")) return false;
			// THE GROUND UNDER THE CAMERA COMES OUT OF THE FILE. Re-deriving
			// the crossfall here would be a second opinion about the street.
			if (!NeedBool(O, "ground_found", C.GroundFound, Err, "camera")) return false;
			if (!NeedNum(O, "ground_y_m", C.GroundY, Err, "camera")) return false;
			if (!NeedStr(O, "ground_edge", C.GroundEdge, Err, "camera")) return false;
			Out.Cameras.push_back(C);
		}

		const Value* Conds = 0;
		if (!Need(Root, "conditions", Conds, Err, "root")) return false;
		for (size_t I = 0; I < Conds->Arr.size(); ++I)
		{
			const Value& O = Conds->Arr[I];
			Condition C;
			if (!NeedStr(O, "id", C.Id, Err, "condition")) return false;
			if (!NeedStr(O, "hdri", C.Hdri, Err, "condition")) return false;
			if (!NeedBool(O, "sun", C.SunOn, Err, "condition")) return false;
			if (!NeedBool(O, "lanterns", C.LanternsOn, Err, "condition")) return false;
			if (!NeedBool(O, "window_practicals", C.WindowsOn, Err, "condition")) return false;
			if (!NeedNum(O, "wetness", C.Wetness, Err, "condition")) return false;
			if (!NeedNum(O, "fog_density", C.FogDensity, Err, "condition")) return false;
			// REQUIRED, AND THE REFUSAL IS THE POINT. NeedNum fails the whole
			// parse with the key named in Err, so a condition that does not
			// say how bright its sun is stops the run rather than inheriting
			// a literal nobody chose. An optional field with a silent default
			// would rebuild exactly the fault queue 205 exists to repair.
			if (!NeedNum(O, "sun_intensity", C.SunIntensity, Err, "condition")) return false;
			if (!NeedNum(O, "sky_intensity", C.SkyIntensity, Err, "condition")) return false;
			// AND THE FOG CAP, ON THE SAME TERMS AND FOR THE SAME REASON.
			// An optional field with a silent default would let one engine
			// cap the fog at 0.45 and the other at 1.0 and both stills would
			// look fine, which is the fault the required fields exist for.
			if (!NeedNum(O, "fog_max_opacity", C.FogMaxOpacity, Err, "condition")) return false;
			// AND THE EXPOSURE PIN, REQUIRED ON THE SAME TERMS, QUEUE 235.
			// Required rather than optional precisely BECAUSE its safe value
			// is 0.0: an optional field defaulting to 0.0 would read the same
			// whether the writer chose auto exposure or forgot the key, and
			// the run would photograph a street at an exposure nobody asked
			// for and print no sign of it. Every condition states its own
			// answer, and the two engines cannot disagree about which ones
			// are pinned.
			if (!NeedNum(O, "exposure_pin", C.ExposurePin, Err, "condition")) return false;
			Out.Conditions.push_back(C);
		}

		const Value* Shots = 0;
		if (!Need(Root, "shots", Shots, Err, "root")) return false;
		for (size_t I = 0; I < Shots->Arr.size(); ++I)
		{
			const Value& O = Shots->Arr[I];
			Shot S;
			if (!NeedStr(O, "id", S.Id, Err, "shot")) return false;
			if (!NeedStr(O, "camera", S.CameraId, Err, "shot")) return false;
			if (!NeedStr(O, "condition", S.ConditionId, Err, "shot")) return false;
			Out.Shots.push_back(S);
		}

		const Value* Pieces = 0;
		if (!Need(Root, "pieces", Pieces, Err, "root")) return false;
		Out.Pieces.reserve(Pieces->Arr.size());
		for (size_t I = 0; I < Pieces->Arr.size(); ++I)
		{
			const Value& O = Pieces->Arr[I];
			Piece P;
			if (!NeedStr(O, "bom", P.Bom, Err, "piece")) return false;
			if (!NeedStr(O, "name", P.Name, Err, "piece")) return false;
			if (!NeedStr(O, "shape", P.Shape, Err, "piece")) return false;
			if (!NeedStr(O, "surface", P.Surface, Err, "piece")) return false;
			if (!NeedStr(O, "asset", P.Asset, Err, "piece")) return false;
			if (!NeedNum(O, "x_m", P.X, Err, "piece")) return false;
			if (!NeedNum(O, "y_m", P.Y, Err, "piece")) return false;
			if (!NeedNum(O, "z_m", P.Z, Err, "piece")) return false;
			if (!NeedNum(O, "sx_m", P.SX, Err, "piece")) return false;
			if (!NeedNum(O, "sy_m", P.SY, Err, "piece")) return false;
			if (!NeedNum(O, "sz_m", P.SZ, Err, "piece")) return false;
			if (!NeedNum(O, "pitch_deg", P.PitchDeg, Err, "piece")) return false;
			if (!NeedNum(O, "yaw_deg", P.YawDeg, Err, "piece")) return false;
			// ROLL IS THE FIELD A READER LOSES SILENTLY. Nine of this
			// scene's 146 cylinders are rolled; a reader that skipped this
			// key would stand nine pipes on end and every count would agree.
			if (!NeedNum(O, "roll_deg", P.RollDeg, Err, "piece")) return false;
			if (!NeedStr(O, "edge", P.Edge, Err, "piece")) return false;
			if (!NeedStr(O, "region", P.Region, Err, "piece")) return false;
			if (!NeedBool(O, "emissive", P.Emissive, Err, "piece")) return false;
			Out.Pieces.push_back(P);
		}
		if ((int)Out.Pieces.size() != Out.HeaderPieces)
		{
			char Buf[160];
			std::snprintf(Buf, sizeof(Buf),
				"the header claims %d pieces and %d are under it",
				Out.HeaderPieces, (int)Out.Pieces.size());
			Err = Buf;
			return false;
		}
		return true;
	}

	// ---- what the emitter needs computed, computed here -----------------

	// GAMMA sRGB TO LINEAR, the exact piecewise sRGB transfer function.
	// The file states its colour space and this engine's lights take linear
	// colour, so the conversion happens once, here, where it is tested,
	// rather than as a pow(2.2) somewhere in an actor spawn.
	inline double SrgbToLinear(double C)
	{
		if (C <= 0.0) return 0.0;
		if (C >= 1.0) return 1.0;
		return (C <= 0.04045) ? (C / 12.92)
		                      : std::pow((C + 0.055) / 1.055, 2.4);
	}

	// AND BACK, THE EXACT INVERSE, because a colour this project computes in
	// LINEAR has to be written into an sRGB texture to be handed to a shader
	// that will convert it back. The pair exists for one reason: Unity
	// multiplies a gamma-encoded texel by a gamma-encoded material colour
	// IN LINEAR SPACE, and the Unreal base material has no colour parameter
	// to multiply by, so the product is baked into the texel instead. Baking
	// it needs the product taken in linear and then re-encoded, and an
	// approximate inverse would shift every one of those surfaces by a
	// fraction of a stop for no reason. Asserted round-trip in the g++ test.
	inline double LinearToSrgb(double C)
	{
		if (C <= 0.0) return 0.0;
		if (C >= 1.0) return 1.0;
		return (C <= 0.0031308) ? (C * 12.92)
		                        : (1.055 * std::pow(C, 1.0 / 2.4) - 0.055);
	}

	// A 0..1 COLOUR CHANNEL AS THE BYTE UNITY WOULD HAVE STORED. Unity's
	// Color32 cast rounds, and the tint tables this project shares are float
	// literals: 0.78 becomes 199 and 199/255 is 0.78039, so the byte is
	// taken FIRST and everything downstream reads the same number both
	// engines actually render. Rounding, not truncation: a truncating cast
	// would land 198 and the two streets would differ by a byte nobody could
	// find.
	inline int ByteOf(double C)
	{
		if (C <= 0.0) return 0;
		if (C >= 1.0) return 255;
		return (int)(C * 255.0 + 0.5);
	}

	// VERTICAL FIELD OF VIEW TO HORIZONTAL, WHICH IS THE TRAP IN THIS FILE.
	// The scene states fov_vertical_deg because Unity's Camera.fieldOfView
	// is vertical. Unreal's UCameraComponent::FieldOfView is HORIZONTAL.
	// Handing 60 straight to Unreal at 16:9 gives a 60 degree horizontal
	// shot against Unity's 91.5, which is a different photograph of the same
	// street and would have been read as a modelling difference. Both
	// numbers are printed on the shot line so the conversion is visible.
	inline double HorizontalFovDeg(double VerticalFovDeg, int W, int H)
	{
		if (H <= 0 || W <= 0) return VerticalFovDeg;
		const double Pi = 3.14159265358979323846;
		const double Aspect = (double)W / (double)H;
		const double V = VerticalFovDeg * Pi / 180.0;
		return 2.0 * std::atan(std::tan(V * 0.5) * Aspect) * 180.0 / Pi;
	}

	// THE SUN'S BEARING TO THIS ENGINE'S YAW, converted in ONE place and
	// derived exactly as the Unity host derives its own.
	//
	// The scene file's frame puts the bearing origin at +x and turns toward
	// +z, and the azimuth is a bearing TO the sun. A directional light faces
	// the way its light TRAVELS, which is the opposite bearing. In this
	// engine's mapping (+x is +X and +z is +Y) a facing at bearing b IS yaw
	// b, so the light's yaw is azimuth + 180. Unity's host arrives at
	// 270 - azimuth because a Unity facing at bearing b is yaw 90 - b; the
	// two are the same direction expressed in two engines, which is the only
	// thing that matters, and the verdict prints both so a reader can check
	// that claim rather than believe it.
	inline double Wrap360(double Deg)
	{
		while (Deg < 0.0) Deg += 360.0;
		while (Deg >= 360.0) Deg -= 360.0;
		return Deg;
	}
	inline double SunYawDeg(double AzimuthDeg) { return Wrap360(AzimuthDeg + 180.0); }
	inline double UnitySunYawDeg(double AzimuthDeg) { return Wrap360(270.0 - AzimuthDeg); }
	// AND THE PITCH, WHICH IS THE HALF THAT IS EASY TO GET RIGHT BY
	// ACCIDENT. A directional light points the way its light travels, so a
	// sun 36 degrees above the horizon sends its light 36 degrees BELOW it.
	inline double SunPitchDeg(double ElevationDeg) { return -ElevationDeg; }

	// HOW MANY PIECES CARRY TWO OR MORE NON-ZERO ROTATIONS.
	//
	// It decides whether this engine is free to compose Euler angles in
	// whatever order its API prefers. At zero, the composition order is
	// unexercised and the two engines cannot differ on it. Counted from the
	// file at runtime and printed, because the Core-side count is a claim
	// about a file and this is the same claim measured by the reader that
	// actually builds the street.
	inline int MultiRotationCount(const std::vector<Piece>& Pieces)
	{
		int N = 0;
		for (size_t I = 0; I < Pieces.size(); ++I)
		{
			int Turns = 0;
			if (std::fabs(Pieces[I].PitchDeg) > 1e-9) ++Turns;
			if (std::fabs(Pieces[I].YawDeg)   > 1e-9) ++Turns;
			if (std::fabs(Pieces[I].RollDeg)  > 1e-9) ++Turns;
			if (Turns >= 2) ++N;
		}
		return N;
	}

	inline int ShapeCount(const std::vector<Piece>& Pieces, const char* Shape)
	{
		int N = 0;
		for (size_t I = 0; I < Pieces.size(); ++I) if (Pieces[I].Shape == Shape) ++N;
		return N;
	}

	inline int EmissiveCount(const std::vector<Piece>& Pieces)
	{
		int N = 0;
		for (size_t I = 0; I < Pieces.size(); ++I) if (Pieces[I].Emissive) ++N;
		return N;
	}

	// A MEDIAN, AND IT IS A MEDIAN OF WHAT IS PASSED IN. Takes the vector by
	// value because it sorts, and returns -1 for an empty series so that a
	// timing that never ran cannot print as a fast frame.
	inline double MedianMs(std::vector<double> Ms)
	{
		if (Ms.empty()) return -1.0;
		std::sort(Ms.begin(), Ms.end());
		const size_t N = Ms.size();
		return (N % 2 == 1) ? Ms[N / 2] : (Ms[N / 2 - 1] + Ms[N / 2]) * 0.5;
	}

	// NO SPACES IN ANY VALUE. Every reader in this project splits on
	// whitespace and truncates silently when a value carries one.
	inline std::string NoSpaces(const std::string& In)
	{
		std::string Out(In);
		for (size_t I = 0; I < Out.size(); ++I)
			if (std::isspace((unsigned char)Out[I])) Out[I] = '~';
		if (Out.empty()) Out = "none";
		return Out;
	}

	// ---- the two verdict lines, both written here ----------------------

	// THE SCENE LINE, ONCE PER RUN. Whole-run numbers, one moment, one line.
	// Every zero carries its denominator: `piecesEmitted` over what the file
	// asked for, `lanterns` over the emissive pieces, `windowsLit` over the
	// interior cards.
	inline std::string SceneLine(const Spec& S, int Emitted, int Boxes, int Cyls,
	                             int Planes, int PropStandIns, int DecalQuads,
	                             int Lanterns, int WindowsLit, int Skipped,
	                             const std::string& Note)
	{
		char Buf[900];
		std::snprintf(Buf, sizeof(Buf),
			"sceneStatus=%s piecesEmitted=%d/%d asBox=%d asCyl=%d asPlane=%d "
			"propStandIns=%d/%d decalQuads=%d/%d skipped=%d "
			"lanternsPlaced=%d/%d windowsLit=%d/%d %s "
			"multiRotationInFile=%d aheadOfUnityRun=%s aheadPiecesThen=%d "
			"lampColourSpace=%s>linear windowColourSpace=%s>linear sceneNote=%s",
			Emitted == 0 ? "NOTHING-EMITTED" : (Emitted == S.HeaderPieces ? "WHOLE" : "PARTIAL"),
			Emitted, S.HeaderPieces, Boxes, Cyls, Planes,
			PropStandIns, ShapeCount(S.Pieces, "mesh"),
			DecalQuads, ShapeCount(S.Pieces, "decal"),
			Skipped,
			Lanterns, EmissiveCount(S.Pieces),
			WindowsLit, (int)S.Windows.LitNames.size(),
			S.Windows.FlatLitNames.empty()
				? "flatsLit=0/0 nothing-to-light"
				: "flatsLit=SEE-flat_lit_names",
			MultiRotationCount(S.Pieces),
			NoSpaces(S.AheadOfRun).c_str(), S.AheadPiecesThen,
			NoSpaces(S.Lantern.ColourSpace).c_str(),
			NoSpaces(S.Windows.ColourSpace).c_str(),
			NoSpaces(Note).c_str());
		return std::string(Buf);
	}

	// ---- THE MESH ROUTE'S SEGMENT: THE TALLY, THE MATHS AND THE STRING ---
	//
	// WHY ALL OF IT IS HERE AND NONE OF IT IS IN VignetteShot.cpp, amendment
	// A5 of the ruling of 2026-09-08, queue 161. This segment used to be
	// tallied and formatted in the .cpp, which this container cannot compile,
	// so it shipped UNRUN and carried three faults through three landed runs:
	// a count of MESHES under a key whose name said Prims, a zero printed
	// over a zero denominator with no words beside it, and ONE number
	// standing for two opposite facts. The 25 August standing rule is that
	// the tally, the arithmetic and the string live where the tests run. The
	// .cpp now supplies membership and live state only: one collision
	// reading per placed prop, and the engine's own bounds readback per
	// piece.

	// N OVER M, OR THE WORDS. One rule in one place decides what a zero
	// denominator prints, because 0 of 0 and 0 of 9 are the same number and
	// opposite facts, and a caller that has to remember the rule forgets it.
	inline std::string OverOrWords(int N, int M)
	{
		char B[48];
		if (M <= 0) { std::snprintf(B, sizeof(B), "nothing-measured/%d", M); }
		else { std::snprintf(B, sizeof(B), "%d/%d", N, M); }
		return std::string(B);
	}

	// MINUS ZERO IS A PRINTING ARTEFACT AND NOT A MEASUREMENT.
	inline double NoNegZero(double V)
	{
		// ROUNDED AT THE FOUR DECIMALS THE VALUE IS PRINTED TO, and ONLY the
		// sign of a printed zero can change: a cover top that lands on the
		// road crown arrives from the corner arithmetic at -7e-17 and prints
		// -0.0000, which reads as a sign somebody should look into. Every
		// value that does not round to zero at four decimals is returned
		// exactly as it came in, so nothing as large as a tenth of a
		// millimetre moves here.
		const double R = std::floor(std::fabs(V) * 10000.0 + 0.5) / 10000.0;
		if (R == 0.0) { return 0.0; }
		return V;
	}

	// A CAPPED LIST VALUE, ONE WHITESPACE-FREE TOKEN, AND THE CAP ANNOUNCES
	// ITSELF. Total is the size of the WHOLE population the shown items came
	// from, which is NOT Items.size() when the caller bounded its own memory
	// at collection time: the remainder can only be announced from a number
	// the caller knows and this function cannot see.
	//
	// THE OTHER COPY OF THIS IDEA is LedgerSurface::PathListValue, which
	// joins on a comma because a slash is inside every path it prints, and
	// which cannot call this one: SurfaceBind.h includes this header, so the
	// dependency only runs one way. Named here rather than left to be
	// discovered, because a second copy is the site nobody looks at when the
	// first is fixed. Merging the two edits a file outside queue 161.
	inline std::string CappedList(const std::vector<std::string>& Items, size_t Cap,
	                             int Total, const char* Sep, const char* WhenEmpty)
	{
		std::string Out;
		size_t Shown = 0;
		for (size_t I = 0; I < Items.size() && Shown < Cap; ++I, ++Shown)
		{
			if (Shown > 0) { Out += Sep; }
			Out += NoSpaces(Items[I]);
		}
		const int Held = Total - (int)Shown;
		if (Held > 0)
		{
			// THE SEPARATOR ONLY WHERE THERE IS SOMETHING TO SEPARATE. A cap
			// that bit with nothing shown printed a leading semicolon once,
			// which reads as an item whose name is empty.
			char Tail[64];
			std::snprintf(Tail, sizeof(Tail), "%s(+%d~more~not~shown)",
			              Shown > 0 ? Sep : "", Held);
			Out += Tail;
		}
		if (Out.empty()) { Out = WhenEmpty; }
		return Out;
	}

	// EVERY CAP ANNOUNCES ITSELF, INCLUDING THE ONES THAT SHOULD BE
	// IMPOSSIBLE. snprintf returns what it WOULD have written, so a chunk
	// that overran its buffer says so rather than ending mid-key and reading
	// as a missing measurement. The container test prints the whole segment's
	// length on every run, which is the series these buffers were sized from.
	inline void AppendChunk(std::string& Out, const char* Buf, int Wrote, int Cap, int Chunk)
	{
		Out += Buf;
		if (Wrote >= 0 && Wrote < Cap) { return; }
		char T[112];
		std::snprintf(T, sizeof(T), " propSegmentTruncated=chunk%d/wanted=%d/buffer=%d",
		              Chunk, Wrote, Cap);
		Out += T;
	}

	// ---- HALF ONE: WHAT A PLACED PROP'S ASSET SAYS ABOUT COLLISION ------
	//
	// THREE-VALUED ON PURPOSE, AND THE THIRD VALUE IS THE POINT. A count of
	// simple primitives reads 0 for two opposite facts: an asset with no
	// body setup under it, where nothing answered the question at all, and an
	// asset whose body setup holds zero simple elements, which a
	// complex-as-simple trace flag makes perfectly solid against a capsule.
	// The first is UNKNOWN and is NEVER NO. A negative count is a refusal
	// and is also UNKNOWN: the importer printed propCollisionPrims=0/15 over
	// fifteen refusals once, and the zero was the lie, not the minus one.
	//
	// THE IMPORTER CALLS THE NO-BODY-SETUP CASE NO, over a different
	// population and at a different time. tools/ue/import_prop_meshes.py
	// collidable_word reads a SAVED asset in an editor, where an absent body
	// setup is a finished fact about a file on disk. This reads an asset
	// LOADED AT RUNTIME in a cooked build, where a null body setup is also
	// what a reader gets when nothing has built one yet. Two populations,
	// two answers, ruled UNKNOWN here on 2026-09-08 and written down so the
	// divergence reads as a decision rather than as a bug.
	enum EPropCollisionRead
	{
		PropCollision_Unknown = 0,  // nothing answered: no body setup, or a refused count
		PropCollision_No      = 1,  // a body setup holding nothing a trace can hit
		PropCollision_Yes     = 2   // a simple primitive, or complex-as-simple over geometry
	};

	// THE CLASSIFIER, TAKING ONLY WHAT AN ENGINE CAN ANSWER ABOUT ONE ASSET,
	// so the rule is run by g++ here and the .cpp does nothing but ask.
	// SimpleElements below zero means the engine refused the count.
	// bHasGeometry is whether the mesh has any extent at all, which is the
	// same thing the importer reads as boundsUu-nonzero: a complex-as-simple
	// flag over an empty mesh is a flag pointing at nothing.
	inline EPropCollisionRead ReadPropCollision(bool bHasBodySetup, int SimpleElements,
	                                           bool bComplexAsSimple, bool bHasGeometry)
	{
		if (!bHasBodySetup) { return PropCollision_Unknown; }
		if (SimpleElements > 0) { return PropCollision_Yes; }
		if (bComplexAsSimple && bHasGeometry) { return PropCollision_Yes; }
		if (SimpleElements < 0) { return PropCollision_Unknown; }
		return PropCollision_No;
	}

	inline const char* PropCollisionWord(EPropCollisionRead R)
	{
		if (R == PropCollision_Yes) { return "YES"; }
		if (R == PropCollision_No) { return "NO"; }
		return "UNKNOWN";
	}

	// THE RUN'S TALLY. CUMULATIVE over the placed prop meshes of one run,
	// and Placed() is its own denominator: the readings taken, never the 23
	// the file asked for, because a denominator larger than the set examined
	// turns a clean result into a false claim with a number on it.
	struct PropCollisionTally
	{
		int Yes, No, Unknown;
		// THE NAMES OF BOTH NON-YES BUCKETS, capped by Add at four each. A
		// count cannot be fixed and a name can, and the two buckets are
		// different jobs: a NO is an asset to give collision to, an UNKNOWN
		// is a reading to chase. Only YES needs no names, because a list of
		// everything that worked is the line itself.
		std::vector<std::string> NoOn, UnknownOn;
		PropCollisionTally() : Yes(0), No(0), Unknown(0) {}
		void Add(const std::string& PieceName, EPropCollisionRead R)
		{
			if (R == PropCollision_Yes) { ++Yes; return; }
			if (R == PropCollision_Unknown)
			{
				++Unknown;
				if (UnknownOn.size() < 4) { UnknownOn.push_back(NoSpaces(PieceName)); }
				return;
			}
			++No;
			if (NoOn.size() < 4) { NoOn.push_back(NoSpaces(PieceName)); }
		}
		int Placed() const { return Yes + No + Unknown; }
	};

	// ---- HALF TWO: WHETHER ANYTHING OCCUPIES THE FOOTPRINT ABOVE IT -----
	//
	// THE PLACEMENT RULE IN .claude/rules/instruments.md, BOTH HALVES. A
	// placement metric is distance to the datum AND whether the datum exists
	// under the footprint. propCentreWorstMm is the first half and it is
	// BLIND TO BURIAL: a piece sitting 0.00 mm from where the file put it is
	// perfectly placed and may still be inside the road. Amendment A6 of the
	// same ruling, queue 162, asks the second half of the drainage grate by
	// name, because the street spec as written puts its top under the
	// channel slab that spans it.
	//
	// WHAT COUNTS AS BURIED, A PREDICATE AND NOT A THRESHOLD. A cell of the
	// prop's own footprint is BURIED when some other placed piece's bounds
	// STRADDLE the prop's top there, MinY <= top < MaxY, so the prop's top
	// surface is inside that piece. It is OVERHUNG when nothing straddles
	// but something sits entirely above the top, which is an awning and not
	// a burial. It is OPEN when neither. Three buckets, exact at the printed
	// grid resolution, and no bound anywhere: the run prints the series and
	// a bound, if one is ever wanted, is read off the series afterwards.
	//
	// THE PERCENTAGE AND THE DEPTH ARE ONE READING AND NEITHER IS A READING
	// ALONE. Five of the live file's twenty-three props read a few buried
	// cells at 0.00 mm depth, which is two world AABBs touching at a face;
	// the grate reads every cell of its footprint at tens of millimetres. A
	// percentage cannot tell those apart, so the pair travels as one value
	// and the piece that is that deep over it is captured AT THE SAME CELL.
	//
	// WHAT THIS CANNOT SEE, SAID PLAINLY AND PRINTED ON THE LINE. World
	// AABBs, not triangles:
	//   A sparse mesh whose box swallows a neighbour reads as covering it,
	//   which is why every reading here ships the covering piece's NAME for a
	//   human to judge.
	//   A PITCHED SLAB'S AABB TOP IS ITS HIGH EDGE, not its height above this
	//   prop, so the DEPTH overstates by TWO terms that ADD when the prop
	//   sits past the slab's centre line, and this prop does: the cross-fall
	//   over the slab's OWN FULL WIDTH, plus the prop's distance beyond that
	//   centre line. At 1.432096 degrees the full-width term is 68.6 mm for
	//   the 2.746 m carriageway and 6.4 mm for the 0.255 m channel. CORRECTED
	//   2026-09-09, ruling section 4: this comment read "34 mm", which is the
	//   HALF width and was read as the whole overstatement, and a reader who
	//   subtracts 34 from the grate's 85.00 mm concludes 51 mm of cover and is
	//   wrong by 3.4 times.
	//   THE DECOMPOSITION AT THIS PROP, ruled as 34.32 mm of half-width
	//   cross-fall plus 35.78 mm of distance past the slab's centre line,
	//   70.10 mm. ReadCoverProfile below now prints that figure instead of
	//   arguing it, off the file's own pitches. ON THE STREET AS IT STOOD
	//   BEFORE THE GRATE WAS RAISED on 2026-09-09 it read
	//   localAtFootprintCentre=15.00mm@z2.800000/aabbWorstMinusThis=70.00mm,
	//   with localDeepestAtFootprintEdge=20.00mm and
	//   localDeepestAtCellCentre=19.75mm; queue 162 then lifted that one row
	//   flush and the same keys read no-local-cover at the centre line,
	//   65.01mm at the east footprint edge (a 75 um sliver of the grate under
	//   the gully kerb block) and 10.26mm at a cell centre (the 12 mm double
	//   yellow line, which crosses the grate and does not break at it). The
	//   decomposition above is unaffected: it is arithmetic about a pitched
	//   AABB and not about where the grate sits.
	//   The ruling's 19.90, 14.90 and 35.78
	//   anchor the slab's top face at the piece's own z; the pitch shifts that
	//   face 3.75 mm in z, which is 0.09 mm of y, and that 0.09 mm is the whole
	//   of the difference in every one of those three. The printed series is
	//   the authority, which is what A8 ordered it for.
	//   AND THE RULED FIGURE IS TWO POINTS. On that pre-raise street 85.00 mm
	//   was the carriageway's AABB depth at the grate's western cells and
	//   15.00 mm was the channel's real cover at the centre line, so that
	//   subtraction crossed both a point and a covering piece. The profile
	//   prints it because a reader subtracting this comment's millimetres from
	//   an AABB depth is computing exactly that, and prints TWO-POINTS beside
	//   it. The strict same-point overstatement, one cell and one cover, was
	//   65.25 mm at iz=0 then and is 65.00 mm at the west footprint edge now.
	//   The buried or not answer is unaffected by any of this, the
	//   millimetres are a ceiling, and the stat key says so. The reading that
	//   has neither limit is a downward trace at the cell, which is the
	//   engine's to do and queue 163's sweep.
	//   An AABB question is not an occlusion question at all, and only a
	//   frame answers that one.
	struct PlacedBox
	{
		std::string Name, Edge, Region;
		bool   bProp;       // a mesh-kind piece: the population the burial half measures
		bool   bFromAsset;  // it got a LOADED prop asset rather than the box stand-in
		double MinX, MaxX, MinY, MaxY, MinZ, MaxZ;   // the file's frame, metres
		PlacedBox() : bProp(false), bFromAsset(false),
		              MinX(0), MaxX(0), MinY(0), MaxY(0), MinZ(0), MaxZ(0) {}
		bool SpansXZ(double X, double Z) const
		{
			return X >= MinX && X <= MaxX && Z >= MinZ && Z <= MaxZ;
		}
		bool OverlapsXZ(const PlacedBox& O) const
		{
			return !(O.MaxX <= MinX || O.MinX >= MaxX || O.MaxZ <= MinZ || O.MinZ >= MaxZ);
		}
	};

	// THE SAME STRUCT FROM THE FILE, WHICH IS A FIXTURE AND NEVER A READING.
	// The run fills PlacedBox from the engine's own GetActorBounds, because
	// where a piece IS is the only thing worth measuring. This makes one from
	// a piece row so the container can exercise the arithmetic against the
	// committed street with no engine present, and the difference between the
	// two is exactly what propCentreWorstMm reports.
	inline PlacedBox SpecBoxBounds(const Piece& P)
	{
		PlacedBox B;
		B.Name = P.Name; B.Edge = P.Edge; B.Region = P.Region;
		B.bProp = (P.Shape == "mesh");
		const double HX = P.SX * 0.5, HY = P.SY * 0.5, HZ = P.SZ * 0.5;
		// THE EIGHT CORNERS, TURNED THE WAY THE FILE'S OWN FRAME SAYS: pitch
		// about +x with positive tipping the +z end down, yaw about +y taking
		// +x toward +z, roll about +z. The file's counts.multi_rotation is 0
		// and the reader prints it every run, so no piece carries two of
		// these at once and the composition order below is unexercised; it is
		// written out rather than skipped because the day that count stops
		// being zero this must not quietly pick an order.
		const double CP = std::cos(P.PitchDeg * 3.14159265358979323846 / 180.0);
		const double SP = std::sin(P.PitchDeg * 3.14159265358979323846 / 180.0);
		const double CY = std::cos(P.YawDeg * 3.14159265358979323846 / 180.0);
		const double SY = std::sin(P.YawDeg * 3.14159265358979323846 / 180.0);
		const double CR = std::cos(P.RollDeg * 3.14159265358979323846 / 180.0);
		const double SR = std::sin(P.RollDeg * 3.14159265358979323846 / 180.0);
		bool bFirst = true;
		for (int I = 0; I < 8; ++I)
		{
			double X = (I & 1) ? HX : -HX;
			double Y = (I & 2) ? HY : -HY;
			double Z = (I & 4) ? HZ : -HZ;
			double T;
			T = Y * CP - Z * SP;  Z = Y * SP + Z * CP;  Y = T;   // pitch about +x
			T = X * CY - Z * SY;  Z = X * SY + Z * CY;  X = T;   // yaw about +y
			T = X * CR - Y * SR;  Y = X * SR + Y * CR;  X = T;   // roll about +z
			X += P.X; Y += P.Y; Z += P.Z;
			if (bFirst)
			{
				B.MinX = B.MaxX = X; B.MinY = B.MaxY = Y; B.MinZ = B.MaxZ = Z;
				bFirst = false;
				continue;
			}
			if (X < B.MinX) { B.MinX = X; }
			if (X > B.MaxX) { B.MaxX = X; }
			if (Y < B.MinY) { B.MinY = Y; }
			if (Y > B.MaxY) { B.MaxY = Y; }
			if (Z < B.MinZ) { B.MinZ = Z; }
			if (Z > B.MaxZ) { B.MaxZ = Z; }
		}
		return B;
	}

	// THE GRID'S SIDE, AND IT IS A SAMPLER WITH A RESOLUTION AND SAYS SO ON
	// THE LINE: a gap in the cover narrower than one cell cannot be seen
	// here at all. 20 over a 0.4 m grate is a 20 mm cell.
	inline int BurialGridSide() { return 20; }

	struct BurialRead
	{
		std::string Name, Edge, Region;
		bool   bFromAsset;
		double TopM;              // the prop's OWN placed world-bounds top
		int    Cells, Buried, Overhung, Open;
		double DeepestMm;         // AT WORST over the buried cells of this prop
		double DeepestCoverTopM;  // the cover's top AT THE SAME CELL as DeepestMm
		std::string DeepestBy;    // and the piece, same cell, same instant
		double HeadroomMm;        // SMALLEST gap to anything above, over cells that are not buried; -1 is nothing above any
		std::string HeadroomBy;
		std::vector<std::string> ByCover;  // one entry per covering piece, deepest first
		int    CoverCount;        // how many pieces straddle this prop's top anywhere
		BurialRead() : bFromAsset(false), TopM(0), Cells(0), Buried(0), Overhung(0),
		               Open(0), DeepestMm(0), DeepestCoverTopM(0), DeepestBy("none"),
		               HeadroomMm(-1), HeadroomBy("none"), CoverCount(0) {}
		double BuriedPct() const
		{
			return Cells <= 0 ? 0.0 : 100.0 * (double)Buried / (double)Cells;
		}
		double OverhungPct() const
		{
			return Cells <= 0 ? 0.0 : 100.0 * (double)Overhung / (double)Cells;
		}
		double OpenPct() const
		{
			return Cells <= 0 ? 0.0 : 100.0 * (double)Open / (double)Cells;
		}
		bool FullyBuried() const { return Cells > 0 && Buried == Cells; }
	};

	// ONE CELL OF ONE PROP'S FOOTPRINT, AND THE ONE PLACE THE STRADDLE
	// PREDICATE LIVES.
	//
	// ONE IMPLEMENTATION PER IDEA, split out 2026-09-09 for A8. The tally
	// below and the per-cell cover profile further down both read a cell
	// through this function, because a second copy of a predicate is the site
	// nobody fixes: a summary key and a depth series that disagreed about
	// what buried MEANS would be worse than no series at all.
	struct BurialCellRead
	{
		double X, Z;            // the cell's centre, the file's own frame, metres
		bool   bStraddled;      // some other piece's bounds contain the prop's top HERE
		bool   bAbove;          // nothing straddles and something sits entirely over
		double CoverTopM;       // the HIGHEST straddling piece's top, at this cell
		double DepthMm;         // how far the prop's top is inside it, at this cell
		std::string By;         // and that piece's name, same cell, same instant
		double LowAboveM;       // the LOWEST thing entirely above, when nothing straddles
		std::string AboveBy;
		// EVERY straddling piece at this cell with its depth here, which is
		// what the per-cover maxima are folded from. Not just the highest:
		// two slabs can straddle one cell and the reader needs both names.
		std::vector<std::pair<std::string, double> > Straddlers;
		BurialCellRead() : X(0), Z(0), bStraddled(false), bAbove(false),
		                   CoverTopM(0), DepthMm(0), By("none"),
		                   LowAboveM(0), AboveBy("none") {}
	};

	// THE CANDIDATES, NARROWED ONCE PER PROP: anything whose bounds reach
	// above the prop's top and over its footprint at all. A handful of boxes
	// per cell instead of 593.
	inline void BurialCandidates(const std::vector<PlacedBox>& All, size_t Which,
	                             std::vector<size_t>& Out)
	{
		const PlacedBox& P = All[Which];
		Out.clear();
		for (size_t I = 0; I < All.size(); ++I)
		{
			if (I == Which) { continue; }
			if (All[I].MaxY <= P.MaxY) { continue; }       // nothing of it is above the top
			if (!P.OverlapsXZ(All[I])) { continue; }       // nor over the footprint
			Out.push_back(I);
		}
	}

	// THE SAMPLER'S OWN GEOMETRY, written once so the series and the tally
	// sample the SAME cell centres. IX and IZ are zero based over
	// BurialGridSide().
	inline double BurialCellX(const PlacedBox& P, int IX)
	{
		return P.MinX + (IX + 0.5) * (P.MaxX - P.MinX) / (double)BurialGridSide();
	}
	inline double BurialCellZ(const PlacedBox& P, int IZ)
	{
		return P.MinZ + (IZ + 0.5) * (P.MaxZ - P.MinZ) / (double)BurialGridSide();
	}

	inline BurialCellRead ReadBurialCell(const std::vector<PlacedBox>& All,
	                                     const std::vector<size_t>& Cand,
	                                     const PlacedBox& P, double CX, double CZ)
	{
		BurialCellRead Cell;
		Cell.X = CX; Cell.Z = CZ;
		for (size_t K = 0; K < Cand.size(); ++K)
		{
			const PlacedBox& C = All[Cand[K]];
			if (!C.SpansXZ(CX, CZ)) { continue; }
			if (C.MinY <= P.MaxY)
			{
				const double D = (C.MaxY - P.MaxY) * 1000.0;
				if (!Cell.bStraddled || C.MaxY > Cell.CoverTopM)
				{
					Cell.bStraddled = true;
					Cell.CoverTopM = C.MaxY;
					Cell.DepthMm = D;
					Cell.By = NoSpaces(C.Name);
				}
				Cell.Straddlers.push_back(std::make_pair(NoSpaces(C.Name), D));
			}
			else if (!Cell.bAbove || C.MinY < Cell.LowAboveM)
			{
				Cell.bAbove = true;
				Cell.LowAboveM = C.MinY;
				Cell.AboveBy = NoSpaces(C.Name);
			}
		}
		return Cell;
	}

	// ONE PROP, EVERY CELL OF ITS OWN FOOTPRINT, AGAINST EVERY OTHER PLACED
	// PIECE.
	inline BurialRead ReadOneBurial(const std::vector<PlacedBox>& All, size_t Which)
	{
		const PlacedBox& P = All[Which];
		BurialRead R;
		R.Name = NoSpaces(P.Name); R.Edge = NoSpaces(P.Edge); R.Region = NoSpaces(P.Region);
		R.bFromAsset = P.bFromAsset;
		R.TopM = P.MaxY;
		std::vector<size_t> Cand;
		BurialCandidates(All, Which, Cand);
		std::map<std::string, double> PerCover;
		const int Side = BurialGridSide();
		for (int IX = 0; IX < Side; ++IX)
		{
			for (int IZ = 0; IZ < Side; ++IZ)
			{
				const BurialCellRead Cell = ReadBurialCell(All, Cand, P,
					BurialCellX(P, IX), BurialCellZ(P, IZ));
				++R.Cells;
				for (size_t K = 0; K < Cell.Straddlers.size(); ++K)
				{
					std::map<std::string, double>::iterator It =
						PerCover.find(Cell.Straddlers[K].first);
					if (It == PerCover.end())
					{
						PerCover[Cell.Straddlers[K].first] = Cell.Straddlers[K].second;
					}
					else if (Cell.Straddlers[K].second > It->second)
					{
						It->second = Cell.Straddlers[K].second;
					}
				}
				if (Cell.bStraddled)
				{
					++R.Buried;
					// AT WORST, AND THE COVER'S NAME AND HEIGHT COME FROM THE
					// SAME CELL: a numerator's denominator is captured at the
					// instant the numerator peaks.
					if (Cell.DepthMm > R.DeepestMm || R.DeepestBy == "none")
					{
						R.DeepestMm = Cell.DepthMm;
						R.DeepestCoverTopM = Cell.CoverTopM;
						R.DeepestBy = Cell.By;
					}
				}
				else if (Cell.bAbove)
				{
					++R.Overhung;
					const double H = (Cell.LowAboveM - P.MaxY) * 1000.0;
					if (R.HeadroomMm < 0.0 || H < R.HeadroomMm)
					{
						R.HeadroomMm = H;
						R.HeadroomBy = Cell.AboveBy;
					}
				}
				else { ++R.Open; }
			}
		}
		// THE COVERS, DEEPEST FIRST. A selection pass rather than a sort with
		// a comparator, because the list is at most a handful and this stays
		// readable in a header that has to be obvious.
		R.CoverCount = (int)PerCover.size();
		std::vector<std::pair<double, std::string> > Cov;
		for (std::map<std::string, double>::const_iterator It = PerCover.begin();
		     It != PerCover.end(); ++It)
		{
			Cov.push_back(std::make_pair(It->second, It->first));
		}
		while (!Cov.empty())
		{
			size_t Best = 0;
			for (size_t I = 1; I < Cov.size(); ++I)
			{
				if (Cov[I].first > Cov[Best].first) { Best = I; }
			}
			char B[160];
			std::snprintf(B, sizeof(B), "%s=%.2fmm", Cov[Best].second.c_str(), Cov[Best].first);
			R.ByCover.push_back(std::string(B));
			Cov.erase(Cov.begin() + Best);
		}
		return R;
	}

	inline std::vector<BurialRead> ReadBurials(const std::vector<PlacedBox>& All)
	{
		std::vector<BurialRead> Out;
		for (size_t I = 0; I < All.size(); ++I)
		{
			if (!All[I].bProp) { continue; }
			Out.push_back(ReadOneBurial(All, I));
		}
		return Out;
	}

	// THE ORDERING RULE, ONCE, HERE: WORSE IS A LARGER BURIED FRACTION, AND
	// A DEEPER BURIAL BREAKS THE TIE. Cross-multiplied rather than divided so
	// two props with different cell counts still compare, and written once
	// because a second copy of an ordering is how a summary and the series
	// under it come to disagree about which row is the worst one.
	inline bool WorseBurial(const BurialRead& A, const BurialRead& B)
	{
		if (A.Buried * B.Cells != B.Buried * A.Cells)
		{
			return A.Buried * B.Cells > B.Buried * A.Cells;
		}
		return A.DeepestMm > B.DeepestMm;
	}

	// WORST FIRST. A selection pass rather than std::sort with a comparator
	// object, because the population is tens of props and this has to be
	// obvious to read.
	inline std::vector<BurialRead> SortedBurials(const std::vector<BurialRead>& In)
	{
		std::vector<BurialRead> R = In;
		for (size_t I = 0; I < R.size(); ++I)
		{
			size_t Best = I;
			for (size_t J = I + 1; J < R.size(); ++J)
			{
				if (WorseBurial(R[J], R[Best])) { Best = J; }
			}
			if (Best != I) { std::swap(R[I], R[Best]); }
		}
		return R;
	}

	// THE PIECE JAFAR'S ITEM 2 IS ABOUT, BY NAME. A6 asks for this one
	// against the channel it drains, so the segment carries a row for it
	// whether or not it is the worst prop in the run: a worst-case key
	// answers "did it ever" and can never answer "what about that one".
	// The live committed street is the accepting fixture for the name, and
	// the container test goes red if no piece is called this, so a rename
	// cannot quietly turn this row into a permanent not-placed.
	inline const char* BurialSubjectName() { return "prop_drainage_grate_01_0"; }

	inline int BurialIndexOf(const std::vector<BurialRead>& R, const char* Name)
	{
		for (size_t I = 0; I < R.size(); ++I) { if (R[I].Name == Name) { return (int)I; } }
		return -1;
	}

	// ONE PROP'S WHOLE READING AS ONE WHITESPACE-FREE TOKEN. Used for the
	// named subject; the run's own worst case gets the shorter pair below.
	//
	// WHY THE COLLISION WORD RIDES THIS ROW AND NOT ONLY THE TALLY. Jafar's
	// item 2 is one sentence with two halves, the grate as a real mesh WITH
	// COLLISION and in a walk clip, and a tally of 23 answers the first half
	// for the population and neither half for that piece. CollisionWord is
	// what this prop's own asset reported, or no-asset-to-read when the piece
	// is standing in as a box and there was nothing to ask.
	inline std::string BurialRowValue(const BurialRead& R,
	                                 const std::string& CollisionWord)
	{
		char B[420];
		char Head[64];
		if (R.HeadroomMm < 0.0) { std::snprintf(Head, sizeof(Head), "none"); }
		else { std::snprintf(Head, sizeof(Head), "%.2fmm/by=%s", R.HeadroomMm, R.HeadroomBy.c_str()); }
		std::snprintf(B, sizeof(B),
			"%s/via=%s/collision=%s/topM=%.4f/buried=%.1fpct/overhung=%.1fpct"
			"/open=%.1fpct/deepestMm=%.2f/coverTopM=%.4f/by=%s/cells=%d/headroom=%s",
			R.Name.c_str(), R.bFromAsset ? "loaded-asset" : "box-stand-in",
			NoSpaces(CollisionWord).c_str(),
			NoNegZero(R.TopM), R.BuriedPct(), R.OverhungPct(), R.OpenPct(),
			R.DeepestMm, NoNegZero(R.DeepestCoverTopM), R.DeepestBy.c_str(), R.Cells,
			Head);
		return std::string(B);
	}

	// ---- THE HALF AN AABB DEPTH CANNOT ANSWER: THE COVER'S TOP FACE HERE --
	//
	// WHY THIS EXISTS, A8 and section 4 of the ruling of 2026-09-09. The
	// burial half above reads world AABBs, which is all a cooked run can ask a
	// placed actor for, and a pitched slab's AABB top is its HIGH EDGE: over
	// the drainage grate it printed 85.00 mm of cover where the road surface
	// was about 15 mm above the grate's top, and since the grate was raised
	// flush on 2026-09-09 it prints 65.01 mm over a top face that is IN that
	// surface. The overstatement is the instrument's, not the street's, both
	// times. Two numbers were then argued from
	// prose, 18.7 mm against 19.90 mm, neither of them a named statistic and
	// neither of them read off a printed series. That is rule 2's own failure
	// and this is the printer rule 2 asks for FIRST. No bound is set here and
	// none may be read off one run of it.
	//
	// IT IS A FILE READING AND SAYS SO IN ITS OWN VALUE. The pitches live in
	// the spec file and nowhere in a placed actor's bounds, so this is
	// arithmetic over Piece rows and NOT over the run's measured placement. It
	// is therefore printed by the container test and never appended to a
	// verdict line beside the engine's numbers: two populations under one key
	// on one line is exactly the confusion A9 had to write a sentence to undo.
	// The independent confirmation is queue 163's downward sweep, which is
	// ground truth and needs a run.
	//
	// WHAT IT STILL CANNOT SEE, AND THE REFUSAL IS COUNTED RATHER THAN READ
	// AS CLEAR SKY. It answers for PITCH ONLY. A yawed or rolled cover is
	// refused BY NAME and counted on the cell, because a refusal that printed
	// as "nothing above" would make this instrument the thing it was built to
	// correct. The committed street carries 44 yawed and 9 rolled pieces, so
	// that counter is not decorative. It is also still a box reading, not
	// triangles, and an occlusion question is still only answered by a frame.
	//
	// ONE INTERVAL CLIP, USED THREE TIMES. Keeps the t where
	// Lo <= A*t + B <= Hi, narrowing [T0,T1] and answering whether anything
	// is left. Written once because three copies of a clip with the sign of A
	// handled differently is how a slab ends up solid on one side only.
	inline bool ClipRange(double A, double B, double Lo, double Hi,
	                      double& T0, double& T1)
	{
		if (A == 0.0) { return B >= Lo && B <= Hi; }
		double Ta = (Lo - B) / A, Tb = (Hi - B) / A;
		if (Ta > Tb) { const double S = Ta; Ta = Tb; Tb = S; }
		if (Ta > T0) { T0 = Ta; }
		if (Tb < T1) { T1 = Tb; }
		return T0 <= T1;
	}

	// A VERTICAL LINE THROUGH ONE POINT, AND THE PIECE'S SOLID ALONG IT. The
	// world-vertical line is carried into the piece's own frame and clipped
	// against its three local slabs, so the answer is the solid and not a
	// pair of faces: at the grate's east footprint edge the vertical line
	// leaves the channel through its END face while the top face overhead is
	// still there, and a two-face reading called that no cover. It printed
	// 0.00 mm under a slab 10 mm above the grate, which is this instrument's
	// own failure mode and was caught by reading its first series.
	//
	// Pitch is about +x with positive tipping the +z end down, the same
	// convention SpecBoxBounds turns the corners by. t IS the world y, so the
	// clipped range comes straight back as the span.
	inline bool PitchedSpanAtXZ(const Piece& P, double X, double Z,
	                            double& OutLoY, double& OutHiY, std::string& OutWhy)
	{
		OutWhy = "none";
		if (P.YawDeg != 0.0 || P.RollDeg != 0.0)
		{
			OutWhy = "yawed-or-rolled/pitch-arithmetic-cannot-answer-for-this-piece";
			return false;
		}
		const double HX = P.SX * 0.5, HY = P.SY * 0.5, HZ = P.SZ * 0.5;
		if (X < P.X - HX || X > P.X + HX)
		{
			OutWhy = "outside-this-pieces-own-x-extent";
			return false;
		}
		const double CP = std::cos(P.PitchDeg * 3.14159265358979323846 / 180.0);
		const double SP = std::sin(P.PitchDeg * 3.14159265358979323846 / 180.0);
		const double DZ = Z - P.Z;
		// The inverse pitch, applied to the line: local y and z are linear in
		// the world y the line runs along.
		const double AY = CP,  BY = DZ * SP - P.Y * CP;
		const double AZ = -SP, BZ = DZ * CP + P.Y * SP;
		double T0 = -1.0e9, T1 = 1.0e9;
		if (!ClipRange(AY, BY, -HY, HY, T0, T1) || !ClipRange(AZ, BZ, -HZ, HZ, T0, T1))
		{
			OutWhy = "the-solid-does-not-reach-this-point";
			return false;
		}
		OutLoY = T0;
		OutHiY = T1;
		return true;
	}

	// ONE SAMPLE OF THE PROFILE, CARRYING BOTH READINGS OF THE SAME POINT so
	// that a reader is never handed one of them alone. Where says WHICH sample
	// this is, because a cell centre and a footprint edge are two different
	// statistics and mixing them is the whole of the 18.7 against 19.90
	// argument.
	struct CoverCell
	{
		std::string Where;     // cell-centre, footprint-edge or footprint-centre
		int    Index;          // the cell index along z, or -1 at an edge or centre
		double X, Z;           // the sample point, the file's own frame, metres
		double PropTopM;       // the subject's own top, repeated so a row reads alone
		bool   bAabb;          // an AABB straddles the subject's top here
		double AabbTopM, AabbDepthMm;
		std::string AabbBy;
		bool   bLocal;         // a pitch-aware solid straddles it here
		double LocalTopM, LocalDepthMm;
		std::string LocalBy;
		// THE SECOND HALF OF THE LOCAL READING, because a bare 0.00 mm cannot
		// tell open sky from a solid sitting just above with air underneath,
		// and on the committed street one point of twenty-three is the second.
		// Which point MOVED when the grate was raised on 2026-09-09 and the
		// reading did not: it was the grate's east footprint edge, where the
		// channel's pitched end face stood overhead with 8 mm of daylight
		// under it and the AABB called 16.37 mm of burial; it is now the cell
		// at z=2.749981, where the double yellow line's end face stands
		// 2.13 mm over the raised grate and the AABB calls 10.75 mm.
		bool   bLocalAbove;
		double LocalAboveLowM, LocalAboveHeadroomMm;
		std::string LocalAboveBy;
		int    Refused;        // candidate pieces the pitch arithmetic refused, here
		std::string RefusedWhy;
		CoverCell() : Where("nothing-measured"), Index(-1), X(0), Z(0), PropTopM(0),
		              bAabb(false), AabbTopM(0), AabbDepthMm(0), AabbBy("none"),
		              bLocal(false), LocalTopM(0), LocalDepthMm(0), LocalBy("none"),
		              bLocalAbove(false), LocalAboveLowM(0), LocalAboveHeadroomMm(0),
		              LocalAboveBy("none"),
		              Refused(0), RefusedWhy("none") {}
		// The overstatement at THIS point, which is the one number A9 is
		// about. Only meaningful where both readings exist, and the caller is
		// told which by bAabb and bLocal.
		double OverstatementMm() const { return AabbDepthMm - LocalDepthMm; }
	};

	// THE SERIES ACROSS ONE PROP'S FOOTPRINT, ALONG Z, AT ITS MIDDLE X
	// COLUMN. Z is the axis the street's cross-fall varies on, which is the
	// axis placement and cover actually vary on here; x is 42 m of unchanging
	// extrusion and a second axis would print 400 rows to say so.
	//
	// THE SAMPLE POINTS ARE THE TALLY'S OWN CELL CENTRES, through
	// BurialCellZ, plus the two footprint EDGES the tally never samples. That
	// pair is the measurement: a cell-centre extreme and a footprint extreme
	// are different statistics over the same plane.
	inline std::vector<CoverCell> ReadCoverProfile(const std::vector<Piece>& Pieces,
	                                              const std::string& SubjectName,
	                                              std::string& OutWhyNot)
	{
		std::vector<CoverCell> Out;
		OutWhyNot = "none";
		size_t Which = 0;
		bool bFound = false;
		for (size_t I = 0; I < Pieces.size(); ++I)
		{
			if (NoSpaces(Pieces[I].Name) == NoSpaces(SubjectName)) { Which = I; bFound = true; break; }
		}
		if (!bFound)
		{
			OutWhyNot = "no-row-named-" + NoSpaces(SubjectName);
			return Out;
		}
		std::vector<PlacedBox> All;
		for (size_t I = 0; I < Pieces.size(); ++I) { All.push_back(SpecBoxBounds(Pieces[I])); }
		const PlacedBox& P = All[Which];
		std::vector<size_t> Cand;
		BurialCandidates(All, Which, Cand);
		const int Side = BurialGridSide();
		const double CX = BurialCellX(P, Side / 2);
		// SIDE CELL CENTRES, THE TWO FOOTPRINT EDGES THE CELL GRID NEVER
		// SAMPLES, AND THE FOOTPRINT'S OWN CENTRE LINE. Three named
		// populations of one plane, because the whole of the 18.7 against
		// 19.90 argument was two of them read under one name, and the centre
		// line is the point the ruling's 70.10 mm of overstatement is taken at.
		for (int Step = 0; Step < Side + 3; ++Step)
		{
			CoverCell C;
			C.PropTopM = P.MaxY;
			C.X = CX;
			if (Step < Side)
			{
				C.Where = "cell-centre";
				C.Index = Step;
				C.Z = BurialCellZ(P, Step);
			}
			else if (Step < Side + 2)
			{
				C.Where = "footprint-edge";
				C.Index = -1;
				C.Z = (Step == Side) ? P.MinZ : P.MaxZ;
			}
			else
			{
				C.Where = "footprint-centre";
				C.Index = -1;
				C.Z = (P.MinZ + P.MaxZ) * 0.5;
			}
			// HALF ONE, THE SAME PREDICATE THE TALLY USES, through the same
			// function, so this column and propBurialWorst cannot disagree.
			const BurialCellRead Cell = ReadBurialCell(All, Cand, P, C.X, C.Z);
			C.bAabb = Cell.bStraddled;
			C.AabbTopM = Cell.CoverTopM;
			C.AabbDepthMm = Cell.bStraddled ? Cell.DepthMm : 0.0;
			C.AabbBy = Cell.bStraddled ? Cell.By : "none";
			// HALF TWO, THE PITCHED SOLID AT THE SAME POINT AT THE SAME
			// INSTANT. Straddle means the same thing as above: the solid's
			// bottom at or below the subject's top and its top above it.
			for (size_t K = 0; K < Cand.size(); ++K)
			{
				double Lo = 0.0, Hi = 0.0;
				std::string Why;
				if (!PitchedSpanAtXZ(Pieces[Cand[K]], C.X, C.Z, Lo, Hi, Why))
				{
					if (Why.find("yawed-or-rolled") != std::string::npos)
					{
						++C.Refused;
						if (C.RefusedWhy == "none")
						{
							C.RefusedWhy = NoSpaces(Pieces[Cand[K]].Name) + "/" + Why;
						}
					}
					continue;
				}
				if (Hi <= P.MaxY) { continue; }      // all of it is below the top
				if (Lo > P.MaxY)
				{
					// ENTIRELY ABOVE: an overhang and not a burial, the same
					// distinction the tally draws, kept here so a zero in the
					// depth column is never ambiguous.
					if (!C.bLocalAbove || Lo < C.LocalAboveLowM)
					{
						C.bLocalAbove = true;
						C.LocalAboveLowM = Lo;
						C.LocalAboveHeadroomMm = (Lo - P.MaxY) * 1000.0;
						C.LocalAboveBy = NoSpaces(Pieces[Cand[K]].Name);
					}
					continue;
				}
				if (!C.bLocal || Hi > C.LocalTopM)
				{
					C.bLocal = true;
					C.LocalTopM = Hi;
					C.LocalDepthMm = (Hi - P.MaxY) * 1000.0;
					C.LocalBy = NoSpaces(Pieces[Cand[K]].Name);
				}
			}
			Out.push_back(C);
		}
		return Out;
	}

	// THE PROFILE AS ONE WHITESPACE-FREE TOKEN, WITH EVERY NUMBER NAMED FOR
	// THE STATISTIC IT IS AND EVERY ZERO CARRYING ITS DENOMINATOR. Printed by
	// the container test; see the note above for why it is not on a verdict
	// line. A profile that sampled nothing says the words.
	inline std::string CoverProfileValue(const std::vector<CoverCell>& Cells,
	                                    const std::string& WhyNot)
	{
		int Centres = 0, Edges = 0, LocalOn = 0, LocalOverhung = 0, AabbOn = 0, Refused = 0;
		int WorstCentre = -1, WorstEdge = -1, WorstAabb = -1, Middle = -1;
		for (size_t I = 0; I < Cells.size(); ++I)
		{
			const bool bCentre = Cells[I].Where == "cell-centre";
			if (Cells[I].Where == "footprint-centre") { Middle = (int)I; }
			if (bCentre) { ++Centres; }
			else if (Cells[I].Where == "footprint-edge") { ++Edges; }
			if (Cells[I].Refused > 0) { ++Refused; }
			if (Cells[I].bLocal)
			{
				++LocalOn;
				if (bCentre && (WorstCentre < 0
				    || Cells[I].LocalDepthMm > Cells[(size_t)WorstCentre].LocalDepthMm))
				{
					WorstCentre = (int)I;
				}
				if (Cells[I].Where == "footprint-edge" && (WorstEdge < 0
				    || Cells[I].LocalDepthMm > Cells[(size_t)WorstEdge].LocalDepthMm))
				{
					WorstEdge = (int)I;
				}
			}
			if (!Cells[I].bLocal && Cells[I].bLocalAbove) { ++LocalOverhung; }
			if (Cells[I].bAabb)
			{
				++AabbOn;
				if (WorstAabb < 0 || Cells[I].AabbDepthMm > Cells[(size_t)WorstAabb].AabbDepthMm)
				{
					WorstAabb = (int)I;
				}
			}
		}
		if (Cells.empty())
		{
			return "nothing-measured/0-points-sampled/why=" + NoSpaces(WhyNot);
		}
		// THE THREE NUMERIC PARTS ARE FIXED-SHAPE AND THE ASSEMBLY IS A
		// std::string, so no cap exists here to announce. The buffers below
		// hold one reading each: a name, a depth, a z and a population.
		char Centre[220], Edge[220], Aabb[260];
		if (WorstCentre < 0)
		{
			std::snprintf(Centre, sizeof(Centre), "no-local-cover/over=%d-cell-centres", Centres);
		}
		else
		{
			std::snprintf(Centre, sizeof(Centre), "%.2fmm@z%.6f/by=%s/over=%d-cell-centres",
			              Cells[(size_t)WorstCentre].LocalDepthMm,
			              Cells[(size_t)WorstCentre].Z,
			              Cells[(size_t)WorstCentre].LocalBy.c_str(), Centres);
		}
		if (WorstEdge < 0)
		{
			std::snprintf(Edge, sizeof(Edge), "no-local-cover/over=%d-footprint-edges", Edges);
		}
		else
		{
			std::snprintf(Edge, sizeof(Edge), "%.2fmm@z%.6f/by=%s/over=%d-footprint-edges",
			              Cells[(size_t)WorstEdge].LocalDepthMm, Cells[(size_t)WorstEdge].Z,
			              Cells[(size_t)WorstEdge].LocalBy.c_str(), Edges);
		}
		if (WorstAabb < 0)
		{
			std::snprintf(Aabb, sizeof(Aabb), "no-aabb-cover/over=%d-points", (int)Cells.size());
		}
		else
		{
			std::snprintf(Aabb, sizeof(Aabb),
			              "%.2fmm@z%.6f/by=%s/overstatementAtThatPoint=%.2fmm",
			              Cells[(size_t)WorstAabb].AabbDepthMm, Cells[(size_t)WorstAabb].Z,
			              Cells[(size_t)WorstAabb].AabbBy.c_str(),
			              Cells[(size_t)WorstAabb].bLocal
			                  ? Cells[(size_t)WorstAabb].OverstatementMm()
			                  : Cells[(size_t)WorstAabb].AabbDepthMm);
		}
		std::string Out;
		Out += "localDeepestAtCellCentre="; Out += Centre;
		Out += "/localDeepestAtFootprintEdge="; Out += Edge;
		Out += "/aabbDeepest="; Out += Aabb;
		// THE FOOTPRINT CENTRE, AND THE ONE FIGURE THAT IS TWO POINTS AND SAYS
		// SO. The ruling of 2026-09-09 computes the overstatement as the worst
		// AABB depth anywhere over the footprint minus the real cover at the
		// centre line, which are two different points and two different
		// covering pieces. It is printed because a reader who subtracts a
		// comment's millimetres from 85.00 is computing exactly this, and it is
		// named so that nobody mistakes it for the same-point figure above.
		char Mid[260];
		if (Middle < 0)
		{
			std::snprintf(Mid, sizeof(Mid), "nothing-measured/no-footprint-centre-sampled");
		}
		else if (!Cells[(size_t)Middle].bLocal)
		{
			std::snprintf(Mid, sizeof(Mid), "no-local-cover@z%.6f",
			              Cells[(size_t)Middle].Z);
		}
		else
		{
			std::snprintf(Mid, sizeof(Mid),
			              "%.2fmm@z%.6f/by=%s/aabbWorstMinusThis=%.2fmm"
			              "/TWO-POINTS-and-says-so/the-figure-the-ruling-of-2026-09-09-decomposes",
			              Cells[(size_t)Middle].LocalDepthMm, Cells[(size_t)Middle].Z,
			              Cells[(size_t)Middle].LocalBy.c_str(),
			              WorstAabb < 0 ? 0.0
			                  : Cells[(size_t)WorstAabb].AabbDepthMm
			                    - Cells[(size_t)Middle].LocalDepthMm);
		}
		Out += "/localAtFootprintCentre="; Out += Mid;
		Out += "/localCoverAt=" + OverOrWords(LocalOn, (int)Cells.size());
		Out += "/localOverhungNotBuriedAt=" + OverOrWords(LocalOverhung, (int)Cells.size());
		Out += "/aabbCoverAt=" + OverOrWords(AabbOn, (int)Cells.size());
		Out += "/refusedForYawOrRollAt=" + OverOrWords(Refused, (int)Cells.size());
		Out += "/stat=deepest-cover-over-a-props-own-top-AT-WORST-per-population";
		Out += "-named-beside-each/local-is-the-pitched-top-face-from-the-SPEC-FILE";
		Out += "-and-aabb-is-what-a-cooked-run-can-ask-a-placed-actor";
		Out += "-so-the-two-are-never-subtracted-except-at-one-point-and-it-says-which";
		return Out;
	}

	// WHAT THE .cpp HANDS OVER: membership, order and live state, and not one
	// piece of arithmetic or formatting.
	struct PropSegmentIn
	{
		int MeshPiecesInFile;    // the denominator off the FILE, before any spawning
		int PlacedAsMesh;        // prop pieces that got a LOADED asset
		int PlacedAsBox;         // prop pieces that fell back to the box stand-in
		std::vector<std::string> FellBackOn;   // capped at collection; PlacedAsBox is the total
		std::string PackageDir, NamePrefix;
		double CentreWorstMm;    // AT WORST over the placed prop meshes
		std::string CentreWorstOn;
		double SizeWorstMm;      // AT WORST over the axis-aligned placed prop meshes
		std::string SizeWorstOn;
		int    SizeComparable;
		PropCollisionTally Collision;
		std::vector<BurialRead> Burials;
		// THE NAMED SUBJECT'S OWN COLLISION WORD, one of YES, NO, UNKNOWN, or
		// no-asset-to-read when that piece stood in as a box and there was no
		// asset to ask. Set by the .cpp at the instant it asked.
		std::string SubjectCollision;
		bool   bInteractive;     // which path built the street, NOT a measurement of anything
		PropSegmentIn() : MeshPiecesInFile(0), PlacedAsMesh(0), PlacedAsBox(0),
		                  CentreWorstMm(0), CentreWorstOn("nothing-measured"),
		                  SizeWorstMm(0), SizeWorstOn("nothing-measured"),
		                  SizeComparable(0), SubjectCollision("nothing-measured"),
		                  bInteractive(false) {}
	};

	// THE WHOLE SEGMENT, APPENDED TO THE SCENE LINE. WHOLE-RUN NUMBERS ONLY:
	// this rides the run's one scene line, which the vignette, walk and
	// crime verdicts all print, so nothing per-shot and nothing per-camera
	// may appear here. Built with std::string rather than into a fixed
	// buffer, because the buffer it replaces was sized by hand and a cap
	// that cannot bite needs no announcement.
	inline std::string PropMeshSegment(const PropSegmentIn& In)
	{
		const int Placed = In.Collision.Placed();
		int Fully = 0, AnyBuried = 0;
		std::vector<std::string> BuriedRows;
		// THE SERIES, WORST FIRST, by the one ordering rule above, so the
		// summary key and the named rows under it cannot disagree about which
		// prop is the worst one.
		const std::vector<BurialRead> Sorted = SortedBurials(In.Burials);
		for (size_t I = 0; I < Sorted.size(); ++I)
		{
			if (Sorted[I].FullyBuried()) { ++Fully; }
			if (Sorted[I].Buried <= 0) { continue; }
			++AnyBuried;
			if (BuriedRows.size() < 3)
			{
				char B[200];
				std::snprintf(B, sizeof(B), "%s/%.1fpct@%.2fmm/by=%s",
				              Sorted[I].Name.c_str(), Sorted[I].BuriedPct(),
				              Sorted[I].DeepestMm, Sorted[I].DeepestBy.c_str());
				BuriedRows.push_back(std::string(B));
			}
		}
		std::string WorstValue = "nothing-measured/of=0";
		if (!Sorted.empty())
		{
			// AT WORST, WITH ITS DENOMINATOR AND ITS NAMES FROM THE SAME
			// PROP AND THE SAME CELL. of=N is how many props this is the
			// worst OF, which is the reading's own denominator.
			char B[200];
			std::snprintf(B, sizeof(B), "%.1fpct@%.2fmm/on=%s/by=%s/of=%d",
			              Sorted[0].BuriedPct(), Sorted[0].DeepestMm,
			              Sorted[0].Name.c_str(), Sorted[0].DeepestBy.c_str(),
			              (int)Sorted.size());
			WorstValue = B;
		}
		// THE PER-EDGE BREAKDOWN, WHICH IS THE AXIS PLACEMENT VARIES ON.
		// Not per camera: a camera cannot move a piece. One entry per edge
		// that placed a prop, carrying how many of its props read any buried
		// cell at all over how many it placed, so an edge with none is
		// visibly an edge that was looked at.
		std::vector<std::string> EdgeRows;
		std::vector<std::string> EdgeNames;
		for (size_t I = 0; I < Sorted.size(); ++I)
		{
			bool bSeen = false;
			for (size_t J = 0; J < EdgeNames.size(); ++J)
			{
				if (EdgeNames[J] == Sorted[I].Edge) { bSeen = true; break; }
			}
			if (!bSeen) { EdgeNames.push_back(Sorted[I].Edge); }
		}
		for (size_t J = 0; J < EdgeNames.size(); ++J)
		{
			int Props = 0, Hit = 0;
			for (size_t I = 0; I < Sorted.size(); ++I)
			{
				if (Sorted[I].Edge != EdgeNames[J]) { continue; }
				++Props;
				if (Sorted[I].Buried > 0) { ++Hit; }
			}
			char B[200];
			std::snprintf(B, sizeof(B), "%s=%d/%d", EdgeNames[J].c_str(), Hit, Props);
			EdgeRows.push_back(std::string(B));
		}
		// THE NAMED SUBJECT, WHICH IS THE ONE A6 ASKED FOR.
		const int Subject = BurialIndexOf(Sorted, BurialSubjectName());
		std::string SubjectValue, SubjectBy;
		if (Subject < 0)
		{
			SubjectValue = std::string("not-placed/asked=") + BurialSubjectName()
			             + "/over=" + OverOrWords((int)Sorted.size(), In.MeshPiecesInFile);
			SubjectBy = "nothing-measured/0";
		}
		else
		{
			SubjectValue = BurialRowValue(Sorted[(size_t)Subject], In.SubjectCollision);
			SubjectBy = CappedList(Sorted[(size_t)Subject].ByCover, 3,
			                       Sorted[(size_t)Subject].CoverCount, ";", "none");
		}

		std::string Out;
		// SIZED FROM A PRINTED SERIES AND NOT FROM A GUESS, which is rule 2.
		// On the committed street the three chunks measure 472, 396 and 1168
		// characters (vignette-spec-test prints the whole segment's length on
		// every run, and the third chunk is the one with the two capped lists
		// and the subject row in it). 2000 leaves the worst chunk 40 percent
		// of headroom, and AppendChunk announces it if that is ever wrong.
		char B[2000];
		int W = std::snprintf(B, sizeof(B),
			"propsAsMesh=%s propsAsBox=%s propFallbackWhy=%s"
			" propPackageDir=%s propNamePattern=%s<asset>"
			" propScale=1/never-scaled/dims-policy"
			" propCentreWorstMm=%.2f/on=%s/of=%d"
			" propCentreStat=distance-from-the-files-own-xyz-to-the-placed-meshes-world-bounds-centre-at-worst"
			" propSizeWorstMm=%.2f/on=%s propSizeComparable=%s"
			" propSizeStat=axis-aligned-pieces-only/a-yawed-world-aabb-is-legitimately-bigger",
			OverOrWords(In.PlacedAsMesh, In.MeshPiecesInFile).c_str(),
			OverOrWords(In.PlacedAsBox, In.MeshPiecesInFile).c_str(),
			CappedList(In.FellBackOn, 4, In.PlacedAsBox, ";", "none").c_str(),
			NoSpaces(In.PackageDir).c_str(), NoSpaces(In.NamePrefix).c_str(),
			In.CentreWorstMm, NoSpaces(In.CentreWorstOn).c_str(), In.PlacedAsMesh,
			In.SizeWorstMm, NoSpaces(In.SizeWorstOn).c_str(),
			OverOrWords(In.SizeComparable, In.PlacedAsMesh).c_str());
		AppendChunk(Out, B, W, (int)sizeof(B), 1);
		W = std::snprintf(B, sizeof(B),
			" propPlacedWithCollision=%s propPlacedCollisionUnread=%s"
			" propPlacedCollisionNoOn=%s propPlacedCollisionUnknownOn=%s"
			// THE RULED DIVERGENCE, ON THE LINE WHERE THE NUMBERS MEET, A9 of
			// the ruling of 2026-09-09. A reader holding this verdict and an
			// importer log saw UNKNOWN here and NO there for one asset and
			// could not tell a decision from a contradiction. Two populations
			// at two times, ruled 2026-09-08 and written at the enum above:
			// the two tallies are never added, never differenced, and never
			// printed as a pair without their populations beside them.
			" propPlacedCollisionStat=placed-prop-mesh-components-whose-asset-reports-collision"
			"/over-placed-prop-meshes/PROXY-only-a-sweep-answers-whether-a-capsule-is-stopped"
			"/a-missing-body-setup-reads-UNKNOWN-here-and-NO-in-import_prop_meshes.py"
			"/ruled-2026-09-08/two-populations-at-two-times/never-added-never-differenced"
			" propCollisionAsked=%s",
			OverOrWords(In.Collision.Yes, Placed).c_str(),
			OverOrWords(In.Collision.Unknown, Placed).c_str(),
			CappedList(In.Collision.NoOn, 4, In.Collision.No, ";", "none").c_str(),
			CappedList(In.Collision.UnknownOn, 4, In.Collision.Unknown, ";", "none").c_str(),
			// NOT A MEASUREMENT AND SAYS SO IN ITS OWN VALUE. This used to be
			// propCollisionEnabled, which read as a verdict on collision and
			// could not fail: it restates the bool that set it two hundred
			// lines earlier, which is two numbers from one variable. Kept
			// because a reader needs to know which path built the street the
			// other numbers were taken on, renamed so it cannot be mistaken
			// for a reading, and refuted in the ruling of 2026-09-08.
			In.bInteractive ? "QueryOnly/the-walk-path/NOT-A-MEASUREMENT-restates-bInteractive"
			                : "NoCollision/the-timed-automation/NOT-A-MEASUREMENT-restates-bInteractive");
		AppendChunk(Out, B, W, (int)sizeof(B), 2);
		W = std::snprintf(B, sizeof(B),
			" propFootprintsRead=%s"
			" propFootprintGrid=%dx%d/%d-cells-per-prop/a-gap-narrower-than-one-cell-is-invisible-here"
			" propFullyBuried=%s propAnyBuried=%s"
			" propBurialWorst=%s"
			" propBurialStat=fraction-of-a-props-own-footprint-whose-top-is-inside-another-placed-pieces-bounds"
			"/at-worst-by-fraction-then-depth/pct-and-mm-and-cover-name-captured-at-the-same-cell"
			"/depth-is-an-AABB-depth-and-OVERSTATES-a-pitched-slab-by-its-cross-fall-across-its-own-width"
			" propBuriedOn=%s propBuriedByEdge=%s"
			" propBurialSubject=%s propBurialSubjectBy=%s",
			OverOrWords((int)Sorted.size(), In.MeshPiecesInFile).c_str(),
			BurialGridSide(), BurialGridSide(),
			BurialGridSide() * BurialGridSide(),
			OverOrWords(Fully, (int)Sorted.size()).c_str(),
			OverOrWords(AnyBuried, (int)Sorted.size()).c_str(),
			WorstValue.c_str(),
			CappedList(BuriedRows, 3, AnyBuried, ";", "none").c_str(),
			CappedList(EdgeRows, 6, (int)EdgeRows.size(), ";", "nothing-measured").c_str(),
			SubjectValue.c_str(), SubjectBy.c_str());
		AppendChunk(Out, B, W, (int)sizeof(B), 3);
		// ONE IDENTITY, PRINTED ONLY WHEN IT BREAKS. Every placed prop mesh
		// is asked exactly once, so the readings taken and the meshes placed
		// are the same number; they come from two different counters in the
		// .cpp and a key that appears at all means one of them is wrong. A
		// silent disagreement here is what makes a denominator a lie.
		if (Placed != In.PlacedAsMesh)
		{
			char M[128];
			std::snprintf(M, sizeof(M),
			              " propCollisionReadingsMismatch=readings=%d/meshesPlaced=%d",
			              Placed, In.PlacedAsMesh);
			Out += M;
		}
		return Out;
	}

	// ONE LINE PER SHOT, AND THE FRAME TIME IS A MEDIAN AND SAYS SO.
	//
	// `frameMedianMs` is the MEDIAN of `Timed` game-thread frame deltas
	// taken after `Warm` discarded frames. It is NOT the Unity host's
	// number even though both are called a median of 24 after 8: Unity times
	// one Camera.Render() plus GL.Flush(), and this times a whole engine
	// frame including tick, so `frameStat` names which one this is and the
	// two may not be subtracted until something measures the difference.
	inline std::string ShotLine(const std::string& ShotId, const std::string& CamId,
	                            const std::string& CondId, double EyeY,
	                            const std::string& GroundEdge,
	                            double FrameMedianMs, int Timed, int Warm,
	                            int W, int H, double VFovDeg, double HFovDeg,
	                            long long Bytes, const std::string& Status,
	                            const std::string& File, const std::string& Note)
	{
		char Buf[900];
		std::snprintf(Buf, sizeof(Buf),
			"shot %s camera=%s condition=%s status=%s eye=%.3f/on=%s "
			"frameMedianMs=%.2f/of=%dwarm%d frameStat=median-of-engine-frame-deltas "
			"px=%dx%d fovV=%.1f/fovH=%.1f file=%s bytes=%lld note=%s",
			NoSpaces(ShotId).c_str(), NoSpaces(CamId).c_str(), NoSpaces(CondId).c_str(),
			NoSpaces(Status).c_str(), EyeY, NoSpaces(GroundEdge).c_str(),
			FrameMedianMs, Timed, Warm, W, H, VFovDeg, HFovDeg,
			NoSpaces(File).c_str(), Bytes, NoSpaces(Note).c_str());
		return std::string(Buf);
	}

	// ---- QUEUE 186: THE SKY, AS READ BACK OFF THE ENGINE -----------------
	//
	// WHY THIS IS HERE AND NOT IN THE .cpp. Until 2026-09-09 the scene line
	// carried skyModel=none-black/phase-C-owns-the-hdri and
	// ambientModel=trilight-3-directional/not-a-captured-sky as HARDCODED
	// LITERALS inside a printf format string in VignetteShot.cpp. Both were
	// claims about the engine that no run ever checked, and one of them was
	// false: the day frame's top band measures 249.5/250.0/250.5 mean RGB
	// over 8858 pixels, which is a pale field and not a black one. A literal
	// in a format string cannot be wrong about the world in any way a test
	// can catch, so the words now come from THESE FUNCTIONS, which g++ runs
	// before any dispatch, out of state the .cpp READ BACK off the actors.
	//
	// WHAT THE .cpp SUPPLIES: live state only. Whether each actor and each
	// component is there, what the component says its own mode and intensity
	// are AFTER being written, and how many times each was written. Not one
	// word of the printed string is decided up there.
	struct SkyIn
	{
		// SPAWNED, read back as a pointer being non-null at the moment the
		// scene line is built, not as a spawn call having returned.
		bool bSkyLightActor;
		bool bSkyLightComponent;
		bool bAtmosphereActor;
		bool bAtmosphereComponent;
		bool bFogComponent;
		// WHAT THE COMPONENT SAYS AFTER THE WRITE, never what was asked for.
		// SourceTypeRead is the engine's own enum value; 0 is its captured
		// scene and 1 its specified cubemap in this engine version, and the
		// number is printed rather than translated so a version that
		// renumbers them cannot silently print the wrong word.
		int    SourceTypeRead;
		bool   bRealTimeCaptureRead;
		double SkyIntensityRead;
		// ---- QUEUE 205: THE SUN, READ OFF ITS OWN COMPONENT ------------
		//
		// The verdict has only ever carried `sun=yes`, which says a
		// directional light was SPAWNED and nothing about what it is. A
		// key that echoes the value just written proves nothing either,
		// so every one of these is asked of the live component after the
		// write, exactly as the sky keys above are.
		//
		// WHAT STATISTIC THESE ARE: one per run, LAST-WINS, taken when a
		// verdict asks for the scene line, so they describe the LAST
		// condition the run applied and not each frame. The per-frame
		// answer is on the shot line, which is where a ladder reads it.
		bool   bSunActor;
		bool   bSunComponent;
		double SunIntensityRead;
		bool   bSunCastShadowsRead;
		double SunPitchRead;
		double SunYawRead;
		// THE ENGINE'S OWN ENUM VALUE, PRINTED AND NOT TRANSLATED, for the
		// same reason SourceTypeRead is: a version that renumbers the enum
		// cannot then make this key print the wrong word.
		int    SunMobilityRead;
		double FogDensityRead;
		double FogMaxOpacityRead;
		// THE AMBIENT MODEL IS A DECISION AND IT IS MADE HERE, from the two
		// booleans that decide it: whether the sky is structurally present,
		// and whether the three fill directionals were retired to zero.
		bool   bFillsRetired;
		int    FillsSpawned;
		// WRITE-ON-CHANGE, COUNTED BOTH WAYS. ApplyCondition is re-entered
		// every tick while a condition settles, so a sky recaptured per tick
		// is a rebuild asked for four times. Asked is how many times
		// ApplyCondition ran; Fired is how many times the sky was actually
		// rewritten. Asked > Fired is the whole point and is not a fault.
		int    ApplyCalls;
		int    SkyWrites;
		// THE HDRI THE SHARED FILE NAMES, AND WHAT BECAME OF IT. This run
		// binds nothing from it; these keys exist so the NEXT run does not
		// have to guess whether the file is even reachable from the packaged
		// binary. BoundAs is the honest word and it is expected to say the
		// file was not bound.
		std::string HdriAsked;
		std::string HdriFoundAt;
		long long   HdriBytes;
		std::string HdriDetectedAs;
		std::string HdriBoundAs;
		SkyIn() : bSkyLightActor(false), bSkyLightComponent(false),
		          bAtmosphereActor(false), bAtmosphereComponent(false),
		          bFogComponent(false), SourceTypeRead(-1),
		          bRealTimeCaptureRead(false), SkyIntensityRead(0.0),
		          bSunActor(false), bSunComponent(false), SunIntensityRead(0.0),
		          bSunCastShadowsRead(false), SunPitchRead(0.0), SunYawRead(0.0),
		          SunMobilityRead(-1),
		          FogDensityRead(0.0), FogMaxOpacityRead(0.0),
		          bFillsRetired(false), FillsSpawned(0),
		          ApplyCalls(0), SkyWrites(0),
		          HdriAsked("none"), HdriFoundAt("NOT-LOOKED-FOR"),
		          HdriBytes(0), HdriDetectedAs("not-read"),
		          HdriBoundAs("NOTHING") {}
		// THE SKY IS STRUCTURALLY PRESENT only when every piece of it is.
		// A skylight with no atmosphere captures a black scene, which is the
		// exact failure the fill-light comment in VignetteShot.cpp warned
		// about before any of this existed.
		bool Whole() const
		{
			return bSkyLightActor && bSkyLightComponent
			    && bAtmosphereActor && bAtmosphereComponent;
		}
	};

	// THE MODEL WORDS. Each names the mechanism AND the thing a reader would
	// otherwise assume: an atmosphere is not a photographed sky, and a sky
	// that failed to spawn must not read as a sky that is dark.
	inline std::string SkyModelWord(const SkyIn& In)
	{
		if (In.Whole()) { return "skyatmosphere+skylight-realtime-capture/not-an-hdri"; }
		if (In.bAtmosphereActor && !In.bSkyLightActor)
		{
			return "SKYLIGHT-MISSING/atmosphere-visible-but-nothing-captures-it";
		}
		if (!In.bAtmosphereActor && In.bSkyLightActor)
		{
			return "ATMOSPHERE-MISSING/skylight-would-capture-a-black-scene";
		}
		return "SPAWN-FAILED/no-sky-of-any-kind/the-far-field-is-the-height-fog";
	}

	inline std::string AmbientModelWord(const SkyIn& In)
	{
		if (In.Whole() && In.bFillsRetired)
		{
			return "skylight-captured-sky/ONE-OWNER/trilight-retired-to-zero";
		}
		if (In.Whole() && !In.bFillsRetired)
		{
			return "skylight+trilight/TWO-CONTRIBUTORS/the-sky-did-not-take-ownership";
		}
		return "trilight-3-directional/not-a-captured-sky/the-sky-is-not-whole";
	}

	// THE FOUR SUN KEYS, AND A MISSING COMPONENT PRINTS WORDS RATHER THAN
	// ZEROS. A sun that failed to spawn reading sunIntensityRead=0.000 is
	// the same string as a sun that is off, and those are different facts;
	// nothing-measured is what a never-read value says here.
	inline std::string SunSegment(const SkyIn& In)
	{
		char Buf[700];
		if (!In.bSunActor || !In.bSunComponent)
		{
			std::snprintf(Buf, sizeof(Buf),
				"sun=%s sunComponent=%s sunIntensityRead=nothing-measured "
				"sunCastShadowsRead=nothing-measured sunPitchYawRead=nothing-measured "
				"sunMobilityRead=nothing-measured "
				"sunReadStat=one-per-run/last-wins/off-the-component-after-the-last-condition-applied",
				In.bSunActor ? "yes" : "SPAWN-FAILED",
				In.bSunComponent ? "yes" : "NOT-FOUND");
			return std::string(Buf);
		}
		std::snprintf(Buf, sizeof(Buf),
			"sun=yes sunComponent=yes sunIntensityRead=%.3f "
			"sunCastShadowsRead=%s sunPitchYawRead=%.1f/%.1f sunMobilityRead=%d "
			"sunMobilityKey=0-static/1-stationary/2-movable/engine-enum-printed-not-translated "
			"sunReadStat=one-per-run/last-wins/off-the-component-after-the-last-condition-applied",
			In.SunIntensityRead, In.bSunCastShadowsRead ? "yes" : "NO",
			In.SunPitchRead, In.SunYawRead, In.SunMobilityRead);
		return std::string(Buf);
	}

	// ---- QUEUE 205: THE LIGHT THAT TOOK ONE FRAME, ON THAT FRAME'S LINE -
	//
	// PER-SAMPLE, NOT PER-RUN. The sun segment above is one reading of the
	// last condition a run applied; a ladder renders six conditions in one
	// run, so five of its six frames would have no readback at all if the
	// scene line were the only place this was asked. These keys are taken
	// off the same components at the moment THIS frame was photographed,
	// which is what lets a rung of the ladder be attributed to the sun
	// that lit it rather than to the row of a data file.
	// A1(c), 2026-09-09, AND IT IS CONDITION C5, BLOCKING: THE ASKED VALUE
	// RIDES BESIDE THE READ ONE ON EVERY CELL'S OWN LINE.
	//
	// Run 38 printed five rungs that all read sky 1.000 and one control row
	// that read 0.350, and the CROSS WAS NEVER PRINTED, so the cell that
	// mattered (a middle sky with the sun in force) had never been rendered
	// and nothing in the verdict said so. A grid of twelve cells is twelve
	// chances to render the wrong row and read it as the right one. The ask
	// comes from the condition this frame was photographed under; the read is
	// off the live components. A cell that could not be read prints the words.
	//
	// THE AGREEMENT IS DECIDED HERE, where the tests run, so the run line's
	// tally and this line's verdict cannot drift apart.
	inline double CellAgreeTol() { return 0.001; }
	inline bool CellAgrees(double Asked, double Read) 
	{
		return std::fabs(Read - Asked) < CellAgreeTol();
	}

	inline std::string ShotLightLine(bool bSunComponent, double SunIntensityAsked,
	                                 double SunIntensityRead,
	                                 bool bCastShadowsRead, double PitchRead,
	                                 double YawRead, int MobilityRead,
	                                 bool bSkyComponent, double SkyIntensityAsked,
	                                 double SkyIntensityRead)
	{
		char Buf[900];
		char Sun[420];
		if (bSunComponent)
		{
			std::snprintf(Sun, sizeof(Sun),
				"shotSunIntensityAsked=%.3f shotSunIntensityRead=%.3f "
				"shotSunCastShadowsRead=%s "
				"shotSunPitchYawRead=%.1f/%.1f shotSunMobilityRead=%d",
				SunIntensityAsked, SunIntensityRead, bCastShadowsRead ? "yes" : "NO",
				PitchRead, YawRead, MobilityRead);
		}
		else
		{
			std::snprintf(Sun, sizeof(Sun),
				"shotSunIntensityAsked=%.3f shotSunIntensityRead=nothing-measured "
				"shotSunCastShadowsRead=nothing-measured "
				"shotSunPitchYawRead=nothing-measured shotSunMobilityRead=nothing-measured",
				SunIntensityAsked);
		}
		char Sky[200];
		if (bSkyComponent)
		{
			std::snprintf(Sky, sizeof(Sky),
				"shotSkyIntensityAsked=%.3f shotSkyIntensityRead=%.3f",
				SkyIntensityAsked, SkyIntensityRead);
		}
		else
		{
			std::snprintf(Sky, sizeof(Sky),
				"shotSkyIntensityAsked=%.3f shotSkyIntensityRead=nothing-measured",
				SkyIntensityAsked);
		}
		// THE CELL'S OWN VERDICT, AND A CELL THAT WAS NOT READ IS NOT A
		// CELL THAT AGREED. Rule 3b: nothing-measured, never a quiet yes.
		const char* Agree = "nothing-measured/no-component-answered-on-this-frame";
		if (bSunComponent && bSkyComponent)
		{
			Agree = (CellAgrees(SunIntensityAsked, SunIntensityRead)
			         && CellAgrees(SkyIntensityAsked, SkyIntensityRead))
			      ? "yes" : "NO/the-frame-was-lit-by-numbers-this-row-did-not-ask-for";
		}
		std::snprintf(Buf, sizeof(Buf),
			"%s %s shotCellAgrees=%s "
			"shotLightStat=read-off-the-components-while-THIS-frame-stood/per-sample-not-per-run/"
			"asked-comes-from-the-condition-row-this-frame-was-photographed-under",
			Sun, Sky, Agree);
		return std::string(Buf);
	}

	// THE WHOLE-RUN TALLY OF THE SAME QUESTION, ONE NUMBER OVER ITS OWN
	// DENOMINATOR. Twelve grid cells live inside Measured, and the count that
	// matters for condition C5 is that every cell read back what it asked
	// for; a run that photographed nothing says the words rather than
	// printing 0/0, which reads as a clean sweep.
	inline std::string CellAgreeLine(int Agree, int Measured, int Asked)
	{
		char Buf[520];
		if (Measured == 0)
		{
			std::snprintf(Buf, sizeof(Buf),
				"cellAgree=nothing-measured/of=%d/shots-asked "
				"cellAgreeStat=one-per-run/counted-over-shots-whose-sun-and-sky-components-both-answered/"
				"a-cell-that-was-not-read-is-not-a-cell-that-agreed",
				Asked);
			return std::string(Buf);
		}
		std::snprintf(Buf, sizeof(Buf),
			"cellAgree=%d/of=%d/read cellAgreeRead=%d/of=%d/asked cellAgreeTolUnitless=%.3f "
			"cellAgreeStat=one-per-run/counted-over-shots-whose-sun-and-sky-components-both-answered/"
			"asked-is-the-condition-row-read-is-the-live-component/"
			"a-cell-that-was-not-read-is-not-a-cell-that-agreed",
			Agree, Measured, Measured, Asked, CellAgreeTol());
		return std::string(Buf);
	}

	// ---- A6: WHERE EVERY DIRECTIONAL LIGHT WAS AIMED, ASKED BESIDE READ -
	//
	// WHY THIS EXISTS, AND IT IS CLAUDE.md RULE 6 WITH A NUMBER ON IT.
	// production/specs/vignette-pieces.json asks for a sun 36 degrees above
	// the horizon, SunPitchDeg turns that into an asked pitch of -36.0, and
	// every run of this rig rendered a sun at -82.0: off by exactly 46.0 with
	// the yaw agreeing to the decimal. The arithmetic was tested
	// (vignette-spec-test.cpp:404) and the format string was tested (:2058)
	// and NOTHING TESTED THAT THE NUMBER REACHED THE LIGHT. The same rig
	// already differences asked against read for the camera
	// (shotCamAskedPitchYaw beside shotCamReadPitchYaw) and for every prop
	// (propCentreWorstMm against the file's own coordinates); the lights were
	// the one actor population nobody differenced, and 46 degrees hid there
	// for every run the key has existed. A 4 m lamp post casts 5.5 m at the
	// asked elevation and 0.56 m at the rendered one.
	//
	// WHOLE-RUN, NOT PER-SAMPLE, and the reason is mechanical rather than
	// stylistic: the rotation is written once at spawn and never rewritten,
	// so it is a fact about the run and not about a frame. The per-sample
	// shotSunPitchYawRead above STAYS, because a per-sample read is what
	// would catch a later write.
	//
	// ASKED IS CAPTURED AT THE SPAWN CALL, not re-derived here from the spec:
	// re-deriving it would compare the formula against itself and agree
	// whatever the spawner did with the value.
	struct LightAim
	{
		std::string Name;    // sun / fillA / fillB / fillC
		bool   bSpawned;     // the actor exists
		bool   bRead;        // a component answered; false prints the words
		double AskedPitch, AskedYaw;
		double ReadPitch, ReadYaw;
		LightAim() : Name("unnamed"), bSpawned(false), bRead(false),
		             AskedPitch(0.0), AskedYaw(0.0), ReadPitch(0.0), ReadYaw(0.0) {}
	};

	// A SIGNED RESIDUAL ON A CIRCLE, AND THE WRAP IS NOT COSMETIC. FRotator
	// normalises each axis to (-180,180], so fill B asked for yaw 200.0 reads
	// back as -160.0, which is THE SAME DIRECTION. A naive subtraction would
	// print -360.0000 and refuse a light that is aimed exactly where it was
	// sent. Wrapped, that pair reads 0.0000.
	inline double AngleResidualDeg(double ReadDeg, double AskedDeg)
	{
		double D = ReadDeg - AskedDeg;
		while (D <= -180.0) { D += 360.0; }
		while (D >   180.0) { D -= 360.0; }
		return D;
	}

	// THE REFUSAL BOUND, AND THIS IS NOT A MEASURED TOLERANCE. It is a CLASS
	// SEPARATOR between the fault it must catch, 46.0 degrees, and the float
	// round trip it must not, which is of order 1e-4. If any run ever prints
	// a residual between 0.001 and 1.0, the bound gets set from that printed
	// series and not before. Ruled 2026-09-09, A6 amendment (a).
	inline double LightAimRefuseAtDeg() { return 1.0; }

	inline bool LightAimAgrees(const LightAim& L)
	{
		if (!L.bSpawned || !L.bRead) { return false; }
		return std::fabs(AngleResidualDeg(L.ReadPitch, L.AskedPitch)) < LightAimRefuseAtDeg()
		    && std::fabs(AngleResidualDeg(L.ReadYaw,   L.AskedYaw))   < LightAimRefuseAtDeg();
	}

	// ONE NUMBER, FORMATTED ONCE, so no caller can print a degree with a
	// different number of decimals than the residual it is compared against.
	inline std::string Deg1(double V)
	{
		char B[48];
		std::snprintf(B, sizeof(B), "%.1f", V);
		return std::string(B);
	}
	inline std::string Deg4(double V)
	{
		char B[48];
		std::snprintf(B, sizeof(B), "%.4f", V);
		return std::string(B);
	}

	// THE WHOLE-RUN LINE. OfAsked is how many directional lights this rig
	// spawns, supplied by the caller so a light added to the rig and left out
	// of this list shows up as a denominator that does not match rather than
	// as silence.
	//
	// NO CAP, SAID OUT LOUD: every light in the population prints its own
	// three keys. The population is four, a cap would hide the thing the line
	// exists to show, and the one place this project has been bitten by a cap
	// is a cap that hid a hundred per cent of its own list.
	inline std::string LightAimLine(const std::vector<LightAim>& Lights, int OfAsked)
	{
		int Spawned = 0, Read = 0, Agreeing = 0;
		double Worst = 0.0;
		std::string WorstOn = "none", WorstAxis = "none";
		bool bAnyRead = false;
		for (size_t I = 0; I < Lights.size(); ++I)
		{
			if (Lights[I].bSpawned) { ++Spawned; }
			if (!Lights[I].bSpawned || !Lights[I].bRead) { continue; }
			++Read;
			if (LightAimAgrees(Lights[I])) { ++Agreeing; }
			const double RP = AngleResidualDeg(Lights[I].ReadPitch, Lights[I].AskedPitch);
			const double RY = AngleResidualDeg(Lights[I].ReadYaw,   Lights[I].AskedYaw);
			if (!bAnyRead || std::fabs(RP) > std::fabs(Worst))
			{
				Worst = RP; WorstOn = NoSpaces(Lights[I].Name); WorstAxis = "pitch";
			}
			if (std::fabs(RY) > std::fabs(Worst))
			{
				Worst = RY; WorstOn = NoSpaces(Lights[I].Name); WorstAxis = "yaw";
			}
			bAnyRead = true;
		}
		// THE STATUS WORD FAILS CLOSED. A run that read no light has not
		// landed this fix either, so NOTHING-MEASURED is not a pass; the
		// only passing word is AGREES, and the CI step reads this key.
		std::string Status = "REFUSED";
		if (Read == 0) { Status = "NOTHING-MEASURED"; }
		else if (Agreeing == Read && Read == OfAsked && Spawned == OfAsked) { Status = "AGREES"; }
		std::string Out = "lightAimStatus=" + Status;
		Out += " lightAimSpawned=" + std::to_string(Spawned) + "/of=" + std::to_string(OfAsked)
		     + "/directional-lights-this-rig-spawns";
		Out += " lightAimRead=" + std::to_string(Read) + "/of=" + std::to_string(Spawned)
		     + "/spawned";
		Out += " lightAimAgreeing=" + std::to_string(Agreeing) + "/of=" + std::to_string(Read)
		     + "/read";
		if (bAnyRead)
		{
			Out += " lightAimWorstResidualDeg=" + Deg4(Worst) + "/on=" + WorstOn
			     + "/axis=" + WorstAxis + "/at-worst-over-the-population-signed";
		}
		else
		{
			Out += " lightAimWorstResidualDeg=nothing-measured/no-light-component-answered";
		}
		Out += " lightAimRefuseAtDeg=" + Deg1(LightAimRefuseAtDeg())
		     + "/NOT-A-MEASURED-TOLERANCE/a-class-separator-between-the-46.0-fault-and-a-1e-4-float-round-trip";
		for (size_t I = 0; I < Lights.size(); ++I)
		{
			const LightAim& L = Lights[I];
			const std::string N = "lightAim." + NoSpaces(L.Name);
			if (!L.bSpawned)
			{
				Out += " " + N + "=SPAWN-FAILED";
				Out += " " + N + ".askedPitchYaw=" + Deg1(L.AskedPitch) + "/" + Deg1(L.AskedYaw);
				Out += " " + N + ".readPitchYaw=nothing-measured";
				Out += " " + N + ".residualPitchYawDeg=nothing-measured";
				continue;
			}
			if (!L.bRead)
			{
				Out += " " + N + "=NO-COMPONENT";
				Out += " " + N + ".askedPitchYaw=" + Deg1(L.AskedPitch) + "/" + Deg1(L.AskedYaw);
				Out += " " + N + ".readPitchYaw=nothing-measured";
				Out += " " + N + ".residualPitchYawDeg=nothing-measured";
				continue;
			}
			Out += " " + N + "=" + (LightAimAgrees(L) ? "AGREES" : "REFUSED");
			Out += " " + N + ".askedPitchYaw=" + Deg1(L.AskedPitch) + "/" + Deg1(L.AskedYaw);
			Out += " " + N + ".readPitchYaw=" + Deg1(L.ReadPitch) + "/" + Deg1(L.ReadYaw);
			Out += " " + N + ".residualPitchYawDeg="
			     + Deg4(AngleResidualDeg(L.ReadPitch, L.AskedPitch)) + "/"
			     + Deg4(AngleResidualDeg(L.ReadYaw,   L.AskedYaw));
		}
		Out += " lightAimStat=one-per-run/the-rotation-is-written-once-at-spawn-and-never-rewritten/"
		       "asked-is-the-rotation-handed-to-the-spawn-call/read-is-the-light-components-world-rotation/"
		       "residual-is-read-minus-asked-wrapped-to-plus-or-minus-180-so-a-yaw-of-200-reading-back-as-"
		       "minus-160-is-zero";
		return Out;
	}

	// ---- QUEUE 208: THE CAMERA THAT TOOK ONE FRAME, ON THAT FRAME'S LINE -
	//
	// PER-SAMPLE, NOT PER-RUN, and it is the same rule ShotLightLine above
	// obeys one bracket away. Until 2026-09-09 the whole verdict carried a
	// single shotCam line that the shot loop OVERWROTE, so the camera a frame
	// was taken from was a per-sample fact printed once on the whole-run line,
	// last-wins. MEASURED, NOT ARGUED: tools/frame-shadow-probe.py reads that
	// line, and on run 38 it refused every ladder frame with
	// camBind=REFUSED probeStatus=REFUSED probe=nothing-measured, because the
	// last camera the run placed was not the one the frame it was asked about
	// was taken from. The tool fails closed, which is correct; the verdict is
	// what could not answer it. A RUN WHOSE SHOT ORDER DECIDES WHETHER A TOOL
	// CAN READ IT IS ONE REORDERING FROM SILENCE.
	//
	// WHAT THE .cpp SUPPLIES: the transform it ASKED FOR and the transform it
	// READ BACK off the player view point, never one standing in for the
	// other, and a status word for the case where there was nothing to read.
	// The distance between the two is computed HERE, because measurement
	// arithmetic belongs where the tests run.
	struct ShotCamIn
	{
		std::string CamId;
		// MEASURED / NO-WORLD / SPAWN-FAILED / NO-VIEWPOINT / NO-SUCH-CAMERA
		// / NOT-REACHED. Only MEASURED prints numbers.
		std::string Status;
		double AskedXCm, AskedYCm, AskedZCm;
		double ReadXCm, ReadYCm, ReadZCm;
		double AskedPitchDeg, AskedYawDeg;
		double ReadPitchDeg, ReadYawDeg;
		ShotCamIn() : CamId("none"), Status("NOT-REACHED"),
		              AskedXCm(0.0), AskedYCm(0.0), AskedZCm(0.0),
		              ReadXCm(0.0), ReadYCm(0.0), ReadZCm(0.0),
		              AskedPitchDeg(0.0), AskedYawDeg(0.0),
		              ReadPitchDeg(0.0), ReadYawDeg(0.0) {}
	};

	// HOW FAR THE CAMERA ENDED UP FROM WHERE IT WAS SENT, in centimetres.
	// Asking for a transform and printing the transform you asked for is not
	// evidence that anything moved, so the pair is printed and this is the
	// distance between the halves.
	inline double ShotCamDeltaCm(const ShotCamIn& In)
	{
		const double DX = In.ReadXCm - In.AskedXCm;
		const double DY = In.ReadYCm - In.AskedYCm;
		const double DZ = In.ReadZCm - In.AskedZCm;
		return std::sqrt(DX * DX + DY * DY + DZ * DZ);
	}

	inline std::string ShotCamSegment(const ShotCamIn& In)
	{
		char Buf[600];
		const std::string Id = NoSpaces(In.CamId.empty() ? std::string("none") : In.CamId);
		const std::string St = NoSpaces(In.Status.empty() ? std::string("NOT-REACHED") : In.Status);
		if (St != "MEASURED")
		{
			std::snprintf(Buf, sizeof(Buf),
				"shotCamId=%s shotCamRead=%s "
				"shotCamAskedXYZcm=nothing-measured shotCamReadXYZcm=nothing-measured "
				"shotCamDeltaCm=nothing-measured "
				"shotCamAskedPitchYaw=nothing-measured shotCamReadPitchYaw=nothing-measured "
				"shotCamStat=asked-against-read-back-off-the-player-view-point-while-THIS-frame-"
				"stood/per-sample-not-per-run",
				Id.c_str(), St.c_str());
			return std::string(Buf);
		}
		std::snprintf(Buf, sizeof(Buf),
			"shotCamId=%s shotCamRead=MEASURED "
			"shotCamAskedXYZcm=%.1f/%.1f/%.1f shotCamReadXYZcm=%.1f/%.1f/%.1f "
			"shotCamDeltaCm=%.2f "
			"shotCamAskedPitchYaw=%.1f/%.1f shotCamReadPitchYaw=%.1f/%.1f "
			"shotCamStat=asked-against-read-back-off-the-player-view-point-while-THIS-frame-"
			"stood/per-sample-not-per-run",
			Id.c_str(),
			In.AskedXCm, In.AskedYCm, In.AskedZCm,
			In.ReadXCm, In.ReadYCm, In.ReadZCm,
			ShotCamDeltaCm(In),
			In.AskedPitchDeg, In.AskedYawDeg, In.ReadPitchDeg, In.ReadYawDeg);
		return std::string(Buf);
	}

	inline std::string SkySegment(const SkyIn& In)
	{
		// GROWN FOR THE SUN SEGMENT. snprintf truncates in silence, which
		// on a verdict line is a key that vanishes rather than an error.
		char Buf[2200];
		std::snprintf(Buf, sizeof(Buf),
			"skyModel=%s ambientModel=%s "
			"skyLight=%s skyLightComponent=%s skyAtmosphere=%s skyAtmosphereComponent=%s "
			"skySourceTypeRead=%d skyRealTimeCaptureRead=%s skyIntensityRead=%.3f "
			"%s "
			"skyWrites=%d/of=%d/applyCondition-calls/write-once-per-shot-never-per-settle-tick "
			"fogComponent=%s fogDensityRead=%.4f fogMaxOpacityRead=%.3f "
			"fillsRetiredToZero=%s fillsSpawned=%d/3 "
			"skyHdriAsked=%s skyHdriFoundAt=%s skyHdriBytes=%lld skyHdriDetectedAs=%s "
			"skyHdriBoundAs=%s "
			"skyReadStat=every-value-above-is-read-back-off-the-component-after-the-write/"
			"never-the-value-that-was-asked-for",
			SkyModelWord(In).c_str(), AmbientModelWord(In).c_str(),
			In.bSkyLightActor ? "yes" : "SPAWN-FAILED",
			In.bSkyLightComponent ? "yes" : "NOT-FOUND",
			In.bAtmosphereActor ? "yes" : "SPAWN-FAILED",
			In.bAtmosphereComponent ? "yes" : "NOT-FOUND",
			In.SourceTypeRead, In.bRealTimeCaptureRead ? "yes" : "no",
			In.SkyIntensityRead, SunSegment(In).c_str(), In.SkyWrites, In.ApplyCalls,
			In.bFogComponent ? "yes" : "NOT-FOUND",
			In.FogDensityRead, In.FogMaxOpacityRead,
			In.bFillsRetired ? "yes" : "no", In.FillsSpawned,
			In.HdriAsked.c_str(), In.HdriFoundAt.c_str(), In.HdriBytes,
			In.HdriDetectedAs.c_str(), In.HdriBoundAs.c_str());
		return std::string(Buf);
	}

	// ---- THE NULL SERIES IS SEVEN SAMPLES, NOT ONE PAIR ------------------
	//
	// C4 as amended by section 4 and section 9 of
	// game-design/decision-2026-09-09-ruling-the-grid-batch-review.md, and
	// amendment 2's engine form, which that record made due on the next commit
	// that touches the verdict-writing path of VignetteShot.cpp. This commit
	// touches it.
	//
	// WHAT THE REVIEW FOUND, BY HAND, ON FIELD VALUES. Seven of the 25 shots
	// have IDENTICAL rendering inputs in this engine: vign_hook_day,
	// vign_grid_sky100_sun003, vign_fog_maxop0450, vign_wet_000, vign_wet_060,
	// vign_wet_100 and vign_grid_null_repeat, at shot positions 5, 7, 18, 22,
	// 23, 24 and 25. They arrived by accident, because four probe families
	// share one reference cell, and the judged hook frame is itself a member.
	// A ONE-PAIR DIFFERENCE CANNOT TELL A MONOTONE DRIFT FROM A STEP, which is
	// the confound that made the sun ladder unreadable; seven samples spanning
	// the run give a SPREAD and an ORDERING, and the smallest sky step the grid
	// can claim is read against that spread rather than against one
	// subtraction.
	//
	// NOTHING HERE NAMES A SHOT. The group is DISCOVERED from the conditions,
	// by the fields this engine applies, so a row added or removed by a later
	// ruling moves the series without anybody editing this function. Seven is
	// a reading, never a constant.
	//
	// WETNESS IS EXCLUDED AND THE STRING SAYS WHY. VignetteShot.cpp has no
	// read site for `wetness` on this commit: three hits in the whole ue-probe
	// tree, all in this header. Two conditions differing only in wetness
	// therefore render the same street HERE, which is what makes wet_000,
	// wet_060 and wet_100 null samples in this engine. The other engine does
	// read it, at ledger/Assets/Scripts/Game/StreetVignetteHost.cs line 715,
	// so the same arithmetic in Unity gives a different group and this
	// function is named for the engine it speaks for.
	// AND THE EXPOSURE PIN IS PART OF THE FINGERPRINT, QUEUE 235. Two
	// conditions differing only in exposure_pin render the same street at two
	// different exposures, so they are NOT null samples of each other. Left
	// out of this key, the eight ladder rows of 2026-09-10 would have formed
	// the largest identical-input group at cam_hook, nine against the day
	// group's seven, and the ladder's DELIBERATE spread would have been
	// published as this run's noise floor: the largest number in the
	// comparison wearing the name of the smallest, which is the fault
	// SampleKey's camera half already exists to stop.
	inline std::string AppliedFieldsUnreal(const Condition& C, bool bWithSky)
	{
		char Buf[384];
		if (bWithSky)
		{
			std::snprintf(Buf, sizeof(Buf),
				"sun.%s/sunI%.3f/skyI%.4f/hdri.%s/fog%.4f/fogMaxOp%.3f/lant.%s/prac.%s/expPin%.4f",
				C.SunOn ? "on" : "off", C.SunIntensity, C.SkyIntensity,
				NoSpaces(C.Hdri).c_str(), C.FogDensity, C.FogMaxOpacity,
				C.LanternsOn ? "on" : "off", C.WindowsOn ? "on" : "off", C.ExposurePin);
		}
		else
		{
			std::snprintf(Buf, sizeof(Buf),
				"sun.%s/sunI%.3f/hdri.%s/fog%.4f/fogMaxOp%.3f/lant.%s/prac.%s/expPin%.4f",
				C.SunOn ? "on" : "off", C.SunIntensity,
				NoSpaces(C.Hdri).c_str(), C.FogDensity, C.FogMaxOpacity,
				C.LanternsOn ? "on" : "off", C.WindowsOn ? "on" : "off", C.ExposurePin);
		}
		return std::string(Buf);
	}

	// ONE MEASURED FRAME, AS MUCH OF IT AS THE SPREAD NEEDS. The .cpp fills
	// these in shot order as the frames are measured, which is the only order
	// that can answer "is the drift monotone in shot order".
	struct FrameSample
	{
		std::string ShotId;
		std::string CameraId;      // see SampleKey: a different camera is a different picture
		std::string Applied;       // the fields this engine applies, sky included
		std::string AppliedNoSky;  // the same without sky, for the sky-only pairs
		double SkyIntensity;
		bool   bMeasured;          // a frame landed and was measured
		double MeanLuma, GroundP05, GroundP50;
		FrameSample() : SkyIntensity(0), bMeasured(false),
		                MeanLuma(0), GroundP05(0), GroundP50(0) {}
	};

	// THE CAMERA IS PART OF THE FINGERPRINT, AND THIS IS A READING AND NOT A
	// PRECAUTION. With the fields alone the live file's largest identical-input
	// group comes back as NINE frames, not the review's seven: vign_camA_day
	// and vign_camB_day carry `overcast_day` too, so their rendering inputs are
	// identical and their PICTURES are not, because they are shot from other
	// cameras. A spread taken over those nine would be a camera difference
	// reported as a noise floor, which is the largest number in the comparison
	// wearing the name of the smallest. The review's seven is right, and it is
	// right because every one of them stands at cam_hook.
	inline std::string SampleKey(const FrameSample& S, bool bWithSky)
	{
		return std::string("cam.") + NoSpaces(S.CameraId) + "/"
		     + (bWithSky ? S.Applied : S.AppliedNoSky);
	}

	inline double SampleStat(const FrameSample& S, int Which)
	{
		if (Which == 0) { return S.MeanLuma; }
		if (Which == 1) { return S.GroundP05; }
		return S.GroundP50;
	}

	inline const char* SampleStatName(int Which)
	{
		if (Which == 0) { return "MeanLuma"; }
		if (Which == 1) { return "GroundP05"; }
		return "GroundP50";
	}

	// THE LINE. WHOLE-RUN KEYS ONLY: every number here is a statistic OVER the
	// run's frames and none of them is true of one frame, so none of them may
	// ride on a sample line.
	inline std::string NullSeriesLine(const std::vector<FrameSample>& All)
	{
		int Measured = 0;
		for (size_t I = 0; I < All.size(); ++I)
		{
			if (All[I].bMeasured) { ++Measured; }
		}
		if (Measured == 0)
		{
			char Buf[420];
			std::snprintf(Buf, sizeof(Buf),
				"nullSeriesStatus=NOTHING-MEASURED nullSeriesSamples=nothing-measured/of=%d"
				"/shots-offered nullSeriesIds=none nullSeriesVerdict=nothing-measured"
				" nullSeriesStat=whole-run/no-frame-was-measured-so-there-is-no-noise-floor",
				(int)All.size());
			return std::string(Buf);
		}
		// THE GROUP: the largest set of measured frames sharing one applied
		// fingerprint. Largest, because the noise floor is read off the widest
		// set of frames the run renders identically; a tie keeps the first
		// group in shot order, and the tie is printed rather than hidden.
		//
		// THE TIE COUNTER COUNTS GROUPS, AND IT COUNTED FRAMES UNTIL
		// AMENDMENT 5 of
		// game-design/decision-2026-09-10-ruling-the-four-lane-batch.md
		// section 9. The old loop ran over FRAMES and incremented once per
		// frame of a rival group, so ONE rival group of seven frames printed
		// nullSeriesTiedGroups=7 and read as seven rival groups: the key's
		// name was not what the number was a statistic of. It was latent only
		// because the live spec has a single largest group, and it would have
		// gone live and wrong on the first real tie, which is exactly when a
		// reader would lean on it.
		//
		// So the frames are collapsed to DISTINCT groups FIRST, each counted
		// once, and the tie count is the number of distinct groups whose size
		// equals the largest, MINUS the one that is kept. Keys are recorded in
		// shot order of first appearance and the winner is taken on a STRICT
		// greater-than, so the kept group is still the first in shot order.
		// The denominator is the number of distinct groups examined, because a
		// bare zero here cannot tell no rival apart from nothing looked at.
		std::vector<std::string> GroupKeys;
		std::vector<int> GroupSizes;
		for (size_t I = 0; I < All.size(); ++I)
		{
			if (!All[I].bMeasured) { continue; }
			const std::string K = SampleKey(All[I], true);
			size_t At = GroupKeys.size();
			for (size_t Q = 0; Q < GroupKeys.size(); ++Q)
			{
				if (GroupKeys[Q] == K) { At = Q; break; }
			}
			if (At == GroupKeys.size()) { GroupKeys.push_back(K); GroupSizes.push_back(0); }
			++GroupSizes[At];
		}
		std::string BestKey;
		int Best = 0;
		for (size_t Q = 0; Q < GroupKeys.size(); ++Q)
		{
			if (GroupSizes[Q] > Best) { Best = GroupSizes[Q]; BestKey = GroupKeys[Q]; }
		}
		int TiedGroups = 0;
		for (size_t Q = 0; Q < GroupKeys.size(); ++Q)
		{
			if (GroupSizes[Q] == Best && GroupKeys[Q] != BestKey) { ++TiedGroups; }
		}
		const int DistinctGroups = (int)GroupKeys.size();
		std::vector<FrameSample> G;
		for (size_t I = 0; I < All.size(); ++I)
		{
			if (All[I].bMeasured && SampleKey(All[I], true) == BestKey) { G.push_back(All[I]); }
		}
		std::string Out;
		char Buf[960];
		std::snprintf(Buf, sizeof(Buf),
			"nullSeriesStatus=%s nullSeriesSamples=%d/of=%d/measured-frames-sharing-the-"
			"largest-identical-applied-input-group-at-one-camera"
			" nullSeriesMeasured=%d/of=%d/shots-offered"
			" nullSeriesTiedGroups=%d/of=%d/distinct-groups-examined/groups-not-frames/"
			"rival-groups-whose-size-equals-the-largest-excluding-the-one-kept"
			" nullSeriesApplied=%s"
			" nullSeriesExcludes=wetness/because-VignetteShot.cpp-has-no-read-site-for-it-"
			"on-this-commit/the-other-engine-applies-it-at-StreetVignetteHost.cs-line-715",
			G.size() >= 2 ? "READ" : "TOO-FEW-SAMPLES",
			(int)G.size(), Measured, Measured, (int)All.size(),
			TiedGroups, DistinctGroups,
			BestKey.empty() ? "none" : BestKey.c_str());
		Out += Buf;
		// THE IDS, IN SHOT ORDER, AND THE CAP ANNOUNCES ITSELF.
		const size_t kIdCap = 12;
		std::string Ids;
		for (size_t I = 0; I < G.size() && I < kIdCap; ++I)
		{
			if (!Ids.empty()) { Ids += ";"; }
			Ids += NoSpaces(G[I].ShotId);
		}
		if (G.size() > kIdCap)
		{
			char More[64];
			std::snprintf(More, sizeof(More), "/+%d-more-not-shown", (int)(G.size() - kIdCap));
			Ids += More;
		}
		Out += " nullSeriesIds=" + (Ids.empty() ? std::string("none") : Ids);
		if (G.size() < 2)
		{
			Out += " nullSeriesVerdict=nothing-measured/one-frame-cannot-hold-a-spread";
			Out += " nullSeriesStat=whole-run/spread-is-max-minus-min-over-the-group";
			return Out;
		}
		// THE SPREAD, THE DRIFT AND THE SMALLEST SKY STEP, PER STATISTIC.
		// THE SPREAD is max minus min over the group, stated as such, with the
		// two frames it came from named. THE DRIFT is last minus first IN SHOT
		// ORDER, which is the one-pair difference the 19:46Z record asked for,
		// and the two together say whether the drift is monotone in shot order:
		// a spread whose extremes ARE the first and last frame reads as drift,
		// and one whose extremes sit in the middle reads as a step or as noise.
		// THE SKY STEP is the SMALLEST absolute difference between any two
		// measured frames whose conditions differ in sky intensity ALONE, which
		// is the weakest signal the grid is allowed to claim. No shot is named
		// to find it.
		int Clear = 0, Judged = 0;
		for (int W = 0; W < 3; ++W)
		{
			double Lo = SampleStat(G[0], W), Hi = Lo;
			size_t LoAt = 0, HiAt = 0;
			bool bUp = true, bDown = true;
			for (size_t I = 0; I < G.size(); ++I)
			{
				const double V = SampleStat(G[I], W);
				if (V < Lo) { Lo = V; LoAt = I; }
				if (V > Hi) { Hi = V; HiAt = I; }
				if (I > 0)
				{
					const double P = SampleStat(G[I - 1], W);
					if (V < P) { bUp = false; }
					if (V > P) { bDown = false; }
				}
			}
			const double Spread = Hi - Lo;
			const double Drift  = SampleStat(G[G.size() - 1], W) - SampleStat(G[0], W);
			// THE SMALLEST SKY STEP, AND ITS OWN DENOMINATOR: how many
			// sky-only pairs were found at all. Zero pairs is not a clean
			// result, it is nothing measured.
			double Step = 0.0;
			int Pairs = 0;
			std::string StepA, StepB;
			for (size_t I = 0; I < All.size(); ++I)
			{
				if (!All[I].bMeasured) { continue; }
				for (size_t J = I + 1; J < All.size(); ++J)
				{
					if (!All[J].bMeasured) { continue; }
					if (SampleKey(All[I], false) != SampleKey(All[J], false)) { continue; }
					if (All[I].SkyIntensity == All[J].SkyIntensity) { continue; }
					const double D = std::fabs(SampleStat(All[I], W) - SampleStat(All[J], W));
					if (Pairs == 0 || D < Step)
					{
						Step = D; StepA = All[I].ShotId; StepB = All[J].ShotId;
					}
					++Pairs;
				}
			}
			char Line[760];
			std::snprintf(Line, sizeof(Line),
				" nullSpread%s=%.4f/max=%s/%.4f/min=%s/%.4f"
				" nullDrift%s=%+.4f/first=%s/last=%s"
				" nullOrder%s=%s",
				SampleStatName(W), Spread, NoSpaces(G[HiAt].ShotId).c_str(), Hi,
				NoSpaces(G[LoAt].ShotId).c_str(), Lo,
				SampleStatName(W), Drift, NoSpaces(G[0].ShotId).c_str(),
				NoSpaces(G[G.size() - 1].ShotId).c_str(),
				SampleStatName(W),
				bUp && bDown ? "flat" : (bUp ? "nondecreasing-in-shot-order"
				                             : (bDown ? "nonincreasing-in-shot-order"
				                                      : "neither/a-step-or-noise")));
			Out += Line;
			char StepS[520];
			if (Pairs == 0)
			{
				std::snprintf(StepS, sizeof(StepS),
					" skyStepSmallest%s=nothing-measured/no-pair-of-measured-frames-differs-"
					"in-sky-alone skyStepPairs%s=0/of=0/sky-only-pairs"
					" nullFloor%s=nothing-measured/no-sky-step-to-read-the-spread-against",
					SampleStatName(W), SampleStatName(W), SampleStatName(W));
				Out += StepS;
				continue;
			}
			++Judged;
			const bool bClear = (Spread < Step);
			if (bClear) { ++Clear; }
			std::snprintf(StepS, sizeof(StepS),
				" skyStepSmallest%s=%.4f/between=%s..%s skyStepPairs%s=%d/of=%d/sky-only-pairs"
				" nullFloor%s=%s/spread%.4f/vs/step%.4f",
				SampleStatName(W), Step, NoSpaces(StepA).c_str(), NoSpaces(StepB).c_str(),
				SampleStatName(W), Pairs, Pairs,
				SampleStatName(W), bClear ? "CLEAR" : "NOT-SMALLER", Spread, Step);
			Out += StepS;
		}
		char Done[520];
		std::snprintf(Done, sizeof(Done),
			" nullSeriesVerdict=%s nullSeriesClear=%d/of=%d/statistics-with-a-sky-step-to-"
			"read-against nullSeriesStat=whole-run/spread-is-max-minus-min-over-the-group/"
			"drift-is-last-minus-first-in-shot-order/sky-step-is-the-SMALLEST-difference-"
			"between-two-frames-differing-in-sky-alone/a-spread-not-smaller-than-that-step-"
			"makes-the-grid-a-NO-READ",
			Judged == 0 ? "nothing-measured"
			            : (Clear == Judged ? "CLEAR" : "NO-READ/no-cell-may-be-quoted"),
			Clear, Judged);
		Out += Done;
		return Out;
	}

	// ========================================================================
	// QUEUE 235: THE EXPOSURE PIN, ASKED BESIDE READ, AND THE LADDER THAT
	// SETS ITS VALUE LATER.
	//
	// WHAT THE FAULT WAS. On 83dec33 one camera under one condition,
	// photographed first and again last, differed by 0.3460 of whole-frame
	// mean luma on 921600 of 921600 pixels, so every cross-frame number that
	// run printed is void. Snapping the adaptation RATE to 10000 did not fix
	// it. The next lever is the VALUE: AutoExposureMinBrightness equal to
	// AutoExposureMaxBrightness leaves the histogram nothing to move.
	//
	// WHY THE VALUE IS NOT IN THIS FILE. It cannot be computed from anything
	// committed. shotMeanLuma is the mean of a tonemapped 8-bit frame and the
	// pin is a scene-luminance input read before the tonemap; no arithmetic
	// joins them, and the adapted exposure is a render-thread quantity this
	// process never reads. So the value is read off a LADDER: rows that
	// differ in nothing but the pin, each printing what its frame came out
	// at, and the number is set in a LATER commit from the printed series.
	// Ship the printer, read the runs, set the bound, in that order.
	//
	// AND THE COST, WHICH IS PAID THE MOMENT A PIN IS IN FORCE: a pinned
	// frame cannot judge an adaptation moment. Walking out of a dark alley
	// and having the street bloom open is exactly the thing this rig stops
	// being able to photograph. That cost was accepted in writing when the
	// rate was snapped and it is restated beside the constant in
	// VignetteShot.cpp, which is where the value lives.
	// ========================================================================

	// A PIN IS ASKED FOR ONLY BY A POSITIVE NUMBER. Zero or less is the
	// condition saying "leave the engine's own policy alone", which is what
	// every condition written before 2026-09-10 says.
	inline bool ExposurePinAsked(double Pin) { return Pin > 0.0; }

	// THE SEPARATOR BETWEEN A FLOAT ROUND TRIP AND A PIN THAT NEVER LANDED,
	// RELATIVE, AND IT IS NOT A MEASURED TOLERANCE. The asked value is a
	// double handed to a float field, so a read back of 0.30000001 is the
	// same number; a pin that did not take reads back as the engine default
	// (0.0300 and 8.0000 on 83dec33), which is wrong by a factor, not by a
	// rounding. One part in a thousand sits between those two classes with
	// four orders of magnitude to spare on each side. A residual printed
	// between 1e-6 and 1e-3 is what a real bound would later be read off.
	inline double ExposurePinRefuseAtRel() { return 0.0010; }

	// WHAT THE COMPONENT SAID AFTER THE WRITE, WHICH IS THE ONLY THING WORTH
	// PRINTING. A value that lands on the game thread and never reaches the
	// render proxy reads back as the same pointer it was written through, so
	// this is necessary and not sufficient, and the word says which: HELD
	// means the game thread agrees, not that a pixel obeyed. The frame's own
	// luma is the other half and it rides the same shot line.
	struct ExposurePinIn
	{
		double Asked;                // the condition's exposure_pin
		double ReadMin, ReadMax;     // AutoExposureMin/MaxBrightness, read back
		bool   bOverMin, bOverMax;   // the override flags beside the values
		bool   bRead;                // a camera component answered at all
		bool   bSunOn;               // which lighting family this row stands in
		ExposurePinIn() : Asked(0), ReadMin(0), ReadMax(0),
		                  bOverMin(false), bOverMax(false), bRead(false), bSunOn(false) {}
	};

	inline double ExposurePinResidual(double Asked, double Read)
	{
		return NoNegZero(Read - Asked);
	}

	inline bool ExposurePinHeld(const ExposurePinIn& In)
	{
		if (!In.bRead || !ExposurePinAsked(In.Asked)) { return false; }
		if (!In.bOverMin || !In.bOverMax) { return false; }
		const double Allow = ExposurePinRefuseAtRel() * In.Asked;
		double DMin = In.ReadMin - In.Asked; if (DMin < 0) { DMin = -DMin; }
		double DMax = In.ReadMax - In.Asked; if (DMax < 0) { DMax = -DMax; }
		return DMin <= Allow && DMax <= Allow;
	}

	inline const char* ExposurePinWord(const ExposurePinIn& In)
	{
		if (!In.bRead)                      { return "NOT-READ"; }
		if (!ExposurePinAsked(In.Asked))    { return "AUTO"; }
		return ExposurePinHeld(In) ? "PINNED-HELD" : "PINNED-DIFFERS";
	}

	// PER-SAMPLE KEYS ONLY. The pin is written at every camera placement, so
	// it is a fact about THIS frame and not about the run; the run-wide
	// tonemap line is one-per-run and last-wins and cannot answer for a shot
	// that is not the last one placed.
	inline std::string ExposurePinSegment(const ExposurePinIn& In)
	{
		// ONE KEY SET ON EVERY SHOT LINE, WHATEVER THE ANSWER IS, and that is
		// the dupkeys rule written into a formatter rather than checked after
		// it. A key is AMBIGUOUS when it takes different values under two
		// different line SHAPES, so a segment that printed six keys on an
		// unpinned row and eight on a pinned one would make every one of them
		// ambiguous across a file that holds both. The VALUES say which case
		// this is; the key names never move.
		const char* Word = ExposurePinWord(In);
		char Read[64], Resid[64], Over[64];
		if (!In.bRead)
		{
			std::snprintf(Read,  sizeof(Read),  "nothing-measured/nothing-measured");
			std::snprintf(Resid, sizeof(Resid), "nothing-measured/nothing-measured");
			std::snprintf(Over,  sizeof(Over),  "nothing-measured/nothing-measured");
		}
		else
		{
			// THE TWO NUMBERS READ BACK ARE WORTH HAVING ON AN UNPINNED ROW
			// TOO: they are the engine's own clamp range, which is the bracket
			// the ladder's rungs are chosen inside.
			std::snprintf(Read, sizeof(Read), "%.4f/%.4f", In.ReadMin, In.ReadMax);
			std::snprintf(Over, sizeof(Over), "%d/%d",
			              In.bOverMin ? 1 : 0, In.bOverMax ? 1 : 0);
			if (ExposurePinAsked(In.Asked))
			{
				std::snprintf(Resid, sizeof(Resid), "%+.6f/%+.6f",
				              ExposurePinResidual(In.Asked, In.ReadMin),
				              ExposurePinResidual(In.Asked, In.ReadMax));
			}
			else
			{
				// A RESIDUAL AGAINST A PIN NOBODY ASKED FOR IS NOT A ZERO.
				std::snprintf(Resid, sizeof(Resid), "not-applicable/no-pin-asked");
			}
		}
		char Buf[760];
		std::snprintf(Buf, sizeof(Buf),
			"shotExposurePin=%s shotExposurePinAsked=%.4f "
			"shotExposurePinRead=%s shotExposurePinResidual=%s "
			"shotExposurePinOverrides=%s shotExposurePinFamily=%s "
			"shotExposurePinRefuseAtRel=%.4f/NOT-A-MEASURED-TOLERANCE/a-class-separator-"
			"between-a-float-round-trip-and-a-pin-that-read-back-as-the-engine-default "
			"shotExposurePinStat=per-sample/min-then-max-read-off-the-cameras-post-process-"
			"after-the-write/residual-is-read-minus-asked/a-row-asking-for-no-pin-reads-AUTO-"
			"and-its-two-numbers-are-the-engines-own-clamp-range/HELD-is-the-game-threads-"
			"agreement-and-not-a-pixels",
			Word, In.Asked, Read, Resid, Over,
			In.bSunOn ? "day" : "night", ExposurePinRefuseAtRel());
		return std::string(Buf);
	}

	// ---- THE LADDER, AND WHY EVERY RUNG IS PHOTOGRAPHED TWICE -------------
	//
	// THE PAIRING IS THE MEASUREMENT. The whole fault is that a frame
	// following darkness came out blown, so a rung photographed only after a
	// day frame cannot answer whether its pin removed the dependence on what
	// came before. Each pin value therefore gets two rows, identical in every
	// applied input, differing only in what the rig photographed IMMEDIATELY
	// BEFORE them: one after a night frame, one after a day frame. The
	// predecessor is READ off the shot actually photographed before this one,
	// never off the row's name.
	//
	// WHAT THIS LINE DOES NOT DO: call a winner. The difference between the
	// two halves of a rung is printed, and the SMALLEST is named, and that is
	// as far as a first series may go. Calling a rung "agreed" needs a bound
	// and this run has not measured one, so the verdict word stays
	// SERIES-ONLY and the number is set in a later commit.
	struct ExposureLadderSample
	{
		std::string ShotId;
		double      Pin;
		bool        bAfterNight;  // the frame before this one was a night frame
		bool        bMeasured;    // a frame landed and was measured
		bool        bPinHeld;     // the readback agreed with the asked pin
		double      MeanLuma;
		long long   ClipHi, ClipLo, Pixels;
		ExposureLadderSample() : Pin(0), bAfterNight(false), bMeasured(false),
		                         bPinHeld(false), MeanLuma(0),
		                         ClipHi(0), ClipLo(0), Pixels(0) {}
	};

	inline std::string ExposureLadderLine(const std::vector<ExposureLadderSample>& All)
	{
		const int Offered = (int)All.size();
		int Measured = 0;
		for (size_t I = 0; I < All.size(); ++I) { if (All[I].bMeasured) { ++Measured; } }
		if (Offered == 0)
		{
			return std::string(
				"ladderStatus=NOTHING-MEASURED ladderRows=0/of=0/ladder-rows-offered "
				"ladderPinsPaired=0/of=0/pin-values-with-both-halves-measured "
				"ladderSmallestDiffPin=nothing-measured ladderSmallestDiff=nothing-measured "
				"ladderVerdict=nothing-measured/no-ladder-row-was-photographed "
				"ladderStat=whole-run/one-segment-per-pin-value/a-difference-never-a-ratio");
		}
		// THE DISTINCT PIN VALUES, IN THE ORDER THE FILE ASKED FOR THEM, so
		// the series reads as a ladder rather than as a sorted summary.
		std::vector<double> Pins;
		for (size_t I = 0; I < All.size(); ++I)
		{
			bool bSeen = false;
			for (size_t J = 0; J < Pins.size(); ++J)
			{
				if (Pins[J] == All[I].Pin) { bSeen = true; }
			}
			if (!bSeen) { Pins.push_back(All[I].Pin); }
		}
		std::string Out;
		int Paired = 0, HeldRows = 0;
		bool   bBest = false;
		double BestDiff = 0.0, BestPin = 0.0;
		for (size_t P = 0; P < Pins.size(); ++P)
		{
			int Rows = 0, RowsMeasured = 0, Held = 0;
			bool bDay = false, bNight = false;
			ExposureLadderSample Day, Night;
			for (size_t I = 0; I < All.size(); ++I)
			{
				if (All[I].Pin != Pins[P]) { continue; }
				++Rows;
				if (All[I].bPinHeld) { ++Held; ++HeldRows; }
				if (!All[I].bMeasured) { continue; }
				++RowsMeasured;
				// LAST WINS AND IT IS SAID ON THE LINE. A file asking for the
				// same half twice is a file fault, not a second reading, and
				// the rows count beside it is what makes it visible.
				if (All[I].bAfterNight) { Night = All[I]; bNight = true; }
				else                    { Day = All[I];   bDay = true; }
			}
			char Seg[760];
			if (bDay && bNight)
			{
				++Paired;
				const double Diff = NoNegZero(Day.MeanLuma - Night.MeanLuma);
				double Abs = Diff; if (Abs < 0) { Abs = -Abs; }
				if (!bBest || Abs < BestDiff) { bBest = true; BestDiff = Abs; BestPin = Pins[P]; }
				std::snprintf(Seg, sizeof(Seg),
					" ladder.pin%.4f.rows=%d/of=%d/rows-this-pin-measured-over-rows-asked"
					" ladder.pin%.4f.afterDayMeanLuma=%.4f"
					" ladder.pin%.4f.afterNightMeanLuma=%.4f"
					" ladder.pin%.4f.afterDayMinusAfterNightMeanLuma=%+.4f"
					" ladder.pin%.4f.afterDayClipHi=%lld/%lld"
					" ladder.pin%.4f.afterNightClipHi=%lld/%lld"
					" ladder.pin%.4f.afterDayClipLo=%lld/%lld"
					" ladder.pin%.4f.afterNightClipLo=%lld/%lld"
					" ladder.pin%.4f.pinHeld=%d/of=%d/rows-whose-readback-matched-the-asked-pin"
					" ladder.pin%.4f.ids=%s;%s",
					Pins[P], RowsMeasured, Rows,
					Pins[P], Day.MeanLuma,
					Pins[P], Night.MeanLuma,
					Pins[P], Diff,
					Pins[P], Day.ClipHi, Day.Pixels,
					Pins[P], Night.ClipHi, Night.Pixels,
					Pins[P], Day.ClipLo, Day.Pixels,
					Pins[P], Night.ClipLo, Night.Pixels,
					Pins[P], Held, Rows,
					Pins[P], NoSpaces(Day.ShotId).c_str(), NoSpaces(Night.ShotId).c_str());
			}
			else
			{
				// A RUNG WITH ONE HALF IS NOT A RUNG. It prints which half is
				// missing rather than a difference against a zero.
				std::snprintf(Seg, sizeof(Seg),
					" ladder.pin%.4f.rows=%d/of=%d/rows-this-pin-measured-over-rows-asked"
					" ladder.pin%.4f.afterDayMeanLuma=%s"
					" ladder.pin%.4f.afterNightMeanLuma=%s"
					" ladder.pin%.4f.afterDayMinusAfterNightMeanLuma=nothing-measured"
					" ladder.pin%.4f.pinHeld=%d/of=%d/rows-whose-readback-matched-the-asked-pin"
					" ladder.pin%.4f.missing=%s",
					Pins[P], RowsMeasured, Rows,
					Pins[P], bDay ? "measured" : "nothing-measured",
					Pins[P], bNight ? "measured" : "nothing-measured",
					Pins[P], Pins[P], Held, Rows,
					Pins[P], bDay ? "the-after-night-half" : "the-after-day-half");
			}
			Out += Seg;
		}
		char Head[560];
		std::snprintf(Head, sizeof(Head),
			"ladderStatus=%s ladderRows=%d/of=%d/ladder-rows-offered "
			"ladderPinsPaired=%d/of=%d/pin-values-with-both-halves-measured "
			"ladderRowsHeld=%d/of=%d/ladder-rows-whose-pin-readback-matched",
			Measured == 0 ? "NOTHING-MEASURED"
			              : (Measured == Offered ? "ALL" : "PARTIAL"),
			Measured, Offered, Paired, (int)Pins.size(), HeldRows, Offered);
		std::string Line(Head);
		Line += Out;
		char Tail[700];
		if (bBest)
		{
			std::snprintf(Tail, sizeof(Tail),
				" ladderSmallestDiffPin=%.4f ladderSmallestDiff=%.4f"
				" ladderVerdict=SERIES-ONLY/the-smallest-difference-is-NAMED-and-NOTHING-is-"
				"called-agreement-on-this-run/a-bound-on-this-difference-has-not-been-measured"
				" ladderStat=whole-run/one-segment-per-pin-value/afterDay-and-afterNight-name-"
				"the-frame-photographed-IMMEDIATELY-BEFORE-each-row-read-off-the-shot-loop-and-"
				"not-off-the-rows-name/the-rows-themselves-share-every-applied-input-except-the-"
				"pin/a-DIFFERENCE-never-a-ratio",
				BestPin, BestDiff);
		}
		else
		{
			std::snprintf(Tail, sizeof(Tail),
				" ladderSmallestDiffPin=nothing-measured ladderSmallestDiff=nothing-measured"
				" ladderVerdict=SERIES-ONLY/no-pin-value-has-both-halves-so-no-difference-exists-"
				"to-be-smallest"
				" ladderStat=whole-run/one-segment-per-pin-value/afterDay-and-afterNight-name-"
				"the-frame-photographed-IMMEDIATELY-BEFORE-each-row-read-off-the-shot-loop-and-"
				"not-off-the-rows-name/a-DIFFERENCE-never-a-ratio");
		}
		Line += Tail;
		return Line;
	}

	// THE WHOLE-RUN PIN LINE. Only numbers that are true of the RUN, and the
	// cost of the pin restated where a reader of the verdict will meet it.
	inline std::string ExposurePinDoneLine(int Pinned, int Held, int Read, int Offered)
	{
		char Buf[820];
		std::snprintf(Buf, sizeof(Buf),
			"expPinStatus=%s expPinRowsAsking=%d/of=%d/shots-offered "
			"expPinRowsRead=%d/of=%d/shots-offered "
			"expPinRowsHeld=%d/of=%d/shots-asking-for-a-pin "
			"expPinConstantSet=no/this-run-prints-the-ladder-series-only/the-value-is-set-in-a-"
			"later-commit-from-what-it-printed "
			"expPinCost=a-pinned-frame-can-never-judge-an-adaptation-moment/walking-out-of-a-"
			"dark-alley-is-the-example "
			"expPinStat=whole-run/asking-is-a-condition-with-a-positive-exposure_pin/held-is-the-"
			"readback-agreeing-at-the-placement-that-photographed-the-frame",
			Offered == 0 ? "NOTHING-MEASURED"
			             : (Pinned == 0 ? "NONE-ASKED"
			                            : (Held == Pinned ? "ALL-HELD" : "PARTIAL")),
			Pinned, Offered, Read, Offered, Held, Pinned);
		return std::string(Buf);
	}

	// THE DONE LINE FOR THE WHOLE CAPTURE. Whole-run numbers only, and a run
	// that photographed nothing says the words rather than printing zeros
	// that read like a clean result.
	inline std::string CaptureDoneLine(int Wrote, int Asked, int Blank, int NoFile,
	                                   double SecondsTotal, int Ticks)
	{
		char Buf[420];
		std::snprintf(Buf, sizeof(Buf),
			"captureStatus=%s shotsWrote=%d/%d shotsBlank=%d/%d shotsNoFile=%d/%d "
			"captureSeconds=%.2f captureTicks=%d",
			Asked == 0 ? "NOTHING-MEASURED" : (Wrote == Asked ? "ALL" : (Wrote == 0 ? "NONE" : "PARTIAL")),
			Wrote, Asked, Blank, Asked, NoFile, Asked, SecondsTotal, Ticks);
		return std::string(Buf);
	}
}
