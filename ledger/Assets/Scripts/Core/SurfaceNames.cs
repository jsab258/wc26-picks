namespace Ledger.Core
{
    /// Normalising material NAMES back to the logical surface they were built
    /// from, so a caller can ask "is this pixel one of the ground surfaces"
    /// without knowing how the asset pipeline decorates a name.
    ///
    /// It lives in Core, and holds no list of its own, ON PURPOSE. The list of
    /// ground surfaces is `AssetLibrary.WetSurfaces` and there must not be a
    /// second copy of it — one idea, one implementation. What is here is the
    /// STRING RULE, which is the only half that can be tested locally: the
    /// Game layer does not compile in this container, so a matcher written
    /// inside `AssetLibrary` would ship unrun.
    ///
    /// The decorations it has to undo, all of them read out of
    /// `AssetLibrary` rather than guessed:
    ///
    ///   `mat_` prefix     `BuildMaterial` names every surface `"mat_" + logical`
    ///   `_b` suffix       `MaterialVariant` picks `logical + "_b"` when the pack
    ///                     ships a second texture for that surface
    ///   `#g2` suffix      `MaterialGraded` copies a base as `baseMat.name + "#g" + g`
    ///   ` (Instance)`     Unity's own suffix when something touched
    ///                     `renderer.material` instead of `sharedMaterial`
    ///
    /// So `mat_asphalt_b#g3 (Instance)` and `mat_asphalt` are both `asphalt`.
    public static class SurfaceNames
    {
        /// The logical surface behind a material name, lower-cased, or the
        /// empty string for null/empty input. Pure string work — no asset
        /// lookup, no Unity types, so CoreTests can run it.
        public static string Logical(string materialName)
        {
            if (string.IsNullOrEmpty(materialName)) return "";
            var n = materialName.Trim();

            // Unity's clone suffix goes first: it is appended AFTER every
            // other decoration, so stripping it last would leave `#g2 (Instance)`
            // hiding the grade marker from the cut below.
            int inst = n.IndexOf(" (Instance)");
            if (inst >= 0) n = n.Substring(0, inst);

            int grade = n.IndexOf('#');
            if (grade >= 0) n = n.Substring(0, grade);

            n = n.Trim().ToLowerInvariant();
            if (n.StartsWith("mat_")) n = n.Substring(4);
            if (n.EndsWith("_b")) n = n.Substring(0, n.Length - 2);
            return n;
        }

        /// WHICH of `logicals` this material name is, normalised, or the empty
        /// string for none. Case-insensitive, and EXACT after normalising — a
        /// prefix test would make `asphaltish` ground and `mat_flat_1f3` is
        /// deliberately not `flat`.
        ///
        /// IT REPLACED A BOOLEAN `IsOneOf`, AND THAT IS THE POINT. The
        /// classifier that decides a pixel IS ground and the classifier that
        /// decides WHICH ground it is must never be able to disagree: every
        /// per-material number in `groundGainBy` is divided by a per-family
        /// denominator the other one produced, so two loops over the same list
        /// is one idea in two implementations with a division across the seam.
        /// Callers wanting the yes/no ask `MatchOf(...).Length > 0`.
        public static string MatchOf(string materialName, string[] logicals)
        {
            if (logicals == null || logicals.Length == 0) return "";
            var n = Logical(materialName);
            if (n.Length == 0) return "";
            for (int i = 0; i < logicals.Length; i++)
            {
                if (string.IsNullOrEmpty(logicals[i])) continue;
                if (n == logicals[i].Trim().ToLowerInvariant()) return n;
            }
            return "";
        }
    }
}
