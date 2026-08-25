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
    ///             every ray in this run that landed on this material, across
    ///             all district shots. Not a peak, not a median, not per shot.
    ///   source    a RAY-WEIGHTED MEAN of the same rays' material albedo,
    ///             sampled at the same ray. Ray-weighted and not per-material
    ///             so that graded copies of one logical (`mat_concrete#g2`)
    ///             contribute in proportion to how much frame they own.
    ///   ratio     rendered / source — a RATIO OF MEANS, not a mean of
    ///             ratios. They differ only when two materials with different
    ///             albedos share a logical name; the ratio of means is the
    ///             one that stays exact when they do.
    ///   @n        the rays this row is a mean OF (rule 3b: every zero ships
    ///             its denominator).
    ///
    /// BOTH SIDES MUST ARRIVE IN THE SAME COLOUR SPACE. This class does no
    /// conversion and cannot check one — it is arithmetic on whatever it is
    /// handed. The caller converts, and the caller's comment names the space.
    /// The signature of getting it wrong is written down in advance, at the
    /// emit site in `SimDirector.GroundMaskRead`: ratios clustering near
    /// 2.05..2.09 are a gamma/linear mismatch, not a lighting gain.
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
        readonly Dictionary<string, double> _src = new Dictionary<string, double>();
        readonly Dictionary<string, long> _n = new Dictionary<string, long>();
        long _rays;

        /// One ray. `logical` is what the classifier matched — an empty or
        /// null name is DROPPED AND NOT COUNTED, so the bucketed count that
        /// `Emit` prints as `groundGainRays` can be compared against the
        /// mask's own ground-ray count, and any disagreement between the two
        /// classifiers shows up as a difference rather than as a row quietly
        /// landing under the empty string. (This sentence used to name a
        /// `Rays` property; the same batch that wrote it deleted that
        /// property for having no caller, which is comment decay inside its
        /// own repair.)
        public void Add(string logical, double renderedLinear, double sourceLinear)
        {
            if (string.IsNullOrEmpty(logical)) return;
            var k = logical.Trim().ToLowerInvariant();
            if (k.Length == 0) return;
            double r, s; long c;
            _ren[k] = (_ren.TryGetValue(k, out r) ? r : 0) + renderedLinear;
            _src[k] = (_src.TryGetValue(k, out s) ? s : 0) + sourceLinear;
            _n[k] = (_n.TryGetValue(k, out c) ? c : 0) + 1;
            _rays++;
        }

        /// The three keys, space-free, in the order `logicals` gives so the
        /// row order is stable across runs and diffable.
        ///
        /// `maskGroundRays` is the OTHER classifier's count of ground rays.
        /// The two are equal by construction — the mask buckets a ray here
        /// exactly when it counts it as ground — so `groundGainRays=a/b` with
        /// a != b is not a statistic, it is the two classifiers disagreeing,
        /// and that is the first thing to read on this line.
        public string Emit(string[] logicals, long maskGroundRays)
        {
            var rows = new List<string>();
            int have = 0;
            int offered = logicals == null ? 0 : logicals.Length;
            for (int i = 0; i < offered; i++)
            {
                if (string.IsNullOrEmpty(logicals[i])) continue;
                var k = logicals[i].Trim().ToLowerInvariant();
                long n;
                if (!_n.TryGetValue(k, out n) || n <= 0)
                {
                    // RAN AND FOUND NONE. The words, not a zero: a material no
                    // ray landed on and a material rendering at black are
                    // different findings with different fixes.
                    rows.Add(k + ":nothing_measured@0");
                    continue;
                }
                have++;
                double ren = _ren[k] / n, src = _src[k] / n;
                string ratio = src > 1e-9
                    ? Num(ren / src, "0.000")
                    // A source albedo of zero cannot be divided, and printing
                    // a large number here would read as an enormous gain.
                    : "source0";
                rows.Add(k + ":" + Num(ren, "0.0000") + "/" + Num(src, "0.0000")
                         + "=" + ratio + "@" + n.ToString(CultureInfo.InvariantCulture));
            }
            string list = rows.Count > 0 ? string.Join(",", rows.ToArray()) : "nothing_measured";
            return "groundGainBy=[" + list + "]"
                 + " groundGainOf=" + have.ToString(CultureInfo.InvariantCulture)
                 + "/" + offered.ToString(CultureInfo.InvariantCulture)
                 + " groundGainRays=" + _rays.ToString(CultureInfo.InvariantCulture)
                 + "/" + maskGroundRays.ToString(CultureInfo.InvariantCulture);
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
