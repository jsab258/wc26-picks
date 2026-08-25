using System.Collections.Generic;
using System.Globalization;

namespace Ledger.Core
{
    /// THE CONVERGENCE PANEL (R1) — the four VALUE BANDS of a still, the
    /// shadowed:lit ratio, the ground's tonal spread, and whether the
    /// reference ORDER holds.
    ///
    /// WHY IT EXISTS, in the director's words
    /// (`decision-ground-albedo.md`, "the visual plan is REPLACED", §1):
    /// **VALUE-STRUCTURE INVERSION.** All five GTA references have sky as the
    /// brightest broad surface and ground mid-dark with the widest tonal
    /// variety; our noon stills have near-white ground under a storm-dark
    /// sky — the inverse. Nothing in this project measures that, so a
    /// 3.07x exposure lift shipped and two days went to measuring its
    /// SYMPTOM. This is the number that would have said so on the first
    /// landing.
    ///
    /// THERE IS NO BOUND HERE AND MUST NOT BE ONE YET. §5 of that ruling:
    /// the ORDER comes from the references, the MARGINS come later from the
    /// landed series. Every method below is a printer. Nothing compares
    /// against a constant, nothing returns a pass/fail for a gate to read,
    /// and the ordering row reports which rungs hold as a TALLY — three
    /// separate yes/no answers, so a reader can see WHICH rung broke rather
    /// than a single word that hides it. Setting a threshold from one run is
    /// the fault this project has paid for most often (rule 2).
    ///
    /// WHAT STATISTIC EACH NUMBER IS — said here because it is the one thing
    /// a reader cannot recover from the number itself:
    ///
    ///   band value    a MEDIAN of the committed frame's luma over the
    ///                 samples classified into that band, PER SHOT. Not a
    ///                 peak, not a run mean. A median answers "is this how
    ///                 the band looks"; it structurally cannot see a fault
    ///                 touching under half the band, which is why the
    ///                 sample COUNT rides beside every one of them and why
    ///                 `groundSpread` (a p10..p90) is a separate row.
    ///   `@n`          the samples that median is a median OF (rule 3b).
    ///                 `none@0` is a band the shot contained none of, which
    ///                 is a reading — a frame with no sunlit wall in it —
    ///                 and must not print as `0.000`.
    ///   shadow:lit    a RATIO OF TWO MEDIANS taken from ONE frame at ONE
    ///                 instant over DISJOINT sample sets. They can move
    ///                 independently — a cast shadow can deepen while the
    ///                 sunlit wall stands still — so this is two
    ///                 measurements, not one number twice. Both counts are
    ///                 printed because the ratio of a 900-sample median to a
    ///                 4-sample median is a different kind of fact.
    ///   groundSpread  p90 MINUS p10 of the ground samples' luma in ONE
    ///                 shot, printed with the two percentiles it is the
    ///                 difference of. "Widest tonal variety" as a number.
    ///                 It is a spread ACROSS the ground samples of a frame,
    ///                 NOT `ref-bench`'s `groundPatch`, which is a median
    ///                 over LOCAL 64px windows — different question, and
    ///                 the two may not be quoted interchangeably.
    ///   albedoOrder   adjacent-pair CONCORDANCE: the ground materials this
    ///                 shot saw, sorted ascending by SOURCE albedo, with a
    ///                 count of how many adjacent pairs also ascend on the
    ///                 RENDERED side. `2of2` is not a percentage and not a
    ///                 correlation.
    ///   horizonRow    a MEDIAN over grid COLUMNS of where the top-connected
    ///                 sky run ends, as a fraction from the TOP of frame.
    ///                 OUR SIDE ONLY — see `HorizonRow`.
    ///
    /// IT HOLDS NO CLASSIFIER AND MUST NOT GROW ONE. The caller decides which
    /// band a sample is in — that decision needs a hit normal, a sun vector
    /// and a shadow raycast, none of which exist in Core. What lives here is
    /// the arithmetic and the string, for the reason `SurfaceNames` and
    /// `GroundGain` live here: the Game layer does not compile in this
    /// container, so a formatter written there ships UNRUN, and an unrun
    /// formatter printing a plausible string is the silent-instrument
    /// failure this project keeps paying for.
    ///
    /// IT HOLDS NO LIST OF GROUND SURFACES EITHER. Material names arrive as
    /// arguments; `AssetLibrary.WetSurfaces` remains the only list.
    public sealed class ValuePanel
    {
        /// The four bands of the reference ordering, plus the bin for
        /// everything that is none of them. `Other` is not a fault: a parked
        /// car, a body, a kerb face and a sloped roof are all legitimately
        /// outside a four-way value split, and they are counted so the four
        /// bands' sum can be checked against the rays cast.
        public const int Sky = 0, LitWall = 1, Ground = 2, Shadow = 3, Other = 4;
        public const int BandCount = 5;

        /// The order §5 of the ruling requires, as three adjacent
        /// comparisons: sky > litWall, litWall > ground, ground > shadow.
        /// The NAMES are here so the row and this comment cannot drift.
        static readonly string[] RungNames = { "sky>lit", "lit>gnd", "gnd>shd" };

        /// Rows are capped so one key cannot become a paragraph, and the cap
        /// ANNOUNCES ITSELF (`refPanelListed=shown/total`) because an
        /// unannounced truncation reads as a finding — a `| head -3` once
        /// read as "three of five bodies failed".
        public const int RowCap = 24;

        readonly List<string> _bands = new List<string>();
        readonly List<string> _shadowLit = new List<string>();
        readonly List<string> _spread = new List<string>();
        readonly List<string> _order = new List<string>();
        readonly List<string> _albedo = new List<string>();
        readonly List<string> _horizon = new List<string>();

        /// WHOLE-RUN DENOMINATORS, cumulative over every shot the panel was
        /// offered. `shots measured` and `shots offered` differ when a frame
        /// could not be read back; the ray chain says WHERE classification
        /// died, in the same shape as `groundMaskRays` — cast, hit,
        /// with-a-renderer, then the five bands.
        long _shotsOffered, _shotsMeasured;
        long _raysCast, _raysHit, _raysRenderer;
        readonly long[] _bandRays = new long[BandCount];

        /// The rungs that HELD, and the rungs that could be JUDGED, summed
        /// over every shot. A rung whose band was empty is judged by nobody
        /// and counts in neither — which is why this is two numbers and not
        /// a percentage.
        long _rungsHeld, _rungsJudged;

        /// ONE SHOT'S SAMPLES. Opened at the shot, closed at the shot, so a
        /// row cannot be assembled out of two different frames — the same
        /// rule `_groundMeanBy` follows and for the same reason.
        public sealed class ShotAcc
        {
            internal readonly string Name;
            internal readonly List<double>[] Band = new List<double>[BandCount];
            internal readonly Dictionary<string, List<double>> GroundRendered
                = new Dictionary<string, List<double>>();
            internal readonly Dictionary<string, double> GroundSourceSum
                = new Dictionary<string, double>();
            internal readonly Dictionary<string, long> GroundSourceN
                = new Dictionary<string, long>();
            internal long RaysCast, RaysHit, RaysRenderer;

            internal ShotAcc(string name)
            {
                Name = Safe(name);
                for (int i = 0; i < BandCount; i++) Band[i] = new List<double>();
            }

            /// A ray that was cast. Called for EVERY sample including the
            /// ones that hit nothing, or the chain loses its denominator.
            public void CountCast() { RaysCast++; }
            public void CountHit() { RaysHit++; }
            public void CountRenderer() { RaysRenderer++; }

            /// One classified sample. `luma` is the committed frame's own
            /// pixel at this sample — the caller reads it from the texture
            /// the JPEG was encoded from, so the number and the picture are
            /// the same instant.
            public void Add(int band, double luma)
            {
                if (band < 0 || band >= BandCount) band = Other;
                Band[band].Add(luma);
            }

            /// A GROUND sample, additionally bucketed by material. Called
            /// AFTER `Add(Ground, luma)` by the same statement in the caller,
            /// with the SAME luma — the numerator and its material come from
            /// one ray at one instant, never from two loops agreeing.
            public void AddGround(string logical, double luma, double sourceAlbedo)
            {
                var k = Key(logical);
                if (k.Length == 0) return;
                List<double> lst;
                if (!GroundRendered.TryGetValue(k, out lst))
                { lst = new List<double>(); GroundRendered[k] = lst; }
                lst.Add(luma);
                double s; GroundSourceSum.TryGetValue(k, out s);
                GroundSourceSum[k] = s + sourceAlbedo;
                long n; GroundSourceN.TryGetValue(k, out n);
                GroundSourceN[k] = n + 1;
            }
        }

        public ShotAcc Open(string shotName)
        {
            _shotsOffered++;
            return new ShotAcc(shotName);
        }

        /// FOLD ONE SHOT'S SAMPLES INTO THE PANEL. Every row for this shot is
        /// formatted here, from this shot's own samples, in one call.
        ///
        /// `horizonRow` is the caller's `HorizonRow(...)` result and its
        /// column counts; pass -1 and 0/0 when the caller did not compute it.
        public void Land(ShotAcc s, double horizonRow, int horizonCols, int horizonColsTotal)
        {
            if (s == null) return;
            _raysCast += s.RaysCast; _raysHit += s.RaysHit; _raysRenderer += s.RaysRenderer;
            for (int i = 0; i < BandCount; i++) _bandRays[i] += s.Band[i].Count;
            if (s.RaysCast <= 0) return;
            _shotsMeasured++;

            double sky = Median(s.Band[Sky]), lit = Median(s.Band[LitWall]);
            double gnd = Median(s.Band[Ground]), shd = Median(s.Band[Shadow]);

            _bands.Add(s.Name + ":sky" + BandVal(sky, s.Band[Sky].Count)
                       + "/lit" + BandVal(lit, s.Band[LitWall].Count)
                       + "/gnd" + BandVal(gnd, s.Band[Ground].Count)
                       + "/shd" + BandVal(shd, s.Band[Shadow].Count)
                       + "/oth" + BandVal(Median(s.Band[Other]), s.Band[Other].Count));

            // SHADOW OVER LIT, with BOTH counts. `..` separates the two
            // denominators because a `/` is already structural inside the
            // value and a space would truncate every reader.
            string ratio = (s.Band[Shadow].Count == 0 || s.Band[LitWall].Count == 0)
                ? "none"
                : (lit > 1e-9 ? Num(shd / lit, "0.000") : "lit0");
            _shadowLit.Add(s.Name + ":" + ratio
                           + "@" + s.Band[Shadow].Count + ".." + s.Band[LitWall].Count);

            // GROUND SPREAD, printed as the two percentiles it is the
            // difference OF, so a wide spread low down and a wide spread up
            // in the highlights are distinguishable.
            if (s.Band[Ground].Count == 0)
                _spread.Add(s.Name + ":none@0");
            else
            {
                var g = new List<double>(s.Band[Ground]); g.Sort();
                double p10 = Percentile(g, 0.10), p90 = Percentile(g, 0.90);
                _spread.Add(s.Name + ":" + Num(p10, "0.000") + ".." + Num(p90, "0.000")
                            + "=" + Num(p90 - p10, "0.000") + "@" + g.Count);
            }

            // THE ORDERING, RUNG BY RUNG. `y` held, `n` did not, `?` could
            // not be judged because one of its two bands had no samples in
            // this frame. Three separate answers and their tally, so a
            // reader sees WHICH rung broke; a single word would hide it.
            var rungs = new string[3];
            int held = 0, judged = 0;
            Rung(s.Band[Sky].Count, s.Band[LitWall].Count, sky, lit, ref rungs[0], ref held, ref judged);
            Rung(s.Band[LitWall].Count, s.Band[Ground].Count, lit, gnd, ref rungs[1], ref held, ref judged);
            Rung(s.Band[Ground].Count, s.Band[Shadow].Count, gnd, shd, ref rungs[2], ref held, ref judged);
            _rungsHeld += held; _rungsJudged += judged;
            _order.Add(s.Name + ":" + RungNames[0] + rungs[0]
                       + "/" + RungNames[1] + rungs[1]
                       + "/" + RungNames[2] + rungs[2]
                       + "=" + held + "of" + judged);

            _albedo.Add(s.Name + ":" + AlbedoChain(s));

            _horizon.Add(s.Name + ":"
                         + (horizonRow < 0 ? "none" : Num(horizonRow, "0.000"))
                         + "@" + horizonCols + "/" + horizonColsTotal);
        }

        static void Rung(int upperN, int lowerN, double upper, double lower,
                         ref string mark, ref int held, ref int judged)
        {
            if (upperN == 0 || lowerN == 0) { mark = "?"; return; }
            judged++;
            if (upper > lower) { mark = "y"; held++; }
            else mark = "n";
        }

        /// The shot's ground materials sorted ascending by SOURCE albedo,
        /// each printed `<name><source>:<rendered>`, joined by `<` because
        /// that character is the assertion the sort makes true on the source
        /// side. The tally counts adjacent pairs on which the RENDERED side
        /// ascends too — which is §5's "rendered ground lumas ordered as
        /// source albedos", with no constant anywhere in it.
        ///
        /// Two materials at the same source albedo carry NO ordering claim,
        /// so their join prints `~` and the pair is in neither half of the
        /// tally — the same treatment a rung with an empty band gets, and for
        /// the same reason: marking it either way would invent a requirement
        /// the references never made.
        static string AlbedoChain(ShotAcc s)
        {
            if (s.GroundRendered.Count == 0) return "nothing_measured@0";
            var names = new List<string>(s.GroundRendered.Keys);
            names.Sort(delegate (string a, string b)
            {
                double sa = SrcMean(s, a), sb = SrcMean(s, b);
                int c = sa.CompareTo(sb);
                return c != 0 ? c : string.CompareOrdinal(a, b);
            });
            var sb2 = new System.Text.StringBuilder();
            long rays = 0;
            int held = 0, pairs = 0;
            double prevRen = 0, prevSrc = 0;
            for (int i = 0; i < names.Count; i++)
            {
                var lst = new List<double>(s.GroundRendered[names[i]]); lst.Sort();
                double ren = Percentile(lst, 0.50);
                double src = SrcMean(s, names[i]);
                rays += lst.Count;
                if (i > 0)
                {
                    // A TIE ON THE SOURCE SIDE IS IN NEITHER HALF OF THE
                    // TALLY, and it says so with `~` rather than `<`. Two
                    // materials at the same albedo carry no ordering claim,
                    // so counting such a pair either way would invent a
                    // requirement the references never made — the same
                    // treatment a rung with an empty band gets.
                    bool claim = prevSrc + 1e-9 < src;
                    sb2.Append(claim ? '<' : '~');
                    if (claim) { pairs++; if (prevRen < ren) held++; }
                }
                sb2.Append(names[i]).Append(Num(src, "0.000"))
                   .Append(':').Append(Num(ren, "0.000"));
                prevRen = ren; prevSrc = src;
            }
            sb2.Append('=').Append(held).Append("of").Append(pairs)
               .Append("@m").Append(names.Count).Append("/n").Append(rays);
            return sb2.ToString();
        }

        static double SrcMean(ShotAcc s, string k)
        {
            long n; double sum;
            if (!s.GroundSourceN.TryGetValue(k, out n) || n <= 0) return 0;
            s.GroundSourceSum.TryGetValue(k, out sum);
            return sum / n;
        }

        /// WHERE THE SKY MASS ENDS, as a fraction from the TOP of frame — the
        /// number the ref cameras' PITCH is set from, so that pitch stops
        /// being taste and becomes a reading (rule 2's order of operations:
        /// ship the printer, read the series, then set the value).
        ///
        /// `skyByCell` is the caller's grid in the caller's own layout: `gx`
        /// columns, `gy` rows, index `row * gx + col`, ROW 0 AT THE BOTTOM —
        /// Unity's `GetPixels` order and viewport v, which agree with no
        /// flip. The walk starts at the TOP row and stops at the first cell
        /// that is not sky, per column; the answer is the MEDIAN over the
        /// columns THAT HAD ANY SKY AT ALL, and the count of those columns is
        /// returned beside it — a frame with sky in four columns and a frame
        /// with sky in sixty must not print alike.
        ///
        /// OUR SIDE ONLY. It is NOT comparable to the reference frames to
        /// three decimals and must never be gated against them: ours
        /// classifies sky as "the ray hit nothing", which needs a depth
        /// buffer, and any reference-side equivalent must threshold on
        /// colour. Two instruments, by construction — the thing this project
        /// forbids comparing. What it CAN do is say where our own horizon
        /// sits across a landed series, which is all the pitch decision
        /// needs.
        public static double HorizonRow(bool[] skyByCell, int gx, int gy, out int colsWithSky)
        {
            colsWithSky = 0;
            if (skyByCell == null || gx <= 0 || gy <= 0
                || skyByCell.Length < gx * gy) return -1;
            var ends = new List<double>();
            for (int c = 0; c < gx; c++)
            {
                int run = 0;
                for (int r = gy - 1; r >= 0; r--)
                {
                    if (!skyByCell[r * gx + c]) break;
                    run++;
                }
                if (run == 0) continue;
                colsWithSky++;
                // The run covers the top `run` rows; it ends at the fraction
                // of frame height `run / gy` measured DOWN from the top.
                ends.Add(run / (double)gy);
            }
            if (ends.Count == 0) return -1;
            ends.Sort();
            return Percentile(ends, 0.50);
        }

        // ---- the done-line rows -------------------------------------------
        //
        // EVERY ONE OF THESE IS A WHOLE-RUN VALUE and belongs on the done
        // line. The per-shot numbers inside them are formatted at the shot;
        // what makes them done-line rows is that the LIST is complete only
        // when the run ends. Splitting them onto the shot lines would put the
        // same key on twenty lines, which `verdict-read.py` refuses.

        public string Bands() => Rows(_bands);
        public string ShadowLit() => Rows(_shadowLit);
        public string Spread() => Rows(_spread);
        public string Order() => Rows(_order);
        public string AlbedoOrder() => Rows(_albedo);
        public string Horizon() => Rows(_horizon);

        /// SHOTS MEASURED OVER SHOTS OFFERED. `0/0` is "the panel never ran";
        /// `0/19` is "it ran nineteen times and read nothing back", which is a
        /// fault. They must not print alike (rule 3b).
        public string Shots() => _shotsMeasured + "/" + _shotsOffered;

        /// THE RAY CHAIN, cumulative over the whole run, in the order a
        /// reader debugs it: cast, hit something, that something had a
        /// renderer, then the five bands. `sky` is deliberately counted from
        /// rays that hit NOTHING, so `cast - hit == sky` is an identity a
        /// reader can check on the printed line.
        public string Rays() =>
            _raysCast + "/" + _raysHit + "/" + _raysRenderer
            + "/sky" + _bandRays[Sky] + "/lit" + _bandRays[LitWall]
            + "/gnd" + _bandRays[Ground] + "/shd" + _bandRays[Shadow]
            + "/oth" + _bandRays[Other];

        /// RUNGS HELD OVER RUNGS JUDGED, summed over every shot — a COUNT,
        /// not a rate, and not a gate. A rung nobody could judge (an empty
        /// band) is in neither number, so a run that photographed no sunlit
        /// wall reads as a small denominator rather than as a failure.
        public string Rungs() => _rungsHeld + "/" + _rungsJudged;

        /// How many rows the capped lists actually show, over how many exist.
        public string Listed()
        {
            int total = _bands.Count;
            return (total > RowCap ? RowCap : total) + "/" + total;
        }

        static string Rows(List<string> rows)
        {
            if (rows == null || rows.Count == 0) return "nothing_measured";
            var sb = new System.Text.StringBuilder("[");
            int n = rows.Count < RowCap ? rows.Count : RowCap;
            for (int i = 0; i < n; i++)
            {
                if (i > 0) sb.Append(',');
                sb.Append(rows[i]);
            }
            // THE CAP ANNOUNCES ITSELF, inside the bracket so the whole value
            // is still one whitespace-free token.
            if (rows.Count > RowCap)
                sb.Append(",+").Append(rows.Count - RowCap).Append("more-not-shown");
            return sb.Append(']').ToString();
        }

        static string BandVal(double median, int n) =>
            n == 0 ? "none@0" : Num(median, "0.000") + "@" + n;

        /// MEDIAN of a list, -1 for empty. -1 can never be a luma, so an
        /// empty band cannot be read as a black one — and every caller of
        /// this prints `none@0` for that case anyway.
        static double Median(List<double> v)
        {
            if (v == null || v.Count == 0) return -1;
            var s = new List<double>(v); s.Sort();
            return Percentile(s, 0.50);
        }

        /// Percentile of an ALREADY-SORTED list, by linear interpolation
        /// between the two neighbouring samples. Used for p10/p50/p90 so the
        /// three cannot use three different conventions.
        internal static double Percentile(List<double> sorted, double q)
        {
            if (sorted == null || sorted.Count == 0) return -1;
            if (sorted.Count == 1) return sorted[0];
            double pos = q * (sorted.Count - 1);
            int lo = (int)pos;
            int hi = lo + 1 < sorted.Count ? lo + 1 : sorted.Count - 1;
            double f = pos - lo;
            return sorted[lo] + (sorted[hi] - sorted[lo]) * f;
        }

        static string Key(string logical) =>
            string.IsNullOrEmpty(logical) ? "" : logical.Trim().ToLowerInvariant();

        /// A SHOT NAME IS FREE TEXT AND THE VERDICT IS SPACE-SEPARATED. This
        /// row already uses `:`, `/`, `=`, `@`, `<`, `,`, `[` and `]`
        /// structurally, so every one of them plus whitespace folds to `_`.
        /// `crowdBodyWidth` cost a reading by emitting a single space.
        static string Safe(string name)
        {
            if (string.IsNullOrEmpty(name)) return "unnamed";
            var sb = new System.Text.StringBuilder(name.Length);
            for (int i = 0; i < name.Length; i++)
            {
                char c = name[i];
                bool bad = char.IsWhiteSpace(c) || c == ',' || c == '[' || c == ']'
                           || c == '=' || c == '@' || c == '/' || c == ':'
                           || c == '<' || c == '>';
                sb.Append(bad ? '_' : c);
            }
            var outName = sb.ToString().Trim('_');
            return outName.Length == 0 ? "unnamed" : outName;
        }

        /// INVARIANT CULTURE. A comma-decimal runner would emit `0,417` and
        /// every reader would take `0` and drop the rest — the silent
        /// truncation the no-spaces rule exists for, one character further in.
        static string Num(double v, string fmt) =>
            v.ToString(fmt, CultureInfo.InvariantCulture);
    }
}
