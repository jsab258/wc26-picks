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

	struct Condition
	{
		std::string Id, Hdri;
		bool   SunOn, LanternsOn, WindowsOn;
		double Wetness, FogDensity;
		Condition() : SunOn(false), LanternsOn(false), WindowsOn(false),
		              Wetness(0), FogDensity(0) {}
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
