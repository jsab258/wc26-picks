namespace Ledger.Core
{
    /// WHICH BITS OF A CHARACTER MESH ARE BARE SKIN AND WHICH WEAR CLOTHES.
    ///
    /// WHY THIS EXISTS, AND IT IS THE BEST-DOCUMENTED BUG IN THE PROJECT.
    ///
    /// `RealBody` dresses the player by painting each renderer either a flesh
    /// colour or a coat colour, and decided which from the renderer's name:
    ///
    ///     bool flesh = n.Contains("head") || n.Contains("hand")
    ///               || n.Contains("eye")  || n.Contains("face");
    ///
    /// The model has exactly two meshes, `Beta_Surface` and `Beta_Joints`.
    /// **`"beta_surface".Contains("face")` is true** — sur-FACE — so the entire
    /// body was classified as bare skin and the coat went on the joint balls.
    /// The player stood in the middle of the noon still with nothing on.
    ///
    /// Every number in the verdict said so and none of them was read as saying
    /// it: `bodySkinned=1 bodyDressed=1` (the split is one mesh each) and
    /// `bodyCoatArea=0.296` (the coat covers 29.6% of the body). A coat that
    /// covers 29.6% of a person is not a coat, and the frame showed a nude
    /// figure for as long as those two numbers were sitting in a passing run.
    ///
    /// THREE RULES OF THIS PROJECT MET IN ONE LINE, so it is worth naming them.
    ///
    /// *Rule 4* — a fault a picture found and no gate did, now the fifth. The
    /// repair is not only the classifier: it is `bodyParts`, which prints each
    /// mesh with its area share and which way it was painted, so the next
    /// version of this mistake is a line of text rather than an afternoon.
    ///
    /// *Rule 1* — the comment above the broken line argued, at length and
    /// correctly, that reading a name beats reading an index. It was right
    /// about the principle and silent about the implementation, and a
    /// confident comment over a wrong line is worse than no comment: it is
    /// what stops the next reader looking.
    ///
    /// *The layering* — this is pure string logic and it lived in the Game
    /// assembly, which does not compile in this container. It could only ever
    /// be tested by a 28-minute Windows round trip, so it never was. Moved to
    /// Core it is four unit tests that run in under a second, and the first of
    /// them is `Beta_Surface`.
    public static class BodyParts
    {
        /// The parts of a person that a coat does not cover. Whole segments,
        /// compared for equality — never `Contains`, which is the entire
        /// subject of this file.
        ///
        /// Hair is deliberately absent. It is not flesh and it is not a coat,
        /// and painting it either is wrong; in practice a model with a hair
        /// mesh is a textured model and `RealBody` leaves textured materials
        /// alone, so it never reaches this decision. If that ever stops being
        /// true, the fix is a third material and not a third guess here.
        static readonly string[] Bare =
        {
            "head", "face", "hand", "hands", "eye", "eyes", "eyelash",
            "eyelashes", "eyebrow", "eyebrows", "ear", "ears", "teeth",
            "tongue", "neck",
        };

        /// Split a renderer name into its words, on the separators modelling
        /// tools actually use, and on the digits they suffix with. So
        /// `Beta_Surface` is {beta, surface}, `Head_01` is {head}, and
        /// `Mesh.Left Hand` is {mesh, left, hand}.
        ///
        /// The point of splitting at all is that a WORD can be compared for
        /// equality, and equality is the thing a substring test only
        /// approximates. `surface` is not `face`; it never was.
        public static string[] Words(string rendererName)
        {
            if (string.IsNullOrEmpty(rendererName)) return new string[0];
            var chars = rendererName.ToCharArray();
            for (int i = 0; i < chars.Length; i++)
            {
                char c = chars[i];
                bool word = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
                if (!word) chars[i] = ' ';
            }
            var raw = new string(chars).ToLowerInvariant()
                .Split(new[] { ' ' }, System.StringSplitOptions.RemoveEmptyEntries);
            return raw;
        }

        /// Is this renderer bare skin?
        public static bool IsFlesh(string rendererName)
        {
            foreach (var w in Words(rendererName))
                foreach (var b in Bare)
                    if (w == b) return true;
            return false;
        }

        /// WHICH MESH GETS WHICH MATERIAL, decided over the whole model rather
        /// than one name at a time. Returns one flag per name: true = leave it
        /// bare, false = put the coat on it.
        ///
        /// The reason this is not just `IsFlesh` mapped over the array: **a
        /// model whose body is a single mesh cannot be dressed at all.** There
        /// is no separate head to leave bare, so asking "is this the head?" of
        /// the only mesh there is has no good answer — and the two wrong
        /// answers are not equally wrong. Painting it flesh is a nude in the
        /// middle of the frame. Painting it the coat colour is a coloured
        /// mannequin, which is exactly what the other fifty people on the
        /// street already are, and reads as a person in a coat at any distance
        /// the game actually shows them at.
        ///
        /// So: if EVERY mesh would be bare, none of them is. That is a
        /// statement about the model's structure, which is checkable, and not
        /// about how much area came out bare, which would silently paper over
        /// exactly the misclassification this file exists to catch.
        public static bool[] Assign(string[] rendererNames)
        {
            if (rendererNames == null) return new bool[0];
            var flesh = new bool[rendererNames.Length];
            bool anyCoat = false;
            for (int i = 0; i < rendererNames.Length; i++)
            {
                flesh[i] = IsFlesh(rendererNames[i]);
                if (!flesh[i]) anyCoat = true;
            }
            if (!anyCoat)
                for (int i = 0; i < flesh.Length; i++) flesh[i] = false;
            return flesh;
        }

        /// HOW MUCH OF A PERSON A COAT HAS TO COVER BEFORE IT IS A COAT.
        ///
        /// Rule 2 says do not invent a threshold, so here is where this one
        /// comes from and what sits on either side of it.
        ///
        /// The failing measurement is real and was taken from the build:
        /// `bodyCoatArea=0.296`. The correct value comes from anatomy — the
        /// clinical rule of nines puts the head at 9% of body surface and the
        /// two hands at about 2%, so a fully dressed person with bare head and
        /// hands is roughly 89% covered, and an undressed one near 0%.
        ///
        /// A half is therefore not a measurement of anything; it is a bound
        /// with the good case at 0.89–1.00 and the observed bad case at 0.296,
        /// far from both. It answers the only question worth asking of this
        /// system — did the torso end up on the right side — and it is not
        /// tuned to make a red run go green, because it was written while the
        /// run was red and stays red until the classifier is fixed.
        public const double MinDressedArea = 0.5;
    }
}
