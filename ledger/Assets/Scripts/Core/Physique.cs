using System;

namespace Ledger.Core
{
    /// WHAT A PERSON IS SHAPED LIKE, from their name (the-gap.md §3b).
    ///
    /// A crowd of identical bodies is worse than a crowd of capsules, because
    /// identical capsules read as placeholder and identical PEOPLE read as a
    /// bug. The moment there is a body, there has to be more than one of them.
    ///
    /// The cheapest variation that actually works is SILHOUETTE — height,
    /// breadth, and the ratio between the two. Skin and clothing colour are
    /// what everyone reaches for first and they do the least: at any real
    /// distance a street is read as outlines, and thirty outlines of the same
    /// dimensions in different colours is thirty of the same person.
    ///
    /// DERIVED FROM THE NAME, never rolled. Same person, same body, in every
    /// session, on every machine, before and after a save — and the name is
    /// the one identifier this project already guarantees is stable.
    public struct Physique
    {
        /// Metres, heel to crown.
        public double Height;
        /// Multiplier on shoulder width and limb thickness. Independent of
        /// height on purpose: tall and narrow, short and broad, and the two
        /// crossed are four silhouettes rather than the two you get from
        /// scaling a body uniformly.
        public double Breadth;
        /// Multiplier on head size. Small, and it is most of what separates
        /// two bodies of otherwise identical dimensions.
        public double HeadScale;
        /// Multiplier on how far this person swings when they walk. A short
        /// brisk stride and a long loose one are recognisable from across a
        /// street when height alone is not.
        public double Gait;
        /// Which leg carries an injury when one is carried. Fixed per person,
        /// so somebody hurt on Tuesday is still limping on the same side on
        /// Friday.
        public bool BadLegIsLeft;

        /// The range. Real adult heights, not a game's idea of them: the
        /// difference between the 5th and 95th percentile is about 25cm, and
        /// a crowd spread wider than that stops reading as people.
        public const double MinHeight = 1.56;
        public const double MaxHeight = 1.93;
        /// The height everything in `Mannequin` is authored at, so a scale
        /// factor is `Height / ReferenceHeight`.
        public const double ReferenceHeight = 1.80;

        public static Physique For(string name)
        {
            // Four INDEPENDENT draws. One hash reused with different
            // arithmetic gives correlated traits — everybody tall is also
            // broad, and the crowd collapses back onto one axis of variation
            // wearing a disguise. Salting the hash separately is the whole
            // trick and it costs four multiplications.
            double h = Fraction(name, 1);
            double b = Fraction(name, 2);
            double k = Fraction(name, 3);
            double g = Fraction(name, 4);
            // The height's SECOND draw gets its own salt rather than
            // borrowing breadth's. Reusing it made height a function of
            // breadth — a correlation of about 0.7, flatly contradicting the
            // "independent of height on purpose" two fields up. Doc comments
            // do not constrain code; the test below does.
            double h2 = Fraction(name, 6);

            return new Physique
            {
                // Biased toward the middle: a triangular draw from two
                // fractions rather than a flat one, because a uniformly
                // distributed crowd has as many giants as average people and
                // reads as a fantasy tavern.
                Height = MinHeight + (MaxHeight - MinHeight) * Triangular(h, h2),
                Breadth = 0.86 + 0.32 * b,
                HeadScale = 0.93 + 0.14 * k,
                Gait = 0.85 + 0.32 * g,
                BadLegIsLeft = Fraction(name, 5) < 0.5,
            };
        }

        /// Scale to apply to a body authored at `ReferenceHeight`.
        public static double HeightScale(Physique p) => p.Height / ReferenceHeight;

        /// Where this person's feet are, once they have been scaled. The
        /// mannequin's sole sits a fixed distance below its origin AT THE
        /// REFERENCE HEIGHT; scale the body and that distance scales too, so
        /// a short person floats and a tall one sinks unless the origin is
        /// lifted to match. Cheaper to state as a function than to rediscover
        /// as a bug.
        public static double SoleOffset(Physique p, double soleAtReference) =>
            soleAtReference * HeightScale(p);

        /// Average of two independent uniforms — a triangular distribution
        /// centred on 0.5. Ordinary is common and extremes are rare, which is
        /// what a street looks like.
        static double Triangular(double a, double b) => (a + b) * 0.5;

        /// FNV-1a with a salt, folded to 0..1.
        ///
        /// Not `GetHashCode`: it is randomised per process on .NET Core, so a
        /// city built on it would give every person a new body on every
        /// launch while passing every test that ran inside one process.
        public static double Fraction(string name, int salt)
        {
            unchecked
            {
                uint h = 2166136261;
                foreach (char c in name ?? "")
                {
                    h ^= c;
                    h *= 16777619;
                }
                // The salt goes through the same mill, byte by byte — which
                // matters only for salts past 255, and is written this way
                // for uniformity rather than because it fixes anything.
                //
                // THE AVALANCHE BELOW IS WHAT ACTUALLY FIXES IT, and the
                // break run is the only reason that is stated correctly here.
                // The first version XORed the salt in once, multiplied once,
                // and carried a comment claiming that kept neighbouring salts
                // apart. It does the opposite: XOR by 1 versus 2 changes the
                // product by one prime versus two, a difference sitting in
                // bits 24 and 25 that never reaches the top bits the fraction
                // is read from. Salts 1 and 2 came out nearly identical,
                // height and breadth were one draw, and the triangular
                // distribution built on averaging them collapsed to uniform —
                // 49% of the crowd near average where an independent pair
                // gives 75%.
                //
                // Reintroducing the weak salt WITH fmix32 still passes. So
                // the byte loop was never the fix, and a comment crediting it
                // would have been the second wrong explanation in one
                // function. Caught by asserting the SHAPE of the distribution
                // rather than its range; the range test passed throughout.
                for (int b = 0; b < 4; b++)
                {
                    h ^= (uint)((salt >> (b * 8)) & 0xFF);
                    h *= 16777619;
                }
                // fmix32: every input bit reaches every output bit.
                h ^= h >> 16;
                h *= 0x85ebca6b;
                h ^= h >> 13;
                h *= 0xc2b2ae35;
                h ^= h >> 16;
                return h / (double)uint.MaxValue;
            }
        }
    }
}
