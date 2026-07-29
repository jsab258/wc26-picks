using System;

namespace Ledger.Core
{
    /// Statistics for the sim's render gates, in Core so they can be tested
    /// against images whose answer is known.
    ///
    /// THIS FILE EXISTS BECAUSE A GATE MEASURED THE WRONG THING FOR MONTHS
    /// AND SAID SO IN ITS OWN COMMENT. The grain gate's documentation read
    /// "grain is signed noise, it barely moves the mean by construction;
    /// local spread is the only thing that changes" — and then computed
    ///
    ///     variance = E[l²] - E[l]²
    ///
    /// over the whole frame, which is GLOBAL spread, not local. Global
    /// variance of a night street is dominated by the difference between the
    /// sky and the lamps: about 0.03, against a grain contribution nearer
    /// 0.0001. The signal was three hundred times under the noise floor of
    /// its own ruler, and the gate passed for two months anyway.
    ///
    /// Then it went NEGATIVE, which is the useful part. Additive noise cannot
    /// reduce spread — but grain clamped at black can. Half the pixels in a
    /// night frame sit near zero, negative grain on them is cut off at zero
    /// while positive grain is not, so the noise lifts the blacks, pulls the
    /// darkest pixels toward the middle, and REDUCES the global variance it
    /// was supposed to raise. A gate reading the wrong statistic did not just
    /// fail to see the effect; it saw it backwards.
    public static class ImageStats
    {
        /// LOCAL spread: the mean squared difference between horizontally
        /// adjacent pixels.
        ///
        /// This is the statistic the grain comment always described. A smooth
        /// gradient — sky, a wall, fog — has almost none of it however bright
        /// or dark it is, because neighbours resemble neighbours. Per-pixel
        /// noise has a great deal of it by definition, because that is what
        /// per-pixel noise IS.
        ///
        /// It is also close to blind to the things that were drowning the
        /// signal. Turning the whole frame up, down, or up in contrast leaves
        /// neighbouring pixels in the same relation to each other; only
        /// something operating at the scale of one pixel moves this number.
        ///
        /// `stride` is the row length. Pairs that would straddle a row
        /// boundary are skipped: the last pixel of one row and the first of
        /// the next are on opposite sides of the image and their difference
        /// is a measurement of nothing.
        public static double LocalSpread(double[] luma, int stride)
        {
            if (luma == null || stride < 2 || luma.Length < 2) return 0;
            double sum = 0;
            int n = 0;
            for (int i = 0; i + 1 < luma.Length; i++)
            {
                if ((i + 1) % stride == 0) continue;   // would wrap to the next row
                double d = luma[i + 1] - luma[i];
                sum += d * d;
                n++;
            }
            return n > 0 ? sum / n : 0;
        }

        /// Global variance, kept because it is the right ruler for other
        /// things — overall contrast, and whether a frame has any structure
        /// in it at all — and wrong only for the one gate that was using it.
        public static double Variance(double[] luma)
        {
            if (luma == null || luma.Length == 0) return 0;
            double sum = 0, sumSq = 0;
            for (int i = 0; i < luma.Length; i++) { sum += luma[i]; sumSq += luma[i] * luma[i]; }
            double mean = sum / luma.Length;
            return Math.Max(0, sumSq / luma.Length - mean * mean);
        }

        public static double Mean(double[] luma)
        {
            if (luma == null || luma.Length == 0) return 0;
            double sum = 0;
            for (int i = 0; i < luma.Length; i++) sum += luma[i];
            return sum / luma.Length;
        }

        /// Rec. 601 luma. The same weights the fingerprint uses, in one place
        /// so a gate and the screenshot it is gating cannot drift apart.
        public static double Luma(double r, double g, double b) =>
            0.299 * r + 0.587 * g + 0.114 * b;

        /// What per-pixel noise of amplitude `sigma` ADDS to the local spread.
        ///
        /// Two independent samples differ with variance 2σ², so the expected
        /// squared difference between neighbours rises by exactly that. Worth
        /// stating as a formula rather than a tuned constant, because it is
        /// what lets the gate's threshold be derived from the grain amount
        /// the shader was actually asked for instead of guessed at — and a
        /// threshold nobody can derive is a threshold nobody can defend when
        /// it starts failing.
        public static double SpreadFromNoise(double sigma) => 2.0 * sigma * sigma;
    }
}
