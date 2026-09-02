// WHAT A FRAME MEASURES, IN A FILE THAT COMPILES WITHOUT UNREAL.
//
// THE RULE THIS EXISTS FOR, ruled standing on 25 August after the third
// instance: measurement arithmetic and formatting live where the tests run.
// In a project whose top layer does not compile locally, a formatter written
// there ships UNRUN, and an unrun formatter printing a plausible string is
// the silent-instrument failure. So the tally, the maths and the string are
// here, in plain C++ with no engine type anywhere in it, and
// ue-probe/tests/frame-stats-test.cpp compiles and runs them with g++ before
// anything is dispatched. The Unreal module supplies only the pixels.
//
// THE WEIGHTS ARE THE UNITY SIM'S WEIGHTS, deliberately. SimDirector.cs reads
// meanLuma as (0.299R + 0.587G + 0.114B) / 255 over every pixel, and D1 is a
// comparison: a UE frame measured by a different ruler would not be
// comparable to the Unity frames sitting in game-design/sim-shots.
//
// WHAT EACH NUMBER IS A STATISTIC OF, said once, here, and repeated into the
// verdict as comment lines:
//   MeanLuma        mean over EVERY pixel of the decoded image, 0 to 1
//   MinLuma/MaxLuma extremes over that same pixel set
//   NonBlack        count of pixels with ANY channel above zero
//   NonBlackPct     that count over Pixels, which is its denominator
//   DistinctBuckets distinct 5-bit-per-channel colour buckets, out of 32768
//
// THE BLANK RULE IS A STRUCTURAL ZERO, NOT A TUNED BOUND. One colour bucket
// over a whole frame means a flat field; no non-black pixel means the
// renderer put nothing there. Neither number was chosen from a series, which
// is why they may be set before one exists. Any bound on how BRIGHT a frame
// ought to be waits for the series these functions print.
#pragma once

#include <cstdio>
#include <string>
#include <vector>

namespace LedgerFrame
{
	struct FrameStats
	{
		int       Width           = 0;
		int       Height          = 0;
		long long Pixels          = 0;
		long long NonBlack        = 0;
		double    MeanLuma        = 0.0;
		double    MinLuma         = 0.0;
		double    MaxLuma         = 0.0;
		double    NonBlackPct     = 0.0;
		int       DistinctBuckets = 0;
		// True for a frame with one colour bucket or no non-black pixel, AND
		// true for a frame with no pixels at all: nothing measured is not the
		// same as measured and fine, and neither may read as a pass.
		bool      Blank           = true;
	};

	inline double Luma(unsigned char R, unsigned char G, unsigned char B)
	{
		return (0.299 * R + 0.587 * G + 0.114 * B) / 255.0;
	}

	// BGRA8, top row first, which is what IImageWrapper::GetRaw returns for
	// ERGBFormat::BGRA at 8 bits. Named in the parameter rather than assumed
	// in the caller.
	inline FrameStats Measure(const unsigned char* Bgra, int W, int H)
	{
		FrameStats S;
		S.Width = W;
		S.Height = H;
		if (Bgra == nullptr || W <= 0 || H <= 0)
		{
			return S;  // Pixels stays 0 and Blank stays true: nothing measured.
		}
		S.Pixels = (long long)W * (long long)H;
		std::vector<unsigned char> Seen(32768, 0);
		double Sum = 0.0;
		double Mn = 1.0;
		double Mx = 0.0;
		for (long long P = 0; P < S.Pixels; ++P)
		{
			const unsigned char B = Bgra[P * 4];
			const unsigned char G = Bgra[P * 4 + 1];
			const unsigned char R = Bgra[P * 4 + 2];
			const double L = Luma(R, G, B);
			Sum += L;
			if (L < Mn) { Mn = L; }
			if (L > Mx) { Mx = L; }
			if (R > 0 || G > 0 || B > 0) { ++S.NonBlack; }
			const int Bucket = ((R >> 3) << 10) | ((G >> 3) << 5) | (B >> 3);
			if (Seen[Bucket] == 0) { Seen[Bucket] = 1; ++S.DistinctBuckets; }
		}
		S.MeanLuma    = Sum / (double)S.Pixels;
		S.MinLuma     = Mn;
		S.MaxLuma     = Mx;
		S.NonBlackPct = 100.0 * (double)S.NonBlack / (double)S.Pixels;
		S.Blank       = (S.DistinctBuckets <= 1) || (S.NonBlack == 0);
		return S;
	}

	// THE DONE LINE. Whole-run numbers, one moment, one line, and NO SPACES
	// INSIDE ANY VALUE: every reader in this project splits on whitespace and
	// truncates silently when a value contains one. Structure goes in `/`.
	inline std::string DoneLine(const FrameStats& S,
	                            const std::string& Attempt,
	                            const std::string& File,
	                            long long Bytes,
	                            double SecondsWaited,
	                            int Ticks,
	                            const std::string& Note)
	{
		char Buf[768];
		std::snprintf(Buf, sizeof(Buf),
			"shotStatus=%s shotAttempt=%s shotFile=%s shotBytes=%lld shotW=%d shotH=%d "
			"shotPixels=%lld shotMeanLuma=%.4f shotMinLuma=%.4f shotMaxLuma=%.4f "
			"shotNonBlackPixels=%lld shotNonBlackPct=%.2f shotDistinctBuckets=%d/32768 "
			"shotSecondsWaited=%.2f shotTicks=%d shotNote=%s",
			S.Pixels == 0 ? "NOTHING-MEASURED" : (S.Blank ? "BLANK" : "WROTE"),
			Attempt.c_str(), File.c_str(), Bytes, S.Width, S.Height,
			S.Pixels, S.MeanLuma, S.MinLuma, S.MaxLuma,
			S.NonBlack, S.NonBlackPct, S.DistinctBuckets,
			SecondsWaited, Ticks, Note.c_str());
		return std::string(Buf);
	}

	// THE PICTURE IN WORDS, for a channel that cannot open a PNG. The same
	// ascii-luma dump the Unity sim writes beside its stills: a reader with
	// nothing but the verdict file can still tell a lit frame from an empty
	// one. Every row is prefixed so no key reader ever parses it as data.
	inline std::string AsciiLuma(const unsigned char* Bgra, int W, int H,
	                             int Cols = 48, int Rows = 27)
	{
		if (Bgra == nullptr || W <= 0 || H <= 0 || Cols <= 0 || Rows <= 0)
		{
			return std::string("# ascii-luma: nothing measured, no pixels to draw");
		}
		static const char* Ramp = " .:-=+*#%@";
		const int RampN = 10;
		std::string Art;
		Art.reserve((size_t)(Cols + 3) * Rows);
		for (int Ry = 0; Ry < Rows; ++Ry)
		{
			Art += "# ";
			const int Y0 = (Ry * H) / Rows;
			int Y1 = ((Ry + 1) * H) / Rows;
			if (Y1 <= Y0) { Y1 = Y0 + 1; }
			for (int Rx = 0; Rx < Cols; ++Rx)
			{
				const int X0 = (Rx * W) / Cols;
				int X1 = ((Rx + 1) * W) / Cols;
				if (X1 <= X0) { X1 = X0 + 1; }
				double Sum = 0.0;
				int N = 0;
				for (int Y = Y0; Y < Y1 && Y < H; ++Y)
				{
					for (int X = X0; X < X1 && X < W; ++X)
					{
						const long long I = ((long long)Y * W + X) * 4;
						Sum += Luma(Bgra[I + 2], Bgra[I + 1], Bgra[I]);
						++N;
					}
				}
				const double L = (N > 0 ? Sum / N : 0.0);
				int Idx = (int)(L * (RampN - 1) + 0.5);
				if (Idx < 0) { Idx = 0; }
				if (Idx > RampN - 1) { Idx = RampN - 1; }
				Art += Ramp[Idx];
			}
			if (Ry + 1 < Rows) { Art += "\n"; }
		}
		return Art;
	}
}
