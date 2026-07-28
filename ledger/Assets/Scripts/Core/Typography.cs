using System;

namespace Ledger.Core
{
    /// TYPE, SPACING AND CONTRAST (the-gap.md §5, "UI typography pass").
    ///
    /// The interface has a colour language and no TYPE language. Font sizes
    /// across the panels are 14, 15, 18, 19, 22, 24, 64 — arbitrary numbers
    /// chosen one at a time, which is exactly what makes a competent UI look
    /// amateur even when every individual screen is fine. Hierarchy comes
    /// from a SYSTEM or it does not come at all.
    ///
    /// Three things live here, and the third is the one nobody ever does:
    ///
    ///   1. A modular scale, so every size is a step rather than a guess.
    ///   2. An eight-point spacing rhythm, so panels breathe alike.
    ///   3. WCAG CONTRAST, computed — because "it looks readable to me on
    ///      this monitor" is not a standard, and a dim grey on a near-black
    ///      panel is the single most common accessibility failure in games.
    public static class Typography
    {
        // ---- the scale -----------------------------------------------------

        /// 16pt at step 0. Sixteen because it is the browser default and the
        /// size most people have read the most words at, which is a better
        /// reason than taste.
        public const double BasePoints = 16;

        /// A major third. Big enough that adjacent steps are unmistakably
        /// different — a scale whose neighbours look similar communicates no
        /// hierarchy and is worse than no scale, because it costs discipline
        /// and buys nothing.
        public const double Ratio = 1.25;

        public static int Size(int step) =>
            (int)Math.Round(Feel.Clamp(BasePoints * Math.Pow(Ratio, step), 8, 96));

        // Named so call sites say what a thing IS rather than how big it is.
        public static int Micro => Size(-2);   // 10 — legal text, timestamps
        public static int Small => Size(-1);   // 13 — captions, hints
        public static int Body => Size(0);     // 16 — the reading size
        public static int Lede => Size(1);     // 20 — the first line that matters
        public static int Title => Size(2);    // 25 — a panel's name
        public static int Display => Size(3);  // 31 — a screen's name
        public static int Hero => Size(4);     // 39 — LEDGER, and nothing else

        // ---- rhythm --------------------------------------------------------

        /// Eight points. Every margin, gap and pad is a multiple of it, which
        /// is the whole of why professional layouts feel calm: nothing is a
        /// pixel or two off from anything else.
        public const double Unit = 8;

        public static int Space(double units) => (int)Math.Round(Unit * Math.Max(0, units));

        /// Line height. Tight for display type, generous for body — a
        /// headline at 1.5 looks disconnected and a paragraph at 1.1 is
        /// unreadable, and using one number for both is the most common
        /// spacing mistake there is.
        public static double LineHeight(int points)
        {
            if (points >= Title) return 1.15;
            if (points >= Lede) return 1.30;
            return 1.5;
        }

        // ---- measure -------------------------------------------------------

        /// THE SINGLE BIGGEST READABILITY FACTOR, and the one a wide panel
        /// always gets wrong. Past about 75 characters the eye loses the
        /// start of the next line on the return sweep; under about 45 it
        /// breaks the rhythm of reading. This game's dialogue panels are wide
        /// and full of prose, which is precisely the case it matters for.
        public const int MinMeasureChars = 45;
        public const int MaxMeasureChars = 75;

        /// Roughly 0.5em per character for a humanist sans at reading sizes.
        /// An approximation, and the right kind: the answer only has to be
        /// good enough to keep a column out of the 100-character range.
        public static double MaxWidthPixels(int points) => points * 0.5 * MaxMeasureChars;

        public static bool MeasureIsReadable(double widthPixels, int points)
        {
            if (points <= 0) return false;
            double chars = widthPixels / (points * 0.5);
            return chars >= MinMeasureChars && chars <= MaxMeasureChars;
        }

        // ---- contrast, per WCAG 2.1 ---------------------------------------

        /// Relative luminance. The gamma expansion is not optional — doing
        /// this on raw sRGB values (the obvious mistake) overstates the
        /// contrast of dark pairs by a wide margin, which is exactly the
        /// range this game's interface lives in.
        public static double Luminance(double r, double g, double b)
        {
            return 0.2126 * Channel(r) + 0.7152 * Channel(g) + 0.0722 * Channel(b);
        }

        static double Channel(double c)
        {
            c = Feel.Clamp01(c);
            return c <= 0.03928 ? c / 12.92 : Math.Pow((c + 0.055) / 1.055, 2.4);
        }

        /// 1.0 (identical) to 21.0 (black on white).
        public static double Contrast(double r1, double g1, double b1,
                                      double r2, double g2, double b2)
        {
            double l1 = Luminance(r1, g1, b1), l2 = Luminance(r2, g2, b2);
            double hi = Math.Max(l1, l2), lo = Math.Min(l1, l2);
            return (hi + 0.05) / (lo + 0.05);
        }

        /// WCAG AA. 4.5:1 for body text, 3:1 for large — where "large" is
        /// 18.66pt bold or 24pt regular, which on our scale is Title and up.
        public const double AaNormal = 4.5;
        public const double AaLarge = 3.0;

        public static bool MeetsAa(double contrast, int points) =>
            contrast >= (points >= Title ? AaLarge : AaNormal);

        /// Lift a foreground until it clears the bar against a background.
        ///
        /// Returns a multiplier rather than a colour, so a hue is never
        /// changed to fix a contrast problem — brightening a colour keeps the
        /// design's intent, and shifting it toward white throws the palette
        /// away one fix at a time.
        public static double LiftToMeet(double fr, double fg, double fb,
                                        double br, double bg, double bb, int points)
        {
            double need = points >= Title ? AaLarge : AaNormal;
            if (Contrast(fr, fg, fb, br, bg, bb) >= need) return 1.0;
            double lo = 1.0, hi = 8.0;
            for (int i = 0; i < 40; i++)
            {
                double mid = (lo + hi) * 0.5;
                double c = Contrast(Feel.Clamp01(fr * mid), Feel.Clamp01(fg * mid),
                                    Feel.Clamp01(fb * mid), br, bg, bb);
                if (c >= need) hi = mid; else lo = mid;
            }
            return hi;
        }
    }
}
