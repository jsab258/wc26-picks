// THE SCENE READER, COMPILED AND RUN HERE, AGAINST THE REAL COMMITTED FILE.
//
// WHY THIS EXISTS. The Unreal module cannot be compiled in the container
// that writes it, so anything put there ships UNRUN and the first thing that
// finds out whether it works is a 25-minute round trip on Jafar's PC. The
// standing rule from 25 August is therefore that measurement arithmetic and
// formatting live where the tests run, and VignetteSpec.h is written to that
// rule: it has no Unreal type in it, so this file compiles it with g++ and
// runs it before any dispatch.
//
// THE ACCEPTING FIXTURE IS THE LIVE CODEBASE, which is the rule for tools
// that check the project itself: production/specs/vignette-pieces.json as
// committed. The rejecting fixtures are synthetic, because a rejection has
// to be provoked and the repository has no broken street in it.
//
// WHAT IT CANNOT SEE, said plainly rather than left to be assumed: nothing
// here proves an actor spawns, that a light reaches a pixel, or that a
// screenshot lands. Those are the run's business. This proves that the file
// is read correctly and that every string this run will print is the string
// it was meant to print.
#include "../Source/LedgerProbe/Public/VignetteSpec.h"
#include "../Source/LedgerProbe/Public/SurfaceBind.h"

#include <clocale>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>

static int gChecks = 0;
static int gFailed = 0;

static void Check(bool Cond, const char* Name, const std::string& Detail = std::string())
{
	++gChecks;
	if (Cond)
	{
		std::printf("  ok - %s\n", Name);
		return;
	}
	++gFailed;
	std::printf("  FAILED - %s%s%s\n", Name,
	            Detail.empty() ? "" : " : ", Detail.c_str());
}

static std::string Slurp(const char* Path, bool& Ok)
{
	std::ifstream In(Path, std::ios::binary);
	if (!In) { Ok = false; return std::string(); }
	std::ostringstream SS;
	SS << In.rdbuf();
	Ok = true;
	return SS.str();
}

static bool NoSpacePastPrefix(const std::string& Line, const char* From)
{
	const size_t At = Line.find(From);
	if (At == std::string::npos) { return false; }
	std::istringstream In(Line.substr(At));
	std::string Tok;
	int Tokens = 0, Equals = 0;
	while (In >> Tok)
	{
		++Tokens;
		int E = 0;
		for (size_t I = 0; I < Tok.size(); ++I) { if (Tok[I] == '=') { ++E; } }
		if (E != 1) { return false; }
		Equals += E;
	}
	return Tokens > 0 && Tokens == Equals;
}

int main(int argc, char** argv)
{
	const char* SpecPath = (argc > 1) ? argv[1] : "production/specs/vignette-pieces.json";
	std::printf("VignetteSpec, against %s\n", SpecPath);

	bool Ok = false;
	const std::string Text = Slurp(SpecPath, Ok);
	Check(Ok && !Text.empty(),
	      "the committed piece list is on disk and not empty",
	      Ok ? "read but empty" : "could not open");
	if (!Ok || Text.empty())
	{
		std::printf("NOTHING MEASURED: no piece list at %s\n", SpecPath);
		return 1;
	}

	LedgerVignette::Spec S;
	std::string Err;
	const bool Parsed = LedgerVignette::ParseSpec(Text, S, Err);
	Check(Parsed, "the reader parses the committed piece list", Err);
	if (!Parsed) { std::printf("%d of %d check(s) failed\n", gFailed, gChecks); return 1; }

	// ---- THE ACCEPTING CASE, WITH ITS DENOMINATORS ----------------------
	std::printf("    read: pieces=%d header=%d cameras=%d conditions=%d shots=%d\n",
	            (int)S.Pieces.size(), S.HeaderPieces, (int)S.Cameras.size(),
	            (int)S.Conditions.size(), (int)S.Shots.size());
	Check((int)S.Pieces.size() == S.HeaderPieces,
	      "every piece the header claims is under it");
	Check(S.Pieces.size() > 500,
	      "the street read back is a street and not a handful of pieces");
	Check(S.Cameras.size() == 2 && S.Conditions.size() == 2 && S.Shots.size() == 4,
	      "the two cameras, the two conditions and the four matched shots came through");

	// ROLL, WHICH IS THE FIELD A READER LOSES WITHOUT CHANGING A COUNT.
	int Rolled = 0, Pitched = 0, Yawed = 0;
	for (size_t I = 0; I < S.Pieces.size(); ++I)
	{
		if (std::fabs(S.Pieces[I].RollDeg)  > 1e-9) ++Rolled;
		if (std::fabs(S.Pieces[I].PitchDeg) > 1e-9) ++Pitched;
		if (std::fabs(S.Pieces[I].YawDeg)   > 1e-9) ++Yawed;
	}
	std::printf("    rotations: rolled=%d pitched=%d yawed=%d multi=%d of %d pieces\n",
	            Rolled, Pitched, Yawed,
	            LedgerVignette::MultiRotationCount(S.Pieces), (int)S.Pieces.size());
	Check(Rolled > 0,
	      "roll survived the read, so the rolled cylinders will lie down rather than stand up",
	      "rolled=0 of the file's own nine");
	Check(LedgerVignette::MultiRotationCount(S.Pieces) == S.HeaderMultiRotation,
	      "the reader counts the same multi-rotation pieces the file's header claims",
	      "reader disagrees with counts.multi_rotation");
	// AT ZERO THE EULER COMPOSITION ORDER IS UNEXERCISED, which is the only
	// reason this engine may compose in whatever order its API prefers. The
	// day it stops being zero the emitter owes a statement of what the pair
	// meant before either engine is trusted with it.
	Check(S.HeaderMultiRotation == 0,
	      "no piece carries two rotations at once, so composition order cannot differ between engines",
	      "multi_rotation is no longer zero: the emitter's rotation order is now load-bearing");

	int Boxes = LedgerVignette::ShapeCount(S.Pieces, "box");
	int Cyls  = LedgerVignette::ShapeCount(S.Pieces, "cyl");
	int Mesh  = LedgerVignette::ShapeCount(S.Pieces, "mesh");
	int Decal = LedgerVignette::ShapeCount(S.Pieces, "decal");
	std::printf("    shapes: box=%d cyl=%d mesh=%d decal=%d unknown=%d of %d\n",
	            Boxes, Cyls, Mesh, Decal,
	            (int)S.Pieces.size() - Boxes - Cyls - Mesh - Decal, (int)S.Pieces.size());
	Check(Boxes + Cyls + Mesh + Decal == (int)S.Pieces.size(),
	      "every piece has a shape this emitter knows how to stand up",
	      "some piece carries a shape string the emitter would silently skip");

	// THE LAMP AND THE PRACTICALS, INCLUDING THE COLOUR SPACE.
	std::printf("    lantern: space=%s rgb=%.4f/%.4f/%.4f range=%.2f intensity=%.2f emissive=%d\n",
	            S.Lantern.ColourSpace.c_str(), S.Lantern.R, S.Lantern.G, S.Lantern.B,
	            S.Lantern.RangeM, S.Lantern.Intensity,
	            LedgerVignette::EmissiveCount(S.Pieces));
	Check(S.Lantern.ColourSpace == "gamma-sRGB",
	      "the lamp colour names the space it is in, so the conversion has something to be checked against",
	      S.Lantern.ColourSpace);
	Check(LedgerVignette::EmissiveCount(S.Pieces) > 0,
	      "there are emissive pieces to hang the lanterns on");
	std::printf("    practicals: space=%s lit=%d/%d flatLit=%d/%d shopIntensity=%.2f\n",
	            S.Windows.ColourSpace.c_str(), (int)S.Windows.LitNames.size(),
	            S.Windows.ShopCards, (int)S.Windows.FlatLitNames.size(),
	            S.Windows.FlatCards, S.Windows.ShopIntensity);
	Check((int)S.Windows.LitNames.size() == 3 && S.Windows.ShopCards == 6,
	      "the file lights three of the six shop interiors and this reader sees the names",
	      "the practicals block did not read back as three of six");
	Check(S.Windows.FlatLitNames.empty() && S.Windows.FlatCards == 0,
	      "the flat practicals light nothing today and the reader carries the empty list rather than a default");
	// EVERY NAME THE FILE ASKS TO BE LIT MUST NAME A PIECE. A name that
	// matched nothing would light nothing and the count would be right by
	// accident, which is the failure the Unity host had before queue 040.
	int Matched = 0;
	for (size_t I = 0; I < S.Windows.LitNames.size(); ++I)
		for (size_t J = 0; J < S.Pieces.size(); ++J)
			if (S.Pieces[J].Name == S.Windows.LitNames[I]) { ++Matched; break; }
	Check(Matched == (int)S.Windows.LitNames.size(),
	      "every name in lit_names is a piece in this file, so no practical can be asked for and never placed",
	      "matched fewer names than the file lists");

	// THE CAMERAS, AND THE GROUND UNDER THEM THAT THIS ENGINE MUST NOT
	// RE-DERIVE. Both cameras stand on a footway that falls 1 in 40, so the
	// two ground levels differ and a shared constant would be wrong for one.
	for (size_t I = 0; I < S.Cameras.size(); ++I)
	{
		const LedgerVignette::Camera& C = S.Cameras[I];
		std::printf("    camera %s: x=%.2f z=%.2f groundFound=%d groundY=%.4f on=%s eye=%.4f fovV=%.1f fovH=%.1f\n",
		            C.Id.c_str(), C.X, C.Z, (int)C.GroundFound, C.GroundY,
		            C.GroundEdge.c_str(), C.GroundY + C.EyeHeightM, C.FovVerticalDeg,
		            LedgerVignette::HorizontalFovDeg(C.FovVerticalDeg, 1280, 720));
		Check(C.GroundFound,
		      "the file found ground under this camera, so the eye height has a datum to sit on",
		      C.Id + " ground_found=false");
	}

	// THE FOV CONVERSION, WHICH IS THE TRAP. Unity's fieldOfView is
	// vertical; Unreal's is horizontal. At 16:9 a vertical 60 is a
	// horizontal 91.5, and handing 60 to Unreal would photograph a
	// different street from a third of the width.
	const double HFov = LedgerVignette::HorizontalFovDeg(60.0, 1280, 720);
	std::printf("    fov: vertical=60.0 horizontal=%.2f at 1280x720\n", HFov);
	Check(HFov > 91.0 && HFov < 92.0,
	      "a vertical 60 at 16:9 converts to a horizontal 91.5, not to 60",
	      "conversion produced something else");
	Check(std::fabs(LedgerVignette::HorizontalFovDeg(60.0, 100, 100) - 60.0) < 1e-9,
	      "and at 1:1 the two are the same number, which is the case that would hide a broken conversion");

	// THE SUN. The two engines derive the same direction two ways and the
	// pair of yaws differs by exactly 90 degrees under this frame's own
	// conventions; asserting the relationship is what makes the pair a
	// check rather than two independent guesses.
	const double UeYaw = LedgerVignette::SunYawDeg(S.SunAzimuthDeg);
	const double UnityYaw = LedgerVignette::UnitySunYawDeg(S.SunAzimuthDeg);
	std::printf("    sun: elevation=%.1f azimuth=%.1f ueYaw=%.1f unityYaw=%.1f\n",
	            S.SunElevationDeg, S.SunAzimuthDeg, UeYaw, UnityYaw);
	Check(std::fabs(S.SunElevationDeg - 36.0) < 1e-9,
	      "the sun elevation is the file's, not a default");
	// THE TWO ENGINES' YAWS ARE ONE DIRECTION SAID TWICE, and the identity
	// between them is what makes the pair a check. A facing at bearing b is
	// Unity yaw 90-b and this engine's yaw b, so the two must differ by
	// exactly that. Without this, both conversions could be wrong in the
	// same way and every frame would agree with every other frame.
	Check(std::fabs(LedgerVignette::Wrap360(90.0 - UnityYaw) - UeYaw) < 1e-9,
	      "the two engines' sun yaws are the same bearing expressed twice, not two guesses",
	      "ue and unity yaws do not satisfy ueYaw = 90 - unityYaw");
	Check(std::fabs(LedgerVignette::SunPitchDeg(S.SunElevationDeg) + S.SunElevationDeg) < 1e-9,
	      "a sun above the horizon sends its light below it");

	// THE COLOUR CONVERSION, ON BOTH ENDS AND IN THE MIDDLE.
	Check(std::fabs(LedgerVignette::SrgbToLinear(0.0) - 0.0) < 1e-12
	      && std::fabs(LedgerVignette::SrgbToLinear(1.0) - 1.0) < 1e-12,
	      "gamma to linear fixes both ends exactly");
	Check(std::fabs(LedgerVignette::SrgbToLinear(0.8573) - 0.7055) < 5e-4,
	      "and the lantern's own gamma green converts to the linear green the scene file states beside it",
	      "the scene file says linear_srgb 0.7055 for gamma 0.8573");
	Check(LedgerVignette::SrgbToLinear(0.5) < 0.5,
	      "a mid grey darkens, which is the direction that catches the conversion being applied backwards");

	// THE MEDIAN, INCLUDING THE CASE THAT MUST NOT READ AS A FAST FRAME.
	std::vector<double> Ms;
	Check(LedgerVignette::MedianMs(Ms) < 0.0,
	      "a timing that never ran reports a negative rather than a zero millisecond frame");
	Ms.push_back(10.0); Ms.push_back(1.0); Ms.push_back(100.0);
	Check(std::fabs(LedgerVignette::MedianMs(Ms) - 10.0) < 1e-9,
	      "an odd series takes the middle value and is not dragged by the outlier",
	      "a mean would read 37");
	Ms.push_back(11.0);
	Check(std::fabs(LedgerVignette::MedianMs(Ms) - 10.5) < 1e-9,
	      "an even series averages the middle pair");

	// THE STRINGS, CHECKED FOR THE FAULT THAT TRUNCATES EVERY READER.
	const std::string Line = LedgerVignette::ShotLine(
		"vign_camA_day", "cam_A", "overcast_day", 1.5723, "east_footway",
		12.34, 24, 8, 1280, 720, 60.0, 91.49, 240000, "WROTE",
		"ue-vign_camA_day.png", "none");
	std::printf("    %s\n", Line.c_str());
	Check(Line.find("frameMedianMs=12.34/of=24warm8") != std::string::npos,
	      "the shot line says the frame time is a median and of how many frames", Line);
	Check(Line.find(": ") == std::string::npos,
	      "the shot line carries no colon-space that would read as prose");
	size_t Sp = Line.find("shot ");
	Check(Sp != std::string::npos, "the shot line is prefixed so a reader can find it");
	// NO VALUE MAY CONTAIN A SPACE. Split on whitespace and every token
	// carrying an '=' must have a non-empty right hand side.
	{
		std::istringstream Toks(Line);
		std::string T;
		int Pairs = 0, Bad = 0;
		while (Toks >> T)
		{
			const size_t Eq = T.find('=');
			if (Eq == std::string::npos) continue;
			++Pairs;
			if (Eq + 1 >= T.size()) ++Bad;
		}
		std::printf("    shot line: keyValuePairs=%d emptyValues=%d/%d\n", Pairs, Bad, Pairs);
		Check(Pairs >= 10 && Bad == 0,
		      "every key on the shot line carries a value with no space in it");
	}
	const std::string Scene = LedgerVignette::SceneLine(S, S.HeaderPieces, 404, 146, 20,
	                                                    23, 20, 4, 3, 0, "none");
	std::printf("    %s\n", Scene.c_str());
	Check(Scene.find("sceneStatus=WHOLE") != std::string::npos,
	      "a scene that stood up everything the file asked for says WHOLE", Scene);
	Check(Scene.find("flatsLit=0/0 nothing-to-light") != std::string::npos,
	      "and the flat practicals say the words rather than printing a bare zero", Scene);
	const std::string ScenePartial = LedgerVignette::SceneLine(S, 0, 0, 0, 0, 0, 0, 0, 0,
	                                                           S.HeaderPieces, "spawn-refused");
	Check(ScenePartial.find("sceneStatus=NOTHING-EMITTED") != std::string::npos,
	      "a scene that stood up nothing says so rather than reporting a whole street of zeros",
	      ScenePartial);
	const std::string Done = LedgerVignette::CaptureDoneLine(0, 0, 0, 0, 0.0, 0);
	Check(Done.find("captureStatus=NOTHING-MEASURED") != std::string::npos,
	      "a capture that photographed nothing says the words", Done);
	const std::string DonePart = LedgerVignette::CaptureDoneLine(2, 4, 1, 1, 31.5, 900);
	std::printf("    %s\n", DonePart.c_str());
	Check(DonePart.find("shotsWrote=2/4") != std::string::npos
	      && DonePart.find("captureStatus=PARTIAL") != std::string::npos,
	      "and a partial capture carries every count over its denominator", DonePart);

	// ---- THE REJECTING FIXTURES, WHICH HAVE TO BE PLANTED --------------
	//
	// A GUARD MUST BE TESTED ON THE CASE IT SHOULD PASS FIRST, which is
	// everything above, AND on the case it should refuse, which is here. A
	// reader that accepted a wrong-schema file, a truncated file or a file
	// with a field missing would build a street nobody asked for and every
	// count would agree with it.
	{
		LedgerVignette::Spec Bad;
		std::string BadErr;
		std::string Wrong(Text);
		const size_t At = Wrong.find("ledger.vignette-pieces/1");
		Wrong.replace(At, 24, "ledger.vignette-pieces/9");
		Check(!LedgerVignette::ParseSpec(Wrong, Bad, BadErr),
		      "a piece list from a future schema is refused rather than half-read", BadErr);
		Check(BadErr.find("schema") != std::string::npos,
		      "and the refusal names the schema as the reason", BadErr);
	}
	{
		LedgerVignette::Spec Bad;
		std::string BadErr;
		Check(!LedgerVignette::ParseSpec(Text.substr(0, Text.size() / 2), Bad, BadErr),
		      "a truncated piece list is refused rather than read as a shorter street", BadErr);
	}
	{
		LedgerVignette::Spec Bad;
		std::string BadErr;
		std::string NoRoll(Text);
		// THE LAST OCCURRENCE, WHICH IS A PIECE. The first is in the frame
		// header, where roll_deg is a prose description of the convention;
		// renaming that one changes nothing and the fixture would have
		// planted no fault at all while reporting a pass.
		std::string NoRollKey = NoRoll;
		const size_t At = NoRoll.rfind("\"roll_deg\"");
		NoRoll.replace(At, 10, "\"rollXdeg\"");
		Check(!LedgerVignette::ParseSpec(NoRoll, Bad, BadErr),
		      "a piece with roll_deg missing is refused rather than defaulted to upright", BadErr);
		Check(BadErr.find("roll_deg") != std::string::npos,
		      "and the refusal names the field that went missing", BadErr);
	}
	{
		LedgerVignette::Spec Bad;
		std::string BadErr;
		std::string NoGround(Text);
		const size_t At = NoGround.find("\"ground_y_m\"");
		NoGround.replace(At, 12, "\"groundXy_m\"");
		Check(!LedgerVignette::ParseSpec(NoGround, Bad, BadErr),
		      "a camera with no ground level is refused rather than stood at y=0", BadErr);
	}
	{
		LedgerVignette::Spec Bad;
		std::string BadErr;
		Check(!LedgerVignette::ParseSpec("{\"schema\":\"ledger.vignette-pieces/1\"}", Bad, BadErr),
		      "a file with a right schema and nothing else is refused", BadErr);
		Check(!LedgerVignette::ParseSpec("", Bad, BadErr),
		      "an empty file is refused rather than read as an empty street", BadErr);
		Check(!LedgerVignette::ParseSpec("[1,2,3]", Bad, BadErr),
		      "a file that is not an object is refused", BadErr);
	}
	{
		// THE HEADER AND THE ARRAY MUST AGREE. A truncated write leaves a
		// header claiming 593 above 400 lines and every other check here
		// reads one or the other.
		LedgerVignette::Spec Bad;
		std::string BadErr;
		std::string Miscount(Text);
		const size_t At = Miscount.find("\"pieces\":593");
		if (At != std::string::npos)
		{
			Miscount.replace(At, 12, "\"pieces\":591");
			Check(!LedgerVignette::ParseSpec(Miscount, Bad, BadErr),
			      "a header that claims more pieces than are under it is refused", BadErr);
		}
		else
		{
			// The count moved; say so rather than passing a check that
			// planted nothing.
			Check(false, "the miscount fixture could not be planted",
			      "no \"pieces\":593 in the committed file: update this fixture to the live count");
		}
	}
	{
		// THE C LOCALE, ASSERTED RATHER THAN ASSUMED. Under a comma-decimal
		// locale strtod reads "1.5" as 1 and every coordinate in this street
		// loses its fraction while every count stays green.
		std::setlocale(LC_NUMERIC, "C");
		LedgerVignette::Spec Loc;
		std::string LocErr;
		// THE FIXTURE HAS TO BE A COORDINATE THAT ACTUALLY CARRIES A
		// FRACTION, found rather than assumed: the first piece in this file
		// is a 42 metre road plane whose sx_m is a whole number, and
		// asserting on it would pass under a broken locale.
		double Frac = 0.0;
		int FracAt = -1;
		for (size_t I = 0; I < S.Pieces.size() && FracAt < 0; ++I)
		{
			const double V = S.Pieces[I].Y;
			if (std::fabs(V - (double)(long long)V) > 1e-6) { Frac = V; FracAt = (int)I; }
		}
		std::printf("    locale: fractionalFixture=piece%d y=%.6f of %d pieces examined\n",
		            FracAt, Frac, (int)S.Pieces.size());
		Check(FracAt >= 0,
		      "the file carries at least one fractional coordinate to test the numeric locale with",
		      "nothing measured: no piece in the file has a fractional y_m");
		Check(FracAt >= 0 && LedgerVignette::ParseSpec(Text, Loc, LocErr)
		      && std::fabs(Loc.Pieces[FracAt].Y - Frac) < 1e-12,
		      "a fractional coordinate reads back as a fraction under the C numeric locale",
		      "it came back changed, which is what a comma-decimal locale does to every coordinate");
	}

	// ---- PHASE C: WHICH SURFACE ASKS FOR WHICH FILE --------------------
	//
	// ACCEPTING CASE FIRST, AND THE ACCEPTING FIXTURE IS THE LIVE STREET.
	// The sixteen surface names are not written down here: they are counted
	// out of the committed piece list, so a surface added to the street
	// enlarges this test's denominator instead of slipping past it.
	{
		const std::vector<LedgerSurface::Ask> Asked = LedgerSurface::SurfacesAsked(S.Pieces);
		int Sum = 0;
		std::string Names;
		for (size_t I = 0; I < Asked.size(); ++I)
		{
			Sum += Asked[I].Pieces;
			if (I > 0) { Names += " "; }
			Names += Asked[I].Surface + "=" + std::to_string(Asked[I].Pieces);
		}
		std::printf("    surfaces asked by the street: %d over %d piece(s)\n      %s\n",
		            (int)Asked.size(), Sum, Names.c_str());
		Check(Sum == (int)S.Pieces.size(),
		      "every piece in the file is under exactly one surface name");
		Check(Asked.size() >= 10,
		      "the street asks for a real spread of surfaces and not one or two");
		bool bSorted = true, bNamed = true;
		for (size_t I = 0; I < Asked.size(); ++I)
		{
			if (Asked[I].Surface.empty()) { bNamed = false; }
			if (I > 0 && !(Asked[I - 1].Surface < Asked[I].Surface)) { bSorted = false; }
		}
		Check(bSorted, "the surfaces come back in one stable order, so two runs read alike");
		Check(bNamed, "no surface comes back nameless");

		// THE FILENAME RULE IS THE UNITY HOST'S, IN ITS ORDER.
		const std::vector<std::string> C = LedgerSurface::Candidates("asphalt", 0);
		Check(C.size() == 3 && C[0] == "asphalt.png" && C[1] == "asphalt.jpg"
		      && C[2] == "asphalt.jpeg",
		      "the albedo candidates are png then jpg then jpeg, as AssetLibrary tries them");
		const std::vector<std::string> N = LedgerSurface::Candidates("asphalt", 1);
		const std::vector<std::string> R = LedgerSurface::Candidates("asphalt", 2);
		Check(N[1] == "asphalt_n.jpg" && R[1] == "asphalt_r.jpg",
		      "the normal and roughness suffixes are _n and _r, as the pack names them");
	}
	// TILING, WHICH IS THE DIFFERENCE BETWEEN A ROAD AND ONE STRETCHED TILE.
	{
		LedgerVignette::Piece Road;
		Road.SX = 42.0; Road.SY = 0.3; Road.SZ = 2.745858;
		const LedgerSurface::Tiling T = LedgerSurface::TilingFor(Road, 2.0);
		std::printf("    tiling: road 42.00x0.30x2.75 at 2.00 m/tile -> %.2f x %.2f\n", T.U, T.V);
		Check(std::fabs(T.U - 21.0) < 1e-9,
		      "a 42 metre carriageway repeats 21 times along its length at 2 m a tile");
		Check(std::fabs(T.V - 2.745858 / 2.0) < 1e-9,
		      "and across its width, which is its second largest dimension and not its 0.3 thickness");
		LedgerVignette::Piece Small;
		Small.SX = 0.4; Small.SY = 0.1; Small.SZ = 0.2;
		const LedgerSurface::Tiling TS = LedgerSurface::TilingFor(Small, 2.0);
		Check(TS.U >= 1.0 && TS.V >= 1.0,
		      "a piece smaller than one tile shows one whole tile rather than a crop of one");
	}
	// THE TWO LINES, BOTH OUTCOMES WATCHED, ACCEPTING FIRST.
	{
		LedgerSurface::Bound B;
		B.Surface = "asphalt"; B.Pieces = 2; B.PiecesAssigned = 2; B.Status = "RESOLVED";
		B.MapFound[0] = true; B.MapFile[0] = "asphalt.jpg";
		B.MapW[0] = 2048; B.MapH[0] = 2048; B.MapLoadedAs[0] = "JPEG-BGRA8";
		B.MapFound[1] = true; B.MapFile[1] = "asphalt_n.jpg";
		B.MapW[1] = 2048; B.MapH[1] = 2048; B.MapLoadedAs[1] = "JPEG-BGRA8";
		B.TileU = 21.0; B.TileV = 1.37; B.Reason = "none";
		const std::string L = LedgerSurface::SurfaceLine(B);
		std::printf("    %s\n", L.c_str());
		Check(L.find("albedoLoadedAs=2048x2048/JPEG-BGRA8") != std::string::npos,
		      "a resolved surface says what the decoder returned, not what the filename claims");
		Check(L.find("roughnessFile=ABSENT") != std::string::npos
		      && L.find("roughnessTried=asphalt_r.png/asphalt_r.jpg/asphalt_r.jpeg")
		         != std::string::npos,
		      "and a map it did not find names every candidate it tried");
		Check(L.find("piecesAssigned=2/2") != std::string::npos,
		      "the assigned count ships with the piece count that is its denominator");

		LedgerSurface::Bound A;
		A.Surface = "card"; A.Pieces = 10; A.Status = "ABSENT";
		A.Reason = "no-file-in-citypack-textures/the-unity-host-generates-this-one-procedurally";
		const std::string AL = LedgerSurface::SurfaceLine(A);
		std::printf("    %s\n", AL.c_str());
		Check(AL.find("surfaceStatus=ABSENT") != std::string::npos
		      && AL.find("albedoTried=card.png/card.jpg/card.jpeg") != std::string::npos
		      && AL.find("procedurally") != std::string::npos,
		      "an absent surface is named with what was tried and why it is missing");
		// NO SPACE INSIDE ANY VALUE, on both lines, mechanically.
		Check(NoSpacePastPrefix(L, "surfaceStatus=") && NoSpacePastPrefix(AL, "surfaceStatus="),
		      "every surface value is space-free and carries exactly one equals");
	}
	{
		std::vector<LedgerSurface::Bound> All;
		LedgerSurface::Bound A;
		A.Surface = "asphalt"; A.Pieces = 2; A.PiecesAssigned = 2; A.MapFound[0] = true;
		A.MapFound[1] = true; A.MapFound[2] = true;
		LedgerSurface::Bound B;
		B.Surface = "concrete"; B.Pieces = 150; B.PiecesAssigned = 150; B.MapFound[0] = true;
		LedgerSurface::Bound C;
		C.Surface = "card"; C.Pieces = 10;
		All.push_back(A); All.push_back(B); All.push_back(C);
		const std::string D = LedgerSurface::MaterialsDoneLine(
			All, "/Game/Ledger/M_LedgerSurface", true, "C:/pack/textures", 51, 593, 4, 152, 2.0);
		std::printf("    %s\n", D.c_str());
		Check(D.find("surfacesResolved=2/3") != std::string::npos,
		      "the resolved count ships over what the street asked for");
		Check(D.find("surfacesAbsent=card") != std::string::npos,
		      "and the absent ones are NAMED on the run's own line, not only per surface");
		Check(D.find("mapsFound=4/9") != std::string::npos,
		      "the map count ships over three maps per surface asked");
		Check(D.find("piecesTextured=152/593") != std::string::npos,
		      "the textured pieces ship over every piece in the file");
		Check(D.find("materialsStatus=PARTIAL") != std::string::npos,
		      "two of three resolved is PARTIAL and says so");
		Check(NoSpacePastPrefix(D, "materialsStatus="),
		      "every value on the materials line is space-free");
		// A BASE MATERIAL THAT NEVER LOADED DOMINATES, because sixteen
		// resolved textures bound to nothing is not a partial success.
		const std::string NoBase = LedgerSurface::MaterialsDoneLine(
			All, "/Game/Ledger/M_LedgerSurface", false, "C:/pack/textures", 51, 593, 4, 0, 2.0);
		Check(NoBase.find("materialsStatus=NO-BASE-MATERIAL") != std::string::npos
		      && NoBase.find("materialBase=MISSING") != std::string::npos,
		      "a missing base material is its own status and outranks the texture count");
		// AND A PASS WITH NOTHING TO DO SAYS THE WORDS.
		const std::vector<LedgerSurface::Bound> None;
		const std::string Empty = LedgerSurface::MaterialsDoneLine(
			None, "/Game/Ledger/M_LedgerSurface", true, "", 0, 0, 0, 0, 2.0);
		Check(Empty.find("materialsStatus=NOTHING-ASKED") != std::string::npos
		      && Empty.find("texRoot=NOT-FOUND") != std::string::npos,
		      "a pass with no surfaces says nothing-asked and a root it never found says so");
	}
	// ---- THE PACK ON DISK, WHICH IS THE HALF THAT ANSWERS D1's QUESTION --
	//
	// This is the accepting fixture for the RESOLUTION rule: the same
	// filenames the Unreal run will try, tried here against the same
	// committed pack. It is skipped rather than failed where the pack is not
	// checked out, and a skip PRINTS ITS DENOMINATOR so that "nothing found"
	// and "nothing looked at" cannot read alike.
	{
		std::string Root(SpecPath);
		const size_t Cut = Root.find("production/specs/");
		if (Cut == std::string::npos) { Root.clear(); }
		else { Root = Root.substr(0, Cut) + "ledger/Assets/StreamingAssets/CityPack/textures/"; }
		const std::vector<LedgerSurface::Ask> Asked = LedgerSurface::SurfacesAsked(S.Pieces);
		int Resolved = 0, Absent = 0, Examined = 0;
		std::string AbsentNames;
		for (size_t I = 0; I < Asked.size() && !Root.empty(); ++I)
		{
			++Examined;
			bool bFound = false;
			const std::vector<std::string> C = LedgerSurface::Candidates(Asked[I].Surface, 0);
			for (size_t J = 0; J < C.size() && !bFound; ++J)
			{
				std::ifstream F((Root + C[J]).c_str(), std::ios::binary);
				if (F.good()) { bFound = true; }
			}
			if (bFound) { ++Resolved; }
			else
			{
				++Absent;
				if (!AbsentNames.empty()) { AbsentNames += "/"; }
				AbsentNames += Asked[I].Surface;
			}
		}
		if (Examined == 0)
		{
			std::printf("    pack: nothing measured, no CityPack textures directory under %s\n",
			            SpecPath);
		}
		else
		{
			std::printf("    pack: albedoResolved=%d/%d albedoAbsent=%s root=%s\n",
			            Resolved, Examined, AbsentNames.empty() ? "none" : AbsentNames.c_str(),
			            Root.c_str());
			Check(Resolved + Absent == Examined,
			      "every surface examined against the pack is either resolved or named absent");
			Check(Resolved > 0,
			      "the committed pack answers at least one surface, so the rule is exercised");
		}
	}

	std::printf("%s: %d of %d check(s) failed\n",
	            gFailed == 0 ? "PASS" : "FAIL", gFailed, gChecks);
	return gFailed == 0 ? 0 : 1;
}
