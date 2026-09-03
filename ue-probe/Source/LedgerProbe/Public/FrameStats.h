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

	// THE SAME PIXEL NUMBERS, FOR A LINE THAT DESCRIBES ONE SAMPLE.
	//
	// DoneLine above carries whole-run keys, `shotSecondsWaited` and
	// `shotTicks`, which are true of a RUN and not of a frame. Phase B takes
	// four frames in one run, so putting DoneLine on each of them would
	// print the run's elapsed time four times as if it were each shot's, and
	// the project's rule is that whole-run numbers sit on the done line and
	// per-sample numbers on the sample line. This is the per-sample half:
	// everything here is a statistic of THIS image and nothing else.
	//
	// Every number keeps the name it has on the done line, because a reader
	// comparing a Phase B frame to run 16's single frame should not have to
	// learn two vocabularies for one measurement.
	inline std::string PixelLine(const FrameStats& S)
	{
		char Buf[512];
		std::snprintf(Buf, sizeof(Buf),
			"shotW=%d shotH=%d shotPixels=%lld shotMeanLuma=%.4f shotMinLuma=%.4f "
			"shotMaxLuma=%.4f shotNonBlackPixels=%lld shotNonBlackPct=%.2f "
			"shotDistinctBuckets=%d/32768 shotBlank=%s",
			S.Width, S.Height, S.Pixels, S.MeanLuma, S.MinLuma, S.MaxLuma,
			S.NonBlack, S.NonBlackPct, S.DistinctBuckets,
			S.Pixels == 0 ? "NOTHING-MEASURED" : (S.Blank ? "yes" : "no"));
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

// ============================================================================
// QUEUE 059: A PLACED LANTERN IS NOT A LIT STREET.
//
// Run 17's scene line read lanternsPlaced=4/4 and every word of it was true.
// It answers "were four lantern lights created". It was never asked "did any
// of them reach a pixel", and both night frames were almost black. At the
// other end of the range shotMeanLuma=0.5030 sat over a day frame whose whole
// ground plane was clipped to flat white, because a mean cannot see clipping.
//
// So there are two measurements below and they live here, in the file g++
// compiles, for the standing reason: an unrun formatter printing a plausible
// string is the quietest instrument fault this project has.
//
// NO BOUND IS SET IN THIS FILE. Every number here is a printer. The counts
// are structural (a channel at 255 is at the top of the 8-bit range; a code
// value of 1 is the quantisation floor) and the histogram edges are powers of
// two, so that a bound can be read off a real series later rather than
// invented now.
// ============================================================================

namespace LedgerFrame
{
	// ---- (b) WHAT THE TONE MAPPER DID, AS COUNTS WITH DENOMINATORS -------
	//
	// Every field is a COUNT over Pixels, never a mean. shotMeanLuma=0.5030
	// and a fully clipped ground plane are the same reading, which is rule
	// 3b's shape: a healthy summary over a population that is not healthy.
	struct ExposureStats
	{
		bool      Measured  = false;   // false means no pixels, not "clean"
		long long Pixels    = 0;
		// Pixels with ANY 8-bit channel at 255. A sodium lamp clipping only
		// its red channel is clipping, and the all-three count below is what
		// separates that from a blown white ground.
		long long ClipHiAny = 0;
		long long ClipHiAll = 0;
		// All three channels at zero. This is the exact complement of
		// FrameStats::NonBlack and is printed anyway, with the complement
		// named in its rule, so that a reader asking about the bottom of the
		// range does not have to do the subtraction and does not read it as a
		// second independent number.
		long long ClipLoAll = 0;
		// EIGHT EQUAL LUMA BANDS OVER 0..1, which is a printed series and not
		// a threshold. Band 0 is the crushed end, band 7 the blown end.
		long long Bands[8]  = {0, 0, 0, 0, 0, 0, 0, 0};
	};

	inline ExposureStats MeasureExposure(const unsigned char* Bgra, int W, int H)
	{
		ExposureStats E;
		if (Bgra == nullptr || W <= 0 || H <= 0) { return E; }
		E.Measured = true;
		E.Pixels = (long long)W * (long long)H;
		for (long long P = 0; P < E.Pixels; ++P)
		{
			const unsigned char B = Bgra[P * 4];
			const unsigned char G = Bgra[P * 4 + 1];
			const unsigned char R = Bgra[P * 4 + 2];
			if (R == 255 || G == 255 || B == 255) { ++E.ClipHiAny; }
			if (R == 255 && G == 255 && B == 255) { ++E.ClipHiAll; }
			if (R == 0 && G == 0 && B == 0)       { ++E.ClipLoAll; }
			int Band = (int)(Luma(R, G, B) * 8.0);
			if (Band < 0) { Band = 0; }
			if (Band > 7) { Band = 7; }
			++E.Bands[Band];
		}
		return E;
	}

	inline double Pct(long long Part, long long Of)
	{
		return Of > 0 ? (100.0 * (double)Part / (double)Of) : 0.0;
	}

	// PER-SAMPLE KEYS ONLY: everything here is a statistic of THIS image.
	// A frame with no pixels prints the words rather than eight zeros that
	// would read as a clean exposure.
	inline std::string ExposureLine(const ExposureStats& E)
	{
		if (!E.Measured || E.Pixels == 0)
		{
			return std::string("shotClipStatus=NOTHING-MEASURED "
			                   "shotClipNote=no-pixels-decoded/nothing-examined");
		}
		char Buf[1200];
		std::snprintf(Buf, sizeof(Buf),
			"shotClipStatus=MEASURED "
			"shotClipHiAny=%lld/%lld shotClipHiAnyPct=%.2f shotClipHiAnyRule=any8bitRGB-at-255 "
			"shotClipHiAll=%lld/%lld shotClipHiAllPct=%.2f shotClipHiAllRule=all8bitRGB-at-255 "
			"shotClipLoAll=%lld/%lld shotClipLoAllPct=%.2f "
			"shotClipLoAllRule=all8bitRGB-at-0/complement-of-shotNonBlackPixels "
			"shotLumaBands=%lld/%lld/%lld/%lld/%lld/%lld/%lld/%lld shotLumaBandsOf=%lld "
			"shotLumaBandEdges=0..1/8equal shotLumaBandStat=pixel-count-per-band/band0-is-darkest",
			E.ClipHiAny, E.Pixels, Pct(E.ClipHiAny, E.Pixels),
			E.ClipHiAll, E.Pixels, Pct(E.ClipHiAll, E.Pixels),
			E.ClipLoAll, E.Pixels, Pct(E.ClipLoAll, E.Pixels),
			E.Bands[0], E.Bands[1], E.Bands[2], E.Bands[3],
			E.Bands[4], E.Bands[5], E.Bands[6], E.Bands[7], E.Pixels);
		return std::string(Buf);
	}

	// ---- (a) DID THIS LIGHT REACH A PIXEL --------------------------------
	//
	// A CONTRIBUTION IS A DIFFERENCE AND NEEDS BOTH HALVES NAMED: the same
	// camera, the same condition, the same frame counts, one light toggled,
	// and the sample region stated. A lantern lighting the far end of the
	// street contributes nothing to a crop of the near end and that is not a
	// failure, so the region this reads is printed beside the number.
	//
	// THE REGION IS A FIXED NAMED GRID, cols by rows over the frame. The
	// whole-frame reading is named `full`; the peak tile is named `cXrY`
	// with its pixel rectangle, so both halves of the difference are
	// attributable to the same rectangle without opening the image.
	//
	// THE CODE-VALUE HISTOGRAM IS A SERIES, NOT A BOUND. Counts of pixels
	// whose luma ROSE by at least 1, 2, 4, 8, 16 and 32 eight-bit code
	// values when the light was on. Powers of two, so no number here was
	// chosen; a bound comes later from real runs. Temporal antialiasing and
	// dither move pixels by a code value or two on their own, which is why
	// the caller is expected to run a CONTROL probe that toggles nothing:
	// the control's histogram is this run's own noise floor and no invented
	// epsilon is needed.
	struct LightDelta
	{
		bool      Comparable = false;   // two decoded frames of equal size
		int       Width = 0, Height = 0;
		long long Pixels = 0;
		double    MeanOnFull = 0.0, MeanOffFull = 0.0, MeanDeltaFull = 0.0;
		double    MaxRise = 0.0;        // largest single-pixel luma rise
		double    MaxDrop = 0.0;        // largest single-pixel luma fall
		// Pixels that got BRIGHTER with the light OFF. Physically impossible
		// for a light in isolation, so a non-trivial count here is the
		// auto-exposure compensating and the whole difference is suspect.
		long long PixelsDarkerWithLightOn = 0;
		static const int Edges = 6;     // 1,2,4,8,16,32 code values
		long long RoseAtLeast[6] = {0, 0, 0, 0, 0, 0};
		int       Cols = 0, Rows = 0;
		int       PeakCol = -1, PeakRow = -1;
		int       PeakX0 = 0, PeakX1 = 0, PeakY0 = 0, PeakY1 = 0;
		double    PeakMeanDelta = 0.0, PeakMeanOn = 0.0, PeakMeanOff = 0.0;
	};

	inline int DeltaCodeEdge(int I)
	{
		const int E[6] = {1, 2, 4, 8, 16, 32};
		return (I >= 0 && I < 6) ? E[I] : 0;
	}

	// On and Off are BGRA8 buffers of the SAME dimensions, top row first.
	// Different dimensions is not a small problem to paper over: it means the
	// two halves are not the same frame and Comparable stays false.
	inline LightDelta MeasureLightDelta(const unsigned char* On, const unsigned char* Off,
	                                    int W, int H, int Cols = 8, int Rows = 4)
	{
		LightDelta D;
		if (On == nullptr || Off == nullptr || W <= 0 || H <= 0 || Cols <= 0 || Rows <= 0)
		{
			return D;
		}
		D.Comparable = true;
		D.Width = W; D.Height = H;
		D.Pixels = (long long)W * (long long)H;
		D.Cols = Cols; D.Rows = Rows;
		std::vector<double> TileOn((size_t)Cols * Rows, 0.0);
		std::vector<double> TileOff((size_t)Cols * Rows, 0.0);
		std::vector<long long> TileN((size_t)Cols * Rows, 0);
		double SumOn = 0.0, SumOff = 0.0;
		for (int Y = 0; Y < H; ++Y)
		{
			int Ty = (Y * Rows) / H;
			if (Ty >= Rows) { Ty = Rows - 1; }
			for (int X = 0; X < W; ++X)
			{
				const long long I = ((long long)Y * W + X) * 4;
				const double LOn  = Luma(On[I + 2], On[I + 1], On[I]);
				const double LOff = Luma(Off[I + 2], Off[I + 1], Off[I]);
				const double Rise = LOn - LOff;
				SumOn += LOn; SumOff += LOff;
				if (Rise > D.MaxRise) { D.MaxRise = Rise; }
				if (-Rise > D.MaxDrop) { D.MaxDrop = -Rise; }
				if (Rise < 0.0) { ++D.PixelsDarkerWithLightOn; }
				const double Codes = Rise * 255.0;
				for (int E = 0; E < LightDelta::Edges; ++E)
				{
					// The edges climb, so the first one not met ends it.
					if (Codes >= (double)DeltaCodeEdge(E) - 1e-9) { ++D.RoseAtLeast[E]; }
					else { break; }
				}
				int Tx = (X * Cols) / W;
				if (Tx >= Cols) { Tx = Cols - 1; }
				const size_t T = (size_t)Ty * Cols + Tx;
				TileOn[T] += LOn; TileOff[T] += LOff; ++TileN[T];
			}
		}
		D.MeanOnFull    = SumOn / (double)D.Pixels;
		D.MeanOffFull   = SumOff / (double)D.Pixels;
		D.MeanDeltaFull = D.MeanOnFull - D.MeanOffFull;
		// THE PEAK TILE, AND ITS TWO HALVES CAPTURED AT THE SAME INSTANT it
		// peaks: the on and off means printed beside it are that tile's, not
		// the frame's, so the number and its denominator describe one region.
		double Best = 0.0;
		for (int Ry = 0; Ry < Rows; ++Ry)
		{
			for (int Rx = 0; Rx < Cols; ++Rx)
			{
				const size_t T = (size_t)Ry * Cols + Rx;
				if (TileN[T] <= 0) { continue; }
				const double MOn  = TileOn[T] / (double)TileN[T];
				const double MOff = TileOff[T] / (double)TileN[T];
				const double Dl   = MOn - MOff;
				if (D.PeakCol < 0 || Dl > Best)
				{
					Best = Dl;
					D.PeakCol = Rx; D.PeakRow = Ry;
					D.PeakMeanDelta = Dl; D.PeakMeanOn = MOn; D.PeakMeanOff = MOff;
					D.PeakX0 = (Rx * W) / Cols; D.PeakX1 = ((Rx + 1) * W) / Cols;
					D.PeakY0 = (Ry * H) / Rows; D.PeakY1 = ((Ry + 1) * H) / Rows;
				}
			}
		}
		return D;
	}

	// ONE LINE PER PROBED LIGHT. Status is the caller's, because a light that
	// was already off in this condition, a probe the budget cut, and a probe
	// whose frame would not decode are three different facts and none of them
	// is a light that contributed nothing.
	//
	// `lightIndex` is 1-based and carries its denominator so a truncated
	// series is visible from any one line.
	inline std::string LightDeltaLine(const std::string& LightId, const std::string& Kind,
	                                  int Index, int OfN, const std::string& ShotId,
	                                  const std::string& CameraId, const std::string& ConditionId,
	                                  const std::string& Status, const LightDelta& D,
	                                  const std::string& Note)
	{
		char Head[420];
		std::snprintf(Head, sizeof(Head),
			"light %s kind=%s lightIndex=%d/%d shot=%s camera=%s condition=%s lightStatus=%s",
			LightId.c_str(), Kind.c_str(), Index, OfN, ShotId.c_str(),
			CameraId.c_str(), ConditionId.c_str(), Status.c_str());
		std::string Out(Head);
		if (!D.Comparable)
		{
			Out += " lightDelta=NOTHING-MEASURED lightDeltaNote=";
			Out += (Note.empty() ? std::string("no-comparable-pair") : Note);
			return Out;
		}
		char Body[1200];
		std::snprintf(Body, sizeof(Body),
			" deltaStat=luma-on-minus-off/per-pixel "
			"region=full deltaMeanFull=%.5f meanOnFull=%.5f meanOffFull=%.5f "
			"peakRegion=c%dr%d/of%dx%d peakRegionPx=x%d..%d/y%d..%d "
			"deltaMeanPeak=%.5f meanOnPeak=%.5f meanOffPeak=%.5f "
			"deltaMaxRise=%.5f deltaMaxDrop=%.5f "
			"deltaCodeEdges=1/2/4/8/16/32 deltaPixelsRoseAtLeast=%lld/%lld/%lld/%lld/%lld/%lld "
			"deltaPixelsOf=%lld deltaHistStat=pixel-count-with-luma-rise-at-or-above-edge-in-8bit-codes "
			"deltaPixelsDarkerWithLightOn=%lld/%lld "
			"deltaDarkerRule=auto-exposure-suspected-if-large lightDeltaNote=%s",
			D.MeanDeltaFull, D.MeanOnFull, D.MeanOffFull,
			D.PeakCol, D.PeakRow, D.Cols, D.Rows,
			D.PeakX0, D.PeakX1, D.PeakY0, D.PeakY1,
			D.PeakMeanDelta, D.PeakMeanOn, D.PeakMeanOff,
			D.MaxRise, D.MaxDrop,
			D.RoseAtLeast[0], D.RoseAtLeast[1], D.RoseAtLeast[2],
			D.RoseAtLeast[3], D.RoseAtLeast[4], D.RoseAtLeast[5],
			D.Pixels, D.PixelsDarkerWithLightOn, D.Pixels,
			(Note.empty() ? "none" : Note.c_str()));
		Out += Body;
		return Out;
	}

	// THE WHOLE-RUN SUMMARY FOR THE LIGHT PASS, on its own line, carrying
	// only numbers that are true of the RUN. `reachedFrame` is the count of
	// probed lights whose luma rose by at least one code value somewhere,
	// over the number actually probed, and a pass that probed nothing says
	// the words instead of printing 0/0 as though it had looked.
	inline std::string LightProbeDoneLine(int Probed, int Eligible, int ReachedFrame,
	                                      int SkippedAlreadyOff, int SkippedBudget,
	                                      int NoFile, int RestoreMismatch,
	                                      int ShotsProbed, int ShotsAsked,
	                                      double BudgetSeconds, double SpentSeconds,
	                                      int FramesBeforeShot, int Controls)
	{
		char Buf[700];
		std::snprintf(Buf, sizeof(Buf),
			"lightProbeStatus=%s lightsProbed=%d/%d lightsReachedFrame=%d/%d "
			"lightsSkippedAlreadyOff=%d lightsSkippedBudget=%d lightProbesNoFile=%d "
			"lightRestoreMismatch=%d/%d controlProbes=%d "
			"shotsProbed=%d/%d lightProbeBudgetSeconds=%.1f lightProbeSpentSeconds=%.1f "
			"lightProbeFramesBeforeShot=%d/same-as-reference "
			"lightProbeMethod=one-light-off-vs-reference/same-camera-condition-framecount",
			Probed == 0 ? "NOTHING-MEASURED" : (SkippedBudget > 0 ? "PARTIAL-BUDGET-BIT" : "ALL"),
			Probed, Eligible, ReachedFrame, Probed,
			SkippedAlreadyOff, SkippedBudget, NoFile,
			RestoreMismatch, Probed, Controls,
			ShotsProbed, ShotsAsked, BudgetSeconds, SpentSeconds, FramesBeforeShot);
		return std::string(Buf);
	}
}
