// THE SELFTEST FOR THE FRAME INSTRUMENT, ACCEPTING CASE FIRST.
//
// Rule 5b: a guard must be tested on the case it should PASS, and shipping
// it means having watched both outcomes. The expensive failure for a blank
// guard is not that it misses a black frame; it is that it rejects every
// frame and the probe reports BLANK for ever while the renderer works.
//
// WHY IT CAN RUN AT ALL. Nothing in FrameStats.h touches an Unreal type, so
// g++ compiles it in this container while the module around it cannot be
// compiled outside CI. That is the whole reason the maths lives there: a
// formatter that ships unrun and prints a plausible string is the quietest
// instrument fault there is.
//
//   g++ -std=c++17 -O0 -Wall -Wextra -o /tmp/frame-stats-test ue-probe/tests/frame-stats-test.cpp
//   /tmp/frame-stats-test
#include "../Source/LedgerProbe/Public/FrameStats.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <sstream>
#include <string>
#include <vector>

using namespace LedgerFrame;

static int Failures = 0;
static int Checks   = 0;

static void Check(bool Ok, const std::string& What)
{
	++Checks;
	if (!Ok) { ++Failures; std::printf("  FAIL %s\n", What.c_str()); }
	else     { std::printf("  ok   %s\n", What.c_str()); }
}

static bool Near(double A, double B) { return std::fabs(A - B) < 1e-6; }

// A frame of one colour, which is how a flat field and an all-black frame are
// both built.
static std::vector<unsigned char> Flat(int W, int H, unsigned char B,
                                       unsigned char G, unsigned char R)
{
	std::vector<unsigned char> Px((size_t)W * H * 4, 255);
	for (long long P = 0; P < (long long)W * H; ++P)
	{
		Px[P * 4] = B; Px[P * 4 + 1] = G; Px[P * 4 + 2] = R; Px[P * 4 + 3] = 255;
	}
	return Px;
}

// EVERY VALUE IN THE DONE LINE IS SPACE-FREE, checked mechanically rather
// than by eye. Every reader in this project splits on whitespace, so a value
// with a space in it truncates silently: the token count and the `=` count
// must agree, and each token must carry exactly one `=`.
static bool ValuesHaveNoSpaces(const std::string& Line)
{
	std::istringstream In(Line);
	std::string Tok;
	int Tokens = 0, Equals = 0;
	while (In >> Tok)
	{
		++Tokens;
		int E = 0;
		for (char C : Tok) { if (C == '=') { ++E; } }
		if (E != 1) { return false; }
		Equals += E;
	}
	return Tokens > 0 && Tokens == Equals;
}

int main()
{
	// ---- ACCEPTING CASE FIRST: a frame with content must read WROTE ----
	{
		const int W = 8, H = 4;
		std::vector<unsigned char> Px = Flat(W, H, 0, 0, 0);
		for (int Y = 0; Y < H; ++Y)
		{
			for (int X = 4; X < 8; ++X)
			{
				const long long I = ((long long)Y * W + X) * 4;
				Px[I] = 255; Px[I + 1] = 255; Px[I + 2] = 255;
			}
		}
		const FrameStats S = Measure(Px.data(), W, H);
		const std::string Line = DoneLine(S, "FScreenshotRequest::RequestScreenshot",
		                                  "ue-shot.png", 4242, 3.5, 118, "none");
		std::printf("accepting (half black, half white):\n  %s\n", Line.c_str());
		Check(!S.Blank, "a half-white frame is not blank");
		Check(S.Pixels == 32, "pixels counted 32");
		Check(S.NonBlack == 16, "16 non-black pixels");
		Check(Near(S.NonBlackPct, 50.0), "nonBlackPct 50.00 with 32 as its denominator");
		Check(Near(S.MeanLuma, 0.5), "meanLuma 0.5 over every pixel");
		Check(Near(S.MaxLuma, 1.0) && Near(S.MinLuma, 0.0), "min and max luma are the extremes");
		Check(S.DistinctBuckets == 2, "two colour buckets");
		Check(Line.find("shotStatus=WROTE") != std::string::npos, "status reads WROTE");
		Check(ValuesHaveNoSpaces(Line), "no value on the done line contains a space");
	}

	// ---- ACCEPTING, THE THIN CASE: one lit pixel is still a render ----
	{
		const int W = 100, H = 100;
		std::vector<unsigned char> Px = Flat(W, H, 0, 0, 0);
		Px[0] = 255; Px[1] = 255; Px[2] = 255;
		const FrameStats S = Measure(Px.data(), W, H);
		std::printf("accepting (one lit pixel of 10000): nonBlackPct=%.2f distinct=%d blank=%d\n",
		            S.NonBlackPct, S.DistinctBuckets, (int)S.Blank);
		Check(!S.Blank, "one non-black pixel in ten thousand is not blank");
		Check(Near(S.NonBlackPct, 0.01), "and its percentage is 0.01, not rounded to zero meaning");
	}

	// ---- REJECTING: an all-black frame ----
	{
		const int W = 16, H = 9;
		std::vector<unsigned char> Px = Flat(W, H, 0, 0, 0);
		const FrameStats S = Measure(Px.data(), W, H);
		const std::string Line = DoneLine(S, "HighResShot", "ue-shot.png", 900, 9.0, 40, "none");
		std::printf("rejecting (all black):\n  %s\n", Line.c_str());
		Check(S.Blank, "an all-black frame is blank");
		Check(S.NonBlack == 0 && S.Pixels == 144, "the zero ships its denominator: 0 of 144");
		Check(Line.find("shotStatus=BLANK") != std::string::npos, "status reads BLANK");
	}

	// ---- REJECTING, THE ONE A NON-BLACK CHECK ALONE WOULD PASS ----
	// A uniform grey frame has 129,600 non-black pixels and shows nothing.
	// This is the case that makes the distinct-bucket half of the rule earn
	// its place, and it is exactly what an offscreen render with no view
	// target can produce.
	{
		const int W = 480, H = 270;
		std::vector<unsigned char> Px = Flat(W, H, 128, 128, 128);
		const FrameStats S = Measure(Px.data(), W, H);
		const std::string Line = DoneLine(S, "HighResShot", "ue-shot.png", 5000, 9.0, 40, "none");
		std::printf("rejecting (uniform grey):\n  %s\n", Line.c_str());
		Check(S.NonBlack == S.Pixels, "every pixel is non-black, which is why the second half matters");
		Check(S.DistinctBuckets == 1, "one colour bucket");
		Check(S.Blank, "a uniform grey frame is blank");
		Check(Near(S.MeanLuma, 128.0 / 255.0), "the luma weights sum to one");
	}

	// ---- NOTHING MEASURED, IN WORDS ----
	{
		const FrameStats S = Measure(nullptr, 0, 0);
		const std::string Line = DoneLine(S, "NONE", "NONE", 0, 0.0, 0, "no-file-anywhere");
		std::printf("never-ran:\n  %s\n", Line.c_str());
		Check(Line.find("shotStatus=NOTHING-MEASURED") != std::string::npos,
		      "a frame with no pixels prints the words, never a clean zero");
		Check(S.Pixels == 0, "and its pixel count is zero");
		Check(ValuesHaveNoSpaces(Line), "the never-ran line is space-free too");
	}

	// ---- THE ASCII DUMP, WHICH IS THE ONLY VIEW A BLIND CHANNEL GETS ----
	{
		const int W = 96, H = 54;
		std::vector<unsigned char> Px = Flat(W, H, 0, 0, 0);
		for (int Y = 20; Y < 34; ++Y)
		{
			for (int X = 30; X < 66; ++X)
			{
				const long long I = ((long long)Y * W + X) * 4;
				Px[I] = 255; Px[I + 1] = 255; Px[I + 2] = 255;
			}
		}
		const std::string Art = AsciiLuma(Px.data(), W, H);
		int Lines = 1, Lit = 0;
		for (char C : Art) { if (C == '\n') { ++Lines; } if (C == '@') { ++Lit; } }
		std::printf("ascii-luma of a centred white block:\n%s\n", Art.c_str());
		Check(Lines == 27, "27 rows");
		Check(Art.rfind("# ", 0) == 0, "every row is a comment row so no reader parses it");
		Check(Lit > 0, "the block shows up in the dump");
		const std::string Empty = AsciiLuma(nullptr, 0, 0);
		Check(Empty.find("nothing measured") != std::string::npos,
		      "and a dump with no pixels says nothing measured");
	}

	// ---- PixelLine, the per-sample half (Phase B) ----------------------
	//
	// Four shots in one run means four sample lines, and the whole-run keys
	// on DoneLine would be printed four times as if each were that shot's.
	// This line must carry the pixel statistics and NOT those keys.
	{
		unsigned char Px[16];
		for (int I = 0; I < 4; ++I)
		{
			Px[I * 4 + 0] = (unsigned char)(I * 60);
			Px[I * 4 + 1] = (unsigned char)(I * 40);
			Px[I * 4 + 2] = (unsigned char)(I * 20);
			Px[I * 4 + 3] = 255;
		}
		const LedgerFrame::FrameStats S = LedgerFrame::Measure(Px, 2, 2);
		const std::string L = LedgerFrame::PixelLine(S);
		std::printf("    %s\n", L.c_str());
		Check(L.find("shotSecondsWaited") == std::string::npos
		      && L.find("shotTicks") == std::string::npos,
		      "the per-sample line carries no whole-run key that would be a lie on four lines");
		Check(L.find("shotDistinctBuckets=") != std::string::npos
		      && L.find("/32768") != std::string::npos,
		      "and it carries the bucket count with its denominator");
		Check(L.find("shotBlank=no") != std::string::npos,
		      "a frame with four different colours is not blank");
		const LedgerFrame::FrameStats Flat = LedgerFrame::Measure(Px, 0, 0);
		const std::string FL = LedgerFrame::PixelLine(Flat);
		Check(FL.find("shotBlank=NOTHING-MEASURED") != std::string::npos,
		      "and a frame with no pixels says nothing measured rather than blank");
		// NO SPACE INSIDE ANY VALUE, which is the fault that truncates every
		// reader in this project silently.
		int Pairs = 0, Bad = 0;
		std::string Tok;
		for (size_t I = 0; I <= L.size(); ++I)
		{
			if (I == L.size() || L[I] == ' ')
			{
				const size_t Eq = Tok.find('=');
				if (Eq != std::string::npos) { ++Pairs; if (Eq + 1 >= Tok.size()) ++Bad; }
				Tok.clear();
			}
			else { Tok += L[I]; }
		}
		std::printf("    pixel line: keyValuePairs=%d emptyValues=%d/%d\n", Pairs, Bad, Pairs);
		Check(Pairs >= 9 && Bad == 0, "every key on the per-sample line carries a value");
	}


	// ---- QUEUE 059 (b): CLIPPING, ACCEPTING CASE FIRST -----------------
	//
	// The accepting case for an exposure instrument is not a blown frame. It
	// is a frame with a KNOWN amount of clipping in it, counted exactly, so
	// that a run reading 13.4% blown is believed and a run reading 0.00% is
	// known to have looked. Rule 5b: the case it should pass, first.
	{
		const int W = 8, H = 4;              // 32 pixels, half of them white
		std::vector<unsigned char> Px = Flat(W, H, 128, 128, 128);
		for (int Y = 0; Y < H; ++Y)
		{
			for (int X = 4; X < W; ++X)
			{
				const size_t I = ((size_t)Y * W + X) * 4;
				Px[I] = 255; Px[I + 1] = 255; Px[I + 2] = 255;
			}
		}
		const ExposureStats E = MeasureExposure(Px.data(), W, H);
		Check(E.Measured && E.Pixels == 32, "exposure measured 32 pixels and says so");
		Check(E.ClipHiAll == 16, "sixteen pixels at 255 on all three channels are counted");
		Check(E.ClipHiAny == 16, "and the any-channel count agrees when the clip is white");
		Check(E.ClipLoAll == 0, "nothing is at the bottom of the range in this frame");
		Check(E.Bands[7] == 16 && E.Bands[4] == 16,
		      "the eight luma bands put the white half at the top and the grey half mid");
		long long BandSum = 0;
		for (int I = 0; I < 8; ++I) { BandSum += E.Bands[I]; }
		Check(BandSum == E.Pixels, "the bands account for every pixel, which is their denominator");
		const std::string L = ExposureLine(E);
		std::printf("    %s\n", L.c_str());
		Check(L.find("shotClipHiAll=16/32") != std::string::npos,
		      "the clip count ships with its denominator and never as a mean");
		Check(L.find("shotClipHiAllPct=50.00") != std::string::npos,
		      "and the percentage beside it");
		Check(L.find("shotLumaBandStat=") != std::string::npos,
		      "the line is not truncated: its last key is present");
		Check(ValuesHaveNoSpaces(L), "every exposure value is space-free and carries one equals");
	}
	// ONE CHANNEL AT THE TOP IS STILL CLIPPING, and the two counts are what
	// separate a blown white ground from a saturated sodium lamp.
	{
		const int W = 4, H = 2;
		std::vector<unsigned char> Px = Flat(W, H, 50, 100, 255);
		const ExposureStats E = MeasureExposure(Px.data(), W, H);
		Check(E.ClipHiAny == 8 && E.ClipHiAll == 0,
		      "a red channel at 255 counts as any-clip and not as white-clip");
	}
	// THE CRUSHED END, AND THE COMPLEMENT CLAIM IN ITS OWN RULE STRING
	// CHECKED RATHER THAN ASSERTED: shotClipLoAll is shotPixels minus
	// shotNonBlackPixels, which is what the printed rule says it is.
	{
		const int W = 6, H = 3;
		std::vector<unsigned char> Px = Flat(W, H, 0, 0, 0);
		for (size_t I = 0; I < 4; ++I) { Px[I * 4 + 1] = 9; }
		const ExposureStats E = MeasureExposure(Px.data(), W, H);
		const FrameStats S = Measure(Px.data(), W, H);
		Check(E.ClipLoAll == S.Pixels - S.NonBlack,
		      "the low-clip count equals pixels minus non-black, as its rule string claims");
		Check(E.Bands[0] == 18, "and a near-black frame puts every pixel in the darkest band");
	}
	// AND NOTHING MEASURED SAYS THE WORDS. Eight zeros with denominators
	// would read as a frame that was examined and found clean.
	{
		const std::string L = ExposureLine(MeasureExposure(nullptr, 0, 0));
		Check(L.find("shotClipStatus=NOTHING-MEASURED") != std::string::npos
		      && L.find("shotClipHiAny=") == std::string::npos,
		      "an undecoded frame prints nothing-measured and no clean-looking zeros");
	}

	// ---- QUEUE 059 (a): PER-LIGHT CONTRIBUTION, ACCEPTING CASE FIRST ----
	//
	// The accepting case is a pair that DIFFERS by a known amount in a known
	// place: right half brighter by 51 code values, which is a luma rise of
	// 0.2 exactly. If this instrument cannot see that, no reading it takes of
	// a real lantern means anything.
	{
		const int W = 8, H = 4;
		std::vector<unsigned char> Off = Flat(W, H, 10, 10, 10);
		std::vector<unsigned char> On  = Off;
		for (int Y = 0; Y < H; ++Y)
		{
			for (int X = 4; X < W; ++X)
			{
				const size_t I = ((size_t)Y * W + X) * 4;
				On[I] = 61; On[I + 1] = 61; On[I + 2] = 61;
			}
		}
		const LightDelta D = MeasureLightDelta(On.data(), Off.data(), W, H);
		Check(D.Comparable && D.Pixels == 32, "the pair is comparable and 32 pixels wide");
		Check(Near(D.MaxRise, 51.0 / 255.0), "the largest single-pixel rise is the one planted");
		Check(Near(D.MeanDeltaFull, 0.5 * 51.0 / 255.0),
		      "half the frame rising by 0.2 is a whole-frame mean delta of 0.1");
		Check(D.RoseAtLeast[0] == 16 && D.RoseAtLeast[5] == 16,
		      "all sixteen lit pixels clear every code edge up to 32");
		Check(D.PixelsDarkerWithLightOn == 0,
		      "and no pixel got darker with the light on, so no auto-exposure is suspected");
		Check(D.PeakCol == 4 && D.PeakRow == 0,
		      "the peak region is named as a grid cell and it is in the half that changed");
		Check(Near(D.PeakMeanOn - D.PeakMeanOff, D.PeakMeanDelta),
		      "the peak's two halves are that region's own means, captured where it peaks");
		const std::string L = LightDeltaLine("lantern_02", "lantern", 2, 4, "vign_camB_night",
		                                     "cam_B", "wet_night", "MEASURED", D, "");
		std::printf("    %s\n", L.c_str());
		Check(L.find("peakRegion=c4r0/of8x4") != std::string::npos
		      && L.find("peakRegionPx=x4..5/y0..1") != std::string::npos,
		      "the sample region is named in the line, in cells and in pixels");
		Check(L.find("deltaPixelsOf=32") != std::string::npos,
		      "the histogram ships its denominator");
		Check(L.find("lightDeltaNote=none") != std::string::npos,
		      "the line is not truncated: its last key is present");
		// The two leading tokens are the line's kind and the light's id, as
		// on the shot line; everything after them is key=value.
		const size_t Cut = L.find("kind=");
		Check(Cut != std::string::npos && ValuesHaveNoSpaces(L.substr(Cut)),
		      "every light value is space-free and carries one equals");
	}
	// THE CONTROL: TWO FRAMES OF THE SAME SCENE WITH NOTHING TOGGLED. This is
	// the run's own noise floor and the reason no epsilon had to be invented.
	// A zero here must still print its denominator.
	{
		const int W = 8, H = 4;
		std::vector<unsigned char> A = Flat(W, H, 30, 40, 50);
		const LightDelta D = MeasureLightDelta(A.data(), A.data(), W, H);
		Check(Near(D.MeanDeltaFull, 0.0) && D.RoseAtLeast[0] == 0,
		      "an untouched pair reads zero rise, which is what a control must read");
		const std::string L = LightDeltaLine("control_no_toggle", "control", 0, 0,
		                                     "vign_camB_night", "cam_B", "wet_night",
		                                     "MEASURED", D, "");
		Check(L.find("deltaPixelsRoseAtLeast=0/0/0/0/0/0") != std::string::npos
		      && L.find("deltaPixelsOf=32") != std::string::npos,
		      "the control's zeros ship the count of what was examined");
	}
	// A LIGHT THAT MAKES PIXELS DARKER IS THE AUTO-EXPOSURE TELL, and it is
	// counted rather than clamped away.
	{
		const int W = 4, H = 4;
		std::vector<unsigned char> Off = Flat(W, H, 90, 90, 90);
		std::vector<unsigned char> On  = Flat(W, H, 80, 80, 80);
		const LightDelta D = MeasureLightDelta(On.data(), Off.data(), W, H);
		Check(D.PixelsDarkerWithLightOn == 16 && D.MaxRise == 0.0,
		      "every pixel darker with the light on is counted, and no rise is invented");
	}
	// AND A PAIR THAT IS NOT A PAIR SAYS SO. A missing half is not a light
	// that contributed nothing.
	{
		const LightDelta D = MeasureLightDelta(nullptr, nullptr, 0, 0);
		const std::string L = LightDeltaLine("lantern_01", "lantern", 1, 4, "vign_camA_night",
		                                     "cam_A", "wet_night", "NO-FILE", D,
		                                     "probe-frame-never-arrived");
		Check(!D.Comparable && L.find("lightDelta=NOTHING-MEASURED") != std::string::npos
		      && L.find("lightStatus=NO-FILE") != std::string::npos,
		      "an absent probe frame prints nothing measured and keeps its own reason");
	}
	// THE RUN SUMMARY. A pass that probed nothing may not read as a pass, and
	// the budget must be visible from the line when it bites.
	{
		const std::string L = LightProbeDoneLine(0, 7, 0, 0, 0, 0, 0, 0, 2, 90.0, 0.0, 32, 0);
		Check(L.find("lightProbeStatus=NOTHING-MEASURED") != std::string::npos,
		      "a light pass that probed nothing says nothing measured");
		const std::string M = LightProbeDoneLine(5, 7, 4, 1, 1, 0, 0, 2, 2, 90.0, 61.5, 32, 2);
		std::printf("    %s\n", M.c_str());
		Check(M.find("lightProbeStatus=PARTIAL-BUDGET-BIT") != std::string::npos
		      && M.find("lightsSkippedBudget=1") != std::string::npos,
		      "and a budget that bit announces itself with the count it cost");
		Check(M.find("lightsReachedFrame=4/5") != std::string::npos,
		      "reached-frame is over the number probed, not over the number of lights");
		Check(ValuesHaveNoSpaces(M), "every light-pass value is space-free");
	}

	std::printf("frame-stats-test: %d check(s), %d failure(s)\n", Checks, Failures);
	return Failures == 0 ? 0 : 2;
}
