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
#include <cstdlib>
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
	// THREE CAMERAS, FIVE JUDGED SHOTS AND TWENTY PROBE ROWS, AND THE SPLIT
	// IS NAMED RATHER THAN SUMMED.
	//
	// cam_A and cam_B by the two conditions are the FOUR MATCHED PAIRS the
	// engine decision is judged on, cam_hook under overcast_day is a fifth
	// judged shot that is deliberately not part of that pairing, and the
	// twenty rows this batch adds are ONE-RUN PROBE ROWS that the item
	// reading the run removes. A bare 25 would read as the pairing having
	// changed, so the three groups are counted apart.
	//
	// THE LADDER IS GONE, 2026-09-09, section 9 of the grid ruling, and its
	// series is preserved in section 3 of that record: five rungs across a
	// HUNDREDFOLD of sun moved band.ground.p05 by 1.06 of the null measured
	// between two shots of one condition.
	{
		int Matched = 0, ProbeShots = 0, ProbeAtHook = 0, JudgedAtHook = 0;
		for (size_t I = 0; I < S.Shots.size(); ++I)
		{
			const bool bJudged = (S.Shots[I].ConditionId == "overcast_day"
			                      || S.Shots[I].ConditionId == "wet_night");
			if (!bJudged)
			{
				++ProbeShots;
				if (S.Shots[I].CameraId == "cam_hook") { ++ProbeAtHook; }
			}
			else if (S.Shots[I].CameraId == "cam_A" || S.Shots[I].CameraId == "cam_B")
			{
				++Matched;
			}
			else if (S.Shots[I].CameraId == "cam_hook")
			{
				++JudgedAtHook;
			}
		}
		int JudgedConds = 0, ProbeConds = 0;
		for (size_t I = 0; I < S.Conditions.size(); ++I)
		{
			if (S.Conditions[I].Id == "overcast_day" || S.Conditions[I].Id == "wet_night")
			{
				++JudgedConds;
			}
			else { ++ProbeConds; }
		}
		std::printf("    rows: cameras=%d judgedConds=%d probeConds=%d shots=%d "
		            "matchedPairs=%d probeShots=%d probeAtHook=%d judgedAtHook=%d\n",
		            (int)S.Cameras.size(), JudgedConds, ProbeConds, (int)S.Shots.size(),
		            Matched, ProbeShots, ProbeAtHook, JudgedAtHook);
		// THE TOTAL IS READ AND NOT PINNED, QUEUE 235. Rows are added to this
		// file by the item that needs them and removed by the item that reads
		// them, so a literal total is a check that fails for the wrong reason
		// every time the file legitimately grows. WHAT MUST STAY TRUE is the
		// pairing and the classification: three cameras, two judged
		// conditions, the four judged pairs still exactly four, and every
		// shot falling into exactly one of the classes counted below, which
		// is the identity a bare total cannot state.
		Check(S.Cameras.size() == 3 && JudgedConds == 2 && Matched == 4,
		      "three cameras, two judged conditions, and the four judged pairs are still "
		      "exactly four whatever else the file has grown");
		Check((int)S.Shots.size() == Matched + ProbeShots + JudgedAtHook
		      && JudgedAtHook > 0,
		      "every shot in the file is one of the four judged pairs, a probe row, or a "
		      "judged row at the hook camera, and the classes sum to the total read",
		      "a shot in none of them is a row nothing in this test describes");
		// EVERY PROBE ROW STANDS AT cam_hook, and that is an instrument
		// repair as much as it is Jafar's judging camera: the three control
		// quads are HIDDEN on this camera (controlQuadHidden named
		// vign_hook_day on run 38), so no whole-frame key on a probe row
		// photographs the instrument, and at fovV 39.0 band.skyCentre is sky
		// rather than the rooftops it holds at fovV 60.0.
		// THE INVARIANT, NOT THE COUNT. The number of probe rows moves with
		// the file; the thing that must never move is that ALL of them stand
		// at one camera, because a group spanning two cameras is two pixel
		// populations read as one, which is the fault the batch review caught
		// in a group of nine. Queue 235's twelve exposure rows are at cam_hook
		// for exactly this reason, including the night rows that give the
		// after-night half of each rung its darkness.
		Check(ProbeShots > 0 && ProbeAtHook == ProbeShots,
		      "every probe row stands at cam_hook, the camera rung 1 is judged from",
		      "a probe row at another camera would be two pixel populations read as one");
		// THE NULL CELL IS SHOT LAST. Identical inputs at maximum order
		// separation is the whole of its value.
		Check(!S.Shots.empty() && S.Shots[S.Shots.size() - 1].ConditionId == "grid_null_repeat",
		      "the null cell is the last shot in the list, as far from its twin as the run allows",
		      S.Shots.empty() ? std::string("no shots") : S.Shots[S.Shots.size() - 1].Id);
	}

	// ---- A1: THE GRID, ITS NULL CELL, AND THE TWO PROBE SERIES ----------
	//
	// PRINTED BEFORE IT IS ASSERTED, because this is the series the next
	// commit sets constants from and rule 2 says the printer ships first.
	{
		std::printf("    grid:");
		for (size_t I = 0; I < S.Conditions.size(); ++I)
		{
			std::printf(" %s=sun%.2f/sky%.2f/wet%.2f/fogMaxOp%.3f",
			            S.Conditions[I].Id.c_str(), S.Conditions[I].SunIntensity,
			            S.Conditions[I].SkyIntensity, S.Conditions[I].Wetness,
			            S.Conditions[I].FogMaxOpacity);
		}
		std::printf("\n");
		double DaySun = -1.0, DaySky = -1.0, DayCap = -1.0;
		double NightSun = -1.0, NightSky = -1.0;
		for (size_t I = 0; I < S.Conditions.size(); ++I)
		{
			const LedgerVignette::Condition& C = S.Conditions[I];
			if (C.Id == "overcast_day")
			{
				DaySun = C.SunIntensity; DaySky = C.SkyIntensity; DayCap = C.FogMaxOpacity;
			}
			if (C.Id == "wet_night") { NightSun = C.SunIntensity; NightSky = C.SkyIntensity; }
		}
		// THE TWO JUDGED ROWS CARRY THE OLD LITERALS UNCHANGED, which is what
		// makes "the field replaced the literal and moved no number" a check
		// rather than a claim. 3.0f was the bare literal at
		// VignetteShot.cpp:1240; 1.0 and 0.35 were kSkyIntensityDay and
		// kSkyIntensityNight; 0.45f was kFogMaxOpacityWithSky.
		Check(std::fabs(DaySun - 3.0) < 1e-9 && std::fabs(DaySky - 1.0) < 1e-9,
		      "the day condition carries the retired sun literal and day sky constant unchanged");
		Check(std::fabs(NightSun) < 1e-9 && std::fabs(NightSky - 0.35) < 1e-9,
		      "the night condition carries the night sky constant with its sun at zero");
		Check(std::fabs(DayCap - 0.450) < 1e-9,
		      "and the retired fog cap literal, 0.45, unchanged on the judged day row");
		// THE GRID IS THE CROSS AND NOTHING ELSE, counted out of the file.
		const double Skies[4] = { 1.00, 0.70, 0.50, 0.35 };
		const double Suns[3]  = { 3.0, 10.0, 30.0 };
		int Cells = 0, GridRows = 0;
		for (int A = 0; A < 4; ++A)
		{
			for (int B = 0; B < 3; ++B)
			{
				for (size_t I = 0; I < S.Conditions.size(); ++I)
				{
					const LedgerVignette::Condition& C = S.Conditions[I];
					if (C.Id.compare(0, 8, "grid_sky") != 0) { continue; }
					if (std::fabs(C.SkyIntensity - Skies[A]) < 1e-9
					    && std::fabs(C.SunIntensity - Suns[B]) < 1e-9) { ++Cells; break; }
				}
			}
		}
		for (size_t I = 0; I < S.Conditions.size(); ++I)
		{
			if (S.Conditions[I].Id.compare(0, 8, "grid_sky") == 0) { ++GridRows; }
		}
		Check(Cells == 12 && GridRows == 12,
		      "the grid is four skies crossed with three suns, twelve cells, none missing and none extra",
		      std::to_string(Cells) + " of 12 cells over " + std::to_string(GridRows) + " rows");
		// A1(a), BLOCKING: THE NULL CELL IS A DUPLICATE OR IT IS NOTHING.
		// Run 38 carried this test as ladder_sun003 against vign_camA_day and
		// IT FAILED, by 0.1106 of whole-frame mean luma, and nobody read it.
		// Asserted field by field here rather than by reading two rows of
		// JSON side by side.
		const LedgerVignette::Condition* Ref = 0;
		const LedgerVignette::Condition* Null = 0;
		for (size_t I = 0; I < S.Conditions.size(); ++I)
		{
			if (S.Conditions[I].Id == "grid_sky100_sun003") { Ref = &S.Conditions[I]; }
			if (S.Conditions[I].Id == "grid_null_repeat")    { Null = &S.Conditions[I]; }
		}
		Check(Ref != 0 && Null != 0,
		      "the grid has a reference cell and a null cell that repeats it");
		Check(Ref != 0 && Null != 0
		      && Null->Hdri == Ref->Hdri && Null->SunOn == Ref->SunOn
		      && Null->LanternsOn == Ref->LanternsOn && Null->WindowsOn == Ref->WindowsOn
		      && std::fabs(Null->SunIntensity - Ref->SunIntensity) < 1e-12
		      && std::fabs(Null->SkyIntensity - Ref->SkyIntensity) < 1e-12
		      && std::fabs(Null->Wetness - Ref->Wetness) < 1e-12
		      && std::fabs(Null->FogDensity - Ref->FogDensity) < 1e-12
		      && std::fabs(Null->FogMaxOpacity - Ref->FogMaxOpacity) < 1e-12,
		      "the null cell is the reference cell in every field that lights a frame",
		      "a null pair that differs in any input measures that difference and not the rig");
		// C6, MECHANICALLY: THE SHOT ORDER RISES AND FALLS IN SKY. The
		// retired ladder rendered in increasing order, so a drift ordered by
		// shot was perfectly confounded with a response to the light.
		bool bRose = false, bFell = false;
		double PrevSky = -1.0;
		std::printf("    gridShotOrder:");
		for (size_t I = 0; I < S.Shots.size(); ++I)
		{
			if (S.Shots[I].ConditionId.compare(0, 8, "grid_sky") != 0) { continue; }
			double Sky = -1.0;
			for (size_t K = 0; K < S.Conditions.size(); ++K)
			{
				if (S.Conditions[K].Id == S.Shots[I].ConditionId)
				{
					Sky = S.Conditions[K].SkyIntensity;
				}
			}
			std::printf(" sky%.2f", Sky);
			if (PrevSky >= 0.0 && Sky > PrevSky + 1e-12) { bRose = true; }
			if (PrevSky >= 0.0 && Sky < PrevSky - 1e-12) { bFell = true; }
			PrevSky = Sky;
		}
		std::printf("\n");
		Check(bRose && bFell,
		      "the grid's shot order rises and falls in sky, so no drift ordered by shot passes as a sky response",
		      "rose and fell are both required, which is condition C6");
		// A4, THE FOG SERIES, AND A3, THE WETNESS SERIES.
		const double WantFog[4] = { 0.450, 0.250, 0.100, 0.000 };
		int FogRows = 0;
		for (int A = 0; A < 4; ++A)
		{
			for (size_t I = 0; I < S.Conditions.size(); ++I)
			{
				if (S.Conditions[I].Id.compare(0, 9, "fog_maxop") != 0) { continue; }
				if (std::fabs(S.Conditions[I].FogMaxOpacity - WantFog[A]) < 1e-9)
				{
					++FogRows; break;
				}
			}
		}
		Check(FogRows == 4,
		      "four fog rows at 0.450, 0.250, 0.100 and 0.000, which is a series and not a pair",
		      std::to_string(FogRows) + " of 4");
		const double WantWet[3] = { 0.0, 0.60, 1.0 };
		int WetRows = 0;
		for (int A = 0; A < 3; ++A)
		{
			for (size_t I = 0; I < S.Conditions.size(); ++I)
			{
				if (S.Conditions[I].Id.compare(0, 4, "wet_") != 0) { continue; }
				if (std::fabs(S.Conditions[I].Wetness - WantWet[A]) < 1e-9) { ++WetRows; break; }
			}
		}
		Check(WetRows == 3,
		      "three wetness rows at 0.0, 0.60 and 1.0, both ends and the value the judged rows carry",
		      std::to_string(WetRows) + " of 3");
	}

	// REJECTING CASE, SYNTHESISED FROM THE LIVE FILE BY DELETING ONE KEY,
	// so the fixture cannot drift from the accepting case above. A
	// condition with no sun_intensity must stop the parse and NAME the
	// key: a silent default is the fault queue 205 repairs, and the value
	// it would fall back on was tuned against three fills that no longer
	// exist.
	{
		const std::string Key = "\"sun_intensity\":";
		const size_t At = Text.find(Key);
		Check(At != std::string::npos,
		      "the committed piece list carries sun_intensity at all, so the deletion below bites");
		if (At != std::string::npos)
		{
			size_t End = Text.find(',', At);
			std::string Broken = Text;
			if (End != std::string::npos) { Broken.erase(At, End - At + 1); }
			LedgerVignette::Spec B;
			std::string BErr;
			const bool BParsed = LedgerVignette::ParseSpec(Broken, B, BErr);
			std::printf("    rejecting: parsed=%s err=%s\n",
			            BParsed ? "yes" : "no", BErr.c_str());
			Check(!BParsed && BErr.find("sun_intensity") != std::string::npos,
			      "REJECTING CASE - a condition with no sun_intensity refuses and names the key",
			      BErr.empty() ? "(no error raised)" : BErr);
		}
	}

	// AND THE SAME RUNG FOR sky_intensity, BECAUSE A REQUIRED FIELD NOT
	// PROVEN REQUIRED IS A DEFAULTED FIELD. The parse calls NeedNum on
	// both, and only one of the two had a rejecting case until this rung.
	//
	// CUT FROM THE COMMA BEFORE IT, NOT TO THE COMMA AFTER IT, and the
	// difference decides what this proves: sky_intensity is the LAST key
	// of its object, so a cut forward to the next comma would take the
	// closing brace with it and the parse would then refuse the SHAPE
	// rather than the missing key. The check below would still pass and
	// would be about the wrong thing.
	{
		const std::string Key = "\"sky_intensity\":";
		const size_t At = Text.find(Key);
		Check(At != std::string::npos,
		      "the committed piece list carries sky_intensity at all, so the deletion below bites");
		if (At != std::string::npos)
		{
			const size_t Cut = Text.rfind(',', At);
			const size_t End = Text.find_first_of(",}", At);
			std::string Broken = Text;
			if (Cut != std::string::npos && End != std::string::npos && End > Cut)
			{
				Broken.erase(Cut, End - Cut);
			}
			Check(Broken.size() < Text.size(),
			      "the sky_intensity fixture actually removed something, so the check below is not vacuous");
			LedgerVignette::Spec B;
			std::string BErr;
			const bool BParsed = LedgerVignette::ParseSpec(Broken, B, BErr);
			std::printf("    rejecting: parsed=%s err=%s\n",
			            BParsed ? "yes" : "no", BErr.c_str());
			Check(!BParsed && BErr.find("sky_intensity") != std::string::npos,
			      "REJECTING CASE - a condition with no sky_intensity refuses and names the key",
			      BErr.empty() ? "(no error raised)" : BErr);
		}
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
		// THE NUMBER COMES OFF THE FILE, NOT OUT OF THIS LINE, repaired
		// 2026-09-10. It read propFootprintsRead=23/23 as a literal, and the
		// fascia package took the street to 40 mesh pieces, so a correct
		// layout change turned this check red while the thing it asserts held
		// perfectly. WHAT IT ASSERTS IS A RELATION AND NOT A COUNT, and its
		// own message says so: the count EXAMINED over the count the FILE
		// ASKED FOR, equal, with the denominator being the file's and not a
		// number typed here. So the expected string is built from the live
		// spec's own mesh-piece count. A zero is refused separately, because
		// propFootprintsRead=0/0 satisfies the equality and would mean the
		// burial half measured nothing at all.
		int MeshPiecesHere = 0;
		for (size_t I = 0; I < S.Pieces.size(); ++I)
		{
			if (S.Pieces[I].Shape == "mesh") { ++MeshPiecesHere; }
		}
		char WantFootprints[64];
		std::snprintf(WantFootprints, sizeof(WantFootprints),
		              "propFootprintsRead=%d/%d", MeshPiecesHere, MeshPiecesHere);
		Check(MeshPiecesHere > 0,
		      "the committed street asks for at least one mesh piece, so the burial "
		      "half has a population to examine at all", WantFootprints);
		Check(LiveSeg.find(WantFootprints) != std::string::npos,
		      "the burial half ships the count it examined over the count the file "
		      "asked for", std::string(WantFootprints) + " | " + LiveSeg);
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
		//
		// THE FIXTURE READS THE LIVE COUNT, 2026-09-09, AND NO LONGER PINS
		// ONE. It carried the literal `"pieces":593` and went red the first
		// time the street legitimately grew, which is a fixture failing for
		// the one reason a fixture must not: the work moved the number it was
		// typed against. The count comes out of the header this run just
		// parsed, so the planted fault is a DECREMENT OF WHATEVER IS THERE
		// and the fixture cannot decay. It still says nothing-measured rather
		// than passing if the key is absent.
		LedgerVignette::Spec Bad;
		std::string BadErr;
		std::string Miscount(Text);
		const std::string Key = "\"pieces\":" + std::to_string(S.HeaderPieces);
		const size_t At = Miscount.find(Key);
		if (At != std::string::npos)
		{
			const std::string Wrong = "\"pieces\":" + std::to_string(S.HeaderPieces - 2);
			Miscount.replace(At, Key.size(), Wrong);
			std::printf("    miscountFixture: planted %s in place of %s\n",
			            Wrong.c_str(), Key.c_str());
			Check(!LedgerVignette::ParseSpec(Miscount, Bad, BadErr),
			      "a header that claims fewer pieces than are under it is refused", BadErr);
		}
		else
		{
			// NOTHING MEASURED rather than a pass: the fixture planted no
			// fault, so the check it stands for did not run.
			Check(false, "the miscount fixture could not be planted",
			      "nothing measured: the header key " + Key
			      + " is not in the committed file in that form");
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

		// THE REJECTING FIXTURE IS SYNTHETIC, and it changed on 10 September
		// with queue 223. It used to be `card`, which made this check assert
		// the exact thing that item found wrong: card is a decal BLEND MODE
		// and not a library surface, so card.png is a file that by design can
		// never exist and three candidate filenames beside it were three
		// filenames nobody should ever have gone looking for. A surface name
		// that exists nowhere is the honest way to watch the absent case.
		LedgerSurface::Bound A;
		A.Surface = "brick_blue"; A.Pieces = 10; A.Status = "ABSENT";
		A.Reason = "no-file-in-citypack-textures/the-unity-host-generates-this-one-procedurally";
		const std::string AL = LedgerSurface::SurfaceLine(A);
		std::printf("    %s\n", AL.c_str());
		Check(AL.find("surfaceStatus=ABSENT") != std::string::npos
		      && AL.find("albedoTried=brick_blue.png/brick_blue.jpg/brick_blue.jpeg")
		         != std::string::npos
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
	// ---- QUEUE 223: EVERY PIECE TAKES EXACTLY ONE PAINT ROUTE -----------
	//
	// THE ACCEPTING FIXTURE IS THE LIVE STREET, which is this project's rule
	// for a check on the project itself. The census below is taken off the
	// committed piece list with the pack ASSUMED PRESENT for the twelve
	// surfaces that carry a file, so it answers the question the item is
	// about: how many pieces the old `continue` left with no material at all.
	{
		int Pack = 0, Tint = 0, Card = 0, Multiply = 0, None = 0;
		for (size_t I = 0; I < S.Pieces.size(); ++I)
		{
			const LedgerVignette::Piece& P = S.Pieces[I];
			// THE TWELVE THAT RESOLVE ARE THE ONES THAT ARE NEITHER A BLEND
			// NOR IN THE PROCEDURAL TABLE, which is what the run itself
			// measured: surfacesResolved=12/16 with card, interior, multiply
			// and paint_yellow absent.
			const bool bPackAnswered =
				!LedgerSurface::IsDecalBlend(P.Surface)
				&& LedgerSurface::ProceduralSurfaceIndex(P.Surface) < 0;
			switch (LedgerSurface::RouteFor(P.Surface, P.Shape == "decal", bPackAnswered))
			{
			case LedgerSurface::Paint_Pack:          ++Pack; break;
			case LedgerSurface::Paint_Tint:          ++Tint; break;
			case LedgerSurface::Paint_DecalCard:     ++Card; break;
			case LedgerSurface::Paint_DecalMultiply: ++Multiply; break;
			default:                                 ++None; break;
			}
		}
		std::printf("    paint routes over the live street: pack=%d tint=%d "
		            "card=%d multiply=%d none=%d of %d piece(s)\n",
		            Pack, Tint, Card, Multiply, None, (int)S.Pieces.size());
		Check(Pack + Tint + Card + Multiply + None == (int)S.Pieces.size(),
		      "every piece in the file takes exactly one route and none takes two");
		Check(None == 0,
		      "no piece in the committed street is left with no rule to paint it, "
		      "which is the whole of queue 223");
		Check(Tint == 10,
		      "the tint route covers the six interiors and the four yellow bands");
		Check(Card == 10 && Multiply == 10,
		      "the twenty decals split ten opaque cards and ten stains");
		// AND THE REJECTING CASE, PLANTED: a library surface the pack does not
		// answer for still has no route, because inventing one would be
		// painting over the gate.
		Check(LedgerSurface::RouteFor("brick_blue", false, false)
		      == LedgerSurface::Paint_None,
		      "a library surface with no pack file is NOT painted by a made-up rule");
		Check(LedgerSurface::RouteFor("brick_blue", false, true)
		      == LedgerSurface::Paint_Pack,
		      "and the same surface with a file takes the pack route");
		// ProceduralOnly OUTRANKS A PACK FILE, which is the one thing that
		// stops a paint_yellow.jpg dropped into the pack from making the two
		// engines render one surface from two different inputs.
		Check(LedgerSurface::RouteFor("paint_yellow", false, true)
		      == LedgerSurface::Paint_Tint,
		      "paint_yellow renders from the tint even when a pack file exists");
	}
	// THE TINT ITSELF, WHICH IS A NUMBER THIS FILE CAN CHECK AND THE ENGINE
	// CANNOT. Both grades, the byte quantisation and the two colour space
	// conversions, asserted against values computed by hand from the Unity
	// literals.
	{
		Check(LedgerSurface::ProceduralSurfaceCount() == 2,
		      "two surfaces are painted from the tint, and they are named");
		Check(std::string(LedgerSurface::ProceduralSurfaceName(0)) == "interior"
		      && std::string(LedgerSurface::ProceduralSurfaceName(1)) == "paint_yellow",
		      "interior and paint_yellow, in that order");
		const LedgerSurface::Texel Y =
			LedgerSurface::ProceduralAlbedoTexel("paint_yellow");
		const LedgerSurface::Texel In =
			LedgerSurface::ProceduralAlbedoTexel("interior");
		std::printf("    tint texels: paint_yellow %d.%d.%d interior %d.%d.%d\n",
		            Y.R, Y.G, Y.B, In.R, In.G, In.B);
		Check(Y.R == 147 && Y.G == 127 && Y.B == 35,
		      "worn municipal yellow at 0.78/0.66/0.18, quantised as Unity quantises "
		      "it and multiplied by TextureGrade in linear");
		Check(In.R == 31 && In.G == 22 && In.B == 14,
		      "and the shop interior at 0.18/0.13/0.08 through the same arithmetic");
		// THE GRADE ACTUALLY DARKENS, which is the half a typo would not move:
		// a grade applied in the wrong direction, or not at all, leaves the
		// raw byte standing.
		Check(Y.R < 199 && Y.G < 168 && Y.B < 46,
		      "the graded texel is darker than the raw tint byte on every channel");
		Check(LedgerSurface::ProceduralRoughnessTexel("paint_yellow") == 242
		      && LedgerSurface::ProceduralRoughnessTexel("interior") == 230,
		      "roughness is the complement of the spec smoothness, as the host's "
		      "gloss map is");
		Check(LedgerSurface::DecalCardRoughnessTexel() == 235,
		      "and an opaque card carries the host's own 0.08 smoothness");
		// THE TRANSFER PAIR IS AN EXACT ROUND TRIP OVER EVERY BYTE, because a
		// tint baked through an approximate inverse would shift every
		// procedural surface by a fraction of a stop.
		int Bad = 0;
		for (int V = 0; V <= 255; ++V)
		{
			const double L = LedgerVignette::SrgbToLinear((double)V / 255.0);
			if (LedgerVignette::ByteOf(LedgerVignette::LinearToSrgb(L)) != V) { ++Bad; }
		}
		Check(Bad == 0, "sRGB to linear and back is a byte-exact round trip",
		      "bytes that did not survive: " + std::to_string(Bad) + " of 256");
		Check(LedgerSurface::MapsFrom("interior") == "window",
		      "the interior borrows the window's maps, which is AssetLibrary.cs:611");
		Check(LedgerSurface::MapsFrom("window") == "window"
		      && LedgerSurface::MapsFrom("asphalt") == "asphalt",
		      "and every other surface wears its own");
		Check(LedgerSurface::IsGroundSurface("kerb")
		      && !LedgerSurface::IsGroundSurface("paint_yellow"),
		      "the ground family is the host's WetSurfaces, and the road paint is "
		      "not in it");
	}
	// THE DECAL ASSET STRING, SPLIT, AGAINST EVERY DECAL IN THE LIVE FILE.
	{
		int Decals = 0, Cropped = 0, Refused = 0;
		for (size_t I = 0; I < S.Pieces.size(); ++I)
		{
			if (S.Pieces[I].Shape != "decal") { continue; }
			++Decals;
			const LedgerSurface::DecalAsset A =
				LedgerSurface::SplitDecalAsset(S.Pieces[I].Asset);
			if (!A.bOk) { ++Refused; continue; }
			if (A.bCropped) { ++Cropped; }
		}
		std::printf("    decal assets: %d parsed, %d cropped, %d refused\n",
		            Decals, Cropped, Refused);
		Check(Decals == 20 && Refused == 0,
		      "every decal asset string in the committed street parses");
		Check(Cropped == 10,
		      "ten carry a crop rectangle and the ten ambientCG sets do not");
		const LedgerSurface::DecalAsset A =
			LedgerSurface::SplitDecalAsset("generated/fascia_mickeys#0.0391,0.2773,0.9766,0.7168");
		Check(A.bOk && A.bCropped && A.Id == "generated/fascia_mickeys",
		      "the id is everything before the hash and the crop is what follows");
		Check(std::fabs(A.U0 - 0.0391) < 1e-9 && std::fabs(A.V1 - 0.7168) < 1e-9,
		      "and all four numbers arrive, u then v, in the file's own order");
		const LedgerSurface::DecalAsset Whole =
			LedgerSurface::SplitDecalAsset("ambientcg/Moss001");
		Check(Whole.bOk && !Whole.bCropped && Whole.U1 == 1.0 && Whole.V1 == 1.0,
		      "no fragment means the whole image, which is 0,0,1,1");
		// FAILS CLOSED, BOTH WAYS, exactly as StreetVignette.SplitAsset does.
		Check(!LedgerSurface::SplitDecalAsset("generated/x#1,2").bOk,
		      "a fragment that is not four numbers is REFUSED and not guessed at");
		Check(!LedgerSurface::SplitDecalAsset("generated/x#a,b,c,d").bOk,
		      "and a fragment that is not numbers at all is refused too");
		Check(LedgerSurface::DecalCardLeaf("generated/poster_gig_bill")
		      == "generated/poster_gig_bill.png",
		      "a card asks for one filename and does not search, as the host does not");
	}
	// THE CROP IN TEXELS, AND THE ROW ORDER IS THE WHOLE OF IT.
	{
		LedgerSurface::DecalAsset Bottom;
		Bottom.bOk = true; Bottom.bCropped = true;
		Bottom.U0 = 0.0; Bottom.V0 = 0.0; Bottom.U1 = 1.0; Bottom.V1 = 0.5;
		const LedgerSurface::CropPx B = LedgerSurface::CropPixels(Bottom, 100, 100);
		std::printf("    crop of the bottom half: x%d..%d y%d..%d (%dx%d)\n",
		            B.X, B.X + B.W, B.Y, B.Y + B.H, B.W, B.H);
		Check(B.X == 0 && B.W == 100 && B.Y == 50 && B.H == 50 && !B.bClamped,
		      "v is measured from the BOTTOM and image rows arrive top down, so the "
		      "bottom half of a picture is the LAST fifty rows");
		LedgerSurface::DecalAsset Top = Bottom;
		Top.V0 = 0.5; Top.V1 = 1.0;
		const LedgerSurface::CropPx T = LedgerSurface::CropPixels(Top, 100, 100);
		Check(T.Y == 0 && T.H == 50,
		      "and the top half is the FIRST fifty, which is the flip that would "
		      "otherwise put a photograph's sky on a fascia");
		// A REAL ONE, at the size the committed fascia picture is.
		const LedgerSurface::DecalAsset M = LedgerSurface::SplitDecalAsset(
			"generated/fascia_mickeys#0.0391,0.2773,0.9766,0.7168");
		const LedgerSurface::CropPx MC = LedgerSurface::CropPixels(M, 1024, 1024);
		std::printf("    fascia_mickeys at 1024 square: x%d..%d y%d..%d (%dx%d)\n",
		            MC.X, MC.X + MC.W, MC.Y, MC.Y + MC.H, MC.W, MC.H);
		Check(MC.W == 960 && MC.H == 450 && !MC.bClamped,
		      "the committed crop takes a wide band out of the middle of the picture");
		Check(MC.Y == 290,
		      "and it starts 290 rows down, which is (1 - v1) and not v0");
		// THE REJECTING CASES, PLANTED, because a clamp that is silent cannot
		// be told from a crop that fitted.
		LedgerSurface::DecalAsset Over = Bottom;
		Over.U1 = 1.6;
		const LedgerSurface::CropPx OC = LedgerSurface::CropPixels(Over, 100, 100);
		Check(OC.bClamped && OC.X + OC.W == 100,
		      "a rectangle past the edge is clamped to the image AND says so");
		LedgerSurface::DecalAsset Inside = Bottom;
		Inside.U0 = 0.5; Inside.U1 = 0.5; Inside.V0 = 0.5; Inside.V1 = 0.5;
		const LedgerSurface::CropPx IC = LedgerSurface::CropPixels(Inside, 100, 100);
		Check(IC.W >= 1 && IC.H >= 1 && IC.bClamped,
		      "a zero-sized rectangle gives one texel rather than an empty upload");
		const LedgerSurface::CropPx NoImage = LedgerSurface::CropPixels(Bottom, 0, 0);
		Check(NoImage.W == 0 && NoImage.H == 0,
		      "and nothing decoded gives nothing cropped, not a one-texel invention");
	}
	// THE CENSUS LINE, ITS IDENTITY, ITS ZERO CASE AND ITS KEYS.
	{
		LedgerSurface::PaintTally T;
		T.Examined = 610; T.Pack = 580; T.Tint = 10; T.DecalCard = 10;
		T.DecalNoStainMaterial = 10; T.Hidden = 10;
		const std::string Seg = LedgerSurface::PaintRouteSegment(T);
		std::printf("   %s\n", Seg.c_str());
		Check(LedgerSurface::PaintedCount(T) == 600
		      && LedgerSurface::UnpaintedCount(T) == 10,
		      "painted plus unpainted is the pieces examined, and neither is derived "
		      "from the other by subtraction");
		Check(Seg.find("piecesUnpainted=10/610") != std::string::npos
		      && Seg.find("piecesPainted=600/610") != std::string::npos,
		      "both halves ship over the pieces EXAMINED");
		Check(Seg.find("paintRoutes=pack.580/tint.10/decal-card.10/decal-multiply.0")
		      != std::string::npos,
		      "and the routes are named with their own counts, not summed into one");
		Check(Seg.find("decal-needs-a-stain-material.10") != std::string::npos,
		      "every unpainted piece says WHICH rule declined it");
		LedgerSurface::PaintTally Zero;
		const std::string ZSeg = LedgerSurface::PaintRouteSegment(Zero);
		Check(ZSeg.find("piecesUnpainted=nothing-measured") != std::string::npos,
		      "a run that examined no piece prints the words and not a clean zero");
		// NO KEY MEANS TWO THINGS ON TWO LINES. The census rides the materials
		// line, so it must share no key with the surface lines or the decal
		// lines beside it.
		LedgerSurface::Bound B;
		B.Surface = "interior"; B.Pieces = 6; B.PiecesAssigned = 6;
		B.Status = "PROCEDURAL"; B.Route = "tint"; B.bTintBuilt = true;
		B.Tint = LedgerSurface::ProceduralAlbedoTexel("interior");
		B.MapBorrowed[1] = true; B.BorrowedFrom = "window";
		B.MapFile[1] = "window_n.jpg"; B.MapW[1] = 2048; B.MapH[1] = 2048;
		B.MapLoadedAs[1] = "JPEG-BGRA8/srgb=no";
		const std::string SurfLine = LedgerSurface::SurfaceLine(B);
		std::printf("    %s\n", SurfLine.c_str());
		Check(SurfLine.find("surfaceStatus=PROCEDURAL") != std::string::npos
		      && SurfLine.find("surfaceRoute=tint") != std::string::npos
		      && SurfLine.find("tintTexel=31.22.14") != std::string::npos,
		      "a procedural surface says so, names its route and prints the texel it "
		      "was painted with");
		Check(SurfLine.find("albedoFile=BUILT-IN-CODE") != std::string::npos
		      && SurfLine.find("albedoTried=card.png") == std::string::npos,
		      "and it never names a candidate file it had no reason to look for");
		Check(SurfLine.find("normalBorrowedFrom=window") != std::string::npos
		      && SurfLine.find("normalFile=window_n.jpg") != std::string::npos,
		      "a borrowed map names the surface it came from");
		LedgerSurface::Bound Blend;
		Blend.Surface = "card"; Blend.Pieces = 10; Blend.Status = "DECAL-BLEND";
		Blend.Route = "decal-card";
		const std::string BlendLine = LedgerSurface::SurfaceLine(Blend);
		std::printf("    %s\n", BlendLine.c_str());
		Check(BlendLine.find("albedoFile=NOT-A-LIBRARY-SURFACE") != std::string::npos,
		      "a decal blend is not a library surface and stops claiming to be one");
		Check(BlendLine.find("card.png") == std::string::npos,
		      "and it names no candidate filename, because card.png can never exist");
		// EveryTokenIsKeyValue AND NOT THE ONE-EQUALS FORM, and the reason is
		// a value this project already prints: a decoder's own words are
		// `JPEG-BGRA8/srgb=no`, so a map line legitimately carries a second
		// equals inside one value. The rule that matters is the one every
		// reader here depends on, which is no WHITESPACE inside a value.
		// FROM surfaceStatus ONWARD, because a surface line opens with the word
		// `surface` and the surface's name, which are a row label and not keys.
		// EveryTokenIsKeyValue and not the one-equals form, for a reason this
		// project's own strings establish: a decoder's words are
		// `JPEG-BGRA8/srgb=no`, so a map value legitimately carries a second
		// equals. The rule every reader here depends on is no WHITESPACE in a
		// value.
		Check(EveryTokenIsKeyValue(SurfLine.substr(SurfLine.find("surfaceStatus=")))
		      && EveryTokenIsKeyValue(BlendLine.substr(BlendLine.find("surfaceStatus=")))
		      && NoSpacePastPrefix(Seg, "piecesPainted="),
		      "every value on all three is space-free and is a key with a value");
		std::vector<LedgerSurface::Bound> All;
		All.push_back(B);
		std::vector<std::string> Tried;
		Tried.push_back("C:/staged/LedgerProbe/CityPackTextures");
		const std::string Done = LedgerSurface::MaterialsDoneLine(
			All, "/Game/Ledger/M_LedgerSurface", true, "C:/pack", 51, Tried,
			610, 3, 600, 2.0) + Seg;
		std::vector<std::string> DoneKeys, SurfKeys;
		KeysOf(Done, DoneKeys);
		KeysOf(SurfLine, SurfKeys);
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
		Check(Shared.empty(),
		      "the census on the materials line shares no key with a surface line",
		      Shared);
		Check(EveryTokenIsKeyValue(Done),
		      "and the joined materials line is every token a key with a value");
	}
	// ONE LINE PER DECAL, AND THE PASS'S OWN DONE LINE.
	{
		LedgerSurface::DecalResult Card;
		Card.Piece = "decal_00_fascia_mickeys"; Card.Blend = "card";
		Card.Id = "generated/fascia_mickeys"; Card.bCropAsked = true;
		Card.bLoaded = true; Card.bPainted = true;
		Card.FullW = 1024; Card.FullH = 1024;
		Card.LoadedAs = "PNG-BGRA8/srgb=yes";
		Card.Crop = LedgerSurface::CropPixels(LedgerSurface::SplitDecalAsset(
			"generated/fascia_mickeys#0.0391,0.2773,0.9766,0.7168"), 1024, 1024);
		Card.Note = "opaque-card/cropped-at-decode";
		const std::string CL = LedgerSurface::DecalLine(Card);
		std::printf("    %s\n", CL.c_str());
		Check(CL.find("decalStatus=PAINTED") != std::string::npos
		      && CL.find("decalCropSize=960x450") != std::string::npos,
		      "a painted card names its picture, its status and the size it was cut to");
		Check(CL.find("decalRowOrder=") != std::string::npos,
		      "and every decal line carries which way round the rows went");
		LedgerSurface::DecalResult Stain;
		Stain.Piece = "decal_17_Moss001"; Stain.Blend = "multiply";
		Stain.Id = "ambientcg/Moss001"; Stain.bHidden = true;
		Stain.Note = "needs-a-modulate-material";
		const std::string SL = LedgerSurface::DecalLine(Stain);
		Check(SL.find("decalStatus=HIDDEN") != std::string::npos
		      && SL.find("decalLoadedAs=not-loaded") != std::string::npos,
		      "a stain that could not be drawn says HIDDEN and never prints a size it "
		      "does not have");
		Check(EveryTokenIsKeyValue(CL) && EveryTokenIsKeyValue(SL),
		      "both decal lines are space-free keys with values, the rule every "
		      "reader of this file depends on");
		std::vector<LedgerSurface::DecalResult> All;
		All.push_back(Card); All.push_back(Stain);
		std::vector<std::string> Tried;
		Tried.push_back("C:/staged/LedgerProbe/LedgerDecals");
		const std::string D = LedgerSurface::DecalsDoneLine(All, "C:/staged/LedgerDecals",
		                                                    40, Tried);
		std::printf("   %s\n", D.c_str());
		Check(D.find("decalsPainted=1/2") != std::string::npos
		      && D.find("decalsHidden=1/2") != std::string::npos
		      && D.find("decalsByBlend=card.1/multiply.1") != std::string::npos,
		      "the pass's totals ship over the decal pieces it examined");
		Check(D.find("decalsStatus=PARTIAL") != std::string::npos,
		      "one of two painted is PARTIAL and says so");
		Check(D.find("decalFlip=rows.no/cols.no") != std::string::npos,
		      "the uv winding lever is printed rather than hidden in the source");
		const std::vector<LedgerSurface::DecalResult> NoneAtAll;
		const std::string ND = LedgerSurface::DecalsDoneLine(NoneAtAll, "", 0, Tried);
		Check(ND.find("decalsPainted=nothing-measured") != std::string::npos
		      && ND.find("decalRoot=NOT-FOUND") != std::string::npos
		      && ND.find("decalRootTried=C:/staged/LedgerProbe/LedgerDecals")
		         != std::string::npos,
		      "a pass that reached no decal prints the words, and a root it did not "
		      "find NAMES where it looked");
		std::vector<std::string> DoneKeys, LineKeys;
		KeysOf(D, DoneKeys);
		KeysOf(CL, LineKeys);
		std::string Shared;
		for (size_t I = 0; I < LineKeys.size(); ++I)
		{
			for (size_t J = 0; J < DoneKeys.size(); ++J)
			{
				if (LineKeys[I] == DoneKeys[J])
				{
					if (!Shared.empty()) { Shared += "/"; }
					Shared += LineKeys[I];
				}
			}
		}
		Check(Shared.empty(),
		      "the per-decal line and the decal done line share no key name", Shared);
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
			// A1(d): EVERY SAMPLE LINE DECLARES WHETHER ITS OWN WHOLE-FRAME
			// KEYS INCLUDE THE INSTRUMENT. Accepting case first, and the
			// accepting case is the camera that DOES carry them, because that
			// is the line a reader of shotMeanLuma has to be warned about.
			// The boxes are projected here rather than quoted from a document:
			// the percentage moves if the camera, the field of view or the
			// placement constants move, which is what a frozen literal could
			// not do.
			const std::string QA = LedgerSurface::ShotControlQuadLine(
				*QuadCam, QuadCam->Id, LedgerSurface::ControlQuadCount(), true, 1280, 720);
			const std::string QH = LedgerSurface::ShotControlQuadLine(
				*Hook, QuadCam->Id, LedgerSurface::ControlQuadCount(), true, 1280, 720);
			std::printf("    %s\n    %s\n", QA.c_str(), QH.c_str());
			Check(QA.find("shotWholeFrameIncludesControlQuads=yes/whole-frame-keys-on-this-"
			              "line-include-them/boxes=see-controlQuadVisibility-and-the-quad-"
			              "lines/PROJECTED-BOXES-NOT-MEASURED-COVERAGE") != std::string::npos,
			      "the shot taken from the camera the controls were placed from declares "
			      "that its own whole-frame keys include them, in the words the ruling "
			      "dictated", QA);
			Check(QA.find("shotControlQuadsBoxed=3/of=3/") != std::string::npos
			      && QA.find("shotControlQuadsBoxPx=x") != std::string::npos,
			      "and it carries the projected boxes with their denominator rather than "
			      "a literal copied out of a document", QA);
			Check(QH == "shotWholeFrameIncludesControlQuads=no/hidden-for-this-camera",
			      "a shot from any other camera declares no, which is the case rung 1's "
			      "own frame is in", QH);
			// AND THE THREE REFUSALS, because "no" is a claim about a frame
			// and a run that did not know its camera, did not spawn the quads
			// or did not measure the frame must not make it.
			Check(LedgerSurface::ShotControlQuadLine(*QuadCam, "", 3, true, 1280, 720)
			          .find("nothing-measured/no-camera-identity-answered") != std::string::npos
			      && LedgerSurface::ShotControlQuadLine(*QuadCam, QuadCam->Id, 0, true,
			                                            1280, 720)
			          .find("no/no-control-quads-were-spawned-in-this-build")
			          != std::string::npos
			      && LedgerSurface::ShotControlQuadLine(*QuadCam, QuadCam->Id, 3, false,
			                                            1280, 720)
			          .find("nothing-measured/this-line-carries-no-whole-frame-keys")
			          != std::string::npos,
			      "an unnamed camera, a build that spawned no quads and a line with no "
			      "whole-frame keys each say so rather than answering yes or no");
			Check(EveryTokenIsKeyValue(QA) && EveryTokenIsKeyValue(QH),
			      "both control-quad declarations are space-free, every token a key "
			      "with a value", QA);
			// THE AT-MOST PERCENTAGE IS A PROJECTION AND THE SERIES IS PRINTED
			// BEFORE ANY BOUND IS SET. No gate reads it tonight; the point of
			// printing three fields of view is that a later session sets its
			// bound off a read series rather than off one frame, which is what
			// froze the number the earlier ruling dictated as a literal.
			//
			// THE VARIABLE IS THE FIELD OF VIEW AND NOT THE FRAME SIZE, and
			// that is itself a reading taken here: the union box scales with
			// the frame, so 1280x720 and 640x360 return the SAME percentage
			// and printing both would be one number twice. The fov moves it.
			{
				const double Fovs[3] = {QuadCam->FovVerticalDeg, 39.0, 90.0};
				std::printf("    controlQuadAtMost series, one projection per field of "
				            "view, 1280x720 throughout, 3 of 3 shown:");
				for (int FI = 0; FI < 3; ++FI)
				{
					LedgerVignette::Camera Vary = *QuadCam;
					Vary.FovVerticalDeg = Fovs[FI];
					const std::string L = LedgerSurface::ShotControlQuadLine(
						Vary, QuadCam->Id, 3, true, 1280, 720);
					const size_t At = L.find("shotControlQuadsAtMostPctOfFrame=");
					std::printf(" fovV=%.1f/%s", Fovs[FI],
					            At == std::string::npos ? "not-printed"
					            : L.substr(At + 33, L.find(' ', At) - At - 33).c_str());
				}
				std::printf("\n");
				LedgerVignette::Camera Narrow = *QuadCam;
				Narrow.FovVerticalDeg = 39.0;
				const std::string N = LedgerSurface::ShotControlQuadLine(
					Narrow, QuadCam->Id, 3, true, 1280, 720);
				Check(QA.find("shotControlQuadsAtMostPctOfFrame=0.00") == std::string::npos
				      && N != QA,
				      "the at-most percentage is a projection that moves with the field of "
				      "view and not a literal, which is why no bound is set on it here",
				      QA + " | " + N);
			}
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

	// ---- QUEUE 186: THE SKY SEGMENT, ACCEPTING CASE FIRST ----------------
	//
	// Rule 5b, in the order it says: the case this must PASS is a whole sky
	// with the fills retired, because that is the state the change exists to
	// produce and a formatter that cannot print it is worth nothing. The
	// refusals come after, each with the condition PLANTED rather than
	// waited for.
	{
		LedgerVignette::SkyIn In;
		In.bSkyLightActor = true; In.bSkyLightComponent = true;
		In.bAtmosphereActor = true; In.bAtmosphereComponent = true;
		In.bFogComponent = true;
		In.SourceTypeRead = 0;
		In.bRealTimeCaptureRead = true;
		In.SkyIntensityRead = 1.0;
		In.FogDensityRead = 0.012;
		In.FogMaxOpacityRead = 0.45;
		In.bFillsRetired = true;
		In.FillsSpawned = 3;
		In.ApplyCalls = 12; In.SkyWrites = 2;
		In.HdriAsked = "Sky/polyhaven/belfast_open_field_2k";
		In.HdriFoundAt = "NOT-FOUND";
		In.HdriDetectedAs = "not-read";
		In.HdriBoundAs = "NOTHING/no-cube-texture-is-built-at-runtime-in-this-change";
		const std::string L = LedgerVignette::SkySegment(In);
		std::printf("    %s\n", L.c_str());
		Check(L.find("skyModel=skyatmosphere+skylight-realtime-capture/not-an-hdri")
		      != std::string::npos,
		      "a whole sky names its mechanism and says it is not an HDRI");
		Check(L.find("ambientModel=skylight-captured-sky/ONE-OWNER/trilight-retired-to-zero")
		      != std::string::npos,
		      "and names one owner for the ambient when the fills are retired");
		Check(L.find("skyWrites=2/of=12/") != std::string::npos,
		      "write-on-change prints both counts, so a per-tick rebuild would be visible");
		Check(L.find("skyRealTimeCaptureRead=yes") != std::string::npos
		      && L.find("skySourceTypeRead=0") != std::string::npos,
		      "the capture mode is printed as the component reported it, enum value and all");
		Check(L.find("fogMaxOpacityRead=0.450") != std::string::npos
		      && L.find("fogDensityRead=0.0120") != std::string::npos,
		      "the fog's two numbers are read back beside the sky that now shares the far field");
		Check(L.find("skyHdriBoundAs=NOTHING/") != std::string::npos,
		      "the named HDRI reports plainly that nothing was bound from it");
		Check(EveryTokenIsKeyValue(L),
		      "every sky value is space-free, so no reader truncates it silently");
	}
	{
		// AN ATMOSPHERE WITH NO SKYLIGHT: visible sky, nothing capturing it,
		// so nothing to reflect. It must not read as a whole sky.
		LedgerVignette::SkyIn In;
		In.bAtmosphereActor = true; In.bAtmosphereComponent = true;
		In.FillsSpawned = 3;
		const std::string L = LedgerVignette::SkySegment(In);
		Check(!In.Whole()
		      && L.find("skyModel=SKYLIGHT-MISSING/") != std::string::npos,
		      "an atmosphere with no skylight names the half that is missing");
		Check(L.find("ambientModel=trilight-3-directional/not-a-captured-sky/the-sky-is-not-whole")
		      != std::string::npos,
		      "and the ambient stays with the tri-light rather than claiming a captured sky");
	}
	{
		// A SKYLIGHT WITH NO ATMOSPHERE captures a black scene. That is the
		// exact failure the fill-light comment in VignetteShot.cpp warned
		// about, and it must be a NAMED state and not a dark frame.
		LedgerVignette::SkyIn In;
		In.bSkyLightActor = true; In.bSkyLightComponent = true;
		In.FillsSpawned = 3;
		const std::string L = LedgerVignette::SkySegment(In);
		Check(L.find("skyModel=ATMOSPHERE-MISSING/skylight-would-capture-a-black-scene")
		      != std::string::npos,
		      "a skylight with nothing to capture says so instead of reporting a sky");
	}
	{
		// NOTHING SPAWNED AT ALL. The far field is then still the height fog,
		// which is what the frames of 2026-09-09 actually showed, and the
		// word must say that rather than "black".
		const LedgerVignette::SkyIn In;
		const std::string L = LedgerVignette::SkySegment(In);
		std::printf("    %s\n", L.c_str());
		Check(L.find("skyModel=SPAWN-FAILED/no-sky-of-any-kind/the-far-field-is-the-height-fog")
		      != std::string::npos,
		      "no sky at all names the height fog as what fills the far field");
		Check(L.find("skyHdriAsked=none") != std::string::npos
		      && L.find("skyHdriFoundAt=NOT-LOOKED-FOR") != std::string::npos,
		      "a run that never looked for the HDRI says so rather than printing NOT-FOUND");
		Check(L.find("skyWrites=0/of=0/") != std::string::npos,
		      "zero writes ship the zero calls they are over");
		Check(EveryTokenIsKeyValue(L), "the spawn-failed sky line is space-free too");
	}
	{
		// A WHOLE SKY THAT DID NOT TAKE THE AMBIENT. Two contributors is a
		// real state and the line must name it as two rather than as one.
		LedgerVignette::SkyIn In;
		In.bSkyLightActor = true; In.bSkyLightComponent = true;
		In.bAtmosphereActor = true; In.bAtmosphereComponent = true;
		In.bFillsRetired = false; In.FillsSpawned = 3;
		const std::string L = LedgerVignette::SkySegment(In);
		Check(L.find("ambientModel=skylight+trilight/TWO-CONTRIBUTORS/") != std::string::npos,
		      "a sky that did not take ownership prints two contributors, not one owner");
	}

	// ---- QUEUE 205: THE FOUR SUN KEYS, OFF THE COMPONENT ----------------
	{
		LedgerVignette::SkyIn In;
		In.bSkyLightActor = true; In.bSkyLightComponent = true;
		In.bAtmosphereActor = true; In.bAtmosphereComponent = true;
		In.SkyIntensityRead = 0.35;
		In.bSunActor = true; In.bSunComponent = true;
		In.SunIntensityRead = 30.0;
		In.bSunCastShadowsRead = true;
		// THE YAW SLOT CARRIES A YAW, NOT AN AZIMUTH. Until 2026-09-09 this
		// fixture read 205.0, which is the file's azimuth_deg; the converted
		// yaw is SunYawDeg(205) = 25.0, and a reader learning the key from
		// this test learned it wrong. Nothing depended on it, and a key
		// taught wrong by its own test is how a unit survives a review.
		In.SunPitchRead = -36.0; In.SunYawRead = LedgerVignette::SunYawDeg(205.0);
		In.SunMobilityRead = 2;
		const std::string L = LedgerVignette::SkySegment(In);
		std::printf("    %s\n", L.c_str());
		Check(L.find("sunIntensityRead=30.000") != std::string::npos,
		      "the sun's intensity is printed as the component reported it");
		Check(L.find("sunCastShadowsRead=yes") != std::string::npos,
		      "and whether it casts, which sun=yes never said");
		Check(L.find("sunPitchYawRead=-36.0/25.0") != std::string::npos,
		      "and where it points, as one pair with no space in it, the CONVERTED yaw and not the azimuth");
		Check(L.find("sunMobilityRead=2") != std::string::npos
		      && L.find("sunMobilityKey=0-static/1-stationary/2-movable/") != std::string::npos,
		      "and its mobility as the engine's own enum value with the key beside it");
		Check(L.find("sunReadStat=one-per-run/last-wins/") != std::string::npos,
		      "and the line says WHICH moment the four are a reading of");
		Check(L.find("skyIntensityRead=0.350") != std::string::npos,
		      "the sky it is being read against is still on the same line");
		Check(EveryTokenIsKeyValue(L),
		      "the grown line is still space-free, so no reader truncates the sun keys");
	}
	{
		// A SUN THAT DID NOT SPAWN PRINTS WORDS, NOT ZEROS. sun=SPAWN-FAILED
		// with sunIntensityRead=0.000 would be the same string a sun that
		// is switched off prints, and those are different facts.
		LedgerVignette::SkyIn In;
		const std::string L = LedgerVignette::SkySegment(In);
		Check(L.find("sun=SPAWN-FAILED") != std::string::npos
		      && L.find("sunIntensityRead=nothing-measured") != std::string::npos
		      && L.find("sunMobilityRead=nothing-measured") != std::string::npos,
		      "a sun that never spawned says nothing-measured rather than printing a zero");
		Check(EveryTokenIsKeyValue(L), "the nothing-measured sun line is space-free too");
	}
	{
		// PER-SAMPLE, ON THE SAMPLE LINE. A ladder renders six conditions
		// in one run and the scene line is one-per-run, so this is the
		// half that can attribute a rung to the sun that lit it.
		const std::string L = LedgerVignette::ShotLightLine(
			true, 300.0, 300.0, true, -36.0, LedgerVignette::SunYawDeg(205.0), 2, true, 1.0, 1.0);
		std::printf("    %s\n", L.c_str());
		Check(L.find("shotSunIntensityRead=300.000") != std::string::npos
		      && L.find("shotSkyIntensityRead=1.000") != std::string::npos,
		      "the frame's own line carries both intensities as the components read them");
		// A1(c), CONDITION C5: THE ASK IS ON THE SAME LINE AS THE READ, and
		// the cell says whether they agreed. Run 38 printed five rungs that
		// all read sky 1.000 and never printed what any of them asked for.
		Check(L.find("shotSunIntensityAsked=300.000") != std::string::npos
		      && L.find("shotSkyIntensityAsked=1.000") != std::string::npos
		      && L.find("shotCellAgrees=yes") != std::string::npos,
		      "a cell lit by the numbers it asked for prints both halves and says it agreed");
		// AND THE PLANTED DISAGREEMENT, which is the case the key exists for:
		// the grid's middle skies are the cells that have never been rendered,
		// so a row reading back the old 1.000 must refuse rather than report.
		const std::string Wrong = LedgerVignette::ShotLightLine(
			true, 3.0, 3.0, true, -36.0, 25.0, 2, true, 0.70, 1.000);
		std::printf("    %s\n", Wrong.c_str());
		Check(Wrong.find("shotSkyIntensityAsked=0.700") != std::string::npos
		      && Wrong.find("shotSkyIntensityRead=1.000") != std::string::npos
		      && Wrong.find("shotCellAgrees=NO/the-frame-was-lit-by-numbers-this-row-did-not-ask-for")
		         != std::string::npos,
		      "a cell that asked for a middle sky and read back 1.000 says NO on its own line");
		Check(EveryTokenIsKeyValue(Wrong), "the disagreeing cell line is space-free");
		Check(L.find("shotLightStat=read-off-the-components-while-THIS-frame-stood/"
		             "per-sample-not-per-run") != std::string::npos,
		      "and says it is a per-sample reading, so it is never read as a whole-run number");
		Check(EveryTokenIsKeyValue(L), "the shot light line is space-free");
		const std::string M = LedgerVignette::ShotLightLine(
			false, 3.0, 0.0, false, 0.0, 0.0, -1, false, 1.0, 0.0);
		Check(M.find("shotSunIntensityRead=nothing-measured") != std::string::npos
		      && M.find("shotSkyIntensityRead=nothing-measured") != std::string::npos,
		      "a frame taken with no sun component says nothing-measured on its own line");
		// AND A CELL THAT WAS NOT READ IS NOT A CELL THAT AGREED. The ask is
		// still printed, because the row existed; the agreement is not.
		Check(M.find("shotSunIntensityAsked=3.000") != std::string::npos
		      && M.find("shotCellAgrees=nothing-measured/no-component-answered-on-this-frame")
		         != std::string::npos,
		      "an unread cell prints what it asked for and refuses to claim agreement");
		Check(EveryTokenIsKeyValue(M), "the unread cell line is space-free too");

		// ---- THE WHOLE-RUN TALLY, AND ITS NEVER-RAN CASE -----------------
		const std::string T = LedgerVignette::CellAgreeLine(25, 25, 25);
		std::printf("    %s\n", T.c_str());
		Check(T.find("cellAgree=25/of=25/read") != std::string::npos
		      && T.find("cellAgreeRead=25/of=25/asked") != std::string::npos,
		      "the run line counts agreeing cells over the cells READ and the cells read over the shots ASKED");
		Check(LedgerVignette::CellAgreeLine(11, 12, 25).find("cellAgree=11/of=12/read")
		      != std::string::npos,
		      "and one cell short of twelve reads as eleven of twelve rather than as a pass");
		const std::string Z = LedgerVignette::CellAgreeLine(0, 0, 25);
		Check(Z.find("cellAgree=nothing-measured/of=25/shots-asked") != std::string::npos,
		      "a run that read no cell says nothing measured over the shots it was asked for, never 0/0");
		Check(EveryTokenIsKeyValue(T) && EveryTokenIsKeyValue(Z),
		      "both forms of the cell tally are space-free");
	}

	{
		// ---- QUEUE 208: THE CAMERA ON THE FRAME'S OWN LINE ---------------
		//
		// ACCEPTING CASE FIRST, and it is the one the tool has to read:
		// cam_hook as run 38 placed it. x_m 4.0 and z_m -2.1 map to X 400.0
		// and Y -210.0, ground -0.0525 plus eye 1.65 is Z 159.8, and the
		// file's pitch of -2.6 down is a POSITIVE 2.6 in this engine. Those
		// are the numbers tools/frame-shadow-probe.py compares against the
		// shared json, so if this string is wrong the tool refuses.
		LedgerVignette::ShotCamIn In;
		In.CamId = "cam_hook";
		In.Status = "MEASURED";
		In.AskedXCm = 400.0; In.AskedYCm = -210.0; In.AskedZCm = 159.75;
		In.ReadXCm  = 400.0; In.ReadYCm  = -210.0; In.ReadZCm  = 159.75;
		In.AskedPitchDeg = 2.6; In.AskedYawDeg = 11.0;
		In.ReadPitchDeg  = 2.6; In.ReadYawDeg  = 11.0;
		const std::string L = LedgerVignette::ShotCamSegment(In);
		std::printf("    %s\n", L.c_str());
		Check(L.find("shotCamId=cam_hook") != std::string::npos
		      && L.find("shotCamReadXYZcm=400.0/-210.0/159.8") != std::string::npos
		      && L.find("shotCamReadPitchYaw=2.6/11.0") != std::string::npos,
		      "the frame's own line carries the camera it was taken from and the pose read back");
		Check(L.find("shotCamDeltaCm=0.00") != std::string::npos,
		      "a camera that landed where it was sent prints a zero distance, not a claim");
		Check(L.find("shotCamStat=asked-against-read-back-off-the-player-view-point-while-THIS-"
		             "frame-stood/per-sample-not-per-run") != std::string::npos,
		      "and says it is a per-sample reading, so it is never read as a whole-run number");
		Check(EveryTokenIsKeyValue(L), "the shot camera segment is space-free");

		// ---- AND THE PLANTED CASE: A CAMERA THAT DID NOT ARRIVE ----------
		//
		// Rule 5b, the other outcome watched. The distance is computed here
		// rather than in the module, so a camera that was sent somewhere and
		// ended up somewhere else says so with a number.
		LedgerVignette::ShotCamIn Off = In;
		Off.ReadZCm = 159.75 - 40.0;
		const std::string M = LedgerVignette::ShotCamSegment(Off);
		Check(M.find("shotCamDeltaCm=40.00") != std::string::npos
		      && M.find("shotCamAskedXYZcm=400.0/-210.0/159.8") != std::string::npos
		      && M.find("shotCamReadXYZcm=400.0/-210.0/119.8") != std::string::npos,
		      "a camera that did not arrive prints both halves and the distance between them");

		// ---- AND A SHOT THAT HAD NO CAMERA TO READ -----------------------
		LedgerVignette::ShotCamIn None;
		None.CamId = "cam_A";
		None.Status = "NO-WORLD";
		const std::string N = LedgerVignette::ShotCamSegment(None);
		std::printf("    %s\n", N.c_str());
		Check(N.find("shotCamRead=NO-WORLD") != std::string::npos
		      && N.find("shotCamReadXYZcm=nothing-measured") != std::string::npos
		      && N.find("shotCamDeltaCm=nothing-measured") != std::string::npos,
		      "a shot whose camera could not be read says the words rather than printing an origin");
		Check(EveryTokenIsKeyValue(N), "the nothing-measured camera segment is space-free too");
		// A ZERO POSE AND AN UNREAD POSE ARE DIFFERENT FACTS, and the second
		// may never print as the first: an unread camera at 0/0/0 would read
		// as a camera that really was at the world origin.
		Check(N.find("0.0/0.0/0.0") == std::string::npos,
		      "an unread camera never prints the origin it was default-constructed at");
	}

	// ---- A6: THE LIGHTS, ASKED AGAINST READ, AND THE GUARD'S TWO CASES ---
	//
	// WHAT WAS MISSING AND WHAT IT COST. The sun's conversion was tested at
	// line 404 of this file and its format string at 2058, and the engine
	// rendered a sun 46.0 degrees from the asked one for every run the key
	// has existed, because no test asked whether the number ARRIVED. These
	// run in the layer that compiles here; the arrival itself is measured on
	// the run, which is what lightAimStatus refuses on.
	//
	// ACCEPTING CASE FIRST, PER RULE 5b, AND ON THE LIVE VALUES: the asked
	// pair is the committed file's own sun put through the same two
	// converters the spawner calls, so this fixture cannot drift from the
	// scene.
	{
		const double AskedPitch = LedgerVignette::SunPitchDeg(S.SunElevationDeg);
		const double AskedYaw   = LedgerVignette::SunYawDeg(S.SunAzimuthDeg);
		std::printf("    lightAim: liveAskedPitchYaw=%.1f/%.1f from elevation=%.1f azimuth=%.1f\n",
		            AskedPitch, AskedYaw, S.SunElevationDeg, S.SunAzimuthDeg);
		std::vector<LedgerVignette::LightAim> Lights;
		LedgerVignette::LightAim Sun;
		Sun.Name = "sun"; Sun.bSpawned = true; Sun.bRead = true;
		Sun.AskedPitch = AskedPitch; Sun.AskedYaw = AskedYaw;
		Sun.ReadPitch = AskedPitch;  Sun.ReadYaw = AskedYaw;
		Lights.push_back(Sun);
		// THE THREE FILLS, WITH THE LITERALS VignetteShot.cpp SPAWNS THEM
		// FROM, and fill B is the case that matters: it asks for yaw 200.0
		// and an FRotator normalises that to -160.0, which is the same
		// direction. A residual that did not wrap would refuse a light aimed
		// exactly where it was sent, and the guard would have been a ratchet.
		const double FillPitch[3] = { -80.0, -10.0,  60.0 };
		const double FillYaw[3]   = {  20.0, 200.0,  90.0 };
		const double FillReadYaw[3] = { 20.0, -160.0, 90.0 };
		const char* FillName[3] = { "fillA", "fillB", "fillC" };
		for (int K = 0; K < 3; ++K)
		{
			LedgerVignette::LightAim F;
			F.Name = FillName[K]; F.bSpawned = true; F.bRead = true;
			F.AskedPitch = FillPitch[K]; F.AskedYaw = FillYaw[K];
			F.ReadPitch = FillPitch[K];  F.ReadYaw = FillReadYaw[K];
			Lights.push_back(F);
		}
		const std::string L = LedgerVignette::LightAimLine(Lights, 4);
		std::printf("    %s\n", L.c_str());
		Check(L.find("lightAimStatus=AGREES") != std::string::npos,
		      "four lights aimed where they were sent print the one passing word");
		Check(L.find("lightAimAgreeing=4/of=4/read") != std::string::npos
		      && L.find("lightAimRead=4/of=4/spawned") != std::string::npos
		      && L.find("lightAimSpawned=4/of=4/") != std::string::npos,
		      "and every count ships the denominator it is over");
		Check(L.find("lightAim.sun.askedPitchYaw=-36.0/25.0") != std::string::npos
		      && L.find("lightAim.sun.readPitchYaw=-36.0/25.0") != std::string::npos,
		      "the sun's asked pair is the live file's -36.0/25.0 and it is printed beside the read pair",
		      "the committed spec asks elevation 36 azimuth 205");
		Check(L.find("lightAim.sun.residualPitchYawDeg=0.0000/0.0000") != std::string::npos,
		      "a light that arrived prints a zero residual on both axes to four decimals");
		Check(L.find("lightAim.fillB.askedPitchYaw=-10.0/200.0") != std::string::npos
		      && L.find("lightAim.fillB.readPitchYaw=-10.0/-160.0") != std::string::npos
		      && L.find("lightAim.fillB.residualPitchYawDeg=0.0000/0.0000") != std::string::npos,
		      "a yaw of 200 reading back as -160 is the same direction and wraps to a zero residual",
		      "an unwrapped subtraction would print -360.0000 and refuse a correct light");
		Check(L.find("lightAimWorstResidualDeg=0.0000/on=") != std::string::npos,
		      "and the worst residual over the population is named with the light and axis it is on");
		Check(L.find("lightAimRefuseAtDeg=1.0/NOT-A-MEASURED-TOLERANCE/") != std::string::npos,
		      "the bound says in its own value that it is a class separator and not a measurement");
		Check(EveryTokenIsKeyValue(L), "the lightAim line is space-free, every token a key with a value");

		// ---- THE PLANTED OFFSET, WHICH MUST REFUSE -----------------------
		//
		// 46.0 degrees of pitch is not an invented number: it is the exact
		// displacement the committed verdict carried, asked -36.0 against
		// read -82.0. The guard is tested on the fault it exists for.
		std::vector<LedgerVignette::LightAim> Planted = Lights;
		Planted[0].ReadPitch = AskedPitch - 46.0;
		const std::string M = LedgerVignette::LightAimLine(Planted, 4);
		std::printf("    %s\n", M.c_str());
		Check(M.find("lightAimStatus=REFUSED") != std::string::npos,
		      "a sun 46 degrees from its ask refuses rather than reporting");
		Check(M.find("lightAim.sun.readPitchYaw=-82.0/25.0") != std::string::npos
		      && M.find("lightAim.sun.residualPitchYawDeg=-46.0000/0.0000") != std::string::npos,
		      "and the line carries the run-38 pair and the signed 46 degree residual",
		      "the committed verdict read sunPitchYawRead=-82.0/25.0 against an asked -36.0/25.0");
		Check(M.find("lightAim.sun=REFUSED") != std::string::npos
		      && M.find("lightAim.fillA=AGREES") != std::string::npos,
		      "the refusal names WHICH light, so three agreeing lights do not hide the fourth");
		Check(M.find("lightAimAgreeing=3/of=4/read") != std::string::npos,
		      "and the count over the population moves with it");
		Check(M.find("lightAimWorstResidualDeg=-46.0000/on=sun/axis=pitch") != std::string::npos,
		      "the at-worst residual is signed and names the light and the axis it was worst on");
		// AND A HALF DEGREE MUST NOT REFUSE, which is the other side of the
		// class separator: the bound exists to catch 46.0 and not a float
		// round trip, and a guard that cannot tell them apart is a ratchet.
		std::vector<LedgerVignette::LightAim> Small = Lights;
		Small[0].ReadYaw = AskedYaw + 0.5;
		Check(LedgerVignette::LightAimLine(Small, 4).find("lightAimStatus=AGREES")
		      != std::string::npos,
		      "half a degree does not refuse, because 1.0 separates the 46.0 fault from rounding");

		// ---- AND A RUN THAT READ NOTHING, WHICH IS NOT A PASS ------------
		std::vector<LedgerVignette::LightAim> NoneRead;
		LedgerVignette::LightAim Dead;
		Dead.Name = "sun"; Dead.bSpawned = true; Dead.bRead = false;
		Dead.AskedPitch = AskedPitch; Dead.AskedYaw = AskedYaw;
		NoneRead.push_back(Dead);
		const std::string N = LedgerVignette::LightAimLine(NoneRead, 4);
		std::printf("    %s\n", N.c_str());
		Check(N.find("lightAimStatus=NOTHING-MEASURED") != std::string::npos
		      && N.find("lightAim.sun=NO-COMPONENT") != std::string::npos
		      && N.find("lightAim.sun.readPitchYaw=nothing-measured") != std::string::npos,
		      "a light with no component prints the words rather than a zero that reads as the horizon");
		Check(N.find("lightAimWorstResidualDeg=nothing-measured/") != std::string::npos
		      && N.find("lightAimRead=0/of=1/spawned") != std::string::npos,
		      "a run that read no light says so with its denominators and never prints a zero residual");
		Check(N.find("lightAimStatus=AGREES") == std::string::npos,
		      "and NOTHING-MEASURED is not the passing word, so the guard fails closed");
		Check(EveryTokenIsKeyValue(N), "the nothing-measured lightAim line is space-free too");
	}

	// ---- THE NULL SERIES, DISCOVERED ON THE LIVE FILE --------------------
	//
	// C4 as amended: the noise floor is a SPREAD over every frame this engine
	// renders identically, not one subtraction. The accepting fixture is the
	// committed spec, which is this project's rule for a tool that checks the
	// project itself, and the thing being checked is the DISCOVERY: the group
	// is found from the conditions, so nobody has to keep a list of seven shot
	// ids in a header. The statistics are synthetic, because no frame exists in
	// this container, and the model is named rather than assumed: a signal
	// linear in sky intensity plus a bounded per-shot noise.
	{
		std::printf("  null series, the spread that C4 reads the grid against\n");
		// THE SIGNAL AND THE NOISE, BOTH CHOSEN HERE SO THE EXPECTED VERDICT
		// IS ARITHMETIC AND NOT A GUESS. Signal: 0.20 of luma per unit of sky,
		// so the smallest sky step in the grid (0.35 to 0.50) is 0.0300.
		// Noise: 0.0005 times the shot index modulo 4, so no spread over any
		// identical-input group can exceed 0.0015.
		std::vector<LedgerVignette::FrameSample> Samples;
		for (size_t I = 0; I < S.Shots.size(); ++I)
		{
			const LedgerVignette::Condition* C = 0;
			for (size_t J = 0; J < S.Conditions.size(); ++J)
			{
				if (S.Conditions[J].Id == S.Shots[I].ConditionId) { C = &S.Conditions[J]; }
			}
			if (C == 0) { continue; }
			LedgerVignette::FrameSample F;
			F.ShotId = S.Shots[I].Id;
			F.CameraId = S.Shots[I].CameraId;
			F.Applied      = LedgerVignette::AppliedFieldsUnreal(*C, true);
			F.AppliedNoSky = LedgerVignette::AppliedFieldsUnreal(*C, false);
			F.SkyIntensity = C->SkyIntensity;
			F.bMeasured = true;
			F.MeanLuma  = 0.30 + 0.20 * C->SkyIntensity + 0.0005 * (double)(I % 4);
			F.GroundP05 = F.MeanLuma * 0.50;
			F.GroundP50 = F.MeanLuma * 0.80;
			Samples.push_back(F);
		}
		const std::string NS = LedgerVignette::NullSeriesLine(Samples);
		std::printf("    %s\n", NS.c_str());
		// THE GROUP SIZE AND THE DENOMINATORS ARE COUNTED HERE, NOT PINNED.
		// Rows enter and leave this file by the item that needs them, so a
		// literal 7 of 25 fails for the wrong reason the first time a row is
		// added. WHAT IS BEING CHECKED IS THE DISCOVERY, so the expected
		// numbers are recomputed from the same conditions by an independent
		// tally here, and the SEVEN NAMED IDS below are what anchors that
		// tally to the review's own group: if the discovery ever picks a
		// different group, the id list fails even though both counts agree.
		int Largest = 0, DistinctGroups = 0;
		{
			std::vector<std::string> Keys;
			std::vector<int> Counts;
			for (size_t I = 0; I < Samples.size(); ++I)
			{
				if (!Samples[I].bMeasured) { continue; }
				const std::string K = LedgerVignette::SampleKey(Samples[I], true);
				size_t At = Keys.size();
				for (size_t J = 0; J < Keys.size(); ++J) { if (Keys[J] == K) { At = J; } }
				if (At == Keys.size()) { Keys.push_back(K); Counts.push_back(0); }
				++Counts[At];
			}
			DistinctGroups = (int)Keys.size();
			for (size_t J = 0; J < Counts.size(); ++J)
			{
				if (Counts[J] > Largest) { Largest = Counts[J]; }
			}
		}
		char WantSamples[96], WantMeasured[96];
		std::snprintf(WantSamples, sizeof(WantSamples), "nullSeriesSamples=%d/of=%d/",
		              Largest, (int)S.Shots.size());
		std::snprintf(WantMeasured, sizeof(WantMeasured), "nullSeriesMeasured=%d/of=%d/",
		              (int)Samples.size(), (int)S.Shots.size());
		std::printf("    counted independently: largestGroup=%d distinctGroups=%d "
		            "samples=%d of shots=%d\n",
		            Largest, DistinctGroups, (int)Samples.size(), (int)S.Shots.size());
		Check(NS.find(WantSamples) != std::string::npos
		      && NS.find(WantMeasured) != std::string::npos,
		      "the live file's largest identical-input group in THIS engine is the size an "
		      "independent tally over the same conditions counts, over the shots the file "
		      "actually carries, recovered from the conditions and not from a list of ids",
		      std::string(WantSamples) + " and " + WantMeasured + " against: " + NS);
		Check(NS.find("nullSeriesIds=vign_hook_day;vign_grid_sky100_sun003;"
		              "vign_fog_maxop0450;vign_wet_000;vign_wet_060;vign_wet_100;"
		              "vign_grid_null_repeat") != std::string::npos,
		      "and they are the seven shots the review named, in shot order, with the "
		      "judged hook frame among them", NS);
		Check(NS.find("nullSeriesExcludes=wetness/because-VignetteShot.cpp-has-no-read-"
		              "site-for-it-on-this-commit") != std::string::npos,
		      "the line says which field it excluded and why, because three of the seven "
		      "are null samples HERE only for want of a read site", NS);
		Check(NS.find("nullSeriesStatus=READ") != std::string::npos
		      && NS.find("nullSeriesVerdict=CLEAR") != std::string::npos
		      && NS.find("nullSeriesClear=3/of=3/") != std::string::npos,
		      "on a fixture whose noise is 0.0015 at most and whose smallest sky step is "
		      "0.0300, all three statistics read CLEAR and the denominator says three",
		      NS);
		// THE SKY STEP IS READ OFF THE LINE AND CHECKED AS A NUMBER, with the
		// tolerance being the noise the fixture itself plants: 0.20 per unit of
		// sky times the 0.15 step is 0.0300, plus or minus 0.0015.
		{
			const size_t At = NS.find("skyStepSmallestMeanLuma=");
			const double Step = At == std::string::npos ? -1.0
			                  : std::atof(NS.c_str() + At + 24);
			std::printf("    skyStepSmallestMeanLuma read back as %.4f, fixture "
			            "arithmetic says 0.0300 plus or minus 0.0015\n", Step);
			Check(Step > 0.0285 - 1e-9 && Step < 0.0315 + 1e-9,
			      "the smallest sky step is the 0.35-to-0.50 step of the grid, within "
			      "the noise the fixture plants, and it is found without naming a cell",
			      NS);
		}
		Check(NS.find("nullSpreadMeanLuma=0.0015/max=") != std::string::npos
		      && NS.find("nullDriftMeanLuma=") != std::string::npos
		      && NS.find("nullOrderMeanLuma=") != std::string::npos,
		      "the spread, the one-pair drift in shot order and whether the group is "
		      "monotone all print, which is what separates a drift from a step", NS);
		Check(EveryTokenIsKeyValue(NS),
		      "the null series line is space-free, every token a key with a value", NS);
		// AND THE CASE THE GATE MUST REFUSE, PLANTED RATHER THAN WAITED FOR.
		// Rule 5b: a guard needs a run where the thing it asserts CAN happen.
		// The same frames with the noise raised to 0.05 per step is a rig whose
		// own repeat moves further than the grid's smallest sky step, which is
		// exactly the condition that made the sun ladder unreadable.
		{
			std::vector<LedgerVignette::FrameSample> Loud = Samples;
			for (size_t I = 0; I < Loud.size(); ++I)
			{
				const double N2 = 0.05 * (double)(I % 4);
				Loud[I].MeanLuma  = 0.30 + 0.20 * Loud[I].SkyIntensity + N2;
				Loud[I].GroundP05 = Loud[I].MeanLuma * 0.50;
				Loud[I].GroundP50 = Loud[I].MeanLuma * 0.80;
			}
			const std::string LN = LedgerVignette::NullSeriesLine(Loud);
			std::printf("    planted: %s\n", LN.substr(0, 220).c_str());
			Check(LN.find("nullSeriesVerdict=NO-READ/no-cell-may-be-quoted")
			      != std::string::npos
			      && LN.find("nullFloorMeanLuma=NOT-SMALLER/") != std::string::npos,
			      "a rig whose null spread is wider than the smallest sky step makes the "
			      "grid a NO-READ, and the key names which statistic failed", LN);
		}
		// AND A RUN THAT MEASURED NOTHING, WHICH IS NOT A CLEAN RESULT.
		std::vector<LedgerVignette::FrameSample> None;
		const std::string Z = LedgerVignette::NullSeriesLine(None);
		std::printf("    %s\n", Z.c_str());
		Check(Z.find("nullSeriesStatus=NOTHING-MEASURED") != std::string::npos
		      && Z.find("nullSeriesSamples=nothing-measured/of=0/") != std::string::npos
		      && Z.find("nullSeriesVerdict=CLEAR") == std::string::npos,
		      "a run with no measured frame prints the words and never the passing "
		      "verdict, so an empty series cannot read as a clear one", Z);
		// ONE MEASURED FRAME IS NOT A SPREAD EITHER.
		std::vector<LedgerVignette::FrameSample> One;
		if (!Samples.empty()) { One.push_back(Samples[0]); }
		const std::string O = LedgerVignette::NullSeriesLine(One);
		Check(O.find("nullSeriesStatus=TOO-FEW-SAMPLES") != std::string::npos
		      && O.find("nullSeriesVerdict=nothing-measured/one-frame-cannot-hold-a-spread")
		         != std::string::npos,
		      "and one frame says so rather than printing a spread of zero", O);
		Check(EveryTokenIsKeyValue(Z) && EveryTokenIsKeyValue(O),
		      "both refusing null series lines are space-free too");
		// AMENDMENT 5: THE TIE COUNTER COUNTS GROUPS, AND THIS IS THE RUN THAT
		// FAILS ON THE CODE THAT COUNTED FRAMES.
		//
		// Section 9 of game-design/decision-2026-09-10-ruling-the-four-lane-
		// batch.md. The old loop in NullSeriesLine ran over FRAMES and
		// incremented once per frame of a rival group, so ONE rival group of
		// seven frames printed nullSeriesTiedGroups=7 and read as seven rival
		// groups. Nothing in the repository asserted the key: one grep hit, the
		// emit itself, which is how it stayed latent while the live spec had a
		// single largest group.
		//
		// WHAT MAKES THESE CATCHING RUNS AND NOT DECORATION. On the old
		// frame-counting code the two-way fixture below prints 3 and the
		// three-way fixture prints 6, because every frame of every rival group
		// incremented once. Both Checks fail there and pass here. The ties are
		// PLANTED, because the committed spec has exactly one largest group and
		// a tie cannot be waited for; the accepting case is the live line NS
		// above, read by name so the no-tie reading is watched too.
		char WantTies[112];
		std::snprintf(WantTies, sizeof(WantTies),
		              "nullSeriesTiedGroups=0/of=%d/distinct-groups-examined/", DistinctGroups);
		Check(NS.find(WantTies) != std::string::npos,
		      "the live spec has ONE largest group so the tie count is zero, and the zero "
		      "ships as its denominator the number of distinct groups an independent tally "
		      "over the same conditions examined", std::string(WantTies) + " against: " + NS);
		{
			// TWO GROUPS OF THREE PLUS A SINGLETON, so the tie count and the
			// denominator are different numbers and neither can stand in for
			// the other. One rival group: the answer is 1, never 3.
			const char* Two[7] = { "gA", "gA", "gA", "gB", "gB", "gB", "gC" };
			std::vector<LedgerVignette::FrameSample> Tie;
			for (int I = 0; I < 7; ++I)
			{
				LedgerVignette::FrameSample F;
				char Sid[32];
				std::snprintf(Sid, sizeof(Sid), "tie_%02d", I);
				F.ShotId = Sid;
				F.CameraId = "cam_tie";
				F.Applied = Two[I];
				F.AppliedNoSky = Two[I];
				F.SkyIntensity = 1.0;
				F.bMeasured = true;
				F.MeanLuma = 0.50;
				F.GroundP05 = 0.25;
				F.GroundP50 = 0.40;
				Tie.push_back(F);
			}
			const std::string T2 = LedgerVignette::NullSeriesLine(Tie);
			std::printf("    planted two-way tie: %s\n",
			            T2.substr(0, 260).c_str());
			Check(T2.find("nullSeriesTiedGroups=1/of=3/distinct-groups-examined/"
			              "groups-not-frames/") != std::string::npos,
			      "one rival group of three frames prints ONE tied GROUP of three "
			      "distinct groups examined, where the frame-counting code printed 3",
			      T2);
			Check(T2.find("nullSeriesIds=tie_00;tie_01;tie_02") != std::string::npos,
			      "and the kept group on a tie is still the first in shot order, which "
			      "the strict greater-than preserves", T2);
			Check(EveryTokenIsKeyValue(T2),
			      "the tied line is space-free, every token a key with a value", T2);
		}
		{
			// THREE GROUPS OF THREE, A SINGLETON, AND ONE UNMEASURED FRAME
			// CARRYING A KEY OF ITS OWN. Two rival groups, four distinct groups
			// examined, and the unmeasured frame must enter NEITHER number: a
			// denominator larger than the set examined turns a clean result
			// into a false claim with a number on it.
			const char* Three[11] = { "gA", "gA", "gA", "gB", "gB", "gB",
			                          "gC", "gC", "gC", "gD", "gZ" };
			std::vector<LedgerVignette::FrameSample> Tie3;
			for (int I = 0; I < 11; ++I)
			{
				LedgerVignette::FrameSample F;
				char Sid[32];
				std::snprintf(Sid, sizeof(Sid), "t3_%02d", I);
				F.ShotId = Sid;
				F.CameraId = "cam_tie";
				F.Applied = Three[I];
				F.AppliedNoSky = Three[I];
				F.SkyIntensity = 1.0;
				F.bMeasured = (I != 10);
				F.MeanLuma = 0.50;
				F.GroundP05 = 0.25;
				F.GroundP50 = 0.40;
				Tie3.push_back(F);
			}
			const std::string T3 = LedgerVignette::NullSeriesLine(Tie3);
			std::printf("    planted three-way tie: %s\n",
			            T3.substr(0, 260).c_str());
			Check(T3.find("nullSeriesTiedGroups=2/of=4/distinct-groups-examined/"
			              "groups-not-frames/") != std::string::npos,
			      "two rival groups of three frames each print TWO tied GROUPS of four "
			      "distinct groups examined, where the frame-counting code printed 6",
			      T3);
			Check(T3.find("nullSeriesMeasured=10/of=11/shots-offered") != std::string::npos,
			      "and the unmeasured frame is outside both the tie count and the "
			      "distinct-group denominator, while the measured count still names the "
			      "eleven offered", T3);
			Check(EveryTokenIsKeyValue(T3),
			      "the three-way tied line is space-free too", T3);
		}
	}

	// ---- QUEUE 235: THE EXPOSURE PIN AND ITS LADDER ----------------------
	//
	// ACCEPTING CASE FIRST, on the live file, then the rejecting cases
	// planted, because a rejection has to be provoked: the repository has no
	// row whose pin failed to land.
	{
		std::printf("  the exposure pin, asked beside read, and the ladder it sets a value from\n");
		// THE LIVE FILE IS THE ACCEPTING FIXTURE. Every condition must carry
		// the field, exactly the ladder rungs may ask for a pin, and the four
		// asked values are read back off the file rather than retyped here.
		int Pinned = 0, Unpinned = 0, Rungs = 0;
		double Lo = 0.0, Hi = 0.0;
		for (size_t I = 0; I < S.Conditions.size(); ++I)
		{
			const LedgerVignette::Condition& C = S.Conditions[I];
			if (LedgerVignette::ExposurePinAsked(C.ExposurePin))
			{
				++Pinned;
				if (Pinned == 1 || C.ExposurePin < Lo) { Lo = C.ExposurePin; }
				if (Pinned == 1 || C.ExposurePin > Hi) { Hi = C.ExposurePin; }
			}
			else { ++Unpinned; }
			if (C.Id.compare(0, 4, "pin_") == 0 && C.Id != "pin_setter_night") { ++Rungs; }
		}
		std::printf("    pins: pinned=%d unpinned=%d rungs=%d span=%.3f..%.3f of %d conditions\n",
		            Pinned, Unpinned, Rungs, Lo, Hi, (int)S.Conditions.size());
		Check(Pinned + Unpinned == (int)S.Conditions.size() && Pinned == Rungs && Rungs > 0,
		      "every condition in the live file answers the pin question, and the only rows "
		      "asking for a pin are the ladder rungs",
		      "a row pinned by accident would be photographed at an exposure nobody chose");
		Check(Hi > Lo * 100.0,
		      "the ladder spans more than two decades of the engine's own clamp range, which "
		      "is a bracket rather than a guess",
		      "the value cannot be computed from any committed luma, so the rungs have to "
		      "straddle the answer");
		// THE SEGMENT, FOUR CASES, IN THE ORDER THE RULE ASKS FOR.
		LedgerVignette::ExposurePinIn Held;
		Held.Asked = 0.300; Held.ReadMin = 0.300000011920929; Held.ReadMax = 0.300000011920929;
		Held.bOverMin = true; Held.bOverMax = true; Held.bRead = true; Held.bSunOn = true;
		const std::string HS = LedgerVignette::ExposurePinSegment(Held);
		std::printf("    %s\n", HS.c_str());
		Check(HS.find("shotExposurePin=PINNED-HELD") != std::string::npos
		      && HS.find("shotExposurePinAsked=0.3000") != std::string::npos
		      && HS.find("shotExposurePinRead=0.3000/0.3000") != std::string::npos
		      && HS.find("shotExposurePinOverrides=1/1") != std::string::npos
		      && HS.find("shotExposurePinFamily=day") != std::string::npos,
		      "a pin written as a double and read back as a float is HELD, because the "
		      "separator is one part in a thousand and a float round trip is of order 1e-7",
		      HS);
		Check(EveryTokenIsKeyValue(HS), "the held pin segment is space-free", HS);
		// REJECTING, PLANTED: the readback is the engine's own default range,
		// which is what a write that never reached the component looks like.
		LedgerVignette::ExposurePinIn Lost;
		Lost.Asked = 0.300; Lost.ReadMin = 0.0300; Lost.ReadMax = 8.0000;
		Lost.bOverMin = false; Lost.bOverMax = false; Lost.bRead = true; Lost.bSunOn = false;
		const std::string LS = LedgerVignette::ExposurePinSegment(Lost);
		std::printf("    planted: %s\n", LS.c_str());
		Check(LS.find("shotExposurePin=PINNED-DIFFERS") != std::string::npos
		      && LS.find("shotExposurePinRead=0.0300/8.0000") != std::string::npos
		      && LS.find("shotExposurePinResidual=-0.270000/+7.700000") != std::string::npos
		      && LS.find("shotExposurePinOverrides=0/0") != std::string::npos
		      && LS.find("shotExposurePinFamily=night") != std::string::npos,
		      "a pin that read back as the engine default is DIFFERS, with both signed "
		      "residuals printed, and HELD is not the word", LS);
		Check(!LedgerVignette::ExposurePinHeld(Lost)
		      && LedgerVignette::ExposurePinHeld(Held),
		      "the held test accepts the float round trip and refuses the default range, "
		      "which is the pair of outcomes rule 5b asks for");
		// AND A PIN THAT LANDED ON THE VALUES WITH THE OVERRIDES OFF IS STILL
		// NOT IN FORCE, which is the case a value-only comparison would pass.
		LedgerVignette::ExposurePinIn NoFlags = Held;
		NoFlags.bOverMin = false;
		Check(!LedgerVignette::ExposurePinHeld(NoFlags),
		      "a value that matches with its override flag off is not a pin in force, "
		      "because an unoverridden value is not the value the renderer uses");
		// AUTO, which is not a failure and must not read as one.
		LedgerVignette::ExposurePinIn Auto;
		Auto.Asked = 0.0; Auto.ReadMin = 0.0300; Auto.ReadMax = 8.0000;
		Auto.bRead = true; Auto.bSunOn = true;
		const std::string AS = LedgerVignette::ExposurePinSegment(Auto);
		Check(AS.find("shotExposurePin=AUTO") != std::string::npos
		      && AS.find("shotExposurePinResidual=not-applicable/no-pin-asked") != std::string::npos
		      && AS.find("shotExposurePinRead=0.0300/8.0000") != std::string::npos,
		      "a condition asking for no pin reads AUTO and prints the engine's own clamp "
		      "range rather than a residual against a number nobody asked for", AS);
		// AND NOTHING READ, which is not a zero.
		LedgerVignette::ExposurePinIn Never;
		Never.Asked = 3.0;
		const std::string NV = LedgerVignette::ExposurePinSegment(Never);
		Check(NV.find("shotExposurePin=NOT-READ") != std::string::npos
		      && NV.find("shotExposurePinRead=nothing-measured/nothing-measured") != std::string::npos
		      && NV.find("shotExposurePinResidual=nothing-measured") != std::string::npos,
		      "a placement that reached no camera component prints the words and never a "
		      "zero residual that would read as agreement", NV);
		Check(EveryTokenIsKeyValue(AS) && EveryTokenIsKeyValue(NV) && EveryTokenIsKeyValue(LS),
		      "the auto, not-read and planted pin segments are all space-free");
		// AND ALL FOUR CASES CARRY ONE KEY SET, WHICH IS THE DUPKEYS RULE AT
		// WRITE TIME. A key is ambiguous when it takes different values under
		// two different line SHAPES, and a file holding pinned rows and
		// unpinned rows holds both shapes. Counted rather than eyeballed.
		{
			std::vector<std::string> KH, KA, KN, KL;
			KeysOf(HS, KH); KeysOf(AS, KA); KeysOf(NV, KN); KeysOf(LS, KL);
			bool bSame = (KH.size() == KA.size() && KH.size() == KN.size()
			              && KH.size() == KL.size());
			for (size_t I = 0; bSame && I < KH.size(); ++I)
			{
				if (KH[I] != KA[I] || KH[I] != KN[I] || KH[I] != KL[I]) { bSame = false; }
			}
			std::printf("    pin segment keys: held=%d auto=%d notRead=%d planted=%d same=%s\n",
			            (int)KH.size(), (int)KA.size(), (int)KN.size(), (int)KL.size(),
			            bSame ? "yes" : "no");
			Check(bSame && KH.size() == 8,
			      "a pinned row, an unpinned row, a row that read nothing and a row whose pin "
			      "did not hold print the SAME eight keys in the same order, so no key on a "
			      "shot line is ambiguous across the shapes one file holds",
			      "the values say which case it is; the key names never move");
		}
		// ---- THE LADDER LINE, ACCEPTING CASE FIRST ----------------------
		//
		// TWO RUNGS, BOTH HALVES EACH, AND THE NUMBERS ARE THE 83dec33
		// READINGS so the expected difference is arithmetic rather than a
		// guess: the run's own first frame read 0.6102 and its repeat 0.9562,
		// a difference of 0.3460, and that pair is what the rung at the wrong
		// pin is expected to look like.
		std::vector<LedgerVignette::ExposureLadderSample> L;
		{
			LedgerVignette::ExposureLadderSample A;
			A.ShotId = "vign_pin_003_afterday"; A.Pin = 0.030; A.bAfterNight = false;
			A.bMeasured = true; A.bPinHeld = true; A.MeanLuma = 0.9562;
			A.ClipHi = 604972; A.ClipLo = 0; A.Pixels = 921600;
			L.push_back(A);
			LedgerVignette::ExposureLadderSample B;
			B.ShotId = "vign_pin_003_afternight"; B.Pin = 0.030; B.bAfterNight = true;
			B.bMeasured = true; B.bPinHeld = true; B.MeanLuma = 0.6102;
			B.ClipHi = 10283; B.ClipLo = 0; B.Pixels = 921600;
			L.push_back(B);
			LedgerVignette::ExposureLadderSample C;
			C.ShotId = "vign_pin_300_afterday"; C.Pin = 3.000; C.bAfterNight = false;
			C.bMeasured = true; C.bPinHeld = true; C.MeanLuma = 0.4010;
			C.ClipHi = 0; C.ClipLo = 12; C.Pixels = 921600;
			L.push_back(C);
			LedgerVignette::ExposureLadderSample D;
			D.ShotId = "vign_pin_300_afternight"; D.Pin = 3.000; D.bAfterNight = true;
			D.bMeasured = true; D.bPinHeld = true; D.MeanLuma = 0.4008;
			D.ClipHi = 0; D.ClipLo = 12; D.Pixels = 921600;
			L.push_back(D);
		}
		const std::string LL = LedgerVignette::ExposureLadderLine(L);
		std::printf("    %s\n", LL.c_str());
		Check(LL.find("ladderStatus=ALL") != std::string::npos
		      && LL.find("ladderRows=4/of=4/ladder-rows-offered") != std::string::npos
		      && LL.find("ladderPinsPaired=2/of=2/") != std::string::npos
		      && LL.find("ladderRowsHeld=4/of=4/") != std::string::npos,
		      "four rows over two rungs, both halves each, with every count shipping its "
		      "denominator", LL);
		Check(LL.find("ladder.pin0.0300.afterDayMinusAfterNightMeanLuma=+0.3460")
		      != std::string::npos
		      && LL.find("ladder.pin3.0000.afterDayMinusAfterNightMeanLuma=+0.0002")
		         != std::string::npos,
		      "the pairing prints as a signed DIFFERENCE per rung, and on the 83dec33 pair "
		      "it is the 0.3460 that run measured between one camera and its own repeat", LL);
		Check(LL.find("ladderSmallestDiffPin=3.0000") != std::string::npos
		      && LL.find("ladderSmallestDiff=0.0002") != std::string::npos
		      && LL.find("ladderVerdict=SERIES-ONLY/") != std::string::npos
		      && LL.find("ladderVerdict=CLEAR") == std::string::npos,
		      "the smallest difference is NAMED and nothing is called agreement, because no "
		      "bound on this difference has been measured yet", LL);
		Check(LL.find("ladder.pin0.0300.afterDayClipHi=604972/921600") != std::string::npos
		      && LL.find("ladder.pin3.0000.afterNightClipLo=12/921600") != std::string::npos,
		      "both clip counts ride the line with their denominators, because a mean cannot "
		      "see a blown frame and a pin chosen on the mean alone would crush or blow one "
		      "end of the run", LL);
		Check(EveryTokenIsKeyValue(LL), "the ladder line is space-free", LL);
		// REJECTING, PLANTED: A RUNG WITH ONE HALF IS NOT A RUNG.
		{
			std::vector<LedgerVignette::ExposureLadderSample> Half;
			Half.push_back(L[0]);
			const std::string HL = LedgerVignette::ExposureLadderLine(Half);
			std::printf("    planted: %s\n", HL.c_str());
			Check(HL.find("ladderPinsPaired=0/of=1/") != std::string::npos
			      && HL.find("ladder.pin0.0300.missing=the-after-night-half") != std::string::npos
			      && HL.find("ladder.pin0.0300.afterDayMinusAfterNightMeanLuma=nothing-measured")
			         != std::string::npos
			      && HL.find("ladderSmallestDiff=nothing-measured") != std::string::npos,
			      "a rung photographed only after a day frame names the half it is missing "
			      "and prints no difference, because a difference against an absent frame "
			      "would be a number with nothing in it", HL);
			Check(EveryTokenIsKeyValue(HL), "the half-rung ladder line is space-free", HL);
		}
		// AND A ROW THAT NEVER LANDED IS OUTSIDE THE MEASURED COUNT AND STILL
		// INSIDE THE DENOMINATOR, which is rule 3b.
		{
			std::vector<LedgerVignette::ExposureLadderSample> Lost2 = L;
			Lost2[1].bMeasured = false;
			const std::string XL = LedgerVignette::ExposureLadderLine(Lost2);
			Check(XL.find("ladderStatus=PARTIAL") != std::string::npos
			      && XL.find("ladderRows=3/of=4/ladder-rows-offered") != std::string::npos
			      && XL.find("ladderPinsPaired=1/of=2/") != std::string::npos,
			      "a row whose frame never landed leaves the measured count and stays in "
			      "the denominator, and its rung stops being paired", XL);
		}
		// AND A RUN WITH NO LADDER AT ALL SAYS SO.
		{
			std::vector<LedgerVignette::ExposureLadderSample> None2;
			const std::string ZL = LedgerVignette::ExposureLadderLine(None2);
			std::printf("    %s\n", ZL.c_str());
			Check(ZL.find("ladderStatus=NOTHING-MEASURED") != std::string::npos
			      && ZL.find("ladderRows=0/of=0/ladder-rows-offered") != std::string::npos
			      && ZL.find("ladderSmallestDiff=nothing-measured") != std::string::npos,
			      "a run that photographed no ladder row prints the words, and its zero "
			      "ships a denominator", ZL);
			Check(EveryTokenIsKeyValue(ZL), "the nothing-measured ladder line is space-free", ZL);
		}
		// ---- THE WHOLE-RUN PIN LINE, AND THE COST ON IT ------------------
		const std::string PD = LedgerVignette::ExposurePinDoneLine(8, 8, 37, 37);
		std::printf("    %s\n", PD.c_str());
		Check(PD.find("expPinStatus=ALL-HELD") != std::string::npos
		      && PD.find("expPinRowsAsking=8/of=37/shots-offered") != std::string::npos
		      && PD.find("expPinRowsHeld=8/of=8/shots-asking-for-a-pin") != std::string::npos
		      && PD.find("expPinConstantSet=no/") != std::string::npos,
		      "the run line carries the counts with their denominators and says in as many "
		      "words that no constant was set from this run", PD);
		Check(PD.find("expPinCost=a-pinned-frame-can-never-judge-an-adaptation-moment/"
		              "walking-out-of-a-dark-alley-is-the-example") != std::string::npos,
		      "and the cost of the pin is restated where a reader of the verdict meets it, "
		      "not only in a comment", PD);
		const std::string PZ = LedgerVignette::ExposurePinDoneLine(0, 0, 0, 0);
		Check(PZ.find("expPinStatus=NOTHING-MEASURED") != std::string::npos
		      && PZ.find("expPinStatus=ALL-HELD") == std::string::npos,
		      "a run that offered no shot is NOTHING-MEASURED and not all-held over zero", PZ);
		const std::string PP2 = LedgerVignette::ExposurePinDoneLine(8, 7, 37, 37);
		Check(PP2.find("expPinStatus=PARTIAL") != std::string::npos
		      && PP2.find("expPinRowsHeld=7/of=8/") != std::string::npos,
		      "one row of eight whose pin did not hold makes the run PARTIAL, which is the "
		      "reading a count without a denominator could not give", PP2);
		Check(EveryTokenIsKeyValue(PD) && EveryTokenIsKeyValue(PZ) && EveryTokenIsKeyValue(PP2),
		      "all three whole-run pin lines are space-free");
		// AND THE TWO LINES MAY NOT COLLIDE ON A KEY NAME, which is the
		// write-time half of the rule tools/verdict-dupkeys.py enforces at
		// read time. KEY NAMES AND NOT SUBSTRINGS: the run line's own prose
		// says it prints the ladder series only, and a substring test on the
		// word would refuse a line that shares no key at all.
		{
			std::vector<std::string> LK, PK;
			KeysOf(LL, LK);
			KeysOf(PD, PK);
			int Shared = 0;
			for (size_t A = 0; A < LK.size(); ++A)
			{
				for (size_t B = 0; B < PK.size(); ++B)
				{
					if (LK[A] == PK[B]) { ++Shared; }
				}
			}
			std::printf("    ladder keys=%d runLine keys=%d shared=%d\n",
			            (int)LK.size(), (int)PK.size(), Shared);
			Check(Shared == 0 && !LK.empty() && !PK.empty(),
			      "the ladder line and the run line share no key name over the keys each "
			      "carries, so a grep for either cannot return the other's value",
			      "and the zero ships both denominators");
		}
	}

	std::printf("%s: %d of %d check(s) failed\n",
	            gFailed == 0 ? "PASS" : "FAIL", gFailed, gChecks);
	return gFailed == 0 ? 0 : 1;
}
