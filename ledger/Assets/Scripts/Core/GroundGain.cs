using System.Collections.Generic;
using System.Globalization;

namespace Ledger.Core
{
    /// RENDERED-OVER-SOURCE, PER GROUND MATERIAL — the division
    /// `AssetLibrary.GroundAlbedoEmit`'s comment used to order and that
    /// nothing could perform.
    ///
    /// WHY IT EXISTS. That comment said `groundMaskMeanBy / groundAlbedoBy`
    /// "per name" is the lighting gain. It cannot be computed: the first is
    /// keyed by DISTRICT (hook, copper, ironside), the second by MATERIAL
    /// (asphalt, sidewalk, kerb, concrete), and the mask pooled all four
    /// materials into one sum per shot. There was no shared name to divide
    /// on. This tally is the division done where both halves are available at
    /// once — inside the ray loop, where the ray already holds the material it
    /// hit and the pixel it landed on.
    ///
    /// WHAT STATISTIC EACH NUMBER IS, said plainly because that is the one
    /// thing a reader cannot recover from the number:
    ///
    ///   rendered  a RAY-WEIGHTED MEAN of the committed frame's luma over
    ///             every ADMITTED ray in this run that landed on this
    ///             material, across all district shots. Not a peak, not a
    ///             median, not per shot.
    ///   raw       the RAY-WEIGHTED MEAN of the SAME rays read off an
    ///             ungraded render of the same camera at the same instant.
    ///             Same rays, same admission test, different pixel source.
    ///   source    a RAY-WEIGHTED MEAN of the same rays' material albedo,
    ///             sampled at the same ray. Ray-weighted and not per-material
    ///             so that graded copies of one logical (`mat_concrete#g2`)
    ///             contribute in proportion to how much frame they own.
    ///   ratio     rendered / source — a RATIO OF MEANS, not a mean of
    ///             ratios. They differ only when two materials with different
    ///             albedos share a logical name; the ratio of means is the
    ///             one that stays exact when they do.
    ///   @n up     the rays this row is a mean OF (rule 3b: every zero ships
    ///             its denominator).
    ///   notup     rays whose material NAME matched this row and which the
    ///             caller's geometry test REJECTED. Not a fault count: it is
    ///             the denominator that tells "this row is the road" from
    ///             "this row was mostly walls". A row that keeps everything
    ///             and a row that drops four fifths must not print alike.
    ///   ^name     the single MATERIAL NAME that contributed the most
    ///             ADMITTED rays to this row — a MODE, not a mean, ties
    ///             broken by ordinal name so the row is stable across runs.
    ///             It exists because a family name hides its members: on
    ///             3a4e335 `concrete` pooled the road, `mat_concrete_b`
    ///             facades and vehicle paint under one heading and no reader
    ///             could tell which of them the number described.
    ///
    /// IT HOLDS NO GEOMETRY TEST AND MUST NOT GROW ONE. `Add` is called for a
    /// ray the caller has already decided is ground; `Drop` is called for one
    /// it has rejected. The name match lives in `SurfaceNames`, the geometry
    /// test lives at the ray site where the hit normal is in hand, and the
    /// arithmetic lives here — three questions, three places, no copy of any
    /// of them anywhere else.
    ///
    /// BOTH SIDES MUST ARRIVE IN THE SAME COLOUR SPACE. This class does no
    /// conversion and cannot check one — it is arithmetic on whatever it is
    /// handed. The caller converts, and the caller's comment names the space.
    /// The signature of getting it wrong is written down in advance, at the
    /// emit site in `SimDirector.GroundMaskRead`: ratios clustering near
    /// 2.05..2.09 are a gamma/linear mismatch, not a lighting gain — and that
    /// trap applies to the RAW rows exactly as it does to the graded ones,
    /// because both numerators go through the same `Color.linear` conversion.
    ///
    /// IT LIVES IN CORE for the reason `SurfaceNames` does: the Game layer
    /// does not compile in this container, so a formatter written there ships
    /// unrun, and an unrun formatter that prints a plausible string is exactly
    /// the silent-instrument fault this project keeps paying for. It holds NO
    /// list of ground surfaces — `AssetLibrary.WetSurfaces` is passed in, so
    /// adding a fifth ground material needs no edit here.
    public sealed class GroundGain
    {
        readonly Dictionary<string, double> _ren = new Dictionary<string, double>();
        readonly Dictionary<string, double> _raw = new Dictionary<string, double>();
        readonly Dictionary<string, double> _src = new Dictionary<string, double>();
        readonly Dictionary<string, long> _n = new Dictionary<string, long>();
        readonly Dictionary<string, long> _rawN = new Dictionary<string, long>();
        readonly Dictionary<string, long> _drop = new Dictionary<string, long>();
        readonly Dictionary<string, Dictionary<string, long>> _mats
            = new Dictionary<string, Dictionary<string, long>>();
        long _rays, _rawRays, _dropped;

        /// ONE RAY, BOTH RENDERS, ONE ADMISSION. `logical` is what the
        /// classifier matched — an empty or null name is DROPPED AND NOT
        /// COUNTED, so the bucketed count that `Emit` prints as
        /// `groundGainRays` can be compared against the mask's own ground-ray
        /// count, and any disagreement between the two classifiers shows up as
        /// a difference rather than as a row quietly landing under the empty
        /// string. (This sentence used to name a `Rays` property; the same
        /// batch that wrote it deleted that property for having no caller,
        /// which is comment decay inside its own repair.)
        ///
        /// THE GRADED AND RAW NUMERATORS ARE TAKEN IN ONE CALL ON PURPOSE.
        /// Two tallies fed by two adjacent statements is the shape that gave
        /// this project four pairs of numbers taken at different instants and
        /// printed as one event; with one entry point the two rows cannot
        /// describe different rays even if somebody later edits the ray site
        /// badly. `rawKnown` is false when the ungraded render did not happen
        /// — that case prints as `nothing_measured` on the raw key and leaves
        /// the graded key untouched, rather than silently reading as raw=0.
        public void Add(string logical, string materialName,
                        double gradedLinear, double sourceLinear,
                        double rawLinear, bool rawKnown)
        {
            var k = Key(logical);
            if (k.Length == 0) return;
            double r, s; long c;
            _ren[k] = (_ren.TryGetValue(k, out r) ? r : 0) + gradedLinear;
            _src[k] = (_src.TryGetValue(k, out s) ? s : 0) + sourceLinear;
            _n[k] = (_n.TryGetValue(k, out c) ? c : 0) + 1;
            _rays++;
            if (rawKnown)
            {
                double w; long d;
                _raw[k] = (_raw.TryGetValue(k, out w) ? w : 0) + rawLinear;
                _rawN[k] = (_rawN.TryGetValue(k, out d) ? d : 0) + 1;
                _rawRays++;
            }
            var mat = Safe(materialName);
            Dictionary<string, long> per;
            if (!_mats.TryGetValue(k, out per)) { per = new Dictionary<string, long>(); _mats[k] = per; }
            long mc;
            per[mat] = (per.TryGetValue(mat, out mc) ? mc : 0) + 1;
        }

        /// A ray whose material NAME matched this row and whose GEOMETRY the
        /// caller rejected. It moves no sum — it is a denominator, and the
        /// only thing that can tell a row describing the road from a row
        /// describing the wall the road runs past.
        public void Drop(string logical)
        {
            var k = Key(logical);
            if (k.Length == 0) return;
            long c;
            _drop[k] = (_drop.TryGetValue(k, out c) ? c : 0) + 1;
            _dropped++;
        }

        /// THE GRADED KEYS — what the committed JPEG holds.
        ///
        /// Rows in the order `logicals` gives so the row order is stable
        /// across runs and diffable. Space-free by construction.
        ///
        /// `maskGroundRays` is the OTHER classifier's count of ground rays,
        /// and the identity to read first is
        /// `admitted + dropped == maskGroundRays`: the mask files a ray here
        /// exactly when it counts it as ground, and this tally then splits
        /// that set in two with the geometry test. A triple that does not add
        /// up is not a statistic, it is the two classifiers disagreeing.
        public string Emit(string[] logicals, long maskGroundRays)
        {
            var rows = new List<string>();
            int have = 0;
            int offered = logicals == null ? 0 : logicals.Length;
            for (int i = 0; i < offered; i++)
            {
                if (string.IsNullOrEmpty(logicals[i])) continue;
                var k = Key(logicals[i]);
                long n, dr;
                if (!_n.TryGetValue(k, out n)) n = 0;
                if (!_drop.TryGetValue(k, out dr)) dr = 0;
                string tail = "@" + n.ToString(CultureInfo.InvariantCulture) + "up/"
                            + dr.ToString(CultureInfo.InvariantCulture) + "notup^" + TopMat(k);
                if (n <= 0)
                {
                    // RAN AND FOUND NONE. The words, not a zero: a material no
                    // ray landed on and a material rendering at black are
                    // different findings with different fixes — and now a
                    // third case joins them, which the `notup` count is the
                    // only thing that can express: a material every ray of
                    // which the geometry test rejected. `kerb` is expected to
                    // read that way and it is a FINDING ABOUT THE OLD ROWS,
                    // not a fault in the filter: a kerb is a 0.2m strip by
                    // construction, so its up-facing top is a sliver and its
                    // vertical face was most of what the old row averaged.
                    rows.Add(k + ":nothing_measured" + tail);
                    continue;
                }
                have++;
                double ren = _ren[k] / n, src = _src[k] / n;
                rows.Add(k + ":" + Num(ren, "0.0000") + "/" + Num(src, "0.0000")
                         + "=" + Ratio(ren, src) + tail);
            }
            string list = rows.Count > 0 ? string.Join(",", rows.ToArray()) : "nothing_measured";
            return "groundGainBy=[" + list + "]"
                 + " groundGainOf=" + have.ToString(CultureInfo.InvariantCulture)
                 + "/" + offered.ToString(CultureInfo.InvariantCulture)
                 + " groundGainRays=" + _rays.ToString(CultureInfo.InvariantCulture)
                 + "/" + _dropped.ToString(CultureInfo.InvariantCulture)
                 + "/" + maskGroundRays.ToString(CultureInfo.InvariantCulture);
        }

        /// THE UNGRADED TWIN — the same rays, the same admission test, read
        /// off a render with `FilmGrade.Bypass` on.
        ///
        /// It prints no `notup` and no `^material`: those describe the
        /// ADMISSION, which is one decision shared by both keys, and printing
        /// them twice would be one number under two names — the thing that
        /// makes a reader believe two measurements exist where there is one.
        /// What it does print is `@<raw>of<admitted>up`, and those two being
        /// equal is the on-the-line proof that the two keys describe one ray
        /// set. They can differ only when the ungraded render failed, and then
        /// the row says `nothing_measured` rather than reading as black.
        public string EmitRaw(string[] logicals)
        {
            var rows = new List<string>();
            int have = 0;
            int offered = logicals == null ? 0 : logicals.Length;
            for (int i = 0; i < offered; i++)
            {
                if (string.IsNullOrEmpty(logicals[i])) continue;
                var k = Key(logicals[i]);
                long n, rn;
                if (!_n.TryGetValue(k, out n)) n = 0;
                if (!_rawN.TryGetValue(k, out rn)) rn = 0;
                string tail = "@" + rn.ToString(CultureInfo.InvariantCulture) + "of"
                            + n.ToString(CultureInfo.InvariantCulture) + "up";
                if (rn <= 0) { rows.Add(k + ":nothing_measured" + tail); continue; }
                have++;
                double raw = _raw[k] / rn, src = _src[k] / rn;
                rows.Add(k + ":" + Num(raw, "0.0000") + "/" + Num(src, "0.0000")
                         + "=" + Ratio(raw, src) + tail);
            }
            string list = rows.Count > 0 ? string.Join(",", rows.ToArray()) : "nothing_measured";
            return "groundGainByRaw=[" + list + "]"
                 + " groundGainRawOf=" + have.ToString(CultureInfo.InvariantCulture)
                 + "/" + offered.ToString(CultureInfo.InvariantCulture)
                 + " groundGainRawRays=" + _rawRays.ToString(CultureInfo.InvariantCulture)
                 + "/" + _rays.ToString(CultureInfo.InvariantCulture);
        }

        /// The MODE of the material names behind a row's admitted rays, or the
        /// word `none` when the row admitted nothing. Ties broken by ordinal
        /// name: an arbitrary winner that changes between runs would read as a
        /// world that changed.
        string TopMat(string k)
        {
            Dictionary<string, long> per;
            if (!_mats.TryGetValue(k, out per) || per.Count == 0) return "none";
            string best = "none"; long bestN = -1;
            foreach (var kv in per)
                if (kv.Value > bestN
                    || (kv.Value == bestN && string.CompareOrdinal(kv.Key, best) < 0))
                { best = kv.Key; bestN = kv.Value; }
            return best;
        }

        static string Ratio(double num, double src)
        {
            // A source albedo of zero cannot be divided, and printing a large
            // number here would read as an enormous gain.
            return src > 1e-9 ? Num(num / src, "0.000") : "source0";
        }

        static string Key(string logical)
        {
            if (string.IsNullOrEmpty(logical)) return "";
            return logical.Trim().ToLowerInvariant();
        }

        /// A MATERIAL NAME IS ASSET DATA AND MAY CONTAIN ANYTHING. The verdict
        /// is space-separated `key=value`, the row list is comma-separated
        /// inside brackets, and this row already uses `:`, `/`, `=`, `@` and
        /// `^` structurally — so every one of those, plus whitespace, is
        /// folded to `_`. Unity's ` (Instance)` suffix goes first because it
        /// is pure noise here and would otherwise become `_(Instance)` on
        /// every row. `crowdBodyWidth` cost a reading by emitting a space; a
        /// name straight out of an imported pack is the same fault waiting.
        static string Safe(string name)
        {
            if (string.IsNullOrEmpty(name)) return "unnamed";
            var n = name.Trim();
            int inst = n.IndexOf(" (Instance)");
            if (inst >= 0) n = n.Substring(0, inst);
            var sb = new System.Text.StringBuilder(n.Length);
            for (int i = 0; i < n.Length; i++)
            {
                char c = n[i];
                bool bad = char.IsWhiteSpace(c) || c == ',' || c == '[' || c == ']'
                           || c == '=' || c == '@' || c == '^' || c == '/' || c == ':';
                sb.Append(bad ? '_' : c);
            }
            var outName = sb.ToString().Trim('_');
            return outName.Length == 0 ? "unnamed" : outName;
        }

        /// INVARIANT CULTURE, deliberately. The verdict is machine-read by
        /// `tools/verdict-read.py` and half a dozen greps that all expect a
        /// dot; a runner in a comma-decimal locale would emit `0,417` and
        /// every reader would take `0` and drop the rest — the same silent
        /// truncation the no-spaces rule exists for, one character further in.
        static string Num(double v, string fmt)
        {
            return v.ToString(fmt, CultureInfo.InvariantCulture);
        }
    }
}
