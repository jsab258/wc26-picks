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
#include <vector>

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

// EVERY KEY NAME ON ONE LINE. Used to prove two lines cannot collide, which
// is the write-time half of the rule tools/verdict-dupkeys.py enforces at read
// time: a key that means one thing per surface and another thing per run is
// returned by whichever line a grep reaches first.
static void KeysOf(const std::string& Line, std::vector<std::string>& Out)
{
	std::istringstream In(Line);
	std::string Tok;
	while (In >> Tok)
	{
		const size_t At = Tok.find('=');
		if (At == std::string::npos || At == 0) { continue; }
		Out.push_back(Tok.substr(0, At));
	}
}

// EVERY TOKEN IS A KEY WITH A VALUE, AND NO VALUE CARRIES WHITESPACE. The
// rule that matters for this project's readers, which all split on space: a
// value may hold several equals signs (propCentreWorstMm=0.00/on=x/of=0 does,
// and so does every row-shaped value in the prop segment), but a value that
// holds a SPACE is silently truncated by every one of them.
static bool EveryTokenIsKeyValue(const std::string& Line)
{
	std::istringstream In(Line);
	std::string Tok;
	int Tokens = 0;
	while (In >> Tok)
	{
		++Tokens;
		const size_t At = Tok.find('=');
		if (At == std::string::npos || At == 0 || At + 1 >= Tok.size()) { return false; }
	}
	return Tokens > 0;
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
	// THREE CAMERAS AND FIVE SHOTS, AND THE SPLIT IS NAMED RATHER THAN
	// SUMMED: cam_A and cam_B by the two conditions are the FOUR MATCHED
	// PAIRS the engine decision is judged on, and cam_hook is a fifth shot
	// that is deliberately not part of that pairing (rung 1 of
	// production/ladder.md, one condition only). A bare 5 here would read as
	// the pairing having changed, so the four are counted separately.
	{
		int Matched = 0;
		for (size_t I = 0; I < S.Shots.size(); ++I)
		{
			if (S.Shots[I].CameraId == "cam_A" || S.Shots[I].CameraId == "cam_B")
			{
				++Matched;
			}
		}
		Check(S.Cameras.size() == 3 && S.Conditions.size() == 2
		      && S.Shots.size() == 5 && Matched == 4,
		      "three cameras, two conditions, and five shots of which the four "
		      "judged pairs are still exactly four");
	}

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

	// ---- THE MESH ROUTE'S SEGMENT, BOTH HALVES, BOTH DIRECTIONS ---------
	//
	// WHY THESE ROWS EXIST, amendments A5 and A6 of the ruling of
	// 2026-09-08, queue 161 and 162. The street side's collision reading and
	// its string were built in VignetteShot.cpp, which this container cannot
	// compile, so they shipped UNRUN and three faults rode in them for three
	// landed runs. Everything they assert now runs here with g++ before any
	// dispatch.
	//
	// ACCEPTING CASE FIRST, EVERY TIME, and the planted cases second. The
	// live committed street is the accepting fixture for the burial half; the
	// rejecting and the planted fixtures are built in this file, because a
	// repository with a prop sunk in the road on purpose is not one anybody
	// wants, and because a guard pinned to a real asset's current fault goes
	// RED THE DAY THE ASSET IS FIXED. So the live street's burial numbers are
	// PRINTED here as a series and never asserted as a verdict; the verdicts
	// are asserted on boxes this file makes and nobody can repair.
	{
		using namespace LedgerVignette;

		// A. THE CLASSIFIER. Accepting case first: an asset with a body setup
		// and one simple primitive is the case the importer was built to
		// produce and the one a capsule is stopped by.
		Check(ReadPropCollision(true, 1, false, true) == PropCollision_Yes,
		      "ACCEPTING CASE - a body setup with a simple primitive reads YES");
		Check(ReadPropCollision(true, 6, false, true) == PropCollision_Yes,
		      "and so does one with six of them");
		// THE FAULT A5 WAS RAISED FOR. A mesh collidable by a
		// complex-as-simple trace flag holds ZERO aggregate elements and
		// stops a capsule perfectly. The count said 0 and the old key called
		// that no collision.
		Check(ReadPropCollision(true, 0, true, true) == PropCollision_Yes,
		      "a body setup with ZERO primitives and complex-as-simple over real "
		      "geometry reads YES");
		Check(ReadPropCollision(true, 0, true, true) != PropCollision_No,
		      "and the same reading is NOT NO, which is what a count of primitives "
		      "called it for three runs");
		// AND THE OTHER HALF OF A5. No body setup is a question nobody
		// answered, not an answer of no.
		Check(ReadPropCollision(false, 0, false, true) == PropCollision_Unknown,
		      "no body setup reads UNKNOWN");
		Check(ReadPropCollision(false, 0, false, true) != PropCollision_No,
		      "and NOT NO, whatever the primitive count beside it says");
		Check(ReadPropCollision(false, 3, true, true) == PropCollision_Unknown,
		      "no body setup is still UNKNOWN even when the other three inputs "
		      "would each have said yes, because there is nothing for them to be "
		      "true of");
		// THE REAL NO, WHICH IS THE CASE THE WHOLE THREE-VALUED READING
		// EXISTS TO LEAVE ROOM FOR. A guard that can only say YES and
		// UNKNOWN is a ratchet.
		Check(ReadPropCollision(true, 0, false, true) == PropCollision_No,
		      "a body setup holding nothing, with no complex-as-simple flag, reads NO");
		Check(ReadPropCollision(true, 0, true, false) == PropCollision_No,
		      "and complex-as-simple over a mesh with NO EXTENT reads NO, because a "
		      "flag pointing at nothing stops nothing");
		// A REFUSED COUNT IS NOT A ZERO. The importer printed
		// propCollisionPrims=0/15 over fifteen refusals and the zero was the
		// lie, not the minus one.
		Check(ReadPropCollision(true, -1, false, true) == PropCollision_Unknown,
		      "a refused primitive count reads UNKNOWN and never NO");
		Check(std::string(PropCollisionWord(PropCollision_Yes)) == "YES"
		      && std::string(PropCollisionWord(PropCollision_No)) == "NO"
		      && std::string(PropCollisionWord(PropCollision_Unknown)) == "UNKNOWN",
		      "and the three words are the three words");

		// B. THE TALLY AND THE STRING. A run with one of each.
		PropSegmentIn In;
		In.MeshPiecesInFile = ShapeCount(S.Pieces, "mesh");
		In.PackageDir = "/Game/Ledger/Props";
		In.NamePrefix = "SM_";
		In.PlacedAsMesh = 3;
		In.PlacedAsBox = In.MeshPiecesInFile - 3;
		In.FellBackOn.push_back("prop_pallet_0=no-uasset-for-pallet");
		In.CentreWorstMm = 0.47; In.CentreWorstOn = "prop_drainage_grate_01_0";
		In.SizeWorstMm = 44.02; In.SizeWorstOn = "prop_wooden_crate_01_0";
		In.SizeComparable = 3;
		In.bInteractive = true;
		In.Collision.Add("prop_drainage_grate_01_0", PropCollision_Yes);
		In.Collision.Add("prop_pavement_sign_0", PropCollision_No);
		In.Collision.Add("prop_skip_0", PropCollision_Unknown);
		const std::string Seg3 = PropMeshSegment(In);
		std::printf("    %s\n", Seg3.c_str());
		Check(Seg3.find("propPlacedWithCollision=1/3") != std::string::npos,
		      "the placed-with-collision count ships the readings TAKEN as its "
		      "denominator, not the 23 the file asked for", Seg3);
		Check(Seg3.find("propPlacedCollisionUnread=1/3") != std::string::npos,
		      "the unread count ships the same denominator, on the same line, at "
		      "the same instant", Seg3);
		Check(Seg3.find("propPlacedCollisionNoOn=prop_pavement_sign_0") != std::string::npos,
		      "and the piece that read NO is NAMED, because a count cannot be fixed "
		      "and a name can", Seg3);
		Check(Seg3.find("propPlacedCollisionStat=placed-prop-mesh-components-whose-asset-"
		                "reports-collision/over-placed-prop-meshes/PROXY-only-a-sweep-"
		                "answers-whether-a-capsule-is-stopped") != std::string::npos,
		      "the stat names the population AND carries PROXY, because only a sweep "
		      "answers whether a capsule is stopped and this reads an asset", Seg3);
		// A9 OF THE RULING OF 2026-09-09: THE DIVERGENCE ON THE LINE WHERE THE
		// NUMBERS MEET. The importer calls a missing body setup NO over saved
		// assets; this side calls it UNKNOWN over assets loaded at runtime,
		// ruled 2026-09-08. A reader holding both files saw two words for one
		// case and could not tell a decision from a bug, so the decision rides
		// the value and not a header comment twelve hundred lines away.
		Check(Seg3.find("/a-missing-body-setup-reads-UNKNOWN-here-and-NO-in-"
		                "import_prop_meshes.py/ruled-2026-09-08/two-populations-at-"
		                "two-times/never-added-never-differenced") != std::string::npos,
		      "the stat names the RULED DIVERGENCE with the importer, in its own "
		      "value, where a reader meets the number", Seg3);
		Check(Seg3.find("propPlacedCollisionStat=") != std::string::npos
		      && Seg3.find("UNKNOWN-here-and-NO-in-import_prop_meshes.py")
		         > Seg3.find("propPlacedCollisionStat="),
		      "and it rides propPlacedCollisionStat rather than a second key, so the "
		      "two tallies are never printed as a pair without their populations",
		      Seg3);
		// THE RENAME, WHICH IS HALF OF A5. The old key counted MESHES under a
		// name that said PRIMS and collided with a key of the same name that
		// tools/ue/import_prop_meshes.py emits over a different population.
		// A SYNTHETIC REJECTING FIXTURE: these two strings now exist nowhere
		// in this segment, so doing the work this tool prompts cannot break it.
		Check(Seg3.find("propCollisionPrims") == std::string::npos,
		      "REJECTING CASE - the old propCollisionPrims name is gone from the "
		      "street side, so it cannot collide with the importer's key of the "
		      "same name over a different population", Seg3);
		Check(Seg3.find("propCollisionEnabled") == std::string::npos,
		      "REJECTING CASE - propCollisionEnabled is gone too: it restated the "
		      "bool that set it and could not fail", Seg3);
		Check(Seg3.find("propCollisionAsked=QueryOnly/the-walk-path/NOT-A-MEASUREMENT-"
		                "restates-bInteractive") != std::string::npos,
		      "what is left of it says in its own value that it is not a measurement, "
		      "and still tells a reader which path built the street", Seg3);
		// THE ZERO DENOMINATOR, WHICH IS THE OTHER HALF OF A5. The last
		// landed walk run printed propCollisionPrims=0/0 with
		// propCollisionUnread=0 beside it.
		PropSegmentIn None;
		None.MeshPiecesInFile = ShapeCount(S.Pieces, "mesh");
		None.PackageDir = "/Game/Ledger/Props";
		None.NamePrefix = "SM_";
		None.PlacedAsBox = None.MeshPiecesInFile;
		const std::string SegNone = PropMeshSegment(None);
		std::printf("    %s\n", SegNone.c_str());
		Check(SegNone.find("propPlacedWithCollision=nothing-measured/0") != std::string::npos,
		      "a run that placed no prop mesh PRINTS THE WORDS nothing measured "
		      "rather than a zero over a zero", SegNone);
		Check(SegNone.find("propPlacedCollisionUnread=nothing-measured/0") != std::string::npos,
		      "and so does the unread count, which used to print a bare 0 with no "
		      "denominator at all", SegNone);
		Check(SegNone.find("propPlacedWithCollision=0/0") == std::string::npos,
		      "REJECTING CASE - 0/0 cannot appear on that key, because a clean "
		      "result and a result that examined nothing must not read alike",
		      SegNone);
		// THE CAP ON THE NAMED LIST, BOTH WAYS ROUND.
		PropSegmentIn Many = In;
		Many.Collision = PropCollisionTally();
		for (int I = 0; I < 5; ++I)
		{
			char N[64];
			std::snprintf(N, sizeof(N), "prop_synthetic_%d", I);
			Many.Collision.Add(N, PropCollision_No);
		}
		const std::string SegMany = PropMeshSegment(Many);
		Check(SegMany.find("propPlacedCollisionNoOn=prop_synthetic_0;prop_synthetic_1;"
		                   "prop_synthetic_2;prop_synthetic_3;(+1~more~not~shown)")
		      != std::string::npos,
		      "a cap that BITES announces itself and says how many it withheld",
		      SegMany);
		Check(Seg3.find("propPlacedCollisionNoOn=prop_pavement_sign_0 ") != std::string::npos,
		      "and the same cap, NOT biting on one name, says nothing at all about a "
		      "cap", Seg3);
		// THE IDENTITY BETWEEN TWO COUNTERS IN TWO DIFFERENT FILES, both ways
		// round. Every placed prop mesh is asked exactly once, so the
		// readings taken and the meshes placed are one number; they are kept
		// by two counters in VignetteShot.cpp and a silent disagreement
		// between them is what makes a denominator a lie.
		Check(Seg3.find("propCollisionReadingsMismatch") == std::string::npos,
		      "ACCEPTING CASE - three readings over three placed meshes prints no "
		      "mismatch key at all", Seg3);
		Check(Seg3.find("propPlacedCollisionUnknownOn=prop_skip_0") != std::string::npos,
		      "the piece that read UNKNOWN is named too, in its own key, because a "
		      "NO is an asset to fix and an UNKNOWN is a reading to chase", Seg3);
		Check(SegNone.find("propPlacedCollisionUnknownOn=none") != std::string::npos,
		      "and a run with no readings at all says none there rather than naming "
		      "a piece nobody asked about", SegNone);
		PropSegmentIn Off = In;
		Off.PlacedAsMesh = 4;
		Check(PropMeshSegment(Off).find(
		          "propCollisionReadingsMismatch=readings=3/meshesPlaced=4")
		      != std::string::npos,
		      "PLANTED CASE - one reading short of the meshes placed says so, with "
		      "both numbers, rather than printing a denominator nobody asked",
		      PropMeshSegment(Off));

		// C. THE BURIAL HALF, PLANTED FIRST BECAUSE THE VERDICTS LIVE HERE.
		// A LADDER OF TWO RUNGS, ONE CONTRIBUTOR TOGGLED, SAME VANTAGE, SAME
		// RUN: the identical prop read under an open sky and then under a
		// slab. The difference between the rungs is the reading.
		std::vector<PlacedBox> Lad;
		PlacedBox Prop;
		Prop.Name = "prop_planted_0"; Prop.Edge = "planted_edge"; Prop.Region = "x00_06";
		Prop.bProp = true; Prop.bFromAsset = true;
		Prop.MinX = 1.8; Prop.MaxX = 2.2; Prop.MinY = -0.10; Prop.MaxY = -0.085;
		Prop.MinZ = 2.6; Prop.MaxZ = 3.0;
		Lad.push_back(Prop);
		std::vector<BurialRead> Rung1 = ReadBurials(Lad);
		Check(Rung1.size() == 1 && Rung1[0].Cells == BurialGridSide() * BurialGridSide(),
		      "ACCEPTING CASE - a prop with nothing over it is still EXAMINED, and "
		      "says how many cells it examined");
		Check(Rung1.size() == 1 && Rung1[0].Buried == 0 && Rung1[0].Open == Rung1[0].Cells,
		      "and it reads every cell OPEN, which is what a correctly placed prop "
		      "on an open street must read");
		// RUNG 2: one slab added, nothing else changed, and it STRADDLES the
		// prop's top the way ground_east_channel straddles the grate's.
		PlacedBox Slab;
		Slab.Name = "planted_slab"; Slab.Edge = "planted_edge"; Slab.Region = "x00_06";
		Slab.MinX = 0.0; Slab.MaxX = 42.0; Slab.MinY = -0.37; Slab.MaxY = -0.0718;
		Slab.MinZ = 2.6; Slab.MaxZ = 3.0;
		Lad.push_back(Slab);
		std::vector<BurialRead> Rung2 = ReadBurials(Lad);
		std::printf("    ladder: rung1 buried=%d/%d open=%d  rung2 buried=%d/%d "
		            "deepestMm=%.2f by=%s\n",
		            Rung1[0].Buried, Rung1[0].Cells, Rung1[0].Open,
		            Rung2[0].Buried, Rung2[0].Cells, Rung2[0].DeepestMm,
		            Rung2[0].DeepestBy.c_str());
		Check(Rung2.size() == 1 && Rung2[0].Buried == Rung2[0].Cells
		      && Rung2[0].FullyBuried(),
		      "PLANTED CASE - the same prop under a slab that straddles its top "
		      "reads every cell BURIED");
		Check(Rung2.size() == 1 && Rung2[0].DeepestBy == "planted_slab"
		      && Rung2[0].DeepestMm > 13.0 && Rung2[0].DeepestMm < 13.5,
		      "the covering piece is NAMED and the depth is the millimetres it "
		      "would have to rise to clear it");
		Check(Rung1[0].Buried != Rung2[0].Buried,
		      "and the two rungs DIFFER, which is the only thing a ladder measures: "
		      "a rung that reads the same under both is measuring neither");
		// THE PREDICATE IS STRADDLE AND NOT ANYTHING-ABOVE, which is the
		// difference between a buried grate and a prop under an awning.
		std::vector<PlacedBox> Awn;
		Awn.push_back(Prop);
		PlacedBox Over = Slab;
		Over.Name = "planted_awning";
		Over.MinY = -0.0800; Over.MaxY = 2.95;
		Awn.push_back(Over);
		std::vector<BurialRead> Hung = ReadBurials(Awn);
		std::printf("    overhead: buried=%d/%d overhung=%d open=%d headroomMm=%.2f by=%s\n",
		            Hung[0].Buried, Hung[0].Cells, Hung[0].Overhung, Hung[0].Open,
		            Hung[0].HeadroomMm, Hung[0].HeadroomBy.c_str());
		Check(Hung[0].Buried == 0 && Hung[0].Overhung == Hung[0].Cells,
		      "PLANTED CASE - a piece entirely ABOVE the prop's top reads OVERHUNG "
		      "and not buried, so an awning cannot print as a burial");
		Check(Hung[0].HeadroomMm > 4.9 && Hung[0].HeadroomMm < 5.1
		      && Hung[0].HeadroomBy == "planted_awning",
		      "and the gap to it is measured in millimetres with the piece named, "
		      "because five millimetres of daylight is the whole difference");
		// AND THE THREE BUCKETS ARE A PARTITION, which is the arithmetic a
		// reader of three percentages is entitled to assume.
		bool bPartition = true;
		for (size_t I = 0; I < Hung.size(); ++I)
		{
			if (Hung[I].Buried + Hung[I].Overhung + Hung[I].Open != Hung[I].Cells)
			{
				bPartition = false;
			}
		}
		Check(bPartition,
		      "buried plus overhung plus open is every cell examined and not one more");

		// D. THE LIVE STREET, WHICH IS THE ACCEPTING FIXTURE, PRINTED AND
		// NOT JUDGED. These are the numbers the next walk run will print,
		// taken here off the FILE rather than off the engine's placement, so
		// the two can be compared when the run lands. No assertion below
		// says the street is correct: a guard that goes red when the street
		// spec is FIXED is a ratchet, and A6 is a measurement order, not a
		// bound.
		std::vector<PlacedBox> Live;
		for (size_t I = 0; I < S.Pieces.size(); ++I)
		{
			Live.push_back(SpecBoxBounds(S.Pieces[I]));
		}
		// WORST FIRST, THROUGH THE HEADER'S OWN SORTER, so this printed series
		// and the propBuriedOn key under it are in one order and not two.
		const std::vector<BurialRead> LiveReads = SortedBurials(ReadBurials(Live));
		// A8 OF THE RULING OF 2026-09-09, FIRST PART: EVERY BURIED PROP, NOT
		// THE WORST THREE AND NOT THE WORST SIX. propAnyBuried=10/23 was the
		// line nobody had read: the verdict key names three and announces
		// seven held, which is honest about the cap and silent about the
		// seven, and a header comment accounting for five of them as AABBs
		// touching at 0.00 mm is an analysis and not evidence. THERE IS NO CAP
		// ON THIS PRINTOUT, which is why nothing here announces one; the
		// verdict line's cap of three stays where it is because that line has
		// a buffer, and a reader who wants all ten has this series. The cell
		// count rides each row because 5.0 percent of 400 cells is 20 cells
		// and a percentage alone cannot say that.
		std::printf("    burial series, %d prop(s) read of %d mesh piece(s) in the file, "
		            "EVERY buried prop, no cap:\n",
		            (int)LiveReads.size(), ShapeCount(S.Pieces, "mesh"));
		int Shown = 0;
		for (size_t I = 0; I < LiveReads.size(); ++I)
		{
			if (LiveReads[I].Buried <= 0) { continue; }
			std::printf("      %-28s edge=%-16s buried=%5.1f%%/%3d-of-%d-cells "
			            "overhung=%5.1f%% open=%5.1f%% deepestMm=%8.2f by=%s\n",
			            LiveReads[I].Name.c_str(), LiveReads[I].Edge.c_str(),
			            LiveReads[I].BuriedPct(), LiveReads[I].Buried, LiveReads[I].Cells,
			            LiveReads[I].OverhungPct(), LiveReads[I].OpenPct(),
			            LiveReads[I].DeepestMm, LiveReads[I].DeepestBy.c_str());
			++Shown;
		}
		// THE ZERO'S DENOMINATOR, ON THE SAME LINE AS THE ZERO. A clean street
		// and a street nobody examined print different words here.
		std::printf("      buriedProps=%d/%d examined, %d read no buried cell at all%s\n",
		            Shown, (int)LiveReads.size(), (int)LiveReads.size() - Shown,
		            LiveReads.empty() ? " (nothing measured: no prop was examined)" : "");
		if (Shown == 0 && !LiveReads.empty())
		{
			std::printf("      no prop read a buried cell, over %d prop(s) examined\n",
			            (int)LiveReads.size());
		}
		Check((int)LiveReads.size() == ShapeCount(S.Pieces, "mesh"),
		      "ACCEPTING CASE - every mesh piece in the committed street got a "
		      "footprint reading, and the denominator is the file's own count");
		bool bOrdered = true;
		for (size_t I = 1; I < LiveReads.size(); ++I)
		{
			if (WorseBurial(LiveReads[I], LiveReads[I - 1])) { bOrdered = false; }
		}
		Check(bOrdered,
		      "the series comes back worst first, by the one ordering rule the "
		      "summary key uses, so a reader cannot be shown a worst that is not "
		      "the top of the list");
		Check(WorseBurial(Rung2[0], Rung1[0]) && !WorseBurial(Rung1[0], Rung2[0]),
		      "and that rule is antisymmetric on the planted pair: the buried rung "
		      "is worse than the open one and the open one is not worse than it");
		const int Subject = BurialIndexOf(LiveReads, BurialSubjectName());
		Check(Subject >= 0,
		      "the piece A6 names by hand is still in the committed street under that "
		      "name, so a rename goes red here rather than printing not-placed for ever",
		      BurialSubjectName());
		if (Subject >= 0)
		{
			const BurialRead& G = LiveReads[(size_t)Subject];
			// no-asset-to-read is what the run prints for this piece TODAY,
			// because propsAsMesh=0/23: the fixture says the same rather than
			// inventing a word the run could not have produced.
			const std::string Row = BurialRowValue(G, "no-asset-to-read");
			std::printf("    A6 subject, from the FILE (the run prints the same read "
			            "off the ENGINE): %s\n", Row.c_str());
			std::printf("    A6 covers, deepest first: %s\n",
			            CappedList(G.ByCover, 4, G.CoverCount, ";", "none").c_str());
			Check(G.Buried + G.Overhung + G.Open == G.Cells,
			      "and its three buckets partition its footprint");
			Check(Row.find(' ') == std::string::npos && Row.find('\t') == std::string::npos,
			      "the subject row is one whitespace-free token, so a reader that "
			      "splits on space cannot truncate it", Row);
			Check(Row.find("/collision=no-asset-to-read/") != std::string::npos,
			      "and it carries the piece's OWN collision word beside its burial, "
			      "because Jafar's item 2 is one sentence with two halves and a "
			      "tally of 23 answers neither of them for one piece", Row);
			Check(BurialRowValue(G, "YES").find("/collision=YES/") != std::string::npos,
			      "PLANTED CASE - the same row with the asset reading YES says YES "
			      "there, so that field can move while the burial stands still");
		}

		// D2. A8, SECOND PART: THE PER-CELL DEPTH SERIES ACROSS THE SUBJECT'S
		// FOOTPRINT, WITH EACH CELL'S Z BESIDE IT, AND BOTH READINGS OF EVERY
		// POINT.
		//
		// WHAT IT SETTLES. Two numbers were argued in prose for the
		// carriageway's cover over this grate, 18.7 mm and 19.90 mm, and
		// neither was a named statistic: one is a SAMPLED CELL CENTRE and the
		// other is the FOOTPRINT EDGE, on one plane, and a series shows that
		// where two paragraphs could not. Rule 2 in its own order: the printer
		// first, the real run second, a bound only after and only if one is
		// ever wanted. NOTHING HERE IS A BOUND and nothing below asserts a
		// live millimetre.
		//
		// THE PLANTED PAIR CARRIES THE VERDICTS, as everywhere else in this
		// section, because a guard pinned to the street's current fault goes
		// red the day the street is fixed.
		{
			// ACCEPTING CASE FIRST: the pitch arithmetic on a slab whose
			// answer can be done by hand. A 45 degree slab 0.2 m thick
			// through its own centre: the top face is at HY*cos45 above the
			// centre minus the z it has fallen, which is 0.141421 at z=0, and
			// the vertical cut through it is 0.2/cos45 = 0.282843 thick.
			Piece Flat;
			Flat.Name = "planted_pitched_slab"; Flat.Shape = "box";
			Flat.X = 0; Flat.Y = 0; Flat.Z = 0;
			Flat.SX = 2; Flat.SY = 0.2; Flat.SZ = 2; Flat.PitchDeg = 45;
			double Lo = 0, Hi = 0;
			std::string SpanWhy;
			const bool bSpan = PitchedSpanAtXZ(Flat, 0.0, 0.0, Lo, Hi, SpanWhy);
			std::printf("    A8 pitch span, 45deg slab at its centre: ok=%d loY=%.6f "
			            "hiY=%.6f thickness=%.6f why=%s\n",
			            bSpan ? 1 : 0, Lo, Hi, Hi - Lo, SpanWhy.c_str());
			Check(bSpan && Hi > 0.14142 && Hi < 0.14143 && Lo < -0.14142 && Lo > -0.14143,
			      "ACCEPTING CASE - the pitched top face at a point is the face and "
			      "not the bounding box: 0.141421 where the AABB top is 0.777817");
			Check(bSpan && (Hi - Lo) > 0.28284 && (Hi - Lo) < 0.28285,
			      "and the vertical cut through a 45 degree slab 0.200 m thick is "
			      "0.282843 m, which is the arithmetic being checked and not a name");
			// THE TWO REFUSALS, BOTH BY NAME, because a refusal that read as
			// clear sky would make this instrument the thing it corrects.
			Piece Yawed = Flat;
			Yawed.Name = "planted_yawed_slab"; Yawed.PitchDeg = 0; Yawed.YawDeg = 30;
			Check(!PitchedSpanAtXZ(Yawed, 0.0, 0.0, Lo, Hi, SpanWhy)
			      && SpanWhy.find("yawed-or-rolled") != std::string::npos,
			      "REJECTING CASE - a yawed cover is refused BY NAME rather than "
			      "answered wrongly, and the street carries 44 of them", SpanWhy);
			Check(!PitchedSpanAtXZ(Flat, 0.0, 1.9, Lo, Hi, SpanWhy)
			      && SpanWhy.find("the-solid-does-not-reach-this-point") != std::string::npos,
			      "REJECTING CASE - a point past the slab's own turned extent is not "
			      "covered by it, and the reason says so rather than a zero", SpanWhy);

			// A PLANTED STREET OF TWO PIECES, WHICH IS THE LADDER FOR THIS
			// READING: one prop, one cross-falling slab over it, and the three
			// statistics of one plane printed together. The numbers are
			// arithmetic off these two rows and nothing can repair them.
			std::vector<Piece> Plant;
			Piece PProp;
			PProp.Name = "prop_planted_grate_0"; PProp.Shape = "mesh";
			PProp.Edge = "planted_edge"; PProp.Region = "x00_06";
			PProp.X = 0; PProp.Y = -0.1; PProp.Z = 0;
			PProp.SX = 0.4; PProp.SY = 0.02; PProp.SZ = 0.4;
			Piece PSlab;
			PSlab.Name = "planted_cross_fall"; PSlab.Shape = "box";
			PSlab.Edge = "planted_edge"; PSlab.Region = "x00_06";
			PSlab.X = 0; PSlab.Y = -0.2; PSlab.Z = 0;
			PSlab.SX = 10; PSlab.SY = 0.3; PSlab.SZ = 1.0;
			PSlab.PitchDeg = 1.432096;
			Plant.push_back(PProp);
			Plant.push_back(PSlab);
			std::string PlantWhy;
			const std::vector<CoverCell> PlantProf =
				ReadCoverProfile(Plant, "prop_planted_grate_0", PlantWhy);
			std::printf("    A8 planted profile: %s\n",
			            CoverProfileValue(PlantProf, PlantWhy).c_str());
			// EACH STATISTIC COUNTED UNDER ITS OWN NAME, which is the whole
			// point of the three Where values: a loop that lumped the edges
			// and the centre line together would be the 18.7 against 19.90
			// mistake committed inside the test that was written to settle it.
			int PlantCentres = 0, PlantEdges = 0, PlantMiddles = 0;
			double PlantWorstCentre = -1, PlantWorstEdge = -1, PlantAabb = -1;
			for (size_t I = 0; I < PlantProf.size(); ++I)
			{
				if (PlantProf[I].Where == "cell-centre")
				{
					++PlantCentres;
					if (PlantProf[I].bLocal && PlantProf[I].LocalDepthMm > PlantWorstCentre)
					{
						PlantWorstCentre = PlantProf[I].LocalDepthMm;
					}
				}
				else if (PlantProf[I].Where == "footprint-edge")
				{
					++PlantEdges;
					if (PlantProf[I].bLocal && PlantProf[I].LocalDepthMm > PlantWorstEdge)
					{
						PlantWorstEdge = PlantProf[I].LocalDepthMm;
					}
				}
				else { ++PlantMiddles; }
				if (PlantProf[I].bAabb && PlantProf[I].AabbDepthMm > PlantAabb)
				{
					PlantAabb = PlantProf[I].AabbDepthMm;
				}
			}
			Check(PlantCentres == BurialGridSide() && PlantEdges == 2 && PlantMiddles == 1,
			      "PLANTED CASE - the profile samples the tally's own cell centres "
			      "AND the two footprint edges the tally never samples AND the "
			      "footprint centre line, and says which each point is");
			Check(PlantWorstEdge > 45.0 && PlantWorstEdge < 45.1,
			      "the deepest cover over the footprint is 45.05 mm at its edge, "
			      "which is arithmetic off the planted rows");
			Check(PlantWorstCentre > 44.7 && PlantWorstCentre < 44.9,
			      "and the deepest over SAMPLED CELL CENTRES is 44.80 mm, a quarter "
			      "of a millimetre shallower: one plane, two statistics, which is "
			      "the whole of the 18.7 against 19.90 argument");
			Check(PlantWorstEdge > PlantWorstCentre,
			      "the edge reading is the deeper of the two and a reader is shown "
			      "both rather than one under a name that fits either");
			Check(PlantAabb > 52.4 && PlantAabb < 52.5 && PlantAabb > PlantWorstEdge,
			      "PLANTED CASE - and the AABB reading of the same slab is 52.46 mm, "
			      "which OVERSTATES the deepest real cover, because an AABB top is "
			      "the slab's high edge");
			// THE TWO-POINT FIGURE, PLANTED TOO, because it is the one the
			// ruling's 70.10 mm is and the one a reader computes by hand off a
			// comment. 52.45 mm of AABB depth at the worst cell less 40.05 mm
			// of real cover at the centre line is 12.40 mm here.
			const std::string PlantValue = CoverProfileValue(PlantProf, PlantWhy);
			Check(PlantValue.find("/aabbWorstMinusThis=12.40mm/TWO-POINTS-and-says-so")
			      != std::string::npos,
			      "PLANTED CASE - the two-point overstatement is printed AND carries "
			      "the words TWO-POINTS, so it cannot be read as the same-point "
			      "figure beside it", PlantValue);
			// THE THIRD BUCKET OF THE LOCAL COLUMN, PLANTED: the same slab
			// lifted clear leaves the prop OVERHUNG and not buried, so a zero
			// in the depth column can never mean two things.
			std::vector<Piece> Lift;
			Lift.push_back(PProp);
			Piece PHigh = PSlab;
			PHigh.Name = "planted_lifted_slab";
			// ITS UNDERSIDE NOW CLEARS THE PROP'S TOP. The span's floor at the
			// +z footprint edge is -0.015050, which is 74.95 mm of daylight
			// over a top at -0.090, and that is the number asserted below:
			// arithmetic off these two planted rows and nothing else.
			PHigh.Y = 0.14;
			Lift.push_back(PHigh);
			std::string LiftWhy;
			const std::vector<CoverCell> LiftProf =
				ReadCoverProfile(Lift, "prop_planted_grate_0", LiftWhy);
			int LiftBuried = 0, LiftOverhung = 0;
			double LiftHeadroom = -1;
			for (size_t I = 0; I < LiftProf.size(); ++I)
			{
				if (LiftProf[I].bLocal) { ++LiftBuried; }
				else if (LiftProf[I].bLocalAbove)
				{
					++LiftOverhung;
					if (LiftHeadroom < 0 || LiftProf[I].LocalAboveHeadroomMm < LiftHeadroom)
					{
						LiftHeadroom = LiftProf[I].LocalAboveHeadroomMm;
					}
				}
			}
			std::printf("    A8 planted lifted slab: buriedAt=%d/%d overhungAt=%d/%d "
			            "leastHeadroomMm=%.2f\n", LiftBuried, (int)LiftProf.size(),
			            LiftOverhung, (int)LiftProf.size(), LiftHeadroom);
			Check(LiftBuried == 0 && LiftOverhung == (int)LiftProf.size()
			      && LiftHeadroom > 74.8 && LiftHeadroom < 75.1,
			      "PLANTED CASE - lift the same slab clear and every point reads "
			      "OVERHUNG with 74.95 mm of daylight rather than a 0.00 mm that "
			      "could mean open sky");

			// THE LIVE STREET, PRINTED AND NEVER JUDGED. This is the series
			// A8 ordered and the one any future bound would be read off.
			std::string ProfWhy;
			const std::vector<CoverCell> Prof =
				ReadCoverProfile(S.Pieces, BurialSubjectName(), ProfWhy);
			std::printf("    A8 cover profile of %s, %d point(s), NO CAP, "
			            "pitch-aware local top beside the AABB depth at the same "
			            "point:\n", BurialSubjectName(), (int)Prof.size());
			if (Prof.empty())
			{
				std::printf("      nothing measured: %s\n", ProfWhy.c_str());
			}
			for (size_t I = 0; I < Prof.size(); ++I)
			{
				char Idx[24];
				if (Prof[I].Index >= 0) { std::snprintf(Idx, sizeof(Idx), "iz=%-2d", Prof[I].Index); }
				else { std::snprintf(Idx, sizeof(Idx), "at   "); }
				// THE LOCAL COLUMN SAYS WHICH OF THREE IT IS, never a bare
				// zero: buried to a depth, overhung with daylight under it,
				// or nothing overhead at all.
				char Local[96];
				if (Prof[I].bLocal)
				{
					std::snprintf(Local, sizeof(Local), "buried%8.2fmm/by=%s",
					              Prof[I].LocalDepthMm, Prof[I].LocalBy.c_str());
				}
				else if (Prof[I].bLocalAbove)
				{
					std::snprintf(Local, sizeof(Local), "overhung+%7.2fmm/by=%s",
					              Prof[I].LocalAboveHeadroomMm, Prof[I].LocalAboveBy.c_str());
				}
				else
				{
					std::snprintf(Local, sizeof(Local), "nothing-overhead");
				}
				std::printf("      %s %-14s z=%.6f x=%.4f top=%.6f "
				            "aabb=%8.2fmm/by=%-24s local=%-46s over=%8.2fmm\n",
				            Idx, Prof[I].Where.c_str(), Prof[I].Z, Prof[I].X, Prof[I].PropTopM,
				            Prof[I].bAabb ? Prof[I].AabbDepthMm : 0.0,
				            Prof[I].bAabb ? Prof[I].AabbBy.c_str() : "none",
				            Local,
				            (Prof[I].bAabb && Prof[I].bLocal) ? Prof[I].OverstatementMm() : 0.0);
			}
			const std::string ProfValue = CoverProfileValue(Prof, ProfWhy);
			std::printf("    A8 cover profile value: %s\n", ProfValue.c_str());
			Check(ProfValue.find(' ') == std::string::npos
			      && ProfValue.find('\t') == std::string::npos,
			      "the profile's whole reading is one whitespace-free token, so a "
			      "reader that splits on space cannot truncate it", ProfValue);
			// THE SYNTHETIC REJECTING FIXTURE, which is this project's rule for
			// a tool that checks the project itself: a name that exists in no
			// street, so doing the work the tool prompts can never break it.
			std::string GoneWhy;
			const std::vector<CoverCell> Gone =
				ReadCoverProfile(S.Pieces, "prop_synthetic_nowhere_0", GoneWhy);
			const std::string GoneValue = CoverProfileValue(Gone, GoneWhy);
			std::printf("    A8 cover profile, synthetic subject: %s\n", GoneValue.c_str());
			Check(Gone.empty() && GoneValue.find("nothing-measured/0-points-sampled") == 0
			      && GoneValue.find("prop_synthetic_nowhere_0") != std::string::npos,
			      "REJECTING CASE - a subject that is in no street prints the words "
			      "nothing measured with the name it was asked for, and never a zero "
			      "that reads as no cover", GoneValue);
		}

		// E. THE WHOLE SEGMENT AS A READER SEES IT: concatenated onto the
		// scene line, which is what GSceneLine is, so a key repeated across
		// the two halves would be returned by whichever one a grep reached
		// first.
		PropSegmentIn LiveIn;
		LiveIn.MeshPiecesInFile = ShapeCount(S.Pieces, "mesh");
		LiveIn.PackageDir = "/Game/Ledger/Props";
		LiveIn.NamePrefix = "SM_";
		LiveIn.PlacedAsBox = LiveIn.MeshPiecesInFile;
		LiveIn.Burials = LiveReads;
		LiveIn.bInteractive = true;
		const std::string LiveSeg = PropMeshSegment(LiveIn);
		const std::string Whole = Scene + " " + LiveSeg;
		std::printf("    %s\n", LiveSeg.c_str());
		std::printf("    segment: chars=%d wholeSceneLineChars=%d\n",
		            (int)LiveSeg.size(), (int)Whole.size());
		Check(LiveSeg.find("propSegmentTruncated") == std::string::npos,
		      "no chunk of the segment overran its buffer, and a chunk that did "
		      "would have said so in its own key", LiveSeg);
		Check(EveryTokenIsKeyValue(LiveSeg),
		      "every token of the segment is a key with a non-empty value and no "
		      "whitespace inside it, which is what every reader in this project "
		      "splits on", LiveSeg);
		// AND THE LINE THE RUN ACTUALLY PRINTS, WHICH IS THIS SEGMENT
		// CONCATENATED ONTO SceneLine. NOT asserted, because SceneLine has
		// one token of its own that carries no equals: the zero case of
		// flatsLit prints "flatsLit=0/0 nothing-to-light", so a grep for
		// flatsLit gets the zero WITHOUT the words beside it and a
		// whitespace-splitting reader gets a stray token. That is a fault in
		// a key amendments A5 and A6 do not own, and the count is printed
		// here rather than fixed or hidden.
		{
			std::istringstream WIn(Whole);
			std::string WTok;
			int Loose = 0;
			std::string LooseNames;
			while (WIn >> WTok)
			{
				if (WTok.find('=') != std::string::npos && WTok.find('=') != 0) { continue; }
				++Loose;
				if (Loose <= 3)
				{
					if (!LooseNames.empty()) { LooseNames += ","; }
					LooseNames += WTok;
				}
			}
			std::printf("    whole scene line: tokens carrying no key=value: %d (%s)\n",
			            Loose, Loose == 0 ? "none" : LooseNames.c_str());
		}
		{
			std::vector<std::string> K;
			KeysOf(Whole, K);
			std::string Dup;
			for (size_t I = 0; I < K.size(); ++I)
			{
				for (size_t J = I + 1; J < K.size(); ++J)
				{
					if (K[I] == K[J]) { Dup = K[I]; }
				}
			}
			std::printf("    keys on the whole scene line: %d, duplicated: %s\n",
			            (int)K.size(), Dup.empty() ? "none" : Dup.c_str());
			Check(Dup.empty(),
			      "no key appears twice once the segment is appended to the scene "
			      "line, because both halves end up on ONE line and every reader "
			      "here greps", Dup);
		}
		Check(LiveSeg.find("propFootprintsRead=23/23") != std::string::npos,
		      "the burial half ships the count it examined over the count the file "
		      "asked for", LiveSeg);
		Check(LiveSeg.find("propFootprintGrid=20x20/400-cells-per-prop/a-gap-narrower-"
		                   "than-one-cell-is-invisible-here") != std::string::npos,
		      "and it says what its own sampler cannot see, rather than leaving the "
		      "resolution to be assumed", LiveSeg);
		Check(LiveSeg.find("propBuriedByEdge=") != std::string::npos
		      && LiveSeg.find("east_channel=") != std::string::npos,
		      "the breakdown is per EDGE, which is an axis placement varies on, and "
		      "names the edges the props sit on", LiveSeg);
		// AND THE NEVER-RAN CASE FOR THE BURIAL HALF TOO.
		PropSegmentIn NoProps;
		NoProps.MeshPiecesInFile = 0;
		NoProps.PackageDir = "/Game/Ledger/Props";
		NoProps.NamePrefix = "SM_";
		const std::string SegEmpty = PropMeshSegment(NoProps);
		std::printf("    %s\n", SegEmpty.c_str());
		Check(SegEmpty.find("propFootprintsRead=nothing-measured/0") != std::string::npos,
		      "a run that examined no footprint at all PRINTS THE WORDS nothing "
		      "measured", SegEmpty);
		Check(SegEmpty.find("propFullyBuried=nothing-measured/0") != std::string::npos,
		      "and the count of buried props says the words too, because 0 buried of "
		      "0 examined is not a clean street", SegEmpty);
		Check(SegEmpty.find("propBurialWorst=nothing-measured/of=0") != std::string::npos
		      && SegEmpty.find(std::string("propBurialSubject=not-placed/asked=")
		                       + BurialSubjectName()) != std::string::npos,
		      "and the named subject says NOT PLACED rather than printing a clean "
		      "row for a piece nobody spawned", SegEmpty);
	}

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
		std::vector<std::string> Tried;
		Tried.push_back("C:/staged/LedgerProbe/CityPackTextures");
		Tried.push_back("C:/staged/LedgerProbe/Binaries/Win64/CityPackTextures");
		const std::string D = LedgerSurface::MaterialsDoneLine(
			All, "/Game/Ledger/M_LedgerSurface", true, "C:/pack/textures", 51, Tried,
			593, 4, 152, 2.0);
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
			All, "/Game/Ledger/M_LedgerSurface", false, "C:/pack/textures", 51, Tried,
			593, 4, 0, 2.0);
		Check(NoBase.find("materialsStatus=NO-BASE-MATERIAL") != std::string::npos
		      && NoBase.find("materialBase=MISSING") != std::string::npos,
		      "a missing base material is its own status and outranks the texture count");
		// AND A PASS WITH NOTHING TO DO SAYS THE WORDS.
		const std::vector<LedgerSurface::Bound> None;
		const std::string Empty = LedgerSurface::MaterialsDoneLine(
			None, "/Game/Ledger/M_LedgerSurface", true, "", 0, Tried, 0, 0, 0, 2.0);
		Check(Empty.find("materialsStatus=NOTHING-ASKED") != std::string::npos
		      && Empty.find("texRoot=NOT-FOUND") != std::string::npos,
		      "a pass with no surfaces says nothing-asked and a root it never found says so");
		// AND IT NAMES WHERE IT LOOKED. This is the half run 19 did not have:
		// `texRoot=NOT-FOUND` alone cannot tell a pack in the wrong place
		// from a search in the wrong place.
		Check(Empty.find("texRootTried=C:/staged/LedgerProbe/CityPackTextures,"
		                 "C:/staged/LedgerProbe/Binaries/Win64/CityPackTextures")
		      != std::string::npos,
		      "a texture root that was not found NAMES every directory it asked about");
		Check(NoSpacePastPrefix(Empty, "materialsStatus="),
		      "and the candidate list is still one space-free value with one equals");
	}
	// ---- THE MID READBACK, WHICH IS THE HALF NOBODY HAD -----------------
	//
	// WHAT THESE PROVE AND WHAT THEY CANNOT. Nothing here runs an engine, so
	// none of this says a parameter arrives anywhere. It says that when the
	// engine answers, the answer is counted, worded and printed correctly,
	// and that the three outcomes a reader has to tell apart print three
	// different strings: same, different, and never asked. The last one is
	// the one that cost this project days elsewhere.
	{
		// THE ACCEPTING CASE FIRST. A surface whose instance answered with
		// exactly what went into it.
		LedgerSurface::Bound B;
		B.Surface = "brick_red"; B.Pieces = 41; B.PiecesAssigned = 41;
		B.Status = "RESOLVED"; B.Reason = "none";
		B.MapFound[0] = true; B.MapFile[0] = "brick_red.jpg";
		B.MapW[0] = 2048; B.MapH[0] = 1024;
		B.TileU = 1.90; B.TileV = 1.00;
		B.Read.bAsked = true;
		B.Read.bTexSame = true; B.Read.bScalarSame = true;
		B.Read.bResourceValid = true; B.Read.bCompIsMid = true;
		B.Read.TexGot = "/Engine/Transient.Texture2D_7";
		B.Read.CompGot = "/Game/Ledger/M_LedgerSurface";
		B.Read.SetU = 1.90; B.Read.GotU = 1.90;
		B.Read.SetV = 1.00; B.Read.GotV = 1.00;
		const std::string L = LedgerSurface::SurfaceLine(B);
		std::printf("    %s\n", L.c_str());
		Check(L.find("midTexReadback=same-pointer") != std::string::npos,
		      "an instance that answered with the pointer that went in says so");
		Check(L.find("midTilingReadback=same-value") != std::string::npos,
		      "and the scalar half is a SEPARATE word on the same line, not the same one twice");
		Check(L.find("midTexResource=valid") != std::string::npos
		      && L.find("midCompMaterial=is-the-instance-we-made") != std::string::npos,
		      "the resource and the component's material are their own readings");
		Check(L.find("midTilingSetGot=U.1.9000..1.9000/V.1.0000..1.0000") != std::string::npos,
		      "both halves of every scalar comparison are printed, set and got");
		Check(NoSpacePastPrefix(L, "midTexReadback="),
		      "every readback value is one space-free token with one equals");
		// THE REJECTING CASE, PLANTED, because a guard that cannot tell a
		// regression from an improvement is a ratchet. This is candidate B as
		// it would print: the scalars land and the texture does not, and what
		// came back instead is NAMED rather than left as a no.
		LedgerSurface::Bound Bad = B;
		Bad.Read.bTexSame = false;
		Bad.Read.TexGot = "/Engine/EngineResources/DefaultTexture.DefaultTexture";
		Bad.Read.bResourceValid = false;
		const std::string BL = LedgerSurface::SurfaceLine(Bad);
		Check(BL.find("midTexReadback=OTHER/"
		              "/Engine/EngineResources/DefaultTexture.DefaultTexture")
		      != std::string::npos,
		      "an instance that answered with something else NAMES what came back");
		Check(BL.find("midTexResource=NULL") != std::string::npos
		      && BL.find("midTilingReadback=same-value") != std::string::npos,
		      "a failed texture readback does not drag the scalar reading down with it");
		Check(NoSpacePastPrefix(BL, "midTexReadback="),
		      "and an engine path name still leaves one equals per token");
		// AND THE CASE THAT WAS NEVER ASKED. A `no` here would say the engine
		// answered wrongly; nothing was ever set, and that is a different
		// fact with a different next action.
		LedgerSurface::Bound Never;
		Never.Surface = "card"; Never.Pieces = 10; Never.Status = "ABSENT";
		const std::string NL = LedgerSurface::SurfaceLine(Never);
		Check(NL.find("midTexReadback=not-asked") != std::string::npos
		      && NL.find("midTilingReadback=not-asked") != std::string::npos
		      && NL.find("midTilingSetGot=not-asked") != std::string::npos,
		      "a surface no instance was made for says not-asked and never prints a no");
	}
	// NO KEY MEANS TWO THINGS ON TWO LINES, ASSERTED RATHER THAN INTENDED.
	// The per-surface readback and the run's readback totals are different
	// moments, and a key carrying both would be returned by a grep from
	// whichever line it reached first. This walks the two lines the run
	// actually prints and fails on any key name they share.
	{
		LedgerSurface::Bound B;
		B.Surface = "kerb"; B.Pieces = 95; B.PiecesAssigned = 95;
		B.MapFound[0] = true; B.Status = "RESOLVED";
		B.Read.bAsked = true; B.Read.bScalarSame = true;
		B.Read.bResourceValid = true; B.Read.bCompIsMid = true;
		std::vector<LedgerSurface::Bound> All;
		All.push_back(B);
		std::vector<std::string> Tried;
		Tried.push_back("C:/staged/LedgerProbe/CityPackTextures");
		const std::string Surf = LedgerSurface::SurfaceLine(B);
		const std::string Done = LedgerSurface::MaterialsDoneLine(
			All, "/Game/Ledger/M_LedgerSurface", true, "C:/pack", 51, Tried,
			593, 3, 95, 2.0);
		std::vector<std::string> SurfKeys, DoneKeys;
		KeysOf(Surf, SurfKeys);
		KeysOf(Done, DoneKeys);
		std::string Shared;
		for (size_t I = 0; I < SurfKeys.size(); ++I)
		{
			for (size_t J = 0; J < DoneKeys.size(); ++J)
			{
				if (SurfKeys[I] == DoneKeys[J])
				{
					if (!Shared.empty()) { Shared += "/"; }
					Shared += SurfKeys[I];
				}
			}
		}
		std::printf("    keys: surface line %d, materials line %d, shared %s\n",
		            (int)SurfKeys.size(), (int)DoneKeys.size(),
		            Shared.empty() ? "none" : Shared.c_str());
		Check(Shared.empty(),
		      "the surface line and the materials line share no key name at all",
		      Shared);
		Check(SurfKeys.size() > 5 && DoneKeys.size() > 5,
		      "and both lines were actually read, so an empty intersection is a "
		      "finding rather than an empty examination");
	}
	// THE SCALAR COMPARISON ON ITS OWN, both ways, because the tolerance is
	// the only judgement in the readback and an exact comparison would print
	// a mismatch that belongs to the float conversion.
	{
		Check(LedgerSurface::ScalarMatches(21.0, 21.0),
		      "a value that survived the trip intact matches");
		Check(LedgerSurface::ScalarMatches(1.3719, 1.37190002),
		      "and one the engine kept as a float still matches");
		Check(!LedgerSurface::ScalarMatches(1.90, 1.00),
		      "a tiling that came back as the material's own default does NOT match");
		Check(!LedgerSurface::ScalarMatches(21.0, 0.0),
		      "and a scalar that came back as nothing at all does not match either");
	}
	// THE RUN'S READBACK TOTALS, ON THE MATERIALS DONE LINE, over the
	// denominator that counts what was actually set rather than what the
	// street asked for.
	{
		std::vector<LedgerSurface::Bound> All;
		LedgerSurface::Bound R1, R2, Absent;
		R1.Surface = "asphalt"; R1.Pieces = 2; R1.PiecesAssigned = 2;
		R1.MapFound[0] = true; R1.Status = "RESOLVED";
		R1.Read.bAsked = true; R1.Read.bScalarSame = true;
		R1.Read.bResourceValid = true; R1.Read.bCompIsMid = true;
		R1.Read.bTexSame = false;    // candidate B, as it would land
		R2 = R1; R2.Surface = "brick_red";
		Absent.Surface = "card"; Absent.Pieces = 10; Absent.Status = "ABSENT";
		All.push_back(R1); All.push_back(R2); All.push_back(Absent);
		std::vector<std::string> Tried;
		Tried.push_back("C:/staged/LedgerProbe/CityPackTextures");
		const std::string D = LedgerSurface::MaterialsDoneLine(
			All, "/Game/Ledger/M_LedgerSurface", true, "C:/pack/textures", 51, Tried,
			593, 2, 43, 2.0);
		std::printf("    %s\n", D.c_str());
		Check(D.find("midReadbackAsked=2/3") != std::string::npos,
		      "the readback denominator counts the surfaces a parameter was set on, "
		      "over the surfaces the street asked for");
		Check(D.find("midParamReadback=0/2") != std::string::npos
		      && D.find("midScalarReadback=2/2") != std::string::npos,
		      "the texture half and the scalar half are counted apart, which is "
		      "what separates candidate A from candidate B");
		Check(D.find("texResourceValid=2/2") != std::string::npos
		      && D.find("compMaterialIsMid=2/2") != std::string::npos,
		      "and the resource and component readings ship over the same denominator");
		Check(D.find("midReadbackStat=") != std::string::npos
		      && D.find("game-thread-copy-not-the-render-proxy") != std::string::npos,
		      "the line says what the number is a statistic OF, and what it cannot see");
		Check(NoSpacePastPrefix(D, "midReadbackAsked="),
		      "every readback total is one space-free token with one equals");
		// A RUN THAT SET NOTHING SAYS THE WORDS. `0/0` reads exactly like a
		// pass that ran and found nothing wrong.
		std::vector<LedgerSurface::Bound> NoneSet;
		NoneSet.push_back(Absent);
		const std::string N = LedgerSurface::MaterialsDoneLine(
			NoneSet, "/Game/Ledger/M_LedgerSurface", true, "", 0, Tried, 593, 0, 0, 2.0);
		Check(N.find("midParamReadback=nothing-measured") != std::string::npos
		      && N.find("midScalarReadback=nothing-measured") != std::string::npos,
		      "a pass that set no parameter prints the words rather than a clean zero");
		Check(N.find("midReadbackAsked=0/1") != std::string::npos,
		      "and the zero still ships the count of what was examined");
	}
	// ---- THE CONTROL QUADS, PLACED AGAINST THE COMMITTED CAMERA ---------
	//
	// THE ACCEPTING FIXTURE IS THE LIVE FILE, which is this project's rule
	// for a tool that checks the project itself: the quads are placed from
	// the camera the committed spec carries, so a camera moved in the file
	// moves them here and this test says whether they are still in frame.
	{
		const LedgerVignette::Camera* CamA = 0;
		for (size_t I = 0; I < S.Cameras.size(); ++I)
		{
			if (!S.Shots.empty() && S.Cameras[I].Id == S.Shots[0].CameraId)
			{
				CamA = &S.Cameras[I];
			}
		}
		if (CamA == 0)
		{
			std::printf("    control quads: nothing measured, the spec names no camera "
			            "for its first shot\n");
		}
		else
		{
			Check(LedgerSurface::ControlQuadCount() == 3,
			      "three controls: one for the texture path and a PAIR for the scalar path");
			int InFrame = 0, Ahead = 0;
			for (int I = 0; I < LedgerSurface::ControlQuadCount(); ++I)
			{
				const LedgerSurface::QuadPlace P = LedgerSurface::ControlQuadPlace(*CamA, I);
				const LedgerSurface::ScreenBox B =
					LedgerSurface::ControlQuadBox(*CamA, P, 1280, 720);
				std::printf("    quad %-6s at %.2f/%.2f/%.2f m  centre %.0f/%.0f px  "
				            "box x%.0f..%.0f y%.0f..%.0f  dist %.2f m  inFrame %d/4\n",
				            P.Id.c_str(), P.XM, P.YM, P.ZM, B.CxPx, B.CyPx,
				            B.X0, B.X1, B.Y0, B.Y1, B.DistM, B.CornersInFrame);
				if (B.CornersAhead == 4) { ++Ahead; }
				if (B.CornersInFrame == 4) { ++InFrame; }
			}
			Check(Ahead == LedgerSurface::ControlQuadCount(),
			      "every control stands in front of the camera, all four corners of it");
			Check(InFrame == LedgerSurface::ControlQuadCount(),
			      "and every corner of every control lands inside 1280x720, which is "
			      "the whole point of placing them from the camera's own numbers");
			// THE ROW IS TO THE LEFT, WHICH IS A DECISION ABOUT THE EVIDENCE
			// FRAME AND IS ASSERTED SO IT CANNOT DRIFT SILENTLY: the right of
			// cam_A's frame is the shopfront the street is read for.
			const LedgerSurface::QuadPlace P0 = LedgerSurface::ControlQuadPlace(*CamA, 0);
			const LedgerSurface::QuadPlace P2 = LedgerSurface::ControlQuadPlace(*CamA, 2);
			const LedgerSurface::ScreenBox B0 =
				LedgerSurface::ControlQuadBox(*CamA, P0, 1280, 720);
			const LedgerSurface::ScreenBox B2 =
				LedgerSurface::ControlQuadBox(*CamA, P2, 1280, 720);
			Check(B0.CxPx < 640.0 && B2.CxPx < B0.CxPx,
			      "the controls sit left of centre and in the order they are numbered");
			Check(LedgerSurface::ControlQuadTiling(1) != LedgerSurface::ControlQuadTiling(2)
			      && LedgerSurface::ControlQuadPlace(*CamA, 1).SizeM
			         == LedgerSurface::ControlQuadPlace(*CamA, 2).SizeM,
			      "the two tile quads differ in their tiling and in NOTHING else, "
			      "which is what makes the pair readable in one still");
			Check(LedgerSurface::ControlQuadBindsTexture(0)
			      && !LedgerSurface::ControlQuadBindsTexture(1)
			      && !LedgerSurface::ControlQuadBindsTexture(2),
			      "exactly one control binds a texture, so the checker on the other "
			      "two is the base material's own default and not an accident");
			// THE ROTATION IS DERIVED FROM THE CAMERA, and a quad facing away
			// is culled or lit from behind, which is the sign error the decal
			// quads paid for once already.
			Check(P0.EnginePitchDeg == 90.0 && P0.EngineYawDeg == CamA->YawDeg,
			      "the plane is pitched a quarter turn so its normal faces the camera, "
			      "and it carries the camera's yaw so it does at any yaw");
			// AND THE FOUR COLOURS, WHICH ARE THE WHOLE READING.
			int MinChroma = 255;
			for (int I = 0; I < LedgerSurface::ControlColourCount(); ++I)
			{
				int R = 0, G = 0, B = 0;
				LedgerSurface::ControlColour(I, R, G, B);
				const int Hi = (R > G ? (R > B ? R : B) : (G > B ? G : B));
				const int Lo = (R < G ? (R < B ? R : B) : (G < B ? G : B));
				if (Hi - Lo < MinChroma) { MinChroma = Hi - Lo; }
			}
			Check(MinChroma == 255,
			      "every control colour is at a corner of the cube, so none of them "
			      "can be confused with a frame whose measured maximum chroma is 15");
			// ONE QUAD'S LINE, BOTH WAYS ROUND THE TRANSFORM READBACK.
			LedgerSurface::QuadResult R;
			R.bSpawned = true; R.bMidMade = true; R.bTexMade = true;
			R.bTexResource = true; R.bTexReadback = true; R.bCompIsMid = true;
			R.bRead = true;
			R.ReadXCm = P0.XCm; R.ReadYCm = P0.YCm; R.ReadZCm = P0.ZCm;
			const std::string QL = LedgerSurface::ControlQuadLine(*CamA, P0, R, 1280, 720);
			std::printf("    %s\n", QL.c_str());
			Check(QL.find("controlQuad=colour") == 0,
			      "the control line names itself first, as the surface lines do");
			Check(QL.find("quadTexels=texel0.red.255.0.0/texel1.green.0.255.0/"
			              "texel2.blue.0.0.255/texel3.yellow.255.255.0") != std::string::npos,
			      "the line carries the four colours ASKED FOR, in the order the "
			      "memcpy writes them, so the still can be read against it");
			Check(QL.find("quadDeltaCm=0.00") != std::string::npos,
			      "a quad that landed where it was asked to prints a zero delta");
			Check(QL.find("quadCentrePx=") != std::string::npos
			      && QL.find("quadBoxPx=x") != std::string::npos,
			      "and it says WHERE ON SCREEN to look, in pixels, not in prose");
			Check(NoSpacePastPrefix(QL, "quadStatus="),
			      "every value on a control line is one space-free token with one equals");
			LedgerSurface::QuadResult NoRead = R;
			NoRead.bRead = false;
			const std::string QN = LedgerSurface::ControlQuadLine(*CamA, P0, NoRead, 1280, 720);
			Check(QN.find("quadReadXYZcm=not-read") != std::string::npos
			      && QN.find("quadDeltaCm=not-read") != std::string::npos,
			      "an actor that never answered for its transform says so rather than "
			      "printing the request back as though it were a reading");
			// THE PASS'S OWN DONE LINE, both ways round the empty case.
			std::vector<LedgerSurface::QuadResult> Quads;
			const std::string Empty = LedgerSurface::ControlQuadsDoneLine(Quads, true);
			Check(Empty.find("controlQuadsStatus=NOT-REACHED") != std::string::npos
			      && Empty.find("controlQuads=nothing-measured/3") != std::string::npos,
			      "a control pass that spawned nothing says the words and still ships "
			      "the count of what it was asked for");
			Quads.push_back(R); Quads.push_back(R); Quads.push_back(R);
			const std::string Done = LedgerSurface::ControlQuadsDoneLine(Quads, true);
			std::printf("    %s\n", Done.c_str());
			Check(Done.find("controlQuadsStatus=ALL") != std::string::npos
			      && Done.find("controlQuads=3/3") != std::string::npos
			      && Done.find("controlQuadMids=3/3") != std::string::npos,
			      "a control pass that made all three prints all three with denominators");
			Check(NoSpacePastPrefix(Done, "controlQuadsStatus="),
			      "and the done line is space-free past its first key");
		}
	}
	// ---- cam_hook, RUNG 1 OF production/ladder.md ------------------------
	//
	// THE VIEWPOINT OF THE LOWER PANEL of the Hook concept sheet, checked
	// against the panel's own MEASURED composition rather than against a
	// number anybody liked the look of. The three panel numbers quoted below
	// were read off the file at production/art/atlas-01/concepts/hook.png on
	// branch origin/art/atlas-01, whose street panel is 1002 by 617 pixels:
	// the horizon at row 348 (0.5640 of the height), the street axis
	// vanishing at column 332 (0.3313 of the width), and the nearest ground
	// at the bottom edge 4.15 m ahead. They are the reference, so a check
	// against them is a check against a measurement.
	//
	// AND THE HALF NOBODY WOULD THINK TO ASK FOR: the three material control
	// quads are placed 3.5 m in front of the FIRST shot's camera, which is
	// cam_A and not this one, so nothing in their placement knows this
	// camera exists. A frame with colour swatches standing in the road is
	// not a frame anybody can judge a street by, so where they land in THIS
	// camera's frame is measured here rather than discovered in the still.
	{
		const LedgerVignette::Camera* Hook = 0;
		// AND THE CAMERA THE QUADS ARE PLACED FROM, looked up again here
		// rather than borrowed from the block above, because it is the FIRST
		// SHOT'S camera by definition and this block must keep saying so even
		// if the shot order changes.
		const LedgerVignette::Camera* QuadCam = 0;
		for (size_t I = 0; I < S.Cameras.size(); ++I)
		{
			if (S.Cameras[I].Id == "cam_hook") { Hook = &S.Cameras[I]; }
			if (!S.Shots.empty() && S.Cameras[I].Id == S.Shots[0].CameraId)
			{
				QuadCam = &S.Cameras[I];
			}
		}
		if (Hook == 0 || QuadCam == 0)
		{
			std::printf("    cam_hook: nothing measured, the committed spec carries no "
			            "camera of that id or no camera for its first shot\n");
		}
		else
		{
			std::printf("    cam_hook at x=%.2f z=%.2f groundY=%.4f (%s) eye=%.2f "
			            "yaw=%.1f pitch=%.1f vfov=%.1f hfov=%.2f\n",
			            Hook->X, Hook->Z, Hook->GroundY, Hook->GroundEdge.c_str(),
			            Hook->EyeHeightM, Hook->YawDeg, Hook->PitchDeg,
			            Hook->FovVerticalDeg,
			            LedgerVignette::HorizontalFovDeg(Hook->FovVerticalDeg, 1280, 720));
			// THE CAMERA STANDS IN THE CARRIAGEWAY, which is half of what
			// "in the road near the left kerb" means and the half a position
			// alone cannot say: the emitter resolved the ground under it.
			Check(Hook->GroundFound && Hook->GroundEdge == "west_carriageway",
			      "cam_hook stands on the west carriageway, as the panel's camera "
			      "stands in the road and not on the pavement",
			      Hook->GroundEdge);
			Check(Hook->Z > -3.0 + 0.255 && Hook->Z < -0.5,
			      "and it is between the west channel and the crown, which is the "
			      "near-kerb half of the carriageway rather than the middle of it");
			// THE HORIZON AND THE VANISHING POINT, against the panel's own
			// rows and columns. The tolerance is one percent of the frame,
			// which is 7 rows of 720, and both numbers are printed.
			const LedgerSurface::ScreenAt Hor = LedgerSurface::ProjectFilePoint(
				*Hook, Hook->X + 2000.0, Hook->GroundY + Hook->EyeHeightM, Hook->Z,
				1280, 720);
			const LedgerSurface::ScreenAt Van = LedgerSurface::ProjectFilePoint(
				*Hook, Hook->X + 2000.0, Hook->GroundY, Hook->Z, 1280, 720);
			const double HorFrac = Hor.Py / 720.0;
			const double VanFrac = Van.Px / 1280.0;
			std::printf("    cam_hook horizonRowFrac=%.4f panel=0.5640 "
			            "vanishColFrac=%.4f panel=0.3313\n", HorFrac, VanFrac);
			Check(Hor.bAhead && HorFrac > 0.5,
			      "the horizon sits BELOW the middle of the frame, as the panel's "
			      "does, which is what a camera tilted slightly up looks like");
			Check(std::fabs(HorFrac - 0.5640) < 0.01,
			      "and it lands within one percent of the frame height of the row "
			      "measured off the panel");
			Check(Van.bAhead && VanFrac < 0.5,
			      "the street axis vanishes LEFT of centre, as the panel's does, "
			      "which for a pinhole camera can only be a rotation");
			// WHERE THE THREE CONTROL QUADS LAND IN THIS FRAME. Their centres
			// and their two lateral extremes, because a centre just outside
			// the edge with 0.35 m of quad beside it is still in the picture.
			int CentresIn = 0, EdgesIn = 0, Ahead4 = 0;
			for (int I = 0; I < LedgerSurface::ControlQuadCount(); ++I)
			{
				const LedgerSurface::QuadPlace P =
					LedgerSurface::ControlQuadPlace(*QuadCam, I);
				// The quad faces the camera it was placed from, so its own
				// width runs along THAT camera's right vector and not along
				// this one's.
				const double CamAYaw = LedgerSurface::DegToRad(QuadCam->YawDeg);
				const double Rx = -std::sin(CamAYaw), Rz = std::cos(CamAYaw);
				const double Half = LedgerSurface::ControlQuadSizeM() * 0.5;
				const LedgerSurface::ScreenAt C0 = LedgerSurface::ProjectFilePoint(
					*Hook, P.XM, P.YM, P.ZM, 1280, 720);
				const LedgerSurface::ScreenAt L = LedgerSurface::ProjectFilePoint(
					*Hook, P.XM - Rx * Half, P.YM, P.ZM - Rz * Half, 1280, 720);
				const LedgerSurface::ScreenAt R2 = LedgerSurface::ProjectFilePoint(
					*Hook, P.XM + Rx * Half, P.YM, P.ZM + Rz * Half, 1280, 720);
				const bool CIn = C0.bAhead && C0.Px >= 0 && C0.Px <= 1280
				                 && C0.Py >= 0 && C0.Py <= 720;
				const bool EIn = (L.bAhead && L.Px >= 0 && L.Px <= 1280
				                  && L.Py >= 0 && L.Py <= 720)
				                 || (R2.bAhead && R2.Px >= 0 && R2.Px <= 1280
				                     && R2.Py >= 0 && R2.Py <= 720);
				if (C0.bAhead && L.bAhead && R2.bAhead) { ++Ahead4; }
				if (CIn) { ++CentresIn; }
				if (EIn) { ++EdgesIn; }
				std::printf("    quad %-6s seen from cam_hook: centre %.0f/%.0f px "
				            "edges %.0f..%.0f px fwd %.2f m inFrameCentre=%s "
				            "inFrameEitherEdge=%s\n",
				            P.Id.c_str(), C0.Px, C0.Py, L.Px, R2.Px, C0.ForwardM,
				            CIn ? "yes" : "no", EIn ? "yes" : "no");
			}
			std::printf("    cam_hook controlQuadsInFrame centres=%d/%d "
			            "eitherEdge=%d/%d ahead=%d/%d\n",
			            CentresIn, LedgerSurface::ControlQuadCount(),
			            EdgesIn, LedgerSurface::ControlQuadCount(),
			            Ahead4, LedgerSurface::ControlQuadCount());
			// AND THE RULE THAT KEEPS THEM OUT OF THE JUDGED FRAME, both
			// outcomes watched and the ACCEPTING one first: the camera the
			// quads were placed from still sees them, and every other camera
			// does not. The measurement above is why the rule exists, and it
			// is printed whatever the rule says, so a future placement that
			// stops intruding shows up as a reading rather than as silence.
			Check(LedgerSurface::ControlQuadsVisibleFor(QuadCam->Id, QuadCam->Id),
			      "the camera the controls were placed from still photographs them, "
			      "which is the frame the material evidence is read from");
			Check(!LedgerSurface::ControlQuadsVisibleFor(Hook->Id, QuadCam->Id),
			      "and cam_hook does not, which is what stops an instrument standing "
			      "in the picture rung 1 is judged by");
			Check(!LedgerSurface::ControlQuadsVisibleFor("", QuadCam->Id)
			      && !LedgerSurface::ControlQuadsVisibleFor(QuadCam->Id, ""),
			      "an unnamed camera on either side hides them rather than guessing");
			std::printf("    cam_hook controlQuadIntrusion=%s "
			            "(this is WHY the rule above exists, and it is measured "
			            "rather than assumed)\n",
			            EdgesIn == 0 ? "none-reaches-the-frame"
			                         : "at-least-one-quad-reaches-the-frame");
			const std::string VLine =
				LedgerSurface::ControlQuadVisibilityLine(5, 1, "vign_hook_day");
			std::printf("    %s\n", VLine.c_str());
			Check(VLine.find("controlQuadHidden=1/5") != std::string::npos
			      && VLine.find("controlQuadHiddenOn=vign_hook_day") != std::string::npos,
			      "the visibility line carries the count, its denominator and the ids");
			Check(LedgerSurface::ControlQuadVisibilityLine(0, 0, "").find(
			          "nothing-measured") != std::string::npos,
			      "a run that took no shot says nothing measured rather than zero");
		}
	}
	// THE SEARCH-PATH FORMATTER ON ITS OWN, both ways round the cap, because
	// a cap that is never exercised is a claim rather than a measurement.
	{
		std::vector<std::string> P;
		Check(LedgerSurface::PathListValue(P, 8) == "nothing-tried",
		      "a search that asked about no directory at all says the words, not empty");
		P.push_back("D:/a/one two/CityPackTextures");
		Check(LedgerSurface::PathListValue(P, 8) == "D:/a/one~two/CityPackTextures",
		      "a path with a space in it cannot split a key=value reader's line");
		P.push_back("D:/b/CityPackTextures");
		Check(LedgerSurface::PathListValue(P, 8)
		      == "D:/a/one~two/CityPackTextures,D:/b/CityPackTextures",
		      "two candidates join on a comma, because a slash is inside every path");
		Check(LedgerSurface::PathListValue(P, 8).find("more-not-shown") == std::string::npos,
		      "and a cap that did not bite says nothing at all");
		Check(LedgerSurface::PathListValue(P, 1)
		      == "D:/a/one~two/CityPackTextures,+1-more-not-shown",
		      "a cap that BITES announces itself and prints how many it withheld");
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
