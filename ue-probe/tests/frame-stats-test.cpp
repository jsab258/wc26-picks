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

	std::printf("frame-stats-test: %d check(s), %d failure(s)\n", Checks, Failures);
	return Failures == 0 ? 0 : 2;
}
