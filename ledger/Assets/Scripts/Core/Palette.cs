using System;

namespace Ledger.Core
{
    /// Colour maths that must not silently wash out.
    ///
    /// This exists because of a measured defect, not a theory. The art pass
    /// set every neon sign's emission to `colour * 2.2`, which is the obvious
    /// way to make a panel read as a light source — and in a low-dynamic-range
    /// build it destroys the colour of exactly the signs that need it most.
    /// Any channel above 1/2.2 clips to white, so a pale sign like (0.95,
    /// 0.90, 0.35) lands at (1.00, 1.00, 0.77): a bright grey. Four of eight
    /// signs were washing out, and the CI render fingerprint caught it —
    /// bright pixels averaging 247,249,244 on a night frame that was supposed
    /// to be full of saturated colour.
    ///
    /// The fix is to scale to the BRIGHTEST CHANNEL rather than multiply
    /// uniformly. That is the only way to raise brightness while keeping hue
    /// and saturation exactly where they were authored, and "exactly" is
    /// checkable, which is why this is here rather than inline in a
    /// MonoBehaviour.
    public static class Palette
    {
        /// Saturation, 0..1, in the HSV sense: how far the colour is from grey.
        public static double Saturation(double r, double g, double b)
        {
            double max = Math.Max(r, Math.Max(g, b));
            if (max <= 0) return 0;
            double min = Math.Min(r, Math.Min(g, b));
            return (max - min) / max;
        }

        /// Raise a colour to `level` brightness WITHOUT changing what colour
        /// it is. The brightest channel lands on `level`; the others keep
        /// their ratio to it.
        ///
        /// level above 1 still clips in an LDR build, so callers should keep
        /// it at or below 1 and get their apparent brightness from the light
        /// the sign throws rather than from the panel's own pixels. That is
        /// also the more truthful model: a neon tube is not very bright, it
        /// just looks it against a dark wet street.
        public static (double r, double g, double b) Emissive(
            double r, double g, double b, double level)
        {
            double max = Math.Max(r, Math.Max(g, b));
            if (max <= 0) return (0, 0, 0);
            double k = level / max;
            return (r * k, g * k, b * k);
        }

        /// What uniform multiplication does, kept so the tests can hold the
        /// two side by side. Not for use.
        public static (double r, double g, double b) NaiveScale(
            double r, double g, double b, double mult)
        {
            double C(double v) => Math.Min(1.0, v * mult);
            return (C(r), C(g), C(b));
        }
    }
}
