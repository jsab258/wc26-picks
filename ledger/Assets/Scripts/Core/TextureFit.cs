namespace Ledger.Core
{
    /// HOW A TEXTURE OF ANY SHAPE TILES WITHOUT LOOKING STRETCHED.
    ///
    /// `AssetLibrary` sets `mainTextureScale` from a per-surface `Tiling` that
    /// was authored against square sources, and every procedural texture the
    /// game generated for itself was square, so the assumption held for months
    /// by never being tested.
    ///
    /// THEN A REAL PACK ARRIVED AND TWO OF THE TWELVE WERE 1024x512. Applying a
    /// uniform tiling factor to a 2:1 image puts twice as many texels across a
    /// metre as it does up it — mortar courses that are oblong, a kerb whose
    /// grain runs stretched, the exact "looks like a photograph pulled sideways"
    /// that reads as cheap from across a street. `pack_check` caught it by
    /// requiring square, which is the right instinct and the wrong rule: a
    /// non-square texture tiles perfectly well, and what actually breaks is
    /// isotropy under a factor that assumed otherwise.
    ///
    /// So the fix belongs here rather than in the choice of asset. Rejecting
    /// every 2:1 material would throw away most of a CC0 library over an
    /// assumption the renderer can simply stop making — and picking
    /// replacements blind would mean guessing at dimensions the catalogue does
    /// not record, which is how the last three CI runs were spent.
    ///
    /// IN CORE BECAUSE IT IS ARITHMETIC. The visible half of this needs a
    /// screenshot and a twenty-eight-minute round trip; the arithmetic does
    /// not, and CoreTests can hold it to both properties below tonight.
    public static class TextureFit
    {
        /// Correct an authored tiling for a source that is not square.
        ///
        /// TWO PROPERTIES, AND THE SECOND IS THE ONE THAT IS EASY TO MISS.
        ///
        ///   ISOTROPY — texels are as dense across the surface as up it. That
        ///   is the whole point, and `y *= aspect` alone achieves it.
        ///
        ///   APPARENT SCALE IS PRESERVED — `x * y` comes out unchanged, so a
        ///   surface tuned to read at a given size still reads at that size.
        ///   `y *= aspect` alone would make a 2:1 source twice as busy as the
        ///   author asked for, which is a different wrong picture from the one
        ///   being fixed. Splitting the correction between the axes — one
        ///   divided by the square root, one multiplied by it — gets both.
        ///
        /// A square source is left exactly alone, which matters because every
        /// procedurally generated texture in the game is square and none of
        /// their appearance may shift.
        public static void Isotropic(double tileX, double tileY,
                                     int textureWidth, int textureHeight,
                                     out double x, out double y)
        {
            x = tileX;
            y = tileY;
            // A DEGENERATE SIZE IS NOT A SHAPE TO CORRECT FOR. Unity hands back
            // a 8x8 placeholder for a texture that failed to load, and zero for
            // one that is not there at all; neither is a reason to change what
            // the surface was authored to look like.
            if (textureWidth <= 0 || textureHeight <= 0) return;
            if (textureWidth == textureHeight) return;

            double aspect = (double)textureWidth / textureHeight;
            double root = System.Math.Sqrt(aspect);
            x = tileX / root;
            y = tileY * root;
        }

        /// Whether a source's shape is one the mip chain and the correction
        /// both stay exact on: each side a power of two — from which a
        /// power-of-two ratio follows, so it is one rule and not two.
        ///
        /// 1024x512 qualifies and is corrected above. 1024x768 does not: the
        /// ratio is 4:3, so the correction's square root is irrational and the
        /// mip chain stops being a clean halving partway down. That is a fact
        /// about the file rather than something to paper over, so `pack_check`
        /// refuses it and says which file.
        public static bool IsCleanShape(int width, int height)
        {
            if (width <= 0 || height <= 0) return false;
            if ((width & (width - 1)) != 0) return false;
            if ((height & (height - 1)) != 0) return false;
            return true;
        }
    }
}
