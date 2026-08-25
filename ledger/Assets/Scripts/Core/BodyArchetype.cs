namespace Ledger.Core
{
    /// WHICH GAIT A BOUGHT MODEL WALKS WITH, from the model's file name.
    ///
    /// WHY THIS EXISTS. `CharacterPrefab.ArchetypeFor` carried this rule and
    /// carried it with a comment saying, in these words: *"'old' is the only
    /// special archetype until a female walk clip actually exists in the
    /// harvest; wiring an archetype whose clips cannot arrive would be rule 6
    /// in advance."* That was correct when written. `walk_f__Female Walk` has
    /// been sitting in `Assets/Characters/B` ever since, listed by
    /// `tools/clip-reach.py` under DISK-ONLY — a clip that ships and nothing
    /// names — so **every woman in Meridian walked the male cycle** while the
    /// clip that fixes it was on disk and in the manifest. The comment was a
    /// claim with no test attached and it decayed exactly the way this
    /// project's comments decay: the world moved and the sentence did not.
    ///
    /// WHY IT IS IN CORE RATHER THAN IN THE EDITOR SCRIPT IT CAME FROM. Two
    /// callers need the same answer and they live in different assemblies: the
    /// Editor builds one animator controller per archetype at import time, and
    /// the RUNTIME has to count how many female bodies actually got the female
    /// controller — which is the only evidence that the wire reached the
    /// street rather than merely being written. Two implementations of one
    /// rule is the shape this project has paid for more often than any other,
    /// and neither the Editor nor the Game layer compiles in the container
    /// where the tests run.
    ///
    /// WHY A NAME LIST AND NOT A MEASUREMENT. `Proportion` argues, correctly,
    /// that "a hand-written list of caricature names is a judgement with no
    /// number under it" and replaces one with a measured ratio. That argument
    /// does not carry here and it is worth saying why rather than quietly
    /// disagreeing with a neighbour: whether Mixamo's `Kate` is a woman is a
    /// FACT ABOUT THE ASSET, not a property of the mesh that any bone height
    /// could recover. There is no ratio that separates `Kate` from `Joe`
    /// without also separating tall men from short ones.
    ///
    /// What the list owes instead is VISIBILITY, because an unlisted model
    /// falls to `Default` and a wrongly-male walk looks identical to a
    /// correctly-male one. So `Roster()` prints every model and the archetype
    /// it drew, on the done line, and a new FBX that nobody classified shows
    /// up as a name in that list rather than as nothing at all.
    public static class BodyArchetype
    {
        /// The male walk cycle: `walk`, the clip the whole city used to share.
        public const string Default = "default";
        /// `walk_old` + `idle_old` — Mixamo's Old Man Walk.
        public const string Old = "old";
        /// `walk_f` — Mixamo's Female Walk, on disk since the B harvest and
        /// referenced by nothing until this file.
        public const string Female = "female";

        /// THE WOMEN ON TODAY'S ROSTER, read off the eighteen FBX in
        /// `Assets/Characters` rather than guessed: Elizabeth, Kate, Martha,
        /// Michelle, Shannon, Sophie. The rest of the pool — Adam, Big Vegas,
        /// David, James, Joe, Leonard, Pete, Remy, The Boss — are men, and
        /// `X Bot`/`Y Bot` are the untextured rig stand-ins `RealBody`
        /// already keeps out of the pool by name.
        ///
        /// Compared as WORDS, through `BodyParts.Words`, never with
        /// `Contains`. The stem arrives with its spaces stripped
        /// (`Sporty Granny` becomes `SportyGranny` on the prefab), and the
        /// camelCase split in `Words` is what makes `{sporty, granny}` out of
        /// it — so this is equality on a segment, which is the entire subject
        /// of `BodyParts` and the reason the naked-player bug happened.
        static readonly string[] Women =
        {
            "elizabeth", "kate", "martha", "michelle", "shannon", "sophie",
        };

        /// The elderly, by the same rule. `granny`, `old` and `elder` are the
        /// words the previous implementation matched and they are kept
        /// verbatim so this change cannot silently re-archetype a body that
        /// already had one.
        static readonly string[] Elders = { "granny", "old", "elder" };

        /// SPORTY GRANNY IS OLD, NOT FEMALE, AND THAT IS A JUDGEMENT.
        ///
        /// She is both, and there is no `walk_old_f` in the harvest, so one
        /// axis has to win. Age wins: at seventy the stoop, the shortened
        /// stride and the arm carriage separate a walk from the crowd far more
        /// than sex does, and `walk_old` is the clip that has those. Said out
        /// loud because it is a call rather than a measurement — if a
        /// `walk_old_f` ever lands, this is the line that should change, and
        /// the alternative (female wins, granny walks young) is the one
        /// rejected here.
        public static string Of(string modelStem)
        {
            foreach (var w in BodyParts.Words(modelStem))
            {
                foreach (var e in Elders) if (w == e) return Old;
            }
            foreach (var w in BodyParts.Words(modelStem))
            {
                foreach (var f in Women) if (w == f) return Female;
            }
            return Default;
        }

        /// THE CANONICAL CONTROLLER KEEPS ITS HISTORIC NAME. Every landed
        /// verdict and every gate has watched `Body.controller`; a variant
        /// renaming it out from under them would read as the controller
        /// vanishing. Variants are `Body_{arch}_{idleKey}`.
        ///
        /// One implementation, because the Editor WRITES this asset and the
        /// runtime READS the name back off the Animator to prove the right
        /// controller arrived. Two spellings of one string is how a wire ships
        /// looking connected.
        public const string CanonicalName = "Body";

        public static string ControllerName(string archetype, string idleKey)
        {
            if (archetype == Default && idleKey == "idle") return CanonicalName;
            return CanonicalName + "_" + archetype + "_" + idleKey;
        }

        /// DOES THE CONTROLLER ON THIS BODY BELONG TO THIS ARCHETYPE?
        ///
        /// The runtime half of the wire, and it reads the asset that actually
        /// arrived rather than re-running `Of` — two numbers derived from one
        /// variable are one number twice, and a counter that asked `Of` again
        /// would print a perfect score on a build where the Editor step never
        /// wrote a female controller at all.
        ///
        /// Segment equality, not `Contains`: the name is machine-generated as
        /// `Body_female_idle_2`, so segment 1 is the archetype and comparing it
        /// whole cannot be fooled by a model called `Body_Femalefoo`.
        public static bool ControllerCarries(string controllerName, string archetype)
        {
            if (string.IsNullOrEmpty(controllerName)) return false;
            // Unity appends " (Instance)" to a controller name in some load
            // paths; the asset stem is everything before the first space.
            var name = controllerName.Split(' ')[0];
            if (archetype == Default)
                return name == CanonicalName || Segment(name, 1) == Default;
            return Segment(name, 1) == archetype;
        }

        static string Segment(string name, int index)
        {
            var parts = name.Split('_');
            return index >= 0 && index < parts.Length ? parts[index] : "";
        }

        /// EVERY MODEL AND THE ARCHETYPE IT DREW, for the done line.
        ///
        /// The list is the denominator rule applied to a classification: a run
        /// that reports `walkFemale=0/0` cannot say whether the city has no
        /// women or whether six women were classified as men, and those need
        /// completely different next actions. This prints the classification
        /// itself, so an unrecognised new FBX is a visible `default` beside a
        /// name a reader knows is a woman's.
        ///
        /// Slash-separated: a verdict value may not contain a space.
        public static string Roster(string[] modelStems)
        {
            if (modelStems == null || modelStems.Length == 0)
                return "no models offered";
            var b = new System.Text.StringBuilder();
            for (int i = 0; i < modelStems.Length; i++)
            {
                if (i > 0) b.Append('/');
                b.Append(modelStems[i]).Append(':').Append(Of(modelStems[i]));
            }
            return b.ToString();
        }
    }
}
