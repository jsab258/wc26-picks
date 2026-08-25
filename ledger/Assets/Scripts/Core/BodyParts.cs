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
        ///
        /// `brows` and `mouth` were added when the camelCase split above made
        /// them reachable: Big Vegas and Sporty Granny each ship
        /// `*_BrowsAnimGeo` and `*_MouthAnimGeo` as separate little meshes, and
        /// both are bare skin by any reading. `eyelasshes` is Kate's shipped
        /// spelling, quoted rather than corrected — the model file is the
        /// authority and it has a typo in it.
        static readonly string[] Bare =
        {
            "head", "face", "hand", "hands", "eye", "eyes", "eyelash",
            "eyelashes", "eyelasshes", "eyebrow", "eyebrows", "brows",
            "mouth", "ear", "ears", "teeth", "tongue", "neck",
        };

        /// Split a renderer name into its words, on the separators modelling
        /// tools actually use, and on the digits they suffix with. So
        /// `Beta_Surface` is {beta, surface}, `Head_01` is {head}, and
        /// `Mesh.Left Hand` is {mesh, left, hand}.
        ///
        /// The point of splitting at all is that a WORD can be compared for
        /// equality, and equality is the thing a substring test only
        /// approximates. `surface` is not `face`; it never was.
        ///
        /// AND ON camelCase, WHICH THE SEPARATOR LIST ALONE CANNOT SEE.
        ///
        /// Read off the shipped roster rather than imagined: Big Vegas ships
        /// `Elvis_BodyGeo`, `Elvis_BrowsAnimGeo`, `Elvis_EyesAnimGeo`,
        /// `Elvis_MouthAnimGeo`, and Sporty Granny the same four under
        /// `Fitness_Grandma_`. Splitting on separators alone gives {elvis,
        /// browsanimgeo} — no word, so the brows read as unclassified and got
        /// washed with the coat colour, which is the face-tinting fault this
        /// whole split exists to remove. A lowercase letter followed by an
        /// uppercase one is a word boundary in every modelling tool's naming,
        /// and it is still EQUALITY afterwards rather than a substring test:
        /// `browsanimgeo` never becomes `brows` by containment, only by being
        /// cut at the capital.
        ///
        /// It cannot loosen anything the old split decided. `Beta_Surface` is
        /// still {beta, surface} — there is no lower-to-upper transition
        /// inside either word — and the CoreTest named after it is first in
        /// the list for that reason.
        public static string[] Words(string rendererName)
        {
            if (string.IsNullOrEmpty(rendererName)) return new string[0];
            var b = new System.Text.StringBuilder(rendererName.Length * 2);
            for (int i = 0; i < rendererName.Length; i++)
            {
                char c = rendererName[i];
                bool lower = c >= 'a' && c <= 'z';
                bool upper = c >= 'A' && c <= 'Z';
                if (!lower && !upper) { b.Append(' '); continue; }
                if (upper && i > 0)
                {
                    char prev = rendererName[i - 1];
                    if (prev >= 'a' && prev <= 'z') b.Append(' ');
                }
                b.Append(c);
            }
            return b.ToString().ToLowerInvariant()
                .Split(new[] { ' ' }, System.StringSplitOptions.RemoveEmptyEntries);
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

        // ------------------------------------------------------------------
        // THE SECOND SPLIT: COAT FROM TROUSERS, ON A MODEL THAT ARRIVED
        // TEXTURED.
        //
        // `Assign` above answers "flesh or coat" for a model with NO textures,
        // where the choice is which MATERIAL to hang on each mesh. Since
        // texture extraction landed, no shipped body reaches it — the landed
        // verdict says so in words, `bodyParts=[nothing to paint — all 9
        // renderer(s) came textured]` — and the only route the wardrobe has to
        // the eye is `Wardrobe.Wash`, a multiply over the artist's own sheet.
        //
        // That wash was applied to EVERY renderer on the body with one colour,
        // head included, so nobody could have a navy coat and stone trousers
        // and the face carried the coat's hue. This is the classifier that
        // splits it, and it is a different question from `Assign`'s: not
        // "which material" but "which of this person's meshes is the upper
        // garment, which is the lower, and which is the artist's business".
        //
        // THE WORD LISTS ARE READ OFF THE SHIPPED ROSTER, NOT IMAGINED. All
        // eighteen FBX under `Assets/Characters` were parsed for their mesh
        // node names before a word was written here; the roster and the
        // per-model outcome are in `game-design/agent-reports/
        // inhabited-wiring.md`. Eleven of the sixteen pool bodies ship a
        // separate upper AND lower garment mesh — `Ch21_Shirt` and
        // `Ch21_Pants`, `Ch08_Hoodie` and `Ch08_Pants`, `Tops` and `Bottoms`,
        // `Jacket_Geo` and `Pants_Geo`. Four are one welded mesh (James,
        // Michelle, Big Vegas, Sporty Granny) and one has an upper only
        // (Sophie's `Ch02_Cloth`).
        //
        // That contradicts `research/inhabited-street.md` §2.2, which says
        // "Component drawables (separate garment meshes) — NEVER, and
        // correctly — Mixamo bodies are single welded meshes". They are not:
        // eleven of sixteen are not, and the garment split is therefore a
        // wiring job rather than a modelling pipeline. The research read the
        // code and not the assets; this list read the assets.
        //
        // A WORD NOBODY LISTED IS LEFT ALONE, NEVER GUESSED AT — see
        // `Garments` for which way each fallback points and why, and
        // `Unclassified` for the report that makes the next drop's unknown
        // words visible instead of silent.

        /// What a renderer on a bought body is, for the purpose of washing it.
        public enum Garment
        {
            /// Leave the artist's texture alone. Faces, hair, shoes, props,
            /// and — on a model that HAS garment meshes — the skin mesh.
            Own = 0,
            /// One welded mesh carrying the whole person, clothes and all.
            /// Gets the coat draw, which is exactly what every body got before
            /// this split existed, so a welded model is not changed by it.
            Whole = 1,
            /// Coat, shirt, jacket, sweater: the upper garment.
            Upper = 2,
            /// Trousers, shorts, belt: the lower garment, and the whole point
            /// of the exercise — it takes its own wardrobe draw.
            Lower = 3,
        }

        /// Upper-garment mesh words. Every one MEASURED on today's roster:
        /// shirt (Elizabeth, Joe, Kate, Martha, Pete, Shannon), tops (Remy),
        /// hoodie (Adam), hoody (David), sweater (Leonard), suit (Joe,
        /// Martha), jacket (The Boss), vest (Pete), collar (Leonard), tie
        /// (Joe), cloth (Sophie).
        ///
        /// NO SYNONYMS. `coat`, `blouse`, `parka` and the rest are not on any
        /// shipped mesh, and a word list is exactly the place this project
        /// invents things — `Bare` above is verbatim-from-the-model for the
        /// same reason. `Unclassified` is how the next drop's vocabulary
        /// arrives: it reports the words nothing matched, and they get added
        /// from that reading rather than from imagination.
        static readonly string[] UpperWords =
        {
            "shirt", "tops", "hoodie", "hoody", "sweater", "suit",
            "jacket", "vest", "collar", "tie", "cloth",
        };

        /// Lower-garment mesh words, all measured: pants (nine bodies),
        /// bottoms (Remy), shorts (Shannon), belt (Joe).
        ///
        /// `belt` is lower rather than upper because it sits at the waist and
        /// reads with the trousers. It is one mesh on one body and the call
        /// is a judgement, said out loud here rather than left in the list.
        static readonly string[] LowerWords =
        {
            "pants", "bottoms", "shorts", "belt",
        };

        /// Meshes that are never washed at any colour, whatever else the model
        /// has. Faces and hair because a wardrobe band on either is the fault
        /// this split exists to remove — and `Bare`'s own comment already made
        /// the hair argument: "it is not flesh and it is not a coat, and
        /// painting it either is wrong". Feet and props because they are small,
        /// dark and already authored, and a navy shoe bought nothing.
        ///
        /// Measured: eyelashes (eight bodies), eyelasshes (Kate — the typo is
        /// in the shipped FBX and is quoted rather than corrected), hair,
        /// beard (Adam), brows/eyes/mouth (Big Vegas, Sporty Granny, Remy),
        /// teeth (The Boss), sneakers/shoes/heels/boots/socks, helmet (Pete),
        /// hat and cigar (The Boss), lens (Sporty Granny's material).
        static readonly string[] OwnWords =
        {
            "eyelash", "eyelashes", "eyelasshes", "eyebrow", "eyebrows",
            "brows", "hair", "beard", "eye", "eyes", "mouth", "teeth",
            "tongue", "lens",
            "shoe", "shoes", "sneakers", "heels", "boots", "socks",
            "helmet", "hat", "cigar", "whistle", "visor",
        };

        /// Meshes that are the PERSON rather than a garment: which way these
        /// go is the whole-model decision below. Measured: body (twelve
        /// bodies, plus `BodyGeo` on the two welded ones), arms and head (The
        /// Boss), face/hand/neck kept for symmetry with `Bare`.
        static readonly string[] SkinWords =
        {
            "body", "arms", "arm", "torso", "head", "face",
            "hand", "hands", "neck", "ear", "ears",
        };

        static bool Has(string[] set, string word)
        {
            foreach (var s in set) if (s == word) return true;
            return false;
        }

        /// WHICH MESH GETS WHICH DRAW, decided over the whole model, exactly
        /// as `Assign` is and for the same reason: the same word means
        /// different things depending on what else the model ships.
        ///
        /// `Ch21_Body` is Kate's bare arms and face, because her shirt and
        /// trousers are separate meshes. `Elvis_BodyGeo` is the whole of Big
        /// Vegas including his clothes, because nothing else on that model is
        /// a garment. Both are called "body". Only the structure tells them
        /// apart, and structure is checkable.
        ///
        ///   * a model with ANY upper or lower garment mesh: garments take
        ///     their draws, and everything else — skin, face, hair, shoes,
        ///     props, and any word nobody has listed — keeps the artist's
        ///     texture. An unknown word leaves the mesh alone because the
        ///     alternative is washing something that might be a face, and
        ///     this file exists because of a face that got washed.
        ///
        ///   * a model with NO garment mesh: it is one welded person, so the
        ///     skin mesh and any unknown mesh become `Whole` and take the coat
        ///     draw — which is byte-for-byte what every body got before this
        ///     split. Face parts stay `Own` even here: Big Vegas's brows, eyes
        ///     and mouth are separate little meshes and tinting them navy is
        ///     the same fault at a smaller size.
        ///
        /// AND IF THE WELDED BRANCH FINDS NOTHING TO WASH, the largest thing
        /// left is nothing — the person wears no wardrobe at all and the run
        /// must be able to say so. `Unclassified` and the `bodyPartsOwn`
        /// denominator are what make that legible instead of invisible; there
        /// is no such model on today's roster and a silent zero would be the
        /// exact rule-3b failure this project keeps paying for.
        public static Garment[] Garments(string[] rendererNames)
        {
            if (rendererNames == null) return new Garment[0];
            var outv = new Garment[rendererNames.Length];
            bool anyCloth = false;
            for (int i = 0; i < rendererNames.Length; i++)
            {
                outv[i] = Garment.Own;
                bool skin = false, known = false;
                foreach (var w in Words(rendererNames[i]))
                {
                    if (Has(UpperWords, w)) { outv[i] = Garment.Upper; anyCloth = true; known = true; break; }
                    if (Has(LowerWords, w)) { outv[i] = Garment.Lower; anyCloth = true; known = true; break; }
                    if (Has(OwnWords, w)) { known = true; break; }
                    if (Has(SkinWords, w)) { skin = true; known = true; }
                }
                // Marked for the second pass: only a model with no garments
                // turns these into the coat.
                if (outv[i] == Garment.Own && (skin || !known)) outv[i] = Garment.Whole;
            }
            if (anyCloth)
                for (int i = 0; i < outv.Length; i++)
                    if (outv[i] == Garment.Whole) outv[i] = Garment.Own;
            return outv;
        }

        /// The renderer names whose every word is unknown to all four lists —
        /// the report that keeps this list honest when the next Mixamo drop
        /// lands. A drop whose garments are called `Ch44_Anorak` would
        /// silently render as "no split available" and read exactly like a
        /// welded model; this is the denominator that tells them apart.
        ///
        /// Returns the NAMES rather than the words, because the name is what a
        /// person needs to go and look at the model with.
        public static string[] Unclassified(string[] rendererNames)
        {
            if (rendererNames == null) return new string[0];
            var list = new System.Collections.Generic.List<string>();
            foreach (var n in rendererNames)
            {
                bool known = false;
                foreach (var w in Words(n))
                    if (Has(UpperWords, w) || Has(LowerWords, w)
                        || Has(OwnWords, w) || Has(SkinWords, w)) { known = true; break; }
                if (!known) list.Add(n ?? "");
            }
            return list.ToArray();
        }
    }
}
