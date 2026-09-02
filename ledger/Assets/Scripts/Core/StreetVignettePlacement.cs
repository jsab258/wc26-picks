using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Ledger.Core
{
    /// DID THE VIGNETTE'S OBJECTS LAND ON THE GROUND, AND WAS THERE ANY
    /// GROUND UNDER THEM TO LAND ON.
    ///
    /// TWO HALVES, AND THE SECOND ONE IS THE ONE THAT GETS LEFT OUT.
    /// `.claude/rules/instruments.md` made this a standing pattern on 25
    /// August after eight blocks were found hanging over open sea at a foot
    /// gap of exactly 0.00. The gap was perfect because there was nothing
    /// under them to be a gap FROM. So every row below prints the distance to
    /// the datum AND how many probes found no datum at all, and neither
    /// number is ever printed without the other.
    ///
    /// BROKEN DOWN PER THE AXIS PLACEMENT ACTUALLY VARIES ON, which for a
    /// street is where across it (the edge: carriageway, channel, kerb,
    /// footway, plot) and where along it (the region, one row per bay module).
    /// NEVER PER CAMERA: a camera row would tell you which picture a fault is
    /// visible in, which is a different question and the one that hid the
    /// eight blocks, since all eight were off-camera.
    ///
    /// A SINGLE AVERAGED GAP IS THE EXACT SHAPE THAT FAILED, so there is no
    /// mean here at all. The median says whether placement is normally right;
    /// floatMax and sinkMax say whether anything is wrong and name it; the
    /// datum count says whether the question was even askable.
    ///
    /// NOTE ON THE NAME: `Vignette` elsewhere in this repository means the
    /// LENS vignette (`LightModel.VignetteCorner`). Everything to do with the
    /// D1b street scene is prefixed `StreetVignette`.
    public sealed class StreetVignettePlacement
    {
        /// One bucket of probes: the whole run, one edge, or one region. The
        /// arithmetic is identical for all three, which is why there is one
        /// class and not three.
        sealed class Bucket
        {
            public int Probes, Missing;
            public double FloatMax = double.NegativeInfinity, SinkMax = double.NegativeInfinity;
            public string FloatAt = "none", SinkAt = "none";
            /// Every landed probe's absolute gap, kept so the row can print
            /// a MEDIAN. A mean is what hid the eight blocks: one object a
            /// metre in the air disappears into three hundred good ones.
            /// Probes that found no datum are NOT in here, which is why
            /// `landed` is printed beside the median as its denominator.
            public readonly List<double> Abs = new List<double>();

            public void Add(double signed, bool hit, string name)
            {
                Probes++;
                if (!hit) { Missing++; return; }
                Abs.Add(Math.Abs(signed));
                if (signed > FloatMax) { FloatMax = signed; FloatAt = name; }
                if (-signed > SinkMax) { SinkMax = -signed; SinkAt = name; }
            }

            public double Median()
            {
                if (Abs.Count == 0) return double.NaN;
                var a = Abs.ToArray();
                Array.Sort(a);
                int n = a.Length;
                return n % 2 == 1 ? a[n / 2] : (a[n / 2 - 1] + a[n / 2]) * 0.5;
            }
        }

        readonly Bucket _all = new Bucket();
        readonly Dictionary<string, Bucket> _edges = new Dictionary<string, Bucket>();
        readonly Dictionary<string, Bucket> _regions = new Dictionary<string, Bucket>();
        readonly Dictionary<string, int> _perBom = new Dictionary<string, int>();
        int _pieces;

        /// How many rows of each breakdown are printed. Small because the
        /// verdict file is read whole, and it ANNOUNCES ITSELF whenever it
        /// bites: a `head -N` that outgrew its input once read as "three of
        /// five systems failed" when nothing was broken.
        public const int MaxRows = 6;

        /// The total object count, which is the denominator for "how many of
        /// them were probed at all". A scene of five hundred pieces with two
        /// probed is a clean report that means nothing.
        public void NotePieces(int n) => _pieces = n;

        /// ONE PROBE. `footY` is what the PLAN said the underside sits at;
        /// `datumHit` and `datumY` are what the emitter's raycast found in the
        /// scene it actually built. The comparison is between the plan and the
        /// engine, which is the only version of this measurement that can
        /// catch an emitter bug: a datum derived from the plan would be the
        /// instrument measuring itself.
        ///
        /// `name` must contain no spaces. Every reader of a `key=value` line
        /// in this project splits on whitespace and truncates in silence.
        public void Probe(string bom, string edge, string region, string name,
                          double footY, bool datumHit, double datumY)
        {
            double signed = footY - datumY;      // positive: floating above the ground
            string tag = Safe(name);
            _all.Add(signed, datumHit, tag);
            Of(_edges, edge ?? "unknown").Add(signed, datumHit, tag);
            Of(_regions, region ?? "unknown").Add(signed, datumHit, tag);
            if (bom != null)
            {
                _perBom.TryGetValue(bom, out int n);
                _perBom[bom] = n + 1;
            }
        }

        static Bucket Of(Dictionary<string, Bucket> d, string k)
        {
            if (!d.TryGetValue(k, out var b)) { b = new Bucket(); d[k] = b; }
            return b;
        }

        static string Safe(string s)
        {
            if (string.IsNullOrEmpty(s)) return "unnamed";
            var sb = new StringBuilder(s.Length);
            foreach (var c in s) sb.Append(char.IsWhiteSpace(c) ? '_' : c);
            return sb.ToString();
        }

        /// THE WHOLE-RUN LINE PLUS THE TWO BREAKDOWNS, one string per line,
        /// caller prefixes them. Whole-run numbers stay on the whole-run line
        /// and per-bucket numbers on their own row, so a grep that merges two
        /// lines cannot invent a pair that never existed.
        public List<string> Report()
        {
            var outp = new List<string>();
            if (_all.Probes == 0)
            {
                // THE WORDS, NOT A ZERO. A run that measured nothing and a run
                // that measured everything and found nothing wrong read
                // identically as `datumMissing=0`, and they have opposite next
                // actions.
                outp.Add(string.Format(CultureInfo.InvariantCulture,
                    "placement nothing measured (pieces={0} probes=0; no footed piece reached the probe)",
                    _pieces));
                return outp;
            }
            outp.Add("placement " + Row(_all, "pieces=" + _pieces.ToString(CultureInfo.InvariantCulture)));
            Breakdown(outp, "place/edge", _edges);
            Breakdown(outp, "place/region", _regions);
            return outp;
        }

        void Breakdown(List<string> outp, string key, Dictionary<string, Bucket> d)
        {
            var keys = new List<string>(d.Keys);
            // Worst first, so what the cap drops is always the least
            // interesting rows rather than an alphabetical accident.
            keys.Sort((a, b) =>
            {
                int c = d[b].Missing.CompareTo(d[a].Missing);
                if (c != 0) return c;
                c = Cmp(d[b].FloatMax, d[a].FloatMax);
                if (c != 0) return c;
                return string.CompareOrdinal(a, b);
            });
            int shown = Math.Min(MaxRows, keys.Count);
            for (int i = 0; i < shown; i++)
                outp.Add(key + " " + keys[i] + " " + Row(d[keys[i]], null));
            if (keys.Count > shown)
                outp.Add(string.Format(CultureInfo.InvariantCulture,
                    "{0} (+{1} more of {2} not shown; sorted worst first)",
                    key, keys.Count - shown, keys.Count));
        }

        static int Cmp(double a, double b)
        {
            bool na = double.IsNegativeInfinity(a) || double.IsNaN(a);
            bool nb = double.IsNegativeInfinity(b) || double.IsNaN(b);
            if (na && nb) return 0;
            if (na) return -1;
            if (nb) return 1;
            return a.CompareTo(b);
        }

        static string Row(Bucket b, string extra)
        {
            var sb = new StringBuilder();
            if (extra != null) sb.Append(extra).Append(' ');
            sb.Append("probes=").Append(b.Probes.ToString(CultureInfo.InvariantCulture));
            // HALF TWO, AND IT IS FIRST BECAUSE IT IS THE ONE THAT GETS
            // SKIMMED PAST. Always with its denominator.
            sb.Append(" datumMissing=").Append(b.Missing.ToString(CultureInfo.InvariantCulture))
              .Append('/').Append(b.Probes.ToString(CultureInfo.InvariantCulture));
            int landed = b.Probes - b.Missing;
            if (landed == 0)
            {
                // Every probe in this bucket found nothing under it, so there
                // is no gap to report and saying `gapMax=0.000` would be a
                // clean number describing a hole.
                sb.Append(" gap=nothing-landed-here");
                return sb.ToString();
            }
            sb.Append(" landed=").Append(landed.ToString(CultureInfo.InvariantCulture));
            sb.Append(" gapMedian=").Append(F(b.Median()));
            // FLOAT AND SINK SEPARATELY. A piece 2 mm into the pavement and a
            // piece 2 mm above it are the same absolute number and only one of
            // them is visible as a line of light under an object.
            sb.Append(" floatMax=").Append(F(Math.Max(0, b.FloatMax)))
              .Append("/at=").Append(b.FloatAt);
            sb.Append(" sinkMax=").Append(F(Math.Max(0, b.SinkMax)))
              .Append("/at=").Append(b.SinkAt);
            return sb.ToString();
        }

        static string F(double v) =>
            double.IsNaN(v) || double.IsInfinity(v)
                ? "n/a"
                : v.ToString("0.000", CultureInfo.InvariantCulture);

        /// DID EVERY BILL-OF-MATERIALS LINE THE SCENE CLAIMS ACTUALLY GET
        /// EMITTED. Rule 6 in one line: built is not running, and a PROC line
        /// that emitted nothing is a line that exists only in a document.
        ///
        /// `authorised` is the set the scene is answerable for. A line in it
        /// with no pieces is named, because a silent zero here is exactly the
        /// case a bill of materials exists to prevent.
        public static string BomReport(Dictionary<string, int> perBom, IList<string> authorised)
        {
            var missing = new List<string>();
            int placed = 0, pieces = 0;
            foreach (var id in authorised)
            {
                perBom.TryGetValue(id, out int n);
                if (n > 0) { placed++; pieces += n; }
                else missing.Add(id);
            }
            var sb = new StringBuilder();
            sb.Append("bom placed=").Append(placed.ToString(CultureInfo.InvariantCulture))
              .Append('/').Append(authorised.Count.ToString(CultureInfo.InvariantCulture))
              .Append(" pieces=").Append(pieces.ToString(CultureInfo.InvariantCulture));
            sb.Append(" unplaced=");
            if (missing.Count == 0) sb.Append("none");
            else
            {
                for (int i = 0; i < missing.Count && i < MaxRows; i++)
                {
                    if (i > 0) sb.Append(',');
                    sb.Append(missing[i]);
                }
                if (missing.Count > MaxRows)
                    sb.Append(",(+").Append((missing.Count - MaxRows).ToString(CultureInfo.InvariantCulture))
                      .Append("more)");
            }
            return sb.ToString();
        }
    }
}
